# 50 — Real-World Problems: AWS, Terraform/OpenTofu, Ansible & Proxmox

This module is a problem library for the infrastructure under your apps: AWS accounts, Terraform and OpenTofu code, Ansible runs, Proxmox VE clusters and the Packer templates that feed them. It collects 40 problems that people really hit. They come from the most-viewed HashiCorp Discuss and Proxmox forum threads, GitHub issues sorted by comments and reactions, the AWS, HashiCorp, Ansible and Proxmox troubleshooting pages, and public postmortems; Stack Overflow and Reddit are reachable through search links. The fundamentals live in [Cloud & AWS](36-learn-cloud-aws.md) and [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md); this module assumes them and goes straight to what breaks. Every command is documented for you to run in your own lab. Nothing here was executed on a live system.

---

## 0. How to use this module

Infrastructure problems differ from application problems in one way: the blast radius. A wrong `terraform apply` or a careless Ansible run touches many machines at once, so every entry here ends with a guardrail, not only a fix. Use the part that matches your stage, then move up.

| Stage | Level | Read first | You are there when |
|---|---|---|---|
| Fresher | L0 Foundations | entries 1.1 and 7.1, then section 1 | you reach a new EC2 instance and a new Proxmox host, and can say why the first attempt failed |
| Junior | L1 Operator | every entry tagged L1, starting with 1.2, 3.1, 5.1 and 8.1 | you fix AccessDenied, a backend mix-up, an UNREACHABLE host and a locked VM without help |
| Mid-level | L2 Troubleshooter | sections 2, 4, 6 and 8 | you explain any plan diff, ALB 5xx or failed backup from evidence alone |
| Senior | L3 Platform | entries 3.4, 4.4, 4.5, 6.5, 8.4 and 9.4 | GitLab CI plans and applies Terraform with locking, secrets kept out of state and a gate on deletes |
| Senior/Lead | L4 SRE | entries 6.6, 2.5 and 7.4, then the Self-check | you design the guardrails others rely on: batches and canaries, prevent_destroy, budgets, quorum |

**How each problem entry is laid out:** a one-line card (what you see, where, level and career stage, how common it is), then *Why it happens*, *Diagnose* (commands with a realistic sample output), *What the output tells you*, *Fix*, *Why this fix works* (including what not to do), *Prevent it*, *Next step* (handbook module, KodeKloud course, docs) and *Community threads* (verified links plus search links).

**How to practise:** three cheap labs cover the whole module. First, an AWS sandbox account with a Budgets alert set on day one and everything built with Terraform, so `terraform destroy` cleans up after each session. Second, a Proxmox lab: three small nested VMs or old PCs, so you can break quorum, plus one VM for Proxmox Backup Server. Third, an Ansible control node (a VM with ansible-core in a virtualenv) and three cloud-init clones as targets. Snapshot first, break one thing on purpose, fix it using only the entry, then write a five-line note: symptom, evidence, cause, fix, prevention. Never practise on production, and never practise `force-unlock`, `pvecm expected` or `-target` on shared state.

**Placeholders and examples:** UPPERCASE words are placeholders (ACCOUNT_ID, ROLE_ARN, BUCKET, VMID, NODE, LOCK_ID, TG_ARN). The examples use AWS account 111122223333 in eu-west-1, a VPC 10.20.0.0/16, your admin address 198.51.100.7, public addresses from 203.0.113.0/24, Proxmox nodes pve1 to pve3 on 192.0.2.11 to 192.0.2.13, a Proxmox Backup Server on 192.0.2.30, Ansible targets on 10.10.0.0/24, the users ops and deploy, and names under example.com.

**Versions this module assumes (October 2026):** Terraform 1.15, OpenTofu 1.12, ansible-core 2.21, Proxmox VE 9.x on Debian 13, Packer 1.10 or later with external plugins, and AWS CLI v2. Where behaviour changed between versions, the entry says so.

> 📚 **Study path:** KodeKloud *Crash Course: AWS Basics*, free ([course](https://kodekloud.com/courses/crash-course-aws-basics)) → *AWS Networking Fundamentals* ([course](https://kodekloud.com/courses/aws-networking-fundamentals)) → *Terraform Basics Training Course* — Terraform State, Remote State ([course](https://kodekloud.com/courses/terraform-basics-training-course)), then the free *Terraform Challenges* ([course](https://kodekloud.com/courses/terraform-challenges)) → *Ansible Basics Course* ([course](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course), free [Ansible playground](https://kodekloud.com/playgrounds/playground-ansible)) → handbook [Cloud & AWS](36-learn-cloud-aws.md) and [CI/CD, IaC & SRE: Ansible and Terraform](33-learn-cicd-iac-sre.md) → docs: [AWS](https://docs.aws.amazon.com/), [Terraform](https://developer.hashicorp.com/terraform/docs), [OpenTofu](https://opentofu.org/docs/), [Ansible](https://docs.ansible.com/), [Proxmox VE](https://pve.proxmox.com/pve-docs/) → lab: the three labs above, then the Self-check. KodeKloud has no Proxmox or Packer course, so for those use the Proxmox docs, the [Packer docs](https://developer.hashicorp.com/packer/docs) and your homelab.

The problem library starts here. Sections 1 and 2 cover AWS, 3 and 4 Terraform and OpenTofu, 5 and 6 Ansible, 7 and 8 Proxmox VE, and 9 the template and image pipeline that ties them together. Each section runs from common to advanced, and each entry stands on its own.

---

## 1. AWS access: SSH, IAM and credentials

### 1.1 Can't SSH into a new EC2 instance

> **Seen as:** `Permission denied (publickey).` · `ssh: connect to host 203.0.113.25 port 22: Connection timed out` · `WARNING: UNPROTECTED PRIVATE KEY FILE!` · **Where:** your first EC2 instances, a new VPC, an instance moved to another subnet · **Level:** [L0 · Fresher] · **How common:** AWS keeps one troubleshooting page with more than ten separate SSH errors; one of the most-asked EC2 questions everywhere

**Why it happens:** the two error families point at different layers. *Timed out* means the packets never got an answer: the security group doesn't allow 22 from your current address, the subnet's route table has no 0.0.0.0/0 route to an internet gateway, the instance has no public IP, or a custom NACL drops the return traffic on ephemeral ports 1024–65535. *Permission denied* means the network works and authentication fails: the wrong login user (ubuntu on Ubuntu AMIs, ec2-user on Amazon Linux, admin on Debian), the wrong key, or a key file readable by others, which OpenSSH refuses to use.

**Diagnose:**

```bash
# From your laptop: refused, denied or timed out?
nc -vz -w 5 203.0.113.25 22
# What AWS thinks: public IP, key pair, subnet, security group
aws ec2 describe-instances --instance-ids i-0abc1234def567890 \
  --query 'Reservations[].Instances[].[PublicIpAddress,KeyName,SubnetId,SecurityGroups[0].GroupId]' --output text
# Who may reach port 22, and does the subnet route to an internet gateway?
aws ec2 describe-security-groups --group-ids sg-0a1a1a1a1a1a1a1a1 \
  --query 'SecurityGroups[].IpPermissions[?ToPort==`22`].IpRanges[].CidrIp' --output text
# (no routes printed? the subnet uses the VPC's main route table implicitly:
#  filter on Name=vpc-id,Values=VPC_ID Name=association.main,Values=true instead)
aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=subnet-0e9d8c7b6a5f40312 \
  --query 'RouteTables[].Routes[].[DestinationCidrBlock,GatewayId]' --output text
# Your address as AWS sees it
curl -s https://checkip.amazonaws.com
```

```text
nc: connect to 203.0.113.25 port 22 (tcp) timed out: Operation now in progress
203.0.113.25    lab-key    subnet-0e9d8c7b6a5f40312    sg-0a1a1a1a1a1a1a1a1
198.51.100.4/32
10.20.0.0/16    local
0.0.0.0/0       igw-0f1e2d3c4b5a69788
198.51.100.7
```

**What the output tells you:** a timeout, not a refusal, so the packets are dropped before sshd sees them. The instance has a public IP and its subnet routes 0.0.0.0/0 to an internet gateway, so routing is fine. The security group only allows 198.51.100.4/32, the address your provider gave you last week; today you are 198.51.100.7. Had nc said `succeeded` and ssh said `Permission denied (publickey)`, you would check the user name and the key instead: `ssh -v` shows which key was offered.

**Fix:**

```bash
# Allow 22 from the address you have now, and remove the stale rule
MYIP=$(curl -s https://checkip.amazonaws.com)
aws ec2 authorize-security-group-ingress --group-id sg-0a1a1a1a1a1a1a1a1 \
  --protocol tcp --port 22 --cidr "${MYIP}/32"
aws ec2 revoke-security-group-ingress --group-id sg-0a1a1a1a1a1a1a1a1 \
  --protocol tcp --port 22 --cidr 198.51.100.4/32
# Permission denied instead? Right user, and a key only you can read
chmod 400 ~/.ssh/lab-key.pem
ssh -i ~/.ssh/lab-key.pem ubuntu@203.0.113.25
# Better: no port 22 at all (instance profile with AmazonSSMManagedInstanceCore,
# Session Manager plugin installed on your laptop)
aws ssm start-session --target i-0abc1234def567890
```

**Why this fix works:** security groups are stateful allow-lists on each network interface, so one correct rule for your current /32 is enough and the replies flow back automatically. `chmod 400` satisfies OpenSSH's check that a private key isn't readable by others. Session Manager goes further: the SSM agent on the instance dials out to AWS over 443, so no inbound port, public IP or key pair is needed, and every session is logged. Don't "fix" it by opening 22 to 0.0.0.0/0: internet-wide scanners find it within minutes.

**Prevent it:** keep security groups and routes in Terraform, use Session Manager or EC2 Instance Connect by default, and give admins a VPN or a fixed office range instead of home addresses that change.

**Next step:** [Cloud & AWS: Security groups vs NACLs](36-learn-cloud-aws.md#security-groups-vs-nacls) · [Cloud & AWS: SSM Session Manager](36-learn-cloud-aws.md#ssm-session-manager) · [SSH & remote access](09-ssh-remote-access.md) · KodeKloud: *AWS Networking Fundamentals* — security groups and routing · [AWS: Troubleshoot connecting to your Linux instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstancesConnecting.html)

**Community threads:** [AWS: Troubleshoot connecting to your Linux instance](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/TroubleshootingInstancesConnecting.html) · Search: [Server Fault](https://serverfault.com/search?q=ec2+ssh+%22Permission+denied+%28publickey%29%22) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=ec2+ssh+connection+timed+out&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=ec2+ssh+connection+timed+out+security+group)

### 1.2 AccessDenied from IAM, S3 or KMS

> **Seen as:** `User: arn:aws:sts::111122223333:assumed-role/gitlab-deploy/ci is not authorized to perform: s3:PutObject on resource: "arn:aws:s3:::example-artifacts/app.tar.gz" because no identity-based policy allows the s3:PutObject action` · `An error occurred (AccessDenied) when calling the GetObject operation: Access Denied` · `AccessControlListNotSupported: The bucket does not allow ACLs` · **Where:** the AWS CLI, Terraform or a CI job calling an API · **Level:** [L1 · Junior] · **How common:** the most common AWS error for newcomers; IAM and S3 each keep a dedicated troubleshooting page, and the S3 one lists more than ten separate causes

**Why it happens:** AWS allows a call only if some policy allows it and no policy denies it, and the end of the message names the layer that said no. "no identity-based policy allows" is an implicit deny: the role has no Allow for that action on that exact ARN (s3:ListBucket matches the bucket ARN, object actions match `bucket/*`). "with an explicit deny in a service control policy" (or a resource-based policy, permissions boundary, session policy or VPC endpoint policy) means a Deny somewhere, and a Deny always wins. S3 adds its own layers: the bucket policy (often a Deny on `aws:SecureTransport` or `aws:SourceVpce`), Object Ownership "Bucket owner enforced" (the default for new buckets since April 2023), which disables ACLs so any `--acl` or `aws_s3_bucket_acl` fails, and SSE-KMS encryption, which also needs `kms:GenerateDataKey` (writes) or `kms:Decrypt` (reads) on the key. Cross-account calls still get a bare "Access Denied", and GetObject on a missing key returns 403 instead of 404 when the caller lacks s3:ListBucket. Finally, you may simply be calling as someone else: a stale AWS_PROFILE or old keys in environment variables.

**Diagnose:**

```bash
# 1. Who am I really?
aws sts get-caller-identity --query Arn --output text
# 2. Would the role's own policies allow it?
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::111122223333:role/gitlab-deploy \
  --action-names s3:PutObject --resource-arns arn:aws:s3:::example-artifacts/app.tar.gz \
  --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output text
# 3. The S3 layers: bucket policy, ownership controls, default encryption
aws s3api get-bucket-policy --bucket example-artifacts --query Policy --output text \
  | jq -c '.Statement[] | {Sid, Effect, Action, Condition}'
aws s3api get-bucket-ownership-controls --bucket example-artifacts \
  --query 'OwnershipControls.Rules[0].ObjectOwnership' --output text
aws s3api get-bucket-encryption --bucket example-artifacts \
  --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault' --output text
# EC2 "Encoded authorization failure message"? Decode it
aws sts decode-authorization-message --encoded-message "$MSG" --query DecodedMessage --output text | jq .
```

```text
arn:aws:sts::111122223333:assumed-role/gitlab-deploy/ci
s3:PutObject    implicitDeny
{"Sid":"TLSOnly","Effect":"Deny","Action":"s3:*","Condition":{"Bool":{"aws:SecureTransport":"false"}}}
BucketOwnerEnforced
arn:aws:kms:eu-west-1:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab    aws:kms
```

**What the output tells you:** you are the role you expected, and the simulator says implicitDeny: the role's policies contain no Allow for s3:PutObject on that object ARN, which matches the "no identity-based policy allows" clause. The bucket policy only denies plain-HTTP requests, which the CLI never sends, so it isn't the cause. Two more layers are waiting: ACLs are disabled (BucketOwnerEnforced), so a job that passes `--acl` will fail next, and the bucket encrypts with a KMS key, so the role also needs `kms:GenerateDataKey` on that key. The simulator ignores resource policies unless you pass them with `--resource-policy`; an SCP or VPC endpoint policy that denies is named in the error message itself.

**Fix:**

```bash
# Least-privilege Allow with the right ARN shapes, plus the KMS key
cat > artifacts-rw.json <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::example-artifacts" },
    { "Effect": "Allow", "Action": ["s3:GetObject", "s3:PutObject"],
      "Resource": "arn:aws:s3:::example-artifacts/*" },
    { "Effect": "Allow", "Action": ["kms:GenerateDataKey", "kms:Decrypt"],
      "Resource": "arn:aws:kms:eu-west-1:111122223333:key/1234abcd-12ab-34cd-56ef-1234567890ab" }
  ]
}
EOF
aws iam put-role-policy --role-name gitlab-deploy --policy-name artifacts-rw \
  --policy-document file://artifacts-rw.json
# AccessControlListNotSupported: stop sending ACLs (drop --acl, remove aws_s3_bucket_acl)
aws s3 cp app.tar.gz s3://example-artifacts/app.tar.gz
# Wrong identity on a laptop: clear stale keys and pick the profile explicitly
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
export AWS_PROFILE=lab
```

**Why this fix works:** an implicit deny only needs a matching Allow, and S3 matches actions against two ARN shapes: bucket-level actions against the bucket, object-level actions against `bucket/*`. The KMS statement works because the default key policy lets IAM policies in the account grant use of the key; a custom key policy may need its own entry. With ACLs disabled, access comes only from policies, so removing ACL arguments removes the error instead of hiding it. An explicit Deny can't be outvoted by any Allow: whoever owns that policy (the org admin for an SCP) has to change it. In real life put the policy in Terraform, not in a one-off CLI call, and don't fix AccessDenied with `"Action": "*"` or AdministratorAccess on a CI role: the next leaked token then owns the account.

**Prevent it:** roles instead of IAM users, one role per pipeline and environment, policies generated from CloudTrail activity with IAM Access Analyzer and tested with the policy simulator in CI, and the bucket, its policy, ownership controls and encryption managed together in one Terraform module.

**Next step:** [Cloud & AWS: Debugging AccessDenied](36-learn-cloud-aws.md#debugging-accessdenied) · [Cloud & AWS: S3 access control](36-learn-cloud-aws.md#s3-access-control) · [Security: Cloud security on AWS](37-learn-security-devsecops.md#10-cloud-security-on-aws) · KodeKloud: *AWS Certified CloudOps Engineer - Associate* — Security domain · [AWS IAM: Troubleshoot access denied error messages](https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html)

**Community threads:** [AWS IAM: Troubleshoot access denied error messages](https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html) · [Amazon S3: Troubleshoot access denied (403 Forbidden) errors](https://docs.aws.amazon.com/AmazonS3/latest/userguide/troubleshoot-403-errors.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22is+not+authorized+to+perform%22+%22because+no+identity-based+policy+allows%22) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=AccessDenied+%22not+authorized+to+perform%22&restrict_sr=1) · [Reddit r/aws (S3 403)](https://www.reddit.com/r/aws/search/?q=s3+403+access+denied&restrict_sr=1)

### 1.3 Unable to locate credentials in containers

> **Seen as:** `Unable to locate credentials. You can configure credentials by running "aws configure".` · `no valid credential sources for Terraform AWS Provider found` · `failed to refresh cached credentials, no EC2 IMDS role found` · `SignatureDoesNotMatch` · **Where:** works on the host but not in a container, works on a laptop but not in CI; GitLab runners and Docker or Dokploy hosts on EC2 · **Level:** [L2 · Mid-level] · **How common:** terraform-provider-aws #14873 on credential validation errors has about 70 comments; AWS documents hop limit 2 for container hosts

**Why it happens:** every SDK walks the same chain: environment variables, then the shared config or SSO profile, then container credentials, then the instance metadata service (IMDS). It fails when nothing in the chain answers, or when an earlier link answers wrongly. With no instance profile attached, IMDS has nothing to give. With IMDSv2 required and a response hop limit of 1, the token reply can't cross the extra hop of a Docker bridge network, so the host works and every container fails. Stale static keys in environment variables override a perfectly good role, an SSO session expires, and clock skew breaks request signatures (SignatureDoesNotMatch, RequestExpired).

**Diagnose:**

```bash
# Which link of the chain answers on the host?
aws configure list
env | grep ^AWS_
# IMDSv2 from the host, then from a container on the default bridge
TOKEN=$(curl -s -X PUT http://169.254.169.254/latest/api/token -H 'X-aws-ec2-metadata-token-ttl-seconds: 60')
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/; echo
docker run --rm curlimages/curl -s -m 3 -X PUT http://169.254.169.254/latest/api/token \
  -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' || echo "no token from inside the container"
# How is the instance configured?
aws ec2 describe-instances --instance-ids i-0abc1234def567890 --query \
  'Reservations[].Instances[].[IamInstanceProfile.Arn,MetadataOptions.HttpTokens,MetadataOptions.HttpPutResponseHopLimit]' --output text
timedatectl | grep synchronized
```

```text
      Name                    Value             Type    Location
      ----                    -----             ----    --------
   profile                <not set>             None    None
access_key     ****************QX7M         iam-role
secret_key     ****************9fKa         iam-role
    region                eu-west-1      config-file    ~/.aws/config
gitlab-runner-role
no token from inside the container
arn:aws:iam::111122223333:instance-profile/gitlab-runner    required    1
System clock synchronized: yes
```

**What the output tells you:** the host gets credentials from its instance profile (Type iam-role, role gitlab-runner-role), no stray AWS_ variables are set, and the clock is fine. A container gets no token at all, and the instance requires IMDSv2 tokens with hop limit 1: that is the hop-limit signature, because the token response is only allowed one network hop and the Docker bridge adds a second. Had `env` printed AWS_ACCESS_KEY_ID, those keys would win over the role; with a broken clock you would see SignatureDoesNotMatch instead of "Unable to locate".

**Fix:**

```bash
# Containers on this host need two hops; keep IMDSv2 required
aws ec2 modify-instance-metadata-options --instance-id i-0abc1234def567890 \
  --http-tokens required --http-put-response-hop-limit 2
# No instance profile at all? Attach one
aws ec2 associate-iam-instance-profile --instance-id i-0abc1234def567890 \
  --iam-instance-profile Name=gitlab-runner
# Laptop or CI: refresh SSO, drop stale keys
aws sso login --profile lab
unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN
```

**Why this fix works:** hop limit 2 lets the token response survive the bridge hop while IMDSv2 keeps blocking the simple GET requests that made IMDSv1 easy to abuse through SSRF. Attaching a profile gives the last link of the chain something to return, and removing stale variables lets the chain fall through to it. Don't switch IMDSv2 off (`--http-tokens optional`) to make containers work, and don't bake static keys into images or Dokploy environment variables.

**Prevent it:** set hop limit 2 in the launch template of every container host, and use no static keys anywhere: instance roles on EC2, and in GitLab CI OIDC `id_tokens` with AssumeRoleWithWebIdentity. Keep NTP healthy on every host.

**Next step:** [Cloud & AWS: IMDSv2](36-learn-cloud-aws.md#imdsv2) · [Cloud & AWS: GitLab CI to AWS with OIDC](36-learn-cloud-aws.md#gitlab-ci-to-aws-with-oidc) · [AWS command reference](16-aws-cloud.md) · KodeKloud: *AWS Certified CloudOps Engineer - Associate* — Security domain · [AWS: Configure instance metadata options for new instances](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-IMDS-new-instances.html)

**Community threads:** [terraform-provider-aws #14873](https://github.com/hashicorp/terraform-provider-aws/issues/14873) · [AWS: Configure instance metadata options](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/configuring-IMDS-new-instances.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+container+ec2+imdsv2+hop+limit+credentials) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=imdsv2+docker+hop+limit&restrict_sr=1)

---

## 2. AWS networking, storage and cost

### 2.1 Private subnet can't reach the internet

> **Seen as:** `Could not connect to eu-west-1.ec2.archive.ubuntu.com:80 (203.0.113.81), connection timed out` · `dial tcp 203.0.113.80:443: i/o timeout` on image pulls · **Where:** app servers or GitLab runners in a private subnet behind a NAT gateway · **Level:** [L1 · Junior] · **How common:** "Instances cannot access the internet" is a top item on AWS's NAT gateway troubleshooting page; a classic VPC beginner trap

**Why it happens:** a private instance reaches the internet through three pieces in order, the same walk as on-prem. Its subnet's route table must send 0.0.0.0/0 to a NAT gateway; that NAT gateway must sit in a public subnet whose own route table sends 0.0.0.0/0 to the internet gateway; and the security group and NACLs must let the traffic out and the replies back. The classic mistakes: the NAT gateway created in a private subnet, so it has no way out itself; the private route table still pointing at nothing or straight at the IGW; a custom NACL that forgot ephemeral ports 1024–65535 for return traffic (NACLs are stateless); or SG egress removed. A quieter one: NAT gateways drop connections that stay idle for 350 seconds, which breaks long-lived idle connections rather than new ones.

**Diagnose:**

```bash
# 1. Where does the private subnet send 0.0.0.0/0?
aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=subnet-0a1b2c3d4e5f60718 \
  --query 'RouteTables[].Routes[].[DestinationCidrBlock,NatGatewayId,GatewayId]' --output text
# 2. Which subnet is the NAT gateway in, and is it available?
aws ec2 describe-nat-gateways --filter Name=vpc-id,Values=vpc-0a1b2c3d4e5f67890 \
  --query 'NatGateways[].[NatGatewayId,SubnetId,State]' --output text
# 3. Does the NAT gateway's subnet route to the internet gateway?
aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=subnet-0b2c3d4e5f6071829 \
  --query 'RouteTables[].Routes[].[DestinationCidrBlock,GatewayId]' --output text
# 4. NACL on the private subnet: inbound rules (return traffic)
aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=subnet-0a1b2c3d4e5f60718 \
  --query 'NetworkAcls[].Entries[?Egress==`false`].[RuleNumber,Protocol,RuleAction]' --output text
```

```text
10.20.0.0/16    None                     local
0.0.0.0/0       nat-0d1c2b3a49586f7e0    None
nat-0d1c2b3a49586f7e0    subnet-0b2c3d4e5f6071829    available
10.20.0.0/16    local
100     -1      allow
32767   -1      deny
```

**What the output tells you:** the private subnet correctly sends 0.0.0.0/0 to the NAT gateway, and the NAT gateway is available, but it sits in subnet-0b2c..., whose route table has only the local route. The NAT gateway translates the source address and then has nowhere to send the packet. The NACL allows all inbound traffic (rule 100), so it isn't the cause here. VPC Reachability Analyzer would draw the same conclusion graphically.

**Fix:**

```bash
# A NAT gateway can't be moved: create one in a PUBLIC subnet, repoint, then delete the old one
aws ec2 create-nat-gateway --subnet-id subnet-0e9d8c7b6a5f40312 --allocation-id eipalloc-0123456789abcdef0
aws ec2 wait nat-gateway-available --nat-gateway-ids nat-0f9e8d7c6b5a43210
aws ec2 replace-route --route-table-id rtb-0c1d2e3f4a5b6c7d8 \
  --destination-cidr-block 0.0.0.0/0 --nat-gateway-id nat-0f9e8d7c6b5a43210
aws ec2 delete-nat-gateway --nat-gateway-id nat-0d1c2b3a49586f7e0
# (then release the old gateway's Elastic IP: it is billed while idle, see 2.5)
# S3 traffic: a free gateway endpoint skips the NAT gateway entirely
aws ec2 create-vpc-endpoint --vpc-id vpc-0a1b2c3d4e5f67890 \
  --service-name com.amazonaws.eu-west-1.s3 --route-table-ids rtb-0c1d2e3f4a5b6c7d8
```

**Why this fix works:** the NAT gateway only rewrites source addresses; the public subnet's route to the internet gateway is what carries the packets out, so its placement is the whole point. The gateway endpoint adds a route for S3's prefix list to the route table, so artifacts, backups and ECR image layers (which are served from S3) skip the NAT data charge. If you use custom NACLs, allow 1024–65535 in both directions and keep the fine-grained filtering in security groups, which are stateful.

**Prevent it:** build VPCs from a tested module (terraform-aws-modules/vpc) instead of by hand, keep NACLs coarse, use VPC Flow Logs or Reachability Analyzer before guessing, and set TCP keepalive below 350 seconds for long idle connections through NAT.

**Next step:** [Cloud & AWS: Route tables, IGW and NAT](36-learn-cloud-aws.md#route-tables-igw-and-nat) · [Cloud & AWS: Flow Logs and Reachability Analyzer](36-learn-cloud-aws.md#flow-logs-and-reachability-analyzer) · [Network speed playbook](24-playbook-network-speed.md) · KodeKloud: *AWS Networking Fundamentals* — gateways and routing · [AWS: Troubleshoot NAT gateways](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-troubleshooting.html)

**Community threads:** [AWS: Troubleshoot NAT gateways](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-troubleshooting.html) · Search: [Server Fault](https://serverfault.com/search?q=aws+private+subnet+nat+gateway+no+internet) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=private+subnet+nat+gateway+no+internet&restrict_sr=1)

### 2.2 Grew the EBS volume, df shows the old size

> **Seen as:** `No space left on device` · `NOCHANGE: partition 1 is size 16775135. it cannot be grown` · `resize2fs: Bad magic number in super-block while trying to open /dev/nvme0n1` · **Where:** an 8 GB root volume filled by Docker images, build caches or logs; data volumes on runners and database hosts · **Level:** [L1 · Junior] · **How common:** the AWS page for extending a filesystem has troubleshooting tips for each command; a very common Server Fault and Ask Ubuntu question

**Why it happens:** `modify-volume` grows only the block device. The partition table and the filesystem inside still describe the old size until you extend each layer: `growpart` for the partition, then `resize2fs` for ext4 (Ubuntu) or `xfs_growfs` for XFS (Amazon Linux). The common slips: running resize2fs on the whole disk instead of the partition (the "Bad magic number" error), using the console's /dev/sda1 or /dev/xvda names on Nitro instances, which expose NVMe names (nvme0n1p1), running growpart on a disk so full that it can't write its temporary files, and trying a second modification within about six hours of the first.

**Diagnose:**

```bash
lsblk -o NAME,SIZE,TYPE,MOUNTPOINT
df -hT /
aws ec2 describe-volumes-modifications --volume-ids vol-0123456789abcdef0 \
  --query 'VolumesModifications[].[ModificationState,OriginalSize,TargetSize]' --output text
sudo du -xh --max-depth=1 / 2>/dev/null | sort -h | tail -4
```

```text
NAME          SIZE TYPE MOUNTPOINT
nvme0n1        30G disk
├─nvme0n1p1   7.9G part /
├─nvme0n1p14    4M part
├─nvme0n1p15  106M part /boot/efi
└─nvme0n1p16  913M part /boot
Filesystem     Type  Size  Used Avail Use% Mounted on
/dev/root      ext4  7.6G  7.6G     0 100% /
optimizing      8       30
412M    /home
1.1G    /usr
5.9G    /var
7.6G    /
```

**What the output tells you:** the disk is already 30G and the modification is in the `optimizing` state, which means the new size is usable now. The partition and the filesystem are still about 8G and full, and /var (Docker data) is what filled them. You need growpart, then resize2fs, and a little room to run them.

**Fix:**

```bash
# 0. Snapshot first, always, before touching partitions
aws ec2 create-snapshot --volume-id vol-0123456789abcdef0 --description "before growpart"
# 1. growpart needs a little free space: make some
sudo journalctl --vacuum-size=200M && sudo apt-get clean
docker system prune -f      # stopped containers, dangling images, unused networks; volumes untouched
# 2. Grow the partition (note the space before the partition number), then the filesystem
sudo growpart /dev/nvme0n1 1
sudo resize2fs /dev/nvme0n1p1          # XFS instead: sudo xfs_growfs -d /
df -h /
```

**Why this fix works:** each layer is extended in order, block device → partition → filesystem, and both growpart and resize2fs work online on a mounted ext4 root. The snapshot is your rollback if the partition table edit goes wrong. Don't make room with `docker system prune -a --volumes`: it removes every unused image and all unused anonymous volumes (and, on Docker before 23.0, unused named volumes too), and an anonymous volume can hold a database's data; `docker volume prune -a` removes unused named volumes on current Docker as well.

**Prevent it:** alarm at 80–85% disk with the CloudWatch agent or node_exporter, rotate Docker logs (`max-size` and `max-file` in daemon.json), and put data on a separate EBS volume mounted by UUID with `nofail`, so a missing volume never blocks boot.

**Next step:** [Storage & disk reference](01-storage-disk.md) · [Cloud & AWS: EBS performance and snapshots](36-learn-cloud-aws.md#ebs-performance-and-snapshots) · [Slow system: Disk I/O](23-playbook-slow-system.md#5-disk-io) · KodeKloud: *Learning Linux Basics Course & Labs* — Storage in Linux · [AWS: Extend the file system after resizing an EBS volume](https://docs.aws.amazon.com/ebs/latest/userguide/recognize-expanded-volume-linux.html)

**Community threads:** [AWS: Extend the file system after resizing an EBS volume](https://docs.aws.amazon.com/ebs/latest/userguide/recognize-expanded-volume-linux.html) · Search: [Server Fault](https://serverfault.com/search?q=ebs+resize+growpart+resize2fs+df+old+size) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=ebs+resize+growpart&restrict_sr=1)

### 2.3 Route 53 has the records, domain doesn't resolve

> **Seen as:** `dig` returns NXDOMAIN, SERVFAIL or an old IP · `curl: (6) Could not resolve host: app.example.com` · **Where:** a new domain, a move from another DNS provider, or a hosted zone that was deleted and recreated · **Level:** [L1 · Junior] · **How common:** AWS keeps a "My domain is unavailable on the internet" page that lists six common causes

**Why it happens:** records in a hosted zone only matter if the parent zone delegates to that hosted zone's name servers. Every hosted zone gets its own set of four name servers, so recreating a zone, or creating a second zone with the same name, produces a new set while the registrar still points at the old one. Delegation is cached at the TLD for up to 48 hours. Inside a VPC, a private hosted zone with the same name hides the public one, and a private zone that isn't associated with the VPC isn't consulted at all. A domain can also be suspended because the registrant email was never confirmed.

**Diagnose:**

```bash
# What do the world and the registrar think the name servers are?
dig +short NS example.com
whois example.com | grep -i 'name server'
# Which hosted zones exist with this name, and what are their name servers?
aws route53 list-hosted-zones-by-name --dns-name example.com \
  --query 'HostedZones[?Name==`example.com.`].[Id,Config.PrivateZone]' --output text
aws route53 get-hosted-zone --id Z0123456789ABCDEFGHIJ --query DelegationSet.NameServers --output text
# Ask the zone you edit directly: is the record there?
dig +short app.example.com @ns-1234.awsdns-26.org
```

```text
ns-401.awsdns-50.com.
ns-1622.awsdns-10.co.uk.
ns-1003.awsdns-61.net.
ns-17.awsdns-02.org.
Name Server: NS-401.AWSDNS-50.COM
Name Server: NS-1622.AWSDNS-10.CO.UK
Name Server: NS-1003.AWSDNS-61.NET
Name Server: NS-17.AWSDNS-02.ORG
/hostedzone/Z0123456789ABCDEFGHIJ    False
/hostedzone/Z0987654321JIHGFEDCBA    False
ns-1234.awsdns-26.org   ns-77.awsdns-09.com   ns-912.awsdns-34.net   ns-1999.awsdns-55.co.uk
203.0.113.40
```

**What the output tells you:** two public hosted zones named example.com exist. The zone you edit (Z0123...) has the record, as the direct query proves, but the registrar delegates to a different set of name servers, those of the old zone Z0987.... Resolvers follow the registrar, so they never see your record.

**Fix:**

```bash
# Route 53 as registrar (the domains API lives in us-east-1): delegate to the zone you use
aws route53domains update-domain-nameservers --region us-east-1 --domain-name example.com \
  --nameservers Name=ns-1234.awsdns-26.org Name=ns-77.awsdns-09.com \
                Name=ns-912.awsdns-34.net Name=ns-1999.awsdns-55.co.uk
# Another registrar: set the same four name servers in its panel.
# Keep a copy of the old zone before removing it (delete only after the new delegation answers)
aws route53 list-resource-record-sets --hosted-zone-id Z0987654321JIHGFEDCBA > old-zone-backup.json
# Private zone not consulted inside the VPC? Associate it
aws route53 associate-vpc-with-hosted-zone --hosted-zone-id Z0PRIVATEZONEEXAMPLE \
  --vpc VPCRegion=eu-west-1,VPCId=vpc-0a1b2c3d4e5f67890
```

**Why this fix works:** resolvers follow the delegation from the TLD, so the answer comes from whichever servers the registrar lists; making those the servers of the zone you edit is the whole fix. Expect the old delegation to linger until the TLD's NS TTL (up to 48 hours) runs out. To remove the duplicate zone you must first delete its non-default records. Don't delete a live zone to "start fresh": that is how this mismatch is usually created.

**Prevent it:** manage the hosted zone and the registrar's name servers in the same Terraform code (feed the zone's `name_servers` output to the registrar resource), lower TTLs a day before planned changes, and run a scheduled `dig` check that alerts when the delegation and the zone disagree.

**Next step:** [DNS reference](08-dns.md) · [Cloud & AWS: Route 53 records and routing](36-learn-cloud-aws.md#route-53-records-and-routing) · KodeKloud: *Demystifying DNS* — DNS as a System (Resolvers, Walking the DNS Tree, TTL) · [Route 53: My domain is unavailable on the internet](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/troubleshooting-domain-unavailable.html)

**Community threads:** [Route 53: My domain is unavailable on the internet](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/troubleshooting-domain-unavailable.html) · Search: [Server Fault](https://serverfault.com/search?q=route53+domain+not+resolving+name+servers) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=route+53+domain+not+resolving&restrict_sr=1)

### 2.4 ALB returns 502, 503 or 504

> **Seen as:** `502 Bad Gateway` · `503 Service Temporarily Unavailable` · `504 Gateway Time-out` · target health `Target.ResponseCodeMismatch` or `Target.Timeout` · **Where:** an Application Load Balancer in front of EC2, ECS, or a Traefik or Dokploy host · **Level:** [L2 · Mid-level] · **How common:** the ALB troubleshooting page lists separate causes for each 5xx; a staple of AWS questions everywhere

**Why it happens:** the ALB is a reverse proxy, and each code names a different failure, just as with Traefik. A 503 means it has no target to send the request to: none registered, either because nothing was ever registered or because ECS or an Auto Scaling group using ELB health checks keeps deregistering and replacing the failing ones. When every registered target fails its health checks, the ALB fails open and sends traffic to all of them anyway, so users get whatever the unhealthy targets answer. Health checks fail when the check path answers 301/302 (an HTTP-to-HTTPS redirect) or 404 (a vhost-based app or Traefik rejecting `Host: 10.20.10.15`), or when the target's security group doesn't allow the ALB's security group on the traffic or health-check port. A 502 means the target answered badly: it closed or reset the connection, often because its keep-alive timeout is shorter than the ALB's idle timeout (60 seconds by default), so the ALB reuses a connection the app has just closed; or the app listens on 127.0.0.1 only. A 504 means the target didn't answer within the idle timeout, or a NACL drops the replies.

**Diagnose:**

```bash
aws elbv2 describe-target-health --target-group-arn "$TG_ARN" --query \
  'TargetHealthDescriptions[].[Target.Id,Target.Port,TargetHealth.State,TargetHealth.Reason,TargetHealth.Description]' \
  --output text
# From another instance in the VPC: what does the health check really get?
curl -s -o /dev/null -D - -H 'Host: 10.20.10.15' http://10.20.10.15:8080/health | grep -E '^(HTTP|Location)'
```

```text
i-0abc1234def567890    8080    unhealthy    Target.ResponseCodeMismatch    Health checks failed with these codes: [301]
i-0def5678abc123456    8080    unhealthy    Target.ResponseCodeMismatch    Health checks failed with these codes: [301]
HTTP/1.1 301 Moved Permanently
Location: https://10.20.10.15/health
```

**What the output tells you:** both targets fail with 301: the app redirects plain HTTP to HTTPS, so the health check never sees a 200 and the target group has no healthy target. The ALB fails open and still forwards requests to both, but an Auto Scaling group using ELB health checks (or ECS) keeps replacing them as unhealthy, and while no target is registered users get 503. A reason of `Target.Timeout` ("Request timed out") would point at the security group or a NACL; `Target.FailedHealthChecks` ("Health checks failed") at a refused or reset connection, such as an app that listens only on localhost. For 502s with healthy targets, compare `elb_status_code` with `target_status_code` in the ALB access logs: a 502 with a target code of `-` means the connection to the target failed or was reset. The CloudWatch pair HTTPCode_ELB_5XX_Count versus HTTPCode_Target_5XX_Count tells you who generated the error.

**Fix:**

```bash
# Give the checker a 200: a cheap /health exempt from the redirect (best), or accept redirects
aws elbv2 modify-target-group --target-group-arn "$TG_ARN" \
  --health-check-path /health --matcher HttpCode=200-399
# Target security group: allow the ALB's security group, not 0.0.0.0/0
aws ec2 authorize-security-group-ingress --group-id sg-0a1a1a1a1a1a1a1a1 \
  --protocol tcp --port 8080 --source-group sg-0b2b2b2b2b2b2b2b2
# 502 under load: app keep-alive longer than the ALB idle timeout (60 s)
#   gunicorn --keep-alive 75   |   nginx: keepalive_timeout 75s;   |   Node.js: server.keepAliveTimeout = 75000
```

**Why this fix works:** the health check only counts codes in the matcher, so either the app gives the checker a 200 or the matcher accepts the redirect; a real /health endpoint is better, because 200-399 also passes a broken app that still redirects. Once the targets pass, they stay registered instead of being replaced, and the 503s stop. Referencing the ALB's security group keeps working when the ALB's IP addresses change, which they do. A keep-alive longer than the idle timeout means the ALB, not the app, always closes idle connections first, so it never reuses one the app already closed. Don't point the health check at a page that queries the database: a slow database then marks every target unhealthy at once.

**Prevent it:** CloudWatch alarms on UnHealthyHostCount and on target 5xx, ALB access logs switched on, and a health endpoint that is cheap but proves the app can serve.

**Next step:** [Cloud & AWS: Health checks and ALB errors](36-learn-cloud-aws.md#health-checks-and-alb-errors) · [Cloud & AWS: Drill: ALB returns 502 or 503](36-learn-cloud-aws.md#drill-alb-returns-502-or-503) · [Site down](25-playbook-site-down.md) · [Traefik deep dive](43-traefik-and-reverse-proxies.md) · KodeKloud: *AWS Networking Fundamentals* — load balancers · [AWS: Troubleshoot your Application Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html)

**Community threads:** [AWS: Troubleshoot your Application Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-troubleshooting.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=aws+alb+502+bad+gateway+target+unhealthy) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=alb+502+unhealthy+targets&restrict_sr=1)

### 2.5 Surprise bill: NAT, public IPv4 and leftovers

> **Seen as:** a Budgets alert, or a bill several times the usual · Cost Explorer shows `EC2-Other`, and usage types ending in `NatGateway-Bytes`, `PublicIPv4:InUseAddress` and `PublicIPv4:IdleAddress` · **Where:** lab and dev accounts left running, production pulling images through NAT · **Level:** [L2 · Mid-level] · **How common:** a recurring top theme on r/aws and Hacker News; AWS has charged for every public IPv4 address since 1 February 2024

**Why it happens:** the expensive items are rarely the instances. "EC2-Other" hides NAT gateway hours and per-GB processing, EBS volumes, snapshots and data transfer. Every public IPv4 address costs $0.005 per hour, in use or idle, about $3.60 a month each. Images, artifacts and backups pulled through a NAT gateway pay processing per GB on top of transfer, often for S3 or ECR traffic that a VPC endpoint would carry for free or cheaper. Then the leftovers: unattached volumes, old snapshots and AMIs, a forgotten load balancer, resources in a region nobody looks at, and cross-AZ traffic between chatty services.

**Diagnose:**

```bash
# Last month by usage type: what is the money actually for? (lines over $20)
aws ce get-cost-and-usage --time-period Start=2026-09-01,End=2026-10-01 --granularity MONTHLY \
  --metrics UnblendedCost --group-by Type=DIMENSION,Key=USAGE_TYPE --query \
  'ResultsByTime[].Groups[?to_number(Metrics.UnblendedCost.Amount) > `20`][].[Keys[0],Metrics.UnblendedCost.Amount]' \
  --output text
# Leftovers: idle Elastic IPs, unattached volumes, the oldest snapshots
aws ec2 describe-addresses --query 'Addresses[?AssociationId==null].[PublicIp,AllocationId]' --output text
aws ec2 describe-volumes --filters Name=status,Values=available \
  --query 'Volumes[].[VolumeId,Size,CreateTime]' --output text
aws ec2 describe-snapshots --owner-ids self \
  --query 'sort_by(Snapshots,&StartTime)[:2].[SnapshotId,VolumeSize,StartTime]' --output text
```

```text
EU-NatGateway-Bytes            412.37
EU-NatGateway-Hours            105.12
EU-EBS:SnapshotUsage            61.12
EU-BoxUsage:t3.large            65.66
EU-EBS:VolumeUsage.gp3          48.00
EU-PublicIPv4:InUseAddress      32.40
203.0.113.61    eipalloc-0aa0aa0aa0aa0aa01
203.0.113.62    eipalloc-0bb0bb0bb0bb0bb02
203.0.113.63    eipalloc-0cc0cc0cc0cc0cc03
vol-0f0e0d0c0b0a09080    200    2026-03-14T10:22:05.000Z
snap-0a9b8c7d6e5f40312    100    2025-02-02T03:00:11.000Z
snap-0b8c7d6e5f4031201     50    2025-02-09T03:00:09.000Z
```

**What the output tells you:** NAT data processing is the biggest line, bigger than the instances, so something pulls terabytes through NAT (CI image pulls, S3 backups). Three NAT gateways run around the clock. Three Elastic IPs are allocated but attached to nothing, each billed at the idle rate. A 200 GB volume has sat unattached since March, and the oldest snapshots date from early 2025.

**Fix:**

```bash
# Release idle Elastic IPs
aws ec2 release-address --allocation-id eipalloc-0aa0aa0aa0aa0aa01
# Orphaned volume: keep a final snapshot, wait for it, then delete the volume
SNAP=$(aws ec2 create-snapshot --volume-id vol-0f0e0d0c0b0a09080 \
  --description "final copy before delete" --query SnapshotId --output text)
aws ec2 wait snapshot-completed --snapshot-ids "$SNAP"
aws ec2 delete-volume --volume-id vol-0f0e0d0c0b0a09080
# Take S3 traffic off the NAT gateways (a gateway endpoint has no hourly or per-GB charge)
aws ec2 create-vpc-endpoint --vpc-id vpc-0a1b2c3d4e5f67890 --service-name com.amazonaws.eu-west-1.s3 \
  --route-table-ids rtb-0c1d2e3f4a5b6c7d8 rtb-0d2e3f4a5b6c7d8e9
# A budget, so this never surprises you again
aws budgets create-budget --account-id 111122223333 \
  --budget '{"BudgetName":"monthly","BudgetLimit":{"Amount":"300","Unit":"USD"},"TimeUnit":"MONTHLY","BudgetType":"COST"}' \
  --notifications-with-subscribers '[{"Notification":{"NotificationType":"ACTUAL","ComparisonOperator":"GREATER_THAN","Threshold":80,"ThresholdType":"PERCENTAGE"},"Subscribers":[{"SubscriptionType":"EMAIL","Address":"ops@example.com"}]}]'
```

**Why this fix works:** idle addresses and detached volumes bill by the hour whether or not anything uses them, so releasing them stops the meter at once. A gateway endpoint adds a route for S3's prefix list to the private route tables, so S3 traffic goes straight to S3 and skips both NAT charges; ECR image layers come from S3 too, so the same endpoint covers most image-pull bytes, and interface endpoints for the ECR API pay off only at volume. A dev VPC rarely needs a NAT gateway per AZ. A budget turns a monthly surprise into an email at 80%. Don't delete snapshots blindly: check first that no AMI or AWS Backup plan still depends on them.

**Prevent it:** Budgets on day one in every account, tags on everything (Terraform `default_tags` plus cost allocation tags), cost diffs on merge requests with infracost, scheduled stops for dev, and `terraform destroy` for labs at the end of every session.

**Next step:** [Cloud & AWS: Common bill surprises](36-learn-cloud-aws.md#common-bill-surprises) · [Senior architecture: Cost and FinOps](39-learn-senior-architecture.md#7-cost-and-finops) · KodeKloud: *AWS Certified CloudOps Engineer - Associate* — Cost and Performance · [AWS blog: public IPv4 address charge and Public IP Insights](https://aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/)

**Community threads:** [AWS blog: New AWS public IPv4 address charge + Public IP Insights](https://aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/) · Search: [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=surprise+bill+nat+gateway&restrict_sr=1) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=aws+bill+nat+gateway&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=aws+nat+gateway+cost+s3+vpc+endpoint)

---

## 3. Terraform and OpenTofu: init, backends and state

### 3.1 Backend configuration changed

> **Seen as:** `Error: Backend configuration changed` with the choice between `terraform init -migrate-state` and `terraform init -reconfigure` · `Error: Variables not allowed` ... `Variables may not be used here.` · **Where:** one codebase for dev, staging and prod with different buckets or keys; a CI cache of .terraform; an attempt to template the backend with var.env · **Level:** [L1 · Junior] · **How common:** hashicorp/terraform #13022 (variables in the backend block) has more than 300 reactions; the Discuss thread "Backend configuration changed" has 21.7k views

**Why it happens:** the backend is configured before Terraform evaluates any variables, because it must load the state first, so the backend block accepts only literal values. `terraform init` records the backend it used in `.terraform/terraform.tfstate`; when the configuration, or a cached .terraform from another environment, disagrees, init stops and makes you choose. The two flags do very different things: `-migrate-state` copies the existing state to the new location, while `-reconfigure` just points at the new location and ignores the old one. Choosing `-reconfigure` against an empty key gives you an empty state, and the next plan wants to create everything.

**Diagnose:**

```bash
# Which backend did this working directory last initialise?
jq '.backend.type, .backend.config.key' .terraform/terraform.tfstate
# What does the environment file ask for?
cat backend/prod.hcl
terraform init -backend-config=backend/prod.hcl
```

```text
"s3"
"staging/app.tfstate"
bucket       = "example-tfstate"
key          = "prod/app.tfstate"
region       = "eu-west-1"
use_lockfile = true
Initializing the backend...
╷
│ Error: Backend configuration changed
│
│ A change in the backend configuration has been detected, which may require migrating existing state.
│
│ If you wish to attempt automatic migration of the state, use "terraform init -migrate-state".
│ If you wish to store the current configuration with no changes to the state, use "terraform init -reconfigure".
╵
```

**What the output tells you:** this directory was last initialised for staging, and you now ask for prod. Here the stop protects you: you want to point at prod's existing state, which is `-reconfigure`. `-migrate-state` would offer to copy staging's state over prod's key.

**Fix:**

```hcl
# backend.tf: nothing that differs per environment
terraform {
  backend "s3" {}
}
```

```hcl
# backend/prod.hcl: literals only, one small file per environment
bucket       = "example-tfstate"
key          = "prod/app.tfstate"
region       = "eu-west-1"
use_lockfile = true
```

```bash
# Point this directory at prod's EXISTING state (copies nothing)
terraform init -reconfigure -backend-config=backend/prod.hcl
# Moving state to a NEW location instead: copy it across, then prove nothing changed
terraform init -migrate-state -backend-config=backend/prod-new-bucket.hcl
terraform plan
```

```hcl
# OpenTofu 1.8 and later only: early evaluation allows variables in the backend block
variable "env" {
  type = string
}
terraform {
  backend "s3" {
    bucket       = "example-tfstate"
    key          = "${var.env}/app.tfstate"
    region       = "eu-west-1"
    use_lockfile = true
  }
}
# tofu init -var env=prod
```

**Why this fix works:** partial configuration keeps the code identical across environments and moves the only differing values into small files that a wrapper or CI job passes in. `-reconfigure` re-points without touching any state; `-migrate-state` copies state and asks before overwriting. OpenTofu evaluates variables early, so `key = "${var.env}/app.tfstate"` works there; Terraform's new constant variables in 1.15 target module sources and versions, so check your version's documentation before relying on variables in a Terraform backend block. GitLab-managed state uses the `http` backend with the same partial-configuration pattern, and GitLab's OpenTofu CI/CD component fills in the address and credentials for you.

**Prevent it:** one backend file per environment, passed by a Makefile or CI job; never a shared or cached `.terraform` across environments; and read the first plan after any backend change line by line: "Plan: 87 to add" on an existing environment means you are looking at an empty state, so stop.

**Next step:** [CI/CD, IaC & SRE: Remote state and locking](33-learn-cicd-iac-sre.md#remote-state-and-locking) · KodeKloud: *Terraform Basics Training Course* — Remote State · [Terraform docs: S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)

**Community threads:** [hashicorp/terraform issues by reactions (#13022)](https://github.com/hashicorp/terraform/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · [InfoQ: Terraform 1.15 dynamic module sources](https://www.infoq.com/news/2026/06/terraform-1-15/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=terraform+backend+%22Variables+may+not+be+used+here%22) · [Reddit r/Terraform](https://www.reddit.com/r/Terraform/search/?q=backend+configuration+changed&restrict_sr=1)

### 3.2 Init picks the wrong provider or checksum

> **Seen as:** `provider registry registry.terraform.io does not have a provider named registry.terraform.io/hashicorp/proxmox` · `the local package for registry.terraform.io/hashicorp/aws 6.14.0 doesn't match any of the checksums previously recorded in the dependency lock file` · `Error: Value for unconfigurable attribute` right after a provider upgrade · **Where:** code split into modules that use community providers (bpg/proxmox, telmate/proxmox); a lock file created on a Mac and used by Linux CI with a plugin cache; loose version constraints · **Level:** [L1 · Junior] · **How common:** Discuss "Using a non hashicorp provider in a module" (22k views); hashicorp/terraform #32124 on lock-file problems; terraform-provider-aws #23106 (v4 S3 changes, 93 comments) and #43235 (version issues, 103 comments)

**Why it happens:** three separate mechanisms, all at `init`. First, a child module that uses a provider without its own `required_providers` entry: Terraform assumes the `hashicorp/` namespace for an unqualified name, so `proxmox` becomes `hashicorp/proxmox`, which doesn't exist. Second, `.terraform.lock.hcl` records an `h1:` hash only for the platforms that ran init; when a CI runner installs from a plugin cache or mirror it can only check `h1:` hashes, finds none for linux_amd64, and refuses the package. Third, a loose constraint such as `>= 5.0.0` lets `init -upgrade` pull a new major version, and majors carry breaking changes: AWS provider v4 split `aws_s3_bucket` into separate `_versioning`, `_acl` and other resources, and the occasional minor release regresses.

**Diagnose:**

```bash
# Which module asks for which provider?
terraform providers
grep -rn 'source' --include=versions.tf .
# How many platforms does the lock file cover? (h1: hashes per provider)
awk '/^provider/ {p=$2} /"h1:/ {n[p]++} END {for (k in n) print k, n[k]}' .terraform.lock.hcl
grep -A2 'provider "registry.terraform.io/hashicorp/aws"' .terraform.lock.hcl
```

```text

Providers required by configuration:
.
├── provider[registry.terraform.io/hashicorp/aws] >= 5.0.0
├── provider[registry.terraform.io/bpg/proxmox] ~> 0.70
└── module.vm
    └── provider[registry.terraform.io/hashicorp/proxmox]

./versions.tf:4:    proxmox = { source = "bpg/proxmox", version = "~> 0.70" }
./versions.tf:5:    aws     = { source = "hashicorp/aws", version = ">= 5.0.0" }
"registry.terraform.io/hashicorp/aws" 1
"registry.terraform.io/bpg/proxmox" 1
provider "registry.terraform.io/hashicorp/aws" {
  version     = "6.14.0"
  constraints = ">= 5.0.0"
```

**What the output tells you:** the root module asks for bpg/proxmox, but module.vm has no versions.tf, so Terraform invented hashicorp/proxmox for it. Each provider has a single `h1:` hash, from the laptop that ran init, which is why a Linux runner using a plugin cache rejects the package. And `>= 5.0.0` already let AWS provider 6.x in; the next major arrives the same way, unreviewed.

**Fix:**

```hcl
# modules/vm/versions.tf: every module declares what it uses
terraform {
  required_providers {
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.70"
    }
  }
}
```

```hcl
# versions.tf (root): pin Terraform and provider majors with ~>
terraform {
  required_version = "~> 1.15"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    proxmox = {
      source  = "bpg/proxmox"
      version = "~> 0.70"
    }
  }
}
```

```bash
terraform init -upgrade
# Record hashes for every platform that runs this code, then commit the lock file
terraform providers lock -platform=linux_amd64 -platform=darwin_arm64 -platform=windows_amd64
git add .terraform.lock.hcl && git commit -m "Lock providers for all platforms"
```

**Why this fix works:** a module's own `required_providers` gives the provider its full source address, so every module resolves the same provider. `providers lock` downloads each platform's package and records its hash, so any machine can verify what it installs. `~> 6.0` allows 6.x updates but never 7.0, so a major arrives only when you choose it: in a branch, with the provider's upgrade guide open and the plan reviewed, adopting split-out resources with import blocks. If a new minor release regresses, pin back one minor version and leave a comment linking the provider issue.

**Prevent it:** a versions.tf in every module, tflint's `terraform_required_providers` rule in CI, the same Terraform version locally and in CI (a pinned image, or mise or tfenv), and Renovate opening provider bumps as merge requests. After switching between Terraform and OpenTofu, regenerate the lock file, and never run both tools against one state.

**Next step:** [CI/CD, IaC & SRE: Providers and resources](33-learn-cicd-iac-sre.md#providers-and-resources) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *Terraform Basics Training Course* — Terraform Basics, Modules · [Terraform docs](https://developer.hashicorp.com/terraform/docs)

**Community threads:** [HashiCorp Discuss: Using a non hashicorp provider in a module](https://discuss.hashicorp.com/t/using-a-non-hashicorp-provider-in-a-module/21841) · [hashicorp/terraform #32124](https://github.com/hashicorp/terraform/issues/32124) · [terraform-provider-aws issues by comments](https://github.com/hashicorp/terraform-provider-aws/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=terraform+%22does+not+have+a+provider+named%22+hashicorp) · [Reddit r/Terraform](https://www.reddit.com/r/Terraform/search/?q=lock+file+checksums+platform&restrict_sr=1)

### 3.3 Error acquiring the state lock

> **Seen as:** `Error: Error acquiring the state lock` · `ConditionalCheckFailedException: The conditional request failed` (DynamoDB) · `StatusCode: 412` ... `PreconditionFailed` (S3 native lock) · `Lock Info:` with ID, Who and Operation · `Error: Saved plan is stale` · **Where:** two pipelines or two people on the same state; a cancelled GitLab job; plan and apply jobs far apart in time · **Level:** [L2 · Mid-level] · **How common:** Discuss "Terraform Lock: how to check terraform lock state?" (22k views) and "Why does a plan lock the state file?" (14k views)

**Why it happens:** every operation that might write state takes the lock, and plan takes it too, because it refreshes. A second run on the same state waits or fails. When a run is killed (a cancelled CI job, a runner that ran out of memory, a laptop lid closed), nothing releases the lock, so it stays until someone removes it. With S3 native locking (`use_lockfile = true`) the lock is a `.tflock` object next to the state, so the role also needs s3:PutObject, s3:GetObject and s3:DeleteObject on that key, or locking itself fails. "Saved plan is stale" is a different guard: the plan file was made from an older state, because another apply ran in between.

**Diagnose:**

```bash
# The error prints Lock Info: read ID, Who, Created and Operation
terraform plan -lock-timeout=60s
# S3 native lock: is the lock object still there?
aws s3 ls s3://example-tfstate/prod/app.tfstate.tflock
# GitLab-managed state: Operate > Terraform states shows which state is locked.
# Then check the pipeline: is the job named in "Who" still running?
```

```text
╷
│ Error: Error acquiring the state lock
│
│ Error message: operation error S3: PutObject, https response error StatusCode: 412, RequestID:
│ 1B2C3D4E5F6A7B8C, api error PreconditionFailed: At least one of the pre-conditions you specified did not hold
│ Lock Info:
│   ID:        6f1c2a9e-4b7d-4e1b-9a30-2d8c5f7e1a42
│   Path:      example-tfstate/prod/app.tfstate
│   Operation: OperationTypeApply
│   Who:       runner@gitlab-runner-02
│   Version:   1.15.0
│   Created:   2026-10-03 06:12:44.123456789 +0000 UTC
│   Info:
│
│ Terraform acquires a state lock to protect the state from being written
│ by multiple users at the same time. Please resolve the issue above and try
│ again. For most commands, you can disable locking with the "-lock=false"
│ flag, but this is not recommended.
╵
2026-10-03 06:12:45        312 app.tfstate.tflock
```

**What the output tells you:** an apply started at 06:12 on gitlab-runner-02 holds the lock, and the lock object still exists. Check the pipeline: if that job is still running, wait. If it was cancelled or its runner died, the lock is stale and safe to remove, but only once you know no apply is still writing.

**Fix:**

```bash
# Only after confirming the owner is dead (OpenTofu: tofu force-unlock ID)
terraform force-unlock 6f1c2a9e-4b7d-4e1b-9a30-2d8c5f7e1a42
# Saved plan is stale: plan again, then apply that new plan in the same pipeline
terraform plan -out=tfplan && terraform apply tfplan
```

```yaml
# .gitlab-ci.yml: one job per environment at a time, and wait instead of failing
apply:prod:
  stage: apply
  resource_group: production
  script:
    - terraform apply -lock-timeout=5m tfplan
```

**Why this fix works:** force-unlock deletes the lock record only and never touches the state, so it is safe exactly when no process is still writing. `resource_group` makes GitLab queue jobs for the same environment instead of running them side by side, and `-lock-timeout` turns a near-miss into a short wait. Never use `-lock=false` to get past a lock: two writers on one state is how state gets corrupted.

**Prevent it:** serialise each environment (`resource_group`), keep one state per environment and component, move from the deprecated DynamoDB table to `use_lockfile = true` (Terraform 1.11 and later, OpenTofu 1.10 and later), give the CI role access to the `.tflock` key, and make apply consume the plan artifact produced earlier in the same pipeline.

**Next step:** [CI/CD, IaC & SRE: Remote state and locking](33-learn-cicd-iac-sre.md#remote-state-and-locking) · [CI/CD toolbox: Deploying from CI](47-cicd-gitlab-jenkins-actions-argocd.md#9-deploying-from-ci) · KodeKloud: *Terraform Basics Training Course* — Remote State (S3 backend, locking) · [Terraform docs: S3 backend](https://developer.hashicorp.com/terraform/language/backend/s3)

**Community threads:** [HashiCorp Discuss: Terraform top topics (all time)](https://discuss.hashicorp.com/c/terraform-core/27/l/top?period=all) · [GitLab-managed Terraform/OpenTofu state](https://docs.gitlab.com/user/infrastructure/iac/terraform_state/) · Search: [Reddit r/Terraform](https://www.reddit.com/r/Terraform/search/?q=%22Error+acquiring+the+state+lock%22&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=terraform+%22Error+acquiring+the+state+lock%22+force-unlock)

### 3.4 Secrets in plaintext in the state

> **Seen as:** the CLI shows `(sensitive value)`, yet `terraform state pull` prints the database password in clear text · `Error: Output refers to sensitive values` · **Where:** database passwords, generated keys, provider tokens; state or plan files that end up in Git, an open bucket or CI artifacts · **Level:** [L3 · Senior] · **How common:** "How to show sensitive values" is the most-viewed Terraform topic on Discuss (130k views); hashicorp/terraform #516 on secrets in state collected 254 reactions over a decade

**Why it happens:** `sensitive = true` only redacts values in CLI output. Terraform must remember every attribute it manages to compute the next diff, so the state, and every saved plan file, holds the real value. Anyone who can read the state bucket, download a plan artifact or see a committed tfstate can read the secret. "Output refers to sensitive values" is the same rule from the other side: an output derived from a sensitive value must be marked sensitive too.

**Diagnose:**

```bash
# Is anything secret in state? (run where you are allowed to see it)
terraform state pull | grep -n -i -E '"(password|secret|token|private_key[a-z_]*)":' | cut -c1-60
# Who can read the state, and how is it encrypted?
aws s3api get-bucket-policy --bucket example-tfstate --query Policy --output text \
  | jq -c '.Statement[] | {Effect, Principal}'
aws s3api get-bucket-encryption --bucket example-tfstate \
  --query 'ServerSideEncryptionConfiguration.Rules[0].ApplyServerSideEncryptionByDefault.SSEAlgorithm' --output text
# Was a state or plan file ever committed?
git log --all --oneline -- '*.tfstate' '*.tfplan' | head -3
```

```text
1418:            "password": "Wq8-EXAMPLE-ONLY-xYz",
2291:            "private_key_openssh": "-----BEGIN OPENSSH
{"Effect":"Allow","Principal":{"AWS":"arn:aws:iam::111122223333:root"}}
AES256
3f9a1c2 add terraform state for quick fix
```

**What the output tells you:** the state holds a database password and a private key in clear text. The bucket policy delegates to the whole account (the `root` principal means "any IAM identity here whose policies allow it"), and the encryption is S3-managed AES256, which protects the disks, not the content: anyone in the account with s3:GetObject on the bucket reads the file in clear. And someone once committed a state file, so the password lives in Git history and must be rotated.

**Fix:**

```hcl
# Best: Terraform never sees the secret. RDS generates it and keeps it in Secrets Manager
resource "aws_db_instance" "app" {
  identifier                  = "app-prod"
  engine                      = "postgres"
  instance_class              = "db.t4g.medium"
  allocated_storage           = 50
  username                    = "app"
  manage_master_user_password = true
}
```

```hcl
# OpenTofu 1.7 and later: encrypt state and plan files with a KMS key
terraform {
  encryption {
    key_provider "aws_kms" "main" {
      kms_key_id = "alias/tofu-state"
      region     = "eu-west-1"
      key_spec   = "AES_256"
    }
    method "aes_gcm" "main" {
      keys = key_provider.aws_kms.main
    }
    state {
      method = method.aes_gcm.main
    }
    plan {
      method = method.aes_gcm.main
    }
  }
}
```

```bash
# Either tool: SSE-KMS on the state bucket, a policy limited to the CI roles, versioning on
aws s3api put-bucket-encryption --bucket example-tfstate --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"aws:kms","KMSMasterKeyID":"alias/tfstate"}}]}'
aws s3api put-bucket-versioning --bucket example-tfstate --versioning-configuration Status=Enabled
# Then rotate every secret that was ever in Git, a public bucket or an artifact
```

**Why this fix works:** the safest secret is one Terraform never handles: RDS-managed passwords, ephemeral values (Terraform 1.10 and later, OpenTofu 1.11 and later) and write-only arguments (Terraform 1.11 and later) keep values out of state entirely. Where state must hold secrets, SSE-KMS plus a bucket policy limited to the CI roles turns "anyone in the account" into "whoever may use that key", and OpenTofu's state encryption makes the file itself unreadable without the key. Rotation is not optional: a secret that was ever in Git or an artifact is burned. Don't print secrets with `terraform output -raw` in CI logs, and remember that losing the OpenTofu encryption key means losing the state.

**Prevent it:** never commit state or plan files (gitignore them and run gitleaks in CI), restrict plan artifacts (GitLab `artifacts:access: developer` and a short expiry), read secrets at runtime from Vault/OpenBao, SSM Parameter Store or Secrets Manager, and include state access in the account's access review.

**Next step:** [CI/CD, IaC & SRE: Secrets management](33-learn-cicd-iac-sre.md#6-secrets-management) · [Security: Secrets management](37-learn-security-devsecops.md#5-secrets-management) · [Wazuh & security tools: Vault and OpenBao](48-wazuh-and-security-tools.md#11-vault-and-openbao) · KodeKloud: *Terraform Basics Training Course* — Terraform State · [Terraform docs: Manage sensitive data](https://developer.hashicorp.com/terraform/language/manage-sensitive-data)

**Community threads:** [Terraform docs: Manage sensitive data](https://developer.hashicorp.com/terraform/language/manage-sensitive-data) · [OpenTofu docs: State and plan encryption](https://opentofu.org/docs/language/state/encryption/) · Search: [Reddit r/Terraform](https://www.reddit.com/r/Terraform/search/?q=secrets+in+state+file&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=terraform+state+file+contains+password+sensitive)

---

## 4. Terraform and OpenTofu: plans, drift and refactoring

### 4.1 Plan shows changes nobody made

> **Seen as:** `Note: Objects have changed outside of Terraform` · a plan that wants to remove a security group rule someone added by hand · `tags_all` or policy JSON updates on every single plan · **Where:** a console hotfix during an incident; another system (Auto Scaling, AWS Backup, a Kubernetes controller) changing attributes Terraform also manages · **Level:** [L2 · Mid-level] · **How common:** terraform-provider-aws #18311 ("default_tags always shows an update", 80 comments); drift is a top r/Terraform theme

**Why it happens:** Terraform compares three things: the code, the state, and reality as refreshed from the API. Drift appears when reality changes without a code change: a rule added by hand during an incident, a tag written by AWS Backup or a cost tool, or an attribute two systems both believe they own. A perpetual diff is different: nothing really changed, but the provider normalises a value differently each time, such as the ordering inside a JSON policy, tags merged from `default_tags`, or inline `ingress` blocks and separate rule resources managing the same security group and undoing each other.

**Diagnose:**

```bash
# What changed outside Terraform, without proposing to undo it
terraform plan -refresh-only
# Exit code 2 means "changes present": the basis of a scheduled drift job
terraform plan -detailed-exitcode -input=false > /dev/null; echo "exit=$?"
# Who changed it?
aws cloudtrail lookup-events --max-results 3 \
  --lookup-attributes AttributeKey=ResourceName,AttributeValue=sg-0a1a1a1a1a1a1a1a1 \
  --query 'Events[].[EventTime,EventName,Username]' --output text
```

```text
Note: Objects have changed outside of Terraform

Terraform detected the following changes made outside of Terraform since the
last "terraform apply" which may have affected this plan:

  # aws_security_group.db has changed
  ~ resource "aws_security_group" "db" {
        id                     = "sg-0a1a1a1a1a1a1a1a1"
      ~ ingress                = [
          + {
              + cidr_blocks      = [
                  + "198.51.100.7/32",
                ]
              + description      = ""
              + from_port        = 5432
              + ipv6_cidr_blocks = []
              + prefix_list_ids  = []
              + protocol         = "tcp"
              + security_groups  = []
              + self             = false
              + to_port          = 5432
            },
            # (1 unchanged element hidden)
        ]
        name                   = "db"
        # (7 unchanged attributes hidden)
    }

This is a refresh-only plan, so Terraform will not take any actions to undo
these. If you were expecting these changes then you can apply this plan to
record the updated values in the Terraform state without changing any remote
objects.
exit=2
2026-10-02T23:41:07+00:00    AuthorizeSecurityGroupIngress    ops-oncall
```

**What the output tells you:** someone on call opened 5432 from one address at 23:41 last night, by hand. A normal `terraform apply` would silently remove that rule. Decide which reality you want before anyone applies: keep the rule (and put it in code) or revert it (apply the code as it is).

**Fix:**

```bash
# Keep reality: add the rule to the code first, then record the refreshed values in state
terraform apply -refresh-only
terraform plan                      # must now say "No changes"
# Revert reality: a normal apply puts the code's version back
terraform apply
```

```hcl
# Another system owns this attribute: tell Terraform to leave it alone
resource "aws_instance" "app" {
  # ...
  lifecycle {
    ignore_changes = [tags["Backup"]]
  }
}
# Perpetual JSON diffs: build policies with the data source, not hand-written strings
data "aws_iam_policy_document" "read" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["arn:aws:s3:::example-artifacts/*"]
  }
}
```

**Why this fix works:** `-refresh-only` updates the state to match reality without changing any infrastructure, so the next plan compares your code with the truth. `ignore_changes` draws a line between the attributes Terraform owns and those another system owns, which stops two owners undoing each other. Policy documents generated by the data source come out in a stable, normalised form, so the provider sees no difference. Don't paper over real drift with `ignore_changes = all`: you lose the ability to change that resource from code.

**Prevent it:** read-only console access in production (a break-glass role for incidents, followed by a merge request), a scheduled drift pipeline that runs `plan -detailed-exitcode` every night and alerts on exit code 2, and every change through a merge request.

**Next step:** [CI/CD, IaC & SRE: Drift and import](33-learn-cicd-iac-sre.md#drift-and-import) · [Cloud & AWS: CloudTrail and Config](36-learn-cloud-aws.md#cloudtrail-and-config) · KodeKloud: *Terraform Basics Training Course* — Terraform State, Working with Terraform (lifecycle rules) · [Terraform docs](https://developer.hashicorp.com/terraform/docs)

**Community threads:** [terraform-provider-aws issues by comments (#18311)](https://github.com/hashicorp/terraform-provider-aws/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Reddit r/Terraform](https://www.reddit.com/r/Terraform/search/?q=drift+detection&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=terraform+plan+%22changed+outside+of+terraform%22)

### 4.2 Already exists: adopting resources with import

> **Seen as:** `Error: creating EC2 Security Group (web): InvalidGroup.Duplicate` · `BucketAlreadyOwnedByYou` · `Error: Resource already managed by Terraform` · **Where:** resources made by hand (ClickOps), a lost state, resources moving between states; the usual first Terraform task in an existing company · **Level:** [L2 · Mid-level] · **How common:** Discuss "Terraform import examples" (9.7k views); a perennial Stack Overflow topic

**Why it happens:** Terraform only knows about objects in its state. If the object already exists in AWS (or Proxmox) but not in state, apply tries to create it and the API refuses because the name is taken. "Resource already managed by Terraform" is the opposite mistake: importing an object this state already tracks. Two states managing one object is worse than either error, because each apply undoes the other.

**Diagnose:**

```bash
# Does this state already track it under some address?
terraform state list | grep -i web || echo "not in this state"
# Find the real ID, and check whether another stack claims it
aws ec2 describe-security-groups --filters Name=group-name,Values=web \
  --query 'SecurityGroups[].[GroupId,VpcId,Tags[?Key==`ManagedBy`]|[0].Value]' --output text
```

```text
not in this state
sg-0c3c3c3c3c3c3c3c3    vpc-0a1b2c3d4e5f67890    None
```

**What the output tells you:** the group exists in the VPC, this state doesn't track it, and it carries no ManagedBy tag, so no other Terraform stack should own it either (grep your other stacks anyway). Import it, rather than renaming your resource to dodge the conflict and ending up with two groups.

**Fix:**

```hcl
# import.tf (Terraform 1.5 and later, OpenTofu 1.6 and later): reviewed in the plan like any change
import {
  to = aws_security_group.web
  id = "sg-0c3c3c3c3c3c3c3c3"
}
```

```bash
# No code for it yet? Let Terraform draft it, then tidy the draft by hand
terraform plan -generate-config-out=generated.tf
terraform plan          # goal: "Plan: 1 to import, 0 to add, 0 to change, 0 to destroy."
terraform apply
# Older CLI way (still available, but it changes state at once with no plan to review):
#   terraform import aws_security_group.web sg-0c3c3c3c3c3c3c3c3
```

**Why this fix works:** an import block is planned like any other change, so you see exactly what Terraform will believe about the object before the state changes, and a clean plan proves the code matches reality. Generated configuration is a draft: it often contains every computed attribute and some conflicting arguments, so trim it before you apply. From Terraform 1.7, import blocks accept `for_each` for adopting many objects at once. Don't run `terraform import` straight against production state from a laptop: the import block keeps the change in review.

**Prevent it:** one owner per resource, a `ManagedBy = terraform` tag through `default_tags`, S3 versioning on the state bucket so a lost state can be restored instead of rebuilt, and imports done in merge requests.

**Next step:** [CI/CD, IaC & SRE: Drift and import](33-learn-cicd-iac-sre.md#drift-and-import) · KodeKloud: *Terraform Basics Training Course* — Import, Taint and Debugging · [Terraform docs: Import existing resources](https://developer.hashicorp.com/terraform/language/import)

**Community threads:** [Terraform docs: Import existing resources](https://developer.hashicorp.com/terraform/language/import) · Search: [Stack Overflow](https://stackoverflow.com/search?q=terraform+import+block+generate-config-out) · [Reddit r/Terraform](https://www.reddit.com/r/Terraform/search/?q=import+existing+resources&restrict_sr=1)

### 4.3 A rename wants to destroy and recreate

> **Seen as:** `Plan: 2 to add, 0 to change, 2 to destroy.` after a refactor that changed nothing real · `# aws_instance.web[1] must be replaced` after deleting one item from a list · **Where:** renaming resources, moving them into a module, switching from count to for_each · **Level:** [L2 · Mid-level] · **How common:** the classic "my rename deleted prod" story; Terraform 1.1 added moved blocks to solve exactly this

**Why it happens:** Terraform identifies objects by their address in state (`aws_instance.web`, `module.app.aws_instance.web`, `aws_instance.web[1]`). A new address is a new object to Terraform: the old address has no configuration, so it is destroyed, and the new one has no state, so it is created. With count, removing an element from the middle of a list shifts every later index, so the objects after it turn into their neighbours and get replaced.

**Diagnose:**

```bash
terraform plan -out=tfplan > /dev/null
terraform show -json tfplan | jq -r '.resource_changes[]
  | select(.change.actions != ["no-op"])
  | "\(.change.actions | join(",")) \(.address)"'
```

```text
delete aws_instance.web[0]
delete aws_instance.web[1]
create module.web.aws_instance.this["a"]
create module.web.aws_instance.this["b"]
```

**What the output tells you:** nothing about the servers changed, only their addresses: deletes paired with creates of the same type are the signature of a refactor. Tell Terraform the objects moved.

**Fix:**

```hcl
# moved.tf: same objects, new addresses (Terraform 1.1 and later, OpenTofu)
moved {
  from = aws_instance.web[0]
  to   = module.web.aws_instance.this["a"]
}
moved {
  from = aws_instance.web[1]
  to   = module.web.aws_instance.this["b"]
}
# Stop managing something without destroying it (Terraform 1.7 and later)
removed {
  from = aws_instance.legacy
  lifecycle {
    destroy = false
  }
}
```

```bash
terraform plan    # goal: "0 to add, 0 to change, 0 to destroy" plus "has moved to" notes
# Older CLI way (still available, but it edits state outside review):
#   terraform state mv 'aws_instance.web[0]' 'module.web.aws_instance.this["a"]'
```

**Why this fix works:** a moved block rewrites the state address during plan, so the existing object simply carries on under its new name, and because the block lives in code it is reviewed and applies the same way in every environment. for_each with stable string keys means a later removal touches only the removed key. A `removed` block with `destroy = false` makes Terraform forget an object while leaving it running. Don't apply a plan with deletes you can't explain: read the delete list every time.

**Prevent it:** prefer for_each with stable keys over count for anything that isn't truly identical, keep moved blocks in shared modules for at least one release, and fail the pipeline when a plan contains unexpected deletes (a conftest or OPA policy on `terraform show -json`).

**Next step:** [CI/CD, IaC & SRE: Variables, outputs and modules](33-learn-cicd-iac-sre.md#variables-outputs-and-modules) · KodeKloud: *Terraform Basics Training Course* — Working with Terraform (count and for_each), Modules · [Terraform docs: Refactor modules](https://developer.hashicorp.com/terraform/language/modules/develop/refactoring)

**Community threads:** [Terraform docs: Refactor modules (moved blocks)](https://developer.hashicorp.com/terraform/language/modules/develop/refactoring) · Search: [Stack Overflow](https://stackoverflow.com/search?q=terraform+rename+resource+without+destroy+moved) · [Reddit r/Terraform](https://www.reddit.com/r/Terraform/search/?q=moved+block+count+for_each&restrict_sr=1)

### 4.4 Invalid for_each: values known after apply

> **Seen as:** `Error: Invalid for_each argument` ... `The "for_each" map includes keys derived from resource attributes that cannot be determined until apply` · `The "count" value depends on resource attributes that cannot be determined until apply` · **Where:** conditional resources; loops over the IDs of resources created in the same run · **Level:** [L3 · Senior] · **How common:** Discuss "Conditionally create resources when a for_each loop is involved" (119k views) and "count value depends on resource attributes" (8.7k)

**Why it happens:** Terraform must know at plan time how many instances a resource has and what their keys are, because each instance becomes its own address in state. Values such as a new instance ID, a random string, or a module output that depends on them are "(known after apply)". Using them as map keys, or as `count = length(...)` of something unknown, asks Terraform to build the graph from values that don't exist yet. Unknown values are fine as map values; they are not allowed as keys or counts.

**Diagnose:**

```bash
# Which input is unknown? The error points at the expression
terraform plan 2>&1 | grep -A12 'Invalid for_each argument'
# Inspect expressions interactively
terraform console
```

```text
│ Error: Invalid for_each argument
│
│   on main.tf line 41, in resource "aws_volume_attachment" "data":
│   41:   for_each = { for v in aws_ebs_volume.data : v.id => v }
│     ├────────────────
│     │ aws_ebs_volume.data is object with 2 attributes
│
│ The "for_each" map includes keys derived from resource attributes that cannot be
│ determined until apply, and so Terraform cannot determine the full set of keys that
│ will identify the instances of this resource.
│
│ When working with unknown values in for_each, it's better to define the map keys
│ statically in your configuration and place apply-time results only in the map values.
```

**What the output tells you:** the keys are volume IDs, which exist only after the volumes are created. The message itself names the fix: static keys, with unknown values only in the map values.

**Fix:**

```hcl
# Keys come from your own input (known at plan time); IDs go in the values
variable "data_disks" {
  type = map(object({ size = number, device = string }))
  default = {
    logs = { size = 50, device = "/dev/sdf" }
    db   = { size = 200, device = "/dev/sdg" }
  }
}
resource "aws_ebs_volume" "data" {
  for_each          = var.data_disks
  availability_zone = aws_instance.app.availability_zone
  size              = each.value.size
}
resource "aws_volume_attachment" "data" {
  for_each    = var.data_disks                         # static keys: logs, db
  device_name = each.value.device
  volume_id   = aws_ebs_volume.data[each.key].id       # unknown until apply: fine as a value
  instance_id = aws_instance.app.id
}
```

```hcl
# OpenTofu 1.11 and later: "this resource exists or not" without the count trick
resource "aws_cloudwatch_metric_alarm" "disk" {
  # ...
  lifecycle {
    enabled = var.create_alarms
  }
}
```

**Why this fix works:** with keys taken from a variable, Terraform knows at plan time that there will be exactly `logs` and `db`, and fills in the unknown IDs during apply. The other escape the error message offers, applying the dependencies first with `-target` and then everything, also converges, but every new environment has to repeat it, so keep it for emergencies. OpenTofu's `enabled` meta-argument expresses a 0-or-1 resource directly, without `count = var.x ? 1 : 0` and the `[0]` indexing that comes with it.

**Prevent it:** design module inputs as maps keyed by names you choose, keep conditionals on input variables rather than on resource attributes, and look for "keys from computed values" when you review module interfaces.

**Next step:** [CI/CD, IaC & SRE: Variables, outputs and modules](33-learn-cicd-iac-sre.md#variables-outputs-and-modules) · KodeKloud: *Terraform Challenges*, then *HashiCorp Certified: Terraform Associate 004* · [OpenTofu 1.11: what's new](https://opentofu.org/docs/v1.11/intro/whats-new/)

**Community threads:** [HashiCorp Discuss: Terraform top topics (all time)](https://discuss.hashicorp.com/c/terraform-core/27/l/top?period=all) · [OpenTofu 1.11: enabled meta-argument](https://opentofu.org/docs/v1.11/intro/whats-new/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=terraform+%22Invalid+for_each+argument%22+%22known+only+after+apply%22) · [Reddit r/Terraform](https://www.reddit.com/r/Terraform/search/?q=for_each+known+after+apply&restrict_sr=1)

### 4.5 Must be replaced on production

> **Seen as:** `# aws_instance.app[0] must be replaced` with `~ ami = "ami-0aaa1111bbbb22223" -> "ami-0ccc3333dddd44445" # forces replacement` · `Error: Instance cannot be destroyed` ... `lifecycle.prevent_destroy` · **Where:** a `data "aws_ami"` lookup with `most_recent = true`, a user_data edit, a renamed resource, `-target` misuse, a destroy run in the wrong workspace · **Level:** [L3 · Senior] · **How common:** terraform-provider-aws #23 ("don't destroy instance on user-data update", 72 comments); hashicorp/terraform #3874 (prevent_destroy, 165 reactions)

**Why it happens:** some attributes can't be changed in place, so the provider marks them "forces replacement": destroy, then create. An AMI lookup with `most_recent = true` returns a new image whenever the vendor publishes one, so a plan that "changes nothing" replaces every instance. Changing user_data replaces an `aws_instance` when `user_data_replace_on_change = true` (otherwise AWS provider v4 and later stop and start the instance to apply it, which is still an outage), and renaming buckets, load balancers and many other named resources forces replacement too. Without guardrails, the plan is the only thing standing between a routine merge and a deleted database.

**Diagnose:**

```bash
terraform workspace show
terraform plan -out=tfplan > /dev/null
terraform show tfplan | grep -E 'must be replaced|forces replacement|will be destroyed'
```

```text
prod
  # aws_instance.app[0] must be replaced
      ~ ami                                  = "ami-0aaa1111bbbb22223" -> "ami-0ccc3333dddd44445" # forces replacement
  # aws_instance.app[1] must be replaced
      ~ ami                                  = "ami-0aaa1111bbbb22223" -> "ami-0ccc3333dddd44445" # forces replacement
```

**What the output tells you:** you are in prod, and the only change is the AMI, which nobody changed on purpose: the `most_recent` lookup found a newer image. Applying this would replace both production instances at once.

**Fix:**

```hcl
# Pin the image; roll new AMIs out deliberately
variable "app_ami" {
  type = string                       # set per environment, bumped in a merge request
}
resource "aws_instance" "app" {
  count                   = 2
  ami                     = var.app_ami
  instance_type           = "t3.large"
  disable_api_termination = true      # provider-side guard
  lifecycle {
    ignore_changes        = [user_data]
    create_before_destroy = true
  }
}
resource "aws_db_instance" "main" {
  # ...
  deletion_protection = true
  lifecycle {
    prevent_destroy = true            # a literal: this argument can't take variables
  }
}
```

**Why this fix works:** a pinned AMI changes only when someone changes the variable, so a replacement becomes a decision rather than a side effect. `prevent_destroy` makes Terraform refuse any plan that would delete the resource, as long as the resource block itself stays in the code (deleting the block deletes the guard with it), and the provider-side flags (`deletion_protection`, `disable_api_termination`, S3 versioning) stop deletion even from outside Terraform. `create_before_destroy` builds the replacement first for resources that support it. If something was destroyed already, restore it from snapshots or AWS Backup and import the result. Don't use `-target` as an everyday workflow: it hides the rest of the plan.

**Prevent it:** a plan review gate that flags any delete or replace (a conftest policy on the JSON plan), stateful resources in their own state with their own pipeline, a CI role without Delete permissions on critical resources, and directory or workspace names that make prod impossible to hit by default.

**Next step:** [CI/CD, IaC & SRE: Plan and apply](33-learn-cicd-iac-sre.md#plan-and-apply) · [Senior architecture: Designing for availability](39-learn-senior-architecture.md#3-designing-for-availability) · KodeKloud: *Terraform Basics Training Course* — Working with Terraform (lifecycle rules) · [Terraform docs](https://developer.hashicorp.com/terraform/docs)

**Community threads:** [hashicorp/terraform issues by reactions (#3874)](https://github.com/hashicorp/terraform/issues?q=is%3Aissue+sort%3Areactions-%2B1-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=terraform+%22forces+replacement%22+ami+user_data) · [Reddit r/Terraform](https://www.reddit.com/r/Terraform/search/?q=terraform+destroyed+production&restrict_sr=1)

---

## 5. Ansible: connections, become and hangs

### 5.1 UNREACHABLE although plain ssh works

> **Seen as:** `fatal: [web1]: UNREACHABLE! => {"changed": false, "msg": "Failed to connect to the host via ssh: deploy@10.10.0.21: Permission denied (publickey,password).", "unreachable": true}` · **Where:** new VMs (Proxmox clones, EC2), or GitLab CI where no ssh-agent holds your key · **Level:** [L1 · Junior] · **How common:** ansible/ansible #15321 ("SSH works, but ansible throws unreachable error", 93 comments) and #19584 (70 comments)

**Why it happens:** Ansible runs its own ssh command with its own settings, so "ssh works" usually means "ssh works as me, with my agent and my ~/.ssh/config". Ansible connects as `ansible_user` (or your local username when that is unset), with `ansible_ssh_private_key_file` or whatever the agent offers, and it checks host keys strictly: new or rebuilt VMs that reuse an IP fail that check. A stale ControlPersist socket, or a control path longer than the Unix socket limit, breaks connections that worked a minute ago. In CI there is often no key loaded at all, or the key file has loose permissions.

**Diagnose:**

```bash
# The exact ssh command Ansible runs, with user, key and options
ansible web1 -i inventories/staging -m ansible.builtin.ping -vvvv 2>&1 \
  | grep -E 'ESTABLISH SSH|SSH: EXEC|Permission denied|Host key'
# What does the inventory really say about this host?
ansible-inventory -i inventories/staging --host web1
```

```text
<10.10.0.21> ESTABLISH SSH CONNECTION FOR USER: deploy
<10.10.0.21> SSH: EXEC ssh -vvv -C -o ControlMaster=auto -o ControlPersist=60s -o KbdInteractiveAuthentication=no -o PreferredAuthentications=gssapi-with-mic,gssapi-keyex,hostbased,publickey -o PasswordAuthentication=no -o 'User="deploy"' -o ConnectTimeout=10 -o 'ControlPath="/home/ops/.ansible/cp/5c1e3a9f0b"' 10.10.0.21 '/bin/sh -c '"'"'echo ~deploy && sleep 0'"'"''
deploy@10.10.0.21: Permission denied (publickey,password).
{
    "ansible_host": "10.10.0.21",
    "ansible_user": "deploy"
}
```

**What the output tells you:** Ansible connects as deploy and passes no IdentityFile, so it only offers what your agent holds: your personal key, which is authorised for ops but not for deploy. Your manual `ssh 10.10.0.21` worked because it logged you in as ops. A `Host key verification failed` line would instead mean a rebuilt VM on a reused IP.

**Fix:**

```yaml
# inventories/staging/group_vars/all.yml
ansible_user: deploy
ansible_ssh_private_key_file: ~/.ssh/deploy_ed25519
```

```bash
# Rebuilt VM on a reused IP: replace that one host key (check the fingerprint out of band)
ssh-keygen -R 10.10.0.21
ssh-keyscan -t ed25519 10.10.0.21 >> ~/.ssh/known_hosts
# Stale or over-long control sockets: clear them, and use a short directory in ansible.cfg
rm -f ~/.ansible/cp/*
#   [ssh_connection]
#   control_path_dir = /tmp/.ansible-cp
```

```yaml
# .gitlab-ci.yml: the key comes from a File-type CI variable
deploy:
  before_script:
    - mkdir -p ~/.ssh && chmod 700 ~/.ssh
    - chmod 600 "$DEPLOY_SSH_KEY"
    - eval "$(ssh-agent -s)" && ssh-add "$DEPLOY_SSH_KEY"
    - echo "$KNOWN_HOSTS" >> ~/.ssh/known_hosts
```

**Why this fix works:** putting the user and key in group_vars makes every run, from a laptop or from CI, connect the same way, whoever's agent happens to be loaded. Replacing a single host key keeps protection against impersonation for every other host. Clearing control sockets removes connections stuck from an earlier failure. Don't set `host_key_checking = False` outside a throwaway lab.

**Prevent it:** a dedicated automation user with key-only auth created at bootstrap (cloud-init `users:` with `ssh_authorized_keys`), known_hosts managed from your inventory or replaced by SSH certificates, and the `-vvvv` habit before guessing.

**Next step:** [SSH & remote access](09-ssh-remote-access.md) · [CI/CD, IaC & SRE: Inventory and ad-hoc commands](33-learn-cicd-iac-sre.md#inventory-and-ad-hoc-commands) · KodeKloud: *Ansible Basics Course* — Inventory · [Ansible docs](https://docs.ansible.com/)

**Community threads:** [ansible/ansible issues by comments (#15321, #19584)](https://github.com/ansible/ansible/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=ansible+UNREACHABLE+%22Permission+denied+%28publickey%22+ssh+works) · [Reddit r/ansible](https://www.reddit.com/r/ansible/search/?q=unreachable+permission+denied&restrict_sr=1)

### 5.2 become fails: password, timeout, temp files

> **Seen as:** `Missing sudo password` · `Timeout (12s) waiting for privilege escalation prompt:` · `Failed to set permissions on the temporary files Ansible needs to create when becoming an unprivileged user` · **Where:** `become: true` on fresh hosts; `become_user: postgres` or `www-data` on minimal Ubuntu images · **Level:** [L1 · Junior] · **How common:** ansible/ansible #13278 (123 comments) and #14426 (73 comments) for the timeout; the unprivileged-user case has its own section in the become docs

**Why it happens:** three different failures share the word become. *Missing sudo password*: the connecting user needs a password for sudo and Ansible wasn't given one. *Timeout waiting for the prompt*: sudo is slow to answer, most often because the host can't resolve its own name (`sudo: unable to resolve host`) and waits on DNS, or a custom prompt or `requiretty` confuses detection; the 12 seconds are the connection `timeout` setting (10 seconds by default) plus 2. *Temp-file permissions*: Ansible copies its module into a temp directory owned by the connecting user, and to let a different unprivileged user (postgres) read it, it uses POSIX ACLs via `setfacl`, which minimal images lack.

**Diagnose:**

```bash
ansible-playbook -i inventories/staging site.yml --limit db1 -vvvv 2>&1 | grep -E 'BECOME|setfacl|Timeout' | head -5
# On the target
time sudo -v
getent hosts "$(hostname)" || echo "own hostname does not resolve"
command -v setfacl || echo "acl package missing"
```

```text
sudo: unable to resolve host db1: Name or service not known

real    0m10.040s
own hostname does not resolve
acl package missing
```

**What the output tells you:** sudo needs ten seconds because db1 can't resolve its own name, close enough to the 12-second limit to fail on a busy day. setfacl is missing, so any task with `become_user: postgres` hits the temp-file error next.

**Fix:**

```yaml
# Bootstrap play, early, on every host
- name: Own hostname resolves locally
  ansible.builtin.lineinfile:
    path: /etc/hosts
    regexp: '^127\.0\.1\.1\s'
    line: "127.0.1.1 {{ ansible_hostname }}"
- name: acl, so become_user can switch to unprivileged users
  ansible.builtin.apt:
    name: acl
    state: present
```

```ini
# ansible.cfg
[defaults]
timeout = 30

[ssh_connection]
pipelining = True
```

```bash
# Password-protected sudo: prompt once per run, or keep ansible_become_password in Vault
ansible-playbook -i inventories/staging site.yml -K
```

**Why this fix works:** a resolvable hostname makes sudo answer instantly, and a longer connection timeout covers genuinely slow hosts. The acl package lets Ansible share its temp files with the target user safely, and pipelining avoids temp files for most modules altogether by streaming them over the SSH session (it needs `requiretty` off in sudoers, the Ubuntu default). Don't make the error go away with `allow_world_readable_tmpfiles` or a passwordless `ALL` rule for the automation user; if you use NOPASSWD, scope it in a drop-in under /etc/sudoers.d.

**Prevent it:** bake acl, a correct /etc/hosts entry and the sudoers drop-in into the base template (Packer or cloud-init), enable pipelining by default, and keep become passwords in Vault rather than in shell history.

**Next step:** [Users, permissions & security](10-users-permissions-security.md) · [CI/CD, IaC & SRE: Playbooks and idempotency](33-learn-cicd-iac-sre.md#playbooks-and-idempotency) · KodeKloud: *Ansible Basics Course* — Playbooks · [Ansible docs: Understanding privilege escalation](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_privilege_escalation.html)

**Community threads:** [Ansible docs: Understanding privilege escalation (become)](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_privilege_escalation.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=ansible+%22Timeout+%2812s%29+waiting+for+privilege+escalation+prompt%22) · [Reddit r/ansible](https://www.reddit.com/r/ansible/search/?q=%22becoming+an+unprivileged+user%22&restrict_sr=1)

### 5.3 apt can't get the dpkg lock on fresh VMs

> **Seen as:** `Could not get lock /var/lib/dpkg/lock-frontend. It is held by process 1234 (unattended-upgr)` · `Failed to lock apt for exclusive operation` · **Where:** the first run against VMs that just booted from cloud-init, a Proxmox clone or a Packer image · **Level:** [L1 · Junior] · **How common:** ansible/ansible #51663 has about 70 comments

**Why it happens:** a fresh Ubuntu VM is busy in its first minutes: cloud-init installs packages from its user-data, and apt-daily plus unattended-upgrades run soon after boot. dpkg allows exactly one writer, so your apt task loses the race. Two playbooks hitting the same host at once do the same.

**Diagnose:**

```bash
ansible web1 -i inventories/staging -b -m ansible.builtin.shell \
  -a 'cloud-init status; ps -eo pid,etime,cmd | grep -E "[u]nattended|[d]pkg"'
```

```text
web1 | CHANGED | rc=0 >>
status: running
   1234   01:52 /usr/bin/python3 /usr/bin/unattended-upgrade
   1301   01:40 /usr/bin/dpkg --status-fd 11 --configure --pending
```

**What the output tells you:** cloud-init is still running and unattended-upgrade holds dpkg. Nothing is wrong with the host; the playbook simply started too early.

**Fix:**

```yaml
- name: Wait for cloud-init to finish first boot
  ansible.builtin.command: cloud-init status --wait
  changed_when: false
  # rc 2 means "done, with recoverable errors": read them before you ignore them
- name: Install base packages, waiting for the dpkg lock if needed
  ansible.builtin.apt:
    name: [acl, qemu-guest-agent, chrony]
    state: present
    update_cache: true
    lock_timeout: 600
  register: apt_result
  retries: 3
  delay: 20
  until: apt_result is succeeded
```

**Why this fix works:** `cloud-init status --wait` blocks until first-boot work is done (waiting for /var/lib/cloud/instance/boot-finished with `wait_for` does the same), and `lock_timeout`, in the apt module since ansible-core 2.12 with a default of 60 seconds, makes the task wait for unattended-upgrades instead of failing. Retries cover the rare case where the lock is taken again between checks. Never delete the lock files: the lock protects dpkg from corrupting its own database.

**Prevent it:** bake updates into the Packer template so first boot has little to do, disable or shift the apt-daily timers on build and CI VMs, and never run two playbooks against the same hosts at once.

**Next step:** [Packages reference](11-packages.md) · KodeKloud: *Ansible Basics Course* — Modules and Plugins · [Ansible docs: apt module](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/apt_module.html)

**Community threads:** [ansible/ansible #51663](https://github.com/ansible/ansible/issues/51663) · [Ansible docs: apt module (lock_timeout)](https://docs.ansible.com/ansible/latest/collections/ansible/builtin/apt_module.html) · Search: [Stack Overflow](https://stackoverflow.com/search?q=ansible+%22Could+not+get+lock+%2Fvar%2Flib%2Fdpkg%2Flock-frontend%22) · [Reddit r/ansible](https://www.reddit.com/r/ansible/search/?q=dpkg+lock+cloud-init&restrict_sr=1)

### 5.4 Playbook hangs with no output

> **Seen as:** output stops at `TASK [Gathering Facts]` or at a command task and never returns · **Where:** large inventories, hosts with NFS or CIFS mounts, interactive commands · **Level:** [L2 · Mid-level] · **How common:** ansible/ansible #30411 ("Ansible hangs forever...") is among the most-commented Ansible issues (about 160 comments)

**Why it happens:** Ansible waits for each task to return, and by default there is no task timeout. Three things commonly never return: become waiting at a password prompt nobody will answer (the become docs warn about this), a command waiting for input (a dpkg conffile question, a git host-key prompt, an interactive installer), and fact gathering stuck on a hung NFS or CIFS mount while it collects mount information. A stale ControlPersist master on the controller can also leave a connection that never completes.

**Diagnose:**

```bash
# Which host and task? -vvvv shows the last command sent
ansible-playbook -i inventories/prod site.yml --limit web3 -vvvv
# On the target: what is the module process waiting on? (state D = stuck in I/O)
ps -eo pid,etime,stat,cmd --forest | grep -B1 -A1 '[p]ython3'
timeout 5 stat -f /mnt/backup > /dev/null || echo "mount /mnt/backup is hung"
```

```text
   4415   12:31 Ss    \_ /bin/sh -c /usr/bin/python3 && sleep 0
   4416   12:31 D         \_ /usr/bin/python3
mount /mnt/backup is hung
```

**What the output tells you:** the module process has sat in state D (uninterruptible I/O wait) for 12 minutes and /mnt/backup doesn't answer: fact gathering is stuck on the NFS mount. A process in state S under a `sudo` waiting for a terminal would mean a become prompt; one under `dpkg`, a conffile question.

**Fix:**

```yaml
- hosts: web
  gather_facts: true
  gather_timeout: 20                 # one slow fact can't block the play
  gather_subset: ['!hardware']       # skips mount facts, where hung mounts bite
  tasks:
    - name: Upgrade without conffile prompts
      ansible.builtin.apt:
        upgrade: dist
        dpkg_options: force-confdef,force-confold
      environment:
        DEBIAN_FRONTEND: noninteractive
      timeout: 1800                  # per-task timeout, ansible-core 2.10 and later
    - name: Long job without holding the SSH session open
      ansible.builtin.command: /usr/local/bin/reindex.sh
      async: 3600
      poll: 30
```

**Why this fix works:** gather_timeout and a smaller gather_subset stop one broken mount from freezing the play, the noninteractive settings answer dpkg's questions in advance (keep the old config, take the default), and `timeout:` turns any future hang into a clear failure on one host. async with poll frees the SSH session during long jobs. For a hang at become, interrupt and rerun with `-K` or fix the sudoers rule. The hung mount itself is a host problem: fix or unmount it, then monitor it.

**Prevent it:** never run interactive commands from Ansible, put timeouts on risky tasks, choose NFS mount options deliberately and alert on hung mounts, and use `strategy: free` for independent hosts so one stuck host doesn't hold up the rest.

**Next step:** [Slow system: Shell hangs and slow commands](23-playbook-slow-system.md#11-scenario-shell-hangs-and-slow-commands) · [Processes reference](05-processes.md) · KodeKloud: *Ansible Basics Course* — Playbooks · [Ansible docs: become (hangs at a prompt)](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_privilege_escalation.html)

**Community threads:** [ansible/ansible #30411](https://github.com/ansible/ansible/issues/30411) · Search: [Stack Overflow](https://stackoverflow.com/search?q=ansible+playbook+hangs+gathering+facts) · [Reddit r/ansible](https://www.reddit.com/r/ansible/search/?q=playbook+hangs+gathering+facts&restrict_sr=1)

---

## 6. Ansible: idempotency, variables, upgrades and scale

### 6.1 Every run reports changed

> **Seen as:** `PLAY RECAP` shows `changed=3` on every run although nothing really changes; services restart on every run · **Where:** beginner playbooks written like shell scripts · **Level:** [L1 · Junior] · **How common:** a classic beginner topic; molecule's idempotence step exists for exactly this

**Why it happens:** `command` and `shell` tasks can't know whether they changed anything, so they always report changed, and every handler they notify runs. `lineinfile` with a regexp that doesn't match the line it inserts appends a duplicate on each run. Templates that embed a timestamp differ every time. Until this is fixed, `--check` and the changed count tell you nothing, and real drift is invisible.

**Diagnose:**

```bash
# Run twice: the second run should report changed=0
ansible-playbook -i inventories/staging site.yml --limit web1 | tail -2
ansible-lint site.yml
```

```text
PLAY RECAP *********************************************************************
web1    : ok=14   changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
no-changed-when: Commands should not change things if nothing needs doing.
roles/docker/tasks/main.yml:12 Task/Handler: Configure log rotation
no-changed-when: Commands should not change things if nothing needs doing.
roles/docker/tasks/main.yml:20 Task/Handler: Add deploy to the docker group
```

**What the output tells you:** a second run still changes three things, and ansible-lint names two command tasks that will always report changed. Each one notifies a Docker restart, so every run restarts Docker on every host.

**Fix:**

```yaml
# Before: ansible.builtin.shell: echo '{"log-driver":"json-file"}' > /etc/docker/daemon.json
- name: Configure log rotation
  ansible.builtin.copy:
    dest: /etc/docker/daemon.json
    content: "{{ docker_daemon | to_nice_json }}\n"
    mode: "0644"
  notify: Restart docker
- name: Add deploy to the docker group
  ansible.builtin.user:
    name: deploy
    groups: docker
    append: true
# A command you can't avoid: tell Ansible when it changed something
- name: Initialise the swarm
  ansible.builtin.command: docker swarm init --advertise-addr {{ ansible_default_ipv4.address }}
  register: swarm
  changed_when: "'Swarm initialized' in swarm.stdout"
  failed_when: swarm.rc != 0 and 'already part of a swarm' not in swarm.stderr
```

**Why this fix works:** real modules compare the desired state with the current one and report changed only when they act, so handlers fire only after a real change. For commands, `creates:` and `removes:`, or `changed_when` and `failed_when`, give Ansible the knowledge it lacks. A second run with changed=0 then becomes a meaningful signal: anything that changes afterwards is drift.

**Prevent it:** ansible-lint in CI (its `no-changed-when` rule), molecule's idempotence test as a merge gate, and a short reviewed list of the shell tasks you allow.

**Next step:** [CI/CD, IaC & SRE: Playbooks and idempotency](33-learn-cicd-iac-sre.md#playbooks-and-idempotency) · [Docker: Ansible installs Docker with your daemon.json](30-learn-docker.md#drill-ansible-installs-docker-with-your-daemonjson) · KodeKloud: *Ansible Basics Course* — Playbooks (verifying, ansible-lint), Handlers, Roles and Collections · [Ansible docs](https://docs.ansible.com/)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=ansible+shell+task+always+changed+changed_when+idempotent) · [Reddit r/ansible](https://www.reddit.com/r/ansible/search/?q=idempotent+changed_when&restrict_sr=1) · [GitHub ansible-lint issues](https://github.com/ansible/ansible-lint/issues?q=no-changed-when)

### 6.2 Vault in CI: no vault secrets found

> **Seen as:** `[ERROR]: Attempting to decrypt but no vault secrets found` (printed as `ERROR! ...` before ansible-core 2.19) · `Decryption failed (no vault secrets were found that could decrypt)` · **Where:** works on the laptop with `--ask-vault-pass`, fails in GitLab CI or AWX · **Level:** [L1 · Junior] · **How common:** a classic Stack Overflow and r/ansible question whenever a team moves Ansible into CI

**Why it happens:** the first message means Ansible got no vault password at all: CI has no terminal for `--ask-vault-pass`, and the variable holding the password was never written to a file or passed. The second means a password was given but it doesn't open this file: the file was encrypted under a different vault ID label (prod versus staging) or a different password, or the CI variable doesn't hold what you think, an extra character from copy-paste being the usual culprit.

**Diagnose:**

```bash
head -1 inventories/prod/group_vars/all/vault.yml          # the header shows the vault ID label
ansible-config dump --only-changed | grep -i vault
# In the job: compare the password's length with the real one, never print it
wc -c < "$VAULT_PASS_PROD"
```

```text
$ANSIBLE_VAULT;1.2;AES256;prod
DEFAULT_VAULT_IDENTITY_LIST(/builds/infra/ansible/ansible.cfg) = ['staging@~/.vault-staging']
25
```

**What the output tells you:** the file is encrypted under the label prod, but ansible.cfg only supplies a staging identity, so nothing even tries the prod password. And the CI variable is 25 bytes where the real password has 24: Ansible strips a trailing newline from password files, but any other extra character makes it a different password, so re-enter the variable before you blame Ansible.

**Fix:**

```yaml
# .gitlab-ci.yml: VAULT_PASS_PROD is a masked, protected CI variable of type File
deploy:prod:
  script:
    - ansible-playbook -i inventories/prod site.yml --vault-id "prod@${VAULT_PASS_PROD}"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

```bash
# Re-key a file to the right label and password (locally, with both passwords at hand)
ansible-vault rekey --vault-id old@prompt --new-vault-id prod@prompt inventories/prod/group_vars/all/vault.yml
# Single values instead of whole files
ansible-vault encrypt_string --vault-id prod@prompt --name db_password
```

**Why this fix works:** a File-type variable gives Ansible a path it can read without a terminal, and the vault ID label tells it which password belongs to which files, so prod and staging can use different passwords in one repository. Protected variables only reach pipelines on protected branches, so a feature branch can't decrypt prod secrets. Don't echo the password, and don't run with `-vvvv` in CI while debugging vault problems.

**Prevent it:** one vault ID per environment, password files in .gitignore and never committed, and an external store (a Vault or OpenBao lookup) once CI should fetch secrets with its own short-lived identity.

**Next step:** [CI/CD, IaC & SRE: Ansible Vault](33-learn-cicd-iac-sre.md#ansible-vault) · [Security: Ansible Vault and sops](37-learn-security-devsecops.md#ansible-vault-and-sops) · [CI/CD toolbox: Quality gates, artifact repositories and secrets](47-cicd-gitlab-jenkins-actions-argocd.md#13-quality-gates-artifact-repositories-and-secrets) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Architecture & Core Concepts (variables) · [Ansible docs](https://docs.ansible.com/)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=ansible+%22Attempting+to+decrypt+but+no+vault+secrets+found%22) · [Reddit r/ansible](https://www.reddit.com/r/ansible/search/?q=vault+password+gitlab+ci&restrict_sr=1) · [GitHub ansible/ansible issues](https://github.com/ansible/ansible/issues?q=%22no+vault+secrets+found%22)

### 6.3 A variable has the wrong value

> **Seen as:** `The task includes an option with an undefined variable. The error was: 'app_port' is undefined` · a dev host receives production settings · **Where:** one inventory holding every environment, a host in several groups, role defaults clashing with role vars · **Level:** [L2 · Mid-level] · **How common:** ansible/ansible #9065 ("separate group_vars being overwritten when deploying to same host", 71 comments)

**Why it happens:** Ansible merges variables from about twenty places in a fixed precedence order: role defaults are the weakest, then inventory group_vars (all, then parent groups, then child groups), host_vars, play vars, role vars, set_fact results, and finally extra vars (`-e`), which always win. When one host sits in two sibling groups that both define a variable, the groups are merged alphabetically and the last one wins, unless `ansible_group_priority` says otherwise. group_vars directories are found relative to the inventory or the playbook, so a misplaced directory silently contributes nothing and a variable stays undefined.

**Diagnose:**

```bash
# The merged variables for one host, as Ansible sees them
ansible-inventory -i inventories/all.yml --host app2 | jq '{env_name, app_port}'
# Group membership (add --vars to list each group's variables after its hosts)
ansible-inventory -i inventories/all.yml --graph
```

```text
{
  "env_name": "prod",
  "app_port": null
}
@all:
  |--@dev:
  |  |--app2
  |  |--app3
  |--@prod:
  |  |--app1
  |  |--app2
  |--@ungrouped:
```

**What the output tells you:** app2 sits in both dev and prod, a copy-paste slip. Sibling groups merge alphabetically and the later one wins, so prod's values override dev's on app2. app_port is undefined because it is only set in group_vars/web.yml, and app2 isn't in the web group.

**Fix:**

```text
inventories/
  dev/
    hosts.yml
    group_vars/all.yml          # env_name: dev
  prod/
    hosts.yml
    group_vars/all.yml          # env_name: prod
roles/app/defaults/main.yml     # app_port: 8080, lowest precedence, role-prefixed name
```

```yaml
# Optional values: a default at the point of use
- name: Render the app environment file
  ansible.builtin.template:
    src: app.env.j2
    dest: /etc/app/app.env
  vars:
    listen_port: "{{ app_port | default(8080) }}"
```

**Why this fix works:** one inventory per environment makes it impossible for a host to belong to two environments, so the alphabetical merge can't pick the wrong one, and `-i inventories/prod` states the target on every command line. Defaults in `roles/NAME/defaults/main.yml` sit at the bottom of the ladder, so any environment can override them, and role-prefixed names (app_port, not port) avoid collisions between roles. Use `ansible_group_priority` only for deliberate overlaps. Don't fix precedence surprises with `-e`: extra vars win everywhere and hide the real problem.

**Prevent it:** a "where each variable lives" table in the repository, `ansible-inventory --host` output for the changed hosts printed in merge request pipelines, and ansible-lint's var-naming rule.

**Next step:** [CI/CD, IaC & SRE: Variables and precedence](33-learn-cicd-iac-sre.md#variables-and-precedence) · KodeKloud: *Ansible Basics Course* — Inventory, Variables and Facts · [Ansible docs](https://docs.ansible.com/)

**Community threads:** [ansible/ansible issues by comments (#9065)](https://github.com/ansible/ansible/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Stack Overflow](https://stackoverflow.com/search?q=ansible+variable+precedence+group_vars+same+host+multiple+groups) · [Reddit r/ansible](https://www.reddit.com/r/ansible/search/?q=variable+precedence+group_vars&restrict_sr=1)

### 6.4 ansible-core upgrade broke playbooks

> **Seen as:** `Conditional result (True) was derived from value of type 'str'` · `Conditional result was 'localhost' of type 'str', which evaluates to True. Conditionals must have a boolean result.` · `SyntaxError: future feature annotations is not defined` on old targets · `[WARNING]: Platform linux on host web1 is using the discovered Python interpreter at /usr/bin/python3.12, but future installation of another Python interpreter could change the meaning of that path.` · **Where:** a pip or pipx upgrade on the controller; a fleet that mixes Ubuntu 24.04 with 20.04 or CentOS 7 · **Level:** [L2 · Mid-level] · **How common:** the 2.19 porting guide has a "Broken conditionals" section, and many popular roles needed fixes (kubespray #13524); the support matrix changes every six months

**Why it happens:** two kinds of breakage arrive with upgrades. The templating overhaul in ansible-core 2.19 (Ansible 12) made conditionals strict: `when: my_string`, `when: "{{ var }}"`, or a `-e flag=true` that arrives as a string are now errors, because a non-empty string isn't a boolean. And each release narrows the supported Python versions: 2.17 dropped Python 2.7 and 3.6 targets (the `future feature annotations` SyntaxError is a 3.6 target receiving code it can't parse), and 2.20 and later need Python 3.9 or newer on targets and 3.12 or newer on the controller, which leaves out Ubuntu 20.04 targets (3.8) and an Ubuntu 22.04 controller (3.10). The interpreter warning is harmless but noisy.

**Diagnose:**

```bash
ansible --version | head -1                       # the core version on this controller
ansible all -i inventories/prod -m ansible.builtin.raw -a 'python3 --version' --one-line
ansible-playbook -i inventories/staging site.yml --check 2>&1 | grep -m1 'Conditional result'
```

```text
ansible [core 2.21.0]
web1 | CHANGED | rc=0 | (stdout) Python 3.12.3
legacy1 | CHANGED | rc=0 | (stdout) Python 3.8.10
fatal: [web1]: FAILED! => {"msg": "Conditional result (True) was derived from value of type 'str' at '/srv/infra/ansible/roles/app/tasks/main.yml:14:11'. Conditionals must have a boolean result."}
```

**What the output tells you:** the controller runs 2.21, legacy1 still has Python 3.8, which this core no longer supports, and line 14 of roles/app tests a string in `when:`. Two separate fixes: the conditional in code, and an older pinned core (or a newer OS) for the legacy host.

**Fix:**

```yaml
# Explicit booleans in conditionals
- name: Enable the feature
  ansible.builtin.template:
    src: feature.conf.j2
    dest: /etc/app/feature.conf
  when: feature_enabled | bool                 # was: when: feature_enabled  (a string from -e)
- name: Only when the list has items
  ansible.builtin.debug:
    var: extra_users
  when: extra_users | length > 0               # was: when: extra_users
```

```bash
# A separate virtualenv per fleet: an older core for legacy targets until they are replaced
python3 -m venv ~/venvs/ansible-legacy && ~/venvs/ansible-legacy/bin/pip install 'ansible-core<2.20'
python3 -m venv ~/venvs/ansible && ~/venvs/ansible/bin/pip install 'ansible-core~=2.21.0'
# Pin the interpreter instead of relying on discovery (group_vars/all.yml):
#   ansible_python_interpreter: /usr/bin/python3
# Short-term only, while you fix the code: turn the error back into a warning
ANSIBLE_ALLOW_BROKEN_CONDITIONALS=true ansible-playbook -i inventories/staging site.yml
```

**Why this fix works:** `| bool` and `| length > 0` turn strings and lists into real booleans, which 2.19 and later demand, and the code then behaves the same on old and new cores. A virtualenv per fleet lets legacy hosts keep a core that still supports their Python while the rest moves on, and a pinned `ansible_python_interpreter` silences discovery. `ALLOW_BROKEN_CONDITIONALS` is a dated exception, not a fix.

**Prevent it:** pin ansible-core in requirements.txt or an execution environment, run ansible-lint and molecule against every target OS as the upgrade gate, read the porting guide before each upgrade, and replace end-of-life operating systems instead of pinning forever.

**Next step:** [CI/CD, IaC & SRE: Ansible](33-learn-cicd-iac-sre.md#4-ansible) · [Security: Vulnerability and patch management](37-learn-security-devsecops.md#11-vulnerability-and-patch-management) · KodeKloud: *Ansible Basics Course* — Conditionals and Loops · [Ansible docs: Releases and maintenance](https://docs.ansible.com/ansible/latest/reference_appendices/release_and_maintenance.html)

**Community threads:** [Ansible-core 2.19 Porting Guide](https://docs.ansible.com/projects/ansible/latest/porting_guides/porting_guide_core_2.19.html) · [kubespray #13524](https://github.com/kubernetes-sigs/kubespray/issues/13524) · [Ansible docs: Interpreter discovery](https://docs.ansible.com/ansible/latest/reference_appendices/interpreter_discovery.html) · Search: [Reddit r/ansible](https://www.reddit.com/r/ansible/search/?q=2.19+conditional+result+derived&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=ansible+%22Conditionals+must+have+a+boolean+result%22)

### 6.5 Slow playbooks on 50+ hosts

> **Seen as:** run time grows linearly with the host count, and `Gathering Facts` dominates · **Where:** patch runs and fleet configuration on default settings · **Level:** [L3 · Senior] · **How common:** a recurring r/ansible topic; profile_tasks is the standard first step

**Why it happens:** the defaults are tuned for safety, not speed. `forks = 5` means Ansible works on five hosts at a time, so 60 hosts take twelve rounds per task. Facts are gathered in every play, each task pays extra SSH round trips unless pipelining and ControlPersist are on, and loops that call apt once per package pay the full module round trip for every item.

**Diagnose:**

```bash
# Both callbacks live in the ansible.posix collection (bundled with the full "ansible" package;
# with plain ansible-core: ansible-galaxy collection install ansible.posix)
ANSIBLE_CALLBACKS_ENABLED=ansible.posix.profile_tasks,ansible.posix.timer \
  ansible-playbook -i inventories/staging patch.yml | tail -6
ansible-config dump --only-changed
```

```text
===============================================================================
Gathering Facts --------------------------------------------------------- 412.33s
common : Install base packages ------------------------------------------ 388.10s
common : Ensure sysctl values ------------------------------------------- 140.72s
common : Render chrony.conf ---------------------------------------------- 61.94s
Playbook run took 0 days, 0 hours, 21 minutes, 37 seconds
CONFIG_FILE() = /srv/infra/ansible/ansible.cfg
```

**What the output tells you:** fact gathering and a package loop eat most of the 21 minutes, and nothing in ansible.cfg has been tuned: forks is still 5 and pipelining is off.

**Fix:**

```ini
# ansible.cfg
[defaults]
forks = 25
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible-facts
fact_caching_timeout = 7200
callbacks_enabled = ansible.posix.profile_tasks

[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

```yaml
# One apt transaction with a list, not one call per item
- name: Install base packages
  ansible.builtin.apt:
    name: "{{ base_packages }}"
    state: present
```

**Why this fix works:** more forks run more hosts in parallel, bounded by the controller's CPU and memory, so measure as you raise it. Smart gathering with a cache skips facts gathered recently, and plays that need no facts can set `gather_facts: false`. Pipelining plus a persistent SSH master cut several round trips from every task, and a list passed to apt is one transaction instead of N. Measure again with profile_tasks after each change so you know which one mattered. Don't reach for `strategy: free` for ordered changes: it lets fast hosts run ahead, which suits independent hosts and is wrong for rolling restarts.

**Prevent it:** profile in CI, keep plays small and targeted with `--limit` and tags, and give fleet-wide runs their own tuned ansible.cfg.

**Next step:** [Performance & observability: Methodologies](32-learn-performance-observability.md#2-methodologies) · [CI/CD, IaC & SRE: Check mode, diff and tags](33-learn-cicd-iac-sre.md#check-mode-diff-and-tags) · KodeKloud: *Ansible Basics Course* — Configuration and Basic Concepts · [Ansible docs](https://docs.ansible.com/)

**Community threads:** Search: [Reddit r/ansible](https://www.reddit.com/r/ansible/search/?q=speed+up+playbook+forks+pipelining&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=ansible+slow+playbook+pipelining+forks+fact+caching) · [GitHub ansible/ansible issues](https://github.com/ansible/ansible/issues?q=is%3Aissue+slow+forks+pipelining)

### 6.6 One run hit every host at once

> **Seen as:** `PLAY RECAP` shows every host changed, and the service restarted everywhere in the same minute · **Where:** a forgotten `--limit`, `hosts: all`, a handler restarting a whole cluster; the AWS S3 outage of 2017 began with a capacity-removal command whose input removed far more servers than intended · **Level:** [L4 · Senior/Lead] · **How common:** a classic postmortem pattern: AWS S3 in 2017 and countless "I ran it against prod" stories on r/sysadmin

**Why it happens:** automation does exactly what it is told, at full speed, everywhere. Without batching, a change that breaks the service breaks it on every host before anyone sees the first failure. Without a minimum-capacity guard, a typo in a target list removes the whole fleet. The S3 postmortem names the same two missing guardrails: a tool that removed capacity too quickly, and no check against dropping below minimum capacity.

**Diagnose:**

```bash
# Before anything fleet-wide: which hosts, which tasks?
ansible-playbook -i inventories/prod site.yml --list-hosts --list-tasks
ansible-playbook -i inventories/prod site.yml --limit canary --check --diff
```

```text
playbook: site.yml

  play #1 (web): Deploy app    TAGS: []
    pattern: ['web']
    hosts (6):
      web01
      web02
      web03
      web04
      web05
      web06
    tasks:
      app : Render config    TAGS: []
```

**What the output tells you:** one play, six hosts, and nothing limiting how many change at once. The handler restarts the app on all six at the end of the play, so if the new config is bad, all six go down together.

**Fix:**

```yaml
- hosts: web
  serial: [1, "25%", "50%"]          # one canary, then growing batches
  max_fail_percentage: 0
  any_errors_fatal: true
  tasks:
    - name: Render config
      ansible.builtin.template:
        src: app.env.j2
        dest: /etc/app/app.env
      notify: Restart app
    - name: Restart inside this batch, not at the end of the play
      ansible.builtin.meta: flush_handlers
    - name: The batch must be healthy before the next one starts
      ansible.builtin.uri:
        url: "http://{{ ansible_host }}:8080/health"
        status_code: 200
      register: health
      retries: 10
      delay: 6
      until: health.status == 200
  handlers:
    - name: Restart app
      ansible.builtin.systemd:
        name: app
        state: restarted
```

**Why this fix works:** `serial` turns one big change into batches, and a first batch of one host is a canary. `max_fail_percentage: 0` with `any_errors_fatal` stops the run at the first failed host or health check, so a bad change costs one host instead of the fleet. Flushing handlers inside the batch makes the restart happen before the health check. For anything that removes or drains hosts, add the guard AWS added after 2017: the tool refuses to go below a capacity floor, whatever the input says.

**Prevent it:** a wrapper or AWX/AAP survey that requires `--limit`, `--check --diff` against a canary group first, a written rollback in every change, staged rollouts across environments, and change windows for fleet-wide work.

**Next step:** [Deployment patterns](35-deployment-patterns.md) · [CI/CD, IaC & SRE: SRE practice](33-learn-cicd-iac-sre.md#7-sre-practice) · [Senior architecture: Reliability leadership](39-learn-senior-architecture.md#11-reliability-leadership) · KodeKloud: *Fundamentals of SRE* — Change Management for Reliability · [AWS: Summary of the Amazon S3 Service Disruption (2017)](https://aws.amazon.com/message/41926/)

**Community threads:** [AWS: Summary of the Amazon S3 Service Disruption (2017)](https://aws.amazon.com/message/41926/) · Search: [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=ansible+ran+against+all+hosts&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=ansible+serial+rolling+update+max_fail_percentage)

---

## 7. Proxmox VE: repositories, host network and cluster

### 7.1 apt update: 401 from the enterprise repo

> **Seen as:** `Failed to fetch https://enterprise.proxmox.com/debian/pve/dists/trixie/InRelease 401 Unauthorized` · `TASK ERROR: command 'apt-get update' failed: exit code 100` · **Where:** every new Proxmox VE install without a subscription; the first thing homelabs and new on-prem clusters hit · **Level:** [L0 · Fresher] · **How common:** forum.proxmox.com: "command 'apt-get update' failed: exit code 100" (301K views) and "Update Unauthorized, after latest update" (236K views)

**Why it happens:** a fresh install enables the enterprise repository, which needs a subscription key, so apt gets 401 for it and the whole update fails; the Ceph enterprise repository is enabled the same way. Proxmox VE 9 on Debian 13 stores repositories as deb822 `.sources` files, so the old sed one-liners written for `sources.list` don't touch them. And plain `apt upgrade` is the wrong command on Proxmox: it never removes or replaces packages, so updates that need that are held back and the host ends up half-upgraded (`apt-get upgrade` also holds back anything that needs a new dependency).

**Diagnose:**

```bash
apt update 2>&1 | grep -A1 '^Err'
ls /etc/apt/sources.list.d/
grep -H -E '^(URIs|Components|Enabled)' /etc/apt/sources.list.d/{pve-enterprise,ceph}.sources
pvesubscription get | grep '^status'
```

```text
Err:4 https://enterprise.proxmox.com/debian/pve trixie InRelease
  401  Unauthorized [IP: 203.0.113.70 443]
Err:5 https://enterprise.proxmox.com/debian/ceph-squid trixie InRelease
  401  Unauthorized [IP: 203.0.113.70 443]
ceph.sources  debian.sources  pve-enterprise.sources
/etc/apt/sources.list.d/pve-enterprise.sources:URIs: https://enterprise.proxmox.com/debian/pve
/etc/apt/sources.list.d/pve-enterprise.sources:Components: pve-enterprise
/etc/apt/sources.list.d/ceph.sources:URIs: https://enterprise.proxmox.com/debian/ceph-squid
/etc/apt/sources.list.d/ceph.sources:Components: enterprise
status: notfound
```

**What the output tells you:** both enterprise repositories are enabled, there is no subscription, and no no-subscription repository is configured, so every update fails with 401.

**Fix:**

```bash
# Simplest and safest: Node > Updates > Repositories in the web UI (Disable, then Add).
# The same from the shell. Disable the enterprise stanzas (deb822: "Enabled: no")
sed -i '/^Components:/a Enabled: no' \
  /etc/apt/sources.list.d/pve-enterprise.sources /etc/apt/sources.list.d/ceph.sources
# Add the no-subscription repository
cat > /etc/apt/sources.list.d/proxmox.sources <<'EOF'
Types: deb
URIs: http://download.proxmox.com/debian/pve
Suites: trixie
Components: pve-no-subscription
Signed-By: /usr/share/keyrings/proxmox-archive-keyring.gpg
EOF
apt update && apt full-upgrade
```

**Why this fix works:** `Enabled: no` keeps the file, and the option to switch it back on with a subscription, while apt skips it. The no-subscription repository carries the same packages without the enterprise testing delay; if you run Ceph, add its no-subscription repository the same way. `full-upgrade` also removes or replaces packages when a Proxmox update requires it, which plain `upgrade` never does. Don't mix repositories from different Debian or Proxmox releases.

**Prevent it:** buy a subscription for production clusters, manage repository files with Ansible so every node matches, and convert old one-line files with `apt modernize-sources`.

**Next step:** [Packages reference](11-packages.md) · KodeKloud: *Learning Linux Basics Course & Labs* — Package Management (DPKG and APT) · [Proxmox wiki: Package Repositories](https://pve.proxmox.com/wiki/Package_Repositories)

**Community threads:** [Proxmox wiki: Package Repositories](https://pve.proxmox.com/wiki/Package_Repositories) · [forum.proxmox.com: most-viewed installation and configuration threads](https://forum.proxmox.com/forums/proxmox-ve-installation-and-configuration.16/?order=view_count&direction=desc) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=401+unauthorized+enterprise+repository&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=proxmox+enterprise+repository+401+unauthorized)

### 7.2 Web UI dead after an IP, hostname or NIC change

> **Seen as:** the browser can't reach `https://192.0.2.11:8006` · `[main] crit: Unable to resolve node name 'pve1' to a non-loopback IP address - missing entry in '/etc/hosts' or DNS?` · after an upgrade: no network at all · **Where:** a box moved to a new network, a DHCP management address, a kernel or PVE 8-to-9 upgrade, a new PCIe card · **Level:** [L1 · Junior] · **How common:** forum.proxmox.com: "Cannot Access Web Interface" (278K views), "Hostname (FQDN)" (338K), "Help with changing IP address" (263K); the 8-to-9 upgrade guide warns that NIC names may change

**Why it happens:** the cluster filesystem (pmxcfs, behind /etc/pve) resolves the node's own name at start and needs the LAN address back; if /etc/hosts still holds the old IP, or maps the name to 127.0.1.1, pve-cluster won't start and pveproxy (the UI on 8006) has nothing to serve. A renamed host is worse: VM configs live under /etc/pve/nodes/OLDNAME, so the "new" node shows no VMs. After a kernel or firmware change, or the PVE 9 upgrade, predictable interface names can change (enp3s0 becomes enp4s0) while vmbr0's `bridge-ports` still names the old one, so the host boots with no network. And sometimes it's just http:// instead of https:// on 8006.

**Diagnose:**

```bash
# From the console or IPMI, not over SSH
hostname --ip-address                 # must print the LAN address, not 127.x
grep pve1 /etc/hosts
ip -br link
grep -n -E 'iface|address|bridge-ports' /etc/network/interfaces
journalctl -b -u pve-cluster --no-pager | grep -m1 crit
```

```text
127.0.1.1
127.0.1.1 pve1.example.lan pve1
lo        UNKNOWN  00:00:00:00:00:00 <LOOPBACK,UP,LOWER_UP>
enp4s0    DOWN     3c:ec:ef:12:34:56 <BROADCAST,MULTICAST>
vmbr0     DOWN     ae:61:9d:3b:7e:20 <NO-CARRIER,BROADCAST,MULTICAST,UP>
2:iface lo inet loopback
7:iface enp3s0 inet manual
10:iface vmbr0 inet static
11:        address 192.0.2.11/24
13:        bridge-ports enp3s0
Oct 03 07:02:11 pve1 pmxcfs[1187]: [main] crit: Unable to resolve node name 'pve1' to a non-loopback IP address - missing entry in '/etc/hosts' or DNS?
```

**What the output tells you:** two problems, both common after a move plus an upgrade. The node name resolves to 127.0.1.1, so pmxcfs stops with the crit message and the UI has no cluster filesystem. And the NIC is now called enp4s0 while vmbr0 still lists enp3s0 as its port, so the bridge has no carrier: the host is offline even with correct addresses.

**Fix:**

```bash
# 1. The node name must resolve to the LAN address
sed -i 's/^127\.0\.1\.1\s\+pve1.*/192.0.2.11 pve1.example.lan pve1/' /etc/hosts
# 2. Point the bridge at the NIC's current name and apply without a reboot (ifupdown2)
sed -i 's/\benp3s0\b/enp4s0/g' /etc/network/interfaces
ifreload -a
# 3. Restart the stack and reissue the node certificate for the right name and address
systemctl restart pve-cluster pveproxy
pvecm updatecerts --force
```

```ini
# 4. Pin the name to the MAC so the next kernel can't rename it:
#    /etc/systemd/network/10-nic0.link, then use nic0 in /etc/network/interfaces,
#    run update-initramfs -u -k all and reboot in a maintenance window
[Match]
MACAddress=3c:ec:ef:12:34:56

[Link]
Name=nic0
```

**Why this fix works:** pmxcfs uses the address the node name resolves to for cluster communication and certificates, so fixing /etc/hosts lets pve-cluster start and pveproxy serve 8006 again, and updatecerts reissues the node certificate for the new name and address. A `.link` file matched on the MAC address makes the name independent of PCI order and kernel naming; PVE 9 ships `pve-network-interface-pinning`, which generates such pins for every NIC as `nicX` names. In a cluster, don't change a node's IP or hostname casually: corosync.conf holds the addresses too, so follow the Cluster Manager docs, or remove, reinstall and rejoin the node.

**Prevent it:** a static management IP and a correct FQDN in /etc/hosts before you create a cluster, NIC names pinned before every upgrade (and `pve8to9 --full` before the move to 9), and out-of-band access (IPMI, iKVM, or at least a monitor) to every host.

**Next step:** [No IP after a reset or a hardware change (Ubuntu, TrueNAS, ESXi too)](42-problems-network-dns-tls-vpn.md#16-a-server-or-nas-gets-no-ip-after-a-reset-or-a-hardware-change) · [Network reference](02-network.md) · [Ports & inventory: who owns this port?](22-playbook-ports-inventory.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — Networking (Configure IPv4/IPv6 Networking and Hostname Resolution) · [Proxmox wiki: Upgrade from 8 to 9](https://pve.proxmox.com/wiki/Upgrade_from_8_to_9)

**Community threads:** [forum.proxmox.com: Unable to resolve node name to a non-loopback IP](https://forum.proxmox.com/threads/main-crit-unable-to-resolve-node-name-prox-to-a-non-loopback-ip-address-missing-entry-in-etc-hosts-or-dns.141719/) · [Proxmox wiki: Cluster Manager](https://pve.proxmox.com/wiki/Cluster_Manager) · [Proxmox wiki: Upgrade from 8 to 9](https://pve.proxmox.com/wiki/Upgrade_from_8_to_9) · Search: [Reddit r/Proxmox (IP change)](https://www.reddit.com/r/Proxmox/search/?q=changed+ip+web+interface+8006&restrict_sr=1) · [Reddit r/Proxmox (NIC names)](https://www.reddit.com/r/Proxmox/search/?q=network+interface+name+changed+after+upgrade&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=proxmox+web+interface+8006+not+accessible)

### 7.3 VLAN-tagged VMs get no network

> **Seen as:** a VM with `tag=20` on its NIC gets no DHCP lease and can't ping its gateway, while untagged VMs work · the host drops off the network after its bridge configuration changes · **Where:** VMs on separate VLANs (servers, DMZ, management) over one or two uplinks · **Level:** [L2 · Mid-level] · **How common:** a constant r/Proxmox and r/homelab question; the network chapter of the Proxmox admin guide covers VLAN-aware bridges and a management address on a VLAN

**Why it happens:** a VLAN tag on a VM's NIC only works if every hop agrees. Proxmox can carry tags two ways: a VLAN-aware bridge (`bridge-vlan-aware yes`, the usual choice, one bridge for all tags) or the traditional mode, where it builds a hidden bridge per tag (vmbr0v20) on a VLAN sub-interface. Either way, the bridge must allow that VLAN ID (`bridge-vids`), and the physical switch port must be a trunk that carries VLAN 20 tagged. That last part is the most common gap: the port is still an access port in the native VLAN, so tagged frames are dropped at the switch. The host itself falls off the network when its management address moves to a VLAN that the switch port or the host config doesn't match.

**Diagnose:**

```bash
qm config 101 | grep ^net
grep -A7 'iface vmbr0' /etc/network/interfaces
bridge -c vlan show dev tap101i0
# Do tagged frames leave the host, and does anything answer?
tcpdump -eni enp3s0 -c 2 vlan 20
```

```text
net0: virtio=BC:24:11:5A:6B:7C,bridge=vmbr0,tag=20
iface vmbr0 inet static
        address 192.0.2.11/24
        gateway 192.0.2.1
        bridge-ports enp3s0
        bridge-stp off
        bridge-fd 0
        bridge-vlan-aware yes
        bridge-vids 2-4094
port              vlan-id
tap101i0          20 PVID Egress Untagged
listening on enp3s0, link-type EN10MB (Ethernet), snapshot length 262144 bytes
07:41:02.113045 bc:24:11:5a:6b:7c > ff:ff:ff:ff:ff:ff, ethertype 802.1Q (0x8100), length 346: vlan 20, p 0, ethertype IPv4 (0x0800), 0.0.0.0.68 > 255.255.255.255.67: BOOTP/DHCP, Request from bc:24:11:5a:6b:7c, length 300
07:41:06.201377 bc:24:11:5a:6b:7c > ff:ff:ff:ff:ff:ff, ethertype 802.1Q (0x8100), length 346: vlan 20, p 0, ethertype IPv4 (0x0800), 0.0.0.0.68 > 255.255.255.255.67: BOOTP/DHCP, Request from bc:24:11:5a:6b:7c, length 300
```

**What the output tells you:** the Proxmox side is right: the bridge is VLAN-aware and allows 2–4094, the VM's tap port sits in VLAN 20, and its DHCP requests leave enp3s0 tagged 20. Nothing answers, so the frames die at the switch: the port isn't a trunk for VLAN 20, or VLAN 20 has no DHCP server or gateway. Had tcpdump shown no tagged frames at all, the problem would be on the host.

**Fix:**

```text
# Switch (vendor syntax differs): the uplink port is a trunk,
# native VLAN 1, allowed VLANs 10,20,30. Then test again with tcpdump.

# Target host layout: one VLAN-aware bridge, the host's own address on VLAN 10
# (/etc/network/interfaces; apply with ifreload -a only with the console open)
auto enp3s0
iface enp3s0 inet manual

auto vmbr0
iface vmbr0 inet manual
        bridge-ports enp3s0
        bridge-stp off
        bridge-fd 0
        bridge-vlan-aware yes
        bridge-vids 2-4094

auto vmbr0.10
iface vmbr0.10 inet static
        address 192.0.2.11/24
        gateway 192.0.2.1
```

```bash
qm set 101 --net0 virtio=BC:24:11:5A:6B:7C,bridge=vmbr0,tag=20
```

**Why this fix works:** a VLAN-aware bridge acts like a small managed switch: the VM's tap port is an access port in VLAN 20, the uplink carries every allowed VLAN tagged, and the physical switch has to mirror that with a trunk. Putting the host's own address on `vmbr0.10` keeps management traffic off the VM VLANs. ifupdown2 applies changes live, which is exactly why you keep a console open: a typo here cuts your SSH session.

**Prevent it:** document the VLAN plan (ID, subnet, gateway, DHCP) next to the switch config, change the switch trunk and the Proxmox bridge in the same change, test each VLAN with a throwaway VM, and consider Proxmox SDN zones once you run several nodes.

**Next step:** [Networking deep dive](28-learn-networking.md) · [Network speed playbook](24-playbook-network-speed.md) · KodeKloud: *DevOps Pre-Requisite Course* — Networking Basics (Switching and Routing) · [Proxmox VE documentation](https://pve.proxmox.com/pve-docs/)

**Community threads:** [forum.proxmox.com: most-viewed installation and configuration threads](https://forum.proxmox.com/forums/proxmox-ve-installation-and-configuration.16/?order=view_count&direction=desc) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=vlan+aware+bridge+no+network&restrict_sr=1) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=proxmox+vlan+trunk+no+dhcp&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=proxmox+vlan+aware+bridge+tagged+vm)

### 7.4 Cluster lost quorum

> **Seen as:** `cluster not ready - no quorum? (500)` · `pvecm status` shows `Quorate: No` · /etc/pve is read-only, so VMs can't be started, edited or created · **Where:** two-node homelab clusters, corosync sharing a busy link with storage or backup traffic, a node that died or was reinstalled · **Level:** [L2 · Mid-level] · **How common:** "[SOLVED] Remove node from cluster" has 386K views on forum.proxmox.com; quorum questions are constant on r/Proxmox and r/homelab

**Why it happens:** a Proxmox cluster only allows changes to /etc/pve while a majority of votes is present, so the two halves of a split cluster can't both write. In a two-node cluster, one node down leaves 1 vote of 2, which is not a majority, so the survivor goes read-only by design. Corosync is also latency-sensitive: if it shares a link with backups or Ceph and latency spikes, nodes drop out of the membership although they are up. A dead node that was never removed keeps counting as an expected vote.

**Diagnose:**

```bash
pvecm status | grep -E 'Quorate|Expected votes|Total votes|Quorum:'
corosync-cfgtool -s
journalctl -b -u corosync --no-pager | grep -m1 QUORUM
```

```text
Quorate:          No
Expected votes:   2
Total votes:      1
Quorum:           2 Activity blocked
Local node ID 1, transport knet
LINK ID 0 udp
        addr    = 192.0.2.11
        status:
                nodeid:          1:     localhost
                nodeid:          2:     disconnected
Oct 03 07:55:10 pve1 corosync[1342]:   [QUORUM] This node is within the non-primary component and will NOT provide any services.
```

**What the output tells you:** a two-node cluster with node 2 unreachable: 1 vote of the 2 needed, so activity is blocked. If pve2 is only rebooting, wait. If it is dead for good, you need either a third vote or a clean removal.

**Fix:**

```bash
# Emergency only, and only if pve2 is certainly OFF: let pve1 work alone for now
pvecm expected 1
# The lasting fix for two nodes: a QDevice on a third small machine
#   third machine:  apt install corosync-qnetd
#   both nodes:     apt install corosync-qdevice
pvecm qdevice setup 192.0.2.40
# Removing a dead node for good: power it off permanently, then on a quorate node
cp -r /etc/pve/nodes/pve2 /root/pve2-configs-backup
pvecm delnode pve2
rm -r /etc/pve/nodes/pve2
```

**Why this fix works:** `pvecm expected 1` lowers the votes needed, so the survivor can write again; it is safe only when the other node can't come back and write too, because two nodes each believing they are alone is split-brain. A QDevice adds a third vote from outside the cluster, so a two-node cluster keeps quorum when either node fails. `delnode` removes the dead node from corosync.conf so it stops counting. A removed node must be reinstalled before it ever joins again: its old cluster configuration would confuse the cluster.

**Prevent it:** an odd number of votes (three nodes, or two plus a QDevice), a dedicated corosync link plus a second redundant link, corosync kept away from Ceph and backup traffic, and no removed node ever reused without a reinstall.

**Next step:** [Senior architecture: Designing for availability](39-learn-senior-architecture.md#3-designing-for-availability) · [Slow system: Slow VM on a busy hypervisor](23-playbook-slow-system.md#13-scenario-slow-vm-on-a-busy-hypervisor) · KodeKloud: no Proxmox course; build a three-node nested lab and break it on purpose · [Proxmox wiki: Cluster Manager](https://pve.proxmox.com/wiki/Cluster_Manager)

**Community threads:** [Proxmox wiki: Cluster Manager](https://pve.proxmox.com/wiki/Cluster_Manager) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=no+quorum+two+node+qdevice&restrict_sr=1) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=proxmox+quorum+2+node&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=proxmox+cluster+no+quorum)

---

## 8. Proxmox VE: VMs, storage and backups

### 8.1 VM locked or frozen by a backup

> **Seen as:** `TASK ERROR: can't lock file '/var/lock/qemu-server/lock-101.conf' - got timeout` · `VM 101 is locked (backup)` · `VM 101 qmp command 'guest-fsfreeze-freeze' failed - got timeout` · the application in the VM hangs during the nightly backup · **Where:** a stuck backup, migration or snapshot; a guest agent that is enabled but not answering; Terraform or Packer firing many API calls in parallel · **Level:** [L1 · Junior] · **How common:** the forum's "can't lock file" thread has 277K views; "Backup crashes VM - guest-fsfreeze-freeze failed" is one of many long backup threads; Telmate provider issue #173 reports the same lock error from Terraform

**Why it happens:** every operation on a VM takes its lock file, and long operations (backup, migrate, snapshot) also write a `lock:` line into the VM config, so the next operation times out while they run or hang. The most common hang is a snapshot-mode backup with the guest agent option on: Proxmox asks the agent to freeze the guest's filesystems, and an agent that is outdated or stuck under heavy I/O (busy databases, Windows VSS) times out, or freezes and never thaws, so every write inside the guest blocks. Parallel API calls from Terraform or Packer, and hung storage such as an NFS target, produce the same lock timeout.

**Diagnose:**

```bash
qm config 101 | grep -E '^(lock|agent)'
ps -eo pid,etime,cmd | grep '[v]zdump'
qm agent 101 ping && echo "agent answers"
qm guest cmd 101 fsfreeze-status
```

```text
agent: 1
lock: backup
   2231   01:42:18 task UPID:pve1:000008B7:0012A3F1:6AC05328:vzdump:101:root@pam:
agent answers
"frozen"
```

**What the output tells you:** a backup of VM 101 has run for 1 h 42 min, the config is locked by it, and the guest's filesystems are still frozen: the freeze happened and the thaw never came. To the application this looks like a hung server, because every write waits.

**Fix:**

```bash
# 1. Thaw the guest first: writes resume immediately
qm guest cmd 101 fsfreeze-thaw
# 2. Stop the stuck backup task (Datacenter > Tasks > Stop), then clear the config lock
qm unlock 101
# 3. Inside the guest: a working, current agent
#      apt install --reinstall qemu-guest-agent && systemctl enable --now qemu-guest-agent
# 4. A guest that can't freeze reliably: keep the agent, skip the freeze
#    (sub-option name on PVE 9; check "man qm" on older releases)
qm set 101 --agent enabled=1,freeze-fs=0
# Terraform against Proxmox: serialise API calls
terraform apply -parallelism=1
```

**Why this fix works:** thawing first ends the outage inside the guest, whatever happens to the backup. Stopping the task releases the lock, and `qm unlock` removes the `lock:` line that a killed task can leave behind; never unlock while the task still runs, because two operations on one disk is how images get corrupted. A healthy agent makes freeze and thaw fast. For guests whose freeze is unreliable, skipping it trades filesystem-consistent backups for availability, so take the database's own dump as well. Serialised API calls stop automation from colliding on locks.

**Prevent it:** install and update qemu-guest-agent in every template, alert on failed and long-running backup jobs, use backup fleecing on newer releases when the backup target is slow, schedule backups off-peak, and limit API parallelism from automation.

**Next step:** [Databases, storage & backup problems](51-problems-databases-storage-backup.md) · [Databases: Backups that actually restore](38-learn-databases-ops.md#4-backups-that-actually-restore) · KodeKloud: no Proxmox course · [qm manual](https://pve.proxmox.com/pve-docs/qm.1.html)

**Community threads:** [forum.proxmox.com: can't lock file - got timeout](https://forum.proxmox.com/threads/trying-to-aquire-lock-task-error-cant-lock-file-var-lock-qemu-server.16235/) · [forum.proxmox.com: Backup crashes VM - guest-fsfreeze-freeze failed](https://forum.proxmox.com/threads/backup-crashes-vm-guest-fsfreeze-freeze-failed-got-timeout.104694/) · [Telmate provider issues by comments](https://github.com/Telmate/terraform-provider-proxmox/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=guest-fsfreeze-freeze+timeout+backup&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=proxmox+vm+locked+backup+qm+unlock)

### 8.2 PBS datastore full, and GC frees nothing

> **Seen as:** backup jobs fail with `No space left on device` · garbage collection fails with an `ENOSPC` error while updating chunk access times · snapshots were pruned, yet disk usage doesn't drop · **Where:** Proxmox Backup Server datastores on ZFS or ext4 that grew for months; retention shortened but no space came back · **Level:** [L2 · Mid-level] · **How common:** a recurring topic in the Backup Server section of forum.proxmox.com; the PBS maintenance docs explain why pruning alone frees nothing

**Why it happens:** PBS stores backups as deduplicated chunks shared between snapshots. Pruning removes only snapshot metadata (manifests and indexes); the chunks stay until garbage collection runs. GC has two phases: it marks every chunk still referenced by an index by updating its access time, then deletes chunks whose access time is older than a cutoff, 24 hours and 5 minutes before the GC started (or the start of the oldest running backup, if that is earlier). So space comes back only after prune, then GC, then a further day for recently touched chunks. Two things make it worse: ZFS snapshots of the dataset under the datastore, which pin every chunk GC deletes, and a pool so full that even the mark phase fails, because copy-on-write needs free space to update metadata.

**Diagnose:**

```bash
# On the Proxmox Backup Server
df -h /mnt/datastore/store1
zfs list -o name,used,avail,usedbysnapshots backup/store1
zfs list -t snapshot -o name,used -s used backup/store1 | tail -2
proxmox-backup-manager prune-job list
```

```text
Filesystem      Size  Used Avail Use% Mounted on
backup/store1   3.6T  3.6T  1.9G 100% /mnt/datastore/store1
NAME            USED  AVAIL  USEDSNAP
backup/store1  3.60T  1.90G      612G
backup/store1@autosnap_2026-09-01_00:00:01_monthly   143G
backup/store1@autosnap_2026-08-01_00:00:02_monthly   201G
```

**What the output tells you:** the dataset is full, and 612 GB of it is held by ZFS snapshots of the datastore itself, taken by a snapshot tool (sanoid) that someone pointed at the whole pool. No prune job is configured either. Even a successful GC couldn't free that space while the snapshots pin the chunks: first make room, then let PBS do its own cleanup.

**Fix:**

```bash
# 1. Make room: drop ZFS snapshots of the datastore (PBS keeps its own history),
#    and remove this dataset from the snapshot tool's config
zfs destroy backup/store1@autosnap_2026-08-01_00:00:02_monthly
zfs destroy backup/store1@autosnap_2026-09-01_00:00:01_monthly
# 2. Retention, then garbage collection: add a prune job in the GUI
#    (Datastore > Prune & GC: keep-daily 7, keep-weekly 4, keep-monthly 6, daily GC), then
proxmox-backup-manager garbage-collection start store1
# 3. An emergency valve for next time: an empty dataset holding a reservation
zfs create -o reservation=100G backup/headroom    # in a crisis: zfs set reservation=none backup/headroom
```

**Why this fix works:** ZFS snapshots under a PBS datastore duplicate what PBS already does and pin every deleted chunk, so removing them is what actually returns space. Prune then drops the snapshot indexes outside your retention, and GC deletes the chunks nothing references once their access time is older than the cutoff: chunks untouched for more than a day go in the first run, while chunks touched within the last day (by a recent GC or backup) only go in the next run a day later. A reserved empty dataset is a cheap emergency valve that gives GC room to run. Never delete files in `.chunks` by hand: you can't know which backups still reference them, and verify jobs would start failing.

**Prevent it:** prune and GC jobs on a schedule from day one, an alert at 80% datastore usage, no filesystem snapshots under a datastore, verify jobs that read back what you stored, and a regular test restore of one VM.

**Next step:** [Databases, storage & backup problems](51-problems-databases-storage-backup.md) · [Senior architecture: Disaster recovery](39-learn-senior-architecture.md#5-disaster-recovery) · [Storage & disk reference](01-storage-disk.md) · KodeKloud: no Proxmox course · [PBS docs: Maintenance tasks](https://pbs.proxmox.com/docs/maintenance.html)

**Community threads:** [PBS docs: Maintenance tasks (prune, garbage collection, verify)](https://pbs.proxmox.com/docs/maintenance.html) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=pbs+datastore+full+garbage+collection&restrict_sr=1) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=proxmox+backup+server+datastore+full&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=proxmox+backup+server+garbage+collection+space)

### 8.3 Host uses all RAM: ZFS ARC and OOM kills

> **Seen as:** `free -h` shows almost no available memory · `Out of memory: Killed process 31337 (kvm)` in `journalctl -k` · VMs stop at night while backups run · **Where:** ZFS on 32–64 GB hosts, especially installs older than PVE 8.1 or upgraded from them; consumer SSDs · **Level:** [L2 · Mid-level] · **How common:** a constant forum and r/Proxmox topic; Proxmox lowered the installer's default ARC size in 8.1 because of it

**Why it happens:** ZFS keeps its read cache, the ARC, in kernel memory. Installs from before PVE 8.1 set no limit, so the ZFS default applies: 50% of RAM on ZFS before 2.3, and 62.5% on ZFS 2.3 and later (PVE 9); newer installs default to 10%, capped at 16 GiB, but upgraded hosts keep whatever they had. The ARC does shrink under pressure, but not instantly, and when memory runs out the OOM killer picks the biggest process, which is almost always some VM's kvm. Overcommitted VM memory, swap on a ZFS zvol, and ballooning that never gives memory back make it worse; consumer SSDs without power-loss protection add I/O stalls that look like memory trouble.

**Diagnose:**

```bash
free -h
awk '/^(size|c_max) / {printf "%s %.1f GiB\n", $1, $3/2^30}' /proc/spl/kstat/zfs/arcstats
cat /sys/module/zfs/parameters/zfs_arc_max
journalctl -k --since -2d | grep -m1 -i 'out of memory'
qm list | awk 'NR>1 && $3=="running" {sum+=$4} END {print "running VM memory (MB):", sum}'
```

```text
               total        used        free      shared  buff/cache   available
Mem:            62Gi        59Gi       1.1Gi        74Mi       2.2Gi       2.0Gi
Swap:          8.0Gi       7.9Gi        85Mi
c_max 39.2 GiB
size 38.6 GiB
0
Oct 02 01:14:07 pve1 kernel: Out of memory: Killed process 31337 (kvm) total-vm:17384520kB, anon-rss:16801232kB, file-rss:2304kB, shmem-rss:0kB, UID:0 pgtables:33664kB oom_score_adj:0
running VM memory (MB): 36864
```

**What the output tells you:** the ARC may use 62.5% of the RAM (`zfs_arc_max` 0 means "the ZFS default" on this old install, and PVE 9's ZFS 2.3 raised that default from 50%) and currently holds 38.6 GiB, while the running VMs are promised 36 GiB on a 62 GiB host. Together they don't fit, so swap fills and the kernel kills a VM during the nightly backup, when I/O and cache pressure peak.

**Fix:**

```bash
# Cap the ARC (8 GiB here): now, and after every reboot
echo "$((8 * 1024**3))" > /sys/module/zfs/parameters/zfs_arc_max
echo "options zfs zfs_arc_max=$((8 * 1024**3))" > /etc/modprobe.d/zfs.conf
update-initramfs -u -k all
# Stop promising more memory than exists: shrink, balloon or move a VM
qm set 105 --memory 8192 --balloon 4096
```

**Why this fix works:** a fixed ARC cap turns "ZFS uses whatever it can" into a budget you can plan around: RAM = ARC + VMs + a few GiB for the host. The runtime write takes effect at once (the ARC shrinks over the next minutes), and the modprobe file plus initramfs make it survive reboots. Ballooning lets a VM give memory back when the host needs it, but only with the balloon driver in the guest. Don't put swap on a zvol, and don't run ZFS on top of hardware RAID: ZFS must see the disks directly, through an HBA in IT mode.

**Prevent it:** size RAM for the ARC plus all VMs, alert on memory pressure and swap use (node_exporter or a Proxmox exporter feeding Prometheus), scrub monthly, and prefer enterprise SSDs with power-loss protection for VM storage.

**Next step:** [Slow system: Memory pressure](23-playbook-slow-system.md#4-memory-pressure) · [Performance & observability: Memory deep dive](32-learn-performance-observability.md#5-memory-deep-dive) · [Observability stack problems](49-observability-stack-problems.md) · KodeKloud: no Proxmox course · [Proxmox wiki: ZFS on Linux](https://pve.proxmox.com/wiki/ZFS_on_Linux)

**Community threads:** [Proxmox wiki: ZFS on Linux](https://pve.proxmox.com/wiki/ZFS_on_Linux) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=zfs+arc+ram+usage+zfs_arc_max&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=proxmox+zfs+arc+memory+oom)

### 8.4 Ceph: degraded, nearfull or blocked I/O

> **Seen as:** `HEALTH_WARN` with `1 nearfull osd(s)` · `Degraded data redundancy: ... objects degraded` · `Reduced data availability: 12 pgs inactive` · `clock skew detected on mon.pve2` · VMs on Ceph freeze while a node is down · **Where:** hyper-converged Ceph on three Proxmox nodes, often over 1 GbE or on consumer SSDs · **Level:** [L3 · Senior] · **How common:** Ceph health questions fill the Ceph section of the Proxmox forum and r/Proxmox; "Ceph on three nodes with 1 GbE" is a perennial homelab debate

**Why it happens:** Ceph keeps each object on `size` OSDs (3 by default) and serves I/O only while at least `min_size` copies (2) are available. With one OSD or node down, placement groups (PGs) are degraded but active; when a PG drops below min_size, I/O to it blocks, and VMs experience that as a frozen disk. Capacity is the second trap: at 85% an OSD is nearfull (a warning), at 90% backfillfull (recovery stops writing to it), at 95% full, and then the cluster stops accepting writes. Because data is spread by weight, one fuller OSD reaches the limit long before the pool looks full. Ceph is also sensitive to the network (replication triples write traffic, so 1 GbE saturates), to clocks (monitors warn about skew) and to consumer SSDs, whose sync-write latency is poor.

**Diagnose:**

```bash
ceph -s
ceph osd df | head -4
ceph osd pool ls detail | grep -o "'[^']*' replicated size [0-9] min_size [0-9]"
```

```text
  cluster:
    health: HEALTH_WARN
            1 osds down
            1 nearfull osd(s)
            Degraded data redundancy: 90100/540600 objects degraded (16.667%), 64 pgs degraded, 64 pgs undersized
  services:
    mon: 3 daemons, quorum pve1,pve2,pve3 (age 3d)
    osd: 6 osds: 5 up (since 8m), 6 in (since 9w)
  data:
    usage:   2.1 TiB used, 700 GiB / 2.8 TiB avail
    pgs:     90100/540600 objects degraded (16.667%)
             65 active+clean
             64 active+undersized+degraded
ID  CLASS  WEIGHT   REWEIGHT  SIZE     RAW USE  DATA     OMAP    META     AVAIL    %USE   VAR   PGS  STATUS
 0    ssd  0.46489   1.00000  476 GiB  410 GiB  409 GiB  14 KiB  1.2 GiB   66 GiB  86.13  1.15   68      up
 1    ssd  0.46489   1.00000  476 GiB  331 GiB  330 GiB  11 KiB  1.0 GiB  145 GiB  69.54  0.93   61      up
 2    ssd  0.46489   1.00000  476 GiB  352 GiB  351 GiB  12 KiB  1.1 GiB  124 GiB  73.95  0.99   63      up
'.mgr' replicated size 3 min_size 2
'vm-pool' replicated size 3 min_size 2
```

**What the output tells you:** one OSD is down, so 64 placement groups run on two copies instead of three: degraded but still serving, because min_size is 2. Separately, osd.0 is at 86% while the average is about 75%; writes stop when one OSD reaches 95%, not when the pool is full, so that single OSD is your real capacity limit. Losing a second copy of any of those 64 PGs now would block I/O for the VMs on them.

**Fix:**

```bash
# Planned maintenance: stop Ceph from re-replicating while a node is briefly away
ceph osd set noout           # before the reboot
ceph osd unset noout         # after the node and its OSDs are back up
# Bring the OSD back (or replace the disk), then watch recovery to HEALTH_OK
systemctl status ceph-osd@4 --no-pager | grep Active
ceph -w
# Even out a too-full OSD, and add capacity before 80%
ceph balancer status
ceph osd reweight-by-utilization 110
```

**Why this fix works:** `noout` keeps a planned reboot from triggering a full re-replication of the node's data, which on a small cluster is slow and risky; when the OSD returns, recovery only copies what changed meanwhile. Balancing spreads data so all OSDs fill at the same rate, which raises the capacity you can really use. Never lower `min_size` to 1 to get I/O back: you would be accepting writes that exist in exactly one place, and losing that disk loses them. Don't set size 2 on a three-node cluster to save space either.

**Prevent it:** three nodes as the minimum and four or more for comfort, a dedicated 10/25 GbE network for Ceph, enterprise SSDs with power-loss protection, NTP on every node, alerts at 75% raw usage (well before nearfull), and Ceph health in your monitoring, not only in the GUI.

**Next step:** [Senior architecture: Capacity planning and performance budgets](39-learn-senior-architecture.md#6-capacity-planning-and-performance-budgets) · [Performance & observability: Disk deep dive](32-learn-performance-observability.md#6-disk-deep-dive) · [Databases, storage & backup problems](51-problems-databases-storage-backup.md) · KodeKloud: no Ceph or Proxmox course · [Ceph documentation](https://docs.ceph.com/) · [Proxmox VE documentation](https://pve.proxmox.com/pve-docs/)

**Community threads:** [forum.proxmox.com: most-viewed installation and configuration threads](https://forum.proxmox.com/forums/proxmox-ve-installation-and-configuration.16/?order=view_count&direction=desc) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=ceph+3+node+degraded+nearfull&restrict_sr=1) · [Reddit r/ceph](https://www.reddit.com/r/ceph/search/?q=nearfull+osd+min_size&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=ceph+HEALTH_WARN+nearfull+osd)

### 8.5 Docker inside an LXC container breaks

> **Seen as:** dockerd fails to start, or containers fail with overlay mount errors or AppArmor `permission denied` · bind-mounted files show as `nobody:nogroup` · it worked until a Proxmox upgrade · **Where:** Docker, Dokploy or k3s inside a Proxmox LXC container to save RAM · **Level:** [L2 · Mid-level] · **How common:** the "Unprivileged LXCs - Mount CIFS shares" tutorial on forum.proxmox.com has 441K views; Docker in LXC versus a VM is a perennial r/Proxmox debate

**Why it happens:** an LXC container shares the host's kernel and is confined by namespaces and AppArmor, so Docker inside it is nested containerisation with limited powers. Unprivileged containers need the `nesting` and `keyctl` features before dockerd works at all, and AppArmor still denies some mount operations. Overlay storage on a ZFS-backed root has historically failed, and Docker then falls back to the slow `vfs` driver. In an unprivileged container, root is UID 100000 on the host, so bind-mounted host directories owned by real UIDs show up as nobody:nogroup. And because the kernel and AppArmor policy belong to the host, a host upgrade can break the container with no change inside it; Docker Swarm (Dokploy) also needs kernel modules such as ip_vs that the container can't load.

**Diagnose:**

```bash
pct config 120 | grep -E '^(features|unprivileged|rootfs|mp[0-9])'
pct exec 120 -- docker info --format '{{.Driver}}'
dmesg | grep -m1 'apparmor="DENIED"'
ls -ln /tank/media | tail -1
```

```text
features: nesting=1
mp0: /tank/media,mp=/srv/media
rootfs: local-zfs:subvol-120-disk-0,size=32G
unprivileged: 1
vfs
[ 8812.402113] audit: type=1400 audit(1791010332.112:417): apparmor="DENIED" operation="mount" class="mount" info="failed flags match" error=-13 profile="lxc-120_</var/lib/lxc>" name="/run/containerd/" pid=48211 comm="containerd" flags="rw, rslave"
drwxr-xr-x 2 1000 1000 4096 Oct  1 18:20 photos
```

**What the output tells you:** an unprivileged container with nesting but without keyctl; Docker has fallen back to the vfs driver because overlay isn't usable on this ZFS subvolume; AppArmor denies a mount containerd needs; and the bind-mounted data belongs to UID 1000 on the host, which the container can't map, hence nobody:nogroup inside.

**Fix:**

```bash
# Preferred: move the workload into a VM cloned from your template (see 9.1)
qm clone 9000 130 --name docker-host --full
qm set 130 --memory 8192 --cores 4 --ipconfig0 ip=dhcp --sshkeys /root/.ssh/deploy.pub
# Staying on LXC for a simple single-service container:
pct set 120 --features nesting=1,keyctl=1
# Bind-mount ownership: host owner = 100000 + the UID used inside the container
chown -R 101000:101000 /tank/media
```

**Why this fix works:** a VM has its own kernel, so overlayfs, AppArmor, ip_vs and cgroups behave like on any Ubuntu server, live migration works, and host upgrades can't break the guest's container runtime; the Proxmox docs recommend VMs for application containers for these reasons. If you keep LXC, nesting and keyctl give dockerd what it needs, and shifting ownership by 100000 maps host files onto the container's UIDs (`lxc.idmap` entries are the finer-grained alternative). Don't switch to a privileged container to "fix" permissions: container root then is host root.

**Prevent it:** a VM for every container host, LXC only for simple single services (DNS, a small proxy, a small database), and a Packer-built VM template so a new Docker host takes minutes.

**Next step:** [Dokploy: Proxmox LXC, names resolve, connections hang](45-dokploy-and-self-hosted-paas.md#54-proxmox-lxc-names-resolve-connections-hang) · [Docker deep dive](30-learn-docker.md) · [Docker & K8s incidents](26-playbook-containers-k8s.md) · KodeKloud: *Docker Certified Associate* — Docker Swarm · [Proxmox wiki: Linux Container](https://pve.proxmox.com/wiki/Linux_Container)

**Community threads:** [Proxmox wiki: Linux Container](https://pve.proxmox.com/wiki/Linux_Container) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=docker+in+lxc+vs+vm&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=docker+inside+lxc+proxmox+overlay+apparmor)

---

## 9. Templates and image pipelines

### 9.1 Cloned cloud-init VMs share an IP or miss keys

> **Seen as:** every clone gets the same DHCP lease or hostname · `cloud-init status` says `disabled` · the SSH key isn't applied · with Terraform: the cloud-init drive is missing after the clone · **Where:** a golden Ubuntu template used by Terraform or Ansible, the on-prem replacement for AMIs · **Level:** [L2 · Mid-level] · **How common:** Telmate provider issues "Cloud-init drive delete when cloning" (#901, 48 comments), "No Cloud-init drive after creation" (#1104) and "cloud-init no longer working" (#944)

**Why it happens:** a template carries everything on its disk. If cloud-init already ran in it and `/etc/machine-id` was not cleared, every clone has the same machine-id, systemd-networkd derives its DHCP client identifier from it, and the DHCP server hands every clone the same address. Clones also need a cloud-init drive (`ide2: ...:cloudinit`) through which Proxmox passes the user, keys and network config; without it cloud-init finds no datasource and disables itself, and older provider versions sometimes dropped the drive during the clone. Ubuntu cloud images also expect a serial console, and without `ipconfig0` there is no network config to apply.

**Diagnose:**

```bash
qm config 9000 | grep -q '^ide2:.*cloudinit' || echo "template 9000 has no cloud-init drive"
qm config 9000 | grep -E '^(serial0|vga|ipconfig0|ciuser)'
# Inside two clones, from their consoles
cat /etc/machine-id
cloud-init status --long | grep -E '^(status|detail)'
```

```text
template 9000 has no cloud-init drive
serial0: socket
vga: serial0
clone 131: 5f2b3c9e1a7d4e8f9b0c1d2e3f4a5b6c
clone 132: 5f2b3c9e1a7d4e8f9b0c1d2e3f4a5b6c
status: disabled
detail: Cloud-init disabled by cloud-init-generator
```

**What the output tells you:** the template has no cloud-init drive and no user or network settings, so clones boot with cloud-init disabled: no user, no keys, no network config. Both clones share one machine-id, so the DHCP server sees one client and gives both the same address.

**Fix:**

```bash
# Inside the template VM, as the last step before shutdown: forget this instance
# (9000 already a template? It can't boot: full-clone it, fix the clone, template that instead)
sudo cloud-init clean --logs --machine-id && sudo poweroff
# On the host: cloud-init drive, serial console, defaults, then make it a template
qm set 9000 --ide2 local-lvm:cloudinit --serial0 socket --vga serial0 --boot order=scsi0
qm set 9000 --ciuser deploy --sshkeys /root/.ssh/deploy.pub --ipconfig0 ip=dhcp
qm template 9000
# Each clone: its own network settings, then regenerate its cloud-init image
qm clone 9000 133 --name app3 --full
qm set 133 --ipconfig0 ip=10.10.0.33/24,gw=10.10.0.1
qm cloudinit update 133
```

**Why this fix works:** `cloud-init clean` removes the record that cloud-init already ran and resets the machine-id to `uninitialized`, so each clone generates its own on first boot and gets its own DHCP identity, hostname and SSH host keys. The cloud-init drive is how Proxmox hands each clone its user, keys and network, and the serial console is what Ubuntu cloud images expect. With bpg/proxmox, an `initialization` block in the VM resource creates the drive for every clone, so it can't go missing.

**Prevent it:** build templates with Packer (proxmox-iso or proxmox-clone) so the cleanup runs every time, test every new template with two clones (two IPs, two machine-ids), and pin the Terraform provider version you tested.

**Next step:** [CI/CD, IaC & SRE: Terraform](33-learn-cicd-iac-sre.md#5-terraform) · [Cloud & AWS: AMIs, user data and cloud-init](36-learn-cloud-aws.md#amis-user-data-and-cloud-init) · KodeKloud: no Proxmox course; *Terraform Basics Training Course* for the Terraform side · [Proxmox wiki: Cloud-Init Support](https://pve.proxmox.com/wiki/Cloud-Init_Support)

**Community threads:** [Proxmox wiki: Cloud-Init Support](https://pve.proxmox.com/wiki/Cloud-Init_Support) · [Telmate provider issues by comments (#901, #1104, #944)](https://github.com/Telmate/terraform-provider-proxmox/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=cloud-init+template+same+ip+machine-id&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=proxmox+cloud-init+clone+same+ip+machine-id)

### 9.2 Packer: Missing plugins after an upgrade

> **Seen as:** `Error: Missing plugins` · `The builder amazon-ebs is unknown by Packer, and is likely part of a plugin that is not installed.` · **Where:** old JSON templates, fresh CI images, air-gapped build hosts · **Level:** [L1 · Junior] · **How common:** HashiCorp announced the removal of bundled plugins for Packer 1.10; HashiCorp Discuss has threads on `packer init` in offline environments

**Why it happens:** since Packer 1.10 the binary ships without plugins. Builders such as amazon-ebs, proxmox-iso and qemu, and provisioners such as ansible, are separate plugins that `packer init` installs from a `required_plugins` block. JSON templates can't declare that block, a fresh CI image has an empty plugin directory, and an air-gapped host can't download anything.

**Diagnose:**

```bash
packer version
packer plugins installed || true
grep -n 'required_plugins' *.pkr.hcl || echo "no required_plugins block"
```

```text
Packer v1.14.2
no required_plugins block
```

**What the output tells you:** a current Packer with no plugins installed and a template that never declares any, so Packer has no idea where amazon-ebs or proxmox-iso should come from.

**Fix:**

```hcl
# plugins.pkr.hcl
packer {
  required_plugins {
    proxmox = {
      source  = "github.com/hashicorp/proxmox"
      version = "~> 1"
    }
    amazon = {
      source  = "github.com/hashicorp/amazon"
      version = "~> 1"
    }
  }
}
```

```bash
packer hcl2_upgrade -with-annotations template.json     # JSON templates first
packer init . && packer validate .
# Air-gapped host: install a downloaded, checksum-verified plugin binary
packer plugins install --path ./packer-plugin-proxmox_v1.2.3_x5.0_linux_amd64 github.com/hashicorp/proxmox
```

**Why this fix works:** `required_plugins` pins where each plugin comes from and which versions are acceptable, and `packer init` installs exactly those, the same way `terraform init` handles providers. Converting JSON to HCL2 is required because only HCL2 templates can declare plugins. On offline hosts, installing a verified local binary (or pointing PACKER_PLUGIN_PATH at a mirrored directory) gives the same result without internet access.

**Prevent it:** pin plugin versions, run `packer init` and `packer validate` in CI on every change, and bake the plugins into your CI image.

**Next step:** [CI/CD toolbox: Building images in CI](47-cicd-gitlab-jenkins-actions-argocd.md#6-building-images-in-ci) · KodeKloud: no Packer course · [Packer docs](https://developer.hashicorp.com/packer/docs)

**Community threads:** [HashiCorp: Announcing the removal of bundled plugins in Packer](https://www.hashicorp.com/en/blog/announcing-the-removal-of-bundled-plugins-in-hashicorp-packer) · [HashiCorp Discuss: Packer init and offline environments](https://discuss.hashicorp.com/t/packer-init-and-offline-environments/63847) · Search: [Stack Overflow](https://stackoverflow.com/search?q=packer+%22Missing+plugins%22+required_plugins) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=packer+missing+plugins&restrict_sr=1)

### 9.3 Packer never gets SSH

> **Seen as:** `==> proxmox-iso.ubuntu: Waiting for SSH to become available...` and later `Timeout waiting for SSH.` · `ssh: handshake failed: ssh: unable to authenticate, attempted methods [none publickey]` · **Where:** Ubuntu 22.04/24.04 ISO builds on Proxmox with autoinstall files served by Packer's HTTP server; amazon-ebs AMI builds in GitLab CI · **Level:** [L2 · Mid-level] · **How common:** hashicorp/packer #9115 (Ubuntu autoinstall builds) is among the most-commented Packer issues (about 140 comments); #788 (46 comments) and #10074 (ssh-rsa deprecation, 46 comments) for the AMI case

**Why it happens:** Packer connects only once the machine is installed, has an IP Packer knows, and accepts its credentials. For ISO builds the usual break is that the install never happens: Ubuntu 20.04 and later use subiquity autoinstall, so old preseed `boot_command`s are ignored; the command is typed before GRUB is ready (boot_wait too short) or the `;` isn't escaped for GRUB; the VM can't reach Packer's HTTP server because the build host's firewall blocks its port (random, 8000–9000 by default) or it binds the wrong interface; the user-data isn't valid (it must start with `#cloud-config` and needs a meta-data file next to it); or qemu-guest-agent is missing, so Packer never learns the VM's IP. For AMI builds the instance is up but login fails: the wrong `ssh_username` for the source AMI (ubuntu, ec2-user or admin), or an older Packer offering an ssh-rsa SHA-1 key that OpenSSH 8.8 and later reject. A build in a private subnet without a public IP times out instead.

**Diagnose:**

```bash
# Watch the VM's console in the Proxmox GUI during the build: does the installer run at all?
PACKER_LOG=1 packer build -on-error=ask . 2>&1 | tee packer.log \
  | grep -E 'Starting HTTP server|Waiting for SSH|handshake'
# Build host: is Packer's HTTP port open to the VM network?
sudo ufw status | grep -E '\b8[0-9]{3}\b' || echo "no ufw rule for the packer http port"
# From the installer's shell on the VM console: can it fetch the user-data?
curl -sS -m 10 http://192.0.2.50:8802/user-data | head -1
```

```text
2026/10/03 10:02:14 ui: ==> proxmox-iso.ubuntu: Starting HTTP server on port 8802
2026/10/03 10:02:31 ui: ==> proxmox-iso.ubuntu: Waiting for SSH to become available...
no ufw rule for the packer http port
curl: (28) Connection timed out after 10002 milliseconds
```

**What the output tells you:** Packer serves the autoinstall files on 8802, but the installer can't reach that port: UFW on the build host has no rule for it and drops the requests. The installer never gets its user-data, so it waits for a human, and Packer waits for SSH until it times out.

**Fix:**

```hcl
source "proxmox-iso" "ubuntu" {
  # ... node, API token, boot_iso, disks, network ...
  http_directory    = "http"                 # user-data plus an empty meta-data file
  http_bind_address = "192.0.2.50"
  http_port_min     = 8802
  http_port_max     = 8802
  boot_wait         = "10s"
  boot_command = [
    "<esc><wait>e<wait><down><down><down><end>",
    " autoinstall ds=nocloud-net\\;s=http://{{ .HTTPIP }}:{{ .HTTPPort }}/<f10>"   # \\ in HCL types one \ for GRUB
  ]
  qemu_agent   = true                        # install qemu-guest-agent via autoinstall packages
  ssh_username = "packer"
  ssh_timeout  = "30m"
}
# AMI builds: the right user, a modern temporary key, and a reachable address
source "amazon-ebs" "ubuntu" {
  # ... region, source_ami_filter with owners, instance_type ...
  ssh_username                = "ubuntu"
  temporary_key_pair_type     = "ed25519"
  associate_public_ip_address = true         # or ssh_interface = "session_manager" + an instance profile
}
```

```bash
sudo ufw allow from 192.0.2.0/24 to any port 8802 proto tcp
```

**Why this fix works:** a fixed HTTP port bound to the build host's address, and allowed through UFW from the VM subnet, lets the installer fetch its autoinstall config; the escaped semicolon survives GRUB's parser, and the guest agent tells Packer the VM's IP after the reboot. You can also skip the HTTP server entirely by putting user-data and meta-data on a small ISO (`cd_files` with `cd_label = "cidata"`, inside an `additional_iso_files` block on proxmox-iso). On AWS, the right user and an ed25519 temporary key satisfy modern OpenSSH, and a public IP or Session Manager gives Packer a path in. Don't paper over the timeout with a huge ssh_timeout alone: watch the console first, it shows which step stalls.

**Prevent it:** keep templates and autoinstall files in Git, pin ISO checksums and plugin versions, test new Ubuntu point releases in CI, and build in a dedicated build subnet or VLAN whose firewall rules live in the template repository.

**Next step:** [CI/CD toolbox: Building images in CI](47-cicd-gitlab-jenkins-actions-argocd.md#6-building-images-in-ci) · [Cloud & AWS: AMIs, user data and cloud-init](36-learn-cloud-aws.md#amis-user-data-and-cloud-init) · [SSH & remote access](09-ssh-remote-access.md) · KodeKloud: no Packer course · [Packer Proxmox ISO builder](https://developer.hashicorp.com/packer/integrations/hashicorp/proxmox/latest/components/builder/iso)

**Community threads:** [hashicorp/packer #9115](https://github.com/hashicorp/packer/issues/9115) · [hashicorp/packer #10074](https://github.com/hashicorp/packer/issues/10074) · [hashicorp/packer issues by comments (#788)](https://github.com/hashicorp/packer/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=packer+waiting+for+ssh+autoinstall&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=packer+amazon-ebs+%22unable+to+authenticate%22+%22attempted+methods+%5Bnone+publickey%5D%22)

### 9.4 Terraform and Proxmox: 400s, permissions, crashes

> **Seen as:** `Error: The terraform-provider-proxmox_v2.9.14 plugin crashed!` · `Error: 400 Parameter verification failed.` · `Error: 500 can't lock file` · `Permission check failed (/sdn/zones/localnetwork/vmbr0, SDN.Use)` · duplicate disks after an apply · **Where:** IaC for an on-prem Proxmox cluster with the community providers telmate/proxmox or bpg/proxmox · **Level:** [L3 · Senior] · **How common:** Telmate issues #863 plugin crash (86 comments), #887 duplicate disks (53), #784 "Too many permissions needed" (29) and #1201 (31)

**Why it happens:** both providers are community projects tracking a moving API. Releases lag behind Proxmox changes, so a new PVE version can crash an older provider, or produce "400 Parameter verification failed" when the provider sends a parameter the API now rejects. Telmate changed its disk schema between 2.9 and 3.0, so old disk blocks plan duplicate or reordered disks. Permissions are the other half: PVE 8 added the SDN.Use privilege for attaching NICs to bridges, PVE 9 deprecated VM.Monitor, and API tokens are privilege-separated by default, so a token can hold fewer rights than its user. Parallel clones collide on VM locks (entry 8.1).

**Diagnose:**

```bash
TF_LOG=DEBUG terraform apply -parallelism=1 2> tf-debug.log
grep -m1 -E 'Permission check failed|panic:|Parameter verification failed' tf-debug.log
pveversion
pveum user token list terraform@pve
```

```text
Error: error creating VM: received an HTTP 403 response - Reason: Permission check failed (/sdn/zones/localnetwork/vmbr0, SDN.Use)
pve-manager/9.0.11/3bf5476b8a4699e2 (running kernel: 6.14.11-4-pve)
┌─────────┬─────────┬────────┬─────────┐
│ tokenid │ comment │ expire │ privsep │
╞═════════╪═════════╪════════╪═════════╡
│ ci      │         │      0 │ 1       │
└─────────┴─────────┴────────┴─────────┘
```

**What the output tells you:** the API refuses the NIC because the token lacks SDN.Use on the bridge, and the token is privilege-separated (privsep 1): it only has the rights granted to the token itself, not the role its user holds. With the PVE version written down, you can match it against the provider's release notes.

**Fix:**

```bash
# A dedicated role (the PVE 9 list; on PVE 8 also add VM.Monitor; an existing role: pveum role modify)
pveum role add TerraformProv -privs "Datastore.AllocateSpace Datastore.AllocateTemplate Datastore.Audit Pool.Allocate Pool.Audit Sys.Audit Sys.Console Sys.Modify VM.Allocate VM.Audit VM.Clone VM.Config.CDROM VM.Config.Cloudinit VM.Config.CPU VM.Config.Disk VM.Config.HWType VM.Config.Memory VM.Config.Network VM.Config.Options VM.Migrate VM.PowerMgmt SDN.Use"
pveum aclmod / -user terraform@pve -role TerraformProv
# A privilege-separated token needs its own ACL as well
pveum aclmod / -token 'terraform@pve!ci' -role TerraformProv
# Pin the provider you tested (versions.tf: source = "bpg/proxmox", version = "~> 0.70"),
# then prove nothing drifts before adding VMs: exit code 0 means no changes
terraform plan -detailed-exitcode
```

**Why this fix works:** a role built for the provider grants what it needs on the paths it touches, including SDN.Use for bridges on PVE 8 and later, and granting it to the token too matters because a privilege-separated token's effective rights are the intersection of the user's and the token's own ACLs. Pinning the provider stops a surprise upgrade from changing the disk schema under existing VMs; moving from Telmate to bpg, or across a schema change, is done with import blocks and a no-change plan as the gate. Don't hand Terraform the root@pam password, and don't switch TLS verification off in production: give Proxmox a certificate from your private CA instead.

**Prevent it:** test provider and PVE upgrades on the lab cluster first, commit the lock file, clone from Packer-built templates, and keep a no-change `terraform plan` as the first job after any upgrade.

**Next step:** [CI/CD, IaC & SRE: Terraform](33-learn-cicd-iac-sre.md#5-terraform) · [Security: TLS and PKI](37-learn-security-devsecops.md#4-tls-and-pki) · KodeKloud: *Terraform Basics Training Course* — Import, Taint and Debugging · [Telmate provider docs: user, role and token setup](https://github.com/Telmate/terraform-provider-proxmox/blob/master/docs/index.md)

**Community threads:** [Telmate provider issues by comments](https://github.com/Telmate/terraform-provider-proxmox/issues?q=is%3Aissue+sort%3Acomments-desc) · [Telmate provider docs](https://github.com/Telmate/terraform-provider-proxmox/blob/master/docs/index.md) · Search: [Stack Overflow](https://stackoverflow.com/search?q=terraform+proxmox+provider+%22Permission+check+failed%22) · [Reddit r/Proxmox](https://www.reddit.com/r/Proxmox/search/?q=terraform+provider+bpg+telmate&restrict_sr=1) · [Reddit r/Terraform](https://www.reddit.com/r/Terraform/search/?q=proxmox+provider&restrict_sr=1)

---

## Self-check

Ten timed break-and-fix exercises. Use an AWS sandbox account (destroy everything afterwards) and your Proxmox lab. Snapshot first, break it exactly as described, then fix it using only the entry and write your five-line note.

| # | Stage | Break it | Fix within | Entry |
|---|---|---|---|---|
| 1 | Fresher | Launch an EC2 instance whose security group allows SSH only from an address that isn't yours | 10 min | 1.1 |
| 2 | Fresher | Fresh Proxmox install: run apt update with only the enterprise repositories enabled | 10 min | 7.1 |
| 3 | Junior | Give a CI role s3:ListBucket only, then upload an object to an SSE-KMS bucket | 15 min | 1.2 |
| 4 | Junior | Cancel a GitLab apply job mid-run, then plan again | 15 min | 3.3 |
| 5 | Junior | Template a VM without cleaning its machine-id; boot two clones on DHCP | 20 min | 9.1 |
| 6 | Mid-level | Rename a resource and move it into a module; reach "0 to destroy" | 20 min | 4.3 |
| 7 | Mid-level | Put a NAT gateway in a private subnet, then restore internet access for the app subnet | 25 min | 2.1 |
| 8 | Mid-level | Two-node lab cluster: stop one node, restore writes safely, then add a QDevice | 30 min | 7.4 |
| 9 | Senior | Make the ALB health check get a 301 and set the app's keep-alive to 5 s; find both from evidence | 30 min | 2.4 |
| 10 | Senior/Lead | Write a rolling Ansible play with a canary and a health gate, then break the canary on purpose | 45 min | 6.6 |

Quick questions to answer from memory:

1. What separates "no identity-based policy allows" from "with an explicit deny in a service control policy", and who fixes each?
2. Why does `terraform plan` take the state lock, and when is `force-unlock` safe?
3. What does `sensitive = true` not protect, and which two approaches keep a secret out of state entirely?
4. Why does a two-node Proxmox cluster go read-only when one node dies, and what are the two correct fixes?
5. Why can a PBS datastore free space only a day after you prune?
6. Why do containers on an EC2 host fail to get credentials when the host itself works?

---

## Where to go next

- [Cloud & AWS](36-learn-cloud-aws.md): IAM evaluation, VPC routing, load balancers and cost, from first principles; the background for sections 1 and 2.
- [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md): the Ansible and Terraform fundamentals behind sections 3 to 6.
- [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md): Terraform, Ansible and Packer inside GitLab CI, with runners, protected variables and image builds.
- [Observability stack problems](49-observability-stack-problems.md): alerts for disk, memory, backup jobs and Ceph health, so these problems page you before users do.
- [Databases, storage & backup problems](51-problems-databases-storage-backup.md): restic, borg, PBS and restore drills.
- [Wazuh & security tools](48-wazuh-and-security-tools.md): Vault and OpenBao for the secrets in 3.4 and 6.2, and monitoring for the hosts you build here.
- [Dokploy & self-hosted PaaS](45-dokploy-and-self-hosted-paas.md): what runs on the VMs these templates produce.
- [Slow system](23-playbook-slow-system.md) and [Performance & observability](32-learn-performance-observability.md): memory and disk pressure on hypervisors and their guests.
- [Senior architecture](39-learn-senior-architecture.md) and [Databases ops](38-learn-databases-ops.md): DR, capacity and cost decisions at platform level.
- Official docs: [AWS](https://docs.aws.amazon.com/) · [Terraform](https://developer.hashicorp.com/terraform/docs) · [OpenTofu](https://opentofu.org/docs/) · [Ansible](https://docs.ansible.com/) · [Proxmox VE](https://pve.proxmox.com/pve-docs/) · [Packer](https://developer.hashicorp.com/packer/docs).
