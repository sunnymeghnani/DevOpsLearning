# 11 — Interview practice: A package lock during emergency patching

[Interview index](README.md) · [Matching handbook module](../11-packages.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M11-Q01 — Main question

A package manager says another process holds its lock. How do you proceed?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M11-Q02 — Interviewer twist

A security update is urgent, and an unattended update may still be active.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Identify the lock owner and its progress before acting. Check package-manager logs, disk capacity and service dependencies. Wait or coordinate with the running job; use documented recovery only after confirming no active transaction.

### Why this order

A lock protects shared package state; deleting its file does not safely terminate the transaction.

### Common trap

Removing lock files as the first step or interrupting installation without a recovery plan.

### Verification and next practice

In a disposable VM, document normal lock contention and the evidence required before any recovery operation.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C10: Terraform locks and overlapping CI work](https://www.reddit.com/r/Terraform/comments/1h5lx6a/) — Reddit. [Scope and access limits](SOURCES.md#c10).
  Technical cross-check: [Terraform state locking and force-unlock cautions](https://developer.hashicorp.com/terraform/language/state/locking).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
