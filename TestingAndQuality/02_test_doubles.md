# Test Doubles: Mocks, Stubs, and Fakes

When a function relies on a database or a third-party API (like Stripe), a unit test cannot
use the real thing: it would be slow, flaky, cost money, or send real emails. You substitute
a **test double**, an object that stands in for the dependency. This chapter covers the five
kinds of double and when each is right, how to build them in Python (`unittest.mock`,
hand-written fakes) and Go (interfaces, `httptest`), the classic mistakes (patching the wrong
name, over-mocking, doubles that drift from reality), and how to control time, the
dependency almost every flaky test forgot.

## Foundations — Why replace a dependency, and with what?

### The problem

Here is a sign-up service. It checks for a duplicate email, stores the user with a 14-day
trial, and sends a welcome email:

```python
# signup.py — the code under test. Dependencies arrive through the constructor (the "seam").
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable, Protocol


@dataclass
class User:
    id: int
    email: str
    trial_ends: datetime


class UserRepository(Protocol):
    def save(self, user: User) -> None: ...
    def get(self, user_id: int) -> User | None: ...
    def by_email(self, email: str) -> User | None: ...


class Mailer(Protocol):
    def send_welcome(self, email: str) -> None: ...


class DuplicateEmail(Exception):
    pass


class SignupService:
    def __init__(self, repo: UserRepository, mailer: Mailer,
                 clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc)):
        self.repo, self.mailer, self.clock = repo, mailer, clock
        self._next_id = 1

    def register(self, email: str) -> User:
        email = email.strip().lower()
        if self.repo.by_email(email) is not None:
            raise DuplicateEmail(email)
        user = User(self._next_id, email, trial_ends=self.clock() + timedelta(days=14))
        self._next_id += 1
        self.repo.save(user)
        self.mailer.send_welcome(email)
        return user
```

To test `register` for real you would need a Postgres server, an SMTP server, and a way to
make "now" a known value so you can check `trial_ends`. All three are slow or
non-deterministic. But `SignupService` doesn't create them; it **receives** them. That place
where you can swap one implementation for another without editing the code under test is
called a **seam** (Michael Feathers' term). Constructor parameters, function parameters,
interfaces, and module attributes are all seams.

```arch
%% caption: The service depends on three interfaces. Production plugs in real implementations; tests plug in doubles at the same seams.
grid 170x100
group prod "Production wiring" color=slate
node pg "Postgres repo" at 0,1 in prod icon=postgresql
node smtp "SMTP mailer" at 0,2 in prod icon=email
node sysclock "System clock" at 0,3 in prod icon=time
group seam "SignupService's seams" color=blue icon=code
node svc "SignupService" at 1,0 in seam shape=card icon=service sub="code under test"
node repo "UserRepository" at 1,1 in seam shape=pill
node mail "Mailer" at 1,2 in seam shape=pill
node clk "clock()" at 1,3 in seam shape=pill
group test "Test wiring" color=green
node fake "Fake repo" at 2,1 in test shape=card icon=table sub="dict in memory"
node spy "Spy mailer" at 2,2 in test shape=card icon=eye sub="records calls"
node frozen "Frozen clock" at 2,3 in test shape=card icon=timer sub="always 2026-03-01"
repo -> pg
mail -> smtp
clk -> sysclock
repo ..> fake
mail ..> spy
clk ..> frozen
```

### The vocabulary

Gerard Meszaros named the kinds of double in *xUnit Test Patterns* (2007), and Martin
Fowler's essay "Mocks Aren't Stubs" made the names common. Many people say "mock" for all of
them, and most libraries (`unittest.mock`, testify) create objects that can play several
roles, but the distinction matters when you choose **what to assert**.

| Double | What it does | You assert on | Example |
|---|---|---|---|
| **Dummy** | Fills a parameter; never actually used | Nothing | `SignupService(repo, mailer=None)` in a test that fails before mailing |
| **Stub** | Returns canned answers (or raises canned errors) | The SUT's output | `repo.by_email.return_value = None` |
| **Spy** | A stub that also records how it was called | The recorded calls, after the fact | `mailer.send_welcome.assert_called_once_with(...)` |
| **Mock** (strict sense) | Pre-programmed with expectations; fails if they are not met | The expectations (verified at the end) | gomock `EXPECT().Charge(500).Return(nil)` |
| **Fake** | A working, simplified implementation | The SUT's output and the fake's state | In-memory repository, SQLite instead of Postgres |

Which one to reach for:

```arch
%% caption: Choosing a double: most tests want a fake or a stub; verify calls only when the call itself is the behaviour.
grid 190x105
node q1 "Is it never really used?" at 1,0 shape=diamond color=amber
node dummy "Dummy" at 0,0 shape=card icon=question sub="None, placeholder"
node q2 "Does logic need real state?" at 1,1 shape=diamond color=amber
node fakeleaf "Fake" at 0,1 shape=card icon=table color=green sub="in-memory repo"
node q3 "Is the call itself the outcome?" at 1,2 shape=diamond color=amber
node stub "Stub" at 0,2 shape=card icon=file sub="canned answers"
node spyleaf "Spy / mock" at 2,2 shape=card icon=eye sub="assert the call"
q1 -> dummy : "yes"
q1 -> q2 : "no"
q2 -> fakeleaf : "yes"
q2 -> q3 : "no"
q3 -> stub : "no"
q3 -> spyleaf : "yes"
```

**State verification vs behaviour verification.** With a stub or fake you check *results*:
the returned user, the row in the fake repository. With a spy or mock you check
*interactions*: which methods were called with which arguments. State checks survive
refactoring; interaction checks break whenever the implementation changes how it talks to
its collaborators, even if the result is identical. Prefer state checks, and check
interactions only when the interaction **is** the behaviour (an email was sent, a payment
was charged exactly once, a message was published).

## 1. Stubs: canned answers and forced errors

A stub makes the dependency return what the test needs so the code can proceed down a
chosen path. Its most valuable use is forcing **error paths** that are hard to trigger for
real: a timeout, a 503, a full disk, a unique-constraint violation.

```python
from unittest.mock import Mock, create_autospec

import pytest

from signup import Mailer, SignupService


def test_stub_forces_an_error_path():
    repo = Mock()
    repo.by_email.return_value = None                         # stub: canned answer
    repo.save.side_effect = ConnectionError("db down")        # stub: canned failure
    svc = SignupService(repo, create_autospec(Mailer, instance=True))
    with pytest.raises(ConnectionError):
        svc.register("bob@example.com")
    svc.mailer.send_welcome.assert_not_called()               # no email for a user we failed to save
```

`side_effect` accepts three things: an exception (class or instance) to raise, an iterable
of successive results (`side_effect=[TimeoutError(), {"ok": True}]` to test a retry), or a
function that computes the result from the arguments.

## 2. Spies and mocks with `unittest.mock`

`unittest.mock` (standard library) gives you `Mock`, `MagicMock` (also supports dunder
methods such as `__len__` and `__enter__`), `AsyncMock` (Python 3.8+, for `async def`), and
`patch`. The `pytest-mock` plugin wraps the same API in a `mocker` fixture that undoes
patches automatically.

```python
# test_signup.py
from datetime import datetime, timezone
from unittest.mock import create_autospec

import pytest

from fakes import FakeUserRepository
from signup import DuplicateEmail, Mailer, SignupService

FROZEN = datetime(2026, 3, 1, 12, 0, tzinfo=timezone.utc)


@pytest.fixture
def mailer():
    # A spy with the real interface: calling a method Mailer doesn't have, or with
    # the wrong arguments, raises instead of silently "working".
    return create_autospec(Mailer, instance=True)


@pytest.fixture
def service(mailer):
    return SignupService(FakeUserRepository(), mailer, clock=lambda: FROZEN)


def test_register_normalises_email_and_sets_trial(service):
    user = service.register("  Alice@Example.COM ")
    assert user.email == "alice@example.com"
    assert user.trial_ends == datetime(2026, 3, 15, 12, 0, tzinfo=timezone.utc)
    assert service.repo.get(user.id) == user          # state check on the fake


def test_register_sends_exactly_one_welcome_email(service, mailer):
    service.register("alice@example.com")
    mailer.send_welcome.assert_called_once_with("alice@example.com")   # interaction check


def test_duplicate_email_is_rejected_and_no_mail_sent(service, mailer):
    service.register("alice@example.com")
    mailer.reset_mock()
    with pytest.raises(DuplicateEmail):
        service.register("ALICE@example.com")
    mailer.send_welcome.assert_not_called()


def test_autospec_catches_a_wrong_signature(mailer):
    with pytest.raises(TypeError):
        mailer.send_welcome("a@example.com", "unexpected extra arg")
```

(The snippets in this chapter were run with pytest 9.1 on Python 3.11: 13 passed.)

### Always spec your mocks

A bare `Mock()` accepts **any** attribute and **any** call, so it keeps "passing" after the
real interface changes. Rename `send_welcome` to `send_welcome_email` in production and a bare
mock still happily records `send_welcome` calls: green tests, broken product.

| Option | Effect |
|---|---|
| `Mock(spec=Mailer)` | Only attributes that exist on `Mailer` are allowed |
| `Mock(spec_set=Mailer)` | Also forbids *setting* attributes that don't exist |
| `create_autospec(Mailer, instance=True)` / `patch(..., autospec=True)` | Recursively specs methods **and their signatures**, so wrong arguments raise `TypeError` |
| `seal(mock)` (3.7+) | After configuring, no new attributes can be created |

`Mock` also guards against one famous typo: attributes starting with `assert`, `assret` (and,
since Python 3.12, `asert`, `aseert`, `assrt`) raise `AttributeError`, because
`mock.assert_called_once_wiht(...)` would otherwise be an auto-created attribute that asserts
nothing.

Useful assertions and attributes: `assert_called_once_with`, `assert_any_call`,
`assert_has_calls([call(...), call(...)], any_order=False)`, `assert_not_called`,
`call_count`, `call_args`, `call_args_list`, and for `AsyncMock`, `assert_awaited_once_with`.

### `patch`: replace a name where it is **looked up**

When the code under test imports a dependency itself instead of receiving it, `patch`
temporarily replaces a **name in a module's namespace**. The rule everyone gets wrong once:
patch the name *where the code under test looks it up*, not where it was defined.

```python
# payments_sdk.py — pretend third-party SDK
def charge(amount_cents: int, token: str) -> dict:
    raise RuntimeError("real network call in a unit test!")
```

```python
# checkout.py
from payments_sdk import charge      # binds the name `charge` inside THIS module


def pay(amount_cents: int, token: str) -> str:
    result = charge(amount_cents, token)
    return "paid" if result["status"] == "succeeded" else "declined"
```

```python
# test_checkout.py
from unittest.mock import patch

import pytest

import checkout


def test_patch_where_the_name_is_looked_up():
    with patch("checkout.charge", return_value={"status": "succeeded"}) as fake_charge:
        assert checkout.pay(500, "tok_visa") == "paid"
    fake_charge.assert_called_once_with(500, "tok_visa")


def test_patching_the_definition_site_does_not_reach_checkout():
    # checkout already holds its own reference to the original function
    with patch("payments_sdk.charge", return_value={"status": "succeeded"}):
        with pytest.raises(RuntimeError, match="real network call"):
            checkout.pay(500, "tok_visa")
```

`from payments_sdk import charge` copies a reference into `checkout`'s namespace at import
time, so replacing `payments_sdk.charge` later changes nothing `checkout` can see. If the code
had done `import payments_sdk` and called `payments_sdk.charge(...)`, then patching
`payments_sdk.charge` would work. Other forms: `patch.object(obj, "attr")`,
`patch.dict(os.environ, {...})`, and `monkeypatch.setattr` in pytest.

Heavy use of `patch` is a design smell: it means dependencies are hidden inside the code
instead of passed in. Passing them in (as `SignupService` does) makes tests simpler and the
dependency graph visible.

## 3. Fakes: the workhorse for domain logic

A fake has a real, working implementation that takes a shortcut unsuitable for production:
a dict instead of Postgres, an in-memory queue instead of Kafka, a local directory instead of
S3.

```python
# fakes.py — a working in-memory implementation, plus the real SQLite one it stands in for.
import sqlite3
from datetime import datetime

from signup import User


class FakeUserRepository:
    def __init__(self):
        self._users: dict[int, User] = {}

    def save(self, user: User) -> None:
        self._users[user.id] = user

    def get(self, user_id: int) -> User | None:
        return self._users.get(user_id)

    def by_email(self, email: str) -> User | None:
        return next((u for u in self._users.values() if u.email == email), None)


class SqliteUserRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        conn.execute("CREATE TABLE IF NOT EXISTS users "
                     "(id INTEGER PRIMARY KEY, email TEXT UNIQUE, trial_ends TEXT)")

    def save(self, user: User) -> None:
        self.conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?)",
                          (user.id, user.email, user.trial_ends.isoformat()))

    def _row(self, row):
        return None if row is None else User(row[0], row[1], datetime.fromisoformat(row[2]))

    def get(self, user_id: int) -> User | None:
        return self._row(self.conn.execute(
            "SELECT id, email, trial_ends FROM users WHERE id = ?", (user_id,)).fetchone())

    def by_email(self, email: str) -> User | None:
        return self._row(self.conn.execute(
            "SELECT id, email, trial_ends FROM users WHERE email = ?", (email,)).fetchone())
```

Fakes are the best default for domain logic: tests read like real usage, check state rather
than calls, and survive refactoring. Their risk is **drift**: the fake slowly stops behaving
like the real thing (the fake allows duplicate emails, Postgres has a unique index), and
tests pass against behaviour production doesn't have.

### Keep the fake honest: one contract suite, two implementations

Run the same behavioural tests against the fake **and** the real implementation. The fake
runs in every unit-test run; the real one runs in the integration stage
([Integration and End-to-End (E2E) Testing](03_integration_and_e2e.md)), against SQLite here or a Testcontainers Postgres in practice.

```python
# test_repo_contract.py — one suite, run against the fake AND the real implementation.
import sqlite3
from datetime import datetime, timezone

import pytest

from fakes import FakeUserRepository, SqliteUserRepository
from signup import User


@pytest.fixture(params=["fake", "sqlite"])
def repo(request):
    if request.param == "fake":
        yield FakeUserRepository()
    else:
        conn = sqlite3.connect(":memory:")
        yield SqliteUserRepository(conn)
        conn.close()


def make_user(uid=1, email="a@example.com"):
    return User(uid, email, datetime(2026, 1, 1, tzinfo=timezone.utc))


def test_get_missing_returns_none(repo):
    assert repo.get(42) is None


def test_save_then_get_roundtrips(repo):
    repo.save(make_user())
    assert repo.get(1) == make_user()


def test_save_same_id_overwrites(repo):
    repo.save(make_user(email="old@example.com"))
    repo.save(make_user(email="new@example.com"))
    assert repo.get(1).email == "new@example.com"
    assert repo.by_email("old@example.com") is None
```

Each test runs twice (`[fake]` and `[sqlite]`). When someone adds a behaviour to the real
repository, they add a test here, and the fake has to keep up. Google calls these
"fidelity" checks and prefers that the team owning a service also ships its fake (the
same idea as Google Cloud's official emulators for Pub/Sub, Spanner and Bigtable).

## 4. Doubles in Go

Go has no monkeypatching; the seam is almost always an **interface** defined by the
consumer, or a field such as a base URL. "Accept interfaces, return structs" is what makes Go
code testable.

```go
// A consumer-defined interface: only the method this package needs.
type Mailer interface {
	SendWelcome(ctx context.Context, email string) error
}

// A hand-written spy: often clearer than a generated mock.
type spyMailer struct {
	mu   sync.Mutex
	sent []string
	err  error // stub a failure when set
}

func (s *spyMailer) SendWelcome(_ context.Context, email string) error {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.sent = append(s.sent, email)
	return s.err
}
```

For HTTP dependencies, `net/http/httptest` starts a real server on localhost, so the real
client code (URL building, headers, JSON decoding, status handling) is exercised:

```go
// rates.go
package rates

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"
)

// Client talks to a currency-rate HTTP API. BaseURL is the seam: tests point it at httptest.
type Client struct {
	BaseURL string
	HTTP    *http.Client
}

func (c *Client) Rate(ctx context.Context, from, to string) (float64, error) {
	req, err := http.NewRequestWithContext(ctx, http.MethodGet,
		fmt.Sprintf("%s/rates?from=%s&to=%s", c.BaseURL, from, to), nil)
	if err != nil {
		return 0, err
	}
	resp, err := c.HTTP.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("rates API: status %d", resp.StatusCode)
	}
	var body struct {
		Rate float64 `json:"rate"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&body); err != nil {
		return 0, err
	}
	return body.Rate, nil
}
```

```go
// rates_test.go
package rates

import (
	"context"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestRate(t *testing.T) {
	var gotQuery string
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		gotQuery = r.URL.RawQuery // spy on the request
		w.Header().Set("Content-Type", "application/json")
		w.Write([]byte(`{"rate": 0.92}`)) // stub the response
	}))
	defer srv.Close()

	c := &Client{BaseURL: srv.URL, HTTP: srv.Client()}
	got, err := c.Rate(context.Background(), "USD", "EUR")
	if err != nil {
		t.Fatalf("Rate() error = %v", err)
	}
	if got != 0.92 {
		t.Errorf("Rate() = %v, want 0.92", got)
	}
	if gotQuery != "from=USD&to=EUR" {
		t.Errorf("query = %q, want %q", gotQuery, "from=USD&to=EUR")
	}
}

func TestRateServerError(t *testing.T) {
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		http.Error(w, "boom", http.StatusServiceUnavailable)
	}))
	defer srv.Close()

	c := &Client{BaseURL: srv.URL, HTTP: srv.Client()}
	if _, err := c.Rate(context.Background(), "USD", "EUR"); err == nil {
		t.Fatal("Rate() error = nil, want an error on 503")
	}
}
```

(Run with Go 1.24: `go vet` clean, `go test` passes.)

| Go tool | Kind | Notes |
|---|---|---|
| Hand-written fake/spy | Any | Usually the clearest; small interfaces make them cheap |
| `go.uber.org/mock` (gomock) | Strict mock | Generated with `mockgen`; the original `golang/mock` was archived in 2023 and Uber maintains the fork |
| `mockery` + `testify/mock` | Mock | Generated from interfaces; popular with testify users |
| `counterfeiter` | Spy/stub | Generated fakes that record calls |
| `httptest` | Stub server | Standard library; real HTTP on localhost |

Python equivalents for HTTP: `respx` (for `httpx`), `responses` (for `requests`),
`pytest-httpserver` (a real local server), and VCR.py (record real responses once, replay them).
Record/replay is convenient but the cassettes go stale silently; pair it with contract tests
([Microservices: Contract Testing](05_contract_testing.md)) or periodic re-recording.

## 5. Classicist vs mockist, and how over-mocking fails

| | Classicist ("Detroit", Kent Beck) | Mockist ("London", Freeman & Pryce, *GOOS*) |
|---|---|---|
| Unit | A unit of behaviour, possibly several classes | One class |
| Collaborators | Real when fast and deterministic; fakes otherwise | Mocks for every collaborator |
| Verifies | State and outputs | Interactions |
| Strength | Tests survive refactoring; catch integration bugs between classes | Drives interface design outside-in; pinpoints which class broke |
| Weakness | A bug in one class may fail many tests | Tests coupled to implementation; refactors break them |

Over-mocking shows up as:

- **Tests that restate the code.** Every line of the method has a matching
  `assert_called_with`. Rename a private helper or batch two calls into one and ten tests fail,
  though users see no change.
- **Green tests, broken product.** Every collaborator is mocked, so nothing ever checks that
  the pieces actually fit. The mock returns `{"emailAddress": ...}`; the real service returns
  `{"email_address": ...}`.
- **Mocking value objects or data structures.** Just build the real `Money` or `datetime`.

Rules of thumb that hold up:

1. **Don't mock what you don't own** (Freeman & Pryce). Wrap a third-party SDK (Stripe,
   boto3) in a thin adapter that *you* own and whose interface speaks your domain
   (`PaymentGateway.charge(order)`), double the adapter in unit tests, and test the adapter
   itself against the real API or its sandbox in an integration test.
2. **Prefer fakes for stateful dependencies, stubs for queries, spies only for side effects
   that are the point.**
3. **Mock at the boundary of your system**, not between your own classes.
4. **Never mock your own database in an integration test.** Use a real one
   ([Integration and End-to-End (E2E) Testing](03_integration_and_e2e.md)).

## 6. Time, randomness and other hidden inputs

The hidden dependency behind most flaky tests is the **clock**: `datetime.now()`,
`time.time()`, `time.Now()` called deep inside the code. Treat time like any other dependency.

| Approach | How | Trade-off |
|---|---|---|
| **Inject a clock** | `clock: Callable[[], datetime]` parameter (as in `SignupService`), or a `Clock` interface in Go | Explicit and simplest to reason about; requires the seam |
| **Freeze time globally** | `time-machine` or `freezegun` in Python: `@time_machine.travel("2026-03-01 12:00Z")` | No code change; patches the time functions globally, which can surprise libraries |
| **Deterministic scheduler** | Go 1.25 `testing/synctest`: code inside `synctest.Test` runs in a bubble with a fake clock that advances only when every goroutine is blocked | Tests timeouts and tickers instantly and deterministically |
| **Seeded randomness** | Inject `random.Random(seed)` / Go `rand.New(rand.NewPCG(s1, s2))` (`math/rand/v2`) | Log the seed so a failure can be replayed |

The same applies to UUIDs, environment variables (`monkeypatch.setenv`, `t.Setenv`), the
file system (`tmp_path`, `t.TempDir`, `fstest.MapFS`), and the network.

## Common interview questions

**Mock vs stub vs fake?**
A stub returns canned answers so the code can proceed; you assert on the code's output. A
mock (or spy) records or expects calls; you assert on the interactions. A fake is a working
lightweight implementation, such as an in-memory repository; you assert on output and state.

**When is verifying interactions correct?**
When the call is the behaviour and has no other observable result: an email sent, a payment
charged once, an event published, a cache invalidated. Otherwise check state, because
interaction checks couple tests to implementation.

**Why did my `patch` not take effect?**
You patched where the object is defined, but the code under test had already imported the name
into its own module (`from x import f`). Patch `code_under_test_module.f`, or change the code to
receive the dependency as a parameter.

**What is the danger of a bare `Mock()`?**
It accepts any attribute and call, so tests keep passing after the real interface changes.
Use `spec`/`autospec`/`create_autospec` so wrong names and signatures raise.

**How do you stop a fake drifting from the real implementation?**
A shared contract test suite run against both: the fake in unit runs, the real one in the
integration stage. Ideally the team that owns the real service ships and maintains the fake.

**What does "don't mock what you don't own" mean?**
Don't mock a third-party SDK's API directly; you'll encode your assumptions about it. Wrap it in
an adapter with your own domain interface, double the adapter in unit tests, and verify the
adapter against the real API in integration tests.

**How do you test code that depends on the current time?**
Inject a clock (a callable or interface) and pass a fixed or controllable one in tests, or use
`time-machine`/`freezegun`. In Go, a `Clock` interface or `testing/synctest` for timers and
timeouts.

**Classicist vs mockist?**
Classicists use real collaborators where cheap and verify state; tests survive refactoring.
Mockists mock every collaborator and verify interactions; they get precise failure location and
outside-in design at the cost of brittleness. Most teams mix them, leaning classicist.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — (intern) | Why tests don't call the real database or payment API; can use `Mock()` with `return_value` |
| Junior (L3) | Software Engineer I | L3 | Names the five doubles; uses `patch` correctly (where looked up), `side_effect` for errors, `autospec`; writes a hand-written fake |
| Mid (L4) | Software Engineer II | L4 | Designs code with seams (injected dependencies, clock); prefers state over interaction checks; spots over-mocked tests; uses `httptest`/`respx` |
| Senior (L5) | Senior Software Engineer | L5 | Sets the team's doubles strategy: adapters around third parties, contract suites keeping fakes honest, deterministic time and randomness; reviews tests for brittleness |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7 | Makes owning teams ship official fakes/emulators for their services; standardises testability patterns across an org; weighs the cost of drift against the cost of real dependencies in CI |

## Interview checklist

- [ ] I can define dummy, stub, spy, mock and fake, with an example of each.
- [ ] I can explain state verification vs behaviour verification and when each is right.
- [ ] I can explain "patch where it is looked up" with a `from x import y` example.
- [ ] I can explain why `autospec` / `create_autospec` matters.
- [ ] I can write a fake and a contract suite that runs against both the fake and the real implementation.
- [ ] I can test a Go HTTP client with `httptest.NewServer`.
- [ ] I can explain "don't mock what you don't own" and the adapter pattern.
- [ ] I can make time-dependent code deterministic (injected clock, `time-machine`, `testing/synctest`).
- [ ] I can recognise over-mocking and explain what it costs.

Related: [The Testing Pyramid and Unit Tests](01_testing_pyramid.md), [Integration and End-to-End (E2E) Testing](03_integration_and_e2e.md) (real dependencies),
[Microservices: Contract Testing](05_contract_testing.md) (keeping doubles of other services honest),
[Testability, Refactoring, and Legacy Code](../SoftwareDesign/05_testability_refactoring_and_legacy_code.md) (seams),
`PyEngineering/20_table_driven_tests_fakes/`, `GoEngineering/20_table_driven_tests_fakes/`.
