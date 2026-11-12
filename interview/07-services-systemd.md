# 07 — Interview practice: Works in a terminal, fails as a service

[Interview index](README.md) · [Matching handbook module](../07-services-systemd.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M07-Q01 — Main question

A script starts manually but systemd reports failure. What differs?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M07-Q02 — Interviewer twist

The script uses a relative path and a variable set only by your login shell.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Compare ExecStart, User, WorkingDirectory, environment, interpreter and access controls; read the unit journal and exit status. Check unit syntax before a controlled change. Service startup does not normally inherit an interactive shell profile.

### Why this order

Test the service execution context, not just the script contents.

### Common trap

Running the unit as root to hide a missing path or permission problem.

### Verification and next practice

Run the corrected unit in a lab, verify startup and restart behavior, and retain the previous unit for rollback.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [P02: systemd.service manual via man7](https://man7.org/linux/man-pages/man5/systemd.service.5.html) — Primary manual. [Scope and access limits](SOURCES.md#p02).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
