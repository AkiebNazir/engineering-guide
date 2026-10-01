# Advanced: Property-Based and Mutation Testing

Hand-written tests only check the cases you thought of, and the bugs that reach production
are usually the ones you didn't. This chapter covers two techniques that attack that blind
spot from opposite sides. **Property-based testing** and **fuzzing** generate the inputs for
you and hunt for a counterexample. **Mutation testing** plants bugs in your code and checks
whether your tests notice, which measures how strong the suite really is. All the examples
below were run, and the failures shown are the tools' real output.

## Foundations — How can a computer write test cases for me?

### From examples to properties

An example-based test states one input and one expected output:

```python
assert encode("aaab") == [("a", 3), ("b", 1)]
```

It proves the code is right for `"aaab"`. It says nothing about `""`, `"🙂🙂"`, a
100,000-character string, or `"a\x00a"`. You could add those by hand, but you would only add the
ones you thought of.

A **property** is a statement that must hold for **every** valid input:

- "Decoding what I encoded gives back the original string."
- "A sorted list has the same elements as the input, in non-decreasing order."
- "Adding an item to the cart never decreases the total."

A **property-based testing (PBT)** library generates hundreds of inputs, often nasty ones
(empty values, huge numbers, unusual Unicode, duplicates), runs the property on each, and if
one fails it **shrinks** the input to the smallest example that still fails, so you debug
`[0, -1]` rather than a list of 312 random integers. The idea comes from Haskell's
**QuickCheck** (Claessen and Hughes, 2000). In Python the standard library is **Hypothesis**; in
Go it is native fuzzing plus the `rapid` library; Java has jqwik; JavaScript has fast-check.

### From "did it run?" to "would it catch a bug?"

Coverage ([The Testing Pyramid and Unit Tests](01_testing_pyramid.md) §7) says which lines ran during the tests, not whether any
test would **fail** if those lines were wrong. **Mutation testing** answers that directly: it
makes a small change to the code (a **mutant**, e.g. `>=` to `>`), runs the tests, and checks
that at least one test fails. A mutant that no test notices marks a behaviour your tests do not
really pin down.

| Technique | Question it answers | Generates | Cost |
|---|---|---|---|
| Example-based tests | Does it work for these cases? | Nothing | Cheap |
| Property-based tests | Does this rule hold for all inputs? | Inputs | Seconds per property |
| Coverage-guided fuzzing | Can any input crash it or break an invariant? | Inputs, steered by coverage | Minutes to days, continuously |
| Mutation testing | Would my tests catch a bug here? | Buggy versions of the code | Runs the suite once per mutant |

## 1. Property-based testing with Hypothesis

```python
# rle.py — run-length encoding: "aaab" <-> [("a", 3), ("b", 1)]
from itertools import groupby


def encode(s: str) -> list[tuple[str, int]]:
    return [(ch, len(list(run))) for ch, run in groupby(s)]


def decode(pairs: list[tuple[str, int]]) -> str:
    return "".join(ch * n for ch, n in pairs)
```

```python
# test_rle.py
from hypothesis import given, strategies as st

from rle import decode, encode


def test_example():
    assert encode("aaab") == [("a", 3), ("b", 1)]


@given(st.text())
def test_decode_inverts_encode(s):                 # round-trip property
    assert decode(encode(s)) == s


@given(st.text())
def test_runs_are_maximal(s):                      # invariant: neighbours differ, counts > 0
    pairs = encode(s)
    assert all(n > 0 for _, n in pairs)
    assert all(a != b for (a, _), (b, _) in zip(pairs, pairs[1:]))
```

`@given` turns the test into a loop over generated values: by default up to 100 examples per
test (`max_examples`), each with a 200 ms deadline. The **strategies** in `st` describe the input
space and compose:

| Strategy | Generates |
|---|---|
| `st.integers(min_value=0)`, `st.floats(allow_nan=False)`, `st.text()`, `st.binary()` | Primitives, including edge values (0, -1, huge, empty, unusual Unicode) |
| `st.lists(x, min_size=1, unique=True)`, `st.dictionaries(k, v)`, `st.tuples(a, b)` | Collections |
| `st.one_of(a, b)`, `a \| b`, `st.sampled_from(["USD", "EUR"])`, `st.none()` | Choices |
| `st.builds(Order, total=st.integers(0, 10**6))`, `st.from_type(Order)` | Your own objects, from constructors or type hints |
| `st.composite` | A function that draws values step by step, where later draws depend on earlier ones |
| `x.map(f)`, `x.filter(pred)`, `assume(cond)` | Transform or constrain; prefer building valid data over filtering lots of it out |

### The sort example, done properly

```python
# test_sort.py — properties of a sort, checked against thousands of generated lists
from collections import Counter

from hypothesis import given, strategies as st


def my_sort(xs):
    return sorted(xs)


@given(st.lists(st.integers()))
def test_sort_properties(xs):
    result = my_sort(xs)
    assert len(result) == len(xs)                                   # nothing lost or added
    assert all(result[i] <= result[i + 1] for i in range(len(result) - 1))   # ordered
    assert Counter(result) == Counter(xs)                           # a permutation of the input
    assert my_sort(result) == result                                # idempotent
```

Length plus "ordered" is not enough: a function that returns `[0] * len(xs)` passes both. The
permutation check is what pins down a sort. (A correction to a common claim: `st.integers()`
never produces NaN; NaN and infinities come from `st.floats()`, which generates them by default
unless you pass `allow_nan=False` / `allow_infinity=False`.)

### Watching it find a real bug

```python
# test_bug.py — Hypothesis finds and shrinks a real bug
from hypothesis import given, strategies as st


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


@given(st.lists(st.floats(allow_nan=False, allow_infinity=False), min_size=1))
def test_mean_is_between_min_and_max(xs):
    assert min(xs) <= mean(xs) <= max(xs)
```

The property looks obviously true. Hypothesis 6.168 disagreed within about a second (output
trimmed):

```text
E       assert 5.614496838258927e+16 <= 5.614496838258926e+16
E       Failing test case: test_mean_is_between_min_and_max(
E           xs=[5.6144968382589256e+16, 5.614496838258926e+16, 5.614496838258926e+16],
E       )
```

Floating-point rounding in `sum` makes the mean of three nearly identical values larger than all
of them. Inputs near `1.7e308` overflow `sum` to infinity as well. Either the property needs a
tolerance, or `mean` needs `math.fsum` or `statistics.fmean`. That is the typical Hypothesis find:
a rule you believed, broken by an input you would never have typed.

### How shrinking and the example database work

```arch
%% caption: Hypothesis generates inputs, and on the first failure it shrinks to a minimal counterexample, saves it, and replays it first on every later run.
grid 170x105
node gen "Generate input" at 0,0 shape=card icon=idea sub="from strategies"
node run "Run property" at 1,0 shape=card icon=code sub="your assertions"
node ok "Passes" at 2,0 shape=card icon=check color=green sub="next of max_examples"
node shrink "Shrink" at 1,1 shape=card icon=filter color=amber sub="smaller, still failing"
node db "Example database" at 0,1 shape=card icon=db sub=".hypothesis/"
node report "Report minimal case" at 1,2 shape=card icon=error color=red sub="plus reproduce hint"
gen -> run
run -> ok : "pass"
ok:T -> gen:T : "again"
run -> shrink : "fail"
shrink -> report
shrink -> db : "save"
db -> gen : "replay first"
```

Hypothesis records every random choice it makes (the **choice sequence**) and shrinks by making
that sequence shorter and simpler, so shrinking works for any strategy, including your composite
ones, without a hand-written shrinker (a notable improvement over classic QuickCheck). Failing
examples are saved under `.hypothesis/examples` and replayed first on the next run, so a failure
doesn't disappear on rerun. In CI, where that directory is usually not preserved, use `@example(...)`
to pin important cases, and consider `derandomize=True` or a shared database for reproducibility.

```python
from hypothesis import settings

settings.register_profile("ci", max_examples=1000, deadline=None)   # dig harder in CI
settings.register_profile("dev", max_examples=50)                    # stay fast locally
# select with:  pytest --hypothesis-profile=ci
```

### Which properties to look for

Finding properties is the real skill. These patterns cover most code:

| Pattern | Example |
|---|---|
| **Round-trip** (inverse) | `decode(encode(x)) == x`; `json.loads(json.dumps(x)) == x`; parse/print |
| **Invariant** | Output sorted; balance never negative; tree stays balanced; no duplicate IDs |
| **Oracle / reference model** | Fast implementation equals a slow obvious one (`my_sort(xs) == sorted(xs)`); new service equals old one |
| **Idempotence** | `normalise(normalise(x)) == normalise(x)`; applying a migration twice |
| **Metamorphic** | Related inputs, related outputs: adding a filter never returns *more* search results; doubling prices doubles the total |
| **Commutativity / order independence** | Merging CRDT states in any order gives the same result; applying events in any order where the domain promises it |
| **"Doesn't crash"** | Any input either parses or raises your documented error, never `KeyError` |

Avoid restating the implementation in the test ("the discount is `total * 0.2` when ..."). That
checks the code equals itself.

## 2. Stateful property testing

Many bugs only appear after a particular **sequence** of operations. Hypothesis's
`RuleBasedStateMachine` generates random sequences of calls, checks each against a simple
**model**, and shrinks a failing sequence to the shortest one.

```python
# lru.py — a small LRU cache with a deliberate bug: get() does not refresh recency
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int):
        self.capacity, self.data = capacity, OrderedDict()

    def get(self, key):
        return self.data.get(key)          # BUG: should move_to_end(key) on a hit

    def put(self, key, value):
        self.data[key] = value
        self.data.move_to_end(key)
        if len(self.data) > self.capacity:
            self.data.popitem(last=False)  # evict the least recently used
```

```python
# test_lru_stateful.py — Hypothesis generates sequences of operations and compares with a model
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from lru import LRUCache

KEYS = st.integers(min_value=0, max_value=4)     # few keys, so hits and evictions happen


class LRUMachine(RuleBasedStateMachine):
    def __init__(self):
        super().__init__()
        self.cache = LRUCache(capacity=2)
        self.model: list[tuple[int, int]] = []    # the obviously-correct model: oldest first

    @rule(key=KEYS, value=st.integers())
    def put(self, key, value):
        self.cache.put(key, value)
        self.model = [(k, v) for k, v in self.model if k != key] + [(key, value)]
        self.model = self.model[-2:]

    @rule(key=KEYS)
    def get(self, key):
        expected = dict(self.model).get(key)
        assert self.cache.get(key) == expected
        if expected is not None:                  # a hit makes the key most recently used
            self.model = [(k, v) for k, v in self.model if k != key] + [(key, expected)]

    @invariant()
    def never_over_capacity(self):
        assert len(self.cache.data) <= 2


TestLRU = LRUMachine.TestCase
```

Hypothesis's shrunk counterexample (invariant checks between steps removed):

```text
state = LRUMachine()
state.put(key=0, value=0)
state.put(key=2, value=0)
state.get(key=0)          # should make 0 the most recently used...
state.put(key=1, value=0) # ...so this should evict 2, but the cache evicts 0
state.get(key=0)          # AssertionError: None == 0
```

Five steps, each necessary. Finding that by hand means thinking of exactly this sequence. The
same technique tests databases, queues, file systems and distributed protocols (with a model of
the expected state), and is close to how Jepsen-style tools check histories for consistency
violations.

## 3. Fuzzing: property testing guided by coverage

**Fuzzing** feeds a program a huge number of generated inputs looking for crashes, hangs, and
sanitizer reports (memory errors, undefined behaviour). Modern fuzzers are **coverage-guided**:
they instrument the code, keep inputs that reach new branches in a **corpus**, and mutate those
inputs further. That lets them get deep into parsers and protocol handlers that purely random
input never reaches.

| | Property-based testing | Coverage-guided fuzzing |
|---|---|---|
| Input generation | From typed strategies, structure-aware | Mutates bytes from a corpus, steered by new coverage |
| Typical run | Seconds, in every test run | Minutes in CI, days on dedicated infrastructure |
| Oracle | Your properties | Crashes, sanitizers, plus any assertions you add |
| Best at | Logic and data-structure invariants | Parsers, decoders, file formats, anything taking untrusted bytes |
| Tools | Hypothesis, QuickCheck, jqwik, fast-check, rapid | libFuzzer, AFL++, Go native fuzzing, Atheris (Python), Jazzer (JVM), cargo-fuzz |

Google's **OSS-Fuzz** (launched 2016) runs continuous fuzzing for over a thousand open-source
projects and has reported tens of thousands of bugs, many of them security vulnerabilities. Fuzzing
is the standard way to test code that parses untrusted input.

## 4. Fuzzing in Go

Go has had native, coverage-guided fuzzing since Go 1.18. A fuzz target is a `FuzzXxx(f
*testing.F)` function in a `_test.go` file:

```go
// rle.go
package rle

import (
	"strconv"
	"strings"
)

// Encode turns "aaab" into "3a1b".
func Encode(s string) string {
	var b strings.Builder
	r := []rune(s)
	for i := 0; i < len(r); {
		j := i
		for j < len(r) && r[j] == r[i] {
			j++
		}
		b.WriteString(strconv.Itoa(j - i))
		b.WriteRune(r[i])
		i = j
	}
	return b.String()
}

// Decode turns "3a1b" back into "aaab".
func Decode(s string) string {
	var b strings.Builder
	n := 0
	for _, c := range s {
		if c >= '0' && c <= '9' {
			n = n*10 + int(c-'0')
			continue
		}
		b.WriteString(strings.Repeat(string(c), n))
		n = 0
	}
	return b.String()
}
```

```go
// rle_test.go
package rle

import (
	"testing"
	"unicode/utf8"
)

func FuzzRoundTrip(f *testing.F) {
	for _, seed := range []string{"", "a", "aaab", "héllo"} {
		f.Add(seed) // seed corpus; also run as ordinary tests by plain `go test`
	}
	f.Fuzz(func(t *testing.T, s string) {
		if !utf8.ValidString(s) {
			t.Skip() // the encoding is defined on text only
		}
		if got := Decode(Encode(s)); got != s {
			t.Errorf("Decode(Encode(%q)) = %q", s, got)
		}
	})
}
```

The seed cases pass under plain `go test`. Running the fuzzer (Go 1.24) found a bug in well under a
second:

```text
$ go test -fuzz=FuzzRoundTrip -fuzztime=20s
fuzz: elapsed: 0s, gathering baseline coverage: 4/4 completed, now fuzzing with 4 workers
--- FAIL: FuzzRoundTrip (0.02s)
        rle_test.go:17: Decode(Encode("0")) = ""
    Failing input written to testdata/fuzz/FuzzRoundTrip/771e938e4458e983
    To re-run:
    go test -run=FuzzRoundTrip/771e938e4458e983
```

`Encode("0")` is `"10"`, which `Decode` reads as "ten of nothing". The format is ambiguous for
input containing digits, a design bug no example test here would have caught. The failing input is
saved under `testdata/fuzz/`; **commit it**, and it becomes a permanent regression test that plain
`go test` runs.

Go fuzzing facts worth knowing: fuzz arguments may be `string`, `[]byte`, integer and float types,
`bool`, `rune` and `byte`; only one target can be fuzzed per `go test -fuzz` invocation; the
generated corpus is cached in `$GOCACHE/fuzz`. For structured property tests (random structs,
state machines with shrinking) Go developers use `pgregory.net/rapid`; the old `testing/quick`
package is frozen.

## 5. Mutation testing

### How it works

```arch
%% caption: Mutation testing: for each small change to the code, run the tests; a mutant that no test notices is a gap in the suite.
grid 170x90
node src "Source code" at 1,0 shape=card icon=code sub="discount_cents()"
node mutate "Mutate" at 1,1 shape=card icon=edit color=amber sub=">= becomes >"
node tests "Run test suite" at 1,2 shape=card icon=check sub="against the mutant"
node killed "Killed" at 0,3 shape=card icon=check color=green sub="a test failed: good"
node survived "Survived" at 2,3 shape=card icon=warn color=red sub="no test noticed"
node score "Mutation score" at 1,4 shape=card icon=gauge sub="killed / valid mutants"
src -> mutate -> tests
tests -> killed : "fails"
tests -> survived : "passes"
killed -> score
survived -> score
```

1. The tool parses the code and applies **mutation operators** one at a time: flip a comparison
   (`>=` to `>`), change a constant (`5000` to `5001`), swap an operator (`+` to `-`, `//` to `/`),
   negate a condition, replace a return value with `None`, delete a statement.
2. For each mutant it runs the tests that cover the mutated line.
3. If a test **fails**, the mutant is **killed**. If all tests **pass**, the mutant **survived**:
   the suite would not have noticed that bug.
4. **Mutation score** = killed / (total − equivalent). Timeouts (the mutant loops forever) count as
   killed.

The theory behind it (DeMillo, Lipton and Sayward, 1978): programmers write code that is *nearly*
right (**competent programmer hypothesis**), and tests that catch simple faults also tend to
catch complex ones built from them (**coupling effect**).

### A real run with mutmut

```python
# src/shop/pricing.py
def discount_cents(total_cents: int, vip: bool) -> int:
    """VIPs get 20% off carts of 5000 cents or more."""
    if vip and total_cents >= 5000:
        return total_cents * 20 // 100
    return 0
```

```python
# tests/test_pricing.py (first version)
from shop.pricing import discount_cents


def test_vip_big_cart():
    assert discount_cents(10_000, vip=True) == 2_000


def test_regular_customer():
    assert discount_cents(10_000, vip=False) == 0
```

These two tests give 100% line and branch coverage. mutmut 3.8 generated 8 mutants and **3
survived** (`mutmut results`, then `mutmut show <name>`):

```diff
-    if vip and total_cents >= 5000:
+    if vip and total_cents > 5000:
-    if vip and total_cents >= 5000:
+    if vip and total_cents >= 5001:
-        return total_cents * 20 // 100
+        return total_cents * 20 / 100
```

Each survivor names a missing test: nothing checks the threshold boundary, and nothing checks
rounding (`10_000 * 20 / 100 == 2000.0`, which Python considers equal to `2000`). Adding two tests
kills all eight:

```python
def test_threshold_boundary():
    assert discount_cents(5_000, vip=True) == 1_000     # exactly on the threshold
    assert discount_cents(4_999, vip=True) == 0         # one cent below


def test_rounds_down_to_whole_cents():
    assert discount_cents(5_003, vip=True) == 1_000     # 1000.6 must become 1000, an int
```

```toml
# pyproject.toml (mutmut 3.x)
[tool.mutmut]
source_paths = ["src/shop/"]
pytest_add_cli_args_test_selection = ["tests/"]

[tool.pytest.ini_options]
pythonpath = ["src"]
```

### Tools

| Language | Tools |
|---|---|
| Java / JVM | **PIT (pitest)**, the most mature; incremental analysis, Maven/Gradle plugins |
| JavaScript / TypeScript, C#, Scala | **Stryker** (StrykerJS, Stryker.NET, Stryker4s) |
| Python | **mutmut**, cosmic-ray |
| Go | gremlins, go-mutesting |
| Rust | cargo-mutants |
| C / C++ | Mull (LLVM-based) |

### Using it without drowning

Correcting a common claim: the goal is **not** to kill 100% of mutants.

- **Equivalent mutants** change the code without changing behaviour (e.g. `i < len` vs `i != len`
  in a loop that only ever increments by one). No test can kill them, and deciding equivalence is
  undecidable in general, so a small fraction of survivors is always noise.
- **Cost.** The suite runs once per mutant: hundreds of mutants for a small module, and for a
  large codebase that becomes thousands of suite runs. Tools cut this by running only the tests that
  cover the mutated line, by caching, and by mutating only changed code.
- **Where it pays**: pricing, billing, authorization, parsers, core algorithms, anything where a
  subtle off-by-one costs money or security. It is rarely worth it on glue code.

Google's approach (Petrović and Ivanković, "State of Mutation Testing at Google", ICSE-SEIP 2018)
is the practical model: mutate only the lines changed in a code review, skip "arid" code such as
logging statements, and show a few surviving mutants to the author as review comments. Developers
act on them as test suggestions, and nobody chases a global score.

Coverage and mutation score answer different questions. Coverage says what ran, which is useful for
finding untested code. Mutation score says whether the tests check what ran. Calling coverage "lies"
overstates it: low coverage is a reliable warning, and high coverage just isn't proof.

## Common interview questions

**What is property-based testing?**
You state a rule that must hold for all valid inputs; the framework generates many inputs,
including edge cases, and if one fails it shrinks it to a minimal counterexample. Hypothesis
(Python), QuickCheck (Haskell), jqwik, fast-check and rapid (Go) are the usual tools.

**What properties would you test for a JSON serializer? For a sort?**
Serializer: round-trip `loads(dumps(x)) == x`, output is valid JSON, deterministic for equal inputs,
never raises except the documented error. Sort: same multiset, ordered, idempotent, equal to a
reference sort.

**What is shrinking and why does it matter?**
After finding a failure, the framework searches for a smaller input that still fails, so you debug a
two-element list rather than a random 300-element one. Hypothesis shrinks the underlying choice
sequence, so it works for any strategy automatically.

**Property testing vs fuzzing?**
Both generate inputs. PBT uses typed, structured generators and your assertions, and runs fast in the
normal suite. Coverage-guided fuzzing mutates raw bytes steered by new code coverage, runs for long
periods, and targets crashes and sanitizer findings; it suits parsers and untrusted input.

**What is mutation testing and what does it measure?**
The tool injects small bugs into the code and runs the tests; a mutant that no test catches has
survived. The killed fraction measures test effectiveness, which coverage can't: a test can execute a
line without asserting anything about it.

**Why not aim for a 100% mutation score?**
Equivalent mutants cannot be killed, and running the suite once per mutant is expensive. Use it on
critical code and changed lines, treat survivors as test suggestions, and don't chase the number.

**How would you test a stateful component such as a cache or a bank account?**
Stateful property testing: generate random operation sequences, compare every result with a simple
model, check invariants after every step, and let the tool shrink failing sequences.

**How does Go fuzzing work?**
`FuzzXxx(f *testing.F)` with `f.Add` seeds and `f.Fuzz(func(t *testing.T, ...))`. Plain `go test` runs
only the seeds and saved crashers; `go test -fuzz=FuzzXxx` does coverage-guided fuzzing and writes
failing inputs to `testdata/fuzz/`, which you commit as regression tests.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — (intern) | Knows example tests only check chosen cases; can read a `@given` test |
| Junior (L3) | Software Engineer I | L3 | Writes round-trip and invariant properties with basic strategies; runs a Go fuzz target; understands a shrunk counterexample |
| Mid (L4) | Software Engineer II | L4 | Chooses properties well (oracle, metamorphic, idempotence); builds composite strategies; explains why coverage is not test strength; reads mutation reports and adds the missing tests |
| Senior (L5) | Senior Software Engineer | L5 | Uses stateful PBT on complex components; puts fuzzing on parsers and untrusted-input paths in CI; applies mutation testing to critical modules with sensible budgets |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7 | Sets policy: continuous fuzzing (OSS-Fuzz / ClusterFuzz-style) for security-sensitive code, diff-based mutation testing in code review, test-effectiveness metrics that teams won't game |

## Interview checklist

- [ ] I can explain the difference between an example and a property, and name five property patterns.
- [ ] I can write a Hypothesis test with `@given`, composite strategies, `assume` and `@example`.
- [ ] I can explain shrinking and Hypothesis's example database.
- [ ] I can write a `RuleBasedStateMachine` that checks a component against a model.
- [ ] I can write and run a Go fuzz target and explain where crashers are stored.
- [ ] I can compare property-based testing with coverage-guided fuzzing.
- [ ] I can explain mutation operators, killed vs survived, and mutation score.
- [ ] I can explain equivalent mutants and why 100% is not the goal.
- [ ] I can say where mutation testing and fuzzing are worth their cost.

Related: [The Testing Pyramid and Unit Tests](01_testing_pyramid.md) (coverage), `PyEngineering/21_fuzzing_property_testing/`,
`GoEngineering/21_fuzzing_property_testing/`, [Security](../SystemDesign/building_blocks/14_security.md)
(untrusted input).
