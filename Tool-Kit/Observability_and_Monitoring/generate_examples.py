import os
import shutil

base = "/Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Observability_and_Monitoring"
examples_py_dir = os.path.join(base, "examples")
examples_go_dir = os.path.join(base, "examples_go")

if os.path.exists(examples_py_dir):
    shutil.rmtree(examples_py_dir)
if os.path.exists(examples_go_dir):
    shutil.rmtree(examples_go_dir)

files = {}

# Python
files["examples/01_flask_prometheus_metrics/README.md"] = "# Flask Prometheus Metrics"
files["examples/01_flask_prometheus_metrics/app.py"] = "print('Flask Prometheus')"
files["examples/02_fastapi_opentelemetry_tracing/README.md"] = "# FastAPI OpenTelemetry Tracing"
files["examples/02_fastapi_opentelemetry_tracing/app.py"] = "print('FastAPI OTel')"
files["examples/03_python_custom_otel_metrics/README.md"] = "# Custom OpenTelemetry Metrics in Python"
files["examples/03_python_custom_otel_metrics/metrics.py"] = "print('Custom OTel')"
files["examples/04_celery_prometheus_exporter/README.md"] = "# Celery Prometheus Exporter"
files["examples/04_celery_prometheus_exporter/worker.py"] = "print('Celery Prometheus')"
files["examples/05_grpc_opentelemetry_py/README.md"] = "# gRPC OpenTelemetry Interceptors"
files["examples/05_grpc_opentelemetry_py/server.py"] = "print('gRPC OTel')"

# Go
files["examples_go/01_nethttp_prometheus/README.md"] = "# Go net/http Prometheus Metrics"
files["examples_go/01_nethttp_prometheus/main.go"] = "package main\nfunc main() {}"
files["examples_go/02_gin_opentelemetry_tracing/README.md"] = "# Gin OpenTelemetry Tracing"
files["examples_go/02_gin_opentelemetry_tracing/main.go"] = "package main\nfunc main() {}"
files["examples_go/03_go_custom_prometheus_collector/README.md"] = "# Go Custom Prometheus Collector"
files["examples_go/03_go_custom_prometheus_collector/main.go"] = "package main\nfunc main() {}"
files["examples_go/04_go_otel_metrics_and_traces/README.md"] = "# OpenTelemetry Traces & Metrics Unified in Go"
files["examples_go/04_go_otel_metrics_and_traces/main.go"] = "package main\nfunc main() {}"
files["examples_go/05_grpc_otel_go/README.md"] = "# gRPC OpenTelemetry Go Instrumentation"
files["examples_go/05_grpc_otel_go/main.go"] = "package main\nfunc main() {}"

for filepath, content in files.items():
    full_path = os.path.join(base, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content.strip() + "\\n")
