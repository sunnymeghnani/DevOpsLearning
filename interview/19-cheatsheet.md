# 19 — Interview practice: You get only three initial checks

[Interview index](README.md) · [Matching handbook module](../19-cheatsheet.md)

Stage: Foundation → intermediate follow-up. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M19-Q01 — Main question

A user says the application is down. You have five minutes and no confirmed layer of failure. Which three observations do you request?

Before answering, state the environment/version you need, your first hypothesis, and one observation that could disprove it.

## M19-Q02 — Interviewer twist

One user can still use it; a deployment happened ten minutes ago.

What changes in your diagnosis? Explain the next safe check and what each possible result would mean.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Establish affected users and a timestamped failing request, compare an unaffected path, and inspect recent changes plus the first failing boundary. Choose commands only after stating the hypothesis each tests.

### Why this order

A bounded differential diagnosis is more useful than dumping every command in the cheat sheet.

### Common trap

Restarting all components or collecting huge logs without a question.

### Verification and next practice

Write a brief incident note with known facts, competing hypotheses, a safe next test and an update time.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C12: An overwhelmed DevOps intern asks where to start](https://www.reddit.com/r/devops/comments/1b5zp6m/i_got_hired_as_a_intern_help/) — Reddit. [Scope and access limits](SOURCES.md#c12).
  Technical cross-check: [Google SRE: effective troubleshooting](https://sre.google/sre-book/effective-troubleshooting/).
- [C27: Slack 2020: why did adding more servers not fix 503s?](https://slack.engineering/a-terrible-horrible-no-good-very-bad-day-at-slack/) — Slack Engineering. [Scope and access limits](SOURCES.md#c27).
  Technical cross-check: [Slack's technical incident account](https://slack.engineering/a-terrible-horrible-no-good-very-bad-day-at-slack/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
