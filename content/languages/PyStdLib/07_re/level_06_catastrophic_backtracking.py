"""
LEVEL 06 (advanced) - MEASURED: catastrophic backtracking, timed
===================================================================
You will learn
  * nested quantifiers like (a+)+ can force the regex engine into exponential
    backtracking on strings that ALMOST match but ultimately fail
  * this is measured with time.perf_counter() on THIS run -- not asserted from memory
  * the fix: remove the redundant nesting so the engine never has to guess

Run: python level_06_catastrophic_backtracking.py
"""
import re
import time

# Bounded on purpose: this input size is enough to show the blowup clearly
# while still finishing in well under a few seconds even on slow hardware.
N = 24
PATHOLOGICAL_INPUT = "a" * N + "b"   # never matches "...c" -- forces full backtracking search

PATHOLOGICAL_PATTERN = re.compile(r"(a+)+c")   # nested quantifier: (a+) repeated by the outer +
FIXED_PATTERN = re.compile(r"a+c")             # equivalent for this input, no nested repetition


def timed_match(pattern: re.Pattern, text: str) -> float:
    start = time.perf_counter()
    result = pattern.match(text)
    elapsed = time.perf_counter() - start
    assert result is None   # neither pattern matches -- the point is HOW LONG it takes to find out
    return elapsed


if __name__ == "__main__":
    pathological_time = timed_match(PATHOLOGICAL_PATTERN, PATHOLOGICAL_INPUT)
    fixed_time = timed_match(FIXED_PATTERN, PATHOLOGICAL_INPUT)

    print(f"pathological (a+)+c  on {N} a's + 'b': {pathological_time*1000:.2f} ms")
    print(f"fixed        a+c     on {N} a's + 'b': {fixed_time*1000:.4f} ms")
    print(f"slowdown factor: {pathological_time / fixed_time:,.0f}x")

    # The fixed pattern must be dramatically faster -- this is a real measurement
    # of THIS run, not a hardcoded number. On a laptop this is typically a
    # 1000x-100000x difference; we assert a conservative floor.
    assert fixed_time < pathological_time
    assert pathological_time / fixed_time > 50   # conservative: real ratio is usually far higher

    # Growing the input by just a few characters roughly DOUBLES the pathological
    # time, because the search space is exponential in the number of a's.
    bigger_input = "a" * (N + 2) + "b"
    bigger_time = timed_match(PATHOLOGICAL_PATTERN, bigger_input)
    print(f"pathological (a+)+c  on {N+2} a's + 'b': {bigger_time*1000:.2f} ms")
    assert bigger_time > pathological_time   # more a's -> measurably slower, not the same

    print("OK")
