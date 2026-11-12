# 51 — Interview practice: The backup job was green, restore failed

[Interview index](README.md) · [Matching handbook module](../51-problems-databases-storage-backup.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M51-Q01 — Main question

Your only production database fails and yesterday's backup cannot be restored. What evidence should have existed before the incident?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M51-Q02 — Interviewer twist

The dump tooling version did not match the server and notifications were ineffective.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Require restore tests with compatible tooling, integrity and application checks, measured restore time and recovery point. During an incident inventory viable snapshots and logs, preserve remaining data and report loss bounds.

### Why this order

Backup completion is not proof of recoverability; restore validation must include the data and application.

### Common trap

Declaring a replicated copy a sufficient backup or restoring over the only surviving evidence.

### Verification and next practice

Restore a small isolated database with known records and verify both contents and application queries against a stated RPO/RTO.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C23: GitLab 2017: what if the backups are not usable during an outage?](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/) — GitLab Engineering. [Scope and access limits](SOURCES.md#c23).
  Technical cross-check: [GitLab's first-party recovery account](https://about.gitlab.com/blog/postmortem-of-database-outage-of-january-31/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
