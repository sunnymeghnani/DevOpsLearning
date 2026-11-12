# 41 — Interview practice: Deleted logs did not free space

[Interview index](README.md) · [Matching handbook module](../41-problems-linux-systems.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M41-Q01 — Main question

A service's log was deleted, but the filesystem remains full. What could retain the storage?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M41-Q02 — Interviewer twist

Another directory is a different mount and du was run without sufficient permissions.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Compare the same mount with equivalent access; inspect open deleted files and the owning service. Coordinate reopening or rotation of the identified log rather than restarting unrelated processes.

### Why this order

An open reference can retain a deleted file's blocks, but a df/du mismatch has other explanations.

### Common trap

Deleting more logs or treating one Stack Overflow hypothesis as a confirmed diagnosis.

### Verification and next practice

Use a tiny disposable test file held open by a process and observe allocation after deletion and after close.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C01: Disk usage disagrees: df versus du](https://stackoverflow.com/questions/13081888/why-do-df-and-du-display-different-used-space-values-on-an-lvm-volume) — Stack Overflow. [Scope and access limits](SOURCES.md#c01).
  Technical cross-check: [Linux unlink semantics](https://man7.org/linux/man-pages/man2/unlink.2.html).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
