"""
20 - Table-driven tests & fakes - Reference Solution
========================================================

See `20_table_driven_tests_fakes_explanation.py` for the full spec,
rationale, and acceptance criteria. This file intentionally stays small -
`20_table_driven_tests_fakes_test.py` is the star of the show for this
problem.
"""

from __future__ import annotations

from typing import Protocol


# ---------------------------------------------------------------------------
# The port + the small component under test.
# ---------------------------------------------------------------------------
class TaxRateSource(Protocol):
    """Structural port: anything that can answer "what's the tax rate for
    this region." A real implementation might query a tax-rate API or a
    database table; tests use a fake or a mock instead (see the test file).
    """

    def rate_for(self, region: str) -> float: ...


class PriceCalculator:
    """The component under test - deliberately simple so the test file
    can focus on demonstrating the table-driven-testing toolkit rather
    than complex business logic."""

    def __init__(self, tax_source: TaxRateSource) -> None:
        self._tax_source = tax_source

    def total(self, subtotal: float, region: str) -> float:
        rate = self._tax_source.rate_for(region)
        return round(subtotal * (1 + rate), 2)

    def receipt(self, subtotal: float, region: str) -> str:
        rate = self._tax_source.rate_for(region)
        tax_amount = round(subtotal * rate, 2)
        total = round(subtotal + tax_amount, 2)
        return (
            f"Subtotal: ${subtotal:.2f}\n"
            f"Region:   {region}\n"
            f"Tax rate: {rate * 100:.2f}%\n"
            f"Total:    ${total:.2f}"
        )


# ---------------------------------------------------------------------------
# A fake dependency - real behavior, no I/O. Lives here (not in the test
# file) because it's a reusable collaborator for anything that depends on
# TaxRateSource, exactly like `InMemorySender` in problem 18.
# ---------------------------------------------------------------------------
class FakeTaxRateSource:
    """An in-memory TaxRateSource: configured with a fixed region->rate
    mapping at construction time, raises KeyError for unknown regions -
    matching the Protocol's documented dict-like lookup semantics.
    """

    def __init__(self, rates: dict[str, float]) -> None:
        self._rates = dict(rates)

    def rate_for(self, region: str) -> float:
        return self._rates[region]


# ---------------------------------------------------------------------------
# Best practices
# ---------------------------------------------------------------------------
# - Keep the component under test free of any test-only concerns - it
#   depends only on the `TaxRateSource` Protocol, same layering discipline
#   as problem 18's ports-and-adapters split.
# - `FakeTaxRateSource` raising `KeyError` (rather than e.g. returning 0.0
#   for unknown regions) matches the Protocol's documented contract - a
#   fake that silently diverges from a real implementation's error
#   behavior is worse than no fake at all, because tests built against it
#   would pass while the real adapter behaves differently in production.
#
# Alternative approaches
# -----------------------
# - `decimal.Decimal` instead of `float`/`round` would be the correct
#   choice for a real billing system (binary floats can't exactly
#   represent most decimal fractions, and `round()` ties break in
#   sometimes-surprising ways) - `float` is used here to keep the
#   arithmetic and golden-file output simple for a testing-focused
#   exercise; see the stretch goals in the explanation file.
