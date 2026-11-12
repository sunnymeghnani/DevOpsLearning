# 56 — Sources & Verification

Use this page to trace a problem back to the research that informed it. Start with your
tool's problem library, open its sources here, and compare the source's environment and
version with your own. The source index below is bundled into the offline handbook;
opening the external references requires internet access.

## Reddit and Stack Overflow: start with a real case

This is your personal learning path under construction, not a record of work you have
completed. These **28 case readings** broaden the path beyond your own incidents.
The initial 12 Reddit and Stack Overflow discussions are now joined by 16 additions from
Stack Overflow, Server Fault, GitHub, official forums and first-party engineering reports.
The additions include **six historical production postmortems** and practical incident
questions with evidence, reported recovery, prevention and proposed verification exercises.
These are documented incidents, not a live outage feed. Two original Reddit cases remain
based only on indexed excerpts. The generated incident directory below links every case.
Reading a page does not verify its proposed fix, and no exercise has been marked complete.

| Topic | Read the incident, evidence limits and your next lab |
|---|---|
| Linux | [Disk usage: df versus du](41-problems-linux-systems.md#community-case-reading) |
| Networking | [DNS tools work, curl does not](42-problems-network-dns-tls-vpn.md#community-case-reading) |
| Traefik | [Running containers but 404 responses](43-traefik-and-reverse-proxies.md#community-case-reading) |
| Docker | [Connection refused and the missing listener](44-problems-docker-swarm-registry.md#community-case-reading) |
| Dokploy | [Host ports versus backend ports](45-dokploy-and-self-hosted-paas.md#community-case-reading) |
| Kubernetes | [Service selectors and missing backends](46-problems-kubernetes.md#community-case-reading) |
| CI/CD | [GitLab runner disk growth and Podman ownership](47-cicd-gitlab-jenkins-actions-argocd.md#community-case-reading) |
| Wazuh | [Registered agent versus event delivery](48-wazuh-and-security-tools.md#community-case-reading) |
| Observability | [Prometheus samples, empty Grafana panel](49-observability-stack-problems.md#community-case-reading) |
| Terraform | [State locks and overlapping CI jobs](50-problems-cloud-iac-proxmox.md#community-case-reading) |
| Databases | [Pool limits and reserved PostgreSQL connections](51-problems-databases-storage-backup.md#community-case-reading) |
| Daily learning | [An overwhelmed intern and a bounded learning task](52-devops-day-to-day.md#community-case-reading) |

Each reading separates the reported symptom, observed outcome, handbook reasoning backed by
primary documentation, and a proposed next exercise. Unresolved cases remain unresolved.
These are a starting selection, not an exhaustive survey or a ranking of incident frequency.
In the source index below, filter **Source status** to a community-reading or first-party
report label; search for a platform or tool to narrow the results. Recovery, workaround,
partial improvement and unresolved outcomes are distinguished rather than all called solved.

## What the labels mean

| Label | What you can conclude |
|---|---|
| Community thread page read · not a verified fix | The retrievable question and visible replies were inspected on the displayed date. Hidden replies, later edits and production reproduction are not covered. See the linked case for the outcome actually established. |
| Indexed community excerpt read · incomplete | Only the search engine's indexed text could be inspected. It may omit the resolution or corrections; the original page was not retrieved successfully. |
| First-party report read · historical account | The vendor's advisory or engineering report was retrieved. This records its stated remediation or recovery, not a reproduction in your environment. |
| Checked 2026-10-04 · limited scope | A specific claim was checked against the linked official page during this integration. The checked claim is displayed beside that reference. This is not a review of every command in the entry. |
| Reported checked in original research | The saved catalog has `verified: true`. This preserves the earlier researcher's report; it does not establish a fresh review, a fixed issue, or that the fix applies to your version. Many records contain no check date. |
| Not verified in saved research | The source was not marked verified. Inspect it before relying on it. |
| Discovery link · not evidence for a fix | A search, issue listing or collection helps you find relevant discussions. It does not substantiate a particular diagnosis or solution, even if someone visited the listing. |

The index preserves source titles and types from the saved catalogs. A community issue is a
report from that environment; an open issue or proposed workaround is not a confirmed universal
root cause. Popularity and comments are useful discovery signals, not proof of frequency.

## When a source cannot be read

The earlier research run could not retrieve Reddit, Stack Overflow and Server Fault. That is
an access limitation recorded for that run, not a permanent claim that every tool or reader is
blocked, nor proof of the reason access failed. On 4 October 2026, the new case readings above
were retrieved using the currently available research tool. The Wazuh and Terraform Reddit
cases remain excerpt-only. Original search links are still labeled discovery, never silently
promoted into read threads. The expanded selection includes a retrieved Server Fault
inode-exhaustion discussion; this does not imply every page on that site is accessible.

When a page is unavailable, use the tool's official documentation for your installed version,
then its release notes, issue tracker or official support forum. Record the unavailable URL and
the replacement source. If the available evidence does not establish the cause, keep the
diagnosis as a hypothesis and test it in a disposable lab.

## From community report to a useful runbook

1. Capture the exact error, application version, operating system and deployment mode.
2. Match the source's environment: Docker Compose and Swarm, for example, may use different
   configuration locations even when the error text looks similar.
3. Read the whole discussion, including later corrections, the resolution and affected versions.
4. Confirm the proposed behavior in the official documentation or an upstream change.
5. Reproduce the symptom in a lab. Record the deciding evidence, smallest corrective change,
   result and rollback. A working website build does not test the server commands in the handbook.
6. Add a dated incident note to [DevOps day to day](52-devops-day-to-day.md), then revisit the
   corresponding [learning topic](34-roadmap.md) and [practice exercise](54-practice-arena.md).

For a Wazuh agent, for example, enrollment and event delivery use different connections.
The official [enrollment troubleshooting guide](https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/troubleshooting.html)
documents their distinct ports. A successful enrollment alone does not show that event delivery
works. The [Wazuh problem library](48-wazuh-and-security-tools.md) develops the diagnostic steps.

## Keeping research manageable

Refresh one domain at a time. Prioritize a problem you actually encountered, an upgrade you plan,
or a command whose behavior has changed. Keep the source URL, date, affected versions and the
claim checked. Save progress after each bounded batch so a usage limit does not require starting
again. The existing catalogs remain usable when a website or research service is unavailable.

The generated index contains the saved problem catalogs for modules 41–52. The
[Practice Arena](54-practice-arena.md) and [Career Ladder](40-career-ladder.md) retain their own
course and practice links; this index does not claim to reverify those catalogs.

<!-- The build appends the source index from research/*.json here. -->
