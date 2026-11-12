# 20 — Interview practice: macOS resolves differently on VPN

[Interview index](README.md) · [Matching handbook module](../20-macos.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M20-Q01 — Main question

An internal hostname works in one Mac application but fails in another after VPN connection. How do you investigate?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M20-Q02 — Interviewer twist

A DNS CLI succeeds, yet the failing application's normal lookup does not.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Compare scutil --dns output, scoped resolver settings, application proxy settings and its resolution path. Test a controlled hostname-preserving address override; check both address families and VPN route scope.

### Why this order

A direct DNS query may not use the same resolver selection as the application.

### Common trap

Repeatedly flushing caches without observing which resolver is wrong.

### Verification and next practice

Record resolver and route behavior before and after VPN connection and identify the smallest relevant configuration difference.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C02: DNS tools resolve a name but curl cannot](https://stackoverflow.com/questions/74782370/dig-host-nslookup-chrome-browser-can-resolve-hostname-curl-cant) — Stack Overflow. [Scope and access limits](SOURCES.md#c02).
  Technical cross-check: [curl name resolution and controlled overrides](https://everything.curl.dev/usingcurl/connections/name.html).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
