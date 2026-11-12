# 15 — Interview practice: Running pods, empty Service backends

[Interview index](README.md) · [Matching handbook module](../15-kubernetes.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M15-Q01 — Main question

All pods are Running but a Service has no usable endpoints. What is your next check?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M15-Q02 — Interviewer twist

One pod label differs from the Service selector and another pod is not Ready.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Inspect namespace, all selector terms, readiness, EndpointSlices, targetPort and actual listener. Fix the smallest mismatch and verify a request from a client pod before investigating ingress.

### Why this order

Running is a lifecycle state, not proof that a Service selects a ready backend.

### Common trap

Recreating the cluster or changing ingress before checking Service backends.

### Verification and next practice

Break one selector in a disposable namespace, observe the EndpointSlice and restore it without recreating workloads.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C06: A Service without endpoints: selectors must all match](https://stackoverflow.com/questions/65296133/kubernetes-service-does-not-have-endpoint) — Stack Overflow. [Scope and access limits](SOURCES.md#c06).
  Technical cross-check: [Kubernetes Service debugging guide](https://kubernetes.io/docs/tasks/debug/debug-application/debug-service/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
