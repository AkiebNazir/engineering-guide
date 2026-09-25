# Prometheus & Grafana Stack

**Goal:** Takes the basic Go app and wraps it in a real production monitoring stack with Prometheus and Grafana.

**Key Concepts:** [Metrics (The "What")](../../Observability_and_Monitoring.md#1-metrics-the-what), [PromQL](../../Observability_and_Monitoring.md#deep-dive-prometheus)

**Prerequisites:** 
- Docker Compose

**Step-by-Step Execution:** 
1. Start the stack:
   ```bash
   docker-compose up -d
   ```
2. Hit the app a few times to generate data:
   ```bash
   curl http://localhost:8080
   ```
3. Go to Prometheus at `http://localhost:9090`. Try typing the PromQL query:
   ```promql
   rate(http_requests_total[1m])
   ```
4. Go to Grafana at `http://localhost:3000` (login: admin / admin).
5. Add Prometheus (`http://prometheus:9090`) as a Data Source.
6. Create a dashboard chart for your requests!

**Try it yourself:** 
Create a new Grafana panel to monitor `active_connections` gauge over time. Try stress-testing the app and watch the Grafana dashboard update!

**Teardown:** 
```bash
docker-compose down
```
