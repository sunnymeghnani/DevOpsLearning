# 44 — Interview practice: Runner cleanup targeted the wrong runtime

[Interview index](README.md) · [Matching handbook module](../44-problems-docker-swarm-registry.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M44-Q01 — Main question

The CI runner is out of storage although a Docker cleanup freed little. What ownership question matters?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M44-Q02 — Interviewer twist

Jobs run as a separate user through rootless Podman.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Identify runtime, user, storage root, mount and active jobs before choosing retention or cleanup. Separate caches, images, build outputs and persistent volumes; inventory anything proposed for removal.

### Why this order

Docker and another user's rootless storage are not the same resource pool.

### Common trap

Running destructive global reset commands from a forum without recording what they remove.

### Verification and next practice

Use a disposable runner to measure storage per job and test a scoped retention policy without losing persistent data.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C07: GitLab runner disk fills up in a different runtime context](https://www.reddit.com/r/gitlab/comments/1adzlb2/gitlab_runner_out_of_space/) — Reddit. [Scope and access limits](SOURCES.md#c07).
  Technical cross-check: [Podman reset scope and warnings](https://docs.podman.io/en/latest/markdown/podman-system-reset.1.html).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
