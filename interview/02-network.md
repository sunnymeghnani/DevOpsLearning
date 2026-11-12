# 02 — Interview practice: Ping works, application times out

[Interview index](README.md) · [Matching handbook module](../02-network.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M02-Q01 — Main question

A server answers ping but its HTTPS endpoint times out. Where do you investigate?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M02-Q02 — Interviewer twist

It works from the server itself but not from another subnet.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Trace DNS result, route, TCP connection, listening address, firewall and return path separately. Compare the exact destination IP and source location; use bounded connection tests and authorized packet capture if needed.

### Why this order

ICMP reachability does not establish a TCP listener or an allowed return path.

### Common trap

Disabling the firewall globally because ping succeeds.

### Verification and next practice

Demonstrate the same request from both locations and identify the first layer where their observations diverge.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C04: A localhost failure that was not automatically a networking problem](https://stackoverflow.com/questions/51442777/failing-to-connect-to-localhost-from-inside-a-container-connection-refused) — Stack Overflow. [Scope and access limits](SOURCES.md#c04).
  Technical cross-check: [Docker container networking model](https://docs.docker.com/engine/network/).
- [C26: Cloudflare 2022: when a routing-policy change removes reachability](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/) — Cloudflare Engineering. [Scope and access limits](SOURCES.md#c26).
  Technical cross-check: [Cloudflare's routing incident analysis](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
