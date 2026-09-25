# Error Handling and Failure Design in Code

> "Errors should never pass silently. Unless explicitly silenced." — The Zen of Python
>
> "Don't just check errors, handle them gracefully." — Go Proverbs

Most code is written for the path where everything works. Most production incidents
happen on the other paths: the timeout nobody set, the retry that double-charged, the
`except Exception: pass` that hid a bug for six months, the cleanup that raised and
buried the real error.

Failure handling is **design**, not a detail added after the happy path. This file is
about deciding, in code, **what can fail, who handles it, and what state the system is
left in when it does.**

Examples are in **Python** with **Go** where the idioms differ (§12). Every example was
run; outputs shown are real.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| Designing error *contracts* for an <abbr title="Application Programming Interface">API</abbr> (categories, `%w` as <abbr title="Application Programming Interface">API</abbr>) | `03_modularity_coupling_and_api_design.md` §8 |
| Defining errors out of existence | `01_philosophy_of_software_design.md` §7 |
| Circuit breakers, bulkheads, retry storms, backpressure (system scale) | `SystemDesign/building_blocks/12_application_resilience_patterns.md` |
| Sagas, outbox, 2PC across services | `CSFundamentals/04_software_engineering_deep_dive.md` §2–§3 |
| Save-pending → idempotent call → save-outcome in a use case | `08_application_architecture_in_code.md` §4.3 |
| Runnable error taxonomy / retrying <abbr title="Application Programming Interface">API</abbr> client projects | `PyEngineering/17_error_taxonomy`, `03_api_client_with_retries`, `GoEngineering/17_*`, `03_*`, `32_context_and_timeouts_deep_dive` |

---

## Contents

1. [A failure model: what can go wrong, and who handles it](#1--a-failure-model-what-can-go-wrong-and-who-handles-it)
2. [Exceptions, error values, and result types](#2--exceptions-error-values-and-result-types)
3. [Where to catch: the four legitimate reasons](#3--where-to-catch-the-four-legitimate-reasons)
4. [Error context: messages that debug themselves](#4--error-context-messages-that-debug-themselves)
5. [Cleanup: resources, and errors during cleanup](#5--cleanup-resources-and-errors-during-cleanup)
6. [Timeouts, deadlines, and cancellation](#6--timeouts-deadlines-and-cancellation)
7. [Retries done right](#7--retries-done-right)
8. [Idempotency in code](#8--idempotency-in-code)
9. [Partial failure: step ordering and compensation](#9--partial-failure-step-ordering-and-compensation)
10. [Fail fast, crash, or degrade?](#10--fail-fast-crash-or-degrade)
11. [Validation: fail on first error or collect them all?](#11--validation-fail-on-first-error-or-collect-them-all)
12. [The same ideas in Go](#12--the-same-ideas-in-go)
13. [Testing failure paths](#13--testing-failure-paths)
14. [Red flags](#14--red-flags)
15. [Interview questions and model answers](#15--interview-questions-and-model-answers)
16. [Checklist](#16--checklist)

---

## 1 · A failure model: what can go wrong, and who handles it

Before writing a single `try`, sort failures into kinds. Each kind has a different
correct response, and mixing them up is the root of most bad error handling.

| Kind | Examples | Expected? | Correct response | Who handles it |
|---|---|---|---|---|
| **Bug** (programmer error) | `None` where an object was required, index out of range, broken invariant | No | **Crash** the operation loudly; alert; fix the code | Nobody locally; top-level boundary logs and returns 500 |
| **Invalid input** | Malformed <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>, qty = −3, unknown SKU | Yes | Reject with a precise message; never retry | The caller (user / client) |
| **Domain outcome** | Insufficient funds, seat already taken, card declined | Yes — part of the business | A normal result, often not an "error" at all | The use case / the user |
| **Transient environment** | Timeout, connection reset, 503, 429, lock wait timeout | Yes, occasionally | Retry with backoff, within a deadline, if idempotent | The adapter closest to the call — once |
| **Persistent environment** | Disk full, bad credentials, dependency down for an hour | Yes, rarely | Fail fast, degrade if possible, alert | Operators; circuit breaker |
| **Partial failure** | Step 3 of 4 failed; response lost after the server committed | Yes, in any distributed flow | Idempotency + compensation or reconciliation | The orchestrating code (§8, §9) |

Two questions settle most design arguments:

1. **Can anyone at this level do something useful about it?** If not, don't catch it.
2. **Is the state still consistent after this failure?** If not, that's the real bug —
   fix the ordering (§9), not the `except` clause.

The **domain outcome** row is the one people most often get wrong. "Seat already taken"
is not exceptional in a booking system; it happens hundreds of times a minute on a
popular show. Model it in the return type if callers must always handle it (§2).

---

## 2 · Exceptions, error values, and result types

Three mechanisms, each with a place:

| Mechanism | Languages | Strength | Weakness |
|---|---|---|---|
| **Exceptions** | Python, Java, C++ | Happy path stays clean; errors propagate automatically to whoever can handle them | Invisible in signatures — any call might raise anything |
| **Error values** | Go, C | Every failure point is visible at the call site | Verbose; easy to write `if err != nil { return err }` without adding context |
| **Result / sum types** | Rust `Result`, Haskell `Either`, Python unions | Type checker forces callers to handle each outcome | Clumsy for errors that should just propagate |

**In Python, use exceptions for failures, and return values for expected outcomes the
caller must always branch on.**

The simplest version of that split, before any framework or type is involved:

```python
# Simplest on-ramp: an exception for a genuine failure, a return value for an expected outcome.
def divide(a: int, b: int) -> float:
    if b == 0:
        raise ZeroDivisionError(f"cannot divide {a} by zero")
    return a / b

def find_user(users: dict[str, str], user_id: str) -> str | None:
    return users.get(user_id)          # absence is normal here, not a failure

try:
    divide(10, 0)
except ZeroDivisionError as e:
    print("caught:", e)

print("lookup:", find_user({"1": "Ada"}, "2"))
```

Output:

```
caught: cannot divide 10 by zero
lookup: None
```

`divide` can't do anything useful with `b=0`, so it raises and lets the caller decide.
`find_user` treats absence as a normal outcome, so it returns `None` — no `try` needed to
call it. The rest of this section is the same split applied to a case where the caller
**must** handle every outcome, enforced by the type checker instead of by convention:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Booked:
    booking_id: str

@dataclass(frozen=True)
class SeatTaken:
    alternatives: list[str]

BookingResult = Booked | SeatTaken       # expected outcomes: both are normal business results

def book(seat: str) -> BookingResult:
    ...                                   # raises only for bugs / infrastructure failures

match book("A7"):                         # pyright/mypy flag a non-exhaustive match
    case Booked(booking_id):
        confirm(booking_id)
    case SeatTaken(alternatives):
        offer(alternatives)
```

Why not `raise SeatTaken`? Because an exception is easy to forget to catch, and the
signature `book(seat) -> Booked` would lie about what happens half the time. The rule
of thumb: **if the caller's code would be wrong without handling it, put it in the
return type; if the caller normally just propagates it, raise it.**

**Avoid these hybrids:**

```python
def find_user(uid) -> User | None: ...    # OK when absence is normal and obvious
def save(user) -> bool: ...               # BAD: False means... what? Callers ignore it.
def parse(s) -> tuple[int, str]: ...      # BAD in Python: Go-style (value, error) tuples
                                          #   fight the language; nobody checks them.
```

---

## 3 · Where to catch: the four legitimate reasons

An `except` (or `if err != nil` that does more than return) is justified only when
the code at that point does one of four things:

| Reason | Example |
|---|---|
| **1. Recover** — do something that makes the operation succeed | Retry a transient error; fall back to a cache; use a default for an optional feature |
| **2. Translate** — convert to the vocabulary of this layer | `sqlite3.IntegrityError` → `DuplicateEmail` in the repository adapter |
| **3. Add context** — then re-raise | "while importing row 1,832 of users.csv" |
| **4. Boundary** — the top of a request, job, thread, or task: log once, respond, keep the process alive | <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> middleware → 500; worker loop → mark job failed, continue with the next |

```arch
%% caption: Error Handling Architecture Boundaries
group bnd "4. Boundary Layer (HTTP/Job)" color=blue style=dashed
node ctrl "HTTP Controller\n(returns 500 / logs)" at 1,0 in bnd icon=api

group domain "3. Domain / Use Case Layer" color=green style=dashed
node usecase "User Onboarding\n(adds context)" at 1,1 in domain icon=process

group adapt "2. Adapter Layer" color=amber style=dashed
node repo "SQL Repository\n(translates error)" at 1,2 in adapt icon=database

node db "Database\n(throws IntegrityError)" at 1,3 icon=db color=slate

db -> repo : "throw"
repo -> usecase : "throw\nDuplicateEmail"
usecase -> ctrl : "throw\n(with note)"
ctrl -> ctrl : "log\n& stop"
```

Everything else should let the error propagate.

```python
# 2. TRANSLATE at the adapter, keeping the cause.
class SqlUserRepository:
    def add(self, user: User) -> None:
        try:
            self._conn.execute("INSERT INTO users (id, email) VALUES (?, ?)", (user.id, user.email))
        except sqlite3.IntegrityError as e:
            if "users.email" in str(e):
                raise DuplicateEmail(user.email) from e     # `from e` keeps the traceback chain
            raise                                           # some other constraint: not ours to interpret

# 3. ADD CONTEXT, re-raise. Python 3.11+: add_note keeps the original type and traceback.
def import_rows(rows):
    for i, row in enumerate(rows, start=1):
        try:
            import_row(row)
        except Exception as e:
            e.add_note(f"while importing row {i}: {row!r}")
            raise

# 4. BOUNDARY: the only place a broad `except Exception` belongs.
def worker_loop(queue, handle, log):
    while (job := queue.get()) is not None:
        try:
            handle(job)
        except Exception:
            log.exception("job %s failed", job.id)          # logs traceback ONCE, here
            job.mark_failed()
```

### Anti-patterns

```python
# ✗ Swallow: the bug is now invisible, and the caller thinks it worked.
try:
    charge(order)
except Exception:
    pass

# ✗ Log and re-raise at every layer: one failure, five stack traces in the logs,
#   nobody knows which is the real one. Log at the boundary only.
except Exception as e:
    log.error("charge failed: %s", e)
    raise

# ✗ Too broad: catches the typo'd attribute name (AttributeError) as if it were "not found".
try:
    return cache[key].valu
except Exception:
    return None

# ✗ Bare except: also catches KeyboardInterrupt and SystemExit — Ctrl-C stops working.
try:
    ...
except:
    ...

# ✗ Error codes smuggled through exceptions: callers must string-match.
raise Exception("ERR_42: user not found")

# ✗ Lost cause: `raise X` inside `except` without `from e` still sets __context__,
#   but `raise X from None` deliberately discards it — do that only for noise, never for real causes.
```

**Keep `try` blocks small.** Put only the call that can raise the error you are
handling inside `try`; put the follow-up work in `else`. Otherwise you handle errors
from code you did not mean to protect.

```python
try:
    user = repo.get(user_id)
except NotFound:
    return None
else:
    return render(user)       # a bug in render() is NOT turned into "return None"
```

---

## 4 · Error context: messages that debug themselves

When an error reaches a log at 3 a.m., it should answer: **what operation, on what
input, failed how, and why.**

```
✗  KeyError: 'price'
✗  Error: failed
✓  price catalog: import feed "supplier-7" row 1832: missing field "price"
      (row={"sku": "A-17", "name": "Widget"})
      caused by: KeyError: 'price'
```

Rules:

1. **Each layer adds what it knows and nothing more.** The DB driver knows the <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>
   error; the repository knows the user ID; the use case knows "while registering".
   Stacked, they form a sentence (Go makes this explicit: §12).
2. **Say what was expected and what was found:** `expected ISO date, got "31/02/2026"`.
3. **Include identifiers, not payloads.** IDs and sizes, not full bodies — logs get
   copied, and bodies contain personal data.
4. **Never include secrets:** tokens, passwords, full card numbers, connection strings
   with credentials. An exception message is a log line waiting to happen.
5. **Separate the internal message from the client message.** Clients get a stable
   code and a safe message; logs get the full chain. Leaking `psycopg2.errors...` text
   to an <abbr title="Application Programming Interface">API</abbr> response reveals your stack and schema.
6. **Make errors structured when machines consume them:** a code/category field, not
   a sentence to grep.

```python
class AppError(Exception):
    code: str = "internal"
    http_status: int = 500
    public_message: str = "Something went wrong."

class DuplicateEmail(AppError):
    code, http_status = "duplicate_email", 409
    def __init__(self, email: str):
        super().__init__(f"email already registered: {email}")      # internal (for logs)
        self.public_message = "That email is already registered."    # safe for clients
```

---

## 5 · Cleanup: resources, and errors during cleanup

Every acquired resource (file, lock, connection, transaction, temp directory, span)
must be released on **every** path — success, error, and cancellation.

| Language | Mechanism |
|---|---|
| Python | `with` (context managers), `contextlib.ExitStack` for a dynamic number, `try/finally` |
| Go | `defer` immediately after successful acquisition |
| Java | try-with-resources |
| C++ / Rust | Destructors (RAII) / `Drop` |

The rule that prevents most leaks: **pair acquisition and release on adjacent lines.**

```python
lock.acquire()
try:                      # try starts IMMEDIATELY after a successful acquire
    ...
finally:
    lock.release()
# or simply: with lock: ...
```

### When cleanup itself fails

Cleanup can raise too (flushing a file to a full disk, rolling back on a dead
connection). Then there are two errors, and the **primary** one is the one you need.

```python
# What happens to the primary error when cleanup also fails?
class Conn:
    def __init__(self, fail_close: bool):
        self.fail_close = fail_close
    def __enter__(self):
        return self
    def __exit__(self, *exc):
        if self.fail_close:
            raise OSError("close failed")
        return False                                   # never return True: that swallows

def work(fail_close: bool):
    with Conn(fail_close):
        raise ValueError("primary failure")

try:
    work(fail_close=True)
except Exception as e:
    print(type(e).__name__, e, "| __context__:", repr(e.__context__))

# Collect several independent failures instead of losing all but the first.
def close_all(resources):
    errors = []
    for r in resources:
        try:
            r()
        except Exception as e:
            errors.append(e)
    if errors:
        raise ExceptionGroup("closing resources", errors)

def ok(): pass
def bad1(): raise OSError("flush a.log")
def bad2(): raise RuntimeError("pool drain")

try:
    close_all([ok, bad1, bad2])
except* OSError as eg:
    print("OSErrors:", [str(e) for e in eg.exceptions])
except* RuntimeError as eg:
    print("RuntimeErrors:", [str(e) for e in eg.exceptions])
```

Output:

```
OSError close failed | __context__: ValueError('primary failure')
OSErrors: ['flush a.log']
RuntimeErrors: ['pool drain']
```

What this shows:

- In Python the cleanup error **wins**; the primary error survives only as
  `__context__` ("During handling of the above exception, another exception occurred").
  It still appears in the printed traceback, but code catching `ValueError` no longer
  sees it. Keep cleanup code simple enough that it rarely raises.
- **Never return `True` from `__exit__`** unless swallowing is the purpose (like
  `contextlib.suppress`).
- When several independent cleanups can fail, run all of them and raise an
  `ExceptionGroup` (Python 3.11+); in Go, `errors.Join` (§12).
- Watch the hierarchy: `TimeoutError`, `ConnectionError`, and `FileNotFoundError` are all
  subclasses of `OSError`, so `except OSError` catches them too.
- **A `close()` error on a file you wrote is a real write error.** Data may be buffered
  until close; ignoring the error loses data silently. (This is why Go code checks the
  error from `Close` on writable files.)

---

## 6 · Timeouts, deadlines, and cancellation

**Every call that crosses a process boundary needs a timeout.** The default for most
clients is *none*: Python `requests` without `timeout=` waits forever, and so does Go's
zero-value `http.Client{}`. A hung dependency then holds a thread, a connection, and a
user — and under load, all of them.

### The simplest timeout

Before deadlines and cancellation, the basic move: give up waiting on a call after a
fixed duration, even though the call itself has no `timeout=` parameter.

```python
# Simplest on-ramp: enforce a timeout on a call that might hang.
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
import time

def slow_call(seconds: float) -> str:
    time.sleep(seconds)
    return "done"

with ThreadPoolExecutor() as pool:
    future = pool.submit(slow_call, 0.3)
    try:
        print(future.result(timeout=0.05))
    except FutureTimeout:
        print("gave up after 0.05s -- the call keeps running in the background")
```

Output:

```
gave up after 0.05s -- the call keeps running in the background
```

That last line is the catch: `slow_call` is still running when the caller moves on —
timing out only stops *waiting*, it doesn't cancel the work (cancellation is covered
below). Real clients (`requests`, database drivers, <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> stubs) build the same idea into a
`timeout=` argument so you don't need the thread pool.

### Deadlines, not per-call timeouts

```
 Per-call timeouts (each 2s)                Propagated deadline (3s total)
 ─────────────────────────────              ─────────────────────────────
 A: 2s  ─▶ B: 2s ─▶ C: 2s                   A (3.0s left) ─▶ B (2.6s left) ─▶ C (1.9s left)
 A's client already gave up at 2s,          Each hop knows how much time is left; work that
 but B and C keep working for 4s more.      can no longer finish in time is not started.
```

A **deadline** is an absolute time for the whole request. Each layer passes it down;
each outbound call uses `min(own timeout, time left)`. <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> propagates deadlines across
services automatically; Go carries them in `context.Context`; in Python asyncio,
`asyncio.timeout_at` applies one to a block.

### Cancellation must be cooperative, and must not be swallowed

```python
# Timeouts and cancellation with asyncio: deadlines, cleanup, and not swallowing cancellation.
import asyncio
import time


async def fetch(name: str, delay: float, log: list[str]) -> str:
    try:
        await asyncio.sleep(delay)              # stands in for a network call
        return f"{name}-data"
    except asyncio.CancelledError:
        log.append(f"{name} cancelled, cleaning up")
        raise                                   # ALWAYS re-raise; swallowing breaks timeouts


async def handler(budget_s: float, log: list[str]) -> dict:
    deadline = asyncio.get_running_loop().time() + budget_s
    async with asyncio.timeout_at(deadline):    # one deadline for the whole request
        profile = await fetch("profile", 0.01, log)
        async with asyncio.TaskGroup() as tg:   # structured: siblings cancelled on failure/timeout
            recs = tg.create_task(fetch("recs", 0.02, log))
            ads = tg.create_task(fetch("ads", 5.0, log))
        return {"profile": profile, "recs": recs.result(), "ads": ads.result()}


async def handler_with_fallback(budget_s: float, log: list[str]) -> dict:
    try:
        return await handler(budget_s, log)
    except TimeoutError:
        return {"degraded": True}               # deliberate, visible degradation


async def main():
    log: list[str] = []
    t = time.perf_counter()
    result = await handler_with_fallback(0.1, log)
    elapsed = time.perf_counter() - t
    print(result, log, f"{elapsed:.2f}s")
    assert result == {"degraded": True}
    assert "ads cancelled, cleaning up" in log and elapsed < 0.5

    log.clear()
    async def swallower():
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            log.append("swallowed")             # BUG: returns normally
            return "pretend success"
    t = time.perf_counter()
    try:
        async with asyncio.timeout(0.05):
            r = await swallower()
        print("timeout ignored! got", r)
    except TimeoutError:
        print("timed out")
    print(f"{time.perf_counter() - t:.2f}s", log)
    print("ALL PASSED")


asyncio.run(main())
```

Output:

```
{'degraded': True} ['ads cancelled, cleaning up'] 0.10s
timeout ignored! got pretend success
0.05s ['swallowed']
```

What the example demonstrates:

1. **One deadline** (`timeout_at`) covers the whole handler, including both parallel
   calls.
2. **`TaskGroup`** gives structured concurrency: when the deadline hits, the running
   sibling (`ads`) is cancelled rather than leaked.
3. **Cleanup on cancellation** runs in `except CancelledError` / `finally`, then
   **re-raises**.
4. **Swallowing `CancelledError` breaks timeouts silently:** the second part of the
   example "succeeded" with a fake result, and the caller's timeout never fired. The same
   happens with `except BaseException` or a bare `except:` around an `await`.
   (`CancelledError` derives from `BaseException` precisely so `except Exception`
   doesn't catch it.)
5. **Degradation is explicit** — `{"degraded": True}` — not a silent empty result.

Threads cannot be cancelled from outside in Python or Go. Long-running synchronous work
must **check** a cancellation signal (`threading.Event`, `ctx.Done()`) between steps.

---

## 7 · Retries done right

Retries turn transient failures into successes — and, done wrong, turn a small outage
into a large one. The questions to answer for every retry:

| Question | Answer |
|---|---|
| **What** is retried? | Only errors known to be transient (timeouts, 503, 429, connection reset). Never 400/401/404 or validation errors. Never unknown exceptions (they may be bugs). |
| **Is it safe to repeat?** | Only if the operation is idempotent, or made so with an idempotency key (§8). A timed-out `POST /charge` may have succeeded. |
| **How long to wait?** | Exponential backoff with **jitter**; honour `Retry-After` when the server sends it. |
| **How many times / how long?** | A small attempt limit **and** an overall deadline. |
| **At which layer?** | **One.** Retrying at the client (×3), the service (×3), and the DB driver (×3) makes 27 attempts per user request against a struggling dependency. |
| **What if many clients retry?** | Retry budgets (e.g. retries ≤ 10% of requests) and circuit breakers — see `SystemDesign/building_blocks/12`. |

Why jitter: without it, a thousand clients that failed at the same moment retry at the
same moment, again and again — synchronised waves that keep the dependency down.

The idea in its smallest form, before backoff, jitter, or a deadline:

```python
# Simplest on-ramp: retry a flaky call a few times with a short pause.
import time

attempts = [RuntimeError("boom"), RuntimeError("boom again"), "ok"]

def flaky_call():
    result = attempts.pop(0)
    if isinstance(result, Exception):
        raise result
    return result

def call_with_simple_retry(fn, max_attempts=3, delay_s=0.01):
    for attempt in range(1, max_attempts + 1):
        try:
            return fn()
        except RuntimeError as e:
            if attempt == max_attempts:
                raise
            print(f"attempt {attempt} failed ({e}), retrying...")
            time.sleep(delay_s)

print(call_with_simple_retry(flaky_call))
```

Output:

```
attempt 1 failed (boom), retrying...
attempt 2 failed (boom again), retrying...
ok
```

Everything below adds what this loop is missing: only retrying errors known to be
transient, backoff that grows and jitters instead of a fixed `delay_s`, and an overall
deadline instead of just an attempt count.

```python
# Retry: one policy object, injected sleep and randomness, retries only what is retryable.
import random
from dataclasses import dataclass
from typing import Callable, TypeVar

T = TypeVar("T")


class Transient(Exception):
    """Safe to retry: timeout, 503, connection reset, 429."""
    def __init__(self, msg: str, retry_after_s: float | None = None):
        super().__init__(msg)
        self.retry_after_s = retry_after_s


class Permanent(Exception):
    """Retrying cannot help: 400, 404, validation, auth failure."""


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 4
    base_s: float = 0.1
    cap_s: float = 5.0
    deadline_s: float = 10.0            # total budget across all attempts

    def delay(self, attempt: int, rng: random.Random) -> float:
        # "Full jitter" (AWS Architecture Blog): uniform in [0, min(cap, base * 2^attempt)].
        return rng.uniform(0, min(self.cap_s, self.base_s * 2 ** attempt))


def call_with_retry(fn: Callable[[], T], policy: RetryPolicy, *,
                    sleep: Callable[[float], None], now: Callable[[], float],
                    rng: random.Random) -> T:
    start = now()
    for attempt in range(policy.max_attempts):
        try:
            return fn()
        except Transient as e:
            last_attempt = attempt == policy.max_attempts - 1
            wait = e.retry_after_s if e.retry_after_s is not None else policy.delay(attempt, rng)
            out_of_time = now() - start + wait > policy.deadline_s
            if last_attempt or out_of_time:
                raise                                  # original exception, original traceback
            sleep(wait)
        # Permanent and unknown exceptions propagate immediately: never retried.
    raise AssertionError("unreachable")


if __name__ == "__main__":
    clock = [0.0]
    slept: list[float] = []
    def fake_sleep(s):
        slept.append(s)
        clock[0] += s

    outcomes = iter([Transient("503"), Transient("timeout"), "ok"])
    def flaky():
        o = next(outcomes)
        if isinstance(o, Exception):
            raise o
        return o

    result = call_with_retry(flaky, RetryPolicy(), sleep=fake_sleep,
                             now=lambda: clock[0], rng=random.Random(42))
    print(result, [round(s, 3) for s in slept])
    assert result == "ok" and len(slept) == 2

    calls = 0
    def bad_request():
        global calls
        calls += 1
        raise Permanent("400 invalid sku")
    try:
        call_with_retry(bad_request, RetryPolicy(), sleep=fake_sleep,
                        now=lambda: clock[0], rng=random.Random(1))
    except Permanent:
        pass
    assert calls == 1                                   # permanent errors are not retried

    def always_down():
        raise Transient("503")
    slept.clear()
    try:
        call_with_retry(always_down, RetryPolicy(max_attempts=4), sleep=fake_sleep,
                        now=lambda: clock[0], rng=random.Random(7))
    except Transient as e:
        print("gave up after", len(slept) + 1, "attempts:", e)
    assert len(slept) == 3

    slept.clear()
    try:
        call_with_retry(lambda: (_ for _ in ()).throw(Transient("429", retry_after_s=30)),
                        RetryPolicy(deadline_s=10), sleep=fake_sleep,
                        now=lambda: clock[0], rng=random.Random(7))
    except Transient:
        print("retry-after 30s exceeds the 10s budget: failed fast, slept", slept)
    assert slept == []
    print("ALL PASSED")
```

Output:

```
ok [0.064, 0.005]
gave up after 4 attempts: 503
retry-after 30s exceeds the 10s budget: failed fast, slept []
ALL PASSED
```

Design choices worth naming in a review or interview:

- **Sleep, clock, and randomness are injected**, so the test runs instantly and is
  deterministic — no real waiting, no flaky assertions.
- **Retryability is decided by type**, set by the adapter that understands the protocol
  (it maps <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> 503 → `Transient`, 400 → `Permanent`). The retry loop knows nothing about
  <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>.
- **Unknown exceptions are not retried.** A `KeyError` is a bug; retrying it three times
  only delays the crash.
- **The last error is re-raised unchanged** (bare `raise`), so its type and traceback
  reach the caller.
- **The deadline check happens before sleeping.** Sleeping 30 s only to exceed a 10 s
  budget wastes the time the caller could have used to fall back.

---

## 8 · Idempotency in code

An operation is **idempotent** if doing it twice has the same effect as doing it once.
Networks make this essential: when a request times out, the client cannot know whether
the server did the work, so the only safe move is to repeat it — which is only safe if
the operation is idempotent.

**Naturally idempotent:** `SET x = 5`, `PUT /users/7 {…}`, `DELETE /orders/9`
(the second delete returns "already gone" — design that as success, `01` §7), "mark
as read", upserts keyed by a natural ID.

**Not idempotent:** `x += 5`, `POST /payments`, "append a row", "send an email".

Four techniques to make them idempotent:

| Technique | How | Example |
|---|---|---|
| **Idempotency key** | Client generates a unique key per logical operation; server stores key → result and replays it | Stripe `Idempotency-Key` header |
| **Natural key / unique constraint** | The operation's identity is a DB unique key; a duplicate insert is a no-op | `UNIQUE(order_id)` on `payments` |
| **Conditional write** | Apply only if state is still what you read | `UPDATE … SET status='paid' WHERE id=? AND status='pending'` |
| **Dedupe on the consumer** | Store processed message IDs in the same transaction as the effect | At-least-once queue consumers |

The simplest version of "dedupe on the consumer" — skip work already done for an ID:

```python
# Simplest on-ramp: skip work already done for a given ID.
processed_ids: set[str] = set()
total = 0

def handle_payment(payment_id: str, amount: int) -> str:
    global total
    if payment_id in processed_ids:
        return "already processed, skipped"
    processed_ids.add(payment_id)
    total += amount
    return "processed"

print(handle_payment("pay-1", 50))
print(handle_payment("pay-1", 50))   # network retry sends the same payment again
print("total charged:", total)
```

Output:

```
processed
already processed, skipped
total charged: 50
```

The full pattern below (idempotency **keys**) generalises this: it also stores the
*result* so a replay can return it, rejects a reused key with a different body, and
handles a retry that arrives while the first attempt is still in flight.

```python
# Idempotency keys: the server remembers the result of each key.
import threading
from dataclasses import dataclass
from typing import Callable


class IdempotencyConflict(Exception):
    """Same key reused with a different request — a client bug."""


class InProgress(Exception):
    """A request with this key is still running; tell the client to retry later (409/425)."""


@dataclass
class _Record:
    fingerprint: str
    done: bool = False
    result: object = None


class IdempotencyStore:
    """In production this is a table: (key PK, fingerprint, status, response, expires_at),
    and the claim is an INSERT that fails on a duplicate key."""

    def __init__(self):
        self._records: dict[str, _Record] = {}
        self._lock = threading.Lock()

    def run(self, key: str, fingerprint: str, operation: Callable[[], object]) -> object:
        with self._lock:                                   # atomic claim
            rec = self._records.get(key)
            if rec is None:
                self._records[key] = _Record(fingerprint)
            elif rec.fingerprint != fingerprint:
                raise IdempotencyConflict(key)
            elif rec.done:
                return rec.result                          # replay the stored result
            else:
                raise InProgress(key)
        try:
            result = operation()
        except Exception:
            with self._lock:
                del self._records[key]                     # failed: let the client retry for real
            raise
        with self._lock:
            rec = self._records[key]
            rec.done, rec.result = True, result
        return result


if __name__ == "__main__":
    store = IdempotencyStore()
    balance = {"acct": 100}

    def withdraw(amount):
        def op():
            balance["acct"] -= amount
            return {"balance": balance["acct"]}
        return op

    r1 = store.run("key-1", "withdraw:30", withdraw(30))
    r2 = store.run("key-1", "withdraw:30", withdraw(30))     # client retried after a timeout
    print(r1, r2, balance)
    assert r1 == r2 and balance["acct"] == 70

    try:
        store.run("key-1", "withdraw:99", withdraw(99))
    except IdempotencyConflict:
        print("key reuse with a different body rejected")

    def failing():
        raise TimeoutError("bank down")
    try:
        store.run("key-2", "withdraw:10", failing)
    except TimeoutError:
        pass
    print(store.run("key-2", "withdraw:10", withdraw(10)), balance)
    assert balance["acct"] == 60
    print("ALL PASSED")
```

Output:

```
{'balance': 70} {'balance': 70} {'acct': 70}
key reuse with a different body rejected
{'balance': 60} {'acct': 60}
ALL PASSED
```

Details that separate a correct implementation from a naive one:

- **The claim is atomic** (the lock here; an `INSERT` into a table with the key as
  primary key in production). Check-then-insert without atomicity lets two concurrent
  retries both run.
- **A fingerprint of the request is stored with the key.** Same key + different body is
  a client bug and must be rejected, not replayed.
- **In-progress is its own state.** A retry arriving while the first attempt is still
  running must not start a second execution.
- **Failure policy is explicit.** Here a failed operation releases the key so a retry
  runs for real. That is correct only if the failure left no side effect. If the
  operation might have partially happened (a timeout from a downstream charge), keep the
  key in an "unknown" state and reconcile instead.
- **Keys expire** (e.g. after 24 h), and the expiry is part of the documented contract.
- **Store the result in the same transaction as the effect** when both live in the same
  database — otherwise a crash between them re-opens the double-execution window.

---

## 9 · Partial failure: step ordering and compensation

A multi-step operation that is not wrapped in one transaction can fail halfway. The
question is not "how do I catch the error" but **"what state does the world end up in?"**

```arch
%% caption: Partial Failure Compensation Flow (Saga Pattern)
node client "Client" at 0,1 icon=client
node s1 "Step 1\n(Reserve Inventory)" at 1,0 icon=box color=blue
node s2 "Step 2\n(Charge Card)" at 2,1 icon=payment color=amber
node comp "Compensate\n(Release Inventory)" at 1,2 icon=undo color=red

client -> s1 : "1. do()"
client -> s2 : "2. do() [fails]"
s2 -> comp : "3. error triggers undo()"
```

### Order the steps

1. **Do reversible, local things first** (reserve inventory, write a `PENDING` row).
2. **Do the irreversible or external thing last** (charge a card, send an email, ship).
3. **Record intent before the external call, and the outcome after** (`08` §4.3), so a
   crash leaves a detectable, resumable state instead of silent inconsistency.

### Compensate what already happened

When a later step fails, undo earlier steps in **reverse order**. `ExitStack` is a
ready-made compensation stack:

```python
# Compensation: undo completed steps in reverse order when a later step fails.
from contextlib import ExitStack


class Inventory:
    def __init__(self, stock, log):
        self.stock = dict(stock)
        self.log = log
    def reserve(self, sku, qty):
        if self.stock.get(sku, 0) < qty:
            raise RuntimeError(f"out of stock: {sku}")
        self.stock[sku] -= qty
        self.log.append(f"reserve {sku}x{qty}")
    def release(self, sku, qty):
        self.stock[sku] += qty
        self.log.append(f"release {sku}x{qty}")


class Wallet:
    def __init__(self, balance, log):
        self.balance = balance
        self.log = log
    def debit(self, amount):
        if amount > self.balance:
            raise RuntimeError("insufficient funds")
        self.balance -= amount
        self.log.append(f"debit {amount}")
    def refund(self, amount):
        self.balance += amount
        self.log.append(f"refund {amount}")


def checkout(inv: Inventory, wallet: Wallet, items: dict[str, int], price: int,
             ship: callable) -> str:
    with ExitStack() as undo:                      # a stack of compensations
        for sku, qty in items.items():
            inv.reserve(sku, qty)
            undo.callback(inv.release, sku, qty)   # registered only AFTER the step succeeded
        wallet.debit(price)
        undo.callback(wallet.refund, price)
        tracking = ship(items)                     # last step: the hardest to undo
        undo.pop_all()                             # success: discard compensations
        return tracking


if __name__ == "__main__":
    log: list[str] = []
    inv, wallet = Inventory({"a": 5, "b": 1}, log), Wallet(100, log)
    print(checkout(inv, wallet, {"a": 2, "b": 1}, 50, ship=lambda items: "TRACK-1"))
    assert inv.stock == {"a": 3, "b": 0} and wallet.balance == 50

    log = []
    inv, wallet = Inventory({"a": 5, "b": 1}, log), Wallet(100, log)
    def courier_down(items):
        raise ConnectionError("courier API down")
    try:
        checkout(inv, wallet, {"a": 2, "b": 1}, 50, ship=courier_down)
    except ConnectionError as e:
        print("failed:", e)
    print(log)
    assert inv.stock == {"a": 5, "b": 1} and wallet.balance == 100   # fully compensated

    log = []
    inv, wallet = Inventory({"a": 5, "b": 0}, log), Wallet(100, log)
    try:
        checkout(inv, wallet, {"a": 2, "b": 1}, 50, ship=lambda i: "x")
    except RuntimeError as e:
        print("failed:", e, log)
    assert inv.stock == {"a": 5, "b": 0} and wallet.balance == 100
    print("ALL PASSED")
```

Output:

```
TRACK-1
failed: courier API down
['reserve ax2', 'reserve bx1', 'debit 50', 'refund 50', 'release bx1', 'release ax2']
failed: out of stock: b ['reserve ax2', 'release ax2']
ALL PASSED
```

Rules the example follows:

- **Register a compensation only after its step succeeds.** Registering before would
  "release" stock that was never reserved.
- **Compensations run in reverse (<abbr title="Last-In, First-Out. A method for processing data where the last items entered are the first to be removed, characteristic of stack data structures.">LIFO</abbr>) order** — the log shows refund, then release b,
  then release a.
- **`pop_all()` on success** discards them.
- **The original error propagates** after compensation, so the caller still learns what
  failed.

What an in-process compensation stack **cannot** do: survive a crash. If the process
dies between `debit` and `refund`, nothing runs the refund. For that you need durable
state — a saga with its progress persisted, or a reconciliation job that finds
inconsistent records (`CSFundamentals/04` §3). Compensations must also be idempotent,
because a durable saga may run one twice.

**Semantic undo is not the same as rollback.** A refund is a new transaction, visible on
the statement; an email cannot be unsent (the compensation is a follow-up email). Design
the order of steps so the hardest-to-compensate step comes last.

---

## 10 · Fail fast, crash, or degrade?

| Strategy | Use when | Example |
|---|---|---|
| **Fail fast** — check preconditions early and stop | Input or configuration is wrong; continuing would do damage or waste work | Validate config at startup and refuse to boot; reject a request before touching the DB |
| **Crash** — let the process or task die | An invariant is broken: state can no longer be trusted | Corrupted in-memory index; `assert` failure in a ledger; Go `panic` on impossible state |
| **Degrade** — continue with reduced function | A **non-essential** dependency is unavailable | Recommendations down → show bestsellers; spell-check down → submit without it |
| **Retry** | Transient, idempotent (§7) | 503 from a replica |

### Fail fast at startup

```python
@dataclass(frozen=True)
class Settings:
    db_url: str
    payment_timeout_s: float

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Settings":
        missing = [k for k in ("DB_URL", "PAYMENT_TIMEOUT_S") if k not in env]
        if missing:
            raise SystemExit(f"missing required config: {', '.join(missing)}")
        return cls(env["DB_URL"], float(env["PAYMENT_TIMEOUT_S"]))
```

A service that boots with a missing setting and fails on the first real request at
2 a.m. is worse than one that refuses to deploy.

### Crash-only thinking

Erlang's "let it crash" and "crash-only software" (Candea & Fox) make the same point:
**if recovery from a crash is correct, you don't need a separate, rarely-tested clean
shutdown path.** Code that tries to limp on after an invariant breaks usually corrupts
more data. Instead: crash the smallest unit (a request, a task, a worker), let a
supervisor restart it, and make startup recovery the normal path.

### Degradation must be visible

```python
def product_page(product_id):
    product = catalog.get(product_id)                  # essential: failure → error page
    try:
        recs = recommender.for_product(product_id, timeout_s=0.15)
    except (Transient, TimeoutError):
        metrics.increment("recs.fallback")              # visible: a dashboard shows it
        recs = bestsellers.cached()                     # deliberate, bounded fallback
    return render(product, recs)
```

The difference from swallowing: the fallback is **narrow** (specific error types),
**intentional** (a real alternative), and **observable** (a metric). A fallback that
catches `Exception` and returns `[]` turns every bug in the recommender into an empty
widget nobody notices.

### Assertions

- `assert` documents and checks **internal invariants** — things that are impossible if
  the code is correct. Never use it for input validation: `python -O` strips asserts.
- In Go, `panic` is for the same class of impossible states; return errors for everything
  else. Recover only at goroutine/request boundaries (§12).

---

## 11 · Validation: fail on first error or collect them all?

| Situation | Strategy | Why |
|---|---|---|
| User-facing form or <abbr title="Application Programming Interface">API</abbr> request body | **Collect all** field errors | The user fixes everything in one round trip |
| Batch import of a million rows | **Collect per row**, continue, report a summary; abort if error rate > threshold | One bad row shouldn't block the batch; 90% bad means a wrong file |
| Precondition inside domain logic | **Fail on first** | Later checks may depend on earlier ones |
| Config at startup | **Collect all**, then refuse to start | Fix the deployment once, not five times |

```python
@dataclass(frozen=True)
class FieldError:
    field: str
    message: str

class ValidationFailed(Exception):
    def __init__(self, errors: list[FieldError]):
        super().__init__("; ".join(f"{e.field}: {e.message}" for e in errors))
        self.errors = errors

def parse_signup(body: dict) -> Signup:
    errors: list[FieldError] = []
    email = str(body.get("email", "")).strip()
    if "@" not in email:
        errors.append(FieldError("email", "must be a valid email address"))
    age = body.get("age")
    if not isinstance(age, int) or not 13 <= age <= 130:
        errors.append(FieldError("age", "must be an integer between 13 and 130"))
    if errors:
        raise ValidationFailed(errors)            # all problems, one response
    return Signup(email=email, age=age)           # parse, don't validate (01 §8)
```

Libraries like Pydantic do exactly this and return a structured list of errors; the
design point is to **return all errors in a machine-readable form**, not a single string.

---

## 12 · The same ideas in Go

Go makes every failure point visible. The design questions are identical; the idioms:

- **Wrap with context** using `fmt.Errorf("doing X: %w", err)` — each layer adds what it
  was doing, forming a readable chain.
- **Branch on categories** with `errors.Is` (sentinel identity) and `errors.As` (typed
  errors carrying data) — never by comparing strings.
- **Decide meaning at the edge**: map categories to <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> status in one place.
- **Deadlines and cancellation** travel in `context.Context`; I/O functions return
  `ctx.Err()` when it's done.
- **Cleanup errors** are combined with `errors.Join` in a deferred function with a named
  return.
- **Panics** are for impossible states; `recover` only at goroutine boundaries, because an
  unrecovered panic in *any* goroutine kills the whole process.

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"strings"
	"time"
)

// Categories callers branch on: sentinels (identity) and a typed error (carries data).
var (
	ErrNotFound    = errors.New("not found")
	ErrUnavailable = errors.New("unavailable") // transient: retryable
)

type ValidationError struct {
	Field, Reason string
}

func (e *ValidationError) Error() string { return e.Field + ": " + e.Reason }

// Lowest layer: says what failed, in its own terms.
func queryUser(ctx context.Context, id string) (string, error) {
	select {
	case <-time.After(20 * time.Millisecond): // pretend network latency
	case <-ctx.Done():
		return "", ctx.Err() // context.DeadlineExceeded or context.Canceled
	}
	if id == "missing" {
		return "", ErrNotFound
	}
	if id == "flaky" {
		return "", fmt.Errorf("dial db-3:5432: connection refused: %w", ErrUnavailable)
	}
	return "user:" + id, nil
}

// Middle layer: adds context about WHAT IT WAS DOING. Does not log. Does not decide.
func loadProfile(ctx context.Context, id string) (string, error) {
	if strings.TrimSpace(id) == "" {
		return "", &ValidationError{Field: "id", Reason: "must not be empty"}
	}
	u, err := queryUser(ctx, id)
	if err != nil {
		return "", fmt.Errorf("load profile %q: %w", id, err)
	}
	return u, nil
}

// Edge: the one place that decides what the failure MEANS for the client, and logs once.
func httpStatus(err error) int {
	var ve *ValidationError
	switch {
	case err == nil:
		return 200
	case errors.As(err, &ve):
		return 400
	case errors.Is(err, ErrNotFound):
		return 404
	case errors.Is(err, context.DeadlineExceeded):
		return 504
	case errors.Is(err, ErrUnavailable):
		return 503
	default:
		return 500
	}
}

// Cleanup errors must not be lost, and must not hide the primary error.
type file struct {
	name      string
	failClose bool
}

func (f *file) Write(p []byte) (int, error) { return len(p), nil }
func (f *file) Close() error {
	if f.failClose {
		return fmt.Errorf("close %s: disk full on flush", f.name)
	}
	return nil
}

func save(f io.WriteCloser, data string, failWrite bool) (err error) {
	defer func() {
		err = errors.Join(err, f.Close()) // both errors survive; nil if both nil
	}()
	if failWrite {
		return errors.New("write: short write")
	}
	_, err = f.Write([]byte(data))
	return err
}

// A panic in a goroutine kills the whole process. Recover at the goroutine boundary only.
func safeGo(fn func()) <-chan error {
	done := make(chan error, 1)
	go func() {
		defer func() {
			if r := recover(); r != nil {
				done <- fmt.Errorf("worker panicked: %v", r)
			}
		}()
		fn()
		done <- nil
	}()
	return done
}

func main() {
	for _, id := range []string{"42", "", "missing", "flaky"} {
		_, err := loadProfile(context.Background(), id)
		fmt.Printf("%-9q -> %d  %v\n", id, httpStatus(err), err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Millisecond)
	defer cancel()
	_, err := loadProfile(ctx, "42")
	fmt.Printf("%-9s -> %d  %v\n", "deadline", httpStatus(err), err)

	fmt.Println(save(&file{name: "a"}, "x", false))
	fmt.Println(save(&file{name: "b", failClose: true}, "x", false))
	fmt.Println(save(&file{name: "c", failClose: true}, "x", true))

	var m map[string]int
	fmt.Println(<-safeGo(func() { m["boom"] = 1 }))
}
```

Output:

```
"42"      -> 200  <nil>
""        -> 400  id: must not be empty
"missing" -> 404  load profile "missing": not found
"flaky"   -> 503  load profile "flaky": dial db-3:5432: connection refused: unavailable
deadline  -> 504  load profile "42": context deadline exceeded
<nil>
close b: disk full on flush
write: short write
close c: disk full on flush
worker panicked: assignment to entry in nil map
```

Notice:

- The middle layer (`loadProfile`) **only adds context**: no logging, no status codes.
- `"flaky"` reads as a sentence from outer to inner: *load profile → dial → refused →
  unavailable*.
- The deadline case needed no special code in the middle layer: `ctx.Err()` was wrapped
  and `errors.Is(err, context.DeadlineExceeded)` still finds it.
- For file `c`, both the write error and the close error survive, one per line.
- Common Go mistakes: `if err != nil { return err }` with no context at every layer (the
  top-level message is just `connection refused` — from where?), `log.Printf(err);
  return err` (double logging), `_ = f.Close()` on a writable file, and `panic` for
  ordinary errors.

---

## 13 · Testing failure paths

Error-handling code is the least-tested code in most repositories — it runs rarely, so
bugs in it surface during incidents. Test it deliberately.

| Technique | How | Example |
|---|---|---|
| **Fakes that fail on command** | A fake adapter with a switch or a script of outcomes | `FakePayments(decline_over_cents=500)` in `08` §4.5; `iter([Transient, Transient, "ok"])` in §7 |
| **Inject time and sleep** | Pass `now`, `sleep`, `rng`; advance a fake clock | Retry tests run in microseconds |
| **Assert final state, not just the exception** | After a failure, check what was stored, charged, published | §9 asserts stock and balance are fully restored |
| **Table of failure points** | Fail step 1, then step 2, … step N; assert consistency each time | Catches a compensation that was registered too early |
| **Fault injection in integration tests** | Toxiproxy, network namespaces, killing a container mid-test | Timeouts actually configured? Pool recovers after DB restart? |
| **Chaos / game days** | Inject failures in staging or production deliberately | Google DiRT, Netflix Chaos Monkey |
| **Crash tests** | Kill the process between steps, restart, run recovery | The outbox or sweeper completes the work |

```python
import pytest

@pytest.mark.parametrize("fail_at", ["reserve_b", "debit", "ship"])
def test_checkout_leaves_no_trace_when_any_step_fails(fail_at):
    log = []
    inv = Inventory({"a": 5, "b": 1 if fail_at != "reserve_b" else 0}, log)
    wallet = Wallet(100 if fail_at != "debit" else 10, log)
    ship = (lambda i: (_ for _ in ()).throw(ConnectionError())) if fail_at == "ship" else (lambda i: "T")
    with pytest.raises((RuntimeError, ConnectionError)):
        checkout(inv, wallet, {"a": 2, "b": 1}, 50, ship)
    assert inv.stock == {"a": 5, "b": 1 if fail_at != "reserve_b" else 0}
    assert wallet.balance == (100 if fail_at != "debit" else 10)
```

---

## 14 · Red flags

| Red flag | Why it's bad | Fix |
|---|---|---|
| `except Exception: pass` / `_ = err` | Bugs and outages become silent wrong behaviour | Handle specifically, or let it propagate |
| Same error logged at several layers | Noise; can't tell one failure from five | Log once, at the boundary |
| Bare `except:` or `except BaseException` around `await` | Breaks Ctrl-C and cancellation/timeouts | `except Exception`, and re-raise `CancelledError` |
| <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> call with no timeout | One hung dependency exhausts threads/connections | Timeout on every remote call; propagate deadlines |
| Retry loop with no backoff/jitter/limit | Retry storms; outages last longer | §7 |
| Retrying a non-idempotent call | Double charges, duplicate emails | Idempotency key or don't retry (§8) |
| Retries at multiple layers | Multiplicative load | Retry at one layer |
| Catching an error to return `None`/`[]`/`False` | Callers can't distinguish "empty" from "broken" | Raise; or return an explicit result type |
| `raise NewError(...)` losing the cause | Root cause gone from logs | `raise ... from e`, `%w` |
| Error messages with tokens, passwords, full bodies | Credential and PII leaks into logs | Identifiers only |
| Internal error text sent to clients | Leaks stack/schema; clients start parsing it | Stable code + public message |
| External call inside an open DB transaction | Lock contention; inconsistent state on timeout | Commit, call, commit |
| `assert` for input validation | Stripped under `python -O` | Explicit checks raising validation errors |
| Huge `try` blocks | Handles errors from code that wasn't meant to be covered | Minimal `try`, logic in `else` |
| Fallback that hides failures without a metric | Degradation becomes permanent and invisible | Narrow catch + metric + alert |

---

## 15 · Interview questions and model answers

**Q: Exceptions or return codes?**
Depends on whether the outcome is a failure or an expected result. In Python I raise
exceptions for failures that callers normally propagate — invalid input, infrastructure
errors, bugs — and return a union type for outcomes callers must always branch on, like
"seat taken" in a booking system, so the type checker enforces handling. In Go, errors
are values; I wrap with context and branch on categories with `errors.Is`/`As`.

**Q: When should you catch an exception?**
Only to recover (retry, fall back), to translate it into this layer's vocabulary, to add
context and re-raise, or at a boundary — the top of a request, job, or goroutine — where
I log once and keep the process alive. Anywhere else I let it propagate.

**Q: How do you design retries?**
Retry only transient errors, only idempotent operations, with exponential backoff and
jitter, a small attempt limit and an overall deadline, at exactly one layer. Honour
`Retry-After`. At fleet scale add a retry budget and circuit breaker so retries can't
amplify an outage.

**Q: A payment request timed out. What do you do?**
I don't know whether it succeeded, so I retry with the same idempotency key — the
provider returns the original result if it already charged. The order was stored as
pending before the call, so if we crash, a reconciliation job can query the provider by
that key and finish or cancel the order.

**Q: How would you implement idempotency keys server-side?**
A table keyed by the idempotency key with a request fingerprint, status, stored response,
and expiry. Claim the key atomically with an insert; if it exists and is complete, replay
the response; if the fingerprint differs, reject; if in progress, return a retry-later
status. Ideally write the key record in the same transaction as the business effect.

**Q: What's the difference between a timeout and a deadline?**
A timeout is a duration for one call; a deadline is an absolute point in time for the
whole request, propagated through every hop. With deadlines, downstream work stops when
the original caller has already given up, and each hop only uses the time actually left.

**Q: When should a service crash instead of handling an error?**
When an invariant is broken and state can't be trusted — continuing risks corrupting
data. Crash the smallest unit, let a supervisor restart it, and make sure startup
recovery is correct. Also fail fast at startup on bad config rather than failing on the
first request.

**Q: How do you handle failure in a multi-step operation without a distributed
transaction?**
Order steps so reversible local work comes first and the irreversible external call
last; persist intent before and outcome after the external call; make each step
idempotent; and compensate completed steps in reverse order on failure. If compensation
must survive crashes, persist saga state or run a reconciliation job.

---

## 16 · Checklist

**Classification**
- [ ] Each failure is classified: bug, invalid input, domain outcome, transient, persistent, partial.
- [ ] Expected business outcomes are return values, not exceptions callers might forget.
- [ ] Error categories callers branch on are types/sentinels, not strings.

**Handling**
- [ ] Every `except` recovers, translates, adds context, or is a boundary.
- [ ] Errors are logged once, at the boundary, with the cause chain intact.
- [ ] `try` blocks contain only the call that can raise the handled error.
- [ ] Clients get stable codes and safe messages; logs get the details; neither gets secrets.

**Resources and time**
- [ ] Every resource is released on success, error, and cancellation.
- [ ] Cleanup errors are not lost and do not hide the primary error.
- [ ] Every remote call has a timeout; request deadlines propagate.
- [ ] `CancelledError` is never swallowed.

**Retries and idempotency**
- [ ] Only transient errors on idempotent operations are retried, at one layer.
- [ ] Backoff has jitter, an attempt limit, and an overall deadline.
- [ ] Non-idempotent operations exposed to retries use idempotency keys or conditional writes.

**Partial failure**
- [ ] Reversible steps first, irreversible last; intent recorded before external calls.
- [ ] Compensations are registered after success, run in reverse, and are idempotent.
- [ ] Something (retry, sweeper, reconciliation) completes work interrupted by a crash.

**Tests**
- [ ] Each failure point has a test asserting the final state, not just the exception.
- [ ] Time, sleep, and randomness are injected so failure tests are fast and deterministic.
