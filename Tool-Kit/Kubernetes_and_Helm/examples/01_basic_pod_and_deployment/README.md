# Basic: Pods and Deployments
**Goal:** Understand the difference between a raw Pod and a Deployment, and why Deployments are preferred for stateless applications.
**Key Concepts:** [Pods](../Kubernetes_and_Helm.md#pods-the-smallest-unit), [Deployments](../Kubernetes_and_Helm.md#deployments-managing-pods)
**Prerequisites:** A running Kubernetes cluster (e.g., Minikube, Docker Desktop K8s, or kind) and `kubectl` installed.
**Step-by-Step Execution:** 
1. Create the Pod:
   ```bash
   kubectl apply -f pod.yaml
   ```
2. Verify the Pod is running:
   ```bash
   kubectl get pods
   ```
3. Create the Deployment:
   ```bash
   kubectl apply -f deployment.yaml
   ```
4. Verify the Deployment and its Replicas:
   ```bash
   kubectl get deployments
   kubectl get pods
   ```
**Try it yourself:** 
1. Delete the raw pod (`kubectl delete pod simple-pod`). It won't come back.
2. Delete one of the pods managed by the deployment (`kubectl delete pod <deployment-pod-name>`). Watch as the Deployment automatically creates a new one to replace it!
3. Scale the deployment up to 5 replicas:
   ```bash
   kubectl scale deployment nginx-deployment --replicas=5
   ```
**Teardown:** 
```bash
kubectl delete -f pod.yaml
kubectl delete -f deployment.yaml
```
