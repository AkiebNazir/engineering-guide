# Kubernetes and Orchestration

If Docker is how you run one container on one machine, **Kubernetes (K8s)** is how you run thousands of containers across hundreds of machines, while abstracting away the physical hardware.

## 1. The Core Primitives

Kubernetes is a declarative system. You don't say "start container A." You say "I desire 3 replicas of container A," and the K8s control plane constantly monitors reality and adjusts it to match your desire.

```arch
%% caption: Kubernetes resources layer on top of each other: Deployments manage ReplicaSets, which manage Pods, which are exposed by Services.
route straight
node dep "Deployment\\n(Desires 3 Replicas)" at 1,0 icon=package color=blue
node rs "ReplicaSet\\n(Maintains 3 Pods)" at 1,1 icon=layers color=amber
group pods "Nodes (Workers)" color=slate style=dashed
node p1 "Pod 1" at 0,2 in pods icon=app color=green
node p2 "Pod 2" at 1,2 in pods icon=app color=green
node p3 "Pod 3" at 2,2 in pods icon=app color=green

node svc "Service\\n(Stable IP & Load Balancing)" at 1,3 icon=lb color=slate

dep -> rs : "updates"
rs -> p1 : "creates"
rs -> p2 : "creates"
rs -> p3 : "creates"
svc -> p1 : "routes traffic"
svc -> p2 : "routes traffic"
svc -> p3 : "routes traffic"
```

- **Pod**: The smallest deployable unit. Usually contains one container, but can contain multiple tightly-coupled containers (like an app and a sidecar proxy) that share the same network namespace (`localhost`).
- **Deployment**: Manages rolling updates and scaling. It creates a ReplicaSet, which ensures the specified number of Pods are always running.
- **Service**: Pods die and get new IP addresses constantly. A Service gives a stable IP address and DNS name (`my-backend.default.svc.cluster.local`) that load-balances across the current set of healthy Pods.

## 2. Configuration and Secrets

Hardcoding environment variables is bad practice. K8s separates code from config:

- **ConfigMap**: Key-value pairs (or whole files) injected into Pods as environment variables or mounted as read-only files. Used for things like `DB_HOST` or `nginx.conf`.
- **Secret**: Exactly like a ConfigMap, but base64-encoded at rest (and ideally encrypted in etcd using KMS). Used for `DB_PASSWORD` or TLS certificates.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  LOG_LEVEL: "info"
---
apiVersion: apps/v1
kind: Deployment
# ...
    spec:
      containers:
      - name: my-app
        image: my-image:1.0
        envFrom:
        - configMapRef:
            name: app-config
```

## 3. Advanced Traffic and Scaling

- **Ingress**: A Service only exposes traffic *inside* the cluster (or via a raw cloud load balancer). An Ingress is an L7 HTTP router (often Nginx) that routes outside traffic (e.g., `api.example.com/v1/*`) to internal Services.
- **Horizontal Pod Autoscaler (HPA)**: Automatically scales the number of Pods up or down based on observed CPU utilization, memory, or custom metrics (like Kafka queue depth).

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: my-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## 4. RBAC (Role-Based Access Control)

K8s is entirely API-driven. RBAC determines who (or what) can call which API.

- **Role**: A list of permissions (e.g., "can get/list/watch Pods" in a specific namespace).
- **ServiceAccount**: An identity assigned to a Pod.
- **RoleBinding**: Connects the Role to the ServiceAccount.

If your Pod needs to talk to the K8s API (for example, a CI/CD worker pod that deploys other pods), it needs a ServiceAccount bound to a Role.

## 5. Helm: The Kubernetes Package Manager

Raw YAML files are hard to manage across environments (Dev, Staging, Prod) because you need to change values like replica counts and domains.

**Helm** packages YAML files into templates called **Charts**.

You write a `deployment.yaml` with Go-templates:
```yaml
replicas: {{ .Values.replicaCount }}
```

And a `values.yaml` file:
```yaml
replicaCount: 3
```

Then deploy it:
```bash
helm upgrade --install my-release ./my-chart -f values-prod.yaml
```
Helm is how almost all third-party software (Datadog, Prometheus, Redis) is installed onto a K8s cluster.

## 6. Daily CLI Cheat Sheet (`kubectl`)

```bash
# Set your context (which cluster you are talking to)
kubectl config get-contexts
kubectl config use-context prod-cluster

# View resources
kubectl get pods -n my-namespace
kubectl get svc,deploy,ingress

# Debugging
kubectl describe pod <pod-name>       # Shows why a pod is failing to schedule or start
kubectl logs -f <pod-name>            # Stream logs
kubectl exec -it <pod-name> -- /bin/sh # SSH into a pod
kubectl port-forward svc/my-db 5432:5432 # Forward a local port to a cluster service
```

## Common Interview/Troubleshooting Questions

**"My pod is stuck in `CrashLoopBackOff`."**
The container starts, but the main process exits immediately (either it crashed, or it ran a script that finished). Use `kubectl logs --previous <pod>` to see why the *last* incarnation of the pod died.

**"My pod is stuck in `Pending`."**
The Kubernetes Scheduler cannot find a Node to place the pod on. Use `kubectl describe pod <pod>`. Common reasons: Insufficient CPU/Memory on all nodes, or failing a Node Selector/Taint requirement.
