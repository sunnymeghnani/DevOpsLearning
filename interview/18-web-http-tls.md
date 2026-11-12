# 18 — Interview practice: Correct IP, wrong HTTPS site

[Interview index](README.md) · [Matching handbook module](../18-web-http-tls.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M18-Q01 — Main question

A hostname resolves to the right server, but the browser gets the wrong certificate or virtual host. Where is routing decided?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M18-Q02 — Interviewer twist

A direct IP request works only with certificate verification disabled.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Inspect TLS SNI, certificate names, HTTP Host, selected virtual host and upstream routing. Test the intended hostname with a controlled address override and valid trust. Keep handshake and HTTP routing evidence separate.

### Why this order

Reaching an IP does not select the intended certificate or application.

### Common trap

Treating curl -k success as a production TLS fix.

### Verification and next practice

Verify the expected certificate and response for each hostname, plus an intentional unmatched-host request.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C02: DNS tools resolve a name but curl cannot](https://stackoverflow.com/questions/74782370/dig-host-nslookup-chrome-browser-can-resolve-hostname-curl-cant) — Stack Overflow. [Scope and access limits](SOURCES.md#c02).
  Technical cross-check: [curl name resolution and controlled overrides](https://everything.curl.dev/usingcurl/connections/name.html).
- [C03: Containers are running, but Traefik returns 404](https://stackoverflow.com/questions/58573806/docker-swarm-with-traefik-containers-are-up-but-getting-404) — Stack Overflow. [Scope and access limits](SOURCES.md#c03).
  Technical cross-check: [Current Traefik Swarm routing reference](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/swarm/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
