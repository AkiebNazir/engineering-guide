# Designing Observable Code: Logs, Metrics, Traces, and Health

> "Observability is not the microscope. It's the clarity of the slide."
> — Baron Schwartz
>
> "You can't debug what you can't see — and you can't add visibility during the incident."

A system is **observable** when you can answer new questions about its behaviour — *why
is checkout slow for users in Brazil since 14:02?* — from the outside, **without
shipping new code.** That property is designed in, line by line, before the incident.

`SystemDesign/building_blocks/15` covers observability at the **platform** level: SLOs,
alerting, golden signals, incident response. This file covers the **code** level: what
an engineer writes into a function, a request handler, and a service so that the
platform has something worth collecting.

Examples are in **Python** with **Go** (`log/slog`) in §9. Every example was run; the
outputs shown are real (timestamps and random IDs removed where noted).

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| <abbr title="Service Level Indicator - A carefully defined quantitative measure of some aspect of the level of service that is provided, such as latency.">SLI</abbr>/<abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr>/error budgets, alert design, RED/USE, incident response | `SystemDesign/building_blocks/15_observability_and_reliability.md` |
| Cross-cutting concerns as middleware/decorators around ports | `08_application_architecture_in_code.md` §9 |
| Error context, "log once at the boundary" | `06_error_handling_and_failure_design.md` §3–§4 |
| Profiling and tracing tools hands-on | `PyEngineering/22_profiling_optimization`, `GoEngineering/35_profiling_and_tracing` |
| Canary, feature flags, rollback | `SystemDesign/building_blocks/15` |

---

## Contents

1. [The three signals, and which question each answers](#1--the-three-signals-and-which-question-each-answers)
2. [Structured logging](#2--structured-logging)
3. [What to log, at what level](#3--what-to-log-at-what-level)
4. [Metrics in code: types, names, labels](#4--metrics-in-code-types-names-labels)
5. [Tracing: spans and context propagation](#5--tracing-spans-and-context-propagation)
6. [Instrument the domain, not just the plumbing](#6--instrument-the-domain-not-just-the-plumbing)
7. [Health checks: liveness vs. readiness](#7--health-checks-liveness-vs-readiness)
8. [Designing for debuggability](#8--designing-for-debuggability)
9. [The same ideas in Go with slog](#9--the-same-ideas-in-go-with-slog)
10. [Cost, sampling, and privacy](#10--cost-sampling-and-privacy)
11. [Testing instrumentation](#11--testing-instrumentation)
12. [Red flags](#12--red-flags)
13. [Interview questions and model answers](#13--interview-questions-and-model-answers)
14. [Checklist](#14--checklist)

---

## 1 · The three signals, and which question each answers

| Signal | Unit | Answers | Cost profile | Example |
|---|---|---|---|---|
| **Metrics** | Numeric time series (name + labels → value) | *Is something wrong? How much? Since when?* | Cheap per event; cost grows with **label combinations** | `http_requests_total{route="/orders/{id}",status="5xx"}` |
| **Logs** | Discrete events with fields | *What exactly happened to this request/order/user?* | Cost grows with **volume** (every event is stored) | `{"msg":"charge declined","order_id":"o-42","reason":"insufficient_funds"}` |
| **Traces** | Tree of timed spans for one request across services | *Where did the time go? Which dependency failed?* | Usually **sampled**; cost grows with spans per request | `POST /checkout 840ms → payments.charge 790ms` |
| **Profiles** (the fourth) | Stack samples over time | *Which code is burning <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>/memory?* | Continuous, low-overhead sampling | pprof flame graph |

The debugging workflow uses them in sequence:

```arch
%% caption: The standard observability workflow moves from aggregate metrics down to specific traces, logs, and code.
node metric "ALERT (Metric)\n'p99 latency > 800ms'" at 0,0 icon=chart color=red
node slice "Slice by Labels\n'region=br, version=1.4'" at 2,0 icon=filter color=grey style=dashed
node trace "EXEMPLAR / TRACE\n'payments = 790ms'" at 0,1 icon=search color=yellow
node traceid "Follow trace_id" at 2,1 icon=link color=grey style=dashed
node log "LOGS (for trace_id)\n'retrying charge...'" at 0,2 icon=file color=blue
node code "PROFILE / CODE\n'connection pool exhausted'" at 0,3 icon=code color=green

metric -> trace : "slice\nby labels"
metric ..> slice : "insight"
trace -> log : "follow\ntrace_id"
trace ..> traceid : "insight"
log -> code
```

This only works if the three signals **share identifiers**: the same `route`, `version`,
and `region` labels on metrics and logs, and `trace_id` on every log line. That is a
code-design decision, not a tooling one.

---

## 2 · Structured logging

An unstructured log line is written for humans and parsed by regular expressions:

```
2026-09-17 14:02:11 ERROR Payment failed for order o-42 (user u-18): provider rejected
```

A structured log event is written for **queries**:

```json
{"level":"ERROR","msg":"payment failed","order_id":"o-42","user_id":"u-18",
 "provider":"acme","error.type":"ProviderRejected","request_id":"6fbab675","version":"1.4.2"}
```

Now `count by provider where msg="payment failed" and version="1.4.2"` is a query instead of a
regex that breaks when someone edits the sentence.

Design rules:

1. **The message is a constant; the variables are fields.** `log.info("payment failed",
   order_id=...)`, never `log.info(f"payment failed for {order_id}")`. Constant messages
   group, count, and alert cleanly.
2. **Request context is attached automatically**, not passed by hand to every call.
   `contextvars` in Python; `context.Context` in Go.
3. **Redaction is central**, in the formatter/handler — not a discipline every call site
   must remember.
4. **Tracebacks are logged once**, at the boundary (`06` §3).
5. **Field names are consistent across services** — adopt a convention (OpenTelemetry
   semantic conventions: `http.request.method`, `error.type`, `user.id`) so queries work
   fleet-wide.

The whole idea in five lines, before the production-shaped version below:

```python
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("demo")


def log_event(msg: str, **fields) -> None:
    log.info(json.dumps({"msg": msg, **fields}))


log_event("order placed", order_id="o-1", amount_cents=1200)
log_event("order placed", order_id="o-2", amount_cents=90000)
```

Output:

```
{"msg": "order placed", "order_id": "o-1", "amount_cents": 1200}
{"msg": "order placed", "order_id": "o-2", "amount_cents": 90000}
```

Constant message, variable fields, one <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> object per line — that's the whole idea. A
real service adds the parts below: request context attached automatically instead of
passed by hand, central redaction, and the traceback logged once at the boundary.

```python
# Structured logging: one JSON object per event, request context attached automatically,
# secrets redacted centrally, and the traceback logged once at the boundary.
import contextvars
import io
import json
import logging
import uuid

request_ctx: contextvars.ContextVar[dict] = contextvars.ContextVar("request_ctx", default={})

SENSITIVE_KEYS = {"password", "token", "authorization", "card_number", "secret"}


def redact(value):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if k.lower() in SENSITIVE_KEYS else redact(v)
                for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        event = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            **request_ctx.get(),                               # request_id, user_id, route...
            **redact(getattr(record, "fields", {})),           # event-specific fields
        }
        if record.exc_info:
            event["error.type"] = record.exc_info[0].__name__
            event["error.stack"] = self.formatException(record.exc_info)
        return json.dumps(event, default=str)


def get_logger(name: str, stream) -> logging.Logger:
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    logger.handlers[:] = [handler]
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


# ---------------- application code ----------------
out = io.StringIO()
log = get_logger("checkout", out)


def charge(order_id: str, cents: int, card: dict) -> None:
    log.info("charge requested", extra={"fields": {"order_id": order_id, "amount_cents": cents,
                                                   "card": card}})
    if cents > 50_000:
        raise RuntimeError("provider rejected: amount over limit")


def handle_request(route: str, user_id: str, body: dict) -> int:
    token = request_ctx.set({"request_id": uuid.uuid4().hex[:8], "route": route, "user_id": user_id})
    try:
        charge(body["order_id"], body["cents"], body["card"])
        log.info("request completed", extra={"fields": {"status": 200}})
        return 200
    except Exception:
        log.exception("request failed", extra={"fields": {"status": 500}})   # boundary: once
        return 500
    finally:
        request_ctx.reset(token)


if __name__ == "__main__":
    handle_request("POST /checkout", "u-17", {"order_id": "o-1", "cents": 1200,
                                               "card": {"card_number": "4242424242424242", "exp": "12/29"}})
    handle_request("POST /checkout", "u-18", {"order_id": "o-2", "cents": 90_000,
                                               "card": {"card_number": "4000000000000002", "exp": "01/30"}})
    lines = [json.loads(l) for l in out.getvalue().splitlines()]
    for l in lines:
        l.pop("ts"); l.pop("error.stack", None)
        print(l)
    assert "4242" not in out.getvalue()                              # no card numbers anywhere
    assert lines[0]["request_id"] == lines[1]["request_id"] != lines[2]["request_id"]
    assert lines[3]["error.type"] == "RuntimeError" and lines[3]["user_id"] == "u-18"
    assert sum("error.type" in l for l in lines) == 1                # traceback logged once
    print("ALL PASSED")
```

Output (`ts` and `error.stack` removed for display; request IDs are random):

```
{'level': 'INFO', 'logger': 'checkout', 'msg': 'charge requested', 'request_id': '08a5c22e', 'route': 'POST /checkout', 'user_id': 'u-17', 'order_id': 'o-1', 'amount_cents': 1200, 'card': {'card_number': '[REDACTED]', 'exp': '12/29'}}
{'level': 'INFO', 'logger': 'checkout', 'msg': 'request completed', 'request_id': '08a5c22e', 'route': 'POST /checkout', 'user_id': 'u-17', 'status': 200}
{'level': 'INFO', 'logger': 'checkout', 'msg': 'charge requested', 'request_id': '6fbab675', 'route': 'POST /checkout', 'user_id': 'u-18', 'order_id': 'o-2', 'amount_cents': 90000, 'card': {'card_number': '[REDACTED]', 'exp': '01/30'}}
{'level': 'ERROR', 'logger': 'checkout', 'msg': 'request failed', 'request_id': '6fbab675', 'route': 'POST /checkout', 'user_id': 'u-18', 'status': 500, 'error.type': 'RuntimeError'}
ALL PASSED
```

What the design buys:

- `charge()` never mentions `request_id` or `user_id`, yet every line it writes has them
  — so all lines for one request can be pulled with one query.
- The card number never reaches the output, even though a careless call site logged the
  whole `card` dict. Redaction by **key allow/deny list at the formatter** is a safety net;
  the better first defence is not logging whole objects (§10).
- The failed request produced exactly one line with an error type — the boundary log.

In production use a library (`structlog`, `python-json-logger`, OpenTelemetry logging)
rather than a hand-written formatter; the design — context vars, constant messages,
central redaction — is the same.

---

## 3 · What to log, at what level

### Levels mean actions

| Level | Means | Who acts | Example |
|---|---|---|---|
| **ERROR** | A request/job failed and the system could not recover | Someone should look (often via a metric alert, not the log itself) | Unhandled exception at the boundary; data inconsistency detected |
| **WARN** | Something unexpected, handled, but a trend would be a problem | Nobody now; dashboards | Retry succeeded on attempt 3; fallback used; deprecated <abbr title="Application Programming Interface">API</abbr> called |
| **INFO** | Significant business or lifecycle events | Nobody; used for investigation | Service started with config hash; order placed; job completed |
| **DEBUG** | Detail useful while developing or diagnosing one component | Off in production, or on dynamically per request/module | <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> text, cache hit/miss per key |

The most common failure is **everything at ERROR**: expected outcomes (a user typed a
wrong password, a 404 for a missing resource) logged as errors. Then the error rate on a
dashboard means nothing, and real errors drown. **A client's mistake is not your error** —
log 4xx at INFO or not at all, and count them in a metric.

### Log these

| Event | Fields |
|---|---|
| Startup | version, commit, config hash (not secrets), feature flags, listening port |
| Shutdown | reason (signal), in-flight requests drained, duration |
| Request completion (access log) | route template, status, duration, request/trace ID, user/tenant ID, bytes |
| State transitions of important entities | entity ID, from → to, actor |
| Decisions with business consequences | "order held for fraud review", rule ID, score |
| External calls that failed or were retried | dependency, attempt, error type, duration |
| Recovery actions | fallback used, circuit opened/closed, cache rebuilt |
| Security-relevant events (to an **audit** log) | who, what, when, from where, outcome |

### Don't log these

- **Secrets and credentials:** passwords, tokens, <abbr title="Application Programming Interface">API</abbr> keys, session cookies,
  `Authorization` headers, connection strings.
- **Personal data you don't need:** full names, emails, addresses, card numbers, message
  bodies. Log the **ID** instead; the data is one lookup away for someone authorised.
- **Whole request/response bodies** by default.
- **Inside tight loops:** one line per item in a million-item batch. Log a summary
  (`processed=1000000 failed=12 duration_s=41`) and the failures.
- **Success of every cache lookup / DB query** at INFO.

### Audit logs are a different product

| | Debug/operational logs | Audit logs |
|---|---|---|
| Purpose | Diagnose the system | Prove who did what (security, compliance) |
| Retention | Days–weeks | Months–years, per regulation |
| Integrity | Best effort; may be sampled | Complete, append-only, tamper-evident |
| Access | Engineers | Restricted; access itself audited |
| In code | Logger | Explicit call (`audit.record(actor, action, resource, outcome)`), often written in the same transaction as the change |

Never implement an audit trail by grepping debug logs.

---

## 4 · Metrics in code: types, names, labels

### Types

| Type | What it is | Use for | Don't |
|---|---|---|---|
| **Counter** | Monotonically increasing total | Requests, errors, bytes, jobs processed | Decrement it; use it for "current" values |
| **Gauge** | A value that goes up and down | Queue depth, in-flight requests, pool size, temperature | Use for things you want rates of |
| **Histogram** | Counts in predefined buckets + sum + count | Latency, payload size — anything where **percentiles** matter | Use a gauge of "last latency" or an average |
| **Summary** | Client-side quantiles | Rarely; quantiles can't be aggregated across instances | Aggregate p99s by averaging them |

**Why histograms, not averages:** averages hide the tail, and the tail is what users feel.

Counters and gauges, minimal — before the histogram and cardinality guard below:

```python
from collections import Counter

requests_total = Counter()          # counter: only ever goes up
in_flight = 0                       # gauge: goes up and down


def start_request() -> None:
    global in_flight
    in_flight += 1
    print("in_flight now:", in_flight)


def finish_request(status_class: str) -> None:
    global in_flight
    in_flight -= 1
    requests_total[status_class] += 1
    print("in_flight now:", in_flight)


for code in [200, 200, 404]:
    start_request()
for code in [200, 200, 404]:
    finish_request(f"{code // 100}xx")

print("counter:", dict(requests_total))
```

Output:

```
in_flight now: 1
in_flight now: 2
in_flight now: 3
in_flight now: 2
in_flight now: 1
in_flight now: 0
counter: {'2xx': 2, '4xx': 1}
```

`in_flight` needs both directions — a counter can't represent it, because a counter
never goes down. That's the type distinction in the table above, in code. A real
metrics client makes both thread-safe and exports them; the example below adds the third
type (histograms) and the cardinality guard every counter/gauge implementation needs.

```python
# Metrics in code: counters, histograms with fixed buckets, and a guard against label explosion.
import bisect
import threading
from collections import defaultdict


class CardinalityError(Exception): ...


class Registry:
    def __init__(self, max_series_per_metric: int = 100):
        self._lock = threading.Lock()
        self._counters: dict[tuple, float] = defaultdict(float)
        self._hists: dict[tuple, list[int]] = {}
        self._hist_sums: dict[tuple, float] = defaultdict(float)
        self._buckets: dict[str, list[float]] = {}
        self._series: dict[str, set] = defaultdict(set)
        self._max = max_series_per_metric

    def _key(self, name: str, labels: dict[str, str]) -> tuple:
        key = (name, tuple(sorted(labels.items())))
        series = self._series[name]
        if key not in series:
            if len(series) >= self._max:
                raise CardinalityError(f"{name}: more than {self._max} label combinations")
            series.add(key)
        return key

    def inc(self, name: str, value: float = 1, **labels: str) -> None:
        with self._lock:
            self._counters[self._key(name, labels)] += value

    def define_histogram(self, name: str, buckets: list[float]) -> None:
        self._buckets[name] = sorted(buckets)

    def observe(self, name: str, value: float, **labels: str) -> None:
        with self._lock:
            key = self._key(name, labels)
            bounds = self._buckets[name]
            counts = self._hists.setdefault(key, [0] * (len(bounds) + 1))   # last = +Inf
            counts[bisect.bisect_left(bounds, value)] += 1
            self._hist_sums[key] += value

    def quantile(self, name: str, q: float, **labels: str) -> float:
        """Upper bound of the bucket containing the q-quantile (what dashboards estimate)."""
        counts = self._hists[(name, tuple(sorted(labels.items())))]
        target, running = q * sum(counts), 0
        for bound, c in zip(self._buckets[name] + [float("inf")], counts):
            running += c
            if running >= target:
                return bound
        return float("inf")

    def counter(self, name: str, **labels: str) -> float:
        return self._counters[(name, tuple(sorted(labels.items())))]


def status_class(code: int) -> str:
    return f"{code // 100}xx"                     # bounded: 5 values, not 60


if __name__ == "__main__":
    m = Registry(max_series_per_metric=50)
    m.define_histogram("http_request_duration_seconds", [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5])

    latencies = [0.004] * 975 + [0.03] * 10 + [0.8] * 14 + [3.0]      # 1,000 requests
    for i, lat in enumerate(latencies):
        code = 500 if lat >= 3.0 else 200
        m.inc("http_requests_total", route="/orders/{id}", status=status_class(code))
        m.observe("http_request_duration_seconds", lat, route="/orders/{id}")

    mean = sum(latencies) / len(latencies)
    p50 = m.quantile("http_request_duration_seconds", 0.50, route="/orders/{id}")
    p99 = m.quantile("http_request_duration_seconds", 0.99, route="/orders/{id}")
    p999 = m.quantile("http_request_duration_seconds", 0.999, route="/orders/{id}")
    print(f"mean={mean:.4f}s  p50<={p50}s  p99<={p99}s  p99.9<={p999}s")
    print("5xx:", m.counter("http_requests_total", route="/orders/{id}", status="5xx"))
    assert p50 == 0.005 and p99 == 1 and p999 == 1 and mean < 0.02

    try:
        for user in range(1_000):                  # BAD: unbounded label value
            m.inc("logins_total", user_id=f"u{user}")
    except CardinalityError as e:
        print("rejected:", e)
    print("ALL PASSED")
```

Output:

```
mean=0.0184s  p50<=0.005s  p99<=1s  p99.9<=1s
5xx: 1.0
rejected: logins_total: more than 50 label combinations
ALL PASSED
```

The mean (18 ms) says the service is fast. The p99 says 1 in 100 requests takes up to a
second — and a page that makes 20 backend calls hits that tail on ~18% of page loads
(`1 − 0.99²⁰`).

Histogram design notes:

- **Bucket boundaries are part of the <abbr title="Application Programming Interface">API</abbr>.** Choose them around your <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> (if the target is
  300 ms, have a bucket boundary at 0.3). Changing buckets later breaks historical
  comparisons.
- Percentiles from histograms are **estimates bounded by bucket edges** ("≤ 1 s"). Native
  / exponential histograms (Prometheus native histograms, OpenTelemetry exponential
  histograms) give finer resolution automatically.
- **Histograms aggregate across instances correctly** (sum the buckets); per-instance
  p99s cannot be averaged into a fleet p99.

### Naming

Prometheus/OpenMetrics conventions, widely adopted:

- `snake_case`, with the **unit as a suffix** in base units: `_seconds`, `_bytes`,
  `_total` for counters. `http_request_duration_seconds`, not `http_latency_ms`.
- Name the **thing measured**, not the code: `orders_placed_total`, not
  `place_order_func_calls`.
- Let labels, not names, distinguish variants: `http_requests_total{status="5xx"}`, not
  `http_5xx_total`.

### Labels and cardinality — the expensive mistake

Every unique combination of label values is a **separate time series** stored forever
(until retention). Series count = product of label cardinalities.

```
route (40) × status class (5) × method (4) × region (6)   =     4,800 series   fine
… × user_id (2,000,000)                                    = 9.6 billion series   outage
```

| Safe label values (bounded, small) | Unsafe (unbounded) — put in logs/traces instead |
|---|---|
| Route **template** `/orders/{id}` | Raw path `/orders/8f3a…` |
| Status class `2xx`/`4xx`/`5xx`, or status code | Error **message** text |
| Method, region, version, dependency name | User ID, order ID, email, <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> address |
| Error **type** from a closed enum | Request ID, trace ID, timestamps |

The `CardinalityError` guard in the example is a pattern worth having in a shared metrics
wrapper: fail loudly in tests rather than silently in the metrics bill.

### What to measure in every service

| Where | Metrics |
|---|---|
| Every inbound endpoint (**RED**) | Rate (`_requests_total`), Errors (by status class), Duration (histogram) |
| Every outbound dependency | Same RED set, labelled by `dependency` — your view of *their* health |
| Every resource pool / queue (**USE**) | Utilisation (in use / max), Saturation (waiters, queue depth), Errors (acquire timeouts) |
| Every background job / consumer | Items processed, failures, **lag** (age of oldest unprocessed item), last success timestamp |
| Every cache | Hits, misses, evictions, size |
| Runtime | <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr> pauses, heap, threads/goroutines, open FDs (usually from the client library) |

"Last success timestamp" deserves emphasis: a cron job that silently stops running
produces **no errors at all**. Alert on `time() - job_last_success_timestamp_seconds > 2h`.

---

## 5 · Tracing: spans and context propagation

A **trace** is the tree of work done for one request. Each node is a **span**: a name,
start, duration, attributes, status, and a parent. Propagating the trace and parent IDs
across process boundaries (the W3C `traceparent` <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> header) stitches spans from many
services into one tree.

A span is just an id, a name, a parent id, and a duration — before context propagation
across processes enters the picture:

```python
import itertools
import time

_next_id = itertools.count(1)


def start_span(name: str, parent_id: int | None = None) -> dict:
    return {"id": next(_next_id), "name": name, "parent_id": parent_id, "start": time.perf_counter()}


def end_span(span: dict) -> dict:
    span["duration_ms"] = (time.perf_counter() - span["start"]) * 1000
    return span


root = start_span("checkout")
child = start_span("charge", parent_id=root["id"])
time.sleep(0.01)
end_span(child)
end_span(root)

print(f"{root['name']:<10} id={root['id']} parent={root['parent_id']}  {root['duration_ms']:5.1f} ms")
print(f"  {child['name']:<8} id={child['id']} parent={child['parent_id']}  {child['duration_ms']:5.1f} ms")
```

Output (duration varies slightly between runs):

```
checkout   id=1 parent=None   10.2 ms
  charge   id=2 parent=1   10.2 ms
```

`child["parent_id"] == root["id"]` is the entire mechanism a tracing backend uses to
rebuild the tree — everything below adds the piece that makes this work across an
in-process call stack *and* across a network call: an implicit current span (via
`contextvars`, so callers don't pass span objects around) and a header that carries the
IDs to the next process.

```python
# Tracing in code: spans nest via contextvars and cross process boundaries via a header.
import contextvars
import secrets
import time
from contextlib import contextmanager
from dataclasses import dataclass, field

_current: contextvars.ContextVar["Span | None"] = contextvars.ContextVar("span", default=None)
FINISHED: list["Span"] = []                         # stands in for an exporter (OTLP, Jaeger)


@dataclass
class Span:
    name: str
    trace_id: str
    span_id: str
    parent_id: str | None
    attrs: dict = field(default_factory=dict)
    start: float = 0.0
    duration_ms: float = 0.0
    status: str = "ok"


@contextmanager
def span(name: str, **attrs):
    parent = _current.get()
    s = Span(name,
             trace_id=parent.trace_id if parent else secrets.token_hex(16),
             span_id=secrets.token_hex(8),
             parent_id=parent.span_id if parent else None,
             attrs=attrs, start=time.perf_counter())
    token = _current.set(s)
    try:
        yield s
    except Exception as e:
        s.status, s.attrs["error"] = "error", repr(e)
        raise
    finally:
        s.duration_ms = (time.perf_counter() - s.start) * 1000
        _current.reset(token)
        FINISHED.append(s)


def inject() -> dict[str, str]:
    """W3C Trace Context header for an outgoing call."""
    s = _current.get()
    return {"traceparent": f"00-{s.trace_id}-{s.span_id}-01"} if s else {}


@contextmanager
def continue_trace(headers: dict[str, str], name: str):
    """Server side: make the caller's span the parent of ours."""
    _, trace_id, parent_span, _ = headers["traceparent"].split("-")
    remote = Span("remote-parent", trace_id, parent_span, None)
    token = _current.set(remote)
    try:
        with span(name) as s:
            yield s
    finally:
        _current.reset(token)


# ---------------- two "services" ----------------
def inventory_service(headers: dict, sku: str) -> int:
    with continue_trace(headers, "inventory.reserve") as s:
        s.attrs["sku"] = sku
        with span("db.update", table="stock"):
            time.sleep(0.02)
        return 1


def checkout(order_id: str) -> None:
    with span("POST /checkout", order_id=order_id):
        with span("pricing.compute"):
            time.sleep(0.005)
        with span("http.call", peer="inventory"):
            inventory_service(inject(), "A-17")          # headers cross the "network"
        with span("payments.charge"):
            time.sleep(0.01)


if __name__ == "__main__":
    checkout("o-42")
    by_id = {s.span_id: s for s in FINISHED}
    def depth(s):
        d = 0
        while s.parent_id in by_id:
            s, d = by_id[s.parent_id], d + 1
        return d
    for s in sorted(FINISHED, key=lambda s: s.start):
        print(f"{'  ' * depth(s) + s.name:<26} {s.duration_ms:6.1f} ms  {s.attrs}")
    assert len({s.trace_id for s in FINISHED}) == 1                  # one trace across both services
    assert by_id[next(s for s in FINISHED if s.name == "inventory.reserve").parent_id].name == "http.call"
    print("ALL PASSED")
```

Output (durations vary slightly between runs):

```
POST /checkout               43.9 ms  {'order_id': 'o-42'}
  pricing.compute             6.3 ms  {}
  http.call                  25.1 ms  {'peer': 'inventory'}
    inventory.reserve        25.0 ms  {'sku': 'A-17'}
      db.update              25.0 ms  {'table': 'stock'}
  payments.charge            12.5 ms  {}
ALL PASSED
```

What this toy tracer shows about the real thing (OpenTelemetry):

- **Parenting is implicit** through a context variable, exactly like request-scoped log
  fields. Application code opens spans; it never passes span objects around.
- **Propagation is explicit at process boundaries:** `inject()` writes headers on the
  client; `continue_trace()` reads them on the server. Every <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> client, <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> stub, and
  queue producer/consumer needs this — **message queues included**, or async work shows up
  as disconnected traces. Put the headers in message metadata.
- **Errors mark the span** and re-raise; the span doesn't swallow anything.
- **The gap is information:** `POST /checkout` took 43.9 ms, children sum to ~44 ms, so no
  time is unaccounted for. A large gap between a parent and the sum of its children means
  uninstrumented work (often lock waits or serialisation).

### Where to put spans

| Instrument | Why |
|---|---|
| Inbound request (automatic via framework middleware) | Root of the tree |
| Every outbound call: <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>, <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr>, DB, cache, queue (automatic via client instrumentation) | Where latency usually lives |
| Significant internal steps a human would name ("pricing.compute", "fraud.score") | Distinguishes your time from dependency time |
| **Not** every function | Span overhead and noise; use a profiler for function-level detail |

**Span attributes vs. metric labels:** spans can carry high-cardinality attributes
(`order_id`, `user_id`, `sku`) because traces are sampled and stored per request. Put the
IDs you'd search by on spans, never on metrics.

**Exemplars** link the two: a histogram bucket stores a sample `trace_id` of a request that
fell into it, so you can click from "the p99 spiked" straight to a slow trace.

---

## 6 · Instrument the domain, not just the plumbing

Automatic instrumentation tells you that `POST /checkout` returned 200 in 300 ms. It
cannot tell you that 30% of those 200s were **orders held for fraud review**, or that the
**checkout conversion rate** halved after a deploy. Only the domain knows that.

Technical health and business health diverge more often than expected: a bug that
silently skips applying discounts produces no errors and no latency change.

Approach: let the domain **record events** (`08` §4.1 `OrderPaid`), and let an outer
handler turn them into metrics, logs, and analytics — the domain never imports a metrics
client.

```python
@dataclass(frozen=True)
class OrderHeldForReview:
    order_id: str
    rule_id: str
    score: float

class ObservabilityEventHandler:
    """Adapter: domain events → signals. The domain doesn't know this exists."""
    def __init__(self, metrics, log):
        self._metrics, self._log = metrics, log

    def handle(self, event) -> None:
        match event:
            case OrderPaid(order_id, amount):
                self._metrics.inc("orders_paid_total", currency=amount.currency)
                self._metrics.inc("revenue_cents_total", amount.cents, currency=amount.currency)
            case OrderHeldForReview(order_id, rule_id, score):
                self._metrics.inc("orders_held_total", rule=rule_id)   # rule_id: bounded set
                self._log.info("order held for review",
                               extra={"fields": {"order_id": order_id, "rule_id": rule_id,
                                                 "score": score}})
```

Business-level signals worth having for any core flow:

- **Throughput of the business outcome** (orders paid per minute), not just requests.
- **Funnel ratios** (carts → checkouts → payments succeeded).
- **Decision distributions** (fraud holds by rule, recommendations served vs. fallback).
- **Money and quantity invariants** (sum of ledger entries = 0, alert if not).

An alert on "orders paid per minute dropped 50% compared with the same time last week"
catches whole classes of bugs that no error-rate alert can.

---

## 7 · Health checks: liveness vs. readiness

Orchestrators (Kubernetes, load balancers) ask two different questions, and conflating
them causes outages.

| Probe | Question | On failure the orchestrator… | Should check |
|---|---|---|---|
| **Liveness** | Is this process wedged beyond self-repair? | **Restarts** the container | Only in-process health: the event loop responds, no deadlock detected |
| **Readiness** | Should this instance receive traffic right now? | **Removes it from the load balancer** (no restart) | Startup finished (caches warm, migrations checked), critical dependencies reachable, not draining |
| **Startup** (k8s) | Has slow initialisation finished? | Delays the other probes | Same as readiness's "started" part |

```python
# Health checks: liveness says "restart me?", readiness says "send me traffic?".
import time
from dataclasses import dataclass
from typing import Callable


@dataclass
class Check:
    name: str
    probe: Callable[[], None]          # raises on failure
    critical: bool                     # if False, failure degrades but doesn't remove from LB


class Health:
    def __init__(self, checks: list[Check], started: Callable[[], bool], timeout_s: float = 0.5):
        self._checks, self._started, self._timeout = checks, started, timeout_s
        self.draining = False

    def liveness(self) -> tuple[int, dict]:
        # Only "is this process wedged?" — NEVER dependencies. A DB outage must not
        # make the orchestrator restart every replica at once.
        return 200, {"status": "alive"}

    def readiness(self) -> tuple[int, dict]:
        if not self._started() or self.draining:
            return 503, {"status": "starting" if not self._started() else "draining"}
        results, ready = {}, True
        for c in self._checks:
            t = time.perf_counter()
            try:
                c.probe()
                ok = (time.perf_counter() - t) <= self._timeout
                results[c.name] = "ok" if ok else "slow"
            except Exception as e:
                ok, results[c.name] = False, f"fail: {e}"
            ready &= ok or not c.critical
        return (200 if ready else 503), {"status": "ready" if ready else "not_ready", "checks": results}


if __name__ == "__main__":
    db_up, recs_up, warmed = [True], [True], [False]
    def db():   assert db_up[0], "connection refused"
    def recs(): assert recs_up[0], "timeout"
    h = Health([Check("db", db, critical=True), Check("recommender", recs, critical=False)],
               started=lambda: warmed[0])

    print("boot      ", h.readiness())
    warmed[0] = True
    print("warm      ", h.readiness())
    recs_up[0] = False
    print("recs down ", h.readiness())
    db_up[0] = False
    print("db down   ", h.readiness(), "liveness:", h.liveness())
    db_up[0], h.draining = True, True
    print("SIGTERM   ", h.readiness())
    assert h.liveness()[0] == 200 and h.readiness()[0] == 503
    print("ALL PASSED")
```

Output:

```
boot       (503, {'status': 'starting'})
warm       (200, {'status': 'ready', 'checks': {'db': 'ok', 'recommender': 'ok'}})
recs down  (200, {'status': 'ready', 'checks': {'db': 'ok', 'recommender': 'fail: timeout'}})
db down    (503, {'status': 'not_ready', 'checks': {'db': 'fail: connection refused', 'recommender': 'fail: timeout'}}) liveness: (200, {'status': 'alive'})
SIGTERM    (503, {'status': 'draining'})
ALL PASSED
```

The mistakes this design avoids:

1. **Dependency checks in liveness.** When the database blips, every replica fails
   liveness, Kubernetes restarts all of them simultaneously, they all reconnect at once
   during cold start, and a 10-second blip becomes a 10-minute outage.
2. **Non-critical dependencies in readiness.** If the recommender being down removed every
   instance from the load balancer, a nice-to-have feature would take down checkout. Degrade
   instead (`06` §10).
3. **Ready before warm.** Receiving traffic before caches load or connections open causes
   a latency spike on every deploy.
4. **No draining.** On `SIGTERM`, flip readiness to failing first, keep serving in-flight
   requests while the load balancer notices, then exit — otherwise each deploy drops
   requests.
5. **Expensive checks.** Probes run every few seconds on every instance; a readiness check
   that runs `SELECT count(*)` on a big table is a self-inflicted load test. Use `SELECT 1`,
   cache results for a few seconds, and time-bound each check.

Caveat on readiness dependency checks: if a *shared* critical dependency is down, every
instance goes unready and the load balancer has nowhere to send traffic — clients get
connection errors instead of a clear 503. Some teams therefore check only local readiness
and let requests fail fast with a proper error. Either is defensible; make it a decision.

---

## 8 · Designing for debuggability

Things to build in before you need them:

| Capability | Implementation |
|---|---|
| **Know exactly what's running** | `/buildinfo` or a startup log + a `build_info{version,commit}` gauge = 1. Label request metrics with `version` so a bad deploy shows as a split. |
| **Know the effective configuration** | Log a config summary (and hash) at startup, secrets excluded; expose feature-flag state per request in the trace. |
| **Correlate a user report to data** | Return the request/trace ID in a response header (`X-Request-ID`) and in error pages: "Error reference: 6fbab675". Support can hand you the exact trace. |
| **Change verbosity without a deploy** | Dynamic log levels per module, or DEBUG for one request via a header/flag honoured only for internal users. |
| **Inspect live internal state** | Admin endpoints (auth-protected, not public): pool stats, cache sizes, circuit-breaker state, queue depths. Go's `net/http/pprof` and `expvar`. |
| **Reproduce a failure** | Record enough input to replay: the message ID and payload location, the idempotency key, the feature flags evaluated. |
| **Error IDs that group** | A stable `error.type` / error code (`06` §4), so dashboards count kinds of failure rather than distinct messages. |
| **Timestamps you can trust** | UTC everywhere, ISO 8601 with offset, monotonic clocks for durations (`time.perf_counter`, Go's `time.Since`). |

---

## 9 · The same ideas in Go with slog

Go 1.21's `log/slog` is structured logging in the standard library. The idioms:
attributes as key-value pairs, `*Context` methods so handlers can read request scope,
`With` for fixed fields, and `LogValuer` for types that control their own representation.

```go
package main

import (
	"context"
	"errors"
	"log/slog"
	"os"
)

// A slog.Handler wrapper that copies request-scoped attributes from the context onto
// every record — so application code never has to pass request_id around by hand.
type ctxKey struct{}

func WithAttrs(ctx context.Context, attrs ...slog.Attr) context.Context {
	existing, _ := ctx.Value(ctxKey{}).([]slog.Attr)
	return context.WithValue(ctx, ctxKey{}, append(append([]slog.Attr{}, existing...), attrs...))
}

type contextHandler struct{ slog.Handler }

func (h contextHandler) Handle(ctx context.Context, r slog.Record) error {
	if attrs, ok := ctx.Value(ctxKey{}).([]slog.Attr); ok {
		r.AddAttrs(attrs...)
	}
	return h.Handler.Handle(ctx, r)
}

func (h contextHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
	return contextHandler{h.Handler.WithAttrs(attrs)}
}

func (h contextHandler) WithGroup(name string) slog.Handler {
	return contextHandler{h.Handler.WithGroup(name)}
}

// Secret implements slog.LogValuer: it can never be printed, even by accident.
type Secret string

func (Secret) LogValue() slog.Value { return slog.StringValue("[REDACTED]") }

var errDeclined = errors.New("card declined")

func charge(ctx context.Context, log *slog.Logger, orderID string, cents int64, token Secret) error {
	log.InfoContext(ctx, "charge requested", "order_id", orderID, "amount_cents", cents, "card_token", token)
	if cents > 50_000 {
		return errDeclined
	}
	return nil
}

func handle(ctx context.Context, log *slog.Logger, requestID, userID string, cents int64) int {
	ctx = WithAttrs(ctx, slog.String("request_id", requestID), slog.String("user_id", userID))
	if err := charge(ctx, log, "o-"+requestID, cents, Secret("tok_live_abc123")); err != nil {
		log.ErrorContext(ctx, "request failed", "status", 402, "err", err) // logged once, at the edge
		return 402
	}
	log.InfoContext(ctx, "request completed", "status", 200)
	return 200
}

func main() {
	opts := &slog.HandlerOptions{
		Level: slog.LevelInfo,
		ReplaceAttr: func(_ []string, a slog.Attr) slog.Attr {
			if a.Key == slog.TimeKey {
				return slog.Attr{} // dropped only to keep this demo's output stable
			}
			return a
		},
	}
	log := slog.New(contextHandler{slog.NewJSONHandler(os.Stdout, opts)}).With("service", "checkout", "version", "1.4.2")
	handle(context.Background(), log, "r1", "u-17", 1200)
	handle(context.Background(), log, "r2", "u-18", 90_000)
}
```

Output:

```
{"level":"INFO","msg":"charge requested","service":"checkout","version":"1.4.2","order_id":"o-r1","amount_cents":1200,"card_token":"[REDACTED]","request_id":"r1","user_id":"u-17"}
{"level":"INFO","msg":"request completed","service":"checkout","version":"1.4.2","status":200,"request_id":"r1","user_id":"u-17"}
{"level":"INFO","msg":"charge requested","service":"checkout","version":"1.4.2","order_id":"o-r2","amount_cents":90000,"card_token":"[REDACTED]","request_id":"r2","user_id":"u-18"}
{"level":"ERROR","msg":"request failed","service":"checkout","version":"1.4.2","status":402,"err":"card declined","request_id":"r2","user_id":"u-18"}
```

Design points:

- **`Secret` redacts itself.** Making the type responsible (via `LogValuer`) beats a
  deny-list of key names: it works whatever the key is called, in every handler. (Also
  implement `String()`/`GoString()` if the value might be printed with `fmt`.)
- **The handler wrapper** reads request attributes from `context.Context`, so `charge`
  doesn't take `requestID` as a parameter. This only works if code calls the `*Context`
  variants (`InfoContext`) — enforce it with the `sloglint` linter.
- **`With("service", …, "version", …)`** attaches process-level fields once.
- In real services, the OpenTelemetry slog bridge adds `trace_id`/`span_id` the same way.

---

## 10 · Cost, sampling, and privacy

Telemetry is not free. At scale, the observability bill rivals compute, and telemetry
pipelines have their own outages.

| Lever | How | Trade-off |
|---|---|---|
| **Log levels** | INFO in prod; DEBUG on demand | Missing detail during the first occurrence |
| **Summarise loops** | One line per batch, plus failures | Less per-item detail |
| **Rate-limit repeated logs** | Log the first N per minute of an identical event, then a count | Hides volume unless the count is logged |
| **Head sampling (traces)** | Decide at the root: keep 1% of traces | May miss the rare slow/failed request |
| **Tail sampling (traces)** | Buffer spans, keep all errors and slow traces + a small % of the rest | Collector must buffer; more infrastructure |
| **Metrics over logs for counting** | Count in a counter, not by counting log lines | Metrics can't answer per-entity questions |
| **Drop high-cardinality labels** | IDs to logs/traces | §4 |

**Sampling must be consistent across a trace:** the sampling decision travels in the
`traceparent` flags so every service keeps or drops the same trace. Logs can carry
`trace_id` either way.

### Privacy by design

- **Log identifiers, not personal data.** `user_id=u-18` is enough to investigate;
  the email address is not needed in a log that 200 engineers can read.
- **Types that can't be logged** (`Secret` in §9, a `SensitiveStr` whose `__repr__`
  returns `[REDACTED]` in Python) are more reliable than reviewer vigilance.
- **Scrub at the boundary too:** framework access logs and <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> client debug logging
  capture headers (`Authorization`, cookies) and query strings (`?token=`).
- **Retention and deletion apply to telemetry.** A GDPR deletion request covers personal
  data in logs; the less you log, the less there is to find and delete.
- **Exceptions carry data.** `ValueError(f"invalid email {email}")` puts the email in
  every log that records the error. Keep messages about *what* was invalid, not the value,
  for sensitive fields.

---

## 11 · Testing instrumentation

Instrumentation is code that runs in production; broken instrumentation is discovered
during the incident it was meant to help with. Test the parts that matter:

| Test | How |
|---|---|
| **Critical logs are emitted with required fields** | Capture output (`caplog` in pytest, a `bytes.Buffer` handler in Go); assert on parsed <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> fields, not on message strings |
| **Secrets never appear** | Run a request containing a canary secret through the full stack; assert the canary is absent from all captured output (as §2's example does) |
| **Metrics change as expected** | Use an isolated registry per test; assert counter deltas after an operation |
| **Cardinality is bounded** | Metric wrapper rejects unknown label values in tests (§4) |
| **Trace context propagates** | Call client → server in-process; assert both spans share a trace ID and the parent link (as §5's example does) |
| **Health endpoints reflect state** | Toggle fake dependencies; assert status codes (as §7's example does) |
| **Alerts actually fire** | Prometheus rule unit tests (`promtool test rules`); game days |

```python
def test_declined_charge_is_counted_and_logged_once(caplog):
    metrics = Registry()
    app = build_app(metrics=metrics, payments=FakePayments(decline_over_cents=0))

    status = app.post("/checkout", json={"order_id": "o-1", "cents": 500})

    assert status == 402
    assert metrics.counter("payments_declined_total", provider="fake") == 1
    errors = [r for r in caplog.records if r.levelname == "ERROR"]
    assert errors == []                     # a decline is a business outcome, not an ERROR
```

---

## 12 · Red flags

| Red flag | Why it hurts | Fix |
|---|---|---|
| `log.info(f"user {uid} did {x}")` | Unqueryable; every message unique | Constant message + fields |
| `print()` in service code | No level, no context, often not collected | Logger |
| Request ID passed as a parameter through 10 functions | Clutter; forgotten in half the calls | Context propagation |
| Stack trace logged at every layer | Noise; inflated error counts | Log once at the boundary |
| 4xx and validation failures logged as ERROR | Error dashboards meaningless | INFO + a metric |
| Average latency on the dashboard | Hides the tail | Histograms, p50/p95/p99 |
| `user_id`, raw URL path, or error message as a metric label | Cardinality explosion | Bounded labels; IDs in traces/logs |
| Metric names with units in the wrong place or mixed units | Misread dashboards | `_seconds`, `_bytes`, base units |
| Queue consumers with no lag metric | Silent backlog growth | Age of oldest message |
| Cron job with no last-success timestamp | Silent non-execution | Gauge + staleness alert |
| No propagation through message queues | Async work appears as separate traces | Trace headers in message metadata |
| Liveness probe checks the database | Mass restarts on a dependency blip | Liveness = process only |
| Logging whole request bodies / objects | Leaks PII and secrets | Log IDs and selected fields |
| Only technical metrics | Silent business failures | Domain metrics (§6) |
| Instrumentation untested | Broken exactly when needed | §11 |

---

## 13 · Interview questions and model answers

**Q: Logs, metrics, traces — when do you use each?**
Metrics to detect and quantify problems cheaply — rates, error ratios, latency
percentiles — and to alert. Traces to find where time or failure is in a request across
services. Logs for the detailed record of specific events. They're most useful linked:
shared labels like version and route, trace IDs on log lines, exemplars from metrics to
traces.

**Q: What makes a good log line?**
Structured, with a constant message and variable data as fields; carries request and trace
IDs automatically; the level reflects whether someone needs to act; no secrets or
unnecessary personal data; and errors are logged once with their type and cause chain.

**Q: Why not use average latency?**
Averages hide the tail. A service can average 18 ms while 1% of requests take a second,
and pages that fan out to many calls hit that 1% most of the time. Use histograms and look
at p95/p99, and set SLOs on percentiles.

**Q: What's the cardinality problem?**
Each unique label combination is its own time series. Labels with unbounded values — user
IDs, raw URLs, error messages — multiply series into the millions and overwhelm the
metrics backend. Keep labels to small bounded sets and put per-entity identifiers in logs
and trace attributes.

**Q: How does distributed tracing work?**
Each unit of work is a span with a trace ID, span ID, and parent ID. Within a process the
current span is carried in context; across processes the IDs travel in a header like W3C
`traceparent`, which the receiver uses as the parent for its spans. A backend assembles
spans with the same trace ID into a tree. Sampling decisions travel with it so a trace is
kept or dropped as a whole.

**Q: Liveness vs. readiness?**
Liveness asks whether to restart the process, so it checks only the process itself.
Readiness asks whether to send traffic, so it covers startup, draining, and critical
dependencies. Putting dependency checks in liveness turns a database blip into
simultaneous restarts of every replica.

**Q: A background job stopped running last week and nobody noticed. How do you prevent
that?**
Absence of errors isn't health. Emit a last-success timestamp gauge and items-processed
counter, and alert when the timestamp is older than the expected interval — plus a lag
metric for queue consumers. Also add a business metric downstream that would drop if the
job stops.

**Q: How do you keep PII out of logs?**
Log identifiers rather than personal data, use types that redact themselves when logged,
add central redaction in the formatter as a safety net, scrub headers and query strings in
access and client logs, keep sensitive values out of exception messages, and test with a
canary value that must never appear in output.

---

## 14 · Checklist

**Logs**
- [ ] Structured (<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>) with constant messages and fields.
- [ ] Request ID, trace ID, user/tenant ID, version attached automatically.
- [ ] Levels mean actions; client errors are not ERROR.
- [ ] Errors logged once at the boundary with type and cause.
- [ ] No secrets; personal data replaced by IDs; central redaction as a backstop.
- [ ] Audit events go to an audit log, not debug logs.

**Metrics**
- [ ] RED for every endpoint and every outbound dependency.
- [ ] USE for every pool and queue; lag for consumers; last-success for jobs.
- [ ] Latency as histograms with buckets around the <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr>.
- [ ] Names follow conventions with base-unit suffixes; labels are bounded.
- [ ] Business outcome metrics for core flows.

**Traces**
- [ ] Inbound and outbound calls instrumented; context propagated over <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>, <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr>, and queues.
- [ ] Significant internal steps have spans; IDs are span attributes, not metric labels.
- [ ] Sampling keeps errors and slow requests.

**Operations**
- [ ] Liveness checks only the process; readiness covers startup, draining, critical dependencies.
- [ ] Build version and config summary visible; request IDs returned to clients.
- [ ] Instrumentation (fields, secrets absent, metrics, propagation) has tests.
