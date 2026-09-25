# Advanced Canary Deployment

**Goal:** Implement a canary deployment routing 90% of traffic to v1 and 10% to v2 using Istio.

**Key Concepts:** [Traffic Management](../Service_Mesh.md#traffic-management)

**Prerequisites:** Kubernetes, Istio installed, a service `my-service` running with `v1` and `v2` pods.

**Step-by-Step Execution:**
```bash
kubectl apply -f destination_rule.yaml
kubectl apply -f virtual_service.yaml
```
Expected output: `destinationrule.networking.istio.io/my-service created` and `virtualservice.networking.istio.io/my-service created`.

**Try it yourself:** Change the VirtualService routing weights to 50/50 and reapply it to see an even distribution of traffic.

**Teardown:**
```bash
kubectl delete -f virtual_service.yaml
kubectl delete -f destination_rule.yaml
```
