# 31 — Learn: Kubernetes Zero to Hero (CKA-Aligned)

This is the Kubernetes learning module of the handbook. It takes you from "what is a pod" to
CKA-level troubleshooting on a kubeadm cluster with containerd, which is the cluster you will
build in your homelab and the cluster type the CKA exam uses. Every topic follows the same
loop: understand the concept, look at it on a real cluster, build it, break it on purpose,
fix it, and only then move on. The command reference for incidents lives in
[Kubernetes reference](15-kubernetes.md); the incident playbook lives in
[Containers & Kubernetes playbook](26-playbook-containers-k8s.md). This module explains the
*why* behind both.

Sample outputs are illustrative (Ubuntu 24.04 nodes, Kubernetes v1.34, containerd 1.7/2.x).
Lab nodes use the private range 192.168.56.0/24, pods 10.244.0.0/16, Services 10.96.0.0/12.

**Who this module serves.** Four of the five career stages in the
[career ladder](40-career-ladder.md). A **Junior** (L1) reads pod status, logs and rollouts on a
cluster someone else built. A **Mid-level** engineer (L2) troubleshoots pods, Services, DNS and
Ingress with evidence. A **Senior** (L3) builds, secures and upgrades kubeadm clusters and passes
the CKA. A **Senior/Lead** (L4) owns backups, certificates, upgrades and game days, and teaches the
method. A **Fresher** (L0) should finish [Linux](27-learn-linux.md) and [Docker](30-learn-docker.md)
first and read only areas 1–2 here for vocabulary. Section 0 maps every area to a stage, and every
topic carries a tag such as [L2 · Mid].

---

## 0. How to use this module

### Who this module is for

Kubernetes sits at L3 (Platform) in your Ops Ladder, but in a real team you meet it much earlier.
What changes from stage to stage is what you are trusted to do with it. Find your stage, do its
focus areas first, and use the matching part of the exit test (area 23) to decide when to move up.
The stage names match the [career ladder](40-career-ladder.md).

| Stage | Tag | What you are expected to do with Kubernetes | Focus areas |
|---|---|---|---|
| Fresher (0–1 yr) | L0 · Fresher | Nothing on a shared cluster yet. Finish Linux and Docker, then learn the vocabulary: pod, Deployment, Service, desired state | prerequisites P1–P3, areas 1–2 (read only) |
| Junior (1–2 yrs) | L1 · Junior | Operate an existing cluster safely: right context and namespace, `get`/`describe`/`logs`, read pod status, roll back a bad deploy, save events | 1, 4, 5, 6, 10, 18 (events and logs) |
| Mid-level (2–4 yrs) | L2 · Mid | Explain any "it is running but broken" incident with evidence: probes, Services and EndpointSlices, DNS, Ingress, config, scheduling, image pulls | 2, 5–13, 16, 17, 18, 20 |
| Senior (4–7 yrs) | L3 · Senior | Build, secure and upgrade kubeadm clusters: containerd, CNI, RBAC, NetworkPolicies, Harbor with a private CA, control-plane repair; pass the CKA | 3, 7–9 (internals), 11–17, 19, 21, 22 |
| Senior/Lead (5+ yrs) | L4 · Lead/SRE | Own reliability: tested etcd restores, certificate and upgrade calendars, game days, runbooks and teaching the method to others | 19, 20, 22, exit test part D |

You already work at about L2 on-prem with Docker and Dokploy. Skim the L1 topics, do the L1 and L2
exit questions in area 23 to prove it, and spend your real hours on the L3 areas and the drills:
that is where the CKA and your homelab break-and-fix live.

### Learning path

Work through the areas in this order. Each row carries a level and career-stage tag from your Ops
Ladder (L0 Foundations, L1 Operator, L2 Troubleshooter, L3 Platform, L4 SRE) and the
[career ladder](40-career-ladder.md). The tag says at which stage you are expected to *own* the
area at work. Kubernetes leans hard on L1 (systemd, journald, ports) and L2 (routing, DNS, TLS)
skills, so the prerequisites are listed first.

| # | Area | Tag | Why it is in this position |
|---|---|---|---|
| P1 | systemd units, journald, ports and sockets ([Linux](27-learn-linux.md)) | [L1 · Junior] | kubelet and containerd are systemd services; node debugging is journalctl |
| P2 | Routing, DNS, TLS, reverse proxies ([Networking](28-learn-networking.md)) | [L2 · Mid] | Services, CoreDNS and Ingress are these same ideas, virtualised |
| P3 | Images, containers, namespaces, cgroups ([Docker](30-learn-docker.md)) | [L1 · Junior] → [L3 · Senior] | a pod is containers plus shared namespaces |
| 1 | Why Kubernetes and the declarative model | [L1 · Junior] | everything else is "a controller reconciling an object" |
| 2 | Architecture and the life of kubectl apply | [L2 · Mid] | tells you which component to suspect at each failure |
| 3 | Building a kubeadm homelab cluster | [L3 · Senior] | you cannot learn break-and-fix without a cluster you own |
| 4 | kubectl fluency | [L1 · Junior] → [L2 · Mid] | speed and precision; exam time is short |
| 5 | Pods | [L1 · Junior] → [L2 · Mid] | the unit of everything; most incidents start here |
| 6 | Deployments, ReplicaSets, rollouts, HPA | [L1 · Junior] → [L2 · Mid] | how real apps run and roll back |
| 7 | Services | [L2 · Mid] → [L3 · Senior] | the number one "it is running but unreachable" cause |
| 8 | Ingress and the Gateway API | [L2 · Mid] → [L3 · Senior] | your Traefik/Apache knowledge, the Kubernetes way |
| 9 | Cluster DNS | [L2 · Mid] → [L3 · Senior] | second most common "unreachable" cause |
| 10 | ConfigMaps and Secrets | [L1 · Junior] → [L2 · Mid] | CreateContainerConfigError and stale config |
| 11 | Storage | [L2 · Mid] → [L3 · Senior] | Pending PVCs and lost data |
| 12 | Scheduling | [L2 · Mid] → [L3 · Senior] | Pending pods, evictions, OOMKills |
| 13 | Workload types | [L2 · Mid] → [L3 · Senior] | StatefulSet, DaemonSet, Job, CronJob |
| 14 | RBAC and ServiceAccounts | [L3 · Senior] | Forbidden errors, least privilege |
| 15 | NetworkPolicies | [L3 · Senior] | "DNS broke after we added a policy" |
| 16 | Helm and Kustomize | [L2 · Mid] → [L3 · Senior] | how most real clusters are installed |
| 17 | Private registries and Harbor | [L2 · Mid] → [L3 · Senior] | ImagePullBackOff with a private CA |
| 18 | Observability and node-level debugging | [L1 · Junior] → [L3 · Senior] | events, logs, metrics, crictl, kubelet |
| 19 | Cluster maintenance | [L3 · Senior] → [L4 · Lead/SRE] | upgrades, etcd backup/restore, certificates |
| 20 | The troubleshooting method | [L2 · Mid] → [L4 · Lead/SRE] | one repeatable bottom-up walk |
| 21 | CKA exam strategy | [L3 · Senior] | the exam is a speed test of areas 3–20 |
| 22 | Twenty timed break-and-fix drills | [L3 · Senior] → [L4 · Lead/SRE] | where real skill comes from |
| 23 | Self-check and exit test | all stages | proves each stage before you move on |
| 24 | Where to go next | — | what to learn after this module and the CKA |

### Study method

For every ### topic, use the same five steps, in this order:

1. **Read this note** for the topic: concept, key terms, the "see it" commands. Ten to twenty minutes.
2. **Do the matching KodeKloud course lesson** (pointers are at the top of each area, under "Study path") including its practice-test lab. KodeKloud labs are pre-built clusters, so you practise the skill without fighting setup.
3. **Optional video** if a concept still feels fuzzy. Watch at 1.25x; stop as soon as it clicks.
4. **Hands-on lab (test VM only)** from this note on your own kubeadm cluster: build, break, fix. This is the step that matters most; do not skip the "break" part.
5. **Related playbook**: read the matching section of [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) and the commands in [Kubernetes reference](15-kubernetes.md), so the next real incident finds you with a page you have already used.

Write a five-line note after each lab (symptom, your first wrong guess, the evidence that settled
it, the fix, what you will check first next time). That is the same habit the Ops Ladder asks for
after real incidents, and those notes become your CKA revision sheet.

### Lab environment you need

| Item | Recommendation | Why |
|---|---|---|
| Nodes | 3 Ubuntu 24.04 VMs: cp1 (2 vCPU, 4 GB), w1 and w2 (2 vCPU, 2–4 GB) | kubeadm needs at least 2 CPUs and 2 GB on the control plane |
| Network | one host-only/bridged network, e.g. 192.168.56.10/11/12 | nodes must reach each other on a stable, non-NAT address |
| Hypervisor | KVM/virt-manager, Proxmox, VirtualBox, VMware, or Multipass | anything that supports snapshots |
| Snapshots | take one after "cluster healthy", and before every break lab | the safe undo for every destructive experiment |
| Fallback | KodeKloud playgrounds and Killercoda | for days you do not want to start VMs |

> Never practise break-and-fix on a cluster that serves anything real, and never on the Dokploy
> or Apache servers from work. Everything marked "test VM only" assumes you can roll back to a
> snapshot in one click.

### Conventions in this module

Placeholders are UPPERCASE: POD, NS (namespace), NODE, DEPLOY, SVC, CONTAINER, IMAGE, HOST, PORT,
DOMAIN. Lab examples use concrete names (namespace `shop`, deployment `web`) so they are
copy-pasteable. `k` is an alias for `kubectl` (set up in area 4); full `kubectl` is used in most
examples so they work anywhere.

Each topic has the same blocks: **Concept**, **Key terms**, **See it on a real system**,
**Hands-on lab (test VM only)**, **How it breaks**, **Why it matters for troubleshooting** and
**Next step**.

> `kubectl delete`, `--force --grace-period=0`, `kubeadm reset` and etcd restores are
> destructive. Every time they appear below there is a warning and a safer first move
> (`kubectl get`/`describe` first, `--dry-run=server`, `kubectl diff`, scaling to zero,
> `rollout restart` or a VM snapshot). Make "look before you delete" a reflex.

---

## 1. Why Kubernetes and the declarative model

> 📚 **Study path:** 1) KodeKloud: *Kubernetes for the Absolute Beginners – Hands-on Tutorial* — Kubernetes Overview, then PODs, ReplicaSets, Deployments ([course](https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners-hands-on-tutorial); free taster: *Crash Course: Kubernetes For Absolute Beginners*, [course](https://kodekloud.com/courses/crash-course-kubernetes-for-absolute-beginners)) · 2) Note: this area, then the Swarm topics in [Docker](30-learn-docker.md) for the comparison · 3) Video: KodeKloud *Kubernetes Crash Course: Learn the Basics and Build a Microservice Application* ([YouTube](https://www.youtube.com/watch?v=XuSQU5Grv1g), 130 min) · 4) Practice: the labs below on your cluster, or the KodeKloud [Kubernetes multi-cluster playground](https://kodekloud.com/playgrounds/playground-kubernetes-multi-cluster) until your own cluster exists (area 3).

### Desired state and reconciliation loops

**Level:** [L1 · Junior] · CKA: Cluster Architecture

**Concept.** On your Apache servers you work *imperatively*: "start this service", "edit this
vhost", "restart Apache". If the process dies at 3 a.m., it stays dead unless systemd restarts it.
Kubernetes works *declaratively*: you write down what should exist ("3 copies of web:1.4, reachable
as `web` on port 80") and store it in the cluster. Small programs called **controllers** run
forever, compare *desired state* (the `spec` you wrote) with *actual state* (the `status` they
observe), and act to close the gap. This is called **reconciliation**. It is level-triggered: a
controller does not care *how* things drifted, only *that* they differ now. Think of it as
systemd's `Restart=always`, applied to every object in a whole cluster.

```
            you write (kubectl apply)                        controllers act
   +--------------------------------+           +-----------------------------------+
   |  DESIRED STATE  (.spec)        |           |  ACTUAL STATE  (.status)          |
   |  Deployment web: replicas 3    |           |  pods running: 2                  |
   |  image web:1.4                 |           |  (one node died)                  |
   +---------------+----------------+           +----------------+------------------+
                   |                                             ^
                   |   watch            +-----------------+      |  observe
                   +------------------> |  controller     | -----+
                                        |  loop: diff ->  |
                                        |  create 1 pod   | ---> new pod scheduled elsewhere
                                        +-----------------+
```

**Key terms**

| Term | Meaning |
|---|---|
| Object | A record in the cluster (Pod, Deployment, Service...) with `metadata`, `spec`, `status` |
| spec | What you want. You (or a tool) write it |
| status | What exists. Controllers and the kubelet write it |
| Controller | A loop that watches objects and makes reality match spec |
| Reconcile | One pass of "read desired, read actual, act on the difference" |
| generation / observedGeneration | `metadata.generation` bumps on every spec change; `status.observedGeneration` shows which spec the controller has processed |
| Manifest | The YAML file describing objects; belongs in Git |
| Label / selector | Key=value tags and queries that link objects (a Service finds pods by labels) |

**See it on a real system**

```bash
# Desired vs actual for a Deployment, in one line
kubectl -n shop get deploy web -o jsonpath='{.spec.replicas} wanted, {.status.readyReplicas} ready, generation {.metadata.generation}, observed {.status.observedGeneration}{"\n"}'

# Watch the controllers react in real time (second terminal)
kubectl -n shop get pods -w
```

```
3 wanted, 2 ready, generation 4, observed 4
```

→ The controller has seen the latest spec (generation 4 = observed 4) but only 2 of 3 replicas are
ready. The gap is in *actual* state: look at pods. If observed were lower than generation, the
controller itself would be behind or down (look at kube-controller-manager).

**Hands-on lab (test VM only)**

**Step 1 — build.** Create a namespace and a Deployment, then watch it in a second terminal.

```bash
kubectl create namespace shop
kubectl -n shop create deployment web --image=nginx:1.27 --replicas=3
kubectl -n shop get pods -o wide -w        # leave running in terminal 2
```

**Step 2 — break (simulate a crash).** Remove one pod by hand. Deleting a pod managed by a
Deployment is safe in a lab because the ReplicaSet recreates it; on a real cluster prefer
`kubectl -n NS rollout restart deploy/DEPLOY`, which replaces pods gradually.

> Warning: `kubectl delete` is immediate and has no undo. Run the `get` first and read the name
> twice. Never delete a bare pod (no controller) in production: nothing will recreate it.

```bash
kubectl -n shop get pods -l app=web                 # look first
kubectl -n shop delete pod "$(kubectl -n shop get pods -l app=web -o name | head -1 | cut -d/ -f2)"
```

**Step 3 — observe.** In terminal 2 a new pod appears within a second, with a new name. Nobody
told Kubernetes to "start" it; the ReplicaSet controller noticed 2 is not 3.

**Step 4 — break the desired state instead.** Change the image to one that does not exist:

```bash
kubectl -n shop set image deploy/web nginx=nginx:9.99-doesnotexist
kubectl -n shop get pods
```

**Step 5 — fix declaratively.** Export the good state to a file, put it in Git, and apply it.
From now on the file is the truth, not your memory.

```bash
kubectl -n shop rollout undo deploy/web
kubectl -n shop get deploy web -o yaml > web-deploy.yaml   # then strip status/uid/resourceVersion
kubectl apply -f web-deploy.yaml
```

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Someone edited live objects (`kubectl edit`) and the next Git apply reverted it | "my fix disappeared" | `kubectl -n NS get deploy DEPLOY -o yaml` and compare with Git (`kubectl diff -f FILE`) | [26](26-playbook-containers-k8s.md) |
| Two controllers fight (HPA vs `replicas:` in your manifest, Helm vs manual edits) | replica count flaps | `kubectl -n NS get hpa`; `kubectl -n NS describe deploy DEPLOY` | [26](26-playbook-containers-k8s.md) |
| kube-controller-manager is down | Deployment created, no ReplicaSet, no pods; observedGeneration stuck | `kubectl -n kube-system get pods` | area 20 |
| Wrong label selector | controller creates pods but Service sends no traffic | `kubectl get pods --show-labels` | area 7 |

**Why it matters for troubleshooting.** "What is the controller trying to do, and why can it not
do it?" is the question behind almost every Kubernetes incident. You fix the *desired state* or
the *obstacle*, not the pods. Deleting pods to "fix" things only works when the obstacle was
transient.

**Next step.** Compare this model with what you already run (Docker Swarm under Dokploy), then
learn the components that run these loops (area 2).

### Kubernetes vs Docker Swarm and Dokploy

**Level:** [L1 · Junior] · CKA: background for your Dokploy work

**Concept.** Dokploy runs Docker in **Swarm mode**, which is also a declarative orchestrator:
a Swarm *service* says "N replicas of this image", and Swarm reconciles it. Kubernetes splits that
one Swarm idea into several smaller objects (Deployment, ReplicaSet, Pod, Service, Ingress), each
with its own controller. More objects means more to learn, but also more precise control and far
better debugging surfaces. Your Traefik knowledge carries straight over: in Kubernetes Traefik is
just one possible *ingress controller*.

**Key terms (translation table)**

| Docker Swarm / Dokploy | Kubernetes | Note |
|---|---|---|
| manager / worker node | control plane / worker node | control plane runs apiserver, etcd, scheduler, controller-manager |
| service (replicas, image) | Deployment → ReplicaSet → Pods | Deployment handles rollouts; RS keeps the count |
| task | Pod | a pod can hold several containers |
| stack / compose file | namespace + manifests, or a Helm chart | Helm is the "compose for clusters" |
| overlay network (dokploy-network) | the CNI pod network | every pod can reach every pod by default |
| routing mesh (published port on all nodes) | NodePort Service via kube-proxy | port range 30000–32767 by default |
| Traefik labels on containers | Ingress or HTTPRoute objects | the controller reads objects, not labels |
| docker secret / config | Secret / ConfigMap | mounted as files or env vars |
| `docker service ps` / `logs` | `kubectl get pods` / `kubectl logs` | |
| `docker service update --image` | `kubectl set image` or apply a new manifest | |
| `docker service rollback` | `kubectl rollout undo` | |
| `docker ps` on the node | `crictl ps` on the node | `docker ps` does not show Kubernetes containers |

**See it on a real system**

```bash
# Swarm side (on a Dokploy server)
docker service ls
docker service ps SERVICE --no-trunc

# Kubernetes side
kubectl get deploy,rs,pods,svc,ingress -n shop
kubectl api-resources | wc -l          # how many object types this cluster knows
```

→ `kubectl api-resources` typically lists 50–60 built-in types plus any CRDs. You do not need
them all: Pods, Deployments, Services, Ingress/HTTPRoute, ConfigMaps, Secrets, PVCs, and RBAC
objects cover most daily work.

**apply vs create vs edit vs replace vs patch**

| Command | Style | Use it for | Danger |
|---|---|---|---|
| `kubectl create` | imperative | generating objects fast; one-off creation | fails if the object exists |
| `kubectl apply -f` | declarative | everything that lives in Git | merges; removed fields may linger if not tracked |
| `kubectl edit` | imperative live edit | emergencies and the exam | drift: Git no longer matches the cluster |
| `kubectl patch` | imperative | scripted one-field changes | same drift risk |
| `kubectl replace --force` | delete + recreate | immutable fields (pod spec changes) | pods are killed; brief outage |
| `kubectl diff -f` | read-only | see what apply would change | none: run it before every apply |

**Hands-on lab (test VM only)**

**Step 1 — build.** Write the same app as a manifest and apply it twice. The second apply reports
`unchanged`: applying is idempotent, exactly like a well-written Ansible play.

```bash
kubectl -n shop create deployment api --image=nginx:1.27 --dry-run=client -o yaml > api.yaml
kubectl apply -f api.yaml
kubectl apply -f api.yaml            # deployment.apps/api unchanged
```

**Step 2 — break (create drift).** Edit live: `kubectl -n shop scale deploy api --replicas=5`.

**Step 3 — observe.** `kubectl diff -f api.yaml` now shows the cluster differs from Git.

**Step 4 — fix.** Decide which is true. Usually Git wins: `kubectl apply -f api.yaml`.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| `create` on an existing object | `Error from server (AlreadyExists): deployments.apps "api" already exists` | use `apply` or `diff` | — |
| Changing an immutable field | `The Deployment "api" is invalid: spec.selector: ... field is immutable` | `kubectl replace --force -f FILE` on a lab, or create a new name | area 6 |
| Editing a pod directly | `The Pod "X" is invalid: spec: Forbidden: pod updates may not change fields other than ...` | edit the Deployment instead | area 5 |

**Why it matters for troubleshooting.** The first question in any "it broke after a change"
incident is "what changed?" With declarative manifests in Git, the answer is `git log`; with live
edits, nobody knows. The Ops Ladder's "change management" case starts here.

**Next step.** Learn which component runs which loop, so a symptom points you to a process (area 2).

---

## 2. Architecture and the life of kubectl apply

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Core Concepts: Cluster Architecture, Docker vs ContainerD, etcd, kube-apiserver, kubelet, kube-proxy ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator); notes: [Cluster Architecture](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Core-Concepts/Cluster-Architecture), [Docker vs ContainerD](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Core-Concepts/Docker-vs-ContainerD/page)) · 2) Note: this area, then [systemd](07-services-systemd.md) for the kubelet and containerd units · 3) Video: TechWorld with Nana *Kubernetes Tutorial for Beginners \[FULL COURSE in 4 Hours\]*, the architecture part ([YouTube](https://www.youtube.com/watch?v=X48VuDVv0do)) · 4) Practice: break the scheduler and stop containerd (labs below), then name the broken component from its fingerprint alone.

### Control plane components

**Level:** [L2 · Mid] · CKA: Cluster Architecture

**Concept.** The control plane is the brain. On a kubeadm cluster its components run as
**static pods** on the control-plane node (cp1), started directly by the kubelet from YAML files
in `/etc/kubernetes/manifests`. Only the API server talks to etcd; every other component, and you,
talk to the API server.

```
                         +---------------------------------------------+
   kubectl, kubelets,    |               kube-apiserver :6443           |
   controllers, CI  ---->|  authn -> authz (RBAC) -> admission -> etcd   |
                         +-------+----------------+------------+--------+
                                 |                |            |
                        watch/update      watch/bind     read/write
                                 |                |            |
                 +---------------v---+  +---------v-------+  +-v------------------+
                 | controller-manager|  | kube-scheduler  |  | etcd :2379/:2380   |
                 | :10257            |  | :10259          |  | (cluster database) |
                 +-------------------+  +-----------------+  +--------------------+
```

**Key terms**

| Component | Job | Port | Where it lives (kubeadm) |
|---|---|---|---|
| kube-apiserver | the only front door: REST API, authentication, RBAC, admission, validation, storage in etcd | 6443 | static pod, `/etc/kubernetes/manifests/kube-apiserver.yaml` |
| etcd | consistent key-value store holding every object; Raft consensus; quorum = (n/2)+1 members | 2379 client, 2380 peer | static pod, data in `/var/lib/etcd` |
| kube-scheduler | picks a node for each unscheduled pod (filter, then score), writes the binding | 10259 | static pod |
| kube-controller-manager | runs the built-in controllers: Deployment, ReplicaSet, Node lifecycle, EndpointSlice, Job, CronJob, Namespace, ServiceAccount... | 10257 | static pod |
| cloud-controller-manager | talks to a cloud API (load balancers, node addresses). Absent on bare-metal kubeadm | — | — |
| Admission controllers | plugins inside the API server that mutate or reject requests (LimitRanger, ResourceQuota, PodSecurity...) | — | `--enable-admission-plugins` flag |

**See it on a real system**

```bash
kubectl -n kube-system get pods -o wide            # control plane pods end in -cp1
sudo ls -l /etc/kubernetes/manifests/              # on cp1: the static pod files
kubectl get --raw='/readyz?verbose' | tail -5      # API server's own health checks
sudo ss -ltnp | grep -E ':(6443|2379|2380|10257|10259|10250)\b'   # on cp1
```

```
$ sudo ls -l /etc/kubernetes/manifests/
total 16
-rw------- 1 root root 2552 Sep 21 09:14 etcd.yaml
-rw------- 1 root root 4012 Sep 21 09:14 kube-apiserver.yaml
-rw------- 1 root root 3394 Sep 21 09:14 kube-controller-manager.yaml
-rw------- 1 root root 1463 Sep 21 09:14 kube-scheduler.yaml

$ kubectl get --raw='/readyz?verbose' | tail -5
[+]poststarthook/apiservice-openapiv3-controller ok
[+]poststarthook/apiservice-discovery-controller ok
[+]shutdown ok
readyz check passed
```

→ Four files, four static pods. If you break one of these files, that component disappears, and
`kubectl` may stop working entirely (for the API server and etcd). That is why control-plane
debugging happens on the node with `crictl` and `journalctl`, not with `kubectl`.

**Hands-on lab (test VM only)**

**Step 1 — snapshot cp1.** This lab breaks the scheduler.

**Step 2 — break.** Move the scheduler manifest out of the directory. The kubelet notices within
about 20 seconds and stops the pod. Keep the copy *outside* the manifests directory: the kubelet
tries to run every manifest file it finds there, including backups.

```bash
sudo mv /etc/kubernetes/manifests/kube-scheduler.yaml /root/
kubectl -n kube-system get pods | grep scheduler        # gone after ~20 s
kubectl -n shop create deployment sched-test --image=nginx:1.27
kubectl -n shop get pods -l app=sched-test -o wide
```

**Step 3 — observe.** The new pod is `Pending`, NODE is empty, and `kubectl describe pod` shows
**no events at all**. No "FailedScheduling" event means nobody even tried: that is the signature
of a missing scheduler, not of a full cluster.

**Step 4 — fix.**

```bash
sudo mv /root/kube-scheduler.yaml /etc/kubernetes/manifests/
kubectl -n kube-system get pods | grep scheduler
kubectl -n shop get pods -l app=sched-test -o wide       # now scheduled
```

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| API server down | `The connection to the server 192.168.56.10:6443 was refused - did you specify the right host or port?` | on cp1: `sudo crictl ps -a --name kube-apiserver` | area 20 |
| etcd down or wrong flags | API server restarts in a loop; its log shows `connection refused` to 127.0.0.1:2379 | `sudo crictl logs CONTAINER` | area 20 |
| Scheduler down | pods Pending with no events | `kubectl -n kube-system get pods` | area 20 |
| Controller-manager down | Deployment exists but no ReplicaSet/pods; scaling does nothing | `kubectl -n kube-system get pods` | area 20 |

**Why it matters for troubleshooting.** Each component leaves a distinct fingerprint. Learning
the fingerprints lets you go straight to the right process instead of restarting things at random.

**Next step.** The node side: kubelet, containerd, CNI and kube-proxy.

### Node components: kubelet, containerd, CNI, kube-proxy

**Level:** [L2 · Mid] · CKA: Cluster Architecture, Troubleshooting

**Concept.** Every node (including cp1) runs the **kubelet**, a normal systemd service. It watches
the API server for pods assigned to its node and makes them real by calling the **container
runtime** (containerd) through the **CRI** (Container Runtime Interface, a gRPC API on a unix
socket). containerd uses **runc** to create containers. For networking, containerd calls a **CNI
plugin** (Calico, Flannel, Cilium...) that gives each pod an IP and routes between nodes.
**kube-proxy** (a DaemonSet) turns Service IPs into iptables or nftables rules. **CoreDNS**
(a Deployment) answers cluster DNS. Since Kubernetes 1.24 Docker is not involved at all: on a
Dokploy host, `docker ps` and Kubernetes would be two different worlds even if they shared the
same containerd binary.

```
 Node w1 (Ubuntu 24.04)
 +----------------------------------------------------------------------------+
 |  systemd                                                                   |
 |   +-- kubelet.service ----- CRI gRPC ----> containerd.service              |
 |   |     | (probes, status,                    |  namespace "k8s.io"        |
 |   |     |  static pods,                       +--> containerd-shim -> runc |
 |   |     |  volume mounts)                     |      +-- pause (sandbox)   |
 |   |     |                                     |      +-- app container     |
 |   |     |                                     +--> CNI plugin (/opt/cni/bin)|
 |   |     |                                            veth + pod IP + routes |
 |  pods from DaemonSets:                                                     |
 |   kube-proxy  -> iptables/nftables rules for Service IPs                   |
 |   calico-node / kube-flannel -> pod network between nodes                  |
 +----------------------------------------------------------------------------+
```

**Key terms**

| Term | Meaning | Where to look |
|---|---|---|
| kubelet | node agent; systemd unit | `systemctl status kubelet`, `/var/lib/kubelet/config.yaml` |
| CRI | the API kubelet uses to talk to the runtime | socket `unix:///run/containerd/containerd.sock` |
| containerd | the runtime; pulls images, runs containers | `/etc/containerd/config.toml`, `journalctl -u containerd` |
| pause / sandbox container | holds the pod's network namespace so app containers can restart without losing the IP | `crictl pods` |
| CNI | plugin spec for pod networking | binaries `/opt/cni/bin`, config `/etc/cni/net.d` |
| kube-proxy | implements Service virtual IPs | `kubectl -n kube-system get ds kube-proxy` |
| crictl | CLI that speaks CRI; the `docker ps` of Kubernetes nodes | `/etc/crictl.yaml` |

**See it on a real system**

```bash
systemctl status kubelet containerd --no-pager | grep -E 'Loaded|Active'
sudo crictl pods | head -5
sudo crictl ps | head -5
ls /etc/cni/net.d/ /opt/cni/bin/ | head -20
sudo ctr -n k8s.io containers ls | head -3       # same containers, low-level view
```

```
$ sudo crictl pods | head -4
POD ID          CREATED       STATE   NAME                        NAMESPACE      ATTEMPT   RUNTIME
9e8d7c6b5a4f3   2 hours ago   Ready   web-7c9d8f6b5-2xkqp         shop           0         (default)
4b3a2c1d0e9f8   12 days ago   Ready   kube-proxy-tw9lc            kube-system    0         (default)
1a2b3c4d5e6f7   12 days ago   Ready   calico-node-x8r2d           calico-system  0         (default)
```

→ `crictl pods` lists sandboxes (one per pod); `crictl ps` lists containers. If a pod shows in
`kubectl` but not in `crictl pods` on its node, the kubelet never got as far as the runtime: read
`journalctl -u kubelet`.

**Hands-on lab (test VM only)**

**Step 1 — observe a healthy node.** On w1 run the commands above and note the pod count.

**Step 2 — break.** Stop the runtime: `sudo systemctl stop containerd`.

**Step 3 — observe.** Within about 40 seconds `kubectl get nodes` shows w1 `NotReady`.
`kubectl describe node w1` shows a condition message such as
`container runtime is down` or `PLEG is not healthy`. `journalctl -u kubelet -n 30` shows CRI
connection errors to `/run/containerd/containerd.sock`. After about five minutes (the default
toleration for `node.kubernetes.io/unreachable` and `not-ready`), pods on w1 are marked for
eviction and recreated elsewhere.

**Step 4 — fix.** `sudo systemctl start containerd`, then watch the node return to `Ready`.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| containerd stopped or crashed | node `NotReady`; kubelet log: `connect: no such file or directory` on containerd.sock | `systemctl status containerd` | [26](26-playbook-containers-k8s.md) |
| CNI not installed or broken | node `NotReady`: `container runtime network not ready: NetworkReady=false reason:NetworkPluginNotReady message:Network plugin returns error: cni plugin not initialized` | `ls /etc/cni/net.d` | area 3 |
| kube-proxy broken | pods fine, Service IPs time out | `kubectl -n kube-system logs ds/kube-proxy` | area 7 |
| Disk full on node | `DiskPressure`, evictions, image pulls fail | `df -h /var/lib/containerd /var/lib/kubelet` | [Storage](01-storage-disk.md) |

**Why it matters for troubleshooting.** When `kubectl` says a node is unhealthy, the real
evidence is on the node, in systemd and journald: skills you already have from L1. Kubernetes
just adds two units (kubelet, containerd) and one CLI (crictl).

**Next step.** Put both halves together and follow one `kubectl apply` through the whole system.

### What happens on kubectl apply

**Level:** [L2 · Mid] · CKA: Troubleshooting

**Concept.** Follow one Deployment with 2 replicas from your keyboard to a running, reachable pod.
Every arrow below is a place where things can stop, and each stop has a recognisable symptom.

```
 kubectl apply -f web.yaml        (Deployment web, replicas 2, plus Service web)
   |
   | (1) HTTPS to https://192.168.56.10:6443 using ~/.kube/config credentials
   v
 +---------------------------- kube-apiserver ------------------------------+
 | (2) authentication: who are you? (client cert, token)                     |
 | (3) authorization: RBAC, may you create deployments in "shop"?           |
 | (4) admission: mutating (defaults, LimitRange) then validating (quota,   |
 |     PodSecurity, webhooks)                                                |
 | (5) schema validation, then (6) write to etcd                             |
 +-----------------------------------+--------------------------------------+
                                     |  watch events
     +-------------------------------+-------------------------------+
     v                                                               v
 (7) controller-manager                                    (8) kube-scheduler
     Deployment ctrl -> creates ReplicaSet web-7c9d8f6b5        sees pods with no node
     ReplicaSet ctrl -> creates 2 Pod objects (no node)        filter + score -> binds pod to w1
                                                                     |
                                                                     v
 (9) kubelet on w1 sees a pod bound to w1
     -> CRI RunPodSandbox: pause container + new network namespace
     -> (10) CNI ADD: veth pair, pod IP 10.244.1.12, routes to other nodes
     -> (11) PullImage: DNS for registry, TLS trust, credentials
     -> (12) CreateContainer + StartContainer (runc), mounts volumes, env
     -> (13) runs probes, reports status: Running, Ready=True
                                     |
                                     v
 (14) EndpointSlice controller: pod is Ready -> add 10.244.1.12:80 to slice for Service web
 (15) kube-proxy on every node: DNAT 10.96.120.15:80 -> 10.244.1.12:80 / 10.244.2.7:80
 (16) CoreDNS: web.shop.svc.cluster.local -> 10.96.120.15
 (17) Ingress/Gateway controller: Host app.example.com -> Service web
```

**Key terms**

| Step | Component | If it stops here you see |
|---|---|---|
| 1 | kubeconfig, network, TLS | `connection refused`, `i/o timeout`, `x509: certificate signed by unknown authority` |
| 2 | authentication | `error: You must be logged in to the server (Unauthorized)` |
| 3 | RBAC | `Error from server (Forbidden): deployments.apps is forbidden: User "jane" cannot create resource ...` |
| 4 | admission | `exceeded quota`, `violates PodSecurity "restricted:latest"`, webhook timeouts |
| 5 | validation | `error validating data`, `unknown field`, `field is immutable` |
| 7 | controllers | Deployment exists, no ReplicaSet or no pods; `kubectl describe rs` shows `FailedCreate` (often quota) |
| 8 | scheduler | pod `Pending`, event `FailedScheduling: 0/3 nodes are available: ...` (or no events if the scheduler is down) |
| 9–10 | kubelet, CNI | `ContainerCreating` forever; event `FailedCreatePodSandBox ... failed to setup network for sandbox` |
| 11 | image pull | `ErrImagePull`, `ImagePullBackOff` |
| 12 | container start | `CreateContainerConfigError`, `RunContainerError`, `CrashLoopBackOff` |
| 13 | probes | `Running` but `READY 0/1`; restarts from liveness failures |
| 14 | endpoints | Service has no endpoints: selector mismatch or pods not Ready |
| 15 | kube-proxy | ClusterIP times out while pod IP works |
| 16 | CoreDNS | `could not resolve host`, `NXDOMAIN`, slow lookups |
| 17 | ingress | 404 from the controller, 502/503, wrong certificate |

**See it on a real system**

```bash
kubectl apply -f web.yaml -v=6 2>&1 | grep -E 'GET|POST|PATCH' | head    # the HTTP calls kubectl makes
kubectl -n shop get events --sort-by=.lastTimestamp | tail -15             # the controllers' story
```

```
LAST SEEN   TYPE     REASON              OBJECT                          MESSAGE
40s         Normal   ScalingReplicaSet   deployment/web                  Scaled up replica set web-7c9d8f6b5 from 0 to 2
40s         Normal   SuccessfulCreate    replicaset/web-7c9d8f6b5        Created pod: web-7c9d8f6b5-2xkqp
40s         Normal   Scheduled           pod/web-7c9d8f6b5-2xkqp         Successfully assigned shop/web-7c9d8f6b5-2xkqp to w1
39s         Normal   Pulling             pod/web-7c9d8f6b5-2xkqp         Pulling image "nginx:1.27"
35s         Normal   Pulled              pod/web-7c9d8f6b5-2xkqp         Successfully pulled image "nginx:1.27" in 3.9s
35s         Normal   Created             pod/web-7c9d8f6b5-2xkqp         Created container: nginx
35s         Normal   Started             pod/web-7c9d8f6b5-2xkqp         Started container nginx
```

→ The events are the table above, in order: Deployment controller (ScalingReplicaSet), ReplicaSet
controller (SuccessfulCreate), scheduler (Scheduled), kubelet (Pulling, Pulled, Created, Started).
The **last event that appears** tells you which step the pipeline stopped at.

**Hands-on lab (test VM only)**

**Step 1 — build.** Apply a Deployment and a Service and read the events as above.

**Step 2 — break three steps on purpose, one at a time:** a non-existent image (step 11), a
`nodeSelector: disk=ssd` that no node has (step 8), and a Service selector `app: webb` (step 14).

**Step 3 — observe.** For each, find the last successful event and name the stopped step before
you read any logs.

**Step 4 — fix** each by correcting the manifest and re-applying.

**How it breaks.** Every row of the table above is a failure mode; areas 5–20 cover each one.

**Why it matters for troubleshooting.** This diagram is your map for the rest of the module and
the backbone of the bottom-up method in area 20. When you are lost, ask: "which numbered step did
this request reach?"

**Next step.** Build your own cluster so you can break every one of these steps (area 3).

---

## 3. Building a kubeadm homelab cluster

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Install Kubernetes the kubeadm way ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator); notes: [Introduction to Deployment with kubeadm](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Install-Kubernetes-the-kubeadm-way/Deployment-With-kubeadm-Introduction/page), [Solution Install a Kubernetes Cluster using kubeadm](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Install-Kubernetes-the-kubeadm-way/Lab-Solution-Install-a-Kubernetes-Cluster-using-kubeadm/page)); the gentler version is the Appendix: kubeadm setup in *Kubernetes for the Absolute Beginners – Hands-on Tutorial* ([course](https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners-hands-on-tutorial)) · 2) Note: [Kernel & sysctl](13-kernel-system.md) and [Packages](11-packages.md) for modules, sysctls and `apt-mark hold` · 3) Docs: the kubeadm install pages under [kubernetes.io/docs](https://kubernetes.io/docs/) (no video needed) · 4) Practice: build cp1, w1 and w2 three times from the bare-Ubuntu snapshot, faster each time.

The CKA exam clusters are kubeadm clusters with containerd. Building one by hand three or four
times is the fastest way to understand where every file lives, which is exactly what the
troubleshooting questions test. Follow the order below; each step exists for a reason and each
skipped step has a known failure signature.

### Lab topology and node prerequisites

**Level:** [L3 · Senior] · CKA: Cluster Architecture, Installation & Configuration

**Concept.** Before Kubernetes can run, every node must be a predictable Linux host: unique
identity, nodes that resolve and reach each other, correct time, no swap, the kernel modules and
sysctls that let bridged pod traffic be routed and filtered, and firewall rules that allow the
control-plane and CNI ports. These are L1 skills ([Linux](27-learn-linux.md),
[Kernel & sysctl](13-kernel-system.md)) applied with a specific purpose.

```
     192.168.56.0/24 (host-only / bridged lab network)
   +-------------------+   +-------------------+   +-------------------+
   | cp1 .10           |   | w1 .11            |   | w2 .12            |
   | apiserver :6443   |   | kubelet :10250    |   | kubelet :10250    |
   | etcd :2379-2380   |   | NodePorts         |   | NodePorts         |
   | sched :10259      |   | 30000-32767       |   | 30000-32767       |
   | ctrl-mgr :10257   |   |                   |   |                   |
   | kubelet :10250    |   | pods 10.244.1.0/24|   | pods 10.244.2.0/24|
   +-------------------+   +-------------------+   +-------------------+
```

**Key terms**

| Prerequisite | Why Kubernetes needs it |
|---|---|
| Unique hostname, MAC, `product_uuid` | node identity; cloned VMs that share them confuse the CNI and the kubelet |
| Swap off | kubelet's memory accounting and eviction assume no swap; by default it refuses to start with swap on (swap support exists but is opt-in) |
| `overlay` module | containerd's default snapshotter uses overlayfs for image layers |
| `br_netfilter` module + `net.bridge.bridge-nf-call-iptables=1` | makes bridged pod traffic visible to iptables, so kube-proxy's Service rules apply to it |
| `net.ipv4.ip_forward=1` | the node must route packets between pods, other nodes and the outside |
| Time sync | certificates and etcd leases break with clock skew ([Time & NTP](12-time-ntp.md)) |
| Open ports | 6443, 2379–2380, 10250, 10257, 10259 on the control plane; 10250 and 30000–32767 on workers; plus your CNI's ports |

**See it on a real system**

```bash
hostnamectl --static
ip -br addr show                             # which interface carries 192.168.56.x?
sudo cat /sys/class/dmi/id/product_uuid      # must differ on every node
swapon --show                                # no output = no swap
lsmod | grep -E '^(overlay|br_netfilter)'
sysctl net.bridge.bridge-nf-call-iptables net.ipv4.ip_forward
timedatectl | grep -E 'synchronized|NTP service'
sudo ufw status verbose
```

```
$ swapon --show
NAME      TYPE  SIZE USED PRIO
/swap.img file    4G   0B   -2

$ sysctl net.bridge.bridge-nf-call-iptables net.ipv4.ip_forward
sysctl: cannot stat /proc/sys/net/bridge/bridge-nf-call-iptables: No such file or directory
net.ipv4.ip_forward = 0
```

→ This node is not ready: Ubuntu Server's installer created `/swap.img`, `br_netfilter` is not
loaded (so the bridge sysctl does not even exist yet), and forwarding is off.

**Hands-on lab (test VM only)**

**Step 1 — identity and name resolution (all nodes).**

```bash
sudo hostnamectl set-hostname cp1            # w1 / w2 on the workers
cat <<'EOT' | sudo tee -a /etc/hosts
192.168.56.10 cp1
192.168.56.11 w1
192.168.56.12 w2
EOT
```

**Step 2 — swap off now and at boot (all nodes).** Comment out the swap line instead of deleting
it, and keep a backup.

```bash
sudo swapoff -a
sudo sed -i.bak '/\sswap\s/ s/^#*/#/' /etc/fstab
grep swap /etc/fstab                          # line now starts with #
systemctl list-units --type swap              # nothing active (zram/systemd swap units count too)
```

**Step 3 — kernel modules and sysctls (all nodes).** Files under `/etc/modules-load.d` and
`/etc/sysctl.d` make the settings survive reboots; `modprobe` and `sysctl --system` apply them now.

```bash
cat <<'EOT' | sudo tee /etc/modules-load.d/k8s.conf
overlay
br_netfilter
EOT
sudo modprobe overlay
sudo modprobe br_netfilter

cat <<'EOT' | sudo tee /etc/sysctl.d/k8s.conf
net.bridge.bridge-nf-call-iptables  = 1
net.bridge.bridge-nf-call-ip6tables = 1
net.ipv4.ip_forward                 = 1
EOT
sudo sysctl --system | grep -E 'bridge-nf-call-iptables|ip_forward'
```

**Step 4 — firewall (lab).** The simplest correct lab setup is to trust the node network and the
pod network on every node, and keep UFW for everything else. Port-by-port rules are in the table
under "How it breaks".

```bash
sudo ufw allow from 192.168.56.0/24 comment 'k8s nodes'
sudo ufw allow from 10.244.0.0/16 comment 'k8s pods'
sudo ufw status numbered
```

**Step 5 — break it.** Reboot one worker *without* Step 3's files (or remove
`/etc/modules-load.d/k8s.conf` before rebooting). After the reboot, Services stop working from pods
on that node in subtle ways, and `sysctl --system` reports that the bridge keys cannot be set.
kubeadm v1.30 and later no longer checks the bridge sysctls in preflight (it still fails on
`[ERROR FileContent--proc-sys-net-ipv4-ip_forward]: /proc/sys/net/ipv4/ip_forward contents are not set to 1`);
older kubeadm versions failed with
`[ERROR FileContent--proc-sys-net-bridge-bridge-nf-call-iptables]: /proc/sys/net/bridge/bridge-nf-call-iptables does not exist`.
Put the file back, `modprobe br_netfilter`, `sysctl --system`.

> RHEL/Rocky: use `firewall-cmd --permanent --add-port=6443/tcp` (and so on) then
> `firewall-cmd --reload`; kubeadm's own docs set SELinux to permissive for labs
> (`sudo setenforce 0` and `SELINUX=permissive` in `/etc/selinux/config`); install packages with
> dnf from the Kubernetes rpm repo. Fedora enables zram swap by default: remove `zram-generator-defaults`
> or swap stays on.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Swap still on | kubelet: `failed to run Kubelet: running with swap on is not supported, please disable swap`; kubeadm init waits for a healthy kubelet then times out | `swapon --show` | [Memory](04-memory.md) |
| `br_netfilter` missing | `sysctl: cannot stat /proc/sys/net/bridge/bridge-nf-call-iptables` (kubeadm before v1.30 also failed preflight on it); Service traffic between pods on the same node misbehaves | `lsmod` (look for `br_netfilter`) | [Kernel](13-kernel-system.md) |
| Forwarding off | pods cannot reach anything outside their node | `sysctl net.ipv4.ip_forward` | [Network](02-network.md) |
| Cloned VM, same product_uuid or MAC | random CNI breakage, two nodes fighting over an IP | `sudo cat /sys/class/dmi/id/product_uuid` | — |
| Firewall blocks 6443/10250 | `kubeadm join` times out; `kubectl logs`/`exec` fail with `dial tcp ...:10250: i/o timeout` | `sudo ufw status verbose`; `nc -vz cp1 6443` | [Ports inventory](22-playbook-ports-inventory.md) |
| UFW/Docker FORWARD policy DROP | pods on the same node talk, pods on different nodes do not | `sudo iptables -S FORWARD` (look for `-P FORWARD DROP` in the first line) | [Network](02-network.md) |

| Port / protocol | Node | Used by |
|---|---|---|
| 6443/tcp | control plane | kube-apiserver (everyone) |
| 2379–2380/tcp | control plane | etcd client and peer |
| 10250/tcp | all | kubelet API (logs, exec, metrics) |
| 10257/tcp, 10259/tcp | control plane | controller-manager, scheduler (localhost health) |
| 10256/tcp | all | kube-proxy health |
| 30000–32767/tcp+udp | all | NodePort Services |
| 8472/udp | all | Flannel VXLAN |
| 179/tcp, 4789/udp, 5473/tcp | all | Calico BGP, Calico VXLAN, Calico Typha |

**Why it matters for troubleshooting.** "Pods on different nodes cannot talk" and "Services work
on one node only" are almost always prerequisite problems: modules, sysctls, firewall or MTU.
When a cluster was built by hand, check the foundation before blaming Kubernetes.

**Next step.** Install and configure the container runtime.

### containerd with SystemdCgroup

**Level:** [L3 · Senior] · CKA: Cluster Architecture, Installation & Configuration

**Concept.** The kubelet and the runtime both create cgroups for pods. On a systemd host with
cgroup v2 (Ubuntu 22.04/24.04), both must use the **systemd cgroup driver**, so systemd stays the
single owner of the cgroup tree. kubeadm configures the kubelet with `cgroupDriver: systemd` by
default; you must make containerd match with `SystemdCgroup = true`. A mismatch does not fail
immediately: the cluster comes up, then control-plane pods restart every few minutes.

Two version facts change this picture. Since Kubernetes v1.34 (`KubeletCgroupDriverFromCRI`, GA),
a kubelet talking to containerd 2.x asks the runtime which driver it uses and ignores its own
`cgroupDriver` setting, so containerd's `SystemdCgroup` becomes the single switch. containerd 1.7
cannot answer that query, so the kubelet falls back to its own setting; the Kubernetes docs say
v1.38 drops this fallback and containerd 1.x will then fail with newer kubelets. Build new clusters
on containerd 2.x, and check the "Container Runtimes" page in the
[Kubernetes docs](https://kubernetes.io/docs/) for the version you install.

**Key terms**

| Setting | containerd 1.7 (config `version = 2`) | containerd 2.x (config `version = 3`) |
|---|---|---|
| systemd cgroups | table `[plugins."io.containerd.grpc.v1.cri".containerd.runtimes.runc.options]` key `SystemdCgroup = true` | table `[plugins.'io.containerd.cri.v1.runtime'.containerd.runtimes.runc.options]` key `SystemdCgroup = true` |
| pause (sandbox) image | `[plugins."io.containerd.grpc.v1.cri"]` key `sandbox_image` | `[plugins.'io.containerd.cri.v1.images'.pinned_images]` key `sandbox` |
| registry hosts directory | `[plugins."io.containerd.grpc.v1.cri".registry]` key `config_path` (empty by default: set it) | `[plugins.'io.containerd.cri.v1.images'.registry]` key `config_path` (defaults include `/etc/containerd/certs.d`) |
| CLI | `crictl` (CRI view, what kubelet sees), `ctr` (low level, needs `-n k8s.io`) | same |

**See it on a real system**

```bash
containerd --version
stat -fc %T /sys/fs/cgroup/                       # cgroup2fs = cgroup v2
sudo containerd config dump | grep -nE 'SystemdCgroup|sandbox|config_path'
grep cgroupDriver /var/lib/kubelet/config.yaml    # after kubeadm init
sudo crictl info | grep -iE 'systemdCgroup|sandboxImage' | head
```

```
$ sudo containerd config dump | grep -nE 'SystemdCgroup|sandbox|config_path'
61:    sandbox_image = "registry.k8s.io/pause:3.10.1"
118:            SystemdCgroup = true
152:      config_path = "/etc/containerd/certs.d"

$ grep cgroupDriver /var/lib/kubelet/config.yaml
cgroupDriver: systemd
```

→ Both sides say systemd, the pause image matches what kubeadm expects, and containerd will read
per-registry settings (Harbor, area 17) from `/etc/containerd/certs.d`.

**Hands-on lab (test VM only)**

**Step 1 — install (all nodes).** Ubuntu's own `containerd` package (1.7.x on 22.04 and 24.04;
check with `apt-cache policy containerd`) works with Kubernetes up to v1.37 only, through the
kubelet fallback described above. For a cluster you will upgrade past that, install containerd 2.x
instead (Docker's `containerd.io` package or the upstream release; confirm with
`containerd --version`). The commands below show the Ubuntu package. Do not install the full Docker
Engine on Kubernetes nodes: it adds its own iptables rules (FORWARD policy DROP) and a second image
store that confuses beginners.

```bash
sudo apt-get update
sudo apt-get install -y containerd
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml > /dev/null
sudo cp /etc/containerd/config.toml /etc/containerd/config.toml.orig
```

**Step 2 — configure.** Turn on the systemd driver (the `sed` works on both config versions),
point containerd at the registry hosts directory, and set the pause image to the tag kubeadm
uses (run `kubeadm config images list` after Step 3 of the next topic to see it).

```bash
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
grep -n 'SystemdCgroup' /etc/containerd/config.toml   # no output: add SystemdCgroup = true under the runc options table yourself
# containerd 1.7 only: set config_path = "/etc/containerd/certs.d" under the cri registry table
sudoedit /etc/containerd/config.toml
sudo systemctl restart containerd
sudo systemctl enable containerd
```

**Step 3 — point crictl at containerd** (crictl ships in the `cri-tools` package installed with
kubeadm; without this file it probes several sockets and prints warnings).

```bash
cat <<'EOT' | sudo tee /etc/crictl.yaml
runtime-endpoint: unix:///run/containerd/containerd.sock
image-endpoint: unix:///run/containerd/containerd.sock
timeout: 10
EOT
sudo crictl version
```

**Step 4 — break (after the cluster is up, area 3 complete).** On cp1 set `SystemdCgroup = false`
and restart containerd. Over the next 5–15 minutes watch
`kubectl -n kube-system get pods -w`: etcd, kube-apiserver and others start accumulating restarts,
and `kubectl` intermittently fails with `connection refused`. (This is the containerd 1.7
behaviour. With containerd 2.x and kubelet v1.34+, the kubelet reads the driver from containerd
when it starts, so the mismatch lasts only until the next kubelet restart; after that both sides
use cgroupfs, which hides the flapping but is still the wrong driver on a systemd host.)

**Step 5 — fix.** Set it back to `true`, `sudo systemctl restart containerd`, then
`sudo systemctl restart kubelet`. Restart counts stop climbing.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| cgroup driver mismatch | control-plane pods restart every few minutes; random `connection refused` from kubectl | `sudo containerd config dump` and grep `SystemdCgroup` | area 20 |
| Typo in config.toml | containerd fails to start: `failed to load TOML` in its journal; node NotReady | `journalctl -u containerd -n 30 --no-pager` | [systemd](07-services-systemd.md) |
| Pause image mismatch | kubeadm warning `detected that the sandbox image ... of the container runtime is inconsistent with that used by kubeadm` | `kubeadm config images list` | — |
| crictl not configured | `WARN ... runtime connect using default endpoints ... deprecated` | `cat /etc/crictl.yaml` | — |
| Docker Engine also installed | duplicate image stores; `docker ps` shows nothing Kubernetes runs; FORWARD DROP | `systemctl status docker` | [Docker](30-learn-docker.md) |

**Why it matters for troubleshooting.** "The control plane flaps every few minutes" is one of the
most confusing homelab failures, and its cause is one boolean in a TOML file. Knowing the runtime
config also unlocks private-registry work (area 17).

**Next step.** Install the Kubernetes packages and bootstrap the control plane.

### Installing kubeadm and running kubeadm init

**Level:** [L3 · Senior] · CKA: Cluster Architecture, Installation & Configuration

**Concept.** `kubeadm` is a bootstrapper: it generates certificates, kubeconfig files and static
pod manifests, starts the control plane through the kubelet, and installs CoreDNS and kube-proxy.
It does **not** install the container runtime or the CNI, and it does not manage the cluster after
bootstrap (except for upgrades and certificate renewal). Each phase writes files you will later
debug, so learn what each one produces.

**Key terms (kubeadm init phases)**

| Phase | What it does | Files it leaves behind |
|---|---|---|
| preflight | checks swap, ports, modules, runtime, images | — |
| certs | creates the cluster CA and all component certificates | `/etc/kubernetes/pki/` |
| kubeconfig | writes credentials for admin, kubelet, scheduler, controller-manager | `/etc/kubernetes/*.conf` (`admin.conf`, `super-admin.conf`, ...) |
| etcd | static pod manifest for a local etcd | `/etc/kubernetes/manifests/etcd.yaml`, data in `/var/lib/etcd` |
| control-plane | static pod manifests for apiserver, controller-manager, scheduler | `/etc/kubernetes/manifests/*.yaml` |
| kubelet-start | writes kubelet config and flags, (re)starts kubelet | `/var/lib/kubelet/config.yaml`, `/var/lib/kubelet/kubeadm-flags.env` |
| wait-control-plane | waits for the static pods to become healthy | — |
| upload-config | stores kubeadm and kubelet config in ConfigMaps | `kube-system/kubeadm-config` |
| mark-control-plane | labels and taints cp1 so normal pods avoid it | taint `node-role.kubernetes.io/control-plane:NoSchedule` |
| bootstrap-token | creates the join token and RBAC for joining nodes | — |
| addon | installs CoreDNS and kube-proxy | Deployments/DaemonSets in kube-system |

**See it on a real system**

```bash
kubeadm version -o short
apt-cache policy kubeadm | head -4
sudo ls /etc/kubernetes /etc/kubernetes/pki
kubectl -n kube-system get cm kubeadm-config -o yaml | grep -E 'podSubnet|serviceSubnet|kubernetesVersion|controlPlaneEndpoint'
systemctl cat kubelet | grep -E 'EnvironmentFile|ExecStart='
```

```
$ kubectl -n kube-system get cm kubeadm-config -o yaml | grep -E 'podSubnet|serviceSubnet|kubernetesVersion'
    kubernetesVersion: v1.34.1
      podSubnet: 10.244.0.0/16
      serviceSubnet: 10.96.0.0/12
```

→ This ConfigMap is the cluster's memory of how it was built. `kubeadm upgrade` reads it, and it
is the quickest way to answer "which pod CIDR did we use?" on a cluster someone else built.

**Hands-on lab (test VM only)**

**Step 1 — add the Kubernetes apt repository (all nodes).** The repository path contains the minor
version (`v1.34` below); pick the version you study for and check the official install page
([Kubernetes docs](https://kubernetes.io/docs/)) for the current one.

```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gpg
sudo mkdir -p -m 755 /etc/apt/keyrings
curl -fsSL https://pkgs.k8s.io/core:/stable:/v1.34/deb/Release.key | sudo gpg --dearmor -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo 'deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.34/deb/ /' | sudo tee /etc/apt/sources.list.d/kubernetes.list
```

**Step 2 — install and hold (all nodes).** `apt-mark hold` stops unattended-upgrades from moving
the kubelet past the control plane's version, which would break the version-skew rules
([Packages](11-packages.md)).

```bash
sudo apt-get update
sudo apt-get install -y kubelet kubeadm kubectl
sudo apt-mark hold kubelet kubeadm kubectl
sudo systemctl enable --now kubelet
```

Right now `systemctl status kubelet` shows it restarting every few seconds, and
`journalctl -u kubelet` says `open /var/lib/kubelet/config.yaml: no such file or directory`.
**That is normal**: the kubelet waits in a crash loop until `kubeadm init` or `join` writes its
config. Do not "fix" it.

**Step 3 — init the control plane (cp1 only).** Pre-pulling the images first separates registry
or DNS problems from bootstrap problems. `--apiserver-advertise-address` pins the API server to the
lab interface; `--pod-network-cidr` must match the CNI you install next.

```bash
sudo kubeadm config images list
sudo kubeadm config images pull
sudo kubeadm init \
  --apiserver-advertise-address=192.168.56.10 \
  --pod-network-cidr=10.244.0.0/16 \
  --node-name=cp1
```

```
[init] Using Kubernetes version: v1.34.1
[preflight] Running pre-flight checks
[certs] Generating "ca" certificate and key
[certs] apiserver serving cert is signed for DNS names [cp1 kubernetes kubernetes.default kubernetes.default.svc kubernetes.default.svc.cluster.local] and IPs [10.96.0.1 192.168.56.10]
[kubeconfig] Writing "admin.conf" kubeconfig file
[kubeconfig] Writing "super-admin.conf" kubeconfig file
[etcd] Creating static Pod manifest for local etcd in "/etc/kubernetes/manifests"
[control-plane] Creating static Pod manifest for "kube-apiserver"
[kubelet-start] Starting the kubelet
[wait-control-plane] Waiting for the kubelet to boot up the control plane as static Pods from directory "/etc/kubernetes/manifests"
[mark-control-plane] Marking the node cp1 as control-plane by adding the taints [node-role.kubernetes.io/control-plane:NoSchedule]
[bootstrap-token] Using token: k8wq3x.9v2m7d1c0b8a6f4e
[addons] Applied essential addon: CoreDNS
[addons] Applied essential addon: kube-proxy

Your Kubernetes control-plane has initialized successfully!
...
kubeadm join 192.168.56.10:6443 --token k8wq3x.9v2m7d1c0b8a6f4e \
	--discovery-token-ca-cert-hash sha256:4f1c0d...e9
```

→ Read the `[certs] apiserver serving cert is signed for ... IPs` line: the API server certificate
is only valid for those names and IPs. If you later reach the API through another name (a load
balancer, a DNS alias), you get `x509: certificate is valid for ..., not ...`. For a cluster you
might make highly available later, pass `--control-plane-endpoint=k8s-api.lab.example.com:6443`
at init time; it is hard to add afterwards.

**Step 4 — kubeconfig for your user.**

```bash
mkdir -p "$HOME/.kube"
sudo cp -i /etc/kubernetes/admin.conf "$HOME/.kube/config"
sudo chown "$(id -u):$(id -g)" "$HOME/.kube/config"
chmod 600 "$HOME/.kube/config"
kubectl get nodes
```

```
NAME   STATUS     ROLES           AGE   VERSION
cp1    NotReady   control-plane   70s   v1.34.1
```

→ `NotReady` is expected until a CNI is installed. CoreDNS pods are `Pending` for the same reason.

**Step 5 — break (VirtualBox classic).** If your VMs have a NAT adapter *and* a host-only adapter,
the kubelet may register the NAT address (often 10.0.2.15, identical on every VM).
`kubectl get nodes -o wide` then shows the same INTERNAL-IP for every node, and
`kubectl logs`/`exec` fail with
`dial tcp 10.0.2.15:10250: connect: connection refused`. Reproduce it by joining a worker
without the fix below.

**Step 6 — fix.** Tell each kubelet which IP to use, then restart it. On Ubuntu the kubelet unit
reads `/etc/default/kubelet` (see `systemctl cat kubelet`).

```bash
echo 'KUBELET_EXTRA_ARGS=--node-ip=192.168.56.11' | sudo tee /etc/default/kubelet   # per node
sudo systemctl restart kubelet
kubectl get nodes -o wide
```

> Warning: `kubeadm reset` wipes this node's Kubernetes state (`/etc/kubernetes`,
> `/var/lib/kubelet`, and on a control plane the etcd data). On a lab VM, restoring the
> "before kubeadm init" snapshot is safer and cleaner. If you do run `sudo kubeadm reset`, read its
> final message: it deliberately leaves CNI config (`/etc/cni/net.d`) and iptables/IPVS rules for
> you to clean up. Restoring the snapshot is still better than flushing firewall rules by hand.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| kubelet unhealthy during init | `[kubelet-check] The kubelet is not healthy after 4m0s` (older kubeadm: `The HTTP call equal to 'curl -sSL http://localhost:10248/healthz' failed`) | `journalctl -u kubelet -n 50 --no-pager` | area 18 |
| Image pull fails at preflight | `[ERROR ImagePull]: failed to pull image registry.k8s.io/...` | `sudo crictl pull registry.k8s.io/pause:3.10.1` (tag from `kubeadm config images list`) | [DNS](08-dns.md) |
| Port already in use | `[ERROR Port-6443]: Port 6443 is in use` (an old cluster or another service) | `sudo ss -ltnp 'sport = :6443'` | [Ports inventory](22-playbook-ports-inventory.md) |
| Wrong node IP | all nodes show the same INTERNAL-IP; logs/exec fail | `kubectl get nodes -o wide` | this topic |
| Packages upgraded unintentionally | node version newer than control plane | `apt-mark showhold` | area 19 |

**Why it matters for troubleshooting.** Every file kubeadm writes is a file the exam (and real
life) will break: a static pod manifest, a kubelet config, a certificate, a kubeconfig. If you know
which phase wrote it, you know what "correct" looks like.

**Next step.** Give the pods a network and add workers.

### Installing a CNI and joining workers

**Level:** [L3 · Senior] · CKA: Installation & Configuration, Services & Networking

**Concept.** Kubernetes requires that every pod gets its own IP and can reach every other pod
without NAT, but it does not ship that network. A **CNI plugin** provides it: it allocates pod IPs
from the node's slice of the pod CIDR, wires each pod's network namespace to the host with a veth
pair, and moves packets between nodes (by routing, BGP, VXLAN or eBPF). Until a CNI is installed,
nodes stay `NotReady` and CoreDNS stays `Pending`.

| CNI | Enforces NetworkPolicy | Default pod CIDR it expects | Node-to-node traffic | Good for |
|---|---|---|---|---|
| Flannel | no | 10.244.0.0/16 | VXLAN UDP 8472 | simplest first cluster |
| Calico | yes | 192.168.0.0/16 in its sample config (change it) | BGP TCP 179 and/or VXLAN UDP 4789 | CKA practice, NetworkPolicy labs |
| Cilium | yes (plus L7) | its own IPAM by default | VXLAN/Geneve or native routing | eBPF, observability (Hubble) |

> Calico's sample pool 192.168.0.0/16 overlaps most home and office LANs, and this lab's node
> network. Always edit the CIDR to match `--pod-network-cidr` (10.244.0.0/16 here) before applying.

**Key terms**

| Term | Meaning |
|---|---|
| podCIDR | the per-node slice (e.g. 10.244.1.0/24) allocated by the controller-manager from the cluster pod CIDR |
| veth pair | virtual cable: one end `eth0` in the pod, the other end on the host |
| Overlay (VXLAN) | pod packets wrapped in UDP between nodes; costs 50 bytes of MTU |
| Bootstrap token | short-lived (24 h default) credential a new node uses to join |
| CA cert hash | lets the joining node verify it is talking to the right API server |

**See it on a real system**

```bash
kubectl get nodes -o custom-columns=NAME:.metadata.name,PODCIDR:.spec.podCIDR,READY:.status.conditions[-1].status
ls /etc/cni/net.d/
ip -br addr | grep -E 'cali|flannel|vxlan|cni'
ip route | grep 10.244
sudo kubeadm token list                      # on cp1
```

```
$ ip route | grep 10.244          # on w1 with Flannel
10.244.0.0/24 via 10.244.0.0 dev flannel.1 onlink
10.244.1.0/24 dev cni0 proto kernel scope link src 10.244.1.1
10.244.2.0/24 via 10.244.2.0 dev flannel.1 onlink

$ ip route | grep 10.244          # on w1 with Calico (BGP, same subnet)
10.244.1.12 dev cali4f3a9b2c1d0 scope link
blackhole 10.244.1.0/26 proto bird
10.244.2.0/26 via 192.168.56.12 dev enp0s8 proto bird
```

→ Each route line is "how this node reaches pods elsewhere". With Flannel, every other node's /24
goes through the `flannel.1` VXLAN device and local pods sit behind the `cni0` bridge. With Calico,
a `via 192.168.56.12 proto bird` line is a BGP-learned route to an address block on w2 (Calico's
own IPAM hands out /26 blocks rather than using the node's podCIDR), and a `dev caliXXXX` host
route is a local pod. No route to another node's pods means cross-node pod traffic will fail.

**Hands-on lab (test VM only)**

**Step 1 — observe the broken state.** Before installing anything, run
`kubectl get nodes` (NotReady) and `kubectl -n kube-system get pods` (CoreDNS Pending). Then
`kubectl describe node cp1` and find `cni plugin not initialized`.

**Step 2 — install a CNI.** Take the current install command and version from the CNI project's
documentation (the Kubernetes docs "Installing Addons" page links them). For Flannel the
manifest is published as a release asset; for Calico you apply the operator, then a custom
resource file in which you set the pool CIDR. The shapes of the commands:

```bash
# Flannel (expects --pod-network-cidr=10.244.0.0/16)
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml

# Calico via its operator: copy both URLs and the version from the Calico docs
kubectl create -f CALICO_OPERATOR_MANIFEST_URL
curl -fsSLo calico-cr.yaml CALICO_CUSTOM_RESOURCES_URL
sed -i 's#cidr: 192.168.0.0/16#cidr: 10.244.0.0/16#' calico-cr.yaml
kubectl create -f calico-cr.yaml

kubectl get pods -A -w                        # wait for CNI pods and CoreDNS to be Running
```

**Step 3 — join the workers.** Tokens expire after 24 hours, so print a fresh join command
rather than scrolling back to the init output.

```bash
sudo kubeadm token create --print-join-command          # on cp1
sudo kubeadm join 192.168.56.10:6443 --token TOKEN --discovery-token-ca-cert-hash sha256:HASH   # on w1, w2
kubectl get nodes -o wide                                # on cp1
kubectl label node w1 node-role.kubernetes.io/worker=    # cosmetic: fills the ROLES column
kubectl label node w2 node-role.kubernetes.io/worker=
```

**Step 4 — smoke test across nodes.** Two pods pinned to different nodes, then a request from one
to the other by pod IP and by Service name.

```bash
kubectl run a --image=nginx:1.27 --overrides='{"spec":{"nodeName":"w1"}}'
kubectl run b --image=nicolaka/netshoot --overrides='{"spec":{"nodeName":"w2"}}' -- sleep 3600
kubectl expose pod a --port=80
kubectl get pods -o wide
kubectl exec b -- curl -s -o /dev/null -w '%{http_code}\n' http://a     # expect 200
```

**Step 5 — break the join.** Create a token that expires quickly, wait, then try to join w2 with it
(do this before w2 joins, or after restoring w2's pre-join snapshot).

```bash
sudo kubeadm token create --ttl 2m --print-join-command   # on cp1, wait 3 minutes
```

The join fails with
`couldn't validate the identity of the API Server: could not find a JWS signature in the cluster-info ConfigMap for token ID "..."`.
Fix: create a new token and join again.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| No CNI | nodes `NotReady`, CoreDNS `Pending`, `cni plugin not initialized` | `ls /etc/cni/net.d` | [26](26-playbook-containers-k8s.md) |
| Init without `--pod-network-cidr` (Flannel) | flannel pods crash: `Error registering network: failed to acquire lease: node "w1" pod cidr not assigned` | `kubectl get nodes -o jsonpath='{.items[*].spec.podCIDR}'` | this topic |
| Pod CIDR overlaps LAN | some LAN hosts unreachable from pods; weird routing | `ip route` | [Network](02-network.md) |
| CNI traffic blocked between nodes | same-node traffic works, cross-node fails; DNS fails only on some nodes | `sudo tcpdump -ni enp0s8 udp port 8472` (Flannel) | [Network speed](24-playbook-network-speed.md) |
| MTU too large for overlay | small requests work, large responses hang | `ip link show flannel.1` (MTU 1450 on a 1500 network) | [Network](02-network.md) |
| Expired token | `could not find a JWS signature in the cluster-info ConfigMap` | `sudo kubeadm token list` | this topic |
| Sandbox networking fails | pod stuck `ContainerCreating`, event `FailedCreatePodSandBox ... failed to setup network for sandbox` | `kubectl -n NS describe pod POD`, then CNI pod logs on that node | [26](26-playbook-containers-k8s.md) |

**Why it matters for troubleshooting.** When "pod A cannot reach pod B" you now have a concrete
path to check: A's veth, A's node routes, the encapsulation between nodes (firewall, MTU), B's node
routes, B's veth. That is the L2 packet walk from [Networking](28-learn-networking.md), with one
extra hop.

**Next step.** Get fast and precise with kubectl (area 4), then start with Pods (area 5).

---

## 4. kubectl fluency

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — the Core Concepts practice tests, solved with imperative commands only ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)), plus the kubectl refresher in the Prerequisites of *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)) · 2) Note: [Kubernetes reference](15-kubernetes.md) and the [Cheatsheet](19-cheatsheet.md) · 3) Video: none; typing speed is the skill · 4) Practice: the 90-second imperative drill below once a day for a week, then free scenarios on [Killercoda](https://killercoda.com/).

### kubeconfig, contexts and namespaces

**Level:** [L1 · Junior] · CKA: every task starts here

**Concept.** kubectl is just an HTTPS client. A **kubeconfig** file tells it *where* (cluster:
API server URL plus the CA to trust), *who* (user: client certificate, token, or an exec plugin
such as `aws eks get-token`), and the default namespace. A **context** binds one cluster, one user
and one namespace under a name. Most "wrong cluster" disasters are context mistakes, so the first
command of any session is "where am I?".

```
 ~/.kube/config
   clusters:  kubernetes -> https://192.168.56.10:6443 + CA
   users:     kubernetes-admin -> client cert/key
              jane -> client cert/key
   contexts:  kubernetes-admin@kubernetes = cluster kubernetes + user kubernetes-admin + ns shop
              jane@lab                    = cluster kubernetes + user jane + ns dev
   current-context: kubernetes-admin@kubernetes
```

**Key terms**

| Term | Meaning |
|---|---|
| `KUBECONFIG` | env var; colon-separated list of files, merged in order |
| context | named cluster + user + namespace |
| `admin.conf` | kubeadm's admin credential (group `kubeadm:cluster-admins`, bound to cluster-admin through RBAC) |
| `super-admin.conf` | break-glass credential in group `system:masters`, which bypasses RBAC entirely; keep it on cp1 only |
| namespace | a name scope for objects; not a security boundary by itself |

**See it on a real system**

```bash
kubectl config get-contexts
kubectl config current-context
kubectl config view --minify            # only the active context; secrets shown as DATA+OMITTED
kubectl auth whoami                     # which identity the API server sees
kubectl config set-context --current --namespace=shop
kubectl version                         # client vs server version (keep within one minor)
```

```
$ kubectl config get-contexts
CURRENT   NAME                          CLUSTER      AUTHINFO           NAMESPACE
*         kubernetes-admin@kubernetes   kubernetes   kubernetes-admin   shop
          jane@lab                      kubernetes   jane               dev

$ kubectl auth whoami
ATTRIBUTE                                           VALUE
Username                                            kubernetes-admin
Groups                                              [kubeadm:cluster-admins system:authenticated]
```

→ The asterisk is where your next command lands. Many teams put the context in their shell
prompt for exactly this reason.

**Hands-on lab (test VM only)**

**Step 1 — use the cluster from your workstation.** Install kubectl (Ubuntu: same apt repo;
macOS: `brew install kubectl`; Windows: `winget install -e --id Kubernetes.kubectl`) and copy the
kubeconfig. A kubeconfig with admin credentials is equivalent to root on every node: keep it `600`
and never commit it.

```bash
scp cp1:.kube/config ~/.kube/lab.config
chmod 600 ~/.kube/lab.config
export KUBECONFIG=~/.kube/config:~/.kube/lab.config
kubectl config get-contexts
```

**Step 2 — break the server address.** Edit `~/.kube/lab.config` and change `:6443` to `:6444`.
Run `kubectl get nodes`: `dial tcp 192.168.56.10:6444: connect: connection refused`.

**Step 3 — break the trust.** Restore the port, then replace the `certificate-authority-data`
value with the one from another cluster (or rebuild the lab cluster and keep the old file):
`tls: failed to verify certificate: x509: certificate signed by unknown authority`.

**Step 4 — fix** both by copying a fresh `admin.conf`. Lesson: kubeconfig errors are connection
and TLS errors; the L2 skills from [Web, HTTP & TLS](18-web-http-tls.md) apply directly.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Wrong context | commands succeed on the wrong cluster or namespace | `kubectl config current-context` | — |
| API server down or wrong address | `The connection to the server HOST:6443 was refused` | `kubectl config view --minify` then `nc -vz HOST 6443` | area 20 |
| Cluster rebuilt, old CA | `x509: certificate signed by unknown authority` | compare CA in kubeconfig and `/etc/kubernetes/pki/ca.crt` | [TLS](18-web-http-tls.md) |
| Expired client certificate | `error: You must be logged in to the server (Unauthorized)` | `kubeadm certs check-expiration` | area 19 |
| Missing namespace in context | `No resources found in default namespace.` | add `-n NS` or set the context namespace | — |

**Why it matters for troubleshooting.** Before you trust any output, confirm the cluster, the
identity and the namespace. "No resources found" in the wrong namespace has sent many engineers
chasing a ghost.

**Next step.** Learn to ask the API precise questions.

### Reading the API: explain, get and output formats

**Level:** [L2 · Mid] · CKA: all domains

**Concept.** Every object is a JSON document. `kubectl get` shows a summary table; output flags let
you see any field; `kubectl explain` is the built-in documentation for every field (it works
offline from the cluster's own schema, which makes it gold in the exam). JSONPath and
custom-columns turn "scroll through YAML" into "one precise answer".

**Key terms**

| Flag / command | What it gives you |
|---|---|
| `-o wide` | extra columns: pod IP, node, nominated node, readiness gates |
| `-o yaml` / `-o json` | the full object, including status |
| `-o name` | `kind/name` lines, perfect for scripts |
| `-o jsonpath='{...}'` | selected fields; `range` loops over lists; `?()` filters |
| `-o custom-columns=H1:.path,H2:.path` | your own table |
| `--show-labels`, `-L KEY`, `-l k=v` | show labels, a label column, filter by label |
| `--field-selector` | server-side filter on some fields (`status.phase`, `spec.nodeName`, `metadata.name`) |
| `--sort-by=.path` | sort by a JSONPath |
| `-w` | watch for changes |
| `kubectl explain RES.FIELD --recursive` | field reference |

**See it on a real system**

```bash
kubectl explain deployment.spec.strategy.rollingUpdate
kubectl explain pod.spec.containers.livenessProbe --recursive | head -30
kubectl get pods -A -o wide --field-selector spec.nodeName=w1
kubectl get pods -A --field-selector status.phase!=Running
kubectl get pods -A --sort-by=.metadata.creationTimestamp | tail -5

# Node name and InternalIP
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.addresses[?(@.type=="InternalIP")].address}{"\n"}{end}'

# Every image running in the cluster
kubectl get pods -A -o jsonpath='{range .items[*]}{range .spec.containers[*]}{.image}{"\n"}{end}{end}' | sort -u

# Restarts per pod as a table
kubectl get pods -A -o custom-columns='NS:.metadata.namespace,POD:.metadata.name,RESTARTS:.status.containerStatuses[*].restartCount,NODE:.spec.nodeName'
```

```
$ kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.addresses[?(@.type=="InternalIP")].address}{"\n"}{end}'
cp1	192.168.56.10
w1	192.168.56.11
w2	192.168.56.12
```

**"Who owns this port?" on Kubernetes.** The same question from your Apache incident
([Ports inventory](22-playbook-ports-inventory.md)) has Kubernetes-specific answers. A NodePort is
implemented as NAT rules by kube-proxy, so `ss -ltnp` on the node may show *nothing* listening on
30080 even though it works; hostPort is also NAT. Only `hostNetwork: true` pods show up in `ss`
with a real process. Ask the API instead:

```bash
# Which Service owns NodePort 30080?
kubectl get svc -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}{" "}{.spec.ports[*].nodePort}{"\n"}{end}' | grep -w 30080
# Which pods use the node's network namespace (and can collide with Apache on 80/443)?
kubectl get pods -A -o jsonpath='{range .items[?(@.spec.hostNetwork==true)]}{.metadata.namespace}/{.metadata.name}{"\n"}{end}'
# Which pods use hostPort?
kubectl get pods -A -o jsonpath='{range .items[*]}{.metadata.namespace}/{.metadata.name}{" "}{.spec.containers[*].ports[*].hostPort}{"\n"}{end}' | awk 'NF>1'
```

**Hands-on lab (test VM only)**

**Step 1 — answer without scrolling.** Using only jsonpath or custom-columns, print: (a) each pod
and its QoS class (`.status.qosClass`), (b) each node and its kubelet version
(`.status.nodeInfo.kubeletVersion`), (c) all PVs sorted by capacity.

**Step 2 — break your query.** Use a wrong path such as `.status.qosclass` (lowercase c). kubectl
prints empty values, not an error. Lesson: an empty column means "check the path with
`-o yaml`", not "the field is empty".

**Step 3 — fix** with `kubectl get pod POD -o yaml | grep -i qos` to find the exact spelling.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Wrong JSONPath | empty output or `error: error executing jsonpath ... is not found` | `kubectl get RES NAME -o yaml` | — |
| Shell eats the quotes | a parse error such as `error parsing jsonpath ..., unrecognized identifier InternalIP` (the filter's string lost its quotes) | wrap the whole template in single quotes | [Linux](27-learn-linux.md) |
| Unsupported field selector | `field label not supported: spec.foo` | use `-l` labels or jsonpath filters | — |

**Why it matters for troubleshooting.** Under pressure you want one line that answers one
question. These queries are also what you will paste into runbooks and CI checks.

**Next step.** Create objects as fast as you can read them.

### Generators and imperative commands

**Level:** [L2 · Mid] · CKA: all domains (speed)

**Concept.** Writing YAML from memory is slow and error-prone. kubectl can *generate* correct YAML
for most objects with `--dry-run=client -o yaml`, which you then edit for the fields the generator
does not support (probes, volumes, affinity). In the exam this is the difference between finishing
and not finishing. In real life it gives you a clean starting manifest for Git.

**Key terms**

| Command | Creates |
|---|---|
| `kubectl run NAME --image=IMG` | a bare Pod (restartPolicy `Always` unless you add `--restart=Never` or `OnFailure`), with `--labels`, `--env`, `--port`, `--command` |
| `kubectl create deployment NAME --image=IMG --replicas=N --port=P` | Deployment |
| `kubectl expose deploy NAME --port=80 --target-port=8080 --type=NodePort` | Service |
| `kubectl create service clusterip NAME --tcp=80:8080` | Service without a matching deployment |
| `kubectl create configmap NAME --from-literal=K=V --from-file=FILE` | ConfigMap |
| `kubectl create secret generic NAME --from-literal=K=V` | Secret |
| `kubectl create secret tls NAME --cert=FILE --key=FILE` | TLS Secret |
| `kubectl create secret docker-registry NAME --docker-server=...` | image pull Secret |
| `kubectl create serviceaccount NAME` | ServiceAccount |
| `kubectl create role / clusterrole NAME --verb=... --resource=...` | RBAC roles |
| `kubectl create rolebinding / clusterrolebinding NAME --role/--clusterrole=... --user/--serviceaccount=...` | bindings |
| `kubectl create job NAME --image=IMG -- CMD` / `--from=cronjob/NAME` | Job |
| `kubectl create cronjob NAME --image=IMG --schedule='*/5 * * * *' -- CMD` | CronJob |
| `kubectl create ingress NAME --class=C --rule='host/path*=svc:port'` | Ingress |
| `kubectl create quota`, `create pdb`, `create priorityclass`, `create token SA` | quota, PodDisruptionBudget, PriorityClass, a short-lived SA token |
| `kubectl set image / resources / env / serviceaccount` | change one aspect of an existing object |
| `kubectl label / annotate / taint / scale / autoscale` | metadata, scheduling, replicas |

**See it on a real system**

```bash
kubectl create deployment web --image=nginx:1.27 --replicas=3 --port=80 --dry-run=client -o yaml
```

```
apiVersion: apps/v1
kind: Deployment
metadata:
  creationTimestamp: null
  labels:
    app: web
  name: web
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  strategy: {}
  template:
    metadata:
      creationTimestamp: null
      labels:
        app: web
    spec:
      containers:
      - image: nginx:1.27
        name: nginx
        ports:
        - containerPort: 80
        resources: {}
status: {}
```

→ Note what the generator decided for you: the label `app: web`, a selector matching it, and the
container name `nginx` (derived from the image). Those names matter later: `kubectl set image`
needs the container name, and a Service selector needs the label.

**Hands-on lab (test VM only)**

**Step 1 — generate, edit, apply.** Create a pod manifest that runs `sleep 3600` and add a
readiness probe by hand.

```bash
kubectl run sleeper --image=busybox:1.36 --restart=Never --dry-run=client -o yaml -- sleep 3600 > sleeper.yaml
vim sleeper.yaml                       # add readinessProbe: exec: command: ["true"]
kubectl apply -f sleeper.yaml
```

**Step 2 — break.** Generate with `--command` and without, and compare the YAML: without
`--command`, words after `--` become `args` (they replace the image's CMD); with `--command` they
become `command` (they replace the ENTRYPOINT). Run `kubectl run t1 --image=nginx:1.27 -- sleep 60`
and see that nginx's entrypoint receives `sleep 60` as arguments.

**Step 3 — validate before applying.** `kubectl apply -f FILE --dry-run=server` sends the object
through validation and admission without saving it; `kubectl diff -f FILE` shows the change. Use
both before touching anything that matters.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Indentation or tab in YAML | `error converting YAML to JSON: yaml: line 14: found character that cannot start any token` | `kubectl apply --dry-run=client -f FILE` | — |
| Unknown or misplaced field | `strict decoding error: unknown field "spec.containers[0].livenessprobe"` | `kubectl explain pod.spec.containers` | — |
| args vs command confusion | container exits immediately or runs the wrong binary | `kubectl get pod POD -o jsonpath='{.spec.containers[0].command} {.spec.containers[0].args}'` | area 5 |

**Why it matters for troubleshooting.** Generated YAML is known-good. When a hand-written manifest
fails, generating the same object and diffing it against yours finds the mistake in seconds.

**Next step.** Make all of this fast with aliases.

### Aliases and exam-speed shell setup

**Level:** [L1 · Junior] · CKA: exam speed

**Concept.** The CKA is about 2 hours of typing. Shortcuts that save 5 seconds per command save
10–15 minutes overall. The exam terminal usually has `k` and completion preconfigured; check on the
first task and add the rest yourself in under a minute.

**Key terms**

| Shortcut | Expands to | Note |
|---|---|---|
| `k` | `kubectl` | with completion attached |
| `$do` | `--dry-run=client -o yaml` | `k run x --image=nginx $do > x.yaml` |
| `$now` | `--force --grace-period 0` | instant deletion: see warning below |
| `k config set-context --current --namespace=NS` | change default namespace | avoids forgetting `-n` |
| `:set paste` in vim | stop auto-indent mangling pasted YAML | |

**See it on a real system**

```bash
cat <<'EOT' >> ~/.bashrc
source <(kubectl completion bash)
alias k=kubectl
complete -o default -F __start_kubectl k
export do="--dry-run=client -o yaml"
export now="--force --grace-period 0"
EOT
cat <<'EOT' >> ~/.vimrc
set expandtab
set tabstop=2
set shiftwidth=2
EOT
source ~/.bashrc
k get po -A | head -3
```

> Warning: `--force --grace-period 0` removes the pod object immediately without waiting for the
> container to stop. On a real cluster the process may still be running on the node (especially if
> the node is unreachable), and for StatefulSets that can mean two pods writing the same volume.
> Use a normal `kubectl delete pod` (30-second graceful stop) or `kubectl rollout restart` first;
> keep `$now` for exam pods and lab cleanup only.

**Hands-on lab (test VM only)**

**Step 1 — time yourself.** Create a Deployment, expose it as NodePort, scale it to 4, and change
its image, using only imperative commands. Target: under 90 seconds.

**Step 2 — break.** Open a generated YAML in vim without the `.vimrc` above and paste a block
from the docs: indentation explodes. Fix with `:set paste` before pasting, or the `.vimrc`.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Completion not attached to `k` | Tab does nothing after `k` | `complete -p k` | — |
| Pasted YAML mangled | `mapping values are not allowed in this context` | `:set paste` | — |

**Why it matters for troubleshooting.** Speed is not just for exams: during an incident, typing
fluency keeps your attention on the evidence instead of on syntax.

**Next step.** The unit of everything: Pods.

---

## 5. Pods

> 📚 **Study path:** 1) KodeKloud: *Kubernetes for the Absolute Beginners – Hands-on Tutorial* — PODs ([course](https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners-hands-on-tutorial)), then *Certified Kubernetes Administrator (CKA)* — Application Lifecycle Management for multi-container and init containers ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Docker](30-learn-docker.md) for PID 1, signals and exit codes · 3) Optional deep dive: the Multi-Container PODs and Observability (probes) modules of *Certified Kubernetes Application Developer (CKAD)* ([course](https://kodekloud.com/courses/certified-kubernetes-application-developer-ckad)) · 4) Practice: the Crashing Pods and Create Container Errors scenarios in *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)).

### Pod anatomy, phases and container states

**Level:** [L1 · Junior] · CKA: Workloads & Scheduling, Troubleshooting

**Concept.** A pod is one or more containers that share a network namespace (one IP, one
`localhost`, one port space) and can share volumes. The kubelet first starts a tiny **pause**
container that owns the network namespace, then the app containers join it. That is why an app
container can restart without the pod losing its IP. Pods are disposable: you rarely create them
directly; controllers do.

```
 Pod web-7c9d8f6b5-2xkqp      IP 10.244.1.12 (owned by the pause container)
 +---------------------------------------------------------------+
 |  pause      app (nginx :80)      sidecar (log shipper)         |
 |     \______ shared net namespace: localhost, ports ________/   |
 |              shared volumes: emptyDir "logs", configMap ...    |
 +---------------------------------------------------------------+
```

The single most misunderstood output in Kubernetes is the `STATUS` column of `kubectl get pods`.
It is a **summary** computed by kubectl from two separate things: the pod **phase** and each
container's **state**.

**Key terms**

| Pod phase (`.status.phase`) | Meaning |
|---|---|
| Pending | accepted, but not all containers are running yet: unscheduled, pulling images, mounting volumes, init containers running |
| Running | bound to a node, at least one container running (or starting/restarting) |
| Succeeded | all containers exited 0 and will not restart |
| Failed | all containers terminated, at least one non-zero, and they will not restart |
| Unknown | the node stopped reporting (usually node down or network partition) |

| Container state | Typical reasons shown in STATUS |
|---|---|
| Waiting | `ContainerCreating`, `PodInitializing`, `ErrImagePull`, `ImagePullBackOff`, `CrashLoopBackOff`, `CreateContainerConfigError`, `CreateContainerError` |
| Running | `Running` |
| Terminated | `Completed` (exit 0), `Error` (non-zero), `OOMKilled`, `StartError` (the runtime could not start the process; `ContainerCannotRun` on old Docker-based nodes) |

| Pod condition | True when |
|---|---|
| PodScheduled | a node was chosen |
| Initialized | all init containers finished |
| ContainersReady | all containers pass readiness |
| Ready | the pod may receive Service traffic |

**See it on a real system**

```bash
kubectl -n shop get pods -o wide
kubectl -n shop get pod POD -o jsonpath='{.status.phase}{"\n"}'
kubectl -n shop get pod POD -o jsonpath='{range .status.containerStatuses[*]}{.name}{" "}{.state}{" lastState="}{.lastState}{"\n"}{end}'
kubectl -n shop describe pod POD | sed -n '/Conditions:/,/Volumes:/p'
```

```
$ kubectl -n shop get pods
NAME                   READY   STATUS             RESTARTS      AGE
web-7c9d8f6b5-2xkqp    1/1     Running            0             2h
api-5d8f7c9b4-k8x2m    0/1     Running            0             3m
worker-6b7c8d9-q2w3e   0/1     CrashLoopBackOff   6 (2m ago)    9m
batch-x7k2p            0/1     Completed          0             1h
db-0                   1/2     Running            3 (5m ago)    2d
```

→ `api` is Running but `0/1` READY: the process runs but fails its readiness probe, so it gets no
Service traffic. `worker` has phase Running but its container is Waiting with reason
CrashLoopBackOff. `batch` is phase Succeeded. `db-0` has one of two containers not ready; name it
with `describe`.

**Hands-on lab (test VM only)**

**Step 1 — make every status appear on purpose.**

```bash
kubectl -n shop run ok   --image=busybox:1.36 --restart=Never -- sh -c 'echo done'          # Completed
kubectl -n shop run fail --image=busybox:1.36 --restart=Never -- sh -c 'exit 3'             # Error
kubectl -n shop run loop --image=busybox:1.36 -- sh -c 'echo starting; exit 1'              # CrashLoopBackOff
kubectl -n shop run pull --image=busybox:9.99-nope                                          # ImagePullBackOff
kubectl -n shop run cfg  --image=busybox:1.36 --overrides='{"spec":{"containers":[{"name":"cfg","image":"busybox:1.36","command":["sleep","3600"],"envFrom":[{"configMapRef":{"name":"missing"}}]}]}}'   # CreateContainerConfigError
kubectl -n shop get pods -w
```

**Step 2 — read each one.** For every pod run `kubectl -n shop describe pod NAME` and find the
line that explains it (Events, State, Last State, Exit Code). Then fix `cfg` with
`kubectl -n shop create configmap missing --from-literal=A=1` and watch it start without being
recreated: the kubelet retries on its own.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Pod never scheduled | `Pending`, NODE empty, `FailedScheduling` event | `kubectl describe pod POD` | area 12 |
| Volume or sandbox problem | `ContainerCreating` for minutes | `kubectl describe pod POD` (FailedMount, FailedCreatePodSandBox) | area 11 |
| Missing ConfigMap/Secret key | `CreateContainerConfigError`: `configmap "missing" not found` | `kubectl describe pod POD` | area 10 |
| Node lost | `Unknown` or stuck `Terminating` | `kubectl get nodes` | area 18 |

**Why it matters for troubleshooting.** The STATUS word tells you *which step* of the life of a
pod failed; the step tells you which command to run next. Never debug "the pod is broken"; debug
"the container is Waiting with reason X".

**Next step.** What happens when a container exits, and why it ends up in CrashLoopBackOff.

### restartPolicy, exit codes and CrashLoopBackOff

**Level:** [L2 · Mid] · CKA: Troubleshooting

**Concept.** `restartPolicy` is per pod: `Always` (default, and the only value Deployments allow),
`OnFailure`, or `Never` (Jobs use the last two). When a container exits and policy says restart,
the kubelet restarts it **in the same pod** with an exponential back-off: 10 s, 20 s, 40 s... capped
at 5 minutes, and reset after the container has run cleanly for 10 minutes. While it waits, the
STATUS shows `CrashLoopBackOff`. CrashLoopBackOff is not a cause, it is "it keeps exiting": the
cause is in the previous container's logs and exit code.

**Key terms**

| Exit code | Meaning | Typical cause |
|---|---|---|
| 0 | clean exit | a server process that should not exit did (wrong command, daemonised itself) |
| 1, 2, other small | application error | config, missing env var, cannot reach DB |
| 126 | not executable | wrong permissions or wrong architecture binary |
| 127 | command not found | a shell (`sh -c '...'`) could not find a command: typo, missing binary in the image. An exec-form `command` whose binary is missing never starts at all: reason `StartError`, exit 128 |
| 128+N | killed by signal N | 137 = SIGKILL (OOMKilled or liveness kill after grace), 143 = SIGTERM, 139 = SIGSEGV |

**See it on a real system**

```bash
kubectl -n shop logs POD --previous                  # logs of the crashed instance, not the new one
kubectl -n shop describe pod POD | grep -A6 'Last State'
kubectl -n shop get pod POD -o jsonpath='{.status.containerStatuses[0].lastState.terminated}{"\n"}'
```

```
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
      Started:      Fri, 03 Oct 2026 10:12:41 +0000
      Finished:     Fri, 03 Oct 2026 10:12:44 +0000
    Ready:          False
    Restart Count:  5
```

→ Reason OOMKilled with exit 137: the container exceeded its memory **limit** (area 12). Without
`--previous`, `kubectl logs` shows the *new* container, which may have printed nothing yet.

**Hands-on lab (test VM only)**

**Step 1 — build an OOM on purpose.** `tail /dev/zero` reads an endless line and keeps growing its
buffer, so it exceeds any limit.

```bash
cat <<'EOT' > hog.yaml
apiVersion: v1
kind: Pod
metadata:
  name: hog
  namespace: shop
spec:
  containers:
  - name: hog
    image: busybox:1.36
    command: ["sh", "-c", "tail /dev/zero"]
    resources:
      requests:
        memory: "32Mi"
      limits:
        memory: "64Mi"
EOT
kubectl apply -f hog.yaml
kubectl -n shop get pod hog -w
```

**Step 2 — observe.** STATUS alternates `OOMKilled` and `CrashLoopBackOff`; `describe` shows
exit 137. On the node, `journalctl -k | grep -i 'killed process'` shows the cgroup OOM kill
([Memory](04-memory.md)).

**Step 3 — fix.** In real life you first check for a leak, then right-size. Here, change the
command to something sane and re-create the pod (pod specs are mostly immutable; this is why you
use Deployments).

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| App config error | CrashLoopBackOff, exit 1, log shows the error | `kubectl logs POD --previous` | [26](26-playbook-containers-k8s.md) |
| Memory limit too low or leak | `OOMKilled`, exit 137 | `kubectl describe pod POD` (Last State) | [Memory](04-memory.md) |
| Wrong command | `StartError`, exit 128, `exec: "sh -c": executable file not found in $PATH` (whole string in one array item); exit 127 when a shell cannot find the command | `kubectl get pod POD -o yaml` (command/args) | area 4 |
| Process exits 0 | `Completed` then CrashLoopBackOff in a Deployment | check the image CMD runs in the foreground | [Docker](30-learn-docker.md) |
| Liveness probe kills it | restarts with events `Liveness probe failed` | `kubectl describe pod POD` | next topics |

**Why it matters for troubleshooting.** The exit code plus `logs --previous` explains most crash
loops in under a minute. The same codes appear in `docker ps -a` ([Docker reference](14-docker-containers.md)).

**Next step.** Pods with more than one container.

### Init containers, sidecars and multi-container patterns

**Level:** [L2 · Mid] · CKA: Workloads & Scheduling

**Concept.** **Init containers** run one after another *before* the app containers, and each must
exit 0. They are for preparation: wait for a dependency, run a migration, fetch config, fix
permissions on a volume. **Sidecars** run *alongside* the app for the pod's whole life: log
shippers, proxies, certificate reloaders. Since Kubernetes 1.33 native sidecars are stable: an init
container with `restartPolicy: Always` starts before the app, keeps running, and is stopped after
the app on shutdown.

```
 time --->
 init-1 (wait-for-db) [====] exit 0
 init-2 (migrate)            [======] exit 0
 sidecar (init, restartPolicy: Always)  [=================================]
 app                                     [==========================]
```

**Key terms**

| Pattern | What the extra container does | Example |
|---|---|---|
| Init | prepares, then exits | wait for DNS of `db`, run DB migration |
| Sidecar | extends the app for its lifetime | log shipper reading a shared `emptyDir` |
| Ambassador | proxies outbound connections for the app | local proxy to a database cluster |
| Adapter | converts the app's output to a standard format | metrics exporter for a legacy app |

STATUS while init runs: `Init:0/2`, `Init:1/2`, `Init:Error`, `Init:CrashLoopBackOff`, then
`PodInitializing`.

**See it on a real system**

```bash
kubectl -n shop get pod POD -o jsonpath='{.spec.initContainers[*].name}{"\n"}{.spec.containers[*].name}{"\n"}'
kubectl -n shop logs POD -c INIT_CONTAINER_NAME
kubectl -n shop logs POD --all-containers --prefix
```

**Hands-on lab (test VM only)**

**Step 1 — build** a pod with an init container that waits for a Service named `db`, and a native
sidecar that tails the app's log file from a shared volume.

```bash
cat <<'EOT' > multi.yaml
apiVersion: v1
kind: Pod
metadata:
  name: multi
  namespace: shop
spec:
  initContainers:
  - name: wait-for-db
    image: busybox:1.36
    command: ["sh", "-c", "until nslookup db.shop.svc.cluster.local; do echo waiting for db; sleep 2; done"]
  - name: log-shipper
    image: busybox:1.36
    restartPolicy: Always
    command: ["sh", "-c", "touch /var/log/app/app.log; tail -F /var/log/app/app.log"]
    volumeMounts:
    - name: logs
      mountPath: /var/log/app
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "while true; do date >> /var/log/app/app.log; sleep 5; done"]
    volumeMounts:
    - name: logs
      mountPath: /var/log/app
  volumes:
  - name: logs
    emptyDir: {}
EOT
kubectl apply -f multi.yaml
kubectl -n shop get pod multi -w
```

**Step 2 — observe the break.** There is no `db` Service, so STATUS stays `Init:0/2`.
`kubectl -n shop logs multi -c wait-for-db` prints `waiting for db` forever. The pod is not broken;
it is waiting for its dependency, exactly as designed.

**Step 3 — fix.** Create the dependency: `kubectl -n shop create service clusterip db --tcp=5432:5432`.
The init container finishes, the sidecar starts, then the app. Check the sidecar:
`kubectl -n shop logs multi -c log-shipper -f`.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Dependency missing | `Init:0/N` forever | `kubectl logs POD -c INIT` | area 9 |
| Init container fails | `Init:Error` / `Init:CrashLoopBackOff` | `kubectl logs POD -c INIT --previous` | [26](26-playbook-containers-k8s.md) |
| Logs command without `-c` | kubectl silently picks a default and prints `Defaulted container "app" out of: app, wait-for-db (init), log-shipper (init)`, so you read the wrong container's log | add `-c NAME` or `--all-containers --prefix` | — |
| Sidecar crashes | READY `1/2`, restarts on the sidecar only | `kubectl describe pod POD` | — |

**Why it matters for troubleshooting.** "Stuck in Init" is almost always a dependency (DNS, a
Service, a database, a permission on a volume) rather than the app. Read the init container's logs
before anything else.

**Next step.** Probes: how Kubernetes decides a container is alive and ready.

### Probes: liveness, readiness, startup

**Level:** [L2 · Mid] · CKA: Workloads & Scheduling, Troubleshooting

**Concept.** The kubelet runs probes against each container. **Readiness** answers "may this pod
receive traffic now?"; failing it removes the pod from Service endpoints but does not restart it.
**Liveness** answers "is this process hopelessly stuck?"; failing it restarts the container.
**Startup** answers "has the app finished starting?"; until it succeeds, liveness and readiness are
not run, which protects slow starters from being killed. Probe types: `httpGet` (2xx/3xx = success),
`tcpSocket`, `exec` (exit 0), `grpc`.

```
 container starts
   |-- startupProbe (if defined) ... success --> liveness + readiness begin
   |                                  failureThreshold x periodSeconds exceeded --> restart
   |-- readinessProbe fails --> Ready=False --> removed from EndpointSlices (no traffic, no restart)
   |-- livenessProbe fails failureThreshold times --> container killed and restarted
```

**Key terms**

| Field | Default | Meaning |
|---|---|---|
| `initialDelaySeconds` | 0 | wait before the first probe |
| `periodSeconds` | 10 | how often |
| `timeoutSeconds` | 1 | per-probe timeout (a slow `/health` counts as a failure) |
| `failureThreshold` | 3 | consecutive failures before acting |
| `successThreshold` | 1 | consecutive successes to be considered OK (must be 1 for liveness/startup) |

**See it on a real system**

```bash
kubectl -n shop get pod POD -o jsonpath='{.spec.containers[0].livenessProbe}{"\n"}{.spec.containers[0].readinessProbe}{"\n"}'
kubectl -n shop describe pod POD | grep -E 'Liveness|Readiness|Startup|Unhealthy|Killing'
kubectl -n shop get events --field-selector reason=Unhealthy
```

```
  Warning  Unhealthy  14s (x3 over 34s)  kubelet  Liveness probe failed: HTTP probe failed with statuscode: 404
  Normal   Killing    14s                kubelet  Container web failed liveness probe, will be restarted
  Warning  Unhealthy  4s (x6 over 54s)   kubelet  Readiness probe failed: Get "http://10.244.1.12:8080/ready": dial tcp 10.244.1.12:8080: connect: connection refused
```

→ The liveness probe path returns 404 (wrong path), so the kubelet restarts a healthy container.
The readiness probe targets 8080 but nginx listens on 80: connection refused, pod never Ready.

**Hands-on lab (test VM only)**

**Step 1 — build** a Deployment with correct probes.

```bash
cat <<'EOT' > probes.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: probed
  namespace: shop
spec:
  replicas: 2
  selector:
    matchLabels:
      app: probed
  template:
    metadata:
      labels:
        app: probed
    spec:
      containers:
      - name: web
        image: nginx:1.27
        ports:
        - containerPort: 80
        startupProbe:
          httpGet: {path: /, port: 80}
          failureThreshold: 30
          periodSeconds: 2
        readinessProbe:
          httpGet: {path: /, port: 80}
          periodSeconds: 5
        livenessProbe:
          httpGet: {path: /, port: 80}
          periodSeconds: 10
          failureThreshold: 3
EOT
kubectl apply -f probes.yaml
kubectl -n shop expose deploy probed --port=80
kubectl -n shop get endpointslices -l kubernetes.io/service-name=probed
```

**Step 2 — break readiness.** `kubectl -n shop edit deploy probed` and set the readiness
port to 8080. New pods stay `0/1`; because the rollout cannot make progress, the old pods keep serving
(area 6). The EndpointSlice lists only the old pods.

**Step 3 — break liveness.** Restore readiness, set the liveness path to `/healthz`. Pods become
Ready, then restart every ~30 seconds (3 failures x 10 s). Watch RESTARTS climb.

**Step 4 — fix** both and re-apply `probes.yaml`.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Wrong readiness path/port | `Running` but `0/1`; Service has no endpoints; 503 from ingress | `kubectl describe pod POD` (Unhealthy events) | area 7 |
| Liveness too aggressive | restarts under load or during slow start; exit 137 or 143 in Last State | `kubectl describe pod POD` | [26](26-playbook-containers-k8s.md) |
| Liveness checks a dependency (DB) | DB blip restarts every pod at once: a cascading outage | review probe design | — |
| `timeoutSeconds: 1` on a slow endpoint | intermittent `context deadline exceeded` probe failures | raise the timeout, use a cheap endpoint | [Slow system](23-playbook-slow-system.md) |

**Why it matters for troubleshooting.** Probes are the bridge between "process runs" and "traffic
flows". A misconfigured probe is the most common cause of "Running but unreachable" and of
mysterious restarts that leave no application error in the logs.

**Next step.** How pods stop, and how to stop them without dropping requests.

### Termination and graceful shutdown

**Level:** [L2 · Mid] · CKA: Workloads & Scheduling

**Concept.** When a pod is deleted (rollout, scale-down, drain), two things happen **in parallel**:
the pod is removed from EndpointSlices (so kube-proxy and ingress controllers stop sending new
traffic), and the kubelet runs the `preStop` hook, then sends **SIGTERM** to PID 1 of each
container. After `terminationGracePeriodSeconds` (default 30) anything still running gets
**SIGKILL**. Because the two paths race, a pod can receive a few new requests after SIGTERM; a
short `preStop` sleep closes that gap.

A process running as **PID 1** in a container gets no default signal handlers: unless it installs
a SIGTERM handler, SIGTERM does nothing. `sleep 3600` as PID 1 therefore always waits the full
30 seconds and dies by SIGKILL.

**Key terms**

| Term | Meaning |
|---|---|
| `terminationGracePeriodSeconds` | time between SIGTERM and SIGKILL (pod level) |
| `preStop` hook | command or HTTP call run before SIGTERM, counted inside the grace period |
| Exit 143 | stopped by SIGTERM (graceful) |
| Exit 137 | SIGKILL: grace period exceeded, or OOM |
| Finalizers | metadata that blocks deletion until a controller removes it (stuck `Terminating`) |

**See it on a real system**

```bash
kubectl -n shop get pod POD -o jsonpath='{.spec.terminationGracePeriodSeconds}{"\n"}'
kubectl -n shop get pod POD -o jsonpath='{.metadata.finalizers}{"\n"}'
time kubectl -n shop delete pod POD          # how long did graceful shutdown take?
```

**Hands-on lab (test VM only)**

> Warning: these steps delete pods. They are lab pods you created; on a real cluster use
> `kubectl rollout restart` and let the controller replace pods one at a time.

**Step 1 — observe the PID 1 problem.**

```bash
kubectl -n shop run stubborn --image=busybox:1.36 -- sleep 3600
time kubectl -n shop delete pod stubborn         # ~30 s: sleep ignores SIGTERM as PID 1
```

**Step 2 — fix with signal handling.** Install a trap so the shell (PID 1) handles SIGTERM:

```bash
kubectl -n shop run polite --image=busybox:1.36 -- sh -c 'trap "echo got TERM; exit 0" TERM; while true; do sleep 1; done'
time kubectl -n shop delete pod polite           # ~1-2 s
```

**Step 3 — add a preStop gap** in a Deployment so in-flight and late-arriving requests finish:

```bash
kubectl -n shop patch deploy probed --type=json -p='[{"op":"add","path":"/spec/template/spec/containers/0/lifecycle","value":{"preStop":{"exec":{"command":["sh","-c","sleep 5"]}}}}]'
```

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| App ignores SIGTERM | every deploy takes 30 s per pod; exit 137 in Last State | `kubectl describe pod POD` | [Docker](30-learn-docker.md) |
| No preStop gap | a burst of 502/503 at each rollout | ingress/Traefik logs during a rollout | [Site down](25-playbook-site-down.md) |
| Stuck finalizer | pod or namespace stuck in `Terminating` | `kubectl get pod POD -o jsonpath='{.metadata.finalizers}'` | [Kubernetes reference](15-kubernetes.md) |
| Node unreachable | pods stuck `Terminating` on that node | `kubectl get nodes` | area 18 |

**Why it matters for troubleshooting.** Deploy-time errors (short bursts of 502s, slow rollouts)
are nearly always termination problems, not capacity problems.

**Next step.** Deployments: the controller that manages all of this for you.

---

## 6. Deployments, ReplicaSets and autoscaling

> 📚 **Study path:** 1) KodeKloud: *Kubernetes for the Absolute Beginners – Hands-on Tutorial* — Deployments and the rolling update labs ([course](https://kodekloud.com/courses/kubernetes-for-the-absolute-beginners-hands-on-tutorial)), then *Certified Kubernetes Administrator (CKA)* — Application Lifecycle Management ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Deployment patterns](35-deployment-patterns.md) for rolling vs blue/green vs canary · 3) Video: KodeKloud *Kubernetes Crash Course: Learn the Basics and Build a Microservice Application*, the deployment part ([YouTube](https://www.youtube.com/watch?v=XuSQU5Grv1g)) · 4) Practice: the bad-tag rollout and rollback lab below until `rollout undo` is a reflex.

### Deployment, ReplicaSet and Pod

**Level:** [L1 · Junior] · CKA: Workloads & Scheduling

**Concept.** A **ReplicaSet** keeps N identical pods running (matching a label selector). A
**Deployment** manages ReplicaSets: every change to the pod template creates a new ReplicaSet and
shifts pods from old to new. Pods get a `pod-template-hash` label so each ReplicaSet only counts
its own pods. You manage Deployments; you almost never touch ReplicaSets directly.

```
 Deployment web (replicas 3, template image nginx:1.27 -> nginx:1.28)
   |-- ReplicaSet web-7c9d8f6b5 (hash for 1.27)  desired 0  <- old revision, kept for rollback
   |-- ReplicaSet web-5f6d4c8b9 (hash for 1.28)  desired 3
          |-- pod web-5f6d4c8b9-a1b2c
          |-- pod web-5f6d4c8b9-d3e4f
          |-- pod web-5f6d4c8b9-g5h6i
```

**Key terms**

| Field | Meaning |
|---|---|
| `spec.selector` | which pods this Deployment owns; immutable after creation |
| `spec.template` | the pod blueprint; any change here triggers a rollout |
| `revisionHistoryLimit` | old ReplicaSets kept for rollback (default 10) |
| `progressDeadlineSeconds` | after this (default 600) without progress the rollout is marked failed |
| `minReadySeconds` | how long a new pod must stay Ready before it counts as available |
| `ownerReferences` | link from pod to RS to Deployment; used for garbage collection |

**See it on a real system**

```bash
kubectl -n shop get deploy,rs,pods -l app=web
kubectl -n shop get pod POD -o jsonpath='{.metadata.ownerReferences[0].kind}/{.metadata.ownerReferences[0].name}{"\n"}'
kubectl -n shop describe deploy web | sed -n '/Conditions:/,/Events:/p'
```

```
NAME                  READY   UP-TO-DATE   AVAILABLE   AGE
deployment.apps/web   3/3     3            3           2d

NAME                             DESIRED   CURRENT   READY   AGE
replicaset.apps/web-5f6d4c8b9    3         3         3       1h
replicaset.apps/web-7c9d8f6b5    0         0         0       2d
```

→ UP-TO-DATE = pods running the newest template; AVAILABLE = Ready for at least `minReadySeconds`.
The old ReplicaSet at 0 is your rollback target.

**Hands-on lab (test VM only)**

**Step 1 — build and inspect.** Create `web` with 3 replicas (area 1) and follow the
ownerReferences chain from a pod up to the Deployment.

**Step 2 — break the selector.** Try to change `spec.selector.matchLabels` with `kubectl edit`:
the API rejects it (`field is immutable`). Now create a bare pod with label `app=web`:
`kubectl -n shop run intruder --image=nginx:1.27 --labels=app=web`. The ReplicaSet does *not*
adopt it (it lacks the `pod-template-hash` label), but a Service selecting `app=web` *will* send
traffic to it. Labels are powerful and global within a namespace.

**Step 3 — fix.** Remove the intruder (`kubectl -n shop delete pod intruder`, after checking
`kubectl -n shop get pods --show-labels`) and keep selectors specific (`app` plus `component`).

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Quota or admission rejects pods | Deployment `0/3`, no pods; RS event `FailedCreate: ... exceeded quota` | `kubectl describe rs RS` | area 12 |
| Controller-manager down | no RS created | `kubectl -n kube-system get pods` | area 20 |
| Selector overlap | traffic goes to unexpected pods | `kubectl get pods -l KEY=VALUE --show-labels` | area 7 |

**Why it matters for troubleshooting.** When a Deployment shows fewer pods than expected and there
are no pod errors, the answer is one level up: `kubectl describe rs`. Events about *creating* pods
live on the ReplicaSet, not on the pods (which do not exist yet).

**Next step.** Rolling updates and rollbacks.

### Rolling updates, history and rollback

**Level:** [L1 · Junior] · CKA: Workloads & Scheduling

**Concept.** The default strategy, `RollingUpdate`, replaces pods gradually, bounded by two numbers:
**maxSurge** (how many extra pods above `replicas` may exist) and **maxUnavailable** (how many may
be missing below `replicas`). Both default to 25%; surge rounds up, unavailable rounds down. A new
pod only counts once it is Ready, so a broken new version **stalls** the rollout instead of taking
the app down, provided readiness probes are meaningful. `Recreate` kills all old pods first
(downtime, but never two versions at once: useful for apps that cannot run side by side).

| replicas | maxSurge 25% | maxUnavailable 25% | max pods during rollout | min available |
|---|---|---|---|---|
| 4 | 1 | 1 | 5 | 3 |
| 3 | 1 (0.75 rounded up) | 0 (0.75 rounded down) | 4 | 3 |
| 10 | 3 | 2 | 13 | 8 |
| 1 | 1 | 0 | 2 | 1 |

**Key terms**

| Command | Purpose |
|---|---|
| `kubectl rollout status deploy/NAME --timeout=120s` | wait for success; non-zero exit on failure (good in CI) |
| `kubectl rollout history deploy/NAME [--revision=N]` | revisions and their change-cause |
| `kubectl rollout undo deploy/NAME [--to-revision=N]` | roll back (creates a new revision) |
| `kubectl rollout pause / resume deploy/NAME` | batch several changes into one rollout |
| `kubectl rollout restart deploy/NAME` | replace all pods gradually with the same spec |
| annotation `kubernetes.io/change-cause` | the text shown in history (the old `--record` flag is deprecated) |

**See it on a real system**

```bash
kubectl -n shop rollout history deploy/web
kubectl -n shop rollout history deploy/web --revision=2
kubectl -n shop get deploy web -o jsonpath='{.spec.strategy}{"\n"}'
```

```
deployment.apps/web
REVISION  CHANGE-CAUSE
1         initial nginx 1.27
2         upgrade to nginx 1.28
3         bad tag test
```

**Hands-on lab (test VM only)**

**Step 1 — roll forward with a recorded cause.**

```bash
kubectl -n shop scale deploy web --replicas=4
kubectl -n shop set image deploy/web nginx=nginx:1.28
kubectl -n shop annotate deploy/web kubernetes.io/change-cause="upgrade to nginx 1.28" --overwrite
kubectl -n shop rollout status deploy/web
```

**Step 2 — break.** Deploy a tag that does not exist and watch how much of the app survives.

```bash
kubectl -n shop set image deploy/web nginx=nginx:1.28-typo
kubectl -n shop annotate deploy/web kubernetes.io/change-cause="bad tag test" --overwrite
kubectl -n shop rollout status deploy/web --timeout=60s
kubectl -n shop get pods -l app=web
```

```
Waiting for deployment "web" rollout to finish: 2 out of 4 new replicas have been updated...
error: timed out waiting for the condition

NAME                   READY   STATUS             RESTARTS   AGE
web-5f6d4c8b9-a1b2c    1/1     Running            0          10m
web-5f6d4c8b9-d3e4f    1/1     Running            0          10m
web-5f6d4c8b9-g5h6i    1/1     Running            0          10m
web-6c7d8e9f0-x1y2z    0/1     ImagePullBackOff   0          60s
web-6c7d8e9f0-p9q8r    0/1     ErrImagePull       0          60s
```

→ With maxUnavailable 1 of 4, three old pods keep serving. That is the rolling update protecting
you. After `progressDeadlineSeconds` the Deployment condition becomes
`Progressing=False, reason ProgressDeadlineExceeded`, which alerting can catch.

**Step 3 — fix by rolling back**, then confirm the history.

```bash
kubectl -n shop rollout undo deploy/web
kubectl -n shop rollout status deploy/web
kubectl -n shop rollout history deploy/web
```

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| New pods never Ready | rollout stuck, `ProgressDeadlineExceeded` | `kubectl get pods` (newest RS) then `describe` | [26](26-playbook-containers-k8s.md) |
| No readiness probe | broken version becomes "available" instantly, outage | add probes (area 5) | — |
| maxUnavailable too high | capacity drop during deploy, latency spike | `kubectl get deploy NAME -o jsonpath='{.spec.strategy}'` | [Slow system](23-playbook-slow-system.md) |
| PodDisruptionBudget plus drain | not a rollout issue: rollouts ignore PDBs, evictions respect them | area 19 | — |
| Rollback target gone | `undo` fails: `unable to find specified revision` | `kubectl rollout history` (`revisionHistoryLimit`) | — |

**Why it matters for troubleshooting.** "Roll back first, diagnose second" (the Ops Ladder change
case) is one command here. Know it cold, and know how to check the rollout really finished.

**Next step.** Let the cluster choose the replica count: the HPA.

### Horizontal Pod Autoscaler

**Level:** [L2 · Mid] · CKA: Workloads & Scheduling

**Concept.** The **HPA** controller periodically (every 15 s) reads metrics from the Metrics API
(served by metrics-server, area 18) and sets `replicas` on a Deployment or StatefulSet:
`desired = ceil(current replicas x current utilisation / target utilisation)`. Utilisation is
measured **against requests**, so a container without CPU requests cannot be autoscaled on CPU.
Scale-down waits through a 5-minute stabilisation window by default to avoid flapping.

**Key terms**

| Term | Meaning |
|---|---|
| `autoscaling/v2` | the HPA API (CPU, memory, custom and external metrics, behavior tuning) |
| target utilisation | e.g. 50% of the CPU *request* across pods |
| `minReplicas` / `maxReplicas` | hard bounds |
| `behavior` | scale-up/down policies and stabilisation windows |
| VPA | a separate add-on that adjusts requests instead of replicas; not built in |

**See it on a real system**

```bash
kubectl -n shop get hpa
kubectl -n shop describe hpa php-apache | sed -n '/Metrics:/,/Events:/p'
```

```
NAME         REFERENCE               TARGETS              MINPODS   MAXPODS   REPLICAS   AGE
php-apache   Deployment/php-apache   cpu: 212%/50%        1         5         4          3m
```

→ Average CPU is 212% of the request against a target of 50%, so the HPA keeps scaling up until it
hits `maxReplicas`. `cpu: <unknown>/50%` instead means no metrics (metrics-server missing) or no
CPU request on the pods.

**Hands-on lab (test VM only)**

**Step 1 — build** (requires metrics-server from area 18). This uses the example image from the
Kubernetes HPA walkthrough, which burns CPU on each request.

```bash
kubectl -n shop create deployment php-apache --image=registry.k8s.io/hpa-example --port=80
kubectl -n shop set resources deploy php-apache --requests=cpu=200m --limits=cpu=500m
kubectl -n shop expose deploy php-apache --port=80
kubectl -n shop autoscale deploy php-apache --min=1 --max=5 --cpu-percent=50   # check --help: newer kubectl may name this flag differently
kubectl -n shop get hpa -w
```

**Step 2 — load it.**

```bash
kubectl -n shop run load --rm -it --image=busybox:1.36 --restart=Never -- sh -c 'while true; do wget -q -O- http://php-apache >/dev/null; done'
```

**Step 3 — break.** Remove the whole `resources` block (removing only the request is not enough:
when a limit is set, the request defaults to the limit), then watch TARGETS turn to `<unknown>` and
`describe hpa` report `failed to get cpu utilization: missing request for cpu`.

```bash
kubectl -n shop patch deploy php-apache --type=json -p='[{"op":"remove","path":"/spec/template/spec/containers/0/resources"}]'
```

**Step 4 — fix** by restoring the request. Stop the load and watch it scale down after about five
minutes.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| No metrics-server | `<unknown>/50%`; `unable to get metrics for resource cpu: no metrics returned from resource metrics API` | `kubectl top pods` | area 18 |
| No requests | `missing request for cpu` | `kubectl get deploy NAME -o yaml` (resources) | area 12 |
| HPA vs manifest replicas | every `kubectl apply` resets replicas, then HPA changes it back | remove `replicas:` from the manifest when an HPA owns it | area 1 |
| Max too low | pinned at maxReplicas, latency rises | `kubectl get hpa` | [Slow system](23-playbook-slow-system.md) |

**Why it matters for troubleshooting.** Autoscaling hides capacity problems until it hits a limit,
then everything slows at once. When latency rises, `kubectl get hpa` is a 1-second check.

**Next step.** Make the pods reachable: Services (area 7).

---

## 7. Services

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Core Concepts: Services, then Networking: Pod and Service Networking ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Networking](28-learn-networking.md) for NAT, conntrack and the packet walk · 3) Deep dive: *Kubernetes Networking Deep Dive* — Services, ending with [Troubleshooting Internal Networking](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Services/Troubleshooting-Internal-Networking/page) ([course](https://kodekloud.com/courses/kubernetes-networking)) · 4) Practice: the Unreachable Pods scenario in *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)).

### Service types and the three ports

**Level:** [L2 · Mid] · CKA: Services & Networking

**Concept.** Pod IPs change every time a pod is replaced, so clients need a stable address. A
**Service** gives a set of pods (chosen by a label selector) one stable virtual IP (the ClusterIP)
and DNS name, and load-balances across the pods that are **Ready**. Three different port numbers
appear in a Service, and confusing them is the classic beginner mistake.

```
 outside client --> 192.168.56.11:30080      nodePort    (every node, range 30000-32767)
                          |
                          | kube-proxy DNAT
 pod in cluster --> 10.96.120.15:80          port        (the Service's own port; ClusterIP:port)
   "web.shop:80"          |
                          | load-balanced to a Ready endpoint
                          v
                    10.244.1.12:8080         targetPort  (where the container really listens)
```

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
  namespace: shop
spec:
  type: NodePort
  selector:
    app: web
  ports:
  - name: http
    port: 80            # clients use this
    targetPort: 8080    # container listens here (a number or a named containerPort)
    nodePort: 30080     # optional; auto-assigned from 30000-32767 if omitted
```

**Key terms**

| Type | What you get | On-prem notes |
|---|---|---|
| ClusterIP (default) | virtual IP reachable only inside the cluster | the building block of all the others |
| NodePort | ClusterIP + the same port opened on every node | what you use for quick external tests |
| LoadBalancer | NodePort + an external IP from a load-balancer implementation | on bare metal you need MetalLB, kube-vip or Cilium LB IPAM, otherwise EXTERNAL-IP stays `<pending>` forever |
| Headless (`clusterIP: None`) | no virtual IP; DNS returns the pod IPs | StatefulSets, client-side load balancing |
| ExternalName | DNS CNAME to an outside name; no proxying | aliases for external databases or APIs |
| `externalTrafficPolicy: Local` | NodePort/LB traffic only to pods on the receiving node; client IP preserved | default `Cluster` hides the client IP behind SNAT |

**See it on a real system**

```bash
kubectl -n shop get svc -o wide
kubectl -n shop describe svc web | grep -E 'Selector|Type|IP:|Port|TargetPort|NodePort|Endpoints'
kubectl -n shop get endpointslices -l kubernetes.io/service-name=web
kubectl run t --rm -it --restart=Never --image=nicolaka/netshoot -n shop -- curl -sv http://web/ 2>&1 | head -15
```

```
$ kubectl -n shop get svc -o wide
NAME   TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE   SELECTOR
web    NodePort   10.96.120.15   <none>        80:30080/TCP   5m    app=web
```

→ `80:30080/TCP` reads as "Service port 80, node port 30080". The targetPort is not shown here;
`describe` or `-o yaml` shows it.

**Hands-on lab (test VM only)**

**Step 1 — build.** Run an app that listens on 8080 so the three ports are all different.

```bash
kubectl -n shop create deployment echo --image=traefik/whoami --replicas=2 -- /whoami --port=8080
kubectl -n shop expose deploy echo --port=80 --target-port=8080 --type=NodePort
kubectl -n shop get svc echo
curl -s http://192.168.56.11:$(kubectl -n shop get svc echo -o jsonpath='{.spec.ports[0].nodePort}')/ | grep Hostname
```

→ Repeat the curl a few times: the `Hostname:` line alternates between the two pods. The node you
called (w1) does not even need to run one of them.

**Step 2 — break the targetPort.** `kubectl -n shop patch svc echo -p '{"spec":{"ports":[{"port":80,"targetPort":9090}]}}'`.
From a netshoot pod, `curl http://echo` gives `Connection refused`: the packet reaches the pod, but
nothing listens on 9090.

**Step 3 — break the selector instead.** Restore 8080, then
`kubectl -n shop patch svc echo -p '{"spec":{"selector":{"app":"echoo"}}}'`. The error is
*also* `Connection refused` (kube-proxy installs a reject rule for Services with no endpoints).
Same error, different cause: the EndpointSlice tells them apart.

**Step 4 — fix** both and confirm with `kubectl -n shop get endpointslices -l kubernetes.io/service-name=echo`.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Selector matches no pods | `Connection refused`; no endpoints | `kubectl get endpointslices -l kubernetes.io/service-name=SVC` | [26](26-playbook-containers-k8s.md) |
| Pods not Ready | endpoints listed as not ready; 503 from ingress | `kubectl get pods -l KEY=VALUE` (READY column) | area 5 |
| Wrong targetPort | `Connection refused` with endpoints present | `kubectl describe svc SVC` vs `containerPort` | this topic |
| App listens on 127.0.0.1 in the container | refused via Service, works via `kubectl exec ... curl localhost` | `kubectl exec POD -- ss -ltn` (or netshoot) | [Ports inventory](22-playbook-ports-inventory.md) |
| LoadBalancer on bare metal | EXTERNAL-IP `<pending>` forever | install MetalLB or use NodePort/Ingress | area 8 |
| NodePort blocked | works from inside, times out from LAN | node firewall for 30000–32767 | [Network](02-network.md) |

**Why it matters for troubleshooting.** "Running but unreachable" is decided at the Service layer
nine times out of ten: selector, readiness, or port mapping. Check those three before touching the
network.

**Next step.** How a Service finds pods, and the special Service kinds.

### Selectors, EndpointSlices, headless and ExternalName

**Level:** [L2 · Mid] · CKA: Services & Networking

**Concept.** The **EndpointSlice controller** watches pods matching each Service's selector and
writes their IPs and readiness into EndpointSlice objects (at most 100 endpoints per slice by
default). kube-proxy, CoreDNS and ingress controllers read EndpointSlices. The older `Endpoints`
API still exists but is deprecated since v1.33, and `kubectl get endpoints` prints a warning.
A Service **without** a selector gets no automatic slices: you can write one by hand to give an
outside server (say, a legacy app still on Apache at 192.168.56.50) a cluster-internal name.

**Key terms**

| Term | Meaning |
|---|---|
| EndpointSlice | list of endpoint IPs, ports and conditions (`ready`, `serving`, `terminating`) for one Service |
| label `kubernetes.io/service-name` | links a slice to its Service |
| Headless Service | `clusterIP: None`; DNS returns one A record per ready pod |
| ExternalName | `spec.externalName: db.example.com`; DNS CNAME, no ports, no proxy |
| Selector-less Service | Service plus hand-written EndpointSlice pointing outside the cluster |

**See it on a real system**

```bash
kubectl -n shop get endpointslices -l kubernetes.io/service-name=echo -o wide
kubectl -n shop get endpointslice SLICE -o jsonpath='{range .endpoints[*]}{.addresses[0]}{" ready="}{.conditions.ready}{" node="}{.nodeName}{"\n"}{end}'
```

```
10.244.1.21 ready=true node=w1
10.244.2.14 ready=true node=w2
```

**Hands-on lab (test VM only)**

**Step 1 — headless.** Compare DNS answers for a normal and a headless Service.

```bash
kubectl -n shop create service clusterip echo-headless --clusterip=None --tcp=80:8080
kubectl -n shop patch svc echo-headless -p '{"spec":{"selector":{"app":"echo"}}}'
kubectl -n shop run dns --rm -it --restart=Never --image=nicolaka/netshoot -- sh -c 'dig +short echo.shop.svc.cluster.local; echo ---; dig +short echo-headless.shop.svc.cluster.local'
```

→ The first name returns one ClusterIP; the headless name returns each pod IP.

**Step 2 — selector-less Service to an outside server.**

```bash
cat <<'EOT' | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: legacy
  namespace: shop
spec:
  ports:
  - name: http
    port: 80
    targetPort: 80
---
apiVersion: discovery.k8s.io/v1
kind: EndpointSlice
metadata:
  name: legacy-1
  namespace: shop
  labels:
    kubernetes.io/service-name: legacy
addressType: IPv4
ports:
- name: http
  port: 80
  protocol: TCP
endpoints:
- addresses: ["192.168.56.50"]
EOT
```

**Step 3 — break ExternalName with TLS.** `kubectl -n shop create service externalname ext --external-name=example.com`.
`curl https://ext.shop.svc.cluster.local` from a pod fails certificate verification: the client
sends SNI and Host for `ext.shop.svc.cluster.local`, which the remote certificate does not cover.
ExternalName is only DNS; it does not rewrite names. Fix: call the real name, or proxy through an
ingress/egress gateway that rewrites Host and SNI.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Typo in selector | slice with no endpoints | `kubectl describe svc SVC` vs `kubectl get pods --show-labels` | [26](26-playbook-containers-k8s.md) |
| Port name mismatch in hand-written slice | traffic refused | compare `ports[].name` in Service and slice | — |
| ExternalName with HTTPS | `SSL: no alternative certificate subject name matches target host name` | `curl -v` | [TLS](18-web-http-tls.md) |
| Old tooling reads Endpoints | warning `v1 Endpoints is deprecated in v1.33+; use discovery.k8s.io/v1 EndpointSlice` | switch to EndpointSlices | — |

**Why it matters for troubleshooting.** The EndpointSlice is the single source of truth for "which
pods will get this traffic". When a Service misbehaves, read its slice before anything else.

**Next step.** What actually happens to a packet sent to a ClusterIP.

### kube-proxy: how a ClusterIP really works

**Level:** [L3 · Senior] · CKA: Services & Networking, Troubleshooting

**Concept.** A ClusterIP is not assigned to any interface. kube-proxy (a DaemonSet) watches
Services and EndpointSlices and writes NAT rules on every node, in `iptables` mode (default),
`nftables` mode (stable since v1.33, the recommended mode for new Linux clusters) or `ipvs` mode
(deprecated since v1.35; kube-proxy warns at startup when it is used). A packet to 10.96.120.15:80 is matched in the
node's NAT table and rewritten (DNAT) to one pod IP:targetPort, picked at random. conntrack
remembers the choice for the rest of the connection. This is why a ClusterIP answers on its
Service ports only and does not answer ping.

```
 pod -> 10.96.120.15:80
   nat PREROUTING/OUTPUT -> KUBE-SERVICES
      -> KUBE-SVC-XXXX (shop/web:http)        one rule per endpoint, random probability
           -> KUBE-SEP-AAAA  DNAT to 10.244.1.21:8080   (p = 0.5)
           -> KUBE-SEP-BBBB  DNAT to 10.244.2.14:8080   (rest)
```

**Key terms**

| Term | Meaning |
|---|---|
| DNAT | destination rewrite from ClusterIP:port to podIP:targetPort |
| conntrack | kernel table tracking NATed connections; `conntrack -L` |
| Reject rule | Services with no endpoints get a REJECT, hence "connection refused" |
| `KUBE-NODEPORTS` | chain matching node ports on any node address |
| `proxyMode` | iptables, nftables or ipvs; set in the `kube-proxy` ConfigMap |

**See it on a real system**

```bash
kubectl -n kube-system get ds kube-proxy
kubectl -n kube-system get cm kube-proxy -o yaml | grep -E '^\s+mode:'      # empty = iptables
curl -s http://127.0.0.1:10249/proxyMode; echo                                # on a node
sudo iptables-save -t nat | grep 'shop/echo'                                  # iptables mode
sudo nft list table ip kube-proxy | grep -A3 'shop/echo'                      # nftables mode
```

```
-A KUBE-SERVICES -d 10.96.88.41/32 -p tcp -m comment --comment "shop/echo:http cluster IP" -m tcp --dport 80 -j KUBE-SVC-6RJVQ3FKZ7WAP6GU
-A KUBE-SVC-6RJVQ3FKZ7WAP6GU -m comment --comment "shop/echo:http -> 10.244.1.21:8080" -m statistic --mode random --probability 0.50000000000 -j KUBE-SEP-2YJ6ZB7TKH3XHBUT
-A KUBE-SVC-6RJVQ3FKZ7WAP6GU -m comment --comment "shop/echo:http -> 10.244.2.14:8080" -j KUBE-SEP-QW3ORH7XNP5DU4SG
-A KUBE-SEP-2YJ6ZB7TKH3XHBUT -p tcp -m comment --comment "shop/echo:http" -m tcp -j DNAT --to-destination 10.244.1.21:8080
```

→ Read top to bottom: the ClusterIP rule jumps to the Service chain, which picks one endpoint
chain with 50% probability, which DNATs to a pod.

**Hands-on lab (test VM only)**

**Step 1 — trace one Service** through the rules above on w1.

**Step 2 — break kube-proxy.** Point its DaemonSet at a non-existent image. The DaemonSet's rolling
update replaces one pod at a time, so one node ends up with a kube-proxy stuck in
`ImagePullBackOff` and the rollout stalls there. Note which node with `-o wide`.

> Warning: this leaves one node without a working kube-proxy until you undo it. Lab only; the fix
> is the `rollout undo` in Step 4.

```bash
kubectl -n kube-system set image ds/kube-proxy kube-proxy=registry.k8s.io/kube-proxy:v0.0.0-broken
kubectl -n kube-system get pods -l k8s-app=kube-proxy -o wide
kubectl -n shop create deployment late --image=nginx:1.27 && kubectl -n shop expose deploy late --port=80
```

**Step 3 — observe the subtle part.** From a pod on the broken node, the *existing* Service `echo`
keeps working (its rules are still in the kernel), but the new Service `late` times out. From pods
on healthy nodes both work. "Old Services work, new ones do not, and only from one node" points at
kube-proxy on that node.

**Step 4 — fix.** `kubectl -n kube-system rollout undo ds/kube-proxy`, then watch the rules for
`shop/late` appear.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| kube-proxy not running on a node | new/changed Services fail from that node only | `kubectl -n kube-system get pods -l k8s-app=kube-proxy -o wide` | [26](26-playbook-containers-k8s.md) |
| `br_netfilter` missing | same-node pod-to-Service traffic fails or loses source IP | `lsmod` (area 3) | area 3 |
| conntrack table full | random connection failures under load; kernel log `nf_conntrack: table full, dropping packet` | `journalctl -k -g conntrack` | [Network speed](24-playbook-network-speed.md) |
| Pinging a ClusterIP | no reply, wrongly taken as "Service down" | test the Service port with curl instead | — |

**Why it matters for troubleshooting.** Knowing that a ClusterIP is a NAT rule turns
"the Service is down" into checkable questions: does the rule exist on this node, does it point at
the right pods, and do those pods answer on the targetPort?

**Next step.** Getting HTTP traffic from outside to Services: Ingress and the Gateway API.

---

## 8. Ingress and the Gateway API

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking: [Ingress](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Networking/Ingress/page) and Gateway API (2025 updates) ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) KodeKloud: *Kubernetes Networking Deep Dive* — Kubernetes Ingress module: [Traefik Overview](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page), [Demo Traefik Installation](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Demo-Traefik-Installation/page) ([course](https://kodekloud.com/courses/kubernetes-networking)) · 3) Note: [Web servers & proxies](29-learn-webservers-proxies.md) and the [Apache 443 case](21-case-apache-443-dokploy.md) · 4) Practice: the "What the Ingress?" scenario in *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)); reference: [Traefik docs](https://doc.traefik.io/traefik/).

### Ingress resources and controllers

**Level:** [L2 · Mid] · CKA: Services & Networking

**Concept.** An **Ingress** is a set of HTTP routing rules (host, path, TLS secret, backend
Service). It does nothing on its own: an **ingress controller** (Traefik, HAProxy, NGINX-based
controllers, cloud controllers) watches Ingress objects and configures a reverse proxy, which is
exactly what Traefik does with Docker labels in Dokploy. The controller is itself a Deployment or
DaemonSet exposed by a Service (NodePort or LoadBalancer) or by `hostNetwork`. `ingressClassName`
says which controller should handle each Ingress.

> In November 2025 the Kubernetes project announced the retirement of the community
> ingress-nginx controller, with best-effort maintenance ending in March 2026. Check its current
> status on [kubernetes.io](https://kubernetes.io/docs/) before choosing it for anything new.
> Traefik, which you already run under Dokploy, supports both Ingress and the Gateway API.

```
 browser: https://app.example.com/api
   -> DNS app.example.com -> 192.168.56.11 (node) or a MetalLB IP
   -> ingress controller Service :443 (NodePort 31443 / LoadBalancer / hostNetwork 443)
   -> controller pod (Traefik): TLS with secret app-tls, match Host + path /api
   -> Service api:80 -> EndpointSlice -> pod 10.244.2.14:8080
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: shop
  namespace: shop
spec:
  ingressClassName: traefik
  tls:
  - hosts: ["app.example.com"]
    secretName: app-tls
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: api
            port:
              number: 80
      - path: /
        pathType: Prefix
        backend:
          service:
            name: web
            port:
              number: 80
```

**Key terms**

| Term | Meaning |
|---|---|
| IngressClass | names a controller; one can be the default (annotation `ingressclass.kubernetes.io/is-default-class: "true"`) |
| pathType | `Prefix` (by path segment), `Exact`, `ImplementationSpecific` |
| TLS secret | type `kubernetes.io/tls` with `tls.crt` and `tls.key`, in the Ingress's namespace |
| Annotations | controller-specific extras (redirects, timeouts, auth); they do not port between controllers |
| Default certificate | what the controller serves when no TLS entry matches (Traefik: `TRAEFIK DEFAULT CERT`) |

**See it on a real system**

```bash
kubectl get ingressclass
kubectl get ingress -A
kubectl -n shop describe ingress shop
kubectl -n traefik get svc,pods                      # where the controller runs and listens
kubectl -n traefik logs deploy/traefik --tail=50
# Test the controller directly, bypassing DNS (Traefik exposed as NodePort 31080/31443 here)
curl -vk --resolve app.example.com:31443:192.168.56.11 https://app.example.com:31443/
curl -v -H 'Host: app.example.com' http://192.168.56.11:31080/
```

```
$ kubectl get ingress -A
NAMESPACE   NAME   CLASS     HOSTS             ADDRESS         PORTS     AGE
shop        shop   traefik   app.example.com   192.168.56.11   80, 443   3m
```

→ The ADDRESS column is filled in by the controller once it has picked up the Ingress. An empty
ADDRESS after a minute usually means no controller is handling that class.

**Hands-on lab (test VM only)**

**Step 1 — install a controller** (Traefik with Helm, area 16) exposed as NodePort, and create the
Ingress above with a self-signed TLS secret:

```bash
openssl req -x509 -nodes -days 30 -newkey rsa:2048 -keyout tls.key -out tls.crt -subj "/CN=app.example.com" -addext "subjectAltName=DNS:app.example.com"
kubectl -n shop create secret tls app-tls --cert=tls.crt --key=tls.key
kubectl -n shop create ingress shop --class=traefik --rule="app.example.com/*=web:80,tls=app-tls"
```

**Step 2 — break the class.** Set `ingressClassName: nginx` (no such controller). ADDRESS stays
empty and requests return the controller's 404: no router matched.

**Step 3 — break the backend.** Point the path at Service `webb`. Depending on the controller you
get a 404 (route skipped) or a 503 (no servers); the controller log names the missing Service.

**Step 4 — break TLS.** Delete the secret reference. The browser receives the controller's default
certificate (`TRAEFIK DEFAULT CERT` for Traefik). Fix each and re-test with the two curl commands.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Wrong or missing class | 404 from controller; ADDRESS empty | `kubectl get ingressclass` | [Site down](25-playbook-site-down.md) |
| Host mismatch | 404 `page not found` | `curl -v -H 'Host: DOMAIN' http://NODE_IP:NODEPORT/` | [Site down](25-playbook-site-down.md) |
| Backend Service missing or no endpoints | 404/503; controller log names the Service | `kubectl get endpointslices -l kubernetes.io/service-name=SVC` | area 7 |
| Wrong backend port | 502 Bad Gateway | `kubectl describe svc SVC` | [26](26-playbook-containers-k8s.md) |
| TLS secret missing, wrong namespace or wrong name | default certificate served; `no alternative certificate subject name matches` | `kubectl -n NS get secret NAME` | [TLS](18-web-http-tls.md) |
| Controller cannot bind 80/443 (hostNetwork) | controller CrashLoopBackOff: `bind: address already in use` | `sudo ss -ltnp 'sport = :443'` on the node | [Apache 443 case](21-case-apache-443-dokploy.md) |

**Why it matters for troubleshooting.** The layered walk from your site-down playbook (DNS, route,
firewall, TLS, proxy, app) maps one-to-one: DNS name, node or LB IP, NodePort/firewall, TLS secret,
controller route, Service, pod.

**Next step.** The successor API that fixes Ingress's limits.

### Gateway API

**Level:** [L3 · Senior] · CKA: Services & Networking

**Concept.** The **Gateway API** is the newer, role-oriented replacement for Ingress (GA since
2023, installed as CRDs). It splits one Ingress into objects owned by different roles: the
platform team provides a **GatewayClass** (which implementation) and a **Gateway** (listeners:
ports, protocols, hostnames, certificates); app teams attach **HTTPRoute** objects (hostnames,
path/header matches, filters, weighted backends). Features that needed controller-specific
annotations on Ingress (header matching, traffic splitting, redirects, rewrites) are standard
fields here. The CKA curriculum includes it.

```
 GatewayClass "traefik"  (cluster-scoped, controllerName of the implementation)
      ^
 Gateway "public" (ns infra)    listeners: http :80, https :443 (cert app-tls), allowedRoutes: All
      ^ parentRefs
 HTTPRoute "shop" (ns shop)     hostnames: app.example.com; /api -> api:80; / -> web:80
```

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: public
  namespace: infra
spec:
  gatewayClassName: traefik
  listeners:
  - name: http
    protocol: HTTP
    port: 80
    allowedRoutes:
      namespaces:
        from: All
---
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: shop
  namespace: shop
spec:
  parentRefs:
  - name: public
    namespace: infra
  hostnames: ["app.example.com"]
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /api
    backendRefs:
    - name: api
      port: 80
  - backendRefs:
    - name: web
      port: 80
```

**Key terms**

| Term | Meaning |
|---|---|
| GatewayClass | which controller implements Gateways of this class |
| Gateway | the actual entry point: listeners (port, protocol, hostname, TLS) and which namespaces may attach routes |
| HTTPRoute | routing rules; attaches to a Gateway through `parentRefs` |
| `allowedRoutes.namespaces.from` | `Same` (default), `All`, or `Selector` |
| ReferenceGrant | permission for a route in one namespace to use a backend or secret in another |
| Status conditions | `Accepted`, `Programmed`, `ResolvedRefs`: the controller's verdict, with reasons |

**See it on a real system**

```bash
kubectl get crd | grep gateway.networking.k8s.io
kubectl get gatewayclass
kubectl get gateway -A
kubectl get httproute -A
kubectl -n shop describe httproute shop | sed -n '/Status:/,$p'
```

```
$ kubectl get gateway -A
NAMESPACE   NAME     CLASS     ADDRESS         PROGRAMMED   AGE
infra       public   traefik   192.168.56.11   True         10m
```

**Hands-on lab (test VM only)**

**Step 1 — install** the Gateway API CRDs (standard channel) using the command from the Gateway
API project's install guide, and enable the Gateway provider of your implementation (for Traefik,
its Kubernetes Gateway provider; see the [Traefik docs](https://doc.traefik.io/traefik/)). Then
apply the YAML above.

**Step 2 — break attachment.** Change the Gateway's `allowedRoutes.namespaces.from` to `Same`. The
HTTPRoute in `shop` is now rejected: `describe httproute` shows condition `Accepted: False` with
reason `NotAllowedByListeners`.

**Step 3 — break a reference.** Restore `All`, then point a backendRef at a Service in another
namespace (`namespace: legacy`). Condition `ResolvedRefs: False`, reason `RefNotPermitted`, until
a ReferenceGrant in the `legacy` namespace allows it.

**Step 4 — fix** both and confirm `Accepted: True` and `ResolvedRefs: True`.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| CRDs not installed | `error: the server doesn't have a resource type "gateway"` | `kubectl get crd` | — |
| No controller for the class | Gateway `PROGRAMMED` stays `Unknown`/`False` | `kubectl describe gatewayclass NAME` | — |
| Route not allowed by listener | `Accepted False NotAllowedByListeners` | `kubectl describe httproute NAME` | this topic |
| Cross-namespace backend | `ResolvedRefs False RefNotPermitted` | create a ReferenceGrant | this topic |
| Backend missing | `ResolvedRefs False BackendNotFound`; 500 or 503 from the gateway | `kubectl get svc -n NS` | area 7 |

**Why it matters for troubleshooting.** Gateway API objects *tell you* why they are not working, in
status conditions. Read `describe` on the route and the Gateway before reading controller logs.

**Next step.** Translate what you run today into these objects.

### From Apache vhosts and Traefik labels to Kubernetes

**Level:** [L2 · Mid] · CKA: background for your Apache to Dokploy migration

**Concept.** Everything in your Apache/Dokploy migration has a Kubernetes equivalent. Moving a
vhost is a translation exercise; the reverse proxy concepts are identical
([Web servers & proxies](29-learn-webservers-proxies.md)).

**Key terms (translation table)**

| Apache vhost / Dokploy Traefik | Kubernetes Ingress | Gateway API |
|---|---|---|
| `Listen 443` | controller Service (NodePort/LB) or hostNetwork port | Gateway listener `port: 443` |
| `ServerName app.example.com` | `rules[].host` | HTTPRoute `hostnames` |
| `ProxyPass / http://127.0.0.1:8000/` | backend `service.name` + `port` | `backendRefs` |
| `SSLCertificateFile` / Let's Encrypt in Traefik | TLS secret (often from cert-manager) | listener `certificateRefs` |
| `RewriteRule`, redirects | controller annotations or middlewares | HTTPRoute `filters` (URLRewrite, RequestRedirect) |
| Traefik label `traefik.http.routers.app.rule=Host(...)` | Ingress rule | HTTPRoute |
| Traefik label `...loadbalancer.server.port=8000` | Service `targetPort` | Service `targetPort` |
| `apachectl -S` (list vhosts) | `kubectl get ingress -A` | `kubectl get httproute -A` |
| `/var/log/apache2/access.log` | controller pod logs | controller pod logs |

**See it on a real system**

```bash
# Apache side (old server): which vhosts exist, and which backends do they proxy to?
sudo apachectl -S
grep -RhiE 'ServerName|ProxyPass ' /etc/apache2/sites-enabled/
# Kubernetes side: every host the cluster answers for
kubectl get ingress -A -o custom-columns='NS:.metadata.namespace,NAME:.metadata.name,HOSTS:.spec.rules[*].host'
kubectl get httproute -A -o custom-columns='NS:.metadata.namespace,NAME:.metadata.name,HOSTS:.spec.hostnames'
```

**Hands-on lab (test VM only)**

**Step 1 — reproduce your incident inside Kubernetes.** On w1 (test VM) install Apache so it holds
port 80, then schedule a `hostNetwork` nginx pod onto the same node.

```bash
sudo apt-get install -y apache2                      # on w1 (test VM only)
kubectl -n shop run hostnet --image=nginx:1.27 --overrides='{"spec":{"hostNetwork":true,"nodeName":"w1"}}'
kubectl -n shop get pod hostnet -w
kubectl -n shop logs hostnet --previous
```

```
nginx: [emerg] bind() to 0.0.0.0:80 failed (98: Address already in use)
```

**Step 2 — diagnose like the real case.** On w1, `sudo ss -ltnp 'sport = :80'` shows `apache2`
holding the port: the scheduler knew nothing about Apache, because it only tracks ports used by
pods.

**Step 3 — fix.** Either "dispatch" Apache (`sudo systemctl disable --now apache2` on the test VM,
after checking which vhosts it serves), or keep the controller off host ports and expose it through
a NodePort or a MetalLB address. The second option is how you avoid this class of conflict.

**How it breaks.** See the Ingress and Gateway tables above, plus the
[Apache 443 case study](21-case-apache-443-dokploy.md) for the non-Kubernetes side.

**Why it matters for troubleshooting.** The skills from the Apache incident (who owns the port,
which app is which, where its logs are) transfer directly. On Kubernetes the inventory comes from
the API instead of `ss` and config files, which makes it faster once you know the queries.

**Next step.** The name resolution that every one of these hops depends on: cluster DNS.

---

## 9. Cluster DNS

> 📚 **Study path:** 1) Note: [DNS](08-dns.md) (systemd-resolved, `dig`, search domains) as a quick refresher · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking: [Prerequisite DNS](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Networking/Prerequisite-DNS), then [CoreDNS in Kubernetes](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/CoreDNS-in-Kubernetes/page) ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 3) Read: Kubernetes docs [Debugging DNS Resolution](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/) and the CoreDNS [loop plugin](https://coredns.io/plugins/loop) page · 4) Practice: the CoreDNS loop and "NetworkPolicy blocks port 53" cases from your Ops Ladder (labs below and drill 9).

### CoreDNS and service names

**Level:** [L2 · Mid] · CKA: Services & Networking

**Concept.** **CoreDNS** runs as a Deployment (label `k8s-app=kube-dns`) behind a Service called
`kube-dns` at a fixed ClusterIP (10.96.0.10 with the default Service CIDR). The kubelet writes
that IP into every pod's `/etc/resolv.conf`. CoreDNS answers cluster names from the API (Services,
EndpointSlices) and forwards everything else to the upstream resolvers it inherited from the node.
Its configuration, the **Corefile**, lives in the `coredns` ConfigMap.

```
 .:53 {
     errors
     health { lameduck 5s }
     ready
     kubernetes cluster.local in-addr.arpa ip6.arpa {     <- answers *.cluster.local from the API
        pods insecure
        fallthrough in-addr.arpa ip6.arpa
        ttl 30
     }
     prometheus :9153
     forward . /etc/resolv.conf { max_concurrent 1000 }  <- everything else goes upstream
     cache 30
     loop                                                <- crashes on purpose if it forwards to itself
     reload
     loadbalance
 }
```

**Key terms**

| Name | Resolves to |
|---|---|
| `SVC` (same namespace) | ClusterIP, via search domains |
| `SVC.NS` | ClusterIP of a Service in another namespace |
| `SVC.NS.svc.cluster.local` | the fully qualified name |
| `POD-0.SVC.NS.svc.cluster.local` | a StatefulSet pod behind a headless Service |
| `10-244-1-12.NS.pod.cluster.local` | a pod by dashed IP (rarely needed) |
| `_http._tcp.SVC.NS.svc.cluster.local` | SRV record for a named port |

**See it on a real system**

```bash
kubectl -n kube-system get deploy,svc -l k8s-app=kube-dns
kubectl -n kube-system get cm coredns -o jsonpath='{.data.Corefile}'
kubectl -n kube-system logs -l k8s-app=kube-dns --tail=20
kubectl run dns --rm -it --restart=Never --image=nicolaka/netshoot -- sh -c 'cat /etc/resolv.conf; dig +search web.shop; dig +short kubernetes.default.svc.cluster.local'
```

```
search default.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5
...
;; ANSWER SECTION:
web.shop.svc.cluster.local. 30	IN	A	10.96.120.15
```

**Hands-on lab (test VM only)**

**Step 1 — break by removing CoreDNS capacity.** Scale it to zero (lab only: this breaks name
resolution for the whole cluster).

```bash
kubectl -n kube-system scale deploy coredns --replicas=0
kubectl run dns --rm -it --restart=Never --image=nicolaka/netshoot -- dig web.shop.svc.cluster.local
```

```
;; communications error to 10.96.0.10#53: timed out
;; no servers could be reached
```

→ Timeouts to 10.96.0.10 mean no CoreDNS endpoint answered. Same symptom as a NetworkPolicy
blocking port 53 (area 15).

**Step 2 — fix.** `kubectl -n kube-system scale deploy coredns --replicas=2`.

**Step 3 — break the Corefile.** `kubectl -n kube-system edit cm coredns` and introduce a typo
(`forwardd . /etc/resolv.conf`). The running pods' `reload` plugin refuses the broken file and keeps
the old config (they only log an error), which hides the problem until the next restart. Now run
`kubectl -n kube-system rollout restart deploy coredns`: the new pods crash with
`/etc/coredns/Corefile:14 - Error during parsing: Unknown directive 'forwardd'` and the rollout
stalls with one old pod still serving. Fix the typo and restart again.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| CoreDNS down or 0 replicas | `no servers could be reached`, apps report `could not resolve host` | `kubectl -n kube-system get pods -l k8s-app=kube-dns` | [26](26-playbook-containers-k8s.md) |
| Short name across namespaces | `NXDOMAIN` for `web` from namespace `api` | use `web.shop` | this topic |
| Corefile typo | CoreDNS CrashLoopBackOff with a parse error | `kubectl -n kube-system logs -l k8s-app=kube-dns --previous` | — |
| NetworkPolicy blocks 53 | timeouts only in some namespaces | `kubectl get netpol -A` | area 15 |
| Upstream unreachable | cluster names work, internet names fail | CoreDNS logs (`i/o timeout` to upstream) | [DNS](08-dns.md) |

**Why it matters for troubleshooting.** DNS failures look like application failures ("cannot
connect to database"). Test with a debug pod in the *same namespace* as the failing app, by short
name and by FQDN, before reading app logs. The official guide is
[Debugging DNS Resolution](https://kubernetes.io/docs/tasks/administer-cluster/dns-debugging-resolution/).

**Next step.** Why some lookups are slow, and how the node's resolver feeds CoreDNS.

### Search domains, ndots and the node resolver

**Level:** [L3 · Senior] · CKA: Troubleshooting

**Concept.** `options ndots:5` means: a name with fewer than 5 dots is first tried with each search
domain appended. So `api.example.com` (2 dots) from namespace `shop` is tried as
`api.example.com.shop.svc.cluster.local`, then `.svc.cluster.local`, then `.cluster.local`, then
any node search domains, and only then as-is. Each try is an A and an AAAA query: up to 8+ queries
before the right one. A trailing dot (`api.example.com.`) makes the name absolute and skips the
list.

CoreDNS's upstream comes from the node: the kubelet passes a resolv.conf to pods with
`dnsPolicy: Default` and to CoreDNS. On Ubuntu, `/etc/resolv.conf` points at systemd-resolved's
stub 127.0.0.53, which inside a pod would mean "myself". kubeadm detects systemd-resolved and sets
the kubelet's `resolvConf: /run/systemd/resolve/resolv.conf` (the real upstreams from netplan). If
that is wrong, CoreDNS forwards to itself and its `loop` plugin deliberately crashes it.

**Key terms**

| Term | Meaning |
|---|---|
| `ndots` | dot threshold for trying search domains first (Kubernetes default 5) |
| `dnsPolicy: ClusterFirst` | default: use CoreDNS |
| `dnsPolicy: Default` | inherit the node's resolver (CoreDNS itself uses this) |
| `dnsPolicy: ClusterFirstWithHostNet` | CoreDNS for `hostNetwork` pods |
| `dnsPolicy: None` + `dnsConfig` | fully custom resolv.conf |
| kubelet `resolvConf` | the file the kubelet hands to pods using `Default` |

**See it on a real system**

```bash
grep resolvConf /var/lib/kubelet/config.yaml           # on a node
cat /run/systemd/resolve/resolv.conf                   # real upstreams (from netplan)
resolvectl status | sed -n '1,15p'
ip route get POD_IP                                    # on the client pod's node: prints "dev caliXXXX", its veth
sudo tcpdump -ni VETH port 53                          # watch that pod's DNS queries while it resolves a name
```

```
$ sudo tcpdump -ni cali4f3a9b2c1d0 port 53         # the client pod's host-side veth
10:31:02.114201 IP 10.244.1.30.41237 > 10.96.0.10.53: 5121+ A? api.example.com.shop.svc.cluster.local. (56)
10:31:02.114233 IP 10.244.1.30.41237 > 10.96.0.10.53: 6402+ AAAA? api.example.com.shop.svc.cluster.local. (56)
10:31:02.115870 IP 10.96.0.10.53 > 10.244.1.30.41237: 5121 NXDomain*- 0/1/0 (149)
10:31:02.116410 IP 10.244.1.30.50112 > 10.96.0.10.53: 7713+ A? api.example.com.svc.cluster.local. (51)
...
10:31:02.121032 IP 10.244.1.30.39876 > 10.96.0.10.53: 9184+ A? api.example.com. (33)
10:31:02.140557 IP 10.96.0.10.53 > 10.244.1.30.39876: 9184 1/0/0 A 203.0.113.20 (64)
```

→ The search-domain expansion in action: three NXDOMAIN rounds before the real query. That is the
"no view of the packets" blind spot from your Ops Ladder, closed with the same tool.

**Hands-on lab (test VM only)**

**Step 1 — measure.** From a netshoot pod, time `dig +search api.example.com` versus
`dig api.example.com.`.

**Step 2 — fix per workload** with `dnsConfig`:

```yaml
spec:
  dnsConfig:
    options:
    - name: ndots
      value: "2"
```

**Step 3 — break the node resolver (CoreDNS loop).** On the node(s) running CoreDNS, set
`resolvConf: /etc/resolv.conf` in `/var/lib/kubelet/config.yaml` (keep a copy of the file
outside `/var/lib/kubelet` first), `sudo systemctl restart kubelet`, then
`kubectl -n kube-system rollout restart deploy coredns`.

```
[FATAL] plugin/loop: Loop (127.0.0.1:47538 -> :53) detected for zone ".", see https://coredns.io/plugins/loop#troubleshooting. Query: "HINFO 4547991504243258144.3688648895315093531."
```

**Step 4 — fix.** Restore `resolvConf: /run/systemd/resolve/resolv.conf`, restart the kubelet,
restart CoreDNS. Reference: [CoreDNS loop plugin](https://coredns.io/plugins/loop).

**Step 5 — on-prem extra: an internal zone.** Forward your company zone to internal DNS servers
by adding a server block to the Corefile (then restart CoreDNS):

```
internal.example.com:53 {
    errors
    cache 30
    forward . 192.0.2.53 192.0.2.54
}
```

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| CoreDNS loop | CrashLoopBackOff, `plugin/loop: Loop ... detected` | `grep resolvConf /var/lib/kubelet/config.yaml` | [DNS](08-dns.md) |
| ndots amplification | slow external calls, CoreDNS CPU high, conntrack pressure | tcpdump port 53 | [Slow system](23-playbook-slow-system.md) |
| Internal zone unknown upstream | `NXDOMAIN` for `*.internal.example.com` from pods, works on nodes | compare `dig` on node vs pod | [DNS](08-dns.md) |
| hostNetwork pod uses node DNS | cannot resolve Service names | set `dnsPolicy: ClusterFirstWithHostNet` | this topic |

**Why it matters for troubleshooting.** Pod DNS is the node's DNS plus one layer. Your
systemd-resolved and netplan skills decide whether CoreDNS has working upstreams.

**Next step.** Give applications their configuration: ConfigMaps and Secrets (area 10).

---

## 10. ConfigMaps and Secrets

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Application Lifecycle Management: the ConfigMaps and Secrets lessons ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Users, permissions & security](10-users-permissions-security.md) for secret hygiene · 3) Practice: the Config Out of Date and Create Container Errors scenarios in *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)) · 4) Lab below: env vs volume updates and the trailing-newline Secret.

### ConfigMaps: env vs volume

**Level:** [L1 · Junior] · CKA: Workloads & Scheduling

**Concept.** A **ConfigMap** holds non-secret configuration as key/value pairs, outside the image,
so the same image runs in dev and prod. A pod consumes it in two ways that behave very differently
on change: as **environment variables** (read once at container start, never updated) or as a
**volume** (each key becomes a file; the kubelet refreshes files eventually, typically within a
minute or two). A volume mounted with `subPath` is never refreshed.

| Consumption | Updates when the ConfigMap changes? | Missing ConfigMap or key |
|---|---|---|
| `env.valueFrom.configMapKeyRef` | no: restart needed | `CreateContainerConfigError` |
| `envFrom.configMapRef` | no: restart needed | `CreateContainerConfigError` |
| volume (whole ConfigMap) | yes, after a delay (atomic symlink swap) | `ContainerCreating`, `FailedMount` event |
| volume with `subPath` | never | same as volume |

**Key terms**

| Term | Meaning |
|---|---|
| `--from-literal`, `--from-file`, `--from-env-file` | ways to create one |
| `optional: true` | start the pod even if the ConfigMap or key is missing |
| `immutable: true` | cannot be changed; protects against accidents and reduces API load |
| Hash suffix pattern | name the ConfigMap after its content (Kustomize `configMapGenerator`) so a change rolls the pods automatically |

**See it on a real system**

```bash
kubectl -n shop get cm
kubectl -n shop describe cm app-cfg
kubectl -n shop exec deploy/cfgdemo -- env | grep LOG_LEVEL
kubectl -n shop exec deploy/cfgdemo -- ls -la /etc/app/
```

```
$ kubectl -n shop exec deploy/cfgdemo -- ls -la /etc/app/
drwxrwxrwx    3 root root  120 Oct  3 10:40 .
drwxr-xr-x    1 root root 4096 Oct  3 10:40 ..
drwxr-xr-x    2 root root   80 Oct  3 10:40 ..2026_10_03_10_40_12.1638572913
lrwxrwxrwx    1 root root   32 Oct  3 10:40 ..data -> ..2026_10_03_10_40_12.1638572913
lrwxrwxrwx    1 root root   16 Oct  3 10:40 LOG_LEVEL -> ..data/LOG_LEVEL
lrwxrwxrwx    1 root root   15 Oct  3 10:40 app.conf -> ..data/app.conf
```

→ Files are symlinks through `..data`, which the kubelet swaps atomically on update. Apps that
watch the file with inotify must watch the directory, not the file.

**Hands-on lab (test VM only)**

**Step 1 — build.**

```bash
printf 'listen=8080\nfeature_x=off\n' > app.conf
kubectl -n shop create configmap app-cfg --from-literal=LOG_LEVEL=info --from-file=app.conf
cat <<'EOT' > cfgdemo.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cfgdemo
  namespace: shop
spec:
  replicas: 1
  selector:
    matchLabels: {app: cfgdemo}
  template:
    metadata:
      labels: {app: cfgdemo}
    spec:
      containers:
      - name: app
        image: busybox:1.36
        command: ["sh", "-c", "while true; do echo env=$LOG_LEVEL file=$(cat /etc/app/LOG_LEVEL); sleep 10; done"]
        env:
        - name: LOG_LEVEL
          valueFrom:
            configMapKeyRef: {name: app-cfg, key: LOG_LEVEL}
        volumeMounts:
        - name: cfg
          mountPath: /etc/app
      volumes:
      - name: cfg
        configMap:
          name: app-cfg
EOT
kubectl apply -f cfgdemo.yaml
kubectl -n shop logs deploy/cfgdemo -f
```

**Step 2 — change it and watch.** In another terminal:
`kubectl -n shop patch cm app-cfg -p '{"data":{"LOG_LEVEL":"debug"}}'`. Within a minute or two
the log shows `env=info file=debug`: the file changed, the env var did not.

**Step 3 — apply the change properly.** `kubectl -n shop rollout restart deploy/cfgdemo`: new
pods read `debug` in both.

**Step 4 — break.** Change the key reference to `LOG_LEVELL` and apply. The new pod shows
`CreateContainerConfigError`; `describe` says `couldn't find key LOG_LEVELL in ConfigMap shop/app-cfg`.
Fix the key name.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| ConfigMap missing (env) | `CreateContainerConfigError`: `configmap "app-cfg" not found` | `kubectl -n NS get cm` | [26](26-playbook-containers-k8s.md) |
| ConfigMap missing (volume) | `ContainerCreating`; `MountVolume.SetUp failed for volume "cfg" : configmap "app-cfg" not found` | `kubectl describe pod POD` | [26](26-playbook-containers-k8s.md) |
| Changed config not picked up | old behaviour after edit | was it env or subPath? `rollout restart` | this topic |
| Wrong namespace | ConfigMaps are namespaced; a pod cannot reference another namespace's | `kubectl -n NS get cm` | — |

**Why it matters for troubleshooting.** "We changed the config but nothing happened" is answered by
how the pod consumes it. Check the pod spec before suspecting the app.

**Next step.** The same mechanics for sensitive data, with extra care.

### Secrets: types, encoding and encryption

**Level:** [L2 · Mid]; encryption at rest [L3 · Senior] · CKA: Workloads & Scheduling

**Concept.** A **Secret** works like a ConfigMap but is meant for passwords, tokens, keys and
certificates: it is mounted on tmpfs (never written to the node's disk), and RBAC can restrict it
separately. Values are **base64-encoded, not encrypted**. Anyone who can `get` secrets in a
namespace, or create pods there (and mount them), can read them. By default they are stored in
plain text in etcd unless the API server is configured with **encryption at rest**.

**Key terms**

| Type | Use | Created with |
|---|---|---|
| `Opaque` | generic key/values | `kubectl create secret generic` |
| `kubernetes.io/tls` | `tls.crt` + `tls.key` for Ingress/Gateway | `kubectl create secret tls` |
| `kubernetes.io/dockerconfigjson` | registry credentials (imagePullSecrets) | `kubectl create secret docker-registry` |
| `kubernetes.io/service-account-token` | legacy long-lived SA tokens (avoid; use `kubectl create token`) | — |
| `stringData` | write plain values in YAML; the API encodes them | manifest field |
| EncryptionConfiguration | API server config that encrypts Secrets in etcd (aescbc, aesgcm, secretbox, KMS v2) | `--encryption-provider-config` |

**See it on a real system**

```bash
kubectl -n shop get secrets
kubectl -n shop get secret db -o jsonpath='{.data.password}' | base64 -d; echo
kubectl -n shop get secret db -o jsonpath='{.data.password}' | base64 -d | od -c | tail -2   # spot hidden newlines
```

**Hands-on lab (test VM only)**

**Step 1 — build.** Quote values in single quotes so the shell does not interpret `!` or `$`.

```bash
kubectl -n shop create secret generic db --from-literal=username=app --from-literal=password='S3cr3t!pw'
kubectl -n shop run sec --image=busybox:1.36 --restart=Never --overrides='{"spec":{"containers":[{"name":"sec","image":"busybox:1.36","command":["sh","-c","echo -n $DB_PASS | wc -c; sleep 3600"],"env":[{"name":"DB_PASS","valueFrom":{"secretKeyRef":{"name":"db","key":"password"}}}]}]}}'
kubectl -n shop logs sec                      # 9 characters
```

**Step 2 — break (the newline bug).** Create the same secret from YAML using `echo` without `-n`:

```bash
echo 'S3cr3t!pw' | base64                      # UzNjcjN0IXB3Cg==  <- the trailing "Cg==" is an encoded newline
```

Put that value in a manifest's `data.password`, re-create the secret and the pod: the length is now
10 and a real database would answer `password authentication failed`. Fix: `printf '%s' 'S3cr3t!pw' | base64`,
or use `stringData` and let the API encode it.

**Step 3 — see why encryption at rest matters** (on cp1; `etcdctl` flags explained in area 19):

```bash
sudo ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key \
  get /registry/secrets/shop/db | strings | grep -A1 password
```

→ Without an EncryptionConfiguration the password is readable in etcd and in every etcd backup.
Protect backups accordingly, or configure encryption at rest (see the
[Kubernetes docs](https://kubernetes.io/docs/) task "Encrypting Confidential Data at Rest").

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Trailing newline in value | auth failures with the "right" password | decode the value and inspect it with `od -c` (see above) | this topic |
| Secret in wrong namespace | `secret "db" not found` | `kubectl -n NS get secret` | [26](26-playbook-containers-k8s.md) |
| Key name mismatch | `couldn't find key password in Secret shop/db` | `kubectl describe secret NAME` (shows keys, not values) | — |
| Secret committed to Git | credential leak | rotate the credential; use sealed or external secrets | [Security](10-users-permissions-security.md) |

**Why it matters for troubleshooting.** Many "the app cannot log in to the database" incidents are
Secret encoding or reference problems. Decode and count characters before resetting passwords.

**Next step.** Data that must outlive pods: storage (area 11).

---

## 11. Storage

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Storage ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Storage & disks](01-storage-disk.md) for NFS exports, permissions and full disks · 3) Practice: the Multi-Attach Volume Errors scenario in *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)) · 4) Lab below: a static PV, the Released trap, then local-path provisioning.

### Volumes inside a pod

**Level:** [L2 · Mid] · CKA: Storage

**Concept.** A container's filesystem is thrown away when the container restarts. **Volumes**
are mounted into containers and live at least as long as the pod. Some are ephemeral (`emptyDir`,
`configMap`, `secret`, `projected`); some point at node or network storage (`hostPath`, `nfs`,
`csi`); and `persistentVolumeClaim` points at storage managed independently of the pod (next topic).

**Key terms**

| Volume | Lifetime | Typical use | Watch out |
|---|---|---|---|
| `emptyDir` | pod | scratch space, sharing files between containers | `medium: Memory` counts against the memory limit |
| `hostPath` | node | node agents (log collectors, CNI) | ties the pod to one node; security risk; avoid for apps |
| `configMap` / `secret` / `projected` | pod (content from API) | config, tokens, certs | read-only |
| `persistentVolumeClaim` | independent of the pod | databases, uploads | access modes, node affinity |
| `nfs` / `csi` | external | shared or managed storage | network and permission problems |

**See it on a real system**

```bash
kubectl -n shop get pod POD -o yaml | sed -n '/^  volumes:/,/^status:/p'
kubectl -n shop describe pod POD | sed -n '/Volumes:/,/QoS/p'
sudo ls /var/lib/kubelet/pods/POD_UID/volumes/      # on the node: where volumes are mounted
```

**Hands-on lab (test VM only)**

**Step 1 — build** a pod with a `hostPath` volume of type `Directory`, pinned to w1:

```bash
cat <<'EOT' > hostpath.yaml
apiVersion: v1
kind: Pod
metadata:
  name: hp
  namespace: shop
spec:
  nodeName: w1
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "date >> /data/log.txt; sleep 3600"]
    volumeMounts:
    - name: data
      mountPath: /data
  volumes:
  - name: data
    hostPath:
      path: /srv/hp-demo
      type: Directory
EOT
kubectl apply -f hostpath.yaml
```

**Step 2 — observe the break.** `/srv/hp-demo` does not exist on w1: the pod stays
`ContainerCreating` and `describe` shows
`MountVolume.SetUp failed for volume "data" : hostPath type check failed: /srv/hp-demo is not a directory`.

**Step 3 — fix.** Create the directory on w1 (`sudo mkdir -p /srv/hp-demo`), or use
`type: DirectoryOrCreate`. Then `cat /srv/hp-demo/log.txt` on w1: the data lives on that node only,
which is exactly why apps should use PVCs.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| hostPath missing | `hostPath type check failed` | `kubectl describe pod POD` | this topic |
| Permission denied writing a volume | app log `Permission denied`; container runs as non-root | `kubectl exec POD -- id` and `ls -ln` on the mount; set `securityContext.fsGroup` | [Permissions](10-users-permissions-security.md) |
| Memory-backed emptyDir fills | OOMKilled although the app uses little RAM | `kubectl describe pod POD` | area 12 |
| Node disk full | evictions with `ephemeral-storage` reasons | `df -h /var/lib/kubelet` | [Storage](01-storage-disk.md) |

**Why it matters for troubleshooting.** Stuck `ContainerCreating` is very often a volume problem,
and the `describe` events say which volume and why.

**Next step.** Storage that survives pods and nodes: PVs and PVCs.

### PersistentVolumes, claims, access modes and reclaim

**Level:** [L2 · Mid] · CKA: Storage

**Concept.** A **PersistentVolume (PV)** is a piece of storage in the cluster (an NFS export, a
disk, a cloud volume), created by an admin or provisioned dynamically. A
**PersistentVolumeClaim (PVC)** is an app's request: "10 GiB, ReadWriteOnce, class X". The control
plane **binds** each PVC to one matching PV; pods mount the PVC by name. The split lets app
manifests stay the same across environments.

```
 Pod --(volumes.persistentVolumeClaim.claimName: data)--> PVC data (10Gi, RWO, class "")
                                                           | bound (1:1)
                                                           v
                                                         PV pv-nfs-01 (10Gi, RWO+RWX, nfs 192.168.56.20:/exports/a)
```

A PVC binds to a PV only if: storage class names are equal (an unset class on the PVC means
"the default class", while `storageClassName: ""` means "no class, static PVs only"), the PV
capacity is at least the request, the PV offers all requested access modes, and any label selector
and `volumeMode` match.

**Key terms**

| Term | Meaning |
|---|---|
| RWO (ReadWriteOnce) | read-write by pods on **one node** (several pods on that node may share it) |
| ROX (ReadOnlyMany) | read-only from many nodes |
| RWX (ReadWriteMany) | read-write from many nodes (NFS, CephFS; not block disks) |
| RWOP (ReadWriteOncePod) | read-write by exactly one pod |
| Reclaim `Retain` | after the PVC is deleted, the PV becomes `Released` and keeps the data; an admin cleans up |
| Reclaim `Delete` | deleting the PVC deletes the PV and the backing storage (dynamic default) |
| PV phases | `Available`, `Bound`, `Released`, `Failed` |
| `kubernetes.io/pvc-protection` | finalizer: a PVC in use by a pod stays `Terminating` until the pod is gone |

**See it on a real system**

```bash
kubectl get pv
kubectl -n shop get pvc
kubectl -n shop describe pvc data | sed -n '/Events:/,$p'
```

```
$ kubectl get pv
NAME      CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS     CLAIM       STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE
pv-demo   1Gi        RWO            Retain           Bound      shop/data                  <unset>                          5m
pv-old    5Gi        RWX            Retain           Released   shop/old                   <unset>                          9d
```

→ `pv-old` is Released: its claim was deleted, the data is still there, and it will not bind to a
new claim until an admin clears its `claimRef`.

**Hands-on lab (test VM only)**

**Step 1 — build** a static PV (hostPath on w1 for the lab; NFS in real life) and a claim that
binds to it.

```bash
cat <<'EOT' > pv.yaml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-demo
spec:
  capacity: {storage: 1Gi}
  accessModes: ["ReadWriteOnce"]
  persistentVolumeReclaimPolicy: Retain
  storageClassName: ""
  hostPath: {path: /srv/pv-demo, type: DirectoryOrCreate}
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - {key: kubernetes.io/hostname, operator: In, values: ["w1"]}
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data
  namespace: shop
spec:
  storageClassName: ""
  accessModes: ["ReadWriteOnce"]
  resources:
    requests: {storage: 2Gi}
EOT
kubectl apply -f pv.yaml
kubectl -n shop get pvc data
```

**Step 2 — observe the break.** The claim asks 2Gi and the PV offers 1Gi: the PVC stays `Pending`
and `describe` shows `no persistent volumes available for this claim and no storage class is set`.

**Step 3 — fix.** Claims cannot be shrunk once created, so recreate the claim with
`storage: 1Gi`. Before deleting anything, confirm nothing uses it:
`kubectl -n shop get pods -o jsonpath='{range .items[*]}{.metadata.name}{" "}{.spec.volumes[*].persistentVolumeClaim.claimName}{"\n"}{end}'`.

> Warning: deleting a PVC can delete its data when the PV's reclaim policy is `Delete`. Check
> `kubectl get pv` (RECLAIM POLICY column) first. This lab PV is `Retain` and still unbound.

```bash
kubectl -n shop delete pvc data
sed -i 's/storage: 2Gi/storage: 1Gi/' pv.yaml && kubectl apply -f pv.yaml
kubectl -n shop get pvc data                     # Bound
```

**Step 4 — the Released trap.** Delete the claim again: the PV becomes `Released`, and a new claim
stays Pending. After checking the data on w1, make the PV available again:
`kubectl patch pv pv-demo --type=json -p='[{"op":"remove","path":"/spec/claimRef"}]'`.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| No matching PV | PVC `Pending`: `no persistent volumes available for this claim and no storage class is set` | `kubectl get pv` vs PVC request | [26](26-playbook-containers-k8s.md) |
| Class mismatch (unset vs `""`) | PVC binds to a dynamic volume instead of your static PV, or never binds | `kubectl get pvc NAME -o jsonpath='{.spec.storageClassName}'` | this topic |
| RWO volume, pods on two nodes | second pod `ContainerCreating`: `Multi-Attach error for volume ... Volume is already used by pod(s)` | `kubectl get pods -o wide` | — |
| Released PV | new PVC Pending although a PV of the right size exists | `kubectl get pv` (STATUS Released) | this topic |
| PVC stuck Terminating | finalizer `kubernetes.io/pvc-protection` | `kubectl get pods` using it | — |
| NFS permissions | `Permission denied` or `mount.nfs: access denied by server` | NFS export options and UID mapping | [Storage](01-storage-disk.md) |

**Why it matters for troubleshooting.** A Pending PVC holds its pod in Pending, and the pod's
event only says `pod has unbound immediate PersistentVolumeClaims`. Always follow the chain pod →
PVC → PV → storage backend.

**Next step.** Stop creating PVs by hand: StorageClasses.

### StorageClasses and dynamic provisioning

**Level:** [L3 · Senior] · CKA: Storage

**Concept.** A **StorageClass** names a **provisioner** (a CSI driver or controller) plus
parameters. When a PVC references a class, the provisioner creates a matching PV on demand. One
class can be marked default, and PVCs without a class use it. `volumeBindingMode:
WaitForFirstConsumer` delays provisioning until a pod using the PVC is scheduled, so the volume is
created on (or reachable from) the right node.

**Key terms**

| Field | Meaning |
|---|---|
| `provisioner` | e.g. `rancher.io/local-path`, `nfs.csi.k8s.io`, `ebs.csi.aws.com` |
| `reclaimPolicy` | `Delete` (default) or `Retain` for provisioned PVs |
| `volumeBindingMode` | `Immediate` or `WaitForFirstConsumer` |
| `allowVolumeExpansion` | lets you grow a PVC by editing its request |
| default class | annotation `storageclass.kubernetes.io/is-default-class: "true"` |

| Homelab / on-prem option | Access modes | Notes |
|---|---|---|
| local-path-provisioner | RWO | node-local directories; simplest; data dies with the node |
| NFS CSI driver (csi-driver-nfs) | RWO, RWX | uses an existing NFS server; good fit for on-prem |
| Longhorn / Rook-Ceph | RWO (RWX via extra components) | replicated block storage; more moving parts |
| AWS EBS CSI (EKS) | RWO | zone-bound; see [AWS](16-aws-cloud.md) |

**See it on a real system**

```bash
kubectl get storageclass
kubectl get csidrivers
kubectl -n shop get pvc -o custom-columns=NAME:.metadata.name,STATUS:.status.phase,CLASS:.spec.storageClassName,VOLUME:.spec.volumeName
```

```
$ kubectl get storageclass
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  3d
```

**Hands-on lab (test VM only)**

**Step 1 — install a provisioner.** Apply local-path-provisioner using the manifest URL from the
project's README (`kubectl apply -f LOCAL_PATH_PROVISIONER_MANIFEST_URL`), then make it the default:

```bash
kubectl patch storageclass local-path -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
```

**Step 2 — claim dynamically.**

```bash
kubectl -n shop create -f - <<'EOT'
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: dyn
spec:
  accessModes: ["ReadWriteOnce"]
  resources:
    requests: {storage: 1Gi}
EOT
kubectl -n shop describe pvc dyn | tail -3
```

→ `Pending` with `waiting for first consumer to be created before binding` is **normal** for
`WaitForFirstConsumer`. Start a pod that mounts `dyn` and it binds.

**Step 3 — break the provisioner.** Scale it to zero
(`kubectl -n local-path-storage scale deploy local-path-provisioner --replicas=0`), create another
PVC and a pod using it. The PVC stays Pending with
`waiting for a volume to be created either by the external provisioner 'rancher.io/local-path' or manually by the system administrator`.
Scale it back to 1 and the volume appears.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| No default class, PVC without class | Pending: `no persistent volumes available for this claim and no storage class is set` | `kubectl get storageclass` | [26](26-playbook-containers-k8s.md) |
| Provisioner down | `waiting for a volume to be created ... by the external provisioner` | provisioner pod logs | this topic |
| Two default classes | unpredictable class choice | `kubectl get sc` (two "(default)") | — |
| Expansion not allowed | `only dynamically provisioned pvc can be resized and the storageclass that provisions the pvc must support resize` | `kubectl get sc NAME -o yaml` | — |
| Zone mismatch (cloud) | pod Pending: `volume node affinity conflict` | `kubectl get pv NAME -o yaml` (nodeAffinity) | [AWS](16-aws-cloud.md) |

**Why it matters for troubleshooting.** With dynamic provisioning there is one more component that
can fail silently: the provisioner. A Pending PVC event always names who it is waiting for.

**Next step.** Where pods land, and why they sometimes cannot land anywhere: scheduling (area 12).

---

## 12. Scheduling

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Scheduling ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Memory](04-memory.md) and [CPU & performance](03-cpu-performance.md) for cgroup limits, OOM kills and throttling · 3) Practice: the Pending Pods scenario in *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)) · 4) Lab below: read every FailedScheduling message aloud before you fix it.

### Requests, limits and QoS classes

**Level:** [L2 · Mid] · CKA: Workloads & Scheduling

**Concept.** **Requests** are what the scheduler reserves: a pod fits on a node only if the sum of
requests of all pods there, plus this one, stays within the node's *allocatable* capacity. Actual
usage does not matter to the scheduler. **Limits** are enforced at runtime by cgroups: exceeding
the CPU limit means **throttling** (slower, not killed); exceeding the memory limit means
**OOMKill** (exit 137). From requests and limits Kubernetes derives a **QoS class**, which decides
who is evicted first when a node runs out of memory or disk.

| QoS class | Rule | Eviction order under pressure |
|---|---|---|
| Guaranteed | every container has CPU and memory limits, and requests equal limits | last |
| Burstable | at least one request or limit set, not Guaranteed | middle (those far above requests first) |
| BestEffort | no requests or limits at all | first |

**Key terms**

| Term | Meaning |
|---|---|
| `100m` CPU | 0.1 of a core (millicores) |
| `256Mi` | mebibytes (use `Mi`/`Gi`; `M` is decimal megabytes) |
| allocatable | node capacity minus system and kubelet reservations |
| CPU throttling | CFS quota exhausted in a period; visible in the container's `cpu.stat` |
| eviction thresholds | kubelet defaults such as `memory.available<100Mi`, `nodefs.available<10%` |

**See it on a real system**

```bash
kubectl describe node w1 | sed -n '/Allocatable:/,/System Info:/p'
kubectl describe node w1 | grep -A10 'Allocated resources'
kubectl -n shop get pod POD -o jsonpath='{.status.qosClass}{"\n"}'
kubectl -n shop exec POD -- cat /sys/fs/cgroup/cpu.stat        # nr_throttled, throttled_usec (cgroup v2)
```

```
Allocated resources:
  (Total limits may be over 100 percent, i.e., overcommitted.)
  Resource           Requests     Limits
  --------           --------     ------
  cpu                1850m (92%)  3 (150%)
  memory             1210Mi (68%) 2560Mi (144%)
```

→ 92% of CPU is *requested* on this node, so a new pod requesting 250m will not fit, even if
`kubectl top node` shows the CPU mostly idle.

**Hands-on lab (test VM only)**

**Step 1 — break.** Request more CPU than any node has.

```bash
kubectl -n shop create deployment big --image=nginx:1.27
kubectl -n shop set resources deploy big --requests=cpu=10,memory=64Mi
kubectl -n shop get pods -l app=big
kubectl -n shop describe pod -l app=big | grep -A3 Events
```

```
Warning  FailedScheduling  5s  default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: }, 2 Insufficient cpu. preemption: 0/3 nodes are available: 1 Preemption is not helpful for scheduling, 2 No preemption victims found for incoming pod.
```

**Step 2 — read the message.** It counts every node and gives each one's reason: the control
plane is tainted, the two workers lack CPU.

**Step 3 — fix.** `kubectl -n shop set resources deploy big --requests=cpu=100m,memory=64Mi --limits=memory=128Mi`.
Check the QoS class of the new pod (Burstable). Make it Guaranteed by setting CPU and memory limits
equal to the requests.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Requests too big | `Insufficient cpu` / `Insufficient memory` | `kubectl describe node NODE` (Allocated resources) | [26](26-playbook-containers-k8s.md) |
| Memory limit too low | OOMKilled, exit 137 | `kubectl describe pod POD` | [Memory](04-memory.md) |
| CPU limit too low | high latency, idle node, `nr_throttled` climbing | `cpu.stat` in the container | [Slow system](23-playbook-slow-system.md) |
| Node memory pressure | pods `Evicted`: `The node was low on resource: memory` | `kubectl describe node NODE` (Conditions) | [Memory](04-memory.md) |
| No requests at all | BestEffort pods evicted first; HPA cannot work | `kubectl get pod POD -o jsonpath='{.status.qosClass}'` | — |

**Why it matters for troubleshooting.** Scheduling and eviction decisions are made on requests,
while performance is limited by limits. Most "Pending" and many "slow" incidents are a mismatch
between the two and reality.

**Next step.** Keeping pods off nodes: taints and tolerations.

### Taints and tolerations

**Level:** [L2 · Mid] · CKA: Workloads & Scheduling

**Concept.** A **taint** on a node repels pods; a **toleration** on a pod lets it ignore a matching
taint. Tolerations allow, they do not attract: to *force* pods onto dedicated nodes you need taints
plus node affinity. Effects: `NoSchedule` (new pods kept away), `PreferNoSchedule` (soft),
`NoExecute` (also evicts running pods that do not tolerate it, optionally after
`tolerationSeconds`).

**Key terms**

| Taint | Who sets it |
|---|---|
| `node-role.kubernetes.io/control-plane:NoSchedule` | kubeadm, on control-plane nodes |
| `node.kubernetes.io/unschedulable:NoSchedule` | `kubectl cordon` |
| `node.kubernetes.io/not-ready:NoExecute`, `unreachable:NoExecute` | node lifecycle controller; pods tolerate them for 300 s by default |
| `node.kubernetes.io/disk-pressure`, `memory-pressure` | kubelet under pressure |

**See it on a real system**

```bash
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
kubectl describe node cp1 | grep -A2 Taints
kubectl -n shop get pod POD -o jsonpath='{.spec.tolerations}{"\n"}'
```

**Hands-on lab (test VM only)**

**Step 1 — taint a node** and watch where pods go.

```bash
kubectl taint nodes w2 dedicated=db:NoSchedule
kubectl -n shop create deployment spread --image=nginx:1.27 --replicas=4
kubectl -n shop get pods -l app=spread -o wide            # all on w1
```

**Step 2 — tolerate it.** Add to the pod template (`kubectl -n shop edit deploy spread`):

```yaml
      tolerations:
      - key: dedicated
        operator: Equal
        value: db
        effect: NoSchedule
```

New pods *may* land on w2; they are not forced to.

**Step 3 — NoExecute.** `kubectl taint nodes w1 maintenance=true:NoExecute`: pods without a
matching toleration are evicted from w1 immediately. Remove both taints (trailing minus):

```bash
kubectl taint nodes w1 maintenance=true:NoExecute-
kubectl taint nodes w2 dedicated=db:NoSchedule-
```

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Untolerated taint | `node(s) had untolerated taint {dedicated: db}` | `kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints` | [26](26-playbook-containers-k8s.md) |
| DaemonSet missing from tainted nodes | DESIRED lower than node count | add tolerations to the DaemonSet | area 13 |
| Forgotten cordon | node `Ready,SchedulingDisabled`, new pods avoid it | `kubectl get nodes` | area 19 |
| Toleration without affinity | "dedicated" nodes also run random pods | add node affinity | next topic |

**Why it matters for troubleshooting.** The FailedScheduling message lists taints by key; one
`kubectl get nodes` with the taints column confirms it.

**Next step.** Attracting pods to nodes and to (or away from) each other.

### nodeSelector, node affinity and pod affinity

**Level:** [L3 · Senior] · CKA: Workloads & Scheduling

**Concept.** **nodeSelector** is the simplest rule: run only on nodes with these labels.
**Node affinity** is the expressive version (operators `In`, `NotIn`, `Exists`, `DoesNotExist`,
`Gt`, `Lt`; `required...` hard rules and `preferred...` weighted soft rules). **Pod affinity /
anti-affinity** places pods relative to *other pods*, per topology domain (`topologyKey`, e.g.
`kubernetes.io/hostname` for "same/different node"). "IgnoredDuringExecution" means rules are only
checked at scheduling time. `spec.nodeName` skips the scheduler entirely (and with it, all
these checks).

**Key terms**

| Field | Example use |
|---|---|
| `nodeSelector: {disk: ssd}` | databases on SSD nodes |
| `requiredDuringSchedulingIgnoredDuringExecution` | hard rule; Pending if unsatisfiable |
| `preferredDuringSchedulingIgnoredDuringExecution` | soft rule with weight 1–100 |
| `podAntiAffinity` + `topologyKey: kubernetes.io/hostname` | one replica per node |
| `podAffinity` | cache next to app |

**See it on a real system**

```bash
kubectl get nodes --show-labels
kubectl get nodes -L disk,topology.kubernetes.io/zone
kubectl -n shop get deploy NAME -o jsonpath='{.spec.template.spec.affinity}{"\n"}'
```

**Hands-on lab (test VM only)**

**Step 1 — required node affinity.**

```bash
kubectl label node w1 disk=ssd
cat <<'EOT' > affinity.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: aff
  namespace: shop
spec:
  replicas: 3
  selector:
    matchLabels: {app: aff}
  template:
    metadata:
      labels: {app: aff}
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchLabels: {app: aff}
            topologyKey: kubernetes.io/hostname
      containers:
      - name: web
        image: nginx:1.27
EOT
kubectl apply -f affinity.yaml
kubectl -n shop get pods -l app=aff -o wide
```

**Step 2 — observe the break.** Three replicas, "one per node", but only two schedulable nodes
(cp1 is tainted): the third pod is Pending with
`0/3 nodes are available: 1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: }, 2 node(s) didn't match pod anti-affinity rules`.

**Step 3 — fix by intent.** If "spread when possible" is what you meant, change `required...` to
`preferred...` (with `weight: 100` and the term under `podAffinityTerm`), or use topology spread
(next topic). Then try a node affinity for `disk In [nvme]`: Pending with
`didn't match Pod's node affinity/selector` until a node has that label.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Label missing or typo | `didn't match Pod's node affinity/selector` | `kubectl get nodes --show-labels` | [26](26-playbook-containers-k8s.md) |
| Hard anti-affinity with too few nodes | `didn't match pod anti-affinity rules` | count nodes vs replicas | this topic |
| `nodeName` to a full/non-existent node | pod fails (`OutOfcpu`, `NodeAffinity`) or stays Pending without scheduler events | `kubectl get pod POD -o yaml` | — |
| Labels changed after scheduling | pods keep running on "wrong" nodes | expected: rules are ignored during execution | — |

**Why it matters for troubleshooting.** Affinity rules are invisible in `kubectl get`, so a pod
that will not schedule "for no reason" needs a look at `spec.affinity` and node labels.

**Next step.** Even spreading, namespace budgets and priorities.

### Topology spread, quotas, LimitRange and priority

**Level:** [L3 · Senior] · CKA: Workloads & Scheduling

**Concept.** **Topology spread constraints** spread replicas evenly across nodes or zones
(`maxSkew`: the allowed difference between the fullest and emptiest domain). **ResourceQuota**
caps what a namespace may consume (pods, CPU and memory requests/limits, PVCs, Services). When a
quota covers CPU or memory, every new pod must declare those values, which is what **LimitRange**
defaults are for. **PriorityClass** lets important pods preempt (evict) less important ones when
the cluster is full.

**Key terms**

| Object | Example |
|---|---|
| `topologySpreadConstraints` | `maxSkew: 1`, `topologyKey: kubernetes.io/hostname`, `whenUnsatisfiable: DoNotSchedule` or `ScheduleAnyway` |
| ResourceQuota | `pods: "10"`, `requests.cpu: "4"`, `limits.memory: 8Gi` per namespace |
| LimitRange | default requests/limits and min/max per container |
| PriorityClass | `value: 1000000`; pods reference it with `priorityClassName` |

**See it on a real system**

```bash
kubectl -n shop describe quota
kubectl -n shop describe limitrange
kubectl get priorityclass
```

```
$ kubectl -n shop describe quota
Name:       shop-quota
Namespace:  shop
Resource    Used  Hard
--------    ----  ----
pods        2     2
```

**Hands-on lab (test VM only)**

**Step 1 — break with a quota.**

```bash
kubectl -n shop create quota shop-quota --hard=pods=2
kubectl -n shop create deployment q --image=nginx:1.27 --replicas=4
kubectl -n shop get deploy q                       # READY stays below 4
kubectl -n shop describe rs -l app=q | grep -A3 Events
```

```
Warning  FailedCreate  4s  replicaset-controller  Error creating: pods "q-6d9f8b7c5-xk2lp" is forbidden: exceeded quota: shop-quota, requested: pods=1, used: pods=2, limited: pods=2
```

→ The error is on the **ReplicaSet**, not on any pod, because the pods were never created.

**Step 2 — break with a compute quota.** Replace the pod-count quota with a CPU/memory quota; new
pods without resources are now rejected (`must specify limits.memory ...`).

```bash
kubectl -n shop delete quota shop-quota            # lab quota from Step 1
kubectl -n shop create quota shop-quota --hard=requests.cpu=2,limits.memory=2Gi
kubectl -n shop rollout restart deploy q
kubectl -n shop describe rs -l app=q | grep -A3 Events
```

Fix with a LimitRange that supplies defaults:

```bash
cat <<'EOT' | kubectl apply -f -
apiVersion: v1
kind: LimitRange
metadata:
  name: defaults
  namespace: shop
spec:
  limits:
  - type: Container
    defaultRequest: {cpu: 100m, memory: 64Mi}
    default: {memory: 128Mi}
EOT
```

**Step 3 — clean up the quota** when done (`kubectl -n shop get quota` first, then
`kubectl -n shop delete quota shop-quota`): later labs assume no quota.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Quota exhausted | Deployment short of replicas; RS event `exceeded quota` | `kubectl describe quota -n NS` | [26](26-playbook-containers-k8s.md) |
| Compute quota without defaults | `failed quota: ... must specify limits.cpu ...` | `kubectl describe limitrange -n NS` | this topic |
| Spread unsatisfiable | `didn't match pod topology spread constraints` | check `maxSkew` and node count | — |
| Preemption surprise | low-priority pods disappear when a high-priority pod arrives | `kubectl get events` (`Preempted`) | — |

**Why it matters for troubleshooting.** Quota and LimitRange failures never reach the pod level.
When a Deployment has fewer pods than desired and the pods themselves look fine, run
`kubectl describe rs`.

**Next step.** Workloads other than Deployments (area 13).

---

## 13. Workload types

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Scheduling ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)); for Jobs, CronJobs and StatefulSets add the POD Design and State Persistence modules of *Certified Kubernetes Application Developer (CKAD)* ([course](https://kodekloud.com/courses/certified-kubernetes-application-developer-ckad)), only those modules for now (the full CKAD comes after CKA) · 2) Note: the Swarm topics in [Docker](30-learn-docker.md) (global vs replicated services) · 3) Practice: the Kubernetes tasks in [100 Days of DevOps](https://kodekloud.com/100-days-of-devops) · 4) Lab below: StatefulSet identity and the OrderedReady block.

| Workload | Pods are | Use it for | Docker/Dokploy analogy |
|---|---|---|---|
| Deployment | interchangeable, random names | stateless web apps, APIs | Swarm replicated service |
| StatefulSet | ordered, stable names and own volumes | databases, queues, clustered apps | a set of named containers with their own volumes |
| DaemonSet | one per (matching) node | node agents: CNI, kube-proxy, log shippers, node_exporter | Swarm global service |
| Job | run to completion | migrations, batch tasks | `docker run --rm` one-shot |
| CronJob | Jobs on a schedule | backups, reports | cron + `docker run` |

### StatefulSet

**Level:** [L3 · Senior] · CKA: Workloads & Scheduling, Storage

**Concept.** A **StatefulSet** gives each replica a stable identity: a fixed name (`db-0`,
`db-1`...), a stable DNS name through a **headless Service**
(`db-0.db.shop.svc.cluster.local`), and its own PVC created from `volumeClaimTemplates`
(`data-db-0`). With the default `podManagementPolicy: OrderedReady`, pods are created one at a time
in order (db-1 starts only after db-0 is Ready) and removed in reverse. Rolling updates also go
in reverse ordinal order. When pods are deleted or the set is scaled down, their PVCs are kept by
default, so data survives.

**Key terms**

| Field | Meaning |
|---|---|
| `serviceName` | the headless Service that provides per-pod DNS (you must create it) |
| `volumeClaimTemplates` | PVC template; one PVC per pod, named `TEMPLATE-STS-ORDINAL` |
| `podManagementPolicy` | `OrderedReady` (default) or `Parallel` |
| `updateStrategy.rollingUpdate.partition` | only pods with ordinal >= partition are updated (canary) |
| `persistentVolumeClaimRetentionPolicy` | whether PVCs are deleted on scale-down or StatefulSet deletion (default: Retain) |

**See it on a real system**

```bash
kubectl -n shop get sts,pods,pvc -l app=db
kubectl -n shop describe sts db | sed -n '/Events:/,$p'
```

```
NAME                  READY   AGE
statefulset.apps/db   2/3     4m

NAME       READY   STATUS    RESTARTS   AGE
pod/db-0   1/1     Running   0          4m
pod/db-1   1/1     Running   0          3m
pod/db-2   0/1     Pending   0          3m

NAME                              STATUS    VOLUME                                     CAPACITY   ACCESS MODES   STORAGECLASS   VOLUMEATTRIBUTESCLASS   AGE
persistentvolumeclaim/data-db-0   Bound     pvc-1f0c9a7e-3b1d-4c2e-9f8a-6d5e4c3b2a10   1Gi        RWO            local-path     <unset>                 4m
persistentvolumeclaim/data-db-1   Bound     pvc-7a6b5c4d-2e1f-4a3b-8c9d-0e1f2a3b4c5d   1Gi        RWO            local-path     <unset>                 3m
persistentvolumeclaim/data-db-2   Pending                                                                        local-path     <unset>                 3m
```

**Hands-on lab (test VM only)** (requires the local-path StorageClass from area 11)

**Step 1 — build.**

```bash
cat <<'EOT' > sts.yaml
apiVersion: v1
kind: Service
metadata:
  name: db
  namespace: shop
spec:
  clusterIP: None
  selector: {app: db}
  ports:
  - port: 80
---
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: db
  namespace: shop
spec:
  serviceName: db
  replicas: 3
  selector:
    matchLabels: {app: db}
  template:
    metadata:
      labels: {app: db}
    spec:
      containers:
      - name: web
        image: nginx:1.27
        volumeMounts:
        - name: data
          mountPath: /usr/share/nginx/html
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes: ["ReadWriteOnce"]
      storageClassName: local-path
      resources:
        requests: {storage: 1Gi}
EOT
kubectl apply -f sts.yaml
kubectl -n shop get pods -l app=db -w
for i in 0 1 2; do kubectl -n shop exec db-$i -- sh -c "echo I am db-$i > /usr/share/nginx/html/index.html"; done
kubectl run c --rm -it --restart=Never -n shop --image=nicolaka/netshoot -- curl -s http://db-1.db
```

**Step 2 — prove the identity.** Remove `db-1` (it is recreated with the same name, on the same
volume) and query it again: still `I am db-1`.

> Warning: deleting a StatefulSet pod is safe here because the controller recreates it with the
> same PVC. Never delete the PVCs of a StatefulSet unless you intend to destroy that replica's data.

```bash
kubectl -n shop delete pod db-1
kubectl -n shop get pod db-1 -w
```

**Step 3 — break the ordering.** Change `storageClassName` in the template to `nope` on a fresh
StatefulSet named `db2`. `db2-0` waits Pending on its PVC, and `db2-1` and `db2-2` are never even
created: with OrderedReady, one stuck pod blocks the rest. Fix the class name (`volumeClaimTemplates`
cannot be changed on an existing StatefulSet, so recreate `db2`, then remove the stuck PVC
`data-db2-0`).

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| PVC cannot bind | `db-0` Pending; later ordinals missing | `kubectl get pvc -l app=db` | area 11 |
| Headless Service missing | `db-0.db` does not resolve | `kubectl get svc db -o jsonpath='{.spec.clusterIP}'` (must be `None`) | area 9 |
| One pod not Ready | rollout stalls; later pods not updated | `kubectl rollout status sts/NAME` | [26](26-playbook-containers-k8s.md) |
| Node lost with RWO volume | pod stays `Terminating`/Unknown and is not recreated elsewhere (by design, to avoid two writers) | `kubectl get nodes`; recover the node first | area 18 |

**Why it matters for troubleshooting.** StatefulSets trade availability for safety: they block
rather than risk two pods on one identity. When they block, find the *lowest* ordinal that is not
Ready.

**Next step.** One pod per node: DaemonSets.

### DaemonSet

**Level:** [L2 · Mid] · CKA: Workloads & Scheduling

**Concept.** A **DaemonSet** runs one copy of a pod on every node that matches its selectors and
tolerations, and adds one automatically when a node joins. kube-proxy and your CNI are DaemonSets;
so are log shippers and node_exporter. Control-plane nodes are skipped unless the DaemonSet
tolerates their taint.

**Key terms**

| Column in `kubectl get ds` | Meaning |
|---|---|
| DESIRED | nodes that should run a pod |
| CURRENT / READY | pods existing / Ready |
| UP-TO-DATE | pods on the current template |
| NODE SELECTOR | restricts which nodes count |

**See it on a real system**

```bash
kubectl get ds -A
kubectl -n kube-system get pods -l k8s-app=kube-proxy -o wide
```

```
NAMESPACE       NAME          DESIRED   CURRENT   READY   UP-TO-DATE   AVAILABLE   NODE SELECTOR            AGE
calico-system   calico-node   3         3         3       3            3           kubernetes.io/os=linux   12d
kube-system     kube-proxy    3         3         3       3            3           kubernetes.io/os=linux   12d
```

**Hands-on lab (test VM only)**

**Step 1 — build** a node agent and count its pods.

```bash
kubectl -n shop create deployment agent --image=busybox:1.36 --dry-run=client -o yaml -- sleep 3600 \
  | sed 's/kind: Deployment/kind: DaemonSet/; /replicas:/d; /strategy:/d; /^status:/d' > ds.yaml
kubectl apply -f ds.yaml
kubectl -n shop get ds agent                     # DESIRED 2: cp1 is tainted
```

**Step 2 — include the control plane.** Add a toleration for
`node-role.kubernetes.io/control-plane` with `operator: Exists` and `effect: NoSchedule`; DESIRED
becomes 3.

**Step 3 — break.** Add `nodeSelector: {role: monitoring}`. DESIRED drops to 0 and nothing
complains. Fix by labelling nodes (`kubectl label node w1 role=monitoring`) or removing the
selector.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Missing toleration | agent absent on tainted nodes | `kubectl get ds NAME` (DESIRED vs node count) | area 12 |
| Selector matches nothing | DESIRED 0, no errors | `kubectl get ds NAME -o wide` (NODE SELECTOR) | — |
| Pod fails on one node only | READY lower than DESIRED | `kubectl get pods -l KEY=VALUE -o wide` | [26](26-playbook-containers-k8s.md) |
| hostPort/hostNetwork conflict | one node CrashLoopBackOff: `address already in use` | `sudo ss -ltnp` on that node | [Ports inventory](22-playbook-ports-inventory.md) |

**Why it matters for troubleshooting.** When a node-level feature (networking, logs, metrics) is
broken on one node only, the first check is whether that node's DaemonSet pod is running and Ready.

**Next step.** Workloads that finish: Jobs and CronJobs.

### Job and CronJob

**Level:** [L2 · Mid] · CKA: Workloads & Scheduling

**Concept.** A **Job** runs pods until a number of them complete successfully, retrying failures up
to `backoffLimit` (default 6) with exponential back-off. A **CronJob** creates a Job on a cron
schedule. Jobs need `restartPolicy: Never` (a new pod per retry, failed pods kept for logs) or
`OnFailure` (the container restarts in place).

**Key terms**

| Field | Meaning |
|---|---|
| `completions` / `parallelism` | how many successes are needed / how many pods at once |
| `backoffLimit` | retries before the Job is marked failed (`BackoffLimitExceeded`) |
| `activeDeadlineSeconds` | hard time limit for the whole Job (`DeadlineExceeded`) |
| `ttlSecondsAfterFinished` | auto-clean finished Jobs and their pods |
| `schedule`, `timeZone` | cron expression, optional IANA time zone |
| `concurrencyPolicy` | `Allow` (default), `Forbid` (skip if the previous run is still going), `Replace` |
| `startingDeadlineSeconds` | how late a missed run may still start |
| `successfulJobsHistoryLimit` / `failedJobsHistoryLimit` | kept Jobs (defaults 3 and 1) |
| `suspend` | pause the schedule |

**See it on a real system**

```bash
kubectl -n shop get cronjobs,jobs,pods
kubectl -n shop describe job JOB | sed -n '/Pods Statuses:/p;/Events:/,$p'
kubectl -n shop wait --for=condition=complete job/JOB --timeout=120s
```

```
NAME                   SCHEDULE      TIMEZONE   SUSPEND   ACTIVE   LAST SCHEDULE   AGE
cronjob.batch/backup   */5 * * * *   <none>     False     0        2m              1h

NAME                        STATUS     COMPLETIONS   DURATION   AGE
job.batch/backup-29318640   Complete   1/1           6s         2m
job.batch/migrate           Failed     0/1           3m         3m
```

**Hands-on lab (test VM only)**

**Step 1 — a failing Job.**

```bash
kubectl -n shop create job migrate --image=busybox:1.36 --dry-run=client -o yaml -- sh -c 'echo migrating; exit 1' > migrate.yaml
sed -i 's/^spec:/spec:\n  backoffLimit: 2/' migrate.yaml       # fewer retries for the lab
kubectl apply -f migrate.yaml
kubectl -n shop get pods -l job-name=migrate -w
kubectl -n shop describe job migrate | tail -5
```

→ Three failed pods (the first try plus two retries, with growing pauses), then the condition
`Failed` with reason `BackoffLimitExceeded`: `Job has reached the specified backoff limit`. The
failed pods stay so you can run `kubectl logs` on them.

**Step 2 — a CronJob, tested without waiting for the schedule.**

```bash
kubectl -n shop create cronjob backup --image=busybox:1.36 --schedule='*/5 * * * *' -- sh -c 'date; echo backup done'
kubectl -n shop create job backup-manual-1 --from=cronjob/backup
kubectl -n shop logs job/backup-manual-1
```

**Step 3 — break the schedule.** `kubectl -n shop patch cronjob backup -p '{"spec":{"schedule":"61 * * * *"}}'`
is rejected: `spec.schedule: Invalid value: "61 * * * *"`. Then set
`concurrencyPolicy: Forbid` with a command that sleeps 400 s on a 5-minute schedule and watch runs
being skipped in the CronJob's events.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Task fails | `BackoffLimitExceeded` | `kubectl logs job/NAME` or the failed pods | [26](26-playbook-containers-k8s.md) |
| Task hangs | `DeadlineExceeded`, or a Job running forever | `kubectl describe job NAME` | — |
| CronJob never runs | `LAST SCHEDULE` empty; `SUSPEND True`, wrong time zone, or controller-manager down | `kubectl describe cronjob NAME` | area 20 |
| Missed runs after downtime | `too many missed start times` in events | set `startingDeadlineSeconds` | — |
| Old Jobs pile up | hundreds of Completed pods | history limits, `ttlSecondsAfterFinished` | — |

**Why it matters for troubleshooting.** Backups are CronJobs. A backup that "ran" but failed looks
fine unless someone checks Job status, so alert on failed Jobs ([Observability](32-learn-performance-observability.md)).

**Next step.** Who may do what: RBAC (area 14).

---

## 14. RBAC and ServiceAccounts

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Security: [TLS Basics](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics), certificates, kubeconfig, RBAC ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Users, permissions & security](10-users-permissions-security.md) (least privilege is the same idea as sudoers) · 3) Practice: the RBAC scenario in *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)), then *Kubernetes Challenges* (free, [course](https://kodekloud.com/courses/kubernetes-challenges)) · 4) Lab below: jane's certificate and the deployer ServiceAccount.

### Roles, ClusterRoles and bindings

**Level:** [L3 · Senior] · CKA: Cluster Architecture, Installation & Configuration

**Concept.** After authentication, the API server asks RBAC: "may this subject perform this verb
on this resource in this namespace?" RBAC is **additive** (there are no deny rules): permissions
come from **Roles** (namespaced) or **ClusterRoles** (cluster-wide, or reusable sets), granted to
subjects (User, Group, ServiceAccount) by **RoleBindings** (in one namespace) or
**ClusterRoleBindings** (everywhere). A RoleBinding may reference a ClusterRole; it then grants
those permissions only inside the binding's namespace, which is how the built-in `view`, `edit`
and `admin` ClusterRoles are reused per namespace.

```
 subject (User jane / Group dev-team / ServiceAccount shop:deployer)
     ^ subjects
 RoleBinding "jane-edit" (ns shop) ----roleRef----> ClusterRole "edit"   => jane can edit in shop only
 ClusterRoleBinding "ops-view" ---------roleRef---> ClusterRole "view"   => ops group can view everywhere
```

**Key terms**

| Field | Meaning |
|---|---|
| `apiGroups` | `""` for core (pods, services, secrets, configmaps), `apps` (deployments, statefulsets), `batch` (jobs), `networking.k8s.io` (ingresses, networkpolicies), `rbac.authorization.k8s.io` |
| `resources` | plural names; subresources like `pods/log`, `pods/exec`, `deployments/scale` |
| `verbs` | `get`, `list`, `watch`, `create`, `update`, `patch`, `delete`, `deletecollection` (`*` = all) |
| `resourceNames` | restrict to named objects |
| Built-in ClusterRoles | `cluster-admin`, `admin`, `edit`, `view` |

**See it on a real system**

```bash
kubectl -n shop get roles,rolebindings
kubectl get clusterrolebindings -o wide | grep -E 'cluster-admin|kubeadm'
kubectl -n shop describe rolebinding NAME
kubectl api-resources -o wide | grep -E '^deployments|^pods '      # API group and verbs per resource
kubectl auth can-i --list -n shop --as jane
```

**Hands-on lab (test VM only)** (uses the `jane` user created in the third topic of this area, or
just `--as`, which works without a certificate because you are cluster-admin)

**Step 1 — build.**

```bash
kubectl -n shop create role deploy-manager --verb=get,list,watch,create,update,patch --resource=pods,deployments
kubectl -n shop create rolebinding jane-deploy --role=deploy-manager --user=jane
kubectl -n shop describe role deploy-manager
```

```
PolicyRule:
  Resources         Non-Resource URLs  Resource Names  Verbs
  ---------         -----------------  --------------  -----
  pods              []                 []              [get list watch create update patch]
  deployments.apps  []                 []              [get list watch create update patch]
```

→ kubectl worked out that deployments live in the `apps` group. When you write YAML by hand you
must do that yourself.

**Step 2 — test with can-i.**

```bash
kubectl auth can-i list pods -n shop --as jane              # yes
kubectl auth can-i delete pods -n shop --as jane            # no
kubectl auth can-i list pods -n default --as jane           # no: the binding is only in shop
kubectl auth can-i get pods --subresource=log -n shop --as jane   # no: pods/log is separate
```

**Step 3 — break by hand-written YAML.** Write the same Role in YAML with `apiGroups: [""]` for
`deployments`. `kubectl -n shop get deploy --as jane` fails:
`Error from server (Forbidden): deployments.apps is forbidden: User "jane" cannot list resource "deployments" in API group "apps" in the namespace "shop"`.
The error names the exact group; fix `apiGroups: ["apps"]`.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Missing permission | `Forbidden ... cannot VERB resource "R" in API group "G" in the namespace "NS"` | `kubectl auth can-i VERB R -n NS --as SUBJECT` | [26](26-playbook-containers-k8s.md) |
| Wrong API group | Forbidden only for deployments/jobs/ingresses | `kubectl api-resources` (APIVERSION column) | this topic |
| Binding in the wrong namespace | works in one namespace, not another | `kubectl get rolebindings -n NS -o wide` | — |
| Subresource missing | can get pods but `kubectl logs`/`exec` is forbidden | add `pods/log`, `pods/exec` | this topic |

**Why it matters for troubleshooting.** Forbidden messages are precise: subject, verb, resource,
group, namespace. Read them literally and reproduce with `can-i --as` before changing anything.

**Next step.** Identities for programs: ServiceAccounts.

### ServiceAccounts and tokens

**Level:** [L3 · Senior] · CKA: Cluster Architecture, Installation & Configuration

**Concept.** Programs (pods, CI pipelines) authenticate as **ServiceAccounts** (SA), which are
namespaced objects. Every namespace has a `default` SA. Pods get a short-lived, automatically
rotated **projected token** mounted at `/var/run/secrets/kubernetes.io/serviceaccount/`. Since
v1.24 no long-lived token Secrets are created automatically; for an external client such as a
GitLab CI job, create a time-limited token with `kubectl create token`. In RBAC an SA is the
subject `system:serviceaccount:NS:NAME`.

**Key terms**

| Term | Meaning |
|---|---|
| `spec.serviceAccountName` | which SA a pod runs as (default `default`) |
| `automountServiceAccountToken: false` | do not mount a token (most apps never call the API) |
| `kubectl create token SA --duration=1h` | short-lived token for testing or CI |
| `imagePullSecrets` on an SA | added automatically to pods using that SA (area 17) |

**See it on a real system**

```bash
kubectl -n shop get sa
kubectl -n shop get pod POD -o jsonpath='{.spec.serviceAccountName}{"\n"}'
kubectl -n shop exec POD -- ls /var/run/secrets/kubernetes.io/serviceaccount/
kubectl auth can-i --list -n shop --as=system:serviceaccount:shop:default | head
```

**Hands-on lab (test VM only)**

**Step 1 — a deploy identity for CI.**

```bash
kubectl -n shop create serviceaccount deployer
kubectl -n shop create rolebinding deployer-edit --clusterrole=edit --serviceaccount=shop:deployer
TOKEN=$(kubectl -n shop create token deployer --duration=1h)
kubectl --token="$TOKEN" --server=https://192.168.56.10:6443 --certificate-authority=/etc/kubernetes/pki/ca.crt -n shop get deploy
```

**Step 2 — break.** Bind it in the wrong namespace
(`kubectl -n default create rolebinding deployer-edit --clusterrole=edit --serviceaccount=shop:deployer`
instead of `-n shop`, after removing the correct one):
`User "system:serviceaccount:shop:deployer" cannot list resource "deployments" in API group "apps" in the namespace "shop"`.

**Step 3 — fix** by binding in `shop`, and test with
`kubectl auth can-i list deployments -n shop --as=system:serviceaccount:shop:deployer`.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| SA bound in wrong namespace | Forbidden for `system:serviceaccount:...` | `kubectl auth can-i ... --as=system:serviceaccount:NS:SA` | this topic |
| Pod references a missing SA | RS event `error looking up service account shop/deployer: serviceaccount "deployer" not found` | `kubectl describe rs RS` | area 6 |
| Token expired in CI | `Unauthorized` after a while | token `--duration`; create per pipeline run | [CI/CD](33-learn-cicd-iac-sre.md) |
| Too much power | CI token can read all Secrets | bind `edit` per namespace, not `cluster-admin` | [Security](10-users-permissions-security.md) |

**Why it matters for troubleshooting.** When an in-cluster tool (an operator, Argo, a CI runner)
"does nothing", the reason is often a Forbidden error in *its* logs, not yours. Check its SA with
`can-i --as`.

**Next step.** Human users and certificates.

### Users, client certificates and kubectl auth can-i

**Level:** [L3 · Senior] · CKA: Cluster Architecture, Installation & Configuration

**Concept.** Kubernetes has no User objects. A human user is whoever presents a credential the API
server trusts: most simply, a client certificate signed by the cluster CA, where the certificate's
**CN** is the username and each **O** is a group. The **CertificateSigningRequest** (CSR) API lets
you sign such certificates without touching the CA key. Group membership comes from the
certificate, so changing groups means a new certificate.

**Key terms**

| Term | Meaning |
|---|---|
| CN / O | username / groups in a client certificate |
| CSR object | `certificates.k8s.io/v1`, signer `kubernetes.io/kube-apiserver-client` |
| `kubectl certificate approve` | signs it with the cluster CA |
| `--as`, `--as-group` | impersonate a user or group (requires the `impersonate` permission) |
| `kubectl auth whoami` | which identity the API server sees for you |

**See it on a real system**

```bash
kubectl get csr
openssl x509 -in jane.crt -noout -subject -enddate
kubectl auth can-i --list -n dev --as jane --as-group dev-team
```

**Hands-on lab (test VM only)**

**Step 1 — create and sign a certificate for jane** (group `dev-team`, valid one day).

```bash
openssl genrsa -out jane.key 2048
openssl req -new -key jane.key -subj "/CN=jane/O=dev-team" -out jane.csr
cat <<EOT | kubectl apply -f -
apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: jane
spec:
  request: $(base64 -w0 < jane.csr)
  signerName: kubernetes.io/kube-apiserver-client
  expirationSeconds: 86400
  usages: ["client auth"]
EOT
kubectl certificate approve jane
kubectl get csr jane -o jsonpath='{.status.certificate}' | base64 -d > jane.crt
```

**Step 2 — build a context for jane and grant the group, not the user.**

```bash
kubectl create namespace dev
kubectl config set-credentials jane --client-key=jane.key --client-certificate=jane.crt --embed-certs=true
kubectl config set-context jane@lab --cluster=kubernetes --user=jane --namespace=dev
kubectl -n dev create rolebinding dev-team-edit --clusterrole=edit --group=dev-team
kubectl --context jane@lab get pods
```

**Step 3 — break.** Sign a second certificate with `/O=devteam` (missing dash). jane authenticates
fine but is Forbidden everywhere: authentication succeeded, authorization did not. Inspect with
`openssl x509 -noout -subject` and compare the O with the binding's group.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| CSR never approved | `status.certificate` empty; jane.crt empty | `kubectl get csr` (CONDITION Pending) | this topic |
| Wrong CN/O | Forbidden as an unexpected user or group | `openssl x509 -in FILE -noout -subject` | [TLS](18-web-http-tls.md) |
| Expired client cert | `You must be logged in to the server (Unauthorized)` | `openssl x509 -in FILE -noout -enddate` | area 19 |
| Wrong cluster CA in kubeconfig | `x509: certificate signed by unknown authority` | area 4 | area 4 |

**Why it matters for troubleshooting.** Separate the two questions every access error contains:
"who does the API think I am?" (`kubectl auth whoami`) and "what may that identity do?"
(`kubectl auth can-i --list`).

**Next step.** Restricting traffic between pods: NetworkPolicies (area 15).

---

## 15. NetworkPolicies

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Security: NetworkPolicies ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) KodeKloud: *Kubernetes Networking Deep Dive* — Cilium CNI and NetworkPolicies ([course](https://kodekloud.com/courses/kubernetes-networking)) · 3) Practice: the Unreachable Pods + Leaky Network Policies scenario in *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)) · 4) Note: [Networking](28-learn-networking.md) for default-deny firewall thinking (UFW rules become NetworkPolicies).

### NetworkPolicy model and default deny

**Level:** [L3 · Senior] · CKA: Services & Networking

**Concept.** By default every pod can reach every other pod in the cluster. A **NetworkPolicy**
selects pods (`podSelector`) and, for the directions listed in `policyTypes` (Ingress, Egress),
makes them **isolated**: only traffic that some policy allows is permitted. Policies are additive:
the allowed set is the union of all policies that select the pod. Return traffic of an allowed
connection is always permitted. Policies are enforced by the **CNI**: Calico and Cilium enforce
them; Flannel silently ignores them, so the objects exist and nothing happens.

```
 namespace shop                           namespace shop
 [frontend] --- allowed (policy) ---> [api :8080]    <- api selected by a policy: isolated for ingress
 [debug pod] ---X  denied ----------> [api :8080]       only listed sources get in
```

**Key terms**

| Field | Meaning |
|---|---|
| `podSelector: {}` | all pods in the policy's namespace |
| `policyTypes` | which directions this policy isolates |
| `ingress[].from` / `egress[].to` | allowed peers: `podSelector`, `namespaceSelector`, `ipBlock` |
| `ports` | allowed ports (with optional `endPort` for ranges) |
| `kubernetes.io/metadata.name` | label every namespace gets automatically, handy for `namespaceSelector` |

**See it on a real system**

```bash
kubectl get networkpolicy -A
kubectl -n shop describe networkpolicy NAME
kubectl get pods -A | grep -E 'calico|cilium|flannel'      # which CNI runs (calico-system, kube-flannel or kube-system)? does it enforce policies?
```

**Hands-on lab (test VM only)** (requires Calico or Cilium)

**Step 1 — build** an API and two clients.

```bash
kubectl -n shop create deployment api --image=nginx:1.27
kubectl -n shop expose deploy api --port=80
kubectl -n shop run frontend --image=nicolaka/netshoot --labels=role=frontend -- sleep 3600
kubectl -n shop run other --image=nicolaka/netshoot --labels=role=other -- sleep 3600
kubectl -n shop exec frontend -- curl -s -m 3 -o /dev/null -w '%{http_code}\n' http://api   # 200
kubectl -n shop exec other -- curl -s -m 3 -o /dev/null -w '%{http_code}\n' http://api      # 200
```

**Step 2 — default deny ingress for the whole namespace.**

```bash
cat <<'EOT' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-ingress
  namespace: shop
spec:
  podSelector: {}
  policyTypes: ["Ingress"]
EOT
kubectl -n shop exec frontend -- curl -s -m 3 -o /dev/null -w '%{http_code}\n' http://api   # 000, timeout
```

**Step 3 — allow only the frontend to reach the API on port 80.**

```bash
cat <<'EOT' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-allow-frontend
  namespace: shop
spec:
  podSelector:
    matchLabels: {app: api}
  policyTypes: ["Ingress"]
  ingress:
  - from:
    - podSelector:
        matchLabels: {role: frontend}
    ports:
    - protocol: TCP
      port: 80
EOT
```

Now `frontend` gets 200 and `other` times out. Note the port is the **pod's** port (targetPort),
not the Service port: policies are evaluated after the Service DNAT.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Default deny added, allows forgotten | timeouts (not refusals) between apps | `kubectl get netpol -n NS` | [26](26-playbook-containers-k8s.md) |
| Policy uses the Service port | allowed client still times out | compare policy `port` with `targetPort` | area 7 |
| Labels on the client differ | one client blocked | `kubectl get pods --show-labels` | — |
| CNI does not enforce | policy "does nothing" | check the CNI (Flannel ignores policies) | area 3 |
| Ingress controller blocked | site returns 504 after a default deny | allow from the controller's namespace | area 8 |

**Why it matters for troubleshooting.** NetworkPolicy drops look like a dead network: timeouts,
no log lines in the app. When "it worked yesterday" and someone added policies, list them first.

**Next step.** The two mistakes everyone makes: DNS and selector logic.

### Allowing DNS and the AND vs OR trap

**Level:** [L3 · Senior] · CKA: Services & Networking, Troubleshooting

**Concept.** A default-deny **egress** policy also blocks DNS, so every name lookup times out and
apps report "could not resolve host". Always pair egress isolation with a rule that allows UDP and
TCP 53 to the CoreDNS pods. The second trap is YAML structure: inside one `from` (or `to`) list
item, a `namespaceSelector` and a `podSelector` are **AND**ed; as two separate list items they are
**OR**ed. One dash changes the meaning.

```yaml
# AND: pods labelled role=frontend IN namespaces labelled team=web
  - from:
    - namespaceSelector:
        matchLabels: {team: web}
      podSelector:
        matchLabels: {role: frontend}

# OR: ANY pod in namespaces labelled team=web, OR pods labelled role=frontend in THIS namespace
  - from:
    - namespaceSelector:
        matchLabels: {team: web}
    - podSelector:
        matchLabels: {role: frontend}
```

**Key terms**

| Pattern | Use |
|---|---|
| default deny egress + allow DNS | baseline for locked-down namespaces |
| `namespaceSelector: {matchLabels: {kubernetes.io/metadata.name: kube-system}}` | target one namespace by name |
| `ipBlock` with `except` | allow external CIDRs (e.g. the database at 192.168.56.50/32) |

**See it on a real system**

```bash
kubectl -n shop get netpol -o yaml | grep -nE 'from:|to:|namespaceSelector|podSelector|- ' | head -40
kubectl get ns --show-labels | head -5
```

**Hands-on lab (test VM only)**

**Step 1 — break DNS.** Add a default deny for egress in `shop`:

```bash
cat <<'EOT' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: shop
spec:
  podSelector: {}
  policyTypes: ["Egress"]
EOT
kubectl -n shop exec frontend -- nslookup api
```

```
;; communications error to 10.96.0.10#53: timed out
;; no servers could be reached
```

**Step 2 — fix DNS** (and then allow frontend to reach the API, since egress is now isolated too).

```bash
cat <<'EOT' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: shop
spec:
  podSelector: {}
  policyTypes: ["Egress"]
  egress:
  - to:
    - namespaceSelector:
        matchLabels: {kubernetes.io/metadata.name: kube-system}
      podSelector:
        matchLabels: {k8s-app: kube-dns}
    ports:
    - {protocol: UDP, port: 53}
    - {protocol: TCP, port: 53}
---
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: frontend-egress-api
  namespace: shop
spec:
  podSelector:
    matchLabels: {role: frontend}
  policyTypes: ["Egress"]
  egress:
  - to:
    - podSelector:
        matchLabels: {app: api}
    ports:
    - {protocol: TCP, port: 80}
EOT
kubectl -n shop exec frontend -- curl -s -m 3 -o /dev/null -w '%{http_code}\n' http://api   # 200
```

**Step 3 — break with one dash.** In `allow-dns`, put a `-` before `podSelector` so it becomes a
separate list item. DNS still works, but the rule now also allows port 53 to *every pod in
kube-system* and *any pod labelled k8s-app=kube-dns in shop*. Nothing fails, which is why this
mistake survives reviews. Check policies with `kubectl describe netpol`, which prints the
interpretation in words.

**Step 4 — clean up** the lab policies when done (list them first with
`kubectl -n shop get netpol`), because later labs in `shop` assume open networking.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Egress deny without DNS | `no servers could be reached`, `could not resolve host` | `kubectl get netpol -n NS` | area 9 |
| AND written as OR | too much allowed (silent) | `kubectl describe netpol NAME` | this topic |
| OR written as AND | expected clients blocked | `kubectl describe netpol NAME` | this topic |
| Namespace label missing | cross-namespace allow does nothing | `kubectl get ns --show-labels` | — |

**Why it matters for troubleshooting.** The CoreDNS case in your Ops Ladder ("a NetworkPolicy
blocks port 53 to kube-dns") is exactly Step 1. Recognise it from the timeout pattern in seconds.

**Next step.** Installing real software into the cluster: Helm and Kustomize (area 16).

---

## 16. Helm and Kustomize

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Helm Basics and Kustomize Basics (2025 updates) ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) KodeKloud: *Helm for Beginners* ([course](https://kodekloud.com/courses/helm-for-beginners)) once the basics are done · 3) Video: KodeKloud *What is Helm? | Helm Concepts Explained* ([YouTube](https://www.youtube.com/watch?v=kJscDZfHXrQ), 13 min) · 4) Practice: the KodeKloud [Helm Playground](https://kodekloud.com/playgrounds/playground-helm), then the Traefik install and failed-upgrade rollback lab below.

### Helm: charts, releases and values

**Level:** [L2 · Mid] (install, rollback) → [L3 · Senior] (own charts) · CKA: Cluster Architecture, Installation & Configuration

**Concept.** **Helm** is the package manager for Kubernetes. A **chart** is a set of templated
manifests plus a default `values.yaml`; installing it with your values creates a **release** (a
named instance in a namespace). Each install, upgrade or rollback is a new **revision**, stored as
a Secret in the release's namespace, which is what makes `helm rollback` possible. Most cluster
add-ons (ingress controllers, cert-manager, monitoring stacks, Harbor itself) are installed this
way. Think of it as "Docker Compose with variables and versioned rollbacks".

**Key terms**

| Command | Purpose |
|---|---|
| `helm repo add NAME URL` / `helm repo update` | register a chart repository / refresh its index |
| `helm search repo KEYWORD` | find charts |
| `helm show values CHART` | every setting the chart accepts, with defaults |
| `helm install REL CHART -n NS --create-namespace -f values.yaml` | install a release |
| `helm upgrade --install REL CHART -f values.yaml` | idempotent install-or-upgrade (the CI favourite) |
| `helm list -A` / `helm history REL -n NS` | releases / revisions with status |
| `helm rollback REL REV -n NS` | go back to a revision |
| `helm get values REL` / `helm get manifest REL` | what you set / what was actually applied |
| `helm template REL CHART -f values.yaml` | render locally without installing (review, diff) |
| `helm uninstall REL -n NS` | remove the release and its objects |

> Helm 4 was released in late 2025 and renamed or changed some flags (for example around
> `--atomic` and `--force`). Commands above work in Helm 3; check `helm help upgrade` for the
> version you run.

**See it on a real system**

```bash
helm version
helm list -A
helm -n traefik history traefik
kubectl -n traefik get secrets -l owner=helm
```

```
$ helm -n shop history demo
REVISION  UPDATED                   STATUS           CHART        APP VERSION  DESCRIPTION
1         Fri Oct  3 10:02:11 2026  superseded       demo-0.1.0   1.16.0       Install complete
2         Fri Oct  3 10:09:45 2026  superseded       demo-0.1.0   1.16.0       Upgrade complete
3         Fri Oct  3 10:15:02 2026  failed           demo-0.1.0   1.16.0       Upgrade "demo" failed: context deadline exceeded
4         Fri Oct  3 10:17:30 2026  deployed         demo-0.1.0   1.16.0       Rollback to 2
```

**Hands-on lab (test VM only)**

**Step 1 — install the ingress controller used in area 8.** Values keys change between chart
versions: confirm them with `helm show values traefik/traefik` before installing.

```bash
helm repo add traefik https://traefik.github.io/charts
helm repo update
cat <<'EOT' > traefik-values.yaml
service:
  type: NodePort
ports:
  web:
    nodePort: 31080
  websecure:
    nodePort: 31443
providers:
  kubernetesGateway:
    enabled: true
EOT
helm upgrade --install traefik traefik/traefik -n traefik --create-namespace -f traefik-values.yaml
kubectl -n traefik get pods,svc
kubectl get ingressclass
```

**Step 2 — your own chart.** `helm create` scaffolds a working nginx chart, perfect for practice.

```bash
helm create demo
helm install demo ./demo -n shop
helm upgrade demo ./demo -n shop --set replicaCount=3
helm -n shop history demo
```

**Step 3 — break.** Upgrade with an image tag that does not exist and wait for readiness:

```bash
helm upgrade demo ./demo -n shop --set image.tag=9.99-nope --wait --timeout 60s
```

`Error: UPGRADE FAILED: context deadline exceeded`; history shows revision 3 `failed`. (If you
interrupt an upgrade with Ctrl-C you may instead see status `pending-upgrade`, and every later
upgrade fails with `another operation (install/upgrade/rollback) is in progress`.)

**Step 4 — fix.** `helm -n shop rollback demo 2`, then `helm -n shop history demo`.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Release stuck pending | `another operation (install/upgrade/rollback) is in progress` | `helm history REL -n NS` then `helm rollback REL LAST_GOOD` | [26](26-playbook-containers-k8s.md) |
| Name reuse | `cannot re-use a name that is still in use` | `helm list -A --all` | — |
| Wrong value key | setting silently ignored (typo in values) | `helm get values REL`; `helm template` and grep | — |
| No kubeconfig (e.g. ran with sudo) | `Kubernetes cluster unreachable: Get "http://localhost:8080/version": ... connection refused` | `echo $KUBECONFIG`; run as your user | area 4 |
| Manual edits to Helm-managed objects | next upgrade reverts them | `helm get manifest REL` vs live | area 1 |

**Why it matters for troubleshooting.** "What exactly is deployed and what changed?" for any
Helm-installed component is `helm history` plus `helm get values/manifest`. Rollback is one
command, like `kubectl rollout undo`.

**Next step.** Template-free customisation with Kustomize.

### Kustomize

**Level:** [L3 · Senior] · CKA: Cluster Architecture, Installation & Configuration

**Concept.** **Kustomize** (built into kubectl as `-k`) customises plain YAML without templates: a
**base** holds the common manifests, and **overlays** (dev, prod) patch them: different replica
counts, image tags, name prefixes, labels, generated ConfigMaps. Everything stays valid YAML you
can read. The CKA curriculum lists it next to Helm.

```
 app/
   base/        kustomization.yaml  deployment.yaml  service.yaml
   overlays/
     prod/      kustomization.yaml  (resources: ../../base, replicas, images, patches)
```

**Key terms**

| Field | Effect |
|---|---|
| `resources` | files or directories to include |
| `namespace`, `namePrefix`, `labels` | applied to every object |
| `images` | change image names or tags without editing the Deployment |
| `replicas` | set replica counts |
| `configMapGenerator` | build a ConfigMap with a content-hash suffix, so changes roll pods |
| `patches` | strategic-merge or JSON patches |

**See it on a real system**

```bash
kubectl kustomize app/overlays/prod | less      # render only
kubectl diff -k app/overlays/prod               # what would change
kubectl apply -k app/overlays/prod
```

**Hands-on lab (test VM only)**

**Step 1 — build.**

```bash
mkdir -p app/base app/overlays/prod
kubectl create deployment web --image=nginx:1.27 --dry-run=client -o yaml > app/base/deployment.yaml
cat <<'EOT' > app/base/kustomization.yaml
resources:
- deployment.yaml
EOT
cat <<'EOT' > app/overlays/prod/kustomization.yaml
namespace: shop
namePrefix: prod-
resources:
- ../../base
replicas:
- name: web
  count: 3
images:
- name: nginx
  newTag: "1.28"
configMapGenerator:
- name: web-cfg
  literals:
  - LOG_LEVEL=warn
EOT
kubectl kustomize app/overlays/prod | grep -E 'name:|image:|replicas:'
kubectl apply -k app/overlays/prod
```

**Step 2 — break.** Change `../../base` to `../base`:
`error: accumulating resources: accumulation err='accumulating resources from '../base': ...': ... no such file or directory`.
Fix the path.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Wrong resource path | `accumulating resources ... no such file or directory` | `ls` relative to the kustomization | — |
| Patch target not found | `no matches for Id ...` | `kubectl kustomize` the base, check names | — |
| Generated ConfigMap name changes | pods reference the old hashed name if applied without the overlay | always apply through `-k` | area 10 |

**Why it matters for troubleshooting.** With GitOps tools (Argo CD, Flux) the deployed YAML is
rendered from Helm or Kustomize. Render it locally (`helm template`, `kubectl kustomize`) to see
exactly what the cluster received.

**Next step.** Pulling your own images from Harbor (area 17).

---

## 17. Private registries and Harbor

> 📚 **Study path:** 1) Note: the registry and Harbor topics in [Docker](30-learn-docker.md) and the certificate chapters of [Web, HTTP & TLS](18-web-http-tls.md) as a refresher · 2) KodeKloud: there is no Harbor course; use the [Docker vs ContainerD](https://notes.kodekloud.com/docs/kubernetes-for-the-absolute-beginners-hands-on-tutorial/Kubernetes-Overview/Docker-vs-ContainerD) note from *Kubernetes for the Absolute Beginners – Hands-on Tutorial* (crictl, ctr, nerdctl) and the LFCS note [Work With SSL Certificates](https://notes.kodekloud.com/docs/Linux-Foundation-Certified-System-Administrator-LFCS/Essential-Commands/Work-With-SSL-Certificates) · 3) Official: [Harbor docs](https://goharbor.io/docs/) and [Configure HTTPS Access to Harbor](https://goharbor.io/docs/2.15.0/install-config/configure-https/) · 4) Practice: the Image Pull Errors scenario in *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)), then the private-CA lab below.

### imagePullSecrets and Harbor robot accounts

**Level:** [L2 · Mid] · CKA: Troubleshooting (ImagePullBackOff)

**Concept.** Image pulls are done by **containerd on the node**, not by the pod and not by
CoreDNS. The kubelet passes credentials from the pod's `imagePullSecrets` (or from its
ServiceAccount's `imagePullSecrets`) to containerd. In Harbor, use a **robot account** per project
with pull-only permission; its name looks like `robot$shop+k8s-pull`, and the `$` must be in single
quotes in the shell. Name resolution and TLS trust for the registry come from the **node**
(systemd-resolved, CA store, containerd config), which is why a pull can fail on one node and work
on another.

```
 kubelet (w1) --CRI PullImage(image, creds from imagePullSecret)--> containerd (w1)
      containerd: resolve harbor.example.com via the NODE's resolver (127.0.0.53)
                  TLS: trust via /etc/containerd/certs.d/harbor.example.com/ or system CA
                  auth: token from Harbor with robot credentials
                  GET /v2/shop/web/manifests/1.4.2 -> layers -> unpack
```

**Key terms**

| Term | Meaning |
|---|---|
| `kubernetes.io/dockerconfigjson` | Secret type holding registry credentials |
| `imagePullSecrets` | list of such Secrets on a pod or ServiceAccount (same namespace) |
| `imagePullPolicy` | `IfNotPresent` (default for tagged images), `Always` (default for `:latest` or no tag), `Never` |
| Robot account | Harbor machine credential scoped to projects and actions |
| Proxy cache project | a Harbor project that caches Docker Hub, useful when nodes cannot reach the internet |

**See it on a real system**

```bash
kubectl -n shop get pod POD -o jsonpath='{.spec.imagePullSecrets}{"\n"}'
kubectl -n shop get sa default -o jsonpath='{.imagePullSecrets}{"\n"}'
kubectl -n shop get secret harbor-pull -o jsonpath='{.data.\.dockerconfigjson}' | base64 -d; echo
kubectl -n shop describe pod POD | grep -A8 Events
sudo crictl pull --creds 'robot$shop+k8s-pull:TOKEN' harbor.example.com/shop/web:1.4.2    # on the node: the raw error
```

**Hands-on lab (test VM only)** (needs a Harbor or any private registry reachable from the nodes;
see the next topic for a minimal TLS registry)

**Step 1 — build the pull secret and attach it to the namespace's default ServiceAccount.**

```bash
kubectl -n shop create secret docker-registry harbor-pull \
  --docker-server=harbor.example.com \
  --docker-username='robot$shop+k8s-pull' \
  --docker-password='ROBOT_TOKEN'
kubectl -n shop patch serviceaccount default -p '{"imagePullSecrets":[{"name":"harbor-pull"}]}'
kubectl -n shop create deployment private --image=harbor.example.com/shop/web:1.4.2
kubectl -n shop get pods -l app=private
```

**Step 2 — break the credentials.** Recreate the secret with a wrong password and restart the
deployment. The events show a 401:

```
Failed to pull image "harbor.example.com/shop/web:1.4.2": failed to pull and unpack image "harbor.example.com/shop/web:1.4.2": failed to resolve reference "harbor.example.com/shop/web:1.4.2": failed to authorize: failed to fetch oauth token: unexpected status from GET request to https://harbor.example.com/service/token?scope=repository%3Ashop%2Fweb%3Apull&service=harbor-registry: 401 Unauthorized
```

**Step 3 — break the reference.** Put the secret only in namespace `default` and deploy in `shop`:
event `Unable to retrieve some image pull secrets (harbor-pull); attempting to pull the image may not succeed.`
Pull secrets are namespaced.

**Step 4 — fix** both, then `kubectl -n shop rollout restart deploy/private`. Note that patching
the ServiceAccount only affects pods created afterwards.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Wrong or missing credentials | `401 Unauthorized` while fetching the token | decode the secret; test with `crictl pull --creds` | [26](26-playbook-containers-k8s.md) |
| Wrong tag or project | `failed to resolve reference ...: not found` | check the tag in Harbor | — |
| Secret in another namespace | `Unable to retrieve some image pull secrets` | `kubectl -n NS get secret` | this topic |
| Node cannot resolve the registry | `dial tcp: lookup harbor.example.com on 127.0.0.53:53: no such host` | `resolvectl query harbor.example.com` on the node | [DNS](08-dns.md) |
| Private CA not trusted | `x509: certificate signed by unknown authority` | next topic | next topic |
| Wrong architecture | `no match for platform in manifest` | build multi-arch or the right arch | [Docker](30-learn-docker.md) |

**Why it matters for troubleshooting.** `ImagePullBackOff` is decided on the node. When `describe`
is not clear enough, `crictl pull` on that node reproduces the exact error in seconds.

**Next step.** Teach containerd to trust Harbor's private CA.

### containerd hosts.toml for a private CA

**Level:** [L3 · Senior] · CKA: background for your Harbor (not an exam topic)

**Concept.** containerd reads per-registry settings from a **hosts directory**:
`/etc/containerd/certs.d/REGISTRY/hosts.toml`. There you set which CA to trust, client
certificates, mirrors, and capabilities. Changes to `hosts.toml` are read on the next pull (no
restart); enabling the directory itself (`config_path`, area 3) needs a containerd restart. Every
node that may run the pod needs it, so manage it with Ansible
([CI/CD & IaC](33-learn-cicd-iac-sre.md)). Docker reads a different place
(`/etc/docker/certs.d/REGISTRY/ca.crt`), which is why "docker pull works on my laptop" proves
nothing about the nodes.

**Key terms**

| Item | Meaning |
|---|---|
| `server` | the upstream registry for this namespace |
| `[host."https://..."]` | an endpoint to try (mirror or the registry itself) |
| `capabilities` | `pull`, `resolve`, `push` |
| `ca` | CA file to trust for that host |
| `override_path = true` | the host URL already contains the API path (used for Harbor proxy-cache projects) |
| System CA alternative | copy the CA to `/usr/local/share/ca-certificates/` and run `update-ca-certificates`, then restart containerd |

**See it on a real system**

```bash
sudo containerd config dump | grep -n config_path
sudo ls -R /etc/containerd/certs.d/
sudo cat /etc/containerd/certs.d/harbor.example.com/hosts.toml
openssl s_client -connect harbor.example.com:443 -servername harbor.example.com -showcerts </dev/null 2>/dev/null | grep -E 's:|i:'
```

```
 0 s:CN = harbor.example.com
   i:CN = Example Internal CA
```

→ The server certificate is issued by `Example Internal CA`, which no default trust store knows.
Every node must be told to trust it.

**Hands-on lab (test VM only)**

**Step 1 — a minimal TLS registry signed by your own CA** (on a separate Docker VM, e.g.
192.168.56.30 with DNS or `/etc/hosts` name `registry.lab.example.com` on every node):

```bash
openssl req -x509 -newkey rsa:4096 -nodes -days 365 -keyout ca.key -out ca.crt -subj "/CN=Lab Internal CA"
openssl req -newkey rsa:2048 -nodes -keyout registry.key -out registry.csr -subj "/CN=registry.lab.example.com"
printf 'subjectAltName=DNS:registry.lab.example.com\n' > san.ext
openssl x509 -req -in registry.csr -CA ca.crt -CAkey ca.key -CAcreateserial -days 365 -out registry.crt -extfile san.ext
mkdir -p certs && cp registry.crt registry.key certs/
docker run -d --name registry -p 443:443 -v "$PWD/certs:/certs:ro" \
  -e REGISTRY_HTTP_ADDR=0.0.0.0:443 \
  -e REGISTRY_HTTP_TLS_CERTIFICATE=/certs/registry.crt \
  -e REGISTRY_HTTP_TLS_KEY=/certs/registry.key registry:2
```

Push an image to it from that VM (trust the CA for Docker there with
`/etc/docker/certs.d/registry.lab.example.com/ca.crt`).

**Step 2 — observe the break.** Deploy `registry.lab.example.com/web:1` to the cluster:
`ErrImagePull` with `tls: failed to verify certificate: x509: certificate signed by unknown authority`.

**Step 3 — fix on every node** (no containerd restart needed once `config_path` is set):

```bash
sudo mkdir -p /etc/containerd/certs.d/registry.lab.example.com
sudo cp ca.crt /etc/containerd/certs.d/registry.lab.example.com/ca.crt
cat <<'EOT' | sudo tee /etc/containerd/certs.d/registry.lab.example.com/hosts.toml
server = "https://registry.lab.example.com"

[host."https://registry.lab.example.com"]
  capabilities = ["pull", "resolve"]
  ca = "/etc/containerd/certs.d/registry.lab.example.com/ca.crt"
EOT
sudo crictl pull registry.lab.example.com/web:1
```

**Step 4 — Harbor as a Docker Hub cache (on-prem pattern).** If nodes cannot reach the internet,
create a proxy-cache project in Harbor (here `dockerhub`) and point `docker.io` at it:

```
# /etc/containerd/certs.d/docker.io/hosts.toml
server = "https://registry-1.docker.io"

[host."https://harbor.example.com/v2/dockerhub"]
  capabilities = ["pull", "resolve"]
  ca = "/etc/containerd/certs.d/harbor.example.com/ca.crt"
  override_path = true
```

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| CA not trusted | `x509: certificate signed by unknown authority` | `openssl s_client ... -showcerts` | [TLS](18-web-http-tls.md) |
| `config_path` not set (containerd 1.7) | hosts.toml ignored, same x509 error | `sudo containerd config dump` (look for `config_path`) | area 3 |
| Directory name differs from image host (or port) | hosts.toml ignored | directory must match `HOST` or `HOST:PORT` exactly as in the image name | this topic |
| Cert lacks SAN | `x509: certificate relies on legacy Common Name field` or name mismatch | `openssl x509 -noout -ext subjectAltName` | [TLS](18-web-http-tls.md) |
| Clock skew on node | `certificate has expired or is not yet valid` | `timedatectl` | [Time](12-time-ntp.md) |
| Fixed on one node only | pod works until rescheduled elsewhere | check every node (Ansible) | — |

**Why it matters for troubleshooting.** This is the exact "x509 pulling from Harbor" case in your
Ops Ladder. The fix is per node, in containerd's config, never in Kubernetes objects.

**Next step.** See what the cluster is doing: observability (area 18).

---

## 18. Observability and node-level debugging

> 📚 **Study path:** 1) Note: [Logs & journal](06-logs-journal.md) and [systemd](07-services-systemd.md) as a refresher, because node debugging is systemd debugging · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Logging & Monitoring, then Troubleshooting: [Worker Node Failure](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Worker-Node-Failure) ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 3) KodeKloud: the Ephemeral/Debug Containers prerequisite in *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)); later, at L4, the video *Kubernetes Monitoring Made Easy with Prometheus* ([YouTube](https://www.youtube.com/watch?v=6xmWr7p5TE0), 68 min) · 4) Practice: [iximiuz Labs Kubernetes challenges](https://labs.iximiuz.com/challenges?category=kubernetes).

### Events and logs

**Level:** [L1 · Junior] · CKA: Troubleshooting

**Concept.** **Events** are short records written by controllers, the scheduler and kubelets
("Scheduled", "Pulled", "FailedMount", "BackOff"). They are the cluster's own narration and the
fastest source of truth, but they expire after **one hour** by default, so look early and save them
during incidents. **Container logs** are the stdout/stderr of each container; the kubelet stores
them on the node under `/var/log/pods/` and rotates them (10 MiB x 5 files per container by
default). `kubectl logs` reads them through the kubelet, so it only works while the pod exists.
Long-term logs need a collector (Loki, Elasticsearch) shipping from the nodes.

**Key terms**

| Command | Purpose |
|---|---|
| `kubectl get events -A --sort-by=.lastTimestamp` | recent events, cluster-wide |
| `kubectl events -n NS --for pod/POD --types=Warning` | events for one object (newer `kubectl events` command) |
| `kubectl logs POD -c C --previous --tail=100 --since=10m --timestamps` | container logs |
| `kubectl logs -l app=web --all-containers --prefix --max-log-requests=10` | logs across pods |
| `/var/log/pods/NS_POD_UID/CONTAINER/0.log` | the files on the node |
| `/var/log/containers/*.log` | symlinks, the path log shippers usually tail |

**See it on a real system**

```bash
kubectl get events -A --field-selector type=Warning --sort-by=.lastTimestamp | tail -20
kubectl -n shop events --for deploy/web
kubectl -n shop logs deploy/web --tail=20 --timestamps
sudo ls /var/log/pods/ | head                                   # on a node
sudo tail -3 /var/log/pods/shop_web-*/nginx/0.log
```

```
2026-10-03T10:41:07.123456789Z stdout F 10.244.2.9 - - [03/Oct/2026:10:41:07 +0000] "GET / HTTP/1.1" 200 615 "-" "curl/8.5.0" "-"
```

→ On-disk format is CRI logging: timestamp, stream, `F` (full line) or `P` (partial), then the
message.

**Hands-on lab (test VM only)**

**Step 1 — save the evidence first.** Get into the habit:
`kubectl get events -A --sort-by=.lastTimestamp > events-$(date +%F-%H%M).txt` at the start of any
incident.

**Step 2 — break.** Crash a lab pod (for example the `loop` pod from area 5), delete it (lab pod
only), and try `kubectl logs` on it:
`Error from server (NotFound): pods "NAME" not found`. The logs went with the pod. On the node
the directory under `/var/log/pods` is removed too. Lesson: logs that matter must be shipped.

**Step 3 — find a node-level event.** Fill a worker's disk in a lab (`fallocate -l 20G /var/tmp/fill`
on a test VM, adjusted to its size) and watch for `EvictionThresholdMet` and `FreeDiskSpaceFailed`
events, then remove the file.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Events gone | `No resources found` an hour after the incident | save events early; ship them | [Observability](32-learn-performance-observability.md) |
| Logs gone with the pod | `pods "X" not found` | central logging | [Logs](06-logs-journal.md) |
| App logs to a file, not stdout | `kubectl logs` empty | log to stdout, or a sidecar that tails the file | area 5 |
| Huge single-line logs | rotation churn, disk pressure | node `du -sh /var/log/pods` | [Storage](01-storage-disk.md) |

**Why it matters for troubleshooting.** Events explain *Kubernetes'* decisions; logs explain the
*app's*. You need both, and you need them before they expire.

**Next step.** Resource usage: metrics-server and `kubectl top`.

### metrics-server and kubectl top

**Level:** [L2 · Mid] · CKA: Troubleshooting

**Concept.** **metrics-server** scrapes CPU and memory usage from every kubelet (`/metrics/resource`
on port 10250) every 15 s or so and serves the **Metrics API**. `kubectl top` and the HPA read
it. It keeps only the latest values (no history: that is Prometheus' job). On kubeadm clusters the
kubelet serving certificates are self-signed by default, so metrics-server refuses them unless you
either enable kubelet serving-certificate bootstrap (proper fix) or pass `--kubelet-insecure-tls`
(lab shortcut).

**Key terms**

| Command | Shows |
|---|---|
| `kubectl top nodes` | usage vs node capacity |
| `kubectl top pods -A --sort-by=memory` | heaviest pods |
| `kubectl top pod POD --containers` | per container |
| `kubectl get apiservice v1beta1.metrics.k8s.io` | is the Metrics API available? |

**See it on a real system**

```bash
kubectl top nodes
kubectl top pods -A --sort-by=cpu | head
kubectl get apiservice v1beta1.metrics.k8s.io
```

```
NAME   CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)
cp1    212m         10%      1630Mi          43%
w1     95m          4%       1124Mi          30%
w2     88m          4%       1040Mi          28%
```

→ Usage, not requests. Compare with `kubectl describe node` (requests): a node can be "full" for
the scheduler while `top` shows it nearly idle (area 12).

**Hands-on lab (test VM only)**

**Step 1 — install.** Apply the release manifest from the metrics-server project:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl -n kube-system get pods -l k8s-app=metrics-server
kubectl top nodes
```

**Step 2 — observe the break** you get on a default kubeadm cluster: the pod runs but is never
Ready, `kubectl top` says `error: Metrics API not available`, and its log shows:

```
"Failed to scrape node" err="Get \"https://192.168.56.11:10250/metrics/resource\": tls: failed to verify certificate: x509: cannot validate certificate for 192.168.56.11 because it doesn't contain any IP SANs" node="w1"
```

**Step 3 — fix (lab).** Add `--kubelet-insecure-tls` to the container args:

```bash
kubectl -n kube-system patch deploy metrics-server --type=json -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
kubectl -n kube-system rollout status deploy metrics-server
kubectl top nodes
```

The production fix is `serverTLSBootstrap: true` in every kubelet config, then approving the
kubelets' serving CSRs (`kubectl get csr`, `kubectl certificate approve NAME`), so metrics-server
can verify real certificates.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Kubelet certs not verifiable | `x509: cannot validate certificate ... doesn't contain any IP SANs` | `kubectl -n kube-system logs deploy/metrics-server` | this topic |
| metrics-server not installed | `error: Metrics API not available` | `kubectl get apiservice v1beta1.metrics.k8s.io` | — |
| Port 10250 blocked | scrape timeouts for one node | firewall on that node | area 3 |
| HPA `<unknown>` | no metrics or no requests | area 6 | area 6 |

**Why it matters for troubleshooting.** `kubectl top` answers "who is eating the node?" in one
second, the Kubernetes version of `top` from [CPU & performance](03-cpu-performance.md).

**Next step.** When the API itself cannot help: working on the node.

### On the node: crictl, kubelet and journalctl

**Level:** [L3 · Senior] · CKA: Troubleshooting

**Concept.** When a node is `NotReady`, or the API server is down, kubectl has nothing to tell you.
Then you SSH to the node and use systemd and CRI tools. The kubelet is a systemd unit with its
config in files; containerd is another unit; `crictl` shows what the runtime is actually running,
including control-plane containers.

**Key terms**

| Command or file | Purpose |
|---|---|
| `systemctl status kubelet containerd` | are the two services up? |
| `journalctl -u kubelet -b --since "10 min ago" --no-pager` | kubelet's view: errors talking to API, CRI, CNI, volumes |
| `systemctl cat kubelet` | unit plus drop-ins: where flags and env files come from |
| `/var/lib/kubelet/config.yaml` | KubeletConfiguration (cgroupDriver, staticPodPath, resolvConf, clientCAFile, eviction) |
| `/var/lib/kubelet/kubeadm-flags.env`, `/etc/default/kubelet` | extra flags (node-ip, runtime endpoint) |
| `/etc/kubernetes/kubelet.conf` | kubelet's kubeconfig (its client cert rotates in `/var/lib/kubelet/pki/`) |
| `crictl ps -a`, `crictl pods`, `crictl logs ID`, `crictl inspect ID`, `crictl images`, `crictl stats` | runtime view |

**See it on a real system**

```bash
systemctl status kubelet --no-pager | head -5
journalctl -u kubelet -b -p warning --no-pager | tail -20
systemctl cat kubelet
sudo grep -E 'cgroupDriver|staticPodPath|resolvConf|clientCAFile' /var/lib/kubelet/config.yaml
sudo crictl ps -a --name kube-apiserver
sudo crictl logs --tail 20 CONTAINER_ID
```

```
$ sudo crictl ps -a --name kube-apiserver
CONTAINER       IMAGE           CREATED          STATE     NAME             ATTEMPT   POD ID          POD
5c8d1e2f3a4b6   a1b2c3d4e5f60   20 seconds ago   Exited    kube-apiserver   7         9e8d7c6b5a4f3   kube-apiserver-cp1
```

→ ATTEMPT 7 and Exited: the API server keeps crashing. `crictl logs 5c8d1e2f3a4b6` shows why,
even though kubectl is dead.

**Hands-on lab (test VM only)**

**Step 1 — break the kubelet config** on w1 (keep a copy outside `/var/lib/kubelet` first):

```bash
sudo cp /var/lib/kubelet/config.yaml /root/kubelet-config.yaml.bak
sudo sed -i 's#clientCAFile: /etc/kubernetes/pki/ca.crt#clientCAFile: /etc/kubernetes/pki/ca-typo.crt#' /var/lib/kubelet/config.yaml
sudo systemctl restart kubelet
```

**Step 2 — diagnose from both sides.** On cp1: `kubectl get nodes` shows w1 `NotReady` after
about 50 s (the controller-manager's `--node-monitor-grace-period`, 40 s before v1.32);
`kubectl describe node w1` says `Kubelet stopped posting node status`. On w1:
`systemctl status kubelet` shows `activating (auto-restart)`, and the journal says:

```
E1003 10:52:14.331207   41822 run.go:72] "command failed" err="failed to construct kubelet dependencies: unable to load client CA file /etc/kubernetes/pki/ca-typo.crt: open /etc/kubernetes/pki/ca-typo.crt: no such file or directory"
```

**Step 3 — fix.** Restore the file and restart:
`sudo cp /root/kubelet-config.yaml.bak /var/lib/kubelet/config.yaml && sudo systemctl restart kubelet`.

**Step 4 — the simplest break of all.** `sudo systemctl stop kubelet` on w1: same NotReady, but
`systemctl status` shows `inactive (dead)`. On the exam, check `systemctl status kubelet` first and
`systemctl enable --now kubelet` if it was simply stopped or disabled.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| kubelet stopped/disabled | node NotReady; `Kubelet stopped posting node status` | `systemctl status kubelet` | [systemd](07-services-systemd.md) |
| Bad kubelet config or flag | kubelet in auto-restart loop; journal names the bad value | `journalctl -u kubelet -n 50 --no-pager` | [Logs](06-logs-journal.md) |
| Wrong kubelet binary path in unit | `status=203/EXEC` | `systemctl cat kubelet` and `which kubelet` | [systemd](07-services-systemd.md) |
| Runtime socket wrong | `validate service connection: ... connect: no such file or directory` | `crictl info`; `kubeadm-flags.env` | area 2 |
| Expired kubelet client cert | `Unauthorized` in kubelet log; node NotReady | `sudo openssl x509 -in /var/lib/kubelet/pki/kubelet-client-current.pem -noout -enddate` | area 19 |

**Why it matters for troubleshooting.** The CKA's "fix the broken node" tasks are mostly this
topic. It is the same method as any broken systemd service: status, journal, config file, fix,
restart, verify.

**Next step.** The control plane's own pods, and debugging containers that have no shell.

### Static pods and kubectl debug

**Level:** [L3 · Senior] · CKA: Troubleshooting

**Concept.** **Static pods** are defined by files in the kubelet's `staticPodPath`
(`/etc/kubernetes/manifests` on kubeadm). The kubelet runs them directly, without the API server,
which is how the control plane can start before the API exists. The kubelet also publishes a
read-only **mirror pod** (named `NAME-NODENAME`) so you can see it with kubectl. Deleting the
mirror pod does nothing lasting; editing the file restarts the pod. **kubectl debug** adds tools
where there are none: an **ephemeral container** inside a running pod (sharing its process and
network namespaces), a debug **copy** of a pod, or a privileged pod on a **node** with the host
filesystem at `/host`.

**Key terms**

| Command | Use |
|---|---|
| `kubectl debug -it POD --image=nicolaka/netshoot --target=CONTAINER` | tools inside a distroless/scratch pod |
| `kubectl debug POD -it --copy-to=POD-debug --container=CONTAINER -- sh` | a copy whose command you can change (crash loops) |
| `kubectl debug node/NODE -it --image=ubuntu` | shell on a node without SSH; host fs at `/host` |
| mirror pod | API reflection of a static pod; not editable via kubectl |

**See it on a real system**

```bash
sudo grep staticPodPath /var/lib/kubelet/config.yaml
sudo ls -la /etc/kubernetes/manifests/
kubectl -n kube-system get pods -o wide | grep -E -- '-cp1 '
kubectl -n kube-system get pod kube-apiserver-cp1 -o jsonpath='{.metadata.annotations.kubernetes\.io/config\.source}{"\n"}'   # "file" = static
```

**Hands-on lab (test VM only)**

**Step 1 — a static pod on w1.**

```bash
# on w1
cat <<'EOT' | sudo tee /etc/kubernetes/manifests/static-web.yaml
apiVersion: v1
kind: Pod
metadata:
  name: static-web
spec:
  containers:
  - name: web
    image: nginx:1.27
EOT
# on cp1
kubectl get pods -o wide | grep static-web          # static-web-w1 (default namespace)
```

Deleting the mirror pod is harmless and teaches the point: `kubectl delete pod static-web-w1`
returns, and the pod is back within seconds, because the file is the source of truth. To really
stop a static pod, move its file out of the directory (keep it somewhere safe, not in the same
directory):

```bash
sudo mv /etc/kubernetes/manifests/static-web.yaml /root/        # on w1: the pod disappears
```

**Step 2 — the backup-file trap.** Copy a manifest to `/etc/kubernetes/manifests/kube-scheduler.yaml.bak`
on cp1 and watch the kubelet log: it tries to run that file too (two pods with the same name
conflict). Always keep backups **outside** the manifests directory.

**Step 3 — debug a container that has no shell.** The `echo` pods from area 7 run `traefik/whoami`,
a scratch image.

```bash
kubectl -n shop exec deploy/echo -- sh
```

```
error: Internal error occurred: ... exec: "sh": executable file not found in $PATH
```

```bash
POD=$(kubectl -n shop get pods -l app=echo -o name | head -1)
kubectl -n shop debug -it "$POD" --image=nicolaka/netshoot --target=whoami -- ss -ltnp
kubectl debug node/w1 -it --image=ubuntu -- chroot /host journalctl -u kubelet -n 5 --no-pager
```

→ The ephemeral container shares the pod's network (and, with `--target`, its process namespace):
`ss` shows whoami listening on 8080. The node debug pod reads the node's journal without SSH.
Clean up the node debug pod afterwards (`kubectl get pods` shows `node-debugger-w1-...`).

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Bad YAML in a static manifest | control-plane pod disappears; kubelet log `Could not process manifest file` | `journalctl -u kubelet -g manifest --no-pager` on the node | area 20 |
| Edit via `kubectl edit` on a mirror pod | change rejected or lost | edit the file on the node | this topic |
| Backup file in manifests dir | duplicate or conflicting static pods | `ls -la /etc/kubernetes/manifests` | this topic |
| No shell in image | `executable file not found in $PATH` | `kubectl debug` | this topic |

**Why it matters for troubleshooting.** Control-plane failures on kubeadm are static-pod failures:
a typo in a file the kubelet reads. And "the image has no tools" is never a blocker again.

**Next step.** Keep the cluster healthy over time: maintenance (area 19).

---

## 19. Cluster maintenance

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Cluster Maintenance: OS upgrades, cluster upgrade, [Backup and Restore Methods](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Cluster-Maintenance/Backup-and-Restore-Methods); then Security for certificates ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 2) Note: [Packages](11-packages.md) (`apt-mark hold`, repository pinning) and [Time & NTP](12-time-ntp.md) (certificates and clock skew) · 3) Docs: the kubeadm upgrade, version-skew and certificate-management pages under [kubernetes.io/docs](https://kubernetes.io/docs/) · 4) Practice: one full upgrade per minor release on the homelab, and the etcd restore (drill 20) every month.

### cordon, drain, uncordon and PodDisruptionBudgets

**Level:** [L3 · Senior] · CKA: Cluster Architecture, Installation & Configuration

**Concept.** Before maintenance on a node (kernel update, reboot, kubelet upgrade) you move the
workloads away gracefully. **cordon** marks the node unschedulable (no new pods). **drain** cordons
and then *evicts* every pod through the Eviction API, which respects **PodDisruptionBudgets**
(PDBs): a PDB says "never voluntarily take this app below N available pods". **uncordon** makes the
node schedulable again; existing pods do not move back on their own.

**Key terms**

| Flag / object | Meaning |
|---|---|
| `--ignore-daemonsets` | DaemonSet pods cannot be evicted meaningfully (they would come straight back); skip them |
| `--delete-emptydir-data` | allow evicting pods with emptyDir volumes: **their emptyDir data is lost** |
| `--force` | also delete pods with no controller: **they are not recreated anywhere** |
| `--timeout=300s` | give up instead of waiting forever on a blocked eviction |
| `--disable-eviction` | delete instead of evict, bypassing PDBs: avoid |
| PDB `minAvailable` / `maxUnavailable` | the availability floor evictions must respect |

**See it on a real system**

```bash
kubectl get nodes                                  # SchedulingDisabled = cordoned
kubectl get pdb -A
kubectl get pods -A -o wide --field-selector spec.nodeName=w1
```

```
NAMESPACE   NAME      MIN AVAILABLE   MAX UNAVAILABLE   ALLOWED DISRUPTIONS   AGE
shop        web-pdb   2               N/A               0                     5m
```

→ ALLOWED DISRUPTIONS 0 means any drain touching these pods will wait (and retry) until more
replicas are available.

**Hands-on lab (test VM only)**

> Warning: `drain` evicts every non-DaemonSet pod on the node. On a real cluster, check spare
> capacity on the other nodes and list the PDBs first; `kubectl drain NODE --dry-run=client` shows
> what would be evicted without doing it.

**Step 1 — block a drain with a PDB.**

```bash
kubectl -n shop scale deploy web --replicas=2
kubectl -n shop create pdb web-pdb --selector=app=web --min-available=2
kubectl drain w1 --ignore-daemonsets --delete-emptydir-data --dry-run=client
kubectl drain w1 --ignore-daemonsets --delete-emptydir-data --timeout=60s
```

```
node/w1 cordoned
Warning: ignoring DaemonSet-managed Pods: calico-system/calico-node-x8r2d, kube-system/kube-proxy-tw9lc
evicting pod shop/web-5f6d4c8b9-a1b2c
error when evicting pods/"web-5f6d4c8b9-a1b2c" -n "shop" (will retry after 5s): Cannot evict pod as it would violate the pod's disruption budget.
```

**Step 2 — fix by adding capacity, not by bypassing the budget.**
`kubectl -n shop scale deploy web --replicas=3`; the drain completes once the third pod is Ready
elsewhere.

**Step 3 — finish maintenance.** `kubectl uncordon w1`, then `kubectl get nodes` (no more
`SchedulingDisabled`).

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| PDB with zero allowed disruptions | `Cannot evict pod as it would violate the pod's disruption budget` | `kubectl get pdb -A` | [26](26-playbook-containers-k8s.md) |
| Bare pods on the node | `cannot delete Pods declare no controller (use --force to override)` (kubectl's own wording) | decide: recreate them elsewhere first | this topic |
| emptyDir pods | `cannot delete Pods with local storage (use --delete-emptydir-data to override)` | confirm the data is disposable | area 11 |
| Forgot to uncordon | node `Ready,SchedulingDisabled` for days | `kubectl get nodes` | — |
| Not enough capacity elsewhere | evicted pods go Pending | `kubectl describe pod POD` (FailedScheduling) | area 12 |

**Why it matters for troubleshooting.** "Pods stuck Pending after maintenance" and "the drain hangs"
are both answered by `kubectl get nodes` and `kubectl get pdb -A`.

**Next step.** Upgrading Kubernetes itself.

### Upgrading a kubeadm cluster

**Level:** [L3 · Senior] · CKA: Cluster Architecture, Installation & Configuration

**Concept.** Upgrade **one minor version at a time** (1.33 → 1.34 → 1.35), **control plane
first**, then workers one by one. The version-skew policy allows kubelets to be older than the API
server (up to three minors) but never newer, which is why the order matters. On each node: upgrade
the `kubeadm` package, run `kubeadm upgrade` (apply on the first control plane, node on the
others), drain, upgrade `kubelet` and `kubectl` packages, restart the kubelet, uncordon.
`kubeadm upgrade apply` also renews the control-plane certificates. Take an etcd snapshot first
(next topic).

**Key terms**

| Step | Command |
|---|---|
| Point apt at the new minor | edit `/etc/apt/sources.list.d/kubernetes.list` (`v1.33` → `v1.34`) and its key if needed |
| See available patch versions | `apt-cache madison kubeadm` |
| Plan | `sudo kubeadm upgrade plan` |
| First control plane | `sudo kubeadm upgrade apply v1.34.X` |
| Other nodes | `sudo kubeadm upgrade node` |
| Unpin/pin packages | `apt-mark unhold` / `apt-mark hold` |

**See it on a real system**

```bash
kubectl get nodes                                   # VERSION column = kubelet versions
kubeadm version -o short
sudo kubeadm upgrade plan
```

```
Components that must be upgraded manually after you have upgraded the control plane with 'kubeadm upgrade apply':
COMPONENT   NODE   CURRENT   TARGET
kubelet     cp1    v1.33.5   v1.34.1
kubelet     w1     v1.33.5   v1.34.1
kubelet     w2     v1.33.5   v1.34.1

Upgrade to the latest stable version:

COMPONENT                 NODE   CURRENT    TARGET
kube-apiserver            cp1    v1.33.5    v1.34.1
kube-controller-manager   cp1    v1.33.5    v1.34.1
kube-scheduler            cp1    v1.33.5    v1.34.1
kube-proxy                       1.33.5     v1.34.1
CoreDNS                          v1.12.0    v1.12.1
etcd                      cp1    3.5.21-0   3.6.4-0

You can now apply the upgrade by executing the following command:

	kubeadm upgrade apply v1.34.1
```

**Hands-on lab (test VM only)** (build the lab one minor behind the latest, so you can practise;
take snapshots of all three VMs first)

**Step 1 — control plane (cp1).**

```bash
sudo sed -i 's#/v1.33/#/v1.34/#' /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
apt-cache madison kubeadm | head -3
sudo apt-mark unhold kubeadm
sudo apt-get install -y kubeadm='1.34.1-1.1'
sudo apt-mark hold kubeadm
kubeadm version -o short
sudo kubeadm upgrade plan
sudo kubeadm upgrade apply v1.34.1
kubectl drain cp1 --ignore-daemonsets
sudo apt-mark unhold kubelet kubectl
sudo apt-get install -y kubelet='1.34.1-1.1' kubectl='1.34.1-1.1'
sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload
sudo systemctl restart kubelet
kubectl uncordon cp1
```

**Step 2 — each worker** (drain from cp1, upgrade on the worker, uncordon from cp1).

```bash
kubectl drain w1 --ignore-daemonsets --delete-emptydir-data        # on cp1
# on w1: same repo change, then
sudo apt-mark unhold kubeadm kubelet kubectl
sudo apt-get install -y kubeadm='1.34.1-1.1'
sudo kubeadm upgrade node
sudo apt-get install -y kubelet='1.34.1-1.1' kubectl='1.34.1-1.1'
sudo apt-mark hold kubeadm kubelet kubectl
sudo systemctl daemon-reload && sudo systemctl restart kubelet
kubectl uncordon w1                                                # on cp1
```

**Step 3 — break.** Try to skip a minor: `sudo kubeadm upgrade apply v1.35.0` with kubeadm 1.35 on
a 1.33 cluster:
`Specified version to upgrade to "v1.35.0" is too high; kubeadm can upgrade only 1 minor version at a time`.
Also try installing the new kubeadm without changing the repo path: `apt-cache madison` shows only
old versions. Both are the most common "upgrade does not work" reasons.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Repo still on old minor | new version not found by apt | `cat /etc/apt/sources.list.d/kubernetes.list` | [Packages](11-packages.md) |
| Packages held | `kubeadm is already the newest version` or `held packages were changed` errors | `apt-mark showhold` | [Packages](11-packages.md) |
| Skipping a minor | `kubeadm can upgrade only 1 minor version at a time` | `kubeadm upgrade plan` | this topic |
| Kubelet upgraded, not restarted | node still shows old VERSION | `systemctl restart kubelet` | — |
| Worker newer than control plane | unsupported skew, odd failures | `kubectl get nodes` | — |

**Why it matters for troubleshooting.** Most upgrade incidents are package-management incidents.
And clusters that are never upgraded eventually hit certificate expiry (last topic of this area).

**Next step.** The backup that makes upgrades and mistakes survivable: etcd snapshots.

### etcd backup and restore

**Level:** [L3 · Senior] (exam) → [L4 · Lead/SRE] (owning tested restores) · CKA: Cluster Architecture, Installation & Configuration

**Concept.** etcd holds the entire cluster state: every object, Secret, RBAC rule. A **snapshot**
is a consistent point-in-time copy of it. Restoring rolls the **whole cluster's desired state**
back to that moment (workload data in volumes is not touched). etcd uses mutual TLS, so `etcdctl`
needs the endpoint plus three certificate paths, which you can read from the etcd static pod
manifest instead of memorising them. `etcdctl snapshot save` takes the backup; restoring and
inspecting snapshots is done with `etcdutl` in current etcd versions (`etcdctl snapshot restore` is
deprecated or removed, depending on the version).

**Key terms**

| Flag | Source in `/etc/kubernetes/manifests/etcd.yaml` |
|---|---|
| `--endpoints=https://127.0.0.1:2379` | `--listen-client-urls` |
| `--cacert=/etc/kubernetes/pki/etcd/ca.crt` | `--trusted-ca-file` |
| `--cert=/etc/kubernetes/pki/etcd/server.crt` | `--cert-file` |
| `--key=/etc/kubernetes/pki/etcd/server.key` | `--key-file` |
| `--data-dir` (restore) | a **new, empty** directory, e.g. `/var/lib/etcd-restore` |

**See it on a real system**

```bash
sudo grep -E 'listen-client-urls|trusted-ca-file|cert-file|key-file|data-dir' /etc/kubernetes/manifests/etcd.yaml
kubectl -n kube-system get pod etcd-cp1 -o jsonpath='{.spec.containers[0].image}{"\n"}'   # match etcdctl to this version
sudo ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key \
  endpoint health -w table
```

Get `etcdctl`/`etcdutl` from the etcd release matching the cluster's etcd image version (Ubuntu's
`etcd-client` package is often older), or run them inside the etcd pod
(`kubectl -n kube-system exec etcd-cp1 -- etcdctl ...`), whose image ships them.

**Hands-on lab (test VM only)**

**Step 1 — save and verify a snapshot.**

```bash
sudo mkdir -p /var/backups/etcd
sudo ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /var/backups/etcd/snap-$(date +%F-%H%M).db
sudo etcdutl snapshot status /var/backups/etcd/snap-*.db -w table
```

```
+----------+----------+------------+------------+
|   HASH   | REVISION | TOTAL KEYS | TOTAL SIZE |
+----------+----------+------------+------------+
| 7c3f2a1b |   482113 |       1342 |     8.4 MB |
+----------+----------+------------+------------+
```

**Step 2 — change something after the backup.** `kubectl create namespace after-backup`.

**Step 3 — restore.**

> Warning: a restore replaces the cluster's entire state with the snapshot. Everything created
> after it (deployments, secrets, RBAC changes) disappears, and objects deleted after it come back.
> Take a fresh snapshot of the current state and a VM snapshot before you start, and stop the API
> server so nothing writes during the restore.

```bash
sudo mkdir -p /root/manifests-off
sudo mv /etc/kubernetes/manifests/kube-apiserver.yaml /root/manifests-off/      # stop writers
sudo etcdutl snapshot restore /var/backups/etcd/snap-YYYY-MM-DD-HHMM.db --data-dir /var/lib/etcd-restore
sudo cp /etc/kubernetes/manifests/etcd.yaml /root/manifests-off/etcd.yaml.orig
sudo sed -i 's#path: /var/lib/etcd$#path: /var/lib/etcd-restore#' /etc/kubernetes/manifests/etcd.yaml   # hostPath of the etcd-data volume
sudo grep -n -B3 'name: etcd-data' /etc/kubernetes/manifests/etcd.yaml           # verify only the hostPath changed
sudo crictl ps --name etcd                                                        # wait for a new etcd container
sudo mv /root/manifests-off/kube-apiserver.yaml /etc/kubernetes/manifests/
sudo systemctl restart kubelet
kubectl get ns | grep after-backup || echo "after-backup is gone: restore worked"
```

→ Only the volume's `hostPath` changes; the `--data-dir` flag inside the container stays
`/var/lib/etcd`. Restarting the scheduler and controller-manager (move their manifests out and back)
is also recommended so no component keeps a stale cache.

**Step 4 — break.** Run `snapshot save` without `--cacert/--cert/--key`. After a few seconds:
`Error: context deadline exceeded`. etcd's TLS handshake failed; the error does not say so. Always
suspect the certificate flags first.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Missing or wrong cert flags | `Error: context deadline exceeded` | compare flags with `etcd.yaml` | this topic |
| Restoring into the existing data dir | `Error: data-dir "/var/lib/etcd" not empty or could not be read` (older etcdctl: `data-dir "/var/lib/etcd" exists`) | restore to a new directory | this topic |
| Manifest edited wrongly | etcd does not start, API server crashes (`connection refused` to 2379) | `sudo crictl ps -a --name etcd`; `crictl logs` | area 20 |
| Backups never tested | restore fails during an incident | restore drill monthly | [SRE](33-learn-cicd-iac-sre.md) |
| Backups unencrypted | Secrets readable from backup files | encrypt and restrict backups | area 10 |

**Why it matters for troubleshooting.** An untested backup is a hope, not a backup. A restore drill
on the homelab is also one of the most valuable exam and interview stories you can have.

**Next step.** The time bomb in every kubeadm cluster: certificate expiry.

### Certificates: expiry and renewal

**Level:** [L3 · Senior] → [L4 · Lead/SRE] (expiry monitoring) · CKA: Cluster Architecture, Troubleshooting

**Concept.** kubeadm issues component certificates valid for **one year** and CAs valid for ten.
If nobody upgrades the cluster for a year, the API server, scheduler, controller-manager and
`admin.conf` certificates expire together and the cluster stops answering. `kubeadm upgrade`
renews them as a side effect; otherwise run `kubeadm certs renew` and restart the control-plane
static pods (they do not reload certificates on their own). The kubelet's client certificate
rotates automatically.

**Key terms**

| Command or file | Purpose |
|---|---|
| `sudo kubeadm certs check-expiration` | expiry of every kubeadm-managed cert and CA |
| `sudo kubeadm certs renew all` | renew all (or name one: `apiserver`, `admin.conf`...) |
| `/etc/kubernetes/pki/` | certificates and keys |
| `/var/lib/kubelet/pki/kubelet-client-current.pem` | kubelet client cert (auto-rotated) |
| `openssl x509 -in FILE -noout -subject -enddate -ext subjectAltName` | inspect any cert |

**See it on a real system**

```bash
sudo kubeadm certs check-expiration
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -enddate -ext subjectAltName
```

```
CERTIFICATE                EXPIRES                  RESIDUAL TIME   CERTIFICATE AUTHORITY   EXTERNALLY MANAGED
admin.conf                 Sep 21, 2027 09:14 UTC   352d            ca                      no
apiserver                  Sep 21, 2027 09:14 UTC   352d            ca                      no
apiserver-etcd-client      Sep 21, 2027 09:14 UTC   352d            etcd-ca                 no
apiserver-kubelet-client   Sep 21, 2027 09:14 UTC   352d            ca                      no
controller-manager.conf    Sep 21, 2027 09:14 UTC   352d            ca                      no
etcd-healthcheck-client    Sep 21, 2027 09:14 UTC   352d            etcd-ca                 no
etcd-peer                  Sep 21, 2027 09:14 UTC   352d            etcd-ca                 no
etcd-server                Sep 21, 2027 09:14 UTC   352d            etcd-ca                 no
front-proxy-client         Sep 21, 2027 09:14 UTC   352d            front-proxy-ca          no
scheduler.conf             Sep 21, 2027 09:14 UTC   352d            ca                      no
super-admin.conf           Sep 21, 2027 09:14 UTC   352d            ca                      no

CERTIFICATE AUTHORITY   EXPIRES                  RESIDUAL TIME   EXTERNALLY MANAGED
ca                      Sep 19, 2036 09:14 UTC   9y              no
etcd-ca                 Sep 19, 2036 09:14 UTC   9y              no
front-proxy-ca          Sep 19, 2036 09:14 UTC   9y              no
```

**Hands-on lab (test VM only)**

**Step 1 — renew and restart.**

```bash
sudo kubeadm certs renew all
sudo mkdir -p /root/manifests-off
sudo mv /etc/kubernetes/manifests/*.yaml /root/manifests-off/
sleep 20                                                          # kubelet stops the static pods
sudo mv /root/manifests-off/*.yaml /etc/kubernetes/manifests/
sudo crictl ps | grep -E 'kube-apiserver|etcd|scheduler|controller'
sudo cp /etc/kubernetes/admin.conf "$HOME/.kube/config"           # your kubeconfig embeds the renewed admin cert
sudo kubeadm certs check-expiration | head -4
```

**Step 2 — see expiry without waiting a year (advanced; VM snapshots of all nodes first).** Disable
NTP and move the clock 13 months forward on all three VMs
(`sudo timedatectl set-ntp false && sudo date -s '+13 months'`). kubectl now fails with
`x509: certificate has expired or is not yet valid: current time ... is after ...`, and nodes go
NotReady. Do **not** renew in this state (certs issued in the "future" break when time returns);
revert the VM snapshots instead.

**How it breaks**

| Failure | Symptom / error text | First command | Playbook |
|---|---|---|---|
| Control-plane certs expired | `x509: certificate has expired or is not yet valid` from kubectl | `sudo kubeadm certs check-expiration` | [TLS](18-web-http-tls.md) |
| Renewed but not restarted | still expired errors | restart static pods (Step 1) | this topic |
| Old kubeconfig after renewal | `Unauthorized` or x509 for your user only | copy the new `admin.conf` | area 4 |
| Node clock wrong | `not yet valid` on one node | `timedatectl` | [Time](12-time-ntp.md) |
| API cert lacks a name or IP | `x509: certificate is valid for ..., not ...` | `openssl x509 -ext subjectAltName` | area 3 |

**Why it matters for troubleshooting.** "Cluster dead on the anniversary of its install" is a
classic outage. A monthly `check-expiration` (or an alert on it) prevents it entirely.

**Next step.** Put all areas together into one method (area 20).

---

## 20. The troubleshooting method

> 📚 **Study path:** 1) Note: [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) and the layered walk in [Site down](25-playbook-site-down.md) · 2) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Troubleshooting: [Troubleshooting Section Introduction](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Troubleshooting-Section-Introduction), [Application Failure](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Application-Failure), [Control Plane Failure](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Troubleshooting/Control-Plane-Failure/page), [Worker Node Failure](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Worker-Node-Failure), Network Troubleshooting ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) · 3) Read: learnkube [Troubleshooting deployments](https://learnkube.com/troubleshooting-deployments) (the flowchart) and real postmortems on [k8s.af](https://k8s.af/) · 4) Practice: *Kubernetes Challenges* (free, [course](https://kodekloud.com/courses/kubernetes-challenges)) and the drills in area 22.

### The bottom-up flowchart

**Level:** [L2 · Mid] · CKA: Troubleshooting

**Concept.** Work **bottom-up**: first make sure you can talk to the cluster, then check the pods,
then the Service in front of them, then the Ingress/Gateway, and only then the nodes and the
control plane in depth. Each layer depends on the one below, so a fix at a lower layer often fixes
everything above it. The same idea as the layered walk in your
[Site down playbook](25-playbook-site-down.md) and the learnkube
[troubleshooting flowchart](https://learnkube.com/troubleshooting-deployments).

```
 START: kubectl get nodes
   |
   +-- error (refused / timeout / x509 / Unauthorized)? ---> CONTROL PLANE & ACCESS (layer 5)
   |                                                          kubeconfig? apiserver/etcd static pods? certs?
   v
 kubectl get pods -n NS -o wide
   |
   +-- Pending ----------------> describe pod: FailedScheduling? (resources, taints, affinity, PVC)
   |                             no events at all? -> scheduler down (layer 5)
   +-- ContainerCreating ------> describe pod: FailedMount? FailedCreatePodSandBox (CNI)? (layer 4)
   +-- ErrImagePull/BackOff ---> describe pod; crictl pull on the node (name, auth, CA, DNS)
   +-- CreateContainerConfigError -> missing ConfigMap/Secret/key
   +-- CrashLoopBackOff -------> logs --previous; Last State exit code; probes; OOM
   +-- Running, READY 0/1 -----> readiness probe failing (describe pod)
   +-- no pods at all ---------> describe deploy/rs: quota, admission, SA; controller-manager (layer 5)
   |
   v  pods Running and Ready
 kubectl port-forward pod/POD 8080:CONTAINER_PORT  -> works?  no -> app itself (listening addr/port)
   |
   v
 SERVICE: get endpointslices -l kubernetes.io/service-name=SVC
   +-- empty / not ready ------> empty: selector vs pod labels; listed but not ready: readiness
   +-- has endpoints, fails ---> targetPort vs containerPort; kube-proxy on that node; NetworkPolicy
   +-- name fails, IP works ---> DNS (CoreDNS pods, Corefile, namespace in the name, NetworkPolicy on 53)
   |
   v
 INGRESS / GATEWAY: describe ingress/httproute; controller logs; curl -H Host / --resolve
   +-- 404 --------------------> class, host, path, route status (Accepted/ResolvedRefs)
   +-- 502/503 ----------------> backend Service/port/endpoints
   +-- wrong cert -------------> TLS secret name/namespace
   |
   v
 NODES (layer 4): get nodes; describe node (Conditions, Allocated); on node: kubelet, containerd, disk, CNI
```

**Key terms**

| Layer | Question | Fastest evidence |
|---|---|---|
| 5 access/control plane | can I talk to a healthy API? | `kubectl get nodes`; on cp1 `crictl ps -a` |
| 1 pods | are the containers running and Ready? | `kubectl get pods`, `describe`, `logs --previous` |
| 2 Service + DNS | does the name lead to Ready endpoints? | `get endpointslices`, debug pod `curl`/`dig` |
| 3 ingress | does the edge route this host/path? | controller logs, `curl -H 'Host: ...'` |
| 4 nodes | are nodes healthy and do they have room? | `describe node`, kubelet journal |

**See it on a real system**

```bash
kubectl get nodes
kubectl get pods -A | grep -vE 'Running|Completed'
kubectl get events -A --field-selector type=Warning --sort-by=.lastTimestamp | tail -20
```

**Hands-on lab (test VM only)**

**Step 1 — have someone (or a script) break one thing** from the drills in area 22 without telling
you what.

**Step 2 — walk the flowchart out loud** and write down, for each layer, the command and the
evidence that cleared it, before moving up or down.

**Step 3 — fix, verify from the user's point of view** (`curl` through the ingress), and write the
five-line note.

**How it breaks.** The method fails in predictable ways: starting at the top (reading app code
while a node is NotReady), changing two things at once, and not verifying from the user's side.

**Why it matters for troubleshooting.** A fixed order turns panic into a checklist, and makes your
reasoning easy for others to follow during an incident.

**Next step.** The commands for each layer, collected.

### Layer by layer: commands and what good looks like

**Level:** [L2 · Mid] · CKA: Troubleshooting

**Concept.** For each layer, a handful of commands and the output that means "this layer is fine,
move on". Learn to recognise "good" quickly; most time is lost staring at healthy layers.

**Key terms**

| Layer | Commands | Good looks like |
|---|---|---|
| Access | `kubectl config current-context`; `kubectl auth whoami` | right cluster, right identity |
| Control plane | `kubectl -n kube-system get pods`; `kubectl get --raw='/readyz?verbose'` | all Running, 0 recent restarts; `readyz check passed` |
| Nodes | `kubectl get nodes -o wide`; `kubectl describe node NODE` | all Ready; no Pressure conditions; same versions |
| Workload | `kubectl -n NS get deploy,rs,pods -o wide` | READY n/n, UP-TO-DATE = replicas |
| Pod detail | `kubectl -n NS describe pod POD`; `logs --previous` | no Warning events; Restart Count stable |
| Service | `kubectl -n NS get svc,endpointslices` | endpoints = Ready pod IPs on targetPort |
| DNS | `kubectl -n NS run t --rm -it --restart=Never --image=nicolaka/netshoot -- dig +search SVC` | answer = ClusterIP |
| In-cluster HTTP | same pod: `curl -sv http://SVC.NS:PORT/` | expected status code |
| Edge | `curl -v -H 'Host: DOMAIN' http://NODE_IP:NODEPORT/` | expected status, right backend |
| TLS | `openssl s_client -connect HOST:PORT -servername DOMAIN` | right certificate and chain |

**See it on a real system.** Run the whole table once on a healthy cluster and keep the outputs
as your "known good" reference. Comparing with known-good output is faster than reasoning.

**Hands-on lab (test VM only)**

**Step 1 — time yourself** running the full table against one app: target under five minutes.

**Step 2 — break the readiness probe** of that app (area 5) and run the table again: note at
which row the first deviation from "good" appears (Workload: READY 0/n).

**How it breaks.** Skipping rows because "that cannot be it". The row you skip is the broken one
more often than you would think.

**Why it matters for troubleshooting.** This table is what you will paste into the
[playbook](26-playbook-containers-k8s.md) runbooks and use under pressure.

**Next step.** Recognise control-plane failures by their fingerprints.

### Control-plane failure signatures

**Level:** [L3 · Senior] · CKA: Troubleshooting

**Concept.** On kubeadm clusters the CKA's "the cluster is broken" tasks are nearly always one of a
few breakages of a static pod manifest or of the kubelet. Each component has a recognisable
fingerprint in kubectl, and the evidence is always on the node (`crictl ps -a`, `crictl logs`,
`journalctl -u kubelet`, the manifest file).

**Key terms**

| Broken component | Fingerprint in kubectl | Where the evidence is | Typical break |
|---|---|---|---|
| kube-apiserver | every command: `connection refused` on 6443 | `crictl ps -a --name kube-apiserver`; `crictl logs ID`; `/var/log/pods/kube-system_kube-apiserver-*` | wrong flag value, wrong cert path, wrong `--etcd-servers` port, bad YAML |
| etcd | API server restarting; its log shows connection errors to 2379 | `crictl logs` of etcd | wrong data-dir or cert path |
| kube-scheduler | new pods Pending, **no events** | `kubectl -n kube-system get pods`; scheduler logs | wrong `--kubeconfig` path, wrong image tag, bad command name |
| kube-controller-manager | Deployment created but no RS/pods; scaling ignored; no new Job pods | controller-manager logs | wrong flag or kubeconfig path, wrong image |
| kubelet on a node | node `NotReady`, `Kubelet stopped posting node status` | `systemctl status kubelet`; `journalctl -u kubelet` | service stopped/disabled, bad config path, wrong CA file |
| containerd on a node | node NotReady, CRI socket errors in kubelet journal | `systemctl status containerd` | stopped, bad config.toml |
| CNI | node NotReady (`cni plugin not initialized`) or pods stuck `ContainerCreating` | CNI pods in kube-system/calico-system; `/etc/cni/net.d` | CNI DaemonSet broken, config removed |
| CoreDNS | name lookups fail cluster-wide | `kubectl -n kube-system logs -l k8s-app=kube-dns` | scaled to 0, Corefile typo, loop |
| kube-proxy | new Services fail, old ones work | kube-proxy pods and logs | DaemonSet broken, ConfigMap typo |

**See it on a real system**

```bash
# on cp1, when kubectl is dead
sudo crictl ps -a | grep -E 'kube-apiserver|etcd|scheduler|controller'
sudo crictl logs --tail 30 "$(sudo crictl ps -a --name kube-apiserver -q | head -1)"
sudo ls -t /var/log/pods/ | head
journalctl -u kubelet --since '5 min ago' --no-pager | grep -iE 'error|failed' | tail -20
```

```
E1003 11:04:52.118207       1 run.go:72] "command failed" err="open /etc/kubernetes/pki/apiserver-typo.crt: no such file or directory"
```

**Hands-on lab (test VM only)** (snapshot cp1 first; break one thing at a time; always keep a copy
of the manifest outside `/etc/kubernetes/manifests`)

**Step 1 — break the API server's etcd address.**

```bash
sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml /root/kube-apiserver.yaml.good
sudo sed -i 's#--etcd-servers=https://127.0.0.1:2379#--etcd-servers=https://127.0.0.1:2380#' /etc/kubernetes/manifests/kube-apiserver.yaml
kubectl get nodes        # after ~30 s: connection refused
```

**Step 2 — diagnose without kubectl.** `crictl ps -a --name kube-apiserver` shows it exiting
repeatedly; `crictl logs` on the latest attempt shows it failing to reach etcd at :2380 (the peer
port). Compare the flag with etcd's `--listen-client-urls` in `etcd.yaml`.

**Step 3 — fix** by restoring the good copy:
`sudo cp /root/kube-apiserver.yaml.good /etc/kubernetes/manifests/kube-apiserver.yaml`, then wait
for `kubectl get nodes` to answer.

**Step 4 — repeat** with: a wrong image tag in `kube-scheduler.yaml`, a wrong `--kubeconfig` path
in `kube-controller-manager.yaml`, and invalid YAML indentation in `kube-apiserver.yaml` (here
`crictl` shows *nothing*, because the kubelet cannot parse the file: the evidence is in the kubelet
journal).

**How it breaks.** See the table above. One more trap: after fixing a manifest, the old container
may keep restarting for a while; wait for the kubelet to pick up the change (up to a minute) before
assuming your fix failed.

**Why it matters for troubleshooting.** Troubleshooting is the heaviest CKA domain, and these
fingerprints answer most of its cluster-level tasks within a couple of minutes.

**Next step.** The error-message decoder for everyday incidents.

### Error message decoder

**Level:** [L2 · Mid] · CKA: Troubleshooting

**Concept.** Kubernetes error messages are long but precise. Search this table by the most
distinctive phrase in the error you are looking at.

**Key terms (the decoder)**

| Error text (distinctive part) | Layer | Meaning | First command |
|---|---|---|---|
| `The connection to the server ... was refused` | access / control plane | API server down, wrong address/port | `kubectl config view --minify`; on cp1 `crictl ps -a` |
| `x509: certificate signed by unknown authority` | access or registry | wrong CA in kubeconfig, or private registry CA not trusted on the node | area 4 or area 17 |
| `x509: certificate has expired or is not yet valid` | access / certs | expired certs or clock skew | `kubeadm certs check-expiration`; `timedatectl` |
| `You must be logged in to the server (Unauthorized)` | authn | bad or expired credentials/token | `kubectl auth whoami` |
| `is forbidden: User "X" cannot VERB resource "R"` | RBAC | missing permission | `kubectl auth can-i VERB R --as X -n NS` |
| `exceeded quota` | admission | ResourceQuota full | `kubectl describe quota -n NS` |
| `0/3 nodes are available: ... Insufficient cpu` | scheduler | requests too large | `kubectl describe node` (Allocated) |
| `had untolerated taint` | scheduler | taint without toleration | `kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints` |
| `didn't match Pod's node affinity/selector` | scheduler | label rules unsatisfied | `kubectl get nodes --show-labels` |
| `pod has unbound immediate PersistentVolumeClaims` | storage | PVC Pending | `kubectl describe pvc` |
| `Multi-Attach error for volume` | storage | RWO volume still attached elsewhere | `kubectl get pods -o wide` |
| `MountVolume.SetUp failed ... not found` | kubelet / config | missing ConfigMap/Secret/volume source | `kubectl describe pod POD` |
| `FailedCreatePodSandBox ... failed to setup network for sandbox` | CNI | CNI broken on that node | CNI pods on the node |
| `ErrImagePull` / `ImagePullBackOff` + `not found` | registry | wrong image or tag | check the registry |
| `... 401 Unauthorized` (pull) | registry auth | imagePullSecret wrong/missing | decode secret; `crictl pull --creds` |
| `CreateContainerConfigError` | config | missing ConfigMap/Secret key | `kubectl describe pod POD` |
| `exec: "X": executable file not found in $PATH` | container | wrong command or no shell in image | check command; `kubectl debug` |
| `CrashLoopBackOff` + exit 137 + `OOMKilled` | resources | memory limit hit | `kubectl describe pod` Last State |
| `Liveness probe failed` / `Readiness probe failed` | probes | wrong path/port/timeout or sick app | `kubectl describe pod POD` |
| `Cannot evict pod as it would violate the pod's disruption budget` | maintenance | PDB blocks drain | `kubectl get pdb -A` |
| `no servers could be reached` (DNS) | DNS | CoreDNS down or port 53 blocked | CoreDNS pods; NetworkPolicies |
| `plugin/loop: Loop ... detected` | DNS | CoreDNS forwards to itself | kubelet `resolvConf` |
| `bind: address already in use` | node / ports | hostNetwork/hostPort clash with a host service | `sudo ss -ltnp 'sport = :PORT'` on the node |
| `Error: context deadline exceeded` (etcdctl, helm) | tooling | TLS/endpoint wrong (etcdctl) or wait timeout (helm) | flags; `helm history` |
| `another operation (install/upgrade/rollback) is in progress` | Helm | release stuck pending | `helm history`, `helm rollback` |

**See it on a real system / Hands-on lab / How it breaks.** Use the drills in area 22: for each
drill, find the matching row here *before* you start fixing.

**Why it matters for troubleshooting.** Matching the exact error text to a layer is the fastest
way to skip straight to the right command, the same idea as the case library in your Ops Ladder
and the [Containers & Kubernetes playbook](26-playbook-containers-k8s.md).

**Next step.** Watch the whole method run on one realistic incident, step by step (next topic).

### Worked example: app.example.com returns 404

**Level:** [L2 · Mid] · CKA: Troubleshooting

**Concept.** This is the bottom-up method from the first topic of this area, written in the
playbook step format the rest of the handbook uses: goal, commands, sample output, what it means,
why this step comes now, and where to go next. The incident: after a quiet morning, users report
that `https://app.example.com` shows `404 page not found`. Nobody "deployed" anything. The cluster
is the lab cluster: Traefik from area 16 as NodePort 31080/31443, Ingress `shop` sending
`app.example.com` to Service `web` in namespace `shop`.

**Key terms**

| Term | Why it matters in this incident |
|---|---|
| Edge test with a Host header | proves the controller answers, without DNS or the browser in the way |
| Skipped backend | Traefik's default: an Ingress backend with no ready endpoints gets no router, so users see 404, not 503 |
| EndpointSlice | the single source of truth for which pods a Service sends traffic to |
| managedFields | who last changed an object, with which tool, and when |

#### Step 1 — Confirm where you are

**Goal:** prove you are on the right cluster and that nodes and the control plane are healthy.

```bash
kubectl config current-context
kubectl get nodes
kubectl -n kube-system get pods | grep -vE 'Running|Completed'
```

```
kubernetes-admin@kubernetes
NAME   STATUS   ROLES           AGE   VERSION
cp1    Ready    control-plane   34d   v1.34.1
w1     Ready    worker          34d   v1.34.1
w2     Ready    worker          34d   v1.34.1
NAME   READY   STATUS   RESTARTS   AGE
```

**What it means:** the right context, all nodes `Ready`, and the last command printed only the
header, so no kube-system pod is unhealthy. Layer 5 (access and control plane) and layer 4
(nodes) are fine for now.

**Why this step (now):** it costs ten seconds and rules out the two most expensive mistakes:
debugging the wrong cluster, and chasing an app symptom while a node or the API server is the real
problem. Every later command trusts this one.

**Next step:** all healthy → Step 2. Connection refused, x509 or Unauthorized → the
control-plane failure signatures earlier in this area. A node `NotReady` → the node topic in
area 18, before anything else.

#### Step 2 — Reproduce the symptom at the edge

**Goal:** see the user's error yourself, bypassing DNS and the browser.

```bash
curl -sv -H 'Host: app.example.com' http://192.168.56.11:31080/ 2>&1 | sed -n '1,4p;/^< HTTP/p;/page not found/p'
curl -sk --resolve app.example.com:31443:192.168.56.11 -o /dev/null -w '%{http_code}\n' https://app.example.com:31443/
```

```
*   Trying 192.168.56.11:31080...
* Connected to 192.168.56.11 (192.168.56.11) port 31080
> GET / HTTP/1.1
> Host: app.example.com
< HTTP/1.1 404 Not Found
404 page not found
404
```

**What it means:** the TCP connection to the NodePort works and an HTTP server answered, so DNS,
routing, the node firewall and the controller pod are fine. `404 page not found` is Traefik's own
body: it has **no router** for this host. Both HTTP and HTTPS agree.

**Why this step (now):** it splits the problem in half. A timeout would point down (NodePort,
firewall, kube-proxy); a 502 or 503 would point at the backend; a 404 from the controller points
at routing: the Ingress itself, or a backend the controller refused to use.

**Next step:** 404 → Step 3. Timeout or refused → check the controller Service and the node
firewall (areas 7 and 3). 502/503 → skip to Step 4 (backend). 200 here but users still fail →
DNS or the outer load balancer, outside the cluster ([Site down](25-playbook-site-down.md)).

#### Step 3 — Ask the controller why it has no route

**Goal:** confirm the Ingress is adopted, then read the controller's own explanation.

```bash
kubectl -n shop get ingress shop
kubectl -n traefik logs deploy/traefik --since=2h | grep -i 'namespace=shop' | tail -3
```

```
NAME   CLASS     HOSTS             ADDRESS         PORTS     AGE
shop   traefik   app.example.com   192.168.56.11   80, 443   34d

2026-10-03T08:41:17Z ERR Skipping service: no endpoints found ingress=shop namespace=shop providerName=kubernetes serviceName=web servicePort=&ServiceBackendPort{Name:,Number:80,}
```

**What it means:** class `traefik` and a filled ADDRESS mean Traefik adopted the Ingress. The log
says why the route is missing: Service `web` has **no endpoints**, so Traefik skipped it (the
exact wording varies between Traefik versions). The first error is at 08:41:17, which gives you a
time to correlate with changes. (With Traefik's `allowEmptyServices` option enabled you would get
503 instead of 404; the cause would be the same.)

**Why this step (now):** the controller has already done the diagnosis for you. Reading its log
costs one command and tells you whether to look at the Ingress (class, host, TLS) or behind it.

**Next step:** "no endpoints" or "service not found" → Step 4. Nothing logged for `shop` and
ADDRESS empty → wrong `ingressClassName` (area 8, drill 10). Errors about a TLS secret → the TLS
rows in area 8.

#### Step 4 — Read the Service and its EndpointSlice

**Goal:** see which pods the Service selects, and whether any are Ready.

```bash
kubectl -n shop get svc web -o wide
kubectl -n shop get endpointslices -l kubernetes.io/service-name=web
```

```
NAME   TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE   SELECTOR
web    ClusterIP   10.96.120.15   <none>        80/TCP    34d   app=web-frontend

NAME        ADDRESSTYPE   PORTS     ENDPOINTS   AGE
web-7xk2p   IPv4          <unset>   <unset>     34d
```

**What it means:** the slice is empty, so the selector matches no running pod. (Pods that match but
are not Ready would still be listed, with `ready: false` in `-o yaml`, and would get no traffic.)
The selector `app=web-frontend` looks unfamiliar: the Deployment was created with `app=web`.

**Why this step (now):** the EndpointSlice is the meeting point of the Service layer and the pod
layer. One command tells you whether to look at labels or at pod health, so you do not debug both.

**Next step:** empty slice → Step 5 to compare selector and pods. Endpoints listed but traffic
still fails → targetPort versus containerPort (area 7, drill 7) or a NetworkPolicy (area 15).

#### Step 5 — Compare selector and pod labels, find the change

**Goal:** prove the selector mismatch and find out who changed what, and when.

```bash
kubectl -n shop get pods -l app=web -o wide
kubectl -n shop get pods -l app=web-frontend
kubectl -n shop get svc web -o yaml --show-managed-fields | grep -E 'manager:|time:'
```

```
NAME                  READY   STATUS    RESTARTS   AGE   IP            NODE   NOMINATED NODE   READINESS GATES
web-5f6d4c8b9-a1b2c   1/1     Running   0          2d    10.244.1.21   w1     <none>           <none>
web-5f6d4c8b9-d3e4f   1/1     Running   0          2d    10.244.2.14   w2     <none>           <none>
No resources found in shop namespace.
    manager: kubectl-client-side-apply
    time: "2026-08-30T10:02:11Z"
    manager: kubectl-edit
    time: "2026-10-03T08:40:55Z"
```

**What it means:** the pods are healthy and Ready with label `app=web`; nothing carries
`app=web-frontend`. The Service was last changed by `kubectl edit` at 08:40:55, 22 seconds before
Traefik's first error. That is the root cause with evidence: a live edit of the Service selector,
outside Git.

**Why this step (now):** you fix causes, not symptoms. Without the "who and when", you would fix
the selector and the person who edited it would do it again tomorrow; with it, you can ask them
what they were trying to do (perhaps a planned relabelling that was only half done).

**Next step:** mismatch confirmed → Step 6. Pods with the right label but `0/1` → readiness probe
(area 5, drill 8). No pods at all → the Deployment and ReplicaSet (area 6, drills 5 and 15).

#### Step 6 — Fix through Git, then verify from the user's side

**Goal:** restore the desired state from the source of truth and prove the site works.

```bash
cd ~/k8s-manifests && git log --oneline -2 -- shop/service.yaml
kubectl diff -f shop/service.yaml                     # what apply will change
kubectl apply -f shop/service.yaml
kubectl -n shop get endpointslices -l kubernetes.io/service-name=web
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: app.example.com' http://192.168.56.11:31080/
```

```
3e1a9c2 shop: web service, selector app=web
diff -u -N /tmp/LIVE-2861750412/v1.Service.shop.web /tmp/MERGED-1093847562/v1.Service.shop.web
...
   selector:
-    app: web-frontend
+    app: web
...
service/web configured
NAME        ADDRESSTYPE   PORTS   ENDPOINTS                 AGE
web-7xk2p   IPv4          80      10.244.1.21,10.244.2.14   34d
200
```

**What it means:** Git still holds the correct selector, `kubectl diff` shows exactly one changed
line, the slice now lists both pod IPs, and the edge returns 200 within a few seconds as Traefik
rebuilds its router.

**Why this step (now):** applying from Git (instead of a second `kubectl edit`) fixes the cause and
removes the drift in one move, and `kubectl diff` makes sure you change nothing else. Verifying
through the edge, not with `kubectl get`, is what proves the user's symptom is gone.

**Next step:** 200 → write the five-line note and the prevention items below. Still 404 → back to
Step 3 and read the controller log again (a second Service or a TLS issue). Different error →
restart the walk at Step 2 with the new symptom.

**Decision tree**

```
app.example.com 404
  |
  +-- Step 1: context, nodes, kube-system healthy? -- no --> control plane / node first
  |
  +-- Step 2: curl -H Host to NodePort
  |      timeout ---------> NodePort, firewall, kube-proxy
  |      502/503 ---------> backend (Step 4)
  |      404 -------------> Step 3
  |
  +-- Step 3: ingress ADDRESS + controller log
  |      ADDRESS empty ---> ingressClassName
  |      "no endpoints" --> Step 4
  |
  +-- Step 4: EndpointSlice
  |      empty -----------> Step 5
  |      has endpoints ---> targetPort / NetworkPolicy
  |
  +-- Step 5: selector vs pod labels; managedFields
  |      mismatch --------> Step 6 (fix from Git)
  |      pods 0/1 --------> readiness probe
  |
  +-- Step 6: kubectl diff + apply; verify 200 at the edge
```

**Fix & verify.** Apply the Service manifest from Git; confirm the EndpointSlice lists the Ready
pods; confirm `200` through the controller over HTTP and HTTPS (`curl --resolve` as in Step 2);
watch Traefik's log for a minute to be sure the "Skipping service" errors stopped.

**Rollback.** The fix *is* a rollback to the Git state. If the live edit was part of a planned
change (new labels on the pods), roll the whole change back instead: `git revert` the half-done
commit, `kubectl diff -f` and `kubectl apply -f` the previous manifests, or `helm rollback` if the
app is a Helm release (area 16).

**Prevent it next time.** Make Git the only way to change `shop` (GitOps, or a CI job that runs
`kubectl diff` and `kubectl apply`); limit humans to the `view` ClusterRole in production
namespaces (area 14); alert when a Service that backs an Ingress has zero ready endpoints
([Observability](32-learn-performance-observability.md)); and add a CI check that every Service
selector matches the labels of at least one Deployment template in the same manifests.

**See it on a real system / Hands-on lab (test VM only).** Recreate it: on the lab cluster run
`kubectl -n shop edit svc web`, change the selector to `app: web-frontend`, and walk Steps 1–6 with
a timer. Target: root cause with evidence in under five minutes.

**How it breaks.** The method itself fails when you skip Step 1, when you "fix" by restarting pods
(they were healthy, nothing changes), or when you fix with a second live edit and leave Git wrong.

**Why it matters for troubleshooting.** Every step narrowed the search to one layer with one
command and named the next move before taking it. That is exactly what the CKA's troubleshooting
tasks, and real incidents, reward.

**Next step.** Turn all of this into a passed CKA (area 21).

---

## 21. CKA exam strategy

> 📚 **Study path:** 1) KodeKloud: *Certified Kubernetes Administrator (CKA)* — Lightning Labs, then the course's Mock Exams ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)), in the order of KodeKloud's [CKA learning path](https://kodekloud.com/learning-path/cka) · 2) KodeKloud: *Ultimate Certified Kubernetes Administrator (CKA) Mock Exam Series* in the last two weeks ([course](https://kodekloud.com/courses/ultimate-certified-kubernetes-administrator-cka-mock-exam)) · 3) Simulator: [killer.sh](https://killer.sh/) sessions in the final week, plus free scenarios on [Killercoda](https://killercoda.com/) every morning · 4) Note: area 4 of this module (aliases, generators, jsonpath) and the timed drills in area 22.

The CKA is not a knowledge quiz. It is a timed, hands-on test of areas 3–20 on real clusters, and
it rewards the same habits as a real incident: confirm where you are, read the evidence, change
one thing, verify. Everything in this area is about spending your two hours on solving tasks, not
on typing, searching or recovering from avoidable mistakes.

### Exam format and domains

**Level:** [L3 · Senior] · CKA: all domains

**Concept.** The CKA is an online, proctored, performance-based exam: about two hours, a remote
Linux desktop with a terminal and a browser, and a set of tasks (typically 15–20, each with its
own weight) solved on live kubeadm clusters. Each task tells you which cluster to use, either a
`kubectl config use-context` command or a host to `ssh` into. During the exam you may open the
Kubernetes documentation ([kubernetes.io/docs](https://kubernetes.io/docs/)) and blog in the exam
browser; the candidate handbook lists any other allowed sites. Pass mark, number of tasks, the
Kubernetes version, the retake policy and the bundled killer.sh simulator sessions change over
time: read the current Linux Foundation candidate handbook and the CNCF curriculum page before you
book, and treat the numbers here as a snapshot.

**Key terms** (domains and weights of the curriculum in force since early 2025, as listed in the
KodeKloud CKA course, which was last updated in April 2026 for Kubernetes 1.35; the Linux Foundation
CKA page showed the same weights and "based on Kubernetes v1.35" in October 2026, while the CNCF
curriculum repository already carries a v1.37 curriculum file, so verify before you book)

| Domain | Weight | Areas in this module | What tasks look like |
|---|---|---|---|
| Troubleshooting | 30% | 2, 5, 7, 9, 18, 20, 22 | fix a NotReady node, a broken control-plane component, a crash-looping app or a Service with no endpoints; read logs, events and metrics |
| Cluster Architecture, Installation & Configuration | 25% | 3, 4, 14, 16, 19 | RBAC, kubeadm install or upgrade, etcd backup and restore, install something with Helm or Kustomize, CRDs and operators, CNI/CSI/CRI basics |
| Services & Networking | 20% | 7, 8, 9, 15 | expose workloads, Ingress and Gateway API routes, NetworkPolicies, CoreDNS |
| Workloads & Scheduling | 15% | 5, 6, 10, 12, 13 | rollouts and rollbacks, ConfigMaps and Secrets, resource limits, affinity and taints, autoscaling, sidecars |
| Storage | 10% | 11 | StorageClasses, PV and PVC binding, access modes, reclaim policies, volume types |

**See it on a real system.** Rehearse the first thirty seconds of every task until it is
automatic. The commands are the same on your homelab, in KodeKloud labs and in the exam.

```bash
# 1. Switch exactly as the task says (copy the command from the task text)
kubectl config use-context CONTEXT          # or: ssh HOST
kubectl config current-context              # prove it before typing anything else
# 2. Namespace named in the task? Put -n NS in every command (safer than changing the default)
kubectl -n NS get all
# 3. Built-in docs, faster than the browser for field names
kubectl explain pod.spec.affinity.nodeAffinity --recursive | less
kubectl create ingress -h | sed -n '/Examples:/,/Options:/p'
```

```
$ kubectl config current-context
k8s-c2-admin@k8s-c2
```

→ If that line does not match the task, stop: anything you create now lands on the wrong cluster
and scores zero.

**Hands-on lab (test VM only).** Build a "mini exam" from this module: eight tasks, 40 minutes,
one per domain plus four troubleshooting drills from area 22. Before each task, write the context
and namespace on paper; after each task, write the one command that proves it is done.

**How it breaks**

| Failure | Symptom | Prevention |
|---|---|---|
| Wrong context or host | your work exists, on another cluster; task scores zero | switch and check at the start of every task |
| Wrong namespace | object created in `default` | `-n NS` on every command; re-read the task's namespace |
| Output saved to the wrong path or format | task asks for `/opt/course/N/file.yaml`, you wrote it elsewhere | copy paths from the task text; `cat` the file at the end |
| Name typo | `web-server` vs `webserver`; the checker finds nothing | copy names from the task text instead of typing them |
| Static pod edit not yet applied | you move on while the kubelet is still restarting the pod | wait for `crictl ps` or `kubectl get` to show the new state |
| Pasted YAML mangled | `mapping values are not allowed` | vim settings from area 4; paste with Ctrl+Shift+V in the terminal |

**Why it matters for troubleshooting.** The exam domains are a fair map of real Kubernetes work,
and Troubleshooting carries the most weight. Every hour you put into areas 18–20 and the drills
pays twice: in the exam and on call.

**Next step.** Plan your two hours before you sit down.

### Time management and task triage

**Level:** [L3 · Senior] · CKA: all domains

**Concept.** With about 120 minutes and roughly 16 tasks you have seven to eight minutes per task
on average, but tasks are not equal: some take one imperative command, some take twenty minutes of
node debugging. The winning strategy is **triage**: do everything quick first, flag anything that
is not going well after a few minutes, and come back with the time that is left. A task worth 4%
is not worth fifteen minutes while three 7% tasks wait.

**Key terms**

| Phase | Time | What you do |
|---|---|---|
| Pass 1 | about 80 min | every task in order; if a task is not clearly converging after about 6 minutes, write down where you stopped, flag it, move on |
| Pass 2 | about 30 min | flagged tasks, highest weight first |
| Final check | last 10 min | for each task, one command that proves it is done (`get`, `describe`, `curl`, `cat FILE`) |

**See it on a real system.** Practise the "prove it" commands so verification takes seconds:

```bash
kubectl -n NS get deploy,pods,svc,endpointslices -o wide        # workloads and wiring
kubectl -n NS get events --sort-by=.lastTimestamp | tail -5      # anything still failing?
kubectl auth can-i VERB RESOURCE -n NS --as SUBJECT              # RBAC tasks
kubectl get nodes                                                # node and upgrade tasks
cat /path/from/the/task                                          # output-file tasks
```

**Hands-on lab (test VM only).** Take one KodeKloud mock exam with a strict clock and a notepad
log: task number, minutes spent, flagged or done. Afterwards, for every task over eight minutes,
write down what cost the time (finding docs, YAML errors, wrong layer). That list is your study
plan for the next week.

**How it breaks**

| Failure | Symptom | Prevention |
|---|---|---|
| Perfectionism on one task | 25 minutes on a 4% task, three tasks never opened | flag after about 6 minutes without progress |
| Writing YAML from scratch | slow, indentation errors | generators: `kubectl create ... --dry-run=client -o yaml` (area 4) |
| Searching the docs for everything | minutes lost per task | `kubectl explain`, `-h` examples; bookmark nothing, search by exact page title |
| No verification | tasks "done" but wrong | the final-check pass |
| Panic after a hard task | the next easy task also goes wrong | flag, breathe, take the next one; it is a points game |

**Why it matters for troubleshooting.** Incidents are also timed. Triage (stabilise what you can,
park what you cannot, come back with more evidence) is how senior engineers work under pressure.

**Next step.** Build the practice plan that gets you to exam speed.

### Practice plan and simulators

**Level:** [L3 · Senior] · CKA: all domains

**Concept.** Speed comes from repetition on clusters that break. Your KodeKloud map puts the CKA in
weeks 6–11 of your plan and the final practice in week 12. KodeKloud's labs give you pre-built
clusters, so you practise the skill without fighting setup; your homelab gives you clusters *you*
built, which is where the troubleshooting intuition comes from. You need both.

**Key terms**

| Resource | What it is | When |
|---|---|---|
| KodeKloud *Certified Kubernetes Administrator (CKA)* ([course](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator)) | course, labs after each lesson, two Lightning Labs, three mock exams | weeks 6–11, in the order of the study paths above |
| KodeKloud *Kubernetes Challenges* (free, [course](https://kodekloud.com/courses/kubernetes-challenges)) | four timed challenges: deploy from a diagram, troubleshoot, secure | weekends during weeks 8–11 |
| KodeKloud *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)) | 43 labs and challenges of broken apps | alongside areas 5–17 |
| KodeKloud *Ultimate Certified Kubernetes Administrator (CKA) Mock Exam Series* ([course](https://kodekloud.com/courses/ultimate-certified-kubernetes-administrator-cka-mock-exam)) | extra full mock exams | last two weeks |
| [killer.sh](https://killer.sh/) | exam simulator, harder than the real exam | final week; review every answer afterwards |
| [Killercoda](https://killercoda.com/) | free browser clusters and scenarios | 30-minute morning reps |
| KodeKloud [Kubernetes multi-cluster playground](https://kodekloud.com/playgrounds/playground-kubernetes-multi-cluster) | throwaway clusters | when the homelab is down |
| Your homelab and the 20 drills (area 22) | clusters you built and broke | every weekend |

**See it on a real system.** Keep a mistakes log next to your five-line lab notes. Each row: date,
source (mock, killer.sh, drill), task, what went wrong, the command or doc page that fixed it. Read
it before every mock exam.

**Hands-on lab (test VM only).** The final two weeks, as a schedule:

| Day | Main block | Morning rep |
|---|---|---|
| 1–3 | CKA Lightning Labs; redo every failed lab task | two Killercoda scenarios |
| 4–6 | CKA course mock exams 1–3; mistakes log after each | drills 11–15 |
| 7–9 | Ultimate CKA Mock Exam Series, one per evening | drills 1–10 |
| 10 | killer.sh session 1, then a full review (it takes longer than the session) | none |
| 11–12 | redo every killer.sh task you missed, without hints | drills 16–20 |
| 13 | killer.sh session 2, review | none |
| 14 | light review of the mistakes log and area 4 shortcuts; sleep | none |

**How it breaks**

| Failure | Symptom | Prevention |
|---|---|---|
| Only watching videos | understands everything, solves nothing in time | lab after every lesson; drills every week |
| Mocks too early | discouraging scores, wasted simulator sessions | mocks only after the course and the drills |
| Never reviewing mistakes | the same errors in every mock | the mistakes log |
| Only pre-built lab clusters | lost when a kubeadm node or static pod is broken | homelab break-and-fix every weekend |

**Why it matters for troubleshooting.** Deliberate practice with feedback is how the method in
area 20 becomes a reflex rather than a page you have to read.

**Next step.** The exam day itself.

### Exam day checklist

**Level:** [L3 · Senior] · CKA: all domains

**Concept.** Most exam-day failures have nothing to do with Kubernetes: ID problems, a desk the
proctor rejects, a webcam or network issue, or arriving tired. Remove them in advance so the only
thing left to manage is the tasks.

**Key terms**

| When | Check |
|---|---|
| A week before | run the exam provider's system check on the exact computer, network and webcam you will use; read the current candidate handbook |
| The day before | government ID that matches your registration name; clear desk and walls; one monitor; charger; stop all background apps that could pop up |
| 30 minutes before | restart the machine, close everything, wired network if possible, phone out of reach, water in a clear glass if allowed |
| First minute | adjust the font size of the terminal, check copy-paste (Ctrl+Shift+C and Ctrl+Shift+V in the terminal), set `alias k=kubectl` and completion if not already present |
| Every task | context or ssh first, namespace second, verification last |

**See it on a real system.** Do one full mock exam on the same computer, at the same time of day,
with the same setup you will use on exam day, a week before.

**Hands-on lab (test VM only).** Not applicable: this topic is about removing non-technical risk.

**How it breaks**

| Failure | Symptom | Prevention |
|---|---|---|
| Name on ID differs from registration | check-in delayed or refused | fix the registration name early |
| Workspace rejected | lost time during check-in | clear desk and walls, nothing written on the whiteboard behind you |
| Unstable connection | the remote desktop freezes | wired network; close sync clients and video calls |
| Fatigue | silly mistakes in the second hour | sleep, eat, and do not cram the night before |

**Why it matters for troubleshooting.** Preparing the environment before the work starts is the
same discipline as a change window: checklists, a rollback plan, no surprises.

**Next step.** Keep the skill sharp, before and after the exam, with timed drills (area 22).

---

## 22. Twenty timed break-and-fix drills

> 📚 **Study path:** 1) Note: area 20 (the method) and the [Containers & Kubernetes playbook](26-playbook-containers-k8s.md), open in a second window · 2) KodeKloud: the Troubleshooting Scenarios of *Kubernetes Troubleshooting for Application Developers* ([course](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers)) and the four timed *Kubernetes Challenges* (free, [course](https://kodekloud.com/courses/kubernetes-challenges)) · 3) Practice outside KodeKloud: [iximiuz Labs Kubernetes challenges](https://labs.iximiuz.com/challenges?category=kubernetes) and [Killercoda](https://killercoda.com/) · 4) Your homelab: the twenty drills below, timed, from VM snapshots.

Real skill comes from fixing things you did not break yourself, against a clock. Each drill below
has a **Break it** block (run it, or better, let a script or a friend run it), the symptom you will
see, the first command and why it comes first, the fix, and the topic it practises. Do not read
past "What you see" until the timer stops.

### How to run the drills

**Level:** [L3 · Senior] → [L4 · Lead/SRE] · CKA: Troubleshooting

**Concept.** A drill is a small, repeatable incident: one fault, one symptom, a target time. You
score two things: **time to evidence** (when you can name the broken layer and prove it) and
**time to fix** (verified from the user's side). The method from area 20 is the same every time;
only the fault changes. Running them at random, from a script, removes the "I know what I broke"
advantage, which is what turns practice into troubleshooting.

**Key terms**

| Rule | Why |
|---|---|
| Lab cluster only, snapshot "drills-clean" taken first | node and control-plane drills can leave debris |
| Everything in namespace `drills`, reset after each drill | drills do not interfere with each other |
| Start every drill with the same three commands | the method, not memory, finds the fault |
| Name the layer and the evidence before you fix | scoring: guessing does not count |
| Five-line note after every drill | symptom, first wrong guess, evidence, fix, what to check first next time |

| Drill needs | Set up in |
|---|---|
| local-path StorageClass (drill 16) | area 11 |
| Traefik as NodePort 31080 (drill 10) | area 16 |
| Calico or Cilium, not Flannel (drill 9) | area 3 |
| Lab registry with a private CA, trusted on all nodes (drill 18) | area 17 |
| `etcdctl` and `etcdutl` on cp1 (drill 20) | area 19 |
| SSH from cp1 to w1 and w2 with sudo (drills 11, 12, 18) | area 3 |

**See it on a real system.** One-time setup on cp1, then the random picker. Save each drill's
**Break it** block below as `~/drills/dNN.sh` (`d01.sh` to `d20.sh`); leave out drills whose
requirements your lab does not have.

```bash
mkdir -p ~/drills
kubectl create namespace drills
# Random picker: runs one drill without telling you which (the number is saved for afterwards)
n=$(printf '%02d' "$(shuf -i 1-20 -n 1)"); echo "$n" > ~/drills/.answer
bash ~/drills/d"$n".sh > /dev/null 2>&1
echo "Something is broken. Timer started at $(date +%T)"
```

Start every drill with the same three commands:

```bash
kubectl get nodes
kubectl get pods -A -o wide | grep -vE 'Running|Completed'
kubectl get events -A --field-selector type=Warning --sort-by=.lastTimestamp | tail -15
```

**Hands-on lab (test VM only).** Reset after each drill. Deleting the namespace removes every drill
object, so check the context first; never run this anywhere but the lab cluster.

```bash
kubectl config current-context                     # must be the lab cluster
kubectl delete namespace drills --wait=true        # lab only
kubectl create namespace drills
kubectl label node w1 disk- 2>/dev/null; kubectl get nodes   # remove drill labels; no SchedulingDisabled left
```

After drills 11–15, 18 and 20, also confirm the node or control-plane file is back to its original
(the drill keeps a `.good` copy in `/root`), or revert to the "drills-clean" snapshot.

**How it breaks**

| Failure | Symptom | Prevention |
|---|---|---|
| Reading the answer first | fast times, no learning | let the picker or a friend run the break |
| Skipping the reset | the next drill shows two faults | reset block every time |
| Fixing without evidence | "it works now" but you cannot say why | name layer and evidence before the fix |
| Always the same drill order | you remember instead of diagnose | random picker |

**Scoring**

| Result | Meaning | Next |
|---|---|---|
| Evidence named, fixed within target | pass | move to a harder drill |
| Fixed, but over target | slow | repeat within a week |
| Fixed by guessing, or not fixed | fail | redo the matching topic's lab, then the drill |

**Why it matters for troubleshooting.** The drills are the Ops Ladder's homelab break-and-fix
sessions made concrete, and they cover every row of the Troubleshooting domain of the CKA.

**Next step.** Drills 1–5.

### Drills 1–5: pods and workloads

**Level:** [L1 · Junior] → [L2 · Mid] · CKA: Workloads & Scheduling, Troubleshooting

**Drill 1 — Image tag typo** · [L1 · Junior] · target 3 min

**Break it (test VM only):**

```bash
kubectl -n drills create deployment d1 --image=nginx:1.27 --replicas=2
kubectl -n drills rollout status deploy/d1 --timeout=90s
kubectl -n drills set image deploy/d1 nginx=nginx:1.27-alpne
```

**What you see:** two old pods still `Running`, one new pod in `ErrImagePull` or
`ImagePullBackOff`, and a rollout that never finishes.

**First command and why:** `kubectl -n drills describe pod -l app=d1 | grep -A2 -E 'Failed|BackOff'`.
The pull error's class picks the next move: `not found` means a wrong name or tag, `401` means
credentials, `x509` means trust, `no such host` means DNS on the node.

**Fix & verify:** `kubectl -n drills rollout undo deploy/d1`, then
`kubectl -n drills rollout status deploy/d1`. Fix the tag in Git before the next deploy.
Practises area 6 and the "ErrImagePull + not found" row of the decoder.

**Drill 2 — Crash loop from a missing setting** · [L1 · Junior] · target 4 min

**Break it (test VM only):**

```bash
kubectl -n drills create deployment d2 --image=busybox:1.36 -- sh -c 'test -n "$DB_HOST" || { echo "FATAL: DB_HOST is not set" >&2; exit 1; }; echo "connecting to $DB_HOST"; sleep 3600'
```

**What you see:** `CrashLoopBackOff`, RESTARTS climbing, `0/1`.

**First command and why:** `kubectl -n drills logs deploy/d2 --previous`, which prints
`FATAL: DB_HOST is not set`. CrashLoopBackOff is not a cause; the previous container's log and
exit code (`describe`: Last State, Exit Code 1) are.

**Fix & verify:** `kubectl -n drills set env deploy/d2 DB_HOST=db.drills.svc.cluster.local`, then
`kubectl -n drills logs deploy/d2` shows `connecting to ...`. In a real app the value belongs in a
ConfigMap (area 10). Practises area 5 (exit codes).

**Drill 3 — OOMKilled** · [L2 · Mid] · target 4 min

**Break it (test VM only):** the worker allocates about 150 MB, the limit allows 100 Mi.

```bash
cat <<'EOT' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: d3
  namespace: drills
spec:
  replicas: 1
  selector:
    matchLabels: {app: d3}
  template:
    metadata:
      labels: {app: d3}
    spec:
      containers:
      - name: worker
        image: polinux/stress
        command: ["stress"]
        args: ["--vm", "1", "--vm-bytes", "150M", "--vm-hang", "1"]
        resources:
          requests: {memory: "50Mi"}
          limits: {memory: "100Mi"}
EOT
```

**What you see:** STATUS alternates between `OOMKilled` and `CrashLoopBackOff`.

**First command and why:** `kubectl -n drills describe pod -l app=d3 | grep -A5 'Last State'`
shows `Reason: OOMKilled` and `Exit Code: 137`. That combination means the container hit its own
cgroup limit; a liveness kill also exits 137 but shows `Killing` events, and node pressure shows
`Evicted` instead.

**Fix & verify:** in real life check for a leak first ([Memory](04-memory.md)); here the worker
legitimately needs 150 MB: `kubectl -n drills set resources deploy/d3 --requests=memory=200Mi --limits=memory=256Mi`.
The new pod stays `Running`; `kubectl -n drills top pod` shows its usage. Practises area 12.

**Drill 4 — Pending: label mismatch** · [L2 · Mid] · target 4 min

**Break it (test VM only):**

```bash
kubectl label node w1 disk=ssd --overwrite
kubectl -n drills create deployment d4 --image=nginx:1.27 --dry-run=client -o yaml \
  | sed 's/^    spec:/    spec:\n      nodeSelector:\n        disk: sdd/' | kubectl apply -f -
```

**What you see:** the pod stays `Pending` with no node assigned.

**First command and why:** `kubectl -n drills describe pod -l app=d4 | tail -3` shows
`0/3 nodes are available: 1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: }, 2 node(s) didn't match Pod's node affinity/selector`.
The scheduler gives a reason per node; "didn't match ... selector" sends you to labels, not to
resources. `kubectl get nodes -L disk` shows the real value `ssd`.

**Fix & verify:** `kubectl -n drills patch deploy d4 -p '{"spec":{"template":{"spec":{"nodeSelector":{"disk":"ssd"}}}}}'`;
the new pod runs on w1. Practises area 12.

**Drill 5 — Two of four replicas, and no failing pods** · [L2 · Mid] · target 5 min

**Break it (test VM only):**

```bash
kubectl -n drills create quota drills-pods --hard=pods=2
kubectl -n drills create deployment d5 --image=nginx:1.27 --replicas=4
```

**What you see:** `kubectl -n drills get deploy d5` shows `2/4`, and the two pods that exist are
healthy.

**First command and why:** `kubectl -n drills describe rs -l app=d5 | grep -A3 Events` shows
`FailedCreate ... exceeded quota: drills-pods, requested: pods=1, used: pods=2, limited: pods=2`.
Missing pods have no events of their own; the error lives one level up, on the ReplicaSet.

**Fix & verify:** agree with the namespace owner, then raise the quota
(`kubectl -n drills patch quota drills-pods -p '{"spec":{"hard":{"pods":"10"}}}'`) or lower the
replicas. The ReplicaSet retries on its own; `get deploy` shows `4/4` within a minute. Practises
area 12 (quotas).

**Next step.** Drills 6–10: traffic that does not arrive.

### Drills 6–10: Services, DNS and Ingress

**Level:** [L2 · Mid] · CKA: Services & Networking, Troubleshooting

All five use a throwaway client pod in the same namespace:

```bash
kubectl -n drills run t --rm -it --restart=Never --image=nicolaka/netshoot -- sh
```

**Drill 6 — Service with no endpoints** · [L2 · Mid] · target 4 min

**Break it (test VM only):**

```bash
kubectl -n drills create deployment d6 --image=nginx:1.27 --replicas=2
kubectl -n drills expose deploy d6 --port=80
kubectl -n drills patch svc d6 -p '{"spec":{"selector":{"app":"d6-web"}}}'
```

**What you see:** from the client pod, `curl -sS -m 3 http://d6` fails with
`Connection refused`, although both pods are `Running` and `1/1`.

**First command and why:** `kubectl -n drills get endpointslices -l kubernetes.io/service-name=d6`
shows `<unset>` endpoints. Refused plus an empty slice means the selector matches nothing
(not-Ready pods would still be listed, marked not ready), so compare `kubectl -n drills get svc d6 -o wide` (SELECTOR) with
`kubectl -n drills get pods --show-labels`.

**Fix & verify:** `kubectl -n drills patch svc d6 -p '{"spec":{"selector":{"app":"d6"}}}'`; the
slice lists two IPs and `curl http://d6` returns the nginx page. Practises area 7 and the worked
example in area 20.

**Drill 7 — Endpoints present, still refused** · [L2 · Mid] · target 4 min

**Break it (test VM only):**

```bash
kubectl -n drills create deployment d7 --image=nginx:1.27 --replicas=2
kubectl -n drills expose deploy d7 --port=80 --target-port=8080
```

**What you see:** `curl http://d7` from the client pod is refused, yet the EndpointSlice lists
both pods.

**First command and why:** `kubectl -n drills get endpointslices -l kubernetes.io/service-name=d7`
shows PORTS `8080`. From the client pod, `curl -sI http://POD_IP:80` answers and
`curl -sI http://POD_IP:8080` is refused. Endpoints prove the selector is right, so the remaining
hop is the port mapping.

**Fix & verify:** `kubectl -n drills patch svc d7 -p '{"spec":{"ports":[{"port":80,"targetPort":80}]}}'`;
`curl http://d7` returns 200. Practises area 7 (the three ports).

**Drill 8 — Running but never Ready** · [L2 · Mid] · target 5 min

**Break it (test VM only):**

```bash
cat <<'EOT' | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: d8
  namespace: drills
spec:
  replicas: 2
  selector:
    matchLabels: {app: d8}
  template:
    metadata:
      labels: {app: d8}
    spec:
      containers:
      - name: web
        image: nginx:1.27
        ports:
        - containerPort: 80
        readinessProbe:
          httpGet: {path: /, port: 8080}
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: d8
  namespace: drills
spec:
  selector: {app: d8}
  ports:
  - port: 80
    targetPort: 80
EOT
```

**What you see:** both pods `Running` but `0/1`; `curl http://d8` is refused.

**First command and why:** `kubectl -n drills describe pod -l app=d8 | grep -E 'Readiness|Unhealthy'`
shows `Readiness probe failed: Get "http://10.244.1.40:8080/": dial tcp 10.244.1.40:8080: connect: connection refused`.
`Running` with `0/1` always means a probe, and the event names the exact URL the kubelet tried.

**Fix & verify:**
`kubectl -n drills patch deploy d8 --type=json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/readinessProbe/httpGet/port","value":80}]'`;
new pods become `1/1`, the slice shows them ready, `curl http://d8` returns 200. Practises area 5
(probes).

**Drill 9 — Names time out after a hardening change** · [L2 · Mid] · target 5 min (needs Calico or
Cilium)

**Break it (test VM only):** a policy meant to "allow traffic inside the namespace only".

```bash
kubectl -n drills create deployment d9 --image=nginx:1.27
kubectl -n drills expose deploy d9 --port=80
cat <<'EOT' | kubectl apply -f -
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: hardening
  namespace: drills
spec:
  podSelector: {}
  policyTypes: ["Egress"]
  egress:
  - to:
    - podSelector: {}
EOT
```

**What you see:** from the client pod, `curl -sS -m 5 http://d9` fails with
`curl: (28) Resolving timed out after 5000 milliseconds`, but `curl http://CLUSTER_IP` of `d9`
works.

**First command and why:** `nslookup d9` in the client pod gives
`;; communications error to 10.96.0.10#53: timed out` and `;; no servers could be reached` (older
BIND tools print `;; connection timed out; no servers could be reached`), then `kubectl -n drills get netpol`.
Name fails while the IP works puts the fault at DNS; a timeout (not NXDOMAIN) means packets are
dropped; a fault limited to one namespace makes its NetworkPolicies the first suspect. The policy
allows egress only to pods in `drills`, and CoreDNS lives in `kube-system`.

**Fix & verify:** add the `allow-dns` policy from area 15 (egress to `k8s-app: kube-dns` in
`kube-system` on UDP and TCP 53) to namespace `drills`; `nslookup d9` and `curl http://d9` both
work. Practises areas 9 and 15, and the Ops Ladder case "a NetworkPolicy blocks port 53".

**Drill 10 — Ingress returns 404** · [L2 · Mid] · target 5 min (needs Traefik from area 16)

**Break it (test VM only):**

```bash
kubectl -n drills create deployment d10 --image=traefik/whoami --replicas=2
kubectl -n drills expose deploy d10 --port=80
kubectl -n drills create ingress d10 --class=nginx --rule="d10.example.com/*=d10:80"
```

**What you see:** `curl -s -H 'Host: d10.example.com' http://192.168.56.11:31080/` returns
`404 page not found`.

**First command and why:** `kubectl -n drills get ingress d10` shows CLASS `nginx` and an empty
ADDRESS; `kubectl get ingressclass` lists only `traefik`. A controller 404 means "no router for
this host", and an empty ADDRESS says no controller adopted the Ingress, so you check the class
before the backend.

**Fix & verify:** `kubectl -n drills patch ingress d10 -p '{"spec":{"ingressClassName":"traefik"}}'`;
the same curl prints the whoami output (`Hostname: d10-...`). Practises area 8.

**Next step.** Drills 11–15: when kubectl itself cannot help.

### Drills 11–15: nodes and control plane

**Level:** [L3 · Senior] · CKA: Troubleshooting

> Warning: these drills stop node services and edit static pod manifests. Lab cluster only, with a
> VM snapshot of every node. Each break keeps a `.good` copy outside
> `/etc/kubernetes/manifests`, because the kubelet tries to run every file in that directory.

**Drill 11 — Worker NotReady, case 1** · [L3 · Senior] · target 4 min

**Break it (test VM only):**

```bash
ssh w1 'sudo systemctl disable --now kubelet'
```

**What you see:** after about 50 seconds (40 before v1.32) `kubectl get nodes` shows w1 `NotReady`, and
`kubectl describe node w1` says `Kubelet stopped posting node status`.

**First command and why:** on w1, `systemctl status kubelet --no-pager` shows `inactive (dead)`
and `disabled`. "Stopped posting" means the kubelet is not talking to the API; the unit state
separates "stopped" (this drill) from "crashing" (auto-restart loop, so read the journal).

**Fix & verify:** `ssh w1 'sudo systemctl enable --now kubelet'`; w1 is `Ready` within a minute.
`enable` matters: without it the next reboot breaks the node again. Practises area 18.

**Drill 12 — Worker NotReady, case 2** · [L3 · Senior] · target 7 min

**Break it (test VM only):**

```bash
ssh w1 'sudo cp /etc/containerd/config.toml /root/config.toml.good && echo "[plugins" | sudo tee -a /etc/containerd/config.toml > /dev/null && sudo systemctl restart containerd'
```

**What you see:** w1 `NotReady`; the kubelet journal on w1 is full of CRI connection errors to
`/run/containerd/containerd.sock`.

**First command and why:** on w1, `systemctl status containerd --no-pager` shows `failed`, and
`journalctl -u containerd -n 20 --no-pager` shows a `failed to load TOML` error pointing at the
last line of the file. The kubelet's errors are the symptom; the runtime's own journal holds the
cause.

**Fix & verify:** `sudo cp /root/config.toml.good /etc/containerd/config.toml`, then
`sudo systemctl restart containerd` and `sudo systemctl restart kubelet`; w1 returns to `Ready`.
Next time, `sudo containerd config dump > /dev/null` before restarting catches the typo.
Practises areas 3 and 18.

**Drill 13 — kubectl is dead** · [L3 · Senior] · target 8 min

**Break it (test VM only, on cp1):**

```bash
sudo cp /etc/kubernetes/manifests/kube-apiserver.yaml /root/kube-apiserver.yaml.good
sudo sed -i 's#--tls-cert-file=/etc/kubernetes/pki/apiserver.crt#--tls-cert-file=/etc/kubernetes/pki/apiserver-typo.crt#' /etc/kubernetes/manifests/kube-apiserver.yaml
```

**What you see:** within a minute every kubectl command fails with
`The connection to the server 192.168.56.10:6443 was refused - did you specify the right host or port?`

**First command and why:** `sudo crictl ps -a --name kube-apiserver` (Exited, ATTEMPT rising),
then `sudo crictl logs --tail 5 CONTAINER_ID`, which ends with
`open /etc/kubernetes/pki/apiserver-typo.crt: no such file or directory`. With the API server
down, kubectl has nothing to ask; crictl talks to containerd directly.

**Fix & verify:** `sudo cp /root/kube-apiserver.yaml.good /etc/kubernetes/manifests/kube-apiserver.yaml`;
wait up to a minute for the kubelet to restart the static pod; `kubectl get nodes` answers.
Practises area 20 (control-plane failure signatures).

**Drill 14 — New pods Pending, with no events** · [L3 · Senior] · target 6 min

**Break it (test VM only, on cp1):**

```bash
sudo cp /etc/kubernetes/manifests/kube-scheduler.yaml /root/kube-scheduler.yaml.good
sudo sed -i 's#\(image: registry.k8s.io/kube-scheduler:\).*#\1v0.0.0-broken#' /etc/kubernetes/manifests/kube-scheduler.yaml
sleep 40
kubectl -n drills create deployment d14 --image=nginx:1.27
```

**What you see:** the d14 pod is `Pending`, and `kubectl -n drills describe pod -l app=d14` shows
**no events at all**.

**First command and why:** `kubectl -n kube-system get pods | grep scheduler` shows
`kube-scheduler-cp1` in `ImagePullBackOff` (or `ErrImagePull`). No `FailedScheduling` event means
nobody even tried to schedule the pod, which points at the scheduler, not at the cluster's
capacity.

**Fix & verify:** `sudo cp /root/kube-scheduler.yaml.good /etc/kubernetes/manifests/kube-scheduler.yaml`;
the scheduler pod returns and d14 gets a node within a minute. Practises area 2 (the scheduler lab)
and area 20.

**Drill 15 — A Deployment that does nothing** · [L3 · Senior] · target 6 min

**Break it (test VM only, on cp1):**

```bash
sudo cp /etc/kubernetes/manifests/kube-controller-manager.yaml /root/kube-controller-manager.yaml.good
sudo sed -i 's#--kubeconfig=/etc/kubernetes/controller-manager.conf#--kubeconfig=/etc/kubernetes/controller-manager-typo.conf#' /etc/kubernetes/manifests/kube-controller-manager.yaml
sleep 40
kubectl -n drills create deployment d15 --image=nginx:1.27 --replicas=2
```

**What you see:** `kubectl -n drills get deploy d15` shows `0/2` with UP-TO-DATE `0`, and
`kubectl -n drills get rs` finds nothing.

**First command and why:** `kubectl -n kube-system get pods | grep controller-manager` shows
`CrashLoopBackOff`; `sudo crictl logs` on its latest container ends with a
`... controller-manager-typo.conf: no such file or directory` error. A Deployment without a
ReplicaSet means the Deployment controller never ran.

**Fix & verify:** `sudo cp /root/kube-controller-manager.yaml.good /etc/kubernetes/manifests/kube-controller-manager.yaml`;
the ReplicaSet and both pods appear within a minute. Practises areas 2 and 20.

**Next step.** Drills 16–20: storage, access and maintenance.

### Drills 16–20: storage, security, maintenance

**Level:** [L2 · Mid] → [L4 · Lead/SRE] · CKA: Storage, Cluster Architecture, Troubleshooting

**Drill 16 — Pod Pending on its volume** · [L2 · Mid] · target 4 min (needs local-path from area 11)

**Break it (test VM only):**

```bash
cat <<'EOT' | kubectl apply -f -
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: d16-data
  namespace: drills
spec:
  storageClassName: local-pth
  accessModes: ["ReadWriteOnce"]
  resources:
    requests: {storage: 1Gi}
---
apiVersion: v1
kind: Pod
metadata:
  name: d16
  namespace: drills
spec:
  containers:
  - name: app
    image: busybox:1.36
    command: ["sh", "-c", "date > /data/started; sleep 3600"]
    volumeMounts:
    - {name: data, mountPath: /data}
  volumes:
  - name: data
    persistentVolumeClaim: {claimName: d16-data}
EOT
```

**What you see:** pod `Pending` with `pod has unbound immediate PersistentVolumeClaims`.

**First command and why:** `kubectl -n drills describe pvc d16-data | tail -3` shows
`ProvisioningFailed ... storageclass.storage.k8s.io "local-pth" not found`, and
`kubectl get storageclass` shows the real name. Follow the chain pod → PVC → StorageClass →
provisioner; the pod's own event only says "unbound".

**Fix & verify:** a PVC's class cannot be changed in place. Nothing is bound yet
(`kubectl get pv` shows no volume for `drills/d16-data`), so recreating loses no data: delete the
pod and the PVC, fix `storageClassName: local-path` in the file, and apply again. The PVC goes
`Bound` and the pod `Running`. Practises area 11.

**Drill 17 — CI deploy fails with Forbidden** · [L3 · Senior] · target 6 min

**Break it (test VM only):**

```bash
kubectl -n drills create serviceaccount ci
cat <<'EOT' | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: ci-deploy
  namespace: drills
rules:
- apiGroups: [""]
  resources: ["deployments", "pods"]
  verbs: ["get", "list", "watch", "create", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: ci-deploy
  namespace: drills
subjects:
- kind: ServiceAccount
  name: ci
  namespace: drills
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: ci-deploy
EOT
```

**What you see:** the "CI job", `kubectl -n drills get deploy --as=system:serviceaccount:drills:ci`,
fails with
`Error from server (Forbidden): deployments.apps is forbidden: User "system:serviceaccount:drills:ci" cannot list resource "deployments" in API group "apps" in the namespace "drills"`.

**First command and why:** `kubectl auth can-i list deployments.apps -n drills --as=system:serviceaccount:drills:ci`
answers `no`, and `kubectl -n drills describe role ci-deploy` lists `deployments` without the
`.apps` suffix. The Forbidden message names group `apps`; the Role grants the core group `""`.

**Fix & verify:** split the rule: `apiGroups: ["apps"]` for `deployments`, `apiGroups: [""]` for
`pods`; apply; `can-i` answers `yes`. Practises area 14.

**Drill 18 — ImagePullBackOff on one node only** · [L3 · Senior] · target 8 min (needs the lab
registry from area 17, trusted on all nodes)

**Break it (test VM only):**

```bash
ssh w2 'sudo mv /etc/containerd/certs.d/registry.lab.example.com /root/'
kubectl -n drills create deployment d18 --image=registry.lab.example.com/web:1 --replicas=4
```

**What you see:** pods on w1 `Running`, pods on w2 in `ErrImagePull` or `ImagePullBackOff`.

**First command and why:** `kubectl -n drills get pods -o wide` shows the split by node; then
`kubectl -n drills describe pod POD_ON_W2 | grep -A2 Failed` shows
`x509: certificate signed by unknown authority`, and `sudo crictl pull registry.lab.example.com/web:1`
on w2 reproduces it. "Fails on one node only" points at node configuration, and x509 points at
trust, not at credentials.

**Fix & verify:** `ssh w2 'sudo mv /root/registry.lab.example.com /etc/containerd/certs.d/'`, then
`kubectl -n drills rollout restart deploy/d18`; all four pods run. The lasting fix is managing
`/etc/containerd/certs.d` on every node with Ansible ([CI/CD & IaC](33-learn-cicd-iac-sre.md)).
Practises area 17.

**Drill 19 — The drain that never finishes** · [L3 · Senior] · target 6 min

**Break it (test VM only):**

```bash
kubectl -n drills create deployment d19 --image=nginx:1.27 --replicas=2
kubectl -n drills create pdb d19 --selector=app=d19 --min-available=2
```

**The task:** "Drain the worker that runs d19's first pod for a kernel update, without violating
any PodDisruptionBudget, then put it back in service." Find the node with
`kubectl -n drills get pods -l app=d19 -o wide`.

**What you see:** `kubectl drain NODE --ignore-daemonsets --delete-emptydir-data --timeout=90s`
loops on `Cannot evict pod as it would violate the pod's disruption budget`, then times out.

**First command and why:** `kubectl get pdb -A` shows `d19` with ALLOWED DISRUPTIONS `0`. The
Eviction API is doing its job: the budget wants two pods available and only two exist. The fix is
capacity, not force.

**Fix & verify:** `kubectl -n drills scale deploy d19 --replicas=3`, wait for `3/3`, run the drain
again (it completes), do the "maintenance", then `kubectl uncordon NODE` and confirm no node shows
`SchedulingDisabled`. Do not use `--disable-eviction` or delete the PDB. Practises area 19.

**Drill 20 — A namespace deleted by mistake** · [L4 · Lead/SRE] · target 15 min

**Break it (test VM only, on cp1):** the backup exists before the "incident".

```bash
kubectl create namespace payments
kubectl -n payments create deployment api --image=nginx:1.27 --replicas=2
sudo mkdir -p /var/backups/etcd
sudo ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key \
  snapshot save /var/backups/etcd/drill20.db
kubectl delete namespace payments          # the "incident"; lab only
```

**The task:** "Namespace `payments` is gone. Restore it from `/var/backups/etcd/drill20.db` within
15 minutes, and state in your note what else the restore rolled back."

**First command and why:** `sudo etcdutl snapshot status /var/backups/etcd/drill20.db -w table`
proves the backup is readable before you stop anything. Then follow the restore steps in area 19
exactly: stop the API server, restore into a new data directory, point the etcd static pod's
`hostPath` at it, start the API server again.

**Fix & verify:** `kubectl -n payments get deploy api` shows `2/2`. The lead-level lesson is in
the note: an etcd restore rolls back **every** object in the cluster to the snapshot time, so for
one deleted namespace the smaller, safer restore is to re-apply its manifests from Git or reinstall
its Helm release. Keep etcd restores for losing the control plane's data, and say so in your
runbook. Practises area 19.

**Next step.** Prove each stage with the self-check and exit test (area 23).

---

## 23. Self-check and exit test

Answer the questions for your stage without notes, out loud or in writing, then do the timed tasks
for that stage. A question counts as passed only if you can name the command that proves your
answer. The area in brackets is where to look afterwards.

### Questions by career stage

**Level:** [L1 · Junior] → [L4 · Lead/SRE]

**Junior [L1 · Junior]**

1. `kubectl get pods` shows `0/1   Running`. What does each part mean, and which command tells you why? (area 5)
2. What is the difference between `kubectl logs POD` and `kubectl logs POD --previous`, and when does the first one mislead you? (area 5)
3. A deploy went wrong five minutes ago. Which commands roll it back and prove the rollback finished? (area 6)
4. How do you prove which cluster, identity and namespace your next command will hit? (area 4)
5. Why is deleting a pod that has no controller different from deleting a Deployment's pod? (area 1)

**Mid-level [L2 · Mid]**

6. A Service gives `Connection refused`. Name two causes that produce exactly that error and the one command that tells them apart. (area 7)
7. Why can `api.example.com` resolve slowly from a pod and fast from the node? What does `ndots:5` do? (area 9)
8. A ConfigMap changed but the app still uses the old value. Which ways of consuming it pick up changes, and which need a restart? (area 10)
9. A pod is `Pending` with `2 Insufficient memory`. Which fixes are legitimate, and why is "remove the requests" not one of them? (area 12)
10. Through Traefik a site returns 404 although the Ingress exists. Give two causes that are not a wrong host name. (area 8, area 20)

**Senior [L3 · Senior]**

11. Follow `kubectl apply` through the cluster. What do you see when it stops at the scheduler, at the CNI and at the EndpointSlice step? (area 2)
12. Control-plane pods restart every few minutes on a new kubeadm cluster. What is the most likely cause and where do you check it? (area 3)
13. Write from memory the policies for namespace `shop`: default deny for ingress and egress, allow DNS, allow `frontend` to reach `api` on 8080. (area 15)
14. `ImagePullBackOff` with `x509: certificate signed by unknown authority` on one node only. Where does the fix go, and why does a working `docker pull` on your laptop prove nothing? (area 17)
15. Which certificates does `kubeadm certs renew all` renew, and what must happen afterwards for the renewal to take effect? (area 19)

**Senior/Lead [L4 · Lead/SRE]**

16. A namespace was deleted by mistake. When is an etcd restore the right answer, and when is it the wrong one? (drill 20)
17. Which alerts would have told you about drills 6, 13 and 19 before a user did? (area 18, [Observability](32-learn-performance-observability.md))
18. What goes into the change request for a cluster upgrade (criticality, steps, verification, rollback), and how do you rehearse it? (area 19, [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md))
19. How would you teach the bottom-up method to a junior engineer in one hour? (area 20)
20. What is your calendar for certificate checks, etcd restore tests and upgrades, and who notices when it slips? (area 19)

### Timed practical tests

**Level:** [L1 · Junior] → [L4 · Lead/SRE] · CKA: all domains

**Part A — Junior [L1 · Junior], 30 minutes.** On the lab cluster: (1) switch to the lab context
and namespace `shop` and prove it with two commands; (2) list every pod in the cluster that is not
`Running` or `Completed` and save the list to `~/exit/not-running.txt`; (3) run drill 1 and roll
it back; (4) save all Warning events of the last hour to a file; (5) run drill 2 and show the
crashed container's last log line.

**Part B — Mid-level [L2 · Mid], 60 minutes.** Four random drills from 1–10 with the picker from
area 22, each within its target time, using the area 20 method out loud. Write the five-line note
for each. Then repeat the worked example in area 20 with the selector broken by someone else.

**Part C — Senior [L3 · Senior], one evening plus 2 hours.** (1) From bare Ubuntu VMs, build the
three-node cluster of area 3 (containerd with `SystemdCgroup`, Calico, two workers) in under 90
minutes, with notes. (2) Then a CKA-style mock of 15 tasks in 2 hours: etcd snapshot; one-minor
control-plane upgrade; Role and RoleBinding for a ServiceAccount; default-deny NetworkPolicy with a
DNS exception; Ingress for two paths; Gateway HTTPRoute; static PV and PVC that bind; fix a
NotReady worker (drill 11 or 12); fix a broken control-plane component (drill 13, 14 or 15);
taint, toleration and node affinity; HPA on CPU; Helm install with a values file; a native
sidecar; a jsonpath query saved to a file; drain a node with a PDB in place. Pass mark: two thirds
of the tasks fully correct.

**Part D — Senior/Lead [L4 · Lead/SRE], one weekend game day.** The Ops Ladder L4 exit test on
Kubernetes: monitoring from [Observability](32-learn-performance-observability.md) is running; the
picker breaks one thing at random while you are away from the screen; you learn about it from an
**alert**, fix it, and publish a one-page postmortem (timeline, impact, root cause, contributing
factors, follow-ups). In the same weekend: run drill 20 and a `kubeadm certs check-expiration`, and
put both on a monthly calendar. Stretch goal that ties the handbook together: move one of your
Apache workloads into the homelab cluster behind the Traefik Ingress, with its image built by
GitLab CI and pulled from Harbor through the private CA, and a rollback (`kubectl rollout undo` or
`helm rollback`) you have actually tested.

**Why it matters for troubleshooting.** Each part maps to what the career stage is trusted with:
reading (A), explaining (B), building and repairing (C), and owning reliability (D). Passing a part
is your signal to spend your hours on the next one.

**Next step.** Where to go after this module (area 24).

---

## 24. Where to go next

**Level:** all stages

Kubernetes is the platform; these modules are what you run on it and around it. Order them by your
stage and by what work needs next.

| Next | Why | Where |
|---|---|---|
| Monitoring and alerting on the cluster | the alerts that Part D of the exit test needs, kube-state-metrics, SLOs | [Performance & observability](32-learn-performance-observability.md); KodeKloud *Prep Course - Prometheus Certified Associate (PCA)*, Monitoring Kubernetes module ([course](https://kodekloud.com/courses/prometheus-certified-associate-pca)) |
| Deploying to Kubernetes from GitLab CI | pipelines that build, push to Harbor and roll out with a rollback | [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) |
| Rolling, blue/green and canary releases | Traefik and Kubernetes patterns, the Apache to Dokploy cutover | [Deployment patterns](35-deployment-patterns.md) |
| Kubernetes security | Pod Security Admission, audit logs, supply chain, the CKS track | [Security & DevSecOps](37-learn-security-devsecops.md); KodeKloud *Certified Kubernetes Security Specialist (CKS)* ([course](https://kodekloud.com/courses/certified-kubernetes-security-specialist-cks)) and *CKS – Challenges* (free, [course](https://kodekloud.com/courses/cks-challenges)), after the CKA |
| Application side of Kubernetes | probes, multi-container pods and pod design in depth | KodeKloud *Certified Kubernetes Application Developer (CKAD)* ([course](https://kodekloud.com/courses/certified-kubernetes-application-developer-ckad)), after the CKA |
| Databases on Kubernetes | StatefulSets, operators, and when to keep databases on VMs | [Databases for DevOps](38-learn-databases-ops.md) |
| EKS and cloud load balancers | what changes when the cluster runs on AWS | [Cloud & AWS](36-learn-cloud-aws.md) |
| Platform design and HA | failure domains, multi-node Dokploy or Kubernetes, DR | [Senior architecture](39-learn-senior-architecture.md) |
| Your career map | which of this you need for the next stage | [Career ladder](40-career-ladder.md) and the [Roadmap](34-roadmap.md) |
| During a real incident | the short version of this module | [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) and the [Kubernetes reference](15-kubernetes.md) |

**Keep the skill alive.** One random drill a week, an etcd restore and a certificate check every
month, one upgrade per Kubernetes minor release on the homelab, and one real postmortem from
[k8s.af](https://k8s.af/) every Sunday (name the failed layer before you read the root cause).
Per your Ops Ladder, collect no more certificates until the CKA is done: one certificate plus a
public trail of fixed problems says more than a list of badges.
