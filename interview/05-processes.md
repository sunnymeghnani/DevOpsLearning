# 05 — Interview practice: A process comes back after being killed

[Interview index](README.md) · [Matching handbook module](../05-processes.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M05-Q01 — Main question

A web process reappears with a new PID every time someone kills it. How do you retire it safely?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M05-Q02 — Interviewer twist

Its systemd unit is stopped, but a listening socket can activate it again.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Inspect parentage, cgroups, unit and socket associations, containers and other supervisors. Identify the application owner and dependencies. Stop the controlling mechanism with approval and preserve its prior configuration for rollback.

### Why this order

A PID is an instance, not the desired-state owner; socket activation and restart policies can recreate it.

### Common trap

An endless kill loop, or masking unrelated units.

### Verification and next practice

In a lab, show which supervisor recreates the process and demonstrate a reversible stop at that layer.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [P02: systemd.service manual via man7](https://man7.org/linux/man-pages/man5/systemd.service.5.html) — Primary manual. [Scope and access limits](SOURCES.md#p02).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
