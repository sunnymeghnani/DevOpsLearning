# 01 — Interview practice: Free bytes, failed writes

[Interview index](README.md) · [Matching handbook module](../01-storage-disk.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M01-Q01 — Main question

A service cannot create a small file, although its disk has free space. What evidence would you collect first?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M01-Q02 — Interviewer twist

The target directory is a separate mount; deleting a large log did not help.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Identify the exact path and mount with findmnt; compare df -h and df -i for that path. Check quotas, permissions and read-only mount errors. If df and du differ, inspect open deleted files before blaming capacity.

### Why this order

Different limits produce similar symptoms. Match the failing filesystem before choosing cleanup, quota adjustment or file rotation.

### Common trap

Deleting random files or restarting all services without identifying the constrained resource.

### Verification and next practice

In a disposable filesystem, reproduce one capacity limit and show a successful write after only that limit is corrected.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C13: Why can an almost-empty tmp directory reject new files?](https://serverfault.com/questions/1190392/cannot-create-files-under-tmp-no-space-left-on-device) — Server Fault. [Scope and access limits](SOURCES.md#c13).
  Technical cross-check: [GNU df manual: inode reporting](https://man7.org/linux/man-pages/man1/df.1.html).
- [C01: Disk usage disagrees: df versus du](https://stackoverflow.com/questions/13081888/why-do-df-and-du-display-different-used-space-values-on-an-lvm-volume) — Stack Overflow. [Scope and access limits](SOURCES.md#c01).
  Technical cross-check: [Linux unlink semantics](https://man7.org/linux/man-pages/man2/unlink.2.html).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
