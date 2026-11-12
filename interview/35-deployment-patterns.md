# 35 — Interview practice: Pick a deployment pattern under constraints

[Interview index](README.md) · [Matching handbook module](../35-deployment-patterns.md)

Stage: Intermediate → senior decision-making. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M35-Q01 — Main question

A single host must run several HTTPS sites and a new application. Compare host ports, one front proxy and a separate host.

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M35-Q02 — Interviewer twist

One application requires TCP passthrough and the old services cannot tolerate downtime.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Clarify protocol, hostname/SNI support, certificates, isolation, capacity and availability requirements. Choose a public ownership model and per-service backend addresses; plan incremental cutover and rollback.

### Why this order

HTTP virtual hosting, raw TCP routing and distinct IPs have different constraints; port renumbering is not universal.

### Common trap

Assuming every protocol can be routed by an HTTP Host header.

### Verification and next practice

Produce a decision table and test each intended protocol through the chosen pattern in a lab.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C05: Dokploy: published host ports versus Traefik backend ports](https://www.reddit.com/r/selfhosted/comments/1ijuwjq/dokploy_and_traefik_how_to_handle_exposed_ports/) — Reddit. [Scope and access limits](SOURCES.md#c05).
  Technical cross-check: [Traefik Docker backend-port selection](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/).
- [C03: Containers are running, but Traefik returns 404](https://stackoverflow.com/questions/58573806/docker-swarm-with-traefik-containers-are-up-but-getting-404) — Stack Overflow. [Scope and access limits](SOURCES.md#c03).
  Technical cross-check: [Current Traefik Swarm routing reference](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/swarm/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
