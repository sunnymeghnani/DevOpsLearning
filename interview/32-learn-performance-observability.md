# 32 — Interview practice: The average looks good while users suffer

[Interview index](README.md) · [Matching handbook module](../32-learn-performance-observability.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M32-Q01 — Main question

A dashboard shows acceptable mean latency, but users report long waits. What signals would you add?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M32-Q02 — Interviewer twist

Only a small customer segment has slow requests and logs arrive late.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Compare latency distribution, errors, traffic and saturation by bounded useful dimensions. Correlate traces and logs with event time. Verify query time range and data freshness before trusting an empty panel.

### Why this order

Averages and ingestion delays can conceal a small but serious failure population.

### Common trap

Adding unique request IDs as metric labels or concluding no telemetry means no incidents.

### Verification and next practice

Use synthetic fast and slow requests to confirm the dashboard reveals the tail without uncontrolled label growth.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C09: Prometheus has samples, but Grafana looks empty](https://stackoverflow.com/questions/58572222/unable-to-fetch-data-in-grafana-even-though-prometheus-source-is-showing-the-var) — Stack Overflow. [Scope and access limits](SOURCES.md#c09).
  Technical cross-check: [Grafana panel inspector](https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/panel-inspector/).
- [C21: Loki is slow: when changing ingestion helped more than tuning knobs](https://community.grafana.com/t/loki-performance-and-missing-logs-issues/127458) — Grafana Community. [Scope and access limits](SOURCES.md#c21).
  Technical cross-check: [Loki label best practices](https://grafana.com/docs/loki/latest/get-started/labels/bp-labels/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
