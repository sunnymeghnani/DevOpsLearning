# 34 — Interview practice: Choose a learning dependency, not another tool

[Interview index](README.md) · [Matching handbook module](../34-roadmap.md)

Stage: All stages: explain honestly, then deepen the evidence. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M34-Q01 — Main question

You can run a sample container but cannot explain why its endpoint fails. Do you start Kubernetes next?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M34-Q02 — Interviewer twist

You have one hour per day and feel behind people listing twenty tools.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Choose a small networking and process-observation lab before adding orchestration. Define an observable outcome and prerequisite checks; retain an uncertainty list rather than declaring mastery.

### Why this order

A learning path should resolve a demonstrated gap, not maximize tool count.

### Common trap

Confusing watched videos or copied manifests with troubleshooting ability.

### Verification and next practice

Explain one request path without notes, break one layer in a lab and record evidence of recovery.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C12: An overwhelmed DevOps intern asks where to start](https://www.reddit.com/r/devops/comments/1b5zp6m/i_got_hired_as_a_intern_help/) — Reddit. [Scope and access limits](SOURCES.md#c12).
  Technical cross-check: [Google SRE: effective troubleshooting](https://sre.google/sre-book/effective-troubleshooting/).
- [G01: GitHub: bregman-arie/devops-exercises](https://github.com/bregman-arie/devops-exercises) — Public practice collection. [Scope and access limits](SOURCES.md#g01).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
