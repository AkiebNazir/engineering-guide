# GitOps and ArgoCD

Traditional CI/CD pipelines use a **Push** model: Jenkins or GitHub Actions builds a Docker image and then runs `kubectl apply` to push the new YAML manifests to the Kubernetes cluster.

**GitOps** is a paradigm shift to a **Pull** model.

## 1. The GitOps Philosophy

In GitOps, the Git repository is the single source of truth for the *entire desired state of the system*.
If a Kubernetes deployment is running 5 replicas, but the Git repo says 3, the Git repo is right, and the cluster is wrong.

You don't push to the cluster. An agent lives *inside* the cluster, constantly polling the Git repo, and pulls changes down.

## 2. ArgoCD Architecture

ArgoCD is the most popular GitOps controller for Kubernetes.

```arch
%% caption: ArgoCD lives inside the cluster, polling Git for desired state, and reconciling the actual cluster state to match it.
route straight
node dev "Developer" at 0,0 icon=client color=blue
node git "Config Repo\n(desired state)" at 2,0 icon=file color=amber
group k8s "Kubernetes Cluster" color=slate style=dashed
node argo "ArgoCD" at 0,1 in k8s icon=package color=blue
node pod "App Pods\n(actual state)" at 2,1 in k8s icon=app color=green

dev -> git : "git push"
argo -> git : "polls\n(detects drift)"
argo -> pod : "kubectl apply\n(reconciles)"
```

### The Workflow
1. The CI pipeline runs tests, builds the Docker image `myapp:v2`, and pushes it to the Docker Registry.
2. The CI pipeline *commits* the new image tag `v2` to a separate "Config Repository" containing the Kubernetes YAML.
3. ArgoCD (running inside the cluster) wakes up, sees the Git commit, notices the cluster is running `v1`, and applies the YAML to make it `v2`.

### Why Pull is Better than Push
- **Security**: In the Push model, your CI server (GitHub Actions) needs cluster admin credentials to run `kubectl apply`. If CI is hacked, the cluster is compromised. In GitOps (Pull), ArgoCD is inside the cluster. It reaches *out* to GitHub. The cluster credentials never leave the cluster.
- **Drift Reconciliation**: If a rogue admin runs `kubectl edit deployment` manually and changes the replica count, ArgoCD will immediately detect that the cluster has "drifted" from Git, and will aggressively overwrite the manual change to put it back exactly how Git says it should be.
- **Disaster Recovery**: If your entire cluster burns down, you spin up a new empty cluster, install ArgoCD, point it at your Git repo, and go get coffee. ArgoCD will recreate the entire infrastructure perfectly.
