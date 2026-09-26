import os

base = "/Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Observability_and_Monitoring"
files = {}

# Python
files["examples/02_fastapi_opentelemetry_tracing/README.md"] = """# FastAPI OpenTelemetry Tracing
Demonstrates how to automatically instrument a FastAPI application using OpenTelemetry. It exports traces to an OTLP endpoint (e.g., Jaeger or Grafana Tempo).

## Concepts Covered
- OpenTelemetry FastAPI Instrumentation
- OTLP Span Exporter
- Context propagation across microservices.
"""
files["examples/02_fastapi_opentelemetry_tracing/app.py"] = """from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

resource = Resource.create({"service.name": "fastapi-tracing-service"})
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True))
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

app = FastAPI()
FastAPIInstrumentor.instrument_app(app)

tracer = trace.get_tracer(__name__)

@app.get("/process")
def process_data():
    with tracer.start_as_current_span("compute_heavy_task") as span:
        span.set_attribute("task.type", "computation")
        import time; time.sleep(0.1)
        return {"status": "processed"}
"""

files["examples/03_python_custom_otel_metrics/README.md"] = """# Custom OpenTelemetry Metrics in Python
Shows how to use the OpenTelemetry Metrics API to create custom UpDownCounters, Gauges, and Histograms and export them via OTLP.
"""
files["examples/03_python_custom_otel_metrics/metrics.py"] = """import time
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.sdk.resources import Resource

resource = Resource.create({"service.name": "custom-metrics-service"})
reader = PeriodicExportingMetricReader(OTLPMetricExporter(insecure=True))
provider = MeterProvider(resource=resource, metric_readers=[reader])
metrics.set_meter_provider(provider)

meter = metrics.get_meter("my.custom.meter")

active_users = meter.create_up_down_counter("active_users", description="Number of active users")
task_duration = meter.create_histogram("task_duration_ms", description="Task duration in ms")

def process_task():
    active_users.add(1, {"tenant": "customer_a"})
    start = time.time()
    time.sleep(0.05)
    duration_ms = (time.time() - start) * 1000
    task_duration.record(duration_ms, {"task_name": "db_sync"})
    active_users.add(-1, {"tenant": "customer_a"})

if __name__ == "__main__":
    for _ in range(5):
        process_task()
"""

files["examples/04_celery_prometheus_exporter/README.md"] = """# Celery Prometheus Exporter
Background jobs are critical to monitor. This example shows how to tap into Celery's signal framework to emit Prometheus metrics.
"""
files["examples/04_celery_prometheus_exporter/worker.py"] = """from celery import Celery
from celery.signals import task_postrun
from prometheus_client import Counter, start_http_server

app = Celery('tasks', broker='redis://localhost:6379/0')

TASK_COUNTER = Counter('celery_task_status_total', 'Total task count', ['task_name', 'state'])

@task_postrun.connect
def on_task_postrun(task_id, task, args, kwargs, retval, state, **kw):
    TASK_COUNTER.labels(task_name=task.name, state=state).inc()

@app.task
def divide(x, y):
    return x / y

if __name__ == '__main__':
    start_http_server(9090)
    app.worker_main(['worker', '--loglevel=info'])
"""

files["examples/05_grpc_opentelemetry_py/README.md"] = """# gRPC OpenTelemetry Interceptors
Microservices communicating over gRPC need distributed tracing. This shows how to use OpenTelemetry interceptors to propagate context automatically.
"""
files["examples/05_grpc_opentelemetry_py/server.py"] = """import grpc
from concurrent import futures
from opentelemetry.instrumentation.grpc import GrpcInstrumentorServer
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

trace.set_tracer_provider(TracerProvider())
grpc_server_instrumentor = GrpcInstrumentorServer()
grpc_server_instrumentor.instrument()

class GreeterServicer:
    def SayHello(self, request, context):
        return {"message": f"Hello, {request.name}!"}

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
"""

# Go
files["examples_go/02_gin_opentelemetry_tracing/README.md"] = """# Gin OpenTelemetry Tracing
Demonstrates how to add distributed tracing to a Gin web application using `otelgin`.
"""
files["examples_go/02_gin_opentelemetry_tracing/main.go"] = """package main

import (
	"context"
	"github.com/gin-gonic/gin"
	"go.opentelemetry.io/contrib/instrumentation/github.com/gin-gonic/gin/otelgin"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/exporters/stdout/stdouttrace"
	"go.opentelemetry.io/otel/sdk/trace"
)

func initTracer() *trace.TracerProvider {
	exporter, _ := stdouttrace.New(stdouttrace.WithPrettyPrint())
	tp := trace.NewTracerProvider(trace.WithBatcher(exporter))
	otel.SetTracerProvider(tp)
	return tp
}

func main() {
	tp := initTracer()
	defer tp.Shutdown(context.Background())

	r := gin.Default()
	r.Use(otelgin.Middleware("my-gin-service"))

	r.GET("/ping", func(c *gin.Context) {
		tracer := otel.Tracer("gin-server")
		_, span := tracer.Start(c.Request.Context(), "internal_work")
		defer span.End()
		
		c.JSON(200, gin.H{"message": "pong"})
	})

	r.Run(":8080")
}
"""
files["examples_go/03_go_custom_prometheus_collector/README.md"] = """# Go Custom Prometheus Collector
When scraping metrics from a 3rd party system, you should implement the `prometheus.Collector` interface rather than directly setting gauge values.
"""
files["examples_go/03_go_custom_prometheus_collector/main.go"] = """package main

import (
	"math/rand"
	"net/http"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

type ExternalSystemCollector struct {
	queueLengthDesc *prometheus.Desc
}

func NewExternalSystemCollector() *ExternalSystemCollector {
	return &ExternalSystemCollector{
		queueLengthDesc: prometheus.NewDesc("external_queue_length", "Length of external queue", nil, nil),
	}
}

func (c *ExternalSystemCollector) Describe(ch chan<- *prometheus.Desc) {
	ch <- c.queueLengthDesc
}

func (c *ExternalSystemCollector) Collect(ch chan<- prometheus.Metric) {
	val := rand.Float64() * 100
	ch <- prometheus.MustNewConstMetric(c.queueLengthDesc, prometheus.GaugeValue, val)
}

func main() {
	registry := prometheus.NewRegistry()
	registry.MustRegister(NewExternalSystemCollector())

	http.Handle("/metrics", promhttp.HandlerFor(registry, promhttp.HandlerOpts{}))
	http.ListenAndServe(":8080", nil)
}
"""
files["examples_go/04_go_otel_metrics_and_traces/README.md"] = """# OpenTelemetry Traces & Metrics Unified in Go"""
files["examples_go/04_go_otel_metrics_and_traces/main.go"] = """package main

import (
	"context"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/metric"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	sdkmetric "go.opentelemetry.io/otel/sdk/metric"
)

func main() {
	ctx := context.Background()
	res := resource.Default()

	tp := sdktrace.NewTracerProvider(sdktrace.WithResource(res))
	otel.SetTracerProvider(tp)

	mp := sdkmetric.NewMeterProvider(sdkmetric.WithResource(res))
	otel.SetMeterProvider(mp)

	tracer := otel.Tracer("example/trace")
	meter := otel.Meter("example/metric")

	counter, _ := meter.Int64Counter("jobs.completed", metric.WithDescription("Completed jobs"))

	ctx, span := tracer.Start(ctx, "job.process")
	counter.Add(ctx, 1)
	span.End()
}
"""
files["examples_go/05_grpc_otel_go/README.md"] = """# gRPC OpenTelemetry Go Instrumentation"""
files["examples_go/05_grpc_otel_go/main.go"] = """package main

import (
	"net"
	"google.golang.org/grpc"
	"go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
)

type server struct{}

func main() {
	lis, _ := net.Listen("tcp", ":50051")
	
	s := grpc.NewServer(
		grpc.UnaryInterceptor(otelgrpc.UnaryServerInterceptor()),
		grpc.StreamInterceptor(otelgrpc.StreamServerInterceptor()),
	)
	
	s.Serve(lis)
}
"""

for filepath, content in files.items():
    full_path = os.path.join(base, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content.strip() + "\n")
