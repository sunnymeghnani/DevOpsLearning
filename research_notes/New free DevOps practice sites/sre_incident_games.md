# Free DevOps/SRE strategy, incident-response and simulation games not yet in the handbook (checked 7 Nov 2026)

How the checks were done: each site was opened on 7 Nov 2026 with curl or the built-in browser, which runs JavaScript. GitHub stars and last-push dates come from the GitHub REST API on the same day. Where only a search snippet or a third-party write-up was seen, the entry says so. Nothing was signed up for, submitted or downloaded.

## Q1. Which new free games and simulators exist in 2026?

### Takeaway
There are about 20 strong new free resources. The best fits for the handbook are these:
- **Server Survival**: a cloud-architecture tower-defence game, about 6.5k stars and maintained.
- **K8s Games**: a 3D Kubernetes simulator with a Chaos mode, about 1.5k stars.
- **SDPD**: a system-design detective game with 33 failure cases.
- **SystemLore** and **System Design Sim**: browser scaling games that need no sign-up.
- **TWiG Online** and **Featureban**: free flow and WIP simulations.
- **Tabletop and drill kits**: Deployments and Disasters (an SRE tabletop RPG), Twilio's GameDay template, the Equal Experts Chaos Day Playbook and PagerDuty's open incident-response training.
- **Incident libraries**: The VOID, which is alive with 10,000+ reports, plus Failure Modes and the Postmortem Index.

Several on-call browser games appeared in Sept–Nov 2026: ON-CALL, Pit Wall On-Call, non-call and The Incident Challenge. They are playable and free, but new and unproven.

### Cited Findings

#### A. On-call / incident-response simulators (browser)
- **ON-CALL: the platform incident simulator.** URL: https://oncall-simulator.vercel.app/
  - You play the platform engineer paged at 02:11 and work six incidents by choosing what to inspect, mitigate and fix. At the end you get a postmortem, a grade and a link your team can use to replay the same shift. The page says "Free, no signup", and the landing page counts "23 incidents · 138 decisions" in total — [site](https://oncall-simulator.vercel.app/)
  - How it scores: each decision has 3–4 options, "One is the right move. One is what you would do at 03:00 with no sleep." Error budget drains on bad calls, and "blast radius" tracks the largest group of customers a single choice touched. If you only patch the symptom, the incident comes back within the shift at one severity higher — [site](https://oncall-simulator.vercel.app/)
  - Repository: github.com/kanishk-sachdeva/oncall-simulator, created 18 Oct 2026 with 0 stars and no licence. The description reads "six incidents, thirteen decisions, one night" — [GitHub](https://github.com/kanishk-sachdeva/oncall-simulator)
- **Pit Wall On-Call.** URL: https://pitwall.rafifdzaky.com/
  - The page describes "A browser game about being on call": you acknowledge the page, investigate alerts, metrics and logs against a real-time clock, then read a postmortem that shows where your error budget went. Its premise is that "the loudest service is not always the cause". It needs a screen at least 1024 px wide — [site](https://pitwall.rafifdzaky.com/)
  - It runs a daily incident: the page showed "Daily #40 2026-11-07 · first attempt per player" — [site, rendered in browser](https://pitwall.rafifdzaky.com/)
  - Repository: AGPL-3.0, created 27 Sep 2026, last push 4 Nov 2026, 0 stars — [GitHub](https://github.com/rafifdzaky27/pit-wall-on-call)
- **non-call (by serum.sh).** URL: https://serum.sh/non-call/
  - An on-call night told in a terminal style. The page says "There is no win condition. There is a 07:00." It also says open alerts cost the company money, "A second alert does not wait for the first", real-life interruptions run on countdowns, and "Not deciding is a decision" — [site, rendered in browser](https://serum.sh/non-call/)
  - Launched as "Show HN: Non-call, an on-call simulator mini-game" on 21 Oct 2026, with 2 points — [HN Algolia API](https://hn.algolia.com/api/v1/search?query=on-call%20game&tags=show_hn)
- **The Incident Challenge.** URL: https://theincidentchallenge.com/
  - A live debugging contest held every other Monday, with a 24-hour window to enter. Correct fixes are ranked by solve time. The site reports "400+ engineers, 36 countries, 20% success rate". The next round showed as Monday 9 Nov 2026 at 13:00 UTC — [site, rendered in browser](https://theincidentchallenge.com/)
  - In each round you compare a staging environment with production and get the brief, system logs, request, service and config. "AI and your usual tools are welcome." A "Famous incidents" page and a "For teams" offering also exist — [site](https://theincidentchallenge.com/)
  - **Account needed:** even the past-challenge demo asks you to "Create an account or sign in", using Google or LinkedIn only — [demo page](https://challenge.theincidentchallenge.com/#/demo)
  - No price is shown anywhere. It is described as "a browser game for practicing production debugging under pressure" with a Product Hunt launch — [ChatGate write-up, 25 May 2026](https://chatgate.ai/post/the-incident-challenge)

#### B. System-design / scaling games
- **Server Survival.** URL: https://pshenok.github.io/server-survival/
  - A 3D tower-defence game. You place Firewall, WAF, API Gateway, load balancer, message queue, compute, serverless, container cluster, GeoDNS, relational DB, NoSQL, cache, read replica, search, object storage, pub/sub, dead-letter queue, monitoring and more. Traffic rises and DDoS waves arrive while you manage budget, upkeep and reputation — [game page](https://pshenok.github.io/server-survival/)
  - Modes: Survival (v3.0, $500 starting budget), a 25-level Campaign, a 10-step Tutorial and a Sandbox. There are 38 trophies. No account; the game saves in the browser or to a file you download — [game page](https://pshenok.github.io/server-survival/)
  - Repository: MIT licence, 6,479 stars, created 21 Nov 2025, last push 4 Nov 2026. The description reads "Tower defense game that teaches cloud architecture. Build infrastructure, survive traffic, learn scaling" — [GitHub](https://github.com/pshenok/server-survival)
  - Launched on Show HN on 23 Nov 2025 — [HN Algolia](https://hn.algolia.com/api/v1/search?query=tower%20defense%20cloud)
  - Copies exist under other names, for example "Server Survival TD" on freetoolonline.com. Use the pshenok.github.io original — [search results](https://github.com/iptoux/server-survival)
- **K8s Games.** URL: https://k8sgames.com/
  - A 3D Kubernetes cluster simulator in the browser with these modes:
    - Campaign: 20 levels from pods to production.
    - Chaos Mode: "Survive escalating incidents".
    - Sandbox: scored 0–100 by an "Architecture Advisor".
    - Challenges: 10 timed scenarios: fix outages, deploy apps, race the clock.
    - K8s Draw: a 3D diagram tool that exports YAML.

    It has a kubectl command bar ("Press / for kubectl"). The README says "No install, no signup, no build step" — [site](https://k8sgames.com/), [README](https://github.com/rohitg00/k8sgames)
  - Repository: Apache-2.0, 1,458 stars, created 15 Feb 2026, last push 28 Apr 2026 — [GitHub](https://github.com/rohitg00/k8sgames)
- **SDPD: Systems Design Police Department.** URL: https://sdpd.live/
  - A detective game set in the city of "Distributia". It has 33 failure cases to diagnose and fix, grouped by topic:
    - Replication: Single Point of Failure, Stale Read, Lost Evidence.
    - Consensus: Split Brain, Leader Election, Clock Synchronization, Byzantine Fault Tolerance.
    - Scaling: Overwhelmed Gateway, Thundering Herd, Hot Partition, and more.

    It also has a "Chaos Simulator" (inject failures, then restore stability) and a system-design interview cheat sheet. It is "Free, open source, EN/PT-BR" — [site, rendered in browser](https://sdpd.live/)
  - Repository: olucasandrade/sdpd, MIT, 97 stars, created 20 Feb 2026, last push 13 Jul 2026 — [GitHub](https://github.com/olucasandrade/sdpd)
- **SystemLore.** URL: https://systemlore.com/
  - "Distributed systems simulation game: keep services alive through traffic spikes, outages, queues, caches, shards, and failover drills". The page shows "No signup needed · 5 minute runs" and a leaderboard. The campaign runs "one box to planet scale" and each run ends "with a post-mortem you can actually learn from". There is a Studio canvas (Client → Load Balancer → App → Cache → Database) and a free Academy covering 39 concepts — [site](https://systemlore.com/), [Academy](https://systemlore.com/academy)
- **System Design Sim.** URL: https://systemdesignsim.com/playground
  - You drag load balancers, API servers, caches, queues, databases and CDNs onto a canvas and choose AWS, Azure or GCP. p99 latency, error rate and the monthly bill update live, using that provider's sizes, limits and prices. Challenges include a flash sale and "Tatkal at 10 am" at up to 20,000 req/s. "Free, in your browser, no signup" — [playground](https://systemdesignsim.com/playground), [home](https://systemdesignsim.com/)
  - What stays free: the playground, every challenge, the calculators and the guides; "No account is needed." A paid plan is planned (learning paths, scored feedback, model answers), but "Practice stays free either way." It is built by one engineer, Winson GR, and has existed since June 2026 — [about](https://systemdesignsim.com/about)
- **StackMonkey.** URL: https://stackmonkey.dev/
  - A "Free browser based system design simulator. Draw system architecture, simulate live traffic, queues, and retry storms." It names the component that fails first. Its queueing maths is tested against Little's Law and the Pollaczek–Khinchine formula, and it gives deterministic runs. "Free to use · In-browser canvas · No credit card" — [home](https://stackmonkey.dev/), [about](https://stackmonkey.dev/about)
- **The CTO Game (minor).** URL: https://thectogame.com/
  - "A strategic simulation game where you make critical technical architecture decisions under pressure. Balance scalability, velocity, tech debt, and business outcomes." It was posted as a Show HN on 5 Mar 2026 with 3 points. The page loads with a Tutorial and a Leaderboard, but I did not play it far enough to judge depth or whether it needs an account — [site](https://thectogame.com/), [HN Algolia](https://hn.algolia.com/api/v1/search?query=system%20design%20game)

#### C. Flow / DORA / value-stream simulations
- **TWiG Online (The WiP Game).** URL: https://analytics.actionableagile.com/twig/index.html
  - "TWiG Online takes the flow-based simulation from Leanability and adapts it for virtual play… analyze your results using built-in ActionableAgile charts… it's free to play!" Facilitator and participant PDF guides are linked — [ActionableAgile page](https://actionableagile.com/play-twig/)
  - The game board (day counter, item ages, BLOCKED cards, "View Analytics") loaded in the browser with no login — [game](https://analytics.actionableagile.com/twig/index.html)
  - TWiG is "Klaus Leopold's lightweight simulation for WIP-limited pull systems" — [LEANability](https://leanability.netlify.app/en/twig)
- **Featureban.** URLs: https://www.agendashift.com/resources/featureban (rules, slides) and https://tools.flowfast.io/featureban/ (free online version)
  - "The classic kanban simulation game", created by Mike Burrows in 2014. It is currently at version 3.0 (June 2019) and licensed CC BY-SA 4.0, and customisation is encouraged. Physical play needs A3 paper, sticky notes and a deck of playing cards; slides are on Dropbox — [Agendashift](https://www.agendashift.com/resources/featureban)
  - "our friends at FlowFast have created a free online version of Featureban" — [Agendashift](https://www.agendashift.com/resources/featureban). The FlowFast URL returned HTTP 200, but I did not check its in-page sign-up flow — [FlowFast](https://tools.flowfast.io/featureban/)
- An index of other Kanban/flow games (Okaloa Flowlab, FlowBan, getKanban, KanbanPizza and others) is at [Kirill Klimov's list](https://kirillklimov.com/kanban-games/), dated Oct 2022. I did not check those games one by one.

#### D. Tabletop games, game-day kits and drill material (free to read or download)
- **Deployments and Disasters.** URL: https://antolius.github.io/deployments-and-disasters/
  - "A tabletop RPG for practicing incident management", with sections on How to play, How to host and Game design. The site says "still in development". The rules are licensed CC0 and the site code MIT — [site](https://antolius.github.io/deployments-and-disasters/), [README](https://github.com/Antolius/deployments-and-disasters)
  - Repository: 8 stars, last push 13 Apr 2022, so it is stale — [GitHub](https://github.com/Antolius/deployments-and-disasters)
- **Twilio SRE GameDay template.** URL: https://github.com/twilio/gameday
  - One Markdown template, "Scenario 1 – Get To Know Your System". It covers service context, customer impact, SLOs and SLIs, a preparation checklist (toolbox, before and after the game day), and roles and responsibilities. MIT licence, 139 stars, last push Oct 2020 — [GitHub](https://github.com/twilio/gameday), [template](https://github.com/twilio/gameday/blob/main/get_to_know_your_systems.md)
- **Equal Experts Chaos Day Playbook.** URL: https://playbooks.equalexperts.com/chaos-day-playbook
  - "a distillation of our thinking on how best to run a Chaos Day", with a 5-minute guide, experiment design and preparation, and a PDF download. The page shows "Last updated 2 years ago" — [playbook](https://playbooks.equalexperts.com/chaos-day-playbook)
- **PagerDuty Incident Response documentation and training.** URL: https://response.pagerduty.com/
  - Free, public role guides for Incident Commander, Deputy, Scribe, SME/Resolver, Customer Liaison and Internal Liaison, plus severity levels, call etiquette and a postmortem template — [training overview](https://response.pagerduty.com/training/overview/)
  - "Incident Response Training Course (2018)" is "an open-source version of… our PagerDuty training course for incident response and incident command", with slides. "Feel free to use this as a base for training in your own organization." The current version lives in the paid PagerDuty University — [course](https://response.pagerduty.com/training/courses/incident_response/)
  - The IC guide says the Incident Commander should "Keep the incident moving towards resolution", should not do remediation themselves, and that "anyone can do it… (yes, even an intern!)" — [IC training](https://response.pagerduty.com/training/incident_commander/)
  - Repositories: PagerDuty/incident-response-docs (1,052 stars, last push 30 Oct 2026) and PagerDuty/postmortem-docs, the source of https://postmortems.pagerduty.com (last push 30 Oct 2026) — [GitHub](https://github.com/PagerDuty/incident-response-docs), [GitHub](https://github.com/PagerDuty/postmortem-docs)
- **Security incident-response tabletops that are separate products from Backdoors & Breaches:**
  - *Rolls & Responders* (NCSC New Zealand): "an open-source tabletop exercise toolkit for cyber security incident response teams". The game manual, facilitator manual, quick guides and a resources ZIP are free downloads — [NCSC NZ](https://www.ncsc.govt.nz/protect-your-organisation/rolls-and-responders/)
  - *Oh Noes!* (Expel): a "D&D-style cybersecurity tabletop game" with character sheets and an "Incident Master". Expel says "Run a realistic cyberattack with your team in under 2 hours. No facilitator required". The "Download now" button links straight to a 2026 kit ZIP — [Expel](https://expel.com/oh-noes-cybersecurity-tabletop/)
  - *Defensomania*: an incident-response card game with scenario cards and activity cards that follow IR phases. It has a free online card dealer. MIT licence, 66 stars, last push 6 Nov 2026 — [GitHub](https://github.com/Karneades/Defensomania), [play online](https://karneades.github.io/Defensomania/play/)

#### E. Collections of real incidents to use as practice scenarios
- **The VOID (formerly the Verica Open Incident Database).** URL: https://www.thevoid.community/
  - **Alive on 7 Nov 2026.** The database page invites you to "Search over 10,000 reports" (built on Softr) and offers impact-category filters such as cascading failure, connection issues and data loss. The home page offers the "2024 Report", an incident-management survey, a community AWS-outage dependency graph and an "Assess Your Incident Processes" service. Partners are listed as "These folks help keep the VOID running". The footer still reads © 2024 — [home, rendered](https://www.thevoid.community/), [database, rendered](https://www.thevoid.community/database)
  - Latest blog titles seen: "Announcing the 2025 VOID Incident Management Survey", "New Podcast: Uptime Labs and the Multiparty Dilemma", "Season 2 of The VOID Podcast is Here!", "MTTR Is (Still) Lying to You" — [blog, rendered](https://www.thevoid.community/blog)
- **Failure Modes.** URL: https://failuremodes.dev/
  - "a community of software practitioners to discuss and share stories about failures in production systems", with incident stories, curated resources and invite-only meetups in Bangalore and Pune held under the Chatham House Rule — [site](https://failuremodes.dev/)
  - Repository: electron0zero/failure-modes, MIT, 27 stars, last push 18 Jan 2026 — [GitHub](https://github.com/electron0zero/failure-modes)
- **Postmortem Index.** URL: https://postmortems.app/
  - "242 postmortems across 8 categories" (automation, cascading-failure, cloud, config-change, hardware, security, time, undescriptive) in a sortable table. Its data is "Postmortem metadata from danluu/post-mortems", so it is a filterable view of a list the handbook already has — [site](https://postmortems.app/), [GitHub icco/postmortems, last push 5 Nov 2026](https://github.com/icco/postmortems)
- **How They SRE.** URL: https://github.com/upgundecha/howtheysre
  - "A curated collection of publicly available resources on how technology and tech-savvy organizations around the world practice Site Reliability Engineering". 9,833 stars, last push 30 Sep 2026 — [GitHub](https://github.com/upgundecha/howtheysre)
- **Resilience engineering papers.** URL: https://github.com/lorin/resilience-engineering
  - Lorin Hochstein's reading list (resiliencepapers.club), with 3,076 stars and a last push on 31 Oct 2026. This is reading for L4 leads, not a game — [GitHub](https://github.com/lorin/resilience-engineering)

#### F. Mechanical Rock: anything besides DevOps Dream?
- devops.games still lists only **DevOps Dream**. The play link is https://dream.devops.games/, the footer links to Mechanical Rock, and no other game is offered — [devops.games](https://devops.games/)
- The site also links WayFinder (wayfinder.ninja), a DORA-benchmarking platform that plugs into source control, CI/CD and incident tools. It is not a game: it needs sign-up and has Pro and Enterprise tiers — [WayFinder](https://wayfinder.ninja/)

### Inferences
- **Best new picks, for quality and a no-account browser experience:** Server Survival, K8s Games, SDPD, SystemLore, System Design Sim, TWiG Online, PagerDuty IR training, and The VOID. All have a large or active user base, an active maintainer or an institutional owner. ON-CALL, Pit Wall, non-call and The Incident Challenge are worth a "new in 2026, may change" label.
- Server Survival and K8s Games are the closest thing to a free "chaos engineering game": failures arrive on their own and you must react. No well-maintained, standalone, free browser chaos-engineering game turned up. The real chaos tools (Steadybit, Litmus, Gremlin) need a platform installed or an account.
- The Incident Challenge is the only one here that works like a real investigation (staging vs production evidence). Note that it needs a Google or LinkedIn account; the handbook already accepts "free account" entries such as SysAdmin Simulator.
- Deployments and Disasters, the Twilio template and the Equal Experts playbook complement Wheel of Misfortune well. They give an L3/L4 reader ready-made rules and templates for the game day in module 33 §8.

### Gaps
- **SystemLore:** I found no owner, licence or pricing page (/pricing returns 404). "No signup needed" is confirmed, but long-term free status is not.
- **The Incident Challenge:** no pricing is shown. I could not confirm it stays free, because I did not sign in.
- **StackMonkey:** the site links a GitHub org (Stack-Monkey), but the API listing of its repositories returned nothing usable, so licence and activity are unconfirmed.
- **The CTO Game and non-call:** I only saw the landing pages. I did not play far enough to judge depth or check whether later screens need an account.
- **learningfromincidents.io:** status unknown. WebFetch and curl failed with a TLS handshake error, and the built-in browser could not open the page. A search found nothing 2026-specific — [search result example](https://chronosphere.io/learn/conference-recap-learning-from-incidents-lfi-2023/).
- **Possibly paid, not checked:** the G2G3 / GamingWorks "Phoenix Project" DevOps simulation, Okaloa Flowlab and getKanban. A search snippet mentioned G2G3 but did not show whether it is free ([Kirill Klimov list](https://kirillklimov.com/kanban-games/)). I did not open their pricing, so they are left out rather than labelled "paid".

## Q2. Details for each find: format, what you practise, free vs paid, sign-up, browser vs install, level, maintenance

### Takeaway
Every recommended item runs in the browser or is a document or PDF; none needs an install. Only The Incident Challenge needs an account. Server Survival, K8s Games, SDPD and PagerDuty are clearly maintained in 2025–2026. The tabletop kits are free but stale (2020–2022), which matters little for rules documents.

### Cited Findings
- No sign-up is stated on the sites for: ON-CALL ("Free, no signup"), Server Survival (browser or file save), K8s Games ("No install, no signup"), SystemLore ("No signup needed"), System Design Sim ("No account is needed"), StackMonkey ("No credit card"), and TWiG Online (loaded without login) — [ON-CALL](https://oncall-simulator.vercel.app/), [Server Survival](https://pshenok.github.io/server-survival/), [K8s Games README](https://github.com/rohitg00/k8sgames), [SystemLore](https://systemlore.com/), [System Design Sim about](https://systemdesignsim.com/about), [StackMonkey](https://stackmonkey.dev/), [TWiG](https://analytics.actionableagile.com/twig/index.html)
- Account required: The Incident Challenge (Google or LinkedIn sign-in, even for past rounds) — [demo](https://challenge.theincidentchallenge.com/#/demo)
- Downloadable documents only, nothing to install: Rolls & Responders PDFs and ZIP, the Oh Noes! ZIP, Featureban slides, the Twilio template and the Equal Experts PDF — [NCSC NZ](https://www.ncsc.govt.nz/protect-your-organisation/rolls-and-responders/), [Expel](https://expel.com/oh-noes-cybersecurity-tabletop/), [Agendashift](https://www.agendashift.com/resources/featureban), [Twilio](https://github.com/twilio/gameday), [Equal Experts](https://playbooks.equalexperts.com/chaos-day-playbook)
- Maintenance from GitHub on 7 Nov 2026, by last push:

  | Repository | Last push | Stars |
  |---|---|---|
  | Server Survival | 4 Nov 2026 | 6,479 |
  | Pit Wall | 4 Nov 2026 | 0 |
  | Defensomania | 6 Nov 2026 | 66 |
  | postmortems.app | 5 Nov 2026 | 47 |
  | PagerDuty IR docs | 30 Oct 2026 | 1,052 |
  | ON-CALL | 18 Oct 2026 | 0 |
  | How They SRE | 30 Sep 2026 | 9,833 |
  | SDPD | 13 Jul 2026 | 97 |
  | K8s Games | 28 Apr 2026 | 1,458 |
  | Failure Modes | 18 Jan 2026 | 27 |
  | Deployments and Disasters | 13 Apr 2022 | 8 |
  | Twilio gameday | 13 Oct 2020 | 139 |

  — [GitHub API results per repo linked above]

### Inferences
At-a-glance table. Levels follow the handbook scale (L0 fresher to L4 lead) and are my judgement from the content described above.

| Find | Format | What you practise | Cost / sign-up | Level | Maintained? |
|---|---|---|---|---|---|
| [Server Survival](https://pshenok.github.io/server-survival/) | Browser 3D tower-defence | Scaling, caching, queues, WAF/DDoS, cost vs capacity | Free, no account, MIT | L1–L3 | Yes (Nov 2026) |
| [K8s Games](https://k8sgames.com/) | Browser 3D K8s simulator | kubectl, CrashLoopBackOff, scaling; Chaos mode incidents; timed outage challenges | Free, no account, Apache-2.0 | L0–L2 (Chaos mode L2) | Yes (Apr 2026) |
| [SDPD](https://sdpd.live/) | Browser detective/puzzle game | Name the root cause of 33 distributed-system failures; chaos simulator | Free, OSS (MIT) | L2–L3 | Yes (Jul 2026) |
| [SystemLore](https://systemlore.com/) | Browser simulation game | Keep a service alive through spikes, outages, caches, shards, failover; post-mortem per run | Free, no sign-up | L1–L3 | Active site; owner unknown |
| [System Design Sim](https://systemdesignsim.com/playground) | Browser simulator with challenges | Real AWS/Azure/GCP capacity, p99, errors and the monthly bill | Free, no account; paid extras planned | L2–L4 | New (June 2026), solo maintainer |
| [StackMonkey](https://stackmonkey.dev/) | Browser simulator | Queues, retry storms, which component fails first | Free | L2–L4 | Active site |
| [The CTO Game](https://thectogame.com/) | Browser strategy game | Architecture vs velocity vs tech-debt trade-offs | Free to load; depth and account unverified | L3–L4 | Mar 2026 launch |
| [ON-CALL](https://oncall-simulator.vercel.app/) | Browser decision game | Triage order, mitigate vs fix, error budget, blast radius | Free, no sign-up | L1–L2 | Brand-new (Oct 2026) |
| [Pit Wall On-Call](https://pitwall.rafifdzaky.com/) | Browser real-time console, daily incident | Acknowledge, read alerts, metrics and logs, find the real cause; postmortem | Free; needs a 1024 px screen | L1–L3 | New, active |
| [non-call](https://serum.sh/non-call/) | Browser terminal-style game | Alert prioritisation, interruptions, hand-off at 07:00 | Free | L1–L3 | New (Oct 2026) |
| [The Incident Challenge](https://theincidentchallenge.com/) | Live competitive debugging rounds every two weeks | Staging vs production root cause under time pressure | Free to enter (no price seen); Google or LinkedIn sign-in | L2–L4 | Active (rounds into Nov 2026) |
| [TWiG Online](https://analytics.actionableagile.com/twig/index.html) | Browser team flow simulation + PDFs | WIP limits, pull, blockers, flow metrics | Free, no login | L2–L4 | Live |
| [Featureban](https://www.agendashift.com/resources/featureban) | Card/board game (CC BY-SA) + free online version | Kanban, WIP limits, flow metrics | Free | L1–L4 (team) | Rules v3.0 (2019); online version live |
| [Deployments and Disasters](https://antolius.github.io/deployments-and-disasters/) | Tabletop RPG rules (web) | Incident roles, communication, decisions | Free (CC0) | L2–L4 (game master L3+) | Stale (2022) |
| [Twilio GameDay template](https://github.com/twilio/gameday) | Markdown template | Plan a game day: SLOs/SLIs, roles, checklists | Free (MIT) | L2–L4 | Stale (2020) |
| [Equal Experts Chaos Day Playbook](https://playbooks.equalexperts.com/chaos-day-playbook) | Web playbook + PDF | Design and run Chaos Days | Free | L3–L4 | Last updated about 2 years ago |
| [PagerDuty IR training](https://response.pagerduty.com/training/overview/) | Docs + open-source course and slides | IC, scribe, liaison roles; severity; postmortems | Free | L1–L4 | Yes (Oct 2026) |
| [Rolls & Responders](https://www.ncsc.govt.nz/protect-your-organisation/rolls-and-responders/) / [Oh Noes!](https://expel.com/oh-noes-cybersecurity-tabletop/) / [Defensomania](https://karneades.github.io/Defensomania/play/) | Security IR tabletop kits and card games | Security incident decisions and priorities | Free downloads / online dealer | L2–L4 | Defensomania active (Nov 2026); others 2026 kits/pages |
| [The VOID](https://www.thevoid.community/) | Incident report database | Read real incidents and name the failing layer | Free to browse | L2–L4 | Alive; 2024 report, 2025 survey |
| [Failure Modes](https://failuremodes.dev/) | Incident stories + India meetups | Incident stories from Indian practitioners | Free | L1–L4 | Yes (Jan 2026) |
| [Postmortem Index](https://postmortems.app/) | Sortable postmortem index | Filter the danluu list by category | Free | L1–L4 | Yes (Nov 2026) |
| [How They SRE](https://github.com/upgundecha/howtheysre) | Curated list | How real orgs run SRE | Free | L3–L4 | Yes (Sep 2026) |

### Gaps
- Levels are my judgement, not stated by the sites, except SDPD and System Design Sim. SDPD positions itself for system-design interviews, and System Design Sim says it is "For engineers going from SDE-2 to staff" ([home](https://systemdesignsim.com/)).
- I did not play any game end to end, so I cannot speak to scenario accuracy, for example whether ON-CALL's "right move" choices match real SRE practice.

## Q3. Which handbook module each find fits

### Takeaway
Module 54 (Practice Arena, games section) should host most of them:
- **On-call games** go in the "incident response, SRE and culture" table, cross-linked to 25 (Site down).
- **Scaling and system-design games** go to 39 (Senior architecture), with 23 (Slow system) for bottleneck thinking.
- **Flow games** go to 39 and 40.
- **PagerDuty IR training** goes to 52 and 33.
- **Game-day kits** go to 33 §8 (the game day).
- **Incident libraries** sit next to Dan Luu and k8s.af in 54 and 39.

### Cited Findings
- Module 54's games table ("From mid-level up, the hard part of an incident is coordination more than commands") currently lists Wheel of Misfortune, DevOps Dream, DORA Quick Check, Backdoors & Breaches, Dan Luu's post-mortems, k8s.af, SysAdmin Simulator and Uptime Labs — [local file 54-practice-arena.md, lines 516–530](54-practice-arena.md)
- Module 33 has an "L4 exit test: the game day" section, which module 54 links to — [local file 54-practice-arena.md, line 563](54-practice-arena.md)

### Inferences
| Find | Primary module | Secondary |
|---|---|---|
| ON-CALL, Pit Wall On-Call, non-call | 54 (SRE/culture table) | 25 Site-down playbook, 52 Day-to-day (on-call) |
| The Incident Challenge | 54 | 25, 23 |
| Server Survival, SystemLore, System Design Sim, StackMonkey | 39 Senior architecture | 23 Slow-system (bottleneck thinking), 54 |
| SDPD | 39 | 54; 40 Career ladder (interview prep) |
| K8s Games | 54 (section 4, Kubernetes) | 26/46 Kubernetes incidents; 31 Learn Kubernetes |
| The CTO Game | 40 Career ladder | 39 |
| TWiG Online, Featureban | 39 | 40, 33 (flow, WIP, DORA lead time) |
| PagerDuty IR training + postmortem docs | 52 DevOps day-to-day | 33 CI/CD-IaC-SRE, 25, 40 (IC role as L3/L4 skill) |
| Deployments and Disasters, Twilio GameDay template, Equal Experts Chaos Day Playbook | 33 (§8 game day) | 54 ("Run a Wheel of Misfortune session") |
| Rolls & Responders, Oh Noes!, Defensomania | 37 Security / 48 Wazuh | 54 (next to Backdoors & Breaches) |
| The VOID, Failure Modes, Postmortem Index, How They SRE | 54 (postmortem reading) | 39 |

### Gaps
- None beyond the judgement calls above. Module numbers come from the handbook's file names and the brief.

## Q4. Status of resources already in the handbook (changes since 3 Oct 2026)

### Takeaway
Nothing in the handbook's list has shut down or gone paid-only. There are two small changes:
- **Backdoors & Breaches:** the link the handbook uses now redirects to a new path.
- **YouBrokeProd:** still offline with the same "Back Online Soon" notice.

### Cited Findings
- Each of these returned HTTP 200 on 7 Nov 2026: devops.games and dream.devops.games, dora.dev/quickcheck, dastergon.github.io/wheel-of-misfortune, k8s.af, sre.google/sre-book/accelerating-sre-on-call, sys-admin-simulator.com/practice/incident-response, uptimelabs.io (redirects to www.uptimelabs.io), letsdefend.io, blueteamlabs.online, hackthebox.com/blog and github.com/lucky-sideburn/kubeinvaders — [curl check, 7 Nov 2026; e.g. devops.games](https://devops.games/)
- **Backdoors & Breaches:** https://www.blackhillsinfosec.com/projects/backdoorsandbreaches/ now redirects to https://www.blackhillsinfosec.com/tools/backdoorsandbreaches/. A "classic" sub-page also exists at /tools/backdoorsandbreaches/classic/ — [BHIS](https://www.blackhillsinfosec.com/tools/backdoorsandbreaches/), [search result](https://www.blackhillsinfosec.com/tools/backdoorsandbreaches/classic/)
- **Wheel of Misfortune:** the repository's "homepage" field now points to https://dastergon.gr/wheel-of-misfortune/, which returns 404. The github.io URL the handbook uses still works — [GitHub](https://github.com/dastergon/wheel-of-misfortune)
- **YouBrokeProd:** still shows "Back Online Soon. We are currently migrating and upgrading our platform", © 2026 Smaash Labs LLC, the same state the handbook records for 3 Oct 2026 — [youbrokeprod.com](https://youbrokeprod.com/)
  - Background: the developer's DEV post lists 10+ scenarios, a free tier and a paid Pro tier — [DEV](https://dev.to/cdnsteve/how-i-turned-my-worst-on-call-nightmare-into-a-browser-game-36fa).
  - A 10 Mar 2026 Show HN offered a playable version of a Terraform-destroy incident — [HN item 47323915](https://news.ycombinator.com/item?id=47323915)

### Inferences
- In module 54, update the Backdoors & Breaches link to /tools/backdoorsandbreaches/, though the old one still redirects. Keep the dastergon.github.io link for Wheel of Misfortune and not the repo's new homepage, which is broken. Keep YouBrokeProd in the "offline" table.

### Gaps
- I checked HTTP status and the redirect target only. I did not re-check free/paid terms on Uptime Labs, LetsDefend or Blue Team Labs pricing pages.
