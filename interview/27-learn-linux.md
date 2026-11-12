# 27 — Interview practice: A command works for root, not the service account

[Interview index](README.md) · [Matching handbook module](../27-learn-linux.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M27-Q01 — Main question

A junior suggests running a failing task as root permanently. What do you ask first?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M27-Q02 — Interviewer twist

The file is readable, but a parent directory lacks traversal permission.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Identify the effective identity, supplementary groups, path permissions, ACLs, capabilities and mandatory controls. Compare environments and cwd. Grant the minimum required access to the correct identity.

### Why this order

Authorization and execution context must be understood before privilege is expanded.

### Common trap

Using recursive chmod 777 or treating root success as proof that the whole system needs root.

### Verification and next practice

Use a small lab directory tree to prove traversal versus file-read permissions independently.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [P01: GNU chmod manual via man7](https://man7.org/linux/man-pages/man1/chmod.1.html) — Primary manual. [Scope and access limits](SOURCES.md#p01).
- [R02: Reddit: interview depth and follow-up discussion](https://www.reddit.com/r/devops/comments/1aiom83/my_top_20_devops_interview_questions_from_about/) — Interview self-report and discussion. [Scope and access limits](SOURCES.md#r02).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
