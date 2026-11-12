# New free cloud and cloud-security practice (AWS, Azure, GCP, OCI), checked 7 Nov 2026

Scope: free hands-on, gamified, sandbox, break-fix and cloud-security CTF resources for an on-prem engineer moving to cloud, that are NOT already in the handbook. All pages were fetched on 2026-11-07 unless marked "(snippet only)", which means only a search-result snippet was seen and the page itself was not opened. Nothing was signed up for, logged into, downloaded or run. "Maintained" for GitHub projects comes from the GitHub API `pushed_at` field, read on 2026-11-07. That field counts any push, including bot or dependency pushes, so it shows the repo is alive, not that its content changed.

Cost-risk legend: **PROVIDED** = runs in an account, tenancy or browser that the vendor provides (no bill to the user). **OWN ACCOUNT** = you deploy it into your own cloud account, which can bill you.

## Q1. Which other free options exist in 2026 (not already in the handbook)?

### Takeaway
About 18 free options are live in Nov 2026. Six of them run in a vendor-provided environment, so there is no bill risk:
- AWS Educate labs
- Oracle LiveLabs sandbox
- Microsoft Applied Skills assessment labs
- Pwned Labs free tier
- Cybr free labs
- the Wiz Cloud Security Championship

The rest are open-source "vulnerable by design" projects that deploy into the user's OWN account:
- CloudFoxable
- IAM Vulnerable
- AWSGoat (plus the older AzureGoat and GCPGoat)
- Thunder CTF
- OWASP WrongSecrets (cloud mode)

Free cloud break-fix platforms and FinOps games are still scarce. The best break-fix product, AWS Jam, is mostly behind a subscription.

### Cited Findings

**A. PROVIDED environment (no cost risk)**

- **AWS Educate**: https://aws.amazon.com/education/awseducate/
  - Free ("completely for free"), "No credit card needed", and open to "any individual" aged 13+ who registers with an email address — [AWS Educate](https://aws.amazon.com/education/awseducate/)
  - Labs run in "the AWS Management Console in a sandbox" with just an email address and no Amazon account. Learners get unlimited attempts within a time window.
  - Lab list includes Introduction to IAM, Introduction to Amazon VPC, EC2, S3, RDS, Hosting a Static Website on S3, and Cognito application security — [AWS T&C blog, 15 Mar 2022](https://aws.amazon.com/blogs/training-and-certification/aws-educate-expands-access-to-free-cloud-education). This post is dated 2022. The 2026 landing page still promises "free hands-on labs … in real-time" but does not list them.
  - The FAQ URL (`/education/awseducate/faqs/`) returned HTTP 404 on 7 Nov 2026.
- **AWS SimuLearn (on AWS Skill Builder)**: https://aws.amazon.com/training/digital/aws-simulearn/
  - You hold an AI "customer" conversation, then build in "a risk-free AWS environment". The page says the building exercises are "guided" — [AWS SimuLearn page](https://aws.amazon.com/training/digital/aws-simulearn/)
  - Free accounts get "limited access to most immersive learning experiences". A full Individual subscription costs $29/month or $299/year — [AWS SimuLearn page](https://aws.amazon.com/training/digital/aws-simulearn/); price from an AWS-hosted page (snippet only) via [training.resources.awscloud.com](https://training.resources.awscloud.com/associate-certification-articles/develop-your-cloud-skills-with-aws-cloud-quest)
  - AWS lists free Cloud Practitioner and Generative AI Practitioner learning plans (snippet only).
- **AWS Workshops plus the AWS Builder Center free sandbox**: https://workshops.aws/ (catalog at https://catalog.workshops.aws/)
  - Workshops are "free, self-guided tutorial experiences". They run either at AWS events (event-provided accounts) or in your own account, where "some workshops may incur small charges". Each workshop has a cleanup tab — [AWS T&C blog, 8 Apr 2024](https://aws.amazon.com/blogs/training-and-certification/use-aws-workshops-to-accelerate-your-learning-of-aws)
  - New since 8 Jul 2026: AWS Builder Center offers free time-limited sandboxes, a "pre-provisioned AWS account" for select workshops.
    - No personal AWS account or credit card is needed.
    - Each sandbox gives 8 hours of access from activation, then is cleaned up automatically.
    - Limit is one sandbox per week (resets every Sunday). Most are ready in about 15 minutes.
    - Start at https://builder.aws.com/workshops — [AWS What's New, 8 Jul 2026](https://aws.amazon.com/about-aws/whats-new/2026/07/aws-builder-center-sandbox/)
  - InfoQ says the launch subset included Claude Code on Bedrock, AI-DLC and Amazon Quick workshops, and that topics also cover serverless APIs, VPCs and containers — [InfoQ, 1 Aug 2026](https://infoq.com/news/2026/08/aws-builder-sandbox)
  - The catalog site itself is JavaScript-only and could not be read by the fetcher.
- **Oracle LiveLabs**: https://livelabs.oracle.com/ (the fetch timed out). The help page is apexapps.oracle.com/pls/apex/dbpm/r/livelabs/page_help (HTTP 403 to the fetcher).
  - The help page says you can try Oracle Cloud "free of charge without creating an account or Oracle Cloud tenancy". Each reservation is a self-contained environment that is deleted when the reservation expires (snippet only) — [LiveLabs help](https://apexapps.oracle.com/pls/apex/dbpm/r/livelabs/page_help)
  - An Oracle forum post describes the "Run on LiveLabs Sandbox" option as resources created in an Oracle-owned tenancy (snippet only) — [Oracle Forums](https://forums.oracle.com/ords/apexds/post/free-livelabs-oracle-s-tools-and-technologies-to-run-a-wide-1419)
  - Contrast: the OCI Always Free tier in your own tenancy usually needs a mobile number and a credit card (snippet only) — [OCI Free Tier docs](https://docs.oracle.com/iaas/Content/FreeTier/freetier.htm)
  - Maintained: the GitHub org `oracle-livelabs` has 31 public repos, several pushed 4–6 Nov 2026 — [github.com/oracle-livelabs](https://github.com/oracle-livelabs)
- **Microsoft Applied Skills (lab-based assessments)**: https://learn.microsoft.com/en-us/credentials/applied-skills/
  - Credentials are earned through "a lab-based assessment" — [Applied Skills hub, updated 5 Aug 2026](https://learn.microsoft.com/en-us/credentials/applied-skills/)
  - Role journeys include Azure Administrator, Azure Network Engineer, Windows Server Hybrid Administrator, Security Engineer and DevOps Engineer.
  - Lab mechanics: you work in "a virtual environment … remotely connected to a live environment" (Azure Portal or Cloud Shell) using lab-supplied username and password. Time is 30 min (beginner) or 45 min (intermediate/expert). You cannot save and resume — [Assessment lab FAQ, updated 21 Nov 2025](https://learn.microsoft.com/en-us/credentials/support/assessment-lab-frequently-asked-questions)
  - The pages I fetched never state that it is free. "Free, no exam fees" comes from community write-ups (snippet only) — [DEV Community](https://dev.to/gracelee087/i-got-a-microsoft-certification-for-free-heres-how-applied-skills-review-5cf9), [Medium/Version 1](https://medium.com/version-1/microsoft-applied-skills-5b247bc748f2)
  - A Tech Community thread reports some assessment labs being unavailable (snippet only) — [Tech Community](https://techcommunity.microsoft.com/discussions/microsoftlearn/microsoft-applied-skills-assessment-update/4397764/replies/4413738)
- **Pwned Labs (free Academy tier)**: https://pwnedlabs.io/explore
  - "Over 30 hands-on scenarios are free to play with a free account", out of 90 scenarios.
  - "Every lab runs in a real cloud account that we provision for you". No own cloud account is needed and "There is nothing to set up" — [Pwned Labs explore](https://pwnedlabs.io/explore)
  - "Labs run in live environments that Pwned Labs provides". The site covers cloud, hybrid and AI security, with premium labs, cyber ranges and bootcamps on paid plans — [pwnedlabs.io](https://pwnedlabs.io/)
  - The pricing page (app.pwnedlabs.io/pricing) is JavaScript-only, so prices and the free/paid split by cloud were not visible.
- **Cybr (free labs)**: https://cybr.com/hands-on-labs/
  - The catalog filter shows 123 labs: 33 Free and 90 Premium. Labs are "One-click labs in real AWS and Azure environments" with automatic cleanup "so forgotten resources [don't create] surprise bills" — [Cybr hands-on labs](https://cybr.com/hands-on-labs/)
  - "No credit card required, just a free Cybr account" (snippet only) — [Cybr announcement](https://cybr.com/?p=22193)
  - Cybr posted monthly lab-release updates through Oct 2025 (snippet only) — [Cybr Oct 2025](https://www.cybr.com/?p=31282)
- **Wiz "Ultimate Cloud Security Championship"**: https://www.cloudsecuritychampionship.com/
  - A monthly CTF run by Wiz Research. Listed challenges run from June 2025 to May 2026 ("Glass House", May 2026, 50 pts). Topics include AWS S3, Azure AD/OAuth, Kubernetes and Terraform.
  - One challenge (Aug 2025) is marked "Inactive". The others still show "Enter Challenge" — [cloudsecuritychampionship.com](https://www.cloudsecuritychampionship.com/)
  - It goes "straight to the expert level". Players get a provided environment with "everything you'll need" — [Wiz blog, 26 Jun 2025](https://www.wiz.io/blog/the-ultimate-cloud-security-championship-12-months-x-12-challenges)
  - Price is not stated. The site has Login/Register.
- **Wiz "The Cloud Hunting Games"**: https://www.cloudhuntinggames.com/
  - An incident-response CTF made by Wiz Research: investigate a fictional data-extortion case at "ExfilCola". The in-story email is dated 6 May 2025.
  - The landing page does not state price, sign-up or exact topics — [cloudhuntinggames.com](https://www.cloudhuntinggames.com/)
  - DNS resolved on 7 Nov 2026. Listed on [wiz.io/ctf](https://www.wiz.io/ctf).

**B. OWN ACCOUNT (can bill you)**

- **CloudFoxable (Bishop Fox)**: https://cloudfoxable.bishopfox.com/ and https://github.com/BishopFox/cloudfoxable
  - A "Gamified Cloud Hacking Sandbox" (CTFd) with 18 challenges, deployed by Terraform into "a user-managed playground AWS account".
  - Challenges are split into "Always on (Low or No cost)" and "Enable as needed (These challenges incur cost)". The README warns: "Do not deploy this in production, shared, or corporate AWS accounts" — [README](https://raw.githubusercontent.com/BishopFox/cloudfoxable/main/README.md)
  - Repo last pushed 2026-05-01 — [GitHub](https://github.com/BishopFox/cloudfoxable)
- **IAM Vulnerable (Bishop Fox)**: https://github.com/BishopFox/iam-vulnerable
  - Terraform builds an IAM privilege-escalation playground with 31 paths. The default config is free. Optional modules cost money: EC2 about $4.50/month, Glue about $4/hour (a bill risk if left running), CloudFormation about $0.40/month.
  - Use a dedicated account — [README](https://github.com/BishopFox/iam-vulnerable)
  - Last pushed 2026-03-12.
- **AWSGoat (INE)**: https://github.com/ine-labs/AWSGoat
  - Module 1 is a serverless blog (Lambda, S3, API Gateway, DynamoDB). Module 2 is an HR app on ECS.
  - Covers XSS, SQLi, IDOR, SSRF, S3 misconfiguration, IAM privilege escalation and ECS container breakout.
  - Deploys "on the user's AWS account" via GitHub Actions or Terraform and needs admin-level keys.
  - Costs nothing inside the free tier. After that it costs $0.0125/h (M1) and $0.0505/h (M2) in us-east-1. The README has no cleanup section — [README](https://raw.githubusercontent.com/ine-labs/AWSGoat/master/README.md)
  - Last pushed 2026-11-04.
  - Siblings: AzureGoat (last pushed 2024-10-30) and GCPGoat (last pushed 2024-10-29) — [GitHub API](https://github.com/ine-labs/AzureGoat), [GitHub API](https://github.com/ine-labs/GCPGoat). Both are stale-ish.
- **Thunder CTF (GCP)**: https://thunder-ctf.cloud/
  - Six levels (a1openbucket … a6container) deployed on demand into your own GCP project and played from Cloud Shell. Billing must be enabled.
  - "Most resource use [fits] in GCP's free tier". Destroy levels after play.
  - Created at Portland State University under NSF Award #1821841 — [thunder-ctf.cloud](https://thunder-ctf.cloud/)
  - Repo last pushed 2025-06-25 — [GitHub](https://github.com/NicholasSpringer/thunder-ctf)
- **OWASP WrongSecrets**: https://github.com/OWASP/wrongsecrets
  - Secrets-management CTF. About 60 challenges run free in local Docker. Others need Kubernetes/Minikube or Vault. Cloud mode, in your OWN AWS/GCP/Azure account, "can be used for challenges 0-72".
  - Free hosted demo at wrongsecrets.herokuapp.com ("not always up").
  - Warning: "never run this on an account which is related to your production environment" — [README](https://raw.githubusercontent.com/OWASP/wrongsecrets/master/README.md)
  - Last pushed 2026-11-02.
- **TerraGoat (Bridgecrew)**: https://github.com/bridgecrewio/terragoat
  - A "Vulnerable by Design" Terraform repo showing how config errors reach production — [GitHub](https://github.com/bridgecrewio/terragoat)
  - Last pushed 2025-07-13. Seen via GitHub metadata only; README not opened.
- **Stratus Red Team (Datadog)**: https://github.com/DataDog/stratus-red-team
  - "Granular, Actionable Adversary Emulation for the Cloud" — [GitHub](https://github.com/DataDog/stratus-red-team)
  - Last pushed 2026-11-04. Seen via metadata only; README not opened.
- **Sadcloud (NCC Group)**: https://github.com/nccgroup/sadcloud
  - Stands up insecure cloud infrastructure — [GitHub](https://github.com/nccgroup/sadcloud)
  - Last pushed 2023-10-14, so stale. Not recommended.

**C. Free "money" programmes that make own-account labs safer**

- **AWS Free Tier "Free plan"**: https://aws.amazon.com/free/
  - Up to $200 in credits ($100 at sign-up plus up to $100 for exploring services).
  - The account "closes on its own 6 months after you open it or when your credits run out".
  - "No charges incurred unless you upgrade to a Paid plan or activate paid-only services" — [AWS Free Tier](https://aws.amazon.com/free/)
- **Azure for Students**: https://azure.microsoft.com/en-us/free/students
  - $100 credit for 12 months with "No credit card required". Only for full-time university students; renews yearly. The subscription is disabled when the credit runs out unless you move to pay-as-you-go — [Azure for Students](https://azure.microsoft.com/en-us/free/students)

**D. Browser sandbox (IaC)**

- **HashiCorp Terraform sandbox**: https://developer.hashicorp.com/terraform/sandbox
  - In-browser, with Terraform, Docker, LocalStack (free edition) and the AWS CLI aliased to awslocal. Sessions last up to 1 hour and nothing is saved.
  - Also offers Vault, Consul (discovery and service mesh), Nomad and Boundary sandboxes.
  - Warning: pointing the provider at real AWS is not cleaned up when the timer ends, so run `terraform destroy` — [HashiCorp sandbox](https://developer.hashicorp.com/terraform/sandbox)
  - Price and sign-in are not stated on the page.

**E. Cloud break-fix and FinOps (weak supply)**

- **AWS Jam**: https://aws.amazon.com/training/digital/aws-jam/
  - "troubleshoot, debug, and solve open-ended problems in the AWS Console". Free accounts get only "limited access".
  - Jam Events need a Skill Builder Team subscription — [AWS Jam page](https://aws.amazon.com/training/digital/aws-jam/)
- **DIY break-fix**:
  - AWS Builder Center article "I Broke AWS on Purpose" gives 10 beginner troubleshooting scenarios, which you break yourself (snippet only) — [builder.aws.com](https://builder.aws.com/content/3KHK3QXbPa3vM0TZQeC1XJo0QJy/i-broke-aws-on-purpose-troubleshooting-scenarios-every-beginner-should-try)
  - re:Invent 2023 NET302 "We break it, you fix it" VPC workshop. A write-up warns its template deletes default VPCs in every region, so use a dedicated account (snippet only) — [Classmethod write-up](https://dev.classmethod.jp/articles/reinvent2023-network-troubleshooting-net302-eng/)
- **FinOps**:
  - FinOps Foundation "FinOps the Board Game" is a 3–7 player cooperative game licensed CC BY 4.0; the page has a purchase link (snippet only) — [finops.org/game](https://www.finops.org/game/)
  - McKinsey cloud cost-optimization simulator, web-based (snippet only) — [McKinsey](https://mckinsey.com/business-functions/mckinsey-digital/our-insights/cloud-cost-optimization-simulator)
  - A KodeKloud repo `kodekloudhub/finops-practitioner-` is described in a mirror snippet as containing a "CloudBill" bill-leak game that runs offline via Docker. GitHub API: 3 stars, last pushed 2025-07-27 — [GitHub](https://github.com/kodekloudhub/finops-practitioner-)

**Paid or trial only, skipped:** Pluralsight / A Cloud Guru break-fix VPC labs ([Pluralsight](https://www.pluralsight.com/labs/aws/fix-a-broken-network-path-in-aws)), AWS Builder Labs and full Jam/SimuLearn/Cloud Quest ($29/mo Skill Builder Individual), Pwned Labs premium, Cybr Premium, QA SimuLab FinOps ([QA](https://platform.qa.com/lab/aws-finops-optimizing-costs-simulab)), LocalStack Base/Ultimate ([pricing](https://www.localstack.cloud/pricing)), Azure 30-day free trial (a trial, so excluded; card requirement not checked).

### Inferences
- For an on-prem engineer, the safest progression is:
  1. AWS Educate (VPC and IAM labs, no card)
  2. Free Skill Builder SimuLearn / Cloud Quest Cloud Practitioner
  3. Builder Center 8-hour sandbox for a VPC or containers workshop
  4. Pwned Labs and Cybr free labs for security
  5. Only then the OWN-ACCOUNT goats, ideally inside an AWS Free-plan account, which cannot bill unless upgraded.
- With Learn sandboxes gone (see Q4), Microsoft Applied Skills labs and Azure for Students (students only) look like the only no-card ways left to touch a live Azure portal.
- Oracle LiveLabs is the only big-cloud option found that gives a free, Oracle-owned sandbox tenancy per reservation. That makes it useful for comparing OCI VCN/IAM with AWS VPC/IAM at zero cost, although most LiveLabs workshops are database or AI focused (the repo names are mostly adb, database, analytics-ai).
- Of the own-account projects, CloudFoxable and IAM Vulnerable have the clearest "free by default, opt-in costs" design. AWSGoat bills per hour once you are outside the free tier and has no documented teardown, so the handbook should stress `terraform destroy`.

### Gaps
- Exact Pwned Labs and Cybr free/premium split by cloud, and their prices: the pricing pages are JavaScript-only and could not be read.
- Whether Microsoft Applied Skills assessments are officially free: no Microsoft page fetched states the price. Only community posts say "free".
- Oracle LiveLabs details (reservation length, whether an Oracle account sign-in is required, list of OCI networking workshops): the site timed out or returned 403, so only snippets were seen.
- Whether the AWS Free plan still requires a credit card at sign-up: the free-tier page does not say.
- Which Builder Center workshops currently support the free sandbox: the announcement names none, and builder.aws.com/workshops was not opened.
- No free, maintained, gamified FinOps/cost game with verified availability was found. Evidence is snippets only.
- No dedicated free cloud break-fix platform (a SadServers-style service for AWS/Azure/GCP) was found.

## Q2. Per-item facts: URL, what you practise, free vs paywalled, sign-up, card, where it runs, level, maintained

### Takeaway
The table below summarises Q1. Levels L0–L4 are my inference from the stated audience. Facts and sources are in Q1.

### Cited Findings

| # | Name / URL | Practise | Free vs paywalled | Sign-up? | Card? | Runs where | Level | Maintained | Source |
|---|---|---|---|---|---|---|---|---|---|
| 1 | AWS Educate, aws.amazon.com/education/awseducate | Console labs: IAM, VPC, EC2, S3, RDS, static site | Fully free | Email registration | No | PROVIDED sandbox | L0 | Page © 2026 | [AWS](https://aws.amazon.com/education/awseducate/), [blog](https://aws.amazon.com/blogs/training-and-certification/aws-educate-expands-access-to-free-cloud-education) |
| 2 | AWS SimuLearn, skillbuilder.aws | AI customer conversation, then guided build | Free CP and GenAI plans (snippet); rest $29/mo | Skill Builder account | Not stated | PROVIDED "risk-free AWS environment" | L0–L2 | Live 2026 | [AWS](https://aws.amazon.com/training/digital/aws-simulearn/) |
| 3 | AWS Workshops, workshops.aws, plus Builder Center sandbox (builder.aws.com/workshops) | VPC, containers, serverless, security, migration workshops | Content free; own-account usage billed; sandbox free (8 h, 1/week, select workshops) | Builder ID for sandbox | Sandbox: no | Event account, OWN ACCOUNT, or PROVIDED sandbox | L1–L3 | Sandbox launched 8 Jul 2026 | [blog](https://aws.amazon.com/blogs/training-and-certification/use-aws-workshops-to-accelerate-your-learning-of-aws), [What's New](https://aws.amazon.com/about-aws/whats-new/2026/07/aws-builder-center-sandbox/) |
| 4 | Oracle LiveLabs, livelabs.oracle.com | OCI and Oracle workshops | Sandbox reservations free (snippet) | Likely Oracle account (unverified) | Sandbox: none mentioned; own Free Tier: usually yes | PROVIDED Oracle-owned tenancy, or own tenancy | L0–L2 | GitHub pushes Nov 2026 | [help (snippet)](https://apexapps.oracle.com/pls/apex/dbpm/r/livelabs/page_help), [GitHub](https://github.com/oracle-livelabs) |
| 5 | Microsoft Applied Skills, learn.microsoft.com/credentials/applied-skills | Timed real-portal tasks (Azure admin, networking, hybrid, security) | Reported free (community only) | Microsoft Learn profile | Not stated | PROVIDED lab VM and Azure tenant | L1–L3 | Hub updated 5 Aug 2026 | [hub](https://learn.microsoft.com/en-us/credentials/applied-skills/), [lab FAQ](https://learn.microsoft.com/en-us/credentials/support/assessment-lab-frequently-asked-questions) |
| 6 | Pwned Labs, pwnedlabs.io/explore | AWS/Azure/GCP attack and defence scenarios | 30+ of 90 free; rest paid | Free account | Not stated | PROVIDED real cloud accounts | L1–L3 | Active (live site) | [explore](https://pwnedlabs.io/explore) |
| 7 | Cybr, cybr.com/hands-on-labs | AWS/Azure red and blue team labs | 33 of 123 free | Free account | No (snippet) | Vendor labs with auto-cleanup | L1–L3 | Releases to Oct 2025 | [labs](https://cybr.com/hands-on-labs/) |
| 8 | Wiz Cloud Security Championship, cloudsecuritychampionship.com | Expert monthly cloud CTF (AWS, Azure, K8s, Terraform) | Price not stated | Login/Register | Not stated | PROVIDED environment | L3–L4 | Last listed challenge May 2026 | [site](https://www.cloudsecuritychampionship.com/), [blog](https://www.wiz.io/blog/the-ultimate-cloud-security-championship-12-months-x-12-challenges) |
| 9 | Wiz Cloud Hunting Games, cloudhuntinggames.com | Incident-response investigation | Not stated | Not stated | Not stated | Browser (likely) | L2–L3 | Story dated May 2025; DNS live Nov 2026 | [site](https://www.cloudhuntinggames.com/) |
| 10 | CloudFoxable, cloudfoxable.bishopfox.com | AWS pentest attack paths (18 flags) | Free OSS | No | n/a (your AWS) | OWN ACCOUNT; low or no cost, opt-in costly flags | L2–L3 | Pushed May 2026 | [README](https://raw.githubusercontent.com/BishopFox/cloudfoxable/main/README.md) |
| 11 | IAM Vulnerable, github.com/BishopFox/iam-vulnerable | 31 IAM privilege-escalation paths | Free OSS; default $0 | No | n/a | OWN ACCOUNT | L2–L3 | Pushed Mar 2026 | [GitHub](https://github.com/BishopFox/iam-vulnerable) |
| 12 | AWSGoat, github.com/ine-labs/AWSGoat | Serverless and ECS app plus IAM/S3 vulns | Free OSS; ~$0.01–0.05/h after free tier | No | n/a | OWN ACCOUNT | L2–L3 | Pushed Nov 2026 (Azure/GCP Goats: Oct 2024) | [README](https://raw.githubusercontent.com/ine-labs/AWSGoat/master/README.md) |
| 13 | Thunder CTF, thunder-ctf.cloud | GCP misconfigurations (6 levels) | Free OSS; mostly within GCP free tier | GCP account | GCP billing needed | OWN PROJECT | L2 | Pushed Jun 2025 | [site](https://thunder-ctf.cloud/) |
| 14 | OWASP WrongSecrets, github.com/OWASP/wrongsecrets | Secrets management across Docker, K8s and cloud | Free; cloud mode billed | No | n/a | Local Docker (free), or OWN cloud account | L1–L3 | Pushed Nov 2026 | [README](https://raw.githubusercontent.com/OWASP/wrongsecrets/master/README.md) |
| 15 | HashiCorp sandboxes, developer.hashicorp.com/terraform/sandbox | Terraform against LocalStack; Vault, Consul, Nomad, Boundary | Price not stated | Not stated | Not stated | Browser (1 h) | L1–L2 | Live page | [HashiCorp](https://developer.hashicorp.com/terraform/sandbox) |
| 16 | AWS Free plan, aws.amazon.com/free | Real AWS with $100–200 credits | Free plan cannot bill unless upgraded | AWS account | Not stated on page | OWN ACCOUNT (capped) | any | Current | [AWS](https://aws.amazon.com/free/) |
| 17 | Azure for Students, azure.microsoft.com/free/students | Real Azure, $100 for 12 months | Students only | School email | No | OWN SUBSCRIPTION (credit-capped) | any | Current | [Azure](https://azure.microsoft.com/en-us/free/students) |
| 18 | TerraGoat / Stratus Red Team | IaC misconfig scanning; cloud attack emulation for detection | Free OSS | No | n/a | Local scan, or OWN ACCOUNT | L2–L4 | Pushed Jul 2025 / Nov 2026 (metadata only) | [TerraGoat](https://github.com/bridgecrewio/terragoat), [Stratus](https://github.com/DataDog/stratus-red-team) |

### Inferences
- Rows 1–9 and 15 carry essentially no bill risk. Rows 10–14 and 18 need a dedicated sandbox account with a budget alarm. Rows 16–17 are the recommended "dedicated account" for them.

### Gaps
- Levels are my inference. Vendors give only rough audience notes (for example, Wiz says "expert level").
- I could not confirm sign-up or card requirements for the HashiCorp sandbox or the Wiz Cloud Hunting Games.

## Q3. Which handbook module does each fit?

### Takeaway
Most finds belong in 36 Learn cloud (AWS) and 37 Security/DevSecOps. The provided-environment Azure, OCI and AWS options strengthen 55 Paths on-prem vs cloud. The Terraform and LocalStack items fit 50.

### Cited Findings
- **16 AWS cloud / 36 Learn cloud (AWS)**: AWS Educate (VPC and IAM labs), SimuLearn, Workshops and the Builder Center sandbox, AWS Free plan — sources in Q1 ([AWS Educate](https://aws.amazon.com/education/awseducate/), [Builder sandbox](https://aws.amazon.com/about-aws/whats-new/2026/07/aws-builder-center-sandbox/), [AWS Free](https://aws.amazon.com/free/))
- **55 Paths on-prem vs cloud**: Microsoft Applied Skills (Azure Network Engineer, Windows Server Hybrid Administrator journeys), Oracle LiveLabs, Azure for Students — ([Applied Skills](https://learn.microsoft.com/en-us/credentials/applied-skills/), [Azure for Students](https://azure.microsoft.com/en-us/free/students))
- **50 Cloud/IaC/Proxmox problems**: HashiCorp Terraform sandbox; TerraGoat; the "I Broke AWS on Purpose" and NET302 break-fix ideas; the AWS Jam format — ([HashiCorp](https://developer.hashicorp.com/terraform/sandbox), [AWS Jam](https://aws.amazon.com/training/digital/aws-jam/))
- **37 Security/DevSecOps**: Pwned Labs, Cybr, Wiz Championship and Cloud Hunting Games, CloudFoxable, IAM Vulnerable, AWSGoat/AzureGoat/GCPGoat, Thunder CTF, WrongSecrets, Stratus Red Team (sources in Q1)
- **39 Senior architecture**: Wiz Championship (expert); Stratus Red Team (detection engineering); FinOps board game and simulator for cost architecture (snippet only)
- **35 Deployment patterns**: AWS Workshops (serverless and containers), AWSGoat (serverless and ECS designs)

### Inferences
- A "cost safety" callout (Free plan, Azure for Students, Builder sandbox) would sit best in 36 and 55, and module 37 should link to it before any OWN-ACCOUNT goat.

### Gaps
- None beyond Q1/Q2.

## Q4. What changed for already-covered items since 3 Oct 2026 (Cloud Quest and others)?

### Takeaway
Several covered items have changed:
- **Microsoft Learn sandboxes are officially gone.** This is the biggest change.
- **AWS Cloud Quest** was relaunched (v2, 11 Aug 2026) inside Skill Builder, and its docs page now just redirects there.
- **Three Wiz CTF domains, including the covered eksclustergames.com and bigiamchallenge.com, had no DNS web records on 7 Nov 2026.**
- **LocalStack** moved to an account-only model with a free non-commercial "Hobby" plan.

### Cited Findings
- **Microsoft Learn sandboxes retired.** The official FAQ says: "Sandboxes are no longer available. To complete exercises in training modules, you'll need access to an Azure subscription." It points to a free 30-day trial or pay-as-you-go (FAQ updated 2026-07-29) — [Microsoft Learn FAQ](https://learn.microsoft.com/en-us/training/support/faq?pivots=sandbox)
  - Learners reported this in Feb 2026 (AZ-104) — [Microsoft Q&A, 12 Feb 2026](https://learn.microsoft.com/en-us/answers/questions/5772915/microsoft-sandbox-is-no-longer-available)
  - AZ-500 training retired 31 Aug 2026 (snippet only) — [Tech Community](https://techcommunity.microsoft.com/discussions/microsoft-learn-for-educators/az-500-online-msl-learn-modules/4555668)
- **AWS Cloud Quest.**
  - `docs.cloudquest.skillbuilder.aws/coming-soon/` now says "AWS Cloud Quest has moved to AWS Skill Builder" and links to https://skillbuilder.aws/cloudquest — [Cloud Quest docs](https://docs.cloudquest.skillbuilder.aws/coming-soon/index.html). The docs root returned HTTP 403.
  - The new Cloud Quest launched 11 Aug 2026: an AI-powered virtual customer, building in "live AWS environments", official AWS badges, and tournaments. Progress carries over. Roles named are Cloud Practitioner and Generative AI Practitioner, with more coming.
  - The Cloud Practitioner quest is at https://skillbuilder.aws/learn/FU5WCYVGKY/aws-cloud-quest-cloud-practitioner/JF9TKU68GT — [AWS T&C blog, 11 Aug 2026](https://aws.amazon.com/blogs/training-and-certification/introducing-the-new-aws-cloud-quest-ai-powered-practice-hands-on-building-and-a-path-to-official-aws-badges/)
  - AWS's product page says "nine cloud roles". Free accounts get "limited access", and all roles need an Individual or Team subscription — [AWS Cloud Quest page](https://aws.amazon.com/training/digital/aws-cloud-quest/)
  - A snippet of the v2 page says the Cloud Practitioner role is free and "two roles are free" (snippet only) — [search snippet of docs.cloudquest page](https://docs.cloudquest.skillbuilder.aws/coming-soon/index.html)
- **Wiz EKS Cluster Games, Big IAM Challenge and K8s LAN Party appear offline.**
  - On 2026-11-07, `eksclustergames.com`, `bigiamchallenge.com` and `k8slanparty.com` (and their `www.` hosts) returned no A, AAAA or CNAME records from 1.1.1.1, although their Route 53 zones (SOA/NS) still exist. My own `dig` checks.
  - Other Wiz sites resolved in the same check: cloudsecuritychampionship.com, cloudhuntinggames.com, promptairlines.com.
  - [wiz.io/ctf](https://www.wiz.io/ctf) still links all three.
  - No shutdown announcement was found. The K8s LAN Party post (11 Mar 2024) has no retirement note — [Wiz blog](https://www.wiz.io/blog/k8s-lan-party-challenge)
- **LocalStack** now delivers "an account-based experience using a single image". The free "Hobby" plan is non-commercial and needs an account and auth token. "The LocalStack Community emulator will no longer receive product updates going forward" — [LocalStack pricing](https://www.localstack.cloud/pricing)
  - Secondary sources date the switch of the `latest` image to 23 Mar 2026 (snippet only) — [DEV Community](https://dev.to/peytongreen_dev/localstack-now-requires-an-account-heres-how-to-test-aws-in-python-without-one-in-2026-2153)
- **Google Skills Arcade** (on covered skills.google):
  - The 2026 Arcade launched 6 Jan 2026 — [Google Dev forum](https://discuss.google.dev/t/welcome-back-to-the-google-skills-arcade/317918)
  - Starting April 2026, "Arcade Sprints and Certification Zone" were sunset, games have fewer labs, and every game is worth 1 point — [Google Dev forum, 1 Apr 2026](https://discuss.google.dev/t/what-s-changing-in-the-google-skills-arcade-from-april-2026/345557)
  - Credits: "35 free credits each month" for developers, from one secondary source only and unverified (snippet only) — [getcoai](https://getcoai.com/?p=92058)
- **Still resolving or active:**
  - flaws.cloud and flaws2.cloud (S3 IPs), cloudresumechallenge.dev — DNS checked 7 Nov 2026; content not opened
  - CloudGoat repo last pushed 2026-10-14 — [GitHub](https://github.com/RhinoSecurityLabs/cloudgoat)
  - builder.aws.com gained the free sandbox (see Q1) — [AWS What's New](https://aws.amazon.com/about-aws/whats-new/2026/07/aws-builder-center-sandbox/)

### Inferences
- The handbook should:
  - Replace "learn.microsoft.com sandboxes" with "your own subscription (trial/Students) or Applied Skills labs".
  - Update the Cloud Quest entry to skillbuilder.aws/cloudquest (v2, Aug 2026).
  - Mark eksclustergames.com and bigiamchallenge.com as "unreachable as of Nov 2026, re-check".
  - Note that LocalStack free use now needs an account and is non-commercial.
- The missing DNS records may be a deliberate retirement or a temporary change. Either way, a learner clicking the links today would get a DNS error.

### Gaps
- No official Wiz statement on whether EKS Cluster Games, Big IAM Challenge or K8s LAN Party were retired. Status is inferred from DNS only.
- Exact free Cloud Quest roles and assignment counts in v2: the official blog and product page do not list them, and skillbuilder.aws is JavaScript-only for the fetcher.
- No official LocalStack blog post on the March 2026 date was opened. The date comes from secondary sources.
