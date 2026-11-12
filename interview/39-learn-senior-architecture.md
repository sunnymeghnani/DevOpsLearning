# 39 — Interview practice: Design recovery before promising high availability

[Interview index](README.md) · [Matching handbook module](../39-learn-senior-architecture.md)

Stage: Intermediate → senior decision-making. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M39-Q01 — Main question

A short network partition leaves database nodes accepting divergent writes. What does a safe recovery decision require?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M39-Q02 — Interviewer twist

Management asks for immediate failback and zero data loss.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Establish authority and fencing, map accepted writes, confirm backups and replication state, then choose a recovery direction with explicit RPO/RTO tradeoffs. Preserve divergent history for reconciliation and coordinate one decision owner.

### Why this order

Fast failover does not automatically preserve consistency; conflicting writers make recovery a data decision.

### Common trap

Promoting another writer without fencing or promising zero loss before examining the evidence.

### Verification and next practice

Tabletop the partition and produce a recovery decision record, validation criteria and communication plan.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C28: GitHub 2018: why did a short network fault need a long recovery?](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/) — GitHub Engineering. [Scope and access limits](SOURCES.md#c28).
  Technical cross-check: [GitHub's failover and recovery analysis](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
