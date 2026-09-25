# Advanced: StatefulSets & Persistent Volumes
**Goal:** Provision a stateful application (PostgreSQL) that maintains a sticky identity and persistent storage, ensuring zero data loss if a pod crashes.
**Key Concepts:** [StatefulSets](../Kubernetes_and_Helm.md#statefulsets), [Persistent Volumes](../Kubernetes_and_Helm.md#7-how-does-kubernetes-handle-persistent-storage-explain-pv-and-pvc)
**Prerequisites:** A running Kubernetes cluster and `kubectl` installed.
**Step-by-Step Execution:** 
1. Apply the storage claim, headless service, and statefulset:
   ```bash
   kubectl apply -f storage.yaml -f service.yaml -f statefulset.yaml
   ```
2. Watch the pods get created sequentially:
   ```bash
   kubectl get pods -w
   ```
3. Check the PersistentVolumeClaim (PVC) status:
   ```bash
   kubectl get pvc
   ```
**Try it yourself:** 
1. Delete the `postgres-db-0` pod:
   ```bash
   kubectl delete pod postgres-db-0
   ```
2. Watch it immediately come back with the exact same name and re-attach to the exact same persistent storage!
3. Scale the StatefulSet to 3 replicas to see how it assigns ordered names (`postgres-db-1`, `postgres-db-2`):
   ```bash
   kubectl scale statefulset postgres-db --replicas=3
   ```
**Teardown:** 
```bash
kubectl delete -f statefulset.yaml -f service.yaml -f storage.yaml
```
