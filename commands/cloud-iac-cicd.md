# Cloud, IaC, Proxmox & CI/CD

These commands change infrastructure at a distance, so the order matters: first prove who and where you are (`aws sts get-caller-identity`, `terraform workspace show`, `ansible-inventory --graph`), then read the current state (`describe-*` calls, `terraform plan`, `--check --diff`, `qm config`, `pvecm status`), then change one thing through a reviewed plan, with Git as the record and `git revert` as the way back. Most of them can touch many machines in one run, so each card marks the forms that change state.

| If you would reach for | Prefer | Because |
|---|---|---|
| `aws configure list` for "which account am I in?" | `aws sts get-caller-identity` | AWS's own answer: the account and role your credentials really belong to |
| opening port 22 to reach an instance | `aws ssm start-session --target ID` | no inbound port, key or public IP, and every session is logged |
| `terraform apply` straight away | `terraform plan -out=tfplan`, review, `terraform apply tfplan` | what was reviewed is exactly what runs; replacements show before they happen |
| `terraform force-unlock` at the first lock error | the lock's `Who` and `Created`, then the pipeline | unlocking a live apply lets two writers corrupt the state |
| `ansible-playbook site.yml` | `ansible-playbook site.yml --check --diff --limit target1` | every file change on one host before the fleet sees it |
| `aws s3 ls` for "the backup is gone" | `aws s3api list-object-versions --prefix KEY` | shows the delete marker and the older versions still stored |
| `git reset --hard` and `git push --force` on a pushed commit | `git revert --no-edit SHA` | an inverse commit keeps shared history intact and deploys like any change |
| `git rm` of a leaked secret | rotate it, then `git filter-repo --invert-paths --path FILE` | the old commits still hold it; only rotation makes it useless |

### aws sts — which account and identity will my next AWS call use?
Match: aws sts
Instead of: aws configure list, the console's account menu
Safety: read-only · `assume-role` prints temporary credentials; `--debug` output contains the signed request headers, session token included

**In one line:** `aws sts get-caller-identity` asks AWS which account, user or role the CLI's current credentials belong to, wherever they came from.

**Read the command:** `aws sts get-caller-identity --query Arn --output text`

| Part | Meaning |
|---|---|
| `sts get-caller-identity` | "who am I?"; needs no permission, so even a role denied everything can run it |
| `--query Arn` | keep only the ARN (a JMESPath filter) |
| `--output text` | plain text instead of JSON |
| `--profile prod-readonly` | ask as that profile from `~/.aws/config` |
| `--debug 2>&1 | grep -i credential` | the debug log names the credential source used |
| `assume-role --role-arn ARN --role-session-name learner-test` | temporary role credentials: an `ASIA…` key with an expiry |
| `decode-authorization-message --encoded-message "$MSG"` | decode an EC2 "Encoded authorization failure message" |

**What the output tells you:**

```
arn:aws:sts::111122223333:assumed-role/gitlab-deploy/ci
```

The 12 digits are the account. `assumed-role/ROLE/SESSION` means temporary role credentials (SSO, a CI job, an instance profile); `:user/NAME` means an IAM user's long-term keys.

**Why it is effective:** most AccessDenied and "not found" surprises are the wrong account, role or keys; one call settles that before you read any policy.

**Compared with `aws configure list`:** it reads local settings only: not which account the keys belong to, nor whether they still work.

**Trap:** it proves identity, not permission. An exported `AWS_ACCESS_KEY_ID` beats both `AWS_PROFILE` and the instance profile. `--debug` output carries signed headers: never paste it whole.

**Next step:** wrong identity → `env | grep ^AWS_`, `aws sso login --profile NAME`. `ExpiredToken` → log in again. Right identity, still denied → `aws iam simulate-principal-policy`.

### aws configure / aws sso — which profile, region and credential source is this shell using?
Match: aws configure, aws sso
Instead of: cat ~/.aws/credentials
Safety: read-only for `list` and `list-profiles` · changes state: `configure sso` writes a profile to `~/.aws/config`; `sso login` caches a session token under `~/.aws/sso/cache`

**In one line:** `aws configure list` shows the profile, keys and region the CLI will use and **where each one came from**; `aws sso login` renews an IAM Identity Center session.

**Read the command:** `aws configure list`

| Part | Meaning |
|---|---|
| `configure list` | the resolved settings, read locally; no call to AWS |
| `Type`, `Location` columns | the source (`env`, `shared-credentials-file`, `config-file`, `iam-role`…) and its file or variable |
| `configure list-profiles` | every profile name |
| `configure sso` | interactive setup of an Identity Center profile |
| `sso login --profile lab` | browser sign-in; the cached session then supplies short-lived role credentials |

**What the output tells you:**

```
      Name                    Value             Type    Location
      ----                    -----             ----    --------
   profile                <not set>             None    None
access_key     ****************QX7M         iam-role
secret_key     ****************9fKa         iam-role
    region                eu-west-1      config-file    ~/.aws/config
```

No profile and no keys in files or variables: the CLI fell through to the EC2 instance profile (`iam-role`). An `env` row would mean an exported variable, which beats every file.

**Why it is effective:** "works on my laptop, not in CI" is a credential-chain question, and the Type column answers it without printing secrets.

**Compared with `cat ~/.aws/credentials`:** it shows what is stored, not what wins, and prints the secret keys.

**Trap:** `list` never calls AWS, so expired or revoked keys look fine here: confirm with `aws sts get-caller-identity`. An expired SSO session fails with `Token has expired and refresh failed`. `--profile` affects one command, `AWS_PROFILE` the whole shell.

**Next step:** wrong source → `unset AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY AWS_SESSION_TOKEN`, `export AWS_PROFILE=NAME`, then `aws sts get-caller-identity`.

### aws ec2 — is the instance itself healthy, and what does its console say?
Match: aws ec2
Instead of: ssh, ping
Safety: read-only for `describe-*` and `get-console-output` · changes state: `reboot-instances`, `modify-*`, `authorize-`/`revoke-security-group-ingress`, `create-*`, `delete-*`; a stop and start moves the instance to new hardware

**In one line:** the `describe-*` calls show an instance as AWS sees it, and `get-console-output` returns its boot log, so you can diagnose a server that SSH can't reach.

**Read the command:** `aws ec2 describe-instance-status --instance-ids i-0a1b2c3d4e5f60011 --include-all-instances --query 'InstanceStatuses[].[InstanceId,InstanceState.Name,SystemStatus.Status,InstanceStatus.Status,Events[0].Code]' --output table`

| Part | Meaning |
|---|---|
| `describe-instance-status` | the two status checks and any scheduled event |
| `--instance-ids i-0a1b…` | this instance only |
| `--include-all-instances` | stopped and pending instances too; otherwise only running ones |
| `--query '…[…,SystemStatus.Status,InstanceStatus.Status,Events[0].Code]'` | ID, state, AWS-side check, OS-side check, first scheduled event |
| `--output table` | aligned columns |
| `get-console-output --instance-id ID --latest --query Output --output text` | the serial console log; `--latest` (Nitro) gets current output, not the copy buffered at the last start or stop |
| `describe-instances --instance-ids ID --query '…'` | IPs, key pair, subnet, security groups, instance profile |

**What the output tells you:**

```
|  i-0a1b2c3d4e5f60011  |  running  |  ok  |  impaired  |  None  |
[DEPEND] Dependency failed for data.mount - /data.
You are in emergency mode. After logging in, type "journalctl -xb" to view
```

System check `ok`: AWS's host and network are fine. Instance check `impaired`: your OS failed, and the console shows why: an fstab entry for a detached volume. An impaired system check is AWS's side; an event code such as `instance-retirement` announces maintenance.

**Why it is effective:** an SSH timeout looks the same whether the host failed, the OS hung at boot or a security group drops you; checks and console tell them apart without any network path.

**Compared with `ssh` and `ping`:** enough when they succeed; when they fail, they can't say whether the instance even runs.

**Trap:** an empty result can mean "stopped" (no `--include-all-instances`) or "another region". A reboot stays on the same host; a stop and start moves it, changes the public IP unless it is an Elastic IP, and wipes instance-store disks.

**Next step:** instance check impaired → the EC2 serial console, fix fstab (`nofail`). System check impaired → stop and start. Both `ok`, SSH times out → security groups, NACLs and routes, or `aws ssm start-session`.

### aws s3 / aws s3api — is the object there, which versions exist, and what guards the bucket?
Match: aws s3, aws s3api
Instead of: aws s3 ls alone, the S3 console
Safety: read-only for `ls`, `presign` and `s3api get-*`/`list-*` · changes state: `cp`, `sync`, `rm`, `s3api put-*`; `s3api delete-object --version-id` on a real version deletes it **permanently**

**In one line:** `aws s3` is the file-style layer (ls, cp, sync, rm, presign); `aws s3api` is one command per API call and shows what the file view hides: versions, delete markers, policies, encryption.

**Read the command:** `aws s3api list-object-versions --bucket lab-backups-123456789012 --prefix pg/daily.sql.gz --query '{versions:Versions[].[VersionId,IsLatest,LastModified,Size],markers:DeleteMarkers[].[VersionId,IsLatest]}'`

| Part | Meaning |
|---|---|
| `s3api list-object-versions` | every stored version and delete marker |
| `--bucket lab-backups-…` | the bucket, by name (no `s3://`) |
| `--prefix pg/daily.sql.gz` | keys **starting with** this (`daily.sql.gz.old` matches too) |
| `--query '{versions:…,markers:…}'` | versions (ID, latest?, date, bytes) and delete markers |
| `s3 ls s3://bucket/pg/`, `s3 cp`, `s3 sync` | current objects; copy files up or down |
| `s3 presign s3://…/daily.sql.gz --expires-in 600` | a download URL valid for 600 s |
| `s3api get-bucket-policy`, `get-bucket-encryption`, `get-bucket-ownership-controls` | the layers that allow or refuse access |

**What the output tells you:**

```
{
    "versions": [ [ "3HL4kqtJlcpXroDTDmJ.rmSpXd3dIbrHY", false, "2026-10-02T01:00:12+00:00", 52428800 ] ],
    "markers":  [ [ "UIORUnfnd89493jJFJ.qwe3h3JKLiuuX", true ] ]
}
```

The latest "version" is a delete marker, so `aws s3 ls` shows nothing, yet the 50 MB backup is still stored. Deleting the **marker** by its version ID brings it back.

**Why it is effective:** "the backup is gone" is usually a delete marker, and AccessDenied usually a bucket policy, an ownership setting or a KMS key; s3api shows each layer as stored.

**Compared with `aws s3 ls`:** enough to confirm an upload, but it hides versions, markers and every access layer.

**Trap:** before `delete-object --version-id`, copy the marker's ID and check `IsLatest: true`: on a real version it deletes for good. `get-bucket-versioning` printing nothing means versioning was never enabled. `sync` never deletes at the destination without `--delete`.

**Next step:** marker found → `s3api delete-object --version-id MARKER_ID`. AccessDenied → `aws sts get-caller-identity`, then policy, ownership and the KMS key's permissions. MinIO and other S3 servers → the `aws` card.

### aws ssm — can I reach this instance without SSH, and run a command on many?
Match: aws ssm
Instead of: ssh, opening port 22, ssh -L
Safety: read-only for `describe-*`, `list-*` and `get-parameter` · changes state: `start-session` opens a shell or tunnel; `send-command` runs commands **as root** on every target

**In one line:** Systems Manager reaches a server through its agent's outbound HTTPS connection: a shell, a port forward or a fleet-wide command, with no inbound port, key pair or public IP.

**Read the command:** `aws ssm start-session --target i-0a1b2c3d4e5f60011 --document-name AWS-StartPortForwardingSession --parameters 'portNumber=81,localPortNumber=8081'`

| Part | Meaning |
|---|---|
| `start-session --target i-0a1b…` | a session to this managed node (`mi-…` = an on-prem server) |
| `--document-name AWS-StartPortForwardingSession` | a tunnel instead of a shell |
| `--parameters 'portNumber=81,localPortNumber=8081'` | port 81 on the instance becomes `localhost:8081` here |
| `describe-instance-information --query '…[InstanceId,PingStatus,…]'` | the nodes SSM manages, and whether each is `Online` |
| `send-command --instance-ids ID --document-name AWS-RunShellScript --parameters 'commands=["df -h"]'` | Run Command: a script on the targets; returns a command ID |
| `list-command-invocations --command-id ID --details` | each target's status and output |

**What the output tells you:**

```
|  i-0a1b2c3d4e5f60011  |  Online  |  Ubuntu  |  24.04  |  3.3.2299.0  |
Starting session with SessionId: ops-0a1b2c3d4e5f60111
Port 8081 opened for sessionId ops-0a1b2c3d4e5f60111.
Waiting for connections...
```

`Online`: agent, identity and network path all work. While the session runs, `curl -sI http://localhost:8081/` reaches Apache on 81 with no security group rule.

**Why it is effective:** nothing listens on the instance, access follows IAM instead of copied keys, sessions are logged, and the same agent covers on-prem servers.

**Compared with `ssh`:** it needs port 22 open, a key on the server and a route: three more things to break or leak.

**Trap:** `start-session` needs the Session Manager plugin on **your** machine. `TargetNotConnected` means the agent, the instance profile (`AmazonSSMManagedInstanceCore`) or the path to the endpoints. Sessions run as `ssm-user`; Run Command runs as root, and its output through the API is truncated.

**Next step:** node missing → the agent via the serial console, the role, a route to the ssm and ssmmessages endpoints. Tunnel up, app silent → a shell session and `ss -ltnp`.

### aws cloudwatch — what did this metric do over time, and which alarms are firing?
Match: aws cloudwatch
Instead of: top inside the instance, a console graph
Safety: read-only for `get-*`, `list-*`, `describe-*` · changes state: `put-metric-alarm`; `set-alarm-state` fires the alarm's notifications and actions

**In one line:** `get-metric-statistics` returns one AWS metric as numbers over a time window: proof of what happened and when.

**Read the command:** `aws cloudwatch get-metric-statistics --namespace AWS/EC2 --metric-name CPUCreditBalance --dimensions Name=InstanceId,Value=i-0123456789abcdef0 --start-time 2026-10-03T00:00:00Z --end-time 2026-10-03T12:00:00Z --period 3600 --statistics Average --output text`

| Part | Meaning |
|---|---|
| `--namespace AWS/EC2` | the metric family (`AWS/ApplicationELB`, `AWS/NATGateway`, `CWAgent`…) |
| `--metric-name CPUCreditBalance` | CPU credits left on a burstable (T) instance |
| `--dimensions Name=InstanceId,Value=i-…` | which time series |
| `--start-time … --end-time …` | the window, in UTC |
| `--period 3600` | one datapoint per hour |
| `--statistics Average` | how a period's values combine (`Sum` for counts such as `HTTPCode_ELB_502_Count`) |
| `--output text` | one `DATAPOINTS` line per period |
| `describe-alarms --state-value ALARM` | what is firing now, each with its `StateReason` |

**What the output tells you:**

```
CPUCreditBalance
DATAPOINTS	288.0	2026-10-03T00:00:00+00:00	Count
DATAPOINTS	62.9	2026-10-03T07:00:00+00:00	Count
DATAPOINTS	0.0	2026-10-03T10:00:00+00:00	Count
```

The balance hit zero at 10:00; from then on the t3 instance (standard mode) is held to its baseline CPU, which the guest sees as high `%steal`.

**Why it is effective:** it shows the host-side facts the guest can't see (credits, burst balances, load-balancer 5xx, NAT port errors) as numbers you can paste into a ticket.

**Compared with `top` inside the instance:** top shows the symptom now, not its cause or its history.

**Trap:** datapoints come back **unsorted**: add `--query 'sort_by(Datapoints,&Timestamp)'`. A wrong dimension or region returns nothing, without an error. EC2 has no memory or disk metrics without the CloudWatch agent. One call returns at most 1,440 datapoints; one-minute points are kept 15 days.

**Next step:** credits at zero → unlimited mode or a non-burstable type. ELB versus target 5xx → the `aws elbv2` card. Alarm firing → its `StateReason`, then the metric for the hours before.

### aws logs — what did the application log, without logging in to its servers?
Match: aws logs
Instead of: ssh and tail -f on each server
Safety: read-only for `tail`, `filter-log-events` and `describe-*` · Logs Insights queries are billed per GB scanned · changes state: `put-*` and `delete-*`

**In one line:** CloudWatch Logs keeps events in log groups (one per app or source), split into streams (one per instance or container); `aws logs tail` follows or searches a whole group.

**Read the command:** `aws logs tail /aws/lambda/myfn --since 1h --filter-pattern ERROR`

| Part | Meaning |
|---|---|
| `logs tail /aws/lambda/myfn` | events from every stream of this group (AWS CLI v2 only) |
| `--since 1h` | start one hour back (default 10 minutes) |
| `--filter-pattern ERROR` | only events containing `ERROR`; patterns are case-sensitive |
| `--follow` | keep printing new events, like `tail -f` |
| `filter-log-events --log-group-name G --start-time MS --filter-pattern P` | the same search as an API call; times in **milliseconds** |
| `start-query --query-string 'fields @timestamp,@message | filter …'` | a Logs Insights query; read it with `get-query-results` |
| `describe-log-groups --query 'logGroups[?!retentionInDays].logGroupName'` | groups that never expire |

**What the output tells you:**

```
2026-10-03T08:52:10.114000+00:00 2026/10/03/[$LATEST]4f1c2a9e0b7d ERROR connect ECONNREFUSED 10.20.5.10:5432
```

Timestamp, stream, then the message as the app wrote it: the function can't reach PostgreSQL on 10.20.5.10.

**Why it is effective:** one command searches every replica's stream from anywhere, including servers and containers that no longer exist.

**Compared with `ssh` and `tail -f`:** enough for one server's file, but it misses the other replicas and replaced instances.

**Trap:** a quiet group can mean the agent stopped shipping, not that the app is fine: check the newest event's time. Groups default to **never expire** and ingestion is billed per GB, so a chatty group leaks money. `ERROR` does not match `error`.

**Next step:** errors around a time → the same window in `aws cloudwatch` and `aws cloudtrail`. Nothing arriving → the CloudWatch agent's status and role. No retention → set it per group.

### aws elbv2 — are the load balancer's targets healthy, and if not, why?
Match: aws elbv2
Instead of: curl through the load balancer
Safety: read-only for `describe-*` · changes state: `modify-target-group`, `register-targets`/`deregister-targets` and listener changes act on live traffic at once

**In one line:** `describe-target-health` lists every target of an ALB or NLB target group with its state and a **reason code** naming the failing layer.

**Read the command:** `aws elbv2 describe-target-health --target-group-arn TG_ARN --query 'TargetHealthDescriptions[].[Target.Id,Target.Port,TargetHealth.State,TargetHealth.Reason,TargetHealth.Description]' --output table`

| Part | Meaning |
|---|---|
| `describe-target-health` | each registered target, as the load balancer's own health checks see it |
| `--target-group-arn TG_ARN` | the target group (ARN from `describe-target-groups`) |
| `--query '[…Id,Port,State,Reason,Description]'` | target, port, state, reason code, and a description with the HTTP code |
| `--output table` | aligned columns |
| `describe-target-groups --load-balancer-arn LB_ARN --query '…[HealthCheckPath,Matcher.HttpCode]'` | what the check requests, and which codes count as healthy |
| `describe-load-balancer-attributes --load-balancer-arn LB_ARN` | settings such as `idle_timeout.timeout_seconds` (60 by default) |

**What the output tells you:**

```
|  i-0a1b2c3d4e5f60011  |  81  |  unhealthy  |  Target.ResponseCodeMismatch  |  Health checks failed with these codes: [301]  |
```

The target answers with a 301: an HTTP-to-HTTPS redirect on the health path. `Target.Timeout` would mean no answer (often a security group); `Target.FailedHealthChecks`, a failed connection, such as an app bound to 127.0.0.1.

**Why it is effective:** from outside, a 502, a 503 and a slow page look alike; the reason code says which target fails at which layer, before you open a shell.

**Compared with `curl` through the load balancer:** curl shows what users get, and `server: awselb/2.0` proves the load balancer made the error, but not which target fails or why.

**Trap:** when **every** target is unhealthy the ALB fails open and sends traffic to all of them, so "the site works" can hide a broken check. An ALB 503 means no registered target to send to. `healthy` only proves the health path answers.

**Next step:** `ResponseCodeMismatch` → curl the health path inside the VPC with the same Host header. `Timeout` → allow the ALB's security group to the target port. Sporadic 502s → app keep-alive longer than the idle timeout.

### aws cloudtrail — who changed this, and when?
Match: aws cloudtrail
Instead of: asking in the team chat
Safety: read-only · lookups are throttled at about two requests per second per account and region

**In one line:** CloudTrail records AWS API calls (who, what, when, from where, and whether they failed); `lookup-events` searches one region's free 90-day event history.

**Read the command:** `aws cloudtrail lookup-events --lookup-attributes AttributeKey=ResourceName,AttributeValue=sg-0a1b2c3d4e5f60072 --max-results 3 --query 'Events[].[EventTime,EventName,Username]' --output text`

| Part | Meaning |
|---|---|
| `lookup-events` | search this region's management events of the last 90 days |
| `--lookup-attributes AttributeKey=ResourceName,AttributeValue=sg-…` | events that touched this resource; other keys include `EventName`, `Username`, `AccessKeyId` |
| `--max-results 3` | the three newest matches |
| `--query 'Events[].[EventTime,EventName,Username]'` | when, which API call, which identity or role session |
| `--output text` | tab-separated lines |
| `describe-trails`, `get-trail-status --name org-trail` | which trails exist; whether they cover every region and still log |

**What the output tells you:**

```
2026-10-03T08:41:48+00:00	RevokeSecurityGroupIngress	ops-oncall
2026-09-28T16:02:10+00:00	AuthorizeSecurityGroupIngress	gitlab-deploy-4302
2026-09-12T11:20:31+00:00	CreateSecurityGroup	gitlab-deploy-4105
```

Someone on call removed a rule this morning, after two pipeline-made changes. Each event's full JSON (`CloudTrailEvent`) adds the source IP, the parameters and an `errorCode` for denied calls.

**Why it is effective:** "what changed?" is the most productive incident question, and this answers it with evidence: the exact call, the identity and the second.

**Compared with asking the team:** people remember the change they meant to make, not what their pipeline or console click actually did.

**Trap:** event history holds only **management** events: S3 object reads and other data events appear only in a trail configured for them. Each region keeps its own history; IAM and other global services log in us-east-1. One lookup attribute per call. New events take several minutes to appear.

**Next step:** an unwanted change → revert it in code (`terraform plan` shows the drift). A key used from an unknown IP → `AttributeKey=AccessKeyId` in every region, then rotate the key.

### aws ce — where is the money going?
Match: aws ce
Instead of: the monthly invoice
Safety: read-only · every Cost Explorer API request is billed (USD 0.01)

**In one line:** `get-cost-and-usage` returns your costs for a period, grouped by service, region, usage type or tag, so a surprise bill becomes a ranked list of meters.

**Read the command:** `aws ce get-cost-and-usage --time-period Start=2026-09-01,End=2026-10-01 --granularity MONTHLY --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE --query 'ResultsByTime[0].Groups[].[Keys[0],Metrics.UnblendedCost.Amount]' --output text`

| Part | Meaning |
|---|---|
| `--time-period Start=2026-09-01,End=2026-10-01` | September; the end date is **exclusive** |
| `--granularity MONTHLY` | one total per month (`DAILY` finds the day it started) |
| `--metrics UnblendedCost` | charges as billed (amortized cost spreads upfront commitments) |
| `--group-by Type=DIMENSION,Key=SERVICE` | one line per service; also `Key=REGION`, `Key=USAGE_TYPE`, `Type=TAG,Key=Project` |
| `--query 'ResultsByTime[0].Groups[].[Keys[0],…Amount]'`, `--output text` | name and amount of each group, one per line |
| `--filter '{"Dimensions":{"Key":"REGION","Values":["us-east-1"]}}'` | one region's costs only |

**What the output tells you:**

```
Amazon Elastic Compute Cloud - Compute	41.82
EC2 - Other	38.15
Amazon Virtual Private Cloud	14.60
```

"EC2 - Other" holds NAT gateways, EBS volumes, snapshots and data transfer: regroup by `USAGE_TYPE` to see which. Public IPv4 addresses are billed under "Amazon Virtual Private Cloud".

**Why it is effective:** usage types name the meter (`NatGateway-Bytes`, `PublicIPv4:IdleAddress`, `EBS:SnapshotUsage`), which points at the resource to delete or redesign.

**Compared with the invoice:** the same totals, but it can't be regrouped, so it never says which region or project is responsible.

**Trap:** a tag key groups costs only after it is activated as a cost allocation tag; an empty `Project$` group is untagged spend. The newest costs lag by up to a day. Each call costs a cent: keep it out of loops. Amounts arrive unsorted: `sort -t$'\t' -k2 -rn`.

**Next step:** NAT bytes → a gateway endpoint for S3. Idle addresses, detached volumes, old snapshots → `aws ec2 describe-addresses`, `describe-volumes`, `describe-snapshots`. Then a budget alert.

### aws iam — would this role be allowed, and who may become it?
Match: aws iam
Instead of: reading policy JSON by eye, attaching AdministratorAccess
Safety: read-only for `get-*`, `list-*`, `simulate-*` and the credential report · changes state: `put-role-policy`, `update-access-key`, `create-*`, `attach-*`

**In one line:** `simulate-principal-policy` runs IAM's policy evaluation for one principal, action and resource, and returns allowed, implicitDeny or explicitDeny without making the real call.

**Read the command:** `aws iam simulate-principal-policy --policy-source-arn arn:aws:iam::123456789012:role/app-ec2-role --action-names s3:GetObject s3:PutObject s3:DeleteObject --resource-arns arn:aws:s3:::lab-artifacts-123456789012/build.tar.gz --query 'EvaluationResults[].[EvalActionName,EvalDecision]' --output table`

| Part | Meaning |
|---|---|
| `--policy-source-arn …:role/app-ec2-role` | the user or role whose policies are evaluated |
| `--action-names s3:GetObject s3:PutObject s3:DeleteObject` | the actions, as named in the error or in CloudTrail |
| `--resource-arns arn:aws:s3:::bucket/build.tar.gz` | the exact resource: object actions need `bucket/key`, bucket actions the bucket ARN |
| `--query '…[EvalActionName,EvalDecision]'`, `--output table` | action and verdict; without the query you also get `MatchedStatements` |
| `get-role --role-name R --query 'Role.AssumeRolePolicyDocument'` | the trust policy: who may assume the role |
| `get-access-key-last-used --access-key-id AKIAIOSFODNN7EXAMPLE` | when, where and for which service a key was last used |

**What the output tells you:**

```
|  s3:GetObject     |  allowed       |
|  s3:PutObject     |  implicitDeny  |
|  s3:DeleteObject  |  explicitDeny  |
```

`allowed`: a statement allows it. `implicitDeny`: nothing allows it, so add a scoped Allow. `explicitDeny`: a Deny matched, and no Allow can outvote it; that Deny must change.

**Why it is effective:** it separates "add a permission" from "remove a Deny" in seconds, and tests a fix before it reaches CI.

**Compared with reading policies:** the JSON shows each statement, not how wildcards, conditions and several policies combine; guessing is how roles end up with AdministratorAccess.

**Trap:** a bucket or key policy counts only when passed with `--resource-policy`, and conditions such as `aws:SourceIp` only with `--context-entries`, so confirm a surprising verdict with the real call and CloudTrail. IAM changes take a few seconds to apply.

**Next step:** implicitDeny → a least-privilege Allow with the right ARN shape, in Terraform. explicitDeny → the policy type the error names (SCP, boundary, resource policy). Allowed, yet the call fails → bucket and KMS key policies.

### aws rds — what happened to the database instance, and what can I restore?
Match: aws rds
Instead of: connecting with psql to guess
Safety: read-only for `describe-*` · changes state: `reboot-db-instance --force-failover`; `restore-db-instance-to-point-in-time` creates a new, billed instance

**In one line:** RDS records an event for every failover, reboot, backup and maintenance action; `describe-events` lists them, and `describe-db-instances` shows status, endpoint and backup settings.

**Read the command:** `aws rds describe-events --source-identifier lab-db --source-type db-instance --duration 120 --query 'Events[].[Date,Message]' --output text`

| Part | Meaning |
|---|---|
| `describe-events` | the RDS event log, which keeps the last 14 days |
| `--source-identifier lab-db` | one DB instance |
| `--source-type db-instance` | what the identifier names (snapshots and parameter groups have their own types) |
| `--duration 120` | the last 120 **minutes** (default: one hour) |
| `--query 'Events[].[Date,Message]'`, `--output text` | timestamp and message, one per line |
| `describe-db-instances --db-instance-identifier lab-db --query '…'` | status, Multi-AZ, endpoint, `LatestRestorableTime`, `DeletionProtection` |

**What the output tells you:**

```
2026-10-03T04:10:02.511000+00:00	Multi-AZ instance failover started.
2026-10-03T04:10:38.902000+00:00	DB instance restarted
2026-10-03T04:11:20.117000+00:00	Multi-AZ instance failover completed
```

A failover took about 80 seconds. The endpoint name stays the same, but its DNS now points at the former standby, so every client had to reconnect.

**Why it is effective:** a database blip has many possible causes; the event log names the one AWS performed, with timestamps to line up against the application's errors.

**Compared with `psql`:** a connection test proves the database answers now, not what happened ten minutes ago.

**Trap:** an app still failing after "failover completed" has a client problem (cached DNS, a stale pool). A restore **never** happens in place: it creates a new instance with a new endpoint, and default network settings unless you pass subnet group and security groups. Deleting an instance deletes its automated backups unless you keep them.

**Next step:** failover → the app's DNS caching and reconnects. Queued reboots → `describe-pending-maintenance-actions`. Bad data → restore to a new instance, compare, copy back only what is missing.

### aws eks — connect kubectl to an EKS cluster, and see why access fails
Match: aws eks
Instead of: copying a kubeconfig from a colleague
Safety: changes state: `update-kubeconfig` edits `~/.kube/config` and switches the current context · read-only for `describe-*` and `list-*` · `create-access-entry` and `associate-access-policy` grant cluster access

**In one line:** `update-kubeconfig` writes a kubeconfig entry that runs `aws eks get-token` on every kubectl call, so kubectl authenticates as the AWS identity the CLI resolves at that moment (or the role given with `--role-arn`).

**Read the command:** `aws eks update-kubeconfig --name lab --region ap-south-1`

| Part | Meaning |
|---|---|
| `update-kubeconfig` | add or refresh cluster, user and context, and make it current |
| `--name lab` | the cluster |
| `--region ap-south-1` | the cluster's region, also written into the token command |
| `--role-arn arn:…:role/eks-admin` | get tokens by assuming this role |
| `describe-cluster --name lab --query 'cluster.[version,status,platformVersion,accessConfig.authenticationMode]'` | version, `ACTIVE`, and whether access entries, the aws-auth ConfigMap or both apply |
| `list-access-entries --cluster-name lab`, `list-addons --cluster-name lab` | the IAM principals allowed in; the managed add-ons |
| `describe-nodegroup --cluster-name prod --nodegroup-name workers --query 'nodegroup.health.issues'` | why nodes fail to join |

**What the output tells you:**

```
1.34	ACTIVE	eks.7	API_AND_CONFIG_MAP
ACCESSENTRIES	arn:aws:iam::123456789012:role/AWSReservedSSO_AdministratorAccess_0a1b2c3d4e5f6a7b
ACCESSENTRIES	arn:aws:iam::123456789012:role/lab-node-role
ADDONS	coredns
ADDONS	vpc-cni
```

Only the SSO admin role and the node role may log in, and no `aws-ebs-csi-driver` add-on is installed: gp3 PVCs will stay Pending.

**Why it is effective:** on EKS a Kubernetes symptom often has an AWS cause (identity, a missing add-on, subnet IPs); these calls show the AWS side next to kubectl's.

**Compared with copying a kubeconfig:** the copy has the right endpoint and CA, but its exec section names someone else's profile or role.

**Trap:** `error: You must be logged in to the server (Unauthorized)` is not a kubeconfig fault: your current AWS identity has no access entry. `update-kubeconfig` switches the current context, so the next kubectl command hits this cluster.

**Next step:** Unauthorized → `aws sts get-caller-identity`, then an access entry for that role. PVC Pending → `list-addons`. Nodes not joining → the node group's health issues, subnet routes and endpoints.

### aws — global options, S3-compatible endpoints and the services without their own card
Match: aws
Instead of: —
Safety: depends on the operation: `describe-*`, `list-*`, `get-*` only read; `create-*`, `put-*`, `update-*`, `delete-*` and `s3 rm` change state

**In one line:** every call is `aws [global options] SERVICE OPERATION [parameters]`; the global options choose endpoint, region, profile and output format, whatever the service.

**Read the command:** `aws --endpoint-url https://minio.example.com:9000 --region us-east-1 s3 ls s3://dokploy-backups/shop-db/`

| Part | Meaning |
|---|---|
| `--endpoint-url https://minio.example.com:9000` | send the call to this S3-compatible server (MinIO, Ceph RGW) instead of AWS: MinIO's API port, not its console port |
| `--region us-east-1` | the region the request is signed for (MinIO's default); on AWS it also picks the endpoint |
| `s3 ls s3://dokploy-backups/shop-db/` | service and operation: the objects under this prefix |
| `--profile shop-app` | credentials and defaults from that profile |
| `--query '…'`, `--output text|table|json` | a JMESPath filter the CLI applies; the output format |
| `--debug`, `--version` | every step of the call; the CLI version (`logs tail` and others exist only in v2) |
| `route53`, `ecr`, `ecs`, `autoscaling`, `guardduty`, `organizations`, `budgets`, `kms`… | the other services the handbook uses: same pattern, same options |

**What the output tells you:**

```
2026-10-02 02:00:14   48211934 shop-db-2026-10-02T02-00-00.sql.gz
2026-10-03 02:00:12   48390211 shop-db-2026-10-03T02-00-00.sql.gz
```

Endpoint, region and credentials work from this host, and last night's backup exists. `RequestTimeTooSkewed` would point at the clock, `SignatureDoesNotMatch` at the key or region, an `x509` error at an untrusted private CA.

**Why it is effective:** one CLI and one set of options reach AWS and on-prem S3 storage alike; only the service and operation change from task to task.

**Trap:** `--query` filters **after** the whole response is downloaded; to narrow a large search on the server, use the operation's `--filters` or `--prefix`. `--output text` flattens nested lists, so columns shift when a field is missing. Without `--region`, `AWS_REGION` or the profile decides: "not found" often means "another region".

**Next step:** identity doubts → `aws sts get-caller-identity`. A service with its own card → that card. ECR login → `aws ecr get-login-password --region R | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.R.amazonaws.com` (the token lasts 12 hours).

### terraform plan — what exactly will change, and is anything replaced or destroyed?
Match: terraform plan
Instead of: terraform apply straight away
Safety: read-only for infrastructure · takes the state lock and calls the provider APIs to refresh · the `-out` file holds sensitive values in clear text

**In one line:** `terraform plan` compares your code, the state and the real infrastructure (refreshed through the provider APIs) and prints every change needed, resource by resource, without making any.

**Read the command:** `terraform plan -out=tfplan`

| Part | Meaning |
|---|---|
| `plan` | compute the diff; nothing is created, changed or destroyed |
| `-out=tfplan` | save this exact plan, so `terraform apply tfplan` runs what you reviewed |
| `-refresh-only` | show only what changed outside Terraform (drift), proposing no fix |
| `-target=ADDRESS` | plan one resource and its dependencies only: for emergencies |
| `-detailed-exitcode` | exit 0 = no changes, 2 = changes, 1 = error: the basis of drift jobs |
| `-lock-timeout=60s`, `-input=false` | wait up to 60 s for the state lock; never prompt (CI) |

**What the output tells you:**

```
  # proxmox_virtual_environment_vm.target["target4"] will be created
  + resource "proxmox_virtual_environment_vm" "target" {
  # aws_security_group.web must be replaced
-/+ resource "aws_security_group" "web" {
      ~ name = "web-sg" -> "web-sg-v2" # forces replacement
Plan: 2 to add, 0 to change, 1 to destroy.
```

`+` create, `~` update in place, `-` destroy, `-/+` destroy then recreate (`+/-` with `create_before_destroy`), `<=` read a data source. `# forces replacement` marks the attribute that can't change in place: the renamed group is deleted and recreated with a new ID (one add plus one destroy in the summary).

**Why it is effective:** every change is listed before it happens, with the attribute that causes it, and the saved file guarantees that the plan you reviewed is the one applied.

**Compared with `terraform apply`:** apply also shows a plan and waits for `yes`, but computes it anew; in CI, or after a colleague's apply, it can differ from what the merge request reviewed.

**Trap:** read the destroy count first: "87 to add" on an existing environment means an empty or wrong state (backend, workspace). `-target` hides the rest of the plan and leaves it unreconciled. Under `set -e`, exit code 2 from `-detailed-exitcode` aborts the script.

**Next step:** unexpected `-/+` → the `# forces replacement` line; a rename → a `moved` block. Changes nobody made → `-refresh-only`, then `aws cloudtrail`. Lock error → the force-unlock card.

### terraform apply — make the reviewed changes, and only those
Match: terraform apply
Instead of: clicking in the AWS or Proxmox console
Safety: changes state: creates, changes and destroys real infrastructure and writes the state · `-refresh-only` writes only the state

**In one line:** `terraform apply` carries out a plan through the provider APIs and records each result in the state; given a saved plan file, it applies exactly that file.

**Read the command:** `terraform apply tfplan`

| Part | Meaning |
|---|---|
| `apply tfplan` | apply the saved plan **without asking again**: the review happened at plan time |
| `apply` with no file | plan now, show it, wait for `yes` |
| `-refresh-only` | accept the drift a `plan -refresh-only` showed: update the state, change nothing real |
| `-parallelism=1` | one operation at a time (default 10): avoids lock collisions on Proxmox |
| `TF_LOG=DEBUG … 2> tf-debug.log` | provider and API debug log, from stderr into a file |

**What the output tells you:**

```
aws_security_group.web: Destroying... [id=sg-0c3c3c3c3c3c3c3c3]
aws_security_group.web: Destruction complete after 2s
aws_security_group.web: Creation complete after 3s [id=sg-0d4d4d4d4d4d4d4d4]
proxmox_virtual_environment_vm.target["target4"]: Creation complete after 41s [id=154]
Apply complete! Resources: 2 added, 0 changed, 1 destroyed.
```

Each line names the address and the real ID it got. Errors are the provider's API errors: read which call failed and why. After a failure the state keeps what succeeded, so plan again before retrying.

**Why it is effective:** the change happens exactly as reviewed, and the state records the result, so the next plan starts from the truth.

**Compared with the console:** faster for one change, but nothing records it in code or state, and the next apply undoes it as drift.

**Trap:** a saved plan applies with **no confirmation prompt**. If someone applied in between, it fails with `Saved plan is stale`: plan again. One Ctrl-C lets running calls finish; a second kills Terraform, which can leave a stale lock and a half-done change. A `-refresh-only` apply blesses drift: read its plan first.

**Next step:** error mid-apply → fix the cause, plan, apply the new plan. Lock left behind → the force-unlock card. Proxmox `can't lock file` errors → `-parallelism=1`.

### terraform init — which backend, providers and modules does this directory use?
Match: terraform init
Instead of: copying a .terraform directory from another machine
Safety: changes local files: `.terraform/` and `.terraform.lock.hcl` · `-migrate-state` copies state into the new backend · `-reconfigure` switches backends without moving any state

**In one line:** `terraform init` connects the working directory to its state backend, downloads the providers and modules the code needs, and records provider versions and checksums in the lock file.

**Read the command:** `terraform init -reconfigure -backend-config=backend/prod.hcl`

| Part | Meaning |
|---|---|
| `init` | prepare this directory; safe to run again |
| `-backend-config=backend/prod.hcl` | fill the empty `backend "s3" {}` block from this file: bucket, key, region |
| `-reconfigure` | use this backend and forget the one saved in `.terraform`; **copies nothing** |
| `-migrate-state` | instead: copy the existing state to the new backend (asks first) |
| `-upgrade` | newest provider and module versions the constraints allow; rewrites the lock file |
| `-backend-config="address=$TF_ADDRESS"` (repeated) | the key=value form, as for GitLab-managed state |

**What the output tells you:**

```
│ Error: Backend configuration changed
│ If you wish to attempt automatic migration of the state, use "terraform init -migrate-state".
│ If you wish to store the current configuration with no changes to the state, use "terraform init -reconfigure".
```

This directory was last initialised for another backend (another environment, or a cached `.terraform`). To work on prod's existing state, `-reconfigure`; to **move** state somewhere new, `-migrate-state`.

**Why it is effective:** the backend decides which state you edit and the lock file which provider code runs against your APIs; init makes both explicit and repeatable.

**Compared with copying `.terraform`:** the copy brings another machine's backend choice and platform-specific provider binaries.

**Trap:** `-reconfigure` against an empty or wrong key gives an empty state, and the next plan wants to create everything. A lock file with hashes for one platform fails on another until `terraform providers lock -platform=…` adds them. `-upgrade` takes a new major version if the constraint allows it (`>= 5.0` does).

**Next step:** after any backend change, read the first plan line by line. Provider not found (`hashicorp/proxmox`) → each module's `required_providers`. Checksum mismatch → `providers lock`, then commit the lock file.

### terraform state — which objects does Terraform manage, and what does it believe about one?
Match: terraform state
Instead of: opening terraform.tfstate in an editor
Safety: read-only for `list` and `show` · `pull` prints the whole state, **secrets included** · changes state: `mv`, `rm` and `push` rewrite shared state with no plan to review

**In one line:** the state maps every resource address in your code to a real object ID and its last-known attributes; `terraform state` lists, shows and (carefully) edits that mapping.

**Read the command:** `terraform state show 'proxmox_virtual_environment_vm.target["target3"]'`

| Part | Meaning |
|---|---|
| `state show` | one resource's attributes as Terraform last recorded them |
| `'…target["target3"]'` | the address: type, name, `for_each` key; single quotes protect brackets and double quotes from the shell |
| `state list` | every managed address |
| `state pull` | the raw state JSON, to stdout |
| `state mv OLD NEW` | rename an address in state (a `moved {}` block does it through a plan) |
| `state rm ADDRESS` | stop managing an object; it is **not** destroyed |

**What the output tells you:**

```
# proxmox_virtual_environment_vm.target["target3"]:
resource "proxmox_virtual_environment_vm" "target" {
    id            = "153"
    name          = "target3"
    node_name     = "pve1"
```

The address is bound to Proxmox VM 153 on pve1. Rename the resource block without a `moved` block and the next plan destroys VM 153 and creates another.

**Why it is effective:** unexpected destroys and creates are mapping problems far more often than cloud problems; list and show reveal which address points at which real object.

**Compared with editing `terraform.tfstate`:** the same data, but remote state is locked and versioned, and a hand edit with a wrong serial or lineage breaks it.

**Trap:** `show` prints recorded values, not live ones: a plan refreshes them. `state pull` output holds passwords and keys in clear text: never redirect it into the repository. `mv` and `rm` act at once on shared state; prefer `moved {}` and `removed {}` blocks.

**Next step:** address missing → an `import {}` block. Wrong address after a refactor → `moved {}`, then a plan with "0 to destroy". Secrets in state → restrict and encrypt the state bucket.

### terraform force-unlock / import — clear a dead lock, adopt an existing object
Match: terraform force-unlock, terraform import
Instead of: -lock=false, deleting and recreating the resource
Safety: changes state: `force-unlock` deletes the lock record only, never the state or the infrastructure; `import` writes a new entry into the state

**In one line:** two repairs outside the plan and apply cycle: `force-unlock` removes a lock left by a killed run, and `import` binds an existing real object to a resource address.

**Read the command:** `terraform force-unlock 6f1c2a9e-4b7d-4e1b-9a30-2d8c5f7e1a42`

| Part | Meaning |
|---|---|
| `force-unlock` | delete the lock of this configuration's backend; asks for confirmation |
| `6f1c2a9e-…` | the lock ID, from `ID:` under `Lock Info` in the error |
| `-force` | skip the confirmation |
| `import ADDRESS ID` | the older CLI form: writes the object into state at once, unreviewed |
| `import {}` block (`to`, `id`) plus `terraform plan` | the reviewed form (Terraform 1.5+, OpenTofu 1.6+): the plan says "N to import" |

**What the output tells you:**

```
│ Lock Info:
│   ID:        6f1c2a9e-4b7d-4e1b-9a30-2d8c5f7e1a42
│   Operation: OperationTypeApply
│   Who:       runner@gitlab-runner-02
│   Created:   2026-10-03 06:12:44.123456789 +0000 UTC
```

`Who` is user@host of the process holding the lock, `Operation` what it was doing. If that CI job still runs, wait; if it was cancelled or its runner died, the lock is stale.

**Why it is effective:** a stale lock blocks every plan and apply on that state, and force-unlock clears exactly that record. Import adopts hand-made resources instead of duplicating them.

**Compared with `-lock=false`:** it skips locking for one run and lets two writers update the same state, which is how state gets corrupted.

**Trap:** unlocking while the holder still runs creates two writers anyway: check the pipeline first, then `terraform plan` to see what the interrupted apply left half-done. The `import` command writes no code; an import block plus `-generate-config-out` drafts it. An object imported into two states is undone by each apply.

**Next step:** lock cleared → plan, reconcile, apply; add `resource_group` and `-lock-timeout` in CI. Import planned → trim the generated code until the plan says "1 to import, 0 to add, 0 to change, 0 to destroy".

### terraform — format, validate, inspect and query the configuration
Match: terraform
Instead of: —
Safety: read-only, except `fmt` without `-check` (rewrites files) and `providers lock` (rewrites the lock file) · `show -json` and `output -json` print sensitive values in clear text

**In one line:** the subcommands around plan and apply: check style and syntax, list providers, read a saved plan as JSON, query outputs and expressions, confirm version and workspace.

**Read the command:** `terraform show -json tfplan | jq -r '.resource_changes[] | select(.change.actions != ["no-op"]) | "\(.change.actions | join(",")) \(.address)"'`

| Part | Meaning |
|---|---|
| `show -json tfplan` | the saved plan as machine-readable JSON |
| `jq -r '.resource_changes[] | select(… != ["no-op"])'` | every resource that will change… |
| `"\(.change.actions | join(",")) \(.address)"` | …printed as `ACTIONS ADDRESS` |
| `fmt -check -recursive`, `validate` | style check (non-zero exit if a file needs formatting); syntax and internal consistency |
| `providers`, `providers lock -platform=linux_amd64 …` | which module needs which provider; checksums for each platform |
| `output -json ansible_inventory`, `console <<< 'var.targets'` | an output as JSON for another tool; evaluate an expression |
| `version`, `workspace show` | the binary in use; the current workspace |

**What the output tells you:**

```
delete aws_instance.web[0]
delete aws_instance.web[1]
create module.web.aws_instance.this["a"]
create module.web.aws_instance.this["b"]
```

Deletes paired with creates of the same type are a refactor, not a real change: add `moved` blocks. A replacement prints as `delete,create` (or `create,delete`).

**Why it is effective:** the JSON reduces a long plan to one line per change, which a pipeline can grep for deletes and fail on; `fmt` and `validate` catch mistakes before any API call.

**Trap:** `validate` needs `init` first, and checks neither credentials nor remote state. `workspace show` saying `default` where you expected `prod`, or the reverse, is how plans hit the wrong environment. Keep plan files and their JSON private and short-lived.

**Next step:** deletes you can't explain → `moved` blocks, then plan again. Lock-file platform errors → `providers lock`. Inventory for Ansible → `terraform output -json NAME`.

### ansible-playbook — dry-run a change on one host before the fleet
Match: ansible-playbook, ansible-lint
Instead of: running the playbook against every host at once
Safety: changes state: configures every matched host (packages, files, services, restarts through handlers) · `--check` predicts without changing; `--list-hosts` and `--list-tasks` only list

**In one line:** `ansible-playbook` runs plays (hosts plus ordered tasks) over SSH; with `--check --diff --limit --tags` it shows, for one host and one part of the playbook, each change it would make.

**Read the command:** `ansible-playbook site.yml --check --diff --limit target1 --tags config`

| Part | Meaning |
|---|---|
| `site.yml` | the playbook |
| `--check` | dry run: modules report what they **would** change |
| `--diff` | before and after of files and templates |
| `--limit target1` | only this host or pattern (`'docker_hosts:!target1'` = all the others) |
| `--tags config` | only tasks tagged `config` (plus those tagged `always`) |
| `--list-hosts`, `--list-tasks` | who and what a run would touch; runs nothing |
| `-i inventories/prod`, `--vault-id prod@prompt`, `-K` | the inventory; the vault password source; ask for the sudo password |

**What the output tells you:**

```
TASK [Write daemon.json (validated before it replaces the old one)] ****
-  "dns": ["8.8.8.8"],
+  "dns": ["192.0.2.53", "192.0.2.54"],
changed: [target1]
RUNNING HANDLER [Restart docker] ***********************************
changed: [target1]
target1   : ok=5    changed=2    unreachable=0    failed=0    skipped=0
```

Someone set 8.8.8.8 by hand (drift); the run would restore the internal resolvers **and restart Docker**. In check mode `changed` means "would change". `unreachable`: never got in over SSH; `failed`: got in, and a task failed.

**Why it is effective:** "correct change, wrong scope" is the worst automation incident; this shows the exact lines that change on one canary host before anything runs anywhere.

**Compared with a plain run:** the same task results, but only after the changes and restarts have happened on every targeted host.

**Trap:** `command` and `shell` tasks are **skipped** in check mode, so tasks depending on them may fail or under-report: check mode is a prediction. A second real run should report `changed=0`. A `--limit` matching no host stops with an error; without `--limit`, the play's `hosts:` decides.

**Next step:** diff as expected → a real run on the canary, then `--limit 'docker_hosts:!target1'`, with `serial` in the play. Surprising value → `ansible-inventory --host`. UNREACHABLE → `ansible HOST -m ansible.builtin.ping -vvvv`. Related: `ansible-lint site.yml` reads the playbook and its roles without running anything and names each rule broken, with file and line (`no-changed-when`: a `command` or `shell` task with no `changed_when`, the classic cause of `changed` on every run); it exits non-zero, so it can fail a CI job.

### ansible — ask one question of many hosts at once
Match: ansible
Instead of: a for loop of ssh commands
Safety: read-only for `ping`, `setup`, `debug` and read-only commands · changes state with modules such as `apt` (`state=latest` upgrades packages) · `-b` runs as root on **every** matched host

**In one line:** an ad-hoc command runs one module against a host pattern from the inventory, in parallel, and prints each host's result.

**Read the command:** `ansible all -b -m ansible.builtin.shell -a 'ss -ltnp | grep -E ":(80|443|81|444) " || true'`

| Part | Meaning |
|---|---|
| `all` | the host pattern: every inventory host (or a group, a host, `docker_hosts:!target2`) |
| `-b` | become root through sudo (`ss -p` needs it to name processes) |
| `-m ansible.builtin.shell` | run through a shell, so the pipe and `||` work (`command` has no shell) |
| `-a '… || true'` | the module's argument; `|| true` stops "no match" (grep exit 1) failing the host |
| `-m ansible.builtin.ping`, `-m ansible.builtin.debug -a 'var=NAME'` | log in and run Python (**not** ICMP); a variable's value as that host sees it |

**What the output tells you:**

```
web01 | CHANGED | rc=0 >>
LISTEN 0 511 *:81  *:*  users:(("apache2",pid=1123,fd=4))
target1 | SUCCESS => {"changed": false, "ping": "pong"}
target2 | UNREACHABLE! => {"msg": "Failed to connect to the host via ssh: … port 22: Connection timed out"}
```

`CHANGED` on `shell` or `command` only means Ansible can't know; the command ran. `UNREACHABLE` is SSH (timeout = network, `Permission denied` = key or user); `FAILED` means it got in and the module failed.

**Why it is effective:** "which hosts still have X?" becomes one command across the inventory, with the same users, keys and become settings as your playbooks.

**Compared with an ssh loop:** fine for a few hosts you can name, but one at a time, with no groups, become or per-host status.

**Trap:** `all` with `-b` and a changing module (`-m apt -a "name=openssh-server state=latest"`) alters every host in seconds: name a group or add `--limit`. Hosts without Python need `-m ansible.builtin.raw`.

**Next step:** UNREACHABLE → `-m ansible.builtin.ping -vvvv` shows the exact ssh command. Wrong variable value → `ansible-inventory --host HOST`. A change worth repeating → a playbook.

### ansible-inventory / ansible-config — what does Ansible see for this host, and which settings apply?
Match: ansible-inventory, ansible-config
Instead of: reading group_vars files by eye
Safety: read-only

**In one line:** `ansible-inventory` prints the inventory as Ansible parsed it (groups, hosts, merged variables); `ansible-config dump --only-changed` prints each setting that differs from the defaults, with where it was set.

**Read the command:** `ansible-inventory -i inventories/all.yml --host app2`

| Part | Meaning |
|---|---|
| `-i inventories/all.yml` | the inventory to read (otherwise the one ansible.cfg names) |
| `--host app2` | one host's variables after merging group_vars and host_vars |
| `--graph` | the group tree with its hosts (`--vars` adds variables) |
| `--yaml` | YAML instead of JSON |
| `ansible-config dump --only-changed` | non-default settings, each with the file or variable that set it |

**What the output tells you:**

```
{
    "env_name": "prod"
}
@all:
  |--@dev:
  |  |--app2
  |--@prod:
  |  |--app1
  |  |--app2
```

app2 sits in both dev and prod. Sibling groups merge alphabetically and the later one (prod) wins, so a dev host gets production values. `app_port` is missing: it is set only for a group app2 isn't in.

**Why it is effective:** it answers "what value will this host get?" with Ansible's own merge rules, instead of tracing precedence by hand.

**Compared with reading group_vars:** the files show what is defined, not which groups a host is in or which definition wins.

**Trap:** `--host` shows **inventory** variables only: play vars, role vars, `set_fact` and `-e` can still override them (`ansible HOST -m ansible.builtin.debug -a var=NAME` shows the final value). Ansible ignores an `ansible.cfg` in a world-writable directory; `dump` shows which file is in use.

**Next step:** a host in two environments → one inventory per environment. Undefined variable → `--graph` and the group_vars location. Unexpected settings → `ANSIBLE_CONFIG` and the file `dump` names.

### ansible-vault — keep secrets encrypted in the same repository as the playbooks
Match: ansible-vault
Instead of: plain-text passwords in group_vars
Safety: changes state: `create`, `edit`, `encrypt` and `rekey` rewrite files · `view` prints the secrets to your terminal

**In one line:** `ansible-vault` encrypts whole variable files or single values with AES-256 under a vault ID label; Ansible decrypts them in memory at run time when it gets the matching password.

**Read the command:** `ansible-vault rekey --vault-id old@prompt --new-vault-id prod@prompt inventories/prod/group_vars/all/vault.yml`

| Part | Meaning |
|---|---|
| `rekey` | decrypt with the current password, encrypt again with a new one |
| `--vault-id old@prompt` | the current secret: label `old`, password typed at a prompt |
| `--new-vault-id prod@prompt` | the new label and password |
| `inventories/prod/group_vars/all/vault.yml` | the encrypted file |
| `create`, `view`, `edit FILE` | make, read or change an encrypted file |
| `encrypt_string --vault-id prod@prompt --name db_password` | encrypt one value to paste into a YAML file |
| `--vault-id "prod@${VAULT_PASS_PROD}"` | a password file instead of a prompt: the CI form |

**What the output tells you:**

```
$ head -1 inventories/prod/group_vars/all/vault.yml
$ANSIBLE_VAULT;1.2;AES256;prod
```

Format (1.2 = with a label), cipher and label. `no vault secrets found` means Ansible got no password at all; `Decryption failed` means it got one, but not this file's.

**Why it is effective:** secrets live versioned and reviewable next to the code that uses them, and one vault ID per environment keeps the staging password from opening prod files.

**Compared with plain-text group_vars:** the same at run time, but every clone, CI cache and backup then holds the passwords.

**Trap:** `rekey` protects the file from now on; old commits stay encrypted with the old password, which a leaver may still have: rotate the secrets themselves. A value typed on the `encrypt_string` command line lands in shell history; omit it and Ansible reads stdin. Put `no_log: true` on tasks that handle decrypted values.

**Next step:** CI can't decrypt → `head -1 FILE` for the label, `ansible-config dump --only-changed | grep -i vault`, then pass the matching `--vault-id`. Plain-text secret found → encrypt it, rotate it, check Git history.

### packer — build a VM template or AMI from code
Match: packer
Instead of: hand-building a golden VM and converting it to a template
Safety: changes state: `build` creates real VMs or cloud instances (billed while they run) and registers templates or AMIs · `init` and `plugins install` install plugins · `validate`, `version` and `plugins installed` only read

**In one line:** Packer boots a temporary machine from an ISO or base image, provisions it and saves it as a Proxmox template or an AMI; `packer init` first installs the plugins the template declares.

**Read the command:** `PACKER_LOG=1 packer build -on-error=ask . 2>&1 | tee packer.log`

| Part | Meaning |
|---|---|
| `PACKER_LOG=1` | verbose log: HTTP server port, SSH attempts, API calls |
| `build .` | build every source defined in this directory's `*.pkr.hcl` files |
| `-on-error=ask` | on failure, ask: clean up, abort (keep the machine to inspect) or retry; the default is `cleanup` |
| `2>&1 | tee packer.log` | keep the log while watching it |
| `init .`, `validate .` | install the plugins in `required_plugins`; check the template |
| `plugins install --path FILE github.com/hashicorp/proxmox` | install a downloaded plugin binary (air-gapped hosts) |

**What the output tells you:**

```
2026/10/03 10:02:14 ui: ==> proxmox-iso.ubuntu: Starting HTTP server on port 8802
2026/10/03 10:02:31 ui: ==> proxmox-iso.ubuntu: Waiting for SSH to become available...
```

Packer serves the autoinstall files on 8802 and waits for SSH. Ending in `Timeout waiting for SSH` means the installer never got its user-data (firewall, boot command) or Packer never learned the VM's IP (no guest agent).

**Why it is effective:** every template is rebuilt the same way from Git, cleanup included (machine-id, cloud-init state), so clones don't share an identity.

**Compared with a hand-built template:** quicker once, but not reproducible, and a forgotten cleanup gives every clone the same machine-id and DHCP lease.

**Trap:** since Packer 1.10 no plugins are bundled: `Missing plugins` means `packer init` never ran or the template lacks `required_plugins` (JSON templates can't declare it: `hcl2_upgrade` first). `-on-error=ask` needs a terminal; in CI use `abort` and delete the leftover machine yourself.

**Next step:** watch the VM's console during the build. HTTP port blocked → a fixed `http_port_min`/`http_port_max` and a firewall rule. Template built → test two clones: two IPs, two machine-ids.

### qm — what is this Proxmox VM's configuration, and how do I change, clone or rescue it?
Match: qm
Instead of: clicking through the web UI for each VM
Safety: read-only for `config`, `list`, `guest cmd … fsfreeze-status` and `agent … ping` · changes state: `set`, `clone`, `template`, `start`, `shutdown`, `cloudinit update`, `unlock`; a `--cpu` change takes effect only after a full stop and start

**In one line:** `qm` is the Proxmox VE command line for QEMU VMs: it prints and edits each VM's config under `/etc/pve/qemu-server/`, clones templates, controls power and talks to the guest agent.

**Read the command:** `qm set 9000 --ide2 local-lvm:cloudinit --serial0 socket --vga serial0 --boot order=scsi0`

| Part | Meaning |
|---|---|
| `set 9000` | change VM 9000's configuration |
| `--ide2 local-lvm:cloudinit` | add a cloud-init drive on storage `local-lvm`: how user, keys and network reach each clone |
| `--serial0 socket --vga serial0` | a serial port, used as the display: Ubuntu cloud images expect one |
| `--boot order=scsi0` | boot from the scsi0 disk |
| `clone 9000 133 --name app3 --full` | an independent full copy (from a template the default is a linked clone) |
| `set 133 --ipconfig0 ip=10.10.0.33/24,gw=10.10.0.1`, `cloudinit update 133` | the clone's own address; regenerate its cloud-init drive |
| `guest cmd 101 fsfreeze-thaw`, `unlock 101` | thaw a guest a backup left frozen; remove a stale `lock:` line |

**What the output tells you:**

```
$ qm config 101 | grep -E '^(agent|lock|net0)'
agent: 1
lock: backup
net0: virtio=BC:24:11:5A:6B:7C,bridge=vmbr0,tag=20
```

`lock: backup`: a backup holds the VM, so other operations time out. `agent: 1`: the guest agent is enabled, not necessarily answering (`qm agent 101 ping`). `net0`: model, MAC, bridge and VLAN 20, which the bridge and switch port must carry too.

**Why it is effective:** one text config per VM shows everything at once, the same change can be scripted across VMs, and it works when the web UI doesn't.

**Compared with the web UI:** the same settings, fine for one VM, but not scriptable, reviewable or repeatable.

**Trap:** `qm unlock` while the backup or migration still runs lets two operations write one disk: stop the task first. A CPU type change (`--cpu x86-64-v3`) needs `qm shutdown` then `qm start`; a reboot inside the guest is not enough. A template can't be started.

**Next step:** guest frozen in a backup → `qm guest cmd 101 fsfreeze-status`, thaw, stop the task, unlock. Clones share an IP → `cloud-init clean --machine-id` inside the template. VLAN VM offline → `bridge vlan show`, then the switch trunk.

### pct — what may this LXC container do, and run a command inside it
Match: pct
Instead of: running Docker in an LXC container without checking its features
Safety: read-only for `config` · changes state: `set` rewrites the container's config (a running container picks feature changes up after a restart); `exec` runs the command as root inside the container

**In one line:** `pct` manages Proxmox LXC containers: `config` prints a container's settings (privileged or not, features, mount points), `set` changes them, and `exec` runs a command inside it from the host.

**Read the command:** `pct exec 120 -- docker info --format '{{.Driver}}'`

| Part | Meaning |
|---|---|
| `exec 120` | run a command inside container 120, as its root user |
| `--` | the end of pct's own options; the rest is the command |
| `docker info --format '{{.Driver}}'` | the command: Docker's storage driver |
| `config 120` | `unprivileged:`, `features:`, `rootfs:` and `mp0:` mount points |
| `set 120 --features nesting=1,keyctl=1` | allow nested containers and the keyring calls dockerd needs |

**What the output tells you:**

```
$ pct config 120 | grep -E '^(features|unprivileged|rootfs|mp[0-9])'
features: nesting=1
mp0: /tank/media,mp=/srv/media
rootfs: local-zfs:subvol-120-disk-0,size=32G
unprivileged: 1
$ pct exec 120 -- docker info --format '{{.Driver}}'
vfs
```

Unprivileged, with nesting but no keyctl, on a ZFS subvolume; Docker has fallen back to `vfs`, which copies every layer in full. Container root is UID 100000 on the host, so host files owned by UID 1000 appear as `nobody:nogroup`.

**Why it is effective:** "Docker in LXC is broken" becomes concrete from the host: the missing feature, the fallback driver, the UID mapping of each mount.

**Trap:** `--features` replaces the whole option: list every feature you want, not only the new one. The container shares the host's kernel and AppArmor policy, so a host upgrade can break it with nothing changed inside. Making it privileged to "fix" permissions makes container root host root.

**Next step:** Docker, Swarm or k3s workloads → a VM cloned from your template (`qm clone`). Staying on LXC → nesting and keyctl, then restart. Bind-mount ownership → host owner = 100000 + the UID inside.

### pvecm — does the Proxmox cluster have quorum, and how do I restore it safely?
Match: pvecm, corosync-cfgtool
Instead of: rebooting nodes until the web UI works again
Safety: read-only for `status` · changes state: `expected` lowers the votes needed (split-brain risk), `delnode` removes a node for good, `qdevice setup` adds a vote, `updatecerts --force` reissues the node's certificates

**In one line:** `pvecm` manages the Proxmox cluster (corosync); `status` shows the votes and whether the cluster is quorate, which decides whether `/etc/pve` is writable at all.

**Read the command:** `pvecm status`

| Part | Meaning |
|---|---|
| `status` | membership, expected and total votes, the quorum threshold, `Quorate:` |
| `expected 1` | emergency: let this node reach quorum alone (only if the others are certainly off) |
| `qdevice setup 192.0.2.40` | add an external vote (corosync-qnetd on a small third machine) |
| `delnode pve2` | remove a dead node from the cluster configuration |
| `updatecerts --force` | reissue this node's certificates after an address or name change |

**What the output tells you:**

```
$ pvecm status | grep -E 'Quorate|Expected votes|Total votes|Quorum:'
Quorate:          No
Expected votes:   2
Total votes:      1
Quorum:           2 Activity blocked
```

A two-node cluster with one node gone: one vote of the two needed, so `/etc/pve` is read-only and VMs can't be started, edited or created (`cluster not ready - no quorum?`).

**Why it is effective:** "the web UI refuses everything" has one cause here, missing votes, and this shows the numbers you need to decide: wait, add a vote, or remove a node.

**Compared with rebooting:** a rebooted survivor still has one vote of two, so nothing changes.

**Trap:** `pvecm expected 1` on both halves of a split cluster lets each write alone: split-brain. Use it only while the other node is certainly off. A removed node must be reinstalled before it rejoins. Corosync is latency-sensitive: sharing its link with backups or Ceph drops members that are actually up.

**Next step:** node only rebooting → wait. Two nodes → `pvecm qdevice setup` on a third machine. Node dead for good → power it off permanently, `pvecm delnode`. Flapping membership → `corosync-cfgtool -s`, a dedicated corosync link. Related: `corosync-cfgtool -s` is read-only and shows this node's corosync links (`LINK ID 0 udp`, its address) and, per node, `localhost`, `connected` or `disconnected`: the network view behind the vote count.

### pveum — which user, token and role does automation use on Proxmox?
Match: pveum
Instead of: giving Terraform the root@pam password
Safety: read-only for `… list` · changes state: `role add`, `aclmod` and token changes alter who may do what, cluster-wide, at once

**In one line:** `pveum` manages Proxmox users, API tokens, roles and ACLs; a token used by Terraform or Packer gets exactly the privileges granted, on the paths granted.

**Read the command:** `pveum aclmod / -token 'terraform@pve!ci' -role TerraformProv`

| Part | Meaning |
|---|---|
| `aclmod` | older alias of `pveum acl modify`: add an ACL entry |
| `/` | the path: the whole tree (also `/vms/101`, `/storage/local-lvm`, `/sdn/zones/…`); entries apply below it |
| `-token 'terraform@pve!ci'` | API token `ci` of user `terraform@pve`; single quotes stop the shell expanding `!` |
| `-role TerraformProv` | the role whose privileges apply |
| `role add TerraformProv -privs "VM.Allocate VM.Clone … SDN.Use"` | define a role from a privilege list |
| `user token list terraform@pve` | the user's tokens, with expiry and `privsep` |

**What the output tells you:**

```
│ tokenid │ comment │ expire │ privsep │
╞═════════╪═════════╪════════╪═════════╡
│ ci      │         │      0 │ 1       │
```

`privsep 1`: a privilege-separated token, whose rights are the **intersection** of its user's ACLs and its own; with no ACL of its own it can do nothing. `expire 0`: never expires.

**Why it is effective:** a role and token per tool limits the blast radius, can be revoked alone, and turns `Permission check failed (/sdn/zones/localnetwork/vmbr0, SDN.Use)` into one missing privilege on one path.

**Compared with root@pam:** it works for everything, which is the problem: it can delete every VM and can't be revoked for one tool.

**Trap:** grant the ACL to the user **and** to a privilege-separated token. Privilege names change between releases (SDN.Use came with PVE 8; PVE 9 deprecated VM.Monitor), so a role copied from an old guide fails on a new version.

**Next step:** 403 from Terraform → the privilege and path in the message, then `pveum role modify` or a new ACL. Provider crashes → pin its version and compare its release notes with `pveversion`.

### proxmox-backup-manager — why doesn't pruning free space on the backup datastore?
Match: proxmox-backup-manager
Instead of: deleting files under .chunks by hand
Safety: read-only for `list` · changes state: `garbage-collection start` deletes unreferenced chunks (by design); prune jobs delete backup snapshots

**In one line:** `proxmox-backup-manager` administers a Proxmox Backup Server: datastores, prune jobs, garbage collection and the task log of each run.

**Read the command:** `proxmox-backup-manager garbage-collection start store1`

| Part | Meaning |
|---|---|
| `garbage-collection start` | run GC now: mark every chunk still referenced, then delete those unused for longer than the cutoff |
| `store1` | the datastore |
| `prune-job list` | the retention jobs (keep-daily, keep-weekly…) per datastore |
| `task list --limit 5` | the five latest tasks; a GC task's log reports pending removals |

**What the output tells you:**

```
2026-10-03T04:00:12+00:00: Pending removals: 812.4 GiB (in 391022 chunks)
```

812 GiB of chunks are unreferenced but were touched within the cutoff (24 hours and 5 minutes by default), so this run keeps them; the next GC after the cutoff deletes them.

**Why it is effective:** PBS deduplicates, so pruning removes only snapshot indexes; space returns only when GC deletes chunks nothing references, after the cutoff. The task log shows which stage you are at.

**Compared with deleting `.chunks` files:** that frees space at once and silently breaks every backup still referencing those chunks.

**Trap:** on a 100% full ZFS pool, GC can't even mark chunks, because copy-on-write needs free space: make a little room first. ZFS snapshots of the datastore's dataset pin every chunk GC deletes. Without a prune job nothing ever becomes unreferenced.

**Next step:** no prune job → retention in the GUI (Datastore → Prune & GC). Space pinned → `zfs list -t snapshot` on the dataset. Afterwards → an alert at 80% and a quota as headroom.

### git log — what changed, when, and by whom?
Match: git log
Instead of: asking the team "did anyone change anything?"
Safety: read-only

**In one line:** `git log` lists commits newest first; with a time window, a path and a format, it answers "what changed in the last few hours, where, and by whom?".

**Read the command:** `git -C infra log --since '3 hours ago' --format='%h %ad %an %s' --date=format:%H:%M`

| Part | Meaning |
|---|---|
| `-C infra` | run as if inside the `infra` directory |
| `log` | the history of the current branch |
| `--since '3 hours ago'` | only commits newer than this |
| `--format='%h %ad %an %s'` | short hash, author date, author name, subject |
| `--date=format:%H:%M` | print that date as hour:minute |
| `-- traefik/` | only commits that touched this path |
| `--oneline --graph --all -15`, `main..origin/main` | every branch as a graph; commits on origin/main you lack |
| `--all -S 'glpat-'` | commits that added or removed that string |

**What the output tells you:**

```
e91b3c0 14:01 ops traefik: add security-headers middleware to all routers
a71f0d2 11:20 ops ufw: allow 9100 from monitoring
```

The first errors appeared at 14:02, so the 14:01 commit is the prime suspect, and `e91b3c0` is what you revert.

**Why it is effective:** most incidents follow a change, and a few hours of history filtered to the affected path usually names both the cause and the rollback.

**Compared with asking the team:** people remember what they meant to change; the log shows what was committed, by which account, and when.

**Trap:** you see only what this clone has: `git fetch` first. `--since` filters on the commit date while `%ad` prints the author date; after a rebase they differ (`%cd` prints the commit date). A change made by hand on a server is not in Git at all.

**Next step:** suspect commit → `git show --stat SHA`, then `git revert`. Nothing in Git → CloudTrail, Ansible logs, the host's shell history. Secret found with `-S` → rotate it, then `git filter-repo`.

### git revert — undo a commit that is already pushed or deployed
Match: git revert
Instead of: git reset --hard, git push --force
Safety: changes state: creates a new commit on the current branch (pushing it deploys the undo); a conflict stops it half-way

**In one line:** `git revert` adds a new commit that applies the inverse of an earlier one, so shared history stays intact and the pipeline deploys the undo like any other change.

**Read the command:** `git -C infra revert --no-edit e91b3c0`

| Part | Meaning |
|---|---|
| `-C infra` | in the `infra` repository |
| `revert e91b3c0` | create a commit that undoes e91b3c0 (any commit, not only the latest) |
| `--no-edit` | keep the default message `Revert "…"`, no editor |
| `revert --no-edit HEAD` | undo the most recent commit |
| `revert -m 1 MERGE_SHA` | undo a merge commit, keeping parent 1 (the main line) |

**What the output tells you:**

```
$ git log --oneline -3
9d8c7b6 (HEAD -> main) Revert "Set Traefik service port to 8080"
5e4f3a2 Set Traefik service port to 8080
a1b2c3d Add /healthz endpoint
```

History shows the mistake and its undo: the pipeline deploys `9d8c7b6`, and the postmortem can point at `5e4f3a2`. Nothing leaves your machine until `git push`.

**Why it is effective:** "revert the last change and let the pipeline redeploy" is often the fastest safe mitigation, and revert does it without rewriting history everyone else has.

**Compared with `git reset --hard` and a force-push:** fine before a push; afterwards it rewrites shared history, breaks colleagues' clones and needs a force-push that protected branches refuse.

**Trap:** a revert undoes the diff, not its side effects: a database migration or a deleted volume stays done. After reverting a merge, merging that branch again brings nothing back until you revert the revert. On a conflict: fix, then `git revert --continue`, or `--abort`.

**Next step:** `git push`, watch the pipeline, confirm the symptom is gone. Config rolled out by Ansible → run the playbook again with `--diff`. Then fix forward on a branch.

### git reset — move a branch back, and choose what happens to your changes
Match: git reset
Instead of: deleting and re-cloning the repository
Safety: changes state: moves the current branch; `--hard` also overwrites the index and the working tree, and **uncommitted work is lost for good**

**In one line:** `git reset TARGET` moves the current branch to another commit; the mode decides whether the changes in between stay staged (`--soft`), stay as unstaged edits (`--mixed`, the default) or are thrown away (`--hard`).

**Read the command:** `git reset --soft HEAD~1`

| Part | Meaning |
|---|---|
| `reset` | move the current branch pointer, and HEAD with it |
| `--soft` | keep index and working tree: the undone commit's changes stay staged |
| `HEAD~1` | the first parent of HEAD: one commit back |
| `--mixed` (default) | also reset the index: changes kept, but unstaged |
| `--hard rescue` | branch, index and working tree all become what `rescue` points at |
| `ORIG_HEAD` | where HEAD was before the last reset, merge or rebase |

**What the output tells you:** `--soft` prints nothing, so check the result:

```
$ git status -s
M  ports.conf
$ git log --oneline -1
a1b2c3d Add /healthz endpoint
```

The commit is gone from the branch and its change to `ports.conf` is staged again (`M` in the first column), ready to be split or committed again.

**Why it is effective:** it repairs local history precisely (redo the last commit, put a branch back on a known commit), and each mode states what happens to your files.

**Compared with re-cloning:** a fresh clone throws away local branches, stashes and the reflog, the very things a rescue needs.

**Trap:** `--hard` overwrites uncommitted edits, which no Git command can recover: `git stash push -u` first. Commits dropped by a reset stay recoverable from the reflog for a while. On a pushed branch, reset plus force-push rewrites shared history: use `git revert`.

**Next step:** commits lost to a reset → `git reflog`. Pushed mistake → `git revert`. Unsure what you'd lose → `git status`, `git diff`. Unstage one file → `git restore --staged FILE`.

### git reflog — where was HEAD before I broke it?
Match: git reflog
Instead of: git log, which no longer shows the lost commits
Safety: read-only · the rescue that follows (`git branch rescue HEAD@{1}`) only adds a pointer

**In one line:** the reflog is a local diary of every position HEAD and each branch has had (commits, resets, rebases, checkouts), so commits that `git log` can no longer reach can be found and restored.

**Read the command:** `git reflog -8`

| Part | Meaning |
|---|---|
| `reflog` | HEAD's moves, newest first (`git reflog show BRANCH` for one branch) |
| `-8` | the last eight entries |
| `HEAD@{1}` | where HEAD was one move ago; usable wherever a commit is |
| `git branch rescue HEAD@{1}` | the safe first step: a new branch at that commit |
| `git reset --hard rescue` | after checking it with `git log --oneline rescue -4`, move your branch there |

**What the output tells you:**

```
a1b2c3d (HEAD -> main) HEAD@{0}: reset: moving to HEAD~3
f4e5d6c HEAD@{1}: commit: Add Traefik labels for shop-web
0b1c2d3 HEAD@{2}: commit: Add healthcheck to Dockerfile
7e8f9a0 HEAD@{3}: commit: Move gunicorn to port 8000
a1b2c3d (HEAD -> main) HEAD@{4}: checkout: moving from feature/healthz to main
```

Read bottom-up: three commits, then a reset threw them away. `f4e5d6c` (HEAD@{1}) is the state just before the reset.

**Why it is effective:** commits survive a reset or a bad rebase in the object store, and the reflog still points at them, so "I destroyed the hotfix" becomes a two-minute recovery.

**Compared with `git log`:** log shows only commits reachable from branches and tags, so the lost work is invisible there.

**Trap:** the reflog belongs to one clone: work lost on a server's clone is in that clone's reflog, and a fresh clone has none. Entries expire (90 days by default, 30 for commits no longer on a branch), and `git gc --prune=now` can remove lost commits sooner. Uncommitted edits never appear.

**Next step:** commit found → `git branch rescue SHA`, inspect, `git reset --hard rescue`. Not in the reflog → `git fsck --lost-found`. Bad rebase → `git reset --hard ORIG_HEAD`.

### git filter-repo — remove a file or a secret from the whole history
Match: git filter-repo
Instead of: git rm in a new commit, git filter-branch
Safety: changes state: rewrites every commit from the first affected one on (new SHAs) and removes the `origin` remote; publishing needs a force-push and fresh clones everywhere

**In one line:** `git filter-repo` (a separate tool: Ubuntu package `git-filter-repo`) rewrites the whole history, dropping paths or replacing text in every commit, so a leaked file leaves the repository itself.

**Read the command:** `git filter-repo --invert-paths --path deploy/harbor.env --force`

| Part | Meaning |
|---|---|
| `--path deploy/harbor.env` | select this path in every commit |
| `--invert-paths` | keep everything **except** the selected paths: delete that file from all history |
| `--force` | run even though this is not a fresh clone (it refuses otherwise, as a safety check) |
| `--replace-text replacements.txt` | rewrite text in every file; lines such as `glpat-OLDVALUE==>REDACTED` |
| `git remote add origin git@gitlab.example.com:shop/api.git` | filter-repo removed `origin` on purpose; add it back |
| `git push --force origin main feature/new-deploy` | publish the rewritten branches (no remote-tracking refs are left for `--force-with-lease`) |

**What the output tells you:**

```
$ git log --all --oneline -- deploy/harbor.env
$ gitleaks git --redact -v .
11:52AM INF 44 commits scanned.
11:52AM INF no leaks found
```

Before the rewrite the first command listed `9b1e44c add harbor env for deploy`; now no commit contains the file, and the scan agrees.

**Why it is effective:** a file deleted in a new commit still sits in every clone's old commits; rewriting is the only way to clean the repository itself, and filter-repo is fast and safe where `git filter-branch` is slow and error-prone.

**Compared with `git rm`:** it removes the file from now on, enough for files that never held secrets; the old snapshots still contain it.

**Trap:** rewriting un-leaks nothing: forks, other clones, CI caches and GitLab merge-request refs keep the old objects. **Rotate the secret first.** Protected branches refuse the force-push until allowed, and a push from an old clone brings the file back.

**Next step:** rotate, check the old credential's use in audit logs, rewrite, force-push, have everyone re-clone, then add gitleaks as a pre-commit hook and a CI job.

### git — the everyday subcommands: status, diff, commit, branches, remotes, config
Match: git
Instead of: —
Safety: read-only for `status`, `diff`, `show`, `branch -vv`, `remote -v`, `grep`, `ls-files`, `check-ignore` · changes state: `add`, `commit`, `switch`, `checkout … -- FILE`, `merge`, `pull`, `push` (`--force` overwrites the remote branch), `config --global`

**In one line:** everything else Git does in this handbook: inspect the working tree, record commits, move between branches, sync with GitLab, configure identity and signing.

**Read the command:** `git branch -r --contains 9b1e44c`

| Part | Meaning |
|---|---|
| `branch -r` | remote-tracking branches (`origin/…`), as of your last fetch |
| `--contains 9b1e44c` | only those whose history includes this commit: where a leak or a fix has spread |
| `fetch --prune` | update remote-tracking branches; drop those deleted on the server |
| `status`, `diff`, `diff --staged`, `show --stat HEAD` | what changed: unstaged, staged, in the last commit |
| `add -p FILE`, `commit -m "…"`, `push -u origin main` | stage hunk by hunk, record, publish and set the upstream |
| `push --force-with-lease` | overwrite a remote branch only if it is still where you last saw it (`--force` doesn't check) |
| `check-ignore -v .env`, `grep -nE 'PATTERN'` | which .gitignore rule applies; search the tracked files |
| `checkout a81c3e7 -- FILE`, `config --global commit.gpgsign true` | restore one file from a commit; sign every commit |

**What the output tells you:**

```
  origin/feature/new-deploy
  origin/main
```

The leaked commit is on `main` and on a feature branch: both need rewriting, and every clone that fetched them has a copy.

**Why it is effective:** most "the pipeline built the wrong code" and "who has this commit?" questions are answered by these read-only views before anyone changes anything.

**Trap:** remote-tracking branches are only as fresh as your last `git fetch`. `git pull` is a fetch plus a merge or rebase, depending on `pull.rebase`. A plain `git push` sends no tags. `.gitignore` affects only untracked files: a tracked `.env` stays tracked until `git rm --cached .env`.

**Next step:** push rejected `(fetch first)` → `git fetch`, `git log --oneline main..origin/main`, `git pull --rebase`. Secret tracked → `git rm --cached`, rotate, `git filter-repo`. Unsure what a commit did → `git show --stat SHA`.

### gitlab-runner — is this runner registered, accepted by GitLab, and picking up jobs?
Match: gitlab-runner
Instead of: restarting the service and hoping
Safety: changes state: `register` adds an entry, token included, to `/etc/gitlab-runner/config.toml`; `verify --delete` removes the entries GitLab rejects · read-only for `verify`, `list`, `status` and `--version` (`list` prints tokens)

**In one line:** `gitlab-runner` polls GitLab for jobs and runs them through an executor; `register` connects it with a runner token, and `verify` asks GitLab whether each configured token is still valid.

**Read the command:** `sudo gitlab-runner register --non-interactive --url "https://gitlab.example.com" --token "$RUNNER_TOKEN" --executor "docker" --docker-image "alpine:3.22" --name "ci-01-docker"`

| Part | Meaning |
|---|---|
| `sudo … register --non-interactive` | system-wide config `/etc/gitlab-runner/config.toml`; no questions asked |
| `--url "https://gitlab.example.com"` | the GitLab instance (its CA must be trusted) |
| `--token "$RUNNER_TOKEN"` | the `glrt-` token shown once when the runner was created in the UI, kept out of history |
| `--executor "docker" --docker-image "alpine:3.22"` | each job in a fresh container; this image when a job names none |
| `--name "ci-01-docker"` | the name in config.toml and in the UI |
| `verify`, `verify --delete`, `list`, `status` | check tokens; drop rejected entries; list runners; service state |

**What the output tells you:**

```
Verifying runner... is valid               runner=t3_Kd9aQ
ERROR: Verifying runner... is removed      runner=t3_Kd9aQ
```

`is valid`: the token works and GitLab answers over TLS. `is removed`: GitLab no longer knows the token (runner deleted, token reset or expired; the journal shows `403 Forbidden` on `jobs/request`), so a restart changes nothing.

**Why it is effective:** verify says in one line whether this host can serve jobs at all, before you debug tags or YAML.

**Compared with restarting the service:** a restart revives a crashed process; it can't fix a dead token, a missing tag or an untrusted CA.

**Trap:** since GitLab 16, tags, "run untagged" and protection are set in the UI: `--tag-list`, `--locked` or `--run-untagged` with a `glrt-` token fails as "reserved", and an old registration token gets `410 Gone`. `list` prints each runner's token.

**Next step:** `is removed` → create the runner again in the UI, `verify --delete`, register. Valid but jobs pending → job `tags:` versus the runner's, and `concurrent` in config.toml. `x509` errors → `/etc/gitlab-runner/certs/HOST.crt`.

### glab / gh — query GitLab or GitHub from the terminal
Match: glab, gh
Instead of: clicking through the web UI, curl with a hand-pasted token
Safety: read-only for `api` GET requests · changes state: `glab issue create` opens an issue; `api -X POST`, `PUT` or `DELETE` writes

**In one line:** `glab api` and `gh api` call the GitLab or GitHub REST API with the token you logged in with, so issues, merge requests, deployments and runners become JSON you can filter with jq.

**Read the command:** `glab api "projects/ops%2Fplatform/issues?labels=incident&state=closed&order_by=updated_at&per_page=10"`

| Part | Meaning |
|---|---|
| `api` | a REST call to the instance you logged in to (`glab auth login`); GET by default |
| `projects/ops%2Fplatform` | project `ops/platform`; the `/` in its path is URL-encoded as `%2F` |
| `issues?labels=incident&state=closed` | closed issues labelled `incident` |
| `order_by=updated_at&per_page=10` | most recently updated first, 10 per page (GitLab's default is 20, the maximum 100) |
| `--paginate` | follow every page, not just the first |
| `glab issue create --repo ops/platform --title "…" --label "incident,sev1"` | open an issue (**writes**) |
| `gh api repos/ORG/REPO/actions/runners --jq '.runners[] | …'` | GitHub: self-hosted runners with status, busy flag and labels; `--jq` filters built in |

**What the output tells you:** a JSON array; counting who closed each incident (`jq -r '.[].closed_by.username' | sort | uniq -c`) gives:

```
      8 ops
      2 deploy
```

Eight of the last ten incidents were closed by the same account: a bus factor of one.

**Why it is effective:** questions about how the team works get answered from data in one line, and the same call scripts into a report.

**Compared with `curl`:** curl with a `PRIVATE-TOKEN` header works too, but puts the token in your command and history; glab and gh reuse the stored login.

**Trap:** without `--paginate` you get only the first page, so counts quietly stop at 20 or 100. Results include only what your account can see. Quote the whole URL: `&` is a shell operator.

**Next step:** a number worth tracking → a scheduled pipeline job running the same call. A GitHub runner `offline` → the runner VM's service and logs.

### multipass — spin up a disposable Ubuntu lab VM
Match: multipass
Instead of: installing a VM by hand from an ISO
Safety: changes state: `launch` creates a VM and its disk on this machine, using its CPU and RAM while it runs

**In one line:** Multipass (from Canonical) launches an Ubuntu cloud-image VM with one command, configured through cloud-init like your servers, so every module gets a lab you are allowed to break.

**Read the command:** `multipass launch 24.04 --name lab1 --cpus 2 --memory 4G --disk 20G`

| Part | Meaning |
|---|---|
| `launch 24.04` | create and start a VM from the Ubuntu 24.04 image |
| `--name lab1` | its name (otherwise a random one) |
| `--cpus 2` | virtual CPUs |
| `--memory 4G` | RAM |
| `--disk 20G` | disk size |
| `multipass shell lab1` | a shell inside it, as the `ubuntu` user |

**What the output tells you:** `Launched: lab1` when the VM is up; `multipass shell lab1` then opens an Ubuntu prompt inside it.

**Why it is effective:** a clean, current Ubuntu on the same cloud-init path as your servers, created and thrown away in minutes, so a broken lab costs nothing.

**Compared with an ISO install:** full control (partitioning, extra disks), but far slower, and it drifts from the cloud images your servers run.

**Trap:** it needs hardware virtualisation: inside a VM, such as a Proxmox guest, that means nested virtualisation switched on. The storage labs want a second virtual disk, which is simpler to add in Proxmox, KVM or VirtualBox.

**Next step:** recreate rather than repair: keep the launch line, and when a lab goes wrong run `multipass delete lab1`, `multipass purge` and launch again.
