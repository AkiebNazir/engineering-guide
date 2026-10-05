# Kubernetes and Orchestration

If Docker is how you run one container on one machine, **Kubernetes (K8s)** is how you run
thousands of containers across hundreds of machines while treating the machines as one
pool. You declare what should be running; Kubernetes places it, restarts it, scales it,
rolls out new versions without downtime and wires up networking between the pieces. This
chapter builds the mental model from zero, then goes through the parts interviews and
incidents actually test: the control-plane architecture and what happens on
`kubectl apply`, scheduling with requests and limits, rolling updates and probes,
Services and Gateway API, configuration and storage, autoscaling, RBAC, Helm, and a
debugging playbook for every common Pod status.

## Foundations — What problem does an orchestrator solve?

### Life without one

Say you run a checkout service as containers on ten servers. Without an orchestrator,
someone (or some script) has to decide which server runs which container, notice when a
server dies and start its containers elsewhere, update the load balancer every time a
container moves, roll out version 2 one server at a time while watching error rates, and
restart containers that hang. Every company that did this by hand wrote the same fragile
scripts. Google did it at scale with an internal system called **Borg**; Kubernetes (open
sourced by Google in 2014, now a CNCF project) is the public redesign of those ideas.

### The core idea: desired state and reconciliation

Kubernetes is **declarative**. You don't say "start container A on server 3". You write
down the state you want ("3 replicas of `checkout:1.8`, each with 250m CPU, reachable at
the name `checkout`") and submit it to the API. Then many small **controllers** each run
the same loop forever:

1. **Observe** the current state (from the API).
2. **Compare** it with the desired state.
3. **Act** to close the gap (create a Pod, delete a Pod, update a load-balancer entry).

If a server dies and takes a Pod with it, the ReplicaSet controller sees 2 running where
3 are desired and creates a new one; the scheduler places it on a healthy node. Nobody
wrote a "server died" handler. Self-healing falls out of reconciliation.

### The pieces

| Piece | What it is | Everyday analogy |
|---|---|---|
| **Cluster** | A set of machines managed as one | A restaurant kitchen |
| **Node** | One machine (VM or bare metal) that runs workloads | A cooking station |
| **Control plane** | The API server, database (etcd), scheduler and controllers that decide what runs where | The head chef and the order board |
| **Pod** | The smallest unit Kubernetes runs: one or more containers sharing a network namespace (one IP, `localhost`) and volumes | One plate being prepared |
| **Deployment** | "Keep N identical Pods of this template running, and roll out changes gradually" | A standing order: "always have 3 margheritas ready" |
| **Service** | A stable virtual IP and DNS name that load-balances to the Pods currently matching a label selector | The pass window where waiters always pick up, whichever cook made the dish |
| **Namespace** | A named scope for resources, quotas and access rules | Separate sections of the kitchen |
| **Labels / selectors** | Key-value tags on objects, and queries over them; the glue between objects | Colored tickets on the plates |

### How the pieces fit

```arch
%% caption: A Deployment manages ReplicaSets, which manage Pods; a Service finds the Pods by label and load-balances to the ready ones.
grid 160x110
node dep "Deployment" at 1,0 icon=package sub="replicas: 3, template"
node rs "ReplicaSet" at 1,1 icon=layers sub="pod-template-hash"
group pods "Pods (app=checkout), spread over nodes" color=slate icon=server
node p1 "Pod 1" at 0,2 in pods icon=container sub="node-a"
node p2 "Pod 2" at 1,2 in pods icon=container sub="node-b"
node p3 "Pod 3" at 2,2 in pods icon=container sub="node-c"
node svc "Service" at 1,3 icon=lb sub="checkout:80 → 8080"
dep -> rs : "owns"
rs -> p1
rs -> p2
rs -> p3
svc -> p1
svc -> p2
svc -> p3
```

A concrete walk-through: you `kubectl apply` a Deployment for `checkout`. The Deployment
creates a ReplicaSet, the ReplicaSet creates three Pods, the scheduler assigns each to a
node, and each node's agent (the kubelet) starts the containers. A Service named
`checkout` selects Pods labeled `app=checkout`; other services call
`http://checkout` and Kubernetes DNS plus kube-proxy deliver the request to one ready Pod.

### Vocabulary table

| Term | Meaning |
|---|---|
| Manifest | A YAML (or JSON) description of an object: `apiVersion`, `kind`, `metadata`, `spec` |
| `spec` vs `status` | What you want, written by you; what is, written by controllers |
| Controller | A reconciliation loop for one kind of object |
| Operator | A custom controller plus Custom Resource Definitions (CRDs) that encodes how to run a specific system (a Postgres operator, a Kafka operator such as Strimzi) |
| kubelet | The agent on every node that makes the Pods assigned to it actually run |
| CRI / CNI / CSI | Plug-in interfaces for the container runtime, the network and storage |
| Probe | A health check the kubelet runs: liveness, readiness, startup |
| Requests / limits | The resources a container is guaranteed (used for scheduling) / the ceiling it may use |

## 1. Architecture: the control plane and the nodes

```arch
%% caption: Everything talks to the API server; only the API server talks to etcd. The scheduler, controllers and kubelets watch the API and reconcile.
grid 170x100
node kubectl "kubectl / CI" at 1,0 icon=cli
group cp "Control plane" color=blue icon=k8s
node sched "kube-scheduler" at 0,1 in cp icon=scheduler sub="assigns Pods to nodes"
node api "kube-apiserver" at 1,1 in cp icon=api sub="authn, authz, admission"
node etcd "etcd" at 2,1 in cp icon=etcd sub="Raft, the only state"
node cm "controller-manager" at 0,2 in cp icon=process sub="Deployment, RS, Node…"
node ccm "cloud-controller" at 2,2 in cp icon=cloud sub="LBs, routes, nodes"
group nd "Worker node" color=orange icon=server
node kubelet "kubelet" at 1,3 in nd icon=worker sub="runs assigned Pods"
node proxy "kube-proxy" at 2,3 in nd icon=network sub="Service rules"
node rt "containerd / CRI-O" at 1,4 in nd icon=container sub="via CRI"
node cni "CNI plugin" at 0,4 in nd icon=connection sub="Pod IPs, policy"
kubectl -> api
api <-> etcd
sched ..> api
cm ..> api
ccm ..> api
kubelet ..> api : "watch"
proxy ..> api
kubelet -> rt
rt -> cni
```

**Control plane components**

| Component | Job | Failure impact |
|---|---|---|
| **kube-apiserver** | The only front door. Authenticates, authorizes (RBAC), runs admission (mutating then validating webhooks and policies), validates, persists to etcd, serves **watches** | Down: no changes can be made; already-running Pods keep running |
| **etcd** | Strongly consistent key-value store (Raft); the single source of truth for cluster state | Loss of quorum = API read-only/unavailable. Back it up; run 3 or 5 members |
| **kube-scheduler** | Watches for Pods without a `nodeName`, picks a node, writes the binding | Down: new Pods stay `Pending`; running ones are unaffected |
| **kube-controller-manager** | Runs the built-in controllers: Deployment, ReplicaSet, StatefulSet, Job, Node lifecycle, EndpointSlice, ServiceAccount… | Down: nothing self-heals or rolls out |
| **cloud-controller-manager** | Cloud-specific loops: create load balancers for `type: LoadBalancer`, manage node lifecycle and routes | Down: no new cloud LBs |

**Node components**

| Component | Job |
|---|---|
| **kubelet** | Watches for Pods bound to its node; asks the runtime to pull images and start containers; runs probes; reports status; evicts Pods under resource pressure |
| **Container runtime** | containerd or CRI-O, through the Container Runtime Interface. Kubernetes removed dockershim in v1.24, so dockerd is not on the node |
| **kube-proxy** | Programs Service virtual IPs into the node's packet filter: iptables (default), IPVS, or nftables (GA in v1.33). Some CNIs (Cilium) replace it with eBPF |
| **CNI plugin** | Gives each Pod an IP and connectivity (Calico, Cilium, the cloud's VPC CNI) and usually enforces NetworkPolicy |

Two design points interviewers like: **everything is a watch on the API server** (no
component calls another directly, which is why they can fail and restart independently),
and **the API server is the only etcd client** (etcd is never exposed to workloads).
Managed offerings (GKE, EKS, AKS) run the control plane for you; you still own the nodes
(unless you use GKE Autopilot, EKS Auto Mode or Fargate) and everything on them.

## 2. What happens when you run `kubectl apply`

```mermaid
sequenceDiagram
    %% caption: One Deployment apply, from the API call to traffic reaching the new Pod
    participant U as kubectl
    participant A as API server
    participant E as etcd
    participant C as Deployment + RS controllers
    participant S as Scheduler
    participant K as kubelet (node-b)
    U->>A: PATCH Deployment checkout (server-side apply)
    A->>A: authn → RBAC → mutating admission → schema → validating admission
    A->>E: write Deployment (resourceVersion++)
    A-->>U: 200 OK (nothing is running yet)
    A--)C: watch event: Deployment changed
    C->>A: create ReplicaSet, then Pods (no nodeName)
    A--)S: watch event: unscheduled Pod
    S->>S: filter nodes → score nodes
    S->>A: bind Pod to node-b
    A--)K: watch event: Pod bound to me
    K->>K: pull image (CRI), create sandbox, CNI assigns IP, start containers
    K->>A: status Running; readiness probe passes → Ready
    A--)C: EndpointSlice controller adds Pod IP to the Service
    Note over K: kube-proxy on every node updates its rules; traffic can arrive
```

Things to take from this:

- `kubectl apply` returning success means **the desired state was stored**, not that
  anything runs. Use `kubectl rollout status deploy/checkout` (or `kubectl wait`) in CI.
- Every arrow after the first write is a **watch**, with no direct calls between components.
- A Pod gets traffic only after it is **Ready** *and* the EndpointSlice change has
  propagated to every node's kube-proxy (usually well under a second, but not zero).

## 3. Workloads: which controller for which job

| Kind | Use for | Key behavior |
|---|---|---|
| **Deployment** | Stateless services | Rolling updates via ReplicaSets; any Pod is interchangeable |
| **StatefulSet** | Databases, Kafka, ZooKeeper-style quorum systems | Stable names (`db-0`, `db-1`), stable per-Pod volumes, ordered start/stop |
| **DaemonSet** | One Pod per node: log shippers, node exporters, CNI agents | New nodes get a copy automatically |
| **Job** | Run to completion (migrations, batch) | Retries with `backoffLimit`; `parallelism`/`completions`; indexed jobs |
| **CronJob** | Scheduled Jobs | `concurrencyPolicy: Forbid` to avoid overlapping runs; `timeZone` field |
| **Pod** (bare) | Almost never | Nothing recreates it if its node dies |

### A production-grade Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout
  namespace: shop
  labels: { app: checkout }
spec:
  replicas: 3
  revisionHistoryLimit: 5
  selector:
    matchLabels: { app: checkout }          # immutable after creation
  strategy:
    type: RollingUpdate
    rollingUpdate: { maxSurge: 1, maxUnavailable: 0 }
  template:
    metadata:
      labels: { app: checkout }
    spec:
      serviceAccountName: checkout
      terminationGracePeriodSeconds: 30
      securityContext:
        runAsNonRoot: true
        seccompProfile: { type: RuntimeDefault }
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector: { matchLabels: { app: checkout } }
      containers:
        - name: app
          image: registry.example.com/checkout@sha256:3f1c9a0e5b7d2c4f6a8b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f
          ports: [{ name: http, containerPort: 8080 }]
          envFrom: [{ configMapRef: { name: checkout-config } }]
          env:
            - name: DB_PASSWORD
              valueFrom: { secretKeyRef: { name: checkout-db, key: password } }
          resources:
            requests: { cpu: 250m, memory: 256Mi }
            limits:   { memory: 256Mi }            # memory limit = request; no CPU limit (see §4)
          startupProbe:
            httpGet: { path: /healthz, port: http }
            failureThreshold: 30
            periodSeconds: 2                       # up to 60 s to start
          readinessProbe:
            httpGet: { path: /ready, port: http }
            periodSeconds: 5
          livenessProbe:
            httpGet: { path: /healthz, port: http }
            periodSeconds: 10
            failureThreshold: 3
          lifecycle:
            preStop:
              sleep: { seconds: 5 }                # let endpoint removal propagate (§5)
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities: { drop: ["ALL"] }
```

The `preStop.sleep` action is built into the kubelet (on by default since v1.30; no `sleep` binary needed in the
image), which matters for distroless images. On older clusters use
`exec: { command: ["sleep", "5"] }`.

### Multi-container Pods and native sidecars

Containers in one Pod share the network namespace (same IP, talk over `localhost`) and
can share volumes. Patterns: a **sidecar** (log shipper, service-mesh proxy, secrets
refresher), an **init container** (run migrations or wait for a dependency before the app
starts), an **adapter** or **ambassador**. Since v1.33, **native sidecars** are GA: an
init container with `restartPolicy: Always` starts before the app containers, keeps
running beside them, and is stopped *after* them, which fixes the old problems of Jobs
never completing because a sidecar kept running and of proxies dying before the app
finished draining.

## 4. Scheduling, resources and QoS

### Requests and limits

- **Request**: what the scheduler reserves on a node. A node "fits" a Pod if the sum of
  requests of the Pods on it plus the new one is at most the node's *allocatable*
  capacity. Requests are also the CPU weight under contention.
- **Limit**: the cgroup ceiling. Exceed the **memory** limit → the container is
  OOM-killed (`OOMKilled`, exit 137) and restarted. Exceed the **CPU** limit → the
  container is **throttled** (CFS quota), never killed.

CPU is in cores (`250m` = a quarter core); memory in bytes (`256Mi`).

**The CPU-limits debate, precisely.** A CPU limit caps usage per 100 ms period. A
multi-threaded service that bursts (GC, a spike of requests) can exhaust its quota in the
first 20 ms and sit throttled for 80 ms, adding tail latency while average CPU looks
low. Many teams therefore set **CPU requests but no CPU limit** for latency-sensitive
services and rely on requests for fair sharing, while **always setting a memory limit
equal to the memory request** (memory is not compressible; overcommitting it leads to
node-level OOMs and evictions). Multi-tenant clusters that need hard isolation keep CPU
limits. Watch `container_cpu_cfs_throttled_periods_total` to see throttling.

### QoS classes and eviction

| QoS class | Rule | Evicted |
|---|---|---|
| **Guaranteed** | Every container has requests = limits for both CPU and memory | Last |
| **Burstable** | At least one request or limit set, not Guaranteed | Middle, ordered by usage above request |
| **BestEffort** | No requests or limits at all | First |

When a node runs low on memory or disk (kubelet eviction thresholds, e.g. the default
hard threshold `memory.available<100Mi`), the kubelet **evicts** Pods (status `Evicted`)
starting with those using the most above their requests. This is distinct from a cgroup
OOM kill of one container.

### How the scheduler picks a node

The scheduler runs a pipeline of plugins for each Pending Pod:

1. **Filter**: drop nodes that can't run it: not enough allocatable CPU/memory for the
   *requests*, a `nodeSelector`/required node affinity mismatch, a taint the Pod doesn't
   tolerate, a volume in another zone, host port conflicts.
2. **Score**: rank the survivors: spread Pods of the same app, prefer nodes with the
   image already present, balance resource use, honor preferred affinities.
3. **Bind**: write the chosen node to the Pod. If no node passes the filters, the
   **PostFilter** step may **preempt** (evict) lower-priority Pods to make room, based on
   `PriorityClass`; otherwise the Pod stays `Pending` with an event explaining why
   (`0/12 nodes are available: 12 Insufficient cpu`).

| Tool | Expresses | Example |
|---|---|---|
| `nodeSelector` / node affinity | "Run on nodes with these labels" (required or preferred) | GPU Pods on `accelerator=nvidia-l4` nodes |
| Taints and tolerations | "Keep everyone off this node unless they tolerate it" | Dedicated nodes for Kafka; `NoSchedule` on GPU nodes |
| Pod affinity / anti-affinity | "Near / away from Pods with these labels" | Never two replicas of the DB on one node |
| `topologySpreadConstraints` | "Keep counts balanced across zones/nodes within `maxSkew`" | Survive a zone outage with capacity left |
| `PriorityClass` | Who wins when capacity is short | Payment API preempts batch jobs |
| PodDisruptionBudget | How many replicas voluntary disruptions may take down at once | `minAvailable: 2` blocks a node drain from taking the third |

## 5. Rolling updates, probes and graceful shutdown

### Rolling update mechanics

Changing the Pod template (a new image, env var, anything under `spec.template`) makes the
Deployment create a **new ReplicaSet** and shift replicas from old to new, bounded by:

- `maxSurge`: how many Pods above `replicas` may exist during the rollout (default 25%).
- `maxUnavailable`: how many below `replicas` may be unready (default 25%).

With `replicas: 3, maxSurge: 1, maxUnavailable: 0`, the controller adds one v2 Pod, waits
until it is **Ready**, removes one v1 Pod, and repeats. Capacity never drops below 3.
Readiness is what gates progress: a v2 Pod that never becomes Ready stalls the rollout,
the old Pods keep serving, and after `progressDeadlineSeconds` (default 600) the
Deployment reports `Progressing=False` so CI can fail and roll back.

```bash
kubectl set image deploy/checkout app=registry.example.com/checkout:1.9.0
kubectl rollout status deploy/checkout --timeout=5m
kubectl rollout history deploy/checkout
kubectl rollout undo deploy/checkout            # back to the previous ReplicaSet
kubectl rollout restart deploy/checkout         # re-create Pods with the same spec
```

A `RollingUpdate` is the only strategy besides `Recreate` built into Deployments. Canary,
blue-green and analysis-driven progressive delivery come from Argo Rollouts, Flagger or a
service mesh; see [Deployment Strategies](../CICD/03_deployment_strategies.md).

### Probes: three different questions

| Probe | Question | On failure | Common mistake |
|---|---|---|---|
| **startup** | "Has it finished starting?" | Kills and restarts after `failureThreshold × periodSeconds` | Missing, so a slow JVM start trips liveness and loops forever |
| **readiness** | "Should it get traffic right now?" | Removed from Service endpoints; not restarted | Checking downstream dependencies, so one DB blip marks *every* Pod unready at once |
| **liveness** | "Is it wedged beyond self-recovery?" | Container restarted | Checking dependencies, so a DB outage restarts the whole fleet and makes it worse |

Liveness should check only the process itself (event loop alive, not deadlocked).
Readiness may reflect local overload or warm-up, but be careful with shared dependencies.

### Graceful termination, and the endpoint race

When a Pod is deleted (rollout, scale-down, node drain), two things start **in parallel**:

1. The kubelet runs the `preStop` hook, then sends SIGTERM to each container, waits up to
   `terminationGracePeriodSeconds` (default 30 s, counted from the start of preStop), then
   SIGKILL.
2. The EndpointSlice controller removes the Pod's IP, and every node's kube-proxy (and
   any ingress controller or mesh) has to observe that and update its rules.

If the app exits on SIGTERM before step 2 has propagated, some nodes still route new
connections to a dead Pod: brief 502s/connection resets on every deploy. The fix is the
`preStop` sleep of a few seconds before SIGTERM, and an app that on SIGTERM stops
accepting new work, finishes in-flight requests, closes idle keep-alive connections and
then exits.

<div class="lab" data-viz="flow-k8s-rollout"></div>

## 6. Networking: Services, DNS, Gateway API and NetworkPolicy

### The model

Every Pod gets its own IP, and every Pod can reach every other Pod without NAT (the
CNI's job). Pod IPs are ephemeral, so clients use **Services**.

| Service type | What you get | Use for |
|---|---|---|
| `ClusterIP` (default) | A virtual IP reachable only inside the cluster | Service-to-service calls |
| Headless (`clusterIP: None`) | DNS returns the Pod IPs directly | StatefulSets (`db-0.db.shop.svc`), client-side load balancing, gRPC |
| `NodePort` | A port (30000–32767) on every node | Behind an external LB you manage |
| `LoadBalancer` | A cloud load balancer pointing at the Service | Exposing TCP/UDP services directly |
| `ExternalName` | A DNS CNAME | Aliasing an external database |

DNS: CoreDNS serves `<service>.<namespace>.svc.cluster.local`. Pods' `/etc/resolv.conf`
has `ndots:5` and several search domains, so a lookup of an external name like
`api.stripe.com` may first try `api.stripe.com.shop.svc.cluster.local` and friends. At
high request rates this multiplies DNS traffic; use fully qualified names with a
trailing dot or lower `ndots` in `dnsConfig`.

```arch
%% caption: North-south traffic enters through a Gateway, is routed by host and path to a Service, and kube-proxy rules pick a ready Pod.
grid 170x100
node user "Client" at 1,0 icon=browser sub="api.example.com"
node lb "Cloud LB" at 1,1 icon=lb sub="L4, per Gateway"
group cl "Cluster" color=blue icon=k8s
node gw "Gateway" at 1,2 in cl icon=gateway sub="HTTPRoute: /v1/checkout"
node svc "Service checkout" at 1,3 in cl icon=network sub="ClusterIP + EndpointSlice"
node p1 "Pod" at 0,4 in cl icon=container sub="ready"
node p2 "Pod" at 1,4 in cl icon=container sub="ready"
node p3 "Pod" at 2,4 in cl icon=container sub="not ready" color=red
user -> lb -> gw -> svc
svc -> p1
svc -> p2
svc .. p3 : "excluded"
```

### Ingress and the Gateway API

An **Ingress** is an L7 HTTP routing rule (host and path → Service) implemented by an
ingress controller. It was deliberately minimal; everything beyond host/path/TLS became
controller-specific annotations. The **Gateway API** (v1.0 GA in 2023) is its successor:
role-oriented resources (`GatewayClass` owned by the platform, `Gateway` owned by the
cluster operator, `HTTPRoute`/`GRPCRoute` owned by app teams), with header matching,
traffic splitting and cross-namespace rules in the spec. The widely used community
**ingress-nginx** controller was retired in March 2026 (announced November 2025), which
pushed many teams to migrate; new clusters should start with a Gateway API
implementation (Envoy Gateway, Istio, Cilium, NGINX Gateway Fabric, the cloud's own).

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: checkout
  namespace: shop
spec:
  parentRefs: [{ name: public, namespace: infra }]
  hostnames: ["api.example.com"]
  rules:
    - matches: [{ path: { type: PathPrefix, value: /v1/checkout } }]
      backendRefs:
        - { name: checkout, port: 80, weight: 90 }
        - { name: checkout-canary, port: 80, weight: 10 }
```

### NetworkPolicy

By default every Pod can talk to every Pod. A NetworkPolicy selects Pods and allows only
listed ingress/egress; once any policy selects a Pod for a direction, everything not
allowed in that direction is denied. It is enforced by the CNI (a CNI without policy
support silently ignores them). Start with default-deny per namespace, then allow:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: checkout-allow-gateway, namespace: shop }
spec:
  podSelector: { matchLabels: { app: checkout } }
  policyTypes: [Ingress]
  ingress:
    - from:
        - namespaceSelector: { matchLabels: { kubernetes.io/metadata.name: infra } }
      ports: [{ port: 8080 }]
```

## 7. Configuration and Secrets

- **ConfigMap**: non-secret key-values or whole files. Inject as env vars (`envFrom`) or
  mount as files. **Env vars are read once at start**; a changed ConfigMap does not reach a
  running process until the Pod restarts. Mounted files update in place after a delay
  (≈ up to a minute; not for `subPath` mounts). A common pattern is to put a hash of the
  config in a Pod annotation (Helm does this with `sha256sum`) so config changes roll the
  Deployment.
- **Secret**: the same shape, for credentials. **Base64 is an encoding, not
  encryption.** Anyone who can `get` the Secret or exec into the Pod can read it. Protect
  Secrets with: RBAC that denies `get/list secrets` broadly, **encryption at rest** in etcd
  (an `EncryptionConfiguration` with a KMS provider; managed clusters offer it as a
  setting), and an external source of truth (Vault, AWS Secrets Manager, GCP Secret
  Manager) synced by the External Secrets Operator or mounted by the Secrets Store CSI
  driver. Sealed Secrets lets you commit encrypted Secrets to Git for GitOps. See
  [Secret Management](11_secret_management.md).

```yaml
apiVersion: v1
kind: ConfigMap
metadata: { name: checkout-config, namespace: shop }
data:
  LOG_LEVEL: "info"
  PAYMENTS_URL: "http://payments.shop.svc.cluster.local"
---
apiVersion: v1
kind: Secret
metadata: { name: checkout-db, namespace: shop }
type: Opaque
stringData:                 # plain text here; the API stores it base64-encoded
  password: "change-me"     # in real life this comes from External Secrets, not Git
```

## 8. Storage

| Object | Role |
|---|---|
| **PersistentVolume (PV)** | A piece of storage (a cloud disk, an NFS share) |
| **PersistentVolumeClaim (PVC)** | A Pod's request: "10Gi, ReadWriteOnce, class `fast-ssd`" |
| **StorageClass** | How to dynamically provision PVs (which CSI driver, disk type, `volumeBindingMode`) |
| **CSI driver** | The plug-in that talks to the storage system |

Access modes: `ReadWriteOnce` (one node; typical cloud block disks), `ReadWriteOncePod`
(exactly one Pod), `ReadOnlyMany`, `ReadWriteMany` (NFS, EFS, Filestore, CephFS). Use
`volumeBindingMode: WaitForFirstConsumer` so the disk is created in the zone where the
scheduler places the Pod; otherwise a zonal disk can be created in a zone where the Pod
can't run, and the Pod stays `Pending`. StatefulSets use `volumeClaimTemplates` to give
each replica its own PVC, which survives Pod rescheduling (and, by default, StatefulSet
deletion).

Running databases on Kubernetes is common in 2026 with mature operators (CloudNativePG,
Strimzi for Kafka, Vitess), but a managed database is still the lower-risk default unless
a team has the operational depth.

## 9. Autoscaling

| Autoscaler | Scales | Signal |
|---|---|---|
| **HorizontalPodAutoscaler (HPA)** | Replica count | CPU/memory utilization vs requests, custom or external metrics |
| **VerticalPodAutoscaler (VPA)** | Requests/limits per Pod | Historical usage; recommend-only mode is the safe start |
| **KEDA** | Replicas, including to zero | Event sources: Kafka lag, queue depth, cron, Prometheus queries |
| **Cluster Autoscaler** | Node groups | Pending Pods that don't fit; underused nodes |
| **Karpenter** | Individual nodes of the right size/type | Pending Pods; consolidates to cheaper nodes |

HPA math: `desiredReplicas = ceil(currentReplicas × currentMetric / targetMetric)`,
with a 10% tolerance band and, by default, a 5-minute scale-down stabilization window
to avoid flapping. Utilization is measured **against requests**, so wrong requests make
the HPA wrong: requests too low and 70% "utilization" is reached almost idle.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata: { name: checkout, namespace: shop }
spec:
  scaleTargetRef: { apiVersion: apps/v1, kind: Deployment, name: checkout }
  minReplicas: 3
  maxReplicas: 30
  metrics:
    - type: Resource
      resource:
        name: cpu
        target: { type: Utilization, averageUtilization: 70 }
  behavior:
    scaleUp:
      policies: [{ type: Percent, value: 100, periodSeconds: 30 }]
    scaleDown:
      stabilizationWindowSeconds: 300
```

Don't let an HPA and a VPA both act on CPU for the same workload; they fight. And if a
Deployment is managed by an HPA, leave `replicas` out of the manifest you apply from Git,
or every apply resets the count.

## 10. RBAC and cluster security

Kubernetes is entirely API-driven, so security is mostly "who may call which API verb on
which resource".

- **Role** (namespaced) / **ClusterRole** (cluster-wide): lists of verbs on resources.
- **RoleBinding** / **ClusterRoleBinding**: grant a role to users, groups or
  **ServiceAccounts**.
- **ServiceAccount**: the identity of a Pod. Since v1.24 Pods get short-lived,
  audience-bound **projected tokens**, not long-lived token Secrets. Set
  `automountServiceAccountToken: false` for Pods that never call the API.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata: { name: deployer, namespace: shop }
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: rollout-manager, namespace: shop }
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get", "list", "watch", "patch"]
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: deployer-rollout, namespace: shop }
subjects: [{ kind: ServiceAccount, name: deployer, namespace: shop }]
roleRef: { apiGroup: rbac.authorization.k8s.io, kind: Role, name: rollout-manager }
```

`kubectl auth can-i patch deployments -n shop --as=system:serviceaccount:shop:deployer`
checks a permission. Dangerous grants to watch for: `*` verbs, `secrets` get/list,
`pods/exec`, `create pods` in privileged namespaces (lets you mount any Secret or the
host), `escalate`/`bind`/`impersonate`.

Other layers: **Pod Security Admission** enforces the Pod Security Standards
(`privileged`, `baseline`, `restricted`) per namespace via labels
(`pod-security.kubernetes.io/enforce: restricted`); it replaced PodSecurityPolicy, which
was removed in v1.25. Policy engines (Kyverno, OPA Gatekeeper, or built-in
`ValidatingAdmissionPolicy` with CEL) enforce custom rules such as "images must come from
our registry and be signed". Cloud **workload identity** (GKE Workload Identity, EKS Pod
Identity/IRSA, Azure Workload Identity) maps a ServiceAccount to a cloud IAM role, so no
cloud keys live in Secrets.

## 11. Helm: packaging and releasing manifests

Raw YAML is hard to reuse across environments: dev wants 1 replica and a small DB, prod
wants 30 and a different domain. **Helm** packages templated manifests into a **chart**;
installing a chart with a set of **values** creates a **release**, and Helm records every
release revision so it can upgrade and roll back.

```text
checkout/
  Chart.yaml            # name, version (of the chart), appVersion, dependencies
  values.yaml           # defaults
  values-prod.yaml      # per-environment overrides (often kept outside the chart)
  templates/
    deployment.yaml
    service.yaml
    hpa.yaml
    _helpers.tpl        # named template snippets
```

```yaml
# templates/deployment.yaml (excerpt)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "checkout.fullname" . }}
  labels:
    {{- include "checkout.labels" . | nindent 4 }}
spec:
  {{- if not .Values.autoscaling.enabled }}
  replicas: {{ .Values.replicaCount }}
  {{- end }}
  selector:
    matchLabels:
      {{- include "checkout.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
      labels:
        {{- include "checkout.selectorLabels" . | nindent 8 }}
    spec:
      containers:
        - name: app
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag | default .Chart.AppVersion }}"
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

```yaml
# values.yaml
replicaCount: 3
image:
  repository: registry.example.com/checkout
  tag: ""
autoscaling:
  enabled: false
resources:
  requests: { cpu: 250m, memory: 256Mi }
  limits: { memory: 256Mi }
```

```bash
helm lint ./checkout
helm template checkout ./checkout -f values-prod.yaml | kubectl diff -f -   # see what would change
helm upgrade --install checkout ./checkout -n shop -f values-prod.yaml --atomic --wait --timeout 5m
helm history checkout -n shop
helm rollback checkout 7 -n shop
helm push checkout-1.4.0.tgz oci://registry.example.com/charts                # charts live in OCI registries
```

Facts worth knowing: Helm 3 removed the in-cluster Tiller component (2019), so Helm uses
your kubeconfig credentials and stores release state as Secrets in the release's
namespace. Helm 4 (released November 2025) keeps installing `apiVersion: v2` charts and
moves toward server-side apply. `--atomic` rolls back automatically if the upgrade fails.
Helm hooks (`pre-upgrade` Jobs for migrations) are powerful but run outside the normal
rollout; keep them idempotent.

**Helm vs Kustomize:** Kustomize (built into `kubectl apply -k`) patches plain YAML with
overlays per environment and has no templating language. Helm is better for distributing
software to others (third-party charts for Prometheus, cert-manager, Strimzi); Kustomize
is often simpler for your own services. GitOps tools (Argo CD, Flux) render either and
continuously reconcile the cluster to Git; see [GitOps and Argo CD](../CICD/04_gitops_and_argocd.md).

## 12. Daily `kubectl` and a debugging playbook

```bash
kubectl config get-contexts && kubectl config use-context prod-eu
kubectl get pods -n shop -o wide                     # node, IP, restarts
kubectl get deploy,rs,svc,endpointslices -n shop
kubectl describe pod <pod> -n shop                   # events at the bottom: scheduling, pulls, probe failures, OOM
kubectl get events -n shop --sort-by=.lastTimestamp
kubectl logs <pod> -c app --previous                 # logs of the crashed previous container
kubectl logs -l app=checkout --tail=100 -f --max-log-requests=10
kubectl exec -it <pod> -c app -- sh
kubectl debug -it <pod> --image=busybox:1.36 --target=app   # ephemeral debug container sharing the process namespace
kubectl debug node/<node> -it --image=ubuntu                # a shell on the node (host at /host)
kubectl port-forward svc/checkout 8080:80 -n shop
kubectl top pods -n shop --containers                # needs metrics-server
kubectl explain deployment.spec.strategy.rollingUpdate
```

**Pod status → cause → first command:**

| Status / symptom | What it means | Look at |
|---|---|---|
| `Pending` | Not scheduled: insufficient requests, taint, affinity, PVC in another zone, quota | `describe pod` events (`FailedScheduling` says which filter) |
| `ContainerCreating` for minutes | Image pull, volume attach, or CNI IP assignment is slow/failing | `describe pod` events |
| `ImagePullBackOff` / `ErrImagePull` | Wrong name/tag, private registry without `imagePullSecrets`, rate limit, wrong architecture | Events; try the pull from the node |
| `CrashLoopBackOff` | The container starts and exits repeatedly; restarts back off exponentially up to 5 minutes | `logs --previous`; exit code in `describe` |
| `OOMKilled` (exit 137) | Hit the memory limit | Memory limit vs runtime heap settings; `kubectl top` |
| `Running` but `0/1 Ready` | Readiness probe failing; gets no traffic | Probe path/port, `describe` events |
| `Evicted` | Node pressure (memory, disk) | Node conditions, `ephemeral-storage` requests, logs filling disk |
| `Terminating` forever | A finalizer isn't removed, or the node is unreachable | `metadata.finalizers`; node status |
| `CreateContainerConfigError` | Referenced ConfigMap/Secret/key missing | Events |
| Service returns nothing | Selector doesn't match Pod labels, or no Ready Pods | `kubectl get endpointslices -l kubernetes.io/service-name=checkout` |

## Common interview questions

**"Walk me through what happens when you `kubectl apply` a Deployment."**
The API server authenticates, authorizes with RBAC, runs admission, validates and writes
to etcd. The Deployment controller (watching) creates a ReplicaSet; the ReplicaSet
controller creates Pods. The scheduler filters and scores nodes and binds each Pod. The
kubelet on that node pulls the image through the CRI, the CNI assigns an IP, containers
start, probes run. When readiness passes, the EndpointSlice controller adds the Pod and
kube-proxy on every node updates its rules.

**"A Pod is stuck in `Pending`. How do you debug it?"**
`kubectl describe pod` and read the `FailedScheduling` event: insufficient CPU/memory
(requests don't fit; check allocatable and whether the cluster autoscaler can add a
node), untolerated taints, affinity or topology constraints, a PVC bound to a volume in
another zone, or a namespace ResourceQuota.

**"A Pod is in `CrashLoopBackOff`."**
The main process keeps exiting. `kubectl logs --previous` for the last run's output;
`describe` for the exit code (137 = OOM kill, 1 = app error, 127 = bad command). Check
config/Secrets, a liveness probe that's too aggressive, or a missing startup probe.

**"Requests vs limits, and would you set CPU limits?"**
Requests are what the scheduler reserves and the weight under contention; limits are
cgroup ceilings. Memory over limit gets OOM-killed; CPU over limit gets throttled.
Setting memory limit = request is standard. CPU limits cause throttling and tail
latency, so latency-sensitive services often set only CPU requests; hard multi-tenant
isolation is the case for keeping them.

**"Liveness vs readiness probe?"**
Readiness decides whether a Pod receives traffic; failing removes it from endpoints.
Liveness decides whether to restart it. Liveness must not depend on downstream services,
or a dependency outage restarts the whole fleet.

**"How do you get zero-downtime deploys?"**
Rolling update with `maxUnavailable: 0` and a correct readiness probe; a PDB for
voluntary disruptions; graceful shutdown: `preStop` sleep so endpoint removal propagates,
then drain in-flight requests on SIGTERM within `terminationGracePeriodSeconds`;
backward-compatible schema changes so v1 and v2 can run side by side.

**"Deployment vs StatefulSet?"**
Deployment Pods are interchangeable with random names and shared or no storage.
StatefulSet Pods have stable ordinal names, stable DNS through a headless Service, their
own PVC each, and ordered rollout. Use StatefulSets for quorum systems and databases.

**"How are Secrets protected?"**
By default only base64 in etcd. Enable encryption at rest with KMS, restrict RBAC on
secrets and `pods/exec`, prefer an external secret manager synced in, and use workload
identity instead of static cloud keys.

**"What is the difference between Ingress and Gateway API?"**
Both route external HTTP to Services. Ingress is a minimal spec extended through
controller-specific annotations. Gateway API is the typed, role-oriented successor with
traffic splitting, header matching and multi-protocol routes in the standard.

**"Why does my HPA not scale up even though the service is slow?"**
It scales on the metric you gave it, relative to requests. A service bottlenecked on a
downstream dependency or on a lock does not show high CPU; scale on a better signal
(request concurrency, queue lag via KEDA) or fix the bottleneck. Also check `maxReplicas`
and whether new Pods are Pending for lack of nodes.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — | Explain cluster, node, Pod, Deployment and Service; run `kubectl get/describe/logs`; understand "desired state" |
| Junior (L3) | Software Engineer I / New grad | L3 | Write a Deployment + Service + ConfigMap, set requests/limits and probes, debug `CrashLoopBackOff`, `ImagePullBackOff` and `Pending` from events and logs, deploy with a given Helm chart |
| Mid (L4) | Software Engineer II | L4 | Explain the `kubectl apply` path end to end, probes and graceful shutdown, rolling-update parameters, QoS and eviction, HPA math; write a Helm chart; basic RBAC and NetworkPolicy |
| Senior (L5) | Senior Software Engineer | L5 | Design zero-downtime rollouts (endpoint race, PDBs, schema compatibility), make the CPU-limit call with evidence, set topology spread for zone failure, debug scheduling and networking (DNS `ndots`, kube-proxy, CNI), set team standards for Helm/Kustomize, Secrets and Pod security |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7 | Own the platform: cluster topology and multi-cluster strategy, control-plane and etcd scaling limits, upgrade cadence, node autoscaling and cost (Karpenter, bin-packing), policy-as-code and supply-chain admission, the Ingress→Gateway API migration, and when Kubernetes is *not* worth it |

## Interview checklist

- [ ] I can name every control-plane and node component and what fails when each one is down.
- [ ] I can narrate the `kubectl apply` → running, Ready, receiving traffic path, including the watches.
- [ ] I can choose between Deployment, StatefulSet, DaemonSet, Job and CronJob.
- [ ] I can explain requests vs limits, QoS classes, eviction, OOM kills and CPU throttling.
- [ ] I can explain scheduler filter/score/bind and use taints, affinity, topology spread and priority.
- [ ] I can explain `maxSurge`/`maxUnavailable` and what stalls a rollout, and roll back.
- [ ] I can distinguish startup, readiness and liveness probes and name the dependency-check anti-pattern.
- [ ] I can explain the endpoint-removal race and fix it with `preStop` and SIGTERM draining.
- [ ] I can compare Service types, explain CoreDNS and `ndots:5`, and Ingress vs Gateway API.
- [ ] I can write a default-deny NetworkPolicy and a least-privilege Role + RoleBinding.
- [ ] I know Secrets are base64, not encrypted, and how to actually protect them.
- [ ] I can explain HPA math and why requests must be right, and name VPA, KEDA, Cluster Autoscaler and Karpenter.
- [ ] I can structure a Helm chart, preview it with `helm template | kubectl diff`, upgrade atomically and roll back.
- [ ] I can map each Pod status in §12 to its cause and first debugging command.

Related: [Docker and Containerization](01_docker_and_containers.md) (what a container is),
[Platform and Infrastructure](../../interview-core/SystemDesign/building_blocks/16_platform_and_infra.md) (when Kubernetes is justified),
[Deployment Strategies](../CICD/03_deployment_strategies.md) and [GitOps and Argo CD](../CICD/04_gitops_and_argocd.md) (progressive
delivery and GitOps), [Service Mesh (Istio / Linkerd)](12_service_mesh.md) (mTLS and traffic policy between
Pods), [Observability and Monitoring](06_observability_and_monitoring.md) (monitoring a cluster),
[Operating Systems & Hardware Symbiosis](../../interview-core/CSFundamentals/01_operating_systems_deep_dive.md) §6 (cgroups under requests and limits).
