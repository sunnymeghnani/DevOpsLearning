# 43 — Interview practice: Traefik routes disappear after a Docker upgrade

[Interview index](README.md) · [Matching handbook module](../43-traefik-and-reverse-proxies.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M43-Q01 — Main question

Applications still run, but Traefik no longer discovers routes after a Docker engine update. What evidence should precede label edits?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M43-Q02 — Interviewer twist

Provider logs report an API compatibility error.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Compare engine and Traefik versions, provider connection errors and upstream compatibility evidence. An API discovery failure is different from a bad router rule. Select a supported fix and canary it before broad rollout.

### Why this order

Changing application labels cannot fix a provider unable to communicate with its control plane.

### Common trap

Copying an unverified release number or downgrading everything without preserving compatibility and rollback constraints.

### Verification and next practice

In a disposable version-matched environment, verify provider discovery and a representative route before and after the selected change.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C15: Why did a Docker upgrade remove every Traefik route?](https://github.com/traefik/traefik/issues/12253) — GitHub / Traefik. [Scope and access limits](SOURCES.md#c15).
  Technical cross-check: [Merged API-negotiation fix and rationale](https://github.com/traefik/traefik/pull/12256).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
