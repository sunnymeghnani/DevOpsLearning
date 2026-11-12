# 17 — Interview practice: Windows port 443 belongs to PID 4

[Interview index](README.md) · [Matching handbook module](../17-windows.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M17-Q01 — Main question

A Windows deployment cannot bind HTTPS and the listener appears under System. What should you inspect?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M17-Q02 — Interviewer twist

Several sites share HTTP.sys and have separate certificate bindings.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Inspect Get-NetTCPConnection, HTTP.sys service state, URL reservations and SSL bindings; correlate IIS sites, application pools and Event Viewer. Determine the owning registration before changing it.

### Why this order

A kernel HTTP listener can represent multiple applications; PID 4 is not a disposable web process.

### Common trap

Attempting to kill System or deleting every URL/SSL binding.

### Verification and next practice

In a Windows lab, document one site's binding, change only that site's approved configuration and test other sites afterward.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [P05: Microsoft netsh http reference](https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/netsh-http) — Official documentation. [Scope and access limits](SOURCES.md#p05).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
