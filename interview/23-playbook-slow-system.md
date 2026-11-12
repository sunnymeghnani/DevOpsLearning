# 23 — Interview practice: A slow system with no single hot process

[Interview index](README.md) · [Matching handbook module](../23-playbook-slow-system.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M23-Q01 — Main question

Users report latency while average CPU and RAM charts look normal. What do you compare?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M23-Q02 — Interviewer twist

Only one endpoint is slow and it waits on a shared database.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Compare percentiles and per-endpoint latency, dependency timings, queueing, I/O pressure and resource limits during the same window. Follow a representative slow request before collecting expensive profiles.

### Why this order

Host averages hide localized contention and downstream waits.

### Common trap

Scaling the entire application before locating the bottleneck.

### Verification and next practice

Use a controlled workload to measure the endpoint before and after a single change; watch error rate as well as latency.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C11: PostgreSQL pool sizing leaves no connection headroom](https://stackoverflow.com/questions/47651864/caused-by-org-postgresql-util-psqlexception-fatal-remaining-connection-slots) — Stack Overflow. [Scope and access limits](SOURCES.md#c11).
  Technical cross-check: [PostgreSQL connection limits and reserved slots](https://www.postgresql.org/docs/current/runtime-config-connection.html).
- [C27: Slack 2020: why did adding more servers not fix 503s?](https://slack.engineering/a-terrible-horrible-no-good-very-bad-day-at-slack/) — Slack Engineering. [Scope and access limits](SOURCES.md#c27).
  Technical cross-check: [Slack's technical incident account](https://slack.engineering/a-terrible-horrible-no-good-very-bad-day-at-slack/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
