# 15 — Kubernetes Troubleshooting

The universal loop: **`kubectl get` → `kubectl describe` (read Events!) →
`kubectl logs` → `kubectl exec`**. `describe` Events answer 80% of questions.

---

## 1. Cluster & context sanity

```bash
kubectl config current-context ; kubectl config get-contexts   # am I on the right cluster?!
kubectl cluster-info
kubectl get nodes -o wide                 # Ready? versions? IPs?
kubectl get pods -A | grep -vE "Running|Completed"   # everything unhappy, cluster-wide ★
kubectl get events -A --sort-by=.lastTimestamp | tail -30      # recent cluster events ★
kubectl api-resources | head              # what resource types exist
kubectl version
```

## 2. Pods — the core workflow

```bash
kubectl get pods -n app -o wide           # status, restarts, node, IP
kubectl describe pod mypod -n app         # ★ read the Events section at the bottom
kubectl logs mypod -n app                 # current container logs
kubectl logs mypod -c sidecar -n app      # specific container
kubectl logs mypod --previous -n app      # ★ the CRASHED container's logs
kubectl logs -f deploy/myapp -n app       # follow via the deployment
kubectl logs -l app=web -n app --tail=50  # by label across pods
kubectl exec -it mypod -n app -- sh       # shell inside
kubectl exec mypod -n app -- env          # env as the app sees it
kubectl get pod mypod -o yaml | less      # full live spec+status
kubectl delete pod mypod -n app           # controller recreates it ("pod restart")
```

```
$ kubectl get pods -n app -o wide
NAME          READY  STATUS             RESTARTS       AGE   NODE
web-7d4b9-x2  1/1    Running            0              3d    node-a
web-7d4b9-k8  0/1    CrashLoopBackOff   12 (2m ago)    1h    node-b
api-6f8c2-p1  0/1    ImagePullBackOff   0              10m   node-a
job-batch-q9  0/1    Pending            0              25m   <none>
db-0          1/2    Running            3 (5m ago)     2d    node-c
```
Reading it: `READY 0/1` = the container isn't passing readiness (gets no
traffic even if Running) • `RESTARTS 12 (2m ago)` = actively crash-looping →
`logs --previous` • `NODE <none>` on Pending = never scheduled → `describe` •
`db-0` `1/2` = one of two containers in the pod is down — name the sick one
with `kubectl describe pod db-0`.

### Pod status decoder

| Status | Meaning | First move |
|---|---|---|
| `Pending` | unscheduled or images/volumes not ready | `describe` → Events |
| `ContainerCreating` (stuck) | volume mount/CNI/image issues | `describe` → Events |
| `ImagePullBackOff` / `ErrImagePull` | can't pull image | typo? private registry auth? arch? |
| `CrashLoopBackOff` | starts then dies repeatedly | `logs --previous` |
| `OOMKilled` (in describe: Last State, exit 137) | hit memory **limit** | raise limits or fix leak |
| `CreateContainerConfigError` | missing ConfigMap/Secret it references | `describe` names it |
| `Completed` for a service | main process exited 0 | wrong command/should be a Job? |
| `Evicted` | node out of resources/disk | `describe` says which; check node |
| `Terminating` (stuck) | finalizers or unresponsive node | see below |

### Pending — why won't it schedule?
`describe` Events say it directly:
```
0/5 nodes are available: 3 Insufficient cpu, 2 node(s) had untolerated taint ...
```
```bash
kubectl describe nodes | grep -A5 "Allocated resources"   # per-node headroom
kubectl get nodes -o custom-columns=NAME:.metadata.name,TAINTS:.spec.taints
kubectl top nodes                          # actual usage (metrics-server required)
```
Fixes: right-size requests, add nodes/autoscaler, tolerations, correct
nodeSelector/affinity, free the PVC's AZ (volume can pin a pod to a zone!).

### CrashLoopBackOff
```bash
kubectl logs mypod --previous              # why it died — THE command for this ★
kubectl describe pod mypod                 # exit code, Last State, probe failures
```
Frequent causes: app config error (env/secret), failing **liveness probe**
(k8s kills a healthy-but-slow app → raise `initialDelaySeconds` or use a
startupProbe), missing dependency (DB), OOM (exit 137), wrong command/args.

### Stuck Terminating
```bash
kubectl get pod mypod -o jsonpath='{.metadata.finalizers}'
kubectl delete pod mypod --grace-period=0 --force        # last resort
kubectl get node <its-node>                              # NotReady node holds pods
```

## 3. Deployments & rollouts

```bash
kubectl get deploy,rs -n app
kubectl rollout status deploy/myapp -n app        # blocked rollout shows why-ish
kubectl rollout history deploy/myapp -n app
kubectl rollout undo deploy/myapp -n app          # ★ instant rollback
kubectl rollout undo deploy/myapp --to-revision=3
kubectl rollout restart deploy/myapp -n app       # rolling bounce of all pods
kubectl describe deploy myapp -n app              # conditions: ProgressDeadlineExceeded?
kubectl scale deploy/myapp --replicas=5 -n app
```
Rollout stuck: usually the NEW pods are unhealthy (probes/pull) →
`kubectl get pods` and debug the newest ReplicaSet's pods; also check
PodDisruptionBudgets: `kubectl get pdb -A`.

## 4. Services & networking

```bash
kubectl get svc -n app -o wide
kubectl get endpoints myapp -n app         # ★ EMPTY endpoints = selector matches no
                                           #   READY pods = the #1 service problem
kubectl describe svc myapp -n app          # selector vs pod labels:
kubectl get pods -n app --show-labels
kubectl get ingress -n app ; kubectl describe ingress myapp -n app
kubectl port-forward svc/myapp 8080:80 -n app     # bypass ingress/LB: test service directly ★
kubectl port-forward pod/mypod 8080:80 -n app     # bypass even the service
```

In-cluster connectivity tests:
```bash
kubectl run tmp --rm -it --image=nicolaka/netshoot -- bash   # throwaway toolbox pod ★
# inside: dig myapp.app.svc.cluster.local ; curl -v http://myapp.app:80 ; traceroute ...
kubectl exec -it mypod -- nslookup kubernetes.default        # DNS sanity from a real pod
kubectl get pods -n kube-system -l k8s-app=kube-dns          # CoreDNS healthy?
kubectl logs -n kube-system -l k8s-app=kube-dns --tail=20
kubectl get networkpolicy -A               # a NetworkPolicy may be blocking you
```
DNS shape: `svc.namespace.svc.cluster.local`. Cross-namespace calls need
at least `svc.namespace`. Slow lookups → ndots:5 expansion — use FQDN with
trailing dot or tune dnsConfig.

## 5. Nodes

```bash
kubectl get nodes ; kubectl describe node node1   # ★ Conditions: MemoryPressure,
                                                  #   DiskPressure, Ready; + Events
kubectl top nodes ; kubectl top pods -A --sort-by=memory
kubectl cordon node1                       # stop new pods scheduling here
kubectl drain node1 --ignore-daemonsets --delete-emptydir-data   # evacuate for maintenance
kubectl uncordon node1
# on the node itself:
systemctl status kubelet ; journalctl -u kubelet -e --no-pager | tail -50
crictl ps ; df -h ; free -h                # kubelet dies on full disk!
```
NotReady node → kubelet logs on the node; usual: disk full, cert expired,
CNI broken, network to control plane lost.

## 6. Config, secrets, storage, RBAC

```bash
kubectl get cm,secret -n app
kubectl get secret mysecret -n app -o jsonpath='{.data.password}' | base64 -d
kubectl get pvc -n app                     # Pending PVC = no storageclass/capacity/AZ ★
kubectl describe pvc data-pvc -n app
kubectl get storageclass
kubectl auth can-i delete pods -n app      # RBAC check for me
kubectl auth can-i list secrets --as=system:serviceaccount:app:mysa -n app   # for a SA ★
```
Note: pods do NOT see ConfigMap/Secret env changes until restarted
(`kubectl rollout restart`); mounted files update eventually, env never.

## 7. Resource usage & quotas

```bash
kubectl top pods -n app
kubectl describe quota -n app              # namespace quota blocking creations?
kubectl describe limitrange -n app
kubectl get pods -n app -o custom-columns=NAME:.metadata.name,REQ:.spec.containers[*].resources.requests.cpu,LIM:.spec.containers[*].resources.limits.cpu
```
CPU **limits** cause throttling (latency!) even when the node is idle; memory
**limit** overrun = OOMKill 137.

## 8. EKS specifics (AWS)

```bash
aws eks update-kubeconfig --name mycluster --region ap-south-1   # get/refresh kubeconfig
kubectl get cm aws-auth -n kube-system -o yaml    # IAM→RBAC mapping ("Unauthorized"!)
kubectl get pods -n kube-system                   # aws-node (VPC CNI), coredns, kube-proxy
kubectl describe ds aws-node -n kube-system
```
- `error: You must be logged in` / `Unauthorized` → your IAM principal isn't in
  aws-auth ConfigMap / EKS access entries.
- Pods stuck ContainerCreating with CNI errors → subnet out of IPs (VPC CNI
  assigns real VPC IPs; check subnet free-IP count) or aws-node daemonset broken.
- LoadBalancer service Pending → AWS LB controller missing/misconfigured, or
  subnet tags (`kubernetes.io/role/elb`) absent.

## Decision tree: "my app on K8s is down"

```
kubectl get pods -o wide
├── no pods at all       → deployment exists? kubectl get deploy,rs; quota? events
├── Pending              → describe → insufficient resources / taints / PVC
├── ImagePullBackOff     → image name/tag/registry-secret/arch
├── CrashLoopBackOff     → logs --previous ; describe (exit code, probes)
├── Running but unreachable
│   ├── kubectl port-forward pod  → works? then service layer:
│   ├── kubectl get endpoints     → empty? label/readiness mismatch
│   ├── readinessProbe failing?   → describe pod
│   └── ingress/LB → describe ingress; controller logs; (EKS: LB controller, SGs)
└── Running but slow     → kubectl top pods (throttled? at memory limit?), node pressure
```
