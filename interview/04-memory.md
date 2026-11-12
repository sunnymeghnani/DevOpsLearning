# 04 — Interview practice: Exit 137 with free host RAM

[Interview index](README.md) · [Matching handbook module](../04-memory.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M04-Q01 — Main question

A container exits with code 137 while the host still has available memory. What can you conclude?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M04-Q02 — Interviewer twist

The container has a memory limit; a colleague also ran a stop command near the failure.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

137 indicates SIGKILL, not its cause. Correlate container state, cgroup memory events, kernel logs and runtime events with timestamps. Distinguish limit OOM, host OOM and an operator or timeout kill.

### Why this order

Host availability and container allowance are different scopes. Evidence must distinguish competing causes.

### Common trap

Automatically increasing every memory limit or claiming every SIGKILL proves OOM.

### Verification and next practice

Reproduce a controlled limit breach in a disposable container and compare its evidence with an intentional stop.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C12: An overwhelmed DevOps intern asks where to start](https://www.reddit.com/r/devops/comments/1b5zp6m/i_got_hired_as_a_intern_help/) — Reddit. [Scope and access limits](SOURCES.md#c12).
  Technical cross-check: [Google SRE: effective troubleshooting](https://sre.google/sre-book/effective-troubleshooting/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
