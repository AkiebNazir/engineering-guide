"""
LEVEL 10 (advanced) - capstone: a small invoice pipeline using functools
===========================================================================
You will learn
  * how reduce, partial, lru_cache, singledispatch, wraps and total_ordering
    combine in one small, realistic program
  * a LineItem type ordered with @total_ordering, formatted per-type with
    @singledispatch, discounted via partial-configured stages folded with
    reduce, taxed via an @lru_cache'd rate lookup, and audited by a
    @wraps-preserving decorator

Run: python level_10_capstone_invoice.py
"""
from functools import lru_cache, partial, reduce, singledispatch, total_ordering, wraps

AUDIT_LOG: list[str] = []


def audited(func):
    """A decorator that records every call -- correctly, thanks to @wraps."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        AUDIT_LOG.append(f"{func.__name__}(...) -> {result}")
        return result
    return wrapper


@total_ordering
class LineItem:
    def __init__(self, name: str, amount: float):
        self.name, self.amount = name, amount

    def __eq__(self, other):
        return isinstance(other, LineItem) and self.amount == other.amount

    def __lt__(self, other):
        if not isinstance(other, LineItem):
            return NotImplemented
        return self.amount < other.amount

    def __repr__(self):
        return f"{self.name}=${self.amount:.2f}"


@singledispatch
def display(value) -> str:
    return str(value)


@display.register
def _(value: float) -> str:
    return f"${value:.2f}"


@display.register
def _(value: LineItem) -> str:
    return f"{value.name}: {display(value.amount)}"


@lru_cache(maxsize=None)
def tax_rate_for(region: str) -> float:
    """Pretend this hits a slow lookup table; caching avoids repeating it."""
    return {"US": 0.08, "EU": 0.20, "UK": 0.20}.get(region, 0.0)


def apply_percentage(rate: float, amount: float) -> float:
    return amount * (1 + rate)


@audited
def total_with_tax(items: list, region: str) -> float:
    subtotal = reduce(lambda acc, item: acc + item.amount, items, 0.0)
    apply_tax = partial(apply_percentage, tax_rate_for(region))
    return round(apply_tax(subtotal), 2)


def main() -> None:
    items = [LineItem("Widget", 19.99), LineItem("Gadget", 49.50), LineItem("Cable", 4.25)]

    # --- total_ordering: sort and compare line items by amount ------------
    ordered = sorted(items)
    assert [i.name for i in ordered] == ["Cable", "Widget", "Gadget"]
    assert max(items) == LineItem("anything", 49.50)  # __eq__ by amount only

    # --- singledispatch: format a float vs a LineItem differently ---------
    assert display(49.5) == "$49.50"
    assert display(items[0]) == "Widget: $19.99"

    # --- reduce + partial + lru_cache, wired through an audited function --
    us_total = total_with_tax(items, "US")
    eu_total = total_with_tax(items, "EU")
    assert us_total == round((19.99 + 49.50 + 4.25) * 1.08, 2)
    assert eu_total == round((19.99 + 49.50 + 4.25) * 1.20, 2)

    # --- the audit decorator preserved the function's identity -----------
    assert total_with_tax.__name__ == "total_with_tax"
    assert len(AUDIT_LOG) == 2
    assert AUDIT_LOG[0].startswith("total_with_tax(...) -> ")

    # --- the tax-rate cache actually cached: 2 distinct regions, no repeats
    info = tax_rate_for.cache_info()
    assert info.misses == 2  # "US" then "EU", each looked up once
    assert info.hits == 0

    # calling total_with_tax("US", ...) a second time reuses the cached rate
    total_with_tax(items, "US")
    info = tax_rate_for.cache_info()
    assert info.hits == 1
    assert info.misses == 2  # no new miss for the repeated "US" lookup

    print(f"US total: ${us_total}, EU total: ${eu_total}")
    print(f"audit log entries: {len(AUDIT_LOG)}")
    print("OK")


if __name__ == "__main__":
    main()
