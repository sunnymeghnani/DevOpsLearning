# 03 — Interview practice: High load, mostly idle CPU

[Interview index](README.md) · [Matching handbook module](../03-cpu-performance.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M03-Q01 — Main question

An eight-core Linux host has load 20 but little CPU utilization. Is adding CPU the right fix?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M03-Q02 — Interviewer twist

Many tasks are in D state and storage latency rose during backups.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Compare run queue, blocked tasks, per-core utilization and I/O latency over the incident window. Inspect storage or network filesystem dependencies and backup concurrency; consider cgroup limits separately.

### Why this order

Load includes runnable and uninterruptible tasks; low CPU does not rule out an overloaded dependency.

### Common trap

Treating load average as CPU percent, or treating iowait alone as proof of a particular disk failure.

### Verification and next practice

Change backup concurrency in a lab and correlate queue depth, latency and application response time.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C12: An overwhelmed DevOps intern asks where to start](https://www.reddit.com/r/devops/comments/1b5zp6m/i_got_hired_as_a_intern_help/) — Reddit. [Scope and access limits](SOURCES.md#c12).
  Technical cross-check: [Google SRE: effective troubleshooting](https://sre.google/sre-book/effective-troubleshooting/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
