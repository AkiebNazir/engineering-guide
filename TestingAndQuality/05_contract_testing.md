# Microservices: Contract Testing

In a microservices architecture, Team A writes the Orders service and Team B writes the
Checkout web app, which calls Orders to show an order's status and total. Each team has
green unit tests. Then Team A renames `totalCents` to `total_cents`, both suites stay green,
and Checkout breaks in production. **Contract testing** catches that break in Team A's CI,
before merge, without starting both services together. This chapter covers
consumer-driven contracts with **Pact** end to end (consumer test, pact file, provider
verification, the broker, `can-i-deploy`), how to evolve an API safely, and the
alternatives (schema-based, provider-driven, bi-directional).

## Foundations — How do two teams know their services still fit together?

### The problem

Checkout (the **consumer**) calls `GET /orders/42` on Orders (the **provider**) and reads three
fields: `id`, `status`, `totalCents`. Each side tests itself:

- Orders' tests check that Orders returns what Orders' developers believe it should return.
- Checkout's tests use a stub of Orders that returns what Checkout's developers believe Orders
  returns.

Both beliefs were true on Monday. On Tuesday Orders renames a field. Orders' tests are updated
along with the code, and Checkout's stub still returns the old shape. Everything is green; production
is broken. The two teams tested against **different ideas of the same API**, and nothing
compared those ideas.

### Why not just run them together?

You could run an end-to-end test that deploys both services (and their databases, and whatever
*they* call) and exercises the call. For two services it works. For fifty, the shared test
environment becomes slow, flaky, and constantly broken by someone else's half-finished change,
and a failure doesn't say which team broke what ([Integration and End-to-End (E2E) Testing](03_integration_and_e2e.md) §5).

### The idea

A **contract** is a written-down agreement about the messages two services exchange: requests,
responses, and the rules the fields must follow. Contract testing checks **each side against the
same contract, separately**:

- The consumer checks that its client code sends those requests and can handle those responses.
- The provider checks that its real implementation returns responses that satisfy the contract.

If both pass, the two services work together for everything the contract covers, and neither team
ever started the other's service.

In **consumer-driven** contract testing, the consumer's tests *generate* the contract, so it
contains exactly what the consumer uses: no more, no less. That precision is the point. The
provider can freely change anything no consumer depends on, and it learns before merge when a
change would break someone who does.

```arch
%% caption: Consumer-driven contract testing prevents breaking changes between microservices without requiring full E2E environments.
grid 190x110
node c "Consumer" at 0,0 icon=app color=blue sub="checkout-web"
node b "Pact Broker" at 1.5,0 icon=file color=slate sub="stores contracts"
node p "Provider" at 3,0 icon=app color=green sub="orders-api"
node cm "Mock provider" at 0,1 shape=card icon=server sub="from the pact"
node pv "Verifier" at 3,1 shape=card icon=check sub="replays requests"
c -> b : "uploads pact"
b -> p : "verify it"
c -- cm
p -- pv
```

| Term | Meaning |
|---|---|
| **Consumer** | The side that initiates: the HTTP client, or the message *reader* for queues |
| **Provider** | The side that responds: the HTTP server, or the message *writer* |
| **Interaction** | One request/response pair (or one message) the consumer depends on |
| **Pact file** | The contract: JSON listing every interaction plus matching rules |
| **Provider state** | A precondition the consumer assumes ("order 42 exists and is paid") |
| **Pact Broker** | Server storing pacts, verification results, and which version is deployed where |
| **Pacticipant** | Pact's word for any application taking part, consumer or provider |
| **can-i-deploy** | A query to the broker: is this version compatible with everything in the target environment? |

## 1. Consumer side: the test writes the contract

The consumer's test declares the interactions it needs, starts a local **mock provider** built from
those declarations, and runs the consumer's **real client code** against it. If the client sends
exactly the declared requests and handles the responses, Pact writes the pact file. The contract is
therefore always proven against real client code, never hand-written.

```python
# orders_client.py — the consumer's real client code (checkout-web)
import json
import urllib.request
from dataclasses import dataclass


@dataclass
class Order:
    id: int
    status: str
    total_cents: int


class OrdersClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get_order(self, order_id: int) -> Order:
        with urllib.request.urlopen(f"{self.base_url}/orders/{order_id}") as resp:
            body = json.load(resp)
        # The consumer reads exactly these three fields, so the pact will require exactly these.
        return Order(id=body["id"], status=body["status"], total_cents=body["totalCents"])
```

```python
# test_orders_pact.py — consumer side: run the REAL client against Pact's mock provider
from pathlib import Path

import pytest
from pact import Pact, match

from orders_client import OrdersClient

PACT_DIR = Path(__file__).parent / "pacts"


@pytest.fixture
def pact():
    pact = Pact("checkout-web", "orders-api").with_specification("V4")
    yield pact
    pact.write_file(PACT_DIR)          # only reached if the test passed


def test_get_paid_order(pact):
    (
        pact.upon_receiving("a request for order 42")
        .given("order 42 exists and is paid")
        .with_request("GET", "/orders/42")
        .will_respond_with(200)
        .with_body(
            {
                "id": match.int(42),
                "status": match.regex("PAID", regex=r"NEW|PAID|SHIPPED"),
                "totalCents": match.int(1999),
            },
            content_type="application/json",
        )
    )

    with pact.serve() as srv:                       # a local mock provider on a random port
        order = OrdersClient(str(srv.url)).get_order(42)

    assert order.status == "PAID"
    assert order.total_cents == 1999
```

(Run with pact-python 3.4 and pytest 9.1: passes and writes
`pacts/checkout-web-orders-api.json`.) The generated pact, trimmed:

```json
{
  "consumer": { "name": "checkout-web" },
  "provider": { "name": "orders-api" },
  "interactions": [
    {
      "type": "Synchronous/HTTP",
      "description": "a request for order 42",
      "providerStates": [ { "name": "order 42 exists and is paid" } ],
      "request": { "method": "GET", "path": "/orders/42" },
      "response": {
        "status": 200,
        "headers": { "Content-Type": [ "application/json" ] },
        "body": {
          "contentType": "application/json",
          "content": { "id": 42, "status": "PAID", "totalCents": 1999 }
        },
        "matchingRules": {
          "body": {
            "$.id":         { "combine": "AND", "matchers": [ { "match": "integer" } ] },
            "$.status":     { "combine": "AND", "matchers": [ { "match": "regex", "regex": "NEW|PAID|SHIPPED" } ] },
            "$.totalCents": { "combine": "AND", "matchers": [ { "match": "integer" } ] }
          }
        }
      }
    }
  ],
  "metadata": { "pactSpecification": { "version": "4.0" } }
}
```

### Matchers: say what matters, not the example

The example values (`42`, `"PAID"`, `1999`) are what the mock returns to the consumer. The
**matching rules** are what the provider must satisfy. Without matchers the provider would have to
return exactly `1999`, which couples the contract to test data.

| Matcher (pact-python `match.`) | Provider must return |
|---|---|
| `int(42)`, `number(...)`, `str("x")`, `bool(...)` / `like(...)` | A value of the same type |
| `regex("PAID", regex=...)` | A string matching the regex |
| `each_like({...}, min=1)` | An array of at least *min* items, each shaped like the template |
| `datetime("2026-03-01T12:00:00Z", format=...)`, `uuid()` | A value in that format |
| `includes("...")` | A string containing the substring |

Rules of thumb for the consumer side:

- **Only include fields the consumer reads.** An extra field in the pact is a promise the provider
  can never remove.
- **Use type matchers by default**, exact values only where the value is part of the protocol
  (an enum the code branches on, a header).
- **Don't test the provider's business logic in the pact.** "Returns 400 when the quantity is
  negative" is fine as a contract; "applies the right tax rate" belongs in the provider's own tests.

## 2. Provider side: verify against the real service

The provider's CI fetches every relevant pact, starts the **real** provider (real code, usually a
test database), and for each interaction: calls the **state handler** to set up the provider state,
replays the request, and checks the response against the matching rules. Extra fields in the
response are allowed; missing or mistyped fields fail.

```python
# orders_api.py — the provider (orders-api): a tiny stdlib HTTP service
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ORDERS: dict[int, dict] = {}          # the provider's "database"
RENAME_TOTAL = False                  # flip to True to simulate a breaking change


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        order_id = int(self.path.rsplit("/", 1)[-1])
        order = ORDERS.get(order_id)
        if order is None:
            self.send_response(404)
            self.end_headers()
            return
        key = "total_cents" if RENAME_TOTAL else "totalCents"
        body = json.dumps({"id": order_id, "status": order["status"], key: order["total"],
                           "currency": "USD"}).encode()   # extra fields are fine: nobody reads them
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):     # keep test output quiet
        pass


def make_server() -> ThreadingHTTPServer:
    return ThreadingHTTPServer(("localhost", 0), Handler)
```

```python
# test_provider_verify.py — provider side: replay every interaction in the pact against the REAL service
import threading
from pathlib import Path

import pytest
from pact import Verifier

import orders_api

PACT_FILE = Path(__file__).parent / "pacts" / "checkout-web-orders-api.json"


@pytest.fixture
def provider_url():
    server = orders_api.make_server()
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield f"http://localhost:{server.server_port}"
    server.shutdown()


def order_42_is_paid(action: str = "setup", **_):
    """Provider state: put the provider into the state the consumer assumed."""
    if action == "setup":
        orders_api.ORDERS[42] = {"status": "PAID", "total": 1999}
    else:
        orders_api.ORDERS.clear()


def verifier(url: str) -> Verifier:
    return (
        Verifier("orders-api")
        .add_transport(url=url)
        .add_source(PACT_FILE)             # in CI: .broker_source(BROKER_URL, token=...) instead
        .state_handler({"order 42 exists and is paid": order_42_is_paid}, teardown=True)
    )


def test_provider_honours_the_pact(provider_url):
    verifier(provider_url).verify()        # raises if any interaction fails


def test_renaming_a_field_breaks_the_build(provider_url, monkeypatch):
    monkeypatch.setattr(orders_api, "RENAME_TOTAL", True)
    with pytest.raises(RuntimeError):
        verifier(provider_url).verify()
```

(Both tests pass.) With the rename switched on, the verifier's report is exactly what the Orders
team sees in CI:

```text
Verifying a pact between checkout-web and orders-api

  a request for order 42 (0s loading, 8ms verification)
     Given order 42 exists and is paid
    returns a response which
      has status code 200 (OK)
      includes headers
        "Content-Type" with value "application/json" (OK)
      has a matching body (FAILED)

Failures:

1) Verifying a pact between checkout-web and orders-api Given order 42 exists and is paid - a request for order 42
    1.1) has a matching body
           $ -> Actual map is missing the following keys: totalCents
```

Notice what did **not** fail: the provider returns an extra `currency` field. No consumer reads it,
so it is not in any pact, and Orders may add, change or remove it freely. A schema diff would treat
removing it as a breaking change; a consumer-driven contract knows nobody cares.

### Provider states

Provider states keep each interaction independent: the consumer names the precondition
(`given("order 42 exists and is paid")`), and the provider team implements a handler that makes it
true, typically by inserting rows into a test database or configuring a stub of the provider's own
downstream dependencies. States can take parameters (`given("an order exists", id=42)`). Keep state
names about **data**, not about test steps, and share a vocabulary between the teams; a state
explosion (hundreds of bespoke states) usually means the pacts are testing business logic.

For providers written in other languages, verification runs through that language's Pact library
or the standalone `pact_verifier_cli`, with provider states exposed on a test-only HTTP endpoint.
`API/REST/labs/golang/08_provider_verification_and_can_i_deploy/` builds a verifier and a
broker from scratch in Go.

## 3. The Pact Broker and `can-i-deploy`

Passing tests on two laptops is not enough. You need to know, for the **exact versions** about to be
deployed, that each consumer's pact was verified by the provider version it will talk to **in that
environment**. That bookkeeping is the broker's job (the open-source **Pact Broker**, or the hosted
**PactFlow**).

```arch
%% caption: Both pipelines report to the broker; each deploy asks can-i-deploy for its target environment and records the deployment afterwards.
grid 175x105
group cpipe "Consumer CI (checkout-web)" color=blue icon=git
node ctest "Pact tests" at 0,0 in cpipe shape=card icon=code sub="write the pact"
node cpub "Publish pact" at 0,1 in cpipe shape=card icon=file sub="version = git SHA"
node cdeploy "can-i-deploy" at 0,2 in cpipe shape=diamond color=amber
node broker "Pact Broker" at 1,1 icon=db sub="pacts + results + envs"
group ppipe "Provider CI (orders-api)" color=green icon=git
node pverify "Verify pacts" at 2,0 in ppipe shape=card icon=check sub="real service"
node presult "Publish results" at 2,1 in ppipe shape=card icon=file sub="version = git SHA"
node pdeploy "can-i-deploy" at 2,2 in ppipe shape=diamond color=amber
node prod "Production" at 1,3 icon=cloud sub="record-deployment"
ctest -> cpub
cpub -> broker
broker ..> pverify : "webhook"
pverify -> presult
presult -> broker
broker -> cdeploy
broker -> pdeploy
cdeploy -> prod : "yes"
pdeploy -> prod : "yes"
```

### Versions, branches and environments

- **Version every publish with the git commit SHA**, never a hand-bumped number. The broker must
  know exactly which code produced which pact and which verification.
- **Record the branch** (`--branch main`, a feature branch) so providers can verify "what's on
  consumers' main branch" and matching feature branches.
- **Record deployments**: after each deploy, `record-deployment` tells the broker which version runs
  in which environment. That is what makes `can-i-deploy --to-environment production` meaningful.

```bash
# consumer CI, after the pact tests pass
pact-broker publish ./pacts \
  --consumer-app-version "$GIT_SHA" --branch "$GIT_BRANCH" \
  --broker-base-url "$PACT_BROKER_BASE_URL" --broker-token "$PACT_BROKER_TOKEN"

# any pipeline, right before deploying version $GIT_SHA of an app
pact-broker can-i-deploy --pacticipant checkout-web --version "$GIT_SHA" \
  --to-environment production --retry-while-unknown 30 --retry-interval 10

# right after the deploy succeeds
pact-broker record-deployment --pacticipant checkout-web --version "$GIT_SHA" \
  --environment production
```

(`pact-broker` is the Pact Broker client CLI, also shipped as the `pactfoundation/pact-cli` Docker
image; the broker URL and token can come from the `PACT_BROKER_BASE_URL` / `PACT_BROKER_TOKEN`
environment variables.)

### The matrix

The broker keeps a **matrix**: rows of (consumer version, provider version, verification result).
`can-i-deploy checkout-web@abc123 --to-environment production` asks: for every provider that
`checkout-web` has a pact with, is there a **successful** verification between `abc123`'s pact and
the provider version **currently recorded in production**? And symmetrically, when a provider
deploys: does this provider version successfully verify the pacts of every consumer version
currently in production?

A missing verification is a **no**, not a yes. `--retry-while-unknown` makes the consumer pipeline
wait for the provider's verification run, which is usually triggered by a webhook.

### Which pacts the provider verifies

The provider does not verify "the latest pact"; it verifies a set chosen by **consumer version
selectors**:

```python
# ci_verifier.py — the same verification in CI, pulling pacts from the broker
import os

from pact import Verifier

from test_provider_verify import order_42_is_paid


def broker_verifier(provider_url: str) -> Verifier:
    return (
        Verifier("orders-api")
        .add_transport(url=provider_url)
        .broker_source(os.environ["PACT_BROKER_BASE_URL"],
                       token=os.environ["PACT_BROKER_TOKEN"], selector=True)
        .consumer_version(main_branch=True)          # what consumers are about to release
        .consumer_version(deployed_or_released=True) # what is running in any environment
        .consumer_version(matching_branch=True)      # a consumer branch with the same name
        .include_pending()                           # new, unverified pacts can't break the build
        .include_wip_since("2026-01-01")
        .build()
        .state_handler({"order 42 exists and is paid": order_42_is_paid}, teardown=True)
        .set_publish_options(version=os.environ["GIT_SHA"], branch=os.environ["GIT_BRANCH"])
    )
```

(The builder chain constructs cleanly against pact-python 3.4; running it needs a broker.)

- **Pending pacts**: a pact whose content the provider's main branch has never successfully
  verified is "pending", and its failures are reported but don't fail the provider build. Without
  this, any consumer could break the provider's build by publishing an expectation the provider has
  not implemented yet.
- **WIP pacts**: pending pacts from other branches are also verified, so a consumer gets feedback on
  a feature-branch pact without the provider changing its configuration.
- **Webhooks**: the broker fires the `contract_requiring_verification_published` event when a pact
  with new content arrives, triggering a provider verification build for exactly the provider
  versions that need it.

This whole handshake (consumer publishes, broker triggers, provider verifies, the gate reads the
matrix) is easiest to understand in motion:

<div class="lab" data-viz="flow-pact"></div>

## 4. Evolving an API without breaking consumers

Contract tests tell you a change is breaking; they don't make it safe. The safe patterns:

| Change | Safe? | How |
|---|---|---|
| Add an optional response field | Yes | Consumers ignore unknown fields (**tolerant reader**) |
| Add an optional request field | Yes | Provider defaults it |
| Remove a response field **no pact uses** | Yes | The broker shows nobody reads it |
| Remove a field a consumer reads | No | Consumer stops reading it first, deploys; then the provider removes it |
| Rename a field | No | **Expand and contract**: provider returns both → consumers switch → provider drops the old one |
| Change a field's type or meaning | No | Add a new field (or a new version) instead |
| Make a request field required | No | Only after every consumer sends it |

A rename therefore takes **three deploys in a forced order**, and `can-i-deploy` enforces the
order: the consumer version that reads `total_cents` cannot reach production until a provider version
that returns `total_cents` is there, and the provider version that stops returning `totalCents` cannot
reach production while any deployed consumer still reads it. See
[Data Design and Schema Evolution in Code](../SoftwareDesign/09_data_design_and_schema_evolution.md) and
[API Design — Low Level](../SystemDesign/building_blocks/04_api_design_low_level.md) for the versioning side.

## 5. Messages, gRPC and GraphQL

Contracts aren't only for HTTP:

- **Message pacts** (asynchronous): the consumer is the message **reader** (a Kafka consumer, an SQS
  worker). Its test declares the message it expects and runs its real handler on it. The provider
  (the producer) proves in its own test that the function that builds the message produces a
  matching payload. No broker cluster is involved in either test.
- **Pact specification V4** (current) supports HTTP, asynchronous messages and synchronous messages
  in one file, plus **plugins**: the protobuf/gRPC plugin, CSV, and others.
- **gRPC / protobuf**: schema compatibility is also checkable with `buf breaking`, which catches
  wire-incompatible changes (renumbered fields, changed types). Buf knows the schema, not which fields
  consumers actually use, so the two approaches complement each other.
- **GraphQL**: consumers send queries naming the exact fields they use, so logging real queries
  (persisted queries) plus schema checks against them gives a similar "who uses what" view.

## 6. Other approaches, and when to use which

| Approach | Contract comes from | Examples | Best for |
|---|---|---|---|
| **Consumer-driven** | Consumer tests (actual usage) | Pact | Internal services with known consumers that can run tests |
| **Provider-driven** | Provider-written contracts; stubs generated for consumers | Spring Cloud Contract | Provider-led teams, especially JVM |
| **Schema / spec-based** | OpenAPI, protobuf, AsyncAPI, JSON Schema | `oasdiff`, `buf breaking`, Specmatic, Schemathesis | Public APIs with unknown consumers; catching wire-level breaks |
| **Bi-directional** | Consumer pacts compared statically with the provider's OpenAPI (itself tested by the provider's own tool) | PactFlow bi-directional contract testing | Providers who already have a well-tested OpenAPI spec and don't want to run verification |

For a **public API** (unknown consumers who can't send you pacts), consumer-driven contracts don't
apply: use explicit versioning, a schema-diff gate in CI, deprecation windows, and usage telemetry.

### Pitfalls

- **Over-specified pacts**: exact values everywhere; every provider data change breaks them.
- **Pacts as functional tests**: asserting business rules through the contract; they belong in the
  provider's unit tests.
- **Hand-written pacts or mocks** that no consumer test produced: that is just a second opinion about
  the API, the original problem again.
- **Skipping `can-i-deploy` or `record-deployment`**: the tests pass but nothing stops an incompatible
  deploy order, which is the main reason to have a broker.
- **Verifying only "latest"**: the provider must verify what is deployed, not only what is newest.

## Common interview questions

**What is contract testing and what problem does it solve?**
Checking each side of an integration separately against a shared contract, so incompatible changes
are caught in the changing team's CI without a shared E2E environment. It closes the gap where both
sides' tests pass against different ideas of the same API.

**Walk me through the Pact workflow.**
The consumer's test declares interactions, runs its real client against a Pact mock provider, and
writes a pact file, which CI publishes to the broker tagged with the git SHA and branch. A webhook
triggers provider verification: set provider states, replay requests against the real provider,
match responses, publish results. Before any deploy, `can-i-deploy` checks the matrix for the target
environment; after the deploy, `record-deployment`.

**Why consumer-driven rather than just sharing an OpenAPI spec?**
A spec says what the provider offers; a pact says what each consumer actually uses. That lets the
provider remove unused fields safely and pinpoints which consumer a change breaks. A spec diff can't
tell unused fields from used ones. For public APIs with unknown consumers, spec-based checks are the
right tool.

**What is a provider state?**
A named precondition the consumer assumes for an interaction, such as "order 42 exists". The
provider implements a handler that sets it up before the request is replayed, which keeps each
interaction independent and deterministic.

**What does `can-i-deploy` check?**
That the version you want to deploy has successful verification results against the versions of all
its integration partners currently recorded in the target environment, in both directions. Missing
results count as failure.

**What are pending and WIP pacts for?**
To stop a consumer from breaking the provider's build with a new expectation the provider hasn't
implemented. Pending pacts report failures without failing the build until the provider's main
branch has verified them once; WIP pacts extend verification to other branches' new pacts
automatically.

**How do you rename a field safely?**
Expand and contract: the provider adds the new field alongside the old one and deploys; consumers
switch to the new field and deploy; once no deployed consumer reads the old field (the broker shows
it), the provider removes it. `can-i-deploy` enforces the order.

**Does contract testing replace E2E tests?**
It replaces most of the cross-service E2E tests whose job was to check integration shape. You still
want a thin E2E layer for critical journeys and to catch what contracts don't cover: configuration,
networking, auth, and semantic mismatches that satisfy the structure.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — (intern) | Can explain why two services' separate green tests don't prove they work together |
| Junior (L3) | Software Engineer I | L3 | Writes a consumer pact test with type matchers; reads a verification failure and knows which side broke |
| Mid (L4) | Software Engineer II | L4 | Implements provider states and verification in CI; publishes with git SHA and branch; applies tolerant reader and additive changes |
| Senior (L5) | Senior Software Engineer | L5 | Designs the broker workflow: selectors, pending/WIP, webhooks, `can-i-deploy` gates, `record-deployment`; plans expand-and-contract migrations across teams |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7 | Chooses the contract strategy per boundary (consumer-driven, schema-based, bi-directional, public API versioning); replaces a flaky shared E2E environment with contracts org-wide; sets API-evolution policy |

## Interview checklist

- [ ] I can explain the Monday/Tuesday rename story and why both test suites stayed green.
- [ ] I can write a consumer pact test and describe what the pact file contains.
- [ ] I can explain matchers and why pacts shouldn't pin example values.
- [ ] I can implement provider states and run verification against a real provider.
- [ ] I can explain the broker matrix, `can-i-deploy`, and `record-deployment`.
- [ ] I can explain consumer version selectors, pending pacts, WIP pacts and webhooks.
- [ ] I can plan a field rename with expand and contract and say which deploy goes first.
- [ ] I can compare consumer-driven, provider-driven, schema-based and bi-directional approaches.
- [ ] I can say when contract testing doesn't apply (public APIs) and what to do instead.

Related: [Consumer driven contracts pact](../API/REST/labs/python/06_consumer_driven_contracts_pact.py) (a Pact-style consumer and
verifier built from scratch), `API/REST/labs/golang/08_provider_verification_and_can_i_deploy/`
(a broker and can-i-deploy from scratch), [Integration and End-to-End (E2E) Testing](03_integration_and_e2e.md),
[Continuous Deployment (CD) and Delivery](../CICD/02_cd_and_delivery.md), [API Design — Low Level](../SystemDesign/building_blocks/04_api_design_low_level.md).
