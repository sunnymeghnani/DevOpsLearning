# 49 — Interview practice: Logging changes make the monitoring stack slow

[Interview index](README.md) · [Matching handbook module](../49-observability-stack-problems.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M49-Q01 — Main question

Loki queries slow down after an application adds a label per request. What would you inspect?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M49-Q02 — Interviewer twist

Some logs also arrive late, and a forum workaround only improved performance.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Inspect stream cardinality, volume, resource pressure, ingestion errors, query scope and timestamp handling. Keep high-cardinality request identifiers out of index labels; use suitable structured fields and search. Track completeness separately from query speed.

### Why this order

An improvement in latency does not prove missing data has been recovered.

### Common trap

Calling a partially successful forum workaround a complete resolution.

### Verification and next practice

Replay bounded synthetic logs and measure both query latency and expected-versus-received event counts.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C21: Loki is slow: when changing ingestion helped more than tuning knobs](https://community.grafana.com/t/loki-performance-and-missing-logs-issues/127458) — Grafana Community. [Scope and access limits](SOURCES.md#c21).
  Technical cross-check: [Loki label best practices](https://grafana.com/docs/loki/latest/get-started/labels/bp-labels/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
