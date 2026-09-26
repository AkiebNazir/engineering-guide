import time
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
