# Intermediate: Services & Networking
**Goal:** Learn how to expose applications internally and externally using Kubernetes Services.
**Key Concepts:** [Services](../Kubernetes_and_Helm.md#services-networking-and-discovery)
**Prerequisites:** A running Kubernetes cluster and `kubectl` installed.
**Step-by-Step Execution:** 
1. Deploy the backend (which uses a ClusterIP service) and frontend (which uses a NodePort service):
   ```bash
   kubectl apply -f backend.yaml -f frontend.yaml
   ```
2. Check the services and their IPs/Ports:
   ```bash
   kubectl get svc
   ```
3. Access the frontend. If using Minikube, run `minikube service web-frontend` or access `http://localhost:30080` (depending on your local setup).
   The frontend will communicate with the backend via the `backend-svc` internal DNS name.
**Try it yourself:** 
1. Scale the backend deployment to 4 replicas and watch the service automatically load balance traffic across the new pods.
   ```bash
   kubectl scale deployment api-backend --replicas=4
   ```
2. Inspect the endpoints associated with the backend service to see the IP addresses of the individual backend pods:
   ```bash
   kubectl get endpoints backend-svc
   ```
**Teardown:** 
```bash
kubectl delete -f backend.yaml -f frontend.yaml
```
