"""
20 - Table-driven tests & fakes
==================================

WHAT WE'RE BUILDING
--------------------
A small, deliberately simple component (`PriceCalculator`) with one real
external dependency described as a `typing.Protocol` port (same pattern as
problem 18): `TaxRateSource.rate_for(region: str) -> float`. The point of
this problem is NOT the component - it's this file's test suite, which
demonstrates the full Python table-driven-testing toolkit:

- `pytest.mark.parametrize` with explicit `ids=` for readable table-driven
  cases (the pytest/Python answer to Go's `t.Run(tt.name, ...)` subtests).
- A **golden file** pattern: `PriceCalculator.receipt(...)` renders a
  human-readable text receipt, tested by comparing against a checked-in
  `.golden` fixture file, with a `--update-golden` custom pytest CLI
  option to regenerate them when the intended output changes.
- A **fake** dependency (`FakeTaxRateSource`, in `_solution.py` since it's
  the thing under test's real collaborator) vs `unittest.mock.Mock`/
  `patch` - both are demonstrated, with commentary on when each is the
  right tool.
- Notes on **parallel-test-safety**: no shared mutable module/class-level
  state, `tmp_path` for filesystem isolation - written so the suite would
  still pass under `pytest-xdist` even though it isn't installed here.

WHY THIS MATTERS IN REAL SYSTEMS
----------------------------------
Table-driven tests turn "I wrote three separate test functions that are
90% copy-pasted with one different input" into one parametrized function
plus a table of cases - the table itself becomes documentation of the
behavior spec (each `id=` is a one-line English description of a case).
Golden files solve the problem of asserting on a large, structured piece
of output (a rendered receipt, a report, a generated file) without either
(a) hand-writing a giant expected-string literal in the test that's
painful to update, or (b) not testing the output shape at all - you
generate it once, review the diff like code, and regenerate deliberately
via a flag rather than by hand-editing the fixture.

Fakes vs mocks is a real, recurring judgment call in production test
suites: `unittest.mock.Mock`/`patch` is the right tool when you need to
assert *how* a dependency was called (call count, argument values) or
when building a real fake is disproportionate effort for a rarely-used
interface. A hand-written fake is the right tool when the dependency has
enough real behavior (state that persists across calls, computed
responses, invariants) that a mock's call-recording alone can't express
it - over-mocking (mocking so much of the system that the test mostly
verifies your mocks were configured correctly, not that the code works)
is one of the most common ways a test suite becomes worthless without
looking broken.

CONCEPTS COVERED
------------------
- `pytest.mark.parametrize` (single and stacked/multi-dimension), `ids=`
- A custom pytest CLI option (`--update-golden`) via a `pytest_addoption`
  hook in a small `conftest.py` next to the test file (pytest only
  recognizes this hook in `conftest.py`/plugins, not in an ordinary test
  module - a real gotcha the first time you try to add a custom flag) and
  a fixture that reads it
- Golden-file testing: generate-and-compare, with a deliberate opt-in
  regeneration path (never silently auto-update)
- A hand-written fake Protocol implementation vs `unittest.mock.Mock`/
  `unittest.mock.patch`
- `tmp_path` fixture for filesystem-isolated, parallel-safe tests
- Why shared mutable global/class state breaks test-parallel-safety

THE SPEC
---------
`TaxRateSource` (Protocol): `rate_for(self, region: str) -> float` -
    returns a tax rate as a fraction (e.g. `0.0825` for 8.25%). Raises
    `KeyError` for an unknown region (matches dict-like lookup semantics).

`PriceCalculator` (constructed with a `tax_source: TaxRateSource`):
    - `total(self, subtotal: float, region: str) -> float` - returns
      `subtotal * (1 + tax_source.rate_for(region))`, rounded to 2
      decimal places (`round(..., 2)`).
    - `receipt(self, subtotal: float, region: str) -> str` - renders a
      fixed-format multi-line text receipt (subtotal, tax rate, tax
      amount, total - see the solution for the exact format) used by the
      golden-file tests.

Test file must include, at minimum:
1. A `@pytest.mark.parametrize` table (with `ids=`) covering `total()`
   across several `(subtotal, region, rate, expected)` cases including a
   zero rate, a fractional-cent rounding case, and a zero subtotal.
2. A golden-file test for `receipt()`: reads/writes a fixture file next
   to the test (e.g. `20_table_driven_tests_fakes/golden/basic_receipt.golden`),
   comparing actual output to the file's contents unless `--update-golden`
   is passed, in which case it writes the actual output to the file and
   the test still passes (a genuine "review the diff, then bless it"
   workflow, not a silent auto-pass).
3. At least one test using the hand-written `FakeTaxRateSource` (multiple
   regions configured, exercising real "compute a total across two
   different fake-configured regions" behavior).
4. At least one test using `unittest.mock.Mock`/`patch` appropriately
   (e.g. asserting `rate_for` was called with the exact expected region
   argument - a call-shape assertion a fake can't express as naturally),
   with a comment explaining why a mock (not a fake) is the right tool
   for *that specific* assertion.
5. A comment block (near the top or bottom of the test file) explicitly
   addressing parallel-test-safety: no shared mutable global/class state
   across tests, `tmp_path` used for any filesystem interaction.

ACCEPTANCE CRITERIA
---------------------
1. All parametrized cases pass individually addressable by their `id=`
   (visible in `pytest -v` output).
2. Golden file test passes against the checked-in fixture by default, and
   `pytest 20_table_driven_tests_fakes/ --update-golden` regenerates it
   (verify by hand once, then re-run without the flag to confirm it
   passes against the regenerated file).
3. The fake and the mock are each used for the case they're best suited
   to - not the same assertion done twice two different ways.
4. No test reads or writes any file outside `tmp_path` or the checked-in
   `golden/` fixture directory.
5. mypy-clean, black-formatted, ruff-clean.
"""

from __future__ import annotations

from typing import Protocol


# ---------------------------------------------------------------------------
# The port + the small component under test.
# ---------------------------------------------------------------------------
class TaxRateSource(Protocol):
    """Structural port (see problem 18): anything that can answer "what's
    the tax rate for this region" - a real implementation might query a
    tax-rate API or a database table; tests use a fake or a mock instead.
    """

    def rate_for(self, region: str) -> float: ...


class PriceCalculator:
    """The (deliberately simple) component under test.

    TODO:
    - __init__(self, tax_source: TaxRateSource) -> None: store it.
    - total(self, subtotal: float, region: str) -> float: look up the
      rate via self._tax_source.rate_for(region), return
      round(subtotal * (1 + rate), 2).
    - receipt(self, subtotal: float, region: str) -> str: render a
      multi-line text receipt. Suggested format (four lines, no trailing
      newline):
          Subtotal: $12.50
          Region:   US-CA
          Tax rate: 8.25%
          Total:    $13.53
      (rate formatted as a percentage with 2 decimal places; dollar
      amounts formatted with 2 decimal places). Match this format exactly
      if you want the checked-in golden fixture (written by the reference
      solution) to compare equal - or regenerate it with --update-golden
      once you've implemented this and decided on your own format.
    """

    def __init__(self, tax_source: TaxRateSource) -> None:
        raise NotImplementedError("TODO: implement PriceCalculator.__init__")

    def total(self, subtotal: float, region: str) -> float:
        raise NotImplementedError("TODO: implement PriceCalculator.total")

    def receipt(self, subtotal: float, region: str) -> str:
        raise NotImplementedError("TODO: implement PriceCalculator.receipt")


# ---------------------------------------------------------------------------
# HINTS
# -----
# - The fake (`FakeTaxRateSource`) belongs in `_solution.py`, not here -
#   it's a real, reusable test collaborator, not part of the stub surface
#   you're implementing. The golden-file `pytest_addoption` hook lives in
#   a small `conftest.py` next to the test file (pytest requires this -
#   it will NOT discover `pytest_addoption` inside an ordinary test
#   module), and the `update_golden` fixture that reads the flag lives in
#   `_test.py`.
# - `round(x, 2)` uses banker's rounding on ties (`round(0.125, 2)` may
#   not do what you expect due to binary float representation) - this is
#   fine for this exercise's purposes but worth knowing; a real billing
#   system would use `decimal.Decimal` throughout instead of `float`.
#
# COMMON PITFALLS
# ---------------
# - Building the golden-file comparison so that a missing fixture file
#   silently "passes" (e.g. via a bare `except FileNotFoundError: pass`)
#   instead of failing loudly and telling the developer to run
#   `--update-golden` once to create it.
# - Letting `--update-golden` regenerate *and* immediately assert success
#   in the same run without ever having compared against a previous
#   version - fine for creating a fixture the first time, but the real
#   value of golden files is in the diff a reviewer sees in version
#   control when the fixture changes, so treat regeneration as a
#   deliberate, reviewed action, not routine.
#
# STRETCH GOALS
# --------------
# - Add a second golden fixture for a zero-subtotal receipt and a second
#   parametrized dimension (currency symbol) to `receipt()`.
# - Add a `pytest.fixture(params=[...])` version of the tax-rate table
#   instead of `@pytest.mark.parametrize` and compare readability/ID
#   output between the two approaches.
# - Convert `PriceCalculator` to use `decimal.Decimal` instead of `float`
#   and adjust the golden fixture + parametrize table accordingly -
#   demonstrates why real billing code avoids binary floating point.
