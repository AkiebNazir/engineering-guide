"""
LEVEL 10 (advanced) - capstone: a small multi-resource report builder
=========================================================================
You will learn (ties together levels 01-09)
  * ExitStack (level 07) opening a variable number of "resources" per report section
  * @contextmanager with try/finally (level 01/02) implementing each resource
  * suppress() (level 04) for an expected, ignorable failure in one section
  * redirect_stdout() (level 08) capturing the whole report as text
  * cleanup happens in reverse order even when one section fails partway through

Run: python level_10_capstone.py
"""
import io
from contextlib import ExitStack, contextmanager, redirect_stdout, suppress


EVENTS: list[str] = []


@contextmanager
def report_section(title: str):
    """One section of a report: prints a header, yields for the body to print
    into, then always prints a footer -- even if the section's body fails."""
    EVENTS.append(f"open:{title}")
    print(f"== {title} ==")
    try:
        yield
    finally:
        print(f"-- end {title} --")
        EVENTS.append(f"close:{title}")


class FlakySource:
    """A "data source" that fails for one particular section, on purpose,
    to exercise suppress() inside the report."""
    def __init__(self, name: str, should_fail: bool):
        self.name = name
        self.should_fail = should_fail

    def fetch(self) -> str:
        if self.should_fail:
            raise LookupError(f"{self.name}: no data available")
        return f"{self.name}: 42 widgets shipped"


def build_report(sources: list[FlakySource]) -> str:
    out = io.StringIO()
    with redirect_stdout(out):
        with ExitStack() as stack:
            for source in sources:
                stack.enter_context(report_section(source.name))
                with suppress(LookupError):
                    print(source.fetch())
    return out.getvalue()


if __name__ == "__main__":
    EVENTS.clear()
    sources = [
        FlakySource("sales", should_fail=False),
        FlakySource("inventory", should_fail=True),   # expected to be missing sometimes
        FlakySource("shipping", should_fail=False),
    ]

    report = build_report(sources)
    print("---- captured report ----")
    print(report)

    # ---- every section printed its header and footer, failure or not ------
    for name in ("sales", "inventory", "shipping"):
        assert f"== {name} ==" in report
        assert f"-- end {name} --" in report

    # ---- successful sources show their data; the flaky one silently doesn't
    assert "sales: 42 widgets shipped" in report
    assert "shipping: 42 widgets shipped" in report
    assert "inventory: 42 widgets shipped" not in report
    assert "no data available" not in report        # suppress() truly hid the exception

    # ---- ExitStack closed every section in reverse order of opening -------
    assert EVENTS == [
        "open:sales", "open:inventory", "open:shipping",
        "close:shipping", "close:inventory", "close:sales",
    ]

    print("OK")
