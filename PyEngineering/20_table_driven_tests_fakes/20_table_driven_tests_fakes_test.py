"""Tests for `20_table_driven_tests_fakes_solution.py` - this file is the
star of the show for problem 20, demonstrating table-driven tests
(`pytest.mark.parametrize`), golden files with an opt-in `--update-golden`
regeneration flag, a hand-written fake vs `unittest.mock`, and
parallel-test-safety practices.

Run: .venv/bin/pytest 20_table_driven_tests_fakes/ -v
Regenerate the golden fixture (review the diff before committing it!):
    .venv/bin/pytest 20_table_driven_tests_fakes/ --update-golden -v

PARALLEL-TEST-SAFETY NOTE
--------------------------
Every test below either (a) constructs its own fresh `FakeTaxRateSource`/
`PriceCalculator`/`Mock` locally - no shared mutable module-level or
class-level state that one test could leave mutated for the next - or
(b) touches the filesystem only via the checked-in read-only `golden/`
fixture (open for read, or for write strictly behind the explicit
`--update-golden` opt-in) or the built-in `tmp_path` fixture, which
pytest guarantees is a fresh, unique directory per test. None of this
suite would need any changes to run correctly under `pytest-xdist`
(not installed here, per the curriculum's fixed toolchain) - the
defining property of a parallel-safe suite is that no two tests can
observe or clobber each other's state no matter what order or process
they run in.
"""

from __future__ import annotations

from importlib import import_module
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

# The module under test is named "20_..." which is not a valid Python
# identifier, so it can't be reached with a normal `import` statement -
# `importlib.import_module` takes an arbitrary string and works fine for a
# file-based module. mypy can't statically resolve these as *types*, only
# as runtime values, hence the `Any` annotations below.
_solution = import_module("20_table_driven_tests_fakes_solution")
TaxRateSource = _solution.TaxRateSource
PriceCalculator = _solution.PriceCalculator
FakeTaxRateSource = _solution.FakeTaxRateSource

_GOLDEN_DIR = Path(__file__).parent / "golden"


# ---------------------------------------------------------------------------
# --update-golden fixture: reads the CLI flag registered in conftest.py.
# ---------------------------------------------------------------------------
@pytest.fixture
def update_golden(request: pytest.FixtureRequest) -> bool:
    result: bool = request.config.getoption("--update-golden")
    return result


def _check_golden(name: str, actual: str, *, update: bool) -> None:
    """Compare `actual` against the checked-in golden fixture `name`, or
    regenerate it when `update` is True.

    Never silently "passes" on a missing fixture - a `FileNotFoundError`
    when NOT updating is a real failure that tells the developer to run
    once with `--update-golden` to create the fixture deliberately.
    """
    path = _GOLDEN_DIR / name
    if update:
        path.write_text(actual)
        return
    expected = path.read_text()
    assert actual == expected, (
        f"{name} does not match golden fixture; if this change is "
        f"intentional, re-run with --update-golden and review the diff"
    )


# ---------------------------------------------------------------------------
# Table-driven tests: PriceCalculator.total() across several cases.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("subtotal", "region", "rate", "expected"),
    [
        (100.0, "US-CA", 0.0825, 108.25),
        (0.0, "US-CA", 0.0825, 0.0),
        (10.0, "US-OR", 0.0, 10.0),
        (19.99, "US-CA", 0.0825, 21.64),
    ],
    ids=[
        "basic-rate",
        "zero-subtotal",
        "zero-rate-region",
        "fractional-cent-rounding",
    ],
)
def test_total_across_cases(
    subtotal: float, region: str, rate: float, expected: float
) -> None:
    fake: Any = FakeTaxRateSource({region: rate})
    calc = PriceCalculator(fake)

    assert calc.total(subtotal, region) == expected


def test_total_raises_key_error_for_unknown_region() -> None:
    fake: Any = FakeTaxRateSource({"US-CA": 0.0825})
    calc = PriceCalculator(fake)

    with pytest.raises(KeyError):
        calc.total(10.0, "US-NY")


# ---------------------------------------------------------------------------
# Golden-file test for receipt() rendering.
# ---------------------------------------------------------------------------
def test_receipt_matches_golden_fixture(update_golden: bool) -> None:
    fake: Any = FakeTaxRateSource({"US-CA": 0.0825})
    calc = PriceCalculator(fake)

    actual = calc.receipt(100.0, "US-CA")

    _check_golden("basic_receipt.golden", actual, update=update_golden)


# ---------------------------------------------------------------------------
# Fake dependency: real behavior across multiple configured regions.
# ---------------------------------------------------------------------------
def test_fake_tax_rate_source_computes_totals_for_multiple_regions() -> None:
    # A fake is the right tool here: we need genuine, stateful behavior
    # (a small lookup table that answers different rates for different
    # regions across multiple calls), not an assertion about how the
    # dependency was *called*. A Mock configured with `side_effect` could
    # technically do this too, but would be strictly more code to express
    # the same thing a two-line dict-backed fake does more readably.
    fake: Any = FakeTaxRateSource({"US-CA": 0.0825, "US-OR": 0.0, "US-NY": 0.08875})
    calc = PriceCalculator(fake)

    assert calc.total(100.0, "US-CA") == 108.25
    assert calc.total(100.0, "US-OR") == 100.0
    assert calc.total(100.0, "US-NY") == 108.88


def test_fake_tax_rate_source_raises_key_error_for_unconfigured_region() -> None:
    fake: Any = FakeTaxRateSource({"US-CA": 0.0825})

    with pytest.raises(KeyError):
        fake.rate_for("US-TX")


# ---------------------------------------------------------------------------
# unittest.mock: asserting call shape, which a fake can't express as
# naturally.
# ---------------------------------------------------------------------------
def test_price_calculator_calls_rate_for_with_exact_region() -> None:
    # A Mock is the right tool for *this* assertion: we don't care what
    # the tax rate actually is, only that PriceCalculator asks its
    # dependency for the rate of exactly the region it was given - a
    # call-shape assertion (was `rate_for` called, with which argument,
    # how many times) that a hand-written fake has no natural vocabulary
    # for without adding call-recording machinery that would just turn it
    # into a worse Mock.
    mock_source = Mock(spec=TaxRateSource)
    mock_source.rate_for.return_value = 0.05
    calc = PriceCalculator(mock_source)

    calc.total(50.0, "EU-DE")

    mock_source.rate_for.assert_called_once_with("EU-DE")


def test_price_calculator_does_not_over_mock_the_computation() -> None:
    # Contrast with over-mocking: this test still asserts on the REAL
    # computed output (not just "total() returned mock_source's return
    # value unchanged"), which is what keeps it meaningful - a test that
    # only checked `mock_source.rate_for.called` and stubbed `total`
    # itself would prove nothing about PriceCalculator's actual logic.
    mock_source = Mock(spec=TaxRateSource)
    mock_source.rate_for.return_value = 0.1
    calc = PriceCalculator(mock_source)

    assert calc.total(20.0, "EU-FR") == 22.0


# ---------------------------------------------------------------------------
# tmp_path: filesystem isolation, no dependency on cwd or shared state.
# ---------------------------------------------------------------------------
def test_receipt_can_be_written_and_reread_via_tmp_path(tmp_path: Path) -> None:
    # Demonstrates the tmp_path pattern for any test that legitimately
    # needs to touch the filesystem: pytest hands each test a fresh,
    # unique directory, so two tests (or two parallel workers) writing a
    # file of the same name can never collide - unlike writing to a fixed
    # relative path or the current working directory.
    fake: Any = FakeTaxRateSource({"US-CA": 0.0825})
    calc = PriceCalculator(fake)
    receipt_text = calc.receipt(42.0, "US-CA")

    receipt_path = tmp_path / "receipt.txt"
    receipt_path.write_text(receipt_text)

    assert receipt_path.read_text() == receipt_text
