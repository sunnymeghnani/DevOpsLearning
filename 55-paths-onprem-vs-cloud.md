# 55 — Choose Your Path: On-Premise or Cloud

DevOps work happens in two kinds of place: servers you own in a room you can walk into, and capacity you rent from a cloud provider through an API.
The skills underneath are the same (Linux, networking, containers, automation, troubleshooting), but the first move in an incident, the cost model and the career path are not.
This page puts both side by side for your setup: Ubuntu servers, Dokploy, GitLab CI with Harbor, Wazuh, Proxmox and a CKA homelab, plus AWS.
Pick your path with the selector in the top bar: this page, the environment-specific entries elsewhere in the handbook, and the 3D course map with its guided path follow it.

---

## 0. How to use this page

### The path selector

The top bar has a path selector with three choices: **🏢 On-prem**, **☁️ Cloud** and **Both**. It changes this page and the study material around it.

| Choice | On this page | On the roadmap and the 3D course map |
|---|---|---|
| 🏢 On-prem | Shows the on-premise blocks: the on-prem path in section 4, the on-prem career notes, self-check and next steps. Cloud-only blocks are hidden | Filters the [3D course map](#map) and its guided path to on-premise topics plus the shared foundations, so the study path you follow skips the five cloud-only topics (marked ☁️ on the [Roadmap](34-roadmap.md) page) |
| ☁️ Cloud | Shows the AWS blocks: the cloud path in section 5, the cloud career notes, self-check and next steps. On-prem-only blocks are hidden | Filters the map and its guided path to AWS topics plus the shared foundations, skipping the seven on-prem-only topics (marked 🏢 on the roadmap page) |
| Both | Shows every block, the two paths one after the other | Shows every topic on the map and the full guided path |

What never changes: sections 1, 2, 3 and 6, and the shared parts of sections 7 to 9, apply to both environments and are always visible. Every numbered section also stays in the sidebar whatever you pick; with one environment selected, the other path's section shows only its heading and a one-line note. In the Markdown file itself, or when the page cannot run scripts, every block is visible, which is the same as Both.

### Which choice to make

| You are | Pick | Read first |
|---|---|---|
| Working only on your own servers, with no cloud plans this year | 🏢 On-prem | Sections 1–4, then the on-prem self-check |
| Joining a cloud-first team, or studying for an AWS exam | ☁️ Cloud | Sections 1–3 and 5, then the cloud self-check |
| Running on-prem today and adding AWS (that is you) | Both | Sections 1–3, your current stage in sections 4 and 5, then 6 and 7 |

Switch to a single path when you want a focused study list for the week, and back to Both when you plan the next quarter.

**When something is broken now:** skip to section 2, find the symptom, run the first check for your environment and follow the playbook link. Section 3 then translates any tool name you meet into its counterpart on the other side.

**Stages and tags:** stages and levels are one scale, as in the [Career Ladder](40-career-ladder.md): Fresher [L0 · Fresher], Junior [L1 · Junior], Mid-level [L2 · Mid], Senior [L3 · Senior] and Senior/Lead [L4 · Lead/SRE].

**Placeholders and examples:** UPPERCASE words in commands are placeholders (INSTANCE_ID, VOL_ID, TG_ARN, SUBNET_ID, CERT_ARN, VMID, HOST). On-prem examples use 192.0.2.0/24 with internal DNS at 192.0.2.53 and the user ops; AWS examples use a lab VPC 10.20.0.0/16; names live under example.com. Every command is documented for your lab or your own servers, so read it before you run it.

---

## 1. What actually changes

A server is a server in both places: Ubuntu, systemd, a disk and a network card. What changes is who owns each layer under your application, how those layers fail, how you pay for them and how fast you get more.

```
                         On-prem       AWS EC2       AWS managed (RDS, Fargate)
 Application             you           you           you
 Data and who reads it   you           you           you
 Runtime and middleware  you           you           AWS
 Operating system        you           you           AWS
 Hypervisor              you           AWS           AWS
 Servers and network     you           AWS           AWS
 Power, cooling, room    you           AWS           AWS
```

### Who owns which layer

| Layer | 🏢 On-prem | ☁️ Cloud (AWS) | Hybrid |
|---|---|---|---|
| Hardware | You buy, rack, cable and replace servers, disks and NICs, watch SMART, RAID and the IPMI event log, and keep spares and warranty contracts | AWS. You pick an instance type; a failing host shows up as a failed system status check or a scheduled retirement event | Hardware tickets on one side and instance events on the other, handled by one on-call rota |
| Power and cooling | You or your colocation provider: dual power supplies on separate feeds, UPS runtime, generator tests, room temperature | AWS. Each Availability Zone has its own power and cooling, so you spread workloads across AZs | A power cut on-prem must not take down the VPN or the DNS that the AWS side depends on |
| Network | Switches, VLANs, routers, the edge firewall, ISP uplinks and cabling | AWS runs the wires; you design the VPC: CIDRs, subnets, route tables, gateways, security groups and NACLs | VPN or Direct Connect, one non-overlapping address plan, routing and MTU across both |
| Hypervisor | Proxmox VE, VMware or KVM: you patch, cluster, size and back it up | AWS (the Nitro system on current instance types). You never log in to it | Two placement models: you place VMs on nodes, AWS places instances on hosts |
| Operating system | Ubuntu: patching, hardening, users, time | Still you on EC2, with the same Ubuntu. On Fargate, Lambda or RDS, AWS patches it | One patch and hardening baseline for both (Ansible roles, Wazuh SCA checks) |
| Runtime and platform | Docker, Swarm under Dokploy, kubeadm or k3s: installs, upgrades, certificates, etcd backups | ECS or EKS: AWS runs the control plane; you run the nodes (unless Fargate), the add-ons and the version upgrades | The same images and Helm charts on both; Harbor replicating to ECR |
| Application | You | You | You, with one pipeline deploying to both |
| Data | You: disks, RAID, replication, encryption at rest, the building it sits in | You decide what is stored, in which region, who can read it and which keys encrypt it; AWS runs the storage hardware | You decide where each dataset's primary copy lives; replication crosses the link and the bill |
| Identity | Active Directory, LDAP or Keycloak, SSH keys, sudo rules | IAM and IAM Identity Center: every API call is authorised by a policy | One identity provider federated into both, never a second set of accounts |
| Security monitoring | Wazuh, CrowdSec, Fail2ban, firewall logs: you collect, store and read them | CloudTrail, GuardDuty, Security Hub and Inspector produce findings; you still route them to a person and act | Alerts from both land in one place, with one on-call |
| Backups | Proxmox Backup Server, restic, pgBackRest, offsite copies and restore tests | AWS Backup and snapshots are features; switching them on, copying them out of the account or region and testing restores is your job | Each side can hold the other's offsite copy |
| Compliance | You prove everything: physical access, change records, retention, audits | Shared: AWS provides attestation reports for its layers (AWS Artifact); you prove your own configuration | One audit, with evidence from two systems |

Read the table as a list of jobs that move. Going to AWS, you stop owning the bottom rows (hardware, power, hypervisor, the physical network) and you start owning a new one: the API, its permissions and its bill. Going the other way, the facility work is the part nobody mentions in the job advert.

### How things fail

**On-prem failures are physical, local and visible.** A disk dies and the RAID rebuild slows every VM on the host, a power supply fails, a switch port flaps, a UPS battery is older than its runtime label, the cooling fails on a weekend, or the Proxmox cluster simply runs out of RAM. You see them in `dmesg`, SMART, the IPMI event log and the switch, and you fix them with hands, spare parts and vendor support. New hardware takes weeks to arrive, so spares and headroom are part of the design.

**Cloud failures come from the provider and from the API.** An instance is retired or fails its system status check, an Availability Zone is impaired, an API call is throttled (`RequestLimitExceeded`, `ThrottlingException`), a service quota blocks a launch (the vCPU limit, Elastic IPs per region), a credential expires, an IAM policy or SCP denies the call, or a route is missing. You cannot touch the hardware, so you replace instead of repair: stopping and starting an EBS-backed instance moves it to a healthy host. The bill is a failure signal too: a NAT gateway that processed a surprise terabyte is an incident.

**Common to both:** most outages start with a change, such as a config edit, an expired certificate, a full disk or a DNS record. The layered walk in [Site down](25-playbook-site-down.md) works in both places; only the first command at each layer changes, which is what section 2 is for.

### How you pay

**On-prem is capital expense (capex).** You pay up front for servers, storage and network gear, then for power, space, cooling, licences, support contracts and the people who run it, and you depreciate the hardware over several years. One more VM costs almost nothing until the cluster is full; then the next step is a large purchase with a lead time. Cost problems arrive as capacity running out, not as a bill. See the [On-prem cost model](39-learn-senior-architecture.md#on-prem-cost-model-l3-senior).

**Cloud is operating expense (opex).** You pay per second, per GB and per request, with nothing up front. Small and spiky workloads are cheap; large, steady ones can cost more than owned hardware over the years unless you buy commitments (Savings Plans or Reserved Instances). The charges that surprise on-prem engineers are data transfer out, NAT gateway processing, public IPv4 addresses, cross-AZ traffic, idle volumes and snapshots, and logs kept forever. See [Cost and FinOps](36-learn-cloud-aws.md#12-cost-and-finops).

### How fast you get capacity

On-prem, new hardware takes weeks to months: quote, purchase order, delivery, racking and cabling. A new VM on existing capacity takes minutes with a Proxmox template and cloud-init, or days if it waits in a ticket queue. On AWS, capacity arrives in minutes through the API until you hit a service quota; raising a quota can take hours or days, and a particular instance type can be short in one AZ. Fast provisioning also means fast mistakes: one wrong `count` in Terraform creates a hundred instances as easily as one.

### Where the data lives

On-prem, you can name the building, the rack and the disk that hold every record, which makes data-residency and sovereignty rules (banking, government, healthcare and many national data-protection laws) easier to prove. On AWS, data stays in the region you choose unless you or a service copies it elsewhere (cross-region replication, backup copies, global services), and you prove it with configuration: an SCP that denies other regions, Config rules and AWS's compliance reports. Some rules also require that you hold the encryption keys yourself, or forbid a foreign provider altogether. That is a legal question: ask your compliance team rather than a forum, and record the answer in a decision record.

---

## 2. Same symptom, different first moves

The symptom is the same in both places; the first command is not. Each row gives the first check for each environment and the playbook that takes over from there. Run the first check, read what it tells you, then follow the link. The selector never hides this table, because comparing the two columns is the point of it.

| Symptom | 🏢 On-prem first check | ☁️ AWS first check | Playbook |
|---|---|---|---|
| Server unreachable (no ping, no SSH) | `ping -c 3 192.0.2.10` and `nc -vz 192.0.2.10 22`; if nothing answers, open the console: `qm status VMID` on the Proxmox host, or the out-of-band controller (IPMI, iDRAC, iLO) for bare metal | `aws ec2 describe-instance-status --instance-ids INSTANCE_ID --include-all-instances` for the instance and system status checks, then the security group, NACL and route table; console: EC2 → Instances → Status and alarms, or VPC Reachability Analyzer | [Site down: connection scenarios](25-playbook-site-down.md#5-connection-scenarios), [AWS timeout checklist](16-aws-cloud.md#5-vpc-networking-the-timeout-checklist) |
| Disk full | `df -h` and `df -i`, then `sudo du -xh --max-depth=1 /var`; on the Proxmox host also `pvesm status` and `lvs` (thin pool Data%) | The same `df -h` inside the instance; to grow it: `aws ec2 modify-volume --volume-id VOL_ID --size 40`, then `sudo growpart /dev/nvme0n1 1` and `sudo resize2fs /dev/nvme0n1p1` | [No space left on device](01-storage-disk.md#decision-tree-no-space-left-on-device), [Grew the EBS volume](50-problems-cloud-iac-proxmox.md#22-grew-the-ebs-volume-df-shows-the-old-size) |
| Slow disk I/O | `iostat -xz 1 5` (await, %util), then `sudo smartctl -a /dev/sda` and the RAID state (`cat /proc/mdstat` or the controller tool); on Proxmox, the health of ZFS or Ceph on the host | `iostat -xz 1 5`, then the volume's CloudWatch metrics (VolumeQueueLength, and BurstBalance on gp2), the IOPS and throughput you provisioned on gp3, and the instance type's EBS bandwidth limit | [Why is it slow? Disk I/O](23-playbook-slow-system.md#5-disk-io), [Disk performance](01-storage-disk.md#3-disk-performance-io) |
| Slow network | `mtr -rwc 50 HOST` for loss per hop, `iperf3 -c HOST` for throughput, `ethtool eno1` for speed and duplex, then the error counters on the switch port | The same mtr and iperf3, then `ethtool -S ens5` for the ENA allowance counters (`bw_in_allowance_exceeded`, `pps_allowance_exceeded`), the instance type's baseline bandwidth, cross-AZ hops and the NAT gateway | [Network speed](24-playbook-network-speed.md), [AWS limits, ENA and NAT](24-playbook-network-speed.md#9-aws-instance-limits-ena-azs-and-nat) |
| DNS failure | `resolvectl status` to see which server the host asks, then `dig @192.0.2.53 app.example.com` against your BIND or Unbound server, and that server's logs | `dig app.example.com` from the instance, which asks the VPC resolver at base + 2 (169.254.169.253 also works); then check the private hosted zone is associated with this VPC, the VPC's DNS attributes and any Resolver rules | [DNS decision tree](08-dns.md#decision-tree), [Site down: DNS scenarios](25-playbook-site-down.md#4-dns-scenarios), [Route 53 records not resolving](50-problems-cloud-iac-proxmox.md#23-route-53-has-the-records-domain-doesnt-resolve) |
| Certificate expired | `curl -svI https://app.example.com` stops at `certificate has expired`; add `-k` (`curl -svkI`) to see the `expire date` line, or run `echo | openssl s_client -connect app.example.com:443 -servername app.example.com 2>/dev/null | openssl x509 -noout -enddate`; then find who renews it: Traefik's ACME log for public names, your private CA for Harbor and internal names | `aws acm describe-certificate --certificate-arn CERT_ARN --query 'Certificate.[Status,NotAfter,RenewalEligibility]'`; ACM renews by itself only while the DNS validation record exists and the certificate is in use | [Site down: TLS scenarios](25-playbook-site-down.md#6-tls-scenarios), [TLS with openssl](18-web-http-tls.md#3-tls-certificates-openssl) |
| Need to restore a backup | List what you have first: `restic -r REPO snapshots`, or the datastore content in Proxmox Backup Server; restore into a scratch VM or a new path, never straight over live data | `aws backup list-recovery-points-by-backup-vault --backup-vault-name VAULT`, `aws ec2 describe-snapshots --owner-ids self`, or an RDS point-in-time restore to a new instance; restore beside production, then switch | [Backups and restores](51-problems-databases-storage-backup.md#5-backups-and-restores), [Disaster recovery](39-learn-senior-architecture.md#5-disaster-recovery) |
| CPU steal or a noisy neighbour | In the VM, `vmstat 1 5` (the `st` column) or `mpstat 1 5` (`%steal`); then on the Proxmox host compare total vCPUs with physical cores and find the busiest VMs | The same `st` column; on burstable T instances, CloudWatch `CPUCreditBalance` at zero looks like a slow server, so move to a non-burstable type or unlimited mode | [Slow VM on a busy hypervisor](23-playbook-slow-system.md#13-scenario-slow-vm-on-a-busy-hypervisor), [Instance types, credits and steal](36-learn-cloud-aws.md#instance-types-credits-and-steal) |
| Machine won't boot | The console shows GRUB, fsck prompts and initramfs shells: Proxmox noVNC or `qm terminal VMID` (needs a serial port on the VM), or the out-of-band console for bare metal | `aws ec2 get-console-output --instance-id INSTANCE_ID --latest --output text`, a screenshot with `aws ec2 get-console-screenshot`, or the EC2 Serial Console; the fix is often to attach the root volume to a rescue instance | [Boot and GRUB](13-kernel-system.md#5-boot-grub), [Boot and recovery](27-learn-linux.md#7-the-boot-process-and-recovery), [Status checks and serial console](36-learn-cloud-aws.md#status-checks-and-serial-console) |
| Permission denied | `id ops`, `namei -l /path/to/file` (every directory on the path), `sudo -l -U ops`; for directory users `getent group GROUP`; AppArmor denials in `journalctl -k` | For an API error: `aws sts get-caller-identity` (who am I really), then `aws sts decode-authorization-message --encoded-message MESSAGE` when the error carries one, and CloudTrail for the denied call; inside EC2 it is the same Linux check as on-prem | [Permission denied decision tree](10-users-permissions-security.md#decision-tree-permission-denied), [AccessDenied from IAM, S3 or KMS](50-problems-cloud-iac-proxmox.md#12-accessdenied-from-iam-s3-or-kms) |
| Sudden cost spike | There is no surprise bill: the spike arrives as capacity, such as a storage pool filling, a licence threshold crossed or a support renewal; check `pvesm status` and the growth trend in Grafana | Console: Cost Explorer grouped by service, then by usage type; or `aws ce get-cost-and-usage --time-period Start=2026-09-01,End=2026-10-01 --granularity DAILY --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE`. Usual suspects: NAT gateway data, public IPv4, idle volumes and snapshots, log retention | [Surprise bill](50-problems-cloud-iac-proxmox.md#25-surprise-bill-nat-public-ipv4-and-leftovers), [Cost and FinOps](36-learn-cloud-aws.md#12-cost-and-finops) |
| Security alert | Open the alert in the Wazuh dashboard (rule, agent, full log), then on the host `last -aiF`, `journalctl -u ssh --since "2 hours ago"` and `sudo ss -tnp` for unexpected connections; `sudo cscli alerts list` where CrowdSec runs | Console: GuardDuty → Findings (type, resource, actor), then what that identity did: `aws cloudtrail lookup-events --lookup-attributes AttributeKey=AccessKeyId,AttributeValue=ACCESS_KEY_ID`; deactivate a leaked key first and investigate second | [Wazuh & security tools](48-wazuh-and-security-tools.md), [Security incident response](37-learn-security-devsecops.md#13-security-incident-response), [Cloud security incidents](36-learn-cloud-aws.md#cloud-security-incidents) |
| IP addresses exhausted | The DHCP scope or IPAM for that VLAN (the leases on the DHCP server or router) and `ip neigh` for who is on the segment; also Docker's default address pools clashing with office ranges (`docker network ls`, then `docker network inspect NETWORK`) | `aws ec2 describe-subnets --query 'Subnets[].[SubnetId,CidrBlock,AvailableIpAddressCount]' --output table`; AWS keeps 5 addresses in every subnet, and on EKS the VPC CNI gives every pod a VPC address, so add a secondary CIDR or use prefix delegation | [IP addressing and subnetting](28-learn-networking.md#3-ip-addressing-cidr-and-subnetting), [CIDR planning and subnets](36-learn-cloud-aws.md#cidr-planning-and-subnets) |
| Clock drift | `chronyc tracking` and `chronyc sources -v`; is your NTP server reachable on UDP 123 through the firewall, and did the VM's clock jump after a migration or a resume? | `chronyc sources -v` (or `timedatectl timesync-status` on images that use systemd-timesyncd) should point at 169.254.169.123, the Amazon Time Sync Service; AWS rejects signed API calls when the clock is off by more than a few minutes (`RequestTimeTooSkewed` from S3, `Signature expired` from most other APIs) | [Time: AWS specifics](12-time-ntp.md#5-aws-specifics), [Time: on-prem specifics](12-time-ntp.md#6-on-prem-specifics) |
| Hardware failure | `sudo dmesg -T` (Ubuntu restricts the kernel log to root) for I/O and machine-check errors, `sudo smartctl -H /dev/sda`, `cat /proc/mdstat` and the server's event log over IPMI (`sudo ipmitool sel elist`); then the spare part or the vendor ticket | There is no hardware to inspect: a failed system status check or a scheduled event (`aws ec2 describe-instance-status --instance-ids INSTANCE_ID --query 'InstanceStatuses[].Events'`) means stop and start the instance so it moves to a healthy host (instance-store data is lost); the AWS Health Dashboard covers wider problems | [Hardware health](13-kernel-system.md#6-hardware-health-on-premise), [Physical disk health](01-storage-disk.md#7-physical-disk-health-on-premise-and-detectable-in-dmesg-anywhere), [EC2 instance health](16-aws-cloud.md#3-ec2-instance-health) |
| No internet from a private subnet | `ip route` for the default gateway, `curl -sv https://example.com`, `printenv HTTPS_PROXY` for a forgotten proxy, then the NAT and egress rules on the edge firewall | The subnet's route table needs 0.0.0.0/0 to a NAT gateway that sits in a public subnet: `aws ec2 describe-route-tables --filters Name=association.subnet-id,Values=SUBNET_ID` (no result means the subnet uses the VPC's main route table); then the NAT gateway's state and the NACL's ephemeral ports. For AWS APIs only, a VPC endpoint avoids the NAT | [Private subnet can't reach the internet](50-problems-cloud-iac-proxmox.md#21-private-subnet-cant-reach-the-internet), [Route tables, IGW and NAT](36-learn-cloud-aws.md#route-tables-igw-and-nat), [NAT](28-learn-networking.md#5-nat-snat-masquerade-and-dnat) |
| Port already in use | `sudo ss -ltnp 'sport = :443'` names the process, then its unit and config; Apache holding 443 before your move to 81/444 is the classic case | The same `ss` command inside EC2, because the OS is still yours; on the AWS side a port problem is usually a listener or target group on the wrong port: `aws elbv2 describe-target-groups --query 'TargetGroups[].[TargetGroupName,Port,HealthCheckPort]'` | [Bind: address already in use](22-playbook-ports-inventory.md#13-scenario-bind-address-already-in-use), [Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md) |
| 502 or 503 at the front door | The proxy's log first (Traefik under Dokploy: `docker logs --since 10m dokploy-traefik`), then the backend directly, for example `curl -sv http://127.0.0.1:81/` for Apache on port 81 | `aws elbv2 describe-target-health --target-group-arn TG_ARN`: the reason code says why each target is unhealthy; then the ALB access log, then the instance's own proxy logs as on-prem | [Site down: 502, 503, 504](25-playbook-site-down.md#7-proxy-error-scenarios-502-503-504), [ALB returns 502, 503 or 504](50-problems-cloud-iac-proxmox.md#24-alb-returns-502-503-or-504) |
| Out of memory, processes killed | `journalctl -k --since today -g 'killed process'` and `free -h`; on a Proxmox host with ZFS, check how much RAM the ARC holds before you blame a VM | The same inside the instance; memory is not an EC2 metric by default, so without the CloudWatch agent (`mem_used_percent`) the console shows nothing; on ECS the stopped reason reads `OutOfMemoryError: Container killed due to memory usage` | [Memory pressure](23-playbook-slow-system.md#4-memory-pressure), [ZFS ARC and OOM kills](50-problems-cloud-iac-proxmox.md#83-host-uses-all-ram-zfs-arc-and-oom-kills) |

Two habits make the table work. On AWS, run `aws sts get-caller-identity` and check the region before you trust any "not found" or "access denied": a lot of cloud confusion is simply the wrong account or the wrong region. On-prem, ask "what changed, and what is physically near it?": a firmware update, a moved cable or a neighbour VM on the same host explains many incidents that look like application bugs.

---

## 3. Equivalents: on-prem and AWS

Almost every building block you run has an AWS counterpart. The last column is the part that matters during an incident: the evidence you look at moves, and some on-prem tricks stop working. The deeper mapping, with the places where it breaks (keepalived, source/destination checks, packet capture, cloud-init and netplan), is in [On-prem to AWS mapping](36-learn-cloud-aws.md#on-prem-to-aws-mapping).

| Component | 🏢 On-prem / self-hosted | ☁️ AWS | What changes when you troubleshoot |
|---|---|---|---|
| Virtual machines | Proxmox VE, VMware vSphere, KVM with libvirt | EC2 | On-prem you can look at the host (load, storage latency, overcommit); on AWS you see status checks, instance limits and CloudWatch, and the fix for a sick host is stop and start |
| Golden images | VM templates with cloud-init, Packer | AMIs, EC2 Image Builder, Packer | Is the template current and patched? AMIs are regional, and cloud-init owns netplan in both places |
| Self-hosted PaaS and container services | Dokploy (Traefik on Docker Swarm), Coolify | ECS on Fargate or EC2 | Swarm task errors and Traefik logs become ECS stopped reasons and target health; on Fargate there is no host to log in to |
| Kubernetes | kubeadm, k3s, RKE2 | EKS | On-prem you own etcd, control-plane certificates and upgrades; on EKS AWS does, and the new problems are VPC CNI address exhaustion, IAM for pods and access entries |
| Block storage | LVM, mdadm RAID, ZFS, iSCSI or Fibre Channel SAN, Ceph RBD | EBS | SMART, RAID rebuilds and controller cache become provisioned IOPS and throughput, burst credits and the instance's EBS bandwidth; an EBS volume lives in one AZ |
| File storage | NFS server, Samba, a NAS | EFS (NFS v4.1), FSx | Exports and UID mapping become mount targets per AZ, security groups on port 2049 and throughput modes |
| Object storage | MinIO, Ceph RGW (S3-compatible) | S3 | Path-style URLs, your private CA, clock skew and the proxy in front become bucket policies, Block Public Access, KMS and VPC endpoints |
| Networks and segments | VLANs, subnets on switches, Linux bridges such as vmbr0 | VPC and subnets (each subnet in one AZ) | Broadcast, ARP and VRRP work on-prem; in a VPC, AWS answers ARP and a floating IP has to be moved by an API call |
| Routing and the edge | Routers, L3 switches, pfSense or OPNsense, the ISP uplink | Route tables, internet gateway, NAT gateway, Transit Gateway | `ip route` and traceroute on a router you can log in to become route tables as API objects; a NAT gateway lives in one AZ and is billed per GB |
| Firewalls | UFW or nftables on hosts, the edge firewall | Security groups (stateful, per network interface), NACLs (stateless, per subnet), plus UFW inside the instance | Two layers become three; NACLs need the ephemeral return ports; ports published by Docker bypass UFW in both places |
| Load balancing and reverse proxy | Traefik, HAProxy, Nginx, Apache, a keepalived virtual IP | ALB for HTTP, NLB for TCP and UDP, often with Traefik or Nginx still behind them | Proxy access logs and a curl to the backend become target health reason codes, ALB access logs and idle timeouts |
| DNS | BIND, Unbound, dnsmasq, AD DNS | Route 53 public and private hosted zones, Route 53 Resolver | Zone files and resolver logs become hosted-zone association with the VPC, the resolver at VPC base + 2 and Resolver rules for hybrid names |
| TLS certificates | Let's Encrypt through Traefik's ACME, your private CA (Harbor), step-ca | ACM for public certificates on AWS services, AWS Private CA | Renewal logs and trust stores become ACM's DNS validation record; ACM certificates attach to services such as ALB and CloudFront |
| VPN and private links | WireGuard, OpenVPN, strongSwan IPsec | Site-to-Site VPN (two tunnels per connection), Client VPN, Direct Connect | One tunnel you configured becomes two AWS endpoints, with BGP (or static routes); MTU and MSS clamping matter on both |
| Identity for people | Active Directory, LDAP or FreeIPA, Keycloak, Authentik | IAM Identity Center federated with your identity provider | Group membership and sudo rules become permission sets, policy evaluation and session expiry |
| Identity for machines | SSH keys, service accounts, Vault AppRole | IAM roles: instance profiles, GitLab OIDC roles, EKS Pod Identity | Key files and tokens become "Unable to locate credentials", IMDSv2 hop limits and role trust policies |
| Secrets | HashiCorp Vault, OpenBao, Ansible Vault, GitLab CI variables | Secrets Manager, SSM Parameter Store, KMS | A sealed Vault or a missing Vault policy becomes IAM and the KMS key policy both having to allow the read |
| Container registry | Harbor with your private CA, the GitLab registry | ECR | `x509: certificate signed by unknown authority` becomes 12-hour login tokens and repository policies |
| CI/CD runners | GitLab Runner on a VM (shell or Docker executor) | GitLab Runner on EC2 (optionally autoscaling), CodeBuild | Runner DNS, Docker-in-Docker and your CA become OIDC role assumption, instance profiles and VPC egress |
| Provisioning and configuration | Ansible, Terraform or OpenTofu with a Proxmox provider | Terraform or OpenTofu with the AWS provider, CloudFormation, SSM State Manager | The same tools with a different blast radius: state locks and drift in both places, and on AWS also API throttling and quotas |
| Remote and console access | SSH through a VPN or bastion, IPMI, iDRAC or iLO, the Proxmox console | SSM Session Manager, EC2 Instance Connect, EC2 Serial Console | An out-of-band network and BMC passwords become IAM permissions and an SSM agent that must be online |
| Metrics and alerting | Prometheus, node_exporter, Alertmanager, Grafana, Zabbix | CloudWatch metrics and alarms, Amazon Managed Service for Prometheus, Amazon Managed Grafana | Scrape targets and exporters become metric namespaces; memory and disk metrics need the CloudWatch agent |
| Logs | Loki with Alloy, ELK or OpenSearch, rsyslog, journald | CloudWatch Logs, Amazon OpenSearch Service, S3 with Athena | Agent and label problems in both places; CloudWatch log groups keep data forever unless you set a retention |
| Audit trail | auditd, Wazuh file integrity monitoring, GitLab audit events, change tickets | CloudTrail, AWS Config | "Who changed it?" means searching several systems on-prem, and one CloudTrail query on AWS |
| Security monitoring | Wazuh, CrowdSec, Fail2ban, Trivy | GuardDuty, Security Hub, Inspector, plus Wazuh agents on EC2 | You write the rules and read the alerts on-prem; on AWS the findings are managed but still need routing to a person |
| Backups | Proxmox Backup Server, restic, Borg, pgBackRest, Velero | AWS Backup, EBS and RDS snapshots, S3 versioning and Object Lock | Datastore space and garbage collection become retention rules, vault locks and copies out of the account or region; test restores in both |
| Time | chrony against your NTP servers or the AD domain controllers | Amazon Time Sync Service at 169.254.169.123 | A firewalled UDP 123 and VM clock jumps become a chrony.conf that a template replaced |
| Hardware and facility | IPMI, iDRAC, iLO, PDUs, a UPS watched by NUT, spare parts | Nothing to manage: status checks, scheduled events, the AWS Health Dashboard | SEL logs, SMART and the spares shelf become stop and start, and a support case |
| Cost tooling | Asset register, power and licence costs, capacity reports, OpenCost for Kubernetes | Cost Explorer, Budgets, Cost Anomaly Detection, Data Exports, Compute Optimizer | Cost is fixed until capacity runs out on-prem; on AWS it is a live signal you alert on like CPU |

Rule of thumb: the closer a component is to the hardware, the more its troubleshooting changes; the closer it is to your application, the more stays the same. Apache logs, Traefik routers, Prometheus queries and Ansible roles read the same on a Proxmox VM and on EC2.

---

## 4. On-premise path, fresher to senior

This section is the on-premise path. Pick 🏢 On-prem or Both in the top bar to see it.

<div class="env" data-env="onprem" markdown="1">

Each stage lists what to learn and practise with the handbook in order, the KodeKloud courses, a homelab lab and what good looks like at that stage. The labs grow from one old PC to a small data centre on your desk. KodeKloud has no Proxmox, Ceph, VMware or data-centre course, so for those the handbook modules and the [Proxmox VE documentation](https://pve.proxmox.com/pve-docs/) fill the gap.

### On-prem Fresher · L0 Foundations

**Learn and practise, in order:**

1. [Linux sections 1–3](27-learn-linux.md#1-shell-basics-and-the-filesystem-hierarchy): the shell, the filesystem, permissions, users and sudo.
2. [Linux sections 4–6](27-learn-linux.md#4-processes-signals-and-jobs): processes, packages, systemd and journald, with [Services & systemd](07-services-systemd.md) and [Logs & journal](06-logs-journal.md) open as references.
3. [Storage and filesystems](27-learn-linux.md#8-storage-and-filesystems): partitions, mounts and LVM, then the [Storage reference](01-storage-disk.md).
4. [Networking sections 1–3](28-learn-networking.md#1-layers-and-the-tools-that-test-them): layers, Ethernet and VLANs, IP addressing and subnetting.
5. [SSH](27-learn-linux.md#10-ssh) with keys, and the [SSH reference](09-ssh-remote-access.md).
6. [Git](33-learn-cicd-iac-sre.md#1-git) for your scripts and config files.
7. The physical basics, by shadowing a senior in the server room: rack units, power distribution units, patch panels, switch ports, cable labels, and why nobody unplugs anything without a ticket.

**KodeKloud:** [DevOps Pre-Requisite Course](https://kodekloud.com/courses/devops-pre-requisite-course) (Networking Basics, Web Server, SSL & TLS Basics) → [Learning Linux Basics Course & Labs](https://kodekloud.com/courses/the-linux-basics-course) → [Shell Scripts for Beginners](https://kodekloud.com/courses/shell-scripts-for-beginners) → [GIT for Beginners](https://kodekloud.com/courses/git-for-beginners). When your lab is not at hand, practise on the free [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu).

**Homelab lab:** VirtualBox on your laptop, or an old PC with Ubuntu Server 24.04 LTS. Build one server by hand: the user ops with sudo and key-only SSH, UFW allowing 22 and 80, Apache with two name-based vhosts, and a nightly cron job that archives /etc to a second disk. Take a snapshot before every change. Then break it twice on purpose (fill the disk, stop Apache) and fix it from the logs alone.

**What good looks like:** you do a defined task on one server correctly, with review. You know where each service keeps its config and logs. You never run a command you cannot explain on a shared server, and you write down what you did. You can find a server in the rack by its label and say which switch port it uses, from the documentation or by asking the network team.

**Exit check:** the [Fresher skills checklist](40-career-ladder.md#fresher-skills-checklist) and the [Linux self-check](27-learn-linux.md#18-self-check-exit-test).

### On-prem Junior · L1 Operator

**Learn and practise, in order:**

1. [Who owns this port?](22-playbook-ports-inventory.md): port → PID → unit → config → logs, and the read-only inventory script.
2. [Web servers & proxies](29-learn-webservers-proxies.md): Apache vhosts, Nginx, and Traefik basics.
3. Your own incident end to end: [Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md), then [Apache moved to 81 and 444](35-deployment-patterns.md#1-your-fix-apache-moved-to-81-and-444) and how to finish the job with Traefik routes.
4. [Docker](30-learn-docker.md) on one host, then [Dokploy in 10 minutes](45-dokploy-and-self-hosted-paas.md#1-dokploy-in-10-minutes).
5. Internal DNS, time and TLS: [DNS](08-dns.md), [Time on-prem](12-time-ntp.md#6-on-prem-specifics) and [Web, HTTP & TLS](18-web-http-tls.md).
6. Virtual machines on Proxmox: templates, snapshots, backups and the enterprise repository trap, in [Proxmox VE problems](50-problems-cloud-iac-proxmox.md#7-proxmox-ve-repositories-host-network-and-cluster).
7. Patching in a maintenance window with a rollback plan: [Packages](11-packages.md) and [Runbooks others can follow](39-learn-senior-architecture.md#runbooks-others-can-follow-l1-junior).

**KodeKloud:** [Prep Course - Linux Foundation Certified System Administrator (LFCS)](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs) (Operations Deployment and Networking first) → [Linux Challenges](https://kodekloud.com/courses/linux-challenges) (free) → [Docker Training Course for the Absolute Beginner](https://kodekloud.com/courses/docker-training-course-for-the-absolute-beginner) (free) → [Nginx For Beginners](https://kodekloud.com/courses/nginx-for-beginners).

**Homelab lab:** install Proxmox VE on an old PC; 16 GB of RAM and any CPU with virtualisation support is enough to start. Make an Ubuntu cloud-init template and clone three VMs from it: web, dns and mon. On the web VM, replay your incident: Apache on 80 and 443 first, then move it to 81 and 444 and put Dokploy's Traefik on 80 and 443 in front of it. Add a Proxmox Backup Server VM (fine for a lab; real backups live on other hardware), back up the web VM, restore it under a new VMID and boot it without an IP conflict.

**What good looks like:** you own routine work end to end. You restart a service safely and read its logs, patch in a window, renew a certificate, add a VM from the template and keep the port inventory current. Your tickets stay closed, your runbooks are used by others, and you know which physical host every VM runs on.

**Exit check:** the [Junior skills checklist](40-career-ladder.md#junior-skills-checklist) and the [ports drills](22-playbook-ports-inventory.md#19-practice-drills-and-exit-test).

### On-prem Mid-level · L2 Troubleshooter

**Learn and practise, in order:**

1. The layered walk in [Site down](25-playbook-site-down.md) and the [60-second checklist](23-playbook-slow-system.md#2-the-60-second-checklist), until you can run both without notes.
2. Network depth: [VLANs](28-learn-networking.md#2-layer-2-ethernet-arp-switches-vlans), [routing](28-learn-networking.md#4-routing), [firewalls](28-learn-networking.md#7-firewalls-and-connection-tracking) and [packet capture](28-learn-networking.md#14-packet-capture-and-syscall-tracing), then [Network speed](24-playbook-network-speed.md).
3. [Traefik & reverse proxies](43-traefik-and-reverse-proxies.md) and the [Dokploy, Traefik and Swarm incidents](26-playbook-containers-k8s.md#7-dokploy-traefik-and-swarm).
4. CI/CD on your own servers: [GitLab runners and builds](47-cicd-gitlab-jenkins-actions-argocd.md#6-building-images-in-ci) and [Harbor with the private CA](47-cicd-gitlab-jenkins-actions-argocd.md#7-registries-harbor-and-the-private-ca).
5. Security you run yourself: [Wazuh & security tools](48-wazuh-and-security-tools.md) and [Linux hardening](37-learn-security-devsecops.md#2-linux-hardening).
6. Data that restores: [Backups that actually restore](38-learn-databases-ops.md#4-backups-that-actually-restore) and the [backup problem library](51-problems-databases-storage-backup.md#5-backups-and-restores).
7. [Ansible](33-learn-cicd-iac-sre.md#4-ansible) for repeatable fixes, with the [Ansible problems](50-problems-cloud-iac-proxmox.md#5-ansible-connections-become-and-hangs) next to it.
8. Hardware evidence: [Physical disk health](01-storage-disk.md#7-physical-disk-health-on-premise-and-detectable-in-dmesg-anywhere), [Software RAID](01-storage-disk.md#6-software-raid-mdadm-on-premise) and [Hardware health](13-kernel-system.md#6-hardware-health-on-premise).
9. Kubernetes on your own VMs, your current certification track: [Building a kubeadm homelab cluster](31-learn-kubernetes.md#3-building-a-kubeadm-homelab-cluster).

**KodeKloud:** [Demystifying DNS](https://kodekloud.com/courses/demystifying-dns) → [Docker Certified Associate](https://kodekloud.com/courses/docker-certified-associate-exam-course) (Engine, Networking and the Swarm section that Dokploy depends on; skip the Enterprise sections) → [GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines](https://kodekloud.com/courses/gitlab-ci-cd) (Self-Managed Runners) → [Ansible Basics Course](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course) → [Certified Kubernetes Administrator (CKA)](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator).

**Homelab lab:** grow the Proxmox lab into a small company. Make the bridge VLAN-aware with two VLANs (servers and management), add an OPNsense or pfSense VM as the router and firewall between them, run Unbound or BIND for an internal zone, and add GitLab CE with a runner, Harbor with a certificate from your own CA, and a Wazuh all-in-one VM with agents on every VM. GitLab, Harbor and Wazuh each want several GB of RAM, so with less than 32 GB run them in turn. Then break one layer at a time (a wrong VLAN tag, a dead DNS forwarder, an expired CA, a full runner disk, MTU 1400 on one hop) and fix each with the matching playbook under a timer.

**What good looks like:** you name the broken layer with evidence (a capture, a log line, a metric) before anyone touches a config. You lead incidents on your own systems and write the postmortem. You own monitoring and backups, and you have restored from them this quarter. You read the network diagram and the firewall rules and spot the gap, and you can tell a failing disk from a slow one and plan the swap.

**Exit check:** the [Mid-level skills checklist](40-career-ladder.md#mid-level-skills-checklist) and the [Site down exit test](25-playbook-site-down.md#14-self-check-and-exit-test).

### On-prem Senior · L3 Platform

**Learn and practise, in order:**

1. Kubernetes as a platform you run: [Cluster maintenance](31-learn-kubernetes.md#19-cluster-maintenance) (etcd backups, upgrades), [Kubernetes storage](31-learn-kubernetes.md#11-storage) and [Kubernetes data and DR](51-problems-databases-storage-backup.md#9-kubernetes-data-and-disaster-recovery).
2. Proxmox as a platform: clusters and quorum, Ceph or ZFS, Proxmox Backup Server, in [Proxmox VMs, storage and backups](50-problems-cloud-iac-proxmox.md#8-proxmox-ve-vms-storage-and-backups) and [Cluster lost quorum](50-problems-cloud-iac-proxmox.md#74-cluster-lost-quorum).
3. Everything as code: [Terraform](33-learn-cicd-iac-sre.md#5-terraform) with a Proxmox provider, Ansible roles and GitLab CI applying both; the traps are in [Terraform and OpenTofu problems](50-problems-cloud-iac-proxmox.md#3-terraform-and-opentofu-init-backends-and-state).
4. Observability you own: [Prometheus](32-learn-performance-observability.md#11-prometheus), [Alertmanager](32-learn-performance-observability.md#12-alertmanager-and-alert-rules), [Grafana](32-learn-performance-observability.md#13-grafana), [Logs and tracing](32-learn-performance-observability.md#14-logs-and-tracing) and the [Observability stack problems](49-observability-stack-problems.md).
5. High availability on your own hardware: [Single points of failure](39-learn-senior-architecture.md#single-points-of-failure-l1-junior) and the [On-prem HA platform](39-learn-senior-architecture.md#on-prem-ha-platform-l3-senior).
6. [Capacity planning](39-learn-senior-architecture.md#capacity-planning-l3-senior) and the [On-prem cost model](39-learn-senior-architecture.md#on-prem-cost-model-l3-senior).
7. [Disaster recovery](39-learn-senior-architecture.md#5-disaster-recovery): backup strategy, RPO and RTO, DR tiers.
8. Change windows and migrations: [Change management and CAB-lite](39-learn-senior-architecture.md#change-management-and-cab-lite-l2-mid) and [Apache to Dokploy, the senior way](39-learn-senior-architecture.md#apache-to-dokploy-the-senior-way-l3-senior).

**KodeKloud:** finish the [CKA](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator), then [Kubernetes Networking Deep Dive](https://kodekloud.com/courses/kubernetes-networking) → [Helm for Beginners](https://kodekloud.com/courses/helm-for-beginners) → [Prep Course - Prometheus Certified Associate (PCA)](https://kodekloud.com/courses/prometheus-certified-associate-pca) → [Grafana Loki](https://kodekloud.com/courses/grafana-loki) → [Terraform Basics Training Course](https://kodekloud.com/courses/terraform-basics-training-course) (the state and module lessons carry over to the Proxmox provider). For clusters, quorum and HA, use the Proxmox [Cluster Manager](https://pve.proxmox.com/wiki/Cluster_Manager) documentation.

**Homelab lab:** three small nodes (mini PCs, or three nested Proxmox VMs on one large host) in a Proxmox cluster with quorum, replicated storage (ZFS replication or a small Ceph) and Proxmox HA for one VM. On top, a kubeadm cluster built by Terraform from your cloud-init template and configured by Ansible, with GitLab CI applying both. Drills: power off one node and watch HA move the VM; restore etcd from a snapshot; upgrade Kubernetes by one minor version with a rollback plan; restore a whole VM from Proxmox Backup Server onto another node and time it.

**What good looks like:** you build platforms other teams use, and you design incidents out instead of fixing them again. At this stage that includes the data-centre basics:

- **Capacity and hardware lifecycle:** a capacity report per cluster (CPU, RAM, storage, growth per month, the date you run out), warranty and end-of-life dates for every server, a refresh plan and budget request filed before you run out, and spare disks and power supplies on the shelf.
- **A DR site:** a second room, a second building, or AWS as a pilot light, with a tested failover and a measured RTO and RPO.
- **Change windows:** every production change has a plan, a rollback and a communication template, and nothing changes outside the window without the emergency process.
- **Power:** dual power supplies on separate PDUs fed by separate circuits (A and B feeds), a UPS sized for a clean shutdown, and NUT (Network UPS Tools) shutting hosts down in the right order when the battery runs low.
- **Out-of-band management:** IPMI, iDRAC or iLO on a separate management VLAN that is unreachable from the internet, credentials in the password vault, and a remote console you have actually tested.
- **The room:** temperature alerts, labelled cables, a rack diagram that matches reality, and a list of who may enter.

**Exit check:** the [Senior skills checklist](40-career-ladder.md#senior-skills-checklist) and the [Senior checks](39-learn-senior-architecture.md#senior-checks) in the architecture module.

### On-prem Senior/Lead · L4 SRE

**Learn and practise, in order:**

1. [SLIs, SLOs and error budgets](32-learn-performance-observability.md#15-slis-slos-and-error-budgets) for the platforms you own.
2. [Incident command](39-learn-senior-architecture.md#incident-command-l4-leadsre) and [On-call design](39-learn-senior-architecture.md#on-call-design-l4-leadsre).
3. [DR drills and game days](39-learn-senior-architecture.md#dr-drills-and-game-days-l4-leadsre), including [Exercise 8: building power off for 8 hours](39-learn-senior-architecture.md#exercise-8-building-power-off-for-8-hours-l4-leadsre).
4. [Compliance as evidence](39-learn-senior-architecture.md#compliance-as-evidence-l4-leadsre) and [Compliance basics for engineers](37-learn-security-devsecops.md#14-compliance-basics-for-engineers).
5. Budget and procurement: the multi-year capex plan, support contracts and [Build vs buy](39-learn-senior-architecture.md#build-vs-buy-l4-leadsre).
6. What stays on-prem and what moves: section 6 of this page and [Migration strategy](39-learn-senior-architecture.md#9-migration-strategy).
7. Growing people: [Mentoring juniors](39-learn-senior-architecture.md#mentoring-juniors-l3-senior) and the [Lead, Staff and SRE stage](40-career-ladder.md#6-lead-staff-and-sre-l4).

**KodeKloud:** [Fundamentals of SRE](https://kodekloud.com/courses/fundamentals-of-sre) (Incident Management, Change Management for Reliability) and, if Kubernetes is your platform, [Certified Kubernetes Security Specialist (CKS)](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks), whose System Hardening part applies straight to your Ubuntu hosts. Leadership is not a KodeKloud topic, so pair it with the [Google SRE books](https://sre.google/books/).

**Homelab lab:** a game day on the whole lab with a colleague as the person who breaks things. They cause a fault you don't know about (a node powered off, a full backup datastore, a revoked CA, a DNS forwarding loop) while you run the incident as commander, with a timeline and status updates. Afterwards, write the blameless postmortem and remove one class of problem for good.

**What good looks like:** the on-prem platform has SLOs, an on-call rota people can sustain, a DR plan tested at least once a year with measured numbers, an audit trail auditors accept, and a multi-year capacity and budget plan that management approved. You can explain with a cost model why each workload is on-prem, in the cloud or in both, and juniors grow faster because of your runbooks and reviews.

**Exit check:** the [Lead and SRE checks](39-learn-senior-architecture.md#lead-and-sre-checks) and the [Lead skills checklist](40-career-ladder.md#lead-skills-checklist).

</div>

---

## 5. Cloud path, fresher to senior

This section is the AWS path. Pick ☁️ Cloud or Both in the top bar to see it.

<div class="env" data-env="cloud" markdown="1">

Cloud work still sits on Linux and networking, so the first stage overlaps with the on-prem path. The difference starts the day you open an AWS account: every piece of infrastructure is an API call, authorised by IAM, logged by CloudTrail and billed by the second. Every lab below therefore starts with a budget alarm, and every lab is destroyed the same day. The full syllabus with exit tests is [Cloud & AWS](36-learn-cloud-aws.md); the certification order is in [Certification path](36-learn-cloud-aws.md#certification-path).

### Cloud Fresher · L0 Foundations

**Learn and practise, in order:**

1. Linux and networking basics first, because AWS is Linux and networking with an API on top: [Linux sections 1–6](27-learn-linux.md#1-shell-basics-and-the-filesystem-hierarchy) and [Networking sections 1–3](28-learn-networking.md#1-layers-and-the-tools-that-test-them).
2. [Sandbox account first](36-learn-cloud-aws.md#sandbox-account-first): lock the root user, use IAM Identity Center every day, and create a budget alarm before any resource.
3. [Cloud concepts](36-learn-cloud-aws.md#1-cloud-concepts): regions and AZs, shared responsibility, pricing models.
4. The identity habit before every session: [CLI identity and config sanity](16-aws-cloud.md#1-cli-identity-config-sanity-start-every-session-here).
5. [Identities and policies](36-learn-cloud-aws.md#identities-and-policies): users, groups, roles and the policy document.
6. One EC2 instance and one S3 bucket from the CLI, then tear both down: [EC2 compute](36-learn-cloud-aws.md#4-ec2-compute) and [S3 access control](36-learn-cloud-aws.md#s3-access-control).

**KodeKloud:** [Crash Course: AWS Basics](https://kodekloud.com/courses/crash-course-aws-basics) (free) → [AWS Certified Cloud Practitioner (CLF-C02)](https://kodekloud.com/courses/aws-cloud-practitioner-clf-c02) only if you are new to IT or want a first badge, since every associate exam covers it. If Linux is new to you, take [Learning Linux Basics Course & Labs](https://kodekloud.com/courses/the-linux-basics-course) first. Practise in the [AWS Playground](https://kodekloud.com/cloud-playgrounds/aws), which keeps experiments off your own bill, and use [100 Days of Cloud](https://kodekloud.com/100-days-of-cloud) as a daily warm-up.

**Free-tier lab, budget alarm first:** in a personal account, create a monthly budget of a few dollars with alerts before you create anything else. AWS changed the Free Tier in July 2025, so check what your account has under Billing and Cost Management → Free Tier instead of trusting a blog post. Then launch one small Ubuntu instance in the default VPC, connect with SSM Session Manager instead of opening port 22, install Apache, copy a file to S3 from the instance using an instance role (no access keys), and delete everything the same evening. The next morning, check the bill shows nothing still running.

**What good looks like:** your sandbox is safe: root locked with MFA, no root access keys, a budget alarm, and no long-lived access keys on your laptop. You check the account and region before every command, you can explain regions, AZs and shared responsibility, and nothing you launch survives the evening by accident.

**Exit check:** the [Fresher exit test](36-learn-cloud-aws.md#fresher-exit-test) in Cloud & AWS.

### Cloud Junior · L1 Operator

**Learn and practise, in order:**

1. [VPC deep dive](36-learn-cloud-aws.md#3-vpc-deep-dive): CIDR planning, route tables, internet and NAT gateways, security groups and NACLs.
2. [EC2 compute](36-learn-cloud-aws.md#4-ec2-compute): AMIs and user data, [SSM Session Manager](36-learn-cloud-aws.md#ssm-session-manager) instead of SSH, EBS resizes and snapshots.
3. Apache behind an ALB, with a Route 53 record and an ACM certificate: [Load balancing and Route 53](36-learn-cloud-aws.md#6-load-balancing-and-route-53).
4. [CloudWatch metrics and alarms](36-learn-cloud-aws.md#cloudwatch-metrics-and-alarms) and [the CloudWatch agent](36-learn-cloud-aws.md#cloudwatch-logs-and-the-agent) for memory and disk.
5. [Reading the bill](36-learn-cloud-aws.md#reading-the-bill), and an owner tag on every resource.
6. [Terraform](33-learn-cicd-iac-sre.md#5-terraform) for everything you build, so every lab can be destroyed with one command.
7. The first AWS problems you will meet: [AWS access: SSH, IAM and credentials](50-problems-cloud-iac-proxmox.md#1-aws-access-ssh-iam-and-credentials), with the [AWS reference](16-aws-cloud.md) at hand.

**KodeKloud:** [AWS Networking Fundamentals](https://kodekloud.com/courses/aws-networking-fundamentals) → [Terraform Basics Training Course](https://kodekloud.com/courses/terraform-basics-training-course) (Terraform with AWS, Remote State) → [Terraform Challenges](https://kodekloud.com/courses/terraform-challenges) (free). For the exam most junior cloud adverts name, AWS Certified Solutions Architect – Associate (check the current catalog).

**Free-tier lab, budget alarm first:** in Terraform, build a VPC with two public and two private subnets across two AZs, an ALB in the public subnets, two small Ubuntu instances in the private subnets running Apache on port 81 as on your servers, SSM for access, a Route 53 record if you own a test domain, and a CloudWatch alarm on unhealthy targets. A NAT gateway is billed per hour and per GB, so create it only for the session, and run `terraform destroy` before bed.

**What good looks like:** you operate without the console as a crutch. Alarms reach you before users do, you resize a volume and restore a snapshot without help, every resource has an owner tag, nobody uses long-lived keys in your projects, and you can read last month's bill by service.

**Exit check:** the [Junior exit test](36-learn-cloud-aws.md#junior-exit-test) in Cloud & AWS.

### Cloud Mid-level · L2 Troubleshooter

**Learn and practise, in order:**

1. [Policy evaluation logic](36-learn-cloud-aws.md#policy-evaluation-logic) and [Debugging AccessDenied](36-learn-cloud-aws.md#debugging-accessdenied).
2. [Flow Logs and Reachability Analyzer](36-learn-cloud-aws.md#flow-logs-and-reachability-analyzer), then the [Drill: EC2 site times out](36-learn-cloud-aws.md#drill-ec2-site-times-out).
3. [Health checks and ALB errors](36-learn-cloud-aws.md#health-checks-and-alb-errors), then the [Drill: ALB returns 502 or 503](36-learn-cloud-aws.md#drill-alb-returns-502-or-503).
4. Instance internals: [IMDSv2](36-learn-cloud-aws.md#imdsv2), [EBS performance and snapshots](36-learn-cloud-aws.md#ebs-performance-and-snapshots), and [Status checks and serial console](36-learn-cloud-aws.md#status-checks-and-serial-console).
5. [Containers on AWS](36-learn-cloud-aws.md#8-containers-on-aws): ECR, ECS and Fargate, and EKS basics.
6. [RDS basics](36-learn-cloud-aws.md#7-rds-basics): Multi-AZ, read replicas and restore drills.
7. Pipelines and state: [GitLab CI to AWS with OIDC](36-learn-cloud-aws.md#gitlab-ci-to-aws-with-oidc) and [Terraform plans, drift and refactoring](50-problems-cloud-iac-proxmox.md#4-terraform-and-opentofu-plans-drift-and-refactoring).
8. The playbooks applied to a VPC: [Site down](25-playbook-site-down.md), [Network speed on AWS](24-playbook-network-speed.md#9-aws-instance-limits-ena-azs-and-nat) and [AWS networking, storage and cost problems](50-problems-cloud-iac-proxmox.md#2-aws-networking-storage-and-cost).

**KodeKloud:** [AWS Certified CloudOps Engineer - Associate](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate) (formerly SysOps Administrator; take its monitoring and networking domains first) and the [CKA](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator) if you have not done it, because EKS problems are Kubernetes problems first. [100 Days of Cloud](https://kodekloud.com/100-days-of-cloud) stays your morning rep.

**Free-tier lab, budget alarm first:** take the Junior lab and break it, one fault per session, then fix it from evidence only. Remove the private subnet's route to the NAT gateway; change the target group port from 81 to 80; delete the outbound rule of a security group; encrypt a bucket with a customer-managed KMS key your role may not use; set the IMDS hop limit to 1 and run the AWS CLI in a container. For each fault, write down which AWS signal named the cause: CloudTrail, Flow Logs, a reason code or a stopped reason.

**What good looks like:** you explain any failure with evidence from AWS's own signals instead of guessing. You never change production by clicking, because it is all in reviewed Terraform. You know your account's service quotas and which ones bite, and you have restored an RDS instance to a point in time this quarter.

**Exit check:** the [Mid-level exit test](36-learn-cloud-aws.md#mid-level-exit-test) in Cloud & AWS.

### Cloud Senior · L3 Platform

**Learn and practise, in order:**

1. [Organizations and SCPs](36-learn-cloud-aws.md#organizations-and-scps), with IAM Identity Center permission sets.
2. [Landing zones at scale](36-learn-cloud-aws.md#landing-zones-at-scale): account structure, central logging and security accounts, guardrails.
3. Network at scale: [CIDR planning and subnets](36-learn-cloud-aws.md#cidr-planning-and-subnets), [Peering and Transit Gateway](36-learn-cloud-aws.md#peering-and-transit-gateway) and [Hybrid connectivity](36-learn-cloud-aws.md#11-hybrid-connectivity).
4. [EKS and its quirks](36-learn-cloud-aws.md#eks-and-its-quirks).
5. Security as the platform owner: [Encryption and KMS](36-learn-cloud-aws.md#encryption-and-kms), [CloudTrail and Config](36-learn-cloud-aws.md#cloudtrail-and-config) and [Cloud security on AWS](37-learn-security-devsecops.md#10-cloud-security-on-aws).
6. [Auto Scaling and quotas](36-learn-cloud-aws.md#auto-scaling-and-quotas), with golden AMIs and instance refresh.
7. A design you can defend: the [AWS reference architecture](39-learn-senior-architecture.md#aws-reference-architecture-l3-senior) and [Golden paths](39-learn-senior-architecture.md#golden-paths-l3-senior).
8. Cost guardrails: [Rightsizing and commitments](36-learn-cloud-aws.md#rightsizing-and-commitments).

**KodeKloud:** [HashiCorp Certified: Terraform Associate 004](https://kodekloud.com/courses/hashicorp-certified-terraform-associate-004) → [Kubernetes Networking Deep Dive](https://kodekloud.com/courses/kubernetes-networking) (ingress and CNI concepts carry over to EKS) → AWS Certified DevOps Engineer – Professional (check the current catalog), only if your platform lives on AWS.

**Lab, budget alarm on every account:** AWS Organizations with three accounts (management, log archive, workload), an SCP that denies every region except yours, IAM Identity Center with two permission sets, an organisation trail in CloudTrail writing to the log-archive bucket, and GitLab CI deploying Terraform into the workload account through OIDC with no stored keys. The EKS control plane is billed per hour, so create the cluster in the evening and destroy it before bed.

**What good looks like:** teams get new accounts and VPCs from your templates rather than from tickets. Guardrails are code (SCPs, Config rules and a budget per account), there are no long-lived keys anywhere, the hybrid link to on-prem has two tunnels and monitored BGP, and you can explain the monthly bill per team using cost-allocation tags.

**Exit check:** the [Senior exit test](36-learn-cloud-aws.md#senior-exit-test) in Cloud & AWS.

### Cloud Senior/Lead · L4 SRE

**Learn and practise, in order:**

1. [Well-Architected pillars](36-learn-cloud-aws.md#well-architected-pillars): run a review of a real workload with the free AWS Well-Architected Tool and turn the findings into a plan.
2. DR strategy: [Designing for failure and DR](36-learn-cloud-aws.md#designing-for-failure-and-dr), [DR tiers](39-learn-senior-architecture.md#dr-tiers-l3-senior) and [Hybrid DR with AWS](39-learn-senior-architecture.md#hybrid-dr-with-aws-l4-leadsre).
3. FinOps as a practice: [Cloud FinOps](39-learn-senior-architecture.md#cloud-finops-l3-senior) and [Common bill surprises](36-learn-cloud-aws.md#common-bill-surprises).
4. [Cloud security incidents](36-learn-cloud-aws.md#cloud-security-incidents): leaked keys, public buckets, crypto-mining.
5. [SLO negotiation](39-learn-senior-architecture.md#slo-negotiation-l4-leadsre) and [DR drills and game days](39-learn-senior-architecture.md#dr-drills-and-game-days-l4-leadsre).
6. Quotas, capacity and the exit plan: what you do if a region, a service or the provider fails you, starting from [Capacity planning](39-learn-senior-architecture.md#capacity-planning-l3-senior).

**KodeKloud:** [Fundamentals of SRE](https://kodekloud.com/courses/fundamentals-of-sre). For architecture depth, AWS Certified Solutions Architect – Professional (check the current catalog), only if your role centres on AWS design. FinOps is not a KodeKloud topic; the FinOps Foundation's framework is the usual reference.

**Lab, budget alarm on every account:** a game day in the sandbox organisation. Restore the workload account's database and application into a second region from backups alone, with a stopwatch running. Then play a cost game: find and remove 30% of the lab's spend with Cost Explorer and Compute Optimizer. Write the first up as a postmortem and the second as a decision record.

**What good looks like:** every critical workload has an RTO and RPO that the business agreed and a drill has proved. A Well-Architected review happens before big launches, costs are reviewed monthly with each team against a unit metric (cost per customer or per deploy), security findings have owners and deadlines, and you can argue with numbers which workloads should come back on-prem.

**Exit check:** the [Lead and SRE exit test](36-learn-cloud-aws.md#lead-and-sre-exit-test) in Cloud & AWS.

</div>

---

## 6. Hybrid: running both

Most companies run hybrid for years: some workloads move, some stay, and the two halves must work as one system. This is where your on-prem experience and your AWS knowledge add up to more than either alone. The full treatment of the network part is [Hybrid connectivity](36-learn-cloud-aws.md#11-hybrid-connectivity); this section is the map.

### Connect the networks

- **Site-to-Site VPN first:** two IPsec tunnels per connection to two AWS endpoints, with BGP so failover between them is automatic. It is cheap and ready in an afternoon.
- **Direct Connect for steady bandwidth and latency:** weeks of lead time, and not encrypted by default, so run a VPN over it or use MACsec where your connection supports it.
- **WireGuard on a small EC2 instance** is a good lab link, not a production one; disable the instance's source/destination check so it can route.
- **One address plan before any tunnel:** your on-prem ranges, every VPC, Docker's default address pools (172.17.0.0/16 to 172.31.0.0/16, then 192.168.0.0/16) and the Kubernetes pod and service ranges must not overlap. The default VPC uses 172.31.0.0/16, which sits inside Docker's pool.
- **MTU:** IPsec overhead lowers the path MTU, so clamp the TCP MSS on the tunnel; see [VPNs, overlays and MTU](28-learn-networking.md#12-vpns-overlays-and-mtu).

### Resolve names both ways

On-prem servers cannot query the VPC resolver directly, and the VPC knows nothing about your internal zone. Route 53 Resolver endpoints bridge the two: an **inbound endpoint** gives on-prem DNS addresses inside the VPC to forward to, and an **outbound endpoint** with a forwarding rule sends VPC queries for your internal zone to 192.0.2.53. On an Unbound server on-prem, the forward looks like this (36 shows the BIND version):

```
# /etc/unbound/unbound.conf.d/aws.conf on the on-prem resolver
forward-zone:
    name: "aws.example.com."
    forward-addr: 10.20.16.10
    forward-addr: 10.20.48.10
```

Test both directions after every change: `dig app.aws.example.com @192.0.2.53` from an on-prem host, and `dig ci.corp.example.com` from an EC2 instance. If the second fails, check the forwarding rule is associated with that VPC and that the on-prem firewall lets the outbound endpoint's addresses reach port 53.

### Federate identity

- **People:** one identity provider (Active Directory, Keycloak or Entra ID) connected to IAM Identity Center with SAML for sign-in and SCIM or a scheduled sync for users and groups. Joiners and leavers are handled once, in one place.
- **On-prem machines calling AWS:** IAM Roles Anywhere exchanges an X.509 certificate from your private CA (the same CA that signs Harbor) for short-lived credentials, instead of access keys in files.
- **On-prem servers managed from AWS:** SSM hybrid activations register them as managed nodes (`mi-` IDs) for Run Command and Session Manager.
- **Pipelines:** GitLab CI reaches AWS through OIDC with no stored keys; see [GitLab CI to AWS with OIDC](36-learn-cloud-aws.md#gitlab-ci-to-aws-with-oidc).

### One toolchain everywhere

| Job | Tool on both sides | The hybrid detail |
|---|---|---|
| Provisioning | Terraform or OpenTofu | The AWS provider and a Proxmox provider in separate states, behind the same pipeline and review |
| Configuration | Ansible | One inventory: the `aws_ec2` dynamic inventory plugin plus static on-prem groups, running the same roles |
| CI/CD | GitLab CI | Runners on-prem and in AWS, tagged by what they can reach; OIDC for AWS credentials |
| Images | Harbor and ECR | Harbor replication rules push release images to ECR, so AWS pulls stay inside AWS |
| Security monitoring | Wazuh | Agents on EC2 report to the manager over the VPN (TCP 1514 and 1515), and Wazuh's AWS module reads CloudTrail and GuardDuty data from S3 |
| Metrics | Prometheus | One Prometheus per site, with federation or `remote_write` into one central store (Thanos, Mimir or Amazon Managed Service for Prometheus) and the same alert rules |
| Logs | Loki with Alloy | The same labels on both sides (env, site, host), so one query covers both |
| Backups | restic or PBS on-prem, AWS Backup in AWS | Each side is the other's offsite copy: on-prem backups to S3 with Object Lock, critical AWS data copied back on-prem |

### Data gravity

Data is the heaviest thing you own. Moving it costs time (bandwidth), money (AWS charges for data leaving it, while data coming in is generally free) and risk. So compute tends to follow the data: an application in AWS that queries a database on-prem pays the VPN round trip on every query and the egress charge on every result. Decide where each dataset's primary copy lives first, then place the compute next to it, and replicate for reads or for DR rather than for convenience.

### Migration strategies

AWS describes migration options as the "7 Rs". Most real migrations mix several of them, one application at a time; the senior skill is choosing per application, with the [strangler pattern](39-learn-senior-architecture.md#strangler-pattern-l3-senior) for anything you refactor. The full method is in [Migration strategy](39-learn-senior-architecture.md#9-migration-strategy).

| Strategy | What it means | An example from your estate | When it fits |
|---|---|---|---|
| Retire | Switch it off | An old Apache vhost nobody uses, found by the inventory in case 21 | Always check this first |
| Retain | Keep it where it is, for now | The Wazuh manager, the Proxmox cluster, data with residency rules | No business reason to move, or a dependency is not ready |
| Rehost (lift and shift) | The same server, now on EC2 | The Apache VM moved as it is, with AWS Application Migration Service or a rebuilt AMI | A deadline or a data-centre exit |
| Relocate | Move a whole virtualisation platform at once | A VMware estate moved to VMware-based hosting on AWS | Rare for a Proxmox shop |
| Replatform (lift, tinker and shift) | Small changes to use managed services | PostgreSQL on a VM becomes RDS; a Swarm service becomes an ECS service | Operations toil is the pain |
| Repurchase | Replace it with SaaS | Self-managed GitLab becomes GitLab.com | The tool is not what makes you different |
| Refactor or re-architect | Rebuild it for the cloud | A monolith split into services on EKS or serverless | Only with a strong business case; the most expensive option |

### When each environment wins

| Situation | Usually wins | Why |
|---|---|---|
| Steady, predictable load running 24/7 for years | On-prem, or cloud with commitments | Owned hardware is paid for once; the cloud bill never stops |
| Spiky, seasonal or unknown load | Cloud | You pay for the peak only while it lasts |
| A new product, a small team, speed matters most | Cloud | No hardware lead time; managed databases and load balancers |
| Strict data residency, or a regulator that forbids foreign providers | On-prem, or a local region where allowed | You can prove where the data is |
| Low latency to machines on a factory floor or in a hospital | On-prem or edge | Physics: the network path to a region is the bottleneck |
| Large, steady volumes of data leaving the system | On-prem | Egress is charged on every GB |
| Short projects, a month of GPUs, test environments | Cloud | Rent and return |
| Users spread around the world | Cloud | Regions and edge locations close to users |
| DR for an on-prem platform | Cloud, as a pilot light | A second data centre costs a lot; a pilot light costs little until you need it |
| No hardware skills, or nobody on site at 3 am | Cloud | Someone has to replace the failed disk |

Most honest answers end up "both": that is why this section exists.

---

## 7. Choosing for your career

### Where each skill set is in demand

On-prem and hybrid skills stay in demand wherever data, latency or regulation keep systems in-house:

- **Banking, insurance and payments:** regulators, data residency and core systems that stay in-house; usually hybrid.
- **Telecom:** network functions, edge sites and large private networks, often with Kubernetes on bare metal.
- **Government and defence:** sovereignty rules, and air-gapped or classified networks.
- **Manufacturing, energy and utilities:** OT networks, and plants that must keep running without the internet.
- **Healthcare and research:** patient-data rules, systems on site in hospitals, and HPC clusters.
- **Hosting providers, managed service providers and data-centre operators**, and companies that moved steady workloads back from the cloud to control cost.

Cloud-first skills dominate in **startups and SaaS companies**, e-commerce and media, consultancies that migrate customers to the cloud, and digital teams inside larger firms. Many senior job adverts ask for both: deep Linux, networking and Kubernetes, plus at least one cloud.

### What transfers between them

| Skill | On-prem form | Cloud form | How much transfers |
|---|---|---|---|
| Linux | Ubuntu on Proxmox VMs and bare metal | Ubuntu on EC2 and EKS nodes | All of it: it is the same OS |
| Networking | VLANs, routing, NAT, firewalls, DNS, TLS | VPCs, route tables, NAT gateways, security groups, Route 53, ACM | The concepts all transfer; the tools change |
| Containers and Kubernetes | Dokploy on Swarm, kubeadm | ECS, EKS | Most of it; the CKA counts on both sides |
| IaC and configuration | Terraform with a Proxmox provider, Ansible | Terraform with the AWS provider, Ansible | All of it: the same languages |
| CI/CD | GitLab CI, Harbor | GitLab CI, ECR | All of it |
| Observability | Prometheus, Grafana, Loki | CloudWatch, managed Prometheus and Grafana | The method fully, the tools partly |
| Security | Wazuh, hardening, a private CA | IAM, GuardDuty, KMS | The method fully; IAM's policy language is new |
| Troubleshooting method | The layered walk, the USE method | The same walk with different first commands | All of it, and it is the most valuable skill you have |
| Hardware, storage arrays, the facility | Daily work | Not needed | On-prem only |
| IAM policies, managed-service limits, billing models | Not needed | Daily work | Cloud only |

<div class="env" data-env="onprem" markdown="1">

### If you lean on-prem

Your proof is a platform that survives failure: a three-node cluster with tested backups, a DR drill with measured RTO and RPO, and a postmortem from a real incident such as your Apache 443 move. The certificates that count are the hands-on ones: the CKA first, the LFCS course for its content, and RHCSA only if your servers move to RHEL. Keep one cloud skill alive, the AWS fundamentals from section 5, because every on-prem estate ends up with a hybrid link and someone has to own it. Write up the homelab in a public repository; see [Building proof](40-career-ladder.md#10-building-proof).

</div>

<div class="env" data-env="cloud" markdown="1">

### If you lean cloud

Your proof is infrastructure as code that others can read: a Terraform repository for a multi-account sandbox, a GitLab OIDC pipeline, and a DR or cost game day written up as a postmortem. The certificates that count are one AWS associate exam (Solutions Architect or CloudOps), the Terraform Associate, and the DevOps Engineer – Professional later. Keep Linux and networking deep: the cloud engineers who stand out can debug the instance and the packet, not only the console. See [Certifications in order](40-career-ladder.md#certifications-in-order).

</div>

### Recommended order for you

You run on-prem every day and you already use AWS, so the best order uses your daily work as the main classroom and adds the cloud on top:

1. **Go deep on on-prem Linux and networking.** It is your job, so every incident is a lesson. Finish the Dokploy migration from [the case](21-case-apache-443-dokploy.md) and use it as proof.
2. **Pass the CKA.** It is your current track, and Kubernetes is the same on kubeadm and on EKS, so it counts on both paths.
3. **Learn AWS fundamentals in a safe sandbox:** the Cloud Fresher and Junior stages in section 5, with AWS Networking Fundamentals and Terraform Basics, and every lab written in Terraform.
4. **Take one AWS associate exam** after the CKA: Solutions Architect if you are job-hunting, CloudOps if you operate AWS day to day.
5. **Build a hybrid project:** back up the on-prem stack to S3 with Object Lock, and build a pilot-light DR copy of one application in AWS behind a Route 53 failover record. Next to your Apache 81/444 to Traefik migration, it is the strongest senior-interview story you can tell.

The [Career ladder](40-career-ladder.md#certifications-in-order) and the [Roadmap](34-roadmap.md) use the same order.

---

## 8. Self-check

Do the tasks for your path under a timer, on a lab and never on production, then answer the hybrid questions, which every senior should answer whichever path they chose.

<div class="env" data-env="onprem" markdown="1">

### On-prem self-check

| # | Stage | Task | Time | Check against |
|---|---|---|---|---|
| 1 | Fresher | On a fresh Ubuntu VM, create the user ops with sudo and key-only SSH, enable UFW for 22 and 80, and serve a page from Apache | 30 min | [Linux self-check](27-learn-linux.md#18-self-check-exit-test) |
| 2 | Fresher | Fill /var on purpose, find the largest files, free the space, and explain what `df -i` shows | 15 min | [No space left on device](01-storage-disk.md#decision-tree-no-space-left-on-device) |
| 3 | Junior | Given port 444, name the process, unit, config file and log path | 10 min | [The chain: port to PID, unit, config and logs](22-playbook-ports-inventory.md#4-the-chain-port-to-pid-unit-config-and-logs) |
| 4 | Junior | Restore a VM from Proxmox Backup Server under a new VMID and boot it without an IP conflict | 30 min | [Proxmox VMs, storage and backups](50-problems-cloud-iac-proxmox.md#8-proxmox-ve-vms-storage-and-backups) |
| 5 | Mid-level | A VM on a VLAN-tagged bridge gets no network: find out why from the host | 20 min | [VLAN-tagged VMs get no network](50-problems-cloud-iac-proxmox.md#73-vlan-tagged-vms-get-no-network) |
| 6 | Mid-level | `docker login` to Harbor fails with an x509 error: fix trust on the Docker host and on the GitLab runner | 25 min | [Harbor and the private CA](47-cicd-gitlab-jenkins-actions-argocd.md#7-registries-harbor-and-the-private-ca) |
| 7 | Mid-level | A disk reports reallocated sectors and the RAID is degraded: decide, document and plan the swap | 20 min | [Physical disk health](01-storage-disk.md#7-physical-disk-health-on-premise-and-detectable-in-dmesg-anywhere) |
| 8 | Senior | Power off one node of a three-node Proxmox cluster, keep quorum and service, then bring it back | 45 min | [Cluster lost quorum](50-problems-cloud-iac-proxmox.md#74-cluster-lost-quorum) |
| 9 | Senior | Write the capacity report for your cluster: CPU, RAM, storage, growth per month and the date you run out | 60 min | [Capacity planning](39-learn-senior-architecture.md#capacity-planning-l3-senior) |
| 10 | Senior/Lead | Run a tabletop for a building power cut: UPS shutdown order, restart order, who is called and how long it takes | 60 min | [Exercise 8](39-learn-senior-architecture.md#exercise-8-building-power-off-for-8-hours-l4-leadsre) |

</div>

<div class="env" data-env="cloud" markdown="1">

### Cloud self-check

| # | Stage | Task | Time | Check against |
|---|---|---|---|---|
| 1 | Fresher | Open a new sandbox safely: root MFA, an Identity Center user, a budget alarm, and `aws sts get-caller-identity` from your laptop | 30 min | [Sandbox account first](36-learn-cloud-aws.md#sandbox-account-first) |
| 2 | Fresher | Launch an Ubuntu instance, reach it with SSM (no port 22), then delete everything and prove nothing is left | 20 min | [SSM Session Manager](36-learn-cloud-aws.md#ssm-session-manager) |
| 3 | Junior | Build a VPC with public and private subnets in Terraform, then destroy it | 45 min | [VPC deep dive](36-learn-cloud-aws.md#3-vpc-deep-dive) |
| 4 | Junior | Grow an EBS volume and its filesystem without a reboot | 15 min | [Grew the EBS volume](50-problems-cloud-iac-proxmox.md#22-grew-the-ebs-volume-df-shows-the-old-size) |
| 5 | Mid-level | The ALB returns 502: name the cause from target health and the ALB access log | 20 min | [ALB returns 502, 503 or 504](50-problems-cloud-iac-proxmox.md#24-alb-returns-502-503-or-504) |
| 6 | Mid-level | A role gets AccessDenied reading from a KMS-encrypted bucket: find which policy denies it | 25 min | [Debugging AccessDenied](36-learn-cloud-aws.md#debugging-accessdenied) |
| 7 | Mid-level | A private instance cannot reach the internet: fix it from the route tables alone | 15 min | [Private subnet can't reach the internet](50-problems-cloud-iac-proxmox.md#21-private-subnet-cant-reach-the-internet) |
| 8 | Senior | Make GitLab CI deploy Terraform to AWS through OIDC with no stored keys | 60 min | [GitLab CI to AWS with OIDC](36-learn-cloud-aws.md#gitlab-ci-to-aws-with-oidc) |
| 9 | Senior | Find the three biggest line items of last month's bill and cut one of them by half | 45 min | [Surprise bill](50-problems-cloud-iac-proxmox.md#25-surprise-bill-nat-public-ipv4-and-leftovers) |
| 10 | Senior/Lead | Restore the application and its database into a second region from backups only, and measure RTO and RPO | 90 min | [Designing for failure and DR](36-learn-cloud-aws.md#designing-for-failure-and-dr) |

</div>

### Hybrid questions

1. An EC2 instance in 10.20.1.0/24 cannot resolve ci.corp.example.com, but every on-prem server can. Which two AWS objects do you check first, and which on-prem one?
2. A container on an on-prem Docker host reaches the internet but not 172.31.5.20 in the default VPC over the VPN. What is the likely cause, and what is the permanent fix?
3. The business wants the PostgreSQL database moved to RDS while the application stays on-prem. Which two numbers do you measure before you agree, and what would make you say no?

**Hints:** (1) the Resolver outbound endpoint and the forwarding rule's association with that VPC, then the on-prem firewall between the endpoint's addresses and 192.0.2.53 on port 53. (2) A Docker network took 172.31.0.0/16 from the default pool, so replies to the VPC never leave the host; set `default-address-pools` in daemon.json to a range nothing else uses and recreate the networks. (3) The round-trip time per query multiplied by the queries per page, and the volume of data returned per month (egress); say no when a page makes hundreds of sequential queries or the data may not leave the building.

---

## 9. Where to go next

Whatever you picked, the playbooks (21–26) work in both places: the layers are the same, and only the first command changes.

- [Career ladder](40-career-ladder.md) and [Roadmap](34-roadmap.md): place yourself, then follow the roadmap and the [3D course map](#map), which both follow your path selection.
- [Senior: architecture & leadership](39-learn-senior-architecture.md): DR, cost and migration decisions across both environments.
- [Hybrid connectivity](36-learn-cloud-aws.md#11-hybrid-connectivity) and [Hybrid DR with AWS](39-learn-senior-architecture.md#hybrid-dr-with-aws-l4-leadsre): the deep dives behind section 6.

<div class="env" data-env="onprem" markdown="1">

### Next on the on-prem path

- [Case: Apache vs Dokploy on 443](21-case-apache-443-dokploy.md) and [Deployment patterns](35-deployment-patterns.md): finish your own migration, step by step.
- [Dokploy & self-hosted PaaS](45-dokploy-and-self-hosted-paas.md), [Traefik & reverse proxies](43-traefik-and-reverse-proxies.md), [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) and [Wazuh & security tools](48-wazuh-and-security-tools.md): the problem libraries for the tools you run.
- [Proxmox VE problems](50-problems-cloud-iac-proxmox.md#7-proxmox-ve-repositories-host-network-and-cluster) and [Databases, storage & backup problems](51-problems-databases-storage-backup.md): the infrastructure and data layers underneath.
- Official docs: [Proxmox VE](https://pve.proxmox.com/pve-docs/) and the [Ansible documentation](https://docs.ansible.com/).

</div>

<div class="env" data-env="cloud" markdown="1">

### Next on the cloud path

- [Cloud & AWS](36-learn-cloud-aws.md): the whole syllabus, stage by stage, with exit tests in section 15.
- [AWS reference](16-aws-cloud.md): the commands for the first five minutes of any AWS incident.
- [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md#1-aws-access-ssh-iam-and-credentials), sections 1–4: AWS, Terraform and OpenTofu problems people really hit.
- [Cloud security on AWS](37-learn-security-devsecops.md#10-cloud-security-on-aws) and [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md#5-terraform): the security and IaC halves of a cloud platform.
- Official docs: the [AWS documentation](https://docs.aws.amazon.com/) and [Terraform](https://developer.hashicorp.com/terraform/docs).

</div>
