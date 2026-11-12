# 38 — Interview practice: More app replicas make database availability worse

[Interview index](README.md) · [Matching handbook module](../38-learn-databases-ops.md)

Stage: Intermediate → senior decision-making. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M38-Q01 — Main question

Autoscaling doubles the app replicas, then PostgreSQL reports exhausted connection slots. Why?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M38-Q02 — Interviewer twist

Each replica has its own pool and a rolling deployment briefly doubles pod count again.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Budget aggregate pools across peak replicas, rollout overlap, jobs and administration; inspect active versus idle connections and leaks. Consider pooling and concurrency limits before increasing database capacity limits.

### Why this order

Per-instance settings multiply at system scale, and each connection has a resource cost.

### Common trap

Raising max_connections without memory and workload analysis.

### Verification and next practice

Calculate peak demand, run a bounded load test and verify useful throughput plus administrative headroom.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C11: PostgreSQL pool sizing leaves no connection headroom](https://stackoverflow.com/questions/47651864/caused-by-org-postgresql-util-psqlexception-fatal-remaining-connection-slots) — Stack Overflow. [Scope and access limits](SOURCES.md#c11).
  Technical cross-check: [PostgreSQL connection limits and reserved slots](https://www.postgresql.org/docs/current/runtime-config-connection.html).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
