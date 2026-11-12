# 55 — Interview practice: Cloud or on-prem is a constraint question

[Interview index](README.md) · [Matching handbook module](../55-paths-onprem-vs-cloud.md)

Stage: Intermediate → senior decision-making. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M55-Q01 — Main question

A team asks whether to migrate a workload to cloud or keep it on-prem. What do you need before recommending?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M55-Q02 — Interviewer twist

It has strict data-location constraints and an expensive low-latency dependency in the current site.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Clarify data rules, dependency latency, availability goals, operational skills, capacity, recovery and full cost including network transfer. Compare realistic operating models and a staged reversible pilot.

### Why this order

Neither location automatically supplies reliability or removes operations work.

### Common trap

Comparing only VM prices or assuming managed services eliminate backup and identity responsibilities.

### Verification and next practice

Create a decision record with measurable pilot exit criteria and a fallback plan for the dependent workload.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C28: GitHub 2018: why did a short network fault need a long recovery?](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/) — GitHub Engineering. [Scope and access limits](SOURCES.md#c28).
  Technical cross-check: [GitHub's failover and recovery analysis](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/).
- [G01: GitHub: bregman-arie/devops-exercises](https://github.com/bregman-arie/devops-exercises) — Public practice collection. [Scope and access limits](SOURCES.md#g01).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
