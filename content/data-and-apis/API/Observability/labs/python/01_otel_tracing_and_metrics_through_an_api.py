"""
LAB 01 (basic) - OpenTelemetry end to end: one request, three services, one trace, RED metrics
==============================================================================================
Three real HTTP services in one process, instrumented BY HAND with the OpenTelemetry SDK (no
auto-instrumentation, so you see every step). Spans and metrics go to IN-MEMORY exporters, so the
lab needs no collector, no Jaeger and no Prometheus, and can ASSERT on what was recorded.

    client -> gateway -> orders -> payments          each hop: inject `traceparent` into the
                           |                         outgoing headers, extract it on the way in
                           +-> "db" (an internal span)

You will learn
  * the data model: a TRACE is a tree of SPANS sharing one trace_id; each span has a kind
    (SERVER / CLIENT / INTERNAL), attributes, events, a status, and its service's RESOURCE
    (service.name). Six spans below, three services, one trace_id
  * CONTEXT PROPAGATION: the W3C `traceparent` header (00-<trace_id>-<span_id>-<flags>) is the
    only thing that links services; forget to inject it once and the trace splits in two
  * errors: status ERROR + a recorded exception event on the span that failed, so "which service
    broke?" is a query, not a guess
  * finding the slow hop with SELF time (a span's duration minus its children's)
  * METRICS with semantic-convention names: `http.server.request.duration` (a histogram, in
    seconds) gives the RED signals - Rate, Errors, Duration - per route, and p95 from buckets
  * the CARDINALITY trap: labelling by raw path (/orders/1, /orders/2 ...) instead of the route
    template makes one time series per id
  * LOG CORRELATION: trace_id and span_id stamped on every log line
  * HEAD SAMPLING: ParentBased(TraceIdRatioBased) decides once at the edge; downstream follows
    the sampled flag, so you keep WHOLE traces or none

In production you swap the in-memory exporters for OTLP exporters that send to an OpenTelemetry
Collector (then Jaeger/Tempo/Honeycomb/Datadog...), and let instrumentation libraries
(opentelemetry-instrumentation-fastapi, -requests, ...) create the HTTP spans for you.

Needs   pip install opentelemetry-sdk
Run it  python 01_otel_tracing_and_metrics_through_an_api.py
"""
import http.client
import io
import json
import logging
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from opentelemetry import trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import InMemoryMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.sdk.trace.sampling import ALWAYS_ON, ParentBased, TraceIdRatioBased
from opentelemetry.trace import SpanKind, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

PROPAGATOR = TraceContextTextMapPropagator()
SPANS = InMemorySpanExporter()                    # every service exports here (a stand-in for a collector)
DURATION_BUCKETS = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]   # seconds (OTel's HTTP advice)

log_stream = io.StringIO()


class TraceIdFilter(logging.Filter):
    """What opentelemetry-instrumentation-logging does: stamp the current span onto the record."""
    def filter(self, record):
        ctx = trace.get_current_span().get_span_context()
        record.trace_id = format(ctx.trace_id, "032x") if ctx.is_valid else "-"
        record.span_id = format(ctx.span_id, "016x") if ctx.is_valid else "-"
        return True


log = logging.getLogger("lab")
_h = logging.StreamHandler(log_stream)
_h.setFormatter(logging.Formatter("%(levelname)s %(name)s trace=%(trace_id)s span=%(span_id)s %(message)s"))
_h.addFilter(TraceIdFilter())
log.addHandler(_h)
log.setLevel(logging.INFO)


# ============================================================ one instrumented service ==
class Service:
    """A tiny HTTP service with its own TracerProvider + MeterProvider (= its own process in real life)."""

    def __init__(self, name: str, handler, sampler=ParentBased(ALWAYS_ON), route_label=True):
        resource = Resource.create({"service.name": name})
        self.tp = TracerProvider(resource=resource, sampler=sampler)
        self.tp.add_span_processor(SimpleSpanProcessor(SPANS))
        self.reader = InMemoryMetricReader()
        self.mp = MeterProvider(resource=resource, metric_readers=[self.reader])
        self.tracer = self.tp.get_tracer("lab.service")
        self.duration = self.mp.get_meter("lab.service").create_histogram(
            "http.server.request.duration", unit="s", description="Duration of HTTP server requests",
            explicit_bucket_boundaries_advisory=DURATION_BUCKETS)
        self.name, self.handler, self.route_label = name, handler, route_label
        svc = self

        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                svc.serve(self)

            def log_message(self, *_):
                pass
        self.srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.port = self.srv.server_port

    def serve(self, req: BaseHTTPRequestHandler):
        route = "/" + req.path.strip("/").split("/")[0] + ("/{id}" if req.path.count("/") > 1 else "")
        # 1. EXTRACT the caller's context from the incoming headers, 2. make it the parent
        parent = PROPAGATOR.extract(carrier=dict(req.headers))
        start = time.perf_counter()
        with self.tracer.start_as_current_span(f"GET {route}", context=parent, kind=SpanKind.SERVER,
                                               attributes={"http.request.method": "GET", "http.route": route,
                                                           "url.path": req.path}) as span:
            try:
                status, body = self.handler(self, req.path)
            except Exception as exc:                     # noqa: BLE001 - the lab wants to show it
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                status, body = 500, {"error": str(exc)}
            span.set_attribute("http.response.status_code", status)
            if status >= 500 and span.status.status_code != StatusCode.ERROR:
                span.set_status(Status(StatusCode.ERROR, f"HTTP {status}"))
        attrs = {"http.request.method": "GET", "http.response.status_code": status,
                 "http.route": route if self.route_label else req.path}
        self.duration.record(time.perf_counter() - start, attrs)
        data = json.dumps(body).encode()
        req.send_response(status)
        req.send_header("Content-Length", str(len(data)))
        req.end_headers()
        req.wfile.write(data)

    def call(self, port: int, path: str) -> tuple[int, dict]:
        """An outgoing call: a CLIENT span, and INJECT its context into the request headers."""
        # Semantic conventions: a CLIENT span without a route template is named just "GET";
        # the concrete URL goes in an attribute, so span names stay low-cardinality.
        with self.tracer.start_as_current_span("GET", kind=SpanKind.CLIENT,
                                               attributes={"server.port": port, "url.path": path}) as span:
            headers: dict[str, str] = {}
            PROPAGATOR.inject(headers)                   # adds 'traceparent' (and 'tracestate')
            c = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
            c.request("GET", path, headers=headers)
            r = c.getresponse()
            body = json.loads(r.read() or b"{}")
            c.close()
            span.set_attribute("http.response.status_code", r.status)
            if r.status >= 500:
                span.set_status(Status(StatusCode.ERROR, f"HTTP {r.status}"))
            return r.status, body


# ================================================================ the three services ==
def payments_handler(svc, path):
    amount = int(path.rsplit("/", 1)[1])
    if amount >= 900:
        raise RuntimeError("card declined by issuer")     # becomes span status ERROR + exception event
    if amount >= 500:
        time.sleep(0.12)                                   # a slow fraud check
    return 200, {"charged": amount}


def orders_handler(svc, path):
    amount = int(path.rsplit("/", 1)[1])
    with svc.tracer.start_as_current_span("db SELECT orders", kind=SpanKind.INTERNAL,
                                          attributes={"db.system.name": "postgresql"}):
        time.sleep(0.002)
        log.info("loaded order for amount=%s", amount)
    status, body = svc.call(SERVICES["payments"].port, f"/charge/{amount}")
    return (200, {"order": amount, **body}) if status == 200 else (502, {"error": "payment failed"})


def gateway_handler(svc, path):
    return svc.call(SERVICES["orders"].port, "/orders/" + path.rsplit("/", 1)[1])


SERVICES: dict[str, Service] = {}


def client_get(path: str) -> int:
    c = http.client.HTTPConnection("127.0.0.1", SERVICES["gateway"].port, timeout=5)
    c.request("GET", path)                                   # the client sends no traceparent: gateway starts the trace
    status = c.getresponse().status
    c.close()
    return status


def trace_of(spans, trace_id):
    return [s for s in spans if s.context.trace_id == trace_id]


def print_tree(spans):
    by_parent = {}
    for s in spans:
        by_parent.setdefault(s.parent.span_id if s.parent else None, []).append(s)

    def walk(parent_id, depth):
        for s in sorted(by_parent.get(parent_id, []), key=lambda s: s.start_time):
            ms = (s.end_time - s.start_time) / 1e6
            err = "  ERROR " + (s.status.description or "") if s.status.status_code == StatusCode.ERROR else ""
            print(f"   {'  ' * depth}{s.resource.attributes['service.name']:9s} {s.kind.name:8s} "
                  f"{s.name:22s} {ms:7.1f} ms{err}")
            walk(s.context.span_id, depth + 1)
    walk(None, 0)


def self_time_ms(span, spans):
    children = [c for c in spans if c.parent and c.parent.span_id == span.context.span_id]
    return ((span.end_time - span.start_time) - sum(c.end_time - c.start_time for c in children)) / 1e6


def histogram_points(svc):
    data = svc.reader.get_metrics_data()
    return [p for rm in data.resource_metrics for sm in rm.scope_metrics for m in sm.metrics
            if m.name == "http.server.request.duration" for p in m.data.data_points]


def p95_from_buckets(points):
    """What histogram_quantile() does in Prometheus: find the bucket holding the 95th percentile."""
    counts = [sum(col) for col in zip(*(p.bucket_counts for p in points))]
    bounds = list(points[0].explicit_bounds) + [float("inf")]
    target, seen = 0.95 * sum(counts), 0
    for bound, c in zip(bounds, counts):
        seen += c
        if seen >= target:
            return bound
    return float("inf")


# =========================================================================== demo ==
def demo():
    for name, h in (("payments", payments_handler), ("orders", orders_handler), ("gateway", gateway_handler)):
        SERVICES[name] = Service(name, h)

    print("== 1. one request -> one trace across three services ==")
    assert client_get("/checkout/120") == 200
    spans = SPANS.get_finished_spans()
    trace_ids = {s.context.trace_id for s in spans}
    print(f"   {len(spans)} spans, {len(trace_ids)} trace_id: {format(next(iter(trace_ids)), '032x')}")
    print_tree(spans)
    assert len(spans) == 6 and len(trace_ids) == 1
    assert {s.resource.attributes["service.name"] for s in spans} == {"gateway", "orders", "payments"}
    root = [s for s in spans if s.parent is None]
    assert len(root) == 1 and root[0].kind == SpanKind.SERVER

    print("\n== 2. what actually crossed the wire ==")
    headers = {}
    with SERVICES["gateway"].tracer.start_as_current_span("demo"):
        PROPAGATOR.inject(headers)
    version, tid, sid, flags = headers["traceparent"].split("-")
    print(f"   traceparent: {headers['traceparent']}")
    print(f"   version={version} trace_id={tid} (16 bytes) parent span_id={sid} (8 bytes) flags={flags}")
    print("   flags is a bit field: 0x01 = sampled; 0x02 = 'trace id is random' (Trace Context Level 2,")
    print("   set by recent SDKs), which lets a downstream sampler trust the id's randomness")
    assert len(tid) == 32 and len(sid) == 16 and int(flags, 16) & 0x01

    print("\n== 3. a failing request: which service broke? ==")
    SPANS.clear()
    assert client_get("/checkout/950") == 502
    spans = SPANS.get_finished_spans()
    print_tree(spans)
    failing = [s for s in spans if s.status.status_code == StatusCode.ERROR and s.kind == SpanKind.SERVER]
    origin = [s for s in failing if any(e.name == "exception" for e in s.events)]
    print(f"   the exception was recorded in: {origin[0].resource.attributes['service.name']} "
          f"-> {origin[0].events[0].attributes['exception.message']!r}")
    assert origin[0].resource.attributes["service.name"] == "payments" and len(failing) == 3
    print("   every SERVER span on the path is ERROR (each returned 5xx), but only one holds the")
    print("   exception event: search for it instead of reading three services' logs.")

    print("\n== 4. a slow request: where did the time go? (self time per span) ==")
    SPANS.clear()
    client_get("/checkout/600")
    spans = SPANS.get_finished_spans()
    worst = max(spans, key=lambda s: self_time_ms(s, spans))
    for s in sorted(spans, key=lambda s: -self_time_ms(s, spans))[:3]:
        print(f"   self {self_time_ms(s, spans):6.1f} ms  {s.resource.attributes['service.name']:9s} {s.name}")
    assert worst.resource.attributes["service.name"] == "payments" and self_time_ms(worst, spans) > 100

    print("\n== 5. RED metrics from the histogram (gateway, after 40 more requests) ==")
    for i in range(40):
        client_get(f"/checkout/{[50, 120, 600, 950][i % 4]}")
    points = histogram_points(SERVICES["gateway"])
    total = sum(p.count for p in points)
    errors = sum(p.count for p in points if p.attributes["http.response.status_code"] >= 500)
    print(f"   series: {[(p.attributes['http.route'], p.attributes['http.response.status_code'], p.count) for p in points]}")
    print(f"   Rate: {total} requests   Errors: {errors / total:.0%}   "
          f"Duration p95 <= {p95_from_buckets(points)} s (bucket upper bound)")
    assert total == 43 and 0.2 < errors / total < 0.35 and p95_from_buckets(points) >= 0.1

    print("\n== 6. the cardinality trap: label by raw path instead of route ==")
    bad = Service("bad-gateway", gateway_handler, route_label=False)
    for i in range(25):
        c = http.client.HTTPConnection("127.0.0.1", bad.port, timeout=5)
        c.request("GET", f"/checkout/{i}")
        c.getresponse().read()
        c.close()
    good_series = len({(p.attributes["http.route"], p.attributes["http.response.status_code"])
                       for p in histogram_points(SERVICES["gateway"])})
    bad_series = len(histogram_points(bad))
    print(f"   route label '/checkout/{{id}}': {good_series} series;  raw path label: {bad_series} series for 25 requests")
    print(f"   each series x {len(DURATION_BUCKETS) + 1} buckets; at a million users that is a metrics-bill incident")
    assert bad_series == 25 and good_series <= 3

    print("\n== 7. log lines carry the trace id ==")
    line = [l for l in log_stream.getvalue().splitlines() if "amount=950" in l][-1]
    print("   " + line)
    assert "trace=" in line and "trace=-" not in line

    print("\n== 8. head sampling at the edge: whole traces or nothing ==")
    SPANS.clear()
    SERVICES["gateway"] = Service("gateway", gateway_handler, sampler=ParentBased(TraceIdRatioBased(0.25)))
    for i in range(200):
        client_get(f"/checkout/{i % 100}")
    spans = SPANS.get_finished_spans()
    per_trace = {}
    for s in spans:
        per_trace.setdefault(s.context.trace_id, set()).add(s.resource.attributes["service.name"])
    complete = sum(1 for svcs in per_trace.values() if svcs == {"gateway", "orders", "payments"})
    print(f"   200 requests -> {len(per_trace)} traces kept ({len(per_trace) / 2:.0f}%), "
          f"{complete} of them complete across all three services")
    assert 25 <= len(per_trace) <= 80 and complete == len(per_trace)
    print("   orders and payments sample with ParentBased too: they obey flags=00/01, never re-decide.")
    print("   (keeping every ERROR trace needs TAIL sampling, in the Collector, after the trace ends)")

    for s in SERVICES.values():
        s.srv.shutdown()
    bad.srv.shutdown()
    print("\nOK")


if __name__ == "__main__":
    demo()
