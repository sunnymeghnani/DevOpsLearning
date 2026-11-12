# 09 — Interview practice: SSH stopped after a configuration change

[Interview index](README.md) · [Matching handbook module](../09-ssh-remote-access.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M09-Q01 — Main question

You still have one SSH session, but new connections fail. What do you do before touching the service?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M09-Q02 — Interviewer twist

The server is remote and no one is physically available.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Keep the current session. Verify console or out-of-band access, inspect authentication logs and validate sshd configuration. Distinguish TCP reachability, host identity, authentication and authorization. Use a second test session before ending the first.

### Why this order

Recovery access is part of the change plan, not an afterthought.

### Common trap

Restarting blindly, opening SSH to the world, or disabling host-key checking.

### Verification and next practice

In a VM with console access, test a bad configuration safely and recover while preserving an existing session.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C26: Cloudflare 2022: when a routing-policy change removes reachability](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/) — Cloudflare Engineering. [Scope and access limits](SOURCES.md#c26).
  Technical cross-check: [Cloudflare's routing incident analysis](https://blog.cloudflare.com/cloudflare-outage-on-june-21-2022/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
