# Free interactive learning tools: cloud, IAM, cost, security/DevSecOps, databases and system design

Research date: 2026-11-09. Reader: an on-prem DevOps engineer moving to cloud. Domains in `known_domains.txt` were skipped. Notable skips: owasp.org (so the OWASP Cheat Sheet Series is not listed), aws.amazon.com, cloud.google.com (this includes the GCP pricing calculator), learn.microsoft.com, developer.mozilla.org (this includes the HTTP Observatory), github.com, systemdesignsim.com, use-the-index-luke.com and wiz.io. Reddit, Stack Overflow and Server Fault were not used.

How each tool was checked:
- **Opened**: WebFetch returned the page's real content.
- **Opened (shell only)**: the page loaded, but it is a JavaScript app and only the title or navigation came back. Its features were confirmed from its official docs or repo, as noted for each tool.
- **Snippet only**: seen only in search results.

Maintenance was checked with GitHub's API (`pushed_at`) on 2026-11-09 where a repo exists. Nothing was logged into, submitted, downloaded or run.

Levels follow `roadmap.json`: L0 Fresher, L1 Junior, L2 Mid, L3 Senior, L4 Lead. Topic ids are the `cloud`, `security`, `data` and `sre` node ids in that file.

## Which free tools are verified, ranked, with privacy, account-impact, maintenance, level and topic fit?

### Takeaway
I ranked 34 free tools. 30 were opened with real content, and four only showed a shell, so their features were checked in docs. The top 26 are good to link and need no sign-up for the browser version (Threat Dragon is install or self-host). The best fits for this reader are these:
- Visual Subnet Calculator, which has an AWS/Azure reserved-IP mode.
- AWS Pricing Calculator and instances.vantage.sh.
- aws.permissions.cloud, plus a client-side IAM policy explainer.
- diagrams.net.
- db<>fiddle, explain.dalibo.com and PGTune.
- RaftScope, and samwho.dev's load-balancing simulator.
- CyberChef and jwt.ms for decoding tokens on your own machine.
- EPSS and Vulnerability-Lookup for CVE triage.
- CycloneDX Sunshine (client-side SBOM viewer) and Rekor Search.

None of the ranked tools touches or bills a cloud account. The only one that needs an account (Cloudcraft) is excluded below. Several tools store whatever you paste on their server; each entry says which.

### Cited Findings

**Ranked list (1 = most useful for this reader)**

1. **Visual Subnet Calculator**: https://visualsubnetcalc.com/
   - **What it does:** Visual VPC/subnet planner. You split and join subnets, add notes and colours, and share the design as a URL. Its AWS, Azure and OCI modes mark each provider's reserved addresses.
   - **Access and data:** Free, no sign-up, runs in the browser. The site says "We store nothing", and designs live in the shareable URL.
   - **Cloud account:** Not touched.
   - **Maintained:** Stable but slow. v1.4.0 came out on 2025-05-19, and the repo was last pushed on 2025-05-19.
   - **Level and topics:** L1–L2. `aws-vpc-alb`, `cloud-concepts`, `cloud-architecture`, `proxmox-ve` (bridge/VLAN addressing).
   - **Verification:** Opened.
   - Sources: [visualsubnetcalc.com](https://visualsubnetcalc.com/); [repo API](https://api.github.com/repos/ckabalan/visualsubnetcalc)

2. **AWS Pricing Calculator**: https://calculator.aws/
   - **What it does:** AWS's official, free web cost estimator. The docs say "You don't need any experience with cloud computing or AWS" to use it. You can group estimates, see how each price is calculated, and export to CSV or PDF.
   - **Access and data:** Free, no account needed, browser. When you save an estimate, its link is "saved to the AWS public servers", so don't put internal hostnames or project names in it.
   - **Cloud account:** The public calculator does not touch an account. Prices come from the AWS Price List API.
   - **Maintained:** Yes (official AWS tool).
   - **Level and topics:** L1–L4. `cloud-concepts`, `cloud-architecture` (FinOps), `aws-platform`.
   - **Verification:** Opened (shell only). Features confirmed from the AWS user guide.
   - Sources: [calculator.aws](https://calculator.aws/); [AWS docs: What is AWS Pricing Calculator](https://docs.aws.amazon.com/pricing-calculator/latest/userguide/what-is-pricing-calculator.html)

3. **instances.vantage.sh** (formerly ec2instances.info): https://instances.vantage.sh/
   - **What it does:** A filterable table of every EC2 instance type: vCPUs, memory, storage, network performance, and On-Demand, Reserved, Spot and Windows prices. The navigation also has RDS, Azure and GCP tabs.
   - **Access and data:** Free, browser. A newsletter and an API key are offered, but neither looked required to browse.
   - **Cloud account:** Not touched.
   - **Maintained:** Very active. The page showed "Updated 11/8/2026", and the repo was pushed on 2026-11-08 (MIT, ~5.8k stars).
   - **Level and topics:** L1–L4. `aws-iam-ec2`, `cloud-architecture`, `db-ha` (RDS sizing).
   - **Gap:** The tool shows no egress or data-transfer prices.
   - **Verification:** Opened.
   - Sources: [instances.vantage.sh](https://instances.vantage.sh/); [repo API](https://api.github.com/repos/vantage-sh/ec2instances.info)

4. **aws.permissions.cloud** (Ian McKay's IAM Dataset): https://aws.permissions.cloud/
   - **What it does:** A searchable, community-run reference for AWS IAM:
     - every permission, with its access level, resource ARN pattern and condition keys;
     - the API-call-to-IAM-permission mapping;
     - AWS managed policies, tagged for risks such as "possible privilege escalation" and "credentials exposure";
     - a **Policy Evaluator**: paste a policy to see its effective actions.
   - **Access and data:** Free, no sign-up, browser. The site doesn't say whether pasted policies leave the browser.
   - **Cloud account:** Not touched.
   - **Maintained:** Yes. The iam-dataset repo was pushed on 2026-11-08.
   - **Level and topics:** L2–L3. `aws-iam-ec2`, `aws-platform`, `security-response`, `k8s-security` (IRSA/role thinking).
   - **Verification:** Opened.
   - Sources: [aws.permissions.cloud](https://aws.permissions.cloud/); [iam-dataset API](https://api.github.com/repos/iann0036/iam-dataset)

5. **gcp.permissions.cloud**: https://gcp.permissions.cloud/
   - **What it does:** The same idea for Google Cloud: predefined roles tagged for risks such as privilege escalation, and the permission-to-API mapping. It links to the AWS and Azure versions.
   - **Access and data:** Free, no sign-up, browser.
   - **Cloud account:** Not touched.
   - **Maintained:** Same dataset repo as #4.
   - **Level and topics:** L2–L3. `cloud-concepts`, `cloud-architecture`.
   - **Caveat:** The captured page showed "-" placeholders instead of numbers, so I could not confirm the data loads.
   - **Verification:** Opened (data not rendered).
   - Source: [gcp.permissions.cloud](https://gcp.permissions.cloud/)

6. **OpenReplay AWS IAM Policy Explainer**: https://openreplay.com/tools/iam-policy-explainer/
   - **What it does:** Paste an IAM policy or a role trust policy and get a plain-English explanation of each statement. It flags full admin, public principals and broad wildcards.
   - **Access and data:** Free, browser. The page says "Runs entirely in your browser — nothing is uploaded", using a rule engine with no AI call.
   - **Cloud account:** Not touched.
   - **Maintained:** Unknown. The footer says © 2026 but gives no release date.
   - **Level and topics:** L1–L2. `aws-iam-ec2`, `object-storage-minio` (bucket policies).
   - **Verification:** Opened.
   - Source: [OpenReplay IAM policy explainer](https://openreplay.com/tools/iam-policy-explainer/)

7. **AWS Policy Generator**: https://awspolicygen.s3.amazonaws.com/policygen.html
   - **What it does:** AWS's form-based generator for IAM, S3 bucket, SNS topic, SQS queue and VPC endpoint policies.
   - **Access and data:** Free, browser, no login.
   - **Cloud account:** Not touched.
   - **Maintained:** Old but still online. The UI hasn't been updated in years.
   - **Level and topics:** L1. `aws-iam-ec2`, `object-storage-minio`.
   - **Verification:** Opened (shell only). The fetch returned only the title "AWS Policy Generator"; the policy types come from snippets of tutorials and the AWS blog.
   - Sources: [policygen page](https://awspolicygen.s3.amazonaws.com/policygen.html); [o7planning tutorial (snippet)](https://o7planning.org/14367/amazon-aws-policygen)

8. **diagrams.net / draw.io with cloud icon libraries**: https://app.diagrams.net/
   - **What it does:** Diagram editor. To get cloud icons, enable the AWS shapes under More Shapes → Networking, or use Arrange → Insert → Template → Cloud → AWS. It includes several years of AWS icon sets plus 3D/isometric shapes, and Azure has its own guide page.
   - **Access and data:** Free. The page says "You don't need to register or sign-up". Files are saved where you choose: your device, Google Drive or OneDrive.
   - **Cloud account:** Not touched.
   - **Maintained:** Yes (© 2026).
   - **Level and topics:** L1–L4. `cloud-architecture`, `aws-vpc-alb`, `availability-dr`, `postmortems` (incident diagrams).
   - **Verification:** Opened the drawio.com AWS guide.
   - Source: [drawio.com AWS diagrams guide](https://www.drawio.com/blog/aws-diagrams)

9. **db<>fiddle**: https://dbfiddle.uk/
   - **What it does:** Run SQL in the browser against many engine versions:
     - PostgreSQL 8.4 up to 19 RC 1, MySQL 5.5–9.7, MariaDB 10.2–12.3;
     - SQL Server 2017–2025, Oracle 11gR2–26ai, Db2, SQLite, DuckDB, Firebird;
     - YugabyteDB, TimescaleDB, DocumentDB, **Redis 8.10** and **Valkey 9.1**.
   - **Access and data:** Free, no sign-up. Your SQL runs on its server. The privacy notes say:
     - only the first three octets of your IP are logged;
     - no cookies or tracking;
     - fiddles are "not enumerable".
     It doesn't say how long fiddles are kept.
   - **Cloud account:** Not touched.
   - **Maintained:** Yes (© 2017–2026, current engine versions, 12.4M fiddles).
   - **Level and topics:** L1–L3. `db-basics`, `db-incidents` (try locks and EXPLAIN), `db-ha`.
   - **Verification:** Opened.
   - Source: [dbfiddle.uk](https://dbfiddle.uk/)

10. **explain.dalibo.com** (PEV2): https://explain.dalibo.com/
    - **What it does:** Shows a PostgreSQL EXPLAIN plan (text or JSON) as a graphical tree.
    - **Access and data:** Free, browser. The submit dialog warns that the plan "will be sent to the server and stored in a database". You can share a link, and "Also delete from server" is offered. A standalone offline HTML version (pev2) lets you avoid sending plans at all.
    - **Cloud account:** Not touched.
    - **Maintained:** Very active. The pev2 repo was pushed on 2026-11-03 (PostgreSQL licence, ~3.6k stars).
    - **Level and topics:** L2–L3. `db-incidents`, `db-basics`.
    - **Verification:** Opened.
    - Sources: [explain.dalibo.com](https://explain.dalibo.com/); [pev2 API](https://api.github.com/repos/dalibo/pev2)

11. **explain.depesz.com**: https://explain.depesz.com/
    - **What it does:** The classic PostgreSQL `EXPLAIN (ANALYZE, BUFFERS)` reader, which highlights the slow nodes.
    - **Access and data:** Free, browser. Plans are saved on the server. An "obfuscate" option hides table and column names, and listing on the public history page is opt-in. I saw no delete option.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes (© 2008–2026).
    - **Level and topics:** L2–L3. `db-incidents`.
    - **Verification:** Opened.
    - Source: [explain.depesz.com](https://explain.depesz.com/)

12. **PGTune**: https://pgtune.leopard.in.ua/
    - **What it does:** Generates postgresql.conf memory, parallelism and WAL settings. Inputs:
      - PostgreSQL version (10–19), OS and workload type;
      - RAM (it says to use the container memory limit for containers);
      - CPUs, connections, storage type (NVMe/SSD/SAN/HDD) and data size.
    - **Access and data:** Free, no sign-up, browser. The page doesn't say whether the calculation runs client-side.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes. The repo was pushed on 2026-11-06 (MIT).
    - **Level and topics:** L2. `db-incidents`, `db-basics`, `db-ha`.
    - **Verification:** Opened.
    - Sources: [pgtune](https://pgtune.leopard.in.ua/); [repo API](https://api.github.com/repos/le0pard/pgtune)

13. **RaftScope** on raft.github.io: https://raft.github.io/
    - **What it does:** An interactive simulation of a five-server Raft cluster and its logs. The page says "You can interact with it to see Raft in action" and admits it is "still pretty rough around the edges". The page also links the paper, talks and implementations.
    - **Access and data:** Free, browser.
    - **Cloud account:** Not touched.
    - **Maintained:** Stable rather than active. The raftscope repo was last pushed in 2024-07.
    - **Level and topics:** L3. `db-ha` (Patroni/etcd quorum), `proxmox-ve` (corosync quorum thinking), `availability-dr`.
    - **Verification:** Opened.
    - Sources: [raft.github.io](https://raft.github.io/); [raftscope API](https://api.github.com/repos/ongardie/raftscope)

14. **The Secret Lives of Data: Raft**: https://thesecretlivesofdata.com/raft/
    - **What it does:** A guided, step-by-step animated explainer of Raft (leader election, log replication). raft.github.io recommends it for beginners.
    - **Access and data:** Free, browser.
    - **Cloud account:** Not touched.
    - **Maintained:** Unknown (old but online). The home page lists only this one visualisation.
    - **Level and topics:** L2. `db-ha`, `availability-dr`.
    - **Verification:** Opened (shell only, JavaScript-driven). Its content is described by raft.github.io.
    - Sources: [thesecretlivesofdata.com](https://thesecretlivesofdata.com/); [raft.github.io](https://raft.github.io/)

15. **samwho.dev, "Load Balancing"**: https://samwho.dev/load-balancing/
    - **What it does:** An interactive simulation comparing round robin, weighted and dynamic-weighted round robin, least connections and PEWMA. It shows dropped requests and p50/p95/p99 latency, and how a queue trades drops for latency. The site also has interactive essays on hashing, Bloom filters and memory allocation, and links his queueing and retries essays on encore.dev.
    - **Access and data:** Free, browser.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes. Published 2023-04-10, updated 2026-10-25.
    - **Level and topics:** L2–L3. `aws-vpc-alb` (ALB routing behaviour), `availability-dr`, `outage-basics`.
    - **Verification:** Opened.
    - Sources: [samwho.dev/load-balancing](https://samwho.dev/load-balancing/); [samwho.dev index](https://samwho.dev/)

16. **CyberChef** (GCHQ): https://gchq.github.io/CyberChef/
    - **What it does:** A "cyber swiss army knife". You chain decode/encode operations (base64, hex, hashes, and more) to inspect tokens, certificates and encoded blobs.
    - **Access and data:** Free, browser. The page says it "runs entirely within your browser with no server-side component". Only Show on map, DNS over HTTPS and HTTP request make network calls.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes. The build was compiled on 2026-11-04 (v11.5.0 changelog).
    - **Level and topics:** L1–L3. `secrets`, `private-ca`, `security-response`.
    - **Verification:** Opened. The page text didn't confirm a JWT Decode operation.
    - Source: [CyberChef](https://gchq.github.io/CyberChef/)

17. **jwt.ms** (JWT decoder): https://jwt.ms/
    - **What it does:** Decodes a JWT and explains its claims (`iss`, `aud`, `nbf`, `exp`, `tfp`/`acr`, `nonce`).
    - **Access and data:** Free, browser. The input prompt says the token "never leaves your browser".
    - **Cloud account:** Not touched.
    - **Maintained:** Online in 2026.
    - **Level and topics:** L2–L3. `vault-sso` (Keycloak/Authentik OIDC tokens), `aws-platform` (OIDC keyless CI), `k8s-security`.
    - **Caveat:** The page didn't name its operator, so I couldn't confirm it is Microsoft's.
    - **Warning:** Even so, decode only test or expired tokens. A live bearer token is a credential.
    - **Verification:** Opened.
    - Source: [jwt.ms](https://jwt.ms/)

18. **jwt.io debugger** (Auth0/Okta): https://www.jwt.io/
    - **What it does:** Decodes, verifies and generates JWTs.
    - **Access and data:** Free, browser. The page I fetched doesn't say whether decoding happens client-side, and **shows no warning about pasting real tokens**.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes (© 2026 Okta, "presented by Auth0").
    - **Level and topics:** L2. `vault-sso`, `secrets`.
    - **Warning:** Use the "Generate example" token or lab tokens only. For anything sensitive, prefer #16 or #17.
    - **Verification:** Opened.
    - Source: [jwt.io](https://www.jwt.io/)

19. **FIRST EPSS** (Exploit Prediction Scoring System): https://www.first.org/epss/
    - **What it does:** Gives each CVE a daily-updated probability (0–1) and a percentile that it will be exploited in the next 30 days. Data comes through a free API (https://api.first.org/epss/), daily CSVs and GitHub.
    - **Access and data:** Free, no key mentioned. The landing page has no web lookup form.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes (scores published daily).
    - **Level and topics:** L2–L4. `container-hardening` (prioritising Trivy/Grype findings), `security-response`.
    - **Verification:** Opened.
    - Source: [first.org/epss](https://www.first.org/epss/)

20. **Vulnerability-Lookup** (CIRCL): https://vulnerability.circl.lu/
    - **What it does:** Combines CVE and advisory feeds from national databases, CSAF and community sources. It adds "sightings" (seen / confirmed / exploited / PoC) and several Known Exploited Vulnerabilities (KEV) catalogues (CISA, ENISA, CIRCL and others).
    - **Access and data:** Free, browser. Public `/vuln/CVE-…` pages; the page doesn't state whether search needs an account.
    - **Cloud account:** Not touched.
    - **Maintained:** Very active (entries dated 2026-11-08).
    - **Level and topics:** L2–L4. `container-hardening`, `security-response`, `wazuh-siem`.
    - **Caveat:** I didn't see EPSS or CVSS on the part of the page I read (the text was truncated).
    - **Verification:** Opened.
    - Source: [vulnerability.circl.lu](https://vulnerability.circl.lu/)

21. **OSV.dev**: https://osv.dev/
    - **What it does:** Google's open vulnerability database across 40 ecosystems (npm, PyPI, Go, Maven, Debian, Alpine, Ubuntu, Wolfi, Chainguard and more). It has a free API and the OSV-Scanner CLI. CVE IDs appear as aliases in records.
    - **Access and data:** Browsing and the API need no key, as shown on the page.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes (schema 1.7.4).
    - **Level and topics:** L2. `container-hardening`.
    - **Verification:** Opened.
    - Source: [osv.dev](https://osv.dev/)

22. **CycloneDX Sunshine** (SBOM viewer): https://cyclonedx.github.io/Sunshine/
    - **What it does:** Upload a CycloneDX JSON SBOM to get a summary, a component chart and a vulnerability table. It can add EPSS and CISA KEV data, lets you query the SBOM with SQL, and exports CSV. For SPDX, convert first.
    - **Access and data:** Free, browser. The page says data is "processed locally within your browser, without being transmitted anywhere else". EPSS/KEV enrichment presumably fetches those public feeds.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes. The repo was pushed on 2026-09-28 (Apache-2.0).
    - **Level and topics:** L2–L3. `container-hardening`, `aws-platform` (supply chain in CI).
    - **Verification:** Opened.
    - Sources: [Sunshine](https://cyclonedx.github.io/Sunshine/); [repo API](https://api.github.com/repos/CycloneDX/Sunshine)

23. **Rekor Search** (Sigstore transparency-log browser): https://search.sigstore.dev/
    - **What it does:** Searches Sigstore's public Rekor log for signing entries. The fields seen were "Attribute" and "Email".
    - **Access and data:** Free, browser. **Remember:** Rekor is public, so a keyless signature publishes the signer's identity (for example an email).
    - **Cloud account:** Not touched.
    - **Maintained:** Yes. The rekor-search-ui repo was pushed on 2026-11-04.
    - **Explainer:** Pair it with the Sigstore overview. Cosign gets a short-lived certificate from Fulcio using an OIDC token, the private key is thrown away, and the signature, digest and certificate go into Rekor. Verification checks the identity plus Rekor's proof of inclusion.
    - **Level and topics:** L3. `container-hardening`, `aws-platform` (keyless CI), `secrets`.
    - **Verification:** Opened.
    - Sources: [search.sigstore.dev](https://search.sigstore.dev/); [Sigstore overview](https://docs.sigstore.dev/about/overview/); [repo API](https://api.github.com/repos/sigstore/rekor-search-ui)

24. **Google CSP Evaluator**: https://csp-evaluator.withgoogle.com/
    - **What it does:** Paste a Content-Security-Policy to find weaknesses and "subtle CSP bypasses" against XSS. Also available as a Chrome extension. Google gives "no guarantees or warranties".
    - **Access and data:** Free, browser, no sign-up. The page doesn't say whether pasted policies reach Google; it links only the general Google privacy policy.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes. The repo was pushed on 2026-05-26.
    - **Level and topics:** L2–L3. No exact topic. Closest: `milestone-senior` (hardening the Apache→Dokploy app) and `security-response`.
    - **Verification:** Opened.
    - Sources: [CSP Evaluator](https://csp-evaluator.withgoogle.com/); [repo API](https://api.github.com/repos/google/csp-evaluator)

25. **OWASP Threat Dragon**: https://www.threatdragon.com/docs/
    - **What it does:** Threat modelling. You draw data-flow diagrams and attach threats using STRIDE, LINDDUN, CIA, CIA-DIE or PLOT4ai.
    - **Access and data:** Free (Apache-2.0). There is a **desktop app (install)** or a **self-hosted container web app**. The web app saves models to your local file system, or to GitHub, GitLab, Bitbucket or Google Drive if you set those up.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes. Docs are for v2.6.2, and the repo was pushed on 2026-11-04.
    - **Level and topics:** L3–L4. `security-response`, `cloud-architecture`, `k8s-security`.
    - **Caveat:** I found no public hosted demo that works without login.
    - **Verification:** Opened the docs. The www.threatdragon.com home page returned only its title.
    - Sources: [Threat Dragon docs](https://www.threatdragon.com/docs/); [repo API](https://api.github.com/repos/OWASP/threat-dragon)

26. **Redis Sandbox** (official): https://redis.io/try/sandbox/
    - **What it does:** Run Redis commands in the browser. Reads run against preloaded datasets. Writes go into a temporary session that expires, and keys must start with `pg:`. Also predefined queries, history and share links.
    - **Access and data:** Free, "no account required" per the guide. Commands run on Redis's servers.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes (guide published 2026-02-25).
    - **Level and topics:** L1–L2. `db-basics`, `oss-toolbox`.
    - **Verification:** Opened the official guide page, not the sandbox app itself. try.redis.io (snippet only) is an older demo with HELP/TUTORIAL. db<>fiddle (#9) also runs Redis 8.10 and Valkey 9.1.
    - Source: [Redis Sandbox guide](https://redis.io/tutorials/howtos/redis-sandbox/)

**Further verified tools, lower rank or narrower fit**

27. **CloudPing.co**: https://www.cloudping.co/
    - **What it does:** A latency matrix between 35 AWS regions, with P10–P99 percentiles over 1 day, week, month or year.
    - **Access and data:** Free, browser. A community project (contact matt@ma.dev, donation link).
    - **Cloud account:** Not touched.
    - **Level and topics:** L3–L4. `cloud-architecture`, `availability-dr` (DR region choice).
    - **Verification:** Opened.
    - Source: [cloudping.co](https://www.cloudping.co/)

28. **Azure Charts**: https://azurecharts.com/
    - **What it does:** A live explorer of Azure services, regions (including a latency map and an address-space map), update heat maps, lifecycle/deprecation timelines and a learning study map. Made by Aleksei Polkovnikov, a Microsoft Cloud Solution Architect.
    - **Access and data:** Free, browser.
    - **Cloud account:** Not touched.
    - **Maintained:** Yes. It says it is continually re-scanned, with a recent "What's New" list.
    - **Level and topics:** L1–L3. `cloud-concepts`, `cloud-architecture`.
    - **Verification:** Opened.
    - Source: [azurecharts.com](https://azurecharts.com/)

29. **Selfboot consistent-hash-ring demo**: https://gallery.selfboot.cn/en/algorithms/hashring
    - **What it does:** Add or remove nodes on a ring and set the number of virtual nodes per node. It shows each node's share of the ring and how keys move when nodes change.
    - **Access and data:** Free, browser.
    - **Cloud account:** Not touched.
    - **Maintained:** Source is in the selfboot/ai_gallery repo; I didn't check its maintenance.
    - **Level and topics:** L3. `db-ha`, `object-storage-minio` (MinIO erasure sets and placement thinking), `availability-dr`.
    - **Verification:** Opened.
    - Source: [hashring demo](https://gallery.selfboot.cn/en/algorithms/hashring)

30. **Aiven Kafka Visualization**: https://aiven.io/tools/kafka-visualization
    - **What it does:** Set partitions, brokers and replication factor, add consumers to groups A–E, and watch a producer send messages, with follower replicas shown faded. I saw no broker-failure option.
    - **Access and data:** Listed under Aiven's "Free tools". The "Get building" sign-up button is for Aiven's paid service, not the tool.
    - **Cloud account:** Not touched.
    - **Level and topics:** L2–L3. `oss-toolbox`, `cloud-architecture`.
    - **Related:** SoftwareMill's similar tool (https://softwaremill.com/kafka-visualisation/) returned only its title.
    - **Verification:** Opened.
    - Sources: [Aiven Kafka visualization](https://aiven.io/tools/kafka-visualization); [search snippet on SoftwareMill](https://softwaremill.com/kafka-visualisation)

31. **Interactive Latency Numbers** (Colin Scott): https://colin-scott.github.io/personal_website/research/interactive_latency.html
    - **What it does:** A year slider (1990–2020) redraws Norvig's latency numbers (L1 cache, RAM, SSD, disk seek, datacenter round trip).
    - **Access and data:** Free, browser.
    - **Cloud account:** Not touched.
    - **Maintained:** Not since 2020. Values after about 2005 (CPU) and 2014 (SSD) are extrapolated, not measured. Fine for intuition, not for current numbers.
    - **Level and topics:** L1–L2. `cloud-architecture`, `db-incidents`.
    - **Verification:** Opened.
    - Source: [interactive_latency](https://colin-scott.github.io/personal_website/research/interactive_latency.html)

32. **MySQL EXPLAIN visualiser**: https://mysqlexplain.com/
    - **What it does:** Paste a query, its EXPLAIN output and `SELECT VERSION()` to get a visual plan. A private self-hosted version is offered.
    - **Access and data:** The hosted version's data handling and price aren't stated on the page (see /legal/privacy).
    - **Cloud account:** Not touched.
    - **Level and topics:** L2–L3. `db-incidents`.
    - **Verification:** Opened.
    - Source: [mysqlexplain.com](https://mysqlexplain.com/)

33. **SQL Fiddle**: https://sqlfiddle.com/
    - **What it does:** A SQL playground for SQL Server, SQLite, PostgreSQL, MySQL, MariaDB and Oracle. The old version shut down at the end of 2023. The new one needs a Google or GitHub login for its AI features, and History is still "Under Development".
    - **Recommendation:** Prefer db<>fiddle.
    - **Level and topics:** L1. `db-basics`.
    - **Verification:** Opened.
    - Source: [sqlfiddle.com](https://sqlfiddle.com/)

34. **ByteByteGo guides**: https://bytebytego.com/guides/
    - **What it does:** About 400 illustrated system-design explainers in 15 categories, including Cloud & Distributed Systems (49), Database and Storage (47), Security (35) and DevOps/CI-CD (27).
    - **Access and data:** The page doesn't say whether the guides are free without login (it shows a Login link and a "Download Bundle" button).
    - **Level and topics:** L2–L4. `cloud-architecture`, `db-ha`, `availability-dr`.
    - **Caveat:** Not interactive.
    - **Verification:** Opened.
    - Source: [bytebytego.com/guides](https://bytebytego.com/guides/)

**Opened but excluded or unconfirmed**
- **Cloudcraft is not free on its own any more.** Its pricing page says it is "free in Datadog" with any Datadog subscription, and the sign-up goes to Datadog. Live AWS sync also needs read access to the account. **Excluded**, because it needs sign-up and account access. — [cloudcraft.co/pricing](https://www.cloudcraft.co/pricing)
- **Azure Pricing Calculator** (https://azure.microsoft.com/en-us/pricing/calculator/): only the title and navigation came back. The official Azure equivalent of #2. Unconfirmed details. — [Azure calculator](https://azure.microsoft.com/en-us/pricing/calculator/)
- **DB Fiddle** (https://www.db-fiddle.com/): only the title "DB Fiddle - SQL Database Playground" came back. — [db-fiddle.com](https://www.db-fiddle.com/)
- **Rego Playground** (https://play.openpolicyagent.org/): only the title came back, and the docs URL I tried returned 404. Relevant to `k8s-security` (OPA/Gatekeeper). Note that its "Publish" feature makes a public link. — [Rego Playground](https://play.openpolicyagent.org/)
- **securityheaders.com** returned HTTP 403 to the fetcher, so it is unverified. — [securityheaders.com](https://securityheaders.com/)
- **FIRST CVSS v4.0 calculator** (https://www.first.org/cvss/calculator/4-0): only the title and its place in the CVSS-SIG section; v3.1 and v3.0 calculators are linked. — [CVSS 4.0 calculator](https://www.first.org/cvss/calculator/4-0)
- **USFCA B+ tree visualisation** (https://www.cs.usfca.edu/~galles/visualization/BPlusTree.html): only the title "B+ Tree Visualization" came back. Useful for index intuition in `db-basics`, but interactivity is unconfirmed. — [USFCA B+ tree](https://www.cs.usfca.edu/~galles/visualization/BPlusTree.html)
- **cidr.xyz**: an IPv4 CIDR calculator with a bit map, by Yuval Adam. It doesn't say whether it runs client-side. It covers less than #1 (no cloud reserved-IP modes). — [cidr.xyz](https://cidr.xyz/)
- **deps.dev (Open Source Insights)** and **paperdraw.dev** (system design simulator; a Show HN post on 2026-03-02 per hnshowcase): only titles came back. Features, pricing and sign-up are unconfirmed. — [deps.dev](https://deps.dev/); [paperdraw.dev](https://paperdraw.dev/); [hnshowcase entry](https://hnshowcase.com/post/47218878/paperdraw-dev-a-system-design-simulator)

### Inferences
- **Starter set for the cloud study path:**
  - Visual Subnet Calculator (#1) for `aws-vpc-alb`.
  - aws.permissions.cloud (#4) plus OpenReplay (#6) for `aws-iam-ec2`.
  - calculator.aws (#2) plus instances.vantage.sh (#3) for `cloud-architecture` FinOps.
  - None of these can touch or bill the user's account, so they are safe on a sandbox-free day.
- **Privacy notes for handbook link labels:**
  - **Uploads what you paste:** explain.dalibo, explain.depesz, db<>fiddle, the Redis Sandbox, and saved AWS estimates (stored on AWS's public servers). Use lab data only.
  - **Stays in your browser:** CyberChef, jwt.ms, Sunshine and OpenReplay.
  - **Unclear:** jwt.io and CSP Evaluator.
- **JWT tools:** link jwt.ms or CyberChef first. jwt.io shows no real-token warning and doesn't state client-side decoding, so the handbook should add its own "never paste a live token" warning.
- **Consensus and HA:** for `db-ha` and `proxmox-ve` quorum, use The Secret Lives of Data (guided, L2) first, then RaftScope (hands-on, L3).
- **Load balancing:** samwho.dev's simulator is the best free interactive match for "why does my ALB/HAProxy spread load unevenly".
- **Domain overlap:** OWASP Cheat Sheets and the MDN HTTP Observatory would fit the security path but are on already-known domains (owasp.org, developer.mozilla.org), so they were left out here.

### Gaps
- **Egress cost explainers:** I found no egress explainer I could trust. The search turned up many egress calculators (egresscost.com, cloudtoolstack.com, spendark.com, holori, serverless-tools.pages.dev). Several look auto-generated, and they disagree on rates: GCP Premium Tier is quoted at both $0.085/GB and $0.12/GB. I didn't open them. For now, point readers at the official calculators (#2, Azure) and treat third-party egress numbers as unverified. Sources (search snippets only): [EgressCost.com](https://egresscost.com/), [SpendArk best egress calculators post (2026-09-07)](https://spendark.com/blog/best-egress-cost-calculators/)
- **CloudFormation/CDK visualisers:**
  - AWS Infrastructure Composer runs in the AWS Console, so it needs an account. I didn't check whether it has a public no-login mode.
  - The open-source options I found are mostly CLIs that you install: cloud-formation-viz, cfn-graph, and AWS-CloudFormation-Diagrams on PyPI.
  - Browser options are cloudgrapher on GitHub and the hosted InfraSketch, which is not open source.
  - I opened none of these, so none is verified. Source: search snippets only ([cloudgrapher](https://github.com/dmgress/cloudgrapher), [AWS-CloudFormation-Diagrams](https://pypi.org/project/AWS-CloudFormation-Diagrams)).
- **IAM Policy Simulator** (policysim.aws.amazon.com): needs AWS sign-in and reads real account policies, so it was **not** opened, per the no-login rule. Note that it's account-bound if the handbook mentions it.
- **Cedar playground** (cedarpolicy.com/en/playground): returned 404 at that URL.
- **Interactive system-design simulators:**
  - The ones found (PaperDraw, Chinilla, FlowFrame, Breakscale, System Design Sandbox) came from Product Hunt and aggregators.
  - Only PaperDraw's page was opened, and only its title came back. Pricing and sign-up are unknown.
  - systemdesignsim.com is a known domain and was skipped.
- **Other consistent-hashing demos:** the IIIT-H Virtual Labs experiment and sdmastery.vercel.app were seen in snippets only.
- **ByteByteGo:** whether the free guides need login is unconfirmed. The system-design-101 repo is on github.com (known domain).
- **Not everything was fully verified:** 34 tools are ranked. Four of them came back only as shells, so their features rest on official docs or snippets: #2 calculator.aws (AWS docs), #7 Policy Generator (snippets), #14 The Secret Lives of Data (raft.github.io) and #25 Threat Dragon (its docs page). The other 30 were opened with real content. I hit the tool-call budget. Hard JavaScript apps (calculator.aws, Azure calculator, Rego Playground, DB Fiddle, deps.dev) returned only shells. Confirming them needs a real browser pass, for example the project's headless-Chrome QA.
