# 25 — Interview practice: Which layer produced the 502?

[Interview index](README.md) · [Matching handbook module](../25-playbook-site-down.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M25-Q01 — Main question

The public site returns 502 but the application health endpoint works locally. How do you isolate the failing hop?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M25-Q02 — Interviewer twist

The reverse proxy expects HTTPS from a backend serving plain HTTP.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Correlate request IDs and proxy error logs; check route selection, upstream address, network access, TLS/SNI and backend listener. Test from the proxy's network context, not just the host shell.

### Why this order

A successful local request does not exercise the proxy-to-backend connection.

### Common trap

Increasing timeouts or disabling TLS validation before proving protocol mismatch.

### Verification and next practice

Correct the lab upstream scheme and confirm public requests, backend identity and rollback behavior.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C17: A solved Swarm 502 thread: should you really rebuild the cluster?](https://community.traefik.io/t/502-bad-gateway-solved/2947) — Traefik Community. [Scope and access limits](SOURCES.md#c17).
  Technical cross-check: [Docker Swarm network requirements](https://docs.docker.com/engine/swarm/networking/).
- [C05: Dokploy: published host ports versus Traefik backend ports](https://www.reddit.com/r/selfhosted/comments/1ijuwjq/dokploy_and_traefik_how_to_handle_exposed_ports/) — Reddit. [Scope and access limits](SOURCES.md#c05).
  Technical cross-check: [Traefik Docker backend-port selection](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
