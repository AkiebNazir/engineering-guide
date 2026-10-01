"""
LEVEL 01 (basic) - functools.reduce: folding a sequence into one value
=======================================================================
You will learn
  * what "reduce" means: repeatedly apply a two-argument function, carrying
    an accumulator, until the sequence is consumed
  * the difference between reduce with and without an explicit initial value
  * why `sum()` / `math.prod()` are usually clearer than `reduce` for the
    common arithmetic cases, and when `reduce` earns its keep instead

Run: python level_01_reduce.py
"""
from functools import reduce


def main() -> None:
    numbers = [1, 2, 3, 4, 5]

    # --- the core idea: fold left-to-right, carrying an accumulator -------
    # reduce(f, seq) with no initial: f(f(f(1, 2), 3), 4) ... starting from
    # the first two elements.
    total = reduce(lambda acc, n: acc + n, numbers)
    assert total == 15 == sum(numbers)  # reduce can reimplement sum()

    product = reduce(lambda acc, n: acc * n, numbers)
    assert product == 120  # 1*2*3*4*5

    # --- explicit initial value changes both the start and the result type
    # of an empty sequence.
    total_with_initial = reduce(lambda acc, n: acc + n, numbers, 100)
    assert total_with_initial == 115  # starts accumulating from 100

    # --- reduce is not limited to numbers: it folds anything -------------
    words = ["Path", "lib", " is", " nice"]
    sentence = reduce(lambda acc, w: acc + w, words)
    assert sentence == "Pathlib is nice"

    # --- flattening a small list-of-lists is a genuinely useful reduce ---
    nested = [[1, 2], [3], [4, 5, 6]]
    flat = reduce(lambda acc, chunk: acc + chunk, nested, [])
    assert flat == [1, 2, 3, 4, 5, 6]

    # --- reduce to find a running maximum (a case where a for-loop or the
    # builtin max() would normally be clearer, but reduce works the same) --
    biggest = reduce(lambda acc, n: n if n > acc else acc, [3, 7, 2, 9, 4])
    assert biggest == 9 == max([3, 7, 2, 9, 4])

    print("OK")


if __name__ == "__main__":
    main()
