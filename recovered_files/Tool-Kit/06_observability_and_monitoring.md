# Observability and Monitoring

Observability is the ability to understand the internal state of a system based on its external outputs. In modern microservices, the "Three Pillars of Observability" are Metrics, Logs, and Traces.

## 1. Metrics: Prometheus and Grafana

Metrics are numerical measurements of your system over time (e.g., CPU usage, HTTP 500 error rate). They are incredibly cheap to store and aggregate.

```arch
%% caption: Prometheus scrapes metrics from targets on an interval, while Grafana queries Prometheus to build dashboards.
node app "App Instance\\n(/metrics endpoint)" at 0,1 icon=app color=green
node prom "Prometheus\\n(Time-series DB)" at 2,1 icon=db color=red
node graf "Grafana\\n(Dashboards)" at 4,1 icon=dashboard color=amber
node alert "Alertmanager" at 2,0 icon=alert color=red

prom -> app : "HTTP GET (Scrape)"
graf -> prom : "PromQL query"
prom -> alert : "Threshold crossed"
```

- **Prometheus**: A time-series database. Unlike traditional systems that push data *to* a monitoring server, Prometheus uses a **pull model**. It actively scrapes `/metrics` endpoints on your applications every 15 seconds.
- **PromQL**: The query language. `rate(http_requests_total{status="500"}[5m])` calculates the per-second rate of 500 errors over the last 5 minutes.
- **Grafana**: A visualization tool that connects to Prometheus (and other databases) to draw graphs and build dashboards.

### The RED Method for Microservices
If you only measure three things for every service, measure:
- **Rate**: Number of requests per second.
- **Errors**: Number of failed requests per second.
- **Duration**: The time requests take (use Histograms to measure the 95th and 99th percentiles, never the average).

## 2. Logs: The ELK Stack

Logs are discrete events (e.g., "User 123 logged in"). They contain the highest fidelity information but are expensive to store.

The classic stack is ELK (Elasticsearch, Logstash, Kibana):
- **Filebeat/Fluent Bit**: Lightweight agents running on every node that tail log files and ship them.
- **Logstash**: Parses, filters, and transforms the raw log text into structured JSON.
- **Elasticsearch**: The search engine where logs are indexed and stored.
- **Kibana**: The UI to search and visualize the logs.

**Best Practice**: Never write logs to files in containers. Write JSON-formatted logs to `stdout`/`stderr`. Let the container engine (Docker/Kubernetes) capture `stdout` and forward it to Elasticsearch.

## 3. Distributed Tracing: OpenTelemetry

In a microservice architecture, a single user click might touch 10 different services. If the request is slow, logs and metrics won't tell you *which* service caused the delay.

Distributed Tracing solves this.

- **Trace**: The entire journey of a single request across all services.
- **Span**: A single operation within a trace (e.g., "DB Query" or "Call Service B"). Spans have start times, end times, and parent spans.

### Context Propagation
How does Service B know it's part of the same trace as Service A? 
Service A injects a **Trace ID** into the HTTP headers (e.g., the W3C standard `traceparent` header). Service B reads that header, does its work, and passes the same Trace ID down to Service C.

**OpenTelemetry (OTel)** is the modern standard for this. You use OTel SDKs in your code to generate spans, and an OTel Collector agent to batch and ship those spans to a backend like Jaeger, Honeycomb, or Datadog.
