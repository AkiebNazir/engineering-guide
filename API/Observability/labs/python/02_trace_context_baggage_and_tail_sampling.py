"""
LAB 02 (advanced) - Under the SDK: W3C Trace Context by hand, baggage, and tail sampling
========================================================================================
Lab 01 let the OpenTelemetry SDK do propagation and sampling. This lab rebuilds both with the
standard library, so you know exactly what an SDK, a proxy or a Collector does with those headers,
and why "keep every error trace" cannot be decided at the edge.

    traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
                 ^^ ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ^^^^^^^^^^^^^^^^ ^^
            version        trace-id (16 bytes)     parent-id (8 B)  flags (bit 0 = sampled)

You will learn
  * PARSING traceparent the way the spec requires: lowercase hex, exact lengths, all-zero ids
    are invalid, version ff is invalid, and an invalid header means START A NEW TRACE (never
    fail the request because of a tracing header)
  * tracestate: vendor key=value pairs, at most 32, the vendor that modifies it moves to the front
  * BAGGAGE: the `baggage` header carries business context (tenant, plan) to every downstream
    service. It is sent to EVERY hop, including third parties: never put secrets or PII in it,
    and strip it at your trust boundary
  * HEAD sampling (decide at the first hop, by trace id) versus TAIL sampling (buffer all spans of
    a trace, decide when it is complete): with a 0.5% error rate and 10% head sampling you keep
    about 1 error trace in 10; a tail policy "all errors + all slow + 5% of the rest" keeps them all
  * the price of tail sampling: every span must reach ONE collector instance per trace (routing by
    trace id, e.g. the Collector's loadbalancing exporter) and be held in memory until decided

Standard library only.
Run it   python 02_trace_context_baggage_and_tail_sampling.py
"""
import random
import re
import secrets
import urllib.parse
from collections import defaultdict
from dataclasses import dataclass

TRACEPARENT_RE = re.compile(r"^([0-9a-f]{2})-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$")


# ================================================================== trace context ==
@dataclass(frozen=True)
class SpanContext:
    trace_id: str
    span_id: str
    sampled: bool

    def header(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{'01' if self.sampled else '00'}"


def parse_traceparent(value: str | None) -> SpanContext | None:
    """Returns None for anything invalid - the caller then starts a fresh trace."""
    if not value:
        return None
    m = TRACEPARENT_RE.match(value.strip())
    if not m:
        return None
    version, trace_id, span_id, flags = m.groups()
    if version == "ff" or trace_id == "0" * 32 or span_id == "0" * 16:
        return None
    return SpanContext(trace_id, span_id, bool(int(flags, 16) & 0x01))


def child_of(parent: SpanContext | None, sample_ratio: float) -> SpanContext:
    """A new span: same trace (and the parent's decision) if there is a parent, else a new root."""
    if parent is None:
        trace_id = secrets.token_hex(16)
        # ratio sampling on the trace id: every service computing it would reach the same answer
        sampled = int(trace_id[-14:], 16) < sample_ratio * 16 ** 14
        return SpanContext(trace_id, secrets.token_hex(8), sampled)
    return SpanContext(parent.trace_id, secrets.token_hex(8), parent.sampled)


def update_tracestate(value: str, vendor: str, entry: str) -> str:
    items = [kv.strip() for kv in value.split(",") if kv.strip()] if value else []
    items = [kv for kv in items if not kv.startswith(vendor + "=")]
    return ",".join([f"{vendor}={entry}"] + items[:31])          # modified vendor first, max 32


def parse_baggage(value: str) -> dict[str, str]:
    out = {}
    for member in value.split(","):
        kv = member.split(";")[0].strip()                         # ";properties" are ignored here
        if "=" in kv:
            k, v = kv.split("=", 1)
            out[k.strip()] = urllib.parse.unquote(v.strip())
    return out


def make_baggage(items: dict[str, str]) -> str:
    return ",".join(f"{k}={urllib.parse.quote(v)}" for k, v in items.items())


# ============================================================ simulated traffic ==
@dataclass
class Span:
    trace_id: str
    service: str
    duration_ms: float
    error: bool


def simulate(n_traces: int, rng: random.Random) -> list[list[Span]]:
    """Each trace: gateway -> orders -> payments. 0.5% fail in payments; 1% are slow (> 1 s)."""
    traces = []
    for _ in range(n_traces):
        tid = "%032x" % rng.getrandbits(128)
        error = rng.random() < 0.005
        slow = rng.random() < 0.01
        pay = rng.uniform(1200, 2000) if slow else rng.uniform(5, 40)
        traces.append([Span(tid, "payments", pay, error),
                       Span(tid, "orders", pay + rng.uniform(2, 10), error),
                       Span(tid, "gateway", pay + rng.uniform(12, 20), error)])
    return traces


def head_sample(traces, ratio):
    return [t for t in traces if int(t[0].trace_id[-14:], 16) < ratio * 16 ** 14]


class TailSampler:
    """What the Collector's tail_sampling processor does: buffer by trace id, decide on completion."""

    def __init__(self, expected_spans=3, baseline=0.05):
        self.buffer = defaultdict(list)
        self.expected, self.baseline = expected_spans, baseline
        self.kept, self.peak_buffered = [], 0

    def on_span(self, span: Span):
        self.buffer[span.trace_id].append(span)
        self.peak_buffered = max(self.peak_buffered, sum(len(v) for v in self.buffer.values()))
        if len(self.buffer[span.trace_id]) == self.expected:        # real one: decision_wait timeout
            self.decide(span.trace_id)

    def decide(self, trace_id):
        spans = self.buffer.pop(trace_id)
        if any(s.error for s in spans):
            reason = "error"
        elif max(s.duration_ms for s in spans) > 1000:
            reason = "slow"
        elif int(trace_id[-14:], 16) < self.baseline * 16 ** 14:
            reason = "baseline"
        else:
            return
        self.kept.append((reason, spans))


# ========================================================================= demo ==
def demo():
    print("== 1. parsing traceparent strictly ==")
    cases = {
        "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01": True,
        "00-4BF92F3577B34DA6A3CE929D0E0E4736-00F067AA0BA902B7-01": False,   # uppercase
        "00-00000000000000000000000000000000-00f067aa0ba902b7-01": False,   # all-zero trace id
        "00-4bf92f3577b34da6a3ce929d0e0e4736-0000000000000000-01": False,   # all-zero parent id
        "ff-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01": False,   # forbidden version
        "00-4bf92f3577b34da6a3ce929d0e0e473-00f067aa0ba902b7-01": False,    # 31 hex chars
        "garbage": False,
    }
    for value, valid in cases.items():
        got = parse_traceparent(value)
        print(f"   {'valid  ' if got else 'INVALID'} {value}")
        assert (got is not None) == valid
    ctx = child_of(parse_traceparent("bogus"), 1.0)
    print(f"   invalid header -> the service starts a NEW trace {ctx.trace_id[:8]}..., request still served")

    print("\n== 2. propagating through three hops ==")
    incoming = None
    hops = []
    for service in ("gateway", "orders", "payments"):
        ctx = child_of(parse_traceparent(incoming), sample_ratio=1.0)
        hops.append(ctx)
        print(f"   {service:9s} receives {incoming or '(nothing)':58s} -> own span {ctx.span_id}")
        incoming = ctx.header()
    assert len({h.trace_id for h in hops}) == 1 and len({h.span_id for h in hops}) == 3

    print("\n== 3. tracestate: modified vendor moves to the front ==")
    ts = "congo=t61rcWkgMzE,rojo=00f067aa0ba902b7"
    ts2 = update_tracestate(ts, "rojo", "d71e4e8a1b6f4c2e")
    print(f"   {ts}\n   {ts2}")
    assert ts2.startswith("rojo=d71e4e8a1b6f4c2e,congo=")

    print("\n== 4. baggage: business context for every hop (and every third party) ==")
    header = make_baggage({"tenant.id": "acme", "plan": "enterprise", "user.email": "ana@acme.test"})
    print(f"   baggage: {header}")
    got = parse_baggage(header)
    assert got["tenant.id"] == "acme" and got["user.email"] == "ana@acme.test"
    outbound = {k: v for k, v in got.items() if k in {"tenant.id", "plan"}}       # allowlist at the boundary
    print(f"   to a third-party API, after the allowlist: {make_baggage(outbound)}")
    assert "user.email" not in outbound
    print("   (baggage is NOT added to spans automatically; copy the keys you want onto span attributes)")

    print("\n== 5. head vs tail sampling on 20,000 traces (0.5% errors, 1% slow) ==")
    rng = random.Random(42)
    traces = simulate(20_000, rng)
    errors = [t for t in traces if t[0].error]
    slow = [t for t in traces if max(s.duration_ms for s in t) > 1000]
    head = head_sample(traces, 0.10)
    head_err = [t for t in head if t[0].error]
    tail = TailSampler(baseline=0.05)
    spans = [s for t in traces for s in t]
    # spans of different traces interleave on the wire; shuffle within a window to mimic that
    for i in range(0, len(spans), 300):
        window = spans[i:i + 300]
        rng.shuffle(window)
        for s in window:
            tail.on_span(s)
    kept_err = [spans for reason, spans in tail.kept if reason == "error"]
    kept_slow = [spans for reason, spans in tail.kept if reason == "slow"]
    print(f"   errors in traffic: {len(errors)}, slow: {len(slow)}")
    print(f"   head 10%  : kept {len(head):5d} traces, {len(head_err):3d} of the {len(errors)} error traces")
    print(f"   tail policy: kept {len(tail.kept):5d} traces, {len(kept_err):3d} of the {len(errors)} error traces, "
          f"{len(kept_slow)} of {len(slow)} slow")
    print(f"   tail cost  : up to {tail.peak_buffered} spans held in memory waiting for their trace to finish")
    assert len(kept_err) == len(errors) and len(head_err) < len(errors) * 0.3
    assert len(kept_slow) == len([t for t in slow if not t[0].error])
    assert len(tail.kept) < len(head)

    print("\n== 6. why tail sampling needs trace-id routing ==")
    collectors = 3
    split = defaultdict(set)
    for s in spans[:3000]:
        split[s.trace_id].add(rng.randrange(collectors))        # round-robin-ish: spans scattered
    scattered = sum(1 for c in split.values() if len(c) > 1)
    routed = {tid: int(tid, 16) % collectors for tid in split}  # hash(trace id) -> one collector
    print(f"   random load balancing : {scattered} of {len(split)} traces split across collectors (no one sees them whole)")
    print(f"   route by trace id     : 0 split; traces spread over collectors {sorted(set(routed.values()))}, each trace on exactly one")
    assert scattered > len(split) // 2
    print("\nOK")


if __name__ == "__main__":
    demo()
