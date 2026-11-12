# Free interactive learning tools: containers, Kubernetes, CI/CD, IaC, observability

Scope: free browser visualisers, explainers, playgrounds, linters, validators and simulators, the same kind as Protocol Explorer. Reader: an on-prem engineer working with Docker/Swarm, Dokploy, Traefik, Harbor, GitLab CI, kubeadm and the CKA. Every domain in `known_domains.txt` was skipped. That list includes github.com, helm-playground.com, editor.networkpolicy.io, killercoda, labs.iximiuz.com, grafana.com, demo.promlens.com, ottl.run, kubernetes.io, docs.gitlab.com and k8sgames.com.

Verification method: each tool was opened in a real browser pane on 2026-11-08/09 (the "Nov 2026" check) and its rendered text read. For several, the page's own JavaScript was also inspected to see where pasted data goes. GitHub repo activity (`pushed_at`) was read from api.github.com on the same day. Nothing was pasted, submitted, run, downloaded or signed into. A few URLs were opened just to load the page: Argo CD demo, VMUI and VictoriaLogs default queries.

Level scale used here (adjust to the handbook's own definitions): **L0** = concept, no prior knowledge. **L1** = first hands-on use. **L2** = everyday operations. **L3** = advanced or debugging. **L4** = internals or expert.

Abbreviations: **"Client-side"** means the page says, or its code shows, that processing happens in the browser. **"Server"** means pasted content is POSTed to the site's backend.

## Q1. Ranked list of verified tools (20-30 finds)

### Takeaway
29 tools were opened and are live as of November 2026; the six best are ranked first, the rest grouped by category. The strongest fits for this reader are:
- Kubesimplify's "Kubernetes, explained" walkthroughs;
- the actionlint and hadolint WASM linters;
- kube-score.com (WASM);
- OTelBin;
- the public read-only Argo CD demo;
- the VictoriaMetrics VMUI playground.

Most Compose, YAML and JSON helpers run client-side. The Ansible and HCL playgrounds and ValidKube are server-side.

### Cited Findings

**Ranked list. The top six are the best fits; from #7 on, entries are grouped by category rather than strictly ranked.**

1. **Kubernetes, explained (Kubesimplify)**: https://kubernetes-explained.vercel.app/
   - **What it does:** step-through animations covering:
     - "From command to running pod" (23 steps, covering kubectl, API server, etcd, scheduler, kubelet and containerd);
     - the scheduler's filter, score and bind phases;
     - "How a Service finds your Pods" (selector to EndpointSlice to kernel);
     - "Inside an EndpointSlice";
     - kube-proxy iptables/IPVS/nftables modes;
     - "A request through ingress".

     It also has an explorable "Anatomy of a cluster" map. Several scenarios say they were "Verified against kubernetes/kubernetes 1.36 source". Keyboard step controls. [Source](https://kubernetes-explained.vercel.app/)
   - **Access:** free, no sign-up, browser. **Data:** nothing pasted. **Maintained:** yes; it cites 1.36 source, which is current. No public repo was found (`kubesimplify/kubernetes-explained` returns 404 on the GitHub API). **Level:** L1-L3.
   - **Topics:** `k8s-architecture`, `k8s-services-dns`, `k8s-networking`, `k8s-troubleshooting`, `cka-exam`.

2. **actionlint playground**: https://rhysd.github.io/actionlint/
   - **What it does:** static checker for GitHub Actions workflow files. Paste a workflow, click Check, and it reports errors. The page loads a WebAssembly binary and shows v1.7.12. [Source](https://rhysd.github.io/actionlint/)
   - **Access:** free, browser, no sign-up. **Data:** client-side (WASM). **Maintained:** repo pushed 2026-07-16, 4.4k stars. [Source](https://api.github.com/repos/rhysd/actionlint) **Level:** L1-L2.
   - **Topics:** `gitops-argocd` (GitHub Actions runners), `platform-engineering`.

3. **Hadolint online**: https://hadolint.github.io/hadolint/
   - **What it does:** Dockerfile linter. It parses the Dockerfile into an AST, applies rules, and runs ShellCheck on `RUN` lines. It has Lint and Clear buttons. [Source](https://hadolint.github.io/hadolint/)
   - **Access:** free, browser. **Data:** client-side. The page loads `js/hadolint.mjs`, which references WASM (inspected in-page). **Maintained:** repo pushed 2026-10-19, 12.5k stars. [Source](https://api.github.com/repos/hadolint/hadolint) **Level:** L1-L2.
   - **Topics:** `dockerfile`, `gitlab-ci-harbor` (lint stage), `docker-basics`.

4. **kube-score (online)**: https://kube-score.com/
   - **What it does:** static analysis of Kubernetes object definitions, with reliability and security recommendations. Paste YAML or JSON; output formats are CLI, CI, JSON, SARIF and JUnit. The page states "This tool is running 100% in your browser, no data is sent to any server!" and loads WebAssembly. [Source](https://kube-score.com/)
   - **Access:** free, MIT. **Maintained:** repo pushed 2026-05-20. [Source](https://api.github.com/repos/zegl/kube-score) **Level:** L2.
   - **Topics:** `k8s-workloads`, `k8s-troubleshooting`, `helm-kustomize` (score rendered output), `cka-exam`.

5. **OTelBin (by Dash0)**: https://www.otelbin.io/
   - **What it does:** web editor and validator for OpenTelemetry Collector configs, with pipeline visualisation. The live page shows "Validation: Browser-only" and offers "the improved, distribution-specific validation", plus a Share button. [Source](https://www.otelbin.io/)
   - **Access:** free, browser. **Maintained:** repo pushed 2026-11-08, 585 stars. [Source](https://api.github.com/repos/dash0hq/otelbin)
   - **Level:** L2-L3.
   - **Topics:** `logs-loki` (Alloy/OTel pipelines), `prometheus-grafana`, `grafana-loki-ops`.

6. **Argo CD public demo**: https://cd.apps.argoproj.io/
   - **What it does:** a live Argo CD instance, browsable without logging in (the "Log in" button is optional). It showed **v3.7.0** with about 57 apps in Healthy, Degraded, Missing, OutOfSync and Progressing states, synced from `argoproj/argocd-example-apps`. [Source](https://cd.apps.argoproj.io/applications)
   - **Access:** free, browser. **Data:** read-only viewing, nothing pasted. **Maintained:** current 3.x release. **Level:** L1-L2.
   - **Topics:** `gitops-argocd`, `deployment-strategies`.

7. **VictoriaMetrics playground (VMUI)**: https://play.victoriametrics.com/
   - **What it does:** a public MetricsQL/PromQL query UI over a live "sandbox" Kubernetes cluster (node-exporter and other targets). The UI offers "Trace query", Explore, Tools and Alerting tabs. [Source](https://play.victoriametrics.com/select/0/prometheus/graph/)
   - **Debug tools:** the official docs list sub-playgrounds for a cardinality explorer, WITH-expression expansion, a metric relabel debugger, and downsampling and retention filter debuggers. [Source](https://docs.victoriametrics.com/victoriametrics/#playgrounds)
   - **Access:** free, no login. **Data:** your queries run on their server against their data. **Level:** L2-L3.
   - **Topics:** `prometheus-grafana`, `prometheus-alertmanager` (relabel debugger), `slo`, `perf-deep-dive`.

8. **VictoriaLogs playground**: https://play-vmlogs.victoriametrics.com/
   - **What it does:** a public LogsQL UI over live Kubernetes and OTel-demo logs. It has stream fields such as `k8s.namespace.name` and `service.name`, plus a hits graph and a live tail. [Source](https://play-vmlogs.victoriametrics.com/)
   - **Access:** free, no login. **Level:** L2. **Topics:** `logs-loki`, `grafana-loki-ops`.
   - **Caveat:** LogsQL is not LogQL (see Inferences).

9. **Registry Explorer (explore.ggcr.dev)**: https://explore.ggcr.dev/
   - **What it does:** browse a public registry or image interactively, drill into manifests and layers, and explore each layer's filesystem. Accepts `?image=` and `?repo=` links. Runs on Cloud Run using google/go-containerregistry. [Source](https://explore.ggcr.dev/)
   - **Access:** free, browser. **Data:** the image reference goes to their server, which pulls public images; it is not usable for a private Harbor. **Maintained:** source repo `jonjohnsonjr/dagdotdev` pushed 2026-06-16. [Source](https://api.github.com/repos/jonjohnsonjr/dagdotdev) **Level:** L2-L3.
   - **Topics:** `dockerfile` (layers), `docker-engine`, `harbor-ops` (manifest, digest, signatures and SBOM tags).

10. **Kubernetes Visual Handbook**: https://k8s-info.pages.dev/docs/intro
    - **What it does:** an open-source handbook claiming "65+ interactive visualizers and simulations", from Pod lifecycle to NetworkPolicies. It is organised in 5 phases from Foundations to Expert, and includes RBAC, observability and GitOps paths. [Source](https://k8s-info.pages.dev/docs/intro)
    - **Access:** free, browser, no sign-up. **Maintained:** unknown; no author or repo was identified. **Level:** L0-L3.
    - **Topics:** `k8s-architecture`, `k8s-workloads`, `k8s-networking`, `k8s-scheduling-storage`.

11. **Webernetes demo (ngrok)**: https://webernetes-demo.ngrok.app/
    - **What it does:** a subset of Kubernetes ported to run entirely in the browser. The live demo shows 3 kubelet nodes, Deployments, Services, Namespaces and Events tables. [Source](https://webernetes-demo.ngrok.app/)
    - **Caveat:** it does not run real Docker Hub images; images are defined in TypeScript. [Source (search snippet of repo README via secondary summaries)](https://www.developersdigest.tech/blog/webernetes-kubernetes-browser-typescript)
    - **Access:** free, client-side, Apache-2.0. **Maintained:** repo created 2026-06-16, pushed 2026-08-13, 1.3k stars. [Source](https://api.github.com/repos/ngrok/webernetes) **Level:** L1-L3.
    - **Topics:** `k8s-architecture`, `k8s-workloads`.

12. **OpsGraph visualisers**: https://opsgraph.pages.dev/
    - **CI/CD Pipeline Visualizer:** covers GitHub Actions, GitLab CI, Jenkins declarative, Azure and CircleCI. It shows jobs, `needs` dependencies, matrices, the critical path, and detects circular dependencies. [Source](https://opsgraph.pages.dev/tools/pipeline-visualizer/)
    - **Kubernetes Manifest Visualizer:** draws Deployment, Service, Ingress, ConfigMap, Secret and PVC relationships from label selectors, volume claims and routing rules. [Source](https://opsgraph.pages.dev/tools/kubernetes-visualizer/)
    - **Others:** a Docker Compose visualizer and a Terraform HCL diagram generator. [Source](https://opsgraph.pages.dev/)
    - **Access:** free, no sign-up. **Data:** "100% in your browser". **Caveat:** share links encode your config in the URL. [Source](https://opsgraph.pages.dev/tools/pipeline-visualizer/)
    - **Maintained:** unknown; © 2026, owner not identified. **Level:** L1-L2.
    - **Topics:** `ci-debugging`, `gitlab-ci-advanced`, `jenkins`, `compose-volumes`, `k8s-workloads`, `terraform`.

13. **Composerize, Decomposerize, Composeverter**: https://www.composerize.com/
    - **What it does:** converts `docker run` commands to `compose.yaml`, with options for Compose spec version, indentation and merging into an existing file. The page links Decomposerize (compose to `docker run`) and Composeverter (converts between Compose file formats). It shows "built with v1.7.6". [Source](https://www.composerize.com/)
    - **Access:** free, browser. **Maintained:** repo pushed 2026-10-23, 3.8k stars. [Source](https://api.github.com/repos/composerize/composerize) **Level:** L1.
    - **Topics:** `docker-basics`, `compose-volumes`, `dokploy` (compose apps).

14. **Docker2Kube**: https://docker2kube.app.enting.org/
    - **What it does:** paste docker-compose or a `docker run` command and get Kubernetes manifests (page live: "docker-compose OR docker command → Kubernetes"). [Source](https://docker2kube.app.enting.org/)
    - **Data:** where processing happens was not confirmed (see Gaps). **Maintenance:** unverified (the GitHub API was rate-limited). **Level:** L1-L2.
    - **Topics:** `compose-volumes`, `k8s-workloads`, `swarm` (migration thinking).

15. **Kompose (install)**: https://kompose.io/
    - **What it does:** the official Compose-to-Kubernetes/OpenShift converter (`kompose convert -f compose.yaml`). It is described as "An official Kubernetes project" and a graduated incubator project. [Source](https://kompose.io/)
    - **Access:** install required. **Data:** local. **Maintained:** repo pushed 2026-11-06, 10.6k stars. [Source](https://api.github.com/repos/kubernetes/kompose) **Level:** L2.
    - **Topics:** `compose-volumes`, `k8s-workloads`, `helm-kustomize`.

16. **Kubernetes YAML Generator (Octopus Deploy)**: https://k8syaml.com/
    - **What it does:** a form-driven generator for Deployments with live YAML output. Fields cover strategy, volumes, containers, DNS policy and config, host networking, pod security context, pod and node affinity, tolerations, annotations, service account and readiness gates. [Source](https://k8syaml.com/)
    - **Access:** free, no sign-up. **Data:** unverified. **Maintained:** unknown. **Level:** L1-L2.
    - **Topics:** `k8s-workloads`, `k8s-scheduling-storage`, `cka-exam`.

17. **Kubernetes NetworkPolicy viewer**: https://artturik.github.io/network-policy-viewer/
    - **What it does:** renders NetworkPolicy manifests as a graph of pods, namespaces, ports and IP blocks; a sample policy loads on open. [Source](https://artturik.github.io/network-policy-viewer/)
    - **Access:** free. **Data:** static GitHub Pages, so presumably client-side. **Maintained:** low; repo last pushed 2024-11-28, 34 stars. [Source](https://api.github.com/repos/artturik/network-policy-viewer) **Level:** L2.
    - **Topics:** `k8s-networking`, `cka-exam`.

18. **ValidKube (Komodor)**: https://validkube.com/
    - **What it does:** paste YAML and pick Validate (kubeconform), Clean (kubectl-neat), Secure (Trivy), Audit (Polaris), Secure (Kubescape) or SBOM (Trivy). [Source](https://validkube.com/)
    - **Data:** server-side, because Trivy, Polaris and Kubescape run on a backend (inference from the tool set). **Maintained:** stale; the footer says "© Komodor 2022" and the repo was last pushed 2024-01-29. [Source](https://api.github.com/repos/komodorio/validkube) **Level:** L2.
    - **Topics:** `k8s-workloads`, `k8s-troubleshooting`.

19. **jq playground (official)**: https://play.jqlang.org/
    - **What it does:** the official jq playground (MIT, `jqlang/playground`). "All jq queries and HTTP requests to fetch JSON are processed locally in your browser"; "Snippets are only sent to the server when you choose to share them." [Source](https://play.jqlang.org/)
    - **Maintained:** repo pushed 2026-10-25. [Source](https://api.github.com/repos/jqlang/playground) **Level:** L1-L2.
    - **Topics:** `k8s-troubleshooting` (`kubectl -o json | jq`), `bash-scripting`, `ci-debugging`.

20. **JSONPath Online Evaluator**: https://jsonpath.com/
    - **What it does:** an RFC 9535 JSONPath evaluator (parser: jsonpath-js) with output paths and Share. [Source](https://jsonpath.com/)
    - **Maintained:** repo pushed 2026-06-01, 699 stars. [Source](https://api.github.com/repos/ashphy/jsonpath-online-evaluator) **Level:** L1-L2.
    - **Topics:** `cka-exam`, `k8s-architecture` (kubectl output).
    - **Caveat:** kubectl JSONPath differs from RFC 9535 (see Inferences).

21. **crontab.guru**: https://crontab.guru/
    - **What it does:** "The quick and simple editor for cron schedule expressions", made by Cronitor. The page also advertises Cronitor's paid monitoring; the editor itself needs nothing. [Source](https://crontab.guru/)
    - **Level:** L0-L1. **Topics:** `k8s-workloads` (CronJob `schedule`), `bash-scripting`, `grafana-loki-ops` (retention and compaction jobs).

22. **YAML Multiline Strings**: https://yaml-multiline.info/
    - **What it does:** an interactive explainer of YAML flow vs block scalars (`|`, `>`, chomping indicators) with live results; it carries EthicalAds. [Source](https://yaml-multiline.info/)
    - **Level:** L1. **Topics:** `helm-kustomize`, `gitlab-ci-advanced` (multi-line `script:`), `k8s-workloads` (ConfigMaps), `ansible`.

23. **Helm Playground (paulvollmer)**: https://paulvollmer.net/helm-playground/
    - **What it does:** a template editor with "Render Output", using a WASM build of Helm's engine. The page loads "Helm Renderer". [Source](https://paulvollmer.net/helm-playground/)
    - **Maintained:** repo pushed 2026-10-19, 15 stars; the search snippet describes it as early stage and compiling `helm.sh/helm/v3/pkg/engine` to WebAssembly. [Source](https://api.github.com/repos/paulvollmer/helm-playground) **Level:** L2.
    - **Topics:** `helm-kustomize`.
    - **Alternative:** helm-playground.com is the better-known equivalent but is in known_domains.

24. **Terraform Visual (hosted)**: https://hieven.github.io/terraform-visual/
    - **What it does:** upload `terraform show -json plan.out > plan.json` and get an interactive plan graph. [Source](https://hieven.github.io/terraform-visual/)
    - **Data:** the bundle uses `FileReader`/`readAsText`, which suggests the file is read in the browser, but the page also loads Google Analytics. The README offers an npm or Docker CLI for people who "don't like to upload Terraform plan to public internet". [Source](https://raw.githubusercontent.com/hieven/terraform-visual/master/README.md)
    - **Maintained:** repo pushed 2026-10-31. [Source](https://api.github.com/repos/hieven/terraform-visual) **Level:** L2.
    - **Topics:** `terraform`, `terraform-opentofu`.

25. **HCL Playground**: https://hcl-playground.com/
    - **What it does:** evaluate HCL expressions in the browser UI. Its `app.js` lists available engines (Terraform and Tofu) and POSTs code to `/evaluate`, so evaluation is **server-side**. [Source](https://hcl-playground.com/)
    - **Maintained:** experimental; repo has 0 stars, pushed 2026-06-28. [Source](https://api.github.com/repos/scottx611x/hcl-playground) **Level:** L2.
    - **Topics:** `terraform`, `terraform-opentofu` (functions, `for` expressions).

26. **Live Jinja Renderer and Parser (Pyodide)**: https://keshav-madhav.github.io/live_jinja/
    - **What it does:** runs Python's Jinja2 in the browser via Pyodide, with selectable versions from 2.10.1 to 3.1.4, JSON or form variables, whitespace view and saved templates. [Source](https://keshav-madhav.github.io/live_jinja/)
    - **Data:** client-side. **Maintained:** small project, repo pushed 2025-11-11, 3 stars. [Source](https://api.github.com/repos/Keshav-Madhav/live_jinja) **Level:** L1-L2.
    - **Topics:** `ansible`, `ansible-practice`.
    - **Caveat:** plain Jinja2, so it has no Ansible filters.

27. **Ansible Template Tester (sivel)**: https://ansible.sivel.net/test/
    - **What it does:** supply YAML variables and a Jinja template and render it with Ansible's templating; a "Raw" mode is included. Its `app.js` POSTs `{variables, template, tag}` to `render`, so it is **server-side**. [Source](https://ansible.sivel.net/test/)
    - **Maintained:** repo last pushed 2023-12-14; the page sat at "Loading ..." during the check, and the backend was not exercised. [Source](https://api.github.com/repos/sivel/ansible-template-ui) **Level:** L2.
    - **Topics:** `ansible`, `ansible-practice`.

28. **Phippy books (CNCF)**: https://www.cncf.io/phippy/
    - **What it does:** "The Illustrated Children's Guide to Kubernetes" and "Phippy Goes to the Zoo" can be read online; the other titles (Wasm, trust, cloud-native recovery) are PDFs. [Source](https://www.cncf.io/phippy/)
    - **Level:** L0. **Topics:** `k8s-architecture`, `docker-basics`.

29. **Kubesec hosted scan**: https://kubesec.io/
    - **What it does:** scores manifests for security risk. The hosted v2.kubesec.io/scan is a POST API used for the demo; there is no paste form. The CLI, Docker image and local HTTP server keep data local. [Source](https://kubesec.io/)
    - **Maintained:** repo pushed 2026-10-08. [Source](https://api.github.com/repos/controlplaneio/kubesec) **Level:** L2.
    - **Topics:** `k8s-workloads`, `k8s-incidents`.
    - **Recommendation:** list it only as a local tool.

**Asked-for tools whose only home is github.com.** github.com is in known_domains, so these are listed for completeness only, unranked and install-only:
- **Rover:** interactive Terraform plan and state explorer, run via Docker on localhost; repo pushed 2025-07-30. [Source](https://api.github.com/repos/im2nguyen/rover); [usage](https://blog.brightcoding.dev/2026/09/27/im2nguyenrover-interactive-terraform-plan-visualization-in-your-browser)
- **Inframap:** builds a graph from tfstate or HCL; repo pushed 2026-04-23. [Source](https://api.github.com/repos/cycloidio/inframap)
- **rbac-tool `viz`:** produces a dot or HTML graph of cluster RBAC; repo pushed 2025-02-13. [Source](https://api.github.com/repos/alcideio/rbac-tool)
- **RBAC Wizard:** in-cluster UI; repo pushed 2026-01-02. [Source](https://api.github.com/repos/pehlicd/rbac-wizard)
- **kube-scheduler-simulator:** SIG project; you create nodes and pods and see each scheduler plugin's filter and score decisions; runs via docker compose; repo pushed 2025-09-21. [Source](https://api.github.com/repos/kubernetes-sigs/kube-scheduler-simulator); [Source](https://kubernetes.io/blog/2025/04/07/introducing-kube-scheduler-simulator/) (the second link is on kubernetes.io, which is in known_domains, and is cited for the description only)
- **dive:** explores image layers; repo pushed 2026-11-02, 54.7k stars. [Source](https://api.github.com/repos/wagoodman/dive)

### Inferences
- **Topic coverage.** The best "Protocol Explorer-like" experiences are:
  - #1 Kubesimplify (animated, step-through);
  - #10 the Visual Handbook;
  - #11 Webernetes;
  - #12 OpsGraph.

  Linters and validators (#2, #3, #4, #5) are the most reliable picks because they wrap upstream engines compiled to WASM. Suggested placement:
  - `k8s-architecture` and `cka-exam`: #1 plus #10.
  - `dockerfile`: #3 plus #9.
  - `gitops-argocd`: #2 plus #6.
  - `logs-loki`: #5.
  - `prometheus-grafana`: #7.
- **Dialect caveats to state in the handbook:**
  - **MetricsQL:** a PromQL superset. Queries that work on play.victoriametrics.com can fail on real Prometheus, so use it to *read* PromQL results, not to learn exact Prometheus semantics.
  - **LogsQL (VictoriaLogs):** a different language from Loki's LogQL. The playground teaches log-filtering thinking, not LogQL syntax.
  - **kubectl JSONPath:** uses `{}` templates and `range`/`end`, unlike RFC 9535, so jsonpath.com builds intuition but expressions may need adapting.
  - **Live Jinja:** runs plain Jinja2, so Ansible filters (`ansible.utils`, `default(omit)` behaviour) won't exist there.
- **Level spread.** L0-L1 entries (Phippy, crontab.guru, yaml-multiline, Composerize) suit early study paths. L3 tools (VMUI trace and relabel, Registry Explorer, Kubesimplify kube-proxy modes) suit `perf-deep-dive`, `harbor-ops` and `k8s-incidents`.

### Gaps
- Docker2Kube's processing location and maintenance were not confirmed. The GitHub API was rate-limited for `sharevb/docker2kube` and the JS was not inspected.
- k8syaml.com: no repo was found (`OctopusDeploy/k8syaml` returns 404), so maintenance and data handling are unknown. It is a generator, so you normally type into its form rather than paste secrets.
- The Kubernetes Visual Handbook (k8s-info.pages.dev) and OpsGraph have no identifiable author or repo, so their long-term maintenance is unknown.
- The level ratings are this researcher's judgement, not taken from a source.

## Q2. Where pasted data goes (privacy warnings)

### Takeaway
For manifests with Secrets, plan or state JSON, and CI files with tokens, the safe set is the client-side group: kube-score, hadolint, actionlint, OTelBin (browser-only mode), play.jqlang.org, OpsGraph, Live Jinja and the NetworkPolicy viewer. ValidKube, HCL Playground, Ansible Template Tester, Kubesec's hosted API and any "Share" button send content to a server.

### Cited Findings
- kube-score.com says "running 100% in your browser, no data is sent to any server". — [kube-score](https://kube-score.com/)
- OpsGraph says CI configs and manifests "never leave your machine", but share links encode the workflow in the URL. — [OpsGraph pipeline](https://opsgraph.pages.dev/tools/pipeline-visualizer/), [OpsGraph k8s](https://opsgraph.pages.dev/tools/kubernetes-visualizer/)
- play.jqlang.org processes locally; snippets go to the server only when shared. — [play.jqlang.org](https://play.jqlang.org/)
- OTelBin defaults to "Validation: Browser-only" and offers an optional distribution-specific validation, which is likely server-side (see Inferences). — [OTelBin](https://www.otelbin.io/)
- HCL Playground POSTs code to `/evaluate`, and lists and installs engine versions server-side. — [hcl-playground.com](https://hcl-playground.com/)
- Ansible Template Tester POSTs variables and the template to `render`. — [ansible.sivel.net](https://ansible.sivel.net/test/)
- Kubesec's hosted service receives your file via POST to v2.kubesec.io/scan, and the page doesn't say how submitted data is handled. — [kubesec.io](https://kubesec.io/)
- Terraform Visual's README itself flags the concern of uploading a plan "to public internet" and offers a local CLI. — [README](https://raw.githubusercontent.com/hieven/terraform-visual/master/README.md)
- Registry Explorer runs on Cloud Run and pulls images server-side, which is fine for public images and useless for private Harbor projects. — [explore.ggcr.dev](https://explore.ggcr.dev/)

### Inferences
- **Terraform plan JSON:** it contains resolved variable values, including sensitive ones unless the provider marks them sensitive. The handbook should say: use local tools (Terraform Visual CLI, Rover, Inframap) for real plans, and the hosted page only with a lab plan.
- **ValidKube:** must be server-side, because Trivy, Polaris and Kubescape can't run in the browser. Paste only sanitised manifests, never `kind: Secret` with real data.
- **OTelBin distribution-specific validation:** likely server-side, since the default mode is labelled "Browser-only". This was not confirmed.
- **Any "Share" or permalink button** (OTelBin, jq, jsonpath.com, OpsGraph, Live Jinja) should be treated as publishing the content.

### Gaps
- OTelBin's server-side validation and share storage, and k8syaml.com's and Docker2Kube's data paths, were not confirmed. Confirming them would need network traces of a submission, which the rules forbid.

## Q3. Dead, blocked or rejected tools (do not link)

### Takeaway
Several commonly recommended tools are gone or unusable:
- Play with Docker is deprecated and unavailable from 1 March 2026.
- Tufin's network-policy viewer domain no longer resolves.
- oci.dag.dev sits behind a bot challenge.
- The EngineersUniverse namespaces/cgroups simulator is paid.

### Cited Findings
- **Play with Docker:** "Deprecation notice: Play with Docker will be unavailable starting March 1, 2026. Visit Docker Docs for supported labs and guides." — [labs.play-with-docker.com](https://labs.play-with-docker.com/)
- **Tufin network-policy viewer:** orca.tufin.io gave DNS ENOTFOUND on 2026-11-08. It was previously announced on the Kubernetes forum. — [forum post](https://discuss.kubernetes.io/t/a-kubernetes-network-policy-viewer/7953)
- **oci.dag.dev:** the newer sibling of Registry Explorer returned HTTP 403 with a Cloudflare "Performing security verification" page. It was not bypassed, per the rules. — [oci.dag.dev](https://oci.dag.dev/)
- **EngineersUniverse Container Isolation Simulator:** covers CPU quota throttling, the cgroup OOM kill and the PID namespace, but sits behind a $5.99-$14.99 paywall, so it is rejected as not free. — [engineersuniverse.com](https://engineersuniverse.com/labs/ai-computing/cloud-computing/container-isolation)
- **yewolf.fr GitLab CI Visualizer:** said to simulate rules for branch, source and variables. The page only showed "yewolf.fr is booting up...", so it is unverified. — [yewolf.fr](https://yewolf.fr/projects/gitlab-ci-visualizer)
- **jqplay.org:** a community project whose repo was last pushed 2024-04-29 (per a search snippet); play.jqlang.org is the official playground. — [search snippet via ecosyste.ms](https://awesome.ecosyste.ms/projects/github.com%2Fowenthereal%2Fjqplay)
- **Ansible playgrounds:** the browser Ansible playgrounds found (KodeKloud, LabEx, Killercoda) are either in known_domains or require sign-in for full environments. — [LabEx](https://labex.io/playgrounds/ansible) (in known_domains; snippet only)

### Inferences
- If the handbook currently links Play with Docker for `docker-basics` or `swarm`, replace it. For Swarm, labs.iximiuz.com and Killercoda are the remaining free options, but both are already known.

### Gaps
- No free, live, no-sign-up browser tool for teaching **namespaces/cgroups** was found outside known domains (iximiuz labs, Julia Evans/wizardzines).

## Q4. Coverage gaps by requested category

### Takeaway
Well covered:
- Dockerfile linting;
- Kubernetes YAML scoring and generation;
- Compose conversion;
- GitHub Actions lint;
- OTel config;
- JSON, YAML and cron helpers;
- Kubernetes architecture explainers.

Weak or missing:
- an in-browser RBAC visualiser;
- an official GitLab CI lint without login;
- a Jenkinsfile playground;
- a free LogQL playground outside grafana.com;
- a namespaces/cgroups teaching tool.

### Cited Findings
- **RBAC visualisers** all run against a live cluster or are installed: rbac-tool `viz`, rback, Krane, RBAC Wizard. ARMO's is part of a commercial platform. No paste-YAML browser RBAC graph was found. — [search results summary: rbac-tool](https://awesome.ecosyste.ms/projects/github.com%2Falcideio%2Frbac-tool), [ARMO](https://www.armosec.io/lp-rbac/)
- **GitLab CI:** GitLab's own pipeline editor and visualiser live inside GitLab, and a static `.gitlab-ci.yml` visualiser is a long-open feature request. OpsGraph (#12) is the only verified offline-style visualiser. — [GitLab issue 241722](https://gitlab.com/gitlab-org/gitlab/-/issues/241722)
- **Helm:** browser renderers are WASM re-implementations that may differ from `helm template` in edge cases. — [search summary incl. th-helm-playground note](https://github.com/tobiashochguertel/th-helm-playground-frontend)

### Inferences
- **GitLab CI lint:** for the on-prem reader, the practical route is their own GitLab instance's CI Lint page (`/-/ci/lint`) or the pipeline editor. Document it in the handbook rather than linking a third-party site.
- **LogQL:** the Loki query analyzer and play.grafana.org are in known domains, so no new LogQL tool is needed.

### Gaps
- **Jenkins:** no free browser Jenkinsfile linter or visualiser was found apart from OpsGraph's Jenkins mode (#12). Jenkins' own linter needs a running controller.
- **gitlab.com CI Lint without login:** not verified; signing in was not allowed.
- **Reddit, Stack Overflow and Server Fault** were not consulted, per the rules. Community discovery relied on search, HN mirrors and GitHub metadata.
