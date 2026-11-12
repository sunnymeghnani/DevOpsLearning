# 48 — Interview practice: Wazuh enrollment succeeds, events do not arrive

[Interview index](README.md) · [Matching handbook module](../48-wazuh-and-security-tools.md)

Stage: Junior → intermediate; senior extension through risk and verification. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M48-Q01 — Main question

A Wazuh agent appears in the dashboard but remains disconnected. Which connections must you distinguish?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M48-Q02 — Interviewer twist

Network access allows enrollment but not the configured event-communication path.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Inspect agent and manager logs, identity/key state, compatibility and configured addresses/protocols. Enrollment and ongoing event communication are separate; compare actual configuration with version-specific defaults. Also distinguish delivery from indexing/dashboard delay.

### Why this order

Registration proves only one stage. A historical reinstall success does not prove every disconnected agent needs replacement.

### Common trap

Opening broad port ranges or assuming dashboard presence proves telemetry delivery.

### Verification and next practice

Send a benign test event in a lab and follow it from agent through manager to indexed result.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C08: Wazuh agent appears in the dashboard but never connects](https://www.reddit.com/r/Wazuh/comments/1e66dun/) — Reddit. [Scope and access limits](SOURCES.md#c08).
  Technical cross-check: [Wazuh enrollment troubleshooting and connection roles](https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/troubleshooting.html).
- [C18: Wazuh: when agent replacement solved a never-connected report](https://groups.google.com/g/wazuh/c/DmlrOS3VXt8) — Wazuh Mailing List. [Scope and access limits](SOURCES.md#c18).
  Technical cross-check: [Wazuh enrollment troubleshooting](https://documentation.wazuh.com/current/user-manual/agent/agent-enrollment/troubleshooting.html).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
