# 53 — Interview practice: Build an OSS pipeline with clear ownership

[Interview index](README.md) · [Matching handbook module](../53-oss-devops-toolbox.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M53-Q01 — Main question

Design a small stack using Git, CI, a registry, Dokploy/Traefik, metrics/logs and Wazuh. Where does each responsibility end?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M53-Q02 — Interviewer twist

CI is green, the application is unreachable, and Wazuh has no events.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Separate build/promotion evidence, deployment state, public routing, application telemetry and security-event delivery. Assign owners and health checks to each boundary; use least-privilege identities and pinned artifacts.

### Why this order

A tool list is not a working pipeline. Each handoff needs an independently testable contract.

### Common trap

Treating a green build or one dashboard as end-to-end proof.

### Verification and next practice

Draw artifact, request and security-event flows; define one benign synthetic check per boundary and a rollback owner.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C16: Why is a successful Dokploy redeploy followed by 404s?](https://github.com/Dokploy/dokploy/issues/5453) — GitHub / Dokploy. [Scope and access limits](SOURCES.md#c16).
  Technical cross-check: [Docker service rollback scope](https://docs.docker.com/reference/cli/docker/service/rollback/).
- [C18: Wazuh: when agent replacement solved a never-connected report](https://groups.google.com/g/wazuh/c/DmlrOS3VXt8) — Wazuh Mailing List. [Scope and access limits](SOURCES.md#c18).
  Technical cross-check: [Wazuh enrollment troubleshooting](https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/troubleshooting.html).
- [C22: Why did unchanged GitLab jobs break after a docker:dind update?](https://about.gitlab.com/blog/docker-in-docker-with-docker-19-dot-03/) — GitLab Engineering. [Scope and access limits](SOURCES.md#c22).
  Technical cross-check: [Current GitLab Docker-in-Docker guidance](https://docs.gitlab.com/ci/docker/docker_in_docker/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
