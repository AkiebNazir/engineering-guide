# The Testing Pyramid and Unit Tests

A test suite is how a team changes code on a Tuesday afternoon without holding its breath.
This chapter starts from what an automated test is and why teams write them, then builds
the **testing pyramid** (many small fast tests, few big slow ones), how to write a good
unit test in pytest and Go, TDD, coverage, and the thing that quietly kills most test
suites: **flakiness**. It ends with what interviewers at each level expect you to say
about all of it.

## Foundations — What is a test, and why does anyone write them?

### The problem tests solve

Every change to a program can break something that used to work. You can check by hand:
start the app, click around, try a few inputs. That works for a weekend project. It stops
working when the code has 200,000 lines, ten people change it every day, and the thing you
broke is a corner of the billing code you never looked at.

An **automated test** is a small program that runs a piece of your real program with a
known input and checks that the output is what you expect. If the check fails, the test
fails, and the person who made the change finds out in seconds instead of from a customer
in a week. A **test suite** is all of those tests together, and a **test runner** (pytest
for Python, `go test` for Go, JUnit for Java, Jest or Vitest for JavaScript) is the tool that
finds them, runs them, and reports which ones failed.

Tests give you three things:

1. **Regression protection.** Once a bug is fixed and a test pins it, the bug cannot come
   back without a red test.
2. **Freedom to refactor.** You can restructure code aggressively because the tests tell
   you whether behaviour changed.
3. **Executable documentation.** A test named `test_vip_gets_twenty_percent_off` says what
   the code is supposed to do, and unlike a wiki page, it fails when it goes out of date.

### The pieces

| Term | Meaning |
|---|---|
| **System under test (SUT)** | The function, class, or service the test exercises |
| **Assertion** | A check (`assert x == 3`) that fails the test when false |
| **Fixture** | Setup the test needs: an object, a temp directory, a database row. In pytest, also the mechanism that provides it |
| **Test double** | A stand-in for a real dependency (a fake database, a stubbed HTTP client). See [Test Doubles: Mocks, Stubs, and Fakes](02_test_doubles.md) |
| **Test runner** | Finds tests, runs them, reports results (pytest, `go test`, JUnit) |
| **Flaky test** | A test that passes and fails on the same code. §6 |
| **Coverage** | Which lines or branches the tests executed. §7 |
| **CI** | Continuous integration: a server runs the suite on every push or pull request. See [Continuous Integration (CI) Fundamentals](../CICD/01_ci_fundamentals.md) |

### An everyday example

A shop gives VIP customers 20% off carts of 50.00 or more. The whole story of a unit
test fits in a few lines:

```python
# pricing.py
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class User:
    is_vip: bool = False


@dataclass(frozen=True)
class Cart:
    total: Decimal


def calculate_discount(cart: Cart, user: User) -> Decimal:
    """VIPs get 20% off carts of 50.00 or more; nobody gets a negative total."""
    if cart.total < 0:
        raise ValueError("cart total cannot be negative")
    if user.is_vip and cart.total >= Decimal("50.00"):
        return (cart.total * Decimal("0.20")).quantize(Decimal("0.01"))
    return Decimal("0.00")
```

```python
# test_pricing.py
from decimal import Decimal

from pricing import Cart, User, calculate_discount


def test_vip_gets_twenty_percent_off():
    # Arrange
    cart = Cart(total=Decimal("100.00"))
    user = User(is_vip=True)

    # Act
    discount = calculate_discount(cart, user)

    # Assert
    assert discount == Decimal("20.00")
```

Run `pytest` in that directory. pytest finds files named `test_*.py`, runs every function
named `test_*`, and prints a dot per pass or a detailed diff per failure. Money uses
`Decimal`, not `float`, because `0.1 + 0.2 != 0.3` in binary floating point, and a test
comparing float prices would be fragile for reasons unrelated to your logic.

### How a test run fits together

```arch
%% caption: A pytest run: collect the tests, build each test's fixtures, run it, tear the fixtures down, report.
route straight
grid 170x110
group run "pytest process" color=blue icon=process
node collect "Collect" at 0,0 in run shape=card icon=search sub="test_*.py, test_*()"
node setup "Fixture setup" at 1,0 in run shape=card icon=layers sub="tmp_path, db, client"
node call "Run test body" at 2,0 in run shape=card icon=code sub="arrange, act, assert"
node teardown "Teardown" at 2,1 in run shape=card icon=delete sub="code after yield"
node report "Report" at 1,1 in run shape=card icon=check sub="pass, fail, skip"
node ci "CI status" at 1,2 shape=pill color=green
collect -> setup -> call
call -> teardown
teardown -> report
report -> ci : "exit code"
```

The exit code is what CI cares about: 0 means every test passed, anything else fails the
build. Everything else in this chapter is about making that signal **fast**, **trustworthy**
and **meaningful**.

## 1. The testing pyramid

The pyramid (popularised by Mike Cohn around 2009) says: write **many** fast, cheap,
narrow tests at the bottom, **fewer** integration tests in the middle, and **very few**
slow, broad end-to-end tests at the top.

```arch
%% caption: The classic testing pyramid balances speed, cost, and confidence: many unit tests, fewer integration tests, a handful of E2E tests.
route straight
grid 190x100
node e2e "E2E tests (UI)" at 1,0 shape=card icon=browser color=red sub="few · minutes each"
node it "Integration tests" at 1,1 shape=card icon=network color=amber sub="some · DB, API · seconds"
node unit "Unit tests" at 1,2 shape=card icon=code color=green sub="many · milliseconds"
node up "going up: fewer tests, more confidence each, slower" at 2,1 shape=text
unit -> it
it -> e2e
```

Why that shape: as a test gets broader it gets slower, flakier, and harder to debug, while
each test covers more real wiring. You want the fast feedback of the bottom and a thin layer
of the realism of the top.

| Layer | Scope | Typical speed | What a failure tells you | Main risk |
|---|---|---|---|---|
| Unit | One function or class, dependencies replaced | ≈ 1 ms or less | Exactly which rule broke | Passes while the wiring between units is broken |
| Integration | Your code plus one real dependency (DB, broker, HTTP) | ≈ 10 ms – seconds | This component cannot talk to that one | Slower; needs containers or services |
| End-to-end | The deployed system through its UI or public API | Seconds – minutes | Something, somewhere, is broken | Flaky, slow, hard to localise |

### Google's version: test **sizes**, not names

"Unit" and "integration" mean different things on different teams. Google classifies tests by
the **resources** they may use (described in *Software Engineering at Google*, ch. 11), and
the test infrastructure enforces the limits:

| Size | Allowed | Default timeout (Bazel) |
|---|---|---|
| **Small** | One process, ideally one thread. No sleep, no disk, no network | 60 s |
| **Medium** | One machine. May use localhost network, disk, multiple processes (e.g. a local DB) | 300 s |
| **Large** | Multiple machines, real network, remote services | 900 s |

Size (resources) and **scope** (how much code is exercised) are separate axes: a small test
can have wide scope if everything runs in one process. The size is what predicts speed and
flakiness. Google's 2015 testing-blog post "Just Say No to More End-to-End Tests" suggested
a starting split of roughly **70% unit, 20% integration, 10% E2E**; treat that as a
starting point, not a law.

### Other shapes, and when they are right

| Shape | Proposed by | Claim | Fits |
|---|---|---|---|
| Pyramid | Mike Cohn | Most tests are unit tests | Logic-heavy code: libraries, domain models, algorithms |
| Trophy | Kent C. Dodds (2018) | Static analysis at the base; most tests are **integration** | Front-end apps, where units are thin and the risk is in composition |
| Honeycomb | Spotify (2018) | Most tests are integration tests of each microservice through its API | Small microservices whose logic is mostly "call other things" |
| Ice-cream cone | (anti-pattern) | Most testing is manual or E2E | Nobody; it is slow, flaky, and expensive |

The shapes agree on the thing that matters: **put each check at the lowest level that can
catch the bug.** An off-by-one in a discount rule is a unit test. "The ORM mapping for the
new column is wrong" is an integration test. "Checkout works in a real browser" is one E2E test.

## 2. Writing a good unit test

### What "unit" means

Two schools disagree (see [Test Doubles: Mocks, Stubs, and Fakes](02_test_doubles.md) §5):

- **Classicist ("Detroit")**: a unit is a *unit of behaviour*. Use real collaborators when they
  are fast and deterministic; replace only slow or non-deterministic ones (network, disk,
  clock, randomness).
- **Mockist ("London")**: a unit is one class. Replace every collaborator with a mock.

Most experienced teams lean classicist because the tests survive refactoring. The shared
rule: a unit test does no real I/O, runs in milliseconds, and gives the same answer every time.

### Arrange, Act, Assert

Every test has three parts. Keep them visually separate, keep **one Act** per test, and make
the Assert check the **observable outcome** (return value, state change, message sent), not
the steps taken.

### Properties of a good test (the "FIRST" rule and friends)

| Property | Meaning | Violation looks like |
|---|---|---|
| **Fast** | Milliseconds | `time.sleep(2)` "to let things settle" |
| **Isolated** | No shared state between tests; any order works | Test B passes only after test A ran |
| **Repeatable** | Same result every run, every machine | Depends on today's date or the network |
| **Self-validating** | Pass/fail without a human reading output | Prints results "to check" |
| **Timely / behavioural** | Written with (or before) the code; tests behaviour | Asserts private fields or call order |
| **Readable** | The name says the rule; a failure says what broke | `test_1`, `assert result` |

**Name tests after behaviour**: `test_expired_coupon_is_rejected`, not `test_apply_coupon_2`.
When it fails in CI, the name alone should tell a reader what regressed.

### What not to test

- **Private methods.** Test the public API of the class. Tests coupled to internals break
  on every refactor even though behaviour is unchanged (brittle tests). If a private helper
  is complex enough to want its own tests, it probably wants to be its own public unit.
- **The framework or the language.** Don't test that `dict` stores keys or that Django
  saves a model.
- **Trivial code** (getters, pure data classes) unless it carries logic.
- **Implementation steps.** "Called `repo.save` exactly once with these args" is sometimes
  necessary (the side effect *is* the behaviour, e.g. sending an email), but often it just
  re-states the code.

### Test the edges

Most bugs live at boundaries. For each input, test: empty, one, many; zero, negative,
maximum; exactly on each threshold and one either side; invalid types; unicode;
duplicates; and the error path. Property-based testing ([Advanced: Property-Based and Mutation Testing](04_property_and_mutation.md))
automates the search for edges you did not think of.

## 3. pytest in depth

pytest is the de facto Python test runner (current major version 9 as of 2026). It uses
plain `assert` and rewrites it at import time so a failure shows both sides of the
comparison.

### Parametrize: one rule, many cases

```python
import pytest
from decimal import Decimal

from pricing import Cart, User, calculate_discount


@pytest.mark.parametrize(
    ("total", "is_vip", "expected"),
    [
        ("49.99", True, "0.00"),    # just below the threshold
        ("50.00", True, "10.00"),   # exactly on the threshold
        ("100.00", False, "0.00"),  # regular customers get nothing
        ("0.00", True, "0.00"),     # empty cart
    ],
    ids=["below-threshold", "on-threshold", "not-vip", "empty-cart"],
)
def test_discount_table(total, is_vip, expected):
    cart = Cart(total=Decimal(total))
    assert calculate_discount(cart, User(is_vip=is_vip)) == Decimal(expected)


def test_negative_total_is_rejected():
    with pytest.raises(ValueError, match="cannot be negative"):
        calculate_discount(Cart(total=Decimal("-1")), User(is_vip=True))
```

Each tuple becomes its own test (`test_discount_table[on-threshold]`), reported and
re-runnable on its own. `pytest.raises(..., match=...)` checks both the exception type and
its message (`match` is a regex searched in `str(exc)`).

### Fixtures: setup that composes

A fixture is a function decorated with `@pytest.fixture`. A test asks for it by naming it as
a parameter. Code before `yield` is setup, code after is teardown, and teardown runs even if
the test fails. Put shared fixtures in `conftest.py`, which pytest loads automatically for
that directory and below.

```python
# conftest.py
import json

import pytest


@pytest.fixture
def price_file(tmp_path):
    """A throwaway JSON file; tmp_path is a fresh directory per test."""
    path = tmp_path / "prices.json"
    path.write_text(json.dumps({"apple": "0.50", "pear": "0.75"}))
    yield path            # the test runs here
    # teardown code after `yield` runs even if the test failed
```

```python
# test_fixtures.py
import json
import os


def load_prices(path):
    return json.loads(path.read_text())


def test_reads_prices(price_file):
    assert load_prices(price_file)["pear"] == "0.75"


def currency():
    return os.environ.get("SHOP_CURRENCY", "USD")


def test_currency_from_env(monkeypatch):
    monkeypatch.setenv("SHOP_CURRENCY", "EUR")   # undone automatically after the test
    assert currency() == "EUR"
```

(All snippets in this section were run with pytest 9.1: 8 passed.)

| Fixture feature | What it does |
|---|---|
| `scope="function"` (default) | New instance per test: maximum isolation |
| `scope="module"` / `"package"` / `"session"` | Shared across tests: use for expensive, **read-only** or reset-between-tests resources (a DB container) |
| `autouse=True` | Applied to every test in scope without being named. Use sparingly; it hides setup |
| `params=[...]` | Run every dependent test once per parameter |
| Built-ins | `tmp_path`, `monkeypatch`, `capsys`/`capfd` (captured output), `caplog` (log records), `request` |

A session-scoped fixture that tests **mutate** is the classic way to make tests depend on
each other. Share the expensive thing (the database server), not the state inside it (roll
back a transaction per test; see [Integration and End-to-End (E2E) Testing](03_integration_and_e2e.md) §3).

### Everyday command line

```bash
pytest -q                          # quiet summary
pytest tests/test_pricing.py::test_discount_table -v   # one test, verbose
pytest -k "discount and not vip"   # select by name expression
pytest -m "not slow"               # select by marker (register markers in pyproject.toml)
pytest -x --lf                     # stop at first failure; rerun last failures first
pytest -n auto                     # parallel across CPUs (pytest-xdist plugin)
pytest -p no:randomly              # pytest-randomly shuffles order once installed; this turns it off
pytest --cov=shop --cov-branch     # coverage with branch data (pytest-cov plugin)
```

Other tools worth knowing: `pytest.approx` for floats, `@pytest.mark.skipif(...)`,
`@pytest.mark.xfail(strict=True)` for a known bug (strict makes an unexpected pass fail, so
the marker cannot outlive the bug), and `--durations=10` to find slow tests.

## 4. Unit tests in Go

Go ships its test runner. Files ending `_test.go` are compiled only by `go test`; functions
`TestXxx(t *testing.T)` are tests. The idiom is the **table-driven test** with subtests:

```go
// pricing.go
package pricing

import "errors"

var ErrNegativeTotal = errors.New("cart total cannot be negative")

// Discount returns the discount in cents: VIPs get 20% off carts of 5000 cents or more.
func Discount(totalCents int64, vip bool) (int64, error) {
	if totalCents < 0 {
		return 0, ErrNegativeTotal
	}
	if vip && totalCents >= 5000 {
		return totalCents * 20 / 100, nil
	}
	return 0, nil
}
```

```go
// pricing_test.go
package pricing

import (
	"errors"
	"testing"
)

func TestDiscount(t *testing.T) {
	tests := []struct {
		name    string
		total   int64
		vip     bool
		want    int64
		wantErr error
	}{
		{name: "below threshold", total: 4999, vip: true, want: 0},
		{name: "on threshold", total: 5000, vip: true, want: 1000},
		{name: "not vip", total: 10000, vip: false, want: 0},
		{name: "negative total", total: -1, vip: true, wantErr: ErrNegativeTotal},
	}
	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			t.Parallel() // Go 1.22+: each iteration has its own tc, so this is safe
			got, err := Discount(tc.total, tc.vip)
			if !errors.Is(err, tc.wantErr) {
				t.Fatalf("Discount(%d, %v) error = %v, want %v", tc.total, tc.vip, err, tc.wantErr)
			}
			if got != tc.want {
				t.Errorf("Discount(%d, %v) = %d, want %d", tc.total, tc.vip, got, tc.want)
			}
		})
	}
}
```

(Run with Go 1.24: `go test -race -count=1 -v ./...` passes.)

Go-specific points interviewers probe:

- `t.Errorf` records a failure and continues; `t.Fatalf` stops this test (it calls
  `runtime.Goexit`, so call it only from the test's own goroutine).
- Before Go 1.22 the loop variable was shared across iterations, so `t.Parallel()` subtests
  all saw the last `tc` unless you wrote `tc := tc`. Go 1.22 made loop variables
  per-iteration.
- Failure messages follow the convention `Func(args) = got, want want`.
- Helpers: `t.Helper()` (report the caller's line), `t.Cleanup(fn)`, `t.TempDir()`,
  `t.Setenv()` (not allowed in parallel tests), `t.Context()` (Go 1.24).
- Flags: `-race` (data-race detector), `-count=1` (bypass the test cache), `-shuffle=on`
  (random order), `-run 'TestDiscount/on_threshold'`, `-short` with `testing.Short()` to skip
  slow tests, `-cover` / `-coverprofile=c.out` then `go tool cover -html=c.out`.
- Standard library doubles: `net/http/httptest` (a real HTTP server on localhost, or a
  `ResponseRecorder`), `testing/fstest.MapFS` (an in-memory file system),
  `testing/iotest` (misbehaving readers). Go also has native fuzzing
  ([Advanced: Property-Based and Mutation Testing](04_property_and_mutation.md) §4).

More practice: `content/languages/GoEngineering/20_table_driven_tests_fakes/` and
`content/languages/PyEngineering/20_table_driven_tests_fakes/`.

## 5. Test-driven development (TDD)

TDD is a design process that happens to leave tests behind. The loop, from Kent Beck:

```arch
%% caption: Red, green, refactor: each lap adds one small behaviour and leaves a test that pins it.
route straight
grid 170x110
node red "Red" at 0,0 shape=card icon=error color=red sub="write a failing test"
node green "Green" at 2,0 shape=card icon=check color=green sub="simplest code to pass"
node refactor "Refactor" at 1,1 shape=card icon=edit color=blue sub="clean up, tests stay green"
red -> green : "make it pass"
green -> refactor : "tidy"
refactor -> red : "next behaviour"
```

1. **Red**: write a test for the next small behaviour. Run it and **watch it fail** for the
   right reason. A test you never saw fail may not be testing anything.
2. **Green**: write the minimum code to pass, even if it is ugly or hard-coded.
3. **Refactor**: remove duplication and improve names with the test as a safety net.

Why it helps: writing the test first makes you use the API before it exists, so awkward
APIs and hidden dependencies (a function that secretly reads the clock) show up
immediately. Highly coupled code is painful to test, and TDD makes you feel that pain
while it is cheap to fix.

Where it fits less well: exploratory spikes (you don't know the shape yet: spike, throw it
away, then TDD the real thing), UI layout, and code whose correctness is statistical (ML
models). Evidence on TDD's productivity effect is mixed across studies; the consistent
benefit is a design with seams and a suite you trust. A pragmatic middle ground many teams
use: for every **bug**, write the failing test that reproduces it first, then fix it.

## 6. Flaky tests

A **flaky test** passes and fails on the same code. It is the most corrosive problem in a
test suite: once people learn that red sometimes means nothing, they re-run until green and
stop reading failures, and real regressions ride through.

Google reported in 2016 that about **1.5%** of all test runs gave a flaky result and that
roughly **16%** of its tests had shown some flakiness (John Micco, "Flaky Tests at Google and
How We Mitigate Them"). Larger tests are much flakier than small ones.

| Cause | Symptom | Fix |
|---|---|---|
| **Time** | Fails at midnight, at month end, on DST change, on a slow CI box | Inject a clock; freeze time in tests ([Test Doubles: Mocks, Stubs, and Fakes](02_test_doubles.md) §6) |
| **Sleeps / races** | `sleep(1)` "usually enough" | Wait for a **condition** with a timeout (poll, event, channel), never a fixed sleep |
| **Order dependence** | Passes alone, fails in the suite (or the reverse) | Fresh state per test; run with random order (`pytest-randomly`, `go test -shuffle=on`) |
| **Shared resources** | Fails under `-n auto` or parallel CI shards | Unique names per test (tmp dirs, DB schemas, ports `:0`) |
| **Randomness** | Fails 1 run in 500 | Seed and log the seed; or make the property hold for all seeds |
| **Unordered collections** | Comparing set/dict iteration order, Go map order | Sort before comparing, or compare as sets |
| **Network / external services** | Fails when a third-party sandbox is slow | Replace with a fake at unit level; contract tests ([Microservices: Contract Testing](05_contract_testing.md)) |
| **Resource leaks** | Later tests fail after an earlier one leaks threads/files | Teardown in fixtures / `t.Cleanup`; leak detectors (`goleak`) |
| **Floating point** | Last-digit differences across platforms | `pytest.approx`, tolerance comparisons |

A flaky-test process that works:

1. **Detect**: rerun failures automatically in CI and record "failed then passed" as flaky
   (not green). Track a per-test flake rate.
2. **Quarantine**: move a known-flaky test out of the blocking suite *with an owner and a
   ticket*, so it stops blocking merges but is not forgotten.
3. **Fix the root cause**, then bring it back. Blind retries (`@flaky(max_runs=3)`) hide
   real concurrency bugs in the product, not only in the test.

## 7. Code coverage: what it measures and what it doesn't

Coverage tools record which code ran during the tests.

| Kind | Measures | Example gap |
|---|---|---|
| **Line / statement** | Each line executed at least once | `if a and b:` fully "covered" with only `a=True, b=True` |
| **Branch** | Each side of each decision taken | Doesn't require every *combination* of conditions |
| **Condition / MC/DC** | Each boolean sub-condition shown to affect the outcome | Required for the most critical avionics software (DO-178C Level A) |
| **Mutation score** | Fraction of injected bugs the tests catch | Expensive; see [Advanced: Property-Based and Mutation Testing](04_property_and_mutation.md) |

The key limit: **coverage shows what was executed, not what was checked.** A test that
calls every function and asserts nothing reaches 100% line coverage. So:

- Low coverage is a reliable signal: that code is definitely untested.
- High coverage is a weak signal: the code ran, and you still don't know whether a bug
  there would fail a test.

Practical targets: many teams set a floor around 70–80% for **new or changed lines** (diff
coverage) rather than a global number, because a global threshold invites tests that
execute code without asserting. Google's published guidance calls ≈60% "acceptable",
≈75% "commendable" and ≈90% "exemplary", while stressing that the number is not the goal.

```bash
pytest --cov=shop --cov-branch --cov-report=term-missing   # Python, shows missed lines
go test -coverprofile=c.out ./... && go tool cover -func=c.out   # Go, per-function
```

## 8. Keeping a large suite fast and trusted

| Problem at scale | Technique |
|---|---|
| Suite takes 40 minutes | Parallelise (`pytest -n auto`, `go test` runs packages in parallel by default, CI sharding); find slow tests with `--durations`; push checks down the pyramid |
| Every change runs every test | **Test selection**: run only tests affected by the change, from the build graph (Bazel, Pants, Nx, Gradle). Google's TAP does this across its monorepo |
| Same tests rerun on unchanged code | Cache results by input hash (Bazel remote cache; `go test` caches passing packages) |
| Pre-merge vs post-merge | Fast small tests block the merge; slower large tests run after merge or on a schedule, with automatic culprit finding and rollback |
| Tests that nobody owns | Every test has an owning team; quarantined tests have tickets |

Heuristic budgets many teams aim for (≈, adjust to taste): a unit test in under 10 ms, the
pre-merge suite under 10 minutes, and a developer's local inner loop (`pytest -x path/`)
in seconds. See [Continuous Integration (CI) Fundamentals](../CICD/01_ci_fundamentals.md) for where these stages sit in a pipeline.

## Common interview questions

**What is the testing pyramid and why that shape?**
Many fast unit tests, fewer integration tests, very few E2E tests. Broad tests are slower,
flakier, and harder to debug but catch wiring bugs; narrow tests are fast and precise but
miss wiring. The shape buys fast feedback with a thin layer of realism. The real rule is to
test each behaviour at the lowest level that can catch its bug.

**What makes a good unit test?**
Fast, isolated, deterministic, self-checking, named after the behaviour, one Act, asserting
observable outcomes through the public API. It should fail only when behaviour breaks, and
its failure message should say what broke.

**Should you test private methods?**
No. Test through the public API. Tests on internals break on every refactor without catching
real regressions. If a private method needs its own tests, extract it into its own unit.

**100% coverage: good goal?**
No. Coverage shows execution, not verification. Low coverage reliably flags untested code;
high coverage doesn't prove the tests would catch bugs. Use a diff-coverage floor to catch
untested new code, and mutation testing on critical modules to measure test strength.

**What causes flaky tests and how do you handle them?**
Time, sleeps and races, shared state and order dependence, unseeded randomness, unordered
collections, real network. Detect by recording pass-on-retry as flaky, quarantine with an
owner, fix the root cause. Blind retries hide real concurrency bugs.

**What is TDD, and when would you not use it?**
Red, green, refactor in small steps; the test comes first so the design is shaped by use.
Less useful for exploratory spikes and statistical code. A good compromise: always write the
failing reproduction test before fixing a bug.

**How does Google classify tests?**
By size: small (single process, no I/O), medium (single machine, localhost), large
(multiple machines). Size predicts speed and flakiness better than the words unit or
integration. Scope, how much code is exercised, is a separate axis.

**Pyramid vs trophy vs honeycomb?**
Same principle, different code. Logic-heavy code wants mostly unit tests; UI apps and thin
microservices carry their risk in composition, so integration tests give more confidence per
test. The ice-cream cone (mostly manual/E2E) is the anti-pattern.

**Your CI takes 45 minutes. What do you do?**
Measure first (`--durations`). Parallelise and shard; cache by input hash; select tests
affected by the change from the build graph; move slow checks post-merge with automatic
culprit finding; replace E2E checks with lower-level tests where possible.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — (intern) | Writes pytest / `go test` tests with plain asserts; runs them; knows a test must fail when the code is wrong |
| Junior (L3) | Software Engineer I | L3 | AAA, parametrize / table-driven tests, fixtures, `tmp_path`/`t.TempDir`; tests edge cases; never ships a change without a test |
| Mid (L4) | Software Engineer II | L4 | Chooses the right pyramid layer; spots and fixes flaky tests (time, order, sleeps); understands coverage limits; practises TDD for bug fixes |
| Senior (L5) | Senior Software Engineer | L5 | Designs code for testability (seams, injected clock); sets test strategy for a service; defines what blocks merge vs runs post-merge; drives flake rate down |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7 | Owns test infrastructure and policy across many teams: test sizes, selection from the build graph, quarantine process, diff-coverage and mutation gates, the cost/confidence budget of the whole suite |

## Interview checklist

- [ ] I can draw the pyramid and explain why broad tests are slower, flakier, and harder to debug.
- [ ] I can explain Google's small/medium/large test sizes and why size is not scope.
- [ ] I can write a parametrized pytest test with a fixture, `tmp_path`, `monkeypatch` and `pytest.raises`.
- [ ] I can write a Go table-driven test with `t.Run`, `t.Parallel` and explain the pre-1.22 loop-variable bug.
- [ ] I can list five causes of flaky tests and the fix for each.
- [ ] I can explain why 100% coverage doesn't mean the code is tested, and name a better measure.
- [ ] I can describe red-green-refactor and when TDD is a poor fit.
- [ ] I can explain the trophy and honeycomb and when they beat the pyramid.
- [ ] I can propose concrete steps to make a slow CI suite fast.

Related: [Test Doubles: Mocks, Stubs, and Fakes](02_test_doubles.md) (replacing dependencies), [Integration and End-to-End (E2E) Testing](03_integration_and_e2e.md),
[Advanced: Property-Based and Mutation Testing](04_property_and_mutation.md), [Continuous Integration (CI) Fundamentals](../CICD/01_ci_fundamentals.md),
[Testability, Refactoring, and Legacy Code](../../interview-core/SoftwareDesign/05_testability_refactoring_and_legacy_code.md),
`content/languages/PyEngineering/20_table_driven_tests_fakes/`, `content/languages/GoEngineering/20_table_driven_tests_fakes/`.
