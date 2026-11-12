# 45 — Interview practice: Dokploy says success, public route is gone

[Interview index](README.md) · [Matching handbook module](../45-dokploy-and-self-hosted-paas.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M45-Q01 — Main question

A Dokploy redeploy succeeds but the hostname returns 404. What should you compare with the previous revision?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M45-Q02 — Interviewer twist

The service is healthy while routing labels are unexpectedly absent.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Capture current service specification, previous specification, labels, provider logs and image digest. Verify the symptom matches the reported issue. Consider a scoped rollback only after assessing all fields and image changes it restores.

### Why this order

Deployment status and externally routable configuration are separate checks. A workaround does not establish a permanent upstream fix.

### Common trap

Claiming the issue is fixed because a rollback helped, or ignoring database compatibility of the old image.

### Verification and next practice

Reproduce only in a disposable project and compare labels and requests across revisions; retain version-specific evidence.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C16: Why is a successful Dokploy redeploy followed by 404s?](https://github.com/Dokploy/dokploy/issues/5453) — GitHub / Dokploy. [Scope and access limits](SOURCES.md#c16).
  Technical cross-check: [Docker service rollback scope](https://docs.docker.com/reference/cli/docker/service/rollback/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
