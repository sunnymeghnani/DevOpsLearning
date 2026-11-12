# 37 — Interview practice: A secret appears in a successful CI log

[Interview index](README.md) · [Matching handbook module](../37-learn-security-devsecops.md)

Stage: Intermediate → senior decision-making. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M37-Q01 — Main question

A deployment token is exposed in job output. Is deleting the log sufficient?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M37-Q02 — Interviewer twist

The token can deploy to production and the build artifact may also contain it.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Contain exposure, revoke or rotate the credential, inspect its use, restrict logs/artifacts and rebuild contaminated outputs as needed. Preserve appropriately redacted incident evidence and fix the injection or logging path.

### Why this order

Removing one visible copy does not invalidate copies or undo unauthorized use.

### Common trap

Treating masking as encryption or pasting the token into another troubleshooting channel.

### Verification and next practice

Use a dummy token to test log/artifact leak prevention and verify the replacement credential has minimal scope.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [P06: GitHub Actions secure-use reference](https://docs.github.com/en/actions/reference/security/secure-use) — Official documentation. [Scope and access limits](SOURCES.md#p06).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
