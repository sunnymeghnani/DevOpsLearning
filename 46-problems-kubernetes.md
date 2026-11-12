# 46 — Real-World Problems: Kubernetes, k3s, Helm, Ingress & GitOps

This module collects 40 problems that engineers really hit when they build and run Kubernetes themselves: kubeadm and k3s/RKE2 clusters on containerd, Calico/Flannel/Cilium networking, CoreDNS, ingress-nginx and Traefik, cert-manager, MetalLB, Longhorn and local-path storage, metrics-server, Helm, Argo CD, Rancher, upgrades, certificate expiry and etcd recovery, with EKS where the answer differs. The problems come from the most-viewed topics on discuss.kubernetes.io, GitHub issues sorted by reactions and comments (k3s, ingress-nginx, cert-manager, MetalLB, Longhorn, Helm, metrics-server, Calico, Rancher, Argo CD, kubernetes/kubernetes), the official docs and the postmortems collected on k8s.af. Stack Overflow and Reddit are reachable through search links. Every command is documented for you to run on your own lab cluster; nothing here was executed on a live system.

---

## 0. How to use this module

[Kubernetes (CKA)](31-learn-kubernetes.md) teaches how the cluster works; [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) walks a live incident from symptom to fix. This module sits between them: it is the library of things that actually break in clusters people build themselves, ordered from the first kubectl command to etcd disaster recovery. Each entry names the CKA domain it exercises, so the library doubles as exam practice: the CKA weights Troubleshooting at 30%, Cluster Architecture, Installation and Configuration at 25%, Services and Networking at 20%, Workloads and Scheduling at 15% and Storage at 10%.

| Stage | Level | Read first | You are there when |
|---|---|---|---|
| Fresher | L0 Foundations | 1.1, 4.1, 8.1 and section 0 of [module 31](31-learn-kubernetes.md) | kubectl talks to a cluster you built, and you can explain why CoreDNS stays Pending until a CNI is installed |
| Junior | L1 Operator | sections 1 and 2, then 6.2, 9.1 and 10.1 | you build a kubeadm or k3s cluster from scratch, join workers, pull from Harbor and expose an app through an Ingress without help |
| Mid-level | L2 Troubleshooter | sections 3–7, 9, 11 and 13.1–13.3 | you bring back a cluster after a reboot, find why pods can't talk across nodes, fix a stuck certificate and restore etcd from a snapshot under time pressure |
| Senior | L3 Platform | 4.2, 5.2, 7.2, 9.2, 13.4, 14.1 and 14.3 | storage, DNS capacity, load balancing and upgrades are designed, monitored and rehearsed rather than repaired |
| Senior/Lead | L4 SRE | 12.2, 13.1, the senior rows of the Self-check | you own the upgrade calendar, the restore drill and the GitOps guard rails, and others learn from your runbooks |

**CKA domains in this module:**

| CKA domain | Entries |
|---|---|
| Troubleshooting (30%) | 1.1, 2.3, 3.1, 3.2, 3.4, 4.1–4.3, 5.1, 9.3 |
| Cluster Architecture, Installation and Configuration (25%) | 1.2, 1.3, 2.1, 2.2, 2.4, 11.1, 11.2, 13.1–13.3 |
| Services and Networking (20%) | 4.4, 5.2, 6.1–6.3, 7.1, 8.1, 8.2, 12.1 |
| Workloads and Scheduling (15%) | 3.3, 10.1 |
| Storage (10%) | 9.1, 9.2, 9.3 |
| Beyond the exam (platform work) | 5.2, 7.2, 7.3, 9.2, 12.2, 13.4, 14.1–14.3 |

**How each problem entry is laid out:** a one-line card (what you see, where, level and career stage, CKA domain, how common it is), then *Why it happens*, *Diagnose* (commands with a realistic sample output), *What the output tells you*, *Fix*, *Why this fix works* (including what not to do), *Prevent it*, *Next step* (handbook module, KodeKloud course, docs) and *Community threads* (verified links plus search links).

**How to practise:** build two labs and snapshot them. Lab A is kubeadm: three Ubuntu 24.04 VMs (cp-1 with 2 vCPU and 4 GB RAM, wk-1 and wk-2 with 2 vCPU and 2 GB RAM), containerd 2.x and Calico or Flannel, as in [31 §3](31-learn-kubernetes.md#3-building-a-kubeadm-homelab-cluster). Lab B is k3s: three small VMs with embedded etcd, so you meet Traefik, ServiceLB and local-path as k3s ships them. Add MetalLB, cert-manager and Longhorn one at a time. Break exactly one thing, fix it using only the entry, then write a five-line note: symptom, evidence, cause, fix, prevention. KodeKloud's CKA labs, the Kubernetes multi-cluster playground and Killercoda work when you have no hardware. Never practise on production.

**On-prem or cloud:** most entries apply everywhere. Where the on-prem and EKS answers genuinely differ (load balancers, storage classes, cluster access, pod IPs), the text is marked 🏢 On-premise or ☁️ Cloud (AWS), and the selector at the top of the page hides the half you don't need. See [On-prem vs cloud paths](55-paths-onprem-vs-cloud.md) for the bigger picture.

**Placeholders and examples:** UPPERCASE words are placeholders (NODE, POD, NS, RELEASE, CLUSTER). The examples use a kubeadm lab with cp-1 (10.20.0.10), wk-1 (10.20.0.21) and wk-2 (10.20.0.22), an API name k8s-api.example.com on the VIP 10.20.0.5, a k3s lab k3s-1 to k3s-3 (10.20.0.30–10.20.0.32), the LAN gateway and DNS server 10.20.0.1, the MetalLB pool 10.20.0.200–10.20.0.220, the router's public address 203.0.113.10 for app.example.com, Harbor at harbor.example.com (10.20.0.50, private CA), pod CIDRs 10.244.0.0/16 (kubeadm) and 10.42.0.0/16 (k3s), service CIDRs 10.96.0.0/12 and 10.43.0.0/16, and the user ops.

> 📚 **Study path:** KodeKloud [*Certified Kubernetes Administrator (CKA)*](https://kodekloud.com/courses/cka-certification-course-certified-kubernetes-administrator) (Install Kubernetes the kubeadm way → Networking → Troubleshooting → Cluster Maintenance) → [*Kubernetes Troubleshooting for Application Developers*](https://kodekloud.com/courses/kubernetes-troubleshooting-for-application-developers) → handbook [Kubernetes (CKA)](31-learn-kubernetes.md) and [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) → [Kubernetes docs](https://kubernetes.io/docs/) and [k3s docs](https://docs.k3s.io/) → lab: build Lab A and Lab B, then work through the Self-check.

---

## 1. kubectl access, kubeconfig and RBAC

The first wall everyone hits: kubectl can't find the cluster, doesn't trust it, or is not allowed to do what you asked. All three are about the kubeconfig: which file, which certificate, which identity.

### 1.1 localhost:8080 refused: no kubeconfig

> **Seen as:** `The connection to the server localhost:8080 was refused - did you specify the right host or port?`, `couldn't get current server API group list: Get "http://localhost:8080/api?timeout=32s"`, or from Helm `Error: Kubernetes cluster unreachable` · **Where:** the first kubectl after kubeadm init, after `sudo -i`, on a worker node, in a CI job, Helm on k3s · **Level:** [L0 · Fresher] · **CKA:** Troubleshooting · **How common:** the most-viewed topic of all time on discuss.kubernetes.io (about 842k views), plus about 160k for the API-group-list variant; k3s #1126 (Helm 3 "cluster unreachable") and #1541 (k3s kubectl prefers /etc/rancher/k3s/k3s.yaml) have 46 and 41 reactions

**Why it happens:** kubectl found no kubeconfig at all, so it fell back to its built-in default of http://localhost:8080, where nothing has listened for years. kubeadm writes the admin credentials to /etc/kubernetes/admin.conf (root only) and expects you to copy them; a worker node only has the kubelet's own kubeconfig; `sudo`, cron and CI jobs don't inherit your KUBECONFIG. k3s and RKE2 write a root-only kubeconfig to /etc/rancher/k3s/k3s.yaml or /etc/rancher/rke2/rke2.yaml. The `k3s kubectl` wrapper reads that file, but Helm and a separately installed kubectl look in ~/.kube/config, which is why kubectl works and Helm doesn't.

**Diagnose:**

```bash
kubectl config view --minify                     # empty clusters/contexts = no kubeconfig loaded
echo "KUBECONFIG=$KUBECONFIG"; ls -l ~/.kube/config
sudo ls -l /etc/kubernetes/admin.conf /etc/rancher/k3s/k3s.yaml /etc/rancher/rke2/rke2.yaml
kubectl get nodes -v=6 2>&1 | grep -E 'Config loaded|GET' | head -3
```

```text
apiVersion: v1
clusters: null
contexts: null
current-context: ""
KUBECONFIG=
ls: cannot access '/home/ops/.kube/config': No such file or directory
-rw------- 1 root root 5653 Oct  2 09:14 /etc/kubernetes/admin.conf
ls: cannot access '/etc/rancher/k3s/k3s.yaml': No such file or directory
I1004 08:02:11.412207   23011 round_trippers.go:553] GET http://localhost:8080/api?timeout=32s  in 0 milliseconds
```

**What the output tells you:** no file was loaded (no "Config loaded from file" line) and the request went to the default localhost:8080. admin.conf exists, so this is a kubeadm control plane where the copy step was skipped. On a worker node, admin.conf would be missing too: run kubectl from the control plane or your workstation instead.

**Fix:**

```bash
# kubeadm control plane: your own copy, owned by you
mkdir -p ~/.kube
sudo cp -i /etc/kubernetes/admin.conf ~/.kube/config
sudo chown "$(id -u):$(id -g)" ~/.kube/config && chmod 600 ~/.kube/config
# k3s (RKE2: /etc/rancher/rke2/rke2.yaml)
sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config
sudo chown "$(id -u):$(id -g)" ~/.kube/config && chmod 600 ~/.kube/config
# From a workstation: the copied file says https://127.0.0.1:6443; point it at the API name
kubectl config set-cluster default --server=https://k8s-api.example.com:6443
# CI: store the kubeconfig as a file-type variable; the job then runs: export KUBECONFIG="$KUBECONFIG_FILE"
```

**Why this fix works:** kubectl and Helm read ~/.kube/config (or KUBECONFIG) and now find a cluster, a CA and a client certificate. Don't make admin.conf or k3s.yaml world-readable (`--write-kubeconfig-mode 644` is for throwaway labs only): it is cluster-admin, and anyone who can read it owns the cluster. Don't copy admin.conf to worker nodes either.

**Prevent it:** give each person their own kubeconfig (a client certificate or OIDC) and CI its own ServiceAccount, name contexts clearly, and show the current context in the shell prompt with kube-ps1 or kubectx.

**Next step:** [Cluster & context sanity](15-kubernetes.md) · [31 §4 kubectl fluency](31-learn-kubernetes.md#4-kubectl-fluency) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Security (kubeconfig) · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [discuss.kubernetes.io: localhost:8080 was refused](https://discuss.kubernetes.io/t/the-connection-to-the-server-localhost-8080-was-refused-did-you-specify-the-right-host-or-port/1464) · [discuss.kubernetes.io: couldn't get current server API group list](https://discuss.kubernetes.io/t/couldnt-get-current-server-api-group-list-get-http-localhost-8080-api-timeout-32s-dial-tcp-127-0-0-1-connect-connection-refused/25471) · [k3s #1126: cluster unreachable with Helm 3](https://github.com/k3s-io/k3s/issues/1126) · [k3s #1541: k3s kubectl prefers k3s.yaml](https://github.com/k3s-io/k3s/issues/1541) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22connection+to+the+server+localhost%3A8080+was+refused%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=localhost%3A8080+refused+kubeconfig&restrict_sr=1)

### 1.2 x509 errors from a remote kubectl

> **Seen as:** `Unable to connect to the server: x509: certificate is valid for 10.96.0.1, 10.20.0.10, not 203.0.113.10`, or `x509: certificate signed by unknown authority` · **Where:** a kubeconfig copied to a laptop or CI and pointed at a VIP, a DNS name or the public address; a kubeconfig kept from before a `kubeadm reset` · **Level:** [L1 · Junior] · **CKA:** Cluster Architecture, Installation and Configuration · **How common:** a classic of every kubeadm and k3s install guide; k3s has a dedicated `--tls-san` flag and kubeadm a `certSANs` field for exactly this

**Why it happens:** the API server's serving certificate lists the names and addresses it may be reached by (its SANs): the advertise address, the first service IP (10.96.0.1), the node name and kubernetes.default. When you connect through anything else, such as a keepalived/kube-vip VIP, a DNS name, a NAT address or an SSH tunnel, TLS verification fails with "valid for X, not Y". "Signed by unknown authority" means the CA embedded in your kubeconfig is not the cluster's CA: the cluster was reset or rebuilt (kubeadm reset creates a new CA), or a TLS-terminating load balancer sits in front of 6443.

**Diagnose:**

```bash
kubectl config view --minify --raw -o jsonpath='{.clusters[0].cluster.server}'; echo
# Which names does the serving certificate actually contain?
openssl s_client -connect k8s-api.example.com:6443 </dev/null 2>/dev/null | openssl x509 -noout -subject -ext subjectAltName
# Does the kubeconfig CA match the cluster CA? (run on cp-1)
sudo openssl x509 -noout -fingerprint -sha256 -in /etc/kubernetes/pki/ca.crt
kubectl config view --minify --raw -o jsonpath='{.clusters[0].cluster.certificate-authority-data}' | base64 -d | openssl x509 -noout -fingerprint -sha256
```

```text
https://k8s-api.example.com:6443
subject=CN=kube-apiserver
X509v3 Subject Alternative Name:
    DNS:cp-1, DNS:kubernetes, DNS:kubernetes.default, DNS:kubernetes.default.svc, DNS:kubernetes.default.svc.cluster.local, IP Address:10.96.0.1, IP Address:10.20.0.10
sha256 Fingerprint=4A:1C:...:9E
sha256 Fingerprint=4A:1C:...:9E
```

**What the output tells you:** the CA fingerprints match, so the trust chain is fine; the certificate simply doesn't list k8s-api.example.com or the VIP 10.20.0.5. If the fingerprints differed, the kubeconfig belongs to an older cluster: fetch a fresh one instead of touching certificates.

**Fix:**

```bash
# kubeadm: add the names to the ClusterConfiguration and re-issue only the serving certificate
kubectl -n kube-system get cm kubeadm-config -o jsonpath='{.data.ClusterConfiguration}' > kubeadm.yaml
#   add under apiServer:   certSANs: ["k8s-api.example.com", "10.20.0.5"]
#   and set:               controlPlaneEndpoint: "k8s-api.example.com:6443"   (new clusters; changing it later is a bigger job)
sudo mv /etc/kubernetes/pki/apiserver.{crt,key} /root/
sudo kubeadm init phase certs apiserver --config kubeadm.yaml
sudo crictl ps --name kube-apiserver -q | xargs -r sudo crictl stop   # kubelet restarts it with the new cert
sudo kubeadm init phase upload-config kubeadm --config kubeadm.yaml  # so upgrades keep the SANs
# k3s: list the extra names in /etc/rancher/k3s/config.yaml, then restart
#   tls-san:
#     - k8s-api.example.com
#     - 10.20.0.5
sudo systemctl restart k3s
```

**Why this fix works:** the new serving certificate is signed by the same CA, so existing kubeconfigs keep working, and it now lists the names you connect by. Uploading the config means the next `kubeadm upgrade` regenerates the certificate with the same SANs. Never "fix" this with `insecure-skip-tls-verify: true`: it removes the only protection against talking to the wrong API server with cluster-admin credentials.

**Prevent it:** decide the API endpoint (VIP plus DNS name) before `kubeadm init` and put it in `controlPlaneEndpoint` and `certSANs` from day one; for k3s, set `tls-san` in config.yaml before the first start.

**Next step:** [31 §3 Building a kubeadm homelab cluster](31-learn-kubernetes.md#3-building-a-kubeadm-homelab-cluster) · [TLS and certificates](18-web-http-tls.md) · KodeKloud: [*TLS Basics*](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics) (CKA, Security) · [k3s server flags](https://docs.k3s.io/cli/server)

**Community threads:** [Kubernetes docs: Troubleshooting kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/) · [k3s docs: server CLI (tls-san)](https://docs.k3s.io/cli/server) · Search: [Stack Overflow](https://stackoverflow.com/search?q=kubectl+x509+%22certificate+is+valid+for%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=x509+certificate+is+valid+for+certSANs&restrict_sr=1)

### 1.3 Forbidden: RBAC denies a user or ServiceAccount

> **Seen as:** `Error from server (Forbidden): deployments.apps is forbidden: User "system:serviceaccount:ci:deployer" cannot list resource "deployments" in API group "apps" in the namespace "shop"` · **Where:** a CI ServiceAccount deploying into another namespace, a new admin with a certificate user, Helm running with a namespace-scoped role · **Level:** [L1 · Junior] · **CKA:** Cluster Architecture, Installation and Configuration (RBAC) · **How common:** daily work; RBAC is a fixed CKA task and one of the KodeKloud troubleshooting scenarios

**Why it happens:** RBAC denies by default, and the error tells you exactly who asked for what: the subject, the verb, the resource, the API group and the namespace. The usual mistakes are a Role created in the ServiceAccount's own namespace instead of the target namespace, a rule written for the core group ("") when Deployments live in "apps", a RoleBinding that names the ServiceAccount without its namespace, or a ClusterRole bound with a RoleBinding (fine, but only for that one namespace). Helm needs rights on everything the chart creates, including Secrets for its release records.

**Diagnose:**

```bash
kubectl auth can-i list deployments.apps -n shop --as system:serviceaccount:ci:deployer
kubectl auth can-i --list -n shop --as system:serviceaccount:ci:deployer | head
kubectl get rolebinding,clusterrolebinding -A -o wide | grep -E 'deployer|NAME'
```

```text
no
Resources                                       Non-Resource URLs   Resource Names   Verbs
selfsubjectreviews.authentication.k8s.io        []                  []               [create]
selfsubjectaccessreviews.authorization.k8s.io   []                  []               [create]
selfsubjectrulesreviews.authorization.k8s.io    []                  []               [create]
NAMESPACE   NAME              ROLE                AGE   USERS   GROUPS   SERVICEACCOUNTS
ci          deployer-access   Role/app-deployer   3d                     ci/deployer
```

**What the output tells you:** the only binding lives in namespace ci, so the ServiceAccount can deploy into ci and nowhere else. It has no rights at all in shop, which is exactly what the error said.

**Fix:**

```yaml
# rbac-shop.yaml: the Role and the binding live in the TARGET namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: app-deployer, namespace: shop }
rules:
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["services", "configmaps", "secrets", "pods"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: ci-deployer, namespace: shop }
subjects:
  - { kind: ServiceAccount, name: deployer, namespace: ci }
roleRef: { apiGroup: rbac.authorization.k8s.io, kind: Role, name: app-deployer }
```

**Why this fix works:** a RoleBinding grants rights only in its own namespace, so it must live in shop, while its subject points back at the ServiceAccount in ci. Check again with `kubectl auth can-i` before rerunning the pipeline. Don't bind cluster-admin to a CI account "to get it working": a leaked CI token then owns the whole cluster.

**Prevent it:** keep RBAC manifests in Git next to the namespace definition, add `kubectl auth can-i` checks to the pipeline, and review who has cluster-admin every quarter (`kubectl get clusterrolebinding -o wide | grep cluster-admin`).

**Next step:** [31 §14 RBAC and ServiceAccounts](31-learn-kubernetes.md#14-rbac-and-serviceaccounts) · KodeKloud: *Kubernetes Troubleshooting for Application Developers* — RBAC scenario · *Certified Kubernetes Administrator (CKA)* — Security · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=%22cannot+list+resource%22+forbidden+serviceaccount) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=rbac+forbidden+serviceaccount+rolebinding&restrict_sr=1) · [kubernetes/kubernetes issues on RBAC forbidden](https://github.com/kubernetes/kubernetes/issues?q=is%3Aissue+rbac+forbidden+serviceaccount)

---

## 2. Building the cluster: kubeadm, k3s and containerd

Most "my new cluster doesn't work" threads come down to four things: the container runtime is not configured for Kubernetes, a node can't join, a node announces the wrong address, or images can't be pulled from your registry.

### 2.1 kubeadm init fails: CRI disabled or wrong cgroup driver

> **Seen as:** `[ERROR CRI]: container runtime is not running: ... rpc error: code = Unimplemented desc = unknown service runtime.v1.RuntimeService`; or init succeeds, then kube-apiserver, etcd and the scheduler restart every few minutes and `The connection to the server 10.20.0.10:6443 was refused` comes and goes · **Where:** a fresh Ubuntu 22.04/24.04 node with containerd.io from Docker's apt repository or Ubuntu's containerd package · **Level:** [L1 · Junior] · **CKA:** Cluster Architecture, Installation and Configuration · **How common:** a classic of CKA labs and homelabs; the Kubernetes container-runtimes page warns that containerd installed from a package may ship with the CRI plugin disabled

**Why it happens:** the config.toml packaged with containerd.io is written for Docker, which doesn't need CRI, so it contains `disabled_plugins = ["cri"]` and kubeadm can't talk to the runtime at all. Once CRI is on, the second trap is the cgroup driver: kubeadm configures the kubelet with `cgroupDriver: systemd`, while containerd's default runc options use cgroupfs (`SystemdCgroup = false`). Two managers then fight over the same cgroups on a cgroup v2 host, and the control-plane static pods are killed and restarted in a loop. Recent kubelets can ask containerd 2.x which driver it uses, but you still need both set to systemd.

**Diagnose:**

```bash
sudo crictl --runtime-endpoint unix:///run/containerd/containerd.sock info > /dev/null && echo "CRI OK"
grep -nE '^version|disabled_plugins|SystemdCgroup' /etc/containerd/config.toml
stat -fc %T /sys/fs/cgroup                                   # cgroup2fs = cgroup v2
sudo grep cgroupDriver /var/lib/kubelet/config.yaml
sudo crictl ps -a --name 'kube-apiserver|etcd' | head -4     # ATTEMPT climbing = restart loop
```

```text
E1004 08:41:02.118604  4410 remote_runtime.go:...] "validate service connection: validate CRI v1 runtime API for endpoint \"unix:///run/containerd/containerd.sock\": rpc error: code = Unimplemented desc = unknown service runtime.v1.RuntimeService"
14:disabled_plugins = ["cri"]
cgroup2fs
cgroupDriver: systemd
```

**What the output tells you:** the CRI plugin is disabled in the packaged file, so nothing else can work yet. After you regenerate the file, run the last command again: an ATTEMPT count of 10 or more for kube-apiserver or etcd within an hour, with `SystemdCgroup = false` in the config, is the cgroup-driver fight.

**Fix:**

```bash
# Replace the Docker-oriented file with containerd's full default
sudo mkdir -p /etc/containerd
containerd config default | sudo tee /etc/containerd/config.toml > /dev/null
# Use the systemd cgroup driver for runc; check the line exists under the runc options table
sudo sed -i 's/SystemdCgroup = false/SystemdCgroup = true/' /etc/containerd/config.toml
grep -n -B4 'SystemdCgroup' /etc/containerd/config.toml
sudo systemctl restart containerd
# If kubeadm init already half-ran, start clean
sudo kubeadm reset -f
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=10.20.0.10
```

**Why this fix works:** the generated default enables CRI and matches the containerd version you actually run. containerd 2.x writes config `version = 3` with different plugin names than 1.7's version 2, which is why pasting an old snippet from a blog into a new file silently does nothing. With both sides on systemd, a single cgroup manager owns the pods and the restarts stop. Don't work around it by switching the host back to cgroup v1: recent kubelets refuse to start on cgroup v1 by default.

**Prevent it:** template config.toml with Ansible, pin the containerd version with `apt-mark hold`, and run `kubeadm init phase preflight` on every new node image. Plan the move to containerd 2.x: the Kubernetes docs say the kubelet's fallback for containerd 1.x is dropped in v1.38.

**Next step:** [31 §3 Building a kubeadm homelab cluster](31-learn-kubernetes.md#3-building-a-kubeadm-homelab-cluster) · [Docker & containers](14-docker-containers.md) · KodeKloud: [*Docker vs ContainerD*](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Core-Concepts/Docker-vs-ContainerD/page) · [*Solution: Install a Kubernetes Cluster using kubeadm*](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Install-Kubernetes-the-kubeadm-way/Lab-Solution-Install-a-Kubernetes-Cluster-using-kubeadm/page) · [Container runtimes docs](https://kubernetes.io/docs/setup/production-environment/container-runtimes/)

**Community threads:** [Kubernetes docs: Container Runtimes](https://kubernetes.io/docs/setup/production-environment/container-runtimes/) · [Kubernetes docs: Troubleshooting kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22unknown+service+runtime.v1.RuntimeService%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=SystemdCgroup+apiserver+restarting&restrict_sr=1)

### 2.2 kubeadm join fails: token, preflight or clone

> **Seen as:** `couldn't validate the identity of the API Server: ... token id "x7k2pq" is invalid for this cluster or it has expired`, `[ERROR Port-10250]: Port 10250 is in use`, `[ERROR FileContent--proc-sys-net-ipv4-ip_forward]: /proc/sys/net/ipv4/ip_forward contents are not set to 1`, or `a Node with name "wk-1" and status "Ready" already exists in the cluster` · **Where:** adding a worker a day after init, re-joining a rebuilt node, VMs cloned from one template · **Level:** [L1 · Junior] · **CKA:** Cluster Architecture, Installation and Configuration · **How common:** discuss.kubernetes.io "Kubeadm init fails" (33k views), "Not able to join node to Master" (31k) and "Kubeadm init failed api server not healthy" (14k)

**Why it happens:** the join command printed by `kubeadm init` contains a bootstrap token that expires after 24 hours. A node that joined before still runs a kubelet on 10250 and has /etc/kubernetes/kubelet.conf, so preflight refuses. Fresh Ubuntu has IP forwarding off and br_netfilter not loaded. VMs cloned from one template share a hostname, /etc/machine-id or even a product_uuid, and the second node with the same name overwrites or is refused by the first. A host firewall that blocks 6443 from the workers makes join hang at discovery.

**Diagnose:**

```bash
# cp-1: is there still a valid token?
sudo kubeadm token list
# worker: reachability, leftovers and prerequisites
nc -vz -w3 10.20.0.10 6443
sudo ss -ltnp 'sport = :10250'
sysctl net.ipv4.ip_forward; lsmod | grep -c br_netfilter; swapon --show
hostnamectl --static; cat /etc/machine-id
```

```text
Connection to 10.20.0.10 6443 port [tcp/*] succeeded!
LISTEN 0 4096 *:10250 *:* users:(("kubelet",pid=812,fd=21))
net.ipv4.ip_forward = 0
0
wk-1
5f0c2e7a9b1d4e3f8a6c0b2d1e4f7a9c
```

**What the output tells you:** `kubeadm token list` printed nothing, so every token has expired. The API port is reachable, but a kubelet from an earlier attempt still owns 10250, forwarding is off and br_netfilter is not loaded. If wk-2 prints the same machine-id, the VMs are clones.

**Fix:**

```bash
# cp-1: a fresh token and the exact command to run
sudo kubeadm token create --print-join-command
# cp-1: a rebuilt node keeps its old Node object; remove it first
kubectl delete node wk-1
# worker: clean up an earlier attempt
sudo kubeadm reset -f && sudo rm -rf /etc/cni/net.d && sudo systemctl restart containerd
# worker: kernel prerequisites, persisted across reboots
printf 'overlay\nbr_netfilter\n' | sudo tee /etc/modules-load.d/k8s.conf
sudo modprobe overlay && sudo modprobe br_netfilter
printf 'net.ipv4.ip_forward = 1\nnet.bridge.bridge-nf-call-iptables = 1\n' | sudo tee /etc/sysctl.d/k8s.conf
sudo sysctl --system
# cloned VM: unique identity
sudo rm /etc/machine-id && sudo systemd-machine-id-setup && sudo hostnamectl set-hostname wk-2
# then paste the join command printed on cp-1
```

**Why this fix works:** a new token passes discovery; the ca-cert-hash in the printed command pins the cluster CA, so the worker can't be tricked into joining another API server. Reset removes the old kubelet identity, and the sysctls give pods a forwarding path. Don't create tokens with `--ttl 0` and keep them in a wiki: anyone holding one can join a node to your cluster.

**Prevent it:** join nodes with an Ansible role that creates a fresh token per run, build VM templates with an empty /etc/machine-id, and keep the port list in [Who owns this port?](22-playbook-ports-inventory.md) up to date (6443, 10250, 2379–2380, plus your CNI's ports).

**Next step:** [31 §3 Building a kubeadm homelab cluster](31-learn-kubernetes.md#3-building-a-kubeadm-homelab-cluster) · KodeKloud: [*Introduction to Deployment with kubeadm*](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Install-Kubernetes-the-kubeadm-way/Deployment-With-kubeadm-Introduction/page) · [*Worker Node Failure*](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Worker-Node-Failure) · [Troubleshooting kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/)

**Community threads:** [discuss.kubernetes.io: Kubeadm init fails](https://discuss.kubernetes.io/t/kubeadm-init-fails/16888) · [discuss.kubernetes.io: Not able to join node to Master](https://discuss.kubernetes.io/t/not-able-to-join-node-to-master/7123) · [discuss.kubernetes.io: Kubeadm init failed api server not healthy](https://discuss.kubernetes.io/t/kubeadm-init-failed-api-server-not-healthy/28097) · Search: [Stack Overflow](https://stackoverflow.com/search?q=kubeadm+join+%22token+id%22+%22invalid+for+this+cluster%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=kubeadm+join+preflight+error&restrict_sr=1)

### 2.3 Nodes register with the wrong IP

> **Seen as:** every node shows the same INTERNAL-IP (10.0.2.15 under Vagrant) or the backup-network address; `Error from server: error dialing backend: dial tcp 10.0.2.15:10250: connect: connection refused` for `kubectl logs` and `exec`; pods on different nodes can't reach each other · **Where:** Vagrant/VirtualBox labs, on-prem servers with separate management, storage or backup NICs · **Level:** [L2 · Mid] · **CKA:** Troubleshooting · **How common:** the kubeadm troubleshooting docs give it two sections (the NIC Flannel picks under Vagrant, and a non-public IP used for containers)

**Why it happens:** the kubelet registers the address of the interface that holds the default route, and Flannel and Calico autodetect the first usable interface. On VirtualBox the NAT adapter (10.0.2.15 on every VM) holds the default route; on a server with several NICs, the default route may sit on a network the other nodes can't reach. The API server then dials the wrong address for logs and exec, and the overlay tunnels are built over the wrong network.

**Diagnose:**

```bash
kubectl get nodes -o wide
ip -br -4 addr; ip -4 route get 1.1.1.1
kubectl -n kube-flannel logs ds/kube-flannel-ds | grep -i 'using interface'
```

```text
NAME   STATUS   ROLES           AGE   VERSION   INTERNAL-IP   EXTERNAL-IP   OS-IMAGE
cp-1   Ready    control-plane   2d    v1.35.3   10.0.2.15     <none>        Ubuntu 24.04.3 LTS
wk-1   Ready    <none>          2d    v1.35.3   10.0.2.15     <none>        Ubuntu 24.04.3 LTS
lo               UNKNOWN        127.0.0.1/8
enp0s3           UP             10.0.2.15/24
enp0s8           UP             10.20.0.21/24
1.1.1.1 via 10.0.2.2 dev enp0s3 src 10.0.2.15 uid 1000
I1004 09:12:40.218331       1 main.go:...] Using interface with name enp0s3 and address 10.0.2.15
```

**What the output tells you:** both nodes claim 10.0.2.15 because enp0s3 (the NAT adapter) holds the default route; the cluster network is enp0s8 (10.20.0.0/24), and Flannel picked the wrong one too.

**Fix:**

```bash
# Every node: register the cluster-network address
echo 'KUBELET_EXTRA_ARGS=--node-ip=10.20.0.21' | sudo tee /etc/default/kubelet
sudo systemctl restart kubelet
# New clusters: put it in the kubeadm config (v1beta4 takes a name/value list)
#   nodeRegistration:
#     kubeletExtraArgs:
#       - name: node-ip
#         value: "10.20.0.21"
#   and init with --apiserver-advertise-address=10.20.0.10
# Flannel: add to the kube-flannel container args, then let the DaemonSet restart its pods
#   - --iface=enp0s8
# Calico (operator): in the Installation resource
#   spec.calicoNetwork.nodeAddressAutodetectionV4: { cidrs: ["10.20.0.0/24"] }
```

**Why this fix works:** the kubelet now advertises an address every node can reach, so the API server can dial port 10250 for logs and exec, and the CNI builds its tunnels on the right network. Selecting by CIDR survives interface renames better than by name.

**Prevent it:** keep node-ip in the kubeadm config file you store in Git; in Vagrantfiles give each VM a private_network IP and template node-ip from it; after adding a node, check `kubectl get nodes -o wide` before scheduling anything there.

**Next step:** [Network commands](02-network.md) · [26 §10 nodes, storage and control plane](26-playbook-containers-k8s.md#10-kubernetes-nodes-storage-and-control-plane) · KodeKloud: [*Troubleshooting Internal Networking*](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Services/Troubleshooting-Internal-Networking/page) (Kubernetes Networking Deep Dive) · [Troubleshooting kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/)

**Community threads:** [Kubernetes docs: Troubleshooting kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=kubernetes+node+internal+ip+10.0.2.15+vagrant) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=node-ip+wrong+interface&restrict_sr=1)

### 2.4 Images: crictl, ctr and Harbor's private CA

> **Seen as:** `Failed to pull image "harbor.example.com/shop/web:1.4.3": ... tls: failed to verify certificate: x509: certificate signed by unknown authority`; `ErrImageNeverPull` for an image you built on the node with docker; crictl warning about deprecated default endpoints · **Where:** kubeadm nodes on containerd and k3s nodes pulling from Harbor with your private CA · **Level:** [L1 · Junior] · **CKA:** Cluster Architecture, Installation and Configuration · **How common:** k3s #145 "Insecure Registry Support" (33 reactions, 39 comments); "Image Pull Errors" is the first KodeKloud troubleshooting scenario

**Why it happens:** Kubernetes uses containerd, not Docker. They keep separate image stores, so an image built with `docker build` on the node doesn't exist for the kubelet; ctr shows nothing because its default namespace is "default" while Kubernetes uses "k8s.io". containerd doesn't read /etc/docker/certs.d: it trusts a private registry through /etc/containerd/certs.d/HOST/hosts.toml (when the CRI `config_path` points there) or through the system CA store after a restart. k3s generates its containerd config at every start from /etc/rancher/k3s/registries.yaml, so edits to its config.toml are lost.

**Diagnose:**

```bash
sudo crictl images | grep shop                     # the kubelet's image store
sudo ctr -n k8s.io images ls -q | grep shop         # the same store through ctr: note -n k8s.io
docker images | grep shop                           # Docker's separate store, if Docker is installed
kubectl -n shop describe pod web-7c9d5b7f9-x2kqp | sed -n '/Events:/,$p' | tail -3
grep -n 'config_path' /etc/containerd/config.toml
```

```text
harbor.example.com/shop/web   1.4.2   3f1a2b7c9d0e   38 hours ago   112MB
  Warning  Failed   14s   kubelet  Failed to pull image "harbor.example.com/shop/web:1.4.3": failed to pull and unpack image "harbor.example.com/shop/web:1.4.3": failed to resolve reference "harbor.example.com/shop/web:1.4.3": failed to do request: Head "https://harbor.example.com/v2/shop/web/manifests/1.4.3": tls: failed to verify certificate: x509: certificate signed by unknown authority
  Warning  Failed   14s   kubelet  Error: ErrImagePull
      config_path = ''
```

**What the output tells you:** crictl and ctr print nothing, so containerd has no shop image at all; only Docker's store has 1.4.2. The pull of 1.4.3 fails on trust, not on credentials (that would be 401 Unauthorized), and containerd has no registry configuration directory to find a CA in.

**Fix:**

```bash
# crictl: name the endpoint once
printf 'runtime-endpoint: unix:///run/containerd/containerd.sock\nimage-endpoint: unix:///run/containerd/containerd.sock\n' | sudo tee /etc/crictl.yaml
# kubeadm nodes: trust the private CA for this registry only
sudo mkdir -p /etc/containerd/certs.d/harbor.example.com
sudo cp example-ca.crt /etc/containerd/certs.d/harbor.example.com/ca.crt
cat <<'EOF' | sudo tee /etc/containerd/certs.d/harbor.example.com/hosts.toml
server = "https://harbor.example.com"
[host."https://harbor.example.com"]
  capabilities = ["pull", "resolve"]
  ca = "/etc/containerd/certs.d/harbor.example.com/ca.crt"
EOF
#   in config.toml, CRI registry section: config_path = "/etc/containerd/certs.d"
sudo systemctl restart containerd
# k3s: /etc/rancher/k3s/registries.yaml on EVERY node, then restart k3s or k3s-agent
#   configs:
#     "harbor.example.com":
#       tls:
#         ca_file: /etc/ssl/certs/example-ca.crt
# Private Harbor projects: a pull secret per namespace, using a robot account
kubectl -n shop create secret docker-registry harbor-pull --docker-server=harbor.example.com \
  --docker-username='robot$shop+puller' --docker-password="$HARBOR_ROBOT_TOKEN"
```

**Why this fix works:** containerd looks up hosts.toml per registry and verifies Harbor's certificate against your CA, so TLS stays on. Images built locally belong in Harbor (or, on a one-node lab only, `docker save web:dev | sudo ctr -n k8s.io images import -` with `imagePullPolicy: IfNotPresent`). Don't use `skip_verify`, plain HTTP or a k3s "insecure registry": a tampered image then runs with whatever privileges the pod has.

**Prevent it:** distribute the CA and the registry files with Ansible to every node, including the ones you add next year; use one Harbor robot account per namespace; pre-pull a test image from Harbor as part of node acceptance.

**Next step:** [30 §11 Registries and Harbor](30-learn-docker.md#11-registries-and-harbor) · [31 §17 Private registries and Harbor](31-learn-kubernetes.md#17-private-registries-and-harbor) · KodeKloud: *Kubernetes Troubleshooting for Application Developers* — Image Pull Errors · [k3s private registry docs](https://docs.k3s.io/installation/private-registry)

**Community threads:** [k3s #145: Insecure Registry Support](https://github.com/k3s-io/k3s/issues/145) · [k3s docs: Private Registry Configuration](https://docs.k3s.io/installation/private-registry) · Search: [Stack Overflow](https://stackoverflow.com/search?q=containerd+harbor+x509+%22certificate+signed+by+unknown+authority%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=containerd+private+registry+x509+hosts.toml&restrict_sr=1)

---

## 3. Nodes and the control plane

These are the "it worked yesterday" problems: the API server is gone after a reboot, a node flaps between Ready and NotReady, the kubelet starts evicting pods, or something refuses to finish deleting. The CKA troubleshooting tasks live here.

### 3.1 API server refused on 6443 after a reboot

> **Seen as:** `The connection to the server 10.20.0.10:6443 was refused - did you specify the right host or port?` after a reboot, a power cut, an OS update, a full disk or a network change · **Where:** kubeadm clusters with one control-plane node, where everything stops with it · **Level:** [L2 · Mid] · **CKA:** Troubleshooting · **How common:** the second most-viewed topic on discuss.kubernetes.io (about 592k views) plus a 47k-view variant; kubeadm #1026 "kubelet won't restart after reboot" (67 comments); "How to shut down and restart Kubernetes clusters?" has about 110k views

**Why it happens:** on kubeadm, the API server is a static pod, so the chain is containerd → kubelet → etcd → kube-apiserver, and a break anywhere looks the same from kubectl. The usual breaks: swap came back from /etc/fstab and the kubelet refuses to start; containerd didn't start; etcd can't start because the disk is full, its data is damaged or the node's IP changed (DHCP or a netplan edit) and etcd can no longer bind the address in its manifest; the control-plane certificates expired after a year (13.2); or a cgroup-driver mismatch (2.1).

**Diagnose:**

```bash
sudo systemctl is-active containerd kubelet
sudo journalctl -u kubelet -b --no-pager | grep -E '^.{16}.*E[0-9]{4}' | tail -2
sudo crictl ps -a --name 'kube-apiserver|etcd'
sudo crictl logs --tail 1 "$(sudo crictl ps -a --name etcd -q | head -1)"
swapon --show; df -h /var/lib/etcd | tail -1; ip -4 -br addr show enp0s8
sudo grep -h -- '--advertise-address\|--listen-client-urls' /etc/kubernetes/manifests/{kube-apiserver,etcd}.yaml
```

```text
active
active
Oct 04 07:58:13 cp-1 kubelet[905]: E1004 07:58:13.019226 905 controller.go:...] "Failed to ensure lease exists, will retry" err="Get \"https://10.20.0.10:6443/apis/coordination.k8s.io/v1/namespaces/kube-node-lease/leases/cp-1?timeout=10s\": dial tcp 10.20.0.10:6443: connect: no route to host"
CONTAINER       IMAGE           CREATED          STATE    NAME             ATTEMPT   POD ID
c41e0a9d7b2f1   a9e7e6b294baf   20 seconds ago   Exited   etcd             23        8d1f6c2e0b7a4
6e2b9c1f0a7d4   9f8d2c1a07e51   35 seconds ago   Exited   kube-apiserver   21        2a7c9e1d4f3b8
{"level":"fatal","ts":"2026-10-04T07:58:20.118Z","caller":"etcdmain/etcd.go:204","msg":"discovery failed","error":"listen tcp 10.20.0.10:2380: bind: cannot assign requested address"}
/dev/mapper/ubuntu--vg-root   38G   14G   22G  39% /
enp0s8           UP             10.20.0.14/24
    - --advertise-address=10.20.0.10
    - --listen-client-urls=https://127.0.0.1:2379,https://10.20.0.10:2379
```

**What the output tells you:** containerd and the kubelet run, swap is off and the disk has room. etcd exits because the node now has 10.20.0.14 (DHCP gave it a new lease) while every manifest and certificate says 10.20.0.10; without etcd, the API server exits too.

**Fix:**

```yaml
# /etc/netplan/50-cloud-init.yaml: give the control plane its address back (or a DHCP reservation)
network:
  version: 2
  ethernets:
    enp0s8:
      dhcp4: false
      addresses: [10.20.0.10/24]
      routes: [{ to: default, via: 10.20.0.1 }]
      nameservers: { addresses: [10.20.0.1] }
```

```bash
sudo netplan apply
# Other links in the same chain:
sudo swapoff -a && sudo sed -i '/\sswap\s/ s/^/#/' /etc/fstab     # swap came back
sudo systemctl restart containerd kubelet
sudo kubeadm certs check-expiration                                  # expired? see 13.2
# Watch the static pods come back, then ask the API server itself
sudo crictl ps --name 'etcd|kube-apiserver'
kubectl get --raw='/readyz?verbose' | tail -3
```

**Why this fix works:** the static pod manifests, the etcd member list and the serving certificates all carry the old address, so restoring the address is one change while re-addressing a kubeadm control plane means new certificates and an etcd member update. Never run `kubeadm reset` on a control plane to "fix" this: it deletes the local etcd data, which is the cluster.

**Prevent it:** static addresses or DHCP reservations for every node, an etcd snapshot before any maintenance (13.3), and an orderly power cycle: drain or stop workers first, then the control plane; power on the control plane first, wait for `kubectl get nodes`, then start the workers. Set `shutdownGracePeriod` in the kubelet config so pods stop cleanly when a node shuts down.

**Next step:** [26 §10 nodes, storage and control plane](26-playbook-containers-k8s.md#10-kubernetes-nodes-storage-and-control-plane) · [31 §20 The troubleshooting method](31-learn-kubernetes.md#20-the-troubleshooting-method) · KodeKloud: [*Control Plane Failure*](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Troubleshooting/Control-Plane-Failure/page) · [Troubleshooting kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/)

**Community threads:** [discuss.kubernetes.io: HOST:6443 was refused](https://discuss.kubernetes.io/t/the-connection-to-the-server-host-6443-was-refused-did-you-specify-the-right-host-or-port/552) · [discuss.kubernetes.io: 192.168.1.2:6443 was refused](https://discuss.kubernetes.io/t/the-connection-to-the-server-192-168-1-2-6443-was-refused-did-you-specify-the-right-host-or-port/22260) · [kubeadm #1026: kubelet won't restart after reboot](https://github.com/kubernetes/kubeadm/issues/1026) · [discuss.kubernetes.io: How to shut down and restart Kubernetes clusters?](https://discuss.kubernetes.io/t/how-to-shut-down-and-restart-kubernetes-clusters/5395) · Search: [Server Fault](https://serverfault.com/search?q=%22connection+to+the+server%22+6443+refused) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=6443+refused+after+reboot&restrict_sr=1)

### 3.2 Node NotReady or flapping

> **Seen as:** a node shows `NotReady`, or flips between Ready and NotReady; `PLEG is not healthy: pleg was last seen active 3m4.118s ago; threshold is 3m0s`; `Kubelet stopped posting node status`; its pods turn Unknown and are recreated elsewhere a few minutes later · **Where:** busy workers, small k3s nodes, nodes after a link flap · **Level:** [L2 · Mid] · **CKA:** Troubleshooting · **How common:** kubernetes #45419 PLEG flapping (249 comments, 109 reactions), #87615 kubelet won't reconnect after a NIC failure (163 comments), k3s #294 high load average (71 comments)

**Why it happens:** Ready means the kubelet renews its heartbeat (a Lease every 10 seconds) and reports itself healthy. It stops being healthy when the kubelet is down (crash, swap, an expired client certificate) or when the runtime stops answering: the PLEG (pod lifecycle event generator) relists all containers, and if that takes longer than 3 minutes the kubelet declares itself not ready. Slow relists come from a saturated disk, too many containers, or a hung NFS mount. A broken path to the API server has the same effect, including a stale HTTP/2 connection after a NIC failure that older kubelets never re-dialled. Small k3s nodes on SD cards or thin disks hit it through IO load.

**Diagnose:**

```bash
kubectl describe node wk-2 | sed -n '/Conditions:/,/Addresses:/p' | grep -E 'Ready|Pressure'
# on wk-2
systemctl is-active kubelet containerd
sudo journalctl -u kubelet --since '-30min' --no-pager | grep -iE 'pleg|certificate|closed network' | tail -2
time sudo crictl ps -q | wc -l
iostat -x 2 2 | grep -E 'Device|sda'      # sample below keeps only the useful columns
```

```text
  MemoryPressure   False   Sat, 04 Oct 2026 10:14:31 +0000   KubeletHasSufficientMemory   kubelet has sufficient memory available
  DiskPressure     False   Sat, 04 Oct 2026 10:14:31 +0000   KubeletHasNoDiskPressure     kubelet has no disk pressure
  Ready            False   Sat, 04 Oct 2026 10:14:31 +0000   KubeletNotReady              PLEG is not healthy: pleg was last seen active 3m4.118s ago; threshold is 3m0s
active
active
Oct 04 10:14:31 wk-2 kubelet[1022]: I1004 10:14:31.208411 1022 kubelet.go:...] "Skipping pod synchronization" err="PLEG is not healthy: pleg was last seen active 3m4.118s ago; threshold is 3m0s"
143

real	0m41.902s
Device   r/s    w/s     rkB/s   wkB/s     r_await  w_await  aqu-sz  %util
sda      12.0   410.5   96.0    52310.2   48.1     187.4    61.3    99.6
```

**What the output tells you:** both services run, but listing 143 containers takes 42 seconds and the disk is 99.6% busy with 187 ms write waits. containerd is starved of IO, so the PLEG relist misses its 3-minute deadline. A log line with "certificate has expired" would send you to 13.2; "use of closed network connection" after a link flap points to the stale-connection bug: restart the kubelet and upgrade.

**Fix:**

```bash
# Find the IO hog (a log-heavy pod, a backup job, image pulls) and stop or move it
sudo iotop -boPa -d 5 -n 3 | head -12        # -b (batch) is required when the output goes to a pipe
# Reserve room for the system so pods can't starve the kubelet (KubeletConfiguration; k3s: kubelet-arg)
#   systemReserved: { cpu: 500m, memory: 512Mi }
#   kubeReserved:   { cpu: 500m, memory: 512Mi }
#   evictionHard:   { memory.available: "300Mi", nodefs.available: "10%", imagefs.available: "15%", nodefs.inodesFree: "5%" }
#   (list every signal: once you set evictionHard, the ones you leave out are not defaulted but set to zero)
sudo systemctl restart containerd && sudo systemctl restart kubelet
kubectl get node wk-2 -w
```

**Why this fix works:** once the disk has headroom, relists complete in seconds and the kubelet reports Ready again; the reservations keep CPU and memory for the kubelet and containerd when pods misbehave. Don't raise the PLEG threshold or the node-monitor grace period to hide it: the node is genuinely unable to manage its pods during those minutes.

**Prevent it:** put /var/lib/containerd on SSD or its own volume, cap pods per node at what the disk can serve, rotate container logs (3.3), and alert on Ready flaps (`kube_node_status_condition` in [Observability problems](49-observability-stack-problems.md)).

**Next step:** [Slow system playbook](23-playbook-slow-system.md) · [26 §10 nodes, storage and control plane](26-playbook-containers-k8s.md#10-kubernetes-nodes-storage-and-control-plane) · KodeKloud: [*Worker Node Failure*](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Troubleshooting/Worker-Node-Failure) · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [kubernetes #45419: Node flapping with PLEG issues](https://github.com/kubernetes/kubernetes/issues/45419) · [kubernetes #87615: kubelet won't reconnect after NIC failure](https://github.com/kubernetes/kubernetes/issues/87615) · [k3s #294: high load average](https://github.com/k3s-io/k3s/issues/294) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22PLEG+is+not+healthy%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=node+NotReady+PLEG&restrict_sr=1)

### 3.3 DiskPressure: evictions and image garbage collection

> **Seen as:** pods `Evicted` with `The node was low on resource: ephemeral-storage`; the taint `node.kubernetes.io/disk-pressure:NoSchedule`; new pods Pending · **Where:** nodes with a 20–40 GB root disk that holds /var/lib/containerd and the logs, k3s nodes, CI-heavy clusters with many image tags · **Level:** [L2 · Mid] · **CKA:** Workloads and Scheduling (evictions and taints) · **How common:** an everyday operations ticket; k3s #14729 (2026) tracked a DiskPressure condition that stayed True for hours after space was freed

**Why it happens:** the kubelet watches two filesystems: nodefs (/var/lib/kubelet and the pod logs) and imagefs (/var/lib/containerd). Below the hard eviction thresholds (by default nodefs.available under 10%, imagefs.available under 15%, inodes under 5%) it taints the node and evicts pods, starting with those using the most ephemeral storage above their requests. Image garbage collection only starts at 85% usage and only deletes images no container uses. Container logs, emptyDir volumes without a size limit and writable layers all count. Evicted pods stay behind as Failed objects until someone deletes them.

**Diagnose:**

```bash
kubectl describe node wk-1 | grep -E 'DiskPressure|Taints'
# on wk-1
df -h / | tail -1
sudo du -xsh /var/lib/containerd /var/lib/kubelet /var/log/pods /var/log/journal 2>/dev/null
sudo crictl images -q | wc -l
kubectl get pods -A --field-selector=status.phase=Failed | head -3
```

```text
  DiskPressure     True    Sat, 04 Oct 2026 11:02:07 +0000   KubeletHasDiskPressure       kubelet has disk pressure
Taints:             node.kubernetes.io/disk-pressure:NoSchedule
/dev/mapper/ubuntu--vg-root   38G   35G  1.6G  96% /
21G	/var/lib/containerd
2.1G	/var/lib/kubelet
6.8G	/var/log/pods
3.9G	/var/log/journal
212
NAMESPACE   NAME                     READY   STATUS    RESTARTS   AGE
batch       report-28771140-zx2lm    0/1     Evicted   0          47m
shop        web-7c9d5b7f9-4kq8d      0/1     Evicted   0          44m
```

**What the output tells you:** images, pod logs and the journal share one 38 GB root disk. 212 images means every CI tag ever deployed is still cached, and 6.8 GB of pod logs means one or two very chatty containers.

**Fix:**

```bash
sudo crictl rmi --prune                          # images no container uses
sudo journalctl --vacuum-size=500M
sudo du -sh /var/log/pods/* | sort -h | tail -3  # the chatty pods: fix their log level
kubectl delete pods -A --field-selector=status.phase=Failed
# KubeletConfiguration (k3s: kubelet-arg in /etc/rancher/k3s/config.yaml)
#   containerLogMaxSize: 20Mi
#   containerLogMaxFiles: 3
#   imageGCHighThresholdPercent: 75
#   imageGCLowThresholdPercent: 60
# Workloads: cap what one pod may write
#   resources: { requests: { ephemeral-storage: 500Mi }, limits: { ephemeral-storage: 2Gi } }
#   volumes:   - name: scratch
#                emptyDir: { sizeLimit: 1Gi }
```

**Why this fix works:** pruning frees the cache without touching running containers, lower GC thresholds keep it from refilling, and ephemeral-storage limits make the kubelet evict the one offending pod instead of the whole node going under pressure. If the condition stays True after the disk is back under the threshold, restart the kubelet (or k3s-agent) and upgrade; that is the latch k3s #14729 describes. Don't `rm -rf` inside /var/lib/containerd while containers run: you corrupt the content store and every pod on the node with it.

**Prevent it:** give /var/lib/containerd its own logical volume, alert at 80% disk usage, set a tag-retention policy in Harbor, and keep log levels at info in production.

**Next step:** [Storage & disk](01-storage-disk.md) · [26 §8 pods that will not run](26-playbook-containers-k8s.md#8-kubernetes-pods-that-will-not-run) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Scheduling (taints and tolerations) · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [k3s #14729: DiskPressure latches True after nodefs recovers](https://github.com/k3s-io/k3s/issues/14729) · Search: [Stack Overflow](https://stackoverflow.com/search?q=kubernetes+DiskPressure+evicted+ephemeral-storage) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=disk+pressure+evicted+image+garbage+collection&restrict_sr=1)

### 3.4 Pods or namespaces stuck Terminating

> **Seen as:** `kubectl delete ns monitoring` hangs and the namespace stays Terminating for hours with `NamespaceDeletionDiscoveryFailure ... metrics.k8s.io/v1beta1: the server is currently unable to handle the request`; pods Terminating forever on a node that was powered off · **Where:** after uninstalling an operator before its custom resources, a broken metrics-server or Rancher add-on, dead nodes · **Level:** [L2 · Mid] · **CKA:** Troubleshooting · **How common:** kubernetes #60807 namespace stuck in Terminating (180 comments, 119 reactions) and #51835 pods stuck on terminating (191 comments, 151 reactions); "Endlessly Terminating Pods" is a KodeKloud troubleshooting scenario

**Why it happens:** deletion has two phases. Objects with finalizers wait until their controller cleans up and removes the finalizer; if the operator that owns a finalizer was uninstalled first, nobody ever removes it. The namespace controller must also list every namespaced API before it can finish, so one unavailable aggregated APIService (metrics.k8s.io when metrics-server is gone) blocks every namespace deletion in the cluster. Pods on an unreachable node stay Terminating because no kubelet can confirm that the containers stopped.

**Diagnose:**

```bash
kubectl get ns monitoring -o jsonpath='{range .status.conditions[*]}{.type}: {.message}{"\n"}{end}'
kubectl get apiservice | grep -v True
kubectl get pods -A -o wide | grep Terminating
```

```text
NamespaceDeletionDiscoveryFailure: Discovery failed for some groups, 1 failing: unable to retrieve the complete list of server APIs: metrics.k8s.io/v1beta1: stale GroupVersion discovery: metrics.k8s.io/v1beta1
NamespaceContentRemaining: Some resources are remaining: prometheuses.monitoring.coreos.com has 1 resource instances
NamespaceFinalizersRemaining: Some content in the namespace has finalizers remaining: monitoring.coreos.com/prometheus in 1 resource instances
NAME                     SERVICE                      AVAILABLE                  AGE
v1beta1.metrics.k8s.io   kube-system/metrics-server   False (MissingEndpoints)   41d
shop   web-7c9d5b7f9-4kq8d   1/1   Terminating   0   3d   10.244.2.17   wk-2   <none>   <none>
```

**What the output tells you:** two separate blockers: the metrics APIService has no endpoints, and one Prometheus object still carries the operator's finalizer although the operator is gone. The pod on wk-2 is a third story: check whether wk-2 is really off before forcing anything.

**Fix:**

```bash
# 1. Repair the aggregated API (10.1), or remove it if metrics-server is gone for good
kubectl delete apiservice v1beta1.metrics.k8s.io
# 2. Best: reinstall the operator briefly so it can clean up, delete its custom resources, then uninstall it
# 3. Last resort, once you are sure no controller will ever handle it: drop that object's finalizer
kubectl -n monitoring patch prometheus kps --type=merge -p '{"metadata":{"finalizers":null}}'
# 4. A pod on a node that is confirmed powered off
kubectl -n shop delete pod web-7c9d5b7f9-4kq8d --grace-period=0 --force
```

**Why this fix works:** with discovery working and no finalizers left, the namespace controller completes on its own. Don't start with the popular trick of clearing the namespace's own finalizers through the /finalize endpoint: it hides the namespace while its objects stay in etcd and reappear if the name is reused. Force-deleting a pod whose node is still running can leave two copies of a StatefulSet member writing to the same data.

**Prevent it:** uninstall in order (custom resources, then the operator, then the CRDs), alert when any APIService is not Available, and configure graceful node shutdown so pods leave cleanly when a node goes down.

**Next step:** [26 §8 pods that will not run](26-playbook-containers-k8s.md#8-kubernetes-pods-that-will-not-run) · KodeKloud: *Kubernetes Troubleshooting for Application Developers* — Endlessly Terminating Pods · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [kubernetes #60807: deleting namespace stuck at Terminating](https://github.com/kubernetes/kubernetes/issues/60807) · [kubernetes #51835: Pods stuck on terminating](https://github.com/kubernetes/kubernetes/issues/51835) · Search: [Stack Overflow](https://stackoverflow.com/search?q=namespace+stuck+terminating+finalizers) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=namespace+stuck+terminating&restrict_sr=1)

---

## 4. Pod networking and CNI

The CNI plugin gives every pod an address and a route to every other pod. When it is missing, misconfigured or blocked by a firewall, the symptoms look like application bugs: timeouts, half-working services and DNS failures.

### 4.1 cni plugin not initialized: NotReady and CoreDNS Pending

> **Seen as:** `container runtime network not ready: NetworkReady=false reason:NetworkPluginNotReady message:Network plugin returns error: cni plugin not initialized`; nodes NotReady; CoreDNS Pending; `failed to find plugin "flannel" in path [/opt/cni/bin]` · **Where:** right after `kubeadm init` or `join`, or after switching or removing a CNI · **Level:** [L1 · Junior] · **CKA:** Troubleshooting · **How common:** kubeadm #1031 "runtime network not ready" (72 comments) and kubernetes #43815 on the same symptom (211 comments); the kubeadm docs state that CoreDNS stays Pending until a network add-on is installed

**Why it happens:** kubeadm deliberately installs no CNI. Until a network plugin writes its config into /etc/cni/net.d, the kubelet reports NetworkReady=false, the node keeps its not-ready taint and CoreDNS can't be scheduled. After you apply a CNI, it can still fail: Flannel needs the node to have a podCIDR, which only exists if `kubeadm init` got `--pod-network-cidr`; the plugin binaries may be missing from /opt/cni/bin; or a previous CNI left its config behind, and the lexically first file in /etc/cni/net.d wins.

**Diagnose:**

```bash
kubectl get nodes; kubectl -n kube-system get pods -l k8s-app=kube-dns
kubectl get pods -A -o wide | grep -Ei 'flannel|calico|cilium'
ls /etc/cni/net.d /opt/cni/bin
kubectl get node cp-1 -o jsonpath='{.spec.podCIDR}'; echo
kubectl -n kube-flannel logs ds/kube-flannel-ds --tail=1
```

```text
NAME   STATUS     ROLES           AGE   VERSION
cp-1   NotReady   control-plane   9m    v1.35.3
NAME                       READY   STATUS    RESTARTS   AGE
coredns-7c65d6cfc9-8x2kq   0/1     Pending   0          9m
coredns-7c65d6cfc9-tq9vn   0/1     Pending   0          9m
kube-flannel   kube-flannel-ds-6lq2w   0/1   CrashLoopBackOff   6 (2m ago)   8m   10.20.0.10   cp-1   <none>   <none>
ls: cannot access '/etc/cni/net.d': No such file or directory
/opt/cni/bin:
bandwidth  bridge  dhcp  firewall  host-local  loopback  portmap  ptp  tuning  vlan

E1004 09:31:22.412870       1 main.go:...] Error registering network: failed to acquire lease: node "cp-1" pod cidr not assigned
```

**What the output tells you:** Flannel is installed but crashes because the node has no podCIDR: init ran without `--pod-network-cidr`, so the controller manager never allocated node ranges. With Flannel down, nothing writes /etc/cni/net.d, the node stays NotReady and CoreDNS stays Pending. The binaries are present, so that is not the problem here.

**Fix:**

```bash
# Lab: start over with the CIDR the CNI expects (Flannel's default is 10.244.0.0/16)
sudo kubeadm reset -f && sudo rm -rf /etc/cni/net.d
sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=10.20.0.10
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
# Existing cluster instead: in /etc/kubernetes/manifests/kube-controller-manager.yaml
#   - --allocate-node-cidrs=true
#   - --cluster-cidr=10.244.0.0/16
# Missing binaries: the CNI plugins release tarball into /opt/cni/bin
# Switching CNIs: delete the old DaemonSet, then on EVERY node remove its config and restart
sudo rm -f /etc/cni/net.d/10-flannel.conflist && sudo systemctl restart containerd kubelet
```

**Why this fix works:** the controller manager now gives each node a /24 out of 10.244.0.0/16, Flannel gets its lease and writes its config, and the kubelet flips to NetworkReady; CoreDNS schedules within a minute. Install exactly one CNI, and keep its pod CIDR away from your LAN (10.20.0.0/24 here), VPN and Docker ranges, or routing breaks in ways that look random.

**Prevent it:** choose pod and service CIDRs before `kubeadm init`, keep them in the kubeadm config file in Git, and make the CNI part of the bootstrap playbook rather than a manual step.

**Next step:** [31 §3 Building a kubeadm homelab cluster](31-learn-kubernetes.md#3-building-a-kubeadm-homelab-cluster) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking (CNI) · [*Prerequisite Network Namespaces*](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/Prerequisite-Network-Namespaces/page) · [Troubleshooting kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/troubleshooting-kubeadm/)

**Community threads:** [kubeadm #1031: runtime network not ready](https://github.com/kubernetes/kubeadm/issues/1031) · [kubernetes #43815: kubelet NotReady due to unconfigured CNI](https://github.com/kubernetes/kubernetes/issues/43815) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22cni+plugin+not+initialized%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=%22cni+plugin+not+initialized%22&restrict_sr=1)

### 4.2 Pods on different nodes can't talk

> **Seen as:** a pod reaches pods on its own node but times out to pods (and Services backed by pods) on other nodes; ping works but TLS or large responses hang; `calico/node is not ready: BIRD is not ready: BGP not established with 10.20.0.22`; new pods stuck in ContainerCreating with `CNI plugin: error getting ClusterInformation: connection is unauthorized: Unauthorized` · **Where:** multi-node labs behind UFW or a hypervisor firewall, overlays over a VPN or VLAN with a smaller MTU, Calico upgrades · **Level:** [L2 · Mid] · **CKA:** Troubleshooting · **How common:** discuss.kubernetes.io "Cannot access pod services from another pod" (40k views); calico #9433 "VXLAN in 3.29 breaks any connectivity except ICMP" (46 comments), #7555 (53) and #5712 (40)

**Why it happens:** traffic between nodes is encapsulated: Flannel VXLAN on UDP 8472, Calico VXLAN on UDP 4789, Calico IP-in-IP as IP protocol 4, Calico BGP on TCP 179, Cilium VXLAN on UDP 8472. A host firewall with default deny drops it, so only same-node traffic works. The overlay adds about 50 bytes per packet; if the path MTU is smaller (a WireGuard link, PPPoE, some hypervisor networks), small packets pass and full-size ones vanish, which is why ping works and TLS hangs. Calico may build BGP sessions or tunnels over the wrong NIC (2.3), and its CNI plugin uses a token that stops working after CA or certificate changes. Some kernel and NIC combinations also mangle VXLAN checksums.

**Diagnose:**

```bash
kubectl get pods -o wide | grep -E 'debug|web'
kubectl exec deploy/debug -- curl -s -m3 -o /dev/null -w '%{http_code}\n' http://10.244.2.17:8080/
# on wk-2: do the encapsulated packets arrive, and does the firewall drop them?
sudo tcpdump -ni enp0s8 -c 2 'udp port 8472 or udp port 4789 or ip proto 4'
sudo journalctl -k --since '-5min' | grep 'UFW BLOCK' | grep -E 'DPT=(8472|4789)' | tail -1
# MTU: a full 1500-byte packet with "don't fragment" set (needs iputils ping, e.g. a netshoot debug image)
kubectl exec deploy/debug -- ping -c2 -M do -s 1472 10.244.2.17
```

```text
debug-6d4f8b7c5-q8w2n   1/1   Running   0   5m   10.244.1.9    wk-1   <none>   <none>
web-7c9d5b7f9-x2kqp     1/1   Running   0   2h   10.244.2.17   wk-2   <none>   <none>
000
10:41:07.118203 IP 10.20.0.21.51234 > 10.20.0.22.8472: OTV, flags [I] (0x08), overlay 0, instance 1
10:41:08.120544 IP 10.20.0.21.51234 > 10.20.0.22.8472: OTV, flags [I] (0x08), overlay 0, instance 1
Oct 04 10:41:07 wk-2 kernel: [UFW BLOCK] IN=enp0s8 OUT= SRC=10.20.0.21 DST=10.20.0.22 LEN=110 TOS=0x00 PREC=0x00 TTL=64 ID=4411 PROTO=UDP SPT=51234 DPT=8472 LEN=90
ping: local error: message too long, mtu=1450
```

**What the output tells you:** the VXLAN packets from wk-1 reach wk-2's NIC (tcpdump sees them before the firewall; it labels port 8472 as "OTV"), and UFW then drops them. That alone explains the timeout. The local "message too long, mtu=1450" for a 1500-byte packet shows the pod MTU is 1450, as expected for VXLAN on a 1500 network (older iputils print `sendmsg: Message too long` instead), so MTU is not the problem here; a silent loss at sizes that fit the pod MTU (up to `-s 1422`) would be.

**Fix:**

```bash
# Open the overlay only between the nodes (Flannel/Cilium VXLAN 8472/udp; Calico VXLAN 4789/udp)
sudo ufw allow from 10.20.0.0/24 to any port 8472 proto udp comment 'flannel vxlan'
sudo ufw allow from 10.20.0.0/24 to any port 179 proto tcp comment 'calico bgp'    # only with BGP
# UFW can't allow IP protocol 4 by port: on UFW hosts prefer Calico VXLAN over IP-in-IP
# Calico (operator) settings live in the Installation resource:
#   spec.calicoNetwork.mtu: 1370                                    # path MTU smaller than 1500
#   spec.calicoNetwork.nodeAddressAutodetectionV4: { cidrs: ["10.20.0.0/24"] }
# Calico CNI "Unauthorized" after a certificate or CA change: let calico-node write a fresh token
kubectl -n calico-system rollout restart ds/calico-node
# VXLAN checksum offload bug on some kernels/NICs: upgrade Calico; temporary workaround per node
sudo ethtool -K vxlan.calico tx-checksum-ip-generic off
```

**Why this fix works:** the encapsulated packets now reach the other node's kernel, which unwraps them and delivers them to the pod; the right MTU and interface keep large packets intact. Don't open 8472 or 4789 to the internet: VXLAN has no authentication, so anyone who can send to that port can inject packets into your pod network. Don't disable the firewall either.

**Prevent it:** list the CNI ports in [Who owns this port?](22-playbook-ports-inventory.md) and in the Ansible firewall role, run a cross-node connectivity check after every node addition and CNI upgrade (Cilium ships `cilium connectivity test`), and read the CNI release notes before upgrading.

**Next step:** [Network speed playbook](24-playbook-network-speed.md) (MTU) · [26 §9 Services, Ingress and DNS](26-playbook-containers-k8s.md#9-kubernetes-services-ingress-and-dns) · KodeKloud: [*Troubleshooting Internal Networking*](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Services/Troubleshooting-Internal-Networking/page) · *Kubernetes Networking Deep Dive* — Cilium CNI · [Calico docs](https://docs.tigera.io/calico/latest/) · [Cilium docs](https://docs.cilium.io/)

**Community threads:** [discuss.kubernetes.io: Cannot access pod services from another pod](https://discuss.kubernetes.io/t/cannot-access-pod-services-from-another-pod/11944) · [calico #9433: VXLAN in 3.29 breaks connectivity except ICMP](https://github.com/projectcalico/calico/issues/9433) · [calico #5712: error getting ClusterInformation: Unauthorized](https://github.com/projectcalico/calico/issues/5712) · [calico #7555: projectcalico.org/v3 unable to handle the request](https://github.com/projectcalico/calico/issues/7555) · Search: [Stack Overflow](https://stackoverflow.com/search?q=kubernetes+pods+different+nodes+cannot+communicate+flannel+vxlan) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=pods+cannot+reach+other+node+vxlan+ufw&restrict_sr=1)

### 4.3 Pods have no internet access

> **Seen as:** `wget: download timed out` or `dial tcp 140.82.121.4:443: i/o timeout` from inside pods, while the node itself reaches the internet · **Where:** Ubuntu nodes with UFW, nodes where IP forwarding was reset, Calico pools without NAT, nodes that also run Docker · **Level:** [L2 · Mid] · **CKA:** Troubleshooting · **How common:** discuss.kubernetes.io "Kubernetes Pods do not have internet access" (about 60k views)

**Why it happens:** a packet from a pod is routed by the node (the FORWARD path), then masqueraded to the node's address on the way out. Each step can break: `net.ipv4.ip_forward` is 0 again after a sysctl file or cloud-init change; UFW's default routed policy is "deny", so forwarded pod traffic is dropped; masquerading is off (Calico IPPool `natOutgoing: false`, Flannel without `--ip-masq`). A node that also runs Docker gets Docker's FORWARD DROP policy as well. If only names fail and IPs work, it is DNS: go to 5.1.

**Diagnose:**

```bash
# Separate routing from DNS: an IP first, then a name
kubectl run nettest --rm -it --restart=Never --image=busybox:1.36 -- sh -c 'wget -qO- -T5 http://1.1.1.1 > /dev/null && echo IP-OK'
# on the node that ran the pod
sysctl net.ipv4.ip_forward
sudo ufw status verbose | grep -i '^default'
sudo iptables -t nat -S | grep -i 'masq' | head -2               # Flannel keeps its rule in FLANNEL-POSTRTG
```

```text
wget: download timed out
pod "nettest" deleted
net.ipv4.ip_forward = 1
Default: deny (incoming), allow (outgoing), deny (routed)
-A POSTROUTING -m comment --comment "flanneld masq" -j FLANNEL-POSTRTG
-A FLANNEL-POSTRTG -s 10.244.0.0/16 ! -d 224.0.0.0/4 -m comment --comment "flanneld masq" -j MASQUERADE --random-fully
```

**What the output tells you:** even a bare IP times out, so this is routing, not DNS. Forwarding is on and the masquerade rule exists, but UFW's "deny (routed)" drops every forwarded packet from the pods.

**Fix:**

```bash
# Allow forwarding for the pod network only; everything else stays denied
sudo ufw route allow from 10.244.0.0/16 comment 'pods egress'
sudo ufw route allow to 10.244.0.0/16 comment 'pods return and cross-node'
# Forwarding off? persist it in /etc/sysctl.d/k8s.conf (see 2.2), then:
sudo sysctl --system
# Calico pool without NAT: masquerade traffic that leaves the cluster
kubectl patch ippool default-ipv4-ippool --type=merge -p '{"spec":{"natOutgoing":true}}'
# Operator installs: set natOutgoing: Enabled under spec.calicoNetwork.ipPools in the Installation resource instead,
# because the operator reconciles the pools it created
```

**Why this fix works:** forwarded pod packets are now accepted, and the masquerade rule rewrites their source to the node's address so replies come back. Don't `ufw disable` or set the FORWARD policy to ACCEPT on a host that faces the internet: you turn the node into an open router. If pods should reach only some destinations, use egress NetworkPolicies (4.4) rather than the host firewall.

**Prevent it:** keep the pod CIDR routes in the Ansible firewall role, don't install Docker on Kubernetes nodes, and add an egress test pod to node acceptance.

**Next step:** [Networking course](28-learn-networking.md) · [Network commands](02-network.md) · [26 §9 Services, Ingress and DNS](26-playbook-containers-k8s.md#9-kubernetes-services-ingress-and-dns) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking (Prerequisite Switching, Routing and Gateways) · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [discuss.kubernetes.io: Kubernetes Pods do not have internet access](https://discuss.kubernetes.io/t/kubernetes-pods-do-not-have-internet-access/5252) · Search: [Stack Overflow](https://stackoverflow.com/search?q=kubernetes+pods+no+internet+access+ufw) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=pods+no+internet+access+ufw&restrict_sr=1)

### 4.4 NetworkPolicy ignored, or default deny breaks DNS

> **Seen as:** a deny policy is applied and traffic still flows; or, after a default-deny, every lookup in the namespace fails with `;; connection timed out; no servers could be reached` · **Where:** kubeadm clusters with Flannel only, k3s (which enforces policies with kube-router's controller), Calico or Cilium clusters adopting default-deny · **Level:** [L2 · Mid] · **CKA:** Services and Networking · **How common:** NetworkPolicy tasks are CKA staples and "Unreachable Pods + Leaky Network Policies" is a KodeKloud scenario; k3s #14711 (2026) asks for default-deny coverage during pod startup

**Why it happens:** a NetworkPolicy is only an API object; the CNI enforces it, and Flannel alone enforces nothing. Policies are allow-lists that add up: once any policy selects a pod for Egress, everything not explicitly allowed is dropped, including DNS to CoreDNS on UDP and TCP 53. Selectors fail quietly too: a namespaceSelector on a label the namespace doesn't have matches nothing, while every namespace automatically carries `kubernetes.io/metadata.name`.

**Diagnose:**

```bash
kubectl -n shop get netpol
kubectl get pods -A | grep -Ei 'calico|cilium|flannel|kube-router' | head -2
kubectl -n shop exec deploy/web -- nslookup kubernetes.default.svc.cluster.local
kubectl get ns kube-system --show-labels
```

```text
NAME           POD-SELECTOR   AGE
default-deny   <none>         5m
allow-web      app=web        5m
calico-system   calico-node-7xk2p   1/1   Running   0   6d
calico-system   calico-node-b9q4m   1/1   Running   0   6d
;; connection timed out; no servers could be reached
NAME          STATUS   AGE   LABELS
kube-system   Active   41d   kubernetes.io/metadata.name=kube-system
```

**What the output tells you:** Calico enforces policies, so default-deny is working exactly as written: it blocks egress to CoreDNS because nothing allows it. On a Flannel-only cluster, the same test would succeed and every policy would be decoration.

**Fix:**

```yaml
# allow-dns.yaml: every pod in shop may query CoreDNS
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: allow-dns, namespace: shop }
spec:
  podSelector: {}
  policyTypes: [Egress]
  egress:
    - to:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: kube-system } }
          podSelector: { matchLabels: { k8s-app: kube-dns } }
      ports:
        - { protocol: UDP, port: 53 }
        - { protocol: TCP, port: 53 }
```

**Why this fix works:** the namespaceSelector and podSelector sit in one list item, so they combine with AND: only the CoreDNS pods in kube-system, only on port 53. Written as two list items they would mean OR and open egress to every pod in kube-system. On Flannel-only clusters, add a policy engine (Calico's policy-only mode, known as Canal, or move to Calico or Cilium) before relying on any policy.

**Prevent it:** ship default-deny together with the DNS rule as one template per namespace, and test policies in CI with a small connectivity matrix (allowed paths succeed, forbidden ones time out).

**Next step:** [31 §15 NetworkPolicies](31-learn-kubernetes.md#15-networkpolicies) · KodeKloud: *Kubernetes Troubleshooting for Application Developers* — Unreachable Pods + Leaky Network Policies · *Kubernetes Networking Deep Dive* — NetworkPolicies · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [k3s #14711: kube-router default deny during pod startup](https://github.com/k3s-io/k3s/issues/14711) · Search: [Stack Overflow](https://stackoverflow.com/search?q=networkpolicy+default+deny+dns+egress+kube-dns) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=networkpolicy+not+working+flannel&restrict_sr=1)

---

## 5. Cluster DNS: CoreDNS

DNS is the most common hidden cause of "the app is slow" and "the app can't connect". On Ubuntu nodes, the interaction between CoreDNS and systemd-resolved adds a trap of its own.

### 5.1 CoreDNS loop detected or upstream timeouts

> **Seen as:** CoreDNS in CrashLoopBackOff with `[FATAL] plugin/loop: Loop (127.0.0.1:44222 -> :53) detected for zone "."`, or running but logging `[ERROR] plugin/errors: 2 github.com. A: read udp 10.244.1.5:43201->10.20.0.1:53: i/o timeout` · **Where:** Ubuntu nodes with systemd-resolved, clusters behind an office or home DNS server, nodes with a strict firewall · **Level:** [L2 · Mid] · **CKA:** Troubleshooting · **How common:** discuss.kubernetes.io "CoreDNS [ERROR] plugin/errors: 2" (38k views); k3s #1606 on scaling CoreDNS (26 reactions); the loop case also appears in [26 §9](26-playbook-containers-k8s.md#9-kubernetes-services-ingress-and-dns)

**Why it happens:** CoreDNS forwards everything outside cluster.local to the servers in the resolv.conf the kubelet gives it. On Ubuntu, /etc/resolv.conf points at 127.0.0.53, the systemd-resolved stub, and inside the CoreDNS pod 127.0.0.53 is the pod itself: CoreDNS asks itself, the loop plugin detects it and stops the process. kubeadm normally sets the kubelet's `resolvConf` to /run/systemd/resolve/resolv.conf, but hand-written kubelet configs and some installers miss it. If there is no loop but the log shows i/o timeouts, the upstream server is unreachable from the pod network: the node firewall (4.3), an upstream that only answers some source networks, or a dead server.

**Diagnose:**

```bash
kubectl -n kube-system get pods -l k8s-app=kube-dns
kubectl -n kube-system logs -l k8s-app=kube-dns --tail=1
kubectl -n kube-system get cm coredns -o jsonpath='{.data.Corefile}' | grep -E 'forward|loop'
sudo grep -i resolvConf /var/lib/kubelet/config.yaml
grep nameserver /etc/resolv.conf /run/systemd/resolve/resolv.conf
```

```text
NAME                       READY   STATUS             RESTARTS      AGE
coredns-7c65d6cfc9-8x2kq   0/1     CrashLoopBackOff   7 (95s ago)   14m
coredns-7c65d6cfc9-tq9vn   0/1     CrashLoopBackOff   7 (88s ago)   14m
[FATAL] plugin/loop: Loop (127.0.0.1:44222 -> :53) detected for zone ".", see https://coredns.io/plugins/loop#troubleshooting. Query: "HINFO 4547991504243258144.3688648895315093531."
    forward . /etc/resolv.conf {
    loop
resolvConf: /etc/resolv.conf
/etc/resolv.conf:nameserver 127.0.0.53
/run/systemd/resolve/resolv.conf:nameserver 10.20.0.1
```

**What the output tells you:** the kubelet hands pods the stub file with 127.0.0.53, so CoreDNS forwards to itself. The real upstream, 10.20.0.1, is in systemd-resolved's own file.

**Fix:**

```bash
# Give pods the real upstream list (every node; for kubeadm also edit the kubelet-config ConfigMap,
# otherwise the next "kubeadm upgrade node" writes the old value back)
sudo sed -i 's#^resolvConf: .*#resolvConf: /run/systemd/resolve/resolv.conf#' /var/lib/kubelet/config.yaml
sudo systemctl restart kubelet
kubectl -n kube-system rollout restart deploy/coredns
# Or name upstreams explicitly in the Corefile:   forward . 10.20.0.1 1.1.1.1
# Internal zones answered by the office DNS:      example.internal:53 { forward . 10.20.0.1 }
# Upstream timeouts rather than a loop: query the upstream straight from a pod
kubectl run dnstest --rm -it --restart=Never --image=busybox:1.36 -- nslookup github.com 10.20.0.1
```

**Why this fix works:** CoreDNS now forwards to a server outside itself, the loop check passes and the pods become Ready. Don't delete the `loop` plugin to make the crash stop: the loop is still there, and CoreDNS will burn CPU and memory on it until it is killed. Don't hard-code a public resolver on the nodes either: you lose internal names and the LAN's DNS policy.

**Prevent it:** run at least two CoreDNS replicas on different nodes, alert on SERVFAIL rate and forward latency, and include a DNS test (cluster name and external name) in node acceptance.

**Next step:** [DNS commands](08-dns.md) · [31 §9 Cluster DNS](31-learn-kubernetes.md#9-cluster-dns) · KodeKloud: [*CoreDNS in Kubernetes*](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/CoreDNS-in-Kubernetes/page) · [*Prerequisite DNS*](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Networking/Prerequisite-DNS) · [CoreDNS docs](https://coredns.io/)

**Community threads:** [discuss.kubernetes.io: CoreDNS ERROR plugin/errors: 2](https://discuss.kubernetes.io/t/coredns-error-plugin-errors-2/16106) · [k3s #1606: CoreDNS replica count](https://github.com/k3s-io/k3s/issues/1606) · Search: [Stack Overflow](https://stackoverflow.com/search?q=coredns+%22loop+detected%22+systemd-resolved) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=coredns+loop+detected+ubuntu&restrict_sr=1)

### 5.2 ndots:5, conntrack races and DNS storms

> **Seen as:** random 5-second delays on outbound calls; floods of NXDOMAIN for names like `api.example.com.shop.svc.cluster.local`; CoreDNS OOMKilled during traffic peaks; `insert_failed` growing in `conntrack -S` · **Where:** busy clusters, Alpine (musl) images, services that call many external APIs · **Level:** [L3 · Senior] · **CKA:** Services and Networking (beyond the exam) · **How common:** recurring in the postmortems on k8s.af: Zalando's total DNS outage (CoreDNS OOM, ndots:5), Preply's DNS postmortem (conntrack, the CoreDNS autoscaler) and Toyota Connected's "perfect DNS storm" (ndots:5, musl)

**Why it happens:** every pod's resolv.conf carries the cluster search domains and `options ndots:5`, so any name with fewer than five dots is first tried with each search suffix. One lookup of api.example.com becomes four or five failed queries, times two for A and AAAA, before the real one. Under load that multiplies CoreDNS traffic, and a CoreDNS with the default memory limit can be OOM-killed, taking every lookup in the cluster with it. Separately, glibc sends the A and AAAA queries in parallel from one UDP socket, and a race in Linux conntrack can drop one of them; the resolver waits 5 seconds before retrying.

**Diagnose:**

```bash
kubectl -n shop exec deploy/web -- cat /etc/resolv.conf
# With the "log" plugin enabled in the Corefile for a few minutes:
kubectl -n kube-system logs -l k8s-app=kube-dns --since=1m | grep 'api.example.com' | tail -5
sudo conntrack -S | grep -o 'insert_failed=[0-9]*' | head -2              # on a node (conntrack package)
kubectl -n kube-system get pods -l k8s-app=kube-dns -o custom-columns=NAME:.metadata.name,RESTARTS:.status.containerStatuses[0].restartCount,LAST:.status.containerStatuses[0].lastState.terminated.reason
```

```text
search shop.svc.cluster.local svc.cluster.local cluster.local example.com
nameserver 10.96.0.10
options ndots:5
[INFO] 10.244.1.12:41022 - 3315 "A IN api.example.com.shop.svc.cluster.local. udp 56 false 512" NXDOMAIN qr,aa,rd 149 0.000128s
[INFO] 10.244.1.12:55804 - 9021 "A IN api.example.com.svc.cluster.local. udp 51 false 512" NXDOMAIN qr,aa,rd 144 0.000097s
[INFO] 10.244.1.12:51920 - 2210 "A IN api.example.com.cluster.local. udp 47 false 512" NXDOMAIN qr,aa,rd 140 0.000088s
[INFO] 10.244.1.12:39811 - 6012 "A IN api.example.com.example.com. udp 45 false 512" NXDOMAIN qr,rd,ra 120 0.0211s
[INFO] 10.244.1.12:47712 - 7731 "A IN api.example.com. udp 33 false 512" NOERROR qr,rd,ra 64 0.0182s
insert_failed=1832
insert_failed=2107
NAME                       RESTARTS   LAST
coredns-7c65d6cfc9-8x2kq   4          OOMKilled
coredns-7c65d6cfc9-tq9vn   3          OOMKilled
```

**What the output tells you:** one lookup costs five A queries (and as many AAAA), one of which even leaves the cluster to the upstream. Thousands of conntrack insert failures explain the 5-second stalls, and both CoreDNS replicas have been OOM-killed: the classic storm pattern from the postmortems.

**Fix:**

```yaml
# Per workload: fewer search expansions for apps that mostly call external names
spec:
  dnsConfig:
    options:
      - { name: ndots, value: "2" }
      - { name: single-request-reopen }    # glibc only; musl (Alpine) ignores it
# In application config, a trailing dot skips the search list entirely: api.example.com.
```

```bash
# Capacity: more replicas spread over nodes, and more memory than the default limit
kubectl -n kube-system scale deploy/coredns --replicas=3
kubectl -n kube-system set resources deploy/coredns -c coredns --requests=cpu=200m,memory=128Mi --limits=memory=512Mi
# Cluster-wide: deploy NodeLocal DNSCache (a cache on every node that talks TCP to CoreDNS)
# k3s re-applies its packaged CoreDNS manifest on restart (the subject of k3s #1606): keep custom
# zones in the coredns-custom ConfigMap and re-check replicas after upgrades
```

**Why this fix works:** ndots:2 still resolves `postgres.db` style Service names through the search list but sends external names out first, cutting queries by four fifths. A node-local cache answers repeats locally and uses TCP upstream, which sidesteps the UDP conntrack race. Don't set ndots:1 cluster-wide without checking apps that use short cross-namespace names, and don't remove CoreDNS memory limits altogether: an unbounded CoreDNS can take a node down instead.

**Prevent it:** a DNS dashboard (queries per second, NXDOMAIN ratio, latency, OOM kills) next to [Observability problems](49-observability-stack-problems.md), a DNS load test before big launches, and a team reading of the DNS stories on k8s.af.

**Next step:** [31 §9 Cluster DNS](31-learn-kubernetes.md#9-cluster-dns) · [Senior architecture](39-learn-senior-architecture.md) · KodeKloud: [*CoreDNS in Kubernetes*](https://notes.kodekloud.com/docs/Certified-Kubernetes-Administrator-CKA/Networking/CoreDNS-in-Kubernetes/page) · *Kubernetes Networking Deep Dive* · [CoreDNS docs](https://coredns.io/)

**Community threads:** [Kubernetes Failure Stories (k8s.af)](https://k8s.af/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=kubernetes+ndots+5+dns+latency+conntrack) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=ndots+conntrack+dns+5+second&restrict_sr=1)

---

## 6. Ingress: webhooks, ingress-nginx and Traefik

The ingress layer is where Kubernetes meets your users and where the reader's Traefik knowledge from Dokploy carries over. Remember the calendar: Kubernetes retired ingress-nginx (no releases or security fixes after March 2026), so new clusters should start on Traefik or the Gateway API, and existing ones need a migration plan ([43 §8](43-traefik-and-reverse-proxies.md#8-traefik-tcp-auth-client-ip-and-kubernetes)).

### 6.1 failed calling webhook: admission webhooks block apply

> **Seen as:** `Internal error occurred: failed calling webhook "validate.nginx.ingress.kubernetes.io": failed to call webhook: Post "https://ingress-nginx-controller-admission.ingress-nginx.svc:443/networking/v1/ingresses?timeout=10s": context deadline exceeded`, and the same shape for `webhook.cert-manager.io` (often with a TLS handshake timeout or x509 error), `ipaddresspoolvalidationwebhook.metallb.io` or Longhorn's conversion webhook · **Where:** right after installing an add-on, after uninstalling one, EKS clusters with a private control plane, namespaces with default-deny policies · **Level:** [L2 · Mid] · **CKA:** Services and Networking · **How common:** ingress-nginx #5401 is the most-reacted issue in that repository (307 reactions, 177 comments); cert-manager #2319 (86 comments) and #2602 (71); MetalLB #1597 (63) and #1540 (43); Jetstack's webhook outage is on k8s.af

**Why it happens:** an admission webhook makes the API server call an HTTPS service inside the cluster before it accepts an object, and with `failurePolicy: Fail` any failure to reach it rejects the request. The call fails when the webhook pods are not ready yet (custom resources applied seconds after the chart), when the Service has no endpoints, when the API server can't reach the pod network, when a NetworkPolicy blocks the webhook port, or when the CA bundle hasn't been injected yet. The sneakiest case is a leftover: webhook configurations are cluster-scoped, so deleting an add-on's namespace leaves them behind, still intercepting every matching object.

**Diagnose:**

```bash
kubectl get validatingwebhookconfigurations,mutatingwebhookconfigurations
kubectl get validatingwebhookconfiguration ingress-nginx-admission -o jsonpath='{.webhooks[0].clientConfig.service}'; echo
kubectl -n ingress-nginx get svc,endpoints,pods
kubectl -n cert-manager get pods -l app.kubernetes.io/component=webhook
```

```text
NAME                                                                                         WEBHOOKS   AGE
validatingwebhookconfiguration.admissionregistration.k8s.io/cert-manager-webhook             1          88d
validatingwebhookconfiguration.admissionregistration.k8s.io/ingress-nginx-admission          1          201d
validatingwebhookconfiguration.admissionregistration.k8s.io/metallb-webhook-configuration    6          120d
mutatingwebhookconfiguration.admissionregistration.k8s.io/cert-manager-webhook               1          88d
{"name":"ingress-nginx-controller-admission","namespace":"ingress-nginx","path":"/networking/v1/ingresses","port":443}
No resources found in ingress-nginx namespace.
NAME                                       READY   STATUS    RESTARTS   AGE
cert-manager-webhook-6d5b8c7f9d-q2xkp      1/1     Running   0          88d
```

**What the output tells you:** ingress-nginx was removed during the move to Traefik, but its ValidatingWebhookConfiguration survived, so every Ingress create or update, including Traefik's, is sent to a Service that no longer exists. The cert-manager webhook is healthy and not involved.

**Fix:**

```bash
# A webhook whose backend is gone for good: remove its configuration
kubectl delete validatingwebhookconfiguration ingress-nginx-admission
# A webhook that exists but isn't ready yet (fresh install): wait, then apply the custom resources
kubectl -n cert-manager rollout status deploy/cert-manager-webhook
kubectl -n metallb-system wait --for=condition=Available deploy --all --timeout=120s
# Default-deny in the add-on namespace: allow ingress to the webhook pods on their port
# (ingress-nginx 8443, cert-manager 10250, MetalLB 9443) from the control-plane nodes
```

<div class="env" data-env="onprem" markdown="1">

On kubeadm and k3s the API server runs on the control-plane host and reaches webhook pods through the CNI. If cross-node pod traffic is broken (4.2), webhooks time out too, so fix the network first.

</div>

<div class="env" data-env="cloud" markdown="1">

On EKS the API server lives in an AWS-managed VPC and reaches webhook pods through the cluster security group. Allow inbound from the cluster security group to the nodes on each webhook port (cert-manager 10250, ingress-nginx 8443, AWS Load Balancer Controller 9443), or the calls time out although every pod is healthy.

</div>

**Why this fix works:** the API server can only accept objects when every matching webhook answers, so either the webhook must be reachable or its configuration must be gone. Don't set `failurePolicy: Ignore` or delete webhooks that are still in use: they validate config that would otherwise crash the controller (6.3) or issue broken certificates. Deleting the configuration is right only when the add-on itself is gone.

**Prevent it:** install with `helm install --wait` or Argo CD sync waves so custom resources come after the webhook is ready, uninstall add-ons with the same tool that installed them and check for cluster-scoped leftovers, scope webhooks with namespaceSelector so kube-system is never blocked (the Jetstack lesson), and alert on `apiserver_admission_webhook_rejection_count` and webhook latency.

**Next step:** [26 §9 Services, Ingress and DNS](26-playbook-containers-k8s.md#9-kubernetes-services-ingress-and-dns) · [43 §8 Traefik on Kubernetes](43-traefik-and-reverse-proxies.md#8-traefik-tcp-auth-client-ip-and-kubernetes) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Security · [Kubernetes docs](https://kubernetes.io/docs/) · [cert-manager docs](https://cert-manager.io/docs/)

**Community threads:** [ingress-nginx #5401: failed calling webhook](https://github.com/kubernetes/ingress-nginx/issues/5401) · [cert-manager #2319: webhook context deadline exceeded](https://github.com/cert-manager/cert-manager/issues/2319) · [cert-manager #2602: webhook TLS handshake timeout](https://github.com/cert-manager/cert-manager/issues/2602) · [metallb #1597: ipaddresspool webhook](https://github.com/metallb/metallb/issues/1597) · [metallb #1540](https://github.com/metallb/metallb/issues/1540) · [k8s.af](https://k8s.af/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22failed+calling+webhook%22+%22context+deadline+exceeded%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=%22failed+calling+webhook%22&restrict_sr=1)

### 6.2 Ingress returns 404: class, two controllers, k3s Traefik

> **Seen as:** Traefik's plain `404 page not found` (or the nginx 404 page) for a host you defined; `svclb-ingress-nginx-controller-...` pods Pending with `0/3 nodes are available: 3 node(s) didn't have free ports for the requested pod ports`; edits to the Traefik Deployment disappear after k3s restarts · **Where:** k3s, which ships Traefik and ServiceLB; kubeadm clusters with two controllers; Ingresses without `ingressClassName` · **Level:** [L1 · Junior] · **CKA:** Services and Networking · **How common:** k3s #1141 "Traefik 2.0 integration" (63 reactions) and #817 "Drop traefik and go to nginx controller" (55); "What the Ingress?" is a KodeKloud troubleshooting scenario

**Why it happens:** an Ingress is served only by the controller whose class it names, or by the default IngressClass if it names none. k3s installs Traefik as that default, and ServiceLB implements LoadBalancer Services by binding ports 80 and 443 on the nodes through svclb pods. Install ingress-nginx next to it and its svclb pods can't get the ports Traefik already holds, so it never receives an address; your Ingress names class nginx while all traffic on port 80 reaches Traefik, which has no route for that host and answers 404. Traefik itself is deployed by k3s's Helm controller from a packaged manifest, so manual edits are reverted: k3s expects a HelmChartConfig.

**Diagnose:**

```bash
kubectl get ingressclass
kubectl get ingress -A -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,CLASS:.spec.ingressClassName,ADDRESS:.status.loadBalancer.ingress[*].ip
kubectl get svc -A | grep LoadBalancer
kubectl -n kube-system get pods | grep svclb
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: shop.example.com' http://10.20.0.30/
```

```text
NAME      CONTROLLER                      PARAMETERS   AGE
traefik   traefik.io/ingress-controller   <none>       30d
nginx     k8s.io/ingress-nginx            <none>       2d
NS     NAME   CLASS   ADDRESS
shop   web    nginx   <none>
kube-system     traefik                    LoadBalancer   10.43.112.9    10.20.0.30,10.20.0.31,10.20.0.32   80:31080/TCP,443:31443/TCP   30d
ingress-nginx   ingress-nginx-controller   LoadBalancer   10.43.88.140   <pending>                          80:30612/TCP,443:32154/TCP   2d
svclb-ingress-nginx-controller-5c1e2a7b-6xk9q   0/2   Pending   0   2d
svclb-traefik-4f9d0c1e-p2m8s                    2/2   Running   0   30d
404
```

**What the output tells you:** the Ingress belongs to class nginx, whose controller never got an address because ServiceLB can't bind 80/443 twice. Requests to the nodes' port 80 reach Traefik, which knows nothing about shop.example.com and returns 404.

**Fix:**

```bash
# Option A (simplest on k3s): keep Traefik and use its class
kubectl -n shop patch ingress web --type=merge -p '{"spec":{"ingressClassName":"traefik"}}'
helm -n ingress-nginx uninstall ingress-nginx
kubectl delete validatingwebhookconfiguration ingress-nginx-admission --ignore-not-found   # 6.1
# Option B: drop the packaged Traefik on every server, then restart
#   /etc/rancher/k3s/config.yaml
#   disable:
#     - traefik
sudo systemctl restart k3s
```

```yaml
# Customise the packaged Traefik the k3s way: /var/lib/rancher/k3s/server/manifests/traefik-config.yaml
# Value keys change between chart versions: check the chart's values for your version,
# then verify the rendered pod arguments (43 §8.5) instead of trusting the file
apiVersion: helm.cattle.io/v1
kind: HelmChartConfig
metadata:
  name: traefik
  namespace: kube-system
spec:
  valuesContent: |-
    logs:
      access:
        enabled: true
    ports:
      web:
        redirections:
          entryPoint: { to: websecure, scheme: https }
```

**Why this fix works:** with one controller owning 80 and 443 and every Ingress naming its class, there is no ambiguity about who answers. The HelmChartConfig is merged into k3s's own chart values on every reconcile, so your settings survive restarts and upgrades. Don't run two controllers on the same host ports; if you need two, give each its own MetalLB address (8.1).

**Prevent it:** decide the cluster's ingress controller once and write it down, require `ingressClassName` on every Ingress (a policy or a CI check), and keep k3s's config.yaml and HelmChartConfig files in Git.

**Next step:** [43 §8 Traefik on Kubernetes](43-traefik-and-reverse-proxies.md#8-traefik-tcp-auth-client-ip-and-kubernetes) · [31 §8 Ingress and the Gateway API](31-learn-kubernetes.md#8-ingress-and-the-gateway-api) · KodeKloud: [*Traefik Overview*](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Traefik-Overview/page) · [*Demo Traefik Installation*](https://notes.kodekloud.com/docs/Kubernetes-Networking-Deep-Dive/Kubernetes-Ingress/Demo-Traefik-Installation/page) · [*Ingress*](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Networking/Ingress/page) · [k3s networking docs](https://docs.k3s.io/networking/networking-services)

**Community threads:** [k3s #1141: Traefik 2.0 integration](https://github.com/k3s-io/k3s/issues/1141) · [k3s #817: Drop traefik and go to nginx controller](https://github.com/k3s-io/k3s/issues/817) · [k3s docs: Networking Services](https://docs.k3s.io/networking/networking-services) · [k3s docs: Helm and HelmChartConfig](https://docs.k3s.io/helm) · Search: [Stack Overflow](https://stackoverflow.com/search?q=k3s+traefik+ingress+404+ingressClassName) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=k3s+traefik+404+ingress&restrict_sr=1)

### 6.3 413, 504 and annotations that break ingress-nginx

> **Seen as:** `413 Request Entity Too Large` on uploads; `504 Gateway Time-out` after exactly 60 seconds; after a controller upgrade, the controller crash-loops on an invalid generated nginx.conf (ingress-nginx #13598: a `proxy-busy-buffers-size` value) or rejects Ingresses with paths it used to accept (#11176: a dot in a Prefix path) · **Where:** apps with uploads, long reports or websockets behind ingress-nginx; controller upgrades; migrations to Traefik · **Level:** [L2 · Mid] · **CKA:** Services and Networking · **How common:** ingress-nginx #13598 (79 reactions, 41 comments), #11176 (43 reactions), #9569 duplicated location blocks after a minor upgrade (53); the retirement notice #14178 drew 216 reactions

**Why it happens:** ingress-nginx accepts request bodies up to 1 MB and waits 60 seconds for the upstream by default, so uploads and slow reports fail until a per-Ingress annotation raises the limit. The controller renders one nginx.conf for the whole cluster, so a single bad value in its global ConfigMap takes every route down. Newer versions validate paths and annotations strictly and disable snippet annotations by default for security reasons, which breaks Ingresses that older versions tolerated. Traefik has different defaults and none of these annotations, which is the core of the migration work in 43 §8.5.

**Diagnose:**

```bash
kubectl -n ingress-nginx logs deploy/ingress-nginx-controller --tail=200 | grep -E 'emerg|too large body|upstream timed out' | tail -2
kubectl -n shop get ingress web -o jsonpath='{.metadata.annotations}'; echo
kubectl -n ingress-nginx get cm ingress-nginx-controller -o jsonpath='{.data}'; echo
```

```text
2026/10/04 11:20:41 [error] 1442#1442: *88123 client intended to send too large body: 52428800 bytes, client: 10.42.1.1, server: shop.example.com, request: "POST /api/upload HTTP/1.1", host: "shop.example.com"
2026/10/04 11:24:03 [error] 1442#1442: *88502 upstream timed out (110: Operation timed out) while reading response header from upstream, client: 10.42.1.1, server: shop.example.com, request: "GET /reports/yearly HTTP/1.1", upstream: "http://10.42.2.17:8080/reports/yearly", host: "shop.example.com"
{"cert-manager.io/cluster-issuer":"letsencrypt"}
{"allow-snippet-annotations":"false","proxy-busy-buffers-size":"256k"}
```

**What the output tells you:** a 50 MB upload hit the 1 MB default and a report took longer than 60 seconds; the Ingress carries no annotations to change either. The global proxy-busy-buffers-size is the kind of value that crashed controllers after the upgrade in #13598: check it against the new version's rules before upgrading.

**Fix:**

```yaml
# Per Ingress, only where needed (ingress-nginx)
metadata:
  annotations:
    nginx.ingress.kubernetes.io/proxy-body-size: "64m"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"
# Paths the strict validation rejects: pathType ImplementationSpecific for that one path
# Global ConfigMap: remove values the new version rejects, then watch the rollout
# The same app on Traefik: a buffering Middleware (maxRequestBodyBytes: 67108864) for the size,
# the entryPoint's transport.respondingTimeouts.readTimeout (60s by default in v3) for slow uploads;
# slow responses are cut only if you set serversTransport forwardingTimeouts.responseHeaderTimeout (default: none)
```

**Why this fix works:** limits rise only on the routes that need them, so every other route keeps the protective defaults. Don't set `proxy-body-size: "0"` globally (unlimited uploads invite resource exhaustion), and don't turn snippet annotations back on cluster-wide: they let anyone who can create an Ingress inject nginx configuration. Because ingress-nginx is retired, treat every change here as a step towards the migration rather than a permanent home.

**Prevent it:** keep an annotation inventory (43 §8.5 shows the one-liner), test controller upgrades on a staging cluster, and put curl assertions for status codes, redirects and upload size into CI.

**Next step:** [43 §8 Traefik on Kubernetes](43-traefik-and-reverse-proxies.md#8-traefik-tcp-auth-client-ip-and-kubernetes) · [Web servers & proxies](29-learn-webservers-proxies.md) · KodeKloud: *Kubernetes Troubleshooting for Application Developers* — What the Ingress? · [ingress-nginx docs](https://kubernetes.github.io/ingress-nginx/)

**Community threads:** [ingress-nginx #13598: proxy-busy-buffers-size keeps NGINX from starting](https://github.com/kubernetes/ingress-nginx/issues/13598) · [ingress-nginx #11176: strict path validation](https://github.com/kubernetes/ingress-nginx/issues/11176) · [ingress-nginx #9569: duplicated location block](https://github.com/kubernetes/ingress-nginx/issues/9569) · [ingress-nginx #14178: So long, and thanks for all the fish](https://github.com/kubernetes/ingress-nginx/issues/14178) · [Kubernetes blog: Ingress NGINX Retirement](https://www.kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/) · [Kubernetes blog: Before You Migrate](https://kubernetes.io/blog/2026/02/27/ingress-nginx-before-you-migrate/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=ingress-nginx+413+proxy-body-size) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=ingress-nginx+504+timeout+annotation&restrict_sr=1)

---

## 7. Certificates: cert-manager

cert-manager turns Certificate objects into TLS secrets. When it fails, the Certificate stays not Ready and the old certificate quietly counts down to expiry, so read the chain top-down: Certificate → CertificateRequest → Order → Challenge.

### 7.1 HTTP-01 self check fails

> **Seen as:** `Waiting for HTTP-01 challenge propagation: failed to perform self check GET request 'http://shop.example.com/.well-known/acme-challenge/...': ... dial tcp 203.0.113.10:80: connect: connection timed out`, or `wrong status code '404', expected '200'` · **Where:** on-prem clusters behind a router with port forwarding; a global HTTPS redirect or auth middleware; a solver that uses the wrong ingress class; proxy protocol on the load balancer · **Level:** [L2 · Mid] · **CKA:** Services and Networking · **How common:** cert-manager #656 (68 comments), #2517 (86), #466 on proxy protocol (83), and #1292 asking to skip the self-check (122 comments, 87 reactions)

**Why it happens:** before cert-manager asks Let's Encrypt to validate, it fetches the challenge URL itself from inside the cluster. A pod resolves shop.example.com to the router's public address 203.0.113.10, and many routers don't loop traffic from the LAN back to their own public address (hairpin NAT), so the self-check times out even though Let's Encrypt, coming from outside, would succeed. A 404 means the request arrived at a controller with no route for the challenge path: the solver's temporary Ingress uses a class no controller serves (6.2), or an entryPoint-wide HTTPS redirect or auth middleware catches the path first. A controller that expects the PROXY protocol rejects the plain request the self-check sends.

**Diagnose:**

```bash
kubectl get certificate,challenge -A
kubectl -n shop describe challenge | grep -E 'Reason|State'
# The same request cert-manager makes, from inside the cluster
kubectl run curl --rm -it --restart=Never --image=curlimages/curl -- curl -sv -m5 http://shop.example.com/.well-known/acme-challenge/test
# Then the same URL from outside (a phone on mobile data, or a cloud VM)
```

```text
NAMESPACE   NAME                                   READY   SECRET     AGE
shop        certificate.cert-manager.io/shop-tls   False   shop-tls   38m
NAMESPACE   NAME                                                              STATE     DOMAIN             AGE
shop        challenge.acme.cert-manager.io/shop-tls-1-2840710231-1902714512   pending   shop.example.com   38m
  Reason:      Waiting for HTTP-01 challenge propagation: failed to perform self check GET request 'http://shop.example.com/.well-known/acme-challenge/Xr2kq0tYv6bJ': Get "http://shop.example.com/.well-known/acme-challenge/Xr2kq0tYv6bJ": dial tcp 203.0.113.10:80: connect: connection timed out
  State:       pending
*   Trying 203.0.113.10:80...
* Connection timed out after 5001 milliseconds
```

**What the output tells you:** inside the cluster the name resolves to the public address and the router doesn't hairpin it. If the outside test reaches the site, users are fine and only the self-check is blocked. A 404 from the inside curl would point at the class or redirect problem instead.

**Fix:**

```bash
# Option 1: split-horizon DNS: inside the LAN, shop.example.com points at the ingress IP (10.20.0.200).
# Either on the LAN DNS server, or for the cluster only in the CoreDNS Corefile:
#   hosts {
#     10.20.0.200 shop.example.com
#     fallthrough
#   }
kubectl -n kube-system edit cm coredns
# Option 2: enable NAT loopback (hairpin NAT) on the router, if it supports it
# Option 3: use DNS-01 instead (7.2): no inbound HTTP at all, and it works for wildcards
```

```yaml
# A 404 instead: make the solver use the controller that owns port 80
solvers:
  - http01:
      ingress:
        ingressClassName: traefik
# With Traefik, prefer a redirect Middleware on the app routers over an entryPoint-wide
# redirect, so the solver's plain-HTTP route still answers on port 80
```

**Why this fix works:** the self-check now reaches the ingress directly over the LAN, passes, and Let's Encrypt validates from the internet as before. Don't skip or disable the self-check: it then fails later at Let's Encrypt, where failed validations count against rate limits (7.3). Don't experiment against the production issuer at all; use the staging ClusterIssuer until the chain works.

**Prevent it:** document the split-horizon records next to the port forwards, start every new hostname on the staging issuer, and alert on Certificates not Ready for more than an hour and on expiry within 14 days.

**Next step:** [Web, HTTP & TLS](18-web-http-tls.md) · [43 §6 Traefik certificates](43-traefik-and-reverse-proxies.md#6-traefik-certificates) · KodeKloud: *Kubernetes Networking Deep Dive* — Network Security: Cert Manager and Let's Encrypt, Lab: Securing Ingress · [cert-manager docs](https://cert-manager.io/docs/)

**Community threads:** [cert-manager #656: http-01 self check failed](https://github.com/cert-manager/cert-manager/issues/656) · [cert-manager #2517: wrong status code 404, expected 200](https://github.com/cert-manager/cert-manager/issues/2517) · [cert-manager #466: proxy_protocol breaks the HTTP01 check](https://github.com/cert-manager/cert-manager/issues/466) · [cert-manager #1292: skipping the self-check](https://github.com/cert-manager/cert-manager/issues/1292) · Search: [Stack Overflow](https://stackoverflow.com/search?q=cert-manager+%22failed+to+perform+self+check%22) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=cert-manager+self+check+hairpin+nat&restrict_sr=1)

### 7.2 DNS-01 stuck: record not yet propagated

> **Seen as:** `Waiting for DNS-01 challenge propagation: DNS record for "shop.example.com" not yet propagated` for hours, or `Error presenting challenge` with an authentication error from the DNS provider · **Where:** split-horizon networks where the office or home DNS server also answers for example.com, API tokens with too few rights, wildcard certificates · **Level:** [L3 · Senior] · **CKA:** beyond the exam · **How common:** cert-manager #5917 (64 comments, still open)

**Why it happens:** after creating the TXT record through the provider's API, cert-manager waits until the record is visible on the zone's authoritative nameservers, which it discovers through the resolvers in its own resolv.conf, that is CoreDNS and then your LAN DNS. If the LAN DNS hosts an internal copy of example.com, it answers with the internal zone, which will never contain the TXT record, so the check never passes. Provider errors usually mean a token without permission to edit that zone.

**Diagnose:**

```bash
kubectl -n cert-manager logs deploy/cert-manager --since=10m | grep -iE 'propagat|error presenting' | tail -1
dig +short TXT _acme-challenge.shop.example.com @1.1.1.1          # what the world sees
dig +short NS example.com @1.1.1.1; dig +short NS example.com @10.20.0.1
```

```text
E1004 12:02:11.481022       1 sync.go:...] "propagation check failed" err="DNS record for \"shop.example.com\" not yet propagated" logger="cert-manager.controller" type="DNS-01"
"Kq0tYv6bJ0m2W7gq8L1r9pX3dZ5cN4aF0sE2uH7iT1o"
ns1.example.net.
ns2.example.net.
dc1.corp.example.com.
```

**What the output tells you:** the TXT record is live on the public nameservers, but the LAN DNS (10.20.0.1) claims to be authoritative for example.com itself, so every check cert-manager makes through it looks at the internal zone.

**Fix:**

```yaml
# cert-manager Helm values: check propagation through public resolvers only
extraArgs:
  - --dns01-recursive-nameservers-only
  - --dns01-recursive-nameservers=1.1.1.1:53,8.8.8.8:53
---
# A DNS-01 ClusterIssuer with a token limited to one zone (Cloudflare: Zone Read + DNS Edit)
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: letsencrypt-dns }
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: ops@example.com
    privateKeySecretRef: { name: letsencrypt-dns-account }
    solvers:
      - selector: { dnsZones: ["example.com"] }
        dns01:
          cloudflare:
            apiTokenSecretRef: { name: cloudflare-token, key: api-token }
```

```bash
helm upgrade cert-manager jetstack/cert-manager -n cert-manager --reuse-values -f cert-manager-values.yaml
```

**Why this fix works:** public resolvers see the real zone, so the propagation check succeeds as soon as the record is live, and the issuance continues. A token scoped to one zone limits the damage if the Secret leaks. Don't use the provider's global API key, and don't "fix" it by making the LAN DNS forward the whole zone: you lose the internal names the split was for.

**Prevent it:** make split-horizon a deliberate design (or use a separate internal zone such as internal.example.com), test new issuers against staging, and alert when a Certificate stays not Ready.

**Next step:** [DNS commands](08-dns.md) · [43 §6 Traefik certificates](43-traefik-and-reverse-proxies.md#6-traefik-certificates) (Traefik's DNS-01 meets the same split-horizon trap) · KodeKloud: *Kubernetes Networking Deep Dive* — Cert Manager and Let's Encrypt · [cert-manager docs](https://cert-manager.io/docs/)

**Community threads:** [cert-manager #5917: DNS record not yet propagated](https://github.com/cert-manager/cert-manager/issues/5917) · Search: [Stack Overflow](https://stackoverflow.com/search?q=cert-manager+dns01+%22not+yet+propagated%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=cert-manager+dns01+propagated+split+dns&restrict_sr=1)

### 7.3 Certificate not Ready: issuer, rate limits, secret

> **Seen as:** a CertificateRequest with `Referenced "Issuer" not found: issuer.cert-manager.io "letsencrypt" not found`; an Order failing with `429 urn:ietf:params:acme:error:rateLimited: too many certificates (5) already issued for this exact set of identifiers in the last 168h0m0s`; an Ingress whose TLS secret lives in another namespace · **Where:** Issuer and ClusterIssuer mix-ups, debugging loops against production Let's Encrypt, a wildcard certificate wanted in many namespaces, internal names that need your private CA · **Level:** [L2 · Mid] · **CKA:** beyond the exam (TLS) · **How common:** cert-manager #407 "hits Let's Encrypt too aggressively" (69 comments) and #494 on syncing secrets between namespaces (60)

**Why it happens:** an Issuer is namespaced and a ClusterIssuer is not, and the Ingress annotation must say which one (`cert-manager.io/issuer` or `cert-manager.io/cluster-issuer`). Let's Encrypt limits duplicate certificates to five per week for the same set of names and also limits failed validations, so deleting and recreating a Certificate while debugging burns the budget. A TLS secret is only usable in its own namespace, and cert-manager doesn't copy secrets. Names that exist only inside your network can't get public certificates at all; they need a CA issuer backed by your private CA, the one Harbor already uses.

**Diagnose:**

```bash
kubectl -n shop get certificate,certificaterequest,order
kubectl -n shop describe certificaterequest shop-tls-1 | grep -E 'Message|Reason' | head -2
kubectl get clusterissuer; kubectl -n shop get issuer
kubectl -n shop get ingress web -o jsonpath='{.metadata.annotations}'; echo
```

```text
NAME                                   READY   SECRET     AGE
certificate.cert-manager.io/shop-tls   False   shop-tls   12m
NAME                                            APPROVED   DENIED   READY   ISSUER        REQUESTER                                         AGE
certificaterequest.cert-manager.io/shop-tls-1   True                False   letsencrypt   system:serviceaccount:cert-manager:cert-manager   12m
    Message:  Referenced "Issuer" not found: issuer.cert-manager.io "letsencrypt" not found
NAME          READY   AGE
letsencrypt   True    90d
No resources found in shop namespace.
{"cert-manager.io/issuer":"letsencrypt"}
```

**What the output tells you:** the Ingress asks for a namespaced Issuer called letsencrypt in shop, which doesn't exist; only a ClusterIssuer of that name does. Nothing has been sent to Let's Encrypt yet, so no rate limit has been touched.

**Fix:**

```bash
# Point the Ingress at the ClusterIssuer
kubectl -n shop annotate ingress web cert-manager.io/issuer- cert-manager.io/cluster-issuer=letsencrypt
# Rate-limited: stop recreating objects, switch to the staging issuer until the chain works,
# then wait for the window the error message names before going back to production
# The same certificate in another namespace: one Certificate per namespace,
# or a deliberate secret-mirroring tool with an allow-list of target namespaces
```

```yaml
# Internal names (harbor.example.com, grafana.internal.example.com): issue from your private CA
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata: { name: internal-ca }
spec:
  ca:
    secretName: internal-ca-keypair    # an intermediate CA's tls.crt and tls.key, in the cert-manager namespace
```

**Why this fix works:** the request now names an issuer that exists and is Ready, so the Order goes out once. Give cert-manager an intermediate CA, never the root key: if the cluster is compromised, you revoke the intermediate and keep the root offline. Every client (browsers, containerd, CI runners) must trust that root for internal certificates to work.

**Prevent it:** keep exactly two public ClusterIssuers (staging and production) with clear names, alert on `certmanager_certificate_expiration_timestamp_seconds`, and check status with `cmctl status certificate` before touching anything.

**Next step:** [Web, HTTP & TLS](18-web-http-tls.md) · [Security & DevSecOps](37-learn-security-devsecops.md) (PKI) · KodeKloud: [*TLS Basics*](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics) · *Kubernetes Networking Deep Dive* — Lab: Securing Ingress · [cert-manager docs](https://cert-manager.io/docs/)

**Community threads:** [cert-manager #407: hits Let's Encrypt too aggressively](https://github.com/cert-manager/cert-manager/issues/407) · [cert-manager #494: syncing secrets between namespaces](https://github.com/cert-manager/cert-manager/issues/494) · Search: [Stack Overflow](https://stackoverflow.com/search?q=cert-manager+certificate+not+ready+%22issuer%22+not+found) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=cert-manager+rate+limit+letsencrypt&restrict_sr=1)

---

## 8. Load balancers: MetalLB, ServiceLB and AWS

A LoadBalancer Service needs something outside Kubernetes to hand out an address. In the cloud that is the provider; on-prem it is MetalLB (or k3s's ServiceLB), and its failure modes are layer-2 networking problems.

### 8.1 LoadBalancer EXTERNAL-IP stays pending

> **Seen as:** `kubectl get svc` shows EXTERNAL-IP as pending for hours, and `kubectl describe svc` shows no events at all, or on EKS an event such as `Failed build model due to unable to resolve at least one subnet` · **Where:** kubeadm on bare metal or VMs, MetalLB installed but never configured, EKS without the AWS Load Balancer Controller · **Level:** [L1 · Junior] · **CKA:** Services and Networking · **How common:** a rite of passage for every on-prem cluster; MetalLB's "Do you use MetalLB? Tell us!" issue #5 has 252 comments, and the MicroK8s MetalLB add-on thread on discuss.kubernetes.io about 15k views

**Why it happens:** a Service of type LoadBalancer only asks for an address; some controller outside the core must provide it. Clouds run one; kubeadm on your own hardware has none, so the Service waits forever (its NodePort still works, which hides the problem). MetalLB has been configured through custom resources since v0.13, so installing it without an IPAddressPool and an L2Advertisement still hands out nothing. k3s answers with ServiceLB, which uses the nodes' own addresses. On EKS, the AWS Load Balancer Controller needs IAM rights and subnets tagged for load balancers.

**Diagnose:**

```bash
kubectl -n shop get svc web
kubectl -n shop describe svc web | sed -n '/Events:/,$p'
kubectl get pods -A | grep -Ei 'metallb|svclb|load-balancer-controller'
```

```text
NAME   TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
web    LoadBalancer   10.96.41.207   <pending>     80:31877/TCP   3h
Events:            <none>
metallb-system   controller-5f9bb77dcd-7xkq2   1/1   Running   0   3h
metallb-system   speaker-4hq8m                 1/1   Running   0   3h
```

**What the output tells you:** MetalLB runs but never even tried: no event on the Service means no address pool matches. On EKS, the same check usually shows an event from the controller that names the missing subnet tag or IAM permission.

**Fix:**

<div class="env" data-env="onprem" markdown="1">

Give MetalLB a range that your DHCP server never hands out, and announce it on the LAN. On k3s, disable ServiceLB first (`disable: [servicelb]` in /etc/rancher/k3s/config.yaml), or both will act on the same Services.

```yaml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata: { name: lan-pool, namespace: metallb-system }
spec:
  addresses: ["10.20.0.200-10.20.0.220"]
---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata: { name: lan-l2, namespace: metallb-system }
spec:
  ipAddressPools: ["lan-pool"]
```

</div>

<div class="env" data-env="cloud" markdown="1">

On EKS the AWS Load Balancer Controller creates an NLB for the Service. Check that it runs, that its IAM role works, and that the subnets carry `kubernetes.io/role/elb=1` (public) or `kubernetes.io/role/internal-elb=1` (internal).

```bash
kubectl -n kube-system get deploy aws-load-balancer-controller
kubectl -n kube-system logs deploy/aws-load-balancer-controller | grep -i error | tail -2
aws ec2 describe-subnets --filters Name=vpc-id,Values=VPC_ID --query 'Subnets[].[SubnetId,Tags[?Key==`kubernetes.io/role/elb`].Value|[0]]' --output text
# On the Service:
#   service.beta.kubernetes.io/aws-load-balancer-type: external
#   service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: ip
#   service.beta.kubernetes.io/aws-load-balancer-scheme: internet-facing
```

</div>

**Why this fix works:** MetalLB's controller now has a pool to allocate from and its speakers announce the address with ARP; on EKS the controller can place an NLB in correctly tagged subnets. Don't work around it with the Service `externalIPs` field: anyone allowed to set it can intercept traffic for any address, which is why many clusters block it. Don't let the MetalLB range overlap DHCP, or two machines end up with the same address.

**Prevent it:** reserve the range in DHCP or your IPAM and write it into [Who owns this port?](22-playbook-ports-inventory.md); on AWS, tag subnets in Terraform together with the VPC.

**Next step:** [31 §7 Services](31-learn-kubernetes.md#7-services) · [On-prem vs cloud: same symptom, different first moves](55-paths-onprem-vs-cloud.md#2-same-symptom-different-first-moves) · [Kubernetes quick reference: EKS specifics](15-kubernetes.md#8-eks-specifics-aws) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Networking (Services) · [MetalLB docs](https://metallb.io/) · [Amazon EKS docs](https://docs.aws.amazon.com/eks/)

**Community threads:** [discuss.kubernetes.io: Addon: MetalLB](https://discuss.kubernetes.io/t/addon-metallb/11790) · [metallb #5: Do you use MetalLB?](https://github.com/metallb/metallb/issues/5) · Search: [Stack Overflow](https://stackoverflow.com/search?q=loadbalancer+external-ip+pending+bare+metal+metallb) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=metallb+external+ip+pending&restrict_sr=1)

### 8.2 MetalLB IP assigned but unreachable

> **Seen as:** the Service shows EXTERNAL-IP 10.20.0.200, but curl from the LAN times out or works only sometimes; several MAC addresses answer `arping` for one IP; failover after a node reboot takes minutes · **Where:** kube-proxy in IPVS mode, node VMs on Proxmox or VMware with MAC filtering, Wi-Fi bridges, speakers missing from some nodes · **Level:** [L2 · Mid] · **CKA:** Services and Networking · **How common:** MetalLB #1154 "provides IPs but doesn't ARP for the address" (31 comments), #153 "kube-proxy in IPVS mode breaks MetalLB IPs" (40), #298 "Failover time very high in layer2 mode" (44) and #888 "MemberList Secret not Created" (49)

**Why it happens:** in layer-2 mode one speaker per Service answers ARP for the address with its node's MAC, the LAN sends all traffic there, and kube-proxy forwards it to the pods. kube-proxy in IPVS mode puts every service address on a dummy interface on every node, so without `strictARP` all nodes answer and the switch keeps moving the address between them. Hypervisor MAC or IP filters drop the speaker's gratuitous ARP, Wi-Fi access points ignore ARP for addresses they didn't assign, and a speaker that isn't scheduled on a node (taints, node selectors) can't announce from it. Failover waits for MetalLB to detect the dead node and for clients' ARP caches to expire, so seconds to minutes in L2 is normal.

**Diagnose:**

```bash
kubectl -n shop get svc web
sudo arping -I enp0s8 -c 3 10.20.0.200            # from another machine on the LAN
kubectl -n metallb-system get pods -o wide | grep speaker
kubectl -n kube-system get cm kube-proxy -o jsonpath='{.data.config\.conf}' | grep -E '^mode|strictARP'
```

```text
NAME   TYPE           CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
web    LoadBalancer   10.96.41.207   10.20.0.200   80:31877/TCP   2d
ARPING 10.20.0.200 from 10.20.0.99 enp0s8
Unicast reply from 10.20.0.200 [52:54:00:3A:91:0C]  0.412ms
Unicast reply from 10.20.0.200 [52:54:00:8F:22:71]  0.398ms
Unicast reply from 10.20.0.200 [52:54:00:C4:5E:19]  0.441ms
speaker-4hq8m   1/1   Running   0   2d   10.20.0.10   cp-1   <none>   <none>
speaker-9w2lk   1/1   Running   0   2d   10.20.0.21   wk-1   <none>   <none>
speaker-tq7cd   1/1   Running   0   2d   10.20.0.22   wk-2   <none>   <none>
mode: ipvs
  strictARP: false
```

**What the output tells you:** three different MACs answer for one address: every node replies because kube-proxy runs IPVS without strictARP. The speakers themselves are fine. A single MAC with no reply reaching the client would point at a hypervisor or Wi-Fi filter instead.

**Fix:**

```bash
# IPVS mode: only MetalLB may answer ARP for service addresses
kubectl -n kube-system get cm kube-proxy -o yaml | sed -e 's/strictARP: false/strictARP: true/' | kubectl apply -f -
kubectl -n kube-system rollout restart ds/kube-proxy
# Hypervisor filters: allow MAC changes and forged transmits on the VMs' port group (VMware),
# or relax the IP/MAC filter for the node VMs in the Proxmox firewall
# Speakers on every node that should announce: compare their tolerations with the node taints
kubectl -n metallb-system get ds speaker -o jsonpath='{.spec.template.spec.tolerations}'; echo
# Need sub-second failover? Use BGP mode with your router instead of L2
```

**Why this fix works:** with strictARP only the elected speaker answers, so the switch learns one location for the address and keeps it until a real failover. Note that kube-proxy's IPVS mode has been deprecated since Kubernetes 1.35; nftables mode (GA since 1.33) is the recommended replacement, and in iptables or nftables mode this ARP problem does not arise, so plan the mode change for new and rebuilt clusters. Don't put service addresses behind Wi-Fi bridges, and don't let keepalived manage addresses from the same range as MetalLB.

**Prevent it:** probe every load-balancer address from outside the cluster (blackbox or Uptime Kuma, see [Observability problems](49-observability-stack-problems.md)), test failover by draining the announcing node, and keep the MetalLB pool in the network documentation.

**Next step:** [Networking course](28-learn-networking.md) (ARP) · [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) · KodeKloud: *Kubernetes Networking Deep Dive* — Services · [MetalLB docs](https://metallb.io/)

**Community threads:** [metallb #1154: no ARP for the address](https://github.com/metallb/metallb/issues/1154) · [metallb #153: kube-proxy IPVS breaks MetalLB IPs](https://github.com/metallb/metallb/issues/153) · [metallb #298: slow failover in layer2](https://github.com/metallb/metallb/issues/298) · [metallb #888: MemberList Secret not Created](https://github.com/metallb/metallb/issues/888) · Search: [Stack Overflow](https://stackoverflow.com/search?q=metallb+layer2+ip+not+reachable+arp) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=metallb+arp+not+reachable&restrict_sr=1)

---

## 9. Storage: local-path, Longhorn and NFS

Storage problems show up as pods stuck in Pending or ContainerCreating, and they are the ones where a wrong "fix" loses data. Read the events of the PVC and the pod before you change anything.

### 9.1 PVC Pending, or a pod pinned to a dead node

> **Seen as:** `no persistent volumes available for this claim and no storage class is set`; `waiting for first consumer to be created before binding`; or, after a node died, `0/3 nodes are available: 1 node(s) had untolerated taint {node.kubernetes.io/unreachable: }, 2 node(s) had volume node affinity conflict` · **Where:** kubeadm clusters with no provisioner, k3s with its default local-path class, NFS classes on nodes without the NFS client · **Level:** [L1 · Junior] · **CKA:** Storage · **How common:** PVC Pending is a fixed CKA storage task; discuss.kubernetes.io "Use NFS for Persistent Volumes on MicroK8s" has 31k views

**Why it happens:** kubeadm ships no dynamic provisioner and no default StorageClass, so a claim without a class waits for a PersistentVolume someone creates by hand. "Waiting for first consumer" is normal with `WaitForFirstConsumer` classes: the volume is created only when a pod using it is scheduled. local-path (k3s's default) creates the volume as a directory on one node's disk and pins it there with node affinity, so if that node dies, the pod can't start anywhere else: the data physically lives on the dead machine. NFS-backed classes fail at mount time when nfs-common is missing on the node.

**Diagnose:**

```bash
kubectl get sc
kubectl -n db describe pod postgres-0 | sed -n '/Events:/,$p' | tail -1
kubectl get pv -o custom-columns=NAME:.metadata.name,CLAIM:.spec.claimRef.name,NODE:.spec.nodeAffinity.required.nodeSelectorTerms[0].matchExpressions[0].values[0]
kubectl get nodes
```

```text
NAME                   PROVISIONER             RECLAIMPOLICY   VOLUMEBINDINGMODE      ALLOWVOLUMEEXPANSION   AGE
local-path (default)   rancher.io/local-path   Delete          WaitForFirstConsumer   false                  60d
  Warning  FailedScheduling  2m  default-scheduler  0/3 nodes are available: 1 node(s) had untolerated taint {node.kubernetes.io/unreachable: }, 2 node(s) had volume node affinity conflict. preemption: 0/3 nodes are available: 3 Preemption is not helpful for scheduling.
NAME                                       CLAIM               NODE
pvc-3b1f0c2e-7a9d-4e1b-9c2f-0d8e7a6b5c41   data-postgres-0     k3s-2
NAME    STATUS     ROLES                       AGE   VERSION
k3s-1   Ready      control-plane,etcd,master   60d   v1.35.3+k3s1
k3s-2   NotReady   control-plane,etcd,master   60d   v1.35.3+k3s1
k3s-3   Ready      control-plane,etcd,master   60d   v1.35.3+k3s1
```

**What the output tells you:** postgres-0's volume is a directory on k3s-2, which is down. The scheduler is right to refuse: no other node has that data. This is a storage design problem, not a scheduler bug.

**Fix:**

<div class="env" data-env="onprem" markdown="1">

```bash
# Fresh kubeadm cluster: install a provisioner and make one class the default
kubectl apply -f https://raw.githubusercontent.com/rancher/local-path-provisioner/LPP_VERSION/deploy/local-path-storage.yaml
kubectl patch storageclass local-path -p '{"metadata":{"annotations":{"storageclass.kubernetes.io/is-default-class":"true"}}}'
# NFS-backed classes: the client on EVERY node
sudo apt-get install -y nfs-common
# A pod pinned to a dead node's local-path volume:
#   1. bring the node back if at all possible: the data is on its disk
#   2. otherwise restore from backup into a new PVC, then remove the old claim
kubectl -n db delete pvc data-postgres-0       # only once the data is safe elsewhere
```

</div>

<div class="env" data-env="cloud" markdown="1">

On EKS the default class needs the EBS CSI driver add-on with its IAM role; without it, claims wait with `waiting for a volume to be created either by the external provisioner "ebs.csi.aws.com"`. EBS volumes live in one availability zone, so the same node-affinity conflict appears when the only healthy nodes are in another zone: keep a node group per zone or use EFS for data that must move between zones.

```bash
aws eks describe-addon --cluster-name CLUSTER --addon-name aws-ebs-csi-driver --query 'addon.status'
kubectl -n kube-system get pods -l app=ebs-csi-controller
```

</div>

**Why this fix works:** a default class lets claims bind without manual PVs, and the client tools make NFS mounts possible. For the pinned volume there is no Kubernetes-level fix, because the data is local: either the node returns or a backup does. Don't delete a PVC to "unstick" a pod before you know where its data is; with the Delete reclaim policy the volume goes too.

**Prevent it:** choose storage per workload: anything for stateless apps, replicated storage (9.2) plus backups for databases, and local-path only for data you can rebuild. Test a restore before you need it ([Databases, storage & backups](51-problems-databases-storage-backup.md)).

**Next step:** [31 §11 Storage](31-learn-kubernetes.md#11-storage) · [26 §10 nodes, storage and control plane](26-playbook-containers-k8s.md#10-kubernetes-nodes-storage-and-control-plane) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Storage · *Kubernetes Troubleshooting for Application Developers* — Pending Pods · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [discuss.kubernetes.io: Use NFS for Persistent Volumes on MicroK8s](https://discuss.kubernetes.io/t/use-nfs-for-persistent-volumes-on-microk8s/19035) · Search: [Stack Overflow](https://stackoverflow.com/search?q=pvc+pending+%22waiting+for+first+consumer%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=local-path+volume+node+affinity+conflict&restrict_sr=1)

### 9.2 Longhorn volume won't attach or mount

> **Seen as:** `MountVolume.MountDevice failed ... /dev/longhorn/pvc-... is apparently in use by the system; will not make a filesystem here!`; `AttachVolume.Attach failed` with iscsiadm errors; RWX volumes failing with `mount.nfs: Protocol not supported`; volumes that won't attach after a Longhorn upgrade · **Where:** Ubuntu Server nodes (multipathd is enabled by default), nodes without open-iscsi or nfs-common, Longhorn upgrades · **Level:** [L2 · Mid] · **CKA:** Storage (beyond the exam) · **How common:** Longhorn's most-discussed bugs include RWX broken in 1.4.0 (#5183, 133 comments), manager pods using 20 GB of RAM in 1.5.1 (#6866, 125), RWX attachment failures (#5456, 76), PVC mount timeouts (#6188, 74) and a failed 1.5.0 conversion webhook (#6259, 72); Longhorn's knowledge base has an article on the multipathd case

**Why it happens:** Longhorn presents each volume to the node as an iSCSI disk (/dev/sdX, linked as /dev/longhorn/NAME). Ubuntu Server runs multipathd, which claims every new sdX and builds a multipath device on top, so mkfs and mount find the disk busy. Every node also needs the iSCSI initiator (open-iscsi with iscsid running), and RWX volumes are served over NFSv4 by a share-manager pod, so nodes need nfs-common. Longhorn upgrades are supported one minor version at a time; skipped versions or an interrupted engine upgrade leave volumes that refuse to attach.

**Diagnose:**

```bash
kubectl -n shop describe pod web-0 | sed -n '/Events:/,$p' | tail -2
# on the node that should mount it
systemctl is-active iscsid multipathd
dpkg -l open-iscsi nfs-common | awk '/^ii/ {print $2, $3}'
sudo multipath -ll | head -2
kubectl -n longhorn-system get volumes.longhorn.io -o custom-columns=NAME:.metadata.name,STATE:.status.state,ROBUSTNESS:.status.robustness,NODE:.status.currentNodeID
```

```text
  Warning  FailedMount  12s (x7 over 2m)  kubelet  MountVolume.MountDevice failed for volume "pvc-8d2e1f4a-6c3b-4f2e-9a1d-7b0e5c4d3a21" : rpc error: code = Internal desc = format of disk "/dev/longhorn/pvc-8d2e1f4a-6c3b-4f2e-9a1d-7b0e5c4d3a21" failed: type:("ext4") ... output:(mke2fs 1.47.0 (5-Feb-2023)
/dev/longhorn/pvc-8d2e1f4a-6c3b-4f2e-9a1d-7b0e5c4d3a21 is apparently in use by the system; will not make a filesystem here!)
active
active
open-iscsi 2.1.9-3ubuntu5
nfs-common 1:2.6.4-3ubuntu5
mpatha (360000000000000000e00000000010001) dm-2 IET,VIRTUAL-DISK
size=10G features='0' hwhandler='0' wp=rw
NAME                                       STATE      ROBUSTNESS   NODE
pvc-8d2e1f4a-6c3b-4f2e-9a1d-7b0e5c4d3a21   attached   healthy      wk-1
```

**What the output tells you:** Longhorn did its part (attached, healthy, on wk-1), and the prerequisites are installed. multipathd then wrapped Longhorn's iSCSI disk (vendor IET) in mpatha, so mke2fs refuses to touch it. The cause is the node's multipath configuration, not Longhorn.

**Fix:**

```bash
# Keep multipathd away from Longhorn's disks (Longhorn KB). If the node uses SAN multipath
# for its own disks, blacklist Longhorn by vendor/product (IET, VIRTUAL-DISK) instead of all sd devices
cat <<'EOF' | sudo tee -a /etc/multipath.conf
blacklist {
    devnode "^sd[a-z0-9]+"
}
EOF
sudo systemctl restart multipathd
# Missing prerequisites on any node
sudo apt-get install -y open-iscsi nfs-common && sudo systemctl enable --now iscsid
# Let the pod retry the mount
kubectl -n shop delete pod web-0
```

**Why this fix works:** without multipath sitting on top, the device is free and the CSI driver formats and mounts it. Upgrades need the same care: one minor version at a time, release notes and the knowledge base read first, and a backup of every volume to the S3 target before you start. Don't format or delete a Longhorn volume by hand to get past an attach error: that is how replicas, and data, get lost.

**Prevent it:** run Longhorn's environment check on every node before installing and when you add nodes, bake open-iscsi, nfs-common and the multipath blacklist into the node image, pin the chart version, and watch the manager pods' memory after each upgrade.

**Next step:** [Databases, storage & backups](51-problems-databases-storage-backup.md) · [Storage & disk](01-storage-disk.md) · [31 §11 Storage](31-learn-kubernetes.md#11-storage) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Storage · [Longhorn docs](https://longhorn.io/docs/)

**Community threads:** [Longhorn KB: MountVolume.SetUp failed due to multipathd](https://longhorn.io/kb/troubleshooting-volume-with-multipath/) · [Longhorn KB: volumes fail to attach after upgrading to v1.5.x](https://longhorn.io/kb/troubleshooting-volume-cannot-attach-due-to-orphan-pending-node-id-or-longhorn-ui-ad-ticket/) · [longhorn #6188: PVC mount timeout](https://github.com/longhorn/longhorn/issues/6188) · [longhorn #5456: RWX attachment failed](https://github.com/longhorn/longhorn/issues/5456) · [longhorn #6866: manager pods using 20 GB RAM](https://github.com/longhorn/longhorn/issues/6866) · Search: [Stack Overflow](https://stackoverflow.com/search?q=longhorn+%22apparently+in+use+by+the+system%22) · [Reddit r/homelab](https://www.reddit.com/r/homelab/search/?q=longhorn+multipath+mount+failed&restrict_sr=1)

### 9.3 Multi-Attach error after a node dies

> **Seen as:** `Multi-Attach error for volume "pvc-..." Volume is already exclusively attached to one node and can't be attached to another`; the replacement pod stays in ContainerCreating while the old node is down · **Where:** StatefulSets and Deployments with ReadWriteOnce volumes (Longhorn, iSCSI, EBS) when a node is powered off without draining; RollingUpdate Deployments that mount an RWO volume · **Level:** [L2 · Mid] · **CKA:** Troubleshooting (Storage) · **How common:** a discuss.kubernetes.io thread on the exact message; kubernetes #65392 "AttachDetachController fails to force detach on pod deletion" (124 comments); "Multi-Attach Volume Errors" is a KodeKloud scenario

**Why it happens:** a ReadWriteOnce volume may be attached to one node at a time, and the VolumeAttachment still says it belongs to the node that died. Kubernetes can't tell a powered-off node from one that is only cut off from the network and may still be writing, so it refuses to attach the volume elsewhere rather than risk two writers corrupting the filesystem. The non-graceful node shutdown feature lets you state that the node is really down. A RollingUpdate Deployment hits the same error on every rollout, because the new pod starts on another node while the old one still holds the volume.

**Diagnose:**

```bash
kubectl -n db describe pod postgres-0 | sed -n '/Events:/,$p' | tail -1
kubectl get volumeattachment -o custom-columns=PV:.spec.source.persistentVolumeName,NODE:.spec.nodeName,ATTACHED:.status.attached
kubectl get node wk-2
```

```text
  Warning  FailedAttachVolume  3m  attachdetach-controller  Multi-Attach error for volume "pvc-41c7e2d9-5d8a-4c1f-b2e7-9a0c3f6d1e58" Volume is already exclusively attached to one node and can't be attached to another
PV                                         NODE   ATTACHED
pvc-41c7e2d9-5d8a-4c1f-b2e7-9a0c3f6d1e58   wk-2   true
NAME   STATUS     ROLES    AGE   VERSION
wk-2   NotReady   <none>   80d   v1.35.3
```

**What the output tells you:** the volume is still attached to wk-2, which is NotReady. Before doing anything, find out whether wk-2 is off or merely unreachable: that decides whether the next step is safe.

**Fix:**

```bash
# 1. Confirm wk-2 is really powered off (IPMI, hypervisor console). If it might still run, stop here.
# 2. Declare it out of service: its pods are deleted and their volumes force-detached
kubectl taint nodes wk-2 node.kubernetes.io/out-of-service=nodeshutdown:NoExecute
# 3. When wk-2 has been repaired and has rejoined, remove the taint
kubectl taint nodes wk-2 node.kubernetes.io/out-of-service=nodeshutdown:NoExecute-
# Deployments with an RWO volume: replace pods instead of overlapping them
#   spec.strategy.type: Recreate
```

**Why this fix works:** the out-of-service taint is your explicit statement that the node is fenced, so the attach/detach controller can move the volume without the two-writer risk. Don't delete VolumeAttachment objects or force-delete pods while the node might still be alive: a database written from two nodes is the worst outcome on this page.

**Prevent it:** configure graceful node shutdown (`shutdownGracePeriod`) so planned shutdowns detach cleanly, drain before maintenance, and use Recreate for every Deployment that mounts an RWO volume.

**Next step:** [31 §11 Storage](31-learn-kubernetes.md#11-storage) · [26 §10 nodes, storage and control plane](26-playbook-containers-k8s.md#10-kubernetes-nodes-storage-and-control-plane) · KodeKloud: *Kubernetes Troubleshooting for Application Developers* — Multi-Attach Volume Errors · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [discuss.kubernetes.io: Multi-Attach error for volume](https://discuss.kubernetes.io/t/multi-attach-error-for-volume-pvc-volume-is-already-exclusively-attached-to-one-node-and-cant-be-attached-to-another/18951) · [kubernetes #65392: force detach on pod deletion](https://github.com/kubernetes/kubernetes/issues/65392) · Search: [Stack Overflow](https://stackoverflow.com/search?q=%22Multi-Attach+error+for+volume%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=multi-attach+error+node+down&restrict_sr=1)

---

## 10. Metrics and autoscaling

`kubectl top` and the HorizontalPodAutoscaler both depend on metrics-server, which scrapes every kubelet over TLS. On kubeadm, that TLS step is where it fails.

### 10.1 metrics-server fails and the HPA shows unknown

> **Seen as:** `error: Metrics API not available` from `kubectl top`; metrics-server logging `x509: cannot validate certificate for 10.20.0.21 because it doesn't contain any IP SANs`; an HPA whose TARGETS column shows unknown instead of a percentage · **Where:** kubeadm clusters (self-signed kubelet serving certificates), nodes whose hostnames don't resolve inside the cluster, Deployments without CPU requests · **Level:** [L1 · Junior] · **CKA:** Workloads and Scheduling (autoscaling) · **How common:** metrics-server #131 (73 comments), #133 "x509: certificate signed by unknown authority" (65), #196 "doesn't contain any IP SANs" (44), #247 "metrics not available yet" (42) and #1282 "Metrics API not available" (36)

**Why it happens:** metrics-server scrapes each kubelet on port 10250 and verifies its serving certificate, but on kubeadm the kubelets present self-signed certificates that the cluster CA never signed and that often lack the node's IP. Verification fails, the APIService turns unavailable, and both `kubectl top` and every HPA lose their data. If metrics-server prefers hostnames that cluster DNS can't resolve, it fails with "no such host" instead. Separately, an HPA computes CPU utilisation as a percentage of the pod's request, so a container without a CPU request gives it nothing to compute.

**Diagnose:**

```bash
kubectl top nodes
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl -n kube-system logs deploy/metrics-server --tail=1
kubectl -n shop get hpa web
```

```text
error: Metrics API not available
NAME                     SERVICE                      AVAILABLE                      AGE
v1beta1.metrics.k8s.io   kube-system/metrics-server   False (FailedDiscoveryCheck)   20m
E1004 13:05:44.218907       1 scraper.go:149] "Failed to scrape node" err="Get \"https://10.20.0.21:10250/metrics/resource\": tls: failed to verify certificate: x509: cannot validate certificate for 10.20.0.21 because it doesn't contain any IP SANs" node="wk-1"
NAME   REFERENCE        TARGETS              MINPODS   MAXPODS   REPLICAS   AGE
web    Deployment/web   cpu: <unknown>/70%   2         10        2          20m
```

**What the output tells you:** metrics-server can't verify the kubelet's certificate, so the metrics API is down and the HPA has no numbers. Once metrics flow, an HPA event saying `missing request for cpu` would point at the Deployment instead.

**Fix:**

```bash
# Proper fix: kubelet serving certificates signed by the cluster CA
# 1. Every node (for kubeadm also the kubelet-config ConfigMap): serverTLSBootstrap: true
sudo sed -i '/^kind: KubeletConfiguration/a serverTLSBootstrap: true' /var/lib/kubelet/config.yaml
sudo systemctl restart kubelet
# 2. Approve the serving CSRs, checking each belongs to a node you own
kubectl get csr | grep kubelet-serving
kubectl certificate approve CSR_NAME
# Lab-only shortcut, as in many course labs: metrics-server args
#   - --kubelet-insecure-tls
#   - --kubelet-preferred-address-types=InternalIP
# HPA: utilisation is measured against requests, so set them
kubectl -n shop set resources deploy/web --requests=cpu=200m,memory=256Mi
```

**Why this fix works:** with CA-signed serving certificates that include the node IPs, metrics-server verifies the kubelets, the APIService turns Available, and the HPA gets numbers to scale on. Serving CSRs are not approved automatically, by design: approve them yourself or run a dedicated approver that checks the node's identity, and remember they renew yearly. Keep `--kubelet-insecure-tls` for throwaway labs.

**Prevent it:** set `serverTLSBootstrap: true` in the kubeadm configuration from the first install, give every namespace a LimitRange with default requests, and alert when any APIService is unavailable (it also blocks namespace deletion, 3.4).

**Next step:** [26 §11 rollouts and autoscaling](26-playbook-containers-k8s.md#11-kubernetes-rollouts-and-autoscaling) · [31 §6 Deployments, ReplicaSets and autoscaling](31-learn-kubernetes.md#6-deployments-replicasets-and-autoscaling) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Logging & Monitoring · [Kubernetes docs](https://kubernetes.io/docs/)

**Community threads:** [metrics-server #133: x509 signed by unknown authority](https://github.com/kubernetes-sigs/metrics-server/issues/133) · [metrics-server #196: doesn't contain any IP SANs](https://github.com/kubernetes-sigs/metrics-server/issues/196) · [metrics-server #131: hostname resolution of kubelets](https://github.com/kubernetes-sigs/metrics-server/issues/131) · [metrics-server #1282: Metrics API not available](https://github.com/kubernetes-sigs/metrics-server/issues/1282) · Search: [Stack Overflow](https://stackoverflow.com/search?q=metrics-server+%22doesn%27t+contain+any+IP+SANs%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=metrics-server+x509+kubelet-insecure-tls&restrict_sr=1)

---

## 11. Helm

Helm keeps every release's history as Secrets in the release namespace. Most Helm incidents are that history getting stuck, or Kubernetes refusing a change Helm tries to make.

### 11.1 Another operation in progress, or no deployed releases

> **Seen as:** `Error: UPGRADE FAILED: another operation (install/upgrade/rollback) is in progress`, or `Error: UPGRADE FAILED: "web" has no deployed releases` · **Where:** a CI job cancelled or timed out mid-upgrade, a first install that failed, two pipelines deploying the same release · **Level:** [L2 · Mid] · **CKA:** Cluster Architecture, Installation and Configuration (Helm) · **How common:** helm #5595 "has no deployed releases" (123 comments, 94 reactions) and #3353 on `upgrade --install` after a failed first install (87 reactions)

**Why it happens:** each Helm revision is a Secret labelled with its status. An upgrade first records the new revision as pending-upgrade; if the client dies (a cancelled pipeline, a runner restart, a timeout), it stays pending, and every later upgrade refuses to start. If the very first install failed, no revision was ever deployed, so there is nothing to upgrade from.

**Diagnose:**

```bash
helm -n shop history web | tail -3
kubectl -n shop get secret -l owner=helm,name=web -L status,version
```

```text
REVISION   UPDATED                    STATUS            CHART       APP VERSION   DESCRIPTION
12         Sat Oct  4 09:12:44 2026   deployed          web-1.8.1   1.4.3         Upgrade complete
13         Sat Oct  4 13:40:02 2026   pending-upgrade   web-1.8.2   1.4.4         Preparing upgrade
NAME                         TYPE                 DATA   AGE   STATUS            VERSION
sh.helm.release.v1.web.v12   helm.sh/release.v1   1      4h    deployed          12
sh.helm.release.v1.web.v13   helm.sh/release.v1   1      12m   pending-upgrade   13
```

**What the output tells you:** revision 13 never finished, and revision 12 is the last good one. Before touching anything, make sure no other helm process or pipeline is still working on this release.

**Fix:**

```bash
# Back to the last good revision; this also clears the pending state
helm -n shop rollback web 12 --wait
# Retry, rolling back automatically if it fails (Helm 4 renames --atomic to --rollback-on-failure)
helm -n shop upgrade web ./chart -f values-prod.yaml --atomic --timeout 10m
# First install failed and nothing was ever deployed: start clean
helm -n shop uninstall web && helm -n shop install web ./chart -f values-prod.yaml --atomic
```

**Why this fix works:** a rollback writes a new revision from a known-good one, so the release leaves the pending state with a consistent history. Deleting only the pending revision's Secret is the last resort described in the issue threads; don't delete the whole history, because you lose every rollback point.

**Prevent it:** don't let deploy jobs be cancelled halfway (`interruptible: false` and a `resource_group` per environment in GitLab CI, see [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md)), and set the Helm timeout longer than your slowest rollout.

**Next step:** [31 §16 Helm and Kustomize](31-learn-kubernetes.md#16-helm-and-kustomize) · KodeKloud: [*Helm for Beginners*](https://kodekloud.com/courses/helm-for-beginners) · [Helm Playground](https://kodekloud.com/playgrounds/playground-helm) · [Helm docs](https://helm.sh/docs/)

**Community threads:** [helm #5595: has no deployed releases](https://github.com/helm/helm/issues/5595) · [helm #3353: upgrade --install after a failed install](https://github.com/helm/helm/issues/3353) · Search: [Stack Overflow](https://stackoverflow.com/search?q=helm+%22another+operation%22+%22is+in+progress%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=helm+another+operation+in+progress&restrict_sr=1)

### 11.2 UPGRADE FAILED: immutable fields, ownership, CRDs

> **Seen as:** `cannot patch "web" with kind Deployment: ... spec.selector: Invalid value: ...: field is immutable`; `spec.clusterIP: Invalid value: "": field is immutable`; `Service "web" in namespace "shop" exists and cannot be imported into the current release: invalid ownership metadata`; new fields of a chart's CRDs silently ignored after an upgrade · **Where:** chart upgrades that change labels, adopting objects created with kubectl, charts that ship CRDs · **Level:** [L2 · Mid] · **CKA:** Cluster Architecture, Installation and Configuration (Helm) · **How common:** helm #7956 "clusterIP field is immutable" (97 reactions), #1193 "no resource with the name found" (124 reactions) and #3275 (105)

**Why it happens:** some fields can't change once an object exists (a Deployment's selector, a Service's clusterIP, a StatefulSet's volumeClaimTemplates), so an upgrade that changes them must recreate the object. Helm refuses to modify objects that it didn't create unless they carry its ownership label and annotations. Helm installs CRDs from a chart's crds/ directory on the first install only and never upgrades or deletes them, so newer chart versions run against old CRDs.

**Diagnose:**

```bash
# helm's own --dry-run renders the chart but never sends it to the API server, so it cannot see
# immutable fields; render with helm, then let the API server validate without changing anything
helm -n shop template web ./chart -f values-prod.yaml | kubectl -n shop apply --dry-run=server -f - 2>&1 | grep -i immutable
kubectl -n shop get deploy web -o jsonpath='{.spec.selector.matchLabels}'; echo
kubectl -n shop get svc web -o jsonpath='{.metadata.labels}{"  "}{.metadata.annotations}'; echo
```

```text
The Deployment "web" is invalid: spec.selector: Invalid value: v1.LabelSelector{MatchLabels:map[string]string{"app.kubernetes.io/instance":"web", "app.kubernetes.io/name":"shop-web"}, MatchExpressions:[]v1.LabelSelectorRequirement(nil)}: field is immutable
{"app":"web"}
{"app":"web"}  {}
```

**What the output tells you:** the new chart version changed the selector labels from `app: web` to the standard app.kubernetes.io labels, which Kubernetes won't patch in place. The Service has no Helm annotations at all: it was created by hand and will block the next step too.

**Fix:**

```bash
# Immutable selector: recreate on purpose. Orphan the old pods so they keep serving meanwhile,
# then delete the orphaned ReplicaSet once the new pods are Ready.
kubectl -n shop delete deploy web --cascade=orphan
helm -n shop upgrade web ./chart -f values-prod.yaml --atomic
# Adopt an object created outside Helm
kubectl -n shop label svc web app.kubernetes.io/managed-by=Helm
kubectl -n shop annotate svc web meta.helm.sh/release-name=web meta.helm.sh/release-namespace=shop
# CRDs: Helm never upgrades them, so apply the new ones first, server-side
kubectl apply --server-side -f chart/crds/
```

**Why this fix works:** the new Deployment is created with the new selector, and the adopted Service is now managed like any other release object. Applying CRDs server-side also avoids the 256 KiB annotation limit large CRDs hit (the kube-prometheus-stack case in [Observability problems §11](49-observability-stack-problems.md#11-prometheus-at-scale)). Don't reach for `helm upgrade --force` by habit: it deletes and recreates resources, which means downtime, and a recreated Service gets a new clusterIP.

**Prevent it:** run `helm diff upgrade` (plugin) and `helm template … | kubectl apply --dry-run=server -f -` in the merge request pipeline (Helm's own `--dry-run` never reaches the API server's validation), never change selector labels in an existing release, and manage CRDs as their own step (or with server-side apply in Argo CD).

**Next step:** [31 §16 Helm and Kustomize](31-learn-kubernetes.md#16-helm-and-kustomize) · KodeKloud: [*Helm for Beginners*](https://kodekloud.com/courses/helm-for-beginners) — Helm Charts Anatomy · [Helm docs](https://helm.sh/docs/)

**Community threads:** [helm #7956: spec.clusterIP field is immutable](https://github.com/helm/helm/issues/7956) · [helm #1193: no resource with the name found](https://github.com/helm/helm/issues/1193) · [helm #3275](https://github.com/helm/helm/issues/3275) · Search: [Stack Overflow](https://stackoverflow.com/search?q=helm+upgrade+%22field+is+immutable%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=helm+upgrade+field+is+immutable&restrict_sr=1)

---

## 12. GitOps on the cluster: Argo CD and Flux

The Argo CD and Flux problems that live in the pipeline (diffs that never clear, hooks, repository access, Flux reconciliation) are in [CI/CD toolbox §12](47-cicd-gitlab-jenkins-actions-argocd.md#12-gitops-argo-cd-and-flux). These two are about the cluster side: how Argo CD is exposed, and what an automated sync can do to a cluster.

### 12.1 Argo CD behind an ingress: redirect loop

> **Seen as:** the browser shows `ERR_TOO_MANY_REDIRECTS` for https://argocd.example.com; `argocd login argocd.example.com` fails with `rpc error: code = Unavailable desc = connection closed before server preface received` · **Where:** Argo CD exposed through Traefik or ingress-nginx with TLS terminated at the ingress · **Level:** [L2 · Mid] · **CKA:** Services and Networking · **How common:** covered by the Argo CD ingress documentation and FAQ, and a recurring homelab question (see the search links)

**Why it happens:** argocd-server serves HTTPS itself and redirects plain HTTP to HTTPS. When the ingress terminates TLS and forwards plain HTTP to it, argocd-server sees an insecure request, redirects to https, the browser comes back through the ingress as plain HTTP again, and the loop never ends. The CLI speaks gRPC over HTTP/2, which a proxy hop that downgrades to HTTP/1.1 breaks.

**Diagnose:**

```bash
curl -sk -o /dev/null -w '%{http_code} %{redirect_url}\n' https://argocd.example.com/
kubectl -n argocd get cm argocd-cmd-params-cm -o jsonpath='{.data.server\.insecure}'; echo
kubectl -n argocd get ingress argocd-server -o jsonpath='{.spec.rules[0].http.paths[0].backend.service.port}'; echo
```

```text
307 https://argocd.example.com/

{"name":"http"}
```

**What the output tells you:** a request that arrived over HTTPS is redirected to the very same HTTPS URL: argocd-server can't see the TLS the ingress already terminated. `server.insecure` is unset, and the ingress sends plain HTTP to the http port.

**Fix:**

```bash
# One TLS terminator: the ingress. Run argocd-server in plain HTTP behind it
kubectl -n argocd patch cm argocd-cmd-params-cm --type=merge -p '{"data":{"server.insecure":"true"}}'
kubectl -n argocd rollout restart deploy/argocd-server
# CLI through the ingress: gRPC-Web works over HTTP/1.1
argocd login argocd.example.com --grpc-web --username admin
# Alternative: TLS passthrough to argocd-server (a Traefik IngressRouteTCP with passthrough)
```

**Why this fix works:** argocd-server no longer redirects, and the ingress handles TLS and certificates like for every other app. "Insecure" refers only to the hop inside the cluster; the browser still uses HTTPS. Don't publish Argo CD to the internet with the built-in admin account: it can change everything in the cluster.

**Prevent it:** log in through SSO (Dex or OIDC with Authentik or Keycloak, see [Wazuh & security tools](48-wazuh-and-security-tools.md)), delete the initial admin secret after first login, and restrict the ingress to admin networks or the VPN.

**Next step:** [CI/CD toolbox §12](47-cicd-gitlab-jenkins-actions-argocd.md#12-gitops-argo-cd-and-flux) · [43 §8 Traefik on Kubernetes](43-traefik-and-reverse-proxies.md#8-traefik-tcp-auth-client-ip-and-kubernetes) · [Argo CD docs](https://argo-cd.readthedocs.io/en/stable/)

**Community threads:** [Argo CD docs](https://argo-cd.readthedocs.io/en/stable/) · [Argo CD FAQ](https://argo-cd.readthedocs.io/en/stable/faq/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=argocd+ingress+%22too+many+redirects%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=argocd+ingress+too+many+redirects&restrict_sr=1) · [argo-cd issues](https://github.com/argoproj/argo-cd/issues?q=is%3Aissue+ingress+redirect+loop)

### 12.2 Automated prune deletes more than intended

> **Seen as:** after a merge, Argo CD (or Flux) deletes Deployments, Services or whole namespaces; the sync result lists dozens of resources as pruned; the fix commit waits while a failed sync keeps retrying · **Where:** app-of-apps and ApplicationSets with templated paths or namespaces, automated sync with prune and selfHeal, namespaces owned by an application · **Level:** [L4 · Lead] · **CKA:** beyond the exam (platform design) · **How common:** Skyscanner's postmortem on k8s.af ("how a couple of characters brought down our site": a templating slip plus namespace deletion caused a global outage); argo-cd #11494 on failed syncs blocking newer commits (49 reactions)

**Why it happens:** GitOps makes the cluster match what Git renders, exactly. If a template variable is empty or a path changes, an application renders a different namespace or fewer objects, and automated prune deletes everything that is no longer rendered: the system does precisely what it was told. When a namespace object belongs to an application, pruning it deletes everything inside, PVCs included. Argo CD's automated sync refuses to prune when an application renders nothing at all (`allowEmpty` is false by default), but a partial or misdirected render passes that check.

**Diagnose:**

```bash
argocd app history shop-web | tail -2
argocd app get shop-web -o json | jq -r '.status.operationState.syncResult.resources[] | select(.message|test("pruned")) | "\(.kind)/\(.name)"' | head -3
kubectl -n argocd get applications -o custom-columns=NAME:.metadata.name,PRUNE:.spec.syncPolicy.automated.prune,SELFHEAL:.spec.syncPolicy.automated.selfHeal
```

```text
41  2026-10-03 16:02:11 +0000 UTC  main (8c1e2f0)
42  2026-10-04 14:10:37 +0000 UTC  main (b7d93a1)
Deployment/web
Service/web
Namespace/shop
NAME            PRUNE   SELFHEAL
platform-apps   true    true
shop-web        true    true
```

**What the output tells you:** commit b7d93a1 made shop-web render without its objects, and automated prune removed them, including the namespace. The parent app also prunes automatically, so it would happily remove whole applications the same way.

**Fix:**

```bash
# 1. Stop the automation first, so selfHeal doesn't fight you
argocd app set platform-apps --sync-policy none
argocd app set shop-web --sync-policy none
# 2. Revert in Git, then sync the known-good revision on purpose
git revert b7d93a1 && git push
argocd app sync shop-web --revision 8c1e2f0
# 3. Data that went with the namespace (PVCs) comes back from backup, not from Git (13.3, Velero)
```

```yaml
# Guard rails: never prune or delete these objects automatically
metadata:
  annotations:
    argocd.argoproj.io/sync-options: Prune=false,Delete=false
# Platform and parent apps: heal drift, but prune only by hand
syncPolicy:
  automated: { prune: false, selfHeal: true }
```

**Why this fix works:** turning automation off stops the bleeding, the revert restores the rendered manifests, and the annotations protect namespaces and stateful objects from the next templating slip. The lesson of the postmortem is about process: a reviewer must see the rendered diff, not only the template change.

**Prevent it:** render and diff in every merge request (`argocd app diff --local` or `kustomize build | kubectl diff -f -`), restrict AppProjects so applications can't create Namespace objects or deploy outside their destinations, use sync windows for production, and practise the restore (13.3). Bring this to the team as a design review: [Career ladder](40-career-ladder.md) counts it as senior-level evidence.

**Next step:** [CI/CD toolbox §12](47-cicd-gitlab-jenkins-actions-argocd.md#12-gitops-argo-cd-and-flux) · [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md) · [Argo CD docs](https://argo-cd.readthedocs.io/en/stable/) · [Flux docs](https://fluxcd.io/flux/)

**Community threads:** [Kubernetes Failure Stories (k8s.af)](https://k8s.af/) · [argo-cd #11494: retrying failed syncs blocks newer commits](https://github.com/argoproj/argo-cd/issues/11494) · Search: [Stack Overflow](https://stackoverflow.com/search?q=argocd+prune+deleted+namespace) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=argocd+prune+deleted+production&restrict_sr=1)

---

## 13. Upgrades, certificates and etcd

The CKA's cluster-maintenance tasks, and the problems that end careers when nobody practised them: upgrades that skip steps, certificates that expire on a Saturday, and an etcd restore done for the first time during an outage.

### 13.1 kubeadm upgrade: skew, package repos and removed APIs

> **Seen as:** `E: Version '1.36.2-1.1' for 'kubeadm' was not found`; `Specified version to upgrade to "v1.37.0" is too high; kubeadm can upgrade only 1 minor version at a time`; after the upgrade, manifests fail with `no matches for kind ... in version ...` or a CNI policy stops matching nodes · **Where:** kubeadm homelabs a few versions behind, the CKA upgrade task · **Level:** [L2 · Mid] · **CKA:** Cluster Architecture, Installation and Configuration · **How common:** a fixed CKA task; Reddit's Pi-Day outage on k8s.af started with a Kubernetes upgrade that removed a node label their Calico configuration selected on

**Why it happens:** kubeadm moves one minor version at a time (1.35 → 1.36 → 1.37), control plane first, and kubelets may lag the API server but never lead it. Packages come from pkgs.k8s.io, which has one repository per minor version (the old apt.kubernetes.io repositories are gone), so apt can't see 1.36 until you change the repository line. Each release removes deprecated APIs and sometimes labels, and anything still using them breaks after the control plane moves: your manifests, Helm charts, and add-ons such as the CNI.

**Diagnose:**

```bash
kubectl get nodes
cat /etc/apt/sources.list.d/kubernetes.list
apt-cache madison kubeadm | head -2
sudo kubeadm upgrade plan | grep -E 'Target version|kubeadm upgrade apply'
# Clients still calling APIs scheduled for removal (any output line is a finding)
kubectl get --raw /metrics | grep apiserver_requested_deprecated_apis
```

```text
NAME   STATUS   ROLES           AGE    VERSION
cp-1   Ready    control-plane   210d   v1.35.3
wk-1   Ready    <none>          210d   v1.35.3
wk-2   Ready    <none>          210d   v1.35.3
deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/v1.35/deb/ /
   kubeadm | 1.35.4-1.1 | https://pkgs.k8s.io/core:/stable:/v1.35/deb  Packages
   kubeadm | 1.35.3-1.1 | https://pkgs.k8s.io/core:/stable:/v1.35/deb  Packages
[upgrade/versions] Target version: v1.35.4
	kubeadm upgrade apply v1.35.4
```

**What the output tells you:** the repository is pinned to v1.35, so the newest thing apt and kubeadm can offer is a 1.35 patch. To reach 1.36 you change the repository first. No deprecated-API lines appeared, so nothing in the cluster calls an API that is about to disappear.

**Fix:**

```bash
# Control plane first, one minor version at a time; take an etcd snapshot before you start (13.3)
sudo sed -i 's#/v1.35/#/v1.36/#' /etc/apt/sources.list.d/kubernetes.list
sudo apt-get update
sudo apt-mark unhold kubeadm && sudo apt-get install -y kubeadm=1.36.2-1.1 && sudo apt-mark hold kubeadm
sudo kubeadm upgrade plan && sudo kubeadm upgrade apply v1.36.2
kubectl drain cp-1 --ignore-daemonsets --delete-emptydir-data
sudo apt-mark unhold kubelet kubectl && sudo apt-get install -y kubelet=1.36.2-1.1 kubectl=1.36.2-1.1 && sudo apt-mark hold kubelet kubectl
sudo systemctl daemon-reload && sudo systemctl restart kubelet && kubectl uncordon cp-1
# Then each worker in turn: repository line, kubeadm package, "sudo kubeadm upgrade node",
# drain from cp-1, kubelet and kubectl packages, restart kubelet, uncordon
# k3s: the system-upgrade-controller, or the install script with INSTALL_K3S_VERSION, one server at a time
```

**Why this fix works:** following the documented order keeps every component inside the supported version skew, and draining moves workloads off each node before its kubelet restarts. Don't skip minor versions, and don't upgrade the kubelets first. Check the CNI, ingress controller and CSI driver compatibility tables before the control plane moves, because they are what usually breaks, not Kubernetes itself.

**Prevent it:** keep an upgrade calendar (each minor release is supported for about 14 months), rehearse on a clone of the cluster, scan manifests and charts for removed APIs in CI, and read the "Urgent Upgrade Notes" of every changelog.

**Next step:** [31 §19 Cluster maintenance](31-learn-kubernetes.md#19-cluster-maintenance) · KodeKloud: *Certified Kubernetes Administrator (CKA)* — Cluster Maintenance (cluster upgrade) · [Kubernetes docs](https://kubernetes.io/docs/) · [k3s: rolling back](https://docs.k3s.io/upgrades/roll-back)

**Community threads:** [Kubernetes Failure Stories (k8s.af)](https://k8s.af/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=kubeadm+upgrade+apply+%22was+not+found%22+pkgs.k8s.io) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=kubeadm+upgrade+failed&restrict_sr=1)

### 13.2 Certificates expired after a year

> **Seen as:** `Unable to connect to the server: x509: certificate has expired or is not yet valid: current time 2026-10-04T08:12:44Z is after 2026-09-30T10:02:11Z`; the API server or etcd failing to start; Rancher or kubelets restarting in a loop · **Where:** kubeadm clusters not upgraded for a year, nodes that were powered off for months, older Rancher installations · **Level:** [L2 · Mid] · **CKA:** Cluster Architecture, Installation and Configuration · **How common:** rancher #26984 "Rancher container restarting every 12 seconds, expired certificates" (81 comments); the k3s docs state that certificates last 365 days and are renewed at startup once they are within 120 days of expiry

**Why it happens:** kubeadm signs the leaf certificates (API server, etcd, front proxy, and the client certificates inside admin.conf, controller-manager.conf and scheduler.conf) for one year; the CAs last ten. `kubeadm upgrade apply` renews them, so a cluster upgraded at least yearly never meets this. Kubelets rotate their own client certificates, unless the node was off when the old one expired. k3s renews at startup, so a k3s server that ran for a year without a restart can still expire.

**Diagnose:**

```bash
sudo kubeadm certs check-expiration | head -6
sudo openssl x509 -noout -enddate -in /var/lib/kubelet/pki/kubelet-client-current.pem
# k3s servers
sudo openssl x509 -noout -enddate -in /var/lib/rancher/k3s/server/tls/serving-kube-apiserver.crt
```

```text
CERTIFICATE                EXPIRES                  RESIDUAL TIME   CERTIFICATE AUTHORITY   EXTERNALLY MANAGED
admin.conf                 Sep 30, 2026 10:02 UTC   <invalid>       ca                      no
apiserver                  Sep 30, 2026 10:02 UTC   <invalid>       ca                      no
apiserver-etcd-client      Sep 30, 2026 10:02 UTC   <invalid>       etcd-ca                 no
apiserver-kubelet-client   Sep 30, 2026 10:02 UTC   <invalid>       ca                      no
controller-manager.conf    Sep 30, 2026 10:02 UTC   <invalid>       ca                      no
notAfter=Jan 18 07:40:11 2027 GMT
```

**What the output tells you:** every kubeadm leaf certificate expired four days ago, while the kubelet's client certificate rotated on its own and is fine. The CAs (further down the same output) still have years left, so a renewal is enough.

**Fix:**

```bash
sudo kubeadm certs renew all
# Restart the control-plane static pods so they load the new certificates
sudo mkdir -p /root/manifests-off && sudo mv /etc/kubernetes/manifests/*.yaml /root/manifests-off/
sleep 20 && sudo mv /root/manifests-off/*.yaml /etc/kubernetes/manifests/
sudo systemctl restart kubelet
# Your kubeconfig embeds the old client certificate: copy the renewed admin.conf again (1.1)
sudo cp /etc/kubernetes/admin.conf ~/.kube/config
# k3s: a restart renews certificates near expiry; or rotate explicitly
sudo systemctl stop k3s && sudo k3s certificate rotate && sudo systemctl start k3s
```

**Why this fix works:** renewal re-signs the leaf certificates with the existing CA, so everything that trusts the CA (kubelets, kubeconfigs with the same CA data) keeps working; moving the manifests out and back forces the static pods to restart with the new files. Don't set the system clock back to "make it work", and don't regenerate the CA unless you must: that invalidates every kubeconfig and kubelet certificate in the cluster.

**Prevent it:** upgrade at least once a year, run `kubeadm certs check-expiration` weekly from cron or alert on `apiserver_client_certificate_expiration_seconds`, and put the expiry date in the team calendar.

**Next step:** [26 §10 nodes, storage and control plane](26-playbook-containers-k8s.md#10-kubernetes-nodes-storage-and-control-plane) · [31 §19 Cluster maintenance](31-learn-kubernetes.md#19-cluster-maintenance) · KodeKloud: [*TLS Basics*](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Security/TLS-Basics) · [k3s certificate docs](https://docs.k3s.io/cli/certificate)

**Community threads:** [rancher #26984: restarting every 12 seconds, expired certificates](https://github.com/rancher/rancher/issues/26984) · [k3s docs: certificate](https://docs.k3s.io/cli/certificate) · Search: [Stack Overflow](https://stackoverflow.com/search?q=kubeadm+certificate+expired+%22certs+renew%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=kubeadm+certificates+expired&restrict_sr=1)

### 13.3 etcd backup and restore: kubeadm and k3s

> **Seen as:** `etcdctl snapshot save` hangs and ends with `context deadline exceeded`; a "successful" restore after which the deleted objects are still missing (or the new ones still present); `member ... has already been bootstrapped`; k3s servers that disagree after one was restored · **Where:** the CKA backup and restore task, undoing a destructive change, a lost control-plane disk · **Level:** [L2 · Mid] · **CKA:** Cluster Architecture, Installation and Configuration · **How common:** discuss.kubernetes.io "ETCD - backup and restore management" (197k views) and "ETCD backup !ssues" (52k); the k3s docs cover etcd-snapshot and cluster-reset

**Why it happens:** etcd only talks TLS: etcdctl needs the endpoint plus a CA, a certificate and a key, and without them it waits until the deadline. A restore never touches the running etcd; `etcdutl snapshot restore` writes a new data directory, and nothing changes until the etcd static pod is pointed at that directory. That forgotten step is the "restore did nothing" case. Restoring into an existing data directory fails with "already bootstrapped". On k3s, snapshots are taken automatically (every 12 hours, five kept) and restored with `--cluster-reset`, after which the other servers must rejoin.

**Diagnose:**

```bash
# kubeadm: snapshot with the endpoint and certificates from the etcd manifest
sudo ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 \
  --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt \
  --key=/etc/kubernetes/pki/etcd/server.key snapshot save /var/backups/etcd-2026-10-04-0600.db
sudo etcdutl snapshot status /var/backups/etcd-2026-10-04-0600.db -w table
sudo grep -B2 'name: etcd-data' /etc/kubernetes/manifests/etcd.yaml
sudo k3s etcd-snapshot ls          # k3s
```

```text
Snapshot saved at /var/backups/etcd-2026-10-04-0600.db
+----------+----------+------------+------------+---------+
|   HASH   | REVISION | TOTAL KEYS | TOTAL SIZE | VERSION |
+----------+----------+------------+------------+---------+
| 7c1f2a9b |   918204 |       1482 |      12 MB |   3.6.0 |
+----------+----------+------------+------------+---------+
    volumeMounts:
    - mountPath: /var/lib/etcd
      name: etcd-data
--
      path: /var/lib/etcd
      type: DirectoryOrCreate
    name: etcd-data
Name                             Location                                                                          Size      Created
etcd-snapshot-k3s-1-1791093600   file:///var/lib/rancher/k3s/server/db/snapshots/etcd-snapshot-k3s-1-1791093600   9814048   2026-10-04T06:00:00Z
```

**What the output tells you:** the snapshot is complete and readable (1482 keys at revision 918204), and the etcd pod reads /var/lib/etcd. A restore must therefore go to a new directory and that hostPath must change, or etcd keeps serving the old data.

**Fix:**

```bash
# kubeadm, one control plane: restore to a NEW directory, then point the etcd pod at it
sudo etcdutl snapshot restore /var/backups/etcd-2026-10-04-0600.db --data-dir /var/lib/etcd-restore
sudo sed -i 's#path: /var/lib/etcd$#path: /var/lib/etcd-restore#' /etc/kubernetes/manifests/etcd.yaml
# The kubelet recreates etcd; restart the controller manager and scheduler the same way (move
# their manifests out and back) so nothing acts on cached state, then check what you expected
kubectl get ns; kubectl get deploy -A | head
# k3s, one server (HA: afterwards remove /var/lib/rancher/k3s/server/db on the other servers and restart them)
sudo systemctl stop k3s
sudo k3s server --cluster-reset --cluster-reset-restore-path=/var/lib/rancher/k3s/server/db/snapshots/etcd-snapshot-k3s-1-1791093600
sudo systemctl start k3s
```

**Why this fix works:** the restored directory is a fresh single-member etcd with the snapshot's data, and changing the hostPath makes the static pod serve it. Restarting the controllers stops them from "correcting" the restored state from their caches. Don't restore over /var/lib/etcd in place, and don't keep snapshots only on the node they protect.

**Prevent it:** schedule snapshots and copy them off the node (S3 or MinIO; k3s has `--etcd-s3` options), and run a restore drill every quarter on a lab clone: a backup you never restored is a hope, not a backup.

**Next step:** [31 §19 Cluster maintenance](31-learn-kubernetes.md#19-cluster-maintenance) · [Databases, storage & backups](51-problems-databases-storage-backup.md) · KodeKloud: [*Backup and Restore Methods*](https://notes.kodekloud.com/docs/CKA-Certification-Course-Certified-Kubernetes-Administrator/Cluster-Maintenance/Backup-and-Restore-Methods) · [k3s etcd-snapshot docs](https://docs.k3s.io/cli/etcd-snapshot) · [etcd docs](https://etcd.io/docs/)

**Community threads:** [discuss.kubernetes.io: ETCD - backup and restore management](https://discuss.kubernetes.io/t/etcd-backup-and-restore-management/11019) · [discuss.kubernetes.io: ETCD backup !ssues](https://discuss.kubernetes.io/t/etcd-backup-ssues/8304) · [k3s docs: etcd-snapshot](https://docs.k3s.io/cli/etcd-snapshot) · Search: [Stack Overflow](https://stackoverflow.com/search?q=etcdctl+snapshot+restore+kubeadm+data-dir) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=etcd+restore+snapshot+kubeadm&restrict_sr=1)

### 13.4 etcd slow, out of space or without quorum

> **Seen as:** `etcdserver: mvcc: database space exceeded` and every write failing; etcd warnings `apply request took too long` and `slow fdatasync`; API timeouts and frequent leader changes; on a k3s HA cluster with two of three servers gone, `etcdserver: no leader` · **Where:** etcd on HDDs, SD cards or busy shared storage; clusters with heavy churn (CI jobs, events); two- and three-node HA labs · **Level:** [L3 · Senior] · **CKA:** beyond the exam · **How common:** etcd is behind the Monzo outages listed on k8s.af; k3s's HA epic #42 has 37 reactions

**Why it happens:** etcd syncs every write to disk, so slow fsync (above about 10 ms at the 99th percentile) means slow API calls, missed heartbeats and leader elections. etcd keeps old revisions until they are compacted, and compaction doesn't return disk space until a defragmentation; when the database reaches its quota (2 GiB by default), etcd raises a NOSPACE alarm and the cluster becomes read-only. Quorum is a majority: three members survive one failure, two members survive none, so two servers are less available than one.

**Diagnose:**

```bash
# ETCD_FLAGS holds --endpoints=https://127.0.0.1:2379 and the three TLS flags from 13.3
sudo etcdctl $ETCD_FLAGS endpoint status
sudo etcdctl $ETCD_FLAGS alarm list
sudo crictl logs --since 10m "$(sudo crictl ps --name etcd -q)" 2>&1 | grep -E 'took too long|slow fdatasync' | tail -2
```

```text
https://127.0.0.1:2379, 8e9e05c52164694d, 3.6.0, 2.1 GB, true, false, 41, 38821044, 38821044, memberID:10276657743932975437 alarm:NOSPACE
memberID:10276657743932975437 alarm:NOSPACE
{"level":"warn","ts":"2026-10-04T15:02:11.204Z","caller":"etcdserver/util.go:170","msg":"apply request took too long","took":"1.284s","expected-duration":"100ms"}
{"level":"warn","ts":"2026-10-04T15:02:13.977Z","caller":"wal/wal.go:805","msg":"slow fdatasync","took":"2.611s","expected-duration":"1s"}
```

**What the output tells you:** the database hit its 2 GiB quota and raised NOSPACE, which is why writes fail, and fsyncs taking 2.6 seconds show the disk under etcd is far too slow. Both need fixing: the alarm today, the disk this week.

**Fix:**

```bash
# NOSPACE: compact old revisions, defragment (one member at a time), then clear the alarm
rev=$(sudo etcdctl $ETCD_FLAGS endpoint status -w json | jq -r '.[0].Status.header.revision')
sudo etcdctl $ETCD_FLAGS compact "$rev"
sudo etcdctl $ETCD_FLAGS defrag
sudo etcdctl $ETCD_FLAGS alarm disarm
# Headroom: raise the quota (kubeadm: etcd.local.extraArgs in the ClusterConfiguration)
#   - --quota-backend-bytes=8589934592
# Slow fsync: move /var/lib/etcd to SSD or NVMe; no etcd setting fixes a slow disk
# Lost quorum on k3s (two of three servers gone for good): on the survivor
sudo systemctl stop k3s && sudo k3s server --cluster-reset && sudo systemctl start k3s
# then delete /var/lib/rancher/k3s/server/db on the other servers and let them rejoin
```

**Why this fix works:** compaction marks old revisions free, defragmentation hands the space back, and disarming lets writes resume. `--cluster-reset` turns the surviving member into a new one-member cluster with all its data, which the others then join. Don't defragment all members at once (each blocks while it runs), don't run two-member etcd clusters, and don't put etcd on NFS or Ceph RBD shared with busy workloads.

**Prevent it:** SSDs for etcd, three or five members in separate failure domains, alerts on database size against the quota, on WAL fsync latency and on leader changes, and a scheduled defragmentation.

**Next step:** [Slow system playbook](23-playbook-slow-system.md) (disk latency) · [Observability problems §11](49-observability-stack-problems.md#11-prometheus-at-scale) · [Senior architecture](39-learn-senior-architecture.md) · [etcd docs](https://etcd.io/docs/) · [k3s docs](https://docs.k3s.io/)

**Community threads:** [Kubernetes Failure Stories (k8s.af)](https://k8s.af/) · [k3s #42: EPIC Support HA](https://github.com/k3s-io/k3s/issues/42) · Search: [Stack Overflow](https://stackoverflow.com/search?q=etcd+%22database+space+exceeded%22+defrag) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=etcd+slow+fdatasync+quorum&restrict_sr=1)

---

## 14. Rancher, RKE2 and EKS

Rancher adds a management plane over many clusters, and its agent's connection home is its most common failure. EKS replaces the parts you build on-prem (load balancers, storage, identity, pod addressing) with AWS services, and two of its classic problems have no on-prem equivalent; they are shown when the selector is set to cloud or both.

### 14.1 Rancher agent can't reach Rancher

> **Seen as:** an imported or downstream cluster stuck Unavailable; cattle-cluster-agent logging `ERROR: https://rancher.example.com/ping is not accessible (Could not resolve host: rancher.example.com)` or `x509: certificate signed by unknown authority` · **Where:** k3s, RKE2 or kubeadm clusters managed by a Rancher server with an internal hostname, a private CA or a proxy · **Level:** [L3 · Senior] · **CKA:** beyond the exam · **How common:** rancher #16454 "Cattle Cluster Agent Could not Resolve Host" (139 comments, 56 reactions); #38816 on high CPU after a Kubernetes upgrade (112 comments)

**Why it happens:** the agent is a pod, so it resolves names through cluster DNS, not through the node's /etc/hosts where an admin may have added the Rancher name. If CoreDNS forwards to resolvers that don't know the internal name, the agent can't find home. With a private CA, the agent compares Rancher's CA with the checksum it was given at registration, so Rancher must be installed with that CA declared. Behind a proxy, the agent needs proxy variables with a NO_PROXY that covers cluster addresses.

**Diagnose:**

```bash
kubectl -n cattle-system logs deploy/cattle-cluster-agent --tail=2
kubectl -n cattle-system get deploy cattle-cluster-agent -o jsonpath='{range .spec.template.spec.containers[0].env[*]}{.name}={.value}{"\n"}{end}' | grep -E 'CATTLE_SERVER|CA_CHECKSUM|PROXY'
kubectl run t --rm -it --restart=Never --image=curlimages/curl -- curl -sv -m5 https://rancher.example.com/ping
```

```text
INFO: Environment: CATTLE_ADDRESS=10.42.1.7 CATTLE_CLUSTER=true CATTLE_SERVER=https://rancher.example.com
ERROR: https://rancher.example.com/ping is not accessible (Could not resolve host: rancher.example.com)
CATTLE_SERVER=https://rancher.example.com
CATTLE_CA_CHECKSUM=4f1c0a9e7b2d...
* Could not resolve host: rancher.example.com
```

**What the output tells you:** any pod in the cluster fails to resolve the Rancher name, so this is cluster DNS, not the agent. With the name resolving and an x509 error instead, the CA declaration would be the next suspect.

**Fix:**

```bash
# Make the Rancher name resolvable for pods (CoreDNS Corefile; on k3s and RKE2 use the
# coredns-custom ConfigMap or the chart values so the change survives restarts)
#   hosts {
#     10.20.0.201 rancher.example.com
#     fallthrough
#   }
kubectl -n kube-system rollout restart deploy/coredns
kubectl -n cattle-system rollout restart deploy/cattle-cluster-agent
# Private CA: install Rancher with privateCA=true and the CA in its tls-ca secret
# Proxy: HTTP_PROXY, HTTPS_PROXY and NO_PROXY (.svc, .cluster.local, pod and service CIDRs) on the agent
```

**Why this fix works:** the agent's pod now resolves and trusts the Rancher URL, opens its tunnel, and the cluster turns Active. hostAliases on the agent Deployment, a workaround often posted in #16454, is only a stopgap: Rancher manages that Deployment and can revert it.

**Prevent it:** one DNS source of truth that every network and cluster can resolve, certificates from a CA every cluster trusts, and a check of Rancher's support matrix before upgrading the managed clusters.

**Next step:** [DNS commands](08-dns.md) · [5.1 CoreDNS](#51-coredns-loop-detected-or-upstream-timeouts) · [Rancher docs](https://ranchermanager.docs.rancher.com/) · [RKE2 docs](https://docs.rke2.io/)

**Community threads:** [rancher #16454: Could not Resolve Host](https://github.com/rancher/rancher/issues/16454) · [rancher #38816: high CPU usage](https://github.com/rancher/rancher/issues/38816) · Search: [Stack Overflow](https://stackoverflow.com/search?q=cattle-cluster-agent+%22could+not+resolve+host%22) · [Reddit r/kubernetes](https://www.reddit.com/r/kubernetes/search/?q=rancher+cattle-cluster-agent+resolve+host&restrict_sr=1)

<div class="env" data-env="cloud" markdown="1">

### 14.2 EKS: Unauthorized, or nodes never join

> **Seen as:** `error: You must be logged in to the server (Unauthorized)`; a node group failing with `NodeCreationFailure: Instances failed to join the kubernetes cluster` · **Where:** new IAM roles or users, custom node roles or launch templates, private subnets without NAT or VPC endpoints · **Level:** [L2 · Mid] · **CKA:** beyond the exam (cloud) · **How common:** a classic for every team new to EKS; it differs from on-prem because identity comes from IAM, not from certificates in a kubeconfig

**Why it happens:** kubectl gets a token for your current AWS identity (`aws eks get-token`), and the cluster maps IAM principals to Kubernetes permissions through access entries (or the older aws-auth ConfigMap). The wrong AWS profile or an unmapped role gives Unauthorized. Nodes need a mapped instance role with the worker, CNI and ECR read policies, and a route to the API and to ECR: a NAT gateway or VPC endpoints from private subnets.

**Diagnose:**

```bash
aws sts get-caller-identity --query Arn --output text
aws eks list-access-entries --cluster-name prod --query 'accessEntries' --output text
aws eks describe-nodegroup --cluster-name prod --nodegroup-name workers --query 'nodegroup.health.issues'
```

```text
arn:aws:sts::111122223333:assumed-role/platform-readonly/ops
arn:aws:iam::111122223333:role/eks-admin	arn:aws:iam::111122223333:role/prod-node-role
[]
```

**What the output tells you:** you are working as platform-readonly, which has no access entry; only eks-admin and the node role do. The node group reports no health issues, so only your access is the problem.

**Fix:**

```bash
# Use the role that has access...
aws eks update-kubeconfig --name prod --region eu-west-1 --role-arn arn:aws:iam::111122223333:role/eks-admin
# ...or let an admin grant this role exactly the access it needs
aws eks create-access-entry --cluster-name prod --principal-arn arn:aws:iam::111122223333:role/platform-readonly
aws eks associate-access-policy --cluster-name prod --principal-arn arn:aws:iam::111122223333:role/platform-readonly \
  --policy-arn arn:aws:eks::aws:cluster-access-policy/AmazonEKSViewPolicy --access-scope type=cluster
# Nodes not joining: the node group's health issues name the failing piece (role policy, subnet route, security group)
```

**Why this fix works:** the token now belongs to a principal with an access entry, which EKS maps to the view policy. Don't hand out the admin policy to make the error go away, and don't depend on the cluster creator's implicit admin rights: keep access entries in Terraform with a documented break-glass role.

**Prevent it:** manage access entries as code next to the cluster, and check node subnets' routes and endpoints in the same Terraform module.

**Next step:** [Cloud & AWS](36-learn-cloud-aws.md) · [AWS cloud commands](16-aws-cloud.md) · [Kubernetes quick reference: EKS specifics](15-kubernetes.md#8-eks-specifics-aws) · [Amazon EKS docs](https://docs.aws.amazon.com/eks/)

**Community threads:** Search: [Stack Overflow](https://stackoverflow.com/search?q=eks+%22You+must+be+logged+in+to+the+server%22+access+entry) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=eks+unauthorized+access+entry&restrict_sr=1) · [aws/containers-roadmap issues](https://github.com/aws/containers-roadmap/issues?q=is%3Aissue+eks+access+entries)

### 14.3 EKS: pods stuck in ContainerCreating, no free IPs

> **Seen as:** `failed to setup network for sandbox ... plugin type="aws-cni" ... failed to assign an IP address to container`; nodes full at 17 or 29 pods while CPU is idle · **Where:** EKS with the Amazon VPC CNI in small subnets, instance types with few network interfaces · **Level:** [L3 · Senior] · **CKA:** beyond the exam (cloud) · **How common:** the classic EKS scaling wall; it has no on-prem twin, because Flannel and Calico give pods addresses from an overlay range while the VPC CNI gives each pod a real VPC address

**Why it happens:** the VPC CNI attaches network interfaces (ENIs) to each node and hands their secondary addresses to pods, so the instance type caps pods per node (17 on a t3.medium) and the subnet's free addresses cap the cluster. By default each node also keeps a whole spare ENI's worth of addresses warm, which drains small subnets quickly.

**Diagnose:**

```bash
kubectl -n shop describe pod web-7c9d5b7f9-q2xkp | sed -n '/Events:/,$p' | tail -1
kubectl get nodes -o custom-columns=NAME:.metadata.name,PODS:.status.allocatable.pods
aws ec2 describe-subnets --subnet-ids subnet-0a1b2c3d subnet-4e5f6a7b --query 'Subnets[].[SubnetId,CidrBlock,AvailableIpAddressCount]' --output text
```

```text
  Warning  FailedCreatePodSandBox  41s  kubelet  Failed to create pod sandbox: rpc error: code = Unknown desc = failed to setup network for sandbox "4b7e1c...": plugin type="aws-cni" name="aws-cni" failed (add): add cmd: failed to assign an IP address to container
NAME                                      PODS
ip-10-0-1-23.eu-west-1.compute.internal   17
ip-10-0-2-41.eu-west-1.compute.internal   17
subnet-0a1b2c3d	10.0.1.0/24	0
subnet-4e5f6a7b	10.0.2.0/24	3
```

**What the output tells you:** both /24 subnets are nearly empty of free addresses, mostly held as warm spares, and each node is capped at 17 pods by its instance type.

**Fix:**

```bash
# Choose one approach. A: prefix delegation (Nitro instances) gives each ENI /28 blocks, then roll the nodes
kubectl -n kube-system set env ds/aws-node ENABLE_PREFIX_DELEGATION=true WARM_PREFIX_TARGET=1
# B: stop reserving a whole spare ENI per node
kubectl -n kube-system set env ds/aws-node WARM_IP_TARGET=5 MINIMUM_IP_TARGET=10
# Address space: larger node subnets, or a secondary VPC CIDR for pods with custom networking
```

**Why this fix works:** prefix delegation multiplies the addresses each interface can carry, and lower warm targets return idle addresses to the subnet. Nodes must be replaced for a new max-pods value to apply. Don't simply add nodes: each one claims more addresses from the same exhausted subnets.

**Prevent it:** size pod address space when designing the VPC, alert on available addresses per subnet, and decide on prefix delegation before the first production cluster.

**Next step:** [Cloud & AWS](36-learn-cloud-aws.md) · [Cloud, IaC & Proxmox problems](50-problems-cloud-iac-proxmox.md) · [Amazon EKS docs](https://docs.aws.amazon.com/eks/)

**Community threads:** [Kubernetes Failure Stories (k8s.af)](https://k8s.af/) · Search: [Stack Overflow](https://stackoverflow.com/search?q=eks+%22failed+to+assign+an+IP+address+to+container%22) · [Reddit r/aws](https://www.reddit.com/r/aws/search/?q=eks+%22failed+to+assign+an+IP+address%22&restrict_sr=1) · [amazon-vpc-cni-k8s issues](https://github.com/aws/amazon-vpc-cni-k8s/issues?q=is%3Aissue+%22failed+to+assign+an+IP+address%22)

</div>

---

## Self-check

Timed break-and-fix tasks in the CKA style: on Lab A (kubeadm) or Lab B (k3s), snapshot, break exactly what the row says, then fix it using only kubectl, the node's shell and the entry. Work against the clock as in the exam, where you have about two hours for a set of performance tasks; finish with killer.sh and the KodeKloud mock exams. After each task, write your five-line note.

| # | Stage | Break it | Fix within | Entry |
|---|---|---|---|---|
| 1 | Fresher | Delete ~/.kube/config on cp-1, then run kubectl and helm | 5 min | 1.1 |
| 2 | Fresher | Run kubeadm init without --pod-network-cidr and apply Flannel; get CoreDNS Running | 15 min | 4.1 |
| 3 | Junior | Put `disabled_plugins = ["cri"]` and `SystemdCgroup = false` back in config.toml and restart containerd; make the control plane stable | 15 min | 2.1 |
| 4 | Junior | Give a ServiceAccount in ci a Role in its own namespace only, then deploy into shop with it | 10 min | 1.3 |
| 5 | Junior | Pull a Harbor image (private CA) on a fresh worker and on a k3s agent | 20 min | 2.4 |
| 6 | Junior | Install metrics-server without the insecure flag; make `kubectl top` and an HPA work | 20 min | 10.1 |
| 7 | Mid-level | Change cp-1's address with netplan and reboot; bring the API server back | 20 min | 3.1 |
| 8 | Mid-level | Block UDP 8472 on wk-2 with UFW; prove the cause from a pod-to-pod test | 15 min | 4.2 |
| 9 | Mid-level | Point the kubelet's resolvConf at /etc/resolv.conf on Ubuntu; fix the CoreDNS crash | 10 min | 5.1 |
| 10 | Mid-level | Delete ingress-nginx's namespace but keep its webhook; make Ingress creation work again | 10 min | 6.1 |
| 11 | Mid-level | Snapshot etcd, delete a namespace, restore it and prove it is back | 30 min | 13.3 |
| 12 | Senior | Install Longhorn on Ubuntu with multipathd running; make a PVC mount | 30 min | 9.2 |
| 13 | Senior | Upgrade Lab A by one minor version with no failed requests to a test app | 60 min | 13.1 |
| 14 | Senior/Lead | In a lab GitOps repository, make an app render without its Deployment; show your guard rails stop the prune | 45 min | 12.2 |

Quick questions to answer from memory:

1. Which chain of components must work for a kubeadm API server to come back after a reboot, and how do you check each link?
2. Why does Flannel crash with "pod cidr not assigned", and which two ways fix it?
3. Why does a CoreDNS pod on Ubuntu loop, and why is deleting the loop plugin the wrong fix?
4. What makes a webhook configuration outlive the add-on that created it, and how does that show up?
5. Why can't Kubernetes move a ReadWriteOnce volume off a powered-off node by itself, and what do you tell it?
6. What does `etcdutl snapshot restore` change on disk, and what must you change afterwards?

---

## Where to go next

- [Kubernetes (CKA)](31-learn-kubernetes.md): the course behind every entry here, from the kubeadm homelab (§3) to cluster maintenance (§19) and the twenty timed drills (§22).
- [Containers & Kubernetes playbook](26-playbook-containers-k8s.md) and [Kubernetes quick reference](15-kubernetes.md): the incident walk and the command sheet to keep open while you fix things.
- [Docker & containers](14-docker-containers.md), [Docker course](30-learn-docker.md) and [Docker, Swarm & registry problems](44-problems-docker-swarm-registry.md): the container layer underneath, Harbor included.
- [Traefik & reverse proxies](43-traefik-and-reverse-proxies.md): Traefik on Kubernetes and the ingress-nginx migration in §8.
- [Dokploy & self-hosted PaaS](45-dokploy-and-self-hosted-paas.md): when Swarm-based Dokploy is enough and when a k3s cluster earns its complexity.
- [CI/CD toolbox](47-cicd-gitlab-jenkins-actions-argocd.md) and [CI/CD, IaC & SRE](33-learn-cicd-iac-sre.md): the pipelines and Argo CD/Flux work that deploy onto these clusters.
- [Wazuh & security tools](48-wazuh-and-security-tools.md) and [Observability problems](49-observability-stack-problems.md): watching the cluster for intrusions and for the slow failures in sections 3, 5 and 13.
- [Who owns this port?](22-playbook-ports-inventory.md): the port map for 6443, 10250, 2379–2380 and the CNI ports.
- [DevOps day to day](52-devops-day-to-day.md): how these problems arrive as tickets and pages, and how to learn from them.
- [Practice arena](54-practice-arena.md#6-kubernetes-and-the-cka): free labs, Killercoda scenarios and CKA mock exams to rehearse this module.
- [On-prem vs cloud paths](55-paths-onprem-vs-cloud.md) and [Career ladder](40-career-ladder.md): where Kubernetes fits in your path, and which of these skills mark each stage.
- Official docs: [Kubernetes](https://kubernetes.io/docs/) · [k3s](https://docs.k3s.io/) · [RKE2](https://docs.rke2.io/) · [Helm](https://helm.sh/docs/) · [cert-manager](https://cert-manager.io/docs/) · [MetalLB](https://metallb.io/) · [Longhorn](https://longhorn.io/docs/) · [Calico](https://docs.tigera.io/calico/latest/) · [Cilium](https://docs.cilium.io/) · [CoreDNS](https://coredns.io/) · [etcd](https://etcd.io/docs/) · [Argo CD](https://argo-cd.readthedocs.io/en/stable/) · [Flux](https://fluxcd.io/flux/) · [Amazon EKS](https://docs.aws.amazon.com/eks/).
