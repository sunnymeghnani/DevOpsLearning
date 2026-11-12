# 28 — Interview practice: Networking explanation without OSI memorization

[Interview index](README.md) · [Matching handbook module](../28-learn-networking.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M28-Q01 — Main question

Explain a browser request to a service behind a proxy, including the return path. Where can a partial failure occur?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M28-Q02 — Interviewer twist

IPv4 succeeds while IPv6 fails for the same hostname.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Trace name resolution, address choice, route, connection, TLS identity, proxy routing and backend response. Compare IPv4 and IPv6 listeners, routes and firewall paths rather than changing DNS blindly.

### Why this order

A dual-stack hostname can expose a failure affecting only some clients.

### Common trap

Deleting the AAAA record without checking the intended IPv6 service or declaring DNS healthy from one A-record query.

### Verification and next practice

Draw both address-family paths and identify an observation at every boundary.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C02: DNS tools resolve a name but curl cannot](https://stackoverflow.com/questions/74782370/dig-host-nslookup-chrome-browser-can-resolve-hostname-curl-cant) — Stack Overflow. [Scope and access limits](SOURCES.md#c02).
  Technical cross-check: [curl name resolution and controlled overrides](https://everything.curl.dev/usingcurl/connections/name.html).
- [C26: Cloudflare 2022: when a routing-policy change removes reachability](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/) — Cloudflare Engineering. [Scope and access limits](SOURCES.md#c26).
  Technical cross-check: [Cloudflare's routing incident analysis](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
