# 10 — Interview practice: Add one permission without changing the rest

[Interview index](README.md) · [Matching handbook module](../10-users-permissions-security.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Adapted from a reported Reddit interview theme (R02); follow-up and teaching guidance are original. The interview claim is unverified.

## M10-Q01 — Main question

A file owner needs read access, but all other existing permission bits must remain unchanged. What do you propose?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M10-Q02 — Interviewer twist

The application still gets permission denied after that change.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

For a controlled ordinary file, symbolic chmod u+r adds the requested bit without replacing the entire mode. Next check path traversal permissions, ACLs, effective service identity and mandatory access-control denials.

### Why this order

Minimal symbolic changes express intent; file mode is only one authorization layer.

### Common trap

Using chmod 644 as a universal add-read operation, chmod 777, or disabling SELinux.

### Verification and next practice

Use a disposable file with non-default permissions; compare before and after and separately test a denied parent directory.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [R02: Reddit: interview depth and follow-up discussion](https://www.reddit.com/r/devops/comments/1aiom83/my_top_20_devops_interview_questions_from_about/) — Interview self-report and discussion. [Scope and access limits](SOURCES.md#r02).
- [P01: GNU chmod manual via man7](https://man7.org/linux/man-pages/man1/chmod.1.html) — Primary manual. [Scope and access limits](SOURCES.md#p01).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
