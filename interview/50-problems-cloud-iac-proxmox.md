# 50 — Interview practice: A provider fix reveals a destructive Terraform plan

[Interview index](README.md) · [Matching handbook module](../50-problems-cloud-iac-proxmox.md)

Stage: Intermediate → senior decision-making. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M50-Q01 — Main question

You repair an aliased provider mapping, but Terraform now proposes unexpected deletes. Do you apply?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M50-Q02 — Interviewer twist

The resources were imported across two regions and the default provider changed.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Stop and confirm backend, workspace, identity, region, module provider bindings, resource addresses and state associations. Compare the plan with actual resources; take secure state backups before any approved state operation.

### Why this order

A syntactically valid provider configuration can still target the wrong identity or region.

### Common trap

Applying to see what happens, editing raw state casually or treating the forum's remaining destructive plan as solved.

### Verification and next practice

Reproduce provider binding and import behavior with disposable resources; require a reviewed expected plan before changes.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C20: Terraform multi-region import: why does fixing a provider reveal destruction?](https://discuss.hashicorp.com/t/terraform-catch-22-lack-of-default-provider-causes-error-default-provider-breaks-per-region-providers/62078) — HashiCorp Discuss. [Scope and access limits](SOURCES.md#c20).
  Technical cross-check: [Terraform provider inheritance and explicit mappings](https://developer.hashicorp.com/terraform/language/modules/develop/providers).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
