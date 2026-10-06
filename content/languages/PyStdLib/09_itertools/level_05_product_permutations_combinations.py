"""
LEVEL 05 (advanced) - product vs permutations vs combinations vs combinations_with_replacement
===================================================================================================
You will learn
  * product: every ordered tuple, WITH repetition, from one or more input pools
  * permutations: every ordering of r items, WITHOUT repeating an item's position twice
  * combinations: every UNORDERED r-subset, no repeats
  * combinations_with_replacement: every unordered r-subset, repeats ALLOWED

Run: python level_05_product_permutations_combinations.py
"""
from itertools import combinations, combinations_with_replacement, permutations, product

ITEMS = ["A", "B", "C"]

if __name__ == "__main__":
    # ---- product: Cartesian product, order matters, repetition allowed -----
    # product(ITEMS, repeat=2) is every (x, y) pair including (x, x)
    prod = list(product(ITEMS, repeat=2))
    assert len(prod) == 9              # 3 x 3
    assert ("A", "A") in prod          # repetition of the SAME item is allowed
    assert ("A", "B") in prod and ("B", "A") in prod   # both orders present

    # ---- permutations: order matters, NO repeated item within one tuple ----
    perms = list(permutations(ITEMS, 2))
    assert len(perms) == 6             # 3 x 2 (3P2)
    assert ("A", "A") not in perms     # an item can't pair with itself
    assert ("A", "B") in perms and ("B", "A") in perms   # both orders still present

    # ---- combinations: order does NOT matter, no repeats -------------------
    combos = list(combinations(ITEMS, 2))
    assert len(combos) == 3            # 3 choose 2
    assert ("A", "B") in combos
    assert ("B", "A") not in combos    # only ONE of the two orderings appears

    # ---- combinations_with_replacement: order doesn't matter, repeats OK ---
    combos_wr = list(combinations_with_replacement(ITEMS, 2))
    assert len(combos_wr) == 6         # 3+2-1 choose 2 = 6
    assert ("A", "A") in combos_wr     # repetition allowed here, unlike plain combinations
    assert ("B", "A") not in combos_wr  # still no reordering, like plain combinations

    # summary: same input and r, four different counts, in increasing order
    counts = (len(combos), len(combos_wr), len(perms), len(prod))
    assert counts == (3, 6, 6, 9)
    assert len(combos) <= len(combos_wr) <= len(perms) <= len(prod)

    print("OK")
