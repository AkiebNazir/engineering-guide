"""pytest plugin hook for this directory only.

`pytest_addoption` is only recognized by pytest when defined in a
`conftest.py` (or an installed plugin) - not in an ordinary test module.
This file exists solely to register `--update-golden`; the fixture that
reads it (`update_golden`) lives in `20_table_driven_tests_fakes_test.py`
next to the golden-file test that uses it.
"""

from __future__ import annotations

import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--update-golden",
        action="store_true",
        default=False,
        help="Regenerate golden fixture files instead of comparing against them.",
    )
