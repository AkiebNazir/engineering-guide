# Observability & Monitoring

Building software is only half the battle. Once your application is running in production, you need to know how it's behaving, when it fails, and why it failed. That is the domain of **Observability** and **Monitoring**.

While **monitoring** tells you *when* a system is not working (e.g., an alert triggers because CPU is at 99%), **observability** lets you ask arbitrary questions to understand *why* it is not working. Observability is a property of the system: a system is "observable" if you can understand its internal state solely from its external outputs.
---

## Interactive Examples

To put these concepts into practice, we've included several hands-on examples in the `examples/` directory. You can run them locally using Docker and Docker Compose:
- **[01 Basic Prometheus Metrics](examples/01_basic_prometheus_metrics/)**: Instrument a Golang app with custom metrics.
- **[02 Prometheus & Grafana](examples/02_intermediate_prometheus_grafana/)**: Run a full metrics stack and visualize data with Grafana.
- **[03 ELK Logging](examples/03_intermediate_elk_logging/)**: Centralize logs from multiple services using Elasticsearch, Logstash, and Kibana.
- **[04 OpenTelemetry & Jaeger](examples/04_advanced_opentelemetry/)**: Trace requests across multiple microservices.

---
## The Three Pillars of Observability

Observability is traditionally broken down into three pillars: **Metrics**, **Logs**, and **Traces**.

### 1. Metrics (The "What")
**Metrics** are numerical representations of data measured over time. They are cheap to store and incredibly fast to query, making them the best tool for high-level dashboards and triggering alerts.
*   **Types:** Counters (e.g., total requests), Gauges (e.g., current memory usage), Histograms (e.g., request latency distribution).
*   **Tools:** **Prometheus**, Datadog, InfluxDB, AWS CloudWatch.

> [!TIP]
> See the [01 Basic Prometheus Metrics](examples/01_basic_prometheus_metrics/) and [02 Prometheus & Grafana](examples/02_intermediate_prometheus_grafana/) examples for hands-on experience setting up metrics and dashboards.

#### Deep Dive: Prometheus
Prometheus has become the industry standard for metrics. Unlike many systems that expect applications to *push* metrics to a central server, Prometheus uses a **pull model**.
*   **Pull Model:** Your application exposes an HTTP endpoint (usually `/metrics`) returning plaintext metrics. The Prometheus server periodically "scrapes" (pulls) this endpoint. This scales well and prevents the monitoring system from overwhelming the application if the monitoring system falls behind.
*   **PromQL:** Prometheus comes with a powerful query language, PromQL, which allows you to perform mathematical operations on time-series data (e.g., calculating the 99th percentile latency over the last 5 minutes).

### 2. Logs (The "Why")
**Logs** are immutable, timestamped records of discrete events that happened over time. When an alert triggers based on a metric, you usually look at the logs to find the exact error message or stack trace.
*   **Structured Logging:** Modern systems emit JSON logs instead of plaintext. This allows log aggregators to easily index and search by specific fields (e.g., `user_id`, `request_id`).
*   **Tools:** **ELK Stack** (Elasticsearch, Logstash, Kibana), **Loki**, Splunk.

> [!TIP]
> Check out the [03 ELK Logging](examples/03_intermediate_elk_logging/) example to see how to aggregate structured logs locally using Docker.

#### Deep Dive: ELK & Loki
*   **ELK Stack:** Applications send logs to Logstash (or fluentd), which parses and enriches them before indexing them into Elasticsearch. Kibana is the UI used to search and visualize these logs. Elasticsearch is powerful but resource-intensive.
*   **Loki:** Designed by Grafana, Loki takes a different approach. Instead of indexing the full text of the logs, it only indexes *labels* (metadata), storing the raw logs in compressed chunks. This makes it significantly cheaper and easier to scale than Elasticsearch, heavily inspired by how Prometheus handles metrics.

### 3. Traces (The "Where")
In a microservices architecture, a single user request might travel through dozens of services. If the request is slow, metrics will tell you it's slow, and logs will give you errors, but how do you know *which* microservice caused the delay? **Distributed Tracing** solves this.
*   **Spans & Traces:** A **Trace** represents the entire journey of a request. It is made up of a tree of **Spans**, where each span represents a single operation (e.g., a database query, an HTTP call to another service).
*   **Context Propagation:** For traces to work, a unique `trace_id` must be passed along with every request between services (often via HTTP headers like `traceparent`).
*   **Tools:** **OpenTelemetry**, **Jaeger**, Zipkin.

> [!TIP]
> Try the [04 OpenTelemetry & Jaeger](examples/04_advanced_opentelemetry/) example to trace requests as they bounce across a multi-language microservice architecture.

#### Deep Dive: OpenTelemetry (OTel)
Historically, tracing was fragmented. OpenTelemetry is now the CNCF standard for generating and collecting observability data (metrics, logs, and traces). Instead of instrumenting your code with vendor-specific SDKs (like Jaeger or Datadog SDKs), you use the OpenTelemetry SDK. The OTel Collector then receives this data and exports it to whatever backend you choose.

---

## Architecture Overview

Here is a typical observability pipeline combining metrics, logs, and traces into a single Grafana dashboard:

```arch
node app "Microservice" at 1,0 icon=app
node prom "Prometheus" at 0,1 icon=prometheus
node loki "Loki" at 1,1 icon=database
node jaeger "Jaeger" at 2,1 icon=metrics
node graf "Grafana" at 1,2 icon=grafana

app -> prom : "/metrics"
app -> loki : "push logs"
app -> jaeger : "push spans"
prom -> graf
loki -> graf
jaeger -> graf
```

*(Note: In reality, an OpenTelemetry Collector often sits between the app and the backends to route the telemetry data).*

---

## Code Examples (Production-Grade)

### 1. Golang: Exposing Prometheus Metrics
Here is how you expose a custom Prometheus metric (a counter for HTTP requests) in Go.

```go
package main

import (
	"net/http"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

var (
	httpRequestsTotal = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "http_requests_total",
			Help: "Total number of HTTP requests.",
		},
		[]string{"path", "method", "status"},
	)
)

func init() {
	// Register the metric with Prometheus's default registry
	prometheus.MustRegister(httpRequestsTotal)
}

func handler(w http.ResponseWriter, r *http.Request) {
	// Increment the counter with specific labels
	httpRequestsTotal.WithLabelValues(r.URL.Path, r.Method, "200").Inc()
	w.Write([]byte("Hello, Observability!"))
}

func main() {
	http.HandleFunc("/", handler)
	// Expose the registered metrics at the /metrics endpoint for Prometheus to scrape
	http.Handle("/metrics", promhttp.Handler())
	http.ListenAndServe(":8080", nil)
}
```

### 2. Python: Creating an OpenTelemetry Span
Here is how you manually create a span and add attributes/events using the OpenTelemetry Python SDK.

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

# Setup tracing (in production, use OTLPSpanExporter instead of ConsoleSpanExporter)
provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)

def process_order(order_id: str):
    # Create a new span for this operation
    with tracer.start_as_current_span("process_order_transaction") as span:
        span.set_attribute("order.id", order_id)
        
        try:
            # Simulate work
            print(f"Processing {order_id}...")
            
            # Add a discrete event to the span (similar to a structured log)
            span.add_event("Order validation started")
            
            # Simulate a successful operation
            span.set_attribute("order.status", "success")
        except Exception as e:
            # Record exceptions automatically in the span
            span.record_exception(e)
            span.set_status(trace.StatusCode.ERROR, str(e))
            raise

if __name__ == "__main__":
    process_order("ORD-12345")
```

---

## MAANG-Level Interview Questions

1.  **Q: What is the difference between monitoring and observability?**
    *   **A:** Monitoring tells you *when* a system is broken by tracking known failure modes (e.g., CPU > 90%). Observability is a property of the system that allows you to debug *why* it is broken by interrogating the system using its external outputs (metrics, logs, traces) to uncover unknown-unknowns.

2.  **Q: Explain the difference between a Push vs. Pull model in metrics collection. Why does Prometheus use Pull?**
    *   **A:** In a Push model (e.g., StatsD, Datadog), applications send metrics directly to the monitoring server. In a Pull model (Prometheus), the server actively scrapes endpoints exposed by applications. Prometheus uses Pull because it simplifies service discovery (the server knows who to scrape), prevents the monitoring backend from being overwhelmed (it controls the rate), and makes it trivial to run a local Prometheus instance for debugging without changing application config.

3.  **Q: You have a microservices architecture and a user complains about a slow request. How do you find the bottleneck?**
    *   **A:** I would use Distributed Tracing. I'd search for the user's `trace_id` in Jaeger/Zipkin. The trace will display a waterfall chart of all spans across every microservice involved in the request. By looking at the duration of each span, I can visually identify exactly which service or database query was responsible for the latency.

4.  **Q: What is cardinality in Prometheus? Why is high cardinality bad?**
    *   **A:** Cardinality refers to the number of unique time-series generated by a metric, which is the product of all possible combinations of its label values. High cardinality (e.g., using a `user_id` or `session_id` as a label) is bad because it generates millions of unique time-series, consuming massive amounts of memory and potentially crashing the Prometheus server.

5.  **Q: How does context propagation work in Distributed Tracing?**
    *   **A:** When a request enters the system, a unique `trace_id` is generated. When Service A calls Service B, it injects this `trace_id` (along with a `parent_span_id`) into the outbound HTTP headers (e.g., `traceparent` or `X-B3-TraceId`). Service B extracts these headers and uses them to attach its new spans to the existing trace.

6.  **Q: Contrast Elasticsearch (ELK) and Loki for log aggregation.**
    *   **A:** Elasticsearch indexes the full text of every log message, enabling complex full-text searches, but at a massive cost in storage and RAM. Loki only indexes a small set of labels (like Prometheus) and stores the log lines themselves compressed. This makes Loki much cheaper and faster to ingest, shifting the compute cost to read-time (querying).

7.  **Q: How would you monitor a batch job or a short-lived script using Prometheus?**
    *   **A:** Since Prometheus uses a pull model, a short-lived script might terminate before Prometheus gets a chance to scrape it. I would use the **Prometheus Pushgateway**. The script pushes its metrics to the Pushgateway before exiting, and Prometheus scrapes the Pushgateway at its regular interval.

8.  **Q: Describe the OpenTelemetry architecture.**
    *   **A:** OpenTelemetry provides SDKs for applications to generate telemetry (metrics, logs, traces) in a vendor-neutral format (OTLP). Instead of sending this directly to a backend, applications usually send it to an **OTel Collector**. The Collector can receive data, process it (filter, batch, scrub PII), and then export it to multiple backends (e.g., Prometheus, Jaeger, Datadog) simultaneously.

9.  **Q: What are the "Four Golden Signals" of monitoring?**
    *   **A:** Coined by Google SREs, they are: **Latency** (time to service a request), **Traffic** (demand on the system, e.g., requests per second), **Errors** (rate of failing requests), and **Saturation** (how "full" your service is, e.g., CPU, memory, or connection pool limits).

10. **Q: You are running out of storage for your metrics. How do you mitigate this without losing historical trends?**
    *   **A:** I would implement **downsampling**. High-resolution metrics (e.g., scraped every 10 seconds) are kept for a short period (e.g., 2 weeks). Older metrics are aggregated (downsampled) to 5-minute or 1-hour intervals and stored in long-term storage solutions like Thanos or Cortex.
