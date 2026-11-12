# 06 — Interview practice: Logs disagree about the incident time

[Interview index](README.md) · [Matching handbook module](../06-logs-journal.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M06-Q01 — Main question

Application logs show a failure after the proxy timeout, but the team believes it happened first. How do you reconstruct the sequence?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M06-Q02 — Interviewer twist

One source uses local time and another clock was offset.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Capture timezone, clock offset, request IDs, boot IDs and source timestamps. Separate event time from ingestion time. Bound uncertain ordering rather than inventing a precise timeline; preserve originals and redact credentials.

### Why this order

A shared identifier and clock context are stronger than sorting raw displayed timestamps.

### Common trap

Changing clocks or rotating evidence before collecting it.

### Verification and next practice

Create a timeline with confidence ranges and show which observation establishes the causal dependency.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C24: Resend 2024: a local migration targeted production](https://resend.com/blog/incident-report-for-february-21-2024) — Resend Engineering. [Scope and access limits](SOURCES.md#c24).
  Technical cross-check: [Resend's incident timeline and remediation](https://resend.com/blog/incident-report-for-february-21-2024).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
