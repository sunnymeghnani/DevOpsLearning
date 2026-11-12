# 14 — Interview practice: Published port, connection refused

[Interview index](README.md) · [Matching handbook module](../14-docker-containers.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M14-Q01 — Main question

Docker shows a host-port mapping, but requests still fail. What does that mapping prove?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M14-Q02 — Interviewer twist

The application listens only on 127.0.0.1 inside its container.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Check process health, actual listener, container address, mapped destination port and the client namespace. EXPOSE is metadata, not proof of a running listener. Bind the application appropriately and restrict host publication to intended clients.

### Why this order

Port translation cannot create an application listener or make container loopback reachable from another namespace.

### Common trap

Adding host networking before understanding the topology.

### Verification and next practice

Test from the container, a peer on its network and the intended host interface, with an expected result for each.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C04: A localhost failure that was not automatically a networking problem](https://stackoverflow.com/questions/51442777/failing-to-connect-to-localhost-from-inside-a-container-connection-refused) — Stack Overflow. [Scope and access limits](SOURCES.md#c04).
  Technical cross-check: [Docker container networking model](https://docs.docker.com/engine/network/).
- [C05: Dokploy: published host ports versus Traefik backend ports](https://www.reddit.com/r/selfhosted/comments/1ijuwjq/dokploy_and_traefik_how_to_handle_exposed_ports/) — Reddit. [Scope and access limits](SOURCES.md#c05).
  Technical cross-check: [Traefik Docker backend-port selection](https://doc.traefik.io/traefik/reference/routing-configuration/other-providers/docker/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
