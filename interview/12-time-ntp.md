# 12 — Interview practice: Time drift looks like an authentication failure

[Interview index](README.md) · [Matching handbook module](../12-time-ntp.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M12-Q01 — Main question

Several services reject short-lived credentials after a VM resumes. How would you test a clock hypothesis?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M12-Q02 — Interviewer twist

DNS and TCP work, but only some nodes fail.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Compare UTC time, synchronization status, peer reachability and offset across affected nodes. Check token validity windows without exposing tokens. Distinguish timezone display from clock error and examine virtualization time behavior.

### Why this order

Time-sensitive authentication can fail even with healthy network connections.

### Common trap

Disabling certificate or token expiry validation, or stepping production clocks without considering workloads.

### Verification and next practice

In an isolated lab, compare authentication before and after correcting a deliberate clock offset; record potential time-jump effects.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C09: Prometheus has samples, but Grafana looks empty](https://stackoverflow.com/questions/58572222/unable-to-fetch-data-in-grafana-even-though-prometheus-source-is-showing-the-var) — Stack Overflow. [Scope and access limits](SOURCES.md#c09).
  Technical cross-check: [Grafana panel inspector](https://grafana.com/docs/grafana/latest/visualizations/panels-visualizations/panel-inspector/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
