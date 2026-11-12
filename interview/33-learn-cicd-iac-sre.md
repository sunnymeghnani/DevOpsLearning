# 33 — Interview practice: Two green pipelines, one broken environment

[Interview index](README.md) · [Matching handbook module](../33-learn-cicd-iac-sre.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M33-Q01 — Main question

Two pipelines deploy successfully but the older commit becomes live last. How do you make release ordering safe?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M33-Q02 — Interviewer twist

Both runs also attempt to change the same Terraform state.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Identify artifact digest, desired revision, deployment ownership and state lock owner. Serialize or supersede deployments per environment; retain immutable promotion evidence. Do not bypass an active state lock.

### Why this order

Job success is not a guarantee of correct final desired state.

### Common trap

Force-unlocking state or allowing a stale job to overwrite a newer deployment.

### Verification and next practice

Run two controlled competing releases in a lab and verify the final revision and state remain consistent.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C10: Terraform locks and overlapping CI work](https://www.reddit.com/r/Terraform/comments/1h5lx6a/) — Reddit. [Scope and access limits](SOURCES.md#c10).
  Technical cross-check: [Terraform state locking and force-unlock cautions](https://developer.hashicorp.com/terraform/language/state/locking).
- [C22: Why did unchanged GitLab jobs break after a docker:dind update?](https://about.gitlab.com/blog/docker-in-docker-with-docker-19-dot-03/) — GitLab Engineering. [Scope and access limits](SOURCES.md#c22).
  Technical cross-check: [Current GitLab Docker-in-Docker guidance](https://docs.gitlab.com/ci/docker/docker_in_docker/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
