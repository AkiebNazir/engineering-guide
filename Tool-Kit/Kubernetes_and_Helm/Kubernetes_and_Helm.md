# Kubernetes and Helm

Welcome to the ultimate guide on Kubernetes and Helm! If Docker is how you run a single container on your laptop, Kubernetes is how you run thousands of containers across hundreds of servers in production. Helm is how you package and deploy those applications effortlessly.

## Interactive Examples
We provide several practical examples in the [`examples`](./examples) directory to help you learn by doing:
- [01 Basic Pod and Deployment](./examples/01_basic_pod_and_deployment)
- [02 Intermediate Services](./examples/02_intermediate_services)
- [03 Intermediate ConfigMap and Secrets](./examples/03_intermediate_configmap_secrets)
- [04 Advanced StatefulSet and PV](./examples/04_advanced_statefulset_pv)
- [05 Advanced Helm Chart](./examples/05_advanced_helm_chart)

---

## 1. Introduction to Kubernetes

### The Problem: Managing Containers at Scale
Imagine you have a Dockerized web application. You run it on a server. Tomorrow, your app goes viral. One container isn't enough; you need 50. 
*   How do you distribute those 50 containers across 5 different servers?
*   What happens if one server crashes? Who restarts the containers that were on it?
*   How do the containers talk to each other across different servers?
*   How do you update the application to v2.0 without bringing the entire system down?

Doing this manually (or with simple scripts) is an operational nightmare. You need an **Orchestrator**.

### The Solution: Kubernetes (K8s)
Kubernetes (often abbreviated as **K8s**, because there are 8 letters between K and s) is an open-source container orchestration platform originally developed by Google. 

Kubernetes is like the conductor of an orchestra. It doesn't play the instruments (run the containers), but it tells everyone what to do, when to start, and ensures they are all playing in harmony.

---

## 2. Kubernetes Architecture

A Kubernetes cluster consists of two main components: the **Control Plane** (the brains) and the **Worker Nodes** (the muscle).

```arch
group cp "Control Plane Master Node" color=blue
node api "API Server" at 1,0 in cp icon=server
node etcd "etcd" at 0,0 in cp icon=etcd sub="Key-Value Store"
node sched "Scheduler" at 2,0 in cp icon=cron
node ccm "Controller Manager" at 3,0 in cp icon=process

group w1 "Worker Node 1" color=slate style=dashed
node k1 "Kubelet" at 0.5,1 in w1 icon=process
node kp1 "Kube-Proxy" at 0.5,2 in w1 icon=proxy
node pod1 "Pod App" at 0,3 in w1 icon=app
node pod2 "Pod App" at 1,3 in w1 icon=app

group w2 "Worker Node 2" color=slate style=dashed
node k2 "Kubelet" at 2.5,1 in w2 icon=process
node kp2 "Kube-Proxy" at 2.5,2 in w2 icon=proxy
node pod3 "Pod App" at 2.5,3 in w2 icon=app

api <..> etcd
api <..> sched
api <..> ccm

api -- k1 : "Commands"
api -- k2 : "Commands"
```

### The Control Plane
The Control Plane makes global decisions about the cluster (e.g., scheduling) and detects/responds to cluster events.
*   **kube-apiserver:** The frontend of the control plane. Every interaction with the cluster (via CLI or UI) goes through the API server.
*   **etcd:** A highly available, distributed key-value store. It is the "source of truth" and holds all the cluster data and state. If etcd dies, your cluster forgets everything.
*   **kube-scheduler:** Watches for newly created Pods that have no Node assigned, and selects a Node for them to run on based on resource requirements (CPU/RAM).
*   **kube-controller-manager:** Runs controller processes. For example, if you ask for 3 replicas of an app and one dies, the controller notices the current state (2) doesn't match the desired state (3) and spins up a new one.

### Worker Nodes
Worker nodes host the application workloads.
*   **kubelet:** An agent that runs on each node. It ensures that containers are running in a Pod by communicating with the container runtime (like containerd).
*   **kube-proxy:** Maintains network rules on nodes. These rules allow network communication to your Pods from network sessions inside or outside of your cluster.
*   **Container Runtime:** The software that actually runs the containers (e.g., Docker, containerd, CRI-O).

---

## 3. Core Kubernetes Objects

Kubernetes has a declarative API. You write YAML files describing *what* you want, and submit them to the API server. K8s will continuously work to make reality match your YAML.

### Pods: The Smallest Unit
In Docker, the smallest unit is a container. In Kubernetes, it's a **Pod**. A Pod is a wrapper around one or more containers that share the same network namespace (they can talk to each other via `localhost`) and storage volumes.

*Why not just run containers directly?* Because sometimes two containers are tightly coupled and must run on the exact same machine (e.g., a web server container and a log-forwarder container).

```yaml
# pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: my-nginx-pod
  labels:
    app: web
spec:
  containers:
  - name: nginx
    image: nginx:latest
    ports:
    - containerPort: 80
```
**Command:** `kubectl apply -f pod.yaml`

### Deployments: Managing Pods
You rarely create Pods directly. Pods are mortal—if a node dies, the Pod dies with it and is *not* resurrected. 
A **Deployment** provides declarative updates for Pods. You tell a Deployment "I want 3 replicas of this Pod," and it ensures 3 are always running.

> [!TIP] Check out the [01 Basic Pod and Deployment](./examples/01_basic_pod_and_deployment) example to see Deployments in action.

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web
  template: # This is the Pod template
    metadata:
      labels:
        app: web
    spec:
      containers:
      - name: nginx
        image: nginx:1.14.2
        ports:
        - containerPort: 80
```

### Services: Networking and Discovery
Pods are ephemeral. Their IP addresses change all the time (when they crash and are recreated). If your Frontend Pods need to talk to your Backend Pods, they can't rely on IP addresses.

A **Service** provides a stable, permanent IP address and DNS name for a set of Pods, acting as a load balancer. It uses **Labels** and **Selectors** to know which Pods to route traffic to.

> [!TIP] Learn how to expose your apps in the [02 Intermediate Services](./examples/02_intermediate_services) example.

```arch
group svc "Service: backend-svc" color=blue
node sip "IP: 10.96.0.1" at 1,0 in svc icon=network sub="Selector: app=backend"

group pods "Pods in Cluster" color=slate style=dashed
node p1 "Pod" at 0,1 in pods icon=app sub="Label: app=backend"
node p2 "Pod" at 1,1 in pods icon=app sub="Label: app=backend"
node p3 "Pod" at 2,1 in pods icon=app sub="Label: app=frontend"

sip -> p1 : "Routes traffic"
sip -> p2 : "Routes traffic"
sip ..> p3 : "Ignored"
```

There are three main types of Services:
1.  **ClusterIP (Default):** Exposes the service on a cluster-internal IP. Only reachable from *inside* the cluster.
2.  **NodePort:** Exposes the service on each Node's IP at a static port (30000-32767). Reachable from outside the cluster.
3.  **LoadBalancer:** Provisions an external Load Balancer from your cloud provider (AWS, GCP, Azure) and assigns a public IP to the service.

### ConfigMaps and Secrets: Configuration Management
You shouldn't hardcode configurations (like database URLs) or secrets (like passwords) into your container images. 
*   **ConfigMap:** Stores non-confidential data in key-value pairs.
*   **Secret:** Stores confidential data (passwords, OAuth tokens, SSH keys). It is base64 encoded.

> [!TIP] See how to inject configuration in the [03 Intermediate ConfigMap and Secrets](./examples/03_intermediate_configmap_secrets) example.

You can inject these into your Pods as environment variables or mount them as files in a volume.

---

## 4. Advanced Concepts

### Ingress
A LoadBalancer service gives you one public IP per service. If you have 10 microservices, paying for 10 cloud load balancers gets expensive. 
An **Ingress** sits in front of your cluster and acts as a smart router (often backed by NGINX or HAProxy). It routes HTTP/HTTPS traffic to different services based on the URL path or hostname.

*   `api.myapp.com/v1/*` -> Routes to `Service A`
*   `myapp.com/blog/*` -> Routes to `Service B`

### StatefulSets
Deployments are for *stateless* applications (like web servers) where every pod is identical and replaceable. 
**StatefulSets** are used for *stateful* applications (like Databases: PostgreSQL, MongoDB, Kafka). They provide:
*   Stable, unique network identifiers (e.g., `mysql-0`, `mysql-1`).
*   Stable, persistent storage (if `mysql-0` dies and restarts on another node, it re-attaches to the exact same storage volume).
*   Ordered, graceful deployment and scaling.

> [!TIP] Deploy a stateful workload with persistence in the [04 Advanced StatefulSet and PV](./examples/04_advanced_statefulset_pv) example.

### DaemonSets
A **DaemonSet** ensures that *all* (or some) Worker Nodes run exactly one copy of a specific Pod. 
**Use cases:** Running a logging agent (Fluentd), a monitoring daemon (Prometheus Node Exporter), or a networking agent on every single machine in the cluster.

---


## 5. Essential `kubectl` Commands

The `kubectl` command-line tool is your primary interface for interacting with a Kubernetes cluster. Mastering these commands will save you countless hours of debugging.

### Getting Information (The `get` command)
*   `kubectl get pods`: List all pods in the current namespace.
*   `kubectl get pods -n <namespace>`: List pods in a specific namespace.
*   `kubectl get pods -A`: List pods across *all* namespaces.
*   `kubectl get svc`: List all services.
*   `kubectl get nodes`: Check the status of your worker nodes (Ready / NotReady).
*   `kubectl get all`: Lists most resources (Pods, Services, DaemonSets, Deployments, ReplicaSets) in the current namespace.

### Deep Dive and Debugging (The `describe` and `logs` commands)
*   `kubectl describe pod <pod-name>`: Shows incredibly detailed information about a pod, including its events. **Crucial for debugging** why a pod is stuck in `Pending` or `CrashLoopBackOff`.
*   `kubectl logs <pod-name>`: View the stdout/stderr logs of the container running in the pod.
*   `kubectl logs <pod-name> -f`: Stream (tail) the logs live.
*   `kubectl logs <pod-name> -c <container-name>`: View logs for a specific container (if the pod has multiple containers, like an InitContainer or a sidecar).
*   `kubectl exec -it <pod-name> -- /bin/sh`: Open an interactive shell *inside* the running pod. Great for poking around the filesystem or testing network connectivity.

### Modifying and Applying
*   `kubectl apply -f deployment.yaml`: Create or update resources declaratively based on a YAML file. (Always prefer this over imperative commands like `kubectl create`).
*   `kubectl delete pod <pod-name>`: Forcibly kill a pod. (Remember, if it's managed by a Deployment, it will immediately respawn).
*   `kubectl scale deployment <deployment-name> --replicas=5`: Imperatively scale a deployment up or down.
*   `kubectl port-forward svc/<service-name> 8080:80`: Forwards your laptop's `localhost:8080` to port `80` on the service inside the cluster. Perfect for testing internal APIs without exposing them to the internet.

### Troubleshooting Cheat Code
If a Pod is failing, follow this exact order of operations:
1.  `kubectl get pods` (Is the status `CrashLoopBackOff`, `ImagePullBackOff`, or `Pending`?)
2.  `kubectl describe pod <pod-name>` (Scroll to the bottom "Events" section to see exactly *why* the API server is unhappy. Usually it's a typo in the image name or insufficient CPU limits).
3.  `kubectl logs <pod-name>` (If the pod booted but crashed, the app itself threw an error. Look at the stack trace here).

---
## 6. Introduction to Helm (The Package Manager)

### The Problem with raw YAML
Imagine deploying a complex application like a WordPress site. You need a Deployment for WordPress, a StatefulSet for MySQL, a Service for both, a ConfigMap, a Secret, and an Ingress. That's 6 different YAML files.
If you want to deploy this app in `dev`, `staging`, and `production`, you have to copy-paste all those YAML files and manually change the names, replica counts, and image tags. 

### The Solution: Helm
Helm is the package manager for Kubernetes (like `apt` for Ubuntu or `npm` for Node.js). It packages all those YAML files into a single logical unit called a **Chart**.

Instead of hardcoding values in your YAML, Helm uses **Templates** (written in Go template syntax) and a `values.yaml` file to inject variables dynamically.

> [!TIP] Package your apps using Helm in the [05 Advanced Helm Chart](./examples/05_advanced_helm_chart) example.

### Helm Architecture
```arch
node dev "Developer" at 0,0.5 icon=developer
node vals "values.yaml" at 1,0 icon=file sub="Variables"
node tmpl "templates/deployment.yaml" at 1,1 icon=file
node helm "Helm CLI" at 2,0.5 icon=cli
node k8s "K8s API Server" at 3,0.5 icon=server

dev -> vals : "Edits"
dev -> tmpl : "Creates"
vals -> helm
tmpl -> helm
helm -> k8s : "Applies YAML"
```

### Understanding a Helm Chart
When you run `helm create mychart`, it generates a directory structure:
```text
mychart/
  Chart.yaml          # Metadata about the chart (name, version)
  values.yaml         # The default configuration values
  templates/          # The directory where your template files live
    deployment.yaml   # A K8s Deployment YAML with Go templating
    service.yaml      # A K8s Service YAML with Go templating
```

**Inside `templates/deployment.yaml`:**
Notice how we use `{{ .Values.replicaCount }}` instead of a hardcoded number.
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}-nginx
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: nginx
  template:
    ...
```

**Inside `values.yaml`:**
```yaml
replicaCount: 3
image:
  repository: nginx
  tag: "1.16.0"
```

### Basic Helm Commands
*   `helm search hub <app>`: Search the public Helm Hub for an application (e.g., redis).
*   `helm install my-release bitnami/redis`: Install a chart into your cluster. "my-release" is the name of your specific deployment.
*   `helm upgrade my-release bitnami/redis -f my-values.yaml`: Upgrade a release with a new custom values file.
*   `helm rollback my-release 1`: Oh no, the upgrade broke everything! Rollback to revision 1.
*   `helm ls`: List all installed releases.
*   `helm uninstall my-release`: Delete the application from the cluster completely.

---

## 7. Interview Questions

### 1. What is the difference between a Pod and a Container?
**Answer:** A container is a single running process isolated by Linux namespaces and cgroups (e.g., a Docker container). A Pod is a Kubernetes abstraction that wraps one or more containers. Containers inside the same Pod share the same network space (they share the same IP and can communicate via `localhost`) and can share storage volumes.

### 2. If a Pod crashes, what does Kubernetes do?
**Answer:** Kubernetes does *not* restart the exact same Pod. Pods are ephemeral. If a Pod was created independently, it stays dead. However, if the Pod is managed by a controller (like a Deployment or ReplicaSet), the controller notices that the desired state (e.g., 3 replicas) does not match the actual state (2 replicas), and it will instruct the API server to create a brand *new* Pod to replace the dead one.

### 3. Explain the difference between ClusterIP, NodePort, and LoadBalancer.
**Answer:**
*   **ClusterIP:** Exposes the service internally. It is only accessible from within the K8s cluster.
*   **NodePort:** Opens a specific port on every Worker Node's IP address and routes traffic to the service. Accessible externally via `<NodeIP>:<NodePort>`.
*   **LoadBalancer:** Triggers the cloud provider (AWS/GCP) to create an external, public-facing Load Balancer that routes traffic directly to the service.

### 4. What happens when a Worker Node dies?
**Answer:** The `kube-controller-manager` constantly monitors node health. If a node stops sending heartbeats, it marks the node as `NotReady`. After a timeout (default 5 minutes), the Pods on that node are marked for eviction. The controllers (Deployments/StatefulSets) managing those Pods will then spin up replacement Pods on healthy, available Worker Nodes in the cluster.

### 5. Why would you use Helm instead of writing plain `kubectl` YAML files?
**Answer:** Plain YAML files are static. If you have different environments (dev, staging, prod), you have to duplicate YAML files and manually change values like replicas and tags. Helm acts as a package manager and templating engine. You write the YAML once using Go templates, and inject dynamic variables via a `values.yaml` file. Helm also tracks releases, allowing you to easily `helm upgrade` or `helm rollback` an entire application composed of multiple K8s resources with a single command.

### 6. What is the exact difference between a Deployment and a StatefulSet?
**Answer:** 
*   **Deployment:** Used for stateless applications (like web servers). Pods are interchangeable and ephemeral. They get random names (e.g., `web-7fg9x`), and if one dies, a new one is spun up with a different name. They share the same storage volumes.
*   **StatefulSet:** Used for stateful applications (like databases). Pods have sticky, unique identities (e.g., `db-0`, `db-1`) and are created in strict order. If `db-0` dies, K8s restarts it and ensures it gets the exact same name and is reattached to the exact same persistent storage volume it had before.

### 7. How does Kubernetes handle persistent storage? Explain PV and PVC.
**Answer:** Kubernetes abstracts storage away from the underlying cloud provider. 
*   **PersistentVolume (PV):** A piece of storage in the cluster (e.g., an AWS EBS volume or NFS share) provisioned by an administrator or dynamically by a StorageClass.
*   **PersistentVolumeClaim (PVC):** A request for storage by a user (the Pod). The Pod asks for a PVC (e.g., "I need 10GB of fast SSD"), and Kubernetes binds that PVC to an available PV that matches the criteria. The Pod then mounts the PVC as a volume.

### 8. What is the role of `etcd` in the Kubernetes Control Plane?
**Answer:** `etcd` is a distributed, highly available key-value store. It serves as the absolute "source of truth" for the entire Kubernetes cluster. It stores the cluster state, configurations, and secrets. If `etcd` is lost and unrecoverable, the cluster is effectively dead because Kubernetes loses all memory of what Pods should be running, what Services exist, etc.

### 9. What is an InitContainer?
**Answer:** An InitContainer is a special container that runs *before* the main app containers in a Pod start. They must run to completion successfully before the next one starts. 
**Use Case:** If your main web app container relies on a database being fully booted and migrated before it can start, you can use an InitContainer with a script that pings the database or runs a migration script. Only when the InitContainer exits with code 0 will the main web container boot.

### 10. How does the Kubernetes Scheduler decide where to place a new Pod?
**Answer:** The `kube-scheduler` filters and scores nodes:
1.  **Filtering (Predicates):** It eliminates nodes that don't meet the Pod's hard requirements (e.g., does the node have enough free CPU/RAM? Does it match NodeSelectors/Taints?).
2.  **Scoring (Priorities):** It ranks the remaining nodes (e.g., it prefers spreading Pods from the same Deployment across different physical zones to ensure high availability).
The node with the highest score is selected, and the Pod is bound to it.

### 11. What are Taints, Tolerations, and Node Affinity?
**Answer:** These are mechanisms to control Pod scheduling:
*   **Taints and Tolerations:** A Taint is applied to a *Node* (e.g., "This node is for GPU workloads only"). A node will repel all Pods unless a Pod has a specific *Toleration* for that taint. It is restrictive.
*   **Node Affinity:** Applied to a *Pod*. It is an attraction mechanism (e.g., "I strongly prefer to run on a node with the label `disktype=ssd`"). 

### 12. Explain Kubernetes Network Policies.
**Answer:** By default, all Pods in a Kubernetes cluster can talk to all other Pods (flat network). A **NetworkPolicy** acts like a firewall at the Pod level. You can write rules to restrict traffic. For example, you can create a policy stating that only Pods with the label `app=frontend` are allowed to send incoming traffic to Pods with the label `app=backend`.

### 13. What is a Custom Resource Definition (CRD)?
**Answer:** Kubernetes comes with standard resources (Pods, Deployments, Services). A CRD allows you to extend the Kubernetes API with your own custom resources. 
For example, you could define a CRD called `DatabaseCluster`. Once defined, you can write a YAML file with `kind: DatabaseCluster`, and use a custom operator (controller) to watch for these resources and automatically provision real databases based on your YAML.

### 14. In Helm, what is the difference between `helm install` and `helm upgrade`? How do rollbacks work?
**Answer:** 
*   `helm install` creates a brand new release of a chart in the cluster.
*   `helm upgrade` updates an existing release. If the release doesn't exist, it fails (unless you use `--install`). 
Helm stores the state of each release as a Secret in the cluster. When you run `helm rollback <release> <revision>`, Helm retrieves the old configuration from that Secret and applies those exact templates to the cluster, restoring the previous state effortlessly.

### 15. What is the difference between a Liveness Probe and a Readiness Probe?
**Answer:** 
*   **Liveness Probe:** Checks if the container is *alive*. If it fails, Kubernetes kills the container and restarts it. Use it to catch deadlocks or crashed processes that haven't exited.
*   **Readiness Probe:** Checks if the container is *ready to accept traffic*. If it fails, Kubernetes does *not* restart it, but removes the Pod's IP from the Service load balancer. Use it when an app is booting up (e.g., loading large caches) or temporarily overwhelmed.
