# 22 — Interview practice: No obvious process owns an exposed port

[Interview index](README.md) · [Matching handbook module](../22-playbook-ports-inventory.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M22-Q01 — Main question

A remote client reaches a port, but ss shows no ordinary listening application on the expected host. What could explain this?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M22-Q02 — Interviewer twist

The service uses Swarm ingress or a Kubernetes NodePort.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Confirm the destination IP, protocol and network namespace. Inspect container/service publication, host-network pods, NAT and load-balancing rules. Follow the path to its actual owner before stopping anything.

### Why this order

Kernel forwarding paths can expose a service without the userspace listener you expected in that namespace.

### Common trap

Declaring a port free solely because one ss invocation shows nothing.

### Verification and next practice

Build an inventory linking public endpoint, forwarding layer, service owner, backend and logs; retest remotely after a scoped change.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C04: A localhost failure that was not automatically a networking problem](https://stackoverflow.com/questions/51442777/failing-to-connect-to-localhost-from-inside-a-container-connection-refused) — Stack Overflow. [Scope and access limits](SOURCES.md#c04).
  Technical cross-check: [Docker container networking model](https://docs.docker.com/engine/network/).
- [C17: A solved Swarm 502 thread: should you really rebuild the cluster?](https://community.traefik.io/t/502-bad-gateway-solved/2947) — Traefik Community. [Scope and access limits](SOURCES.md#c17).
  Technical cross-check: [Docker Swarm network requirements](https://docs.docker.com/engine/swarm/networking/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
