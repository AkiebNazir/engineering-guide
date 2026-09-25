# Advanced: OpenTelemetry & Distributed Tracing (Jaeger)

**Goal:** Understand how to use distributed tracing to follow a request as it bounces between different microservices written in different languages.

**Key Concepts:** [Traces (The "Where")](../../Observability_and_Monitoring.md#3-traces-the-where), [Distributed Tracing](../../Observability_and_Monitoring.md#3-traces-the-where), [OpenTelemetry Deep Dive](../../Observability_and_Monitoring.md#deep-dive-opentelemetry-otel)

**Prerequisites:** 
- Docker Compose

**Step-by-Step Execution:** 
1. Build and start the stack:
   ```bash
   docker-compose up -d --build
   ```
2. Trigger the multi-service flow:
   ```bash
   curl http://localhost:3000/buy
   ```
   The Node.js Express API receives the request, starts a Trace, and calls the Python API.
3. The Node OpenTelemetry SDK automatically injects a `traceparent` HTTP header. The Python OpenTelemetry SDK automatically reads that header, ensuring both services are part of the exact same visual Trace tree.
4. Open the Jaeger UI at `http://localhost:16686`.
5. Search for traces on the `node-gateway` service.
6. You will see a waterfall chart showing exactly how many milliseconds were spent in Node, the network hop, and then inside Python!

**Try it yourself:** 
Add a third service (e.g., a simple Go or Python service) and configure the Python API to call it. Ensure the trace continues through all three services!

**Teardown:** 
```bash
docker-compose down
```
