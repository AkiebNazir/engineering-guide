# End-to-End Observability with OpenTelemetry

This lab instruments an API with OpenTelemetry to generate distributed traces and metrics.

## Setup
We use the OpenTelemetry Collector, Jaeger (for tracing), and Prometheus (for metrics).

### docker-compose.yml
```yaml
version: '3'
services:
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
  otel-collector:
    image: otel/opentelemetry-collector:latest
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
```

### API Instrumentation (Node.js Example)
```javascript
const { NodeTracerProvider } = require('@opentelemetry/sdk-trace-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');
const { SimpleSpanProcessor } = require('@opentelemetry/sdk-trace-base');

const provider = new NodeTracerProvider();
const exporter = new OTLPTraceExporter({
  url: 'http://localhost:4318/v1/traces'
});
provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
provider.register();

// Express instrumentation here...
```

## Instructions
1. Create the `docker-compose.yml` and `otel-collector-config.yaml` files.
2. Run `docker-compose up -d` to start the observability stack.
3. Run your instrumented API application.
4. Make HTTP requests to the API endpoints to generate trace data.
5. Open Jaeger at `http://localhost:16686` in your browser to view the distributed traces.
