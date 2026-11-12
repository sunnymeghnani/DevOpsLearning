# 57 — Interview practice: The only database is down, and the fast fix could lose data

[Interview index](README.md) · [Matching handbook module](../57-method-protect-risk-ladder.md)

Stage: Intermediate → senior; lead extension through decision rights and communication. Suggested time: 10–15 minutes.

Provenance: Original practice scenario. Related incidents and references provide context; no claim that an employer asked this exact question.

## M57-Q01 — Main question

A single-instance database behind every internal app has exhausted its connections. Users are waiting. Walk through what you do in the first ten minutes and how you choose the next step.

Before answering, state which actions you consider reversible, how far each one can reach, and what evidence you save before acting.

## M57-Q02 — Interviewer twist

Killing idle sessions did not hold. A colleague proposes restarting the database now; there is no replica.

What changes in your plan? Explain how you make the restart as safe as possible, who decides, and what you tell users before it happens.

<details>
<summary>Answer checkpoints — open after attempting both questions</summary>

### Expected reasoning

Contain first and say so: size up who is hurt, send a first update with a next update time, name one lead and one person at the keyboard. Observe read-only (sessions, locks, the connection limit, what changed) and save it. Try the lowest rungs first: kill the offending sessions, shed load, raise the one exhausted limit if it can change live (MySQL's `max_connections` can; PostgreSQL's needs a restart, which is the next rung). A restart of the only instance is an outage and cannot be undone, so it needs a verified backup, a validated config, console access, a stated turn-back point, and the lead's decision announced with a pause for objections.

### Why this order

Protecting users and evidence comes before root cause, and each step up the ladder costs more reach and less reversibility.

### Common trap

Restarting "to see if it helps", or treating a single-box restart as low-risk because it is one command.

### Verification and next practice

Watch the same probe that showed the problem for a set time, then write the five-line note. Practise on a disposable VM: exhaust connections on purpose and rehearse the decision message.

### Senior extension

Specify blast radius, who must approve a change, a reversible mitigation, the evidence needed to restore normal operation, and what would make you stop or escalate. If no change is justified, say so.

</details>

## Sources and limits

- [C28: GitHub 2018: why did a short network fault need a long recovery?](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/) — GitHub Engineering. [Scope and access limits](SOURCES.md#c28).
  Technical cross-check: [GitHub's choice of data integrity over recovery time](https://github.blog/news-insights/company-news/oct21-post-incident-analysis/).

Technical detail also lives in the matching handbook module above. Sources support only their stated subject, not every branch of this invented scenario. Compare versions before using operational commands. For interview-format context see [Reddit and GitHub references](SOURCES.md#interview-context); these are not production instructions.

Nothing here records work you have completed. Labs are proposed, not executed. Use the [practice rubric](README.md#practice-rubric) without changing handbook progress.
