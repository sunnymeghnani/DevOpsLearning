# 52 — DevOps Day to Day: How Engineers Work, Fail and Learn

This module is about the job itself rather than one tool: what a DevOps, SRE or sysadmin day and week really look like from fresher to lead, the tickets and requests that fill them, on-call and incidents, changes that go wrong, working with developers and managers, documentation, and how engineers keep learning while they work. The 40 most common day-to-day situations are written as problem entries you can practise. The material comes from the Google SRE book chapters on toil, on-call, incidents and postmortems, DORA's research on well-being and delivery, public postmortems (Dan Luu's collection, GitLab's 2017 database outage), Ask HN threads on on-call life and practitioner write-ups on dev.to; Stack Overflow, Server Fault and Reddit are reachable through search links. Every command is documented for your own lab VM or servers. Nothing here was executed on a live system.

---

## 0. How to use this module

Most of a DevOps engineer's week is not heroic debugging. It is a stream of requests (access, ports, DNS, deploys, certificates), a few small changes, many interruptions, and now and then a real incident. What separates a fresher from a senior is less the tools they know and more how they handle that stream: which questions they ask before acting, how they make a change safe, how they talk during an incident, and whether each ticket leaves the team a little better off. Use the part that matches your stage, then move up.

| Stage | Level | Read first | You are there when |
|---|---|---|---|
| Fresher | L0 Foundations | sections 1 and 2, entries 3.1, 4.1, 7.1, 14.2 and 16.2 | you take a ticket, ask the four intake questions, and close it with a note a colleague can follow |
| Junior | L1 Operator | sections 2–8 and every L1 entry | you close access, port, DNS, certificate and disk tickets alone and safely, and every closed ticket leaves a note |
| Mid-level | L2 Troubleshooter | sections 5, 9 and 10 | you roll back a bad deploy without being told, lead a small incident and write the postmortem |
| Senior | L3 Platform | sections 10–13 | toil is measured and falling, changes follow a template, and other people run your runbooks at 3 AM |
| Senior/Lead | L4 SRE | sections 9, 15–17 and the Self-check | the on-call rotation is sustainable, postmortems are blameless and acted on, and juniors grow on a plan you wrote |

**How each problem entry is laid out:** a one-line card (what you see, where, level and career stage, how common it is), then *Why it happens*, *Diagnose* (commands or the facts to collect, with a realistic sample output), *What the output tells you*, *Fix*, *Why this fix works* (including what not to do), *Prevent it*, *Next step* (handbook module, KodeKloud course, docs) and *Community threads* (verified links plus search links). Process problems such as toil or burnout use the same layout: the "commands" are the queries and counts that turn a feeling into evidence.

**How to practise:** use two lab VMs with Ubuntu 24.04 (dokploy-1 with Dokploy installed, and a small dokploy-2) plus a free GitLab project. Turn each entry into a ticket on a personal board, ask a friend to file tickets at you in the words a developer would use, and work them with a timer. For the technical entries, break the lab on purpose and fix it using only the entry. For the process entries, write the reply, the change record or the postmortem the entry asks for. After each one, write a five-line note: symptom, evidence, cause, fix, prevention. Never practise on production.

**Placeholders and examples:** UPPERCASE words are placeholders (HOST, USER, APP, TICKET, CONTAINER). The examples use dokploy-1 (192.0.2.10, private 10.10.0.10) as the Dokploy manager that also runs Prometheus and Grafana, dokploy-2 (192.0.2.20, private 10.10.0.20) as a second server, runner-1 (10.10.0.30) as the GitLab runner, 203.0.113.10 as the public address of shop.example.com, gitlab.example.com and harbor.example.com behind your private CA, ticket keys like OPS-1423, and the generic users ops and deploy.

> 📚 **Study path:** KodeKloud [*Fundamentals of SRE*](https://kodekloud.com/courses/fundamentals-of-sre) (Incident Management → Managing Complexity, Risk and Toil) → handbook [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) §7 SRE practice and [Career ladder](40-career-ladder.md) §11 Soft skills → the Google SRE book chapters on [toil](https://sre.google/sre-book/eliminating-toil/), [on-call](https://sre.google/sre-book/being-on-call/), [incidents](https://sre.google/sre-book/managing-incidents/) and [postmortems](https://sre.google/sre-book/postmortem-culture/) → daily reps on [KodeKloud Engineer](https://engineer.kodekloud.com/) or [100 Days of DevOps](https://kodekloud.com/100-days-of-devops) → the 90-day plan in section 17.

---

## 1. A realistic day and week by career stage

### The shape of a normal week

Ops work arrives in two streams. The **planned** stream is project work: a new Dokploy server, a Harbor upgrade, an Ansible role, a monitoring dashboard. The **unplanned** stream is interrupts: tickets, chat questions, alerts, incidents and "can you just" requests. The unplanned stream always wins in the short term, because someone is blocked or something is down, so the planned stream only moves if you protect it on purpose.

Google's SRE teams cap operational work at 50% of each engineer's time and report that the average engineer spends about a third of their time on toil, with individuals anywhere from almost none to 80%. Small on-prem teams often sit far above that, which is why section 11 is about measuring and cutting it.

A typical week on a small team looks like this:

| Day | Morning | Afternoon |
|---|---|---|
| Monday | on-call handoff (what fired, what is still open), plan the week | ticket queue, small changes in staging |
| Tuesday | standup, project work in a protected block | change window: reviewed changes to production |
| Wednesday | standup, ticket queue | pairing with developers, design or architecture review |
| Thursday | standup, project work | change window, postmortem review if there was an incident |
| Friday | toil review, documentation, learning | no risky changes after lunch; tidy notes, update runbooks |

Here is a rough share of the week by stage. It is a common shape, not a measurement, and your company will differ:

| Stage | Tickets and requests | Project work | On-call and incidents | Meetings, reviews, mentoring | Learning |
|---|---|---|---|---|---|
| Fresher | 35% | 10% (shadowing) | 5% (shadowing) | 15% | 35% |
| Junior | 45% | 20% | 10% | 10% | 15% |
| Mid-level | 30% | 35% | 15% | 10% | 10% |
| Senior | 15% | 45% | 10% | 20% | 10% |
| Lead | 10% | 25% | 10% (escalations) | 45% | 10% |

### Fresher · L0: a day

- **09:30** standup: say what you did, what you will do, and what blocks you. Keep it under a minute.
- **09:45** read the on-call handoff and the team channel. Write down every term you don't know.
- **10:00** shadow a senior on an access request (entry 3.1). Watch which questions they ask before touching anything.
- **11:00** your own small ticket: add a DNS record for a staging app (entry 4.2), with the senior reviewing before you apply it.
- **13:30** one KodeKloud lab or a [Linux Challenges](https://kodekloud.com/courses/linux-challenges) task linked to something you saw this morning.
- **15:00** pair on a disk warning (entry 7.1). You type and they explain.
- **16:30** write two five-line notes in your ticket journal (section 14) and ask one question you saved during the day.

What good looks like: you ask before you act, you write things down, and you never change production alone.

### Junior · L1: a day

- **09:15** look at the overnight alerts and the main dashboards before standup, so you can report anything odd.
- **09:30** standup.
- **09:45** ticket queue: an access request (3.1), an "open port 8080" request that you turn into a Traefik route (4.1), and a check of which certificates expire this month (6.1).
- **11:30** runner-1 warns at 85% disk. You clean it safely and file a follow-up to fix the cause (7.1).
- **14:00** change window: patch the staging hosts, verify them, and write the change record (section 10).
- **15:30** a developer asks why their pipeline is red. You read the first error in the job log together (5.3).
- **17:00** update tickets and write the handoff note for tomorrow.

What good looks like: tickets close with evidence, small changes are safe and reversible, and you escalate after a time box instead of guessing for hours.

### Mid-level · L2: an on-call week

- **Monday** take the pager at the handoff meeting. Read the open incidents, the change calendar and any alerts that fired last week.
- **Tuesday 07:50** paged: 5xx errors on shop.example.com right after a deploy. You roll back first (5.2), post status updates every 30 minutes, and the site is healthy by 08:20.
- **Tuesday afternoon** write the incident timeline while it is fresh. Project work waits.
- **Wednesday** a noisy disk alert pages twice at night. You tune it to a trend alert and delete one alert nobody acts on (9.2).
- **Thursday** run the blameless postmortem review and agree three action items with owners (9.5).
- **Friday** hand the pager over with a written summary: pages, actions, what is still open.

What good looks like: you mitigate before you investigate, keep people informed without being asked, and leave the system better after every page.

### Senior · L3: a week

- **Monday** review the change calendar and the risky changes in it. Comment on two merge requests for Ansible and Traefik.
- **Tuesday** write a design note for moving Harbor to highly available storage, with the options, costs and the recommendation.
- **Wednesday** architecture review with the developers of a new service: health checks, logs, metrics, how it deploys and how it rolls back.
- **Thursday** run a game day: break dokploy-2 on purpose and watch a junior handle it (section 9).
- **Friday** toil review: the top three repeat tickets this month. Automate one, and write a runbook for the next.

What good looks like: fewer tickets next month than this month, and other people can do what only you could do last quarter.

### Lead · L4: a week

- **Monday** on-call health: pages per shift, pages outside working hours, the share of actionable pages, and open postmortem actions.
- **Tuesday** roadmap with your manager: what the team will stop doing to make room for reliability work.
- **Wednesday** one-to-ones and the onboarding plan for a new junior (section 17).
- **Thursday** postmortem review across teams, and a decision on whether a service is ready for production.
- **Friday** budget and capacity: next quarter's hardware or cloud spend, backed by utilisation data (8.1, 8.2).

What good looks like: the rotation is sustainable, the team says no with options rather than heroics, and the same incident does not happen twice.

### On-prem and cloud days differ

The rhythm is the same, but the tickets change with where the servers live. Pick 🏢 On-prem or ☁️ Cloud in the top bar to see one side, or Both.

<div class="env" data-env="onprem" markdown="1">

**On-prem days** include work that cloud teams never see: a disk or PSU replacement with the data-centre team, Proxmox capacity before a new VM, firewall requests to the network team (who own the edge), internal DNS and the private CA for harbor.example.com and gitlab.example.com, NTP inside a closed network, monthly patch windows agreed with the business, and hardware purchases planned months ahead. Capacity is fixed until you buy more, so "do we have room for this?" is a real question every week. Most of your evidence comes from your own Prometheus, Wazuh and Proxmox graphs.

</div>

<div class="env" data-env="cloud" markdown="1">

**Cloud days** swap hardware for API limits and money: IAM role requests, security group and NACL changes, service quota increases, AWS Health notices about scheduled maintenance, Cost Explorer questions from finance, RDS minor-version upgrades forced by the provider, and tagging clean-ups. Capacity is elastic, so the hard question moves from "do we have room?" to "what will this cost, and who approved it?". Your evidence comes from CloudWatch, CloudTrail and Cost Explorer as well as your own monitoring.

</div>

[On-prem vs cloud paths](55-paths-onprem-vs-cloud.md) goes deeper on how the two careers differ.

---

## 2. The ticket and request taxonomy

### Four questions for every ticket

Before touching anything, answer these four. A fresher who asks them looks like a junior, and a junior who asks them looks like a mid-level engineer.

1. **What outcome is needed?** Ask for the outcome, not the solution. "Open port 8080" is a solution; "the partner's webhook must reach our app" is the outcome, and it usually has a safer answer.
2. **Who is asking, and who approves?** The requester is not always the owner. Production access, firewall openings and restores need the service owner's approval in the ticket, not in a DM.
3. **By when, and why then?** A real deadline (a release, an audit, a customer) changes the priority. "ASAP" without a reason does not.
4. **What is the risk, and how do I undo it?** Write the rollback before the change. If you can't undo it, it needs review.

### The request types at a glance

| Type | Sounds like | Ask first | Risk | Approver | Entry |
|---|---|---|---|---|---|
| Access | "give me prod access" | which task, which system, until when? | high | service owner and manager | 3.1 |
| Secrets | "here's the DB password" in chat | where else was it pasted? | high | security | 3.2 |
| Joiner or leaver | an HR email, often late | which systems, which shared accounts? | high | manager | 3.3 |
| Port or firewall | "open 8080 on prod" | from where, to what, why? | medium to high | owner and security | 4.1 |
| DNS, domain, TLS | "we need app.example.com" | which app, which port, which health path? | low to medium | owner | 4.2 |
| Egress or partner | "the partner API times out from prod" | which IP does the partner allow? | medium | security | 4.3 |
| Deploy or release | "deploy this today" | is it merged, and did CI pass? | medium to high | release owner | 5.1 |
| Broken pipeline | "CI is red" | what is the first error line? | low, but blocking | none | 5.3 |
| Certificate | "the site says not secure" | which hostname, which certificate? | high once expired | none | 6.1 |
| Disk or memory | an alert | how fast is it growing? | medium | none | 7.1, 7.3 |
| Slow app | "the site is slow" | slow for whom, since when, how slow? | medium | none | 7.2 |
| Restore | "we need yesterday's data" | which data, as of what time? | high | data owner | 7.4 |
| Cost or capacity | "why is the bill so high?" | which period, which account? | low | manager | 8.1, 8.2 |
| Patching | "are we affected by this CVE?" | which versions, exposed where? | medium | owner or change board | 8.3 |

### A ticket reply that closes the loop

A ticket is not done when the change is made. It is done when the requester can see what changed, how it was verified and how to undo it. Use this shape:

```text
Summary:   Added Traefik route app.example.com -> app:3000 with a Let's Encrypt certificate (OPS-1423).
What I did: Created the A record app.example.com -> 203.0.113.10 (TTL 300); added the domain
            in Dokploy, container port 3000, HTTPS on.
Verified:  curl -sI https://app.example.com/healthz -> HTTP/2 200; certificate issued by Let's Encrypt,
            valid until 2027-01-02.
Rollback:  Remove the domain in Dokploy, delete the A record.
Follow-up: Port 8080 was NOT opened; the app is reachable only through Traefik (see 4.1).
Note:      wiki/runbooks/new-app-domain.md updated.
```

### Standard, normal and emergency changes

Most teams sort requests into three change types, even if they don't use these names:

- **Standard:** pre-approved, low risk and repeatable, with a runbook. Examples: add a DNS record in staging, add an SSH key from the approved list, renew a certificate.
- **Normal:** reviewed before it happens, by a peer or a change board, with a plan, a verification step and a rollback. Examples: a firewall opening in production, a Traefik upgrade, a database migration.
- **Emergency:** done during an incident to restore service, recorded as it happens and reviewed afterwards. Examples: a rollback, failing over a database, blocking an abusive IP range.

DORA's research finds that heavyweight approval boards slow delivery without making it safer, while a clear, lightweight process with peer review improves both speed and stability and lowers burnout. Aim to turn as many request types as you can into standard changes with a runbook, and later into self-service.

---

## 3. Access and secrets requests

Access tickets look simple and carry the most risk: every grant you make is a door someone can use after the task is over. The pattern in all three entries is the same: the smallest role that meets the outcome, granted through a group in Git or SSO, with an end date.

### 3.1 "Give me production access"

> **Seen as:** "can you give me sudo on prod, just for today?" in a DM · **Where:** SSH and sudo on Ubuntu hosts, the Dokploy panel, GitLab roles, database accounts, AWS IAM · **Level:** [L1 · Junior] · **How common:** the most frequent ticket in most ops queues, and a perennial r/sysadmin argument about least privilege versus speed

**Why it happens:** the developer has a task (read logs, check a config, run a migration) and asks for the widest access because it is the quickest thing to ask for. Without defined roles every grant is improvised: a personal key in authorized_keys, a sudoers line, a shared admin password. Nobody removes them later, so access only ever grows, and the next audit finds a dozen people with root on production.

**Diagnose:**

```bash
# What does the person already have? (on the target host)
id dev.alice
sudo -l -U dev.alice
getent group sudo prod-readonly prod-deploy
# Whose keys can log in as the shared deploy user? (last field = key comment)
sudo awk '{print $NF}' /home/deploy/.ssh/authorized_keys
```

```text
uid=1104(dev.alice) gid=1104(dev.alice) groups=1104(dev.alice),1002(prod-readonly)
User dev.alice may run the following commands on dokploy-1:
    (root) NOPASSWD: /usr/bin/journalctl, /usr/bin/docker logs *
sudo:x:27:ops
prod-readonly:x:1002:dev.alice,dev.bob
prod-deploy:x:1003:deploy
alice@laptop
ci-deploy@runner-1
old-contractor@laptop
```

**What the output tells you:** alice can already read logs through prod-readonly, which covers her stated task ("see why the worker crashes"). The real finding is in the shared deploy user: a key labelled old-contractor still works. Handle that with entry 3.3 and mention it in the ticket.

**Fix:** answer the outcome with the smallest role, time-boxed, through a group managed in Git.

```yaml
# ansible/group_vars/prod.yml — access lives in Git and changes by merge request
access_grants:
  - user: dev.alice
    group: prod-readonly        # journalctl and docker logs only
    ticket: OPS-1431
    approved_by: shop-owner
    expires: 2026-10-11         # a nightly job removes expired grants
```

```text
Reply: You already have log access through prod-readonly (journalctl, docker logs).
Grafana > Explore > Loki {app="worker"} shows the same logs without SSH.
The migration runs as the CI job "migrate" once the owner approves it in OPS-1431.
```

<div class="env" data-env="onprem" markdown="1">

**On-prem:** roles are Linux groups (prod-readonly, prod-deploy) and sudoers drop-ins pushed by Ansible, plus roles in Dokploy, GitLab and Grafana. If you have LDAP or FreeIPA, grant through its groups so one change covers every host.

</div>

<div class="env" data-env="cloud" markdown="1">

**Cloud:** roles are IAM roles assumed through SSO (IAM Identity Center permission sets) with short-lived credentials, never long-lived access keys for people. Prefer SSM Session Manager to SSH: no inbound port 22, and every session is logged in CloudTrail.

</div>

**Why this fix works:** a group is reviewable and removable in one place, and an expiry date ends the grant even if everyone forgets. Offering logs in Grafana or a CI job often removes the need for a shell at all. Don't add a personal sudoers line by hand, don't share the deploy user's key, and never hand out "temporary" root without an end date in writing.

**Prevent it:** a short role catalogue per system (read-only, deploy, admin), grants only through Git or SSO groups, expiry dates by default, and a quarterly access review where each owner confirms who still needs what.

**Next step:** [Users, permissions and security](10-users-permissions-security.md) · [Security & DevSecOps](37-learn-security-devsecops.md) · [On-prem vs cloud paths](55-paths-onprem-vs-cloud.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* — the users, groups and sudo lessons · [Ubuntu Server docs](https://ubuntu.com/server/docs)

**Community threads:** [DORA capabilities](https://dora.dev/capabilities/) (lightweight, clear processes beat ad-hoc ones) · Search: [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=developers+production+access&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=temporary+sudo+access+expire) · [Stack Overflow](https://stackoverflow.com/search?q=least+privilege+production+access+developers)

### 3.2 A secret was pasted in chat or committed

> **Seen as:** a GitLab token `glpat-…` posted in #dev-help, an `AWS_SECRET_ACCESS_KEY` in a committed `.env`, or a secret-detection job that fails the pipeline · **Where:** chat, tickets, Git history, CI job logs · **Level:** [L1 · Junior] · **How common:** constant; GitLab and GitHub both ship secret push protection because it happens every day

**Why it happens:** someone debugs under pressure and pastes the whole config, `.env` is not in `.gitignore`, a script echoes a variable into the CI log, or there is simply no password manager or vault to share secrets through. Deleting the message or force-pushing does not un-leak anything: chat history, clones, forks, CI caches and backups still hold the value.

**Diagnose:**

```bash
# Where is it in history? Search by prefix; never paste the full secret into tools or tickets
git log --all -S 'glpat-' --format='%h %an %ad %s' --date=short
# Scan the whole history with gitleaks (redacted output)
docker run --rm -v "$PWD:/repo" ghcr.io/gitleaks/gitleaks:latest git --redact -v /repo
```

```text
9c41e2a dev.bob 2026-10-02 add deploy script
Finding:     TOKEN=REDACTED
RuleID:      gitlab-pat
File:        scripts/deploy.sh
Line:        4
Commit:      9c41e2a
WRN leaks found: 1
```

**What the output tells you:** the token was committed two days ago and is already pushed, so treat it as compromised whatever the repository's visibility. The next question is whether anyone used it: check the token's "last used" date in GitLab and the audit events, or CloudTrail for an AWS key.

**Fix:** revoke first, check for misuse second, clean up last.

```bash
# 1. Revoke the token now (GitLab: User settings > Access tokens > Revoke) and create a replacement
# 2. Store the replacement as a masked, protected CI/CD variable or in Vault, never in the repo
# 3. Review what the old token did while exposed (GitLab admin: Monitoring > Audit events)
# 4. Only then rewrite history, if your policy requires it, and tell everyone to re-clone
#    (filter-repo is not part of git: sudo apt install git-filter-repo)
git filter-repo --replace-text replacements.txt     # file contains: glpat-OLDVALUE==>REDACTED
```

**Why this fix works:** rotation is the only step that makes the leaked value useless; rewriting history cannot reach clones, forks or CI caches. Revoking before you investigate also stops any ongoing misuse. Don't just delete the chat message and move on, and don't skip rotation because "the repo is private".

**Prevent it:** gitleaks as a pre-commit hook and a CI job, GitLab secret push protection, `.env` in every `.gitignore` template, short-lived tokens with expiry dates, and one team rule: secrets travel through the password manager or vault, never through chat.

**Next step:** [Security & DevSecOps](37-learn-security-devsecops.md) §5 Secrets management · [Wazuh & security tools](48-wazuh-and-security-tools.md) (Vault entries) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — variables · [gitleaks](https://github.com/gitleaks/gitleaks) · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** [gitleaks project](https://github.com/gitleaks/gitleaks) · Search: [Stack Overflow](https://stackoverflow.com/search?q=remove+password+from+git+history) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=secret+committed+git+rotate&restrict_sr=1) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=leaked+token+revoke&restrict_sr=1)

### 3.3 A leaver still has access

> **Seen as:** an audit finds old-contractor's key on two hosts, or a leaver's personal access token still runs a nightly CI job · **Where:** authorized_keys, GitLab tokens and deploy keys, VPN profiles, Harbor robot accounts, shared passwords, cloud keys · **Level:** [L1 · Junior] · **How common:** a classic r/sysadmin offboarding thread and one of the first findings in any ISO 27001 or SOC 2 audit

**Why it happens:** keys were copied to hosts by hand, so nobody knows where they all are. Automation runs on a person's token, so revoking it would break production and nobody dares. Shared passwords were never rotated. HR tells IT late or not at all.

**Diagnose:**

```bash
# Which hosts still hold the key? (ad-hoc Ansible over the whole inventory)
ansible all -i inventory/prod.ini -b -m shell \
  -a "grep -l 'old-contractor' /home/*/.ssh/authorized_keys /root/.ssh/authorized_keys 2>/dev/null || true"
# Was it used after the person left? Logs show fingerprints, not comments
grep old-contractor /home/deploy/.ssh/authorized_keys > /tmp/leaver.pub && ssh-keygen -lf /tmp/leaver.pub
sudo journalctl -u ssh --since '-30 days' | grep 'Accepted publickey' | grep 'SHA256:Qm4x0c'
```

```text
dokploy-1 | CHANGED | rc=0 >>
/home/deploy/.ssh/authorized_keys
dokploy-2 | CHANGED | rc=0 >>
/home/deploy/.ssh/authorized_keys
runner-1 | CHANGED | rc=0 >>

256 SHA256:Qm4x0cT1d0cExampleFingerprint old-contractor@laptop (ED25519)
Sep 12 22:41:07 dokploy-1 sshd[48211]: Accepted publickey for deploy from 198.51.100.77 port 53122 ssh2: ED25519 SHA256:Qm4x0cT1d0cExampleFingerprint
```

**What the output tells you:** the key is on two hosts, and it logged in on 12 September from 198.51.100.77, after the contract ended on 31 August. This is no longer tidying up; it is a possible security incident. Stop, preserve the logs and bring in security (section 9) before you change anything else.

**Fix:** remove the key everywhere from one list in Git, then work the checklist.

```yaml
# playbooks/revoke-keys.yml — the list of revoked keys lives in Git
- hosts: all
  become: true
  tasks:
    - name: Remove revoked keys from the deploy user
      ansible.posix.authorized_key:
        user: deploy
        key: "{{ item }}"
        state: absent
      loop: "{{ revoked_keys }}"
```

```text
Leaver checklist (OPS-1450): SSO/LDAP account disabled · VPN profile revoked · SSH keys removed (playbook above)
· GitLab user blocked (not deleted, to keep history) · personal access tokens and deploy keys revoked
· Harbor robot accounts rotated · Dokploy, Grafana, Wazuh users removed · shared passwords rotated
· cloud access keys deleted · automation moved to service accounts first
```

**Why this fix works:** one list applied everywhere cannot miss a host the way a manual sweep does. Blocking rather than deleting the GitLab user keeps the audit trail. Moving automation to service accounts first means revocation doesn't break production, which removes the reason people hesitate. Don't delete accounts before you know what runs under them.

**Prevent it:** a joiner-mover-leaver checklist triggered by HR, SSO wherever the tool supports it, service or robot accounts for all automation, central key management (Ansible or SSH certificates), and a Wazuh file-integrity rule on authorized_keys so new keys raise an alert.

**Next step:** [SSH and remote access](09-ssh-remote-access.md) · [Users, permissions and security](10-users-permissions-security.md) · [Wazuh & security tools](48-wazuh-and-security-tools.md) · KodeKloud: *Ansible Basics Course* — Playbooks · [Ansible docs](https://docs.ansible.com/)

**Community threads:** [Ansible docs](https://docs.ansible.com/) · Search: [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=offboarding+checklist&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=remove+ssh+key+from+all+servers) · [Stack Overflow](https://stackoverflow.com/search?q=ansible+remove+authorized_key+all+hosts)

---

## 4. Network and domain requests

Network tickets almost always arrive phrased as a solution ("open a port", "whitelist this IP"). Translate them back into an outcome, then pick the safest path to it. On this stack that path usually runs through Traefik on 443.

### 4.1 A developer asks you to open a port

> **Seen as:** "please open 8080 on dokploy-1 so the partner can call our webhook" · **Where:** UFW on Ubuntu, Docker published ports, Traefik, AWS security groups · **Level:** [L1 · Junior] · **How common:** the most common network ticket; Docker's documentation has a whole page on published ports bypassing UFW because it catches so many teams

**Why it happens:** the request names a solution. The real need is usually "make this HTTP app reachable", which on this stack belongs behind Traefik on 443 with a hostname, TLS, access logs and CrowdSec. A raw 8080 is a second, unencrypted door that skips all of that. Worse, if the container already publishes `-p 8080:8080`, the port is open to the world whatever UFW says, because Docker's NAT rules are evaluated before UFW's.

**Diagnose:**

```bash
sudo ss -ltnp 'sport = :8080'                          # who listens, on which address
docker ps --format '{{.Names}}\t{{.Ports}}' | grep 8080
sudo ufw status | grep -E 'Status|8080'
# From another host: does it already answer?
curl -s -o /dev/null -w '%{http_code}\n' --max-time 5 http://192.0.2.10:8080/healthz
```

```text
LISTEN 0 4096 0.0.0.0:8080 0.0.0.0:* users:(("docker-proxy",pid=2210,fd=7))
webhook-api	0.0.0.0:8080->8080/tcp
Status: active
200
```

**What the output tells you:** the container already publishes 8080 on every address, and it answers from outside although UFW has no rule for 8080. So the ticket has uncovered an exposure that already exists. The right fix gives the developer what they need and closes that hole.

**Fix:** remove the published port and route through Traefik instead.

```yaml
# Dokploy: Application > Advanced > Ports: delete 8080
#          Domains: hooks.example.com -> container port 8080, HTTPS on
# If the partner must be allowlisted, do it at Traefik (v3 middleware), not with a raw port:
http:
  middlewares:
    partner-only:
      ipAllowList:
        sourceRange:
          - "198.51.100.0/24"
```

```bash
# Only when a non-HTTP port is truly needed (here: one migration host, with an end date)
sudo ufw allow proto tcp from 198.51.100.25 to any port 5432 comment 'OPS-1440 until 2026-10-15'
# UFW does not filter Docker-published ports: bind them to the private IP instead
#   ports: ["10.10.0.10:5432:5432"]
```

**Why this fix works:** the Traefik route adds TLS, logs and a single place to allow or deny, and nothing listens on a public high port any more. For container ports, binding to a private address (or rules in the DOCKER-USER chain) is the filter that actually applies. Don't `ufw disable`, don't open a port to 0.0.0.0/0 "for now", and never publish a database to the internet.

**Prevent it:** a port request template (source, destination, port, protocol, reason, owner, expiry), a ports inventory, and a weekly scan from outside compared with that inventory. In AWS, the same request becomes a security group rule that references a source group or a narrow CIDR, behind an ALB.

**Next step:** [Who owns this port?](22-playbook-ports-inventory.md) · [Traefik deep dive](43-traefik-and-reverse-proxies.md) · [Docker networking](30-learn-docker.md) · KodeKloud: LFCS [*Configure Packet Filtering (Firewall)*](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Networking/Configure-Packet-Filtering-Firewall) · [Traefik docs](https://doc.traefik.io/traefik/)

**Community threads:** [Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+published+port+bypass+ufw) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=developer+asked+open+port&restrict_sr=1) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=docker+ufw+bypass&restrict_sr=1)

### 4.2 New app needs a domain and HTTPS

> **Seen as:** "can we get app.example.com for the new service?", then `404 page not found` or a browser warning showing TRAEFIK DEFAULT CERT · **Where:** public or internal DNS, Dokploy domains, Traefik's ACME resolver · **Level:** [L1 · Junior] · **How common:** Dokploy's troubleshooting docs have a page just for domains, and "default certificate instead of Let's Encrypt" is among the top Traefik community threads

**Why it happens:** the order of operations is wrong. An HTTP-01 certificate needs DNS pointing at Traefik and port 80 reachable from the internet *before* the domain is added. Add the domain first and the first ACME attempt fails, so Traefik serves its self-signed default until it retries. A wrong container port gives 502 or 404. Internal-only hostnames can never pass HTTP-01; they need DNS-01 or your private CA.

**Diagnose:**

```bash
dig +short app.example.com @1.1.1.1          # what the internet sees
dig +short app.example.com                   # what this host sees (split DNS?)
curl -sI http://app.example.com/.well-known/acme-challenge/probe | head -1
echo | openssl s_client -connect app.example.com:443 -servername app.example.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer
docker logs --since 15m dokploy-traefik 2>&1 | grep -iE 'acme|app.example.com' | tail -2
```

```text
203.0.113.99
203.0.113.10
HTTP/1.1 404 Not Found
subject=CN = TRAEFIK DEFAULT CERT
issuer=CN = TRAEFIK DEFAULT CERT
... error="unable to generate a certificate for the domains [app.example.com]: ... 203.0.113.99: Timeout during connect (likely firewall problem)"
```

**What the output tells you:** the public record still points at an old address (203.0.113.99), while the internal resolver already has the new one. Let's Encrypt validated against the old server and timed out, so Traefik kept its default certificate. The 404 on the challenge path is normal for a probe; the DNS mismatch is the cause.

**Fix:**

```text
1. Fix the public A record: app.example.com -> 203.0.113.10 (TTL 300). Wait one old TTL.
2. Confirm: dig +short app.example.com @1.1.1.1 returns 203.0.113.10, and port 80 is open.
3. In Dokploy, remove and re-add the domain (or redeploy) with container port 3000 and HTTPS on,
   so Traefik retries ACME at once instead of waiting for its next attempt.
4. Verify: curl -sI https://app.example.com/healthz -> 200, issuer Let's Encrypt.
```

**Why this fix works:** ACME validates from the internet, so public DNS and port 80 must be right before Traefik asks. Re-adding the domain triggers a fresh attempt. Don't hammer retries while DNS is wrong: Let's Encrypt rate-limits failed validations per hostname, and you can lock yourself out for an hour.

**Prevent it:** a domain request template (hostname, app, container port, health path, owner, public or internal), a standard runbook with "DNS first, then domain", and a certificate-expiry probe for every hostname (entry 6.1).

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md) entry 6.1 · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) section 6 · [Site down](25-playbook-site-down.md) · KodeKloud: *Demystifying DNS* — Troubleshooting DNS · [Dokploy docs](https://docs.dokploy.com/docs/core)

**Community threads:** [Dokploy docs: troubleshooting domains](https://docs.dokploy.com/docs/core/troubleshooting/domains) · [Traefik community top threads](https://community.traefik.io/top?period=all) · Search: [Stack Overflow](https://stackoverflow.com/search?q=traefik+%22TRAEFIK+DEFAULT+CERT%22+lets+encrypt) · [Reddit r/Traefik](https://www.reddit.com/r/Traefik/search/?q=default+cert+instead+of+lets+encrypt&restrict_sr=1)

### 4.3 App can't reach a partner API

> **Seen as:** `curl: (28) Connection timed out after 10001 milliseconds` from the app container, while the same call works from a laptop · **Where:** egress firewalls, partner IP allowlists, NAT, outbound proxies, container DNS · **Level:** [L1 · Junior] · **How common:** a classic Server Fault question, and a weekly ticket in any company with B2B integrations

**Why it happens:** the partner allowlists source IPs and does not know your server's egress address (or still has the old one after a migration). Or a corporate egress firewall blocks the destination port, or outbound traffic must go through a proxy the container doesn't know about. Less often, the container resolves the partner's name differently from the host.

**Diagnose:**

```bash
# From inside the app container, the path the app really takes
docker exec -it APP sh -c 'getent hosts api.partner.example.net; curl -sv --max-time 10 https://api.partner.example.net/ping 2>&1 | tail -3'
# Which address does the outside world see for us?
docker exec -it APP curl -s --max-time 5 https://ifconfig.me ; echo
# Do packets leave and does anything come back? (on the host's uplink; find it with: ip route get 198.51.100.40)
sudo tcpdump -ni eth0 host 198.51.100.40 and port 443 -c 3
```

```text
198.51.100.40   api.partner.example.net
*   Trying 198.51.100.40:443...
* Connection timed out after 10001 milliseconds
203.0.113.10
10:02:11.120412 IP 192.0.2.10.48810 > 198.51.100.40.443: Flags [S], seq 991..., length 0
10:02:12.141873 IP 192.0.2.10.48810 > 198.51.100.40.443: Flags [S], seq 991..., length 0
10:02:14.189530 IP 192.0.2.10.48810 > 198.51.100.40.443: Flags [S], seq 991..., length 0
```

**What the output tells you:** DNS is fine and SYN packets leave the host (from 192.0.2.10, which the edge translates to 203.0.113.10, the address ifconfig.me reports), but nothing answers. That pattern means a silent drop on the far side or on your own edge. If your edge firewall logs show the packets passing, the partner's allowlist is the suspect: ask whether 203.0.113.10 is on it.

**Fix:**

```text
1. Send the partner the exact egress IP(s) and port, with a ticket reference, and ask them to confirm.
2. If your own egress firewall blocks it: add one rule (destination 198.51.100.40/32, tcp/443, owner, ticket).
3. If egress must use a proxy: set HTTPS_PROXY and NO_PROXY in the app's environment in Dokploy.
4. Verify from inside the container with the same curl, and record the egress IP in the service docs.
```

**Why this fix works:** an allowlist is an agreement between two teams, so the fix is a confirmed exchange of exact addresses, not trial and error. Don't route the app through a random host that "works", and don't disable certificate checks when a proxy intercepts TLS; install the proxy's CA instead (entry 6.3).

**Prevent it:** document every egress IP per environment, keep it stable (a static SNAT address on-prem, a NAT gateway with an Elastic IP in AWS), tell partners before you migrate, and add a blackbox probe to each critical partner endpoint.

**Next step:** [Network speed](24-playbook-network-speed.md) · [Site down](25-playbook-site-down.md) §5 Connection scenarios · [Docker networking](30-learn-docker.md) · KodeKloud: *Learning Linux Basics Course & Labs* — [Networking Troubleshooting](https://notes.kodekloud.com/docs/Learning-Linux-Basics-Course-Labs/Networking/Troubleshooting) · [curl docs](https://curl.se/docs/)

**Community threads:** [Docker docs: Packet filtering and firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) · Search: [Server Fault](https://serverfault.com/search?q=outbound+connection+timeout+whitelist+ip) · [Stack Overflow](https://stackoverflow.com/search?q=docker+container+outbound+connection+timed+out) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=vendor+ip+whitelist+egress&restrict_sr=1)

---

## 5. Deploys, releases and pipelines

Deploy tickets carry most of the risk in a normal week, because almost every incident starts with a change. The rule that runs through this section: production changes go through the pipeline, and the first move when a deploy hurts users is to roll back, not to debug.

### 5.1 "Deploy this to prod today"

> **Seen as:** "it's a one-line fix, can you just pull the image and restart it on prod?" · **Where:** GitLab CI → Harbor → Dokploy, asked outside the pipeline or the change window · **Level:** [L1 · Junior] · **How common:** a daily request on small teams; DORA's research links fast and safe delivery to automated deploys and lightweight approval, not to manual pushes

**Why it happens:** the pipeline is slow or red, the fix is not merged yet, or a customer is shouting. A manual deploy skips the tests, breaks the link between Git and what is running, and leaves no audit trail, so when it goes wrong nobody can say what is in production.

**Diagnose:**

```bash
# Is the fix merged, and did its pipeline pass?
git fetch -q && git log --oneline -3 origin/main
curl -s -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.example.com/api/v4/projects/42/pipelines?ref=main&per_page=1" | jq -r '.[0] | "\(.sha[0:7]) \(.status)"'
# What runs in production right now?
docker service inspect shop-web --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'
```

```text
a41f9c2 Merge branch 'fix-vat-rounding' into 'main'
7d0e3b1 Raise worker memory limit
c19a7e5 Add order export
a41f9c2 failed
harbor.example.com/shop/web:7d0e3b1@sha256:41ab0c...
```

**What the output tells you:** the fix is merged, but its pipeline failed, and production still runs 7d0e3b1. A manual deploy would ship an image nobody has tested. The fastest safe route to production is usually to fix the pipeline (entry 5.3).

**Fix:** reply with the facts and the path, and keep an expedited path inside the pipeline for real emergencies.

```text
Reply: The fix is merged (a41f9c2) but its pipeline failed at test:unit; I'm on it in OPS-1462.
When it is green, the deploy job ships it in about 8 minutes with the usual rollback.
If it is urgent enough to skip a stage, the release owner decides that in the ticket, and we still
deploy through the pipeline's manual deploy-hotfix job, never by hand on the server.
```

```yaml
# .gitlab-ci.yml — an expedited path that is still logged, reviewed afterwards and reversible
deploy-hotfix:
  stage: deploy
  rules:
    - if: '$CI_COMMIT_BRANCH == "main"'
      when: manual              # the person who presses it is recorded
  script:
    - >
      curl -fsS -X POST "$DOKPLOY_URL/api/application.deploy"
      -H "x-api-key: $DOKPLOY_TOKEN" -H "Content-Type: application/json"
      -d "{\"applicationId\": \"$DOKPLOY_APP_ID\"}"
```

**Why this fix works:** the requester gets a time and a reason instead of a "no", and production stays reproducible from Git. A manual job in the pipeline gives you speed with an audit trail. Don't `docker pull` and restart by hand on the server, and don't build an image on a laptop and push it to Harbor "just this once".

**Prevent it:** make the pipeline the fastest path (cache dependencies, run tests in parallel), define which small changes count as standard changes, and publish the deploy schedule so people stop asking for exceptions.

**Next step:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) entry 9.2 · [Deployment patterns](35-deployment-patterns.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Deployment · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** [DORA capabilities: continuous delivery](https://dora.dev/capabilities/continuous-delivery/) · Search: [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=manager+wants+deploy+friday+hotfix&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=gitlab+ci+manual+deploy+job+production) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=bypass+change+process+urgent&restrict_sr=1)

### 5.2 Deploy broke production

> **Seen as:** the 5xx rate jumps from 0.1% to 30% two minutes after "deploy succeeded", or the new task restarts in a loop · **Where:** Dokploy (Swarm) apps behind Traefik, or Kubernetes Deployments · **Level:** [L2 · Mid-level] · **How common:** changes are the leading trigger in public postmortem collections; Dokploy issue #319 (502s during deploys) and GitHub's November 2021 availability report (a migration in a rolling deploy) are typical examples

**Why it happens:** a variable or secret exists in staging but not in production; the new code needs a migration that has not run, or the migration ran and the old code can't read the new schema; there is no health check, so Swarm sends traffic to a container that is still starting; limits are too low for the new version; or a dependency (Harbor, the database) is unreachable from the new task.

**Diagnose:**

```bash
# 1. Did errors start with the deploy? (Prometheus, Traefik metrics)
#    sum by (code) (rate(traefik_service_requests_total{service=~"shop-web.*",code=~"5.."}[2m]))
# 2. What changed: current and previous image of the service
docker service inspect shop-web \
  --format '{{.Spec.TaskTemplate.ContainerSpec.Image}} | prev: {{.PreviousSpec.TaskTemplate.ContainerSpec.Image}}'
docker service ps shop-web --format '{{.Name}} {{.CurrentState}} {{.Error}}' | head -3
docker service logs --since 10m shop-web 2>&1 | grep -iE 'error|exception' | tail -2
```

```text
harbor.example.com/shop/web:a41f9c2@sha256:9f2c1d... | prev: harbor.example.com/shop/web:7d0e3b1@sha256:41ab0c...
shop-web.1 Running 3 minutes ago
shop-web.1 Shutdown 3 minutes ago
shop-web.1.x9k2m4@dokploy-1    | KeyError: 'PAYMENT_WEBHOOK_SECRET'
shop-web.1.x9k2m4@dokploy-1    | ERROR worker exited, request failed with 500
```

**What the output tells you:** errors began with a41f9c2, and the logs show a variable that exists in staging but not in production. The merge request says this release has no migration, so rolling back is safe.

**Fix:** roll back first, then fix forward through the pipeline.

```bash
# Swarm / Dokploy: return the service to its previous spec
# (or redeploy the previous deployment from the app's Deployments tab in Dokploy)
docker service rollback shop-web
# Kubernetes equivalent
kubectl rollout undo deployment/shop-web && kubectl rollout status deployment/shop-web
# Then add PAYMENT_WEBHOOK_SECRET in Dokploy (Environment) and redeploy a41f9c2 through the pipeline
```

**Why this fix works:** a rollback returns users to a known-good version in about a minute, and you can investigate calmly afterwards. It only works if the release is backward compatible, which is why migrations should use expand and contract: add new columns first, switch the code, remove the old columns in a later release. Don't debug on production while users get errors, and don't hot-patch files inside the running container.

**Prevent it:** health checks with start-first updates, a canary or a small first batch, a required-variables check at start-up (entry 5.4), release notes that flag migrations, and a rollback you have actually rehearsed.

**Next step:** [Deployment patterns](35-deployment-patterns.md) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) entries 6.2 and 8.6 · [Docker & K8s incidents](26-playbook-containers-k8s.md) · [Kubernetes problems](46-problems-kubernetes.md) · KodeKloud: CKA [*Application Failure*](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Application-Failure) · [Docker docs](https://docs.docker.com/)

**Community threads:** [Dokploy issue #319](https://github.com/Dokploy/dokploy/issues/319) · [GitHub availability report, November 2021](https://github.blog/2021-12-01-github-availability-report-november-2021/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+service+rollback+swarm+failed+deploy) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=deploy+broke+production+rollback&restrict_sr=1)

### 5.3 Pipeline red before a release

> **Seen as:** `This job is stuck because you don't have any active runners online with any of these tags assigned to them`, `no space left on device`, `HTTP Basic: Access denied`, or a test that fails once and passes on retry · **Where:** GitLab CI with runner-1 (Docker executor) pushing to Harbor · **Level:** [L1 · Junior] · **How common:** "job stuck" and "runner not picking up jobs" are among the most-viewed threads on forum.gitlab.com

**Why it happens:** red pipelines fall into four families. *Runner*: offline, tag mismatch, a protected-only runner on an unprotected branch, or a full disk. *Credentials*: an expired deploy token or Harbor robot account, or a new runner that doesn't trust the private CA. *Code*: a real failing test. *Flaky*: timing, ordering or an external service. Each family has a different owner, so the first job is to classify.

**Diagnose:**

```bash
# In the job log: read the FIRST error, not the last line
# On runner-1:
sudo gitlab-runner status
sudo gitlab-runner verify
df -h /var/lib/docker
docker system df
```

```text
gitlab-runner: Service is running
Verifying runner... is valid                        runner=Xy7Ab
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb1       100G   97G  3.1G  97% /var/lib/docker
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          412       6         71.3GB    69.8GB (97%)
Containers      9         2         1.2GB     1.1GB (91%)
Local Volumes   38        2         6.4GB     6.1GB (95%)
Build Cache     1893      0         18.2GB    18.2GB
```

**What the output tells you:** the runner is registered and running, so this is not a tag or token problem. The disk is 97% full with 70 GB of reclaimable images and 18 GB of build cache, so jobs fail while pulling or building. Fix the disk, retry once, and if a test still fails, it belongs to the code or flaky family and goes to the developers with the log line.

**Fix:**

```bash
# Free space now; images used by running containers are kept
docker builder prune -af --filter until=72h
docker image prune -af --filter until=72h
# Make it permanent: the cleanup script shipped with gitlab-runner, weekly
echo '0 3 * * 0 root /usr/share/gitlab-runner/clear-docker-cache prune' | sudo tee /etc/cron.d/runner-docker-cache
```

```text
First error                                         Family        Next move
"stuck ... no active runners ... tags"              runner        check tags, protected flag, runner online
"no space left on device"                           runner        clean disk (above), add trend alert
"HTTP Basic: Access denied" / "unauthorized"        credentials   rotate token/robot account, check expiry
"x509: certificate signed by unknown authority"     credentials   trust the private CA (entry 6.3)
assertion failed in a test, same on retry           code          hand to the developer with the log line
passes on retry, fails 1 in 10                      flaky         quarantine the test, file a ticket
```

**Why this fix works:** pruning by age keeps the images and caches recent jobs still use, and the weekly cron stops the problem returning before the next release. Classifying first sends the problem to the right owner in minutes. Don't press retry five times, don't add `allow_failure: true` to get the release out, and don't run `docker system prune -a --volumes` on a Dokploy host, where volumes hold data.

**Prevent it:** a disk trend alert on every runner, a calendar of token and robot-account expiry dates, a quarantine list for flaky tests, and a rule that the release branch is green the day before release, not the hour before.

**Next step:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) entries 5.1, 7.2 and 8.1 · [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) §2 GitLab CI/CD · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Self-Managed Runners · [GitLab Runner docs: Docker executor](https://docs.gitlab.com/runner/executors/docker/)

**Community threads:** [GitLab forum: job stuck, no active runners with these tags](https://forum.gitlab.com/t/this-job-is-stuck-because-you-don-t-have-any-active-runners-online-with-any-of-these-tags-assigned/28205) · [GitLab forum: runner not picking up jobs](https://forum.gitlab.com/t/gitlab-runner-not-picking-up-jobs/70464) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+runner+%22no+space+left+on+device%22) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=pipeline+stuck+pending+runner&restrict_sr=1)

### 5.4 Works in staging, fails in production

> **Seen as:** `KeyError: 'SMTP_HOST'`, `connection refused` to a service that exists in staging, or a feature that works for QA and times out for customers · **Where:** two Dokploy environments (or two namespaces) that have drifted apart · **Level:** [L2 · Mid-level] · **How common:** one of the oldest themes on Stack Overflow

**Why it happens:** the environments differ in ways nobody wrote down. Variables were added by hand in one Dokploy project; staging was built from a branch, not the released tag; production has an egress firewall or a partner allowlist; production data is a hundred times larger, so a query that takes 50 ms in staging takes 9 s; Traefik middlewares differ between the two.

**Diagnose:**

```bash
# Same artifact? Compare digests, not tags
for h in staging-1 dokploy-1; do
  ssh "$h" "docker service inspect shop-web --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'"; done
# Same configuration? Compare variable NAMES only, never values
for h in staging-1 dokploy-1; do
  ssh "$h" "docker service inspect shop-web --format '{{range .Spec.TaskTemplate.ContainerSpec.Env}}{{println .}}{{end}}'" \
    | cut -d= -f1 | sort > "env-$h.txt"; done
diff env-staging-1.txt env-dokploy-1.txt
```

```text
harbor.example.com/shop/web:a41f9c2@sha256:9f2c1d...
harbor.example.com/shop/web:a41f9c2@sha256:9f2c1d...
12,13d11
< SMTP_HOST
< SMTP_PORT
```

**What the output tells you:** both environments run the same digest, so the code is identical. Production lacks two variables that staging has, which explains the error. If the variables matched, the next suspects would be network rules and data size.

**Fix:** set the missing variables in Dokploy for production, redeploy, and make the app fail fast next time.

```bash
#!/bin/sh
# entrypoint.sh — refuse to start without required variables, so the health check
# fails the deploy and the old version keeps serving
for v in DATABASE_URL SMTP_HOST SMTP_PORT PAYMENT_WEBHOOK_SECRET; do
  [ -n "$(printenv "$v")" ] || { echo "missing required env var: $v" >&2; exit 1; }
done
exec "$@"
```

**Why this fix works:** comparing digests and variable names separates "different code" from "different configuration" in two commands. Failing at start-up turns a 500 for customers into a failed deploy that nobody outside the team sees. Don't copy the staging env file to production wholesale: it carries staging credentials and test keys.

**Prevent it:** a list of required variables in the repository, the same image digest promoted from staging to production, staging network rules that mirror production, and a monthly drift check.

**Next step:** [Deployment patterns](35-deployment-patterns.md) · [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Continuous Deployment (environments) · [Dokploy docs](https://docs.dokploy.com/docs/core)

**Community threads:** [Dokploy docs](https://docs.dokploy.com/docs/core) · Search: [Stack Overflow](https://stackoverflow.com/search?q=works+in+staging+but+not+production+docker+environment+variables) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=staging+production+drift&restrict_sr=1)

---

## 6. Certificates, DNS and trust

These three cause a large share of "everything is broken at once" mornings. They sit underneath every app, so one failure shows up as many unrelated-looking tickets. When three teams report three different errors at the same time, check certificates, DNS and time before anything else.

### 6.1 Certificate expired

> **Seen as:** `NET::ERR_CERT_DATE_INVALID` in browsers, `x509: certificate has expired or is not yet valid` from clients and CI jobs · **Where:** Let's Encrypt through Traefik in Dokploy, certbot on the old Apache, hand-installed commercial certificates, certificates from the private CA · **Level:** [L1 · Junior] · **How common:** Let's Encrypt stopped sending expiry emails on 4 June 2025, and lifetimes are shrinking (45-day certificates opt-in since May 2026, a 64-day default from February 2027, 45 days from February 2028), so a broken renewal path now bites sooner and with no warning

**Why it happens:** automatic renewal fails silently: a firewall change closed port 80, DNS moved, `acme.json` was not on persistent storage and vanished on a redeploy, a catch-all router swallows the challenge path, or the certbot timer on the old Apache host was disabled. Hand-installed certificates have no renewal at all. "Not yet valid" usually means the client's clock is wrong: blocked NTP or a VM restored from a snapshot.

**Diagnose:**

```bash
# What is actually served, and until when?
echo | openssl s_client -connect shop.example.com:443 -servername shop.example.com 2>/dev/null \
  | openssl x509 -noout -subject -issuer -enddate
# Is this machine's clock right? (rules out "not yet valid")
timedatectl | grep -E 'Local time|synchronized'
# Why did renewal fail? (certbot hosts: sudo certbot renew --dry-run)
docker logs --since 72h dokploy-traefik 2>&1 | grep -i 'unable to obtain ACME certificate' | tail -1
```

```text
subject=CN = shop.example.com
issuer=C = US, O = Let's Encrypt, CN = R11
notAfter=Oct  4 06:12:40 2026 GMT
                Local time: Sun 2026-10-04 07:31:02 UTC
System clock synchronized: yes
... unable to obtain ACME certificate for domains "shop.example.com": ... 403 ... Invalid response from http://shop.example.com/.well-known/acme-challenge/...: 404
```

**What the output tells you:** the certificate expired at 06:12 today, and the clock is fine, so it really is expired. Renewal has been failing for days because something other than Traefik's challenge handler answers on port 80 for the challenge path. Find what answers there before you retry.

**Fix:**

```bash
# 1. Who answers on port 80 for the challenge path? Expect Traefik's own 404, not Apache or a redirect elsewhere
curl -sI http://shop.example.com/.well-known/acme-challenge/probe | grep -iE '^HTTP|^server|^location'
# 2. Remove the catch-all or redirect that captures it, then trigger a new attempt
#    (restarting Traefik drops every route for a few seconds: do it on purpose and say so)
docker restart dokploy-traefik
# 3. Verify the new date
echo | openssl s_client -connect shop.example.com:443 -servername shop.example.com 2>/dev/null | openssl x509 -noout -enddate
# certbot hosts: sudo certbot renew --dry-run, fix what it prints, then sudo certbot renew && sudo systemctl reload apache2
```

**Why this fix works:** ACME renewal is the same validation as the first issuance, so whatever broke the path must be fixed before any retry can succeed. A restart makes Traefik try again at once rather than at its next scheduled attempt. Don't tell users to click through the warning, don't set `InsecureSkipVerify` or `curl -k` in clients, and don't "fix" it by buying a one-year certificate by hand: that only moves the cliff.

**Prevent it:** a blackbox probe and the alert `probe_ssl_earliest_cert_expiry - time() < 14 * 86400` for every hostname, internal ones included; a certificate inventory that lists the hand-installed ones; and renewal at about two-thirds of the lifetime, which suits the shorter certificates coming.

**Next step:** [Traefik deep dive](43-traefik-and-reverse-proxies.md) §3.7 Certificates in 2026 and entry 6.1 · [Web, HTTP & TLS](18-web-http-tls.md) · [Observability](49-observability-stack-problems.md) entry 5.4 · [Time and NTP](12-time-ntp.md) · KodeKloud: LFCS [*Work With SSL Certificates*](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates) · [Let's Encrypt docs](https://letsencrypt.org/docs/)

**Community threads:** [Let's Encrypt: expiration emails have ended](https://letsencrypt.org/docs/expiration-emails/) · [Let's Encrypt: decreasing certificate lifetimes to 45 days](https://letsencrypt.org/2025/12/02/from-90-to-45) · [Dan Luu's post-mortems](https://github.com/danluu/post-mortems) (the Time section includes Azure's leap-day certificate outage) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22certificate+has+expired+or+is+not+yet+valid%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=traefik+lets+encrypt+renewal+failed&restrict_sr=1)

### 6.2 It's always DNS

> **Seen as:** `Temporary failure in name resolution`, `curl: (6) Could not resolve host`, `lookup harbor.example.com on 127.0.0.53:53: server misbehaving`, and several unrelated things failing at once · **Where:** systemd-resolved on Ubuntu, Docker's DNS, internal DNS servers, CoreDNS · **Level:** [L1 · Junior] · **How common:** DNS is one of the two biggest themes on Kubernetes Failure Stories, and AWS's October 2025 us-east-1 outage began when automation left an empty DNS record for DynamoDB's regional endpoint

**Why it happens:** a netplan change dropped the internal resolver, split DNS for an internal zone was never configured in systemd-resolved, a firewall blocks port 53 (TCP included), a negative answer is still cached after a record was fixed, or automation wrote an empty or wrong record. Because every service depends on names, one DNS fault looks like a registry outage, a CI outage and an app outage at once.

**Diagnose:**

```bash
resolvectl status ens18 | grep -E 'DNS Server|DNS Domain'
resolvectl query harbor.example.com
getent ahosts harbor.example.com              # what applications actually get
dig +short harbor.example.com @10.10.0.53     # ask the internal server directly
docker run --rm busybox nslookup harbor.example.com
```

```text
Current DNS Server: 192.0.2.53
       DNS Servers: 192.0.2.53
harbor.example.com: resolve call failed: 'harbor.example.com' not found
10.10.0.40
Server:    192.0.2.53
Address:   192.0.2.53:53
** server can't find harbor.example.com: NXDOMAIN
```

**What the output tells you:** the host only asks 192.0.2.53, a public resolver that knows nothing about the internal record, and getent prints nothing. The internal server 10.10.0.53 answers correctly. Yesterday's netplan change removed the internal resolver, so the fix is in netplan, not in Harbor.

**Fix:**

```yaml
# /etc/netplan/50-cloud-init.yaml (excerpt): internal resolvers first, internal search domain
network:
  ethernets:
    ens18:
      nameservers:
        addresses: [10.10.0.53, 10.10.0.54]
        search: [example.com]
```

```bash
# If the file's header says cloud-init generated it, also write /etc/cloud/cloud.cfg.d/99-disable-network-config.cfg
# containing "network: {config: disabled}", or cloud-init may regenerate the file and drop your change
sudo netplan try                 # reverts by itself after 120 s if you lose access
sudo resolvectl flush-caches
# Containers copy resolver settings when they start: recreate the affected ones
```

**Why this fix works:** `netplan try` applies the change with an automatic undo, so a mistake can't lock you out. Flushing removes the cached failure, and recreated containers pick up the new upstream. Don't paste IPs into /etc/hosts across the fleet (it drifts and hides the real fault), and don't point containers at 8.8.8.8, which cannot see internal names.

**Prevent it:** two internal resolvers, netplan managed by Ansible, blackbox DNS probes for the critical names, and lower TTLs a day before planned moves.

**Next step:** [DNS](08-dns.md) · [Docker networking](30-learn-docker.md) · [Kubernetes problems](46-problems-kubernetes.md) · KodeKloud: *Demystifying DNS* — [Troubleshooting DNS](https://notes.kodekloud.com/docs/Demystifying-DNS/Miscellaneous/Troubleshooting-DNS/page) · [Ubuntu Server docs](https://ubuntu.com/server/docs)

**Community threads:** [AWS: summary of the DynamoDB service disruption, October 2025](https://aws.amazon.com/message/101925/) · [Kubernetes Failure Stories](https://k8s.af/) · Search: [Server Fault](https://serverfault.com/search?q=temporary+failure+in+name+resolution+systemd-resolved) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=%22always+DNS%22&restrict_sr=1)

### 6.3 x509 unknown authority with the private CA

> **Seen as:** `x509: certificate signed by unknown authority` from docker pull or push, `server certificate verification failed. CAfile: none` from git in a CI job · **Where:** a new host, a new runner, a fresh job image, or right after the CA was rotated · **Level:** [L1 · Junior] · **How common:** among the most common CI and registry problems on the GitLab forum, with its own pages in the Docker and GitLab Runner docs

**Why it happens:** every client keeps its own trust store: the OS store, Docker's per-registry directory, the runner's config, the job image's own store, plus Java keystores, Node and Python's bundles. A new host or image misses one of them. Less often the server sends only its leaf certificate without the intermediate, and only clients that cache intermediates succeed.

**Diagnose:**

```bash
# Does the server send the full chain, and who issued it?
echo | openssl s_client -connect harbor.example.com:443 -servername harbor.example.com -showcerts 2>/dev/null \
  | grep -E '^ *[0-9] s:|^ *i:'
# Does this host trust it, at OS level and for Docker?
curl -sS -o /dev/null https://harbor.example.com/ && echo os-trust-ok
ls /etc/docker/certs.d/harbor.example.com/ 2>/dev/null || echo no-docker-ca-for-harbor
```

```text
 0 s:CN = harbor.example.com
   i:CN = Example Internal Issuing CA
 1 s:CN = Example Internal Issuing CA
   i:CN = Example Internal Root CA
curl: (60) SSL certificate problem: unable to get local issuer certificate
no-docker-ca-for-harbor
```

**What the output tells you:** the server sends a complete chain up to the internal root, so the server is fine. This new host trusts the root neither at OS level nor for Docker.

**Fix:**

```bash
sudo cp example-root-ca.crt /usr/local/share/ca-certificates/example-root-ca.crt
sudo update-ca-certificates
sudo mkdir -p /etc/docker/certs.d/harbor.example.com
sudo cp example-root-ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt
# GitLab Runner, in /etc/gitlab-runner/config.toml under [[runners]]:
#   tls-ca-file = "/etc/gitlab-runner/certs/example-root-ca.crt"
# Job images: bake the CA into your base images, or run update-ca-certificates in before_script
```

**Why this fix works:** each layer gets the root it was missing, and Docker reads `certs.d` without a restart. Don't add the registry to `insecure-registries`, don't set `GIT_SSL_NO_VERIFY`, and don't sprinkle `-k` through scripts: each one turns off the protection the private CA exists to provide.

**Prevent it:** the CA in the Ansible baseline and in every base image, a "new runner" checklist, and an expiry alert for the CA certificates themselves.

**Next step:** [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) entry 7.2 · [Docker, Swarm & registry problems](44-problems-docker-swarm-registry.md) · [Security & DevSecOps](37-learn-security-devsecops.md) §4 TLS and PKI · KodeKloud: LFCS [*Work With SSL Certificates*](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates) · [Harbor docs](https://goharbor.io/docs/)

**Community threads:** [Docker docs: registry certificates](https://docs.docker.com/engine/security/certificates/) · [GitLab Runner docs: self-signed certificates](https://docs.gitlab.com/runner/configuration/tls-self-signed/) · [GitLab forum: runner certificate verification failed](https://forum.gitlab.com/t/gitlab-runner-server-certificate-verification-failed/59450) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22x509%3A+certificate+signed+by+unknown+authority%22+docker+registry) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=x509+unknown+authority+runner&restrict_sr=1)

---

## 7. Disk, memory, slowness and restores

These are the classic resource tickets. Two habits make them easy: look at the trend before the number, and name the saturated resource before you touch anything.

### 7.1 Disk full at 3 AM

> **Seen as:** a page `HostDiskWillFillIn4Hours`, or `no space left on device` from Docker, Postgres or the runner · **Where:** Dokploy hosts and GitLab runners · **Level:** [L1 · Junior] · **How common:** the most common night page on container hosts; Docker's json-file log driver has no size limit by default, and GitLab documents weekly cache cleanup for runners because of it

**Why it happens:** container logs that never rotate, old images and build cache from every deploy, journald growth, backups written to the same disk, or a log deleted with `rm` while the process still holds it open, so `df` and `du` disagree. Millions of small files can exhaust inodes while bytes are still free.

**Diagnose:**

```bash
df -hT / && df -hi /
sudo du -xh --max-depth=1 /var/lib/docker 2>/dev/null | sort -h | tail -3
sudo find /var/lib/docker/containers -name '*-json.log' -size +1G -exec ls -lh {} \;
sudo lsof -nP +L1 | head -3          # deleted files still held open
```

```text
Filesystem     Type  Size  Used Avail Use% Mounted on
/dev/sda2      ext4   98G   95G  924M 100% /
Filesystem     Inodes IUsed IFree IUse% Mounted on
/dev/sda2        6.3M  412K  5.9M    7% /
21G     /var/lib/docker/overlay2
52G     /var/lib/docker/containers
74G     /var/lib/docker
-rw-r----- 1 root root 49G Oct  4 03:02 /var/lib/docker/containers/8c1f2a.../8c1f2a...-json.log
```

**What the output tells you:** inodes are fine and nothing deleted is held open. One container's JSON log has grown to 49 GB, so a chatty app with no log rotation filled the disk, not images.

**Fix:**

```bash
# Tonight: keep the last lines as evidence, then empty the file in place
sudo tail -n 5000 /var/lib/docker/containers/8c1f2a.../8c1f2a...-json.log | sudo tee /root/8c1f2a-tail.log >/dev/null
sudo truncate -s 0 /var/lib/docker/containers/8c1f2a.../8c1f2a...-json.log
# Next change window: default rotation for every new container, in /etc/docker/daemon.json
#   { "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
# then restart Docker (this restarts every container) and recreate containers so they pick it up
```

**Why this fix works:** `truncate` frees the space at once and the writing process keeps a valid file handle. `rm` would not free anything while Docker holds the file open, which is how `df` and `du` drift apart. The daemon setting only applies to containers created afterwards. Don't `docker system prune -a --volumes` at 3 AM on a Dokploy host: volumes hold databases.

**Prevent it:** a trend alert such as `predict_linear(node_filesystem_avail_bytes{mountpoint="/"}[6h], 4*3600) < 0`, `/var/lib/docker` on its own volume, log rotation in the Ansible baseline, and a ticket to the app owner about why it logs 49 GB.

**Next step:** [Storage and disk](01-storage-disk.md) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) entry 11.1 · [Docker, Swarm & registry problems](44-problems-docker-swarm-registry.md) · KodeKloud: DCA [*Logging Driver*](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Logging-Driver/page) · [Docker docs: json-file driver](https://docs.docker.com/engine/logging/drivers/json-file/)

**Community threads:** [Docker docs: json-file defaults](https://docs.docker.com/engine/logging/drivers/json-file/) · [GitLab Runner docs: clearing the Docker cache](https://docs.gitlab.com/runner/executors/docker/) · Search: [Server Fault](https://serverfault.com/search?q=no+space+left+on+device+docker+overlay2) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=disk+full+container+logs&restrict_sr=1)

### 7.2 "The app is slow"

> **Seen as:** "the site is slow" in chat with no numbers, and `load average: 24.10` while the CPU looks mostly idle · **Where:** any host, any app · **Level:** [L2 · Mid-level] · **How common:** the vaguest ticket and one of the most common; Brendan Gregg reports that his USE method solves most server performance issues with a small fraction of the effort

**Why it happens:** "slow" hides several questions: slow for whom, since when, which page, and how slow. The cause can be disk I/O saturation (blocked tasks count towards the load average), memory pressure, a noisy neighbour VM, a slow database or partner API, or DNS timeouts. Juniors restart things; seniors find the saturated resource first.

**Diagnose:** ask the three questions (who, since when, how slow in seconds), then measure.

```bash
# Latency per service from Traefik metrics (PromQL in Grafana)
#   histogram_quantile(0.95, sum by (le) (rate(traefik_service_request_duration_seconds_bucket{service=~"shop-web.*"}[5m])))
# USE on the host: run queue, blocked tasks, swap, iowait, steal
vmstat 1 3
iostat -xz 1 2 | grep -E 'Device|sda'
```

```text
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 2 14      0 412000  88000 5120000    0    0 98000  1200 2100 3900  6  3 31 60  0
 1 15      0 409000  88000 5118000    0    0 97000  1100 2050 3800  5  3 30 62  0
Device     r/s     rkB/s  r_await   w/s   wkB/s  w_await  aqu-sz  %util
sda     1450.0   97800.0    48.20  35.0  1150.0    12.40    69.8   99.8
(vmstat shows its first, since-boot line too, and iostat prints more columns; trimmed to the ones that matter)
```

**What the output tells you:** 14–15 tasks are blocked on I/O, iowait is 60%, and sda is 99.8% busy with 48 ms reads, while swap and steal are zero. The disk is saturated by reads. The next question is which process is reading.

**Fix:** find the culprit, mitigate, then fix the cause.

```bash
sudo pidstat -d 1 3 | tail -4          # which process reads so much?
# Example result: restic (PID 23817) running the nightly backup, rescheduled into business hours
sudo ionice -c3 -p 23817 && sudo renice +10 -p 23817
# ionice classes only take effect with the bfq or mq-deadline scheduler: cat /sys/block/sda/queue/scheduler
# (with "none", common on NVMe and virtio disks, throttle the job or pause it instead)
```

```text
Reply: Slow since 10:02 because the backup job saturated the disk on dokploy-1.
Mitigated at 10:20 (p95 back from 4.1 s to 0.3 s). Backup moved back to 02:00 (OPS-1477).
```

**Why this fix works:** naming the saturated resource tells you which fix can possibly help: more CPU does nothing for a saturated disk. Lowering the backup's I/O class restores users now, and the schedule fix stops a repeat. Don't restart the app "to see if it helps": it destroys the evidence and does not touch the disk.

**Prevent it:** USE dashboards per host, a latency objective per service, heavy jobs on a schedule that is reviewed, and limits so one container can't starve the host.

**Next step:** [Slow system](23-playbook-slow-system.md) · [CPU and performance](03-cpu-performance.md) · [Performance & observability](32-learn-performance-observability.md) · KodeKloud: *Fundamentals of SRE* — [Performance Monitoring Deep Dive](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Observability-and-Monitoring/Performance-Monitoring-Deep-Dive/page) · [Prometheus docs](https://prometheus.io/docs/)

**Community threads:** [Brendan Gregg: the USE method](https://www.brendangregg.com/usemethod.html) · Search: [Server Fault](https://serverfault.com/search?q=high+load+average+low+cpu+iowait) · [Reddit r/linuxadmin](https://www.reddit.com/r/linuxadmin/search/?q=server+slow+troubleshooting&restrict_sr=1)

### 7.3 A process was killed without a log line

> **Seen as:** the app's own log ends mid-line, `docker inspect` shows `OOMKilled=true` and exit code 137, and the kernel log says `Out of memory: Killed process` · **Where:** Dokploy (Swarm) services, Kubernetes pods, systemd services · **Level:** [L1 · Junior] · **How common:** a Stack Overflow and Server Fault classic; OOM kills and evictions are among the most common themes on Kubernetes Failure Stories

**Why it happens:** a memory leak or unbounded cache, a container limit below the runtime's heap (JVM, Node), or no limits at all, so the kernel kills the biggest process on the host, which is often the database. Reading the "used" column of `free` instead of "available" hides real pressure.

**Diagnose:**

```bash
sudo journalctl -k --since '-6h' | grep -iE 'out of memory|oom-kill' | tail -2
docker inspect -f '{{.Name}} OOMKilled={{.State.OOMKilled}} exit={{.State.ExitCode}}' $(docker ps -aq --filter name=shop-worker)
docker stats --no-stream --format '{{.Name}} {{.MemUsage}}' | grep shop-worker
free -h | head -2
```

```text
Oct 04 02:17:33 dokploy-1 kernel: Memory cgroup out of memory: Killed process 4121 (java) total-vm:4012340kB, anon-rss:1046120kB
Oct 04 02:17:33 dokploy-1 kernel: oom-kill:constraint=CONSTRAINT_MEMCG,...
/shop-worker.1.k3j9x2 OOMKilled=true exit=137
shop-worker.1.p8x4m1 1021MiB / 1GiB
               total        used        free      shared  buff/cache   available
Mem:            15Gi       9.8Gi       1.1Gi       210Mi       4.6Gi       5.2Gi
```

**What the output tells you:** CONSTRAINT_MEMCG means the container hit its own 1 GiB limit; the host still has 5.2 GiB available. The replacement task is already at 1021 MiB of 1 GiB, so it will die again. The JVM heap is not sized to the limit.

**Fix:**

```yaml
# Dokploy (Swarm) service: size the runtime to the limit, then the limit to real usage
environment:
  JAVA_TOOL_OPTIONS: "-XX:MaxRAMPercentage=75"
deploy:
  resources:
    limits:
      memory: 1536M
```

**Why this fix works:** the heap now leaves room for the JVM's non-heap memory inside the limit, and the limit matches measured usage plus headroom. If usage keeps climbing after this, it is a leak: give the developers the graph, because scheduled restarts are toil, not a fix. Don't remove limits altogether (the host's OOM killer then picks the database) and don't disable the OOM killer.

**Prevent it:** an alert when the working set passes 90% of the limit, an alert on restart counts, and memory checked in load tests before release.

**Next step:** [Memory](04-memory.md) · [Docker containers](14-docker-containers.md) · [Docker & K8s incidents](26-playbook-containers-k8s.md) · [Kubernetes problems](46-problems-kubernetes.md) · KodeKloud: CKA [*Application Failure*](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Application-Failure) · [Docker docs](https://docs.docker.com/)

**Community threads:** [Kubernetes Failure Stories](https://k8s.af/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=exit+code+137+OOMKilled+docker) · [Server Fault](https://serverfault.com/search?q=%22Out+of+memory%3A+Killed+process%22) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=exit+code+137+oomkilled&restrict_sr=1)

### 7.4 Restore request: "we need yesterday's data"

> **Seen as:** "someone deleted 300 orders at 09:40, can you get them back?" · **Where:** Postgres in Dokploy with scheduled dumps to MinIO, restic for volumes · **Level:** [L2 · Mid-level] · **How common:** GitLab's 2017 database outage (a deletion on the wrong host, then backups that did not work as expected) is the classic, and dev.to still regularly carries stories like "I thought my backups were safe until I tried restoring one"

**Why it happens:** restores are rare, so nobody has tested one recently. Daily dumps mean up to 24 hours of data loss (the RPO). Restoring over production would also wipe everything written since the dump. And nobody knows how long a restore takes (the RTO) until the business is waiting for it.

**Diagnose:** collect the facts first: which records, as of what time, what has been written since, and who approves any change to production data.

```bash
# Which dumps exist, how big, how recent?
mc ls --recursive minio/backups/shop-db/ | tail -3
```

```text
[2026-10-02 02:00:14 UTC] 1.9GiB STANDARD shop-2026-10-02T020000.dump
[2026-10-03 02:00:11 UTC] 1.9GiB STANDARD shop-2026-10-03T020000.dump
[2026-10-04 02:00:16 UTC] 2.0GiB STANDARD shop-2026-10-04T020000.dump
```

**What the output tells you:** today's 02:00 dump was taken before the 09:40 deletion, so the rows are in it. Orders created between 02:00 and 09:40 are not, so restoring the whole database over production would lose a morning of real orders. Restore to the side and copy only the missing rows.

**Fix:**

```bash
# From a host with database access (or inside the Postgres container with docker exec)
mc cp minio/backups/shop-db/shop-2026-10-04T020000.dump .
createdb -h 10.10.0.10 -U postgres shop_restore_ops1490
time pg_restore -h 10.10.0.10 -U postgres -d shop_restore_ops1490 --no-owner -j 4 shop-2026-10-04T020000.dump
# Export only the deleted rows for the data owner to review before anything is re-inserted
psql -h 10.10.0.10 -U postgres -d shop_restore_ops1490 \
  -c "\copy (SELECT * FROM orders WHERE id BETWEEN 88120 AND 88419) TO 'orders-ops1490.csv' CSV HEADER"
```

**Why this fix works:** a side restore cannot damage current data, the owner decides what goes back, and `time` gives you the real restore duration for the runbook. Don't restore over production without written approval, and drop the side database when the ticket closes, because it holds customer data.

**Prevent it:** a quarterly restore drill with timings, point-in-time recovery (WAL archiving or pgBackRest) for important databases, soft deletes in the application, and 3-2-1 backups with one immutable copy.

**Next step:** [Databases, storage & backups](51-problems-databases-storage-backup.md) entries 5.1 and 9.3 · [Databases for DevOps](38-learn-databases-ops.md) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) · [PostgreSQL docs](https://www.postgresql.org/docs/)

**Community threads:** [GitLab: postmortem of the database outage of 31 January 2017](https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/) · [dev.to: I thought my backups were safe until I tried restoring one](https://dev.to/highflyer910/i-thought-my-backups-were-safe-until-i-tried-restoring-one-387i) · Search: [Stack Overflow](https://stackoverflow.com/search?q=pg_restore+single+table+from+dump) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=test+restore+backup+disaster&restrict_sr=1)

---

## 8. Cost, capacity and patching questions

From mid-level up, more tickets are questions than tasks: "why", "how much", "are we affected". They are answered with data, a recommendation and a date, never with a guess.

### 8.1 "Why is the bill so high?"

> **Seen as:** finance forwards "the AWS bill went from $1,900 to $3,400", or a manager asks "should we buy two more servers?" · **Where:** AWS accounts; on-prem Proxmox and Dokploy hosts · **Level:** [L2 · Mid-level] · **How common:** a recurring top theme on r/aws and Hacker News; AWS has charged for every public IPv4 address since 1 February 2024

**Why it happens:** in the cloud, the usual suspects are NAT gateway data processing (image pulls through NAT), public IPv4 addresses, forgotten volumes and snapshots, and dev environments left running over the weekend, made worse by missing tags, so nobody knows whose cost it is. On-prem, the question is about buying hardware, and it is usually asked without utilisation data: one host at 95% while another idles at 12%.

**Diagnose:**

```bash
# Cloud: cost per service for two months (Cost Explorer API)
aws ce get-cost-and-usage --time-period Start=2026-08-01,End=2026-10-01 --granularity MONTHLY \
  --metrics UnblendedCost --group-by Type=DIMENSION,Key=SERVICE \
  --query 'ResultsByTime[].Groups[].[Keys[0],Metrics.UnblendedCost.Amount]' --output text \
  | sort -t$'\t' -s -k1,1 | grep -E 'Compute Cloud - Compute|Virtual Private Cloud|EC2 - Other'
# On-prem: p95 CPU and memory use per host over 30 days (PromQL in Grafana)
#   quantile_over_time(0.95, (1 - avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])))[30d:1h])
#   quantile_over_time(0.95, (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)[30d:1h])
```

```text
Amazon Elastic Compute Cloud - Compute	1104.20
Amazon Elastic Compute Cloud - Compute	1131.85
Amazon Virtual Private Cloud	61.10
Amazon Virtual Private Cloud	118.20
EC2 - Other	402.75
EC2 - Other	1688.40
dokploy-1  cpu p95 0.71  mem p95 0.82
dokploy-2  cpu p95 0.12  mem p95 0.31
```

**What the output tells you:** compute is flat. "EC2 - Other", the bucket for NAT gateway processing, EBS volumes, snapshots and data transfer, quadrupled, and the VPC line (where public IPv4 is billed) doubled. Group by usage type next to find the exact line. On-prem, dokploy-2 is mostly idle, so the honest answer to "buy more servers?" is "not yet".

**Fix:**

<div class="env" data-env="cloud" markdown="1">

**Cloud:** group by USAGE_TYPE to find the line (NatGateway-Bytes, EBS snapshots, public IPv4). If image pulls go through NAT, add a gateway endpoint for S3 and interface endpoints for ECR. Delete orphaned volumes and old snapshots, release idle Elastic IPs, stop dev environments on a schedule, then tag everything and set a budget alert.

</div>

<div class="env" data-env="onprem" markdown="1">

**On-prem:** rebalance before you buy. Move two apps from dokploy-1 to dokploy-2 with Dokploy's multi-server support, set limits, and come back with p95 data and a growth trend. Hardware has a lead time of weeks or months, so present the trend line and the date you will run out, not a feeling.

</div>

```text
Reply: The bill rose $1,500; about 80% is NAT data processing since the image-pull job added on 9 Sep (OPS-1480).
Fix: S3 and ECR endpoints, expected saving about $1,100 a month. Budget alert at $2,500 added.
```

**Why this fix works:** an answer grouped by service and usage type, with an owner and an expected saving, turns a worried email into a decision. Don't delete resources you can't attribute without asking first, and don't buy hardware to solve an imbalance.

**Prevent it:** a tagging policy, a monthly cost review, budget alerts, and a quarterly capacity review on-prem.

**Next step:** [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) entry 2.5 · [Cloud & AWS](36-learn-cloud-aws.md) · [On-prem vs cloud paths](55-paths-onprem-vs-cloud.md) · KodeKloud: [*AWS Certified CloudOps Engineer - Associate*](https://kodekloud.com/courses/aws-certified-sysops-administrator-associate) — Cost and Performance · [AWS docs](https://docs.aws.amazon.com/)

**Community threads:** [AWS blog: public IPv4 address charge and Public IP Insights](https://aws.amazon.com/blogs/aws/new-aws-public-ipv4-address-charge-public-ip-insights/) · Search: [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=surprise+bill+nat+gateway&restrict_sr=1) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=capacity+planning+new+servers&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=aws+cost+explorer+nat+gateway+cost)

### 8.2 "Will it hold during the launch?"

> **Seen as:** "marketing emails 200,000 customers on Tuesday; will the shop survive?" · **Where:** Dokploy apps behind Traefik, with Postgres behind them · **Level:** [L3 · Senior] · **How common:** a classic r/devops and Server Fault question in the form "how many users can my server handle?"

**Why it happens:** nobody knows today's peak, the cost of one request or which component gives up first. The limit is usually the database or a single-replica service, not the CPU everyone looks at.

**Diagnose:**

```bash
# Today's peak and latency (PromQL in Grafana)
#   max_over_time(sum(rate(traefik_service_requests_total{service=~"shop-web.*"}[5m]))[14d:5m])
# Load test a staging copy with production-sized data
k6 run --vus 200 --duration 10m checkout.js
```

```text
peak (14 days): 38 req/s, p95 0.31 s
     http_req_duration..............: avg=410ms  p(95)=1.92s
     http_req_failed................: 4.10%  1873 out of 45685
     http_reqs......................: 45685  76.1/s
```

**What the output tells you:** a rough estimate: 200,000 emails with about 3% clicking in the first hour is 6,000 visitors, around 10 requests each, so about 17 req/s on average with peaks of three to four times that, on top of today's 38 req/s: roughly 100 req/s. Staging already fails at 76 req/s with a 1.9 s p95, so the answer today is no. Watch the database during the test to find the limit.

**Fix:**

```text
1. Find the limit during the test: here Postgres hit max_connections (100) with 3 web replicas x 40 pool slots.
2. Fix it: pool sizes that fit, PgBouncer in front of Postgres, cache product pages at the app or Traefik layer.
3. Re-test until twice the expected peak passes with p95 under 500 ms and errors under 0.1%.
4. Prepare degradation: a flag to switch off recommendations, a static "busy" page.
5. Launch day: change freeze for other work, on-call staffed, a dashboard on the big screen.
```

**Why this fix works:** an estimate with a safety factor, verified by a test that changes one thing at a time, gives a yes or no you can defend. Don't load test production without agreement, and don't add web replicas when the database is the limit: more replicas mean more connections and fail faster.

**Prevent it:** launches on the change calendar, a quarterly capacity review, and a load test per critical service in the pipeline.

**Next step:** [Performance & observability](32-learn-performance-observability.md) · [Senior architecture](39-learn-senior-architecture.md) · [Databases for DevOps](38-learn-databases-ops.md) · KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil (capacity planning) · [k6 docs](https://grafana.com/docs/k6/latest/)

**Community threads:** [Google SRE book: Managing Incidents](https://sre.google/sre-book/managing-incidents/) (prepare procedures before the big day) · Search: [Stack Overflow](https://stackoverflow.com/search?q=how+many+requests+per+second+can+my+server+handle) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=load+testing+before+launch&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=capacity+planning+web+traffic+spike)

### 8.3 "Are we affected by this CVE?"

> **Seen as:** security forwards a headline with "patch everything by Friday" · **Where:** Ubuntu packages, Docker images, Traefik and Dokploy versions · **Level:** [L2 · Mid-level] · **How common:** weekly on r/sysadmin, and patching bites back: the Docker 29 upgrade broke Traefik and Dokploy routing and became one of the most-viewed Docker forum topics of its year

**Why it happens:** without an inventory of versions nobody can answer quickly, so teams either panic-patch every host at once or do nothing. Patching the host does not fix the libraries inside container images. And a big upgrade (Docker engine, kernel) can break things the CVE never would have.

**Diagnose:**

```bash
# Hosts: installed version, to compare with the fixed version in the Ubuntu security notice
ansible all -i inventory/prod.ini -m shell -a "dpkg-query -W -f='\${Version}\n' openssh-server"
# Images: what is inside what we run
trivy image --severity CRITICAL,HIGH --ignore-unfixed harbor.example.com/shop/web:a41f9c2 | grep -E '^Total|CVE-'
```

```text
dokploy-1 | CHANGED | rc=0 >>
1:9.6p1-3ubuntu13.13
dokploy-2 | CHANGED | rc=0 >>
1:9.6p1-3ubuntu13.13
Total: 2 (HIGH: 2, CRITICAL: 0)
│ libssl3t64 │ CVE-2026-NNNNN │ HIGH │ fixed │ 3.0.13-0ubuntu3.5 │ 3.0.13-0ubuntu3.6 │ openssl: ... │
│ openssl    │ CVE-2026-NNNNN │ HIGH │ fixed │ 3.0.13-0ubuntu3.5 │ 3.0.13-0ubuntu3.6 │ openssl: ... │
```

**What the output tells you:** decide per CVE with three questions: is our version affected (compare with the notice), is it exposed (sshd here is reachable only over the VPN), and is it exploited in the wild (CISA's KEV list)? Affected, exposed and exploited means today; affected but not exposed means the next patch window.

**Fix:** patch in rings, with a check between each.

```bash
# Ring 0: lab VM. Ring 1: one production host. Ring 2: the rest.
ansible lab -b -m apt -a "name=openssh-server state=latest update_cache=true"
ansible dokploy-2 -b -m apt -a "name=openssh-server state=latest update_cache=true"
# Hold packages whose upgrades need their own change and testing
sudo apt-mark hold docker-ce docker-ce-cli containerd.io
# Images: rebuild on a patched base image and redeploy through the pipeline
```

**Why this fix works:** rings catch a bad patch on one host instead of all of them, holds stop a routine upgrade from changing the Docker engine under Traefik, and rebuilt images fix what host patching cannot. Don't run `apt upgrade` on every host at once in business hours, and don't answer "not affected" without the version evidence.

**Prevent it:** a version inventory (Ansible facts, SBOMs from the pipeline), a monthly patch window, weekly image rebuilds, KEV-based priorities, and reading release notes for Docker, Traefik and Dokploy before upgrading.

**Next step:** [Security & DevSecOps](37-learn-security-devsecops.md) §11 Vulnerability and patch management · [Packages](11-packages.md) · [Wazuh & security tools](48-wazuh-and-security-tools.md) · [Ubuntu security notices](https://ubuntu.com/security/notices) · [Trivy docs](https://trivy.dev/)

**Community threads:** [Docker forums: Docker 29 breaks Traefik](https://forums.docker.com/t/docker-29-increased-minimum-api-version-breaks-traefik-reverse-proxy/150384) · [Ubuntu Server docs: automatic updates](https://ubuntu.com/server/docs/how-to/software/automatic-updates/) · Search: [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=patch+management+cve+priority&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=unattended-upgrades+docker+restart)

---

## 9. On-call and incident response in practice

### Before, during and after a shift

**Before the shift:** take the handoff (what fired, what is still open, which risky changes are scheduled), check that every access works (VPN, SSH, Dokploy, Grafana, GitLab, the AWS console), charge the laptop, and know who your secondary and the service owners are. Finding out at 3 AM that your VPN certificate expired is a classic first page.

**When the pager goes:** acknowledge within the agreed time (the SRE book suggests about 5 minutes for user-facing services and 30 for less critical ones), check user impact before anything else, mitigate before you investigate (roll back, fail over, scale, block), and say what you are doing in the incident channel. Declare a formal incident when a second team is needed, when customers can see the problem, or when it is still unsolved after an hour of focused work; those are the SRE book's own criteria.

**After the page:** write the timeline while it is fresh, update or create the runbook, file tickets for the causes, hand over in writing, and take the rest you are owed. A night of pages followed by a normal working day is how mistakes happen.

### Incident roles on a small team

| Role | Does | Does not |
|---|---|---|
| Incident commander (IC) | holds the overall picture, assigns work, decides, keeps the live incident document | type commands into production |
| Operations lead | the only person who changes production, announcing each change first | talk to stakeholders |
| Communications | posts status updates on a fixed schedule, answers stakeholders | debug |
| Scribe (optional) | records the timeline with timestamps | make decisions |

On a three-person team one person can be IC and communications, but never IC and operations lead in a big incident: someone has to keep their head out of the terminal. Hand over command explicitly ("you are now IC") and write it down.

### A status update template

```text
[10:30 UTC] Checkout errors: INVESTIGATING -> MITIGATING
Impact:   about 9% of checkouts fail since 09:12; browsing works.
Doing:    rolled back to the 7d0e3b1 release at 10:24; error rate falling.
Next:     confirm recovery, then find why the new release exhausted DB connections.
Next update: 11:00 UTC or sooner if anything changes.   IC: Priya · Comms: Sam
```

### What a healthy rotation looks like

The SRE book treats about six hours as the full cost of one incident (response, cleanup, postmortem), which caps a sustainable load at about two incidents per 12-hour shift, with a median of zero. It recommends at least eight engineers for a single-site rotation (six per site for two sites), no more than 25% of time on-call, and on-call at least once or twice a quarter for everyone so skills don't fade. In an Ask HN thread on how often people get paged, healthy rotations reported anything from one or two pages a month to one or two a week, while several people described five to seven a day as the sign of a broken system. Small on-prem teams can't reach eight people; section 16 covers how to stay sustainable anyway.

### 9.1 Paged by an alert you don't understand

> **Seen as:** `[FIRING:1] HostHighLoad instance=10.10.0.20:9100` at 02:14, with no runbook link and no dashboard · **Where:** Alertmanager or Grafana alerting to your phone · **Level:** [L1 · Junior] · **How common:** vague, unowned alerts come up again and again in Ask HN on-call threads, and the SRE book names clear procedures and escalation paths as the main way to keep on-call stress manageable

**Why it happens:** the alert was written by someone who has left, it measures a cause (load) rather than a symptom users feel (errors, latency), and it carries no runbook. As the newest person on the rotation, you also don't yet know what normal looks like.

**Diagnose:**

```bash
# What fired, since when, with which labels?
amtool alert query alertname=HostHighLoad --alertmanager.url=http://10.10.0.10:9093 -o extended
# Are users affected? Check the user-facing signal first
curl -s -o /dev/null -w '%{http_code} %{time_total}s\n' https://shop.example.com/healthz
# What is the host doing?
ssh dokploy-2 'uptime; journalctl --since -1h --no-pager -g "^Started" | tail -3'   # unit starts are logged at info level
```

```text
Labels                                                 Annotations                       Starts At
alertname="HostHighLoad" instance="10.10.0.20:9100"   summary="Load above 8 for 10m"    2026-10-04 02:04:11 UTC
200 0.284s
 02:16:40 up 41 days, 3:02,  0 users,  load average: 9.12, 8.80, 7.95
Oct 04 02:00:01 dokploy-2 systemd[1]: Started restic-backup.service - Nightly restic backup.
Oct 04 02:16:40 dokploy-2 systemd[1]: Started session-912.scope - Session 912 of User ops.
```

**What the output tells you:** users are fine (200 in 0.28 s), and the load comes from the nightly backup that started at 02:00. This is not an emergency. It is an alert that should never page at night.

**Fix:**

```text
1. Acknowledge and note it: "HostHighLoad dokploy-2: nightly backup, no user impact (healthz 200, 0.28 s). Not acting."
2. If you can't tell within 15 minutes whether users are affected, escalate to the secondary. Asking is part of the job.
3. In the morning, file a ticket to fix the alert (below), and add what you learned to the runbook.
```

```yaml
- alert: HostHighLoad
  expr: node_load15 / count without (cpu, mode) (node_cpu_seconds_total{mode="idle"}) > 2
  for: 30m
  labels:
    severity: ticket            # no user impact by itself: never a page
  annotations:
    summary: "Load per CPU above 2 for 30m on {{ $labels.instance }}"
    runbook_url: "https://wiki.example.com/runbooks/host-high-load"
```

**Why this fix works:** user impact decides urgency, a time box stops you struggling alone at 3 AM, and fixing the alert means the next person sleeps. Don't silence it for a week without a ticket, and don't reboot the host to make the alert stop.

**Prevent it:** every paging alert has an owner, a runbook link and a dashboard link; new alerts are reviewed in a merge request; and new people shadow a shift before their first solo week.

**Next step:** [Observability](49-observability-stack-problems.md) entries 8.1 and 8.4 · [Site down](25-playbook-site-down.md) · [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) §7 SRE practice · KodeKloud: *Fundamentals of SRE* — Incident Management (Designing Effective Alerts) · [Prometheus docs](https://prometheus.io/docs/)

**Community threads:** [Google SRE book: Being On-Call](https://sre.google/sre-book/being-on-call/) · [Ask HN: What is your company's on-call rotation like?](https://news.ycombinator.com/item?id=10892771) · Search: [Reddit r/sre](https://www.reddit.com/r/sre/search/?q=alert+without+runbook&restrict_sr=1) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=on-call+first+page+junior&restrict_sr=1)

### 9.2 Pages every night: alert fatigue

> **Seen as:** four pages last night, three closed as "no action needed" · **Where:** Alertmanager or Grafana on-call · **Level:** [L2 · Mid-level] · **How common:** in the Ask HN thread on how often people are paged, the difference between bearable and miserable rotations came down to alert hygiene and fixing causes; the SRE book calls on-call above 25% of time "operational overload"

**Why it happens:** alerts on causes (CPU, load) instead of symptoms (errors, latency), thresholds without a `for:` duration, one alert per instance with no grouping, flapping during deploys, and nobody owning alert quality. Every page that needs no action teaches people to ignore pages.

**Diagnose:** count pages and how many needed action, over four weeks.

```bash
# Export the page history from your on-call tool or Alertmanager receiver log to CSV, then count
cut -d, -f2,5 pages-september.csv | sort | uniq -c | sort -rn | head -5
```

```text
     41 HostHighLoad,no-action
     17 DiskSpaceLow,manual-cleanup
      9 TargetDown,no-action
      4 ShopCheckoutErrors,rolled-back
      2 CertExpirySoon,renewed
```

**What the output tells you:** 73 pages in a month and 50 of them (68%) needed nothing. HostHighLoad is a cause alert, TargetDown flaps during deploys, and DiskSpaceLow is the same manual cleanup 17 times, which is toil (entry 7.1). Only ShopCheckoutErrors is a real symptom page.

**Fix:**

```text
1. Demote HostHighLoad to ticket-only (entry 9.1).
2. TargetDown: add "for: 5m", group by service, inhibit it during deploy windows.
3. DiskSpaceLow: automate the cleanup it keeps asking for and switch to a trend alert.
4. Keep and improve symptom alerts: error rate and latency per user journey, each with a runbook.
5. New rule: any page that needed no action gets a ticket to fix or delete that alert within a week.
```

**Why this fix works:** pages are a scarce resource, and removing noise makes the remaining pages believable again. Turning repeated manual fixes into automation removes the page and the toil together. Don't just raise every threshold until nothing fires, and never mute the pager.

**Prevent it:** a short weekly review of pages at the on-call handoff, an owner per alert, and a team target such as fewer than two out-of-hours pages per on-call week.

**Next step:** [Observability](49-observability-stack-problems.md) entry 8.4 · section 16 of this module · KodeKloud: *Fundamentals of SRE* — Incident Management (Designing Effective Alerts) · [Prometheus docs](https://prometheus.io/docs/)

**Community threads:** [Ask HN: For those on call, how often are you called?](https://news.ycombinator.com/item?id=21039191) · [Google SRE book: Being On-Call](https://sre.google/sre-book/being-on-call/) · Search: [Reddit r/sre](https://www.reddit.com/r/sre/search/?q=alert+fatigue&restrict_sr=1) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=alert+fatigue+pagerduty&restrict_sr=1)

### 9.3 Big outage, everyone in the call, nobody leading

> **Seen as:** 25 people in a call, four of them restarting things, and a director asking for an ETA every five minutes · **Where:** any outage that touches more than one team · **Level:** [L3 · Senior] · **How common:** the reason incident command exists; the SRE book's incident chapter defines the roles, a live incident document and explicit handoffs for exactly this situation

**Why it happens:** nobody declared an incident, so nobody owns it. People make uncoordinated changes, so nobody knows which change helped or hurt. With no updates, stakeholders fill the silence by interrupting the responders.

**Diagnose:** the facts to establish in the first two minutes.

```text
Is there an incident channel?            no      -> create #inc-20261004-checkout
Who is incident commander?               nobody  -> the most senior person NOT typing commands
Who may change production?               anyone  -> only the operations lead, announcing each change
When is the next status update?          never   -> every 30 minutes, by the comms person
Where is the timeline?                   scrollback -> a live incident document
```

**What the output tells you:** every "nobody" or "anyone" is a gap that makes the outage longer. Fill them before anyone runs another command.

**Fix:**

```text
IC, out loud in the call: "I'm incident commander. Operations lead: Priya. Comms: Sam. Scribe: Lee.
Only Priya changes production, and she says what she will change before she does it.
Everyone else investigates read-only and reports to me. Next update at 10:30."
```

**Why this fix works:** one person holds the state, changes happen one at a time so you know what fixed it, and regular updates protect the people doing the work. Don't let the strongest engineer be IC and also type the commands, and don't wait to send an update until you know the cause.

**Prevent it:** written severity levels and declaration criteria, channel and document templates, roles practised on game days, and an IC role that rotates so more than one person can do it.

**Next step:** [Site down](25-playbook-site-down.md) §10 Communicating during an outage · [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) §8 game day · [Practice Arena](54-practice-arena.md) §10 · KodeKloud: *Fundamentals of SRE* — Incident Management (IMAG roles)

**Community threads:** [Google SRE book: Managing Incidents](https://sre.google/sre-book/managing-incidents/) · [Google SRE book: Accelerating SREs to on-call](https://sre.google/sre-book/accelerating-sre-on-call/) · Search: [Reddit r/sre](https://www.reddit.com/r/sre/search/?q=incident+commander+small+team&restrict_sr=1) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=incident+management+roles&restrict_sr=1)

### 9.4 Users reported it before monitoring did

> **Seen as:** support writes "checkout has been failing for 40 minutes" while every dashboard is green · **Where:** a monitoring stack that watches hosts but not user journeys · **Level:** [L2 · Mid-level] · **How common:** a postmortem trigger on its own in the SRE book: a monitoring failure, where people found the problem by hand

**Why it happens:** only host metrics (CPU, disk) are monitored; the probe hits a /healthz that does not touch the database or the payment provider; the alert goes to an old mailbox; or Alertmanager itself is down and nothing watches it.

**Diagnose:**

```bash
# Does any probe or rule watch the failing journey?
grep -rln 'checkout' monitoring/blackbox/ monitoring/prometheus/rules/ || echo 'no checkout probe or rule'
# Is the alert pipeline alive end to end?
curl -s http://10.10.0.10:9093/api/v2/status | jq -r '.cluster.status'
```

```text
no checkout probe or rule
ready
```

**What the output tells you:** Alertmanager is healthy, but nothing watches checkout, and the existing probe is a /healthz that returns 200 without touching payment. Monitoring did exactly what it was told; it was told the wrong thing.

**Fix:**

```yaml
# Probe the journey, not just the process, and alert on the symptom
- alert: CheckoutProbeFailing
  expr: probe_success{job="blackbox-checkout"} == 0
  for: 3m
  labels:
    severity: page
  annotations:
    summary: "Checkout journey failing from the outside"
    runbook_url: "https://wiki.example.com/runbooks/checkout"
```

**Why this fix works:** an outside probe of the real journey, plus an error-rate alert on the checkout route from Traefik's metrics, sees what customers see. Add a dead man's switch (an always-firing Watchdog alert to an external heartbeat) so a dead alert pipeline is noticed too. Don't stop at a deeper /healthz that the app answers itself.

**Prevent it:** every critical user journey has a probe and an error-rate alert, "found by users" is an automatic postmortem, and once a month ask "who would notice first if this broke?" for each service.

**Next step:** [Observability](49-observability-stack-problems.md) entries 5.4 and 8.1 · [Performance & observability](32-learn-performance-observability.md) · KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Alerting · [Prometheus docs](https://prometheus.io/docs/)

**Community threads:** [Google SRE book: Postmortem Culture](https://sre.google/sre-book/postmortem-culture/) · Search: [Reddit r/sre](https://www.reddit.com/r/sre/search/?q=customers+noticed+outage+before+monitoring&restrict_sr=1) · [Reddit r/PrometheusMonitoring](https://www.reddit.com/r/PrometheusMonitoring/search/?q=blackbox+exporter+user+journey&restrict_sr=1)

### 9.5 The same incident happens again

> **Seen as:** "didn't we have exactly this outage in March?" · **Where:** any team without a working postmortem habit · **Level:** [L3 · Senior] · **How common:** the SRE book lists when a postmortem is due (user-visible downtime, any data loss, on-call intervention, a long resolution, a monitoring failure); in the Ask HN on-call threads, teams that fix causes are the ones with bearable rotations

**Why it happens:** the fix at 3 AM was a symptom fix, the postmortem was skipped or turned into blame, and action items had no owner or date, so nothing changed.

**Diagnose:**

```bash
# Same alert, same cause, over the year (incident tracker export)
grep -i 'ShopCheckoutErrors' incidents-2026.csv | cut -d, -f1,4
```

```text
2026-03-11,DB connection pool exhausted
2026-06-02,DB connection pool exhausted
2026-10-04,DB connection pool exhausted
```

**What the output tells you:** the same cause three times this year. The March postmortem had the action "increase the pool", with no owner and no date, and it was never done.

**Fix:** a short, blameless postmortem with owned actions, reviewed until closed.

```text
Postmortem OPS-1502: checkout errors, 2026-10-04 (blameless)
Impact:     89 minutes (09:12-10:41), about 9% of checkouts failed; the first 41 went unnoticed
Timeline:   09:12 deploy · 09:53 support reports · 10:12 IC named · 10:24 rollback · 10:41 recovered
Causes:     3 replicas x 40 pool slots > Postgres max_connections 100; no alert on pool saturation
Went well:  rollback in 12 minutes once an IC was named
Went wrong: found by support, not monitoring; the March action was never done
Actions:    1. PgBouncer in front of Postgres        Priya  2026-10-18  OPS-1503
            2. Alert on connection pool saturation   Sam    2026-10-11  OPS-1504
            3. Open postmortem actions reviewed weekly at the handoff   Lead   ongoing
```

**Why this fix works:** blamelessness is what makes people tell the whole story, and owners plus dates plus a weekly review are what make actions happen. "Human error" is where the analysis starts, not where it ends: ask what made the mistake easy. Don't name a person as the root cause.

**Prevent it:** written postmortem triggers, a template, a weekly look at open actions, and a monthly "postmortem of the month" or reading club.

**Next step:** [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) §7 SRE practice (full template) · [Practice Arena](54-practice-arena.md) §10 · KodeKloud: *Fundamentals of SRE* — [Blameless Postmortem Culture](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page) and [Root Cause Analysis](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Root-Cause-Analysis/page)

**Community threads:** [Google SRE book: Postmortem Culture](https://sre.google/sre-book/postmortem-culture/) · [Dan Luu's post-mortems](https://github.com/danluu/post-mortems) · Search: [Reddit r/sre](https://www.reddit.com/r/sre/search/?q=blameless+postmortem+action+items&restrict_sr=1) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=postmortem+action+items+never+done&restrict_sr=1)

---

## 10. Changes that go wrong and change hygiene

Most outages in public postmortem collections start with a change: a config push, a deploy, an upgrade, a command typed on the wrong host. Change hygiene is the set of small habits that make those changes boring.

### The change checklist

Before every production change, be able to answer:

1. **What and why?** One sentence, with the ticket.
2. **Blast radius?** Which hosts, services and users can it touch? Can it be smaller (one host first)?
3. **Exact plan?** The commands or the merge request, not "update the config".
4. **Pre-checks?** Validation (`nginx -t`, `promtool check config`, `terraform plan`, `ansible-playbook --check --diff`) and the current state saved.
5. **How will I verify?** The URL, query or command that proves it worked, and how long to watch.
6. **How do I undo it?** A rollback you have tried, with how long it takes.
7. **When and who knows?** Not in peak hours, not late on Friday, announced in the team channel, monitoring open while you work.

DORA's research on [change approval](https://dora.dev/capabilities/) finds that a clear, lightweight process with peer review beats heavyweight approval boards for both speed and stability, and lowers burnout. The checklist is that lightweight process.

### A change record template

```text
Change OPS-1511: Traefik security-headers middleware on all routers
Risk: medium (every site)   Window: Tue 14:00-15:00 UTC   Owner: ops   Reviewer: Priya (MR !412)
Plan:      merge !412; ansible-playbook traefik.yml --limit dokploy-2; verify; then dokploy-1
Pre-check: ansible-playbook traefik.yml --check --diff; traefik config check in CI
Verify:    curl -sI https://shop.example.com | grep -i strict-transport-security; 5xx rate flat for 15 min
Rollback:  git revert, re-run playbook (about 3 min, tested in the lab)
Comms:     announced in #ops at 13:50; done or rolled back message at the end
```

### Guard rails that prevent the classics

- **Make production look different:** a red prompt, a different terminal profile, and hostnames with "prod" in them.
- **Go narrow first:** Ansible `--limit` and `serial: 1`, Swarm and Kubernetes rolling updates with health checks, one canary before the rest.
- **Validate before applying:** config checks in CI, `--check --diff`, `terraform plan` saved and applied as a plan file.
- **Make destructive commands slow:** wrapper scripts that ask you to type the hostname, read-only database users by default, a second person for anything irreversible.
- **Feed emergency changes back into Git** before the incident is closed (entry 10.3).

### 10.1 A routine config change takes production down

> **Seen as:** "everything was fine until the change at 14:02": every site behind Traefik returns 404 after a middleware edit pushed to all hosts at once · **Where:** Ansible-managed Traefik dynamic config on the Dokploy hosts · **Level:** [L2 · Mid-level] · **How common:** config errors are the first and largest section of Dan Luu's postmortem collection: a bad router rule that crashed every edge router, a typo during maintenance that sent all traffic to one data centre, autogenerated config that withdrew a provider's IP blocks, a firewall rule that blocked a whole site

**Why it happens:** the change went to every host at once, nothing validated it, there was no canary and no written rollback, and the tool happily applied it everywhere. The bug itself is usually tiny: a typo, a missing reference, a wrong default.

**Diagnose:**

```bash
# What changed, and when? Correlate with the first error
git -C infra log --since '3 hours ago' --format='%h %ad %an %s' --date=format:%H:%M
grep -h -A3 'PLAY RECAP' /var/log/ansible/2026-10-04-1401.log
docker logs --since 20m dokploy-traefik 2>&1 | grep -i 'middleware' | tail -1
```

```text
e91b3c0 14:01 ops traefik: add security-headers middleware to all routers
a71f0d2 11:20 ops ufw: allow 9100 from monitoring
PLAY RECAP *********************************************************************
dokploy-1                  : ok=6    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
dokploy-2                  : ok=6    changed=1    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
2026-10-04T14:02:09Z ERR error="middleware \"security-headers@file\" does not exist" entryPointName=websecure routerName=shop-web@swarm
```

**What the output tells you:** one commit changed both hosts at 14:01, and Traefik now refuses routers that reference a middleware name that doesn't exist (a typo in the file provider's name). Routers with a broken reference are disabled, so every request gets 404.

**Fix:** roll back first, then make the next rollout narrow and verified.

```bash
git -C infra revert --no-edit e91b3c0
ansible-playbook -i inventory/prod.ini traefik.yml --diff
```

```yaml
# traefik.yml: one host at a time, stop at the first failure, verify before moving on
- hosts: dokploy
  serial: 1
  max_fail_percentage: 0
  tasks:
    # ... render and reload the config, then:
    - name: The site still answers through Traefik
      ansible.builtin.uri:
        url: https://shop.example.com/healthz
        status_code: 200
      delegate_to: localhost
```

**Why this fix works:** a revert restores a known-good state in minutes, and `serial: 1` with a verify task means the next mistake stops at one host. Don't fix forward under pressure with another untested edit: two unknown changes are worse than one.

**Prevent it:** the checklist and change record above, a config check in CI, canary hosts, and changes announced before they happen.

**Next step:** [Deployment patterns](35-deployment-patterns.md) · [Traefik deep dive](43-traefik-and-reverse-proxies.md) · [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) §4 Ansible · KodeKloud: *Fundamentals of SRE* — [Change Management for Reliability](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page) · [Ansible docs](https://docs.ansible.com/)

**Community threads:** [Dan Luu's post-mortems (Config Errors)](https://github.com/danluu/post-mortems) · [DORA capabilities](https://dora.dev/capabilities/) · Search: [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=change+broke+production+rollback&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=ansible+serial+rolling+update)

### 10.2 Ran the command on the wrong server

> **Seen as:** "I think I just truncated the table on prod, not staging" · **Where:** SSH sessions with identical prompts, late at night, many tabs · **Level:** [L1 · Junior] · **How common:** GitLab's 2017 outage began when an engineer deleted a database directory on the primary while believing they were on the replica, and Amazon's 2017 S3 outage began with a mistyped command that removed far more servers than intended

**Why it happens:** production and staging look identical, the engineer is tired, a runbook command is pasted into the wrong tab, and nothing asks "are you sure?" before a destructive action.

**Diagnose:** the first five minutes: stop typing, establish facts, tell someone.

```bash
hostname -f; whoami; date -u          # where am I, as whom, when (for the timeline)
history | tail -4                     # exactly what ran (the last line is this command itself)
```

```text
db-prod-1.example.com
postgres
Sun Oct  4 21:47:10 UTC 2026
  981  psql -c 'DROP TABLE IF EXISTS orders_archive_tmp;'
  982  psql -c 'TRUNCATE orders_archive;'
  983  hostname -f; whoami; date -u
  984  history | tail -4
```

**What the output tells you:** you are on production and the truncate ran. Stop here: tell the on-call lead now, declare an incident if the data matters to users, and recover from backup with a second person reviewing each step (entry 7.4). Entry 16.2 covers the human side.

**Fix:** after the recovery, make production impossible to mistake.

```bash
# /etc/profile.d/prod-prompt.sh, pushed by Ansible to production hosts only
case "$(hostname)" in
  *prod*) PS1='\[\e[1;37;41m\] PROD \[\e[0m\] \u@\h:\w\$ ' ;;
esac
```

**Why this fix works:** a red PROD banner breaks the autopilot that causes these mistakes. Pair it with read-only database users by default and a wrapper that asks you to type the hostname before destructive scripts run. Don't hide what happened: the first ten minutes of honesty decide how bad the outcome is.

**Prevent it:** coloured production prompts, separate SSH configs or jump hosts per environment, read-only defaults, a second person for irreversible commands, and restores you have rehearsed.

**Next step:** [SSH and remote access](09-ssh-remote-access.md) · [Databases, storage & backups](51-problems-databases-storage-backup.md) entry 9.3 · entry 16.2 · KodeKloud: *Advanced Bash Scripting* — Good Practices Applied · [Bash manual](https://www.gnu.org/software/bash/manual/)

**Community threads:** [GitLab: postmortem of the database outage of 31 January 2017](https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/) · [Dan Luu's post-mortems](https://github.com/danluu/post-mortems) · Search: [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=ran+command+on+wrong+server&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=bash+prompt+color+production+server)

### 10.3 A hand-edited server drifts from Git

> **Seen as:** the next Ansible run silently reverts last week's hotfix, or `terraform plan` wants to change things nobody touched · **Where:** servers managed by Ansible, cloud resources managed by Terraform · **Level:** [L2 · Mid-level] · **How common:** drift is a top theme in the most-commented terraform-provider-aws issues, and "automation reverted my fix" is an ops classic

**Why it happens:** during an incident someone fixed the server by hand, and nobody copied the fix back into Git. The automation still believes the old state, so its next run "repairs" the fix and breaks production again.

**Diagnose:**

```bash
# What would automation change on this host right now?
ansible-playbook -i inventory/prod.ini site.yml --check --diff --limit dokploy-1 | grep -B2 -A6 'legacy-apache'
```

```text
TASK [traefik : Render dynamic config] ***************************************
--- before: /etc/dokploy/traefik/dynamic/legacy-apache.yml
+++ after: /home/ops/.ansible/tmp/ansible-local-1182/legacy-apache.yml.j2
@@ -7,7 +7,7 @@
-          - url: "http://10.10.0.10:8081"
+          - url: "http://10.10.0.10:81"
changed: [dokploy-1]
```

**What the output tells you:** the live server points the legacy Apache route at 8081, but Git still says 81. The next real run would revert it and break the legacy sites. The ticket history shows why: Apache moved to 8081 during incident OPS-1388.

**Fix:** bring the hotfix into Git, review it, and prove automation agrees.

```bash
sed -i 's#10.10.0.10:81"#10.10.0.10:8081"#' roles/traefik/templates/legacy-apache.yml.j2
git commit -am "traefik: legacy Apache backend on 8081 (hotfix from OPS-1388)"
ansible-playbook -i inventory/prod.ini site.yml --check --diff --limit dokploy-1    # expect: changed=0
```

**Why this fix works:** Git is only the source of truth if emergency changes flow back into it, and a check run with no changes proves that they did. Don't run the playbook "to clean up" before you know why the server differs.

**Prevent it:** a rule that every emergency change gets a "back into Git" task before the incident closes, a nightly `--check --diff` job (and `terraform plan -refresh-only`) that alerts on drift, and direct edits on servers reserved for incidents.

**Next step:** [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) §4 Ansible and §5 Terraform · [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) · [Apache on 443 case](21-case-apache-443-dokploy.md) · KodeKloud: *Ansible Basics Course* — Playbooks · [Ansible docs](https://docs.ansible.com/)

**Community threads:** [terraform-provider-aws issues by comments](https://github.com/hashicorp/terraform-provider-aws/issues?q=is%3Aissue+sort%3Acomments-desc) · Search: [Reddit r/ansible](https://www.reddit.com/r/ansible/search/?q=check+diff+drift+detection&restrict_sr=1) · [Server Fault](https://serverfault.com/search?q=configuration+drift+ansible)

### 10.4 An upgrade broke a dependent tool

> **Seen as:** after a routine `apt upgrade`, every Dokploy domain returns 404 and Traefik logs `client version 1.24 is too old` · **Where:** Docker engine upgrades under Traefik, Portainer or Dokploy; unattended-upgrades · **Level:** [L2 · Mid-level] · **How common:** Docker 29 raised the minimum API version and broke Traefik, Portainer and Dokploy routing; the Docker forum thread drew about 41,000 views and the Portainer issue hundreds of comments

**Why it happens:** one package upgrade changes an interface another component depends on. A blanket `apt upgrade` or unattended-upgrades pulled in a new major Docker engine, and nobody read the release notes first.

**Diagnose:**

```bash
grep -E ' upgrade (docker-ce|containerd)' /var/log/dpkg.log | tail -1
docker version --format '{{.Server.Version}} (min API {{.Server.MinAPIVersion}})'
docker logs --since 30m dokploy-traefik 2>&1 | grep -i 'too old' | tail -1
```

```text
2026-10-04 06:25:13 upgrade docker-ce:amd64 5:28.5.2-1~ubuntu.24.04~noble 5:29.1.2-1~ubuntu.24.04~noble
29.1.2 (min API 1.44)
... Error response from daemon: client version 1.24 is too old. Minimum supported API version is 1.44, please upgrade your client to a newer version
```

**What the output tells you:** the engine moved from 28 to 29 at 06:25, and Traefik's Docker provider still speaks an API version the new engine refuses. The apps themselves are running; only routing is broken.

**Fix:**

```bash
# Mitigate now: let the daemon accept the older API again
#   /etc/docker/daemon.json: { "min-api-version": "1.24" }
sudo systemctl restart docker
docker version --format '{{.Server.MinAPIVersion}}'        # expect 1.24
# Real fix: update Traefik to v3.6.1 or newer through Dokploy's update path, then remove the override
# Stop surprise engine upgrades: hold the packages and upgrade them in a change window
sudo apt-mark hold docker-ce docker-ce-cli containerd.io
```

**Why this fix works:** the override restores routing in minutes, the client upgrade removes the need for it, and the hold turns the next engine upgrade into a planned change. Don't leave the override in place for good, and don't downgrade without a hold, or the next upgrade run repeats the outage.

**Prevent it:** read the release notes for Docker, Traefik and Dokploy before upgrading, keep Docker out of unattended-upgrades, upgrade the lab first, and roll out in rings (entry 8.3).

**Next step:** [Docker, Swarm & registry problems](44-problems-docker-swarm-registry.md) · [Dokploy deep dive](45-dokploy-and-self-hosted-paas.md) entry 6.5 · [Packages](11-packages.md) · KodeKloud: DCA [*Troubleshooting Docker Daemon*](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Engine/Troubleshooting-Docker-Daemon/page) · [Docker docs](https://docs.docker.com/)

**Community threads:** [Docker forums: Docker 29 breaks Traefik](https://forums.docker.com/t/docker-29-increased-minimum-api-version-breaks-traefik-reverse-proxy/150384) · [Portainer issue #12925](https://github.com/portainer/portainer/issues/12925) · [Ubuntu Server docs: automatic updates](https://ubuntu.com/server/docs/how-to/software/automatic-updates/) · Search: [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=docker+29+client+version+too+old+traefik&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=%22client+version+1.24+is+too+old%22)

---

## 11. Toil and interruptions

### What counts as toil

The SRE book defines toil as work tied to running a service that is manual, repetitive, automatable, tactical (interrupt-driven), leaves no lasting value, and grows with the size of the service. Meetings are overhead, not toil. Grungy work that permanently improves something (cleaning up alerts, writing the automation) is engineering. A little toil is fine and even satisfying; the danger is when it quietly takes over the week, stalls your career and burns people out.

### Measure it before you fight it

For four weeks, tag every ticket and interruption with a type and the minutes spent. Hours per month for each type is count times minutes. The top three types are your automation backlog, and the totals are the argument your manager needs.

### The automation ladder

Climb one rung at a time, and only as far as the numbers justify:

1. **Document it:** a runbook anyone on the team can follow (section 13).
2. **Script it:** one command or a CI job with parameters.
3. **Make it self-service:** a merge request, a form or a pipeline the requester runs themselves, with guard rails.
4. **Eliminate it:** change the design so the request never arises (ACME instead of manual certificates, log rotation instead of disk cleanups).

A rule many engineers use: the second time you do something, write it down; the third time, script it.

### Protect project time with an interrupt shield

Rotate one person per week who takes all tickets and chat questions, so everyone else gets uninterrupted project time. On small teams the shield is often the on-call person. The shield does not do project work that week, which is also the advice from on-call threads: on-call engineers do better when they are not expected to deliver projects at the same time.

### 11.1 Toil eats the week

> **Seen as:** "I spent the whole week on tickets again", and the same project slips every sprint · **Where:** any ops team without measurement · **Level:** [L2 · Mid-level] · **How common:** Google's quarterly surveys put the average SRE at about a third of their time on toil, with individuals up to 80%, against a cap of 50%; interrupts, on-call and releases are the biggest sources

**Why it happens:** nobody measures, so toil is invisible. The same requests are handled by hand forever because each one only takes ten minutes, and releases still need a person to babysit them.

**Diagnose:**

```bash
# Ticket export for four weeks: column 3 = type, column 5 = minutes spent
awk -F, 'NR>1 {n[$3]++; m[$3]+=$5} END {for (t in n) printf "%-20s %3d tickets %5.1f h\n", t, n[t], m[t]/60}' tickets-sept.csv \
  | sort -k4 -rn | head -5
```

```text
access-request        38 tickets  19.0 h
disk-cleanup          17 tickets  11.3 h
deploy-help           14 tickets   9.8 h
dns-record            22 tickets   7.3 h
cert-renewal-manual    6 tickets   6.0 h
```

**What the output tells you:** 53 hours in a month, more than a person-week, went on five repeatable request types. Access requests are the biggest block and a good candidate for self-service; disk cleanups need automation plus the root-cause fix from entry 7.1; DNS records can become merge requests; manual certificate renewals should move to ACME.

**Fix:** take the top type up the ladder. For DNS records, for example, developers open a merge request and CI validates and applies it (with a tool such as OctoDNS or Terraform's DNS providers):

```yaml
# dns/zones/example.com.yml
records:
  - name: app
    type: A
    value: 203.0.113.10
    ttl: 300
    owner: team-shop
    ticket: OPS-1520
```

**Why this fix works:** count times minutes shows where automation pays back, and self-service takes you out of the loop while review and CI keep it safe. Don't automate a process you have never written down, and don't build a platform for a request that comes twice a year.

**Prevent it:** a quarterly toil review, toil hours as a team metric, and a target of keeping operational work under half of everyone's time.

**Next step:** [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) §7 SRE practice · [Career ladder](40-career-ladder.md) §10 Building proof (toil cut is strong evidence) · KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil

**Community threads:** [Google SRE book: Eliminating Toil](https://sre.google/sre-book/eliminating-toil/) · Search: [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=toil+automation&restrict_sr=1) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=automate+repetitive+tickets&restrict_sr=1)

### 11.2 Every request arrives by DM

> **Seen as:** twelve "quick questions" before lunch, across five channels and three DMs, while the ticket queue looks empty · **Where:** chat-first teams · **Level:** [L1 · Junior] · **How common:** a 2025 Ask HN thread asked how other teams run the DevOps support ticket lifecycle, and "people DM me instead of filing a ticket" is a perennial r/sysadmin complaint

**Why it happens:** there is no single front door, answering DMs rewards DMs, nobody shields the team, and because none of it is tracked, the manager never sees the load.

**Diagnose:** tally one week of interruptions in a text file as they happen.

```text
Mon-Fri interruptions: 61   (DM 34, #dev-help 19, in person 8)
Took more than 15 min: 22   Became a ticket: 3
Asked 3+ times: "how do I see my app's logs?" (9), "why is my pipeline stuck?" (7)
```

**What the output tells you:** 61 interruptions and only 3 tracked, so most of your work is invisible. Two questions make up a quarter of the load and can be answered once in writing.

**Fix:**

```text
1. One door: #ops-requests with a four-line form (what, why, by when, owner). DMs get a friendly redirect:
   "Happy to help. Can you post it in #ops-requests with the form? Whoever is on shield picks it up today."
2. An interrupt shield: one person per week answers #ops-requests; everyone else is protected.
3. Short how-tos for the repeat questions (logs in Grafana, stuck pipelines) pinned in the channel.
4. Weekly numbers to your manager: requests, hours, top types.
```

**Why this fix works:** one door makes the work visible and batchable, the shield absorbs the context switches, and written answers stop the repeats. Don't ignore DMs; redirect kindly and consistently, every time.

**Prevent it:** a short service catalogue (what we do, how to ask, how fast), office hours for developers, and the shield rota on the team calendar.

**Next step:** [Career ladder](40-career-ladder.md) §11 Soft skills · section 13 of this module · [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) §7 SRE practice

**Community threads:** [Ask HN: What does your DevOps support ticket lifecycle look like?](https://news.ycombinator.com/item?id=42731128) · Search: [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=users+message+directly+instead+of+ticket&restrict_sr=1) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=interruptions+context+switching&restrict_sr=1)

---

## 12. Working with developers and managers

### Speak in outcomes, risks and dates

Developers and managers don't need to know which iptables chain you changed. They need the outcome, the risk, and when. Compare "I fixed the DOCKER-USER rules" with "the webhook works again; it now only accepts the partner's network; nothing else changed". The second one builds trust.

### Say no with options

| Request | A bare "no" | A useful answer |
|---|---|---|
| "Give me root on prod" | "No, policy." | "Log access now through prod-readonly; the migration runs as a CI job after approval." |
| "Open 8080 to the world" | "Not allowed." | "I'll put it behind Traefik at hooks.example.com today, with an allowlist for the partner." |
| "Deploy it by hand now" | "Use the pipeline." | "The pipeline is red at test:unit; I'm fixing it, and it ships in about 30 minutes." |
| "Just disable TLS checks" | "That's insecure." | "I'll add our CA to the image; same effort, and it stays secure." |

### 12.1 Dev blames infra, infra blames code

> **Seen as:** "the server is slow" against "the code is slow", bouncing around a thread for two days · **Where:** any team without shared dashboards · **Level:** [L2 · Mid-level] · **How common:** a constant r/devops theme; the usual way out is to split latency by layer and check host saturation with the USE method

**Why it happens:** each side looks at its own graphs, nobody sees the whole request path, and there are no request IDs to follow one slow request from edge to database.

**Diagnose:**

```bash
# Traefik sees the whole request; the app sees only its own part (PromQL in Grafana)
#   edge p95: histogram_quantile(0.95, sum by (le) (rate(traefik_service_request_duration_seconds_bucket{service=~"shop-web.*"}[5m])))
#   app p95:  histogram_quantile(0.95, sum by (le) (rate(http_server_request_duration_seconds_bucket{job="shop-web"}[5m])))
# Host saturation in the same window
ssh dokploy-1 'vmstat 1 3 | sed -n "2p;5p"'      # the column header and the last sample
```

```text
edge p95: 2.31 s
app p95:  2.24 s
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 1  0      0 3120400 91200 6210000    0    0    12    40  910 1700 12  4 83  1  0
```

**What the output tells you:** almost all of the 2.3 seconds is spent inside the app, and the host is 83% idle with no iowait. It is not the infrastructure; the next place to look is the app's database queries.

**Fix:** share the evidence and offer the next step together.

```text
"Edge p95 is 2.31 s and app p95 is 2.24 s, while the host is 83% idle with no iowait,
so the time is spent inside the app. Shall we look at the slow-query log for /api/orders
together at 14:00? I'll bring the Postgres stats."
```

**Why this fix works:** numbers from both layers end the argument, and offering help keeps the relationship intact for the next incident, which may be yours. Don't aim to win; aim to fix.

**Prevent it:** one shared dashboard per service with edge, app and database panels side by side, request IDs in every log line, and tracing for the critical paths.

**Next step:** [Slow system](23-playbook-slow-system.md) · [Observability](49-observability-stack-problems.md) · [Career ladder](40-career-ladder.md) §11 Soft skills · KodeKloud: *Fundamentals of SRE* — Observability and Monitoring

**Community threads:** [Brendan Gregg: the USE method](https://www.brendangregg.com/usemethod.html) · Search: [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=developers+blame+infrastructure&restrict_sr=1) · [Stack Overflow](https://stackoverflow.com/search?q=how+to+tell+if+latency+is+application+or+server)

### 12.2 Everything is urgent

> **Seen as:** three managers each say their request is the top priority this week · **Where:** small teams serving several departments · **Level:** [L2 · Mid-level] · **How common:** a perennial r/sysadmin topic; DORA's research on empowered teams stresses clear priorities and fast feedback over juggling

**Why it happens:** there is no shared priority list, each requester only sees their own request, and the engineer chooses silently and disappoints two people.

**Diagnose:** put the requests side by side.

```text
Request                      Asked by       Real deadline           Impact if late          Effort
Harbor upgrade (CVE)         security       KEV-listed, exposed     high: exploit risk      1 day
New staging env for team B   product        demo on 15 Oct          medium: demo moves      2 days
Grafana dashboards revamp    support lead   none given              low                     3 days
```

**What the output tells you:** one request has a risk deadline, one has a date and one has none, and you have about four days this week. Written down, the order is obvious.

**Fix:** send the table to your manager with a proposal, and let them decide.

```text
"I can do the Harbor upgrade and team B's staging this week. The dashboards start on the 20th
unless you want to swap them with staging. OK?"
```

**Why this fix works:** priority across departments is a manager's decision; making the trade-off visible is your job. Don't promise all three and deliver all three late.

**Prevent it:** one visible board, priorities agreed weekly with your lead, and a limit on work in progress.

**Next step:** [Career ladder](40-career-ladder.md) §11 Soft skills · [Senior architecture](39-learn-senior-architecture.md) · [DORA: empowering software delivery teams](https://dora.dev/devops-capabilities/cultural/how-to-empower-software-delivery-teams/)

**Community threads:** [DORA capabilities](https://dora.dev/capabilities/) · Search: [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=everything+is+top+priority+manager&restrict_sr=1) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=competing+priorities+manager&restrict_sr=1)

### 12.3 Asked to do something unsafe to make it work

> **Seen as:** "just chmod 777 it", "set verify=False", "run the container as root", "turn the firewall off for a bit" · **Where:** any deadline · **Level:** [L1 · Junior] · **How common:** some of the most upvoted wrong answers on Stack Overflow are exactly these, and they persist because they make the error disappear at once

**Why it happens:** there is pressure and an error message, and the unsafe change removes the message without anyone understanding the cause.

**Diagnose:** find the real error behind "permission denied".

```bash
ps -o user= -p "$(pgrep -f gunicorn | head -1)"     # who runs the app?
namei -l /srv/shop/uploads/2026                       # who owns each part of the path?
```

```text
www-data
f: /srv/shop/uploads/2026
drwxr-xr-x root   root   /
drwxr-xr-x root   root   srv
drwxr-xr-x deploy deploy shop
drwxr-xr-x deploy deploy uploads
drwxr-xr-x deploy deploy 2026
```

**What the output tells you:** the app runs as www-data, but the upload directories belong to deploy with mode 755, so only deploy can write. The fix is group write for www-data, not write for everyone.

**Fix:**

```bash
sudo chgrp -R www-data /srv/shop/uploads && sudo chmod -R g+rwX /srv/shop/uploads
# The same effort, done safely, for the other classics:
#   TLS verification off  -> install the private CA (entry 6.3)
#   firewall off          -> one rule for one source and port (entry 4.1)
#   container as root     -> fix the volume's ownership, keep the image's user
```

**Why this fix works:** the safe version takes the same minute and keeps the protection. Don't do the unsafe version "temporarily": temporary changes have a way of becoming permanent.

**Prevent it:** templates and base images with safe defaults, review checks that flag 777, `-k` and `verify=False`, and explaining the "why" once to the team.

**Next step:** [Users, permissions and security](10-users-permissions-security.md) · [Security & DevSecOps](37-learn-security-devsecops.md) §2 Linux hardening · KodeKloud: *Learning Linux Basics Course & Labs* — Security and File Permissions · [Ubuntu Server docs](https://ubuntu.com/server/docs)

**Community threads:** [Ubuntu Server docs](https://ubuntu.com/server/docs) · Search: [Stack Overflow](https://stackoverflow.com/search?q=chmod+777+alternative+web+server+permissions) · [Stack Overflow](https://stackoverflow.com/search?q=verify%3DFalse+self+signed+certificate+alternative) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=chmod+777+developer&restrict_sr=1)

---

## 13. Documentation and runbooks

### What to write down, and where

| Document | Answers | Written when |
|---|---|---|
| Service README | what it is, owner, how it deploys, where its logs, metrics and dashboards are | when the service is created |
| Runbook | what to do when a specific alert fires | with the alert, in the same merge request |
| Decision record (ADR) | why we chose X over Y | when the decision is made |
| Change record | what changed, how it was verified, how to undo it | before the change (section 10) |
| Postmortem | what happened and what we changed | within a week of the incident (entry 9.5) |
| Ticket note | the five-line note | when the ticket closes |

Keep them in one place, in Git or a wiki that links to Git, and link every alert to its runbook.

### A runbook template

```text
Runbook: ShopCheckoutErrors          Owner: team-shop / ops      Last tested: 2026-09-18 (game day)
What it means:   more than 2% of checkout requests return 5xx for 5 minutes.
User impact:     customers cannot pay. Severity: page.
First checks:    1. Grafana "Shop overview": did errors start with a deploy? (Deployments annotation)
                 2. docker service ps shop-web: restarts?  3. Postgres connections near max?
Mitigate:        recent deploy -> roll back (entry 5.2). DB connections -> restart PgBouncer, then escalate.
Escalate:        after 15 min without mitigation -> secondary on-call, then team-shop lead.
Don't:           restart Postgres during checkout traffic; scale web replicas (adds connections).
```

### Docs that stay alive

Write docs as part of "done", review them in merge requests, test runbooks on game days, put a "last tested" date at the top, and follow one habit: every time you use a runbook, fix one thing in it.

### 13.1 The runbook is missing or wrong at 3 AM

> **Seen as:** the runbook says `systemctl restart shop`, but the shop moved to Dokploy a year ago · **Where:** wikis that nobody tests · **Level:** [L2 · Mid-level] · **How common:** the SRE book lists preparing procedures beforehand among its core incident practices, and stale documentation is a staple r/sysadmin complaint

**Why it happens:** runbooks are written once and never tested, nobody owns them, and architecture changes don't touch the docs.

**Diagnose:**

```bash
# How old is the runbook, and how many alerts have one at all?
git -C runbooks log -1 --format='%ad %h' --date=short -- shop-down.md
grep -h 'runbook_url:' monitoring/prometheus/rules/*.yml | wc -l
grep -h -- '- alert:' monitoring/prometheus/rules/*.yml | wc -l
```

```text
2025-06-14 3c1e9a0
14
37
```

**What the output tells you:** the shop runbook was last touched 16 months ago, before the move to Dokploy, and only 14 of 37 alerts link to a runbook at all.

**Fix:** tonight, follow what works and correct the runbook while it is fresh. This week, write the missing ones for paging alerts first, using the template above, and make CI refuse a paging alert without a runbook link.

**Why this fix works:** fixing the runbook right after using it costs ten minutes and captures knowledge you will have forgotten by Monday. A CI check stops new gaps. Don't wait for a "documentation sprint" that never comes.

**Prevent it:** an owner and a "last tested" date on every runbook, runbooks run on game days, and a CI rule that every `severity: page` alert has a `runbook_url`.

**Next step:** [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) §7 SRE practice (runbook example "Alert: ShopWebDown") · [Practice Arena](54-practice-arena.md) §10 · KodeKloud: *Fundamentals of SRE* — Incident Management (Preparing for Incidents)

**Community threads:** [Google SRE book: Managing Incidents](https://sre.google/sre-book/managing-incidents/) · Search: [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=outdated+documentation+runbook&restrict_sr=1) · [Reddit r/sre](https://www.reddit.com/r/sre/search/?q=runbook+template&restrict_sr=1)

### 13.2 Only one person knows how it works

> **Seen as:** "ask Ravi, he built it", and Ravi is on holiday during the outage · **Where:** small teams where one person built each system · **Level:** [L3 · Senior] · **How common:** the "bus factor" is an r/sysadmin classic, and the SRE book warns that engineers who rarely handle a system lose the confidence to fix it

**Why it happens:** the builder never had time to document, hero work gets praised, and nobody else ever touches the system, so nobody else learns it.

**Diagnose:**

```text
System             Can fix it alone       Docs        Last time someone else did it
Harbor + CA        Ravi                   none        never
Wazuh manager      Ravi, Priya            partial     March
Dokploy cluster    Priya, Sam, Lee        runbooks    last week
```

**What the output tells you:** Harbor with the private CA has a bus factor of one and no docs. It is the team's biggest operational risk this quarter.

**Fix:** a knowledge-transfer plan for Harbor: the next Harbor task is done by Sam with Ravi navigating (Ravi doesn't type), a 20-minute recorded walkthrough, a README and two runbooks written by Sam and reviewed by Ravi, and the following change done by Lee with Ravi only watching.

**Why this fix works:** the person who knows is the worst person to type during a handover, because the knowledge stays in their hands. Learning by doing, with the expert reviewing, moves it into other heads and into the docs.

**Prevent it:** a bus factor of at least two for every production system as a quarterly goal, docs as part of done, and rotating who does routine changes.

**Next step:** [Career ladder](40-career-ladder.md) §6 Lead, Staff and SRE · [Senior architecture](39-learn-senior-architecture.md) · section 17 of this module

**Community threads:** [Google SRE book: Being On-Call](https://sre.google/sre-book/being-on-call/) (operational underload) · Search: [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=bus+factor+documentation&restrict_sr=1) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=knowledge+silo+one+person&restrict_sr=1)

---

## 14. How engineers learn on the job

Courses teach the map; tickets teach the territory. The engineers who grow fastest are not the ones with the most certificates, but the ones who turn every ticket into a small lesson and revisit it.

### The learning loop

Each week, run the same loop on two or three tickets: **ticket** (something real happened) → **note** (five lines: symptom, evidence, cause, fix, prevention) → **lab** (reproduce it on your homelab and break it on purpose) → **flashcard** (the one fact you had to look up) → **share** (a two-minute explanation at standup or in the team channel). Explaining it is what makes it stick.

### The ticket journal

Keep one file per month in Git. A note looks like this:

```text
2026-10-04 OPS-1477 "site is slow"
Symptom:    p95 4.1 s on shop.example.com from 10:02
Evidence:   vmstat b=14, wa=60%; iostat sda 99.8% util; pidstat: restic reading 95 MB/s
Cause:      nightly backup rescheduled into business hours by a cron edit
Fix:        ionice -c3 on the backup; cron back to 02:00; alert on backup duration
Learned:    blocked tasks count towards the load average (flashcard)
```

### Read issues, release notes and postmortems

- **GitHub issues:** when a tool misbehaves, open its issues sorted by reactions or comments before you search the web. Read the maintainers' replies first; the workaround is often in the tenth comment.
- **Release notes:** read them before every upgrade of Docker, Traefik, Dokploy, GitLab Runner or Kubernetes. Entry 10.4 is what happens when nobody does.
- **Postmortems:** one a week from [Dan Luu's collection](https://github.com/danluu/post-mortems) or [Kubernetes Failure Stories](https://k8s.af/). Before reading the root cause, guess which layer failed.

### A homelab that mirrors work

Two VMs (dokploy-1 and dokploy-2), Dokploy with Traefik, a GitLab project with a runner, Prometheus and Grafana, and snapshots before every experiment. It does not need to be big; it needs to look like work, so that every ticket can be replayed. [On-prem vs cloud paths](55-paths-onprem-vs-cloud.md) has homelab plans by stage, and an AWS free-tier account covers the cloud side.

### Flashcards for the facts you keep looking up

Use spaced repetition (Anki or any similar app) for small facts you look up more than twice: port numbers, `ss` and `journalctl` flags, PromQL functions, Traefik label names, where the private CA goes on each client. Make cards from your notes, not from course slides, and keep each card to one fact.

### KodeKloud labs and the Practice Arena as reps

Treat labs like a gym: short and regular beats long and rare. A 30-minute morning rep on [KodeKloud Engineer](https://engineer.kodekloud.com/) or [100 Days of DevOps](https://kodekloud.com/100-days-of-devops), one longer lab a week from the course for your current level, and a timed broken-server exercise from the [Practice Arena](54-practice-arena.md) every fortnight. The [Ubuntu playground](https://kodekloud.com/playgrounds/playground-ubuntu) is enough to replay most Linux tickets when your homelab is busy.

### Learning with AI assistants

Assistants are good at explaining an error, a flag or a config file, and at drafting a runbook. Verify what they say against the official docs, never paste secrets or customer data into them, and never run a command you don't understand on a production host. Ask "why" until you could explain the answer at standup.

### 14.1 Trying to learn every tool at once

> **Seen as:** a roadmap with 80 logos, five half-finished courses, and the feeling that everyone else knows more · **Where:** freshers and juniors, especially while job-hunting · **Level:** [L0 · Fresher] · **How common:** a dev.to post titled "I stopped trying to learn every DevOps tool and started building a platform instead" drew over 150 reactions on the DevOps tag in the past year, and the Ask HN thread "I feel so shallow and dumb when I see what other smart people are doing" has over 500 points and 300 comments

**Why it happens:** roadmaps show breadth, while the job needs depth in the handful of tools your tickets actually touch. Comparing yourself with everyone's highlights makes it worse.

**Diagnose:**

```bash
# Tag your last 30 closed tickets with the tools they needed (column 4, ";"-separated), then count
cut -d, -f4 my-tickets.csv | tr ';' '\n' | sort | uniq -c | sort -rn | head -6
```

```text
     19 linux
     14 docker
     11 traefik
      9 gitlab-ci
      6 dns
      2 kubernetes
```

**What the output tells you:** your job is Linux, Docker, Traefik, GitLab CI and DNS. Kubernetes appeared twice: keep it on your CKA plan, but not at the expense of the top five.

**Fix:** pick the top three, follow the 90-day plan in section 17, build one small platform on your homelab that uses them together, and take one course at a time to the end.

**Why this fix works:** depth in the tools you use daily pays off every week, and a working platform teaches the integration that separate courses skip. Don't drop long-term goals; schedule them.

**Prevent it:** recount every quarter, and keep a "later" list for shiny tools so they stop interrupting.

**Next step:** section 17 · [Roadmap](34-roadmap.md) · [Career ladder](40-career-ladder.md) §9 Learning with KodeKloud · [Practice Arena](54-practice-arena.md) §14 Practice plans by career stage

**Community threads:** [dev.to: I stopped trying to learn every DevOps tool](https://dev.to/maame-codes/i-stopped-trying-to-learn-every-devops-tool-and-started-building-a-platform-instead-33i6) · [Ask HN: I feel so shallow and dumb when I see what other smart people are doing](https://news.ycombinator.com/item?id=29281468) · [dev.to: DevOps From Scratch, a student's diary](https://dev.to/maame-codes/devops-from-scratch-a-students-diary-entry-00-5b71) · Search: [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=overwhelmed+too+many+tools&restrict_sr=1)

### 14.2 Stuck for hours without asking for help

> **Seen as:** four hours on one error, then a senior solves it in five minutes with one question · **Where:** every team with juniors · **Level:** [L0 · Fresher] · **How common:** one of the most common regrets in junior "what I wish I knew" threads on r/devops and r/sysadmin

**Why it happens:** fear of looking stupid, not knowing what a good question looks like, and no team habit of asking early.

**Diagnose:** check yourself against a time box.

```text
Started:        10:05
Error:          CI push to harbor.example.com fails: x509: certificate signed by unknown authority
Tried:          re-ran the job (same); docker login on runner-1 from a shell works
Suspect:        the job's docker:dind container doesn't trust our CA
Time spent:     35 min -> past the 30-minute box: ask now
```

**What the output tells you:** you have evidence and a hypothesis, which is exactly what makes a good question. You are past the time box.

**Fix:** ask with what you know, what you tried and what you think.

```text
"I'm stuck on OPS-1533: pushes to Harbor fail in CI with x509 unknown authority.
Tried: re-running (same); docker login on runner-1 from a shell works.
I think the dind container lacks our CA. Can you sanity-check before I change the runner config?"
```

**Why this fix works:** a question that shows your work is quick to answer and teaches you more than the answer alone. Thirty minutes alone, then ask, is a common rule of thumb; adjust it with your lead. Don't ask "it doesn't work, help", and don't wait until the end of the day.

**Prevent it:** agree a time box with your team, pair at least once a week, and keep a list of questions for your one-to-one.

**Next step:** entry 6.3 · [Career ladder](40-career-ladder.md) §11 Soft skills · KodeKloud [community forum](https://kodekloud.com/community/) for lab errors

**Community threads:** [KodeKloud community forum](https://kodekloud.com/community/) · Search: [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=junior+afraid+to+ask+questions&restrict_sr=1) · [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=when+to+ask+for+help+junior&restrict_sr=1)

---

## 15. What juniors struggle with and what seniors do differently

| Situation | What juniors often do | What seniors do |
|---|---|---|
| A vague ticket | start working on the literal request | ask for the outcome, owner, deadline and risk (section 2) |
| Something is broken | restart it and hope | look at evidence first, then mitigate with the smallest safe step |
| An error message | search the last line | read the first error, and the logs around it |
| A production change | type commands live | write the plan, the verify step and the rollback first |
| Being stuck | grind alone for hours | time-box, then ask with evidence |
| An incident | jump in and change things | ask who leads, then do the assigned part |
| A mistake | hide it or fix it quietly | say it at once, then fix the guard rail |
| Repeat requests | handle each one by hand | measure, document, automate, then remove the need |
| Learning | collect courses and tools | learn from tickets and build one platform deeply |
| Communication | "done" | outcome, how it was verified, how to undo it |

Habits worth copying from good seniors:

- **They narrate.** In incidents and pairing they say what they check and why, which teaches everyone around them.
- **They prefer reversible steps.** Feature flags, rollbacks, `--check`, snapshots; one-way doors get extra review.
- **They read the docs and the source.** When a tool behaves oddly, they open its docs, issues and sometimes its code before guessing.
- **They leave things better.** A runbook fixed, an alert tuned, a note written, every time.
- **They protect their focus.** Interrupt shields, batched requests and calendar blocks are deliberate, not luck.

[Career ladder](40-career-ladder.md) turns these into expectations per stage.

---

## 16. Burnout and sustainable on-call

### Signs to take seriously

Dreading releases, sleeping badly in on-call weeks, cynicism in retros, being snappy with developers, and losing interest in learning are early signs. Burnout is mostly about the work environment, not personal weakness. DORA cites the burnout researcher Christina Maslach, who names six drivers: too much workload, too little control, too little reward, a poor community, unfairness, and clashing values. DORA's own data adds deployment pain and unplanned work, and finds that continuous delivery practices predict lower burnout.

### Designing a rotation for a small on-prem team

You will rarely have the eight people the SRE book suggests, so adapt:

- **Page only for user impact.** Everything else becomes a ticket for working hours (entries 9.1 and 9.2).
- **Cover hours honestly.** If a service doesn't need 24/7, say so in writing and page only in business hours.
- **Share the pager with developers** for the services they build, with ops as the secondary.
- **No project deadlines in on-call weeks**, and a "fix-it" person who works on the causes of last week's pages.
- **Compensate:** time off in lieu or pay after night pages, as the SRE book and many Ask HN replies describe.
- **Track it:** out-of-hours pages, weekend work and unplanned-work share as team health metrics, reviewed monthly.

### Personal habits that help

Hand the pager over properly and then switch off. Keep a fixed time to stop work. Keep learning tied to work (section 14) rather than piling on evenings of courses. Talk to your lead early, with numbers, not when you are already exhausted.

### 16.1 Burning out on deployment pain and unplanned work

> **Seen as:** dread before every release, weekends spent on deploys, cynicism in retros · **Where:** teams with manual releases and noisy pagers · **Level:** [L2 · Mid-level] · **How common:** DORA's well-being research links burnout to deployment pain and unplanned work and reports that low performers spend 27% of their time on rework against 21% for high performers; Ask HN threads on on-call benefits and on "I can't do on-call rotations" show how widespread the strain is

**Why it happens:** releases are rare, large and manual, so they are scary and happen when nobody is around; the pager is noisy; and the fixes for both never get prioritised because everyone is too busy firefighting.

**Diagnose:** measure the environment, not the person.

```bash
# Pages outside 08:00-19:00 and weekend deploys this quarter (exports from the pager and the pipeline)
awk -F, 'NR>1 && ($3 < 8 || $3 >= 19) {n++} END {print n " out-of-hours pages"}' pages-q3.csv
awk -F, 'NR>1 && ($2 == "Sat" || $2 == "Sun") {n++} END {print n " weekend deploys"}' deploys-q3.csv
```

```text
46 out-of-hours pages
11 weekend deploys
```

**What the output tells you:** about three and a half disturbed evenings or nights a week across the quarter, and deploys so risky that the team does them at weekends. Both are problems of the system, and both have known fixes.

**Fix:** take the numbers to your manager with a plan: small automated deploys in working hours with a tested rollback (entry 5.2), the alert clean-up from entry 9.2, time off after night pages, and no project deadlines in on-call weeks. Ask for the time to do it explicitly.

**Why this fix works:** DORA's advice is to change the work environment rather than "fix the person", and continuous delivery reduces both deployment pain and unplanned work. Numbers turn a complaint into a project. Don't treat it only as a matter of personal resilience.

**Prevent it:** out-of-hours pages, weekend work and unplanned-work share on the team's monthly dashboard, with a target for each.

**Next step:** section 9 · [Deployment patterns](35-deployment-patterns.md) · [Career ladder](40-career-ladder.md) §11 Soft skills · KodeKloud: *Fundamentals of SRE* — Managing Complexity, Risk and Toil

**Community threads:** [DORA: well-being](https://dora.dev/capabilities/well-being/) · [Ask HN: What on-call benefits do you get in your company?](https://news.ycombinator.com/item?id=30600755) · [Ask HN: I can't do on-call rotations](https://news.ycombinator.com/item?id=28346085) · Search: [Reddit r/sre](https://www.reddit.com/r/sre/search/?q=on-call+burnout&restrict_sr=1) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=burnout&restrict_sr=1)

### 16.2 Your first big mistake in production

> **Seen as:** the stomach-drop moment: "I think I just deleted the wrong volume" · **Where:** sooner or later, every career · **Level:** [L0 · Fresher] · **How common:** almost everyone has one; GitLab published its 2017 postmortem in full, and Dan Luu's collection is full of routine mistakes at large, experienced companies

**Why it happens:** a missing guard rail, not missing talent. The system let one tired person do something irreversible without a second check.

**Diagnose:** the first five minutes.

```text
1. Stop. Hands off the keyboard. Don't try to undo it quietly.
2. Write down: time, host, the exact command (from history), what you expected to happen.
3. Tell your lead or the on-call person now, in the team channel.
4. Help with the recovery as the person with the most context, not as the one in charge.
```

**What the output tells you:** these four steps decide how bad the day gets. Fast, honest disclosure is what lets the team start recovery while backups and logs are still fresh.

**Fix:** the message to send.

```text
"21:47 UTC: I ran TRUNCATE orders_archive on db-prod-1 thinking I was on staging.
Impact: archive reports are empty; live orders are not affected. Last dump: 02:00 today.
I've stopped. Can someone take IC? I'll write the timeline."
```

**Why this fix works:** it gives the facts, the impact and what you don't know, and hands coordination to someone calmer. Afterwards, write the blameless postmortem yourself and propose the guard rail (entry 10.2); handled well, your worst day becomes evidence of maturity. Don't hide it, and don't let anyone make "be more careful" the only action item.

**Prevent it:** the guard rails in section 10, a team culture where mistakes are reported quickly, and seniors who tell their own stories to new juniors.

**Next step:** entries 10.2 and 9.5 · [Career ladder](40-career-ladder.md) §10 Building proof · KodeKloud: *Fundamentals of SRE* — [Blameless Postmortem Culture](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page)

**Community threads:** [GitLab: postmortem of the database outage of 31 January 2017](https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/) · [Dan Luu's post-mortems](https://github.com/danluu/post-mortems) · Search: [Reddit r/sysadmin](https://www.reddit.com/r/sysadmin/search/?q=deleted+production+database+first+job&restrict_sr=1) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=broke+production+junior&restrict_sr=1)

---

## 17. A 90-day "learn from your own tickets" plan

This plan works at any stage; a fresher shadows more, and a mid-level engineer automates more. It needs about 30 minutes a day plus one longer session a week.

### Before you start

Create a ticket journal in Git (one file per month), snapshot your two homelab VMs, install a flashcard app, and block 30 minutes in your calendar every morning. Tell your lead what you are doing; most leads will feed you good tickets.

### Days 1–30: observe and record

- Write a five-line note for every ticket you touch or watch, even when someone else does the work.
- Tag each ticket with a type from section 2 and the tools it needed.
- Replay one ticket a week on the homelab.
- Morning reps: KodeKloud Engineer or 100 Days of DevOps tasks on the tools your tickets used.
- End of month: count types and tools (entry 14.1) and pick your top three.

### Days 31–60: own the common tickets

- Ask to own the top two ticket types end to end, with a reviewer.
- Write or fix the runbook for each (section 13), and test it on the homelab.
- Shadow one on-call shift, or one incident review, and write your own timeline of it.
- Read one postmortem a week and one set of release notes before any upgrade you see scheduled.
- End of month: you close those two types alone, and someone else has used your runbook.

### Days 61–90: remove one source of tickets

- Pick the type with the most hours (entry 11.1) and climb the automation ladder by at least one rung.
- Measure before and after: tickets and hours per month.
- Present it to the team in ten minutes: problem, numbers, what you built, what is next.
- Run one game day scenario from your notes with a colleague (Wheel of Misfortune style).
- End of month: update your career evidence file (see [Career ladder](40-career-ladder.md) §10).

### The weekly rhythm

| Day | 30 minutes |
|---|---|
| Monday | review last week's notes; pick two tickets to replay |
| Tuesday | morning rep (KodeKloud Engineer or 100 Days of DevOps) |
| Wednesday | replay a ticket on the homelab, break it differently |
| Thursday | read one postmortem or one set of release notes |
| Friday | flashcards from the week's notes; share one lesson in the team channel |

### What to show at the end

Ninety notes or so, two runbooks other people use, one automation with before-and-after numbers, a game day you ran, and a list of the facts you now know without looking them up. That is stronger evidence for your next step than any certificate alone.

---

## Self-check

Ten timed exercises, using the lab VMs and a colleague who plays the requester. Write the reply, change record or postmortem each one asks for, then compare with the entry.

| # | Stage | Exercise | Time | Entry |
|---|---|---|---|---|
| 1 | Fresher | A colleague DMs "give me sudo on dokploy-1": ask the four questions and reply with the smallest role | 10 min | 3.1 |
| 2 | Fresher | Publish a container on -p 8080 behind UFW, prove it is reachable, then move it behind Traefik | 20 min | 4.1 |
| 3 | Junior | Fill the lab disk with a chatty container log at "3 AM"; free space safely and add rotation | 15 min | 7.1 |
| 4 | Junior | Point a hostname at a wrong IP before adding the domain; get a valid certificate | 20 min | 4.2, 6.1 |
| 5 | Junior | Remove the private CA from a runner and fix the x509 error without disabling verification | 15 min | 6.3 |
| 6 | Mid-level | Deploy a release missing an environment variable; roll back, then fix forward through CI | 20 min | 5.2, 5.4 |
| 7 | Mid-level | Export a month of fake pages and propose which alerts to delete, demote or fix | 30 min | 9.2 |
| 8 | Mid-level | Hand-edit a Traefik file, then find and resolve the drift with --check --diff | 20 min | 10.3 |
| 9 | Senior | Run a 30-minute incident as IC with three colleagues, including two status updates | 45 min | 9.3 |
| 10 | Senior/Lead | From a ticket export, find the top toil type and present an automation plan with numbers | 45 min | 11.1 |

Quick questions to answer from memory:

1. What are the four questions to ask before working any ticket?
2. Why does closing UFW not protect a port published with `docker run -p`?
3. What are the SRE book's three criteria for declaring an incident?
4. What makes work toil rather than engineering, and what is the cap on operational work?
5. In what order do you handle a leaked secret: clean history, rotate, or check for misuse?

---

## Where to go next

- [Career ladder](40-career-ladder.md): what each stage is expected to do, how to build proof, and soft skills in depth.
- [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md): Ansible, Terraform, SLOs, the full postmortem template and the L4 game day.
- [Practice Arena](54-practice-arena.md): broken-server sites, incident games and practice plans by stage.
- [On-prem vs cloud paths](55-paths-onprem-vs-cloud.md): how the day-to-day differs between data centre and cloud careers.
- Playbooks for the tickets in this module: [Who owns this port?](22-playbook-ports-inventory.md) · [Docker & K8s incidents](26-playbook-containers-k8s.md) · [Site down](25-playbook-site-down.md) · [Slow system](23-playbook-slow-system.md).
- Tool modules: [Traefik](43-traefik-and-reverse-proxies.md) · [Dokploy](45-dokploy-and-self-hosted-paas.md) · [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) · [Wazuh & security tools](48-wazuh-and-security-tools.md) · [Observability](49-observability-stack-problems.md).
- Problem libraries: [Docker, Swarm & registry](44-problems-docker-swarm-registry.md) · [Kubernetes](46-problems-kubernetes.md) · [Cloud, IaC & Proxmox](50-problems-cloud-iac-proxmox.md) · [Databases, storage & backups](51-problems-databases-storage-backup.md).
- Learn tracks and references: [Learn Docker](30-learn-docker.md) · [Learn Kubernetes](31-learn-kubernetes.md) · [Docker containers](14-docker-containers.md) · [Kubernetes](15-kubernetes.md).
- Reading: the Google SRE book chapters on [toil](https://sre.google/sre-book/eliminating-toil/), [on-call](https://sre.google/sre-book/being-on-call/), [incidents](https://sre.google/sre-book/managing-incidents/) and [postmortems](https://sre.google/sre-book/postmortem-culture/) · [DORA capabilities](https://dora.dev/capabilities/) · [Dan Luu's post-mortems](https://github.com/danluu/post-mortems).
