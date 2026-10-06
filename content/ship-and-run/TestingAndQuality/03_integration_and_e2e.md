# Integration and End-to-End (E2E) Testing

Unit tests prove that the gears work in isolation. Integration tests prove that the gears
mesh: that your SQL runs on the real database, your client speaks the real protocol, and your
message really lands on the topic. End-to-end tests prove the whole machine works from the
user's side. This chapter covers what each kind of test is for, how to run real dependencies
in tests with **Testcontainers**, how to keep test data isolated, how to write E2E tests with
**Playwright** that aren't flaky, and where each kind belongs in a pipeline.

## Foundations — What does "integration" add that unit tests can't?

### The gap unit tests leave

In [Test Doubles: Mocks, Stubs, and Fakes](02_test_doubles.md) the sign-up service was tested against a fake repository, a Python
dict. That test can never catch:

- a typo in the SQL, or SQL that works on SQLite but not Postgres;
- a missing index, a unique constraint, a `NOT NULL` column the migration forgot;
- an ORM mapping that silently drops a field;
- a timezone lost in a round-trip through a `timestamp without time zone` column;
- a Kafka producer configured with the wrong serializer;
- an HTTP client that sends `Content-Type: text/plain`.

These are **wiring bugs**: every unit is right and the joins between them are wrong. They are
exactly what integration tests exist to catch.

### The three levels, in plain words

| Level | Question it answers | Real parts | Replaced parts |
|---|---|---|---|
| **Unit** | Is this logic right? | One function/class (plus cheap collaborators) | Everything with I/O |
| **Integration (narrow)** | Does my code talk to *this one* dependency correctly? | Your adapter + one real dependency (Postgres, Redis, Kafka, an HTTP API) | Everything else |
| **Component / service test** | Does my service, as deployed, behave correctly through its API? | The whole service + its own datastores, in containers | Other teams' services (stubs, contract-tested) |
| **End-to-end (broad)** | Can a user do the thing? | Every service, a real browser or client | Only true externals (payment provider sandbox) |

Martin Fowler's distinction between **narrow** integration tests (one boundary at a time, with
everything else doubled) and **broad** ones (many live services) is the practical one. Narrow
tests are fast and precise; broad ones are slow and flaky. Most of your integration tests
should be narrow.

### An everyday example

A repository with real SQL, tested against a real database. SQLite ships with Python, so this
version runs anywhere; §2 shows the same pattern against Postgres in a container.

```python
# orders_repo.py — a repository with real SQL, the thing an integration test should exercise
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY,
    customer    TEXT    NOT NULL,
    total_cents INTEGER NOT NULL CHECK (total_cents >= 0),
    status      TEXT    NOT NULL DEFAULT 'NEW'
);
"""


class OrdersRepo:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(self, customer: str, total_cents: int) -> int:
        cur = self.conn.execute(
            "INSERT INTO orders (customer, total_cents) VALUES (?, ?)", (customer, total_cents))
        return cur.lastrowid

    def mark_paid(self, order_id: int) -> bool:
        cur = self.conn.execute(
            "UPDATE orders SET status = 'PAID' WHERE id = ? AND status = 'NEW'", (order_id,))
        return cur.rowcount == 1

    def status(self, order_id: int) -> str | None:
        row = self.conn.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
        return row[0] if row else None
```

```python
# conftest.py — one database per session, one rolled-back transaction per test
import sqlite3

import pytest

from orders_repo import SCHEMA


@pytest.fixture(scope="session")
def db_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("db") / "test.sqlite"
    conn = sqlite3.connect(path)
    conn.executescript(SCHEMA)          # "run the migrations" once
    conn.close()
    return path


@pytest.fixture
def conn(db_path):
    conn = sqlite3.connect(db_path, isolation_level=None)   # manage transactions by hand
    conn.execute("BEGIN")
    yield conn
    conn.execute("ROLLBACK")            # every test leaves the database exactly as it found it
    conn.close()
```

```python
# test_orders_repo.py
import sqlite3

import pytest

from orders_repo import OrdersRepo


def test_new_order_starts_as_new(conn):
    repo = OrdersRepo(conn)
    oid = repo.create("alice", 1999)
    assert repo.status(oid) == "NEW"


def test_mark_paid_is_idempotent(conn):
    repo = OrdersRepo(conn)
    oid = repo.create("alice", 1999)
    assert repo.mark_paid(oid) is True
    assert repo.mark_paid(oid) is False          # second call changes nothing
    assert repo.status(oid) == "PAID"


def test_database_rejects_negative_totals(conn):
    # A constraint that lives in the schema: a fake repository would never catch this.
    with pytest.raises(sqlite3.IntegrityError):
        OrdersRepo(conn).create("mallory", -5)


def test_previous_tests_left_no_rows(conn):
    assert conn.execute("SELECT count(*) FROM orders").fetchone()[0] == 0
```

(Run with pytest 9.1: 4 passed.) Two ideas carry over to every integration suite: **create
the expensive thing once** (the database, the schema) and **isolate the cheap thing per test**
(the rows, via a rolled-back transaction).

## 1. The golden rule: don't mock your own database

A mock of your own database encodes what you *think* the database does. The bugs integration
tests catch are precisely the places where that belief is wrong: constraint behaviour,
isolation levels, `NULL` semantics, collation and case sensitivity, JSON operators, `ON
CONFLICT`, time zones, and dialect differences.

Corollaries:

- **Test against the same engine and major version as production.** SQLite or H2 as a stand-in
  for Postgres misses exactly the dialect bugs you care about. SQLite is fine above as a
  self-contained demonstration; a Postgres service should test on Postgres.
- **Run the real migrations** in the test setup, so the migration scripts are themselves tested.
- **Keep the fake for unit tests** and keep it honest with a shared contract suite
  ([Test Doubles: Mocks, Stubs, and Fakes](02_test_doubles.md) §3).

## 2. Testcontainers: real dependencies, started from the test

**Testcontainers** is a family of libraries (Java, Go, Python, .NET, Node, Rust and others)
that starts throwaway Docker containers from test code, waits until they are ready, hands the
test a connection string, and removes them afterwards. It began as a Java project; since 2023
it has been backed by Docker Inc., which acquired AtomicJar.

```arch
%% caption: The test asks Docker for a container on a random host port, waits for readiness, runs against it, and the Ryuk reaper removes anything a crashed run leaves behind.
grid 175x110
group host "CI runner or laptop" color=slate icon=server
node test "Test process" at 0,0 in host shape=card icon=code sub="pytest / go test / JUnit"
node pg "Postgres 17" at 2,0 in host icon=postgresql sub="random host port"
node docker "Docker Engine" at 0,1 in host icon=docker-icon
node ryuk "Ryuk reaper" at 2,1 in host shape=card icon=delete sub="kills orphans"
test ==> pg : "SQL"
test -> docker : "start"
docker -> pg : "run"
docker -> ryuk : "session label"
ryuk:R ..> pg:R : "on crash"
```

How it works:

1. The library talks to the Docker API (local Docker, Docker Desktop, Podman in Docker-compatible
   mode, or a remote/cloud engine).
2. It starts the container with the port mapped to a **random free host port**, so parallel
   runs don't collide, and waits using a **wait strategy**: a log line, an open port, an HTTP
   health check, or a command that succeeds (`pg_isready`).
3. It starts a small **Ryuk** sidecar that removes every container labelled with this session
   if the test process dies without cleaning up.
4. The test gets the mapped host and port and connects normally.

Python (pytest), one container per test session, one rolled-back transaction per test:

```python
# conftest.py — a real Postgres in Docker for the whole session, a clean transaction per test
import psycopg
import pytest
from testcontainers.community.postgres import PostgresContainer  # testcontainers >= 4.15
# (older 4.x releases: from testcontainers.postgres import PostgresContainer)


@pytest.fixture(scope="session")
def pg_url():
    with PostgresContainer("postgres:17-alpine", driver=None) as pg:   # driver=None -> postgresql://
        url = pg.get_connection_url()
        with psycopg.connect(url, autocommit=True) as conn:
            conn.execute(open("migrations/001_orders.sql").read())    # run migrations once
        yield url
    # leaving the `with` block stops and removes the container


@pytest.fixture
def conn(pg_url):
    with psycopg.connect(pg_url) as conn:      # psycopg 3 opens a transaction on first query
        yield conn
        conn.rollback()                         # undo everything this test wrote
```

```python
# test_orders_pg.py
import psycopg
import pytest


def test_check_constraint_is_enforced(conn):
    with pytest.raises(psycopg.errors.CheckViolation):
        conn.execute("INSERT INTO orders (customer, total_cents) VALUES ('m', -5)")


def test_insert_returns_generated_id(conn):
    (oid,) = conn.execute(
        "INSERT INTO orders (customer, total_cents) VALUES ('alice', 1999) RETURNING id"
    ).fetchone()
    assert oid > 0
```

Go (testcontainers-go v0.44 module API; compiles and `go vet`s cleanly, needs Docker to run):

```go
package orders_test

import (
	"context"
	"testing"

	"github.com/jackc/pgx/v5"
	"github.com/testcontainers/testcontainers-go"
	"github.com/testcontainers/testcontainers-go/modules/postgres"
)

func TestOrdersAgainstRealPostgres(t *testing.T) {
	if testing.Short() {
		t.Skip("needs Docker; skipped with -short")
	}
	ctx := context.Background()

	ctr, err := postgres.Run(ctx, "postgres:17-alpine",
		postgres.WithDatabase("app"),
		postgres.WithUsername("test"),
		postgres.WithPassword("test"),
		postgres.BasicWaitStrategies(), // wait for "ready to accept connections" twice + the port
	)
	testcontainers.CleanupContainer(t, ctr) // terminate when the test ends, even on failure
	if err != nil {
		t.Fatalf("start postgres: %v", err)
	}

	dsn, err := ctr.ConnectionString(ctx, "sslmode=disable")
	if err != nil {
		t.Fatal(err)
	}
	conn, err := pgx.Connect(ctx, dsn)
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { conn.Close(ctx) })

	if _, err := conn.Exec(ctx, `CREATE TABLE orders (
		id BIGSERIAL PRIMARY KEY,
		total_cents BIGINT NOT NULL CHECK (total_cents >= 0))`); err != nil {
		t.Fatal(err)
	}
	if _, err := conn.Exec(ctx, `INSERT INTO orders (total_cents) VALUES (-5)`); err == nil {
		t.Fatal("negative total accepted; want a CHECK constraint violation")
	}
}
```

Postgres logs "ready to accept connections" twice on first start (once for the temporary
init server, once for the real one), which is why naive "wait for the log line" strategies
connect too early; the module's wait strategy accounts for it.

Java (the original, JUnit 5):

```java
@Testcontainers
class UserRepositoryTest {
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:17-alpine");

    @Test
    void savesUser() {
        UserRepository repo = new UserRepository(
            postgres.getJdbcUrl(), postgres.getUsername(), postgres.getPassword());
        repo.save(new User("Alice"));
        assertEquals(1, repo.count());   // not Java's `assert`: it is disabled unless the JVM runs with -ea
    }
}
```

A `static` `@Container` field is started once for the class; an instance field would start a
new container for every test method.

| Concern | Practice |
|---|---|
| Startup cost | A Postgres container starts in ≈ 1–5 s once the image is cached; share it per session/class, never per test |
| Image pulls in CI | Pin tags (`postgres:17-alpine`, or by digest), use a registry mirror, cache images on runners |
| CI runners | Needs a Docker API: a VM-based runner (GitHub-hosted Linux runners have Docker), Docker-in-Docker, or a remote/cloud container runtime |
| Parallel test workers | Each `pytest-xdist` worker gets its own container, or all share one with a database/schema per worker |
| Local speed | Reusable containers (`testcontainers.reuse.enable=true` in Java) keep a container alive between runs; never in CI |
| Many services | Testcontainers modules exist for Kafka, Redis, LocalStack (AWS APIs), Elasticsearch, MinIO and more; Docker Compose support for full stacks |

## 3. Keeping test data isolated

Integration tests fail in confusing ways when they share data. Pick one of these, from
fastest to most isolated:

| Technique | How | Watch out for |
|---|---|---|
| **Rollback per test** | Begin a transaction in the fixture, roll back in teardown | Code under test that commits itself, or opens its own connections, escapes the transaction; use savepoints / "join the outer transaction" features in the ORM |
| **Truncate per test** | `TRUNCATE ... RESTART IDENTITY CASCADE` after each test | Slower as tables grow; must list every table |
| **Template database** | Postgres `CREATE DATABASE t_42 TEMPLATE app_template` per test or per worker | Creating a DB costs tens of ms (≈); great for parallel workers |
| **Unique data per test** | Every test creates its own customer `test-<uuid>` and only reads its own rows | Needs discipline; works even against shared environments |
| **Fresh container per test** | Maximum isolation | Seconds per test; only for tests that break the server itself |

Also: **never depend on test order**, generate IDs rather than hard-coding `id=1`, and assert
on the rows *this test* created rather than on table counts when data may be shared.

## 4. Testing HTTP services and other boundaries

**Your own HTTP API, in-process.** Most frameworks let you call the app without a network:
FastAPI/Starlette `TestClient` (built on `httpx`), Flask's `app.test_client()`, Django's test
client, Go's `httptest.NewRecorder()` with your handler. These are fast and still exercise
routing, validation, serialization, and middleware.

**Your own service, out of process (component test).** Build the real container image, start it
with its real datastores via Testcontainers or Compose, and drive it through its public API.
This catches configuration and packaging bugs (missing env var, wrong port, migrations not run
on start) that in-process tests can't.

**Someone else's HTTP API.** Options, in order of preference:

1. A **contract test** so your stub is guaranteed to match what the provider actually serves
   ([Microservices: Contract Testing](05_contract_testing.md)).
2. A **stub server** (WireMock, `pytest-httpserver`, `httptest`) for the component test.
3. The provider's **sandbox** (Stripe test mode) in a small number of slower tests, run on a
   schedule so their flakiness doesn't block merges.

**Message brokers.** Start Kafka (KRaft mode; ZooKeeper was removed in Kafka 4.0) or RabbitMQ in a
container, produce, and **poll with a deadline** for the consumer's effect. Never
`sleep(5)` and hope. Java's Awaitility, a small `wait_until(predicate, timeout)` helper in
Python, or `require.Eventually` in Go's testify all implement this.

**Faults at the boundary.** Toxiproxy (a TCP proxy you control from the test) injects latency,
dropped connections, and bandwidth limits between your service and a real dependency, so you
can test timeouts and retries deterministically. See [Resilience: Chaos Engineering](06_chaos_engineering.md) §4.

## 5. End-to-end tests

E2E tests drive the deployed system the way a user does: a real browser (or mobile app, or
public API client) against the real frontend, backend services, and datastores.

```arch
%% caption: An E2E run: the runner seeds data through the API, then drives a real browser through the deployed stack and records a trace for debugging.
grid 165x110
node runner "Test runner" at 0,0 shape=card icon=code sub="Playwright + pytest"
group env "Test env" color=blue icon=cloud
node web "Web frontend" at 1,1 in env icon=browser
node api "API gateway" at 2,1 in env icon=gateway
node svc "Services" at 2,2 in env icon=service
node db "Databases" at 2,3 in env icon=db
node browser "Headless browser" at 0,1 icon=chrome sub="Chromium / WebKit"
node trace "Trace artifact" at 0,2 shape=card icon=file sub="DOM, network, video"
runner -> browser : "drive"
browser -> web
web -> api -> svc -> db
runner ..> api : "seed via API"
browser ..> trace : "on failure"
```

- **Pros**: the highest confidence per test; catches problems no lower layer can (a CDN
  misconfiguration, a broken JS bundle, a cookie domain).
- **Cons**: slow (seconds to minutes each), expensive environments, flaky, and a failure says
  only "something is wrong somewhere".

**Keep E2E tests to the critical journeys**: sign up, log in, search, add to cart, check out,
the one flow that makes money. Test the edge cases (invalid password, empty cart, expired
coupon) in unit and integration tests, where they are fast and precise. A common rule of thumb
is tens of E2E tests for a product, not thousands.

### Tools in 2026

| Tool | Model | Strengths | Limits |
|---|---|---|---|
| **Playwright** (Microsoft) | Drives Chromium, Firefox and WebKit over their debugging protocols; runners for TS/JS, Python, Java, .NET | Auto-waiting, web-first assertions, parallel isolated browser contexts, trace viewer, network interception, codegen | Patched browser builds rather than branded browsers for Firefox/WebKit |
| **Cypress** | Runs inside the browser alongside the app; JS/TS only | Excellent interactive debugging, time-travel UI | Historically single-tab/single-origin limits (relaxed by `cy.origin`); WebKit support experimental |
| **Selenium 4** | W3C WebDriver (and WebDriver BiDi) against real branded browsers; every major language | The standard; Selenium Grid; real Chrome/Firefox/Safari/Edge | More manual waiting; slower |
| **Appium / Espresso / XCUITest** | Mobile | Native apps | Device farms are costly |

### A Playwright test that isn't flaky

```python
# test_checkout_e2e.py — pytest-playwright provides the `page` fixture (one fresh browser context per test)
import re

from playwright.sync_api import Page, expect

BASE = "https://staging.shop.example.com"


def test_signed_in_user_can_buy_one_item(page: Page, seeded_user):
    # Arrange through the API, not the UI: faster and not what this test is about
    page.goto(f"{BASE}/login")
    page.get_by_label("Email").fill(seeded_user.email)
    page.get_by_label("Password").fill(seeded_user.password)
    page.get_by_role("button", name="Sign in").click()

    # Act: the one journey this E2E test exists for
    page.goto(f"{BASE}/products/blue-mug")
    page.get_by_role("button", name="Add to cart").click()
    page.get_by_role("link", name="Cart").click()
    page.get_by_role("button", name="Checkout").click()

    # Assert with web-first assertions: they retry until true or the timeout (5 s default)
    expect(page).to_have_url(re.compile(r"/orders/\d+$"))
    expect(page.get_by_role("heading", name="Thank you for your order")).to_be_visible()
```

(`seeded_user` is a project fixture that creates a user through the API; the test collects
with pytest-playwright 0.9 / Playwright 1.63.) What makes it robust:

1. **User-facing locators**: `get_by_role`, `get_by_label`, `get_by_text`, or a dedicated
   `data-testid`. Never CSS paths like `div > div:nth-child(3) > button`, which break on every
   layout change. (The classic complaint, "a button colour changes and the test breaks", is a symptom of
   bad locators, not of E2E testing itself.)
2. **No sleeps.** Playwright waits for an element to be attached, visible, stable, enabled and
   receiving events before clicking (**actionability checks**), and `expect(...)` retries until
   the condition holds.
3. **Seed state through the API or database**, and reuse a logged-in session
   (`storage_state`) instead of logging in through the UI in every test. Only the login test
   should use the login form.
4. **Isolation**: each test gets a new browser context (cookies, storage) and its own data.
5. **Debuggability**: record traces on failure (`--tracing retain-on-failure`) and open them
   with `playwright show-trace`; you get DOM snapshots, network, console and a timeline for each
   step.
6. **Page objects** (a class per page exposing `checkout()`, not raw locators) keep a UI change
   to one place.

### Where E2E tests run

| Environment | Use |
|---|---|
| **Ephemeral per-PR environment** | Spun up per pull request (Kubernetes namespace, preview deployment); the best signal before merge, if you can afford it |
| **Shared staging** | Post-merge or pre-release suite; watch out for tests colliding on shared data and for staging drifting from production |
| **Production (synthetic monitoring)** | A few read-only or test-account journeys run every few minutes against production; they are monitoring, and they page ([Deployment Strategies](../CICD/03_deployment_strategies.md) covers canaries) |

## 6. Where each layer runs in the pipeline

```arch
%% caption: Cheap checks gate every commit; expensive ones run later and less often, each stage filtering what reaches the next.
route straight
grid 150x100
node commit "Push / PR" at 0,0 shape=pill color=slate
node unit "Lint + unit" at 1,0 shape=card icon=code color=green sub="≈ 1–5 min"
node integ "Integration" at 2,0 shape=card icon=docker-icon sub="containers, ≈ 5–15 min"
node e2e "E2E (critical)" at 3,0 shape=card icon=browser color=red sub="preview env"
node merge "Merge + deploy" at 3,1 shape=pill color=green
node synth "Synthetic checks" at 2,1 shape=card icon=monitor sub="prod, every few min"
commit -> unit -> integ -> e2e
e2e -> merge
merge -> synth
```

Durations are typical targets (≈), not rules. The principle: the earlier and more often a
stage runs, the faster and more reliable it must be. See [Continuous Integration (CI) Fundamentals](../CICD/01_ci_fundamentals.md) and
[Continuous Deployment (CD) and Delivery](../CICD/02_cd_and_delivery.md) for how these stages are wired.

## Common interview questions

**What is the difference between unit, integration and E2E tests?**
Unit: one piece of logic, no I/O, milliseconds. Integration: your code against one real
dependency (DB, broker, HTTP), catching wiring bugs like SQL errors and serialization. E2E: the
deployed system through its UI or public API, the highest confidence but slow, flaky and hard to
localise.

**Why not mock the database in integration tests?**
The bugs you are hunting are exactly where your mental model of the database is wrong:
constraints, isolation levels, NULLs, dialect, time zones. A mock encodes that mental model.
Use the same engine and version as production, with real migrations.

**How does Testcontainers work?**
It uses the Docker API to start a container on a random host port, waits with a strategy (log
line, port, health check), gives the test the connection details, and removes the container
afterwards; a Ryuk sidecar cleans up if the process crashes. Share containers per session; isolate
data per test.

**How do you keep integration tests independent?**
Transaction rollback per test (watch for code that commits itself), truncation, template
databases per worker, or unique data per test. Never rely on order or fixed IDs.

**Why are E2E tests flaky, and how do you reduce it?**
Timing (fixed sleeps), brittle locators, shared data, environment instability, third-party
dependencies. Use auto-waiting and web-first assertions, role/label/test-id locators, seeded
data via API, isolated browser contexts, traces on failure, and keep the suite small.

**How many E2E tests should a product have?**
Enough to cover the critical user journeys (often tens, not thousands). Every other case goes
lower in the pyramid. Each E2E test should justify its minutes of CI time.

**How would you test a service that calls three other teams' services?**
Unit tests with doubles for logic; component tests with the real service and its own datastore
in containers and stubs for the other teams; contract tests to keep those stubs honest; a thin
E2E layer for the critical journey in a shared or ephemeral environment.

**What is synthetic monitoring?**
E2E-style journeys run continuously against production with test accounts. It is monitoring
rather than testing: it detects outages, certificate expiry and CDN problems that pre-release tests
cannot see.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — (intern) | Knows the difference between unit, integration and E2E; can run an existing suite |
| Junior (L3) | Software Engineer I | L3 | Writes integration tests against a real DB with per-test isolation; uses in-process API test clients; writes a Playwright test with good locators |
| Mid (L4) | Software Engineer II | L4 | Sets up Testcontainers fixtures with the right scope; chooses the right layer for each check; debugs flaky E2E tests from traces |
| Senior (L5) | Senior Software Engineer | L5 | Designs a service's test strategy (unit / component / contract / E2E split); owns test-data isolation and CI stage budgets; decides what runs pre-merge vs post-merge |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7 | Sets org-wide environment strategy (ephemeral environments vs shared staging vs testing in production); balances confidence against CI cost and flakiness at scale |

## Interview checklist

- [ ] I can list five kinds of bug that only integration tests catch.
- [ ] I can explain narrow vs broad integration tests and why most should be narrow.
- [ ] I can explain how Testcontainers starts, waits for, and cleans up containers (including Ryuk).
- [ ] I can write a session-scoped container fixture and a per-test rollback fixture.
- [ ] I can compare rollback, truncate, template DB and unique-data isolation.
- [ ] I can explain why polling with a deadline beats `sleep` for async assertions.
- [ ] I can write a Playwright test with role-based locators and web-first assertions.
- [ ] I can say which journeys deserve an E2E test and which cases belong lower.
- [ ] I can place unit, integration, E2E and synthetic checks in a CI/CD pipeline.

Related: [The Testing Pyramid and Unit Tests](01_testing_pyramid.md), [Test Doubles: Mocks, Stubs, and Fakes](02_test_doubles.md), [Microservices: Contract Testing](05_contract_testing.md),
[Resilience: Chaos Engineering](06_chaos_engineering.md), [Continuous Integration (CI) Fundamentals](../CICD/01_ci_fundamentals.md), [Deployment Strategies](../CICD/03_deployment_strategies.md),
`content/languages/PyEngineering/09_database_repository_layer/`, `content/languages/GoEngineering/09_database_repository_layer/`.
