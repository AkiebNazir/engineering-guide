# Advanced Fault Injection

**Goal:** Test microservice resilience by injecting a 5-second delay into 50% of requests.

**Key Concepts:** [Traffic Management](../Service_Mesh.md#traffic-management)

**Prerequisites:** Kubernetes, Istio installed, a `ratings` service deployed.

**Step-by-Step Execution:**
```bash
kubectl apply -f fault_injection.yaml
```
Expected output: `virtualservice.networking.istio.io/ratings created`.

**Try it yourself:** Modify the fault injection rule to return an HTTP 500 abort error instead of a delay.

**Teardown:**
```bash
kubectl delete -f fault_injection.yaml
```
