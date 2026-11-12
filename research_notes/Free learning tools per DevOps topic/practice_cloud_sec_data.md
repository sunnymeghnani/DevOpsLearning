# Practice sites per topic: cloud, security, data tracks

Checked 2026-11-09 (00:58-01:25 IST). Per-topic deep links into known platforms plus a few new ones.
Method: each URL opened with curl/WebFetch (status + page text/meta). SadServers access level read from the
scenario list page; Pwned Labs free/premium read from each lab page's `isAccessibleForFree` field and meta description.
No logins, sign-ups or labs were run.

Legend: Runs = browser / vendor account (vendor-hosted VM or cloud account) / throwaway VM (local) / **YOUR OWN CLOUD ACCOUNT (can bill)**.
SadServers "Email" = free with an email account; "Public" = no account at all. Pwned Labs free labs need a free account, no card.

**BILLING FLAG:** Pwned Labs "Loot Public EBS Snapshots" and "Plunder Public RDS Snapshots" say "Needs an AWS account":
you restore a snapshot in YOUR OWN AWS account (EBS volume / RDS instance bill per hour; delete right after).

## Coverage: new finds per topic (rows naming the topic; P = existing prove_sites count)

| Topic | Level | Existing prove_sites | New rows |
|---|---|---|---|
| cloud-concepts | L0 | 2 | 5 |
| host-firewall | L1 | 1 | 7 |
| ssh-hardening | L1 | 2 | 5 |
| aws-iam-ec2 | L1 | 3 | 11 |
| db-basics | L1 | 2 | 3 |
| backups-restore | L1 | 1 | 7 |
| private-ca | L2 | 1 | 5 |
| docker-firewall | L2 | 1 | 2 |
| container-hardening | L2 | 1 | 7 |
| db-incidents | L2 | 3 | 3 |
| backup-tools | L2 | 0 | 0 |
| aws-vpc-alb | L2 | 3 | 3 |
| secrets | L3 | 2 | 11 |
| vault-sso | L3 | 1 | 9 |
| k8s-security | L3 | 2 | 6 |
| wazuh | L3 | 1 | 8 |
| crowdsec-fail2ban | L3 | 0 | 4 |
| aws-platform | L3 | 2 | 11 |
| proxmox-ve | L3 | 0 | 0 |
| db-ha | L3 | 1 | 4 |
| object-storage-minio | L3 | 0 | 8 |
| cloud-architecture | L4 | 2 | 4 |
| wazuh-siem | L4 | 2 | 5 |
| security-response | L4 | 3 | 14 |

## cloud-concepts - Cloud concepts and a safe AWS sandbox (L0)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| cloud-concepts, aws-iam-ec2 | https://cybr.com/hands-on-labs/lab/getting-started-with-the-aws-cli/ | First AWS CLI session in a lab account: profiles, whoami, list resources | Free lab (Cybr "free" category, 33 free labs) | Free Cybr account, no card | vendor AWS account (1-click deploy) | L0 | verified (catalog JSON + 200) |
| cloud-concepts, aws-iam-ec2 | https://cybr.com/hands-on-labs/lab/aws-cli-tips-and-tricks/ | CLI filters, --query, output formats | Free lab | Free account | vendor AWS account | L1 | verified (catalog JSON) |
| cloud-concepts, object-storage-minio | https://cybr.com/hands-on-labs/lab/creating-buckets-uploading-objects-in-s3-cli/ | Create buckets, upload objects with the CLI (role variant: .../creating-buckets-uploading-objects-in-s3-role/) | Free lab | Free account | vendor AWS account | L0 | verified (catalog JSON) |
| cloud-concepts | https://cybr.com/hands-on-labs/lab/create-a-static-s3-website-using-terraform/ | Terraform an S3 static site | Free lab | Free account | vendor AWS account | L1 | verified (catalog JSON + WebFetch of announcement post) |

## host-firewall - Host firewall: UFW and nftables (L1)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| host-firewall | https://sadservers.com/scenario/tokyo | curl 127.0.0.1:80 returns nothing though the file is there; page says it is not about web-server config (known answer involves a packet-filter rule - from memory, not stated) | Free (Email) | Free account | vendor VM | L2 | verified |
| host-firewall | https://sadservers.com/scenario/kampot | Expose an app hard-coded to :20280 on :80 without changing it (NAT redirect / proxy) | Free (Email) | Free account | vendor VM | L1 | verified |
| host-firewall, ssh-hardening | https://sadservers.com/scenario/taipei | Port knocking in front of a web server | Free (Email) | Free account | vendor VM | L1 | verified |
| host-firewall | https://sadservers.com/scenario/porto | Audit listening ports without ss/netstat (/proc/net) | Free (Email) | Free account | vendor VM | L2 | verified |
| host-firewall | https://labs.iximiuz.com/challenges/linux-preserve-iptables-rules and https://labs.iximiuz.com/challenges/linux-preserve-nftables-rules | Rules vanish on reboot; make iptables / nftables persistent | Free plan | Free account | vendor VM | L1 (Easy) | verified |
| host-firewall | https://labs.iximiuz.com/challenges/networking-block-unexpected-access-on-dual-homed-server | Service bound to one NIC still reachable from the other network; block it | Free plan | Free account | vendor VM | L2 | verified |

## ssh-hardening - SSH hardening, fail2ban and auto-updates (L1)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| ssh-hardening | https://sadservers.com/scenario/pokhara and https://sadservers.com/scenario/nuuk | SSH break-fix ("sshenanigans", "More SSH troubles") | **Paid** | Paid | vendor VM | L2-L3 | verified (Access: Paid) |
| ssh-hardening, security-response | https://sadservers.com/scenario/rinconada and https://sadservers.com/scenario/annapurna | Privilege escalation as a normal user: see what a hardened sudo/permissions setup must stop | Free (Email) | Free account | vendor VM | L2 | verified |
| ssh-hardening | https://tryhackme.com/room/linuxsystemhardening | Firewall, SSH, accounts, updates, audit on Linux | **Premium room** (per search snippet) | Subscription | vendor VM | L1 | snippet only (Vercel 429 blocked opening) |
| ssh-hardening, host-firewall | https://labs.iximiuz.com/challenges/networking-restore-emergency-ssh-access | VPN down: restore SSH to a dual-homed server with a routing trick (and see why firewalls must cover every interface) | Free plan | Free account | vendor VM | L2 | verified |

## aws-iam-ec2 - AWS basics: IAM, EC2 and SSM (L1)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| aws-iam-ec2 | https://pwnedlabs.io/labs/intro-to-aws-iam-enumeration | Enumerate IAM users, roles, groups, policies with the CLI | Free lab | Free account, no card | vendor AWS account ("no account needed") | L1 | verified (isAccessibleForFree=true) |
| aws-iam-ec2 | https://cybr.com/hands-on-labs/lab/introduction-to-aws-iam-enumeration/ | Same skill, second provider: list-attached-policies, get-policy-version | Free lab | Free account | vendor AWS account | L1 | verified |
| aws-iam-ec2, security-response | https://cybr.com/hands-on-labs/lab/generate-iam-credentials-reports/ | Credential report: stale keys, no-MFA users (audit before an incident) | Free lab | Free account | vendor AWS account | L1 | verified |
| aws-iam-ec2 | https://cybr.com/hands-on-labs/lab/iam-createaccesskey-privesc/ and https://cybr.com/hands-on-labs/lab/iam-createloginprofile-privesc/ | Why iam:CreateAccessKey / CreateLoginProfile on others = admin; least privilege | Free CTF labs | Free account | vendor AWS account | L2 | verified |
| aws-iam-ec2, aws-platform | https://pwnedlabs.io/labs/ssrf-to-pwned | SSRF to EC2 instance metadata, steal the role creds (why IMDSv2) | Free lab | Free account | vendor AWS account | L2 | verified |
| aws-iam-ec2 | https://pwnedlabs.io/labs/assume-privileged-role-with-external-id | sts assume-role with an External ID from a leaked config | Free lab | Free account | vendor AWS account | L2 | verified |
| aws-iam-ec2 | https://pwnedlabs.io/labs/understand-authentication-mechanisms-using-boto3 | How AWS auth works in code: STS, IAM, Secrets Manager via boto3 | Free lab | Free account | vendor AWS account | L1 | verified |
| aws-iam-ec2, cloud-architecture | https://sadservers.com/scenario/istanbul | Find and delete unattached EBS volumes (FinOps clean-up) with the AWS CLI against a local emulator | Free (Email tier) | Free SadServers account | vendor VM, AWS emulator - no real AWS | L1 | verified (scenario list + 200) |

## db-basics - Databases for ops: connect, inspect, can't-connect (L1)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| db-basics | https://sadservers.com/scenario/manhattan | Postgres can't write data (disk/permissions) | Free, **Public - no account** | None | vendor VM | L2 | verified |
| db-basics | https://www.crunchydata.com/developers/playground/psql-basics and https://www.crunchydata.com/developers/playground/postgres-users-and-roles | psql meta-commands; roles, grants, login problems | Free | None | browser (Postgres in WASM) | L1 | verified (listed on tutorials index) |
| db-basics | https://pgexercises.com/questions/basic/ , /joins/ , /updates/ , /aggregates/ , /date/ , /recursive/ | Graded SQL sections in order | Free | None | browser | L1 | verified (all 200) |

## backups-restore - Backups that actually restore (L1)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| backups-restore | https://sadservers.com/scenario/alexandria | "The Vanishing Backups": backup script that silently fails | Free (Email) | Free account | vendor VM | L1 | verified |
| backups-restore, db-ha | https://sadservers.com/scenario/tigoni | Upgrade a stateful backup/archive app without losing data | Free (Email) | Free account | vendor VM | L3 | verified |
| backups-restore | https://sadservers.com/scenario/montevideo | A restore test that would clobber production | **Paid** | Paid | vendor VM | L2 | verified (Access: Paid) |
| backups-restore, aws-platform | https://pwnedlabs.io/labs/leverage-insecure-storage-and-backups-for-profit | Exposed backups in AWS lead to domain creds: why backups need encryption + access control | Free lab | Free account | vendor AWS account | L3 | verified |
| backups-restore, security-response | https://pwnedlabs.io/labs/loot-public-ebs-snapshots | Public unencrypted EBS snapshot leaks creds | Free lab | Free account + **YOUR OWN AWS ACCOUNT - restoring the volume can bill** | **your own cloud account** | L2 | verified ("Needs an AWS account") |

## private-ca - Private CA and trust stores (L2)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| private-ca | https://sadservers.com/scenario/geneva | Renew an expired cert keeping the same subject | Free (Email) | Free account | vendor VM | L1 | verified |
| private-ca | https://sadservers.com/scenario/salzburg | HTTPS on :443 broken though the key still matches the cert (chain/config) | Free (Email) | Free account | vendor VM | L2 | verified |
| private-ca, k8s-security | https://sadservers.com/scenario/lisbon | etcd TLS cert trouble | Free (Email) | Free account | vendor VM | L2 | verified |
| private-ca | https://sadservers.com/scenario/moyogalpa | Go app broken by new TLS settings; make HTTPS work "without ignoring any checks" (trust store) | Free (Email) | Free account | vendor VM | L2 | verified |
| private-ca, vault-sso | https://sadservers.com/scenario/campina-grande | "Give me my cert, Vault": nginx cert from Vault PKI | **Paid** | Paid | vendor VM | L3 | verified (Access: Paid) |

## docker-firewall - Docker bypasses UFW (L2)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| docker-firewall | https://labs.iximiuz.com/challenges/docker-networking-prevent-unexpected-access-to-published-port | Exact match: a published container port is reachable from outside; restrict it with firewall rules (DOCKER-USER) without breaking legit traffic | Free plan (iximiuz free tier has playground time limits; no premium marker on page) | Free account to start | vendor VM (browser) | L2 (Hard) | verified |
| docker-firewall | https://labs.iximiuz.com/challenges/docker-networking-reach-host-service-bound-to-localhost | Container reaching a localhost-only host service without exposing it to the LAN | Free plan | Free account | vendor VM | L2 | verified |

## container-hardening - Container hardening and image scanning (L2)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| container-hardening | https://www.cloudsecuritychampionship.com/challenge/2 | Wiz "Contain Me If You Can": container escape to host filesystem | Free | Free Wiz account | browser shell, vendor | L3 | verified (WebFetch list, "Enter Challenge") |
| container-hardening | https://sadservers.com/scenario/venice | "Am I in a container?" - detect container vs host | Free (Email) | Free account | vendor VM | L1 | verified |
| container-hardening | https://sadservers.com/scenario/madrid | Exploiting Linux capabilities (why --cap-drop ALL) | **Paid** | Paid | vendor VM | L3 | verified (Access: Paid) |
| container-hardening, k8s-security | https://labs.iximiuz.com/challenges/lock-down-container-syscalls-with-seccomp-5c86273c | RuntimeDefault seccomp, custom profile, fix a profile that blocks a needed syscall | Free plan | Free account | vendor VM | L3 | verified |

## db-incidents - Database incidents: connections, locks, slow queries (L2)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| db-incidents | https://sadservers.com/scenario/luxor | Postgres analytics queries crawl (missing index / planner) | Free (Email) | Free account | vendor VM | L2 | verified |
| db-incidents | https://sadservers.com/scenario/hongkong | Harder "can't write data" Postgres | **Paid** | Paid | vendor VM | L3 | verified (Access: Paid) |
| db-incidents | https://www.crunchydata.com/developers/playground/transactions , /query-performance-analytics , /high-level-performance-analytics , /btree-indexes | Transactions/locking behaviour; pg_stat_statements-style analysis; indexes | Free | None | browser | L2 | verified (listed) |

## aws-vpc-alb - AWS VPC and ALB: the timeout checklist (L2)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| aws-vpc-alb | https://sadservers.com/scenario/bologna | Count 5xx in a classic ELB access log | **Paid tier** - listed for completeness | Paid | vendor VM | L1 | verified (Access: Paid) |
| aws-vpc-alb, aws-iam-ec2 | https://pwnedlabs.io/labs/pillage-exposed-rds-instances | Internet-exposed RDS: scan with nmap, connect with mysql, then remediate (security groups) and detect | Free lab | Free account | vendor AWS account | L2 | verified |
| aws-vpc-alb | https://catalog.workshops.aws/networking/en-US | AWS Networking Immersion Day: VPC, subnets, NAT, TGW, endpoints | Free content; **runs in YOUR OWN AWS ACCOUNT unless taken at an AWS event - NAT gateways, TGW, endpoints bill hourly** | AWS account with card | **your own cloud account** | L2 | partly verified (200, Workshop Studio SPA) |

## secrets - Secrets management: Vault, sops, CI variables (L3)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| secrets | https://pwnedlabs.io/labs/hunt-for-secrets-in-git-repos | Find leaked keys with git-secrets and TruffleHog, then prevent/respond | Free lab | Free account | browser/vendor | L1 | verified |
| secrets, container-hardening | https://pwnedlabs.io/labs/uncover-secrets-in-codecommit-and-docker | Keys left in Docker image layers and commit history | Free lab | Free account | vendor AWS account | L2 | verified |
| secrets | https://pwnedlabs.io/labs/leverage-leaked-credentials-for-pwnage | .env leaked to public git, reused against AWS/RDS; detect with TruffleHog | Free lab | Free account | vendor | L2 | verified |
| secrets | https://cybr.com/hands-on-labs/lab/introduction-to-secrets-manager-enumeration/ | What a principal can read in Secrets Manager | Free lab | Free account | vendor AWS account | L1 | verified |
| secrets | https://cybr.com/hands-on-labs/lab/access-secrets-manager-via-lambda-function-with-lfi/ | LFI in Lambda leaks env creds then Secrets Manager | Free CTF | Free account | vendor AWS account | L2 | verified |
| secrets, vault-sso | https://cybr.com/hands-on-labs/lab/audit-the-blast-radius-of-kms-keys-with-finders-keypers/ | Who can use each KMS key (key policy + grants) | Free lab | Free account | vendor AWS account | L2 | verified |
| secrets, container-hardening | https://labs.iximiuz.com/challenges/docker-build-using-secrets-private-go-module | BuildKit secret mounts so creds never land in image layers or cache | Free plan | Free account | vendor VM | L2 | verified |
| secrets | https://www.wrongsecrets.com/ (README "Choose your path" table) | Online container: basic challenges 0-4, 8, 12-32, 34-43, 49-52, 54-66, 68-73 (hard-coded, git, Docker, CI, binaries, AI/MCP). Same set via `docker run jeroenwillemsen/wrongsecrets:latest-no-vault` | Free | None | browser (Heroku) or throwaway VM | L1-L3 | verified (README raw; herokuapp challenge pages 0-69 return 200) |
| secrets, vault-sso, k8s-security | https://github.com/OWASP/wrongsecrets#vault-exercises-with-minikube | `k8s-vault-minikube-start.sh`: Vault + K8s secrets challenges 0-8, 12-66 (Vault agent/injection mistakes) | Free | None | throwaway VM with minikube (needs ~8 GB RAM) | L3 | verified (README) |
| secrets, aws-platform | https://github.com/OWASP/wrongsecrets#cloud-challenges | Cloud secrets challenges (AWS Secrets Manager/SSM, GCP, Azure Key Vault), all challenges 0-72 | Free code, **runs in YOUR OWN CLOUD ACCOUNT via Terraform - EKS/GKE/AKS bills hourly; destroy right after** | Cloud account with card | **your own cloud account** | L3-L4 | verified (README) |

## vault-sso - Vault, OpenBao and SSO with Keycloak or Authentik (L3)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| vault-sso | https://cybr.com/hands-on-labs/lab/breaking-jwt-to-forge-an-admin-token/ | Forge an admin JWT: why token validation (alg, key, audience) matters for SSO | Free lab | Free account | vendor/browser | L2 | verified |
| vault-sso | https://cybr.com/hands-on-labs/lab/require-microsoft-entra-sign-in-for-an-azure-app/ | Put SSO (Entra ID) in front of an app | Free lab | Free account | vendor Azure account | L2 | verified |
| vault-sso | https://pwnedlabs.io/labs/unlock-access-with-azure-key-vault | Key Vault secrets reused for lateral movement (blast radius of one vault) | Free lab | Free account | vendor Azure tenant | L3 | verified |
| vault-sso | https://developer.hashicorp.com/vault/tutorials/get-started | Vault foundations tutorials, several with in-browser interactive labs (dev server, KV, policies, auth methods) | Free | Free HashiCorp account for the lab | vendor VM (browser) | L2 | partly verified (200; "interactive lab" markers on page) |
| vault-sso | https://openbao.org/docs/get-started/developer-qs/ | OpenBao dev-mode quick start (same API as Vault) | Free, open source | None | throwaway VM | L2 | verified (200) |
| vault-sso | https://www.keycloak.org/getting-started/getting-started-docker | Keycloak in Docker: realm, user, client, then log in to the account console (base for OIDC in front of apps/Vault) | Free | None | throwaway VM | L2 | verified (200) |

## k8s-security - Kubernetes security: RBAC, PSA, audit (L3)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| k8s-security | https://www.cloudsecuritychampionship.com/challenge/5 and https://www.cloudsecuritychampionship.com/challenge/11 | "Game of Pods" (K8s privesc) and "Split Horizon" (reach an isolated workload despite policies) | Free | Free account | browser shell | L3-L4 | verified (listed active) |
| k8s-security | https://killercoda.com/killer-shell-cks/scenario/falco-change-rule and https://killercoda.com/killer-shell-cks/scenario/apiserver-misconfigured | CKS: change a Falco rule; fix a broken kube-apiserver manifest. Index: https://killercoda.com/killer-shell-cks | Free (Killercoda free plan, session time limits) | Free login to start | vendor VM | L3 | index verified 200 (SPA); scenario slugs snippet only |
| k8s-security | https://labs.iximiuz.com/challenges/roll-out-pod-security-standards-across-three-namespaces-1be633bd | Staged Pod Security Admission rollout (warn/audit/enforce) without breaking running services | Free plan | Free account | vendor VM | L3 | verified |

## wazuh - Wazuh: host monitoring and detection (L3)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| wazuh | https://tryhackme.com/room/wazuhct | Wazuh room: agents, vulnerability assessment, policy audit, alerts (~160 min) | Free room (per TryHackMe free-training blog) | Free THM account | vendor VM (browser) | L2 | snippet only (Vercel 429) |
| wazuh, crowdsec-fail2ban | https://documentation.wazuh.com/current/proof-of-concept-guide/detect-brute-force-attack.html | Generate SSH brute force against your agent, watch rule 5710/5712 alerts (compare with fail2ban/CrowdSec detection) | Free, open source | None | throwaway VM (2 VMs: manager + agent; snapshot first) | L2 | verified (200, title) |
| wazuh | https://documentation.wazuh.com/current/proof-of-concept-guide/poc-file-integrity-monitoring.html | FIM on a directory, change a file, see the alert | Free | None | throwaway VM | L2 | verified |
| wazuh | https://documentation.wazuh.com/current/proof-of-concept-guide/poc-vulnerability-detection.html | Vulnerability detection on an agent's packages | Free | None | throwaway VM | L2 | verified |
| wazuh, security-response | https://documentation.wazuh.com/current/proof-of-concept-guide/audit-commands-run-by-user.html | auditd + Wazuh: alert on malicious commands run by a user | Free | None | throwaway VM | L3 | verified |
| wazuh, container-hardening | https://documentation.wazuh.com/current/proof-of-concept-guide/monitoring-docker.html | Docker events into Wazuh (container start/exec alerts) | Free | None | throwaway VM | L3 | verified (listed in PoC index) |

## crowdsec-fail2ban - Blocking attackers: CrowdSec and Fail2ban (L3)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| crowdsec-fail2ban | https://playground.crowdsec.net/ | CrowdSec Playground: paste log lines, see parser/scenario results (test before deploying a custom scenario) | Free | none seen | browser | L2 | partly verified (200, title only; SPA content not readable) |
| crowdsec-fail2ban | https://academy.crowdsec.net/ | Free CrowdSec courses (install, bouncers, scenarios) - video-first, practise on your own VM | Free | Free account | throwaway VM | L1 | verified (title "Free CrowdSec video courses") |
| crowdsec-fail2ban, wazuh | https://documentation.wazuh.com/current/proof-of-concept-guide/block-malicious-actor-ip-reputation.html | Active response: auto-block an IP from a reputation list (Wazuh's answer to a CrowdSec blocklist) | Free | None | throwaway VM | L3 | verified |

## aws-platform - AWS platform: containers, audit, keyless CI (L3)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| aws-platform | https://pwnedlabs.io/labs/s3-bucket-brute-force-to-breach | Bucket-name brute force, leaked key, SSM secret, Lambda | Free lab | Free account | vendor AWS account | L3 | verified |
| aws-platform | https://pwnedlabs.io/labs/abuse-cognito-user-and-identity-pools | Cognito identity pools hand out AWS creds | Free lab | Free account | vendor AWS account | L3 | verified |
| aws-platform | https://pwnedlabs.io/labs/sqs-and-lambda-sql-injection | SQS + Lambda consumer second-order SQLi | Free lab | Free account | vendor AWS account | L3 | verified |
| aws-platform | https://cybr.com/hands-on-labs/lab/introduction-to-aws-lambda-enumeration/ and https://cybr.com/hands-on-labs/lab/pentesting-aws-lambda-with-cloudfox/ | Lambda enumeration (env vars, roles, URLs) | Free | Free account | vendor AWS account | L2 | verified |
| aws-platform | https://cybr.com/hands-on-labs/lab/api-gateway-lambda-authorizer-bypass/ | API Gateway Lambda authorizer bypass | Free | Free account | vendor AWS account | L3 | verified |
| aws-platform (keyless CI) | https://pwnedlabs.io/labs/abuse-openid-connect-and-gitlab-for-aws-access | Over-broad GitLab OIDC trust policy -> assume AWS role (exactly the GitLab keyless-CI risk) | **Premium** - listed because it is the only exact match | Paid | vendor AWS account | L3 | verified (isAccessibleForFree=false) |
| aws-platform, cloud-architecture | https://www.cloudsecuritychampionship.com/challenge/7 | "State of Affairs": exploiting Terraform automation/state | Free | Free account | browser shell | L3 | verified |

## db-ha - PITR, replication and failover (L3)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| db-ha, security-response | https://pwnedlabs.io/labs/plunder-public-rds-snapshots | Public RDS snapshot restored = whole DB leaked | Free lab | Free account + **YOUR OWN AWS ACCOUNT - RDS instance bills per hour** | **your own cloud account** | L2 | verified |
| db-ha | https://sadservers.com/scenario/suzhou | MongoDB replica set broken, re-init | Free (Email) | Free account | vendor VM | L3 | verified |
| db-ha | https://sadservers.com/scenario/tunis | Redis replication problem | **Paid** | Paid | vendor VM | L3 | verified |

## object-storage-minio - Object storage: MinIO and S3-compatible targets (L3)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| object-storage-minio, cloud-concepts | https://pwnedlabs.io/labs/aws-s3-enumeration-basics | List vs read on S3 buckets; what public means | Free lab | Free account | vendor AWS account | L1 | verified |
| object-storage-minio | https://pwnedlabs.io/labs/access-secrets-with-s3-bucket-versioning | Recover deleted secrets from old S3 object versions (versioning is not deletion) | Free lab | Free account | vendor AWS account | L1 | verified |
| object-storage-minio | https://pwnedlabs.io/labs/exploit-weak-bucket-policies-for-privileged-access | Read a bucket policy; GetObject allowed though ListBucket denied | Free lab | Free account | vendor | L2 | verified |
| object-storage-minio, secrets | https://cybr.com/hands-on-labs/lab/backdoor-an-s3-bucket-via-its-bucket-policy/ | How a bucket policy backdoor looks, so you can audit for it | Free lab | Free account | vendor AWS account | L2 | verified |
| object-storage-minio, backups-restore | https://cybr.com/hands-on-labs/lab/securing-s3-against-ransomware-with-yes3/ | Versioning, Object Lock, Block Public Access checks with YES3 | Free lab | Free account | vendor AWS account | L2 | verified |
| object-storage-minio, backups-restore | https://sadservers.com/scenario/auckland | S3 lifecycle on backups: delete old keys, move mid-age ones to GLACIER | Free (Email tier) | Free account | vendor VM, local AWS emulator (Floci) | L2 | verified |
| object-storage-minio | https://play.min.io/ | Public MinIO demo server (console on :9443): buckets, policies, versioning, mc alias target | Free public demo; data is public and wiped | Public demo credentials are in MinIO docs; never upload private data | browser / vendor server | L1 | verified (200, "MinIO AIStor Console") |

## cloud-architecture - AWS architecture: hybrid, DR and FinOps (L4)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| cloud-architecture | https://www.cloudsecuritychampionship.com/challenge/4 | "Needle in a Haystack": recon for hidden infra/data (attack-surface view of an architecture) | Free | Free account | browser | L3 | verified |
| cloud-architecture | https://catalog.workshops.aws/well-architected-reliability/en-US and https://catalog.workshops.aws/well-architected-cost-optimization/en-US | Well-Architected reliability (backup/DR, failure injection) and cost-optimisation labs | Free content; **YOUR OWN AWS ACCOUNT - bills** | AWS account with card | **your own cloud account** | L3-L4 | partly verified (200, SPA) |

## wazuh-siem - Wazuh in production: indexer, rules and alerts (L4)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| wazuh-siem | https://playground.opensearch.org/ | Public OpenSearch Dashboards (Wazuh dashboard/indexer are forks): DQL queries, Discover, visualisations, alerting UI on sample data | Free, anonymous | None | browser | L2 | verified (302 to /auth/anonymous, OSD server) |
| wazuh-siem, aws-platform | https://documentation.wazuh.com/current/proof-of-concept-guide/aws-infrastructure-monitoring.html | CloudTrail/GuardDuty logs from S3 into Wazuh | Free tool, **but needs YOUR OWN AWS ACCOUNT (CloudTrail S3 storage, small bill)** | AWS account | **your own cloud account** + VM | L4 | verified (listed in PoC index) |
| wazuh-siem | https://documentation.wazuh.com/current/proof-of-concept-guide/integrate-network-ids-suricata.html and https://documentation.wazuh.com/current/proof-of-concept-guide/detect-unauthorized-processes-netcat.html | Suricata IDS alerts into Wazuh; custom rule for an unauthorized process (rule-writing practice) | Free | None | throwaway VM | L4 | verified (listed) |
| wazuh-siem | https://tryhackme.com/room/exploringwazuh | Exploring Wazuh room (dashboard, alerts) | Unknown free/premium | THM account | vendor VM | L2 | snippet only (Vercel 429) |

## security-response - Security incidents: contain, rotate, rebuild (L4)

| Topic id(s) | URL | What you practise | Free tier / limits | Sign-up / card | Runs | Level | Verified |
|---|---|---|---|---|---|---|---|
| security-response | https://pwnedlabs.io/labs/breach-in-the-cloud | Reconstruct an AWS breach from CloudTrail logs | Free lab | Free account | vendor AWS account | L3 | verified |
| security-response | https://pwnedlabs.io/labs/identify-iam-breaches-with-cloudtrail-and-athena | Set up CloudTrail + Athena, query for credential attacks | Free lab | Free account | vendor AWS account | L3 | verified |
| security-response | https://pwnedlabs.io/labs/execute-and-identify-credential-abuse-in-aws | Run a credential-abuse chain then detect it (purple team) | Free lab | Free account | vendor AWS account | L3 | verified |
| security-response, wazuh-siem | https://pwnedlabs.io/labs/investigate-threats-with-amazon-detective | GuardDuty alert -> Detective -> was the EC2 compromised? | Free lab | Free account | vendor AWS account | L3 | verified |
| security-response | https://pwnedlabs.io/labs/reveal-hidden-risks-with-aws-security-hub | Security Hub CSPM findings, prioritise | Free lab | Free account | vendor ("no AWS account needed") | L2 | verified |
| security-response | https://cybr.com/hands-on-labs/lab/investigate-unauthorized-changes-in-the-azure-activity-log/ | Who changed what: Azure Activity Log forensics | Free | Free account | vendor Azure | L2 | verified |
| security-response | https://www.cloudsecuritychampionship.com/challenge/9 | "Trust Issues": investigate a breach and exfiltration | Free | Free account | browser | L4 | verified |
| security-response, wazuh | https://sadservers.com/scenario/amsterdam | "Cron Hijack": find a malicious cron persistence | Free (Email) | Free account | vendor VM | L2 | verified (listed, Email) |
| security-response | https://sadservers.com/scenario/anatolia | Compromised web server: find what the attacker changed, restore integrity | **Paid** | Paid | vendor VM | L3 | verified (Access: Paid) |

## Notes, gaps and cautions

- **backup-tools, proxmox-ve**: left to the parallel researcher (backups/Proxmox). Backup-adjacent finds above are filed under backups-restore and object-storage-minio.
- **crowdsec-fail2ban** stays thin: no hosted fail2ban break-fix lab found (SadServers, iximiuz, TryHackMe search had none). Best options: CrowdSec Playground (browser) + Wazuh PoC brute-force/active-response pages on a throwaway VM.
- **Paid rows** (SadServers Bologna, Pokhara, Nuuk, Campina Grande, Madrid, Montevideo, Hong-Kong, Tunis, Anatolia; Pwned Labs GitLab-OIDC) are listed only as exact topic matches. Don't add them to prove_sites as free.
- **Your-own-account / billing rows**: Pwned Labs EBS and RDS snapshot labs, WrongSecrets cloud challenges, Wazuh AWS monitoring, AWS Networking Immersion Day, Well-Architected labs. Everything else runs in the vendor's account or on a local VM.
- **SadServers AWS scenarios** (Istanbul, Auckland) use a local AWS emulator (Floci): real AWS CLI, no real account, no bill.
- **TryHackMe** pages return a Vercel 429 to scripted fetches. The Wazuh room's free status comes only from search snippets and THM's free-training blog. Linux System Hardening and Hardening Basics 1/2 are premium.
- **Killercoda killer-shell-cks**: the index loads (200, SPA), but the scenario slugs come from third-party study pages.
- **Wiz Cloud Security Championship**: challenge 3 is inactive. The others are listed as "Enter Challenge" (free Wiz account).
- **Pwned Labs** free/premium status was read from each lab page's `isAccessibleForFree` (90 labs checked; about 35 free). Cybr free status was read from the catalog JSON's "free" category (33 labs).
