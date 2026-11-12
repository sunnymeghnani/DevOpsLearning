# 37 — Learn: Security & DevSecOps (Fresher to Senior)

This is the security learning module of the handbook. It covers the security work that lands on
a DevOps engineer's desk whether or not "security" is in the job title: hardening the Ubuntu
servers you run, keeping Docker from punching holes in your firewall, running the private CA
that Harbor depends on, keeping secrets out of Git and GitLab job logs, building images that
pass a scanner, locking down your Kubernetes homelab the way the CKS expects, and knowing what
to do in the first hour after something gets compromised. It is written for your real stack:
on-prem Ubuntu 22.04/24.04 with UFW, Apache moved to ports 81/444, Dokploy (Traefik v3 on
Docker Swarm, `dokploy-network`), GitLab CI, Harbor behind a private CA, and a kubeadm cluster
with containerd. AWS appears where the same idea has a cloud form.

The quick-lookup commands for permission problems, sudo, SELinux and auditing live in
[Users, Permissions & Security](10-users-permissions-security.md), and SSH debugging lives in
[SSH & Remote Access](09-ssh-remote-access.md). This module is the *why* and the *how to build
it properly* behind both, plus everything those two modules do not cover.

**Who it serves.** Every career stage. Freshers [L0 · Fresher] and Juniors [L1 · Junior] learn
not to weaken anything and to operate the controls that exist (sections 1–3, 5 and 12). Mid-level
engineers [L2 · Mid] find and close the holes: Docker bypassing UFW, x509 trust errors, image CVEs
(sections 3, 4, 6, 9 and 11). Seniors [L3 · Senior] design security in: PKI, secrets flow,
Kubernetes policy, signed images, cloud IAM (sections 4, 5, 7, 8 and 10). Leads and SREs
[L4 · Lead/SRE] run it as a programme: detection, incident response and compliance evidence
(sections 12–14). Section 0 has the detail and the order to learn it in.

> All sample outputs are illustrative: Ubuntu 22.04/24.04, OpenSSH 8.9/9.6, Docker Engine 27–29,
> Kubernetes v1.34, Harbor 2.x, current Trivy, syft and cosign releases. IPs come from
> documentation ranges (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) or private ranges; lab VMs
> use 192.168.56.0/24. CVE numbers in scanner output are illustrative unless the text names a
> real, well-known CVE. UPPERCASE words in commands are placeholders: HOST, USER, IMAGE,
> CONTAINER, NAMESPACE, SA, VERSION, REGISTRY, PROJECT.

> Security labs are only ever run against systems you own or are explicitly authorised to test.
> Scanning, brute-forcing or probing anyone else's machines is illegal in most countries and will
> get you fired even when it is "just nmap". Every lab here runs on test VMs, a homelab cluster
> or a sandbox AWS account.

---

## 0. How to use this module

> 📚 **Study path:** 1) Note: this section (who it is for, the learning path, the lab setup) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions, as the shared starting point ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 3) KodeKloud: skim the outline of *Certified Kubernetes Security Specialist (CKS)* so you know where this module leads after the CKA ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · 4) Practice: build the three lab VMs below, or use the free [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) when your homelab is off.

### Who this module is for

Security is not a separate career stage. It grows with you: a fresher is expected not to make
things worse, a senior is expected to make whole classes of mistakes impossible. Use this table
to find where you are and which sections to put your hours into.

| Stage | Tag | What you own in security | Focus sections | You have reached it when |
|---|---|---|---|---|
| Fresher (0–1 yr) | [L0 · Fresher] | Not weakening anything: key-only SSH, correct file modes, no secrets in Git | 1, 2 (users, SSH, permissions), 5 (never in git) | you can create a sudo user with key-only SSH and explain every bit of `ls -l /etc/shadow` |
| Junior (1–2 yrs) | [L1 · Junior] | Operating the controls that exist: UFW, fail2ban, patching, GitLab variables, reading auth logs | 2, 3 (firewalls, 80/443), 5, 12 (auth logs) | a fresh VM you hand over passes Lynis at 75+ and nothing but 22/80/443 answers |
| Mid-level (2–4 yrs) | [L2 · Mid] | Finding the hole: Docker bypassing UFW, x509 trust errors, image CVEs, container privileges | 3, 4, 6, 9, 11 | you can explain and fix "x509: certificate signed by unknown authority" on Docker, containerd and in a container, without searching |
| Senior (4–7 yrs) | [L3 · Senior] | Designing it in: private PKI, secrets flow, RBAC/PSA/NetworkPolicy, signed images, Harbor policy, AWS IAM | 4, 5, 7, 8, 10, 1 (threat modelling) | your GitLab → Harbor → Dokploy/Kubernetes pipeline ships only scanned, signed, digest-pinned images with no long-lived secrets in CI |
| Lead / SRE (5+ yrs) | [L4 · Lead/SRE] | Running it as a programme: detection, incident response, patch SLAs, compliance evidence | 11, 12, 13, 14 | you have run a security game day, written the postmortem, and your CVE and access-review processes run without you |

### Learning path

The areas below are grouped by subject so the module also works as a reference. To learn from
zero, follow this order instead. Each item carries its Ops Ladder level and career stage.

| # | Topic | Tag | Section | Why it is in this position |
|---|---|---|---|---|
| 1 | CIA triad, attack surface, least privilege | [L0 · Fresher] | 1 | the vocabulary every later decision uses |
| 2 | Users, sudo, file permissions, SUID | [L0 · Fresher] | 2 | most real compromises escalate through these |
| 3 | SSH hardening and key management | [L1 · Junior] | 2 | SSH is the front door of every Linux server you own |
| 4 | UFW and "only 80/443 are public" | [L1 · Junior] | 3 | the cheapest, biggest reduction in attack surface |
| 5 | Automatic security updates, fail2ban | [L1 · Junior] | 2 | patching is the control that stops most attacks |
| 6 | Secrets never in Git, GitLab CI variables | [L1 · Junior] | 5 | leaked credentials are the most common cloud breach |
| 7 | Auth logs and the journal | [L1 · Junior] | 12 | you cannot respond to what you cannot see |
| 8 | Docker bypasses UFW, DOCKER-USER, nmap your own hosts | [L2 · Mid] | 3 | the hole your Dokploy host has today if nobody checked |
| 9 | TLS trust, private CA, distributing trust | [L2 · Mid] | 4 | Harbor, containerd and GitLab runners all depend on it |
| 10 | Container hardening, docker group, Trivy | [L2 · Mid] | 6 | containers are processes, and they run as root by default |
| 11 | Web and edge hardening on Traefik and Apache | [L2 · Mid] | 9 | the part of your stack the internet actually touches |
| 12 | CVE triage and patch windows | [L2 · Mid] | 11 | turns scanner noise into a short, ordered to-do list |
| 13 | Lynis, CIS benchmarks, auditd | [L2 · Mid] | 2, 12 | measurable hardening instead of opinions |
| 14 | Secrets tooling: Ansible Vault, sops, Vault | [L3 · Senior] | 5 | secrets that rotate and never touch a laptop in plain text |
| 15 | Harbor policies, SBOMs, cosign, digests, SAST/DAST | [L3 · Senior] | 6, 8 | you can prove what is running and where it came from |
| 16 | Kubernetes RBAC, PSA, NetworkPolicy, encryption, audit | [L3 · Senior] | 7 | the CKS syllabus, applied to your homelab |
| 17 | AWS IAM, IMDSv2, CloudTrail | [L3 · Senior] | 10 | the cloud form of least privilege and audit logs |
| 18 | STRIDE threat modelling, segmentation, WireGuard, mTLS | [L3 · Senior] | 1, 3, 4 | designing security in instead of bolting it on |
| 19 | Centralised logging and detection rules | [L4 · Lead/SRE] | 12 | detection that survives the attacker deleting local logs |
| 20 | Incident response, credential rotation, postmortems | [L4 · Lead/SRE] | 13 | the hour that decides how bad an incident becomes |
| 21 | Compliance basics: ISO 27001, SOC 2, evidence | [L4 · Lead/SRE] | 14 | auditors ask engineers for evidence, so learn to produce it |

### Study method

For every ### topic, use the same six steps, in this order:

1. **Read this note** for the topic: concept, key terms and the "see it" commands. Ten to twenty minutes.
2. **Do the matching KodeKloud lesson** (pointers sit at the top of each area under "Study path", and the route table below lists the main courses), including its lab.
3. **Optional video** if a concept still feels fuzzy. Stop as soon as it clicks.
4. **Hands-on lab on your own test VM.** Build the control, break it on purpose, fix it. In security the "break" half has two forms: break the *control* (it stops protecting) and break the *workload* (the control was too strict). You need both.
5. **Attacker hat, then defender hat.** After each lab, write one line on how an attacker would abuse the weakness and one line on how you would detect it. That habit is most of threat modelling.
6. **Open the related playbook** linked in "How it breaks", so the incident version of the problem feels familiar.

After each lab, write the five-line note from your weekly rhythm: symptom, first wrong guess,
evidence that settled it, fix, what you will check first next time. Security notes go into your
public runbook repo too, with hostnames and addresses swapped for documentation ranges.

> Timebox. One topic per 30–45 minute morning slot, as in the Ops Ladder. Until your CKA exam,
> CKA sessions come first. The Kubernetes security area (section 7) doubles as CKS preparation,
> which only makes sense after the CKA.

### KodeKloud route for this module

These are the KodeKloud courses and free lesson notes that line up with this module. Do the named
sections only, in this order, and come back to the matching section here for the on-prem and
Dokploy parts that KodeKloud does not cover.

| Order | KodeKloud material | Covers | Then read here |
|---|---|---|---|
| 1 | [Learning Linux Basics Course & Labs](https://kodekloud.com/courses/the-linux-basics-course), section *Security and File Permissions* | accounts, permissions, SSH, iptables, cron | sections 1 and 2 |
| 2 | [LFCS prep course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs): *Configure SSH Servers and Clients*, *Users and Groups*, [Configure Packet Filtering (Firewall)](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall) | sshd, sudo, UFW | sections 2 and 3 |
| 3 | DevOps Pre-Requisite [SSL & TLS Basics](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page), then LFCS [Work With SSL Certificates](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates), then CKA [TLS Basics](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics) | certificates, CSRs, chains | section 4 |
| 4 | [Docker Certified Associate](https://kodekloud.com/courses/docker-certified-associate-exam-course): *Docker Engine – Security*, *Authenticating to Registries* | namespaces, capabilities, registry logins | sections 4 and 6 |
| 5 | [GitLab CI/CD course](https://kodekloud.com/courses/gitlab-ci-cd): *Architecture & Core Concepts* (variables), then *Optimization, Security and Monitoring* (SAST, container scanning) | CI variables and scanners | sections 5 and 8 |
| 6 | [CKA course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator): *Security* (TLS, kubeconfig, RBAC, NetworkPolicies) | Kubernetes security basics | section 7 |
| 7 | After the CKA: [CKS course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks) (*System Hardening*, then *Supply Chain Security*, then *Runtime Security*) and the free [CKS – Challenges](https://kodekloud.com/courses/cks-challenges) | hardening, Trivy, Falco, audit logs | sections 2, 6, 7, 8, 12 |
| 8 | [Fundamentals of SRE](https://kodekloud.com/courses/fundamentals-of-sre): *Incident Management*, notes on [Blameless Postmortem Culture](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page) | incidents and postmortems | section 13 |

KodeKloud has no course on Harbor, Dokploy, Docker firewalling, sops or Vault. For those, use
the [Harbor docs](https://goharbor.io/docs/), the Docker docs page
[Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/)
and the labs in this module. For a ready-made Ubuntu machine when your homelab is off, use the
free [KodeKloud Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu).

### Lab setup

Use three Ubuntu 24.04 VMs (2 vCPU, 2–4 GB RAM, 25 GB disk) on a host-only network, plus the
kubeadm cluster from [Learn Kubernetes](31-learn-kubernetes.md) for section 7.

| VM | Address | Role in the labs |
|---|---|---|
| sec-target | 192.168.56.21 | the server you harden: Docker, Apache on 81/444, a Traefik container |
| sec-scan | 192.168.56.22 | the "outside": nmap, Trivy, syft, cosign, gitleaks; also your "attacker" |
| sec-reg | 192.168.56.30 | `harbor.example.com`: a registry (Harbor, or `registry:2` for quick labs) and the private CA |

Add `192.168.56.30 harbor.example.com` to `/etc/hosts` on every lab machine. **Take a snapshot of
every VM before each lab.** Several labs lock you out of SSH, block your own traffic or break
Docker networking on purpose, and the snapshot is the undo button.

> Never run these labs on a work server, and never run the "attacker" steps against anything you
> do not own. Several steps (SUID shells, docker-group escalation, planted persistence) are
> exactly what a real attacker does.

Base tools on all three VMs:

```bash
sudo apt-get update
sudo apt-get install -y nmap ndiff lynis auditd audispd-plugins fail2ban wireguard-tools \
  jq curl openssl ca-certificates
```

Scanner tools (Trivy, syft, cosign, gitleaks) change fast, and the Ubuntu archive either does not
carry them or carries old versions. Install each one from its project's official release
instructions, or run its official container image pinned to an exact version. The container
form is used in this module so nothing has to be installed on the host:

```bash
# Pin real version numbers in place of VERSION; never use :latest for security tooling
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:VERSION image IMAGE
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock anchore/syft:VERSION IMAGE
docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:VERSION git -v /repo
```

→ Mounting `/var/run/docker.sock` gives that container root on the host (section 6 explains
why). That is acceptable on a dedicated scan VM and unacceptable on a production host. On
production hosts, scan an exported tarball instead (`docker save IMAGE -o image.tar`, then
`trivy image --input image.tar`).

→ Pinning is not paranoia. In March 2026 the Trivy project itself was hit by a supply-chain attack
(CVE-2026-33634): release v0.69.4 on every channel, Docker Hub images v0.69.5 and v0.69.6, and most
`trivy-action` tags carried a credential stealer aimed at CI secrets. Pin security tools by version
**and** digest, verify release checksums or signatures, and if a pipeline ever ran a version named in
the vendor's advisory, rotate every secret that job could read (section 5).

You also need a throwaway GitLab project (for sections 5 and 8) and, for section 10, a sandbox
AWS account with a budget alarm and nothing else in it.

### Conventions in this module

Each ### topic has the same parts: a level tag, the concept in plain words then precisely, key
terms, "See it on a real system" (read-only commands with sample output), a hands-on lab
(build, break, fix), "How it breaks" (failure, symptom, first command, playbook), why it matters
for troubleshooting, and the next step.

Commands that change security settings carry a warning and a safer alternative first. The
safety habits used throughout:

- **Keep a second root session open** whenever you change SSH, sudo, PAM or the firewall, and test with a *new* connection before closing the old one.
- **Validate before reload:** `sudo sshd -t`, `sudo visudo -c`, `sudo nft -c -f FILE`, `sudo apachectl configtest`.
- **Use a dead-man switch** for remote firewall changes: schedule an automatic rollback with `at` before you apply, cancel it once you have confirmed access (section 3).
- **Snapshot first** on VMs, and record what you changed in the five-line note.

---

## 1. Security mindset

> 📚 **Study path:** 1) Note: this area first (KodeKloud has no threat-modelling course in the verified map, so the handbook leads here) · 2) KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions, for the least-privilege half ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 3) Reading: [OWASP](https://owasp.org/) — search its threat modelling and Top 10 projects · 4) Note: the [Apache 443 case](21-case-apache-443-dokploy.md), which you will model with STRIDE · 5) Practice: the STRIDE lab below on your own Dokploy host's data-flow diagram, checked with nmap from sec-scan.

Tools change every year; the questions behind them do not. This area gives you the five ideas
that every later section applies: what you are protecting (CIA), how it can be attacked
(STRIDE), where it can be reached (attack surface), and how to limit damage (least privilege and
defence in depth).

### CIA triad and risk

**Level:** [L0 · Fresher]

**Concept.** Security protects three properties of systems and data. **Confidentiality**: only
the right people can read it. **Integrity**: nobody can change it without being noticed.
**Availability**: it works when it is needed. Every security control protects one or more of
these, and every incident breaks one or more of them. Two more properties come up constantly:
**authenticity** (it really is who or what it claims to be) and **non-repudiation** (someone
cannot later deny an action, which is what audit logs give you).

Precisely, **risk = likelihood × impact**. You never remove all risk; you reduce the biggest
risks to an acceptable level with the least effort, and you write down the ones you accept.
That last part matters: an accepted, documented risk is a decision; an unknown one is a
surprise.

```
                    Confidentiality
                     (who can read)
                          /\
                         /  \          Your stack, mapped:
                        /    \         C: Harbor robot token in a job log, .env in Git,
                       / DATA \           a world-readable private key
                      /  AND   \       I: an image re-pushed under the same tag,
                     / SYSTEMS  \         a tampered sudoers file, a MITM on HTTP
                    /____________\     A: Apache holding 443, an expired certificate,
          Integrity              Availability   a firewall rule that drops your own SSH
       (who can change)          (does it work)
```

Notice that availability failures are often *caused by* security controls: an expired
certificate, an over-strict firewall rule, a fail2ban jail that bans your office IP. Good
security work keeps availability in the same picture.

**Key terms**

| Term | Meaning |
|---|---|
| Asset | Anything worth protecting: data, a server, a credential, a pipeline |
| Threat | Something that could harm an asset (an attacker, a mistake, a disk failure) |
| Vulnerability | A weakness a threat can use (an unpatched OpenSSH, a password login) |
| Risk | Likelihood that a threat uses a vulnerability, times the impact if it does |
| Control | Anything that reduces risk: a firewall rule, a review, a backup, an alert |
| AAA | Authentication (who are you), Authorisation (what may you do), Accounting (what did you do) |

**See it on a real system**

Each of the three properties can be checked directly on any Ubuntu host:

```bash
ls -l /etc/shadow /etc/passwd /etc/ssl/private          # C: who can read the secrets
sudo dpkg --verify openssh-server sudo                  # I: have packaged files been changed
systemctl is-active ssh apache2 docker                  # A: are the services up
echo | openssl s_client -connect 127.0.0.1:444 2>/dev/null | openssl x509 -noout -enddate  # A: cert expiry
```

```
-rw-r--r-- 1 root root   2217 Sep 30 10:12 /etc/passwd
-rw-r----- 1 root shadow 1290 Sep 30 10:12 /etc/shadow
ls: cannot open directory '/etc/ssl/private': Permission denied
??5?????? c /etc/sudoers
active
active
active
notAfter=Mar 14 08:21:07 2027 GMT
```

→ `/etc/shadow` is `640 root:shadow`: only root and the `shadow` group can read password hashes
(confidentiality). `dpkg --verify` reports `/etc/sudoers` with a `5` in the third column, meaning
its MD5 checksum differs from the packaged file; the `c` marks it as a config file, so a change
is expected after hardening. A `5` on a *binary* such as `/usr/sbin/sshd` would be an integrity
alarm. (`/etc/ssh/sshd_config` never appears here: Ubuntu generates it with `ucf` instead of
shipping it as a dpkg conffile, so `dpkg --verify` does not check it; use your configuration
management or auditd for that file.) The services are up and the certificate is valid until March (availability).

**Hands-on lab (test VM only)**

**Step 1 — Build an asset inventory.** On paper or in a Markdown file, list the assets of
sec-target: the OS, Apache and its vhosts, Docker, the Traefik container, the SSH host keys, the
TLS private keys, your SSH key, any `.env` files. For each, rate C, I and A as high, medium or
low. This is the input to every later lab.

**Step 2 — Break confidentiality.** Make the shadow file world-readable and read it as a normal
user:

```bash
sudo chmod 644 /etc/shadow
sudo -u nobody head -2 /etc/shadow
```

```
root:*:20089:0:99999:7:::
daemon:*:20089:0:99999:7:::
```

→ Any local user (or any compromised web app running as `www-data`) can now copy the password
hashes and crack them offline.

**Step 3 — Fix it and verify against the package default.**

```bash
sudo chmod 640 /etc/shadow && sudo chown root:shadow /etc/shadow
stat -c '%a %U:%G %n' /etc/shadow
sudo -u nobody head -2 /etc/shadow
```

```
640 root:shadow /etc/shadow
head: cannot open '/etc/shadow' for reading: Permission denied
```

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Secret file readable by everyone | Nothing visible until it is stolen | `stat -c '%a %U:%G' FILE` | [Users & permissions](10-users-permissions-security.md) |
| Package binary modified | `dpkg --verify` shows `5` on a non-config file | `sudo dpkg --verify PACKAGE` | section 13 of this module |
| Security control breaks availability | Site down after a firewall or certificate change | `journalctl --since '30 min ago' -p warning` | [Site down playbook](25-playbook-site-down.md) |

**Why it matters for troubleshooting.** When an incident starts, naming the broken property
tells you which evidence to collect: a confidentiality incident needs access logs and a list of
exposed credentials, an integrity incident needs checksums and change history, an availability
incident needs the layered walk from the site-down playbook. It also keeps you honest: "we
disabled the firewall to fix the outage" trades one broken property for another.

**Next step:** apply CIA to a whole system at once with a threat model.

### Threat modelling with STRIDE

**Level:** [L3 · Senior] (start reading at [L2 · Mid])

**Concept.** Threat modelling is asking four questions before an attacker does: *What are we
building? What can go wrong? What are we going to do about it? Did we do a good job?* STRIDE is a
checklist for the second question. You draw the system as a data-flow diagram, mark **trust
boundaries** (places where data crosses from less trusted to more trusted), and for each element
ask which of the six threat types apply.

| Letter | Threat | Property broken | Example in your stack | Typical control |
|---|---|---|---|---|
| S | Spoofing | Authenticity | someone pushes to Harbor with a leaked robot token | short-lived tokens, MFA, mTLS |
| T | Tampering | Integrity | an image re-pushed under the same tag | digest pinning, cosign signatures, tag immutability |
| R | Repudiation | Non-repudiation | "I never ran that `docker rm`" | auditd, Kubernetes audit logs, CloudTrail, central logs |
| I | Information disclosure | Confidentiality | a `.env` file in Git, a Traefik dashboard on the internet | secret scanning, least privilege, closing ports |
| D | Denial of service | Availability | a flood on 443, a disk filled by unrotated logs | rate limits, log rotation, resource limits |
| E | Elevation of privilege | Authorisation | a user in the `docker` group becomes root | no docker group, rootless, PSA restricted |

```
 Data-flow diagram: GitLab CI to Dokploy (= = = marks a trust boundary)

  Developer ──push──► GitLab ──job──► Runner (DinD) ──push──► Harbor
  laptop              (git, CI vars)  ║                       (private CA, Trivy)
       ═══════════════════════════════╬══════════════════════════ boundary: CI → registry
                                      ║                          │ pull (robot account)
  Internet ──443──► Traefik ──► app containers ◄── Dokploy ◄─────┘
  (untrusted)   ═══ boundary: internet → host ═══  (Swarm, docker.sock, :3000 UI)
```

For each arrow crossing a boundary, ask "who can send this, and how do we know it is really
them and unchanged?". Most real findings sit on those arrows.

**Key terms**

| Term | Meaning |
|---|---|
| DFD | Data-flow diagram: processes, data stores, external entities and flows between them |
| Trust boundary | A line where privilege or trust changes, such as internet to host, or CI to registry |
| Threat model | The diagram plus the list of threats, decisions and accepted risks; a living document |
| Mitigation | A control that reduces one threat; each threat should have one or a written acceptance |

**See it on a real system**

Threat models are documents, but the facts in them come from systems. These read-only commands
give you the real boundaries of a Dokploy host instead of the ones you assume:

```bash
sudo ss -tlnp | awk 'NR==1 || /0.0.0.0|\[::\]/'            # what crosses internet → host
docker ps --format '{{.Names}}\t{{.Ports}}'                  # which containers publish ports
docker ps -q | xargs docker inspect --format '{{.Name}} {{range .Mounts}}{{if eq .Source "/var/run/docker.sock"}}MOUNTS-DOCKER-SOCK{{end}}{{end}}'
getent group docker sudo                                     # who can cross host → root
```

```
State  Recv-Q Send-Q Local Address:Port  Peer Address:Port Process
LISTEN 0      4096         0.0.0.0:3000       0.0.0.0:*     users:(("docker-proxy",pid=1873,fd=7))
LISTEN 0      4096         0.0.0.0:443        0.0.0.0:*     users:(("docker-proxy",pid=2101,fd=7))
LISTEN 0      4096         0.0.0.0:80         0.0.0.0:*     users:(("docker-proxy",pid=2117,fd=7))
LISTEN 0      511          0.0.0.0:444        0.0.0.0:*     users:(("apache2",pid=1204,fd=6))
LISTEN 0      511          0.0.0.0:81         0.0.0.0:*     users:(("apache2",pid=1204,fd=4))
LISTEN 0      4096         0.0.0.0:22         0.0.0.0:*     users:(("sshd",pid=998,fd=3))
dokploy-traefik	0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp, 0.0.0.0:443->443/udp
dokploy.1.k3x9p	0.0.0.0:3000->3000/tcp
dokploy-postgres.1.8hd2q	
/dokploy-traefik MOUNTS-DOCKER-SOCK
/dokploy.1.k3x9p MOUNTS-DOCKER-SOCK
/dokploy-postgres.1.8hd2q
docker:x:988:ops,gitlab-runner
sudo:x:27:ops
```

→ Five things cross the internet boundary (22, 80, 443, 3000, and Apache on 81/444), two
containers hold the Docker socket (which is root on the host), and `gitlab-runner` is in the
`docker` group, so every CI job on that runner is effectively root on this host. None of these is
automatically wrong, but each one belongs in the threat model with a decision next to it.

**Hands-on lab (test VM only)**

**Step 1 — Draw it.** Draw the DFD of the Apache-to-Dokploy migration from
[the Apache 443 case](21-case-apache-443-dokploy.md): users, DNS, Traefik, Apache on 81/444,
the app containers, Dokploy UI, GitLab, Harbor. Mark the trust boundaries.

**Step 2 — Fill the STRIDE table.** For every boundary-crossing flow, write at least one threat
per letter that applies, its current control, and a decision: *mitigate*, *accept* (with a
reason and an owner) or *transfer*. Aim for 15–25 rows.

**Step 3 — Break an assumption.** Pick one row whose control you *assumed* exists, for example
"Dokploy UI on 3000 is blocked by UFW". Test it from sec-scan with `nmap -p 3000 192.168.56.21`.
If the port is open (it will be, see section 3), the threat model just found a real
vulnerability. That is the point of the exercise.

**Step 4 — Fix and record.** Apply the fix from the matching section, re-test, and update the
row with the evidence (the nmap output). A threat model with evidence is one an auditor and a
new team member can both trust.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Model drawn from memory, not from the system | The model says "closed", the port is open | `nmap -Pn -p- HOST` from outside | section 3 |
| Model never updated | A new service (Dokploy) is missing from it | `docker ps`, `sudo ss -tlnp` | [Ports inventory](22-playbook-ports-inventory.md) |
| Every threat "mitigated", none accepted | Nobody knows which risks are real | review the decision column | section 14 |

**Why it matters for troubleshooting.** A threat model is a map of where things can be
abused, and abuse often looks like a fault at first: an unexpected 401 from Harbor, a CI job
that suddenly can do too much, traffic on a port nobody remembers opening. Engineers who have
modelled the system recognise these faster.

**Next step:** measure the attack surface the model talks about.

### Attack surface

**Level:** [L1 · Junior]

**Concept.** The attack surface is everything an attacker can reach or use: every listening
port, every exposed admin page, every account that can log in, every installed package with a
possible bug, every credential that exists, every dependency in every image. Shrinking it is the
cheapest security work there is, because a service that is not installed or not reachable cannot
be exploited, no matter how buggy it is.

Precisely, think in three surfaces. The **network** surface: listeners and who can reach them.
The **software** surface: packages, images, libraries, SUID binaries. The **human and
credential** surface: accounts with shells, keys in `authorized_keys`, tokens in CI, members of
`sudo` and `docker`.

**Key terms**

| Term | Meaning |
|---|---|
| Listener | A socket in LISTEN state; reachable from wherever its bind address and firewall allow |
| Bind address | `0.0.0.0` means every interface; `127.0.0.1` means this host only |
| Exposure | Reachable from where: the internet, the LAN, the host, or nothing |
| Hardening | Removing or restricting surface without breaking the workload |

**See it on a real system**

```bash
sudo ss -tulnp                                       # network surface: every listener
systemctl list-units --type=service --state=running --no-legend | wc -l
dpkg-query -W -f='${binary:Package}\n' | wc -l       # software surface: package count
awk -F: '$7 !~ /(nologin|false)$/ {print $1, $7}' /etc/passwd   # accounts that can get a shell
```

```
Netid State  Local Address:Port  Process
udp   UNCONN 127.0.0.54:53       users:(("systemd-resolve",pid=612,fd=16))
udp   UNCONN 127.0.0.53%lo:53    users:(("systemd-resolve",pid=612,fd=14))
tcp   LISTEN 0.0.0.0:81          users:(("apache2",pid=1204,fd=4))
tcp   LISTEN 0.0.0.0:444         users:(("apache2",pid=1204,fd=6))
tcp   LISTEN 127.0.0.1:631       users:(("cupsd",pid=871,fd=7))
tcp   LISTEN 0.0.0.0:22          users:(("sshd",pid=998,fd=3))
31
612
root /bin/bash
sync /bin/sync
ops /bin/bash
backup2 /bin/bash
```

→ (Recv-Q, Send-Q and peer columns trimmed.) Three findings in four commands. Apache on 81/444 listens on every interface even though
only Traefik should talk to it now. A print server (`cupsd`) is installed on a server. And an
account called `backup2` has a login shell that nobody can explain. Each is surface you can
remove. (`sync` with `/bin/sync` is a harmless historical default.)

**Hands-on lab (test VM only)**

**Step 1 — Baseline.** Save the four outputs above to `~/surface-before.txt`.

**Step 2 — Break: grow the surface.** Install something you do not need and leave Apache
listening everywhere:

```bash
sudo apt-get install -y cups vsftpd
sudo ss -tlnp | grep -E ':(21|631)\s'
```

**Step 3 — Fix: shrink it.** Remove the packages, lock unknown accounts, and restrict Apache to
the addresses Traefik uses. Apache is a *host* process, so UFW does protect it (unlike Docker
published ports, section 3). Restrict 81/444 to the Docker networks only:

```bash
sudo apt-get purge -y cups vsftpd && sudo apt-get autoremove -y
sudo usermod -L -s /usr/sbin/nologin backup2           # lock, do not delete (evidence)
sudo ufw allow from 172.16.0.0/12 to any port 81,444 proto tcp comment 'Traefik to Apache'
sudo ufw deny 81,444/tcp
sudo ufw status numbered | grep -E '81|444'
```

→ UFW evaluates rules in order, so the `allow from 172.16.0.0/12` rule must come before the
`deny`. The 172.16.0.0/12 range covers Docker's default local bridge pools (172.17–172.31:
`docker0`, user-defined bridges and `docker_gwbridge`, the bridge through which Swarm and overlay
containers such as Traefik reach host services). The overlay subnets themselves, including
`dokploy-network`, come from 10.0.0.0/8 by default, but their packets reach the host from the
`docker_gwbridge` address, not the overlay one. In production, narrow the rule to the source
address Traefik's connections really arrive from (`sudo ss -tn '( sport = :81 or sport = :444 )'`
while the site is in use shows the peers; Apache's access log shows it too until `mod_remoteip`,
section 9, replaces it with the client address). If
Traefik reaches Apache through the host's LAN address instead, allow that path and test before you
deny.

**Step 4 — Verify from outside.** UFW must be active for these rules to apply (`sudo ufw status
verbose` shows `Status: active`; section 3 enables it safely). From sec-scan,
`nmap -p 21,81,444,631 192.168.56.21` should show 81 and 444 as `filtered`. With UFW's default
"deny incoming" policy, 21 and 631 show `filtered` too (they would be `closed` only with UFW off),
so also confirm on sec-target that nothing listens there any more (`sudo ss -tlnp`). Save the new
baseline.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Service listens on 0.0.0.0 by default | Port reachable from the LAN or internet | `sudo ss -tlnp` | [Ports inventory](22-playbook-ports-inventory.md) |
| Restriction breaks the proxy path | Traefik returns 502 or 504 for the Apache-backed site | `docker logs dokploy-traefik --tail 50` | [Site down playbook](25-playbook-site-down.md) |
| Unknown account with a shell | Appears in `/etc/passwd`, nobody owns it | `sudo lastlog -u ACCOUNT` | section 13 |

**Why it matters for troubleshooting.** The inventory you build for security is the same one
you need for every "what is on this port?" incident. Engineers who keep the attack surface small
also have fewer moving parts to suspect when something breaks.

**Next step:** limit what each remaining piece can do if it is compromised.

### Least privilege and defence in depth

**Level:** [L0 · Fresher] for the idea, [L3 · Senior] to design with it

**Concept.** **Least privilege** means every user, process, token and container gets only the
permissions it needs, for only as long as it needs them. **Defence in depth** means you never
rely on a single control: if one layer fails, the next one still stops or at least detects the
attacker.

```
 Defence in depth for one Dokploy app (an attacker must beat every layer)

  ┌──────────────────────────────────────────────────────────────────────┐
  │ Network   UFW + DOCKER-USER, only 80/443 public, admin over VPN      │
  │ ┌──────────────────────────────────────────────────────────────────┐ │
  │ │ Host     patched kernel, key-only SSH, no docker group, auditd   │ │
  │ │ ┌──────────────────────────────────────────────────────────────┐ │ │
  │ │ │ Runtime  non-root, read-only rootfs, cap-drop ALL, seccomp   │ │ │
  │ │ │ ┌──────────────────────────────────────────────────────────┐ │ │ │
  │ │ │ │ App      authn/authz, input validation, security headers │ │ │ │
  │ │ │ │ ┌──────────────────────────────────────────────────────┐ │ │ │ │
  │ │ │ │ │ Data   least-privilege DB user, encryption, backups  │ │ │ │ │
  │ │ │ │ └──────────────────────────────────────────────────────┘ │ │ │ │
  │ │ │ └──────────────────────────────────────────────────────────┘ │ │ │
  │ │ └──────────────────────────────────────────────────────────────┘ │ │
  │ └──────────────────────────────────────────────────────────────────┘ │
  └──────────────────── Detection: central logs + alerts ────────────────┘
```

Least privilege shows up everywhere in your stack: a `sudoers` rule for one command instead of
`ALL`, a Harbor robot account that can only pull from one project, a GitLab deploy token with
only `read_registry`, a Kubernetes Role in one namespace instead of a ClusterRole, an IAM policy
for one bucket. It also applies to *time*: an SSH certificate valid for 8 hours beats a key that
works forever.

**Key terms**

| Term | Meaning |
|---|---|
| Least privilege | Minimum permissions, minimum scope, minimum duration |
| Separation of duties | No single person or token can both make and approve a risky change |
| Blast radius | What an attacker can reach after compromising one thing |
| Defence in depth | Several independent layers, so one failure is not a breach |
| GTFOBins-style escape | Using an allowed program (an editor, a pager) to get a shell with its privileges |

**See it on a real system**

```bash
sudo -l -U deploy                 # what a user may run with sudo
id deploy                         # groups that grant power (sudo, docker, adm, lxd)
sudo grep -rh NOPASSWD /etc/sudoers /etc/sudoers.d/ 2>/dev/null
```

```
Matching Defaults entries for deploy on sec-target:
    env_reset, mail_badpass, secure_path=/usr/local/sbin\:/usr/local/bin\:/usr/sbin\:/usr/bin\:/sbin\:/bin\:/snap/bin, use_pty

User deploy may run the following commands on sec-target:
    (root) NOPASSWD: /usr/bin/systemctl restart apache2, /usr/bin/less /var/log/apache2/*
uid=1003(deploy) gid=1003(deploy) groups=1003(deploy)
ubuntu ALL=(ALL) NOPASSWD:ALL
deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart apache2, /usr/bin/less /var/log/apache2/*
```

→ The first rule is tight. The second one is a root shell in disguise: `less` can run shell
commands with `!`, and the `*` wildcard also matches `/var/log/apache2/../../../etc/shadow`. The
`ubuntu ALL=(ALL) NOPASSWD:ALL` line comes from cloud-init on cloud images and means a stolen
`ubuntu` key is instant root.

**Hands-on lab (test VM only)**

**Step 1 — Build the "tight" rule.** Create the `deploy` user and give it the two rules above
through a drop-in file, always with `visudo` so a typo cannot lock everyone out:

```bash
sudo adduser --disabled-password --gecos '' deploy
echo 'deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart apache2, /usr/bin/less /var/log/apache2/*' \
  | sudo tee /etc/sudoers.d/deploy >/dev/null
sudo chmod 440 /etc/sudoers.d/deploy
sudo visudo -cf /etc/sudoers.d/deploy
```

```
/etc/sudoers.d/deploy: parsed OK
```

**Step 2 — Break it: escape through the pager.** As `deploy`, open a log with the allowed
command, then type `!id` inside `less`:

```bash
sudo -iu deploy
sudo /usr/bin/less /var/log/apache2/access.log
# inside less, type:  !id   then Enter
```

```
uid=0(root) gid=0(root) groups=0(root)
!done  (press RETURN)
```

→ The "read a log" rule just gave root. The same class of escape exists for `vi`, `find
-exec`, `tar --checkpoint-action`, `awk`, `git` and many others.

**Step 3 — Fix it with less privilege, not a cleverer rule.** Reading logs does not need root
at all on Ubuntu: the `adm` group can read `/var/log/apache2` and most of `/var/log`, and the
`systemd-journal` group can read the whole journal.

```bash
sudo tee /etc/sudoers.d/deploy >/dev/null <<'EOF'
deploy ALL=(root) NOPASSWD: /usr/bin/systemctl restart apache2
EOF
sudo visudo -cf /etc/sudoers.d/deploy
sudo usermod -aG adm deploy
sudo -iu deploy less /var/log/apache2/access.log    # works, as deploy, no sudo
```

If a program genuinely must run as root and can spawn commands, add the `NOEXEC:` tag
(`deploy ALL=(root) NOEXEC: /usr/bin/less /var/log/apache2/access.log`) and name exact files,
never wildcards. For editing root-owned files, grant `sudoedit FILE`, which edits a copy as the
user and writes it back, instead of `sudo vi FILE`.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Too much privilege | A "limited" user reaches root | `sudo -l -U USER` | [Users & permissions](10-users-permissions-security.md) |
| Too little privilege | Deploys fail with "a password is required" or "not allowed to execute" | `sudo -l -U USER`, `journalctl _COMM=sudo -n 20` | [Users & permissions](10-users-permissions-security.md) |
| A layer silently missing | Pen test or nmap finds what you thought was blocked | test each layer separately | section 3 |

**Why it matters for troubleshooting.** Many "permission denied" incidents are least privilege
working as designed, and the wrong fix (`chmod 777`, `NOPASSWD:ALL`, `--privileged`) removes a
layer for good. The right fix grants the *one* missing permission. You will use this reasoning
in every area of this module.

**Next step:** apply all of this to the host itself, starting with users and sudo.

---

## 2. Linux hardening

> 📚 **Study path:** 1) KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions (accounts, permissions, SSH) ([course](https://kodekloud.com/courses/the-linux-basics-course)) · 2) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Users and Groups, then Networking: Configure SSH Servers and Clients ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 3) Note: [Users & permissions](10-users-permissions-security.md), [SSH & remote access](09-ssh-remote-access.md) and the security basics area of [Learn Linux](27-learn-linux.md) · 4) After the CKA: *Certified Kubernetes Security Specialist (CKS)* — System Hardening, which is this area with a Kubernetes label ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · 5) Practice: the Lynis lab at the end of this area on a fresh VM or the [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu), then the free *Linux Challenges* ([course](https://kodekloud.com/courses/linux-challenges)).

Hardening is removing what an attacker could use and making what remains harder to abuse,
*without breaking the workload*. Every server you run should get the same baseline: named
accounts, key-only SSH, automatic security updates, a measured file-permission state, an audit
trail, and a score you can compare over time. The quick-lookup commands for permission errors
are in [Users & permissions](10-users-permissions-security.md); this area is about building the
baseline.

### Users, sudo and accounts

**Level:** [L0 · Fresher]

**Concept.** Every human gets a **named account**, never a shared `ubuntu`, `admin` or `root`
login, because shared accounts make the audit trail useless ("ubuntu ran `rm -rf`" names nobody).
Power comes from **group membership**, so the groups are what you audit. On Ubuntu, `sudo`
grants root through sudo, and several other groups are root-equivalent or close to it:

| Group | Grants | Treat as |
|---|---|---|
| `sudo` (Ubuntu), `wheel` (RHEL) | root through sudo, per `/etc/sudoers` | root |
| `docker` | full control of the Docker daemon, which runs as root | root (section 6) |
| `lxd` / `incus-admin` | control of LXD/Incus containers, which can mount the host | root |
| `adm` | read most of `/var/log` | sensitive (logs contain tokens and IPs) |
| `systemd-journal` | read the whole journal | sensitive |
| `shadow` | read `/etc/shadow` | sensitive |

Service accounts (for apps and daemons) are **system users**: UID below 1000, no password, shell
`/usr/sbin/nologin`, and a home directory only if the service needs one.

**Key terms**

| Term | Meaning |
|---|---|
| UID 0 | root; any account with UID 0 *is* root, whatever its name |
| Locked account | `!` prefixed to the hash in `/etc/shadow`; password login refused (keys may still work) |
| nologin shell | `/usr/sbin/nologin`; refuses interactive logins with a polite message |
| sudoers drop-in | a file in `/etc/sudoers.d/`; files whose names contain `.` or end in `~` are **ignored** |
| `use_pty` | sudo default on recent Ubuntu; runs commands in a new pty so background processes cannot hijack your terminal |

**See it on a real system**

```bash
getent group sudo adm docker lxd                           # who holds power
awk -F: '$3 == 0 {print $1}' /etc/passwd                   # every UID-0 account (should be only root)
sudo awk -F: '$2 == "" {print $1 " has an EMPTY password"}' /etc/shadow
sudo grep -rv '^\s*#' /etc/sudoers.d/ | grep -v ':\s*$'   # active drop-in rules
sudo lastlog | awk 'NR==1 || !/Never logged in/'           # who has ever logged in
sudo chage -l ops                                        # password and account expiry
```

```
sudo:x:27:ops,ubuntu
adm:x:4:syslog,ops
docker:x:988:ops,gitlab-runner
lxd:x:110:ubuntu
root
/etc/sudoers.d/90-cloud-init-users:ubuntu ALL=(ALL) NOPASSWD:ALL
Username         Port     From             Latest
ops            pts/0    192.168.56.1     Fri Oct  2 09:14:51 +0000 2026
ubuntu           pts/1    203.0.113.45     Sun Sep 13 02:41:07 +0000 2026
Last password change                                    : Sep 30, 2026
Password expires                                        : never
Password inactive                                       : never
Account expires                                         : never
Minimum number of days between password change          : 0
Maximum number of days between password change          : 99999
Number of days of warning before password expires       : 7
```

→ Two findings. The `ubuntu` cloud-image account still has passwordless sudo and is in `lxd`.
And it last logged in at 02:41 on a Sunday from 203.0.113.45, an address nobody recognises.
That second line is the start of section 13, not a hardening task.

**Hands-on lab (test VM only)**

**Step 1 — Build: named admin, password for sudo, shared account locked.** Keep a root shell
open in a second terminal (`sudo -i`) for the whole lab.

```bash
sudo adduser --gecos '' alice                    # set a strong password: sudo will ask for it
sudo usermod -aG sudo alice
sudo install -d -m 700 -o alice -g alice /home/alice/.ssh
sudo cp ~/.ssh/authorized_keys /home/alice/.ssh/ && sudo chown alice: /home/alice/.ssh/authorized_keys
# test in a NEW terminal: ssh alice@192.168.56.21, then sudo -v  (asks for alice's password)
sudo rm /etc/sudoers.d/90-cloud-init-users       # only after alice's sudo works
sudo usermod -L -s /usr/sbin/nologin ubuntu
sudo gpasswd -d ubuntu lxd
```

**Step 2 — Break it: a sudoers typo written without visudo.**

```bash
echo 'alice ALL=(ALL) NOPASSWD ALL' | sudo tee /etc/sudoers.d/alice     # missing colon
sudo -v
```

```
>>> /etc/sudoers.d/alice: syntax error near line 1 <<<
sudo: parse error in /etc/sudoers.d/alice near line 1
sudo: no valid sudoers sources found, quitting
sudo: error initializing audit plugin sudoers_audit
```

→ One bad drop-in disables sudo for *everyone* (exact wording varies by sudo version: the output
above is the older format, while newer releases such as the one in Ubuntu 24.04 report
`FILE:LINE:COLUMN: syntax error` and mark the bad token under the line). Without
the root shell you kept open, recovery means the hypervisor console and recovery mode, or on a
cloud VM a serial console or attaching the disk to another instance.

**Step 3 — Fix it from the root shell, and never repeat it.**

```bash
# in the root shell you kept open
rm /etc/sudoers.d/alice
visudo -c
# from now on, always edit drop-ins like this:
visudo -f /etc/sudoers.d/alice
```

```
/etc/sudoers: parsed OK
/etc/sudoers.d/README: parsed OK
/etc/sudoers.d/deploy: parsed OK
```

`visudo` refuses to save a file that does not parse. If you script sudoers changes (Ansible, for
example), validate before moving the file into place; Ansible's `template` module does this with
`validate: 'visudo -cf %s'`.

**RHEL/Rocky difference:** the admin group is `wheel`, and the log goes to `/var/log/secure`.
Cloud images use `/etc/sudoers.d/90-cloud-init-users` the same way.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Syntax error in a drop-in | every `sudo` fails with "parse error" | `visudo -c` (as root) | [Users & permissions](10-users-permissions-security.md) |
| Drop-in named `alice.conf` | rule silently ignored, "user is not in the sudoers file" | `ls /etc/sudoers.d/` | [Users & permissions](10-users-permissions-security.md) |
| Group change not picked up | still "permission denied" after `usermod -aG` | `id` (log out and in, or `newgrp`) | [Users & permissions](10-users-permissions-security.md) |
| Unknown login in `lastlog` | logins at odd times from unknown IPs | `last -i -F USER`, `journalctl -u ssh` | section 13 |

**Why it matters for troubleshooting.** Group membership explains many confusing incidents:
a user who "isn't root" but can read every log (`adm`), or a CI job that can start privileged
containers (`docker`). And a named-account policy is what makes `journalctl _COMM=sudo` tell you
*who* restarted Apache at 3 a.m.

**Next step:** lock down the way those accounts log in.

### SSH hardening

**Level:** [L1 · Junior]

**Concept.** SSH is the front door to every Linux server you run, and the internet scans port 22
constantly. A hardened sshd accepts only public keys, never root, only from members of one
group, and gives up quickly on failed attempts. That alone removes password guessing, which is
how most opportunistic compromises of Linux servers start.

Precisely, two OpenSSH behaviours decide whether your hardening actually applies:

1. **The first value wins.** For most keywords, sshd uses the *first* value it reads.
2. **Drop-ins are read first.** Ubuntu's `/etc/ssh/sshd_config` begins with `Include /etc/ssh/sshd_config.d/*.conf`, and the files are read in lexical order.

So a cloud-init file named `50-cloud-init.conf` containing `PasswordAuthentication yes` beats your
`99-hardening.conf`. Name your file so it sorts first (`10-hardening.conf`) and always verify the
*effective* configuration with `sshd -T`, never by reading files.

**Key terms**

| Term | Meaning |
|---|---|
| `sshd -t` | test the configuration for syntax errors (run before every reload) |
| `sshd -T` | print the effective configuration after all includes; `-C user=,host=,addr=` evaluates `Match` blocks |
| `KbdInteractiveAuthentication` | keyboard-interactive (PAM prompts); replaces `ChallengeResponseAuthentication` on 22.04+ |
| `AllowGroups` | only members of these groups may log in at all |
| `AuthenticationMethods` | the methods required to log in; `publickey` alone means key-only |
| `ssh.socket` | on Ubuntu 22.10 and later, systemd listens on 22 and starts sshd; port changes need a daemon-reload |

**See it on a real system**

```bash
sudo sshd -T | grep -Ei '^(permitrootlogin|passwordauthentication|kbdinteractiveauthentication|pubkeyauthentication|maxauthtries|x11forwarding|allowtcpforwarding|allowgroups|authenticationmethods)'
ls -l /etc/ssh/sshd_config.d/
systemctl list-units 'ssh*' --no-legend
```

```
maxauthtries 6
permitrootlogin without-password
pubkeyauthentication yes
passwordauthentication yes
kbdinteractiveauthentication no
x11forwarding yes
allowtcpforwarding yes
authenticationmethods any
-rw-r--r-- 1 root root 27 Sep 30 10:02 50-cloud-init.conf
ssh.service   loaded active running OpenBSD Secure Shell server
ssh.socket    loaded active running OpenBSD Secure Shell server socket
```

→ This is a typical fresh cloud VM: password logins on (from `50-cloud-init.conf`), root
allowed with a key (`without-password` is the old name for `prohibit-password`), six attempts
per connection, X11 and TCP forwarding on. No `allowgroups` line means everyone may log in.

**Hands-on lab (test VM only)**

> Keep your current SSH session open for the whole lab and test every change from a **new**
> terminal. If the new login fails, fix it from the old session. Snapshot first.

**Step 1 — Build the hardened drop-in.**

```bash
sudo groupadd -f sshusers
sudo usermod -aG sshusers alice
sudo usermod -aG sshusers ops
sudo tee /etc/ssh/sshd_config.d/10-hardening.conf >/dev/null <<'EOF'
# Loaded before 50-cloud-init.conf; the first value of a keyword wins.
PermitRootLogin no
PasswordAuthentication no
KbdInteractiveAuthentication no
PubkeyAuthentication yes
AuthenticationMethods publickey
AllowGroups sshusers
MaxAuthTries 3
LoginGraceTime 30
X11Forwarding no
AllowAgentForwarding no
AllowTcpForwarding no
PermitTunnel no
ClientAliveInterval 300
ClientAliveCountMax 2
LogLevel VERBOSE
EOF
sudo sshd -t && sudo systemctl reload ssh
```

`LogLevel VERBOSE` adds the fingerprint of every key *tried*, which you want during an
investigation. `AllowTcpForwarding no` breaks port tunnels and editor remote sessions; keep it
`yes` on a bastion (section 3) or for a `Match Group` of admins who need it.

**Step 2 — Verify from a new terminal.**

```bash
ssh -o PubkeyAuthentication=no -o PreferredAuthentications=password alice@192.168.56.21
ssh alice@192.168.56.21 'id'
```

```
alice@192.168.56.21: Permission denied (publickey).
uid=1001(alice) gid=1001(alice) groups=1001(alice),27(sudo),1005(sshusers)
```

→ Password authentication is refused outright (the server only offers `publickey`), and the key
login still works.

**Step 3 — Break it: lose the include-order race.** Rename your file so it sorts after
cloud-init's, and make cloud-init's file enable passwords:

```bash
echo 'PasswordAuthentication yes' | sudo tee /etc/ssh/sshd_config.d/50-cloud-init.conf
sudo mv /etc/ssh/sshd_config.d/10-hardening.conf /etc/ssh/sshd_config.d/99-hardening.conf
sudo sshd -t && sudo systemctl reload ssh
sudo sshd -T | grep -i '^passwordauthentication'
```

```
passwordauthentication yes
```

→ Your file still says `no`, the file you did not write says `yes`, and `yes` wins. Anyone who
"checked the config file" would swear password logins are off.

**Step 4 — Break it again: lock yourself out with AllowGroups.** Rename the file back to
`10-hardening.conf`, remove `alice` from `sshusers` (`sudo gpasswd -d alice sshusers`), and try a
new login. The client says only `Permission denied (publickey)`; the server says why:

```bash
sudo journalctl -u ssh -n 5 --no-pager
```

```
Oct 02 10:31:12 sec-target sshd[4120]: User alice from 192.168.56.1 not allowed because none of user's groups are listed in AllowGroups
Oct 02 10:31:12 sec-target sshd[4120]: Connection closed by invalid user alice 192.168.56.1 port 50122 [preauth]
```

**Step 5 — Fix and record.** Put `alice` back in `sshusers`, set `PasswordAuthentication no` in
`50-cloud-init.conf` too (or set `ssh_pwauth: false` in cloud-init so it stops writing `yes`),
reload, and confirm with `sshd -T`.

**RHEL/Rocky difference:** the unit is `sshd`, the drop-in shipped by the OS is
`50-redhat.conf`, and changing `Port` also needs an SELinux label
(`sudo semanage port -a -t ssh_port_t -p tcp 2222`). On Ubuntu 24.04, a `Port` change needs
`sudo systemctl daemon-reload && sudo systemctl restart ssh.socket` because of socket
activation. Moving SSH off port 22 only reduces log noise; it is not a security control.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Earlier drop-in overrides yours | password logins still accepted | `sudo sshd -T | grep -i passwordauth` | [SSH & remote access](09-ssh-remote-access.md) |
| User not in AllowGroups | `Permission denied (publickey)` with a valid key | `sudo journalctl -u ssh -n 20` | [SSH & remote access](09-ssh-remote-access.md) |
| `AllowTcpForwarding no` on a jump host | `channel 0: open failed: administratively prohibited` | `sudo sshd -T | grep -i allowtcp` | section 3 (bastions) |
| Syntax error, sshd reload refused | `sshd -t` prints the bad line; existing sessions survive | `sudo sshd -t` | [Services & systemd](07-services-systemd.md) |

**Why it matters for troubleshooting.** "SSH broke after hardening" is one of the most common
self-inflicted outages, and the client-side message is nearly always just `Permission denied`.
The habit this lab builds (effective config with `sshd -T`, reason from the server log, never
close the working session) is the same one that solves every SSH incident.

**Next step:** manage the keys that are now the only way in.

### SSH key management

**Level:** [L1 · Junior] for keys, [L3 · Senior] for SSH certificates

**Concept.** Once passwords are off, **keys are the credentials**, and they need the same care
as passwords: strong type, a passphrase, an owner, an expiry, and removal when people leave.
The usual failure is not a weak key but a forgotten one: the contractor key in
`root/.ssh/authorized_keys` from 2024, or the decommissioned CI server's key that still works
on every host.

Precisely, use `ed25519` keys (or `ed25519-sk` on a FIDO2 hardware key), protect them with a
passphrase and `ssh-agent`, restrict automation keys with `authorized_keys` options, and verify
host keys instead of typing `yes`. At scale ([L3 · Senior]), replace scattered
`authorized_keys` files with **SSH certificates**: a CA you control signs a user's public key
for a few hours, servers trust the CA, and offboarding means simply not signing any more.

**Key terms**

| Term | Meaning |
|---|---|
| Fingerprint | `SHA256:...` hash of a public key; what logs and `ssh-keygen -l` show |
| `restrict` | `authorized_keys` option that disables forwarding, pty and X11 for that key |
| `from="..."` | key only accepted from these addresses |
| `command="..."` | forced command; the key can run only this, whatever the client asks |
| Agent forwarding | lets the remote host use your local agent; root there can impersonate you |
| `ProxyJump` | connect through a bastion without forwarding your agent |
| User certificate | a public key signed by a CA with a key ID, principals and validity window |
| KRL | key revocation list, read by sshd through `RevokedKeys` |

**See it on a real system**

Inventory every authorized key on a host and compare it with what has actually been used:

```bash
sudo find /root /home -name authorized_keys -path '*/.ssh/*' 2>/dev/null |
  while read -r f; do echo "== $f"; sudo ssh-keygen -lf "$f"; done
sudo journalctl -u ssh --since '90 days ago' --no-pager | grep 'Accepted publickey' |
  awk '{print $9, $NF}' | sort | uniq -c
```

```
== /home/ops/.ssh/authorized_keys
256 SHA256:9mQ2vKx3c7Yp1hT0dLw8JfR4uZ6aNbE5sVqGiOyXk2M ops@laptop-2026 (ED25519)
3072 SHA256:Lq7Rz0bW1yH8mT5cV9pK3dJ6sF2nX4gA0eU7iO1rQ8E jenkins@old-ci (RSA)
== /root/.ssh/authorized_keys
256 SHA256:Xr4pA1bC2dE3fG4hI5jK6lM7nO8pQ9rS0tU1vW2xY3Z contractor-2024 (ED25519)
    412 ops SHA256:9mQ2vKx3c7Yp1hT0dLw8JfR4uZ6aNbE5sVqGiOyXk2M
```

→ Three keys exist, one has been used in 90 days. The old Jenkins key and the contractor key in
root's file are pure risk: remove them (after a quick check that nothing automated still uses
them, which the 90-day log just answered).

**Hands-on lab (test VM only)**

**Step 1 — Build a good key and a restricted automation key.**

```bash
# on your workstation
ssh-keygen -t ed25519 -a 100 -C "alice@laptop-2026"            # -a 100: slow KDF for the passphrase
ssh-keygen -t ed25519 -N '' -f ~/.ssh/backup_push -C "backup-push"
# on sec-target, in /home/alice/.ssh/authorized_keys (one line):
# restrict,from="192.168.56.22",command="/usr/local/bin/backup-receive" ssh-ed25519 AAAAC3...Q backup-push
```

The backup key can only run one script, only from sec-scan, and can never open a shell or a
tunnel, so stealing it gains an attacker almost nothing.

**Step 2 — Build an SSH user CA ([L3 · Senior]).** On sec-reg (your CA host):

```bash
mkdir -p -m 700 ~/ssh-ca
ssh-keygen -t ed25519 -f ~/ssh-ca/user_ca -C "Example user CA 2026"
# sign alice's public key for 10 minutes, principal (allowed login name) "alice"
ssh-keygen -s ~/ssh-ca/user_ca -I alice@example.com -n alice -V +10m alice_id_ed25519.pub
ssh-keygen -L -f alice_id_ed25519-cert.pub
```

```
alice_id_ed25519-cert.pub:
        Type: ssh-ed25519-cert-v01@openssh.com user certificate
        Public key: ED25519-CERT SHA256:9mQ2vKx3c7Yp1hT0dLw8JfR4uZ6aNbE5sVqGiOyXk2M
        Signing CA: ED25519 SHA256:Hc2Lk9Pq4Wd7Zs1Xv8Tn3Ry6Ub0Mf5Je2Ga9Ko4Ni7B (using ssh-ed25519)
        Key ID: "alice@example.com"
        Serial: 0
        Valid: from 2026-10-02T10:41:12 to 2026-10-02T10:51:12
        Principals: 
                alice
        Critical Options: (none)
        Extensions: 
                permit-X11-forwarding
                permit-agent-forwarding
                permit-port-forwarding
                permit-pty
                permit-user-rc
```

On sec-target, trust the CA and remove alice's `authorized_keys` to prove the certificate alone
works:

```bash
sudo install -m 644 user_ca.pub /etc/ssh/user_ca.pub
echo 'TrustedUserCAKeys /etc/ssh/user_ca.pub' | sudo tee /etc/ssh/sshd_config.d/20-user-ca.conf
sudo sshd -t && sudo systemctl reload ssh
sudo mv /home/alice/.ssh/authorized_keys /home/alice/.ssh/authorized_keys.off
# copy alice_id_ed25519-cert.pub next to alice's private key on the workstation, then:
ssh alice@192.168.56.21 id
```

**Step 3 — Break it: let the certificate expire.** Wait 11 minutes and log in again. The client
just falls back to `Permission denied (publickey)`. The server log has the reason:

```
Oct 02 10:52:03 sec-target sshd[4388]: error: Certificate invalid: expired
```

**Step 4 — Fix it the way production does.** Sign a new certificate. In production this is a
short command or a small service (`step ssh`, Vault's SSH secrets engine, Teleport and similar
tools do it after SSO) that issues 8-hour certificates each morning. Offboarding then needs no
change on any server. For an emergency revocation, add the key to a KRL
(`sudo ssh-keygen -k -f /etc/ssh/revoked_keys alice_id_ed25519.pub`; add `-u` to update an existing
KRL) and point `RevokedKeys` at it.

Also verify **host** keys properly once: read the fingerprint on the console
(`ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub`) and compare it with what the client shows
on first connect. In GitLab CI, store a known-good `known_hosts` in a file-type variable rather
than using `StrictHostKeyChecking no`, which accepts any man in the middle.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Wrong key offered, or too many keys in the agent | `Too many authentication failures` | `ssh -v USER@HOST` (lists each key tried) | [SSH & remote access](09-ssh-remote-access.md) |
| `authorized_keys` permissions too open | key ignored, "bad ownership or modes" in the server log | `ls -ld ~ ~/.ssh ~/.ssh/authorized_keys` | [SSH & remote access](09-ssh-remote-access.md) |
| Host rebuilt or MITM | `REMOTE HOST IDENTIFICATION HAS CHANGED!` | compare with console fingerprint, then `ssh-keygen -R HOST` | [SSH & remote access](09-ssh-remote-access.md) |
| Certificate expired or wrong principal | `Permission denied (publickey)` | `ssh-keygen -L -f CERT`, server journal | this topic |

**Why it matters for troubleshooting.** Half of SSH incidents are key problems: the wrong key,
an expired certificate, a changed host key after a rebuild. Knowing that the *server* log holds
the reason, and that `ssh-keygen -L` and `-l` show you exactly what is being presented, turns a
guessing game into a two-command fix.

**Next step:** slow down the bots that keep knocking anyway.

### fail2ban

**Level:** [L1 · Junior]

**Concept.** fail2ban reads logs (or the journal), counts failures per source IP, and bans an IP
in the firewall for a while when it crosses a threshold. With key-only SSH it no longer prevents
compromise; what it gives you is **less noise** (smaller logs, fewer alerts) and protection for
services that still use passwords, such as a web login behind Apache.

Precisely: a **jail** combines a **filter** (regexes that recognise a failure line), a
**backend** (where to read: `systemd` journal or a log file), and an **action** (how to ban:
nftables, iptables, UFW). Never edit `jail.conf`; put overrides in `/etc/fail2ban/jail.local` or
`/etc/fail2ban/jail.d/*.local`.

**Key terms**

| Term | Meaning |
|---|---|
| `maxretry` / `findtime` | ban after this many failures within this window |
| `bantime` | how long a ban lasts; `bantime.increment = true` makes repeat offenders' bans longer |
| `ignoreip` | never ban these (your VPN, office, monitoring) |
| `banaction` | firewall backend: `nftables`, `iptables-multiport`, `ufw` |
| `fail2ban-regex` | tests a filter against a log; the first tool when a jail never bans anything |

**See it on a real system**

```bash
sudo fail2ban-client status
sudo fail2ban-client status sshd
sudo fail2ban-client get sshd actions
```

```
Status
|- Number of jail:	1
`- Jail list:	sshd
Status for the jail: sshd
|- Filter
|  |- Currently failed:	3
|  |- Total failed:	1874
|  `- Journal matches:	_SYSTEMD_UNIT=sshd.service + _COMM=sshd
`- Actions
   |- Currently banned:	12
   |- Total banned:	241
   `- Banned IP list:	203.0.113.45 203.0.113.77 198.51.100.23 198.51.100.61 ...
The jail sshd has the following actions:
nftables
```

→ The jail reads the journal (it matches on `_COMM=sshd`, so it works even though the Ubuntu unit
is called `ssh.service`), and it has banned 241 sources. If "Total failed" stayed at 0 while
`journalctl -u ssh` filled with failures, the filter would not be matching; test it with
`fail2ban-regex`. On OpenSSH 9.8 and later (Ubuntu 25.04 onwards, not 22.04 or 24.04) the
per-connection process is `sshd-session`, so check that your fail2ban release's sshd filter matches
it (`sudo fail2ban-client get sshd journalmatch`).

**Hands-on lab (test VM only)**

**Step 1 — Build a jail with a safe ignore list.**

```bash
sudo tee /etc/fail2ban/jail.d/sshd.local >/dev/null <<'EOF'
[DEFAULT]
ignoreip = 127.0.0.1/8 ::1 192.168.56.1
bantime = 1h
bantime.increment = true
findtime = 10m
maxretry = 5
banaction = nftables

[sshd]
enabled = true
backend = systemd
EOF
sudo systemctl restart fail2ban
sudo fail2ban-client status sshd
```

On early Ubuntu 24.04 package builds, fail2ban failed to start with a Python `ModuleNotFoundError`
(the `asynchat` module was removed from Python 3.12); `sudo apt-get install --only-upgrade
fail2ban` fixes it. `journalctl -u fail2ban -n 30` shows that error if you hit it.

**Step 2 — Break it: ban your own scan host.** From sec-scan, fail to log in six times with a
user that does not exist:

```bash
for i in $(seq 1 6); do ssh -o BatchMode=yes -o ConnectTimeout=3 nosuchuser@192.168.56.21; done
ssh -o ConnectTimeout=3 alice@192.168.56.21
```

```
nosuchuser@192.168.56.21: Permission denied (publickey).
...
ssh: connect to host 192.168.56.21 port 22: Connection timed out
```

→ After the fifth failure the next connection times out: fail2ban dropped sec-scan's packets.
This is exactly what happens when a colleague's script with a wrong key runs from the office
NAT address and locks the whole office out.

**Step 3 — Fix it: find, unban, prevent.**

```bash
sudo fail2ban-client status sshd | grep 'Banned IP'
sudo nft list table inet f2b-table
sudo fail2ban-client set sshd unbanip 192.168.56.22
```

Prevent it by adding trusted sources (your VPN subnet, monitoring hosts, the office NAT) to
`ignoreip`, and by fixing the script rather than raising `maxretry`.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Admin IP banned | SSH times out from one place, works from another | `sudo fail2ban-client status sshd` | [SSH & remote access](09-ssh-remote-access.md) |
| Filter does not match the log format | attacks in the log, "Total failed: 0" | `sudo fail2ban-regex systemd-journal sshd` | [Logs & journal](06-logs-journal.md) |
| Service will not start | `fail2ban.service` failed after an upgrade | `journalctl -u fail2ban -n 30` | [Services & systemd](07-services-systemd.md) |
| Bans in a different firewall than you check | `ufw status` looks clean but traffic is dropped | `sudo nft list ruleset | grep -A5 f2b` | section 3 |

**Why it matters for troubleshooting.** "Connection timed out from one network only" has a short
list of causes, and an automatic ban is high on it. Knowing that fail2ban writes its own
nftables table, separate from UFW's, saves an hour of staring at a clean `ufw status`.

**Next step:** close the vulnerabilities attackers would use, automatically.

### Automatic security updates

**Level:** [L1 · Junior]

**Concept.** Most successful attacks use known vulnerabilities that already have a fix. The
cheapest control in this whole module is installing security updates automatically. Ubuntu ships
**unattended-upgrades** enabled by default for the security pocket; your job is to confirm it is
still on, decide what happens about reboots and daemon restarts, and keep risky packages (the
Docker engine on a Swarm node) for planned windows.

Precisely: two systemd timers drive it. `apt-daily.timer` refreshes package lists,
`apt-daily-upgrade.timer` runs `unattended-upgrade`, which installs upgrades from the
**allowed origins** in `/etc/apt/apt.conf.d/50unattended-upgrades`, switched on by
`/etc/apt/apt.conf.d/20auto-upgrades`. Kernel and libc updates need a reboot to take effect, and
library updates need the services using them restarted (`needrestart` handles that on Ubuntu).

**Key terms**

| Term | Meaning |
|---|---|
| Allowed origins | repositories u-u may install from; by default Ubuntu's security pocket and ESM |
| `Package-Blacklist` | packages u-u must never upgrade automatically |
| `/var/run/reboot-required` | created when an installed update needs a reboot; `.pkgs` lists which |
| needrestart | checks which services still use old libraries and restarts them |
| ESM | Expanded Security Maintenance, via Ubuntu Pro (free for a few personal machines) |
| `dnf-automatic` | the RHEL equivalent, with `upgrade_type = security` |

**See it on a real system**

```bash
cat /etc/apt/apt.conf.d/20auto-upgrades
systemctl list-timers 'apt-daily*' --no-pager
sudo tail -n 8 /var/log/unattended-upgrades/unattended-upgrades.log
cat /var/run/reboot-required.pkgs 2>/dev/null
```

```
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
NEXT                        LEFT     LAST                        PASSED  UNIT                    ACTIVATES
Sat 2026-10-03 06:21:44 UTC 19h left Fri 2026-10-02 06:12:09 UTC 4h ago  apt-daily-upgrade.timer apt-daily-upgrade.service
Sat 2026-10-03 07:55:10 UTC 21h left Fri 2026-10-02 08:31:52 UTC 2h ago  apt-daily.timer         apt-daily.service
2026-10-02 06:12:31,507 INFO Starting unattended upgrades script
2026-10-02 06:12:31,508 INFO Allowed origins are: o=Ubuntu,a=noble, o=Ubuntu,a=noble-security, o=UbuntuESMApps,a=noble-apps-security, o=UbuntuESM,a=noble-infra-security
2026-10-02 06:12:31,508 INFO Initial blacklist: docker-ce docker-ce-cli containerd.io
2026-10-02 06:12:31,508 INFO Initial whitelist (not strict):
2026-10-02 06:12:37,140 INFO Packages that will be upgraded: libssl3t64 linux-generic linux-headers-generic linux-image-generic openssl
2026-10-02 06:12:37,140 INFO Writing dpkg log to /var/log/unattended-upgrades/unattended-upgrades-dpkg.log
2026-10-02 06:13:02,661 INFO All upgrades installed
linux-image-6.8.0-49-generic
```

→ Updates run daily, OpenSSL and a new kernel were installed this morning (u-u lists the kernel
metapackages; the new `linux-image-6.8.0-49-generic` comes in as their dependency), and the Docker
packages are deliberately held back for a patch window. The new kernel is not running yet:
`reboot-required.pkgs` names it, and `uname -r` would still show the old version.

**Hands-on lab (test VM only)**

**Step 1 — Build: confirm, configure reboots and holds.** Edit
`/etc/apt/apt.conf.d/50unattended-upgrades` (keep the shipped file, change only these lines):

```
Unattended-Upgrade::Package-Blacklist {
    "docker-ce";
    "docker-ce-cli";
    "containerd.io";
};
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Mail "ops@example.com";
Unattended-Upgrade::MailReport "on-change";
```

Docker packages come from Docker's own repository, which is not an allowed origin anyway, but
the explicit hold documents the decision. The reason: upgrading the engine restarts `dockerd`,
and on a Swarm node such as Dokploy every container restarts with it (`live-restore` does not
work in Swarm mode). Leave `Automatic-Reboot` off on servers people depend on, and reboot in the
patch window instead (section 11). Then dry-run:

```bash
sudo unattended-upgrade --dry-run --debug 2>&1 | grep -E 'Allowed origins|Packages that will be upgraded|blacklist'
```

**Step 2 — Break it: a "tuned" golden image.** Simulate someone disabling updates in the image
to "avoid surprises":

```bash
sudo sed -i 's/Unattended-Upgrade "1"/Unattended-Upgrade "0"/' /etc/apt/apt.conf.d/20auto-upgrades
apt-config dump | grep -E 'Periodic::(Update-Package-Lists|Unattended-Upgrade)'
```

```
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "0";
```

→ Nothing errors, nothing alerts, and the log simply stops growing. Months later a scanner
shows 40 fixable CVEs on this host.

**Step 3 — Fix it and make the failure visible.** Restore `"1"`, then add a monitoring check
that alerts when the u-u log has not changed for more than three days (for example a
node_exporter textfile metric holding the log's modification time, from
[Observability](32-learn-performance-observability.md)). A control you cannot see failing is a
control you do not have.

**RHEL/Rocky difference:** `sudo dnf install dnf-automatic`, set `upgrade_type = security` and
`apply_updates = yes` in `/etc/dnf/automatic.conf`, then `sudo systemctl enable --now
dnf-automatic.timer`. `needs-restarting -r` replaces `/var/run/reboot-required`.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Updates disabled or timer stopped | log not updated for days | `systemctl list-timers 'apt-daily*'` | [Packages](11-packages.md) |
| dpkg lock held or interrupted upgrade | `Could not get lock /var/lib/dpkg/lock-frontend` | `sudo lsof /var/lib/dpkg/lock-frontend` | [Packages](11-packages.md) |
| Kernel installed, never rebooted | scanners still flag the kernel CVE | `uname -r`, `cat /var/run/reboot-required.pkgs` | section 11 |
| Docker engine upgraded unplanned | every container restarted at 06:12 | `grep docker /var/log/apt/history.log` | [Containers playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting.** When several services restart at the same minute in the
early morning, check `/var/log/apt/history.log` and the u-u log before anything else: an
automatic upgrade with a library restart is a very common "mystery restart". Knowing the timers
and logs turns it into a one-command answer.

**Next step:** measure the file-permission state of the host.

### File permissions and SUID audit

**Level:** [L1 · Junior] for the checks, [L2 · Mid] for baselines

**Concept.** File modes are the oldest security control on Linux and still one of the most
important. Three classes of problem matter. **Sensitive files readable by too many** (private
keys, `.env` files, `/etc/shadow`). **Writable by too many** (world-writable scripts that root
runs from cron are a privilege escalation). **SUID/SGID binaries** that run with their owner's
privileges whoever starts them: a few are needed (`sudo`, `passwd`), any unexpected one is either
a misconfiguration or a backdoor.

Precisely: the setuid bit (`s` in the owner execute position, octal 4000) makes the process run
with the file owner's effective UID. **File capabilities** are the finer-grained modern
alternative (`cap_net_raw` on `ping`), and they need auditing the same way.

| File or directory | Expected on Ubuntu | Why |
|---|---|---|
| `/etc/shadow` | `640 root:shadow` | password hashes |
| `/etc/sudoers`, `/etc/sudoers.d/*` | `440 root:root` | sudo refuses world-writable files |
| `/etc/ssh/ssh_host_*_key` | `600 root:root` | host identity |
| `~/.ssh` and `authorized_keys` | `700` and `600`, owned by the user | sshd ignores keys otherwise |
| TLS private keys | `600 root:root` or `640 root:ssl-cert` | the server's identity |
| `/var/run/docker.sock` | `660 root:docker` | root-equivalent API |
| `acme.json` (Traefik) | `600` | Traefik refuses to use it otherwise ("permissions ... are too open, please use 600"), so ACME certificates stop working |

**Key terms**

| Term | Meaning |
|---|---|
| SUID / SGID | run as file owner / group; `-perm -4000` / `-perm -2000` in `find` |
| Sticky bit | on a directory (`/tmp`, mode 1777), only the owner can delete their files |
| `nosuid`, `nodev`, `noexec` | mount options that disable those features on a filesystem |
| File capability | a single root power attached to a binary; shown by `getcap` |
| umask | default mode mask for new files; 022 gives 644/755, 027 gives 640/750 |

**See it on a real system**

```bash
sudo find / -xdev \( -perm -4000 -o -perm -2000 \) -type f -printf '%m %u:%g %p\n' 2>/dev/null | sort -k3
sudo getcap -r / 2>/dev/null
sudo find / -xdev -type f -perm -0002 ! -path '/proc/*' ! -path '/sys/*' 2>/dev/null | head
sudo find / -xdev \( -nouser -o -nogroup \) 2>/dev/null | head
for m in /tmp /dev/shm; do findmnt -no TARGET,OPTIONS "$m"; done   # one mount point per call
```

```
2755 root:shadow /usr/bin/chage
4755 root:root /usr/bin/chfn
4755 root:root /usr/bin/chsh
2755 root:crontab /usr/bin/crontab
2755 root:shadow /usr/bin/expiry
4755 root:root /usr/bin/fusermount3
4755 root:root /usr/bin/gpasswd
4755 root:root /usr/bin/mount
4755 root:root /usr/bin/newgrp
4755 root:root /usr/bin/passwd
4755 root:root /usr/bin/su
4755 root:root /usr/bin/sudo
4755 root:root /usr/bin/umount
4754 root:messagebus /usr/lib/dbus-1.0/dbus-daemon-launch-helper
4755 root:root /usr/lib/openssh/ssh-keysign
4755 root:root /usr/local/bin/.cache-helper
2755 root:shadow /usr/sbin/unix_chkpwd
/usr/bin/ping cap_net_raw=ep
/usr/bin/mtr-packet cap_net_raw=ep
/opt/app/run-backup.sh
/dev/shm rw,nosuid,nodev,inode64
```

→ Every SUID file is a known Ubuntu binary except `/usr/local/bin/.cache-helper`: a hidden
name, SUID root, in a directory no package owns. That is how an attacker keeps root after the
first break-in. `/opt/app/run-backup.sh` is world-writable, so if root's cron runs it, anyone on
the box can become root. `/tmp` printed nothing because it is not a separate mount here (CIS
recommends making it one with `nosuid,nodev,noexec`).

**Hands-on lab (test VM only)**

**Step 1 — Build a baseline.** Save the SUID/SGID list and capabilities from a clean VM:

```bash
sudo find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null | sort > ~/suid-baseline.txt
sudo getcap -r / 2>/dev/null | sort > ~/caps-baseline.txt
```

**Step 2 — Break it: plant a SUID shell, exactly as an attacker would.**

```bash
sudo cp /bin/bash /usr/local/bin/.cache-helper
sudo chmod 4755 /usr/local/bin/.cache-helper
sudo -u nobody /usr/local/bin/.cache-helper -p -c 'id'
```

```
uid=65534(nobody) gid=65534(nogroup) euid=0(root) groups=65534(nogroup)
```

→ `euid=0`: any user, or any compromised web app, now has root. (`-p` stops bash from dropping
the elevated privilege, which it does by default.)

**Step 3 — Detect and fix.** Diff against the baseline, identify the owner package, remove what
no package owns:

```bash
sudo find / -xdev \( -perm -4000 -o -perm -2000 \) -type f 2>/dev/null | sort | diff ~/suid-baseline.txt -
dpkg -S /usr/local/bin/.cache-helper
sudo rm /usr/local/bin/.cache-helper
```

```
15a16
> /usr/local/bin/.cache-helper
dpkg-query: no path found matching pattern /usr/local/bin/.cache-helper
```

On a real server, do **not** delete it first: copy it and its timestamps as evidence
(section 13), then remove it. Run the diff daily from cron or your monitoring, and alert on any
new line; that is cheap, effective intrusion detection.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Private key too open | Traefik ignores `acme.json` or sshd ignores the key, "permissions ... too open" | `stat -c '%a %U:%G' FILE` | [Users & permissions](10-users-permissions-security.md) |
| Unexpected SUID binary | new line in the daily SUID diff | `dpkg -S FILE`, `stat FILE` | section 13 |
| `noexec` on `/tmp` breaks installers | `Permission denied` running a script from `/tmp` | `findmnt -no OPTIONS /tmp` | [Users & permissions](10-users-permissions-security.md) |
| World-writable script run by root | (silent) privilege escalation path | `find / -xdev -perm -0002 -type f` | this topic |

**Why it matters for troubleshooting.** Permission and mount-option problems produce the same
"Permission denied" whether you caused them by hardening or an attacker exploited them. The
`namei -l` and `stat` habits from [Users & permissions](10-users-permissions-security.md) plus a
known-good baseline let you tell "too strict" from "tampered with" in a minute.

**Next step:** record who changed what, with auditd.

### auditd basics

**Level:** [L2 · Mid]

**Concept.** The kernel audit system records security-relevant events (file writes, executed
commands, syscalls, logins) with the identity of the person behind them. `auditd` writes them to
`/var/log/audit/audit.log`. Its most valuable field is **auid**, the login UID: it is set when a
user logs in and **survives `sudo` and `su`**, so a command run as root still names the human who
ran it. Normal logs cannot do that.

Precisely: rules are loaded from `/etc/audit/rules.d/*.rules` by `augenrules`. **Watch rules**
(`-w PATH -p rwxa -k KEY`) record access to a file or directory. **Syscall rules**
(`-a always,exit -F arch=b64 -S SYSCALL ... -k KEY`) record specific syscalls with filters. The
`-k` key is a label you search for later. Detection-oriented rules are in section 12; this topic
gets auditd running and readable.

**Key terms**

| Term | Meaning |
|---|---|
| auid | audit (login) UID; shows `unset` (4294967295) for daemons started at boot |
| `-p rwxa` | permissions to watch: read, write, execute, attribute change |
| `ausearch -k KEY -i` | search by key; `-i` interprets numbers into names |
| `aureport` | summaries: logins, executables, failed events |
| `-e 2` | immutable mode; rules cannot change until reboot (put it last) |

**See it on a real system**

```bash
sudo auditctl -s                      # status: enabled, lost events, backlog
sudo auditctl -l                      # loaded rules
sudo ausearch -k sudoers -i --start today | tail -n 6
```

```
enabled 1
failure 1
pid 731
rate_limit 0
backlog_limit 8192
lost 0
backlog 0
backlog_wait_time 60000
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d -p wa -k sudoers
----
type=PROCTITLE msg=audit(10/02/2026 14:03:11.204:812) : proctitle=vi /etc/sudoers
type=PATH msg=audit(10/02/2026 14:03:11.204:812) : item=1 name=/etc/sudoers inode=1311 dev=fd:00 mode=file,440 ouid=root ogid=root rdev=00:00 nametype=NORMAL
type=CWD msg=audit(10/02/2026 14:03:11.204:812) : cwd=/root
type=SYSCALL msg=audit(10/02/2026 14:03:11.204:812) : arch=x86_64 syscall=openat success=yes exit=3 a0=AT_FDCWD a1=0x55d0c3e1a2b0 a2=O_WRONLY|O_CREAT|O_TRUNC a3=0x1b6 items=2 ppid=2211 pid=2240 auid=alice uid=root gid=root euid=root suid=root fsuid=root egid=root sgid=root fsgid=root tty=pts1 ses=7 comm=vi exe=/usr/bin/vim.basic subj=unconfined key=sudoers
```

→ Someone opened `/etc/sudoers` for writing with `vi` as root, bypassing `visudo`. The
`auid=alice` field says it was alice, even though `uid=root`. `lost 0` confirms no events were
dropped; a growing `lost` count means your rules are too noisy for the backlog.

**Hands-on lab (test VM only)**

**Step 1 — Build a small identity rule set.**

```bash
sudo tee /etc/audit/rules.d/30-identity.rules >/dev/null <<'EOF'
-w /etc/passwd -p wa -k identity
-w /etc/group -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k sudoers
-w /etc/sudoers.d -p wa -k sudoers
-w /etc/ssh/sshd_config -p wa -k sshd_config
-w /etc/ssh/sshd_config.d -p wa -k sshd_config
EOF
sudo augenrules --load
sudo auditctl -l | grep -c -- '-k'
```

**Step 2 — Generate events and read them.**

```bash
sudo useradd -M -s /usr/sbin/nologin audittest
sudo ausearch -k identity -i --start recent | grep -E 'type=(SYSCALL|PROCTITLE)' | tail -n 4
sudo aureport -k --summary
```

**Step 3 — Break it: make the rules immutable, then try to change them.** Add `-e 2` as the
last line of a file named `99-finalize.rules`, run `sudo augenrules --load`, then try
`sudo auditctl -D` (delete all rules):

```
Error deleting rule (Operation not permitted)
The audit system is in immutable mode, no rule changes allowed
```

→ That is the point of immutable mode: an attacker with root cannot quietly switch auditing off
without a reboot, and a reboot is itself an event you can alert on.

**Step 4 — Fix it (lab only).** Remove `99-finalize.rules` and reboot the VM to leave
immutable mode. In production, keep `-e 2` and plan rule changes with a reboot.

**RHEL/Rocky difference:** auditd is installed and enabled by default, the service is restarted
with `sudo service auditd restart` (systemctl refuses to restart it by design), and SELinux
denials land in the same log as `type=AVC`.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Too many rules (execve on a busy host) | `lost` counter rising, high CPU in `kauditd` | `sudo auditctl -s` | [CPU & performance](03-cpu-performance.md) |
| Audit log fills the disk | `/var/log/audit` large, auditd may halt the system if configured to | `sudo du -sh /var/log/audit` | [Storage & disk](01-storage-disk.md) |
| Rules not loaded after reboot | `auditctl -l` shows "No rules" | `sudo augenrules --check` | [Logs & journal](06-logs-journal.md) |

**Why it matters for troubleshooting.** auditd answers "who changed this file?" and "what ran
right before it broke?", which the journal often cannot. When a config file changes and nobody
admits it, `ausearch -f FILE -i` settles it in seconds.

**Next step:** measure the whole host against a published standard.

### CIS benchmarks and Lynis

**Level:** [L2 · Mid]

**Concept.** Hardening by opinion never ends ("should we disable IPv6?"). A **benchmark** turns
it into a checklist with reasons. The [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks)
are consensus hardening guides for each OS and for Docker and Kubernetes, with **Level 1**
(sensible for nearly every server) and **Level 2** (stricter, may break things) profiles.
**Lynis** is an open-source auditing tool that runs a few hundred checks, prints warnings and
suggestions, and gives a **hardening index** from 0 to 100 that you can track over time.

Precisely: Lynis is not a CIS implementation; it is a broad auditor whose score is useful as a
*trend* on your own fleet, not as a number to compare between companies. For formal CIS
compliance on Ubuntu, Ubuntu Pro includes the **Ubuntu Security Guide** (`usg audit
cis_level1_server`), and OpenSCAP covers RHEL. A benchmark item that breaks your workload becomes
a documented **exception**, never a silent skip.

**Key terms**

| Term | Meaning |
|---|---|
| Hardening index | Lynis score; higher is better, track it per host over time |
| Test ID | e.g. `SSH-7408`, `AUTH-9286`, `KRNL-6000`; used to look up or skip a check |
| Warning vs suggestion | warnings need action; suggestions are improvements |
| Profile | `/etc/lynis/default.prf`; put overrides and `skip-test=` lines in `custom.prf` |
| Exception | a benchmark item you deliberately do not apply, with reason, owner, review date |

**See it on a real system**

```bash
sudo lynis audit system --quick 2>/dev/null | sed -n '/Warnings/,/Lynis security scan details/p' | head -n 30
sudo grep -E '^(hardening_index|warning\[\])' /var/log/lynis-report.dat
```

```
  Warnings (1):
  ----------------------------
  ! Found one or more vulnerable packages. [PKGS-7392]

  Suggestions (41):
  ----------------------------
  * Set a password on GRUB boot loader to prevent altering boot configuration [BOOT-5122]
  * Install a PAM module for password strength testing like pam_cracklib or pam_passwdqc [AUTH-9262]
  * Configure minimum password age in /etc/login.defs [AUTH-9286]
  * Default umask in /etc/login.defs could be more strict like 027 [AUTH-9328]
  * Consider hardening SSH configuration [SSH-7408]
      - Details  : AllowTcpForwarding (set YES to NO)
  * Enable process accounting [ACCT-9622]
  * Enable sysstat to collect accounting (no results) [ACCT-9626]
  * Audit daemon is enabled with an empty ruleset. Disable the daemon or define rules [ACCT-9630]
  * One or more sysctl values differ from the scan profile and could be tweaked [KRNL-6000]
  ...
  Lynis security scan details:

  Hardening index : 61 [############        ]
  Tests performed : 271
hardening_index=61
warning[]=PKGS-7392|Found one or more vulnerable packages.|-|-|
```

→ A fresh Ubuntu 24.04 server typically scores in the low 60s. The one warning (vulnerable
packages) is fixed by patching; most suggestions map to topics in this area. Each suggestion
also prints a link to the control's description on the Lynis site.

**Hands-on lab (test VM only)**

The full walkthrough is the next topic, "Lab: harden a VM to a Lynis target". Before it, do this
short break-and-fix to learn the most important lesson about benchmarks.

**Step 1 — Apply a benchmark item blindly.** CIS recommends disabling IP forwarding on hosts that
are not routers. Apply it on sec-target, which runs Docker:

```bash
echo 'net.ipv4.ip_forward = 0' | sudo tee /etc/sysctl.d/60-cis-forwarding.conf
sudo sysctl --system >/dev/null
docker run --rm alpine wget -qO- -T 5 http://example.com >/dev/null && echo OK || echo FAILED
```

```
wget: download timed out
FAILED
```

→ Containers on bridge networks reach the outside through the host's routing, so with
forwarding off, every container loses outbound connectivity. (Depending on whether the DNS lookup
or the connection fails first, BusyBox prints `bad address 'example.com'` instead of `download timed
out`; both mean the same here.) Dokploy apps would fail health
checks, pulls from Harbor inside builds would fail, and the cause would be a "security
improvement" made a week earlier.

**Step 2 — Fix it and document the exception.**

```bash
sudo rm /etc/sysctl.d/60-cis-forwarding.conf
sudo sysctl -w net.ipv4.ip_forward=1
echo '# Docker/Swarm host: forwarding required for container networking. Owner: ops. Review: 2027-04.' \
  | sudo tee -a /etc/lynis/custom.prf
```

A benchmark is a list of questions, not a list of answers. Container hosts, Kubernetes nodes
and routers legitimately differ from a generic server.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Benchmark item breaks the workload | containers lose network, app logins fail | `sysctl net.ipv4.ip_forward`, recent changes | [Containers playbook](26-playbook-containers-k8s.md) |
| Score drops after a deploy | new suggestions in the Lynis diff | `diff` two `lynis-report.dat` files | this topic |
| Old Lynis from the Ubuntu archive | missing newer tests, wrong advice for 24.04 | `lynis show version` | [Packages](11-packages.md) |

**Why it matters for troubleshooting.** Hardening changes are changes. When an outage follows a
hardening ticket, the benchmark item that was applied is the prime suspect, and the "everything
broke right after a change" case from your Ops Ladder applies: roll back first, diagnose second.

**Next step:** put it all together on a fresh VM.

### Lab: harden a VM to a Lynis target

**Level:** [L2 · Mid] to do by hand, [L3 · Senior] to codify in Ansible

This is the required hardening lab. Target: take a fresh Ubuntu 24.04 VM from its baseline score
to **80 or more**, with **no warnings**, while Docker, a Traefik container and Apache on 81/444
keep working. Time: one evening by hand.

**Step 0 — Baseline and snapshot.**

```bash
sudo lynis audit system --quick >/dev/null 2>&1
sudo cp /var/log/lynis-report.dat ~/lynis-before.dat
grep hardening_index ~/lynis-before.dat
```

**Step 1 — Apply the baseline, one block at a time, re-running Lynis after each.** The deltas
below are typical, not guaranteed; Lynis weights vary by version.

| Block | What to do | Section | Typical gain |
|---|---|---|---|
| Patching | `sudo apt-get update && sudo apt-get full-upgrade -y`, reboot; confirm unattended-upgrades | 2 | clears PKGS-7392 warning, +2 |
| Accounts | named admin, lock `ubuntu`, remove NOPASSWD, `UMASK 027` in `/etc/login.defs` | 2 | +2 to +3 |
| SSH | `10-hardening.conf` from the SSH topic | 2 | +3 to +5 |
| Firewall | UFW default deny, allow 22 from lab subnet, 80/443 (section 3) | 3 | +2 |
| fail2ban | sshd jail from the fail2ban topic | 2 | +1 to +2 |
| auditd | identity rules plus section 12 rules | 2, 12 | +2 to +3 |
| Accounting | `sudo apt-get install -y acct sysstat` and enable sysstat | 2 | +1 to +2 |
| Kernel sysctls | the safe set below (not ip_forward on Docker hosts) | 2 | +2 to +4 |
| Integrity | `sudo apt-get install -y aide` and initialise it, or keep your SUID diff | 2 | +1 to +2 |
| Legal banner | text in `/etc/issue.net` and `Banner /etc/issue.net` in sshd | 2 | +1 |
| Remove surface | purge unused packages and services (cups, snapd if unused) | 1 | +1 to +2 |

A safe sysctl set for a Docker host:

```
# /etc/sysctl.d/60-hardening.conf
kernel.kptr_restrict = 2
kernel.dmesg_restrict = 1
kernel.yama.ptrace_scope = 1
fs.protected_fifos = 2
fs.protected_regular = 2
fs.suid_dumpable = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv6.conf.all.accept_redirects = 0
net.ipv4.tcp_syncookies = 1
```

Apply with `sudo sysctl --system`. `rp_filter = 1` (strict) can break asymmetric routing on
multi-homed hosts; use `2` (loose) if a host has several uplinks.

**Step 2 — Prove the workload still works.** After every block:

```bash
docker run --rm alpine wget -qO- -T 5 http://example.com >/dev/null && echo 'containers: OK'
curl -sk -o /dev/null -w 'apache 444: %{http_code}\n' https://127.0.0.1:444/
ssh -o BatchMode=yes alice@192.168.56.21 true && echo 'ssh: OK'     # from another machine
```

**Step 3 — Break it once on purpose.** Add `noexec` to `/tmp` (as many guides suggest) with a
temporary mount, then try an `apt-get` upgrade of a package with a maintainer script that uses
`/tmp`, or run a script from `/tmp`:

```bash
sudo mount -o remount,noexec /tmp 2>/dev/null || sudo mount -t tmpfs -o noexec,nosuid,nodev tmpfs /tmp
printf '#!/bin/sh\necho hello\n' > /tmp/t.sh && chmod +x /tmp/t.sh && /tmp/t.sh
```

```
-bash: /tmp/t.sh: Permission denied
```

Decide deliberately: keep `noexec` and point tools elsewhere (`APT::ExtractTemplates::TempDir`,
`TMPDIR` for build tools), or record an exception. Then `sudo umount /tmp` to undo the lab tmpfs
mount (if `/tmp` was already a separate mount and the remount succeeded, use
`sudo mount -o remount,exec /tmp` instead, so you do not unmount the real `/tmp`).

**Step 4 — Compare and record.**

```bash
sudo lynis audit system --quick >/dev/null 2>&1
grep hardening_index /var/log/lynis-report.dat
diff <(grep -E '^suggestion\[\]' ~/lynis-before.dat | cut -d'|' -f1 | sort) \
     <(grep -E '^suggestion\[\]' /var/log/lynis-report.dat | cut -d'|' -f1 | sort)
```

```
hardening_index=82
< suggestion[]=AUTH-9328
< suggestion[]=SSH-7408
< suggestion[]=ACCT-9622
...
```

Every remaining suggestion gets one of three labels in your notes: *fixed later* (with a date),
*exception* (with a reason, in `custom.prf`), or *not applicable*.

**Step 5 — Codify it ([L3 · Senior]).** Turn the blocks into an Ansible role (`hardening`) with
handlers for sshd and sysctl, run it against a fresh VM, and run Lynis in the same pipeline
with a threshold (`hardening_index >= 80` or the job fails). See
[CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md). A hardening standard that lives only in a wiki
drifts within months; one that runs in CI does not.

**Exit criteria:** score of 80 or more, zero warnings, all three workload checks pass, every
remaining suggestion labelled, snapshot taken as your "golden" baseline.

---

## 3. Network security

> 📚 **Study path:** 1) KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking: Configure Packet Filtering (Firewall) ([note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall)), then Port Redirection and NAT ([note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Port-Redirection-and-Network-Address-Translation-NAT/page)) · 2) Note: the UFW and nftables topic in [Learn Linux](27-learn-linux.md) and the networking areas of [Learn Docker](30-learn-docker.md) · 3) Docs: Docker *Packet filtering and firewalls* ([docs](https://docs.docker.com/engine/network/packet-filtering-firewalls/)) — KodeKloud does not cover Docker bypassing UFW · 4) Video: KodeKloud *How Docker Networking Actually Works* (9 min, [YouTube](https://www.youtube.com/watch?v=W7X6u2BGVRY)) · 5) Practice: the DOCKER-USER scenario below on sec-target, scanned from sec-scan; after the CKA, CKS *UFW Firewall Basics* ([note](https://notes.kodekloud.com/docs/Certified-Kubernetes-Security-Specialist-CKS/System-Hardening/UFW-Firewall-Basics/page)).

The network is where most attacks start, and the cheapest control in this whole module is
making sure that only the ports you meant to expose answer. On your stack that means: 80 and 443
to the world (Traefik), SSH and admin UIs only from an admin network or a VPN, Apache on 81/444
only from Traefik, and nothing else. This area teaches you to build that, to prove it from the
outside, and to find the one big hole that almost every Docker host has: published container
ports skip UFW.

### Host firewalls: UFW and nftables

**Level:** [L1 · Junior]

**Concept.** A host firewall decides which packets reach the processes on a machine. The safe
pattern is **default deny incoming, allow outgoing**, then one explicit allow rule per service
and source. On Ubuntu you write rules with **UFW**, a friendly front end; underneath, the kernel's
**netfilter** runs them, and on Ubuntu 22.04 and later the `iptables` commands that UFW calls are
themselves translated to **nftables** (`iptables-nft`).

Precisely, netfilter has hooks a packet passes through. Packets for a process on this host
(sshd, Apache) pass **INPUT**. Packets the host routes somewhere else, including into a container
on a Docker bridge, pass **FORWARD**. UFW's rules sit mostly in INPUT. Docker's rules sit in the
nat table's PREROUTING and in FORWARD. Keep this picture; the next topic depends on it.

```
 packet arrives on eth0
        │
   PREROUTING (nat) ── Docker DNAT for published ports ───────────┐
        │                                                         │
   for this host?                                                 ▼
        │ yes                                                  FORWARD
      INPUT  ◄── UFW rules (ufw-user-input)                   DOCKER-USER   ◄── your rules for containers
        │                                                     Docker's own chains
   sshd :22, Apache :81/:444                                  containers: Traefik :80/:443, UI :3000
```

**Key terms**

| Term | Meaning |
|---|---|
| Default policy | what happens to a packet no rule matched: `deny (incoming)`, `allow (outgoing)`, `deny (routed)` |
| `allow` / `deny` / `reject` / `limit` | accept; drop silently (client times out); refuse (client gets "refused"); accept but rate-limit new connections |
| `ufw route` | rules for forwarded traffic (FORWARD), as opposed to traffic for the host itself |
| conntrack | the kernel's connection table; replies to allowed connections are accepted as `ESTABLISHED` |
| Dead-man switch | a scheduled automatic rollback, cancelled only after you confirm you still have access |

**See it on a real system**

```bash
sudo ufw status verbose
sudo iptables -V
sudo nft list ruleset | grep -E '^\s*(table|chain) ' | head -n 12
```

```
Status: active
Logging: on (low)
Default: deny (incoming), allow (outgoing), deny (routed)
New profiles: skip

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW IN    192.168.56.0/24            # SSH from admin net
80,443/tcp                 ALLOW IN    Anywhere                   # public web
81,444/tcp                 ALLOW IN    172.16.0.0/12              # Traefik to Apache
81,444/tcp                 DENY IN     Anywhere
80,443/tcp (v6)            ALLOW IN    Anywhere (v6)              # public web
81,444/tcp (v6)            DENY IN     Anywhere (v6)

iptables v1.8.10 (nf_tables)
table ip filter {
	chain INPUT {
	chain FORWARD {
	chain OUTPUT {
	chain ufw-before-logging-input {
	chain ufw-before-input {
	chain ufw-user-input {
	chain DOCKER {
	chain DOCKER-USER {
table ip nat {
	chain PREROUTING {
	chain DOCKER {
```

→ Default deny incoming, SSH only from the admin network, the web ports public, Apache's
internal ports only from Docker's address range. `(nf_tables)` confirms that UFW's iptables
rules are really nftables rules, which is why `nft list ruleset` shows UFW's chains and Docker's
chains side by side in the same `ip filter` table. That shared table is where the surprises of
the next topic come from.

**Hands-on lab (test VM only)**

**Step 1 — Build with a dead-man switch.** Before enabling a firewall over SSH, schedule its
rollback. If you lock yourself out, it disables itself five minutes later.

```bash
sudo apt-get install -y at
echo 'ufw --force disable' | sudo at now + 5 minutes        # the dead-man switch
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow from 192.168.56.0/24 to any port 22 proto tcp comment 'SSH from admin net'
sudo ufw allow 80,443/tcp comment 'public web'
sudo ufw --force enable
# in a NEW terminal: ssh alice@192.168.56.21 true && echo still-in
sudo atq                                                   # shows the job number, e.g. 3
sudo atrm 3                                                # cancel the rollback only after the new login worked
```

**Step 2 — Break it: lock yourself out on purpose.** Schedule the dead-man switch again, then
"move" SSH to a VPN subnet that does not exist yet:

```bash
echo 'ufw --force disable' | sudo at now + 5 minutes
sudo ufw delete allow from 192.168.56.0/24 to any port 22 proto tcp
sudo ufw allow from 10.8.0.0/24 to any port 22 proto tcp comment 'SSH from VPN only'
```

Your current session survives (its packets are `ESTABLISHED`), but a new `ssh` from your
workstation now times out. That is the classic remote lockout: everything looks fine until you
disconnect. Wait for the `at` job, and UFW switches off by itself.

**Step 3 — Fix and verify.** Re-add the admin-network rule *before* removing anything, list the
rules with numbers, and test from a new terminal before cancelling the switch:

```bash
sudo ufw allow from 192.168.56.0/24 to any port 22 proto tcp comment 'SSH from admin net'
sudo ufw --force enable
sudo ufw status numbered
```

`ufw insert 1 RULE` puts a rule at the top when order matters; `ufw delete NUMBER` removes one.

**RHEL/Rocky difference:** the front end is **firewalld** with zones:
`sudo firewall-cmd --list-all`, `sudo firewall-cmd --permanent --add-service=https`, then
`sudo firewall-cmd --reload`. Docker integrates with firewalld through its own `docker` zone.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| SSH rule removed or wrong source | new SSH connections time out, old ones keep working | `sudo ufw status numbered` (from the console) | [SSH & remote access](09-ssh-remote-access.md) |
| `deny` placed after an `allow` that matches first | port still reachable | `sudo ufw status numbered` | this topic |
| UFW enabled before allowing 80/443 | site down right after "hardening" | `sudo ufw status`, `curl -I` from outside | [Site down playbook](25-playbook-site-down.md) |
| Packets dropped, nothing in UFW explains it | timeouts from one place only | `sudo nft list ruleset | grep -B2 -A5 drop` (fail2ban, Docker) | [Network](02-network.md) |

**Why it matters for troubleshooting.** "Connection timed out" is a firewall drop until proven
otherwise, and "connection refused" means a packet reached a host that answered. Reading UFW and
the nftables ruleset under it tells you which firewall dropped the packet, and the dead-man habit
means a firewall change can never become an outage you cannot reach.

**Next step:** see why this firewall does not protect your containers.

### Docker bypasses UFW

**Level:** [L2 · Mid]

**Concept.** When you publish a container port (`-p 3000:3000`, or `ports:` in Compose), Docker
adds a **DNAT** rule in the nat table that rewrites the packet's destination to the container's
private address *before* the filter rules run. The rewritten packet is no longer for the host, so
it goes through **FORWARD**, not INPUT, and UFW's INPUT rules never see it. `ufw deny 3000` is
accepted, shows up in `ufw status`, and changes nothing. Your Dokploy host has exactly this
exposure on port 3000 (the Dokploy UI) unless someone dealt with it.

Precisely, Docker gives you one supported place for your own rules on forwarded traffic: the
**DOCKER-USER** chain, which FORWARD evaluates before Docker's own rules. Because DNAT already
happened, the destination port in the packet is the *container* port; to match the port the
client actually connected to, use conntrack's original destination
(`-m conntrack --ctorigdstport 3000 --ctdir ORIGINAL`). Your options, best first:

1. **Do not publish.** Containers behind Traefik only need to be on `dokploy-network`; Traefik reaches them over the overlay. No published port, no exposure.
2. **Publish on a specific address**, such as `-p 127.0.0.1:3000:3000` for something you reach through an SSH tunnel, or a VPN interface address.
3. **Filter in DOCKER-USER** when a port must be published but only some sources may use it.

Two version notes. Docker Engine 28 added rules that stop hosts on the same LAN segment from
reaching container bridge addresses directly, a hole older engines had; keep engines current.
Recent engines also offer an experimental **nftables backend**, and with it there is no
DOCKER-USER chain; the Docker docs page on packet filtering describes the replacement. Check which
backend your engine uses before copying rules from the internet.

**Key terms**

| Term | Meaning |
|---|---|
| Published port | a host port forwarded to a container (`-p`, `ports:`); reachable from outside |
| Exposed port | documentation in the image (`EXPOSE`); opens nothing by itself |
| DNAT | destination NAT: rewrites the destination address and port of incoming packets |
| DOCKER-USER | filter chain Docker creates and never flushes, evaluated first for forwarded traffic |
| `--ctorigdstport` | conntrack match on the port the client originally connected to, before DNAT |
| `docker_gwbridge` | bridge that connects Swarm containers (Dokploy's) to the host; their host-mode published ports go through it |

**See it on a real system**

```bash
sudo ufw status | grep 3000
docker ps --format '{{.Names}}\t{{.Ports}}' | grep 3000
sudo iptables -t nat -L DOCKER -n | grep 'dpt:3000'
sudo iptables -L DOCKER-USER -n -v --line-numbers
```

```
3000/tcp                   DENY        Anywhere
dokploy.1.k3x9p	0.0.0.0:3000->3000/tcp
DNAT       tcp  --  0.0.0.0/0            0.0.0.0/0            tcp dpt:3000 to:172.18.0.4:3000
Chain DOCKER-USER (1 references)
num   pkts bytes target     prot opt in     out     source               destination
```

→ UFW claims 3000 is denied. Docker's DNAT rule rewrites every packet for port 3000 to the
Dokploy container at 172.18.0.4, so UFW's deny rule never runs. DOCKER-USER is empty, so nothing
else filters it either. (Engines older than 28.2.2 created DOCKER-USER with a single `RETURN` rule;
that is also "empty" in effect. Since 28.2.2 the chain starts truly empty, and an old `RETURN` rule
survives an upgrade only until the next reboot.)

### Scenario: port open despite ufw deny

**Level:** [L2 · Mid]. Lab version: on sec-target run `docker run -d --name admin-ui -p 3000:80 nginx:alpine`
as a stand-in for the Dokploy UI, and `sudo ufw deny 3000/tcp`.

**Step 1 — Confirm the exposure from outside**

**Goal:** prove what an outsider sees, independent of what any config file says.

```bash
# on sec-scan
nmap -Pn -p 22,80,443,3000 192.168.56.21
```

```
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
443/tcp  open  https
3000/tcp open  ppp
```

**What it means:** port 3000 is open from the network even though `ufw status` lists a deny
rule for it. (`ppp` is just nmap's historical name for port 3000; ignore the service column for
non-standard ports.)

**Why this step (now):** an outside scan is the only test that includes every layer at once.
Starting with config files would show you the rule you wrote, not the packet path; starting
with the scan tells you whether there is a problem at all.

**Next step:** if 3000 is `filtered` or `closed`, the firewall works; stop here and record the
scan as evidence. If it is `open` → Step 2.

**Step 2 — Find who publishes the port**

**Goal:** name the process or container behind the listener.

```bash
sudo ss -tlnp 'sport = :3000'
docker ps --format '{{.Names}}\t{{.Ports}}' | grep ':3000'
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      4096         0.0.0.0:3000      0.0.0.0:*     users:(("docker-proxy",pid=5120,fd=7))
admin-ui	0.0.0.0:3000->80/tcp
```

**What it means:** the listener is `docker-proxy`, so a container publishes the port, here
`admin-ui` mapping host 3000 to container 80. If the process were `apache2` or `sshd`, UFW would
be in the packet path and the problem would be rule order instead.

**Why this step (now):** the fix depends entirely on the owner. A host process is filtered by
INPUT (UFW works); a published container port is filtered by FORWARD (UFW does not). Two
read-only commands decide which world you are in.

**Next step:** if the owner is a host process → check rule order with `sudo ufw status numbered`
and the UFW topic above. If it is `docker-proxy` or a container → Step 3.

**Step 3 — Prove the packet path with counters**

**Goal:** show that packets hit Docker's DNAT rule and never reach UFW's deny rule.

```bash
# run nmap from sec-scan again, then on sec-target:
sudo iptables -t nat -L DOCKER -n -v | grep 'dpt:3000'
sudo iptables -L ufw-user-input -n -v | grep 'dpt:3000'
```

```
    4   240 DNAT       tcp  --  !docker0 *  0.0.0.0/0  0.0.0.0/0  tcp dpt:3000 to:172.17.0.2:80
    0     0 DROP       tcp  --  *        *  0.0.0.0/0  0.0.0.0/0  tcp dpt:3000
```

**What it means:** the DNAT rule's packet counter rose with your scan; UFW's DROP rule for 3000
has never matched a packet. The deny rule is real but sits on a path these packets do not take.

**Why this step (now):** counters turn a theory ("Docker bypasses UFW") into evidence for this
host and this port, which you will want in the ticket and the postmortem. It also rules out a
third firewall (cloud security group, upstream router) as the explanation.

**Next step:** if the DNAT counter does not rise, something upstream answers for this address
(check `ip -br addr` and any load balancer) → [Who owns this port?](22-playbook-ports-inventory.md).
If it rises as shown → Step 4.

**Step 4 — Choose the fix**

**Goal:** pick the narrowest fix that keeps the service working for the people who need it.

```bash
docker inspect admin-ui --format '{{json .HostConfig.PortBindings}}'
docker network ls --format '{{.Name}}\t{{.Driver}}\t{{.Scope}}'
```

```
{"80/tcp":[{"HostIp":"","HostPort":"3000"}]}
bridge	bridge	local
docker_gwbridge	bridge	local
dokploy-network	overlay	swarm
host	host	local
ingress	overlay	swarm
none	null	local
```

**What it means:** the binding has an empty `HostIp`, meaning every address. A
`dokploy-network` overlay exists, so Traefik could reach this container without any published
port at all.

**Why this step (now):** the three fixes have different costs. Removing the publication is the
strongest, binding to one address is next, DOCKER-USER filtering is the most flexible but also
the easiest to lose on reboot. Deciding before changing anything avoids stacking all three.

**Next step:** if only Traefik needs the service → remove the publication and route it through
Traefik ([Traefik in depth](29-learn-webservers-proxies.md)), then go to Step 6. If admins need
it directly and you have a VPN → publish on the VPN address only. If the port must stay published
for a set of sources (the Dokploy UI on 3000 is the usual case) → Step 5.

**Step 5 — Filter in DOCKER-USER, with a dead-man switch**

**Goal:** allow 3000 only from the admin network and drop it for everyone else.

```bash
ip route show default                                   # find the external interface name
echo 'iptables -F DOCKER-USER' | sudo at now + 5 minutes # dead-man switch
sudo iptables -I DOCKER-USER 1 -i eth0 -p tcp -m conntrack --ctorigdstport 3000 --ctdir ORIGINAL \
  ! -s 192.168.56.0/24 -j DROP
sudo iptables -L DOCKER-USER -n -v --line-numbers
```

```
default via 192.168.56.1 dev eth0 proto static
job 4 at Fri Oct  2 11:47:00 2026
Chain DOCKER-USER (1 references)
num   pkts bytes target     prot opt in     out     source               destination
1        0     0 DROP       tcp  --  eth0   *      !192.168.56.0/24      0.0.0.0/0            ctorigdstport 3000 ctdir ORIGINAL
```

**What it means:** traffic arriving on `eth0` for original port 3000 from anywhere outside the
admin network is dropped before Docker's own rules accept it. Traffic from the admin network, and
traffic between containers (which does not arrive on `eth0`), is untouched.

**Why this step (now):** you have proven the path and chosen the fix, so this is the first
change, and it is made on the chain Docker promises not to touch. The `at` job protects you if
the rule is wrong; matching on `-i eth0` keeps container-to-container traffic out of scope. If
the host has IPv6 enabled for Docker, repeat the rule with `ip6tables`.

**Next step:** → Step 6 to verify from both sides; if the verification fails, the dead-man
switch flushes the chain in five minutes.

**Step 6 — Verify from both sides and make it persistent**

**Goal:** prove outsiders are blocked, admins are not, and the rule survives a reboot.

```bash
# from a host OUTSIDE 192.168.56.0/24 (for the lab, add a second NIC or use a VPN address):
nmap -Pn -p 3000 192.168.56.21
# from the admin network:
curl -s -o /dev/null -w '%{http_code}\n' http://192.168.56.21:3000/
sudo atq && sudo atrm 4                                  # cancel the dead-man switch
```

```
PORT     STATE    SERVICE
3000/tcp filtered ppp
200
```

**What it means:** outsiders now see `filtered` (packets dropped), the admin network still gets
`200`. Now persist the rule; Docker never flushes DOCKER-USER, but rules added by hand are lost at
reboot. A small oneshot unit that runs after Docker is the simplest durable form:

```bash
sudo tee /usr/local/sbin/docker-user-firewall.sh >/dev/null <<'EOF'
#!/bin/sh
# Rules for published container ports. UFW does not see these packets.
set -eu
iptables -F DOCKER-USER
iptables -A DOCKER-USER -i eth0 -p tcp -m conntrack --ctorigdstport 3000 --ctdir ORIGINAL \
  ! -s 192.168.56.0/24 -j DROP
iptables -A DOCKER-USER -j RETURN
EOF
sudo chmod 750 /usr/local/sbin/docker-user-firewall.sh
sudo tee /etc/systemd/system/docker-user-firewall.service >/dev/null <<'EOF'
[Unit]
Description=Restrict published Docker ports (DOCKER-USER)
After=docker.service
Requires=docker.service
PartOf=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
ExecStart=/usr/local/sbin/docker-user-firewall.sh

[Install]
WantedBy=docker.service
EOF
sudo systemctl daemon-reload && sudo systemctl enable --now docker-user-firewall.service
```

**Why this step (now):** a fix that disappears at the next reboot or Docker upgrade is worse than
no fix, because everyone believes the port is closed. Re-scanning from outside after a reboot is
the only proof that counts.

**Next step:** reboot the lab VM and re-run the outside nmap. If 3000 is `filtered` → done; add
the scan to your weekly baseline (next topic). If it is `open` → `systemctl status
docker-user-firewall` and `journalctl -u docker-user-firewall` show why the unit did not run.

**Decision tree**

```
Port reachable from outside although "ufw deny" exists?
│
├─ owner is a host process (sshd, apache2)?
│     └─ yes → UFW is in the path → rule order / wrong source → ufw status numbered
│
└─ owner is docker-proxy / a container
      ├─ only Traefik needs it ──────────► remove the publication, route via Traefik
      ├─ only admins on a VPN need it ───► publish on the VPN or loopback address
      └─ must stay published ────────────► DOCKER-USER rule (+ persist + re-scan after reboot)
```

**Fix & verify:** outside scan shows `filtered`, admin network gets a response, the rule is
present after a reboot (`sudo iptables -L DOCKER-USER -n`), and the threat model row for this
port has the scan output as evidence.

**Rollback:** `sudo iptables -F DOCKER-USER` restores the previous behaviour immediately;
`sudo systemctl disable --now docker-user-firewall.service` stops it coming back at boot.

**Prevent it next time:** never publish ports for anything that sits behind Traefik; give the
Dokploy UI its own domain through Traefik and reach port 3000 only from the admin network or VPN;
keep the outside scan in a weekly job with `ndiff` (next topic) so a new published port is noticed
within days, not after an incident.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Published port ignores UFW | `nmap` shows open, `ufw status` shows deny | `sudo iptables -t nat -L DOCKER -n` | this topic |
| DOCKER-USER rule matches the container port, not the published one | rule never matches, port still open | `sudo iptables -L DOCKER-USER -n -v` (counters at 0) | this topic |
| DOCKER-USER rule too broad | containers lose internet or inter-host traffic | `sudo iptables -L DOCKER-USER -n -v`, test with `curl` from a container | [Containers playbook](26-playbook-containers-k8s.md) |
| Rules gone after reboot | port open again after maintenance | `systemctl status docker-user-firewall` | [Services & systemd](07-services-systemd.md) |
| Traefik cannot reach Apache on 81 | 504 from Traefik for legacy sites | `sudo ufw status | grep 81` (container → host traffic *does* pass UFW) | [Deployment patterns](35-deployment-patterns.md) |

**Why it matters for troubleshooting.** This is the most common "but the firewall says…" puzzle
on Docker hosts, and it cuts both ways: published ports are open despite UFW, while traffic from
a container to a host process (Traefik to Apache on 81) *is* filtered by UFW. Knowing which hook a
packet takes explains both in one sentence.

**Next step:** prove your whole exposure from the outside, regularly.

### Scanning your own servers with nmap

**Level:** [L1 · Junior] to run a scan, [L2 · Mid] to baseline and automate it

**Concept.** "Only 80 and 443 are public" is a hypothesis until a scanner outside the host agrees.
nmap sends probes and reports each port's state. Scan from more than one vantage point, because
each answers a different question: from the **internet** (what attackers see), from the **LAN**
(what a compromised neighbour sees), and from **the host itself** (what listens at all).

Precisely: `open` means something accepted the connection; `closed` means the host answered
with a reset (reachable, nothing listening); `filtered` means no answer (a firewall dropped it);
`open|filtered` is common for UDP, which rarely answers. A TCP **connect scan** (`-sT`, the default
without root) completes the handshake; a **SYN scan** (`-sS`, default with root) does not. `-Pn`
skips host discovery, which you need when ICMP is blocked.

> Scan only addresses you own or are authorised in writing to test, and tell the team first:
> intrusion detection and your provider may flag the scan. AWS permits scanning your own
> resources for most services without pre-approval; read its penetration-testing policy first.

**Key terms**

| Term | Meaning |
|---|---|
| `-p-` | all 65535 TCP ports (the default is the top 1000) |
| `-sV` | probe open ports for the service and version |
| `-sU --top-ports 50` | the most common UDP ports (slow; UDP needs patience) |
| `-oX FILE` | XML output, which `ndiff` compares between two scans |
| `ndiff` | prints what changed between two scans: new ports, closed ports, new versions |

**See it on a real system**

```bash
# from sec-scan: every TCP port, then versions for the open ones
sudo nmap -Pn -p- --min-rate 1000 192.168.56.21
sudo nmap -Pn -sV -p 22,80,443,8080 192.168.56.21
```

```
Starting Nmap 7.94SVN ( https://nmap.org ) at 2026-10-02 11:02 UTC
Nmap scan report for 192.168.56.21
Host is up (0.00041s latency).
Not shown: 65531 filtered tcp ports (no-response)
PORT     STATE SERVICE
22/tcp   open  ssh
80/tcp   open  http
443/tcp  open  https
8080/tcp open  http-proxy
MAC Address: 08:00:27:3A:91:C4 (Oracle VirtualBox virtual NIC)

Nmap done: 1 IP address (1 host up) scanned in 68.20 seconds

PORT     STATE SERVICE  VERSION
22/tcp   open  ssh      OpenSSH 9.6p1 Ubuntu 3ubuntu13.5 (Ubuntu Linux; protocol 2.0)
80/tcp   open  http     Golang net/http server
443/tcp  open  ssl/http Golang net/http server
8080/tcp open  http     Golang net/http server
```

→ 3000 is gone after the previous topic, but **8080** is open, served by the same Go program as
80/443: Traefik. That is the Traefik dashboard and API published to the network (section 9 closes
it). `-sV` also tells an attacker your exact OpenSSH package version, which is one reason patching
quickly matters.

**Hands-on lab (test VM only)**

**Step 1 — Baseline.** On sec-scan, store a dated full scan of sec-target:

```bash
sudo install -d -m 750 /var/lib/portscan
sudo nmap -Pn -p- --min-rate 1000 -oX /var/lib/portscan/sec-target-$(date +%F).xml 192.168.56.21 >/dev/null
```

**Step 2 — Break it: someone publishes a database "for a quick test".**

```bash
# on sec-target
docker run -d --name quicktest -e POSTGRES_PASSWORD=quicktest -p 5432:5432 postgres:16
```

**Step 3 — Detect it with ndiff.** Scan again and compare with the dated baseline file:

```bash
sudo nmap -Pn -p- --min-rate 1000 -oX /var/lib/portscan/sec-target-new.xml 192.168.56.21 >/dev/null
ndiff /var/lib/portscan/sec-target-2026-10-02.xml /var/lib/portscan/sec-target-new.xml
```

```
-Nmap 7.94SVN scan initiated Fri Oct 02 11:10:04 2026 as: nmap -Pn -p- --min-rate 1000 -oX ...
+Nmap 7.94SVN scan initiated Fri Oct 02 11:31:40 2026 as: nmap -Pn -p- --min-rate 1000 -oX ...

 192.168.56.21:
-Not shown: 65531 filtered tcp ports (no-response)
+Not shown: 65530 filtered tcp ports (no-response)
 PORT     STATE SERVICE VERSION
+5432/tcp open  postgresql
```

→ A database with a weak password, published to every network, found by a diff. Run this from
cron daily and send non-empty diffs to your alert channel; `ndiff` exits with status 1 when the
scans differ, which makes scripting easy.

**Step 4 — Fix.** Remove the container (`docker rm -f quicktest`); if a database must be
reachable, put it on a Docker network with its app and publish nothing. Re-scan and confirm the
diff is empty again.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Scan from inside the same firewall zone | "only 22/80/443" from the LAN, more from elsewhere | scan from a second vantage point | this topic |
| Rate too high on a fragile network | missed ports, IDS alerts | lower `--min-rate`, scan in a window | [Network speed](24-playbook-network-speed.md) |
| Everything `filtered`, even 443 | upstream firewall or the scanner's egress blocks it | `curl -v https://HOST` from the scanner | [Site down playbook](25-playbook-site-down.md) |
| New port nobody recognises | diff shows `+PORT open` | `sudo ss -tlnp 'sport = :PORT'` on the host | [Who owns this port?](22-playbook-ports-inventory.md) |

**Why it matters for troubleshooting.** The same scan answers "why can't users reach it?"
(`filtered` where you expected `open`) and "why can attackers reach it?" (`open` where you expected
`filtered`). A dated baseline also answers the most useful incident question of all: what changed?

**Next step:** reduce who can reach the management ports in the first place.

### Segmentation, bastions and WireGuard

**Level:** [L3 · Senior] for the design, [L2 · Mid] for setting up WireGuard

**Concept.** **Segmentation** splits systems into zones and allows only the flows that are
needed between them, so a compromised web container cannot talk to the database server's SSH
port. A **bastion** (jump host) is the single hardened way into the management zone. A **VPN**
such as **WireGuard** puts an admin's laptop "inside" with a cryptographic identity, so admin
ports (22, the Dokploy UI on 3000, Harbor's UI, Grafana) never need to face the internet.

```
 Internet ──80/443──► [edge: Traefik] ──► [app: containers, Apache 81/444] ──► [data: PostgreSQL, backups]
                                               ▲                                    ▲
 Admin laptop ──WireGuard 51820/udp──► [mgmt 10.8.0.0/24] ── SSH 22, Dokploy 3000, Harbor UI, Grafana
                                               (only this zone may open admin ports)
```

Precisely, WireGuard is a kernel VPN with one UDP port, public/private key pairs instead of
certificates, and **cryptokey routing**: each peer's `AllowedIPs` is both the routing table (send
these destinations to this peer) and the access list (accept only these source addresses from
this peer). On-prem, segmentation is VLANs plus firewall rules between them; on AWS it is subnets,
security groups and NACLs ([Learn Cloud & AWS](36-learn-cloud-aws.md)).

**Key terms**

| Term | Meaning |
|---|---|
| Zone / segment | a group of systems with the same trust level and the same allowed flows |
| Bastion / jump host | hardened entry point; the only host that accepts SSH from outside the management zone |
| `ProxyJump` (`ssh -J`) | connect through a bastion without copying keys or forwarding your agent to it |
| `AllowedIPs` | WireGuard: addresses routed to a peer and accepted from it |
| Handshake | WireGuard key exchange; repeated every two minutes while traffic flows |
| `PersistentKeepalive` | keeps NAT mappings open for a peer behind NAT (typically 25 s) |

**See it on a real system**

```bash
sudo wg show
ip -br addr show wg0
sudo ufw status | grep -E 'wg0|51820'
```

```
interface: wg0
  public key: kX3mJ2v9TzR1aQ8yLw5uE0bN6cH4pG7dS2fK1lM9oV0=
  private key: (hidden)
  listening port: 51820

peer: Q9fzW1xC4eV7bN0mA3sD6gH9jK2lP5oI8uY1tR4eE7w=
  endpoint: 203.0.113.45:41622
  allowed ips: 10.8.0.2/32
  latest handshake: 47 seconds ago
  transfer: 1.21 MiB received, 3.88 MiB sent
wg0              UNKNOWN        10.8.0.1/24
51820/udp                  ALLOW       Anywhere
22/tcp on wg0              ALLOW       Anywhere
3000/tcp on wg0            ALLOW       Anywhere
```

→ One peer, recent handshake, traffic flowing. SSH and the Dokploy UI are allowed only when they
arrive on `wg0`, so the only internet-facing admin surface is a UDP port that silently ignores
anything not signed by a known key. (For port 3000, which is a published container port, the UFW
rule is not enough on its own; pair it with the DOCKER-USER rule from the scenario, using
`! -i wg0` instead of a source subnet.)

**Hands-on lab (test VM only)**

**Step 1 — Build a tunnel from your workstation to sec-target.** On both machines:

```bash
sudo apt-get install -y wireguard-tools
umask 077 && wg genkey | tee wg.key | wg pubkey > wg.pub
```

On sec-target, `/etc/wireguard/wg0.conf` (mode 600):

```
[Interface]
Address = 10.8.0.1/24
ListenPort = 51820
PrivateKey = SERVER_PRIVATE_KEY

[Peer]
# alice-laptop
PublicKey = ALICE_PUBLIC_KEY
AllowedIPs = 10.8.0.2/32
```

On the workstation:

```
[Interface]
Address = 10.8.0.2/32
PrivateKey = ALICE_PRIVATE_KEY

[Peer]
PublicKey = SERVER_PUBLIC_KEY
Endpoint = 192.168.56.21:51820
AllowedIPs = 10.8.0.0/24
PersistentKeepalive = 25
```

```bash
sudo ufw allow 51820/udp comment 'WireGuard'
sudo systemctl enable --now wg-quick@wg0          # on both ends
ping -c 2 10.8.0.1                                # from the workstation
```

**Step 2 — Move SSH behind the tunnel (with the dead-man switch from the UFW topic).**

```bash
sudo ufw allow in on wg0 to any port 22 proto tcp comment 'SSH via VPN'
ssh alice@10.8.0.1 true && echo 'ssh over VPN works'      # test BEFORE removing the old rule
sudo ufw delete allow from 192.168.56.0/24 to any port 22 proto tcp
```

**Step 3 — Break it: a wrong AllowedIPs on the server.** Change the server's peer to
`AllowedIPs = 10.8.0.20/32` and restart `wg-quick@wg0`. The handshake still succeeds (keys are
fine), but pings and SSH time out: the server drops packets whose source, 10.8.0.2, is not in that
peer's `AllowedIPs`. `sudo wg show` shows "latest handshake" recent but "received" not growing.

**Step 4 — Fix and add a bastion pattern.** Restore `10.8.0.2/32`. For more servers, do not
run a VPN endpoint on each one: terminate WireGuard on one hardened host and jump from it, with an
SSH client config such as this:

```
Host bastion
    HostName 10.8.0.1
    User alice
Host *.mgmt.example.com
    ProxyJump bastion
    User alice
```

On the bastion keep `AllowTcpForwarding yes` (jumping needs it) but `AllowAgentForwarding no`;
on every other server, the hardened drop-in from section 2 stays as it is.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| UDP 51820 blocked upstream | no "latest handshake" line at all | `sudo tcpdump -ni eth0 udp port 51820` | [Network](02-network.md) |
| Wrong `AllowedIPs` | handshake OK, no traffic | `sudo wg show` (transfer counters) | this topic |
| Address overlap with Docker or the office LAN | VPN up, some hosts unreachable | `ip route get 10.8.0.1` | [Learn networking](28-learn-networking.md) |
| Bastion forwarding disabled | `channel 0: open failed: administratively prohibited` | `sudo sshd -T | grep -i allowtcp` on the bastion | [SSH & remote access](09-ssh-remote-access.md) |

**Why it matters for troubleshooting.** Segmentation turns "the attacker has a web container"
from a total loss into a contained incident, and it changes how you debug: a timeout between two
zones is often a correct rule, not a fault. A design note listing the allowed flows per zone is the
document you check first.

**Next step:** protect the traffic itself with TLS, and run the CA your internal services trust.

---

## 4. TLS and PKI

> 📚 **Study path:** 1) KodeKloud: *DevOps Pre-Requisite Course* — Security: SSL & TLS Basics ([note](https://notes.kodekloud.com/docs/DevOps-Pre-Requisite-Course/Security/SSL-TLS-Basics/page)) · 2) KodeKloud: *Prep Course - LFCS* — Essential Commands: Work With SSL Certificates ([note](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates)) · 3) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Security: TLS Basics ([note](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics)) · 4) Video: ByteByteGo *SSL, TLS, HTTPS Explained* (5 min, [YouTube](https://www.youtube.com/watch?v=j9QmMEWmcfo)) · 5) Note: [Web, HTTP & TLS](18-web-http-tls.md) and the TLS area of [Learn networking](28-learn-networking.md) · 6) Docs: Harbor *Configure HTTPS Access to Harbor* ([docs](https://goharbor.io/docs/2.15.0/install-config/configure-https/)) — KodeKloud has no Harbor course · 7) Practice: the private-CA lab below, then [badssl.com](https://badssl.com/) to meet every broken-certificate error once.

TLS gives you confidentiality and integrity on the wire and, through certificates, authenticity:
the client knows it is talking to the real `harbor.example.com`. Public sites get certificates from
Let's Encrypt through Traefik. Internal services (Harbor, GitLab, Grafana, the Kubernetes API) often
use a **private CA**, and then *you* are the certificate authority: you issue, you distribute
trust, you rotate, and you get paged when something expires. Most "x509" errors in your stack are
trust-distribution problems, not broken certificates.

### Certificates, chains and trust

**Level:** [L1 · Junior] to read a certificate, [L2 · Mid] to debug a chain

**Concept.** A certificate binds a public key to names, signed by an issuer. Clients trust a
small set of **root CAs** in their **trust store**. Servers present their **leaf** certificate plus
any **intermediate** certificates; the client builds a chain from the leaf up to a root it already
trusts. If any link is missing or untrusted, the connection fails, however correct the leaf is.

```
  client trust store                  what the server sends
  ┌──────────────────────┐            ┌────────────────────────────────────┐
  │ Example Lab Root CA  │◄─ signs ───│ Example Lab Intermediate CA 2026   │
  │ (+ public roots)     │            │            │ signs                 │
  └──────────────────────┘            │            ▼                       │
                                      │ harbor.example.com (leaf)          │
                                      │ SAN: DNS:harbor.example.com        │
                                      └────────────────────────────────────┘
```

Precisely: modern clients match the hostname against the **Subject Alternative Name (SAN)**
only; the Common Name is ignored (Go programs, which include Docker, containerd and kubelet, have
required SANs since Go 1.15). A CA certificate carries `basicConstraints CA:TRUE`; a leaf carries
`CA:FALSE` and an **extended key usage** of `serverAuth` (servers) or `clientAuth` (clients).

**Key terms**

| Term | Meaning |
|---|---|
| Root CA | self-signed, lives in trust stores; its key should be offline |
| Intermediate CA | signed by the root; signs leaves, so the root key can stay offline |
| Leaf | the server's or client's own certificate |
| SAN | the names (DNS, IP) the certificate is valid for |
| Full chain | leaf followed by intermediates, the file a server should serve |
| Trust store | the set of roots a client accepts; each client may have its own |

**See it on a real system**

```bash
echo | openssl s_client -connect harbor.example.com:443 -servername harbor.example.com -showcerts 2>/dev/null \
  | grep -E '^ [0-9] s:|^   i:|Verify return code'
openssl x509 -in /data/cert/harbor.crt -noout -subject -issuer -dates \
  -ext subjectAltName,basicConstraints,extendedKeyUsage
```

```
 0 s:CN = harbor.example.com
   i:CN = Example Lab Intermediate CA 2026
 1 s:CN = Example Lab Intermediate CA 2026
   i:CN = Example Lab Root CA
    Verify return code: 20 (unable to get local issuer certificate)
subject=CN = harbor.example.com
issuer=CN = Example Lab Intermediate CA 2026
notBefore=Oct  2 09:00:00 2026 GMT
notAfter=Nov  3 09:00:00 2027 GMT
X509v3 Subject Alternative Name: 
    DNS:harbor.example.com
X509v3 Basic Constraints: critical
    CA:FALSE
X509v3 Extended Key Usage: 
    TLS Web Server Authentication
```

→ The server sends a correct chain: leaf (0) issued by the intermediate (1), which is issued by
the root. `Verify return code: 20` means *this client* does not have `Example Lab Root CA` in its
store, so the chain ends at an unknown issuer. That is a client-side trust problem, fixed by
distributing the root (two topics down), not by touching Harbor. Code 19 ("self-signed certificate
in certificate chain") is the same trust problem when the server also sends the root: sending it is
harmless but unnecessary, and the client still does not trust it until the root is in its store;
code 21 ("unable to verify the first certificate") usually means the server forgot the
intermediate.

**Hands-on lab (test VM only)**

**Step 1 — Read three public chains.** Run the `s_client` command above against
`example.com:443`, against `expired.badssl.com:443` and against `untrusted-root.badssl.com:443`.
Write down each `Verify return code` and what it means.

**Step 2 — Break it: request the wrong name.** Connect by IP or with a different
`-servername` to a host that serves several names (Traefik, for example) and add
`-verify_hostname harbor.example.com`. Note the `hostname mismatch` result and the
`TRAEFIK DEFAULT CERT` subject that Traefik serves when no router matches the SNI name.

**Step 3 — Fix your reading habit.** Always pass `-servername` with `s_client`, always check the
SAN list, and always read the verify code before blaming the server.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Root not in the client's store | `x509: certificate signed by unknown authority`, verify code 20 | `openssl s_client ... -showcerts` | this area, the x509 scenario |
| Intermediate missing on the server | works in a browser, fails in curl, Docker or Java (code 21) | count the certificates in `-showcerts` | [Web, HTTP & TLS](18-web-http-tls.md) |
| Name not in SAN | `certificate is valid for X, not Y` | `openssl x509 -noout -ext subjectAltName` | [Web, HTTP & TLS](18-web-http-tls.md) |
| Clock wrong | `certificate has expired or is not yet valid` on a valid certificate | `timedatectl` | [Time & NTP](12-time-ntp.md) |

**Why it matters for troubleshooting.** Reading a chain takes one command and tells you which
side to fix. Most TLS outages are lost because someone regenerated a perfectly good server
certificate when the client's trust store was the problem.

**Next step:** become the CA.

### Lab: build a private CA for Harbor

**Level:** [L2 · Mid] with openssl, [L3 · Senior] to run step-ca as a service

This is the required PKI lab. Target: a two-tier CA (offline root, online intermediate), a
Harbor certificate with the right extensions, served as a full chain. Time: about an hour.

**Concept.** A two-tier CA keeps the root key offline: if the intermediate is ever compromised,
you revoke and replace it without touching every trust store. Leaf lifetimes should be short.
The CA/Browser Forum is cutting the maximum lifetime of publicly trusted certificates in steps
(200 days from March 2026, down to 47 days by 2029). A private CA is not bound by those rules, but
short lifetimes force you to automate renewal early. This lab uses 397 days to keep the first run
simple; step-ca in Step 5 defaults to 24 hours.

**Key terms**

| Term | Meaning |
|---|---|
| CSR | certificate signing request: the public key plus requested names, signed by the requester |
| `pathlen:0` | this CA may sign leaves but not further CAs |
| Serial file | `-CAcreateserial` keeps a serial counter so every certificate is unique |
| step-ca | open-source online CA from Smallstep with ACME support and automatic renewal |

**See it on a real system**

After the lab, the CA directory and the certificate file you deploy look like this:

```bash
ls -l ~/pki
grep -c 'BEGIN CERTIFICATE' ~/pki/harbor-fullchain.crt
```

```
total 52
-rw------- 1 alice alice  562 Oct  2 09:00 harbor.crt
-rw------- 1 alice alice  428 Oct  2 09:00 harbor.csr
-rw------- 1 alice alice  136 Oct  2 09:00 harbor.ext
-rw------- 1 alice alice 1165 Oct  2 09:00 harbor-fullchain.crt
-rw------- 1 alice alice  241 Oct  2 09:00 harbor.key
-rw------- 1 alice alice  603 Oct  2 08:58 int.crt
-rw------- 1 alice alice  436 Oct  2 08:58 int.csr
-rw------- 1 alice alice  137 Oct  2 08:58 int.ext
-rw------- 1 alice alice  241 Oct  2 08:58 int.key
-rw------- 1 alice alice   41 Oct  2 09:00 int.srl
-rw------- 1 alice alice  595 Oct  2 08:57 root.crt
-rw------- 1 alice alice  241 Oct  2 08:57 root.key
-rw------- 1 alice alice   41 Oct  2 08:58 root.srl
2
```

→ Every file is mode 600 (the lab's `umask 077`), the CSR, extension and serial (`.srl`) files are
the lab's working files, and the full chain holds two certificates (leaf and intermediate),
never the root. In real life `root.key` would not be on this machine at all after signing the
intermediate.

**Hands-on lab (test VM only)**

**Step 1 — Root and intermediate, on sec-reg.**

```bash
mkdir -p ~/pki && cd ~/pki && umask 077
# Root CA: 10 years; move root.key offline after this lab (encrypted USB, password manager, HSM)
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out root.key
openssl req -x509 -new -key root.key -sha256 -days 3650 -subj "/CN=Example Lab Root CA" \
  -addext "basicConstraints=critical,CA:TRUE" -addext "keyUsage=critical,keyCertSign,cRLSign" \
  -out root.crt
# Intermediate CA: 3 years, may only sign leaves
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out int.key
openssl req -new -key int.key -subj "/CN=Example Lab Intermediate CA 2026" -out int.csr
printf '%s\n' 'basicConstraints=critical,CA:TRUE,pathlen:0' 'keyUsage=critical,keyCertSign,cRLSign' \
  'subjectKeyIdentifier=hash' 'authorityKeyIdentifier=keyid' > int.ext
openssl x509 -req -in int.csr -CA root.crt -CAkey root.key -CAcreateserial -days 1095 -sha256 \
  -extfile int.ext -out int.crt
```

**Step 2 — The Harbor leaf, with a SAN and serverAuth.**

```bash
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out harbor.key
openssl req -new -key harbor.key -subj "/CN=harbor.example.com" -out harbor.csr
printf '%s\n' 'basicConstraints=critical,CA:FALSE' 'keyUsage=critical,digitalSignature' \
  'extendedKeyUsage=serverAuth' 'subjectAltName=DNS:harbor.example.com' > harbor.ext
openssl x509 -req -in harbor.csr -CA int.crt -CAkey int.key -CAcreateserial -days 397 -sha256 \
  -extfile harbor.ext -out harbor.crt
cat harbor.crt int.crt > harbor-fullchain.crt
openssl verify -CAfile root.crt -untrusted int.crt harbor.crt
```

```
harbor.crt: OK
```

**Step 3 — Serve it.** For Harbor, set `https.certificate` to the full chain and
`https.private_key` to the key in `harbor.yml`, then run `sudo ./prepare` and restart Harbor
with `docker compose down && docker compose up -d` from the Harbor directory. For a quick lab
registry without Harbor:

```bash
docker run -d --name registry --restart unless-stopped -p 443:443 -v ~/pki:/certs:ro \
  -e REGISTRY_HTTP_ADDR=0.0.0.0:443 \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/harbor-fullchain.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/harbor.key registry:2
```

**Step 4 — Break it: serve the leaf without the intermediate.** Point the registry at
`harbor.crt` instead of the full chain and restart it. Even a client that trusts your root now
fails with `unable to verify the first certificate` (code 21), because it cannot link the leaf to
the root. Browsers sometimes hide this by fetching intermediates themselves; curl, Docker and
Java do not. Switch back to the full chain.

**Step 5 — The same with step-ca ([L3 · Senior]).** An online CA issues short-lived certificates
and renews them automatically, which removes the "expired certificate" class of outage:

```bash
step ca init --name "Example Lab CA" --dns ca.example.com --address :9000 --provisioner admin@example.com
step-ca "$(step path)/config/ca.json"                            # run as a systemd service in real use
step ca certificate harbor.example.com harbor.crt harbor.key     # 24 h by default
step ca renew --daemon harbor.crt harbor.key                     # renews before expiry, keeps running
```

step-ca's defaults are deliberately short (24-hour certificates), so renewal must be automated
from day one. It can also act as an **ACME** server (`step ca provisioner add acme --type ACME`),
which lets Traefik obtain internal certificates exactly as it does from Let's Encrypt.

**Exit criteria:** `openssl verify` says OK, the registry serves two certificates in
`-showcerts`, `root.key` is no longer on an online machine, and you wrote down the expiry dates of
root, intermediate and leaf in your calendar or monitoring.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| No SAN | Go clients refuse: `x509: certificate relies on legacy Common Name field` | `openssl x509 -noout -ext subjectAltName` | this topic |
| Leaf served without intermediate | code 21 in curl, works in Chrome | `openssl s_client -showcerts` | this topic |
| CA key readable by others | silent; anyone can mint trusted certificates | `stat -c '%a %U' ~/pki/*.key` | section 13 |
| Intermediate expired | every leaf it signed fails at once | `openssl x509 -in int.crt -noout -enddate` | next topics |

**Why it matters for troubleshooting.** When you built the chain yourself, every error message
maps to a step you did: no SAN, missing intermediate, wrong key usage, expired link. That turns
"TLS is broken" into a specific, one-line fix.

**Next step:** make every client trust the new root.

### Distributing trust: hosts, Docker, containerd

**Level:** [L2 · Mid]

**Concept.** There is no single trust store on a Linux server. The OS has one, Docker reads its
own per-registry directory, containerd reads another, and every container image carries its own
copy of a CA bundle, sometimes several (Python, Node and Java bring their own). Adding your root
to one of them fixes exactly one client.

| Client | Where it looks | Takes effect |
|---|---|---|
| curl, apt, git, wget on the host | `/etc/ssl/certs/ca-certificates.crt`, rebuilt by `update-ca-certificates` from `/usr/local/share/ca-certificates/*.crt` | immediately (new processes) |
| Docker Engine (`docker login`, pull, push) | `/etc/docker/certs.d/HOST/ca.crt` (add `:PORT` to the directory name if not 443), plus the system store | immediately for `certs.d` |
| containerd, kubelet, `crictl` | `/etc/containerd/certs.d/HOST/hosts.toml`, enabled by `config_path` in `/etc/containerd/config.toml` | `hosts.toml` per pull; `config_path` needs a containerd restart |
| Inside a container | the image's own `/etc/ssl/certs`; Python `certifi`, Node's bundled roots, Java `cacerts` | rebuild the image or mount the CA |
| GitLab Runner with Docker-in-Docker | the `dind` service container's own Docker, not the host's | per job: mount or install the CA in the service |
| Browsers | OS store (Chrome on Linux uses NSS), Firefox has its own | browser restart |

`update-ca-certificates` only picks up files ending in **`.crt`**; a `.pem` file there is silently
ignored. That one detail costs people hours.

**Key terms**

| Term | Meaning |
|---|---|
| `update-ca-certificates` | rebuilds the OS bundle from the system and local CA directories |
| `certs.d` | Docker's per-registry trust directory |
| `hosts.toml` | containerd's per-registry config: endpoint, capabilities, CA file |
| `REQUESTS_CA_BUNDLE`, `NODE_EXTRA_CA_CERTS` | environment variables that point Python requests and Node.js at a CA file |

**See it on a real system**

```bash
ls /usr/local/share/ca-certificates/ /etc/docker/certs.d/*/ /etc/containerd/certs.d/*/ 2>&1
grep -n 'config_path' /etc/containerd/config.toml
awk -v cmd='openssl x509 -noout -subject' '/BEGIN/{close(cmd)};{print | cmd}' \
  /etc/ssl/certs/ca-certificates.crt | grep -i example
```

```
/usr/local/share/ca-certificates/:
example-root-ca.crt

/etc/docker/certs.d/harbor.example.com/:
ca.crt

ls: cannot access '/etc/containerd/certs.d/*/': No such file or directory
164:    config_path = ""
subject=CN = Example Lab Root CA
```

→ The OS and Docker trust the lab root. containerd does not: no `certs.d` directory and an empty
`config_path`. On this node `docker pull` from Harbor works and the kubelet's pulls fail with x509
errors, which is exactly the confusing split you see on mixed Docker/Kubernetes hosts.

**Hands-on lab (test VM only)**

**Step 1 — Break it first: no trust anywhere.** On sec-target:

```bash
docker login harbor.example.com
curl -sS https://harbor.example.com/v2/ -o /dev/null
```

```
Error response from daemon: Get "https://harbor.example.com/v2/": tls: failed to verify certificate: x509: certificate signed by unknown authority
curl: (60) SSL certificate problem: unable to get local issuer certificate
```

**Step 2 — Make Docker trust it (the required "Docker trusts the private CA" lab).**

```bash
sudo install -d /etc/docker/certs.d/harbor.example.com
sudo install -m 644 root.crt /etc/docker/certs.d/harbor.example.com/ca.crt
docker login harbor.example.com
curl -sS https://harbor.example.com/v2/ -o /dev/null
```

```
Login Succeeded
curl: (60) SSL certificate problem: unable to get local issuer certificate
```

→ Docker is fixed, curl is not: two clients, two stores.

**Step 3 — Fix the OS store.**

```bash
sudo install -m 644 root.crt /usr/local/share/ca-certificates/example-root-ca.crt
sudo update-ca-certificates
curl -sS -o /dev/null -w '%{http_code}\n' https://harbor.example.com/v2/
```

```
Updating certificates in /etc/ssl/certs...
rehash: warning: skipping ca-certificates.crt,it does not contain exactly one certificate or CRL
1 added, 0 removed; done.
Running hooks in /etc/ca-certificates/update.d...
done.
401
```

→ `401` is success here: TLS worked and the registry asks for credentials.

**Step 4 — containerd (Kubernetes nodes).** Point containerd at the `certs.d` directory once,
then add a `hosts.toml` per registry:

```
# /etc/containerd/config.toml, containerd 1.7 (config version 2)
[plugins."io.containerd.grpc.v1.cri".registry]
  config_path = "/etc/containerd/certs.d"

# containerd 2.x (config version 3) uses this section instead:
# [plugins."io.containerd.cri.v1.images".registry]
#   config_path = "/etc/containerd/certs.d"
```

```
# /etc/containerd/certs.d/harbor.example.com/hosts.toml
server = "https://harbor.example.com"

[host."https://harbor.example.com"]
  capabilities = ["pull", "resolve"]
  ca = "/etc/containerd/certs.d/harbor.example.com/ca.crt"
```

```bash
sudo install -D -m 644 root.crt /etc/containerd/certs.d/harbor.example.com/ca.crt   # -D creates the directory
sudo systemctl restart containerd
sudo crictl pull harbor.example.com/library/alpine:3.20
```

`ctr` ignores `hosts.toml` unless you pass `--hosts-dir /etc/containerd/certs.d`, so test with
`crictl`, which uses the same path as the kubelet.

**Step 5 — Inside a container.** Build the root into images that call internal HTTPS services:

```dockerfile
FROM python:3.12-slim
COPY example-root-ca.crt /usr/local/share/ca-certificates/example-root-ca.crt
RUN update-ca-certificates
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt \
    NODE_EXTRA_CA_CERTS=/usr/local/share/ca-certificates/example-root-ca.crt
```

Do this in one shared base image in Harbor, not in every application's Dockerfile, and roll the
whole fleet of hosts with Ansible (a `copy` task plus a handler that runs
`update-ca-certificates`), never by hand.

### Scenario: x509 unknown authority

**Level:** [L2 · Mid]. The most common TLS incident on your stack: a pull, login or API call to
an internal service fails with `x509: certificate signed by unknown authority`.

**Step 1 — Identify the failing client**

**Goal:** know *which* program's trust store is being used.

```bash
kubectl -n shop describe pod api-7d4b9c6f5-x2k8q | grep -A3 'Failed'
```

```
  Warning  Failed     12s   kubelet  Failed to pull image "harbor.example.com/shop/api:1.8.0": failed to pull and unpack image "harbor.example.com/shop/api:1.8.0": failed to resolve reference "harbor.example.com/shop/api:1.8.0": failed to do request: Head "https://harbor.example.com/v2/shop/api/manifests/1.8.0": tls: failed to verify certificate: x509: certificate signed by unknown authority
  Warning  Failed     12s   kubelet  Error: ErrImagePull
```

**What it means:** the kubelet asked containerd to pull, so containerd's `certs.d` is the store
in play, on the node where the pod was scheduled. Docker's `certs.d` and the OS bundle are
irrelevant to this error.

**Why this step (now):** "unknown authority" names a symptom, not a location. Each client in the
trust table has its own store, so naming the client first prevents the classic fix-the-wrong-store
loop (adding the CA to Docker on a Kubernetes node and wondering why nothing changed).

**Next step:** if the message comes from `docker` → the store is `/etc/docker/certs.d`. From a
GitLab job → the DinD service or the job image. From an application log → the image's bundle.
From kubelet/containerd, as here → Step 2, run on the node that failed (`kubectl get pod -o wide`).

**Step 2 — See what the server actually sends**

**Goal:** rule out a server-side problem before touching any client.

```bash
echo | openssl s_client -connect harbor.example.com:443 -servername harbor.example.com -showcerts 2>/dev/null \
  | grep -E '^ [0-9] s:|^   i:|Verify return code'
```

```
 0 s:CN = harbor.example.com
   i:CN = Example Lab Intermediate CA 2026
 1 s:CN = Example Lab Intermediate CA 2026
   i:CN = Example Lab Root CA
    Verify return code: 20 (unable to get local issuer certificate)
```

**What it means:** the server sends leaf and intermediate, issued by your lab root. The chain is
complete; only the root is unknown to this machine's OpenSSL store.

**Why this step (now):** if the server sent the wrong certificate (`TRAEFIK DEFAULT CERT`,
expired, missing intermediate), no client-side fix would help. One read-only command settles which
side is wrong.

**Next step:** if only one certificate is listed (missing intermediate) → fix the server's full
chain (previous lab, Step 4). If the subject is wrong or expired → fix the server certificate. If
the chain is complete and ends at your root, as here → Step 3.

**Step 3 — Verify the chain against the CA file you intend to distribute**

**Goal:** prove that the root you are about to install really is the issuer.

```bash
echo | openssl s_client -connect harbor.example.com:443 -servername harbor.example.com 2>/dev/null \
  | openssl x509 > /tmp/leaf.pem
openssl verify -CAfile /etc/containerd/certs.d/harbor.example.com/ca.crt -untrusted int.crt /tmp/leaf.pem
```

```
/tmp/leaf.pem: OK
```

**What it means:** the CA file on the node can validate the served chain. If it printed
`unable to get issuer certificate`, the node holds the wrong CA (an old root, the intermediate
instead of the root, or a different lab CA).

**Why this step (now):** distributing the wrong CA file is the second most common mistake after
the wrong store. Verifying offline with `openssl verify` costs seconds and avoids a restart cycle.

**Next step:** if `verify` fails → replace `ca.crt` with the correct root, then Step 4. If it is
OK → the file is right and the client is not reading it → Step 4.

**Step 4 — Check that the client reads its store**

**Goal:** confirm containerd is configured to use `certs.d`.

```bash
sudo grep -n 'config_path' /etc/containerd/config.toml
sudo ls -l /etc/containerd/certs.d/harbor.example.com/
sudo crictl info | grep -i -A2 '"registry"'
```

```
164:    config_path = ""
-rw-r--r-- 1 root root 595 Oct  2 10:12 ca.crt
-rw-r--r-- 1 root root 171 Oct  2 10:12 hosts.toml
    "registry": {
      "configPath": "",
```

**What it means:** the files are present, but `config_path` is empty, so containerd never reads
them. This is the default in a freshly generated `config.toml`.

**Why this step (now):** you have proven the server and the CA file are right, so the remaining
hypothesis is configuration of the client itself. `crictl info` shows the *running* config, which
also catches an edit that was made but never applied with a restart.

**Next step:** if `configPath` is empty or wrong → Step 5. If it is set and the files are there →
check the directory name matches the registry host exactly (including `:PORT` when not 443) and
that `hosts.toml` has no TOML syntax error (`journalctl -u containerd -n 30`).

**Step 5 — Fix and verify on every node**

**Goal:** set `config_path`, restart containerd, and prove the pull works.

```bash
sudo sed -i 's|config_path = ""|config_path = "/etc/containerd/certs.d"|' /etc/containerd/config.toml
sudo systemctl restart containerd
sudo crictl pull harbor.example.com/shop/api:1.8.0
kubectl -n shop get pods -l app=api
```

```
Image is up to date for sha256:5c1e8f3a9d2b4c6e7f8091a2b3c4d5e6f708192a3b4c5d6e7f8091a2b3c4d5e6f
NAME                   READY   STATUS    RESTARTS   AGE
api-7d4b9c6f5-x2k8q    1/1     Running   0          6m
```

**What it means:** containerd now trusts Harbor, and the pod that was in `ImagePullBackOff`
started on its next retry.

**Why this step (now):** restarting containerd briefly interrupts container management on the
node (running containers keep running), so it comes last, after every cheaper check passed. Do it
node by node, and through Ansible on a real cluster so a new node cannot miss it.

**Next step:** repeat for every node (`kubectl get nodes`), then add the check to your node
bootstrap. If the pull still fails, compare the exact error text with Step 1: a different error
(`401`, `not found`) means TLS is now fixed and you have moved on to authentication or naming.

**Decision tree**

```
x509: certificate signed by unknown authority
│
├─ Which client? (error source)
│    docker CLI ──► /etc/docker/certs.d/HOST/ca.crt
│    kubelet / containerd ──► config_path + certs.d/HOST/hosts.toml (+ restart once)
│    GitLab job ──► DinD service or job image needs the CA
│    app in a container ──► image CA bundle / REQUESTS_CA_BUNDLE / Java cacerts
│
├─ openssl s_client -showcerts: chain complete and issued by your CA?
│    no ──► fix the server (full chain, right certificate, not expired)
│
└─ openssl verify -CAfile FILE: OK?
     no ──► wrong CA file distributed
     yes ─► client not reading it (path, directory name, config_path, restart)
```

**Fix & verify:** the exact operation that failed now works (`crictl pull`, `docker login`,
`curl` from inside the container), and `openssl verify` against the deployed CA file says OK.

**Rollback:** restore the previous `config.toml` (keep a copy before `sed`) and restart
containerd; removing a CA file from a store is equally safe and immediate for Docker.

**Prevent it next time:** distribute the root with Ansible to all three host stores in one role,
bake it into one shared base image, and add a node-bootstrap check that runs `crictl pull` from
Harbor before the node joins the cluster.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| CA added to Docker on a Kubernetes node | `docker pull` works, pods stay in `ImagePullBackOff` | `sudo crictl info | grep configPath` | [Containers playbook](26-playbook-containers-k8s.md) |
| File named `.pem` in `/usr/local/share/ca-certificates` | `update-ca-certificates` reports `0 added` | `ls /usr/local/share/ca-certificates/` | this topic |
| CA on the host, not in the image | host `curl` works, the app logs `CERTIFICATE_VERIFY_FAILED` | `docker exec CONTAINER ls /usr/local/share/ca-certificates` | [Learn Docker](30-learn-docker.md) |
| DinD job cannot push to Harbor | `x509` in the GitLab job log only | job log, then the runner's `dind` service config | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |

**Why it matters for troubleshooting.** The trust table above is the map for every x509 error you
will meet in this stack. Learn it once and the error stops being scary: it is always "which
client, which store".

**Next step:** keep all these certificates from expiring on you.

### Rotation and expiry monitoring

**Level:** [L2 · Mid] to monitor, [L3 · Senior] to design rotation

**Concept.** Every certificate expires, and expiry is the most predictable outage there is. Two
habits remove it: **monitor** every certificate you depend on (served endpoints, files on disk,
CAs, kubeadm's internal certificates) with alerts weeks ahead, and **automate rotation** so that a
human is the exception. Rotating a leaf signed by an unchanged CA needs no client changes;
rotating a **CA** does, and needs an overlap period in which clients trust both the old and the
new root.

**Key terms**

| Term | Meaning |
|---|---|
| `-checkend SECONDS` | `openssl x509` exits 1 if the certificate expires within that time |
| `probe_ssl_earliest_cert_expiry` | blackbox_exporter metric: Unix time of the soonest expiry in the served chain |
| `kubeadm certs check-expiration` | lists kubeadm-managed certificates and their remaining time |
| CA rollover | distribute new root alongside old, switch issuance, then remove old |

**See it on a real system**

```bash
for h in harbor.example.com:443 gitlab.example.com:443 shop.example.com:443 192.0.2.10:444; do
  end=$(echo | openssl s_client -connect "$h" -servername "${h%:*}" 2>/dev/null | openssl x509 -noout -enddate | cut -d= -f2)
  printf '%-26s %5s days  %s\n' "$h" $(( ( $(date -d "$end" +%s) - $(date +%s) ) / 86400 )) "$end"
done
sudo kubeadm certs check-expiration | grep -m1 -A5 '^CERTIFICATE '   # skip the "[check-expiration]" preamble
```

```
harbor.example.com:443       396 days  Nov  3 09:00:00 2027 GMT
gitlab.example.com:443        23 days  Oct 25 11:40:12 2026 GMT
shop.example.com:443          71 days  Dec 12 04:13:55 2026 GMT
192.0.2.10:444                 9 days  Oct 11 23:59:59 2026 GMT
CERTIFICATE                EXPIRES                  RESIDUAL TIME   CERTIFICATE AUTHORITY   EXTERNALLY MANAGED
admin.conf                 Mar 14, 2027 08:21 UTC   162d            ca                      no
apiserver                  Mar 14, 2027 08:21 UTC   162d            ca                      no
apiserver-etcd-client      Mar 14, 2027 08:21 UTC   162d            etcd-ca                 no
apiserver-kubelet-client   Mar 14, 2027 08:21 UTC   162d            ca                      no
controller-manager.conf    Mar 14, 2027 08:21 UTC   162d            ca                      no
```

→ Apache's old certificate on 444 expires in nine days. Nobody notices because public traffic now
arrives through Traefik with a Let's Encrypt certificate, but if Traefik talks to Apache over
HTTPS and verifies it, legacy sites break on day ten. GitLab's 23 days needs a ticket today.
kubeadm's certificates are renewed by every `kubeadm upgrade`; a cluster that is never upgraded
hits the one-year wall.

**Hands-on lab (test VM only)**

**Step 1 — Build an alert.** If you run Prometheus with blackbox_exporter
([Observability](32-learn-performance-observability.md)), add this rule:

```yaml
groups:
  - name: tls
    rules:
      - alert: CertificateExpiresSoon
        expr: (probe_ssl_earliest_cert_expiry - time()) / 86400 < 21
        for: 1h
        labels:
          severity: ticket
        annotations:
          summary: "{{ $labels.instance }}: certificate expires in {{ $value | humanize }} days"
      - alert: CertificateExpiresVerySoon
        expr: (probe_ssl_earliest_cert_expiry - time()) / 86400 < 7
        labels:
          severity: page
```

Without Prometheus, run the loop above from cron daily and mail any line under 21 days.

**Step 2 — Break it: issue a one-day certificate.** Re-run Step 2 of the CA lab with `-days 1`
and deploy it to the lab registry. Confirm the check catches it:

```bash
openssl x509 -in harbor.crt -noout -checkend $((7*86400)); echo "exit=$?"
```

```
Certificate will expire
exit=1
```

**Step 3 — Fix it with a rotation script, not by hand.** Write `rotate-harbor-cert.sh`: issue a
new leaf with the same SAN, build the full chain, `openssl verify` it, back up the old files,
install the new ones, restart the registry, and re-check the served `notAfter` with `s_client`.
Run it, then schedule it (or switch to step-ca's `renew --daemon`).

**Step 4 — Plan a CA rollover ([L3 · Senior]).** On paper: create a new intermediate (or root),
distribute the new root to every trust store *alongside* the old one (Ansible run, verify on every
node with `openssl verify`), start issuing from the new CA, wait until every leaf from the old CA
has expired or been replaced, then remove the old root. This is the senior scenario "the Harbor CA
expires in 10 days across 40 nodes" in [Senior architecture](39-learn-senior-architecture.md).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Leaf expired | `certificate has expired` for every client at once | `openssl x509 -noout -enddate` on the served certificate | [Web, HTTP & TLS](18-web-http-tls.md) |
| kubeadm certificates expired | `kubectl`: `x509: certificate has expired or is not yet valid` | `sudo kubeadm certs check-expiration` | [Containers playbook](26-playbook-containers-k8s.md) |
| Let's Encrypt renewal failing in Traefik | Traefik serves an old or default certificate | `docker logs dokploy-traefik 2>&1 | grep -i acme` | [Apache 443 case](21-case-apache-443-dokploy.md) |
| Renewed on disk, old one still served | `notAfter` from `s_client` is the old date | restart or reload the service | this topic |

**Why it matters for troubleshooting.** Expired certificates produce errors that look like
attacks or network faults. A dated inventory of every certificate turns that ten-minute panic into
a glance at a dashboard.

**Next step:** use certificates to authenticate clients too.

### mTLS

**Level:** [L3 · Senior]

**Concept.** In normal TLS only the server proves its identity. In **mutual TLS (mTLS)** the
client also presents a certificate, and the server only talks to clients whose certificate chains
to a CA it trusts. Kubernetes runs on mTLS (the kubelet, the scheduler and your `admin.conf` all
authenticate with client certificates), service meshes use it between every pod, and you can use
it to protect admin routes such as Grafana or the Dokploy UI with something stronger than a
password.

Precisely: the server sends a `CertificateRequest` during the handshake; the client answers with
its certificate and proves possession of the key. Client certificates need the `clientAuth`
extended key usage. Revocation is the weak spot: Kubernetes cannot revoke a client certificate at
all, which is why a leaked `admin.conf` stays valid until it expires, and why humans should use
short-lived credentials.

**Key terms**

| Term | Meaning |
|---|---|
| Client certificate | a certificate with `extendedKeyUsage=clientAuth` that identifies a user or service |
| `RequireAndVerifyClientCert` | Traefik TLS option: reject clients without a valid certificate |
| Client CA | the CA that issues client certificates; keep it separate from the server CA |
| Service mesh | sidecars or node agents that add mTLS between services automatically |

**See it on a real system**

```bash
curl -sS -o /dev/null -w '%{http_code}\n' https://grafana.example.com/
curl -sS -o /dev/null -w '%{http_code}\n' --cert alice-client.crt --key alice-client.key https://grafana.example.com/
grep client-certificate-data ~/.kube/config | head -c 60; echo
```

```
curl: (56) OpenSSL SSL_read: OpenSSL/3.0.13: error:0A00045C:SSL routines::tlsv13 alert certificate required, errno 0
200
    client-certificate-data: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURS0
```

→ Without a client certificate, the TLS handshake itself is refused (`alert certificate
required`), so the application never sees the request and its login page is never exposed. With
alice's certificate, Grafana answers. Your kubeconfig shows that `kubectl` already does mTLS
every day.

**Hands-on lab (test VM only)**

**Step 1 — Build a client CA and one client certificate.** Reuse the commands from the CA lab
with a separate `ops-client-ca` and this extension file for the client:

```bash
printf '%s\n' 'basicConstraints=critical,CA:FALSE' 'keyUsage=critical,digitalSignature' \
  'extendedKeyUsage=clientAuth' > client.ext
openssl genpkey -algorithm EC -pkeyopt ec_paramgen_curve:P-256 -out alice-client.key
openssl req -new -key alice-client.key -subj "/CN=alice@example.com/O=ops" -out alice-client.csr
openssl x509 -req -in alice-client.csr -CA ops-client-ca.crt -CAkey ops-client-ca.key -CAcreateserial \
  -days 30 -sha256 -extfile client.ext -out alice-client.crt
```

**Step 2 — Require it in Traefik.** Copy `ops-client-ca.crt` into Dokploy's dynamic directory and
add a TLS option there (Traefik watches the directory):

```yaml
# /etc/dokploy/traefik/dynamic/admin-mtls.yml
tls:
  options:
    admin-mtls:
      minVersion: VersionTLS12
      clientAuth:
        caFiles:
          - /etc/dokploy/traefik/dynamic/certs/ops-client-ca.crt
        clientAuthType: RequireAndVerifyClientCert
```

Attach it to the admin router with the label
`traefik.http.routers.grafana.tls.options=admin-mtls@file` and redeploy the app.

**Step 3 — Break it: a server certificate as a client certificate.** Try
`curl --cert harbor.crt --key harbor.key https://grafana.example.com/`. It fails: the certificate
is from the wrong CA and lacks `clientAuth`. Then issue alice a certificate with `-days 1`, wait,
and watch the handshake fail: curl shows the TLS alert, and Traefik logs the
`x509: certificate has expired or is not yet valid` reason only when its log level is `DEBUG`
(TLS handshake errors are logged at debug level).

**Step 4 — Fix and operate it.** Issue short-lived client certificates (30 days or less), keep
the client CA key offline or in step-ca, and for a lost laptop remove that user's certificate by
rotating the client CA or, better, keep lifetimes short enough that expiry is the revocation.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Client sends no certificate | `alert certificate required` / `handshake failure` | `curl -v --cert ... --key ...` | this topic |
| Wrong `caFiles` path inside the Traefik container | Traefik log error, option ignored or every client rejected | `docker logs dokploy-traefik 2>&1 | grep -i tls` | [Learn web servers & proxies](29-learn-webservers-proxies.md) |
| Client certificate lacks `clientAuth` | `x509: certificate specifies an incompatible key usage` (Go servers such as Traefik), `unsupported certificate purpose` (OpenSSL-based servers) | `openssl x509 -noout -ext extendedKeyUsage` | this topic |
| Leaked kubeconfig | someone else acts as cluster admin | Kubernetes audit log (section 7) | section 13 |

**Why it matters for troubleshooting.** mTLS failures happen inside the handshake, so the
application logs nothing. Knowing that, you go straight to `curl -v` and the proxy's TLS log
instead of the application.

**Next step:** protect the other kind of credential: secrets.

---

## 5. Secrets management

> 📚 **Study path:** 1) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Architecture & Core Concepts (variables), then Optimization, Security and Monitoring ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · 2) Note: [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) and the secrets topic in [Learn Docker](30-learn-docker.md) · 3) KodeKloud: *Ansible Basics Course* — Variables and Facts, Playbooks, then add Ansible Vault from this area ([course](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course)) · 4) HashiCorp Vault and sops have no course in the verified KodeKloud map; look for a Vault course by name (check the current catalog) or use the projects' own documentation · 5) Practice: the gitleaks lab and the leaked-secret scenario below on a throwaway GitLab project.

A secret is any value that grants access: passwords, API tokens, private keys, Harbor robot
tokens, kubeconfigs, cloud access keys, Dokploy's environment variables. The rules are short:
never in Git, never in a log, never in an image, as few copies as possible, as short-lived as
possible, and a rotation procedure for each one *before* it leaks. Leaked credentials, not clever
exploits, are behind most cloud breaches.

### Secrets never in Git

**Level:** [L1 · Junior]

**Concept.** Git never forgets. A secret committed and then deleted in the next commit is still
in the history, in every clone, in forks, in merge-request refs and in CI caches. **Secret
scanners** such as **gitleaks** and **trufflehog** search files and history for patterns (token
prefixes like `glpat-`, AWS key IDs, private-key headers) and for high-entropy strings. Run them in
three places: a pre-commit hook (cheapest, before the secret leaves the laptop), the CI pipeline
(catches what the hook missed) and a scheduled scan of all repositories (catches old history).

Precisely: when a secret leaks, **rotation comes first and history rewriting second**. Rewriting
history removes the secret from *your* copy of the repository; it cannot remove it from clones,
forks, CI logs or the attacker who already scraped it. Only revoking the secret makes it useless.

**Key terms**

| Term | Meaning |
|---|---|
| Finding | a match a scanner reports, with file, line, commit and rule |
| Verified result | trufflehog tried the credential against its provider and it worked; treat it as live |
| Baseline / allowlist | known false positives you accept explicitly, so the scan can fail on new ones |
| `.gitignore` | stops a file being added; does nothing for files already committed |
| History rewrite | `git filter-repo` removing a path or string from every commit; needs a force-push |

**See it on a real system**

```bash
# scan the whole history of the current repository, without printing the secrets themselves
docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:VERSION git --redact -v /repo
```

```
Finding:     GITLAB_TOKEN=REDACTED
Secret:      REDACTED
RuleID:      gitlab-pat
Entropy:     4.321928
File:        deploy/.env
Line:        3
Commit:      4f2c1d9a7be0c3e5f1a2b3c4d5e6f708192a3b4c
Author:      ops
Email:       ops@example.com
Date:        2026-09-30T16:02:11Z
Fingerprint: 4f2c1d9a7be0c3e5f1a2b3c4d5e6f708192a3b4c:deploy/.env:gitlab-pat:3

11:04AM INF 41 commits scanned.
11:04AM INF scanned ~388210 bytes (388.21 KB) in 412ms
11:04AM WRN leaks found: 1
```

→ A GitLab personal access token was committed two days ago in `deploy/.env`. The current
version of the file may be clean; the finding comes from history. `--redact` keeps the secret out
of your terminal scrollback and CI logs, which matters because the scanner's own output is a new
place for the secret to leak.

**Hands-on lab (test VM only)**

Use a throwaway local repository and a fake token, generated so that no real-looking token is
printed in this handbook.

**Step 1 — Break it: commit a secret, then "remove" it.**

```bash
mkdir -p ~/leaklab && cd ~/leaklab && git init -q
mkdir deploy && echo "GITLAB_TOKEN=glpat-$(head -c 32 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 20)" > deploy/.env
git add . && git commit -qm "add deploy config"
git rm -q deploy/.env && echo 'deploy/.env' > .gitignore && git add .gitignore && git commit -qm "remove env file"
ls deploy/ ; git log --oneline
```

The file is gone from the working tree, and anyone would say the repository is clean.

**Step 2 — Detect it.** Run gitleaks as in "See it": it finds the token in the first commit.
Run trufflehog too, which can also check whether a credential is live:

```bash
docker run --rm -v "$PWD:/repo" trufflesecurity/trufflehog:VERSION git file:///repo --results=verified,unknown
```

(The fake token cannot be verified, so with `--results=verified,unknown` trufflehog does not list it
at all; add `unverified` to that list to see it. A real leaked token would show as **verified**,
which means "rotate now".)

**Step 3 — Fix it in the right order.** First revoke and replace the token in GitLab (user
settings, access tokens). Then, if the repository is shared, rewrite history and force-push:

```bash
git filter-repo --invert-paths --path deploy/.env --force     # git-filter-repo package
git log --all --oneline -- deploy/.env                        # prints nothing now
```

On GitLab, a force-push to a protected branch needs it temporarily unprotected (or "Allowed to force
push"), and old merge-request refs (`refs/merge-requests/*`) keep the blob until you use GitLab's
repository cleanup or *Remove blobs* tool (Settings → Repository → Repository maintenance);
housekeeping alone does not remove it. Another reason rotation, not deletion, is the real fix.

**Step 4 — Prevent it.** Install the gitleaks binary from its official release and add a
pre-commit hook, so the next leak is stopped on the laptop:

```bash
cat > .git/hooks/pre-commit <<'HOOK'
#!/bin/sh
exec gitleaks git --pre-commit --staged --redact -v
HOOK
chmod +x .git/hooks/pre-commit
```

Add the same scan as a CI job (section 8) so a missing hook on one laptop does not matter.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Secret in history only | "the file is deleted", scanner still finds it | `gitleaks git -v` | this topic |
| `.env` committed before `.gitignore` | `.gitignore` has no effect on it | `git ls-files | grep -i env` | this topic |
| Scanner prints the secret into CI logs | new copy of the secret in job output | add `--redact` | section 8 |
| False positives block every pipeline | team disables the scanner | maintain a reviewed allowlist or baseline | this topic |

**Why it matters for troubleshooting.** When an account is used from an unexpected place,
"where could this credential have leaked?" is the first question, and a history scan of every
repository answers it in minutes.

**Next step:** give the pipeline its secrets without putting them in the repository.

### GitLab CI variables

**Level:** [L1 · Junior] to use, [L2 · Mid] to design

**Concept.** GitLab CI/CD variables keep secrets out of `.gitlab-ci.yml`. Three settings decide
how safe a variable is. **Masked** replaces the value with `[MASKED]` in job logs. **Protected**
makes it available only to pipelines on protected branches and tags, so a feature branch (or a
merge request from anyone with Developer access) cannot read the production password. **Hidden**
(the "Masked and hidden" visibility option in recent GitLab versions) also stops anyone reading
the value back in the UI. **File** type writes the value to a temporary file and puts the *path*
in the variable, which is what tools like `kubectl --kubeconfig` and `cosign --key` expect.

Precisely: masking is a string replacement on the log stream. It cannot catch a transformed
value: `echo "$TOKEN" | base64`, a URL-encoded copy, or a value split across lines all print in
clear. And `CI_DEBUG_TRACE: "true"` prints every variable of the job; GitLab warns about it for
that reason. The senior answer is to need fewer stored secrets at all: GitLab can issue each job
a short-lived **OIDC ID token** (`id_tokens:`), which Vault or AWS exchange for temporary
credentials (sections 5 and 10).

**Key terms**

| Term | Meaning |
|---|---|
| Masked | value hidden in job logs; must be a single line of at least 8 characters GitLab can mask (the UI says when it cannot) |
| Protected | only exposed to protected branches and tags |
| Environment scope | only exposed to jobs that deploy to a matching `environment:` |
| Expand variable reference | when on, `$` in the value is expanded; turn it off for values containing `$` |
| `id_tokens` | job-specific OIDC JWT with an audience you choose |

**See it on a real system**

In a job (on a protected branch), print only metadata, never values:

```bash
# inside a CI job
echo "user set: ${HARBOR_ROBOT_USER:+yes}, token length: ${#HARBOR_ROBOT_TOKEN}"
echo "kubeconfig is a file: $KUBECONFIG_PROD"
printf '%s' "$HARBOR_ROBOT_TOKEN" | base64 | head -c 12; echo '...  <- masking does not cover this'
```

```
user set: yes, token length: 32
kubeconfig is a file: /builds/platform/shop.tmp/KUBECONFIG_PROD
WkV6bU5zcGtR...  <- masking does not cover this
```

→ Checking presence and length is safe debugging. The third line shows the limit of masking: a
transformed value is not recognised, so a debug `base64` or `env | sort` in a job is a leak.

**Hands-on lab (test VM only)**

On your throwaway GitLab project, with a lab Harbor robot account:

**Step 1 — Build.** Create `HARBOR_ROBOT_USER` (visible) and `HARBOR_ROBOT_TOKEN` (masked,
protected) under Settings → CI/CD → Variables, and use them like this:

```yaml
push:
  image: docker:VERSION
  services: ["docker:VERSION-dind"]
  script:
    - echo "$HARBOR_ROBOT_TOKEN" | docker login -u "$HARBOR_ROBOT_USER" --password-stdin harbor.example.com
    - docker build -t harbor.example.com/lab/app:$CI_COMMIT_SHORT_SHA .
    - docker push harbor.example.com/lab/app:$CI_COMMIT_SHORT_SHA
```

`--password-stdin` keeps the token out of the process list and the shell history.

**Step 2 — Break it, two ways.** Push the same pipeline on an unprotected feature branch. Then,
on `main`, rename the robot account to Harbor's real format, `robot$lab+gitlab-ci`, with
"Expand variable reference" left on.

```
Error: Cannot perform an interactive login from a non TTY device
```

```
Error response from daemon: Get "https://harbor.example.com/v2/": unauthorized: authentication required
```

→ The first error is from the feature branch: the protected token variable is not exposed there,
so `--password-stdin` reads an empty password and `docker login` tries to fall back to an
interactive prompt, which a CI job cannot answer. (If the username variable were the empty one,
the error would be `Must provide --username with --password-stdin`.) The second comes from
GitLab expanding `$lab` inside `robot$lab+gitlab-ci` to an empty string, so Harbor sees the user
`robot+gitlab-ci`.

**Step 3 — Fix.** Run deploy jobs only on protected branches (`rules: - if: $CI_COMMIT_REF_PROTECTED == "true"`),
and turn off "Expand variable reference" for any value containing `$`. Give the robot account
the narrowest permissions (push to one project) and an expiry date.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Protected variable on an unprotected branch | empty value, login errors only on feature branches | `echo "${VAR:+set}"` in the job | this topic |
| `$` in a value expanded | wrong username or password, only in CI | check "Expand variable reference" | this topic |
| Value cannot be masked | GitLab refuses to save it as masked | store it as a file variable, or encode it once at rest | this topic |
| Secret printed transformed | value visible in the job log | search the log, then rotate | the leaked-secret scenario below |

**Why it matters for troubleshooting.** "Works on main, fails on my branch" and "works locally,
401 in CI" are nearly always variable scoping or expansion. Checking presence and length first
saves an afternoon.

**Next step:** what to do when a secret leaks anyway.

### Scenario: a secret was pushed

**Level:** [L2 · Mid] to execute, [L3 · Senior] to own. Trigger: the gitleaks CI job fails on
`main`, or a colleague says "I think I pushed the Harbor robot token".

**Step 1 — Confirm and classify the secret**

**Goal:** know exactly which credential leaked, what it grants and since when.

```bash
gitleaks git --redact -v . 2>/dev/null | grep -E '^(RuleID|File|Commit|Date):'
git branch -r --contains 9b1e44c
```

```
RuleID:      generic-api-key
File:        deploy/harbor.env
Commit:      9b1e44c0d2a5f6e7b8c9d0e1f2a3b4c5d6e7f809
Date:        2026-10-02T08:41:30Z
  origin/main
  origin/feature/new-deploy
```

**What it means:** a Harbor credential has been on `main` and a feature branch since 08:41 UTC.
Everyone who cloned or fetched since then, and every CI job that ran, has a copy.

**Why this step (now):** the response depends on what the credential can do. A pull-only robot
for one project is an annoyance; an admin password or a cloud key is an incident. Two minutes of
classification set the urgency for everything else.

**Next step:** if it is a test value or a revoked credential → clean history at leisure (Step 5)
and close. If it is live → Step 2 immediately, before anything else.

**Step 2 — Revoke and replace the credential first**

**Goal:** make the leaked value useless.

```bash
# Harbor: Projects → shop → Robot Accounts → gitlab-ci → Refresh secret (or delete and recreate)
# then update the masked, protected GitLab variable and check the new one works:
echo "$NEW_ROBOT_TOKEN" | docker login -u 'robot$shop+gitlab-ci' --password-stdin harbor.example.com
```

```
Login Succeeded
```

**What it means:** the new secret works; the old one no longer does (verify that too with a
`docker login` using the old value, which must now fail).

**Why this step (now):** every minute the old value stays valid is exposure, and nothing you do to
Git history removes copies that already exist. Rotation is the only step that actually ends the
risk, so it comes before cleanup, before investigation, before the postmortem.

**Next step:** if rotation breaks a deployment that also used the old secret → update that
consumer now (this tells you where else it was copied). Then → Step 3.

**Step 3 — Look for use of the leaked credential**

**Goal:** find out whether anyone used it between the leak and the rotation.

```bash
# Harbor keeps an audit log (Logs page / audit-log API); filter on the robot account:
curl -su admin "https://harbor.example.com/api/v2.0/audit-logs?q=username%3Drobot%24shop%2Bgitlab-ci&page_size=50" \
  | jq -r '.[] | [.op_time, .operation, .resource] | @tsv'
```

```
2026-10-02T09:02:11Z	pull	shop/api:1.8.0
2026-10-02T09:02:15Z	create	shop/api:9b1e44c
2026-10-02T10:17:40Z	pull	shop/api:1.8.0
```

**What it means:** the pushes and pulls line up with your own CI pipelines (compare with the
pipeline times). An operation at an odd time, or from a project or tag your CI never touches,
would mean misuse. (The audit log records the operation, not the source IP; Harbor's core logs
and your proxy's access log hold the client addresses.)

**Why this step (now):** rotation stopped future misuse; this step answers whether past misuse
happened, which decides whether this stays a cleanup ticket or becomes a security incident.

**Next step:** if there is unexplained use → treat it as an incident (section 13) and check what
was pulled or pushed (a pushed image under an existing tag is a supply-chain compromise, section 8).
If all use is explained → Step 4.

**Step 4 — Find every other copy**

**Goal:** make sure no other place still holds the old value or will reintroduce it.

```bash
git log --all --oneline -- deploy/harbor.env | head
grep -rIl --exclude-dir=.git 'robot\$shop+gitlab-ci' ~/src 2>/dev/null
```

```
9b1e44c add harbor env for deploy
/home/ops/src/shop-api/deploy/harbor.env
/home/ops/src/infra/ansible/group_vars/prod/vars.yml
```

**What it means:** the same robot credential also sits in clear text in an Ansible variables
file. It was rotated in Step 2, but whoever runs that playbook will now get failures, and the file
is the next leak waiting to happen.

**Why this step (now):** a leak is usually a symptom of a habit. Finding the other copies while the
incident has everyone's attention is how you remove the habit, not just this instance.

**Next step:** move the remaining copies into Ansible Vault or sops (next topic) → Step 5.

**Step 5 — Clean history and prevent recurrence**

**Goal:** remove the file from history and stop the next push.

```bash
git filter-repo --invert-paths --path deploy/harbor.env --force
git remote add origin git@gitlab.example.com:shop/api.git   # filter-repo removes 'origin' on purpose
git push --force origin main feature/new-deploy             # no remote-tracking refs left for --force-with-lease
gitleaks git --redact -v . ; echo "exit=$?"
```

```
11:52AM INF 44 commits scanned.
11:52AM INF no leaks found
exit=0
```

**What it means:** the repository history no longer contains the file. Ask everyone with a clone
to re-clone (an old clone pushed back would reintroduce it).

**Why this step (now):** last, because it is disruptive (force-push, re-clones) and protects less
than rotation did. It is still worth doing so the next scan is clean and the next junior does not
find a working-looking credential in history.

**Next step:** add the pre-commit hook and the CI secret-scanning job (section 8), and record a
short postmortem (section 13): how it leaked, how long it was exposed, what you changed.

**Decision tree**

```
Secret found in Git
│
├─ Live credential? ── no ──► clean history later, close
│
└─ yes ─► 1. ROTATE NOW (before anything else)
          2. audit logs: any use you cannot explain? ── yes ──► security incident (section 13)
          3. find other copies (repos, Ansible, wikis, CI logs) ─► move to Vault / sops
          4. filter-repo + force-push + re-clone
          5. pre-commit hook + CI scan + short postmortem
```

**Fix & verify:** the old credential fails, the new one works in every consumer, gitleaks finds
nothing in history, and the CI secret-scanning job is green.

**Rollback:** there is none for rotation, and you would not want one. If a consumer breaks, roll
it *forward* to the new secret.

**Prevent it next time:** pre-commit hooks, CI secret detection on every branch, robot accounts
with expiry dates, and OIDC-based short-lived credentials wherever the target supports them.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| History rewritten, no rotation | the "removed" token still works | test the old credential | this topic |
| Old clone pushed back | the secret reappears in history | `gitleaks git` in CI on every push | section 8 |
| Rotation forgot a consumer | deploys fail after rotation | grep for the old value's location (Step 4) | this topic |

**Why it matters for troubleshooting.** The order (rotate, check use, find copies, clean,
prevent) is the same for every leaked credential, from a robot token to an AWS key. Under pressure,
people do it backwards; having the order written down is the fix.

**Next step:** store the secrets your automation needs, encrypted.

### Ansible Vault and sops

**Level:** [L3 · Senior] (using an existing vault file is [L2 · Mid])

**Concept.** Some secrets must live next to code: the database password an Ansible role
templates into a config file, the values a Kubernetes manifest needs. **Ansible Vault** encrypts
whole files or single values with a password. **sops** encrypts only the *values* in YAML, JSON,
ENV or INI files, with keys from **age**, PGP or a cloud KMS, so diffs and code review still show
which keys changed. Either way, the repository holds ciphertext and the decryption key lives
somewhere else (a password manager, a KMS, the CI runner's protected variable).

**Key terms**

| Term | Meaning |
|---|---|
| `ansible-vault encrypt_string` | encrypts one value for pasting into a YAML file |
| `--vault-id LABEL@SOURCE` | names a vault password and where to get it (`prompt`, a file, a script) |
| age | a small modern encryption tool; its public keys start with `age1` |
| `.sops.yaml` | rules mapping file paths to the keys that may decrypt them |
| Envelope encryption | data encrypted with a data key, data key encrypted with your master key |

**See it on a real system**

```bash
ansible-vault encrypt_string --vault-id prod@prompt 'S3cr3t-lab-only' --name 'vault_db_password'
sops -e secrets/prod.yaml | head -n 8
```

```
New vault password (prod):
Confirm new vault password (prod):
Encryption successful
vault_db_password: !vault |
          $ANSIBLE_VAULT;1.2;AES256;prod
          62313465366332623539346533366461663764373238363435383461643235616661353334336337
          3933376132353065393165613761326261303437356638390a643761363864373636343239366235
          ...
db_password: ENC[AES256_GCM,data:Tr3x9QkZ1wP0aLm8cV2e,iv:3s0vK2dP...,tag:Qm8x...,type:str]
db_user: ENC[AES256_GCM,data:Xq2b7A==,iv:Hq7v...,tag:p1Lk...,type:str]
sops:
    age:
        - recipient: AGE_PUBLIC_KEY
          enc: |
            -----BEGIN AGE ENCRYPTED FILE-----
            YWdlLWVuY3J5cHRpb24ub3JnL3YxCi0+IFgyNTUxOSBF...
```

→ Ansible Vault output is a block you paste into `group_vars`. The sops file keeps its keys
(`db_password`, `db_user`) readable and encrypts the values, with metadata saying which age key
can decrypt it.

**Hands-on lab (test VM only)**

**Step 1 — Build with Ansible Vault.** Put `vault_db_password` in
`group_vars/prod/vault.yml`, reference it from `group_vars/prod/vars.yml` as
`db_password: "{{ vault_db_password }}"`, and run
`ansible-playbook site.yml --vault-id prod@prompt`. The indirection (`vault_` prefix) lets
reviewers see which variables are secret without decrypting anything.

**Step 2 — Build with sops and age.**

```bash
mkdir -p -m 700 ~/.config/sops/age                   # age-keygen does not create the directory
age-keygen -o ~/.config/sops/age/keys.txt            # prints the public key; the file holds the private key
cat > .sops.yaml <<'EOF'
creation_rules:
  - path_regex: secrets/.*\.yaml$
    age: AGE_PUBLIC_KEY
EOF
sops -e -i secrets/prod.yaml                         # encrypt in place
sops -d secrets/prod.yaml                            # decrypt to stdout
sops secrets/prod.yaml                               # edit in $EDITOR, re-encrypted on save
```

**Step 3 — Break it: lose the key.** Move `~/.config/sops/age/keys.txt` away and run
`sops -d secrets/prod.yaml`. sops fails with an error that no key could decrypt the data key.
Without a second recipient (a team key, a KMS key in `.sops.yaml`), those secrets are gone.

**Step 4 — Fix and design it properly.** Add at least two recipients (your key plus a team or
break-glass key kept offline), store the CI's private key as a protected file variable, and
document key rotation (`sops updatekeys` after changing `.sops.yaml`).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Vault password file committed | encryption is decorative | `git ls-files | grep -i vault` | this area, Git topic |
| Single recipient lost | `sops -d` cannot decrypt | check `.sops.yaml` recipients | this topic |
| Decrypted file left on disk | plain secrets in `/tmp` or the workspace | `find . -name '*.dec*'` | this topic |
| Playbook prints the secret | value visible with `-v` | add `no_log: true` to tasks that handle secrets | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |

**Why it matters for troubleshooting.** "The playbook works for me but not in CI" is usually the
CI missing the vault password or the age key; encrypted values make the error obvious
(`Attempting to decrypt but no vault secrets found`) instead of a silent wrong value.

**Next step:** a central secrets service for when files are not enough.

### HashiCorp Vault

**Level:** [L3 · Senior]

**Concept.** A secrets **service** instead of secrets **files**. Clients authenticate (an
AppRole, a Kubernetes ServiceAccount, a GitLab job's OIDC token), receive a short-lived token
limited by a **policy**, and read only the paths that policy allows. Every read is audited. Vault
can also issue **dynamic secrets**: a database user or AWS credentials created on request and
deleted when their lease ends, so there is nothing long-lived to leak.

Precisely: Vault stores data encrypted and starts **sealed**; it needs unseal keys (or an
auto-unseal KMS) before it can serve. Production needs HA storage (integrated Raft), backups of
that storage, TLS, audit devices, and a tested unseal procedure, which makes Vault an [L3 · Senior]
platform commitment, not a weekend install. Since 2023 Vault is under the Business Source License;
**OpenBao** is the community fork (Linux Foundation) with a largely compatible API and its own
`bao` CLI. Many teams are well served by sops plus GitLab
variables until they need dynamic secrets.

**Key terms**

| Term | Meaning |
|---|---|
| Seal / unseal | Vault cannot read its own storage until unsealed |
| Auth method | how a client proves identity: `approle`, `kubernetes`, `jwt` (GitLab OIDC) |
| Policy | HCL rules: which paths, which capabilities |
| KV v2 | versioned key/value engine; API paths contain `/data/` |
| Lease / TTL | lifetime of a token or dynamic secret; revoked when it ends |

**See it on a real system**

```bash
# lab only: an in-memory, auto-unsealed dev server with a known root token. Never in production.
vault server -dev -dev-root-token-id=lab-root >/tmp/vault-dev.log 2>&1 &
export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=lab-root
vault kv put secret/shop/db password='S3cr3t-lab-only'
vault kv get -field=password secret/shop/db
```

```
== Secret Path ==
secret/data/shop/db

======= Metadata =======
Key                Value
---                -----
created_time       2026-10-02T12:10:03.511Z
custom_metadata    <nil>
deletion_time      n/a
destroyed          false
version            1
S3cr3t-lab-only
```

→ The CLI path is `secret/shop/db`, the API path is `secret/data/shop/db`; policies must use the
`/data/` form, the most common Vault policy mistake.

**Hands-on lab (test VM only)**

**Step 1 — Build a least-privilege policy and token.**

```bash
vault policy write shop-read - <<'EOF'
path "secret/data/shop/*" {
  capabilities = ["read"]
}
EOF
SHOP_TOKEN=$(vault token create -policy=shop-read -ttl=15m -field=token)
VAULT_TOKEN=$SHOP_TOKEN vault kv get -field=password secret/shop/db
```

**Step 2 — Break it: write the policy without `/data/`.** Rewrite it as `path "secret/shop/*"`,
create a new token and read again. The read fails with `permission denied` (403), although the
policy "obviously" allows it.

**Step 3 — Fix and explore.** Restore `secret/data/shop/*`. Then let the token expire (15
minutes) and watch the read fail with `permission denied` again; that expiry is the property you
are buying with Vault. For GitLab, the `jwt` auth method lets a job log in with its `id_tokens`
JWT and a role bound to the project path and branch, so no Vault token is ever stored in GitLab.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Policy path without `/data/` (KV v2) | `permission denied` on a path the policy names | `vault token lookup`, `vault policy read NAME` | this topic |
| Vault sealed after a restart | every client fails, `Vault is sealed` | `vault status` | [Services & systemd](07-services-systemd.md) |
| Token TTL shorter than the job | job fails halfway with 403 | `vault token lookup` (ttl) | this topic |
| Vault down | every deploy blocked | `vault status`, HA peers | [Senior architecture](39-learn-senior-architecture.md) |

**Why it matters for troubleshooting.** Once secrets come from a service, "the app cannot connect
to the database" has a new layer: did it get a secret, and was the lease still valid? Vault's audit
log answers both.

**Next step:** know the limits of the secret features built into Docker and Kubernetes.

### Docker and Kubernetes secrets limits

**Level:** [L2 · Mid]

**Concept.** Environment variables are the most common way to give a container a secret and the
leakiest. They show in `docker inspect`, in `/proc/PID/environ`, in crash reports and debug pages,
and they are inherited by every child process. **Swarm secrets** are better: encrypted in the
Swarm's Raft log, delivered only to services that are granted them, mounted as files on a tmpfs at
`/run/secrets/NAME`. **Compose secrets** without Swarm are just bind-mounted files from the host,
better than env vars but no more. **Kubernetes Secrets** are only base64-*encoded*, stored in plain
text in etcd unless you enable encryption at rest (section 7), and readable by anyone who can `get`
secrets in the namespace, or who can **create a pod** there (the pod can mount any secret in its
namespace).

**Key terms**

| Term | Meaning |
|---|---|
| `/run/secrets/NAME` | where Swarm (and Compose) mount a secret inside the container |
| `_FILE` convention | many images read `POSTGRES_PASSWORD_FILE=/run/secrets/...` instead of the value |
| base64 | an encoding, not encryption; `base64 -d` reverses it |
| External Secrets / Sealed Secrets | Kubernetes add-ons that sync from Vault or a KMS, or store encrypted secrets in Git |

**See it on a real system**

```bash
docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' shop-api | grep -iE 'pass|token|secret'
sudo cat /proc/$(pgrep -f gunicorn | head -n1)/environ | tr '\0' '\n' | grep -i pass
kubectl -n shop get secret db -o jsonpath='{.data.password}' | base64 -d; echo
```

```
DATABASE_PASSWORD=S3cr3t-lab-only
DATABASE_PASSWORD=S3cr3t-lab-only
S3cr3t-lab-only
```

→ Three commands, three plain-text copies of the same password. Anyone in the `docker` group,
anyone with root, and anyone with `get secrets` in `shop` can read it.

**Hands-on lab (test VM only)**

**Step 1 — Build the env-var version, then break it.** Run
`docker run -d --name envdemo -e DB_PASSWORD=S3cr3t-lab-only alpine sleep 3600` and read the value
back with `docker inspect` as a user in the `docker` group.

**Step 2 — Fix with a Swarm secret.** On a Swarm node (Dokploy hosts are Swarm managers):

```bash
printf '%s' 'S3cr3t-lab-only' | docker secret create shop_db_password -
docker service create --name secretdemo --secret shop_db_password alpine sleep 3600
docker exec "$(docker ps -q -f name=secretdemo)" sh -c 'ls -l /run/secrets; mount | grep secrets'
docker service inspect secretdemo --format '{{json .Spec.TaskTemplate.ContainerSpec.Secrets}}'
```

```
total 4
-r--r--r--    1 root     root            15 Oct  2 12:31 shop_db_password
tmpfs on /run/secrets/shop_db_password type tmpfs (ro,relatime)
[{"File":{"Name":"shop_db_password","UID":"0","GID":"0","Mode":292},"SecretID":"q3x8k1v0m2n9b7c5z4l6j8h1g","SecretName":"shop_db_password"}]
```

→ The value is in a read-only tmpfs file, and `service inspect` shows only the secret's name and
ID, never the value. Secrets are immutable: rotation means creating `shop_db_password_v2` and
updating the service to use it.

**Step 3 — Kubernetes: reduce who can read.** Check `kubectl auth can-i get secrets -n shop
--as=system:serviceaccount:shop:default` (it should be `no`), enable encryption at rest
(section 7), and for secrets that come from Vault or a cloud KMS use an operator rather than
copying values into manifests.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Secret in an env var | visible in `docker inspect` | `docker inspect --format '{{.Config.Env}}' C` | this topic |
| Secret baked into an image layer | `docker history` or Trivy's secret scanner finds it | `trivy image --scanners secret IMAGE` | section 6 |
| App reads env, secret is a file | app starts with an empty password | check for a `_FILE` variant in the image docs | [Learn Docker](30-learn-docker.md) |
| Broad `get secrets` RBAC | many identities can read every secret | `kubectl auth can-i --list -n NS --as=...` | section 7 |

**Why it matters for troubleshooting.** When a credential leaks from a running system, these are
the places it leaked from. And when an app "cannot read its password" after a move to files, the
`_FILE` convention and mount permissions are the first things to check.

**Next step:** harden the containers that hold these secrets.

---

## 6. Container security

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Engine – Security (namespaces, capabilities, seccomp), then Docker Image Management: [Multi-Stage Builds](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Image-Management/Multi-Stage-Builds/page) ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · 2) Note: the Security area (section 13) and the registries area (section 11) of [Learn Docker](30-learn-docker.md), which this area builds on · 3) After the CKA: *Certified Kubernetes Security Specialist (CKS)* — System Hardening and Minimize Microservice Vulnerabilities, then Supply Chain Security for image scanning ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · 4) Docs: vulnerability scanning and project policies in the [Harbor docs](https://goharbor.io/docs/) — KodeKloud has no Harbor course · 5) Practice: the labs below on sec-target, or the free [Docker playground](https://kodekloud.com/playgrounds/playground-docker) for the capability and read-only experiments.

A container is not a small virtual machine. It is an ordinary Linux process that the kernel shows a
reduced view of the system, with some of root's powers removed. Every control in this area either
keeps those reductions in place (non-root users, dropped capabilities, seccomp, AppArmor, a
read-only filesystem) or reduces what is inside the image to attack (minimal bases, scanning,
registry policy). Learn Docker section 13 explains the mechanisms; this area turns them into
defaults you can enforce and audit on sec-target, on your Dokploy host and in Harbor.

### Containers share the kernel

**Level:** [L1 · Junior] to understand, [L2 · Mid] to audit

**Concept.** Each container is a process (or a few) on the host. Isolation comes from layers the
kernel applies to that process, and all containers share one kernel:

```
             container process: PID 2481 on the host, PID 1 inside
                    │
  ┌─────────────────┼────────────────────────────────────────────────┐
  │ user            │ the image's USER: root (uid 0) or 10001        │ who it is
  │ namespaces      │ pid, net, mnt, uts, ipc, cgroup                 │ what it can see
  │ cgroups         │ memory, CPU and pids limits                     │ how much it can use
  │ capabilities    │ 14 of root's ~41 powers by default              │ which root powers remain
  │ seccomp         │ default profile blocks dozens of risky syscalls │ which kernel calls
  │ AppArmor        │ docker-default profile on Ubuntu                │ which files and operations
  └─────────────────┼────────────────────────────────────────────────┘
                    ▼
           ONE shared host kernel   ◄── a kernel CVE affects every container at once
```

Precisely: without user namespaces, uid 0 in the container **is** uid 0 on the host, held back
only by the capability, seccomp and AppArmor layers. Some options remove those layers wholesale,
and those options are what you audit for:

| Option | What it removes | Legitimate users |
|---|---|---|
| `--privileged` | all capabilities granted, seccomp and AppArmor off, all host devices visible | almost none; some low-level tools during setup |
| `-v /var/run/docker.sock:...` | the daemon itself becomes reachable: root-equivalent (next topic) | Dokploy, Traefik's Docker provider, CI tooling |
| `-v /:/host` or other sensitive host paths | the host filesystem is writable from inside | backup and monitoring agents, ideally read-only |
| `--pid=host`, `--network=host` | the pid or network namespace | node_exporter, some network tools |
| `--cap-add SYS_ADMIN` | the broadest single capability ("the new root") | rarely justified |

**Key terms**

| Term | Meaning |
|---|---|
| Namespace | kernel feature that gives a process its own view of PIDs, network, mounts, hostname |
| Capability | one slice of root's power, such as `CAP_NET_BIND_SERVICE` or `CAP_SYS_ADMIN` |
| seccomp | kernel syscall filter; Docker applies a default profile to every container |
| AppArmor | Ubuntu's mandatory access control; containers get the `docker-default` profile |
| Breakout | a process escaping its container's restrictions to act on the host |

**See it on a real system**

```bash
docker info --format '{{.SecurityOptions}}'
docker run -d --name kdemo alpine:3.20 sleep 600
ps -o pid,user,cmd -C sleep
docker ps -q | xargs docker inspect --format \
  '{{.Name}} priv={{.HostConfig.Privileged}} user={{.Config.User}} pid={{.HostConfig.PidMode}} net={{.HostConfig.NetworkMode}} capadd={{.HostConfig.CapAdd}} apparmor={{.AppArmorProfile}}'
```

```
[name=apparmor name=seccomp,profile=builtin name=cgroupns]
    PID USER     CMD
   2481 root     sleep 600
/kdemo priv=false user= pid= net=bridge capadd=[] apparmor=docker-default
/dokploy-traefik priv=false user= pid= net=dokploy-network capadd=[] apparmor=docker-default
/shop-api.1.p3k9x priv=false user=10001 pid= net=bridge capadd=[] apparmor=docker-default
/node-exporter priv=false user=nobody pid=host net=host capadd=[] apparmor=docker-default
/legacy-backup priv=true user= pid= net=bridge capadd=[] apparmor=unconfined
```

→ The container's `sleep` shows up in the host's process list as `root`: there is no user
namespace, so that is real uid 0, restricted only by the other layers. An empty `user=` means the
image default, which is root for most images. `legacy-backup` is privileged and unconfined: that
is the first finding to chase. `node-exporter` shares the host pid and network namespaces, which
is expected for it; it belongs on a written exceptions list with the reason, so the next audit does
not have to rediscover why.

**Hands-on lab (test VM only)**

**Step 1 — Build a baseline.** Save the audit loop above into `~/container-audit.sh`, run it on
sec-target and store the output as `~/container-baseline.txt`. Write one line per expected
exception (who needs it and why).

**Step 2 — Break it.** Start a privileged container, as a careless colleague might do "to make it
work":

```bash
docker run -d --name privdemo --privileged alpine:3.20 sleep 600
docker exec privdemo grep CapEff /proc/1/status
~/container-audit.sh | diff ~/container-baseline.txt -
```

```
CapEff:	000001ffffffffff
0a1
> /privdemo priv=true user= pid= net=bridge capadd=[] apparmor=unconfined
```

→ `000001ffffffffff` is every capability the kernel knows, and AppArmor is off. The diff makes the
drift visible in one line, which is exactly what a scheduled audit or an alert (section 12) should
report.

**Step 3 — Fix it.** Remove the container (`docker rm -f privdemo kdemo`). In real life, find out
what the workload actually needed (usually one device or one capability), grant only that, and add
it to the exceptions list with an owner.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Privileged container in production | audit shows `priv=true`, `apparmor=unconfined` | the audit loop above | this topic |
| Host path mounted read-write | container can change host files | `docker inspect --format '{{json .Mounts}}' C | jq` | next topic |
| Kernel vulnerability | every container exposed at once | `uname -r`, then section 11 | section 11 |
| A dropped capability is needed | `Operation not permitted` at start | `docker logs C` | capabilities topic below |

**Why it matters for troubleshooting.** "Operation not permitted", "Permission denied" and
"Read-only file system" inside containers are very often a security layer doing its job. Knowing
which layer applies to a container turns those errors from mysteries into a two-minute check.

**Next step:** the option that removes every layer at once, the Docker socket.

### Docker socket and group audit

**Level:** [L2 · Mid]

**Concept.** The Docker daemon runs as root and carries out whatever any client on its socket
asks, including starting containers with host directories mounted. Therefore these four things are
all **equivalent to root on the host**: membership of the `docker` group, write access to
`/var/run/docker.sock`, a container that mounts that socket, and an unauthenticated TCP API on
2375. [Learn Docker](30-learn-docker.md) section 13 explains why; this topic is about auditing
and reducing it.

On a Dokploy host two containers legitimately mount the socket: Dokploy itself (it creates and
updates services) and `dokploy-traefik` (its Docker and Swarm providers read container labels).
That makes both of them high-value targets: a remote-code-execution bug in either one is root on
the host. You cannot remove those mounts without breaking Dokploy, so you compensate: patch Dokploy
and Traefik promptly (section 11), keep the Dokploy UI off the internet (section 3), keep the
Traefik dashboard closed (section 9), and alert on any *new* socket mount (section 12).

**Key terms**

| Term | Meaning |
|---|---|
| `docker.sock` | the Unix socket `/var/run/docker.sock` where dockerd takes API calls (`/var/run` is a symlink to `/run`, so it is the same file as `/run/docker.sock`) |
| `docker` group | group owner of the socket; members can use Docker without sudo |
| Socket proxy | a small proxy in front of the socket that only allows chosen API calls (for example read-only GETs) |
| TCP API | dockerd listening on 2375 (plain) or 2376 (TLS); plain 2375 means anyone who reaches it is root |
| `:ro` socket mount | read-only applies to the file, **not** the API: a client can still send any request |

**See it on a real system**

```bash
getent group docker
ls -l /var/run/docker.sock
sudo ss -ltnp | grep -E ':(2375|2376)\b' || echo "no TCP API listener"
docker ps -q | xargs docker inspect --format '{{.Name}}{{range .Mounts}} {{.Source}}{{end}}' | grep docker.sock
```

```
docker:x:999:deploy,alice,gitlab-runner
srw-rw---- 1 root docker 0 Oct  3 08:02 /var/run/docker.sock
no TCP API listener
/dokploy.1.k3x9p /var/run/docker.sock
/dokploy-traefik /etc/dokploy/traefik/traefik.yml /etc/dokploy/traefik/dynamic /var/run/docker.sock
```

→ Three accounts are effectively root on this host. `gitlab-runner` is the worrying one: with a
shell executor, every CI job from every project allowed to use this runner can drive the daemon.
That is why [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) builds images with DinD or on a dedicated
build host instead of on the Dokploy host. The two socket mounts are the expected Dokploy ones;
anything else is a finding.

**Hands-on lab (test VM only)**

**Step 1 — Build the inventory.** A read-only script you can also run from cron or Ansible:

```bash
cat > ~/docker-sock-audit.sh <<'EOF'
#!/usr/bin/env bash
# Read-only audit: who and what can drive the Docker daemon on this host
set -euo pipefail
echo "== docker group members"; getent group docker | cut -d: -f4
echo "== containers mounting the socket"
docker ps -q | xargs -r docker inspect --format '{{.Name}}{{range .Mounts}} {{.Source}}{{end}}' \
  | grep -E 'docker\.sock' || true
echo "== TCP API listeners"; ss -ltn | grep -E ':(2375|2376)\b' || echo none
EOF
chmod +x ~/docker-sock-audit.sh
sudo ~/docker-sock-audit.sh | tee ~/docker-sock-baseline.txt
```

**Step 2 — Break it.** Simulate drift: someone deploys a "monitoring agent" that mounts the socket,
read-only, believing that makes it safe:

```bash
docker run -d --name agent-demo -v /var/run/docker.sock:/var/run/docker.sock:ro alpine:3.20 sleep 3600
sudo ~/docker-sock-audit.sh | diff ~/docker-sock-baseline.txt -
```

```
3a4
> /agent-demo /var/run/docker.sock
```

→ The audit catches it. The `:ro` flag gives no protection: it stops the container from deleting
or replacing the socket file, but connecting to the socket and sending API calls still works.

**Step 3 — Fix it.** Remove the container. If a tool genuinely needs container metadata, give it a
socket proxy that allows only the GET endpoints it needs, on an internal network, and record the
exception. Then shrink the group:

```bash
sudo gpasswd -d alice docker      # takes effect at alice's next login
id alice                          # check in a NEW session; old sessions keep the group
```

People who still need Docker use `sudo docker ...`, which is logged in the auth log with the full
command line (section 12). That trade, a little convenience for accountability, is the point.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| New socket mount appears | diff against the baseline shows a new line | `~/docker-sock-audit.sh` | section 12 (alert on it) |
| Removed user can still run docker | an old login session still holds the group | `id USER` in a new session | [Users & permissions](10-users-permissions-security.md) |
| Dokploy upgrade recreates Traefik | manual changes to its mounts are gone | `docker inspect dokploy-traefik` | [Learn Docker](30-learn-docker.md) |
| TCP API 2375 open | port open in nmap from sec-scan | `sudo ss -ltnp | grep 2375`, `/etc/docker/daemon.json`, `systemctl cat docker` | section 3 |

**Why it matters for troubleshooting.** In any incident on a Docker host, "who could talk to the
daemon?" defines the blast radius. The same inventory answers an auditor's access-review question
(section 14), so keeping it current pays twice.

**Next step:** shrink what runs inside each container, starting with the image.

### Minimal images and non-root

**Level:** [L2 · Mid]

**Concept.** Every package in an image is code that can carry CVEs and a tool an intruder can use.
The base image decides most of your scan results; the `USER` decides what a compromise of the
application can do next.

| Base | Example | Size and CVE count | Trade-off |
|---|---|---|---|
| Full | `python:3.12` | ~1 GB, hundreds of findings | compilers and tools you never use at runtime |
| Slim | `python:3.12-slim` | ~150 MB, a handful | good default for Python and Node |
| Alpine | `python:3.12-alpine` | smallest, few findings | musl libc: some wheels must compile, subtle differences |
| Distroless / chiselled | Google distroless, Ubuntu chiselled images | tiny, no shell, no package manager | debugging needs another approach (below) |
| scratch | `FROM scratch` | only your static binary | Go and Rust static binaries only |

Run as a **numeric** non-root user. Kubernetes can only verify `runAsNonRoot` when the image's
user is numeric; with `USER app` the kubelet refuses to start the pod (section 7). Keep the code
owned by root and read-only to the app user, and give the app one writable data directory, so code
execution in the app cannot rewrite the app.

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.12-slim AS build
WORKDIR /src
COPY requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt

FROM python:3.12-slim
RUN groupadd --gid 10001 app \
 && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin app \
 && mkdir -p /data/uploads && chown 10001:10001 /data/uploads
WORKDIR /app
COPY --from=build /wheels /wheels
RUN pip install --no-cache-dir /wheels/* && rm -rf /wheels
COPY . .
USER 10001:10001
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "app:app"]
```

→ Build tools stay in the `build` stage, the code is owned by root (no `--chown`), and only
`/data/uploads` is writable by uid 10001. Section 8 adds pinning the base image by digest.

**Key terms**

| Term | Meaning |
|---|---|
| Multi-stage build | build in one stage, copy only the results into a clean final stage |
| Numeric `USER` | `USER 10001:10001`; lets runtimes verify non-root without reading `/etc/passwd` |
| Distroless | images with the runtime only: no shell, no package manager |
| Attack surface (image) | packages and binaries present at runtime that the app does not need |

**See it on a real system**

```bash
for i in shop-api:root shop-api:nonroot; do
  printf '%s user=%s vulns=' "$i" "$(docker image inspect --format '{{.Config.User}}' "$i")"
  trivy image --quiet --scanners vuln --severity HIGH,CRITICAL --format json "$i" \
    | jq '[.Results[]?.Vulnerabilities[]?] | length'
done
docker run --rm shop-api:nonroot id
docker run --rm --entrypoint ls shop-api:nonroot -ld /app /data/uploads
```

```
shop-api:root user= vulns=412
shop-api:nonroot user=10001:10001 vulns=9
uid=10001(app) gid=10001(app) groups=10001(app)
drwxr-xr-x 1 root root 4096 Oct  3 09:02 /app
drwxr-xr-x 1 app  app  4096 Oct  3 09:02 /data/uploads
```

→ `shop-api:root` was built `FROM python:3.12` without a `USER`; the slim, non-root build has 9
high or critical findings instead of 412, and the app can write only to its upload directory.

**Hands-on lab (test VM only)**

**Step 1 — Build both variants.** Build `shop-api:root` from a one-stage Dockerfile on
`python:3.12` with no `USER`, and `shop-api:nonroot` from the Dockerfile above. Run the comparison.

**Step 2 — Break it.** Make the app write uploads to `/app/uploads` (the old path) and run the
non-root image. The request fails with
`PermissionError: [Errno 13] Permission denied: '/app/uploads/report.pdf'`. The tempting "fix" is
`COPY --chown=10001:10001 . .` or `chmod -R 777 /app`. Do not take it: it makes the code writable
by the app user again.

**Step 3 — Fix it properly.** Point the upload path at `/data/uploads` (an environment variable or
config setting), mount a named volume there in production, and rebuild. Then check that a volume
created by an older root-running version is owned correctly
(`docker run --rm -v VOLUME:/d alpine:3.20 ls -ln /d`); if it is root-owned, fix ownership once with a
one-off container rather than running the app as root forever.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Writes fail after switching to non-root | `Permission denied` on a path under `/app` | `docker run --rm --entrypoint ls IMAGE -ln /app` | this topic |
| `USER app` (a name) in Kubernetes | `container has runAsNonRoot and image has non-numeric user (app), cannot verify user is non-root` | `kubectl describe pod POD` | section 7 |
| Old volume owned by root | app cannot write existing data | `ls -ln` inside a one-off container | [Learn Docker](30-learn-docker.md) |
| Alpine breaks a Python dependency | slow builds compiling wheels, or `Error loading shared library` | `ldd` on the failing library | this topic |
| No shell in a distroless image | `exec: "sh": executable file not found in $PATH` | `docker run --rm -it --pid container:C --network container:C nicolaka/netshoot` | [Containers & K8s playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting.** Most "it worked as root" bugs are file ownership, and most
"thousands of CVEs" reports are a base-image choice. Both are fixed in the Dockerfile, not on the
server.

**Next step:** take away the root powers that are left.

### Capabilities, seccomp and AppArmor

**Level:** [L2 · Mid]

**Concept.** Linux splits root's power into about 41 **capabilities**. Docker keeps 14 of them for
a container by default (`CHOWN`, `DAC_OVERRIDE`, `FOWNER`, `FSETID`, `KILL`, `SETGID`, `SETUID`,
`SETPCAP`, `NET_BIND_SERVICE`, `NET_RAW`, `SYS_CHROOT`, `MKNOD`, `AUDIT_WRITE`, `SETFCAP`). The
standard hardening is to **drop all and add back only what the process proves it needs**. Three
more layers work alongside:

- **`no-new-privileges`** stops setuid binaries (such as `su` or `sudo`) from gaining privileges inside the container.
- **seccomp**: Docker's default profile blocks syscalls such as loading kernel modules, `kexec_load` and `reboot`, and allows some others only when the matching capability is present.
- **AppArmor**: on Ubuntu every container gets the `docker-default` profile, which denies mounts and writes to sensitive `/proc` and `/sys` paths.

Two details save confusion later. Since Docker 20.10, containers get
`net.ipv4.ip_unprivileged_port_start=0` in their own network namespace, so a process inside can
bind port 80 without `NET_BIND_SERVICE`. In Kubernetes it depends on the runtime: containerd 2.x
enables `enable_unprivileged_ports` by default and sets the same sysctl in every pod with its own
network namespace, while containerd 1.7 does not, so on older nodes the same image may need the
capability. Check inside a pod with `cat /proc/sys/net/ipv4/ip_unprivileged_port_start`. And a container running as a non-root user has **no effective
capabilities** at all, even before you drop anything.

**Key terms**

| Term | Meaning |
|---|---|
| `CapEff` / `CapBnd` | effective capabilities now / the upper bound the process could ever regain |
| `--cap-drop ALL --cap-add X` | start from nothing, add only X |
| `no-new-privileges` | kernel flag: execve can never increase privileges (setuid bits are ignored) |
| `RuntimeDefault` | Kubernetes' name for the container runtime's default seccomp profile |
| `docker-default` | the AppArmor profile Docker generates and loads for containers |

**See it on a real system**

```bash
docker run --rm alpine:3.20 grep -E '^Cap(Eff|Bnd)' /proc/1/status
docker run --rm --cap-drop ALL alpine:3.20 grep CapEff /proc/1/status
docker run --rm --user 10001 alpine:3.20 grep CapEff /proc/1/status
capsh --decode=00000000a80425fb
docker run --rm alpine:3.20 grep -E '^(NoNewPrivs|Seccomp):' /proc/1/status
docker run --rm --security-opt no-new-privileges alpine:3.20 grep NoNewPrivs /proc/1/status
```

```
CapEff:	00000000a80425fb
CapBnd:	00000000a80425fb
CapEff:	0000000000000000
CapEff:	0000000000000000
0x00000000a80425fb=cap_chown,cap_dac_override,cap_fowner,cap_fsetid,cap_kill,cap_setgid,cap_setuid,cap_setpcap,cap_net_bind_service,cap_net_raw,cap_sys_chroot,cap_mknod,cap_audit_write,cap_setfcap
NoNewPrivs:	0
Seccomp:	2
NoNewPrivs:	1
```

→ Container root holds the 14 default capabilities (`a80425fb`). Dropping all, or simply running as
uid 10001, leaves none effective. `Seccomp: 2` means a filter is active. `NoNewPrivs` is off by
default and on with the flag. (`capsh` comes from the `libcap2-bin` package.)

**Hands-on lab (test VM only)**

**Step 1 — Drop everything and watch a real image fail.**

```bash
docker run --rm --cap-drop ALL nginx:1.27-alpine
```

```
/docker-entrypoint.sh: Configuration complete; ready for start up
2026/10/03 09:20:11 [emerg] 1#1: chown("/var/cache/nginx/client_temp", 101) failed (1: Operation not permitted)
nginx: [emerg] chown("/var/cache/nginx/client_temp", 101) failed (1: Operation not permitted)
```

→ The nginx master runs as root, creates its temp directories, hands them to the `nginx` user
(uid 101) and then switches to that user for the workers. That needs `CHOWN`, `SETUID` and `SETGID`.

**Step 2 — Fix it two ways.** Minimal capabilities for the standard image, adding one at a time and
re-reading the error after each:

```bash
docker run -d --name ng-caps --cap-drop ALL --cap-add CHOWN --cap-add SETUID --cap-add SETGID \
  --security-opt no-new-privileges -p 127.0.0.1:8081:80 nginx:1.27-alpine
curl -sI http://127.0.0.1:8081/ | head -n1
```

Better, use an image designed to run unprivileged, which needs no capabilities at all:

```bash
docker run -d --name ng-unpriv --cap-drop ALL --security-opt no-new-privileges \
  -p 127.0.0.1:8082:8080 nginxinc/nginx-unprivileged:1.27-alpine
curl -sI http://127.0.0.1:8082/ | head -n1
```

**Step 3 — Make it the default, carefully.** `"no-new-privileges": true` in
`/etc/docker/daemon.json` applies it to every container. Note two traps before you do that on a
Dokploy host. First, restarting dockerd restarts every container, because `live-restore` cannot be
used with Swarm mode, so this belongs in a maintenance window after a test on sec-target. Second,
`docker stack deploy` ignores `security_opt` (it prints only `Ignoring unsupported options:
security_opt`), so on Swarm the daemon-wide setting is the practical way to get
`no-new-privileges`.

**Step 4 — Confirm AppArmor is in force.**

```bash
docker inspect --format '{{.AppArmorProfile}}' ng-unpriv
sudo aa-status | grep -A1 'docker-default'
sudo journalctl -k --since today | grep 'apparmor="DENIED"' | tail -n 3
```

→ `docker-default` for normal containers, `unconfined` for privileged ones. Denials appear in the
kernel log with `profile="docker-default"`; they are the evidence when a workload hits AppArmor.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Needed capability dropped | `Operation not permitted` right at start | `docker logs C`, add back one capability at a time | this topic |
| setuid tool inside the container after `no-new-privileges` | `sudo: effective uid is not 0` or `su: Authentication failure` | redesign: no sudo or su inside containers | this topic |
| Someone added `--privileged` "to make it work" | everything works, nothing is protected | `docker inspect --format '{{.HostConfig.Privileged}}' C` | first topic of this area |
| AppArmor denies an operation | `Permission denied` although file modes allow it | `journalctl -k | grep DENIED` | [Users & permissions](10-users-permissions-security.md) |
| Suspected seccomp block | `Operation not permitted` with no capability explanation | on the lab only, retry with `--security-opt seccomp=unconfined` to confirm, then write a narrow profile | this topic |

**Why it matters for troubleshooting.** "Operation not permitted" (EPERM) usually means a
capability, seccomp or AppArmor decision; "Permission denied" (EACCES) usually means file ownership
or modes. Telling them apart sends you to the right fix the first time.

**Next step:** stop the container from changing its own filesystem.

### Read-only rootfs and limits

**Level:** [L2 · Mid]

**Concept.** With `--read-only`, the container's root filesystem cannot be written. The app writes
only where you allow: a tmpfs for scratch files and volumes for data. Nothing can be dropped into
the image paths at runtime, and the running container cannot drift from the image you scanned.
Resource limits complete the picture: a memory limit, a `pids` limit against runaway forking, and
CPU limits, so one compromised or buggy container cannot starve the host.

```bash
docker run -d --name api-ro \
  --read-only --tmpfs /tmp:rw,noexec,nosuid,size=64m \
  --user 10001:10001 --cap-drop ALL --security-opt no-new-privileges \
  --memory 512m --pids-limit 200 \
  -v shop-uploads:/data/uploads \
  shop-api:nonroot
```

The same in a Compose file. The long `volumes` form for the tmpfs works for both `docker compose`
and Swarm stacks:

```yaml
services:
  api:
    image: harbor.example.com/shop/api:1.8.0
    user: "10001:10001"
    read_only: true
    cap_drop: [ALL]
    volumes:
      - shop-uploads:/data/uploads
      - type: tmpfs
        target: /tmp
        tmpfs:
          size: 67108864
    deploy:
      resources:
        limits:
          memory: 512M
volumes:
  shop-uploads:
```

→ `docker stack deploy` ignores some service keys (`security_opt` among them) with nothing more than
an `Ignoring unsupported options` line that is easy to miss. After deploying a stack or
a Dokploy Compose app, check what was really applied with
`docker service inspect --format '{{json .Spec.TaskTemplate.ContainerSpec}}' SERVICE | jq` instead of
trusting the file.

**Key terms**

| Term | Meaning |
|---|---|
| `--read-only` / `read_only: true` | root filesystem mounted read-only |
| tmpfs | RAM-backed scratch mount; `noexec,nosuid` stop it being used to run dropped binaries |
| `--pids-limit` | maximum number of processes and threads in the container's cgroup |
| Drift | difference between the running container and its image; read-only rootfs prevents it |

**See it on a real system**

```bash
docker inspect --format 'ro={{.HostConfig.ReadonlyRootfs}} pids={{.HostConfig.PidsLimit}} mem={{.HostConfig.Memory}} tmpfs={{.HostConfig.Tmpfs}}' api-ro
docker exec api-ro sh -c 'touch /app/x; touch /tmp/x && echo tmp-ok'
docker diff api-ro | head
```

```
ro=true pids=200 mem=536870912 tmpfs=map[/tmp:rw,noexec,nosuid,size=64m]
touch: cannot touch '/app/x': Read-only file system
tmp-ok
```

→ `docker diff` prints nothing: the container has not changed its filesystem since it started, and
it cannot.

**Hands-on lab (test VM only)**

**Step 1 — Break it.** Run the unprivileged nginx image read-only without any writable path:

```bash
docker run --rm --read-only nginxinc/nginx-unprivileged:1.27-alpine
```

```
10-listen-on-ipv6-by-default.sh: info: can not modify /etc/nginx/conf.d/default.conf (read-only file system?)
2026/10/03 09:41:02 [emerg] 1#1: mkdir() "/tmp/client_temp" failed (30: Read-only file system)
nginx: [emerg] mkdir() "/tmp/client_temp" failed (30: Read-only file system)
```

**Step 2 — Fix it.** Give it exactly one writable scratch path:
`docker run --rm --read-only --tmpfs /tmp nginxinc/nginx-unprivileged:1.27-alpine`. The entrypoint
still reports that it cannot modify `default.conf`, which is harmless: you ship the configuration in
the image instead of letting a script edit it at start.

**Step 3 — Prove the pids limit.** A harmless test that tries to start 50 background sleeps in a
container allowed 20 processes:

```bash
docker run --rm --pids-limit 20 alpine:3.20 sh -c 'for i in $(seq 1 50); do sleep 30 & done; wait'
```

```
sh: can't fork: Resource temporarily unavailable
```

→ The container hits its own limit; the host and the other containers are unaffected.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| App writes somewhere unexpected | `Read-only file system` in the app log | `docker diff` on a writable test run shows the paths | this topic |
| tmpfs too small | `No space left on device` in `/tmp` only | `docker exec C df -h /tmp` | [Storage & disk](01-storage-disk.md) |
| Memory limit too low | exit code 137, `OOMKilled: true` | `docker inspect --format '{{.State.OOMKilled}}' C` | [Containers & K8s playbook](26-playbook-containers-k8s.md) |
| pids limit too low | `can't fork` or thread creation errors under load | `cat /sys/fs/cgroup/system.slice/docker-ID.scope/pids.events` (the `max` counter rises) | this topic |
| Setting ignored by Swarm | flag in the file, not on the container | `docker service inspect` | this topic |

**Why it matters for troubleshooting.** A read-only container is also an easier one to debug: if it
behaves differently from yesterday, the image or the configuration changed, never "something someone
edited inside it".

**Next step:** make container root not be host root at all.

### Rootless Docker and userns-remap

**Level:** [L3 · Senior]

**Concept.** Two features break the "container root is host root" rule:

| | userns-remap | Rootless Docker |
|---|---|---|
| Daemon runs as | root | an ordinary user |
| Container uid 0 maps to | an unprivileged range (user `dockremap`, e.g. 100000+) | that user's subordinate range |
| Swarm and overlay networks | works for many setups; test first | **not supported** (no overlay networks) |
| Ports below 1024 | normal | need a sysctl or a capability on rootlesskit |
| `--privileged`, `--pid=host`, `--network=host` | not compatible unless `--userns=host` | limited |
| Good for | hardening a single-host Docker server | CI build hosts, developer machines, shared lab VMs |

The practical conclusion for your stack: **Dokploy hosts stay rootful** (Dokploy needs Swarm and
overlay networks, and runs privileged-adjacent components). Rootless fits a dedicated build host
for GitLab jobs, where many projects' code runs and the blast radius of a job should be one user,
not the machine. Kubernetes has its own form, user namespaces for pods (`hostUsers: false`), worth
reading about after the CKS.

**Key terms**

| Term | Meaning |
|---|---|
| `/etc/subuid`, `/etc/subgid` | ranges of subordinate IDs a user may map into a namespace |
| `dockremap` | the user Docker creates for `"userns-remap": "default"` |
| rootlesskit | helper that sets up the user and network namespaces for rootless dockerd |
| `DOCKER_HOST` | where the CLI connects; for rootless, `unix:///run/user/UID/docker.sock` |

**See it on a real system** (a rootless build host):

```bash
docker info --format '{{.SecurityOptions}}'
grep -E '^ci:' /etc/subuid
ps -o user,cmd -C dockerd
```

```
[name=seccomp,profile=builtin name=rootless name=cgroupns]
ci:100000:65536
USER     CMD
ci       dockerd
```

→ `name=rootless` confirms the mode, and the daemon runs as `ci`. AppArmor is not listed: rootless
mode does not apply AppArmor profiles, one of its documented limitations.

**Hands-on lab (test VM only, on sec-scan)**

**Step 1 — Install rootless Docker for a `ci` user.**

```bash
sudo apt-get install -y uidmap docker-ce-rootless-extras
sudo useradd -m -s /bin/bash ci && sudo loginctl enable-linger ci
sudo -iu ci                                   # then, as ci, in a real login session:
dockerd-rootless-setuptool.sh install
systemctl --user enable --now docker
export DOCKER_HOST=unix:///run/user/$(id -u)/docker.sock
docker run --rm alpine:3.20 id
```

→ Inside the container `id` still says `uid=0(root)`, but on the host that process runs as a
subordinate uid of `ci`. Ubuntu 24.04 restricts unprivileged user namespaces through AppArmor, so
rootlesskit needs an AppArmor profile that allows them; Docker's rootless documentation says the
apt-installed `docker-ce-rootless-extras` setup already has one (check with
`sudo aa-status | grep -i rootlesskit`). If the setup tool stops with a message about it, follow its
printed instructions. If `systemctl --user` fails under `sudo -iu`, log in as
`ci` over SSH instead; the user systemd instance needs a real session.

**Step 2 — Break it.** Publish a privileged port: `docker run --rm -p 80:80 nginx:1.27-alpine`.

```
docker: Error response from daemon: driver failed programming external connectivity on endpoint ...:
error while calling RootlessKit PortManager.AddPort(): cannot expose privileged port 80, you can add
'net.ipv4.ip_unprivileged_port_start=80' to /etc/sysctl.conf (currently 1024), or set CAP_NET_BIND_SERVICE
on rootlesskit binary, or choose a larger port number (>= 1024)
```

**Step 3 — Fix it.** Publish a high port (`-p 8080:80`). Lowering `ip_unprivileged_port_start`
host-wide lets *every* user bind low ports, which is a host-level decision, not a container one.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Swarm or overlay on rootless | `docker swarm init` or overlay network creation fails | `docker info` (rootless?) | this topic |
| Privileged port | `cannot expose privileged port` | the error text | this topic |
| userns-remap enabled on a used host | all images and containers "disappear" | `docker info --format '{{.DockerRootDir}}'` (now a remapped subdirectory) | [Learn Docker](30-learn-docker.md) |
| Bind-mounted files show odd owners | files owned by 100000+ on the host | `ls -ln` on the host path | this topic |

**Why it matters for troubleshooting.** When files on a host appear owned by uid 100999, or a
privileged port refuses to bind on one machine only, user namespaces are the first suspect.

**Next step:** find the vulnerabilities in what you ship.

### Image scanning with Trivy

**Level:** [L2 · Mid] to run, [L3 · Senior] to run as a gate

**Concept.** Trivy reads an image's package databases (dpkg, apk, rpm) and the language manifests
and lockfiles inside it (Python, Node, Go, Java...), and matches the versions against its
vulnerability database. The same tool also finds **secrets** in image layers and
**misconfigurations** in Dockerfiles, Compose files and Kubernetes manifests. Learn Docker
section 11 introduced the basic commands; here you make scanning reliable enough to gate a pipeline.

Three facts drive most surprises:

- **The database changes, the image does not.** An image that scanned clean last month can fail today. Results always belong to a DB date.
- **Status matters more than severity.** `fixed` means an upstream fix exists and rebuilding on a fresh base usually clears it. `affected`, `will_not_fix` and `fix_deferred` mean no fix is available from the distribution; that is a triage decision (section 11), not a rebuild.
- **Severity comes from the vendor first.** For OS packages Trivy prefers the distribution's own rating (Debian, Ubuntu, Alpine), which can differ from the NVD's CVSS score.

**Key terms**

| Term | Meaning |
|---|---|
| `--scanners vuln,secret,misconfig` | what to look for; images default to `vuln,secret` |
| `--ignore-unfixed` | hide findings that have no fixed version yet |
| `--exit-code 1` | non-zero exit when findings remain: the CI gate |
| Ignore file | `.trivyignore` or `.trivyignore.yaml`: accepted findings, ideally with expiry and reason |
| `--cache-dir`, `--skip-db-update` | reuse a downloaded DB; skip downloading it again |
| `--db-repository` | where to pull the DB from (an OCI registry; a Harbor proxy cache works) |

**See it on a real system**

```bash
trivy --version
trivy image --scanners vuln,secret --severity HIGH,CRITICAL --ignore-unfixed shop-api:nonroot
trivy config --severity HIGH,CRITICAL ./Dockerfile.root
```

```
Version: VERSION
Vulnerability DB:
  Version: 2
  UpdatedAt: 2026-10-03 06:12:44.218 +0000 UTC
  DownloadedAt: 2026-10-03 07:01:12.554 +0000 UTC

shop-api:nonroot (debian 13.1)
==============================
Total: 2 (HIGH: 2, CRITICAL: 0)

┌────────────┬────────────────┬──────────┬────────┬───────────────────┬─────────────────┬────────────────────────┐
│ Library    │ Vulnerability  │ Severity │ Status │ Installed Version │ Fixed Version   │ Title                  │
├────────────┼────────────────┼──────────┼────────┼───────────────────┼─────────────────┼────────────────────────┤
│ libexpat1  │ CVE-YYYY-NNNNN │ HIGH     │ fixed  │ 2.7.1-2           │ 2.7.1-2+deb13u1 │ expat: example issue   │
│ libssl3t64 │ CVE-YYYY-MMMMM │ HIGH     │ fixed  │ 3.5.1-1           │ 3.5.1-1+deb13u1 │ openssl: example issue │
└────────────┴────────────────┴──────────┴────────┴───────────────────┴─────────────────┴────────────────────────┘

Dockerfile.root (dockerfile)
============================
Tests: 27 (SUCCESSES: 26, FAILURES: 1)
Failures: 1 (HIGH: 1, CRITICAL: 0)

DS-0002 (HIGH): Specify at least 1 USER command in Dockerfile with non-root user as argument
```

→ `python:3.12-slim` has been based on Debian 13 (trixie) since 2025, hence the `deb13u` package
revisions (check with `docker run --rm IMAGE cat /etc/debian_version`); pin `-slim-bookworm` if you
still need Debian 12. Trivy releases differ in how they print the config check ID
(`AVD-DS-0002`, `DS002` or `DS-0002`); match on the number when you search or write ignores, and
check `trivy config --format json` for the exact `ID` your version uses. Both image findings are `fixed`: rebuild with
`docker build --pull` and they should disappear.
The config scan catches the missing `USER` before an image even exists, which is why it belongs in
the merge-request pipeline.

**Hands-on lab (test VM only)**

**Step 1 — Build a two-level gate.** Fail only on what you can act on, report the rest:

```bash
# gate: fixable CRITICAL fails the job
trivy image --exit-code 1 --severity CRITICAL --ignore-unfixed --ignorefile .trivyignore.yaml IMAGE
# report: everything HIGH and above, kept as a job artifact for triage
trivy image --exit-code 0 --severity HIGH,CRITICAL --format json --output trivy-report.json IMAGE
```

**Step 2 — Break it the way CI breaks.** Block the scan host's outbound access to the DB registry
(on the lab, a temporary UFW `deny out 443` on sec-scan with your SSH session already open) and scan:

```
FATAL	Fatal error	init error: DB error: failed to download vulnerability DB: ...
```

→ The pipeline is now red for a reason unrelated to the code. Remove the UFW rule. The fixes: cache
the DB between jobs (`--cache-dir .trivycache/` plus a GitLab `cache:` entry), scan once with the
download and then with `--skip-db-update` for further images in the same job, and on networks
without internet access pull the DB through a Harbor proxy-cache project with `--db-repository`.

**Step 3 — Record an exception properly.** Never raise the threshold to get a green build. Accept
one specific finding, with a reason and an expiry date, in `.trivyignore.yaml`:

```yaml
vulnerabilities:
  - id: CVE-YYYY-NNNNN
    statement: "Not reachable: the XML parser is only used by a CLI tool the service never runs. Ticket SEC-142."
    expired_at: 2026-12-31
```

→ After the expiry date the finding fails the gate again and forces a re-decision. The plain
`.trivyignore` format supports the same idea with a line such as `CVE-YYYY-NNNNN exp:2026-12-31`
and a comment above it.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| DB download fails | `failed to download vulnerability DB` | `trivy --version` (DB age), runner egress | this topic |
| x509 when scanning a Harbor image | `x509: certificate signed by unknown authority` | the job image's trust store | section 4 |
| Gate fails on a CVE with no fix | release blocked, nothing to upgrade | `--ignore-unfixed`, an expiring exception | section 11 |
| CI and Harbor disagree | different counts for the same digest | compare DB `UpdatedAt` in both | next topic |
| Registry rate limit on the DB | `TOOMANYREQUESTS` | mirror the DB through Harbor | this topic |

**Why it matters for troubleshooting.** A security gate that fails a hotfix at 2 a.m. is an
operational incident. Knowing whether the failure is the code, the DB or the network decides
whether you fix, wait or record an exception.

**Next step:** let the registry enforce the same rules for every consumer.

### Harbor scanning and policies

**Level:** [L3 · Senior]

**Concept.** A CI gate only protects images that went through CI. **Harbor** sees every image
pushed and every pull, so it is where you enforce policy for all consumers: the Dokploy host, the
Kubernetes nodes and anyone's laptop. Per project you can:

- **scan on push** with the built-in Trivy scanner, and schedule a daily **scan all**, because new CVEs appear in old images;
- **prevent vulnerable images from running**: block pulls of artifacts with findings at or above a chosen severity;
- keep a **CVE allowlist** (system-wide or per project) with an expiry date for accepted findings;
- **prevent unsigned images from running** with Cosign (section 8);
- keep **tag immutability** rules and **robot accounts** limited to one project;
- generate and store **SBOMs** (Harbor 2.11 and later).

```
 GitLab CI ──push──► Harbor project "shop"
                      ├─ scan on push (Trivy) ───────────► report per digest
                      ├─ block pull if severity ≥ High ──► unless allowlisted (with expiry)
                      ├─ block pull if no Cosign signature
                      └─ immutable v* tags, robot accounts per project
 Dokploy host / kubelet ──pull──► allowed only if the digest passes every rule
```

**Key terms**

| Term | Meaning |
|---|---|
| Interrogation Services | Harbor admin page for scanners, scan schedules and SBOM settings |
| Prevent vulnerable images | project policy that blocks pulls above a severity threshold |
| CVE allowlist | IDs exempt from the policy, with an optional expiry date |
| Scan overview | per-artifact summary Harbor returns through its API |
| Accessory | an artifact attached to an image, such as a Cosign signature or an SBOM |

**See it on a real system**

```bash
curl -s -u "$HARBOR_USER:$HARBOR_PASSWORD" "https://harbor.example.com/api/v2.0/projects/shop" | jq '.metadata'
curl -s -u "$HARBOR_USER:$HARBOR_PASSWORD" \
  "https://harbor.example.com/api/v2.0/projects/shop/repositories/api/artifacts/1.8.0?with_scan_overview=true" \
  | jq '.scan_overview[] | {scan_status, severity, by_severity: .summary.summary, fixable: .summary.fixable, end_time}'
```

```json
{
  "auto_scan": "true",
  "enable_content_trust_cosign": "true",
  "prevent_vul": "true",
  "public": "false",
  "reuse_sys_cve_allowlist": "true",
  "severity": "high"
}
{
  "scan_status": "Success",
  "severity": "High",
  "by_severity": {
    "High": 3,
    "Medium": 11,
    "Low": 24
  },
  "fixable": 9,
  "end_time": "2026-10-03T06:40:12.000Z"
}
```

→ This project scans on push, blocks High and above, and requires a Cosign signature, so
`shop/api:1.8.0` (three High findings) cannot be pulled until it is rebuilt or the findings are
allowlisted. (Use a robot account or a netrc file in scripts; `-u` on the command line shows in the
process list.)

**Hands-on lab (test VM only, on sec-reg with Harbor)**

**Step 1 — Turn the policies on.** In a lab project: Configuration → enable *Automatically scan
images on push* and *Prevent vulnerable images from running* at *High*. Push an old image you know
has findings (any base image a year or two old), wait for the scan, and pull it on sec-target:

```
Error response from daemon: unknown: current image with "47 vulnerabilities" cannot be pulled due to
configured policy in 'Prevent images with vulnerability severity of "High" or higher from running.'
To continue with pull, please contact your project administrator to exempt matched vulnerabilities
through configuring the CVE allowlist.
```

→ The exact wording varies between Harbor versions; the shape does not. This is the error a Dokploy
deployment or a pod's `ImagePullBackOff` event will show.

**Step 2 — Break it operationally.** Stop the scanner (on the lab, `docker stop trivy-adapter` in
the Harbor install directory's compose project) and push a fresh image. Its scan never completes,
and with the policy on, an image **without** a finished scan is refused too. A broken scanner can
therefore block every deployment, so treat the scanner as production infrastructure.

**Step 3 — Fix and harden.** Start the scanner again and rescan. Monitor scanner health (Harbor
exposes Prometheus metrics, and Interrogation Services shows the scanner state). For hosts without
internet access, set the `trivy:` options `offline_scan` and `skip_update` in `harbor.yml` and update
the DB yourself on a schedule. Finally, if one finding has to be accepted, add it to the project's
CVE allowlist **with an expiry date**, and record why.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Pull blocked by severity policy | `cannot be pulled due to configured policy` | scan overview API call above | this topic, then rebuild |
| Scanner down or DB stale | scans `Error` or pending; new images blocked | Interrogation Services page, `docker ps` on the Harbor host | this topic |
| Pull blocked: unsigned image | Cosign policy message | `cosign verify` (section 8) | section 8 |
| Allowlist expired | a deploy that worked yesterday fails today | project CVE allowlist expiry | section 11 |
| Kubernetes shows only `ImagePullBackOff` | real reason hidden | `kubectl describe pod POD` (events carry Harbor's message) | [Containers & K8s playbook](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting.** Registry policy turns a security decision into a deployment
failure. When a pull fails with a 412 or a policy message, it is Harbor working, and the fix is in the
image or the allowlist, never in disabling the policy for "just this deploy".

**Next step:** the same discipline inside Kubernetes.

---

## 7. Kubernetes security

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Security section: [TLS Basics](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics), then the RBAC, Service Accounts, Security Contexts and Network Policies lessons ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Learn Kubernetes](31-learn-kubernetes.md) sections 10 (Secrets), 14 (RBAC and ServiceAccounts) and 15 (NetworkPolicies), which this area assumes · 3) After the CKA: *Certified Kubernetes Security Specialist (CKS)* — Cluster Setup and Hardening, then Minimize Microservice Vulnerabilities, then Monitoring, Logging and Runtime Security ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · 4) Practice: every lab below on your kubeadm homelab or the [Kubernetes playground](https://kodekloud.com/playgrounds/playground-kubernetes-multi-cluster), then the free *CKS – Challenges* ([course](https://kodekloud.com/courses/cks-challenges)) · 5) Docs: [kubernetes.io/docs](https://kubernetes.io/docs/) — the security concepts and Pod Security Standards pages; the Kubernetes docs are allowed during the exam, so learn to find things in them now.

Kubernetes is secure enough by default to pass a demo and open enough to fail an audit. Out of
the box, any pod can talk to any other pod, a ServiceAccount token is mounted into every pod,
anyone who can create a pod in a namespace can read that namespace's secrets through it, secrets
sit unencrypted in etcd, and nothing records who did what. Each topic below closes one of those
gaps on your kubeadm homelab (cp1 192.168.56.10, workers w1 .11 and w2 .12, Calico, Traefik ingress).
Together they are most of the CKS syllabus.

### Cluster attack surface

**Level:** [L3 · Senior]

**Concept.** Think in four layers, the "4C" model: **Cloud** (or your datacenter and hosts),
**Cluster**, **Container**, **Code**. Each layer can only be as secure as the one under it. For the
cluster layer, the components and who should reach them:

| Port | Component | Who should reach it | kubeadm default |
|---|---|---|---|
| 6443 | kube-apiserver | admins (via VPN or bastion), nodes, CI | listens on the node IP, TLS, RBAC |
| 2379–2380 | etcd | the API servers and etcd peers only | client certificates required (mTLS) |
| 10250 | kubelet API | the API server (and metrics-server) | anonymous auth off, webhook authorization |
| 10257, 10259 | controller-manager, scheduler | localhost | bound to 127.0.0.1 |
| 30000–32767 | NodePort services | whatever you deliberately expose | open on every node |

kubeadm's defaults are sound, so on a homelab the real risks sit elsewhere: who holds an admin
kubeconfig, who can create pods (section 5 explained why that equals reading secrets), NodePorts
that expose internal services, and an outdated version.

**Key terms**

| Term | Meaning |
|---|---|
| 4C model | Cloud, Cluster, Container, Code: security layers that depend on each other |
| Anonymous auth | requests with no credentials; the API server allows a few public endpoints like `/version` |
| Webhook authorization | the kubelet asks the API server whether a caller may use its API |
| NodePort | a service port opened on every node's IP |

**See it on a real system** (from sec-scan, read-only checks):

```bash
nmap -Pn -p 6443,2379,2380,10250,10257,10259 192.168.56.10
curl -sk https://192.168.56.10:10250/pods; echo
curl -sk https://192.168.56.10:6443/version | jq '{gitVersion, platform}'
kubectl get svc -A --field-selector spec.type=NodePort
```

```
PORT      STATE  SERVICE
2379/tcp  open   unknown
2380/tcp  open   unknown
6443/tcp  open   sun-sr-https
10250/tcp open   unknown
10257/tcp closed unknown
10259/tcp closed unknown
Unauthorized
{
  "gitVersion": "v1.34.1",
  "platform": "linux/amd64"
}
NAMESPACE   NAME           TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)          AGE
tools       grafana        NodePort   10.96.141.27    <none>        3000:31300/TCP   41d
```

→ The kubelet refuses anonymous callers (`Unauthorized`), and the controller-manager and scheduler
are not reachable at all. etcd answers on the network, but only to clients holding certificates
signed by the etcd CA; a host firewall rule limiting 2379–2380 to the control plane is still worth
adding as a second layer. `/version` is public by design, which is one more reason to patch on time.
The finding is Grafana on NodePort 31300: an admin UI reachable on every node's IP.

**Hands-on lab (homelab only)**

**Step 1 — Firewall the control plane.** With the dead-man switch from section 3 armed, allow
6443 from your admin network and the nodes, 2379–2380 only from control-plane nodes, 10250 from
the control plane, and the Calico ports between nodes (see the port table in
[Learn Kubernetes](31-learn-kubernetes.md) section 3). Then change the Grafana service to
`ClusterIP` and publish it through the Traefik ingress with authentication instead.

**Step 2 — Break it.** On w1, deny 10250 from cp1, inserted above any allow rule
(`sudo ufw insert 1 deny from 192.168.56.10 to any port 10250 proto tcp`). Then, from your workstation:

```
$ kubectl -n shop logs deploy/api
Error from server: Get "https://192.168.56.11:10250/containerLogs/shop/api-6d9f7c8b5-x2k8p/api": dial tcp 192.168.56.11:10250: i/o timeout
```

→ `kubectl logs`, `exec` and `port-forward` travel workstation → API server → **kubelet on the
node**. A firewall that is right for the internet can still break the control plane's own path.

**Step 3 — Fix it.** Delete the deny rule (`sudo ufw status numbered`, then `sudo ufw delete N`),
keep 10250 open from the control plane only, and re-test `kubectl logs`.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| kubelet port blocked from the control plane | `logs`/`exec` time out, pods still run | `nc -vz 192.168.56.11 10250` from cp1 | [Containers & K8s playbook](26-playbook-containers-k8s.md) |
| Admin UI on a NodePort | reachable on every node IP | `kubectl get svc -A --field-selector spec.type=NodePort` | this topic |
| etcd reachable from everywhere | open in nmap from the office network | `sudo ss -ltnp | grep 2379` on cp1 | section 3 |
| Old cluster version | known CVEs, version visible on `/version` | `kubectl version` | section 11 |

**Why it matters for troubleshooting.** Knowing which component talks to which on which port is
how you tell "the firewall change broke the cluster" from "the cluster is broken" within a minute.

**Next step:** decide who may do what through the API.

### RBAC least privilege

**Level:** [L3 · Senior]

**Concept.** [Learn Kubernetes](31-learn-kubernetes.md) section 14 covers Roles, ClusterRoles and
bindings. Security adds two habits: grant per namespace with the exact verbs a job needs, and
recognise the permissions that are **escalation paths** even though they look harmless:

| Permission | Why it is dangerous |
|---|---|
| `*` on `*`, or the `cluster-admin` ClusterRole | everything, everywhere |
| `get`, `list` or `watch` on `secrets` | reads every credential in scope; `list` returns the values, not just names |
| `create` on `pods`, deployments, jobs or cronjobs | can start a pod that mounts any secret in the namespace and, without Pod Security Admission, a privileged pod |
| `create` on `pods/exec` | a shell in any pod in scope, with that pod's identity and secrets |
| `escalate` or `bind` on roles | can grant permissions they do not hold |
| `impersonate` | can act as another user, group or ServiceAccount |
| `create` on `serviceaccounts/token` | can mint tokens for other identities |
| `get` or `create` on `nodes/proxy` | direct access to the kubelet API |
| `patch` on `namespaces` | can relabel a namespace and switch off Pod Security Admission |

Two kubeadm facts matter. Since v1.29, `admin.conf` belongs to the group `kubeadm:cluster-admins`,
bound through a normal ClusterRoleBinding you can audit, while `super-admin.conf` carries the
`system:masters` group, which **bypasses RBAC entirely**. Kubernetes cannot revoke client
certificates: a leaked `system:masters` certificate stays valid until it expires or you rotate the
cluster CA. Keep `super-admin.conf` offline as break-glass and give people their own identities.

**Key terms**

| Term | Meaning |
|---|---|
| Role / ClusterRole | a set of rules: API groups, resources, verbs |
| RoleBinding / ClusterRoleBinding | who gets a role: users, groups, ServiceAccounts |
| `system:masters` | group hard-wired to full access; RBAC cannot restrict it |
| `kubectl auth can-i` | asks the API server whether an identity may do something |
| Aggregated ClusterRoles | `admin`, `edit`, `view`; note that `edit` includes reading secrets |

**See it on a real system**

```bash
kubectl auth can-i --list -n shop --as=system:serviceaccount:shop:gitlab-deployer
kubectl get clusterrolebindings -o json \
  | jq -r '.items[] | select(.roleRef.name=="cluster-admin") | "\(.metadata.name): \([.subjects[]? | "\(.kind):\(.name)"] | join(", "))"'
```

```
Resources                                       Non-Resource URLs   Resource Names   Verbs
deployments.apps                                []                  []               [get list watch patch update]
pods                                            []                  []               [get list watch]
replicasets.apps                                []                  []               [get list watch]
selfsubjectreviews.authentication.k8s.io        []                  []               [create]
selfsubjectaccessreviews.authorization.k8s.io   []                  []               [create]
selfsubjectrulesreviews.authorization.k8s.io    []                  []               [create]
                                                [/api/*]            []               [get]
cluster-admin: Group:system:masters
kubeadm:cluster-admins: Group:kubeadm:cluster-admins
ci-temp-admin: ServiceAccount:default
```

→ The deployer can update Deployments and read pods in `shop`, nothing else. The finding is
`ci-temp-admin`: a "temporary" binding from an old debugging session that makes a namespace's
`default` ServiceAccount cluster-admin. Every pod in that namespace that mounts its token is
therefore cluster-admin.

**Hands-on lab (homelab only)**

**Step 1 — Build a deployer identity for GitLab CI.**

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: gitlab-deployer
  namespace: shop
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer
  namespace: shop
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "patch", "update"]
  - apiGroups: ["apps"]
    resources: ["replicasets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: gitlab-deployer
  namespace: shop
subjects:
  - kind: ServiceAccount
    name: gitlab-deployer
    namespace: shop
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: deployer
```

Apply it, then test as that identity:
`kubectl -n shop set image deployment/api api=harbor.example.com/shop/api:1.8.1 --as=system:serviceaccount:shop:gitlab-deployer`.

**Step 2 — Break it.** Change the first rule's `apiGroups` to `[""]` (a very common mistake:
Deployments live in the `apps` group) and repeat the command:

```
Error from server (Forbidden): deployments.apps "api" is forbidden: User "system:serviceaccount:shop:gitlab-deployer" cannot get resource "deployments" in API group "apps" in the namespace "shop"
```

→ Read Forbidden messages left to right: **who** (the user), **verb** (`get`: `kubectl set image`
reads the object before it patches it, so the first missing verb is reported), **resource**,
**API group** (`apps`), **namespace**. Every one of them must match a rule.

**Step 3 — Fix it, then clean up.** Restore `["apps"]`. Then deal with `ci-temp-admin`: check the
audit log (topic below) for anything using that ServiceAccount, and delete the binding
(`kubectl delete clusterrolebinding ci-temp-admin`). Give CI short-lived tokens for this identity
(next topic) instead of a static kubeconfig.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Missing verb, resource or API group | `Forbidden` naming exactly what was refused | `kubectl auth can-i VERB RESOURCE -n NS --as=...` | this topic |
| RoleBinding in a different namespace than the Role | binding exists, nothing granted | `kubectl -n NS describe rolebinding NAME` | this topic |
| Over-broad grant | `can-i --list` shows `*` or secrets | the jq audit above | this topic |
| Leaked `system:masters` credential | cannot be revoked through RBAC | rotate the cluster CA, investigate | section 13 |

**Why it matters for troubleshooting.** A `Forbidden` message contains its own diagnosis. Reading
it precisely, instead of granting `cluster-admin` "for now", is the difference between a fix and a
new vulnerability.

**Next step:** the credentials every pod receives by default.

### ServiceAccount tokens

**Level:** [L3 · Senior]

**Concept.** Every pod runs as a ServiceAccount, `default` unless you say otherwise, and by default
gets a token for it mounted at `/var/run/secrets/kubernetes.io/serviceaccount/token`. Since v1.22
these are **bound tokens**: requested through the TokenRequest API, valid for one audience, tied to
the pod (deleting the pod invalidates the token) and refreshed by the kubelet. Since v1.24 old-style
token Secrets are no longer created automatically, and unused ones are labelled and then removed by the
legacy token clean-up (GA in v1.30).

Two details. The kubelet requests tokens of about one hour, but with the API server's default
`--service-account-extend-token-expiration` the token is issued for a year, with a `warnafter`
claim one hour out, so that old client libraries keep working while use of stale tokens is logged.
And most application pods never call the Kubernetes API at all, so for them the right setting is
`automountServiceAccountToken: false`.

**Key terms**

| Term | Meaning |
|---|---|
| Bound token | audience-, time- and pod-bound JWT from the TokenRequest API |
| Projected volume | how the kubelet mounts and refreshes the token in the pod |
| `automountServiceAccountToken` | ServiceAccount or pod field; `false` means no token in the pod |
| `kubectl create token` | issues a short-lived token for a ServiceAccount, for CI or testing |
| Legacy token Secret | type `kubernetes.io/service-account-token`; long-lived, avoid |

**See it on a real system**

```bash
kubectl -n shop exec deploy/api -- cat /var/run/secrets/kubernetes.io/serviceaccount/token \
  | jq -R 'split(".")[1] | gsub("-";"+") | gsub("_";"/") | @base64d | fromjson'
kubectl -n shop get sa default -o jsonpath='automount={.automountServiceAccountToken}{"\n"}'
kubectl get secrets -A --field-selector type=kubernetes.io/service-account-token
```

```json
{
  "aud": [
    "https://kubernetes.default.svc.cluster.local"
  ],
  "exp": 1822554000,
  "iat": 1791018000,
  "iss": "https://kubernetes.default.svc.cluster.local",
  "jti": "5b0e3c1a-8f2d-4c7e-9a61-2d4f8b7c9e10",
  "kubernetes.io": {
    "namespace": "shop",
    "node": {
      "name": "w1",
      "uid": "8d2f5a7c-1b3e-4f60-9c8a-7e6d5c4b3a21"
    },
    "pod": {
      "name": "api-6d9f7c8b5-x2k8p",
      "uid": "c41e9f20-6a7b-4d3c-8e2f-1a0b9c8d7e6f"
    },
    "serviceaccount": {
      "name": "default",
      "uid": "0f9e8d7c-6b5a-4c3d-2e1f-0a9b8c7d6e5f"
    },
    "warnafter": 1791021607
  },
  "nbf": 1791018000,
  "sub": "system:serviceaccount:shop:default"
}
```

```
automount=
No resources found
```

→ The token names this exact pod and node. `exp` is a year away, `warnafter` one hour: the
extended-expiry compatibility mode described above. `automount=` is empty, meaning unset, which
defaults to true: the API pod carries a token it never uses. There are no legacy token Secrets.

**Hands-on lab (homelab only)**

**Step 1 — Stop mounting tokens where they are not needed.**

```bash
kubectl -n shop patch serviceaccount default -p '{"automountServiceAccountToken": false}'
kubectl -n shop rollout restart deployment api
kubectl -n shop exec deploy/api -- ls /var/run/secrets/kubernetes.io/serviceaccount
```

```
ls: cannot access '/var/run/secrets/kubernetes.io/serviceaccount': No such file or directory
command terminated with exit code 2
```

**Step 2 — Break it.** A reporting CronJob in `shop` that lists pods (a small Go program using
client-go's in-cluster configuration) also used `default`. Its next run fails:

```
open /var/run/secrets/kubernetes.io/serviceaccount/token: no such file or directory
```

The wording depends on the client: the Python client reports `Service token file does not exist`,
and `kubectl` itself, finding no token, falls back to `localhost:8080` and reports
`The connection to the server localhost:8080 was refused`.

**Step 3 — Fix it properly.** Give the job its own ServiceAccount (`pod-reader`), set
`automountServiceAccountToken: true` on that ServiceAccount or in the job's pod spec, and bind a
Role with only `get` and `list` on `pods`. For CI, issue short-lived tokens instead of storing a
kubeconfig with a permanent one:

```bash
kubectl -n shop create token gitlab-deployer --duration=15m
```

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Token not mounted where needed | `token: no such file or directory` | `kubectl get pod POD -o jsonpath='{.spec.automountServiceAccountToken}'` | this topic |
| Copied pod token stops working | `401 Unauthorized` after the pod was deleted | check the token's `pod` claim | this topic |
| Legacy token Secret still in use | long-lived credential in a CI variable | `kubectl get secrets -A --field-selector type=kubernetes.io/service-account-token` | section 5 |
| Token works but the call is refused | `403 Forbidden` | `kubectl auth can-i ... --as=system:serviceaccount:NS:SA` | previous topic |

**Why it matters for troubleshooting.** "401 Unauthorized" means the token is invalid (expired,
wrong audience, deleted pod); "403 Forbidden" means it is valid but RBAC said no. The fix lives in
completely different places.

**Next step:** control what pods themselves may do.

### Pod Security Admission

**Level:** [L3 · Senior]

**Concept.** Pod Security Admission (PSA, GA since v1.25) is the built-in admission controller
that checks every pod against the **Pod Security Standards**. You switch it on per namespace with
labels. There are three levels and three modes:

| Level | Allows | Use for |
|---|---|---|
| `privileged` | anything | CNI, storage and node agents in their own namespaces |
| `baseline` | blocks the known escalations: privileged, host namespaces, hostPath, host ports, added dangerous capabilities | system add-ons that need a little more |
| `restricted` | baseline plus: non-root, `allowPrivilegeEscalation: false`, all capabilities dropped (only `NET_BIND_SERVICE` may be added), seccomp `RuntimeDefault` or `Localhost`, limited volume types | every application namespace |

| Mode | Effect |
|---|---|
| `enforce` | violating pods are rejected |
| `audit` | allowed, but recorded in the API server audit log |
| `warn` | allowed, and the client sees a warning |

Enforcement applies to **pods**. A Deployment that violates the policy is created happily; its
ReplicaSet then fails to create pods, which is the most confusing symptom PSA produces.

**Key terms**

| Term | Meaning |
|---|---|
| `pod-security.kubernetes.io/enforce` | namespace label choosing the enforced level |
| `...-version` labels | pin the standard's version (`v1.34`) or follow `latest` |
| `securityContext` | pod- and container-level settings PSA checks |
| Exemptions | users, namespaces or runtime classes excluded in the admission configuration |

A pod spec that passes `restricted` (the image runs as uid 10001, section 6):

```yaml
spec:
  automountServiceAccountToken: false
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    runAsGroup: 10001
    fsGroup: 10001
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: api
      image: harbor.example.com/shop/api:1.8.1
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
      volumeMounts:
        - name: tmp
          mountPath: /tmp
  volumes:
    - name: tmp
      emptyDir:
        sizeLimit: 64Mi
```

→ `readOnlyRootFilesystem` is not required by `restricted`, but it is the Kubernetes form of
section 6's read-only rootfs and costs one `emptyDir`.

**See it on a real system**

```bash
kubectl get ns -L pod-security.kubernetes.io/enforce,pod-security.kubernetes.io/warn
kubectl label --dry-run=server --overwrite ns shop pod-security.kubernetes.io/enforce=restricted
```

```
NAME              STATUS   AGE   ENFORCE      WARN
calico-system     Active   92d   privileged
default           Active   92d
kube-system       Active   92d
shop              Active   40d                restricted
traefik           Active   60d   baseline
Warning: existing pods in namespace "shop" violate the new PodSecurity enforce level "restricted:latest"
Warning: legacy-report-7c9d5b8f4-q2w7e: allowPrivilegeEscalation != false, unrestricted capabilities, runAsNonRoot != true, seccompProfile
namespace/shop labeled (server dry run)
```

→ `shop` only warns today. The server-side dry run lists exactly which running pods would fail
under `enforce=restricted`, without changing anything: always run it before switching enforcement on.

**Hands-on lab (homelab only)**

**Step 1 — Build.** Fix the API Deployment to the spec above, then label the namespace:

```bash
kubectl label --overwrite ns shop \
  pod-security.kubernetes.io/enforce=restricted pod-security.kubernetes.io/enforce-version=v1.34 \
  pod-security.kubernetes.io/warn=restricted pod-security.kubernetes.io/audit=restricted
```

**Step 2 — Break it.** Deploy the old `legacy-report` image (runs as root, no securityContext):

```bash
kubectl -n shop get deploy legacy-report
kubectl -n shop get events --field-selector reason=FailedCreate | tail -n 1
```

```
NAME            READY   UP-TO-DATE   AVAILABLE   AGE
legacy-report   0/1     0            0           2m
LAST SEEN   TYPE      REASON         OBJECT                              MESSAGE
5s          Warning   FailedCreate   replicaset/legacy-report-7c9d5b8f4  Error creating: pods "legacy-report-7c9d5b8f4-k8x2v" is forbidden: violates PodSecurity "restricted:v1.34": allowPrivilegeEscalation != false (container "report" must set securityContext.allowPrivilegeEscalation=false), unrestricted capabilities (container "report" must set securityContext.capabilities.drop=["ALL"]), runAsNonRoot != true (pod or container "report" must set securityContext.runAsNonRoot=true), seccompProfile (pod or container "report" must set securityContext.seccompProfile.type to "RuntimeDefault" or "Localhost")
```

→ No pods, no pod events: the refusal is recorded on the **ReplicaSet**. The message lists every
field to set.

**Step 3 — Fix it the right way.** Add the securityContext. If the image genuinely needs root,
rebuild it as non-root (section 6) instead of weakening the namespace. Workloads that really need
host access (CNI, CSI, node exporters) go into their own namespaces labelled `privileged` or
`baseline`, with an owner and a reason.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Deployment shows 0 pods, no pod events | `FailedCreate` on the ReplicaSet | `kubectl -n NS get events --field-selector reason=FailedCreate` | this topic |
| Image user is a name | `CreateContainerConfigError`: `image has non-numeric user (app), cannot verify user is non-root` | `kubectl describe pod POD` | section 6 |
| Root-only image under restricted | `container has runAsNonRoot and image will run as root` | rebuild with a numeric `USER` | section 6 |
| Upgrade changed the policy | new warnings after a cluster upgrade with `latest` | pin `enforce-version` | this topic |
| Someone relabelled the namespace | enforcement silently off | audit log: `patch` on `namespaces` | audit topic below |

**Why it matters for troubleshooting.** "The Deployment exists but has no pods" sends people to
the scheduler and the nodes; with PSA in place, the ReplicaSet's events are the first place to look.

**Next step:** limit what pods can reach on the network.

### NetworkPolicy default deny

**Level:** [L3 · Senior]

**Concept.** Without NetworkPolicies, every pod can open connections to every other pod in every
namespace: one compromised pod can probe the whole cluster. The secure pattern is **default deny
per namespace, then explicit allows**. Policies are additive allow-lists; there is no "deny" rule.
Three facts from [Learn Kubernetes](31-learn-kubernetes.md) section 15 matter most here: the CNI
must enforce them (Calico does; plain Flannel silently ignores them), egress default-deny also
blocks **DNS** until you allow it, and traffic between a node and its own pods (kubelet probes) is
always allowed.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: shop
spec:
  podSelector: {}
  policyTypes: ["Ingress", "Egress"]
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: shop
spec:
  podSelector: {}
  policyTypes: ["Egress"]
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-from-traefik
  namespace: shop
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes: ["Ingress"]
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: traefik
      ports:
        - protocol: TCP
          port: 8000
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-to-postgres
  namespace: shop
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes: ["Egress"]
  egress:
    - to:
        - ipBlock:
            cidr: 192.168.56.50/32
      ports:
        - protocol: TCP
          port: 5432
```

→ `kubernetes.io/metadata.name` is a label Kubernetes puts on every namespace automatically, so
the selectors work without you labelling anything. The database is a VM outside the cluster, hence
`ipBlock`.

**Key terms**

| Term | Meaning |
|---|---|
| `podSelector: {}` | every pod in the namespace |
| `policyTypes` | which directions the policy restricts; listing `Egress` with no rules denies all egress |
| `namespaceSelector` + `podSelector` in one item | AND: those pods in those namespaces |
| `ipBlock` | CIDR-based rule, for destinations outside the cluster |

**See it on a real system**

```bash
kubectl get networkpolicy -A
kubectl -n shop run np-test --rm -it --restart=Never --image=busybox:1.36 -- wget -qO- -T 3 http://api:8000/healthz
```

```
NAMESPACE   NAME               POD-SELECTOR   AGE
shop        allow-dns-egress   <none>         2m
shop        api-from-traefik   app=api        2m
shop        api-to-postgres    app=api        2m
shop        default-deny-all   <none>         2m
wget: download timed out
pod "np-test" deleted
```

→ The test pod resolves `api` (DNS is allowed) but its connection times out: its own egress is
denied by `default-deny-all`, and it is not in the `traefik` namespace either. That is the policy
working. If `shop` already enforces `restricted` from the PSA topic, the plain `kubectl run` is
rejected by Pod Security Admission before any network test; do this lab before labelling the
namespace, or give the test pod a restricted `securityContext` through `--overrides`.

**Hands-on lab (homelab only)**

**Step 1 — Measure before.** Run the `np-test` command with no policies in `shop`: it prints `ok`.

**Step 2 — Break it.** Apply only `default-deny-all` and run the test again:

```
wget: bad address 'api:8000'
```

→ The first symptom of an egress default-deny is **DNS failure**, not a timeout. The pod cannot
reach CoreDNS, so the name never resolves.

**Step 3 — Fix it in order.** Apply `allow-dns-egress` (now the test times out instead: DNS works,
the API is still closed), then `api-from-traefik` and `api-to-postgres`. Check through the ingress
that the site works (`curl -sI https://shop.example.com/`), and that the API still reaches PostgreSQL.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| DNS egress not allowed | `bad address`, `i/o timeout` on port 53 | `kubectl -n NS get networkpolicy` | [Containers & K8s playbook](26-playbook-containers-k8s.md) |
| CNI does not enforce | policies exist, nothing is blocked | check the CNI (`kubectl get pods -n calico-system`) | [Learn Kubernetes](31-learn-kubernetes.md) |
| Ingress from Traefik blocked | 504 or 502 from the ingress | `kubectl get ns traefik --show-labels` | [Site down playbook](25-playbook-site-down.md) |
| External DB blocked | app logs `connection timed out` to 5432 | `ipBlock` CIDR and port | [Databases for DevOps](38-learn-databases-ops.md) |

**Why it matters for troubleshooting.** In a cluster with policies, "timed out" between pods is a
policy question before it is a network question. `kubectl get networkpolicy -n NS` takes two seconds.

**Next step:** protect the secrets where they are stored.

### Secrets encryption at rest

**Level:** [L3 · Senior]

**Concept.** Kubernetes Secrets are base64-encoded, and etcd stores them **unencrypted** unless the
API server is given an `EncryptionConfiguration`. Anyone with an etcd backup file, a copy of the
control plane's disk, or etcd client certificates can read every secret. Encryption at rest closes
that; it does **not** protect against identities that RBAC allows to `get` secrets, because the API
server decrypts for them.

| Provider | Key held | Notes from the Kubernetes docs |
|---|---|---|
| `identity` | none | no encryption (the default) |
| `aescbc` | on the control-plane host | rated weak; still what most CKS tasks use |
| `aesgcm` | on the host | needs key rotation every 200,000 writes |
| `secretbox` | on the host | strong; the better choice for a homelab with a local key |
| `kms` v2 | in an external KMS (Vault transit, a cloud KMS) | recommended for production; the key never sits on the node |

The **first** provider in the list encrypts new writes; the others are tried for reading. That
ordering is what makes key rotation possible.

**Key terms**

| Term | Meaning |
|---|---|
| `EncryptionConfiguration` | file passed to kube-apiserver with `--encryption-provider-config` |
| Static pod manifest | `/etc/kubernetes/manifests/kube-apiserver.yaml`; the kubelet restarts the API server when it changes |
| `k8s:enc:` prefix | marks an encrypted value in etcd |
| Re-encryption | rewriting every Secret so it is stored under the current key |

**See it on a real system** (on cp1):

```bash
kubectl -n shop create secret generic enc-test --from-literal=k=lab-only
kubectl -n kube-system exec etcd-cp1 -- etcdctl \
  --cacert /etc/kubernetes/pki/etcd/ca.crt --cert /etc/kubernetes/pki/etcd/server.crt \
  --key /etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/shop/enc-test | hexdump -C | head -n 4
```

```
00000000  2f 72 65 67 69 73 74 72  79 2f 73 65 63 72 65 74  |/registry/secret|
00000010  73 2f 73 68 6f 70 2f 65  6e 63 2d 74 65 73 74 0a  |s/shop/enc-test.|
00000020  6b 38 73 00 0a 0c 0a 02  76 31 12 06 53 65 63 72  |k8s.....v1..Secr|
00000030  65 74 12 a1 01 0a 8a 01  0a 08 65 6e 63 2d 74 65  |et........enc-te|
```

→ `k8s` followed by protobuf: the Secret, value included, is stored in clear.

**Hands-on lab (homelab only, snapshot cp1 first)**

**Step 1 — Build.** Create the key and the configuration:

```bash
sudo mkdir -p /etc/kubernetes/enc
KEY=$(head -c 32 /dev/urandom | base64)
sudo tee /etc/kubernetes/enc/enc.yaml >/dev/null <<EOF
apiVersion: apiserver.config.k8s.io/v1
kind: EncryptionConfiguration
resources:
  - resources:
      - secrets
    providers:
      - secretbox:
          keys:
            - name: key1
              secret: ${KEY}
      - identity: {}
EOF
sudo chmod 600 /etc/kubernetes/enc/enc.yaml
```

> Copy the manifest **outside** `/etc/kubernetes/manifests/` before editing it
> (`sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml /root/`). The kubelet runs every file in
> that directory, so a backup left there becomes a second, broken API server.

Then add to `/etc/kubernetes/manifests/kube-apiserver.yaml` the flag, the mount and the volume:

```yaml
    - --encryption-provider-config=/etc/kubernetes/enc/enc.yaml
```

```yaml
    volumeMounts:
    - mountPath: /etc/kubernetes/enc
      name: enc
      readOnly: true
```

```yaml
  volumes:
  - hostPath:
      path: /etc/kubernetes/enc
      type: DirectoryOrCreate
    name: enc
```

Wait for the API server to come back (`kubectl get --raw /readyz` prints `ok`), create a new secret
and rerun the `etcdctl` check:

```
00000020  6b 38 73 3a 65 6e 63 3a  73 65 63 72 65 74 62 6f  |k8s:enc:secretbo|
00000030  78 3a 76 31 3a 6b 65 79  31 3a 8f 3c 0a 9e 41 d2  |x:v1:key1:.<..A.|
```

Then rewrite every existing Secret so the old ones are encrypted too:

```bash
kubectl get secrets --all-namespaces -o json | kubectl replace -f -
```

**Step 2 — Break it.** Change the `hostPath` in the manifest to `/etc/kubernetes/encryption` (a
directory that does not contain the file). The API server never becomes ready:

```
The connection to the server 192.168.56.10:6443 was refused - did you specify the right host or port?
```

```bash
sudo crictl ps -a --name kube-apiserver
sudo crictl logs "$(sudo crictl ps -a --name kube-apiserver -q | head -n 1)" 2>&1 | tail -n 2
```

```
E1003 10:42:17.551203       1 run.go:72] "command failed" err="error while parsing file: error reading encryption provider configuration file \"/etc/kubernetes/enc/enc.yaml\": open /etc/kubernetes/enc/enc.yaml: no such file or directory"
```

**Step 3 — Fix it.** Correct the path; the kubelet notices the manifest change and recreates the
pod. Keep the key file backed up **separately** from etcd backups: an etcd backup without its key
cannot restore any secret, and a backup stored together with its key protects nothing.

To **rotate** later: add `key2` as the second key, restart the API servers; move `key2` first,
restart; re-encrypt all secrets with the `replace` command; remove `key1`, restart.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Wrong path or mount | API server down, `connection refused` on 6443 | `sudo crictl ps -a --name kube-apiserver`, then its logs | [Containers & K8s playbook](26-playbook-containers-k8s.md) |
| Key lost | restored cluster cannot read Secrets | backup procedure for the key | [Databases for DevOps](38-learn-databases-ops.md) (restore drills) |
| Old secrets still plain | only new secrets show `k8s:enc:` | rerun the `replace` command | this topic |
| HA control plane, files differ | random decryption errors | compare `enc.yaml` on every control-plane node | this topic |

**Why it matters for troubleshooting.** An API server that will not start after a manifest edit is
one of the most common self-inflicted outages on kubeadm clusters, and `crictl logs` on the
control-plane node is the only place its reason appears.

**Next step:** record who does what through the API.

### API server audit logs

**Level:** [L3 · Senior] to set up, [L4 · Lead/SRE] to use in investigations

**Concept.** Audit logging records every request to the API server: who, what, when, from where,
and whether it was allowed. kubeadm does not enable it. A **policy** decides how much is recorded
per request; the first matching rule wins:

| Level | Records |
|---|---|
| `None` | nothing |
| `Metadata` | user, verb, resource, timestamps, response code; no bodies |
| `Request` | metadata plus the request body |
| `RequestResponse` | metadata plus request and response bodies |

Never log Secrets, ConfigMaps or token requests above `Metadata`: the bodies contain the values,
and your audit log would become the easiest place to steal them.

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
  - "RequestReceived"
rules:
  - level: None
    nonResourceURLs: ["/healthz*", "/livez*", "/readyz*", "/version"]
  - level: None
    users: ["system:kube-proxy"]
    verbs: ["watch"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets", "configmaps", "serviceaccounts/token"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach", "pods/portforward"]
  - level: RequestResponse
    resources:
      - group: "rbac.authorization.k8s.io"
        resources: ["roles", "rolebindings", "clusterroles", "clusterrolebindings"]
  - level: Request
    verbs: ["create", "update", "patch", "delete", "deletecollection"]
  - level: Metadata
```

**Key terms**

| Term | Meaning |
|---|---|
| Audit policy | the rules above, passed with `--audit-policy-file` |
| Stage | `RequestReceived`, `ResponseStarted`, `ResponseComplete`, `Panic` |
| `auditID` | unique ID per request, to correlate events |
| `authorization.k8s.io/reason` | annotation naming the binding that allowed the request |

**See it on a real system.** Add these flags to the API server manifest, with `hostPath` volumes for
`/etc/kubernetes/audit` (read-only) and `/var/log/kubernetes/audit` exactly as in the encryption
topic:

```yaml
    - --audit-policy-file=/etc/kubernetes/audit/policy.yaml
    - --audit-log-path=/var/log/kubernetes/audit/audit.log
    - --audit-log-maxage=30
    - --audit-log-maxbackup=10
    - --audit-log-maxsize=100
```

Then ask the questions an investigation asks:

```bash
LOG=/var/log/kubernetes/audit/audit.log
# humans reading secrets
sudo jq -r 'select(.objectRef.resource=="secrets" and (.verb=="get" or .verb=="list") and (.user.username|startswith("system:")|not))
  | [.requestReceivedTimestamp, .user.username, .verb, .objectRef.namespace, (.objectRef.name // "*")] | @tsv' "$LOG"
# shells opened in pods
sudo jq -r 'select(.objectRef.subresource=="exec") | [.requestReceivedTimestamp, .user.username, .objectRef.namespace, .objectRef.name] | @tsv' "$LOG"
# RBAC changes
sudo jq -r 'select(.objectRef.apiGroup=="rbac.authorization.k8s.io" and (.verb|IN("create","update","patch","delete")))
  | [.requestReceivedTimestamp, .user.username, .verb, .objectRef.resource, .objectRef.name] | @tsv' "$LOG"
```

```
2026-10-03T02:14:07.112233Z	alice	get	shop	db
2026-10-03T02:19:44.901122Z	alice	shop	api-6d9f7c8b5-x2k8p
2026-10-03T02:21:10.004512Z	alice	create	clusterrolebindings	alice-temp-admin
```

→ At 02:14 a person read a production database secret, five minutes later opened a shell in the
API pod, then created a cluster-admin binding for themselves. Legitimate or not, that sequence is
exactly what section 12's alerts should page someone about. One event in full shows why the
`edit` role deserves care:

```json
{
  "kind": "Event",
  "apiVersion": "audit.k8s.io/v1",
  "level": "Metadata",
  "auditID": "4f6a2b1c-9d3e-4a5b-8c7d-1e2f3a4b5c6d",
  "stage": "ResponseComplete",
  "requestURI": "/api/v1/namespaces/shop/secrets/db",
  "verb": "get",
  "user": {
    "username": "alice",
    "groups": ["devs", "system:authenticated"]
  },
  "sourceIPs": ["192.168.56.1"],
  "userAgent": "kubectl/v1.34.1 (linux/amd64) kubernetes/abcdef0",
  "objectRef": {
    "resource": "secrets",
    "namespace": "shop",
    "name": "db",
    "apiVersion": "v1"
  },
  "responseStatus": {
    "metadata": {},
    "code": 200
  },
  "requestReceivedTimestamp": "2026-10-03T02:14:07.112233Z",
  "stageTimestamp": "2026-10-03T02:14:07.118410Z",
  "annotations": {
    "authorization.k8s.io/decision": "allow",
    "authorization.k8s.io/reason": "RBAC: allowed by RoleBinding \"devs-edit/shop\" of ClusterRole \"edit\" to Group \"devs\""
  }
}
```

→ The `reason` annotation names the binding that granted access: the built-in `edit` role, which
includes reading Secrets. Developers often get `edit` "so they can debug"; this event is what that
grant means.

**Hands-on lab (homelab only)**

**Step 1 — Build.** Save the policy as `/etc/kubernetes/audit/policy.yaml`, add the flags and
volumes, wait for `/readyz`, and run the three queries after some normal work.

**Step 2 — Break it.** Introduce a YAML mistake in the policy (for example `level: Metdata`). The
API server stops coming up; `crictl logs` shows the policy loading error. Fix the typo.

**Step 3 — Ship it off the node.** The audit log on cp1 is only as trustworthy as cp1. Collect
`/var/log/kubernetes/audit/*.log` with the same agent that ships your other logs (section 12), and
check the rotation settings against your retention needs (section 14).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Policy or mount error | API server will not start | `sudo crictl ps -a --name kube-apiserver`, logs | encryption topic above |
| Disk filling | `/var/log` grows fast on cp1 | `du -sh /var/log/kubernetes/audit` | [Storage & disk](01-storage-disk.md) |
| Secrets logged at `Request` | secret values in audit files | `grep -c '"secrets"' ...` and the policy order | this topic |
| No history for an incident | audit was never enabled | enable now; rely on other logs this time | section 13 |

**Why it matters for troubleshooting.** "Who deleted the Deployment?" and "what changed at 02:20?"
are answered in seconds with an audit log and become guesswork without one.

**Next step:** put these topics in exam order.

### CKS preparation

**Level:** [L3 · Senior], after the CKA

**Concept.** The Certified Kubernetes Security Specialist exam is a two-hour, hands-on exam in live
clusters. You need an active CKA to sit it, and the Kubernetes documentation is allowed during the
exam. The curriculum domains and their current weights (check the official curriculum before you
book; it is revised from time to time):

| CKS domain | Weight | Where it lives in this handbook |
|---|---|---|
| Cluster Setup | 15% | NetworkPolicies, CIS checks with kube-bench, ingress TLS, verifying binaries: this area, sections 2 and 4 |
| Cluster Hardening | 15% | RBAC, ServiceAccount tokens, API access, upgrades: this area, [Learn Kubernetes](31-learn-kubernetes.md) section 19 |
| System Hardening | 10% | host footprint, firewalls, AppArmor, seccomp: sections 2, 3 and 6 |
| Minimize Microservice Vulnerabilities | 20% | Pod Security Admission, securityContext, secrets, isolation with RuntimeClass, pod-to-pod encryption: this area, sections 4 and 6 |
| Supply Chain Security | 20% | base images, SBOMs, signing, scanning, static analysis of manifests: sections 6 and 8 |
| Monitoring, Logging and Runtime Security | 20% | audit logs, Falco, immutable containers: this area, sections 6 and 12 |

**Key terms**

| Term | Meaning |
|---|---|
| kube-bench | checks a node against the CIS Kubernetes Benchmark |
| Falco | runtime detection from syscalls (section 12) |
| RuntimeClass | selects a different runtime (for example gVisor) for sandboxed pods |
| `appArmorProfile` | pod and container field (GA since v1.30) that replaced the old annotations |

**See it on a real system.** Run the CIS benchmark checks against cp1 with kube-bench, using the
job manifest from the kube-bench project (it mounts host paths read-only), then read the summary:

```
== Summary master ==
41 checks PASS
9 checks FAIL
11 checks WARN
0 checks INFO
```

→ Each FAIL carries a remediation line. Several will be things this area already covered (audit
logging, encryption at rest); others, such as file permissions on manifests, are one-line fixes.

**Hands-on lab (homelab only).** A six-to-eight-week plan of morning slots, after the CKA:

| Week | Do | Handbook |
|---|---|---|
| 1 | KodeKloud CKS: cluster setup; kube-bench on cp1, fix three FAILs | this area, section 2 |
| 2 | RBAC, ServiceAccounts, API server flags; audit logging | this area |
| 3 | System hardening: AppArmor and seccomp profiles for pods, host firewalls | sections 2, 3, 6 |
| 4 | PSA, securityContext, secrets encryption, RuntimeClass | this area |
| 5 | Supply chain: Trivy, SBOMs, signing, static analysis of manifests | sections 6, 8 |
| 6 | Falco rules, audit log investigations, immutable pods | section 12, this area |
| 7–8 | *CKS – Challenges*, then the two exam simulator sessions that come with registration | all |

**How it breaks (in the exam)**

| Failure | Symptom | First command | Fix |
|---|---|---|---|
| API server does not return after a manifest edit | `connection refused` for minutes | `sudo crictl ps -a`, `crictl logs` | keep a copy outside the manifests directory; fix the YAML |
| Task done in the wrong cluster | checker finds nothing | `kubectl config current-context` | run the context command each task gives you, every time |
| Falco change has no effect | no new alerts | `journalctl -u falco` (or the Falco pod log) | edit the local rules file, restart Falco |
| AppArmor profile not found | pod `Blocked` or `CreateContainerError` | `sudo aa-status` on the node | load the profile on the node that runs the pod |

**Why it matters for troubleshooting.** The CKS teaches you to change control-plane configuration
under time pressure without losing the cluster, which is the same skill an incident needs.

**Next step:** security of everything that comes before deployment, the supply chain.

---

## 8. Supply chain security

> 📚 **Study path:** 1) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Optimization, Security and Monitoring (SAST, container scanning), plus the [Docker Push](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Continuous-Integration-with-GitLab/Docker-Push/page) lesson ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · 2) Note: [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 2 (building images, pushing to Harbor with the commit SHA) and the Trivy and Cosign topic in [Learn Docker](30-learn-docker.md) section 11 · 3) After the CKA: *Certified Kubernetes Security Specialist (CKS)* — Supply Chain Security ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · 4) Reading: [OWASP](https://owasp.org/) — its Top 10 and its CI/CD security risks project give you the vocabulary for SAST, DAST and dependency risks · 5) Practice: the pipeline lab at the end of this area on a throwaway GitLab project, or the [CI/CD playground](https://kodekloud.com/playgrounds/playground-ci-cd).

Your software supply chain is everything between a developer's keyboard and the container that
runs in production: source, dependencies, the build, the image, the registry and the deployment.
Attackers increasingly target the chain rather than the running service, because one compromised
dependency or CI token reaches every customer at once. The goal of this area is a pipeline where
you can prove, for any running container, **what is inside it, who built it, and that it has not
changed since**.

### Supply chain threats

**Level:** [L3 · Senior]

**Concept.** Walk the chain stage by stage and ask what could change the result without anyone
noticing:

| Stage | What goes wrong | Controls | Section |
|---|---|---|---|
| Source | secrets committed; unreviewed changes reach `main` | protected branches, merge-request approvals, secret scanning | 5, this area |
| Dependencies | a vulnerable or malicious package; typosquatting; dependency confusion | lockfiles, dependency scanning, one private package proxy | this area |
| Build | stolen CI tokens; a shared runner reused across projects; a tampered build tool | protected variables, ephemeral runners, OIDC instead of static keys, pinned tool versions | 5, 10 |
| Artifact | old base image; secrets in layers; root user | Trivy, SBOMs, minimal non-root images | 6, this area |
| Registry | a tag overwritten with a different image | immutable tags, project robot accounts, signatures | 6, this area |
| Deploy | an unverified or wrong image deployed | deploy by digest, verify the signature, registry policy | this area |

Three well-known incidents show why each stage matters. In **SolarWinds** (2020) attackers
modified the build system, so customers received backdoored updates that were properly signed:
signing alone does not help if the build is compromised. In **Codecov** (2021) a modified
uploader script that thousands of pipelines downloaded at run time sent CI environment variables,
including credentials, to the attackers: pin and verify every tool your pipeline fetches. In
**xz-utils** (CVE-2024-3094, 2024) a maintainer identity built up over years shipped a backdoor in
release tarballs; it was caught just before it reached stable distribution releases, and teams with
SBOMs could answer "are we affected?" in minutes.

**Key terms**

| Term | Meaning |
|---|---|
| SBOM | software bill of materials: every component and version inside an artifact |
| Provenance | a signed statement of how and where an artifact was built |
| Attestation | a signed statement about an artifact (an SBOM, a scan result, provenance) |
| SLSA | "Supply-chain Levels for Software Artifacts", a framework of build-integrity levels |
| Dependency confusion | an installer picks a public package that has the same name as your internal one |

**See it on a real system.** Two read-only questions that map who can change what reaches
production (project 42 is `shop/api`):

```bash
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.example.com/api/v4/projects/42/protected_branches" \
  | jq '.[] | {name, push: [.push_access_levels[].access_level_description], merge: [.merge_access_levels[].access_level_description]}'
curl -s -u "$HARBOR_USER:$HARBOR_PASSWORD" "https://harbor.example.com/api/v2.0/projects/shop/members" \
  | jq -r '.[] | "\(.entity_name)\t\(.role_name)"'
```

```json
{
  "name": "main",
  "push": ["No one"],
  "merge": ["Maintainers"]
}
```

```
admin	projectAdmin
alice	developer
bob	maintainer
```

→ Nobody pushes straight to `main`; maintainers merge reviewed changes. In Harbor, `alice` as a
developer can push images into `shop` directly from a laptop, bypassing CI entirely. Unless tags are
immutable and deployments require a CI signature, that is a path to production that skips every
check.

**Hands-on lab (paper and read-only commands)**

**Step 1 — Draw your chain.** For one service, draw source → runner → Harbor → Dokploy or
Kubernetes. Next to each arrow write the credential used (GitLab token, Harbor robot, kubeconfig,
Dokploy API key), where it is stored and who can read it.

**Step 2 — Find the weakest link.** For each credential ask: if it leaked today, what could someone
change, and would anything notice? Typical answer for a Harbor robot with push rights: it can push
a different image under a mutable tag, and nothing notices until the next deploy.

**Step 3 — Pick the controls.** Map each weak link to a control in the table above and to a topic in
this area. The rest of this area builds them in order.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Image pushed outside CI | a digest in Harbor with no matching pipeline | Harbor audit log for pushes by people | section 12 |
| Leaked CI credential | unexpected pushes or deploys | rotate first, then investigate | section 5, section 13 |
| Unpinned tool in the pipeline | behaviour changes without a commit | grep `.gitlab-ci.yml` for `latest` and `curl ... | sh` | this area |
| Unknown contents in production | "are we affected?" takes days | SBOM search (next topic) | next topic |

**Why it matters for troubleshooting.** When behaviour changes "without a deploy", the cause is
often a moved tag or a tool fetched fresh in the pipeline. The chain map tells you where to look.

**Next step:** know exactly what is inside each image.

### SBOMs with syft

**Level:** [L3 · Senior]

**Concept.** An SBOM lists every package in an artifact with its version, type, licence and
location. Two formats dominate: **SPDX** (Linux Foundation, also an ISO standard) and
**CycloneDX** (OWASP). Generate the SBOM **from the image you ship**, not from the source tree: a
source scan misses the operating-system packages and whatever the Dockerfile installs. Store SBOMs
next to the image (as a CI artifact, as a cosign attestation, or in Harbor, which can generate them
from version 2.11). Regulation is moving the same way: US federal guidance has promoted SBOMs since
Executive Order 14028 (2021), and the EU Cyber Resilience Act requires manufacturers to draw one up
for products in its scope (check the current obligations for your market).

**Key terms**

| Term | Meaning |
|---|---|
| syft | Anchore's SBOM generator for images, directories and archives |
| `-o FORMAT=FILE` | write one output format to a file; repeat for several |
| `registry:` source | read the image straight from the registry, no Docker daemon needed |
| PURL | package URL, a standard identifier like `pkg:deb/debian/libssl3@...` |

**See it on a real system**

```bash
syft scan harbor.example.com/shop/api:1.8.1 -o table | head -n 6
syft scan harbor.example.com/shop/api:1.8.1 -o spdx-json=sbom.spdx.json -o cyclonedx-json=sbom.cdx.json
jq '.components | length' sbom.cdx.json
trivy sbom --severity HIGH,CRITICAL sbom.cdx.json | grep -E '^Total'
```

```
NAME                VERSION          TYPE
adduser             3.152            deb
apt                 3.0.3            deb
base-files          13.8+deb13u1     deb
bash                5.2.37-1.1+b2    deb
certifi             2025.8.3         python
187
Total: 2 (HIGH: 2, CRITICAL: 0)
```

→ 187 components. `trivy sbom` scans the SBOM itself, so a new CVE can be checked against last
month's releases without pulling a single image.

The question an SBOM exists for, "are we affected?", asked across every service at once:

```bash
for f in sboms/*.cdx.json; do
  jq -r --arg f "$f" '.components[] | select(.name=="liblzma5" or .name=="xz-utils") | "\($f)\t\(.name)\t\(.version)"' "$f"
done
```

```
sboms/api.cdx.json	liblzma5	5.8.1-1
sboms/report.cdx.json	liblzma5	5.6.1+really5.4.5-1
sboms/legacy-cron.cdx.json	liblzma5	5.6.1-1
```

→ Read the whole version string. `report` (Ubuntu 24.04) shows `5.6.1+really5.4.5`, which despite
the "5.6.1" is 5.4.5 and not affected. `legacy-cron` was built in March 2024 from a rolling Debian
base and carries 5.6.1: the one image to rebuild and investigate. Without SBOMs this answer means
pulling and inspecting every image you run.

**Hands-on lab (test VM only)**

**Step 1 — Build.** Generate SBOMs for three images in CI or by hand, store them in a `sboms/`
directory named by service and digest, and run the search above for a package of your choice.

**Step 2 — Break it.** Generate an SBOM from the source directory instead
(`syft scan dir:. -o cyclonedx-json=src.cdx.json`) and compare the component counts. The source
SBOM lists only the Python packages: the OS packages, where most image CVEs live, are missing.

**Step 3 — Fix the process.** SBOMs come from the pushed image digest, are produced by the same
pipeline that builds the image, and are attached to that digest (the cosign topic shows how), so
nobody has to guess which SBOM belongs to which release.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| SBOM from source, not image | OS packages missing | compare component counts | this topic |
| SBOM not linked to a digest | unclear which release it describes | `cosign verify-attestation` (next topic) | next topic |
| Version strings misread | false alarm or false all-clear | read the full version, check the vendor's tracker | section 11 |
| Registry auth for `registry:` source | `UNAUTHORIZED` | `docker login` or `cosign login` first | section 6 |

**Why it matters for troubleshooting.** On the day of the next xz-style announcement, the team with
SBOMs answers management in ten minutes and spends the rest of the day fixing; the team without
them spends the day finding out.

**Next step:** prove that an image came from your pipeline.

### Signing with cosign

**Level:** [L3 · Senior]

**Concept.** A cosign signature binds an **image digest** to a key you control. Harbor stores the
signature as an accessory of the image and can refuse to serve unsigned images (section 6); a
deployment step can verify before deploying. Sign **digests, never tags**, because a tag can move
after you signed. Two models:

| | Key-based | Keyless |
|---|---|---|
| What signs | a key pair you generate (or a key in a KMS) | a short-lived certificate tied to an OIDC identity (for example a GitLab job) |
| Public infrastructure | none required | public Sigstore services (Fulcio, Rekor) |
| What becomes public | an entry in the public transparency log by default (signature, payload hash, your public key) | the same, plus the identity in the certificate (for a CI job, its project path) |
| Fits | on-prem, private GitLab, air-gapped networks | public projects, organisations happy to publish build identities |

For a private GitLab and Harbor, key-based signing with the key in a KMS (or at least in a
protected CI file variable) is the usual choice. If signatures must not reach the public log, cosign
2.x signs with `--tlog-upload=false` and verifies with `--insecure-ignore-tlog=true`; newer cosign
releases changed how signing destinations are configured, so check `cosign sign --help` for the
version you pinned. Pin the **same cosign major version** in every job that signs or verifies:
cosign 3.x writes new signatures in the Sigstore bundle format as OCI 1.1 referrers by default, and
cosign 2.x does not find those (`Error: no signatures found` on a correctly signed image). Check that
your Harbor version shows such signatures as accessories before you rely on its Cosign policy.

**Key terms**

| Term | Meaning |
|---|---|
| `cosign.key` / `cosign.pub` | encrypted private key and public key from `cosign generate-key-pair` |
| `COSIGN_PASSWORD` | the password that decrypts `cosign.key`; a masked, protected CI variable |
| Transparency log (Rekor) | append-only public log of signing events |
| Attestation | a signed statement attached to a digest, such as an SBOM (`cosign attest`) |
| KMS key reference | `hashivault://NAME`, `awskms://...`: cosign signs without the key leaving the KMS |

**See it on a real system**

```bash
DIGEST=$(docker buildx imagetools inspect harbor.example.com/shop/api:1.8.1 | awk '/^Digest:/ {print $2}')
cosign verify --key cosign.pub "harbor.example.com/shop/api@${DIGEST}" | jq '.[0].critical'
```

```
Verification for harbor.example.com/shop/api@sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - Existence of the claims in the transparency log was verified offline
  - The signatures were verified against the specified public key
{
  "identity": {
    "docker-reference": "harbor.example.com/shop/api"
  },
  "image": {
    "docker-manifest-digest": "sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c"
  },
  "type": "cosign container image signature"
}
```

→ The signed payload names the repository and the exact digest. The three check lines go to
stderr, the JSON to stdout, so `cosign verify ... >/dev/null && echo verified` works in scripts.

**Hands-on lab (lab Harbor on sec-reg)**

**Step 1 — Sign and attest.**

```bash
cosign generate-key-pair                    # prompts for COSIGN_PASSWORD; keep cosign.key out of Git
cosign sign --yes --key cosign.key "harbor.example.com/lab/api@${DIGEST}"
cosign attest --yes --key cosign.key --type cyclonedx --predicate sbom.cdx.json "harbor.example.com/lab/api@${DIGEST}"
cosign verify-attestation --key cosign.pub --type cyclonedx "harbor.example.com/lab/api@${DIGEST}" \
  | jq -r '.payload' | base64 -d | jq '.predicate.components | length'
```

→ The last command prints `187`: the SBOM is now cryptographically tied to that digest. In Harbor's
UI the image shows a signature and an attestation as accessories.

**Step 2 — Break it.** In the lab project (tags not yet immutable), push a different build under
the same tag and verify the tag:

```
Error: no signatures found
```

→ The tag now points to a new, unsigned digest, so cosign finds no signature at all. A digest that
*is* signed, but with a different key than the one you verify with, fails differently:
`Error: no matching signatures`.

Then enable the project's Cosign policy (*Prevent unsigned images from running*) and pull the new
image on sec-target. Harbor refuses it with a message that the image is not signed (the wording
varies by version).

**Step 3 — Fix the process.** Signing happens only in CI, after the scan passes, on the digest the
pipeline pushed; the private key never sits on a laptop; tags are immutable. For Kubernetes, an
admission controller (Kyverno's `verifyImages` or the Sigstore policy controller) can verify
signatures at deploy time; for Dokploy, verify in the deploy job and let Harbor's policy be the
backstop.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Tag moved after signing | `no signatures found` | `docker buildx imagetools inspect IMAGE:TAG` (digest changed?) | this topic |
| Wrong public key | `no matching signatures` for a correct digest | check which key the pipeline used | this topic |
| cosign 2.x verifying a cosign 3.x signature | `no signatures found` although the image is signed | `cosign version` in the signing and the verifying job | this topic |
| Harbor blocks pulls | unsigned-image policy message in pull errors | `cosign verify` on the digest | section 6 |
| Signing cannot reach the public log | timeout talking to the transparency log | proxy and egress, or the private-log options above | this topic |
| Private CA not trusted by cosign | `x509: certificate signed by unknown authority` | system trust store in the job image | section 4 |

**Why it matters for troubleshooting.** A failed verification is a deployment blocker by design.
Your first question is always "did the digest change, or the key?", and the two commands above
answer it.

**Next step:** make every reference to an image immutable.

### Pinning by digest

**Level:** [L2 · Mid] to use, [L3 · Senior] to enforce

**Concept.** A tag is a movable label; a digest is the SHA-256 of the image manifest (or of the
multi-architecture index) and never changes. Pin by digest in two places: **base images** in
Dockerfiles, so a rebuild cannot silently pull a different base, and **deployments**, so every node
runs exactly what was tested and signed. Keep the tag next to the digest for humans:
`FROM python:3.12-slim@sha256:9c3f...`. Pin the **index** digest of a multi-architecture image so each
node still pulls its own platform. A bot (Renovate or Dependabot) can raise merge requests when a
pinned base gets a new digest, which turns base-image updates into reviewed, tested changes.

Docker Swarm already resolves the tag to a digest when a service is created or updated, so all
tasks of one deployment run the same image. Kubernetes does not: each node pulls whatever the tag
points to when it pulls, and `IfNotPresent` keeps whatever it pulled before. That is how two
replicas end up running different code under one tag.

**Key terms**

| Term | Meaning |
|---|---|
| Manifest digest | hash of one platform's image manifest |
| Index digest | hash of the multi-architecture list; pin this one |
| `RepoDigests` | the registry digests Docker recorded for a pulled image |
| `imageID` | in a pod's status, the digest the node actually runs |

**See it on a real system**

```bash
docker buildx imagetools inspect python:3.12-slim | head -n 3
docker service inspect --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}' shop_api
kubectl -n shop get pods -l app=api \
  -o custom-columns='POD:.metadata.name,NODE:.spec.nodeName,IMAGEID:.status.containerStatuses[0].imageID'
```

```
Name:      docker.io/library/python:3.12-slim
MediaType: application/vnd.oci.image.index.v1+json
Digest:    sha256:9c3f1e8a7b6d5c4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c1d0e
harbor.example.com/shop/api:1.8.1@sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c
POD                    NODE   IMAGEID
api-6d9f7c8b5-x2k8p    w1     harbor.example.com/shop/api@sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c
api-6d9f7c8b5-r7m4q    w2     harbor.example.com/shop/api@sha256:7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b7c6d
```

→ Swarm stored `tag@digest`, so the Dokploy service is pinned. In Kubernetes the two replicas of
the same Deployment run **different digests**: someone pushed a new build under `1.8.1` between the
two pulls.

**Hands-on lab (homelab only)**

**Step 1 — Pin the base.** Replace `FROM python:3.12-slim` with the tag plus the digest from
`imagetools inspect`, rebuild, and record the digest in the merge request.

**Step 2 — Break it.** In a lab Harbor project without immutability, push a second build as
`lab/api:1.0`, then delete one pod of a Deployment that uses `lab/api:1.0` with
`imagePullPolicy: Always`. Compare `imageID` across the pods as above: they differ.

**Step 3 — Fix it.** Deploy by digest (`kubectl -n shop set image deployment/api api=harbor.example.com/shop/api@sha256:...`),
enable tag immutability for release tags in Harbor, and have the pipeline pass digests, not tags,
from build to deploy (the last topic of this area).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Replicas run different code | intermittent behaviour, "only some requests fail" | `imageID` per pod (above) | [Containers & K8s playbook](26-playbook-containers-k8s.md) |
| Rebuild picks a new base silently | new CVEs or behaviour after a "no-change" rebuild | `docker history`, the `FROM` line | this topic |
| Digest of the wrong platform pinned | `no matching manifest for linux/arm64` on some nodes | `docker buildx imagetools inspect` (index vs manifest) | this topic |
| Digest deleted by retention | `manifest unknown` on rollback | Harbor retention rules | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |

**Why it matters for troubleshooting.** "Half the pods behave differently" has a short list of
causes, and a moved tag is near the top. A digest makes "what exactly is running?" a fact rather
than an assumption.

**Next step:** the application's own dependencies.

### Dependency scanning

**Level:** [L2 · Mid]

**Concept.** Application dependencies (pip, npm, Maven, Go modules) bring most of an app's code and
a large share of its vulnerabilities. Two different risks hide here:

- **Known vulnerabilities** in legitimate packages: found by scanners that read your **lockfile** and compare exact versions with advisory databases.
- **Malicious packages**: typosquats (`reqeusts`), hijacked maintainer accounts, and **dependency confusion**, where an installer prefers a public package that has the same name as your internal one. Scanners catch these poorly; process catches them: review every new dependency, install only from one private index or proxy, and use scoped names for internal packages.

A scanner can only check versions it can see. An unpinned `requirements.txt` gives it nothing to
check, so a clean result means nothing. The lockfile is the security artifact: `pip-compile
--generate-hashes`, `poetry.lock`, `package-lock.json` (`npm ci` installs exactly what it says).

**Key terms**

| Term | Meaning |
|---|---|
| Lockfile | exact versions (ideally with hashes) of every direct and transitive dependency |
| Transitive dependency | a dependency of a dependency; most vulnerable packages arrive this way |
| `trivy fs` | scans lockfiles and manifests in a directory |
| `pip-audit`, `npm audit` | ecosystem-specific vulnerability checks |
| Private index or proxy | one place packages come from (GitLab package registry, Nexus, Artifactory) |

**See it on a real system**

```bash
trivy fs --scanners vuln --severity HIGH,CRITICAL --ignore-unfixed .
pip-audit -r requirements.txt
npm audit --omit=dev --audit-level=high
```

```
requirements.txt (pip)
======================
Total: 1 (HIGH: 1, CRITICAL: 0)

┌─────────┬────────────────┬──────────┬────────┬───────────────────┬───────────────┬───────────────────────┐
│ Library │ Vulnerability  │ Severity │ Status │ Installed Version │ Fixed Version │ Title                 │
├─────────┼────────────────┼──────────┼────────┼───────────────────┼───────────────┼───────────────────────┤
│ jinja2  │ CVE-YYYY-NNNNN │ HIGH     │ fixed  │ 3.1.4             │ 3.1.6         │ jinja2: example issue │
└─────────┴────────────────┴──────────┴────────┴───────────────────┴───────────────┴───────────────────────┘
```

→ One fixable finding in a transitive dependency (Flask pulls in Jinja2). The fix is a lockfile
update in a merge request, tested like any other change.

**Hands-on lab (throwaway GitLab project)**

**Step 1 — Build.** Add a merge-request job:

```yaml
dependency-scan:
  stage: test
  image:
    name: aquasec/trivy:VERSION
    entrypoint: [""]
  script:
    - trivy fs --exit-code 1 --scanners vuln --severity CRITICAL,HIGH --ignore-unfixed .
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

**Step 2 — Break it.** Replace the pinned `requirements.txt` with unpinned names (`flask`,
`requests`) and run the job. It passes, and Trivy reports nothing: it cannot know which versions
`pip install` will choose tomorrow. A green scan of an unpinned file is false comfort.

**Step 3 — Fix it.** Keep loose requirements in `requirements.in`, generate a hashed lock with
`pip-compile --generate-hashes requirements.in`, install with `pip install --require-hashes -r requirements.txt`,
and scan the lock. Point pip at your one internal index (`PIP_INDEX_URL`) so a public package can
never shadow an internal one.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Unpinned dependencies | scan always clean; builds differ week to week | look for `==` or a lockfile | this topic |
| Lock out of date | scan of the lock disagrees with the image | scan the image too (section 6) | section 6 |
| Hash mismatch on install | `THESE PACKAGES DO NOT MATCH THE HASHES FROM THE REQUIREMENTS FILE` | regenerate the lock; investigate if unexpected | this topic |
| Internal name resolved publicly | unexpected package version installed | `pip download NAME --no-deps -d /tmp/x -v` shows the index used | this topic |

**Why it matters for troubleshooting.** "Nothing changed but the build broke" is very often an
unpinned dependency that released a new version overnight. Lockfiles make builds reproducible,
which is a reliability property before it is a security one.

**Next step:** scan the code itself and the running application.

### SAST and DAST in GitLab CI

**Level:** [L3 · Senior] to set up, developers own the code fixes

**Concept.** **SAST** (static application security testing) reads source code without running it
and flags patterns like SQL built from user input. **DAST** (dynamic testing) attacks the running
application from outside, the way a scanner on the internet would. **Secret detection** looks for
credentials in the repository. GitLab ships templates for all of them; what you get depends on the tier:

| Scanner | GitLab tier | Free-tier alternative |
|---|---|---|
| SAST (Semgrep-based analyzers) | all tiers; MR widgets and the security dashboard need Ultimate | the same template; read the JSON report artifact |
| Secret detection | all tiers | the same template, or gitleaks (section 5) |
| Container scanning (Trivy-based) | all tiers | the same template, or the Trivy job in section 6 |
| Dependency scanning | Ultimate | `trivy fs` (previous topic) |
| DAST | Ultimate | the OWASP ZAP baseline scan below |

The ZAP **baseline** scan only spiders the site and inspects responses passively, so it is safe
against your own staging environment. Full (active) scans send attack payloads: run them only
against a test environment you own, never against production or anything shared.

**Key terms**

| Term | Meaning |
|---|---|
| SAST | source-code analysis; finds injection, weak crypto, unsafe deserialisation |
| DAST | testing the running app over HTTP; finds missing headers, exposed files, injection |
| False positive | a finding that is not exploitable in context; needs a recorded decision |
| `ADDITIONAL_CA_CERT_BUNDLE` | variable that makes GitLab's analyzers trust your private CA |

**See it on a real system** (a pipeline's report artifacts on the Free tier):

```bash
jq -r '.vulnerabilities[] | [.severity, .name, .location.file, (.location.start_line|tostring)] | @tsv' gl-sast-report.json | sort | head -n 3
jq -r '.vulnerabilities[] | [.severity, .name, .location.file] | @tsv' gl-secret-detection-report.json
```

```
High	Improper neutralization of special elements used in an SQL Command ('SQL Injection')	app/reports.py	88
Medium	Use of a broken or risky cryptographic algorithm	app/tokens.py	14
Critical	Generic API Key	deploy/old.env
```

→ One likely real issue (string-built SQL at `reports.py:88`), one to check (which algorithm, used
for what?), and a committed secret, which is handled with section 5's leaked-secret scenario, not by
a code review.

**Hands-on lab (throwaway GitLab project)**

**Step 1 — Build.** Add the templates and a ZAP baseline job against staging:

```yaml
include:
  - template: Jobs/SAST.gitlab-ci.yml
  - template: Jobs/Secret-Detection.gitlab-ci.yml
  - template: Jobs/Container-Scanning.gitlab-ci.yml

variables:
  SAST_EXCLUDED_PATHS: "tests, docs"
  CS_IMAGE: harbor.example.com/shop/api:$CI_COMMIT_SHORT_SHA
  CS_REGISTRY_USER: $HARBOR_ROBOT_USER
  CS_REGISTRY_PASSWORD: $HARBOR_ROBOT_TOKEN

zap-baseline:
  stage: test
  image: zaproxy/zap-stable:VERSION
  script:
    - mkdir -p /zap/wrk
    - zap-baseline.py -t https://staging.example.com -r zap-report.html -I
    - cp /zap/wrk/zap-report.html .
  artifacts:
    when: always
    paths: [zap-report.html]
  allow_failure: true
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

→ `-I` stops warnings from failing the job; FAIL-level findings still do, and `allow_failure`
keeps DAST informative while you tune it. Set `ADDITIONAL_CA_CERT_BUNDLE` (as a CI/CD variable
holding the PEM of your root CA) so GitLab's analyzers (SAST, secret detection, container scanning)
trust Harbor and staging. The ZAP job is your own job, not a GitLab analyzer, so that variable does
not affect it; check its report for TLS errors against staging and, if there are any, give that job
the CA by its own means.

**Step 2 — Break it.** Leave out `ADDITIONAL_CA_CERT_BUNDLE`. The container-scanning job fails
pulling from Harbor with `x509: certificate signed by unknown authority`, while the ZAP job, which
never read that variable, behaves exactly as before.

**Step 3 — Fix and triage.** Add the variable. Then hold a 30-minute triage with the developers:
each finding is fixed, accepted with a reason (a `nosemgrep` comment with a justification, or the
Ultimate dismissal workflow), or ticketed with a date. Untriaged findings turn into noise that
everyone learns to ignore.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Analyzer job never appears | no `semgrep-sast` job | the template runs only when files of a supported language exist | this topic |
| Private CA not trusted | `x509` errors in analyzer logs | `ADDITIONAL_CA_CERT_BUNDLE` | section 4 |
| Reports nobody reads | findings pile up | a triage slot in the weekly rhythm | this topic |
| DAST finds missing headers | ZAP warnings on HSTS, CSP, X-Content-Type-Options | the edge headers topic | section 9 |
| Active scan run against production | errors, junk data, alerts | stop it; scope rules to test environments | this topic |

**Why it matters for troubleshooting.** Security jobs fail pipelines like any other job. A failing
analyzer is usually trust (x509), access (registry credentials) or rules (wrong branch), and its log
says which, just as in [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 2.

**Next step:** put every control from this area into one pipeline.

### Pipeline: scan, sign, deploy

**Level:** [L3 · Senior]

**Concept.** The target pipeline builds once, passes the **digest** from job to job, and only signs
what passed the scan. The deploy job verifies the signature and deploys that digest, and Harbor's
policies (section 6) refuse anything that slipped around the pipeline:

```
 build ──► push IMAGE:SHA ──► digest D ──► trivy gate on D ──► SBOM of D ──► sign D, attest SBOM
                                                                                     │
 Harbor: scan on push, block High+, block unsigned, v* immutable                     ▼
                                              deploy: cosign verify D ──► deploy IMAGE@D
```

The scanning and signing tools come from a small **tools image** your platform team builds from
pinned, checksum-verified releases and keeps in Harbor (`harbor.example.com/platform/ci-tools`).
That avoids `curl | sh` installs in every job, the exact pattern the Codecov incident abused.

```yaml
stages: [build, scan, sign, deploy]

variables:
  IMAGE: harbor.example.com/shop/api
  TOOLS: harbor.example.com/platform/ci-tools:2026.10

build:
  stage: build
  image: docker:27
  services:
    - name: docker:27-dind
  variables:
    DOCKER_TLS_CERTDIR: "/certs"
  script:
    # the DinD service must trust Harbor's CA: see "Building images" in the CI/CD module
    - echo "$HARBOR_ROBOT_TOKEN" | docker login -u "$HARBOR_ROBOT_USER" --password-stdin harbor.example.com
    - docker build --pull -t "$IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker push "$IMAGE:$CI_COMMIT_SHORT_SHA" | tee push.log
    - awk '/digest: sha256:/ {print "DIGEST=" $3}' push.log > build.env
    - cat build.env
  artifacts:
    reports:
      dotenv: build.env

trivy-gate:
  stage: scan
  image: $TOOLS
  variables:
    TRIVY_USERNAME: $HARBOR_ROBOT_USER
    TRIVY_PASSWORD: $HARBOR_ROBOT_TOKEN
    TRIVY_CACHE_DIR: .trivycache/
  cache:
    key: trivy-db
    paths: [.trivycache/]
  script:
    - trivy image --exit-code 0 --severity HIGH,CRITICAL --format json --output trivy.json "$IMAGE@$DIGEST"
    - trivy image --skip-db-update --exit-code 1 --severity CRITICAL --ignore-unfixed --ignorefile .trivyignore.yaml "$IMAGE@$DIGEST"
  artifacts:
    when: always
    paths: [trivy.json]

sbom-sign:
  stage: sign
  image: $TOOLS
  script:
    - echo "$HARBOR_ROBOT_TOKEN" | cosign login harbor.example.com -u "$HARBOR_ROBOT_USER" --password-stdin
    - syft scan "registry:$IMAGE@$DIGEST" -o cyclonedx-json=sbom.cdx.json
    - cosign sign --yes --key "$COSIGN_KEY_FILE" "$IMAGE@$DIGEST"
    - cosign attest --yes --key "$COSIGN_KEY_FILE" --type cyclonedx --predicate sbom.cdx.json "$IMAGE@$DIGEST"
  artifacts:
    paths: [sbom.cdx.json]
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH

deploy-staging:
  stage: deploy
  image: $TOOLS
  environment: staging
  script:
    - cosign verify --key "$COSIGN_PUB_FILE" "$IMAGE@$DIGEST" > /dev/null
    - kubectl -n shop set image deployment/api api="$IMAGE@$DIGEST"
    - kubectl -n shop rollout status deployment/api --timeout=180s
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

→ Variables to create in GitLab, all **protected** so only protected branches see them:
`HARBOR_ROBOT_USER` and `HARBOR_ROBOT_TOKEN` (masked), `COSIGN_PASSWORD` (masked; cosign reads it
from the environment), `COSIGN_KEY_FILE` and `COSIGN_PUB_FILE` (type *File*), and a kubeconfig for
the `gitlab-deployer` identity from section 7 as a *File* variable named `KUBECONFIG` (or the GitLab
agent for Kubernetes instead). For Dokploy, the deploy job calls Dokploy's API with `IMAGE@DIGEST`
as the image, as shown in [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md).

**Key terms**

| Term | Meaning |
|---|---|
| dotenv report | job artifact whose `KEY=value` lines become variables in later jobs |
| Tools image | a pinned, scanned, signed image holding trivy, syft, cosign, kubectl |
| Protected variable | only exposed to pipelines on protected branches and tags |
| Gate | a job whose non-zero exit stops the pipeline |

**See it on a real system** (the build job's log tail and the deploy job's check):

```
$ cat build.env
DIGEST=sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c
...
Verification for harbor.example.com/shop/api@sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c --
The following checks were performed on each of these signatures:
  - The cosign claims were validated
  - Existence of the claims in the transparency log was verified offline
  - The signatures were verified against the specified public key
deployment.apps/api image updated
deployment "api" successfully rolled out
```

**Hands-on lab (throwaway GitLab project, lab Harbor and homelab)**

**Step 1 — Build it** exactly as above. Confirm in Harbor that the pushed digest shows a scan
report, a signature and an attestation.

**Step 2 — Break it, three ways, one at a time.** Switch the Dockerfile to an old base image: the
`trivy-gate` job fails and nothing is signed or deployed. Comment out the `cosign sign` line: the
deploy job's `cosign verify` fails, and even a manual `kubectl set image` to that digest ends in
`ImagePullBackOff`, because Harbor's Cosign policy refuses the pull. Rename the dotenv file in the
build job: later jobs fail with `could not parse reference: harbor.example.com/shop/api@` (the
go-containerregistry wording used by Trivy and cosign; Docker itself says
`invalid reference format`), because `$DIGEST` is empty.

**Step 3 — Fix each one** and write down, for each break, which control caught it. That table is
your answer when someone asks "what stops a bad image reaching production?"

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| `$DIGEST` empty | `could not parse reference` (Trivy, cosign) or `invalid reference format` (Docker) | the build job's `cat build.env` output | this topic |
| Gate fails on CRITICAL | red `trivy-gate`, nothing deployed | read `trivy.json`; rebuild with a fresh base | section 6 |
| Signing fails | `UNAUTHORIZED` or decryption error | `cosign login`; `COSIGN_PASSWORD` protected but branch not protected | section 5 |
| Verify fails in deploy | `no signatures found` (digest never signed) or `no matching signatures` (other key) | was the digest signed, with which key? | signing topic above |
| Pull refused on nodes | `ImagePullBackOff` with Harbor's policy message | `kubectl describe pod POD` | section 6 |

**Why it matters for troubleshooting.** When a release does not arrive, this pipeline tells you
which control stopped it and why, in the job log. That is the operational payoff of DevSecOps:
security decisions that explain themselves.

**Next step:** harden the edge that the internet actually talks to.

---

## 9. Web and edge hardening

> 📚 **Study path:** 1) Note: [Web servers & proxies](29-learn-webservers-proxies.md) topics 2.6 (TLS with mod_ssl) and 4.9 (dashboard, API and access logs), and its section 8 capstone (Apache behind Traefik) — the mechanics this area secures · 2) KodeKloud: *Nginx For Beginners* — Security: [HTTPS](https://notes.kodekloud.com/docs/Nginx-For-Beginners/Security/HTTPS/page), for TLS and header concepts that carry over to any proxy ([course](https://kodekloud.com/courses/nginx-for-beginners)) · 3) KodeKloud: *Kubernetes Networking Deep Dive* — [Traefik Overview](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page) ([course](https://kodekloud.com/courses/kubernetes-networking)) · 4) Video: Jim's Garage *Traefik v3.3 - Secure Everything! Complete Tutorial* (32 min, [YouTube](https://www.youtube.com/watch?v=CmUzMi5QLzI)) · 5) Reading: the [OWASP](https://owasp.org/) Secure Headers project · 6) Practice: the labs below on sec-target, checked from sec-scan, then [badssl.com](https://badssl.com/) to compare your results with known-good and known-bad configurations.

The edge is the only part of your stack the internet talks to directly: Traefik on 80/443 in front
of Dokploy apps, and Apache on 81/444 behind it. Section 3 reduced what is reachable to those ports;
this area hardens what answers on them. The four topics follow the order an attacker would probe:
admin interfaces first, then TLS and headers, then paths around the proxy, then brute force.

### Closing admin endpoints

**Level:** [L2 · Mid]

**Concept.** Admin interfaces are worth more to an attacker than any application page: the Traefik
dashboard and API (every route, backend and middleware), the Dokploy UI, Apache's `server-status`,
Grafana, Prometheus, Portainer. Each one should be **closed**, reachable only over the VPN or a
tunnel, or published on 443 behind authentication **and** an IP allowlist.

Dokploy's generated `traefik.yml` contains `api: insecure: true` (see the
[Apache 443 case](21-case-apache-443-dokploy.md)). That serves the API and dashboard on port 8080
inside the container. Port 8080 is only published on the host when you enable the dashboard in
Dokploy's Traefik settings, but even unpublished it is reachable from every container on
`dokploy-network`, so any compromised app can read your full routing table. Section 3's nmap scan
found 8080 open on sec-target; this topic closes it properly.

**Key terms**

| Term | Meaning |
|---|---|
| `api@internal` | Traefik's built-in service for its API and dashboard |
| `api.insecure` | serves the API on the `traefik` entryPoint (8080) without any authentication |
| `ipAllowList` | Traefik v3 middleware that only admits listed source ranges (v2 called it `ipWhiteList`) |
| `basicAuth` | middleware for HTTP basic authentication with htpasswd hashes |
| mod_status | Apache's `server-status` page: live requests, client IPs, URLs |

**See it on a real system**

```bash
nmap -Pn -p 3000,8080,9090,9100 192.168.56.21                      # from sec-scan
sudo grep -A1 '^api:' /etc/dokploy/traefik/traefik.yml          # host path; inside the container it is /etc/traefik/traefik.yml
docker port dokploy-traefik
curl -s -H 'Host: crm.example.com' 'http://127.0.0.1:81/server-status?auto' | head -n 4
```

```
PORT     STATE    SERVICE
3000/tcp filtered ppp
8080/tcp open     http-proxy
9090/tcp filtered zeus-admin
9100/tcp filtered jetdirect
api:
  insecure: true
80/tcp -> 0.0.0.0:80
443/tcp -> 0.0.0.0:443
443/udp -> 0.0.0.0:443
8080/tcp -> 0.0.0.0:8080
crm.example.com
ServerVersion: Apache/2.4.58 (Ubuntu)
ServerMPM: event
Server Built: 2025-07-14T15:07:26
```

→ 3000, 9090 and 9100 are filtered (section 3's work), but 8080 is published and open: the dashboard
toggle is on. Apache's `server-status` answers here because the request comes from 127.0.0.1:
Ubuntu's `/etc/apache2/mods-available/status.conf` ships with `Require local`. Check that nobody
widened it (`grep -A4 'server-status' /etc/apache2/mods-enabled/status.conf`), because requests
proxied by Traefik arrive from a Docker address and must keep getting 403.

**Hands-on lab (test VM only)**

**Step 1 — Publish the dashboard safely.** Turn the dashboard toggle off in Dokploy (8080 disappears
from `docker port`), then add a router in `/etc/dokploy/traefik/dynamic/admin.yml`:

```yaml
http:
  routers:
    traefik-dashboard:
      rule: "Host(`traefik.example.com`) && (PathPrefix(`/api`) || PathPrefix(`/dashboard`))"
      entryPoints: ["websecure"]
      service: api@internal
      middlewares: ["office-only", "admin-auth"]
      tls:
        certResolver: letsencrypt
  middlewares:
    office-only:
      ipAllowList:
        sourceRange: ["198.51.100.0/24", "10.8.0.0/24"]
    admin-auth:
      basicAuth:
        users:
          - "admin:HASH_FROM_HTPASSWD"
```

Generate the hash with `htpasswd -nB admin` (package `apache2-utils`) and paste the whole
`admin:...` line. In a file-provider YAML the `$` signs need no escaping; in Docker labels they do
(`$$`). `10.8.0.0/24` stands for your WireGuard range from section 3.

**Step 2 — Break it.** From sec-scan (not in the allowlist) request the dashboard:
`curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: traefik.example.com' -k https://192.168.56.21/dashboard/`
prints `403`. From an allowed address without credentials it prints `401`. Both are the controls
working; a `200` without credentials would be the finding.

**Step 3 — Close the rest.** Keep `server-status` limited to localhost in Apache
(`<Location "/server-status">` with `Require local`, the Ubuntu default; restore it if someone
changed it to `Require all granted`), confirm Grafana and Prometheus are reachable
only through authenticated routes or the VPN, and add the four ports to the nmap check you run after
every change.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Dashboard published again | 8080 open after a Dokploy update or toggle | `docker port dokploy-traefik` | this topic |
| Router not loaded | 404 for `traefik.example.com` | Traefik log: `docker logs dokploy-traefik 2>&1 | grep -i error` | [Web servers & proxies](29-learn-webservers-proxies.md) |
| Allowlist sees the wrong IP | everyone gets 403 behind another proxy or LB | `ipStrategy` settings, access log client IP | this topic |
| `server-status` reachable through Traefik | status page on a public hostname | `curl -s https://crm.example.com/server-status` | this topic |

**Why it matters for troubleshooting.** A 401 means "authentication needed", a 403 from Traefik
usually means an allowlist decision. Reading the code and the access log tells you which control
answered before you touch any configuration.

**Next step:** what every client sees, TLS and response headers.

### TLS settings and headers

**Level:** [L2 · Mid]

**Concept.** Two layers decide how safely a browser talks to you. **TLS settings**: protocol
versions (1.2 and 1.3 only), cipher suites with forward secrecy, and `sniStrict` (refuse handshakes
for names you do not serve). Traefik v3 already defaults to TLS 1.2 and Go's modern cipher list;
setting them explicitly protects you from a copied config or a future default change. **Security
headers**: HSTS (always use HTTPS for this site), `X-Content-Type-Options: nosniff`, frame
protection against clickjacking, a referrer policy, and removing headers that advertise versions.

HSTS deserves care. Once a browser has seen `max-age=31536000`, it refuses plain HTTP to that host
for a year. With `includeSubDomains`, that applies to every subdomain, including internal tools that
may still be HTTP-only. Start with a short `max-age`, raise it after a week, and add
`includeSubDomains` only when every subdomain serves valid HTTPS. `preload` is effectively permanent.

On Dokploy, put both in a file under `/etc/dokploy/traefik/dynamic/` and attach the headers
middleware to the `websecure` entryPoint in the static `traefik.yml`, so every app gets it
(`entryPoints.websecure.http.middlewares: [secure-headers@file]`; a static change needs a Traefik
restart from Dokploy):

```yaml
tls:
  options:
    default:
      minVersion: VersionTLS12
      sniStrict: true
      cipherSuites:
        - TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256
        - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
        - TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305
        - TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305
http:
  middlewares:
    secure-headers:
      headers:
        stsSeconds: 300
        forceSTSHeader: true
        contentTypeNosniff: true
        frameDeny: true
        referrerPolicy: "strict-origin-when-cross-origin"
        permissionsPolicy: "camera=(), microphone=(), geolocation=()"
        customResponseHeaders:
          Server: ""
          X-Powered-By: ""
```

For Apache vhosts that still terminate TLS themselves, the equivalent in a conf snippet (needs
`a2enmod headers ssl`):

```apache
SSLProtocol -all +TLSv1.2 +TLSv1.3
SSLHonorCipherOrder off
SSLSessionTickets off
ServerTokens Prod
ServerSignature Off
TraceEnable Off
Header always set Strict-Transport-Security "max-age=300"
Header always set X-Content-Type-Options "nosniff"
Header always set X-Frame-Options "DENY"
```

**Key terms**

| Term | Meaning |
|---|---|
| Forward secrecy | ECDHE key exchange: recorded traffic stays safe even if the key leaks later |
| `sniStrict` | reject TLS clients that send no SNI or an unknown name |
| HSTS | `Strict-Transport-Security`: browsers use HTTPS only, for `max-age` seconds |
| `nosniff` | stops browsers guessing content types (MIME sniffing) |
| `ServerTokens Prod` | Apache sends `Server: Apache` instead of the exact version and OS |

**See it on a real system**

```bash
curl -sI https://shop.example.com/ | grep -iE '^(strict-transport-security|x-content-type-options|x-frame-options|referrer-policy|server):'
openssl s_client -connect shop.example.com:443 -servername shop.example.com -brief </dev/null 2>&1 | head -n 3
nmap --script ssl-enum-ciphers -p 443 shop.example.com
```

```
strict-transport-security: max-age=300
x-content-type-options: nosniff
x-frame-options: DENY
referrer-policy: strict-origin-when-cross-origin
CONNECTION ESTABLISHED
Protocol version: TLSv1.3
Ciphersuite: TLS_AES_128_GCM_SHA256
PORT    STATE SERVICE
443/tcp open  https
| ssl-enum-ciphers:
|   TLSv1.2:
|     ciphers:
|       TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256 (secp256r1) - A
|       TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384 (secp256r1) - A
|       TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256 (secp256r1) - A
|     compressors:
|       NULL
|     cipher preference: client
|   TLSv1.3:
|     ciphers:
|       TLS_AKE_WITH_AES_128_GCM_SHA256 (ecdh_x25519) - A
|       TLS_AKE_WITH_AES_256_GCM_SHA384 (ecdh_x25519) - A
|       TLS_AKE_WITH_CHACHA20_POLY1305_SHA256 (ecdh_x25519) - A
|     cipher preference: client
|_  least strength: A
```

→ Headers present, no `Server` header leaking a version, TLS 1.3 negotiated, only TLS 1.2 and 1.3
offered, every suite graded A. Save this output: it is the before-and-after evidence for a change
request and for an auditor (section 14).

**Hands-on lab (test VM only)**

**Step 1 — Build.** Apply the file above on sec-target's Traefik and rerun the three checks from
sec-scan. Record the results.

**Step 2 — Break it, twice.** Add `stsIncludeSubdomains: true` while an internal tool such as
`http://grafana.lab.example.com` still serves plain HTTP: after visiting the main site, the browser
refuses to load the tool over HTTP. Then point a monitoring check at `https://192.168.56.21/` (an IP,
no hostname): with `sniStrict`, the handshake fails instead of returning the default certificate.

**Step 3 — Fix it.** Clear the HSTS entry for the lab host in the browser's settings, move the tool
behind HTTPS before adding `includeSubDomains` again, and make monitors use hostnames. Raise
`stsSeconds` to 31536000 only after a quiet week.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| HSTS on a host without valid HTTPS | browser refuses, no "proceed anyway" button | `curl -sI` for the header; browser HSTS settings | this topic |
| `sniStrict` and IP-based checks | handshake failure from monitors or old clients | `openssl s_client -connect IP:443` with and without `-servername` | [Site down playbook](25-playbook-site-down.md) |
| Headers missing on one app | that app's router bypasses the entryPoint middleware | Traefik dashboard: the router's middlewares | [Web servers & proxies](29-learn-webservers-proxies.md) |
| Header set twice | Apache and Traefik both add it | `curl -sI` shows duplicates; set it in one place | this topic |

**Why it matters for troubleshooting.** TLS and HSTS mistakes produce some of the hardest client
errors to debug from the server side, because the browser refuses before any request reaches you.
`openssl s_client` and `curl -sI` show exactly what clients see.

**Next step:** make sure nobody reaches Apache without going through Traefik.

### Apache behind Traefik

**Level:** [L2 · Mid]

**Concept.** Your migration moved Apache to ports 81 and 444, with Traefik routing the legacy sites
to `http://192.0.2.10:81` ([Deployment patterns](35-deployment-patterns.md) section 1). That design
is only secure if three things hold:

1. **81 and 444 are not reachable from outside.** Otherwise clients can skip Traefik and with it HTTPS, the security headers, rate limits and the access log. The UFW rule allows 81 only on `docker_gwbridge`, the interface Traefik's packets arrive on.
2. **Apache trusts `X-Forwarded-For` only from Traefik.** `mod_remoteip` with `RemoteIPInternalProxy` limited to the `docker_gwbridge` range; trusting it from everywhere lets any client forge its address in logs and in `Require ip` rules.
3. **The default vhost on 81 reveals nothing.** Requests with an unknown Host header should get a 404 or 403, not the first site in alphabetical order.

**Key terms**

| Term | Meaning |
|---|---|
| Bypass path | any route to a backend that skips the proxy's controls |
| `docker_gwbridge` | the bridge through which Swarm containers reach host services (172.18.0.0/16 here) |
| `RemoteIPInternalProxy` | proxies whose `X-Forwarded-For` Apache believes, including private client IPs |
| Default vhost | the first vhost for an IP and port; it answers unknown Host headers |

**See it on a real system**

```bash
nmap -Pn -p 80,81,443,444 192.0.2.10                                   # from outside
sudo ufw status numbered | grep -E ' (81|444)/'
sudo grep -rhE '^\s*RemoteIP(Header|InternalProxy|TrustedProxy)' /etc/apache2/
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: unknown.example.net' http://127.0.0.1:81/
```

```
PORT    STATE    SERVICE
80/tcp  open     http
81/tcp  filtered hosts2-ns
443/tcp open     https
444/tcp filtered snpp
[ 5] 81/tcp on docker_gwbridge     ALLOW IN    Anywhere                   # Traefik -> Apache
RemoteIPHeader X-Forwarded-For
RemoteIPInternalProxy 172.18.0.0/16
404
```

→ All three hold: 81 and 444 are filtered from outside, only Traefik's interface may reach 81,
Apache believes `X-Forwarded-For` only from 172.18.0.0/16, and an unknown Host gets a 404.

**Hands-on lab (test VM only)**

**Step 1 — Build.** Reproduce the setup on sec-target from the capstone in
[Web servers & proxies](29-learn-webservers-proxies.md) section 8, with the UFW rule from
[Deployment patterns](35-deployment-patterns.md) section 1. Run the checks above against
192.168.56.21 from sec-scan.

**Step 2 — Break it.** "Temporarily" run `sudo ufw allow 81/tcp`, as someone debugging might. From
sec-scan, `curl -s -H 'Host: crm.example.com' http://192.168.56.21:81/` now returns the site over
plain HTTP, with no Traefik headers and no line in Traefik's access log. Then check that the
`X-Forwarded-For` trust is still narrow: send
`curl -s -H 'Host: crm.example.com' -H 'X-Forwarded-For: 203.0.113.99' http://192.168.56.21:81/`
and confirm Apache's access log records sec-scan's real address (192.168.56.22), not 203.0.113.99.

**Step 3 — Fix it.** Delete the rule (`sudo ufw status numbered`, `sudo ufw delete N`), rerun nmap,
and add "81 and 444 filtered from outside" to the post-change checklist in
[Deployment patterns](35-deployment-patterns.md) section 6.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| 81 or 444 opened to the world | site reachable without HTTPS on 81 | nmap from outside | section 3 |
| Remote IP trusted from everywhere | forged addresses in logs, allowlists bypassed | the `RemoteIP*` grep above | [Apache 443 case](21-case-apache-443-dokploy.md) |
| Every client logged as 172.18.0.x | `mod_remoteip` missing or wrong range | `apache2ctl -M | grep remoteip` | [Web servers & proxies](29-learn-webservers-proxies.md) |
| Unknown Host gets a real site | a default vhost serves content | `apache2ctl -S` | this topic |

**Why it matters for troubleshooting.** When a legacy site "works on port 81 but not through the
domain", the fix is in Traefik's routing or the UFW interface rule, never in opening 81 to the world.

**Next step:** slow down brute force and filter obvious attacks.

### Rate limits, allowlists and WAF

**Level:** [L3 · Senior]

**Concept.** Three edge controls with different jobs:

- **Rate limits** slow down password guessing and scraping. Traefik's `rateLimit` middleware answers `429 Too Many Requests` above an average rate with a burst allowance, per client IP by default.
- **Allowlists** remove whole audiences: admin paths only from the office and VPN ranges (`ipAllowList`, answers `403`).
- **A WAF** (web application firewall) inspects requests for attack patterns. On Apache that is ModSecurity with the OWASP Core Rule Set (CRS), packaged in Ubuntu; ModSecurity is now maintained under OWASP. For Traefik, WAF plugins such as Coraza exist; evaluate them like any other dependency.

A WAF always starts in **detection-only** mode. Run it for a week or two, read what it would have
blocked, tune the false positives, and only then switch blocking on. A WAF switched straight to
blocking breaks a login form or an API client on the first day, and gets disabled for good.

```yaml
http:
  middlewares:
    login-ratelimit:
      rateLimit:
        average: 10
        period: 1m
        burst: 20
```

Attach it only to the routes that need it (login, password reset, API token endpoints), for example
by adding `login-ratelimit@file` to that router's middlewares in the app's Traefik configuration
(Dokploy shows it in the application's advanced Traefik settings).

**Key terms**

| Term | Meaning |
|---|---|
| `average`, `period`, `burst` | allowed requests per period, and how many may arrive at once |
| `sourceCriterion` | what a rate limit counts by: client IP (default), a header, or the host |
| OWASP CRS | the Core Rule Set: generic rules for injection, scanners, protocol abuse |
| Paranoia level | CRS strictness from 1 to 4; higher catches more and breaks more |
| `DetectionOnly` | ModSecurity logs matches but blocks nothing |

**See it on a real system** (sec-target, Apache on 81 with ModSecurity in detection mode):

```bash
sudo apt-get install -y libapache2-mod-security2 modsecurity-crs
sudo cp /etc/modsecurity/modsecurity.conf-recommended /etc/modsecurity/modsecurity.conf
grep -E '^SecRuleEngine' /etc/modsecurity/modsecurity.conf
sudo apachectl configtest && sudo systemctl reload apache2
curl -s -o /dev/null -A 'Nikto' -H 'Host: crm.example.com' http://127.0.0.1:81/
sudo grep -h 'id "913100"' /var/log/apache2/error.log | tail -n 1
```

```
SecRuleEngine DetectionOnly
Syntax OK
[Sat Oct 03 11:02:41.118204 2026] [security2:error] [pid 4121] [client 127.0.0.1] ModSecurity: Warning. Matched phrase "nikto" at REQUEST_HEADERS:User-Agent. [file "/usr/share/modsecurity-crs/rules/REQUEST-913-SCANNER-DETECTION.conf"] [id "913100"] [msg "Found User-Agent associated with security scanner"] [hostname "crm.example.com"] [uri "/"]
```

→ A harmless request carrying a scanner's User-Agent matched CRS rule 913100. In detection mode
the request was still served; the log line is what you review during tuning.

**Hands-on lab (test VM only)**

**Step 1 — Rate-limit a login route** on sec-target's Traefik and test from sec-scan:

```bash
for i in $(seq 1 40); do
  curl -s -o /dev/null -w '%{http_code}\n' -k -H 'Host: shop.example.com' https://192.168.56.21/login
done | sort | uniq -c
```

```
     20 200
     20 429
```

**Step 2 — Break it.** Put another proxy or a load balancer in front of Traefik (on the lab, a
second Traefik or HAProxy container on sec-scan). Now every request arrives from that proxy's IP and
all users share one bucket: real users get 429 together. The same happens to `ipAllowList`, which
sees only the proxy.

**Step 3 — Fix it.** Tell the middleware how to find the client: `sourceCriterion.ipStrategy.depth: 1`
(or `excludedIPs` with the proxy's address) for `rateLimit`, and `ipStrategy` for `ipAllowList`,
together with `forwardedHeaders.trustedIPs` on the entryPoint so Traefik only believes
`X-Forwarded-For` from that proxy. Then plan the WAF: one to two weeks in `DetectionOnly`, a tuning
review, then `SecRuleEngine On` in a change window, with the rollback (set it back to
`DetectionOnly`, reload) written in the change request.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Everyone rate-limited together | bursts of 429 for all users | access log: one client IP for everyone | this topic |
| Allowlist blocks the office | 403 after a network change | access log client IP vs `sourceRange` | this topic |
| WAF blocks a legitimate form | 403 on POST, ModSecurity line in `error.log` | `grep ModSecurity /var/log/apache2/error.log | tail` | this topic |
| fail2ban bans have no effect on Traefik | attacker keeps hitting 443 | bans land in INPUT; Docker traffic goes through FORWARD | section 3 (DOCKER-USER) |

**Why it matters for troubleshooting.** 401, 403 and 429 are controls answering. The access log's
status code and client IP, read before anything else, tell you which control and whether it saw the
right client.

**Next step:** the same thinking for cloud accounts.

---

## 10. Cloud security on AWS

> 📚 **Study path:** 1) Note: [Learn: Cloud & AWS](36-learn-cloud-aws.md) sections 2 (IAM and identity), 4 (its IMDSv2 topic) and 9 (CloudTrail and Config), which this area builds on · 2) KodeKloud: *AWS Certified CloudOps Engineer - Associate* — the Security domain (IAM, KMS, GuardDuty, Security Hub) ([link](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 3) KodeKloud: *Crash Course: AWS Basics* first if IAM users and roles are new ([link](https://kodekloud.com/courses/crash-course-aws-basics)) · 4) Docs: the IAM, EC2 instance metadata and GuardDuty user guides at [docs.aws.amazon.com](https://docs.aws.amazon.com/) · 5) Practice: the sandbox account from section 0 (budget alarm first) or the [AWS Playground](https://kodekloud.com/cloud-playgrounds/aws).

In the cloud, identity is the perimeter. Most AWS incidents do not start with an exploit; they
start with a long-lived access key in a Git repository, a CI variable or a laptop, or with an
instance role reachable through a web application bug. This area applies the earlier ideas (least
privilege, short-lived credentials, audit logs, detection) to an AWS account. The commands assume
the AWS CLI v2 and the sandbox account 123456789012 in `ap-south-1`.

### Account security baseline

**Level:** [L3 · Senior]

**Concept.** A short list of account-level settings prevents or exposes most common mistakes. Check
them in every account you are responsible for, at least quarterly:

| Control | Check | Expected |
|---|---|---|
| Root user has MFA, no access keys | `aws iam get-account-summary --query 'SummaryMap.[AccountMFAEnabled,AccountAccessKeysPresent]'` | `[1, 0]` |
| People sign in through IAM Identity Center, not IAM users | `aws iam list-users --query 'Users[].UserName'` | only break-glass and documented service users |
| CloudTrail multi-region trail, logging, with validation | `aws cloudtrail describe-trails`, `get-trail-status` | logging, `LogFileValidationEnabled: true` |
| GuardDuty on in every region you use | `aws guardduty list-detectors` | one detector ID per region |
| S3 Block Public Access at account level | `aws s3control get-public-access-block --account-id 123456789012` | all four settings `true` |
| EBS encryption by default | `aws ec2 get-ebs-encryption-by-default` | `true` |
| IMDSv2 required by default | `aws ec2 get-instance-metadata-defaults` | `HttpTokens: required` |
| IAM Access Analyzer | `aws accessanalyzer list-analyzers` | at least one active analyzer |
| Budget alarm | `aws budgets describe-budgets --account-id 123456789012` | a budget with an alert |

**Key terms**

| Term | Meaning |
|---|---|
| Root user | the account owner identity; cannot be restricted by IAM; used almost never |
| IAM Identity Center | AWS single sign-on: people get short-lived role sessions instead of IAM users |
| Block Public Access | account- or bucket-level switches that override public ACLs and policies |
| Access Analyzer | finds resources shared outside the account and, optionally, unused access |

**See it on a real system**

```bash
aws iam get-account-summary --query 'SummaryMap.[AccountMFAEnabled,AccountAccessKeysPresent]' --output text
aws s3control get-public-access-block --account-id 123456789012
aws ec2 get-instance-metadata-defaults --region ap-south-1
```

```
1	0
{
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }
}
{
    "AccountLevel": {
        "HttpTokens": "required",
        "HttpPutResponseHopLimit": 1
    }
}
```

→ Root has MFA and no keys, nothing in S3 can be made public by accident, and new instances in
this region require IMDSv2 unless someone overrides it at launch.

**Hands-on lab (sandbox account only)**

**Step 1 — Build.** Run every check in the table, fix the gaps in the sandbox, and save the outputs
with a date: that file is your baseline evidence (section 14).

**Step 2 — Break it.** Try to make a bucket public while Block Public Access is on:

```bash
aws s3api create-bucket --bucket lab-public-test-123456789012 --region ap-south-1 \
  --create-bucket-configuration LocationConstraint=ap-south-1
aws s3api put-bucket-policy --bucket lab-public-test-123456789012 --policy '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":"*","Action":"s3:GetObject","Resource":"arn:aws:s3:::lab-public-test-123456789012/*"}]}'
```

```
An error occurred (AccessDenied) when calling the PutBucketPolicy operation: User: arn:aws:iam::123456789012:user/alice is not authorized to perform: s3:PutBucketPolicy on resource: "arn:aws:s3:::lab-public-test-123456789012" because public policies are blocked by the BlockPublicPolicy block public access setting.
```

**Step 3 — Fix the need, not the control.** If something must be public (a static site, downloads),
serve it through CloudFront with origin access control and keep the bucket private. Delete the lab
bucket afterwards.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Public policy refused | `blocked by the BlockPublicPolicy block public access setting` | `aws s3control get-public-access-block` | this topic |
| Root used for daily work | `ConsoleLogin` events by root in CloudTrail | `aws cloudtrail lookup-events` (last topic) | section 13 |
| A region without GuardDuty | resources there are unmonitored | `aws guardduty list-detectors --region R` per region | last topic |
| Bill surprise from a forgotten resource | budget alert | Cost Explorer | [Learn: Cloud & AWS](36-learn-cloud-aws.md) section 12 |

**Why it matters for troubleshooting.** Many "AccessDenied" errors in a well-run account are these
guardrails speaking, and their messages say so. Recognising them saves you from loosening IAM to
fix something IAM never blocked.

**Next step:** the credentials themselves.

### Access keys and access reviews

**Level:** [L3 · Senior]

**Concept.** An IAM access key never expires on its own. It ends up in CI variables, `.env` files,
laptops and screenshots, and it keeps working from anywhere in the world. The safe pattern: people
use Identity Center sessions, workloads use roles (instance profiles, task roles, OIDC from CI), and
the few remaining keys are inventoried, rotated and reviewed. The **credential report** lists every
IAM user with password, MFA and key status and last use; it is the input to a quarterly access
review, which auditors expect to see (section 14).

Rotation without an outage uses the two key slots: create a second key, switch the consumer to it,
confirm the old key's last-used date stops moving, **deactivate** the old key, wait a week, then
delete it. Deactivating first is the safe way to find consumers nobody remembered: if something
breaks, reactivate it and you have found one.

**Key terms**

| Term | Meaning |
|---|---|
| Credential report | CSV of all IAM users: password, MFA, keys, last rotated, last used |
| Access key last used | date, region and service of a key's last request |
| Deactivate vs delete | inactive keys can be re-enabled; deleted keys are gone |
| Access review | periodic check that every identity still needs its access, with a record of the decision |

**See it on a real system**

```bash
aws iam generate-credential-report >/dev/null
aws iam get-credential-report --query Content --output text | base64 -d \
  | cut -d, -f1,4,8,9,10,11 | column -s, -t
aws iam get-access-key-last-used --access-key-id AKIAIOSFODNN7EXAMPLE
```

```
user              password_enabled  mfa_active  access_key_1_active  access_key_1_last_rotated  access_key_1_last_used_date
<root_account>    not_supported     true        false                N/A                        N/A
alice             true              true        false                N/A                        N/A
gitlab-ci         false             false       true                 2024-02-11T09:12:44+00:00  2026-10-02T21:40:03+00:00
old-backup        false             false       true                 2022-06-01T10:00:00+00:00  2023-01-14T03:00:12+00:00
{
    "UserName": "gitlab-ci",
    "AccessKeyLastUsed": {
        "LastUsedDate": "2026-10-02T21:40:03+00:00",
        "ServiceName": "ecr",
        "Region": "ap-south-1"
    }
}
```

→ Two findings. `gitlab-ci` has a key more than two and a half years old that is used every day:
replace it with OIDC (two topics on). `old-backup` has not been used since January 2023: deactivate
it now, delete it after a quiet week. (If `generate-credential-report` was just triggered for the
first time, wait a few seconds before fetching.)

**Hands-on lab (sandbox account only)**

**Step 1 — Build a review.** Generate the report, and for every user write one line: owner, purpose,
still needed (yes/no), action. That table is what an access review looks like.

**Step 2 — Break it on purpose.** In the sandbox, deactivate a key that a small test script uses
(`aws iam update-access-key --user-name lab-script --access-key-id AKIA... --status Inactive`) and run
the script:

```
An error occurred (InvalidClientTokenId) when calling the GetCallerIdentity operation: The security token included in the request is invalid.
```

→ This is how an unknown consumer announces itself after you deactivate a key.

**Step 3 — Fix it.** Move the script to a role it can assume (or run it where an instance or task
role exists), then delete the key. Record the review result with the date.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Deactivated key still needed | `InvalidClientTokenId` in some job | reactivate, find the consumer, migrate it | this topic |
| Key leaked | GuardDuty or AWS abuse notice; unknown API calls | deactivate first, then investigate | section 13 |
| Unused permissions pile up | roles with services never called | Access Analyzer unused-access findings | [Learn: Cloud & AWS](36-learn-cloud-aws.md) section 2 |
| Report shows no MFA for a human | `mfa_active false` with `password_enabled true` | enforce MFA or move the person to Identity Center | this topic |

**Why it matters for troubleshooting.** `InvalidClientTokenId` means the key itself is wrong,
inactive or deleted; `AccessDenied` means the key works but the policy refuses. Different problems,
different owners.

**Next step:** the credentials every EC2 instance can hand out.

### IMDSv2 and instance roles

**Level:** [L3 · Senior]

**Concept.** An EC2 instance with a role gets temporary credentials from the instance metadata
service at `169.254.169.254`. With the old **IMDSv1**, a plain GET returns them, so a server-side
request forgery (SSRF) bug in a web application, which makes the server fetch a URL an attacker
chooses, can expose the role's credentials; this is how the Capital One breach in 2019 unfolded.
**IMDSv2** requires a session token obtained with a `PUT` request and a special header first, which
typical SSRF bugs cannot send, and its **hop limit** stops the token response from travelling
further than you allow. With a hop limit of 1, containers on the instance (one extra network hop
behind the Docker bridge) cannot obtain tokens at all; with 2, they can.

**Key terms**

| Term | Meaning |
|---|---|
| IMDS | instance metadata service at 169.254.169.254 |
| `HttpTokens: required` | IMDSv2 only; v1 requests get `401` |
| Hop limit | IP TTL of the token response: 1 = the instance only, 2 = also containers behind a bridge |
| `MetadataNoToken` | CloudWatch metric counting IMDSv1 calls; check it before enforcing |
| Instance profile | the container for the role an instance uses |

**See it on a real system**

```bash
aws ec2 describe-instances --query 'Reservations[].Instances[].[InstanceId, MetadataOptions.HttpTokens, MetadataOptions.HttpPutResponseHopLimit]' --output text
# on the instance itself:
curl -s -o /dev/null -w '%{http_code}\n' http://169.254.169.254/latest/meta-data/
TOKEN=$(curl -s -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 300')
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/info | jq -r .InstanceProfileArn
```

```
i-0abc123def4567890	required	1
i-0fed987cba6543210	optional	1
401
arn:aws:iam::123456789012:instance-profile/shop-web
```

→ The first instance enforces IMDSv2: the plain GET gets `401`, the token flow works. The second
still accepts IMDSv1: that is the finding.

**Hands-on lab (sandbox account only)**

**Step 1 — Check, then enforce.** Look at the second instance's `MetadataNoToken` metric in
CloudWatch for the last two weeks. If it is zero, enforce:

```bash
aws ec2 modify-instance-metadata-options --instance-id i-0fed987cba6543210 \
  --http-tokens required --http-put-response-hop-limit 1
```

If it is not zero, find and upgrade the old SDK or agent first; enforcing would break it.

**Step 2 — Break it.** On an enforced instance with hop limit 1, run a container that uses the AWS
SDK with the instance role (`docker run --rm amazon/aws-cli:VERSION sts get-caller-identity`). It
fails with `Unable to locate credentials`: the token response cannot reach the container.

**Step 3 — Fix it deliberately.** Choose. Hop limit 2 lets every container on the instance use the
instance role, so all containers share one identity. Better, give the workload its own identity: an
ECS task role, or EKS Pod Identity or IRSA on Kubernetes, and keep hop limit 1. Then set the
account-level default so new instances start correct:
`aws ec2 modify-instance-metadata-defaults --http-tokens required --http-put-response-hop-limit 1`.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Old SDK after enforcement | app logs credential errors after the change | `MetadataNoToken` metric before, SDK version | this topic |
| Containers lose credentials | `Unable to locate credentials` inside containers only | hop limit in `describe-instances` | this topic |
| Instance launched with v1 | `optional` in the audit query | account defaults, launch templates | this topic |
| Role credentials used elsewhere | GuardDuty `InstanceCredentialExfiltration` finding | last topic of this area | section 13 |

**Why it matters for troubleshooting.** "Works on the instance, fails in the container" with AWS
credentials is almost always the hop limit, and `describe-instances` shows it in one line.

**Next step:** remove the last long-lived key, the one in GitLab.

### GitLab OIDC to AWS

**Level:** [L3 · Senior]

**Concept.** Instead of storing an AWS access key in GitLab, a job asks GitLab for a signed
**OIDC ID token** (`id_tokens:`), and AWS STS exchanges it for temporary credentials of a role whose
**trust policy** names exactly which project and branch may assume it. Nothing long-lived exists to
leak. The flow needs AWS to fetch GitLab's discovery document
(`/.well-known/openid-configuration`) and signing keys (`/oauth/discovery/keys`) over the internet
with a certificate it can validate. An internal-only GitLab behind your private CA cannot do this
directly: you either publish those two read-only paths through the edge (they contain only public
keys; agree it with your security owner), or keep a narrowly scoped key and rotate it (previous topic).

Trust policy for the role `gitlab-shop-deploy` (only `main` of `shop/api`):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/gitlab.example.com" },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "gitlab.example.com:aud": "https://gitlab.example.com",
          "gitlab.example.com:sub": "project_path:shop/api:ref_type:branch:ref:main"
        }
      }
    }
  ]
}
```

The job, using the AWS CLI's built-in web-identity support:

```yaml
deploy-aws:
  image:
    name: amazon/aws-cli:VERSION
    entrypoint: [""]
  id_tokens:
    GITLAB_OIDC_TOKEN:
      aud: https://gitlab.example.com
  variables:
    AWS_ROLE_ARN: arn:aws:iam::123456789012:role/gitlab-shop-deploy
    AWS_ROLE_SESSION_NAME: "GitLabRunner-${CI_PROJECT_ID}-${CI_PIPELINE_ID}"
    AWS_WEB_IDENTITY_TOKEN_FILE: /tmp/web-identity-token
    AWS_DEFAULT_REGION: ap-south-1
  script:
    - echo "$GITLAB_OIDC_TOKEN" > "$AWS_WEB_IDENTITY_TOKEN_FILE"
    - aws sts get-caller-identity
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

**Key terms**

| Term | Meaning |
|---|---|
| `id_tokens` | GitLab keyword that issues a signed JWT to the job, with the audience you name |
| `sub` claim | identifies project, ref type and ref: `project_path:GROUP/PROJECT:ref_type:branch:ref:main` |
| OIDC provider (IAM) | IAM's record of an external identity provider it trusts |
| `AssumeRoleWithWebIdentity` | the STS call that trades the JWT for temporary credentials |

**See it on a real system** (creating the provider once, then the job's output):

```bash
# current IAM fetches the certificate thumbprint itself; older CLI versions need --thumbprint-list
aws iam create-open-id-connect-provider --url https://gitlab.example.com --client-id-list https://gitlab.example.com
```

```json
{
    "UserId": "AROA3XFRBF23EXAMPLE:GitLabRunner-42-4812",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/gitlab-shop-deploy/GitLabRunner-42-4812"
}
```

→ The job runs as the role, with a session name that names the project and pipeline, so CloudTrail
shows exactly which pipeline did what.

**Hands-on lab (sandbox account, GitLab reachable by AWS)**

**Step 1 — Build** the provider, the role with the trust policy above and a minimal permissions
policy, and the job. Run it on `main`.

**Step 2 — Break it.** Remove the `rules:` and run the job from a feature branch:

```
An error occurred (AccessDenied) when calling the AssumeRoleWithWebIdentity operation: Not authorized to perform sts:AssumeRoleWithWebIdentity
```

→ The `sub` claim says `ref:feature/x`, which the trust policy does not allow. That refusal is the
whole point: a merge request from any branch cannot deploy to production.

**Step 3 — Fix and finish.** Keep feature branches on a separate staging role if they need AWS at
all. Then delete the old `gitlab-ci` access key from the previous topic, after deactivating it for a
week.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Branch or project not in `sub` condition | `Not authorized to perform sts:AssumeRoleWithWebIdentity` | decode the token's claims in a debug job (never print the token itself) | this topic |
| Audience mismatch | `Incorrect token audience` | `aud` in `id_tokens` vs the provider's client ID | this topic |
| AWS cannot reach GitLab | `Couldn't retrieve verification key from your identity provider` | can the internet reach `/oauth/discovery/keys`? | this topic |
| Session too short | job fails halfway with `ExpiredToken` | role's maximum session duration | this topic |

**Why it matters for troubleshooting.** OIDC errors look alike but name their cause precisely:
audience, subject or key retrieval. Read the message, then compare the token's claims with the
trust policy line by line.

**Next step:** see what happens in the account.

### CloudTrail and GuardDuty

**Level:** [L3 · Senior] to set up, [L4 · Lead/SRE] to run

**Concept.** **CloudTrail** records API calls: management events by default, data events (such as
S3 object reads) when you pay for them. Without a trail you only get 90 days of management events in
the console's event history. A good setup is a multi-region (or organization) trail into a bucket in
a separate log-archive account, with log file validation on, so someone who compromises a workload
account cannot quietly delete the evidence. **GuardDuty** analyses CloudTrail, VPC Flow Logs and DNS
logs (plus optional S3, EKS and runtime sources) and raises **findings**. Severity 7 and above (High
and Critical) should reach a human within minutes; route findings through EventBridge to email or
chat. [Learn: Cloud & AWS](36-learn-cloud-aws.md) covers CloudTrail and Config in depth; this topic
is the security use.

**Key terms**

| Term | Meaning |
|---|---|
| Management vs data events | control-plane calls (CreateUser) vs object-level calls (GetObject) |
| Log file validation | signed digest files that prove trail logs were not modified |
| Finding type | `ThreatPurpose:ResourceType/ThreatName`, e.g. `UnauthorizedAccess:EC2/SSHBruteForce` |
| EventBridge rule | routes matching events (findings) to targets such as SNS |

**See it on a real system**

```bash
aws cloudtrail describe-trails --query 'trailList[].{Name:Name,MultiRegion:IsMultiRegionTrail,Validation:LogFileValidationEnabled,Bucket:S3BucketName}'
aws cloudtrail get-trail-status --name org-trail --query '{Logging:IsLogging,LastDelivery:LatestDeliveryTime}'
DET=$(aws guardduty list-detectors --query 'DetectorIds[0]' --output text)
aws guardduty list-findings --detector-id "$DET" \
  --finding-criteria '{"Criterion":{"severity":{"Gte":7}}}' --query 'FindingIds' --output text \
  | xargs -r aws guardduty get-findings --detector-id "$DET" \
      --query 'Findings[].{Type:Type,Sev:Severity,Res:Resource.ResourceType,Updated:UpdatedAt}' --finding-ids
```

```json
[
    {
        "Name": "org-trail",
        "MultiRegion": true,
        "Validation": true,
        "Bucket": "log-archive-cloudtrail-123456789012"
    }
]
{
    "Logging": true,
    "LastDelivery": "2026-10-03T10:41:07.512000+00:00"
}
[
    {
        "Type": "UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration.OutsideAWS",
        "Sev": 8.0,
        "Res": "AccessKey",
        "Updated": "2026-10-03T09:14:52.118Z"
    }
]
```

→ The trail is healthy. The finding says temporary credentials that belong to an EC2 instance role
were used from outside AWS: the role's credentials have left the instance. That is an incident, not a
ticket; go to section 13 and to the cloud incident topic in
[Learn: Cloud & AWS](36-learn-cloud-aws.md) section 13.

**Hands-on lab (sandbox account only)**

**Step 1 — Build.** Enable GuardDuty in the sandbox region, create sample findings and route them:

```bash
aws guardduty create-sample-findings --detector-id "$DET" \
  --finding-types 'UnauthorizedAccess:IAMUser/InstanceCredentialExfiltration.OutsideAWS'   # a High-severity type
aws events put-rule --name guardduty-high \
  --event-pattern '{"source":["aws.guardduty"],"detail-type":["GuardDuty Finding"],"detail":{"severity":[{"numeric":[">=",7]}]}}'
```

Add an SNS topic with your email as the rule's target (`aws events put-targets`), and confirm a
high-severity sample finding arrives.

**Step 2 — Break it.** Stop the sandbox trail: `aws cloudtrail stop-logging --name lab-trail`.
Within minutes GuardDuty raises `Stealth:IAMUser/CloudTrailLoggingDisabled`, because turning off
logging is what an intruder does early.

**Step 3 — Fix it.** `aws cloudtrail start-logging --name lab-trail`, archive the sample findings,
and write the one-line runbook entry for each finding type you route: who is paged and which section
of the incident runbook they open.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Trail stopped or misconfigured | gaps in logs, `IsLogging: false` | `aws cloudtrail get-trail-status` | this topic |
| Findings nobody sees | findings pile up unread | EventBridge rule and target | this topic |
| Event not in history | data events were never enabled | trail event selectors | [Learn: Cloud & AWS](36-learn-cloud-aws.md) section 9 |
| High-severity credential finding | compromised credentials | contain first: section 13 | section 13 |

**Why it matters for troubleshooting.** CloudTrail answers "who changed this?" for every AWS outage
caused by a change, which is most of them. The same trail is your evidence in a security incident.

**Next step:** turn the stream of CVEs into a manageable process.

---

## 11. Vulnerability and patch management

> 📚 **Study path:** 1) Note: the *Automatic security updates* topic in section 2 and [Packages](11-packages.md), for the apt mechanics this area builds on · 2) KodeKloud: *Fundamentals of SRE* — [Change Management for Reliability](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page), because a patch window is a change ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) After the CKA: *Certified Kubernetes Security Specialist (CKS)* — Supply Chain Security (Trivy) and Cluster Hardening (upgrades) ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · 4) Reading: [FIRST EPSS](https://www.first.org/epss/), the [CISA KEV catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog), [CVSS](https://www.first.org/cvss/) and the [Ubuntu CVE tracker](https://ubuntu.com/security/cves) · 5) Practice: the triage lab on sec-scan, then the patch-window lab on sec-target (snapshot first).

A scanner pointed at an ordinary Dokploy host and its images produces hundreds of findings. Fixing
all of them today is impossible, and patching blindly breaks production: in November 2025 a routine
apt upgrade to Docker Engine 29 made every Traefik route disappear on hosts that still ran an old
Traefik. Fixing nothing is worse, because most breaches use vulnerabilities that had a fix for
months. This area turns the stream into a process with five parts: know what you run, triage by real
risk, patch in windows, rebuild images on a cadence, and record every exception with an owner and an
expiry date.

```
 inventory ──► scan ──► triage: CVSS + EPSS + KEV + exposure ──► P1: emergency change (days)
 (hosts, images,           │                                     P2/P3: patch window or rebuild
  platform versions)       └─► no fix yet / not reachable ──────► exceptions register (expiry)
                                                                        │
       verify: rescan, probes, running digests ◄────────────────────────┘ re-decide on expiry
```

**Field notes: what engineers actually ask**

| What people post | What is usually going on | Topic here | Search |
|---|---|---|---|
| "The PCI or Nessus scan says OpenSSH on Ubuntu is vulnerable, but apt says it is up to date" | Ubuntu backported the fix; the upstream version number never changes | Backports and false positives | [Server Fault](https://serverfault.com/search?q=ubuntu+backport+vulnerability+scan+openssh) |
| "Trivy shows 300 CVEs in my image, where do I even start?" | no triage: most findings have no fix or are not reachable | CVE triage with CVSS, EPSS and KEV | [Trivy discussions](https://github.com/aquasecurity/trivy/discussions?discussions_q=prioritize+vulnerabilities) |
| "After apt upgrade every Dokploy site returns 404" | Docker 29 raised its minimum API version; Traefik before v3.6.1 could not talk to it | Patch windows and reboots | [Docker forum](https://forums.docker.com/t/docker-29-increased-minimum-api-version-breaks-traefik-reverse-proxy/150384), [Dokploy #4123](https://github.com/Dokploy/dokploy/issues/4123) |
| "Do I really have to reboot after unattended-upgrades?" | kernel and libc fixes are not active until a reboot or a service restart | Patch windows and reboots | [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=unattended-upgrades+reboot&restrict_sr=1) |
| "I rebuilt the image and the CVE is still there" | cached layers, or a digest-pinned base that never moved | Image rebuild cadence | [Server Fault](https://serverfault.com/search?q=docker+rebuild+image+security+updates) |
| "Can Livepatch replace reboots?" | no; it buys time for a subset of kernel CVEs | Kernel live patching | [Reddit r/Ubuntu](https://www.reddit.com/r/Ubuntu/search/?q=livepatch+reboot&restrict_sr=1) |

### Inventory and support status

**Level:** [L2 · Mid] to build, [L3 · Senior] to keep current

**Concept.** You cannot patch what you do not know you run. Before any scanner, list for every
host: the OS release and whether it still receives security updates, the kernel that is actually
running, packages from third-party repositories (Docker, GitLab, Wazuh, Grafana), which
unattended-upgrades ignores unless you add their origins, the containers that are running and the
image digests behind them, and the **platform components** that update differently from apt:
Dokploy and its `dokploy-traefik` container, Harbor, GitLab and its runners, the Wazuh manager and
the kubeadm cluster.

Each of them has a **support window**. Inside it, "patch" means a package or image update in a
window. Outside it there are no fixes at all, and "patch" turns into "upgrade to a supported
version", which is a project with its own risk. Two examples from October 2026: kubernetes.io lists
1.35 to 1.37 as the maintained minor versions (three at a time, about a year of patches each) and
shows 1.34's end of life as 27 October 2026, so a cluster still on 1.34, the version this module's
sample outputs use, leaves patch support this month; and Traefik's release support table shows v3.6
(security support ended August 2026) and v2.11 (ended September 2026) out of security support.
Neither shows up as a
CVE until the first unfixed vulnerability is published.

Ubuntu itself has two layers. Packages from **main** get five years of standard security updates
per LTS release (22.04 until 2027, 24.04 until 2029). Packages from **universe**, which includes
tools you install such as fail2ban and lynis, are community-maintained and receive security fixes
through Ubuntu Pro's ESM Apps. `pro security-status` shows the split on any host.

**Key terms**

| Term | Meaning |
|---|---|
| Support window / end of life | the period a vendor publishes security fixes for a version; after end of life there are none |
| Standard security maintenance | Ubuntu's five years of fixes for main packages on an LTS release |
| ESM Infra / ESM Apps | Ubuntu Pro coverage: extra years for main, and security fixes for universe |
| Running digest | the image digest a container actually runs, which may differ from what the tag points to today |
| Platform component | software you run that apt does not update: Dokploy, Traefik, Harbor, GitLab, Kubernetes |

**See it on a real system**

```bash
lsb_release -ds; uname -r
pro security-status | sed -n '1,4p'
apt-cache policy | grep -E '^ +[0-9]+ https?://' | awk '{print $2, $3}' | sort -u
docker service inspect --format '{{.Spec.Name}} {{.Spec.TaskTemplate.ContainerSpec.Image}}' $(docker service ls -q)
docker inspect --format '{{.Name}} {{.Config.Image}}' dokploy-traefik
kubectl version | grep Server
```

```
Ubuntu 24.04.3 LTS
6.8.0-79-generic
1342 packages installed:
     1201 packages from Ubuntu Main/Restricted repository
     97 packages from Ubuntu Universe/Multiverse repository
     44 packages from third parties
http://archive.ubuntu.com/ubuntu noble-updates/main
http://security.ubuntu.com/ubuntu noble-security/main
https://download.docker.com/linux/ubuntu noble/stable
https://packages.wazuh.com/4.x/apt/ stable/main
dokploy dokploy/dokploy:v0.28.8@sha256:3c9a5e7b1d2f4a6c8e0b2d4f6a8c0e2b4d6f8a0c2e4b6d8f0a2c4e6b8d0f2a4c
shop-api harbor.example.com/shop/api:1.8.1@sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c
/dokploy-traefik traefik:v3.6.2
Server Version: v1.34.3
```

→ 97 universe packages are covered only if ESM Apps is enabled; the Docker and Wazuh repositories
are third-party, so unattended-upgrades leaves them alone (deliberately, for Docker). Swarm pinned
each service to a digest at deploy time, which is what you will scan later. Two items are at or
past the end of support: Traefik's v3.6 branch (already out) and the 1.34 cluster (out on
27 October 2026). Both become planned upgrades with a change request, not patches.

**Hands-on lab (test VMs only)**

**Step 1 — Build the inventory file.** One file in your ops repository, one entry per component,
reviewed in every patch window:

```yaml
# inventory/platform-versions.yaml
- component: ubuntu
  hosts: [sec-target, sec-scan, sec-reg]
  version: "24.04"
  support: "standard security maintenance until 2029; longer with Ubuntu Pro"
  update_path: unattended-upgrades daily, reboot in the monthly window
- component: docker-engine
  hosts: [sec-target]
  version: "29.1.x"
  update_path: "held; upgraded in the monthly window after a staging check"
- component: traefik (dokploy-traefik)
  hosts: [sec-target]
  version: v3.6.2
  support: "branch out of security support, see the Traefik release table"
  next_action: "move to the current v3 branch, change CR-2026-044"
- component: kubernetes (kubeadm)
  hosts: [cp1, w1, w2]
  version: v1.34.3
  support: "patch support ends 2026-10-27, see kubernetes.io/releases"
  next_action: "upgrade one minor at a time: 1.35, then 1.36"
```

**Step 2 — Break it: let something drift.** On sec-target, run an image tag that is years old as a
"temporary test" (`docker run -d --name tmp-redis redis:6.2`) and forget about it. Run the
inventory commands again: the container is not in the file and nobody owns it. Forgotten containers
are how the oldest, most vulnerable software on a host gets there.

**Step 3 — Fix it.** Remove the container, or add it to the inventory with an owner. Then automate
the comparison: a weekly job that lists running images (`docker service inspect` and `docker ps`
as above, or `kubectl get pods -A -o jsonpath=...` on Kubernetes) and diffs them against the file.
Anything running that nobody owns is a finding, not a curiosity.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Component past end of life | no new fixes; scanners show "will_not_fix" or nothing at all | vendor release table, `kubectl version` | this topic |
| Third-party repository never patched | Docker or Wazuh far behind while Ubuntu packages are current | `apt list --upgradable` | Patch windows and reboots |
| Universe packages without coverage | `pro security-status` counts universe packages, the tracker says vulnerable | `pro security-status` | Backports and false positives |
| Forgotten container | running image months old, owner unknown | `docker ps --format '{{.Names}} {{.Image}} {{.RunningFor}}'` | this topic |

**Why it matters for troubleshooting.** In an incident, the first question about any new
vulnerability is "do we run that, and where?". An inventory answers in a minute what an unprepared
team answers in a day of SSH sessions.

**Next step:** decide which findings matter first.

### CVE triage with CVSS, EPSS and KEV

**Level:** [L2 · Mid]

**Concept.** Four public signals, each answering a different question:

- **CVE** is only an identifier for one vulnerability. It says nothing about urgency.
- **CVSS** answers "how bad is it in the worst case?": a 0–10 base score computed from a vector such as `AV:N/AC:L/PR:N/UI:N` (network, low complexity, no privileges, no user interaction). Ratings: Low 0.1–3.9, Medium 4.0–6.9, High 7.0–8.9, Critical 9.0–10.0. CVSS 4.0 was published in November 2023, so you will see 3.1 and 4.0 scores side by side for years.
- **EPSS**, from FIRST, answers "how likely is it to be exploited in the wild in the next 30 days?": a probability from 0 to 1 plus a percentile, recalculated daily from observed exploitation.
- **KEV**, CISA's Known Exploited Vulnerabilities catalog, answers "is it being exploited right now?". An entry means there is reliable evidence of exploitation in the wild. US federal agencies must fix KEV entries by a due date; for everyone else it is the strongest "fix this first" signal available.

None of them knows your environment. The fifth signal is yours: is the vulnerable component **exposed**
(internet-facing or reachable from untrusted networks), is the vulnerable code **actually used**,
and how **critical** is the asset. For OS packages, the distribution's own
priority (Ubuntu rates CVEs negligible, low, medium, high or critical for its builds) often beats
the generic CVSS score, which is why Trivy prefers vendor severities (section 6). And since 2024 the
NVD has had a large enrichment backlog, so many new CVEs arrive without an NVD score at all: use the
distribution's rating or the advisory of the project that published the fix.

An example policy for a small platform team (tune the thresholds, then write the result down):

| Bucket | Rule | Target | Typical action |
|---|---|---|---|
| P1 emergency | in KEV, or EPSS 0.1 or higher, **and** a fix exists **and** the asset is exposed | 72 hours, as an emergency change | patch or rebuild now; mitigate first if the fix needs testing |
| P2 high | CVSS 7.0 or more (or vendor high/critical), fix exists, reachable | 14 days | next weekly window or image rebuild |
| P3 normal | any other finding with a fix | 30 days | monthly window, scheduled rebuild |
| P4 track | no fix yet, or the vulnerable code is provably not reachable | review monthly | exceptions register with an expiry (last topic of this area) |

Only a small fraction of all CVEs ever reach an EPSS of 0.1, so the P1 bucket stays short enough to
act on within days.

**Key terms**

| Term | Meaning |
|---|---|
| Vector string | the CVSS inputs, e.g. `CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H` |
| EPSS percentile | share of all scored CVEs with an equal or lower score; 0.98 means "higher than 98% of CVEs" |
| KEV `dateAdded` / `dueDate` | when CISA listed it, and the federal remediation deadline |
| Fixable | a patched version exists in your distribution or ecosystem (`Status: fixed` in Trivy) |
| Reachability | whether the vulnerable function can be called in your deployment |

**See it on a real system** (sec-scan; the CVE IDs and scores are illustrative). First the fixable
and unfixable HIGH and CRITICAL findings from a Trivy JSON report:

```bash
trivy image --quiet --format json --output scan.json harbor.example.com/shop/gateway:2.4.0   # a Go service on ubuntu:24.04
jq -r '.Results[].Vulnerabilities[]? | select(.Severity=="HIGH" or .Severity=="CRITICAL")
  | [.VulnerabilityID, .PkgName, .InstalledVersion, (.FixedVersion // "-"), .Status, .Severity] | @tsv' scan.json | sort -u
```

```
CVE-2025-44444	libc6	2.39-0ubuntu8.5	-	affected	HIGH
CVE-2026-11111	libexpat1	2.6.1-2ubuntu0.2	2.6.1-2ubuntu0.3	fixed	HIGH
CVE-2026-22222	libssl3t64	3.0.13-0ubuntu3.5	3.0.13-0ubuntu3.6	fixed	CRITICAL
CVE-2026-33333	golang.org/x/net	v0.36.0	0.38.0	fixed	HIGH
```

Then enrich them with EPSS (FIRST's public API) and KEV (CISA's JSON feed):

```bash
curl -s "https://api.first.org/data/v1/epss?cve=CVE-2025-44444,CVE-2026-11111,CVE-2026-22222,CVE-2026-33333" \
  | jq -r '.data[] | [.cve, .epss, .percentile] | @tsv'
curl -s -o kev.json https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json
jq -r '.vulnerabilities[] | select(.cveID | IN("CVE-2025-44444","CVE-2026-11111","CVE-2026-22222","CVE-2026-33333"))
  | [.cveID, .dateAdded, .dueDate, .knownRansomwareCampaignUse] | @tsv' kev.json
```

```
CVE-2025-44444	0.000310000	0.081000000
CVE-2026-11111	0.000520000	0.190000000
CVE-2026-22222	0.312000000	0.982000000
CVE-2026-33333	0.004100000	0.712000000
CVE-2026-22222	2026-09-29	2026-10-20	Unknown
```

→ Four findings, four different actions. The OpenSSL library is critical, listed in KEV, has an
EPSS of 0.31 and sits in the internet-facing gateway image: **P1**, rebuild today on the fixed base. The
Go `x/net` module is high with a fix and the service uses its HTTP/2 server code: **P2**, bump the
dependency in the next release. The expat finding has a fix but a low EPSS, and the parser is only
used by a command-line helper: **P3**, the weekly rebuild picks it up. The libc finding has no fix
yet: **P4**, an exceptions-register entry and a monthly re-check. Sorting by CVSS alone would have
put the libc and expat findings level with the one being exploited right now.

**Hands-on lab (sec-scan)**

**Step 1 — Build a triage sheet.** Scan an image you really use (the Traefik and Apache images on
sec-target, or an old tag such as `nginx:1.24`), enrich the HIGH and CRITICAL findings with the
commands above, and write a bucket and a one-line reason next to each.

**Step 2 — Break it: triage by CVSS only.** Sort the same findings by CVSS score alone and take the
top five as "this week's work". Compare with your bucket list. Typically the CVSS-only list
contains findings with no fix (nothing to do but wait) and misses a lower-scored finding that is in
KEV.

**Step 3 — Fix it: write the policy down and gate on it.** Put the bucket table, thresholds and
targets into your ops repository (`security/vuln-policy.md`). Keep the section 8 CI gate failing on
fixable CRITICAL findings, and add a small step that also fails when any fixable finding appears in
`kev.json`. A gate that matches the written policy is respected; a gate that blocks on noise gets
disabled.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| CVSS-only priorities | backlog never shrinks; exploited bugs wait behind theoretical ones | compare the top 10 with KEV and EPSS | this topic |
| EPSS used alone | an exposed authentication bypass waits because its EPSS is low on day one | exposure and KEV check | this topic |
| No NVD score | severity "UNKNOWN" in reports | the distribution's tracker or the project's advisory | this topic |
| KEV feed or EPSS API unreachable from CI | enrichment step fails, pipeline red | mirror `kev.json` daily to an internal web server | section 12 |

**Why it matters for troubleshooting.** When a "critical CVE!" message arrives from management at
6 p.m., the triage questions (fixable? in KEV? exposed? reachable?) turn panic into a decision in
ten minutes, and give you the words to explain it.

**Next step:** check whether a finding is real at all.

### Backports and false positives

**Level:** [L2 · Mid]

**Concept.** Ubuntu, Debian and RHEL fix security bugs by **backporting** the patch into the
version they shipped, without changing the upstream version number. OpenSSH on Ubuntu 22.04 is
"8.9p1" for the whole life of the release; the fix shows in the package revision (for example,
`1:8.9p1-3ubuntu0.10` fixed CVE-2024-6387, "regreSSHion"). Any tool that compares only the **upstream
version**, such as a network scanner reading the SSH banner, a compliance scanner or a
penetration-test report, flags CVEs that are already fixed. Distribution-aware tools (Trivy for OS
packages, Wazuh's vulnerability detection, `pro fix`) compare against the distribution's own
advisories and get it right.

The opposite failure is quieter. Anything installed **outside a package manager** (a binary
downloaded with `curl` in a Dockerfile, a vendored library, a tarball unpacked in `/opt`) has no
package record, so package-based scanning cannot see it at all. Go and Rust binaries are partly
visible because they embed module information; plain C binaries are not.

**Key terms**

| Term | Meaning |
|---|---|
| Backport | applying an upstream fix to an older version without changing its upstream version number |
| Package revision | the distribution part of the version, e.g. `-3ubuntu0.10` |
| USN | Ubuntu Security Notice: the fixed package versions per release |
| Ubuntu CVE tracker | per-CVE status for every release: fixed, vulnerable, not affected, needs evaluation, deferred |
| False positive / false negative | a reported finding that is not real / a real vulnerability nobody reports |

**See it on a real system** (sec-target on Ubuntu 22.04; your revision may be newer, and `apt
changelog` downloads the changelog, so it needs network access):

```bash
ssh -V
dpkg-query -W -f='${Package} ${Version}\n' openssh-server
apt changelog openssh-server 2>/dev/null | grep -m1 -- '- CVE-2024-6387$'
pro fix CVE-2024-6387
```

```
OpenSSH_8.9p1 Ubuntu-3ubuntu0.13, OpenSSL 3.0.2 15 Mar 2022
openssh-server 1:8.9p1-3ubuntu0.13
    - CVE-2024-6387
CVE-2024-6387: OpenSSH vulnerability
 - https://ubuntu.com/security/CVE-2024-6387

1 affected source package is installed: openssh
(1/1) openssh:
A fix is available in Ubuntu standard updates.
The update is already installed.

✔ CVE-2024-6387 is resolved.
```

→ The banner and the upstream version say 8.9p1, which a version-matching scanner reports as
vulnerable to CVE-2024-6387. The package revision, the changelog entry and `pro fix` all show that
the fix is installed. That output, saved with the date, is the evidence that closes the finding for
an auditor or a customer's scan report (section 14).

**Hands-on lab (test VMs only)**

**Step 1 — Build: answer a scan report.** On sec-scan, run `nmap -sV -p 22,80,443 192.168.56.21`
against your own lab VM and note the versions it reports. For each, decide whether a version-only
scanner would flag it, then prove the real status on sec-target with the commands above. Write one
line per finding: "not affected", "fixed in revision X", or "vulnerable, fixing in window Y".

**Step 2 — Break it: hide a binary from the scanner.** Build a test image that downloads a release
tarball of some C tool into `/usr/local/bin` with `curl` (any old version will do), then scan it
with Trivy. The OS packages are listed; the tool is not, however old it is.

**Step 3 — Fix it.** Install the tool from the distribution's packages or a language package
manager, so the scanner can see it. If you must download a binary, pin it with a checksum, list it
in a "manual components" file next to the Dockerfile, and check that list against advisories in
every patch window. Add a review rule for Dockerfiles: no `curl` into the final image without an
entry in that list.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Version-only scanner | report lists CVEs fixed months ago | `dpkg-query -W PACKAGE`, `pro fix CVE-ID` | this topic |
| Status "needs evaluation" or "deferred" | no fix from Ubuntu yet | the Ubuntu CVE tracker page | Exceptions register |
| Universe package without ESM | tracker shows a fix only for Pro subscribers | `pro security-status` | Inventory and support status |
| Binary outside the package manager | scanner clean, binary old | `syft scan IMAGE`, Dockerfile review | section 8 |

**Why it matters for troubleshooting.** Half of security triage is proving a finding is not real,
and the other half is noticing what the scanner cannot see. Both start with one question: where did
this version come from?

**Next step:** apply the real fixes without breaking production.

### Patch windows and reboots

**Level:** [L1 · Junior] to run, [L2 · Mid] to design

**Concept.** Split patching into what installs itself and what waits for a window:

| Installs automatically | Waits for a window (weekly or monthly) | Why the split |
|---|---|---|
| Ubuntu security updates via unattended-upgrades (section 2), with needrestart restarting affected services | kernel reboots; Docker Engine, containerd and runc; Dokploy and its Traefik; Harbor; GitLab and runners; Kubernetes versions; the Wazuh manager | the left column rarely breaks anything; the right column restarts every container or changes behaviour |

A **patch window** is a scheduled change with a fixed runbook: pre-checks, a staging node first,
then one production node, verification, then the rest, with a rollback for each step. P1 findings
use the same runbook out of schedule, as an emergency change.

The Docker 29 case shows why the Docker Engine sits in the right column. Docker Engine 29.0
(November 2025) raised the minimum Docker API version it accepts to 1.44. Traefik releases before
v3.6.1 asked for API 1.24, so after a routine `apt upgrade` the Traefik Docker provider failed,
every label-based route disappeared, and all Dokploy sites returned 404 while their containers kept
running ([Docker forum](https://forums.docker.com/t/docker-29-increased-minimum-api-version-breaks-traefik-reverse-proxy/150384),
[Dokploy #4123](https://github.com/Dokploy/dokploy/issues/4123)). Hosts with the Docker packages
held and a staging node met the problem in a window with a rollback ready, instead of at 06:12 on a
weekday.

**Reboots** are what most teams postpone. A new kernel or libc does nothing until the host reboots
or the services using it restart. Plan reboots by topology, one node at a time, least critical
first, verifying between nodes:

```
 single Dokploy host  → announce; reboot in the window; verify every site (all apps go down together)
 Docker Swarm node    → docker node update --availability drain NODE → patch, reboot → --availability active
 Kubernetes node      → kubectl drain NODE --ignore-daemonsets --delete-emptydir-data → patch, reboot → kubectl uncordon NODE
```

**Key terms**

| Term | Meaning |
|---|---|
| Patch window | an agreed recurring time for planned patching, run as a change |
| `apt-mark hold` | stops apt from upgrading a package for everyone, humans included; u-u's `Package-Blacklist` only stops u-u |
| needrestart | lists services still using replaced libraries, and whether the running kernel is outdated |
| Drain / cordon | move workloads off a node / stop new ones landing on it |
| Emergency change | a P1 patch applied out of schedule, with the same runbook and a short approval |

**See it on a real system**

```bash
uname -r; cat /var/run/reboot-required.pkgs 2>/dev/null
sudo needrestart -b
apt-mark showhold
zgrep -h -A5 'Start-Date' /var/log/apt/history.log* | grep -E '^(Start-Date|Install|Upgrade)' | tail -n 3
```

```
6.8.0-79-generic
linux-image-6.8.0-85-generic
libc6
NEEDRESTART-VER: 3.6
NEEDRESTART-KCUR: 6.8.0-79-generic
NEEDRESTART-KEXP: 6.8.0-85-generic
NEEDRESTART-KSTA: 3
NEEDRESTART-SVC: containerd.service
NEEDRESTART-SVC: ssh.service
NEEDRESTART-SVC: systemd-logind.service
containerd.io
docker-ce
docker-ce-cli
Start-Date: 2026-10-02  06:12:31
Install: linux-image-6.8.0-85-generic:amd64 (6.8.0-85.85, automatic), linux-modules-6.8.0-85-generic:amd64 (6.8.0-85.85, automatic)
Upgrade: linux-image-generic:amd64 (6.8.0-79.79, 6.8.0-85.85), libc6:amd64 (2.39-0ubuntu8.5, 2.39-0ubuntu8.6)
```

→ `KSTA: 3` means a newer kernel is installed but not running (1 would mean current, 2 an
ABI-compatible update pending). libc6 was updated on 2 October and three services still map the
old library. The Docker packages are held. Restart those services in the window, not in the middle
of the day: containerd is on the list, and restarting the container runtime on a Swarm node is a
planned action. The simplest plan is a reboot, which also activates the new kernel.

**Hands-on lab (sec-target, snapshot first)**

**Step 1 — Pre-checks.** Record the starting state, so you can tell "the patch broke it" from "it
was already broken":

```bash
for h in shop.example.com api.example.com; do curl -s -o /dev/null -w "$h %{http_code}\n" "https://$h/healthz"; done
docker version --format 'server {{.Server.Version}} api {{.Server.APIVersion}} min {{.Server.MinAPIVersion}}'
docker inspect --format '{{.Config.Image}}' dokploy-traefik
```

```
shop.example.com 200
api.example.com 200
server 28.5.2 api 1.51 min 1.24
traefik:v3.1.2
```

→ Everything is healthy, and Traefik is v3.1.2, older than v3.6.1. A release-note check before the
window would already say: upgrade Traefik first, then Docker.

**Step 2 — Break it (lab only): upgrade the engine first.** Unhold and upgrade Docker with the old
Traefik still running:

```bash
sudo apt-mark unhold docker-ce docker-ce-cli containerd.io
sudo apt-get install -y --only-upgrade docker-ce docker-ce-cli containerd.io
docker logs --since 5m dokploy-traefik 2>&1 | grep -m1 'too old'
```

```
ERR Provider error, retrying in 26.37s error="Error response from daemon: client version 1.24 is too old. Minimum supported API version is 1.44, please upgrade your client to a newer version" providerName=docker
```

→ Every Docker-label route is gone and the sites return 404, while `docker ps` shows every
container up. This is the November 2025 incident in miniature.

**Step 3 — Fix it, then fix the runbook.** Roll forward: move Traefik to a supported release (with
Dokploy, update Dokploy and confirm the Traefik image really changed, because a Dokploy update does
not always replace the Traefik container), then re-run the probes. If the proxy cannot move today,
roll the engine back and hold it again:

```bash
apt-cache madison docker-ce | head -n 3        # pick the previous version string
sudo apt-get install -y --allow-downgrades docker-ce=5:28.5.2-1~ubuntu.24.04~noble docker-ce-cli=5:28.5.2-1~ubuntu.24.04~noble
sudo apt-mark hold docker-ce docker-ce-cli containerd.io
```

Then add two lines to the runbook: "read the release notes of Docker, Traefik and Dokploy for
minimum versions and API changes", and "staging node patched one week before production".

**Step 4 — Reboot and verify.** `sudo reboot` in the window; afterwards `uname -r` shows the new
kernel, `sudo needrestart -b` shows `NEEDRESTART-KSTA: 1`, the probes return 200, and `docker ps`
shows every container back. Write the five-line note.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Kernel installed, never rebooted | scanners keep flagging the kernel CVE | `uname -r` vs `/var/run/reboot-required.pkgs` | this topic |
| Services still on replaced libraries | old OpenSSL still loaded after the upgrade | `sudo needrestart -b` | this topic |
| Engine upgrade breaks the proxy | all routes 404 after a Docker upgrade | `docker logs dokploy-traefik 2>&1 | grep 'too old'` | [Containers playbook](26-playbook-containers-k8s.md) |
| Host does not come back after the reboot | no ping or SSH after the window | hypervisor console, then `journalctl -b -1 -p err` | [Kernel & system](13-kernel-system.md) |
| Drain hangs | `kubectl drain` waits forever | `kubectl get pdb -A` (PodDisruptionBudgets) | [Learn Kubernetes](31-learn-kubernetes.md) |
| Windows skipped "just this month" | P2 targets missed, backlog grows | the patch SLA report | section 14 |

**Why it matters for troubleshooting.** Patch windows are the most common planned cause of
unplanned outages. A runbook with pre-checks and probes turns "something broke after patching" into
"step 2 broke the proxy; rolled back in four minutes".

**Next step:** the kernel fixes you cannot wait a month for.

### Kernel live patching

**Level:** [L3 · Senior] (overview)

**Concept.** Live patching replaces vulnerable kernel functions in memory, so a fix takes effect
without a reboot. On Ubuntu this is **Canonical Livepatch**, part of Ubuntu Pro, which is free for
up to five machines for personal use. It targets kernel vulnerabilities rated high and critical,
with a focus on privilege escalation and remote code execution, and only on supported kernels.
Canonical's own documentation states plainly that Livepatch is **not a replacement for rebooting**:
the fix lives in memory until you boot a fixed kernel, coverage is limited to selected CVEs, and long
uptimes accumulate other problems. Other distributions have the same idea under other names: kpatch
on RHEL, Ksplice on Oracle Linux, live patching on SUSE, and kernel live patching on Amazon Linux
(see its user guide).

Where it fits the policy: Livepatch moves a P1 kernel CVE from "emergency reboot of the single
Dokploy host tonight" to "covered now, reboot in the normal window". It does nothing for libc,
OpenSSL, the Docker engine, or anything inside containers.

**Key terms**

| Term | Meaning |
|---|---|
| Livepatch module | the kernel module that carries the replacement functions |
| Kernel coverage | whether your kernel flavour and version still receive livepatches |
| `pro enable livepatch` | switches the service on after `sudo pro attach TOKEN` |

**See it on a real system** (output format varies between client versions):

```bash
pro status | grep -E '^(SERVICE|esm|livepatch)'
canonical-livepatch status
```

```
SERVICE          ENTITLED  STATUS       DESCRIPTION
esm-apps         yes       enabled      Expanded Security Maintenance for Applications
esm-infra        yes       enabled      Expanded Security Maintenance for Infrastructure
livepatch        yes       enabled      Canonical Livepatch service
last check: 41 minutes ago
kernel: 6.8.0-79.79-generic
server check-in: succeeded
kernel state: ✓ kernel series 6.8 is covered by Livepatch
patch state: ✓ all applicable livepatch modules inserted
patch version: 131.2
```

→ The running kernel is still 6.8.0-79, but the applicable fixes are in memory. The reboot into
6.8.0-85 still goes into the next window.

**Hands-on lab (personal test VM with a free Pro token)**

**Step 1 — Build.** `sudo pro attach TOKEN`, `sudo pro enable livepatch`, then read
`canonical-livepatch status`.

**Step 2 — Break it.** Snapshot, then boot a kernel outside Livepatch coverage (for example a
mainline test kernel). The status reports the kernel as not covered, and nothing warns you unless
someone looks.

**Step 3 — Fix it.** Boot back into the supported GA or HWE kernel, and add the Livepatch status to
monitoring (a textfile metric or a Wazuh command check), so "not covered" becomes an alert instead
of a surprise.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Kernel not covered | `kernel state` not covered | `canonical-livepatch status` | this topic |
| Check-in failing | `server check-in: failed` behind a proxy or egress firewall | `canonical-livepatch config` (proxy settings) | section 3 |
| Treated as "no reboots ever" | 400 days of uptime; libc and microcode never activated | `uptime`, `sudo needrestart -b` | Patch windows and reboots |

**Why it matters for troubleshooting.** When someone says "Livepatch is on, so we are patched",
`uname -r`, the Livepatch status and `needrestart -b` together show what is actually running.

**Next step:** containers get none of this; they need rebuilding.

### Image rebuild cadence

**Level:** [L2 · Mid] to run, [L3 · Senior] to automate

**Concept.** Nothing patches a running container. Its packages are frozen at build time, so fixes
arrive only by **rebuilding on a fixed base and redeploying**. Three things have to move, and each
one fails silently:

1. **The base image.** Upstream re-publishes tags such as `ubuntu:24.04` or `python:3.12-slim` with fixes. If you pin the base by digest (section 8, which you should), the digest never moves by itself: a bot such as Renovate has to propose the new digest as a merge request.
2. **The build.** A scheduled pipeline must rebuild even when the application code has not changed, and must not reuse a cached `apt-get install` layer from months ago. `--pull` refreshes the base; `--no-cache` refreshes the package layers.
3. **The deployment.** A rebuilt image in Harbor fixes nothing until Dokploy or Kubernetes runs the new digest. Scan what is **running**, not only what is in the registry.

A cadence that works for a small team: a weekly scheduled rebuild of every service, weekly Renovate
digest updates, a daily Harbor "scan all" so new CVEs in old images surface, and an immediate
rebuild for P1 findings.

**Key terms**

| Term | Meaning |
|---|---|
| Scheduled pipeline | a GitLab pipeline started by a schedule; `CI_PIPELINE_SOURCE == "schedule"` |
| Digest bump | changing `FROM image@sha256:...` to the newer digest of the same tag |
| Image age | time since the running image was built: a simple, honest metric |
| Runtime scan | scanning the digests that are running, not the newest tag |

**See it on a real system**

```bash
# what runs, by digest, on the Dokploy host
docker service inspect --format '{{.Spec.Name}} {{.Spec.TaskTemplate.ContainerSpec.Image}}' $(docker service ls -q)
docker image inspect --format '{{.Created}}' harbor.example.com/shop/api:1.8.1
# Harbor's current view of that same digest (rescanned daily with today's database)
curl -s -u "$HARBOR_USER:$HARBOR_PASSWORD" \
  "https://harbor.example.com/api/v2.0/projects/shop/repositories/api/artifacts/sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c?with_scan_overview=true" \
  | jq '.scan_overview[] | {scan_status, summary: .summary.summary}'
```

```
dokploy dokploy/dokploy:v0.28.8@sha256:3c9a5e7b1d2f4a6c8e0b2d4f6a8c0e2b4d6f8a0c2e4b6d8f0a2c4e6b8d0f2a4c
shop-api harbor.example.com/shop/api:1.8.1@sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c
2026-07-14T08:21:37.402Z
{
  "scan_status": "Success",
  "summary": {
    "Critical": 1,
    "High": 6,
    "Medium": 23
  }
}
```

→ The API image running in production was built in July. Harbor's daily rescan of that same digest
now finds one critical and six high findings that did not exist in the vulnerability database when
the image passed the gate. Nothing in the pipeline went red, because nothing ran. That gap is what a
cadence closes.

**Hands-on lab (throwaway GitLab project and sec-reg)**

**Step 1 — Build the cadence.** Add a pipeline schedule (Build → Pipeline schedules, weekly, on the
default branch). In the build job from section 8, force fresh layers for scheduled runs and give
each rebuild a unique tag, because the commit SHA alone repeats when the code has not changed:

```yaml
build:
  stage: build
  script:
    - echo "$HARBOR_ROBOT_TOKEN" | docker login -u "$HARBOR_ROBOT_USER" --password-stdin harbor.example.com
    - CACHE_FLAG=""; if [ "$CI_PIPELINE_SOURCE" = "schedule" ]; then CACHE_FLAG="--no-cache"; fi
    - docker build --pull $CACHE_FLAG -t "$IMAGE:$CI_COMMIT_SHORT_SHA-$CI_PIPELINE_IID" .
    - docker push "$IMAGE:$CI_COMMIT_SHORT_SHA-$CI_PIPELINE_IID" | tee push.log
    - awk '/digest: sha256:/ {print "DIGEST=" $3}' push.log > build.env
  artifacts:
    reports:
      dotenv: build.env
```

Let Renovate propose base-digest bumps once a week (`renovate.json` in the repository):

```json
{
  "extends": ["config:recommended", "docker:pinDigests"],
  "packageRules": [
    {
      "matchDatasources": ["docker"],
      "matchUpdateTypes": ["digest"],
      "schedule": ["before 6am on monday"]
    }
  ]
}
```

**Step 2 — Break it: rebuild without fresh layers.** After an Ubuntu security update, run the build
manually without `--no-cache`. It finishes in seconds, the build log shows `CACHED` for the
`apt-get install` step, and Trivy reports the same fixable finding. Fast and useless.

**Step 3 — Fix it and close the loop.** Run the scheduled variant, confirm the finding is gone from
the new digest, and confirm the deploy job rolled it out (`docker service inspect` or `kubectl get
pods -o jsonpath=...` shows the new digest). Then add an alert for any production image older than
30 days: a weekly script that writes image ages as a node_exporter textfile metric, the same pattern
section 12 uses for Docker socket mounts.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Cached package layers | rebuild takes seconds, findings unchanged | `CACHED` on the `apt-get` step in the build log | this topic |
| Pinned base never bumped | every image carries months-old base packages | `FROM` digest vs upstream; open Renovate merge requests | section 8 |
| Rebuilt but not deployed | registry clean, production vulnerable | running digest vs newest digest | this topic |
| New Harbor policy blocks old images | a node restart or redeploy fails to pull | Harbor "prevent vulnerable images" setting | section 6 |
| Same tag pushed twice | Harbor rejects the push (immutable tag) | Harbor tag immutability rules | section 6 |

**Why it matters for troubleshooting.** "Why does production still have this CVE? We fixed it last
week" is answered by comparing three digests: the one in the merge request, the one in Harbor and
the one running.

**Next step:** record what you decide not to fix.

### Exceptions register

**Level:** [L2 · Mid] to write entries, [L3 · Senior] to own the process

**Concept.** Some findings cannot or should not be fixed now: no fix exists yet, the vulnerable code
is provably not reachable, the fix breaks something critical, or a vendor appliance cannot be
changed. Leaving them in the scanner as permanent red noise trains everyone to ignore red.
Silencing them in `.trivyignore` with no record hides a risk. The middle path is an **exceptions
register**: a reviewed list of risk decisions, each with a reason, a compensating control, an
owner, an approver who owns the risk (not the engineer who wants a green build), and an **expiry
date** that forces a new decision.

The register is the single source of truth. The `.trivyignore.yaml` entries and the Harbor CVE
allowlist from section 6 are derived from it and always carry its ID and an expiry. In ISO 27001
terms this is risk treatment ("retain" or accept the risk) with a record, which is exactly what an
auditor asks to see (section 14).

**Key terms**

| Term | Meaning |
|---|---|
| Risk acceptance | a named owner decides to live with a risk for a period, on the record |
| Compensating control | something that reduces the risk while the fix is missing: non-root, no egress, a WAF rule |
| Expiry | the date the decision lapses and the finding fails the gate again |
| False-positive record | a finding proven not real (backport, not affected), kept with its evidence |

**See it on a real system** — the register, in Git:

```yaml
# security/exceptions.yaml (every change through a merge request approved by the security owner)
- id: EXC-2026-014
  cve: CVE-2025-44444
  asset: harbor.example.com/shop/gateway (base ubuntu:24.04)
  finding: "libc6 HIGH, status affected, no fixed package yet"
  decision: accept-until-fix
  reason: "No fix released by Ubuntu. The affected function is not called by the service (SEC-142)."
  compensating_control: "Runs non-root with a read-only root filesystem; egress only to the database."
  owner: shop-team-lead
  approved_by: security-lead
  created: 2026-10-03
  expires: 2026-12-31
- id: EXC-2026-015
  cve: CVE-2024-6387
  asset: external scan report, web01 port 22
  finding: "Reported by version match on OpenSSH 8.9p1"
  decision: false-positive
  reason: "Fixed by backport in openssh-server 1:8.9p1-3ubuntu0.10 or later; pro fix output attached."
  owner: ops
  approved_by: security-lead
  created: 2026-10-03
  expires: 2027-04-03
```

A small check, run in CI and before every patch window, keeps it honest:

```python
#!/usr/bin/env python3
"""check_exceptions.py: fail on expired or incomplete exceptions, and on ignores without a register ID."""
import datetime
import sys

import yaml

REQUIRED = {"id", "cve", "asset", "decision", "reason", "owner", "approved_by", "expires"}
today = datetime.date.today()
register = yaml.safe_load(open("security/exceptions.yaml")) or []
ids, errors = set(), []
for e in register:
    missing = REQUIRED - e.keys()
    if missing:
        errors.append(f"{e.get('id', '?')}: missing {sorted(missing)}")
        continue
    ids.add(e["id"])
    if e["expires"] < today:
        errors.append(f"{e['id']}: expired on {e['expires']} ({e['cve']}, owner {e['owner']})")
ignores = (yaml.safe_load(open(".trivyignore.yaml")) or {}).get("vulnerabilities", [])
for v in ignores:
    if not any(i in v.get("statement", "") for i in ids):
        errors.append(f".trivyignore.yaml: {v['id']} has no register ID in its statement")
    if "expired_at" not in v:
        errors.append(f".trivyignore.yaml: {v['id']} has no expired_at")
print("\n".join(errors) or "exceptions register OK")
sys.exit(1 if errors else 0)
```

```
EXC-2026-009: expired on 2026-09-30 (CVE-2026-55555, owner web-team-lead)
.trivyignore.yaml: CVE-2026-66666 has no register ID in its statement
```

→ One decision has lapsed and must be made again (fix now, or renew with a new approval), and one
finding was silenced directly in the ignore file, bypassing review. Both fail the job until someone
acts.

**Hands-on lab (throwaway GitLab project)**

**Step 1 — Build.** Create `security/exceptions.yaml` with two entries like the ones above, a
matching `.trivyignore.yaml` whose `statement` fields start with the register IDs, and a
`check-exceptions` job that runs the script in the scan stage.

**Step 2 — Break it.** Add an ignore for a new CVE straight into `.trivyignore.yaml` "to unblock a
release", and set one register entry's expiry to yesterday. The check fails with both messages.

**Step 3 — Fix it.** Move the new ignore into the register with a reason, a compensating control
and an approver, and make a new decision on the expired one. List the security owner for
`security/` in a `CODEOWNERS` file (enforced Code Owner approval needs a paid GitLab tier; on the
free tier, make it a review rule).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Ignore without a record | a finding vanished and nobody knows why | `git log -p .trivyignore.yaml` | this topic |
| No expiry | year-old exceptions for long-fixed CVEs | entries without `expires` | this topic |
| Harbor allowlist out of sync | Harbor blocks a pull that CI allowed, or the reverse | project CVE allowlist vs the register | section 6 |
| Engineers approve their own exceptions | an audit finding on segregation of duties | merge request approvals on `security/` | section 14 |

**Why it matters for troubleshooting.** When an expired exception blocks a 2 a.m. hotfix, the
register tells you in seconds what was accepted, why, and who can renew it, so nobody "fixes" it by
deleting the gate.

**Next step:** see attacks and mistakes as they happen.

---

## 12. Logging and detection

> 📚 **Study path:** 1) KodeKloud: *LFCS* — [Locate and Analyze System Log Files](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Operations-Deployment/Locate-and-Analyze-System-Log-Files/page) ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · 2) Note: [Logs & Journal](06-logs-journal.md), then [Performance & Observability](32-learn-performance-observability.md) section 14 (journald, Loki, Alloy and LogQL) · 3) KodeKloud: *Grafana Loki* for central search ([course](https://kodekloud.com/courses/grafana-loki)); optional, heavier: *EFK Stack* ([course](https://kodekloud.com/courses/efk-stack-enterprise-grade-logging-and-monitoring)) · 4) After the CKA: *CKS* — Runtime Security (Falco, audit logs) ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) · 5) Docs: the [Wazuh documentation](https://documentation.wazuh.com/current/) and the [CrowdSec documentation](https://docs.crowdsec.net/) (the verified KodeKloud map has no Wazuh or CrowdSec course), then the handbook module [Wazuh and security tools](48-wazuh-and-security-tools.md) · 6) Practice: the labs below on sec-target, with sec-scan as the noisy outsider.

Prevention fails eventually: a key leaks, a patch is late, a container is misconfigured. Detection
decides whether you find out in minutes or months. Section 2 got auditd running and section 7 turned
on the Kubernetes audit log; this area decides what to collect, gets it off the host before anyone
can delete it, and turns it into a small number of alerts that a person acts on.

```
 sources                      ship (TLS, buffered)              store and detect          people
 auth.log / journal ──┐
 auditd               ├──► rsyslog / Alloy / Wazuh agent ──► Loki / Wazuh indexer ──► rules ──► page / ticket / report
 Traefik access log   │                                         (off the host,        (tuned)        │
 docker events, K8s ──┘                                          retention set)                       └──► runbook (section 13)
```

**Field notes: what engineers actually ask**

| What people post | What is usually going on | Topic here | Search |
|---|---|---|---|
| "auth.log is full of `Invalid user` from all over the world, am I hacked?" | internet background noise; with key-only SSH it is noise, and closing port 22 to the world removes it | Auth logs and the journal | [Server Fault](https://serverfault.com/search?q=auth.log+invalid+user+many+attempts) |
| "fail2ban or CrowdSec bans the IP, but it still reaches my container" | bans land in INPUT; Docker-published ports go through FORWARD and DOCKER-USER | CrowdSec and Fail2ban behind Traefik | [CrowdSec issues](https://github.com/crowdsecurity/crowdsec/issues?q=is%3Aissue+docker+DOCKER-USER) |
| "Every request in my logs comes from 10.0.0.2 or 172.18.0.1" | Swarm ingress or an untrusted proxy hop replaces the client IP | CrowdSec and Fail2ban behind Traefik | [Traefik forum: Real IP and Host Header](https://community.traefik.io/t/real-ip-and-host-header/12336) |
| "Wazuh stopped showing new alerts after a few months" | the indexer hit its shard limit; no index retention policy | Wazuh host IDS and SIEM | [Wazuh group thread](https://groups.google.com/g/wazuh/c/AungE5r1llI) |
| "Wazuh dashboard: Port 443 is already in use" | Traefik or Apache already owns 443 on the host | Wazuh host IDS and SIEM | [Wazuh group thread](https://groups.google.com/g/wazuh/c/sXlJ4zGgLGA) |
| "auditd: backlog limit exceeded, events lost" | one rule too broad for the host's activity | auditd detection rules | [Server Fault](https://serverfault.com/search?q=auditd+backlog+limit+exceeded) |

### Auth logs and the journal

**Level:** [L1 · Junior]

**Concept.** Most security questions on a Linux host start with three facts: who logged in, from
where, and what they ran as root. On Ubuntu, `sshd`, `sudo`, `su`, PAM and `systemd-logind` write to
the **journal**, and rsyslog copies the `auth` and `authpriv` facilities to `/var/log/auth.log`
(rotated weekly, four weeks kept by default). Login records live in binary files with their own
commands: `wtmp` (`last`), `btmp` (failed logins, `lastb`) and `lastlog`. sudo logs every command
with its full command line, working directory and target user, which is why section 6 prefers
`sudo docker ...` to membership of the `docker` group.

Three version details decide whether your filters work. On Ubuntu, SSH runs as `ssh.service`
(socket-activated by default since 22.10), so filter with `-u ssh`, not `-u sshd`. Since
Ubuntu 23.10, rsyslog writes ISO 8601 timestamps with microseconds into `/var/log/auth.log`. And from
OpenSSH 9.8 (Ubuntu 25.04 and later; 24.04 has 9.6 and 24.10 has 9.7), per-connection messages come
from a separate `sshd-session` process, which matters for regex-based tools such as fail2ban
filters and for `_COMM=` journal matches.

The journal is persistent on Ubuntu (it keeps `/var/log/journal`) and capped by default at 10% of
the file system, at most 4 GB. Persistent does not mean safe: anyone with root can delete it, which
is why the next topics ship logs off the host.

**Key terms**

| Term | Meaning |
|---|---|
| `Invalid user` | a login attempt for an account that does not exist; constant noise on internet-facing SSH |
| `Accepted publickey` | a successful key login; the line names the user, the source IP and the key fingerprint |
| `COMMAND=` (sudo) | the exact command run as root, with `PWD` and the target `USER` |
| `wtmp` / `btmp` | binary records of logins and failed logins, read with `last` and `lastb` |
| Forward Secure Sealing | `journalctl --setup-keys`: makes later tampering with journal files detectable with `--verify` |

**See it on a real system**

```bash
sudo journalctl -u ssh --since "-1h" --no-pager | tail -n 4
sudo grep 'COMMAND=' /var/log/auth.log | tail -n 2
last -i -n 3
sudo journalctl --disk-usage
```

```
Oct 03 09:12:01 sec-target sshd[4120]: Invalid user admin from 203.0.113.50 port 40112
Oct 03 09:12:01 sec-target sshd[4120]: Connection closed by invalid user admin 203.0.113.50 port 40112 [preauth]
Oct 03 09:14:22 sec-target sshd[4188]: Accepted publickey for deploy from 198.51.100.23 port 51514 ssh2: ED25519 SHA256:Xq3cP0yq7mJ0kX6r2ZB8n1V1w9dT4kL0hS5aQ2eR7uY
Oct 03 09:14:22 sec-target sshd[4188]: pam_unix(sshd:session): session opened for user deploy(uid=1001) by (uid=0)
2026-10-03T09:20:41.512233+00:00 sec-target sudo:   deploy : TTY=pts/0 ; PWD=/home/deploy ; USER=root ; COMMAND=/usr/bin/docker exec -it shop-api sh
2026-10-03T09:22:05.004118+00:00 sec-target sudo:   deploy : TTY=pts/0 ; PWD=/home/deploy ; USER=root ; COMMAND=/usr/bin/systemctl restart apache2
deploy   pts/0        198.51.100.23    Sat Oct  3 09:14   still logged in
alice    pts/1        10.8.0.6         Fri Oct  2 18:02 - 18:40  (00:37)
reboot   system boot  0.0.0.0          Fri Oct  2 06:20   still running
Archived and active journals take 1.1G in the file system.
```

→ An internet scanner tried `admin` and was dropped before authentication (`[preauth]`): noise,
because passwords are off. `deploy` logged in with a key from 198.51.100.23. Is that address
expected? That single question is the most valuable security check on this page. Then `deploy`
opened a shell inside the shop-api container as root: legitimate debugging or not, it is on the
record with the exact command. The journal keeps 1.1 GB of history locally.

**Hands-on lab (sec-target and sec-scan)**

**Step 1 — Build a baseline.** From sec-scan, log in with your key, run two sudo commands, and make
one failed attempt with an unknown user (`ssh -o BatchMode=yes nosuchuser@192.168.56.21 true`).
Find all four events in the journal and in `auth.log`, and write down the filter you used for each.
Those filters become your detection queries later.

**Step 2 — Break it: lose the evidence.** Set `Storage=volatile` in a drop-in
(`/etc/systemd/journald.conf.d/lab.conf`), restart `systemd-journald`, reboot, and try to answer
"who logged in yesterday?". The journal starts at this boot. `auth.log` survived only because
rsyslog wrote a second copy, and root can delete that too.

**Step 3 — Fix it.** Remove the drop-in (persistent is Ubuntu's default), set a size cap that
matches your retention needs (`SystemMaxUse=2G`), optionally enable sealing (`sudo journalctl
--setup-keys`, keeping the verification key off the host), and continue with the next topics to get
a copy off the host.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Journal not persistent | `journalctl --list-boots` shows a single boot | `ls /var/log/journal`, journald drop-ins | [Logs & journal](06-logs-journal.md) |
| No `/var/log/auth.log` | minimal images without rsyslog | `systemctl status rsyslog`; use `journalctl` | [Logs & journal](06-logs-journal.md) |
| Filter finds no SSH lines | `journalctl -u sshd` is empty on Ubuntu | `journalctl -u ssh` or `-t sshd` | this topic |
| Clocks disagree | events from two hosts do not line up | `timedatectl` | [Time & NTP](12-time-ntp.md) |
| Unexpected login | accepted login from an unknown IP or at an odd hour | `last -i USER`, `journalctl -u ssh` | section 13 |

**Why it matters for troubleshooting.** The same three commands answer "who restarted Apache at
09:22?" during an outage and "who was on this box?" during an incident. Knowing the unit names and
timestamp formats is what makes those filters work the first time.

**Next step:** record changes to the files that matter, with auditd.

### auditd detection rules

**Level:** [L2 · Mid]

**Concept.** Section 2 got auditd running with identity rules. Detection rules watch the places
where attackers and careless administrators both make changes that matter: who may log in (SSH
authorized keys), what runs automatically (cron, systemd units), who controls Docker (its
configuration and its CLI), what the kernel loads (modules), who reads the private CA key, and which
commands people run as root. Two habits keep it useful. Filter on **auid** wherever daemons would
flood you (`-F auid>=1000 -F auid!=unset` records only logged-in humans). And measure the volume
before you ship it: one careless `execve` rule can produce more events than the rest of the host
together.

Watches cannot use wildcards, and the parent directory must exist when the rule loads, so list each
account whose keys matter (root, deploy, the users behind Dokploy and the GitLab Runner) instead of
watching all of `/home`. On 64-bit hosts, CIS-style rule sets repeat each syscall rule with
`arch=b32`, so 32-bit programs cannot slip past.

**Key terms**

| Term | Meaning |
|---|---|
| `-w PATH -p wa` | watch writes and attribute changes on a file or directory |
| `-S init_module,finit_module` | the syscalls that load kernel modules |
| `-F dir=PATH` | match a whole directory tree in a syscall rule |
| `auid>=1000 auid!=unset` | events caused by a logged-in person, not by daemons started at boot |
| Key (`-k`) | the label you search and alert on |

**See it on a real system** — the rule file:

```
# /etc/audit/rules.d/40-detect.rules
# SSH trust: list each account whose keys matter (the directory must exist)
-w /root/.ssh -p wa -k ssh_keys
-w /home/deploy/.ssh -p wa -k ssh_keys
# Persistence: scheduled jobs and services
-w /etc/crontab -p wa -k persistence
-w /etc/cron.d -p wa -k persistence
-w /var/spool/cron/crontabs -p wa -k persistence
-w /etc/systemd/system -p wa -k persistence
# Docker control plane
-w /etc/docker -p wa -k docker_cfg
-w /usr/bin/docker -p x -k docker_cli
# Kernel modules
-a always,exit -F arch=b64 -S init_module,finit_module,delete_module -k kmod
# Private CA key read by a person (the step-ca service itself runs with auid unset)
-a always,exit -F arch=b64 -S openat -F dir=/etc/step-ca/secrets -F auid>=1000 -F auid!=unset -k ca_key
# Commands run as root by people (measure the volume on busy hosts first)
-a always,exit -F arch=b64 -S execve -F euid=0 -F auid>=1000 -F auid!=unset -k root_cmd
```

Load it and read the results:

```bash
sudo augenrules --load
sudo ausearch -k ssh_keys -i --start today | grep -E 'type=(PROCTITLE|SYSCALL)' | tail -n 2
sudo aureport -k --summary --start today
```

```
type=PROCTITLE msg=audit(10/03/2026 10:02:44.118:1932) : proctitle=tee -a /home/deploy/.ssh/authorized_keys
type=SYSCALL msg=audit(10/03/2026 10:02:44.118:1932) : arch=x86_64 syscall=openat success=yes exit=3 a0=AT_FDCWD a1=0x7ffd5e3c8f21 a2=O_WRONLY|O_CREAT|O_APPEND a3=0x1b6 items=2 ppid=5120 pid=5121 auid=alice uid=root gid=root euid=root tty=pts1 ses=9 comm=tee exe=/usr/bin/tee key=ssh_keys

Key Summary Report
===========================
total  key
===========================
1406  root_cmd
12  persistence
9  docker_cli
2  ssh_keys
1  docker_cfg
```

→ alice, working as root, appended a line to deploy's `authorized_keys`: a new key for an account
used by automation. Whether it was a planned change is a question for the change log; whether it
was seen is no longer in doubt. The summary shows the cost: `root_cmd` produced 1,406 events today on
this lab host, which is fine here and may not be on a busy Dokploy node.

**Hands-on lab (sec-target)**

**Step 1 — Build.** Load the rule file (adjust the account names), then trigger each key once: edit
a crontab with `sudo crontab -e`, `sudo touch /etc/docker/daemon.json`, run `sudo docker ps`, and
load and unload a module you do not use (`sudo modprobe xfs && sudo modprobe -r xfs`). Find each
event with `sudo ausearch -k KEY -i`.

**Step 2 — Break it: one rule too broad.** Replace the `root_cmd` rule with an unfiltered one
(`-a always,exit -F arch=b64 -S execve -k all_exec`), load it, and run a busy loop as root
(`for i in $(seq 1 20000); do /bin/true; done`). Watch `sudo auditctl -s`: the backlog climbs, the
`lost` counter may grow, and `aureport --summary` shows thousands of events a minute.

**Step 3 — Fix it.** Restore the filtered rule. If `lost` is above zero under normal load, raise the
backlog (`-b 16384` at the top of a rules file) and remove noisy rules rather than accept lost
events. Then ship `audit.log` with the next topics, and alert only on keys that mean something on
their own: `ssh_keys`, `persistence` outside change windows, `kmod`, `ca_key` and `docker_cfg`.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Watch on a missing directory | `augenrules --load` reports an error, the rule is not loaded | `sudo auditctl -l | grep KEY` | this topic |
| Lost events | `lost` counter rising, gaps in the record | `sudo auditctl -s` | [CPU & performance](03-cpu-performance.md) |
| Only 64-bit rules | a 32-bit program's syscalls are not recorded | add the same rules with `arch=b32` | this topic |
| Immutable mode blocks a change | `The audit system is in immutable mode` | plan the change with a reboot | section 2 |
| Alerts on the service's own reads | `ca_key` fires every time step-ca starts | missing `auid` filter | this topic |

**Why it matters for troubleshooting.** "Someone added a cron job", "someone changed daemon.json"
and "someone added a key" each become a one-line `ausearch` answer with a person's name, instead of
a guessing game in the team chat.

**Next step:** get these events off the host before anyone can delete them.

### Centralised security logs

**Level:** [L2 · Mid] to ship, [L4 · Lead/SRE] to own retention, integrity and coverage

**Concept.** Local logs fail exactly when you need them: whoever gets root can delete them, rotation
removes old ones, and nobody correlates ten hosts by logging into each. A security logging design
answers five questions:

1. **What to ship:** the journal and `auth.log` (sshd, sudo, su, account changes), `audit.log`, the Traefik access log, Apache logs, Docker daemon logs, the Kubernetes API audit log (section 7), Harbor's audit log, Dokploy logs, and CloudTrail for AWS (section 10).
2. **How fast:** within seconds, over TLS, with a disk-backed queue so an outage of the log server loses nothing.
3. **Where:** a store the source hosts cannot modify, on a separately administered host or account.
4. **For how long:** set by your policy and contracts, not by disk size. A common pattern is 90 days searchable plus a year archived; PCI DSS, for example, requires a year of audit log history with the last three months immediately available.
5. **Is it still working:** alert when a host stops sending. Silence is the most common failure and the most dangerous one.

Three patterns fit this stack, and many teams run two of them. **rsyslog to rsyslog over TLS** is
built into Ubuntu and simple, with files on the log host. **Grafana Alloy to Loki** is your
observability stack from [Performance & Observability](32-learn-performance-observability.md)
section 14, with LogQL for detection queries. The **Wazuh agent to the Wazuh server** (next topic)
adds ready-made security rules. "Loki for operations, Wazuh for security" is a common split.

Time matters as much as transport: correlating events across hosts needs synchronised clocks
([Time & NTP](12-time-ntp.md)) and UTC in every report.

**Key terms**

| Term | Meaning |
|---|---|
| Syslog over TLS | RFC 5425, usually TCP 6514 |
| Disk-assisted queue | rsyslog buffers to disk while the destination is down and sends later |
| Retention / archive | how long logs stay searchable / how long they are kept at all |
| Object Lock (S3) | write-once storage: archived logs cannot be changed or deleted before their retention date |
| Absent-data alert | fires when a source stops sending, e.g. LogQL `absent_over_time` |

**See it on a real system** — every host forwards to `logs.example.com` (needs the `rsyslog-gnutls`
package and the private CA from section 4):

```
# /etc/rsyslog.d/60-forward-tls.conf on every host
global(DefaultNetstreamDriverCAFile="/usr/local/share/ca-certificates/example-root-ca.crt")
*.* action(type="omfwd" target="logs.example.com" port="6514" protocol="tcp"
    StreamDriver="gtls" StreamDriverMode="1" StreamDriverAuthMode="x509/name"
    StreamDriverPermittedPeers="logs.example.com"
    queue.type="LinkedList" queue.filename="fwd_all" queue.maxDiskSpace="1g"
    queue.saveOnShutdown="on" action.resumeRetryCount="-1")
```

The receiving side on the log host. Here the server only encrypts (`anon`) and UFW limits who may
connect; mutual TLS, with client certificates from your CA and `x509/name` on both ends, is the
stronger option:

```
# /etc/rsyslog.d/10-receive-tls.conf on logs.example.com
global(DefaultNetstreamDriverCAFile="/usr/local/share/ca-certificates/example-root-ca.crt"
       DefaultNetstreamDriverCertFile="/etc/rsyslog-tls/logs.example.com.crt"
       DefaultNetstreamDriverKeyFile="/etc/rsyslog-tls/logs.example.com.key")
module(load="imtcp" StreamDriver.Name="gtls" StreamDriver.Mode="1" StreamDriver.AuthMode="anon")
template(name="PerHost" type="string" string="/var/log/remote/%HOSTNAME%/%PROGRAMNAME%.log")
ruleset(name="remote") { action(type="omfile" dynaFile="PerHost") }
input(type="imtcp" port="6514" ruleset="remote")
```

rsyslog on Ubuntu drops privileges to the `syslog` user, so the key must be readable by that user
(owner root, group syslog, mode 640). Test the path end to end:

```bash
logger -t central-test -p auth.notice "central log test from $(hostname) at $(date -u +%FT%TZ)"
# then on logs.example.com:
sudo tail -n 1 /var/log/remote/sec-target/central-test.log
```

```
2026-10-03T10:40:12.118734+00:00 sec-target central-test: central log test from sec-target at 2026-10-03T10:40:12Z
```

→ The message crossed the network encrypted and landed in a per-host directory on a machine that
sec-target can send to but not change. If you use Loki instead, the same idea is an Alloy file
target for `/var/log/audit/audit.log` with `job="auditd"` (Alloy needs read access, because the file
is root-only by default), and detection queries in LogQL. Two that earn their place, using the labels
from the Alloy configuration in module 32 (logins from outside the VPN range, and a host that went
silent):

```
sum by (host) (count_over_time({job="systemd-journal", unit="ssh.service"} |= "Accepted publickey" != "from 10.8.0." [5m])) > 0
absent_over_time({job="systemd-journal", host="web01"}[15m])
```

**Hands-on lab (sec-target forwarding to sec-scan as the log host)**

**Step 1 — Build.** On sec-scan, install `rsyslog-gnutls`, issue a certificate for
`logs.example.com` from your lab CA (section 4), add the receiving configuration, and allow TCP 6514
from the lab network only (`sudo ufw allow from 192.168.56.0/24 to any port 6514 proto tcp`). On
sec-target, add `192.168.56.22 logs.example.com` to `/etc/hosts`, add the forwarding file, restart
rsyslog and send the test message.

**Step 2 — Break it twice.** First stop rsyslog on sec-scan, generate a few sudo events on
sec-target, then start it again: the queued messages arrive late but complete (compare the
timestamps). Then point the client at a wrong CA file and restart rsyslog: `journalctl -u rsyslog`
shows TLS errors, and nothing arrives.

**Step 3 — Fix it and watch the pipeline.** Restore the CA path. Add an absent-data check for every
host: `absent_over_time` in Loki, or a cron job on the log host that alerts when no file in a host's
directory has changed for 15 minutes (check the files: a directory's own timestamp only changes when
files are created or removed, not when they grow). A log pipeline without a silence alert fails quietly, and usually
right before you need it.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| TLS trust missing | `journalctl -u rsyslog` shows certificate errors; nothing arrives | CA path in the client configuration | section 4 |
| Log host down, no queue | a gap in central logs for the length of the outage | `queue.filename` set on the client? | this topic |
| A host stopped sending | its directory or stream stops updating, nobody notices | the absent-data alert | this topic |
| Log host disk full | everything stops at once | `df -h /var/log/remote` | [Storage & disk](01-storage-disk.md) |
| Local-time timestamps | events "out of order" across hosts | `timedatectl` on each host | [Time & NTP](12-time-ntp.md) |
| Secrets in logs | tokens visible in central search | the application's log lines, CI job logs | section 5 |

**Why it matters for troubleshooting.** Central logs answer cross-host questions ("which hosts did
this IP touch?") in one query, and they outlive the host. In an incident they are often the only
evidence an intruder could not reach.

**Next step:** add ready-made security detection on top of the logs, with Wazuh.

### Wazuh host IDS and SIEM

**Level:** [L2 · Mid] to operate, [L3 · Senior] to design and tune

**Concept.** Wazuh is an open-source security platform that grew out of OSSEC. It combines a
host-based intrusion detection agent with a SIEM. The **agent** on each host collects logs, watches
files (file integrity monitoring, FIM), checks configuration against CIS-based policies (security
configuration assessment, SCA), inventories packages for vulnerability detection, and can run **active
responses** such as blocking an IP. The **server** decodes events, matches them against
thousands of rules, each with a **level** from 0 to 15, and raises alerts. The **indexer**
(OpenSearch-based) stores them and the **dashboard** displays them. The module
[Wazuh and security tools](48-wazuh-and-security-tools.md) covers installation, sizing and
day-to-day operation; this topic covers what Wazuh adds to detection and how to read it.

```
 agents (web01, sec-target, harbor01)        Wazuh server                       indexer and dashboard
 logs, FIM, SCA, inventory ──1514/tcp──►  decoders ► rules (0–15) ► alerts ──► OpenSearch :9200 ──► dashboard :443
 enrolment ──────────────────1515/tcp──►  API 55000/tcp
```

Ports to record in firewalls and in the port inventory: 1514/tcp (agent events), 1515/tcp
(enrolment), 55000/tcp (API), 9200/tcp (indexer API) and 443/tcp (dashboard). The dashboard's
default of 443 collides with Traefik or Apache on a shared host, a common forum thread: move the
dashboard to another port (`server.port` in `/etc/wazuh-dashboard/opensearch_dashboards.yml`) and
publish it through Traefik with the dashboard's CA trusted, never with certificate verification
switched off in production.

Default rules you will meet first:

| Rule | Level | Meaning |
|---|---|---|
| 5710 | 5 | sshd: attempt to log in with a non-existent user |
| 5712 | 10 | sshd: brute force with non-existent users (8 events within 120 s) |
| 5715 | 3 | sshd: authentication success |
| 5402 | 3 | successful sudo to root |
| 5403 | 4 | first time a user ran sudo |
| 5404 | 10 | three failed attempts to run sudo |
| 550 / 554 | 7 / 5 | FIM: file checksum changed / file added |
| 504 | 3 | Wazuh agent disconnected |

**Key terms**

| Term | Meaning |
|---|---|
| Decoder | extracts fields (user, source IP, program) from a raw log line |
| Rule level | 0 means no alert (used for grouping and silencing), up to 15 for the most severe |
| `if_sid` | a child rule that only matches after a parent rule matched: how you refine or silence |
| FIM `realtime` / `whodata` | inotify-based change detection / who-data from auditd, naming the user who changed a file |
| SCA | security configuration assessment against policy files, many based on CIS benchmarks |
| Active response | a script the server triggers on an agent, for example a firewall drop for an IP |

**See it on a real system** (on the Wazuh server):

```bash
sudo /var/ossec/bin/agent_control -l
sudo jq -r 'select(.rule.level >= 7) | [.timestamp, .agent.name, .rule.id, .rule.level, .rule.description, (.data.srcip // .syscheck.path // "-")] | @tsv' \
  /var/ossec/logs/alerts/alerts.json | tail -n 4
```

```
Wazuh agent_control. List of available agents:
   ID: 000, Name: wazuh-mgr (server), IP: 127.0.0.1, Active/Local
   ID: 001, Name: web01, IP: any, Active
   ID: 002, Name: sec-target, IP: any, Active
   ID: 003, Name: harbor01, IP: any, Disconnected

2026-10-03T09:12:40.118+0000	sec-target	5712	10	sshd: brute force trying to get access to the system. Non existent user.	203.0.113.50
2026-10-03T10:02:45.006+0000	sec-target	550	7	Integrity checksum changed.	/home/deploy/.ssh/authorized_keys
2026-10-03T10:31:17.442+0000	web01	5404	10	Three failed attempts to run sudo	-
2026-10-03T11:05:09.871+0000	web01	100110	12	sshd: login accepted from outside the VPN range	198.51.100.23
```

→ Four alerts, four different responses. The brute force is internet noise on a host that still
exposes SSH to the world: fix the exposure, do not page anyone. The `authorized_keys` change matches
the auditd event from the previous topic and needs either a change ticket or an incident. Three
failed sudo attempts on web01 deserve a look today. The last one comes from a custom rule (below) and
should page, because a successful login from outside the VPN range is either a policy break or a
stolen key. And harbor01 has gone quiet: an agent that stopped reporting is a detection gap, not a
cosmetic issue.

Agent settings on each host (in `/var/ossec/etc/ossec.conf`):

```xml
<syscheck>
  <directories realtime="yes" report_changes="yes">/etc/ssh,/etc/docker,/etc/cron.d,/etc/systemd/system</directories>
  <directories whodata="yes">/root/.ssh,/home/deploy/.ssh</directories>
  <nodiff>/etc/ssh/ssh_host_ecdsa_key</nodiff>
  <nodiff>/etc/ssh/ssh_host_ed25519_key</nodiff>
  <nodiff>/etc/ssh/ssh_host_rsa_key</nodiff>
</syscheck>
<localfile>
  <log_format>audit</log_format>
  <location>/var/log/audit/audit.log</location>
</localfile>
```

`report_changes` sends the diff of a changed text file to the server. That is excellent for
configuration files and dangerous for files that hold secrets, because whatever is in the diff ends
up in the alert index, readable by everyone with dashboard access. The SSH host private keys live in
`/etc/ssh`, hence the `nodiff` lines.

A custom rule on the server, in `/var/ossec/etc/rules/local_rules.xml`, turns "SSH success" into
"SSH success from outside the VPN range":

```xml
<group name="local,sshd,">
  <rule id="100110" level="12">
    <if_sid>5715</if_sid>
    <srcip negate="yes">10.8.0.0/24</srcip>
    <description>sshd: login accepted from outside the VPN range</description>
    <group>authentication_success,</group>
  </rule>
</group>
```

Test it without waiting for a real login: run `sudo /var/ossec/bin/wazuh-logtest`, paste an
`Accepted publickey` line, and read the third phase (illustrative):

```
**Phase 3: Completed filtering (rules).
	id: '100110'
	level: '12'
	description: 'sshd: login accepted from outside the VPN range'
	groups: '["local","sshd","authentication_success"]'
	firedtimes: '1'
	mail: 'True'
**Alert to be generated.
```

Restart the server to load rule changes (`sudo systemctl restart wazuh-manager`). Custom rules
conventionally use IDs from 100000 upwards, so upgrades of the default ruleset never collide with
them.

**Hands-on lab (a fourth VM, sec-siem, with about 4 vCPU and 8 GB RAM)**

The all-in-one Wazuh installation needs more than the 2–4 GB lab VMs; check the current quickstart
requirements in the Wazuh documentation before you size the VM.

**Step 1 — Build.** Install the all-in-one server on sec-siem following the quickstart in the
[Wazuh documentation](https://documentation.wazuh.com/current/), enrol an agent on sec-target, add
the FIM and audit settings above, and load the custom rule. From sec-scan, generate failed logins
against your own lab VM (`for i in $(seq 1 10); do ssh -o BatchMode=yes -o ConnectTimeout=3
nouser$i@192.168.56.21 true; done`) and find rule 5712 in the dashboard.

**Step 2 — Break it: leak a secret into the index.** Create `/etc/lab-secrets/db.env` with a fake
password, add `/etc/lab-secrets` to a `directories` line with `report_changes="yes"`, then change the
file. Search the dashboard for the fake password: it is in the alert's diff.

**Step 3 — Fix it.** Add the file to `nodiff` (or drop `report_changes` for that directory),
"rotate" the fake secret, and remove the affected alerts following the procedure for your indexer.
Then write the rule down for the team: no `report_changes` on any path that can hold keys or
credentials.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Dashboard collides with Traefik or Apache on 443 | `Port 443 is already in use` during installation or start | `sudo ss -ltnp 'sport = :443'` | [Who owns this port?](22-playbook-ports-inventory.md), [Wazuh and security tools](48-wazuh-and-security-tools.md) |
| Agent disconnected | `Disconnected` in `agent_control -l`, rule 504 | `sudo tail /var/ossec/logs/ossec.log` on the agent; 1514 and 1515 reachable? | [Wazuh and security tools](48-wazuh-and-security-tools.md) |
| Agents from cloned VMs fight | agents flap or replace each other | duplicate `client.keys` baked into the image | [Wazuh and security tools](48-wazuh-and-security-tools.md) |
| No new alerts months after installation | `[1000]/[1000] maximum shards open` in the indexer | shard count, index retention policy | [Wazuh group thread](https://groups.google.com/g/wazuh/c/AungE5r1llI) |
| Indexer read-only | disk above the flood-stage watermark | `df -h` on the indexer | [Storage & disk](01-storage-disk.md) |
| Secret in FIM diffs | a credential readable in alert text | `report_changes` paths | this topic |

**Why it matters for troubleshooting.** Wazuh's FIM and log rules answer "what changed on this host,
and who did it?" across the fleet in one search, which is as useful in an outage ("who edited
daemon.json?") as in an incident.

**Next step:** block abusive sources automatically, without blocking your own users.

### CrowdSec and Fail2ban behind Traefik

**Level:** [L2 · Mid]

**Concept.** Both tools read logs, detect abusive behaviour per source IP and block it. **fail2ban**
(section 2) does everything locally, with regex filters and firewall actions. **CrowdSec** splits
the job: its security engine parses logs with parsers and **scenarios** from its hub, installed as **collections**
such as `crowdsecurity/linux`, `crowdsecurity/sshd` and `crowdsecurity/traefik`, and
records **decisions** in a local API; separate **remediation components** (bouncers) enforce them,
for example the firewall bouncer or a Traefik plugin. Participants can also receive a community
blocklist of known-bad IPs. Installation and day-to-day operation of both tools, including the
Traefik bouncer, are in [Wazuh and security tools](48-wazuh-and-security-tools.md); this topic is
about the two traps that decide whether they work on a Docker host.

On a Docker or Dokploy host both tools fail in the same two ways, which together account for a large
share of the forum threads about them:

1. **The wrong IP.** If Traefik runs as a Swarm service with its ports published in the default ingress mode, or sits behind another proxy or load balancer it does not trust, its access log shows `10.0.0.2` or `172.18.0.1` for every request. The tools then ban the proxy (everyone is locked out) or ban nothing. Fix the chain first: publish Traefik's ports in host mode on Swarm, set `forwardedHeaders.trustedIPs` (or PROXY protocol) for the hop in front, and use `mod_remoteip` with `%a` on Apache (section 9).
2. **The wrong chain.** Bans in the host's INPUT chain do not touch traffic to Docker-published ports, which is forwarded through FORWARD and Docker's chains: the same reason Docker bypasses UFW (section 3). Put bans into `DOCKER-USER` instead (fail2ban: `chain = DOCKER-USER` with an iptables action; CrowdSec's firewall bouncer: add `DOCKER-USER` to `iptables_chains`), or block at Traefik with the bouncer plugin, which sees the correct client IP once point 1 is fixed. If you run Docker with its newer, opt-in nftables backend, check the Docker documentation for where your own rules belong.

**Key terms**

| Term | Meaning |
|---|---|
| Acquisition | which logs CrowdSec reads, and with which `type` label: `/etc/crowdsec/acquis.yaml` or files in `acquis.d/` |
| Scenario | a behaviour to detect, e.g. `crowdsecurity/ssh-bf`, `crowdsecurity/http-probing` |
| Decision | an action on a scope and value, e.g. ban `Ip:203.0.113.50` for four hours |
| Bouncer | the component that enforces decisions: firewall, Traefik plugin, nginx module |
| `DOCKER-USER` | the iptables chain Docker evaluates before its own rules, reserved for yours |

**See it on a real system** — sec-target with CrowdSec, the sshd and traefik collections, and the
iptables firewall bouncer. First the acquisition file for Dokploy's Traefik access log (enabled in
Dokploy's Traefik settings, as in the [Apache 443 case](21-case-apache-443-dokploy.md)):

```yaml
# /etc/crowdsec/acquis.d/traefik.yaml
filenames:
  - /etc/dokploy/traefik/dynamic/access.log
labels:
  type: traefik
```

If Traefik logs only to stdout, read the container instead: `source: docker` with
`container_name: [dokploy-traefik]` and the same label. Then the bouncer, so bans also cover
published container ports (`/etc/crowdsec/bouncers/crowdsec-firewall-bouncer.yaml`, or a `.local`
override file that survives upgrades):

```yaml
mode: iptables
iptables_chains:
  - INPUT
  - DOCKER-USER
```

```bash
sudo cscli decisions list
```

```
╭────────┬──────────┬──────────────────┬────────────────────────────┬────────┬─────────┬────┬────────┬────────────┬──────────╮
│   ID   │  Source  │   Scope:Value    │           Reason           │ Action │ Country │ AS │ Events │ expiration │ Alert ID │
├────────┼──────────┼──────────────────┼────────────────────────────┼────────┼─────────┼────┼────────┼────────────┼──────────┤
│ 120035 │ crowdsec │ Ip:198.51.100.77 │ crowdsecurity/http-probing │ ban    │         │    │ 11     │ 3h41m2s    │ 42       │
│ 120034 │ crowdsec │ Ip:203.0.113.50  │ crowdsecurity/ssh-bf       │ ban    │         │    │ 7      │ 3h12m40s   │ 41       │
╰────────┴──────────┴──────────────────┴────────────────────────────┴────────┴─────────┴────┴────────┴────────────┴──────────╯
```

→ Two addresses are banned for about four hours: one for SSH brute force, one for probing web paths
through Traefik. Because the bouncer also writes to `DOCKER-USER`, the web ban covers the Dokploy
apps behind Traefik's published ports. Remove a false positive with `sudo cscli decisions delete
--ip 198.51.100.77`, and test a parser against a log with `sudo cscli explain --file
/etc/dokploy/traefik/dynamic/access.log --type traefik`.

The fail2ban equivalent for a service on a Docker-published port:

```ini
# /etc/fail2ban/jail.d/traefik-auth.local
[traefik-auth]
enabled   = true
filter    = traefik-auth
logpath   = /etc/dokploy/traefik/dynamic/access.log
banaction = iptables-multiport
chain     = DOCKER-USER
port      = http,https
maxretry  = 10
findtime  = 10m
bantime   = 1h
```

In both tools, exempt trusted sources (fail2ban's `ignoreip`; CrowdSec's whitelist or allowlist
feature, depending on your version) so monitoring, the office NAT and the VPN are never banned.

**Hands-on lab (sec-target and sec-scan)**

**Step 1 — Build.** Install CrowdSec and the iptables firewall bouncer from CrowdSec's repository on
sec-target, run `sudo cscli collections install crowdsecurity/traefik`, add the acquisition file,
enable Traefik's access log, and reload CrowdSec (`sudo systemctl reload crowdsec`). Leave the
bouncer on `INPUT` only for now.

**Step 2 — Break it, both ways.** (a) From sec-scan, probe paths on your own lab site until a
decision appears (repeat `for p in .env .git/config wp-login.php phpmyadmin admin.php; do curl -sk
-o /dev/null -w '%{http_code} ' https://app.example.com/$p; done`). sec-scan is now banned, yet
`curl -sk https://app.example.com/` from sec-scan still answers: the published port bypasses INPUT.
(b) If you run Traefik as a Swarm service with ingress-mode ports, look at the IP in the decision:
it is the ingress mesh address, so every visitor is now banned.

**Step 3 — Fix it.** Add `DOCKER-USER` to `iptables_chains` and restart the bouncer; for (b),
publish Traefik's ports in host mode. Repeat the probe: the decision now names sec-scan's real
address and blocks the published port too. Unban with `sudo cscli decisions delete --ip ADDRESS`,
and add your VPN and monitoring ranges to the allowlist.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Ban does not block a container | a banned IP still reaches Dokploy apps | `sudo iptables -L DOCKER-USER -n` | section 3 |
| Everyone banned at once | decision for `10.0.0.2` or `172.18.0.1` | access log client IP, Swarm publish mode | section 9 |
| No decisions, ever | log not parsed (`cscli metrics` shows unparsed lines) | `sudo cscli explain --file LOG --type traefik` | this topic |
| Monitoring banned | probes fail from one source only | `sudo cscli decisions list`, `sudo fail2ban-client status` | this topic |
| Access log path changed after a Dokploy update | CrowdSec reads nothing new | `ls -l /etc/dokploy/traefik/dynamic/access.log` | [Apache 443 case](21-case-apache-443-dokploy.md) |

**Why it matters for troubleshooting.** "Works from my phone, times out from the office" and "the
site is down for everyone" both have an automatic ban high on the list of causes. `cscli decisions
list` and `fail2ban-client status` rule it in or out in seconds.

**Next step:** signals from containers and the cluster.

### Container and cluster signals

**Level:** [L2 · Mid] for Docker, [L3 · Senior] for Kubernetes and Falco

**Concept.** On a container platform, many security-relevant events never appear in host logs:

| Event | Why it matters | Source |
|---|---|---|
| a container starts with `--privileged`, host network or PID, a `/` mount, or the Docker socket | each one is root on the host | `docker events`, a periodic `docker inspect` audit |
| `docker exec` into a production container | a hands-on change outside the pipeline | `docker events`, the auditd `docker_cli` key, the sudo log |
| an image pushed to Harbor by a person instead of a robot account | bypasses the scan-and-sign pipeline (section 8) | Harbor's audit log |
| a person reads a production Secret, opens a shell in a pod, or creates a role binding | the sequence in section 7's audit log example | Kubernetes API audit log |
| a shell spawns in a container, a sensitive file is read, an unexpected binary runs | runtime behaviour no log line describes | Falco |

**Falco** watches system calls on every node (through eBPF) and matches them against rules; its
default rules include *Terminal shell in container* and *Read sensitive file untrusted*. It is part
of the CKS syllabus (section 7) and runs as a DaemonSet in the homelab cluster.

This topic also keeps a promise from section 6: alert on any new Docker socket mount. A small script
exports the count as a node_exporter textfile metric (the pattern from
[Performance & Observability](32-learn-performance-observability.md)), and Prometheus alerts when
it differs from what the host should have: two on a Dokploy host (`dokploy` and `dokploy-traefik`),
zero elsewhere.

**Key terms**

| Term | Meaning |
|---|---|
| `docker events` | the daemon's live event stream (start, exec, pull); only a short history is kept |
| Robot account | Harbor's non-human account, named `robot$...`; pushes by anything else deserve a look |
| Falco rule | a condition on system calls, with an output template and a priority |
| Falcosidekick | Falco's companion that forwards events to Loki, Alertmanager, chat and more |

**See it on a real system.** Container starts and execs on the Dokploy host, live:

```bash
docker events --filter type=container \
  --format '{{.TimeNano}} {{.Action}} {{.Actor.Attributes.name}} {{.Actor.Attributes.image}}' \
  | grep -E ' (start|exec_create)'
```

```
1791020042118734000 start metrics-agent alpine:3.20
1791020101004512000 exec_create: sh shop-api.1.k3x9p0q7r2s4 harbor.example.com/shop/api:1.8.1@sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c
```

The Docker socket metric, run from cron every five minutes:

```bash
sudo tee /usr/local/bin/docker-sock-metric.sh >/dev/null <<'EOF'
#!/usr/bin/env bash
# Export how many running containers mount the Docker socket (read-only check)
set -euo pipefail
dir=/var/lib/node_exporter/textfile
n=$(docker ps -q | xargs -r docker inspect --format '{{range .Mounts}}{{.Source}} {{end}}' | grep -c 'docker\.sock' || true)
printf 'docker_sock_mounts %s\n' "$n" > "$dir/docker_sock.prom.$$"
mv "$dir/docker_sock.prom.$$" "$dir/docker_sock.prom"
EOF
sudo chmod 755 /usr/local/bin/docker-sock-metric.sh
echo '*/5 * * * * root /usr/local/bin/docker-sock-metric.sh' | sudo tee /etc/cron.d/docker-sock-metric
```

And the alert rule, assuming your scrape targets carry a `role` label:

```yaml
groups:
  - name: container-security
    rules:
      - alert: DockerSocketMountsChanged
        expr: (docker_sock_mounts{role="dokploy"} != 2) or (docker_sock_mounts{role!="dokploy"} > 0)
        for: 5m
        labels:
          severity: page
        annotations:
          summary: "{{ $labels.instance }}: {{ $value }} running containers mount docker.sock"
          runbook: "37-learn-security-devsecops.md, section 6, Docker socket and group audit"
```

Falco in the homelab cluster (after the CKA), then a test that should trigger it:

```bash
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco -n falco --create-namespace \
  --set driver.kind=modern_ebpf --set tty=true
kubectl -n shop exec -it deploy/api -- sh -c 'exit'
kubectl -n falco logs -l app.kubernetes.io/name=falco -c falco --since 5m | grep -i 'shell was spawned'
```

```
10:41:07.402114500: Notice A shell was spawned in a container with an attached terminal (evt_type=execve user=app user_uid=10001 process=sh proc_exepath=/bin/busybox parent=containerd-shim command=sh -c exit terminal=34816 container_id=6f0c2a1b9e3d container_image=harbor.example.com/shop/api k8s_ns=shop k8s_pod_name=api-6d9f7c8b5-x2k8p)
```

The exact fields vary between Falco versions. Kubernetes audit events become detections with LogQL
once the audit log is shipped with `job="k8s-audit"` (the json parser flattens `user.username` to
`user_username`):

```
{job="k8s-audit"} | json | objectRef_resource="secrets" and verb="get" and user_username!~"system:.*"
{job="k8s-audit"} | json | objectRef_subresource="exec"
{job="k8s-audit"} | json | objectRef_resource=~"clusterrolebindings|rolebindings" and verb="create"
```

And Harbor pushes by people rather than robot accounts (the audit log API changed in recent Harbor
releases, so check the API explorer at `https://harbor.example.com/devcenter-api-2.0` for your
version):

```bash
curl -s -u "$HARBOR_USER:$HARBOR_PASSWORD" "https://harbor.example.com/api/v2.0/audit-logs?page_size=50" \
  | jq -r '.[] | select(.operation=="create" and .resource_type=="artifact" and (.username | startswith("robot$") | not))
           | [.op_time, .username, .resource] | @tsv'
```

```
2026-10-02T21:47:13.000Z	alice	shop/api:hotfix-test
```

→ A person pushed an image straight into the production project at 21:47, outside the pipeline. If
Harbor's "only signed images" policy (section 6) is on, production cannot pull it; if not, this is
exactly how an unscanned image reaches a server.

**Hands-on lab (sec-target and the homelab cluster)**

**Step 1 — Build.** Install the socket metric and the alert on sec-target. Ship `docker events` to
your log store; for a lab, a small systemd service that writes the stream to the journal is enough:

```ini
# /etc/systemd/system/docker-events-log.service
[Unit]
Description=Log Docker events to the journal
After=docker.service
Requires=docker.service

[Service]
ExecStart=/usr/bin/docker events --format '{{json .}}'
Restart=always

[Install]
WantedBy=multi-user.target
```

In the homelab cluster, install Falco and ship the API audit log with `job="k8s-audit"`.

**Step 2 — Break it.** Start `docker run -d --name metrics-agent -v
/var/run/docker.sock:/var/run/docker.sock:ro alpine:3.20 sleep infinity` on sec-target, `kubectl
exec` into a pod, and push an image to Harbor with your own account. Note which of the three raised
an alert, and how long each took.

**Step 3 — Fix the gaps.** For every event that was logged but did not alert, choose a route (next
topic). Then remove the test container and the test image.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Events lost while nothing listened | gaps in the `docker events` history | ship the stream continuously | this topic |
| Falco not running on a node | no events from that node | `kubectl -n falco get pods -o wide` | [Learn Kubernetes](31-learn-kubernetes.md) |
| Falco floods | thousands of Notice events from one workload | a local rules file with narrow exceptions | next topic |
| Socket metric stale | value never changes, cron silent | `ls -l /var/lib/node_exporter/textfile/` | [Performance & Observability](32-learn-performance-observability.md) |
| Audit log only on the control plane | the evidence lives only on cp1 | agent configuration for `/var/log/kubernetes/audit/` | section 7 |

**Why it matters for troubleshooting.** "Who changed this container?" and "how did this image get
here?" are operational questions as often as security ones, and the same events answer both.

**Next step:** make sure the alerts you now have are ones people act on.

### Alert tuning

**Level:** [L3 · Senior] to design, [L4 · Lead/SRE] to run the review

**Concept.** A detection is only worth something if a person acts on it. Teams that turn on every
rule drown within a month and start ignoring the channel, and the one real alert then sits unread
among four hundred others. Tuning is a routine, not a project:

- **Route by action, not by tool.** Page: act within minutes. Ticket: look today. Report: weekly review only.
- **Narrow, never delete.** Silence a known-benign case with the narrowest condition (this account, this command, this host) and a review date, and keep the rule for everything else.
- **Correlate with changes.** A file-integrity alert on `/etc/docker` during an approved window is expected; the same alert at 02:00 with no change ticket is not.
- **Test detections like code.** Rules live in Git, and each one has a sample event and a test (`wazuh-logtest`, `cscli explain`, `promtool test rules`).
- **Measure.** For each rule: alerts per week, the share that led to action, and time to acknowledge. A rule that fired 50 times and nobody acted is a report, not an alert.

A starting routing table for this stack:

| Signal | Route | Why |
|---|---|---|
| SSH or sudo success from outside the VPN or office ranges | page | a stolen key or a policy break; minutes matter |
| new binding to `cluster-admin`, or a person reading production Secrets | page | the step before a takeover |
| audit rules changed, journal or audit log deleted, CloudTrail stopped | page | someone is hiding |
| Docker socket mount count changed | page in production, ticket elsewhere | root on the host |
| KEV finding on an exposed asset (section 11) | ticket within the hour, P1 process | exploited in the wild |
| FIM change in `/etc` outside a change window, first-time sudo, new SUID file | ticket | usually a person's change, sometimes not |
| CrowdSec or fail2ban bans, internet SSH noise, blocked scans | weekly report | the controls doing their job |

**Key terms**

| Term | Meaning |
|---|---|
| Precision | the share of alerts that were real and actionable |
| Alert fatigue | people stop reading a channel because most of it is noise |
| Suppression | a narrow, documented rule that silences a known-benign case |
| Detection as code | rules, tests and routing kept in Git and reviewed like application code |

**See it on a real system** — which rules make the noise (Wazuh server):

```bash
sudo jq -r '"\(.rule.id) L\(.rule.level) \(.rule.description)"' /var/ossec/logs/alerts/alerts.json \
  | sort | uniq -c | sort -rn | head -n 5
```

```
   2310 5710 L5 sshd: Attempt to login using a non-existent user
    412 5402 L3 Successful sudo to ROOT executed.
    289 5712 L10 sshd: brute force trying to get access to the system. Non existent user.
     37 550 L7 Integrity checksum changed.
      3 100110 L12 sshd: login accepted from outside the VPN range
```

→ Internet SSH noise is most of today's volume and nobody needs to act on it. Close port 22 to the
world (VPN or allowlist, section 3) and the noise disappears at the source, which beats any filter.
Rule 5402 is a report, not an alert. The three 100110 alerts are the ones that matter, and with the
noise gone they will actually be read.

A narrow suppression in `local_rules.xml`, with its reason in the file (Wazuh rules have no expiry
field, so the ticket and review date in the comment are what the weekly review checks). It matches
the sudo log text for one account and one command, and like every rule change it is tested with
`wazuh-logtest` against a real log line before it is deployed:

```xml
<group name="local,sudo,">
  <!-- SEC-151: the backup account runs this exact command nightly. Review on 2027-01-31. -->
  <rule id="100120" level="0">
    <if_sid>5402</if_sid>
    <regex>^\s*backup : </regex>
    <match>COMMAND=/usr/bin/rsync</match>
    <description>Silenced: nightly rsync by the backup account (SEC-151)</description>
  </rule>
</group>
```

**Hands-on lab (sec-siem and sec-target)**

**Step 1 — Build a week of data.** Run sec-target with this area's controls for a week (or replay the
lab events several times), then run the count above.

**Step 2 — Break it: one loud rule.** Raise rule 5402 to level 10 with an `overwrite="yes"` copy of
the rule in `local_rules.xml`, and route level 10 to a chat channel. Within a day the channel is
unreadable, and a planted test event (an SSH login from sec-scan's address, outside the VPN range)
goes unnoticed in the flood.

**Step 3 — Fix it.** Remove the overwrite, route by the table above, add one narrow suppression with
a ticket reference, and write a test for rule 100110 (a sample log line and the expected rule ID)
that you run with `wazuh-logtest` before every rule change. Book a 30-minute weekly review: the top
five noisy rules, one tuning change each.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Alert fatigue | channel muted, real alert missed | the top-five noisy rules query | this topic |
| Over-suppression | a broad level-0 rule hides real events | review level-0 rules without a narrow condition | this topic |
| Alerts to nobody | mail to an unmonitored mailbox | routing configuration, last acknowledged alert | [Performance & Observability](32-learn-performance-observability.md) section 12 |
| Rule broken by an upgrade | decoder or field names changed, the rule never fires | the test with a sample event | this topic |
| Nobody on call for security | night pages go to the wrong team | the on-call rota | [Senior architecture](39-learn-senior-architecture.md) section 11 |

**Why it matters for troubleshooting.** The skills are the same as for operational alerting
(grouping, inhibition and silences in [Performance & Observability](32-learn-performance-observability.md)
section 12): an alert must be rare, actionable and owned, or it is noise.

**Next step:** what to do when one of these alerts is real.

---

## 13. Security incident response

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Incident Management: Preparing for Incidents, IMAG roles, [Blameless Postmortem Culture](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page) and [Root Cause Analysis](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Root-Cause-Analysis/page) ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 2) Note: [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 7 (incident roles, the first fifteen minutes, blameless postmortems) and [Senior architecture](39-learn-senior-architecture.md) section 11 (incident command); this area adds what changes when the incident is a compromise · 3) Reading: the [NIST incident response project](https://csrc.nist.gov/projects/incident-response) (SP 800-61 Rev. 3) and the [Google SRE book](https://sre.google/sre-book/table-of-contents/), chapters 14 and 15 · 4) Note: [Learn: Cloud & AWS](36-learn-cloud-aws.md) section 13 (cloud security incidents) for the AWS side · 5) Practice: the tabletop in the first topic, then the security game day at the end of this area.

A security incident is not an outage with a different label. An adversary may still be active and
adapting; evidence matters for the investigation, for insurers, for customers and sometimes for the
courts; the fix is usually "rebuild and rotate", not "restart"; communication is on a need-to-know
basis; and legal notification deadlines may start the moment you become aware. DevOps engineers are
usually the hands in such an incident. You hold the access and know the systems, so you can contain
fast, and you can also destroy the evidence fast. This area is procedural and defensive throughout:
how to respond, not how attacks work.

Five rules hold through every topic below:

1. **Do not "clean up" first.** No reboot, no reinstall, no deleting suspicious files before the evidence is preserved, unless active destruction is under way and containment cannot wait.
2. **Assume your normal channels are read.** Coordinate out of band until you know the scope.
3. **Work from a clean machine.** Never type new credentials on a compromised host.
4. **Write everything down**, in UTC, as you go: what you saw, what you did, and when.
5. **Escalate early.** Bring in the security owner, your manager and, through them, legal. Calling an incident that turns out to be benign costs an hour; calling it late can cost a lot more.

**Field notes: what engineers actually ask**

| What people post | What is usually going on | Topic here | Search |
|---|---|---|---|
| "My server is at 100% CPU with a process called kdevtmpfsi or kinsing" | a crypto-miner, typically through an exposed Docker API, an exposed Redis or a vulnerable web app; killing the process does not remove the way in | Containment, then Rebuild from known-good | [Server Fault](https://serverfault.com/search?q=kdevtmpfsi), [GitHub issues](https://github.com/search?q=kdevtmpfsi&type=issues) |
| "I pushed my AWS key to GitHub and the bill exploded" | leaked access key used within minutes | Rotating credentials | [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=leaked+access+key+bill&restrict_sr=1) |
| "There is a container on my Docker host I did not start" | exposed Docker API on 2375, a compromised panel, or a stolen deploy credential | The first hour | [Server Fault](https://serverfault.com/search?q=unknown+container+docker+host+hacked) |
| "I found a user or an SSH key I did not create" | persistence after a compromise, or an undocumented change | The first hour | [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=found+unknown+ssh+key+authorized_keys&restrict_sr=1) |
| "Should I just reinstall the server?" | yes, eventually, but after evidence and credential rotation | Rebuild from known-good | [Server Fault](https://serverfault.com/search?q=compromised+server+reinstall) |

### Response lifecycle and roles

**Level:** [L3 · Senior] to know, [L4 · Lead/SRE] to lead

**Concept.** Incident response runs through the same phases whatever the tool or the attacker:

```
 prepare ──► detect & analyse ──► contain ──► eradicate ──► recover ──► learn
    ▲         (section 12)        (isolate,    (rebuild,     (restore,    (postmortem,
    │                              preserve)    rotate)       monitor)     actions)
    └────────────────────── lessons feed the preparation ◄───────────────────┘
```

NIST SP 800-61 Rev. 3 (April 2025) places these activities inside the six functions of the NIST
Cybersecurity Framework 2.0 (Govern, Identify, Protect, Detect, Respond, Recover) and withdrew the
older revision; the practical steps above are unchanged.

The roles from [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 7 still apply, with two
additions, the security lead and legal, and a different emphasis:

| Role | In a security incident | Usually |
|---|---|---|
| Incident commander | decides on containment timing together with the security lead; keeps the timeline moving | senior engineer or lead |
| Security lead | owns the investigation, the evidence and the scope; decides when a host may be wiped | security team, or the most senior engineer trained for it |
| Operations hands | isolate, collect, rotate, rebuild: on instruction, one change at a time, each one logged | you, as the DevOps engineer |
| Communications | need-to-know updates through the out-of-band channel; external messages only through legal | lead or manager |
| Scribe | the UTC timeline, with attacker actions and our actions kept apart | anyone not typing commands |
| Legal and privacy | notification duties, insurers, law enforcement, customer contracts | company function |

Security severities can map onto the same SEV levels:

| Severity | Security meaning (example) |
|---|---|
| SEV1 | confirmed compromise of production, or of credentials with production access; data exposure likely, or an active attacker |
| SEV2 | confirmed compromise of a non-production system, or a suspected production compromise under investigation |
| SEV3 | a blocked or contained attempt that revealed a weakness, e.g. a leaked token revoked before any use |
| SEV4 | informational: scans, noise, policy deviations without exposure |

**Notification clocks** belong to legal and management, but engineers should know they exist,
because they start with awareness, not with the end of the investigation. Examples: under GDPR a
personal-data breach must be reported to the supervisory authority within 72 hours of becoming aware
of it; in India, CERT-In's 2022 directions require listed incident types to be reported within six
hours of noticing them; contracts and cyber-insurance policies often add their own deadlines.

**Key terms**

| Term | Meaning |
|---|---|
| Containment | stopping further damage while keeping evidence |
| Eradication | removing the attacker's access and footholds, usually by rebuilding |
| Dwell time | time from the first attacker activity to detection |
| Out-of-band channel | a communication path that does not depend on the possibly compromised systems |
| Break-glass account | an emergency admin account, stored offline, tested regularly |

**See it on a real system** — a readiness check you can run today. Each line is something that must
already work on the day you need it:

```bash
# break-glass account: present, unexpired, with a password set? (on each critical host)
sudo chage -l breakglass | grep -E 'Account expires|Last password change'
# every host still reporting to the security tooling? (Wazuh server)
sudo /var/ossec/bin/agent_control -l | grep -c Disconnected
# central logs fresh for each host? (log host from section 12)
for d in /var/log/remote/*/; do sudo find "$d" -type f -mmin -15 | grep -q . || echo "stale: $(basename "$d")"; done
```

```
Last password change                                    : Jul 01, 2026
Account expires                                         : never
1
stale: harbor01
```

→ The break-glass account exists and was rotated this quarter. One agent is disconnected and its
logs are 15 minutes stale: harbor01 is invisible right now. Fix it before you need it, because an
incident on the one unmonitored host is the worst kind.

**Hands-on lab (tabletop, 45 minutes, no VM)**

**Step 1 — Build.** With one or two colleagues, take the scenario "the GitLab Runner registration
of the Dokploy host appears in a public paste site" and walk through it on paper: who is incident
commander, who is the security lead, which channel you use, what you check first, and who must be
told by when.

**Step 2 — Break it.** Look for the gaps the walk-through exposed. Typical ones: the contact list is
out of date, the out-of-band channel uses the same company SSO, nobody knows where the runner token
is used, there is no evidence share.

**Step 3 — Fix it.** Turn every gap into a preparation item with an owner and a date, and keep the
list next to the runbooks. Repeat the tabletop every quarter with a different scenario.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| No incident commander | everyone investigates, nobody contains | declare and assign roles | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 7 |
| Host wiped too early | the scope and the entry point can never be established | the security lead decides when to wipe | Evidence preservation |
| Coordination over a compromised channel | the attacker reads the plan | move to the out-of-band channel | this topic |
| Legal told late | a notification deadline missed | the escalation list in the runbook | this topic |

**Why it matters for troubleshooting.** The incident machinery is the same as for outages; what
changes is the order of priorities (evidence and containment before restoring service) and who
decides. Knowing that in advance prevents the most expensive mistake, the "quick cleanup".

**Next step:** the first hour, step by step.

### The first hour

**Level:** [L2 · Mid] as the hands, [L3 · Senior] as incident commander

The scenario: at 03:12 UTC, the custom Wazuh rule from section 12 pages. `deploy` logged in to
web01, the Dokploy host, with a key from 203.0.113.77, not from the VPN range.

**Step 1 — Validate the signal from outside the host.**

**Goal:** confirm what happened from the central logs, without touching web01.

```bash
# on the log host (section 12), or the same search in Grafana or the Wazuh dashboard
sudo grep -h 'Accepted publickey for deploy' /var/log/remote/web01/sshd.log | tail -n 1
sudo grep -h 'sudo: *deploy' /var/log/remote/web01/sudo.log | tail -n 2
```

```
2026-10-03T03:11:58.204511+00:00 web01 sshd[88213]: Accepted publickey for deploy from 203.0.113.77 port 50122 ssh2: ED25519 SHA256:Lk0v3eF7pQm2s9TgXa1bC4dE5fG6hI7jK8lM9nO0pQr
2026-10-03T03:12:40.881002+00:00 web01 sudo:   deploy : TTY=pts/2 ; PWD=/home/deploy ; USER=root ; COMMAND=/usr/bin/docker ps
2026-10-03T03:13:05.120334+00:00 web01 sudo:   deploy : TTY=pts/2 ; PWD=/home/deploy ; USER=root ; COMMAND=/usr/bin/docker service inspect dokploy-postgres
```

**What it means:** the login came from outside the VPN with the key whose fingerprint belongs to the
CI deploy key (check it against your key inventory), and within a minute the session listed
containers and inspected the Dokploy database service, whose definition shows its configuration and,
depending on the Dokploy version, its credentials or the secret names that hold them. That
is not an administrator on a hotel network; it is someone collecting secrets.

**Why this step (now):** alerts can be wrong, and the central copy is evidence the intruder cannot
have edited. Reading it neither alerts the intruder nor changes web01.

**Next step:** real → Step 2. Explained (a colleague confirms it was them) → record it, fix the
policy break, and close it as SEV4. Unclear → treat it as real.

**Step 2 — Declare, assign roles, open the record.**

**Goal:** one person in charge, one timeline, and a channel the intruder cannot read.

```
SEC-2026-007  SEV1 (suspected compromise of production host web01)   declared 03:16 UTC
IC: lead-oncall   Security lead: sec-oncall   Hands: ops-oncall   Comms: eng-manager   Scribe: dev-oncall
Channel: phone bridge, plus the out-of-band workspace; nothing about this in company chat
Rule: no reboots, deletions or cleanup on web01 without the security lead's OK
03:11:58  ATTACKER  key login deploy@web01 from 203.0.113.77 (CI deploy key, SHA256:Lk0v3e...)
03:13:05  ATTACKER  sudo docker service inspect dokploy-postgres
03:16     US        declared SEV1, roles assigned
```

**What it means:** the record separates attacker actions from responder actions; later, that
separation is what makes the postmortem and any legal questions answerable.

**Why this step (now):** without a named commander, several people start "fixing" web01 at the same
time, and every uncoordinated command changes evidence.

**Next step:** Step 3, scope.

**Step 3 — Scope the identity's reach.**

**Goal:** list everything the compromised identity can read or control, because that list is what
you must contain and rotate.

```bash
# on web01: read-only commands, typed by one person, each one noted in the timeline
id deploy
sudo -l -U deploy | tail -n 2
sudo ls -lA /home/deploy/.ssh /home/deploy/.docker /home/deploy/.kube 2>/dev/null | grep -v -e '^total' -e '^$'
```

```
uid=1001(deploy) gid=1001(deploy) groups=1001(deploy),999(docker)
User deploy may run the following commands on web01:
    (root) NOPASSWD: /usr/bin/docker
/home/deploy/.ssh:
-rw------- 1 deploy deploy  402 Sep 12 10:20 authorized_keys
-rw------- 1 deploy deploy  411 Jun  4 08:02 id_ed25519
/home/deploy/.docker:
-rw------- 1 deploy deploy  178 Aug 30 14:51 config.json
```

**What it means:** deploy is in the `docker` group and may run any Docker command as root, which on
this host is full root (section 6). Treat web01 as fully compromised: every container's
environment, Dokploy's database (all apps' environment variables, registry and Git credentials, SSH
keys for remote servers), Traefik's `acme.json` (the private keys of every certificate), deploy's own
SSH private key (which other servers trust it?) and `.docker/config.json` (Harbor credentials).

**Why this step (now):** the containment list and the rotation list both come from this answer.
Underestimating the scope is the most common reason an incident comes back a week later.

**Next step:** Step 4, contain, starting with the live session.

**Step 4 — Contain the identity, keep the host running.**

**Goal:** cut the intruder's access without destroying memory, processes or files.

```bash
# first, one minute of volatile state to the evidence share (full collection follows in Step 5)
ps -fu deploy | sudo tee /mnt/evidence/SEC-2026-007/web01-ps-deploy.txt >/dev/null
sudo ss -tnp | sudo tee /mnt/evidence/SEC-2026-007/web01-ss.txt >/dev/null
# then lock AND expire the account (expiry is what stops key logins), and end its sessions
sudo usermod -L -e 1 deploy
sudo loginctl terminate-user deploy
```

```
(no output: both commands succeed silently)
```

**What it means:** `usermod -L` alone only locks the password. On Ubuntu, where sshd uses PAM, a
locked password does not stop a key login; the expiry date (`-e 1`) does, because PAM's account check
refuses expired accounts. `terminate-user` ends the live session.

**Why this step (now):** an active intruder with root can do more damage every minute, while
cutting the session costs nothing in evidence once the process list is saved.

**Next step:** the incident commander and security lead decide on network isolation (next topic):
web01 serves every production site, so isolating it is an outage. With root already lost and
secrets being read, the usual decision is to isolate now and serve a maintenance page from
elsewhere. Then Step 5.

**Step 5 — Preserve evidence.**

**Goal:** collect volatile state and a disk snapshot before anything else changes, following the
Evidence preservation topic: the collection script to the evidence share, then a hypervisor snapshot
including memory.

**Why this step (now):** once you rotate, rebuild and restore, the host's current state is the only
record of what the intruder did.

**Next step:** Step 6.

**Step 6 — Rotate from a clean machine, highest privilege first.**

**Goal:** make everything in the Step 3 list useless to the intruder: the CI deploy key (the way
in), then the Harbor robot account, Dokploy's admin and stored secrets, the database passwords, and
the TLS certificates, following the Rotating credentials topic.

**Why this step (now):** containment stops the session; rotation stops the next session from
somewhere else with the same secrets.

**Next step:** Step 7.

**Step 7 — First update, then a fixed rhythm.**

**Goal:** the people who need to know, know; nobody else does yet.

```
[SEC-2026-007 update 1, 03:58 UTC]  Status: investigating, SEV1
What we know: unauthorised access to production host web01 at 03:11 UTC using a CI deploy credential.
What we did: access cut at 03:24, host isolated at 03:41, evidence collected, credentials being rotated.
Customer impact: all sites behind web01 show a maintenance page since 03:41.
What we do not know yet: how the credential was obtained; whether data left the host.
Next update: 04:30 UTC, or earlier if anything changes.
```

**Why this step (now):** silence creates rumours and side channels; a fixed rhythm keeps everyone off
the responders' backs.

**Next step:** eradicate by rebuilding, recover, and run the postmortem (the topics below).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Reboot "to be safe" | process list, network connections and memory gone | (none: avoid it) | Evidence preservation |
| Processes killed before they were recorded | no record of what was running | save `ps` and `ss` output first | this topic |
| Locked but not expired | the intruder logs in again with the key | `sudo chage -l USER` | this topic |
| Scope too narrow | the same intruder returns with a secret that was not rotated | redo Step 3 with the security lead | Rotating credentials |
| Investigation on the live host by several people | conflicting changes, polluted evidence | one pair of hands, everything in the timeline | Response lifecycle and roles |

**Why it matters for troubleshooting.** The first hour decides how bad the incident becomes. A
practised sequence (validate, declare, scope, contain, preserve, rotate, communicate) means nobody
has to think about the order at 03:12.

**Next step:** containment options for every layer of your stack.

### Containment

**Level:** [L2 · Mid]

**Concept.** Containment stops further damage while keeping evidence and, where possible, service.
Every option trades one of those three against the others, so choose deliberately and record why:

| Layer | Action | Example | Evidence kept? | Side effect |
|---|---|---|---|---|
| Account | lock and expire, end sessions | `sudo usermod -L -e 1 USER`; `sudo loginctl terminate-user USER` | yes | automation using the account stops |
| SSH key | copy, then move `authorized_keys` aside | `sudo cp -a FILE /mnt/evidence/...`, then `sudo mv FILE FILE.disabled` | yes, if copied first | all logins with that file stop |
| VM network | disconnect the virtual NIC or move it to a quarantine VLAN at the hypervisor | hypervisor console | yes: memory and disk untouched | full outage of that host |
| Host firewall | allow only the forensic workstation and the log host | the nftables quarantine table below | yes | outage; Docker traffic needs care |
| Container | pause it (freezes processes, keeps memory), disconnect its networks | `docker pause C`; `docker network disconnect NET C` | yes | that service degraded |
| Kubernetes pod | take it out of its Service and ReplicaSet, deny all traffic | relabel plus a quarantine NetworkPolicy, below | yes | a clean replacement pod starts |
| Kubernetes node | stop new pods landing on it | `kubectl cordon NODE` | yes | capacity reduced |
| AWS instance | isolation security group, detach from the Auto Scaling group, snapshot volumes | see [Learn: Cloud & AWS](36-learn-cloud-aws.md) section 13 | yes | outage of that instance |

Destructive "containment", such as `docker rm`, scaling a service to zero, terminating an instance
or reinstalling, also stops the attacker, and it destroys the evidence along with them. Use it only
when the security lead agrees the evidence is already safe.

**Host isolation that also covers Docker.** UFW rules do not filter traffic to published container
ports (section 3), so a quarantine needs its own nftables table with drop policies on all three
hooks. A drop in any base chain is final, whatever Docker's own chains say. This one keeps SSH from
the forensic workstation 10.8.0.6 and log shipping to the log host 10.20.0.15:

```bash
# WARNING: apply from the hypervisor console or from 10.8.0.6; any other SSH session is cut.
# Safer first step: schedule a rollback with `at` (section 3), then apply.
sudo nft -f - <<'EOF'
table inet quarantine {
  chain input {
    type filter hook input priority -10; policy drop;
    iif lo accept
    ip saddr 10.8.0.6 accept
    ip saddr 10.20.0.15 tcp sport 6514 ct state established accept
  }
  chain forward {
    type filter hook forward priority -10; policy drop;
  }
  chain output {
    type filter hook output priority -10; policy drop;
    oif lo accept
    ip daddr 10.8.0.6 accept
    ip daddr 10.20.0.15 tcp dport 6514 accept
  }
}
EOF
sudo nft list table inet quarantine | head -n 4
```

```
table inet quarantine {
	chain input {
		type filter hook input priority -10; policy drop;
		iif "lo" accept
```

→ The host keeps running, with memory, processes and disk intact, but it can reach only the
forensic workstation and the log host, and forwarded container traffic is dropped. Keeping the log
stream open means you still see what happens on the host while it is isolated. If the forensic
workstation reaches this host through a WireGuard tunnel that ends **on this host** (section 3),
the table also drops the tunnel's own UDP packets and cuts you off: add
`udp dport 51820 accept` to the input chain and `udp sport 51820 accept` to the output chain (or
allow the workstation's public endpoint address) before you apply it.

**Pod quarantine in Kubernetes.** Removing the label the ReplicaSet and the Service select on makes
the pod an orphan: the ReplicaSet starts a clean replacement and the Service stops sending it
traffic, while the suspect pod keeps running for investigation. A NetworkPolicy that selects the
quarantine label with no allow rules then blocks all its traffic (your CNI must enforce
NetworkPolicy, section 7):

```bash
kubectl -n shop label pod api-6d9f7c8b5-x2k8p app- quarantine=true
kubectl apply -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: quarantine
  namespace: shop
spec:
  podSelector:
    matchLabels:
      quarantine: "true"
  policyTypes: [Ingress, Egress]
EOF
kubectl -n shop get pods -l 'app=api' -o name; kubectl -n shop get pods -l quarantine=true -o name
```

```
pod/api-6d9f7c8b5-7mq2d
pod/api-6d9f7c8b5-x2k8p
```

NetworkPolicies are additive allow-lists, so remove any other labels that existing policies select
on, or they may still allow traffic to the quarantined pod. Cordon the node it runs on, so nothing
new lands next to it.

**Key terms**

| Term | Meaning |
|---|---|
| Isolation | cutting network access while the system keeps running |
| Orphaned pod | a pod no longer selected by its ReplicaSet, which then starts a replacement |
| Tracked connection | in AWS security groups, an existing flow can survive a rule change; a network ACL deny cuts it |
| Maintenance page | a static page served from elsewhere while the real host is isolated |

**Hands-on lab (sec-target, snapshot first)**

**Step 1 — Build.** Run a test container with a published port on sec-target. From sec-scan,
confirm SSH and the web port answer. Prepare a rollback with `at` (section 3).

**Step 2 — Break it: contain the wrong way.** Add `sudo ufw insert 1 deny from 192.168.56.22` (at
the top, so no earlier allow rule matches first) and test from
sec-scan: SSH is blocked, but the container's published port still answers, because UFW does not
filter forwarded Docker traffic. Your "isolation" leaks.

**Step 3 — Fix it.** Remove the UFW rule, apply the quarantine table above with sec-scan's address as
the forensic workstation, and confirm from a third machine that nothing answers, while sec-scan
still has SSH. Delete the table afterwards (`sudo nft delete table inet quarantine`) or restore the
snapshot.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| UFW used for isolation | published container ports still reachable | `sudo nft list ruleset | grep -c DOCKER` | section 3 |
| Isolation also cut logging | the host goes dark in central logs | allow the log host in the quarantine table | this topic |
| Responder locked out | the isolation dropped your own session | hypervisor console; the `at` rollback | section 3 |
| Quarantined pod still talks | another NetworkPolicy allows it by a remaining label | `kubectl get networkpolicy -n NS -o yaml` | section 7 |
| Scaled to zero to "contain" | container and writable layer gone | (prevent: pause or isolate instead) | Evidence preservation |

**Why it matters for troubleshooting.** Every containment option is a firewall, label or account
change you already know from troubleshooting. The new part is choosing the one that keeps evidence,
and knowing which shortcut (UFW on a Docker host) leaks.

**Next step:** collect the evidence while the system is contained.

### Evidence preservation

**Level:** [L2 · Mid] to collect, [L3 · Senior] to own the process

**Concept.** Collect in **order of volatility** (RFC 3227): what disappears first goes first. Memory
and running state (processes, network connections, logged-in users) come before temporary files,
which come before the disk, while logs already shipped off the host (section 12) are safe where they
are. Five rules make the collection usable later:

1. **Write to external storage**, never to the compromised disk: an evidence share or an encrypted USB disk.
2. **Hash everything** (`sha256sum`) and record the hashes somewhere else as well, such as the incident record, so later changes are detectable.
3. **Keep a chain of custody:** who collected what, when, how, and where it is stored.
4. **Minimise your footprint:** do not install tools on the victim, and note every command you run, because each one changes the system a little.
5. **Do not trust the host's own binaries** if root was compromised: they can lie. Prefer a hypervisor snapshot (disk and memory) analysed on another machine, and leave memory forensics to specialists. On Proxmox, for example, `qm snapshot VMID NAME --vmstate 1` includes the memory.

**Key terms**

| Term | Meaning |
|---|---|
| Order of volatility | collect the most short-lived data first |
| Chain of custody | the record that shows evidence was handled without tampering |
| Hash manifest | a list of SHA-256 hashes of every collected file |
| `docker diff` | the files a container added (A), changed (C) or deleted (D) compared with its image |

**See it on a real system** — a read-only collection script, run as root from the evidence share
and writing only to it:

```bash
#!/usr/bin/env bash
# collect-volatile.sh CASE_ID: read-only collection to /mnt/evidence/CASE_ID/HOST-TIMESTAMP
set -u
CASE=${1:?usage: collect-volatile.sh CASE_ID}
OUT=/mnt/evidence/$CASE/$(hostname)-$(date -u +%Y%m%dT%H%M%SZ)
mkdir -p "$OUT" && exec 2>>"$OUT/errors.log"
run() { local name=$1; shift; { echo "== $(date -u +%FT%TZ) $*"; "$@"; } > "$OUT/$name.txt"; }
run date         date -u
run uptime       uptime
run who          w
run last         last -Fiwx -n 200
run ps           ps auxwwf
run ss           ss -tunap
run ip-addr      ip -br addr
run ip-route     ip route show table all
run lsof-net     lsof -nPi
run deleted-exe  bash -c "ls -l /proc/[0-9]*/exe 2>/dev/null | grep '(deleted)'"
run modules      lsmod
run mounts       findmnt -A
run cron         bash -c 'cat /etc/crontab; ls -la /etc/cron.* /var/spool/cron/crontabs'
run recent-etc   find /etc /usr/local /var/spool/cron -xdev -type f -mtime -7 -printf '%TY-%Tm-%Td %TT %u %m %p\n'
run docker-ps    docker ps -a --no-trunc
run docker-svc   docker service ls
(cd "$OUT" && sha256sum ./*.txt > SHA256SUMS)
echo "collected into $OUT; record this manifest hash in the incident: $(sha256sum "$OUT/SHA256SUMS")"
```

For a suspect container, add its own evidence before you pause or remove anything:

```bash
C=shop-api.1.k3x9p0q7r2s4; E=/mnt/evidence/SEC-2026-007/containers
docker inspect "$C" > "$E/$C.inspect.json"
docker diff "$C" > "$E/$C.diff.txt"
docker logs --timestamps "$C" > "$E/$C.log" 2>&1
docker export "$C" -o "$E/$C.fs.tar"
sha256sum "$E/$C".* >> "$E/SHA256SUMS"
```

And for a pod: `kubectl get pod POD -o yaml`, `kubectl logs POD --all-containers --timestamps`
(plus `--previous` after a restart), `kubectl get events -n NS --sort-by=.lastTimestamp`, the API
audit log for the time window, and on the node `sudo crictl ps -a` and `sudo crictl inspect ID`.

Sample results:

```
collected into /mnt/evidence/SEC-2026-007/web01-20261003T034402Z; record this manifest hash in the incident: 9f2c4e1ab07d3c5e8f6a2b9d0c1e4f7a8b3c6d9e0f1a2b5c8d7e4f3a6b9c0d1e  /mnt/evidence/SEC-2026-007/web01-20261003T034402Z/SHA256SUMS
C /etc
A /etc/cron.d
A /etc/cron.d/sys-update
C /tmp
A /tmp/.x
A /tmp/.x/config.json
```

→ The manifest hash goes into the incident record. The `docker diff` output is a good start for the
investigation: the container gained a hidden directory under `/tmp` and a cron file, neither of
which belongs in an image built by the pipeline. Do not open or run anything you find; hand it to
the security lead.

A chain-of-custody log can be as simple as lines in the incident record:

```
SEC-2026-007 evidence log
2026-10-03T03:44Z  volatile collection web01 → evidence share .../web01-20261003T034402Z  manifest 9f2c4e1a...  by ops-oncall
2026-10-03T03:51Z  container shop-api.1.k3x9p0q7r2s4: inspect, diff, logs, export  manifest appended  by ops-oncall
2026-10-03T03:55Z  Proxmox snapshot of web01 "sec-2026-007" including memory  by ops-oncall, verified by sec-oncall
2026-10-03T04:05Z  evidence share switched to read-only for everyone except sec-oncall
```

**Hands-on lab (sec-target, with an NFS export on sec-scan as the evidence share)**

**Step 1 — Build.** Export a directory from sec-scan, mount it on sec-target at `/mnt/evidence`, and
run the script with a test case ID. Check the manifest with `sha256sum -c SHA256SUMS` on sec-scan.

**Step 2 — Break it.** Start a test container, create a file inside it, then "clean up" first: `docker
rm -f` the container and reboot sec-target. Now try to answer: which processes were running, which
connections were open, what did the container change? Nothing is left to answer with.

**Step 3 — Fix it.** Repeat in the right order: container evidence, the volatile script, a VM
snapshot, and only then removal. Time yourself: the target is under ten minutes from "go" to a
hashed evidence set.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Evidence written to the victim's disk | deleted data overwritten, evidence on a disk you do not trust | always write to `/mnt/evidence` | this topic |
| No hashes | integrity cannot be shown later | `sha256sum -c SHA256SUMS` | this topic |
| Mixed time zones | timeline steps out of order | `date -u` in every file, UTC in the record | [Time & NTP](12-time-ntp.md) |
| Tools installed on the victim | package logs and files changed by the responder | use the share and preinstalled tools only | this topic |
| `docker events` history gone | the daemon keeps only a short history | ship the stream continuously (section 12) | section 12 |

**Why it matters for troubleshooting.** The collection script is also a perfect snapshot of a
misbehaving host for a normal outage: processes, sockets, mounts and recent changes in one hashed
folder you can study without time pressure.

**Next step:** make everything the intruder could read worthless.

### Rotating credentials

**Level:** [L2 · Mid] to execute, [L3 · Senior] to plan

**Concept.** Assume every secret the compromised identity could read is known to the intruder.
Rotation means: issue a new secret, deploy it to every consumer, verify, then revoke the old one.
When there is active abuse, revoke first and accept the outage. Do it from a clean workstation, from
the highest privilege down, and keep a **rotation register**: secret, where it is used, owner,
rotated at, verified by.

What root on a Dokploy host exposes, in rotation order:

| Order | Secret | Where it lives | Rotate how |
|---|---|---|---|
| 1 | the entry credential (here the CI deploy key) | GitLab CI variable, `authorized_keys` on hosts | new key pair from a clean workstation; remove the old public key everywhere with Ansible |
| 1 | cloud and cluster admin credentials used on the host | `~/.aws`, environment variables, `~/.kube/config` | deactivate keys, revoke role sessions, issue new kubeconfigs |
| 2 | private CA intermediate, if it lives on this host | `/etc/step-ca/secrets` | revoke it, issue a new intermediate, reissue leaf certificates (section 4) |
| 2 | registry credentials and Harbor robot accounts | `~/.docker/config.json`, Dokploy registry settings | refresh the robot secret, update consumers |
| 2 | GitLab Runner token | `/etc/gitlab-runner/config.toml` | reset the runner's token (API or UI) and register the rebuilt runner |
| 2 | Dokploy admin password, API tokens, Git provider tokens, SSH keys for remote servers | Dokploy's database | change and recreate from a clean browser session |
| 3 | application secrets: database passwords, API keys, SMTP | container environment, Dokploy environment, `.env` files | new values, redeploy; dual-user rotation for databases |
| 3 | TLS private keys | Traefik's `acme.json` | keep a copy as evidence, reissue, revoke the old certificates as "key compromise" |
| 4 | SSH host keys | `/etc/ssh/ssh_host_*` | the rebuilt host gets new ones; update `known_hosts` or your SSH CA |

**Key terms**

| Term | Meaning |
|---|---|
| Rotation with overlap | the new secret works before the old one stops, so consumers switch without an outage |
| Dual-user rotation | two database users alternate: create B, switch the app to B, then remove A |
| Session revocation | invalidating credentials already issued, e.g. AWS role sessions issued before a timestamp |
| Rotation register | the list that proves every exposed secret was replaced |

**See it on a real system** — the exposure inventory of a host (read-only, lists paths and counts,
never values), then examples of rotation run from a clean workstation:

```bash
sudo ls -l /etc/gitlab-runner/config.toml /root/.docker/config.json /home/*/.docker/config.json /home/*/.kube/config 2>/dev/null
sudo find / -xdev \( -name 'id_ed25519' -o -name 'id_rsa' -o -name '*.key' -o -name 'acme.json' -o -name '.env' \) \
  -printf '%m %u %p\n' 2>/dev/null | head -n 8
docker ps -q | xargs -r docker inspect --format '{{.Name}}: {{len .Config.Env}} environment variables'
```

```
-rw------- 1 root   root    512 Sep  1 09:14 /etc/gitlab-runner/config.toml
-rw------- 1 deploy deploy  178 Aug 30 14:51 /home/deploy/.docker/config.json
600 deploy /home/deploy/.ssh/id_ed25519
600 root /etc/dokploy/traefik/dynamic/acme.json
600 root /etc/ssh/ssh_host_ed25519_key
640 root /opt/shop/.env
/dokploy-traefik: 3 environment variables
/shop-api.1.k3x9p0q7r2s4: 14 environment variables
```

```bash
# GitLab Runner: reset its token through the API (admin token from your password manager),
# then put the new token into config.toml on the REBUILT runner host only
curl -s --request POST --header "PRIVATE-TOKEN: $GITLAB_ADMIN_TOKEN" \
  "https://gitlab.example.com/api/v4/runners/42/reset_authentication_token" | jq -r '.token_expires_at'
# AWS: deactivate the key first; delete it after the investigation has used CloudTrail
aws iam update-access-key --user-name ci-deploy --access-key-id AKIAIOSFODNN7EXAMPLE --status Inactive
# PostgreSQL: \password prompts, so the new password never lands in shell history or server logs
psql -h db.example.com -U postgres -c '\password shop_app'
```

For AWS role credentials that were already issued, attach a deny policy for sessions issued before
the containment time; the IAM console's "Revoke active sessions" button adds exactly this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Deny",
      "Action": "*",
      "Resource": "*",
      "Condition": { "DateLessThan": { "aws:TokenIssueTime": "2026-10-03T03:30:00Z" } }
    }
  ]
}
```

→ The inventory gives the rotation register its rows: the runner token, Harbor credentials, deploy's
private key, every certificate key in `acme.json`, the host keys, an application `.env`, and the
environment of every container. The commands show the pattern: new credential, update consumers,
revoke or deactivate the old one, and never print a secret value on screen.

**Hands-on lab (sec-reg Harbor, a test app on sec-target)**

**Step 1 — Build.** Create a Harbor robot account, use it for `docker login` on sec-target and in a
GitLab CI variable, and list both consumers in a rotation register.

**Step 2 — Break it: rotation outage.** Refresh the robot's secret in Harbor and update only the CI
variable. The next deploy on sec-target fails with `unauthorized`, because one consumer still has
the old secret.

**Step 3 — Fix it with overlap.** Create a second robot account, switch every consumer from the
register to it, verify each one with a pull, and only then disable the first robot. Record the
rotation, with times and who verified it.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| A consumer missed | `unauthorized` or `401` after rotation | the rotation register | this topic |
| Rotated on the compromised host | the intruder reads the new secret too | rotate from a clean workstation | this topic |
| Old secret never revoked | both the old and the new one work | provider's credential list (`aws iam list-access-keys`) | this topic |
| Kubernetes client certificate leaked | cannot be revoked; it works until it expires | rotate the cluster CA, investigate | section 7 |
| CA root key leaked | every certificate it ever signed is suspect | new root, redistribute trust (section 4) | section 4 |

**Why it matters for troubleshooting.** Rotation outages are among the most common self-inflicted
outages, in incidents and in routine work alike. A register of consumers turns "who still uses the
old token?" into a checklist.

**Next step:** replace the compromised system with a known-good one.

### Rebuild from known-good

**Level:** [L2 · Mid] to execute, [L3 · Senior] to design for it

**Concept.** You cannot prove that a root-compromised host is clean, so you do not try. Eradication
is a **rebuild**: a fresh OS from a verified image, configuration from Git (Ansible), applications
from signed images by digest (section 8), data from backups taken before the compromise, and secrets
that were rotated (previous topic). The way in is closed first, and monitoring is raised for weeks
afterwards. A team that can rebuild a host from zero in an hour can afford to treat every
compromised host this way.

The **known-good point** comes from the timeline: the last backup before the earliest attacker
activity. If the start is unknown, restore data only (not system state), into an isolated network,
and inspect it before it goes live. For Dokploy: if the panel itself was the way in, recreate the
projects from your Git repositories with rotated secrets, rather than restoring its database
wholesale. If you must restore it, review users, SSH keys, registries and Compose definitions first.
In Kubernetes, drain and delete a compromised node and join a freshly built one with a new bootstrap
token, then review cluster-level objects an intruder might have added (DaemonSets, role bindings,
admission webhooks, CronJobs).

**Key terms**

| Term | Meaning |
|---|---|
| Known-good point | the most recent state you can show predates the compromise |
| Golden image | a verified base image (VM template or AMI) built by a pipeline |
| Heightened monitoring | extra detections on the incident's indicators for a period after recovery |
| Indicator of compromise (IOC) | an observable left by the incident: an IP, a file hash, a key fingerprint |

**See it on a real system** — checks on the rebuilt platform before it takes traffic:

```bash
# is production running exactly what the pipeline signed?
docker service inspect --format '{{.Spec.Name}} {{.Spec.TaskTemplate.ContainerSpec.Image}}' shop-api
cosign verify --key cosign.pub harbor.example.com/shop/api@sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c > /dev/null && echo "signature OK"
# Kubernetes: cluster-level objects to compare with the Git baseline
kubectl get clusterrolebindings,mutatingwebhookconfigurations,validatingwebhookconfigurations -o name | sort > objects-now.txt
diff objects-baseline.txt objects-now.txt
```

```
shop-api harbor.example.com/shop/api:1.8.1@sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c
signature OK
61a62
> clusterrolebinding.rbac.authorization.k8s.io/system-metrics-reader
```

→ The service runs the signed digest. The cluster has one role binding that is not in the Git
baseline, with a name chosen to look like a system object: find out who created it from the API
audit log (section 7) before deleting it, and add its name to the incident's indicators.

**Hands-on lab (sec-target, rebuild instead of repair)**

**Step 1 — Build.** Write, or reuse from [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md), an Ansible
playbook that takes a fresh Ubuntu 24.04 VM to a working sec-target: users, SSH hardening, UFW,
Docker, and the test app from a signed image digest.

**Step 2 — Break it.** Time a rebuild from a fresh VM. Typical first results: a manual step nobody
wrote down, a secret only present on the old host, or a dependency on a package version that no
longer exists.

**Step 3 — Fix it.** Fix each gap in the playbook until a rebuild runs unattended, and record the
time. That number is your real eradication time.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Backup restored from after the compromise | the intruder's foothold returns | timeline vs backup dates | this topic |
| Old secrets reused on the new host | the intruder logs in to the new host | rotation register | Rotating credentials |
| Way in not closed | the same weakness is used again | the postmortem's root cause, fixed first | Security postmortem |
| Old host destroyed too early | investigation cannot finish | the security lead releases it | Evidence preservation |
| Rebuild depends on the old host | missing files, keys or configuration | an unattended rebuild test | this topic |

**Why it matters for troubleshooting.** The same rebuild capability turns a corrupted or hopelessly
misconfigured host in a normal outage into a one-hour job instead of a day of repairs.

**Next step:** keep everyone informed without telling the wrong people.

### Incident communication

**Level:** [L3 · Senior] to draft, [L4 · Lead/SRE] to own

**Concept.** Communication in a security incident follows four rules. **Need to know:** inform the
people who must act or decide, not the whole company. **Out of band:** until the scope is known,
assume email, company chat and the ticket system may be read by the intruder. **Facts, not
speculation:** say what is known, what was done, what is not yet known, and when the next update
comes. **One external voice:** messages to customers, regulators and the public go through legal
and management, never from an engineer directly.

**Key terms**

| Term | Meaning |
|---|---|
| Update rhythm | fixed times for updates (every 30–60 minutes for SEV1), even when nothing changed |
| Holding statement | a short, factual external message prepared before details are known |
| Single source of truth | the incident record that every update is written from |

**See it on a real system** — a later internal update, and a customer holding statement drafted for
legal to approve:

```
[SEC-2026-007 update 3, 05:30 UTC]  Status: contained, SEV1
Known: access came through a CI deploy key that was stored in a project's job artifacts in August.
Done: key revoked, all secrets readable on web01 rotated (register: 14 of 14 verified), web01 isolated,
      replacement host web02 built from Git and signed images, sites restored at 05:12.
Not yet known: whether data left web01 (network logs under review with the security lead).
Next update: 07:00 UTC.
```

```
On 3 October 2026 we detected unauthorised access to one of our servers. We contained it within the
hour, replaced the affected system and changed the related credentials. Our investigation is ongoing.
We will update you by [DATE] and contact you directly if your data is affected.
```

→ The internal update is written from the incident record and names numbers, not impressions. The
external statement promises nothing the investigation has not proven ("no data was accessed" is
never said before the evidence supports it).

**Hands-on lab (paper)**

**Step 1 — Build.** For the game day at the end of this area, prepare three templates: the internal
update, the management summary and the holding statement.

**Step 2 — Break it.** Write update 1 from the scenario in "The first hour", then check it for
speculation, blame, names of suspects and technical indicators that should not leave the incident
channel.

**Step 3 — Fix it.** Rewrite it so that a manager can read it in thirty seconds, and store the
templates with the runbooks.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Updates stop | stakeholders open side channels and ask the responders directly | a fixed update rhythm | this topic |
| Speculation shared | a guess is repeated as fact, then retracted | the known / unknown structure | this topic |
| Plan discussed on a compromised channel | the intruder changes tactics | the out-of-band channel | Response lifecycle and roles |
| Engineer talks to a customer directly | statements that conflict with the official one | route through comms and legal | this topic |

**Why it matters for troubleshooting.** The same templates work for outages
([CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 7): calm, regular, factual updates are what
make people trust the responders.

**Next step:** learn from it without blame.

### Security postmortem

**Level:** [L3 · Senior] to write, [L4 · Lead/SRE] to run

**Concept.** A security postmortem follows the same blameless rules as any postmortem
([CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 7, [Senior architecture](39-learn-senior-architecture.md)
section 11): people acted on the information they had, and the goal is to change the system. Three
parts are specific to security:

- **Two timelines.** Attacker actions and responder actions, side by side, from which three numbers follow: **dwell time** (first attacker activity to detection), **time to contain** and **time to recover**.
- **Detection gap analysis.** For each attacker step: which control should have prevented it, which detection should have fired, and why it did not (no log source, no rule, an alert routed to nobody).
- **Exposure accounting.** Which data and which credentials were exposed, which were rotated (the register), which notifications were made and when.

Action items fall into three classes, **prevent**, **detect** and **respond**, each with an owner
and a due date, tracked until closed. Indicators of compromise and evidence stay in the restricted
incident record; the version shared widely is sanitised.

**Key terms**

| Term | Meaning |
|---|---|
| Dwell time | how long the intruder was inside before anyone noticed |
| Detection gap | an attacker step that no alert caught |
| Contributing factor | a condition that made the incident possible or worse, without being the single cause |
| Sanitised version | the postmortem without indicators, secrets or personal data, for wide sharing |

**See it on a real system** — an excerpt for a classic community scenario, a crypto-miner on a
staging Docker host (fictional, condensed):

```
SEC-2026-004  Crypto-miner on staging host stg01  (SEV2, closed)
Summary: a debug change exposed the Docker API on TCP 2375 without TLS. Within two days an automated
  scan found it and started mining containers. Detected 3 days later by a CPU alert, not by security tooling.
Dwell time: 3 d 4 h      Time to contain: 22 min      Time to recover: 5 h (rebuild from Ansible)
Timeline (UTC, attacker | us):
  09-12 14:02  us        change "temporary remote Docker access for debugging" (no change request)
  09-14 03:17  attacker  first container created through the API on 2375
  09-17 07:40  us        alert "stg01 CPU > 95% for 30 min"; on-call sees unknown containers
  09-17 08:02  us        host isolated (quarantine table), evidence collected, SEV2 declared
Detection gaps:
  - no alert on a new listening port: the weekly nmap diff (section 3) was not running for staging
  - no alert on unknown images: docker events not shipped from staging (section 12)
Actions:
  prevent  remove tcp://0.0.0.0:2375 from all daemon configs; CI check on daemon.json   owner ops   due 09-24
  detect   nmap diff + docker events shipping for staging too                          owner ops   due 10-01
  respond  add "unknown container" scenario to the runbook and the game day             owner lead  due 10-15
```

→ The root cause is a configuration change, not the miner; the detection gaps explain the three
days; and the actions close the class of problem (any exposed daemon, any unknown image), not just
this host.

**Hands-on lab (after the game day)**

**Step 1 — Build.** Write the postmortem for the game day below using this structure, within two
working days.

**Step 2 — Break it.** Review it with a colleague, looking for blame ("X forgot to..."), actions
without owners or dates, and attacker steps that are missing from the detection gap list.

**Step 3 — Fix it.** Rewrite blame as conditions ("the change process allowed a debug change
without review"), give every action an owner and a date, and publish the sanitised version in your
runbook repository.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Only the attacker's last step analysed | the way in stays open | a full attacker timeline | this topic |
| Actions never closed | the same incident class returns | action tracking in the issue tracker | [Senior architecture](39-learn-senior-architecture.md) section 11 |
| Blame | people hide mistakes next time | blameless review | this topic |
| Indicators published widely | the intruder learns what you know | sanitised version only | this topic |

**Why it matters for troubleshooting.** Detection gap analysis is the security version of "what
would have made this faster to diagnose?", and its answers improve your operational monitoring too.

**Next step:** practise all of it in a game day.

### Lab: security game day

**Level:** [L3 · Senior] to run, every stage to play

**Concept.** A game day practises the whole response on a system that looks compromised but is
safe. A facilitator plants harmless indicators of compromise on a snapshotted lab VM and keeps a
sealed answer key; the responders only get the first alert. Each planted item is detectable by a
section 12 control, so the game day also tests your detections. Nothing here is an attack technique:
the items are ordinary administrative changes, made by the facilitator, that look out of place.

**Key terms**

| Term | Meaning |
|---|---|
| Facilitator | plants the indicators, holds the answer key, keeps time, does not help |
| Sealed answer key | the list of planted items, opened only at the end |
| Inject | an extra event the facilitator adds during the exercise ("a customer reports a strange email") |

**See it on a real system** — the facilitator's preparation on a snapshot of sec-target (benign
items only; the curl target is a documentation address that goes nowhere):

```bash
# facilitator only, on a snapshot; write the answer key on your own laptop, not on the VM
sudo useradd -m -s /bin/bash -G sudo support2
echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIGameDayTestKeyNotARealKey00000000000000000 gameday' \
  | sudo tee -a /home/deploy/.ssh/authorized_keys >/dev/null
echo '*/10 * * * * root curl -s -m 5 http://203.0.113.50/ping >/dev/null 2>&1' | sudo tee /etc/cron.d/sys-update >/dev/null
docker run -d --name metrics-agent -v /var/run/docker.sock:/var/run/docker.sock:ro alpine:3.20 sleep infinity
```

Expected detections, for the answer key:

| Planted item | Should be caught by | Section |
|---|---|---|
| new user `support2` in the sudo group | auditd `identity` key, Wazuh, auth log `useradd` lines | 2, 12 |
| extra key for deploy | auditd `ssh_keys`, Wazuh FIM rule 550 | 12 |
| cron file contacting 203.0.113.50 | auditd `persistence`, Wazuh FIM, outbound connection attempts in the firewall log | 12 |
| container with the Docker socket | the `DockerSocketMountsChanged` alert | 12 |

**Hands-on lab (two to three hours, sec-target, sec-scan and the log host)**

**Step 1 — Build.** The facilitator snapshots sec-target, plants the items at a random time, and
notes the time. The responders follow this area: validate, declare, scope, contain, preserve, rotate,
rebuild and communicate, with a scribe keeping the timeline.

**Step 2 — Break it on purpose.** The facilitator adds one inject halfway: "the deploy key also
works on sec-reg", which widens the scope and tests whether the rotation register is updated.

**Step 3 — Fix and score.** Open the answer key. Score: time to detect each item, time to contain,
whether the evidence set is hashed and complete, whether every exposed secret is in the rotation
register, and which items no alert caught. Restore the snapshot, write the postmortem (previous
topic), and turn every missed detection into an action item.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| An item never detected | found only in the answer key | the detection gap list | section 12 |
| "Cleaned up" before evidence | items deleted, no evidence set | the evidence order | Evidence preservation |
| Inject ignored | sec-reg never checked | scope again after every new fact | The first hour |
| Game day never repeated | skills fade, runbooks rot | a quarterly calendar entry | this topic |

**Why it matters for troubleshooting.** The ops-ladder L4 game day (in
[CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 8) trains outage response; this one trains the
security version. Together they make both kinds of incident feel familiar.

**Next step:** show auditors the evidence that all of this happens.

---

## 14. Compliance basics for engineers

> 📚 **Study path:** 1) Note: [Senior architecture](39-learn-senior-architecture.md) section 13, *Compliance as evidence*, for the Lead view of the same subject · 2) Reading: the [CIS Controls](https://www.cisecurity.org/controls) (v8.1) and the [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks) you already used with Lynis in section 2 · 3) KodeKloud: the verified map has no compliance course; the closest useful lesson is *Fundamentals of SRE* — [Change Management for Reliability](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page), because change control is the control auditors test most ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 4) Practice: the quarterly evidence pack lab at the end of this area, on your homelab.

Engineers rarely write security policies, but they operate most of the controls those policies
promise, and they are the ones who can produce the proof. The good news: the frameworks overlap
heavily, and if you do what sections 2 to 13 describe and keep the records, you can answer most of
what an auditor asks. This area explains the frameworks in one page, maps the controls you already
operate onto them, shows how to produce evidence that stands up, lists what auditors typically ask
DevOps for, and ends with a quarterly evidence pack you build yourself.

**Field notes: what engineers actually ask**

| What people post | What is usually going on | Topic here | Search |
|---|---|---|---|
| "We are starting SOC 2. What does DevOps actually have to do?" | operate controls for the whole observation period and keep the records | ISO 27001, SOC 2 and CIS | [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=soc+2+devops+evidence&restrict_sr=1) |
| "The auditor wants every production change for the year" | change management is tested by sampling; changes outside Git have no record | What auditors ask DevOps for | [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=auditor+change+management+evidence&restrict_sr=1) |
| "How long do we have to keep logs for ISO 27001?" | the standard asks you to decide and justify; contracts and laws set the numbers | Controls engineers operate | [Server Fault](https://serverfault.com/search?q=log+retention+compliance) |
| "Are screenshots acceptable evidence?" | yes, but exports with the query and a date are stronger | Evidence collection | [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=audit+evidence+screenshots&restrict_sr=1) |

### ISO 27001, SOC 2 and CIS

**Level:** [L3 · Senior] for awareness, [L4 · Lead/SRE] for working knowledge

**Concept.** Three names come up again and again, and they are different kinds of thing:

| | ISO/IEC 27001:2022 | SOC 2 | CIS Controls v8.1 | CIS Benchmarks |
|---|---|---|---|---|
| What it is | a certifiable standard for an information security management system (ISMS) | an attestation report by a CPA firm against the AICPA Trust Services Criteria | a prioritised set of 18 control groups with safeguards | hardening guides per product: Ubuntu, Docker, Kubernetes and more |
| What you get | a certificate, on a three-year cycle with yearly surveillance audits | a report: Type I (controls designed, at one date) or Type II (controls operated over a period, often 3–12 months) | a self-assessed maturity, by Implementation Group (IG1 to IG3) | scored checks at Level 1 or Level 2 |
| Who asks for it | enterprise customers and tenders worldwide | customers of SaaS companies, especially in the US | internal programmes, insurers, as a practical baseline | auditors and your own hardening (section 2, kube-bench in section 7) |
| Your part as an engineer | operate the Annex A controls in scope, keep records | operate the controls throughout the period, provide samples | implement the safeguards | run the benchmark scans, fix or justify findings |

**ISO 27001:2022** has a management-system part (clauses 4 to 10: context, leadership, risk
assessment and treatment, objectives, internal audit, management review, improvement) and Annex A
with 93 controls in four themes: 37 organisational, 8 people, 14 physical and 34 technological.
The **Statement of Applicability** (SoA) records which controls apply and why. The transition from
the 2013 edition ended on 31 October 2025, so current certificates cite the 2022 edition. Risk treatment
offers four choices (modify the risk with controls, retain or accept it, avoid it, share it), and
"retain" with a named owner is a legitimate answer: that is what section 11's exceptions register
records, and it answers the threat-model question from section 1 about risks that are accepted
rather than mitigated.

**SOC 2** reports against the **Trust Services Criteria**: Security (the common criteria, CC1 to
CC9, always included) plus optional Availability, Processing Integrity, Confidentiality and Privacy.
In a Type II report, the auditor tests samples across the whole period, so one missed quarterly
access review shows up as an **exception** in the report. When you rely on a provider such as AWS,
its own SOC 2 report lists **complementary user entity controls** (CUECs): things the provider
assumes you do, such as managing your own IAM users. Those are yours to operate.

**Key terms**

| Term | Meaning |
|---|---|
| ISMS | the management system: policies, risk process, roles and reviews, not just technical controls |
| Statement of Applicability | the list of Annex A controls in scope, with the reason for each inclusion or exclusion |
| Nonconformity | an ISO audit finding: minor (a lapse) or major (a control missing or failing) |
| Observation period | the time a SOC 2 Type II report covers |
| Exception (SOC 2) | a tested sample where the control did not operate as described |
| CUEC | a control the service provider expects you, the customer, to operate |

**See it on a real system** — in your organisation, rather than on a host. Five things to look up
this week, and where they usually live:

| Question | Usually found in |
|---|---|
| Which frameworks do we hold or promise customers? | the company's trust or security page, sales contracts |
| What is in scope (systems, locations, teams)? | the ISO scope statement or the SOC 2 system description |
| Which controls do I or my team own? | the control matrix kept by the compliance owner |
| When is the next audit, and what period does it cover? | the compliance calendar |
| Where does evidence go? | a GRC tool, an evidence repository or a shared drive |

**Hands-on lab (paper, 30 minutes)**

**Step 1 — Build.** Answer the five questions for your real workplace, or for an imagined company
that hosts customer apps on your Dokploy platform.

**Step 2 — Break it.** Find one system you operate that is in scope but that nobody listed in the
control matrix, for example the GitLab Runner host, the Wazuh server or the homelab-style tooling
host everyone forgot.

**Step 3 — Fix it.** Write a short note to the compliance owner: the system, what it does, which
controls apply to it, and who operates them.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| "We are ISO certified, so we are secure" | a certificate whose scope excludes your systems | read the scope statement | this topic |
| Scope surprise | a system you run turns out to be in scope a week before the audit | the system description | this topic |
| One missed review | a SOC 2 Type II exception | the control calendar | Evidence collection |
| CUECs ignored | provider controls assumed to cover your side too | the provider's SOC 2 report, CUEC section | section 10 |

**Why it matters for troubleshooting.** Knowing which framework a system falls under explains many
"why must I do this?" moments, from change tickets to access reviews, and helps you push back with
precise questions instead of frustration.

**Next step:** map the controls you already operate.

### Controls engineers operate

**Level:** [L3 · Senior]

**Concept.** Most controls in all three frameworks are things this module has already taught. The
mapping below is indicative, because the authoritative mapping is your compliance owner's control
matrix, but it shows how one piece of work satisfies several frameworks at once:

| Control area | What you do (this module) | ISO 27001:2022 Annex A | SOC 2 | CIS Controls v8 | Evidence |
|---|---|---|---|---|---|
| Asset inventory | inventory file, Ansible inventory, Dokploy projects (section 11) | 5.9 | CC6.1 | 1, 2 | dated inventory export |
| Secure configuration | Lynis and CIS benchmarks, kube-bench, hardened images (sections 2, 6, 7) | 8.9 | CC7.1 | 4 | scan reports, configuration in Git |
| Access control and reviews | users and sudo, docker group audit, RBAC, IAM (sections 2, 6, 7, 10) | 5.15, 5.18, 8.2 | CC6.1, CC6.2, CC6.3 | 5, 6 | review records, removal tickets |
| Authentication and MFA | key-only SSH, SSO with MFA for GitLab and AWS (sections 2, 10) | 5.17, 8.5 | CC6.1 | 6 | MFA settings, AWS credential report |
| Cryptography and TLS | private CA, rotation, TLS settings (sections 4, 9) | 8.24 | CC6.7 | 3 | certificate inventory with expiry, TLS scan results |
| Secrets management | gitleaks, protected variables, Vault, sops (section 5) | 5.17, 8.24 | CC6.1 | 3 | scanner reports, access policies |
| Vulnerability management | triage, patch windows, rebuilds, exceptions (section 11) | 8.8 | CC7.1 | 7 | scan reports, SLA metrics, exceptions register |
| Malware and runtime protection | Wazuh, Falco, Harbor policies (sections 6, 12) | 8.7 | CC6.8 | 10 | agent coverage report |
| Logging and monitoring | central logs, detections, alert routing (section 12) | 8.15, 8.16, 8.17 | CC7.2, CC7.3 | 8, 13 | retention settings, sample alerts with their tickets |
| Network security | UFW and DOCKER-USER, segmentation, nmap diffs (section 3) | 8.20, 8.22 | CC6.6 | 12, 13 | rule exports, review records, scan diffs |
| Change management | merge requests, change requests ([CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) section 7) | 8.32 | CC8.1 | – | merge request approvals linked to deploys |
| Secure development and CI | SAST, scanning, signing (section 8) | 8.25, 8.28 | CC8.1 | 16 | pipeline definitions, scan results |
| Backup and recovery | backups and restore tests ([Databases](38-learn-databases-ops.md)) | 8.13, 5.30 | A1.2, A1.3 | 11 | restore-test records |
| Incident management | response, evidence, postmortems (section 13) | 5.24 to 5.28 | CC7.3, CC7.4, CC7.5 | 17 | incident records, postmortems, game day reports |
| Cloud services | account baseline, CloudTrail, GuardDuty (section 10) | 5.23 | CC9.2 | 15 | provider reports reviewed, CUEC mapping |
| Environment separation | separate accounts, namespaces and Dokploy projects | 8.31 | CC8.1 | – | account and namespace lists, deploy permissions |

Two habits make this mapping pay. **Write controls the way they actually run** ("all production
changes go through a merge request with one approval, enforced by protected branches"), never the
way you wish they ran, because an auditor tests what is written. And **prefer controls that a tool
enforces** (protected branches, Harbor policies, CI gates, admission policies): they operate every
time, and their configuration in Git is the evidence.

**Key terms**

| Term | Meaning |
|---|---|
| Control | a specific, testable practice: who does what, how often, with what record |
| Control owner | the person accountable for a control operating; often a team lead, with engineers doing the work |
| Policy as code | a control implemented as enforced configuration (branch protection, admission policy, CI gate) |
| Segregation of duties | the person who makes a change is not the only person who approves it |

**See it on a real system** — one control tested with data, as an auditor would: did every
production change in the quarter have an approval by someone other than its author? (`glab` is the
GitLab CLI; the same query appears in [Senior architecture](39-learn-senior-architecture.md)
section 13.)

```bash
glab api "projects/ops%2Finfra/merge_requests?state=merged&target_branch=main&updated_after=2026-07-01T00:00:00Z&per_page=100" \
  | jq -r '.[] | select(.merge_user.username == .author.username) | "!\(.iid)\t\(.merged_at[0:10])\t\(.title)"'
```

```
!431	2026-09-02	traefik: temporary allowlist for vendor
```

→ One change in the quarter was merged by its own author. Either it was a documented emergency
change (and the emergency procedure's record should exist), or it is an exception the auditor will
report. The durable fix is a control a tool enforces: protected branches that require an approval
from someone other than the author.

**Hands-on lab (your homelab or a throwaway GitLab group)**

**Step 1 — Build.** Pick five rows of the table that apply to your homelab and write each control
in one sentence, the way it really runs.

**Step 2 — Break it.** For each one, ask "how would I prove this for the last quarter?". Mark the
ones where the honest answer is "I could not".

**Step 3 — Fix it.** For each unprovable control, either make a tool enforce it (and keep the
configuration in Git), or add a recurring record to the evidence pack (last topic of this area).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Control written as an aspiration | the auditor finds the documented control does not operate | rewrite it as it really runs | this topic |
| Manual controls only | evidence must be assembled by hand every quarter | enforce with tools, export automatically | Evidence collection |
| Changes outside Git | Dokploy UI edits, hand-edited servers with no record | change process, audit trails | What auditors ask DevOps for |
| No owner | nobody notices the control has stopped | name an owner per control | this topic |

**Why it matters for troubleshooting.** The controls that satisfy auditors (reviewed changes,
central logs, inventories, backups that restore) are the same ones that make outages shorter. The
mapping is a reason to do them well, not extra work.

**Next step:** produce evidence that stands up.

### Evidence collection

**Level:** [L2 · Mid] to produce, [L3 · Senior] to automate

**Concept.** Good evidence is **system-generated**, **complete** (the whole population for the
period, not a convenient subset), **dated**, **attributable** (you can tell what produced it) and **tamper-evident**
(stored where it cannot be quietly edited). Auditors work with populations and
samples: they ask for the full list (all production changes in Q3), choose a sample from it (say 25
changes), then ask for the details of each sampled item. Screenshots are accepted but weak, because
they prove nothing about completeness; an export with the query that produced it is better; an
export produced on a schedule by a pipeline is best.

Three rules are not negotiable. Never create evidence after the fact and date it backwards. Never
edit an export to make it look better. And if a control failed, say so and show the corrective
action: an honest exception is normal and survivable, while falsified evidence is fraud.

**Key terms**

| Term | Meaning |
|---|---|
| Population | every item the control applies to in the period |
| Sample | the items the auditor selects from the population for detailed testing |
| PBC list | "prepared by client": the auditor's list of requested evidence |
| Evidence index | which artefact proves which control, where it lives and who produces it |
| Write-once storage | storage where evidence cannot be changed or deleted, e.g. S3 with Object Lock |

**See it on a real system** — a monthly evidence job (a scheduled pipeline on the 1st of each month,
running with read-only credentials) and what it produces:

```bash
#!/usr/bin/env bash
# monthly-evidence.sh: read-only exports into a dated folder, then a hash manifest
set -euo pipefail
OUT=evidence/$(date -u +%Y-%m); mkdir -p "$OUT"
ansible all -b -m ansible.builtin.command -a 'getent group sudo docker' > "$OUT/linux-privileged-groups.txt"
kubectl get clusterrolebindings -o json \
  | jq -r '.items[] | select(.roleRef.name=="cluster-admin") | [.metadata.name, ((.subjects // []) | map(.kind + ":" + .name) | join(","))] | @tsv' \
  > "$OUT/k8s-cluster-admins.tsv"
aws iam generate-credential-report > /dev/null; sleep 15   # repeat until the report state is COMPLETE
aws iam get-credential-report --query Content --output text | base64 -d > "$OUT/aws-credential-report.csv"
ansible all -b -m ansible.builtin.shell -a "zgrep -h 'Start-Date' /var/log/apt/history.log* | tail -n 5; last -x reboot -n 2" \
  > "$OUT/patching-and-reboots.txt"
curl -s -u "$HARBOR_USER:$HARBOR_PASSWORD" \
  "https://harbor.example.com/api/v2.0/projects/shop/repositories/api/artifacts?with_scan_overview=true&page_size=20" \
  | jq -r '.[] | [.digest[0:19], (.tags // [] | map(.name) | join(",")), (.scan_overview[]?.summary.summary | tostring)] | @tsv' \
  > "$OUT/harbor-scan-summary.tsv"
cp security/exceptions.yaml "$OUT/exceptions-register.yaml"
(cd "$OUT" && sha256sum ./* > SHA256SUMS)
```

```
evidence/2026-09/
├── SHA256SUMS
├── aws-credential-report.csv
├── exceptions-register.yaml
├── harbor-scan-summary.tsv
├── k8s-cluster-admins.tsv
├── linux-privileged-groups.txt
└── patching-and-reboots.txt
```

→ Every file is produced by a system, carries its month in the path, and is covered by the hash
manifest. Commit the folder to a protected evidence repository (no force-push, maintainers only) or
upload it to a bucket with Object Lock. Next year, when the auditor asks for "privileged users in
September", you open one file instead of reconstructing history. Keep the job's credentials
read-only: an evidence pipeline must never be able to change the systems it reports on.

**Hands-on lab (homelab)**

**Step 1 — Build.** Adapt the script to your lab (drop what you do not run), schedule it monthly in
a private GitLab project, and write an evidence index: control, artefact, generator, frequency,
location, owner.

**Step 2 — Break it.** Edit one line of last month's export by hand, then run `sha256sum -c
SHA256SUMS` in that folder: the check fails. That is tamper-evidence working. Restore the file from
Git.

**Step 3 — Fix it.** Protect the evidence repository (protected default branch, no force-push,
restricted maintainers), and add the manifest's hash to the merge request description, so the
history shows exactly what was submitted and when.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Evidence assembled before audits | weeks of screenshots; gaps nobody can fill | a scheduled export job | this topic |
| Incomplete population | the auditor finds an item missing from your list | export with the query, not by hand | this topic |
| Evidence editable by anyone | integrity cannot be shown | protected repository, Object Lock | this topic |
| Secrets inside evidence | tokens or passwords in exports | review exports; export metadata, never values | section 5 |
| Evidence job with admin rights | a compliance tool becomes an attack path | read-only credentials | section 10 |

**Why it matters for troubleshooting.** The same monthly exports answer "who had root on web01 in
August?" or "when was this host last patched and rebooted?" during an incident, without anyone
having to remember.

**Next step:** what auditors typically ask a DevOps team.

### What auditors ask DevOps for

**Level:** [L3 · Senior]

**Concept.** Requests vary by framework and auditor, but the same fifteen come back almost every
time. Knowing them turns an audit from an interruption into a forty-minute exercise per request:

| Request | What it tests | What you provide | Common pitfall |
|---|---|---|---|
| all production changes in the period | change management (8.32, CC8.1) | merge request export with approvals, pipeline IDs, deploy times | changes made outside Git: Dokploy UI edits, hand-edited servers |
| details for 25 sampled changes | that each change was approved and tested | merge request links, CI logs, the change request for big changes | self-approved merges |
| everyone with production access | access control (5.18, CC6.2, CC6.3) | exports from Linux, Kubernetes, AWS, GitLab, Dokploy, Harbor | shared accounts such as root or a shared Dokploy admin |
| quarterly access reviews and the removals they caused | that reviews happen and lead to action | review tickets with exported lists and removal records | review done, nothing recorded |
| leavers removed within the policy time | deprovisioning (CC6.2, CC6.3) | HR leaver list against removal timestamps | SSH keys in `authorized_keys` that outlive the SSO account |
| MFA enforcement | authentication (8.5, CC6.1) | identity provider, GitLab and AWS settings, credential report | a break-glass or service account without MFA, undocumented |
| vulnerability scans and remediation times | vulnerability management (8.8, CC7.1) | scan reports, SLA metrics, the exceptions register | findings older than the SLA without an exception |
| patch status of servers | technical vulnerabilities, configuration | apt history, unattended-upgrades logs, reboot records | servers not rebooted for a year |
| logging configuration and review | logging and monitoring (8.15, 8.16, CC7.2) | shipping and retention settings, sample alerts with their tickets | alerts that go to an unmonitored mailbox |
| incidents and how they were handled | incident management (5.24 to 5.27, CC7.3, CC7.4) | incident list, postmortems, closed actions | "we had no incidents" (near misses count) |
| backups and a restore test | backup (8.13, A1.2, A1.3) | job configuration, restore-test record | backups that were never restored |
| encryption in transit and at rest | cryptography (8.24, CC6.7) | TLS settings and scan results, disk and KMS settings | plain HTTP between the proxy and apps, never justified |
| network diagram and firewall review | network security (8.20, CC6.6) | diagram, rule exports, review record | Docker-published ports missing from the reviewed rules (section 3) |
| asset inventory | inventory (5.9) | the inventory export | hosts nobody listed |
| separation of environments and duties | 8.31, CC8.1 | separate accounts and namespaces, protected branches | developers deploying straight to production |

How to behave in an audit: answer exactly the question asked; provide evidence rather than
narratives; say "I don't know, I will find out" instead of guessing; send scope questions to the
compliance owner; and in a **walkthrough**, where the auditor watches you perform a control live
("show me how you remove a leaver from every system"), close windows that show secrets first. Do
not volunteer unrelated systems, and never hide anything.

**Key terms**

| Term | Meaning |
|---|---|
| Walkthrough | the auditor observes a control being performed, end to end |
| Deprovisioning | removing all of a person's access when they leave or change role |
| Emergency change | a change made outside the normal process, recorded and reviewed afterwards |
| Finding | a gap the auditor reports: exception, nonconformity or observation |

**See it on a real system** — the leaver check that most often fails for DevOps teams, because SSH
keys outlive SSO accounts. Compare the key comments on every host with the leaver list:

```bash
ansible all -b -m ansible.builtin.shell \
  -a "for f in /root/.ssh/authorized_keys /home/*/.ssh/authorized_keys; do [ -f \"\$f\" ] && awk -v f=\"\$f\" '{print f, \$NF}' \"\$f\"; done; true" \
  | grep -i -E 'bob|carol'
```

```
web01 | CHANGED | rc=0 >>
/home/deploy/.ssh/authorized_keys bob@laptop-2024
```

→ bob left in July; his key still opens the deploy account on web01. That is an audit finding and,
more importantly, an open door. Remove it now, then fix the process: keys distributed from one
source (Ansible, or an SSH certificate authority with short-lived certificates, section 2), so
removing a person happens in one place.

**Hands-on lab (paper plus homelab)**

**Step 1 — Build.** Pick five requests from the table and prepare the answer for your homelab: the
artefact, the command or export that produces it, and where it is stored.

**Step 2 — Break it.** Ask a colleague to act as the auditor and pick three random items from your
change population. For each, show the approval and the pipeline run within five minutes.

**Step 3 — Fix it.** For every item you could not produce in time, add an export to the monthly
evidence job, or change the process so the record exists automatically next time.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Changes made in UIs | no record for Dokploy or Harbor setting changes | record UI changes in change requests; prefer configuration in Git | [Senior architecture](39-learn-senior-architecture.md) section 11 |
| Leaver keys left behind | an old key in `authorized_keys` | the leaver check above | section 2 |
| Narrative instead of evidence | "we always do that" without a record | the evidence index | Evidence collection |
| Guessing an answer | a statement later contradicted by evidence | "I will find out" | this topic |

**Why it matters for troubleshooting.** Several requests on this list (who had access, what changed,
was it patched) are the first questions of every incident too. A team that can answer auditors fast
can answer incident commanders fast.

**Next step:** build the quarterly evidence pack.

### Lab: quarterly evidence pack

**Level:** [L3 · Senior] to build, [L4 · Lead/SRE] to keep running

**Concept.** Bring the area together: one folder per quarter that proves the main controls operated,
built mostly by the monthly job, reviewed by a person, and stored where it cannot be changed. For a
homelab it is practice; at work it is what makes an audit routine.

**Key terms**

| Term | Meaning |
|---|---|
| Evidence pack | the set of artefacts for a period, with an index and a manifest |
| Reviewer sign-off | a person confirms the pack is complete and notes exceptions |

**See it on a real system** — the index of a finished pack:

```
evidence/2026-Q3/README.md
| Control                     | Artefact                                   | Produced by          | Status |
| Privileged access           | 2026-07..09/linux-privileged-groups.txt    | monthly job          | OK     |
| Access review               | access-review-2026-Q3.md (issue #212)      | team lead            | OK, 2 removals |
| Vulnerability management    | harbor-scan-summary.tsv, exceptions        | monthly job          | 1 expired exception renewed |
| Patching                    | patching-and-reboots.txt                   | monthly job          | sec-reg missed August reboot |
| Change management           | changes-2026-Q3.tsv (merge request export) | quarterly export     | 1 self-merge, emergency CR-2026-038 |
| Backup and restore          | restore-test-2026-09-14.md                 | ops                  | OK, RTO 42 min |
| Incident management         | SEC-2026-004 postmortem, game day report   | lead                 | 3 actions open |
Reviewed by: lead-ops, 2026-10-03   Manifest: SHA256SUMS (hash recorded in issue #219)
```

**Hands-on lab (homelab)**

**Step 1 — Build.** Assemble the pack for last quarter from the monthly folders, plus an access
review, a restore-test record and the change export, and write the index.

**Step 2 — Break it.** Play auditor on yourself: pick three random changes and one random month of
patching, and trace each to its evidence. Typically one change was made directly in a UI and has no
record.

**Step 3 — Fix it.** Record the gap honestly in the index (with its corrective action), change the
process that allowed it, and set a calendar reminder for the next quarter's pack.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Pack built the week before the audit | missing months that cannot be recreated | the monthly job | Evidence collection |
| Gaps hidden | an auditor finds what the index omitted | record exceptions honestly | this topic |
| Nobody reviews the pack | broken exports go unnoticed for months | a named reviewer with a date | this topic |

**Why it matters for troubleshooting.** A quarter of dated, hashed facts about your platform is also
the best baseline you will ever have for the question "what is different now?".

**Next step:** test yourself.

---

## 15. Self-check and exit tests

> 📚 **Study path:** 1) Practice first: do each timed task on the lab VMs from section 0 (snapshot first) or on the free [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu), without notes · 2) KodeKloud: the free [CKS – Challenges](https://kodekloud.com/courses/cks-challenges) for the Kubernetes tasks, after the CKA · 3) Note: re-read the section named in brackets for every question you miss · 4) Then place yourself in the [Career ladder](40-career-ladder.md) and its self-check.

Tags: one test per stage, from [L0 · Fresher] to [L4 · Lead/SRE].

How to use the tests: answer the questions out loud or in writing, in your own words, then check
your answer against the section named in brackets. Do the timed tasks on test VMs or the homelab
cluster, never on production. You pass a stage when every question is answered correctly and every
task is done within its time, without help. Restore your snapshots after every attempt and write the
five-line note (symptom, first wrong guess, deciding evidence, fix, what you will check first next
time). Security skills fade without practice: repeat your current stage's tasks every quarter.

### Fresher exit test

**Level:** [L0 · Fresher]

Questions:

1. Explain confidentiality, integrity and availability with one example each from a Dokploy host. (section 1)
2. Why is key-only SSH safer than passwords, and what should `PermitRootLogin` be set to? (section 2)
3. Read `ls -l /etc/shadow` aloud and explain every field. Why is the file not world-readable? (section 2)
4. You pushed a commit containing a password. What do you do first, and why is deleting the commit not enough? (section 5)
5. What does UFW's default "deny incoming" mean, and which ports should a public web server answer on? (section 3)
6. Why do personal accounts plus `sudo` beat a shared root login? (sections 2 and 12)
7. An `auth.log` line says `Invalid user admin from 203.0.113.50 ... [preauth]`. Should you worry? Which line would worry you instead? (section 12)

Timed tasks:

1. **15 minutes.** On a fresh VM, create a sudo user with key-only SSH, and verify it from a new session before closing the old one. (section 2)
2. **10 minutes.** List world-writable files under `/etc` and `/usr/local`, and explain any you find. (section 2)
3. **10 minutes.** From the journal, list the last five successful SSH logins with user, source IP and time. (section 12)

### Junior exit test

**Level:** [L1 · Junior]

Questions:

1. Where do you check that unattended-upgrades ran, and what does `/var/run/reboot-required.pkgs` tell you? (sections 2 and 11)
2. Why are the Docker packages held on a Dokploy host, and what happened in November 2025 to hosts where they were not? (section 11)
3. Name the three parts of a fail2ban jail, and explain `ignoreip`. (section 2)
4. How do you prove, from outside, that only ports 22, 80 and 443 answer? (section 3)
5. What is the difference between a masked and a protected GitLab CI variable? (section 5)
6. What do CVE and CVSS mean, and why is a CVSS 9.8 finding with no available fix not this week's work? (section 11)
7. Monitoring shows an SSH login from an unknown IP at 03:00. What are your first three actions, and what must you not do? (sections 12 and 13)
8. What does `usermod -L` fail to stop on Ubuntu, and what do you add? (section 13)

Timed tasks:

1. **30 minutes.** Harden a fresh VM to a Lynis hardening index of 75 or more. (section 2)
2. **15 minutes.** Prove unattended-upgrades works, find the pending reboot, and list the held packages. (section 11)
3. **10 minutes.** From sec-scan, scan sec-target with nmap and explain every open port. (section 3)
4. **10 minutes.** List every command run with sudo today, and by whom. (section 12)

### Mid-level exit test

**Level:** [L2 · Mid]

Questions:

1. Why does a UFW deny not block a Docker-published port, and where do your own rules belong? (section 3)
2. Fix "x509: certificate signed by unknown authority" for the Docker daemon, for containerd and inside a container: where does the CA go in each case? (section 4)
3. Why is membership of the `docker` group equivalent to root, and how do you audit it? (section 6)
4. In Trivy output, what is the difference between `fixed` and `affected`, and what do you do with each? (sections 6 and 11)
5. Rank three findings using CVSS, EPSS, KEV and exposure, and justify the order. (section 11)
6. A customer's scan says your OpenSSH is vulnerable. How do you prove it is patched? (section 11)
7. fail2ban banned an IP, but that IP still reaches your app on a Docker-published port. Why? (section 12)
8. What does `auid` give you that `uid` does not? (sections 2 and 12)
9. Why must you not reboot a compromised host first, and what do you collect before anything else? (section 13)

Timed tasks:

1. **30 minutes.** Triage a Trivy report of a real image into P1 to P4 using EPSS and KEV, and write two exceptions-register entries with expiry dates. (section 11)
2. **20 minutes.** Write auditd rules for `authorized_keys` and cron, trigger both, and show the `auid` of each event. (section 12)
3. **20 minutes.** Make CrowdSec or fail2ban ban a test IP for a Docker-published port, prove it from sec-scan, then unban it. (section 12)
4. **15 minutes.** Collect volatile evidence from sec-target to the evidence share, with a verified SHA-256 manifest. (section 13)

### Senior exit test

**Level:** [L3 · Senior]

Questions:

1. Design the PKI for Harbor and internal services: root, intermediate, lifetimes, rotation and distribution of trust. (section 4)
2. How does a GitLab job deploy to AWS with no long-lived secret, and what does the role's trust policy check? (section 10)
3. Which Pod Security Admission level and which NetworkPolicy baseline do you set for an application namespace, and why? (section 7)
4. Describe the path from build to deploy that guarantees only scanned, signed, digest-pinned images run. (section 8)
5. Design an image rebuild cadence, and explain the three ways a rebuild silently fails. (section 11)
6. What does Livepatch cover, what does it not, and how does it change your patch policy? (section 11)
7. Which five events would you page on for a Dokploy host, and why those five? (section 12)
8. How do you contain a compromised pod without losing evidence, and how do you prove the quarantine blocks traffic? (section 13)
9. After root on the Dokploy host, list the secrets to rotate, in order. (section 13)
10. Apply STRIDE to the GitLab → Harbor → Dokploy path and name the top three threats with their controls. (section 1)

Timed tasks:

1. **45 minutes.** Add a scheduled rebuild with fresh layers and a KEV check to the section 8 pipeline, and prove the deployment runs the new digest. (sections 8 and 11)
2. **30 minutes.** Quarantine a pod with a NetworkPolicy, confirm a clean replacement serves traffic, and collect the quarantined pod's evidence. (section 13)
3. **30 minutes.** Write the Wazuh rule for logins from outside the VPN range and prove it with `wazuh-logtest`. (section 12)
4. **30 minutes.** Produce the exposure inventory and the rotation register for a Docker host. (section 13)

### Lead and SRE exit test

**Level:** [L4 · Lead/SRE]

Questions:

1. State your vulnerability and patch policy in five lines (buckets, targets, windows, emergency path, exceptions). How do you measure that it works? (section 11)
2. Who may approve an exception, and why must every exception expire? (section 11)
3. How do you know whether your alerting is healthy? Name three numbers. (section 12)
4. Which roles does a security incident need that an outage does not, and why? (section 13)
5. Which notification deadlines could apply to your organisation, and who owns them? (section 13)
6. What is a detection gap analysis, and how does it shape the action items? (section 13)
7. Explain ISO 27001 certification and a SOC 2 Type II report to a new engineer in two minutes. (section 14)
8. What makes evidence trustworthy, and how do you produce it without manual work? (section 14)
9. How do you design a security game day that also tests your detections? (section 13)

Timed tasks:

1. **Half a day.** Run the security game day with a colleague as facilitator, and publish the postmortem within two working days. (section 13)
2. **60 minutes.** Build the quarterly evidence pack for your homelab. (section 14)
3. **30 minutes.** Write the one-page vulnerability and patch policy for your team. (section 11)
4. **30 minutes.** Present a detection coverage map (sources → rules → routes) with your three biggest gaps. (section 12)

---

## 16. Where to go next

> 📚 **Study path:** 1) KodeKloud: after the CKA, *Certified Kubernetes Security Specialist (CKS)* ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) and the free [CKS – Challenges](https://kodekloud.com/courses/cks-challenges) · 2) Note: [Senior architecture](39-learn-senior-architecture.md) section 13, then the [Career ladder](40-career-ladder.md) · 3) Tools: the handbook module [Wazuh and security tools](48-wazuh-and-security-tools.md) · 4) Practice: one game day and one evidence pack per quarter, on the homelab.

Security is never finished: new CVEs, new tool versions and new ways to misconfigure arrive every
week. What carries you from fresher to senior is not knowing every tool, but having the habits from
this module running quietly: patching on a rhythm, detections that people trust, evidence that builds
itself, and an incident response that has been practised.

### Next modules and courses

| You are | Next in this handbook | KodeKloud | Proof to build |
|---|---|---|---|
| Fresher [L0 · Fresher] | [Learn Linux](27-learn-linux.md), [Users & permissions](10-users-permissions-security.md), [SSH & remote access](09-ssh-remote-access.md) | *Learning Linux Basics Course & Labs* ([course](https://kodekloud.com/courses/the-linux-basics-course)) | a hardened VM and your five-line notes |
| Junior [L1 · Junior] | [Who owns this port?](22-playbook-ports-inventory.md), [Learn Docker](30-learn-docker.md) section 13 | *LFCS* ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) | a Lynis report before and after hardening |
| Mid-level [L2 · Mid] | sections 3, 4, 6, 11 and 12 applied to your own hosts; [Docker & K8s incidents](26-playbook-containers-k8s.md) | *Docker Certified Associate*, security sections ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)); *Grafana Loki* ([course](https://kodekloud.com/courses/grafana-loki)) | a triage policy and detection rules in Git |
| Senior [L3 · Senior] | [Learn Kubernetes](31-learn-kubernetes.md), [Learn: Cloud & AWS](36-learn-cloud-aws.md) sections 2 and 13, [Senior architecture](39-learn-senior-architecture.md) section 13 | *CKS* after the CKA, with *CKS – Challenges* | a signed, digest-pinned pipeline; a PSA and NetworkPolicy homelab |
| Lead / SRE [L4 · Lead/SRE] | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) sections 7 and 8, [Senior architecture](39-learn-senior-architecture.md) sections 11 and 13 | *Fundamentals of SRE* ([course](https://kodekloud.com/courses/fundamentals-of-sre)) | a game day postmortem and a quarterly evidence pack |

Beyond the verified map: KodeKloud also lists DevSecOps-focused material (check the current catalog
for titles and syllabus). Vendor-neutral and cloud security certifications, such as CompTIA Security+
and the AWS security specialty, change their exam versions regularly; check the vendor's site, and
leave them until after the CKA, in line with your study plan's advice to collect no further
certificates before then.

### Communities and references

| Topic | Where | Why |
|---|---|---|
| Wazuh | [documentation](https://documentation.wazuh.com/current/), [Wazuh Google group](https://groups.google.com/g/wazuh), [GitHub issues](https://github.com/wazuh/wazuh/issues?q=is%3Aissue+agent+disconnected) | most real Wazuh problems are answered in the group |
| CrowdSec | [documentation](https://docs.crowdsec.net/), [GitHub issues](https://github.com/crowdsecurity/crowdsec/issues?q=is%3Aissue+traefik) | bouncer and parser questions |
| Traefik | [community forum, top topics of the year](https://community.traefik.io/top?period=yearly) | real-IP, ban and certificate threads |
| Falco | [documentation](https://falco.org/docs/) | default rules and tuning |
| Vulnerability data | [FIRST EPSS](https://www.first.org/epss/), [CISA KEV](https://www.cisa.gov/known-exploited-vulnerabilities-catalog), [Ubuntu CVE tracker](https://ubuntu.com/security/cves), [Ubuntu Livepatch](https://ubuntu.com/security/livepatch) | triage signals and patch status |
| Standards | [OWASP](https://owasp.org/), [CIS Controls](https://www.cisecurity.org/controls), [CIS Benchmarks](https://www.cisecurity.org/cis-benchmarks), [NIST incident response](https://csrc.nist.gov/projects/incident-response) | the frameworks behind sections 1, 2, 13 and 14 |
| Incidents and postmortems | [Google SRE book](https://sre.google/sre-book/table-of-contents/), chapters 14 and 15 | incident management and postmortem culture |
| What other engineers face | [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=security+incident&restrict_sr=1), [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=devsecops&restrict_sr=1), [Server Fault](https://serverfault.com/search?q=hardening+ubuntu+server) | the problems behind this module's field notes |

### Habits that keep you secure

| Rhythm | Habit | Section |
|---|---|---|
| Weekly | 30-minute alert review: top five noisy rules, one tuning change each; triage new HIGH and CRITICAL findings | 11, 12 |
| Monthly | patch window with reboots; check the evidence job ran; renew or close expiring exceptions | 11, 14 |
| Quarterly | access review; tabletop or game day; evidence pack; a restore test | 13, 14 |
| Yearly | refresh the threat model; rehearse a CA rotation; review the policies against reality | 1, 4, 14 |

### Your next 30 days

You are moving from Junior to Mid-level, with the CKA in progress and Apache moving behind Dokploy.
Keep the CKA sessions first; these four weeks fit around them:

1. **Week 1:** on your Dokploy host, check from outside which ports answer and confirm your own rules sit in `DOCKER-USER` (section 3). Hold the Docker packages and write the patch-window runbook with the Traefik compatibility check (section 11).
2. **Week 2:** ship the journal, `auth.log` and `audit.log` off the host, and add three alerts: SSH login from outside the VPN range, a change in Docker socket mounts, and a host that stops sending logs (section 12).
3. **Week 3:** create the exceptions register and the triage policy, then triage the images you actually run from Harbor with EPSS and KEV (section 11).
4. **Week 4:** run a 45-minute tabletop with a colleague on "the deploy key leaked" (section 13) and write the five-line note. Leave section 7 and the CKS for after the CKA exam.
