# 26 — Interview practice: CrashLoopBackOff is a symptom

[Interview index](README.md) · [Matching handbook module](../26-playbook-containers-k8s.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M26-Q01 — Main question

A new pod repeatedly restarts. Which evidence should survive your investigation?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M26-Q02 — Interviewer twist

The latest logs are empty; the previous container failed before startup completed.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Capture previous-container logs, termination reason, exit code, events and probe configuration. Compare image, command, configuration, secrets and resource limits with the previous revision.

### Why this order

Restart backoff describes repeated failure, not its root cause; current logs may omit the failing instance.

### Common trap

Deleting the pod immediately or removing all probes as the final fix.

### Verification and next practice

Reproduce one startup failure in a disposable namespace and demonstrate a targeted fix with stable restarts and readiness.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [P03: Kubernetes probe semantics](https://kubernetes.io/docs/concepts/workloads/pods/probes/) — Official documentation. [Scope and access limits](SOURCES.md#p03).
- [C14: Why does Docker say the entrypoint is missing when the file exists?](https://stackoverflow.com/questions/76085121/docker-for-windows-entrypoint-no-such-file-exists-even-though-it-does/76087946) — Stack Overflow. [Scope and access limits](SOURCES.md#c14).
  Technical cross-check: [Git attributes: text and eol](https://git-scm.com/docs/gitattributes).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
