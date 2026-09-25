# Basic Prometheus Metrics

**Goal:** Demonstrates how to instrument a Golang application with custom metrics (Counters and Gauges) and expose a `/metrics` endpoint.

**Key Concepts:** [Metrics (The "What")](../../Observability_and_Monitoring.md#1-metrics-the-what), [Prometheus Pull Model](../../Observability_and_Monitoring.md#deep-dive-prometheus), [Golang: Exposing Prometheus Metrics](../../Observability_and_Monitoring.md#1-golang-exposing-prometheus-metrics)

**Prerequisites:** 
- Docker

**Step-by-Step Execution:** 
1. Build the image:
   ```bash
   docker build -t go-metrics .
   ```
2. Run the container:
   ```bash
   docker run -p 8080:8080 go-metrics
   ```
3. Generate some traffic by visiting `http://localhost:8080/` in your browser or running `curl http://localhost:8080/` a few times.
4. View the metrics endpoint by visiting `http://localhost:8080/metrics`. You will see Prometheus' plain-text format containing `http_requests_total` and `active_connections`.

**Try it yourself:** 
Add a new metric, for example, a histogram to track the duration of requests, and expose it in the application. Rebuild and verify it appears in `/metrics`.

**Teardown:** 
```bash
# Find the container ID
docker ps

# Stop and remove the container
docker stop <container_id>
docker rm <container_id>
```
