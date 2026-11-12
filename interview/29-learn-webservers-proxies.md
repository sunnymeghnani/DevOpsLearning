# 29 — Interview practice: A proxy is healthy but users get errors

[Interview index](README.md) · [Matching handbook module](../29-learn-webservers-proxies.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M29-Q01 — Main question

The proxy's health check is green and new backends have been added, yet requests fail. What might the health check miss?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M29-Q02 — Interviewer twist

Some proxy workers retain stale backend membership.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Compare live backend configuration and capacity with discovery state, per-worker errors and real request success. Check configuration reload and update behavior; canary any restart or rollback.

### Why this order

Process health, correct routing and useful capacity are separate properties.

### Common trap

Adding unlimited backends or restarting every proxy simultaneously.

### Verification and next practice

Model a stale backend in a lab and verify both control-plane configuration and data-plane traffic after recovery.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C27: Slack 2020: why did adding more servers not fix 503s?](https://slack.engineering/a-terrible-horrible-no-good-very-bad-day-at-slack/) — Slack Engineering. [Scope and access limits](SOURCES.md#c27).
  Technical cross-check: [Slack's technical incident account](https://slack.engineering/a-terrible-horrible-no-good-very-bad-day-at-slack/).
- [C03: Containers are running, but Traefik returns 404](https://stackoverflow.com/questions/58573806/docker-swarm-with-traefik-containers-are-up-but-getting-404) — Stack Overflow. [Scope and access limits](SOURCES.md#c03).
  Technical cross-check: [Current Traefik Swarm routing reference](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/swarm/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
