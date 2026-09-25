# Advanced: Helm Chart
**Goal:** Package complex Kubernetes deployments using Helm, allowing you to deploy parameterized and reusable applications.
**Key Concepts:** [Helm (The Package Manager)](../Kubernetes_and_Helm.md#6-introduction-to-helm-the-package-manager)
**Prerequisites:** A running Kubernetes cluster, `kubectl`, and the `helm` CLI installed.
**Step-by-Step Execution:** 
1. Install the Helm chart from the local directory:
   ```bash
   helm install my-release ./my-webapp
   ```
2. Verify the release was deployed:
   ```bash
   helm ls
   kubectl get all
   ```
**Try it yourself:** 
1. Upgrade the release! Open `./my-webapp/values.yaml` and change `replicaCount` to `3`. Then run:
   ```bash
   helm upgrade my-release ./my-webapp
   ```
2. Watch the new pods spin up.
3. Oh no, the upgrade "broke" something! Roll it back to the first revision instantly:
   ```bash
   helm rollback my-release 1
   ```
**Teardown:** 
```bash
helm uninstall my-release
```
