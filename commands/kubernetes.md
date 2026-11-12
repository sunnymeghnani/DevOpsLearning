# Kubernetes & GitOps

Kubernetes questions are answered in a fixed order: confirm which cluster and namespace you are talking to (`kubectl config`), see the state (`get`), read why the controllers did what they did (`describe`, events), then hear the app itself (`logs`, `exec`, `debug`). Changes go through the object that owns the pods (`apply`, `rollout`, `set`, `scale`), node work through `drain` and `taint`, and cluster plumbing through `kubeadm`, `etcdctl` and `k3s`. Where Helm, Argo CD or Flux own an object, change it there: they undo manual fixes.

| If you would reach for | Prefer | Because |
|---|---|---|
| `kubectl get pods` | `kubectl get pods -A -o wide`, then `kubectl describe pod POD` | other namespaces stay hidden otherwise; wide adds node and IP, describe adds the events that say why |
| `kubectl logs POD` on a crash loop | `kubectl logs POD --previous` | the running container has just restarted; the crash was logged by the one before it |
| `kubectl delete pod` as a restart | `kubectl rollout restart deploy/NAME` | pods are replaced gradually within `maxUnavailable`, never all at once |
| `kubectl edit` on a live object | `kubectl diff -f FILE`, then `kubectl apply -f FILE` (or a Git commit) | the change is reviewed, repeatable, and not undone by the next apply or sync |
| `curl` from the node to test the app | `kubectl run t --rm -it --restart=Never --image=nicolaka/netshoot -n shop -- curl -sv http://web/` | a pod uses cluster DNS and is judged by NetworkPolicies, like the app's real clients |
| `kubectl exec` into a distroless image | `kubectl debug -it POD --image=nicolaka/netshoot --target=CONTAINER` | brings its own tools into the pod without rebuilding the image |
| reading Roles and RoleBindings | `kubectl auth can-i VERB RESOURCE -n NS --as SUBJECT` | the API server's own yes or no, groups and ClusterRoles included |
| `openssl x509` on each control-plane file | `kubeadm certs check-expiration` | every kubeadm certificate and kubeconfig with its expiry in one table |

### kubectl config — which cluster, user and namespace will my next command hit?
Match: kubectl config
Instead of: reading the kubeconfig file by hand
Safety: read-only for `current-context`, `get-contexts` and `view` · changes state: `use-context`, `set-context` and `set-credentials` rewrite the kubeconfig file · `view --raw` prints credentials

**In one line:** kubectl is an HTTPS client: the kubeconfig says where (API server URL and CA), as whom (certificate, token or exec plugin) and in which default namespace, and a **context** names one such combination. `kubectl config` shows and switches them without calling the cluster.

**Read the command:** `kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}{"\n"}'`

| Part | Meaning |
|---|---|
| `config view` | the kubeconfig as kubectl merged it from every file in `$KUBECONFIG`, credentials hidden |
| `--minify` | only what the current context uses |
| `-o jsonpath='{.clusters[0].cluster.server}'` | one field, the API server URL; `{"\n"}` adds a newline |
| `--raw` | include certificate and token data (to check a client certificate's expiry with openssl) |
| `current-context`, `get-contexts` | the active context / all contexts, the active one marked `*` |
| `use-context NAME` | switch the default context (**rewrites the file**) |
| `set-context --current --namespace=shop` | change the current context's namespace (**rewrites the file**) |

**What the output tells you:**

```
$ kubectl config view --minify -o jsonpath='{.clusters[0].cluster.server}{"\n"}'
https://10.20.0.10:6443
$ kubectl config get-contexts
CURRENT   NAME                          CLUSTER      AUTHINFO           NAMESPACE
*         kubernetes-admin@kubernetes   kubernetes   kubernetes-admin   shop
          deploy@prod                   prod         deploy
```

Every kubectl command goes to that URL: an old IP, or a name missing from the API server's certificate, fails with timeouts or `x509` errors before RBAC is even asked. `*` marks the context in use; an empty NAMESPACE means `default`.

**Why it is effective:** wrong-cluster accidents and many connection and x509 errors are kubeconfig problems, and these commands answer them locally, even while the API server is unreachable.

**Compared with reading the kubeconfig file:** the file holds the same entries, but not the merge of several `$KUBECONFIG` files, and the active context is easy to misread among the others.

**Trap:** `use-context` and `set-context` edit the shared file, so every terminal using it switches too: scripts should pass `--context NAME` instead. Plain `view` shows key and certificate data as `DATA+OMITTED`, so its output is not a working kubeconfig; `--raw` output is a live credential.

**Next step:** wrong context → `kubectl config use-context NAME`, then `kubectl auth whoami`. Right URL but x509 errors or timeouts → `openssl s_client -connect HOST:6443`, and `kubeadm certs check-expiration` on the control plane.

### kubectl get — what exists, where it runs, and what state it is in
Match: kubectl get
Instead of: docker ps, kubectl get pods in the current namespace only
Safety: read-only · `-o yaml` or jsonpath on a Secret prints its values (base64 is not encryption)

**In one line:** `kubectl get` lists objects of any kind, one status line each; selectors choose the objects and `-o` chooses how much of each you see.

**Read the command:** `kubectl -n shop get pods -l app=web -o wide`

| Part | Meaning |
|---|---|
| `-n shop` | namespace `shop`; without it, the context's default namespace |
| `get pods` | the kind; several at once also work: `deploy,rs,pods,svc` |
| `-l app=web` | only objects with this label: the pods a selector `app=web` picks |
| `-o wide` | more columns: IP and node for pods; IP, OS and runtime for nodes |
| `-A` | every namespace |
| `--field-selector status.phase!=Running` | filter on fields (the phase, `spec.nodeName=w1`) |
| `-w` | keep watching and print each change |
| `-o yaml`, `-o jsonpath='{.status.qosClass}'` | the whole live object / one field |

**What the output tells you:** (trimmed)

```
NAME                  READY   STATUS             RESTARTS      AGE   IP            NODE
web-5f6d4c8b9-a1b2c   1/1     Running            0             3d    10.244.1.21   w1
web-5f6d4c8b9-d3e4f   0/1     Running            0             3d    10.244.2.14   w2
web-5f6d4c8b9-k8m2p   0/1     CrashLoopBackOff   12 (2m ago)   1h    10.244.2.19   w2
web-6c7d8e9f0-x1y2z   0/1     ImagePullBackOff   0             10m   10.244.1.30   w1
```

READY counts ready containers: `0/1` while `Running` means a failing readiness probe, so no Service traffic. STATUS is the phase or why a container waits or ended (`CrashLoopBackOff`, `ImagePullBackOff`, `OOMKilled`, `Completed`). `12 (2m ago)` is a live crash loop; a Pending pod on node `<none>` was never scheduled.

**Why it is effective:** every replica with its node and restarts on one screen, so patterns jump out: failures on one node (a node problem), only the newest ReplicaSet's pods failing (a bad release). `-o jsonpath` then pulls one exact field from the live object.

**Compared with plain `kubectl get pods` and `docker ps`:** plain get shows the same STATUS, enough when you know the namespace, but hides the other namespaces and gives no node or IP to correlate. `docker ps` on a node sees nothing of the pods when containerd runs them.

**Trap:** `Running` is not healthy: read READY. `No resources found in default namespace.` usually means the wrong namespace. `kubectl get all` leaves out ConfigMaps, Secrets, Ingresses, PVCs and most custom resources. A replacement pod's RESTARTS starts again at 0.

**Next step:** `CrashLoopBackOff` → `kubectl logs POD --previous`. `Pending`, `ImagePullBackOff`, stuck `ContainerCreating` → `kubectl describe pod POD`. `0/1 Running` → describe (Readiness), then the Service's EndpointSlices. Failures on one node → `kubectl describe node NODE`.

### kubectl describe — why is this object in this state?
Match: kubectl describe
Instead of: kubectl get, kubectl get -o yaml
Safety: read-only

**In one line:** `kubectl describe` summarises one object (spec, status, conditions) and then lists the **events** that mention it: where the scheduler, the controllers and the kubelet explain what they did and what failed.

**Read the command:** `kubectl -n NS describe pod POD | sed -n '/^Events:/,$p'`

| Part | Meaning |
|---|---|
| `-n NS` | the pod's namespace |
| `describe pod POD` | one pod; `-l app=api` describes every matching pod |
| `| sed -n '/^Events:/,$p'` | print from `Events:` to the end |
| `describe node w1` | Conditions (pressure, Ready), Taints, Allocated resources |
| `describe deploy api` | Conditions such as `ProgressDeadlineExceeded` |
| `describe rs RS` | `FailedCreate` when a quota or admission blocks new pods |
| `describe svc web`, `describe pvc data` | Selector and Endpoints / the volume provisioner's events |

**What the output tells you:**

```
    Last State:     Terminated
      Reason:       OOMKilled
      Exit Code:    137
    Restart Count:  6
Events:
  Type     Reason   Age               From     Message
  ----     ------   ----              ----     -------
  Warning  BackOff  2m (x25 over 8m)  kubelet  Back-off restarting failed container api in pod api-6d9f7b8c5-mx2lq_shop(…)
```

The previous container went over its memory limit and was killed (137 = SIGKILL). `x25 over 8m` is one event repeated 25 times; From names the component. A Pending pod gets the scheduler's verdict per node: `0/3 nodes are available: 1 node(s) had untolerated taint {node-role.kubernetes.io/control-plane: }, 2 Insufficient memory …`.

**Why it is effective:** `get` says *that* a pod is Pending or crashing; describe says *why*, in the components' own words (FailedScheduling, FailedMount, Unhealthy, OOMKilled), without searching three components' logs.

**Compared with `kubectl get -o yaml`:** every field, `lastState` included, and what scripts should parse, but no events.

**Trap:** events expire (one hour by default), so `Events: <none>` on an old problem proves nothing. Events sit on the object that acted: a Deployment short of pods has its `FailedCreate` on the ReplicaSet, not on pods that were never created. The layout changes between versions: scripts should parse `-o json`.

**Next step:** FailedScheduling → `kubectl describe node`, taints, requests. FailedMount → `kubectl describe pvc`, the StorageClass, or the ConfigMap or Secret it names. Unhealthy → the probe settings, `kubectl logs`. OOMKilled → the limit and `kubectl top pod POD --containers`.

### kubectl events — what happened in the cluster, in time order?
Match: kubectl events, kubectl get events
Instead of: unsorted kubectl get events, kubectl describe on each object
Safety: read-only

**In one line:** events are short records from controllers, the scheduler and kubelets (`Scheduled`, `FailedMount`, `BackOff`, `Killing`); sorted by time, they tell an incident's story across every object.

**Read the command:** `kubectl get events -A --field-selector type=Warning --sort-by=.lastTimestamp | tail -20`

| Part | Meaning |
|---|---|
| `get events -A` | the Event objects of every namespace |
| `--field-selector type=Warning` | only warnings; also `reason=Unhealthy`, `involvedObject.name=POD` |
| `--sort-by=.lastTimestamp` | oldest first, so the newest end up at the bottom |
| `| tail -20` | the 20 most recent |
| `kubectl -n shop events --for deploy/web` | the newer `events` command: one object's events, in time order |
| `--types=Warning` | the `kubectl events` way to keep only warnings |

**What the output tells you:**

```
NAMESPACE   LAST SEEN   TYPE      REASON        OBJECT                    MESSAGE
shop        6m          Warning   FailedMount   pod/api-6d9f7b8c5-q7r2t   MountVolume.SetUp failed for volume "config" : configmap "api-config" not found
shop        4m          Warning   Unhealthy     pod/api-6d9f7b8c5-mx2lq   Readiness probe failed: HTTP probe failed with statuscode: 503
shop        1m          Warning   BackOff       pod/web-5f6d4c8b9-k8m2p   Back-off restarting failed container web in pod web-5f6d4c8b9-k8m2p_shop(…)
```

REASON is a stable keyword to grep or alert on, OBJECT is where to look next, and MESSAGE names the missing ConfigMap, the probe's status code or the failing container.

**Why it is effective:** describe gives one object's events; this gives all of them in order, so cause and effect line up: a node goes NotReady, its pods are evicted, FailedScheduling follows elsewhere.

**Compared with `kubectl describe` and unsorted `get events`:** describe shows the same events for one object next to its spec, better once you know the object; unsorted output is in no useful order.

**Trap:** events live one hour by default (the API server's `--event-ttl`): at the start of an incident save them (`kubectl get events -A --sort-by=.lastTimestamp > events.txt`). Node events are stored in the `default` namespace. Repeats merge into one event with a count. Events that carry only `eventTime` sort out of place with `--sort-by=.lastTimestamp`; `kubectl events` orders by whichever time an event has.

**Next step:** FailedScheduling → `kubectl describe node`, requests and taints. FailedMount → the ConfigMap, Secret or PVC it names. Unhealthy or BackOff → `kubectl logs POD --previous`. Node events (NotReady, DiskPressure) → `kubectl describe node NODE`, then the kubelet's journal.

### kubectl logs — what did the container print, including the one that just crashed?
Match: kubectl logs
Instead of: docker logs, reading /var/log/pods on the node
Safety: read-only · logs can contain tokens and personal data

**In one line:** `kubectl logs` returns a container's stdout and stderr as the kubelet stored them, for the running instance or, with `--previous`, for the instance that died before it.

**Read the command:** `kubectl -n NS logs POD -c CONTAINER --previous --tail=50`

| Part | Meaning |
|---|---|
| `-n NS` `POD` | the pod; `deploy/api` or `job/migrate` pick one of their pods |
| `-c CONTAINER` | the container: sidecars and init containers log separately |
| `--previous` (`-p`) | the last **terminated** instance: the crash, not the restart |
| `--tail=50` | the last 50 lines |
| `-f` | follow until Ctrl-C |
| `-l app=web --prefix` | every pod with that label, each line prefixed with its pod and container |
| `--all-containers` | every container of the pod, init containers included |
| `--since=10m`, `--timestamps` | the last 10 minutes / a time on each line |

**What the output tells you:**

```
$ kubectl -n shop logs api-6d9f7b8c5-mx2lq --previous --tail=2
2026-10-04T09:12:02Z INFO  starting api 1.4.3
2026-10-04T09:12:02Z FATAL cannot connect to db.shop.svc:5432: connection refused
$ kubectl -n shop logs web-5f6d4c8b9-a1b2c --previous
Error from server (BadRequest): previous terminated container "web" in pod "web-5f6d4c8b9-a1b2c" not found
```

The dying instance's last lines name the cause, here a database it cannot reach. The BadRequest error means that container has not restarted yet, so there is no previous instance.

**Why it is effective:** after a crash the kubelet restarts the container at once, so plain `logs` shows a clean start; `--previous` shows the dying instance's last words. `-l` with `--prefix` reads every replica, so you see whether all fail or only one.

**Compared with `docker logs` or the files on the node:** `docker logs` does not exist on containerd nodes; `/var/log/pods/` and `crictl logs` hold the same lines but need SSH to the right node.

**Trap:** logs go with the pod: after deletion or eviction they are gone, so logs that matter must be shipped. `deploy/NAME` reads one pod only (`Found 3 pods, using pod/…`). With `-l` you get 10 lines per pod unless you set `--tail`. Empty output often means the app logs to a file instead of stdout.

**Next step:** the error names a host or Service → `kubectl exec POD -- nslookup NAME`, the EndpointSlices. Restarts without an error → `kubectl describe pod` (Last State: OOMKilled, liveness kills). No logs at all → `kubectl describe pod` (image, ConfigMap, Secret).

### kubectl exec — run a command inside a running container
Match: kubectl exec
Instead of: SSH to the node, then docker exec or crictl exec
Safety: depends on what you run · the process runs in a live pod with the container's user and rights; changes are lost on restart

**In one line:** `kubectl exec` starts an extra process in a container of a running pod, so you test DNS, network, files and environment exactly as the app sees them, from anywhere kubectl works.

**Read the command:** `kubectl -n shop exec deploy/api -- cat /etc/resolv.conf`

| Part | Meaning |
|---|---|
| `-n shop` | the namespace |
| `exec deploy/api` | run in one pod of Deployment `api` (or name a pod) |
| `--` | the end of kubectl's options: the rest is the command |
| `cat /etc/resolv.conf` | the command, which must exist **inside the image** |
| `-it … -- sh` | interactive: stdin and a terminal, for a shell |
| `-c CONTAINER` | the container in a multi-container pod (default: the first, or the one marked default) |
| `-- env` | the environment the container got, Secret values included |

**What the output tells you:**

```
search shop.svc.cluster.local svc.cluster.local cluster.local
nameserver 10.96.0.10
options ndots:5
```

`nameserver` is the cluster DNS Service's ClusterIP, not the node's resolver. With `ndots:5`, a name with fewer than five dots tries each search domain first: `api` finds `api.shop.svc.cluster.local`, while `api.partner.example.com` costs several failed lookups before the real one.

**Why it is effective:** the test runs in the pod's own network namespace, DNS settings, mounts and service-account token, which all differ from the node's, and the API server carries the session, so you need neither SSH nor the node's name.

**Compared with SSH plus `docker exec` or `crictl exec`:** the same idea one level down, and the fallback when the API server itself is broken, but you must first find the node and the container ID.

**Trap:** slim and distroless images have no shell, `curl` or `nslookup`: `executable file not found in $PATH` means the tool is missing, not the app broken (use `kubectl debug`). `deploy/api` picks one pod; the others may differ. exec needs the `pods/exec` permission, a powerful right worth auditing.

**Next step:** tool missing → `kubectl debug -it POD --image=nicolaka/netshoot --target=CONTAINER`. DNS fails → CoreDNS pods and `kubectl -n kube-system logs -l k8s-app=kube-dns`. Need a neutral client → `kubectl run … --rm -it`.

### kubectl debug — tools in a pod or on a node, without changing the image
Match: kubectl debug
Instead of: kubectl exec, rebuilding the image with tools, SSH to the node
Safety: changes state: adds an ephemeral container to a live pod (listed until the pod is deleted), creates a copy of a pod, or a pod with the node's host namespaces and filesystem

**In one line:** `kubectl debug` brings a toolbox image to the problem: as an ephemeral container inside a running pod, as a modified copy of a crashing pod, or as a pod on a node with the node's filesystem mounted.

**Read the command:** `kubectl -n NS debug -it POD --image=nicolaka/netshoot --target=api`

| Part | Meaning |
|---|---|
| `-n NS` `debug POD` | add an ephemeral container to this running pod, without a restart |
| `-it` | attach interactively with a terminal |
| `--image=nicolaka/netshoot` | the toolbox: curl, dig, ss, tcpdump |
| `--target=api` | also share container `api`'s process namespace, so `ps` sees its processes |
| `… -- ss -ltn` | run one command instead of a shell |
| `--copy-to=api-debug --container=api -- sh` | a **copy** of the pod in which container `api` runs `sh` instead of its command |
| `node/w1 … -- chroot /host journalctl -u kubelet -n 5 --no-pager` | a pod on node w1 in the host's namespaces, the node's filesystem at `/host` |

**What the output tells you:** `If you don't see a command prompt, try pressing enter.`, then a shell. A pod's containers share one network namespace, so `ss -ltn` in the debug container lists the app's listening ports and `curl 127.0.0.1:8080` reaches the app directly. In a `--copy-to` copy you start the app's command by hand and read its error.

**Why it is effective:** a distroless image offers nothing to exec into; debug adds tools for this session only, without a rebuild or a restart that would wipe the evidence. The node variant answers kubelet questions without SSH.

**Compared with `kubectl exec`:** enough when the image already has the tools; it cannot add any.

**Trap:** an ephemeral container cannot be removed; it stays listed until the pod is replaced. By default the copy has no labels (no Service traffic) and no probes; delete it when done. The node pod uses host namespaces, so a namespace enforcing the `baseline` or `restricted` Pod Security level rejects it, and it stays behind as `node-debugger-w1-…` until deleted. `--target` needs container runtime support.

**Next step:** listener missing in `ss` → the app's bind address or port. Works in the copy, not in the real pod → compare env, mounts and probes (`kubectl get pod POD -o yaml`). Node problems → the kubelet journal, then `kubectl describe node`.

### kubectl run — a throwaway test pod inside the cluster network
Match: kubectl run
Instead of: curl or nslookup from the node
Safety: changes state: creates a pod (deleted on exit with `--rm`); `--overrides` can pin it to a node or put it on the host network

**In one line:** `kubectl run` creates a single pod from an image; with `--rm -it --restart=Never` it is a disposable client that tests DNS, Services and NetworkPolicies from where the app's real clients sit.

**Read the command:** `kubectl -n shop run np-test --rm -it --restart=Never --image=busybox:1.36 -- wget -qO- -T 3 http://api:8000/healthz`

| Part | Meaning |
|---|---|
| `-n shop` | that namespace's NetworkPolicies and DNS search path apply |
| `run np-test` | a pod named `np-test`, labelled `run=np-test` |
| `--rm -it` | attach a terminal; delete the pod when the command exits |
| `--restart=Never` | a one-shot pod: it completes instead of restarting |
| `--image=busybox:1.36` | `wget` and `nslookup`; `nicolaka/netshoot` adds curl, dig, iperf3, tcpdump |
| `-- wget -qO- -T 3 http://api:8000/healthz` | the container's arguments: fetch quietly to stdout, 3 s timeout (`--command --` makes them the command) |
| `--labels=role=frontend` | the labels a NetworkPolicy should match |
| `--overrides='{"spec":{"nodeName":"w1"}}'` | JSON merged into the pod: place it on w1, bypassing the scheduler |

**What the output tells you:**

```
ok
pod "np-test" deleted
```

The Service answered. Failures read differently: `wget: bad address …` = the name did not resolve (DNS); `download timed out` = nothing answered (a NetworkPolicy, routing); `Connection refused` = usually no ready endpoints, or nothing listening on the targetPort.

**Why it is effective:** the node is not a pod: it uses the host's resolver, and NetworkPolicies judge it differently. A pod with the right namespace and labels reproduces what the app's clients see, and `--rm` leaves nothing behind.

**Compared with curl or nslookup from the node:** proves the node reaches a pod IP or a NodePort, useful for kube-proxy questions, but says nothing about cluster DNS or policies between pods.

**Trap:** without `--rm`, test pods pile up. The image must be pullable: air-gapped clusters and Docker Hub rate limits turn the test itself into ImagePullBackOff. A pod in `default` is judged by `default`'s policies, not the app's. Add `--command` when the words after `--` must replace the image's entrypoint.

**Next step:** bad address → `kubectl -n kube-system get pods -l k8s-app=kube-dns`, CoreDNS logs. Timed out → `kubectl -n shop get networkpolicy`. Refused → `kubectl get endpointslices -l kubernetes.io/service-name=api`, the targetPort.

### kubectl port-forward — reach one pod from your machine, skipping Service and Ingress
Match: kubectl port-forward
Instead of: testing only through a NodePort or the Ingress
Safety: read-only for the cluster · opens a listening port on your machine (127.0.0.1 by default) until stopped

**In one line:** `kubectl port-forward` tunnels a local port through the API server and the kubelet into one pod, so you test the app itself with no Service, Ingress, load balancer or NetworkPolicy on the path.

**Read the command:** `kubectl -n NS port-forward pod/POD 8081:3000 &`

| Part | Meaning |
|---|---|
| `-n NS` | the namespace |
| `port-forward pod/POD` | tunnel into this pod |
| `8081:3000` | local port 8081 → port 3000 inside the pod |
| `&` | run in the background, so the next line can `curl 127.0.0.1:8081`; stop it with `kill %1` |
| `svc/myapp 8080:80` | pick one pod behind Service `myapp`, on the targetPort behind service port 80 |

**What the output tells you:**

```
Forwarding from 127.0.0.1:8081 -> 3000
Forwarding from [::1]:8081 -> 3000
Handling connection for 8081
```

The tunnel is up; each `Handling connection` line is one client connection through it. If the pod answers here but not through the Service, the fault is in the Service layer (selector, targetPort, endpoints) or the Ingress.

**Why it is effective:** it splits "the app is broken" from "the path to the app is broken" in one step, through the API server you already reach, and changes nothing in the cluster.

**Compared with testing through a NodePort or the Ingress:** that tests the whole path users take, but a failure there could sit in any layer.

**Trap:** the tunnel connects from inside the pod's network namespace, so it also reaches an app listening only on 127.0.0.1, which other pods cannot: a working port-forward does not prove the Service will work. `svc/NAME` picks one pod at the start and stays on it; if that pod dies, the forward breaks.

**Next step:** works via the pod, fails via the Service → `kubectl describe svc` (Selector, targetPort) and the EndpointSlices. Fails via the pod too → `kubectl logs`, and what the app listens on (`kubectl debug … -- ss -ltn`).

### kubectl top — how much CPU and memory pods and nodes use right now
Match: kubectl top
Instead of: top on each node, kubectl describe node (requests)
Safety: read-only · needs metrics-server

**In one line:** `kubectl top` reads the Metrics API, which metrics-server fills from every kubelet, and shows the current CPU and memory **usage** of nodes, pods or single containers.

**Read the command:** `kubectl top pod POD -n NAMESPACE --containers`

| Part | Meaning |
|---|---|
| `top pod POD` | one pod; `top pods` for the namespace, `top nodes` for nodes |
| `-n NAMESPACE` | the namespace |
| `--containers` | one line per container: which one uses the memory? |
| `-A --sort-by=memory` | every namespace, heaviest first (`--sort-by=cpu` likewise) |
| `-l app=api` | only pods with this label |

**What the output tells you:**

```
$ kubectl top nodes
NAME   CPU(cores)   CPU(%)   MEMORY(bytes)   MEMORY(%)
cp1    212m         10%      1630Mi          43%
w1     1890m        94%      3124Mi          82%
$ kubectl top pod api-6d9f7b8c5-mx2lq -n shop --containers
POD                   NAME    CPU(cores)   MEMORY(bytes)
api-6d9f7b8c5-mx2lq   api     480m         498Mi
api-6d9f7b8c5-mx2lq   proxy   5m           21Mi
```

`212m` is 0.212 of a core; node percentages are of allocatable resources. Memory is the working set, the figure kubelet eviction uses; compare it with the container's limit.

**Why it is effective:** it shows real usage, not reservations: a node can be full for the scheduler (requests) yet half idle, or close to out of memory while its requests look modest. `--containers` puts the cost on the right container.

**Compared with `kubectl describe node` and `top`:** describe's "Allocated resources" sums requests and limits, the scheduler's view, which says nothing about load. `top` on a node sees processes, not pods or limits.

**Trap:** `error: Metrics API not available` means metrics-server is missing or unhealthy, not zero usage. Values are a recent sample with no history (that is Prometheus' job). CPU below the limit can still be throttled: `nr_throttled` in the container's `/sys/fs/cgroup/cpu.stat` shows it.

**Next step:** memory near the limit → raise it or fix the leak, then watch restarts. Node near 100% → `kubectl describe node`, spread the load or add capacity. Metrics missing → `kubectl get apiservice v1beta1.metrics.k8s.io`, the metrics-server logs.

### kubectl auth can-i — is this user or service account allowed to do this?
Match: kubectl auth
Instead of: reading Roles and RoleBindings by hand
Safety: read-only · `--as` uses impersonation, which needs that permission itself

**In one line:** `kubectl auth can-i` asks the API server's authorizer whether a subject may perform a verb on a resource in a namespace; `kubectl auth whoami` shows which user and groups the server sees for your credentials.

**Read the command:** `kubectl auth can-i list secrets --as=system:serviceaccount:app:mysa -n app`

| Part | Meaning |
|---|---|
| `auth can-i` | "may I?": answered `yes` or `no`, exit code 0 or 1 |
| `list secrets` | verb and resource (plural); `deployments.apps` adds the API group |
| `--as=system:serviceaccount:app:mysa` | ask for ServiceAccount `mysa` of namespace `app`, not for yourself |
| `-n app` | in this namespace (RoleBindings work per namespace) |
| `--list` | everything the subject may do there |
| `--subresource=log` | `pods/log` and `pods/exec` are permissions separate from `pods` |
| `--as-group dev-team` | add a group, for users whose rights come through one |
| `auth whoami` | the username and groups your credentials map to |

**What the output tells you:**

```
$ kubectl auth can-i list secrets --as=system:serviceaccount:app:mysa -n app
no
$ kubectl auth whoami
ATTRIBUTE   VALUE
Username    kubernetes-admin
Groups      [kubeadm:cluster-admins system:authenticated]
```

`no` matches the `Forbidden` the app gets. `whoami` shows the identity RBAC really evaluates; a CI job may run as another ServiceAccount than you assume.

**Why it is effective:** RBAC combines Roles, ClusterRoles bound per namespace, aggregation and groups; can-i returns the API server's own decision for one exact request, without trying a dangerous action to find out.

**Compared with reading Roles and RoleBindings:** `kubectl get rolebindings -A -o wide` shows who is bound to what, which you need to fix a rule, but tracing one request through every binding and group by hand is slow and error-prone.

**Trap:** can-i answers authorization only: admission (Pod Security, quotas, webhooks) can still refuse. `--as` with a user ignores that user's groups unless you add `--as-group`. Without `-n`, the answer is for your current namespace. A Forbidden message names subject, verb, resource, group and namespace: feed them to can-i literally.

**Next step:** `no` → `kubectl get rolebindings,clusterrolebindings -A -o wide | grep SUBJECT`, then fix or create the binding. `yes` but still refused → admission: the error text, Pod Security labels, quotas.

### kubectl explain / api-resources — what is this field called, and which resource types exist?
Match: kubectl explain, kubectl api-resources
Instead of: searching the web for YAML examples
Safety: read-only

**In one line:** `kubectl explain` prints the documentation of any field of any resource as **this** cluster's API serves it; `kubectl api-resources` lists every resource type with its short name, API group and scope.

**Read the command:** `kubectl explain pod.spec.containers.livenessProbe --recursive | head -30`

| Part | Meaning |
|---|---|
| `explain` | documentation from the API server's OpenAPI schema |
| `pod.spec.containers.livenessProbe` | the field path: resource, then fields, separated by dots |
| `--recursive` | the whole tree of sub-fields with their types, no descriptions |
| `| head -30` | the first 30 lines |
| `api-resources` | NAME, SHORTNAMES, APIVERSION, NAMESPACED and KIND of every type |
| `api-resources -o wide` | adds VERBS: what RBAC rules can grant on each type |

**What the output tells you:** explain gives the field's type (`Probe`), its description and its sub-fields (`httpGet`, `exec`, `initialDelaySeconds`, `periodSeconds`, `failureThreshold` …). api-resources, trimmed:

```
NAME          SHORTNAMES   APIVERSION             NAMESPACED   KIND
nodes         no           v1                     false        Node
pods          po           v1                     true         Pod
deployments   deploy       apps/v1                true         Deployment
ingresses     ing          networking.k8s.io/v1   true         Ingress
```

SHORTNAMES are what you can type. APIVERSION is the YAML `apiVersion:`, and its group (`apps`) is what a Role's `apiGroups` must say. NAMESPACED `false` means cluster-wide: `-n` has no effect.

**Why it is effective:** the answer comes from the cluster you run, so it matches its version, includes custom resources that publish a schema, and needs no internet (it works in the CKA exam too).

**Compared with searching for YAML examples:** examples show whole working manifests, but often for another version or API group; explain is exact but terse.

**Trap:** both ask the API server, so they fail when it is down. When an aggregated API such as metrics is down, `api-resources` prints `unable to retrieve the complete list of server APIs: metrics.k8s.io/v1beta1: …`, and the rest of the list is still valid.

**Next step:** field found → write it into the manifest, then `kubectl diff -f FILE`. Forbidden for deployments or ingresses → the group from APIVERSION in the Role. Aggregated API errors → `kubectl get apiservice`.

### kubectl apply / diff — make the cluster match these files, after seeing what will change
Match: kubectl apply, kubectl diff
Instead of: kubectl edit, kubectl create on objects that may already exist
Safety: diff is read-only (a server-side dry run) · changes state: apply creates or updates every object in the files at once

**In one line:** `kubectl apply` creates or updates each object to match its manifest, so the same command is safe to repeat; `kubectl diff` shows what apply would change, as computed by the server.

**Read the command:** `kubectl apply --server-side -f chart/crds/`

| Part | Meaning |
|---|---|
| `apply` | create the object if missing, otherwise update the fields the file sets |
| `--server-side` | the API server merges and records which manager owns each field; no `last-applied-configuration` annotation, so very large CRDs fit |
| `-f chart/crds/` | every manifest in the directory; a file, a URL or `-` (stdin) also work |
| `--force-conflicts` | take over fields that another manager (Helm, a controller) owns, instead of failing |
| `-k app/overlays/prod` | build this Kustomize overlay, then apply it |
| `diff -f shop/service.yaml` | the change apply would make, as a unified diff; exit code 1 means differences |
| `-v=6` | log each HTTP request kubectl sends, with its status code |

**What the output tells you:**

```
$ kubectl diff -f shop/service.yaml
   selector:
-    app: web-frontend
+    app: web
$ kubectl apply -f shop/service.yaml
service/web configured
```

`-` is the live object, `+` what it will become: here a live edit of the selector gets reverted. apply prints one line per object: `created`, `configured`, `unchanged`, or `serverside-applied`.

**Why it is effective:** the files become the source of truth: one command creates and updates, re-running it is safe, and the diff shows what will change before anything does, including defaults and webhook mutations, because the server computes it.

**Compared with `kubectl edit`:** handy in a lab, but it leaves no file and no review, and the next apply or GitOps sync reverts it.

**Trap:** client-side apply deletes a field only if a previous apply set it (it compares with the `last-applied-configuration` annotation), so fields added by `kubectl edit` survive unnoticed. Immutable fields such as a Deployment's selector cannot be applied (`field is immutable`): recreate the object. Objects owned by Helm, Argo CD or Flux are reset at their next sync. `apply -f URL` installs whatever the URL serves today: pin versions.

**Next step:** unexpected diff → someone edited live: `kubectl get … -o yaml --show-managed-fields` names the manager and time. `field is immutable` → recreate (`kubectl delete deploy NAME --cascade=orphan` keeps the pods serving). Rejected by admission → read the webhook's or Pod Security's message.

### kubectl create — new objects from the command line, or a correct YAML skeleton
Match: kubectl create
Instead of: writing manifests from memory, copying YAML from the web
Safety: changes state: creates objects, and fails if they exist · `--dry-run=client -o yaml` creates nothing

**In one line:** `kubectl create` builds a new object from flags (deployment, service, secret, configmap, role, token …); with `--dry-run=client -o yaml` it prints the manifest instead, a quick start for files you keep in Git.

**Read the command:** `kubectl create deployment web --image=nginx:1.27 --replicas=3 --port=80 --dry-run=client -o yaml`

| Part | Meaning |
|---|---|
| `create deployment web` | a Deployment `web`, label and selector `app: web` |
| `--image=nginx:1.27` | the image; the container is named after it (`nginx`) |
| `--replicas=3` | the desired pod count |
| `--port=80` | the containerPort, which `kubectl expose` reads later |
| `--dry-run=client` | build the object locally, send nothing |
| `-o yaml` | print it; `> web.yaml` saves it as a starting manifest |
| `create secret generic db --from-literal=password=…` | a Secret from a literal (`--from-file` for files) |
| `create token deployer --duration=1h` | a short-lived token for ServiceAccount `deployer`, printed once |

**What the output tells you:** a complete Deployment whose labels, selector and template match, plus empty `resources: {}`, `strategy: {}` and `status: {}` entries to fill in or delete. Without `--dry-run` the reply is `deployment.apps/web created`, or `Error from server (AlreadyExists)`.

**Why it is effective:** generated labels, selector and template agree, which hand-written YAML often gets wrong, and it is the fastest way to create objects in a lab or the CKA exam.

**Compared with writing YAML by hand or copying it:** a full manifest carries what create lacks (probes, resources, volumes); the skeleton gets the structure right first.

**Trap:** create is not idempotent: a second run fails with AlreadyExists, so scripts use `create … --dry-run=client -o yaml | kubectl apply -f -`. `--from-literal` leaves the secret in shell history, and Secrets are only base64-encoded. A client dry run cannot see quotas, admission or name clashes (`--dry-run=server` can).

**Next step:** save the YAML, edit it, `kubectl apply -f`. Deployment but no pods → `kubectl describe rs` (quota, admission). Need a Service → `kubectl expose`. CI access → `kubectl create token` plus a RoleBinding, checked with `kubectl auth can-i --as`.

### kubectl expose — put a Service in front of a workload, with the right selector
Match: kubectl expose
Instead of: kubectl create service, hand-written Service YAML
Safety: changes state: creates a Service; `--type=NodePort` opens a port on every node

**In one line:** `kubectl expose` creates a Service for an existing Deployment, pod or ReplicaSet and copies that workload's selector, so the Service matches exactly the pods the workload runs.

**Read the command:** `kubectl -n shop expose deploy echo --port=80 --target-port=8080 --type=NodePort`

| Part | Meaning |
|---|---|
| `-n shop` | the namespace; a Service selects pods in its own namespace only |
| `expose deploy echo` | a Service named `echo` (`--name` to change) with the Deployment's selector |
| `--port=80` | the port clients use on the Service |
| `--target-port=8080` | the container port traffic goes to; omitted, it equals `--port` |
| `--type=NodePort` | also open a port from 30000–32767 on every node; the default `ClusterIP` is in-cluster only |

**What the output tells you:** `service/echo exposed`. Then:

```
$ kubectl -n shop get svc echo
NAME   TYPE       CLUSTER-IP     EXTERNAL-IP   PORT(S)        AGE
echo   NodePort   10.96.141.27   <none>        80:31234/TCP   5s
```

`80:31234/TCP` is service port 80 and node port 31234. Whether pods stand behind it is a separate question: `kubectl -n shop get endpointslices -l kubernetes.io/service-name=echo`.

**Why it is effective:** the most common Service bug is a selector that matches no pods; expose cannot make it, because it copies the selector instead of having you type it.

**Compared with `kubectl create service`:** that derives the selector from the Service's name (`app=NAME`), right only if your pods happen to carry that label.

**Trap:** a wrong `--target-port` still gives endpoints, but connections are refused and an Ingress answers 502. `expose pod a` copies the pod's labels (`run=a`), so any other pod with the same labels joins the Service. A NodePort is open on every node, from outside too unless a firewall stops it.

**Next step:** no endpoints → compare `kubectl get pods --show-labels` with the selector, and readiness. Endpoints but refused → what the app listens on (`kubectl debug … -- ss -ltn`) against `--target-port`.

### kubectl rollout — follow, undo or restart a workload's update
Match: kubectl rollout
Instead of: kubectl get pods -w, kubectl delete pod as a restart
Safety: status and history are read-only · changes state: undo and restart replace pods (gradually)

**In one line:** `kubectl rollout` handles the rolling update of a Deployment, DaemonSet or StatefulSet: wait for it to finish, list its revisions, go back to an earlier one, or restart every pod with the same spec.

**Read the command:** `kubectl -n shop rollout status deploy/web --timeout=60s`

| Part | Meaning |
|---|---|
| `-n shop` | the namespace |
| `rollout status deploy/web` | wait until the update has finished; non-zero exit if it fails |
| `--timeout=60s` | stop waiting after 60 s (by default it waits forever) |
| `history deploy/web` | revisions and CHANGE-CAUSE; `--revision=2` shows that revision's pod template |
| `undo deploy/web` | back to the previous revision; `--to-revision=3` to a chosen one |
| `restart deploy/web` | replace every pod gradually with the same spec (`ds/`, `sts/` too) |

**What the output tells you:**

```
$ kubectl -n shop rollout status deploy/web --timeout=60s
Waiting for deployment "web" rollout to finish: 2 out of 4 new replicas have been updated...
error: timed out waiting for the condition
$ kubectl -n shop rollout history deploy/web
deployment.apps/web
REVISION  CHANGE-CAUSE
2         upgrade to nginx 1.28
3         bad tag test
```

The new pods never became Ready, so the update stalled while the old pods kept serving; revision 3 is the bad one. CHANGE-CAUSE comes from the `kubernetes.io/change-cause` annotation, `<none>` if unset. Success reads `deployment "web" successfully rolled out`.

**Why it is effective:** status reads the Deployment's own progress instead of you judging a pod list, and its exit code makes it a deploy gate in CI. undo switches back to the previous ReplicaSet's pod template, which rolls out like any update.

**Compared with `kubectl get pods -w` and deleting pods:** the watch shows which pods fail but not whether the rollout succeeded; deleting pods ignores the strategy, while restart respects `maxUnavailable`.

**Trap:** `--timeout` only stops the waiting: the rollout carries on. undo restores the pod template only, not ConfigMaps, Secrets, replica counts or database migrations. If Helm, Argo CD or Flux manage the workload, their next sync reapplies the bad version: roll back there, or in Git.

**Next step:** stalled → `kubectl get pods -l app=web`, then describe one of the newest pods. Bad version live → `kubectl rollout undo`, then fix the image or config. `ProgressDeadlineExceeded` in `kubectl describe deploy` → the same checks, and alert on it.

### kubectl set — change one setting of a workload's pod template
Match: kubectl set
Instead of: kubectl edit
Safety: changes state: edits the pod template, which starts a rolling update that replaces every pod

**In one line:** `kubectl set` changes one thing in a Deployment, DaemonSet or StatefulSet (a container's image, its requests and limits, or environment variables) and lets the normal rollout replace the pods.

**Read the command:** `kubectl -n shop set image deploy/web nginx=nginx:1.28`

| Part | Meaning |
|---|---|
| `-n shop` | the namespace |
| `set image deploy/web` | change an image in this Deployment's pod template |
| `nginx=nginx:1.28` | **container name** = new image: the left side is the container's name, not the image's |
| `set resources deploy/web --requests=cpu=200m,memory=256Mi` | requests (and `--limits=…`); `-c NAME` for one container |
| `set env ds/aws-node WARM_IP_TARGET=5` | add or change environment variables; `KEY-` removes one |

**What the output tells you:** `deployment.apps/web image updated`, and a rollout starts: follow it with `kubectl rollout status deploy/web`. A wrong container name fails at once (`unable to find container named …`); a wrong tag is accepted and appears later as ImagePullBackOff on the new pods.

**Why it is effective:** one exact change, typed or scripted, with no editor and no chance of touching other fields; rollout status and undo work as for any release.

**Compared with `kubectl edit`:** edit can change anything, handy for exploring, but it is interactive, unreviewed and easy to slip on.

**Trap:** the handbook's drill `nginx=nginx:1.27-alpne` shows the danger: the typo surfaces only at the image pull, after the rollout started (old pods keep serving if `maxUnavailable` allows). Changing env or resources restarts every pod too. Helm, GitOps or the next `kubectl apply` bring the old value back: change the source as well.

**Next step:** rollout stuck → the new pods' events, then `kubectl rollout undo`. Unsure about resources → `kubectl top pod POD --containers`. Record why → `kubectl annotate deploy/web kubernetes.io/change-cause="…" --overwrite`.

### kubectl scale / autoscale — change the replica count, or hand it to an HPA
Match: kubectl scale, kubectl autoscale
Instead of: kubectl delete deployment to stop an app
Safety: changes state: scale changes the number of running pods at once (0 stops the app); autoscale creates an HPA that keeps changing it

**In one line:** `kubectl scale` sets the replica count of a Deployment or StatefulSet now; `kubectl autoscale` creates a HorizontalPodAutoscaler that adjusts it to the load.

**Read the command:** `kubectl -n NS scale deploy/NAME --replicas=0`

| Part | Meaning |
|---|---|
| `-n NS` | the namespace |
| `scale deploy/NAME` | the workload; `sts/db` for a StatefulSet |
| `--replicas=0` | stop every pod but keep the Deployment, its config and history: a reversible off switch |
| `--replicas=3` | the count to bring it back to |
| `autoscale deploy php-apache --min=1 --max=5 --cpu-percent=50` | an HPA: 1 to 5 pods, aiming at 50 % of the pods' CPU **requests** |

**What the output tells you:** `deployment.apps/NAME scaled`; `kubectl get deploy NAME` then shows READY moving to the new count. `kubectl get hpa` shows TARGETS such as `cpu: 71%/50%`; `<unknown>` means the HPA gets no metrics.

**Why it is effective:** scaling to 0 frees a port, database connections or CPU without deleting anything, and scaling back restores the same spec. The handbook's labs scale CoreDNS to 0 to break cluster DNS on purpose, safely.

**Compared with `kubectl delete deployment`:** delete loses the object, its revisions and the configuration needed to bring it back.

**Trap:** an HPA owns the replica count and overrides a manual scale at its next check (every 15 s by default); so does the next Helm or GitOps sync. Zero replicas means a Service without endpoints (503 at the Ingress). Pods without CPU requests cannot scale on CPU (`<unknown>`). A StatefulSet scales down from the highest ordinal and, by default, keeps the PVCs.

**Next step:** pods not appearing → `kubectl describe rs` (quota) or `kubectl describe pod` (Pending). HPA `<unknown>` → metrics-server, CPU requests. Replica count keeps changing → `kubectl get hpa`, then the Helm values or Git.

### kubectl patch / edit — change fields of a live object in place
Match: kubectl patch, kubectl edit
Instead of: deleting and recreating the object
Safety: changes state: the live object changes at once; a pod-template change starts a rollout; removing finalizers skips their cleanup

**In one line:** `kubectl patch` sends a small JSON or YAML change for one object, scriptable and repeatable; `kubectl edit` opens the whole live object in your editor and applies it when you save.

**Read the command:** `kubectl -n monitoring patch prometheus kps --type=merge -p '{"metadata":{"finalizers":null}}'`

| Part | Meaning |
|---|---|
| `-n monitoring` | the namespace |
| `patch prometheus kps` | the object: a custom resource of kind Prometheus named `kps` |
| `--type=merge` | JSON merge patch: maps merge, lists are replaced whole, `null` deletes a key; required for custom resources |
| `-p '{"metadata":{"finalizers":null}}'` | drop every finalizer, so a deletion waiting for a removed operator can finish |
| no `--type` | strategic merge, built-in kinds only: lists such as `containers` merge by name |
| `--type=json -p='[{"op":"remove","path":"/spec/template/spec/containers/0/resources"}]'` | JSON patch: exact operations on paths (`add`, `remove`, `replace`; `/-` appends) |
| `edit cm coredns` | open the live ConfigMap in `$EDITOR`; saving applies it |

**What the output tells you:** `prometheus.monitoring.coreos.com/kps patched`, or `patched (no change)`. A rejected edit is reported with the reason, and kubectl keeps your version in a temporary file so the work is not lost.

**Why it is effective:** a patch states exactly what changes and nothing else, fits into a runbook, and works the same every time; for custom resources and stuck finalizers it is often the only practical tool.

**Compared with deleting and recreating:** recreating loses the object's status and UID, and for a Service its ClusterIP and NodePort.

**Trap:** a merge patch replaces lists whole: merge-patching `containers` drops every container you left out. Clearing finalizers skips their controller's cleanup, so external resources can be orphaned: only once that controller is gone for good. The next `kubectl apply`, Helm upgrade or GitOps sync undoes patches and edits, and editing a ConfigMap does not restart pods that read it as environment variables.

**Next step:** pod-template patch → `kubectl rollout status`. ConfigMap changed → `kubectl rollout restart` for pods using it as env. Make it permanent → the manifest, chart values or Git.

### kubectl label / annotate — the tags selectors match, and the notes tools read
Match: kubectl label, kubectl annotate
Instead of: kubectl edit to change metadata
Safety: changes state: labels change what Services, ReplicaSets, NetworkPolicies and Pod Security select · `--dry-run=server` changes nothing

**In one line:** labels are the key=value tags that selectors match (Services, ReplicaSets, nodeSelectors, NetworkPolicies, a namespace's Pod Security level); annotations are notes and settings that tools read (change-cause, cert-manager, Velero, Helm ownership).

**Read the command:** `kubectl label --dry-run=server --overwrite ns shop pod-security.kubernetes.io/enforce=restricted`

| Part | Meaning |
|---|---|
| `label` | set labels on an object |
| `--dry-run=server` | the API server validates and runs admission, prints warnings, saves nothing |
| `--overwrite` | allow replacing an existing value; without it the change is refused |
| `ns shop` | the object: namespace `shop` |
| `pod-security.kubernetes.io/enforce=restricted` | enforce the `restricted` Pod Security level in this namespace |
| `node w1 disk-` | a trailing `-` removes label `disk` |
| `annotate deploy/web kubernetes.io/change-cause="upgrade to nginx 1.28"` | the text `rollout history` shows |

**What the output tells you:**

```
Warning: existing pods in namespace "shop" violate the new PodSecurity enforce level "restricted:latest"
Warning: legacy-report-7c9d5b8f4-q2w7e: allowPrivilegeEscalation != false, unrestricted capabilities, runAsNonRoot != true, seccompProfile
namespace/shop labeled (server dry run)
```

The dry run names each running pod that would be rejected when next created, and why, before you switch enforcement on. Real runs print `node/w1 labeled` or `unlabeled`.

**Why it is effective:** labels are how Kubernetes connects things: one label decides which pods a Service sends traffic to, where a pod may run and which policies apply, and the server dry run tests a risky one without the risk.

**Compared with `kubectl edit`:** it can change the same metadata, but one command with `--overwrite` is exact and scriptable.

**Trap:** removing a pod's `app` label takes it out of its Service **and** its ReplicaSet, which starts a replacement (the handbook uses this to quarantine a pod for forensics). A label typo silently matches nothing. A tool that ignores your annotation gives no error.

**Next step:** Service lost its pods → compare `kubectl get pods --show-labels` with `kubectl describe svc`. Pod no longer schedules after a node label change → its nodeSelector or affinity. Pod Security warnings → fix the pods' securityContext, then label for real.

### kubectl delete — remove objects, and know what each deletion leaves behind
Match: kubectl delete
Instead of: —
Safety: changes state: immediate, no undo; a namespace takes everything in it; `--force` can leave a container running on an unreachable node

**In one line:** `kubectl delete` removes objects by name, label, field selector or file; a pod gets SIGTERM, its grace period, then SIGKILL, and its controller, if any, creates a replacement.

**Read the command:** `kubectl -n shop delete pod web-7c9d5b7f9-4kq8d --grace-period=0 --force`

| Part | Meaning |
|---|---|
| `-n shop` | the namespace |
| `delete pod web-7c9d5b7f9-4kq8d` | one pod; normally it gets its grace period (30 s unless the pod sets another) |
| `--grace-period=0 --force` | remove the API object at once, without waiting for the kubelet to confirm the container stopped |
| `pods -A --field-selector=status.phase=Failed` | every failed (e.g. evicted) pod in the cluster |
| `namespace drills --wait=true` | the namespace and everything in it; wait until it is gone |
| `deploy web --cascade=orphan` | delete the Deployment but keep its ReplicaSet and pods running |
| `--ignore-not-found` | no error if it is already gone |

**What the output tells you:**

```
Warning: Immediate deletion does not wait for confirmation that the running resource has been terminated. The resource may continue to run on the cluster indefinitely.
pod "web-7c9d5b7f9-4kq8d" force deleted
```

The warning is literal: if the node is only unreachable, not dead, the container may keep running there while its replacement starts elsewhere. A normal delete prints `pod "…" deleted` once the pod has stopped.

**Why it is effective:** deleting a controller-owned pod restarts that one replica; force deletion clears a pod stuck Terminating on a node confirmed off; `--cascade=orphan` replaces a Deployment without dropping its pods.

**Compared with `kubectl rollout restart`:** restart replaces every pod gradually within `maxUnavailable`; delete removes exactly what you name, immediately.

**Trap:** a bare pod (no controller) is gone for good. Force-deleting a StatefulSet pod whose node still runs can leave two copies writing one volume. A namespace stuck Terminating waits on finalizers or an unavailable APIService, not on you deleting harder. Deleting a PVC whose volume's reclaim policy is `Delete` deletes the data.

**Next step:** pod stuck Terminating → `kubectl get pod POD -o jsonpath='{.metadata.finalizers}'` and `kubectl get node`. Namespace stuck → `kubectl get ns NAME -o jsonpath='{.status.conditions}'`, `kubectl get apiservice`.

### kubectl taint — keep pods off a node unless they tolerate it
Match: kubectl taint
Instead of: kubectl cordon
Safety: changes state: NoSchedule blocks new pods; NoExecute also evicts running pods without a matching toleration

**In one line:** a taint marks a node so that only pods with a matching **toleration** may be scheduled there (NoSchedule) or stay there (NoExecute); the same command with a trailing `-` removes it.

**Read the command:** `kubectl taint nodes w2 dedicated=db:NoSchedule`

| Part | Meaning |
|---|---|
| `taint nodes w2` | the node to mark |
| `dedicated=db` | key=value of the taint (the value is optional) |
| `:NoSchedule` | no new pods without a toleration; running pods stay |
| `:PreferNoSchedule` | a soft version: avoid the node when possible |
| `:NoExecute` | also evict running pods that do not tolerate it |
| `dedicated=db:NoSchedule-` | the same taint with `-`: remove it |
| `node.kubernetes.io/out-of-service=nodeshutdown:NoExecute` | you confirm the node is really down: its pods are deleted and their volumes detached, so StatefulSets can move |

**What the output tells you:** `node/w2 tainted` or `untainted`. `kubectl describe node w2` lists `Taints: dedicated=db:NoSchedule`, and a pod without the toleration gets a FailedScheduling event such as `1 node(s) had untolerated taint {dedicated: db}`.

**Why it is effective:** it keeps general workloads off special nodes (databases, GPUs, the control plane) while letting chosen pods in; the out-of-service taint is the supported way to release a dead node's volumes.

**Compared with `kubectl cordon`:** cordon blocks every new pod, without exceptions, for maintenance; a taint is selective and lasting.

**Trap:** a taint repels, it does not attract: a pod with the toleration can still land anywhere, so pair it with a nodeSelector or affinity. NoExecute evicts at once unless a toleration sets `tolerationSeconds`. Apply out-of-service only to a node really powered off, or two pods can write to one volume; remove it when the node returns.

**Next step:** Pending with `untolerated taint` → add the toleration or remove the taint. StatefulSet stuck after a node died → fence the node, then the out-of-service taint (the handbook's Multi-Attach case).

### kubectl drain / cordon / uncordon — empty a node for maintenance, then bring it back
Match: kubectl drain, kubectl cordon, kubectl uncordon
Instead of: rebooting the node and letting Kubernetes notice, kubectl delete pod
Safety: changes state: cordon blocks new pods; drain evicts every pod except DaemonSet pods (emptyDir data is lost)

**In one line:** `cordon` marks a node unschedulable; `drain` cordons it, then evicts its pods through the Eviction API, which honours PodDisruptionBudgets; `uncordon` lets pods be scheduled there again.

**Read the command:** `kubectl drain w1 --ignore-daemonsets --delete-emptydir-data --dry-run=client`

| Part | Meaning |
|---|---|
| `drain w1` | cordon node w1, then evict its pods; their controllers recreate them elsewhere |
| `--ignore-daemonsets` | leave DaemonSet pods alone (they belong on every node); without it drain refuses |
| `--delete-emptydir-data` | allow evicting pods with emptyDir volumes, whose data is deleted |
| `--dry-run=client` | only list what would be evicted |
| `--timeout=60s` | give up after 60 s instead of retrying forever |
| `cordon w1` / `uncordon w1` | only mark / unmark the node unschedulable |

**What the output tells you:** (the handbook's lab, without `--dry-run`)

```
node/w1 cordoned
Warning: ignoring DaemonSet-managed Pods: calico-system/calico-node-x8r2d, kube-system/kube-proxy-tw9lc
evicting pod shop/web-5f6d4c8b9-a1b2c
error when evicting pods/"web-5f6d4c8b9-a1b2c" -n "shop" (will retry after 5s): Cannot evict pod as it would violate the pod's disruption budget.
```

The PDB allows no disruption now, so drain retries until more replicas are Ready elsewhere. A finished drain ends with `node/w1 drained`; `kubectl get nodes` shows `Ready,SchedulingDisabled` until uncordon.

**Why it is effective:** eviction respects PodDisruptionBudgets, so maintenance never takes an app below the minimum its owners declared, and pods move before the node goes down rather than after.

**Compared with rebooting and letting Kubernetes notice:** pods on a node that stops answering are evicted only after it is marked unreachable and their default 5-minute toleration runs out, and StatefulSet pods may wait for a human. `kubectl delete pod` ignores PDBs.

**Trap:** a PDB with `ALLOWED DISRUPTIONS 0` blocks the drain until you add capacity; deleting the PDB defeats its purpose. Bare pods stop the drain unless you add `--force`, which deletes them for good. uncordon does not move pods back: the node fills only as new pods are scheduled.

**Next step:** drain blocked → `kubectl get pdb -A`, then scale the app up. Evicted pods Pending → capacity on the other nodes. Maintenance done → `kubectl uncordon w1`, `kubectl get nodes`.

### kubectl — wait, version, cluster-info and the rarer subcommands
Match: kubectl
Instead of: sleep loops in scripts
Safety: read-only for `wait`, `version`, `cluster-info` and `kustomize` · changes state: `certificate approve` issues a credential; `replace` rewrites whole objects

**In one line:** the kubectl subcommands without a card of their own: `wait` blocks until a condition holds, `version` and `cluster-info` say what you are talking to, `certificate approve` signs a CSR, `kustomize` renders an overlay, `replace` rewrites whole objects.

**Read the command:** `kubectl -n metallb-system wait --for=condition=Available deploy --all --timeout=120s`

| Part | Meaning |
|---|---|
| `-n metallb-system` | the namespace |
| `wait --for=condition=Available` | block until each object reports this status condition as True |
| `deploy --all` | every Deployment in the namespace |
| `--timeout=120s` | give up after 120 s with a non-zero exit code |
| `--for=condition=complete job/JOB`, `--for=delete pod/POD` | wait for a Job to finish / for an object to be gone |
| `version`, `cluster-info` | client and server versions / the API server's and CoreDNS's URLs |
| `certificate approve CSR`, `kustomize DIR` | approve a CertificateSigningRequest / print an overlay without applying it |
| `replace -f -` | replace whole objects with the input (the handbook re-encrypts every Secret this way) |

**What the output tells you:**

```
deployment.apps/controller condition met
$ kubectl -n shop wait --for=condition=complete job/migrate --timeout=120s
error: timed out waiting for the condition on jobs/migrate
```

`condition met` per object; a timeout names the object that never got there. `kubectl version` prints `Client Version` and `Server Version`: kubectl is supported within one minor version of the API server.

**Why it is effective:** wait uses the controllers' own status, so scripts and labs continue the moment an object is ready and fail clearly when it is not.

**Compared with `sleep` loops:** a fixed sleep is too short or wasted time, and never says which object failed.

**Trap:** a failed Job never becomes `complete`, so waiting for it runs into the timeout: check `kubectl describe job`. `replace` swaps the whole object: anything missing from your input is removed. `certificate approve` signs whatever identity and groups the CSR asks for: read it first (`kubectl get csr NAME -o yaml`).

**Next step:** wait timed out → `kubectl describe` the object it names. Version skew → the kubectl matching the server's minor. Kustomize output wrong → fix the overlay, then `kubectl diff -k DIR`.

### kubeadm certs — when do the control-plane certificates expire, and renew them
Match: kubeadm certs
Instead of: openssl x509 -enddate on every file
Safety: needs root (reads /etc/kubernetes/pki) · check-expiration is read-only · changes state: renew re-signs certificates and kubeconfigs, which the control-plane pods load only after a restart

**In one line:** `kubeadm certs check-expiration` lists every certificate and kubeconfig that kubeadm manages, with expiry and signing CA; `kubeadm certs renew` re-signs them with the existing CA.

**Read the command:** `sudo kubeadm certs check-expiration | head -6`

| Part | Meaning |
|---|---|
| `sudo` | the keys under /etc/kubernetes are root-only |
| `certs check-expiration` | leaf certificates (API server, etcd, front proxy), the client certificates inside admin.conf, controller-manager.conf and scheduler.conf, then the CAs |
| `| head -6` | the header and the first five rows |
| `certs renew all` | re-sign every leaf with the current CA (**changes state**) |
| `certs renew apiserver` | just that one |

**What the output tells you:** (from the handbook)

```
CERTIFICATE                EXPIRES                  RESIDUAL TIME   CERTIFICATE AUTHORITY   EXTERNALLY MANAGED
admin.conf                 Sep 30, 2026 10:02 UTC   <invalid>       ca                      no
apiserver                  Sep 30, 2026 10:02 UTC   <invalid>       ca                      no
apiserver-etcd-client      Sep 30, 2026 10:02 UTC   <invalid>       etcd-ca                 no
apiserver-kubelet-client   Sep 30, 2026 10:02 UTC   <invalid>       ca                      no
```

`<invalid>` RESIDUAL TIME means already expired: the cause of `x509: certificate has expired` from kubectl and of an API server that will not start. Leaves last one year, the CAs (further down) ten. EXTERNALLY MANAGED `yes`: an outside CA signed it, and kubeadm cannot renew it.

**Why it is effective:** one table covers every control-plane certificate and the credentials embedded in kubeconfigs, a dozen openssl commands' worth, with the CA each depends on.

**Compared with `openssl x509 -noout -enddate -in FILE`:** exact for one file, and the way to check certificates kubeadm does not list, but blind to certificates embedded in kubeconfigs.

**Trap:** renew writes new files, but the API server, controller manager, scheduler and etcd keep the old certificates in memory until their static pods restart (move their manifests out of /etc/kubernetes/manifests and back). Your kubeconfig is a copy of the old admin.conf: copy it again. The kubelet rotates its own client certificate, so it is not listed. Renew on every control-plane node; `kubeadm upgrade apply` renews everything, so a cluster upgraded yearly never expires.

**Next step:** expired → `sudo kubeadm certs renew all`, restart the static pods, refresh your kubeconfig. Kubelet errors → `openssl x509 -noout -enddate -in /var/lib/kubelet/pki/kubelet-client-current.pem`. Prevention → check-expiration from cron, or an expiry alert.

### kubeadm upgrade — move the control plane to the next Kubernetes version
Match: kubeadm upgrade
Instead of: upgrading the packages and restarting by hand
Safety: needs root · plan is read-only · changes state: apply upgrades the control plane (static pods restart, certificates are renewed); node upgrades the local node's configuration

**In one line:** `kubeadm upgrade plan` checks the cluster and shows the version it can move to and what will change; `upgrade apply` upgrades the first control-plane node and `upgrade node` every other node, one minor version at a time.

**Read the command:** `sudo kubeadm upgrade apply v1.34.1`

| Part | Meaning |
|---|---|
| `sudo` | it rewrites files under /etc/kubernetes |
| `upgrade apply` | on the first control-plane node only: new static-pod manifests, CoreDNS and kube-proxy, renewed certificates |
| `v1.34.1` | the target version; it may not be newer than the kubeadm binary itself |
| `upgrade plan` | preflight checks, current and target versions per component, and the exact apply command |
| `upgrade node` | on the other control-plane nodes and the workers: update that node's kubelet configuration (and its control-plane pods) |

**What the output tells you:** `plan` prints COMPONENT, NODE, CURRENT and TARGET tables, lists the kubelets separately because it does not upgrade them, and ends with the command to run, e.g. `kubeadm upgrade apply v1.34.1`. `apply` ends with `[upgrade/successful] SUCCESS! Your cluster was upgraded to "v1.34.1". Enjoy!`

**Why it is effective:** it checks version skew and control-plane health before touching anything, then upgrades the components in a safe order, which is hard to get right by hand.

**Compared with upgrading packages by hand:** apt only replaces binaries; the control plane runs as static pods whose manifests only kubeadm rewrites.

**Trap:** upgrade the kubeadm package first; on pkgs.k8s.io each minor version has its own repository line, so `Version '1.36.2-1.1' for 'kubeadm' was not found` means apt still points at the old minor. Skipping a minor fails with `kubeadm can upgrade only 1 minor version at a time`. kubelet and kubectl are upgraded separately on every node, between a drain and an uncordon. Take an etcd snapshot first.

**Next step:** a preflight check fails → fix it first. apply done → drain the node, upgrade kubelet and kubectl, `systemctl restart kubelet`, uncordon; then `kubeadm upgrade node` on each other node in turn.

### kubeadm token / join — let a new node into the cluster
Match: kubeadm token, kubeadm join
Instead of: copying the join line from the original kubeadm init output
Safety: needs root · changes state: token create makes a credential that lets any machine join until it expires; join turns this machine into a cluster node

**In one line:** a bootstrap token is a short-lived credential (24 hours by default) a new machine uses to join; `kubeadm token create --print-join-command` makes a fresh one and prints the complete `kubeadm join` line for that machine.

**Read the command:** `sudo kubeadm token create --ttl 2m --print-join-command`

| Part | Meaning |
|---|---|
| `sudo` | as root, on a control-plane node |
| `token create` | a new bootstrap token |
| `--ttl 2m` | it expires after 2 minutes (default 24h; `0` never expires: avoid) |
| `--print-join-command` | print the whole join command: API endpoint, token and CA hash |
| `token list` | existing tokens with TTL, EXPIRES and USAGES |
| `join ENDPOINT:6443 --token TOKEN --discovery-token-ca-cert-hash sha256:HASH` | on the new machine: fetch the cluster information with the token and check it against this CA hash |

**What the output tells you:** (sample values)

```
kubeadm join 10.20.0.10:6443 --token abcdef.0123456789abcdef --discovery-token-ca-cert-hash sha256:5f3c…
```

Run it as root on the new machine; it ends with `This node has joined the cluster`. In `token list`, an expired token has disappeared.

**Why it is effective:** the init output's token expires after a day; this prints a working line in one step, and the CA hash makes the new node verify it talks to the real API server, not an impostor.

**Compared with the line from `kubeadm init`:** the same form, valid only for its first 24 hours.

**Trap:** the join line is a credential: anyone holding it can add a machine to your cluster until it expires, so keep TTLs short and keep it out of tickets. An expired token fails with `could not find a JWS signature in the cluster-info ConfigMap for token ID`. A machine joined before fails preflight (`/etc/kubernetes/kubelet.conf already exists`, port 10250 in use): `kubeadm reset` it first. A control-plane join also needs `--control-plane` and a certificate key.

**Next step:** join hangs → can the machine reach port 6443 (`nc -zv ENDPOINT 6443`), its clock, its container runtime. Joined but NotReady → the CNI (`kubectl describe node`).

### kubeadm — build, rebuild or reset a control plane
Match: kubeadm
Instead of: —
Safety: needs root · `version` and `config images list` are read-only · changes state: `init` builds a control plane, `init phase` re-runs one step, `reset -f` wipes this node's Kubernetes state without asking

**In one line:** `kubeadm init` turns a machine into the first control-plane node (certificates, kubeconfigs, static pods, a bootstrap token); its phases re-run single steps; `kubeadm reset` undoes init or join on a node; `config images` and `version` are read-only helpers.

**Read the command:** `sudo kubeadm init --pod-network-cidr=10.244.0.0/16 --apiserver-advertise-address=10.20.0.10`

| Part | Meaning |
|---|---|
| `init` | create a new control plane on this machine, after preflight checks |
| `--pod-network-cidr=10.244.0.0/16` | the pod IP range: it must match the CNI (Flannel's default) and overlap neither the LAN nor the Service range |
| `--apiserver-advertise-address=10.20.0.10` | the address the API server announces: the NIC the other nodes reach |
| `--node-name=cp1` | the node's name, instead of the hostname |
| `init phase certs apiserver --config kubeadm.yaml` | re-create only the API server certificate (old one moved away first), e.g. with new SANs |
| `reset -f` | undo init or join on this node, without a prompt |
| `config images list` / `pull` | the images this version needs / pull them ahead (air gap, slow links) |
| `version -o short` | the kubeadm binary's version, e.g. `v1.34.1` |

**What the output tells you:** init ends with `Your Kubernetes control-plane has initialized successfully!`, the commands that copy admin.conf into your kubeconfig, and a `kubeadm join …` line for the workers. Problems stop it at preflight with `[ERROR …]` lines (a port in use, no container runtime) before anything changes.

**Why it is effective:** a complete, standard control plane in one command, with every file where upgrades, `kubeadm certs` and the CKA expect it.

**Trap:** `reset` does not clean /etc/cni/net.d, iptables or IPVS rules, or your kubeconfig; leftovers break the next init, so the handbook removes /etc/cni/net.d by hand. On a control-plane node, reset destroys its etcd data. On VirtualBox or Vagrant VMs the default route is often the NAT interface (10.0.2.15): without `--apiserver-advertise-address` the API server announces an address the other nodes cannot reach. The pod CIDR is very hard to change later.

**Next step:** init done → install the CNI, then join the workers. Nodes NotReady → the CNI pods, `ls /etc/cni/net.d`. Wrong SANs → `init phase certs apiserver`, then `init phase upload-config kubeadm --config kubeadm.yaml` so upgrades keep them.

### etcdctl — is etcd healthy and how full, and take a snapshot
Match: etcdctl
Instead of: kubectl get --raw='/readyz?verbose'
Safety: needs root (etcd's client key) · read-only for `endpoint`, `alarm list` and `get` · `snapshot save` writes a file holding every Secret · changes state: `compact`, `defrag`, `alarm disarm`

**In one line:** `etcdctl` talks to etcd, the database of the whole cluster state, over mutual TLS: member health, size and alarms, snapshots for backup, and the maintenance that frees space.

**Read the command:** `sudo ETCDCTL_API=3 etcdctl --endpoints=https://127.0.0.1:2379 --cacert=/etc/kubernetes/pki/etcd/ca.crt --cert=/etc/kubernetes/pki/etcd/server.crt --key=/etc/kubernetes/pki/etcd/server.key endpoint health -w table`

| Part | Meaning |
|---|---|
| `sudo ETCDCTL_API=3` | as root (the key is root-only), with the v3 API (the default since etcd 3.4) |
| `--endpoints=https://127.0.0.1:2379` | the member's client URL, from the etcd manifest |
| `--cacert`, `--cert`, `--key` | CA, client certificate and key: the paths in /etc/kubernetes/manifests/etcd.yaml |
| `endpoint health -w table` | can this member serve requests, and how fast? As a table (`-w json` for jq) |
| `endpoint status` | version, DB size, leader, raft index, active alarms |
| `snapshot save FILE` | a consistent copy of the whole keyspace: the cluster backup |
| `alarm list`, `compact REV`, `defrag`, `alarm disarm` | the NOSPACE fix: drop old revisions, return the space, clear the alarm |

**What the output tells you:**

```
+------------------------+--------+-------------+-------+
|        ENDPOINT        | HEALTH |    TOOK     | ERROR |
+------------------------+--------+-------------+-------+
| https://127.0.0.1:2379 |   true | 11.204571ms |       |
+------------------------+--------+-------------+-------+
$ sudo etcdctl $ETCD_FLAGS alarm list
memberID:10276657743932975437 alarm:NOSPACE
```

`true` within milliseconds is a healthy member; hundreds of milliseconds point at a slow disk. `alarm:NOSPACE`: the database hit its quota (2 GiB by default), so the cluster is read-only until you compact, defragment and disarm.

**Why it is effective:** when the API server times out, etcd is the layer below; these answers come from etcd itself and separate a database or disk problem from one above it.

**Compared with `kubectl get --raw='/readyz?verbose'`:** shows `[+]etcd ok` or a failure as the API server sees it, but no size, leader or alarms, and it needs a working API server.

**Trap:** without the TLS flags etcdctl waits and fails with `context deadline exceeded`, not with an auth error. Use an etcdctl matching the server (the etcd image has one: `kubectl -n kube-system exec etcd-cp1 -- etcdctl …`). Defragment one member at a time: it blocks that member while it runs. A snapshot holds every Secret in clear text unless encryption at rest is on.

**Next step:** slow or unhealthy → the etcd logs (`slow fdatasync`) and the disk under /var/lib/etcd. NOSPACE → compact, defrag, disarm, then a larger `--quota-backend-bytes`. Snapshot saved → `etcdutl snapshot status FILE`, then copy it off the node.

### etcdutl — is this snapshot usable, and restore it into a new data directory
Match: etcdutl
Instead of: etcdctl snapshot restore
Safety: needs root · `snapshot status` is read-only · `snapshot restore` writes a new data directory; the cluster changes only when etcd is pointed at it, and then its whole state returns to the snapshot

**In one line:** `etcdutl` works on etcd's files offline, without a running member: `snapshot status` checks a backup file, `snapshot restore` turns it into a fresh data directory for etcd to start from.

**Read the command:** `sudo etcdutl snapshot restore /var/backups/etcd-2026-10-04-0600.db --data-dir /var/lib/etcd-restore`

| Part | Meaning |
|---|---|
| `sudo` | the data directory belongs to root, like etcd's own |
| `snapshot restore FILE` | build a new etcd data directory from this snapshot |
| `--data-dir /var/lib/etcd-restore` | where: a new path, not one already holding etcd data |
| `snapshot status FILE -w table` | hash, revision, total keys and size: is the file complete? |

**What the output tells you:**

```
$ sudo etcdutl snapshot status /var/backups/etcd/snap-2026-10-04-0600.db -w table
+----------+----------+------------+------------+
|   HASH   | REVISION | TOTAL KEYS | TOTAL SIZE |
+----------+----------+------------+------------+
| 7c3f2a1b |   482113 |       1342 |     8.4 MB |
+----------+----------+------------+------------+
```

A readable file with a plausible key count and size is a usable snapshot; an error means the backup is damaged. restore logs a few lines and leaves a `member` directory in /var/lib/etcd-restore.

**Why it is effective:** status proves a backup is restorable before you need it, and restore never touches the running etcd, so you prepare the new state safely and switch over in one controlled step.

**Compared with `etcdctl snapshot restore`:** the same operation, deprecated in etcdctl in favour of etcdutl and gone from newer releases.

**Trap:** the "restore did nothing" case: etcd keeps serving /var/lib/etcd until the `etcd-data` hostPath in /etc/kubernetes/manifests/etcd.yaml points at the new directory. A restore rolls the **whole** cluster back: objects created since vanish, deleted ones return; stop the API server first, restart the controller manager and scheduler afterwards. With several etcd members, each needs its own restore with matching member flags.

**Next step:** hostPath switched → `sudo crictl ps --name etcd` until it runs, then `kubectl get ns` to confirm the expected state. Status fails → take a new snapshot and check it at once.

### k3s — snapshots, certificates and quorum recovery on a k3s server
Match: k3s
Instead of: the kubeadm and etcdctl procedures, on a k3s cluster
Safety: needs root · `etcd-snapshot ls` is read-only · changes state: `certificate rotate` replaces certificates (k3s stopped first); `server --cluster-reset` turns this server into a new one-member cluster

**In one line:** k3s is one binary that is server, agent and bundled tools (`kubectl`, `crictl`, `ctr`); its subcommands manage the embedded etcd's snapshots and the certificates, and `--cluster-reset` recovers from lost quorum or restores a snapshot.

**Read the command:** `sudo k3s server --cluster-reset --cluster-reset-restore-path=/var/lib/rancher/k3s/server/db/snapshots/etcd-snapshot-k3s-1-1791093600`

| Part | Meaning |
|---|---|
| `sudo` | k3s's data under /var/lib/rancher/k3s belongs to root |
| `server` | run the k3s server by hand (after `systemctl stop k3s`) |
| `--cluster-reset` | make this server a new one-member etcd cluster that keeps its data: the way out of lost quorum |
| `--cluster-reset-restore-path=…` | restore this snapshot first, then reset |
| `etcd-snapshot ls` | the snapshots: every 12 hours by default, 5 kept |
| `certificate rotate` | renew the k3s certificates, with the service stopped |
| `crictl pull docker.io/library/alpine:3.20` | the bundled crictl, already pointed at k3s's containerd: tests the registry mirror and CA setup |

**What the output tells you:** `etcd-snapshot ls` lists Name, Location (a `file://` path or S3), Size and Created per snapshot. `--cluster-reset` exits with a message to restart without the flag: start the service, and on the other servers delete /var/lib/rancher/k3s/server/db before they rejoin.

**Why it is effective:** k3s hides etcd behind its own binary, paths and token; these commands use what k3s really uses.

**Compared with the kubeadm and etcdctl procedures:** etcdctl can reach k3s's etcd once you find its certificate paths; kubeadm commands do not exist on k3s.

**Trap:** a single k3s server uses SQLite by default, not etcd: no etcd snapshots, and the backup is /var/lib/rancher/k3s/server/db plus the server token. Every restore needs the original server token, because k3s encrypts its bootstrap data with it. Certificates renew only when k3s starts near their expiry, so a never-restarted server can still expire. Two servers have no quorum to spare: run one or three.

**Next step:** reset done → `kubectl get nodes`, then rejoin the other servers. No snapshots → the `etcd-snapshot-schedule-cron` and `etcd-s3` settings in the k3s config. Image pulls fail → /etc/rancher/k3s/registries.yaml, then `k3s crictl pull` again.

### helm upgrade / install — deploy or update a release, and roll back on failure
Match: helm upgrade, helm install
Instead of: kubectl apply on rendered templates
Safety: changes state: creates or updates every object of the release and records a new revision

**In one line:** `helm upgrade` renders a chart with your values, applies the result as a new revision of a named release and keeps that revision (as a Secret) for rollback; `--install`, or `helm install`, creates the release first.

**Read the command:** `helm -n shop upgrade web ./chart -f values-prod.yaml --atomic --timeout 10m`

| Part | Meaning |
|---|---|
| `-n shop` | the release's namespace, where its objects and history Secrets live |
| `upgrade web ./chart` | release `web`, from the chart in `./chart` (or `repo/chart`) |
| `-f values-prod.yaml` | a values file; several `-f` merge, the last wins |
| `--atomic` | wait until everything is ready and roll back automatically on failure (Helm 4 renames it `--rollback-on-failure`) |
| `--timeout 10m` | how long to wait (default 5m) |
| `--install --create-namespace` | install if the release is missing, creating the namespace |
| `--set image.tag=1.4.4`, `--reuse-values` | override one value / start from the previous release's values |
| `--wait` | wait for readiness, without the automatic rollback |

**What the output tells you:**

```
Release "web" has been upgraded. Happy Helming!
NAME: web
NAMESPACE: shop
STATUS: deployed
REVISION: 14
```

Failures end with `Error: UPGRADE FAILED: …` and the reason: `context deadline exceeded` (pods not ready in time), `another operation (install/upgrade/rollback) is in progress` (an earlier revision is stuck), or an API server refusal such as `field is immutable`.

**Why it is effective:** one command renders, applies, deletes what the chart dropped and records a revision; with `--atomic` a failed deploy undoes itself instead of leaving half a release.

**Compared with `kubectl apply` on rendered YAML:** fine for one-off objects, but no history, no rollback, and dropped objects are never removed.

**Trap:** without `--wait` or `--atomic`, Helm reports success once the API server accepts the objects, even if every new pod then crashes. A cancelled upgrade (a killed CI job) leaves the release `pending-upgrade`, blocking every later one. `--reuse-values` ignores new chart defaults. CRDs in a chart's crds/ directory are installed once, never upgraded.

**Next step:** failed or pending → `helm -n shop history web`, then `helm rollback`. Immutable field → recreate that object (the handbook's `--cascade=orphan` path). Values unclear → `helm get values web`, `helm template`.

### helm history / rollback — which revision is live, and return to a good one
Match: helm history, helm rollback
Instead of: kubectl rollout undo on Helm-managed workloads
Safety: history is read-only · changes state: rollback re-applies an old revision as a new one

**In one line:** `helm history` lists a release's revisions with status, chart version, app version and description; `helm rollback` re-applies an earlier revision's manifests and values as a new revision.

**Read the command:** `helm -n shop rollback web 12 --wait`

| Part | Meaning |
|---|---|
| `-n shop` | the release's namespace |
| `rollback web` | release `web` |
| `12` | the revision to return to; omitted, the previous one |
| `--wait` | wait until the rolled-back objects are ready |
| `history web` | REVISION, UPDATED, STATUS, CHART, APP VERSION, DESCRIPTION |
| `kubectl -n shop get secret -l owner=helm,name=web -L status,version` | the same history, as the Secrets Helm keeps it in |

**What the output tells you:** (the handbook's stuck release)

```
REVISION   UPDATED                    STATUS            CHART       APP VERSION   DESCRIPTION
12         Sat Oct  4 09:12:44 2026   deployed          web-1.8.1   1.4.3         Upgrade complete
13         Sat Oct  4 13:40:02 2026   pending-upgrade   web-1.8.2   1.4.4         Preparing upgrade
```

Revision 13 never finished, so every new upgrade refuses to start; 12 is the last good one. Other statuses: `superseded`, `failed`, `pending-install`, `pending-rollback`. Rollback answers `Rollback was a success! Happy Helming!` and appears as a new revision described `Rollback to 12`.

**Why it is effective:** history shows exactly which chart and app version is live and which revision broke; rollback returns to a known-good state and clears a stuck pending status in one step.

**Compared with `kubectl rollout undo`:** undo changes one Deployment behind Helm's back; Helm still believes the new revision is live, and its next upgrade re-applies it.

**Trap:** rollback restores manifests and values, not data: database migrations and PVC contents stay. Make sure no pipeline is still working on the release. Helm keeps 10 revisions by default (`--history-max` on upgrade), so an old good one may be gone. If Argo CD or Flux manage the release, roll back in Git.

**Next step:** rolled back → fix the chart or values, then `helm upgrade --atomic`. First install failed and nothing was ever deployed → `helm uninstall`, then install again. One revision's details → `helm get values web --revision 12`, `helm get manifest web --revision 12`.

### helm — repositories, releases and charts
Match: helm
Instead of: —
Safety: `list` and `version` are read-only · `repo add` and `repo update` change your local Helm configuration · `pull` downloads a chart · changes state: `uninstall` deletes every object of the release and its history

**In one line:** the rest of Helm: `list` shows the releases on the cluster, `repo` manages where charts come from, `pull` downloads a chart to read it, `create` scaffolds one, `uninstall` removes a release.

**Read the command:** `helm pull prometheus-community/kube-prometheus-stack --version X.Y.Z --untar`

| Part | Meaning |
|---|---|
| `pull` | download a chart without installing it |
| `prometheus-community/kube-prometheus-stack` | repository name / chart name |
| `--version X.Y.Z` | the **chart** version, not the app version: pin it |
| `--untar` | unpack into a directory, to read values.yaml, the templates and crds/ |
| `list -A` | releases in every namespace with revision, status, chart and app version |
| `repo add traefik https://traefik.github.io/charts`, `repo update` | register a chart repository / refresh every local index |
| `uninstall web` | delete the release's objects and its history |
| `create demo` | scaffold a working example chart in `demo/` |

**What the output tells you:**

```
$ helm list -A
NAME   NAMESPACE   REVISION   UPDATED                                   STATUS     CHART        APP VERSION
demo   shop        4          2026-10-03 10:17:30.412345 +0000 UTC      deployed   demo-0.1.0   1.16.0
web    shop        13         2026-10-04 13:40:02.481516 +0000 UTC      failed     web-1.8.2    1.4.4
```

CHART is the chart's name and version, APP VERSION the application version it declares; `failed` means the last operation on that release failed.

**Why it is effective:** `list -A` finds every release and its state on one screen, and `pull --untar` shows what a chart will install (defaults, CRDs, hooks) before it touches the cluster.

**Trap:** `helm list` shows only deployed and failed releases: one stuck `pending-install` or `pending-upgrade` stays hidden unless you add `--all`. A stale local index reports a chart version as not found until `helm repo update`. `uninstall` also deletes the history (no rollback afterwards); StatefulSet PVCs and CRDs stay behind. Helm uses your kubeconfig: run with sudo and it finds no cluster (`Kubernetes cluster unreachable`).

**Next step:** failed or pending → `helm history`, `helm rollback`. What a release really applied → `helm get manifest REL`, `helm get values REL`. Chart unclear → `helm pull --untar`, then `helm template`.

### argocd app — in sync with Git, healthy, and what did the last sync do?
Match: argocd app
Instead of: kubectl get on each resource, the web UI
Safety: `get`, `diff` and `history` are read-only · changes state: `sync` applies Git to the cluster, `set` changes the Application, `terminate-op` stops a running sync

**In one line:** `argocd app` shows and drives one Argo CD Application: does the cluster match Git (sync), does it work (health), what did the last sync do, and which revisions were deployed.

**Read the command:** `argocd app get shop-web --show-operation`

| Part | Meaning |
|---|---|
| `app get shop-web` | sync and health status, the source and every resource's state |
| `--show-operation` | add the current or last sync operation: revision, phase, message |
| `-o json` | the whole Application as JSON, for jq |
| `app diff shop-web` | rendered Git state against the live objects |
| `app history shop-web` | the deployed revisions with their Git commits |
| `app sync shop-web --revision 8c1e2f0` | sync now, to this commit |
| `app set shop-web --sync-policy none` | turn automated sync off |
| `app terminate-op shop-web` | stop the running sync operation |

**What the output tells you:** (trimmed)

```
Sync Status:        OutOfSync from main (3f2a9c1)
Health Status:      Degraded
Sync Revision:      3f2a9c1d
Phase:              Running
Message:            Retrying attempt #4 at 10:51AM: one or more objects failed to apply
```

The live objects differ from what `main` renders at that commit, and health is `Degraded` (others: `Healthy`, `Progressing`, `Missing`, `Suspended`). The sync of that commit keeps failing and retrying; the resource table further down names the failing object.

**Why it is effective:** it separates "the cluster differs from Git" from "the app is broken", names the failing resource, and shows which commit Argo CD is really trying to apply.

**Compared with `kubectl get` on the resources:** full detail of the live objects, but not whether they match Git or what the controller keeps retrying.

**Trap:** with automated sync and selfHeal, manual kubectl fixes are reverted within minutes: fix Git, or turn automation off first. A child app's policy changed by hand is reset by its parent (app of apps) unless the parent's automation is off too, which is why the handbook disables `platform-apps` first. `argocd app rollback` is refused while auto-sync is on; the GitOps rollback is `git revert`.

**Next step:** OutOfSync that never settles → `argocd app diff` (HPA replicas, injected fields → `ignoreDifferences`). Degraded → the named resource with `kubectl describe` and `kubectl logs`. Stuck Running → `argocd app terminate-op`, fix, sync again.

### argocd — log in, connect repositories and trust their certificates
Match: argocd
Instead of: editing the Argo CD ConfigMaps by hand
Safety: changes state: `login` stores a session token in your CLI configuration; `repo add` and `cert add-*` change what Argo CD can reach and trust · `admin initial-password` prints the admin password

**In one line:** the Argo CD CLI's setup commands: `login`, `repo add` to give Argo CD access to a Git or Helm repository, `cert add-tls` and `add-ssh` to trust a private CA or SSH host keys, `admin initial-password` for the first login.

**Read the command:** `argocd repo add harbor.example.com/charts --type helm --name harbor-charts --enable-oci --username "$HARBOR_ROBOT" --password "$HARBOR_SECRET"`

| Part | Meaning |
|---|---|
| `repo add harbor.example.com/charts` | register this repository and its credentials |
| `--type helm` | a Helm chart repository, not Git |
| `--name harbor-charts` | the name shown for it in Argo CD |
| `--enable-oci` | the charts sit in an OCI registry (Harbor) |
| `--username "$HARBOR_ROBOT" --password "$HARBOR_SECRET"` | a robot account read from variables, so the secret is not typed into shell history |
| `repo list` | every repository with its connection STATUS and MESSAGE |
| `cert add-tls gitlab.example.com --from corp-chain.pem` | trust this CA chain for that host (stored in `argocd-tls-certs-cm`) |
| `login argocd.example.com --grpc-web` | log the CLI in; `--grpc-web` passes through proxies that break gRPC |

**What the output tells you:** (the handbook's `repo list`)

```
TYPE  NAME           REPO                                                   INSECURE  OCI    LFS    CREDS  STATUS      MESSAGE
git                  https://gitlab.example.com/platform/deploy-config.git  false     false  false  true   Failed      ...x509: certificate signed by unknown authority
helm  harbor-charts  harbor.example.com/charts                              false     true   false  true   Successful
```

Harbor works; GitLab fails on TLS because its internal CA is missing from Argo CD's own store, which `cert add-tls` fixes.

**Why it is effective:** Argo CD's repo-server ignores the node's CA bundle and known_hosts and trusts only what these commands store in its ConfigMaps, so this fix actually reaches it.

**Compared with editing the ConfigMaps by hand:** the same objects in the end (keep them in Git long-term), but the CLI writes the right keys in the right format.

**Trap:** `--insecure-skip-server-verification` hides the TLS problem instead of fixing it. `cert add-ssh --batch --from FILE` trusts whatever keys the file holds: take them from a trusted source. `admin initial-password -n argocd` reads `argocd-initial-admin-secret`: change the password, then delete that Secret. `transport is closing` from the CLI usually means a proxy without HTTP/2: add `--grpc-web`.

**Next step:** repo still Failed → `kubectl -n argocd logs deploy/argocd-repo-server --since=15m` for x509 or knownhosts errors. Logged in → `argocd app get APP`.

### flux — which Flux objects are not ready, and make them try again
Match: flux
Instead of: kubectl get on each Flux custom resource
Safety: `get` and `logs` are read-only · changes state: `reconcile` applies now; `suspend` stops reconciliation until `resume`

**In one line:** the `flux` CLI lists Flux's sources, Kustomizations and HelmReleases with their Ready condition and revision, reads the Flux controllers' logs, and triggers, pauses or resumes reconciliation.

**Read the command:** `flux get all -A --status-selector ready=false`

| Part | Meaning |
|---|---|
| `get all` | every Flux kind: Git and Helm sources, Kustomizations, HelmReleases |
| `-A` | all namespaces |
| `--status-selector ready=false` | only objects whose Ready condition is False |
| `logs --level=error --since=30m` | the Flux controllers' errors of the last 30 minutes |
| `reconcile kustomization apps --with-source` | fetch the Git source now, then apply `apps` |
| `suspend helmrelease shop-web -n shop`, `resume …` | stop reconciling it / start again, which makes the controller retry |

**What the output tells you:** (from the handbook)

```
NAMESPACE    NAME                   REVISION  SUSPENDED  READY  MESSAGE
shop         helmrelease/shop-web   0.4.2     False      False  Helm upgrade failed for release shop/shop-web with chart shop-web@0.4.2: upgrade retries exhausted

NAMESPACE    NAME                   REVISION  SUSPENDED  READY  MESSAGE
flux-system  kustomization/apps               False      False  kustomization path not found: stat /tmp/kustomization-417/clusters/prod/apps: no such file or directory
```

One table per kind; MESSAGE is the Ready condition's reason, and SUSPENDED `True` would mean Flux ignores the object on purpose.

**Why it is effective:** one command lists every broken GitOps object with the controller's own explanation, and `reconcile --with-source` tests a fix at once instead of waiting for the interval.

**Compared with `kubectl get kustomizations,helmreleases -A`:** the same custom resources with a READY column, enough for a glance; flux adds revision and suspension state, and triggers reconciles.

**Trap:** `reconcile` without `--with-source` re-applies the revision Flux already has, not your new commit. A suspended object stays suspended until someone resumes it, and deploys silently stop. After `upgrade retries exhausted` a HelmRelease does not retry by itself: fix the cause, then suspend and resume. `kubectl edit` on Flux-managed objects is reverted at the next reconcile.

**Next step:** path not found → the Kustomization's `spec.path` against the branch. Source not ready → credentials, deploy key, CA. HelmRelease failed → `flux logs --level=error`, the values, then suspend and resume.

### velero — what a backup really contains, and a restore you can test safely
Match: velero
Instead of: trusting a Completed backup status
Safety: `backup describe` is read-only · changes state: `install` deploys Velero and its node agent; `restore create` recreates objects (into a new namespace with a mapping)

**In one line:** Velero backs up Kubernetes objects to object storage and, when configured, the data of persistent volumes (CSI snapshots, or file-system copies by its node agent); the `velero` CLI creates, inspects and restores those backups.

**Read the command:** `velero restore create shop-drill --from-backup nightly-20261003 --namespace-mappings shop:shop-restore`

| Part | Meaning |
|---|---|
| `restore create shop-drill` | create a Restore named `shop-drill` |
| `--from-backup nightly-20261003` | the backup to restore from |
| `--namespace-mappings shop:shop-restore` | restore namespace `shop` into a new namespace `shop-restore`, leaving production alone |
| `backup describe nightly-20261003 --details` | phase, errors, warnings and, with `--details`, every resource and volume backup |
| `install --use-node-agent --provider aws …` | deploy Velero with the node-agent DaemonSet (file-system backups) for S3-compatible storage; bucket, plugin and credential options follow |

**What the output tells you:** (from `backup describe --details`)

```
Backup Volumes:
  Velero-Native Snapshots: <none included>

  CSI Snapshots: <none included>

  Pod Volume Backups: <none included>
```

Manifests only: no snapshot and no file-system copy, so a restored database comes back empty. `restore create` answers `Restore request "shop-drill" submitted successfully.`; follow it with `velero restore describe shop-drill`.

**Why it is effective:** `--details` shows what is inside the backup, not just that it finished, and a restore into a mapped namespace, then a row count, is the only real proof that a backup works.

**Compared with the Completed status:** Completed means Velero did everything it was configured to do; volume data is opt-in.

**Trap:** file-system backup copies a volume only when the pod carries the `backup.velero.io/backup-volumes` annotation or Velero runs with `--default-volumes-to-fs-backup`, and a file copy of a running database is not consistent unless hooks quiesce it. `PartiallyFailed` hides its errors in `velero backup logs`. By default a restore skips objects that already exist.

**Next step:** no volumes → `kubectl -n velero get daemonset node-agent`, the annotations, a CSI VolumeSnapshotClass. Storage errors → `kubectl -n velero get backupstoragelocations`, `kubectl -n velero logs deploy/velero`. Restore finished → count rows in `shop-restore`.

### cilium — Cilium's own view of Services and their backends
Match: cilium, cilium-dbg
Instead of: iptables-save, ipvsadm -Ln on a Cilium cluster
Safety: read-only for `status` and `service list` · `cilium connectivity test` deploys test workloads into the cluster

**In one line:** with Cilium as the CNI, and often as kube-proxy's replacement, Services, policies and routing live in eBPF maps rather than iptables, so Cilium's own tools show them: `cilium` on your workstation, `cilium-dbg` inside each agent pod.

**Read the command:** `kubectl -n kube-system exec ds/cilium -- cilium-dbg service list 2>/dev/null | grep 8081`

| Part | Meaning |
|---|---|
| `-n kube-system exec ds/cilium` | run in one pod of the `cilium` agent DaemonSet (kubectl picks one) |
| `--` | the rest is the command inside the agent |
| `cilium-dbg service list` | the agent's load-balancing table: each Service frontend and its backends (older releases call the tool `cilium`) |
| `2>/dev/null` | hide the error on clusters without Cilium |
| `| grep 8081` | only entries for the port in question |
| `cilium status --wait` | from your workstation: wait until agents and operator report OK, then summarise |
| `cilium connectivity test` | deploy test pods and check pod, Service, DNS and policy paths (**creates workloads**) |

**What the output tells you:** (without the grep)

```
ID   Frontend            Service Type   Backend
1    10.96.0.1:443       ClusterIP      1 => 10.20.0.10:6443 (active)
7    192.0.2.10:8081     ExternalIPs    1 => 10.244.1.12:8080 (active)
```

The handbook's mystery port 8081: an ExternalIPs Service on this node's address, forwarded to a pod on 8080, which nothing in `ss`, iptables or IPVS shows.

**Why it is effective:** with kube-proxy replaced there are no KUBE-SERVICES rules and no IPVS table; this table is what the data path actually does.

**Compared with `iptables-save` and `ipvsadm -Ln`:** the right tools where kube-proxy runs; under Cilium's kube-proxy replacement they come back empty.

**Trap:** `ds/cilium` picks one agent; for a node-specific problem exec into that node's agent (`kubectl -n kube-system get pods -l k8s-app=cilium -o wide`). `cilium` (the CLI) and `cilium-dbg` (the agent tool) are different programs. A connectivity test creates its own namespace and pods: check they are gone afterwards.

**Next step:** backend missing → the Service's EndpointSlices and pod readiness. Policy suspected → `cilium-dbg endpoint list` in the agent, Hubble if installed. Agent not OK → `kubectl -n kube-system logs ds/cilium`.
