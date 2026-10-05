"""
LAB 03 (advanced) - Upstream management: load balancing, health, retries, and overload protection
==================================================================================================
Routing picks a SERVICE; this lab is about picking an INSTANCE of it and surviving the ones that are
slow, broken or overloaded. These are the knobs Envoy calls clusters, and Kong calls upstreams/targets.

    gateway --pick--> [ a ] [ b ] [ c ]      per instance the gateway tracks:
                                               outstanding requests, consecutive 5xx, active health

You will learn
  * ROUND ROBIN vs POWER-OF-TWO-CHOICES least-request (P2C): with one slow instance, RR keeps
    feeding it a third of the traffic; P2C sees its queue and sends almost nothing there
  * PASSIVE health (outlier ejection): N consecutive 5xx -> eject for a while, then try again
  * ACTIVE health checks: poll /healthz; a draining instance leaves the pool before it breaks
  * RETRIES done safely: only idempotent requests (or ones with an Idempotency-Key), on a DIFFERENT
    instance, inside a RETRY BUDGET so an outage cannot triple your traffic (a retry storm)
  * CONCURRENCY LIMITS (what Envoy calls circuit breakers): past max in-flight requests, fail FAST
    with 503 instead of queueing until everything times out

Standard library only.
Run it   python 03_load_balancing_health_and_resilience.py
"""
import http.client
import json
import random
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

IDEMPOTENT = {"GET", "HEAD", "PUT", "DELETE", "OPTIONS"}


# ================================================================ upstream instances ==
def make_instance(name: str, behaviour: dict):
    """behaviour is live-editable: {"delay": s, "status": code for '/', "healthz": code}."""
    class Instance(BaseHTTPRequestHandler):
        def _handle(self):
            n = int(self.headers.get("Content-Length") or 0)
            self.rfile.read(n)
            if self.path == "/healthz":
                status = behaviour.get("healthz", 200)
            else:
                time.sleep(behaviour.get("delay", 0))
                status = behaviour.get("status", 200)
            body = json.dumps({"instance": name}).encode()
            self.send_response(status)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        do_GET = do_POST = _handle

        def log_message(self, *_):
            pass
    return Instance


# ================================================================ the upstream pool ==
@dataclass
class Host:
    name: str
    port: int
    outstanding: int = 0
    consecutive_5xx: int = 0
    ejected_until: float = 0.0
    healthy: bool = True           # set by the active health checker
    hc_fails: int = 0
    hc_oks: int = 0


class Pool:
    def __init__(self, hosts, algo="rr", eject_after=5, eject_for=0.4,
                 retries=0, budget_ratio=0.2, budget_min=3, max_requests=None):
        self.hosts, self.algo = hosts, algo
        self.eject_after, self.eject_for = eject_after, eject_for
        self.retries, self.budget_ratio, self.budget_min = retries, budget_ratio, budget_min
        self.max_requests = max_requests
        self.lock = threading.Lock()
        self.rr = 0
        self.in_flight = 0
        self.stats = {"requests": 0, "attempts": 0, "retries": 0, "overflow": 0, "budget_denied": 0}
        self.rng = random.Random(7)

    # --- selection ---
    def _available(self, exclude):
        now = time.monotonic()
        return [h for h in self.hosts if h.healthy and h.ejected_until <= now and h not in exclude]

    def pick(self, exclude=()) -> Host | None:
        with self.lock:
            hosts = self._available(exclude)
            if not hosts:
                return None
            if self.algo == "rr":
                self.rr += 1
                h = hosts[self.rr % len(hosts)]
            else:                                          # P2C: two random hosts, take the less busy
                a, b = self.rng.sample(hosts, 2) if len(hosts) > 1 else (hosts[0], hosts[0])
                h = a if a.outstanding <= b.outstanding else b
            h.outstanding += 1
            return h

    def _record(self, h: Host, status: int):
        with self.lock:
            h.outstanding -= 1
            if status >= 500:
                h.consecutive_5xx += 1
                if h.consecutive_5xx >= self.eject_after:
                    h.ejected_until = time.monotonic() + self.eject_for
                    h.consecutive_5xx = 0
            else:
                h.consecutive_5xx = 0

    def _retry_allowed(self) -> bool:
        # budget: retries may be at most ratio x requests (plus a small floor so low traffic can retry)
        with self.lock:
            if self.stats["retries"] < self.budget_min + self.budget_ratio * self.stats["requests"]:
                self.stats["retries"] += 1
                return True
            self.stats["budget_denied"] += 1
            return False

    # --- one request through the gateway ---
    def send(self, method="GET", path="/", headers=None) -> tuple[int, str | None]:
        headers = headers or {}
        with self.lock:
            self.stats["requests"] += 1
            if self.max_requests is not None and self.in_flight >= self.max_requests:
                self.stats["overflow"] += 1
                return 503, "overflow"                     # fail fast: no socket, no queue, no timeout
            self.in_flight += 1
        try:
            retryable = method in IDEMPOTENT or "Idempotency-Key" in headers
            tried = []
            for attempt in range(1 + self.retries):
                if attempt and not (retryable and self._retry_allowed()):
                    break
                h = self.pick(exclude=tried)
                if h is None:
                    return 503, "no_healthy_upstream"
                tried.append(h)
                with self.lock:
                    self.stats["attempts"] += 1
                try:
                    c = http.client.HTTPConnection("127.0.0.1", h.port, timeout=2)
                    c.request(method, path, headers=headers)
                    status = c.getresponse().status
                    c.close()
                except OSError:
                    status = 503                           # connect failure counts as a 5xx for health
                self._record(h, status)
                if status not in (502, 503, 504):          # retry only "the instance could not serve it"
                    return status, h.name
            return status, h.name
        finally:
            with self.lock:
                self.in_flight -= 1

    # --- active health checking ---
    def health_check_once(self, unhealthy_after=2, healthy_after=2):
        for h in self.hosts:
            try:
                c = http.client.HTTPConnection("127.0.0.1", h.port, timeout=0.5)
                c.request("GET", "/healthz")
                ok = c.getresponse().status == 200
                c.close()
            except OSError:
                ok = False
            with self.lock:                                # hysteresis: one blip does not flap the pool
                h.hc_oks, h.hc_fails = (h.hc_oks + 1, 0) if ok else (0, h.hc_fails + 1)
                if h.healthy and h.hc_fails >= unhealthy_after:
                    h.healthy = False
                elif not h.healthy and h.hc_oks >= healthy_after:
                    h.healthy = True


# ================================================================ demo ==
def start_instances():
    behaviours = {n: {} for n in "abc"}
    servers = {}
    for n in "abc":
        srv = ThreadingHTTPServer(("127.0.0.1", 0), make_instance(n, behaviours[n]))
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers[n] = srv
    return behaviours, servers


def fresh_hosts(servers):
    return [Host(n, s.server_port) for n, s in servers.items()]


def load(pool, n, workers, method="GET", headers=None):
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(lambda _: pool.send(method, "/", headers), range(n)))


def demo():
    beh, servers = start_instances()

    print("-- 1. round robin vs P2C least-request, instance b is slow (120 ms vs ~0 ms) --")
    beh["b"]["delay"] = 0.12
    share = {}
    for algo in ("rr", "p2c"):
        pool = Pool(fresh_hosts(servers), algo=algo)
        t = time.perf_counter()
        res = load(pool, 150, workers=12)
        took = time.perf_counter() - t
        share[algo] = sum(1 for _, who in res if who == "b") / len(res)
        print(f"  {algo:4s}: {share[algo]:5.0%} of requests went to slow b, 150 requests took {took:.2f}s")
    assert share["rr"] > 0.3 and share["p2c"] < share["rr"] * 0.6
    beh["b"]["delay"] = 0

    print("\n-- 2. passive health: b starts returning 500; ejected after 5 in a row --")
    beh["b"]["status"] = 500
    pool = Pool(fresh_hosts(servers), algo="rr", eject_after=5, eject_for=0.4)
    res = [pool.send() for _ in range(40)]
    errors = sum(1 for s, _ in res if s == 500)
    print(f"  40 sequential GETs: {errors} errors, then b is out of the pool")
    assert errors == 5 and pool.hosts[1].ejected_until > time.monotonic()
    beh["b"]["status"] = 200
    time.sleep(0.45)
    back = {who for _, who in (pool.send() for _ in range(6))}
    print("  b fixed and ejection over -> serving again:", sorted(back))
    assert "b" in back

    print("\n-- 3. retries: b answers 503; GETs retried on another instance, POSTs are not --")
    beh["b"]["status"] = 503
    # budget_ratio=1.0: a generous retry budget here, so this step shows WHICH requests may be
    # retried; step 4 shows why the budget must normally be much tighter.
    pool = Pool(fresh_hosts(servers), algo="rr", retries=2, eject_after=10_000, budget_ratio=1.0)
    gets = [pool.send("GET") for _ in range(30)]
    posts = [pool.send("POST") for _ in range(30)]
    keyed = [pool.send("POST", headers={"Idempotency-Key": f"k{i}"}) for i in range(30)]
    ok = lambda rs: sum(1 for s, _ in rs if s == 200)
    print(f"  GET  : {ok(gets)}/30 succeeded (a failed try on b is retried on a or c)")
    print(f"  POST : {ok(posts)}/30 succeeded (the ones sent to b fail: retrying could double-charge)")
    print(f"  POST + Idempotency-Key: {ok(keyed)}/30 succeeded")
    assert ok(gets) == 30 and ok(posts) == 20 and ok(keyed) == 30
    beh["b"]["status"] = 200

    print("\n-- 4. retry budget during a full outage (every instance 503, retries=2) --")
    for n in "abc":
        beh[n]["status"] = 503
    for budget in (None, 0.2):
        kwargs = {"budget_ratio": 10.0, "budget_min": 10_000} if budget is None else {"budget_ratio": budget}
        pool = Pool(fresh_hosts(servers), retries=2, eject_after=10_000, **kwargs)
        for _ in range(100):
            pool.send()
        label = "no budget " if budget is None else "20% budget"
        print(f"  {label}: 100 client requests -> {pool.stats['attempts']} upstream attempts")
        assert pool.stats["attempts"] == (300 if budget is None else 100 + 3 + 20)
    for n in "abc":
        beh[n]["status"] = 200

    print("\n-- 5. active health checks: c is draining (/healthz 503) but '/' still works --")
    pool = Pool(fresh_hosts(servers), algo="rr")
    beh["c"]["healthz"] = 503
    pool.health_check_once()
    print("  after 1 failed check  c.healthy =", pool.hosts[2].healthy, "(hysteresis: need 2)")
    assert pool.hosts[2].healthy
    pool.health_check_once()
    served = {who for _, who in (pool.send() for _ in range(12))}
    print("  after 2 failed checks c.healthy =", pool.hosts[2].healthy, "-> traffic to", sorted(served))
    assert served == {"a", "b"}
    beh["c"]["healthz"] = 200
    pool.health_check_once()
    pool.health_check_once()
    assert pool.hosts[2].healthy

    print("\n-- 6. concurrency limit (Envoy 'circuit breaker'): max 4 in flight, 10 arrive at once --")
    for n in "abc":
        beh[n]["delay"] = 0.3
    pool = Pool(fresh_hosts(servers), max_requests=4)
    t = time.perf_counter()
    res = load(pool, 10, workers=10)
    took = time.perf_counter() - t
    over = sum(1 for _, who in res if who == "overflow")
    print(f"  {10 - over} served, {over} rejected instantly with 503 (whole burst took {took:.2f}s)")
    assert over >= 5 and 10 - over <= 5
    for n in "abc":
        beh[n]["delay"] = 0

    for s in servers.values():
        s.shutdown()
    print("\nOK")


if __name__ == "__main__":
    demo()
