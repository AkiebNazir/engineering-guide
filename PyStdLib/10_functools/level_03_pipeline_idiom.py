"""
LEVEL 03 (basic) - combining reduce + partial into a small pipeline idiom
===========================================================================
You will learn
  * a common real idiom: build a list of single-argument callables (some of
    them `partial`-configured) and fold a value through all of them with
    `reduce`, applying each stage left to right
  * this is a tiny, dependency-free stand-in for a "pipeline" / middleware
    chain: each stage takes and returns the same type
  * how partial lets you parameterize a generic stage (e.g. "clamp",
    "scale") into a concrete pipeline step without writing a new function

Run: python level_03_pipeline_idiom.py
"""
from functools import partial, reduce


def clamp(low: float, high: float, value: float) -> float:
    """Generic stage: keep value within [low, high]."""
    return max(low, min(high, value))


def scale(factor: float, value: float) -> float:
    """Generic stage: multiply value by factor."""
    return value * factor


def add(offset: float, value: float) -> float:
    """Generic stage: shift value by offset."""
    return value + offset


def run_pipeline(stages: list, value: float) -> float:
    """Fold `value` through every stage, left to right."""
    return reduce(lambda acc, stage: stage(acc), stages, value)


def main() -> None:
    # Each stage is a plain function of one remaining argument (`value`),
    # built with partial from a generic, reusable stage function.
    pipeline = [
        partial(scale, 2),          # double it
        partial(add, -3),           # shift down by 3
        partial(clamp, 0, 100),     # keep it in [0, 100]
    ]

    # 10 -> scale(2) -> 20 -> add(-3) -> 17 -> clamp(0,100) -> 17
    assert run_pipeline(pipeline, 10) == 17

    # A value that would go out of range gets clamped by the last stage.
    # 60 -> scale(2) -> 120 -> add(-3) -> 117 -> clamp(0,100) -> 100
    assert run_pipeline(pipeline, 60) == 100

    # A negative result gets clamped up to 0.
    # 1 -> scale(2) -> 2 -> add(-3) -> -1 -> clamp(0,100) -> 0
    assert run_pipeline(pipeline, 1) == 0

    # The pipeline is just data: reordering stages changes the outcome,
    # which is the whole point of building it out of composable pieces.
    reordered = [
        partial(add, -3),
        partial(scale, 2),
        partial(clamp, 0, 100),
    ]
    # 10 -> add(-3) -> 7 -> scale(2) -> 14 -> clamp -> 14
    assert run_pipeline(reordered, 10) == 14

    # An empty pipeline is the identity function, thanks to reduce's
    # explicit initial value (the starting `value` itself).
    assert run_pipeline([], 42) == 42

    print("OK")


if __name__ == "__main__":
    main()
