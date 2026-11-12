# 46 — Interview practice: A historical Kubernetes answer meets a modern cluster

[Interview index](README.md) · [Matching handbook module](../46-problems-kubernetes.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M46-Q01 — Main question

A node cannot join and an old thread recommends changing Docker's cgroup driver. Should you copy it?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M46-Q02 — Interviewer twist

Your cluster uses containerd and the cited thread predates dockershim removal.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Identify Kubernetes, kubelet, CRI runtime and cgroup versions; inspect node and runtime logs. Check applicable driver configuration using current runtime documentation. Determine whether the reported symptom actually matches.

### Why this order

A similar error in a different runtime generation is a hypothesis, not a portable command.

### Common trap

Editing Docker configuration on a containerd node or mixing current and historical setup instructions.

### Verification and next practice

Write a version-aware diagnostic plan and validate matching drivers on a disposable node before attempting rejoin.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C19: Kubernetes node join failures and mismatched cgroup drivers](https://discuss.kubernetes.io/t/problem-when-joining-nodes-to-a-master/17640) — Discuss Kubernetes. [Scope and access limits](SOURCES.md#c19).
  Technical cross-check: [Kubernetes container runtimes and cgroup drivers](https://kubernetes.io/docs/setup/production-environment/container-runtimes/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
