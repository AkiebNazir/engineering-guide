# Intermediate Istio Install

**Goal:** Install Istio on a Kubernetes cluster and enable automatic sidecar injection for a namespace.

**Key Concepts:** [Control Plane vs. Data Plane](../Service_Mesh.md#control-plane-vs-data-plane)

**Prerequisites:** Kubernetes cluster (minikube/kind), `curl`

**Step-by-Step Execution:**
```bash
chmod +x install_istio.sh
./install_istio.sh
```
Expected output: Success messages for downloading Istio, installing demo profile, and labeling the namespace.

**Try it yourself:** Verify the namespace label by running `kubectl get namespace default --show-labels` and deploy a sample Nginx pod to see if the Envoy sidecar gets injected.

**Teardown:**
```bash
istioctl uninstall -y --purge
kubectl label namespace default istio-injection-
```
