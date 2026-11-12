# 21 — Interview practice: Apache moved to 81/444: is deployment finished?

[Interview index](README.md) · [Matching handbook module](../21-case-apache-443-dokploy.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M21-Q01 — Main question

Apache hosts three sites on 443. You move it to 81/444 so Dokploy can use 80/443. Will the old sites still work without explicit ports?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M21-Q02 — Interviewer twist

Traefik runs in a container, while Apache remains on the host.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Name the new public listener, then draw each hostname's route to Apache or a container backend. Configure reachable upstream addressing, protocol and trusted forwarding. Test certificates, redirects and every legacy site; preserve a cutover rollback.

### Why this order

Browsers still default to 80/443. Moving Apache alone neither forwards traffic nor makes host loopback reachable from a container.

### Common trap

Assuming all deployments can be solved solely by changing default ports.

### Verification and next practice

In a lab, verify three legacy hostnames and a new app through the public proxy, including HTTP-to-HTTPS redirects.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C05: Dokploy: published host ports versus Traefik backend ports](https://www.reddit.com/r/selfhosted/comments/1ijuwjq/dokploy_and_traefik_how_to_handle_exposed_ports/) — Reddit. [Scope and access limits](SOURCES.md#c05).
  Technical cross-check: [Traefik Docker backend-port selection](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
