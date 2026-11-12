# 13 — Interview practice: Read-only filesystem after I/O errors

[Interview index](README.md) · [Matching handbook module](../13-kernel-system.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M13-Q01 — Main question

An application loses write access and kernel logs show storage errors. Is remounting read-write enough?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M13-Q02 — Interviewer twist

The machine hosts the only copy of a database.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Preserve evidence, assess backup and redundancy, stop avoidable write pressure, and inspect the device, controller and filesystem state. Plan recovery on safe copies or offline filesystems using the platform's procedure.

### Why this order

A read-only remount may protect data from worsening corruption; restoring writes without diagnosing storage can compound loss.

### Common trap

Forcing writes, running filesystem repair on a mounted writable filesystem, or calling a snapshot a verified backup.

### Verification and next practice

Practice the recovery procedure on a disposable disk image and verify file or database integrity afterward.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C23: GitLab 2017: what if the backups are not usable during an outage?](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/) — GitLab Engineering. [Scope and access limits](SOURCES.md#c23).
  Technical cross-check: [GitLab's first-party recovery account](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
