# 30 — Interview practice: The entrypoint file exists, but cannot run

[Interview index](README.md) · [Matching handbook module](../30-learn-docker.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M30-Q01 — Main question

A Linux container says its entrypoint is missing although the image contains it. What would you inspect before rebuilding everything?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M30-Q02 — Interviewer twist

The script was edited on Windows and its shebang carries a carriage return.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Check exact path, executable mode, shebang, line endings and interpreter availability. Separately check architecture for exec-format errors. Normalize script line endings in source control and rebuild reproducibly.

### Why this order

A missing interpreter path can surface as a misleading file error; not every startup failure is architecture mismatch.

### Common trap

Installing random interpreters or editing only a running container.

### Verification and next practice

Compare the committed script bytes and a clean rebuilt image; rerun its intended startup in a disposable environment.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C14: Why does Docker say the entrypoint is missing when the file exists?](https://stackoverflow.com/questions/76085121/docker-for-windows-entrypoint-no-such-file-exists-even-though-it-does/76087946) — Stack Overflow. [Scope and access limits](SOURCES.md#c14).
  Technical cross-check: [Git attributes: text and eol](https://git-scm.com/docs/gitattributes).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
