# 33 — Learn: Git, CI/CD, Infrastructure as Code & SRE Practice

This is the automation and operating-discipline module of the handbook. The other learn modules
teach you how a server, a network, a container and a cluster work. This one teaches you how to
**change** them safely and repeatably, and how to behave when a change goes wrong: Git to record
every change, GitLab CI/CD to build and ship it, Ansible and Terraform to make servers and
infrastructure reproducible, a secrets workflow that does not leak, and the SRE habits (incident
response, postmortems, change requests, runbooks, SLOs) that turn a good troubleshooter into a
senior engineer people trust with production.

Everything here is anchored to your real stack: on-prem Ubuntu servers, Apache workloads moving
to Dokploy (Traefik, Docker Swarm mode, `dokploy-network`), GitLab CI, a Harbor registry behind
a private CA, and a kubeadm Kubernetes cluster with containerd. The incident that started this
handbook, [Apache holds 443, deploy Dokploy](21-case-apache-443-dokploy.md), is the running
example. You solved it by moving Apache to ports 81 and 444 so Traefik could own 80 and 443
([Deployment patterns](35-deployment-patterns.md) analyses that fix and shows how to finish it
with Traefik routing). By the end of this module you will be able to rebuild that server with
Ansible, ship the new app through a pipeline into Harbor and Dokploy, roll it back in one click,
write the change request that finally retires system Apache, and write the postmortem if it
goes wrong.

> All sample outputs are illustrative: Ubuntu 22.04/24.04 (git 2.34/2.43), GitLab 17–19 with
> GitLab Runner 17–19 (GitLab 19.0 shipped in May 2026), Ansible core 2.16+, Terraform 1.9+, Docker Engine 27+. IPs come from
> documentation ranges (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) or private lab ranges
> (192.168.56.0/24). UPPERCASE words in commands are placeholders: HOST, PORT, BRANCH, SHA,
> PROJECT_ID, TOKEN, APP_ID, IMAGE, TAG.

---

## 0. How to use this module

> 📚 **Study path:** 1) KodeKloud: *GIT for Beginners* ([course](https://kodekloud.com/courses/git-for-beginners)) · 2) KodeKloud: *Ansible Basics Course* ([course](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course)) · 3) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · 4) KodeKloud: *Terraform Basics Training Course* ([course](https://kodekloud.com/courses/terraform-basics-training-course)) · 5) KodeKloud: *Fundamentals of SRE* ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · each ## area below names the exact sections, the handbook note, a video and a lab, in the order to do them.

### Who this module is for

This module serves every career stage, but each stage owns a different slice of it. Find your
row, put your hours into its sections, and skim the rest so you know what is coming. The tags
used on every topic below combine the Ops Ladder level and the career stage, for example
[L3 · Senior].

| Stage | Tag | What you own in this area | Focus sections | You have reached it when |
|---|---|---|---|---|
| Fresher (0–1 yr) | [L0 · Fresher] | Git without fear: commit, branch, push, open an MR, revert a bad commit | 1 | you can revert a bad commit on a shared branch and recover a "lost" commit from the reflog in under 5 minutes |
| Junior (1–2 yrs) | [L1 · Junior] | Working inside the team workflow; reading pipeline logs; running existing playbooks with `--check --diff` | 1, 2 (anatomy, debugging), 4 (running playbooks) | you fix a red pipeline caused by YAML, a missing variable or a stuck job without asking for help |
| Mid-level (2–4 yrs) | [L2 · Mid] | Debugging the automation itself: runners, executors, x509 to Harbor, idempotency bugs, state locks | 2, 3, 4, 5 (state), 6 | you can explain why a job is stuck, why a push to Harbor fails with x509, and why a playbook reports `changed` on every run |
| Senior (4–7 yrs) | [L3 · Senior] | Designing pipelines, roles, modules, the secrets flow and the rollback path | 2–6 in full, 7 (change management) | the Ops Ladder L3 exit test passes: GitLab CI builds, pushes to Harbor, Dokploy deploys, and the rollback was actually tested |
| Lead / SRE (5+ yrs) | [L4 · Lead/SRE] | Running production as a practice: incidents, postmortems, change control, SLOs, on-call, toil | 7, 8 | you have run the game day, published the postmortem, and your team's changes follow a written CR format |

> Fresher and junior readers: section 1 is the whole job for now. Read sections 2 and 4 only far
> enough to understand the pipeline and playbook you are asked to use, then come back later.

### Learning path

The areas are grouped by tool so the module also works as a reference. To learn from zero,
follow this order. Level tags come from your Ops Ladder (L0 Foundations, L1 Operator,
L2 Troubleshooter, L3 Platform, L4 SRE) plus the matching career stage. Git is L0 because every
other skill in this module assumes it; CI/CD and IaC are L3; the operating discipline is L4.

| # | Topic | Tag | Section | Why it is in this position |
|---|---|---|---|---|
| 1 | Git object model, three trees, branches | [L0 · Fresher] | 1 | you cannot undo safely what you do not understand |
| 2 | Undoing mistakes, reflog rescue | [L0 · Fresher] | 1 | the L0 exit test includes "revert a bad Git commit" |
| 3 | Merge, rebase, conflicts, tags, signed commits | [L1 · Junior] | 1 | daily team work and release tagging |
| 4 | A team branching workflow | [L1 · Junior] | 1 | how changes reach `main` and production |
| 5 | Ansible: inventory, ad-hoc, playbooks, idempotency | [L3 · Senior] | 4 | you already do these steps by hand on every server |
| 6 | Ansible: handlers, variables, templates, roles, vault | [L3 · Senior] | 4 | the Ops Ladder drill: Docker with your daemon.json |
| 7 | GitLab CI anatomy, rules, variables | [L3 · Senior] | 2 | how a commit becomes a pipeline (juniors: read it to debug) |
| 8 | Runners, executors, artifacts vs cache | [L3 · Senior] | 2 | most "pipeline is stuck/slow" problems live here |
| 9 | Building images and pushing to Harbor | [L3 · Senior] | 2 | the Ops Ladder drill: build, tag with the SHA, push |
| 10 | Deploying to Dokploy and Kubernetes, environments | [L3 · Senior] | 2 | the L3 exit test, end to end |
| 11 | Debugging failed pipelines | [L2 · Mid] | 2 | the first CI skill anyone will ask of you |
| 12 | Deployment strategies and rollback design | [L3 · Senior] | 3 | how to ship without an outage and undo without panic |
| 13 | Secrets management | [L3 · Senior] | 6 | every pipeline and playbook needs secrets |
| 14 | Terraform: state, plan/apply, modules, remote state | [L3 · Senior] | 5 | VMs and cloud resources as code (Proxmox, vSphere, AWS) |
| 15 | Troubleshooting method, incident response | [L4 · Lead/SRE] | 7 | what to do in the first ten minutes of an outage |
| 16 | Postmortems, change management, runbooks | [L4 · Lead/SRE] | 7 | the Ops Ladder L4 drills; your public proof of skill |
| 17 | On-call, toil, SLOs and error budgets | [L4 · Lead/SRE] | 7 | operating, not only fixing ([Observability](32-learn-performance-observability.md)) |
| 18 | L4 exit test: the game day | [L4 · Lead/SRE] | 8 | the Ops Ladder L4 exit test |
| 19 | Self-check and exit tests per stage | all | 9 | proves the skill transferred out of the notes |

Ansible comes before GitLab CI on purpose: an Ansible playbook is the simplest possible
"automation that runs the same way every time", and the habits it teaches (idempotency, dry
runs, variables, secrets) carry straight into pipelines.

### Study method

For every ### topic, use the same five steps, in this order:

1. **Read this note** for the topic: concept, key terms, the "see it" commands. Ten to twenty minutes.
2. **Do the matching KodeKloud course lesson** (pointers sit at the top of each area under "Study path"), including its lab. KodeKloud labs are pre-built, so you practise without fighting setup.
3. **Optional video** if a concept still feels fuzzy. Stop as soon as it clicks.
4. **Hands-on lab on your own test VM or test project.** Build it, break it on purpose, fix it. Do not skip the "break" half; it is the half your job pays for.
5. **Open the related playbook** linked under "How it breaks" and read the scenario that matches what you just broke.

After each lab, write the five-line note from your weekly rhythm: symptom, first wrong guess,
evidence that settled it, fix, what you will check first next time. In this module those notes
are not just practice: section 7 turns them into runbooks, postmortems and a public portfolio.

> Timebox. One topic per 30–45 minute morning slot. Until your CKA exam, CKA sessions come
> first; the Git and Kubernetes-deploy topics count double because the exam and your homelab
> both use them.

### Build your automation lab

You need a small lab that mirrors work. Every "Hands-on lab" below assumes these machines.
Snapshot every VM after its base install so any "break it" step can be undone in seconds.

| VM | Address | Role | Size |
|---|---|---|---|
| ctrl | 192.168.56.10 | your workstation VM: git, Ansible, Terraform, kubectl | 2 vCPU, 2 GB |
| gitlab | 192.168.56.20 | GitLab CE (or skip it and use a free gitlab.com project) | 4 vCPU, 8 GB |
| runner01 | 192.168.56.21 | GitLab Runner with the Docker executor | 2 vCPU, 4 GB |
| harbor | 192.168.56.22 | Harbor registry with a certificate from your lab CA | 2 vCPU, 4 GB |
| dokploy | 192.168.56.30 | Dokploy (Traefik + Swarm), the "staging" target | 2 vCPU, 4 GB |
| k8s-cp1, k8s-w1 | 192.168.56.41–42 | kubeadm cluster from the [Kubernetes module](31-learn-kubernetes.md) | as in module 31 |
| target1, target2 | 192.168.56.51–52 | fresh Ubuntu 24.04 VMs for Ansible to configure | 1 vCPU, 1 GB |

The examples use the names your work servers will use: `gitlab.example.com`,
`harbor.example.com`, `dokploy.example.com`, internal DNS servers `192.0.2.53` and `192.0.2.54`.
In the lab, point those names at the lab IPs with your internal DNS or `/etc/hosts` on every VM.

> Never run the labs of this module against a work GitLab project, a work Harbor project, or a
> work server inventory. Several labs deliberately break pipelines, delete state, leak a fake
> secret into Git history or restart Docker.

A lab GitLab is optional. A free gitlab.com project with **your own runner registered to it**
gives you 95 percent of the learning (runners, executors, Harbor pushes, deploys) without
running GitLab itself. Install GitLab CE in the lab only when you want to practise GitLab
administration as well.

### Trust map for the private CA

Your Harbor (and possibly your GitLab) uses a certificate issued by a private CA. **Every client
keeps its own trust store**, so "x509: certificate signed by unknown authority" can come from
any of these places, and fixing one does not fix the others. Keep this table next to you for
the whole module.

| Client | Where it looks for the CA | Symptom when missing |
|---|---|---|
| Ubuntu tools (curl, git, apt, Python with system certs) | `/usr/local/share/ca-certificates/corp-root-ca.crt` then `sudo update-ca-certificates` | `curl: (60) SSL certificate problem: unable to get local issuer certificate` |
| Docker daemon pulling or pushing | `/etc/docker/certs.d/harbor.example.com/ca.crt` (no restart needed) | `x509: certificate signed by unknown authority` on pull or push |
| containerd on Kubernetes nodes | `/etc/containerd/certs.d/harbor.example.com/hosts.toml` | `ImagePullBackOff`, `crictl pull` shows the x509 error |
| gitlab-runner talking to GitLab | `/etc/gitlab-runner/certs/gitlab.example.com.crt` or `tls-ca-file` | `x509` when registering or polling for jobs |
| Docker-in-Docker service in CI | inside the dind container: `/etc/docker/certs.d/harbor.example.com/ca.crt` | push fails in CI but works from your laptop |
| buildah and skopeo | `/etc/containers/certs.d/harbor.example.com/ca.crt` | `x509` on `buildah push` or `skopeo copy` |
| Python requests (certifi bundle) | `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt` | `SSLError ... CERTIFICATE_VERIFY_FAILED` |
| Terraform providers, Vault CLI, Go tools | the system store (Go reads `/etc/ssl/certs`) or `SSL_CERT_FILE` | `x509: certificate signed by unknown authority` |

The trust-store details and the Harbor setup itself are in the [Docker module](30-learn-docker.md)
and the [x509 scenario in the containers playbook](26-playbook-containers-k8s.md#x509-unknown-authority-pulling-from-harbor).

---

## 1. Git

> 📚 **Study path:** 1) KodeKloud: *GIT for Beginners* — GIT Introduction → Git Branches → Initialize Remote Repositories → Rebasing → Resetting and Reverting (reflog last) ([course](https://kodekloud.com/courses/git-for-beginners)) · 2) Note: this section, topic by topic, then [Linux learn module](27-learn-linux.md) if the shell itself is new · 3) Video: KodeKloud *What is Git? | GIT Basics for DevOps Beginners* ([YouTube](https://www.youtube.com/watch?v=Lr7sYCrhxE0)) · 4) Practice: KodeKloud [Git playground](https://kodekloud.com/playgrounds/playground-git), then *Pro Git* chapters 1–3 ([book](https://git-scm.com/book/en/v2)) and the labs below.

Git is the first tool in this module because it is the foundation of everything after it:
pipelines run on commits, Ansible and Terraform code lives in repositories, change requests
link to merge requests, and "what changed?" (the first question of every incident) is answered
with `git log`. Learn the model once and every Git command stops being a magic spell.

### How Git stores your work

**Level:** [L0 · Fresher]

**Concept.** Git is a small database of **snapshots**, not a list of diffs. Each commit records
the complete state of the project at that moment, plus a pointer to the commit before it.
Unchanged files are not copied again; they are shared by reference. Everything is stored as
**objects**, and every object is named by the hash of its content, so nothing can change
silently: change one byte and you get a different name.

There are four object types:

```
 commit a1b2c3d ──parent──► commit 4e1d0c9 ──parent──► ...
   │  author, date, message
   ▼
 tree (the root directory)
   ├── blob  Dockerfile         (file content)
   ├── blob  README.md
   └── tree  app/
         └── blob  main.py

 branch "main"  = a file containing "a1b2c3d..."   (a movable pointer)
 HEAD           = "ref: refs/heads/main"            (which branch you are on)
 tag "v1.4.2"   = a pointer (or tag object) that should never move
```

**Key terms**

| Term | Meaning |
|---|---|
| Blob | The content of one file (no name, no permissions) |
| Tree | A directory listing: names, modes, and the blobs/trees they point to |
| Commit | A snapshot: one root tree, parent commit(s), author, committer, message |
| Ref | A name pointing at a commit: branches (`refs/heads/`), tags (`refs/tags/`), remote branches (`refs/remotes/`) |
| HEAD | The ref you currently have checked out; "detached HEAD" means it points at a commit directly |
| SHA | The object's hash name; 7–8 characters are usually enough to identify it |

**See it on a real system**

```bash
cd ~/lab/shop-web                # any repository
git log --oneline -3             # the last three commits
git cat-file -t HEAD             # the type of the object HEAD points at
git cat-file -p HEAD             # pretty-print the commit object
cat .git/HEAD                    # which branch HEAD points at
cat .git/refs/heads/main         # a branch is just a file holding a SHA (may be in .git/packed-refs instead)
```

```
a1b2c3d (HEAD -> main, origin/main) Add /healthz endpoint
4e1d0c9 Pin gunicorn to 23.0
77f0a12 Initial import from Apache docroot
commit
tree 9a3f1c2d8e7b6a5f4e3d2c1b0a9f8e7d6c5b4a39
parent 4e1d0c9b8a7f6e5d4c3b2a1f0e9d8c7b6a5f4e3d
author Ops Engineer <ops@example.com> 1759479600 +0000
committer Ops Engineer <ops@example.com> 1759479600 +0000

Add /healthz endpoint
ref: refs/heads/main
a1b2c3d4e5f60718293a4b5c6d7e8f9012345678
```

→ A commit is tiny: a tree, a parent, two identities and a message. The branch `main` is a
41-byte file. That is why branching in Git is instant and why "deleting a branch" only deletes
a pointer: the commits are still in the database until garbage collection removes unreachable
objects (which is what makes the reflog rescue in this section possible).

**Hands-on lab (test VM only)**

**Step 1 — Build a repository by hand and look inside.**

```bash
mkdir -p ~/lab/git-model && cd ~/lab/git-model
git init -b main
echo 'Listen 8081' > ports.conf
git add ports.conf
git commit -m "Apache listens on 8081"
find .git/objects -type f | sort        # three objects: blob, tree, commit
git cat-file -p HEAD^{tree}             # the tree lists ports.conf -> blob
```

```
.git/objects/1f/0c4e...
.git/objects/8b/2d1a...
.git/objects/d4/91f3...
100644 blob 5c7d0b2e9a1f3e4d5c6b7a8f9e0d1c2b3a4f5e6d    ports.conf
```

**Step 2 — Break it: "lose" a commit by deleting its branch.**

```bash
git switch -c experiment
echo 'Listen 8082' >> ports.conf && git commit -am "Add 8082"
git switch main
git branch -D experiment                # force-delete an unmerged branch
```

```
Deleted branch experiment (was 3c9e2f1).
```

**Step 3 — Fix it.** Git printed the SHA it was pointing at. The commit still exists, so point a
new branch at it:

```bash
git branch experiment 3c9e2f1
git log --oneline experiment -2
```

→ You just proved that branches are pointers and commits are durable. If you had not seen the
SHA, `git reflog` (later in this section) would give it to you.

**How it breaks**

| Symptom / error text | First command | Where to read more |
|---|---|---|
| `fatal: not a git repository (or any of the parent directories): .git` | `git rev-parse --show-toplevel` | you are outside the repo, or `.git` was not copied with the files |
| `error: object file .git/objects/... is empty` / `fatal: bad object HEAD` | `git fsck --full` | disk filled or VM crashed mid-write; see [Storage reference](01-storage-disk.md) |
| `You are in 'detached HEAD' state` | `git status` then `git switch -c BRANCH` | you checked out a SHA or tag; commits made here are easy to lose |

**Why it matters for troubleshooting.** "What changed?" is the first question in every incident.
If you know that every deploy is a commit and every commit is a snapshot, `git log` and
`git diff OLD NEW` become your fastest diagnostic tools for config repositories (Ansible,
Traefik dynamic files, Compose files).

**Next step:** learn the three places a change lives before it becomes a commit, because every
"undo" command works on one or more of them.

### The three trees: working tree, index, HEAD

**Level:** [L0 · Fresher]

**Concept.** A file change passes through three areas. The **working tree** is the files you
edit. The **index** (also called the staging area) is the exact snapshot your next commit will
contain. **HEAD** is the last commit. `git add` copies from working tree to index;
`git commit` turns the index into a commit and moves the branch.

```
  working tree   ── git add ──►   index (staging)   ── git commit ──►   HEAD (last commit)
       ▲                              │    ▲                                │
       └──── git restore FILE ────────┘    └──── git restore --staged ──────┘
   git diff  = working tree vs index      git diff --staged = index vs HEAD
```

Staging lets you commit **part** of your work: fix a typo and change a port in the same file,
then commit them separately with `git add -p`, so a reviewer (and a future `git revert`) sees
one logical change per commit.

**Key terms**

| Term | Meaning |
|---|---|
| Untracked | a file Git has never been told about |
| Modified / staged | changed in the working tree / copied into the index |
| `git add -p` | interactively stage hunks (parts of files) |
| `git diff --staged` | exactly what the next commit will contain |
| `git stash` | shelve working tree and index changes temporarily |

**See it on a real system**

```bash
git status
git diff                 # unstaged changes
git diff --staged        # staged changes (what will be committed)
```

```
On branch feature/healthz
Changes to be committed:
  (use "git restore --staged <file>..." to unstage)
	modified:   app/main.py

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   Dockerfile

Untracked files:
  (use "git add <file>..." to include in what will be committed)
	notes.txt
```

→ `app/main.py` is in the index and will be committed. `Dockerfile` is changed but will **not**
be committed unless you add it. `notes.txt` is invisible to Git. Read `git status` before every
commit; it prints the undo command for each area.

**Hands-on lab (test VM only)**

**Step 1 — Stage part of a file.** In `~/lab/git-model`, edit `ports.conf` to change two separate
lines, then run `git add -p ports.conf`, answer `y` for one hunk and `n` for the other, and
compare `git diff` with `git diff --staged`.

**Step 2 — Break it: commit the wrong thing.** Run `git commit -am "WIP"` (the `-a` stages every
tracked modified file, including the hunk you meant to keep out).

**Step 3 — Fix it without losing work.** Move the commit back into the index and restage
properly:

```bash
git reset --soft HEAD~1      # undo the commit, keep everything staged
git restore --staged ports.conf
git add -p ports.conf        # stage only the hunk you wanted
git commit -m "Change Apache port to 8081"
```

**How it breaks**

| Symptom | First command | Fix |
|---|---|---|
| A file you edited is missing from the commit | `git show --stat HEAD` | `git add FILE && git commit --amend --no-edit` (only if not pushed yet) |
| "nothing added to commit but untracked files present" | `git status` | `git add FILE` |
| Line-ending noise: every line shows as changed | `git diff --stat` and `file FILE` | set `core.autocrlf` correctly on Windows clients; add `.gitattributes` |

**Why it matters for troubleshooting.** Small, single-purpose commits are what make
`git revert` safe during an incident. A commit titled "WIP" that changes Traefik, the Compose
file and the app at once cannot be reverted without reverting all three.

**Next step:** branches, so you can work on a change without touching `main`.

### Branches, HEAD and remotes

**Level:** [L0 · Fresher]

**Concept.** A **branch** is a movable pointer to a commit; committing on a branch moves it
forward. A **remote** (usually `origin`) is another copy of the repository, for example on
your GitLab. `git fetch` downloads new commits and updates **remote-tracking branches** such as
`origin/main`, without touching your own branches. `git pull` is `fetch` plus a merge (or
rebase) into your current branch. `git push` uploads your commits and moves the branch on the
remote.

```
 your laptop                                   gitlab.example.com
 main ──► a1b2c3d                              main ──► f00ba12  (someone pushed)
 origin/main ──► a1b2c3d  (stale until fetch)
          git fetch  ──► origin/main ──► f00ba12   (now you can see it, nothing merged yet)
```

**Key terms**

| Term | Meaning |
|---|---|
| `git switch -c BRANCH` | create a branch and move HEAD to it (modern form of `checkout -b`) |
| Upstream | the remote branch your local branch tracks (`git push -u origin BRANCH` sets it) |
| Ahead / behind | how many commits you have that the remote lacks, and vice versa |
| Fast-forward | the target branch can just move forward; no merge commit needed |

**See it on a real system**

```bash
git branch -vv                       # local branches, their upstream and ahead/behind counts
git remote -v                        # where origin points (SSH or HTTPS URL)
git fetch --prune                    # update remote-tracking branches, drop deleted ones
git log --oneline --graph --all -15  # the whole picture
```

```
* feature/healthz a1b2c3d [origin/feature/healthz: ahead 1] Add /healthz endpoint
  main            4e1d0c9 [origin/main: behind 2] Pin gunicorn to 23.0
origin	git@gitlab.example.com:shop/shop-web.git (fetch)
origin	git@gitlab.example.com:shop/shop-web.git (push)
```

→ Your feature branch has one commit not yet pushed. Your local `main` is two commits behind
GitLab: anything you branch from it now starts from stale code. `git switch main && git pull`
first.

**Hands-on lab (test VM only)**

**Step 1 — Simulate a remote locally.** A bare repository behaves exactly like GitLab for
practice:

```bash
git init --bare ~/lab/remote.git
cd ~/lab/git-model && git remote add origin ~/lab/remote.git && git push -u origin main
git clone ~/lab/remote.git ~/lab/colleague     # a second "person"
```

**Step 2 — Break it: push from both clones.** Commit different changes in `~/lab/colleague` and in
`~/lab/git-model`, push from the colleague first, then push from yours:

```
 ! [rejected]        main -> main (fetch first)
error: failed to push some refs to '/home/USER/lab/remote.git'
hint: Updates were rejected because the remote contains work that you do not
hint: have locally.
```

**Step 3 — Fix it.** Never "fix" this with `--force`. Integrate first, then push:

```bash
git fetch origin
git log --oneline main..origin/main     # what they pushed that you do not have
git pull --rebase                       # replay your commit on top of theirs
git push
```

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `! [rejected] ... (fetch first)` / `non-fast-forward` | `git fetch && git status` | the remote moved; integrate before pushing |
| `Permission denied (publickey)` on push | `ssh -T git@gitlab.example.com` | wrong or missing SSH key; see [SSH reference](09-ssh-remote-access.md) |
| `remote: GitLab: You are not allowed to push code to protected branches on this project.` | check Settings → Repository → Protected branches | push to a branch and open a merge request instead |
| `server certificate verification failed. CAfile: /etc/ssl/certs/ca-certificates.crt CRLfile: none` | `git ls-remote https://gitlab.example.com/shop/shop-web.git` | private CA missing from the trust store (see the trust map) |

**Why it matters for troubleshooting.** "The pipeline built the wrong code" is very often a
stale local branch or a tag pointing at an unexpected commit. `git log --oneline --graph --all`
shows the truth in one screen.

**Next step:** the two ways to combine branches, and when each is safe.

### Merge vs rebase

**Level:** [L1 · Junior]

**Concept.** Both integrate the commits of one branch into another. **Merge** keeps history as
it happened and adds a merge commit with two parents. **Rebase** replays your commits on top of
the other branch, creating **new** commits with new SHAs, so the history looks linear.

```
 before:            A───B───C  main
                         \
                          D───E  feature

 git merge feature   A───B───C───────M  main        (M has two parents: C and E)
 (on main)                \         /
                           D───────E

 git rebase main     A───B───C───D'───E'  feature   (D', E' are NEW commits; D, E are abandoned)
 (on feature)
```

The golden rule: **never rebase commits that other people already have** (anything pushed to
a shared branch). Rebasing rewrites SHAs; everyone else's copy then disagrees with the remote.
Rebasing your own unpushed or personal feature branch is fine and keeps history clean.

**Key terms**

| Term | Meaning |
|---|---|
| Merge commit | a commit with two parents, recording an integration |
| `--no-ff` | always create a merge commit, even when a fast-forward was possible |
| Squash merge | combine all commits of a branch into one commit on the target (GitLab MR option) |
| Interactive rebase | `git rebase -i BASE`: reorder, squash, reword commits before sharing |
| `--force-with-lease` | force-push only if the remote is still where you last saw it |

**See it on a real system**

```bash
git log --oneline --graph --decorate -12     # merges show as forks and joins
git log --merges --oneline -5                # only merge commits
git config --get pull.rebase                 # how `git pull` integrates on this machine
```

**Hands-on lab (test VM only)**

**Step 1 — Do both on copies of the same history.** Create `feature` with two commits while
`main` gets one more commit. Copy the repository (`cp -a`), run `git merge feature` on `main` in
one copy and `git rebase main` on `feature` in the other. Compare `git log --graph` in both.

**Step 2 — Break it: rebase a shared branch.** Push `feature`, rebase it, and push again:

```
 ! [rejected]        feature -> feature (non-fast-forward)
```

A colleague who already pulled `feature` now has commits that no longer exist on the remote.

**Step 3 — Fix it the safe way.** If the branch is yours alone, `git push --force-with-lease`
(it refuses if someone else pushed in the meantime; plain `--force` silently overwrites their
work). If others use it, undo the rebase with `git reset --hard ORIG_HEAD` (see the warning in
"Undoing mistakes safely") and merge instead.

**How it breaks**

| Symptom | First command | Fix |
|---|---|---|
| A colleague's pushed commits vanished after your push | `git reflog` on their machine, `git log origin/BRANCH` | they re-push from their reflog; you stop using `--force` |
| `fatal: Need to specify how to reconcile divergent branches.` on `git pull` | `git config --global pull.rebase false` (merge) or `true` (rebase) | pick a team default once |
| The same conflict appears again and again during a rebase | `git rebase --abort` | merge instead, or enable `git config --global rerere.enabled true` |

**Why it matters for troubleshooting.** A linear history makes `git bisect` (binary search for
the commit that broke something) and "which commit is deployed?" much easier to answer. That
is why many teams squash-merge MRs into `main`.

**Next step:** conflicts, which both merge and rebase can produce.

### Resolving merge conflicts

**Level:** [L1 · Junior]

**Concept.** A conflict happens when both sides changed the same lines (or one side deleted a
file the other changed). Git stops, writes both versions into the file between markers, and
waits for you to decide. Resolving is a **content** decision, not a Git one: you must know
which value is correct, which is why you read both sides before choosing.

```
<<<<<<< HEAD                  (your side: the branch you are on)
      - "traefik.http.services.shop.loadbalancer.server.port=8000"
||||||| base                  (the common ancestor, shown with merge.conflictStyle diff3)
      - "traefik.http.services.shop.loadbalancer.server.port=80"
=======
      - "traefik.http.services.shop.loadbalancer.server.port=8080"
>>>>>>> feature/port-change   (their side)
```

→ The base shows the original value was 80. You changed it to 8000, they changed it to 8080.
Without the base you only see two different numbers; with it you see that both sides changed
the line and you must ask which port the app really listens on. Turn the base on once:

```bash
git config --global merge.conflictStyle diff3     # Ubuntu 22.04 (git 2.34)
git config --global merge.conflictStyle zdiff3    # git 2.35+ (Ubuntu 24.04): same, less noise
```

**Key terms**

| Term | Meaning |
|---|---|
| Ours / theirs | during a merge: ours = current branch, theirs = branch being merged. During a rebase they are **swapped** |
| `git merge --abort` / `git rebase --abort` | return to the state before you started |
| `git checkout --ours FILE` / `--theirs FILE` | take one side for a whole file |
| `git mergetool` | open a 3-way merge tool (vimdiff, meld) |

**See it on a real system**

```bash
git status                              # "both modified:" lists conflicted files
git diff --name-only --diff-filter=U    # only the conflicted file names
git diff                                # conflicts with context
```

**Hands-on lab (test VM only)**

**Step 1 — Create the conflict.** On `main`, set the port label to 8000 in `compose.yml` and
commit. On a branch from the previous commit, set it to 8080 and commit. Merge the branch into
`main`.

**Step 2 — Break it on purpose: resolve wrongly.** Delete only the marker lines, keep both
port lines, `git add` and commit. Run `docker compose config` (or `python3 -c 'import yaml,sys; yaml.safe_load(open("compose.yml"))'`):
the file is now invalid or has a duplicate label.

**Step 3 — Fix it.** The bad merge exists only on your machine, so drop it and merge again, and
this time keep exactly one line with the correct port, then validate before committing. (Do not
"revert the merge, then merge the branch again": after `git revert -m 1`, Git still considers the
branch merged and the second merge answers `Already up to date.` On a shared branch you would fix
forward with a new commit, or revert the revert.)

```bash
git reset --hard HEAD~1       # drop the unpushed bad merge (HEAD~1 = main before the merge)
git merge feature/port-change
# edit compose.yml: keep one correct line, remove all markers
grep -n '^<<<<<<<\|^=======\|^>>>>>>>' compose.yml || echo "no markers left"
docker compose config >/dev/null && git add compose.yml && git commit
```

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Conflict markers reached production config | `git grep -n '^<<<<<<< '` | someone committed without resolving; add a CI check for markers |
| `error: Committing is not possible because you have unmerged files.` | `git status` | resolve, `git add`, then commit |
| Rebase "ours/theirs" picked the wrong side | `git rebase --abort` | the meanings are swapped during a rebase |

**Why it matters for troubleshooting.** A config file with a half-resolved conflict is a
classic "it broke right after a merge" outage. A pipeline job that runs `apache2ctl -t`,
`docker compose config`, `nginx -t` or `ansible-lint` on every MR catches it before deploy.

**Next step:** undoing mistakes, which is what you will most often reach for Git under stress.

### Undoing mistakes safely

**Level:** [L0 · Fresher]

**Concept.** Git has several "undo" commands because there are several things to undo: a file
edit, a staged file, a local commit, or a commit everybody already has. Choose by asking two
questions: **which area** do I want to change (working tree, index, branch pointer), and **has
anyone else got this commit** (was it pushed to a shared branch)?

| Command | Moves the branch | Index | Working tree | Use for |
|---|---|---|---|---|
| `git restore FILE` | no | untouched | **discards** uncommitted edits to FILE | throw away a local edit |
| `git restore --staged FILE` | no | FILE unstaged | kept | unstage |
| `git reset --soft HEAD~1` | back one commit | kept (changes staged) | kept | redo the last local commit |
| `git reset --mixed HEAD~1` (default) | back one commit | reset (changes unstaged) | kept | split or restage the last local commit |
| `git reset --hard HEAD~1` | back one commit | reset | **reset: uncommitted work is lost** | throw away local commits and edits |
| `git revert SHA` | no, adds a new commit | n/a | n/a | undo a commit that is already pushed or deployed |
| `git commit --amend` | replaces the last commit | n/a | n/a | fix the last local commit's message or content |

The rule for shared history: **pushed means revert**. `git revert` creates a new commit that is
the inverse of the old one, so everyone's history still agrees and the pipeline can deploy the
revert like any other change. `reset` rewrites history and is only for commits that exist on
your machine alone.

> ⚠️ `git reset --hard` and `git restore FILE` destroy **uncommitted** work, which no Git command
> can recover (it was never stored as an object). Safer first: run `git stash push -u -m
> "before reset"` (keeps a recoverable copy, including untracked files), or `git status` and
> `git diff` to see what you would lose. Committed work is recoverable through the reflog;
> uncommitted work is not.

**Key terms**

| Term | Meaning |
|---|---|
| `HEAD~1` | the first parent of HEAD (one commit back); `HEAD~3` is three back |
| `ORIG_HEAD` | where HEAD was before the last reset, merge or rebase |
| `git revert -m 1 MERGE_SHA` | revert a merge commit, keeping parent 1 (the main line) |
| `git stash` / `git stash pop` | shelve and restore uncommitted work |

**See it on a real system**

```bash
git log --oneline -5
git show --stat HEAD            # what the last commit changed, before you undo it
git revert --no-edit HEAD       # create the inverse commit
git log --oneline -3
```

```
9d8c7b6 (HEAD -> main) Revert "Set Traefik service port to 8080"
5e4f3a2 Set Traefik service port to 8080
a1b2c3d Add /healthz endpoint
```

→ History now shows both the mistake and its undo, which is exactly what you want on a shared
branch: the pipeline deploys `9d8c7b6`, and the postmortem can point at `5e4f3a2`.

**Hands-on lab (test VM only)** — this is the Ops Ladder L0 exit test item "revert a bad Git commit".

**Step 1 — Make three commits** in `~/lab/git-model`: a good one, a bad one (break `ports.conf`),
and another good one. Push them to `~/lab/remote.git`.

**Step 2 — Revert the bad one in the middle** without touching the others:

```bash
git log --oneline -4
git revert --no-edit SHA_OF_BAD_COMMIT
git push
```

**Step 3 — Practise each reset mode on unpushed commits.** Make a local commit and run
`reset --soft`, check `git status` (changes staged); recommit, run `reset --mixed`, check
(changes unstaged); recommit, `git stash push -u` anything you care about, then `reset --hard`
and check (changes gone from the working tree, commit only reachable via the reflog).

**How it breaks**

| Symptom | First command | Fix |
|---|---|---|
| "I reset --hard and lost my commits" | `git reflog` | next topic: reflog rescue |
| "I reset --hard and lost my uncommitted edits" | `git fsck --lost-found` (only finds content that was once `git add`ed) | usually unrecoverable; restore from editor backups |
| Revert of a merge fails: `is a merge but no -m option was given` | `git show SHA` (see "Merge:" line) | `git revert -m 1 SHA` |
| Reverting the revert is needed later to re-apply the change | `git revert REVERT_SHA` | yes, reverts can be reverted |

**Why it matters for troubleshooting.** In an incident the fastest safe mitigation is very often
"revert the last change and let the pipeline redeploy". Knowing that `git revert` is safe on
shared branches lets you do it in 30 seconds, without a debate.

**Next step:** what to do when you have already used the destructive command.

### Reflog rescue

**Level:** [L0 · Fresher] (the rescue itself), [L1 · Junior] (rebase undo)

**Concept.** The **reflog** is a local diary of every position HEAD and each branch have had:
commits, resets, rebases, checkouts, amends. Because commits are only deleted by garbage
collection after they are unreachable **and** older than the reflog expiry (by default 90
days for reachable entries, 30 days for unreachable ones), almost any committed work can be
found again. The reflog is **local only**: it is not pushed, and a fresh clone has an empty one.

**Key terms**

| Term | Meaning |
|---|---|
| `HEAD@{2}` | where HEAD was two moves ago |
| `main@{yesterday}` | where `main` was yesterday (time-based reflog lookup) |
| `git reflog show BRANCH` | the reflog of one branch |
| `git fsck --lost-found` | find dangling objects not referenced by any ref or reflog |

**See it on a real system**

```bash
git reflog -8
```

```
a1b2c3d (HEAD -> main) HEAD@{0}: reset: moving to HEAD~3
f4e5d6c HEAD@{1}: commit: Add Traefik labels for shop-web
0b1c2d3 HEAD@{2}: commit: Add healthcheck to Dockerfile
7e8f9a0 HEAD@{3}: commit: Move gunicorn to port 8000
a1b2c3d (HEAD -> main) HEAD@{4}: checkout: moving from feature/healthz to main
```

→ Reading bottom-up: three commits were made, then `reset: moving to HEAD~3` threw them away.
The commit you want is `f4e5d6c` (HEAD@{1}), the last state before the reset.

**Hands-on lab (test VM only)**

**Step 1 — Lose work on purpose.** Make three commits, then `git reset --hard HEAD~3`.
`git log` no longer shows them.

**Step 2 — Find and restore them.** Create a rescue branch first (non-destructive), inspect it,
then move your branch:

```bash
git reflog -5
git branch rescue HEAD@{1}           # safe: only adds a pointer
git log --oneline rescue -4          # confirm these are the commits you want
git reset --hard rescue              # move main back (nothing uncommitted to lose here)
git branch -d rescue
```

**Step 3 — Undo a bad rebase.** Rebase a branch, decide you hate the result, and run
`git reset --hard ORIG_HEAD` (or find the `rebase (start)` line in the reflog and reset to the
entry just before it).

**How it breaks**

| Symptom | First command | Note |
|---|---|---|
| Reflog does not show the commit | `git fsck --lost-found` | then `git show SHA` for each dangling commit |
| Work was lost on a server clone, not yours | run `git reflog` **on that clone** | reflogs are per clone |
| `git gc --prune=now` was run | nothing to do | that is why you never run prune commands during a rescue |

**Why it matters for troubleshooting.** It turns "I destroyed the hotfix" from a disaster into a
two-minute recovery, and it lets you experiment boldly (rebases, resets) in your own repos.

**Next step:** tags, which give commits stable human names for releases and rollbacks.

### Tags and releases

**Level:** [L1 · Junior]

**Concept.** A **tag** is a ref meant to never move. **Annotated** tags (`git tag -a`) are real
objects with a tagger, date and message (and can be signed); **lightweight** tags are bare
pointers. Use annotated tags for releases. In your pipeline, a tag such as `v1.4.2` is what
triggers a production release, and the same name labels the Harbor image, so "which code is
running in production?" has a one-word answer.

**Key terms**

| Term | Meaning |
|---|---|
| Semantic version | `vMAJOR.MINOR.PATCH`: breaking change, new feature, fix |
| `git push origin v1.4.2` | tags are **not** pushed by a plain `git push` |
| `git push --follow-tags` | push commits plus annotated tags that point at them |
| `git describe --tags` | "nearest tag plus commits since", e.g. `v1.4.2-3-ga1b2c3d` |
| Protected tags | GitLab setting so only maintainers can create `v*` tags |

**See it on a real system**

```bash
git tag -l 'v1.*' --sort=-v:refname | head -5     # newest release tags first
git show v1.4.2 --stat | head -12                 # tag object, then the commit it points at
git describe --tags --always                      # what this checkout is, as a version string
```

```
v1.4.2
v1.4.1
v1.4.0
tag v1.4.2
Tagger: Ops Engineer <ops@example.com>
Date:   Sat Oct 3 09:12:44 2026 +0000

Release 1.4.2: healthcheck and gunicorn timeout fix

commit a1b2c3d4e5f60718293a4b5c6d7e8f9012345678 (tag: v1.4.2)
v1.4.2-3-g9d8c7b6
```

**Hands-on lab (test VM only)**

**Step 1 — Tag and push a release.** `git tag -a v0.1.0 -m "First release"`, then
`git push origin v0.1.0`. Check it exists remotely with `git ls-remote --tags origin`.

**Step 2 — Break it: move a published tag.** `git tag -f v0.1.0 HEAD` and `git push -f origin v0.1.0`.
In your colleague clone, `git fetch --tags` prints `! [rejected] v0.1.0 -> v0.1.0 (would clobber existing tag)`.
Two machines now disagree about what `v0.1.0` means, and a deploy of "v0.1.0" depends on where
it ran.

**Step 3 — Fix it.** Restore the tag to the original commit (find it in the colleague clone with
`git rev-parse v0.1.0`), and release the new code as `v0.1.1` instead. In GitLab, protect `v*`
tags so this cannot happen again; in Harbor, make release tags immutable.

**How it breaks**

| Symptom | First command | Fix |
|---|---|---|
| Tag pipeline never started | `git ls-remote --tags origin` | the tag was not pushed |
| `would clobber existing tag` | `git rev-parse TAG` on both sides | never move release tags; cut a new version |
| Deployed "v1.4.2" behaves differently on two hosts | compare image digests, not tags | a mutable tag was re-pushed |

**Why it matters for troubleshooting.** Rollback means "deploy the previous known-good version".
That is only reliable if versions are immutable: a Git tag that never moves, and a Harbor tag
that cannot be overwritten.

**Next step:** keeping files that must never be committed out of the repository.

### .gitignore and secrets in history

**Level:** [L0 · Fresher] for `.gitignore`, [L2 · Mid] for history rewriting

**Concept.** `.gitignore` tells Git which **untracked** files to ignore: build output, virtual
environments, `.env` files, Terraform state, editor junk. It does nothing for files that are
already tracked. And once a secret has been committed and pushed, deleting the file in a new
commit does not remove it: every clone and every fork still has the old snapshot. The only
real fix for a pushed secret is to **rotate it** (make the leaked value useless), and only
then, optionally, rewrite history.

**Key terms**

| Term | Meaning |
|---|---|
| `.gitignore` | per-repo ignore patterns; `!pattern` re-includes |
| `.git/info/exclude` | local-only ignore patterns, not shared |
| `core.excludesFile` | your global ignore file (editor and OS junk) |
| `git check-ignore -v FILE` | which pattern (file and line) ignores FILE |
| `git rm --cached FILE` | stop tracking a file but keep it on disk |
| gitleaks | scanner for secrets in files and history; run it in CI and before pushing |

A good starting `.gitignore` for an infrastructure repository:

```
# Terraform: state and *.tfvars hold secrets (commit a terraform.tfvars.example instead)
*.tfstate
*.tfstate.*
.terraform/
crash.log
*.tfvars
# Ansible
*.retry
.vault-pass*
# Python and editors
__pycache__/
.venv/
.env
*.swp
.idea/
.vscode/
```

Comments in `.gitignore` must sit on their own line: text after a pattern (`*.tfvars  # note`)
becomes part of the pattern, and the rule silently stops matching.

**See it on a real system**

```bash
git check-ignore -v .env terraform.tfstate     # which rule ignores each file
git ls-files | grep -Ei '\.env$|tfstate|id_rsa|\.pem$'   # sensitive-looking files that ARE tracked
git log --all --oneline -- .env                # every commit that ever touched .env
```

```
.gitignore:13:.env	.env
.gitignore:2:*.tfstate	terraform.tfstate
f00ba12 Add local env for testing
```

→ `.env` is ignored **now**, but `git log --all -- .env` shows it was committed in `f00ba12`.
Its contents are in history. Treat every value in it as leaked.

**Hands-on lab (test VM only)**

**Step 1 — Leak a fake secret.** In a throwaway repo, `echo 'DB_PASSWORD=lab-not-real-123' > .env`,
commit and push to `~/lab/remote.git`. Then add `.env` to `.gitignore`, `git rm --cached .env`
and commit. Clone the remote fresh and run `git log -p --all -- .env`: the password is still there.

**Step 2 — Detect it.** Install gitleaks on the lab VM and scan the history (`gitleaks git .`
in gitleaks 8.19+, `gitleaks detect --source .` in older releases). A generic rule should report
the commit and line; add a custom rule to `.gitleaks.toml` if it does not.

**Step 3 — Fix it properly, in this order.** (1) **Rotate**: in real life, change the password
in the database and everywhere it is used. (2) Rewrite history only if policy requires it,
with `git filter-repo --path .env --invert-paths` on a fresh mirror clone, force-push, and tell
everyone to re-clone. (3) Prevent: add a gitleaks job to the pipeline and a pre-commit hook.

> ⚠️ History rewriting changes every SHA after the leak, breaks every open MR and every clone, and
> GitLab may still hold the old objects (MR diffs, pipeline refs) until housekeeping runs.
> It is never a substitute for rotation. Section 6 has the full leaked-secret procedure.

**How it breaks**

| Symptom | First command | Fix |
|---|---|---|
| A file still shows in `git status` despite `.gitignore` | `git ls-files FILE` | it is tracked: `git rm --cached FILE` |
| An ignored file you needed is missing on the server | `git check-ignore -v FILE` | ship it via config management or a secret store, not Git |
| `terraform.tfstate` found in the repo | `git log --all -- '*.tfstate'` | rotate everything in it, move state to a remote backend |

**Why it matters for troubleshooting.** Leaked credentials are both a security incident and an
outage source (rotation under pressure breaks things). Knowing what `.gitignore` can and cannot
do keeps you from a false sense of safety.

**Next step:** signed commits, so GitLab can prove who made a change.

### Signed commits

**Level:** [L1 · Junior] to use, [L3 · Senior] to enforce

**Concept.** Anyone can set `user.name` and `user.email` to anything, so the author line of a
commit proves nothing. A **signed** commit carries a cryptographic signature made with your
private key; GitLab verifies it against the public key on your profile and shows a **Verified**
badge. Since git 2.34 you can sign with your existing **SSH key**, which is far simpler than
GPG. Signing matters most for infrastructure repositories, where a commit can change firewalls
or production deploys.

**Key terms**

| Term | Meaning |
|---|---|
| `gpg.format ssh` | sign with an SSH key instead of GPG |
| `user.signingkey` | the public key (file path) used to sign |
| `commit.gpgsign true` | sign every commit automatically |
| allowed signers file | local list of trusted keys, needed for `git log --show-signature` to verify SSH signatures |
| Signing key in GitLab | an SSH key added with usage type "Signing" (or "Authentication & Signing") |

**See it on a real system**

```bash
git config --global gpg.format ssh
git config --global user.signingkey ~/.ssh/id_ed25519.pub
git config --global commit.gpgsign true
git config --global tag.gpgSign true
# let git verify SSH signatures locally
mkdir -p ~/.config/git
echo "ops@example.com $(cat ~/.ssh/id_ed25519.pub)" >> ~/.config/git/allowed_signers
git config --global gpg.ssh.allowedSignersFile ~/.config/git/allowed_signers
git commit --allow-empty -m "Signed test commit"
git log --show-signature -1
```

```
commit 3e2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d (HEAD -> main)
Good "git" signature for ops@example.com with ED25519 key SHA256:kq3V9mXc0yZ8l7r2Qe1Jt5uWfA4bH6dN0sP3gT9vY2E
Author: Ops Engineer <ops@example.com>
```

→ "Good signature" locally. In GitLab the commit shows **Verified** only if the same public key
is on your profile with signing enabled **and** the commit email is a verified email of your
GitLab account.

**Hands-on lab (test VM only)**

**Step 1 — Sign** as above and push to your lab GitLab or gitlab.com project. Check the badge.

**Step 2 — Break it.** Change `user.email` to an address not on your GitLab profile, make a new
signed commit and push. GitLab shows **Unverified** even though the signature is valid.

**Step 3 — Fix it** by committing with your verified email (`git commit --amend --reset-author`
for the last local commit after correcting `user.email`). Optionally enable the push rule
"Reject unsigned commits" (a paid GitLab tier feature) on the infrastructure repository.

**How it breaks**

| Symptom / error text | First command | Fix |
|---|---|---|
| `error: Load key ...: invalid format` / `fatal: failed to write commit object` | `git config --get user.signingkey` | point at the `.pub` file, or load the key into ssh-agent |
| `No signature` in `git log --show-signature` | `git config --get commit.gpgsign` | enable signing, re-sign with `git commit --amend -S --no-edit` |
| `gpg.ssh.allowedSignersFile needs to be configured` | add the file as above | local verification only; GitLab does not need it |

**Why it matters for troubleshooting.** During a security incident ("who changed the firewall
rule?"), signed commits plus protected branches give an audit trail you can trust.

**Next step:** put branches, MRs, tags and protections together into a team workflow.

### A team branching workflow

**Level:** [L1 · Junior] to follow, [L3 · Senior] to design

**Concept.** A branching workflow is a team agreement about how a change travels from an idea
to production. For a small ops/platform team using GitLab, the simplest workflow that works is
**trunk-based with short-lived branches and merge requests** (close to what GitLab calls
GitLab Flow):

```
  issue / change request #42
        │
        ▼
  git switch -c 42-traefik-timeouts main         (branch named after the issue)
        │  small commits, pushed early
        ▼
  merge request ──► pipeline: lint, test, build, plan/check  ──► review + approval
        │
        ▼  squash-merge into main (protected: nobody pushes directly)
  main ──► pipeline: build image SHA, deploy to staging automatically
        │
        ▼  git tag -a v1.5.0  (protected tag, maintainers only)
  tag pipeline ──► promote the same image ──► manual "deploy production" job
        │
        ▼  if bad: revert on main (or redeploy previous tag) ──► pipeline ships the undo
```

Rules that make it work:

- **`main` is always deployable** and protected: "Allowed to push: No one", "Allowed to merge: Maintainers", pipelines must succeed before merge.
- **Branches live hours to two days.** Long-lived branches are where painful conflicts come from.
- **One logical change per MR**, linked to an issue or change request. Infrastructure MRs show the plan output (`terraform plan`, `ansible --check --diff`) in the pipeline.
- **Build once, promote the artifact.** The image built from commit `a1b2c3d4` on `main` is the one that goes to production; production never rebuilds.
- **Hotfixes** also go through `main` (branch, MR, merge, tag). Emergency changes still get an MR, even if it is approved after the fact.
- **Commit messages say why**, not only what: `Raise Traefik read timeout to 120s: report export takes 90s (INC-2026-014)`.

**Key terms**

| Term | Meaning |
|---|---|
| Merge request (MR) | GitLab's pull request: review, discussion, pipeline results, approvals |
| Protected branch / tag | GitLab settings restricting who can push, merge or create |
| CODEOWNERS | file mapping paths to owners; a Premium/Ultimate feature: owners are shown on MRs and can be made required approvers on protected branches (ignored on the Free tier) |
| Draft MR | an MR marked not ready; cannot be merged |
| Squash commit | the MR's commits combined into one on `main` |

**See it on a real system**

```bash
git log --oneline --first-parent main -10     # main's history only, one line per merged MR
git log --oneline main..BRANCH                 # what a branch would add to main
git branch -r --merged origin/main             # remote branches already merged (safe to delete)
```

**Hands-on lab (test VM only)**

**Step 1 — Protect `main`** in your lab GitLab project (Settings → Repository → Protected
branches) and enable "Pipelines must succeed" (Settings → Merge requests).

**Step 2 — Break it: push straight to `main`.** You get
`remote: GitLab: You are not allowed to push code to protected branches on this project.`
Then open an MR whose pipeline fails (introduce a YAML syntax error) and try to merge: the
button is disabled.

**Step 3 — Fix it the workflow way.** Push the fix to the same branch, let the pipeline pass,
merge with squash, tag a release, and watch the tag pipeline. Write the workflow above into
your team's `CONTRIBUTING.md` so the next person does not have to guess.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Huge, painful conflicts | `git log --oneline main...BRANCH | wc -l` | branch lived for weeks; merge main in daily or split the work |
| "Works on staging, broken in prod" | compare image digests per environment | prod rebuilt from source instead of promoting the tested image |
| Nobody knows what is deployed | `git describe --tags` on the deployed SHA | no tags, or tags not tied to images |

**Why it matters for troubleshooting.** With this workflow, "what changed?" always has an answer:
one MR, one squash commit, one image tag, one pipeline, one deployment record in GitLab's
environment history. That chain is what you follow in the first five minutes of an incident.

**Next step:** section 2, where the pipeline in this diagram is built for real.

---

## 2. GitLab CI/CD

> 📚 **Study path:** 1) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Architecture & Core Concepts → Continuous Integration with GitLab (Docker build/test/push) → Self-Managed Runners (Docker executor) → Continuous Deployment ([course](https://kodekloud.com/courses/gitlab-ci-cd)); lesson notes: [Types of Executors](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Architecture-Core-Concepts/Types-of-Executors/page), [Docker Push](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Continuous-Integration-with-GitLab/Docker-Push/page), [Install Group Runner with Docker Executor](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Self-Managed-Runners/Install-Group-Runner-on-Linux-Machine-with-Docker-Executor/page) · 2) Note: this section, then GitLab's [CI quick start](https://docs.gitlab.com/ci/quick_start/) and [Use Docker to build Docker images](https://docs.gitlab.com/ci/docker/using_docker_build/) · 3) Video: TechWorld with Nana *GitLab CI CD Tutorial for Beginners [Crash Course]* ([YouTube](https://www.youtube.com/watch?v=qP8kir2GUgo)) · 4) Practice: KodeKloud [CI/CD playground](https://kodekloud.com/playgrounds/playground-ci-cd), then the Ops Ladder drill in this section: build, tag with the commit SHA, push to Harbor.

A pipeline is the automated, repeatable version of what you did by hand during the Apache to
Dokploy migration: check the config, build the thing, put it somewhere safe, deploy it, prove it
works, and know how to undo it. This section builds that pipeline piece by piece for the
`shop-web` app, ending with a complete `.gitlab-ci.yml` that pushes to Harbor with the commit
SHA, deploys to Dokploy (staging) and Kubernetes (production), and has a tested rollback job.
Then it teaches you how to debug a red pipeline step by step.

```
  git push / MR / tag
        │
        ▼
  GitLab (gitlab.example.com) ── evaluates .gitlab-ci.yml + rules ──► pipeline with jobs
        │                                                           (pending)
        │   runners poll GitLab every few seconds: "any job for me?"
        ▼
  runner01 (gitlab-runner service) ── executor: docker ──► one fresh container per job
        │                                                  clones the repo at the commit SHA
        │                                                  runs script: lines, uploads log
        ▼                                                  and artifacts back to GitLab
  harbor.example.com/shop/shop-web:9d8c7b6a  ──►  Dokploy (staging)  ──►  Kubernetes (production)
```

### Pipeline anatomy

**Level:** [L1 · Junior] to read, [L3 · Senior] to design

**Concept.** A pipeline is defined by one file in the repository root, `.gitlab-ci.yml`. Every
push, merge request or tag makes GitLab read that file **at that commit** and create a pipeline.
A pipeline is made of **jobs** (named units of work, each with a `script`), grouped into
**stages** that run in order. Jobs in the same stage run in parallel; the next stage starts when
the previous one succeeds (unless `needs:` says otherwise). Each job runs on a **runner**, in a
fresh environment, starting from a clean checkout of the commit. Nothing carries over between
jobs unless you pass it explicitly (artifacts) or speed it up (cache).

```
 stages:   lint ──────────► test ─────────► build ─────────► deploy
 jobs:     yaml-check        unit-tests      build-image      deploy-staging
           conflict-check    compose-check                   deploy-production (manual)
           (parallel)        (parallel)
 a job fails ──► later stages do not start ──► pipeline "failed" ──► MR cannot merge
```

A minimal but real `.gitlab-ci.yml`:

```yaml
stages: [lint, test, build]

variables:                       # available to every job
  IMAGE: harbor.example.com/shop/shop-web

default:                         # defaults every job inherits
  image: python:3.12-slim
  interruptible: true            # a newer pipeline on the same branch cancels this one

yaml-check:
  stage: lint
  script:
    - pip install --quiet yamllint
    - yamllint -d relaxed .gitlab-ci.yml compose.yml

unit-tests:
  stage: test
  script:
    - pip install --quiet -r requirements.txt pytest
    - pytest -q

build-image:
  stage: build
  image: docker:27
  services: [docker:27-dind]          # simplified: TLS variables, DNS and the CA are in "Building images"
  script:
    - docker build -t "$IMAGE:$CI_COMMIT_SHORT_SHA" .
```

**Key terms**

| Term | Meaning |
|---|---|
| Pipeline | one run of `.gitlab-ci.yml` for one commit, triggered by a push, MR, tag, schedule, API or manual run |
| Stage | an ordered group; all jobs of stage N normally finish before stage N+1 starts |
| Job | a named set of `script:` commands run by one runner in one fresh environment |
| `image:` | the container image the job runs in (Docker and Kubernetes executors) |
| `services:` | extra containers started next to the job, reachable by hostname (for example `docker:27-dind` as `docker`) |
| `before_script` / `after_script` | commands before the script / always after it, even on failure (in a separate shell) |
| `default:` | settings every job inherits unless it overrides them |
| `include:` | pull YAML from other files, projects or templates (`include: local:`, `project:`, `template:`) |
| `extends:` / YAML anchors | reuse job definitions instead of copying them |
| Exit code | a script line that exits non-zero fails the job (the shell runs with `set -e` semantics per line) |

**See it on a real system.** The UI shows the same data, but the API is faster to grep and works
over SSH. Use a personal or project access token with `read_api` scope, sent in a header, never
in the URL:

```bash
export GITLAB=https://gitlab.example.com/api/v4
export PROJECT_ID=42                        # Settings → General shows the project ID
# the last three pipelines: id, status, ref, short SHA
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$GITLAB/projects/$PROJECT_ID/pipelines?per_page=3" \
  | jq -r '.[] | "\(.id)  \(.status)  \(.ref)  \(.sha[0:8])"'
# the jobs of one pipeline: stage, name, status, runner
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$GITLAB/projects/$PROJECT_ID/pipelines/4812/jobs" \
  | jq -r '.[] | "\(.stage)\t\(.name)\t\(.status)\t\(.runner.description // "-")"'
```

```
4812  failed   main             9d8c7b6a
4811  success  feature/healthz  a1b2c3d4
4810  success  main             4e1d0c9b
build	build-image	failed	runner01-docker
test	unit-tests	success	runner01-docker
lint	yaml-check	success	runner01-docker
```

→ Pipeline 4812 on `main` failed in the **build** stage; lint and test passed. That already tells
you the code and config are syntactically fine and the problem is in building or pushing the
image. The GitLab CLI (`glab ci status`, `glab ci view`, `glab ci lint`) gives the same view if
your team installs it.

**Hands-on lab (test VM only)**

**Step 1 — First pipeline.** In a lab project, commit the minimal file above without the
`build-image` job. Watch it in Build → Pipelines. Open each job log and find the lines
`Running with gitlab-runner`, `Preparing the "docker" executor`, `Getting source from Git
repository`, `Executing "step_script" stage` and `Job succeeded`. Those five phases are where
every failure will later be located.

**Step 2 — Break it.** Indent `script:` of `unit-tests` by one space less than `stage:` and push.
The pipeline does not run at all; GitLab shows a "yaml invalid" badge. Then fix the YAML but add
`exit 3` as the last script line: now the pipeline runs and the job fails with
`ERROR: Job failed: exit code 3`.

**Step 3 — Fix it and learn the tool.** Open Build → Pipeline editor, paste the broken YAML and
use **Validate** and the **Full configuration** tab (the merged YAML after `include:` and
`extends:`). Fix, commit, confirm green.

**How it breaks**

| Symptom / error text | First command | Where to read more |
|---|---|---|
| Pipeline fails at once with no jobs, "yaml invalid" badge | Pipeline editor → Validate | Step 3 of "Debugging failed pipelines" below |
| `jobs:unit-tests config should implement the script:, run:, or trigger: keyword` (older GitLab: `... a script: or a trigger: keyword`) | look at indentation of the job | YAML nesting is off by one level |
| `ERROR: Job failed: exit code 1` | read the log **above** that line | Step 6 below |
| Pipeline runs twice for one push (branch + MR) | check `workflow: rules` | next topic |

**Why it matters for troubleshooting.** Every red pipeline is a layered problem, like a site
being down: config (did GitLab understand the YAML?), scheduling (did a runner pick it up?),
environment (did the executor start the image?), and finally your script. Knowing the anatomy
tells you which layer the error text belongs to.

**Next step:** control *when* each job runs, which is what `rules` and `needs` do.

### Rules, needs and the DAG

**Level:** [L3 · Senior] ([L2 · Mid] to debug "why did my job not run?")

**Concept.** `rules:` decide **whether** a job is added to a pipeline and **how** (`on_success`,
`manual`, `delayed`, `never`). GitLab evaluates the rules top to bottom when the pipeline is
created; the first rule that matches wins; if none matches, the job is not added. `workflow:
rules` does the same for the whole pipeline. `needs:` decides **what a job waits for**: instead of
waiting for the whole previous stage, a job starts as soon as the jobs it needs are done. That
turns stages into a directed acyclic graph (DAG) and can cut pipeline time in half.

```
 without needs:   lint-a ─┐                 with needs:   lint-a ──► test-a ──► build-a
                  lint-b ─┴─► test-a ─┐                    lint-b ──► test-b
                              test-b ─┴─► build-a          (build-a starts as soon as test-a is done,
                                                             it does not wait for test-b)
```

The rules you will use in almost every pipeline:

```yaml
workflow:                                  # one pipeline per change, not two
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS
      when: never                          # branch push with an open MR: the MR pipeline covers it
    - if: $CI_COMMIT_BRANCH
    - if: $CI_COMMIT_TAG

deploy-staging:
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH       # only main

deploy-production:
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/          # only release tags
      when: manual                                     # a human clicks; blocks the pipeline until then

terraform-plan:
  rules:
    - changes: [terraform/**/*]                        # only when IaC files changed
```

**Key terms**

| Term | Meaning |
|---|---|
| `rules: if:` | a condition on CI variables; regex with `=~`, `&&`, `||`, parentheses |
| `rules: changes:` | add the job only if listed paths changed (compared to the MR target or the previous push) |
| `rules: exists:` | add the job only if a file exists in the repo |
| `when: never` | explicitly exclude |
| `needs: [job]` | start after `job`, ignoring stage order; also limits which artifacts are downloaded |
| `needs: []` | start immediately when the pipeline starts |
| `only` / `except` | the older syntax; still works, but do not mix it with `rules` in one job |
| `CI_PIPELINE_SOURCE` | `push`, `merge_request_event`, `schedule`, `web`, `api`, `trigger`, `parent_pipeline` |

**See it on a real system.** "Why did my job not run?" is answered by the variables GitLab saw.
Add a throwaway debug job (never echo secrets; these variables are not secret):

```yaml
debug-rules:
  stage: lint
  script:
    - echo "source=$CI_PIPELINE_SOURCE branch=${CI_COMMIT_BRANCH:-none} tag=${CI_COMMIT_TAG:-none} default=$CI_DEFAULT_BRANCH"
```

```
source=merge_request_event branch=none tag=none default=main
```

→ In a merge request pipeline `CI_COMMIT_BRANCH` is **not set** (the branch is in
`CI_MERGE_REQUEST_SOURCE_BRANCH_NAME` instead). A rule `if: $CI_COMMIT_BRANCH == "main"` can
therefore never match in an MR pipeline. That single fact explains a large share of "my job
silently disappeared" questions.

**Hands-on lab (test VM only)**

**Step 1 — Build a DAG.** Give `unit-tests` `needs: [yaml-check]` and add a slow job
`integration-tests` with `script: sleep 60` in the test stage. Add `build-image` with
`needs: [unit-tests]`. In the pipeline graph (Job dependencies view), `build-image` starts while
`integration-tests` is still sleeping.

**Step 2 — Break it.** Change `deploy-staging` to `if: $CI_COMMIT_BRANCH == "master"` (the old
default branch name) and merge an MR. The job never appears and nothing errors. Also add a job with
both `only: [main]` and `rules:` and watch the "yaml invalid" error
(`jobs:JOB config key may not be used with rules: only`).

**Step 3 — Fix it.** Use `$CI_DEFAULT_BRANCH` instead of a hard-coded name, remove `only`, and
confirm with the debug job.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Job missing from the pipeline, no error | debug job printing the variables | no rule matched (MR vs branch variables, wrong branch name, regex) |
| Two pipelines per push ("detached" MR pipeline plus branch pipeline) | look at the pipeline sources | no `workflow: rules` |
| `rules: changes` job runs on every tag or schedule | read the docs note on `changes` | without a comparison base, `changes` evaluates to true |
| `job needs another job that does not exist in the pipeline` | check the needed job's rules | the needed job was excluded by its own rules; use `needs: [{job: X, optional: true}]` |

**Why it matters for troubleshooting.** A production deploy that "did not happen" is often a rule
that did not match. A deploy that happened when it should not have is a rule that matched too
broadly. Rules are code: review them like code.

**Next step:** the data a job works with, which is variables and secrets.

### Variables: predefined, masked, protected

**Level:** [L2 · Mid] to use, [L3 · Senior] to design the secret flow

**Concept.** Jobs get configuration through **CI/CD variables**. Three kinds: **predefined**
variables GitLab sets for every job (`CI_COMMIT_SHORT_SHA`, `CI_COMMIT_TAG`, `CI_PROJECT_PATH`,
`CI_JOB_TOKEN`...), variables you write in `.gitlab-ci.yml` (not secret, they are in Git), and
variables stored in **Settings → CI/CD → Variables** at project, group or instance level (the
place for secrets). Stored variables have flags that matter for security:

| Flag | What it does | Use it for |
|---|---|---|
| **Masked** | the value is replaced by `[MASKED]` in job logs (value must be one line, at least 8 characters, limited character set) | every token and password |
| **Masked and hidden** | masked, and the value can no longer be revealed in the UI after saving (GitLab 17.4+) | long-lived high-value secrets |
| **Protected** | only exposed to pipelines on **protected** branches and tags | production credentials (Harbor push, Dokploy, kubeconfig) |
| **Expand variable reference** | `$NAME` inside the value is expanded | turn **off** for values containing `$`, such as Harbor robot names |
| **Type: File** | GitLab writes the value to a temp file and the variable holds the **path** | kubeconfig, CA certificates, SSH keys |
| **Environment scope** | only exposed to jobs with a matching `environment:` | different kubeconfigs for staging and production |

Precedence, highest first (simplified): manual-run or trigger variables → project variables →
group variables → instance variables → variables in `.gitlab-ci.yml` (job level over global) →
predefined variables.

**Key terms**

| Term | Meaning |
|---|---|
| `CI_COMMIT_SHA` / `CI_COMMIT_SHORT_SHA` | the full / 8-character commit hash; use the short one as image tag |
| `CI_COMMIT_REF_SLUG` | branch or tag name made safe for URLs and tags (`feature/healthz` → `feature-healthz`) |
| `CI_DEFAULT_BRANCH` | usually `main` |
| `CI_JOB_TOKEN` | short-lived token of this job; can call some GitLab APIs and clone allowed projects |
| `CI_REGISTRY_IMAGE` | the project's GitLab container registry path (you use Harbor instead) |
| `CI_ENVIRONMENT_NAME` | set for jobs with `environment:` |

**See it on a real system.** Print the **names** of variables, never their values:

```yaml
list-vars:
  script:
    - env | cut -d= -f1 | grep -E '^(CI_|HARBOR_|DOKPLOY_|KUBECONFIG)' | sort
```

```
CI_COMMIT_REF_SLUG
CI_COMMIT_SHA
CI_COMMIT_SHORT_SHA
CI_DEFAULT_BRANCH
CI_JOB_TOKEN
...
HARBOR_PASSWORD
HARBOR_USER
```

→ On a feature branch, `HARBOR_PASSWORD` would be **missing** from this list if it is protected:
the variable exists in the settings but this pipeline is not allowed to see it. That is the
designed behaviour, not a bug.

**Hands-on lab (test VM only)**

**Step 1 — Store a robot credential.** In your lab Harbor, create a robot account in project
`shop` with push and pull permission. Harbor names it like `robot$shop+gitlab-ci`. In GitLab add
`HARBOR_USER` (not masked, **Expand variable reference off**) and `HARBOR_PASSWORD` (masked,
protected).

**Step 2 — Break it, twice.** First, leave "Expand variable reference" **on** for `HARBOR_USER` and
run a `docker login` job on `main`: the `$shop` part is expanded to an empty string, the user
becomes `robot+gitlab-ci`, and Harbor answers `unauthorized: authentication required`. Second,
fix that and run the same job on an unprotected feature branch: `HARBOR_PASSWORD` is empty and
`docker login` prompts or fails with `Error: Cannot perform an interactive login from a non TTY
device`.

**Step 3 — Fix it.** Turn expansion off, and decide on purpose: either protect the feature branch
pattern that needs pushes (rarely right), or push only from `main` and tags (right). Feature
branches build the image without pushing, or push to a separate unprotected "dev" robot with
pull-only access to production projects.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| Variable is empty in the job | the `list-vars` job above (names only) | protected variable on an unprotected ref, or environment scope mismatch |
| `unauthorized: authentication required` with a robot account | check the "Expand variable reference" flag | `$` in the robot name was expanded |
| Secret visible in a job log | rotate it now, then mask it | not masked, or printed in a transformed form (base64, URL-encoded) that masking cannot recognise |
| "Unable to create masked variable because: The value must..." | check the value | masking needs one line, 8+ characters, a limited character set; store multi-line secrets as File type |

**Why it matters for troubleshooting.** "Works on main, fails on my branch" and "works for me, not
in CI" are usually variable visibility problems. Check scope and protection before you debug the
script.

**Next step:** where the job actually runs: runners and executors.

### Runners and executors

**Level:** [L2 · Mid] to debug, [L3 · Senior] to choose and operate

**Concept.** A **runner** is the `gitlab-runner` program on one of your machines. It polls GitLab
over HTTPS ("do you have a job for me?"), so GitLab never needs to reach the runner: only
outbound 443 from the runner to GitLab is required. The **executor** decides how a job runs on
that machine:

| Executor | How a job runs | Good for | Watch out for |
|---|---|---|---|
| `shell` | directly as the `gitlab-runner` user on the host | Ansible against your servers, quick on-prem deploys | jobs share the host: leftovers, installed tools drift, one job can break the next |
| `docker` | in a fresh container from `image:`, with `services:` as sibling containers | almost everything: builds, tests, image pushes | DinD needs `privileged = true`; mounting `/var/run/docker.sock` gives jobs root on the host |
| `kubernetes` | a pod per job in a namespace | teams already on Kubernetes; autoscaling | needs RBAC, resource limits, image pull secrets for Harbor |
| `docker-autoscaler` / `instance` | VMs created on demand (cloud autoscaling) | large or bursty workloads | more moving parts; replaces the deprecated docker+machine |
| `ssh`, `virtualbox`, `custom` | rare | special cases | not for your setup |

Runner **scope**: instance runners (any project), group runners (all projects of a group),
project runners (one project). **Tags** connect jobs and runners: a job with `tags: [docker]`
only runs on runners with that tag. A runner can be **protected**: it only runs jobs from
protected branches and tags, which is how you keep production credentials and deploy access on a
dedicated machine.

```
 runner01 (192.168.56.21)                            gitlab.example.com
 ┌─────────────────────────────────────┐   HTTPS     ┌──────────────────┐
 │ gitlab-runner (systemd service)     │ ──poll────► │ job queue        │
 │  config: /etc/gitlab-runner/        │ ◄──job───── │                  │
 │          config.toml                │ ──log/art─► │                  │
 │  executor docker ──► dockerd        │             └──────────────────┘
 │    ├─ helper container (git clone, artifacts, cache)
 │    ├─ job container   (image: python:3.12-slim, your script)
 │    └─ service container (docker:27-dind, alias "docker")
 └─────────────────────────────────────┘
```

**Key terms**

| Term | Meaning |
|---|---|
| `concurrent` | global limit of jobs running at once on this runner process |
| `limit` | per-runner-entry limit |
| `check_interval` | how often the runner polls (default 3 s) |
| Helper image | `gitlab-runner-helper`, does clone, cache and artifact transfer |
| `privileged` | lets job and service containers run privileged; required for DinD |
| Run untagged jobs | whether this runner picks up jobs without `tags:` |

**See it on a real system** (on the runner host):

```bash
sudo gitlab-runner --version | head -3
sudo gitlab-runner list                     # runners configured in config.toml
sudo gitlab-runner verify                   # can each one authenticate to GitLab?
systemctl status gitlab-runner --no-pager | head -5
sudo journalctl -u gitlab-runner --since "1 hour ago" --no-pager | tail -20
sudo grep -vE 'token' /etc/gitlab-runner/config.toml      # read the config without printing tokens
```

```
Version:      17.11.0
Git revision: 0f7d7b4a
Git branch:   17-11-stable
Runtime platform    arch=amd64 os=linux pid=4120 revision=0f7d7b4a version=17.11.0
Listing configured runners    ConfigFile=/etc/gitlab-runner/config.toml
runner01-docker     Executor=docker Token=glrt-t1_XXXXXXXX URL=https://gitlab.example.com
Verifying runner... is valid    runner=t1_XXXXXX
● gitlab-runner.service - GitLab Runner
     Active: active (running) since Sat 2026-10-03 07:58:12 UTC; 1h 14min ago
Oct 03 09:10:02 runner01 gitlab-runner[4120]: Checking for jobs... received   job=91234 repo_url=https://gitlab.example.com/shop/shop-web.git runner=t1_XXXXXX
Oct 03 09:11:40 runner01 gitlab-runner[4120]: Job succeeded   duration_s=98.2 job=91234 project=42 runner=t1_XXXXXX
concurrent = 4
check_interval = 0
[[runners]]
  name = "runner01-docker"
  url = "https://gitlab.example.com"
  executor = "docker"
  [runners.docker]
    image = "alpine:3.20"
    privileged = true
    volumes = ["/certs/client", "/cache", "/etc/docker/certs.d:/etc/docker/certs.d:ro"]
    dns = ["192.0.2.53", "192.0.2.54"]
```

→ `is valid` means the token works and GitLab is reachable through TLS. `Checking for jobs...
received` proves the runner is actually picking up work. `concurrent = 4` caps parallel jobs on
this host; if pipelines queue for minutes while the runner is idle at 4 jobs, that is the limit.
The `dns` line gives every job container your internal resolvers, and the `volumes` line shares
`/etc/docker/certs.d` (your Harbor CA) with job **and** service containers, which is what DinD
needs to trust Harbor.

> ⚠️ Mounting `/var/run/docker.sock` into jobs ("socket binding") is a common shortcut instead of
> DinD. It gives every job full root control of the runner host and of every container on it,
> including other jobs. Only acceptable on a runner dedicated to one trusted project. Prefer DinD
> on a dedicated runner VM, or a rootless builder (buildah).

**Hands-on lab (test VM only)**

**Step 1 — Install and register** a runner on `runner01` (next topic).

**Step 2 — Break it.** Give the runner the tag `docker` and turn off "Run untagged jobs", then push
a pipeline whose jobs have no `tags:`. Jobs stay **pending** with "This job is stuck because you
don't have any active runners that can run this job". Then stop the service
(`sudo systemctl stop gitlab-runner`) and watch the runner turn grey ("offline") in
Settings → CI/CD → Runners after a few minutes.

**Step 3 — Fix it.** Start the service, then either add `tags: [docker]` via `default:` in the YAML
or allow untagged jobs. Write down which one your team standard should be, and why.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `This job is stuck because the project doesn't have any runners online assigned to it` | `sudo gitlab-runner verify` | runner offline, paused, or not assigned to the project |
| Stuck only for some jobs | compare job `tags:` with runner tags | tag mismatch, or protected runner and unprotected branch |
| Jobs queue for minutes, runner idle otherwise | `grep concurrent /etc/gitlab-runner/config.toml` | `concurrent`/`limit` too low |
| `ERROR: Job failed (system failure): Error response from daemon: ... no space left on device` | `df -h /var/lib/docker` on the runner | images, volumes and build cache piling up (see [Docker learn module](30-learn-docker.md)) |
| `x509: certificate signed by unknown authority` in the runner journal | `openssl s_client -connect gitlab.example.com:443 -showcerts` | GitLab's CA not in `/etc/gitlab-runner/certs/` (see the trust map in section 0) |

**Why it matters for troubleshooting.** "Pending" and "stuck" are scheduling problems, not script
problems: no amount of editing the script will help. Knowing the runner model sends you to the
right machine first.

**Next step:** install and register a runner yourself.

### Registering a runner

**Level:** [L3 · Senior]

**Concept.** Since GitLab 16, runners are **created in the GitLab UI first** (Settings → CI/CD →
Runners → New project runner, or the group or admin area). You set tags, "run untagged",
protected and the maximum timeout there, and GitLab shows a **runner authentication token**
starting with `glrt-`. On the runner host you then run `gitlab-runner register` with that token.
The old method with a shared **registration token** is deprecated; do not build new automation on
it.

**Key terms**

| Term | Meaning |
|---|---|
| Runner authentication token (`glrt-...`) | identifies one runner; stored in `config.toml`; treat as a secret |
| `config.toml` | `/etc/gitlab-runner/config.toml` when running as root/service |
| `/etc/gitlab-runner/certs/HOST.crt` | CA certificate the runner uses to trust `HOST` (your private CA) |
| `gitlab-runner unregister` | removes a runner entry from `config.toml`; for a runner created in the UI (`glrt-` token) it deletes only the runner manager, so delete the runner itself in the UI or with the Runners API |

**See it on a real system.** Installing and registering, Ubuntu (lab runner VM only):

```bash
# 1) install from GitLab's package repository (read the script before piping it to bash)
curl -fsSL -o /tmp/runner-repo.sh https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh
less /tmp/runner-repo.sh && sudo bash /tmp/runner-repo.sh
sudo apt-get install -y gitlab-runner
# 2) trust your private CA for GitLab (file name must be the GitLab host name)
sudo install -d -m 0755 /etc/gitlab-runner/certs
sudo cp corp-root-ca.crt /etc/gitlab-runner/certs/gitlab.example.com.crt
# 3) register with the glrt- token copied from the UI (keep it out of shell history)
read -rs RUNNER_TOKEN
sudo gitlab-runner register --non-interactive \
  --url "https://gitlab.example.com" \
  --token "$RUNNER_TOKEN" \
  --executor "docker" \
  --docker-image "alpine:3.20" \
  --name "runner01-docker"
sudo gitlab-runner verify
```

```
Runtime platform    arch=amd64 os=linux pid=5521 revision=0f7d7b4a version=17.11.0
Running in system-mode.
Verifying runner... is valid    runner=t1_XXXXXX
Runner registered successfully. Feel free to start it, but if it's running already the config should be automatically reloaded!
Configuration (with the authentication token) was saved in "/etc/gitlab-runner/config.toml"
```

→ The runner is now in `config.toml` and the service reloads it automatically. Finish the config by
hand: set `privileged = true` (only if this runner builds images with DinD), the `dns` list, and the
`/etc/docker/certs.d` volume shown in the previous topic, then `sudo systemctl restart gitlab-runner`.

**Hands-on lab (test VM only)**

**Step 1 — Register** `runner01` to your lab project as above with tags `docker,build`.

**Step 2 — Break it.** Remove `/etc/gitlab-runner/certs/gitlab.example.com.crt` and restart the
service. The journal fills with `x509: certificate signed by unknown authority` and the runner
turns offline in the UI. Jobs that do start fail cloning with `server certificate verification
failed`.

**Step 3 — Fix it.** Restore the CA file, restart, `gitlab-runner verify`. Then automate the runner
install and CA file with Ansible (section 4) so the next runner is identical.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `ERROR: Verifying runner... is removed` | check the runner still exists in the UI | runner deleted in GitLab; register again |
| `403 Forbidden` (or `is not valid`) when registering or verifying | the token | wrong, revoked or copied with a trailing space; tokens are shown only once |
| `x509` during register or polling | `ls /etc/gitlab-runner/certs/` | CA missing or named after the wrong host |
| `dial tcp: lookup gitlab.example.com ... no such host` | `getent ahosts gitlab.example.com` on the runner host | runner host DNS; see [DNS reference](08-dns.md) |

**Why it matters for troubleshooting.** A runner is just a Linux service: every L1 skill applies
(`systemctl status`, `journalctl -u`, config file, CA trust, DNS). Most "GitLab CI is broken"
reports are "the runner host is broken".

**Next step:** what to keep between jobs, and how: artifacts and cache.

### Artifacts vs cache

**Level:** [L2 · Mid]

**Concept.** Jobs start clean. Two mechanisms move files between them, and they are **not**
interchangeable:

| | Artifacts | Cache |
|---|---|---|
| Purpose | pass **results** to later jobs and to humans (reports, binaries, `tfplan`) | **speed up** jobs by reusing downloads (pip, npm, Go modules) |
| Stored | on GitLab (uploaded by the runner) | on the runner host (`/cache` volume) or a shared S3/MinIO bucket |
| Guaranteed? | yes, within the pipeline (until `expire_in`) | **no**: best effort, may be missing, the job must work without it |
| Scope | this pipeline (and downloadable later) | across pipelines, keyed by `key:` |
| Typical keyword | `artifacts: paths: [...] expire_in: 1 week` | `cache: key: files: [requirements.txt] paths: [.cache/pip]` |

Rule of thumb: if the next job **needs** the file to be correct, it is an artifact. If it only
makes the job faster, it is a cache.

```yaml
unit-tests:
  variables:
    PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"   # cache paths must be inside the project dir
  cache:
    key:
      files: [requirements.txt]                  # new cache when dependencies change
    paths: [.cache/pip]
  script:
    - pip install -r requirements.txt pytest
    - pytest -q --junitxml=report.xml
  artifacts:
    when: always                                 # upload the report even when tests fail
    reports:
      junit: report.xml                          # shown in the MR widget
    expire_in: 1 week
```

**Key terms**

| Term | Meaning |
|---|---|
| `artifacts:reports:junit` | test results shown in MRs |
| `artifacts:expire_in` | how long GitLab keeps them; old artifacts fill GitLab's disk |
| `dependencies:` / `needs:` | which earlier jobs' artifacts a job downloads |
| `cache:policy: pull` | only download the cache, do not upload (for jobs that do not change it) |
| Distributed cache | runner `[runners.cache]` with S3/MinIO so several runners share caches |

**See it on a real system.** In a job log:

```
Restoring cache
Checking cache for 3f2a1b0c-protected...
No URL provided, cache will not be downloaded from shared cache server. Instead a local version of cache will be extracted.
Successfully extracted cache
...
Uploading artifacts for successful job
Uploading artifacts...
report.xml: found 1 matching artifact files and directories
Uploading artifacts as "junit" to coordinator... 201 Created  id=91235 responseStatus=201 Created
```

→ The cache key ends in `-protected`: GitLab keeps separate caches for protected and unprotected
refs so a feature branch cannot poison the cache that `main` uses. "No URL provided" means the
cache is local to this runner host; a job on another runner will start with an empty cache.

**Hands-on lab (test VM only)**

**Step 1 — Measure.** Run `unit-tests` twice without cache, then with the cache block. Note the
`pip install` time in both logs.

**Step 2 — Break it.** Make `build-image` depend on a file produced by `unit-tests` but put that file
in `cache:` instead of `artifacts:`. It works on runner01, then you register a second runner and it
fails randomly with "file not found" whenever the jobs land on different runners.

**Step 3 — Fix it.** Move the file to `artifacts:` and add `needs: [unit-tests]` to `build-image`.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| "File not found" only sometimes | check which runner ran each job | data passed via cache instead of artifacts |
| `WARNING: ...: no matching files` on upload | `ls` in the script before upload | path outside `$CI_PROJECT_DIR` or wrong relative path |
| GitLab disk filling up | Admin → Usage quotas / storage | artifacts without `expire_in`, huge build outputs |
| Cache never restored | compare `key:` between jobs | different keys, protected vs unprotected refs |

**Why it matters for troubleshooting.** Flaky pipelines that fail "randomly" are very often a cache
being treated as a guarantee. The fix is design, not retries.

**Next step:** the job that matters most for the L3 exit test: building the image.

### Building images: DinD, kaniko, buildah

**Level:** [L3 · Senior]

**Concept.** A CI job runs inside a container, but `docker build` needs a Docker daemon. There are
three common ways around that, and each has a security and a troubleshooting profile:

```
 1) Docker-in-Docker (DinD)               2) socket binding               3) daemonless builder
 job container ──TCP 2376/TLS──►          job container                   job container
   docker CLI      docker:27-dind           docker CLI ──► /var/run/        buildah / kaniko
                   (privileged, its own       docker.sock of the HOST       builds layers itself,
                   dockerd, own cache,        (= root on the runner host)   pushes directly;
                   own resolv.conf)                                         no daemon, no privilege*
```

| Method | Needs | Pros | Cons |
|---|---|---|---|
| DinD (`docker:27-dind` service) | `privileged = true` on the runner | isolated daemon per job, the normal `docker` commands | privileged containers; no layer cache between jobs unless you use `--cache-from`; DinD has its **own** DNS and CA trust |
| Socket binding | `/var/run/docker.sock` volume | fast, shared cache | every job is root on the host; jobs can see and kill each other's containers |
| buildah | unprivileged container, `vfs` or fuse-overlayfs storage | no daemon, rootless-friendly, OCI and Docker formats | slower with `vfs`; different CLI flags |
| kaniko | the `executor` image | no daemon, popular in Kubernetes runners | the upstream Google repository was archived in 2025; check the maintenance status of any fork before adopting (GitLab's docs now point kaniko users to rootless BuildKit or Buildah) |

For your on-prem stack the sensible default is **DinD on a dedicated build runner VM** (simple,
matches the KodeKloud course and the GitLab docs) or **buildah** if you want to avoid privileged
containers. Either way, pull CI images through a **Harbor proxy-cache project** (for example
`harbor.example.com/dockerhub-proxy/library/docker:27`) so builds do not depend on Docker Hub rate
limits or your Internet link.

The DinD job, with the two on-prem details people miss (internal DNS and the private CA):

```yaml
build-image:
  stage: build
  image: docker:27
  services:
    - name: docker:27-dind
      alias: docker
      command: ["--dns=192.0.2.53", "--dns=192.0.2.54"]   # RUN steps resolve via your DNS, not 8.8.8.8
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"           # dind generates TLS certs into the shared /certs volume
    DOCKER_TLS_VERIFY: "1"
    DOCKER_CERT_PATH: "/certs/client"
  before_script:
    - for i in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 1; done   # wait for dind
    - docker info --format 'dind {{.ServerVersion}}'                                  # proves the daemon answers
    - echo "$HARBOR_PASSWORD" | docker login harbor.example.com -u "$HARBOR_USER" --password-stdin
  script:
    - docker build --pull --build-arg GIT_SHA="$CI_COMMIT_SHORT_SHA" -t "$IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker push "$IMAGE:$CI_COMMIT_SHORT_SHA"
```

The private CA reaches the DinD daemon through the runner's `volumes` line
(`/etc/docker/certs.d:/etc/docker/certs.d:ro`), which GitLab Runner mounts into service
containers too. If you cannot change the runner config, build your own DinD image in Harbor
(`FROM docker:27-dind` plus `COPY ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt`) and use it as
the service.

The buildah alternative (no privileged daemon):

```yaml
build-image-buildah:
  stage: build
  image: harbor.example.com/platform/buildah:1.37     # mirror of quay.io/buildah/stable, pinned
  variables:
    STORAGE_DRIVER: vfs
    BUILDAH_ISOLATION: chroot
    BUILDAH_FORMAT: docker
  before_script:
    - mkdir -p /etc/containers/certs.d/harbor.example.com
    - cp "$HARBOR_CA_FILE" /etc/containers/certs.d/harbor.example.com/ca.crt   # File-type variable
    - echo "$HARBOR_PASSWORD" | buildah login -u "$HARBOR_USER" --password-stdin harbor.example.com
  script:
    - buildah build -t "$IMAGE:$CI_COMMIT_SHORT_SHA" .
    - buildah push "$IMAGE:$CI_COMMIT_SHORT_SHA"
```

**Key terms**

| Term | Meaning |
|---|---|
| `DOCKER_HOST` | where the docker CLI sends API calls; `tcp://docker:2376` is the DinD service |
| `DOCKER_TLS_CERTDIR` | makes DinD create TLS certs; empty string disables TLS (port 2375, not recommended) |
| `--pull` | always check for a newer base image, so security fixes in the base reach your image |
| Build arg `GIT_SHA` | bakes the commit into the image so `/version` can report what is running |
| Proxy-cache project | a Harbor project that transparently caches images from Docker Hub or another registry |

**See it on a real system.** The lines of a healthy DinD job log, in order:

```
Starting service docker:27-dind ...
Waiting for services to be up and running (timeout 30 seconds)...
dind 27.3.1
Login Succeeded
$ docker build --pull --build-arg GIT_SHA="$CI_COMMIT_SHORT_SHA" -t "$IMAGE:$CI_COMMIT_SHORT_SHA" .
#0 building with "default" instance using docker driver
#5 [1/6] FROM docker.io/library/python:3.12-slim@sha256:...
#9 [4/6] RUN pip install --no-cache-dir -r requirements.txt
#12 naming to harbor.example.com/shop/shop-web:9d8c7b6a done
$ docker push "$IMAGE:$CI_COMMIT_SHORT_SHA"
The push refers to repository [harbor.example.com/shop/shop-web]
5f70bf18a086: Pushed
c3a1b2d4e5f6: Pushed
9d8c7b6a: digest: sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c size: 1786
Job succeeded
```

→ Four checkpoints: the service started, the daemon answered (`docker info`), login worked, and the
push printed a **digest**. The digest (`sha256:4b1e...`) is the immutable identity of the image;
write it into the deployment record, because tags can be moved and digests cannot.

**Hands-on lab (test VM only)** — this is the Ops Ladder L3 drill "write a GitLab CI pipeline that
builds an image, tags it with the commit SHA and pushes it to Harbor".

**Step 1 — Build and push** with the DinD job to your lab Harbor project `shop`. Check the tag
`9d8c7b6a`-style name appears in Harbor's UI with the same digest as the job log.

**Step 2 — Break it, three ways, one at a time.** (a) Remove the `/etc/docker/certs.d` volume from
the runner config: push fails with `x509: certificate signed by unknown authority`. (b) Remove the
`command: ["--dns=..."]` line and point the lab runner VM's resolv.conf at a loopback-only resolver:
`RUN pip install` fails with `Temporary failure in name resolution` because DinD fell back to
8.8.8.8, which your lab firewall blocks. (c) Set `privileged = false`: the job fails with
`Cannot connect to the Docker daemon at tcp://docker:2376. Is the docker daemon running?`.

**Step 3 — Fix each** and write one line per failure in your runbook: error text → layer → fix.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `Cannot connect to the Docker daemon at tcp://docker:2376` | runner config `privileged`, service logs in the job | DinD not privileged, or TLS variables inconsistent (2375 vs 2376) |
| `x509: certificate signed by unknown authority` on push | `ls /etc/docker/certs.d/harbor.example.com/` **inside** the DinD service | CA not mounted into the service container |
| `Temporary failure in name resolution` during `RUN apt-get` | the service `command: --dns` | DinD uses its own resolver config; see [Docker learn module](30-learn-docker.md) |
| `toomanyrequests: You have reached your pull rate limit` | which registry the base image comes from | Docker Hub limits; use a Harbor proxy-cache project |
| Builds slow, every layer rebuilt | look for `CACHED` in the log | DinD starts empty each job; use `--cache-from` an image in Harbor or BuildKit registry cache |

**Why it matters for troubleshooting.** A CI build is a container inside a container: two resolvers,
two trust stores, two networks. Most "works on my laptop, fails in CI" image problems are one of
those three, in the inner layer.

**Next step:** what makes the push to Harbor correct: tags, robots and immutability.

### Pushing to Harbor with the commit SHA

**Level:** [L3 · Senior]

**Concept.** The tag decides whether you can answer "what is running?" and "what do I roll back
to?". Tag every build with the **commit SHA** (`$CI_COMMIT_SHORT_SHA`), add the **release tag**
(`v1.4.2`) for releases, and never deploy `latest`. A SHA tag maps an image straight back to a
commit, a merge request and a pipeline. Harbor adds the safety net: **robot accounts** (scoped
machine credentials instead of a person's password), **tag immutability rules** (a `v*` tag cannot
be overwritten), **vulnerability scanning** (Trivy) and **retention policies** (delete old SHA tags,
keep releases).

```
 commit 9d8c7b6a ──► pipeline 4812 ──► harbor.example.com/shop/shop-web:9d8c7b6a  (digest sha256:4b1e…)
 git tag v1.4.2  ──► tag pipeline  ──► harbor.example.com/shop/shop-web:v1.4.2    (same digest, immutable)
 production deploys the digest behind v1.4.2; rollback = deploy v1.4.1's digest
```

**Key terms**

| Term | Meaning |
|---|---|
| Robot account | Harbor machine user, project- or system-level, with chosen permissions and an expiry; name like `robot$shop+gitlab-ci` |
| Tag immutability rule | Harbor project rule: matching tags cannot be pushed again or deleted |
| Retention policy | rules that delete old artifacts, for example "keep the 20 most recent SHA tags, keep all `v*`" |
| Digest | `sha256:...`, the content hash of the image manifest |
| Promotion | giving an already-tested image a new tag (or copying it to another project) instead of rebuilding |

**See it on a real system.** From any machine that trusts the CA, without pulling the image:

```bash
# list tags of a repository through Harbor's v2 API (robot or user credentials)
curl -s -u "$HARBOR_USER:$HARBOR_PASSWORD" \
  "https://harbor.example.com/api/v2.0/projects/shop/repositories/shop-web/artifacts?page_size=3&with_tag=true" \
  | jq -r '.[] | "\(.digest[0:19])  \([.tags[]?.name] | join(","))  \(.push_time)"'
# which digest does a tag point to? (docker CLI, manifest only)
docker buildx imagetools inspect harbor.example.com/shop/shop-web:v1.4.2 | head -3
```

```
sha256:4b1e0c2d9f8a  9d8c7b6a,v1.4.2  2026-10-03T09:12:44.512Z
sha256:7c6d5e4f3a2b  5e4f3a2b         2026-10-02T16:40:03.118Z
sha256:0a1b2c3d4e5f  4e1d0c9b,v1.4.1  2026-09-30T11:02:57.904Z
Name:      harbor.example.com/shop/shop-web:v1.4.2
MediaType: application/vnd.docker.distribution.manifest.v2+json
Digest:    sha256:4b1e0c2d9f8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b8c7d6e5f4a3b2c
```

→ `v1.4.2` and `9d8c7b6a` share one digest: the release is exactly the image that was tested on
staging. `v1.4.1` is your rollback target, and you can name its digest without guessing. (Pass the
password through a netrc file or the credential helper in real scripts; `-u` puts it in the
process list.)

**Hands-on lab (test VM only)**

**Step 1 — Promote, do not rebuild.** Add a job on tag pipelines that pulls the SHA image, tags it
with `$CI_COMMIT_TAG` and pushes it. Confirm both tags show the same digest.

**Step 2 — Break it.** Push a different build to `v0.1.0` a second time (simulating someone re-tagging
a release). Then enable a tag immutability rule for `v*` in the Harbor project and try again: the
push now fails with an error that the tag is immutable.

**Step 3 — Fix the process.** Releases get new version numbers; immutability stays on; add a
retention policy that keeps all `v*` and the last 30 SHA tags.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `unauthorized: unauthorized to access repository: shop/shop-web, action: push` | robot permissions in Harbor | robot lacks push on this project, or expired |
| `denied: requested access to the resource is denied` or `project ... not found` (wording varies by Harbor version) | check the image path | pushing to a project that does not exist or a typo in the project name |
| Push fails for a release tag | Harbor project → Policy → Tag immutability | the tag already exists and is immutable (working as designed) |
| Production runs an unexpected build | compare digests of the tag over time | a mutable tag (often `latest`) was overwritten |
| `manifest unknown` on deploy | list tags as above | the pipeline that should have pushed it failed or was skipped by rules |

**Why it matters for troubleshooting.** When an incident starts after a deploy, the first question
is "what exactly changed?". A SHA tag plus a digest answers it in one API call and gives you the
exact rollback target.

**Next step:** deploy the image, first to Dokploy.

### Deploying to Dokploy from CI

**Level:** [L3 · Senior]

**Concept.** Dokploy can deploy in two ways, and they lead to different pipelines:

| Mode | How it works | Build happens | Use when |
|---|---|---|---|
| Git source + webhook | Dokploy clones the repo and builds the image itself; CI (or GitLab's webhook) calls Dokploy's deploy URL | on the Dokploy server | small apps, no Harbor, quick start |
| Docker image source + API | CI builds and pushes to Harbor; CI calls Dokploy's API to set the new image tag and deploy | in CI (build once) | your target: the same image goes to staging and production |

With the image mode, Dokploy runs the app as a Docker Swarm service on `dokploy-network`, and
Traefik routes the domain to it. The Dokploy host's Docker must **trust Harbor's CA**
(`/etc/docker/certs.d/harbor.example.com/ca.crt`) and have **pull credentials** (configure Harbor
under Dokploy's registry settings, or log in on the host), otherwise the service task fails with
`No such image` or an x509 error.

Dokploy's API uses an **API key** created in the Dokploy UI (under your profile's API/CLI settings; menu names vary by version) and sent
in the `x-api-key` header; the instance documents its endpoints in a Swagger page
(`https://dokploy.example.com/swagger`). Endpoint names such as `application.deploy` and
`application.saveDockerProvider` are used below; **confirm them in your Dokploy version's Swagger
page** before you rely on them, because the API is still evolving. See [Dokploy docs](https://docs.dokploy.com/).

```yaml
deploy-staging:
  stage: deploy
  image: harbor.example.com/platform/deploy-tools:1.2     # your image: curl, jq, kubectl
  environment:
    name: staging
    url: https://shop-staging.example.com
  resource_group: staging                                 # never two deploys at once
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script:
    - |
      curl -fsS -X POST "$DOKPLOY_URL/api/application.saveDockerProvider" \
        -H "x-api-key: $DOKPLOY_TOKEN" -H "Content-Type: application/json" \
        -d "{\"applicationId\":\"$DOKPLOY_APP_ID\",\"dockerImage\":\"$IMAGE:$CI_COMMIT_SHORT_SHA\"}"
    - |
      curl -fsS -X POST "$DOKPLOY_URL/api/application.deploy" \
        -H "x-api-key: $DOKPLOY_TOKEN" -H "Content-Type: application/json" \
        -d "{\"applicationId\":\"$DOKPLOY_APP_ID\"}"
    # the deploy call returns before the rollout finishes: wait until the new version answers
    - |
      for i in $(seq 1 30); do
        v=$(curl -fsS https://shop-staging.example.com/version || true)
        [ "$v" = "$CI_COMMIT_SHORT_SHA" ] && echo "staging runs $v" && exit 0
        sleep 10
      done
      echo "staging still reports '$v', expected $CI_COMMIT_SHORT_SHA"; exit 1
```

**Key terms**

| Term | Meaning |
|---|---|
| Application ID | Dokploy's identifier of the app; visible in the app URL in the UI |
| Webhook deploy URL | per-app URL Dokploy shows for "auto deploy"; anyone with the URL can trigger a deploy, so treat it as a secret |
| `resource_group` | GitLab keyword that serialises jobs sharing the name across pipelines |
| `/version` endpoint | an app route returning the baked-in `GIT_SHA`; the only reliable proof of what is running |

**See it on a real system** (on the Dokploy host, read-only):

```bash
docker service ls --format 'table {{.Name}}\t{{.Replicas}}\t{{.Image}}' | grep -E '^NAME|shop'
docker service ps shop-web-x1y2z3 --format 'table {{.Name}}\t{{.Image}}\t{{.CurrentState}}\t{{.Error}}' | head -4
```

```
NAME              REPLICAS   IMAGE
shop-web-x1y2z3   1/1        harbor.example.com/shop/shop-web:9d8c7b6a
NAME                IMAGE                                       CURRENT STATE            ERROR
shop-web-x1y2z3.1   harbor.example.com/shop/shop-web:9d8c7b6a   Running 2 minutes ago
 \_ shop-web-x1y2z3.1   harbor.example.com/shop/shop-web:5e4f3a2b   Shutdown 2 minutes ago
```

→ The service now runs the new SHA, and Swarm kept the previous task in history (`\_` line) with
the old image. If the new task were failing you would see `Rejected` or `Failed` with an error
such as `No such image: harbor.example.com/shop/shop-web:9d8c7b6a` (pull problem) or `task:
non-zero exit (1)` (app problem).

**Hands-on lab (test VM only)**

**Step 1 — Wire it up.** In the lab Dokploy, create an application with source "Docker", image
`harbor.example.com/shop/shop-web:SOME_SHA`, domain `shop-staging.example.com`, container port 8000.
Create an API key, store `DOKPLOY_URL`, `DOKPLOY_TOKEN` (masked, protected) and `DOKPLOY_APP_ID` in
GitLab. Run the job above.

**Step 2 — Break it.** Remove Harbor's CA from `/etc/docker/certs.d/` on the Dokploy VM and
deploy a new SHA. The API call succeeds, but the Swarm task is rejected and the verify loop fails
after five minutes. Then restore the CA and instead push an image whose app listens on port 5000
while Dokploy still says 8000: Traefik returns `502 Bad Gateway`.

**Step 3 — Fix it** with the evidence: `docker service ps` (pull error) for the first, Traefik's log
and the container's real port for the second (see
[Traefik 502 in the containers playbook](26-playbook-containers-k8s.md)).

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `curl: (22) The requested URL returned error: 401` from the API | check the `x-api-key` header and token | wrong, expired or unmasked-then-rotated token |
| API call OK, app still old | `docker service ps SERVICE` on the Dokploy host | task rejected: image pull failed (CA, credentials, tag missing) |
| `502 Bad Gateway` after deploy | `docker logs` of Traefik, the app's real listen port | port mismatch, app on 127.0.0.1, wrong network (see [Dokploy troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting)) |
| Two deploys overlap, older one wins | look for parallel pipelines | missing `resource_group` |

**Why it matters for troubleshooting.** "The pipeline is green but the site shows the old version"
is a classic. A green deploy job only proves an API call succeeded. The `/version` check makes the
pipeline tell the truth.

**Next step:** the same idea on Kubernetes, where the cluster reports rollout success for you.

### Deploying to Kubernetes from CI

**Level:** [L3 · Senior]

**Concept.** Two models exist. **Push**: the CI job has credentials for the cluster and runs
`kubectl` (or `helm upgrade`). **Pull** (GitOps): an agent inside the cluster (the GitLab agent for
Kubernetes, Argo CD, Flux) watches Git and applies changes itself, so CI never holds cluster
credentials. Start with push, done safely: a ServiceAccount that can only update Deployments in
one namespace, its kubeconfig stored as a **File** variable scoped to the environment, and a
rollout status check that fails the job if the new Pods never become Ready.

```yaml
deploy-production:
  stage: deploy
  image: harbor.example.com/platform/deploy-tools:1.2
  environment:
    name: production
    url: https://shop.example.com
  resource_group: production
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
      when: manual                       # inside rules, manual jobs block the pipeline by default
  script:
    # KUBECONFIG is a File-type variable scoped to environment "production"
    - kubectl -n shop set image deployment/shop-web shop-web="$IMAGE:$CI_COMMIT_TAG"
    - kubectl -n shop annotate deployment/shop-web kubernetes.io/change-cause="$CI_COMMIT_TAG pipeline $CI_PIPELINE_ID" --overwrite
    - kubectl -n shop rollout status deployment/shop-web --timeout=180s
```

The least-privilege RBAC for that ServiceAccount (apply once, by an admin):

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: {name: gitlab-deployer, namespace: shop}
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: {name: deployer, namespace: shop}
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "patch", "update"]
  - apiGroups: ["apps"]
    resources: ["replicasets"]
    verbs: ["get", "list", "watch"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: {name: gitlab-deployer, namespace: shop}
subjects: [{kind: ServiceAccount, name: gitlab-deployer, namespace: shop}]
roleRef: {apiGroup: rbac.authorization.k8s.io, kind: Role, name: deployer}
```

Every node must be able to pull from Harbor: an `imagePullSecret` in the namespace and the CA in
containerd's `hosts.toml` on every node (see [Kubernetes learn module](31-learn-kubernetes.md),
section 17).

**Key terms**

| Term | Meaning |
|---|---|
| `kubectl rollout status` | waits until the Deployment's new ReplicaSet is fully available, or fails at the timeout |
| `progressDeadlineSeconds` | Deployment field; after it the rollout is marked failed (`ProgressDeadlineExceeded`) |
| `change-cause` annotation | text shown by `kubectl rollout history` |
| GitLab agent for Kubernetes | in-cluster agent that lets CI jobs or GitOps apply manifests without a stored kubeconfig |
| `kubectl auth can-i` | checks what the ServiceAccount is allowed to do |

**See it on a real system**

```bash
kubectl -n shop auth can-i patch deployments --as=system:serviceaccount:shop:gitlab-deployer
kubectl -n shop auth can-i delete pods --as=system:serviceaccount:shop:gitlab-deployer
kubectl -n shop rollout history deployment/shop-web
```

```
yes
no
deployment.apps/shop-web
REVISION  CHANGE-CAUSE
4         v1.4.0 pipeline 4790
5         v1.4.1 pipeline 4801
6         v1.4.2 pipeline 4815
```

→ The deployer can patch Deployments but cannot delete Pods: a leaked CI credential cannot wipe the
namespace. The history ties each revision to a release and a pipeline, so `kubectl rollout undo
--to-revision=5` has a meaning you can say out loud ("back to v1.4.1").

**Hands-on lab (test VM only)**

**Step 1 — Deploy** to your kubeadm homelab with the job above, from a `v0.2.0` tag.

**Step 2 — Break it.** Tag `v0.2.1` from a commit whose readiness probe path is wrong. The rollout
never completes: `kubectl rollout status` prints `Waiting for deployment "shop-web" rollout to
finish: 1 out of 3 new replicas have been updated...` and then
`error: timed out waiting for the condition`. The job fails, but with the default
`maxUnavailable: 25%` (0 Pods for 3 replicas) and `maxSurge: 25%` (1 Pod) the three old Pods are
still serving: only one new, never-Ready Pod was added.

**Step 3 — Fix it.** Run the rollback job (in the complete pipeline below) or
`kubectl -n shop rollout undo deployment/shop-web`, then fix the probe and release `v0.2.2`.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `error: You must be logged in to the server (Unauthorized)` | `kubectl config view --minify` in the job | expired token or wrong kubeconfig for this environment scope |
| `... is forbidden: User "system:serviceaccount:shop:gitlab-deployer" cannot patch resource "deployments"` | `kubectl auth can-i` as above | Role or RoleBinding missing or in another namespace |
| `ImagePullBackOff` after deploy | `kubectl -n shop describe pod POD` | pull secret or containerd CA missing (see [containers playbook](26-playbook-containers-k8s.md)) |
| `error: timed out waiting for the condition` | `kubectl -n shop get pods`, `describe`, `logs --previous` | probes failing or CrashLoopBackOff in the new ReplicaSet |

**Why it matters for troubleshooting.** `rollout status` turns "the deploy job is green" into "the
new Pods are Ready", which is the property you actually care about. Without it, broken releases
look successful until users complain.

**Next step:** put a human gate and an audit trail in front of production: environments.

### Environments and manual approvals

**Level:** [L3 · Senior]

**Concept.** An **environment** (`environment: name: production`) makes GitLab record every
deployment: which commit, which pipeline, who triggered it, when. Operate → Environments then
shows what is running where, and each old deployment has a **Re-deploy** (rollback) button that
re-runs that old deploy job. Add control in layers:

| Control | Tier | Effect |
|---|---|---|
| `when: manual` (inside `rules`) | all | a person must click; the pipeline shows "blocked" until then |
| Protected tags `v*` + protected variables | all | only maintainers can create releases; only release pipelines see production secrets |
| Protected runner | all | production deploys only run on a dedicated runner that also has network access to production |
| `resource_group: production` | all | at most one deploy to production at a time; others queue |
| Protected environments | Premium | only named users or groups can deploy to `production` |
| Deployment approvals | Premium | N approvals required before the deploy job runs |
| Deploy freezes | all (Settings → CI/CD → Deploy freezes, checked with `CI_DEPLOY_FREEZE` in `rules`) | block deploys during holidays or change freezes |

**Key terms**

| Term | Meaning |
|---|---|
| Deployment | one run of a job with `environment:` |
| Re-deploy / rollback | re-running an older deployment job from the environment page |
| `environment:action: stop` | a job that tears down a review environment |
| `CI_DEPLOY_FREEZE` | variable set during a configured freeze window; use it in `rules` |

**See it on a real system**

```bash
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB/projects/$PROJECT_ID/deployments?environment=production&order_by=id&sort=desc&per_page=3" \
  | jq -r '.[] | "\(.id) \(.status) \(.ref) \(.sha[0:8]) by \(.user.username) at \(.created_at)"'
```

```
1207 success v1.4.2 9d8c7b6a by ops.engineer at 2026-10-03T09:20:11.000Z
1199 success v1.4.1 4e1d0c9b by ops.engineer at 2026-09-30T11:15:40.000Z
1190 failed v1.4.0 77f0a12c by dev.lead at 2026-09-24T14:03:09.000Z
```

→ This is your deployment audit trail. In an incident, "did anything deploy in the last hour?" is
one API call; in a postmortem, these lines are the timeline.

**Hands-on lab (test VM only)**

**Step 1 — Gate production.** Make `deploy-production` manual on tags and give it
`resource_group: production`. Release `v0.3.0` and click the play button.

**Step 2 — Break it.** Start two tag pipelines quickly (`v0.3.1`, `v0.3.2`) and click both deploys.
With `resource_group` the second waits ("waiting for resource"). Remove `resource_group` and repeat:
both run at once and the final state depends on which finished last.

**Step 3 — Fix it and practise the undo.** Restore `resource_group`, then use Operate →
Environments → production → Re-deploy on `v0.3.1` and confirm with `/version` and `kubectl rollout
history`.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Pipeline stuck "blocked" | look for a manual job | `when: manual` inside `rules` defaults to `allow_failure: false`, which blocks; intended for production gates |
| Manual job appears on feature branches | its `rules` | rule too broad; production deploy must match only release tags |
| Re-deploy of an old version fails | that old job's log | the old image was deleted by retention, or the old job needs variables that changed |

**Why it matters for troubleshooting.** Rollback must be boring: one click, a known version, a
recorded result. If your rollback depends on someone remembering a command at 3 a.m., you do not
have one.

**Next step:** everything together in one file.

### The complete example pipeline

**Level:** [L3 · Senior]

**Concept.** This is the Ops Ladder L3 exit test pipeline: one Apache workload containerised as
`shop-web`, built by GitLab CI, pushed to Harbor with the commit SHA, deployed to Dokploy staging
on every merge to `main`, promoted (not rebuilt) on a release tag, deployed to production behind a
manual gate, verified by `/version`, with a manual rollback job you have actually run. Read it
top to bottom; every block was explained in the topics above.

```yaml
# .gitlab-ci.yml — shop-web: lint → test → build → deploy, Harbor + Dokploy + Kubernetes
stages: [lint, test, build, release, deploy, verify]

workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS
      when: never
    - if: $CI_COMMIT_BRANCH
    - if: $CI_COMMIT_TAG

variables:
  IMAGE: harbor.example.com/shop/shop-web
  # CI images come through the Harbor proxy cache, pinned
  DOCKER_IMAGE: harbor.example.com/dockerhub-proxy/library/docker:27
  DIND_IMAGE: harbor.example.com/dockerhub-proxy/library/docker:27-dind
  TOOLS_IMAGE: harbor.example.com/platform/deploy-tools:1.2

default:
  tags: [docker]
  interruptible: true

.docker: &docker                      # reusable DinD setup (YAML anchor)
  image: $DOCKER_IMAGE
  services:
    - name: $DIND_IMAGE
      alias: docker
      command: ["--dns=192.0.2.53", "--dns=192.0.2.54"]
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"
    DOCKER_TLS_VERIFY: "1"
    DOCKER_CERT_PATH: "/certs/client"
  before_script:
    - for i in $(seq 1 30); do docker info >/dev/null 2>&1 && break; sleep 1; done
    # HARBOR_PASSWORD is protected: empty on feature branches and MRs, which only build, never push
    - |
      if [ -n "$HARBOR_PASSWORD" ]; then
        echo "$HARBOR_PASSWORD" | docker login harbor.example.com -u "$HARBOR_USER" --password-stdin
      fi

# ---------- lint ----------
conflict-markers:
  stage: lint
  image: $TOOLS_IMAGE
  script:
    # a leading "!" would not fail the job (bash ignores errexit for negated commands), so test explicitly
    - |
      if git grep -nE '^(<<<<<<<|=======|>>>>>>>)( |$)' -- . ':!*.md'; then
        echo "conflict markers found"; exit 1
      fi

compose-config:
  stage: lint
  <<: *docker
  before_script: []                   # no login needed to validate
  script:
    - docker compose -f compose.yml config --quiet

# ---------- test ----------
unit-tests:
  stage: test
  image: harbor.example.com/dockerhub-proxy/library/python:3.12-slim
  needs: []
  variables:
    PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  cache:
    key: {files: [requirements.txt]}
    paths: [.cache/pip]
  script:
    - pip install -r requirements.txt pytest
    - pytest -q --junitxml=report.xml
  artifacts:
    when: always
    reports: {junit: report.xml}
    expire_in: 1 week

# ---------- build (branches and MRs build; only main pushes; tags never rebuild) ----------
build-image:
  stage: build
  <<: *docker
  needs: [unit-tests]
  rules:
    - if: $CI_COMMIT_TAG
      when: never                     # build once: the tag pipeline promotes main's image
    - when: on_success
  script:
    - docker build --pull --build-arg GIT_SHA="$CI_COMMIT_SHORT_SHA" -t "$IMAGE:$CI_COMMIT_SHORT_SHA" .
    - |
      if [ "$CI_COMMIT_BRANCH" = "$CI_DEFAULT_BRANCH" ]; then
        docker push "$IMAGE:$CI_COMMIT_SHORT_SHA"
      else
        echo "feature branch or MR: image built, not pushed"
      fi

# ---------- release: promote the SHA image main built and staging tested ----------
promote-release:
  stage: release
  <<: *docker
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
  script:
    # fails with "manifest unknown" if the tagged commit was never built on main
    - docker pull "$IMAGE:$CI_COMMIT_SHORT_SHA"
    - docker tag "$IMAGE:$CI_COMMIT_SHORT_SHA" "$IMAGE:$CI_COMMIT_TAG"
    - docker push "$IMAGE:$CI_COMMIT_TAG"

# ---------- deploy ----------
deploy-staging:
  stage: deploy
  image: $TOOLS_IMAGE
  needs: [build-image]
  environment: {name: staging, url: "https://shop-staging.example.com"}
  resource_group: staging
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script:
    - ./ci/dokploy-deploy.sh "$IMAGE:$CI_COMMIT_SHORT_SHA"     # the two API calls from the Dokploy topic

deploy-production:
  stage: deploy
  image: $TOOLS_IMAGE
  needs: [promote-release]
  environment: {name: production, url: "https://shop.example.com"}
  resource_group: production
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/ && $CI_DEPLOY_FREEZE == null
      when: manual
  script:
    - kubectl -n shop set image deployment/shop-web shop-web="$IMAGE:$CI_COMMIT_TAG"
    - kubectl -n shop annotate deployment/shop-web kubernetes.io/change-cause="$CI_COMMIT_TAG pipeline $CI_PIPELINE_ID" --overwrite
    - kubectl -n shop rollout status deployment/shop-web --timeout=180s

# ---------- verify: prove what is running ----------
verify-staging:
  stage: verify
  image: $TOOLS_IMAGE
  needs: [deploy-staging]
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
  script:
    - ./ci/wait-for-version.sh https://shop-staging.example.com/version "$CI_COMMIT_SHORT_SHA" 300

verify-production:
  stage: verify
  image: $TOOLS_IMAGE
  needs: [deploy-production]
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
  script:
    - ./ci/wait-for-version.sh https://shop.example.com/version "$CI_COMMIT_SHORT_SHA" 300

# ---------- rollback: tested, boring, one click ----------
rollback-production:
  stage: deploy
  image: $TOOLS_IMAGE
  environment: {name: production, url: "https://shop.example.com"}
  resource_group: production
  rules:
    - if: $CI_COMMIT_TAG =~ /^v\d+\.\d+\.\d+$/
      when: manual
      allow_failure: true                # does not block the pipeline
  script:
    - kubectl -n shop rollout undo deployment/shop-web
    - kubectl -n shop rollout status deployment/shop-web --timeout=180s
    - kubectl -n shop rollout history deployment/shop-web | tail -3
```

**Key terms**

| Term | Meaning |
|---|---|
| YAML anchor `&docker` / `<<: *docker` | define a block once, merge it into several jobs (within one file) |
| `needs: []` on tests | tests do not wait for lint; feedback arrives sooner |
| Promote | `v1.4.2` is the **same** image that passed staging, retagged |
| `CI_DEPLOY_FREEZE == null` | the production deploy is not offered during a configured freeze |

**See it on a real system.** A successful release pipeline, as the API reports it:

```
lint     conflict-markers     success
lint     compose-config       success
test     unit-tests           success
release  promote-release      success   (pulled 9d8c7b6a, pushed v1.4.2: same digest)
deploy   deploy-production    success   (manual, played by ops.engineer)
deploy   rollback-production  manual    (not played)
verify   verify-production    success
```

→ Every stage has a reason to exist; the rollback job is visible on every release pipeline, so
undoing a release is one click on the pipeline that caused the problem.

**Hands-on lab (test VM only)** — this is the core of the Ops Ladder L3 exit test.

**Step 1 — Build it.** Containerise one of your Apache workloads (a static site or the PHP app) into
`shop-web`, add the file above and the two helper scripts, and get a green pipeline on `main` and
on a `v0.1.0` tag.

**Step 2 — Break it on purpose, in production-like staging.** Release `v0.1.1` with a deliberate
bug that makes `/healthz` fail. Watch the rollout fail and the old version keep serving.

**Step 3 — Roll back and write it down.** Play `rollback-production`, confirm `/version`, then write
the rollback procedure into the app's runbook (section 7) with the time it took. A rollback you have
not timed is not tested.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| `promote-release` fails with `manifest unknown` | was the tagged commit built on `main`? (`git branch -r --contains TAG`) | tag created on a feature-branch commit; tag only commits that passed `main` |
| `verify-production` times out but the rollout succeeded | `curl -s https://shop.example.com/version` | Traefik or Ingress still routing to old Pods, caching proxy, or `GIT_SHA` build arg missing |
| Rollback job does nothing useful | `kubectl rollout history` | only one revision exists, or `revisionHistoryLimit: 0` |

**Why it matters for troubleshooting.** This pipeline encodes your troubleshooting knowledge: the
conflict-marker check prevents a known outage, `compose config` and `rollout status` catch broken
releases, `/version` exposes "green but not deployed", and the rollback job turns an incident into
a two-minute event.

**Next step:** when it goes red anyway, debug it methodically.

### Debugging failed pipelines

**Level:** [L2 · Mid]

**Concept.** A failed pipeline is debugged like a site that is down: by layers, from the outside in,
with evidence at each layer. The layers are: **configuration** (did GitLab understand the YAML and
create the job?), **scheduling** (did a runner pick it up?), **environment** (did the executor
prepare the container, services, clone?), **script** (did your commands fail?), and **external
systems** (Harbor, Dokploy, Kubernetes). Steps 1 to 7 below walk them in that order.

```
 pipeline red / missing
   │
   ├─ no pipeline or "yaml invalid" ─────────────────────► Step 3 (config)
   ├─ job pending / stuck ───────────────────────────────► Step 4 (runner, tags)
   ├─ "ERROR: Job failed (system failure)" ──────────────► Step 5 (executor, host)
   ├─ "ERROR: Job failed: exit code N" ───────────────────► Step 6 (script, reproduce)
   └─ fails talking to Harbor / Dokploy / cluster ────────► Step 7 (external system)
```

### Step 1 — Read the failed job log bottom-up

**Goal:** find the **first** real error, not the last line.

```bash
# from the UI: open the red job. From the API (job id from the pipeline's job list):
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$GITLAB/projects/$PROJECT_ID/jobs/91240/trace" > job-91240.log
grep -nE 'ERROR|error:|denied|x509|refused|timed out|No such|not found|exit code' job-91240.log | head -20
tail -25 job-91240.log
```

```
212:#9 [4/6] RUN pip install --no-cache-dir -r requirements.txt
231:#9 2.411 WARNING: Retrying (Retry(total=4 ...)) after connection broken by 'NewConnectionError(...: Failed to establish a new connection: [Errno -3] Temporary failure in name resolution')': /simple/flask/
247:#9 ERROR: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
252:ERROR: failed to solve: process "/bin/sh -c pip install --no-cache-dir -r requirements.txt" did not complete successfully: exit code: 1
258:ERROR: Job failed: exit code 1
```

**What it means:** read upward from `ERROR: Job failed`. Line 258 only says the script failed;
lines 247 and 252 say the Docker build failed in a `RUN` step; line 231 is the **first** real error:
DNS resolution failed **inside the build**. The cause is in the environment layer (DinD's resolver),
not in the Dockerfile or the Python code.

**Why this step (now):** the log is the only evidence that already exists; reading it costs a minute
and usually names the layer. Re-running the job first ("maybe it was flaky") destroys nothing but
wastes runner time and teaches you nothing.

**Next step:** if you found a specific error, classify it with Step 2. If the job has no log at all
(it never started), go to Step 4. If there is no pipeline at all, go to Step 3.

### Step 2 — Classify the failure by its last line

**Goal:** decide which layer to investigate from the job's final status line.

```bash
grep -E '^ERROR: Job failed|This job is stuck|Job succeeded' job-91240.log
```

```
ERROR: Job failed: exit code 1                                       → script layer (Step 6)
ERROR: Job failed (system failure): Error response from daemon: ...  → executor/host layer (Step 5)
ERROR: Job failed: execution took longer than 1h0m0s seconds         → timeout (Step 6, or a hung service)
This job is stuck because ... runners ...                           → scheduling layer (Step 4)
```

**What it means:** `exit code N` means your commands ran and one returned non-zero. `system
failure` means the runner could not even prepare or run the container (image pull, disk, Docker
daemon). A timeout means something hung, often a command waiting for input or a network call
without a timeout. "Stuck" means no runner took the job.

**Why this step (now):** the same error text ("cannot connect") means different things in different
layers; classifying first stops you from editing the YAML when the runner host's disk is full.

**Next step:** config problem → Step 3. Stuck → Step 4. System failure → Step 5. Exit code or
timeout → Step 6. If the failing command talks to Harbor, Dokploy or Kubernetes → Step 7.

### Step 3 — Pipeline missing or YAML invalid

**Goal:** prove GitLab understands the configuration and that your job's rules match this pipeline.

```bash
# validate the file as GitLab sees it (project-scoped lint, includes resolved)
jq -n --rawfile y .gitlab-ci.yml '{content: $y}' | \
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" --header "Content-Type: application/json" \
  --data @- "$GITLAB/projects/$PROJECT_ID/ci/lint" | jq '{valid, errors, warnings}'
```

```
{
  "valid": false,
  "errors": [
    "jobs:deploy-production:rules:rule if invalid expression syntax"
  ],
  "warnings": []
}
```

**What it means:** `valid: false` names the exact key. Typical messages: `rule if invalid
expression syntax` (a regex without slashes, `==` with an unquoted string containing spaces),
`config key may not be used with 'rules': only`, `jobs:X config should implement the script:,
run:, or trigger: keyword`, `Included file ... does not have valid YAML syntax`. If `valid` is `true` but
your job is missing, the YAML is fine and **rules** excluded the job: print the variables with the
debug job from the "Rules, needs and the DAG" topic.

**Why this step (now):** without a valid config there is no pipeline and no job log, so every later
step is impossible. The lint endpoint (or the Pipeline editor's Validate button) is the only
evidence at this layer.

**Next step:** if invalid, fix the named key, re-lint, push. If valid but the job is missing, fix
the rule and confirm with the debug job. If the job exists but is pending, go to Step 4.

### Step 4 — Job pending or stuck

**Goal:** prove a runner is online, allowed and tagged to take this job.

```bash
# on the runner host
sudo gitlab-runner verify
systemctl is-active gitlab-runner
sudo journalctl -u gitlab-runner --since "15 min ago" --no-pager | tail -5   # "Checking for jobs... nothing" is logged only with log_level = "debug"
# from anywhere: the job's tags and whether it is from a protected ref
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$GITLAB/projects/$PROJECT_ID/jobs/91241" | jq '{status, tag_list, ref, runner}'
```

```
Verifying runner... is valid    runner=t1_XXXXXX
active
Oct 03 09:31:02 runner01 gitlab-runner[4120]: Checking for jobs... nothing   runner=t1_XXXXXX
{
  "status": "pending",
  "tag_list": ["docker", "prod-deploy"],
  "ref": "feature/healthz",
  "runner": null
}
```

**What it means:** the runner is healthy and polling ("nothing", visible here because `log_level = "debug"`
is set in `config.toml` for the investigation; at the default level only "received" lines appear), so GitLab is deliberately **not**
giving it the job. The job wants tags `docker` **and** `prod-deploy`; runner01 has only `docker`.
And the ref is an unprotected feature branch, so even a protected `prod-deploy` runner would refuse
it. Other outcomes: `verify` fails → runner auth or network problem; service inactive → start it
and read why it stopped; "Checking for jobs... received" but job still pending → `concurrent` limit
reached.

**Why this step (now):** a stuck job has no log, so the evidence lives on the runner host and in the
job's metadata. Checking tags and protection before touching the runner avoids "fixing" a runner
that is working as designed.

**Next step:** tag mismatch → fix the job's `tags:` or the runner's tags. Protected runner with
unprotected ref → that job should not run on this branch; fix its `rules`. Runner unhealthy → fix
the service, then re-run. Once the job starts and fails, go back to Step 2.

### Step 5 — System failure on the runner host

**Goal:** find the host-level reason the executor could not prepare or run the job.

```bash
# on the runner host
df -h /var/lib/docker /
docker system df
sudo journalctl -u docker --since "30 min ago" --no-pager | tail -5
sudo journalctl -u gitlab-runner --since "30 min ago" --no-pager | grep -iE 'error|fail' | tail -5
```

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda2        98G   97G  1.0G  99% /
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          214       6         61.2GB    58.9GB (96%)
Containers      9         2         1.1GB     1.0GB (90%)
Local Volumes   388       2         21.7GB    21.5GB (99%)
Build Cache     0         0         0B        0B
Oct 03 09:40:17 runner01 gitlab-runner[4120]: ERROR: Job failed (system failure): Error response from daemon: mkdir /var/lib/docker/overlay2/...: no space left on device
```

**What it means:** the disk is 99% full, almost all of it reclaimable: 214 old images and 388
orphaned volumes from finished jobs (each DinD and cache container leaves volumes behind). Other
typical system failures: `Error response from daemon: pull access denied` or `x509` (the runner's
Docker cannot pull the job image), `Cannot connect to the Docker daemon at unix:///var/run/docker.sock`
(dockerd down on the runner host), `ERROR: Preparation failed: ... context deadline exceeded`
(image pull too slow or blocked).

**Why this step (now):** a system failure is never fixed in `.gitlab-ci.yml`. Checking disk and the
Docker daemon first covers the most common causes in under a minute.

**Next step:** disk full → clean up **on the runner VM only** (below) and add the scheduled cleanup
from "Prevent it next time". Pull or x509 errors → fix the CA or credentials on the runner host
(trust map, section 0). Daemon down → see [Docker reference](14-docker-containers.md). Then re-run
the job and return to Step 2 if it still fails.

> ⚠️ `docker system prune -a --volumes` deletes **every** unused image and volume on the host. On a
> dedicated CI runner VM that is usually fine; on a host that also runs services (never do CI on the
> Dokploy host) it deletes data. Safer first: GitLab Runner ships a cleanup script,
> `/usr/share/gitlab-runner/clear-docker-cache`, that only touches runner-managed containers and
> volumes; or `docker volume prune --all -f --filter "label=com.gitlab.gitlab-runner.managed=true"`
> (Docker 23+ needs `--all` to include named volumes; check the label with `docker volume inspect`
> first), and `docker image prune -a -f --filter "until=168h"` removes unused images created more
> than a week ago (`until` filters on creation time, not on last use).

### Step 6 — Reproduce a script failure locally

**Goal:** run the failing command in the **same image** with the same inputs, outside GitLab.

```bash
# on your lab workstation (or the runner VM), in a checkout of the failing commit
git switch --detach 9d8c7b6a
docker run --rm -it -v "$PWD":/src -w /src \
  -e CI=true -e CI_COMMIT_SHORT_SHA=9d8c7b6a \
  harbor.example.com/dockerhub-proxy/library/python:3.12-slim bash
# inside: paste the job's script lines one by one
pip install -r requirements.txt pytest && pytest -q
```

```
FAILED tests/test_health.py::test_version_endpoint - AssertionError: assert 'unknown' == '9d8c7b6a'
1 failed, 23 passed in 3.41s
```

**What it means:** the failure reproduces outside CI, so it is a real code or test problem, not the
runner. Here the app reads the SHA from an environment variable the test sets differently. If it
does **not** reproduce locally, the difference is the CI environment: a variable that is empty in CI
(protected or scoped), a different image tag than you think, a service missing, or network/DNS from
the runner.

**Why this step (now):** reproducing in the same image separates "my code is wrong" from "CI is
different" with one experiment. It is cheaper than pushing ten debug commits.

**Next step:** reproduces → fix the code or test, push, Step 1 on the new pipeline if it still fails.
Does not reproduce → compare variables (names only) and image digests between CI and local; if the
failing command talks to an external system, go to Step 7.

> ⚠️ `CI_DEBUG_TRACE: "true"` makes the job print every shell command **with expanded variables,
> including secrets that masking may not catch**, and anyone with access to the job log can read
> them. Use it only on a throwaway branch in a lab project, then delete the job log and rotate any
> credential it exposed. Prefer `set -x` around the few lines you need.

### Step 7 — Harbor, Dokploy or cluster rejects the job

**Goal:** identify which external system refused the request and why, from inside a job.

```bash
# add temporarily to the failing job (names and hosts only, no secret values)
- getent ahosts harbor.example.com
- echo | openssl s_client -connect harbor.example.com:443 -servername harbor.example.com 2>/dev/null | openssl x509 -noout -issuer -enddate
- curl -sS -o /dev/null -w '%{http_code}\n' https://harbor.example.com/api/v2.0/ping
- echo "user=$HARBOR_USER password_set=${HARBOR_PASSWORD:+yes}"
```

```
192.0.2.22      STREAM harbor.example.com
issuer=CN = Example Corp Root CA
notAfter=Mar 14 12:00:00 2027 GMT
curl: (60) SSL certificate problem: unable to get local issuer certificate
000
user=robot+gitlab-ci password_set=yes
```

**What it means:** DNS works (192.0.2.22). The certificate is from your private root CA and not
expired, but **this container** does not trust that CA (curl error 60), so every HTTPS client in it
fails. Separately, the user name lost its `$shop` part: "Expand variable reference" is on. Two
independent problems, both now proven. For Dokploy the same checks apply with `DOKPLOY_URL` and an
HTTP 401 meaning a bad API key; for Kubernetes, `kubectl auth can-i` and the error text
(`Unauthorized` vs `forbidden`) separate authentication from authorisation.

**Why this step (now):** external failures look like script failures (`exit code 1`), but no code
change fixes them. Testing DNS, TLS, reachability and identity separately, in the job's own
container, tells you exactly which one to fix.

**Next step:** TLS → add the CA to the job image or mount it (trust map, section 0). Identity → fix the
variable flags or robot permissions (Harbor), token (Dokploy), RBAC (Kubernetes). DNS → runner `dns`
setting or DinD `--dns`. Then remove the debug lines and re-run from Step 1.

### Pipeline decision tree, fix and prevent

**Level:** [L2 · Mid]

```
 Pipeline problem
 ├─ No pipeline / "yaml invalid"?
 │    └─ CI lint → fix named key → still missing job? → rules: print CI_ vars (Step 3)
 ├─ Job pending/stuck?
 │    ├─ runner verify fails → runner host: service, CA, DNS (Step 4)
 │    └─ runner OK → tags, protected runner vs ref, concurrent limit (Step 4)
 ├─ "system failure"?
 │    └─ runner host: disk, dockerd, image pull/x509 (Step 5)
 ├─ "exit code N" / timeout?
 │    ├─ reproduces in same image → code/test bug (Step 6)
 │    └─ does not reproduce → env: variables, image, DNS, services (Step 6)
 └─ external system refuses?
      └─ DNS → TLS trust → reachability → identity → permission (Step 7)
```

**Fix & verify.** After any fix, re-run the **whole** pipeline, not only the failed job, if the fix
touched `.gitlab-ci.yml`, variables or the runner. Verify with the job log (the error is gone and
the expected checkpoint lines appear: `Login Succeeded`, a push digest, `successfully rolled out`,
the `/version` match).

**Rollback.** If a pipeline change broke `main`, revert the commit that changed `.gitlab-ci.yml`
(`git revert`, section 1) so the team can merge again, then fix forward on a branch.

**Prevent it next time.**

- Lint `.gitlab-ci.yml` in an MR job or a pre-commit hook; keep shared CI templates in one project and `include:` them with a pinned `ref`.
- Pin CI images (tag plus digest for critical ones) and pull them through Harbor's proxy cache.
- Give the runner host disk monitoring and a weekly cleanup timer (Prometheus alert at 85%, see [Observability](32-learn-performance-observability.md)).
- Keep the trust map (section 0) as code: an Ansible role that installs the CA into every trust store on runners, Docker hosts and nodes.
- Write each new failure into your runbook as "error text → layer → fix".

---

## 3. Deployment strategies

> 📚 **Study path:** 1) KodeKloud: *Docker Certified Associate* — Docker Swarm → Swarm Services → Scaling, Rolling Updates and Rollbacks ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)), then *Kubernetes for the Absolute Beginners – Hands-on Tutorial* — Deployments and the rolling update labs ([course](https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners-hands-on-tutorial)) · 2) Note: this section, then [Deployment patterns](35-deployment-patterns.md) for how your Traefik/Dokploy host exposes each version · 3) KodeKloud: *Fundamentals of SRE* — Release Engineering ([course](https://kodekloud.com/courses/fundamentals-of-sre)); no video verified for this topic · 4) Practice: the labs below on the Dokploy VM (Swarm) and the kubeadm homelab.

A deployment strategy answers three questions: **how do users move from the old version to the
new one**, **how many users see a broken version before you notice**, and **how fast can you go
back**. The pipeline from section 2 delivers an image; the strategy decides what happens to
traffic. Choose it per application, write it into the runbook, and test the "go back" half.

```
                     users exposed to a bad release      rollback speed     extra capacity
 recreate            all, plus downtime                  redeploy (minutes) none
 rolling             grows with each batch               redeploy/undo      +1 batch
 blue/green          all at switch time (if no smoke)    switch back (secs) 2x
 canary              small %, then more                  shift weight (secs) small
 feature flag        chosen users                        flip flag (secs)   none
```

### Recreate and rolling updates

**Level:** [L2 · Mid] to operate, [L3 · Senior] to tune

**Concept.** **Recreate** stops every old instance, then starts the new ones: simple, never two
versions at once (good for apps that cannot run side by side, such as a single-writer worker), but
always some downtime. **Rolling** replaces instances in batches: start some new, wait until they are
healthy, stop some old, repeat. No downtime if health checks are honest and the app can run two
versions at once for a few minutes. Both Swarm (Dokploy) and Kubernetes do rolling updates natively.

```
 rolling, 3 replicas, start-first, parallelism 1:
   v1 v1 v1  →  v1 v1 v1 v2  →  v1 v1 v2  →  v1 v1 v2 v2  →  v1 v2 v2  → ... →  v2 v2 v2
                 (start v2,       (healthy? then
                  wait healthy)    stop one v1)
```

| Setting | Swarm (`docker service update`) | Kubernetes (Deployment `strategy`) |
|---|---|---|
| Batch size | `--update-parallelism 1` | `maxSurge` / `maxUnavailable` |
| New before old | `--update-order start-first` | `maxSurge: 1, maxUnavailable: 0` |
| Wait between batches | `--update-delay 10s`, `--update-monitor 30s` | readiness probe + `minReadySeconds` |
| Bad release | `--update-failure-action rollback` | rollout stalls; `progressDeadlineSeconds` marks it failed |
| Manual undo | `docker service rollback SERVICE` | `kubectl rollout undo deployment/NAME` |
| Recreate | `--update-order stop-first --update-parallelism 0` | `strategy: type: Recreate` |

A rolling update is only as good as the **health check** that gates it. Without a Docker
`HEALTHCHECK` (or a Kubernetes readiness probe), "healthy" means "the process started", and a broken
release rolls out to every instance.

**Key terms**

| Term | Meaning |
|---|---|
| `start-first` / `stop-first` | Swarm: start the new task before stopping the old one, or the reverse (default) |
| Failure action | Swarm: `pause` (default), `continue` or `rollback` when a new task fails |
| Readiness probe | Kubernetes: a Pod receives traffic only while it passes |
| `minReadySeconds` | a new Pod must stay Ready this long before it counts as available |
| Version skew | two versions serving at once during the rollout; the app must tolerate it |

**See it on a real system** (Dokploy host and homelab, read-only):

```bash
docker service inspect --pretty shop-web-x1y2z3 | sed -n '/UpdateConfig/,/RollbackConfig/p'
kubectl -n shop get deployment shop-web -o jsonpath='{.spec.strategy}{"\n"}{.spec.minReadySeconds}{"\n"}'
```

```
UpdateConfig:
 Parallelism:	1
 On failure:	pause
 Monitoring Period: 5s
 Max failure ratio: 0
 Update order:      stop-first
RollbackConfig:
{"rollingUpdate":{"maxSurge":"25%","maxUnavailable":"25%"},"type":"RollingUpdate"}

```

→ The Swarm service uses the defaults: **stop-first** (each batch drops capacity before the new task
is up) and **pause** on failure (a bad release stops halfway and waits for a human, with mixed
versions serving). For a one-replica Dokploy app, stop-first means a short outage on every deploy.
Kubernetes uses 25%/25% and no `minReadySeconds`. Both are tunable, and Dokploy exposes the Swarm
update settings per application (Advanced → Swarm settings in recent versions; check yours).

**Hands-on lab (test VM only)**

**Step 1 — Make it zero-downtime.** On the Dokploy VM, for a 2-replica test service with a
`HEALTHCHECK`, run `docker service update --update-order start-first --update-parallelism 1
--update-delay 10s --update-failure-action rollback --update-monitor 30s SERVICE`. In another
terminal run a loop of `curl -s -o /dev/null -w '%{http_code}\n'` against it every 0.2 s, and deploy
a new image: only 200s.

**Step 2 — Break it.** Deploy an image whose healthcheck fails after 10 seconds. Watch
`docker service ps SERVICE`: new tasks go `Running` then `Failed`, and Swarm rolls back
automatically (`rollback_started` in `docker service inspect --format '{{.UpdateStatus.State}}'`).
Repeat with `--update-failure-action pause` and see it stop half-way.

**Step 3 — Fix it.** Fix the image, deploy again, and write the chosen update settings into the
app's runbook and its Dokploy configuration so the next person does not reset them.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Short 502/503 burst on every deploy | `docker service inspect --pretty` | stop-first with one replica, or no healthcheck |
| Broken release reached all instances | check for a healthcheck / readiness probe | "started" was treated as "healthy" |
| Rollout stuck half-way, two versions serving | `docker service inspect --format '{{json .UpdateStatus}}'` | failure action `pause`; decide: `docker service rollback` or fix forward |
| Errors only during rollouts | app logs during the window | version skew: v2 writes data or sessions v1 cannot read |

**Why it matters for troubleshooting.** Many "random" errors happen only during deploys. If you know
the strategy and its timing, you can correlate error spikes with rollout batches instead of chasing
the network.

**Next step:** strategies that switch traffic instead of replacing instances: blue/green.

### Blue/green

**Level:** [L3 · Senior]

**Concept.** Run two complete environments: **blue** (current) and **green** (new). Deploy and test
green while blue serves all users, then switch the router so all traffic goes to green. Rollback is
switching back, which takes seconds, because blue is still running. The cost is double capacity
during the switch and the requirement that both versions can share the same database.

```
                 before switch                          after switch
 users ─► Traefik ─► shop-blue (v1.4.1)        users ─► Traefik ─► shop-green (v1.4.2)
                     shop-green (v1.4.2)                           shop-blue (v1.4.1, idle, kept
                     (tested via shop-green.                       for fast rollback until v1.4.3)
                      internal.example.com)
```

On your stack, the switch can live in a Traefik **file-provider** route (one line changes), in
Dokploy (move the domain from one app to the other), or in a Kubernetes Service selector:

```yaml
# /etc/dokploy/traefik/dynamic/shop.yml  (Traefik v3 file provider; Git-tracked copy in your infra repo)
http:
  routers:
    shop:
      rule: "Host(`shop.example.com`)"
      entryPoints: [websecure]
      service: shop-active
      tls: {certResolver: letsencrypt}
  services:
    shop-active:
      loadBalancer:
        servers:
          - url: "http://shop-green:8000"     # was http://shop-blue:8000 — this line IS the switch
```

**Key terms**

| Term | Meaning |
|---|---|
| Active / idle | the colour serving users / the one kept warm for rollback or the next release |
| Smoke test | a short automated check of the idle colour before the switch |
| Switch | changing the router, DNS (slow, TTL-bound) or Service selector |
| Connection draining | letting in-flight requests on the old colour finish |

**See it on a real system**

```bash
curl -s --resolve shop.example.com:443:192.0.2.10 https://shop.example.com/version
curl -s -H 'Host: shop-green.internal.example.com' http://192.0.2.10/version     # test the idle colour
kubectl -n shop get service shop-web -o jsonpath='{.spec.selector}{"\n"}'
```

```
5e4f3a2b
9d8c7b6a
{"app":"shop-web","color":"blue"}
```

→ Users get blue (`5e4f3a2b`); green (`9d8c7b6a`) is deployed and answering on an internal name; in
Kubernetes the Service still selects `color: blue`. The switch is a single, reviewable change.

**Hands-on lab (test VM only)**

**Step 1 — Two colours.** In the lab Dokploy, run `shop-blue` and `shop-green` as two applications
on `dokploy-network`, without public domains. Route `shop.example.com` to blue with the file
provider above.

**Step 2 — Switch and break it.** Deploy a green that only works with a database column blue does not
have, switch, then switch back. Blue now fails: green's migration changed the shared schema. That is
the classic blue/green trap.

**Step 3 — Fix it.** Restore the database from the lab snapshot, redo the release with the
expand/contract migration from the "Database migrations" topic, and switch again. Then make the
switch a Git commit to the infra repository, deployed by a pipeline, so it has an author and a
revert.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Rollback to blue fails after the switch | the migration history of the DB | green ran a destructive or incompatible migration |
| Some users still on blue minutes later | `dig +short shop.example.com` | switch done in DNS; TTL and caches keep old answers |
| Sessions lost at switch | where sessions are stored | in-memory sessions per container; use a shared store |
| Traefik 404 after editing the file | `docker logs` of Traefik for file-provider errors | YAML error in the dynamic file; Traefik drops the whole file |

**Why it matters for troubleshooting.** Blue/green gives you the fastest safe mitigation there is:
"switch back, then investigate". It also gives you a live copy of the previous version to compare
against while debugging.

**Next step:** expose the new version to a few users first: canary.

### Canary releases

**Level:** [L3 · Senior]

**Concept.** Send a small share of real traffic (1–10%) to the new version, compare its error rate
and latency with the old one, and increase the share step by step only while the numbers stay
healthy. A canary limits the **blast radius** of a bad release to a few percent of requests for a
few minutes. It needs two things blue/green does not: a router that can split traffic by weight,
and **metrics per version** so you can compare.

```yaml
# Traefik v3 file provider: 90/10 weighted canary
http:
  routers:
    shop:
      rule: "Host(`shop.example.com`)"
      entryPoints: [websecure]
      service: shop-canary
      tls: {certResolver: letsencrypt}
  services:
    shop-canary:
      weighted:
        services:
          - name: shop-stable
            weight: 9
          - name: shop-next
            weight: 1
    shop-stable:
      loadBalancer: {servers: [{url: "http://shop-blue:8000"}]}
    shop-next:
      loadBalancer: {servers: [{url: "http://shop-green:8000"}]}
```

```
 steps:   1% ──(15 min, errors ≤ stable, p95 ≤ stable+10%)──► 10% ──► 50% ──► 100%
 abort:   any step worse than the criteria ──► weight 0 for shop-next (seconds) ──► investigate
```

In Kubernetes, the simplest canary is a second Deployment with the same `app` label and fewer
replicas (traffic splits by Pod count); finer control comes from the Gateway API (`HTTPRoute`
`backendRefs` with `weight`) or ingress-controller canary features (see
[Kubernetes learn module](31-learn-kubernetes.md)).

**Key terms**

| Term | Meaning |
|---|---|
| Blast radius | how many users or requests a failure can affect |
| Analysis | comparing canary vs stable on SLIs (error rate, latency) |
| Abort criteria | numbers decided **before** the release that trigger rollback |
| Sticky canary | the same user always lands on the same version (cookie), avoiding flip-flopping |

**See it on a real system.** With the Traefik access log enabled in JSON (see
[case study logs map](21-case-apache-443-dokploy.md) and the Traefik module's access-log section in
[43-traefik-and-reverse-proxies.md](43-traefik-and-reverse-proxies.md)), count status codes per
backend for the last requests. The command below assumes the access log goes to stdout; if your
static config sets `accessLog.filePath`, run the same `jq` on that file instead of `docker logs`:

```bash
docker logs --since 15m dokploy-traefik 2>/dev/null \
  | jq -r 'select(.RequestHost=="shop.example.com") | "\(.ServiceName) \(.DownstreamStatus)"' \
  | sort | uniq -c | sort -rn
```

```
   8712 shop-stable@file 200
    961 shop-next@file 200
     74 shop-next@file 502
      9 shop-stable@file 502
```

→ Stable: 9 errors in 8,721 (0.10%). Canary: 74 in 1,035 (7.1%). The canary is 70 times worse:
abort now. Without the per-service split, the overall error rate (0.85%) might have looked
acceptable. That is why canaries need metrics by version.

**Hands-on lab (test VM only)**

**Step 1 — Split traffic** 90/10 with the file above and send 1,000 requests with a curl loop; count
`/version` answers.

**Step 2 — Break it.** Make `shop-next` return 500 for one endpoint. Run the jq count above and decide
using numbers, not feelings.

**Step 3 — Abort and automate the decision.** Set the weight to 0, then write the abort criteria into
the runbook and, if you have Prometheus scraping Traefik metrics, as an alert on the canary's error
ratio (see [Observability](32-learn-performance-observability.md)).

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Canary "looks fine" but users complain later | per-version error rate | canary too small or too short to see rare paths |
| Same user flips between versions | check sticky settings | no cookie stickiness; UI and API from different versions |
| Weighted service ignored | Traefik logs at startup | YAML error, or the router still points at the old service name |

**Why it matters for troubleshooting.** A canary turns "is this release bad?" into a measurable
question answered in minutes, on a small share of traffic, with a one-line abort.

**Next step:** separate *deploying* code from *releasing* features: feature flags.

### Feature flags

**Level:** [L3 · Senior]

**Concept.** A feature flag is an `if` in the code whose condition comes from configuration, not
from a deploy: the new code ships **off**, and you turn it on for internal users, then 10% of
users, then everyone, without redeploying. Turning it off is the fastest rollback for a feature
(seconds, no pipeline). Flags range from an environment variable read at startup (simple, needs a
restart) to a flag service with per-user targeting. GitLab includes an Unleash-compatible feature
flag service (Deploy → Feature flags) that apps query through an Unleash client.

| Flag type | Lives for | Example |
|---|---|---|
| Release flag | days to weeks, then removed | `new_checkout` |
| Kill switch | permanent | `disable_pdf_export` when a dependency is down |
| Ops flag | permanent | `read_only_mode` during a database migration |
| Experiment | weeks | A/B tests (usually product, not ops) |

**Key terms**

| Term | Meaning |
|---|---|
| Dark launch | code deployed but not active |
| Targeting | turning a flag on for specific users, groups or a percentage |
| Flag debt | old flags nobody removed; every flag doubles the paths to test |
| Default | the value used when the flag service is unreachable; must be the safe one |

**See it on a real system.** Even without a flag service, you can see env-var flags of a running
service:

```bash
docker service inspect shop-web-x1y2z3 --format '{{range .Spec.TaskTemplate.ContainerSpec.Env}}{{println .}}{{end}}' | grep -E '^FEATURE_'
```

```
FEATURE_NEW_CHECKOUT=false
FEATURE_PDF_EXPORT=true
```

→ Two flags, both readable by anyone with Docker access on the host and both changed only by
redeploying the service (a Swarm env change restarts the tasks). For kill switches you want to flip
in seconds, a flag service is better.

**Hands-on lab (test VM only)**

**Step 1 — Add a kill switch** to the lab app: `FEATURE_PDF_EXPORT` read on each request from a
small config file or a GitLab feature flag via an Unleash client.

**Step 2 — Break it.** Make the PDF endpoint call an unreachable backend and hang for 30 seconds.
Watch gunicorn workers fill up and the whole app slow down (see the "requests die after 30 or 60
seconds" case in [Deployment patterns](35-deployment-patterns.md) and the ops ladder).

**Step 3 — Mitigate with the flag.** Turn the flag off: the app recovers without a deploy. Then fix
the timeout in code, and put "flip `FEATURE_PDF_EXPORT`" in the runbook as a first mitigation.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Flag change has no effect | how and when the app reads the flag | read only at startup; needs restart |
| Everything turned on when the flag service died | the client's default | unsafe default |
| Old code path breaks months later | grep for old flags | flag debt: the "off" path was never tested again |

**Why it matters for troubleshooting.** In an incident, a kill switch is a mitigation you can apply
before you understand the root cause, which is exactly what incident response asks for (section 7).

**Next step:** the hardest part of every strategy above: the database.

### Database migrations and compatibility

**Level:** [L3 · Senior]

**Concept.** Code can be rolled back in seconds; data cannot. Every strategy above runs two versions
at once for some time (rolling, canary) or relies on going back (blue/green, rollback). So every
schema change must keep the **previous version working**. The pattern is **expand/contract**
(also called parallel change), spread over several releases:

```
 release N   EXPAND     add the new column/table (nullable, with default); old code ignores it
 release N+1 MIGRATE    new code writes both old and new; backfill old rows in batches
 release N+2 SWITCH     new code reads the new column; old column still written (rollback-safe)
 release N+3 CONTRACT   stop writing the old column; later drop it (only when no version needs it)
 never:      rename or drop a column in the same release as the code that stops using it
```

Run migrations as an explicit, observable step: a separate pipeline job before the deploy, or a
Kubernetes Job or init container, never silently on app start with several replicas racing each
other. Take a backup (or confirm the last good one) before a risky migration. See
[Databases for ops](38-learn-databases-ops.md) for backups and restores.

**Key terms**

| Term | Meaning |
|---|---|
| Backward compatible | the old code works with the new schema |
| Forward compatible | the new code works with the old schema (needed if migration and deploy are separate) |
| Backfill | filling the new column for existing rows, in batches to avoid long locks |
| Lock time | how long a migration blocks reads or writes (e.g. `ALTER TABLE` on a big table) |

**See it on a real system** (lab PostgreSQL, read-only):

```bash
psql -h 192.168.56.60 -U shop -d shop -c "SELECT version, applied_at FROM schema_migrations ORDER BY applied_at DESC LIMIT 3;"
psql -h 192.168.56.60 -U shop -d shop -c "\d orders" | head -12
```

```
   version    |          applied_at
--------------+-------------------------------
 20261003_02  | 2026-10-03 09:18:40.112+00
 20261001_01  | 2026-10-01 14:02:11.731+00
 20260924_01  | 2026-09-24 13:55:02.004+00
                         Table "public.orders"
     Column     |           Type           | Collation | Nullable | Default
----------------+--------------------------+-----------+----------+---------
 id             | bigint                   |           | not null | nextval(...)
 customer_email | text                     |           |          |
 email_hash     | text                     |           |          |
```

→ The migration table (its name depends on your framework: `schema_migrations`, `alembic_version`,
`django_migrations`, `flyway_schema_history`) shows the last migration ran at 09:18, two minutes before
the 09:20 deploy in the GitLab deployment history: correlate these timestamps in every incident.
`email_hash` is new and nullable: an expand step; `customer_email` is still there, so the previous
release still works.

**Hands-on lab (test VM only)**

**Step 1 — Do it wrong.** In a lab app, rename a column and update the code in the same release.
During a rolling update, old Pods throw `column "customer_email" does not exist`.

**Step 2 — Roll back and see why it fails.** Roll back the code: the old code still fails, because the
schema change was not rolled back. Restore the lab DB from the snapshot.

**Step 3 — Do it right** in three releases with expand/contract, rolling back after each one to prove
every step is reversible.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `column "X" does not exist` only during a rollout | deployment and migration timestamps | contract step shipped together with the code change |
| Site hangs during deploy | `SELECT * FROM pg_locks` / slow query log | migration holding a table lock on a large table |
| Rollback "did not fix it" | migration history | data or schema changed irreversibly; roll forward instead |

**Why it matters for troubleshooting.** "We rolled back but it is still broken" almost always means
state changed: database schema, data, cache contents, or messages in a queue. Ask "what state did
the release change?" before assuming the rollback failed.

**Next step:** design rollback itself, so it works when you need it.

### Rollback design

**Level:** [L3 · Senior] to design, [L4 · Lead/SRE] to make it policy

**Concept.** A rollback plan is part of the change, written and tested **before** the change. There
are five kinds of "going back", from fastest to slowest; know which ones each app supports:

| Rollback type | Time | Needs | Your stack |
|---|---|---|---|
| Flip a feature flag | seconds | flag in the code | GitLab feature flags or env flags |
| Switch traffic | seconds | blue/green or canary router | Traefik file provider, Service selector |
| Redeploy previous artifact | 1–3 min | immutable, retained images | `rollback-production` job, `docker service rollback`, `kubectl rollout undo`, GitLab Re-deploy |
| Revert the commit and let the pipeline ship it | 5–15 min | working pipeline | `git revert` (section 1) |
| Restore data or a VM snapshot | 15 min to hours | tested backups | last resort; loses data written since |

The rollback **trigger** is decided in advance ("any kept site failing for more than 15 minutes", "error
rate above 2% for 5 minutes"), so nobody debates it under stress. **Roll back first, debug second**
when users are affected and a rollback path exists; roll forward only when the rollback is riskier
than the fix (for example after an irreversible migration).

**Key terms**

| Term | Meaning |
|---|---|
| Rollback trigger | the measurable condition that ends "fixing forward" |
| Rollback readiness | previous image retained, DB compatible, config versioned, procedure tested |
| Roll forward | fixing with a new release instead of going back |
| MTTR | mean time to restore; rollback speed is most of it |

**See it on a real system.** Rollback readiness, checked before a release:

```bash
# 1) is the previous release image still in Harbor? (retention could have deleted it)
docker buildx imagetools inspect harbor.example.com/shop/shop-web:v1.4.1 | grep Digest
# 2) does Kubernetes keep history to undo to?
kubectl -n shop get deployment shop-web -o jsonpath='{.spec.revisionHistoryLimit}{"\n"}'
# 3) is the Traefik dynamic config in Git, so a revert restores routing?
git -C ~/infra log --oneline -3 -- traefik/dynamic/
```

```
Digest:    sha256:0a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5
10
c4d5e6f Route api.example.com to Apache on 192.0.2.10:81
b3c4d5e Add shop canary weights
a2b3c4d Initial Traefik dynamic config from web01
```

→ Previous image exists, Kubernetes keeps 10 revisions, and routing is versioned in Git. All three
rollback paths are open. If any line came back empty, fix that **before** the release, not during
the incident.

**Hands-on lab (test VM only)**

**Step 1 — Time each rollback type** on the lab: flag flip, Traefik switch, `rollback-production`,
`git revert` through the pipeline. Write the measured times into the app's runbook.

**Step 2 — Break it.** Set Harbor retention to keep only the latest 1 tag, release twice, then try to
roll back: `manifest unknown`. Rollback readiness failed silently weeks earlier.

**Step 3 — Fix it** with a retention rule that always keeps `v*` tags, and add the readiness check
above as a job that runs before `deploy-production`.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Rollback image missing | Harbor tag list | retention deleted it |
| `kubectl rollout undo` goes to an unexpected version | `kubectl rollout history` | undo goes to the previous **revision**, which may be a config-only change |
| Rollback restores app but not routing | `git log` of the Traefik config | routing changed by hand outside Git |
| Rollback works on staging, not production | compare procedures | the production path was never tested |

**Why it matters for troubleshooting.** The best incident is the one that lasts two minutes because
the rollback was boring. Rollback design is the step where a senior engineer saves the most
downtime per hour spent.

**Next step:** make the servers themselves reproducible with Ansible (section 4).

---

## 4. Ansible

> 📚 **Study path:** 1) KodeKloud: *Ansible Basics Course* — Configuration and Basic Concepts → Inventory → Variables and Facts → Playbooks (+ verifying, ansible-lint) → Conditionals/Loops → Modules & Plugins → Handlers, Roles and Collections → Templates (Jinja2) ([course](https://kodekloud.com/courses/ansible-for-the-absolute-beginners-course)) · 2) Note: this section, topic by topic · 3) Video: Jeff Geerling *Ansible 101* ([playlist](https://www.youtube.com/playlist?list=PL2_OBreMn7FqZkvMYt6ATmgC0KAGGJNAN)) or KodeKloud *Ansible for the Absolute Beginners* ([playlist](https://www.youtube.com/playlist?list=PL2We04F3Y_42_PN52bT_U5o_lt6uPQqqq)) · 4) Practice: KodeKloud [Ansible playground](https://kodekloud.com/playgrounds/playground-ansible), then the Ops Ladder drill in this section: Docker with your `daemon.json` on target1 and target2.

Every server in the Apache to Dokploy story was configured by hand: packages, `ports.conf`, the
Docker `daemon.json`, the CA files, UFW rules. Ansible writes those steps down as YAML and runs
them over SSH, the same way every time, on one server or fifty. No agent is installed on the
targets: Ansible needs SSH and Python there, and runs from your workstation (`ctrl` in the lab) or
from a CI job.

```
 ctrl (192.168.56.10)                                    targets
 ┌──────────────────────────┐   SSH (key, as ops)   ┌──────────────────────┐
 │ ansible.cfg              │ ────────────────────► │ target1 192.168.56.51 │  python3 runs the
 │ inventory/hosts.yml      │  copies a small       │ target2 192.168.56.52 │  module, returns
 │ group_vars/ host_vars/   │  Python module,       │ runner01 ...          │  JSON: ok/changed/
 │ site.yml, roles/         │  runs it with sudo    └──────────────────────┘  failed
 └──────────────────────────┘
```

### Inventory and ad-hoc commands

**Level:** [L1 · Junior] to run, [L3 · Senior] to structure

**Concept.** The **inventory** lists your hosts and groups them (`docker_hosts`, `runners`,
`k8s_nodes`). Groups get shared variables from `group_vars/GROUP.yml`, single hosts from
`host_vars/HOST.yml`. **Ad-hoc commands** run one module against a group from the command line:
perfect for read-only questions across many servers ("which kernel?", "is Apache still running
anywhere?").

```yaml
# inventory/hosts.yml
all:
  vars:
    ansible_user: ops
  children:
    docker_hosts:
      hosts:
        target1: {ansible_host: 192.168.56.51}
        target2: {ansible_host: 192.168.56.52}
    runners:
      hosts:
        runner01: {ansible_host: 192.168.56.21}
    legacy_web:
      hosts:
        web01: {ansible_host: 192.0.2.10}
```

```ini
# ansible.cfg (in the repository root; Ansible reads ./ansible.cfg first)
[defaults]
inventory = inventory/hosts.yml
forks = 10
host_key_checking = True
callback_result_format = yaml
retry_files_enabled = False

[ssh_connection]
pipelining = True
```

**Key terms**

| Term | Meaning |
|---|---|
| Module | the unit of work (`apt`, `copy`, `template`, `systemd_service`, `user`, `ufw`); use full names like `ansible.builtin.apt` |
| Ad-hoc | `ansible PATTERN -m MODULE -a ARGS` |
| Pattern | which hosts: `all`, a group, a host, `docker_hosts:!target2` |
| `-b` / `become` | run with sudo |
| Facts | data gathered from each host (`ansible_distribution`, `ansible_default_ipv4`...) |
| `ansible-inventory --graph` | shows groups and hosts as Ansible sees them |

**See it on a real system** (from `ctrl`, read-only):

```bash
ansible-inventory --graph
ansible all -m ansible.builtin.ping
ansible docker_hosts -m ansible.builtin.command -a 'uname -r'
ansible all -b -m ansible.builtin.shell -a 'ss -ltnp | grep -E ":(80|443|81|444) " || true'
ansible target1 -m ansible.builtin.setup -a 'filter=ansible_distribution*'
```

```
@all:
  |--@ungrouped:
  |--@docker_hosts:
  |  |--target1
  |  |--target2
  |--@runners:
  |  |--runner01
  |--@legacy_web:
  |  |--web01
target1 | SUCCESS => {
    "ansible_facts": {"discovered_interpreter_python": "/usr/bin/python3"},
    "changed": false,
    "ping": "pong"
}
target2 | UNREACHABLE! => {
    "changed": false,
    "msg": "Failed to connect to the host via ssh: ssh: connect to host 192.168.56.52 port 22: Connection timed out",
    "unreachable": true
}
target1 | CHANGED | rc=0 >>
6.8.0-45-generic
web01 | CHANGED | rc=0 >>
LISTEN 0 511 *:81  *:*  users:(("apache2",pid=1123,fd=4))
LISTEN 0 511 *:444 *:*  users:(("apache2",pid=1123,fd=6))
```

→ `ping` here is not ICMP: it proves SSH login and a working Python. `UNREACHABLE` is an SSH-layer
failure (timeout = network or firewall; `Permission denied (publickey)` = keys; see
[SSH reference](09-ssh-remote-access.md)). `CHANGED` on a `command` is Ansible being honest that it
cannot know whether an arbitrary command changed something. The last command answers "where is
Apache listening?" across the whole estate in one line: on web01 it is on 81 and 444, as you left it.

**Hands-on lab (test VM only)**

**Step 1 — Build the inventory** for ctrl, target1, target2 and runner01; copy your SSH key with
`ssh-copy-id ops@192.168.56.51`; run `ansible all -m ansible.builtin.ping` until all are green.

**Step 2 — Break it.** Change target2's `ansible_host` to a wrong IP, and on target1 remove `ops`
from sudoers. Run `ansible all -b -m ansible.builtin.ping`: one `UNREACHABLE` (network) and one
`FAILED` with `Missing sudo password` (privilege).

**Step 3 — Fix it** and write down the difference: unreachable means Ansible never got in; failed
means it got in and the task failed.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `UNREACHABLE! ... Connection timed out` | `nc -vz HOST 22` | routing, firewall, host down |
| `UNREACHABLE! ... Permission denied (publickey)` | `ssh -v ops@HOST` | key not installed, wrong user |
| `FAILED! ... Missing sudo password` | `ssh ops@HOST sudo -n true` | no passwordless sudo; use `-K` or fix sudoers |
| `/usr/bin/python3: not found` | `ssh HOST which python3` | minimal image; install python3 with the `raw` module first |
| `Could not match supplied host pattern` | `ansible-inventory --graph` | typo in group name or wrong inventory file |

**Why it matters for troubleshooting.** Ad-hoc commands turn "check this on every server" from an
hour of SSH sessions into one command, which is often the fastest way to scope an incident ("which
hosts have the bad config?").

**Next step:** write repeatable changes as playbooks, and learn the property that makes them safe.

### Playbooks and idempotency

**Level:** [L3 · Senior] ([L1 · Junior] to run an existing one)

**Concept.** A **playbook** is a YAML list of **plays**; each play maps a group of hosts to an
ordered list of **tasks**; each task calls one module with arguments. The central property is
**idempotency**: running the playbook twice gives the same result as running it once, and the
second run reports `changed=0`. Modules achieve this by describing **desired state**
(`state: present`, `state: started`) instead of actions ("run apt install"). Idempotency is what lets
you re-run a playbook after a half-failed run, or run it every night to correct drift.

```
 imperative (shell script)                 declarative (Ansible module)
 apt-get install -y apache2                ansible.builtin.apt: {name: apache2, state: present}
 echo "Listen 81" >> ports.conf  ← appends ansible.builtin.lineinfile:
   a duplicate line every run                path: /etc/apache2/ports.conf
                                             regexp: '^Listen 80$'
                                             line: 'Listen 81'          ← same result every run
```

**Key terms**

| Term | Meaning |
|---|---|
| Play | `hosts:` + `tasks:` (+ vars, handlers, roles) |
| Task status | `ok` (already as desired), `changed`, `failed`, `skipped`, `unreachable` |
| `register` | save a task's result in a variable |
| `changed_when` / `failed_when` | define change and failure for `command`/`shell` tasks |
| `creates` / `removes` | skip a command if a file exists / does not exist |
| PLAY RECAP | the per-host summary at the end of a run |

**See it on a real system.** The recap is the line you read first:

```bash
ansible-playbook docker.yml --limit target1
ansible-playbook docker.yml --limit target1          # second run: must report changed=0
```

```
PLAY RECAP *********************************************************************
target1                    : ok=11   changed=7    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
PLAY RECAP *********************************************************************
target1                    : ok=11   changed=0    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

→ First run: seven tasks changed the host. Second run: zero, so the playbook is idempotent. If the
second run shows `changed=1` again, find that task: it either uses `command`/`shell` without
`changed_when`, or it rewrites a file with content that changes on every run (a timestamp in a
template, for example).

**Hands-on lab (test VM only)**

**Step 1 — Write a tiny playbook** that installs `chrony` and ensures it is started. Run it twice and
confirm `changed=0` on the second run.

**Step 2 — Break idempotency on purpose.** Add a task
`ansible.builtin.shell: echo "server 192.0.2.123 iburst" >> /etc/chrony/chrony.conf`. Run three
times: the file now has three identical lines and the recap always says `changed=1`.

**Step 3 — Fix it** with `ansible.builtin.lineinfile` (or a template), clean the duplicates, and
confirm two clean runs with `changed=0`.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| `changed` on every run | `ansible-playbook ... --diff` and look for the task | `command`/`shell` without `changed_when`, or non-deterministic template |
| Duplicate lines in config files | `grep -c` on the target | shell append instead of `lineinfile`/`template` |
| Run fails half-way, re-run fails differently | read the first failure only | a task assumed the previous one succeeded; make tasks independent of order where possible |

**Why it matters for troubleshooting.** A non-idempotent playbook cannot be safely re-run during an
incident, which is exactly when you need it most. "Re-run the playbook" should always be a safe,
boring action.

**Next step:** restart services only when their config actually changed: handlers.

### Handlers

**Level:** [L3 · Senior]

**Concept.** A **handler** is a task that runs only when another task **notifies** it **and that
task reported `changed`**. Handlers run once at the end of the play (or at `meta: flush_handlers`),
even if several tasks notified them. That is how you restart Docker or reload Apache only when
`daemon.json` or a vhost actually changed, and only once.

```yaml
tasks:
  - name: Write daemon.json
    ansible.builtin.template: {src: daemon.json.j2, dest: /etc/docker/daemon.json}
    notify: Restart docker
handlers:
  - name: Restart docker
    ansible.builtin.systemd_service: {name: docker, state: restarted}
```

**Key terms**

| Term | Meaning |
|---|---|
| `notify` | name of the handler(s) to trigger when the task changes something |
| `listen` | handlers can subscribe to a topic name, so several handlers run for one notify |
| `meta: flush_handlers` | run pending handlers now instead of at the end |
| `--force-handlers` | run notified handlers even if a later task fails |

**See it on a real system.** In the run output, handlers appear under `RUNNING HANDLER`:

```
TASK [Write daemon.json (validated before it replaces the old one)] *************
changed: [target1]

RUNNING HANDLER [Restart docker] ************************************************
changed: [target1]
```

→ The template changed, so Docker restarted once. On the second run the template is `ok`, and the
handler section does not appear at all.

> ⚠️ Restarting Docker restarts every container on the host (unless `live-restore` is enabled,
> which is **not** compatible with Swarm mode, so not available on a Dokploy host). On a production
> Docker or Dokploy host, run Docker-config playbooks in a maintenance window, one host at a time
> (`serial: 1`), and use `--check --diff` first.

**Hands-on lab (test VM only)**

**Step 1 — Notify a handler** from the daemon.json template task and run twice.

**Step 2 — Break it.** Add a failing task **after** the template task (`ansible.builtin.command:
/bin/false`) and change the DNS servers. The template changes, the play fails, and the handler never
runs: Docker keeps the **old** config in memory while the file on disk is new. That mismatch is a
time bomb for the next unrelated restart.

**Step 3 — Fix it.** Re-run with `--force-handlers` (or add `meta: flush_handlers` right after the
template task) and verify with `docker info` that the running config matches the file.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Config file updated, service still uses old config | compare file mtime with service start time (`systemctl show -p ActiveEnterTimestamp UNIT`) | handler skipped because the play failed later |
| Handler never runs | `--diff` on the notifying task | the task reported `ok`, or the handler name does not match `notify` exactly |
| Service restarted twice | look for a `notify` and an explicit restart task | duplicate restart logic |

**Why it matters for troubleshooting.** "It broke after a reboot last night but nobody changed
anything" is often a config written weeks ago by a run whose handler never fired. Compare file
change times with service start times.

**Next step:** make one playbook work for many hosts with variables.

### Variables and precedence

**Level:** [L3 · Senior]

**Concept.** Variables let one playbook configure lab and production differently: DNS servers, log
sizes, users. Ansible merges variables from many places, and when the same name is set twice, the
**higher-precedence** place wins. You do not need all 22 levels; you need this order (lowest to
highest) and two habits: put defaults in **role defaults**, environment-specific values in
**group_vars**, and use `-e` (extra vars, always wins) only for one-off overrides.

```
 lowest ──────────────────────────────────────────────────────────────────────► highest
 role defaults < group_vars/all < group_vars/GROUP < host_vars/HOST < play vars
               < role vars < task vars < set_fact / register < extra vars (-e)
```

```yaml
# group_vars/all.yml        — company-wide
docker_dns_servers: [192.0.2.53, 192.0.2.54]
docker_log_max_size: "10m"
docker_log_max_file: "3"

# group_vars/runners.yml    — CI runners create lots of short-lived logs
docker_log_max_size: "50m"
docker_log_max_file: "2"
```

**Key terms**

| Term | Meaning |
|---|---|
| `group_vars/` / `host_vars/` | directories next to the inventory or playbook, one file per group/host |
| Role defaults | `roles/NAME/defaults/main.yml`, lowest precedence, meant to be overridden |
| Extra vars | `-e key=value` or `-e @file.yml`; highest precedence |
| `hostvars['target1']` | read another host's variables |
| Magic variables | `inventory_hostname`, `group_names`, `ansible_check_mode` |

**See it on a real system.** Ask Ansible what it will use, instead of guessing:

```bash
ansible-inventory --host runner01 --yaml | grep -A3 docker_
ansible runner01 -m ansible.builtin.debug -a 'var=docker_log_max_size'
ansible target1 -m ansible.builtin.debug -a 'var=docker_log_max_size'
```

```
docker_dns_servers:
- 192.0.2.53
- 192.0.2.54
docker_log_max_file: '2'
docker_log_max_size: 50m
runner01 | SUCCESS => {
    "docker_log_max_size": "50m"
}
target1 | SUCCESS => {
    "docker_log_max_size": "10m"
}
```

→ runner01 is in `runners`, so `group_vars/runners.yml` overrides `all.yml`; target1 only has the
`all` value. When a value surprises you, this is the first command to run.

**Hands-on lab (test VM only)**

**Step 1 — Layer the values** exactly as above and confirm with `debug`.

**Step 2 — Break it.** Define `docker_log_max_size: "1m"` in the play's `vars:` "temporarily" and
forget it. Every host now gets 1m, whatever group_vars say, and runner logs rotate away before you
can read them.

**Step 3 — Fix it** by removing the play var, and adopt the rule: plays and roles hold no
environment-specific values; group_vars do.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Host gets the "wrong" value | `ansible HOST -m debug -a var=NAME` | a higher-precedence definition wins |
| `'docker_dns_servers' is undefined` | `ansible-inventory --host HOST` | file in the wrong `group_vars` directory, or host not in that group |
| Number treated as string or vice versa | quote values in YAML deliberately | `"3"` vs `3`; daemon.json needs strings for log-opts |

**Why it matters for troubleshooting.** Most "Ansible did something strange" reports are precedence
surprises. The debug command answers them in seconds.

**Next step:** turn variables into config files: templates.

### Templates with Jinja2

**Level:** [L3 · Senior]

**Concept.** The `template` module renders a **Jinja2** file with your variables and writes it to the
host. Use it for whole files you own (`daemon.json`, a Traefik dynamic file, an Apache vhost);
use `lineinfile`/`blockinfile` only for small edits to files you do not own. Two template features
protect production: `backup: true` (keeps the previous file) and `validate:` (runs a checker on the
rendered temp file and refuses to install it if the checker fails).

```jinja
{# templates/daemon.json.j2 — rendered per host #}
{
  "dns": {{ docker_dns_servers | to_json }},
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "{{ docker_log_max_size }}",
    "max-file": "{{ docker_log_max_file }}"
  }
}
```

| Config file | `validate:` command |
|---|---|
| `/etc/docker/daemon.json` | `dockerd --validate --config-file %s` (Docker 23+) |
| Apache vhost | `apache2ctl -t -f %s` only works for a full config; validate after deploy with `apache2ctl configtest` and a handler |
| `/etc/sudoers.d/FILE` | `visudo -cf %s` |
| Nginx | `nginx -t -c %s` (full config) |
| sshd | `sshd -t -f %s` |

**Key terms**

| Term | Meaning |
|---|---|
| `{{ var }}` / `{% if %}` / `{# #}` | expression, statement, comment |
| Filters | `to_json`, `to_nice_yaml`, `default('x')`, `join(',')`, `regex_replace` |
| `ansible_managed` | a header string marking the file as managed ("do not edit by hand") |
| `{% raw %}` | output literal braces (for Go templates like `docker info --format`) |

**See it on a real system.** `--check --diff` shows the rendered difference before anything changes:

```bash
ansible-playbook docker.yml --limit target1 --check --diff --tags config
```

```
TASK [Write daemon.json (validated before it replaces the old one)] *************
--- before: /etc/docker/daemon.json
+++ after: /home/ops/.ansible/tmp/ansible-local-2201/tmpk3x/daemon.json.j2
@@ -1,5 +1,5 @@
 {
-  "dns": ["8.8.8.8"],
+  "dns": ["192.0.2.53", "192.0.2.54"],
   "log-driver": "json-file",
   "log-opts": {
changed: [target1]
```

→ Someone set `8.8.8.8` by hand on target1 (drift); the playbook will put back your internal
resolvers. You see exactly which line changes, on which host, before it happens.

**Hands-on lab (test VM only)**

**Step 1 — Render** daemon.json for target1 and runner01 and compare (`--check --diff`).

**Step 2 — Break it.** Add a trailing comma after the last `log-opts` entry in the template and run
without `validate:`: the file is installed, the handler restarts Docker, and Docker fails to start
(`unable to configure the Docker daemon with file /etc/docker/daemon.json: invalid character '}'
looking for beginning of object key string`). Now add `validate:` and run again: the task fails with
`failed to validate`, and the **old, working** file stays in place.

**Step 3 — Fix** the template and restore Docker (`backup: true` left the previous file next to
the new one as `daemon.json.NNNN.DATE~`).

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| Service fails after a template change | `journalctl -u UNIT -n 30` | syntax error rendered; add `validate:` |
| `AnsibleUndefinedVariable: 'x' is undefined` | `ansible HOST -m debug -a var=x` | missing variable; give it a role default |
| Go template braces break the task | quote and wrap with `{% raw %}` | Jinja tries to render `{{.Field}}` |

**Why it matters for troubleshooting.** `validate:` plus `backup:` turns "the playbook took down
Docker" into "the playbook refused a bad file". It is the IaC version of `apache2ctl configtest`
before every reload.

**Next step:** package everything into a reusable unit: a role.

### Roles and the Docker playbook

**Level:** [L3 · Senior]

**Concept.** A **role** is a standard directory layout for tasks, handlers, templates, defaults and
files that belong together, so `site.yml` can say "these hosts get the `docker` role". Roles are
shared through Git or Ansible Galaxy; **collections** bundle modules and roles (for example
`community.docker`, `community.general`, `ansible.posix`).

This is the Ops Ladder L3 drill: install Docker with your `daemon.json` (internal DNS servers and
log rotation) on a fresh VM. First as one complete playbook, then the same thing as a role.

```yaml
# docker.yml — Docker Engine from Docker's apt repo + our daemon.json (Ubuntu 22.04/24.04)
---
- name: Install Docker Engine with our daemon.json
  hosts: docker_hosts
  become: true
  vars:
    docker_dns_servers: [192.0.2.53, 192.0.2.54]     # normally in group_vars
    docker_log_max_size: "10m"
    docker_log_max_file: "3"
    docker_users: [ops]
    docker_arch_map: {x86_64: amd64, aarch64: arm64}

  pre_tasks:
    - name: Refuse anything that is not Ubuntu
      ansible.builtin.assert:
        that: ansible_distribution == "Ubuntu"
        fail_msg: "Ubuntu only, found {{ ansible_distribution }}"
      tags: [always]

  tasks:
    - name: Remove distro packages that conflict with Docker CE (never target Kubernetes nodes with this play)
      ansible.builtin.apt:
        name: [docker.io, docker-doc, docker-compose, docker-compose-v2, podman-docker, containerd, runc]
        state: absent
      tags: [packages]

    - name: Install prerequisites
      ansible.builtin.apt:
        name: [ca-certificates, curl]
        state: present
        update_cache: true
        cache_valid_time: 3600
      tags: [packages]

    - name: Create the apt keyrings directory
      ansible.builtin.file:
        path: /etc/apt/keyrings
        state: directory
        mode: "0755"
      tags: [packages]

    - name: Download Docker's apt signing key
      ansible.builtin.get_url:
        url: https://download.docker.com/linux/ubuntu/gpg
        dest: /etc/apt/keyrings/docker.asc
        mode: "0644"
      tags: [packages]

    - name: Add Docker's apt repository
      ansible.builtin.apt_repository:
        repo: >-
          deb [arch={{ docker_arch_map[ansible_architecture] }} signed-by=/etc/apt/keyrings/docker.asc]
          https://download.docker.com/linux/ubuntu {{ ansible_distribution_release }} stable
        filename: docker
        state: present
      tags: [packages]

    - name: Install Docker Engine, CLI, containerd and plugins
      ansible.builtin.apt:
        name: [docker-ce, docker-ce-cli, containerd.io, docker-buildx-plugin, docker-compose-plugin]
        state: present
        update_cache: true
      tags: [packages]

    - name: Create /etc/docker
      ansible.builtin.file:
        path: /etc/docker
        state: directory
        mode: "0755"
      tags: [config]

    - name: Write daemon.json (validated before it replaces the old one)
      ansible.builtin.template:
        src: templates/daemon.json.j2
        dest: /etc/docker/daemon.json
        owner: root
        group: root
        mode: "0644"
        backup: true
        validate: dockerd --validate --config-file %s
      notify: Restart docker
      tags: [config]

    - name: Enable and start Docker
      ansible.builtin.systemd_service:
        name: docker
        enabled: true
        state: started
      tags: [service]

    - name: Let listed users run docker (the docker group is root-equivalent)
      ansible.builtin.user:
        name: "{{ item }}"
        groups: docker
        append: true
      loop: "{{ docker_users }}"
      tags: [users]

  handlers:
    - name: Restart docker
      ansible.builtin.systemd_service:
        name: docker
        state: restarted

  post_tasks:
    - name: Apply pending restarts before verifying
      ansible.builtin.meta: flush_handlers

    - name: Read the effective logging driver
      ansible.builtin.command: "docker info --format '{% raw %}{{.LoggingDriver}}{% endraw %}'"
      register: docker_logdriver
      changed_when: false
      tags: [verify]

    - name: Read the DNS servers a container on the default bridge gets
      ansible.builtin.command: docker run --rm busybox:1.36 cat /etc/resolv.conf
      register: docker_resolv
      changed_when: false
      when: not ansible_check_mode
      tags: [verify]

    - name: Fail if the running config does not match what we asked for
      ansible.builtin.assert:
        that:
          - docker_logdriver.stdout == "json-file"
          - docker_resolv.stdout is search(docker_dns_servers[0])
        success_msg: "Docker uses json-file and {{ docker_dns_servers | join(', ') }}"
      when: not ansible_check_mode
      tags: [verify]
```

The same playbook as a role, which is how it should live in your infrastructure repository:

```
roles/docker/
├── defaults/main.yml      docker_dns_servers, docker_log_max_size, docker_log_max_file, docker_users
├── tasks/main.yml         the tasks above (packages, config, service, users, verify)
├── handlers/main.yml      Restart docker
├── templates/daemon.json.j2
└── meta/main.yml          supported platforms, dependencies
site.yml:
  - hosts: docker_hosts
    become: true
    roles: [docker]
```

Create the skeleton with `ansible-galaxy role init --init-path roles docker`, move the tasks, and keep only
**defaults** in the role; the real DNS servers belong in `group_vars`.

**Key terms**

| Term | Meaning |
|---|---|
| `roles/NAME/tasks/main.yml` | entry point of the role |
| `defaults/` vs `vars/` | overridable defaults vs high-precedence role internals |
| `meta: dependencies` | roles this role needs first (for example a `ca_trust` role before `docker`) |
| `requirements.yml` | list of roles and collections to install with `ansible-galaxy install -r` |
| ansible-lint | linter for playbooks and roles; run it in CI |

**See it on a real system.** The verification lines from a first run on a fresh target:

```
TASK [Read the effective logging driver] *****************************************
ok: [target1]

TASK [Fail if the running config does not match what we asked for] **************
ok: [target1] => {
    "changed": false,
    "msg": "Docker uses json-file and 192.0.2.53, 192.0.2.54"
}

PLAY RECAP ***********************************************************************
target1                    : ok=16   changed=9    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

→ The playbook does not only install: it **proves** the running daemon uses the config (a handler that
silently failed would make the assert fail). On the default bridge a container's
`/etc/resolv.conf` lists the `dns` servers directly; on user-defined networks such as
`dokploy-network` it shows `127.0.0.11`, Docker's embedded DNS, which forwards to those same
servers (see the ops ladder blind spot and [Docker learn module](30-learn-docker.md)).

**Hands-on lab (test VM only)** — Ops Ladder L3 drill.

**Step 1 — Run** `ansible-playbook docker.yml --check --diff` against fresh target1 and target2
snapshots (check mode will fail at Docker-dependent tasks on a fresh host; that is expected, and
why the verify tasks have `when: not ansible_check_mode`), then for real. Run again: `changed=0`.

**Step 2 — Break it.** On target2 edit `/etc/docker/daemon.json` by hand to use `8.8.8.8` and restart
Docker (simulating drift), and on target1 block outbound HTTPS to `download.docker.com` with UFW.
Run the playbook: target2 is corrected and restarted; target1 fails at the key download with a
timeout.

**Step 3 — Fix and convert.** Remove the UFW block (or point the repo at an internal apt mirror),
convert the playbook into `roles/docker`, add `ansible-lint` and `ansible-playbook --syntax-check` as
a CI job, and commit it. You now have the first role of your infrastructure repository.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `Failed to update apt cache: W:GPG error ... NO_PUBKEY` | `ls -l /etc/apt/keyrings/` | key missing or wrong `signed-by` path |
| `Could not get lock /var/lib/dpkg/lock-frontend` | `ps aux | grep -E 'apt|unattended'` on the target | unattended-upgrades running; retry, or wait with `lock_timeout` |
| `Unable to locate package docker-ce` | the repo line in `/etc/apt/sources.list.d/docker.list` | wrong release codename or architecture |
| Docker restart fails after the run | `journalctl -u docker -n 30` | daemon.json error (use `validate:`), or conflicting `-H`/`--dns` flags in a systemd override |

**Why it matters for troubleshooting.** When a Docker host misbehaves, "re-run the role with
`--check --diff`" shows every way it drifted from the known-good state, in one screen. That is
often faster than inspecting the host by hand.

**Next step:** the secrets this playbook will soon need (Harbor robot, runner token): Ansible Vault.

### Ansible Vault

**Level:** [L3 · Senior]

**Concept.** **Ansible Vault** encrypts variables or whole files with AES-256 so secrets can live in
the same Git repository as the playbooks. Ansible decrypts them in memory at run time when you give
it the vault password. A clean convention: keep `vault_` prefixed variables in an encrypted
`vault.yml` and reference them from a plain `vars.yml`, so `grep` still shows where every secret is
used.

```
group_vars/runners/
├── vars.yml      runner_token: "{{ vault_runner_token }}"        (plain, greppable)
└── vault.yml     $ANSIBLE_VAULT;1.2;AES256;ops                   (encrypted)
                  vault_runner_token: glrt-...
```

**Key terms**

| Term | Meaning |
|---|---|
| `ansible-vault create / edit / view FILE` | work with an encrypted file (opens `$EDITOR`) |
| `ansible-vault encrypt_string` | encrypt one value to paste into a YAML file |
| `--vault-id LABEL@SOURCE` | password source, e.g. `ops@prompt` or `ops@~/.vault-pass` |
| `no_log: true` | hide a task's arguments and results from output (use on tasks handling secrets) |

**See it on a real system**

```bash
ansible-vault create --vault-id ops@prompt group_vars/runners/vault.yml
head -2 group_vars/runners/vault.yml
ansible-vault view --vault-id ops@prompt group_vars/runners/vault.yml
ansible-playbook runners.yml --vault-id ops@prompt --check --diff
```

```
$ANSIBLE_VAULT;1.2;AES256;ops
62383637396532356135313063336364353862636132383961393031623735366335383934623030
vault_runner_token: glrt-XXXXXXXXXXXXXXXXXXXX
```

→ The file in Git is ciphertext with a label (`ops`), so it is safe to commit **if** the password is
not. The password goes in your password manager, and for CI in a masked, protected GitLab variable
of type File, passed as `--vault-password-file "$ANSIBLE_VAULT_PASS_FILE"`.

**Hands-on lab (test VM only)**

**Step 1 — Encrypt** a fake Harbor robot secret and use it in a task that writes
`/root/.docker/config.json` on target1, with `no_log: true` on that task.

**Step 2 — Break it.** Remove `no_log` and run with `-v`: the secret appears in the output. Then commit
an unencrypted `vault.yml` by mistake and watch gitleaks (section 1) catch it in CI.

**Step 3 — Fix it.** Restore `no_log`, rotate the fake secret, re-encrypt with `ansible-vault rekey`
when someone with the password leaves the team.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `Attempting to decrypt but no vault secrets found` | how the playbook was called | no `--vault-id` / `--ask-vault-pass` |
| `Decryption failed (no vault secrets were found that could decrypt)` | `head -1 FILE` (label) | wrong password or label |
| Secret visible in CI log | the task's `no_log` | missing `no_log: true`; rotate the secret |

**Why it matters for troubleshooting.** Secrets that live in a known place, encrypted and versioned,
can be rotated in minutes during an incident. Secrets scattered over servers and laptops cannot.
Section 6 compares Vault with the alternatives.

**Next step:** run changes safely: check mode, diff and tags.

### Check mode, diff and tags

**Level:** [L2 · Mid] to use every time

**Concept.** `--check` runs the playbook without changing anything (modules report what **would**
change); `--diff` shows the content differences for files. Together they are Ansible's dry run, and
they belong in every change request (section 7). **Tags** select parts of a playbook (`--tags
config`), and `--limit` selects hosts. Combine them to make the smallest possible change: one task
group, one host first.

```bash
ansible-playbook site.yml --list-hosts --limit docker_hosts          # who would be touched
ansible-playbook site.yml --list-tasks --tags config                 # which tasks
ansible-playbook site.yml --check --diff --limit target1 --tags config
ansible-playbook site.yml --limit target1 --tags config              # canary host first
ansible-playbook site.yml --limit 'docker_hosts:!target1' --tags config
```

**Key terms**

| Term | Meaning |
|---|---|
| `--check` / `--diff` | dry run / show file differences |
| `check_mode: false` on a task | always run it (for read-only commands needed by later tasks) |
| `ansible_check_mode` | variable true during `--check` |
| `--limit` | host pattern restriction |
| `serial: 1` / `serial: "25%"` | rolling execution in batches inside a play |
| `-vvv` | verbose: shows SSH commands and module arguments (careful with secrets) |

**See it on a real system**

```
PLAY [Install Docker Engine with our daemon.json] ********************************
TASK [Write daemon.json (validated before it replaces the old one)] *************
changed: [target1]
RUNNING HANDLER [Restart docker] ************************************************
changed: [target1]
PLAY RECAP ***********************************************************************
target1                    : ok=5    changed=2    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

→ In check mode, `changed` means "would change". Here the run would rewrite `daemon.json` and
restart Docker on target1: a restart is a service interruption, which belongs in the change request.
Tasks outside the `config` tag are not run and not counted at all; `ok=5` is fact gathering, the
`always`-tagged assert, the directory, the template and the handler.

**Hands-on lab (test VM only)**

**Step 1 — Dry run** the Docker role against both targets and read every `changed`.

**Step 2 — Break it.** Run the real playbook against `all` without `--limit` after changing the DNS
variable: every Docker host restarts at once, including runner01 in the middle of a CI job.

**Step 3 — Fix the habit**: add `serial: 1` to plays that restart services, always run
`--check --diff` first, then one host, then the rest.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Check mode fails at a task that needs an earlier change | the error and the task order | expected on fresh hosts; guard with `when: not ansible_check_mode` |
| Check mode says "ok" but the real run changes things | the module used | `command`/`shell` are skipped in check mode unless `check_mode: false` |
| A run touched hosts you did not intend | `--list-hosts` | missing `--limit`, or a group containing more hosts than you thought |

**Why it matters for troubleshooting.** The worst automation incidents are "correct change, wrong
scope". `--list-hosts`, `--check --diff` and `serial` are the three habits that prevent them.

**Next step:** Ansible configures servers that already exist; Terraform creates them (section 5).

---

## 5. Terraform

> 📚 **Study path:** 1) KodeKloud: *Terraform Basics Training Course* — Getting Started → Terraform Basics → Terraform State → Working with Terraform → Terraform with AWS → Remote State (S3 backend, locking) → Import/Taint/Debugging → Modules ([course](https://kodekloud.com/courses/terraform-basics-training-course)) · 2) Note: this section, then [Cloud & AWS](36-learn-cloud-aws.md) for the AWS side · 3) Video: KodeKloud *What is Terraform? | Introduction To Terraform Basics* ([YouTube](https://www.youtube.com/watch?v=mzgfHmDRamk)) · 4) Practice: *Terraform Challenges* (free) ([course](https://kodekloud.com/courses/terraform-challenges)), then the Proxmox or AWS labs below.

Ansible changes what is **inside** servers that exist. Terraform creates and changes the
**infrastructure** itself: virtual machines on Proxmox or vSphere, AWS VPCs, security groups,
EC2 instances, DNS records, even GitLab projects. You describe the desired infrastructure in HCL
files, Terraform compares it with reality and with its **state** file, shows a **plan**, and
applies only the difference. The combination is the standard on-prem pattern: Terraform creates
`target3`, outputs its IP, Ansible installs Docker on it.

> Terraform 1.6+ is published under the BUSL licence; **OpenTofu** is the open-source fork with the
> same language and commands (`tofu init`, `tofu plan`). Everything in this section applies to both;
> GitLab's own CI components now use OpenTofu.

### Providers and resources

**Level:** [L3 · Senior]

**Concept.** A **provider** is a plugin that knows one API (Proxmox, vSphere, AWS, GitLab,
Cloudflare). A **resource** is one object that provider manages (`aws_instance`,
`proxmox_virtual_environment_vm`). A **data source** reads something that exists but is not managed
by this configuration (the latest Ubuntu AMI, an existing network). Terraform builds a dependency
graph from references between them and creates things in the right order.

```hcl
# versions.tf
terraform {
  required_version = ">= 1.9"
  required_providers {
    proxmox = { source = "bpg/proxmox", version = "~> 0.70" }   # pin what you tested
    aws     = { source = "hashicorp/aws", version = "~> 6.0" }
  }
}

# proxmox.tf — one Ubuntu VM cloned from template 9000 (cloud-init), on-prem
provider "proxmox" {
  endpoint  = "https://pve1.example.com:8006/"
  api_token = var.pve_api_token        # "terraform@pve!ci=SECRET", from an env var, never in Git
  insecure  = false                    # trust your private CA instead (system store or SSL_CERT_FILE)
}

resource "proxmox_virtual_environment_vm" "target" {
  for_each  = var.targets              # {"target3" = "192.168.56.53"}
  name      = each.key
  node_name = "pve1"
  clone { vm_id = 9000 }
  cpu { cores = 1 }
  memory { dedicated = 1024 }
  network_device { bridge = "vmbr0" }
  initialization {
    ip_config {
      ipv4 {
        address = "${each.value}/24"
        gateway = "192.168.56.1"
      }
    }
    user_account {
      username = "ops"
      keys     = [file("~/.ssh/id_ed25519.pub")]
    }
  }
}
```

Argument names change between provider versions: read the provider's documentation **for the
version you pinned** before copying any example, including this one. For vSphere the equivalent is
the `hashicorp/vsphere` provider with `vsphere_virtual_machine` cloned from a template, plus data
sources for the datacenter, datastore, cluster and network. For AWS it is `aws_instance` with an
`aws_ami` data source and an `aws_security_group`.

**Key terms**

| Term | Meaning |
|---|---|
| Provider | plugin for one API, downloaded by `terraform init` into `.terraform/` |
| `.terraform.lock.hcl` | exact provider versions and checksums; **commit it** |
| Resource address | `TYPE.NAME` or `TYPE.NAME["key"]`, e.g. `proxmox_virtual_environment_vm.target["target3"]` |
| Data source | read-only lookup: `data "aws_ami" "ubuntu" {...}` |
| `for_each` / `count` | create several resources from one block |

**See it on a real system** (lab `ctrl` VM, in the Terraform directory):

```bash
terraform version
terraform init
terraform providers
terraform fmt -check -recursive && terraform validate
```

```
Terraform v1.9.8
on linux_amd64
Initializing the backend...
Initializing provider plugins...
- Finding bpg/proxmox versions matching "~> 0.70"...
- Installing bpg/proxmox v0.70.1...
- Installed bpg/proxmox v0.70.1 (self-signed, key ID ...)
Terraform has been successfully initialized!
Providers required by configuration:
.
├── provider[registry.terraform.io/bpg/proxmox] ~> 0.70
└── provider[registry.terraform.io/hashicorp/aws] ~> 6.0
Success! The configuration is valid.
```

→ `init` downloaded the providers and wrote `.terraform.lock.hcl`; `fmt -check` and `validate`
passed, which is exactly what a merge request pipeline job should run first.

**Hands-on lab (test VM only)**

**Step 1 — Create one VM** on a lab Proxmox (or, without Proxmox, an `aws_security_group` in a
sandbox AWS account; see [Cloud & AWS](36-learn-cloud-aws.md)). Use an API token with the minimum
role the provider documents.

**Step 2 — Break it.** Remove the `required_providers` version pin, delete `.terraform.lock.hcl`, and
`init` on another machine months later: a newer provider version renames an argument and `plan`
fails with `Unsupported argument`. Then point `endpoint` at the IP instead of the name: TLS fails
with `x509: cannot validate certificate for 192.168.56.5 because it doesn't contain any IP SANs`.

**Step 3 — Fix it.** Restore the pin and the committed lock file; use the DNS name that matches the
certificate (or add the IP as a SAN when you reissue it).

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `Error: Failed to query available provider packages` | `curl -sI https://registry.terraform.io` from the host | no Internet or proxy; use a provider mirror for air-gapped sites |
| `Error: Inconsistent dependency lock file` | `git diff .terraform.lock.hcl` | lock file changed or missing; `terraform init -upgrade` deliberately |
| `Unsupported argument` after an upgrade | provider changelog | unpinned provider version |
| `x509: certificate signed by unknown authority` | `openssl s_client -connect pve1.example.com:8006` | private CA not in the trust store Terraform (Go) reads |

**Why it matters for troubleshooting.** Terraform errors are API errors with an extra layer on top.
Read them as "which provider, which API call, which HTTP status", then debug the API (DNS, TLS,
token permissions) like any other client.

**Next step:** the file that makes Terraform work, and break: state.

### State and why it matters

**Level:** [L3 · Senior] ([L2 · Mid] to read)

**Concept.** Terraform's **state** maps every resource address in your code to a real object ID
(`proxmox_virtual_environment_vm.target["target3"]` → VM 153 on pve1) and stores the attributes it
last saw. Without state, Terraform cannot know that VM 153 is "its" VM; it would try to create a
second one. State is therefore:

- **critical**: lose it and Terraform no longer manages your infrastructure;
- **sensitive**: it contains every attribute in plain text, including passwords and tokens that resources return;
- **shared**: two people applying with two copies of state will damage each other's changes.

Hence the three rules: never commit `terraform.tfstate` (section 1's `.gitignore`), store it in a
**remote backend** with encryption and access control, and use **locking**.

```
   code (*.tf)  ──┐
                  ├──► terraform plan ──► diff = what to create / change / destroy
   state  ────────┤        ▲
   (last known)   │        │ refresh: read real objects through the provider API
   real world ────┘ ───────┘
```

**Key terms**

| Term | Meaning |
|---|---|
| `terraform state list` / `show ADDRESS` | list managed resources / show one with its attributes |
| `terraform state mv` / `moved {}` block | rename an address without destroying the object |
| `terraform state rm` | stop managing an object (does **not** delete it) |
| Refresh | reading current real values into the plan |
| Serial / lineage | version counter / unique ID of a state, used to detect conflicting copies |

**See it on a real system**

```bash
terraform state list
terraform state show 'proxmox_virtual_environment_vm.target["target3"]' | head -12
```

```
proxmox_virtual_environment_vm.target["target3"]
aws_security_group.web
# proxmox_virtual_environment_vm.target["target3"]:
resource "proxmox_virtual_environment_vm" "target" {
    id            = "153"
    name          = "target3"
    node_name     = "pve1"
    started       = true
    vm_id         = 153
    ...
```

→ Two managed objects. The real Proxmox VM 153 is bound to that address; if you renamed the
resource block in code without a `moved` block, the next plan would show "destroy 153, create a new
VM", which is how people delete production VMs by "just refactoring".

**Hands-on lab (test VM only)**

**Step 1 — Read your state**: `state list`, `state show`, and `terraform show -json | jq` on the lab
config. Find any value you would not want in Git (a password, a token) in the JSON.

**Step 2 — Break it.** Rename `resource "proxmox_virtual_environment_vm" "target"` to `"vm"` and run
`terraform plan`: `1 to add, 0 to change, 1 to destroy`. Do **not** apply.

**Step 3 — Fix it** with a `moved` block (`moved { from = proxmox_virtual_environment_vm.target
to = proxmox_virtual_environment_vm.vm }`) and confirm the plan shows no changes.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Plan wants to recreate something that exists | `terraform state list` | address changed (rename, `count` → `for_each`) without `moved` |
| Plan wants to create everything | which backend did `init` use? | empty or wrong state (wrong workspace, wrong backend key) |
| Secrets found in a Git repo | `git log --all -- '*.tfstate'` | state committed; rotate the secrets, move to a remote backend |

**Why it matters for troubleshooting.** When a plan shows destroys you did not expect, the problem
is almost never the cloud: it is the mapping between code and state. Read the addresses before you
read anything else.

**Next step:** use the plan as your safety net.

### Plan and apply

**Level:** [L3 · Senior]

**Concept.** `terraform plan` computes the changes; `terraform apply` executes them. Save the plan
to a file (`-out=tfplan`) and apply **that file**, so what you reviewed is exactly what runs, even
if someone changes the code or the world in between. Read every plan symbol, and stop at any
`destroy` or `forces replacement` you did not expect.

| Symbol | Meaning | Risk |
|---|---|---|
| `+` | create | low |
| `~` | update in place | medium: read which attribute |
| `-/+` (or `+/-` with create_before_destroy) | destroy and recreate: "forces replacement" | **high**: new VM, new IP, data on local disks gone |
| `-` | destroy | **high** |
| `<=` | read a data source | none |

In GitLab CI the usual flow is: MR pipeline runs `fmt`, `validate`, `plan -out=tfplan` and posts the
plan (as an artifact or MR comment); merging to `main` runs a **manual** `apply` job that applies the
saved plan artifact, with `resource_group: terraform` so applies never overlap.

**Key terms**

| Term | Meaning |
|---|---|
| `-out=tfplan` | save the plan; `terraform show tfplan` reads it |
| `-target=ADDRESS` | limit to one resource (emergency use only; leaves the rest unreconciled) |
| `-replace=ADDRESS` | force recreation of one resource (replaces the old `taint`) |
| `lifecycle { prevent_destroy = true }` | refuse any plan that destroys this resource |
| `-detailed-exitcode` | exit 0 no changes, 2 changes present, 1 error (useful for drift jobs) |

**See it on a real system**

```bash
terraform plan -out=tfplan          # review this output; `terraform show tfplan` prints it again later
```

```
Terraform will perform the following actions:

  # proxmox_virtual_environment_vm.target["target4"] will be created
  + resource "proxmox_virtual_environment_vm" "target" {
      + name      = "target4"
      + node_name = "pve1"
      ...
    }

  # aws_security_group.web must be replaced
-/+ resource "aws_security_group" "web" {
      ~ name = "web-sg" -> "web-sg-v2" # forces replacement
      ...
    }

Plan: 2 to add, 0 to change, 1 to destroy.

Saved the plan to: tfplan
```

→ Adding target4 is what you wanted. The security group **replacement** is a side effect of renaming
it: by default Terraform deletes the old group first, which AWS refuses while instances or network
interfaces still use it (the apply hangs, then fails with `DependencyViolation`), and anything that
loses the group loses its rules until the new one is attached. Stop, and either keep the name or plan
the replacement in a window (`create_before_destroy` plus `name_prefix` is the usual pattern).

**Hands-on lab (test VM only)**

**Step 1 — Add target4** with a saved plan, review, apply the saved plan.

**Step 2 — Break it.** Change a field that forces replacement (the VM's `vm_id`), plan, and notice
`-/+`. Add `lifecycle { prevent_destroy = true }` to the resource and plan again: Terraform refuses
with `Instance cannot be destroyed`.

**Step 3 — Fix it** by reverting the field. Keep `prevent_destroy` on stateful resources (database
VMs, state buckets).

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `Saved plan is stale` | re-run plan | state changed after the plan was saved (someone else applied) |
| Apply half done, then error | `terraform plan` again | partial apply; state records what succeeded; fix and re-plan |
| Unexpected `-/+` | read the `# forces replacement` line | changed an immutable attribute |
| `Error: Instance cannot be destroyed` | the resource's lifecycle block | `prevent_destroy` doing its job |

**Why it matters for troubleshooting.** A saved, reviewed plan is the IaC equivalent of a change
request's "steps" section. When something breaks after an apply, the plan artifact in the pipeline
tells you exactly what changed.

**Next step:** make configurations reusable with variables, outputs and modules.

### Variables, outputs and modules

**Level:** [L3 · Senior]

**Concept.** **Input variables** parameterise a configuration (`var.targets`, `var.pve_api_token`),
**outputs** export values (IPs, IDs) for humans or other tools, and **modules** package a set of
resources behind inputs and outputs so you can reuse them ("an Ubuntu VM with our cloud-init"). A
module is just a directory of `.tf` files; the root configuration calls it.

```hcl
# variables.tf
variable "targets" {
  description = "VM name => IPv4 address"
  type        = map(string)
}
variable "pve_api_token" {
  type      = string
  sensitive = true                  # hidden in plan output; still stored in state
}

# main.tf — calling a local module once per VM
module "lab_vm" {
  source   = "./modules/ubuntu-vm"
  for_each = var.targets
  name     = each.key
  ip       = each.value
}

# outputs.tf — feed Ansible
output "ansible_inventory" {
  value = { for name, m in module.lab_vm : name => m.ipv4 }
}
```

```bash
# terraform.tfvars is gitignored; values for CI come from TF_VAR_* environment variables
export TF_VAR_pve_api_token="$(pass show lab/pve-token)"
terraform output -json ansible_inventory
```

```
{"target3":"192.168.56.53","target4":"192.168.56.54"}
```

→ That JSON becomes Ansible's inventory (a small script or the `cloud.terraform` inventory plugin),
so a new VM is created by Terraform and configured by your `docker` role in one pipeline.

**Key terms**

| Term | Meaning |
|---|---|
| `TF_VAR_name` | environment variable that sets `var.name` (use for secrets in CI) |
| `*.tfvars` | files of variable values; `*.auto.tfvars` load automatically |
| `sensitive = true` | redacts the value in CLI output, **not** in state |
| Module source | local path, Git URL with `?ref=v1.2.0`, or a registry |
| `validation {}` | input checks that fail early with your own error message |

**See it on a real system**

```bash
terraform console <<< 'var.targets'
terraform output
```

```
tomap({
  "target3" = "192.168.56.53"
  "target4" = "192.168.56.54"
})
ansible_inventory = {
  "target3" = "192.168.56.53"
  "target4" = "192.168.56.54"
}
```

**Hands-on lab (test VM only)**

**Step 1 — Extract a module** `modules/ubuntu-vm` from the VM resource, with inputs `name`, `ip` and
an output `ipv4`. Use `moved` blocks so the existing VMs are not recreated.

**Step 2 — Break it.** Reference a Git module with `?ref=main` instead of a tag; change the module in
another repo; the next plan in your project suddenly wants to change every VM.

**Step 3 — Fix it** by pinning modules to tags (`?ref=v1.0.0`) and upgrading them deliberately, like
providers.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `No value for required variable` | how CI sets `TF_VAR_*` | variable missing in this environment |
| Plan changes resources nobody touched | `git log` of the module source | unpinned module changed |
| `Module not installed` | `terraform init` | new module added; init must run again |

**Why it matters for troubleshooting.** Modules multiply both good and bad changes. When many
resources change at once in a plan, the first suspect is a module or provider version, not your
diff.

**Next step:** share state safely: remote backends and locking.

### Remote state and locking

**Level:** [L3 · Senior]

**Concept.** A **backend** stores the state somewhere shared and durable, and **locks** it during
operations so two applies cannot run at once. Two backends fit your world:

| Backend | Where | Locking | Notes |
|---|---|---|---|
| GitLab-managed state (`http` backend) | your GitLab, per project, versioned | yes (GitLab API) | access controlled by GitLab roles; perfect on-prem; CI jobs authenticate with `CI_JOB_TOKEN` or a token |
| `s3` | an AWS S3 bucket (versioning + encryption on) | `use_lockfile = true` (Terraform 1.10+, GA in 1.11) | DynamoDB locking is deprecated; block public access, restrict IAM |

```hcl
# GitLab-managed state: keep the block empty, pass settings at init time
terraform {
  backend "http" {}
}
```

```bash
TF_ADDRESS="https://gitlab.example.com/api/v4/projects/42/terraform/state/lab"
terraform init \
  -backend-config="address=$TF_ADDRESS" \
  -backend-config="lock_address=$TF_ADDRESS/lock" \
  -backend-config="unlock_address=$TF_ADDRESS/lock" \
  -backend-config="username=ops.engineer" \
  -backend-config="password=$GITLAB_TOKEN" \
  -backend-config="lock_method=POST" \
  -backend-config="unlock_method=DELETE" \
  -backend-config="retry_wait_min=5"
```

```hcl
# S3 backend (AWS)
terraform {
  backend "s3" {
    bucket       = "example-tfstate-123456789012"
    key          = "web/terraform.tfstate"
    region       = "eu-west-1"
    encrypt      = true
    use_lockfile = true
  }
}
```

**Key terms**

| Term | Meaning |
|---|---|
| Lock | a marker held during plan/apply; others wait or fail |
| `terraform force-unlock LOCK_ID` | remove a stale lock (dangerous if the holder is still running) |
| Workspace | several states for one configuration (`default`, `staging`); prefer separate directories or state names for environments |
| State versioning | GitLab keeps state versions; S3 bucket versioning does the same |

**See it on a real system.** The error everyone meets once:

```bash
terraform plan
```

```
│ Error: Error acquiring the state lock
│
│ Error message: HTTP remote state already locked: ID=7f3c9a1e-2b4d-4c8e-9f10-5a6b7c8d9e0f
│ Lock Info:
│   ID:        7f3c9a1e-2b4d-4c8e-9f10-5a6b7c8d9e0f
│   Path:
│   Operation: OperationTypeApply
│   Who:       root@runner-t1xxxxxx-project-42-concurrent-0
│   Version:   1.9.8
│   Created:   2026-10-03 08:51:12.123456789 +0000 UTC
│   Info:
│
│ Terraform acquires a state lock to protect the state from being written
│ by multiple users at the same time. Please resolve the issue above and try
│ again. For most commands, you can disable locking with the "-lock=false"
│ flag, but this is not recommended.
```

→ An **apply** started by a CI job at 08:51 holds the lock (`Who` is user@hostname of the process, here
a Docker-executor job container on runner01). Before anything else, find out whether
that apply is still running (the pipeline page, the runner's job list). If it is running, wait. If
its job was killed (runner restarted, job timeout), the lock is stale.

> ⚠️ `terraform force-unlock LOCK_ID` while the other apply is still running lets two processes write
> the same state, which can corrupt it and orphan real resources. Only unlock after proving the
> holder is dead (job cancelled or failed, runner process gone), and then run `terraform plan` to see
> what the interrupted apply left behind. Never use `-lock=false` as a workaround.

**Hands-on lab (test VM only)**

**Step 1 — Move lab state to GitLab.** Configure the `http` backend and run `terraform init
-migrate-state`; confirm the state appears under Operate → Terraform states in the project.

**Step 2 — Break it.** Start `terraform apply` on a slow change and kill it with Ctrl+C twice (or
cancel the CI job). Run `terraform plan`: lock error with your user as `Who`.

**Step 3 — Fix it safely.** Prove no apply is running, `terraform force-unlock LOCK_ID`, then `plan`
and reconcile whatever the interrupted apply half-created.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `Error acquiring the state lock` | check pipelines and `Who`/`Created` | another run, or a stale lock from a killed run |
| `HTTP remote state endpoint requires auth` / `401` | the token's scope and role | token lacks `api` scope or Maintainer role on the project |
| `Backend configuration changed` | `terraform init -reconfigure` or `-migrate-state` | backend settings changed since the last init |
| Two people see different resources | which state each uses | one of them is on a local state file |

**Why it matters for troubleshooting.** Remote state with locking turns "two engineers broke
production at the same time" into a polite error message. Treat a lock as information, not an
obstacle.

**Next step:** what to do when reality and code disagree: drift and import.

### Drift and import

**Level:** [L3 · Senior]

**Concept.** **Drift** is any difference between the real infrastructure and what Terraform last
applied: someone opened port 22 in a security group by hand during an incident, a VM's memory was
raised in the Proxmox UI. **Import** is the opposite problem: an object that exists but is not in any
state (your old web01 VM, created by hand years ago). Both are normal in brownfield environments;
the goal is to bring everything under code, deliberately.

```
 drift:   code says 1 GB ─► state says 1 GB ─► real VM has 2 GB (changed in UI)
          plan: "~ memory 2048 -> 1024"  ← applying would silently undo the hand change
 import:  real web01 (VM 110) exists ─► no state ─► import block ─► now managed
```

```hcl
# import.tf (Terraform 1.5+): bring the hand-made web01 VM under management
import {
  to = proxmox_virtual_environment_vm.web01
  id = "pve1/110"                    # format documented by the provider: NODE/VMID
}
```

```bash
terraform plan -generate-config-out=generated_web01.tf   # writes a starting resource block
terraform plan -refresh-only                             # show drift without proposing changes
terraform plan -detailed-exitcode; echo "exit=$?"        # 0 no diff, 2 diff, 1 error
```

**Key terms**

| Term | Meaning |
|---|---|
| `plan -refresh-only` | show what changed outside Terraform; `apply -refresh-only` accepts it into state |
| `import {}` block | declarative import, reviewed in a plan like any change |
| `-generate-config-out` | let Terraform draft HCL for imported objects (review it; it is verbose) |
| `lifecycle { ignore_changes = [...] }` | deliberately ignore attributes managed elsewhere |

**See it on a real system**

```
Note: Objects have changed outside of Terraform

Terraform detected the following changes made outside of Terraform since the
last "terraform apply" which may have affected this plan:

  # aws_security_group.web has changed
  ~ resource "aws_security_group" "web" {
      ~ ingress = [
          + {
              + cidr_blocks = ["0.0.0.0/0"]
              + from_port   = 22
              + protocol    = "tcp"
              + to_port     = 22
            },
            # (2 unchanged elements hidden)
        ]
    }
```

→ Someone opened SSH to the whole Internet by hand. Applying the normal plan would remove it again
(good, if it was an incident hack nobody cleaned up; bad, if someone depends on it right now). Drift
is a conversation, not just a diff: find out who and why, then either codify or remove it.

**Hands-on lab (test VM only)**

**Step 1 — Import** a hand-made lab VM with an `import` block and `-generate-config-out`; trim the
generated code until `plan` shows no changes.

**Step 2 — Break it.** Change the VM's memory in the Proxmox UI. Run a scheduled-style drift check
(`plan -detailed-exitcode`), exit code 2.

**Step 3 — Fix it** by deciding: put the new value in code (codify) or apply to revert. Then create a
nightly GitLab scheduled pipeline that runs the drift check and fails (exit 2) to alert you.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `Resource already managed by Terraform` on import | `terraform state list` | already in state under another address |
| `Cannot import non-existent remote object` | check the ID format in the provider docs | wrong import ID |
| Plan always shows the same small change | `ignore_changes` candidates | attribute set by another system (autoscaling, tags added by policy) |

**Why it matters for troubleshooting.** "Who changed this?" is a question drift detection answers
before an incident instead of during one. And after an incident, hand-made mitigations must be
either codified or reverted, or the next apply will undo them at the worst moment.

**Next step:** all of this needs credentials: section 6, secrets management.

---

## 6. Secrets management

> 📚 **Study path:** 1) Note: this section first (KodeKloud has no dedicated course that covers this whole flow), then [Security & DevSecOps](37-learn-security-devsecops.md) for the security side · 2) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* — Architecture & Core Concepts (variables) and Optimization, Security and Monitoring ([course](https://kodekloud.com/courses/gitlab-ci-cd)); *Fundamentals of SRE* — Release Engineering, secure release pipeline lab ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) Optional: a KodeKloud HashiCorp Vault course (check the current catalog) · 4) Practice: the labs below: sops + age in a lab repo, a Vault dev server on `ctrl`, and the leaked-secret drill (Steps 8–12).

A secret is any value that grants access: the Harbor robot secret, the GitLab runner token, the
Dokploy API key, the Proxmox API token, database passwords, the kubeconfig of the deployer, the
Ansible Vault password, TLS private keys. Secrets management answers four questions for each one:
**where is it stored, who and what can read it, how is it delivered to the process that needs it,
and how fast can it be rotated?** The last question is the one that matters during an incident.

```
                   store (encrypted, access-controlled, audited)
 GitLab CI vars ─┐       Ansible Vault ─┐      sops+age ─┐     HashiCorp Vault / OpenBao
 (per project)   │       (in Git)       │      (in Git)  │     (central service, dynamic)
                 ▼                      ▼                ▼            ▼
             deliver: masked env var / File variable / decrypted at run / short-lived token
                 ▼
             consume: docker login, ansible-playbook, terraform, the app at runtime
                 ▼
             rotate: change at the source, every consumer picks up the new value
```

### Choosing where secrets live

**Level:** [L3 · Senior]

**Concept.** There is no single right tool; there is a right tool per use. A senior engineer can
explain each choice in one sentence.

| Tool | Strength | Weakness | Use it for |
|---|---|---|---|
| GitLab CI/CD variables (masked, protected, File) | zero extra infrastructure; scoped per environment | static, long-lived; anyone with Maintainer can change; visible to every job on matching refs | CI-only credentials: Harbor robot, Dokploy key, deployer kubeconfig |
| Ansible Vault | lives next to playbooks; simple | one shared password; whole-file or per-value encryption; rotation is manual | server config secrets used only by Ansible |
| sops + age | encrypted values in Git with readable keys, diffable; several recipients (team + CI) | key distribution and revocation are on you | config repos (Compose env files, Traefik, Kubernetes manifests) |
| HashiCorp Vault / OpenBao | central, audited, short-lived and dynamic secrets, fine-grained policies | a critical service to run (HA, unseal, backups) | many teams, dynamic DB credentials, short-lived CI tokens via JWT |
| Swarm / Kubernetes Secrets | delivered as files at runtime | Kubernetes Secrets are base64, not encrypted, unless encryption at rest is enabled | runtime secrets of containers |

Two rules apply everywhere. Prefer **files over environment variables** for runtime secrets
(environment variables leak through `docker inspect`, `/proc/PID/environ`, crash reports and debug
pages). And prefer **short-lived** credentials over long-lived ones wherever the tool allows.

**Key terms**

| Term | Meaning |
|---|---|
| Rotation | replacing a secret with a new value and revoking the old one |
| Dynamic secret | generated on request with a short TTL (Vault database engine) |
| Secret zero | the first credential needed to fetch all others (vault password, Vault token); minimise and protect it |
| Least privilege | each credential can do only what its consumer needs (push to one Harbor project, patch one Deployment) |

**See it on a real system.** An inventory of where secrets are consumed, from your infra repo:

```bash
git grep -nE 'HARBOR_|DOKPLOY_|VAULT_|KUBECONFIG|vault_[a-z_]+|password|token' -- '*.yml' '*.yaml' '*.tf' '*.sh' | head -15
```

```
.gitlab-ci.yml:61:    - echo "$HARBOR_PASSWORD" | docker login harbor.example.com -u "$HARBOR_USER" --password-stdin
ci/dokploy-deploy.sh:6:  -H "x-api-key: $DOKPLOY_TOKEN" \
group_vars/runners/vars.yml:2:runner_token: "{{ vault_runner_token }}"
terraform/variables.tf:8:variable "pve_api_token" {
```

→ Four secrets, three stores (GitLab variables, Ansible Vault, Terraform `TF_VAR_*`). Write this list
into the secrets register (the "Where secrets live" page of your runbook) with owner, store, consumer
and rotation procedure. During an incident, that page is worth more than any tool.

**Hands-on lab (test VM only)**

**Step 1 — Build the register** for your lab: every secret, its store, consumers, owner, last rotation.

**Step 2 — Break it.** "Lose" the register and pretend the Harbor robot secret leaked. Time how long it
takes to find every consumer by searching.

**Step 3 — Fix it.** Keep the register in the infra repo (names only, never values) and review it
quarterly.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Rotation breaks a forgotten consumer | search the register and the repos for the variable name | no secrets inventory |
| A secret works everywhere for everything | its permissions | over-privileged credential (admin token used for pushes) |
| Nobody knows how to rotate | the runbook | rotation never practised |

**Why it matters for troubleshooting.** A large share of "sudden" outages are expired or rotated
credentials. A register with expiry dates turns them into calendar entries.

**Next step:** encrypt config secrets in Git with sops.

### sops with age

**Level:** [L3 · Senior]

**Concept.** **sops** encrypts the **values** in YAML, JSON, ENV or INI files and leaves the **keys**
readable, so `git diff` still shows which setting changed. **age** is a small modern encryption tool
whose key pairs sops can use. Each file is encrypted for several recipients (each engineer's age
public key plus the CI key), and `.sops.yaml` says which recipients apply to which paths.

```bash
mkdir -p ~/.config/sops/age
age-keygen -o ~/.config/sops/age/keys.txt          # private key; never committed
grep 'public key' ~/.config/sops/age/keys.txt
```

```yaml
# .sops.yaml (committed)
creation_rules:
  - path_regex: secrets/.*\.enc\.yaml$
    age: >-
      age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p,
      age1lggyhqrw2nlhcxprm67z43rta597azn8gknawjehu9d9dl0jq3yqqvfafg
```

**Key terms**

| Term | Meaning |
|---|---|
| `sops edit FILE` | decrypt to a temp file, open `$EDITOR`, re-encrypt on save (`sops FILE` in older versions) |
| `sops -d FILE` | decrypt to stdout (pipe it, never redirect to a tracked file) |
| `sops updatekeys FILE` | re-encrypt the data key for the current recipients after `.sops.yaml` changes |
| `SOPS_AGE_KEY_FILE` | where sops finds the private key (for CI: a File variable) |

**See it on a real system**

```bash
sops edit secrets/shop.enc.yaml
head -6 secrets/shop.enc.yaml
sops -d secrets/shop.enc.yaml | yq '.db_host'
```

```
db_host: ENC[AES256_GCM,data:3Jq0b8m3o0Gq9tE=,iv:Wq...,tag:Rk...,type:str]
db_password: ENC[AES256_GCM,data:Yp7n2T0kQ8vGx1sA2w==,iv:...,tag:...,type:str]
sops:
    age:
        - recipient: age1ql3z7hjy54pw3hyww5ayyfg7zqgvc7w3j2elw8zmrj2kg5sfn9aqmcac8p
          enc: |
192.168.56.60
```

→ The key names are visible, the values are ciphertext, and the `sops:` block lists who can decrypt.
A reviewer sees "db_password changed" in the MR without seeing the password.

**Hands-on lab (test VM only)**

**Step 1 — Encrypt** a Compose env file for `shop-web` with two recipients (you and a "CI" key);
decrypt it in a CI job using a File variable for `SOPS_AGE_KEY_FILE`.

**Step 2 — Break it.** Add a new teammate's key to `.sops.yaml` but forget `sops updatekeys`. They get
`Error getting data key: 0 successful groups required, got 0`.

**Step 3 — Fix it** with `sops updatekeys secrets/*.enc.yaml`. Then remove a departed engineer's key,
run `updatekeys` **and rotate the secret values**, because they could have kept a decrypted copy.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `Error getting data key: 0 successful groups required, got 0` | `sops -d` with `SOPS_AGE_KEY_FILE` set explicitly | your key is not a recipient, or the key file is not found |
| `no matching creation rules found` | `cat .sops.yaml` | path does not match `path_regex` |
| Decrypted file committed | `git log --all -- FILE` | redirected `sops -d` output into the repo; rotate |

**Why it matters for troubleshooting.** With sops, the config that broke production and the secrets
it used are in the same commit history, so "what changed?" includes secrets without exposing them.

**Next step:** a central secrets service: HashiCorp Vault.

### HashiCorp Vault and short-lived CI tokens

**Level:** [L3 · Senior] to use, [L4 · Lead/SRE] to operate

**Concept.** **Vault** (and its open-source fork **OpenBao**, same API) is a server that stores
secrets, issues **short-lived** credentials, enforces **policies** per path, and **audits** every
access. The pattern that removes long-lived secrets from GitLab: each CI job gets a signed **ID
token** (JWT) from GitLab; Vault verifies it (project, branch, protected or not) and returns a Vault
token valid for one minute, which reads only that project's secrets.

```
 GitLab job (id_tokens: aud=https://vault.example.com)
     │ JWT: project_id=42, ref=main, ref_protected=true, signed by GitLab
     ▼
 Vault auth/jwt ── checks signature (GitLab's JWKS) + bound_claims ── role shop-ci
     │ Vault token, TTL 60 s, policy shop-ci: read secret/data/shop/*
     ▼
 job reads secret/shop/harbor → docker login → token expires
```

Lab setup on `ctrl` (dev server: in-memory, unsealed, plain HTTP; **lab only**):

```bash
vault server -dev -dev-root-token-id=lab-root &           # lab only, never production
export VAULT_ADDR=http://127.0.0.1:8200 VAULT_TOKEN=lab-root
vault kv put -mount=secret shop/harbor user='robot$shop+gitlab-ci' password='lab-not-real-123'
vault policy write shop-ci - <<'EOF'
path "secret/data/shop/*" { capabilities = ["read"] }
EOF
vault auth enable jwt
vault write auth/jwt/config oidc_discovery_url="https://gitlab.example.com" bound_issuer="https://gitlab.example.com"
vault write auth/jwt/role/shop-ci - <<'EOF'
{
  "role_type": "jwt",
  "policies": ["shop-ci"],
  "token_explicit_max_ttl": 60,
  "user_claim": "user_email",
  "bound_audiences": "https://vault.example.com",
  "bound_claims": {"project_id": "42", "ref_protected": "true"}
}
EOF
```

The CI job (free tier; GitLab Premium also offers a `secrets:` keyword that does this for you):

```yaml
push-with-vault:
  image: harbor.example.com/platform/deploy-tools:1.2     # includes the vault CLI
  id_tokens:
    VAULT_ID_TOKEN:
      aud: https://vault.example.com
  script:
    - export VAULT_ADDR=https://vault.example.com
    - export VAULT_TOKEN="$(vault write -field=token auth/jwt/login role=shop-ci jwt="$VAULT_ID_TOKEN")"
    - vault kv get -field=password -mount=secret shop/harbor | docker login harbor.example.com -u "$(vault kv get -field=user -mount=secret shop/harbor)" --password-stdin
```

**Key terms**

| Term | Meaning |
|---|---|
| Seal / unseal | Vault starts sealed (cannot decrypt) until unseal keys or auto-unseal are provided |
| Policy | HCL rules: which paths, which capabilities (read, create, update, delete, list) |
| Auth method | how clients log in: `jwt`, `approle`, `userpass`, `kubernetes` |
| KV v2 | versioned key/value engine; API path `secret/data/...` |
| Audit device | log of every request, with secrets HMAC'd |

**See it on a real system**

```bash
vault status
vault kv get -mount=secret shop/harbor
```

```
Key             Value
---             -----
Seal Type       shamir
Initialized     true
Sealed          false
Total Shares    1
Threshold       1
Version         1.17.6
Storage Type    inmem
HA Enabled      false
=== Secret Path ===
secret/data/shop/harbor

======= Metadata =======
Key                Value
---                -----
created_time       2026-10-03T09:30:12.345678Z
deletion_time      n/a
destroyed          false
version            1

====== Data ======
Key         Value
---         -----
password    lab-not-real-123
user        robot$shop+gitlab-ci
```

→ `Sealed false` and `Storage Type inmem`: a dev server that forgets everything on restart. In
production you would see `Sealed false` only after unseal, raft or another persistent storage, and
`HA Enabled true`. The secret is versioned (`version 1`); writing it again creates version 2, and you
can roll back to 1, which is useful when a rotation goes wrong.

**Hands-on lab (test VM only)**

**Step 1 — Run the flow** above against your lab GitLab (Vault must reach GitLab's JWKS endpoint, and
GitLab jobs must reach Vault).

**Step 2 — Break it.** Run the job on an unprotected feature branch: login fails with
`error validating claims: claim "ref_protected" does not match any associated bound claim values`.
Then set the role's `bound_audiences` to a different URL: `error validating token: invalid audience
(aud) claim`.

**Step 3 — Fix it** deliberately: the first failure is the policy working; only the second is a bug.
Document which branches may read which paths.

**How it breaks**

| Symptom / error text | First command | Cause |
|---|---|---|
| `Vault is sealed` (HTTP 503) | `vault status` | restart without auto-unseal; unseal with the key holders |
| `permission denied` (403) on a path | `vault token capabilities secret/data/shop/harbor` | policy path wrong (KV v2 needs `data/` in policies) |
| JWT login: `invalid audience` / `claim ... does not match` | decode the JWT payload in a lab job (never in production logs) | `aud` or `bound_claims` mismatch |
| `x509` from the vault CLI | `VAULT_CACERT` or the system trust store | private CA (trust map, section 0) |

**Why it matters for troubleshooting.** With 60-second CI tokens, a leaked job token is useless a
minute later, and the audit log tells you exactly which job read which secret. That shrinks a leak
from an incident to a footnote.

**Next step:** what to do when a secret leaks anyway: the leaked-secret procedure.

### Runtime secrets in Swarm and Kubernetes

**Level:** [L2 · Mid] to use, [L3 · Senior] to design

**Concept.** Pipelines and playbooks are not the only consumers: running containers need database
passwords and API keys too. Docker Swarm (and so Dokploy) has **secrets** stored encrypted in the
Swarm raft log and mounted as files under `/run/secrets/NAME` in the containers that are granted
them. Kubernetes **Secrets** are mounted as files or environment variables, but are only
**base64-encoded** in etcd unless you enable encryption at rest; RBAC on `secrets` is what really
protects them. Dokploy's per-app environment variables are stored in Dokploy's database and
injected as environment variables: convenient, visible to every Dokploy admin and in
`docker service inspect`.

**Key terms**

| Term | Meaning |
|---|---|
| `docker secret create NAME FILE` | create a Swarm secret (needs a Swarm manager) |
| `/run/secrets/NAME` | where Swarm mounts it (tmpfs, not on disk) |
| `*_FILE` convention | many images read `POSTGRES_PASSWORD_FILE` instead of `POSTGRES_PASSWORD` |
| Encryption at rest | Kubernetes API server `--encryption-provider-config` encrypting Secrets in etcd |

**See it on a real system** (Dokploy host and homelab, read-only):

```bash
docker secret ls
docker service inspect shop-web-x1y2z3 --format '{{json .Spec.TaskTemplate.ContainerSpec.Secrets}}' | jq -c '.[]'
kubectl -n shop get secret shop-db -o jsonpath='{.data.password}' | base64 -d | wc -c
```

```
ID                          NAME          DRIVER    CREATED        UPDATED
q1w2e3r4t5y6u7i8o9p0a1s2d   shop_db_pass            3 weeks ago    3 weeks ago
{"File":{"Name":"shop_db_pass","UID":"0","GID":"0","Mode":292},"SecretID":"q1w2e3r4t5y6u7i8o9p0a1s2d","SecretName":"shop_db_pass"}
17
```

→ The Swarm service receives the password as a read-only file (mode 292 = 0444). The Kubernetes
command decodes the Secret: anyone with `get secrets` in the namespace can do the same, which is
why the length (`wc -c`) is all you should ever print.

**Hands-on lab (test VM only)**

**Step 1 — Use a file secret** for the lab database password in a Swarm service, with the image's
`*_FILE` variable.

**Step 2 — Break it.** Put the same password in a plain environment variable and find it with
`docker service inspect` and `cat /proc/PID/environ` on the host.

**Step 3 — Fix it** by removing the env var, and in Kubernetes check who can read Secrets with
`kubectl auth can-i get secrets -n shop --as=system:serviceaccount:shop:default`.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| Secret visible in `docker inspect` | `docker service inspect --format '{{json .Spec.TaskTemplate.ContainerSpec.Env}}'` | env var instead of a secret file |
| `secret not found` when the service starts | `docker secret ls` | created on another Swarm, or a typo |
| App cannot read `/run/secrets/NAME` | `docker exec CONTAINER id` and the secret's mode | app runs as a non-root UID; set UID/GID/mode |

**Why it matters for troubleshooting.** When an app suddenly cannot authenticate to its database
after a redeploy, the first question is "how does it get the password, and did that path change?".

**Next step:** the leaked-secret procedure, which ties all of this together.

### Leaked secret response

**Level:** [L2 · Mid] to execute, [L4 · Lead/SRE] to own

**Concept.** A leaked secret is an incident, even if nothing bad has happened yet. The order matters:
**rotate first** (make the leaked value useless), then make sure everything still works with the
new value, then check whether the old value was abused, and only then clean up history and prevent
a repeat. Deleting the commit first and rotating later is the most common mistake: the value is
already in clones, forks, CI caches and job logs. Steps 8 to 12 below use the running example: the
Harbor robot secret was printed in a CI job log on a public-to-the-company project.

```
 detect ──► rotate (Step 9) ──► update consumers + verify (Step 10) ──► check abuse (Step 11)
   │                                                                          │
 Step 8: scope it                                       Step 12: clean history, prevent, postmortem
```

### Step 8 — Scope the leak

**Goal:** know exactly which secret leaked, where, since when, and who could have seen it.

```bash
# where else is it? scan the repo history with redaction (no secret values printed)
gitleaks git --redact --report-format json --report-path leak.json .   # gitleaks 8.19+; older: gitleaks detect --source . --redact
jq -r '.[] | "\(.RuleID)  \(.File):\(.StartLine)  \(.Commit[0:8])  \(.Date)"' leak.json
# which job logs printed it? (search names, not values: the job that ran the debug line)
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$GITLAB/projects/$PROJECT_ID/jobs?scope[]=success&scope[]=failed&per_page=50" \
  | jq -r '.[] | select(.name=="build-image") | "\(.id) \(.created_at) \(.ref)"' | head -5
```

```
generic-api-key  ci/debug.sh:4  a7b8c9d0  2026-10-01T14:22:05Z
91180 2026-10-03T08:02:11.000Z feature/debug-push
91102 2026-10-01T14:25:40.000Z feature/debug-push
```

**What it means:** the secret was committed in `a7b8c9d0` on 1 October (a debug script echoing it)
and printed in at least two job logs on a feature branch. Exposure window: 1 October 14:22 until
now. Audience: everyone who can read the project's job logs (Reporter and above; on an internal
project with "Public pipelines" enabled, every signed-in user) and anyone with a clone.

**Why this step (now):** you cannot rotate everything blindly, and you cannot judge abuse without
knowing the window and the audience. Ten minutes of scoping also tells you whether this is "rotate
one robot" or "rotate everything in this repo".

**Next step:** if the secret is identified → Step 9 immediately. If several secrets are involved →
Step 9 for each, highest privilege first. If it is a personal credential (your GitLab password or
SSH key), rotate it yourself first and tell your security contact.

### Step 9 — Rotate the secret

**Goal:** make the leaked value useless by replacing it at the source and revoking the old one.

```bash
# Harbor: Project shop → Robot Accounts → robot$shop+gitlab-ci → Refresh secret (UI),
# or delete and recreate the robot with the same permissions. Then prove the OLD value is dead:
echo "$OLD_HARBOR_PASSWORD" | docker login harbor.example.com -u 'robot$shop+gitlab-ci' --password-stdin
# and the NEW one works:
echo "$NEW_HARBOR_PASSWORD" | docker login harbor.example.com -u 'robot$shop+gitlab-ci' --password-stdin
```

```
Error response from daemon: Get "https://harbor.example.com/v2/": unauthorized: authentication required
Login Succeeded
```

**What it means:** the old secret is rejected and the new one is accepted. From this moment the leak
cannot be used to push or pull images. (Run these on your workstation, and clear the variables
afterwards with `unset`.)

**Why this step (now):** every minute between detection and rotation is exposure. Rotation is also
reversible in practice (you can always issue another secret), while abuse of a live credential is
not.

**Next step:** → Step 10 to update every consumer before pipelines start failing. If rotation is
impossible right now (for example a vendor key that needs a support ticket), restrict it instead
(IP allow-list, reduce permissions) and continue with Step 11 in parallel.

### Step 10 — Update every consumer and verify

**Goal:** put the new value everywhere the old one was used, and prove each consumer works.

```bash
# consumers from the secrets register (section "Choosing where secrets live")
# 1) GitLab: update HARBOR_PASSWORD (masked, protected) in Settings → CI/CD → Variables, then re-run a build on main
# 2) Dokploy host: registry credentials in Dokploy's registry settings, then redeploy one app
# 3) Kubernetes: the imagePullSecret
kubectl -n shop create secret docker-registry harbor-pull \
  --docker-server=harbor.example.com --docker-username='robot$shop+gitlab-ci' \
  --docker-password="$NEW_HARBOR_PASSWORD" --dry-run=client -o yaml | kubectl apply -f -
kubectl -n shop rollout restart deployment/shop-web && kubectl -n shop rollout status deployment/shop-web --timeout=180s
```

```
secret/harbor-pull configured
deployment.apps/shop-web restarted
deployment "shop-web" successfully rolled out
```

**What it means:** the pull secret was replaced in place and new Pods pulled successfully with it.
The same "change, then prove" pattern applies to every other consumer: a green build job with
`Login Succeeded`, a Dokploy redeploy that pulls the image.

**Why this step (now):** a rotation that breaks production is how teams learn to avoid rotating. Doing
consumers in the order of the register, with a check after each, keeps the change boring.

**Next step:** all consumers verified → Step 11. A consumer fails → fix that consumer (most often a
forgotten copy of the old value); do **not** restore the old secret.

### Step 11 — Check whether the old secret was used

**Goal:** find any use of the leaked credential by someone other than your own systems during the
exposure window.

```bash
# Harbor audit log: operations by the robot account, newest first (Harbor before 2.13; from 2.13 new
# events go to the extended audit log, UI tab "Audit Logs": find its endpoint in your instance's API explorer)
curl -s -u "$HARBOR_ADMIN_USER:$HARBOR_ADMIN_PASSWORD" \
  "https://harbor.example.com/api/v2.0/audit-logs?page_size=100" \
  | jq -r '.[] | select(.username=="robot$shop+gitlab-ci") | "\(.op_time) \(.operation) \(.resource)"' | head -10
# Harbor's nginx access log on the Harbor VM shows source IPs (it does not log the user name, so filter
# by repository path; the log path depends on the install)
sudo grep '/v2/shop/shop-web/' /var/log/harbor/proxy.log | awk '{print $1, $2, $6}' | sort | uniq -c | sort -rn | head
```

```
2026-10-03T08:03:02Z create shop/shop-web:9d8c7b6a
2026-10-02T16:40:44Z create shop/shop-web:5e4f3a2b
2026-10-01T14:26:10Z create shop/shop-web:a7b8c9d0
     41 Oct  3 192.168.56.21
     37 Oct  2 192.168.56.21
```

**What it means:** every push matches a known pipeline commit, and all requests came from runner01
(192.168.56.21). No sign of abuse. A push of an unknown tag, a pull from an unknown IP, or activity at
odd hours would turn this into a security incident: preserve the logs, check the pushed images, and
escalate.

**Why this step (now):** only after rotation is the evidence stable: no new legitimate use of the old
secret can muddy the logs. Checking earlier risks confusing your own pipeline's traffic with abuse.

**Next step:** no abuse → Step 12. Abuse found → treat as a security incident: keep the logs,
quarantine suspicious images (Harbor project policies can prevent pulls of vulnerable or unsigned
artifacts; delete the suspicious ones once the evidence is preserved), inform your
security contact, and run section 7's incident process.

### Step 12 — Clean up, prevent and write it down

**Goal:** remove the secret from places people will look, and stop it happening again.

```bash
# erase the job logs that printed the secret (API; also available in the job page UI)
for j in 91180 91102; do
  curl -s -X POST --header "PRIVATE-TOKEN: $GITLAB_TOKEN" "$GITLAB/projects/$PROJECT_ID/jobs/$j/erase" | jq -r '"\(.id) erased=\(.erased_at)"'
done
git rm ci/debug.sh && git commit -m "Remove debug script that printed the Harbor secret (INC-2026-021)"
```

```
91180 erased=2026-10-03T10:12:40.000Z
91102 erased=2026-10-03T10:12:41.000Z
```

**What it means:** the logs are gone from GitLab and the script is gone from `main`. The value still
exists in Git history, but it is now **dead** (Step 9), so rewriting history is optional and only
worth it if policy requires it (`git filter-repo` on a fresh mirror, force-push, everyone re-clones;
see the warning in section 1).

**Why this step (now):** clean-up comes last because it does not reduce risk once the secret is
rotated; it reduces noise and future false alarms. Prevention is what stops the next leak.

**Next step:** add a `gitleaks` job to the pipeline and a pre-commit hook, mask the variable, add
"never echo secrets; use `set +x` around logins" to the CI guidelines, and write a short blameless
postmortem (section 7) with the timeline from Steps 8 to 12.

**Leaked-secret decision tree**

```
 secret exposed?
 ├─ which secret, where, since when, who could see? ──► Step 8
 ├─ can you rotate now?
 │    ├─ yes ──► rotate, prove old fails / new works ──► Step 9
 │    └─ no  ──► restrict (permissions, IP allow-list), escalate, rotate ASAP
 ├─ consumers updated and verified one by one ──► Step 10
 ├─ audit logs during the window
 │    ├─ only known sources ──► Step 12
 │    └─ unknown use ──► security incident (section 7), keep evidence
 └─ erase logs, remove from main, prevent (gitleaks, masking), postmortem ──► Step 12
```

**Fix & verify:** old value rejected, new value works in every consumer, a full pipeline on `main`
is green, a production pull succeeds.

**Rollback:** there is no rollback to the old secret. If the new secret breaks something, issue
another new one or fix the consumer.

**Prevent it next time:** secrets register with owners; masked and protected variables; short-lived
tokens (Vault JWT) where possible; gitleaks in CI and pre-commit; never print credentials in CI;
quarterly rotation drills so the procedure stays fast.

---

## 7. SRE practice

> 📚 **Study path:** 1) KodeKloud: *Fundamentals of SRE* — Service Level Objectives and Measurements → Incident Management (Preparing for Incidents, Designing Effective Alerts, IMAG roles, Blameless Postmortem Culture, Root Cause Analysis) → Managing Complexity, Risk and Toil (Change Management for Reliability) ([course](https://kodekloud.com/courses/fundamentals-of-sre)); lesson notes: [Root Cause Analysis](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Root-Cause-Analysis/page), [Blameless Postmortem Culture](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Incident-Management/Blameless-Postmortem-Culture/page), [Change Management for Reliability](https://notes.kodekloud.com/docs/Fundamentals-of-SRE/Managing-Complexity-Risk-and-Toil/Change-Management-for-Reliability/page) · 2) Note: this section, then the Google SRE book [Effective Troubleshooting](https://sre.google/sre-book/effective-troubleshooting/) and chapters 14–15 from the [table of contents](https://sre.google/sre-book/table-of-contents/) · 3) Read (no video recommended): [GitLab change management](https://handbook.gitlab.com/handbook/engineering/infrastructure-platforms/change-management/), their [2017 database outage postmortem](https://about.gitlab.com/2017/02/10/postmortem-of-database-outage-of-january-31/), and [Debugging: The 9 Indispensable Rules](https://debuggingrules.com/) · 4) Practice: the incident drill (Steps 13–18), the Apache change request, and the game day in section 8.

Everything before this section is about tools. This section is about **behaviour**: how you act when
production is broken, how you change production so it rarely breaks, and how you learn from the
times it does. These habits are what separates a senior engineer from a strong mid-level one, and
they are visible to employers: a sanitized postmortem or change request in a public repository is
better evidence of seniority than another certificate.

### Effective troubleshooting method

**Level:** [L2 · Mid] to practise, [L4 · Lead/SRE] to teach

**Concept.** Your notes already follow the right method: collect evidence, then test one layer at a
time. The SRE book formalises it as a loop, and David Agans' nine rules name the habits that keep
the loop honest:

```
   report ──► triage (how bad? stop the bleeding first)
                 │
                 ▼
   ┌──► examine (logs, metrics, captures: LOOK, do not guess)
   │       │
   │       ▼
   │    diagnose: form ONE hypothesis that explains ALL the evidence
   │       │
   │       ▼
   │    test it: an experiment whose result can prove it wrong
   │       │ (change ONE thing, write down what and when)
   │       ▼
   └── wrong? ── next hypothesis          right? ──► treat ──► verify ──► write it down
```

| Rule (Agans) | What it means on your servers |
|---|---|
| Understand the system | know the path: DNS → Traefik → container → app → DB before debugging it |
| Make it fail | find a command that reproduces it (`curl -v --resolve ...`) |
| Quit thinking and look | `tcpdump`, `ss`, the access log, not "it is probably DNS" |
| Divide and conquer | test the middle of the path (`curl` the container directly) to halve the search |
| Change one thing at a time | one config change, one reload, one test; otherwise you learn nothing |
| Keep an audit trail | timestamped notes of what you ran and saw |
| Check the plug | is it running, listening, on the right port, on the right network? |
| Get a fresh view | explain it to a colleague; the gap in your story is often the bug |
| If you did not fix it, it is not fixed | a problem that "went away" will come back |

**Key terms**

| Term | Meaning |
|---|---|
| Hypothesis | a falsifiable explanation ("Traefik cannot reach 127.0.0.1:81 because that is the container's own loopback") |
| Mitigation | an action that reduces user impact without needing the root cause (rollback, failover, flag off) |
| Root cause | the condition that, if absent, prevents the incident; usually several contributing factors |
| Audit trail | the timestamped record of actions and observations |

**See it on a real system.** Build the audit trail into your shell before you need it:

```bash
# in ~/.bashrc on every admin workstation and jump host
export HISTTIMEFORMAT='%F %T '
# at the start of any incident: record the whole terminal session
mkdir -p ~/incidents && script -a ~/incidents/INC-$(date -u +%Y%m%d-%H%M)-$(hostname).log
history | tail -3
```

```
Script started, output log file is '/home/ops/incidents/INC-20261003-0914-ctrl.log'.
 1012  2026-10-03 09:14:40 curl -sv --resolve api.example.com:443:192.0.2.10 https://api.example.com/healthz
 1013  2026-10-03 09:15:02 docker logs --since 10m dokploy-traefik 2>&1 | grep api.example.com | tail
 1014  2026-10-03 09:15:31 ss -ltnp 'sport = :81'
```

→ Every command now has a timestamp, and the full output is in the `script` log. Writing the
postmortem timeline becomes copying, not remembering.

**Hands-on lab (test VM only)**

**Step 1 — Practise on someone else's failure.** Do three SadServers scenarios (ops ladder morning
reps) and, before typing each command, say the hypothesis it tests.

**Step 2 — Break the method on purpose.** On a lab Traefik route, make **two** changes at once
(wrong backend port **and** wrong Host rule) and try to fix them by changing several things per
attempt. Notice how you lose track of which change fixed what.

**Step 3 — Fix it properly.** Revert both, re-break, and now change one thing per test, logging
each in the `script` session. Compare the two attempts' times and notes.

**How it breaks**

| Anti-pattern | Symptom | Better |
|---|---|---|
| Shotgun debugging | many changes, nobody knows which one fixed it | one change, one test |
| Streetlight | looking where it is easy (the app) rather than where the evidence points (DNS) | follow the layer the evidence names |
| Confirmation bias | ignoring evidence that does not fit the favourite theory | the hypothesis must explain **all** symptoms |
| Fixing before stabilising | debugging for 40 minutes while users are down | mitigate first if a mitigation exists |

**Why it matters for troubleshooting.** This is the whole handbook in one loop. The playbooks
(21–26) are this method applied to specific layers.

**Next step:** do it with other people, under time pressure: incident response.

### Incident roles and severity

**Level:** [L3 · Senior] to participate, [L4 · Lead/SRE] to command

**Concept.** An incident is any unplanned event that degrades a service enough that someone must act
now. The goal of incident response is to **restore service**, not to find the root cause; that comes
later, calmly. Two things make response fast: **clear roles** (so people do not all debug the same
thing while nobody updates the client) and **agreed severity levels** (so everyone knows how loud to
be).

| Role | Does | Does not |
|---|---|---|
| Incident Commander (IC) | owns the incident: decides, delegates, keeps the timeline moving, declares resolved | type commands (in larger incidents) |
| Operations lead | investigates and changes systems, one change at a time, reports to IC | talk to the client |
| Communications lead | posts updates on a fixed rhythm to stakeholders and the client | debug |
| Scribe | writes the timeline with UTC timestamps | decide |

In a two-person team the IC is often also the ops lead; the one role you should still split off is
**communications**, because updates are the first thing forgotten under stress.

| Severity | Definition (adapt to your clients) | Response |
|---|---|---|
| SEV1 | customer-facing service down or data at risk; no workaround | everyone available, IC named, updates every 30 min, client informed immediately |
| SEV2 | major degradation or one important site down; workaround exists | on-call plus one, updates every 60 min |
| SEV3 | minor degradation, internal impact only | on-call, normal hours |
| SEV4 | cosmetic or potential issue | ticket |

**Stabilise before root cause.** Mitigation options in order of preference: roll back the last
change (section 3), switch traffic (blue/green), turn off a feature flag, scale out, fail over, block
an abusive client, serve a maintenance page. You can do all of these without knowing why the release
broke.

**Key terms**

| Term | Meaning |
|---|---|
| Declare | say out loud (in the channel) "this is an incident, SEV2, I am IC" |
| Handover | explicit transfer of IC or ops role, with a summary |
| MTTD / MTTR | mean time to detect / to restore |
| Resolved vs closed | service restored / follow-ups and postmortem done |

**See it on a real system.** "What changed?" in one block, for the incident channel:

```bash
# deployments in the last 2 hours (GitLab)
curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "$GITLAB/projects/$PROJECT_ID/deployments?updated_after=$(date -u -d '-2 hours' +%FT%TZ)&order_by=updated_at&sort=desc" \
  | jq -r '.[] | "\(.updated_at) \(.environment.name) \(.ref) \(.status)"'
# infra repo changes (Traefik routes, Ansible, Terraform)
git -C ~/infra log --since='2 hours ago' --format='%ci %an %s'
# proxy errors and package changes on web01 (Traefik runs as a container: its log is in docker logs, not the journal)
ssh web01 "docker logs --since 2h dokploy-traefik 2>&1 | grep -m1 'connection refused'; grep -h 'install\|upgrade' /var/log/dpkg.log | tail -3"
```

```
2026-10-03T09:02:11Z production v1.4.2 success
2026-10-03 08:58:40 +0000 Ops Engineer Route api.example.com to Apache on 127.0.0.1:81
2026-10-03T09:03:12Z DBG ... 502 Bad Gateway error="dial tcp 127.0.0.1:81: connect: connection refused"
2026-10-03 06:25:01 upgrade libssl3:amd64 3.0.13-0ubuntu3.4 3.0.13-0ubuntu3.5
```

→ Three candidate changes in the window: a release, a Traefik route change, and a library upgrade.
The Traefik log line points straight at the route change: Traefik (in a container) cannot reach
`127.0.0.1:81`, which inside the container is the container itself
(see [Deployment patterns](35-deployment-patterns.md), Step 9).

**Hands-on lab (test VM only)**

**Step 1 — Tabletop.** With a colleague (or alone, playing all roles), walk through "api.example.com
returns 502" using the Steps below on paper: who is IC, what is the first update, what is the
mitigation.

**Step 2 — Break the process.** Repeat with no roles: both of you debug, nobody updates the "client"
(a third person or a timer every 15 minutes). Note how long until the first update would have been
sent.

**Step 3 — Fix it.** Write a one-page incident procedure (roles, severity table, update rhythm,
templates from the next topic) into your runbook repository.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Client hears about the outage from their users | no comms role | comms lead from minute one |
| Two engineers undo each other's changes | no IC, no "one change at a time" | IC approves every change |
| Root-cause hunting while down for an hour | no mitigation mindset | ask "what can we roll back?" first |

**Why it matters for troubleshooting.** Under pressure, good technical skill is wasted without
coordination. The structure is what lets your troubleshooting method survive a real outage.

**Next step:** the first fifteen minutes, step by step.

### Incident: the first fifteen minutes

**Level:** [L3 · Senior]

**Concept.** The running example: at 09:03 UTC monitoring alerts that `api.example.com` returns 502.
The partner at 203.0.113.45 depends on it. Steps 13 to 18 are the first fifteen minutes, in
STEP FORMAT. The point is not the specific bug; it is the **order**: confirm, organise, ask what
changed, mitigate, verify, then hand over to diagnosis.

```
 alert ──► Step 13 confirm impact ──► Step 14 declare + roles + timeline ──► Step 15 what changed?
                                                                                  │
                     Step 18 resolve, keep evidence ◄── Step 17 verify + update ◄─ Step 16 mitigate
```

### Step 13 — Confirm the impact

**Goal:** verify the alert from outside and measure who is affected, in under two minutes.

```bash
# from a host outside web01 (ctrl, or your laptop on the VPN)
for h in shop.example.com api.example.com intranet.example.com app.example.com; do
  printf '%-22s ' "$h"; curl -s -o /dev/null -m 10 -w '%{http_code} %{time_total}s\n' "https://$h/healthz"
done
```

```
shop.example.com       200 0.112s
api.example.com        502 0.009s
intranet.example.com   200 0.098s
app.example.com        200 0.143s
```

**What it means:** one site is down, the others are fine. The 502 comes back in 9 ms, so Traefik
answers instantly but cannot reach its backend: the proxy layer is up, the backend path is broken.
The impact is the API and its partner integration: a customer-facing service with no workaround, so
SEV2 at least (SEV1 if the partner's orders are failing).

**Why this step (now):** alerts can be wrong (a monitoring host losing DNS) and impact decides
severity, which decides who you wake up. Two minutes of confirmation prevents both false alarms and
under-reaction.

**Next step:** confirmed → Step 14. Not reproducible from outside → check the monitoring path itself
(DNS, the probe's network) before declaring. All sites failing → the shared layer (DNS, Traefik,
firewall, host); use [Site down playbook](25-playbook-site-down.md) in parallel with Step 14.

### Step 14 — Declare, assign roles, start the timeline

**Goal:** make the incident official so people, communication and records start in parallel.

```bash
mkdir -p ~/incidents && script -a ~/incidents/INC-20261003-api502-$(hostname).log
date -u '+%F %H:%MZ'
```

```
2026-10-03 09:06Z
```

```
INC-2026-022 | SEV2 | api.example.com returns 502 since ~09:03Z
IC + ops: Ops Engineer | Comms: Team Lead | Scribe: Ops Engineer (script log)
Timeline (UTC)
09:03 alert "api.example.com probe failing" (blackbox)
09:05 confirmed from ctrl: api 502 in 9 ms, shop/intranet/app 200
09:06 declared SEV2, roles assigned, first client update due 09:15
```

**What it means:** the incident has a name, a severity, owners and a clock. The communications lead
can now tell the client "we know, we are on it, next update at 09:30" while you investigate.

**Why this step (now):** it costs one minute and saves many: without it, the first fifteen minutes are
spent on side conversations ("is someone looking at this?") and nobody records the timeline you will
need later.

**Next step:** → Step 15 to find what changed. The comms lead sends the initial update using the
template in the next topic.

### Step 15 — Ask what changed

**Goal:** find recent changes in the affected path, because most incidents follow a change.

```bash
git -C ~/infra log --since='3 hours ago' --format='%ci %h %an %s' -- traefik/
ssh web01 "docker logs --since 15m dokploy-traefik 2>&1 | grep -m3 api.example.com"
ssh web01 "sudo ss -ltnp 'sport = :81'"
```

```
2026-10-03 08:58:40 +0000 c4d5e6f Ops Engineer Route api.example.com to Apache on 127.0.0.1:81
... level=debug ... "error":"dial tcp 127.0.0.1:81: connect: connection refused" ... api.example.com
LISTEN 0 511 192.0.2.10:81 0.0.0.0:* users:(("apache2",pid=1123,fd=4))
```

**What it means:** at 08:58 a route change pointed Traefik at `127.0.0.1:81`. Apache listens on
`192.0.2.10:81`, and inside the Traefik **container** `127.0.0.1` is the container itself, so the
connection is refused. One change, fully explains the symptom (only api affected, instant 502).
Traefik writes this "dial tcp ... connection refused" detail only at log level DEBUG; at the usual
INFO or ERROR level, look for the same router in the JSON access log with `DownstreamStatus` 502 and
`OriginStatus` 0 (no backend answered).

**Why this step (now):** "what changed?" is the highest-yield question in incident response and it is
cheap: three commands. It also tells you which mitigation exists (revert this commit).

**Next step:** a recent change explains the symptom → Step 16, roll it back. No change found →
investigate by layers with the [site down playbook](25-playbook-site-down.md) or the
[containers playbook](26-playbook-containers-k8s.md), keeping the IC updated every 15 minutes.

### Step 16 — Mitigate first

**Goal:** restore service with the fastest safe rollback, before root-causing.

```bash
git -C ~/infra revert --no-edit c4d5e6f && git -C ~/infra push    # pipeline redeploys the Traefik dynamic file
# or, if the pipeline is slow and the IC approves, restore the previous file directly (and commit later):
#   scp web01:/etc/dokploy/traefik/dynamic/legacy-apache.yml.bak ... (record it in the timeline)
sleep 20; curl -s -o /dev/null -w '%{http_code}\n' https://api.example.com/healthz
```

```
[main 7a8b9c0] Revert "Route api.example.com to Apache on 127.0.0.1:81"
 1 file changed, 1 insertion(+), 1 deletion(-)
200
```

**What it means:** the revert restored the previous backend address and the API answers 200. Users
are served again at about 09:12, nine minutes after the alert.

**Why this step (now):** the revert is low-risk (it restores a known-good state), fast, and recorded.
Fixing the route "properly" now would be fixing forward under pressure, which is how one incident
becomes two.

**Next step:** 200 and stable → Step 17. Still failing → the change was not the (only) cause: roll back
the next candidate (the 09:02 release) or continue layer-by-layer diagnosis; tell the IC.

### Step 17 — Verify recovery and update stakeholders

**Goal:** prove recovery with the same signal that alerted, and tell people.

```bash
for i in $(seq 1 30); do curl -s -o /dev/null -w '%{http_code} ' https://api.example.com/healthz; sleep 2; done; echo
ssh web01 "sudo tail -n 200 /var/log/apache2/api_access.log | awk '{print \$9}' | sort | uniq -c"
```

```
200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200 200
    196 200
      4 304
```

**What it means:** sixty seconds of clean 200s, and Apache's own access log shows the requests
arriving again (the backend sees traffic, not just Traefik). The alert should clear on its next
evaluation.

**Why this step (now):** "it works for me once" is not recovery. Checking the user-facing signal and
the backend's own log closes the loop from both ends. Stakeholders need the update now, not after
the postmortem.

**Next step:** stable → send the "mitigated" update (template below) and go to Step 18. Errors return
→ the incident is not over; back to Step 15 with the new evidence.

### Step 18 — Resolve, keep evidence, schedule the postmortem

**Goal:** close the acute phase without losing the information the postmortem needs.

```bash
exit                                     # ends the script session; the log is saved
ls -l ~/incidents/INC-20261003-api502-*.log
ssh web01 "docker logs --since 1h dokploy-traefik > /tmp/INC-2026-022-traefik.log 2>&1; ls -l /tmp/INC-2026-022-traefik.log"
```

```
-rw-r--r-- 1 ops ops 48211 Oct  3 09:21 /home/ops/incidents/INC-20261003-api502-ctrl.log
-rw-r--r-- 1 ops ops 912345 Oct  3 09:22 /tmp/INC-2026-022-traefik.log
```

**What it means:** your terminal record and the proxy logs from the incident window are saved before
log rotation or container restarts remove them.

**Why this step (now):** evidence disappears fast (container logs vanish on recreation, journals
rotate). The postmortem's quality depends on what you keep in this minute.

**Next step:** declare "resolved" with the time, send the resolution update, open a postmortem issue
with an owner and a date within five working days, and create follow-up issues (here: "route legacy
sites to the host IP, not loopback", "add a CI check that rejects 127.0.0.1 in Traefik dynamic
files").

**Incident decision tree**

```
 alert
 ├─ reproducible from outside? ── no ──► check the monitoring path, do not declare yet
 └─ yes ──► impact & severity ──► declare, IC, comms, timeline
             └─ what changed in the last hours?
                 ├─ change explains ALL symptoms ──► roll it back ──► verify ──► resolve
                 ├─ several changes ──► roll back the most likely first, one at a time
                 └─ nothing changed ──► layer walk (DNS → route → firewall → TLS → proxy → app)
                                         with updates every 15–30 min; mitigate as soon as possible
```

**Fix & verify:** the permanent fix (route to `192.0.2.10:81`, or better the Docker gateway address as
in [Deployment patterns](35-deployment-patterns.md)) goes through a normal MR and change request,
with `curl --resolve` checks in the pipeline.

**Rollback:** the mitigation itself was a rollback; if the permanent fix misbehaves, revert it the
same way.

**Prevent it next time:** a CI lint rule for Traefik dynamic files, a staging Traefik that receives
infra changes first, and a blackbox probe per site (it is what detected this one).

### Communication templates and timelines

**Level:** [L3 · Senior]

**Concept.** Good incident updates are short, factual, timestamped, and promise the next update
time. They say what users experience, not what you are typing. Three templates cover almost
everything:

```
INITIAL (within 15 min of declaring)
[SEV2] api.example.com unavailable — investigating
Since 09:03 UTC requests to api.example.com fail with an error. Other sites are not affected.
We are investigating and will update by 09:30 UTC.

UPDATE (on the promised time, even if nothing changed)
[SEV2] api.example.com — mitigated, monitoring
At 09:12 UTC we reverted a configuration change made at 08:58 UTC. Since then the API responds
normally. Requests between 09:03 and 09:12 UTC may have failed and can be retried.
Next update by 10:00 UTC or when resolved.

RESOLVED
[SEV2] api.example.com — resolved
The API was unavailable from 09:03 to 09:12 UTC (9 minutes) after a routing change.
Service is fully restored. A post-incident review will follow by 2026-10-08.
```

The **timeline** is the backbone of the postmortem. Write it in UTC, one line per event, with the
source of each fact:

```
09:03 blackbox probe api.example.com fails (Prometheus alert ApiDown)          [alert]
09:05 confirmed: api 502 in 9 ms; shop, intranet, app 200                      [curl from ctrl]
09:06 SEV2 declared; IC/ops Ops Engineer; comms Team Lead                      [chat]
09:08 Traefik log: dial tcp 127.0.0.1:81 connection refused                     [docker logs]
09:09 infra commit c4d5e6f at 08:58 changed api route to 127.0.0.1:81           [git log]
09:11 revert pushed; pipeline 4830 applied previous route                       [GitLab]
09:12 api 200; Apache access log shows traffic                                  [curl, access log]
09:21 resolved; evidence saved                                                  [script log]
```

**Key terms**

| Term | Meaning |
|---|---|
| Update cadence | promised interval between updates (SEV1 30 min, SEV2 60 min) |
| Customer impact statement | what users experienced, in their words |
| Time to detect / mitigate / resolve | derived from the timeline; the metrics postmortems track |

**See it on a real system.** Most timelines can be rebuilt from three sources: the alert history
(Alertmanager or Prometheus `ALERTS` series), the GitLab deployment and commit history, and your
`script` log with `HISTTIMEFORMAT` timestamps. Practise pulling all three for one lab incident.

**Hands-on lab (test VM only)**

**Step 1 — Write the three updates** for the Traefik 502 example in under five minutes total.

**Step 2 — Break it.** Write an update that includes "we think it is probably DNS" and internal
hostnames. Read it as the client would: speculation and jargon create more questions.

**Step 3 — Fix it** with facts, user impact and the next update time only.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Client escalates during the incident | no updates or missed promised time | fixed cadence, set a timer |
| Postmortem timeline has gaps | nobody scribing | `script` log, scribe role |
| Update promises a fix time you miss | guessing | promise the next update, not the fix |

**Why it matters for troubleshooting.** Clear communication buys you the quiet time to troubleshoot.
A client who receives updates does not call you every five minutes.

**Next step:** learn from the incident: the blameless postmortem.

### Blameless postmortems

**Level:** [L3 · Senior] to write, [L4 · Lead/SRE] to run the review

**Concept.** A postmortem is a written analysis of an incident whose purpose is **learning and
prevention**, not punishment. **Blameless** means you assume everyone acted reasonably given what
they knew at the time, and you ask "how did the system let this happen?" instead of "who did it?".
If people fear blame they hide information, and hidden information is how the same incident happens
twice. A postmortem is written for every SEV1 and SEV2, for every incident with data loss, and for
any near miss that taught you something.

The **five-line incident note** from your weekly rhythm is the seed of every postmortem: symptom,
first wrong guess, evidence that settled it, fix, what you will check first next time. The template
below grows it into the SRE book's structure.

```markdown
# Postmortem: INC-2026-022 — api.example.com 502 after Traefik route change

Status: final · Date: 2026-10-03 · Authors: Ops Engineer · Reviewers: Team Lead
Severity: SEV2 · Duration: 09:03–09:12 UTC (9 min) · Detection: blackbox probe (2 min)

## Summary
A routing change pointed Traefik at 127.0.0.1:81 for api.example.com. Inside the Traefik
container, 127.0.0.1 is the container itself, so every API request failed with 502 for 9 minutes.
Reverting the change restored service.

## Impact
- api.example.com: 100% of requests failed 09:03–09:12 UTC (about 1,150 requests).
- Partner 203.0.113.45: 212 order-sync calls failed; their client retried all of them by 09:20.
- No data loss. Other sites unaffected.

## Timeline (UTC)
(the timeline from the incident, with sources)

## Root cause and contributing factors
- Root cause: the Traefik file-provider route used 127.0.0.1:81, which is unreachable from a container.
- Contributing: the change was tested with curl on the host (where 127.0.0.1:81 works), not through Traefik.
- Contributing: no staging Traefik; infra changes go straight to web01.
- Contributing: the pipeline for the infra repo has no lint for loopback backends.

## What went well
- Alert fired within 2 minutes; "what changed?" found the commit in 3 minutes; revert was one command.

## What went wrong
- The change request had no "verify through Traefik with curl --resolve" step.

## Where we got lucky
- The partner's client retries; another integration might not.

## Action items
| # | Action | Type | Owner | Due | Issue |
|---|--------|------|-------|-----|-------|
| 1 | Route legacy sites to the docker_gwbridge gateway / host IP, not loopback | fix | Ops Engineer | 2026-10-06 | infra#118 |
| 2 | CI lint: reject 127.0.0.1/localhost backends in traefik/dynamic/*.yml | prevent | Ops Engineer | 2026-10-10 | infra#119 |
| 3 | Add "curl --resolve through Traefik" to the CR verification template | process | Team Lead | 2026-10-10 | infra#120 |
| 4 | Staging Traefik on the dokploy lab VM receives infra changes first | prevent | Ops Engineer | 2026-10-31 | infra#121 |

## Lessons
Testing from the host is not testing from the proxy's network namespace.
```

**Key terms**

| Term | Meaning |
|---|---|
| Contributing factor | a condition that made the incident possible or worse; there are usually several |
| Action item types | detect, mitigate, prevent, fix, process; each with owner, due date and an issue |
| Five whys | asking "why" repeatedly; useful, but stop at system causes, never at a person |
| Near miss | an incident that almost happened; often the cheapest lesson |

**See it on a real system.** Read real ones. The ops ladder's Sunday reading is exactly this: pick
one from [k8s.af](https://k8s.af/) or [Dan Luu's list](https://github.com/danluu/post-mortems), and
GitLab's [2017 database outage](https://about.gitlab.com/2017/02/10/postmortem-of-database-outage-of-january-31/).
Before reading the root-cause section, write down which layer you think failed. Then list three
controls that would have stopped the GitLab outage in **your** environment (ops ladder L4 drill), for
example: backups that are restored and verified on a schedule, a prompt or hostname colour that makes
production obvious, and a second person on destructive commands.

**Hands-on lab (test VM only)**

**Step 1 — Write a postmortem** for one of your own lab "break it" exercises from this module, using
the template, in under 45 minutes.

**Step 2 — Break it on purpose.** Write the root cause as "engineer used the wrong IP". Read it back:
the only action item it suggests is "be more careful", which prevents nothing.

**Step 3 — Fix it.** Rewrite it as system causes (no lint, no staging, test from the wrong namespace)
with concrete, owned action items. Publish the sanitized version in your portfolio repo (last topic
of this section).

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Same incident again in three months | action items without owners or due dates | track them as issues; review in a weekly meeting |
| People avoid writing postmortems | blame culture or postmortems used in performance reviews | blameless wording, managers model it |
| Postmortem is a 10-page novel | no template | the template above, one page for SEV2 |

**Why it matters for troubleshooting.** Your postmortems become the case library of your own
environment. The next time a similar symptom appears, the "what you will check first next time"
line saves the first twenty minutes.

**Next step:** prevent incidents caused by change: change management.

### Change management

**Level:** [L3 · Senior] to write CRs, [L4 · Lead/SRE] to own the process

**Concept.** Most outages are caused by changes, so the cheapest reliability work is making changes
safer. **Change management** is not bureaucracy; it is writing down, **before** the change: what
exactly you will do, how risky it is, how you will know it worked, and how you will undo it. GitLab
runs its own production this way and publishes the format: every change request (CR) states its
**criticality**, **steps** with expected durations, **verification**, and **rollback** with a
trigger, and risky changes are rehearsed with **dry runs**.

| Criticality (GitLab-style, 1 = highest) | Examples in your environment | Required |
|---|---|---|
| C1 | database migration with no rollback, firewall change on the edge, anything that can cause data loss or a full outage | peer review + approval, maintenance window, rehearsal on staging, IC on standby |
| C2 | moving Apache off 80/443, installing Dokploy on web01, Kubernetes upgrade | peer review + approval, maintenance window, tested rollback |
| C3 | retiring an idle service, adding a Traefik route, rotating a credential | peer review, rollback written |
| C4 | adding a DNS record for a new name, a dashboard change | normal MR |

Change types: **standard** (pre-approved, repeatable, low risk, such as a routine deploy through the
pipeline), **normal** (needs a CR and review), **emergency** (during an incident; approved verbally by
the IC, documented afterwards).

**Dry runs** you already know from this module: `ansible-playbook --check --diff`, `terraform plan`,
`apache2ctl configtest`, `docker compose config`, `kubectl apply --dry-run=server`, `curl --resolve`
against a new route before DNS changes.

**Key terms**

| Term | Meaning |
|---|---|
| CR | change request: a GitLab issue (or MR) with the template below |
| Rollback trigger | the measurable condition that ends the attempt |
| Change freeze | a period with no normal changes (holidays, client events) |
| Pre-flight checks | conditions that must all be true before step 1 |

**See it on a real system.** Keep the template in the infra project so every CR starts from it:

```bash
ls .gitlab/issue_templates/
sed -n '1,12p' .gitlab/issue_templates/change-request.md
```

```
change-request.md  incident.md  postmortem.md
### Change summary
### Criticality (C1–C4) and why
### Window and communication
### Pre-flight checks (all must pass)
### Steps (with expected duration)
### Verification
### Rollback (trigger, steps, expected duration)
### Dry run evidence
### Monitoring during the change
```

→ GitLab offers these templates in the "New issue" form. The template is the process: if a section
is empty, the change is not ready.

**Hands-on lab (test VM only)**

**Step 1 — Write a CR** for "add the Docker role to target3" using the template, including the
`--check --diff` output as dry-run evidence.

**Step 2 — Break it.** Execute a change without a CR in the lab (change Traefik's entrypoint port
"quickly") and then try to write the rollback afterwards from memory.

**Step 3 — Fix it** by writing the CR for the same change before redoing it, and compare how long the
rollback takes with and without a written procedure.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Rollback improvised during the window | no rollback section | CR not approved without one |
| "Small" change causes an outage | criticality underestimated | criticality table with concrete examples |
| CRs approved without reading | rubber-stamping | reviewers must comment on rollback and verification |

**Why it matters for troubleshooting.** When something breaks during or after a change, the CR is
your map: you know every step taken, in order, and the rollback is already written.

**Next step:** the example the ops ladder asks for: the CR that retires system Apache.

### Example CR: retire system Apache

**Level:** [L4 · Lead/SRE] (the ops ladder L4 drill)

**Concept.** This is the change request the ops ladder asks you to write **before** you do it at
work: "write the change request for disabling system Apache in GitLab's format (criticality, steps,
verification, rollback)". It starts from where you are today: Apache was moved to ports 81 and 444
to give Traefik 80/443 ([Deployment patterns](35-deployment-patterns.md), section 1), the legacy
sites were then routed through Traefik and moved into Dokploy one by one
([case study](21-case-apache-443-dokploy.md)), and Apache should now be serving nothing. This CR
**proves** that and then disables it, keeping the package and config for a fast rollback. Removing the
package is a separate, later CR.

```markdown
### CR-2026-031: web01 — disable system Apache (apache2) after migration to Dokploy

### Change summary
Since the 81/444 move, shop, api and intranet were migrated to Dokploy apps behind Traefik
(CR-2026-024, -027, -029). Apache on 192.0.2.10:81/444 should receive no user traffic.
This change: confirm zero traffic, remove the legacy Traefik route file, stop and disable apache2,
close 81/444 in UFW. Package, /etc/apache2 and docroots stay for 30 days (rollback path).
Out of scope: apt purge (CR to follow after 30 days), certbot cleanup (step 9 only checks it).

### Criticality: C3 (would be C2 if any site still depended on Apache)
All sites already run in Dokploy; Apache is idle; rollback is a service start (< 2 min).
Customer-facing names are involved, so: peer review, window, written rollback.

### Window and communication
Thu 2026-10-15 06:30–07:00 UTC (quietest half hour in Traefik access logs).
Client informed 2026-10-12. Partner 203.0.113.45 informed (api moved to Dokploy on 2026-10-06, after INC-2026-022).

### Pre-flight checks (all must pass, evidence pasted below)
- [ ] Apache access logs: 0 non-monitoring requests on each of the last 7 days (per-day counts;
      dd/Mon/yyyy dates cannot be compared as strings)
      sudo zcat -f /var/log/apache2/*access.log* | grep -v 'blackbox' | awk '{print substr($4, 2, 11)}' | sort | uniq -c
- [ ] Traefik routes for shop/api/intranet point at Dokploy services, not 192.0.2.10:81
      grep -R '192.0.2.10:81\|:444' /etc/dokploy/traefik/dynamic/   (only legacy-apache.yml may match)
- [ ] Each site healthy through Traefik: curl --resolve SITE:443:192.0.2.10 https://SITE/healthz = 200
- [ ] Nothing else uses Apache: no ProxyPass targets in use by other hosts, cron/timers checked
      grep -R 'apache2ctl\|apachectl\|systemctl .*apache2' /etc/cron* /etc/systemd/system 2>/dev/null
- [ ] Backup B2 of /etc/apache2, /var/www, /etc/letsencrypt taken, listed and copied off-host
- [ ] Monitoring: apache-specific checks (process, port 81) silenced for the window
- [ ] Rollback rehearsed on the dokploy lab VM (time: 1 min 40 s)

### Steps (expected duration)
1. Announce start in the change channel (1 min)
2. Move legacy-apache.yml out of /etc/dokploy/traefik/dynamic/ (Traefik reloads it) (1 min)
3. Verify all four sites through Traefik: status, cert issuer, /version (3 min)
4. sudo systemctl stop apache2 ; verify ss -ltnp shows nothing on :81/:444 (1 min)
5. Verify all four sites again; watch Traefik logs for 5xx for 10 min (10 min)
6. sudo systemctl disable apache2 (1 min)
7. sudo ufw delete allow 81/tcp ; sudo ufw delete allow 444/tcp (if those rules exist) (1 min)
8. Commit the removal of legacy-apache.yml in the infra repo (MR !212) (2 min)
9. Check certbot: renewal configs using the apache authenticator are no longer needed
   (Traefik issues certs now); list them in the follow-up CR, do not delete today (2 min)
10. Announce end (1 min)

### Verification
- curl -s -o /dev/null -w '%{http_code}' https://SITE/healthz → 200 for all four sites
- openssl s_client -connect 192.0.2.10:443 -servername SITE → issuer = Let's Encrypt via Traefik
- systemctl is-enabled apache2 → disabled ; systemctl is-active apache2 → inactive
- ss -ltnp | grep -E ':(81|444) ' → no output
- Traefik access log: no 5xx increase compared to the previous 30 min

### Rollback (trigger: any site non-200 for > 5 min, or Traefik 5xx > 1% for 5 min)
1. sudo systemctl enable --now apache2 ; ss -ltnp 'sport = :81' shows apache2 (1 min)
2. Restore legacy-apache.yml into /etc/dokploy/traefik/dynamic/ from the infra repo (1 min)
3. Verify the failing site through Traefik with curl --resolve (2 min)
Expected total: 4 min. Rollback owner: Ops Engineer; decision: Team Lead (IC for the window).

### Dry run evidence
(paste: 7-day access log count, grep of dynamic routes, curl matrix, rehearsal timing)

### Monitoring during the change
docker logs -f dokploy-traefik | grep -E '" (5[0-9]{2}) '  ·  blackbox probes for 4 sites
· partner contact available 06:30–07:30 UTC
```

**Key terms**

| Term | Meaning |
|---|---|
| Disable vs mask vs purge | `disable` removes boot start; `mask` prevents any start; `purge` removes package and config |
| Scream test | turning something off to see who complains; only acceptable with a fast rollback and a window |
| Evidence-based retirement | proving zero use from logs before turning a service off |

**See it on a real system.** The pre-flight evidence commands, read-only, on web01:

```bash
sudo zcat -f /var/log/apache2/*access.log* | awk '{print $1}' | sort | uniq -c | sort -rn | head -5
systemctl list-timers --all --no-pager | grep -Ei 'certbot|apache' ; ls /etc/letsencrypt/renewal/
sudo grep -h '^authenticator' /etc/letsencrypt/renewal/*.conf | sort | uniq -c
```

```
   2016 172.18.0.3
     14 192.168.56.70
Thu 2026-10-15 12:41:00 UTC 6h left  Wed 2026-10-14 23:12:04 UTC  7h ago  certbot.timer  certbot.service
api.example.com.conf  intranet.example.com.conf  shop.example.com.conf
      3 authenticator = apache
```

→ The only clients are `172.18.0.3` (the Traefik container's address on docker_gwbridge, the bridge it
uses to reach the host: Traefik's health checks or a forgotten route) and `192.168.56.70` (the monitoring host). 2,016 requests from Traefik in the window
means **something still routes to Apache**: find which Host header those requests carry before
proceeding. And certbot still renews three certificates with the Apache authenticator; once Apache is
stopped, those renewals will fail and send warning emails. Both are exactly the kind of surprise the
pre-flight section exists to catch.

**Hands-on lab (test VM only)**

**Step 1 — Rehearse** the CR on the dokploy lab VM with a lab Apache on 81/444 and one Traefik file
route to it. Time the rollback.

**Step 2 — Break it.** Leave one Traefik route pointing at Apache and run the change: that site returns
502 at step 5. Execute the rollback exactly as written and time it.

**Step 3 — Fix the CR.** Add the "Traefik requests by Host header" check to pre-flight (`awk` on the
Apache log's Host field, or the Traefik access log by `ServiceName`) and rehearse again until it passes.

**How it breaks**

| Symptom | First command | Cause |
|---|---|---|
| A site 502s after Apache stops | Traefik log for that host | a route still pointed at Apache; pre-flight missed it |
| Apache is running again after a reboot | `systemctl is-enabled apache2` | stopped but not disabled; or another unit `Wants=` it |
| Certbot renewal failure emails | `sudo certbot renew --dry-run` | apache authenticator left behind |
| Monitoring pages at 06:31 | alert rules for apache | checks not silenced or not updated |

**Why it matters for troubleshooting.** Retiring things is where hidden dependencies surface. A CR with
evidence-based pre-flight turns "who still uses this?" into data, and the rehearsed rollback makes
being wrong cheap.

**Next step:** the document you reach for during an incident: the runbook.

### Runbooks

**Level:** [L2 · Mid] to use, [L3 · Senior] to write

**Concept.** A **runbook** is the operating manual for one service or one alert: what it is, how it is
deployed, where its logs are, how to check it, and what to do for each known failure. It is written
for the person on call at 3 a.m. who did not build the service. The best runbooks are short, linked
from the alert itself, tested in drills, and updated after every incident.

```markdown
# Runbook: shop-web (Dokploy app on web01)

Owner: Ops Engineer · Last tested: 2026-10-03 · Dashboards: Grafana "shop-web"
What: Python app (gunicorn :8000) behind Dokploy's Traefik; image harbor.example.com/shop/shop-web
Deploy: GitLab pipeline (staging on main, production on tag vX.Y.Z); rollback job "rollback-production"
Logs: docker service logs shop-web-x1y2z3 · Traefik: docker logs dokploy-traefik · App: /version, /healthz

## Alert: ShopWebDown (probe /healthz failing)
1. Confirm: curl -s -o /dev/null -w '%{http_code}' https://shop.example.com/healthz
2. 502 → Traefik cannot reach the app: docker service ps shop-web-x1y2z3 (task state), app port 8000?
3. 404 → no router matched: domain in Dokploy, Host rule, redeploy after domain change
4. Task restarting → docker service logs --tail 100 shop-web-x1y2z3; OOM? exit code 137?
5. Started after a deploy (GitLab Environments) → run rollback-production, then investigate
Escalate: Team Lead after 30 min or immediately for SEV1.
```

**Key terms**

| Term | Meaning |
|---|---|
| Alert runbook link | an annotation (`runbook_url`) on the Prometheus alert pointing to the right section |
| Playbook vs runbook | in this handbook, playbooks are generic methods (21–26); runbooks are per service |
| Toil candidate | a runbook step done often enough to automate |

**See it on a real system.** Check that every alert links to a runbook:

```bash
grep -L 'runbook_url' /etc/prometheus/rules/*.yml
grep -h 'runbook_url' /etc/prometheus/rules/*.yml | sort | uniq -c | head -5
```

```
/etc/prometheus/rules/node.yml
      1     runbook_url: https://gitlab.example.com/ops/runbooks/-/blob/main/shop-web.md#alert-shopwebdown
```

→ `node.yml` has alerts without any runbook link: the person paged by "disk 90%" gets no guidance.
That is a gap to close before it costs someone an hour at night.

**Hands-on lab (test VM only)**

**Step 1 — Write the runbook** for your lab `shop-web` from the template, and add `runbook_url` to its
alert (see [Observability](32-learn-performance-observability.md) for alert rules).

**Step 2 — Break it.** Hand the runbook to someone else (or yourself in a week) with a broken lab app
and no other help. Note every place they got stuck.

**Step 3 — Fix it** by rewriting those steps with exact commands and expected outputs.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| On-call ignores the runbook | outdated or vague | update after every incident; "last tested" date |
| Runbook says "check the logs" | no exact command | write the command and what good output looks like |
| Runbook lives on one laptop | not in Git | runbooks repo, linked from alerts |

**Why it matters for troubleshooting.** A runbook is your troubleshooting knowledge in a form other
people can use. It is also how you stop being the only person who can fix things, which is a
prerequisite for taking holidays and getting promoted.

**Next step:** being on call without burning out.

### On-call hygiene

**Level:** [L3 · Senior] to be on call, [L4 · Lead/SRE] to design the rotation

**Concept.** On-call means you are reachable and able to act within an agreed time. It is sustainable
only if pages are **rare, real and actionable**. Every page should be urgent, about user-visible
symptoms (or imminent ones, such as a disk full in 4 hours), and have a runbook. Everything else is a
ticket or a dashboard. Healthy rotations have a handover, compensation or time off, and a weekly
review of every page.

| Practice | Why |
|---|---|
| Page on symptoms (site down, error rate, latency), not causes (CPU 90%) | high CPU without user impact is not worth waking up for |
| Every alert has an owner and a runbook | an unowned alert becomes noise |
| Weekly page review: delete, tune or automate | alert fatigue is fixed by removing alerts |
| Handover note at rotation change | open incidents, risky changes planned, known flaky alerts |
| Escalation path written down | nobody should wonder who to call |
| No changes on Friday evening without the on-call's agreement | the on-call inherits your change |

**Key terms**

| Term | Meaning |
|---|---|
| Page vs ticket | wakes a human now vs handled in working hours |
| Alert fatigue | so many alerts that real ones are ignored |
| Escalation policy | who is paged next if the first person does not acknowledge |
| Acknowledge (ack) | "I have it", stops further escalation |

**See it on a real system.** How noisy were last week's alerts? From Prometheus (lab):

```bash
curl -s 'http://192.168.56.10:9090/api/v1/query' \
  --data-urlencode 'query=sort_desc(sum by (alertname) (count_over_time(ALERTS{alertstate="firing"}[7d])))' \
  | jq -r '.data.result[] | "\(.value[1])\t\(.metric.alertname)"' | head
```

```
2016	HighCPU
288	DiskSpaceLow
12	ShopWebDown
1	TargetDown
```

→ `HighCPU` was firing for most of the week (with this lab's 5-minute rule evaluation interval, 2016 samples is the whole week): it
is noise and should be deleted or turned into a symptom-based alert. `ShopWebDown` fired for a real
incident. Count of samples is a rough measure, but enough to start the review.

**Hands-on lab (test VM only)**

**Step 1 — Review your lab alerts** with the query above and classify each as page, ticket or delete.

**Step 2 — Break it.** Add an alert on CPU above 50% and run the stress-ng drill from the ops ladder:
it pages constantly while users are fine.

**Step 3 — Fix it** by replacing it with a latency or error-rate alert on the service.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Real alert missed | alert fatigue | delete noisy alerts |
| Same person always paged | no rotation | rotation plus escalation |
| Pages without action | cause-based alerts | symptom-based alerting (see [Observability](32-learn-performance-observability.md)) |

**Why it matters for troubleshooting.** A well-run on-call means you start incidents rested and with
a runbook, which directly improves how well you troubleshoot.

**Next step:** remove the repetitive work that fills on-call weeks: toil.

### Toil reduction

**Level:** [L3 · Senior] to spot, [L4 · Lead/SRE] to budget

**Concept.** **Toil** is operational work that is manual, repetitive, automatable, reactive, without
lasting value, and that grows linearly with the service. Restarting a stuck container every Monday,
renewing a certificate by hand, creating the same Harbor robot for every project, cleaning a full
runner disk: all toil. The SRE book suggests keeping toil under about half of an engineer's time; the
rest goes into engineering work that removes toil permanently.

| Toil you have | Engineering that removes it |
|---|---|
| Manually checking which app owns a port | the inventory script from [Ports inventory](22-playbook-ports-inventory.md) |
| Installing Docker and daemon.json by hand | the Ansible role in section 4 |
| Building and deploying by SSH | the pipeline in section 2 |
| Cleaning runner disks when CI fails | a systemd timer + disk alert |
| Renewing certs by hand | Traefik / cert-manager ACME |
| Creating VMs by clicking in Proxmox | Terraform module in section 5 |

**Key terms**

| Term | Meaning |
|---|---|
| Toil budget | the maximum share of time the team accepts for toil |
| Automation ROI | time saved per month vs time to automate and maintain |
| Self-service | turning a ticket you handle into a button or pipeline others run |

**See it on a real system.** Measure before automating: your own shell history is data.

```bash
history | awk '{ $1=$2=$3=""; print $0 }' | sed 's/^ *//' | cut -c1-40 | sort | uniq -c | sort -rn | head -5
```

```
     87 docker ps --format 'table {{.Names}}\t{{.Port
     41 sudo ss -ltnp
     33 sudo systemctl restart shop-worker
     19 sudo du -xh --max-depth=1 /var/lib/docker
     12 ssh web01 sudo tail -f /var/log/apache2/
```

→ 33 manual restarts of `shop-worker` is a bug report, not a habit: find why it hangs (or at least
add a health check and `Restart=on-failure`). 19 disk checks on Docker hosts say "add the disk alert
and the cleanup timer".

**Hands-on lab (test VM only)**

**Step 1 — List your top five toil items** for a week from history and incident notes.

**Step 2 — Break it.** Automate one badly: a cron job that restarts `shop-worker` every hour "to be
safe". Note that it hides the hang and breaks in-flight work.

**Step 3 — Fix it** properly: health check, `Restart=on-failure`, an alert on restart count, and an
issue to fix the hang.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Automation that nobody understands | no docs, no owner | automation is code: Git, review, README |
| Cron restarts hide real bugs | automating the symptom | fix the cause; alert on restarts |
| Team always busy, nothing improves | toil above budget | protect engineering time |

**Why it matters for troubleshooting.** Every hour of toil removed is an hour available for the
deep troubleshooting and design work that senior roles are measured on.

**Next step:** decide how reliable is reliable enough: SLOs and error budgets.

### SLOs and error budgets

**Level:** [L4 · Lead/SRE]

**Concept.** A **Service Level Indicator** (SLI) measures what users experience, such as the share
of successful requests or the share of requests faster than 300 ms. A **Service Level Objective**
(SLO) is the target for that SLI over a window: "99.5% of requests to shop.example.com succeed over
30 days". The **error budget** is what is left: 0.5% of requests, or about 3.6 hours of full outage
per 30 days. The budget turns reliability arguments into a number: if there is budget left, ship
features and take reasonable risks; if it is spent, slow down and invest in reliability. The full
treatment, with PromQL, is in [Observability](32-learn-performance-observability.md).

| SLO | Allowed bad time per 30 days |
|---|---|
| 99% | 7 h 12 min |
| 99.5% | 3 h 36 min |
| 99.9% | 43 min |
| 99.95% | 21 min 36 s |

**Key terms**

| Term | Meaning |
|---|---|
| SLI | good events / valid events, measured where users are (Traefik, blackbox probe) |
| SLO | target for an SLI over a rolling window |
| SLA | a contract with penalties; should be looser than the SLO |
| Burn rate | how fast the budget is being spent; alerts fire on fast burn |

**See it on a real system.** Availability SLI from Traefik metrics (Prometheus, lab):

```bash
curl -s 'http://192.168.56.10:9090/api/v1/query' --data-urlencode \
 'query=1 - (sum(rate(traefik_service_requests_total{service=~"shop.*",code=~"5.."}[30d])) / sum(rate(traefik_service_requests_total{service=~"shop.*"}[30d])))' \
 | jq -r '.data.result[0].value[1]'
```

```
0.99731
```

→ 99.73% success over 30 days against a 99.5% SLO: about 46% of the error budget is left
(0.27% used of 0.5%). Releases can continue; the INC-2026-022 type incidents are what spent the rest.

**Hands-on lab (test VM only)**

**Step 1 — Define one SLO** for your lab `shop-web` and compute it as above.

**Step 2 — Break it.** Run a release with a bug that returns 500 on 10% of requests for 20 minutes and
recompute: see how much budget one bad release spends.

**Step 3 — Fix it** with a burn-rate alert (see module 32) and a written policy: "if more than 50% of
the budget is spent, only reliability changes until it recovers".

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| SLO always 100% | measuring the wrong thing (host up, not requests OK) | measure at the edge, per request |
| Budget spent, nothing changes | no policy | agree the policy with the client or product owner |
| 99.99% promised on one VM | target not grounded in the architecture | set SLOs the design can meet (see [Senior architecture](39-learn-senior-architecture.md)) |

**Why it matters for troubleshooting.** SLOs tell you which incidents matter most and how much risk
the next change may take. They also make the case for the reliability work your postmortems ask for.

**Next step:** show the world what you can do: the public portfolio.

### Your public portfolio

**Level:** [L2 · Mid] to start, [L4 · Lead/SRE] to lead with it

**Concept.** Remote and senior roles are hired on **written evidence**. Your Apache to Dokploy
write-up is already that kind of document. Keep a public Git repository of **sanitized** runbooks,
postmortems, change requests and the automation from this module, one folder per level you clear. It
shows how you think: evidence, method, rollback, learning.

```
ops-portfolio/
├── README.md                     who you are, what each folder proves, levels cleared
├── L1-operator/ports-inventory.sh + README (the 5-minute port → app → logs drill)
├── L2-troubleshooter/postmortem-dns-in-containers.md
├── L3-platform/
│   ├── gitlab-ci-harbor-dokploy/    .gitlab-ci.yml, Dockerfile, rollback test notes
│   ├── ansible-docker-role/         role + molecule or check-mode evidence
│   └── case-apache-81-444-to-traefik.md
└── L4-sre/
    ├── cr-retire-system-apache.md
    ├── postmortem-api-502-loopback.md
    └── game-day-2026-11.md
```

**Sanitization checklist** (every file, before every push):

- Hostnames to `example.com`, IPs to documentation ranges (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24).
- No client names, internal URLs, ticket IDs that identify the client, screenshots with real data.
- No secrets, tokens, certificate private keys or `config.json`; run gitleaks before pushing.
- Get your employer's agreement for anything derived from work, and say in the README that details are changed.

**Key terms**

| Term | Meaning |
|---|---|
| Sanitize | remove or replace anything identifying or sensitive |
| Proof of work | artefacts that show your method, not just claims on a CV |
| Write-up | the narrative version: problem, evidence, decision, result |

**See it on a real system.** Check a portfolio repo before pushing:

```bash
gitleaks git --redact . && echo "no secrets found"
git grep -nE '([0-9]{1,3}\.){3}[0-9]{1,3}' | grep -vE '192\.0\.2\.|198\.51\.100\.|203\.0\.113\.|192\.168\.56\.|172\.1[78]\.0\.|127\.0\.0\.1' | head
```

```
INF no leaks found
no secrets found
L2-troubleshooter/postmortem-dns-in-containers.md:41:nameserver 10.20.30.53
```

→ No secrets, but one real internal resolver address slipped through. Replace it with `192.0.2.53`
before pushing.

**Hands-on lab (test VM only)**

**Step 1 — Create the repository** with the structure above and publish your first sanitized item
(the Git revert drill or the ports inventory script).

**Step 2 — Break it.** Copy a real log excerpt into a postmortem and run the checks: they flag it.

**Step 3 — Fix it** and make the two checks a pre-commit hook in the portfolio repo.

**How it breaks**

| Symptom | Cause | Fix |
|---|---|---|
| Employer asks you to take a post down | client details recognisable | sanitize harder; ask first |
| Nobody reads it | no README, no narrative | a README that says what each item proves |
| Repo is a dump of configs | no write-ups | every folder gets a one-page explanation |

**Why it matters for troubleshooting.** Writing for others forces you to make your reasoning
explicit, which is the best way to find gaps in it. And it is how the next employer sees you are
already senior. The [career ladder](40-career-ladder.md) shows how to use it in interviews.

**Next step:** prove all of this under realistic pressure: the game day (section 8).

---

## 8. L4 exit test: the game day

> 📚 **Study path:** 1) Note: [Observability](32-learn-performance-observability.md) sections 11–12 first (Prometheus, Alertmanager, the alert rules this test depends on) · 2) KodeKloud: *Prep Course - Prometheus Certified Associate (PCA)* — Prometheus Fundamentals (Node Exporter) → Alerting ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)), then *Fundamentals of SRE* — Incident Management and Chaos Engineering ([course](https://kodekloud.com/courses/fundamentals-of-sre)) · 3) Video: KodeKloud *Kubernetes Monitoring Made Easy with Prometheus* ([YouTube](https://www.youtube.com/watch?v=6xmWr7p5TE0)) if alerting still feels abstract · 4) Practice: Steps 19–25 below on your homelab, then publish the postmortem in your portfolio.

The ops ladder's L4 exit test: **a script breaks one thing in the homelab at random; you learn about
it from an alert, fix it, and publish a one-page postmortem with timeline, root cause and
follow-ups.** It tests everything in this module at once: monitoring that actually pages, a
method under pressure, a rollback mindset, the incident process, and the written learning. Run it
first alone with a sealed answer, then with a colleague as game master.

| Pass criteria | Why |
|---|---|
| You learned about the breakage from an **alert**, not by looking | detection is the first SRE skill; a dashboard nobody watches detects nothing |
| Service restored within **60 minutes** of the alert | mitigation speed is what users feel |
| Root cause named **with evidence** (a log line, a metric, a command output) | not a guess that happened to be right |
| One-page postmortem published within **24 hours** with timeline, root cause, follow-ups | the learning is the deliverable |
| Every follow-up has an owner and an issue | otherwise nothing changes |

```
 game master                          responder (you)
 ───────────                          ──────────────
 Step 19 prove alerts reach you  ◄──► (together)
 Step 20 prepare chaos + answer
 Step 21 run it at a random time ───► normal work ... ALERT
                                      Step 22 triage with the incident process
                                      Step 23 mitigate, fix, verify, stop the clock
                                      Step 24 postmortem (24 h)
 Step 25 score with the sealed answer ◄──►
```

### Step 19 — Prove detection before breaking anything

**Goal:** confirm the alert rules exist and that a firing alert actually reaches you.

```bash
# on the monitoring VM (ctrl in the lab): rules loaded in Prometheus
curl -s http://192.168.56.10:9090/api/v1/rules | jq -r '.data.groups[].rules[] | "\(.health)\t\(.name)"'
# end-to-end: fire a synthetic alert through Alertmanager and check your phone/mail
amtool alert add alertname=GameDayTest severity=page instance=lab \
  --annotation=summary="game day detection test" --alertmanager.url=http://192.168.56.10:9093
amtool alert query --alertmanager.url=http://192.168.56.10:9093
```

```
ok	HostDiskSpaceAbove85
ok	HostDiskWillFillIn4Hours
ok	SystemdUnitFailed
ok	BlackboxProbeFailed
ok	HostHighLoad
ok	TargetDown
Alertname     Starts At                Summary                   State
GameDayTest   2026-10-03 10:02:11 UTC  game day detection test   active
```

**What it means:** six rules are loaded and healthy (`ok`; `err` would mean a bad expression), and
Alertmanager accepted the synthetic alert. The test is only passed when the **notification** arrives
where you will see it (mail, chat, phone). If it does not, the game day would measure your luck,
not your skills.

**Why this step (now):** a game day without working detection always "fails" at the first criterion,
and you learn nothing about troubleshooting. Testing the alert path first is also what real SRE teams
do after every monitoring change.

**Next step:** notification received → Step 20. Not received → fix the Alertmanager route or receiver
(see [Observability](32-learn-performance-observability.md), Alertmanager), then repeat this step. A rule
shows `err` → fix the expression first.

### Step 20 — Prepare the chaos script and the sealed answer

**Goal:** a script that breaks exactly one thing, chosen at random, and records the answer and the
undo where the responder cannot see it.

> ⚠️ This script deliberately breaks services, fills a disk, adds firewall rules and saturates CPU.
> Run it **only on lab VMs**, after taking a **snapshot**, never on a host that serves anything real.
> It refuses to run unless `/etc/gameday-allowed` exists and the hostname matches the lab pattern.
> Rehearse every scenario once with a fixed number (`sudo ./gameday-chaos.sh 3`) and its undo before
> the real game day.

```bash
#!/usr/bin/env bash
# gameday-chaos.sh — break ONE thing at random on a LAB host.
# Prints "scenario + undo" to stdout: the game master redirects it to a file the responder cannot read:
#   ssh dokploy 'sudo bash -s' < gameday-chaos.sh > ~/gameday/answer-$(date -u +%F).txt
set -euo pipefail

# ---- guard rails ------------------------------------------------------------
[[ -f /etc/gameday-allowed ]] || { echo "refusing: /etc/gameday-allowed missing" >&2; exit 1; }
[[ "$(hostname)" =~ ^(dokploy|target[0-9]+)$ ]] || { echo "refusing: $(hostname) is not a lab host" >&2; exit 1; }
[[ $EUID -eq 0 ]] || { echo "run as root" >&2; exit 1; }

# ---- lab-specific names (edit once) -----------------------------------------
APP_UNIT=shop-worker.service                       # lab systemd unit, alert: SystemdUnitFailed
SWARM_SERVICE=shop-web-x1y2z3                      # lab Dokploy app, alert: BlackboxProbeFailed
ROUTE_FILE=/etc/dokploy/traefik/dynamic/shop.yml   # lab Traefik file route from section 3
MONITOR_IP=192.168.56.10                           # Prometheus/blackbox host

choice=${1:-$(( RANDOM % 6 + 1 ))}
ts=$(date -u +%FT%TZ)

case "$choice" in
  1) what="unit $APP_UNIT fails: drop-in points ExecStart at a missing config"
     mkdir -p "/etc/systemd/system/$APP_UNIT.d"
     printf '[Service]\nExecStart=\nExecStart=/usr/local/bin/shop-worker --config /etc/shop/missing.yml\n' \
       > "/etc/systemd/system/$APP_UNIT.d/99-gameday.conf"
     systemctl daemon-reload; systemctl restart "$APP_UNIT" || true
     undo="rm /etc/systemd/system/$APP_UNIT.d/99-gameday.conf; systemctl daemon-reload; systemctl restart $APP_UNIT" ;;
  2) what="/var filled to about 90% by /var/tmp/.gameday-fill"
     size_kb=$(df --output=size -k /var | tail -1); avail_kb=$(df --output=avail -k /var | tail -1)
     fill_kb=$(( avail_kb - size_kb / 10 ))
     (( fill_kb > 0 )) || { echo "disk already above 90%, rerun with another scenario" >&2; exit 1; }
     fallocate -l "${fill_kb}K" /var/tmp/.gameday-fill
     undo="rm -f /var/tmp/.gameday-fill" ;;
  3) what="Traefik route for shop points at port 8001 instead of 8000 (502)"
     cp -a "$ROUTE_FILE" "/root/.gameday-route.bak"
     sed -i 's/:8000"/:8001"/' "$ROUTE_FILE"
     undo="cp -a /root/.gameday-route.bak $ROUTE_FILE" ;;
  4) # assumes Traefik publishes 443 through Docker; with host networking use the INPUT chain instead
     what="DOCKER-USER drops HTTPS from the monitoring host $MONITOR_IP (UFW would not: Docker-published ports bypass it)"
     iptables -I DOCKER-USER -s "$MONITOR_IP" -p tcp -m conntrack --ctorigdstport 443 -j DROP
     undo="iptables -D DOCKER-USER -s $MONITOR_IP -p tcp -m conntrack --ctorigdstport 443 -j DROP" ;;
  5) replicas=$(docker service inspect "$SWARM_SERVICE" --format '{{.Spec.Mode.Replicated.Replicas}}')
     what="Swarm service $SWARM_SERVICE scaled from $replicas to 0"
     docker service scale "$SWARM_SERVICE=0" >/dev/null
     undo="docker service scale $SWARM_SERVICE=$replicas" ;;
  6) what="CPU saturated for 30 min by transient unit gameday-stress"
     systemd-run --unit=gameday-stress --collect stress-ng --cpu 0 --cpu-load 95 --timeout 30m >/dev/null
     undo="systemctl stop gameday-stress" ;;
  *) echo "unknown scenario $choice" >&2; exit 1 ;;
esac

echo "$ts $(hostname) scenario=$choice :: $what"
echo "UNDO: $undo"
```

```
2026-10-03T14:37:52Z dokploy scenario=4 :: DOCKER-USER drops HTTPS from the monitoring host 192.168.56.10 (UFW would not: Docker-published ports bypass it)
UNDO: iptables -D DOCKER-USER -s 192.168.56.10 -p tcp -m conntrack --ctorigdstport 443 -j DROP
```

**What it means:** the answer file holds the scenario, the time and the exact undo. The responder never
sees it during the exercise. Each scenario maps to an alert from Step 19: 1 → `SystemdUnitFailed`,
2 → `HostDiskSpaceAbove85`, 3 and 5 → `BlackboxProbeFailed` (502 / 503), 4 → `BlackboxProbeFailed`
(timeout) while users on other networks are fine, 6 → `HostHighLoad`. Scenario 4 is the nastiest:
from your laptop the site works, which tests whether you trust the alert and reason about **where** the
probe runs.

**Why this step (now):** the guard rails and the recorded undo make the exercise safe to run at a
random time. Mapping each scenario to an alert beforehand proves the test is fair: every breakage is
detectable.

**Next step:** snapshot taken and each scenario rehearsed → Step 21. A scenario has no matching alert
→ either add the alert (good) or remove the scenario.

### Step 21 — Run it at a random time

**Goal:** start the exercise without warning the responder, and start the clock.

```bash
# game master, from ctrl, at a time the responder does not know (cron, at, or by hand)
mkdir -p ~/gameday && ssh dokploy 'sudo bash -s' < gameday-chaos.sh > ~/gameday/answer-$(date -u +%F).txt
chmod 600 ~/gameday/answer-*.txt && date -u '+chaos started %F %T UTC' | tee -a ~/gameday/clock.txt
```

```
chaos started 2026-10-03 14:37:52 UTC
```

**What it means:** the breakage is live and the start time is recorded independently of the
responder's notes. If you are both game master and responder, run it from a `systemd-run
--on-active=$((RANDOM % 7200))s` timer so even you do not know when it fires, and do not open the
answer file until Step 25.

**Why this step (now):** surprise is the point: real incidents do not wait until you have your
terminal open. The independent clock is what makes the detection and restore times honest.

**Next step:** the responder carries on with normal work until an alert arrives → Step 22. If no alert
arrives within 30 minutes of the start time, the game master stops the exercise: detection failed, and
the postmortem is about monitoring (go to Step 24 with that as the incident).

### Step 22 — Triage with the incident process

**Goal:** handle the alert exactly as a real incident (section 7): confirm, declare, timeline, what
changed.

```bash
script -a ~/incidents/GAMEDAY-$(date -u +%Y%m%d-%H%M).log
date -u '+%H:%MZ alert received'
amtool alert query --alertmanager.url=http://192.168.56.10:9093
# the same request from two vantage points: your laptop, and the probe host (ctrl runs Prometheus/blackbox)
curl -s -o /dev/null -m 10 -w 'laptop: %{http_code} %{time_total}s\n' https://shop-staging.example.com/healthz
ssh ctrl "curl -s -o /dev/null -m 10 -w 'probe host: %{http_code} %{time_total}s\n' https://shop-staging.example.com/healthz"
```

```
14:41Z alert received
Alertname            Starts At                Summary                                     State
BlackboxProbeFailed  2026-10-03 14:39:22 UTC  probe https://shop-staging.example.com failed  active
laptop: 200 0.131s
probe host: 000 10.001s
```

**What it means:** from your laptop the site works; from the monitoring host the request gets no TCP
answer at all (`000` after the full 10-second timeout). The disagreement itself is the clue: the
failure depends on **where the request comes from**. That points at the network path from the
monitoring host (firewall, route, DNS on that host), not at the app, and it means "it works for me"
is not evidence that the alert is false.

**Why this step (now):** the process keeps you from jumping to the app logs. Confirming from the same
vantage point as the alert, and noting when results differ by source, is "quit thinking and look" in
practice.

**Next step:** symptoms consistent from everywhere → walk the layers with the
[site down playbook](25-playbook-site-down.md) or the [containers playbook](26-playbook-containers-k8s.md).
Symptoms differ by source → compare the paths (`curl` from both places, `tcpdump` on web01 for the
monitoring host's packets, `iptables -L DOCKER-USER -n -v` counters) → Step 23 once the cause is proven.

### Step 23 — Mitigate, fix, verify, stop the clock

**Goal:** restore service with evidence, then confirm the alert clears.

```bash
# on the lab Dokploy host: prove the cause before changing anything
sudo iptables -L DOCKER-USER -n -v --line-numbers | head -5
sudo tcpdump -ni any -c 5 'host 192.168.56.10 and tcp port 443'
# fix: remove exactly the offending rule (by its spec, not by guessing a line number)
sudo iptables -D DOCKER-USER -s 192.168.56.10 -p tcp -m conntrack --ctorigdstport 443 -j DROP
curl -s -o /dev/null -w '%{http_code}\n' https://shop-staging.example.com/healthz     # from ctrl
date -u '+%H:%MZ restored'
```

```
Chain DOCKER-USER (1 references)
num   pkts bytes target     prot opt in     out     source               destination
1       38  2280 DROP       6    --  *      *       192.168.56.10        0.0.0.0/0            ctorigdstport 443
2     9123  731K RETURN     0    --  *      *       0.0.0.0/0            0.0.0.0/0
14:52:07.112233 ens18 In  IP 192.168.56.10.51322 > 192.168.56.30.443: Flags [S], seq 1234567890, win 64240, length 0
14:52:08.140011 ens18 In  IP 192.168.56.10.51322 > 192.168.56.30.443: Flags [S], seq 1234567890, win 64240, length 0
200
14:53Z restored
```

**What it means:** rule 1 has dropped 38 packets from the monitoring host, and `tcpdump` shows SYNs
arriving with no reply: proven before touching anything. After deleting that rule the probe target
answers 200. Wait for the alert to resolve in Alertmanager (one or two evaluation intervals) before
stopping the clock: 14:41 alert to 14:53 restored is a 12-minute time to restore.

**Why this step (now):** fixing only after evidence is the pass criterion "root cause named with
evidence". Deleting the rule by its full specification avoids removing the wrong rule, which a bare
line number can do if the chain changed.

**Next step:** alert resolved → Step 24. Alert still firing → something else is broken too (or your fix
did not apply); back to Step 22 with the new evidence. If you cannot find the cause within 60 minutes,
the game master reveals it: you fail the time criterion, and the postmortem becomes about what
made it hard to find.

### Step 24 — Write and publish the postmortem

**Goal:** a one-page, blameless postmortem within 24 hours, sanitized and in your portfolio.

```bash
cp ~/ops-portfolio/templates/postmortem.md ~/ops-portfolio/L4-sre/game-day-$(date -u +%F).md
grep -E '^[0-9]{2}:[0-9]{2}Z' ~/incidents/GAMEDAY-*.log | head -20      # timeline candidates from the script log
gitleaks git --redact ~/ops-portfolio && git -C ~/ops-portfolio add -A && git -C ~/ops-portfolio commit -m "Game day 2026-10-03 postmortem"
```

```
14:41Z alert received
14:53Z restored
INF no leaks found
[main 3c4d5e6] Game day 2026-10-03 postmortem
 1 file changed, 64 insertions(+)
```

**What it means:** the postmortem is committed with a timeline built from your recorded session, after
a secret scan. Use the template from section 7: summary, impact (which probe, how long), timeline,
root cause (the DOCKER-USER rule) with the evidence (counters, tcpdump), contributing factors (UFW
status would have looked clean: Docker-published ports bypass UFW), what went well, what went wrong,
and action items with owners.

**Why this step (now):** the ops ladder's exit test is not complete until the write-up is published.
Writing within 24 hours keeps the details accurate, and the public version is the proof of skill.

**Next step:** → Step 25 with the game master. Follow-up ideas for this scenario: an alert on
DOCKER-USER rule changes (or config management that owns that chain), a runbook line "probe fails but
site works from my laptop → check firewall rules for the probe's source address".

### Step 25 — Score it and plan the next one

**Goal:** compare what happened with the sealed answer and decide the next exercise.

```bash
cat ~/gameday/answer-2026-10-03.txt ~/gameday/clock.txt
```

```
2026-10-03T14:37:52Z dokploy scenario=4 :: DOCKER-USER drops HTTPS from the monitoring host 192.168.56.10 (UFW would not: Docker-published ports bypass it)
UNDO: iptables -D DOCKER-USER -s 192.168.56.10 -p tcp -m conntrack --ctorigdstport 443 -j DROP
chaos started 2026-10-03 14:37:52 UTC
```

| Criterion | Result | Pass |
|---|---|---|
| Detected by alert | `BlackboxProbeFailed` at 14:39:22, 1.5 min after start | yes |
| Restored within 60 min of alert | 14:41 → 14:53 = 12 min | yes |
| Root cause with evidence | DOCKER-USER rule, counters + tcpdump | yes |
| Postmortem within 24 h | committed 2026-10-03 | yes |
| Follow-ups owned | 2 issues created | yes |

**What it means:** this run passes the L4 exit test. Time to detect was 1.5 minutes (probe interval and
`for:` duration), time to acknowledge 2 minutes, time to restore 12 minutes. The slowest part was
deciding whether to trust the alert when the laptop showed 200; that goes into the runbook.

**Why this step (now):** scoring against the sealed answer keeps the exercise honest, and the
numbers (detect, acknowledge, restore) are the baseline the next game day must beat.

**Next step:** run the game day again monthly with a different scenario, add scenarios from your real
incidents, and let a colleague be the responder while you are game master: designing fair failures is
itself a senior skill. When you pass three in a row, move on to [Senior architecture](39-learn-senior-architecture.md).

### Game day decision tree, verify and prevent

**Level:** [L4 · Lead/SRE]

```
 alert fired?
 ├─ no (30 min after start) ──► detection failed: postmortem on monitoring (rules, routes, receivers)
 └─ yes ──► reproduce from the alert's vantage point
             ├─ same result everywhere ──► layer walk: DNS → route → firewall → TLS → proxy → app
             └─ differs by source ──► path from the probe: firewall (DOCKER-USER!), route, DNS on the probe host
                 └─ evidence (log line, counter, capture) ──► one change ──► alert resolves ──► stop clock
                     └─ postmortem within 24 h ──► score against the sealed answer ──► next scenario
```

**Fix & verify:** every fix is checked from the alert's vantage point and by the alert resolving, not
only by your own `curl`.

**Rollback:** if a fix makes things worse, or when the exercise ends without a fix, the game master
runs the `UNDO` line from the answer file; if anything is still odd, revert the VM to the snapshot
taken in Step 20.

**Prevent it next time:** each game day ends with at least one improvement to monitoring, a runbook
or automation. Over a few months that loop builds exactly the operational maturity the L4 level
describes.

---

## 9. Self-check and exit tests

> 📚 **Study path:** 1) Note: answer the questions below without looking, then check the answer key · 2) KodeKloud: the free *Terraform Challenges* ([course](https://kodekloud.com/courses/terraform-challenges)) and the daily task of *100 Days of DevOps* ([program](https://kodekloud.com/100-days-of-devops)) for Git, CI/CD and Terraform reps · 3) Re-read the topic behind every question you missed · 4) Practice: the timed task for your career stage, with a timer and no notes.

Use this section twice: once after your first pass through the module (expect gaps), and again
before you claim the level. The questions test understanding; the timed tasks test whether the skill
survives pressure. The ops ladder rule applies: pass the exit test inside its time limit, then move
up.

### Questions by area

**Git** [L0 · Fresher] / [L1 · Junior]

1. What exactly is a branch in Git, and why does deleting one not delete its commits?
2. You pushed a bad commit to `main` an hour ago. Which command undoes it, and why not `git reset --hard`?
3. You ran `git reset --hard HEAD~3` by mistake. How do you get the three commits back?
4. Which data does `git reset --hard` destroy that no Git command can recover?
5. During a rebase, what do "ours" and "theirs" mean, and how does that differ from a merge?
6. A `.env` file with a password was pushed last week. List the steps in the right order.

**GitLab CI/CD** [L2 · Mid] / [L3 · Senior]

7. A job is "pending" with "stuck" in the UI. Name three causes and the first command for each.
8. Why is a job that uses `if: $CI_COMMIT_BRANCH == "main"` missing from merge request pipelines?
9. What is the difference between artifacts and cache, and which one may a job depend on?
10. Why does a DinD build fail to resolve names when the runner host resolves fine?
11. Why tag images with `$CI_COMMIT_SHORT_SHA`, and what does a release pipeline do with that image?
12. Your Harbor robot login fails only in CI with `unauthorized`. Name the GitLab variable setting to check.
13. The deploy job is green but users see the old version. What check should the pipeline have had?

**Deployment strategies** [L3 · Senior]

14. When is `recreate` the right strategy despite its downtime?
15. What makes a rolling update roll out a broken release to every instance?
16. Blue/green rollback "did not work". What is the most likely cause?
17. Describe expand/contract for renaming a database column.

**Ansible** [L3 · Senior]

18. What does `changed=0` on a second run prove, and what usually breaks it?
19. A handler did not run although the template changed. Why, and how do you recover?
20. Two places set `docker_log_max_size`. How do you find which value a host gets?
21. Why put `validate:` on the daemon.json template task?

**Terraform** [L3 · Senior]

22. What is in the state file, and why must it never be in Git?
23. A plan shows `-/+` for a VM you only renamed in code. What happened and what fixes it?
24. `Error acquiring the state lock`: what do you check before `force-unlock`?
25. What is the difference between drift and an unmanaged resource, and which command handles each?

**Secrets** [L3 · Senior]

26. In what order do you handle a leaked secret, and why does rotation come before history clean-up?
27. Why are files preferred to environment variables for runtime secrets?
28. What does a 60-second Vault token from GitLab's ID token give you that a masked variable does not?

**SRE practice** [L4 · Lead/SRE]

29. In an incident, why mitigate before root-causing, and what are your mitigation options?
30. Name the four incident roles and the one you must never skip in a two-person team.
31. What makes a postmortem blameless, and what is wrong with "root cause: human error"?
32. What are the four mandatory parts of a GitLab-style change request?
33. Your SLO is 99.5% over 30 days. How much full-outage time is that, and what happens when it is spent?
34. Give one example each of a page, a ticket and an alert you should delete.

### Answer key

| # | Short answer |
|---|---|
| 1 | a file holding one commit SHA; commits stay in the object database until GC removes unreachable ones (reflog keeps them reachable for weeks) |
| 2 | `git revert SHA`: adds an inverse commit, keeps shared history consistent; `reset` rewrites history others already have |
| 3 | `git reflog`, then `git branch rescue HEAD@{1}`, inspect, then `git reset --hard rescue` |
| 4 | uncommitted changes in the working tree (and index); they were never stored as commits |
| 5 | in a rebase "ours" is the branch being rebased onto, "theirs" is your commit being replayed: swapped compared to a merge |
| 6 | rotate the password → update consumers → check for abuse → remove from `main` and erase logs → optionally rewrite history → add gitleaks |
| 7 | runner offline (`gitlab-runner verify`), tag mismatch (job `tag_list` vs runner tags), protected runner on unprotected ref; also `concurrent` limit |
| 8 | `CI_COMMIT_BRANCH` is not set in MR pipelines; use `CI_MERGE_REQUEST_SOURCE_BRANCH_NAME` or a source-based rule |
| 9 | artifacts are guaranteed within the pipeline and stored on GitLab; cache is best-effort speed-up; only artifacts may be depended on |
| 10 | DinD runs its own dockerd with its own resolver config and may fall back to 8.8.8.8; give it `--dns` |
| 11 | maps every image to a commit and pipeline; the release pipeline retags the same tested image (promotion), never rebuilds |
| 12 | "Expand variable reference" must be off, because the `$` in `robot$shop+gitlab-ci` gets expanded |
| 13 | a `/version` check that compares the running SHA with `$CI_COMMIT_SHORT_SHA` |
| 14 | when two versions cannot run at the same time (single-writer worker, incompatible schema change in a maintenance window) |
| 15 | no real health check or readiness probe, so "started" counts as "healthy" |
| 16 | the new version changed shared state (schema, data, sessions) that the old version cannot use |
| 17 | add the new column; write both; backfill; read the new one; stop writing the old; drop it in a later release |
| 18 | idempotency; usually `command`/`shell` without `changed_when`, or a template with changing content |
| 19 | the play failed after the notify; re-run with `--force-handlers` or flush handlers right after the task |
| 20 | `ansible HOST -m ansible.builtin.debug -a var=docker_log_max_size` and `ansible-inventory --host HOST` |
| 21 | the rendered file is checked by `dockerd --validate` before it replaces the working one |
| 22 | resource-to-real-ID mapping plus all attributes in plain text, including secrets; it must be shared and locked |
| 23 | the address changed, so Terraform sees "delete old, create new"; add a `moved` block |
| 24 | whether the lock holder (`Who`, `Created`) is still running: pipeline and runner job status |
| 25 | drift: managed object changed outside Terraform (`plan -refresh-only`); unmanaged: exists but not in state (`import` block) |
| 26 | scope → rotate → update consumers → check abuse → clean up and prevent; rotation makes the leaked value useless, clean-up does not |
| 27 | env vars leak through `docker inspect`, `/proc/PID/environ`, crash reports and debug pages |
| 28 | short lifetime, per-job identity tied to project and ref, and an audit trail of every read |
| 29 | users suffer while you investigate; roll back, switch traffic, flag off, scale, fail over, block, maintenance page |
| 30 | IC, ops lead, comms lead, scribe; never skip communications |
| 31 | it analyses system causes assuming good intent; "human error" stops the analysis and produces no useful action items |
| 32 | criticality, steps (with durations), verification, rollback (with trigger) |
| 33 | about 3 h 36 min per 30 days; spent budget means reliability work takes priority over risky changes |
| 34 | page: site down or burning error budget fast; ticket: disk full in 3 days; delete: CPU above 80% with no user impact |

### Timed exit tests per career stage

Run them on lab VMs and lab projects only, with a timer and without this module open. Record the
time and the five-line note for each.

| Stage | Time | Task | Passes when |
|---|---|---|---|
| [L0 · Fresher] | 30 min | In a shared lab repo: revert a bad commit in the middle of `main` and push; recover three commits lost to `reset --hard`; resolve a `compose.yml` conflict and prove it with `docker compose config` | all three done, `git log --graph` shows clean history, no force-push |
| [L1 · Junior] | 30 min | Fix a pipeline that fails twice: first a YAML indentation error, then a job stuck on a tag mismatch; then run an existing playbook with `--check --diff --limit target1` and explain every `changed` | green pipeline, a written explanation of each change |
| [L2 · Mid] | 45 min | A game master breaks one of: DinD push to Harbor (x509), a non-idempotent task, a stale Terraform lock, a protected variable on a feature branch. Diagnose with evidence and fix | root cause named with the log line or command output that proves it |
| [L3 · Senior] | one weekend | Ops ladder L3 exit test: move one Apache workload into a container behind Dokploy, built by a GitLab CI pipeline that pushes to Harbor with the commit SHA, with a written rollback you have actually tested; plus the Docker Ansible role run on a VM created by Terraform | pipeline green on `main` and on a tag, rollback timed, role idempotent, code in Git |
| [L4 · Lead/SRE] | game day + 24 h | Section 8 game day; plus the "retire system Apache" CR reviewed by a colleague; plus one SLO with a burn-rate alert | all section 8 criteria, CR approved, postmortem published |

---

## 10. Where to go next

> 📚 **Study path:** 1) KodeKloud: keep CKA first until you pass it (*Certified Kubernetes Administrator (CKA)* — [course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)); the courses of this module run on the morning rep · 2) Note: [Roadmap](34-roadmap.md) to see where this module sits · 3) Video: none needed · 4) Practice: the next module's drills, chosen from the table below.

| If you want to... | Go to | Why now |
|---|---|---|
| Measure and alert on what your pipelines deploy | [Observability](32-learn-performance-observability.md) | SLOs, burn-rate alerts and the monitoring the game day depends on |
| Apply the pipeline to your real migration | [Apache holds 443 case study](21-case-apache-443-dokploy.md) and [Deployment patterns](35-deployment-patterns.md) | finish the 81/444 move with Traefik routing, then retire Apache with the CR from section 7 |
| Go deeper on the deploy targets | [Docker learn module](30-learn-docker.md) and [Kubernetes learn module](31-learn-kubernetes.md) | Harbor, daemon.json, Swarm, rollouts, RBAC for deployers |
| Debug what the pipeline deployed | [Containers and Kubernetes playbook](26-playbook-containers-k8s.md) and [Site down playbook](25-playbook-site-down.md) | 502s, ImagePullBackOff, x509, routing |
| Harden the supply chain and secrets | [Security & DevSecOps](37-learn-security-devsecops.md) | image scanning, signing, least privilege, secrets in depth |
| Run Terraform against AWS | [Cloud & AWS](36-learn-cloud-aws.md) and the [AWS reference](16-aws-cloud.md) | IAM for CI, VPCs and security groups as code |
| Handle database migrations safely | [Databases for ops](38-learn-databases-ops.md) | backups, restores and expand/contract in practice |
| Design systems, not just pipelines | [Senior architecture](39-learn-senior-architecture.md) | availability, trade-offs, design reviews |
| Turn this into a career step | [Career ladder](40-career-ladder.md) | what each stage is expected to show, and how your portfolio proves it |

The short version: if you are a **fresher or junior**, finish section 1 and its exit test, then go
to the [Linux](27-learn-linux.md) and [Networking](28-learn-networking.md) learn modules. If you are
**mid-level**, take section 2's debugging steps and section 4's Ansible into your daily work, and do
the L2 exit test. If you are aiming for **senior**, the L3 exit test is your next weekend. And at
**lead/SRE** level, schedule the first game day and write the Apache CR this month.
