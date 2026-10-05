"""
LEVEL 04 (basic) - the real TypeError: naive vs aware datetimes don't compare
================================================================================
You will learn
  * a "naive" datetime has no tzinfo; an "aware" one does
  * comparing (or subtracting) a naive datetime against an aware one raises
    TypeError -- triggered and caught here for real
  * the fix: make both aware (attach a tzinfo), or both naive, before comparing

Run: python level_04_naive_vs_aware_error.py
"""
from datetime import datetime, timezone


def main() -> None:
    naive = datetime(2024, 3, 15, 12, 0, 0)                  # no tzinfo
    aware = datetime(2024, 3, 15, 12, 0, 0, tzinfo=timezone.utc)  # has tzinfo

    assert naive.tzinfo is None
    assert aware.tzinfo is timezone.utc

    # --- the real, triggered exception --------------------------------------
    try:
        naive < aware
        raised = False
    except TypeError as exc:
        raised = True
        message = str(exc)
    assert raised, "comparing naive and aware datetimes must raise TypeError"
    assert "naive" in message and "aware" in message

    # subtraction hits the same wall.
    try:
        aware - naive
        raised = False
    except TypeError:
        raised = True
    assert raised, "subtracting a naive datetime from an aware one must raise TypeError"

    # equality is the one exception: naive == aware is allowed and just False,
    # it does not raise (Python defines cross-type __eq__ to fall back to
    # False rather than error, unlike <, <=, >, >=, and subtraction).
    assert (naive == aware) is False

    # --- the fix: make both aware (preferred) --------------------------------
    naive_made_aware = naive.replace(tzinfo=timezone.utc)
    assert naive_made_aware == aware
    assert naive_made_aware <= aware

    # --- the fix, alternative: strip tzinfo to compare as naive -------------
    aware_made_naive = aware.replace(tzinfo=None)
    assert aware_made_naive == naive
    assert aware_made_naive <= naive

    # --- a mixed collection cannot be sorted without normalizing first ------
    try:
        sorted([naive, aware])
        raised = False
    except TypeError:
        raised = True
    assert raised, "sorting a mixed naive/aware list must raise TypeError"

    normalized = sorted([naive.replace(tzinfo=timezone.utc), aware])
    assert normalized == [naive_made_aware, aware]

    print("OK")


if __name__ == "__main__":
    main()
