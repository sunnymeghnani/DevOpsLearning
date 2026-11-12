# 47 — CI/CD Toolbox & Problems: GitLab CI, Jenkins, GitHub Actions, ArgoCD

This module is the CI/CD toolbox and problem library. Part one explains GitLab CI, your main tool, and compares it with Jenkins, GitHub Actions and Argo CD/Flux: how each one works, how to install it safely in a lab, and how to run it day to day. Part two is a library of 40 problems that DevOps engineers hit most often. They were collected from the GitLab, Jenkins and Sonar forums, from GitHub issues of `actions/runner` and `argo-cd`, from GitLab Runner work items and from the official troubleshooting docs. Every command is documented here for you to run on your own lab or servers. None of them were executed while writing this module.

> All sample outputs are illustrative: Ubuntu 22.04/24.04, GitLab 18/19 with GitLab Runner 18, Docker Engine 28, Harbor 2.x with a private CA, Dokploy on Docker Swarm with Traefik v3, Jenkins LTS on Java 21, Argo CD 2.x/3.x, Flux v2. IPs come from documentation ranges (192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24) or a private lab range (10.20.0.0/24). UPPERCASE words are placeholders: PROJECT_ID, RUNNER_ID, TOKEN, APP, SHA, VERSION, HOST.

---

## 0. How to use this module

> 📚 **Study path:** 1) KodeKloud: *GIT for Beginners* ([course](https://kodekloud.com/courses/git-for-beginners)) → 2) KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, sections Architecture & Core Concepts → Continuous Integration with GitLab → Self-Managed Runners ([course](https://kodekloud.com/courses/gitlab-ci-cd)) → 3) handbook: [GitLab CI/CD in module 33](33-learn-cicd-iac-sre.md), then sections 1–3 here → 4) docs: [GitLab docs](https://docs.gitlab.com/) and [Use Docker to build Docker images](https://docs.gitlab.com/ci/docker/using_docker_build/) → 5) lab: break and fix the problems in sections 5–9 on a test runner VM. Add *Certified Jenkins Engineer*, *GitHub Actions Certification* and the Argo CD docs only when your job needs them.

### Who this module is for

Each career stage uses a different part of this module. The tags on every problem combine the Ops Ladder level with the career stage, for example [L2 · Mid].

| Stage (level) | Read first | You should be able to |
|---|---|---|
| Fresher (L0) | Section 1, entries 5.1, 5.4, 9.3 | read a job log bottom-up and say whether the problem is the runner, a variable, or the script |
| Junior (L1) | Sections 1–2, all of section 5, 7.3, 8.1, 10.1, 10.6 | register a runner, fix stuck jobs and empty variables, clean a full runner disk |
| Mid-level (L2) | Sections 3, 6, 7, 8, 10 | build and push images through a private CA, fix DinD, caches, artifacts and Jenkins plugin and proxy breakage |
| Senior (L3) | Sections 6.4, 9, 12, 13 and section 4 | split runners by trust level, design deploys that cannot race, run Argo CD and keep pipelines secret-safe |
| Senior/Lead (L4) | 9.4, 12.5, 13.4, the self-check | own the release process: promotion, rollback, supply-chain and secret policy across teams |

### How the entries are laid out

Every problem in sections 5–13 uses the same layout, so you can skim it under pressure:

- **Seen as** is the exact error text or symptom, followed by where it happens, the level, and how often the community hits it.
- **Why it happens** gives the cause in plain words first, then the precise mechanism.
- **Diagnose** lists the read-only commands, a realistic sample output, and **What the output tells you** explains how to read it.
- **Fix** gives the commands or configuration, and **Why this fix works** explains the mechanism, the trade-offs, and what you must *not* do.
- **Prevent it**, **Next step** and **Community threads** link to the KodeKloud course, the docs, the forum threads and issues the entry came from, plus Stack Overflow and Reddit search links you can open yourself.

### How to practise

1. Build a lab: one GitLab instance (GitLab.com free tier or a small Omnibus VM), one runner VM (`ci-01`), a Harbor VM with a certificate from your own lab CA, and a Dokploy VM. Keep it isolated from production credentials.
2. Pick an entry, reproduce the failure on purpose (each entry says what breaks it), and write down the first error line you see.
3. Diagnose it using only the entry's commands, apply the fix, and then write the "Prevent it" control into your runner or pipeline template.
4. Time yourself. The self-check at the end lists ten timed break-and-fix drills by stage.

---

## 1. GitLab CI in 10 minutes

GitLab CI/CD is built into GitLab. You commit a `.gitlab-ci.yml` file to the repository, and on each push or merge request GitLab turns it into a **pipeline**: **stages** made of **jobs**. GitLab never runs your jobs itself. A separate program, **GitLab Runner**, polls GitLab for work, runs the job with an **executor** (shell, Docker, Kubernetes and others), streams the log back and uploads artifacts and caches. Everything the job needs comes from **CI/CD variables** (some predefined, some yours, some protected or masked), the **cache** (speed only) and **artifacts** (files passed to later jobs).

### Architecture on your on-prem stack

```text
 developer ── git push / merge request ──▶ GitLab  gitlab.example.com (10.20.0.10)
                                            Puma/Rails · Sidekiq · Gitaly · PostgreSQL · Redis
                                            creates the pipeline; jobs wait as "pending"
                                                       ▲
                       HTTPS 443, OUTBOUND from runner │ POST /api/v4/jobs/request (long poll)
                                                       │
  ci-01 (10.20.0.21)  gitlab-runner service ── /etc/gitlab-runner/config.toml
        │  docker executor: one set of containers per job
        ├── build container  (your image + script)
        ├── helper container (git clone, cache, artifacts upload)
        └── service docker:28-dind (privileged; builds the image)
                    │ docker push over HTTPS, trusts the private CA
                    ▼
  Harbor  harbor.example.com (10.20.0.30)  project "shop", robot account for CI
                    │
        ┌───────────┴──────────────────────────────┐
        ▼ push model                               ▼ pull model (GitOps)
  deploy job → Dokploy API (x-api-key)       job commits the new tag to a deploy repo
  Dokploy 10.20.0.40: Swarm service pulls    Argo CD in Kubernetes sees the commit,
  the SHA tag, Traefik routes the domain     pulls from Harbor and syncs the Deployment
```

Three facts in this diagram explain most of the problem library:

1. **The runner only makes outbound connections.** It needs to reach GitLab on 443. GitLab never connects to the runner, so a "stuck" job is almost always about runner matching (tags, protection, project), not about network access to the runner. See 5.1.
2. **Each job runs in fresh containers.** Nothing survives between jobs except the cache, the artifacts and whatever you push to a registry. A tool, a CA certificate or a `known_hosts` entry that exists on `ci-01` does not exist inside the job container. That explains 6.3, 7.2 and 9.3.
3. **Every client keeps its own trust store.** The runner host, the build container, the DinD daemon, BuildKit, the Dokploy nodes and Argo CD each need the private CA separately. See 7.1, 7.2, 9.1 and 12.3.

### Executors at a glance

| Executor | Isolation | Image builds | Use it for |
|---|---|---|---|
| shell | none: jobs run as `gitlab-runner` on the host | host Docker (the user must be in the `docker` group, which equals root) | legacy builds, quick labs |
| docker | a container per job | DinD (privileged) or Buildah, or socket binding (root on host) | the default on-prem choice: what you run on `ci-01` |
| docker-autoscaler | autoscaled VMs (fleeting plugins); a fresh VM per job with `max_use_count = 1` | DinD without sharing a host | shared or untrusted workloads at scale; replaces the deprecated docker+machine |
| kubernetes | a pod per job | Buildah or rootless BuildKit (avoid privileged pods) | when the platform is already Kubernetes |
| instance, custom, ssh | varies | varies | special cases |

### GitLab CI compared with the other tools

| | GitLab CI | Jenkins | GitHub Actions | Argo CD / Flux | Woodpecker / Drone |
|---|---|---|---|---|---|
| Model | push CI/CD inside GitLab | push CI/CD server | push CI/CD inside GitHub | **pull** CD: a controller in the cluster syncs from Git | push CI, container per step |
| Config | `.gitlab-ci.yml` | `Jenkinsfile` + controller config (JCasC) | `.github/workflows/*.yml` | `Application` / `Kustomization` / `HelmRelease` objects | `.woodpecker.yml` |
| Executes on | GitLab Runner | controller + agents | hosted or self-hosted runners | in-cluster controllers | agents |
| State lives in | GitLab DB | `JENKINS_HOME` on disk | GitHub | Git + cluster | server DB |
| Strength | one product: repo, CI, registry, environments | unlimited flexibility, huge plugin ecosystem | marketplace, easy for GitHub repos | drift detection, audit trail, easy rollback by revert | small, simple, self-hosted |
| Typical pain | runner matching, DinD, variables | plugin upgrades, controller sprawl, Groovy | self-hosted runner security | OutOfSync noise, hooks, secrets | fewer features |
| Docs | [docs.gitlab.com](https://docs.gitlab.com/) | [jenkins.io/doc](https://www.jenkins.io/doc/) | [GitHub Actions docs](https://docs.github.com/en/actions) | [Argo CD](https://argo-cd.readthedocs.io/en/stable/) · [Flux](https://fluxcd.io/flux/) | [woodpecker-ci.org](https://woodpecker-ci.org/) |

**How it fits your work.** On-prem you will mostly run GitLab CI with your own runners, push to Harbor and deploy to Dokploy (push model). As you move to Kubernetes, the deploy step usually changes to GitOps: CI only builds and pushes, then commits the new tag to a deploy repository, and Argo CD or Flux applies it. Jenkins shows up in older enterprises and GitHub Actions in teams that host code on GitHub. The troubleshooting skills carry across, because every tool has the same moving parts: a scheduler, workers, credentials, a registry and a deploy target. Supporting tools such as SonarQube (quality gates), Nexus or Harbor (artifact and image repositories) plug into all of them.

---

## 2. Install and first configuration

This section builds the lab from the diagram: a Docker-executor runner on `ci-01` that builds images, pushes them to Harbor through your private CA, and deploys to Dokploy. Short quick starts for Jenkins, a GitHub Actions runner and Argo CD follow. Use a test VM. A runner configured this way has root-equivalent power on its host (see 6.4).

### Runner host prerequisites

- **A dedicated VM**, Ubuntu 24.04 with 4 vCPU, 8 GB RAM and a separate 100 GB disk for `/var/lib/docker`. Do not put the runner on the Dokploy or Harbor host: cleanup jobs on a runner (8.1) must never be able to delete production containers or volumes.
- **Outbound HTTPS** to GitLab and Harbor, plus your package mirrors. No inbound ports are needed.
- **Internal DNS** configured, so you know which resolvers the jobs must use (6.3), and the **path MTU** of the network (6.2).
- **The private CA certificate** (`corp-ca.crt`, PEM format) for GitLab and Harbor.

### Install GitLab Runner on Ubuntu

```bash
# Docker Engine first (official Docker apt repository), then the runner from GitLab's repository.
curl -fsSL "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" -o /tmp/runner-repo.sh
less /tmp/runner-repo.sh                      # read a script before you run it as root
sudo bash /tmp/runner-repo.sh
apt-cache madison gitlab-runner | head -3     # pick the version that matches your GitLab major.minor
sudo apt-get install -y gitlab-runner=18.10.1-1 gitlab-runner-helper-images=18.10.1-1   # since 17.7.1 both must match
sudo apt-mark hold gitlab-runner gitlab-runner-helper-images   # upgrade on purpose, not with unattended-upgrades

# Trust the private CA on the host (runner process + host Docker)
sudo cp corp-ca.crt /usr/local/share/ca-certificates/corp-ca.crt && sudo update-ca-certificates
sudo mkdir -p /etc/gitlab-runner/certs /etc/docker/certs.d/harbor.example.com
sudo cp corp-ca.crt /etc/gitlab-runner/certs/gitlab.example.com.crt
sudo cp corp-ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt
```

### Create and register the runner

Since GitLab 16 you **create** the runner in the UI first (Admin, group or project, then CI/CD, Runners, New runner). You set its tags, "Run untagged jobs" and "Protected" there, and copy the `glrt-` authentication token it shows once. Since GitLab 17.0 the old registration tokens are disabled by default, and their removal is planned for GitLab 20.0 (see 5.2).

```bash
sudo gitlab-runner register --non-interactive \
  --url "https://gitlab.example.com" \
  --token "$RUNNER_TOKEN" \
  --executor "docker" \
  --docker-image "alpine:3.22" \
  --name "ci-01-docker"
sudo gitlab-runner verify
```

```text
Runtime platform                                    arch=amd64 os=linux pid=2817 revision=6f1d2e3a version=18.10.1
Running in system-mode.
Verifying runner... is valid                        runner=t3_Kd9aQ
```

### config.toml for Docker builds

The `register` command writes a skeleton. Edit `/etc/gitlab-runner/config.toml` so that DinD works with TLS, jobs use your internal DNS, the dind daemon trusts Harbor, and metrics are exposed. The runner re-reads the file a few seconds after you save it. Restart the service after changing global settings such as `listen_address`.

```toml
concurrent = 4                       # jobs at once on this host, across all [[runners]]
check_interval = 0
listen_address = "127.0.0.1:9252"    # Prometheus metrics; scrape through a firewall rule or local agent

[[runners]]
  name = "ci-01-docker"
  url = "https://gitlab.example.com"
  token = "glrt-REDACTED"            # never commit this file to Git
  executor = "docker"
  limit = 4
  environment = ["FF_NETWORK_PER_BUILD=true"]
  [runners.docker]
    image = "alpine:3.22"
    privileged = true                # needed for docker:dind; only on this dedicated build runner
    dns = ["10.20.0.53", "10.20.0.54"]
    dns_search = ["example.com"]
    network_mtu = 1400               # path MTU minus overhead (6.2); used with FF_NETWORK_PER_BUILD
    pull_policy = ["if-not-present"] # single-team runner only; shared runners should keep "always"
    volumes = [
      "/certs/client",
      "/cache",
      "/etc/docker/certs.d/harbor.example.com/ca.crt:/etc/docker/certs.d/harbor.example.com/ca.crt:ro",
    ]
  [runners.cache]
    Type = "s3"                      # distributed cache, optional (8.2)
    Shared = true
    [runners.cache.s3]
      ServerAddress = "minio.example.com:9000"
      BucketName = "runner-cache"
      Insecure = false
```

The volume line mounts the CA file into every job container *and* into the `docker:dind` service container, at the path where the inner Docker daemon looks for Harbor's CA. This one line prevents the most common Harbor push failure (7.2).

### Run the runner in Docker instead

If you prefer containers, the runner itself can run in Docker. It then starts job containers through the host socket, so the security trade-off is the same as above.

```yaml
# /opt/gitlab-runner/compose.yaml
services:
  gitlab-runner:
    image: gitlab/gitlab-runner:v18.10.1      # pin; match your GitLab version
    restart: unless-stopped
    volumes:
      - ./config:/etc/gitlab-runner           # config.toml and certs/ live here
      - /var/run/docker.sock:/var/run/docker.sock
```

### First pipeline: build, push to Harbor, deploy

A minimal `.gitlab-ci.yml` for the lab. Module 33 has the complete version with tests, environments and rollback ([GitLab CI/CD in module 33](33-learn-cicd-iac-sre.md)).

```yaml
workflow:
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS
      when: never
    - if: $CI_COMMIT_BRANCH

stages: [build, deploy]

variables:
  IMAGE: harbor.example.com/shop/web

build-image:
  stage: build
  image: docker:28
  services:
    - name: docker:28-dind
      command: ["--mtu=1400"]
  tags: [docker]
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"
    DOCKER_TLS_VERIFY: "1"
    DOCKER_CERT_PATH: "$DOCKER_TLS_CERTDIR/client"
  script:
    - echo "$HARBOR_PASSWORD" | docker login -u "$HARBOR_USER" --password-stdin harbor.example.com
    - docker build --pull -t "$IMAGE:$CI_COMMIT_SHORT_SHA" .
    - docker push "$IMAGE:$CI_COMMIT_SHORT_SHA"
  rules:
    - if: $CI_COMMIT_REF_PROTECTED == "true"

deploy-staging:
  stage: deploy
  image: alpine:3.22
  tags: [docker]
  resource_group: staging
  environment: { name: staging, url: "https://shop-staging.example.com" }
  script:
    - apk add --no-cache curl
    - >
      curl -fsS -X POST "$DOKPLOY_URL/api/application.deploy"
      -H "x-api-key: $DOKPLOY_TOKEN" -H "Content-Type: application/json"
      -d "{\"applicationId\":\"$DOKPLOY_APP_ID\"}"
  rules:
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

Store `HARBOR_USER`, `HARBOR_PASSWORD` and `DOKPLOY_TOKEN` as **masked, protected** variables. Untick "Expand variable reference" on `HARBOR_USER`, because Harbor robot names contain `$` (5.5). Check the Dokploy endpoint names in your instance's Swagger page before relying on them, and add the version check from module 33 so a green job means a deployed app (9.1). The Dokploy side is covered in [module 45](45-dokploy-and-self-hosted-paas.md).

### Jenkins in Docker with JCasC

Use Jenkins when an employer already does. Build the controller from code from day one: a pinned image, a pinned plugin list, and Configuration as Code (JCasC), so the controller can be rebuilt (10.7).

```dockerfile
# Dockerfile
FROM jenkins/jenkins:lts-jdk21
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt
COPY --chown=jenkins:jenkins casc/ /var/jenkins_casc/
```

```text
# plugins.txt (pin versions once the lab works: name:VERSION)
configuration-as-code
workflow-aggregator
git
credentials-binding
ssh-slaves
matrix-auth
ws-cleanup
```

```yaml
# casc/jenkins.yaml
jenkins:
  systemMessage: "Managed by JCasC: change casc/jenkins.yaml in Git, not the UI"
  numExecutors: 0                      # the controller schedules; agents build (10.4)
  securityRealm:
    local:
      allowsSignup: false
      users:
        - id: "ops"
          password: "${JENKINS_ADMIN_PASSWORD}"
  authorizationStrategy:
    loggedInUsersCanDoAnything:
      allowAnonymousRead: false
unclassified:
  location:
    url: "https://jenkins.example.com/"
```

```yaml
# compose.yaml (put it behind Traefik; do not publish 8080, Traefik's dashboard often uses it)
services:
  jenkins:
    build: .
    restart: unless-stopped
    env_file: .env                      # JENKINS_ADMIN_PASSWORD=..., chmod 600
    environment:
      CASC_JENKINS_CONFIG: /var/jenkins_casc
      JAVA_OPTS: "-Djenkins.install.runSetupWizard=false -Xmx2g"
    volumes:
      - jenkins_home:/var/jenkins_home
volumes:
  jenkins_home:
```

### A GitHub Actions self-hosted runner

Use self-hosted runners only for **private** repositories (6.4). The download URL, checksum and one-time token come from the repository or organisation page: Settings, then Actions, Runners, New self-hosted runner.

```bash
sudo useradd -m -s /bin/bash ghrunner
sudo -iu ghrunner bash -c '
  mkdir -p actions-runner && cd actions-runner
  curl -fsSLO https://github.com/actions/runner/releases/download/vVERSION/actions-runner-linux-x64-VERSION.tar.gz
  echo "SHA256_FROM_THE_PAGE  actions-runner-linux-x64-VERSION.tar.gz" | sha256sum -c
  tar xzf actions-runner-linux-x64-VERSION.tar.gz
  ./config.sh --url https://github.com/ORG/REPO --token REG_TOKEN --name ci-02 --labels onprem,docker --unattended'
# /home/ghrunner is mode 750 on Ubuntu 22.04+ (HOME_MODE 0750), so change into it as root
sudo bash -c 'cd /home/ghrunner/actions-runner && ./svc.sh install ghrunner && ./svc.sh start'
```

Workflows then target it with `runs-on: [self-hosted, linux, onprem]`. All labels must match (11.1).

### Argo CD on a lab cluster

Argo CD runs inside Kubernetes and pulls from Git. Install it on the lab kubeadm cluster from [module 31](31-learn-kubernetes.md):

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
# if apply fails with "metadata.annotations: Too long", re-run it with: --server-side --force-conflicts
kubectl -n argocd rollout status deploy/argocd-server
argocd admin initial-password -n argocd      # then log in, change it, and delete argocd-initial-admin-secret
```

```yaml
# apps/shop-web.yaml: one Application per app and environment, stored in Git
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: shop-web
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://gitlab.example.com/platform/deploy-config.git
    targetRevision: main
    path: apps/shop-web/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: shop
  syncPolicy:
    automated: { prune: true, selfHeal: true }
    syncOptions: [CreateNamespace=true]
```

Argo CD reconciles about every three minutes by default (`timeout.reconciliation` in `argocd-cm`). It renders Helm charts with `helm template`, so `helm ls` shows nothing for Argo-managed apps. That is expected.

---

## 3. Day-2 operations

Installing a CI system takes an afternoon. Running it for years is the actual job: upgrades, capacity, security, backups, cleanup, and monitoring the CI tools themselves.

### Upgrades and version skew

- **GitLab first, runners second.** Keep each runner's major.minor version close to GitLab's. Upgrade GitLab along its documented upgrade path, which has required stops between some versions. Skipping a stop is a classic cause of failed Omnibus upgrades on the forum.
- **Runner upgrade without killing jobs:** pause the runner in the UI, wait until `journalctl -fu gitlab-runner` shows no running jobs, upgrade the package, run `sudo gitlab-runner verify`, then unpause.
- **Read deprecations before upgrading.** The changes that broke pipelines in recent years were all announced in advance: registration tokens disabled in 17.0 (5.2), kaniko dropped from the GitLab docs as unmaintained (6.5), Jenkins requiring Java 21 from LTS 2.555.1 (10.1), and Traefik v3's 60-second default read timeout (7.4).
- **Pin everything a pipeline pulls:** `docker:28` and `docker:28-dind`, `alpine:3.22`, the scanner image, and Jenkins plugin versions. A floating `:latest` makes "nothing changed but it broke" possible.

### Capacity and concurrency

| Setting | Where | Meaning |
|---|---|---|
| `concurrent` | top of `config.toml` | maximum jobs at once for the whole runner process |
| `limit` | each `[[runners]]` block | maximum jobs for that runner entry (0 means no limit) |
| `request_concurrency` | each `[[runners]]` block | parallel requests for new jobs. Raise it when jobs queue while the host is idle |
| `resource_group` | `.gitlab-ci.yml` | one job at a time per group, for deploys (9.4) |

Size by the heaviest job: a DinD build of a Node.js app can use 2 vCPU and 3 GB of RAM. Four concurrent builds on an 8 GB VM will swap. The runner's metrics endpoint shows whether you are short of capacity:

```bash
curl -s http://127.0.0.1:9252/metrics | grep -E '^gitlab_runner_(jobs|concurrent|limit|errors_total)'
```

```text
gitlab_runner_concurrent 4
gitlab_runner_jobs{executor_stage="docker_run",runner="t3_Kd9aQ",stage="step_script",state="running"} 4
gitlab_runner_limit{runner="t3_Kd9aQ",system_id="s_8f2c1d"} 4
gitlab_runner_errors_total{level="warning"} 12
```

→ Four running jobs out of `concurrent = 4` during the morning merge rush means jobs are queueing on capacity, not on tags. Add a second runner VM rather than raising `concurrent` on a host that is already busy.

### Security hardening checklist

| Control | Why |
|---|---|
| Separate runners by trust: a **protected** deploy runner (only protected branches, holds Harbor push and deploy credentials) and an **unprivileged** runner for merge requests | merge request code must never reach production secrets or a privileged daemon (6.4) |
| Protected branches and tags (`main`, `v*`) plus protected variables | secrets only reach reviewed code (5.4) |
| Masked and hidden variables, file-type variables for keys | fewer leaks in logs (13.4) |
| CI/CD job token allowlist | stops other projects from using a job token against your project (8.3) |
| Short-lived credentials: GitLab `id_tokens` (OIDC) for Vault or AWS | nothing long-lived to steal |
| One Harbor robot account per project and purpose, with expiry and a rotation date | limits the blast radius and avoids surprise expiry (7.3) |
| Dokploy API keys stored only in protected variables, and the webhook URL treated as a secret | anyone holding the URL can trigger a deploy |
| Runner hosts patched, with their own audit logging (forward to Wazuh, see [module 48](48-wazuh-and-security-tools.md)) | the runner is root-equivalent on its host |

Supply-chain controls (image scanning with Trivy in Harbor or in CI, signing, SBOMs) are in [Security and DevSecOps](37-learn-security-devsecops.md).

### Backups and restore

| System | Back up | Restore test |
|---|---|---|
| GitLab Omnibus | `sudo gitlab-backup create`, plus `/etc/gitlab/gitlab-secrets.json` and `/etc/gitlab/gitlab.rb`. These two files are **not** in the backup archive, and without the secrets file CI variables and runner tokens cannot be decrypted | quarterly on a scratch VM |
| GitLab Runner | nothing critical: runners are cattle. Keep `config.toml` templates in configuration management and recreate runners with new tokens | rebuild `ci-01` from scratch once |
| Harbor | the database and the registry storage (or replication to a second Harbor), plus `harbor.yml` and certificates | pull an old SHA from the restored instance |
| Jenkins | JCasC files and Jenkinsfiles in Git, plus `JENKINS_HOME` without `workspace/` (build history, credentials store and its `secrets/` key files together) | start a controller from the image plus the restored home |
| Argo CD | Git is the source of truth. Also run `argocd admin export -n argocd > argocd-backup.yaml` for repos, projects and settings | `argocd admin import` into a lab cluster |

The 2017 GitLab.com database outage is the reference story for backups that silently did not work ([postmortem](https://about.gitlab.com/blog/2017/02/10/postmortem-of-database-outage-of-january-31/)). [Module 33](33-learn-cicd-iac-sre.md) turns it into a lab.

### Logs and health of the CI tools themselves

| Tool | Logs | Quick health check |
|---|---|---|
| GitLab Runner | `journalctl -u gitlab-runner` | `sudo gitlab-runner verify`, plus the metrics endpoint |
| GitLab Omnibus | `sudo gitlab-ctl tail` (or `gitlab-ctl tail gitlab-rails`, `sidekiq`) | `sudo gitlab-ctl status`, `sudo gitlab-rake gitlab:check SANITIZE=true` |
| Harbor | `/var/log/harbor/` (core.log, registry.log, proxy.log) | `docker compose ps` in the Harbor directory, `/api/v2.0/health` |
| Jenkins | `journalctl -u jenkins` or `docker logs jenkins` | Manage Jenkins, then System Information, plus the admin monitors |
| Actions runner | `_diag/Runner_*.log` and `_diag/Worker_*.log`, `journalctl -u 'actions.runner.*'` | runner status in the GitHub UI or API |
| Argo CD | `kubectl -n argocd logs deploy/argocd-repo-server`, `statefulset/argocd-application-controller` | `argocd app list`, `kubectl -n argocd get pods` |

### Cleanup routines

- **Runner disk:** a weekly systemd timer running `/usr/share/gitlab-runner/clear-docker-cache`, plus image and build-cache pruning with an age filter (8.1).
- **GitLab:** set a default artifact expiry. Occasionally run `sudo gitlab-rake gitlab:cleanup:orphan_job_artifact_files` (dry run by default) on Omnibus.
- **Harbor:** tag retention rules per project (for example, keep the last 30 SHA tags plus anything matching `v*`), then scheduled garbage collection. Retention removes old tags and artifacts, but only garbage collection frees the disk.
- **Jenkins:** a `buildDiscarder` in every pipeline, and `cleanWs()` in `post` (10.4).

---

## 4. Learning path

| Stage | Weeks | Do this | Prove it |
|---|---|---|---|
| Fresher (L0) | 1–2 | KodeKloud *GIT for Beginners* ([course](https://kodekloud.com/courses/git-for-beginners)). Then *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, section Architecture & Core Concepts ([course](https://kodekloud.com/courses/gitlab-ci-cd); note [Types of Executors](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Architecture-Core-Concepts/Types-of-Executors/page)) | a two-stage pipeline on GitLab.com that runs tests, and you can explain every log line |
| Junior (L1) | 3–5 | Same course: Continuous Integration with GitLab ([Docker Push](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Continuous-Integration-with-GitLab/Docker-Push/page)), then Self-Managed Runners ([Install Group Runner on Linux Machine with Docker Executor](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Self-Managed-Runners/Install-Group-Runner-on-Linux-Machine-with-Docker-Executor/page)). Free practice: [CI/CD Playground](https://kodekloud.com/playgrounds/playground-ci-cd) and the CI/CD tasks of [100 Days of DevOps](https://kodekloud.com/100-days-of-devops) | your own runner on `ci-01`, with entries 5.1–5.5 reproduced and fixed |
| Mid-level (L2) | 6–9 | *Docker Certified Associate*, Docker Image Management section ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course); note [Docker Image Registry](https://notes.kodekloud.com/docs/Docker-Certified-Associate-Exam-Course/Docker-Image-Management/Docker-Image-Registry/page)), plus [Harbor HTTPS docs](https://goharbor.io/docs/2.15.0/install-config/configure-https/) and LFCS [Work With SSL Certificates](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates) | the ops-ladder L3 exit test: build, tag with the SHA, push to Harbor through the private CA, deploy to Dokploy, test the rollback |
| Senior (L3) | 10–16 | GitLab course: Continuous Deployment, then Optimization, Security and Monitoring. *Helm for Beginners* ([course](https://kodekloud.com/courses/helm-for-beginners)), the CKA Helm Basics and Kustomize Basics sections, then the Argo CD docs. Add *Certified Jenkins Engineer* ([course](https://kodekloud.com/courses/certified-jenkins-engineer)) or *GitHub Actions Certification* ([course](https://kodekloud.com/courses/github-actions-certification), modules Self Hosted Runner and Security Guide) if your job uses them | runners split by trust level, an Argo CD app on the lab cluster, and a Jenkins controller rebuilt from JCasC |
| Senior/Lead (L4) | ongoing | *Certified Kubernetes Security Specialist (CKS)*, Supply Chain Security section ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)). *Fundamentals of SRE* ([course](https://kodekloud.com/courses/fundamentals-of-sre)). Use the change-request format (criticality, steps, verification, rollback) from [module 33](33-learn-cicd-iac-sre.md) | a written release and rollback policy, a secrets policy and a runner fleet design that another engineer can run without you |

The verified KodeKloud course list has no Argo CD or Flux course, so use the [Argo CD docs](https://argo-cd.readthedocs.io/en/stable/) and [Flux docs](https://fluxcd.io/flux/) directly. TechWorld with Nana's *GitLab CI CD Tutorial for Beginners* ([video](https://www.youtube.com/watch?v=qP8kir2GUgo), 68 minutes) is a good first watch before the course. The [career ladder](40-career-ladder.md) shows how CI/CD ownership grows from "fix my job" to "own the release process".

**How practitioners say they learned this.** The forum top lists are dominated by beginner questions: runner not picking up jobs, `docker login` from a non-TTY device, x509 errors, DinD not connecting. Each one costs hours the first time and minutes after that. Engineers who move up fast break things in a lab on purpose, standardise one shared CI template with pinned images, keep everything (runner config, JCasC, Argo CD apps) in Git, and read release notes and deprecation pages. Those pages predicted every big CI break of the last few years.

---

## 5. GitLab jobs that never start

These are the first problems every GitLab CI user meets: the pipeline exists, but jobs sit in *pending*, the runner refuses to register, the pipeline is missing or doubled, or a job starts with empty secrets. They dominate the GitLab forum's all-time top list.

### 5.1 Job stuck pending: no runner matches

> **Seen as:** `This job is stuck because of one of the following problems. There are no active runners online, no runners for the protected branch, or no runners that match all of the job's tags: docker harbor` · **Where:** a job that stays pending on a new project, a new branch, or after a runner change · **Level:** [L1 · Junior] · **How common:** one of the most-asked GitLab CI questions. "Gitlab runner not picking up jobs" alone has about 68k forum views

**Why it happens:** GitLab only gives a job to a runner that is allowed to take it. A runner must carry **every** tag the job lists. A job with no tags needs a runner with "Run untagged jobs" switched on. A runner marked **Protected** only takes jobs from protected branches and tags. A project runner only serves the projects it is assigned to, and instance runners can be switched off per project. A runner that is paused, or has not contacted GitLab for a while (shown as offline), takes nothing. When every matching runner is busy up to `concurrent`, the job also waits, but GitLab shows it as pending rather than stuck.

**Diagnose:**

```bash
sudo gitlab-runner verify                                 # on ci-01: is the token valid?
curl -sS -H "PRIVATE-TOKEN: $GITLAB_TOKEN" "https://gitlab.example.com/api/v4/runners/RUNNER_ID" \
  | jq -c '{status, paused, tag_list, run_untagged, access_level}'
grep -n 'tags:' .gitlab-ci.yml                            # what does the job ask for?
```

```
Verifying runner... is valid                        runner=t3_Kd9aQ
{"status":"online","paused":false,"tag_list":["docker","linux"],"run_untagged":false,"access_level":"ref_protected"}
42:  tags: [docker, harbor]
```

**What the output tells you:** The runner is healthy and online, so this is a matching problem, not a network one. Two things block the job. It asks for the `harbor` tag, which the runner does not have. And `access_level: ref_protected` means the runner only runs protected refs, so a feature-branch job will never match it. If `verify` had printed `is removed`, or the journal showed `403 Forbidden`, go to 5.2 instead.

**Fix:**

```bash
# UI: CI/CD > Runners > edit the runner: add the tag, untick "Protected" only if feature branches belong here.
curl -sS -X PUT -H "PRIVATE-TOKEN: $GITLAB_TOKEN" "https://gitlab.example.com/api/v4/runners/RUNNER_ID" \
  --data "tag_list=docker,linux,harbor"
# Or change the job so it only asks for tags that really exist:   tags: [docker]
```

**Why this fix works:** Matching is all-or-nothing on tags and protection, so either the runner gains what the job requires or the job stops requiring it. Keep deploy runners protected. When a feature-branch job asks for the deploy runner, the right fix is usually to change the job's tags, not to unprotect the runner that holds production credentials. Do not register an extra runner carrying every tag just to get jobs moving; that hides the design mistake.

**Prevent it:** Publish a short tag vocabulary (`docker`, `harbor-push`, `deploy-prod`) in your CI template repository. Alert when a runner goes offline, using the runner metrics or the API `status` field. Switch on "Run untagged jobs" only on general-purpose runners.

**Next step:** [Runners and executors in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, Self-Managed Runners ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** [GitLab forum: stuck, no runners with these tags](https://forum.gitlab.com/t/this-job-is-stuck-because-you-don-t-have-any-active-runners-online-with-any-of-these-tags-assigned/28205) · [GitLab forum: stuck because of one of the following problems](https://forum.gitlab.com/t/this-job-is-stuck-because-of-one-of-the-following-problems/104997) · [GitLab forum: runner not picking up jobs](https://forum.gitlab.com/t/gitlab-runner-not-picking-up-jobs/70464) · [gitlab issue 336205: runners need all tags](https://gitlab.com/gitlab-org/gitlab/-/issues/336205) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+runner+%22This+job+is+stuck%22+tags) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=job+stuck+pending+runner+tags&restrict_sr=1)

### 5.2 Runner can't register or authenticate

> **Seen as:** `Registering runner... failed ... 410 Gone (runner registration disallowed)`, or `FATAL: Runner configuration other than name and executor configuration is reserved ...`, or later `WARNING: Checking for jobs... forbidden ... 403 Forbidden` · **Where:** `gitlab-runner register` on GitLab 17+, or a runner that worked until someone touched it in the UI · **Level:** [L2 · Mid] · **How common:** a wave of forum questions after GitLab 17.0; the deprecation work item and Terraform runner modules all had to change

**Why it happens:** GitLab 16 introduced **runner authentication tokens** (prefix `glrt-`). You create the runner in the UI and the server stores its tags, protection and untagged settings. GitLab 17.0 disabled the old **registration tokens** by default, and removal is planned for 20.0. Old Ansible roles and blog posts still pass a registration token, which returns `410 Gone`. They also pass `--tag-list`, `--locked`, `--run-untagged` or `--access-level` together with a `glrt-` token, which triggers the "reserved" FATAL error because those settings now live on the server. A runner that registered fine and later logs `403 Forbidden` has a dead token: the runner was deleted in the UI, or its token was reset or expired.

**Diagnose:**

```bash
sudo gitlab-runner verify
sudo journalctl -u gitlab-runner -n 20 --no-pager | grep -E 'forbidden|410|FATAL|removed'
```

```
ERROR: Verifying runner... is removed               runner=t3_Kd9aQ
WARNING: Checking for jobs... forbidden             runner=t3_Kd9aQ status=POST https://gitlab.example.com/api/v4/jobs/request: 403 Forbidden
```

**What the output tells you:** `is removed` together with a 403 on `jobs/request` means GitLab no longer knows this token. Re-create the runner; restarting the service will not help. `410 Gone` during register means you used a legacy registration token. The "reserved" FATAL message means your command line mixes old flags with a new token.

**Fix:**

```bash
# 1. UI: CI/CD > Runners > New runner: set tags, Protected and Run untagged here, then copy the glrt- token.
sudo gitlab-runner verify --delete           # drop entries whose tokens GitLab rejects
sudo gitlab-runner register --non-interactive --url "https://gitlab.example.com" \
  --token "$RUNNER_TOKEN" --executor docker --docker-image alpine:3.22 --name ci-01-docker
```

**Why this fix works:** The new workflow splits responsibilities. The server owns the runner's identity and matching rules, and the host only holds a token plus executor settings, so tags set in the UI always match what GitLab enforces. Re-enabling registration tokens in the admin settings works as a short bridge for old automation, but it is a dead end, because removal is planned. Several identical build hosts may share one runner entry (each shows up as its own runner manager), but give hosts with different trust levels separate runners.

**Prevent it:** Provision runners with the new workflow in your configuration management (the token comes from the API or the UI, never hard-coded), document token expiry if your instance enforces it, and read the deprecations page before each GitLab major upgrade.

**Next step:** [Registering a runner in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, Self-Managed Runners ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · [GitLab docs: Registering runners](https://docs.gitlab.com/runner/register/)

**Community threads:** [GitLab deprecation 380872: registration tokens](https://gitlab.com/gitlab-org/gitlab/-/work_items/380872) · [terraform-aws-gitlab-runner #850](https://github.com/cattle-ops/terraform-aws-gitlab-runner/issues/850) · [GitLab forum: runner not picking up jobs](https://forum.gitlab.com/t/gitlab-runner-not-picking-up-jobs/70464) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab-runner+register+%22410+Gone%22) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=runner+registration+token+deprecated&restrict_sr=1)

### 5.3 Pipeline missing, doubled or invalid

> **Seen as:** no pipeline after a push; two pipelines for every push to a merge request branch; `'deploy' job needs 'build' job, but 'build' does not exist in the pipeline`; `Pipeline cannot be run. No stages / jobs for this pipeline.` · **Where:** after moving from `only/except` to `rules`, or after adding includes · **Level:** [L2 · Mid] · **How common:** "Multiple pipelines for same repo" (about 96k views) and "OR condition with needs" (about 73k) are GitLab forum classics

**Why it happens:** `rules` are evaluated per job and per pipeline source. A rule such as `if: $CI_COMMIT_BRANCH` matches the branch pipeline, and a merge request rule matches the merge request pipeline, so every push creates two pipelines. A `workflow:rules` block that excludes the ref, a `[skip ci]` in the commit message, or invalid YAML means no pipeline at all. When `rules` remove a job that another job `needs`, the pipeline is rejected, unless the dependency is declared optional.

**Diagnose:**

```bash
curl -sS -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.example.com/api/v4/projects/PROJECT_ID/ci/lint?dry_run=true&dry_run_ref=main" | jq -c '.valid, .errors'
git log -1 --format=%B | grep -i 'skip ci'
```

```
false
["'deploy' job needs 'build' job, but 'build' does not exist in the pipeline. This might be because of the only, except, or rules keywords. To need a job that sometimes does not exist in the pipeline, use needs:optional."]
```

**What the output tells you:** The lint API runs the same validation GitLab runs on push, simulated for the `main` branch (`dry_run_ref`; the older `ref` parameter is deprecated). Here `build` is filtered out by its own rules on `main`, so `deploy` cannot depend on it. For doubled pipelines, the Pipelines page shows one entry labelled "merge request" and one labelled "branch" for the same commit.

**Fix:**

```yaml
workflow:                                  # one pipeline per push: MR pipeline if an MR is open, else branch
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH && $CI_OPEN_MERGE_REQUESTS
      when: never
    - if: $CI_COMMIT_BRANCH
deploy:
  needs: [{ job: build, optional: true }]
```

**Why this fix works:** `workflow:rules` decides whether a pipeline exists before any job rule is checked. This pattern is GitLab's documented switch between branch and merge request pipelines. `needs:optional` tells GitLab to ignore the dependency when rules removed that job. Do not paper over doubled pipelines with `interruptible` alone. You would still burn runner time and get two statuses on the merge request.

**Prevent it:** Add a lint job (or the pipeline editor's validation) to the CI template repository, keep exactly one `workflow:rules` block at the top of the main file, and test rule changes on a branch with a draft merge request.

**Next step:** [Rules, needs and the DAG in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, Optimization, Security and Monitoring ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** [GitLab forum: multiple pipelines for same repo](https://forum.gitlab.com/t/multiple-pipelines-for-same-repo/3897) · [GitLab forum: OR condition with needs](https://forum.gitlab.com/t/is-there-a-way-to-use-or-condition-with-needs-in-gitlab-ci-job/70393) · [GitLab forum: pipeline fail with no CI configuration](https://forum.gitlab.com/t/pipeline-fail-in-project-with-no-ci-configuration/54277) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+duplicate+pipelines+merge+request+workflow+rules) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=duplicate+pipelines+merge+request&restrict_sr=1)

### 5.4 Protected variables arrive empty

> **Seen as:** `Error: Cannot perform an interactive login from a non TTY device` on `docker login`, or `curl: (22) The requested URL returned error: 401` from a deploy call · **Where:** feature-branch or merge request pipelines; the same job works on `main` · **Level:** [L1 · Junior] · **How common:** about 92k views on the GitLab forum thread, plus a long-running Stack Overflow classic

**Why it happens:** A variable marked **Protected** is only exported to pipelines running on protected branches or tags. On any other branch the variable is simply absent. `docker login -u "" -p ""` then falls back to an interactive prompt, which cannot work without a terminal. The same happens when a variable is scoped to an environment the job does not use, or when an old pipeline still uses `CI_BUILD_TOKEN`, which was deprecated in GitLab 9.0 and removed in 16.0 (with all `CI_BUILD_*` variables). Replace it with `CI_JOB_TOKEN`.

**Diagnose:**

```bash
# Add temporarily to the failing job; prints facts, never the secret itself
echo "ref=$CI_COMMIT_REF_NAME protected=$CI_COMMIT_REF_PROTECTED env=${CI_ENVIRONMENT_NAME:-none}"
echo "HARBOR_USER set: ${HARBOR_USER:+yes}   HARBOR_PASSWORD set: ${HARBOR_PASSWORD:+yes}"
```

```
ref=feature/new-cart protected=false env=none
HARBOR_USER set:    HARBOR_PASSWORD set:
```

**What the output tells you:** An unprotected ref with both variables unset is the protected-variable rule at work. If the ref was protected and the variables were still empty, check environment scope and spelling (variable names are case-sensitive), and whether the variable belongs to a different group.

**Fix:**

```yaml
build-image:
  rules:
    - if: $CI_COMMIT_REF_PROTECTED == "true"          # push to Harbor only from protected refs
  script:
    - echo "$HARBOR_PASSWORD" | docker login -u "$HARBOR_USER" --password-stdin harbor.example.com
# For MR builds use a separate, pull-only or scratch-project robot stored as an unprotected variable.
```

**Why this fix works:** Protection exists so that unreviewed branch code cannot read production credentials. Gating the job on `CI_COMMIT_REF_PROTECTED` makes the pipeline say what it needs, instead of failing with a confusing TTY error. `--password-stdin` also keeps the password out of the process list. Do **not** unprotect the production push or deploy credentials to make feature branches pass. That undoes the control for everyone who can push a branch.

**Prevent it:** Add a `before_script` guard that fails with a clear message when required variables are missing (`: "${HARBOR_USER:?not set - is this ref protected?}"`). Protect `main` and the release tags `v*`.

**Next step:** [Variables: predefined, masked, protected in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, Architecture & Core Concepts ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** [GitLab forum: Cannot perform an interactive login from a non TTY device](https://forum.gitlab.com/t/error-cannot-perform-an-interactive-login-from-a-non-tty-device/59936) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+%22Cannot+perform+an+interactive+login+from+a+non+TTY+device%22) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=protected+variable+empty&restrict_sr=1)

### 5.5 Masked values and dollar-sign expansion

> **Seen as:** `unauthorized: authentication required` when logging in to Harbor as `robot$shop+ci`, a password containing `$` that "is wrong" only in CI, or the UI refusing to save a masked variable · **Where:** GitLab CI with Harbor robot accounts, or any secret containing `$` · **Level:** [L2 · Mid] · **How common:** two Harbor issues about it; "use variable inside other variable" is the most upvoted GitLab Runner work item (488 upvotes)

**Why it happens:** GitLab expands `$NAME` references inside variable values by default. Harbor names robot accounts `robot$PROJECT+NAME`. The `$shop` part is read as a reference to a variable named `shop` (a name ends at the first character that is not a letter, digit or underscore), which does not exist, so the username that reaches the job is `robot+ci`. Shell quoting in your script cannot fix this, because the expansion already happened before the shell runs. Masking has its own rules: the value must be a single line, meet a minimum length, and use only certain characters. Multi-line keys and some passwords therefore cannot be masked.

**Diagnose:**

```bash
echo "user length=${#HARBOR_USER} starts=${HARBOR_USER:0:6}"   # safe: length and a non-secret prefix
```

```
user length=8 starts=robot+
```

**What the output tells you:** Eight characters for a username that should read `robot$shop+ci` (13 characters) means `$shop` was expanded to an empty string, leaving `robot+ci`.

**Fix:**

```yaml
# Best: Settings > CI/CD > Variables > HARBOR_USER: untick "Expand variable reference" (API: raw=true).
# Or, for a non-secret value defined in YAML, escape the dollar:
variables:
  HARBOR_USER: 'robot$$shop+ci'
```

**Why this fix works:** A raw (non-expanded) variable is passed to the job byte for byte, and `$$` is GitLab's escape for a literal `$`. Harbor also lets an administrator change the robot name prefix, which avoids the `$` for new accounts. For values that cannot be masked, use a **file-type** variable, which never prints the value in the log, and never echo it.

**Prevent it:** Create every credential variable as masked, protected and raw. When you rotate a robot account, test the login in a scratch pipeline before the release pipeline needs it.

**Next step:** [Variables in module 33](33-learn-cicd-iac-sre.md) · [Harbor docs: robot accounts](https://goharbor.io/docs/1.10/working-with-projects/project-configuration/create-robot-accounts/) · KodeKloud community post *Setting up your own Container Registry with Harbor* ([post](https://kodekloud.com/community/t/setting-up-your-own-container-registry-with-harbor/275367))

**Community threads:** [goharbor/harbor #9732: robot$ breaks GitLab CI](https://github.com/goharbor/harbor/issues/9732) · [goharbor/harbor #9553: no $ in robot names](https://github.com/goharbor/harbor/issues/9553) · [renovate discussion #32194](https://github.com/renovatebot/renovate/discussions/32194) · [GitLab forum: docker login with gitlab-ci](https://forum.gitlab.com/t/cannot-do-docker-login-with-gitlab-ci-in-local/16229) · [gitlab-runner 1809: variable inside variable](https://gitlab.com/gitlab-org/gitlab-runner/-/work_items/1809) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+ci+harbor+robot+docker+login+unauthorized) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=variable+dollar+sign+expand&restrict_sr=1)

---

## 6. Building images in CI

Building a container image inside a container is where CI meets Docker internals: DinD and TLS, nested networks with their own MTU and DNS, the security cost of the Docker socket, and the move away from kaniko. Background: [Building images in module 33](33-learn-cicd-iac-sre.md) and [Learn Docker](30-learn-docker.md).

### 6.1 Cannot connect to the Docker daemon in DinD

> **Seen as:** `Cannot connect to the Docker daemon at tcp://docker:2375. Is the docker daemon running?` or `error during connect: Post http://docker:2375/v1.40/auth: dial tcp: lookup docker on 169.254.169.254:53: no such host` · **Where:** jobs using `services: [docker:dind]` · **Level:** [L1–L2 · Junior → Mid] · **How common:** about 141k views on the GitLab forum "lookup docker ... no such host" thread, plus about 62k on "dind stops working after update"

**Why it happens:** The job's Docker client talks to a second Docker daemon running in the `docker:dind` service container. Since Docker 19.03, the dind image generates TLS certificates into `DOCKER_TLS_CERTDIR` and listens with TLS on **2376**. Old templates still point at 2375. If the runner is not `privileged`, the dind container dies at start. If the job has no `services:`, runs on a shell executor (which ignores services), or uses a network setting that breaks service aliases, the name `docker` does not resolve. That is the "no such host" error.

**Diagnose:**

```bash
# In the failing job, with CI_DEBUG_SERVICES: "true" in its variables so the dind log is shown
env | grep -E '^DOCKER_(HOST|TLS|CERT)'; getent hosts docker || echo "no docker alias"; ls /certs/client
sudo grep -nE 'privileged|volumes' /etc/gitlab-runner/config.toml      # on ci-01
```

```
DOCKER_HOST=tcp://docker:2375
DOCKER_TLS_CERTDIR=/certs
172.17.0.3      docker
ca.pem  cert.pem  key.pem
[service:docker-dind] level=info msg="API listen on [::]:2376"
12:    privileged = true
```

**What the output tells you:** The alias resolves, the service runs privileged and client certificates exist, but the client dials 2375 while the daemon listens with TLS on 2376. That is the version-era mismatch. If `getent` had printed "no docker alias", look for a missing `services:` entry or a shell executor. If the service log shows `mount: permission denied (are you root?)`, the runner is not privileged.

**Fix:**

```yaml
build-image:
  image: docker:28
  services: [docker:28-dind]
  variables:
    DOCKER_HOST: tcp://docker:2376
    DOCKER_TLS_CERTDIR: "/certs"
    DOCKER_TLS_VERIFY: "1"
    DOCKER_CERT_PATH: "$DOCKER_TLS_CERTDIR/client"
# config.toml on the build runner: privileged = true, volumes = ["/certs/client", "/cache"]
```

**Why this fix works:** The `/certs/client` volume is shared by the service and the job container. The daemon writes the client certificates there, and the client reads them to connect on 2376. Pinning the client and the daemon to the same major version avoids API mismatches. Turning TLS off (`DOCKER_TLS_CERTDIR: ""` with port 2375) also works, but only on a runner nobody else shares. Do not switch to mounting `/var/run/docker.sock` as a "quick fix" (6.4).

**Prevent it:** Ship one `include:` template for image builds with pinned images, and document `CI_DEBUG_SERVICES` in it.

**Next step:** [Building images: DinD, kaniko, buildah in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, Continuous Integration with GitLab ([Docker Push note](https://notes.kodekloud.com/docs/GitLab-CICD-Architecting-Deploying-and-Optimizing-Pipelines/Continuous-Integration-with-GitLab/Docker-Push/page)) · [GitLab docs: Use Docker to build Docker images](https://docs.gitlab.com/ci/docker/using_docker_build/)

**Community threads:** [GitLab forum: lookup docker on 169.254.169.254:53: no such host](https://forum.gitlab.com/t/error-during-connect-post-http-docker-2375-v1-40-auth-dial-tcp-lookup-docker-on-169-254-169-254-no-such-host/28678) · [GitLab forum: dind stops working after 12.1.0 update](https://forum.gitlab.com/t/docker-dind-stops-working-after-12-1-0-update/28664) · [GitLab Runner docs: Docker executor](https://docs.gitlab.com/runner/executors/docker/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+%22Cannot+connect+to+the+Docker+daemon+at+tcp%3A%2F%2Fdocker%3A2375%22) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=dind+cannot+connect+docker+daemon&restrict_sr=1)

### 6.2 DinD builds hang on downloads (MTU)

> **Seen as:** `npm install`, `pip download`, `dotnet restore` or `apt-get update` inside `docker build` hangs and then times out, while DNS works and small requests succeed · **Where:** DinD on runners behind VXLAN, VPN, OpenStack or Kubernetes overlays · **Level:** [L3 · Senior] · **How common:** GitLab forum threads on NuGet and pip hangs, a GitLab Runner issue and a GitLab support KB article on this exact mismatch

**Why it happens:** Your runner's network path carries packets of at most, for example, 1450 bytes (VXLAN overhead, WireGuard, an MTU-limited tunnel). The inner dockerd in `docker:dind` creates its bridge with MTU 1500 regardless. Small packets get through, but full-size TCP segments (TLS certificates, package downloads) are dropped. The "fragmentation needed" ICMP reply that should shrink them is often filtered, so the connection stalls silently instead of failing. This is a path-MTU black hole.

**Diagnose:**

```bash
ip link show ens18 | grep -o 'mtu [0-9]*'                       # on ci-01: the uplink MTU
ping -c2 -M do -s 1472 mirror.example.com                       # 1472 + 28 = 1500 bytes, DF set
docker run --rm alpine cat /sys/class/net/eth0/mtu              # inside the job: MTU of dind's containers
```

```
mtu 1450
ping: local error: message too long, mtu=1450
1500
```

**What the output tells you:** The host can only send 1450-byte packets, but containers created by the inner daemon think they can send 1500. Every large segment they send is lost. If the host MTU were 1500 and only a remote VPN hop were smaller, you would see 100% loss on the 1472-byte ping and success at `-s 1372`.

**Fix:**

```yaml
services:
  - name: docker:28-dind
    command: ["--mtu=1400"]          # host MTU minus a safety margin; go to 1360 behind VPNs
# config.toml: environment = ["FF_NETWORK_PER_BUILD=true"] and [runners.docker] network_mtu = 1400
```

**Why this fix works:** A smaller MTU on the inner bridge makes TCP advertise a smaller MSS, so segments fit the real path and no fragmentation or ICMP is needed. `network_mtu` does the same for the per-job network the runner creates. Do not "fix" this with retries or longer timeouts. The download will keep stalling at the same size.

**Prevent it:** Record the path MTU of every network segment in your inventory ([ports and inventory playbook](22-playbook-ports-inventory.md)) and bake `--mtu` into the shared build template. A pipeline that "hangs only on big downloads" should make you suspect MTU first.

**Next step:** [Network speed playbook](24-playbook-network-speed.md) · KodeKloud: *Docker Certified Associate*, Docker Engine – Networking ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · [GitLab Runner docs: Docker executor](https://docs.gitlab.com/runner/executors/docker/)

**Community threads:** [GitLab forum: DinD network issue, NuGet hang](https://forum.gitlab.com/t/docker-in-docker-network-issue-nuget-hang/133841) · [GitLab Support: DinD jobs and MTU mismatch](https://support.gitlab.com/hc/en-us/articles/27528955698972-Docker-in-Docker-jobs-on-GitLab-com-hosted-runners-fail-to-reach-NuGet-API-due-to-MTU-mismatch) · [gitlab-runner #6697: hangs with docker:dind](https://gitlab.com/gitlab-org/gitlab-runner/-/issues/6697) · [GitLab forum: pip install hangs](https://forum.gitlab.com/t/gitlab-runner-hangs-infrequently-on-pythons-pip-install-or-pip-download/26143) · [Dustin Rue: DinD builds that stall](https://dustinrue.com/2020/08/fixing-dind-builds-that-stall-when-using-gitlab-and-kubernetes/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+dind+mtu+hang+npm+install) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=docker+in+docker+mtu+hang&restrict_sr=1)

### 6.3 Builds can't resolve internal names

> **Seen as:** `Could not resolve host: git.internal.example.com`, `getaddrinfo EAI_AGAIN registry.npmjs.org` or `Temporary failure resolving 'archive.ubuntu.com'`, but only inside `docker build` in CI · **Where:** on-prem runners whose firewall allows only the internal resolvers · **Level:** [L2 · Mid] · **How common:** it is in the ops-ladder case library, and Dokploy's networking troubleshooting page covers the same build-DNS failure

**Why it happens:** Containers copy their resolver list from where they were started. With `FF_NETWORK_PER_BUILD` (as in section 2), the dind service sits on a per-job network, so its `/etc/resolv.conf` points at Docker's embedded DNS `127.0.0.11`. On a host-network setup it points at systemd's stub `127.0.0.53` instead. A loopback resolver is unusable inside nested containers, so the inner daemon falls back to Docker's defaults, **8.8.8.8 and 8.8.4.4**. Your on-prem firewall blocks those, and internal split-horizon names do not exist there anyway.

**Diagnose:**

```bash
grep -E '^nameserver|ExtServers' /etc/resolv.conf                   # in the job container
docker run --rm busybox grep '^nameserver' /etc/resolv.conf          # a container started by the dind daemon
docker run --rm busybox nslookup git.internal.example.com
```

```
nameserver 127.0.0.11
# ExtServers: [10.20.0.53 10.20.0.54]
nameserver 8.8.8.8
nameserver 8.8.4.4
;; connection timed out; no servers could be reached
```

**What the output tells you:** The job container sits on the per-job network, so it uses Docker's embedded DNS (`127.0.0.11`), which forwards to your resolvers from the runner's `dns` setting (recent Docker Engine versions list them on a `# ExtServers:` comment line; older ones show only `127.0.0.11`). Containers the build creates got Google's public servers instead, which the firewall drops. Each nesting level must be configured separately.

**Fix:**

```yaml
services:
  - name: docker:28-dind
    command: ["--mtu=1400", "--dns=10.20.0.53", "--dns=10.20.0.54"]
# config.toml [runners.docker]: dns = ["10.20.0.53", "10.20.0.54"], dns_search = ["example.com"]
# shell-executor hosts and Dokploy build hosts: "dns" in /etc/docker/daemon.json
```

**Why this fix works:** `--dns` sets the inner daemon's default resolvers for every container and BuildKit `RUN` step it starts, which replaces the 8.8.8.8 fallback. The runner's `dns` covers the job and service containers. Do not open 8.8.8.8 in the firewall as the fix: internal names still will not resolve, and DNS leaves your network unlogged.

**Prevent it:** Add a smoke job to the template that resolves one internal name and one external name from inside a nested container, and keep resolver IPs in configuration management. DNS internals: [DNS module](08-dns.md).

**Next step:** [Learn Docker: networking](30-learn-docker.md) · KodeKloud: *Demystifying DNS* ([course](https://kodekloud.com/courses/demystifying-dns)) · [Dokploy docs: networking and DNS troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/networking)

**Community threads:** [Dokploy docs: build DNS failures](https://docs.dokploy.com/docs/core/troubleshooting/networking) · [GitLab Runner docs: Docker executor (dns option)](https://docs.gitlab.com/runner/executors/docker/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+runner+docker+build+%22could+not+resolve+host%22+dind+dns) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=gitlab+runner+dns+docker+build&restrict_sr=1)

### 6.4 Runner hosts are root: socket and privileged

> **Seen as:** a security review finds a job that ran `docker run -v /:/host alpine cat /host/etc/shadow`; jobs from different projects see each other's containers in `docker ps`; a fork pull request ran a crypto miner on a self-hosted GitHub runner · **Where:** shared on-prem runners, and GitHub self-hosted runners on public repositories · **Level:** [L3 · Senior] · **How common:** a long-standing warning in both GitLab and GitHub docs; "runner inside Docker" is a top `actions/runner` request

**Why it happens:** Mounting `/var/run/docker.sock` into jobs gives every job full control of the host's Docker daemon, which means root on the host. It can start privileged containers, read other jobs' environment variables and touch production containers on the same machine. `privileged = true` for DinD is root-equivalent inside the job too. When one runner serves merge requests, sandbox projects and production deploys, the least-trusted code runs next to the most valuable secrets. On GitHub, a self-hosted runner attached to a public repository runs code from anyone who opens a pull request.

**Diagnose:**

```bash
sudo grep -nE 'privileged|docker.sock|volumes' /etc/gitlab-runner/config.toml
curl -sS -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.example.com/api/v4/runners/RUNNER_ID/projects?per_page=100" | jq -r '.[].path_with_namespace'
```

```
15:    volumes = ["/var/run/docker.sock:/var/run/docker.sock", "/cache"]
platform/deploy-config
shop/web
sandbox/intern-tests
```

**What the output tells you:** One socket-bound runner is shared by the deploy repository and a sandbox project. Anyone who can push to `sandbox/intern-tests` effectively has root on the host that runs your production deploy jobs.

**Fix:**

```toml
# ci-build-01: unprivileged, any branch or MR; images built rootless with Buildah (6.5)
[[runners]]
  name = "ci-build-01"
  [runners.docker]
    privileged = false
    volumes = ["/cache"]
# ci-deploy-01: marked Protected in the UI, tag deploy-prod, assigned only to release projects,
#               the only place with Harbor push and Dokploy API credentials
```

**Why this fix works:** It turns one trust zone into two. Unreviewed code runs where there is nothing to steal and no root to gain. Reviewed code on protected refs runs where the credentials are. For stronger isolation, use docker-autoscaler (with `max_use_count = 1`, a fresh VM per job) or the Kubernetes executor with rootless builds. On GitHub, use self-hosted runners only for private repositories, and prefer ephemeral runners (`--ephemeral`, or Actions Runner Controller) so no state survives between jobs.

**Prevent it:** Keep a runner inventory listing trust level, executor, privileged yes or no, and assigned projects. Review it every quarter, and forward runner host audit logs to Wazuh ([module 48](48-wazuh-and-security-tools.md)).

**Next step:** [Security and DevSecOps](37-learn-security-devsecops.md) · KodeKloud: *GitHub Actions Certification*, Security Guide module ([course](https://kodekloud.com/courses/github-actions-certification)) · [GitLab docs: Use Docker to build Docker images](https://docs.gitlab.com/ci/docker/using_docker_build/)

**Community threads:** [actions/runner #406: runner inside a Docker container](https://github.com/actions/runner/issues/406) · [GitLab docs: DinD and socket binding trade-offs](https://docs.gitlab.com/ci/docker/using_docker_build/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+runner+docker.sock+security+privileged) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=self+hosted+runner+security+docker+socket&restrict_sr=1)

### 6.5 Kaniko is archived: moving to Buildah

> **Seen as:** the GitLab kaniko docs page now only says that kaniko is no longer maintained; migrating to Buildah fails with `'overlay' is not supported over overlayfs, a mount_program is required` or `unshare(CLONE_NEWUSER): Operation not permitted`; old kaniko jobs fail with `error checking push permissions ... x509: certificate signed by unknown authority` · **Where:** unprivileged image builds · **Level:** [L2–L3 · Mid → Senior] · **How common:** every team that adopted kaniko to avoid privileged DinD has to migrate

**Why it happens:** Kaniko was the popular daemonless builder. Its repository is no longer maintained, and GitLab replaced its kaniko documentation with a notice that points to Docker, Buildah or Podman instead. An unmaintained builder receives no security fixes. Buildah is the usual replacement, but inside an unprivileged container it cannot stack overlayfs on overlayfs or create user namespaces. It needs the `vfs` storage driver and `chroot` isolation. Kaniko's own x509 error comes from its separate trust bundle in `/kaniko/ssl/certs`, which ignores the host CA store.

**Diagnose:**

```bash
buildah info | grep -E '"GraphDriverName"|"rootless"'       # in a debug job using the buildah image
```

```
        "rootless": false,
        "GraphDriverName": "overlay",
```

**What the output tells you:** Buildah is trying overlay storage inside a container whose filesystem is already overlay, without fuse-overlayfs, so the first layer write fails. Switch the storage driver.

**Fix:**

```yaml
build-image:
  image: quay.io/buildah/stable:VERSION          # pin the tag you tested
  variables: { STORAGE_DRIVER: vfs, BUILDAH_ISOLATION: chroot, BUILDAH_FORMAT: docker }
  before_script:
    - mkdir -p /etc/containers/certs.d/harbor.example.com
    - cp "$HARBOR_CA_FILE" /etc/containers/certs.d/harbor.example.com/ca.crt   # file-type variable
    - echo "$HARBOR_PASSWORD" | buildah login -u "$HARBOR_USER" --password-stdin harbor.example.com
  script:
    - buildah build -t "$IMAGE:$CI_COMMIT_SHORT_SHA" .
    - buildah push "$IMAGE:$CI_COMMIT_SHORT_SHA"
```

**Why this fix works:** `vfs` copies layers instead of mounting them, so nothing depends on nested overlayfs. It is slower and uses more disk, which is the price of no privileges. `chroot` isolation runs `RUN` steps without new namespaces. `/etc/containers/certs.d/HOST/ca.crt` is where Buildah and Podman look for a registry CA. If a runner's seccomp or AppArmor profile still blocks Buildah, use a dedicated build runner with a relaxed profile rather than going back to privileged mode. Until a kaniko job is migrated, `--registry-certificate harbor.example.com=/path/ca.crt` fixes its x509 error.

**Prevent it:** Treat build tools like any dependency. Track their maintenance status, pin versions, and keep the build logic in one shared template so a migration is one merge request.

**Next step:** [Building images in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, Optimization, Security and Monitoring ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** [GitLab docs: kaniko page (no longer maintained)](https://docs.gitlab.com/ci/docker/using_kaniko) · [GoogleContainerTools/kaniko](https://github.com/GoogleContainerTools/kaniko) · [Stuart Ellis: Buildah and GitLab](https://www.stuartellis.name/articles/buildah-gitlab/) · [to be continuous: Docker template (Buildah default)](https://to-be-continuous.gitlab.io/doc/ref/docker/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=buildah+gitlab+ci+%22not+supported+over+overlayfs%22) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=kaniko+archived+buildah&restrict_sr=1)

---

## 7. Registries: Harbor and the private CA

Pushing to Harbor through an internal CA is the core of your L3 exit test, and the point where most on-prem pipelines first fail. Each client keeps its own trust store, Harbor's permission model is strict, and a reverse proxy in the path adds body-size and timeout limits. The Harbor server side (projects, GC, replication) is covered in [Learn Docker](30-learn-docker.md). This section is the CI side.

### 7.1 Runner rejects GitLab's certificate

> **Seen as:** `tls: failed to verify certificate: x509: certificate signed by unknown authority` during `gitlab-runner register` or `verify`, or in the clone step `fatal: unable to access 'https://gitlab.example.com/shop/web.git/': server certificate verification failed. CAfile: none CRLfile: none` · **Where:** a GitLab served with an internal CA · **Level:** [L2 · Mid] · **How common:** about 129k views on the GitLab forum thread "Gitlab runner Server certificate verification failed"

**Why it happens:** Two processes talk to GitLab: the runner process on the host, and the helper container that clones your repository inside each job. Both must trust the CA that signed GitLab's certificate. Often the host was never given the CA. Or GitLab sends only its leaf certificate without the intermediate, so even clients that trust the root cannot build the chain. The certificate's SAN may also lack the hostname the runner uses.

**Diagnose:**

```bash
openssl s_client -connect gitlab.example.com:443 -servername gitlab.example.com -showcerts </dev/null 2>/dev/null \
  | grep -E '^ *[0-9] s:|^ *i:|Verify return code'
ls -l /etc/gitlab-runner/certs/
```

```
 0 s:CN = gitlab.example.com
   i:CN = Example Corp Issuing CA 1
Verify return code: 21 (unable to verify the first certificate)
total 0
```

**What the output tells you:** Only depth 0 is sent, so the server omits its intermediate, and this host cannot build a chain from the leaf (code 21, which OpenSSL reports after an earlier `num=20` line for depth 0). The empty `certs/` directory means the runner has no CA file of its own. Code 20 ("unable to get local issuer certificate") as the final result, with depth 0 and 1 both listed, would mean the chain is complete but this host lacks the root CA. Code 19 means the server also sent a self-signed root that this host does not trust.

**Fix:**

```bash
sudo cp corp-root-ca.crt /usr/local/share/ca-certificates/ && sudo update-ca-certificates   # host trust
sudo cp corp-chain.pem /etc/gitlab-runner/certs/gitlab.example.com.crt   # PEM, file named after the host
sudo gitlab-runner verify
# Server side (Omnibus): point nginx['ssl_certificate'] at leaf + intermediate (full chain), then gitlab-ctl reconfigure
```

**Why this fix works:** The runner reads `/etc/gitlab-runner/certs/HOSTNAME.crt` (or `tls-ca-file` in `config.toml`) and passes that CA to the helper container through `CI_SERVER_TLS_CA_FILE`, which fixes the clone step too. Your own job images that call other HTTPS services need the CA mounted, plus `update-ca-certificates` in a `pre_build_script`. Do not set `GIT_SSL_NO_VERIFY=true` or skip-verify flags. They also hide a real man-in-the-middle.

**Prevent it:** Distribute the CA through configuration management to every runner, monitor certificate expiry, and test the chain with `openssl s_client` from a host that has only the root.

**Next step:** [Web, HTTP and TLS](18-web-http-tls.md) · KodeKloud: LFCS note [Work With SSL Certificates](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates) · [GitLab Runner docs: self-signed certificates](https://docs.gitlab.com/runner/configuration/tls-self-signed/)

**Community threads:** [GitLab forum: runner server certificate verification failed](https://forum.gitlab.com/t/gitlab-runner-server-certificate-verification-failed/59450) · [GitLab Runner docs: custom CAs](https://docs.gitlab.com/runner/configuration/tls-self-signed/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab-runner+x509+%22certificate+signed+by+unknown+authority%22) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=runner+x509+self+signed&restrict_sr=1)

### 7.2 Push to Harbor fails with x509

> **Seen as:** `Error response from daemon: Get "https://harbor.example.com/v2/": tls: failed to verify certificate: x509: certificate signed by unknown authority` in a DinD job, although `docker login harbor.example.com` works on `ci-01` itself; with a BuildKit builder, `failed to do request: Head "https://harbor.example.com/v2/...": x509: ...` · **Where:** DinD, BuildKit container builders, Buildah · **Level:** [L2 · Mid] · **How common:** the ops-ladder Harbor case, a long-running `docker/buildx` issue, and a frequent forum topic

**Why it happens:** The push is done by the daemon inside the `docker:dind` service container, not by the host's Docker. That daemon reads its own `/etc/docker/certs.d`, which is empty unless you mount the CA into it. A `docker-container` BuildKit builder ignores `certs.d` completely and needs the CA in its `buildkitd.toml`. Buildah reads `/etc/containers/certs.d` (6.5).

**Diagnose:**

```bash
# Inside the DinD job: this bind mount is resolved by the dind daemon, so it shows the daemon's certs.d
docker run --rm -v /etc/docker/certs.d:/x:ro alpine ls -R /x
docker buildx ls | head -2            # docker driver = uses the daemon's trust; docker-container = its own
```

```
/x:
NAME/NODE     DRIVER/ENDPOINT   STATUS    BUILDKIT   PLATFORMS
default*      docker
```

**What the output tells you:** The dind daemon has no Harbor CA at all, so the host's correct `certs.d` is irrelevant. The builder uses the `docker` driver, so fixing the daemon's `certs.d` is enough. With a `docker-container` builder you would also need the `buildkitd.toml` change below.

**Fix:**

```toml
# /etc/gitlab-runner/config.toml [runners.docker]: runner volumes are mounted into service containers too
volumes = ["/certs/client", "/cache", "/etc/docker/certs.d/harbor.example.com/ca.crt:/etc/docker/certs.d/harbor.example.com/ca.crt:ro"]
```

```toml
# buildkitd.toml for a docker-container builder: docker buildx create --use --buildkitd-config buildkitd.toml
# (older buildx releases call this flag --config; it is deprecated in current ones)
[registry."harbor.example.com"]
  ca = ["/etc/ssl/certs/corp-root-ca.crt"]
```

**Why this fix works:** Docker reads `certs.d/HOST/ca.crt` on every registry connection, so the mounted file takes effect without restarting anything. `buildx create --buildkitd-config` copies the referenced CA into the builder. Do **not** add Harbor to `insecure-registries`. It turns off certificate verification for that registry, and the habit tends to spread to production hosts.

**Prevent it:** Keep a CA distribution checklist per client: host Docker, DinD (runner volumes), BuildKit, Buildah, containerd on Kubernetes nodes (`/etc/containerd/certs.d`), every Dokploy Swarm node (9.1) and Argo CD (12.3).

**Next step:** [Pushing to Harbor with the commit SHA in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *Docker Certified Associate*, Docker Image Management ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · [Harbor docs: Configure HTTPS](https://goharbor.io/docs/2.15.0/install-config/configure-https/)

**Community threads:** [Docker docs: registry certificates](https://docs.docker.com/engine/security/certificates/) · [docker/buildx #1642](https://github.com/docker/buildx/issues/1642) · [Docker docs: BuildKit configuration](https://docs.docker.com/build/buildkit/configure/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+dind+harbor+x509+%22certificate+signed+by+unknown+authority%22) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=harbor+x509+gitlab+runner&restrict_sr=1)

### 7.3 Push denied or unauthorized

> **Seen as:** `denied: requested access to the resource is denied`, or Harbor's `unauthorized: unauthorized to access repository: shop/web, action: push`, or a pipeline that worked for a month now failing with `unauthorized: authentication required` · **Where:** the first push from CI, or after an account change · **Level:** [L1 · Junior] · **How common:** the top `forums.docker.com` topic family; Harbor robot accounts often expire silently

**Why it happens:** An image name without a registry host (`shop/web:1.4`) is pushed to Docker Hub, which denies it. Harbor does not create projects on push, so the project must already exist. A robot account needs explicit **push** permission on that project. Robot accounts created with the default expiry setting stop working after 30 days. Docker stores credentials per exact host string, so a login to `harbor.example.com:443` does not cover pushes to `harbor.example.com`.

**Diagnose:**

```bash
echo "$IMAGE"                                   # must start with harbor.example.com/PROJECT/
curl -sS -u "$HARBOR_USER:$HARBOR_PASSWORD" \
  "https://harbor.example.com/service/token?service=harbor-registry&scope=repository:shop/web:pull,push" \
  | python3 -c 'import sys,json,base64; t=json.load(sys.stdin)["token"].split(".")[1]; t+="="*(-len(t)%4); print(json.loads(base64.urlsafe_b64decode(t))["access"])'
```

```
harbor.example.com/shop/web
[{'type': 'repository', 'name': 'shop/web', 'actions': ['pull']}]
```

**What the output tells you:** Harbor's token service accepted the credentials but granted only `pull`, so the robot lacks push permission on project `shop`. An empty `actions` list means no access to that repository at all (wrong project, or a project the robot is not part of). An HTTP 401 from the token call means a wrong or expired secret.

**Fix:**

```bash
# Harbor UI: Projects > shop > Robot Accounts > New: Repository push + pull, expiry per your policy.
# Store name and secret as masked, protected, raw variables (5.5). Then, in the job:
echo "$HARBOR_PASSWORD" | docker login -u "$HARBOR_USER" --password-stdin harbor.example.com
docker push "harbor.example.com/shop/web:$CI_COMMIT_SHORT_SHA"
```

**Why this fix works:** Harbor issues short-lived tokens scoped per repository and action. Decoding the token shows exactly what Harbor granted, which ends the guessing. A full image path sends the push to Harbor, and logging in to the same host string makes Docker send the credentials. Do not "fix" it with an administrator account in CI. A leaked admin credential can delete every project.

**Prevent it:** Use one robot account per project and purpose (CI push, Dokploy pull), with the expiry date recorded in your secrets inventory and a reminder before it, or an alert on `expires_at` from Harbor's robots API.

**Next step:** [Pushing to Harbor in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *Docker Certified Associate*, Docker Image Management, Authenticating to Registries ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · [Harbor docs: robot accounts](https://goharbor.io/docs/1.10/working-with-projects/project-configuration/create-robot-accounts/)

**Community threads:** [forums.docker.com top topics](https://forums.docker.com/top?period=all) · [Harbor docs: create robot accounts](https://goharbor.io/docs/1.10/working-with-projects/project-configuration/create-robot-accounts/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=harbor+%22unauthorized+to+access+repository%22+push+robot) · [Reddit r/docker](https://www.reddit.com/r/docker/search/?q=denied+requested+access+to+the+resource+is+denied+push&restrict_sr=1)

### 7.4 Large pushes die behind the proxy

> **Seen as:** `error parsing HTTP 413 response body: invalid character '<' looking for beginning of value: "<html>...413 Request Entity Too Large..."`, or `unexpected EOF` / HTTP 499 after exactly 60 seconds, or `blob upload unknown` · **Where:** Harbor or the GitLab registry behind nginx, Apache or Traefik (Dokploy's Traefik too) · **Level:** [L2–L3 · Mid → Senior] · **How common:** Harbor issue #22353, a 2025 Traefik forum thread on 499s during large pushes, and GitLab forum threads on registries behind Traefik

**Why it happens:** Registry uploads are long `PATCH` and `PUT` streams of hundreds of megabytes. nginx refuses request bodies over 1 MB by default (`client_max_body_size`) and buffers uploads to disk. Traefik v3 entry points have a default `readTimeout` of 60 seconds, which cuts any upload that takes longer. If Harbor's `external_url` or the forwarded protocol is wrong, upload URLs point to the wrong scheme or host, and the registry no longer recognises the upload session.

**Diagnose:**

```bash
# Traefik JSON access log: status and duration of blob uploads
jq -r 'select(.RequestPath | test("/v2/.*/blobs/uploads")) | "\(.DownstreamStatus) \(.Duration/1e9 | floor)s"' \
  /var/log/traefik/access.log | sort | uniq -c
```

```
     41 202 2s
      3 499 60s
```

**What the output tells you:** Small layers succeed, and the big ones are cut at exactly 60 s with 499 (client closed), which is the Traefik v3 read timeout. A 413 in the nginx access log points at the body size limit instead.

**Fix:**

```yaml
# Traefik v3 static configuration (in Dokploy: /etc/dokploy/traefik/traefik.yml, then restart Traefik)
entryPoints:
  websecure:
    address: ":443"
    transport:
      respondingTimeouts:
        readTimeout: 600s          # 0s disables the limit; v3 default is 60s
```

```nginx
# nginx in front of Harbor or the GitLab registry
client_max_body_size 0;
proxy_request_buffering off;
proxy_read_timeout 900s;
```

**Why this fix works:** The stream is allowed to run as long as it needs, without a size cap or disk buffering in the proxy. Harbor's own internal nginx already uses settings like these, and the outer proxy must match. Raise the limits only on the registry route or entry point, not globally for every app. Keep `external_url` as the public `https://` URL, so redirects stay correct.

**Prevent it:** After any proxy change, push a 1–2 GB test image, and alert on 413 and 499 responses for `/v2/` paths. Traefik details: [module 43](43-traefik-and-reverse-proxies.md).

**Next step:** [Web servers and proxies](29-learn-webservers-proxies.md) · KodeKloud: *Nginx For Beginners* ([course](https://kodekloud.com/courses/nginx-for-beginners)) · [Harbor docs](https://goharbor.io/docs/)

**Community threads:** [Harbor #22353: 413 on push](https://github.com/goharbor/harbor/issues/22353) · [Traefik forum: registry uploads fail with 499 behind v3.6](https://community.traefik.io/t/docker-registry-uploads-fail-with-http-499-errors-when-running-behind-traefik-v3-6-in-docker-swarm-buffering-or-timeout-behavior-during-large-image-pushes/29527) · [Claudio Kuenzler: Harbor behind a reverse proxy](https://www.claudiokuenzler.com/blog/958/running-harbor-registry-behind-reverse-proxy-solve-docker-push-errors) · [GitLab forum: registry behind Traefik](https://forum.gitlab.com/t/troubles-enabling-container-registry-behind-traefik-reverse-proxy/97005) · [Harbor #12135: relative URLs](https://github.com/goharbor/harbor/issues/12135) · Search: [Stack Overflow](https://stackoverflow.com/search?q=docker+push+%22413+Request+Entity+Too+Large%22+nginx+registry) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=docker+push+413+traefik+registry&restrict_sr=1)

---

## 8. Caches, artifacts and runner disk

Runners are cheap until their disks fill, their caches miss and their artifacts disappear. These three entries cover the runner's storage, from "job failed: no space left" to "why is npm slower with the cache than without it".

### 8.1 Runner disk full

> **Seen as:** `ERROR: Job failed (system failure): Error response from daemon: ... no space left on device`, or `failed to register layer: ... no space left on device`; random jobs fail on one runner host · **Where:** Docker-executor runners after a few months · **Level:** [L1–L2 · Junior → Mid] · **How common:** "Clean up old build directories" (186 upvotes) and "Smart cache cleanup for Docker images & volumes" (179) are among the most upvoted GitLab Runner work items

**Why it happens:** The Docker executor creates a cache volume per project and concurrency slot (`runner-...-cache-...`) and never deletes them. Every pipeline leaves a new image layer set, tagged by SHA, plus BuildKit cache. Shell executors keep old build directories under `/home/gitlab-runner/builds`. Nothing expires on its own.

**Diagnose:**

```bash
df -h /var/lib/docker
docker system df
docker volume ls -q --filter name=runner- | wc -l
```

```
Filesystem      Size  Used Avail Use% Mounted on
/dev/sdb1        98G   97G  1.0G  99% /var/lib/docker
TYPE            TOTAL     ACTIVE    SIZE      RECLAIMABLE
Images          412       6         61.2GB    58.9GB (96%)
Containers      9         4         212MB     96.4MB (45%)
Local Volumes   1287      4         29.4GB    29.1GB (98%)
Build Cache     2210      0         4.3GB     4.3GB
1281
```

**What the output tells you:** Almost everything is reclaimable: 59 GB of old images and 1281 runner cache volumes holding 29 GB. This is accumulation, not one runaway job.

**Fix:**

```bash
sudo /usr/share/gitlab-runner/clear-docker-cache       # GitLab's script: removes unused runner containers and cache volumes
docker image prune -af --filter "until=168h"           # images unused for 7 days
docker builder prune -af --filter "until=72h"
# Make it routine: a weekly systemd timer on the RUNNER host only.
```

**Why this fix works:** Runner caches and old images are optimisations, not data, so deleting them only makes the next job slower. The age filters keep the hot set. Never run `docker system prune -a --volumes` on a host that also runs stateful services. On a shared Dokploy host it deletes database volumes. That is one more reason to keep runners on their own VM.

**Prevent it:** Give the runner a dedicated `/var/lib/docker` disk, alert at 80% with node_exporter ([observability](32-learn-performance-observability.md)), run the cleanup timer, and apply Harbor retention so the registry does not fill the same way.

**Next step:** [Storage and disk](01-storage-disk.md) · [Containers playbook](26-playbook-containers-k8s.md) · KodeKloud: *Docker Certified Associate*, Docker Engine – Storage ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · [GitLab Runner docs: Docker executor](https://docs.gitlab.com/runner/executors/docker/)

**Community threads:** [gitlab-runner 3103: clean up old build directories](https://gitlab.com/gitlab-org/gitlab-runner/-/work_items/3103) · [gitlab-runner 27332: smart cache cleanup](https://gitlab.com/gitlab-org/gitlab-runner/-/work_items/27332) · [GitLab Runner docs: clearing the Docker cache](https://docs.gitlab.com/runner/executors/docker/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+runner+%22no+space+left+on+device%22+docker+volumes) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=runner+disk+full+cache+volumes&restrict_sr=1)

### 8.2 Cache never hits or is slow

> **Seen as:** `No URL provided, cache will not be downloaded from shared cache server. Instead a local version of cache will be extracted.` followed by `WARNING: file does not exist`; `Checking cache for feature-cart-non_protected...`; `npm ci` takes the same four minutes every run, or restoring the cache takes longer than downloading · **Where:** several runners, branch-based cache keys, Node.js projects · **Level:** [L2 · Mid] · **How common:** "Caching is very slow for Node.JS projects" has 165 comments on the GitLab Runner tracker

**Why it happens:** Without a distributed cache, each runner host keeps its own local cache, so a job that lands on another host misses. Keys such as `$CI_COMMIT_REF_SLUG` start every new branch cold. GitLab also keeps separate caches for protected and unprotected branches (the `-protected` and `-non_protected` suffixes), so merge request pipelines cannot read `main`'s cache. Paths outside the project directory are not cached at all. Zipping tens of thousands of small files (`node_modules`) can cost more than it saves.

**Diagnose:**

```bash
grep -E 'Running on|Checking cache for|Successfully extracted|file does not exist|Created cache' job-41.log job-42.log
sudo grep -A6 '\[runners.cache\]' /etc/gitlab-runner/config.toml
```

```
job-41.log:Running on runner-t3kd9aq-project-42-concurrent-0 via ci-01...
job-41.log:Created cache
job-42.log:Running on runner-p7xq2mw-project-42-concurrent-1 via ci-02...
job-42.log:Checking cache for feature-cart-non_protected...
job-42.log:WARNING: file does not exist
```

**What the output tells you:** The cache was written to `ci-01`'s local disk, and the next job ran on `ci-02`, which cannot see it. The key is also per branch, so every feature branch starts from nothing.

**Fix:**

```yaml
install:
  variables: { FF_USE_FASTZIP: "true", CACHE_COMPRESSION_LEVEL: "fast" }
  cache:
    key: { files: [package-lock.json] }        # changes only when dependencies change
    paths: [.npm/]
  script: [npm ci --cache .npm --prefer-offline]
# config.toml on every runner: [runners.cache] Type = "s3", Shared = true, pointing at the same MinIO bucket (section 2)
```

**Why this fix works:** A shared S3 or MinIO cache is visible from every runner. A lock-file key is reused across branches until dependencies change. Caching npm's download cache instead of `node_modules` gives fewer, larger files that compress quickly with fastzip. Keep the protected and unprotected separation. It stops merge request code from poisoning the cache that release builds use.

**Prevent it:** Compare the cache restore time with a clean install every quarter. For dependencies, a local proxy registry (Nexus, 13.3, or Harbor's proxy cache for images) is often faster and simpler than CI caches.

**Next step:** [Artifacts vs cache in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, Continuous Integration with GitLab ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** [gitlab-runner 1797: caching very slow for Node.js](https://gitlab.com/gitlab-org/gitlab-runner/-/work_items/1797) · [gitlab-runner 1107: Docker artifact caching](https://gitlab.com/gitlab-org/gitlab-runner/-/work_items/1107) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+ci+cache+not+shared+between+runners) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=cache+not+shared+between+runners&restrict_sr=1)

### 8.3 Artifacts missing, too large or blocked

> **Seen as:** `ERROR: Uploading artifacts as "archive" to coordinator... 413 Request Entity Too Large`, or `WARNING: dist/: no matching files. Ensure that the artifact path is relative to the working directory`, or a later job failing to download artifacts (404 or 403 across projects) · **Where:** builds that pass output to later stages or other projects · **Level:** [L2 · Mid] · **How common:** "Passing Docker image between build and test stage" has about 106k views on the GitLab forum, and cross-project artifacts are another classic

**Why it happens:** Artifacts larger than the **maximum artifacts size** (an instance setting that administrators can override per group or project) are rejected. So is any upload bigger than the body limit of a reverse proxy in front of GitLab. Paths must be relative to the project directory. Expired artifacts are gone. Downloading another project's artifacts with `CI_JOB_TOKEN` requires the source project to allow the caller in its job token allowlist. `needs:project` is a Premium feature, so Community Edition uses the API. Docker images do not belong in artifacts at all.

**Diagnose:**

```bash
grep -E 'Uploading artifacts|matching|ERROR' job.log
curl -sS -H "PRIVATE-TOKEN: $GITLAB_TOKEN" "https://gitlab.example.com/api/v4/projects/PROJECT_ID/jobs/JOB_ID" \
  | jq -c '{artifacts_expire_at, files: [.artifacts[] | {file_type, size}]}'
```

```
dist/: found 18432 matching artifact files and directories
ERROR: Uploading artifacts as "archive" to coordinator... 413 Request Entity Too Large  id=7731 responseStatus=413 Request Entity Too Large status=413
{"artifacts_expire_at":null,"files":[{"file_type":"trace","size":48211}]}
```

**What the output tells you:** The archive (18k files, including source maps) exceeded a size limit, so only the job log (`trace`) was stored and the next stage has nothing to download. Check the GitLab setting first, then any proxy limit in front of GitLab.

**Fix:**

```yaml
build:
  artifacts:
    paths: [dist/]
    exclude: ["dist/**/*.map"]
    expire_in: 1 week
# Images: push to Harbor with the SHA tag and pull it in later stages, never as an artifact.
# Cross-project in CE:  curl --header "JOB-TOKEN: $CI_JOB_TOKEN" -o build.zip \
#   "https://gitlab.example.com/api/v4/projects/SOURCE_ID/jobs/artifacts/main/download?job=build"
#   and add the calling project to SOURCE's CI/CD job token allowlist.
```

**Why this fix works:** A smaller artifact fits the existing limits. Raise the instance limit only deliberately, because it costs storage. `expire_in` keeps artifact storage bounded. The registry is built for images: it deduplicates layers, which artifacts cannot do. The allowlist replaces the old behaviour, where any job token could read any project the user could see.

**Prevent it:** Set `expire_in` in the shared template, keep a size budget per artifact, and review the job token allowlists of release projects.

**Next step:** [Artifacts vs cache in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, Architecture & Core Concepts ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** [GitLab forum: passing a Docker image between stages](https://forum.gitlab.com/t/passing-docker-image-between-build-and-test-stage-in-gitlab-runner/2444) · [GitLab forum: artifacts from another project](https://forum.gitlab.com/t/use-an-artifact-from-a-project-in-a-different-projects-ci/6276) · [gitlab-runner 1057: artifacts root folder](https://gitlab.com/gitlab-org/gitlab-runner/-/work_items/1057) · [gitlab-runner 1664: dynamic artifact names](https://gitlab.com/gitlab-org/gitlab-runner/-/work_items/1664) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+artifacts+%22413+Request+Entity+Too+Large%22) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=artifacts+too+large+413&restrict_sr=1)

---

## 9. Deploying from CI

The last stage is where a green pipeline and a working site part ways: the deploy call "succeeds" but nothing changes, the pipeline cannot tag its own release, SSH refuses the key, or two deploys overwrite each other. The Dokploy side of these problems is in [module 45](45-dokploy-and-self-hosted-paas.md). The rollout strategies are in [Deployment patterns](35-deployment-patterns.md).

### 9.1 Dokploy deploy succeeds but nothing changes

> **Seen as:** the deploy job is green, but `https://shop.example.com/version` still reports the old SHA; or every domain of the app returns `404 page not found` right after the deploy; or `docker service ps` shows `No such image: harbor.example.com/shop/web:9d8c7b6a` · **Where:** GitLab CI → Harbor → Dokploy (API or webhook) · **Level:** [L2–L3 · Mid → Senior] · **How common:** Dokploy issue #5453 (labels dropped on redeploy) and recurring Dokploy questions about webhook deploys

**Why it happens:** `curl` without `-f` exits 0 even when Dokploy answers 401 or 404, so a wrong API key or application ID still gives a green job. The deploy endpoint only queues the deploy and returns before the rollout. A reused tag such as `latest` may never be pulled again. Swarm pulls on whichever node runs the task, and if that node lacks Harbor credentials or the private CA, the new task is rejected while the old one keeps serving. Separately, Dokploy issue #5453 describes deploys that drop the service's `traefik.*` labels, which turns every domain into a 404.

**Diagnose:**

```bash
curl -sS -o /dev/null -w '%{http_code}\n' -X POST "$DOKPLOY_URL/api/application.deploy" \
  -H "x-api-key: $DOKPLOY_TOKEN" -H "Content-Type: application/json" -d "{\"applicationId\":\"$DOKPLOY_APP_ID\"}"
docker service ps shop-web-x1y2z3 --format '{{.Image}} {{.CurrentState}} {{.Error}}' | head -2      # on the Dokploy host
docker service inspect shop-web-x1y2z3 --format '{{json .Spec.Labels}}' | jq '[keys[] | select(startswith("traefik"))] | length'
```

```
200
harbor.example.com/shop/web:9d8c7b6a Rejected 40 seconds ago No such image: harbor.example.com/shop/web:9d8c7b6a
harbor.example.com/shop/web:5e4f3a2b Running 3 days ago
6
```

**What the output tells you:** Dokploy accepted the call, but the node could not pull the new tag, so Swarm kept the old task running. That is why the site still shows the old version. The six Traefik labels are present, so this is not #5453. A count of `0` would explain a 404 instead. On the node, `docker pull` of the same tag will show whether the cause is the CA (`x509`) or the credentials (`unauthorized`).

**Fix:**

```bash
# CI: fail on HTTP errors and deploy an immutable SHA tag (module 33 shows the full job with a /version check)
curl -fsS -X POST "$DOKPLOY_URL/api/application.deploy" -H "x-api-key: $DOKPLOY_TOKEN" \
  -H "Content-Type: application/json" -d "{\"applicationId\":\"$DOKPLOY_APP_ID\"}"
# Every Swarm node that can run the app: trust the CA and prove it can pull
sudo install -D -m 644 corp-root-ca.crt /etc/docker/certs.d/harbor.example.com/ca.crt
docker pull harbor.example.com/shop/web:9d8c7b6a
# Dokploy UI: add Harbor as a registry (pull-only robot) and select it on the application.
# Labels gone (#5453): docker service update --rollback SERVICE, then redeploy from the UI and pin the Dokploy version.
```

**Why this fix works:** `-f` turns HTTP errors into a failed job. The registry setting makes Dokploy pass credentials to the nodes, and the CA in `certs.d` makes the pull trusted. A verification loop on `/version` turns "deploy requested" into "deploy proven". The `--rollback` restores the labels, but also the previous image, so treat it as a stopgap until a fixed Dokploy version is out.

**Prevent it:** Make post-deploy verification part of the pipeline, run a synthetic check on `/version` (Uptime Kuma or blackbox_exporter), and read Dokploy release notes before upgrading.

**Next step:** [Apache and Dokploy case](21-case-apache-443-dokploy.md) · [Site-down playbook](25-playbook-site-down.md) · KodeKloud: *Docker Certified Associate*, Docker Swarm, Swarm Services ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · [Dokploy docs: domains troubleshooting](https://docs.dokploy.com/docs/core/troubleshooting/domains)

**Community threads:** [Dokploy #5453: deploy drops Traefik labels](https://github.com/Dokploy/dokploy/issues/5453) · [Dokploy release v0.30.0](https://github.com/Dokploy/dokploy/releases/tag/v0.30.0) · [Dokploy docs: troubleshooting domains and Traefik](https://docs.dokploy.com/docs/core/troubleshooting/domains) · Search: [GitHub Dokploy issues](https://github.com/Dokploy/dokploy/issues?q=webhook+deploy+gitlab) · [Stack Overflow](https://stackoverflow.com/search?q=docker+swarm+service+%22No+such+image%22+private+registry) · [Reddit r/selfhosted](https://www.reddit.com/r/selfhosted/search/?q=dokploy+gitlab+ci+deploy&restrict_sr=1)

### 9.2 CI can't push back to the repository

> **Seen as:** `remote: You are not allowed to push code to this project.` with `The requested URL returned error: 403`, or `error: src refspec main does not match any` · **Where:** release jobs that create tags, changelogs or version bumps · **Level:** [L2 · Mid] · **How common:** about 150k views on the GitLab forum thread "Git push from inside a gitlab-runner"; "allow runners to push via their CI token" has 326 upvotes

**Why it happens:** The job clones with `CI_JOB_TOKEN`, which has traditionally been read-only for Git. Newer GitLab versions add an opt-in project setting for job-token pushes, so check your version's docs before relying on it. The runner checks out a **detached HEAD** at the commit SHA, so no local `main` branch exists to push. The default shallow clone (`GIT_DEPTH` 20) lacks older tags. A successful push-back starts another pipeline, which can loop.

**Diagnose:**

```bash
git rev-parse --abbrev-ref HEAD; git rev-parse --is-shallow-repository
git remote get-url origin | sed 's#//[^@]*@#//***@#'
```

```
HEAD
true
https://***@gitlab.example.com/shop/web.git
```

**What the output tells you:** Detached HEAD (`HEAD`, not a branch name), a shallow clone, and an origin that uses the job token. All three must be handled.

**Fix:**

```yaml
release-tag:
  variables: { GIT_DEPTH: "0" }
  rules: [{ if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH }]
  script:
    - git config user.email "ci-bot@example.com"; git config user.name "ci-bot"
    - git tag "v$VERSION" "$CI_COMMIT_SHA"
    - git push "https://ci-bot:${RELEASE_TOKEN}@gitlab.example.com/${CI_PROJECT_PATH}.git" "v$VERSION" -o ci.skip
```

**Why this fix works:** `RELEASE_TOKEN` is a **project access token** (a bot user) with `write_repository` and the role your branch or tag protection requires, stored masked and protected. Pushing a tag at an explicit SHA avoids the detached-HEAD problem. To push a commit, use `git push ... HEAD:refs/heads/$CI_COMMIT_BRANCH`. `-o ci.skip` prevents the pipeline loop. Do not use an engineer's personal token: it breaks when they leave and gives the pipeline their access.

**Prevent it:** Prefer Git tags and SHA-tagged images over committing from CI. Project access tokens expire, so track the date.

**Next step:** [Git in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *GIT for Beginners*, Initialize Remote Repositories ([course](https://kodekloud.com/courses/git-for-beginners)) · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** [GitLab forum: git push from inside a gitlab-runner](https://forum.gitlab.com/t/git-push-from-inside-a-gitlab-runner/30554) · [gitlab-runner 4421: push via the CI token](https://gitlab.com/gitlab-org/gitlab-runner/-/work_items/4421) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+ci+git+push+%22You+are+not+allowed+to+push+code+to+this+project%22) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=push+from+ci+job+token&restrict_sr=1)

### 9.3 SSH deploy fails from the job

> **Seen as:** `Host key verification failed.`, or `Load key "/builds/shop/web.tmp/SSH_PRIVATE_KEY": error in libcrypto`, or `deploy@192.0.2.20: Permission denied (publickey).` · **Where:** jobs that ssh to a VM for rsync, Ansible or `docker compose` (Jenkins too) · **Level:** [L1 · Junior] · **How common:** about 802k views on the GitLab forum's "Permission Denied (publickey)" and about 36k on Jenkins' "Host key verification failed"

**Why it happens:** A fresh job container has an empty `known_hosts`, so strict checking refuses the unknown server. A private key pasted into a normal variable often loses its final newline or gains Windows line endings, and OpenSSL then cannot parse it (`error in libcrypto`). `Permission denied (publickey)` means the key was read and offered, but the server did not accept it: wrong user, key missing from `authorized_keys`, or bad permissions on the server's `~/.ssh`.

**Diagnose:**

```bash
ssh-keygen -lf "$SSH_PRIVATE_KEY"                     # can the key be parsed at all?
ssh -vvv -o BatchMode=yes deploy@192.0.2.20 true 2>&1 | grep -E 'Offering|can continue|denied|Host key'
```

```
256 SHA256:4mF0c2Qk9oZr1V0bS3hT2yXw8pLm1nB7aD6eF5gH4iJ deploy-ci (ED25519)
debug1: Offering public key: /builds/shop/web.tmp/SSH_PRIVATE_KEY ED25519 SHA256:4mF0c2Qk... explicit
debug1: Authentications that can continue: publickey
deploy@192.0.2.20: Permission denied (publickey).
```

**What the output tells you:** The key parses and is offered, so the job side is fine. The server rejects it, so look at the server: `sudo tail /var/log/auth.log` usually shows `Authentication refused: bad ownership or modes` or no matching key for user `deploy`. If `ssh-keygen` had failed, fix the variable. If you saw `Host key verification failed`, fix `known_hosts`.

**Fix:**

```yaml
deploy:
  before_script:
    - apk add --no-cache openssh-client
    - eval "$(ssh-agent -s)" && chmod 400 "$SSH_PRIVATE_KEY" && ssh-add "$SSH_PRIVATE_KEY"   # File-type variable
    - install -m 700 -d ~/.ssh && cp "$SSH_KNOWN_HOSTS" ~/.ssh/known_hosts                   # File-type variable
  script:
    - ssh deploy@192.0.2.20 'cd /opt/shop && docker compose pull && docker compose up -d'
```

**Why this fix works:** File-type variables keep the exact bytes, including the final newline, and never print the content. A `known_hosts` file captured once from a trusted network, with the fingerprints compared to the server's own, keeps host checking on. `StrictHostKeyChecking=no` would accept any impostor. On the server, `chmod 700 ~/.ssh` and `chmod 600 ~/.ssh/authorized_keys`, owned by `deploy`.

**Prevent it:** Restrict the deploy key in `authorized_keys` with `from="10.20.0.21"` and, where possible, a forced `command=`. Rotate it on a schedule, and move repeated SSH deploys to Ansible ([module 33](33-learn-cicd-iac-sre.md)).

**Next step:** [SSH and remote access](09-ssh-remote-access.md) · KodeKloud: *Prep Course - Linux Foundation Certified System Administrator (LFCS)* ([course](https://kodekloud.com/courses/linux-foundation-certified-system-administrator-lfcs)) · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** [GitLab forum: Permission Denied (publickey)](https://forum.gitlab.com/t/permission-denied-publickey/29670) · [Jenkins community: Host key verification failed](https://community.jenkins.io/t/git-stderr-host-key-verification-failed/4534) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+ci+ssh+%22error+in+libcrypto%22) · [Reddit r/gitlab](https://www.reddit.com/r/gitlab/search/?q=ssh+deploy+host+key+verification+failed&restrict_sr=1)

### 9.4 Two deploys race and the older wins

> **Seen as:** production runs an older SHA after two quick merges, and the deployment list shows the older pipeline's deploy finishing last · **Where:** long pipelines, manual retries of old deploy jobs, mutable tags · **Level:** [L3 · Senior] · **How common:** a classic release-engineering failure; GitLab has dedicated features for it

**Why it happens:** Two pipelines run in parallel. The older one has a slower build, so its deploy job finishes after the newer one and overwrites production with older code. The same happens when someone clicks "retry" on last week's deploy job. With a mutable `latest` tag you cannot even see that it happened.

**Diagnose:**

```bash
curl -sS -H "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.example.com/api/v4/projects/PROJECT_ID/deployments?environment=production&order_by=id&sort=desc&per_page=2" \
  | jq -r '.[] | "id=\(.id) sha=\(.sha[0:8]) pipeline=\(.deployable.pipeline.id) finished=\(.deployable.finished_at)"'
```

```
id=911 sha=8b7e6d5c pipeline=1843 finished=2026-09-30T10:41:05Z
id=910 sha=3f2a9c1d pipeline=1842 finished=2026-09-30T10:42:17Z
```

**What the output tells you:** Deployment 910 belongs to the older pipeline, 1842, but finished 72 seconds after the newer one. Production runs `3f2a9c1d`, the older commit, even though the newest deployment record says `8b7e6d5c`.

**Fix:**

```yaml
build:
  interruptible: true                   # a newer pipeline may cancel this one
deploy-production:
  resource_group: production            # one deploy at a time
  environment: { name: production, url: "https://shop.example.com" }
# Settings > CI/CD > General pipelines: "Auto-cancel redundant pipelines" and "Prevent outdated deployment jobs"
```

**Why this fix works:** `resource_group` serialises deploys to the same environment. "Prevent outdated deployment jobs" refuses to run a deploy job older than the last successful deployment, which also covers manual retries. Auto-cancel stops obsolete pipelines early. With immutable SHA tags, a rollback means re-running the deploy of the last good pipeline, on purpose and visibly. Argo CD has its own version of this problem (12.5).

**Prevent it:** After every deploy, compare the running version (`/version`) with `CI_COMMIT_SHA` and alert on a mismatch. Use deploy freeze windows for risky periods.

**Next step:** [Deployment patterns](35-deployment-patterns.md) · [Environments and manual approvals in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, Continuous Deployment ([course](https://kodekloud.com/courses/gitlab-ci-cd))

**Community threads:** [GitLab docs](https://docs.gitlab.com/) (resource_group, deployment safety) · Search: [Stack Overflow](https://stackoverflow.com/search?q=gitlab+resource_group+deploy+older+pipeline) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=older+pipeline+deployed+over+newer&restrict_sr=1)

---

## 10. Jenkins: controller, agents and plugins

Jenkins is a Java server with a plugin for everything, and that is both its strength and its pain. The problems below are the most-viewed topics on community.jenkins.io: install and start failures, plugin upgrades, proxies, overloaded controllers, agents and Git. Most of them disappear once the controller is built from code (10.7).

### 10.1 Jenkins won't install or start

> **Seen as:** `NO_PUBKEY 7198F4B714ABFC68` (the 2026 key; `5BA31D57EF5975CA` was the 2023 one) on `apt update`; `Running with Java 17 from /usr/lib/jvm/java-17-openjdk-amd64, which is older than the minimum required version (Java 21). Supported Java versions are: [21, 25]`; `jenkins.service: start operation timed out. Terminating.`; `java.net.BindException: Address already in use` · **Where:** Ubuntu package installs after an upgrade · **Level:** [L1–L2 · Junior → Mid] · **How common:** the startup-timeout, failed-to-start and signing-key topics each have 12–47k views on community.jenkins.io

**Why it happens:** Jenkins rotates its apt signing key every few years: in 2023, and again for weekly 2.543 and LTS 2.541.1 (`jenkins.io-2026.key`, from December 2025 and January 2026). Old keyrings then stop verifying. The Java baseline keeps rising: weekly 2.545 and LTS 2.555.1 (April 2026) require Java 21 or 25, and LTS 2.541.x was the last line that ran on Java 17. An unattended `apt upgrade` can install the new Jenkins on the old Java. A controller with many plugins can start more slowly than the systemd timeout allows. Port 8080 is a popular default, also used by Traefik's dashboard and many other apps.

**Diagnose:**

```bash
sudo journalctl -u jenkins -n 30 --no-pager | grep -E 'older than|BindException|timed out'
java -version 2>&1 | head -1; sudo ss -ltnp 'sport = :8080'
```

```
Running with Java 17 from /usr/lib/jvm/java-17-openjdk-amd64, which is older than the minimum required version (Java 21). Supported Java versions are: [21, 25]
openjdk version "17.0.16" 2025-07-15
LISTEN 0 4096 0.0.0.0:8080 0.0.0.0:* users:(("docker-proxy",pid=1874,fd=4))
```

**What the output tells you:** Two separate faults. apt upgraded Jenkins past the Java 17 line, and a container already publishes port 8080, so after fixing Java the next start would fail with `BindException`.

**Fix:**

```bash
sudo apt-get install -y fontconfig openjdk-21-jre-headless
sudo update-alternatives --config java              # select Java 21
sudo systemctl edit jenkins                         # add: [Service]  Environment="JENKINS_PORT=8081"  TimeoutStartSec=300
sudo systemctl restart jenkins && sudo apt-mark hold jenkins
# NO_PUBKEY: fetch the key named on the current Jenkins Linux install page (jenkins.io-2026.key as of 2026)
#   into the keyring file your jenkins.list "signed-by=" points at, then apt update
```

**Why this fix works:** Jenkins refuses to start on an unsupported Java, so installing the required version is the actual fix. A systemd override (`systemctl edit`) survives package upgrades, unlike edits to the shipped unit file. Holding the package turns upgrades into planned changes. Do not mark the repository `[trusted=yes]` to get around a key error: that disables package signature checking.

**Prevent it:** Read the LTS upgrade guide before each upgrade, upgrade a staging controller first, and keep Jenkins behind Traefik on a hostname instead of publishing 8080.

**Next step:** [Services and systemd](07-services-systemd.md) · [Packages](11-packages.md) · KodeKloud: *Certified Jenkins Engineer* ([course](https://kodekloud.com/courses/certified-jenkins-engineer)) · [Jenkins docs: Java support policy](https://www.jenkins.io/doc/book/platform-information/support-policy-java/)

**Community threads:** [Jenkins community: new repository signing keys](https://community.jenkins.io/t/new-linux-repository-signing-keys-for-jenkins-2-397-and-2-387-2/6509) · [failed to start Jenkins](https://community.jenkins.io/t/failed-to-start-jenkins-continuous-integration-server/8223) · [startup times out](https://community.jenkins.io/t/my-jenkins-startup-times-out-it-appears-to-work-but-the-start-command-times-out-on-the-shell-prompt/1038) · [Java 11 install fails to start](https://community.jenkins.io/t/newly-installed-jenkins-2-387-with-java-11-jenkins-service-failed-to-start/7357) · Search: [Stack Overflow](https://stackoverflow.com/search?q=jenkins+%22older+than+the+minimum+required+version%22+java) · [Reddit r/jenkinsci](https://www.reddit.com/r/jenkinsci/search/?q=jenkins+wont+start+after+upgrade+java&restrict_sr=1)

### 10.2 A plugin update breaks jobs or login

> **Seen as:** after "Update all": `Failed Loading plugin Matrix Authorization Strategy Plugin ...`, a login page that throws `CannotResolveClassException: hudson.security.GlobalMatrixAuthorizationStrategy`, or jobs missing from the dashboard · **Where:** long-lived controllers with dozens of plugins · **Level:** [L2 · Mid] · **How common:** three top community.jenkins.io topics (lockout, jobs not loading, "post upgrade issue") with about 16–21k views each

**Why it happens:** Plugins depend on each other and on a minimum Jenkins core version. Updating some plugins without their dependencies, or installing a plugin that needs a newer core, makes it fail to load at startup. When the failing plugin provides the authorization strategy or security realm, Jenkins cannot read its own security configuration, and nobody can log in. Jobs whose configuration uses a class from a failed plugin are not loaded.

**Diagnose:**

```bash
sudo journalctl -u jenkins --since "1 hour ago" --no-pager | grep -E 'Failed Loading plugin|or higher required' | head -3
ls -lt /var/lib/jenkins/plugins/*.bak | head -3
```

```
SEVERE jenkins.InitReactorRunner$1#onTaskFailed: Failed Loading plugin Matrix Authorization Strategy Plugin v3.2.6 (matrix-auth)
java.io.IOException: Failed to load: Matrix Authorization Strategy Plugin (matrix-auth 3.2.6) - Jenkins (2.479.3) or higher required
-rw-r--r-- 1 jenkins jenkins 312144 Sep 30 21:04 /var/lib/jenkins/plugins/matrix-auth.bak
```

**What the output tells you:** The new `matrix-auth` needs a newer Jenkins core than the one installed. It failed to load, which explains the lockout. The plugin manager kept the previous version as `matrix-auth.bak`.

**Fix:**

```bash
sudo systemctl stop jenkins
cd /var/lib/jenkins/plugins && sudo -u jenkins mv matrix-auth.jpi matrix-auth.jpi.broken && sudo -u jenkins cp matrix-auth.bak matrix-auth.jpi
sudo systemctl start jenkins
# Then: upgrade the core first, then the plugins, from a tested plugins.txt (10.7). Disable a plugin with an empty NAME.jpi.disabled file.
```

**Why this fix works:** The previous plugin version matches the installed core, so the security configuration loads again. Core first, then plugins, is the order the dependency rules expect. Turning off security in `config.xml` is a last resort, only on an isolated controller, and it must be reverted at once, because it leaves Jenkins open to anyone who can reach it.

**Prevent it:** Keep a pinned `plugins.txt`, test updates on a staging controller (`jenkins-plugin-cli --plugin-file plugins.txt --available-updates`), back up `JENKINS_HOME` before upgrading, and remove plugins nobody uses.

**Next step:** KodeKloud: *Certified Jenkins Engineer* ([course](https://kodekloud.com/courses/certified-jenkins-engineer)) · [Jenkins docs](https://www.jenkins.io/doc/) · entry 10.7 here

**Community threads:** [Jenkins community: cannot resolve GlobalMatrixAuthorizationStrategy](https://community.jenkins.io/t/cannot-resolve-class-exception-hudson-security-global-matrix-authorization-strategy/4218) · [jobs can't be loaded after a plugin update](https://community.jenkins.io/t/why-my-jenkins-jobs-cant-be-loaded-after-updated-new-version-plugin/10341) · [post-upgrade issue](https://community.jenkins.io/t/jenkins-post-upgrade-issue/5866) · Search: [Stack Overflow](https://stackoverflow.com/search?q=jenkins+%22Failed+Loading+plugin%22+%22or+higher+required%22) · [Reddit r/jenkinsci](https://www.reddit.com/r/jenkinsci/search/?q=plugin+update+broke+jenkins&restrict_sr=1)

### 10.3 No valid crumb or 403 behind a proxy

> **Seen as:** `HTTP ERROR 403 No valid crumb was included in the request` when saving settings or triggering builds, plus the admin warning `It appears that your reverse proxy set up is broken.` · **Where:** Jenkins behind nginx, Apache or Traefik, and scripts calling its API · **Level:** [L2 · Mid] · **How common:** three community.jenkins.io topics on crumbs and 403s, with about 23–29k views each

**Why it happens:** Jenkins protects forms against CSRF with a crumb tied to your web session. If the proxy does not pass `Host` and `X-Forwarded-Proto`/`X-Forwarded-Port`, Jenkins builds URLs and cookies for `http://...:8080` while the browser uses `https://`, so sessions and crumbs stop matching. A wrong Jenkins URL setting, or several controllers behind a load balancer without sticky sessions, cause the same failure. Scripts that log in with a password must fetch a crumb. Scripts that use an API token are exempt.

**Diagnose:**

```bash
curl -s -u ops:API_TOKEN 'https://jenkins.example.com/api/json?tree=url' | jq -r .url   # the root URL Jenkins uses
curl -s -u ops:API_TOKEN https://jenkins.example.com/crumbIssuer/api/json | jq -r .crumbRequestField
```

```
http://jenkins.example.com:8080/
Jenkins-Crumb
```

**What the output tells you:** Jenkins builds its links for `http://...:8080`, so it does not know it is served over HTTPS on 443: either the Jenkins URL setting is wrong, or it is empty and the proxy does not send the forwarded headers. (An anonymous `curl -I` of the home page is no help here: Jenkins answers it with a 403 page that redirects in HTML, not with a `Location` header.) The API token call works, which confirms the problem is on the browser and proxy path, not in Jenkins security itself.

**Fix:**

```nginx
location / {
  proxy_pass         http://127.0.0.1:8080;
  proxy_set_header   Host              $host;
  proxy_set_header   X-Forwarded-Proto $scheme;
  proxy_set_header   X-Forwarded-Port  $server_port;
  proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
}
# and set the Jenkins URL to https://jenkins.example.com/ (UI or JCasC unclassified.location.url)
```

**Why this fix works:** With the forwarded headers and the correct Jenkins URL, Jenkins generates `https` URLs and secure cookies that the browser sends back, so crumbs validate again. Traefik passes the `X-Forwarded-*` headers by default, so with Traefik the usual culprit is the Jenkins URL setting. Use API tokens for automation. Do not disable CSRF protection: the system property for that exists only as an emergency escape hatch.

**Prevent it:** Add "login, save a setting, trigger a build through the proxy" to the upgrade checklist, and watch the admin monitors after each proxy change.

**Next step:** [Web servers and proxies](29-learn-webservers-proxies.md) · [Traefik module 43](43-traefik-and-reverse-proxies.md) · KodeKloud: *Nginx For Beginners* ([course](https://kodekloud.com/courses/nginx-for-beginners))

**Community threads:** [Jenkins community: no valid crumb after plugin installation](https://community.jenkins.io/t/no-valid-crumb-error-after-plug-in-installation/3348) · [how to fix invalid crumb warnings](https://community.jenkins.io/t/how-to-fix-invalid-crumb-warnings/121) · [HTTP 403 Forbidden](https://community.jenkins.io/t/jenkins-http-status-403-forbidden-error/3214) · Search: [Stack Overflow](https://stackoverflow.com/search?q=jenkins+%22No+valid+crumb+was+included+in+the+request%22+nginx) · [Reddit r/jenkinsci](https://www.reddit.com/r/jenkinsci/search/?q=no+valid+crumb+reverse+proxy&restrict_sr=1)

### 10.4 Builds run on the controller and fill it

> **Seen as:** `Disk space is below threshold of 1.00 GiB. Only 812.34 MiB out of 49.12 GiB left on /var/lib/jenkins.` with the built-in node taken offline; a slow controller with Java heap errors; builds appearing on the built-in node · **Where:** small single-VM Jenkins installations · **Level:** [L2–L3 · Mid → Senior] · **How common:** disk threshold (about 16k views), builds on the built-in node, and "too much RAM" topics on community.jenkins.io

**Why it happens:** The controller is meant to schedule work, but older installs give the built-in node executors, so builds, their workspaces and their Docker images land on the controller's disk. Without a build discarder, every build's logs and artifacts are kept forever. The JVM's default heap is sized from total RAM, which competes with the builds on the same host.

**Diagnose:**

```bash
sudo du -sh /var/lib/jenkins/{jobs,workspace} 2>/dev/null
sudo find /var/lib/jenkins/jobs -maxdepth 5 -type d -name builds -exec du -s {} + | sort -n | tail -1
```

```
31G	/var/lib/jenkins/jobs
14G	/var/lib/jenkins/workspace
8123412	/var/lib/jenkins/jobs/shop-web/branches/main/builds
```

**What the output tells you:** 14 GB of workspaces means builds run on the controller, and 31 GB of build history means nothing is discarded. One branch alone holds 8 GB of old builds and artifacts.

**Fix:**

```groovy
pipeline {
  agent { label 'linux-docker' }                                   // never the built-in node
  options { buildDiscarder(logRotator(numToKeepStr: '30', artifactNumToKeepStr: '5')) }
  stages { stage('Build') { steps { sh 'make build' } } }
  post { always { cleanWs() } }                                     // Workspace Cleanup plugin
}
```

**Why this fix works:** With `numExecutors: 0` on the built-in node (JCasC, section 2) and an agent label in every pipeline, build load moves to agents you can rebuild at will. The discarder bounds history, and `cleanWs()` frees workspaces after each build. Set the heap explicitly (`-Xmx` in `JAVA_OPTS`) so the controller does not compete with the OS for memory.

**Prevent it:** Alert on `JENKINS_HOME` disk usage, put the discarder in a shared library default, and review the largest jobs monthly.

**Next step:** [Storage and disk](01-storage-disk.md) · [Memory](04-memory.md) · KodeKloud: *Certified Jenkins Engineer* ([course](https://kodekloud.com/courses/certified-jenkins-engineer))

**Community threads:** [Jenkins community: disk space below threshold](https://community.jenkins.io/t/disk-space-below-threshold/11942) · [builds appearing on the built-in node](https://community.jenkins.io/t/why-are-builds-appearing-on-built-in-node-but-its-not-using-the-executors-assigned-causing-high-memory-issue/9666) · [too much RAM on a small environment](https://community.jenkins.io/t/jenkins-on-small-environment-taking-too-much-ram-too-much-processes/3975) · Search: [Stack Overflow](https://stackoverflow.com/search?q=jenkins+%22Disk+space+is+below+threshold%22) · [Reddit r/jenkinsci](https://www.reddit.com/r/jenkinsci/search/?q=built-in+node+executors+disk+full&restrict_sr=1)

### 10.5 Agents keep disconnecting

> **Seen as:** `java.nio.channels.ClosedChannelException`, `ChannelClosedException: ... Remote call on agent-01 failed. The channel is closing down or has closed down`, or for inbound agents `provided port:50000 is not reachable on host jenkins.example.com` · **Where:** SSH or inbound agents on VMs and containers · **Level:** [L2–L3 · Mid → Senior] · **How common:** about 25k views each on the ClosedChannelException and "agents on Java 17" topics, plus about 19k on "FATAL: command execution failed"

**Why it happens:** The agent's JVM gets killed by the kernel's OOM killer when a build eats the agent's RAM. Firewalls and NAT devices drop idle TCP connections. After a controller upgrade, agents must also run a supported Java version, or they fail to reconnect. Inbound (JNLP) agents connect on TCP 50000 by default, which an HTTP reverse proxy does not carry.

**Diagnose:**

```bash
sudo dmesg -T | grep -iE 'killed process' | tail -1           # on the agent
java -version 2>&1 | head -1; nc -vz jenkins.example.com 50000
```

```
[Thu Oct  1 03:12:09 2026] Out of memory: Killed process 22841 (java) total-vm:6123456kB, anon-rss:3901234kB
openjdk version "17.0.16" 2025-07-15
nc: connect to jenkins.example.com (10.20.0.50) port 50000 (tcp) failed: Connection refused
```

**What the output tells you:** Three faults at once on this agent. The OOM killer took the agent JVM during a build. It still runs Java 17, which the upgraded controller no longer supports. And the inbound port is not reachable through the proxy.

**Fix:**

```bash
sudo apt-get install -y openjdk-21-jre-headless      # agents follow the controller's Java baseline
# Inbound agent over WebSocket through the HTTPS proxy: no TCP 50000 needed
java -jar agent.jar -url https://jenkins.example.com/ -name agent-01 \
  -secret @/etc/jenkins-agent/secret -webSocket -workDir /var/lib/jenkins-agent
```

**Why this fix works:** WebSocket agents use the same HTTPS path as the UI, so the proxy and firewall rules you already have apply. Giving the agent its own memory budget (fewer executors per agent, or more RAM) stops the OOM kills, and a matching Java version lets the remoting channel come back after upgrades. For on-prem VMs, SSH agents, where the controller connects to port 22, are often the simplest choice.

**Prevent it:** Treat agents as cattle (VM templates or containers), monitor node availability, and set agent memory limits that leave headroom for the JVM.

**Next step:** [Memory](04-memory.md) · KodeKloud: *Certified Jenkins Engineer* ([course](https://kodekloud.com/courses/certified-jenkins-engineer)) · [Jenkins docs](https://www.jenkins.io/doc/)

**Community threads:** [Jenkins community: agent does not stay connected](https://community.jenkins.io/t/agent-does-not-stay-connected-java-nio-channels-closedchannelexception/1634) · [upgrading agents to Java 17](https://community.jenkins.io/t/how-to-upgrade-agents-to-java-17-but-keep-java-version-for-builds-at-java-8-11/2824) · [FATAL: command execution failed](https://community.jenkins.io/t/jenkins-issue-fatal-command-execution-failed/12460) · Search: [Stack Overflow](https://stackoverflow.com/search?q=jenkins+agent+ClosedChannelException+disconnect) · [Reddit r/jenkinsci](https://www.reddit.com/r/jenkinsci/search/?q=agent+keeps+disconnecting&restrict_sr=1)

### 10.6 Git checkout fails in Jenkins

> **Seen as:** `stderr: Host key verification failed. fatal: Could not read from remote repository.`, `No ED25519 host key is known for gitlab.example.com and you have requested strict checking.`, or `Command "git ls-remote -h -- git@gitlab.example.com:shop/web.git HEAD" returned status code 128` · **Where:** pipelines that check out over SSH, after a Git plugin upgrade or a GitLab reinstall · **Level:** [L1 · Junior] · **How common:** about 36k views on "Host key verification failed" and about 17k on "failed to connect after upgrade to 2.332.1"

**Why it happens:** The Git client plugin verifies SSH host keys using the "Git Host Key Verification Configuration" setting, which defaults to the `known_hosts` file of the user running Git. That user is the `jenkins` user on the controller **and** on each agent. A fresh agent has no entry, and a reinstalled GitLab presents new host keys. Using a username and password credential for an SSH URL, or an HTTPS URL with a private CA, fails in similar ways.

**Diagnose:**

```bash
sudo -u jenkins ssh -T git@gitlab.example.com                 # on the controller or agent that runs the checkout
sudo -u jenkins ssh-keygen -F gitlab.example.com || echo "no known_hosts entry"
```

```
No ED25519 host key is known for gitlab.example.com and you have requested strict checking.
Host key verification failed.
no known_hosts entry
```

**What the output tells you:** The `jenkins` user has never trusted GitLab's host key, so strict checking stops the connection before authentication. Credentials are not the problem yet.

**Fix:**

```yaml
# JCasC: pin GitLab's host keys for every node (fingerprints checked against GitLab's own instance config page)
security:
  gitHostKeyVerificationConfiguration:
    sshHostKeyVerificationStrategy:
      manuallyProvidedKeyVerificationStrategy:
        approvedHostKeys: |-
          gitlab.example.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExampleKeyOnlyForDocs
```

**Why this fix works:** Manually provided keys apply on the controller and on all agents, survive agent rebuilds, and keep verification on. Use an "SSH Username with private key" credential for SSH URLs. For HTTPS with the private CA, add the CA to the agent's OS and Java trust stores. Do not pick "No verification": it accepts any server that answers as `gitlab.example.com`.

**Prevent it:** Keep host keys in JCasC next to the credentials definitions, and update them deliberately when GitLab is rebuilt.

**Next step:** [SSH and remote access](09-ssh-remote-access.md) · KodeKloud: *Certified Jenkins Engineer* ([course](https://kodekloud.com/courses/certified-jenkins-engineer)) · [JCasC docs](https://www.jenkins.io/doc/book/managing/casc/)

**Community threads:** [Jenkins community: Git host key verification failed](https://community.jenkins.io/t/git-stderr-host-key-verification-failed/4534) · [failed to connect after upgrade to 2.332.1](https://community.jenkins.io/t/failed-to-connect-to-git-repository-after-upgrade-to-jenkins-2-332-1-with-git-source-code-management/1986) · [not able to connect to the git repository](https://community.jenkins.io/t/jenkins-not-able-to-connect-to-git-repository/8707) · [timeout connecting to GitHub](https://community.jenkins.io/t/timeout-connecting-to-github/2007) · Search: [Stack Overflow](https://stackoverflow.com/search?q=jenkins+%22Host+key+verification+failed%22+git) · [Reddit r/jenkinsci](https://www.reddit.com/r/jenkinsci/search/?q=host+key+verification+failed+git&restrict_sr=1)

### 10.7 Jenkins configuration drifts: rebuild with JCasC

> **Seen as:** nobody knows how the controller was configured; a restore turns into guesswork; or at startup `ConfiguratorException: Invalid configuration elements for type: class jenkins.model.Jenkins : numExecutor.` · **Where:** long-lived controllers configured by hand, and teams adopting JCasC · **Level:** [L3 · Senior] · **How common:** "Migrating Jenkins" (about 15k views) is a top community.jenkins.io topic, and JCasC is the standard answer

**Why it happens:** Configuration made in the UI lives only in XML files under `JENKINS_HOME`, mixed with build history, so it cannot be reviewed or rebuilt. JCasC fixes that, but its YAML keys come from plugin data models, which change between plugin versions. Typos are rejected at startup, and any UI edit is overwritten when the YAML is applied again.

**Diagnose:**

```bash
docker logs jenkins 2>&1 | grep -A1 'ConfiguratorException' | head -2
grep -n 'numExecutor' casc/jenkins.yaml
```

```
io.jenkins.plugins.casc.ConfiguratorException: Invalid configuration elements for type: class jenkins.model.Jenkins : numExecutor.
Available attributes : authorizationStrategy, clouds, crumbIssuer, ..., numExecutors, ...
3:  numExecutor: 0
```

**What the output tells you:** The key is misspelled (`numExecutor` instead of `numExecutors`), and the exception lists the valid attribute names. When migrating an old controller, start from its exported configuration instead of writing YAML from scratch.

**Fix:**

```bash
# 1. Old controller: Manage Jenkins > Configuration as Code > View / Download Configuration: commit, then trim it.
# 2. Build the image from section 2 (pinned plugins.txt + casc/), secrets as ${VARS} from env or /run/secrets.
# 3. Jobs as code: multibranch pipelines that discover Jenkinsfiles from GitLab, so jobs need no backup.
docker compose build && docker compose up -d && docker logs -f jenkins | grep -iE 'casc|ConfiguratorException'
```

**Why this fix works:** With the image, `plugins.txt`, `casc/` and the Jenkinsfiles in Git, the controller becomes a disposable build product: a restore means building the image, applying the YAML and letting multibranch rediscover the jobs. Only build history and credentials need a backup. Pin plugin versions, because a plugin upgrade can rename JCasC keys.

**Prevent it:** Run a monthly lab drill that rebuilds the controller from Git, and reject UI changes in review ("change it in `casc/`").

**Next step:** KodeKloud: *Certified Jenkins Engineer* ([course](https://kodekloud.com/courses/certified-jenkins-engineer)) · [Jenkins docs: Configuration as Code](https://www.jenkins.io/doc/book/managing/casc/) · [Configuration as Code plugin](https://plugins.jenkins.io/configuration-as-code/)

**Community threads:** [Jenkins community: Migrating Jenkins](https://community.jenkins.io/t/migrating-jenkins/894) · [JCasC plugin page](https://plugins.jenkins.io/configuration-as-code/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=jenkins+configuration+as+code+%22Invalid+configuration+elements%22) · [Reddit r/jenkinsci](https://www.reddit.com/r/jenkinsci/search/?q=jcasc+migration&restrict_sr=1)

---

## 11. GitHub Actions self-hosted runners

Hosted GitHub runners rarely need troubleshooting, but self-hosted ones on your own VMs bring back every runner problem: matching, availability and host health. Most `actions/runner` issues are feature requests. The two families below are the operational ones.

### 11.1 Waiting for a runner to pick up the job

> **Seen as:** `Waiting for a runner to pick up this job...` with no end, for `runs-on: [self-hosted, linux, onprem, docker]` · **Where:** repository or organisation self-hosted runners · **Level:** [L1–L2 · Junior → Mid] · **How common:** `actions/runner` #3609 (92 comments), plus "Self-hosted runners disappeared" and "Runner not found" issues

**Why it happens:** A single runner must carry **all** the labels in `runs-on`. Organisation runners sit in runner groups that only some repositories may use, and public repositories are excluded by default. A runner runs one job at a time, so one busy runner looks like "no runner". Runners that are offline (service stopped, proxy or firewall blocking GitHub) take nothing. GitHub automatically removes runners that stay offline for a long time, and an outdated runner with auto-update disabled stops receiving jobs.

**Diagnose:**

```bash
gh api repos/ORG/REPO/actions/runners --jq '.runners[] | "\(.name) \(.status) busy=\(.busy) [\([.labels[].name] | join(","))]"'
# organisation runners: gh api orgs/ORG/actions/runners ...;  on the runner VM:
sudo journalctl -u 'actions.runner.*' -n 5 --no-pager
```

```
ci-02 online busy=true [self-hosted,Linux,X64,onprem,docker]
ci-03 offline busy=false [self-hosted,Linux,X64,onprem]
2026-10-01 08:14:11Z: Running job: build-image
```

**What the output tells you:** Only `ci-02` has every requested label, and it is busy. `ci-03` is offline and lacks the `docker` label anyway. The job is waiting for capacity, not hitting an error.

**Fix:**

```bash
sudo -i                                                          # on ci-03; /home/ghrunner is mode 750 on Ubuntu 22.04+
cd /home/ghrunner/actions-runner && ./svc.sh status
sudo -u ghrunner ./config.sh --check --url https://github.com/ORG/REPO --pat "$GH_PAT"   # PASS/FAIL per GitHub endpoint
./svc.sh start
# Add the missing label in the runner settings page, add runners, or autoscale with Actions Runner Controller.
```

**Why this fix works:** `--check` tests the exact GitHub endpoints the runner needs, which separates network and proxy problems from service problems. Restoring the second runner and its labels adds the missing capacity. For bursts, autoscaled ephemeral runners are the long-term answer. If a runner was removed after being offline, register it again with a new token.

**Prevent it:** Alert on runner status through the API, avoid labels that only one runner carries, and keep auto-update on.

**Next step:** KodeKloud: *GitHub Actions Certification*, Self Hosted Runner module ([course](https://kodekloud.com/courses/github-actions-certification)) · [GitHub docs: monitoring and troubleshooting self-hosted runners](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/monitoring-and-troubleshooting-self-hosted-runners)

**Community threads:** [actions/runner #3609: stuck waiting for a runner](https://github.com/actions/runner/issues/3609) · [#756: self-hosted runners disappeared](https://github.com/actions/runner/issues/756) · [#3857: Runner not found](https://github.com/actions/runner/issues/3857) · Search: [Stack Overflow](https://stackoverflow.com/search?q=github+actions+self-hosted+%22Waiting+for+a+runner+to+pick+up+this+job%22) · [Reddit r/github](https://www.reddit.com/r/github/search/?q=self+hosted+runner+waiting+for+a+runner&restrict_sr=1)

### 11.2 Self-hosted job lost or cancelled mid-run

> **Seen as:** `The self-hosted runner: ci-02 lost communication with the server. Verify the machine is running and has a healthy network connection.`, or `The operation was canceled.`, or `The runner has received a shutdown signal.` · **Where:** runner VMs under memory or disk pressure, or with automatic reboots · **Level:** [L2 · Mid] · **How common:** `actions/runner` issues on abandoned jobs, cancelled operations and random "task was cancelled" errors, each with dozens of comments

**Why it happens:** The job runs in a `Runner.Worker` process on your VM. Anything that kills it or the listener ends the job: the OOM killer during a heavy build, a full disk, `unattended-upgrades` rebooting the VM at 06:00, a hypervisor pausing the VM, or a workflow step that runs `pkill` or `docker system prune` against the runner's own containers.

**Diagnose:**

```bash
sudo dmesg -T | grep -i 'killed process' | tail -1
last -x reboot | head -1
grep -h 'ERR' /home/ghrunner/actions-runner/_diag/Runner_*.log | tail -2
```

```
[Fri Oct  2 06:04:51 2026] Out of memory: Killed process 31877 (Runner.Worker) total-vm:9421312kB, anon-rss:7340032kB
reboot   system boot  6.8.0-85-generic Fri Oct  2 06:10   still running
[2026-10-02 06:04:52Z ERR  JobDispatcher] Worker process exited with code 137
```

**What the output tells you:** Exit code 137 is SIGKILL, and the kernel log shows the OOM killer took the worker. Six minutes later the VM rebooted for updates, which would have killed any job running then too.

**Fix:**

```bash
# /etc/apt/apt.conf.d/52unattended-upgrades-local on runner VMs: reboot only in a quiet window
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:30";
# and: more RAM or fewer parallel jobs per VM; memory limits on container jobs; a separate disk for _work
```

**Why this fix works:** It removes both killers: memory headroom stops the OOM kills, and reboots move to a window with no jobs, or you drain the runner first. Ephemeral runners, one job per fresh VM or pod, also limit the damage any one job can do to the next.

**Prevent it:** Monitor runner VMs like production (node_exporter, OOM-kill alerts, disk alerts), and keep `_diag` logs off ephemeral disks if you need them after a crash.

**Next step:** [Memory](04-memory.md) · [Processes](05-processes.md) · KodeKloud: *GitHub Actions Certification*, Self Hosted Runner module ([course](https://kodekloud.com/courses/github-actions-certification))

**Community threads:** [actions/runner #1546: job abandoned](https://github.com/actions/runner/issues/1546) · [#2468: The operation was canceled](https://github.com/actions/runner/issues/2468) · [#3819: random "A task was cancelled"](https://github.com/actions/runner/issues/3819) · [GitHub docs: troubleshooting self-hosted runners](https://docs.github.com/en/actions/hosting-your-own-runners/managing-self-hosted-runners/monitoring-and-troubleshooting-self-hosted-runners) · Search: [Stack Overflow](https://stackoverflow.com/search?q=github+actions+self-hosted+runner+%22lost+communication+with+the+server%22) · [Reddit r/github](https://www.reddit.com/r/github/search/?q=self+hosted+runner+lost+communication&restrict_sr=1)

---

## 12. GitOps: Argo CD and Flux

GitOps moves the deploy step into the cluster. A controller compares Git with the live state and fixes the difference. That gives you drift detection and rollback by `git revert`, plus a new class of problems: diffs that never settle, health checks that never finish, hooks, and auto-sync behaviour. Kubernetes background: [Learn Kubernetes](31-learn-kubernetes.md) and the [containers and Kubernetes playbook](26-playbook-containers-k8s.md).

### 12.1 OutOfSync right after a successful sync

> **Seen as:** the sync succeeds and the app turns `OutOfSync` again at once; the diff shows `replicas`, normalised quantities (`500m` vs `0.5`), an injected `caBundle`, or a Helm-generated value that changes on every render · **Where:** Helm or Kustomize apps with HPAs, webhooks or cert-manager · **Level:** [L3 · Senior] · **How common:** the first entries of the Argo CD FAQ, and several top `argo-cd` issues on diffing (#9678 with 69 comments, #11143, #4537, #5202 with 254 reactions)

**Why it happens:** Argo CD compares the rendered manifests with the live objects. Anything that changes live objects after the apply creates a diff that never goes away: an HPA setting `replicas`, admission webhooks and controllers adding defaults, cert-manager injecting CA bundles. Templates that render differently on each run do the same, for example `randAlphaNum` passwords, or Helm `lookup`, which returns nothing because Argo CD renders with `helm template` and no cluster access.

**Diagnose:**

```bash
argocd app diff shop-web | head -6
kubectl -n shop get hpa shop-web
```

```
===== apps/Deployment shop/shop-web ======
86c86
<   replicas: 5
---
>   replicas: 3
NAME       REFERENCE             TARGETS        MINPODS   MAXPODS   REPLICAS   AGE
shop-web   Deployment/shop-web   cpu: 71%/60%   3         10        5          12d
```

**What the output tells you:** Git says 3 replicas, and the HPA scaled to 5. Argo CD reports the difference, and with `selfHeal` it would fight the HPA on every reconcile.

**Fix:**

```yaml
spec:                                    # Application
  ignoreDifferences:
    - { group: apps, kind: Deployment, jsonPointers: [/spec/replicas] }
    - group: admissionregistration.k8s.io
      kind: MutatingWebhookConfiguration
      jqPathExpressions: [".webhooks[]?.clientConfig.caBundle"]
  syncPolicy:
    syncOptions: [RespectIgnoreDifferences=true]
```

**Why this fix works:** `ignoreDifferences` removes the fields from the comparison, and `RespectIgnoreDifferences=true` also stops a sync from overwriting them. Without it, a sync resets replicas to 3. The cleanest fix is still at the source: remove `replicas` from the manifest when an HPA owns it, and keep random or `lookup`-based values out of templates. Do not turn off `selfHeal` globally to stop the noise. That hides real drift too.

**Prevent it:** Render and diff in the merge request (`helm template` or `kustomize build` plus `argocd app diff --local`), and review every new `ignoreDifferences` entry like code.

**Next step:** [Learn Kubernetes](31-learn-kubernetes.md) · KodeKloud: *Helm for Beginners* ([course](https://kodekloud.com/courses/helm-for-beginners)) · [Argo CD FAQ](https://argo-cd.readthedocs.io/en/stable/faq/)

**Community threads:** [Argo CD FAQ: OutOfSync after sync](https://argo-cd.readthedocs.io/en/stable/faq/) · [argo-cd #9678: ignoreDifferences with RespectIgnoreDifferences](https://github.com/argoproj/argo-cd/issues/9678) · [#11143: StatefulSet diff with server-side apply](https://github.com/argoproj/argo-cd/issues/11143) · [#4537: env diff not reported](https://github.com/argoproj/argo-cd/issues/4537) · [#5202: Helm lookup](https://github.com/argoproj/argo-cd/issues/5202) · Search: [Stack Overflow](https://stackoverflow.com/search?q=argocd+OutOfSync+after+sync+ignoreDifferences) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=argocd+always+outofsync&restrict_sr=1)

### 12.2 Stuck in Progressing on-prem

> **Seen as:** application health stays `Progressing` forever, and the resource tree points at an `Ingress` (or a `SealedSecret`) · **Where:** kubeadm clusters on-prem with Traefik or ingress-nginx and no load balancer · **Level:** [L3 · Senior] · **How common:** `argo-cd` issues #14607 and #5991, and an Argo CD FAQ entry that names the Traefik fix

**Why it happens:** Argo CD's built-in health check for an Ingress waits until `status.loadBalancer.ingress` contains an address. In the cloud a load balancer fills it in. On-prem nobody does, unless the ingress controller publishes its Service address into the Ingress status. Traefik does that only with `publishedService` enabled, and ingress-nginx only with `--publish-service`. Custom resources whose controllers never write status, such as older SealedSecrets controllers, stay Progressing too.

**Diagnose:**

```bash
kubectl -n shop get ingress shop-web -o wide
argocd app get shop-web | grep -E 'Health Status|Ingress'
```

```
NAME       CLASS     HOSTS              ADDRESS   PORTS     AGE
shop-web   traefik   shop.example.com             80, 443   3d
Health Status:      Progressing
networking.k8s.io  Ingress  shop  shop-web  Synced  Progressing
```

**What the output tells you:** The site may work fine, but the Ingress has an empty `ADDRESS`, so by Argo CD's rules it is still progressing, and the app never becomes Healthy. That blocks sync waves and any automation waiting for Healthy.

**Fix:**

```yaml
# Traefik Helm chart values: copy Traefik's Service address into every Ingress status
providers:
  kubernetesIngress:
    publishedService:
      enabled: true
# Traefik's Service needs an address: MetalLB (type LoadBalancer) or externalIPs on your nodes.
```

**Why this fix works:** With an address published, the Ingress status matches what Argo CD's health check expects. As a fallback, a custom health check in `argocd-cm` (`resource.customizations.health.networking.k8s.io_Ingress`, a short Lua script) can declare Ingresses healthy without an address. Use that only knowingly, because it also hides Ingresses that really are broken. For SealedSecrets, enable the controller's status updates.

**Prevent it:** When you add a new resource kind, check how Argo CD judges its health, and test the first app on the lab cluster before production.

**Next step:** [Traefik module 43](43-traefik-and-reverse-proxies.md) · KodeKloud: *Kubernetes Networking Deep Dive*, Kubernetes Ingress module ([course](https://kodekloud.com/courses/kubernetes-networking)) · [Argo CD FAQ](https://argo-cd.readthedocs.io/en/stable/faq/)

**Community threads:** [argo-cd #14607: Progressing for Ingress with no LB IP](https://github.com/argoproj/argo-cd/issues/14607) · [argo-cd #5991: SealedSecret stuck Progressing](https://github.com/argoproj/argo-cd/issues/5991) · [Argo CD FAQ: stuck in Progressing](https://argo-cd.readthedocs.io/en/stable/faq/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=argocd+ingress+progressing+traefik+publishedService) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=argocd+progressing+ingress&restrict_sr=1)

### 12.3 Argo CD can't reach Git, Helm or its API

> **Seen as:** `x509: certificate signed by unknown authority` for the GitLab repository or Harbor charts; `ssh: handshake failed: knownhosts: key mismatch`; from the CLI `rpc error: code = Unavailable desc = transport is closing`; for Helm OCI, `... is not a valid chart repository or cannot be reached` · **Where:** private GitLab with an internal CA, Harbor as an OCI Helm registry, the CLI going through Traefik · **Level:** [L3 · Senior] · **How common:** `argo-cd` #7723 (host key mismatch after GitHub rotated its key) and #10823 (`oci://` prefix), plus two FAQ entries

**Why it happens:** Argo CD's repo-server does not use the node's trust store. It trusts the certificates in `argocd-tls-certs-cm` and the SSH host keys in `argocd-ssh-known-hosts-cm`. When a Git server's host key changes (GitHub rotated its RSA key in 2023, and a reinstalled GitLab gets new keys), every SSH repository breaks with a mismatch. The CLI speaks gRPC over HTTP/2, which some proxies do not pass through. Helm OCI repositories need the OCI flag, and older versions reject an `oci://` prefix in the repository URL.

**Diagnose:**

```bash
argocd repo list
kubectl -n argocd logs deploy/argocd-repo-server --since=15m | grep -E 'x509|knownhosts' | tail -1
```

```
TYPE  NAME           REPO                                                   INSECURE  OCI    LFS    CREDS  STATUS      MESSAGE
git                  https://gitlab.example.com/platform/deploy-config.git  false     false  false  true   Failed      ...x509: certificate signed by unknown authority
helm  harbor-charts  harbor.example.com/charts                              false     true   false  true   Successful
```

**What the output tells you:** Harbor works, and the GitLab repository fails on TLS, so the internal CA is missing from Argo CD's own certificate store. A `knownhosts: key mismatch` line would instead point at the SSH known hosts ConfigMap.

**Fix:**

```bash
argocd cert add-tls gitlab.example.com --from corp-chain.pem          # stored in argocd-tls-certs-cm
argocd cert add-ssh --batch --from gitlab_known_hosts                 # stored in argocd-ssh-known-hosts-cm (verified keys)
argocd repo add harbor.example.com/charts --type helm --name harbor-charts --enable-oci \
  --username "$HARBOR_ROBOT" --password "$HARBOR_SECRET"
argocd login argocd.example.com --grpc-web                            # CLI through proxies without gRPC/HTTP2
```

**Why this fix works:** The certificate and known-hosts ConfigMaps are exactly what the repo-server reads, so the repository turns `Successful` on the next refresh. `--grpc-web` wraps gRPC in plain HTTP/1.1 requests that any proxy carries. Do not mark repositories `insecure` or use `--insecure` outside a throwaway test. The FAQ says the same.

**Prevent it:** Keep both ConfigMaps in Git, managed declaratively, and add "update Argo CD" to the runbooks for CA rotation and Git server rebuilds.

**Next step:** [Web, HTTP and TLS](18-web-http-tls.md) · KodeKloud: *Helm for Beginners* ([course](https://kodekloud.com/courses/helm-for-beginners)) · [Argo CD docs](https://argo-cd.readthedocs.io/en/stable/)

**Community threads:** [argo-cd #7723: host key mismatch](https://github.com/argoproj/argo-cd/issues/7723) · [argo-cd #10823: oci:// prefix](https://github.com/argoproj/argo-cd/issues/10823) · [Argo CD FAQ: x509 and transport is closing](https://argo-cd.readthedocs.io/en/stable/faq/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=argocd+repository+x509+%22certificate+signed+by+unknown+authority%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=argocd+private+ca+gitlab&restrict_sr=1)

### 12.4 Sync waits forever for a hook

> **Seen as:** the operation shows `waiting for completion of hook batch/Job/db-migrate` for hours, and new syncs report that another operation is already running · **Where:** PreSync database migration Jobs · **Level:** [L3 · Senior] · **How common:** `argo-cd` #6880 has 137 comments; #9830 covers hooks that behave differently on auto-sync

**Why it happens:** A PreSync hook must finish before Argo CD applies anything else. If the Job never completes (the database is unreachable, the image cannot be pulled, or a lock is held), the sync waits indefinitely. If something deletes the Job before Argo CD records the result (a short `ttlSecondsAfterFinished`), the result is lost. Without a delete policy, an old Job with the same name blocks the next run.

**Diagnose:**

```bash
argocd app get shop-web | grep -E 'Phase|Message'
kubectl -n shop get pods -l job-name=db-migrate; kubectl -n shop logs job/db-migrate --tail=1
```

```
Phase:              Running
Message:            waiting for completion of hook batch/Job/db-migrate
NAME               READY   STATUS             RESTARTS      AGE
db-migrate-x7k2p   0/1     CrashLoopBackOff   12 (3m ago)   47m
dial tcp 10.20.0.60:5432: connect: connection refused
```

**What the output tells you:** The hook is not stuck in Argo CD. The migration pod cannot reach PostgreSQL and keeps restarting, so the Job never completes and never fails either.

**Fix:**

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migrate
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation,HookSucceeded
spec:
  backoffLimit: 2
  activeDeadlineSeconds: 600       # fail visibly after 10 minutes instead of hanging
  template:
    spec:
      restartPolicy: Never
      containers:
        - { name: migrate, image: "harbor.example.com/shop/web:9d8c7b6a", command: ["./migrate.sh"] }
```

**Why this fix works:** A deadline and a backoff limit turn "hangs forever" into a failed hook and a failed sync, which alerts can see. `BeforeHookCreation` removes the previous Job before creating a new one. Free the app now with `argocd app terminate-op shop-web`, fix the database path, then sync again.

**Prevent it:** Keep migrations idempotent and backward compatible ([Databases ops](38-learn-databases-ops.md)), give every hook a deadline, and alert on sync operations that run longer than a few minutes.

**Next step:** [Deployment patterns](35-deployment-patterns.md) · KodeKloud: *Certified Kubernetes Application Developer (CKAD)*, POD Design ([course](https://kodekloud.com/courses/certified-kubernetes-application-developer-ckad)) · [Argo CD docs](https://argo-cd.readthedocs.io/en/stable/)

**Community threads:** [argo-cd #6880: waiting for completion of hook](https://github.com/argoproj/argo-cd/issues/6880) · [argo-cd #9830: hook not running on auto sync](https://github.com/argoproj/argo-cd/issues/9830) · Search: [Stack Overflow](https://stackoverflow.com/search?q=argocd+%22waiting+for+completion+of+hook%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=argocd+presync+hook+stuck&restrict_sr=1)

### 12.5 A failed sync blocks newer commits

> **Seen as:** auto-sync keeps retrying a broken revision while the fix commit waits; the app condition says `Skipping auto-sync: failed previous sync attempt to [3f2a9c1d]`; `argocd app rollback` answers `rollback cannot be initiated when auto-sync is enabled` · **Where:** production apps with automated sync and retries · **Level:** [L4 · Lead/SRE] · **How common:** `argo-cd` #11494 (retries block newer commits) and #9570 (rollback-aware auto-sync, 117 reactions)

**Why it happens:** With `retry` configured, auto-sync keeps retrying the revision that failed, with backoff, and the running operation holds the app until the retries are exhausted. After that, auto-sync deliberately does not retry the same revision. The UI or CLI rollback conflicts with auto-sync, because auto-sync would immediately re-apply whatever Git says. In GitOps, the rollback has to happen in Git.

**Diagnose:**

```bash
argocd app get shop-web --show-operation | grep -E 'Sync Revision|Phase|Message'
argocd app history shop-web | tail -1
```

```
Sync Revision:      3f2a9c1d
Phase:              Running
Message:            Retrying attempt #4 at 10:51AM: one or more objects failed to apply
41  2026-09-30 10:12:44 +0000 UTC  main (8b7e6d5c)
```

**What the output tells you:** The controller is still retrying `3f2a9c1d`, a bad commit that fails to apply, while history shows `8b7e6d5c` as the last good deploy. A newer fix will only apply once this operation ends.

**Fix:**

```bash
argocd app terminate-op shop-web                      # stop retrying the broken revision
git revert --no-edit 3f2a9c1d && git push             # the GitOps rollback: Git becomes the good state again
argocd app sync shop-web                              # optional: do not wait for the next reconcile
```

**Why this fix works:** Terminating the operation frees the app. The revert makes Git describe the last good state, which auto-sync then applies, and the audit trail shows who rolled back and why. Set `syncPolicy.retry` with a small `limit` and a `maxDuration` so a bad commit fails fast instead of blocking for an hour. Treat the CLI rollback (with auto-sync disabled first) as a break-glass tool, not the routine.

**Prevent it:** Promote between environments through merge requests, keep a written rollback runbook that you practise, and alert on `Degraded` or failed syncs. Tools that write image tags to Git, such as Argo CD Image Updater, need the same care.

**Next step:** [SRE practice in module 33](33-learn-cicd-iac-sre.md) · [Career ladder](40-career-ladder.md) · KodeKloud: *Fundamentals of SRE* ([course](https://kodekloud.com/courses/fundamentals-of-sre))

**Community threads:** [argo-cd #11494: retrying failed syncs block newer commits](https://github.com/argoproj/argo-cd/issues/11494) · [argo-cd #9570: rollback-aware auto-sync](https://github.com/argoproj/argo-cd/issues/9570) · [argo-cd #7385: Image Updater in Argo CD](https://github.com/argoproj/argo-cd/issues/7385) · Search: [Stack Overflow](https://stackoverflow.com/search?q=argocd+rollback+%22auto-sync+is+enabled%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=argocd+rollback+auto+sync&restrict_sr=1)

### 12.6 Flux reconciliation stuck

> **Seen as:** `kustomization path not found: stat /tmp/kustomization-417/clusters/prod/apps: no such file or directory`, a HelmRelease reporting `upgrade retries exhausted`, or `dependency 'flux-system/infra' is not ready` · **Where:** Flux v2 bootstrapped against GitLab · **Level:** [L3 · Senior] · **How common:** recurring topics in the Flux issue trackers and community chats (see the search links)

**Why it happens:** A Kustomization points at a path and branch that no longer exist after the repository was reorganised. The source cannot authenticate (deploy key or private CA). A Helm install or upgrade failed (bad values, a missing CRD), and after the configured retries the helm-controller stops trying until something changes. One failing object then blocks everything that `dependsOn` it.

**Diagnose:**

```bash
flux get all -A --status-selector ready=false
flux logs --level=error --since=30m | tail -2
```

```
NAMESPACE    NAME                   REVISION  SUSPENDED  READY  MESSAGE
shop         helmrelease/shop-web   0.4.2     False      False  Helm upgrade failed for release shop/shop-web with chart shop-web@0.4.2: upgrade retries exhausted

NAMESPACE    NAME                   REVISION  SUSPENDED  READY  MESSAGE
flux-system  kustomization/apps               False      False  kustomization path not found: stat /tmp/kustomization-417/clusters/prod/apps: no such file or directory
```

`flux get all` prints one table per kind, each with its own header.

**What the output tells you:** Two independent faults. The `apps` Kustomization looks for a directory the tracked branch no longer has, and the HelmRelease gave up after failed upgrades and will not retry on its own.

**Fix:**

```bash
git ls-tree -d --name-only origin/main clusters/prod/      # what paths really exist on the tracked branch?
# fix spec.path in the Kustomization (in Git), then:
flux reconcile kustomization apps --with-source
flux suspend helmrelease shop-web -n shop && flux resume helmrelease shop-web -n shop   # retry after fixing values
```

**Why this fix works:** Reconciling with `--with-source` fetches the fixed Git revision immediately. Suspending and resuming the HelmRelease makes the controller attempt the release again after you fixed its cause. Recent Flux versions also document dedicated reset or force options. Never edit Flux-managed objects with `kubectl edit`: the next reconcile reverts them, and the fix must live in Git.

**Prevent it:** Run `kustomize build` on every cluster path, plus `flux check`, in CI before merging, and route Flux notification-controller alerts to your chat.

**Next step:** [Learn Kubernetes](31-learn-kubernetes.md) · KodeKloud: *Helm for Beginners* ([course](https://kodekloud.com/courses/helm-for-beginners)) · [Flux docs](https://fluxcd.io/flux/)

**Community threads:** Search: [GitHub fluxcd/flux2 issues](https://github.com/fluxcd/flux2/issues?q=%22upgrade+retries+exhausted%22) · [GitHub fluxcd/helm-controller issues](https://github.com/fluxcd/helm-controller/issues?q=%22retries+exhausted%22) · [Stack Overflow](https://stackoverflow.com/search?q=flux+helmrelease+%22upgrade+retries+exhausted%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=flux+helmrelease+retries+exhausted&restrict_sr=1)

---

## 13. Quality gates, artifact repositories and secrets

The supporting tools of a pipeline fail in their own ways: SonarQube refuses to start on a stock Ubuntu 22.04 host, quality gates that never block anything, Nexus rejecting CI credentials, and secrets ending up in job logs.

### 13.1 SonarQube won't start: vm.max_map_count

> **Seen as:** the SonarQube container exits, and its log shows `bootstrap check failure [1] of [1]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]` · **Where:** SonarQube in Docker, Compose or a Dokploy template on Ubuntu 22.04, or on a 24.04 host where an old sysctl file lowers the default · **Level:** [L1 · Junior] · **How common:** a classic first-install failure; Sonar's own docs and community explain the 524288 requirement

**Why it happens:** SonarQube embeds Elasticsearch, and Elasticsearch refuses to start when the kernel allows too few memory map areas. The kernel default, and Ubuntu 22.04's, is 65530. Ubuntu 24.04 raised its default to 1048576, so a fresh 24.04 host passes unless a sysctl file (an old hardening role, a copied `/etc/sysctl.conf`) sets it lower. Sonar's documented requirement is at least 524288, plus high file and process limits. `vm.max_map_count` is a host kernel setting, so it cannot be changed from inside a container: it must be set on the Docker host, or on every Swarm node that can run the service.

**Diagnose:**

```bash
sysctl vm.max_map_count
docker logs sonarqube 2>&1 | grep -i 'bootstrap check' | tail -1
```

```
vm.max_map_count = 65530
bootstrap check failure [1] of [1]: max virtual memory areas vm.max_map_count [65530] is too low, increase to at least [262144]
```

**What the output tells you:** The host still has the old 65530 default (Ubuntu 22.04, or a 24.04 host where something overrides the new default: find it with `grep -rs max_map_count /etc/sysctl.conf /etc/sysctl.d /usr/lib/sysctl.d`), and Elasticsearch names the exact limit it rejected. Nothing is wrong with the SonarQube image or its database.

**Fix:**

```bash
# only raise it: on Ubuntu 24.04 the default 1048576 is already higher, so do not write 524288 there
[ "$(sysctl -n vm.max_map_count)" -lt 524288 ] && echo 'vm.max_map_count=524288' | sudo tee /etc/sysctl.d/99-sonarqube.conf
sudo sysctl --system
# compose: ulimits: { nofile: { soft: 131072, hard: 131072 }, nproc: 8192 }, then recreate the container
```

**Why this fix works:** A file in `/etc/sysctl.d/` survives reboots, and `sysctl --system` applies it now. The ulimits cover Sonar's file-descriptor and thread requirements. `fs.file-max` must also be at least 131072, but modern Ubuntu's default is far higher, so check it and never lower it. Do not run the container privileged to make the error go away.

**Prevent it:** Put the host prerequisites in your provisioning (Ansible), and give SonarQube its own VM or strict resource limits plus an external PostgreSQL database.

**Next step:** [Kernel and system](13-kernel-system.md) · KodeKloud: *Docker Certified Associate*, Docker Engine – Security, resource limits ([course](https://kodekloud.com/courses/docker-certified-associate-exam-course)) · [Sonar docs: Linux pre-installation](https://docs.sonarsource.com/sonarqube-community-build/server-installation/pre-installation/linux)

**Community threads:** [Sonar community: why vm.max_map_count=524288](https://community.sonarsource.com/t/sonarqube-8-8-prerequisites-why-set-vm-max-map-count-524288-regardless-of-hardware-specifications/48406) · [Sonar docs: Linux prerequisites](https://docs.sonarsource.com/sonarqube-community-build/server-installation/pre-installation/linux) · Search: [Stack Overflow](https://stackoverflow.com/search?q=sonarqube+docker+%22vm.max_map_count%22+65530) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=sonarqube+docker+max_map_count&restrict_sr=1)

### 13.2 Sonar analysis or quality gate misleads

> **Seen as:** `Shallow clone detected, no blame information will be provided.`; "new code" metrics that make no sense; merge request analysis failing with `To use the property "sonar.branch.name" and analyze branches, Developer Edition or above is required.`; a green pipeline while the quality gate is red · **Where:** a SonarScanner job in GitLab CI · **Level:** [L2 · Mid] · **How common:** standard scanner warnings that most teams meet in their first week

**Why it happens:** GitLab clones only the last 20 commits by default, so the scanner cannot run blame or work out which code is new. The free Community Build analyses a single branch (main), and branch and merge request analysis need a commercial edition. The scanner uploads its report and exits successfully unless you ask it to wait for the quality gate. A Sonar server behind the private CA makes the scanner's JVM fail with `PKIX path building failed`.

**Diagnose:**

```bash
grep -E 'Shallow clone|QUALITY GATE|ANALYSIS SUCCESSFUL|PKIX' sonar-job.log
```

```
WARN  Shallow clone detected, no blame information will be provided. You can convert to non-shallow with 'git fetch --unshallow'.
INFO  ANALYSIS SUCCESSFUL, you can find the results at: https://sonar.example.com/dashboard?id=shop-web
```

**What the output tells you:** The analysis ran on a shallow clone, and there is no `QUALITY GATE STATUS` line, so the job never waited for the gate. The green status says nothing about code quality.

**Fix:**

```yaml
sonar:
  image: sonarsource/sonar-scanner-cli:VERSION
  variables: { GIT_DEPTH: "0", SONAR_USER_HOME: "${CI_PROJECT_DIR}/.sonar" }
  cache: { key: sonar, paths: [.sonar/cache] }
  script: [sonar-scanner -Dsonar.qualitygate.wait=true -Dsonar.qualitygate.timeout=300]
  rules: [{ if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH }]     # Community Build: main only
```

**Why this fix works:** `GIT_DEPTH: "0"` gives the scanner the full history. `sonar.qualitygate.wait` makes the job fail when the gate fails, so the pipeline actually blocks bad code. `SONAR_TOKEN` and `SONAR_HOST_URL` come from masked, protected variables. For the private CA, point `SONAR_SCANNER_OPTS` at a Java truststore containing your root CA.

**Prevent it:** Make the Sonar job required on the default branch, and decide early whether you need merge request analysis, which affects which edition you need.

**Next step:** [Security and DevSecOps](37-learn-security-devsecops.md) · KodeKloud: *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines*, Optimization, Security and Monitoring ([course](https://kodekloud.com/courses/gitlab-ci-cd)) · [Sonar docs](https://docs.sonarsource.com/)

**Community threads:** [Sonar docs](https://docs.sonarsource.com/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=sonarqube+%22Shallow+clone+detected%22+gitlab) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=sonarqube+quality+gate+gitlab+ci&restrict_sr=1)

### 13.3 Nexus proxy repositories fail from CI

> **Seen as:** `npm ERR! code E401` (current npm versions print `npm error code E401`) with `Unable to authenticate, need: BASIC realm="Sonatype Nexus Repository Manager"`; for Docker, `http: server gave HTTP response to HTTPS client`; uploads suddenly refused when the Nexus disk is nearly full · **Where:** Nexus as the npm, Maven or Docker proxy for on-prem CI · **Level:** [L2 · Mid] · **How common:** recurring Nexus questions in every community (see the search links)

**Why it happens:** npm 9 and later only send credentials that are scoped to the registry URL in `.npmrc`. An old, unscoped `_auth` line is ignored, so requests arrive anonymous and get a 401. Nexus serves Docker repositories on a separate connector port, which is plain HTTP unless you configured an HTTPS connector or a reverse proxy. Cleanup policies only mark components for deletion, and disk space returns only after the "Admin - Compact blob store" task runs. Nexus also protects itself by refusing writes when free space drops below its threshold.

**Diagnose:**

```bash
npm config get registry && npm ping
curl -sI https://nexus.example.com:8443/v2/ | head -1
df -h /opt/sonatype-work
```

```
https://nexus.example.com/repository/npm-group/
npm error code E401
curl: (35) OpenSSL/3.0.13: error:0A00010B:SSL routines::wrong version number
/dev/sdc1       200G  196G  4.0G  98% /opt/sonatype-work
```

**What the output tells you:** Three separate problems. npm reaches Nexus without valid credentials (401). The Docker connector port speaks plain HTTP (`wrong version number` is what TLS reports when it gets an HTTP answer). And the blob store disk is almost full.

**Fix:**

```ini
# .npmrc in the repository; NPM_AUTH = base64 of "user:password", stored as a masked CI variable
registry=https://nexus.example.com/repository/npm-group/
//nexus.example.com/repository/npm-group/:_auth=${NPM_AUTH}
```

**Why this fix works:** The scoped auth line matches the registry path, so npm sends the credentials. For Docker, either add an HTTPS connector in the repository settings or route a hostname such as `docker.example.com` through Traefik to the connector port. Then clients use normal TLS on 443. Free disk space with cleanup policies followed by the compact task. Deleting files under `sonatype-work` by hand corrupts the blob store.

**Prevent it:** Alert on the blob store disk at 80%, use one group repository per ecosystem, and keep the CI credentials in a dedicated Nexus user with read-only access to the group repositories.

**Next step:** [Storage and disk](01-storage-disk.md) · [Web, HTTP and TLS](18-web-http-tls.md) · [Sonatype docs](https://help.sonatype.com/)

**Community threads:** [Sonatype docs](https://help.sonatype.com/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=nexus+npm+E401+%22Unable+to+authenticate%22) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=nexus+repository+docker+proxy&restrict_sr=1)

### 13.4 Secrets leak into job logs

> **Seen as:** a token readable in a job log (from `set -x`, `env`, `curl -v`, or an error message that prints a URL with credentials); Jenkins printing `Warning: A secret was passed to "sh" using Groovy String interpolation, which is insecure.`; a secret scanner alert on exported logs · **Where:** any CI tool · **Level:** [L2–L3 · Mid → Senior] · **How common:** a common incident class, serious enough that Jenkins prints a dedicated warning and GitLab added hidden variables

**Why it happens:** Masking replaces only the exact value as it appears. A base64-encoded, URL-encoded or multi-line copy slips through. `set -x` prints every expanded command, and verbose tools echo headers. In Jenkins, a double-quoted Groovy string inserts the secret into the command line before the shell runs, where it shows up in logs and the process list. GitHub masks registered secrets but not values derived from them. Job logs are readable by many project members and kept for a long time.

**Diagnose:**

```bash
# scan the last 50 job logs of a project for token-like strings (GitLab API, token with read_api)
for j in $(curl -sS -H "PRIVATE-TOKEN: $GITLAB_TOKEN" "https://gitlab.example.com/api/v4/projects/PROJECT_ID/jobs?per_page=50" | jq -r '.[].id'); do
  curl -sS -H "PRIVATE-TOKEN: $GITLAB_TOKEN" "https://gitlab.example.com/api/v4/projects/PROJECT_ID/jobs/$j/trace" \
    | grep -qE 'glpat-|glrt-|AKIA[0-9A-Z]{16}' && echo "job $j: possible secret"; done
```

```
job 88412: possible secret
```

**What the output tells you:** At least one log contains something shaped like a GitLab or AWS key. Open that log, confirm what leaked, and treat it as compromised, however short the exposure was.

**Fix:**

```bash
# 1. Rotate the credential first: deleting the log does not un-leak it.
# 2. Erase the job log and artifacts:
curl -sS -X POST -H "PRIVATE-TOKEN: $GITLAB_TOKEN" "https://gitlab.example.com/api/v4/projects/PROJECT_ID/jobs/88412/erase"
# 3. Fix the pattern: no set -x near secrets, --password-stdin, file-type variables, no curl -v in pipelines.
```

**Why this fix works:** Rotation removes the value an attacker could use, and erasing the log limits further exposure. The pattern fixes stop the next leak. In Jenkins, wrap credentials in `withCredentials` and use single-quoted `sh '...'` steps, so the shell expands `$PASSWORD`, not Groovy. In GitHub Actions, register derived values with `echo "::add-mask::$VALUE"`. Better still, remove long-lived secrets entirely with GitLab `id_tokens` (OIDC) for Vault or AWS, and use masked and hidden variables for what remains.

**Prevent it:** Run secret detection (for example gitleaks) on repositories and periodically on job logs, shorten log retention for deploy jobs, and prefer short-lived credentials. More in [Security and DevSecOps](37-learn-security-devsecops.md) and [Wazuh and security tools](48-wazuh-and-security-tools.md).

**Next step:** [Secrets management in module 33](33-learn-cicd-iac-sre.md) · KodeKloud: *GitHub Actions Certification*, Security Guide module ([course](https://kodekloud.com/courses/github-actions-certification)) · [GitLab docs](https://docs.gitlab.com/)

**Community threads:** Search: [GitHub gitleaks issues](https://github.com/gitleaks/gitleaks/issues?q=ci+logs) · [Stack Overflow](https://stackoverflow.com/search?q=jenkins+%22Groovy+String+interpolation%2C+which+is+insecure%22) · [Reddit r/devops](https://www.reddit.com/r/devops/search/?q=secret+leaked+in+ci+logs&restrict_sr=1)

---

## Self-check

Ten timed break-and-fix drills on the lab from section 2, ordered by stage. Break the lab exactly as described, start a timer, and fix it using only the entry's Diagnose and Fix steps. You pass when you beat the time and can explain the cause in two sentences.

| # | Stage | Break it on purpose | Target time | Done when |
|---|---|---|---|---|
| 1 | Fresher | Add `tags: [harbor]` to a job when no runner has that tag | 10 min | you can read the stuck message aloud and explain each of its three causes, then fix it (5.1) |
| 2 | Fresher | Mark `HARBOR_PASSWORD` as protected and push a feature branch | 10 min | the push job is skipped on unprotected refs instead of failing with the TTY error (5.4) |
| 3 | Junior | Delete the runner in the GitLab UI while it is idle | 15 min | the runner is re-created with a `glrt-` token and `verify` says `is valid` (5.2) |
| 4 | Junior | Start a Jenkins agent on a fresh VM with no `known_hosts` | 15 min | the checkout works with pinned host keys, with no "No verification" shortcut (10.6) |
| 5 | Mid-level | Change `DOCKER_HOST` to `tcp://docker:2375` in the build template | 15 min | builds pass again with TLS on 2376, and you can explain what `/certs/client` is for (6.1) |
| 6 | Mid-level | Remove the Harbor CA volume line from `config.toml` | 20 min | the push works, and you showed which daemon lacked the CA (7.2) |
| 7 | Mid-level | Set Traefik's `readTimeout` to 10s on the lab registry entry point and push a 500 MB image | 30 min | the access log shows the cut, and the push passes after the fix (7.4) |
| 8 | Senior | Set the lab runner VM's NIC MTU to 1400 and keep dind at 1500 | 30 min | you proved the black hole with `ping -M do` and fixed it with `--mtu` (6.2) |
| 9 | Senior | Add `replicas: 3` to an Argo CD app that has an HPA | 20 min | the app is Synced and Healthy, with a written reason for the chosen fix (12.1) |
| 10 | Senior/Lead | Merge two commits a minute apart while the first one's build is slowed with `sleep 120` | 45 min | you showed the older deploy winning, fixed it with `resource_group` and outdated-job protection, and wrote a five-line postmortem (9.4) |

---

## Where to go next

- **Fundamentals and the complete pipeline:** [Learn Git, CI/CD, IaC and SRE](33-learn-cicd-iac-sre.md), sections 2 (GitLab CI/CD), 6 (secrets) and 7 (SRE practice).
- **How to roll out safely:** [Deployment patterns](35-deployment-patterns.md), for blue-green, canary and the Apache-to-Dokploy migration.
- **Where your pipelines deploy:** [Dokploy and self-hosted PaaS](45-dokploy-and-self-hosted-paas.md), [Traefik and reverse proxies](43-traefik-and-reverse-proxies.md), and the original [Apache 443 and Dokploy case](21-case-apache-443-dokploy.md).
- **Container and cluster internals behind the build problems:** [Learn Docker](30-learn-docker.md), [Learn Kubernetes](31-learn-kubernetes.md), and the [containers and Kubernetes playbook](26-playbook-containers-k8s.md).
- **When a deploy takes the site down:** [Site-down playbook](25-playbook-site-down.md) and the [ports inventory playbook](22-playbook-ports-inventory.md).
- **Security of the whole chain:** [Security and DevSecOps](37-learn-security-devsecops.md) and [Wazuh and security tools](48-wazuh-and-security-tools.md).
- **Your growth path:** the [career ladder](40-career-ladder.md), where CI/CD ownership grows from fixing your own job to owning the release process.
- **Official docs:** [GitLab](https://docs.gitlab.com/) · [Jenkins](https://www.jenkins.io/doc/) · [GitHub Actions](https://docs.github.com/en/actions) · [Argo CD](https://argo-cd.readthedocs.io/en/stable/) · [Flux](https://fluxcd.io/flux/) · [Harbor](https://goharbor.io/docs/) · [SonarQube](https://docs.sonarsource.com/).
- **KodeKloud next:** finish *GitLab CI/CD: Architecting, Deploying, and Optimizing Pipelines* ([course](https://kodekloud.com/courses/gitlab-ci-cd)), then add *Certified Jenkins Engineer* or *GitHub Actions Certification* only if your job uses those tools.
