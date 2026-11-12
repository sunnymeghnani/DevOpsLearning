# 16 — Interview practice: Open security group, unreachable EC2

[Interview index](README.md) · [Matching handbook module](../16-aws-cloud.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M16-Q01 — Main question

An EC2 service is unreachable although its security group permits the port. What else matters?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M16-Q02 — Interviewer twist

The subnet lacks the expected route and a custom NACL blocks return traffic.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Inspect effective routes, public/private addressing, gateway path, security groups, NACLs, host firewall and listener. Security groups track connections; custom stateless NACLs require suitable traffic rules in both directions.

### Why this order

An allow rule at one boundary is not an end-to-end path.

### Common trap

Opening every port or assuming a public IP alone creates internet reachability.

### Verification and next practice

Draw request and reply paths, then use scoped reachability evidence to identify the exact blocking boundary.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [P04: AWS VPC security groups](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-security-groups.html) — Official documentation. [Scope and access limits](SOURCES.md#p04).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
