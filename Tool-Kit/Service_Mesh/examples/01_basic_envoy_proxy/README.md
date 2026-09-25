# Basic Envoy Proxy

**Goal:** Demonstrate how to configure Envoy as a standalone reverse proxy routing to a dummy backend.

**Key Concepts:** [The Sidecar Pattern](../Service_Mesh.md#the-sidecar-pattern), [Data Plane](../Service_Mesh.md#1-data-plane)

**Prerequisites:** Docker, Docker Compose

**Step-by-Step Execution:**
```bash
docker-compose up -d
curl http://localhost:10000
```
Expected output: `Hello from the backend!`

**Try it yourself:** Modify the `envoy.yaml` to route to a different port or add a custom HTTP header to the request.

**Teardown:**
```bash
docker-compose down
```
