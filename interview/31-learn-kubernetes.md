# 31 — Interview practice: A slow dependency causes a restart storm

[Interview index](README.md) · [Matching handbook module](../31-learn-kubernetes.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M31-Q01 — Main question

A Kubernetes application restarts whenever its database is briefly unavailable. What should the probes mean?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M31-Q02 — Interviewer twist

Startup migrations are slow, while the readiness and liveness checks both query the database.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Separate startup completion, ability to serve traffic and unrecoverable process failure. A transient dependency outage should not automatically imply that restarting the app helps. Set measured thresholds and observe EndpointSlice readiness.

### Why this order

Probe design affects cascading failures and recovery, not just green status icons.

### Common trap

Making all probes identical or disabling them indefinitely.

### Verification and next practice

Inject a brief dependency failure in a lab and show traffic readiness and restart behavior match the intended policy.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [P03: Kubernetes probe semantics](https://kubernetes.io/docs/concepts/workloads/pods/probes/) — Official documentation. [Scope and access limits](SOURCES.md#p03).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
