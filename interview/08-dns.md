# 08 — Interview practice: DNS succeeds, the client still fails

[Interview index](README.md) · [Matching handbook module](../08-dns.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M08-Q01 — Main question

dig resolves an internal hostname, but an application reports name-resolution failure. Why can both be true?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M08-Q02 — Interviewer twist

The laptop uses a VPN with split DNS; an explicit address override works.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Compare the queried DNS server with the OS and application's resolver path, search domains, proxy configuration and address families. Preserve the hostname during a controlled curl --resolve test so TLS validation remains meaningful.

### Why this order

Different clients can use different resolution paths; bypassing lookup isolates only part of the request.

### Common trap

Claiming internal hostnames must be publicly registered or using insecure TLS flags as the fix.

### Verification and next practice

Record normal lookup and controlled override results from the affected client and explain what remains untested.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C02: DNS tools resolve a name but curl cannot](https://stackoverflow.com/questions/74782370/dig-host-nslookup-chrome-browser-can-resolve-hostname-curl-cant) — Stack Overflow. [Scope and access limits](SOURCES.md#c02).
  Technical cross-check: [curl name resolution and controlled overrides](https://everything.curl.dev/usingcurl/connections/name.html).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
