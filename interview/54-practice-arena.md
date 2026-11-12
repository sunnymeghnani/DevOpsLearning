# 54 — Interview practice: Make a safe incident exercise

[Interview index](README.md) · [Matching handbook module](../54-practice-arena.md)

Stage: All stages: explain honestly, then deepen the evidence. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M54-Q01 — Main question

You want to practise a production-style outage without risking your host. What belongs in the exercise plan?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M54-Q02 — Interviewer twist

The source thread recommends deleting storage or rebuilding a cluster.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Use isolated disposable resources, synthetic data, spending/resource limits, a baseline and a stop condition. Inject one reversible failure with a predicted signal. Record actual observations separately from the source's report.

### Why this order

A useful lab tests a hypothesis and recovery, not merely whether a destructive command runs.

### Common trap

Reproducing a public incident on a shared or production system.

### Verification and next practice

Have someone follow the plan, confirm recovery from independent checks, then remove only the known disposable resources.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C17: A solved Swarm 502 thread: should you really rebuild the cluster?](https://community.traefik.io/t/502-bad-gateway-solved/2947) — Traefik Community. [Scope and access limits](SOURCES.md#c17).
  Technical cross-check: [Docker Swarm network requirements](https://docs.docker.com/engine/swarm/networking/).
- [C12: An overwhelmed DevOps intern asks where to start](https://www.reddit.com/r/devops/comments/1b5zp6m/i_got_hired_as_a_intern_help/) — Reddit. [Scope and access limits](SOURCES.md#c12).
  Technical cross-check: [Google SRE: effective troubleshooting](https://sre.google/sre-book/effective-troubleshooting/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
