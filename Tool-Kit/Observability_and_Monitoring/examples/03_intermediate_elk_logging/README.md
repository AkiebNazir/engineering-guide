# The ELK Stack (Logs)

**Goal:** Centralize logs scattered across microservices using the ELK (Elasticsearch, Logstash, Kibana) stack.

**Key Concepts:** [Logs (The "Why")](../../Observability_and_Monitoring.md#2-logs-the-why), [Structured Logging](../../Observability_and_Monitoring.md#2-logs-the-why), [ELK Stack Deep Dive](../../Observability_and_Monitoring.md#deep-dive-elk--loki)

**Prerequisites:** 
- Docker Compose

**Step-by-Step Execution:** 
1. Start the stack (this might take a few minutes for Elasticsearch to start up):
   ```bash
   docker-compose up -d
   ```
2. The `python-app` service will automatically write strict JSON strings to a shared volume.
3. `logstash` tails that file, parses the JSON, and pushes it to `elasticsearch`.
4. Open Kibana at `http://localhost:5601`.
5. Go to **Discover**, and create an index pattern for `app-logs-*`.
6. You can now search, filter, and alert on all your application logs across your entire infrastructure!

**Try it yourself:** 
Modify the python-app to log a new field (e.g., `user_id` or `trace_id`). Restart the container, and try to filter for this new field in Kibana!

**Teardown:** 
```bash
docker-compose down -v
```
