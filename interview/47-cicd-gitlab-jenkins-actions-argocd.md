# 47 — Interview practice: An unchanged pipeline breaks on a mutable image tag

[Interview index](README.md) · [Matching handbook module](../47-cicd-gitlab-jenkins-actions-argocd.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M47-Q01 — Main question

A CI build fails to contact Docker after its docker:dind image refreshes. What changed without a repository commit?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M47-Q02 — Interviewer twist

The new service expects TLS, but the client still uses the previous endpoint.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Resolve the actual image digest, compare release behavior and inspect client endpoint, certificates and shared volumes. Use matching documented TLS configuration; pin and deliberately update tested images.

### Why this order

Mutable dependencies can change runtime assumptions independently of source code.

### Common trap

Disabling TLS as the universal solution or exposing a Docker daemon without authentication.

### Verification and next practice

Validate client-to-daemon authentication in an isolated runner, then test the controlled image upgrade path.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C22: Why did unchanged GitLab jobs break after a docker:dind update?](https://about.gitlab.com/blog/docker-in-docker-with-docker-19-dot-03/) — GitLab Engineering. [Scope and access limits](SOURCES.md#c22).
  Technical cross-check: [Current GitLab Docker-in-Docker guidance](https://docs.gitlab.com/ci/docker/docker_in_docker/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
