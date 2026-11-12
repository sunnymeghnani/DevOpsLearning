# Interview sources and evidence limits

Research date: 2026-10-04. External links need internet access. This ledger separates interview context, technical references and historical incident reports.

## Interview context

Yes, Reddit contains interview discussions and people reporting questions they encountered. Those are self-reports, not verified employer question banks. GitHub practice collections help organize learning. Stack Overflow provides real troubleshooting questions, usually **not** evidence that a question was asked in an interview.

The 56 module files are a first practice batch, not exhaustive coverage of DevOps interviews. One scenario adapts a Reddit-reported theme; 55 are newly authored. They are deliberately not labeled “actual interview questions.” Similar symptoms across scenarios are intentional: command knowledge, diagnosis, architecture and evidence assessment test different skills.

No site is guaranteed readable. Two inherited Reddit incident sources remain excerpt-only. Historical recovery is not proof that the same action is safe now. The case records in [community threads](../research/community-threads.json) and [community incidents](../research/community-incidents.json) preserve reported outcomes, unresolved questions, version context and technical comparisons.

The GitHub collection is only a coverage pointer; its individual answers were not revalidated as part of this pack. References in a module are relevant supporting/contextual sources, not a fabricated claim that Reddit, GitHub and Stack Overflow each supplied an exact interview for every field.

## R01

[Reddit: DevOps interview-experience discussion](https://www.reddit.com/r/devopsjobs/comments/1qepvk2/devops_interview_questions_recently_attended/)

Type: Interview self-reports. Visible replies describe candidate experiences and scenario topics. Claims about interviews, seniority and employers are not independently verified. Used for format and topic context, not as a technical answer key.

## R02

[Reddit: interview depth and follow-up discussion](https://www.reddit.com/r/devops/comments/1aiom83/my_top_20_devops_interview_questions_from_about/)

Type: Interview self-report and discussion. A commenter describes an add-owner-read-permission question and deeper follow-ups. Module 10 adapts that reported theme; its path-permission twist and answer checkpoints are newly authored. Other drills are not attributed to this thread.

## G01

[GitHub: bregman-arie/devops-exercises](https://github.com/bregman-arie/devops-exercises)

Type: Public practice collection. Used as a topic-coverage reference, not copied as an answer bank. Its README explicitly warns that most exercises do not represent actual interviews. It does not establish the accuracy of every community answer.

## P01

[GNU chmod manual via man7](https://man7.org/linux/man-pages/man1/chmod.1.html)

Type: Primary manual. Symbolic permission changes; consulted for the owner-read example. The GNU website request timed out, so the rendered GNU manual here was used.

## P02

[systemd.service manual via man7](https://man7.org/linux/man-pages/man5/systemd.service.5.html)

Type: Primary manual. Service execution and lifecycle reference. The freedesktop page returned 403; the rendered upstream manual here was retrieved.

## P03

[Kubernetes probe semantics](https://kubernetes.io/docs/concepts/workloads/pods/probes/)

Type: Official documentation. Startup, readiness and liveness have different lifecycle effects; match configuration details to your installed version.

## P04

[AWS VPC security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html)

Type: Official documentation. Stateful security-group behavior and scoped access. This page alone does not verify the complete proposed cloud architecture.

Also consulted for modules 16 and 36: [AWS network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html) explains stateless filtering and return traffic; [AWS PrivateLink concepts](https://docs.aws.amazon.com/vpc/latest/privatelink/concepts.html) explains private service access and endpoint types. Endpoint availability and policy still depend on the selected service.

## P05

[Microsoft netsh http reference](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/netsh-http)

Type: Official documentation. HTTP service state, URL reservations and SSL bindings; use read-only show operations for initial inventory.

## P06

[GitHub Actions secure-use reference](https://docs.github.com/en/actions/reference/security/secure-use)

Type: Official documentation. Secrets, log exposure and workflow trust boundaries; technical context, not a reported interview.

## C01

[Disk usage disagrees: df versus du](https://stackoverflow.com/questions/13081888/why-do-df-and-du-display-different-used-space-values-on-an-lvm-volume)

Type: Stack Overflow. Thread page retrieved; reading is not a verified fix. 2012 Linux/LVM report; historical discussion Outcome limitations remain in the handbook case record.

Technical comparison: [Linux unlink semantics](https://man7.org/linux/man-pages/man2/unlink.2.html).

## C02

[DNS tools resolve a name but curl cannot](https://stackoverflow.com/questions/74782370/dig-host-nslookup-chrome-browser-can-resolve-hostname-curl-cant)

Type: Stack Overflow. Thread page retrieved; reading is not a verified fix. 2022 macOS Ventura and local dnsmasq; not a Linux repair recipe Outcome limitations remain in the handbook case record.

Technical comparison: [curl name resolution and controlled overrides](https://everything.curl.dev/usingcurl/connections/name.html).

## C03

[Containers are running, but Traefik returns 404](https://stackoverflow.com/questions/58573806/docker-swarm-with-traefik-containers-are-up-but-getting-404)

Type: Stack Overflow. Thread page retrieved; reading is not a verified fix. 2019 Traefik migration with Compose and Swarm; old provider syntax Outcome limitations remain in the handbook case record.

Technical comparison: [Current Traefik Swarm routing reference](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/swarm/).

## C04

[A localhost failure that was not automatically a networking problem](https://stackoverflow.com/questions/51442777/failing-to-connect-to-localhost-from-inside-a-container-connection-refused)

Type: Stack Overflow. Thread page retrieved; reading is not a verified fix. 2018 Molecule/Ansible test with nginx and curl inside a container Outcome limitations remain in the handbook case record.

Technical comparison: [Docker container networking model](https://docs.docker.com/engine/network/).

## C05

[Dokploy: published host ports versus Traefik backend ports](https://www.reddit.com/r/selfhosted/comments/1ijuwjq/dokploy_and_traefik_how_to_handle_exposed_ports/)

Type: Reddit. Thread page retrieved; reading is not a verified fix. r/selfhosted Dokploy/OJS discussion; published mapping 8081:80 Outcome limitations remain in the handbook case record.

Technical comparison: [Traefik Docker backend-port selection](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/).

## C06

[A Service without endpoints: selectors must all match](https://stackoverflow.com/questions/65296133/kubernetes-service-does-not-have-endpoint)

Type: Stack Overflow. Thread page retrieved; reading is not a verified fix. 2020 Kubernetes Service selector discussion; related backend prerequisite, not proof of an ingress-controller defect Outcome limitations remain in the handbook case record.

Technical comparison: [Kubernetes Service debugging guide](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/).

## C07

[GitLab runner disk fills up in a different runtime context](https://www.reddit.com/r/gitlab/comments/1adzlb2/gitlab_runner_out_of_space/)

Type: Reddit. Thread page retrieved; reading is not a verified fix. 2024 GitLab Runner 16.7 with Podman and runner-user storage Outcome limitations remain in the handbook case record.

Technical comparison: [Podman reset scope and warnings](https://docs.podman.io/en/latest/markdown/podman-system-reset.1.html).

## C08

[Wazuh agent appears in the dashboard but never connects](https://www.reddit.com/r/Wazuh/comments/1e66dun/)

Type: Reddit. Indexed excerpt only; incomplete. July 2024 Windows-agent discussion; indexed question and reply excerpts only Outcome limitations remain in the handbook case record.

Technical comparison: [Wazuh enrollment troubleshooting and connection roles](https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/troubleshooting.html).

## C09

[Prometheus has samples, but Grafana looks empty](https://stackoverflow.com/questions/58572222/unable-to-fetch-data-in-grafana-even-though-prometheus-source-is-showing-the-var)

Type: Stack Overflow. Thread page retrieved; reading is not a verified fix. 2019 Grafana/Prometheus dashboard discussion Outcome limitations remain in the handbook case record.

Technical comparison: [Grafana panel inspector](https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/panel-inspector/).

## C10

[Terraform locks and overlapping CI work](https://www.reddit.com/r/Terraform/comments/1h5lx6a/)

Type: Reddit. Indexed excerpt only; incomplete. December 2024 Terraform/CI discussion; indexed excerpts only Outcome limitations remain in the handbook case record.

Technical comparison: [Terraform state locking and force-unlock cautions](https://developer.hashicorp.com/terraform/language/state/locking).

## C11

[PostgreSQL pool sizing leaves no connection headroom](https://stackoverflow.com/questions/47651864/caused-by-org-postgresql-util-psqlexception-fatal-remaining-connection-slots)

Type: Stack Overflow. Thread page retrieved; reading is not a verified fix. 2017 PostgreSQL 9.3 and c3p0; legacy versions, not current defaults Outcome limitations remain in the handbook case record.

Technical comparison: [PostgreSQL connection limits and reserved slots](https://www.postgresql.org/docs/current/runtime-config-connection.html).

## C12

[An overwhelmed DevOps intern asks where to start](https://www.reddit.com/r/devops/comments/1b5zp6m/i_got_hired_as_a_intern_help/)

Type: Reddit. Thread page retrieved; reading is not a verified fix. 2024 career discussion; personal experiences, not a representative survey Outcome limitations remain in the handbook case record.

Technical comparison: [Google SRE: effective troubleshooting](https://sre.google/sre-book/effective-troubleshooting/).

## C13

[Why can an almost-empty tmp directory reject new files?](https://serverfault.com/questions/1190392/cannot-create-files-under-tmp-no-space-left-on-device)

Type: Server Fault. Thread page retrieved; reading is not a verified fix. August 2025 Ubuntu 18.04 report; filesystem-specific behavior Outcome limitations remain in the handbook case record.

Technical comparison: [GNU df manual: inode reporting](https://man7.org/linux/man-pages/man1/df.1.html).

## C14

[Why does Docker say the entrypoint is missing when the file exists?](https://stackoverflow.com/questions/76085121/docker-for-windows-entrypoint-no-such-file-exists-even-though-it-does/76087946)

Type: Stack Overflow. Thread page retrieved; reading is not a verified fix. April 2023 Windows checkout used to build a Linux container; a related startup failure, not an architecture mismatch Outcome limitations remain in the handbook case record.

Technical comparison: [Git attributes: text and eol](https://git-scm.com/docs/gitattributes).

## C15

[Why did a Docker upgrade remove every Traefik route?](https://github.com/traefik/traefik/issues/12253)

Type: GitHub / Traefik. Thread page retrieved; reading is not a verified fix. November 2025 report: Docker 29.0.0 with Traefik 3.6.0; historical version pair Outcome limitations remain in the handbook case record.

Technical comparison: [Merged API-negotiation fix and rationale](https://github.com/traefik/traefik/pull/12256).

## C16

[Why is a successful Dokploy redeploy followed by 404s?](https://github.com/Dokploy/dokploy/issues/5453)

Type: GitHub / Dokploy. Thread page retrieved; reading is not a verified fix. September 2026 issue report: Dokploy 0.29.12 and 0.30.6, Docker-image apps on a single-node Swarm Outcome limitations remain in the handbook case record.

Technical comparison: [Docker service rollback scope](https://docs.docker.com/reference/cli/docker/service/rollback/).

## C17

[A solved Swarm 502 thread: should you really rebuild the cluster?](https://community.traefik.io/t/502-bad-gateway-solved/2947)

Type: Traefik Community. Thread page retrieved; reading is not a verified fix. November 2019 Traefik v2 / Swarm thread, with later replies; historical topology Outcome limitations remain in the handbook case record.

Technical comparison: [Docker Swarm network requirements](https://docs.docker.com/engine/swarm/networking/).

## C18

[Wazuh: when agent replacement solved a never-connected report](https://groups.google.com/g/wazuh/c/DmlrOS3VXt8)

Type: Wazuh Mailing List. Thread page retrieved; reading is not a verified fix. May 2021 Windows 10 and Wazuh 4.0-era discussion; incomplete exact version inventory Outcome limitations remain in the handbook case record.

Technical comparison: [Wazuh enrollment troubleshooting](https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/troubleshooting.html).

## C19

[Kubernetes node join failures and mismatched cgroup drivers](https://discuss.kubernetes.io/t/problem-when-joining-nodes-to-a-master/17640)

Type: Discuss Kubernetes. Thread page retrieved; reading is not a verified fix. 2021–2022 thread: Kubernetes 1.22, Ubuntu 20.04 and the historical Docker/dockershim setup Outcome limitations remain in the handbook case record.

Technical comparison: [Kubernetes container runtimes and cgroup drivers](https://kubernetes.io/docs/setup/production-environment/container-runtimes/).

## C20

[Terraform multi-region import: why does fixing a provider reveal destruction?](https://discuss.hashicorp.com/t/terraform-catch-22-lack-of-default-provider-causes-error-default-provider-breaks-per-region-providers/62078)

Type: HashiCorp Discuss. Thread page retrieved; reading is not a verified fix. January 2024 Terraform 1.6/1.7 and AWS provider 5.31; imported multi-region configuration Outcome limitations remain in the handbook case record.

Technical comparison: [Terraform provider inheritance and explicit mappings](https://developer.hashicorp.com/terraform/language/modules/develop/providers).

## C21

[Loki is slow: when changing ingestion helped more than tuning knobs](https://community.grafana.com/t/loki-performance-and-missing-logs-issues/127458)

Type: Grafana Community. Thread page retrieved; reading is not a verified fix. 2024 Loki on Kubernetes with S3 and shared read/write node capacity Outcome limitations remain in the handbook case record.

Technical comparison: [Loki label best practices](https://grafana.com/docs/loki/latest/get-started/labels/bp-labels/).

## C22

[Why did unchanged GitLab jobs break after a docker:dind update?](https://about.gitlab.com/blog/docker-in-docker-with-docker-19-dot-03/)

Type: GitLab Engineering. Historical first-party report retrieved. July 2019 vendor advisory about Docker 19.03; compare with current runner documentation Outcome limitations remain in the handbook case record.

Technical comparison: [Current GitLab Docker-in-Docker guidance](https://docs.gitlab.com/ci/docker/docker_in_docker/).

## C23

[GitLab 2017: what if the backups are not usable during an outage?](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/)

Type: GitLab Engineering. Historical first-party report retrieved. 31 January 2017 GitLab.com PostgreSQL incident; historical production postmortem Outcome limitations remain in the handbook case record.

Technical comparison: [GitLab's first-party recovery account](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/).

## C24

[Resend 2024: a local migration targeted production](https://resend.com/blog/incident-report-for-february-21-2024)

Type: Resend Engineering. Historical first-party report retrieved. 21 February 2024 production outage; published recovery and improvement plan Outcome limitations remain in the handbook case record.

Technical comparison: [Resend's incident timeline and remediation](https://resend.com/blog/incident-report-for-february-21-2024).

## C25

[Cloudflare 2019: how can one WAF rule exhaust CPU worldwide?](https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/)

Type: Cloudflare Engineering. Historical first-party report retrieved. 2 July 2019 global edge outage; historical first-party postmortem Outcome limitations remain in the handbook case record.

Technical comparison: [Cloudflare's WAF outage analysis](https://blog.cloudflare.com/details-of-the-cloudflare-outage-on-july-2-2019/).

## C26

[Cloudflare 2022: when a routing-policy change removes reachability](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/)

Type: Cloudflare Engineering. Historical first-party report retrieved. 21 June 2022 BGP policy incident; advanced routing comparison, not a Linux default-gateway recipe Outcome limitations remain in the handbook case record.

Technical comparison: [Cloudflare's routing incident analysis](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/).

## C27

[Slack 2020: why did adding more servers not fix 503s?](https://slack.engineering/a-terrible-horrible-no-good-very-bad-day-at-slack/)

Type: Slack Engineering. Historical first-party report retrieved. 12 May 2020 HAProxy/Consul incident; not a report about every backend being DOWN Outcome limitations remain in the handbook case record.

Technical comparison: [Slack's technical incident account](https://slack.engineering/a-terrible-horrible-no-good-very-bad-day-at-slack/).

## C28

[GitHub 2018: why did a short network fault need a long recovery?](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/)

Type: GitHub Engineering. Historical first-party report retrieved. 21–22 October 2018 MySQL/Orchestrator incident; related recovery-scale lesson, not an example of entirely untested backups Outcome limitations remain in the handbook case record.

Technical comparison: [GitHub's failover and recovery analysis](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/).
