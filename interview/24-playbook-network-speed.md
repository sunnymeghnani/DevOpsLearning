# 24 — Interview practice: Fast speed test, slow application transfer

[Interview index](README.md) · [Matching handbook module](../24-playbook-network-speed.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M24-Q01 — Main question

A public speed test is fast but an application upload is slow. What is the measurement missing?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M24-Q02 — Interviewer twist

Small requests work; large transfers over a VPN stall.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Test the actual path, direction and payload size. Compare RTT, loss, retransmits, throughput, MTU/PMTUD and server storage or CPU. Use authorized bandwidth tests within a safe limit.

### Why this order

A different endpoint or short test cannot characterize the application's full path or sustained bottleneck.

### Common trap

Disabling MTU discovery or flooding a production link to prove bandwidth.

### Verification and next practice

Record same-path small/large transfer results and validate the suspected limiting layer with a reversible lab change.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C26: Cloudflare 2022: when a routing-policy change removes reachability](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/) — Cloudflare Engineering. [Scope and access limits](SOURCES.md#c26).
  Technical cross-check: [Cloudflare's routing incident analysis](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
