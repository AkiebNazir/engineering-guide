# Intermediate Istio mTLS

**Goal:** Enforce strict mutual TLS (mTLS) authentication for services within a namespace.

**Key Concepts:** [mTLS (Mutual TLS) for Zero-Trust Security](../Service_Mesh.md#mtls-mutual-tls-for-zero-trust-security)

**Prerequisites:** Kubernetes, Istio installed, Sidecar injection enabled

**Step-by-Step Execution:**
```bash
kubectl apply -f peer_authentication.yaml
```
Expected output: `peerauthentication.security.istio.io/default created`. 

**Try it yourself:** Attempt to curl a pod in the default namespace from a pod outside the mesh. The connection should be rejected.

**Teardown:**
```bash
kubectl delete -f peer_authentication.yaml
```
