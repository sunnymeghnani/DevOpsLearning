# 52 — Interview practice: Your local command targeted production

[Interview index](README.md) · [Matching handbook module](../52-devops-day-to-day.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M52-Q01 — Main question

A developer runs a migration believed to be local, but production data changes. How should the response proceed?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M52-Q02 — Interviewer twist

The first selected backup is unsuitable and restoration must be reconsidered.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Contain further writes where appropriate, identify exact environment and command effects, preserve evidence and verify backup timestamps/content before restore. Coordinate recovery and communicate uncertainty and loss. Improve identity, target confirmation and environment separation.

### Why this order

The original mistake and a mistaken recovery target are separate failure opportunities.

### Common trap

Rerunning migrations blindly or promising full recovery before validating the backup.

### Verification and next practice

Use dummy isolated environments to test unmistakable target identification and an independently checked restore selection.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C24: Resend 2024: a local migration targeted production](https://resend.com/blog/incident-report-for-february-21-2024) — Resend Engineering. [Scope and access limits](SOURCES.md#c24).
  Technical cross-check: [Resend's incident timeline and remediation](https://resend.com/blog/incident-report-for-february-21-2024).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
