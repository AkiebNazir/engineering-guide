# The Philosophy of Software Design

> "There are two ways of constructing a software design: One way is to make it so simple
> that there are obviously no deficiencies, and the other way is to make it so complicated
> that there are no obvious deficiencies." — C. A. R. Hoare

This file is about **how to think** when you write code, not a list of rules to memorize.
Every rule you have ever heard (DRY, SOLID, "small functions", "comment your code") is a
tool for one goal: **keeping complexity under control.** Once you understand the goal, you
can tell when a rule applies, when it doesn't, and when two rules disagree.

The spine of this file is John Ousterhout's *A Philosophy of Software Design*, with the
most useful ideas from *Clean Code*, *Refactoring*, the Go proverbs, and functional
programming folded in where they sharpen the picture. Examples are in **Python and Go**.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| SOLID with before/after examples | `02_oop_and_domain_modeling.md` §12 |
| Law of Demeter, composition over inheritance | `02_oop_and_domain_modeling.md` §9, §4 (all named principles are indexed in §17 below) |
| Design patterns (GoF) | `04_design_patterns_in_practice.md` §1 (all 23 at a glance), §3–§18 |
| Layered / hexagonal / clean architecture | `08_application_architecture_in_code.md` §2–§3 |
| Testing pyramid, TDD, code review | `05_testability_refactoring_and_legacy_code.md` §1, §5, §10 |
| Named anti-patterns (god object, shotgun surgery...) | `05_testability_refactoring_and_legacy_code.md` §6 |

---

## Contents

1. [What complexity actually is](#1--what-complexity-actually-is)
2. [Strategic vs. tactical programming](#2--strategic-vs-tactical-programming)
3. [Deep modules](#3--deep-modules)
4. [Information hiding (and leakage)](#4--information-hiding-and-leakage)
5. [Pull complexity downward](#5--pull-complexity-downward)
6. [Different layer, different abstraction](#6--different-layer-different-abstraction)
7. [Define errors out of existence](#7--define-errors-out-of-existence)
8. [Make illegal states unrepresentable](#8--make-illegal-states-unrepresentable)
9. [Functional core, imperative shell](#9--functional-core-imperative-shell)
10. [Functions: size, shape, and flow](#10--functions-size-shape-and-flow)
11. [Names](#11--names)
12. [Comments](#12--comments)
13. [Consistency and obviousness](#13--consistency-and-obviousness)
14. [Duplication and abstraction](#14--duplication-and-abstraction)
15. [Design it twice](#15--design-it-twice)
16. [A worked refactor, start to finish](#16--a-worked-refactor-start-to-finish)
17. [When principles collide](#17--when-principles-collide)
18. [Red flags — the master table](#18--red-flags--the-master-table)
19. [How this shows up in interviews](#19--how-this-shows-up-in-interviews)
20. [The checklist](#20--the-checklist)
21. [Further reading](#21--further-reading)

---

## 1 · What complexity actually is

Ousterhout's definition:

> **Complexity is anything related to the structure of a software system that makes it
> hard to understand and modify the system.**

Note what this definition is *not*:

- It is **not** size. A 10,000-line system that is easy to change is simple.
- It is **not** algorithmic complexity. O(n log n) says nothing about readability.
- It is **not** measured by the author. Complexity is felt by the **reader** — the person
  changing the code six months from now, who is usually you with no memory of writing it.

A useful mental formula:

```
            ___
Complexity = \   (complexity of part p) × (time developers spend in part p)
            /__
             p
```

A horrible module nobody ever opens costs almost nothing. A mildly confusing function
that every feature touches costs enormously. **Spend your cleanliness budget where people
actually work.**

### The three symptoms

| Symptom | What it feels like | Example |
|---|---|---|
| **Change amplification** | A simple change requires edits in many places. | The brand colour is hard-coded in 40 CSS files. Adding a field to `User` means editing the model, 3 serializers, 2 validators, and the migration by hand. |
| **Cognitive load** | You must hold a lot in your head to make a change safely. | A function that works only if you remember to call `init()` first, lock `mu`, and never pass a negative id. |
| **Unknown unknowns** | You can't even tell *what* you need to know. | Changing a timeout breaks a retry loop in a different service that silently assumed the old value. |

Unknown unknowns are the worst of the three. Change amplification is annoying but
*visible* — grep finds all 40 files. Cognitive load is costly but you *know* you're
loaded. An unknown unknown gives you no signal at all until production breaks.

> **The core goal of good design is to make the system *obvious*:** a developer can form
> a correct guess about what the code does, and about what they need to change, quickly
> and without great effort.

### The two causes

Every symptom traces back to one of two causes:

1. **Dependencies** — code that can't be understood or changed in isolation. Some
   dependencies are unavoidable (a caller depends on a function's signature). The goal is
   *fewer* dependencies, and making the remaining ones **obvious**.
2. **Obscurity** — important information is not visible. A variable named `data`. A
   magic number. A function whose error behavior is undocumented. A config key read in
   one file and written in another.

### Complexity is incremental

No single change makes a codebase terrible. It's a thousand small "just this once"
decisions, each individually defensible:

```
 week 1   add a boolean flag             "it's just one parameter"
 week 3   add a special case             "only this customer needs it"
 week 6   copy-paste the handler         "no time to generalize"
 week 9   add a second flag              "same pattern as the first one"
 week 14  nobody wants to touch the file
```

Because it accumulates silently, you need **zero tolerance** for small increments. The
moment to fix it is when the change is small, not after it has compounded.

---

## 2 · Strategic vs. tactical programming

**Tactical programming:** the goal is to get *this feature* working *now*. Design is
whatever falls out of the shortest path to green tests.

**Strategic programming:** the goal is a **great design that also happens to work**.
Working code is necessary but not sufficient.

```
 value
   ▲                                         strategic
   │                                    ___---
   │                              ___---
   │                        __---
   │                  __--          ___..... tactical
   │            __--      __..--''
   │       _--  __..--''
   │   _-..--'
   │ .'
   └──────────────────────────────────────────────────▶ time
     tactical looks faster early; strategic wins within months
```

Ousterhout's recommendation: spend roughly **10–20% of development time on design
investment** — improving structure, writing interface comments, fixing a clumsy
abstraction you noticed while passing through. It's slower at first and faster within
months, because every future change is cheaper.

**The tactical tornado.** Every team has someone who ships features very quickly and
leaves a trail of wreckage for others to clean up. Management often sees them as the
most productive person on the team. Their real productivity is negative, because the
cost lands on everyone else.

**Practical strategic habits:**

- When you open a file to make a change, leave the surrounding code slightly better than
  you found it (the "boy scout rule") — but *keep the cleanup in a separate commit* so
  review stays easy.
- If a change requires a hack, first ask: *"Is there a design where this change would
  have been natural?"* Often a 30-minute restructure makes the feature a 5-line change.
- Treat design as ongoing, not a phase. You understand the problem best *after* you've
  written the first version.

---

## 3 · Deep modules

This is the single most important idea in the file.

A **module** is anything with an interface and an implementation: a function, a class,
a package, a service. Every module has:

- a **cost** — its interface, which every user must learn;
- a **benefit** — the functionality it provides, hidden behind that interface.

```
      DEEP MODULE                         SHALLOW MODULE

   ┌──────────────┐ ◀─ small interface   ┌──────────────────────────────┐ ◀─ big interface
   │              │                      │                              │
   │              │                      └──────────────────────────────┘ ◀─ little inside
   │              │
   │   lots of    │
   │ functionality│
   │   hidden     │
   │              │
   └──────────────┘
```

**The best modules are deep:** a simple interface hiding a lot of power.

### Canonical deep modules

**Unix file I/O.** Five calls — `open`, `read`, `write`, `lseek`, `close` — hide
directory lookup, permissions, disk block allocation, caching, buffering, device
drivers, concurrent access, and journaling. Implementations have changed radically for
decades; the interface barely has.

**Go's `io.Reader`.**

```go
type Reader interface {
    Read(p []byte) (n int, err error)
}
```

One method. Files, network sockets, gzip streams, HTTP bodies, in-memory buffers, and
encryption layers all implement it, and everything that consumes a `Reader`
(`io.Copy`, `bufio.Scanner`, `json.NewDecoder`) works with all of them. Rob Pike's
proverb: **"The bigger the interface, the weaker the abstraction."**

**Garbage collection.** The interface is *nothing* — you just stop using the object. The
implementation is one of the most sophisticated pieces of any runtime.

**Python's `dict`.** `d[k]`, `d[k] = v`, `del d[k]`, `k in d`. Behind it: open
addressing, perturbation-based probing, resizing, a compact insertion-ordered layout,
key-sharing between instances. You never think about any of it.

### Canonical shallow modules

```python
# Shallow: the interface is as complex as the implementation.
class UserNameGetter:
    def __init__(self, user):
        self._user = user

    def get_user_name(self):
        return self._user.name
```

Calling `UserNameGetter(user).get_user_name()` is *more* work than `user.name`.
The module costs a name, a file, an import, and a concept — and gives nothing.

Other shallow patterns:

- **Pass-through methods** — a method whose only job is to call another method with the
  same signature (see §6).
- **Getter/setter pairs for every field** — they expose the representation almost as
  much as a public field, while adding ceremony.
- **One-method wrapper classes** around a stdlib function, "in case we swap it later."

### Classitis

The belief that "classes should be small" taken to an extreme produces **classitis**:
dozens of tiny classes, each simple, whose *combination* is enormously complex. Every
class boundary adds an interface to learn.

The textbook example is old Java I/O:

```java
FileInputStream     fileStream     = new FileInputStream(fileName);
BufferedInputStream bufferedStream = new BufferedInputStream(fileStream);
ObjectInputStream   objectStream   = new ObjectInputStream(bufferedStream);
```

Buffering is what almost everyone wants, yet you have to ask for it explicitly — and if
you forget, nothing fails; the program is just slow. **The common case should be the
default.** Compare Python:

```python
with open(path, "rb") as f:   # buffered by default; pass buffering=0 to opt out
    data = f.read()
```

### How to make a module deeper

1. **Ask what the caller actually wants**, not what the implementation happens to do.
   The caller wants "give me the config"; they don't want "open file, parse TOML, merge
   env vars, validate schema."
2. **Make the common case trivial.** Defaults should be right for 90% of callers.
3. **Merge modules that are always used together.** If every caller does `a(); b()`,
   there should be one function.
4. **Be somewhat general-purpose.** An interface designed for exactly today's one use
   case tends to be shallow and specialized. Ask: *"What is the simplest interface that
   covers all my current needs?"* and *"In how many situations will this method be
   used?"* A text editor's buffer is deeper with `insert(pos, text)` and
   `delete(start, end)` than with `backspace()` and `delete_selection()`.

> **Depth is the counterweight to "small functions."** Small is not the goal. A
> 60-line function with a two-parameter signature that fully solves a problem is often
> better than six 10-line functions whose caller must orchestrate all six.

---

## 4 · Information hiding (and leakage)

**Information hiding:** each module encapsulates a few *design decisions* — a data
format, an algorithm, a protocol detail — and the decision is invisible from outside.
If the decision changes, only that module changes.

This is the mechanism that makes modules deep.

### Information leakage

Leakage happens when **one design decision is reflected in several modules.** Change the
decision and all of them must change together — change amplification plus unknown
unknowns.

Leakage doesn't require a shared interface. **Back-door leakage** is worse: two modules
both "know" the file format, or both assume the list is sorted, with nothing in the code
linking them.

```python
# LEAKY: two modules both know the on-disk format.

# writer.py
def save(records, path):
    with open(path, "w") as f:
        for r in records:
            f.write(f"{r.id}|{r.name}|{r.email}\n")

# reader.py  — written by someone else, three months later
def load(path):
    with open(path) as f:
        return [Record(*line.rstrip("\n").split("|")) for line in f]
```

Add a field, or allow `|` inside a name, and you must find *both* files. Nothing tells
you that.

```python
# HIDDEN: one module owns the format. Nobody else knows it exists.

# record_store.py
_SEP = "|"

def save(records, path): ...
def load(path): ...
```

**Fix for leakage:** pull the shared knowledge into a single module that owns it. If two
classes both need to know a format, that is usually a sign they should be one class.

### Temporal decomposition — the most common source of leakage

Structuring code by the **order operations happen** rather than by **what knowledge they
need**:

```
 BAD (temporal)                      GOOD (by knowledge)

 read_file.py   ─┐                   http_request.py
 parse_file.py  ─┼─ all three know   ├── parse()   ┐
 write_file.py  ─┘  the format       ├── serialize()├─ format known in ONE place
                                     └── validate()┘
```

Reading and writing happen at different times, but they share the knowledge of the
format, so they belong together. **Decompose by knowledge, not by time.**

### Over-exposure in the interface

- Returning internal mutable state (`return self._items` instead of a copy or iterator).
- Configuration that exposes implementation (`hash_bucket_count=` on a cache class).
- Exceptions that reveal internals (`PostgresUniqueViolation` bubbling out of
  `UserService.create`) — callers now depend on your database choice.

```go
// LEAKS: callers can now depend on the backing slice and mutate it.
func (s *Store) Items() []Item { return s.items }

// HIDES: callers get a snapshot; the representation is free to change.
func (s *Store) Items() []Item { return slices.Clone(s.items) }
```

---

## 5 · Pull complexity downward

When some complexity is unavoidable, **it is better for the module to absorb it than to
push it onto every caller.** A module has one implementer and many users. It's more
important for a module to have a simple interface than a simple implementation.

The most common violation is **configuration parameters**:

```python
# PUSHED UP: every caller must understand retry theory.
client = HttpClient(
    retry_count=3,
    backoff_base_ms=100,
    backoff_multiplier=2.0,
    jitter=True,
    retry_on_status={502, 503, 504},
)
```

Most callers have no idea what the right numbers are — they copy-paste from somewhere
else, and the "flexibility" becomes cargo cult. Before adding a parameter ask:

> *"Will callers be able to choose a better value than I can compute here?"*

Usually the module knows more than the caller does. It can observe latency, see which
status codes are retryable, and adapt. Provide **sensible defaults**, expose knobs only
for the rare caller who truly needs them:

```python
client = HttpClient()                 # right for 95% of callers
client = HttpClient(timeout=30)       # the one knob people genuinely need
```

**Don't take this too far.** Pulling complexity down is good when (a) the complexity is
closely related to the module's existing job, (b) it simplifies many callers, and (c) it
simplifies the interface. Pulling an unrelated concern into a module just to "hide" it
creates a god object.

---

## 6 · Different layer, different abstraction

In a well-designed system, each layer provides a **different abstraction** from the
layers above and below it. File system → blocks. Network stack → reliable byte streams
over unreliable packets. If two adjacent layers have *the same* abstraction, one of them
is probably not earning its keep.

### Pass-through methods

```python
class OrderController:
    def get_order(self, order_id):
        return self.service.get_order(order_id)

class OrderService:
    def get_order(self, order_id):
        return self.repository.get_order(order_id)

class OrderRepository:
    def get_order(self, order_id):
        return self.db.query(...)
```

Three layers, one idea. Each pass-through adds an interface without adding functionality.
This is the signature of **architecture chosen by template** ("every feature must have a
controller, service, and repository") rather than by need.

It's fine *if the layers eventually diverge* — the controller does HTTP concerns, the
service enforces business rules, the repository maps rows. It's not fine as ceremony.

**Fixes:** let the upper layer call the lower one directly; merge the layers; or push real
responsibility into the middle one.

### Pass-through variables

A value threaded through a long chain of functions that don't use it, only so the bottom
one can:

```
 main(cert) → run_server(cert) → handle(cert) → route(cert) → open_tls(cert)
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
              none of these care about cert
```

Options, in rough order of preference:

1. Store it in an object that the deep function already has access to (a `Server` struct
   field, a shared context object built once at startup).
2. Use a request-scoped context — Go's `context.Context` for *request-scoped* values like
   deadlines and trace ids (not for optional parameters in general).
3. A global. Last resort — it makes testing and concurrency harder.

### Decorators and wrappers

Decorators are useful, but a wrapper that forwards 20 methods to add behavior to 1 is
shallow. Before writing one, consider: can the feature go directly into the underlying
class? Into the caller? Into a separate, independent class?

---

## 7 · Define errors out of existence

Exception handling is one of the largest sources of complexity. Every thrown error is
an extra thing each caller must understand — and error paths are rarely tested, so they
are where bugs hide.

The instinct "throw lots of exceptions, it's defensive" is often wrong. **Throwing an
exception is easy; handling it is hard.** You're pushing the hard part onto the caller.

### Technique 1: redefine the semantics so the error cannot happen

**Python slicing** doesn't raise on out-of-range indices:

```python
s = "abc"
s[1:100]   # 'bc'  — clamps instead of raising
s[5:10]    # ''    — empty, not an error
```

Compare Java's `substring`, which throws `IndexOutOfBoundsException` and forces every
caller to clamp by hand. Python's semantics ("give me whatever overlaps this range") make
a whole category of error impossible.

**Go's zero values** do the same thing:

```go
var m map[string]int       // nil map
fmt.Println(m["missing"])  // 0     — reading a nil map is fine
fmt.Println(len(m))        // 0

var s []int                // nil slice
s = append(s, 1)           // works  — no need to initialize first

var mu sync.Mutex          // ready to use, no constructor
var buf bytes.Buffer       // ready to use, no constructor
```

Go proverb: **"Make the zero value useful."** (Note the one sharp edge: *writing* to a
nil map panics — which is why the map is the type Go programmers most often initialize
explicitly.)

**Idempotent operations:**

```python
os.makedirs(path, exist_ok=True)   # "ensure it exists", not "create it"
```

```go
os.MkdirAll(path, 0o755)           // returns nil if it already exists
```

"Delete this key" should succeed if the key is already gone. "Ensure this directory
exists" should succeed if it already does. The caller's actual *goal* is the end state,
not the transition.

**Unix `unlink` vs. old Windows delete.** On Windows, deleting a file that is open
historically failed with an error, so users hunted for the process holding it. Unix
removes the directory entry immediately and frees the data when the last handle closes.
No error case exists.

### Technique 2: mask exceptions at a low level

Handle the error inside the module so callers never see it. TCP retransmits lost packets;
the application sees a reliable stream. A retrying HTTP client retries a transient 503;
the caller sees success or a final failure.

### Technique 3: aggregate exceptions

Instead of handling errors at each of 40 call sites, let them propagate to **one place**
that handles them all uniformly:

```python
def handle_request(request):
    try:
        return dispatch(request)          # dozens of handlers inside
    except NotFound as e:
        return response(404, str(e))
    except InvalidInput as e:
        return response(400, str(e))
    # every handler just raises; none formats its own error response
```

### Technique 4: just crash

For errors that are extremely rare and impossible to meaningfully recover from — out of
memory, a corrupted internal invariant — handling them adds code no one will ever test.
Crash with a clear message. `panic` in Go is for exactly this (programmer errors,
impossible states), not for expected failures.

### The balance

Don't define away errors the caller genuinely needs to know about. A bank transfer
failing for insufficient funds is **business logic**, not a nuisance to be masked.
The question is always: *does the caller have something useful to do with this error?*
If yes, surface it clearly. If no, eliminate or absorb it.

```go
// Go: errors are values. Wrap to add context without losing the cause.
if err := db.Save(order); err != nil {
    return fmt.Errorf("save order %s: %w", order.ID, err)
}
// callers can still errors.Is(err, sql.ErrNoRows)
```

---

## 8 · Make illegal states unrepresentable

(Yaron Minsky's phrase.) Instead of writing code that *checks* for invalid combinations,
design data types in which invalid combinations **cannot be constructed.** The checks
disappear because there is nothing to check.

### Boolean soup

```python
# BAD: 2^3 = 8 possible combinations, only 4 are meaningful.
@dataclass
class Connection:
    is_connecting: bool
    is_connected: bool
    is_closed: bool
    error: str | None
```

What does `is_connected=True, is_closed=True, error="timeout"` mean? Nothing — but the
type allows it, so every function must defend against it.

```python
# GOOD: exactly the valid states exist.
class ConnState(Enum):
    CONNECTING = auto()
    CONNECTED = auto()
    CLOSED = auto()
    FAILED = auto()

@dataclass(frozen=True)
class Connection:
    state: ConnState
    error: str | None = None   # only meaningful when state is FAILED
```

Even better, when the fields differ per state, use a separate type per state:

```python
@dataclass(frozen=True)
class Connected:
    socket: Socket

@dataclass(frozen=True)
class Failed:
    error: str

ConnectionState = Connecting | Connected | Closed | Failed

match state:
    case Connected(socket=s): s.send(data)
    case Failed(error=e):     log(e)
```

Now `socket` only exists when connected, and `error` only exists when failed. Neither
can be accessed in the wrong state.

### Parse, don't validate

(Alexis King's phrase.) **Validation** checks data and throws the result of the check
away; **parsing** checks data and returns a *more precise type* that carries the proof.

```python
# VALIDATE: every function downstream wonders "was this checked?"
def send_welcome(email: str):
    if "@" not in email:          # checked again... and again... and again
        raise ValueError(email)
    ...

# PARSE: check once at the boundary, then the type is the proof.
@dataclass(frozen=True)
class Email:
    value: str

    @classmethod
    def parse(cls, raw: str) -> "Email":
        raw = raw.strip().lower()
        if "@" not in raw:
            raise ValueError(f"not an email: {raw!r}")
        return cls(raw)

def send_welcome(email: Email):   # cannot be called with an unchecked string
    ...
```

In Go, the same idea uses an unexported field so the value can only come from the
constructor:

```go
type Email struct{ value string }   // unexported: can't build one by hand outside the package

func ParseEmail(raw string) (Email, error) {
    raw = strings.ToLower(strings.TrimSpace(raw))
    if !strings.Contains(raw, "@") {
        return Email{}, fmt.Errorf("not an email: %q", raw)
    }
    return Email{value: raw}, nil
}
```

**Validate at the edges** (HTTP handlers, file readers, CLI args). Once data is inside
the core, trust the types.

### Primitive obsession

The general smell behind this: representing domain concepts as raw `str`, `int`, `float`.

```python
def transfer(from_id: int, to_id: int, amount: float): ...
transfer(500, 17, 42)       # which is which? is 500 dollars or an id?
```

`AccountId`, `Money` (in integer cents, never float), `Duration` instead of
`timeout_ms: int`. Go's `time.Duration` is a model here: `time.Sleep(5)` is 5
*nanoseconds*, which is why idiomatic code writes `5 * time.Second`.

---

## 9 · Functional core, imperative shell

(Gary Bernhardt's phrasing.) Most hard-to-test, hard-to-reason-about code mixes two
things in the same function: **decisions** (logic) and **effects** (I/O, time,
randomness, mutation of shared state).

Separate them:

```
 ┌───────────────────────────────────────────────┐
 │  IMPERATIVE SHELL  (thin, boring, few tests)  │
 │   read DB · call APIs · read clock · log      │
 │                                               │
 │     ┌──────────────────────────────────┐      │
 │     │  FUNCTIONAL CORE  (thick, pure)  │      │
 │     │  data in → decisions → data out  │      │
 │     │  no I/O, no clock, no globals    │      │
 │     └──────────────────────────────────┘      │
 │                                               │
 │   write DB · send emails · return response    │
 └───────────────────────────────────────────────┘
```

```python
# MIXED: can't test the pricing rule without a database and a real clock.
def checkout(cart_id):
    cart = db.load_cart(cart_id)
    total = sum(i.price * i.qty for i in cart.items)
    if datetime.now().weekday() == 4 and total > 10_000:   # Friday promo
        total = int(total * 0.9)
    db.save_invoice(cart_id, total)
    email.send(cart.owner, f"Total: {total}")

# SEPARATED
def price(items, today: date) -> int:          # pure: trivially testable
    total = sum(i.price * i.qty for i in items)
    if today.weekday() == 4 and total > 10_000:
        total = int(total * 0.9)
    return total

def checkout(cart_id):                          # shell: just wiring
    cart = db.load_cart(cart_id)
    total = price(cart.items, date.today())
    db.save_invoice(cart_id, total)
    email.send(cart.owner, f"Total: {total}")
```

Now `price` can be tested with a hundred cases in milliseconds, including "a Friday" —
without mocking anything. The shell is so thin it barely needs tests.

**Related habits:**

- **Pass time in, don't read it.** `now()` inside logic makes it untestable and
  non-deterministic.
- **Prefer returning new values to mutating arguments.** A function that mutates its
  input is a hidden output. (The DSA curriculum's "mutates input?" column exists for this
  reason.)
- **Avoid global mutable state.** Every global is an implicit parameter to every function
  in the program.

---

## 10 · Functions: size, shape, and flow

### Size: the honest answer

"Functions should be 5 lines" (Clean Code) and "prefer deep functions" (Ousterhout)
seem to conflict. They don't, once you ask the right question:

> **Split a function when the pieces are independently understandable.** Don't split
> it when you'd have to read the pieces together to understand either one.

Good split: a function that parses input, then computes a result, then formats output —
three separable concerns.

Bad split: a 40-line algorithm chopped into `_step1`, `_step2`, `_step3` that share six
variables through parameters. The reader now jumps between four places to follow one
idea. That's **conjoined methods** — a red flag.

### Do one thing at one level of abstraction

```python
# MIXED LEVELS: business intent and byte-level detail interleaved.
def register(user):
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", user.email):
        raise InvalidEmail(user.email)
    h = hashlib.pbkdf2_hmac("sha256", user.pw.encode(), salt, 600_000)
    conn.execute("INSERT INTO users VALUES (?, ?)", (user.email, h))
    smtp.sendmail(FROM, user.email, WELCOME_TEMPLATE.format(...))

# ONE LEVEL: reads like the requirement.
def register(user):
    email = Email.parse(user.email)
    account = Account(email, hash_password(user.pw))
    accounts.add(account)
    notifier.welcome(account)
```

### Guard clauses over nesting

```python
# ARROW CODE
def ship(order):
    if order is not None:
        if order.paid:
            if order.items:
                if order.address:
                    return carrier.ship(order)
                else:
                    raise NoAddress()
            else:
                raise EmptyOrder()
        else:
            raise Unpaid()
    else:
        raise NoOrder()

# GUARD CLAUSES: handle the exceptions first, then the main path is unindented.
def ship(order):
    if order is None:     raise NoOrder()
    if not order.paid:    raise Unpaid()
    if not order.items:   raise EmptyOrder()
    if not order.address: raise NoAddress()
    return carrier.ship(order)
```

Go makes this the dominant idiom — **the happy path runs down the left margin**:

```go
f, err := os.Open(path)
if err != nil {
    return fmt.Errorf("open config: %w", err)
}
defer f.Close()

cfg, err := parse(f)
if err != nil {
    return fmt.Errorf("parse config: %w", err)
}
return apply(cfg)
```

### Boolean flag parameters

```python
render(doc, True, False)        # what do these mean?
```

A boolean parameter usually means **the function does two different things.** Options:

- Split it: `render_preview(doc)` and `render_final(doc)`.
- Or at minimum make it keyword-only so the call site is readable:

```python
def render(doc, *, include_comments: bool = False): ...
render(doc, include_comments=True)
```

### Parameter count

Past three or four parameters, callers mix up the order and every change to the list
touches every call site. Group parameters that travel together into a type
(`Point(x, y)`, `DateRange(start, end)`) — often that type turns out to own behavior too.

### Side effects must be visible

A function named `check_password(user, pw)` that also *resets the session on failure*
is a trap. Either the name should say it (`authenticate_or_reset_session`) or the
side effect should move elsewhere. **Command–query separation:** a function either
*answers a question* or *changes state* — not both, where you can help it.

---

## 11 · Names

A name is a tiny interface comment. Good names make code obvious; bad ones create
obscurity.

### Precise over generic

| Vague | Precise |
|---|---|
| `data`, `info`, `obj`, `result`, `tmp` | `unpaid_invoices`, `retry_after` |
| `process()`, `handle()`, `manage()` | `charge_card()`, `expire_sessions()` |
| `count` | `num_active_users` vs. `num_login_attempts` |
| `flag` | `is_trial_expired` |
| `x` for a line index | `line_num` (but `x`/`y` for coordinates, `i` for a short loop index, are fine) |
| `timeout` | `timeout_seconds` — or better, a `Duration` type |

### Rules of thumb

- **Scope determines length.** A 3-line loop variable can be `i`. A package-level
  exported function needs a full, unambiguous name. Go leans hard into this: short
  names for short scopes (`r` for a reader in a 5-line function), descriptive names for
  wide scopes.
- **Be consistent.** If a concept is called `customer` in one place, don't call it
  `client`, `account`, and `user` elsewhere. One word per concept, one concept per word.
- **Don't encode the type** (`strName`, `listUsers`, `IUserService`). The type system
  already knows.
- **Don't stutter.** In Go, `http.HTTPServer` → `http.Server`. In Python,
  `user.user_name` → `user.name`.
- **Booleans read as assertions:** `is_ready`, `has_children`, `can_retry`.
- **Avoid negatives:** `if not is_disabled` is harder than `if is_enabled`.

### The name is a design test

> **If you struggle to find a precise name for something, the design is probably
> unclear.**

A function you can only call `do_stuff_and_update` is doing two things. A variable you
can only call `data2` is not a real concept. The difficulty naming is the symptom; fix
the design, and a good name usually appears on its own.

---

## 12 · Comments

"Good code is self-documenting" is half true. **Code tells you *what* and *how*.
It cannot tell you *why*, and it cannot tell you what the designer was thinking.**

### What comments are for

Comments should describe **things that aren't obvious from the code**:

| Kind | Purpose | Example |
|---|---|---|
| **Interface comment** | What a function/class does, for someone who will *use* it without reading its body. Inputs, outputs, side effects, errors, preconditions. | `"""Returns the user's active sessions, newest first. Never raises; returns [] if the user doesn't exist."""` |
| **Why comment** | A decision that looks wrong but isn't. | `# Sort before dedupe: the API returns duplicates non-adjacently.` |
| **Data structure comment** | What a field *means*, units, invariants. | `# Cents, never negative. Refunds are separate records.` |
| **Cross-module comment** | A dependency the code can't express. | `# If you change this format, also update scripts/migrate_v2.py.` |
| **Warning / TODO** | Known sharp edges. | `# Not thread-safe; callers must hold s.mu.` |

### What comments are NOT for

```python
i += 1          # increment i                        ← repeats the code
user = get()    # get the user                       ← repeats the name
# loop over items
for item in items:                                   ← says nothing new
```

If a comment just restates the code, delete it. If you feel a comment is needed to
explain *what* a block does, that block probably wants to be a well-named function.

### Write comments first

Write the interface comment **before** the implementation. This turns comments into a
design tool:

- If the comment is long and full of caveats, **the interface is too complex.**
- If you can't describe the function simply, you don't yet understand what it should do.
- Comments written afterwards tend to be skipped or perfunctory.

### Keep comments near the code they describe

Comments far from their code rot. Put them at the declaration, not in a separate design
document nobody updates. Commit messages are good for *why this change was made*, but
bad for *how this code works now* — they aren't visible when reading the code.

---

## 13 · Consistency and obviousness

### Consistency is leverage

Once a reader learns how one thing is done, they can predict everything else that's
done the same way. Inconsistency means every instance must be learned separately.

Be consistent in:

- naming (`get_` vs. `fetch_` vs. `load_` — pick one meaning for each),
- error handling (all functions return errors, or all raise — not a mix),
- file and package layout,
- the patterns used for the same problem (don't use three different retry helpers).

**Don't change an existing convention just because you prefer a new one.** A consistently
"okay" convention beats a codebase half-migrated to a "better" one. If you truly must
change it, change it everywhere.

Tools enforce the cheap parts so humans can focus on the expensive parts: `gofmt` and
`go vet`, `ruff format` / `ruff check`, type checkers (`mypy`, `pyright`), linters in CI.

### Obvious code

Code is **obvious** when a reader's first guess about it is right. Things that make code
non-obvious:

- **Event-driven / callback-heavy flow** — it's hard to see what runs when. Document
  when handlers are invoked.
- **Generic containers as return types** — `Tuple[int, int, str]` or `Pair<A,B>` hide
  meaning. Return a named type with named fields.
- **Declared type differs from actual type** — `items: list` that is actually always a
  `deque`.
- **Code that violates reader expectations** — a `__eq__` that mutates, a `get_` that
  performs network I/O, a constructor that starts a goroutine.
- **Cleverness.**

> "Debugging is twice as hard as writing the code in the first place. Therefore, if you
> write the code as cleverly as possible, you are, by definition, not smart enough to
> debug it." — Brian Kernighan

> **"Clear is better than clever."** — Go proverb

```python
# Clever
return [x for x in (y.strip() for y in s.split(",")) if x] or None

# Clear
parts = [p.strip() for p in s.split(",")]
non_empty = [p for p in parts if p]
return non_empty or None
```

---

## 14 · Duplication and abstraction

### DRY is about knowledge, not text

"Don't Repeat Yourself" (from *The Pragmatic Programmer*) is defined as: **every piece of
knowledge must have a single, unambiguous, authoritative representation.** It is about
*knowledge*, not *characters*.

Two functions that happen to contain the same five lines but represent **different
rules** are not duplication. Merging them couples two things that will change for
different reasons.

```python
def max_username_length():  return 32
def max_tag_length():        return 32
```

These are not "the same 32". One is a UI constraint, the other a database column.
Extracting `MAX_LENGTH = 32` would mean changing one silently changes the other.

### The wrong abstraction

> "Duplication is far cheaper than the wrong abstraction." — Sandi Metz

How it happens:

```
 1. Programmer A sees duplication, extracts a shared function.
 2. A new requirement is *almost* the same. Programmer B adds a parameter + an `if`.
 3. Repeat several times. The function now has 5 flags and 12 branches.
 4. Nobody understands it; everyone is afraid to touch it.
```

**The fix is to go backwards:** inline the abstraction back into every caller, delete the
branches each caller doesn't use, and look at what's actually left. Often a better
abstraction appears — or none is needed.

### Rule of three

A practical heuristic: tolerate the first duplicate. On the **third** occurrence, you have
enough examples to see what actually varies, and can extract a correct abstraction instead
of a guessed one.

### "A little copying is better than a little dependency"

(Go proverb.) Pulling in a library — or a shared internal package — to avoid writing ten
lines couples your build, your upgrades, and your security surface to someone else's
decisions. Copy the ten lines.

### YAGNI and speculative generality

Designing for requirements you imagine you'll have is the mirror-image failure of
tactical programming. Abstract base classes with one implementation, plugin systems with
one plugin, config options nobody sets — all cost interface and give nothing.

The resolution with §3's "be somewhat general-purpose": make the **interface** general
enough that it isn't tied to one caller's specifics, but **don't build machinery** for
use cases that don't exist yet.

---

## 15 · Design it twice

Your first idea for an interface is rarely the best one — it's just the first one.

Before committing to a significant design, **sketch at least two radically different
alternatives** (not two variations of the same idea) and compare them:

| Question | Design A | Design B |
|---|---|---|
| How simple is the interface for the common case? | | |
| How general-purpose is it? | | |
| How much does the caller need to know? | | |
| What happens when requirement X changes? | | |
| Can it be implemented efficiently? | | |

Example — a text editor's buffer:

- **A:** line-oriented — `get_line(n)`, `set_line(n, text)`, `insert_line(n, text)`.
- **B:** character-range-oriented — `insert(pos, text)`, `delete(start, end)`.
- **C:** user-action-oriented — `backspace()`, `delete_selection()`, `paste()`.

C is shallow and has to grow a method per UI action. A makes cross-line edits awkward.
B is general and small; the UI builds its actions on top. You only see that by comparing.

This costs an hour and routinely saves weeks. It is also exactly what a system design
interview asks you to do out loud.

---

## 16 · A worked refactor, start to finish

A realistic tactical function. Read it and try to list what's wrong before reading on.

```python
def process(data, flag=False, flag2=False):
    res = []
    for d in data:
        if d["type"] == 1:
            if d["amt"] > 0:
                if flag:
                    x = d["amt"] * 1.2
                else:
                    x = d["amt"]
                if flag2:
                    print("LOG:", d["id"], x)
                res.append({"id": d["id"], "val": x})
        elif d["type"] == 2:
            if d["amt"] > 0:
                x = d["amt"] * 0.5
                if flag2:
                    print("LOG:", d["id"], x)
                res.append({"id": d["id"], "val": x})
    return res
```

### Diagnosis

| # | Problem | Section |
|---|---|---|
| 1 | Name `process` / `data` / `res` / `x` says nothing. | §11 |
| 2 | Two boolean flags → really 4 functions in one. | §10 |
| 3 | Magic numbers `1`, `2`, `1.2`, `0.5`. | §11, §13 |
| 4 | Raw dicts with string keys: typos fail at runtime, no IDE help. | §8 |
| 5 | Logging (an effect) mixed into a calculation. | §9 |
| 6 | Money as `float`. | §8 |
| 7 | Filtering `amt > 0` duplicated per branch. | §14 |
| 8 | Unknown `type` is silently dropped — an unknown unknown. | §1, §7 |
| 9 | Nested ifs 4 deep. | §10 |

### After

```python
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class LineKind(Enum):
    PRODUCT = 1
    SERVICE = 2


VAT_RATE = Decimal("0.20")          # applied to products when tax is included
SERVICE_DISCOUNT = Decimal("0.50")  # services are billed at half rate


@dataclass(frozen=True)
class LineItem:
    id: str
    kind: LineKind
    amount: Decimal


@dataclass(frozen=True)
class BilledLine:
    id: str
    amount: Decimal


def bill(items: list[LineItem], *, include_vat: bool) -> list[BilledLine]:
    """Returns the billable amount for each positive line item.

    Zero and negative amounts are skipped. Products gain VAT when include_vat is
    True; services are always billed at SERVICE_DISCOUNT of their amount.
    """
    return [
        BilledLine(item.id, _billed_amount(item, include_vat))
        for item in items
        if item.amount > 0
    ]


def _billed_amount(item: LineItem, include_vat: bool) -> Decimal:
    match item.kind:
        case LineKind.PRODUCT:
            return item.amount * (1 + VAT_RATE) if include_vat else item.amount
        case LineKind.SERVICE:
            return item.amount * SERVICE_DISCOUNT
    raise AssertionError(f"unhandled line kind: {item.kind}")
```

And the shell, where logging and parsing live:

```python
def bill_order(raw_rows, include_vat, log):
    items = [parse_line_item(r) for r in raw_rows]   # raises on unknown kind: loud, at the edge
    billed = bill(items, include_vat=include_vat)
    for line in billed:
        log.debug("billed %s: %s", line.id, line.amount)
    return billed
```

What changed, and why it matters:

- **The core is pure.** `bill` can be tested exhaustively without capturing stdout.
- **Unknown kinds fail loudly at the boundary** (`parse_line_item` → `LineKind(raw["type"])`
  raises `ValueError`), instead of vanishing silently from the output.
- **The `flag2` logging switch disappeared** — it's the caller's logger's level now,
  which is where that decision belongs.
- **The remaining flag is keyword-only**, so every call site reads
  `bill(items, include_vat=True)`.
- **The interface comment** states the non-obvious rules (negative amounts skipped),
  which a reader could otherwise only learn by reading the body.

The same idea in Go:

```go
type LineKind int

const (
	Product LineKind = iota + 1
	Service
)

type LineItem struct {
	ID          string
	Kind        LineKind
	AmountCents int64
}

type BilledLine struct {
	ID          string
	AmountCents int64
}

// Bill returns the billable amount for each positive line item.
// Products gain 20% VAT when includeVAT is true; services are billed at half.
func Bill(items []LineItem, includeVAT bool) ([]BilledLine, error) {
	out := make([]BilledLine, 0, len(items))
	for _, it := range items {
		if it.AmountCents <= 0 {
			continue
		}
		amount, err := billedAmount(it, includeVAT)
		if err != nil {
			return nil, err
		}
		out = append(out, BilledLine{ID: it.ID, AmountCents: amount})
	}
	return out, nil
}

func billedAmount(it LineItem, includeVAT bool) (int64, error) {
	switch it.Kind {
	case Product:
		if includeVAT {
			return it.AmountCents * 120 / 100, nil
		}
		return it.AmountCents, nil
	case Service:
		return it.AmountCents / 2, nil
	default:
		return 0, fmt.Errorf("line %s: unknown kind %d", it.ID, it.Kind)
	}
}
```

(Integer cents with integer division truncates fractions of a cent. A real billing
system states its rounding rule explicitly — that rule is itself a design decision that
belongs in exactly one place.)

---

## 17 · When principles collide

Principles are heuristics, and they conflict. Knowing *which one wins when* is the
difference between a senior engineer and someone who has memorized a list.

| Tension | Resolve by asking |
|---|---|
| **DRY vs. low coupling** | Is this the same *knowledge*, or the same *text*? Only merge shared knowledge. |
| **Small functions vs. deep modules** | Can each piece be understood alone? If not, keep it together. |
| **General-purpose vs. YAGNI** | Generalize the *interface* (cheap); don't build *machinery* for imagined cases (expensive). |
| **Flexibility (config) vs. simplicity** | Can the caller pick a better value than the module can? Usually no → default it. |
| **Defensive errors vs. defining errors away** | Does the caller have something useful to do with the error? |
| **Abstraction vs. obviousness** | Does the layer provide a *different* abstraction, or just forward? |
| **Consistency vs. improvement** | Can you change it everywhere? If not, stay consistent. |
| **Performance vs. clarity** | Have you *measured* that it matters? Clean designs are usually fast enough, and are easier to optimize in the one place that's hot. |

> "A complex system that works is invariably found to have evolved from a simple system
> that worked." — John Gall

### The named principles, and where each is treated

Reviewers and interviewers use these names as shorthand. Each is a rule for one kind of
complexity, and each is worked in full somewhere in this track — this table is the index.

| Principle | The rule | The failure it prevents | Where |
|---|---|---|---|
| **DRY** | Every piece of *knowledge* has one authoritative home | A bug fixed in one of N copies while the others keep it | §14 |
| **KISS** | Prefer the simplest design that meets the actual requirement | Cleverness only its author can safely change: bus-factor risk, slow onboarding | §13 |
| **YAGNI** | Don't build for a requirement you don't have yet | Speculative knobs, plugin points, and layers that must still be maintained and explained | §14 |
| **Separation of concerns** | Each part addresses one concern (I/O, rules, presentation) | Rule bugs that only show up with a particular UI or database, because the layers were never independent | §9; `08` §1, §3 |
| **Single level of abstraction** | A function's body reads at one conceptual level | Readers context-switching between "what" and "how" line by line | §10 |
| **Encapsulation / information hiding** | Expose behaviour, hide representation | Callers depending on internals that can then never change | §4; `02` §3 |
| **Law of Demeter** | Talk to your immediate collaborators, not through them | `a.b().c().d()` chains that break when something deep inside moves | `02` §9 |
| **Composition over inheritance** | Assemble behaviour from small parts | Fragile base classes, diamonds, N×M class explosions | `02` §4 |
| **Least astonishment** | An <abbr title="Application Programming Interface">API</abbr> behaves as its name and shape suggest | A `save()` that also sends an email; callers stop reading docs and guess | `03` §9 |
| **Postel's law** | Liberal in what you accept, conservative in what you send | Producers and consumers that break on harmless variation — but over-applied it silently accepts corrupt input, so pair it with validation and versioning | `03` §7; `09` §4 |
| **Fail fast vs. defensive** | Fail fast on programmer errors and broken internal invariants, near the source; be defensive with untrusted external input | Corrupt state surfacing far from its cause (too defensive) or a system brittle to any input variance (too strict) | `06` §10–§11; `12` §1 |
| **Immutability by default** | Make values unchangeable after construction; make mutation explicit | Action at a distance and races on shared mutable state | `07` §6; `02` §7 |
| **SOLID** | SRP, OCP, LSP, ISP, DIP | See the table in `02` §12 | `02` §12 |

### On performance specifically

Simple code is usually *easier* to make fast, because the hot path is isolated and
visible. Complicated code tends to be slow in ways nobody can find. The workflow:

1. Write the clean design.
2. **Measure** (profile, don't guess — this repo's DSA files show repeatedly that
   intuition about what's fast in CPython is often wrong).
3. Optimize the one critical path, keep the rest clean, and hide the optimized
   implementation behind the same simple interface.

---

## 18 · Red flags — the master table

If you see one of these in your code (or in code review), stop and reconsider the design.

| Red flag | What it signals |
|---|---|
| **Shallow module** | Interface isn't much simpler than implementation. |
| **Information leakage** | One design decision is reflected in multiple modules. |
| **Temporal decomposition** | Code is structured by execution order, not by knowledge. |
| **Overexposure** | Callers must learn rarely-used features to use common ones. |
| **Pass-through method** | A method does little except call another with the same signature. |
| **Repetition** | The same non-trivial code appears again and again. |
| **Special-general mixture** | General-purpose code contains special cases for particular callers. |
| **Conjoined methods** | You can't understand one method without reading another. |
| **Comment repeats code** | The comment adds nothing the code doesn't already say. |
| **Implementation docs contaminate interface** | Interface comment describes internals the user doesn't need. |
| **Vague name** | The name is too imprecise to convey useful information. |
| **Hard to pick name** | You can't find a simple, precise name → the design is muddled. |
| **Hard to describe** | The interface comment needs to be long and full of caveats. |
| **Non-obvious code** | Behavior or meaning can't be understood with a quick read. |
| **Boolean parameter** | Function is likely doing two things. |
| **Boolean soup** | Several flags whose combinations include invalid states. |
| **Primitive obsession** | Domain concepts are raw strings/ints/floats. |
| **Hidden side effect** | A query-sounding function changes state. |
| **Logic reads the clock / globals** | Non-deterministic, hard to test. |
| **Silent fallthrough** | Unknown input is dropped instead of rejected. |
| **Swallowed exception** | `except: pass` / `_ = err` — failures become unknown unknowns. |
| **Arrow code** | Deep nesting where guard clauses would flatten it. |
| **Flag-accreting shared function** | A "wrong abstraction" in progress. |

(The first 14 are Ousterhout's list; the rest are the most common additions.)

---

## 19 · How this shows up in interviews

### In a coding interview

Interviewers at Google and similar companies grade **code quality** as a distinct signal,
alongside correctness and complexity analysis. Cheap, visible wins:

- **Name things precisely,** even under time pressure. `left`, `right`, `window_sum` —
  not `a`, `b`, `s`.
- **Extract a helper when it names an idea** (`is_valid(r, c)`, `neighbors(node)`),
  not to hit a line count.
- **Guard clauses** for edge cases at the top: empty input, `k == 0`, single element.
- **No magic numbers** — `DIRECTIONS = [(0,1),(1,0),(0,-1),(-1,0)]`.
- **Don't mutate the input** unless you say so out loud and the problem allows it.
- **State the interface before coding:** "This function takes X, returns Y, and returns
  -1 if not found." That's §12's "write the comment first," spoken.

### In a system design interview

- **Design it twice** (§15) *is* the interview: present two options, compare, choose.
- **Deep modules** at service level: a small, stable <abbr title="Application Programming Interface">API</abbr> hiding a lot of complexity.
- **Information hiding:** "Clients don't know which database we use; the storage service
  owns that decision so we can change it."
- **Pull complexity downward:** the rate limiter is a shared component, not something
  every service re-implements.

### Behavioral / "tell me about code you're proud of"

Talk about a design decision in terms of **complexity removed**: which change got
cheaper, which class of bug became impossible, which errors were defined out of
existence. That framing signals senior thinking far more than naming a pattern does.

### Talk tracks worth having ready

- *"What makes code good?"* → "It's easy to change correctly. Concretely: deep modules
  with small interfaces, information hidden so decisions change in one place, and
  obvious code — a reader's first guess is right."
- *"How do you reduce complexity?"* → the two causes (dependencies, obscurity) and a
  technique against each.
- *"DRY — always?"* → knowledge vs. text; wrong abstraction; rule of three.
- *"Small functions — always?"* → split when independently understandable; depth beats
  size.

---

## 20 · The checklist

Before you open a PR (or say "done" in an interview), run through this:

**Interface**
- [ ] Can I describe what this module does in one or two sentences?
- [ ] Is the common case trivial to call, with good defaults?
- [ ] Does the interface expose any decision the caller shouldn't need to know?
- [ ] Are there boolean flags that should be separate functions or keyword-only?

**Structure**
- [ ] Is each piece of knowledge (format, rule, constant) in exactly one place?
- [ ] Are logic and I/O separated?
- [ ] Do adjacent layers provide different abstractions?
- [ ] Can invalid states be constructed? Can the types prevent it?

**Errors**
- [ ] Can any error case be defined away (idempotent, clamping, zero values)?
- [ ] Are unknown inputs rejected loudly rather than dropped silently?
- [ ] Is every surfaced error something the caller can act on?
- [ ] Are errors wrapped with context (`%w`, `raise ... from e`)?

**Readability**
- [ ] Would a new teammate's first guess about each name be right?
- [ ] Is the happy path unindented?
- [ ] Do comments explain *why* and *what for the user*, not *what the code does*?
- [ ] Is anything clever that could be plain instead?

**Change**
- [ ] If the most likely next requirement arrives, how many files change?
- [ ] Did I leave the surrounding code a little better — in a separate commit?

---

## 21 · Further reading

| Book / essay | Why read it |
|---|---|
| John Ousterhout — *A Philosophy of Software Design* (2nd ed.) | The source of most of this file. Short. Read it twice. |
| Robert C. Martin — *Clean Code* | Naming, functions, and formatting advice. Read critically: some advice (very small functions) is contested — see Ousterhout's chapter comparing the two. |
| Martin Fowler — *Refactoring* (2nd ed.) | The catalog of smells and the mechanical, safe steps to fix each. |
| Hunt & Thomas — *The Pragmatic Programmer* | The original DRY, orthogonality, tracer bullets, broken windows. |
| Sandi Metz — "The Wrong Abstraction" (blog post) | The definitive essay on when *not* to be DRY. |
| Alexis King — "Parse, don't validate" (blog post) | §8 in depth. |
| Gary Bernhardt — "Boundaries" (talk) | Functional core, imperative shell (§9). |
| Rob Pike — "Go Proverbs" (talk) | Short, sharp design heuristics, most of which apply beyond Go. |
| Rich Hickey — "Simple Made Easy" (talk) | The distinction between *simple* (not entangled) and *easy* (familiar). |

> "Any fool can write code that a computer can understand. Good programmers write code
> that humans can understand." — Martin Fowler
