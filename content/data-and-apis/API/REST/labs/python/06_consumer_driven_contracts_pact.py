"""
LAB 06 (advanced) - Consumer-driven contract testing (Pact), built from scratch
===============================================================================
You will learn
  * the problem: the provider's unit tests pass, the consumer's unit tests (with a hand-written
    mock) pass, and production still breaks, because the two sides tested against DIFFERENT
    ideas of the API
  * the Pact workflow, in two halves that never run at the same time:
      CONSUMER side: the consumer's test declares the interactions it needs, runs its REAL
                     client code against a MOCK provider built from those declarations, and
                     writes a PACT FILE (JSON) only if the client really made exactly those calls
      PROVIDER side: the provider's CI loads the pact file, sets up each "provider state",
                     replays each request against the REAL provider and checks the response
  * matchers: the pact says "an integer", "a string like PAID|SHIPPED", "a list of at least one
    item shaped like this", not the exact example values
  * the payoff versus a schema diff: the provider may REMOVE a field no consumer uses (a schema
    diff calls that breaking), and CANNOT rename a field a consumer reads (caught before deploy)

    consumer test ---> mock provider ---> pact file (JSON) ---> provider verification ---> real API
       (checkout-web)    (records calls)     (the contract)       (replays + matches)     (orders-api)

The pact file written here follows the Pact v3 JSON layout (interactions, providerStates,
matchingRules with "$.body..." paths), so you can open it next to one from the real tools.
Real projects use pact-python / pact-js / pact-jvm / pact-go plus a Pact Broker (or PactFlow);
the Go lab 08 builds the broker side ("can I deploy?").

Needs   pip install fastapi httpx
Run it  python 06_consumer_driven_contracts_pact.py
"""
import json
import re
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient


# =================================================================== matchers ===
# A matcher wraps an EXAMPLE value (what the mock returns) plus a RULE (what the provider must satisfy).
class Like:                                     # "same JSON type as the example"
    def __init__(self, example):
        self.example = example


class Term:                                     # "a string matching this regex"
    def __init__(self, regex: str, example: str):
        assert re.fullmatch(regex, example), "the example must match its own regex"
        self.regex, self.example = regex, example


class EachLike:                                 # "a list of >= min items, each shaped like this"
    def __init__(self, template, min: int = 1):
        self.template, self.min = template, min


def reify(node):
    """The concrete example: what the mock provider sends back to the consumer."""
    if isinstance(node, (Like, Term)):
        return reify(node.example)
    if isinstance(node, EachLike):
        return [reify(node.template)] * node.min
    if isinstance(node, dict):
        return {k: reify(v) for k, v in node.items()}
    if isinstance(node, list):
        return [reify(v) for v in node]
    return node


def rules(node, path: str = "$", out: dict | None = None) -> dict:
    """Flatten matchers into Pact v3 matchingRules: {"$.items[*].qty": {"matchers": [...]}}."""
    out = {} if out is None else out
    if isinstance(node, Like):
        out[path] = {"matchers": [{"match": "type"}]}
        rules(node.example, path, out)               # a Like around a dict/list cascades to children
    elif isinstance(node, Term):
        out[path] = {"matchers": [{"match": "regex", "regex": node.regex}]}
    elif isinstance(node, EachLike):
        out[path] = {"matchers": [{"match": "type", "min": node.min}]}
        rules(node.template, path + "[*]", out)
    elif isinstance(node, dict):
        for k, v in node.items():
            rules(v, f"{path}.{k}", out)
    return out


# ============================================================ CONSUMER SIDE ===
class Pact:
    """The consumer's test builds interactions, runs its client against a mock, writes the pact."""

    def __init__(self, consumer: str, provider: str):
        self.consumer, self.provider = consumer, provider
        self.interactions: list[dict] = []
        self.received: list[tuple] = []
        self.unexpected: list[str] = []

    def interaction(self, state: str, description: str, method: str, path: str,
                    status: int, body=None, request_body=None):
        self.interactions.append({
            "description": description,
            "providerStates": [{"name": state}],
            "request": {"method": method, "path": path,
                        **({"body": request_body} if request_body is not None else {})},
            "response": {"status": status, "headers": {"Content-Type": "application/json"},
                         "body": reify(body),
                         "matchingRules": {"body": rules(body)}},
        })

    # ---- the mock provider: serves ONLY what was declared, remembers what was called --------
    def _handler(self):
        pact = self

        class Mock(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _any(self):
                n = int(self.headers.get("Content-Length") or 0)
                body = json.loads(self.rfile.read(n)) if n else None
                for i in pact.interactions:
                    rq = i["request"]
                    if (rq["method"], rq["path"], rq.get("body")) == (self.command, self.path, body):
                        pact.received.append((self.command, self.path))
                        out = json.dumps(i["response"]["body"]).encode()
                        self.send_response(i["response"]["status"])
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Content-Length", str(len(out)))
                        self.end_headers()
                        self.wfile.write(out)
                        return
                pact.unexpected.append(f"{self.command} {self.path} {body}")
                self.send_response(500)             # Pact mocks answer unknown calls with an error
                self.send_header("Content-Length", "0")
                self.end_headers()

            do_GET = do_POST = do_PUT = do_PATCH = do_DELETE = _any

        return Mock

    def verify_and_write(self, run_consumer_tests, pact_dir: Path) -> Path:
        server = ThreadingHTTPServer(("127.0.0.1", 0), self._handler())
        threading.Thread(target=server.serve_forever, daemon=True).start()
        try:
            run_consumer_tests(f"http://127.0.0.1:{server.server_port}")
        finally:
            server.shutdown()
        declared = {(i["request"]["method"], i["request"]["path"]) for i in self.interactions}
        missing = declared - set(self.received)
        # Both checks matter: an unexpected call means the client does something the pact does not
        # promise; a missing call means the pact promises something the client never needed.
        if self.unexpected or missing:
            raise AssertionError(f"mock mismatch: unexpected={self.unexpected} never-called={missing}")
        doc = {"consumer": {"name": self.consumer}, "provider": {"name": self.provider},
               "interactions": self.interactions,
               "metadata": {"pactSpecification": {"version": "3.0.0"}}}
        out = pact_dir / f"{self.consumer}-{self.provider}.json"
        out.write_text(json.dumps(doc, indent=2))
        return out


# ---- the consumer's REAL client code (what ships in checkout-web) --------------------------
class OrdersClient:
    def __init__(self, base_url: str):
        self.http = httpx.Client(base_url=base_url, timeout=2)

    def order_summary(self, order_id: int) -> str | None:
        r = self.http.get(f"/orders/{order_id}")
        if r.status_code == 404:
            return None
        r.raise_for_status()
        o = r.json()                                         # the fields this consumer READS:
        qty = sum(item["qty"] for item in o["items"])        #   items[].qty
        return f"#{o['id']} {o['status']} {qty} item(s) ${o['total_cents'] / 100:.2f}"  # id, status, total_cents

    def place_order(self, sku: str, qty: int) -> int:
        r = self.http.post("/orders", json={"sku": sku, "qty": qty})
        assert r.status_code == 201, r.status_code
        return r.json()["id"]


def build_checkout_pact() -> Pact:
    pact = Pact("checkout-web", "orders-api")
    pact.interaction("order 42 exists", "a request for order 42", "GET", "/orders/42", 200, body={
        "id": Like(42),
        "status": Term(r"PENDING|PAID|SHIPPED", "PAID"),
        "total_cents": Like(1999),
        "items": EachLike({"sku": Like("SKU-1"), "qty": Like(1)}),
    })
    pact.interaction("order 999 does not exist", "a request for a missing order", "GET", "/orders/999",
                     404, body={"detail": Like("order not found")})
    pact.interaction("SKU-1 is in stock", "a request to place an order", "POST", "/orders", 201,
                     body={"id": Like(43), "status": Term(r"PENDING|PAID", "PENDING")},
                     request_body={"sku": "SKU-1", "qty": 2})
    return pact


def consumer_tests(base_url: str):
    """Ordinary unit tests of the consumer. The mock answers with the pact's example values."""
    c = OrdersClient(base_url)
    assert c.order_summary(42) == "#42 PAID 1 item(s) $19.99"
    assert c.order_summary(999) is None
    assert c.place_order("SKU-1", 2) == 43


# ============================================================ PROVIDER SIDE ===
def match(expected, actual, path: str, rule_map: dict, errors: list):
    """Pact matching: the provider may send MORE than expected (extra keys are fine: Postel's law),
    never less, and every value must satisfy its rule (or equal the example if it has none)."""
    rule_path = re.sub(r"\[\d+\]", "[*]", path)
    rule = rule_map.get(rule_path, {}).get("matchers", [{}])[0]
    kind = rule.get("match")
    if kind == "regex":
        if not (isinstance(actual, str) and re.fullmatch(rule["regex"], actual)):
            errors.append(f"{path}: {actual!r} does not match /{rule['regex']}/")
        return
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            errors.append(f"{path}: expected an object, got {actual!r}")
            return
        for k, v in expected.items():
            if k not in actual:
                errors.append(f"{path}.{k}: missing (the consumer reads this field)")
            else:
                match(v, actual[k], f"{path}.{k}", rule_map, errors)
        return
    if isinstance(expected, list):
        if not isinstance(actual, list):
            errors.append(f"{path}: expected a list, got {actual!r}")
        elif kind == "type":
            if len(actual) < rule.get("min", 0):
                errors.append(f"{path}: expected at least {rule['min']} item(s), got {len(actual)}")
            for i, item in enumerate(actual):
                match(expected[0], item, f"{path}[{i}]", rule_map, errors)
        elif len(actual) != len(expected):
            errors.append(f"{path}: expected exactly {len(expected)} items")
        else:
            for i, (e, a) in enumerate(zip(expected, actual)):
                match(e, a, f"{path}[{i}]", rule_map, errors)
        return
    if kind == "type":
        same = type(actual) is type(expected) or (
            isinstance(actual, (int, float)) and isinstance(expected, (int, float))
            and not isinstance(actual, bool) and not isinstance(expected, bool))
        if not same:
            errors.append(f"{path}: expected a {type(expected).__name__}, got {actual!r}")
    elif expected != actual:
        errors.append(f"{path}: expected {expected!r}, got {actual!r}")


def verify_provider(pact_file: Path, app: FastAPI, state_handlers: dict) -> list[str]:
    pact = json.loads(pact_file.read_text())
    client = TestClient(app)
    failures = []
    for i in pact["interactions"]:
        for st in i["providerStates"]:
            if st["name"] not in state_handlers:
                failures.append(f"[{i['description']}] no handler for provider state {st['name']!r}")
                continue
            state_handlers[st["name"]]()                # put the provider's data in the right shape
        rq, rs = i["request"], i["response"]
        r = client.request(rq["method"], rq["path"], json=rq.get("body"))
        errs = []
        if r.status_code != rs["status"]:
            errs.append(f"status: expected {rs['status']}, got {r.status_code}")
        if not r.headers.get("content-type", "").startswith(rs["headers"]["Content-Type"]):
            errs.append(f"Content-Type: got {r.headers.get('content-type')}")
        if "body" in rs and not errs:
            match(rs["body"], r.json(), "$", rs["matchingRules"]["body"], errs)
        failures += [f"[{i['description']}] {e}" for e in errs]
    return failures


# ---- three versions of the provider ------------------------------------------------------
DB: dict[int, dict] = {}


def make_provider(version: str) -> tuple[FastAPI, dict]:
    app = FastAPI()

    def shape(o: dict) -> dict:
        body = {"id": o["id"], "status": o["status"], "items": o["items"],
                "currency": "USD", "created_at": "2026-09-25T10:00:00Z"}       # extra fields: fine
        if version == "v1":
            body |= {"total_cents": o["total_cents"], "legacy_ref": f"ORD-{o['id']}"}
        elif version == "v2-drops-unused":
            body |= {"total_cents": o["total_cents"]}                        # legacy_ref removed
        elif version == "v3-renames-total":
            body |= {"total": {"amount": o["total_cents"], "currency": "USD"}}  # total_cents renamed
        return body

    @app.get("/orders/{order_id}")
    def get_order(order_id: int):
        if order_id not in DB:
            raise HTTPException(404, "order not found")
        return shape(DB[order_id])

    @app.post("/orders", status_code=201)
    def create_order(req: dict):
        oid = max(DB, default=42) + 1
        DB[oid] = {"id": oid, "status": "PENDING", "total_cents": 999 * req["qty"],
                   "items": [{"sku": req["sku"], "qty": req["qty"], "name": "Mug"}]}
        return shape(DB[oid])

    states = {
        "order 42 exists": lambda: (DB.clear(), DB.update({42: {
            "id": 42, "status": "SHIPPED", "total_cents": 4598,
            "items": [{"sku": "SKU-7", "qty": 2, "name": "Lamp"}, {"sku": "SKU-9", "qty": 1, "name": "Bulb"}]}})),
        "order 999 does not exist": lambda: DB.pop(999, None),
        "SKU-1 is in stock": lambda: None,
    }
    return app, states


def main():
    pact_dir = Path(tempfile.mkdtemp(prefix="pacts-"))

    print("== CONSUMER side: checkout-web's tests run against a mock orders-api ==")
    pact_file = build_checkout_pact().verify_and_write(consumer_tests, pact_dir)
    doc = json.loads(pact_file.read_text())
    print(f"   wrote {pact_file.name}: {len(doc['interactions'])} interactions")
    print("   matchingRules for GET /orders/42:")
    for p, r in doc["interactions"][0]["response"]["matchingRules"]["body"].items():
        print(f"      {p:<18} {r['matchers'][0]}")
    assert "$.items[*].qty" in doc["interactions"][0]["response"]["matchingRules"]["body"]

    print("\n-- a consumer test that calls something it never declared cannot write a pact --")
    try:
        build_checkout_pact().verify_and_write(
            lambda url: (consumer_tests(url), httpx.get(f"{url}/orders/42/invoice")), pact_dir)
        raise SystemExit("should have failed")
    except AssertionError as e:
        print("  ", str(e)[:90])

    print("\n== PROVIDER side: orders-api verifies the pact file against each version ==")
    results = {}
    for version in ("v1", "v2-drops-unused", "v3-renames-total"):
        app, states = make_provider(version)
        failures = verify_provider(pact_file, app, states)
        results[version] = failures
        print(f"   {version:<18} {'PASS' if not failures else 'FAIL'}")
        for f in failures:
            print(f"        {f}")

    # v1: real data differs from the examples (SHIPPED, 2 items, 4598) and has extra fields: still passes
    assert results["v1"] == []
    # v2 removed legacy_ref. An OpenAPI diff flags that as breaking; no consumer reads it, so Pact passes
    assert results["v2-drops-unused"] == []
    # v3 renamed total_cents: checkout-web would crash in production. Caught here, before deploy.
    assert any("$.total_cents: missing" in f for f in results["v3-renames-total"])
    # ...and ONLY on GET /orders/42: the POST interaction never promised total_cents, so it still passes
    assert len(results["v3-renames-total"]) == 1
    print("   => v3 fails only where this consumer actually reads the renamed field")

    print("\n-- a provider state nobody implemented is a failure, not a silent skip --")
    app, states = make_provider("v1")
    del states["SKU-1 is in stock"]
    fails = verify_provider(pact_file, app, states)
    print("  ", fails[0])
    assert fails and "no handler for provider state" in fails[0]
    print("\nOK")


if __name__ == "__main__":
    main()
