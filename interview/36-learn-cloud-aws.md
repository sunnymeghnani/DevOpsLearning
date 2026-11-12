# 36 — Interview practice: A private cloud workload needs dependencies

[Interview index](README.md) · [Matching handbook module](../36-learn-cloud-aws.md)

Stage: Intermediate → senior decision-making. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M36-Q01 — Main question

A private-subnet application cannot fetch a build dependency. Should it get a public IP?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M36-Q02 — Interviewer twist

Only one cloud service is needed, and the organization restricts outbound access.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Identify required destinations, DNS, route, identity and endpoint policy. Compare a suitable private service endpoint with controlled NAT/proxy egress, considering availability and cost. Keep ingress requirements separate.

### Why this order

Making a workload publicly addressed is not the only way to provide its required outbound path.

### Common trap

Broad internet exposure to solve a narrow dependency problem.

### Verification and next practice

Document allowed flows and demonstrate both required access and denial of an unrelated destination in a lab.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [P04: AWS VPC security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) — Official documentation. [Scope and access limits](SOURCES.md#p04).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
