# Code Quality and Practices

Practical engineering discipline, not patterns. This is the day-to-day judgment that determines whether a well-architected system stays healthy after six months of real changes.

## The testing pyramid

```text
        /\
       /e2e\        few — slow, flaky, expensive, high confidence per test
      /------\
     /integr. \     some — real boundaries (DB, HTTP), moderate speed
    /----------\
   /   unit     \   many — fast, isolated, cheap to write and rerun
  /--------------\
```

Most of the suite should be fast unit tests against isolated logic; a smaller layer of integration tests should check that components actually wire together (DB queries, <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> contracts); a thin top layer of end-to-end tests should check that the full user-facing flow works.

**Inverting it (the "ice cream cone"):** mostly e2e tests, few unit tests. Consequence: the suite is slow (minutes to hours instead of seconds), flaky (e2e tests depend on timing, network, shared environments), and a single logic bug requires spinning up the whole stack to even locate — feedback loops go from seconds to <abbr title="Continuous Integration. The practice of merging all developers' working copies to a shared mainline several times a day.">CI</abbr>-run minutes, so engineers stop running tests locally before pushing.

## <abbr title="Test-Driven Development. A software development process relying on software requirements being converted to test cases before software is fully developed.">TDD</abbr>

What it actually buys you is not "tests exist" — you can write tests after the fact and get that. Writing the test *first* forces you to design the interface from the caller's point of view before the implementation exists, which applies design pressure toward small, dependency-injected, testable units (naturally pushes toward DIP, [01](01_design_principles.md)) and toward functions with one clear job (SRP). A codebase written test-first tends to have narrower, more composable interfaces than one where tests were retrofitted onto an implementation that was never designed to be called in isolation.

## Code review

A good review checks, in priority order:

1. **Correctness** — does this do what it claims, including edge cases and failure paths?
2. **Design fit** — does this belong here, does it duplicate/contradict existing logic, does it violate an established boundary (module, layer, bounded context)?
3. **Test coverage of the actual risk** — are the paths that can break covered, not just line coverage for its own sake?
4. **Readability for the next reader**, not for the author who already has full context.

What a good review does **not** spend time on: style/formatting a linter or formatter should catch automatically (indentation, import order, line length) — bikeshedding style in review is a signal the team is missing automated tooling, not a signal the reviewer is being thorough.

## Refactoring discipline

- Small, reversible steps — each step leaves the code in a working state, so you can stop or revert at any point without a half-finished mess.
- Keep tests green throughout — a refactor that requires temporarily breaking tests isn't a refactor, it's a rewrite wearing a refactor's name.
- **Never mix refactor and feature-change in one commit.** A commit that both renames a function and changes its behavior makes the diff unreviewable — the reviewer can't tell which lines are "moved" versus "changed," and a regression introduced by the behavior change is hidden inside noise from the rename.

## Technical debt

Debt is a legitimate trade-off when it's taken on **consciously**: "we're shipping the fast, less-general version now to hit a date, and we know the cost is X, tracked in ticket Y." Debt accrued **by accident** — no test coverage because no one thought about it, an interface that leaked implementation details because no one reviewed the boundary — is not a trade-off, it's a quality failure with a rebranded name. The difference matters because conscious debt has a payoff already banked (the date was hit) and a known payoff structure (a ticket, a plan); accidental debt has no offsetting payoff at all — it's pure future cost.

## Clean naming and function-size heuristics

- A function does one thing, at one level of abstraction (see <abbr title="Service Level Agreement - A commitment between a service provider and a client outlining expected performance metrics such as availability.">SLA</abbr>, [01](01_design_principles.md)) — if you need "and" to describe it (`validateAndSave`), it's two functions wearing one name.
- Name for *what*, not *how*: `activeUsers()` not `filterListWhereStatusEqualsActive()`.
- If a function needs a comment explaining a block within it, that block is usually a candidate to extract into a well-named function — the extraction *is* the comment.
- Function length is a symptom, not the rule itself: a long function is suspicious because it's usually doing several unrelated things, not because line count has an inherent limit.

## The 12-factor app (the parts that actually matter)

| Factor | Practice | Why it earns its place in review |
|---|---|---|
| Config via environment | Secrets/endpoints/feature flags come from environment/config service, never hardcoded or committed. | Makes the same build promotable across dev/staging/prod unchanged — a hardcoded URL means you're not actually testing what you'll ship. |
| Stateless processes | No sticky in-memory session/user state in the app process; externalize to a store. | Any instance can serve any request — this is what makes horizontal scaling and rolling deploys safe. |
| Logs as event streams | Write logs to stdout/stderr as a stream; let the platform route/aggregate them. | Decouples the app from log-storage/rotation concerns and makes local dev and prod behave the same way. |
| Dev/prod parity | Keep dev, staging, and prod as similar as practical (same backing services, close versions). | "Works on my machine" is usually a parity gap — a dependency version or a backing service swapped for a lighter local stand-in. |

## Semantic versioning basics

`MAJOR.MINOR.PATCH` for any public <abbr title="Application Programming Interface">API</abbr>/library:

- **MAJOR** — incompatible/breaking <abbr title="Application Programming Interface">API</abbr> change.
- **MINOR** — backward-compatible new functionality.
- **PATCH** — backward-compatible bug fix.

A consumer pinning `^1.4.0` (or equivalent) is trusting that you will never ship a breaking change as a minor or patch bump — violating that trust (shipping a breaking change as a patch) is the single fastest way to break every downstream consumer's build silently, because they never expected to need to review that release.

## Related

- [01 — Design principles](01_design_principles.md) — <abbr title="Service Level Agreement - A commitment between a service provider and a client outlining expected performance metrics such as availability.">SLA</abbr> and DIP underpin naming/function-size heuristics and <abbr title="Test-Driven Development. A software development process relying on software requirements being converted to test cases before software is fully developed.">TDD</abbr>'s design pressure.
- [07 — Anti-patterns and code smells](07_anti_patterns_and_code_smells.md)
