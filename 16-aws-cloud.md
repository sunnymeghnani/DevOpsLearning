# 16 — AWS Troubleshooting

Everything from sections 01–13 applies inside an EC2 instance. This file covers
the AWS-specific layer around it. Two golden AWS facts:

1. **Security Groups are stateful** (return traffic auto-allowed) and have only
   allow rules. **NACLs are stateless** (must allow BOTH directions, including
   ephemeral ports 1024–65535) and have deny rules. Most "timeout" issues = SG;
   weird one-direction issues = NACL.
2. When APIs fail mysteriously: **wrong region, wrong profile, wrong credentials,
   or clock skew** — check those before anything clever.

---

## 1. CLI identity & config sanity (start EVERY session here)

```bash
aws sts get-caller-identity                # WHO am I? (account, role/user) ★
aws configure list                         # which profile/region/keys are active
aws configure list-profiles
echo $AWS_PROFILE $AWS_DEFAULT_REGION      # env overrides trump config files
aws ec2 describe-instances --region ap-south-1 --query 'Reservations[].Instances[].InstanceId'
                                           # "it's not there!" → usually WRONG REGION
aws sts get-caller-identity --debug 2>&1 | grep -i credential   # where creds came from
```
```
$ aws sts get-caller-identity
{
    "UserId": "AROA3XFRBF535PLBIFPI4:ops",
    "Account": "111122223333",                          ← the RIGHT account?
    "Arn": "arn:aws:sts::111122223333:assumed-role/DevOpsRole/ops"
}                                                       ← the role you THINK you have?
```
Wrong account or an unexpected role here explains most "AccessDenied" and
"resource not found" surprises before you debug anything else.

- `ExpiredToken` → refresh SSO/assume-role: `aws sso login` / new STS creds
- `AccessDenied ... is not authorized to perform X on Y` → the error names the
  missing IAM permission — read it literally; check for explicit Deny in SCPs too
- `SignatureDoesNotMatch` / `RequestTimeTooSkewed` → clock skew → 12-time-ntp.md
- CLI hangs on EC2 with no internet → it's trying IMDS/API without a route:
  NAT GW / VPC endpoints missing

## 2. Instance metadata (IMDS) — from inside an instance

```bash
TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" \
        -H "X-aws-ec2-metadata-token-ttl-seconds: 300")          # IMDSv2 token
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/iam/security-credentials/<role-name>
                                           # ★ are role creds actually being served? expiry?
curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/user-data
```
- IMDSv2 enforced (normal now) → plain `curl http://169.254.169.254/...` returns
  401 — you must use the token dance above.
- App in a container can't get role creds → IMDS hop limit:
  `aws ec2 modify-instance-metadata-options --instance-id i-x --http-put-response-hop-limit 2`

## 3. EC2 instance health

```bash
aws ec2 describe-instance-status --instance-ids i-0abc123 --include-all-instances
# SystemStatus   = AWS-side (host hardware/network)  → impaired: stop/start moves host
# InstanceStatus = your-side (OS reachable)          → impaired: OS issue, see console
aws ec2 get-console-output --instance-id i-0abc123 --latest --output text | tail -50
                                           # ★ boot log when SSH is dead (kernel panic,
                                           #   fstab hang, cloud-init failure)
aws ec2 get-console-screenshot --instance-id i-0abc123 --query ImageData --output text | base64 -d > screen.jpg   # the console as a JPG
aws ec2 describe-instances --instance-ids i-0abc123 \
  --query 'Reservations[].Instances[].[State.Name,StateTransitionReason]'
aws ec2 reboot-instances --instance-ids i-0abc123
# stop + start (NOT reboot) migrates to new hardware — fixes host-level issues;
# ⚠ changes public IP unless EIP; instance-store data is lost
```
Inside the instance, first-boot problems live in:
```bash
cat /var/log/cloud-init-output.log         # ★ user-data script output/errors
cat /var/log/cloud-init.log
cloud-init status --long
```

### CPU credits (t2/t3/t4g "mysteriously slow")
```bash
# symptom inside VM: high %st in top
aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUCreditBalance \
  --dimensions Name=InstanceId,Value=i-0abc123 --statistics Average \
  --start-time 2026-08-09T00:00:00Z --end-time 2026-08-09T12:00:00Z --period 3600
# balance ≈ 0 → throttled → bigger instance, non-burstable family, or unlimited mode
```

## 4. EBS volumes

```bash
aws ec2 describe-volumes --volume-ids vol-0abc --query 'Volumes[].[State,Attachments]'
aws ec2 describe-volume-status --volume-ids vol-0abc      # impaired?
lsblk ; sudo file -s /dev/xvdf                            # inside: attached? formatted?
# resize flow: modify → grow partition → grow fs (all online):
aws ec2 modify-volume --volume-id vol-0abc --size 200
aws ec2 describe-volumes-modifications --volume-ids vol-0abc   # wait: optimizing/completed
growpart /dev/xvda 1 && (resize2fs /dev/xvda1 || xfs_growfs /)
```
- Volume stuck "attaching" → wrong device name in use, or instance in bad state
- I/O crawling → gp2 burst exhausted / IOPS cap → CloudWatch `VolumeQueueLength`,
  `BurstBalance`; upgrade to gp3 and set IOPS explicitly
- Nitro instances: volumes show as `/dev/nvme*` — map with `lsblk -o NAME,SERIAL`
  (serial = vol-id)

## 5. VPC networking — the timeout checklist

For "instance A can't reach instance B on port P", check IN ORDER:
```bash
# 1. B's Security Group allows P from A's SG or CIDR?
aws ec2 describe-security-groups --group-ids sg-0abc \
  --query 'SecurityGroups[].IpPermissions'
# 2. NACLs on BOTH subnets allow the traffic AND the return (ephemeral 1024-65535)?
aws ec2 describe-network-acls --filters Name=association.subnet-id,Values=subnet-0abc
# 3. Route tables actually route A→B (and back)?
aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=subnet-0abc
# 4. A's OUTBOUND SG rules (people forget these exist when tightened)
# 5. OS firewall on B (iptables/firewalld) + service bound to 0.0.0.0? (ss -tlnp)
```
Faster: **VPC Reachability Analyzer** does this whole analysis:
```bash
aws ec2 create-network-insights-path --source i-0aaa --destination i-0bbb \
  --destination-port 443 --protocol tcp
aws ec2 start-network-insights-analysis --network-insights-path-id nip-0abc
aws ec2 describe-network-insights-analyses --network-insights-analysis-ids nia-0abc
                                           # → NetworkPathFound: false + the exact
                                           #   component that blocks it ★
```
Internet access from private subnet: needs NAT GW in a PUBLIC subnet + route
`0.0.0.0/0 → nat-...` in the private route table. Public subnet: IGW route +
public IP on the instance + SG/NACL.

**VPC Flow Logs** — see accepts/rejects per ENI:
```
version account eni src dst srcport dstport proto packets bytes start end action status
2 111122223333 eni-0abc 10.0.1.5 10.0.2.9 43512 443 6 8 3620 ... REJECT OK
```
`REJECT` = SG or NACL said no. Query in CloudWatch Logs Insights:
```
fields @timestamp, srcAddr, dstAddr, dstPort, action
| filter action = "REJECT" and dstPort = 443
| sort @timestamp desc | limit 50
```

## 6. Load balancers (ALB/NLB)

```bash
aws elbv2 describe-target-health --target-group-arn arn:...:targetgroup/tg/abc
# ★ THE command: State + Reason for every target
```
```
$ aws elbv2 describe-target-health --target-group-arn arn:...:tg/web/abc \
    --query 'TargetHealthDescriptions[].[Target.Id,TargetHealth.State,TargetHealth.Reason]'
[
    [ "i-0aaa111", "healthy",   null ],
    [ "i-0bbb222", "unhealthy", "Target.ResponseCodeMismatch" ],
    [ "i-0ccc333", "unhealthy", "Target.Timeout" ]
]
```
Reason codes decoded:

- `Target.ResponseCodeMismatch` → target answers, but the health-check path
  returns the wrong status (redirect 301? app error 500?) — curl it from the box
- `Target.Timeout` → no answer at all: SG doesn't allow LB→target on the health
  port, or the app is too slow/hung
- `Target.FailedHealthChecks` → generic failure — check app + SG both
- `Elb.RegistrationInProgress` → just registered, wait
```bash
aws elbv2 describe-listeners --load-balancer-arn ...
aws elbv2 describe-target-groups --target-group-arn ... \
  --query 'TargetGroups[].[HealthCheckPath,HealthCheckPort,Matcher]'
curl -v http://localhost:8080/health        # from the target itself: does the health
                                            # check path actually return 200?
```
502/503/504 from an ALB: 502 = target sent garbage/reset (app crashed mid-request,
keepalive shorter than ALB idle timeout); 503 = no registered targets in the target
group (if every registered target is unhealthy, the ALB fails open and still sends them
traffic); 504 = target didn't answer in time. Enable ALB access logs to S3 for per-request evidence.

## 7. SSM — access without SSH

```bash
aws ssm describe-instance-information       # ★ which instances SSM can manage;
                                            #   missing instance = agent/role/network issue
aws ssm start-session --target i-0abc123    # interactive shell, no port 22
aws ssm send-command --instance-ids i-0abc123 --document-name "AWS-RunShellScript" \
  --parameters 'commands=["df -h","systemctl --failed"]'
aws ssm list-command-invocations --command-id <id> --details \
  --query 'CommandInvocations[].CommandPlugins[].Output'
# on the instance:
systemctl status amazon-ssm-agent ; journalctl -u amazon-ssm-agent -e
```
Instance not in SSM: role lacks `AmazonSSMManagedInstanceCore`, agent stopped, or
no path to SSM endpoints (needs internet/NAT or the ssm/ssmmessages/ec2messages
VPC endpoints).

## 8. CloudWatch from the CLI

```bash
aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0abc123 --statistics Average Maximum \
  --start-time 2026-08-09T00:00:00Z --end-time 2026-08-09T12:00:00Z --period 300
aws logs tail /aws/lambda/myfn --follow            # ★ live log tail
aws logs filter-log-events --log-group-name /app/prod \
  --filter-pattern "ERROR" --start-time $(date -d '1 hour ago' +%s)000
aws logs start-query --log-group-name /app/prod --query-string \
  'fields @timestamp,@message | filter @message like /ERROR/ | sort @timestamp desc | limit 50' \
  --start-time $(date -d '1 hour ago' +%s) --end-time $(date +%s)
aws cloudwatch describe-alarms --state-value ALARM   # what's firing right now ★
```
Note: EC2 memory & disk metrics need the CloudWatch Agent — they are NOT default.

## 9. Other high-value one-liners

```bash
# S3 access denied? test the exact op; check bucket policy + Block Public Access + SCP
aws s3 ls s3://bucket/prefix/ ; aws s3api get-bucket-policy --bucket bucket
# RDS status/endpoint/recent events (failovers, storage-full):
aws rds describe-db-instances --db-instance-identifier mydb \
  --query 'DBInstances[].[DBInstanceStatus,Endpoint.Address]'
aws rds describe-events --duration 1440
# Lambda: recent errors
aws lambda get-function --function-name myfn --query 'Configuration.[State,LastUpdateStatus]'
aws logs tail /aws/lambda/myfn --since 1h --filter-pattern ERROR
# Who changed it? CloudTrail:
aws cloudtrail lookup-events --lookup-attributes \
  AttributeKey=ResourceName,AttributeValue=i-0abc123 --max-results 20   # ★ audit trail
# Account-level health events:
aws health describe-events --filter eventStatusCodes=open 2>/dev/null   # (Business support)
# IAM: simulate whether a principal CAN do an action:
aws iam simulate-principal-policy --policy-source-arn arn:aws:iam::111122223333:role/app \
  --action-names s3:GetObject --resource-arns arn:aws:s3:::bucket/key
```

## Decision trees

```
Can't SSH to EC2:
  nc -zv <ip> 22 timeout? → SG inbound 22 from YOUR current IP? subnet route/IGW? NACL?
  refused/creds problems? → 09-ssh-remote-access.md (wrong username per AMI!)
  instance sick?          → describe-instance-status; get-console-output (fstab hang, panic)
  no luck?                → aws ssm start-session (bypasses network entirely)

Website on EC2 down:
  instance up? → status checks → console output
  app up?      → ssm/ssh: systemctl status app ; ss -tlnp ; curl localhost:port
  LB healthy?  → describe-target-health (reason codes!)
  DNS right?   → dig yourdomain → points at the LB/EIP?
  path open?   → SG (LB→instance, world→LB), NACL, Reachability Analyzer
```
