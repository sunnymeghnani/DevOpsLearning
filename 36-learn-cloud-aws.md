# 36 — Learn: Cloud & AWS (Fresher to Senior)

This is the cloud learning module of the handbook. It takes you from "what is a region" to
designing, operating and paying for a multi-account AWS platform that is connected to your
on-prem Ubuntu fleet. Everything is framed against what you already run: Ubuntu 22.04/24.04 with
netplan, systemd-resolved and UFW/nftables, Apache on ports 81/444, Dokploy (Traefik v3 on Docker
Swarm), GitLab CI pushing to Harbor behind a private CA, and a kubeadm homelab on the CKA track.
The AWS command reference lives in [AWS troubleshooting](16-aws-cloud.md); Terraform, pipelines
and SRE practice live in [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md). This module is the *why*
behind both, plus the labs that make it stick.

The cloud does not replace what you know. A VPC is still routing, a security group is still a
stateful firewall, an EC2 instance is still Ubuntu with systemd, and an ALB is still a reverse
proxy. What changes is that **every piece of infrastructure is an API call**: it is created by an
API, authorized by IAM, logged by CloudTrail and billed by the second. A fresher learns the
services; a senior engineer learns those three consequences and designs around them.

**Who it serves.** Every career stage, each with a different job. Freshers [L0 · Fresher] learn the
vocabulary and build a safe sandbox. Juniors [L1 · Junior] operate EC2, S3, ALB, Route 53 and
CloudWatch. Mid-level engineers [L2 · Mid] debug IAM, VPC paths, health checks and containers from
evidence. Seniors [L3 · Senior] build the platform: multi-account, hybrid network to on-prem, IaC
and GitLab OIDC, EKS. Leads and SREs [L4 · Lead/SRE] own architecture reviews, disaster recovery,
incident response and cost. Every topic carries its tag, and section 0 tells you where to start.

> All sample outputs are illustrative: AWS CLI v2 (2.3x), Ubuntu 22.04/24.04 EC2 instances,
> region **ap-south-1** (Mumbai) unless stated, sandbox account **123456789012**, second account
> **210987654321**. VPC addresses are private (lab VPC 10.20.0.0/16, second VPC 10.30.0.0/16),
> on-prem is 192.168.10.0/24 with DNS at 192.168.10.53, public addresses come from the
> documentation ranges (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24), and names are under
> example.com. UPPERCASE words in commands are placeholders: INSTANCE_ID, BUCKET, ROLE_NAME,
> PROFILE, REGION, ACCOUNT_ID, VPC_ID, SUBNET_ID, SG_ID, TG_ARN. Prices are approximate us-east-1
> list prices in USD as of 2026; other regions differ and prices change, so check the pricing pages
> before you rely on a number.

---

## 0. How to use this module

### Who this module is for

Cloud work appears at every career stage, but what you are trusted with changes. Find your stage,
do its sections first, and use its exit test in section 15 to decide when to move up. The stage
names match the [career ladder](40-career-ladder.md) used across the handbook.

| Stage | Tag | What you are expected to do on AWS | Focus sections |
|---|---|---|---|
| Fresher (0–1 yr) | L0 · Fresher | Explain regions, AZs and shared responsibility; open a sandbox account safely (MFA, budget alarm); launch and connect to one EC2 instance; use S3 from the CLI; always check identity, region and cost first | 0, 1, 2 (identities), 4 (types, AMIs), 5 (basics) |
| Junior (1–2 yrs) | L1 · Junior | Operate: SSM instead of SSH, SG rules, ALB in front of Apache, Route 53 records, CloudWatch alarms, EBS snapshots and resizes, key rotation; read the monthly bill | 2, 3 (subnets, SG/NACL), 4, 6, 9, 12 (billing) |
| Mid-level (2–4 yrs) | L2 · Mid | Explain any failure with evidence: AccessDenied from CloudTrail and the policy simulator, timeouts from Flow Logs and Reachability Analyzer, unhealthy targets from reason codes, ECS stopped reasons, IMDS and EBS performance issues | 2 (evaluation, debugging), 3 (endpoints, flow logs), 4, 6, 7, 8 (ECR, ECS), 9 |
| Senior (4–7 yrs) | L3 · Senior | Build the platform: IaC with GitLab OIDC, multi-account with SCPs, Transit Gateway, VPN and hybrid DNS to on-prem, EKS, Auto Scaling, KMS, cost guardrails | 2 (SCPs), 3 (TGW), 5 (KMS), 8 (EKS), 10, 11, 12 |
| Senior/Lead/SRE (5+ yrs) | L4 · Lead/SRE | Design for failure and for money: Well-Architected reviews, RTO/RPO and DR strategy, game days, landing zone governance, security incident response, FinOps with commitments | 12, 13, 14, 15 |

You already work at roughly L2 on-prem. On AWS, follow the Ops Ladder advice: skim L0 and L1,
**do their exit tests** in section 15, and put your real hours into L2 and L3, where your on-prem
troubleshooting habits transfer directly and the AWS-specific traps (IAM, NACLs, IMDS, health
checks, cost) are new.

### Learning path

The areas below are grouped by subject so the module also works as a reference. To learn from zero,
follow this order instead.

| # | Topic | Tag | Section | Why it is in this position |
|---|---|---|---|---|
| 1 | Sandbox account, budget alarm, CLI with SSO | [L0 · Fresher] | 0 | Nothing else is safe until a budget alarm exists |
| 2 | What the cloud is; regions and AZs | [L0 · Fresher] | 1 | Vocabulary, and the "wrong region" reflex |
| 3 | Shared responsibility and pricing models | [L0 · Fresher] | 1 | Who patches what, and what costs money |
| 4 | On-prem to AWS mapping | [L1 · Junior] | 1 | Reuse what you know from Ubuntu, UFW and Apache |
| 5 | IAM identities, policies and roles | [L0 · Fresher] → [L1 · Junior] | 2 | Every API call is authorized by IAM |
| 6 | EC2: types, AMIs, user data, SSM | [L1 · Junior] | 4 | Your first workload, without opening port 22 |
| 7 | S3 basics and access control | [L1 · Junior] | 5 | Backups, artifacts and logs all land here |
| 8 | VPC: subnets, routes, IGW, NAT, SG vs NACL | [L1 · Junior] → [L2 · Mid] | 3 | Where most "it times out" tickets live |
| 9 | ALB, target groups, Route 53 | [L1 · Junior] | 6 | Apache behind a cloud load balancer |
| 10 | CloudWatch metrics, alarms, logs agent | [L1 · Junior] | 9 | Learn about problems from an alert |
| 11 | Billing, tags, budgets | [L1 · Junior] | 12 | Cost is an operational signal from day one |
| 12 | Policy evaluation and debugging AccessDenied | [L2 · Mid] | 2 | The most common AWS error, solved with evidence |
| 13 | Endpoints, Flow Logs, Reachability Analyzer | [L2 · Mid] | 3 | Look at the network layer instead of guessing |
| 14 | IMDSv2, EBS performance, status checks | [L2 · Mid] | 4 | "Slow" and "dead" instances explained |
| 15 | Health check reason codes, ALB 5xx | [L2 · Mid] | 6 | The cloud version of your Traefik 502 drill |
| 16 | RDS HA and restore drills | [L2 · Mid] | 7 | Managed does not mean backed up and tested |
| 17 | ECR and ECS/Fargate | [L2 · Mid] | 8 | Harbor and Swarm, AWS edition |
| 18 | CloudTrail, Config, Auto Scaling | [L2 · Mid] → [L3 · Senior] | 9 | Who changed it, and self-healing capacity |
| 19 | CIDR planning, peering, Transit Gateway | [L3 · Senior] | 3 | Networks that can still be connected in three years |
| 20 | Encryption and KMS; Organizations and SCPs | [L3 · Senior] | 5, 2 | Guardrails and keys a platform team owns |
| 21 | IaC and GitLab CI with OIDC | [L3 · Senior] | 10 | No click-ops, no static keys |
| 22 | Hybrid: VPN, Direct Connect, Resolver | [L3 · Senior] | 11 | Your on-prem fleet and AWS as one network |
| 23 | EKS and its quirks | [L3 · Senior] | 8 | Your CKA knowledge on a managed control plane |
| 24 | Bill surprises, rightsizing, commitments | [L3 · Senior] → [L4 · Lead/SRE] | 12 | Saving money is a senior deliverable |
| 25 | Well-Architected; designing for failure | [L4 · Lead/SRE] | 13 | Architecture you can defend in a review |
| 26 | Landing zone; incident response | [L4 · Lead/SRE] | 13 | Running AWS for a whole company |
| 27 | Certifications and the stage matrix | all stages | 14 | Proof, in the right order |
| 28 | Exit tests | all stages | 15 | Move up only when you pass |

> Fast track for a Mid-level engineer: do the sandbox setup in this section, skim 2–11, pass the
> Junior exit test in section 15, then spend your real hours on 12–22.

### Study method

For every ### topic, use the same five steps, in this order:

1. **KodeKloud lesson first.** Each area starts with a 📚 Study path line naming the course section
   and its lab. KodeKloud labs and the AWS playground run in accounts KodeKloud pays for, so they
   cost you nothing and cannot surprise your bill.
2. **One short video**, only if the concept still feels fuzzy. Stop as soon as it clicks.
3. **This handbook note.** Concept, key terms, then run the "See it on a real system" commands in
   your sandbox. They are read-only.
4. **Hands-on lab in your sandbox account.** Build it, break it on purpose, then diagnose from
   evidence **before** you fix it. Write down the exact error text and the cost line, then tear
   everything down the same day.
5. **Open the playbook** named in "How it breaks" ([Site down](25-playbook-site-down.md),
   [Network speed](24-playbook-network-speed.md), [Containers & K8s](26-playbook-containers-k8s.md)
   and the [AWS reference](16-aws-cloud.md)), and read the scenario that matches what you broke.

The KodeKloud route for this module, verified in the handbook's KodeKloud map on 3 Oct 2026:

| Order | KodeKloud item | Free? | Use it for |
|---|---|---|---|
| 1 | [Crash Course: AWS Basics](https://kodekloud.com/courses/crash-course-aws-basics) | free | First contact with S3, EC2 and VPC (sections 1, 4, 5) |
| 2 | [AWS Networking Fundamentals](https://kodekloud.com/courses/aws-networking-fundamentals) | subscription | VPC, subnets, gateways, routing, SGs, load balancers, Route 53, Transit Gateway (sections 3, 6) |
| 3 | [AWS Certified Cloud Practitioner (CLF-C02)](https://kodekloud.com/courses/aws-cloud-practitioner-clf-c02) | subscription | Only if you want the badge (section 14) |
| 4 | [AWS Certified CloudOps Engineer - Associate](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate) | subscription | CloudWatch, CloudTrail, SSM, reliability, networking troubleshooting, cost (sections 4, 9, 12). After CKA |
| 5 | [Terraform Basics Training Course](https://kodekloud.com/courses/terraform-basics-training-course) | subscription | State, remote state on S3, import and debugging (section 10) |
| Labs | [AWS Playground](https://kodekloud.com/cloud-playgrounds/aws) and [100 Days of Cloud](https://kodekloud.com/100-days-of-cloud) | playground with plan; 100 Days free | Morning reps, and labs that would cost money in your own account (NAT, TGW, EKS) |
| Video | [AWS Networking Basics: AWS VPC & Subnets for Beginners](https://www.youtube.com/watch?v=QM63dyA_4Pc) (KodeKloud, 18 min) | free | Watch before section 3 if subnets and route tables feel abstract |

AWS-specific habits to build from day one:

- **Identity, region, account first.** Run `aws sts get-caller-identity` and check the region before
  every session. Half of all "it disappeared" and "AccessDenied" tickets end right there.
- **Tag everything you create** with `Project=lab` and an owner. Untagged resources become orphaned
  resources, and orphaned resources become bills.
- **Read the error literally.** AWS errors name the action, the resource and often the policy type
  that denied it. Copy the full text into your notes.
- **Prefer the reversible action.** Stop before terminate, deactivate a key before deleting it,
  disable a KMS key before scheduling deletion, snapshot before deleting a volume, `--dryrun` before
  `aws s3 rm`.
- **Every lab ends with teardown and a cost check.** The next morning, look at Cost Explorer.

After each lab, write the five-line note from your weekly rhythm: symptom, first wrong guess,
evidence that settled it, fix, what you will check first next time.

> Timebox: one topic per 30–45 minute morning slot. Until your CKA exam, CKA sessions come first,
> and the KodeKloud map puts AWS CloudOps after CKA. EKS (section 8) counts as CKA practice too.

### Sandbox account first

Every lab here runs in a **personal sandbox account** or a KodeKloud AWS playground, never in a
work account. The first hour of cloud learning is spent making that sandbox safe. Do these steps
in order, and do not launch anything until step 4 is done.

**Step 1 — Know which free tier you have.** AWS changed the Free Tier in July 2025. Accounts
created after 15 July 2025 get sign-up credits (USD 100, plus up to USD 100 more for completing
onboarding activities) and choose a *free plan* (up to six months, some services limited) or a
*paid plan*. Older accounts keep the classic 12-month offers (for example 750 hours a month of
t2.micro or t3.micro and 30 GB of EBS) until they expire. Some offers are always free in both
models. Check **Billing and Cost Management → Free Tier** in the console to see what yours has
instead of trusting a blog post.

**Step 2 — Lock the root user.** The root user is the email address that opened the account. It
can do anything, including close the account, and SCPs cannot restrict it in a standalone account.
Turn on MFA for root (AWS now requires it, but do it yourself on day one), never create root access
keys, store the password in a password manager, and log out. You will use root only for the few
tasks that need it, such as activating IAM access to billing.

**Step 3 — Create your daily identity.** Enable **IAM Identity Center** (formerly AWS SSO), create a
user for yourself with MFA, and assign the `AdministratorAccess` permission set to the sandbox
account. This gives you short-lived credentials from `aws sso login` instead of long-lived access
keys on disk. As root, also activate **IAM user and role access to Billing information** in account
settings, so your admin role can see costs.

**Step 4 — Budget alarm before any resource.** Create a monthly cost budget with alerts at 50% and
80% of actual spend and 100% of forecasted spend, and turn on Free Tier usage alerts in Billing
preferences. Cost Anomaly Detection is free; check that a monitor exists. From the CLI (the budget
API lives in us-east-1 regardless of where your resources run):

```bash
cat > budget.json <<'EOF'
{
  "BudgetName": "lab-monthly-10usd",
  "BudgetLimit": { "Amount": "10", "Unit": "USD" },
  "TimeUnit": "MONTHLY",
  "BudgetType": "COST"
}
EOF
cat > notifications.json <<'EOF'
[
  { "Notification": { "NotificationType": "ACTUAL", "ComparisonOperator": "GREATER_THAN",
                      "Threshold": 50, "ThresholdType": "PERCENTAGE" },
    "Subscribers": [ { "SubscriptionType": "EMAIL", "Address": "you@example.com" } ] },
  { "Notification": { "NotificationType": "ACTUAL", "ComparisonOperator": "GREATER_THAN",
                      "Threshold": 80, "ThresholdType": "PERCENTAGE" },
    "Subscribers": [ { "SubscriptionType": "EMAIL", "Address": "you@example.com" } ] },
  { "Notification": { "NotificationType": "FORECASTED", "ComparisonOperator": "GREATER_THAN",
                      "Threshold": 100, "ThresholdType": "PERCENTAGE" },
    "Subscribers": [ { "SubscriptionType": "EMAIL", "Address": "you@example.com" } ] }
]
EOF
aws budgets create-budget --account-id 123456789012 \
  --budget file://budget.json --notifications-with-subscribers file://notifications.json
aws budgets describe-budgets --account-id 123456789012 \
  --query 'Budgets[].[BudgetName,BudgetLimit.Amount,CalculatedSpend.ActualSpend.Amount]' --output table
```

```
----------------------------------------
|           DescribeBudgets            |
+---------------------+--------+-------+
|  lab-monthly-10usd  |  10.0  |  0.0  |
+---------------------+--------+-------+
```

→ `create-budget` prints nothing on success. A budget is an **alert, not a limit**: AWS will not
stop your resources when you cross it. The alarm buys you hours instead of a month of surprise.

**Step 5 — Install the CLI and log in with SSO.** On Ubuntu, the AWS CLI v2 is available as an
official snap (or use the bundled installer described in the AWS CLI user guide on
[docs.aws.amazon.com](https://docs.aws.amazon.com/)). Avoid the old `awscli` apt package, which is
CLI v1 on older releases. For `aws ssm start-session` later, also install the Session Manager
plugin `.deb` from the Session Manager section of the same docs.

```bash
sudo snap install aws-cli --classic
aws --version
aws configure sso            # session name: lab, start URL from Identity Center, region ap-south-1
aws sso login --profile lab-admin
export AWS_PROFILE=lab-admin
aws sts get-caller-identity
aws configure list
```

```
aws-cli/2.31.4 Python/3.13.7 Linux/6.8.0-85-generic exe/x86_64.ubuntu.24
{
    "UserId": "AROA4EXAMPLEROLEID1234:learner",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/AWSReservedSSO_AdministratorAccess_0a1b2c3d4e5f6a7b/learner"
}
      Name                    Value             Type    Location
      ----                    -----             ----    --------
   profile                lab-admin              env    ['AWS_PROFILE', 'AWS_DEFAULT_PROFILE']
access_key     ****************QX7Z              sso
secret_key     ****************d9Kc              sso
    region               ap-south-1      config-file    ~/.aws/config
```

→ The `Arn` shows an **assumed role** created by Identity Center, and `configure list` shows the
credentials came from `sso`, not from a key file. That is exactly what you want. The resulting
`~/.aws/config` looks like this:

```
[profile lab-admin]
sso_session = lab
sso_account_id = 123456789012
sso_role_name = AdministratorAccess
region = ap-south-1
output = json

[sso-session lab]
sso_start_url = https://d-1234567890.awsapps.com/start
sso_region = ap-south-1
sso_registration_scopes = sso:account:access
```

**Step 6 — Pick one region and stay in it.** Use ap-south-1 (or the region nearest you) for every
lab. Forgotten resources in a second region are the classic sandbox bill. Global services (IAM,
Route 53, CloudFront, Organizations, budgets) are not tied to your region.

**Step 7 — Learn the teardown hunt now.** Everything you create carries `Project=lab`, so one
command lists what is still alive. Run it at the end of every lab:

```bash
aws resourcegroupstaggingapi get-resources --tag-filters Key=Project,Values=lab \
  --query 'ResourceTagMappingList[].ResourceARN' --output text | tr '\t' '\n'
# Untagged leftovers that cost money even when "idle":
aws ec2 describe-instances --filters Name=instance-state-name,Values=running,stopped \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,Tags[?Key==`Name`]|[0].Value]' --output table
aws ec2 describe-nat-gateways --filter Name=state,Values=available --query 'NatGateways[].NatGatewayId'
aws ec2 describe-addresses --query 'Addresses[?AssociationId==null].PublicIp'
aws ec2 describe-volumes --filters Name=status,Values=available --query 'Volumes[].[VolumeId,Size]'
```

```
arn:aws:ec2:ap-south-1:123456789012:instance/i-0a1b2c3d4e5f60011
arn:aws:ec2:ap-south-1:123456789012:natgateway/nat-0a1b2c3d4e5f60012
arn:aws:elasticloadbalancing:ap-south-1:123456789012:loadbalancer/app/lab-alb/50dc6c495c0c9188
```

→ Three things still alive after the lab: an instance, a NAT gateway (about USD 33 a month on its
own) and an ALB (about USD 16 a month). Section 12 extends this into a cross-region bill hunt.

### Conventions

Each topic starts with a **Level** line: its stage tag, a time estimate and a **lab cost** label.

| Lab cost label | Meaning |
|---|---|
| free | Covered by the free tier or credits, or truly free (IAM, VPC, security groups) |
| cents | Under about USD 0.50 if you tear it down the same day |
| dollars | NAT gateways, Transit Gateway, VPN, EKS, Multi-AZ RDS: a few dollars per day. Use the KodeKloud AWS playground if your plan includes it, or tear down within hours |
| paper | Too expensive or slow to build for practice (Direct Connect, Control Tower in a real org): a design exercise instead |

Commands that change or delete things are marked in the text. Destructive ones come with a
⚠️ warning and the safer command first.

---

## 1. Cloud concepts

> 📚 **Study path:** 1) KodeKloud: *Crash Course: AWS Basics* — the whole 30-minute course, free ([link](https://kodekloud.com/courses/crash-course-aws-basics)) · 2) Note: this section, then [AWS reference](16-aws-cloud.md) section 1 (CLI identity and config) · 3) Video: *AWS Networking Basics: AWS VPC & Subnets for Beginners* (KodeKloud, 18 min) ([link](https://www.youtube.com/watch?v=QM63dyA_4Pc)) · 4) KodeKloud: *AWS Certified Cloud Practitioner (CLF-C02)* — its cloud concepts, global infrastructure and billing material, only if you want the badge ([link](https://kodekloud.com/courses/aws-cloud-practitioner-clf-c02)) · 5) Practice: the sandbox setup in section 0, then one task a day from [100 Days of Cloud](https://kodekloud.com/100-days-of-cloud)

Tags: [L0 · Fresher] for the first three topics, [L1 · Junior] for the on-prem mapping.

Four ideas carry the rest of the module: the cloud is an API, it is spread over regions and
availability zones, responsibility is split between you and AWS, and every resource has a meter.
The last topic maps your on-prem stack onto AWS so you can reuse everything you already know.

### What the cloud really is

**Level:** [L0 · Fresher] · about 30 minutes · lab cost: free

**Concept.** "The cloud" is someone else's data centers, sold to you through an **API**. When you
click "Launch instance" in the console, the console calls the same `RunInstances` API that the
CLI, Terraform and GitLab CI call. That single fact explains three things you will meet every day:

- **Everything is authorized.** Each API call is checked against IAM policies (section 2).
- **Everything is logged.** CloudTrail records who called which API, from where, and whether it
  failed (section 9).
- **Everything is metered.** You pay per second, per GB, per request or per hour for what exists,
  whether you use it or not (section 12).

Services sit on a spectrum of how much you manage. On-prem you own everything from the rack to the
app. With EC2 you still own the OS. With RDS or Fargate you own only configuration and data. With S3
or Lambda you own only your data and code.

```
 You manage ▼                On-prem      EC2 (IaaS)     RDS / Fargate     S3 / Lambda
 ─────────────────────────   ─────────    ──────────     ─────────────     ───────────
 Data, access, config         you          you            you               you
 Application code             you          you            you               you
 Runtime, middleware          you          you            AWS (mostly)      AWS
 Operating system, patches    you          you            AWS               AWS
 Virtualization               you          AWS            AWS               AWS
 Servers, storage, network    you          AWS            AWS               AWS
 Data center, power           you          AWS            AWS               AWS
```

**Key terms**

| Term | Meaning |
|---|---|
| IaaS / PaaS / SaaS | Infrastructure (VMs, disks, networks), Platform (managed runtimes, databases), Software (finished apps) as a service |
| Serverless | You run code or store data without managing servers or capacity (Lambda, S3, Fargate, DynamoDB) |
| Control plane | The APIs that create and change resources (`RunInstances`, `CreateBucket`) |
| Data plane | The running resource doing its job (the instance serving traffic, S3 serving objects) |
| Elasticity | Capacity follows demand: scale out under load, scale in when quiet, pay for what runs |
| Endpoint | The HTTPS URL an API call goes to, for example `ec2.ap-south-1.amazonaws.com` |

**See it on a real system**

```bash
aws ec2 describe-vpcs --debug 2>&1 | grep -m2 -E 'Endpoint provider result|Making request for OperationModel'
aws sts get-caller-identity --query Arn --output text
```

```
2026-10-03 09:12:41,201 - MainThread - botocore.regions - DEBUG - Endpoint provider result: https://ec2.ap-south-1.amazonaws.com
2026-10-03 09:12:41,207 - MainThread - botocore.endpoint - DEBUG - Making request for OperationModel(name=DescribeVpcs) with params: {...}
arn:aws:sts::123456789012:assumed-role/AWSReservedSSO_AdministratorAccess_0a1b2c3d4e5f6a7b/learner
```

→ A CLI command is a signed HTTPS request to a regional endpoint, made with a specific identity.
`--debug` is your `curl -v` for AWS: it shows which endpoint, which credentials and which
request were used (exact debug wording varies between CLI versions).

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create an S3 bucket in the console, then list it from the CLI. Same API,
two clients.

```bash
aws s3 ls
```

**Step 2 — Break it.** Run the same command with a profile that does not exist, and again with a
deliberately wrong region for a regional API:

```bash
aws s3 ls --profile nosuchprofile
aws ec2 describe-instances --region eu-north-1 --query 'Reservations[].Instances[].InstanceId'
```

```
The config profile (nosuchprofile) could not be found
[]
```

→ The second command "succeeds" with an empty list. Nothing is wrong with your instances; you asked
the wrong region. This is the single most common fresher mistake on AWS.

**Step 3 — Fix it.** Always pin the region in your profile and say it out loud in tickets: "i-0abc
in ap-south-1, account 123456789012".

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Wrong region | Resource "missing", empty lists, `InvalidInstanceID.NotFound` | `aws configure list` | [AWS reference](16-aws-cloud.md) |
| Wrong account or role | `AccessDenied`, unexpected resources | `aws sts get-caller-identity` | section 2 |
| Expired SSO session | `Error when retrieving token from sso: Token has expired and refresh failed` | `aws sso login --profile PROFILE` | section 2 |
| Clock skew on the client | `SignatureDoesNotMatch`, `RequestTimeTooSkewed` | `timedatectl` | [Time & NTP](12-time-ntp.md) |

**Why it matters for troubleshooting.** On-prem you reason about machines. On AWS you also reason
about **API calls**: who made them, where they went and what they were allowed to do. Every AWS
investigation starts with identity, region and account, the same way an on-prem one starts with
"which host am I on?".

**Next step:** where those regional endpoints physically are: regions and availability zones.

### Regions, AZs and the edge

**Level:** [L0 · Fresher] · about 30 minutes · lab cost: free

**Concept.** A **region** is a geographic area (ap-south-1 is Mumbai) containing several
**availability zones**. An AZ is one or more discrete data centers with independent power, cooling
and networking, connected to the other AZs of the region by redundant low-latency links. New
regions launch with at least three AZs. Most services are **regional**: a VPC, an EC2 instance, an
S3 bucket's data and an RDS database live in one region. A few are **global**: IAM, Route 53,
CloudFront, Organizations. **Edge locations** (hundreds of them, in many more cities) serve
CloudFront and Route 53 close to users. Local Zones and Outposts push AWS infrastructure closer to
users or into your own data center.

```
 Region ap-south-1 (Mumbai)
 ┌──────────────────────────────────────────────────────────────────┐
 │  AZ ap-south-1a        AZ ap-south-1b        AZ ap-south-1c        │
 │  (id aps1-az1)         (id aps1-az3)         (id aps1-az2)         │
 │  ┌────────────┐        ┌────────────┐        ┌────────────┐        │
 │  │ DC  DC     │◀──────▶│ DC         │◀──────▶│ DC  DC     │        │
 │  │ power, net │  low-latency private links    │ power, net │        │
 │  └────────────┘        └────────────┘        └────────────┘        │
 │  subnet lives in ONE AZ; an EBS volume lives in ONE AZ              │
 │  VPC, S3 bucket, ALB, RDS Multi-AZ span the region's AZs            │
 └──────────────────────────────────────────────────────────────────┘
```

A subtle senior point: the AZ **name** `ap-south-1a` is mapped to a physical AZ **per account**, so
your `1a` and another account's `1a` may be different buildings. The **AZ ID** (`aps1-az1`) is the
same for everyone. Use AZ IDs when you coordinate across accounts (shared subnets, PrivateLink,
VPN partners, capacity reservations).

**Key terms**

| Term | Meaning |
|---|---|
| Region | Isolated geographic area, own endpoints, own copies of regional services |
| Availability zone | Failure domain inside a region; design so losing one AZ is survivable |
| AZ ID | Account-independent identifier of a physical AZ, such as `aps1-az1` |
| Edge location | CloudFront and Route 53 point of presence near users |
| Global service | IAM, Route 53, CloudFront, Organizations: not tied to a region (their API is often served from us-east-1) |
| Opt-in region | Newer regions you must enable before use (every region launched after 20 March 2019) |

**See it on a real system**

```bash
aws ec2 describe-availability-zones --region ap-south-1 \
  --query 'AvailabilityZones[].[ZoneName,ZoneId,State]' --output table
aws ec2 describe-regions --query 'Regions[].RegionName' --output text | wc -w
```

```
--------------------------------------------
|        DescribeAvailabilityZones         |
+---------------+------------+-------------+
|  ap-south-1a  |  aps1-az1  |  available  |
|  ap-south-1b  |  aps1-az3  |  available  |
|  ap-south-1c  |  aps1-az2  |  available  |
+---------------+------------+-------------+
17
```

→ Note the name-to-ID mapping in your account (`1b` is `az3` here). The region count only includes
regions enabled for your account; opt-in regions are missing until you enable them.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Write a one-liner that lists running or stopped instances in **every**
enabled region. Keep it; it is your forgotten-resource detector.

```bash
for r in $(aws ec2 describe-regions --query 'Regions[].RegionName' --output text); do
  n=$(aws ec2 describe-instances --region "$r" \
        --filters Name=instance-state-name,Values=running,stopped \
        --query 'length(Reservations[].Instances[])' --output text)
  [ "$n" != "0" ] && echo "$r $n"
done
```

```
ap-south-1 1
us-east-1 1
```

**Step 2 — Break it.** Launch a t3.micro in us-east-1 "by accident" (switch the console region),
then try to find it with your default profile.

**Step 3 — Fix it.** Your loop finds it. Terminate it and add the loop to your end-of-lab routine.
For a full inventory across services, the console's **Resource Explorer** (aggregator index) or
**Tag Editor** search all regions at once.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Resource in another region | Bill line for a region you "never used" | the loop above | section 12 |
| AZ out of capacity for a type | `InsufficientInstanceCapacity` on launch | retry in another AZ or type | section 9 (Auto Scaling) |
| Single-AZ design during an AZ event | Whole site down while AWS status shows one AZ impaired | `aws ec2 describe-availability-zones` | section 13 |
| Cross-account AZ confusion | "Same AZ" partner has extra latency or cross-AZ charges | compare `ZoneId`, not `ZoneName` | section 3 |

**Why it matters for troubleshooting.** Regions and AZs are the cloud's failure domains, the same
way a rack and a building are on-prem. "Is it only one AZ?" is the first question in any AWS
outage, and the answer decides whether you wait, fail over, or redesign.

**Next step:** who is responsible for what inside those data centers.

### Shared responsibility

**Level:** [L0 · Fresher] · about 25 minutes · lab cost: free

**Concept.** AWS is responsible for security **of** the cloud: buildings, hardware, hypervisor,
the network between AZs, and the software of managed services. You are responsible for security
**in** the cloud: your data, IAM, network rules, encryption choices, and the operating system on
anything where you can log in. The line moves with the service.

| Service | AWS handles | You still handle |
|---|---|---|
| EC2 | Hardware, hypervisor, physical network | OS patching, UFW/SG rules, users and SSH keys, agents, backups, app |
| EBS | Durability inside the AZ, replication of blocks | Snapshots, encryption setting, sizing, deleting what you do not need |
| RDS | OS and engine patching (in your maintenance window), backups machinery, failover | Engine version choice, parameters, users and grants, SG, encryption at creation, testing restores |
| S3 | Durability (11 nines), availability, the service | Bucket policies, Block Public Access, versioning, lifecycle, encryption choice |
| ECS on Fargate | Hosts, OS, container runtime | Images (and their CVEs), task roles, secrets, network rules |
| EKS | Control plane (API server, etcd) | Nodes (unless Fargate or Auto Mode), add-ons, upgrades, RBAC, workloads |

**Key terms**

| Term | Meaning |
|---|---|
| Security of the cloud | AWS's half: facilities, hardware, virtualization, managed service software |
| Security in the cloud | Your half: identity, data, configuration, OS where you have root |
| Maintenance window | Weekly slot in which AWS may patch a managed service you run (RDS, ElastiCache) |
| Compliance inheritance | Certifications AWS holds for its half (ISO 27001, SOC 2) that you can reference in audits |

**See it on a real system**

```bash
# On an Ubuntu EC2 instance: patching is yours
apt list --upgradable 2>/dev/null | head -5
systemctl status unattended-upgrades --no-pager | head -3
# On a managed database: AWS schedules engine patches, you choose the window
aws rds describe-pending-maintenance-actions --output table \
  --query 'PendingMaintenanceActions[].[ResourceIdentifier,PendingMaintenanceActionDetails[0].Action,PendingMaintenanceActionDetails[0].AutoAppliedAfterDate]'
```

```
Listing...
linux-aws/noble-updates 6.8.0-1036.38 amd64 [upgradable from: 6.8.0-1031.33]
openssl/noble-updates 3.0.13-0ubuntu3.6 amd64 [upgradable from: 3.0.13-0ubuntu3.5]
● unattended-upgrades.service - Unattended Upgrades Shutdown
     Loaded: loaded (/usr/lib/systemd/system/unattended-upgrades.service; enabled; preset: enabled)
     Active: active (running) since Fri 2026-10-02 08:02:11 UTC; 1 day ago
---------------------------------------------------------------------------------------------------
|                                DescribePendingMaintenanceActions                                |
+-------------------------------------------------+-----------------+-----------------------------+
|  arn:aws:rds:ap-south-1:123456789012:db:lab-db  |  system-update  |  2026-10-20T00:00:00+00:00  |
+-------------------------------------------------+-----------------+-----------------------------+
```

→ On EC2 the kernel update waits for **you**. On RDS, AWS has queued an OS update and will apply
it automatically after the date shown, inside your maintenance window, unless you apply it earlier.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Take the table above and fill in a third column for your own on-prem stack:
who patches Apache, Docker, Harbor, the hypervisor, the switches? (On-prem: you, for everything.)

**Step 2 — Break it.** Imagine your lab EC2 instance from section 4 with SSH open to 0.0.0.0/0 and
password login enabled. List which half of the model each failure belongs to.

**Step 3 — Fix it.** Every item on the list is yours: SG, sshd config, patching. That is the point.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Unpatched EC2 exploited | GuardDuty finding, CPU pegged by a miner | `aws guardduty list-findings --detector-id DETECTOR_ID` | [Security & DevSecOps](37-learn-security-devsecops.md) |
| Public bucket with data | Access Analyzer or Security Hub finding | `aws s3api get-public-access-block --bucket BUCKET` | section 5 |
| RDS publicly accessible with weak password | Brute-force attempts in DB logs | `aws rds describe-db-instances --query 'DBInstances[].PubliclyAccessible'` | section 7 |
| "AWS patched it" assumption | Maintenance reboot surprises the app | `aws rds describe-pending-maintenance-actions` | section 7 |

**Why it matters for troubleshooting.** When something breaks, the shared responsibility line tells
you whether to open a support case or open a terminal. Almost every incident in this module is on
**your** side of the line.

**Next step:** what each of these choices costs.

### Pricing models

**Level:** [L0 · Fresher] → [L1 · Junior] · about 35 minutes · lab cost: free

**Concept.** AWS bills on a few dimensions: **time** (instance-seconds, NAT-hours, load
balancer-hours), **capacity** (GB-months of EBS or S3), **requests** (S3 GETs, KMS calls, API
calls), and **data transfer** (out to the internet, between AZs, between regions). For compute
there are five ways to pay:

| Model | Discount vs On-Demand | Commitment | Good for | Risk |
|---|---|---|---|---|
| On-Demand | none | none, per second (Linux, 60 s minimum) | Labs, spiky or unknown load | Most expensive steady state |
| Savings Plans (Compute / EC2 Instance) | up to roughly 66% / 72% | USD per hour for 1 or 3 years | Steady baseline across EC2, Fargate, Lambda | Paying for unused commitment |
| Reserved Instances | similar to Savings Plans | specific type/region, 1 or 3 years | RDS, ElastiCache, OpenSearch, Redshift when you want the deepest database discount (Database Savings Plans, since December 2025, cover RDS, Aurora, ElastiCache, DynamoDB and more with smaller discounts but more flexibility) | Wrong family or size, no flexibility |
| Spot | up to 90% | none, but AWS can reclaim with a 2-minute warning | CI runners, batch, stateless ASGs | Interruptions you must handle |
| Dedicated Hosts / Instances | premium | per host | Licensing (per-socket), compliance | Cost |

Rough monthly numbers worth memorizing (us-east-1, 730 hours):

| Item | Approximate price | About per month |
|---|---|---|
| t3.micro On-Demand | USD 0.0104/hour | USD 7.60 |
| t3.medium On-Demand | USD 0.0416/hour | USD 30 |
| m7i.large On-Demand | USD 0.1008/hour | USD 74 |
| gp3 EBS | USD 0.08/GB-month | USD 8 per 100 GB |
| S3 Standard | USD 0.023/GB-month | USD 2.30 per 100 GB |
| NAT gateway | USD 0.045/hour + USD 0.045/GB processed | USD 33 + data |
| Application Load Balancer | USD 0.0225/hour + LCUs | USD 16 + usage |
| Public IPv4 address (since Feb 2024) | USD 0.005/hour, in use or idle | USD 3.65 each |
| Data transfer out to internet | about USD 0.09/GB after the first 100 GB per month | depends |
| Cross-AZ traffic | USD 0.01/GB in each direction | depends |

**Key terms**

| Term | Meaning |
|---|---|
| On-Demand | Pay per second with no commitment |
| Savings Plan | Commit to USD per hour of compute for 1 or 3 years in exchange for a discount |
| Spot | Spare capacity at a discount that can be reclaimed with a 2-minute notice |
| Free tier | Credits or free monthly allowances for new accounts (see section 0) |
| Data transfer | Traffic charges; inbound from the internet is free, outbound and cross-AZ are not |
| Unit price | The price of one dimension, such as per GB-month or per million requests |

**See it on a real system**

```bash
aws ec2 describe-spot-price-history --instance-types t3.medium \
  --product-descriptions "Linux/UNIX" --start-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --query 'SpotPriceHistory[].[AvailabilityZone,SpotPrice]' --output table
```

```
------------------------------
|  DescribeSpotPriceHistory  |
+---------------+------------+
|  ap-south-1a  |  0.016100  |
|  ap-south-1b  |  0.015700  |
|  ap-south-1c  |  0.016900  |
+---------------+------------+
```

→ Spot is about a third of the On-Demand price here, and differs per AZ. That difference is why a
Spot fleet should be allowed to use several AZs and several instance types.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** On paper, price a small stack for one month: two t3.medium web servers, one
ALB, one NAT gateway, 100 GB gp3, 50 GB S3, 200 GB out to the internet.

**Step 2 — Break it.** Add the "forgotten" items: two public IPv4 addresses, cross-AZ traffic of
500 GB between the web servers and a database in another AZ, and CloudWatch Logs ingestion of
20 GB. Recalculate.

**Step 3 — Fix it.** Find the two biggest lines and write one sentence each on how to cut them
(answers in section 12: NAT data and cross-AZ traffic are usually the surprise).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Spot interruption not handled | Instances vanish, jobs fail mid-run | `aws ec2 describe-spot-instance-requests` | section 12 |
| Burstable instance in unlimited mode at high CPU | "CPU Credits" line on the bill | `aws ec2 describe-instance-credit-specifications` | section 4 |
| Savings Plan not covering usage | Coverage report under 100% while you expected full | Cost Explorer, Savings Plans coverage | section 12 |
| Free tier expired or credits used | Bill jumps on a date, not after a change | Billing → Free Tier | section 0 |

**Why it matters for troubleshooting.** On AWS, cost is an operational signal. A sudden jump in
NAT bytes or data transfer often reveals a misrouted pipeline or a loop before any alert fires.
Knowing the unit prices lets you read the bill like a log.

**Next step:** map all of this onto the stack you already run on-prem.

### On-prem to AWS mapping

**Level:** [L1 · Junior] · about 45 minutes · lab cost: cents

**Concept.** Almost every on-prem building block has an AWS equivalent. Knowing the mapping lets
you reuse your troubleshooting instincts, and knowing where the mapping **breaks** saves you from
the traps that catch on-prem engineers.

| On-prem (your world) | AWS equivalent | What is different |
|---|---|---|
| VLAN / L2 segment | Subnet | One AZ only; no broadcast, no multicast by default, no gratuitous ARP; AWS answers ARP |
| Router / L3 switch | Route table + implicit VPC router (subnet base + 1) | Longest-prefix match like Linux; you edit routes via API, not on a box |
| Edge firewall (nftables, pfSense) | NACL (subnet, stateless) + security group (ENI, stateful) | SGs are allow-only and follow the instance; NACLs need ephemeral return ports |
| UFW on the host | Still UFW on the instance, inside the SG | Two layers; Ubuntu AMIs ship with UFW inactive |
| NAT on the firewall | NAT gateway (per AZ) | Billed per hour and per GB processed |
| Internet uplink | Internet gateway | Does 1:1 NAT for public IPs; the instance never sees its public IP on `ens5` |
| VM on VMware/KVM | EC2 instance | Instance types instead of custom vCPU/RAM; host maintenance can force a stop/start |
| VM template / golden image | AMI | Region-scoped; copy it to use elsewhere |
| SAN LUN (iSCSI, FC) | EBS volume | AZ-bound; performance is provisioned (gp3 IOPS/throughput) and capped by instance type |
| NAS / NFS share | EFS (NFS v4.1) or FSx | Pay per GB stored; throughput modes |
| Backup target, MinIO | S3, S3 Glacier | Object storage, not a filesystem |
| HAProxy / F5 / Apache proxy / Traefik | ALB (L7) / NLB (L4) | Managed, multi-AZ, health checks with reason codes |
| BIND / AD DNS | Route 53 (public and private zones) + Resolver | Alias records; Amazon DNS at VPC base + 2 |
| LDAP / AD groups, sudoers | IAM Identity Center + IAM roles and policies | Every API call authorized and logged |
| Nagios / Prometheus / Grafana | CloudWatch metrics and alarms | Memory and disk need the agent |
| rsyslog server, Loki | CloudWatch Logs | Retention defaults to never expire |
| cron on a box | EventBridge Scheduler | Managed, IAM-authorized |
| Ansible inventory and ad-hoc | Tags + SSM Run Command / State Manager | Works on on-prem servers too (hybrid activation) |
| SSH bastion / jump host | SSM Session Manager | No inbound port, IAM-authenticated, logged |
| Harbor | ECR | IAM auth, 12-hour login tokens, lifecycle policies |
| Docker Swarm + Dokploy | ECS (EC2 or Fargate) | Task definitions instead of compose files |
| kubeadm cluster | EKS | You never see the control plane nodes or etcd |
| PostgreSQL VM + streaming replica | RDS Multi-AZ / read replica, Aurora | No SSH, parameter groups, failover via DNS |
| HashiCorp Vault | Secrets Manager / SSM Parameter Store | IAM-authorized, KMS-encrypted |
| Private CA (your Harbor CA) | AWS Private CA; ACM for public certs | Standard ACM public certs attach only to integrated AWS services (ALB, CloudFront); exportable public certs (since June 2025, paid per name) can be installed on EC2 or on-prem |
| MPLS / leased line | Direct Connect | Weeks of lead time; not encrypted by default |
| IPsec to a branch | Site-to-Site VPN | Two tunnels per connection, both should be up |
| Change log, audit log | CloudTrail | Every API call, 90 days in event history for free |
| CMDB | AWS Config | Resource configuration history and rules |

Where the mapping breaks, and how on-prem habits fail:

- **keepalived / VRRP floating IPs do not work.** The VPC does not honour gratuitous ARP, so a
  "moved" virtual IP stays where AWS thinks it is. Use an NLB, or move an Elastic IP or secondary
  private IP by API.
- **Source/destination check.** An instance drops traffic not addressed to itself unless you disable
  the check. Your Linux router or VPN box on EC2 needs that.
- **No packet capture on the switch.** There is no SPAN port; use tcpdump on the instance, VPC
  Traffic Mirroring, or Flow Logs (summaries only).
- **Netplan belongs to cloud-init.** On Ubuntu EC2, cloud-init writes `/etc/netplan/50-cloud-init.yaml`
  at boot. Your edits there can be overwritten; put changes in another file or disable cloud-init's
  network config deliberately.

```
 On-prem today                                AWS equivalent
 ┌─────────────────────────────────┐          ┌─────────────────────────────────────────────┐
 │ ISP ─ edge FW (NAT, nftables)    │          │ IGW ─ NACL ─ public subnet: ALB, NAT GW      │
 │   └ VLAN 10 192.168.10.0/24      │          │                └ route table 0/0 → IGW       │
 │      ├ apache01  :81 :444        │   ==>    │ private subnet: EC2 (SG) Apache :81           │
 │      ├ dokploy01 Traefik :80/443 │          │                 ECS/Fargate tasks             │
 │      ├ harbor01  (private CA)    │          │ ECR, ACM certificate on the ALB               │
 │      └ pg01      PostgreSQL 16   │          │ data subnet: RDS PostgreSQL Multi-AZ          │
 │ BIND 192.168.10.53               │          │ Route 53 + Resolver endpoints                 │
 └─────────────────────────────────┘          └─────────────────────────────────────────────┘
```

**Key terms**

| Term | Meaning |
|---|---|
| ENI | Elastic network interface: the virtual NIC an SG attaches to |
| Elastic IP (EIP) | Static public IPv4 you own until you release it |
| Source/destination check | ENI setting that drops traffic not addressed to the instance |
| cloud-init | The first-boot agent that applies user data, SSH keys and netplan config on EC2 |
| Amazon DNS | The VPC resolver at the VPC base address + 2 (10.20.0.2) and 169.254.169.253 |

**See it on a real system**

```bash
# On an Ubuntu 24.04 EC2 instance: it is just Ubuntu
ip -br addr
ip route
resolvectl status ens5 | sed -n '1,8p'
sudo cat /etc/netplan/50-cloud-init.yaml
sudo ufw status
```

```
lo               UNKNOWN        127.0.0.1/8 ::1/128
ens5             UP             10.20.17.25/20 metric 100 fe80::8a3:4fff:fe21:7b1d/64
default via 10.20.16.1 dev ens5 proto dhcp src 10.20.17.25 metric 100
10.20.0.2 via 10.20.16.1 dev ens5 proto dhcp src 10.20.17.25 metric 100
10.20.16.0/20 dev ens5 proto kernel scope link src 10.20.17.25 metric 100
10.20.16.1 dev ens5 proto dhcp scope link src 10.20.17.25 metric 100
Link 2 (ens5)
    Current Scopes: DNS
         Protocols: +DefaultRoute -LLMNR -mDNS -DNSOverTLS DNSSEC=no/unsupported
Current DNS Server: 10.20.0.2
       DNS Servers: 10.20.0.2
        DNS Domain: ap-south-1.compute.internal
network:
    ethernets:
        ens5:
            dhcp4: true
            dhcp6: false
            match:
                macaddress: 0a:13:4f:21:7b:1d
            set-name: ens5
    version: 2
Status: inactive
```

→ Everything you know applies: netplan, systemd-resolved, `ip route`. The default gateway is the
VPC router at subnet base + 1, DNS is the Amazon resolver at VPC base + 2, there is no public IP on
the interface (the IGW translates it), and UFW is off, so the SG is the only firewall until you
turn UFW on.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Draw your current on-prem Apache/Dokploy/Harbor/PostgreSQL stack and write
the AWS equivalent next to each box, using the table. Keep the drawing; sections 3–8 build it.

**Step 2 — Break it.** On a lab instance (section 4), add a static DNS server by editing
`/etc/netplan/50-cloud-init.yaml`, run `sudo netplan apply`, then reboot. Check whether your
change survived.

**Step 3 — Fix it.** Put the change in its own file, for example
`/etc/netplan/60-dns.yaml` with `nameservers: addresses: [10.20.0.2]` under `ens5`, and keep
permissions at 600. If you truly need to own networking, disable cloud-init's network rendering
with a file in `/etc/cloud/cloud.cfg.d/` containing `network: {config: disabled}`, knowing that you
now own every future NIC change.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| keepalived VIP moved but unreachable | Failover "works" in logs, clients time out | `ip addr`, then check the ENI's private IPs in the console | section 6 (use an NLB) |
| Router/VPN instance drops forwarded traffic | Routes correct, packets vanish | `aws ec2 describe-instances --query 'Reservations[].Instances[].SourceDestCheck'` | section 11 |
| UFW enabled without allowing SSH or SSM path | Locked out after `ufw enable` | serial console or SSM | section 4 |
| Netplan change lost after reboot | DNS or routes revert | `ls /etc/netplan/`, `cloud-init status --long` | [DNS](08-dns.md) |

**Why it matters for troubleshooting.** The cloud adds layers **around** the OS (SG, NACL, route
tables, IGW, NAT) but the OS layer is unchanged. When a request fails you walk the same path as
on-prem, with a few extra checkpoints. [Learn: Networking](28-learn-networking.md) is still the
foundation.

**Next step:** the layer that authorizes every one of those API calls: IAM.

---

## 2. IAM and identity

> 📚 **Study path:** 1) KodeKloud: *Crash Course: AWS Basics* — refresher on users and roles if you are a Fresher ([link](https://kodekloud.com/courses/crash-course-aws-basics)) · 2) Note: this section, then [AWS reference](16-aws-cloud.md) section 1 and the on-prem analogy in [Users & permissions](10-users-permissions-security.md) · 3) KodeKloud: *AWS Certified CloudOps Engineer - Associate* — the Security domain (IAM, roles, policies), after CKA ([link](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 4) Practice: in the [AWS Playground](https://kodekloud.com/cloud-playgrounds/aws) or your sandbox, reproduce the three denials from "Debugging AccessDenied" and solve each in under 10 minutes

Tags: [L0 · Fresher] → [L1 · Junior] for identities and keys, [L2 · Mid] for evaluation and debugging, [L3 · Senior] for Organizations.

IAM decides whether **every** API call succeeds. On-prem, a permission problem shows up as
`Permission denied` from one file or one sudo rule. On AWS it shows up as `AccessDenied` from one of
six policy types, and the skill is knowing which one, with evidence. Start with the building
blocks, then learn the evaluation logic, then debug like a Mid-level engineer, then govern many
accounts like a Senior.

### Identities and policies

**Level:** [L0 · Fresher] → [L1 · Junior] · about 45 minutes · lab cost: free

**Concept.** A **principal** makes a request: the root user, an **IAM user** (a long-lived identity,
ideally rare), a **role** (an identity with no password or keys of its own, which people and
services *assume* for temporary credentials), or a federated user from Identity Center. A
**policy** is a JSON document that answers four questions: **who** (Principal, only in resource
policies), may do **what** (Action), on **which** thing (Resource), under **which conditions**
(Condition). Policies attach to identities (identity-based) or to resources such as buckets, KMS
keys and roles (resource-based; a role's **trust policy** is a resource policy that says who may
assume it).

```
 "Can role app-ec2-role do s3:GetObject on lab-artifacts/build.tar.gz?"
     WHO (principal)      WHAT (action)        WHICH (resource)                       WHEN (condition)
 arn:...:role/app-ec2-role  s3:GetObject   arn:aws:s3:::lab-artifacts-123456789012/*   aws:SecureTransport = true
```

A read-only policy for one bucket, the shape you will write most often:

```
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "ListTheBucket",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::lab-artifacts-123456789012" },
    { "Sid": "ReadObjects",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::lab-artifacts-123456789012/*" }
  ]
}
```

Note the two resources: `s3:ListBucket` acts on the **bucket** ARN, `s3:GetObject` on **object**
ARNs (`/*`). Mixing them up is the most common S3 policy bug.

**Key terms**

| Term | Meaning |
|---|---|
| Principal | The identity making the request (user, role session, service, account) |
| IAM user | Long-lived identity with a password and/or access keys; avoid for humans and machines alike |
| Role | Identity assumed for temporary credentials; has a trust policy and permission policies |
| Trust policy | Resource policy on a role: who may call `sts:AssumeRole` on it |
| Instance profile | The container that hands a role to an EC2 instance through IMDS |
| Managed vs inline policy | Reusable standalone policy vs a policy embedded in one identity |
| ARN | Amazon Resource Name, for example `arn:aws:iam::123456789012:role/app-ec2-role` |

**See it on a real system**

```bash
aws iam list-attached-role-policies --role-name app-ec2-role --output table
aws iam get-role --role-name app-ec2-role --query 'Role.AssumeRolePolicyDocument'
aws iam list-instance-profiles-for-role --role-name app-ec2-role \
  --query 'InstanceProfiles[].InstanceProfileName' --output text
```

```
---------------------------------------------------------------------------------------------
|                                  ListAttachedRolePolicies                                 |
+-------------------------------------------------------------------------------------------+
||                                     AttachedPolicies                                    ||
|+--------------------------------------------------------+--------------------------------+|
||                       PolicyArn                        |           PolicyName           ||
|+--------------------------------------------------------+--------------------------------+|
||  arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore  |  AmazonSSMManagedInstanceCore  ||
||  arn:aws:iam::123456789012:policy/lab-artifacts-read   |  lab-artifacts-read            ||
|+--------------------------------------------------------+--------------------------------+|
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": { "Service": "ec2.amazonaws.com" },
            "Action": "sts:AssumeRole"
        }
    ]
}
app-ec2-profile
```

→ Two halves of a role: the **permissions** (what it may do) and the **trust policy** (who may
become it: here, the EC2 service on behalf of an instance). The instance profile is what you attach
to the instance.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create the bucket policy above as a managed policy `lab-artifacts-read`,
create role `app-ec2-role` trusted by `ec2.amazonaws.com`, attach the policy plus
`AmazonSSMManagedInstanceCore`, and attach the role to a lab instance (section 4) through an
instance profile. On the instance:

```bash
aws sts get-caller-identity --query Arn --output text
aws s3 ls s3://lab-artifacts-123456789012/
aws s3 ls
```

```
arn:aws:sts::123456789012:assumed-role/app-ec2-role/i-0a1b2c3d4e5f60011
2026-10-02 09:31:07   10485760 build.tar.gz

An error occurred (AccessDenied) when calling the ListBuckets operation: User: arn:aws:sts::123456789012:assumed-role/app-ec2-role/i-0a1b2c3d4e5f60011 is not authorized to perform: s3:ListAllMyBuckets because no identity-based policy allows the s3:ListAllMyBuckets action
```

→ The instance is the role (the session name is the instance ID). It can list its one bucket but
not all buckets. Least privilege, working as designed.

**Step 2 — Break it.** Detach the role from the instance (console: Actions → Security → Modify IAM
role → No IAM role) and repeat the commands.

```
Unable to locate credentials. You can configure credentials by running "aws configure".
```

**Step 3 — Fix it.** Reattach the instance profile; credentials appear within seconds through IMDS.
Never "fix" this by copying access keys onto the instance.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| No instance profile | `Unable to locate credentials` on EC2 | `aws ec2 describe-instances --query 'Reservations[].Instances[].IamInstanceProfile'` | section 4 (IMDS) |
| Bucket vs object ARN mix-up | `AccessDenied` on GetObject or ListBucket only | read the policy Resource lines | section 5 |
| Trust policy wrong | `not authorized to perform: sts:AssumeRole` | `aws iam get-role --role-name ROLE_NAME` | next topics |
| Using an IAM user's keys everywhere | Keys in repos, no rotation | `aws iam list-access-keys` | "Keys, MFA and Identity Center" |

**Why it matters for troubleshooting.** Most AWS "it does not work" tickets are not network or
service failures but authorization. Recognizing principal, action, resource and condition in an
error message turns a mystery into a one-line policy fix.

**Next step:** how AWS combines all the policies that apply to one request.

### Policy evaluation logic

**Level:** [L2 · Mid] · about 45 minutes · lab cost: free

**Concept.** Every request starts as **denied**. AWS collects every policy that applies and walks
them in a fixed order. One **explicit Deny anywhere wins**. Otherwise the request needs an
**Allow** that survives every guardrail layer.

```
 request ──▶ any explicit Deny in ANY applicable policy? ── yes ──▶ DENY (explicit)
                │ no
                ▼
        Organizations SCPs / RCPs allow it?  ── no ──▶ DENY (implicit)    [guardrails: max permissions]
                │ yes (or no org)
                ▼
        resource-based policy allows this principal? ── yes, same account ──▶ ALLOW (for most services)
                │ no / cross-account
                ▼
        permissions boundary allows it? ── no ──▶ DENY (implicit)          [guardrail on the identity]
                │ yes (or none)
                ▼
        session policy allows it? ── no ──▶ DENY (implicit)                 [guardrail on this session]
                │ yes (or none)
                ▼
        identity-based policy allows it? ── no ──▶ DENY (implicit)
                │ yes
                ▼
              ALLOW
```

Rules worth memorizing:

- **Guardrails never grant.** SCPs, RCPs, permissions boundaries and session policies only cap what
  identity or resource policies grant.
- **Same account:** an Allow in **either** the identity policy or the resource policy is enough
  (exceptions: KMS key policies and role trust policies must allow explicitly).
- **Cross-account:** **both** sides must allow: the caller's identity policy in account A **and** the
  resource policy in account B.
- **Conditions are part of the match.** A statement whose condition is false does not apply, so an
  Allow with `aws:SourceIp` from the office does nothing when you work from home.

**Key terms**

| Term | Meaning |
|---|---|
| Implicit deny | No policy allowed it; the default for everything |
| Explicit deny | A statement with `"Effect": "Deny"` matched; nothing can override it |
| SCP / RCP | Organization-level maximum permissions for principals / for resources |
| Permissions boundary | Managed policy that caps what a user or role can ever do |
| Session policy | Policy passed when assuming a role, capping that one session |
| Condition key | Context such as `aws:SourceIp`, `aws:PrincipalTag/team`, `aws:SecureTransport` |

**See it on a real system**

```bash
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/app-ec2-role \
  --action-names s3:GetObject s3:PutObject s3:DeleteObject \
  --resource-arns arn:aws:s3:::lab-artifacts-123456789012/build.tar.gz \
  --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output table
```

```
--------------------------------------
|      SimulatePrincipalPolicy       |
+-------------------+----------------+
|  s3:GetObject     |  allowed       |
|  s3:PutObject     |  implicitDeny  |
|  s3:DeleteObject  |  explicitDeny  |
+-------------------+----------------+
```

→ Three different outcomes (this run assumes the read-only policy plus a Deny on `s3:DeleteObject`
like the one in the lab below): allowed by a statement, denied because nothing allowed it, and denied by
a matching Deny statement. Drop the `--query` to see `MatchedStatements`, which names the policy
and statement responsible. The simulator does not reproduce every real-world context (some
resource policies, SCP/RCP details, session tags, VPC endpoint policies), so confirm surprising
results with a real call and CloudTrail.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Add an inline policy to `app-ec2-role` that allows `s3:*` on the bucket and
its objects, plus this Deny:

```
{ "Effect": "Deny", "Action": "s3:DeleteObject",
  "Resource": "arn:aws:s3:::lab-artifacts-123456789012/*" }
```

**Step 2 — Break it.** From the instance, try `aws s3 rm s3://lab-artifacts-123456789012/build.tar.gz`.
The `s3:*` Allow does not help; the explicit Deny wins. Then add a condition to the Allow statement
(`"Condition": {"IpAddress": {"aws:SourceIp": "203.0.113.0/24"}}`) and watch even reads fail from
the instance, because its requests do not come from that range.

**Step 3 — Fix it.** Remove the condition (or use `aws:SourceVpc` / `aws:SourceVpce` conditions,
which match traffic through a VPC endpoint, not public source IPs). Re-run the simulator after
every change and compare with the real call.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Explicit Deny somewhere | `... with an explicit deny in a service control policy` (or identity-based / resource-based policy) | read the error's policy type | next topics |
| Permissions boundary caps a new role | Admin policy attached, still denied, message mentions permissions boundary | `aws iam get-role --role-name ROLE_NAME --query Role.PermissionsBoundary` | "Debugging AccessDenied" |
| Condition never true | Works from office, fails from CI or EC2 | simulator with `--context-entries` | "Debugging AccessDenied" |
| Cross-account half missing | Owner account allows, caller still denied | check both accounts' policies | "Roles, STS and assume-role" |

**Why it matters for troubleshooting.** "But I attached AdministratorAccess!" is answered by this
diagram: an explicit Deny, an SCP or a boundary sits above it. Walk the layers top-down instead of
adding more Allows.

**Next step:** temporary credentials, which is how all of this is meant to be used.

### Roles, STS and assume-role

**Level:** [L1 · Junior] → [L2 · Mid] · about 45 minutes · lab cost: free

**Concept.** The **Security Token Service** (STS) turns "I am allowed to become role X" into
temporary credentials: an access key starting with **ASIA** (long-term keys start with **AKIA**), a
secret, a **session token** and an **expiration**. Everything modern uses this: Identity Center
logins, EC2 instance profiles, ECS task roles, EKS Pod Identity, GitLab CI via OIDC
(`AssumeRoleWithWebIdentity`), and cross-account access. Sessions last 1 hour by default and up to
the role's `MaxSessionDuration` (maximum 12 hours). **Role chaining** (using role credentials to
assume another role) is capped at 1 hour.

The CLI finds credentials in a fixed order, and the first match wins: command-line options,
**environment variables** (`AWS_ACCESS_KEY_ID`, `AWS_SESSION_TOKEN`, `AWS_PROFILE`), web identity
token, SSO, the shared credentials file, the config file, then container credentials and finally
the EC2 instance profile through IMDS. A stale `AWS_ACCESS_KEY_ID` exported in `~/.bashrc` silently
beats the instance profile, which is a classic "works for root, not for the service" puzzle.

A cross-account profile in `~/.aws/config`:

```
[profile prod-readonly]
role_arn = arn:aws:iam::210987654321:role/ReadOnlyFromLab
source_profile = lab-admin
role_session_name = learner-readonly
duration_seconds = 3600
region = ap-south-1
```

**Key terms**

| Term | Meaning |
|---|---|
| STS | Service that issues temporary credentials |
| AssumeRole / AssumeRoleWithWebIdentity | Get role credentials using AWS credentials / an OIDC token |
| Session name | Free text you choose; appears in the ARN and in CloudTrail (put a person or job ID in it) |
| ExternalId | Shared secret condition for third parties assuming your role (confused-deputy protection) |
| Role chaining | Assuming a role from a role session; maximum 1 hour |
| Credential provider chain | The order in which SDKs and the CLI look for credentials |

**See it on a real system**

```bash
aws sts assume-role --role-arn arn:aws:iam::210987654321:role/ReadOnlyFromLab \
  --role-session-name learner-test --query 'Credentials.[AccessKeyId,Expiration]' --output text
aws sts get-caller-identity --profile prod-readonly
env | grep '^AWS_' | sed 's/=.*/=.../'
```

```
ASIA4EXAMPLETEMPKEY12	2026-10-03T10:41:22+00:00
{
    "UserId": "AROA5EXAMPLEROLEID987:learner-readonly",
    "Account": "210987654321",
    "Arn": "arn:aws:sts::210987654321:assumed-role/ReadOnlyFromLab/learner-readonly"
}
AWS_PROFILE=...
```

→ The temporary key starts with ASIA and expires in an hour. The profile transparently performs the
same AssumeRole and caches the result in `~/.aws/cli/cache/`. Only `AWS_PROFILE` is set in the
environment, so no stale keys will override it.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** In the sandbox (a second account is optional; a same-account role works for
learning), create role `ReadOnlyFromLab` with `ReadOnlyAccess` and this trust policy, which
requires MFA in the calling session:

```
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "AWS": "arn:aws:iam::123456789012:root" },
    "Action": "sts:AssumeRole",
    "Condition": { "Bool": { "aws:MultiFactorAuthPresent": "true" } }
  }]
}
```

→ `arn:aws:iam::123456789012:root` means "this account may delegate to its principals", not "the
root user". Each principal still needs `sts:AssumeRole` in its own identity policy.

**Step 2 — Break it.** Change the trusted account ID to a wrong one (for example 111111111111) and
assume the role:

```
An error occurred (AccessDenied) when calling the AssumeRole operation: User: arn:aws:sts::123456789012:assumed-role/AWSReservedSSO_AdministratorAccess_0a1b2c3d4e5f6a7b/learner is not authorized to perform: sts:AssumeRole on resource: arn:aws:iam::210987654321:role/ReadOnlyFromLab
```

Then restore the trust policy, export a fake `AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE` with any
`AWS_SECRET_ACCESS_KEY`, select the profile through the environment with
`export AWS_PROFILE=prod-readonly`, and run `aws sts get-caller-identity`:

```
An error occurred (InvalidClientTokenId) when calling the GetCallerIdentity operation: The security token included in the request is invalid.
```

The exported keys won: the CLI never read the profile and sent the fake key straight to STS. An
explicit `--profile` flag on the command line would have ignored the key variables, while
`AWS_PROFILE` does not, which is why the stale-variable trap bites scripts and services that rely
on `AWS_PROFILE`.

**Step 3 — Fix it.** Restore the trust principal; `unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY
AWS_SESSION_TOKEN`; run `aws configure list` and confirm the credential source is what you expect.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Trust policy does not name the caller | `not authorized to perform: sts:AssumeRole on resource` | `aws iam get-role --role-name ROLE_NAME --query Role.AssumeRolePolicyDocument` | this topic |
| Session expired | `ExpiredToken: The security token included in the request is expired` | `aws sso login` or re-assume | section 0 |
| Stale env vars override profile | Wrong account in `get-caller-identity` | `env`, `aws configure list` | this topic |
| Role chaining over 1 hour | `The requested DurationSeconds exceeds the 1 hour session limit for roles assumed by role chaining.` | lower `duration_seconds` | this topic |
| Clock skew | `SignatureDoesNotMatch` / `Signature expired` | `timedatectl` | [Time & NTP](12-time-ntp.md) |

**Why it matters for troubleshooting.** When `get-caller-identity` shows an unexpected ARN, every
later error is misleading. Fixing the credential source first is the AWS equivalent of checking
`id` before debugging file permissions.

**Next step:** what to do about the long-lived keys that still exist.

### Keys, MFA and Identity Center

**Level:** [L1 · Junior] · about 40 minutes · lab cost: free

**Concept.** Long-lived access keys (AKIA...) are the most common way AWS accounts are compromised:
they get committed to Git, baked into images, pasted into CI variables and left in laptops' backups.
The modern rule set is short:

- **Humans** sign in through **IAM Identity Center** with MFA and get short-lived role credentials.
- **Machines on AWS** use roles (instance profiles, task roles, Pod Identity).
- **CI/CD** uses OIDC federation: GitLab CI presents an ID token and assumes a role (section 10).
- **Machines on-prem** use SSM hybrid activation, or **IAM Roles Anywhere** with X.509 certificates
  from a CA you trust (your private CA can issue them).
- **Root** has MFA, no access keys, and is used only for the handful of root-only tasks.

When a key must exist (a legacy app or vendor tool), rotate it without downtime: create a second
key, deploy it, watch the old key's **last used** time stop moving, **deactivate** the old key,
wait, then delete it.

**Key terms**

| Term | Meaning |
|---|---|
| AKIA / ASIA | Prefixes of long-term / temporary access key IDs |
| Access key last used | Timestamp, service and region of the key's last successful call |
| Credential report | Account-wide CSV of users, password age, MFA, key age and last use |
| Permission set | Identity Center's reusable bundle of policies, deployed as a role in each assigned account |
| IAM Roles Anywhere | Exchanges an X.509 certificate for role credentials, for workloads outside AWS |

**See it on a real system**

```bash
aws iam list-access-keys --user-name ci-legacy --output table
aws iam get-access-key-last-used --access-key-id AKIAIOSFODNN7EXAMPLE
aws iam generate-credential-report >/dev/null; sleep 5
aws iam get-credential-report --query Content --output text | base64 -d \
  | cut -d, -f1,4,8,9,11 | column -ts,
```

```
-----------------------------------------------------------------------------------
|                                  ListAccessKeys                                 |
+---------------------------------------------------------------------------------+
||                               AccessKeyMetadata                               ||
|+------------------------+-----------------------------+----------+-------------+|
||      AccessKeyId       |          CreateDate         |  Status  |   UserName  ||
|+------------------------+-----------------------------+----------+-------------+|
||  AKIAIOSFODNN7EXAMPLE  |  2024-03-11T07:22:41+00:00  |  Active  |  ci-legacy  ||
|+------------------------+-----------------------------+----------+-------------+|
{
    "UserName": "ci-legacy",
    "AccessKeyLastUsed": {
        "LastUsedDate": "2026-10-03T06:15:00+00:00",
        "ServiceName": "s3",
        "Region": "ap-south-1"
    }
}
user                   password_enabled  mfa_active  access_key_1_active  access_key_1_last_used_date
<root_account>         not_supported     true        false                N/A
learner-breakglass     true              true        false                N/A
ci-legacy              false             false       true                 2026-10-03T06:15:00+00:00
```

→ `ci-legacy` has a key that is two and a half years old and used daily by something in S3. That is
the key to replace with an OIDC role first. The `<root_account>` row is literal output from AWS.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create user `ci-legacy` with a key, configure it in a throwaway profile, and
run a small loop that lists the lab bucket every minute (your "app").

**Step 2 — Break it.** Rotate badly: deactivate the only key while the "app" still uses it.

```
An error occurred (InvalidAccessKeyId) when calling the ListObjectsV2 operation: The AWS Access Key Id you provided does not exist in our records.
```

**Step 3 — Fix it.** Reactivate it (this is why you deactivate before deleting). Then rotate
properly: `aws iam create-access-key`, update the profile, confirm the new key's last-used time
moves, then deactivate the old one.

> ⚠️ `aws iam delete-access-key` is irreversible, and any system still using the key breaks with no
> way back. Safer first: `aws iam update-access-key --access-key-id KEY_ID --status Inactive
> --user-name USER`, watch for errors and the last-used date for a week, then delete.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Key leaked in a Git repo | AWS email "your account may be compromised", quarantine policy attached to the user | `aws iam list-attached-user-policies --user-name USER` | section 13 (incident response) |
| Key deactivated too early | `InvalidAccessKeyId` (S3) or `InvalidClientTokenId` (most other APIs) in the app | `aws iam list-access-keys --user-name USER` | this topic |
| Wrong secret or clock skew | `SignatureDoesNotMatch` | `timedatectl` | [Time & NTP](12-time-ntp.md) |
| No MFA on privileged humans | Audit finding, phishing risk | credential report | [Security & DevSecOps](37-learn-security-devsecops.md) |

**Why it matters for troubleshooting.** Every static key is a future incident. Knowing how to find
who uses a key (last used, CloudTrail by `AccessKeyId`) is also how you investigate a leak.

**Next step:** a repeatable method for the error you will see most: AccessDenied.

### Debugging AccessDenied

**Level:** [L2 · Mid] · about 60 minutes · lab cost: free

**Concept.** Treat AccessDenied like any other incident: collect evidence, then test one layer at a
time. The error message itself usually tells you most of the answer, because AWS now includes the
**policy type** that caused the denial for many services.

The method, in order:

1. **Who am I?** `aws sts get-caller-identity`. Wrong account or role ends the investigation early.
2. **Read the whole message.** It names the principal, the action, the resource and, often, the
   policy type: `because no identity-based policy allows`, `with an explicit deny in a service
   control policy`, `... in a resource-based policy`, `... in a permissions boundary`,
   `... in a VPC endpoint policy`, `... in a session policy`.
3. **Right region and resource?** A bucket or key in another account or region changes everything.
4. **Find the event in CloudTrail.** Management events appear in Event History within about
   5–15 minutes. Data events (S3 object reads and writes, Lambda invokes) are **not** in Event
   History; you need a trail with data events enabled, or S3 server access logs.
5. **Simulate.** `simulate-principal-policy` for identity policies; then check the resource
   policy, KMS key policy, SCPs, boundary and endpoint policy that the error hinted at.
6. **Decode EC2's message.** EC2 and a few others return an encoded authorization message; decode it
   with `aws sts decode-authorization-message` (needs `sts:DecodeAuthorizationMessage`).

**Key terms**

| Term | Meaning |
|---|---|
| Event History | Free, 90-day, per-region view of management events in CloudTrail |
| Management vs data event | Control-plane calls (CreateBucket) vs high-volume data calls (GetObject) |
| `errorCode` | CloudTrail field such as `AccessDenied`, `UnauthorizedOperation`, `Client.UnauthorizedOperation` |
| Encoded authorization message | Opaque blob in EC2 errors with the full evaluation context |
| IAM Access Analyzer | Finds external access, unused access, and generates policies from CloudTrail activity |

**See it on a real system**

```bash
# Last hour of denied management calls by one role session, in this region
aws cloudtrail lookup-events --start-time "$(date -u -d '1 hour ago' +%FT%TZ)" \
  --lookup-attributes AttributeKey=Username,AttributeValue=i-0a1b2c3d4e5f60011 --output json \
  | jq -r '.Events[].CloudTrailEvent | fromjson | select(.errorCode != null)
           | [.eventTime, .eventSource, .eventName, .errorCode] | @tsv'

# EC2 error with an encoded message
aws sts decode-authorization-message --encoded-message "$MSG" --query DecodedMessage --output text \
  | jq '{allowed, explicitDeny, action: .context.action, resource: .context.resource}'
```

```
2026-10-03T08:52:10Z	ec2.amazonaws.com	DescribeInstances	Client.UnauthorizedOperation
2026-10-03T08:49:31Z	ssm.amazonaws.com	GetParameter	AccessDenied
{
  "allowed": false,
  "explicitDeny": true,
  "action": "ec2:RunInstances",
  "resource": "arn:aws:ec2:us-west-2:123456789012:instance/*"
}
```

→ CloudTrail confirms the denied calls and their exact API names (which are the IAM actions you need,
`ec2:DescribeInstances`, `ssm:GetParameter`). The decoded EC2 message adds the missing fact:
the denial is **explicit**, so adding an Allow will never fix it; find the Deny (here, a region
restriction, see the next topic).

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Three deliberate denials for `app-ec2-role`: (a) call `ssm:GetParameter` on
a parameter it has no permission for; (b) attach a permissions boundary that allows only `s3:*`
and then call `ec2:DescribeInstances`; (c) encrypt an object in the lab bucket with a
customer-managed KMS key whose key policy does not mention the role (section 5).

**Step 2 — Break it.** Trigger each one and record the error text. For (b):

```
An error occurred (UnauthorizedOperation) when calling the DescribeInstances operation: You are not authorized to perform this operation. User: arn:aws:sts::123456789012:assumed-role/app-ec2-role/i-0a1b2c3d4e5f60011 is not authorized to perform: ec2:DescribeInstances because no permissions boundary allows the ec2:DescribeInstances action
```

**Step 3 — Fix it.** For each, name the policy type from the message, find it, and fix the
narrowest thing: add the parameter ARN to the identity policy; widen the boundary deliberately (or
accept that the boundary is doing its job); add the role to the key policy or grant `kms:Decrypt`.
Time yourself; the Mid-level exit test in section 15 expects under 10 minutes per denial.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Missing identity Allow | `because no identity-based policy allows` | `aws iam simulate-principal-policy` | this topic |
| SCP explicit deny | `with an explicit deny in a service control policy` | ask the org admin; `aws organizations list-policies-for-target` | next topic |
| KMS key policy | AccessDenied mentioning `kms:Decrypt` or `kms:GenerateDataKey` | `aws kms get-key-policy --key-id KEY_ID --policy-name default` | section 5 |
| VPC endpoint policy | `... because no VPC endpoint policy allows` | `aws ec2 describe-vpc-endpoints` | section 3 |
| S3 GetObject denials not in CloudTrail | Event History shows nothing | enable data events or S3 access logs | section 9 |

**Why it matters for troubleshooting.** Guessing at IAM (attaching broader policies until the error
goes away) is how accounts end up with admin everywhere. The evidence-first method fixes the actual
layer and leaves least privilege intact.

**Next step:** the guardrails that sit above every account: Organizations and SCPs.

### Organizations and SCPs

**Level:** [L3 · Senior] · about 50 minutes · lab cost: free

**Concept.** Real companies run **many accounts**: one per environment and per team, plus security,
logging and networking accounts. Accounts are the strongest isolation boundary AWS has (separate
IAM, quotas, blast radius, bills). **AWS Organizations** groups them into **organizational units**
(OUs) and applies **service control policies** (SCPs), which cap what any principal in the member
accounts can do, including the member account's root user. **Resource control policies** (RCPs,
since late 2024) cap what can be done **to** resources such as S3 buckets and KMS keys, whoever asks.
The management account is not restricted by SCPs, so keep workloads out of it.

```
 Root (management account 123456789012: billing only, no workloads)
 ├── OU Security      ── log-archive, audit             SCP: deny disabling CloudTrail/Config
 ├── OU Infrastructure── network (TGW, DNS), shared (ECR, CI runners)
 ├── OU Workloads
 │    ├── OU Prod     ── app-prod 210987654321           SCP: region allow-list, deny leaving org
 │    └── OU NonProd  ── app-dev, app-stage
 └── OU Sandbox       ── learner-sandbox                  SCP: region allow-list, deny expensive types
```

A region allow-list SCP (global services must be exempted or they break):

```
{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "DenyOutsideApprovedRegions",
    "Effect": "Deny",
    "NotAction": [ "iam:*", "organizations:*", "route53:*", "cloudfront:*", "sts:*",
                   "support:*", "budgets:*", "ce:*", "health:*", "account:*" ],
    "Resource": "*",
    "Condition": { "StringNotEquals": { "aws:RequestedRegion": [ "ap-south-1", "us-east-1" ] } }
  }]
}
```

**Key terms**

| Term | Meaning |
|---|---|
| Management account | Pays the bill, owns the organization; not affected by SCPs |
| OU | Folder of accounts that policies attach to |
| SCP | Maximum permissions for principals in member accounts |
| RCP | Maximum permissions on resources in member accounts |
| Delegated administrator | A member account allowed to manage a service (GuardDuty, Security Hub) for the org |
| Centralized root access | Org feature that removes root credentials from member accounts |

**See it on a real system**

```bash
aws organizations describe-organization --query 'Organization.[Id,FeatureSet,MasterAccountId]' --output text
aws organizations list-accounts --query 'Accounts[].[Id,Name,State]' --output table
aws organizations list-policies-for-target --target-id 210987654321 \
  --filter SERVICE_CONTROL_POLICY --query 'Policies[].Name' --output text
```

```
o-a1b2c3d4e5	ALL	123456789012
-------------------------------------------------
|                  ListAccounts                 |
+----------------+-------------------+----------+
|  123456789012  |  management       |  ACTIVE  |
|  210987654321  |  app-prod         |  ACTIVE  |
|  345678901234  |  learner-sandbox  |  ACTIVE  |
+----------------+-------------------+----------+
FullAWSAccess	DenyOutsideApprovedRegions	DenyLeaveOrganization
```

→ `FullAWSAccess` is the default SCP that allows everything; the two custom SCPs then subtract.
An SCP list is the first thing to check when a member account is denied something its admin
"definitely allowed". `list-policies-for-target` shows only the policies attached **directly** to
that target, and SCPs are inherited, so repeat it for every parent OU and the root
(`aws organizations list-parents --child-id ACCOUNT_ID` walks up the tree). The account's
lifecycle field is `State`; AWS scheduled the older `Status` field for removal from the API on
9 September 2026, so scripts that still query `Status` can get empty (`None`) values.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Organizations is free. In a sandbox management account, create an OU
`Sandbox`, move a second sandbox account into it (or create one), and attach the region SCP above.

**Step 2 — Break it.** From the member account, launch an instance in us-west-2. Decode the error:
`explicitDeny: true`. Then remove `sts:*` from the `NotAction` list and try
`aws sts get-caller-identity --region us-west-2`; note which calls still work (`GetCallerIdentity`
cannot be denied) and which global-service calls start failing.

**Step 3 — Fix it.** Restore the exemptions. Write down the rule: **test every SCP on a sandbox OU
first**, and never attach a broad Deny to the organization root.

> ⚠️ An SCP attached to the root or a production OU applies instantly to every principal in those
> accounts, including their admins and automation. A wrong `Deny` can stop deployments company-wide.
> Safer first: attach to a sandbox OU, run your test suite of calls, then promote it.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| SCP denies a needed action | Admins denied, message says "service control policy" | `aws organizations list-policies-for-target --target-id ACCOUNT_ID --filter SERVICE_CONTROL_POLICY` | this topic |
| Region SCP without global exemptions | IAM, Support or billing calls fail | read the SCP `NotAction` | this topic |
| Workloads in the management account | SCP guardrails silently not applied | `aws organizations describe-organization` | section 13 |
| Account hit a quota | `LimitExceeded`, `VcpuLimitExceeded` | `aws service-quotas list-service-quotas --service-code ec2` | section 9 |

**Why it matters for troubleshooting.** At senior level, the answer to "why is this denied" is
often one level above the account. Knowing the org structure, and having read-only access to it, is
part of being able to debug production.

**Next step:** the network those identities operate in: the VPC.

---

## 3. VPC deep dive

> 📚 **Study path:** 1) KodeKloud: *AWS Networking Fundamentals* — VPC, subnets, gateways, routing and security groups first, Transit Gateway last ([link](https://kodekloud.com/courses/aws-networking-fundamentals)) · 2) Video: *AWS Networking Basics: AWS VPC & Subnets for Beginners* (KodeKloud, 18 min) ([link](https://www.youtube.com/watch?v=QM63dyA_4Pc)) · 3) Note: refresh CIDR and routing in [Learn: Networking](28-learn-networking.md), then [AWS reference](16-aws-cloud.md) section 5 (the timeout checklist) · 4) Practice: NAT gateway and Transit Gateway labs in the [AWS Playground](https://kodekloud.com/cloud-playgrounds/aws), everything else in your sandbox, then the drill at the end of this section under a 20-minute timer

Tags: [L1 · Junior] for subnets, routes, SGs and NACLs, [L2 · Mid] for endpoints, Flow Logs, Reachability Analyzer and the drill, [L3 · Senior] for CIDR planning at scale, peering and Transit Gateway.

A VPC is your data-center network rebuilt as API objects: the VLANs are subnets, the router is a
route table, the edge firewall is split into NACLs and security groups, and the uplink is an
internet gateway. Most "it times out" tickets on AWS are a missing route, a missing rule or a
missing return path. This section teaches each layer, then the two tools that show you the layer
instead of making you guess, then a timed drill.

The lab VPC used throughout the module:

```
 VPC lab 10.20.0.0/16 (ap-south-1)                    Internet
 ┌───────────────────────────────────────────────────────┐  ▲
 │  AZ ap-south-1a                 AZ ap-south-1b          │  │
 │  ┌──────────────────────┐       ┌──────────────────────┐│  │
 │  │ public-a 10.20.0.0/20 │       │ public-b 10.20.32.0/20││  │
 │  │  ALB node, NAT GW     │       │  ALB node            ││  │
 │  └──────────┬───────────┘       └──────────┬───────────┘│  │
 │  ┌──────────▼───────────┐       ┌──────────▼───────────┐│ IGW
 │  │ private-a 10.20.16.0/20│      │ private-b 10.20.48.0/20│
 │  │  web EC2 10.20.17.25  │       │  web EC2, ECS tasks   ││
 │  └──────────────────────┘       └──────────────────────┘│
 │  data-a 10.20.64.0/22            data-b 10.20.68.0/22     │
 │  (RDS, no internet route)        (RDS standby)            │
 │  10.20.128.0/17 reserved for EKS pods and growth          │
 └───────────────────────────────────────────────────────┘
 public route table : 10.20.0.0/16 → local, 0.0.0.0/0 → igw
 private route table: 10.20.0.0/16 → local, 0.0.0.0/0 → nat (same AZ)
 data route table   : 10.20.0.0/16 → local only
```

### CIDR planning and subnets

**Level:** [L1 · Junior] → [L3 · Senior] · about 45 minutes · lab cost: free

**Concept.** A VPC gets one primary IPv4 CIDR between /16 and /28 (you can add secondary CIDRs
later). You carve it into **subnets**, and each subnet lives in exactly **one AZ**. AWS reserves
**five addresses** in every subnet: the network address, base + 1 (the VPC router), base + 2 (the
Amazon DNS resolver), base + 3 (reserved for future use) and the last address. A /24 therefore gives
251 usable addresses, not 254.

The fresher question is "how big is a subnet?". The senior question is "**what will this VPC ever
need to talk to?**", because two networks with overlapping ranges can never be routed to each
other cleanly. Before you pick a range, list every network that might be connected later:

| Network that may meet the VPC | Typical range | Why it matters |
|---|---|---|
| Your on-prem LAN | 192.168.10.0/24 | Site-to-Site VPN and hybrid DNS (section 11) need distinct routes |
| Docker default bridge and address pools | 172.17.0.0/16, then 172.18–172.31 as /16s, then 192.168.0.0/16 in /20 chunks | A Docker host that also needs to reach the VPC routes those ranges to its own bridges |
| Docker Swarm overlays (Dokploy) | 10.0.0.0/8 pool, /24 per network; ingress 10.0.0.0/24 | A VPC in 10.0.0.0/16 collides with `dokploy-network` containers over a VPN |
| Kubernetes (kubeadm homelab) | Services 10.96.0.0/12; pods 10.244.0.0/16 (Flannel) or 192.168.0.0/16 (Calico default) | Calico's default pod range swallows your on-prem LAN |
| Other VPCs, other accounts, partners | often 10.0.0.0/16 | Peering and Transit Gateway refuse or misroute overlaps |

The usual answer is a written IP plan: one /16 per VPC from a block nobody else uses (here
10.20.0.0/16 and 10.30.0.0/16), subnets of /20 for application tiers, small /22s for databases,
and a large range reserved for EKS pods. At company scale, **VPC IPAM** tracks the allocations.

**Key terms**

| Term | Meaning |
|---|---|
| CIDR block | The VPC's address range, /16 (65,536 addresses) to /28 (16) |
| Subnet | A slice of the VPC CIDR in one AZ; the unit you attach route tables and NACLs to |
| Public subnet | A subnet whose route table sends 0.0.0.0/0 to an internet gateway |
| Private subnet | A subnet whose default route goes to a NAT gateway, or nowhere |
| Auto-assign public IPv4 | Subnet setting (`MapPublicIpOnLaunch`) that gives new instances a public IP |
| VPC IPAM | AWS service that plans, allocates and audits CIDRs across accounts |

**See it on a real system**

```bash
aws ec2 describe-vpcs --query 'Vpcs[].[VpcId,CidrBlock,IsDefault]' --output table
aws ec2 describe-subnets --filters Name=vpc-id,Values=VPC_ID \
  --query 'Subnets[].[Tags[?Key==`Name`]|[0].Value,CidrBlock,AvailabilityZone,AvailableIpAddressCount,MapPublicIpOnLaunch]' \
  --output table
# Plan on paper, locally: split the /16 into /20s
python3 -c "import ipaddress as i; print([str(n) for n in i.ip_network('10.20.0.0/16').subnets(new_prefix=20)][:6])"
```

```
-------------------------------------------------------
|                     DescribeVpcs                    |
+-------------------------+-----------------+---------+
|  vpc-0b1c2d3e4f5a60001  |  172.31.0.0/16  |  True   |
|  vpc-0a1b2c3d4e5f60020  |  10.20.0.0/16   |  False  |
+-------------------------+-----------------+---------+
--------------------------------------------------------------------
|                         DescribeSubnets                          |
+-------------+-----------------+---------------+--------+---------+
|  public-a   |  10.20.0.0/20   |  ap-south-1a  |  4089  |  True   |
|  private-a  |  10.20.16.0/20  |  ap-south-1a  |  4087  |  False  |
|  public-b   |  10.20.32.0/20  |  ap-south-1b  |  4090  |  True   |
|  private-b  |  10.20.48.0/20  |  ap-south-1b  |  4088  |  False  |
|  data-a     |  10.20.64.0/22  |  ap-south-1a  |  1018  |  False  |
|  data-b     |  10.20.68.0/22  |  ap-south-1b  |  1018  |  False  |
+-------------+-----------------+---------------+--------+---------+
['10.20.0.0/20', '10.20.16.0/20', '10.20.32.0/20', '10.20.48.0/20', '10.20.64.0/20', '10.20.80.0/20']
```

→ The **default VPC** (172.31.0.0/16, `IsDefault True`) exists in every region; it is fine for a
first instance and wrong for anything you will connect to on-prem. A /20 holds 4,096 addresses;
4,091 are usable and the rest of the gap is ENIs already in use (ALB nodes, NAT gateway,
instances). Watch `AvailableIpAddressCount` on subnets used by EKS, where every pod takes one.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** In the VPC console use **Create VPC → VPC and more**: name `lab`, CIDR
10.20.0.0/16, 2 AZs, 2 public and 2 private subnets, **NAT gateways: None** for now, **VPC
endpoints: None**. Rename the subnets to match the table above and tag everything `Project=lab`.

**Step 2 — Break it.** Try to add a subnet that overlaps an existing one, and one that is too
small:

```bash
aws ec2 create-subnet --vpc-id VPC_ID --cidr-block 10.20.16.0/24 --availability-zone ap-south-1a
aws ec2 create-subnet --vpc-id VPC_ID --cidr-block 10.20.200.0/29 --availability-zone ap-south-1a
```

```
An error occurred (InvalidSubnet.Conflict) when calling the CreateSubnet operation: The CIDR '10.20.16.0/24' conflicts with another subnet
An error occurred (InvalidSubnet.Range) when calling the CreateSubnet operation: The CIDR '10.20.200.0/29' is invalid.
```

**Step 3 — Fix it.** Pick a free, aligned range (10.20.64.0/22 for `data-a`) and record it in your
IP plan. Then write the plan for your real estate: on-prem LAN, Dokploy's Swarm pools, the
homelab pod and service CIDRs, and two future VPCs, with no overlaps.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Subnet out of addresses | `InsufficientFreeAddressesInSubnet`, EKS pods stuck `ContainerCreating` | `aws ec2 describe-subnets --query 'Subnets[].AvailableIpAddressCount'` | section 8 |
| VPC overlaps on-prem or another VPC | Peering refused, VPN routes ambiguous, traffic goes to the wrong side | compare CIDRs in your IP plan | "Peering and Transit Gateway" |
| VPC overlaps Docker or Swarm pools | Containers on the hybrid host cannot reach VPC hosts | `ip route` on the Docker host | [Learn: Docker](30-learn-docker.md) |
| Instance launched without a public IP | Cannot reach it from the internet even with a correct SG | `aws ec2 describe-instances --query 'Reservations[].Instances[].PublicIpAddress'` | the drill below |

**Why it matters for troubleshooting.** An address plan is the one network decision you cannot fix
later without rebuilding. Half of hybrid connectivity incidents are overlapping ranges, and they
look like random timeouts until someone draws the CIDRs side by side.

**Next step:** how packets leave a subnet: route tables, the internet gateway and NAT.

### Route tables, IGW and NAT

**Level:** [L1 · Junior] · about 45 minutes · lab cost: dollars (NAT gateway; delete it the same day)

**Concept.** Every subnet is associated with exactly **one route table**; a subnet you never
associated uses the VPC's **main** route table. Each table starts with a `local` route for the VPC
CIDR that you cannot remove, and AWS picks the **longest prefix match**, just like `ip route` on
Ubuntu. Three targets matter for internet access:

- An **internet gateway** (IGW) attached to the VPC. A subnet is *public* only because its route
  table says `0.0.0.0/0 → igw-...`. The IGW does one-to-one NAT between the instance's private IP
  and its public IP, so the instance never sees its public address on `ens5`.
- A **NAT gateway** lives in a public subnet and lets private instances start outbound connections
  (apt, ECR pulls, SSM) without being reachable from outside. It is zonal: build one per AZ and
  point each private route table at the NAT in its own AZ, or one AZ's failure takes out egress for
  all of them and you pay cross-AZ data charges on top.
- A **blackhole** route is a route whose target was deleted. Traffic matching it is silently
  dropped.

```
 private-a instance 10.20.17.25 ──▶ route table "private-a"
     dst 10.20.0.0/16  → local            (stays in the VPC)
     dst 0.0.0.0/0     → nat-0a1b...      ──▶ NAT GW in public-a (10.20.3.180, EIP 203.0.113.40)
                                                 └──▶ route table "public" 0.0.0.0/0 → igw ──▶ Internet
 Reply comes back to the NAT GW's EIP, NAT translates back to 10.20.17.25.
 Nothing on the internet can start a connection to 10.20.17.25.
```

**Key terms**

| Term | Meaning |
|---|---|
| Main route table | Used by every subnet without an explicit association |
| Local route | The VPC CIDR; always present, always wins for in-VPC destinations |
| Internet gateway | Horizontally scaled VPC attachment for internet traffic; no bandwidth limit, no cost by itself |
| NAT gateway | Managed source NAT for private subnets; zonal; billed per hour and per GB processed |
| Elastic IP | Static public IPv4; a NAT gateway needs one |
| Blackhole | Route state when its target (NAT, ENI, peering) no longer exists |

**See it on a real system**

```bash
aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=SUBNET_ID \
  --query 'RouteTables[].Routes[].[DestinationCidrBlock,GatewayId,NatGatewayId,State]' --output table
# Empty output? The subnet uses the main route table implicitly:
aws ec2 describe-route-tables --filters Name=vpc-id,Values=VPC_ID Name=association.main,Values=true \
  --query 'RouteTables[].RouteTableId' --output text
aws ec2 describe-nat-gateways --filter Name=vpc-id,Values=VPC_ID \
  --query 'NatGateways[].[NatGatewayId,SubnetId,State,NatGatewayAddresses[0].PublicIp]' --output table
```

```
-----------------------------------------------------------------
|                      DescribeRouteTables                      |
+----------------+---------+-------------------------+----------+
|  10.20.0.0/16  |  local  |  None                   |  active  |
|  0.0.0.0/0     |  None   |  nat-0a1b2c3d4e5f60012  |  active  |
+----------------+---------+-------------------------+----------+
rtb-0f1e2d3c4b5a60003
---------------------------------------------------------------------------------------
|                                 DescribeNatGateways                                 |
+-------------------------+----------------------------+-------------+----------------+
|  nat-0a1b2c3d4e5f60012  |  subnet-0a1b2c3d4e5f60101  |  available  |  203.0.113.40  |
+-------------------------+----------------------------+-------------+----------------+
```

→ This private subnet sends everything that is not VPC-local to the NAT gateway, which sits in a
public subnet and owns the EIP 203.0.113.40. That EIP is the address partners must allow-list
when your instances call them, the same way your on-prem firewall's public IP is.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Launch a t3.micro Ubuntu 24.04 instance in `private-a` with the
`app-ec2-role` instance profile from section 2 and no public IP. With no NAT gateway yet, connect
through the EC2 serial console or wait for section 4's SSM setup. Run `sudo apt-get update` and
watch it hang on `Connecting to ap-south-1.ec2.archive.ubuntu.com`.

**Step 2 — Break it, then fix it.** Create a NAT gateway in `public-a` with a new EIP and add
`0.0.0.0/0 → nat-...` to the private route table. `apt-get update` now works. Then delete the NAT
gateway and look at the route table again:

```
|  0.0.0.0/0     |  None   |  nat-0a1b2c3d4e5f60012  |  blackhole  |
```

**Step 3 — Fix it properly.** Decide what the private subnet really needs. Package mirrors and
ECR pulls need egress (a NAT gateway, or VPC endpoints for AWS services, next topics). A database
subnet needs none. Remove the blackhole route so nobody mistakes it for a working one, and release
the EIP.

> ⚠️ A NAT gateway costs about USD 33 a month before data, and an unattached EIP still costs about
> USD 3.65 a month. Safer habit: create NAT only for the lab hour, delete it, then run the teardown
> hunt from section 0 to confirm the EIP is released.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Subnet left on the main route table | "Public" subnet has no internet, or a private one is unexpectedly public | `aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=SUBNET_ID` | this topic |
| NAT gateway deleted or failed | `apt`, `docker pull`, SSM all hang in private subnets; route shows `blackhole` | `aws ec2 describe-nat-gateways` | this topic |
| One NAT for all AZs | Egress dies with one AZ; cross-AZ charges on the bill | compare NAT subnet AZ with each route table | section 12 |
| NAT gateway port exhaustion | `ErrorPortAllocation` metric above zero, intermittent outbound failures to one destination | CloudWatch `ErrorPortAllocation` for the NAT | [Network speed](24-playbook-network-speed.md) |
| Instance in public subnet without public IP | Outbound and inbound both fail | `aws ec2 describe-instances --query '...PublicIpAddress'` | the drill below |

**Why it matters for troubleshooting.** A timeout with a correct security group is very often a
routing problem: no route out, no route back, or a route into a blackhole. Reading one route table
takes ten seconds and rules out a whole layer.

**Next step:** the two firewalls that sit on that path.

### Security groups vs NACLs

**Level:** [L1 · Junior] → [L2 · Mid] · about 50 minutes · lab cost: cents

**Concept.** AWS gives you two firewalls, and they behave differently.

| | Security group (SG) | Network ACL (NACL) |
|---|---|---|
| Attached to | An ENI (instance, ALB, RDS, endpoint) | A subnet |
| State | **Stateful**: replies are allowed automatically | **Stateless**: replies must be allowed explicitly |
| Rules | Allow only | Allow and Deny, numbered, lowest number first, first match wins |
| Sources | CIDRs, prefix lists and **other security groups** | CIDRs only |
| Default | New SG: no inbound, all outbound | Default NACL: allow all both ways; a new custom NACL denies all |
| Typical use | The real firewall for every workload | Coarse subnet guardrails, blocking a hostile range quickly |
| On-prem analogy | UFW on each host, following the host wherever it moves | ACL on the VLAN's router interface |

The stateless NACL is where on-prem engineers get caught. A client connects from port 51514 to
your instance's port 81. The reply goes **from** port 81 **to** port 51514, so the NACL's
**outbound** rules must allow the **ephemeral range** (1024–65535 to cover every OS) back to the
client. An SG remembers the connection and never needs that rule.

```
 client 198.51.100.10:51514 ──▶ IGW ──▶ NACL inbound (tcp 81 allowed?) ──▶ SG inbound (tcp 81 from where?)
                                                                              ──▶ UFW on the instance ──▶ Apache :81
 reply  :81 ──▶ SG (stateful, auto) ──▶ NACL outbound (tcp 1024-65535 to client allowed?) ──▶ IGW ──▶ client
```

Reference SGs instead of CIDRs wherever you can: "the web SG allows tcp 81 **from the ALB's SG**"
stays correct when the ALB's nodes change IP, and it documents intent.

**Key terms**

| Term | Meaning |
|---|---|
| Stateful | Return traffic for an allowed connection is allowed without a rule |
| Stateless | Every packet is checked against the rules in its own direction |
| Ephemeral ports | The client's random source port range; Linux uses 32768–60999 by default |
| SG reference | A rule source that is another SG, meaning "any ENI in that group" |
| Prefix list | A named, reusable set of CIDRs (your office ranges, AWS service ranges) |

**See it on a real system**

```bash
aws ec2 describe-security-group-rules --filters Name=group-id,Values=SG_ID \
  --query 'SecurityGroupRules[].[IsEgress,IpProtocol,FromPort,ToPort,CidrIpv4,ReferencedGroupInfo.GroupId]' \
  --output table
aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=SUBNET_ID \
  --query 'NetworkAcls[].Entries[].[RuleNumber,Egress,Protocol,PortRange.From,PortRange.To,CidrBlock,RuleAction]' \
  --output table
```

```
--------------------------------------------------------------------------
|                       DescribeSecurityGroupRules                       |
+---------+-------+-------+-------+-------------+------------------------+
|  False  |  tcp  |  81   |  81   |  None       |  sg-0a1b2c3d4e5f60081  |
|  False  |  tcp  |  444  |  444  |  None       |  sg-0a1b2c3d4e5f60081  |
|  True   |  -1   |  -1   |  -1   |  0.0.0.0/0  |  None                  |
+---------+-------+-------+-------+-------------+------------------------+
--------------------------------------------------------------------------
|                          DescribeNetworkAcls                           |
+---------+---------+------+--------+---------+----------------+---------+
|  100    |  False  |  6   |  81    |  81     |  10.20.0.0/16  |  allow  |
|  110    |  False  |  6   |  444   |  444    |  10.20.0.0/16  |  allow  |
|  120    |  False  |  6   |  1024  |  65535  |  0.0.0.0/0     |  allow  |
|  32767  |  False  |  -1  |  None  |  None   |  0.0.0.0/0     |  deny   |
|  100    |  True   |  6   |  1024  |  65535  |  0.0.0.0/0     |  allow  |
|  110    |  True   |  6   |  443   |  443    |  0.0.0.0/0     |  allow  |
|  32767  |  True   |  -1  |  None  |  None   |  0.0.0.0/0     |  deny   |
+---------+---------+------+--------+---------+----------------+---------+
```

→ The SG allows Apache's ports 81 and 444 only from the ALB's security group, which mirrors your
on-prem layout where only Traefik should talk to Apache. The NACL (protocol 6 is TCP) allows those
ports from inside the VPC, allows replies to inbound return traffic on 1024–65535 (rule 120, needed
because outbound HTTPS calls such as SSM, ECR or S3 get their replies on ephemeral ports), and allows
outbound HTTPS plus ephemeral replies. Rule 32767 (`*` in the console) is the implicit final deny.
Ubuntu's default EC2 package mirrors use plain HTTP on port 80, so `apt` through this NACL would also
need an outbound tcp 80 rule.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Launch a second t3.micro Ubuntu instance, `lab-apache`, in `public-a`
with auto-assign public IPv4 on. Install Apache and make it listen on 81 (edit
`/etc/apache2/ports.conf` to `Listen 81` and the default vhost to `*:81`, as on your on-prem
server), and add an SG rule for tcp 81 from your own public IP only.
`curl -sI http://PUBLIC_IP:81/` returns `200 OK`. This instance is also the target of the Flow
Logs topic and the drill.

**Step 2 — Break it.** Create a custom NACL for the public subnet with inbound rule 100 allowing
tcp 81 from 0.0.0.0/0 and **only** an outbound rule allowing tcp 81. Associate it. `curl` now
hangs and times out.

**Step 3 — Fix it.** Explain why from the diagram: the SYN gets in, the SYN-ACK leaves from port 81
towards your ephemeral port, and the NACL drops it. Replace outbound rule 100 with tcp 1024–65535
to 0.0.0.0/0, and add inbound 1024–65535 too if the instance must make outbound calls. Then put
the subnet back on its original NACL and delete the custom one.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Port missing from the SG | Connection **times out** (SGs drop, never reject) | `aws ec2 describe-security-group-rules` | the drill below |
| NACL without ephemeral return rule | Times out even though the SG is right; Flow Logs show inbound ACCEPT, outbound REJECT | `aws ec2 describe-network-acls` | "Flow Logs and Reachability Analyzer" |
| SG source is a CIDR that changed | Worked yesterday; office or NAT IP changed | compare with `curl -s https://checkip.amazonaws.com` from the client | this topic |
| UFW turned on inside the instance | AWS layers look perfect, still timeouts | `sudo ufw status verbose` via SSM | [Users & permissions](10-users-permissions-security.md) |
| Port closed on the instance | **Connection refused** (an RST), not a timeout | `sudo ss -ltnp` | [Ports inventory](22-playbook-ports-inventory.md) |

**Why it matters for troubleshooting.** "Timeout" means a firewall or route dropped the packet;
"refused" means the packet arrived and nothing listened. That one distinction tells you whether to
look at AWS (SG, NACL, routes) or at the OS (`ss`, Apache), exactly as on-prem.

**Next step:** reaching AWS services privately, without NAT or the internet.

### VPC endpoints

**Level:** [L2 · Mid] · about 40 minutes · lab cost: cents

**Concept.** Your private instances call AWS APIs (S3, ECR, SSM, CloudWatch Logs, STS) all the
time. Without help, those calls go out through the NAT gateway to public endpoints, which costs
NAT data processing and needs internet egress. **VPC endpoints** keep them inside AWS:

- **Gateway endpoints** exist only for **S3 and DynamoDB**. They add a route (to a prefix list,
  `pl-...`) to the route tables you choose. They are **free**. Every VPC with private subnets
  should have the S3 one.
- **Interface endpoints** (PrivateLink) put an ENI with a private IP into your subnets for almost
  any other service. With **private DNS** enabled, the normal name
  (`ssm.ap-south-1.amazonaws.com`) resolves to that private IP inside the VPC, so nothing in your
  code changes. They cost about USD 0.01 per hour per AZ plus USD 0.01 per GB, and their ENIs have
  a security group that must allow tcp 443 from your instances.
- Both kinds accept an **endpoint policy**, a resource policy that limits what can be done through
  that endpoint. A bucket policy can, in turn, demand that requests arrive through a given endpoint
  with the `aws:SourceVpce` condition.

Common sets: **SSM without NAT** needs `ssm`, `ssmmessages` and `ec2messages` (SSM Agent 3.3.40.0
and later prefer `ssmmessages` over `ec2messages`, but keep all three so older agents and on-prem
images still work). **ECR pulls
without NAT** need `ecr.api`, `ecr.dkr` and the **S3 gateway endpoint** (image layers are served
from S3), plus `logs` if tasks use the awslogs driver and `sts` for web identity.

**Key terms**

| Term | Meaning |
|---|---|
| Gateway endpoint | Route-table target for S3 or DynamoDB; free; same-region only |
| Interface endpoint | ENI-based private access to a service; billed per AZ-hour and per GB |
| Private DNS | Makes the public service name resolve to the endpoint's private IPs inside the VPC |
| Endpoint policy | Resource policy on the endpoint that caps the allowed actions and resources |
| PrivateLink | The technology behind interface endpoints; also used to publish your own service to other VPCs |

**See it on a real system**

```bash
aws ec2 describe-vpc-endpoints --filters Name=vpc-id,Values=VPC_ID \
  --query 'VpcEndpoints[].[VpcEndpointType,ServiceName,State,PrivateDnsEnabled]' --output table
# On a private instance: does the service name resolve to a VPC address?
getent hosts ssm.ap-south-1.amazonaws.com
getent hosts s3.ap-south-1.amazonaws.com
```

```
--------------------------------------------------------------------------------
|                             DescribeVpcEndpoints                             |
+-------------+----------------------------------------+-------------+---------+
|  Gateway    |  com.amazonaws.ap-south-1.s3           |  available  |  False  |
|  Interface  |  com.amazonaws.ap-south-1.ssm          |  available  |  True   |
|  Interface  |  com.amazonaws.ap-south-1.ssmmessages  |  available  |  True   |
|  Interface  |  com.amazonaws.ap-south-1.ec2messages  |  available  |  True   |
+-------------+----------------------------------------+-------------+---------+
10.20.18.77     ssm.ap-south-1.amazonaws.com
198.51.100.180  s3.ap-south-1.amazonaws.com
```

→ The SSM name resolves to a private 10.20.x address: the interface endpoint and its private DNS
work. The S3 name still resolves to a public address, which is **correct** for a gateway endpoint:
the traffic is steered by the route table's prefix-list route, not by DNS.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Remove the NAT route from `private-a`. Create the three SSM interface
endpoints in `private-a` and `private-b` with private DNS on, and an SG `vpce-sg` allowing tcp 443
from 10.20.0.0/16. Add the S3 gateway endpoint to the private route tables. Within a few minutes
`aws ssm describe-instance-information` lists the instance as `Online`.

**Step 2 — Break it.** Remove the 443 rule from `vpce-sg`. After a few minutes the instance
drops out of Fleet Manager. Through the serial console, read the agent log:

```bash
sudo tail -n 5 /var/log/amazon/ssm/amazon-ssm-agent.log
```

```
2026-10-03 10:02:41 ERROR [HealthCheck] error when calling AWS APIs. error details - RequestError: send request failed
caused by: Post "https://ssm.ap-south-1.amazonaws.com/": dial tcp 10.20.18.77:443: i/o timeout
```

**Step 3 — Fix it.** The log names the private endpoint IP and an `i/o timeout`: a firewall on
the endpoint's ENI. Restore the 443 rule. Write down the rule of thumb: an endpoint is an ENI, so it
has a security group, and that group is checked like any other.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Endpoint SG blocks 443 | `dial tcp 10.20.x.x:443: i/o timeout` in agent or SDK logs | `aws ec2 describe-vpc-endpoints --query 'VpcEndpoints[].Groups'` | this topic |
| Private DNS disabled or VPC DNS settings off | Name resolves to a public IP, call times out with no NAT | `getent hosts SERVICE.REGION.amazonaws.com`; check `enableDnsSupport` and `enableDnsHostnames` | [DNS](08-dns.md) |
| S3 gateway endpoint missing from a route table | ECR pulls fail at layer download; S3 traffic still billed through NAT | route table for the subnet | section 8 |
| Endpoint policy too narrow | `... because no VPC endpoint policy allows` | `aws ec2 describe-vpc-endpoints --query 'VpcEndpoints[].PolicyDocument'` | section 2 |
| Bucket in another region | Gateway endpoint ignored, traffic needs NAT | `aws s3api get-bucket-location --bucket BUCKET` | section 5 |

**Why it matters for troubleshooting.** In private subnets, "AWS API call hangs" is nearly always
DNS (resolving to the public name with no NAT) or the endpoint's security group. Endpoints also
remove NAT data charges, which is why they show up again in section 12.

**Next step:** stop guessing about packets; let AWS show you the path and the drops.

### Flow Logs and Reachability Analyzer

**Level:** [L2 · Mid] · about 50 minutes · lab cost: cents

**Concept.** You cannot run tcpdump on an AWS router, but you get two tools that are often better:

- **VPC Flow Logs** record a summary line for each network flow on an ENI, subnet or VPC: source,
  destination, ports, protocol, packets, bytes and whether the SG/NACL layer **ACCEPT**ed or
  **REJECT**ed it. They go to CloudWatch Logs or S3, aggregated over 10 minutes by default (1 minute
  if you choose). They are evidence after the fact, like a firewall log. They do **not** record
  traffic to the Amazon DNS resolver, instance metadata (169.254.169.254), the Amazon Time Sync
  Service or DHCP.
- **Reachability Analyzer** is a configuration checker. You give it a source (an IGW, an instance,
  an ENI) and a destination plus port, and it reasons over route tables, SGs, NACLs, gateways and
  peering **without sending a packet**, then tells you whether a path exists and, if not, which
  component blocks it. Each analysis costs about USD 0.10.

A flow log line in the default format:

```
2 123456789012 eni-0a1b2c3d4e5f60031 198.51.100.10 10.20.5.10 51514 81 6 3 180 1759485600 1759485660 REJECT OK
│ │            │                     │             │           │     │  │ │ │   │          │          │      └ log-status
│ │            │                     │             │           │     │  │ │ │   └ start    └ end      └ action
│ account      interface             srcaddr       dstaddr     sport dport proto(6=tcp) packets bytes
└ version
```

**Key terms**

| Term | Meaning |
|---|---|
| Flow | A 5-tuple (src, dst, sport, dport, protocol) observed on an ENI in an aggregation window |
| ACCEPT / REJECT | Whether security groups and NACLs allowed the traffic |
| NODATA / SKIPDATA | log-status values: no traffic in the window / records lost |
| Network Insights path | Reachability Analyzer's saved source, destination, protocol and port |
| Explanation | The analyzer's reason a path fails, naming the blocking component |

**See it on a real system**

```bash
# Enable flow logs for one subnet, rejected traffic only (a change; cheap)
aws ec2 create-flow-logs --resource-type Subnet --resource-ids SUBNET_ID --traffic-type REJECT \
  --log-destination-type cloud-watch-logs --log-group-name /vpc/lab-flowlogs \
  --deliver-logs-permission-arn arn:aws:iam::123456789012:role/vpc-flowlogs-role
# Read a few rejected flows to port 81 from the last 30 minutes (oldest first)
aws logs filter-log-events --log-group-name /vpc/lab-flowlogs \
  --start-time "$(date -u -d '30 minutes ago' +%s)000" \
  --filter-pattern '[v, acct, eni, src, dst, sport, dport="81", proto, pkts, bytes, start, end, action="REJECT", st]' \
  --max-items 3 --query 'events[].message' --output text | tr '\t' '\n'
# Ask the analyzer: can the internet gateway reach the instance on tcp 81?
aws ec2 create-network-insights-path --source IGW_ID --destination INSTANCE_ID \
  --protocol tcp --destination-port 81 --query 'NetworkInsightsPath.NetworkInsightsPathId' --output text
aws ec2 start-network-insights-analysis --network-insights-path-id PATH_ID \
  --query 'NetworkInsightsAnalysis.NetworkInsightsAnalysisId' --output text
aws ec2 describe-network-insights-analyses --network-insights-analysis-ids ANALYSIS_ID \
  --query 'NetworkInsightsAnalyses[].{found:NetworkPathFound,why:Explanations[].ExplanationCode}'
```

```
2 123456789012 eni-0a1b2c3d4e5f60031 198.51.100.10 10.20.5.10 51514 81 6 3 180 1759485600 1759485660 REJECT OK
2 123456789012 eni-0a1b2c3d4e5f60031 198.51.100.10 10.20.5.10 51520 81 6 3 180 1759485600 1759485660 REJECT OK
nip-0a1b2c3d4e5f60041
nia-0a1b2c3d4e5f60042
[
    {
        "found": false,
        "why": [ "ENI_SG_RULES_MISMATCH" ]
    }
]
```

→ The flow log proves packets from 198.51.100.10 reached the instance's ENI and were rejected
(three SYN retries, 180 bytes each window). The analyzer agrees without any traffic: the path fails
at the ENI's security group rules. The analysis runs asynchronously, so repeat the `describe` call
until its `Status` is `succeeded` (`found` is empty while it is `running`). Drop the `--query` to see
the full explanation, which names the SG and the missing port. Explanation code names can change between releases; the console shows the
same result in plain language.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Enable REJECT flow logs on `public-a` (create the delivery role with the
console's "create role" helper). Keep the Apache-on-81 instance from the SG topic.

**Step 2 — Break it.** Remove the SG rule for port 81 and curl it from home three times. Wait about
ten minutes and read the flow log. Then run the analyzer from the IGW to the instance on tcp 81.

**Step 3 — Fix it.** Restore the rule and run a **new** analysis on the same path: `found: true`.
Next, break it a second way (the stateless NACL from the previous topic) and compare: the flow log
shows the inbound flow ACCEPTed and the outbound reply REJECTed, and the analyzer names the NACL.
Delete the flow log when you finish, or set a 3-day retention on the log group.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Expecting flow logs to be instant | Empty results during the incident | wait one aggregation interval; use 1-minute interval for debugging | this topic |
| No REJECT lines but still timing out | Packets never reached the ENI: routing, DNS, wrong IP | Reachability Analyzer, then `dig` | the drill below |
| ACCEPT in, nothing back | Problem inside the instance (UFW, app) or the return route | SSM session, `ss -ltnp`, `ufw status` | section 4 |
| Flow logs to CloudWatch with no retention | Logs bill grows forever | `aws logs describe-log-groups --query 'logGroups[].[logGroupName,retentionInDays]'` | section 12 |

**Why it matters for troubleshooting.** These two tools replace guesswork with evidence: Flow Logs
answer "did the packet arrive and what happened to it", and Reachability Analyzer answers "should it
be able to arrive, given the configuration". Use the analyzer first when a change is suspected,
and flow logs when the problem is intermittent.

**Next step:** connecting VPCs to each other.

### Peering and Transit Gateway

**Level:** [L3 · Senior] · about 60 minutes · lab cost: free (peering) / dollars (Transit Gateway)

**Concept.** Sooner or later one VPC must reach another: prod and shared services, or two accounts.

- **VPC peering** is a private link between exactly two VPCs (same or different account or
  region). It is **not transitive**: if A peers with B and B with C, A cannot reach C through B, and
  A cannot use B's IGW, NAT gateway or VPN. CIDRs must not overlap. You add routes on **both** sides
  and allow the traffic in SGs on both sides (in the same region an SG can reference the peer's SG).
  There is no hourly charge; cross-AZ and cross-region data charges still apply.
- **Transit Gateway** (TGW) is a regional router. VPCs, VPNs and Direct Connect gateways
  **attach** to it, and TGW **route tables** decide who can reach whom. Each attachment is
  **associated** with one TGW route table (which it uses for lookups) and can **propagate** its
  routes into others. That is how you build "every VPC reaches shared services and on-prem, but
  prod and dev cannot reach each other". It costs per attachment-hour (about USD 0.05) and per GB
  processed (about USD 0.02).
- **PrivateLink** exposes one service (behind an NLB) to other VPCs without routing whole networks,
  and works even when CIDRs overlap.

```
 Peering (2–3 VPCs)                Transit Gateway hub (many VPCs + on-prem)
 VPC A ◀──pcx──▶ VPC B                      ┌────────────┐
   ▲                                VPC prod─┤            ├─ VPN to on-prem 192.168.10.0/24
   └── no path to C via B           VPC dev ─┤    TGW     ├─ VPC shared (ECR, CI runners)
       (not transitive)             VPC net ─┤ RT: prod   ├─ Direct Connect gateway
 VPC B ◀──pcx──▶ VPC C                      │ RT: nonprod │
                                            └────────────┘
```

**Key terms**

| Term | Meaning |
|---|---|
| Peering connection (pcx) | One-to-one VPC link; requester and accepter |
| Transitive routing | Reaching a third network through an intermediate one; peering forbids it |
| TGW attachment | A VPC, VPN, Direct Connect gateway or TGW peering connected to the TGW |
| Association / propagation | Which TGW route table an attachment uses / which tables learn its routes |
| Appliance mode | TGW setting that keeps both directions of a flow in one AZ, needed for stateful firewalls |

**See it on a real system**

```bash
aws ec2 describe-vpc-peering-connections \
  --query 'VpcPeeringConnections[].[VpcPeeringConnectionId,Status.Code,RequesterVpcInfo.CidrBlock,AccepterVpcInfo.CidrBlock]' \
  --output table
aws ec2 search-transit-gateway-routes --transit-gateway-route-table-id TGW_RTB_ID \
  --filters Name=state,Values=active \
  --query 'Routes[].[DestinationCidrBlock,TransitGatewayAttachments[0].ResourceType,TransitGatewayAttachments[0].ResourceId,Type]' \
  --output table
```

```
------------------------------------------------------------------------
|                    DescribeVpcPeeringConnections                     |
+-------------------------+----------+----------------+----------------+
|  pcx-0a1b2c3d4e5f60051  |  active  |  10.20.0.0/16  |  10.30.0.0/16  |
+-------------------------+----------+----------------+----------------+
----------------------------------------------------------------------
|                     SearchTransitGatewayRoutes                     |
+-------------------+-------+-------------------------+--------------+
|  10.20.0.0/16     |  vpc  |  vpc-0a1b2c3d4e5f60020  |  propagated  |
|  10.30.0.0/16     |  vpc  |  vpc-0c1d2e3f4a5b60021  |  propagated  |
|  192.168.10.0/24  |  vpn  |  vpn-0a1b2c3d4e5f60061  |  propagated  |
+-------------------+-------+-------------------------+--------------+
```

→ The peering is `active` between non-overlapping ranges. The TGW route table has learned both VPCs
and the on-prem LAN (propagated from the VPN's BGP session, section 11). A VPC subnet still needs
its **own** route table entry pointing those prefixes at the TGW; propagation only fills the TGW's
tables.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create VPC `lab2` 10.30.0.0/16 with one private subnet and a t3.micro
instance. Request and accept a peering connection between `lab` and `lab2`.

**Step 2 — Break it.** Add the route `10.30.0.0/16 → pcx-...` only in `lab`'s private route table,
and allow ICMP from 10.20.0.0/16 in `lab2`'s SG. Ping from `lab` to `lab2`: nothing comes back.
Run Reachability Analyzer from the `lab` instance to the `lab2` instance; it reports the missing
return route.

**Step 3 — Fix it.** Add `10.20.0.0/16 → pcx-...` in `lab2`'s route table. Ping works. For
Transit Gateway, use the KodeKloud AWS playground or a one-hour window: attach both VPCs to a TGW,
replace the peering routes with routes to the TGW, check the TGW route table, then delete the
attachments and the TGW.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Route on one side only | One-way reachability; analyzer reports no return route | route tables on both sides | this topic |
| Expecting transitive peering | A reaches B, B reaches C, A cannot reach C | draw the topology | this topic (use TGW) |
| TGW attachment not associated or not propagated | Attached VPC unreachable; TGW route table lacks its CIDR | `aws ec2 search-transit-gateway-routes` | this topic |
| Overlapping CIDRs | Peering request fails; TGW routes ambiguous | your IP plan | "CIDR planning and subnets" |
| Firewall VPC behind TGW drops flows | Asymmetric routing across AZs | check appliance mode on the attachment | [Senior architecture](39-learn-senior-architecture.md) |

**Why it matters for troubleshooting.** In multi-VPC networks the question becomes "which route
table, on which hop, lacks the prefix?". Walk the path hop by hop (subnet route table, TGW route
table, the far subnet's route table, then back) exactly as you would trace routers on-prem.

**Next step:** put every VPC layer together in a timed drill.

### Drill: EC2 site times out

**Level:** [L2 · Mid] · 20-minute timer · lab cost: cents

The scenario: your lab copy of the on-prem Apache runs on an Ubuntu instance in `public-a`,
listening on port 81 like your real server, and `http://lab.example.com:81/` should answer from your
office IP 198.51.100.10. A colleague "tidied up" the VPC yesterday and now the request times out.
The steps below are the AWS version of the layered walk in [Site down](25-playbook-site-down.md):
DNS, then the address, then AWS's view of the path, then each firewall layer, then the OS.

**Step 1 — Classify the failure.**

**Goal:** know whether this is DNS, a timeout or a refusal before touching anything.

```bash
dig +short lab.example.com
curl -sv --connect-timeout 5 http://lab.example.com:81/ -o /dev/null
```

```
203.0.113.25
*   Trying 203.0.113.25:81...
* Connection timed out after 5001 milliseconds
* Closing connection
```

**What it means:** the name resolves, so DNS is not the first suspect. "Timed out" means no
answer at all; a closed port would print `Connection refused` immediately.

**Why this step (now):** the three answers (no name, timeout, refused) point to three different
layers. Thirty seconds here prevents an hour in the wrong console.

**Next step:** if the name did not resolve → section 6, Route 53. If refused → jump to Step 6
(something answered, so the AWS path is fine). If it timed out → Step 2.

**Step 2 — Confirm the address belongs to the instance.**

**Goal:** prove DNS points at the instance you think it does.

```bash
aws ec2 describe-instances --filters Name=tag:Name,Values=lab-apache \
  --query 'Reservations[].Instances[].[InstanceId,State.Name,PublicIpAddress,SubnetId,SecurityGroups[0].GroupId]' \
  --output table
```

```
------------------------------------------------------------------------------------------------------------
|                                            DescribeInstances                                             |
+-----------------------+-----------+----------------+----------------------------+------------------------+
|  i-0a1b2c3d4e5f60071  |  running  |  203.0.113.25  |  subnet-0a1b2c3d4e5f60101  |  sg-0a1b2c3d4e5f60072  |
+-----------------------+-----------+----------------+----------------------------+------------------------+
```

**What it means:** the instance is running and its public IP matches DNS. If the IP differed, the
instance was stopped and started (an auto-assigned public IP changes on every stop/start) and DNS
still points at the old one.

**Why this step (now):** a stale record is the cheapest cause to rule out, and every later check
needs the instance, subnet and SG IDs printed here.

**Next step:** if the IP differs → attach an Elastic IP or put an ALB in front, update DNS, retest.
If it matches → Step 3.

**Step 3 — Ask AWS whether the path exists.**

**Goal:** let Reachability Analyzer check route tables, NACLs and SGs in one pass.

```bash
aws ec2 describe-internet-gateways --filters Name=attachment.vpc-id,Values=VPC_ID \
  --query 'InternetGateways[].InternetGatewayId' --output text
aws ec2 create-network-insights-path --source IGW_ID --destination i-0a1b2c3d4e5f60071 \
  --protocol tcp --destination-port 81 --query 'NetworkInsightsPath.NetworkInsightsPathId' --output text
aws ec2 start-network-insights-analysis --network-insights-path-id PATH_ID \
  --query 'NetworkInsightsAnalysis.NetworkInsightsAnalysisId' --output text
aws ec2 describe-network-insights-analyses --network-insights-analysis-ids ANALYSIS_ID \
  --query 'NetworkInsightsAnalyses[].[Status,NetworkPathFound,Explanations[0].ExplanationCode]' --output text
```

```
igw-0a1b2c3d4e5f60073
nip-0a1b2c3d4e5f60074
nia-0a1b2c3d4e5f60075
succeeded	False	ENI_SG_RULES_MISMATCH
```

**What it means:** the configuration itself blocks the path, and the first blocking component is
the instance ENI's security group. Other answers you may see name a NACL, a missing IGW route or a
missing public IP.

**Why this step (now):** one analysis checks every AWS layer at once and costs about ten cents,
instead of reading four consoles. It also does not depend on sending traffic, so it works even
while the site is down.

**Next step:** if the explanation names an SG → Step 4. If it names a NACL → Step 4, NACL part. If
it names a route or gateway → Step 5. If `NetworkPathFound` is `True` → the AWS side is fine, go to
Step 6.

**Step 4 — Read the firewall rules the analyzer named.**

**Goal:** find the missing or wrong rule, with Flow Logs as evidence.

```bash
aws ec2 describe-security-group-rules --filters Name=group-id,Values=sg-0a1b2c3d4e5f60072 \
  --query 'SecurityGroupRules[?IsEgress==`false`].[IpProtocol,FromPort,ToPort,CidrIpv4]' --output table
aws logs filter-log-events --log-group-name /vpc/lab-flowlogs \
  --start-time "$(date -u -d '30 minutes ago' +%s)000" \
  --filter-pattern '[v, acct, eni, src="198.51.100.10", dst, sport, dport="81", proto, pkts, bytes, start, end, action, st]' \
  --max-items 2 --query 'events[].message' --output text | tr '\t' '\n'
```

```
----------------------------------------------
|         DescribeSecurityGroupRules         |
+-------+-------+-------+--------------------+
|  tcp  |  444  |  444  |  198.51.100.10/32  |
|  tcp  |  22   |  22   |  198.51.100.10/32  |
+-------+-------+-------+--------------------+
2 123456789012 eni-0a1b2c3d4e5f60031 198.51.100.10 10.20.5.10 51514 81 6 3 180 1759485600 1759485660 REJECT OK
```

**What it means:** port 81 is missing from the SG (the "tidy-up" removed it and left SSH open,
which is the wrong way round), and the flow log confirms packets from your office reached the ENI
and were rejected.

**Why this step (now):** the analyzer told you *where*; the rule list tells you *what*, and the
flow log proves the live traffic hit exactly that block, so you fix one rule with confidence.

**Next step:** add the rule (Fix and verify below) and retest from Step 1. If the SG was right but
the NACL was named → check its inbound rule for 81 and its outbound ephemeral rule, as in
"Security groups vs NACLs". If both are right → Step 5.

**Step 5 — Check the subnet's route to the internet.**

**Goal:** make sure replies can leave through the IGW.

```bash
aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=subnet-0a1b2c3d4e5f60101 \
  --query 'RouteTables[].Routes[].[DestinationCidrBlock,GatewayId,State]' --output table
```

```
-------------------------------------------------------
|                 DescribeRouteTables                 |
+----------------+-------------------------+----------+
|  10.20.0.0/16  |  local                  |  active  |
|  0.0.0.0/0     |  igw-0a1b2c3d4e5f60073  |  active  |
+----------------+-------------------------+----------+
```

**What it means:** the subnet is genuinely public. If the `0.0.0.0/0` line were missing or pointed
at a NAT gateway, inbound SYNs would arrive but replies would never reach the internet.

**Why this step (now):** after firewall rules, routing is the next most common cause, and it is a
single read-only call. An empty result means the subnet uses the main route table, which is
itself a frequent cause after a tidy-up.

**Next step:** if the default route is missing or wrong → associate the subnet with the public
route table and retest. If it is correct and Step 3 found a path → Step 6.

**Step 6 — Look inside the instance.**

**Goal:** confirm Apache listens on 81 on all addresses and nothing on the host drops the traffic.

```bash
aws ssm start-session --target i-0a1b2c3d4e5f60071
# inside the session:
sudo ss -ltnp 'sport = :81'
sudo ufw status verbose | head -5
curl -sI http://127.0.0.1:81/ | head -1
```

```
State  Recv-Q Send-Q Local Address:Port Peer Address:Port Process
LISTEN 0      511          0.0.0.0:81        0.0.0.0:*     users:(("apache2",pid=1342,fd=4),("apache2",pid=1341,fd=4))
Status: inactive
HTTP/1.1 200 OK
```

**What it means:** Apache listens on every address on 81, UFW is off and the local request works.
If `Local Address` showed `127.0.0.1:81`, Apache would be reachable only from the instance itself;
if UFW were active without an allow rule, the AWS layers would look perfect and still time out.

**Why this step (now):** you only open a shell after the AWS layers are cleared, because the OS
layer cannot explain an SG or route problem, and SSM gives you a shell without opening port 22.

**Next step:** if Apache is not listening or bound to 127.0.0.1 → fix `ports.conf` and the vhost,
`sudo apache2ctl configtest`, reload, and see [Ports inventory](22-playbook-ports-inventory.md). If
UFW blocks → `sudo ufw allow 81/tcp` (or from the specific source) and retest from Step 1.

**Decision tree**

```
 curl times out / refused / no DNS?
 ├─ no DNS ─────────────▶ Route 53 (section 6)
 ├─ refused ────────────▶ Step 6: ss -ltnp, Apache config
 └─ timeout
     └─ DNS IP == instance public IP?
         ├─ no ─────────▶ stale record: EIP or ALB, fix DNS
         └─ yes ─▶ Reachability Analyzer IGW → instance:81
                  ├─ SG named ─────▶ add rule (source = office /32 or ALB SG)
                  ├─ NACL named ───▶ inbound 81 + outbound 1024-65535
                  ├─ route named ──▶ subnet → public route table (0/0 → igw)
                  └─ path found ───▶ Step 6: UFW, bind address, app
```

**Fix and verify.**

```bash
aws ec2 authorize-security-group-ingress --group-id sg-0a1b2c3d4e5f60072 \
  --ip-permissions 'IpProtocol=tcp,FromPort=81,ToPort=81,IpRanges=[{CidrIp=198.51.100.10/32,Description=office-apache}]'
curl -sI --connect-timeout 5 http://lab.example.com:81/ | head -1
```

```
HTTP/1.1 200 OK
```

Then re-run the analysis on the same path and expect `NetworkPathFound: True`.

**Rollback.** The fix only adds a rule. To undo it, run `aws ec2 revoke-security-group-ingress`
with the same `--ip-permissions`. Note the rule ID from `describe-security-group-rules` in the
ticket so the rollback is exact.

**Prevent it next time.** Manage SGs in Terraform or CloudFormation (section 10) so a "tidy-up"
shows up as a reviewed diff; keep a saved Reachability Analyzer path for each critical service and
re-run it after network changes; alert on a CloudTrail `RevokeSecurityGroupIngress` event for
production SGs (section 9); and close port 22 entirely in favour of SSM.

---

## 4. EC2 compute

> 📚 **Study path:** 1) KodeKloud: *Crash Course: AWS Basics* — the EC2 part, free ([link](https://kodekloud.com/courses/crash-course-aws-basics)) · 2) Note: this section, then [AWS reference](16-aws-cloud.md) sections 2–4 and 7 (IMDS, EC2 health, EBS, SSM) and the Linux side in [Learn: Linux](27-learn-linux.md) · 3) KodeKloud: *AWS Certified CloudOps Engineer - Associate* — the Monitoring, Logging and Remediation domain (CloudWatch, SSM) and the Reliability domain, after CKA ([link](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 4) Practice: one EC2 task from [100 Days of Cloud](https://kodekloud.com/100-days-of-cloud) each morning, and the break-and-fix labs below in your sandbox

Tags: [L0 · Fresher] for types and AMIs, [L1 · Junior] for user data, EBS and SSM, [L2 · Mid] for credits and steal, IMDSv2, EBS performance and status checks.

An EC2 instance is an Ubuntu server you already know how to run. What is new is everything around
it: how its size limits CPU, disk and network; how it boots from an image and configures itself;
how it gets credentials; and how you reach it when SSH is not an option. Your on-prem tools
(`top`, `iostat`, `journalctl`, `ss`) all still work and you will use them in every topic.

### Instance types, credits and steal

**Level:** [L0 · Fresher] → [L2 · Mid] · about 45 minutes · lab cost: cents

**Concept.** An instance type name encodes what you get: `m7i.large` is family **m** (general
purpose), generation **7**, processor option **i** (Intel; **g** is Graviton ARM, **a** is AMD),
size **large** (2 vCPUs, 8 GiB). Families: **t** burstable, **m** general purpose, **c** compute,
**r** memory, **i**/**d** local NVMe storage, **g**/**p** GPU. The size also caps **network
bandwidth** and **EBS bandwidth**, which is why a small instance can be "slow" with a fast disk.

**Burstable (t2, t3, t3a, t4g)** instances earn **CPU credits** while below a baseline (for example
20% per vCPU on t3.small) and spend them above it. One credit is one vCPU at 100% for one minute.

- In **standard** mode (t2 default), when credits reach zero the instance is throttled to the
  baseline. The app gets slow and `top` shows high **steal** (`st`).
- In **unlimited** mode (t3/t3a/t4g default), it keeps bursting and you pay for **surplus credits**
  if the 24-hour average exceeds the baseline. No slowdown, a bill line instead.

**Steal time** is CPU time the hypervisor gave to someone else while your vCPU wanted to run. On a
throttled t-instance it is the credit limiter; on other types, steady steal above a few percent
means you need a bigger or different type. On-prem you see the same number on an overcommitted
KVM or VMware host.

**Key terms**

| Term | Meaning |
|---|---|
| vCPU | One hardware thread; most x86 types have 2 vCPUs per physical core |
| Baseline | The CPU percentage a burstable instance can sustain without spending credits |
| CPUCreditBalance | CloudWatch metric: credits left |
| CPUSurplusCreditBalance | Credits spent beyond the balance in unlimited mode (billed if not paid back) |
| Steal (`st`) | CPU time stolen by the hypervisor; visible in `top`, `vmstat`, `mpstat` |
| Nitro | Current AWS hypervisor and hardware; NVMe device names, ENA networking |

**See it on a real system**

```bash
aws ec2 describe-instance-types --instance-types t3.medium m7i.large \
  --query 'InstanceTypes[].[InstanceType,VCpuInfo.DefaultVCpus,MemoryInfo.SizeInMiB,NetworkInfo.NetworkPerformance,EbsInfo.EbsOptimizedInfo.BaselineThroughputInMBps]' \
  --output table
aws ec2 describe-instance-credit-specifications --instance-ids i-0a1b2c3d4e5f60011 --output text
aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUCreditBalance \
  --dimensions Name=InstanceId,Value=i-0a1b2c3d4e5f60011 --statistics Minimum \
  --start-time "$(date -u -d '6 hours ago' +%FT%TZ)" --end-time "$(date -u +%FT%TZ)" --period 3600 \
  --query 'sort_by(Datapoints,&Timestamp)[].[Timestamp,Minimum]' --output text
# On the instance
vmstat 1 5
```

```
---------------------------------------------------------------
|                    DescribeInstanceTypes                    |
+-------------+-----+--------+----------------------+---------+
|  t3.medium  |  2  |  4096  |  Up to 5 Gigabit     |  43.75  |
|  m7i.large  |  2  |  8192  |  Up to 12.5 Gigabit  |  81.25  |
+-------------+-----+--------+----------------------+---------+
INSTANCECREDITSPECIFICATIONS	standard	i-0a1b2c3d4e5f60011
2026-10-03T04:00:00+00:00	142.3
2026-10-03T05:00:00+00:00	61.8
2026-10-03T06:00:00+00:00	3.1
2026-10-03T07:00:00+00:00	0.0
2026-10-03T08:00:00+00:00	0.0
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 3  0      0 2131452  60212 1104388   0    0     1     6  612  901 17  2  0  0 81
 2  0      0 2131300  60212 1104390   0    0     0     0  598  880 18  2  0  0 80
```

→ The baseline EBS throughput of a t3.medium is about 44 MB/s (it can burst higher for a while),
which matters for the EBS topic below. The instance is in **standard** credit mode, its balance
fell to zero two hours ago, and `vmstat` shows `st` around 80%: the hypervisor is throttling it to
baseline. This is the classic "server got slow at 07:00 for no reason" on a t2/t3.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Launch a t3.micro, switch it to standard mode with
`aws ec2 modify-instance-credit-specification --instance-credit-specification
'InstanceId=INSTANCE_ID,CpuCredits=standard'`, and install `stress-ng`.

**Step 2 — Break it.** Run `stress-ng --cpu 2 --timeout 3h` and watch `CPUCreditBalance` fall and
`st` climb in `vmstat 5`. A freshly launched t3.micro has little or no credit balance, so this
happens within the hour.

**Step 3 — Fix it.** Choose deliberately: switch to unlimited (pay for the burst), move to a bigger
t-size, or move to a non-burstable type (m7i or m7g) if the load is steady. Stop `stress-ng` and
terminate the instance.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Credits exhausted (standard mode) | App slow, `st` high, CPU graph flat at baseline | `aws cloudwatch get-metric-statistics ... CPUCreditBalance` | [Slow system](23-playbook-slow-system.md) |
| Unlimited mode surplus | "EC2 CPU Credits" line on the bill | `aws ec2 describe-instance-credit-specifications` | section 12 |
| Network or EBS cap of a small size | Throughput plateaus at a round number | `aws ec2 describe-instance-types` | "EBS performance and snapshots" |
| `InsufficientInstanceCapacity` | Launch fails in one AZ | try another AZ or type | section 9 (Auto Scaling) |

**Why it matters for troubleshooting.** On-prem, a slow VM makes you check the host. On AWS you
cannot see the host, but the instance type, its credit balance and `st` tell you the same story.
Check them before tuning Apache.

**Next step:** what the instance boots from and how it configures itself.

### AMIs, user data and cloud-init

**Level:** [L0 · Fresher] → [L1 · Junior] · about 40 minutes · lab cost: cents

**Concept.** An **AMI** (Amazon Machine Image) is a template: one or more EBS snapshots plus
launch metadata. It is **regional**; copy it to use it in another region. Canonical publishes
official Ubuntu AMIs (owner ID 099720109477) and also publishes their IDs as public SSM parameters,
so scripts never hardcode an AMI ID that is different in every region.

At first boot, **cloud-init** reads **user data** (a shell script or a `#cloud-config` YAML you
pass at launch) from the instance metadata service, then sets the hostname, installs SSH keys,
writes netplan, and runs your script **once**. It is the same cloud-init you can use on-prem with
KVM or a NoCloud seed. A golden-image pipeline (Packer or EC2 Image Builder) bakes the slow parts
into the AMI so user data stays short.

**Key terms**

| Term | Meaning |
|---|---|
| AMI | Image used to launch instances; regional; backed by EBS snapshots |
| User data | Script or cloud-config passed at launch, run by cloud-init on first boot (16 KB limit) |
| cloud-init | First-boot agent; logs to `/var/log/cloud-init.log` and `/var/log/cloud-init-output.log` |
| Launch template | Saved, versioned set of launch parameters (AMI, type, SG, user data, IMDS settings) |
| Golden AMI | Your pre-hardened, pre-installed image, rebuilt on a schedule |

**See it on a real system**

```bash
aws ssm get-parameter --name /aws/service/canonical/ubuntu/server/24.04/stable/current/amd64/hvm/ebs-gp3/ami-id \
  --query Parameter.Value --output text
aws ec2 describe-images --image-ids ami-0f1e2d3c4b5a60091 \
  --query 'Images[].[Name,OwnerId,CreationDate]' --output text
# On the instance
cloud-init status --long
sudo tail -n 4 /var/log/cloud-init-output.log
```

```
ami-0f1e2d3c4b5a60091
ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-20260918	099720109477	2026-09-18T11:04:52.000Z
status: done
extended_status: done
boot_status_code: enabled-by-generator
last_update: Sat, 03 Oct 2026 08:14:31 +0000
detail: DataSourceEc2Local
errors: []
recoverable_errors: {}
Setting up apache2 (2.4.58-1ubuntu8.8) ...
Enabling site 000-default.
apache2 started on port 81
Cloud-init v. 25.2-0ubuntu1~24.04.1 finished at Sat, 03 Oct 2026 08:14:31 +0000. Datasource DataSourceEc2Local.  Up 41.62 seconds
```

→ The SSM parameter returns the current official Ubuntu 24.04 AMI for this region; `describe-images`
confirms the owner is Canonical. `cloud-init status` says `done` with no errors, and the output log
ends with your script's last `echo` and the total boot time.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Save this as `userdata.sh` and launch an instance with
`--user-data file://userdata.sh`, the AMI from the SSM parameter and a `Project=lab` tag:

```bash
#!/bin/bash
set -euxo pipefail
apt-get update
apt-get install -y apache2
sed -i 's/^Listen 80$/Listen 81/' /etc/apache2/ports.conf
sed -i 's/<VirtualHost \*:80>/<VirtualHost *:81>/' /etc/apache2/sites-available/000-default.conf
systemctl restart apache2
echo "apache2 started on port 81"
```

**Step 2 — Break it.** Launch another one with a typo (`apt-get install -y apache`). The instance
is "running" and passes status checks, yet nothing listens on 81. `cloud-init status --long`
shows `status: error`, and `/var/log/cloud-init-output.log` contains
`E: Unable to locate package apache`.

**Step 3 — Fix it.** User data runs only on the first boot, so editing it and rebooting does not
re-run it. Fix the launch template and replace the instance (the cloud way), or run the corrected
script by hand once. Keep `set -euxo pipefail` so a failure stops the script and shows up as a
cloud-init error instead of a half-configured server.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| User data script failed | Instance up, service missing | `cloud-init status --long`, `/var/log/cloud-init-output.log` | this topic |
| Edited user data, nothing happened | Change "ignored" on reboot | remember it runs once per instance | this topic |
| Hardcoded AMI ID in another region | `InvalidAMIID.NotFound` | use the SSM parameter | section 1 |
| Old AMI deregistered | Auto Scaling launches fail | `aws autoscaling describe-scaling-activities` | section 9 |
| No internet at first boot (private subnet) | `apt-get` hangs, cloud-init times out | route table, NAT or endpoints | section 3 |

**Why it matters for troubleshooting.** An instance that "came up broken" is usually a first-boot
problem. `cloud-init status --long` and the output log are the first two things to read, just
as `journalctl -b` is on-prem.

**Next step:** the metadata service that delivered that user data, and how to protect it.

### IMDSv2

**Level:** [L2 · Mid] · about 40 minutes · lab cost: cents

**Concept.** Every instance can reach the **Instance Metadata Service** at 169.254.169.254 (link
local, never leaves the host). It serves the instance ID, region, user data and, most importantly,
the **temporary credentials of the instance role**. IMDSv1 answered any plain GET, which made
server-side request forgery (an app tricked into fetching a URL) a credential-theft bug. **IMDSv2**
requires a session token obtained with a `PUT` first, and the token response has an IP TTL
(**hop limit**) of 1 by default, so it does not survive an extra network hop. The defaults depend on
the AMI: an AMI flagged `ImdsSupport: v2.0` (Amazon Linux 2023, for example) launches with tokens
required and a hop limit of 2, and an account-level default can override both, so check
`MetadataOptions` on the instance instead of assuming.

That hop limit matters for containers: a process in a Docker bridge network or a pod is one hop
further away, so it times out fetching the token and the SDK reports "no credentials". Set the hop
limit to 2 when containers on the instance must use the instance role, or (better) give them their
own role (ECS task roles, EKS Pod Identity).

**Key terms**

| Term | Meaning |
|---|---|
| IMDS | Instance Metadata Service at 169.254.169.254 (and fd00:ec2::254 for IPv6) |
| IMDSv2 | Session-oriented IMDS: PUT for a token, then GETs with the token header |
| `HttpTokens` | `optional` (v1 and v2 allowed) or `required` (v2 only) |
| Hop limit | `HttpPutResponseHopLimit`, the IP TTL of the token response; default 1 (2 for `ImdsSupport: v2.0` AMIs) |
| Account default | Region-level default IMDS settings for new launches |

**See it on a real system**

```bash
TOKEN=$(curl -s -X PUT http://169.254.169.254/latest/api/token \
  -H 'X-aws-ec2-metadata-token-ttl-seconds: 300')
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id; echo
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/; echo
curl -s -o /dev/null -w 'v1 GET: %{http_code}\n' http://169.254.169.254/latest/meta-data/instance-id
aws ec2 describe-instances --instance-ids i-0a1b2c3d4e5f60011 \
  --query 'Reservations[].Instances[].MetadataOptions.[HttpTokens,HttpPutResponseHopLimit,HttpEndpoint]' --output text
```

```
i-0a1b2c3d4e5f60011
app-ec2-role
v1 GET: 401
required	2	enabled
```

→ The token flow works and the role name is `app-ec2-role`. A plain v1 GET gets `401
Unauthorized`, which proves v2 is enforced. The hop limit is 2, so containers on this host can
reach IMDS. Never print the full credentials document in a ticket or a log.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** On the lab instance with `HttpTokens=required` and hop limit 1, install
Docker and run `docker run --rm amazon/aws-cli sts get-caller-identity`.

**Step 2 — Break it.** It fails after a delay:

```
Unable to locate credentials. You can configure credentials by running "aws configure".
```

The same command on the host works. The container is one hop further away, so the token response
dies on the way.

**Step 3 — Fix it.** Raise the hop limit and retry:

```bash
aws ec2 modify-instance-metadata-options --instance-id INSTANCE_ID \
  --http-tokens required --http-put-response-hop-limit 2
```

Then decide whether containers should share the instance role at all. On ECS and EKS, they should
not: use task roles or Pod Identity (section 8).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Hop limit 1 with containers | SDK in a container: no credentials or timeout; host works | `aws ec2 describe-instances --query '...MetadataOptions'` | this topic |
| Old SDK or script uses v1 | `401` from IMDS after enforcing v2 | CloudWatch `MetadataNoToken` metric before enforcing | this topic |
| IMDS disabled (`HttpEndpoint=disabled`) | cloud-init and agents cannot get metadata | `MetadataOptions.HttpEndpoint` | this topic |
| UFW or iptables blocks 169.254.169.254 | Agents fail after a firewall change | `curl -s -X PUT ...` on the host | section 3 |

**Why it matters for troubleshooting.** "Unable to locate credentials" on EC2 means one of three
things: no instance profile, a credential env var overriding it, or IMDS unreachable. This topic is
the third; section 2 covers the first two.

**Next step:** the disks behind the instance.

### EBS performance and snapshots

**Level:** [L1 · Junior] → [L2 · Mid] · about 60 minutes · lab cost: cents

**Concept.** An EBS volume is network block storage: an iSCSI LUN you never cable. It lives in
**one AZ** and attaches to instances in that AZ. Performance is **provisioned**, not "as fast as the
disks":

| Type | IOPS | Throughput | Use |
|---|---|---|---|
| gp3 (default) | 3,000 included at any size; provision more independently | 125 MiB/s included; provision more | Almost everything |
| gp2 (legacy) | 3 per GiB, burst to 3,000 for small volumes with a **BurstBalance** | tied to size | Migrate to gp3 (cheaper, no burst cliff) |
| io2 Block Express | provisioned, up to 256,000 | up to 4,000 MiB/s | Large databases that need low latency |
| st1 / sc1 | low | throughput-oriented HDD | Logs, big sequential data |

Per-volume maximums for gp3 were raised in 2025; check the current EBS volume types page on
[docs.aws.amazon.com](https://docs.aws.amazon.com/) before you size a large volume. The other
limit is the **instance**: every type has a maximum EBS bandwidth and IOPS, and small sizes run on
a burst bucket for EBS too. A 10,000-IOPS gp3 volume on a t3.micro will not deliver 10,000 IOPS.

**Snapshots** are incremental, block-level copies stored regionally (in S3, managed by AWS). They
are crash-consistent unless you quiesce the application. A volume restored from a snapshot is
**lazily loaded**: the first read of each block is fetched from S3 and is slow until the volume
is initialized (or you pay for Fast Snapshot Restore). Restoring a database volume and benchmarking
it immediately is a classic misleading test.

On Nitro instances volumes appear as NVMe devices (`/dev/nvme1n1`), not the `/dev/sdf` name you
chose at attach time. The volume ID is in the NVMe serial number.

**Key terms**

| Term | Meaning |
|---|---|
| IOPS / throughput | Operations per second / MiB per second; gp3 provisions them separately |
| VolumeQueueLength | CloudWatch metric; the cloud version of `aqu-sz` in `iostat -x` |
| Snapshot | Incremental, regional point-in-time copy of a volume |
| Initialization | First-touch fetch of blocks for a volume created from a snapshot |
| Data Lifecycle Manager | Scheduled snapshot policies by tag |
| Elastic Volumes | Change size, type, IOPS and throughput of a live volume |

**See it on a real system**

```bash
aws ec2 describe-volumes --filters Name=attachment.instance-id,Values=i-0a1b2c3d4e5f60011 \
  --query 'Volumes[].[VolumeId,VolumeType,Size,Iops,Throughput,Attachments[0].Device]' --output table
# On the instance
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,SERIAL
iostat -xm 1 3 nvme1n1
```

```
--------------------------------------------------------------------------
|                            DescribeVolumes                             |
+-------------------------+-------+-------+--------+-------+-------------+
|  vol-0a1b2c3d4e5f60101  |  gp3  |  20   |  3000  |  125  |  /dev/sda1  |
|  vol-0a1b2c3d4e5f60102  |  gp3  |  100  |  3000  |  125  |  /dev/sdf   |
+-------------------------+-------+-------+--------+-------+-------------+
NAME          SIZE TYPE MOUNTPOINT SERIAL
nvme0n1        20G disk            vol0a1b2c3d4e5f60101
├─nvme0n1p1    19G part /
├─nvme0n1p14    4M part
├─nvme0n1p15  106M part /boot/efi
└─nvme0n1p16  913M part /boot
nvme1n1       100G disk /data      vol0a1b2c3d4e5f60102
Device            r/s     w/s     rMB/s     wMB/s   r_await w_await aqu-sz  %util
nvme1n1          0.00 3010.00      0.00    117.60     0.00   10.84  32.61  100.00
```

→ `/dev/sdf` in the API is `nvme1n1` on the host (match the serial to the volume ID; the `iostat`
lines are trimmed to the key columns, and `wMB/s` comes from `-m`). The data
volume is writing at about 3,000 IOPS and 118 MB/s with a queue of 32 and 11 ms write latency: it
is pinned at exactly its provisioned gp3 limits. This is not a broken disk; it is a full one.
The fix is to provision more IOPS or throughput, not to tune the filesystem.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Attach a 20 GiB gp3 volume, format it ext4, mount it on `/data`. Run
`fio --name=w --filename=/data/t --size=2G --rw=randwrite --bs=16k --iodepth=32 --direct=1
--runtime=60 --time_based` and note IOPS.

**Step 2 — Break it.** You need more space and speed, without downtime. Grow it live:

```bash
aws ec2 modify-volume --volume-id VOLUME_ID --size 40 --iops 6000 --throughput 250
aws ec2 describe-volumes-modifications --volume-ids VOLUME_ID \
  --query 'VolumesModifications[].[ModificationState,Progress]' --output text
# On the instance, after the state is optimizing or completed:
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT /dev/nvme1n1
df -h /data
```

```
optimizing	12
NAME    SIZE TYPE MOUNTPOINT
nvme1n1  40G disk /data
Filesystem      Size  Used Avail Use% Mounted on
/dev/nvme1n1     20G  2.1G   17G  12% /data
```

The block device is 40G but the filesystem still says 20G.

**Step 3 — Fix it.** Grow the filesystem: `sudo resize2fs /dev/nvme1n1` (ext4 on a whole disk;
for a partition, first `sudo growpart /dev/nvme0n1 1`; for XFS, `sudo xfs_growfs /data`). Rerun
`fio` and compare. Then snapshot the volume, create a new volume from the snapshot, attach it and
run the same `fio` read test twice: the first run is slower because of initialization.

> ⚠️ Volume modifications are rationed (since January 2026, up to four per volume in a rolling
> 24 hours, each only after the previous one completes; before that it was one every six hours),
> and you cannot shrink a volume. Safer first: snapshot before any resize, and decide the target
> size and performance before you run `modify-volume`.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Volume at provisioned limit | `%util` 100, high `await`, flat IOPS at a round number | `iostat -x 1`, `aws ec2 describe-volumes` | [Storage & disk](01-storage-disk.md) |
| Instance EBS bandwidth cap | Several volumes together cap at one number | `aws ec2 describe-instance-types ... EbsInfo` | this topic |
| gp2 BurstBalance at 0 | Fast for an hour, then slow | CloudWatch `BurstBalance` | this topic (move to gp3) |
| Volume grown, filesystem not | `df` shows the old size | `lsblk` vs `df -h` | [Storage & disk](01-storage-disk.md) |
| Restored volume slow | First reads slow after restore | initialize with `fio` or `dd` read pass | this topic |
| Unattached volumes | Bill for storage nobody uses | `aws ec2 describe-volumes --filters Name=status,Values=available` | section 12 |

**Why it matters for troubleshooting.** On-prem, slow I/O sends you to the RAID controller. On AWS
it sends you to two numbers: the volume's provisioned IOPS/throughput and the instance's EBS limit.
`iostat -x` tells you which one you are hitting.

**Next step:** what to do when the instance itself stops answering.

### Status checks and serial console

**Level:** [L2 · Mid] · about 45 minutes · lab cost: cents

**Concept.** EC2 runs automated checks every minute and shows them as **2/2** or **3/3 checks
passed**:

| Check | What it tests | Typical causes when it fails | Who fixes it |
|---|---|---|---|
| System status | AWS host: power, network, hardware | Host failure, network loss | AWS; you stop/start (moves to a new host) or let auto-recovery do it |
| Instance status | Your OS answers the hypervisor's network probe | Kernel panic, bad `/etc/fstab`, broken netplan, full memory, wrong kernel | You |
| Attached EBS status | Attached volumes reachable and performing | EBS impairment | AWS, then you verify the data |

When the instance check fails you usually cannot SSH or use SSM, because the OS or its network is
down. Two tools still work: **get-console-output** (the boot log, read-only) and the **EC2 serial
console** (an interactive TTY on Nitro instances, like an iLO/iDRAC console). The serial console
must be enabled at account level, and you need a local OS user with a password to log in. Systemd's
emergency mode asks specifically for **root's** password, which Ubuntu locks by default (with a
locked root the console prints `Cannot open access to console, the root account is locked.` instead
of a password prompt), so decide before an incident how you will get in: a root password on the image, or the rescue-instance method
in the lab below.

**Key terms**

| Term | Meaning |
|---|---|
| StatusCheckFailed_System / _Instance | CloudWatch metrics for the two checks |
| Auto recovery | Recovers an instance to new hardware on system check failure (default on supported types) |
| Console output | Buffered serial log of the boot, readable through the API |
| Serial console | Interactive serial access via EC2 Instance Connect; Nitro only; account opt-in |
| Scheduled event | Planned AWS maintenance (reboot, retirement) on your instance |

**See it on a real system**

```bash
aws ec2 describe-instance-status --instance-ids i-0a1b2c3d4e5f60011 --include-all-instances \
  --query 'InstanceStatuses[].[InstanceId,InstanceState.Name,SystemStatus.Status,InstanceStatus.Status,Events[0].Code]' \
  --output table
aws ec2 get-console-output --instance-id i-0a1b2c3d4e5f60011 --latest --query Output --output text | tail -n 6
```

```
------------------------------------------------------------------
|                     DescribeInstanceStatus                     |
+-----------------------+-----------+------+------------+--------+
|  i-0a1b2c3d4e5f60011  |  running  |  ok  |  impaired  |  None  |
+-----------------------+-----------+------+------------+--------+
[  OK  ] Finished systemd-remount-fs.service - Remount Root and Kernel File Systems.
[ TIME ] Timed out waiting for device dev-disk-by\x2duuid-3f6c1d2e\x2d....device - /dev/disk/by-uuid/3f6c1d2e-....
[DEPEND] Dependency failed for data.mount - /data.
[DEPEND] Dependency failed for local-fs.target - Local File Systems.
You are in emergency mode. After logging in, type "journalctl -xb" to view
Give root password for maintenance
```

→ The system check is `ok` (the AWS host is fine) and the instance check is `impaired` (your OS).
The console output shows why: an `/etc/fstab` entry for `/data` points at a volume that is no
longer attached, and systemd dropped into emergency mode. On-prem you would see the same on the
VM console.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Enable the serial console for the account
(`aws ec2 enable-serial-console-access`). On a lab instance, set a root password for this lab only
(`sudo passwd root`), because emergency mode will ask for it.

**Step 2 — Break it.** Add the `/data` volume to `/etc/fstab` by UUID **without** `nofail`, stop the
instance, detach the volume, start it again. Within a few minutes the instance check shows
`impaired`, SSM shows the instance offline, and the console output looks like the sample above.

**Step 3 — Fix it.** Connect: EC2 console → Connect → EC2 serial console. Press Enter, type the
root password at "Give root password for maintenance", then `mount -o remount,rw /`, edit
`/etc/fstab` to add `nofail` to the `/data` line (or remove it), and `reboot`. The check returns to
`ok`. Without a root password you have two other ways out: reattach the missing volume and reboot,
or use a **rescue instance** (stop the broken instance, detach its root volume, attach it to a
helper instance in the same AZ, mount it, fix `etc/fstab`, then reattach it as the root device and
start). Write the lesson down: **every non-root EBS line in fstab gets `nofail`**. Finally lock
root again with `sudo passwd -l root`.

> ⚠️ The serial console is a powerful back door. Safer setup: enable it only in accounts that need
> it, restrict `ec2-instance-connect:SendSerialConsoleSSHPublicKey` in IAM to your admin role, and
> treat any OS password you set for it as a secret with an owner and a rotation date. Practise the
> rescue-instance method too, because it works on every instance type.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| fstab entry for missing volume | Instance check impaired, emergency mode in console output | `aws ec2 get-console-output --instance-id INSTANCE_ID --latest --query Output --output text` | [Storage & disk](01-storage-disk.md) |
| Broken netplan or UFW lockout | Instance check impaired or unreachable, console shows normal boot | serial console, `netplan get`, `ufw status` | [Network](02-network.md) |
| System check failed | AWS host issue | stop and start (not reboot) to move hosts | this topic |
| Scheduled retirement event | Email and an `Events` entry | `aws ec2 describe-instance-status` | section 9 |
| Out of memory, hung | Status flaps, OOM lines in console | `get-console-output`, then [Memory](04-memory.md) | [Slow system](23-playbook-slow-system.md) |

**Why it matters for troubleshooting.** "Which check failed" decides who acts: system means AWS
hardware (stop/start, recovery), instance means your OS (console output, serial console). Reading
the console output before rebooting keeps the evidence.

**Next step:** the everyday way in, without SSH at all.

### SSM Session Manager

**Level:** [L1 · Junior] · about 40 minutes · lab cost: free

**Concept.** **Session Manager** gives you a shell on an instance through the SSM agent, which
connects **outbound** over HTTPS to the SSM service. No inbound port, no SSH keys, no bastion.
Access is an IAM permission (`ssm:StartSession`) and every session can be logged to CloudWatch Logs
or S3. It also does **port forwarding**, which is how you reach Apache on 81 or a database from your
laptop without exposing anything. The same agent runs commands across a fleet (Run Command) and
can manage **on-prem servers** through a hybrid activation, so your Ubuntu fleet and EC2 can share
one access path.

Three conditions must all be true for an instance to appear as **Online**:

```
 1. Agent installed and running   (Ubuntu AMIs: snap "amazon-ssm-agent", preinstalled)
 2. Identity                       (instance profile with AmazonSSMManagedInstanceCore,
                                    or Default Host Management Configuration)
 3. Network path to ssm, ssmmessages (and ec2messages for agents before 3.3.40.0) over 443
                                   (public subnet, NAT gateway, or VPC interface endpoints)
```

**Key terms**

| Term | Meaning |
|---|---|
| SSM agent | Daemon on the instance that talks to Systems Manager |
| Managed node | Instance or on-prem server registered with Systems Manager |
| Session document | Defines session type, for example `AWS-StartPortForwardingSession` |
| Session Manager plugin | Local binary the AWS CLI needs for `start-session` |
| Hybrid activation | Registers non-AWS servers as managed nodes (`mi-` IDs) |

**See it on a real system**

```bash
aws ssm describe-instance-information \
  --query 'InstanceInformationList[].[InstanceId,PingStatus,PlatformName,PlatformVersion,AgentVersion]' --output table
aws ssm start-session --target i-0a1b2c3d4e5f60011 \
  --document-name AWS-StartPortForwardingSession --parameters 'portNumber=81,localPortNumber=8081'
# On the instance
sudo snap services amazon-ssm-agent
```

```
-------------------------------------------------------------------------
|                      DescribeInstanceInformation                      |
+------------------------+----------+----------+---------+--------------+
|  i-0a1b2c3d4e5f60011   |  Online  |  Ubuntu  |  24.04  |  3.3.2299.0  |
|  mi-0a1b2c3d4e5f6a0b1  |  Online  |  Ubuntu  |  22.04  |  3.3.2299.0  |
+------------------------+----------+----------+---------+--------------+

Starting session with SessionId: learner-0a1b2c3d4e5f60111
Port 8081 opened for sessionId learner-0a1b2c3d4e5f60111.
Waiting for connections...
Service                            Startup  Current  Notes
amazon-ssm-agent.amazon-ssm-agent  enabled  active   -
```

→ Both the EC2 instance and an on-prem server (the `mi-` ID, registered with a hybrid activation)
are online. The port-forwarding session maps `localhost:8081` on your laptop to Apache on 81 on
the instance, so `curl -sI http://localhost:8081/` works with no SG rule at all.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Remove the SSH rule from the lab instance's SG. Make sure the instance
profile has `AmazonSSMManagedInstanceCore`, install the Session Manager plugin locally, and open a
shell with `aws ssm start-session --target INSTANCE_ID`. Run `whoami` (sessions start as
`ssm-user`).

**Step 2 — Break it.** Detach the instance profile and wait a few minutes. The instance turns
`ConnectionLost` and `start-session` fails:

```
An error occurred (TargetNotConnected) when calling the StartSession operation: i-0a1b2c3d4e5f60011 is not connected.
```

**Step 3 — Fix it.** Walk the three conditions in order: agent (`snap services`, via the serial
console if needed), identity (instance profile), network (route to NAT or endpoints, endpoint SG).
Reattach the profile; the agent picks up credentials within minutes (restart it with
`sudo snap restart amazon-ssm-agent` to hurry it). Then turn on session logging to CloudWatch
Logs in Session Manager preferences.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| No instance profile or missing policy | `TargetNotConnected`; not listed in Fleet Manager | `aws ec2 describe-instances --query '...IamInstanceProfile'` | section 2 |
| No path to the SSM endpoints | Agent log shows `i/o timeout` to ssm.REGION.amazonaws.com | agent log, route table, endpoints | section 3, "VPC endpoints" |
| Plugin not installed locally | `SessionManagerPlugin is not found` | install the plugin | [AWS reference](16-aws-cloud.md) section 7 |
| Agent stopped or old | `ConnectionLost` | `sudo snap services amazon-ssm-agent` | this topic |
| IAM denies StartSession for that instance | `AccessDeniedException` | read the message; tag-based conditions | section 2 |

**Why it matters for troubleshooting.** Session Manager removes port 22 from your attack surface and
gives you an audit trail of who ran what. When it fails, the three-condition checklist finds the
reason in minutes, and port forwarding lets you test a backend from your laptop without touching a
security group.

**Next step:** the storage service every other service writes to: S3.

---

## 5. S3, encryption and KMS

> 📚 **Study path:** 1) KodeKloud: *Crash Course: AWS Basics* — the S3 part, free ([link](https://kodekloud.com/courses/crash-course-aws-basics)) · 2) Note: this section, plus the secrets and encryption concepts in [Security & DevSecOps](37-learn-security-devsecops.md) · 3) KodeKloud: *AWS Certified CloudOps Engineer - Associate* — the Security domain (encryption, KMS, S3 access) ([link](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 4) Practice: an S3 task from [100 Days of Cloud](https://kodekloud.com/100-days-of-cloud), then the three labs below; ship your on-prem backups to a versioned bucket as the capstone

Tags: [L0 · Fresher] for buckets and classes, [L1 · Junior] for versioning, lifecycle and Block Public Access, [L2 · Mid] for policy debugging, [L3 · Senior] for KMS key design.

S3 is where backups, CI artifacts, Terraform state, logs and static sites end up. It is also where
the most famous cloud data leaks happened. This section covers how S3 stores and ages data, who can
read it, and how encryption with KMS adds a second permission check that catches people out.

### S3 storage classes and lifecycle

**Level:** [L0 · Fresher] → [L1 · Junior] · about 45 minutes · lab cost: cents

**Concept.** S3 is **object storage**: you PUT and GET whole objects by key in a bucket, over
HTTPS. There are no directories (a `/` in the key is just a character), no in-place edits and no
file locks, so it is a backup target and artifact store, not a filesystem to mount under a
database. Bucket names are global; the data lives in one region. Standard storage is designed for
11 nines of durability across at least three AZs.

| Class | Use for | Minimum storage duration | Retrieval |
|---|---|---|---|
| Standard | Hot data, artifacts, static sites | none | immediate |
| Intelligent-Tiering | Unknown or changing access patterns | none (small monitoring fee per object) | immediate for frequent and infrequent tiers |
| Standard-IA / One Zone-IA | Backups read rarely; One Zone loses data if its AZ is lost | 30 days | immediate, per-GB retrieval fee |
| Glacier Instant Retrieval | Archives read a few times a year | 90 days | immediate, higher retrieval fee |
| Glacier Flexible Retrieval | Archives | 90 days | minutes to hours (restore request) |
| Glacier Deep Archive | Compliance copies | 180 days | up to 12–48 hours |

**Versioning** keeps every version of every key. A delete only adds a **delete marker**, so an
accidental `aws s3 rm` or a ransomware overwrite is reversible. Once enabled, versioning can only
be suspended, never removed. **Lifecycle rules** then age data automatically: transition to a
cheaper class after N days, expire current versions, expire **noncurrent** versions after N days
(otherwise versioned buckets grow forever), and abort incomplete multipart uploads.

**Key terms**

| Term | Meaning |
|---|---|
| Bucket / key / object | Container / full name of an object / the data plus metadata |
| Prefix | The leading part of a key, used like a folder in policies and lifecycle rules |
| Versioning | Keeps all versions; deletes become delete markers |
| Lifecycle rule | Automatic transition or expiration by prefix, tag and age |
| Multipart upload | Large uploads in parts; unfinished parts are billed until aborted |
| Object Lock | WORM retention (governance or compliance mode) for backups that must not be deleted |

**See it on a real system**

```bash
aws s3api get-bucket-versioning --bucket lab-backups-123456789012
aws s3api get-bucket-lifecycle-configuration --bucket lab-backups-123456789012 \
  --query 'Rules[].[ID,Status,Transitions[0].StorageClass,Transitions[0].Days,NoncurrentVersionExpiration.NoncurrentDays]' --output table
aws s3api list-object-versions --bucket lab-backups-123456789012 --prefix pg/daily.sql.gz \
  --query '{versions:Versions[].[VersionId,IsLatest,LastModified,Size],markers:DeleteMarkers[].[VersionId,IsLatest]}'
```

```
{
    "Status": "Enabled"
}
---------------------------------------------------------------
|               GetBucketLifecycleConfiguration               |
+-------------------+-----------+---------------+------+------+
|  backups-tiering  |  Enabled  |  STANDARD_IA  |  30  |  90  |
+-------------------+-----------+---------------+------+------+
{
    "versions": [
        [ "3HL4kqtJlcpXroDTDmJ.rmSpXd3dIbrHY", false, "2026-10-02T01:00:12+00:00", 52428800 ]
    ],
    "markers": [
        [ "UIORUnfnd89493jJFJ.qwe3h3JKLiuuX", true ]
    ]
}
```

→ Versioning is on, backups move to Standard-IA after 30 days and old versions expire after 90.
The `list-object-versions` output shows the classic accident: the **latest** "version" of the
backup is a delete marker, so `aws s3 ls` no longer shows the file, but yesterday's 50 MB version is
still there and can be restored.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create `lab-backups-ACCOUNT_ID`, enable versioning, and add a lifecycle rule
(Standard-IA after 30 days, noncurrent expiration after 90 days, abort multipart uploads after
7 days). Upload a test file twice with different content.

**Step 2 — Break it.** Delete it: `aws s3 rm s3://lab-backups-ACCOUNT_ID/pg/daily.sql.gz`.
`aws s3 ls` shows nothing.

**Step 3 — Fix it.** Remove the delete marker, which "undeletes" the object:

```bash
aws s3api delete-object --bucket lab-backups-123456789012 --key pg/daily.sql.gz \
  --version-id UIORUnfnd89493jJFJ.qwe3h3JKLiuuX
aws s3 ls s3://lab-backups-123456789012/pg/
```

```
{
    "DeleteMarker": true,
    "VersionId": "UIORUnfnd89493jJFJ.qwe3h3JKLiuuX"
}
2026-10-02 01:00:12   52428800 daily.sql.gz
```

> ⚠️ `delete-object` **with a version ID** permanently deletes that version; only on a delete marker
> is it an undelete. Safer first: run `list-object-versions`, copy the exact delete-marker ID, and
> check `IsLatest` before you run it. For backups, Object Lock stops versions being deleted early:
> governance mode can still be bypassed by principals with `s3:BypassGovernanceRetention`, while
> compliance mode stops everyone, including the root user, until the retention date.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Accidental delete or overwrite | Object missing or wrong | `aws s3api list-object-versions --prefix KEY` | this topic |
| Versioned bucket grows forever | Storage line keeps rising after deletes | lifecycle `NoncurrentVersionExpiration` | section 12 |
| Small objects moved to IA | Bill higher than Standard (minimum 128 KB billable size, 30-day minimum) | Storage Lens or Cost Explorer by storage class | section 12 |
| Restore from Glacier "fails" | `InvalidObjectState` on GET | `aws s3api restore-object` first, then wait | this topic |
| Using S3 as a database filesystem | Corrupt or slow app behaviour | redesign: EBS or EFS for files, S3 for objects | [Learn: Databases](38-learn-databases-ops.md) |

**Why it matters for troubleshooting.** "The backup is gone" is usually a delete marker, and "the
bucket bill doubled" is usually noncurrent versions or incomplete uploads. Both are visible with one
read-only command if you know where to look.

**Next step:** who may read and write those objects.

### S3 access control

**Level:** [L1 · Junior] → [L2 · Mid] · about 50 minutes · lab cost: free

**Concept.** Three mechanisms decide access to a bucket, and the modern defaults simplify them:

- **Bucket policy**: a resource policy on the bucket (section 2 rules apply). This is where you
  grant other accounts or roles, require TLS, or require a VPC endpoint.
- **ACLs**: the legacy per-object grant system. Since April 2023 new buckets use **Object
  Ownership: Bucket owner enforced**, which disables ACLs entirely. Leave them disabled; if an old
  tool needs ACLs, that is a finding, not a requirement.
- **Block Public Access** (BPA): four switches at account and bucket level that override any policy
  or ACL that would make data public. On by default for new buckets. Turn it on at the **account**
  level and keep public websites behind CloudFront instead.

A bucket policy that enforces TLS and lets only the backup role write:

```
{
  "Version": "2012-10-17",
  "Statement": [
    { "Sid": "DenyInsecureTransport", "Effect": "Deny", "Principal": "*", "Action": "s3:*",
      "Resource": [ "arn:aws:s3:::lab-backups-123456789012", "arn:aws:s3:::lab-backups-123456789012/*" ],
      "Condition": { "Bool": { "aws:SecureTransport": "false" } } },
    { "Sid": "BackupRoleWrite", "Effect": "Allow",
      "Principal": { "AWS": "arn:aws:iam::123456789012:role/onprem-backup-role" },
      "Action": [ "s3:PutObject", "s3:AbortMultipartUpload" ],
      "Resource": "arn:aws:s3:::lab-backups-123456789012/pg/*" }
  ]
}
```

**Key terms**

| Term | Meaning |
|---|---|
| Bucket policy | Resource-based JSON policy on a bucket |
| Object Ownership | `BucketOwnerEnforced` disables ACLs and makes the bucket owner own every object |
| Block Public Access | Four settings that override public policies and ACLs |
| Presigned URL | Time-limited URL signed with your credentials for one GET or PUT |
| Access Analyzer for S3 | Lists buckets shared outside your account or publicly |

**See it on a real system**

```bash
aws s3control get-public-access-block --account-id 123456789012
aws s3api get-bucket-ownership-controls --bucket lab-backups-123456789012 \
  --query 'OwnershipControls.Rules[0].ObjectOwnership' --output text
aws s3api get-bucket-policy-status --bucket lab-backups-123456789012
aws s3 presign s3://lab-backups-123456789012/pg/daily.sql.gz --expires-in 600
```

```
{
    "PublicAccessBlockConfiguration": {
        "BlockPublicAcls": true,
        "IgnorePublicAcls": true,
        "BlockPublicPolicy": true,
        "RestrictPublicBuckets": true
    }
}
BucketOwnerEnforced
{
    "PolicyStatus": {
        "IsPublic": false
    }
}
https://lab-backups-123456789012.s3.ap-south-1.amazonaws.com/pg/daily.sql.gz?X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=...&X-Amz-Expires=600&X-Amz-Signature=...
```

→ Account-level BPA is fully on, ACLs are disabled, and AWS evaluates the bucket policy as not
public. A presigned URL is the safe way to hand one object to someone for ten minutes, without
changing any policy. It carries your permissions, so it fails if you lose access.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Apply the bucket policy above to your lab bucket (with a role that exists).
From the on-prem-style lab instance, upload with the role:
`aws s3 cp /tmp/test.gz s3://lab-backups-ACCOUNT_ID/pg/test.gz`.

**Step 2 — Break it.** Upload to a different prefix (`s3://.../etc/test.gz`), then try plain HTTP
with `aws s3 ls s3://lab-backups-ACCOUNT_ID --endpoint-url http://s3.ap-south-1.amazonaws.com`:

```
upload failed: /tmp/test.gz to s3://lab-backups-123456789012/etc/test.gz An error occurred (AccessDenied) when calling the PutObject operation: User: arn:aws:sts::123456789012:assumed-role/onprem-backup-role/host01 is not authorized to perform: s3:PutObject on resource: "arn:aws:s3:::lab-backups-123456789012/etc/test.gz" because no identity-based policy allows the s3:PutObject action
An error occurred (AccessDenied) when calling the ListObjectsV2 operation: User: arn:aws:sts::123456789012:assumed-role/onprem-backup-role/host01 is not authorized to perform: s3:ListBucket on resource: "arn:aws:s3:::lab-backups-123456789012" with an explicit deny in a resource-based policy
```

**Step 3 — Fix it.** Read each message with the section 2 method: the first is a prefix outside the
grant (working as designed), the second is the explicit TLS Deny in the bucket policy (also by
design). Then try to make the bucket public with a `"Principal": "*"` GetObject policy and watch
BPA refuse it with `AccessDenied ... public policies are blocked by the BlockPublicPolicy block
public access setting`. That refusal is the guardrail doing its job.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Bucket vs object ARN confusion | ListBucket works, GetObject denied (or the reverse) | read policy `Resource` lines | section 2 |
| Explicit Deny in bucket policy | `with an explicit deny in a resource-based policy` | `aws s3api get-bucket-policy` | section 2 |
| Public website needed, BPA blocks | Policy save refused | use CloudFront with origin access control | section 6 |
| Cross-account upload, owner cannot read | Old bucket with ACLs enabled | set `BucketOwnerEnforced` | this topic |
| Data exposed publicly | Access Analyzer or Security Hub finding | `aws s3api get-bucket-policy-status` | section 13 |

**Why it matters for troubleshooting.** S3 AccessDenied has more possible layers than most: identity
policy, bucket policy, BPA, endpoint policy and KMS. The error text names the layer; your job is to
read it instead of widening policies.

**Next step:** the KMS layer, which is the one people forget.

### Encryption and KMS

**Level:** [L2 · Mid] → [L3 · Senior] · about 50 minutes · lab cost: cents (a customer managed key is about USD 1 a month)

**Concept.** Encryption at rest on AWS is mostly a checkbox; key **access** is the real design
decision.

- **S3** encrypts every new object by default with **SSE-S3** (AWS-owned keys) since January 2023.
  **SSE-KMS** uses a KMS key instead, which adds an audit trail (every decrypt is a CloudTrail
  event) and a **second permission**: readers need `kms:Decrypt` on the key, writers need
  `kms:GenerateDataKey`. Enable **S3 Bucket Keys** with SSE-KMS to cut KMS request costs.
- **EBS** encryption uses KMS too. Turn on **EBS encryption by default** per region so nobody
  creates an unencrypted volume or snapshot by accident.
- **KMS keys** are either **AWS managed** (`aws/s3`, `aws/ebs`: free, cannot be shared across
  accounts, key policy fixed) or **customer managed** (about USD 1 a month plus requests: your key
  policy, cross-account sharing, rotation settings, deletion control).
- Every KMS key has a **key policy**, and unlike most resources, IAM policies alone do not grant
  access unless the key policy delegates to the account (the default key policy does).
- Deleting a key is **scheduled** (7–30 days) and irreversible after that: every object and volume
  encrypted under it becomes unreadable. Disable first and watch for errors.

```
 GetObject on an SSE-KMS object
   app ──▶ S3: s3:GetObject allowed?  (identity policy, bucket policy, BPA)
                └──▶ S3 asks KMS to decrypt the data key on your behalf
                       KMS: kms:Decrypt allowed for this caller? (key policy + identity policy)
                       └── no → AccessDenied from S3, mentioning kms:Decrypt
```

**Key terms**

| Term | Meaning |
|---|---|
| SSE-S3 / SSE-KMS | Server-side encryption with S3-owned keys / with a KMS key you choose |
| Envelope encryption | Data encrypted with a data key, which is itself encrypted by the KMS key |
| Key policy | Resource policy on a KMS key; required for any access |
| Grant | Temporary, delegated KMS permission used by services such as EBS |
| Key rotation | Automatic yearly rotation of key material by default when enabled; old material kept for decrypting |
| Pending deletion | 7–30-day waiting state before a key is destroyed |

**See it on a real system**

```bash
aws s3api get-bucket-encryption --bucket lab-backups-123456789012 \
  --query 'ServerSideEncryptionConfiguration.Rules[0]'
aws ec2 get-ebs-encryption-by-default
aws kms describe-key --key-id alias/lab-backups \
  --query 'KeyMetadata.[KeyId,KeyManager,KeyState,KeySpec]' --output text
aws kms get-key-rotation-status --key-id alias/lab-backups
```

```
{
    "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "aws:kms",
        "KMSMasterKeyID": "arn:aws:kms:ap-south-1:123456789012:alias/lab-backups"
    },
    "BucketKeyEnabled": true
}
{
    "EbsEncryptionByDefault": true
}
1234abcd-12ab-34cd-56ef-1234567890ab	CUSTOMER	Enabled	SYMMETRIC_DEFAULT
{
    "KeyRotationEnabled": true,
    "KeyId": "1234abcd-12ab-34cd-56ef-1234567890ab",
    "RotationPeriodInDays": 365
}
```

→ The bucket encrypts new objects with a customer managed key and uses a bucket key, EBS encryption
by default is on in this region, and the key rotates yearly. Rotation keeps old key material for
decryption, so it never breaks existing data.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create a customer managed key with alias `lab-backups` whose key policy
gives your admin role full control and `onprem-backup-role` only `kms:GenerateDataKey` (enough for
single-part SSE-KMS uploads; see the multipart note in Step 3). Set it as the bucket's default
encryption with a bucket key, and give the role `s3:GetObject` on `pg/*` in its identity policy so
that S3 itself allows the read and only KMS can refuse it.

**Step 2 — Break it.** Upload the small test file with the backup role (works), then try to read
the object back with the same role:

```
download failed: s3://lab-backups-123456789012/pg/test.gz to ./test.gz An error occurred (AccessDenied) when calling the GetObject operation: User: arn:aws:sts::123456789012:assumed-role/onprem-backup-role/host01 is not authorized to perform: kms:Decrypt on resource: arn:aws:kms:ap-south-1:123456789012:key/1234abcd-12ab-34cd-56ef-1234567890ab because no identity-based policy allows the kms:Decrypt action
```

**Step 3 — Fix it.** Decide whether it should read at all. A write-only backup role that cannot
read the backups is a good ransomware defence; the **restore** role gets `kms:Decrypt` instead.
One catch: multipart uploads with SSE-KMS (which `aws s3 cp` uses automatically above 8 MB, so for
every real dump) need `kms:Decrypt` as well as `kms:GenerateDataKey`. For real backups, give the
backup role both KMS actions and keep it write-only at the S3 layer instead: no `s3:GetObject` in
its policy, or an explicit Deny on `s3:GetObject` for it in the bucket policy. Add a separate
restore role and test a restore. Then practise the safe key retirement path:
`aws kms disable-key`, watch CloudTrail for failed `Decrypt` calls for a week, and only then
`aws kms schedule-key-deletion --pending-window-in-days 30` in the lab.

> ⚠️ A key that finishes its deletion window takes every object, snapshot and volume encrypted
> under it with it, and AWS cannot recover them. Safer first: `disable-key` (reversible with
> `enable-key`), check CloudTrail for usage, use the full 30-day window, and alarm on
> `ScheduleKeyDeletion` events (section 9).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Missing `kms:Decrypt` or `kms:GenerateDataKey` | AccessDenied from S3, EBS attach or RDS mentioning KMS; large uploads fail while small ones work (multipart needs `kms:Decrypt`) | `aws kms get-key-policy --key-id KEY_ID --policy-name default` | section 2 |
| Cross-account access with an AWS managed key | Other account cannot decrypt shared snapshot or object | use a customer managed key and share it | this topic |
| Key disabled or pending deletion | `KMS.DisabledException` from S3, `KMSInvalidStateException` from KMS calls; instances with encrypted volumes stop at launch with `Client.InternalError` | `aws kms describe-key` | this topic |
| KMS request costs | Big KMS line from SSE-KMS on chatty buckets | enable Bucket Keys | section 12 |
| Unencrypted volumes found in audit | Compliance finding | `aws ec2 get-ebs-encryption-by-default` | section 13 |

**Why it matters for troubleshooting.** KMS is the hidden second lock. Whenever an AccessDenied
mentions `kms:` or an encrypted volume will not attach, stop editing S3 or EC2 policies and read the
key policy.

**Next step:** putting your Apache apps behind a managed load balancer and DNS.

---

## 6. Load balancing and Route 53

> 📚 **Study path:** 1) Note: [Learn: Web servers & proxies](29-learn-webservers-proxies.md) first, because an ALB is a reverse proxy you already understand from Apache and Traefik · 2) KodeKloud: *AWS Networking Fundamentals* — the load balancer and Route 53/DNS-in-VPC lessons ([link](https://kodekloud.com/courses/aws-networking-fundamentals)) · 3) KodeKloud: *Demystifying DNS* — DNS as a System (resolvers, TTL), only if records and TTLs still feel shaky ([link](https://kodekloud.com/courses/demystifying-dns)) · 4) Note: [AWS reference](16-aws-cloud.md) section 6 and [Site down](25-playbook-site-down.md) · 5) Practice: Apache-on-81 behind an ALB in the [AWS Playground](https://kodekloud.com/cloud-playgrounds/aws) or your sandbox, then the 502/503 drill below under a 20-minute timer

Tags: [L1 · Junior] for ALB, target groups and records, [L2 · Mid] for reason codes, 5xx diagnosis, routing policies and the drill.

On-prem, Traefik owns 80/443 and routes by host name to Apache on 81/444 and to Dokploy apps. On
AWS, an **ALB** does that job, **ACM** supplies the certificates, and **Route 53** points names at
it. The concepts carry over one to one; the evidence (reason codes, metrics, access logs) is new.

```
 On-prem (module 35)                          AWS equivalent
 client ─▶ Traefik :443 (Let's Encrypt)        client ─▶ Route 53 alias ─▶ ALB :443 (ACM cert)
            ├─ Host(app1) ─▶ Apache :81                     ├─ host app1.example.com ─▶ TG "apache" → EC2 :81
            ├─ Host(app2) ─▶ Dokploy service               ├─ host app2.example.com ─▶ TG "app2" → ECS tasks (ip)
            └─ health: none by default                      └─ health: per target group, with reason codes
```

### ALB vs NLB and target groups

**Level:** [L1 · Junior] · about 50 minutes · lab cost: cents (an ALB is about USD 0.03 per hour)

**Concept.** Elastic Load Balancing has two main types you will use:

| | Application Load Balancer (ALB) | Network Load Balancer (NLB) |
|---|---|---|
| Layer | 7: HTTP, HTTPS, gRPC, WebSocket | 4: TCP, UDP, TLS |
| Routing | Host, path, header, method, query string rules | Port only |
| TLS | Terminates TLS with ACM certificates; SNI for many names | TLS termination or pure TCP passthrough |
| Client IP at target | In `X-Forwarded-For` (the TCP source is the ALB) | Preserved for instance targets |
| Addresses | DNS name only; node IPs change | One static IP per AZ, EIPs possible |
| Security groups | Yes | Optional (must be chosen at creation) |
| Cross-zone balancing | On | Off by default (cross-AZ data charges if on) |
| On-prem analogy | Traefik HTTP routers, Apache `ProxyPass` | HAProxy in TCP mode, Traefik TCP routers with `HostSNI` |

A **target group** is the backend pool: a protocol and port, a **target type** (`instance`, `ip`
for containers and on-prem servers over VPN, or `lambda`), the targets, and the **health check**.
A **listener** (port 443) has **rules** that forward to target groups. The load balancer itself
lives in at least two public subnets (internet-facing) or private subnets (internal).

Because the ALB terminates TCP, Apache logs the ALB node's private IP as the client. Use
`mod_remoteip` with `RemoteIPHeader X-Forwarded-For` and `RemoteIPInternalProxy 10.20.0.0/16`, the
same fix you apply behind Traefik.

**Key terms**

| Term | Meaning |
|---|---|
| Listener / rule | Port and protocol the LB accepts / condition-and-action pairs evaluated by priority |
| Target group | Backend pool with its own protocol, port and health check |
| Target type | `instance`, `ip` or `lambda` |
| ACM | AWS Certificate Manager: free public certificates for ALB, NLB and CloudFront, auto-renewed (exportable certificates for use elsewhere are a paid option) |
| Deregistration delay | Draining time before a removed target stops receiving requests (300 s default) |
| Idle timeout | Seconds the ALB keeps an idle connection open (60 s default) |

**See it on a real system**

```bash
aws elbv2 describe-load-balancers --names lab-alb \
  --query 'LoadBalancers[].[Type,Scheme,DNSName,State.Code]' --output table
aws elbv2 describe-listeners --load-balancer-arn LB_ARN \
  --query 'Listeners[].[Port,Protocol,Certificates[0].CertificateArn,DefaultActions[0].Type]' --output table
aws elbv2 describe-target-groups --load-balancer-arn LB_ARN \
  --query 'TargetGroups[].[TargetGroupName,Protocol,Port,TargetType,HealthCheckPath,Matcher.HttpCode]' --output table
```

```
----------------------------------------------------------------------------------------------------
|                                      DescribeLoadBalancers                                       |
+---------------+-------------------+---------------------------------------------------+----------+
|  application  |  internet-facing  |  lab-alb-1234567890.ap-south-1.elb.amazonaws.com  |  active  |
+---------------+-------------------+---------------------------------------------------+----------+
-------------------------------------------------------------------------------------------------
|                                       DescribeListeners                                       |
+-------+---------+----------------------------------------------------------------+------------+
|  80   |  HTTP   |  None                                                          |  redirect  |
|  443  |  HTTPS  |  arn:aws:acm:ap-south-1:123456789012:certificate/0a1b2c3d-...  |  forward   |
+-------+---------+----------------------------------------------------------------+------------+
--------------------------------------------------------------------
|                       DescribeTargetGroups                       |
+----------+--------+--------+------------+------------+-----------+
|  apache  |  HTTP  |  81    |  instance  |  /health   |  200      |
|  app2    |  HTTP  |  3000  |  ip        |  /healthz  |  200-299  |
+----------+--------+--------+------------+------------+-----------+
```

→ Port 80 redirects to HTTPS, 443 terminates TLS with an ACM certificate and forwards. Two target
groups mirror your on-prem layout: Apache on 81 by instance, and a container app by IP. The
health check path and matcher are the most important two fields on the page.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Request an ACM certificate for `app1.example.com` in a domain you control
(DNS validation), create target group `apache` (HTTP 81, health check `/health`, matcher 200),
register the private Apache instance, and create an internet-facing ALB in `public-a` and
`public-b` with SG `alb-sg` (443 and 80 from 0.0.0.0/0). Listener 443 forwards to `apache`; 80
redirects to 443. On the instance, allow tcp 81 **from `alb-sg`** and add
`Alias /health /var/www/health.txt` (or a file at `/var/www/html/health`) so the path returns 200.

**Step 2 — Break it.** Add a second host-based rule for `app2.example.com` pointing to a target
group with no targets, and request it:

```
HTTP/2 503
server: awselb/2.0
```

**Step 3 — Fix it.** Register a target or remove the rule. Note the `server: awselb/2.0` header:
it tells you the ALB generated that response, not Apache. Tear the ALB down after the lab.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| No targets or none registered in that AZ | `503` with `server: awselb/2.0` | `aws elbv2 describe-target-health` | the drill below |
| Target SG does not allow the ALB SG | All targets `unhealthy`, reason `Target.Timeout` | `aws ec2 describe-security-group-rules` | section 3 |
| Client IP missing in Apache logs | Every request from 10.20.x.x | check `mod_remoteip` | [Learn: Web servers & proxies](29-learn-webservers-proxies.md) |
| NLB clients time out after adding SGs | NLB SG or target SG missing rules | NLB and target SGs | section 3 |
| Certificate in the wrong region | ACM cert not offered for the listener | ACM certs are regional (CloudFront uses us-east-1) | this topic |

**Why it matters for troubleshooting.** A load balancer adds a hop that can produce its own errors.
The first question in every LB incident is "did the LB generate this response, or the target?",
and the `server` header plus the ELB vs Target metrics answer it.

**Next step:** health checks and the meaning of each 5xx.

### Health checks and ALB errors

**Level:** [L2 · Mid] · about 50 minutes · lab cost: cents

**Concept.** Each target group sends health checks from **every LB node** to every target. A target
becomes `healthy` after `HealthyThresholdCount` consecutive successes (default 5 for ALB) and
`unhealthy` after `UnhealthyThresholdCount` failures (default 2), checked every `Interval` (30 s)
with a `Timeout` (5 s). When a target is unhealthy, `describe-target-health` returns a **reason
code**. They are your best clue:

| Reason code | Meaning | Usual cause |
|---|---|---|
| `Elb.InitialHealthChecking` | Still running the first checks | Wait one threshold × interval |
| `Target.ResponseCodeMismatch` | Got an HTTP code the matcher does not accept | Path returns 301 (HTTP to HTTPS redirect), 302 to a login page, 404 |
| `Target.Timeout` | No response within the timeout | SG blocks the LB, wrong port, app hung |
| `Target.FailedHealthChecks` | Connection failed or the target closed it | Nothing listening, connection refused |
| `Target.NotRegistered` | Not in the target group | Deployment never registered it |
| `Target.NotInUse` | Target group not used by an LB, or target's AZ not enabled on the LB | Listener rule or LB subnets missing |
| `Target.DeregistrationInProgress` | Draining | Normal during deploys |
| `Target.InvalidState` | Instance stopped or terminated | Check EC2 |

Two ALB behaviours surprise people. **Fail-open**: if every target in a group is unhealthy, the
ALB routes to all of them anyway, so a broken health check can hide behind "the site still works".
And the ALB's own error codes each have a short list of causes:

| Code from the ALB | Meaning | Most common causes |
|---|---|---|
| 502 Bad Gateway | The target's response was unusable | Target reset or closed the connection; target keep-alive shorter than ALB idle timeout; malformed headers; TLS handshake to an HTTPS target failed |
| 503 Service Unavailable | No target to send to | No registered targets; rule points to an empty group |
| 504 Gateway Timeout | No response in time | Could not connect within 10 s; target slower than the idle timeout |
| 460 | Client closed the connection first | Client timeout shorter than target response time |
| 5xx with a target code | Target's own error passed through | Look in Apache or app logs, not at the ALB |

**Key terms**

| Term | Meaning |
|---|---|
| Reason code | Machine-readable cause in `TargetHealth.Reason` |
| `HTTPCode_ELB_5XX_Count` | 5xx generated by the load balancer itself |
| `HTTPCode_Target_5XX_Count` | 5xx returned by your targets and passed through |
| `UnHealthyHostCount` | Unhealthy targets per target group and AZ |
| Access logs | Per-request logs to S3 with ELB and target status codes and timings |

**See it on a real system**

```bash
aws elbv2 describe-target-health --target-group-arn TG_ARN \
  --query 'TargetHealthDescriptions[].[Target.Id,Target.Port,TargetHealth.State,TargetHealth.Reason,TargetHealth.Description]' \
  --output table
aws elbv2 describe-target-group-attributes --target-group-arn TG_ARN \
  --query "Attributes[?Key=='deregistration_delay.timeout_seconds']"
aws elbv2 describe-load-balancer-attributes --load-balancer-arn LB_ARN \
  --query "Attributes[?Key=='idle_timeout.timeout_seconds' || Key=='access_logs.s3.enabled']" --output text
```

```
-------------------------------------------------------------------------------------------------------------------------------
|                                                     DescribeTargetHealth                                                    |
+-----------------------+------+-------------+-------------------------------+------------------------------------------------+
|  i-0a1b2c3d4e5f60011  |  81  |  unhealthy  |  Target.ResponseCodeMismatch  |  Health checks failed with these codes: [301]  |
|  i-0a1b2c3d4e5f60012  |  81  |  unhealthy  |  Target.ResponseCodeMismatch  |  Health checks failed with these codes: [301]  |
+-----------------------+------+-------------+-------------------------------+------------------------------------------------+
[
    {
        "Key": "deregistration_delay.timeout_seconds",
        "Value": "300"
    }
]
idle_timeout.timeout_seconds	60
access_logs.s3.enabled	false
```

→ Both targets answer the health check with **301**: someone added an HTTP-to-HTTPS redirect in
the Apache vhost on 81, so the health check path redirects. On-prem behind Traefik you would
never notice; here the ALB marks every target unhealthy and fails open. Fix the health path (exempt
`/health` from the redirect) rather than widening the matcher to 301. Access logs are off, which
you will want for the next incident.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Use the ALB from the previous topic. Enable access logs to a log bucket
(the bucket policy must allow the regional ELB log delivery principal; the console sets this up).

**Step 2 — Break it, three ways.** One at a time, then read `describe-target-health` after a
minute: (a) add `Redirect permanent / https://app1.example.com/` to the vhost on 81; (b) remove
the SG rule that lets `alb-sg` reach 81; (c) `sudo systemctl stop apache2`. You should see
`ResponseCodeMismatch [301]`, `Target.Timeout` and `Target.FailedHealthChecks` respectively.

**Step 3 — Fix it.** Reverse each break and watch the target pass through `initial` to `healthy`
(about 5 × 30 s with defaults; lower the interval to 10 s and the healthy threshold to 2 for
faster labs). Then compare the ALB's `HTTPCode_ELB_5XX_Count` and `HTTPCode_Target_5XX_Count`
metrics for the lab period.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Health path redirects or requires login | `ResponseCodeMismatch` with 301/302/401 | `curl -sI http://TARGET_IP:81/health` from inside the VPC | this topic |
| SG blocks LB nodes | `Target.Timeout` on all targets | target SG rules | section 3 |
| Intermittent 502s under light load | Target keep-alive shorter than 60 s idle timeout | Apache `KeepAliveTimeout` | the drill below |
| 504 on slow endpoints | Requests longer than 60 s | ALB idle timeout vs app timing | the drill below |
| Deploys drop requests | Deregistration delay 0 or app exits before draining | target group attributes | [Deployment patterns](35-deployment-patterns.md) |

**Why it matters for troubleshooting.** The reason code turns "targets unhealthy" into a specific
layer: HTTP (mismatch), network (timeout) or process (failed). The ELB vs Target 5xx split tells you
whether to read ALB settings or Apache logs.

**Next step:** the DNS name in front of all this.

### Route 53 records and routing

**Level:** [L1 · Junior] → [L2 · Mid] · about 50 minutes · lab cost: cents (USD 0.50 per hosted zone per month)

**Concept.** Route 53 is AWS's authoritative DNS (plus domain registration and health checks).
A **public hosted zone** answers for `example.com` on the internet once the registrar's NS records
point at the zone's four `awsdns` name servers. A **private hosted zone** answers only inside the
VPCs you associate it with, through the Amazon resolver at VPC base + 2.

Record types are the ones you know (A, AAAA, CNAME, MX, TXT, CAA, NS, SOA) plus the AWS **alias**
record: an A or AAAA record that points at an AWS resource (ALB, CloudFront, S3 website, another
record) and follows its changing IPs. Alias records work at the **zone apex** (`example.com`), where
a CNAME is not allowed, and queries to them are free.

**Routing policies** decide which answer each query gets:

| Policy | Answers | Use it for |
|---|---|---|
| Simple | The record's values | One endpoint |
| Weighted | Records in proportion to weights | Canary 90/10, blue/green cutover ([Deployment patterns](35-deployment-patterns.md)) |
| Failover | Primary while healthy, else secondary | Active-passive DR, maintenance page |
| Latency | The region with the lowest latency for the resolver | Multi-region apps |
| Geolocation / geoproximity | By user location | Compliance, regional content |
| Multivalue answer | Up to 8 healthy records | Simple client-side load spreading |
| IP-based | By the resolver's source CIDR | Routing known networks |

**Health checks** probe an endpoint from many locations and mark it healthy or not; routing
policies use them to drop failed answers. Remember **TTL**: lowering a TTL only helps after the old
TTL has expired in every resolver, so lower it a day before a migration, exactly as you would with
BIND.

**Key terms**

| Term | Meaning |
|---|---|
| Hosted zone | Container of records for one domain; public or private |
| Delegation | Registrar or parent zone NS records pointing at the zone's name servers |
| Alias record | Route 53 extension pointing a name at an AWS resource; allowed at the apex |
| Health check | Periodic probe from Route 53 checkers; can drive failover |
| Evaluate target health | Alias option to inherit the health of the ALB's targets |

**See it on a real system**

```bash
aws route53 list-hosted-zones-by-name --dns-name example.com \
  --query 'HostedZones[].[Id,Name,Config.PrivateZone]' --output text
aws route53 list-resource-record-sets --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --query "ResourceRecordSets[?Name=='app1.example.com.']"
dig +short NS example.com
dig +short app1.example.com @ns-1234.awsdns-26.org
aws route53 test-dns-answer --hosted-zone-id Z0123456789ABCDEFGHIJ \
  --record-name app1.example.com --record-type A --query '[ResponseCode,RecordData]' --output text
```

```
/hostedzone/Z0123456789ABCDEFGHIJ	example.com.	False
/hostedzone/Z9876543210ZYXWVUTSRQ	example.com.	True
[
    {
        "Name": "app1.example.com.",
        "Type": "A",
        "AliasTarget": {
            "HostedZoneId": "ZP97RAFLXTNZK",
            "DNSName": "dualstack.lab-alb-1234567890.ap-south-1.elb.amazonaws.com.",
            "EvaluateTargetHealth": true
        }
    }
]
ns-1234.awsdns-26.org.
ns-567.awsdns-06.net.
ns-89.awsdns-11.com.
ns-1890.awsdns-44.co.uk.
203.0.113.61
198.51.100.62
NOERROR	203.0.113.61	198.51.100.62
```

→ There are two zones named `example.com.`: a public one and a private one (split-horizon). The
record is an alias to the ALB with target health evaluation. The public delegation matches the
zone's name servers, the authoritative answer returns two ALB node IPs, and `test-dns-answer`
shows what Route 53 itself would answer. When this works but users still get the old IP, the
problem is caching (TTL) or a different resolver, not Route 53.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** In a domain you control, create `app1.example.com` as an alias to your lab
ALB. Then create a failover pair: primary = the ALB alias with evaluate target health, secondary =
an S3 static website or CloudFront distribution serving a maintenance page.

**Step 2 — Break it.** Stop Apache on every target. Within a few minutes the ALB has no healthy
targets, Route 53 marks the primary unhealthy, and `dig` returns the secondary. Separately, delete
and recreate the public hosted zone, and notice that the new zone has **different** name servers
from the ones at your registrar: resolution fails with `SERVFAIL` or old answers.

**Step 3 — Fix it.** Start Apache and watch the primary return. For the recreated zone, update the
registrar's NS records to the new four servers (and wait for the parent's NS TTL). Write the
lesson down: deleting a public hosted zone is a DNS outage, never a cleanup.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Registrar NS does not match the zone | `SERVFAIL`, or answers from an old provider | `dig +short NS example.com` vs the zone's NS record | [DNS](08-dns.md) |
| Private zone not associated with the VPC | Instances get `NXDOMAIN` for internal names | `aws route53 get-hosted-zone --id ZONE_ID --query VPCs` | section 11 |
| High TTL before a migration | Some users hit the old server for hours | `dig app1.example.com` (TTL column) | this topic |
| CNAME at the apex | Record creation refused | use an alias record | this topic |
| Health check cannot reach the endpoint | Failover flaps to secondary | `aws route53 get-health-check-status --health-check-id ID` | this topic |

**Why it matters for troubleshooting.** DNS is the first layer of every "site down" walk. Route 53
adds two AWS-specific failure modes (delegation to the wrong zone, private zone association) on
top of the classic TTL and resolver problems from [DNS](08-dns.md).

**Next step:** the timed drill that puts the ALB topics together.

### Drill: ALB returns 502 or 503

**Level:** [L2 · Mid] · 20-minute timer · lab cost: cents

The scenario: `https://app1.example.com` sits behind the lab ALB, which forwards to Apache on port
81 on two private instances. Since this morning users report errors: mostly occasional `502 Bad
Gateway`, and for ten minutes after the 09:00 deploy a solid `503`. This is the AWS twin of your
Traefik 502 drill in [Site down](25-playbook-site-down.md).

**Step 1 — Find out who generates the error.**

**Goal:** separate errors produced by the ALB from errors produced by Apache.

```bash
curl -s -o /dev/null -D - https://app1.example.com/ | grep -iE '^HTTP|^server'
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HTTPCode_ELB_502_Count \
  --dimensions Name=LoadBalancer,Value=app/lab-alb/50dc6c495c0c9188 --statistics Sum --period 3600 \
  --start-time "$(date -u -d '6 hours ago' +%FT%TZ)" --end-time "$(date -u +%FT%TZ)" \
  --query 'sort_by(Datapoints,&Timestamp)[].[Timestamp,Sum]' --output text
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HTTPCode_Target_5XX_Count \
  --dimensions Name=LoadBalancer,Value=app/lab-alb/50dc6c495c0c9188 --statistics Sum --period 3600 \
  --start-time "$(date -u -d '6 hours ago' +%FT%TZ)" --end-time "$(date -u +%FT%TZ)" \
  --query 'sort_by(Datapoints,&Timestamp)[].[Timestamp,Sum]' --output text
```

```
HTTP/2 502
server: awselb/2.0
2026-10-03T05:00:00+00:00	14.0
2026-10-03T06:00:00+00:00	17.0
2026-10-03T07:00:00+00:00	12.0
2026-10-03T08:00:00+00:00	16.0
```

**What it means:** the 502 carries `server: awselb/2.0`, so the ALB produced it, a steady handful
per hour. `HTTPCode_Target_5XX_Count` returned no datapoints: Apache itself is not returning 5xx.

**Why this step (now):** ELB-generated and target-generated errors have completely different
causes. Splitting them first decides whether you read ALB settings and connection behaviour, or
Apache's error log.

**Next step:** if the errors are target 5xx → read Apache's error log on the targets (Step 5). If
ELB 503 → Step 2. If ELB 502 or 504 → Step 2, then Step 4.

**Step 2 — Read target health with reason codes.**

**Goal:** see whether the ALB has healthy targets right now, and why not if it does not.

```bash
aws elbv2 describe-target-health --target-group-arn TG_ARN \
  --query 'TargetHealthDescriptions[].[Target.Id,TargetHealth.State,TargetHealth.Reason]' --output text
```

```
i-0a1b2c3d4e5f60011	healthy	None
i-0a1b2c3d4e5f60012	healthy	None
```

**What it means:** both targets are healthy now. A solid 503 means "no target to send to", so during
the 09:00 deploy there were zero registered targets for a while. A healthy target group with
sporadic 502s points at the connection between the ALB and Apache, not at the health check.

**Why this step (now):** target health is the single fastest view of the backend from the ALB's
side, and its reason code names the layer for any unhealthy target before you open a shell.

**Next step:** if targets are unhealthy → fix by reason code ("Health checks and ALB errors"). If
the 503 window matches a deploy → Step 3. For the sporadic 502s → Step 4.

**Step 3 — Explain the 503 window from the deploy history.**

**Goal:** prove the 503 came from the deploy deregistering every target at once.

```bash
aws cloudtrail lookup-events --lookup-attributes AttributeKey=EventName,AttributeValue=DeregisterTargets \
  --start-time "$(date -u -d '4 hours ago' +%FT%TZ)" \
  --query 'Events[].[EventTime,Username]' --output text
aws cloudwatch get-metric-statistics --namespace AWS/ApplicationELB --metric-name HealthyHostCount \
  --dimensions Name=TargetGroup,Value=targetgroup/apache/6d0ecf831eec9f09 Name=LoadBalancer,Value=app/lab-alb/50dc6c495c0c9188 \
  --statistics Minimum --period 60 --start-time 2026-10-03T03:25:00Z --end-time 2026-10-03T03:45:00Z \
  --query 'sort_by(Datapoints,&Timestamp)[].[Timestamp,Minimum]' --output text
```

```
2026-10-03T03:30:04+00:00	gitlab-deploy-4411
2026-10-03T03:30:02+00:00	gitlab-deploy-4411
2026-10-03T03:30:00+00:00	0.0
2026-10-03T03:31:00+00:00	0.0
2026-10-03T03:39:00+00:00	1.0
2026-10-03T03:40:00+00:00	2.0
```

**What it means:** the GitLab deploy job deregistered both targets within two seconds (09:00 IST is
03:30 UTC), and the healthy count stayed at zero until the new instances passed their health checks
ten minutes later. That is a deployment-order bug, not an AWS fault.

**Why this step (now):** a 503 that starts at a deploy is almost always the deploy. CloudTrail turns
"we think it was the deploy" into the exact API calls and the pipeline that made them.

**Next step:** fix the pipeline to replace targets one at a time, or register new ones and wait for
`healthy` before deregistering old ones (see [Deployment patterns](35-deployment-patterns.md)).
Then continue with the sporadic 502s in Step 4.

**Step 4 — Compare keep-alive and idle timeouts.**

**Goal:** test the most common cause of sporadic ELB 502s with healthy targets.

```bash
aws elbv2 describe-load-balancer-attributes --load-balancer-arn LB_ARN \
  --query "Attributes[?Key=='idle_timeout.timeout_seconds'].Value" --output text
aws ssm start-session --target i-0a1b2c3d4e5f60011
# inside the session:
grep -RiE '^\s*KeepAlive(Timeout)?\b' /etc/apache2/apache2.conf /etc/apache2/conf-enabled/ /etc/apache2/sites-enabled/
```

```
60
/etc/apache2/apache2.conf:KeepAlive On
/etc/apache2/apache2.conf:KeepAliveTimeout 5
```

**What it means:** the ALB reuses idle connections to Apache for up to 60 seconds, but Apache closes
idle connections after 5. Now and then the ALB sends a request on a connection Apache is closing at
that instant, gets a reset, and returns 502. The rate is low and steady, exactly as in Step 1.

**Why this step (now):** with healthy targets and no target 5xx, a timeout mismatch is the leading
hypothesis, and it is checked with two read-only commands. AWS's guidance is that the target's
keep-alive must be **longer** than the load balancer's idle timeout.

**Next step:** if Apache's timeout is shorter → apply the fix below and watch the 502 metric for
an hour. If it is already longer → Step 5 (access logs and Apache error log).

**Step 5 — Correlate access logs with Apache.**

**Goal:** match individual failed requests to what Apache saw, for anything Step 4 did not explain.

```bash
aws s3 cp s3://lab-alb-logs-123456789012/AWSLogs/123456789012/elasticloadbalancing/ap-south-1/2026/10/03/ /tmp/alb/ \
  --recursive --exclude '*' --include '*T0[5-8]*'
zcat /tmp/alb/*.log.gz | awk '$9 ~ /^50[24]$/ {print $2, $4, $5, $7, $9, $10, $13, $14, $15}' | head -5
```

```
2026-10-03T06:12:41.118Z 198.51.100.23:51870 10.20.17.25:81 -1 502 - "GET https://app1.example.com:443/orders HTTP/2.0"
2026-10-03T07:44:09.502Z 203.0.113.77:40212 10.20.49.12:81 -1 502 - "GET https://app1.example.com:443/ HTTP/2.0"
```

**What it means:** the fields are time, client, target, target processing time, ELB status, target
status and the request. A target processing time of `-1` with no target status means the ALB never
got a response from that target: the connection was closed or reset. Both targets are affected,
which fits a shared configuration (the keep-alive default) rather than one sick instance.

**Why this step (now):** access logs are the per-request evidence that metrics summarize. You use
them after the cheap hypothesis tests, to confirm the fix covers every failing request.

**Next step:** if the target status is a real 5xx → Apache's error log at the same timestamp, then
[Learn: Web servers & proxies](29-learn-webservers-proxies.md). If target processing time is near
60 s with 504 → the backend is slow: [Slow system](23-playbook-slow-system.md).

**Decision tree**

```
 5xx from the site
 ├─ server: awselb/2.0 ?  no ─▶ target error: Apache/app logs at that time
 └─ yes, ELB-generated
     ├─ 503 ─▶ describe-target-health
     │        ├─ no targets / all draining ─▶ deploy order (CloudTrail DeregisterTargets)
     │        └─ rule → empty group ───────▶ register targets or fix rule
     ├─ 502 ─▶ targets healthy?
     │        ├─ no  ─▶ reason code: Timeout=SG/port, ResponseCodeMismatch=path, FailedHealthChecks=process
     │        └─ yes ─▶ target keep-alive < ALB idle timeout? ─▶ raise KeepAliveTimeout
     │                  └─ no ─▶ access logs: -1 target time = reset; TLS to target? malformed headers?
     └─ 504 ─▶ target processing time ≈ idle timeout ─▶ slow backend or raise idle timeout deliberately
```

**Fix and verify.** On each Apache instance (or better, in the golden image or user data), set a
keep-alive longer than the ALB idle timeout, test the config, and reload gracefully:

```bash
echo 'KeepAliveTimeout 65' | sudo tee /etc/apache2/conf-available/alb-keepalive.conf
sudo a2enconf alb-keepalive
sudo apache2ctl configtest && sudo systemctl reload apache2
```

```
Syntax OK
```

Verify by watching `HTTPCode_ELB_502_Count` drop to zero over the next hours, with the same traffic.

**Rollback.** `sudo a2disconf alb-keepalive && sudo systemctl reload apache2` restores the old
behaviour. For the deploy fix, the previous pipeline version is one revert away in Git.

**Prevent it next time.** Bake `KeepAliveTimeout` into the image or Ansible role for every server
behind an ALB; alarm on `HTTPCode_ELB_5XX_Count` and on `HealthyHostCount < 1` per target group
(section 9); make the deploy job wait for `aws elbv2 wait target-in-service` before deregistering
the next target; and keep ALB access logs on with an S3 lifecycle rule.

---

## 7. RDS basics

> 📚 **Study path:** 1) Note: [Learn: Databases for DevOps](38-learn-databases-ops.md) first — backups, replication, PITR and connection limits are the concepts RDS automates, so refresh them before the AWS layer · 2) KodeKloud: *AWS Certified CloudOps Engineer - Associate* — the Reliability domain (backups, Multi-AZ, restores) ([link](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 3) Note: this section · 4) Practice: the failover and point-in-time restore drills below in your sandbox (a db.t4g.micro single-AZ costs cents per hour; do Multi-AZ for one hour only); KodeKloud has no RDS-specific course in the verified map, so check the current catalog if you want one

Tags: [L1 · Junior] for creating and connecting, [L2 · Mid] for Multi-AZ behaviour, replicas and restore drills.

RDS runs PostgreSQL, MySQL, MariaDB, SQL Server or Oracle for you: AWS installs, patches, backs up
and fails over; you choose the engine version, size, parameters, network and users, and you
**test the restores**. You do not get SSH, superuser or the data directory. Everything in
[Learn: Databases for DevOps](38-learn-databases-ops.md) about connections, locks and slow queries
still applies inside the engine.

### Multi-AZ vs read replicas

**Level:** [L2 · Mid] · about 50 minutes · lab cost: dollars (Multi-AZ doubles the instance price; one hour only)

**Concept.** Two features that sound similar and solve different problems:

| | Multi-AZ (DB instance) | Multi-AZ DB cluster | Read replica |
|---|---|---|---|
| Purpose | Availability | Availability plus read capacity | Read scaling, reporting, DR copy |
| Replication | Synchronous to one standby | Semi-synchronous to two readable standbys | Asynchronous |
| Standby readable? | No | Yes (reader endpoint) | Yes, own endpoint |
| Failover | Automatic, typically 1–2 minutes | Automatic, typically under a minute | Manual promotion; breaks replication |
| Other region? | No | No | Yes (cross-region replica) |
| On-prem analogy | Patroni pair with a synchronous standby | Patroni with synchronous standbys serving reads | A streaming replica you query for reports |

Failover is a **DNS change**: the instance endpoint (`lab-db.c9abcdefgh12.ap-south-1.rds.amazonaws.com`)
is re-pointed at the standby. Clients must reconnect and must not cache DNS for long: Java's
default caching, connection pools that never re-resolve, and hardcoded IPs all turn a 60-second
failover into a long outage. **RDS Proxy** pools connections and shortens failover for
applications. **Aurora** is a separate, AWS-built engine family (PostgreSQL- and MySQL-compatible)
with shared storage across three AZs and faster failovers; it is a choice to make deliberately,
not a default.

**Key terms**

| Term | Meaning |
|---|---|
| Instance endpoint | DNS name that always points at the current primary |
| Reader endpoint | DNS name that spreads connections across readable standbys or replicas |
| ReplicaLag | CloudWatch metric: seconds a read replica is behind |
| Forced failover | `reboot-db-instance --force-failover`, used to test Multi-AZ |
| Subnet group | The subnets (in at least two AZs) RDS may place instances in |
| Parameter group | The engine configuration (the cloud version of `postgresql.conf`) |

**See it on a real system**

```bash
aws rds describe-db-instances --db-instance-identifier lab-db \
  --query 'DBInstances[].[DBInstanceStatus,Engine,EngineVersion,MultiAZ,AvailabilityZone,SecondaryAvailabilityZone,PubliclyAccessible,Endpoint.Address]' \
  --output text
aws rds describe-events --source-identifier lab-db --source-type db-instance --duration 120 \
  --query 'Events[].[Date,Message]' --output text
# From an app instance
dig +short lab-db.c9abcdefgh12.ap-south-1.rds.amazonaws.com
```

```
available	postgres	16.8	True	ap-south-1a	ap-south-1b	False	lab-db.c9abcdefgh12.ap-south-1.rds.amazonaws.com
2026-10-03T04:10:02.511000+00:00	Multi-AZ instance failover started.
2026-10-03T04:10:38.902000+00:00	DB instance restarted
2026-10-03T04:11:20.117000+00:00	Multi-AZ instance failover completed
ec2-10-20-69-14.ap-south-1.compute.internal.
10.20.69.14
```

→ PostgreSQL 16 with a standby in ap-south-1b, not publicly accessible (good). The event log shows
a failover that took about 80 seconds end to end. The endpoint now resolves to 10.20.69.14 in
`data-b`: the old standby is the new primary. Any client still connected to the old address had
to reconnect.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create a subnet group from `data-a` and `data-b`, an SG allowing 5432 only
from the app instances' SG, and a PostgreSQL 16 `db.t4g.micro` with Multi-AZ, not public,
encrypted. From an app instance, run a loop that writes a timestamp every second:

```bash
export PGPASSWORD='LAB_PASSWORD' PGHOST=lab-db.c9abcdefgh12.ap-south-1.rds.amazonaws.com PGUSER=labadmin PGDATABASE=postgres
psql -c 'create table if not exists beat(t timestamptz default now())'
while true; do psql -qtAc 'insert into beat default values returning t' || date '+FAIL %T'; sleep 1; done
```

**Step 2 — Break it.** Force a failover: `aws rds reboot-db-instance --db-instance-identifier lab-db
--force-failover`. Count the `FAIL` lines and compare the gap with the event timestamps.

**Step 3 — Fix it.** There is nothing to fix on the AWS side; the lesson is the client. A new
`psql` per insert reconnects and resolves DNS every time, so it recovers on its own. An app with a
long-lived pool needs reconnect-on-error and short DNS caching, or RDS Proxy. Then turn Multi-AZ
off (or delete the instance) to stop the double charge.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| App caches DNS or IP | App broken long after the failover completed | `dig` the endpoint; app DNS settings | [DNS](08-dns.md) |
| Using a read replica as HA | Primary dies, nobody promotes, replica lags | `aws rds describe-db-instances --query '...ReadReplicaSourceDBInstanceIdentifier'` | this topic |
| Replica lag growing | Stale reads; `ReplicaLag` climbing | CloudWatch `ReplicaLag` | [Learn: Databases](38-learn-databases-ops.md) |
| Maintenance reboot surprise | Short outage in the maintenance window | `aws rds describe-pending-maintenance-actions` | section 1 |
| Publicly accessible database | Security finding, brute-force attempts | `PubliclyAccessible` field | section 13 |
| Too many connections | `FATAL: remaining connection slots are reserved` | `DatabaseConnections` metric; `max_connections` in the parameter group | [Learn: Databases](38-learn-databases-ops.md) |

**Why it matters for troubleshooting.** "The database failed over" explains a short blip; it does
not explain a long outage. When an app stays down after the RDS events say "completed", the
problem is on the client side: DNS caching, pools or retries.

**Next step:** backups that you have actually restored.

### RDS backups and restore drills

**Level:** [L2 · Mid] · about 50 minutes · lab cost: cents

**Concept.** RDS **automated backups** take a daily storage snapshot during the backup window and
ship transaction logs every few minutes, which gives **point-in-time recovery** (PITR) to any
second within the retention period (1 to 35 days) up to `LatestRestorableTime`, usually a few
minutes ago. **Manual snapshots** live until you delete them and can be copied to other regions or
shared with other accounts (with a customer managed KMS key, section 5).

The rule that catches everyone: **a restore always creates a new DB instance** with a new endpoint.
You never restore "in place". So a restore drill is: restore to a new instance, verify the data,
then either repoint the application or copy the needed rows back (for example one table with
`pg_dump -t`, exactly as in [Learn: Databases for DevOps](38-learn-databases-ops.md)). Deleting a DB
instance deletes its automated backups unless you choose to retain them, so always take a final
snapshot.

```
 RPO: how much data you can lose      ── PITR: minutes; daily snapshot only: up to 24 h
 RTO: how long until service is back  ── restore time (size-dependent) + verification + repoint
 Measure both in a drill; write them in the runbook; re-measure after the database grows.
```

**Key terms**

| Term | Meaning |
|---|---|
| Backup retention | Days of automated backups kept (0 disables them; avoid) |
| LatestRestorableTime | Most recent second you can restore to |
| PITR | Restore to a chosen timestamp from snapshot plus logs |
| Final snapshot | Manual snapshot taken when deleting an instance |
| AWS Backup | Central service for backup plans across RDS, EBS, EFS and more, with vaults and cross-account copies |

**See it on a real system**

```bash
aws rds describe-db-instances --db-instance-identifier lab-db \
  --query 'DBInstances[].[BackupRetentionPeriod,PreferredBackupWindow,LatestRestorableTime,DeletionProtection]' --output text
aws rds describe-db-snapshots --db-instance-identifier lab-db \
  --query 'DBSnapshots[].[DBSnapshotIdentifier,SnapshotType,SnapshotCreateTime,Status]' --output table
```

```
7	20:30-21:00	2026-10-03T04:37:05+00:00	True
--------------------------------------------------------------------------------------------
|                                   DescribeDBSnapshots                                    |
+--------------------------------+-------------+-----------------------------+-------------+
|  rds:lab-db-2026-10-02-20-31   |  automated  |  2026-10-02T20:31:44+00:00  |  available  |
|  lab-db-before-migration-0412  |  manual     |  2026-10-01T10:02:13+00:00  |  available  |
+--------------------------------+-------------+-----------------------------+-------------+
```

→ Seven days of PITR, a nightly backup window at 20:30 UTC (02:00 IST, outside business hours),
latest restorable time a few minutes ago, and deletion protection on. A manual snapshot was taken
before last week's migration, which is the habit you want.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** On `lab-db`, create a table `orders` and insert 100 rows. Note the UTC time.
Wait five minutes.

**Step 2 — Break it.** `DELETE FROM orders WHERE id > 10;` (the "bad migration"). Note the time.

**Step 3 — Fix it.** Restore to a moment between the two times, into a new instance, then copy the
table back:

```bash
aws rds restore-db-instance-to-point-in-time --source-db-instance-identifier lab-db \
  --target-db-instance-identifier lab-db-pitr-0410 --restore-time 2026-10-03T04:08:00Z \
  --db-subnet-group-name lab-data --vpc-security-group-ids sg-0a1b2c3d4e5f60091 \
  --db-instance-class db.t4g.micro --no-multi-az --no-publicly-accessible
aws rds wait db-instance-available --db-instance-identifier lab-db-pitr-0410
pg_dump -h lab-db-pitr-0410.c9abcdefgh12.ap-south-1.rds.amazonaws.com -U labadmin -d postgres \
  -t orders --data-only -Fc -f orders.dump
```

Load it into a side table on the primary, compare, then merge the missing rows. Time the whole
drill from "data is wrong" to "data is back": that is your measured RTO for this size. Delete the
restored instance afterwards.

> ⚠️ Never point the application at the restored instance, or drop and reload a production table,
> without a fresh manual snapshot of the current primary first. Safer path: restore to the side,
> verify, copy only what is missing, and keep both until the owner signs off.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Expecting an in-place restore | Searching for a "restore over" button | restore creates a new instance | this topic |
| Restored instance unreachable | App or `psql` times out | restored instance SG and subnet group (defaults may differ) | section 3 |
| Retention 0 or 1 day | PITR target outside the window | `BackupRetentionPeriod` | this topic |
| Instance deleted without final snapshot | Data gone, automated backups gone | `aws rds describe-db-snapshots` | section 13 |
| Restore much slower than expected | RTO missed during a drill | measure and record restore time per GB | [Senior architecture](39-learn-senior-architecture.md) |

**Why it matters for troubleshooting.** A backup you have not restored is a hope, not a backup.
The drill gives you real RTO and RPO numbers for incident decisions ("restore or fix forward?"),
and makes the restore commands familiar before the day you need them under pressure.

**Next step:** running your containers on AWS.

---

## 8. Containers on AWS

> 📚 **Study path:** 1) Note: refresh [Learn: Docker](30-learn-docker.md) and [Learn: Kubernetes](31-learn-kubernetes.md) first — you already run Swarm and kubeadm, so this section is a mapping exercise · 2) KodeKloud: *Docker Training Course for the Absolute Beginner* — the Docker Registry lesson, for the registry concepts behind ECR ([notes](https://notes.kodekloud.com/docs/Docker-Training-Course-for-the-Absolute-Beginner/Docker-Registry/Docker-Registry/page)) · 3) KodeKloud: *Certified Kubernetes Administrator (CKA)* — your CKA work is the EKS foundation; finish it first ([link](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 4) KodeKloud ECS- or EKS-specific courses are not in the verified map, so check the current catalog · 5) Practice: ECS and EKS labs in the [AWS Playground](https://kodekloud.com/cloud-playgrounds/aws), because an EKS cluster in your own account costs dollars per day

Tags: [L2 · Mid] for ECR and ECS/Fargate, [L3 · Senior] for EKS.

| Your on-prem stack | AWS | What changes |
|---|---|---|
| Harbor with a private CA | ECR | IAM authentication with 12-hour tokens; a public, trusted certificate (no CA to distribute) |
| Dokploy on Docker Swarm | ECS on Fargate or EC2 | Task definitions instead of compose files; each task gets its own ENI and SG |
| Traefik labels and `dokploy-network` | ALB listener rules and IP target groups | Routing lives on the load balancer, not in container labels |
| kubeadm cluster with containerd | EKS | Control plane and etcd are AWS's; IAM maps to Kubernetes RBAC; pods get VPC IPs |

### ECR, the AWS Harbor

**Level:** [L2 · Mid] · about 40 minutes · lab cost: cents

**Concept.** Amazon ECR is a private registry per account and region:
`123456789012.dkr.ecr.ap-south-1.amazonaws.com/REPOSITORY:TAG`. Instead of a username and password,
you exchange IAM credentials for a **registry token valid for 12 hours** and give it to Docker.
Repositories are created explicitly: a push to a missing repository fails, unless you have set up
a **repository creation template** for that name prefix, in which case ECR creates the repository on
push (since December 2025). Useful features map to
what you configure in Harbor: **lifecycle policies** (Harbor retention rules), **tag immutability**
(Harbor immutable tags), **image scanning** on push (Harbor's Trivy scanning), **replication**
across regions and accounts, and **pull-through cache** for Docker Hub and other upstreams (Harbor
proxy cache). ECR's endpoint uses a publicly trusted certificate, so the private-CA trust work you
did for Harbor (`/etc/docker/certs.d/`, containerd `hosts.toml`) does not apply.

**Key terms**

| Term | Meaning |
|---|---|
| Registry / repository | One per account per region / one image name inside it |
| Authorization token | Output of `get-login-password`; valid 12 hours |
| Credential helper | `docker-credential-ecr-login`, fetches tokens automatically |
| Lifecycle policy | Rules that expire images by age, count or tag prefix |
| Tag immutability | Refuses to overwrite an existing tag |
| Pull-through cache | ECR repository that caches an upstream registry on first pull |

**See it on a real system**

```bash
aws ecr describe-repositories \
  --query 'repositories[].[repositoryName,imageTagMutability,imageScanningConfiguration.scanOnPush]' --output table
aws ecr get-login-password --region ap-south-1 \
  | docker login --username AWS --password-stdin 123456789012.dkr.ecr.ap-south-1.amazonaws.com
aws ecr describe-images --repository-name app2 \
  --query 'sort_by(imageDetails,&imagePushedAt)[-3:].[imageTags[0],imagePushedAt,imageSizeInBytes]' --output table
```

```
------------------------------------
|       DescribeRepositories       |
+----------+-------------+---------+
|  app2    |  IMMUTABLE  |  True   |
|  apache  |  MUTABLE    |  False  |
+----------+-------------+---------+
Login Succeeded
----------------------------------------------------------------
|                        DescribeImages                        |
+------------+------------------------------------+------------+
|  3f9c2a1b  |  2026-10-01T09:12:44.103000+00:00  |  48211932  |
|  7d41e0c8  |  2026-10-02T15:40:02.881000+00:00  |  48230517  |
|  a1c3e5f7  |  2026-10-03T03:28:57.316000+00:00  |  48230981  |
+------------+------------------------------------+------------+
```

→ `app2` is immutable and scanned on push, with images tagged by commit SHA as your GitLab pipeline
does for Harbor. `apache` is mutable and unscanned: two settings to fix. The Docker login stores
the token in `~/.docker/config.json` (unencrypted unless you use a credential helper), and it
expires in 12 hours.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create repository `app2` with immutable tags and scan on push. Pull a small
image from your Harbor, retag it for ECR and push it with the commit SHA tag. Add a lifecycle policy
that keeps the last 10 images.

**Step 2 — Break it.** Push the same tag again with different content, then wait (or simulate) for
the token to expire and pull:

```
tag invalid: The image tag 'a1c3e5f7' already exists in the 'app2' repository and cannot be overwritten because the repository is immutable.
Error response from daemon: pull access denied for 123456789012.dkr.ecr.ap-south-1.amazonaws.com/app2, repository does not exist or may require 'docker login': denied: Your authorization token has expired. Reauthenticate and try again.
```

**Step 3 — Fix it.** The first error is the guardrail working: use a new tag per build. For the
second, install the ECR credential helper (package `amazon-ecr-credential-helper` on Ubuntu) and set
`"credHelpers": {"123456789012.dkr.ecr.ap-south-1.amazonaws.com": "ecr-login"}` in
`~/.docker/config.json`, so every pull fetches a fresh token with the instance role.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Token expired | `denied: Your authorization token has expired` | `aws ecr get-login-password ...` or credential helper | this topic |
| Missing IAM permission | `no basic auth credentials` or AccessDenied on `ecr:GetAuthorizationToken` / `ecr:BatchGetImage` | `aws sts get-caller-identity`, role policies | section 2 |
| Repository not created | `name unknown: The repository with name 'app2' does not exist` | `aws ecr describe-repositories`; create it, or add a repository creation template for create-on-push | this topic |
| Private subnet, no NAT or endpoints | Pull hangs at layer download | `ecr.api`, `ecr.dkr` endpoints plus the S3 gateway endpoint | section 3 |
| Lifecycle policy expired a running tag | Rollback to an old tag fails | lifecycle rules and `describe-images` | [Deployment patterns](35-deployment-patterns.md) |

**Why it matters for troubleshooting.** Registry problems on AWS are IAM and network problems, not
certificate problems. Separate "can I authenticate" (`get-login-password`) from "can I reach the
registry and S3" (endpoints, NAT) and you will find the cause quickly.

**Next step:** running those images without managing servers.

### ECS and Fargate

**Level:** [L2 · Mid] · about 60 minutes · lab cost: cents (a small Fargate task for an hour)

**Concept.** ECS is AWS's own orchestrator, simpler than Kubernetes and close to Swarm in spirit:

- A **task definition** (versioned as `family:revision`) describes containers, CPU and memory,
  ports, environment, secrets, log configuration and two IAM roles.
- A **service** keeps N copies of a task running, replaces failed ones, registers them with a
  target group and performs rolling deployments, optionally with a **circuit breaker** that rolls
  back automatically.
- A **cluster** is the namespace. Tasks run on **Fargate** (no servers to manage, you pay per vCPU
  and GB per second) or on EC2 instances you manage.
- With `awsvpc` networking each task gets **its own ENI**, private IP and security group, so target
  groups use target type `ip`.

The two roles are the most common source of confusion:

```
 Task EXECUTION role  ── used by the ECS agent BEFORE your app starts:
                         pull from ECR, write to CloudWatch Logs, fetch secrets for the task definition
 Task role            ── used by YOUR APP at runtime:
                         S3, SQS, DynamoDB calls made by the code (the container's credentials)
```

**Key terms**

| Term | Meaning |
|---|---|
| Task definition | Versioned JSON spec of one or more containers |
| Service | Long-running controller for a desired count of tasks |
| Fargate | Serverless compute for tasks; no hosts to patch |
| `stoppedReason` | Why ECS stopped a task: the first thing to read |
| Deployment circuit breaker | Stops and optionally rolls back a failing deployment |
| ECS Exec | `aws ecs execute-command` shell into a running container through SSM |

**See it on a real system**

```bash
aws ecs describe-services --cluster lab --services app2 \
  --query 'services[].[status,desiredCount,runningCount,pendingCount,deployments[0].rolloutState]' --output text
aws ecs describe-services --cluster lab --services app2 \
  --query 'services[0].events[:3].[createdAt,message]' --output text
aws ecs list-tasks --cluster lab --service-name app2 --desired-status STOPPED --query 'taskArns[:1]' --output text
aws ecs describe-tasks --cluster lab --tasks TASK_ARN \
  --query 'tasks[].[lastStatus,stoppedReason,containers[0].exitCode,containers[0].reason]' --output text
```

```
ACTIVE	2	0	2	IN_PROGRESS
2026-10-03T09:41:12.004000+05:30	(service app2) has started 2 tasks: (task 5f1e...) (task 9a2c...).
2026-10-03T09:40:31.881000+05:30	(service app2) deployment ecs-svc/1234567890123456789 deployment failed: tasks failed to start.
2026-10-03T09:39:57.402000+05:30	(service app2) has started 2 tasks: (task 1b7d...) (task 4c8e...).
arn:aws:ecs:ap-south-1:123456789012:task/lab/4c8e0f1a2b3c4d5e6f7a8b9c0d1e2f3a
STOPPED	ResourceInitializationError: unable to pull secrets or registry auth: execution resource retrieval failed: unable to retrieve ecr registry auth: service call has been retried 3 time(s): RequestError: send request failed caused by: Post "https://api.ecr.ap-south-1.amazonaws.com/": dial tcp 198.51.100.20:443: i/o timeout	None	None
```

→ The service wants 2 tasks and has 0 running: every task stops before the container starts. The
stopped reason says the task could not even reach the ECR API (`i/o timeout`). This is a network
problem, not an image or code problem: the tasks run in a private subnet with no NAT gateway and no
ECR endpoints, or in a public subnet without a public IP.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create cluster `lab`, a task definition for `app2` (Fargate, 0.25 vCPU,
512 MiB, port 3000, awslogs driver, execution role with `AmazonECSTaskExecutionRolePolicy`) and a
service with 2 tasks in the private subnets, attached to the `app2` target group from section 6,
with the circuit breaker and rollback enabled.

**Step 2 — Break it, two ways.** (a) Remove the NAT route (and have no endpoints): tasks stop with
the `ResourceInitializationError` above. (b) Restore the route, then lower the container's hard
memory limit (`memory` in the container definition; the Fargate task itself cannot go below
512 MiB) to 128 MiB for an app that needs more:

```
STOPPED	Essential container in task exited	137	OutOfMemoryError: Container killed due to memory usage
```

**Step 3 — Fix it.** (a) Restore egress or add the `ecr.api`, `ecr.dkr`, `logs` interface endpoints
and the S3 gateway endpoint (section 3). (b) Exit code 137 means SIGKILL; the reason says it was the
memory limit, exactly like `docker inspect` showing `OOMKilled: true` on your Dokploy host. Raise the
memory, register a new task definition revision, update the service. Watch the circuit breaker roll
back a deliberately broken revision, then delete the service.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| No path to ECR/Logs/Secrets | `ResourceInitializationError ... i/o timeout` | subnet routes, endpoints, `assignPublicIp` | section 3 |
| Execution role missing permissions | `ResourceInitializationError ... AccessDeniedException` | execution role policies | section 2 |
| Image tag missing | `CannotPullContainerError ... not found` | `aws ecr describe-images` | "ECR, the AWS Harbor" |
| Out of memory | Exit 137, `OutOfMemoryError` | `describe-tasks`, CloudWatch memory metrics | [Containers & K8s](26-playbook-containers-k8s.md) |
| Failing ALB health checks | `Task failed ELB health checks in (target-group ...)` | `describe-target-health` | section 6 |
| App uses the wrong role | App AccessDenied as the execution role | task role vs execution role | this topic |

**Why it matters for troubleshooting.** ECS writes down why it stopped every task. `stoppedReason`
plus the service events are the ECS equivalent of `docker service ps --no-trunc` on Swarm: read them
before you look at application logs.

**Next step:** Kubernetes on AWS, with your CKA skills.

### EKS and its quirks

**Level:** [L3 · Senior] · about 75 minutes · lab cost: dollars (about USD 0.10 per hour per cluster plus nodes; use the playground)

**Concept.** EKS runs the Kubernetes control plane (API servers, etcd) for you across three AZs.
Your `kubectl`, manifests, Helm charts and troubleshooting from [Learn: Kubernetes](31-learn-kubernetes.md)
work unchanged. What differs from your kubeadm homelab is what sits **around** Kubernetes:

| Area | kubeadm homelab | EKS |
|---|---|---|
| Control plane, etcd backups | Yours (`etcdctl snapshot save`) | AWS's; you never see the nodes |
| Who can use `kubectl` | Client certificates, kubeconfig | IAM principals mapped through **access entries** (the older `aws-auth` ConfigMap is deprecated) |
| Pod networking | Flannel or Calico overlay | **Amazon VPC CNI**: every pod gets a real VPC IP from the node's subnet |
| Pods per node | `maxPods` 110 by default | Limited by ENIs and IPs per instance type (for example 17 on a t3.medium) unless prefix delegation is on |
| Persistent volumes | local-path, NFS | EBS via the **EBS CSI driver add-on** (gp3), EFS via its CSI driver |
| Ingress / LoadBalancer services | Traefik or MetalLB | **AWS Load Balancer Controller** creates ALBs and NLBs |
| Pod credentials | Secrets you mount | **EKS Pod Identity** (or IRSA) gives a pod an IAM role |
| Upgrades | `kubeadm upgrade` | One minor version at a time; about 14 months of standard support per version, then paid extended support |
| Nodes | Your VMs | Managed node groups, Karpenter, Fargate or EKS Auto Mode |

**Key terms**

| Term | Meaning |
|---|---|
| Access entry | EKS API object that maps an IAM principal to Kubernetes permissions |
| Amazon VPC CNI (`aws-node`) | CNI plugin that assigns VPC IPs to pods |
| Prefix delegation | VPC CNI mode that assigns /28 prefixes to ENIs to raise pod density |
| EKS add-on | AWS-managed install of vpc-cni, coredns, kube-proxy, EBS CSI and others |
| Pod Identity | Association of a ServiceAccount with an IAM role |
| Extended support | Paid support period after a Kubernetes version's standard support ends |

**See it on a real system**

```bash
aws eks describe-cluster --name lab \
  --query 'cluster.[version,status,platformVersion,accessConfig.authenticationMode]' --output text
aws eks update-kubeconfig --name lab --region ap-south-1
aws eks list-access-entries --cluster-name lab --output text
aws eks list-addons --cluster-name lab --output text
kubectl get nodes -o wide
kubectl get pvc -A
```

```
1.34	ACTIVE	eks.7	API_AND_CONFIG_MAP
Updated context arn:aws:eks:ap-south-1:123456789012:cluster/lab in /home/learner/.kube/config
ACCESSENTRIES	arn:aws:iam::123456789012:role/AWSReservedSSO_AdministratorAccess_0a1b2c3d4e5f6a7b
ACCESSENTRIES	arn:aws:iam::123456789012:role/lab-node-role
ADDONS	coredns
ADDONS	kube-proxy
ADDONS	vpc-cni
ADDONS	eks-pod-identity-agent
NAME                                          STATUS   ROLES    AGE   VERSION               INTERNAL-IP    EXTERNAL-IP   OS-IMAGE                         KERNEL-VERSION                  CONTAINER-RUNTIME
ip-10-20-17-140.ap-south-1.compute.internal   Ready    <none>   2d    v1.34.1-eks-113cf36   10.20.17.140   <none>        Amazon Linux 2023.8.20250915    6.1.150-174.273.amzn2023.x86_64 containerd://1.7.27
ip-10-20-49-88.ap-south-1.compute.internal    Ready    <none>   2d    v1.34.1-eks-113cf36   10.20.49.88    <none>        Amazon Linux 2023.8.20250915    6.1.150-174.273.amzn2023.x86_64 containerd://1.7.27
NAMESPACE   NAME         STATUS    VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
app2        data-app2-0  Pending                                      gp3            <unset>                 11m
```

→ The cluster accepts both access entries and the legacy ConfigMap. The nodes run containerd, like
your homelab, with VPC addresses. The add-on list has **no `aws-ebs-csi-driver`**, which is why the
PVC is `Pending`: nothing can create EBS volumes. `kubectl describe pvc` would say it is waiting for
the external provisioner `ebs.csi.aws.com`.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** In the KodeKloud AWS playground (or a one-afternoon sandbox window), create a
small cluster with `eksctl create cluster --name lab --region ap-south-1 --nodes 2
--node-type t3.medium`, then run `aws eks update-kubeconfig`.

**Step 2 — Break it, three ways.** (a) From a second IAM role with no access entry, run
`kubectl get nodes`: `error: You must be logged in to the server (Unauthorized)`. (b) Apply a
StatefulSet with a gp3 PVC: `Pending`. (c) Scale a Deployment to 40 replicas on two t3.medium nodes:
pods stay `Pending` with `Too many pods` once each node hits its pod limit.

**Step 3 — Fix it.** (a) `aws eks create-access-entry` plus `aws eks associate-access-policy` for the
second role with a scoped policy. (b) Install the `aws-ebs-csi-driver` add-on with a Pod Identity
association for its controller, and create a gp3 StorageClass. (c) Add nodes, use larger types, or
enable prefix delegation, and check subnet free IPs (section 3). Then `eksctl delete cluster --name
lab` and verify the load balancers and volumes it created are gone.

> ⚠️ Deleting a cluster does not always delete the ALBs, NLBs and EBS volumes that controllers created
> for it, and those keep billing. Safer order: delete Ingresses, `LoadBalancer` Services and PVCs
> first, wait for the AWS resources to disappear, then delete the cluster, then run the teardown hunt
> from section 0.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| IAM principal has no access entry | `You must be logged in to the server (Unauthorized)` | `aws eks list-access-entries` | this topic |
| EBS CSI driver missing | PVC `Pending`, waiting for `ebs.csi.aws.com` | `aws eks list-addons` | [Containers & K8s](26-playbook-containers-k8s.md) |
| Pod limit or subnet IPs exhausted | `Too many pods`, or `failed to assign an IP address to container` | `kubectl describe node`, subnet `AvailableIpAddressCount` | section 3 |
| Ingress creates nothing | No ALB appears | AWS Load Balancer Controller logs and its IAM role | section 6 |
| Version past standard support | Extended support charge on the bill | `aws eks describe-cluster --query cluster.version` | section 12 |
| Pod uses node role instead of its own | AccessDenied naming the node role | Pod Identity association for the ServiceAccount | section 2 |

**Why it matters for troubleshooting.** On EKS, a Kubernetes symptom often has an AWS cause: IAM for
authentication, VPC IPs for scheduling, a missing add-on for storage, a controller's IAM role for
load balancers. Your CKA method still finds the symptom; this table finds the AWS layer behind it.

**Next step:** seeing all of these services from one place: CloudWatch, CloudTrail and Config.

---

## 9. Observability, audit and scaling

> 📚 **Study path:** 1) KodeKloud: *AWS Certified CloudOps Engineer - Associate* — the Monitoring, Logging and Remediation domain (CloudWatch, CloudTrail, EventBridge, SSM), then Reliability for Auto Scaling ([link](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 2) Note: [Learn: Performance & observability](32-learn-performance-observability.md) for metrics, alert design and the USE method, which CloudWatch only re-labels · 3) KodeKloud: *Fundamentals of SRE* — the Incident Management lessons on designing effective alerts ([link](https://kodekloud.com/courses/fundamentals-of-sre)) · 4) Note: [AWS reference](16-aws-cloud.md) section 8 (CloudWatch from the CLI) · 5) Practice: alarms on `mem_used_percent` and target 5xx in your sandbox, then an Auto Scaling group behind your lab ALB

Tags: [L1 · Junior] for metrics, alarms and the logs agent, [L2 · Mid] for CloudTrail, Config and Auto Scaling, [L3 · Senior] for org-wide trails, rules and quota management.

On-prem you run node_exporter, Prometheus, Grafana and Loki, and you read `/var/log/apache2` and
your shell history to learn who changed what. On AWS the same questions have managed answers:
**CloudWatch** for metrics, alarms and logs; **CloudTrail** for every API call; **Config** for the
configuration history of every resource; and **Auto Scaling** to act on metrics automatically.

### CloudWatch metrics and alarms

**Level:** [L1 · Junior] · about 45 minutes · lab cost: free to cents

**Concept.** AWS services publish **metrics** into **namespaces** (`AWS/EC2`, `AWS/ApplicationELB`,
`AWS/RDS`, `AWS/NATGateway`), identified by **dimensions** such as `InstanceId`. EC2 sends CPU,
network, disk and credit metrics every 5 minutes for free (1 minute with paid detailed monitoring);
status check metrics arrive every minute at no charge. EC2 does **not** see inside the OS, so **memory and disk-space metrics do not exist**
until you install the CloudWatch agent (next topic). That surprises everyone coming from
node_exporter.

An **alarm** watches one metric (or a math expression) and moves between `OK`, `ALARM` and
`INSUFFICIENT_DATA`. Its key settings mirror a Prometheus rule: period (the step), statistic
(Average, Maximum, p99), threshold, **evaluation periods** and **datapoints to alarm** (the `for:`
clause, "2 out of 3"), and **missing data treatment**. Actions go to SNS (email, chat, PagerDuty),
or act directly: recover, reboot or stop an EC2 instance, or scale an Auto Scaling group.

**Key terms**

| Term | Meaning |
|---|---|
| Namespace / dimension | Metric family / key-value that identifies one time series |
| Period / statistic | Aggregation window / how datapoints are combined |
| M out of N | Datapoints to alarm out of evaluation periods; prevents flapping |
| Missing data treatment | `missing`, `notBreaching`, `breaching` or `ignore` |
| Composite alarm | Alarm built from other alarms with AND/OR, to cut noise |
| SNS topic | Fan-out notification target for alarms |

**See it on a real system**

```bash
aws cloudwatch list-metrics --namespace AWS/EC2 --dimensions Name=InstanceId,Value=i-0a1b2c3d4e5f60011 \
  --query 'Metrics[].MetricName' --output text | tr '\t' '\n' | sort -u | paste -sd ' ' | fold -s -w 100
aws cloudwatch describe-alarms --state-value ALARM \
  --query 'MetricAlarms[].[AlarmName,StateReason]' --output text
```

```
CPUCreditBalance CPUCreditUsage CPUSurplusCreditBalance CPUSurplusCreditsCharged CPUUtilization
EBSByteBalance% EBSIOBalance% EBSReadBytes EBSReadOps EBSWriteBytes EBSWriteOps MetadataNoToken
MetadataNoTokenRejected NetworkIn NetworkOut NetworkPacketsIn NetworkPacketsOut StatusCheckFailed
StatusCheckFailed_AttachedEBS StatusCheckFailed_Instance StatusCheckFailed_System
lab-web-cpu-high	Threshold Crossed: 2 out of the last 3 datapoints [91.4 (03/10/26 04:20:00), 88.7 (03/10/26 04:15:00)] were greater than the threshold (80.0) (minimum 2 datapoints for OK -> ALARM transition).
```

→ The metric list has no memory or filesystem metric, confirming you need the agent. The alarm's
`StateReason` explains itself: two of the last three 5-minute averages exceeded 80%. Paste that
line into the incident channel; it answers "why did it page?".

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create an SNS topic `ops-alerts` with your email, confirm the subscription,
then create two alarms:

```bash
aws cloudwatch put-metric-alarm --alarm-name lab-web-cpu-high \
  --namespace AWS/EC2 --metric-name CPUUtilization --dimensions Name=InstanceId,Value=INSTANCE_ID \
  --statistic Average --period 300 --evaluation-periods 3 --datapoints-to-alarm 2 \
  --threshold 80 --comparison-operator GreaterThanThreshold --treat-missing-data missing \
  --alarm-actions arn:aws:sns:ap-south-1:123456789012:ops-alerts
aws cloudwatch put-metric-alarm --alarm-name lab-web-status-recover \
  --namespace AWS/EC2 --metric-name StatusCheckFailed_System --dimensions Name=InstanceId,Value=INSTANCE_ID \
  --statistic Maximum --period 60 --evaluation-periods 2 --threshold 0 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:automate:ap-south-1:ec2:recover arn:aws:sns:ap-south-1:123456789012:ops-alerts
```

**Step 2 — Break it.** Run `stress-ng --cpu 2 --timeout 20m` on the instance and wait for the email.
Then test the notification path without waiting for a real failure:
`aws cloudwatch set-alarm-state --alarm-name lab-web-status-recover --state-value ALARM
--state-reason "notification test"`. The SNS message is sent; do not rely on a forced state to
prove the EC2 recover action, which only makes sense on a real system-check failure, and run this
test only on a lab instance in case the action fires.

**Step 3 — Fix it.** Stop the stress test and watch the alarm return to `OK`. Then decide whether
you want an `--ok-actions` notification too, and write the alarm's runbook link into its
description so whoever is paged knows what to do.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| No memory or disk metrics | "Disk full" outage with no alert | `aws cloudwatch list-metrics --namespace CWAgent` | next topic |
| SNS subscription never confirmed | Alarm in ALARM, nobody notified | `aws sns list-subscriptions-by-topic --topic-arn ARN` | this topic |
| Alarm stuck `INSUFFICIENT_DATA` | Wrong dimension, instance replaced, metric not published | `aws cloudwatch list-metrics` with the alarm's dimensions | this topic |
| Flapping alarm | Pages every few minutes | raise M of N, use composite alarms | [Learn: Performance & observability](32-learn-performance-observability.md) |
| Alarm on a terminated instance | Silent: the metric just stops | missing data treatment `breaching` for heartbeat-style alarms | this topic |

**Why it matters for troubleshooting.** An alarm's history and `StateReason` are the start of every
AWS incident timeline. Knowing which metrics exist by default (and which do not) tells you which
blind spots you have before the incident finds them.

**Next step:** the metrics and logs from inside the OS.

### CloudWatch Logs and the agent

**Level:** [L1 · Junior] → [L2 · Mid] · about 50 minutes · lab cost: cents

**Concept.** **CloudWatch Logs** stores log events in **log groups** (one per application or log
file type) and **log streams** (one per instance or container). Retention defaults to **never
expire**, so set it on every group. Ingestion costs about USD 0.50 per GB, which makes chatty debug
logs a real bill line. **Logs Insights** queries groups with a pipe language similar to LogQL;
**metric filters** turn matching lines into metrics you can alarm on.

The **CloudWatch agent** runs on EC2 or on-prem servers and ships OS metrics (memory, disk,
swap, per-process) into the `CWAgent` namespace and log files into log groups. It needs the
`CloudWatchAgentServerPolicy` on the instance role. Systems Manager can install and configure it
across a fleet, the same way you would use Ansible on-prem.

**Key terms**

| Term | Meaning |
|---|---|
| Log group / stream | Container with retention and permissions / sequence from one source |
| Retention | Days to keep events; default is never expire |
| Logs Insights | Interactive query engine, billed per GB scanned |
| Metric filter | Pattern that increments a metric for each matching line |
| `CWAgent` namespace | Where agent metrics such as `mem_used_percent` and `disk_used_percent` land |

**See it on a real system**

```bash
aws logs describe-log-groups --query 'logGroups[].[logGroupName,retentionInDays,storedBytes]' --output table
# On the instance: agent status and its own log
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a status
sudo tail -n 3 /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log
```

```
------------------------------------------------
|              DescribeLogGroups               |
+----------------------+--------+--------------+
|  /aws/ecs/app2       |  30    |  1873221     |
|  /lab/apache/access  |  None  |  9214877120  |
|  /vpc/lab-flowlogs   |  3     |  44021       |
+----------------------+--------+--------------+
{
  "status": "running",
  "starttime": "2026-10-03T03:58:12+00:00",
  "configstatus": "configured",
  "version": "1.300060.0b1205"
}
2026-10-03T04:31:02Z I! [outputs.cloudwatchlogs] Configured middleware on AWS client
2026-10-03T04:31:02Z I! [processors.ec2tagger] ec2tagger: EC2 tagger has started, finished initial retrieval of tags and Volumes
2026-10-03T04:31:05Z I! [logagent] piping log from /lab/apache/access/i-0a1b2c3d4e5f60011(/var/log/apache2/access.log) to cloudwatchlogs
```

→ `/lab/apache/access` has no retention and already stores about 9 GB: a slow bill leak. The agent
runs and ships Apache's access log, with the instance ID as the stream name.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Attach `CloudWatchAgentServerPolicy` to `app-ec2-role`. Install the agent
through Systems Manager (`aws ssm send-command --document-name AWS-ConfigureAWSPackage --parameters
'action=Install,name=AmazonCloudWatchAgent' --targets Key=tag:Project,Values=lab`), then write
`/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json`:

```
{
  "agent": { "metrics_collection_interval": 60 },
  "metrics": {
    "append_dimensions": { "InstanceId": "${aws:InstanceId}" },
    "metrics_collected": {
      "mem":  { "measurement": [ "mem_used_percent" ] },
      "disk": { "measurement": [ "used_percent" ], "resources": [ "/", "/data" ] }
    }
  },
  "logs": { "logs_collected": { "files": { "collect_list": [
    { "file_path": "/var/log/apache2/access.log", "log_group_name": "/lab/apache/access",
      "log_stream_name": "{instance_id}", "retention_in_days": 14 },
    { "file_path": "/var/log/apache2/error.log", "log_group_name": "/lab/apache/error",
      "log_stream_name": "{instance_id}", "retention_in_days": 30 }
  ] } } }
}
```

Load it with `sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config
-m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json`.

**Step 2 — Break it.** Detach `CloudWatchAgentServerPolicy` from the role and restart the agent.
The agent log fills with `AccessDeniedException ... not authorized to perform: logs:PutLogEvents`,
and new `mem_used_percent` points stop arriving. Then fill `/data` to 95% with `fallocate -l` and
check whether any alarm would have told you.

**Step 3 — Fix it.** Reattach the policy. Create an alarm on `CWAgent disk_used_percent` above 85%
for `/data` (the ops-ladder L4 drill threshold), and run a Logs Insights query for Apache 5xx per
5 minutes:

```
fields @timestamp, @message
| parse @message '* - - [*] "* * *" * *' as ip, ts, method, path, proto, status, size
| filter status like /^5/
| stats count() as errors by bin(5m)
```

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Agent lacks permissions | `AccessDeniedException` in the agent log; metrics stop | agent log; role policies | section 2 |
| Agent cannot reach endpoints | Timeouts in the agent log from private subnets | `logs` and `monitoring` endpoints or NAT | section 3 |
| No retention set | Logs storage grows forever | `describe-log-groups` retention column | section 12 |
| Disk metric dimensions do not match the alarm | Alarm `INSUFFICIENT_DATA` | `aws cloudwatch list-metrics --namespace CWAgent` | previous topic |
| Logs Insights cost | Large scans on huge groups | narrow the time range and the groups | section 12 |

**Why it matters for troubleshooting.** The agent closes the gap between what AWS sees (the VM from
outside) and what you need (memory, disks, Apache logs). Its own log is the first place to look
when metrics or logs go quiet.

**Next step:** who changed what: CloudTrail and Config.

### CloudTrail and Config

**Level:** [L2 · Mid] → [L3 · Senior] · about 50 minutes · lab cost: free to cents

**Concept.** **CloudTrail** records API calls: who (`userIdentity`), what (`eventSource`,
`eventName`), when, from where (`sourceIPAddress`, `userAgent`), with what parameters, and whether
it failed (`errorCode`). **Event history** keeps 90 days of management events per region for free;
a **trail** delivers events to an S3 bucket for long-term storage and should be multi-region (an
**organization trail** at company scale), with log file validation on. Data events (S3 object
reads, Lambda invokes) cost extra and must be enabled explicitly.

**AWS Config** answers a different question: "what did this resource look like, and when did it
change?" It records **configuration items** for resources (an SG's rules, a bucket's policy) over
time, links them to the CloudTrail events that changed them, and evaluates **Config rules** such as
"no SG allows 22 from 0.0.0.0/0" or "all EBS volumes encrypted".

```
 "Port 81 stopped working at 03:12"
   Config:      sg-0a1b...72 rules at 03:00 vs 03:15  → the 81 rule disappeared
   CloudTrail:  RevokeSecurityGroupIngress at 03:11:48 by assumed-role/.../ravi from 198.51.100.40
   → you have the what, the when and the who, without asking anyone
```

**Key terms**

| Term | Meaning |
|---|---|
| Management event | Control-plane call such as `RunInstances` or `PutBucketPolicy` |
| Trail | Configuration that delivers events to S3 (and optionally CloudWatch Logs) |
| Organization trail | One trail for every account in the organization |
| Configuration item | Snapshot of a resource's configuration at a point in time |
| Config rule | Managed or custom check that marks resources compliant or not |
| EventBridge rule | Matches events (including CloudTrail API calls) and triggers targets |

**See it on a real system**

```bash
aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=sg-0a1b2c3d4e5f60072 \
  --max-results 3 --query 'Events[].[EventTime,EventName,Username]' --output text
aws cloudtrail describe-trails --query 'trailList[].[Name,IsMultiRegionTrail,IsOrganizationTrail,LogFileValidationEnabled,S3BucketName]' --output text
aws configservice get-resource-config-history --resource-type AWS::EC2::SecurityGroup \
  --resource-id sg-0a1b2c3d4e5f60072 --limit 2 \
  --query 'configurationItems[].[configurationItemCaptureTime,configurationItemStatus]' --output text
aws configservice describe-compliance-by-config-rule --compliance-types NON_COMPLIANT \
  --query 'ComplianceByConfigRules[].ConfigRuleName' --output text
```

```
2026-10-03T08:41:48+05:30	RevokeSecurityGroupIngress	ravi
2026-09-28T16:02:10+05:30	AuthorizeSecurityGroupIngress	gitlab-deploy-4302
2026-09-12T11:20:31+05:30	CreateSecurityGroup	gitlab-deploy-4105
org-trail	True	True	True	log-archive-cloudtrail-210987654322
2026-10-03T08:43:02.104000+05:30	OK
2026-09-28T16:03:30.811000+05:30	OK
restricted-ssh	s3-bucket-public-read-prohibited
```

→ CloudTrail shows a person removed a rule from the SG this morning, after two pipeline-made
changes. Config holds the before and after versions to compare. The organization trail is
multi-region with validation, delivered to a separate log-archive account. Two Config rules are
failing: someone has SSH open to the world and a bucket allows public reads.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create a multi-region trail to a new bucket with log file validation. Turn on
AWS Config for SGs, S3 buckets and EBS volumes only (to keep cost low), and add the managed rules
`restricted-ssh` and `encrypted-volumes`.

**Step 2 — Break it.** Add an SG rule allowing tcp 22 from 0.0.0.0/0 and create an unencrypted
volume (turn encryption by default off for a minute in the lab region). Within minutes both rules
report `NON_COMPLIANT`.

**Step 3 — Fix it.** Find each change in CloudTrail (`AuthorizeSecurityGroupIngress`,
`CreateVolume`), revert it, and re-evaluate the rules. Then add an EventBridge rule that matches
`RevokeSecurityGroupIngress` and `AuthorizeSecurityGroupIngress` on tagged production SGs and sends
them to `ops-alerts`. Turn Config recording off afterwards if you do not want the ongoing cost.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Looking in the wrong region | Event history empty | `--region` of the resource; global services log in us-east-1 | section 1 |
| Expecting data events | No S3 GetObject entries | trail event selectors | section 2 |
| Trail stopped or deleted | Gap in logs; attacker cleanup | alarm on `StopLogging` and `DeleteTrail` | section 13 |
| Events still arriving | Recent change not visible yet | wait about 5–15 minutes | this topic |
| Config cost surprise | Many configuration items from busy resources | record only the resource types you need | section 12 |

**Why it matters for troubleshooting.** "What changed?" is the most productive question in any
incident. On-prem it depends on discipline and shell history; on AWS, CloudTrail and Config answer
it with evidence, if you turned them on before the incident.

**Next step:** letting AWS add and replace servers for you.

### Auto Scaling and quotas

**Level:** [L2 · Mid] → [L3 · Senior] · about 60 minutes · lab cost: cents

**Concept.** An **Auto Scaling group** (ASG) keeps a number of identical instances, built from a
**launch template**, between a **min** and **max** around a **desired** capacity, spread across
subnets in several AZs. It does three jobs:

- **Self-healing.** With **health check type ELB**, an instance the target group marks unhealthy is
  terminated and replaced (with type EC2, only failed status checks count). A **grace period**
  stops it from killing instances that are still booting.
- **Scaling.** **Target tracking** ("keep average CPU at 50%" or "keep requests per target at
  1,000") is the default choice; step, scheduled and predictive policies exist for special cases.
- **Rolling replacement.** **Instance refresh** replaces instances gradually when you change the
  launch template (new AMI, new user data), the cloud version of a rolling deploy.

Scaling hits two kinds of ceilings: **capacity** (an AZ may have no spare instances of a type, so
allow several types and AZs) and **service quotas** (for example the vCPU limit for On-Demand
standard instances per region). Quotas are per account and region, have defaults far below what
large teams use, and are raised through Service Quotas, sometimes taking days.

**Key terms**

| Term | Meaning |
|---|---|
| Launch template | Versioned instance definition used by the ASG |
| Desired / min / max | Target count / floor / ceiling |
| Health check type | `EC2` (status checks) or `ELB` (target group health too) |
| Health check grace period | Seconds after launch before health checks count |
| Instance refresh | Rolling replacement of instances to a new template version |
| Service quota | Per-account, per-region limit such as running On-Demand vCPUs |

**See it on a real system**

```bash
aws autoscaling describe-auto-scaling-groups --auto-scaling-group-names lab-web \
  --query 'AutoScalingGroups[].[MinSize,DesiredCapacity,MaxSize,HealthCheckType,HealthCheckGracePeriod,length(Instances)]' \
  --output text
aws autoscaling describe-scaling-activities --auto-scaling-group-name lab-web --max-items 3 \
  --query 'Activities[].[StartTime,StatusCode,Description]' --output text
aws service-quotas get-service-quota --service-code ec2 --quota-code L-1216C47A \
  --query 'Quota.[QuotaName,Value]' --output text
```

```
2	4	6	ELB	300	4
2026-10-03T04:52:11.220000+00:00	Successful	Launching a new EC2 instance: i-0a1b2c3d4e5f60131
2026-10-03T04:51:58.004000+00:00	Successful	Terminating EC2 instance: i-0a1b2c3d4e5f60118
2026-10-03T04:22:40.731000+00:00	Failed	Launching a new EC2 instance.  Status Reason: You have requested more vCPU capacity than your current vCPU limit of 16 allows for the instance bucket that the specified instance type belongs to. (...) Launching EC2 instance failed.
Running On-Demand Standard (A, C, D, H, I, M, R, T, Z) instances	16.0
```

→ The group runs 4 of a desired 4 with ELB health checks and a 300-second grace period. Its
activity log shows a normal replacement of an unhealthy instance, and an earlier scale-out that
**failed on the account's vCPU quota** of 16. No metric shows that; only the activity log and
Service Quotas do.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create a launch template from your Apache-on-81 user data (section 4) and
an ASG `lab-web` (min 2, desired 2, max 4) in both private subnets, attached to the `apache` target
group, health check type ELB, grace period 300, with a target tracking policy at 50% CPU.

**Step 2 — Break it, two ways.** (a) Stop Apache on one instance: within a few minutes the target is
unhealthy and the ASG replaces the instance. (b) Create a launch template version with broken user
data (the `apache` typo from section 4) and start an instance refresh: new instances never become
healthy, and the activity log shows them terminated and relaunched in a loop.

**Step 3 — Fix it.** For (b), cancel the refresh (`aws autoscaling cancel-instance-refresh`), set the
template's default version back, and next time use instance refresh with a minimum healthy
percentage and **checkpoints** or auto rollback so a bad version stops itself. Then run
`stress-ng` on both instances and watch target tracking add instances up to the max. Set min,
desired and max to 0 to tear down.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Grace period too short | Healthy-to-be instances killed during boot; endless churn | `describe-scaling-activities` | this topic |
| Bad launch template version | Launch/terminate loop after a change | template versions, instance refresh status | section 4 (cloud-init) |
| vCPU or other quota | `Failed ... vCPU limit` in activities | `aws service-quotas get-service-quota` | this topic |
| No capacity for a type in an AZ | `InsufficientInstanceCapacity` | allow more types and AZs (mixed instances policy) | section 1 |
| Health check type EC2 only | Broken app instances never replaced | `HealthCheckType` | this topic |
| Scale-in kills a busy instance | Dropped requests or jobs | lifecycle hooks, scale-in protection, deregistration delay | [Deployment patterns](35-deployment-patterns.md) |

**Why it matters for troubleshooting.** With an ASG, "the server" is replaceable, so the evidence
moves from the instance (which may already be gone) to the group's activity log, the target health
history and centralized logs. Read the activity log first when instances appear and disappear.

**Next step:** describing all of this as code, deployed from GitLab without static keys.

---

## 10. Infrastructure as code

> 📚 **Study path:** 1) KodeKloud: *Terraform Basics Training Course* — Terraform State, Terraform with AWS, Remote State (S3 backend, locking), then Import/Taint/Debugging ([link](https://kodekloud.com/courses/terraform-basics-training-course)) · 2) Video: *What is Terraform? Introduction To Terraform Basics* (KodeKloud, 23 min), only if IaC is new ([link](https://www.youtube.com/watch?v=mzgfHmDRamk)) · 3) Note: [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) for the Terraform workflow and GitLab pipelines, then this section for the AWS side · 4) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Architecture & Core Concepts (variables, runners) ([link](https://kodekloud.com/courses/gitlab-ci-cd)) · 5) Practice: *Terraform Challenges*, free ([link](https://kodekloud.com/courses/terraform-challenges)), then rebuild the section 3 VPC in Terraform and deploy it from GitLab with OIDC

Tags: [L2 · Mid] for reading stacks and plans, [L3 · Senior] for owning state, pipelines and OIDC trust.

Everything in sections 3–9 was built by hand so you could see each piece. In a real team none of it
should be: a console change is invisible to review, impossible to reproduce in a second region and
the cause of the "tidied up" incident in the section 3 drill. This section compares the two main
IaC tools on AWS and shows how GitLab CI deploys with short-lived credentials. The Terraform
language and workflow itself is taught in [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md).

### CloudFormation vs Terraform

**Level:** [L2 · Mid] → [L3 · Senior] · about 45 minutes · lab cost: free

**Concept.** Both tools turn declarative files into AWS API calls and track what they created. They
differ in where that tracking lives and how failures behave:

| | CloudFormation | Terraform (or OpenTofu) |
|---|---|---|
| Language | YAML/JSON templates (or CDK in a programming language) | HCL |
| State | Kept by AWS inside the **stack** | A **state file** you store, usually in S3 |
| Locking | Implicit: one operation per stack | S3 backend lock file (`use_lockfile`, Terraform 1.10+; DynamoDB locking is the older method) |
| Preview | Change sets | `terraform plan` |
| Failure behaviour | Automatic **rollback** to the last good state | No rollback: partial apply, fix forward |
| Drift | Drift detection on demand | Every `plan` compares real resources with state |
| Scope | AWS only (plus registry extensions) | AWS, GitLab, Cloudflare, Kubernetes, vSphere... |
| Typical home | AWS-native teams, Control Tower, service-provided templates | Mixed estates like yours (on-prem plus AWS) |

For your situation, Terraform is the pragmatic choice: one tool for AWS, your GitLab projects and
possibly on-prem resources, and the KodeKloud path above already teaches it. Learn to **read**
CloudFormation anyway, because AWS services, Control Tower and many vendor quick starts deploy
stacks into your accounts, and you will debug them.

**Key terms**

| Term | Meaning |
|---|---|
| Stack | A CloudFormation deployment unit; owns its resources |
| Change set | Preview of what an update will add, modify or replace |
| `UPDATE_ROLLBACK_FAILED` | Stack state after a failed rollback; needs `continue-update-rollback` |
| State file | Terraform's map from code addresses to real resource IDs |
| Drift | Difference between code or state and what exists in AWS |
| Import | Bringing an existing resource under IaC management |

**See it on a real system**

```bash
aws cloudformation describe-stacks --query 'Stacks[].[StackName,StackStatus,LastUpdatedTime]' --output table
aws cloudformation describe-stack-events --stack-name lab-artifacts --max-items 4 \
  --query 'StackEvents[].[Timestamp,LogicalResourceId,ResourceStatus,ResourceStatusReason]' --output text
# Terraform, in the repository of the lab VPC
terraform state list | head -5
terraform plan -detailed-exitcode -lock-timeout=60s >/dev/null; echo "plan exit code: $?"
```

```
--------------------------------------------------
|                 DescribeStacks                 |
+-----------------+---------------------+--------+
|  lab-artifacts  |  ROLLBACK_COMPLETE  |  None  |
|  lab-budget     |  CREATE_COMPLETE    |  None  |
+-----------------+---------------------+--------+
2026-10-03T05:02:41.551000+00:00	lab-artifacts	ROLLBACK_COMPLETE	None
2026-10-03T05:02:40.102000+00:00	ArtifactsBucket	DELETE_COMPLETE	None
2026-10-03T05:02:31.817000+00:00	lab-artifacts	ROLLBACK_IN_PROGRESS	The following resource(s) failed to create: [ArtifactsBucket]. Rollback requested by user.
2026-10-03T05:02:31.660000+00:00	ArtifactsBucket	CREATE_FAILED	Resource handler returned message: "lab-artifacts-123456789012 already exists"
aws_internet_gateway.lab
aws_route_table.private_a
aws_route_table.public
aws_security_group.web
aws_subnet.private_a
plan exit code: 2
```

→ The stack failed because the bucket name already exists (it was created by hand earlier), and
CloudFormation rolled back automatically. A stack in `ROLLBACK_COMPLETE` cannot be updated; delete
it and create it again after fixing the cause. For Terraform, exit code 2 from
`plan -detailed-exitcode` means "changes pending": either new code or **drift** someone made in
the console. Exit code 0 means real resources match the code.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Create a state bucket (versioned, encrypted, Block Public Access on) and put
the section 3 security group in Terraform with this backend:

```
terraform {
  required_version = ">= 1.10"
  backend "s3" {
    bucket       = "lab-tfstate-123456789012"
    key          = "network/lab-vpc.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }
}
```

Run `terraform init`, `terraform plan`, `terraform apply`.

**Step 2 — Break it, two ways.** (a) Add an SG rule for tcp 8080 by hand in the console, then run
`terraform plan`: it proposes to remove the rule (drift). (b) Run `terraform apply` in two
terminals at once:

```
Error: Error acquiring the state lock

Error message: operation error S3: PutObject, https response error StatusCode: 412, api error PreconditionFailed: At least one of the pre-conditions you specified did not hold
Lock Info:
  ID:        3f1c9b2e-5a7d-4e2b-9c1f-0d8e6a4b2c11
  Path:      lab-tfstate-123456789012/network/lab-vpc.tfstate
  Operation: OperationTypeApply
  Who:       learner@lab01
```

**Step 3 — Fix it.** (a) Decide: if the 8080 rule is wanted, add it to the code and apply; if not,
let the plan remove it. Never leave drift unresolved. (b) The second apply correctly refused to run.
Wait for the first one to finish. Use `terraform force-unlock LOCK_ID` only when you have proven
that the lock's owner is dead (the runner was killed), never to get past a running apply.

> ⚠️ Deleting or hand-editing a Terraform state file can make Terraform forget, duplicate or destroy
> real infrastructure. Safer first: the state bucket is versioned, so copy the current version
> aside, then use `terraform state list`, `state mv`, `import` and `state rm` instead of editing the
> JSON.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Console change on IaC-managed resource | Next plan reverts someone's "quick fix" | `terraform plan`, CloudTrail for who changed it | section 9 |
| Stale lock after a killed CI job | `Error acquiring the state lock` with an old timestamp | check the job is dead, then `force-unlock` | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| CloudFormation stuck | `UPDATE_ROLLBACK_FAILED` | `describe-stack-events`, then `continue-update-rollback` | this topic |
| Resource exists outside IaC | "already exists" on create | `terraform import` or a CloudFormation import | this topic |
| Replacement instead of update | Plan shows `-/+` on a database or volume | read the plan's "forces replacement" lines | this topic |

**Why it matters for troubleshooting.** With IaC, "what is deployed" and "what should be deployed"
are both readable, and the difference is drift. A plan is a free, read-only diagnostic you can run
during an incident to see what someone changed by hand.

**Next step:** letting the pipeline apply that code without long-lived AWS keys.

### GitLab CI to AWS with OIDC

**Level:** [L3 · Senior] · about 60 minutes · lab cost: free

**Concept.** The old way to deploy from CI was an IAM user's access key in masked CI variables:
long-lived, copied everywhere, rarely rotated. The modern way is **OIDC federation**. GitLab signs a
short-lived **ID token** for each job (a JWT describing the project, branch and environment). AWS
trusts GitLab as an identity provider, and the job exchanges the token for temporary role
credentials with `AssumeRoleWithWebIdentity`. Nothing secret is stored in GitLab.

```
 GitLab job (protected branch main, project platform/infra)
   │ id_tokens: AWS_ID_TOKEN (JWT: iss=https://gitlab.example.com, aud=..., sub=project_path:platform/infra:ref_type:branch:ref:main)
   ▼
 AWS STS AssumeRoleWithWebIdentity(role gitlab-deploy, token)
   │ IAM checks: is the issuer a registered OIDC provider? signature valid (fetches GitLab's public keys)?
   │             trust policy conditions on aud and sub match?
   ▼
 temporary credentials (1 h) ──▶ terraform apply / aws ecs update-service / aws s3 sync
```

The **trust policy** is the security boundary. Pin the `sub` claim to a project and a protected
branch (or environment), so a merge request from a feature branch cannot assume the production role:

```
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Federated": "arn:aws:iam::123456789012:oidc-provider/gitlab.example.com" },
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {
        "gitlab.example.com:aud": "https://gitlab.example.com",
        "gitlab.example.com:sub": "project_path:platform/infra:ref_type:branch:ref:main"
      }
    }
  }]
}
```

And the job:

```yaml
deploy:
  stage: deploy
  image:
    name: amazon/aws-cli:2.31.4
    entrypoint: [""]
  id_tokens:
    AWS_ID_TOKEN:
      aud: https://gitlab.example.com
  variables:
    AWS_ROLE_ARN: arn:aws:iam::123456789012:role/gitlab-deploy
    AWS_DEFAULT_REGION: ap-south-1
  script:
    - echo "$AWS_ID_TOKEN" > /tmp/web-identity-token
    - export AWS_WEB_IDENTITY_TOKEN_FILE=/tmp/web-identity-token
    - export AWS_ROLE_SESSION_NAME="gitlab-${CI_PROJECT_ID}-${CI_PIPELINE_ID}"
    - aws sts get-caller-identity
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

One on-prem catch: AWS must be able to fetch your GitLab's OIDC discovery document and signing
keys (JWKS) over HTTPS from the internet. A self-managed GitLab that is reachable only on your LAN
cannot be an OIDC provider for AWS as is. The certificate should come from a public CA; if it is
signed by your private Harbor-style CA, IAM falls back to the certificate thumbprint registered on
the provider, which you must then update by hand on every CA change (see the IAM guide on OIDC
thumbprints). The alternatives are a runner on EC2 that uses its instance profile, or **IAM Roles
Anywhere**, which accepts X.509 certificates from a CA you register (your private CA can issue the
runner's certificate).

**Key terms**

| Term | Meaning |
|---|---|
| OIDC provider (IAM) | IAM object that trusts an issuer URL and audience |
| ID token | JWT that GitLab issues per job via the `id_tokens` keyword |
| `sub` claim | Subject: project path plus ref type and ref, or environment |
| `aud` claim | Audience; must match the provider's registered client ID and the trust condition |
| AssumeRoleWithWebIdentity | STS call that trades an OIDC token for role credentials |
| IAM Roles Anywhere | Role credentials for workloads outside AWS using X.509 certificates |

**See it on a real system**

```bash
aws iam list-open-id-connect-providers --output text
aws iam get-role --role-name gitlab-deploy --query 'Role.AssumeRolePolicyDocument.Statement[0].Condition'
# In the job log (masked output from the script above)
aws sts get-caller-identity
```

```
OPENIDCONNECTPROVIDERLIST	arn:aws:iam::123456789012:oidc-provider/gitlab.example.com
{
    "StringEquals": {
        "gitlab.example.com:aud": "https://gitlab.example.com",
        "gitlab.example.com:sub": "project_path:platform/infra:ref_type:branch:ref:main"
    }
}
{
    "UserId": "AROA6EXAMPLEDEPLOYID:gitlab-42-98765",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/gitlab-deploy/gitlab-42-98765"
}
```

→ The pipeline is running as the `gitlab-deploy` role with a session name that names the project
and pipeline. In CloudTrail, every change it makes carries that session name, so "which pipeline
changed this SG?" has an exact answer.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** In IAM, add an OIDC provider for your GitLab URL (gitlab.com works if your
self-managed instance is not internet-reachable) with audience `https://gitlab.example.com`. Create
role `gitlab-deploy` with the trust policy above, adjusted to your project, and a permission policy
limited to the lab (for example, Terraform on the lab VPC and the state bucket). Run the job on
`main`.

**Step 2 — Break it, three ways.** (a) Run the job from a feature branch (remove the `rules`). (b)
Change the job's `aud` to something else. (c) Point the provider at a GitLab that AWS cannot reach.

```
An error occurred (AccessDenied) when calling the AssumeRoleWithWebIdentity operation: Not authorized to perform sts:AssumeRoleWithWebIdentity
An error occurred (InvalidIdentityToken) when calling the AssumeRoleWithWebIdentity operation: Incorrect token audience
An error occurred (InvalidIdentityToken) when calling the AssumeRoleWithWebIdentity operation: Couldn't retrieve verification key from your identity provider,  please reference AssumeRoleWithWebIdentity documentation for requirements
```

**Step 3 — Fix it.** (a) is the trust policy protecting production: correct. For merge-request
pipelines, create a separate read-only role whose trust policy matches
`project_path:platform/infra:ref_type:branch:ref:*` with a `StringLike` condition (wildcards do not
work under `StringEquals`) and that only runs `terraform plan`. (b) Make the job's `aud`, the provider's audience and the trust condition
identical. (c) Make the issuer reachable or switch to an EC2 runner role or Roles Anywhere. Finally,
delete any old IAM user keys the pipeline used (deactivate first, section 2).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| `sub` does not match (branch, tag, MR) | `Not authorized to perform sts:AssumeRoleWithWebIdentity` | decode the JWT payload in a test job; compare with the trust policy | this topic |
| Audience mismatch | `InvalidIdentityToken: Incorrect token audience` | `id_tokens` aud vs provider client IDs | this topic |
| Issuer unreachable, or private CA without a matching thumbprint | `Couldn't retrieve verification key from your identity provider` | `curl -s https://gitlab.example.com/.well-known/openid-configuration` from outside | this topic |
| Role too broad | Any branch can deploy to production | review trust conditions | [Security & DevSecOps](37-learn-security-devsecops.md) |
| Old static keys still in CI variables | Keys in use alongside OIDC | `aws iam list-access-keys`, last used | section 2 |

**Why it matters for troubleshooting.** OIDC failures always come down to three claims (issuer,
audience, subject) and one trust policy. Reading them side by side solves the error, and keeping
them tight is what stops a compromised branch from reaching production.

**Next step:** joining the AWS network to your on-prem one.

---

## 11. Hybrid connectivity

> 📚 **Study path:** 1) Note: refresh routing, IPsec basics and DNS forwarding in [Learn: Networking](28-learn-networking.md) and [DNS](08-dns.md) · 2) KodeKloud: *AWS Networking Fundamentals* — the Transit Gateway and Route 53/DNS-in-VPC lessons ([link](https://kodekloud.com/courses/aws-networking-fundamentals)) · 3) KodeKloud: *AWS Certified CloudOps Engineer - Associate* — Networking and Content Delivery (troubleshooting connectivity) ([link](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 4) Practice: a Site-to-Site VPN from a strongSwan VM for one afternoon (dollars), Direct Connect as a paper design; KodeKloud VPN-specific labs are not in the verified map, so check the current catalog

Tags: [L3 · Senior] for all three topics; [L2 · Mid] engineers should be able to read the VPN and Resolver status commands.

Your company will not move everything to AWS at once. For years, Apache, Dokploy, Harbor and the
PostgreSQL servers on-prem will need to talk to workloads in VPCs, and both sides will need to
resolve each other's names. Three building blocks do that: an encrypted tunnel over the internet,
a private circuit, and DNS forwarding in both directions.

```
 On-prem 192.168.10.0/24                                     AWS ap-south-1
 ┌──────────────────────────────┐   IPsec tunnel 1 ─────▶   ┌─────────────────────────────────┐
 │ edge: strongSwan / firewall   │═══════════════════════════│ VGW or Transit Gateway          │
 │ public IP 203.0.113.10        │   IPsec tunnel 2 ─────▶   │  ├─ VPC lab 10.20.0.0/16        │
 │ BIND 192.168.10.53            │   (optional: Direct Connect│  └─ VPC lab2 10.30.0.0/16       │
 │  forward aws.example.com ─────┼──▶ Resolver INBOUND        │ Resolver OUTBOUND endpoint      │
 │  ◀──── corp.example.com ──────┼─── forwarding rule ◀───────│  rule: corp.example.com → .53   │
 └──────────────────────────────┘                            └─────────────────────────────────┘
```

### Site-to-Site VPN

**Level:** [L3 · Senior] · about 60 minutes · lab cost: dollars (about USD 0.05 per hour per connection)

**Concept.** An AWS **Site-to-Site VPN connection** joins a **customer gateway** (your on-prem
device: its public IP and, for BGP, its ASN) to a **virtual private gateway** on one VPC or to a
**Transit Gateway** for many. Each connection always has **two IPsec tunnels** to two different
AWS endpoints, so that AWS can maintain one while the other carries traffic. Routing is **static**
(you list the on-prem prefixes) or **dynamic with BGP** (recommended: failover between tunnels is
automatic). A standard tunnel carries up to about 1.25 Gbps; since November 2025, connections
attached to a Transit Gateway or Cloud WAN can choose **Large** tunnels of up to 5 Gbps each.

Common traps for on-prem engineers:

- **Route propagation.** The tunnel can be `UP` and nothing flows because the VPC route tables do not
  have a route to 192.168.10.0/24. Enable propagation from the VGW (or add TGW routes).
- **Both tunnels.** Configure both on your device. AWS tunnel maintenance takes one down without
  warning beyond a notification, and a single-tunnel setup turns that into an outage.
- **MTU and MSS.** IPsec overhead lowers the usable MTU. Clamp TCP MSS on the on-prem side (AWS
  recommends about 1379 bytes) or large transfers hang while pings work.
- **Firewalls on both ends.** UDP 500 and 4500 to the AWS tunnel endpoints, SGs that allow
  192.168.10.0/24, NACLs, and UFW on the on-prem hosts.

**Key terms**

| Term | Meaning |
|---|---|
| Customer gateway (CGW) | AWS object describing your on-prem VPN device |
| Virtual private gateway (VGW) | VPN concentrator attached to one VPC |
| Tunnel | One of the two IPsec SAs per connection, each to a different AWS endpoint |
| BGP ASN | Autonomous system number for dynamic routing (private range 64512–65534) |
| Route propagation | Route table setting that installs routes learned by the VGW |
| Dead peer detection (DPD) | IKE keepalive that tears down a dead tunnel |

**See it on a real system**

```bash
aws ec2 describe-vpn-connections --vpn-connection-ids vpn-0a1b2c3d4e5f60061 \
  --query 'VpnConnections[].VgwTelemetry[].[OutsideIpAddress,Status,StatusMessage,AcceptedRouteCount,LastStatusChange]' \
  --output table
aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=SUBNET_ID \
  --query 'RouteTables[].[PropagatingVgws[0].GatewayId, Routes[?DestinationCidrBlock==`192.168.10.0/24`]|[0].[GatewayId,Origin,State]]'
# On the on-prem strongSwan host (Ubuntu, swanctl)
sudo swanctl --list-sas | grep -E 'ESTABLISHED|INSTALLED'
```

```
---------------------------------------------------------------------------------
|                             DescribeVpnConnections                            |
+-----------------+--------+----------------+-----+-----------------------------+
|  198.51.100.71  |  UP    |  1 BGP ROUTES  |  1  |  2026-10-03T02:11:40+00:00  |
|  198.51.100.72  |  DOWN  |                |  0  |  2026-10-03T04:40:12+00:00  |
+-----------------+--------+----------------+-----+-----------------------------+
[
    [
        "vgw-0a1b2c3d4e5f60062",
        [ "vgw-0a1b2c3d4e5f60062", "EnableVgwRoutePropagation", "active" ]
    ]
]
aws-tunnel1: #3, ESTABLISHED, IKEv2, 2b4f1c0e9d8a7b6c_i* 5e6f7a8b9c0d1e2f_r
  aws-tunnel1-net: #7, reqid 1, INSTALLED, TUNNEL, ESP:AES_GCM_16-256
```

→ Tunnel 1 is up with one BGP route accepted (192.168.10.0/24); tunnel 2 went down at 04:40, and the
on-prem side shows only tunnel 1 established, so the device never brought up its second tunnel
again. Traffic still flows because the route table learned the on-prem prefix by propagation, but
you are one AWS maintenance away from an outage.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** If you have a lab box with a public IP, install strongSwan, create a CGW with
that IP and ASN 65010, a VGW on the `lab` VPC, and a VPN connection with BGP. Download the generic
or strongSwan configuration from the console, configure both tunnels and enable route propagation on
the private route tables. Without a public IP, simulate on-prem with an EC2 instance running
strongSwan in `lab2` (source/destination check disabled).

**Step 2 — Break it, three ways.** (a) Disable route propagation: tunnels stay `UP`, pings from
on-prem to 10.20.17.25 die. (b) Bring down tunnel 1 on your side (`sudo swanctl --terminate --ike
aws-tunnel1`) with tunnel 2 not configured: total outage. (c) Copy a 200 MB file over SSH through the
tunnel without MSS clamping: it stalls while ping works.

**Step 3 — Fix it.** (a) Re-enable propagation and confirm the route with `Origin
EnableVgwRoutePropagation`. (b) Configure both tunnels and let BGP fail over; test by terminating
each tunnel in turn. (c) Clamp MSS on the on-prem forwarding path (for example an nftables rule
`tcp flags syn tcp option maxseg size set 1379` in the forward chain). Delete the VPN connection and
VGW afterwards.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Tunnel up, no route | Pings time out, both tunnels `UP` | route table propagation | section 3 |
| Only one tunnel configured | Outage during AWS tunnel maintenance | `describe-vpn-connections` telemetry | this topic |
| IKE never establishes | Both tunnels `DOWN` | UDP 500/4500 on the edge firewall, PSK and proposals in `swanctl` logs | [Network](02-network.md) |
| MTU/MSS | Small requests work, large transfers hang | `ping -M do -s 1400 10.20.17.25` | [Network speed](24-playbook-network-speed.md) |
| SG or UFW blocks on-prem range | Tunnel and routes fine, one service times out | SG rules for 192.168.10.0/24 | section 3 |
| Overlapping CIDRs | Traffic goes to the local network instead | IP plan | section 3 |

**Why it matters for troubleshooting.** Hybrid outages are diagnosed in the same order as any
network path: tunnel state, routes on both sides, firewalls on both sides, then MTU. The VPN
telemetry and `swanctl` give you both ends of the tunnel in two commands.

**Next step:** the private-circuit alternative for bandwidth and predictability.

### Direct Connect

**Level:** [L3 · Senior] · about 30 minutes · lab cost: paper (a design exercise)

**Concept.** **Direct Connect** (DX) is a private circuit from your data center or colocation to an
AWS Direct Connect location, instead of the internet. **Dedicated connections** are 1, 10, 100 (and
in some locations 400) Gbps ports; **hosted connections** from partners range from 50 Mbps to
25 Gbps. Over the physical connection you create **virtual interfaces**: a **private VIF** to a VGW
or a **Direct Connect gateway**, a **transit VIF** to a Transit Gateway, or a **public VIF** to AWS
public endpoints. Routing is always BGP.

What a senior must know about DX before anyone signs an order:

- **Lead time is weeks**, involving a cross-connect at the location (LOA-CNA document) or a
  partner's provisioning.
- **It is not encrypted by default.** Use MACsec on supported dedicated connections, or run a
  Site-to-Site VPN over the DX for encryption.
- **One connection is one failure domain.** Resilience models range from a VPN backup to two
  connections at two DX locations for critical workloads.
- **Cost** is port-hours plus data transfer out at a lower rate than the internet. It pays off with
  steady, high-volume traffic or when consistent latency matters (database replication, large
  backups), not for a few Mbps.

**Key terms**

| Term | Meaning |
|---|---|
| Direct Connect location | Colocation facility where AWS has routers |
| Dedicated vs hosted connection | Your own port vs a partner-provided slice |
| Virtual interface (VIF) | Private, transit or public BGP session over the connection |
| Direct Connect gateway | Global object linking VIFs to VGWs or TGWs in many regions |
| LOA-CNA | Letter of authorization for the cross-connect |

**See it on a real system**

```bash
aws directconnect describe-connections \
  --query 'connections[].[connectionName,bandwidth,location,connectionState]' --output table
aws directconnect describe-virtual-interfaces \
  --query 'virtualInterfaces[].[virtualInterfaceName,virtualInterfaceType,virtualInterfaceState,bgpPeers[0].bgpStatus]' --output table
```

```
----------------------------------------------------
|               DescribeConnections                |
+---------------+---------+----------+-------------+
|  dc-mumbai-1  |  1Gbps  |  DXLOC1  |  available  |
+---------------+---------+----------+-------------+
-------------------------------------------------------
|              DescribeVirtualInterfaces              |
+--------------------+-----------+-------------+------+
|  prod-transit-vif  |  transit  |  available  |  up  |
+--------------------+-----------+-------------+------+
```

→ One 1 Gbps connection at one location, with a transit VIF whose BGP session is up. That is a
single point of failure: the design question is what carries traffic when this port or location
fails (a VPN backup over the internet is the usual minimum).

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it (on paper).** Your company backs up 2 TB a night from on-prem PostgreSQL to S3
and replicates a database to RDS. Sketch DX plus VPN backup: connection, transit VIF, DX gateway,
TGW, VPN as a backup path with BGP preferring DX.

**Step 2 — Break it (on paper).** The DX location loses power. Walk the traffic: BGP withdraws the
DX routes, the TGW prefers the VPN routes, throughput drops to about 1.25 Gbps per standard tunnel
(5 Gbps if you chose Large tunnels). Does the
nightly backup still finish? Does replication lag stay within the RPO?

**Step 3 — Fix it (on paper).** Decide between a second DX at another location, more VPN tunnels
with ECMP on the TGW, or accepting the degraded mode with a documented RPO. Write it as an ADR
([Senior architecture](39-learn-senior-architecture.md)).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| BGP session down | VIF `down`, routes withdrawn | `describe-virtual-interfaces` | this topic |
| No backup path | Full hybrid outage when the circuit fails | design review | section 13 |
| Assuming encryption | Audit finding | MACsec status or VPN-over-DX design | [Security & DevSecOps](37-learn-security-devsecops.md) |
| Asymmetric routing DX/VPN | Stateful firewalls drop return traffic | BGP local preference and AS path prepending on both sides | [Learn: Networking](28-learn-networking.md) |

**Why it matters for troubleshooting.** DX failures are physical and BGP failures, and the
incident depends entirely on whether someone designed a backup path. That is why DX is a senior
topic: the troubleshooting is easy, the design is not.

**Next step:** making names resolve across the hybrid network.

### Hybrid DNS with Resolver

**Level:** [L3 · Senior] · about 50 minutes · lab cost: dollars (each endpoint has at least two ENIs at about USD 0.125 per ENI-hour)

**Concept.** Inside a VPC, the Amazon resolver at base + 2 (the **Route 53 Resolver**) answers
private hosted zones, VPC endpoint private DNS and public names. It knows nothing about
`corp.example.com` in your BIND server at 192.168.10.53, and your on-prem servers cannot query it
directly (it is reachable only from inside the VPC). **Resolver endpoints** bridge the two:

- An **outbound endpoint** plus a **forwarding rule** ("`corp.example.com` → 192.168.10.53") lets
  VPC resources resolve on-prem names. Rules are associated with VPCs and can be shared to other
  accounts with RAM.
- An **inbound endpoint** gives the Resolver IP addresses in your VPC (for example 10.20.16.10 and
  10.20.48.10) that on-prem DNS can forward to for `aws.example.com` (your private hosted zone).

On the on-prem side, a BIND forward zone does the job:

```
zone "aws.example.com" {
    type forward;
    forward only;
    forwarders { 10.20.16.10; 10.20.48.10; };
};
```

For a single Ubuntu host, systemd-resolved can route just that domain over the VPN with a drop-in
file, `/etc/systemd/resolved.conf.d/aws.conf`, containing `DNS=10.20.16.10 10.20.48.10` and
`Domains=~aws.example.com` under `[Resolve]`, then `sudo systemctl restart systemd-resolved`.

**Key terms**

| Term | Meaning |
|---|---|
| Route 53 Resolver | The VPC's built-in resolver at base + 2 |
| Outbound endpoint | ENIs that send forwarded queries from the VPC to your DNS servers |
| Inbound endpoint | ENIs that receive queries from on-prem into the Resolver |
| Forwarding rule | Domain-to-target-IP rule used by the outbound endpoint |
| Rule association | Links a rule to a VPC; without it the rule does nothing there |

**See it on a real system**

```bash
aws route53resolver list-resolver-endpoints \
  --query 'ResolverEndpoints[].[Name,Direction,Status,IpAddressCount]' --output table
aws route53resolver list-resolver-rules \
  --query 'ResolverRules[?RuleType==`FORWARD`].[Id,DomainName,Status]' --output text
aws route53resolver list-resolver-rule-associations \
  --query 'ResolverRuleAssociations[].[ResolverRuleId,VPCId,Status]' --output text
# On an EC2 instance, and from an on-prem host
resolvectl query db01.corp.example.com
dig +short api.aws.example.com @192.168.10.53
```

```
-----------------------------------------------------
|               ListResolverEndpoints               |
+----------------+------------+---------------+-----+
|  lab-inbound   |  INBOUND   |  OPERATIONAL  |  2  |
|  lab-outbound  |  OUTBOUND  |  OPERATIONAL  |  2  |
+----------------+------------+---------------+-----+
rslvr-rr-0a1b2c3d4e5f60081	corp.example.com.	COMPLETE
rslvr-rr-0a1b2c3d4e5f60081	vpc-0a1b2c3d4e5f60020	COMPLETE
db01.corp.example.com: 192.168.10.40                 -- link: ens5

-- Information acquired via protocol DNS in 41.2ms.
-- Data is authenticated: no; Data was acquired via local or encrypted transport: no
-- Data from: network
10.20.17.25
```

→ Both endpoints are operational, the `corp.example.com` rule is associated with the lab VPC, the EC2
instance resolves an on-prem database name, and on-prem BIND answers for the private hosted zone
through the inbound endpoint. Each direction is a separate path; test both every time.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** With the VPN from the first topic up, create an inbound and an outbound
endpoint in `private-a` and `private-b` with an SG allowing tcp and udp 53 from 192.168.10.0/24
and from the VPC. Create the `corp.example.com` forwarding rule to 192.168.10.53, associate it with
`lab`, and add the BIND forward zone on-prem.

**Step 2 — Break it, three ways.** (a) Disassociate the rule from the VPC: `resolvectl query
db01.corp.example.com` returns `NXDOMAIN` from the public resolver path. (b) Remove udp 53 from the
endpoint SG: on-prem `dig` for `aws.example.com` times out. (c) Add a forward for `corp.example.com`
on-prem back to the inbound endpoint: queries loop until they time out.

**Step 3 — Fix it.** Re-associate, restore the SG rule, and remove the loop. Write down the rule:
each zone has exactly **one** authoritative home, and forwarding only ever points towards it. Delete
the endpoints after the lab (they cost about USD 180 a month each).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Rule not associated with the VPC | `NXDOMAIN` for on-prem names on EC2 | `list-resolver-rule-associations` | this topic |
| Endpoint SG or on-prem firewall blocks 53 | Timeouts in one direction only | SG rules; `sudo tcpdump -ni any port 53` on the BIND host | [DNS](08-dns.md) |
| Private zone not associated with the VPC | Inbound queries return `NXDOMAIN` | `aws route53 get-hosted-zone --id ZONE_ID --query VPCs` | section 6 |
| Forwarding loop | Slow timeouts, `SERVFAIL` | draw the forwarding chain for each zone | this topic |
| VPN down | Every on-prem name fails from AWS at once | VPN telemetry first | "Site-to-Site VPN" |

**Why it matters for troubleshooting.** In hybrid setups, "the app cannot reach the database" is
often "the app cannot resolve the database". Test name resolution from both sides before you test
the network path, exactly as the [Site down](25-playbook-site-down.md) layered walk starts with DNS.

**Next step:** what all of this costs, and how to keep the bill under control.

---

## 12. Cost and FinOps

> 📚 **Study path:** 1) Note: re-read "Pricing models" in section 1 and the teardown hunt in section 0 — this section builds on both · 2) KodeKloud: *AWS Certified Cloud Practitioner (CLF-C02)* — its billing and pricing material, if the vocabulary is new ([link](https://kodekloud.com/courses/aws-cloud-practitioner-clf-c02)) · 3) KodeKloud: *AWS Certified CloudOps Engineer - Associate* — the Cost and Performance Optimization domain ([link](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 4) Practice: a monthly 30-minute bill review of your sandbox using the commands below, and the bill-surprise hunt lab

Tags: [L1 · Junior] for reading the bill, tags and budgets, [L2 · Mid] → [L3 · Senior] for bill surprises, [L3 · Senior] → [L4 · Lead/SRE] for rightsizing and commitments.

On-prem, cost is a purchase decision made once every few years. On AWS it is an operational metric
that changes every hour, and every engineer who can create resources can create cost. Seniors are
expected to explain the bill, find waste and design for cost as deliberately as for availability.
FinOps is the team practice around it: **inform** (who spends what), **optimize** (remove waste,
buy commitments), **operate** (budgets, reviews, ownership).

### Reading the bill

**Level:** [L1 · Junior] · about 40 minutes · lab cost: free (Cost Explorer API calls cost USD 0.01 each)

**Concept.** Four tools cover almost every question:

| Tool | Answers | Notes |
|---|---|---|
| Bills page (Billing console) | What did last month cost, by service and region? | The authoritative invoice view |
| Cost Explorer | How did spend change, by service, usage type, region, account or tag? | Daily granularity, 13 months back by default (check Cost Explorer preferences for longer monthly history), forecasts |
| Budgets and Cost Anomaly Detection | Tell me before it hurts | Budgets alert on thresholds; anomaly detection learns your pattern |
| Data Exports (Cost and Usage Report) | Every line item, for Athena or a spreadsheet | For deep analysis and chargeback |

The most useful grouping is **usage type**, because it names the meter: `APS3-NatGateway-Bytes` is
NAT data processing in ap-south-1 (APS3 is that region's billing code), `APS3-DataTransfer-Regional-Bytes`
is cross-AZ traffic, `APS3-EBS:VolumeUsage.gp3` is gp3 storage. **Cost allocation tags** (such as
`Project` and `Owner`) must be **activated** in the Billing console before they appear in Cost
Explorer. They apply from activation forward unless the management account requests a
**backfill**, which re-tags up to 12 months of past usage (only for resources that already carried
the tag then).

**Key terms**

| Term | Meaning |
|---|---|
| Unblended / amortized cost | Charges as billed / upfront commitment fees spread over their term |
| Usage type | The specific meter, prefixed with a region code |
| Cost allocation tag | Resource tag activated for billing reports |
| Linked account | Member account whose costs roll up to the management account |
| Cost category | Rules that group costs into business units or products |

**See it on a real system**

```bash
aws ce get-cost-and-usage --time-period Start=2026-09-01,End=2026-10-01 --granularity MONTHLY \
  --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[0].Groups[].[Keys[0],Metrics.UnblendedCost.Amount]' --output text \
  | sort -t$'\t' -k2 -rn | head -5
aws ce get-cost-and-usage --time-period Start=2026-09-01,End=2026-10-01 --granularity MONTHLY \
  --metrics UnblendedCost --group-by Type=DIMENSION,Key=REGION \
  --query 'ResultsByTime[0].Groups[].[Keys[0],Metrics.UnblendedCost.Amount]' --output text
aws ce get-cost-and-usage --time-period Start=2026-09-01,End=2026-10-01 --granularity MONTHLY \
  --metrics UnblendedCost --group-by Type=TAG,Key=Project \
  --query 'ResultsByTime[0].Groups[].[Keys[0],Metrics.UnblendedCost.Amount]' --output text
```

```
Amazon Elastic Compute Cloud - Compute	41.82
EC2 - Other	38.15
Amazon Virtual Private Cloud	14.60
Elastic Load Balancing	12.33
Amazon Relational Database Service	9.71
ap-south-1	104.27
us-east-1	18.44
global	3.10
Project$	22.36
Project$lab	103.45
```

→ "EC2 - Other" is almost as large as compute: that bucket holds NAT gateways, EBS, snapshots and
data transfer, and it is where surprises hide. Public IPv4 charges, including idle Elastic IPs, have
been billed under "Amazon Virtual Private Cloud" since February 2024, and are often most of that
line. us-east-1 costs USD 18 although all labs run in
ap-south-1: something was left running there. `Project$` with an empty value is untagged spend.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Activate the `Project` and `Owner` cost allocation tags. Create a Cost
Anomaly Detection monitor for AWS services with an email subscription, if section 0 did not.

**Step 2 — Break it.** Find the us-east-1 spend: group the us-east-1 costs by usage type, then run
the region loop from section 1 and the teardown hunt from section 0 with `--region us-east-1`.

```bash
aws ce get-cost-and-usage --time-period Start=2026-09-01,End=2026-10-01 --granularity MONTHLY \
  --metrics UnblendedCost --filter '{"Dimensions":{"Key":"REGION","Values":["us-east-1"]}}' \
  --group-by Type=DIMENSION,Key=USAGE_TYPE \
  --query 'ResultsByTime[0].Groups[].[Keys[0],Metrics.UnblendedCost.Amount]' --output text
```

```
USE1-BoxUsage:t3.medium	15.02
USE1-EBS:VolumeUsage.gp3	1.20
USE1-PublicIPv4:InUseAddress	1.81
```

**Step 3 — Fix it.** A t3.medium with a 30 GB volume and a public IP has been running in us-east-1
since the middle of the month (about 361 hours): an "accidental" console launch like the one in
section 1. Terminate it, check that its volume was
deleted, and add a region allow-list SCP (section 2) or at least a budget filtered to unexpected
regions.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Untagged resources | Large `Project$` (empty) group | Tag Editor, `get-resources` | section 0 |
| Spend in an unused region | Region line you did not expect | region loop, teardown hunt | section 1 |
| Tags not activated | Tag grouping shows nothing | Billing → Cost allocation tags | this topic |
| Budget alert ignored | Email to a person on leave | send budgets to a team channel via SNS | section 9 |

**Why it matters for troubleshooting.** The bill is a log of what exists and what moved. A jump in a
usage type often points at a technical problem (a loop, a misroute, a leak) before any alarm does.

**Next step:** the specific line items that surprise almost every team.

### Common bill surprises

**Level:** [L2 · Mid] → [L3 · Senior] · about 50 minutes · lab cost: free (read-only hunting)

**Concept.** Most unexpected bills come from a short list. Learn it, check it monthly, and design
to avoid it:

| Surprise | Why it happens | How to find it | How to fix it |
|---|---|---|---|
| NAT gateway data processing | Every GB through NAT costs about USD 0.045, including S3, ECR and CloudWatch traffic from private subnets | usage type `NatGateway-Bytes`; NAT `BytesOutToDestination` metric; Flow Logs by destination | S3 gateway endpoint (free), interface endpoints for ECR and Logs, pull-through cache |
| Cross-AZ traffic | USD 0.01/GB each way between AZs: app in 1a talking to DB or cache in 1b, NLB cross-zone, Kafka replication | usage type `DataTransfer-Regional-Bytes` | AZ-aware routing, keep chatty pairs in one AZ where availability allows |
| Public IPv4 addresses | Every public IPv4 address costs about USD 3.65 a month, in use or idle, since February 2024 | usage types `PublicIPv4:InUseAddress` and `IdleAddress`; VPC IPAM public IP insights | Release idle EIPs; put instances behind an ALB in private subnets; IPv6 where possible |
| Idle EBS volumes and old snapshots | Volumes outlive terminated instances; snapshots never expire | `describe-volumes --filters Name=status,Values=available`; snapshots by age | Delete after a final snapshot; Data Lifecycle Manager retention |
| Idle load balancers and NAT gateways | Lab or old environment never torn down | teardown hunt; `RequestCount` near zero | Delete; tag owners |
| CloudWatch Logs | Debug logging ingested at USD 0.50/GB; never-expire retention | log groups by `storedBytes`; usage type `DataProcessing-Bytes` | Retention on every group; lower log levels; sample |
| Data transfer out | Downloads, backups to on-prem, API responses | usage type `DataTransfer-Out-Bytes` | CloudFront, compression, keep backups in-region |
| Versioned S3 buckets | Noncurrent versions and incomplete uploads | Storage Lens; lifecycle config | Noncurrent expiration, abort multipart uploads |
| EKS extended support | Cluster left on an old Kubernetes version | `describe-cluster` version | Upgrade on schedule |
| Unlimited t-instances | Surplus CPU credits | usage type `CPUCredits` | Right type for steady load |

**Key terms**

| Term | Meaning |
|---|---|
| Data processing charge | Per-GB fee for traffic through NAT gateways, TGW, endpoints |
| Regional data transfer | Traffic between AZs in a region, billed in both directions |
| Idle address | Allocated public IPv4 not attached to a running resource |
| Orphaned resource | Resource whose owner or parent no longer exists |

**See it on a real system**

```bash
aws ce get-cost-and-usage --time-period Start=2026-09-01,End=2026-10-01 --granularity MONTHLY \
  --metrics UnblendedCost UsageQuantity --group-by Type=DIMENSION,Key=USAGE_TYPE \
  --filter '{"Dimensions":{"Key":"SERVICE","Values":["EC2 - Other","Amazon Virtual Private Cloud"]}}' \
  --query 'ResultsByTime[0].Groups[].[Keys[0],Metrics.UsageQuantity.Amount,Metrics.UnblendedCost.Amount]' --output text \
  | sort -t$'\t' -k3 -rn | head -5
aws ec2 describe-addresses --query 'Addresses[?AssociationId==null].[PublicIp,AllocationId]' --output text
aws ec2 describe-snapshots --owner-ids self \
  --query 'Snapshots[?StartTime<`2026-04-01`].[SnapshotId,VolumeSize,StartTime]' --output text | wc -l
```

```
APS3-NatGateway-Hours	720.0	32.40
APS3-NatGateway-Bytes	412.6	18.57
APS3-EBS:VolumeUsage.gp3	140.0	11.20
APS3-PublicIPv4:IdleAddress	1440.0	7.20
APS3-DataTransfer-Regional-Bytes	188.3	3.77
203.0.113.40	eipalloc-0a1b2c3d4e5f60201
198.51.100.90	eipalloc-0a1b2c3d4e5f60202
37
```

→ The NAT gateway processed 413 GB, and an S3 gateway endpoint would remove much of that if it is
S3 or ECR traffic. Two EIPs are idle (1,440 idle address-hours) and 37 snapshots are older than six
months. Each line has a one-command check and a known fix. The NAT gateway's hourly charge is the
largest single line: in a lab, that alone justifies deleting it after each session.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** In the lab VPC with the NAT gateway from section 3, run `aws s3 cp` of a
1 GB file from a private instance to a bucket in the same region, five times.

**Step 2 — Break it.** The next day, look at `NatGateway-Bytes` in Cost Explorer and the NAT's
`BytesOutToDestination` metric for that hour: 5 GB billed for traffic that never left AWS.

**Step 3 — Fix it.** Add the S3 gateway endpoint to the private route tables and repeat the copy.
The NAT metric stays flat. Then run the full hunt: idle EIPs, available volumes, snapshot age, log
groups without retention, load balancers without targets. Release, delete or tag each one with an
owner.

> ⚠️ `aws ec2 release-address` and `delete-snapshot` are irreversible: a released EIP may never come
> back, and a deleted snapshot may be your only backup. Safer first: check what references an EIP
> (DNS records, partner allow-lists), and check snapshot tags and AMIs that use it
> (`describe-images --filters Name=block-device-mapping.snapshot-id,Values=SNAPSHOT_ID`).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| S3/ECR through NAT | High `NatGateway-Bytes` | NAT metrics, endpoints list | section 3 |
| Chatty cross-AZ design | High `DataTransfer-Regional-Bytes` | Flow Logs by AZ pair | section 13 |
| Idle public IPv4 | `PublicIPv4:IdleAddress` line | `describe-addresses` | this topic |
| Snapshots never expire | EBS snapshot storage grows monthly | snapshot age query | section 4 |
| Log retention never set | CloudWatch storage grows | `describe-log-groups` | section 9 |

**Why it matters for troubleshooting.** These surprises are often technical signals: NAT bytes
reveal traffic that should use an endpoint, cross-AZ bytes reveal a design that ignores AZ
affinity, and orphaned volumes reveal a broken teardown. Fixing them improves architecture as well
as cost.

**Next step:** paying less for what you genuinely need.

### Rightsizing and commitments

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · about 50 minutes · lab cost: free

**Concept.** After waste is gone, cost comes down by doing the same work with less, then committing
to the remainder:

- **Rightsize.** Use **Compute Optimizer** (free, opt-in; it needs the CloudWatch agent's memory
  metrics for good EC2 advice) and your own utilization data. Typical wins: oversized instances,
  gp2 to gp3 (about 20% cheaper with better baseline performance), Graviton (`m7g`, `t4g`) for
  workloads that run on ARM, which is most containerized Linux services.
- **Turn off what nobody uses.** Non-production running nights and weekends costs about 70% of the
  week for nothing; schedule it off with EventBridge Scheduler or Instance Scheduler.
- **Use Spot** where interruption is fine: CI runners (GitLab runner autoscaling on Spot), batch,
  stateless ASG capacity above a baseline.
- **Commit** to the steady baseline with **Savings Plans** (Compute Savings Plans apply across
  instance families, regions, Fargate and Lambda), **Database Savings Plans** (since December 2025:
  RDS, Aurora, ElastiCache, DynamoDB and more, up to about 20% on provisioned instances) and
  **Reserved Instances** for RDS, ElastiCache, OpenSearch and Redshift where the deeper, less flexible
  discount fits. Commit to the **minimum** steady usage, not the average, and track **coverage** (how
  much usage the commitment covers) and **utilization** (how much of the commitment you use).
- **Measure unit cost.** "Cost per 1,000 requests" or "cost per customer" tells you whether a growing
  bill is success or waste.

**Key terms**

| Term | Meaning |
|---|---|
| Rightsizing | Matching instance type and size to measured demand |
| Compute Optimizer | AWS service that recommends instance, volume, Lambda and ECS sizes |
| Savings Plan coverage | Share of eligible usage covered by commitments |
| Savings Plan utilization | Share of the commitment actually used |
| Unit economics | Cost divided by a business unit of work |

**See it on a real system**

```bash
aws compute-optimizer get-ec2-instance-recommendations \
  --query 'instanceRecommendations[].[currentInstanceType,finding,recommendationOptions[0].instanceType,utilizationMetrics[0].value]' \
  --output text
aws ce get-savings-plans-purchase-recommendation --savings-plans-type COMPUTE_SP \
  --term-in-years ONE_YEAR --payment-option NO_UPFRONT --lookback-period-in-days THIRTY_DAYS \
  --query 'SavingsPlansPurchaseRecommendation.SavingsPlansPurchaseRecommendationSummary.[HourlyCommitmentToPurchase,EstimatedMonthlySavingsAmount,EstimatedSavingsPercentage]' \
  --output text
aws ce get-savings-plans-coverage --time-period Start=2026-09-01,End=2026-10-01 \
  --query 'SavingsPlansCoverages[0].Coverage.CoveragePercentage' --output text
```

```
m7i.xlarge	Overprovisioned	m7g.large	11.4
t3.medium	Optimized	t3.medium	38.2
0.412	92.06	27.4
0.0
```

→ One instance averages 11% CPU on an m7i.xlarge and could be an m7g.large (smaller and Graviton).
Savings Plans would save about 27% on the current steady compute for a commitment of USD 0.41 per
hour, and current coverage is zero. A senior's job is to validate the recommendation (does the app
run on ARM? is the last 30 days representative?) before anyone buys a three-year commitment.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Opt in to Compute Optimizer for the sandbox account and leave the lab ASG
from section 9 running at low load for a day or two with the CloudWatch agent installed.

**Step 2 — Break it.** Read the recommendation and imagine buying a 3-year all-upfront Savings Plan
sized to last month's **peak**. Write down what happens when the lab is torn down next week: you
pay the commitment for three years for nothing.

**Step 3 — Fix it.** Write a one-page recommendation instead: rightsizing changes first, schedule
non-prod off, Spot for CI, then a 1-year no-upfront Compute Savings Plan sized to the minimum steady
hourly usage of the last 30 days, reviewed quarterly. That page is a senior deliverable; it belongs
with the cost section of your architecture docs in
[Senior architecture](39-learn-senior-architecture.md).

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Over-commitment | Savings Plan utilization under 100% | `aws ce get-savings-plans-utilization` | this topic |
| Rightsizing by CPU only | Memory-bound app OOMs after downsizing | CloudWatch agent `mem_used_percent` history | section 9 |
| Graviton migration breaks images | `exec format error` in containers | build multi-arch images in CI | [Learn: Docker](30-learn-docker.md) |
| Spot without interruption handling | CI jobs or tasks killed mid-run | Spot interruption notices, capacity-rebalance | section 9 |

**Why it matters for troubleshooting.** Cost changes are changes. Downsizing, Graviton and Spot each
introduce their own failure modes, so a senior treats a cost optimization like any production
change: measured, reversible and monitored.

**Next step:** stepping back to the architecture and governance view.

---

## 13. Architecture and governance

> 📚 **Study path:** 1) Note: [Senior architecture](39-learn-senior-architecture.md) for availability, DR tiers, ADRs and incident leadership — the vendor-neutral half of this section · 2) KodeKloud: *Fundamentals of SRE* — Incident Management (IMAG roles, blameless postmortems, root cause analysis) and Change Management for Reliability ([link](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) Reading: the AWS Well-Architected Framework and the security incident response guide in the AWS documentation ([docs.aws.amazon.com](https://docs.aws.amazon.com/)), and the Google SRE books ([sre.google/books](https://sre.google/books/)) · 4) Practice: a Well-Architected review of your own lab design, then a tabletop exercise of the leaked-key playbook below

Tags: [L3 · Senior] for designing for failure and landing zones, [L4 · Lead/SRE] for Well-Architected reviews, DR strategy and security incident response.

At this level the question changes from "how do I fix this?" to "how do we design so that this
class of failure cannot take us down, and how do we govern dozens of accounts?" The tools are
frameworks, reference architectures and rehearsed playbooks.

### Well-Architected pillars

**Level:** [L4 · Lead/SRE] · about 45 minutes · lab cost: free

**Concept.** The **AWS Well-Architected Framework** is a structured set of questions and best
practices grouped into six **pillars**. Its value is not the certificate-style vocabulary; it is a
checklist that forces trade-offs into the open. The questions apply just as well to your on-prem
Dokploy platform.

| Pillar | Core question | Example finding in your stack |
|---|---|---|
| Operational excellence | Can we run, observe and change it safely? | Console changes without IaC (section 3 drill) |
| Security | Are identities, data and networks protected? | Static keys in GitLab variables; SSH open to the world |
| Reliability | Does it recover from failure and meet demand? | One NAT gateway for all AZs; untested RDS restore |
| Performance efficiency | Are we using the right resources efficiently? | gp2 volumes at their burst limit; wrong instance family |
| Cost optimization | Are we paying only for value? | NAT bytes for S3 traffic; idle EIPs |
| Sustainability | Are we minimizing waste and impact? | Non-prod running all weekend |

A **review** walks a workload through these questions with its owners and records
**high-risk issues** (HRIs) and medium risks, then an improvement plan with owners and dates. The
free **Well-Architected Tool** in the console stores reviews and milestones, and **lenses** add
domain questions (serverless, SaaS, containers).

**Key terms**

| Term | Meaning |
|---|---|
| Pillar | One of the six areas of the framework |
| Workload | The set of components that delivers business value, reviewed as a unit |
| High-risk issue (HRI) | A best practice missing in a way likely to cause significant harm |
| Milestone | A saved snapshot of a review's state |
| Lens | Additional question set for a technology or industry |

**See it on a real system**

```bash
aws wellarchitected list-workloads --query 'WorkloadSummaries[].[WorkloadName,RiskCounts]' --output json
aws wellarchitected list-lens-review-improvements --workload-id WORKLOAD_ID \
  --lens-alias wellarchitected --pillar-id reliability \
  --query 'ImprovementSummaries[?Risk==`HIGH`].QuestionTitle' --output text
```

```
[
    [
        "lab-web",
        { "UNANSWERED": 12, "HIGH": 4, "MEDIUM": 6, "NONE": 35, "NOT_APPLICABLE": 0 }
    ]
]
How do you back up data?	How do you design your workload to withstand component failures?	How do you test reliability?
```

→ The lab workload has four high-risk issues, three of them in reliability: backups, component
failure and reliability testing. That is the improvement plan written for you, in priority order.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Define workload `lab-web` in the Well-Architected Tool: ALB, ASG, RDS, S3
backups, the VPN to on-prem.

**Step 2 — Break it.** Answer the Reliability and Security pillars honestly for the lab as you built
it. Expect HRIs: single NAT, no restore test, static keys if you still have any.

**Step 3 — Fix it.** Pick the top three HRIs, fix them with what you learned in sections 3–10, and
save a milestone. Repeat the review for your on-prem Dokploy platform on paper; the questions work
unchanged.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Review done once, never revisited | Same HRIs a year later | compare milestones | this topic |
| Checkbox answers | No HRIs found, incidents keep happening | review with on-call engineers present | [Senior architecture](39-learn-senior-architecture.md) |
| No owner per improvement | Plan never executed | assign owners and dates | [Career ladder](40-career-ladder.md) |

**Why it matters for troubleshooting.** Postmortems find one cause; a Well-Architected review finds
the next ones before they happen. Using both is how a lead eliminates classes of incidents instead
of single bugs.

**Next step:** designing for failure concretely.

### Designing for failure and DR

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · about 60 minutes · lab cost: dollars for a full drill, paper otherwise

**Concept.** AWS gives you failure domains (instances, AZs, regions) and expects you to design across
them. Two habits cover most of it:

- **Multi-AZ by default, static stability.** Run at least two of everything in two AZs (ALB nodes,
  ASG instances or ECS tasks, NAT gateways, RDS Multi-AZ), with enough capacity that losing one AZ
  does not require launching anything new during the event, when capacity may be scarce.
- **Disaster recovery by tier.** Choose a strategy per workload from its RTO and RPO, and rehearse
  it.

| DR strategy | What runs in the recovery site | RPO | RTO | Relative cost |
|---|---|---|---|---|
| Backup and restore | Only backups (cross-region snapshots, S3 replication) | hours | hours to a day | lowest |
| Pilot light | Data replicated; core infrastructure defined, compute off | minutes | tens of minutes to hours | low |
| Warm standby | Scaled-down full copy running | seconds to minutes | minutes | medium |
| Multi-site active/active | Full capacity in both, traffic split | near zero | near zero | highest |

For you, the most realistic first design is **hybrid**: on-prem Dokploy stays primary, and AWS is
the pilot-light DR site.

```
 Normal                                         On-prem down (DR)
 users ─▶ Route 53 failover record              users ─▶ Route 53 (primary health check failed)
          ├─ PRIMARY: on-prem Traefik :443               └─▶ SECONDARY: ALB in ap-south-1
          │   (health check /health)                          ├─ ASG / ECS scaled from 0 → 2 (IaC)
          └─ SECONDARY: ALB (no healthy targets yet)          ├─ RDS restored from cross-copied snapshot,
 nightly: pg_dump / WAL archive → S3 (versioned, locked)      │  or replica promoted
 nightly: Harbor images replicated → ECR                      └─ images already in ECR
 RTO target 2 h, RPO target 15 min, drilled twice a year
```

**Key terms**

| Term | Meaning |
|---|---|
| RTO / RPO | Maximum acceptable downtime / maximum acceptable data loss |
| Static stability | Surviving a failure without needing to change or add anything during it |
| Failure domain | Scope one failure can take out: instance, AZ, region, account |
| Game day | Planned exercise that injects a real failure to test recovery |
| Fault Injection Service | AWS service that runs controlled failure experiments |

**See it on a real system**

```bash
aws route53 get-health-check-status --health-check-id HEALTH_CHECK_ID \
  --query 'HealthCheckObservations[:3].[Region,StatusReport.Status]' --output text
aws rds describe-db-snapshots --region ap-southeast-1 --snapshot-type manual \
  --query 'DBSnapshots[-1].[DBSnapshotIdentifier,SnapshotCreateTime]' --output text
aws ecr describe-images --repository-name app2 --query 'length(imageDetails)'
```

```
ap-southeast-1	Success: HTTP Status Code 200, OK. Resolved IP: 203.0.113.10
eu-west-1	Success: HTTP Status Code 200, OK. Resolved IP: 203.0.113.10
us-east-1	Success: HTTP Status Code 200, OK. Resolved IP: 203.0.113.10
lab-db-dr-copy-2026-10-02	2026-10-02T21:14:03.211000+00:00
24
```

→ Route 53 checkers in three regions see the on-prem primary as healthy. The latest cross-region
snapshot copy is from last night (so the RPO for a regional disaster is up to a day, not 15 minutes;
the WAL archive in S3 would close that gap). ECR holds 24 images, so the DR site does not depend on
the on-prem Harbor being up.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it (small).** Use the Route 53 failover pair from section 6 with your on-prem or
lab primary and an ALB secondary whose ASG is at 0. Keep the IaC that scales it to 2.

**Step 2 — Break it.** Game day: stop the primary's web service. Measure, with timestamps: health
check failure detected, DNS answers changed, ASG scaled, targets healthy, first successful user
request. That total is your real RTO.

**Step 3 — Fix it.** Compare with the target. The usual findings: DNS TTL too high, ASG grace
period too long, database restore slowest of all. Fix the biggest gap, write a postmortem of the
exercise, and schedule the next drill.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| DR never tested | Recovery takes days, steps missing | run a game day | [Senior architecture](39-learn-senior-architecture.md) |
| DR depends on the failed site | Images or secrets only on-prem | ECR replication, Secrets Manager copies | section 8 |
| Single-AZ component | Whole service down during one AZ event | review every tier for two AZs | section 3 |
| Quota in the DR region | DR scale-out fails | Service Quotas in the DR region | section 9 |
| RPO assumed, not measured | More data lost than promised | measure snapshot and log shipping lag | section 7 |

**Why it matters for troubleshooting.** During a real disaster you execute, you do not design. The
drill turns the DR plan into muscle memory and turns guessed RTO and RPO into measured numbers that
management can make decisions with.

**Next step:** running many accounts the same way.

### Landing zones at scale

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · about 40 minutes · lab cost: paper (Control Tower in a real organization)

**Concept.** A **landing zone** is the pre-built, governed multi-account foundation every workload
lands in: the account structure from section 2, plus identity, logging, security services,
networking and guardrails, all deployed as code. **AWS Control Tower** automates a standard one;
large teams also build their own with Terraform (Account Factory for Terraform) or similar.

| Layer | Typical landing-zone choice |
|---|---|
| Accounts | Management (billing only), log archive, audit/security, network, shared services, one account per workload per environment, sandboxes |
| Identity | IAM Identity Center with your directory; permission sets per role; no IAM users |
| Guardrails | SCPs and RCPs (region allow-list, deny disabling CloudTrail and GuardDuty, deny root use), Config rules as detective controls |
| Logging | Organization CloudTrail and Config to the log archive account, write-once |
| Security services | GuardDuty, Security Hub, IAM Access Analyzer with a delegated admin in the audit account |
| Network | Transit Gateway in the network account, shared subnets through RAM, hybrid VPN/DX and Resolver rules (section 11) |
| Account vending | New accounts created through a pipeline with all of the above applied |
| Cost | Tag policies, budgets per account, cost categories per team |

**Key terms**

| Term | Meaning |
|---|---|
| Landing zone | The governed multi-account baseline |
| Control Tower | AWS service that sets up and governs a landing zone |
| Control (guardrail) | Preventive (SCP), detective (Config rule) or proactive (hook) rule |
| Account vending | Automated, standardized account creation |
| RAM | Resource Access Manager: shares subnets, TGWs and Resolver rules across accounts |

**See it on a real system**

```bash
aws controltower list-landing-zones --output text
aws organizations list-delegated-administrators \
  --query 'DelegatedAdministrators[].[Name,Id]' --output text
aws ram get-resource-shares --resource-owner SELF \
  --query 'resourceShares[].[name,status]' --output text
```

```
LANDINGZONES	arn:aws:controltower:ap-south-1:123456789012:landingzone/1A2B3C4D5E6F7G8H
audit	210987654323
network	210987654324
shared-subnets-prod	ACTIVE
resolver-rules-corp	ACTIVE
```

→ A Control Tower landing zone exists, security services are delegated to the audit account, and the
network account shares subnets and the `corp.example.com` resolver rules with workload accounts.
When a workload account "cannot resolve on-prem names", one place to check is whether it received
that share.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it (on paper).** Draw a landing zone for your company: the OU tree from section 2,
which account owns the VPN to 192.168.10.0/24, where GitLab OIDC roles live, where Harbor-to-ECR
replication lands.

**Step 2 — Break it (on paper).** A team creates a workload in the management account "because it
was quicker". List what goes wrong: SCPs do not apply, billing and workload permissions mix, and the
blast radius of a compromise includes the whole organization.

**Step 3 — Fix it (on paper).** Write the guardrail that prevents it (an IAM policy on the
management account and a process rule) and the account-vending path that makes the right way the
quick way. That is platform engineering applied to AWS.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Workloads in the management account | Guardrails silently absent | `aws organizations describe-organization` | section 2 |
| Hand-made accounts | Missing trail, no GuardDuty, open defaults | Config aggregator, Security Hub | section 9 |
| Shared resource not shared | New account cannot reach TGW or resolve on-prem | `aws ram get-resource-shares` | section 11 |
| Guardrail too broad | Deployments fail across many accounts at once | CloudTrail `errorCode` with SCP deny messages | section 2 |

**Why it matters for troubleshooting.** At scale, many incidents are "this account is not like the
others". A landing zone makes accounts identical by construction, so differences become findings
instead of surprises.

**Next step:** what to do when the incident is a security breach.

### Cloud security incidents

**Level:** [L4 · Lead/SRE] · about 50 minutes · lab cost: free (tabletop)

**Concept.** Cloud breaches usually start with leaked credentials, an exposed service or a
vulnerable instance, and attackers move fast: within minutes of a key appearing in a public repo,
bots launch crypto-mining instances in every region. Your playbook follows the classic order from
[Security & DevSecOps](37-learn-security-devsecops.md) (detect, contain, preserve evidence,
eradicate, recover, learn), with AWS-specific moves:

**Leaked access key.** Deactivate the key first (reversible), then find everything it did in
CloudTrail by `AccessKeyId` across all regions: new IAM users, keys, roles, policies, instances,
Lambda functions. AWS may already have attached a quarantine managed policy to the user and opened
a support case; that does not replace your investigation.

**Compromised role session.** Use IAM's **revoke active sessions** for the role, which adds a policy
denying all sessions issued before now, then fix whatever leaked the session (an SSRF with IMDSv1,
a container with too much access).

**Compromised instance.** Do **not** terminate it first; you would destroy the evidence. Isolate it
with a security group that has no rules (existing tracked connections may persist, so also apply a
NACL deny if needed), detach it from its ASG and target groups, snapshot its volumes for forensics,
then rebuild from a known-good AMI.

**Detection sources.** GuardDuty findings, CloudTrail anomalies, budget and anomaly alerts (a sudden
spend spike is a classic first signal), Config rule changes, Security Hub.

**Key terms**

| Term | Meaning |
|---|---|
| GuardDuty | Threat detection from CloudTrail, VPC Flow Logs, DNS logs and more |
| Quarantine policy | AWS managed policy attached to users whose keys were exposed |
| Revoke active sessions | IAM action that invalidates role sessions issued before a time |
| Forensic snapshot | EBS snapshot of a compromised instance, kept for analysis |
| Isolation SG | Security group with no rules, used to contain an instance |

**See it on a real system**

```bash
aws guardduty list-detectors --query 'DetectorIds[0]' --output text
aws guardduty list-findings --detector-id DETECTOR_ID \
  --finding-criteria '{"Criterion":{"severity":{"Gte":7}}}' --query 'FindingIds[:5]' --output text
aws guardduty get-findings --detector-id DETECTOR_ID --finding-ids FINDING_ID \
  --query 'Findings[].[Type,Severity,Resource.InstanceDetails.InstanceId,Service.Count]' --output text
aws cloudtrail lookup-events --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=AKIAIOSFODNN7EXAMPLE \
  --max-results 5 --query 'Events[].[EventTime,EventName,CloudTrailEvent]' --output text | cut -c1-120
```

```
12abc34d567e8fa901bc2d34e56789f0
5cbf2a1e9d0b4c7e8f6a3b2c1d0e9f8a
CryptoCurrency:EC2/BitcoinTool.B!DNS	8.0	i-0f9e8d7c6b5a40001	412
2026-10-03T03:58:12+05:30	RunInstances	{"eventVersion":"1.10","userIdentity":{"type":"IAMUser","principalId":"AIDA...
2026-10-03T03:57:40+05:30	CreateAccessKey	{"eventVersion":"1.10","userIdentity":{"type":"IAMUser","principalId":"AIDA...
2026-10-03T03:57:31+05:30	ListBuckets	{"eventVersion":"1.10","userIdentity":{"type":"IAMUser","principalId":"AIDA...
```

→ GuardDuty reports an instance querying crypto-mining domains (severity 8), and CloudTrail shows the
leaked key listing buckets, **creating a new access key** (persistence) and launching instances.
Containment must include the new key, not just the leaked one.

**Hands-on lab (test VM / sandbox account only)**

**Step 1 — Build it.** Enable GuardDuty in the sandbox (free trial period) and generate sample
findings with `aws guardduty create-sample-findings --detector-id DETECTOR_ID`.

**Step 2 — Break it (tabletop).** Scenario: a developer pushed `ci-legacy`'s key to a public GitHub
repo 40 minutes ago. Run the playbook against your sandbox with the fake key from section 2, writing
every command and timestamp in an incident doc.

**Step 3 — Fix it.** Containment checklist: deactivate the key and any keys created by it; revoke
sessions of roles it could assume; list and stop (not terminate) unknown instances in **every**
region; snapshot their volumes; check IAM for new users, roles and policies; rotate secrets the key
could read; then write the postmortem and replace the key with OIDC (section 10).

> ⚠️ Deleting the attacker's resources or the leaked user immediately feels right and destroys
> evidence (and sometimes the trail of what else they touched). Safer order: deactivate and isolate,
> snapshot and export CloudTrail, then delete, with the incident lead's agreement.

**How it breaks**

| Failure | Symptom | First command | Go to |
|---|---|---|---|
| Only the leaked key revoked | Attacker returns with a key they created | CloudTrail `CreateAccessKey`, `CreateUser` by that key | this topic |
| Searching one region | Miners keep running elsewhere | region loop from section 1 | section 1 |
| Instance terminated first | No evidence of how it was compromised | snapshot before terminate | this topic |
| No GuardDuty or trail | Breach discovered from the bill | enable both org-wide | "Landing zones at scale" |
| Root account compromised | Attacker changes root email and MFA | contact AWS Support immediately; centralized root access | section 2 |

**Why it matters for troubleshooting.** A security incident is an outage of trust with an active
adversary. The same evidence-first method applies, but the order changes: contain and preserve
first, explain later. Rehearsing it as a tabletop is what makes that order automatic.

**Next step:** turning all of this into a certification and career path.

---

## 14. Certifications and stages

> 📚 **Study path:** 1) Note: [Career ladder](40-career-ladder.md), "Certifications in order", which places these exams among CKA, Terraform and CKS · 2) KodeKloud: *AWS Certified Cloud Practitioner (CLF-C02)* only for a true beginner ([link](https://kodekloud.com/courses/aws-cloud-practitioner-clf-c02)) · 3) KodeKloud: *AWS Certified CloudOps Engineer - Associate* for the operations associate exam ([link](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 4) KodeKloud: *HashiCorp Certified: Terraform Associate 004* ([link](https://kodekloud.com/courses/hashicorp-certified-terraform-associate-004)) · 5) KodeKloud courses for Solutions Architect – Associate and DevOps Engineer – Professional are not in the verified map, so check the current catalog · 6) Practice: the exit tests in section 15 before you book any exam

Tags: all stages.

A certificate proves you studied a syllabus; the exit tests and a public repository of labs prove
you can do the work. Use certifications as structure and as a recruiter keyword, in the order that
matches your stage, and never instead of the labs.

### Certification path

**Level:** all stages · about 20 minutes to plan

The AWS ladder, mapped to the handbook's career stages:

| Certification | AWS level | Career stage | What it proves | Take it when |
|---|---|---|---|---|
| Cloud Practitioner (CLF-C02) | Foundational | Fresher [L0 · Fresher] | Vocabulary, pricing, shared responsibility | Only if you are new to IT or need a first badge; otherwise skip, the associate exams cover it |
| Solutions Architect – Associate | Associate | Junior → Mid [L1 · Junior] → [L2 · Mid] | Designing across VPC, EC2, S3, RDS, IAM; the most-searched AWS keyword | After sections 1–9 and the Junior exit test |
| CloudOps Engineer – Associate (formerly SysOps Administrator – Associate) | Associate | Mid [L2 · Mid] | Operating, monitoring, troubleshooting, networking and cost; closest to this module | After the Mid-level exit test; it has a verified KodeKloud course |
| DevOps Engineer – Professional | Professional | Senior [L3 · Senior] | CI/CD, IaC, monitoring, incident response and governance at scale | After you have built sections 9–11 for real |
| Advanced Networking – Specialty, Security – Specialty, Solutions Architect – Professional | Specialty / Professional | Senior → Lead [L3 · Senior] → [L4 · Lead/SRE] | Deep hybrid networking, security or architecture | Only if your role centres on that area |

Exam codes and names change (CloudOps replaced SysOps in 2025); check the AWS Certification pages
before you book, and remember AWS certifications expire after three years.

**Your order** (consistent with the [career ladder](40-career-ladder.md)): finish **CKA** first, it is
your current track. Then the Terraform Associate, because once you can write Terraform every AWS lab
becomes code you apply in the evening and destroy before bed. Then **one** associate exam:
Solutions Architect if you are job-hunting (recruiters filter on it), CloudOps if you operate AWS
day to day (it matches this module and has the verified KodeKloud course). DevOps Engineer –
Professional comes later and only if your platform lives on AWS.

Pair every certificate with proof in a public repository: the section 3 VPC in Terraform, the GitLab
OIDC pipeline from section 10, the ALB 502 drill write-up from section 6, and a DR game-day postmortem
from section 13. Interviewers ask about those, not about exam scores.

### Stage-by-stage skills matrix

**Level:** all stages · use it for self-assessment every quarter

Mark each cell for yourself as "can do alone", "with help" or "not yet". The cell text is what the
stage expects.

| Area | Fresher [L0] | Junior [L1] | Mid [L2] | Senior [L3] | Lead/SRE [L4] |
|---|---|---|---|---|---|
| Account and identity | Sandbox with MFA and budget; `get-caller-identity` habit | SSO profiles, roles for instances, key rotation | Debug AccessDenied from the message, CloudTrail and simulator | Organizations, SCPs, permission sets, OIDC roles | Landing-zone identity design, break-glass, audits |
| Network | Explain VPC, subnet, IGW, SG | Build public/private subnets, NAT, SG vs NACL | Timeout drill with Reachability Analyzer and Flow Logs; endpoints | CIDR plan, TGW, VPN, hybrid DNS | Network account, DX resilience, segmentation policy |
| Compute and storage | Launch and connect to EC2 | User data, SSM, EBS resize, snapshots | Credits/steal, IMDSv2, status checks, EBS limits | Golden AMIs, ASGs with instance refresh | Capacity and quota strategy across accounts |
| Data | Upload to S3 from the CLI | Versioning, lifecycle, BPA | Bucket policy and KMS debugging; RDS failover and PITR drills | Encryption and key ownership model; DR copies | RTO/RPO policy, data governance |
| Delivery | — | Push to ECR | ECS stopped reasons, ALB reason codes | EKS operations, Terraform state, GitLab OIDC | Platform templates, golden paths for teams |
| Observability | Find a metric in the console | Alarms to SNS, CloudWatch agent | CloudTrail and Config for "what changed" | Org trail, Config rules, EventBridge alerting | SLOs and alert strategy, incident command |
| Cost | Budget alarm, teardown hunt | Read the bill by service and tag | Find NAT, cross-AZ and idle charges | Rightsizing, Spot, commitments | FinOps practice, unit economics |
| Architecture | Explain regions, AZs, shared responsibility | Map on-prem to AWS | Explain failures by layer with evidence | Multi-AZ and hybrid designs, ADRs | Well-Architected reviews, DR strategy, game days |

**Next step:** prove each stage with its exit test.

---

## 15. Self-check and exit tests

> 📚 **Study path:** 1) Practice first: run each timed task in your sandbox or the [AWS Playground](https://kodekloud.com/cloud-playgrounds/aws), without notes, then check yourself against the referenced section · 2) KodeKloud: [100 Days of Cloud](https://kodekloud.com/100-days-of-cloud) as daily warm-ups between attempts · 3) Note: [AWS reference](16-aws-cloud.md) is the only document allowed open during the timed tasks, just as in an incident · 4) Video: none needed; if a question stumps you, reread its section

Tags: one test per stage, from [L0 · Fresher] to [L4 · Lead/SRE].

How to use the tests: answer the questions out loud or in writing, in your own words, then check
against the section named in brackets. Do the timed tasks in a sandbox account (budget alarm on) or
the KodeKloud playground. You pass a stage when every question is answered correctly and every task
is done within its time, without help. Tear down after every attempt and write the five-line note
(symptom, first wrong guess, deciding evidence, fix, what to check first next time).

### Fresher exit test

**Level:** [L0 · Fresher]

Questions:

1. What is the difference between a region and an AZ, and why does a subnet live in exactly one AZ?
   (section 1, section 3)
2. Name three things AWS is responsible for and three you are responsible for on an EC2 instance.
   (section 1)
3. Why can `aws ec2 describe-instances` return an empty list when your instance is running? (section 1)
4. What is a budget alarm, and does it stop resources when it fires? (section 0)
5. What does `aws sts get-caller-identity` tell you, and why run it first? (section 0, section 2)
6. Why should the root user have MFA and no access keys? (section 0)
7. What is the difference between S3 and an EBS volume? (sections 4 and 5)

Timed tasks:

1. **15 minutes.** From a fresh sandbox: confirm MFA on root, a monthly budget with alerts, and an
   SSO CLI profile that shows an assumed-role ARN in `get-caller-identity`.
2. **15 minutes.** Launch a t3.micro Ubuntu 24.04 from the SSM parameter AMI, connect with Session
   Manager (no port 22), run `ip -br addr` and `resolvectl status`, and explain every line.
3. **10 minutes.** Run the teardown hunt and the all-regions loop; prove nothing is left running.

### Junior exit test

**Level:** [L1 · Junior]

Questions:

1. What makes a subnet "public"? What does a NAT gateway do that an IGW does not? (section 3)
2. Why does a NACL need an outbound rule for ports 1024–65535 when an SG does not? (section 3)
3. What is the difference between `s3:ListBucket` and `s3:GetObject` resources in a policy?
   (section 2)
4. How do you undo an accidental delete in a versioned bucket? (section 5)
5. What are the three conditions for an instance to appear in Session Manager? (section 4)
6. Why does a `curl` to your ALB return a 503 with `server: awselb/2.0`? (section 6)
7. Which EC2 metrics do not exist without the CloudWatch agent? (section 9)
8. What does an alias record do that a CNAME cannot? (section 6)

Timed tasks:

1. **30 minutes.** Build the section 3 VPC (two AZs, public and private subnets, no NAT) with an
   S3 gateway endpoint and the three SSM interface endpoints, and reach a private instance through
   Session Manager.
2. **30 minutes.** Put Apache on port 81 behind an internet-facing ALB with an ACM certificate,
   health check `/health`, and an alias record. `curl -I https://app1.example.com` returns 200.
3. **15 minutes.** Grow a mounted 20 GiB gp3 volume to 40 GiB with 6,000 IOPS without unmounting it,
   and show the new size in `df -h`.
4. **10 minutes.** Create an alarm on `mem_used_percent` above 90% that emails you, and prove the
   notification path with `set-alarm-state`.

### Mid-level exit test

**Level:** [L2 · Mid]

Questions:

1. Walk the policy evaluation order. Why can `AdministratorAccess` still be denied? (section 2)
2. A private instance cannot reach SSM after someone removed the NAT gateway. List two fixes and
   their cost implications. (sections 3 and 12)
3. Flow Logs show inbound ACCEPT and outbound REJECT for the same flow. What is wrong? (section 3)
4. A t3 instance became slow at the same time every day and `st` is high. Explain it. (section 4)
5. Containers on an instance get "Unable to locate credentials", the host does not. Why? (section 4)
6. What do `Target.ResponseCodeMismatch`, `Target.Timeout` and `Target.FailedHealthChecks` each
   point to? (section 6)
7. Why do sporadic ALB 502s happen with healthy targets, and what is the Apache fix? (section 6)
8. After an RDS Multi-AZ failover completed, the app stayed down for 20 minutes. Where do you look?
   (section 7)
9. What is the difference between an ECS task execution role and a task role? (section 8)
10. Which two services answer "who changed this security group, and what did it look like before"?
    (section 9)

Timed tasks:

1. **10 minutes each.** Have someone (or a script) create three AccessDenied problems for a role: a
   missing identity Allow, a permissions boundary and a KMS key policy. Name the policy type and fix
   each in under 10 minutes using the error text, CloudTrail and the simulator.
2. **20 minutes.** Run the section 3 drill "EC2 site times out" against a break someone else
   injected (SG, NACL, route or UFW), ending with a verified fix and a rollback note.
3. **20 minutes.** Run the section 6 drill "ALB returns 502 or 503" against an injected break.
4. **45 minutes.** RDS point-in-time restore of one deleted table into the live database, with a
   measured RTO written down.
5. **15 minutes.** Read an ECS service whose tasks never start, quote the `stoppedReason`, and fix it.

### Senior exit test

**Level:** [L3 · Senior]

Questions:

1. Present an IP plan for three VPCs, on-prem 192.168.10.0/24, Dokploy's Swarm pools and the
   homelab pod CIDR, and defend every choice. (section 3)
2. When do you choose peering, Transit Gateway or PrivateLink? (section 3)
3. Design the trust policy for a GitLab production deploy role. Why must the `sub` condition be
   exact? What changes if GitLab is only reachable on your LAN? (section 10)
4. A region allow-list SCP broke IAM changes. What did its author forget? (section 2)
5. Explain how a VPN tunnel can be `UP` while no traffic flows. (section 11)
6. Draw hybrid DNS for `corp.example.com` and `aws.example.com` in both directions. (section 11)
7. Name four EKS-specific causes of Kubernetes symptoms that kubeadm does not have. (section 8)
8. Who should own KMS keys for backups, and why might the backup writer not have `kms:Decrypt`?
   (section 5)

Timed tasks:

1. **2 hours.** Rebuild the section 3 VPC, the ALB and an ASG from Terraform with an S3 backend and
   lock file, applied by a GitLab pipeline through OIDC, with no static keys anywhere.
2. **90 minutes.** Bring up a Site-to-Site VPN with BGP to a strongSwan box, both tunnels, route
   propagation, and Resolver endpoints so that each side resolves the other's zone. Prove failover by
   killing one tunnel.
3. **60 minutes.** In an EKS playground cluster: fix an unauthorized IAM user with an access entry,
   install the EBS CSI add-on so a PVC binds, and explain the pod limit of the node type.
4. **30 minutes.** A one-page cost review of a sandbox month: top three lines, two waste findings
   with commands, and one design change.

### Lead and SRE exit test

**Level:** [L4 · Lead/SRE]

Questions:

1. Run a Well-Architected review of your on-prem Dokploy platform and of its AWS DR design. Which
   three high-risk issues come first, and why? (section 13)
2. Choose a DR strategy for each of three workloads (marketing site, internal wiki, customer
   database) with RTO, RPO and monthly cost, and defend them to a manager. (section 13)
3. Design the landing zone for 15 accounts, including where the VPN, the log archive and the GitLab
   OIDC roles live. (section 13)
4. A key leaked 40 minutes ago. Give the first ten actions, in order, with the reason for that order.
   (section 13)
5. Present a Savings Plan recommendation with coverage and utilization targets, and the risks of
   over-committing. (section 12)

Timed tasks:

1. **Half a day.** Run a game day: fail the on-prem primary, fail over to the AWS pilot light,
   measure RTO and RPO, fail back, and write the blameless postmortem.
2. **2 hours.** Lead a tabletop of the leaked-key incident with two colleagues: assign incident
   commander, operations and communications roles; produce the timeline and the follow-up actions.
3. **One week (elapsed).** Write an ADR for "AWS as DR site for the on-prem platform", get it
   reviewed by a peer, and present the cost per month and the measured RTO.

---

## 16. Where to go next

> 📚 **Study path:** 1) KodeKloud: *AWS Certified CloudOps Engineer - Associate* once CKA is done ([link](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate)) · 2) KodeKloud: *HashiCorp Certified: Terraform Associate 004* ([link](https://kodekloud.com/courses/hashicorp-certified-terraform-associate-004)) · 3) Note: the modules below, by stage · 4) Practice: [100 Days of Cloud](https://kodekloud.com/100-days-of-cloud) as your morning rep

Pick the next step for your stage:

| If you are | Do next | Why |
|---|---|---|
| Fresher [L0] | [AWS reference](16-aws-cloud.md) sections 1–4, then [Learn: Linux](27-learn-linux.md) and [Learn: Networking](28-learn-networking.md) | AWS is Linux and networking with an API on top |
| Junior [L1] | [Site down](25-playbook-site-down.md) and [Network speed](24-playbook-network-speed.md), applied to your lab VPC | The layered walk works the same in a VPC |
| Mid-level [L2] | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md), then rebuild sections 3–9 as Terraform | Move from clicking to code |
| Senior [L3] | [Security & DevSecOps](37-learn-security-devsecops.md) and [Learn: Databases for DevOps](38-learn-databases-ops.md) | Own the security and data layers of the platform |
| Lead/SRE [L4] | [Senior architecture](39-learn-senior-architecture.md) and [Deployment patterns](35-deployment-patterns.md) | Design, DR and change management across on-prem and AWS |
| Any stage | [Career ladder](40-career-ladder.md) and the [Roadmap](34-roadmap.md) | See how this module fits your whole path |

For your real environment, the most valuable single project from this module is the hybrid DR
design from section 13: on-prem Apache and Dokploy stay primary, Harbor replicates to ECR, backups go
to a versioned and locked S3 bucket, and an ALB pilot light in ap-south-1 is reachable through a
Route 53 failover record. It exercises IAM, VPC, ALB, Route 53, RDS or backups, ECR, IaC, cost and DR
in one design, and it is the story you will tell in a senior interview alongside your Apache 81/444
to Traefik migration from [Case: Apache 443 & Dokploy](21-case-apache-443-dokploy.md).
