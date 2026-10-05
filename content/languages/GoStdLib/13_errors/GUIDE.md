# errors — creating, wrapping, and inspecting error values

`errors` is the small package behind Go's `if err != nil` idiom. It gives you
three things: ways to *make* an error (`errors.New`, or `fmt.Errorf` with
`%w`), ways to *build a chain* of errors that remember what caused them
(wrapping), and ways to *inspect* a chain without caring how deep it is
(`errors.Is`, `errors.As`, `errors.Unwrap`, `errors.Join`).

## When to reach for it vs alternatives already in this repo

- A fixed, comparable "this specific thing happened" value → a package-level
  sentinel via `errors.New` (like `io.EOF`), checked with `errors.Is`. Not a
  raw string compare on `err.Error()` — see the gotcha table.
- An error that needs to carry data (which field failed, what value was out
  of range) → a custom type implementing `error`, extracted with `errors.As`.
- Adding context while a real error travels up the call stack → `fmt.Errorf("doing
  X: %w", err)`, not `errors.New(err.Error())` (that drops the chain — `errors.Is`
  can no longer see through it).
- Several independent failures from one operation (e.g. validating every
  field of a form) → `errors.Join`, not just returning the first one you hit.
- Logging/printing an error for a human → `fmt` verbs (`%v`, `%s`, `%+v` if the
  type supports it) — see `../02_fmt`. `errors` is for *program logic* on an
  error value, `fmt` is for *displaying* one.
- Recovering from a panic, or control flow that isn't really an "error" (e.g.
  end of an iteration) → plain `panic`/`recover`, not shoehorned into
  `errors`.

## Gotchas

| Gotcha | Detail |
|---|---|
| `%v` vs `%w` in `fmt.Errorf` | `%v` stringifies the inner error — `errors.Is`/`As` can no longer see it. `%w` wraps it — the chain stays walkable. Silent, no compile error either way. |
| Two `errors.New("x")` calls are never `==` | `errors.New` returns a pointer to a new `errorString` struct each call. Comparing errors with `==` (or by message) instead of `errors.Is` looks fine until someone wraps one side. |
| `errors.Is` walks the *whole* chain every call | It calls `Unwrap` repeatedly until it finds a match or hits `nil`. A very deep wrap chain is not free — see level 6's numbers. |
| `errors.Join`'s result unwraps to `[]error`, not one error | Its `Unwrap() []error` method is why `Is`/`As` still work on every joined error, but you can't just chain-`Unwrap()` it like a single wrap. |
| A custom error type must have a comparable `Is`/`As` shape | `errors.As` needs a pointer to a type (or interface) implementing `error`; passing the wrong kind (e.g. a non-pointer) panics at runtime, not compile time. |
| `MustCompile`-style panics belong at startup, not mid-request | Not this package's own function, but the same principle applies to any `errors.New`/`panic` used for "this must never happen" invariants: fail at init, don't let a bad state limp into production traffic. |

## What the 10 levels cover

Levels 1-3 build the basics: `errors.New` and equality via `errors.Is`,
`fmt.Errorf("%w", ...)` plus manual `errors.Unwrap`, then a realistic
multi-layer wrap chain checked end-to-end with `errors.Is`. Level 4 adds a
custom error type with structured fields, extracted through the chain with
`errors.As`. Level 5 covers `errors.Join` for independent errors and proves
`Is`/`As` still see through it. Level 6 is a measured comparison of
`errors.Is` cost on a shallow vs. a deep wrap chain. Level 7 is a design
concern: opaque (`%v`) vs. transparent (`%w`) wrapping at an API boundary, and
why you'd deliberately choose either. Level 8 is `errors` + `fmt` interop:
`fmt.Errorf` with *multiple* `%w` verbs (Go 1.20+), producing a multi-child
tree that `Is`/`As` both traverse. Level 9 is a correctness trap: comparing
errors with `==` instead of `errors.Is`. Level 10 is a capstone config
validator combining sentinels, a custom type, wrapping, and `errors.Join`.
