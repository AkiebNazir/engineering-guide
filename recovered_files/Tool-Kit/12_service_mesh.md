# Service Mesh (Istio / Linkerd)

In a microservices architecture, you might have hundreds of services talking to each other. How do you ensure that:
1. Traffic between them is encrypted (mTLS)?
2. Service A retries exactly once if Service B fails?
3. Service C splits 10% of traffic to a new "Canary" release of Service D?
4. You get telemetry (latency, errors) for every hop?

You *could* import a "retry/mTLS/telemetry" library into every single codebase. But what if half your services are in Java, a quarter in Node, and a quarter in Go? Keeping those libraries synchronized is impossible.

## 1. The Sidecar Pattern

A Service Mesh solves this at the infrastructure layer, completely invisibly to the application code.

It injects a **Sidecar Proxy** (usually Envoy or Linkerd-proxy) into every single Pod.

```arch
%% caption: The application only talks to localhost; the Sidecar Proxy intercepts the traffic, applies policies, and forwards it to the destination Sidecar.
group poda "Pod A" color=slate style=dashed
node appa "Service A" at 0,1 in poda icon=app color=blue
node proxa "Envoy Proxy" at 2,1 in poda icon=proxy color=amber

group podb "Pod B" color=slate style=dashed
node proxb "Envoy Proxy" at 2,3 in podb icon=proxy color=amber
node appb "Service B" at 0,3 in podb icon=app color=green

appa -> proxa : "HTTP (local)"
proxa <-> proxb : "mTLS + Retries"
proxb -> appb : "HTTP (local)"
```

Service A thinks it is making an unencrypted HTTP call to `http://service-b`. But the network rules force that packet into Service A's sidecar proxy. The proxy encrypts it, sends it over the network to Service B's sidecar proxy, which decrypts it and hands it to Service B as a plain HTTP request.

## 2. Istio Core Features

Istio is the most popular service mesh for Kubernetes.

### Traffic Management (Virtual Services & Destination Rules)
You can route traffic based on headers, cookies, or weights without touching the deployment.
```yaml
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: reviews-route
spec:
  hosts:
  - reviews
  http:
  - route:
    - destination:
        host: reviews
        subset: v1
      weight: 90
    - destination:
        host: reviews
        subset: v2
      weight: 10
```

### Security (mTLS and Authorization)
Istio includes a Certificate Authority (Citadel) that automatically provisions and rotates TLS certificates for every sidecar. You can write policies stating "Only the Frontend service is allowed to communicate with the Checkout service".

### Observability
Because the Envoy sidecars see every byte of L7 (HTTP/gRPC) traffic flowing through the cluster, Istio can automatically generate Prometheus metrics for the RED signals (Rate, Errors, Duration) and automatically inject OpenTelemetry trace headers, giving you a complete dashboard of your cluster's health without writing a single line of observability code in your apps.

## 3. The Trade-offs

A service mesh is heavy.
- **Latency**: Every network hop now passes through two proxies. Envoy is fast (sub-millisecond), but it adds up.
- **Resource Cost**: Running an Envoy proxy in *every single pod* can consume a massive amount of RAM across a large cluster.
- **Complexity**: Debugging network issues now involves deciphering complex Envoy proxy logs and Istio routing rules.

Only adopt a Service Mesh when the pain of managing cross-language mTLS and traffic routing outweighs the immense operational complexity of running Istio. (Alternatively, newer architectures like Cilium use eBPF in the kernel to provide service mesh features without sidecars).
