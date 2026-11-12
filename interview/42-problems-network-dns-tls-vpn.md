# 42 — Interview practice: Route rollback is itself a coordinated change

[Interview index](README.md) · [Matching handbook module](../42-problems-network-dns-tls-vpn.md)

Stage: Intermediate → senior decision-making. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M42-Q01 — Main question

A network policy rollout removes reachability at several sites. What must a rollback plan include?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M42-Q02 — Interviewer twist

Two engineers independently revert and reapply changes while normal management access is impaired.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Freeze competing changes, identify an incident commander and obtain backup access. Compare affected policy versions, restore in a coordinated sequence and validate routes and service reachability at each site.

### Why this order

Recovery can be prolonged by conflicting actions even when the technical rollback is known.

### Common trap

Editing broadly over the failed path without backup access or ownership.

### Verification and next practice

Run a tabletop with assigned change ownership, explicit rollback checkpoints and independent external verification.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C26: Cloudflare 2022: when a routing-policy change removes reachability](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/) — Cloudflare Engineering. [Scope and access limits](SOURCES.md#c26).
  Technical cross-check: [Cloudflare's routing incident analysis](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
