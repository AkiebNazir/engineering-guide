# Service Mesh (Istio / Linkerd)

In a microservices architecture you may have hundreds of services calling each other.
Every one of those calls needs encryption, a timeout, sensible retries, identity-based
access control and telemetry, and you want canary releases without code changes. A
**service mesh** provides those features in the infrastructure, uniformly, for every
service in every language. This chapter explains what a mesh is and when it is worth its
considerable cost, then goes through the mechanics: sidecar injection and traffic
capture, the control plane and xDS, automatic mutual TLS with SPIFFE identities,
authorization policies, traffic management, observability (including what a mesh
*cannot* do for tracing), sidecar-less designs (Istio ambient mode, Cilium), and the
failure modes that appear in production.

## Foundations — What is a service mesh, and what problem does it solve?

### The problem

Picture 200 services, written in Java, Go, Node.js and Python, owned by 30 teams. The
security team wants every call encrypted and authenticated. The SRE team wants every
call to have a timeout, bounded retries and latency metrics. A product team wants to send
5% of traffic to a new version of the recommendations service.

You *could* put a networking library in every codebase. But you would need one per
language, and 30 teams would have to upgrade it in lockstep every time a policy changes,
which never happens. Half the fleet would run last year's TLS settings.

### The idea

Move the network logic **out of the application process** into a proxy that sits next
to every service instance and handles all its traffic. The app makes a plain HTTP or
gRPC call to `http://reviews`; the proxy next to it adds mTLS, picks a healthy
destination, applies the timeout and retry policy, records metrics and forwards the
call to the proxy next to the destination, which checks authorization and hands the
request to the destination app. Neither app knows.

A mesh has two halves:

| Half | What it is | Examples |
|---|---|---|
| **Data plane** | the proxies that carry every request | Envoy (Istio, Consul), linkerd2-proxy (Linkerd), ztunnel (Istio ambient), eBPF + node Envoy (Cilium) |
| **Control plane** | the brain: watches the Kubernetes API for services, endpoints and policy objects, computes proxy configuration and pushes it; also runs the certificate authority | `istiod`, the Linkerd control plane, Consul servers |

```arch
%% caption: The control plane never touches requests. It pushes configuration and certificates to every proxy; the proxies carry the traffic.
grid 170x105
node k8s "Kubernetes API" at 0,0 icon=k8s sub="Services, endpoints, policies"
node cp "Control plane" at 1,0 icon=scheduler sub="istiod: config + CA"
node ops "Operators" at 2,0 icon=admin sub="VirtualService, AuthorizationPolicy"
group pa "frontend pod" color=blue icon=container
node pxa "Sidecar proxy" at 0,1 in pa icon=envoy
node appa "frontend app" at 0,2 in pa icon=app
group pb "reviews pod" color=green icon=container
node pxb "Sidecar proxy" at 2,1 in pb icon=envoy
node appb "reviews app" at 2,2 in pb icon=app
k8s -> cp : "watch"
ops -> cp : "apply"
cp ..> pxa:T : "xDS + certs"
cp ..> pxb:T
appa -> pxa : "plain HTTP"
pxa:R -> pxb:L : "mTLS"
pxb -> appb : "plain HTTP"
```

### An everyday analogy

Every employee in a large company sends mail through the mailroom rather than
delivering it personally. The mailroom (the proxy) checks the sender's badge,
seals the envelope, picks the fastest courier, retries if a delivery fails and logs
every package. Head office (the control plane) sends each mailroom the current rules and
fresh badges. Employees just write letters.

## 1. Sidecars: injection and traffic capture

In the classic model, the mesh adds a **sidecar** proxy container to every pod.

- **Injection**: a Kubernetes mutating admission webhook rewrites each new pod spec to
  add the proxy container, when the namespace is labelled
  (`kubectl label namespace shop istio-injection=enabled`, or `istio.io/rev=<revision>`
  for revision-based upgrades). Existing pods get the sidecar only when they are
  re-created (`kubectl rollout restart deployment -n shop`).
- **Capture**: an init container (`istio-init`) or, better, the **Istio CNI plugin**
  (which avoids giving pods the `NET_ADMIN` capability) installs iptables rules in the
  pod's network namespace. Outbound TCP from the app is redirected to Envoy on port
  **15001**, inbound TCP to Envoy on port **15006**. The app still thinks it connected
  directly to `reviews:9080`; Envoy recovers the original destination from the socket
  (`SO_ORIGINAL_DST`) and applies the routing rules for it.
- **Other ports** worth recognizing in an Istio sidecar: 15000 (Envoy admin, local
  only), 15020/15090 (merged Prometheus metrics), 15021 (health), 15008 (HBONE tunnel
  in ambient and newer sidecars).

**Startup and shutdown ordering** caused years of bugs: the app starts before the
proxy is ready and its first outbound calls fail, or at shutdown the proxy exits before
the app has drained. Kubernetes **native sidecar containers** (init containers with
`restartPolicy: Always`; on by default since 1.29 and GA in 1.33) start the proxy before
app containers, keep it running for the pod's lifetime and stop it after them, and let
Jobs complete while a sidecar runs. Istio supports this mode; on older setups the
workaround is `holdApplicationUntilProxyStarts: true`.

## 2. The control plane and xDS

`istiod` watches Kubernetes Services, EndpointSlices, pods and Istio's custom resources,
translates them into Envoy configuration and pushes it to every proxy over the **xDS**
gRPC APIs (listeners, routes, clusters, endpoints, secrets; see
[Web Servers and Proxies](09_web_servers_and_proxies.md) §6). When a pod becomes ready, the new endpoint reaches
every interested proxy within seconds without restarts.

History worth knowing because interviews and old blog posts still mention it: early
Istio had separate components (Pilot for config, **Citadel** for certificates, Galley,
Mixer for telemetry and policy). Since Istio 1.5 (2020) they are merged into a single
binary, **istiod**, and Mixer was removed; telemetry is generated in the proxies.

**Scaling concern**: by default every sidecar receives configuration for every service
in the mesh. With thousands of services that means large configs, high memory per proxy
and slow pushes. The `Sidecar` resource (or discovery selectors) limits what each proxy
learns to the services it actually calls:

```yaml
apiVersion: networking.istio.io/v1
kind: Sidecar
metadata:
  name: default
  namespace: shop
spec:
  egress:
    - hosts:
        - "./*"              # services in this namespace
        - "istio-system/*"
        - "payments/*"       # plus the one other namespace we call
```

## 3. Mutual TLS and workload identity

Regular TLS proves the *server's* identity to the client. **Mutual TLS** (mTLS) also
proves the *client's* identity to the server, so both ends know exactly which workload
is on the other side, and everything in between is encrypted.

How a mesh makes that automatic:

1. **Identity comes from the Kubernetes service account.** Each workload gets a
   **SPIFFE ID** of the form `spiffe://cluster.local/ns/shop/sa/frontend` (trust
   domain / namespace / service account). SPIFFE is a CNCF standard for workload
   identity; SPIRE is its reference implementation, and meshes can plug into it.
2. **Certificates are issued and rotated automatically.** The Istio agent in each proxy
   generates a private key (the key never leaves the pod), sends a certificate signing
   request to istiod along with the pod's service account token as proof, and receives
   a short-lived X.509 certificate (24 h by default in Istio) carrying the SPIFFE ID in
   its SAN. Envoy receives it over SDS and it is rotated well before expiry with no
   restart. The mesh CA can be rooted in your own PKI (cert-manager, Vault PKI, a cloud
   CA) instead of istiod's self-signed root.
3. **Every hop is authenticated both ways.** The client-side proxy checks that the
   server's certificate carries the expected identity; the server-side proxy extracts
   the client's SPIFFE ID and uses it for authorization.

Istio starts in **PERMISSIVE** mode, where sidecars accept both mTLS and plain text so
you can migrate workloads gradually. Production meshes should end in **STRICT**:

```yaml
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system   # root namespace = mesh-wide
spec:
  mtls:
    mode: STRICT
```

### Authorization by identity

With verified identities, access rules can be written in terms of *who is calling*
rather than IP addresses, which change every time a pod restarts:

```yaml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: checkout-allow-frontend
  namespace: shop
spec:
  selector:
    matchLabels:
      app: checkout
  action: ALLOW
  rules:
    - from:
        - source:
            principals: ["cluster.local/ns/shop/sa/frontend"]
      to:
        - operation:
            methods: ["POST"]
            paths: ["/api/checkout/*"]
```

Once any `ALLOW` policy selects a workload, requests that match no rule are denied
(Envoy returns `403` with `RBAC: access denied`). A namespace-wide empty `ALLOW`-nothing
policy gives default-deny, and then each service opens exactly the callers it needs.
This is the network half of **zero trust**: the network location of a request is never
trusted, only its cryptographic identity. `AuthorizationPolicy` can also validate end
user JWTs (`RequestAuthentication`), which complements, not replaces, the application's
own authorization ([Cross-Cutting Concerns](../../data-and-apis/API/Fundamentals/03_cross_cutting_concerns.md)).

The live flow below follows one call through both sidecars, then shows a denied caller
and a failing upstream being retried and ejected.

<div class="lab" data-viz="flow-mesh-mtls"></div>

## 4. Traffic management

Routing rules live in Istio's `VirtualService` (what to do with requests for a host)
and `DestinationRule` (policies for the destination: subsets, load balancing,
connection pools, outlier detection). The owner's original example used
`networking.istio.io/v1alpha3`; these APIs have been `v1` since Istio 1.22 (2024), and
the older versions are still served for compatibility.

```yaml
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: reviews
  namespace: shop
spec:
  host: reviews
  subsets:
    - name: v1
      labels: { version: v1 }
    - name: v2
      labels: { version: v2 }
  trafficPolicy:
    connectionPool:
      http:
        http1MaxPendingRequests: 100
        maxRequestsPerConnection: 0
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: reviews
  namespace: shop
spec:
  hosts:
    - reviews
  http:
    - match:
        - headers:
            x-beta-tester: { exact: "true" }
      route:
        - destination: { host: reviews, subset: v2 }
    - route:
        - destination: { host: reviews, subset: v1 }
          weight: 90
        - destination: { host: reviews, subset: v2 }
          weight: 10
      timeout: 2s
      retries:
        attempts: 2
        perTryTimeout: 500ms
        retryOn: "connect-failure,refused-stream,unavailable,503"
```

What this does: beta testers always get v2; everyone else is split 90/10 by weight; the
whole call has a 2 s budget with at most two retries of 500 ms each; endpoints returning
5 consecutive 5xx errors are ejected for 30 s (growing on repeat), never more than half
the pool at once.

Other traffic features: **fault injection** (add a delay or abort a percentage of
requests to test resilience; see [Resilience: Chaos Engineering](../TestingAndQuality/06_chaos_engineering.md)),
**mirroring** (copy live traffic to a new version and discard its responses), locality
aware load balancing and failover between zones and regions, and **egress control**
(`ServiceEntry` for external hosts, an egress gateway to force outbound traffic through
known IPs). Progressive delivery tools (Argo Rollouts, Flagger) drive these weights
automatically based on metrics ([Deployment Strategies](../CICD/03_deployment_strategies.md)).

The **Kubernetes Gateway API** now covers much of this in a vendor-neutral way: under
the GAMMA initiative (stable for mesh in Gateway API v1.1, 2024) an `HTTPRoute` whose
`parentRef` is a Service configures east-west mesh routing in Istio, Linkerd and
Cilium alike. New configurations increasingly use it instead of mesh-specific CRDs.

**Retries deserve care.** Istio retries twice by default on connection failures and
some 503s. Retries multiply load at every layer: with three layers of services each
retrying twice, one failing leaf call can become 3 × 3 × 3 = 27 attempts, exactly when
the leaf is overloaded. Retry at one layer, keep budgets small, and only retry
idempotent operations; a mesh-level retry of `POST /charge` is as dangerous as an
application-level one ([Application Resilience Patterns](../../interview-core/SystemDesign/building_blocks/12_application_resilience_patterns.md)).

## 5. Observability: what you get free, and what you do not

Because every request passes through a proxy, the mesh can emit without code changes:

- **Metrics** per source, destination, response code and protocol, i.e. the RED
  signals (rate, errors, duration) for every service-to-service edge. Istio exposes
  `istio_requests_total` and `istio_request_duration_milliseconds` for Prometheus, and
  tools like Kiali draw the live service graph from them.
- **Access logs** for every hop.
- **Spans**: each proxy reports a span for the request it handled to a tracing backend
  (OpenTelemetry collector, Jaeger, Zipkin).

**Correction to a common claim** (and to this file's earlier text): a mesh does *not*
give you complete distributed traces with zero code changes. The proxy creates trace
context on the inbound request, but it cannot know which *outbound* call your
application makes in response to which inbound request. The application must copy the
trace headers (`traceparent`/`tracestate` for W3C Trace Context, or the `x-b3-*` headers)
from the incoming request to its outgoing requests. Without that, every hop appears as a
separate, disconnected trace. OpenTelemetry's auto-instrumentation libraries do this
propagation for most frameworks, so the practical recipe is mesh for edge metrics plus
OpenTelemetry in the app for propagation and in-process spans
([Observability and Monitoring](06_observability_and_monitoring.md)).

## 6. Beyond sidecars: ambient mode, Cilium and Linkerd

Sidecars have real costs: a proxy in every pod (memory and CPU multiplied by pod
count), two extra proxy hops per call, restarts of every pod to upgrade the proxy, and
the lifecycle ordering issues from §1. The industry answer since 2022 has been to move
the data plane to the node.

**Istio ambient mode** (GA in Istio 1.24, November 2024) splits the data plane in two:

- **ztunnel**, a small per-node proxy written in Rust (a DaemonSet), handles L4: mTLS,
  identity, L4 authorization and telemetry. Traffic between nodes travels in **HBONE**
  tunnels (HTTP CONNECT over mTLS, port 15008). Pods need no sidecar and no restart to
  join: label the namespace `istio.io/dataplane-mode=ambient`.
- **Waypoint proxies**, Envoy deployments you create per namespace or service account
  only where you need L7 features (HTTP routing, retries, L7 authorization, fault
  injection). Services that only need mTLS never pay for L7 processing.

```arch
%% caption: Ambient mode: every pod gets mTLS from its node's ztunnel; only traffic that needs L7 policy detours through a waypoint proxy.
grid 170x105
group n1 "Node 1" color=blue icon=server
node a "frontend pod" at 0,0 in n1 icon=app sub="no sidecar"
node z1 "ztunnel" at 0,1 in n1 icon=proxy sub="L4: mTLS, identity"
group wp "Namespace shop" color=amber icon=gateway
node w "Waypoint proxy" at 1,1 in wp icon=envoy sub="L7: routes, retries, authz"
group n2 "Node 2" color=green icon=server
node z2 "ztunnel" at 2,1 in n2 icon=proxy sub="L4: mTLS, identity"
node b "reviews pod" at 2,0 in n2 icon=app sub="no sidecar"
a -> z1 : "captured"
z1 -> w : "HBONE"
w -> z2 : "HBONE"
z2 -> b
z1 ..> z2 : "L4-only path"
```

**Cilium Service Mesh** builds on the Cilium CNI: eBPF programs in the kernel handle L3/L4
load balancing and network policy, a per-node Envoy handles L7 when a policy needs it, and
encryption comes from WireGuard or IPsec between nodes (or a SPIFFE-based mutual
authentication feature). Attractive if you already run Cilium as the CNI.

**Linkerd** keeps sidecars but makes them very small: `linkerd2-proxy` is a purpose-built
Rust proxy, not Envoy, with mTLS on by default and very little configuration. It is a
CNCF graduated project; since 2024 open-source users get "edge" releases, while stable
release builds come from Buoyant's commercial distribution.

| | Istio sidecar | Istio ambient | Linkerd | Cilium |
|---|---|---|---|---|
| Data plane | Envoy per pod | ztunnel per node + optional Envoy waypoints | Rust micro-proxy per pod | eBPF + Envoy per node |
| mTLS | yes (SPIFFE) | yes (SPIFFE, in ztunnel) | yes, on by default | WireGuard/IPsec or mutual auth |
| L7 features | richest | via waypoints | core set (retries, timeouts, splits, authz) | via Envoy and CRDs |
| Resource overhead | highest | low for L4, pay for L7 where used | low | low |
| Operational complexity | high | medium-high | lower | medium, tied to the CNI |

Other options: **Consul service mesh** (Envoy, strong for VMs plus Kubernetes and
multi-datacenter), **Kuma / Kong Mesh**, and cloud-managed meshes (Google Cloud Service
Mesh, AWS VPC Lattice, which is a managed service-networking layer rather than a
sidecar mesh). **Proxyless gRPC** is another design: gRPC libraries speak xDS directly
to the control plane, getting routing and mTLS without any proxy, for gRPC traffic only.

## 7. Costs, failure modes and when to adopt

**Costs**, with rough magnitudes (≈; they depend heavily on configuration, payload size
and version):

- **Latency**: each proxy adds on the order of a fraction of a millisecond at the
  median, more at p99; a sidecar-to-sidecar hop crosses two proxies. Irrelevant for a
  100 ms API, significant for a sub-millisecond cache path.
- **Resources**: a sidecar is typically tens of MB of memory and a slice of a CPU core
  under load; multiplied by thousands of pods it becomes a real line in the cloud bill.
  Ambient and node-level designs exist largely because of this.
- **Complexity**: a new control plane to upgrade (canary upgrades with revisions), CRDs
  to learn, and a new place for failures to hide.

**Failure modes you will meet:**

| Symptom | Likely cause |
|---|---|
| `503 UF` / `upstream connect error or disconnect/reset before headers` | the destination is down, or its sidecar rejected mTLS (one side STRICT, the other plain text) |
| `403 RBAC: access denied` | an `AuthorizationPolicy` does not allow this caller's identity or path |
| `503 NR` (no route) | no route matches: missing VirtualService host, wrong port name/protocol, or the proxy's `Sidecar` scope does not include the destination |
| app fails its first calls at startup | the app started before the proxy was ready; use native sidecars or `holdApplicationUntilProxyStarts` |
| a Job pod never completes | the sidecar keeps running after the job; native sidecars fix this |
| latency spikes during pod churn | slow config pushes in a large mesh; scope config with `Sidecar` or discovery selectors |
| mesh-wide outage after an upgrade or a bad policy | control-plane changes are global: roll out mesh upgrades by revision and test policies in a canary namespace |
| traffic works in-mesh but not to external APIs | `outboundTrafficPolicy: REGISTRY_ONLY` without a `ServiceEntry` |

Debugging tools: `istioctl analyze` (lints configuration), `istioctl proxy-status`
(is every proxy in sync with istiod?), `istioctl proxy-config routes|clusters|endpoints
<pod>` (what this proxy actually believes), Envoy response flags in access logs (`UF`,
`UH`, `NR`, `URX`, `UO`), and the Kiali service graph.

**When a mesh is worth it**: many services in several languages, a hard requirement
for encryption and service identity in transit (compliance, zero trust), a need for
traffic splitting and consistent resilience policy, and a platform team to own it.

**When it is not**: a handful of services, one language (a shared library or gRPC
interceptors do the job), no one to operate it, or latency budgets that cannot absorb
extra hops. Kubernetes `NetworkPolicy` plus TLS in the app may be enough. Adopt
incrementally: mTLS in PERMISSIVE mode, then STRICT, then authorization, then traffic
management, one namespace at a time.

## Common interview questions

**What is a service mesh?**
A dedicated infrastructure layer for service-to-service communication: a data plane of
proxies next to (or on the node of) every workload, and a control plane that configures
them and issues identities. It provides mTLS, authorization, retries, timeouts, traffic
splitting and telemetry without application code changes.

**How does a sidecar intercept traffic without the app knowing?**
A webhook injects the proxy container; iptables rules (from an init container or the
CNI plugin) in the pod's network namespace redirect outbound and inbound TCP to the
proxy's ports; the proxy recovers the original destination and applies routing.

**How does mTLS work in Istio, and where does identity come from?**
Each workload's identity is its Kubernetes service account, expressed as a SPIFFE ID.
The proxy's agent creates a key and a CSR, istiod signs a short-lived certificate after
validating the pod's service account token, Envoy gets it via SDS, and both proxies
verify each other's certificate on every connection. PeerAuthentication STRICT rejects
plain text.

**Does a mesh give you distributed tracing for free?**
Partly. Proxies emit spans and metrics, but the application must propagate trace
headers from inbound to outbound requests, or traces fragment. Use OpenTelemetry
instrumentation for that.

**How would you do a canary with a mesh?**
Two subsets by version label in a DestinationRule, and a VirtualService (or Gateway API
HTTPRoute) with weights 95/5, increased step by step while watching error rate and
latency, ideally automated by Argo Rollouts or Flagger with automatic rollback.

**What are the costs of a sidecar mesh, and how does ambient mode address them?**
Per-pod proxy memory and CPU, two extra hops, pod restarts for upgrades and startup
ordering bugs. Ambient mode moves L4 mTLS into a per-node ztunnel and only adds Envoy
waypoints where L7 policy is needed, so most traffic pays less and apps need no restart
to join.

**Mesh retries and application retries, which should you use?**
Retry at one layer, with budgets and only for idempotent operations. Stacked retries
multiply load during outages, and a mesh retry of a non-idempotent call duplicates side
effects just as an application retry would.

**When would you not adopt a service mesh?**
Few services, one language, no platform team, or tight latency budgets. Use libraries,
NetworkPolicy and TLS instead, and revisit when the fleet or compliance needs grow.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — | What a proxy is, what mTLS means, and the sidecar idea: network features outside the app. |
| Junior (L3) | Software Engineer I | L3 | Their service runs with a sidecar; read mesh metrics and access logs; know that 403 RBAC and 503 errors can come from mesh policy; propagate trace headers. |
| Mid (L4) | Software Engineer II | L4 | Write VirtualService/DestinationRule or HTTPRoute for timeouts, retries and weighted canaries; write AuthorizationPolicies by service account; debug with `istioctl proxy-config` and response flags. |
| Senior (L5) | Senior Software Engineer | L5 | Explain injection, iptables capture, xDS, SPIFFE certificates and STRICT mTLS; design retry budgets and outlier detection; plan an incremental mesh rollout and diagnose startup ordering and config-scale problems. |
| Staff+ (L6+) | Staff / Principal Engineer | L6+ | Decide whether and which mesh to adopt (sidecar vs ambient vs Linkerd vs Cilium vs libraries) on cost, risk and team capacity; own zero-trust identity and CA hierarchy, multi-cluster topology, and safe control-plane upgrades. |

## Interview checklist

- [ ] I can explain data plane vs control plane and draw where requests and config flow.
- [ ] I can describe sidecar injection, iptables capture and the ports involved.
- [ ] I can explain why native sidecar containers fixed startup and Job-completion bugs.
- [ ] I can explain mesh mTLS end to end: SPIFFE ID, CSR, SDS, rotation, PERMISSIVE vs STRICT.
- [ ] I can write an AuthorizationPolicy that allows one service account and explain default deny.
- [ ] I can configure a weighted canary, timeouts, retries and outlier detection.
- [ ] I can explain why the app must still propagate trace headers.
- [ ] I can compare Istio sidecar, Istio ambient (ztunnel, waypoints), Linkerd and Cilium.
- [ ] I can list the costs of a mesh and the common failure signatures (UF, NR, RBAC 403).
- [ ] I can argue when not to adopt a mesh.

Related: [Platform and Infrastructure](../../interview-core/SystemDesign/building_blocks/16_platform_and_infra.md) (mesh and eBPF at the
architecture level), [Web Servers and Proxies](09_web_servers_and_proxies.md) (Envoy internals and the Gateway
API), [Secret Management](11_secret_management.md) (workload identity), [Kubernetes and Orchestration](02_kubernetes_and_helm.md),
[Observability and Monitoring](06_observability_and_monitoring.md), [Deployment Strategies](../CICD/03_deployment_strategies.md) (canaries).
