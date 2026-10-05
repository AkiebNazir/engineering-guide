"""
================================================================================
LLD 006 · In-Memory Key-Value Store with Nested Transactions       [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Implement an in-memory key-value store that supports nested transactions.

This is a Karat / Stripe / Google favourite, often phrased as "a mini Redis
with BEGIN, ROLLBACK and COMMIT". These are the agreed requirements.

REQUIREMENTS
------------
  1. get(key) -> value, or None if absent.
     set(key, value). value=None raises ValueError.
     delete(key) -> True if the key existed, else False.
  2. count(value) -> how many keys currently hold `value`, in O(1).
  3. begin() opens a transaction. Transactions nest.
  4. rollback() undoes everything done since the innermost begin().
  5. commit() folds the innermost transaction into its parent (or into the
     store if it was outermost). If the parent is later rolled back, the
     committed child's changes are undone too.
  6. commit() / rollback() with no open transaction raise NoTransaction and
     change nothing.
  7. depth -> number of open transactions. len(store) -> number of live keys.
  8. Inside a transaction, reads see that transaction's writes.

  Implement it TWICE, behind the same API:
     KVStore         write in place + an undo log per transaction
     LayeredKVStore  a stack of write-set layers (deletes need tombstones)
  The tests run the same contract against both.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * How is a delete inside a transaction represented?
  * Complexity of get, set, begin, commit, rollback for each design.
  * Why is "copy the whole dict on begin" a poor answer?
  * How does count() stay O(1) through rollbacks?
  * On nested commit, whose "original value" wins?

FOLLOW-UPS TO PREPARE
---------------------
  concurrent clients (isolation) · durability · TTLs · "commit everything"
  semantics · range queries · savepoints.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations


class NoTransaction(Exception): ...


class KVStore:
    """Design B: write in place, undo log per transaction."""

    def __init__(self) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def get(self, key): raise NotImplementedError
    def set(self, key, value) -> None: raise NotImplementedError
    def delete(self, key) -> bool: raise NotImplementedError
    def count(self, value) -> int: raise NotImplementedError
    def begin(self) -> None: raise NotImplementedError
    def rollback(self) -> None: raise NotImplementedError
    def commit(self) -> None: raise NotImplementedError

    @property
    def depth(self) -> int: raise NotImplementedError

    def __len__(self) -> int: raise NotImplementedError


class LayeredKVStore:
    """Design A: stack of write-set layers with tombstones."""

    def __init__(self) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def get(self, key): raise NotImplementedError
    def set(self, key, value) -> None: raise NotImplementedError
    def delete(self, key) -> bool: raise NotImplementedError
    def count(self, value) -> int: raise NotImplementedError
    def begin(self) -> None: raise NotImplementedError
    def rollback(self) -> None: raise NotImplementedError
    def commit(self) -> None: raise NotImplementedError

    @property
    def depth(self) -> int: raise NotImplementedError

    def __len__(self) -> int: raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _raises(exc, fn) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def run_contract(make) -> bool:
    all_ok = True
    name = make.__name__
    s = make()
    s.set("a", 10)
    s.set("b", 10)
    all_ok &= _check(f"[{name}] get / count", s.get("a") == 10 and s.count(10) == 2)
    s.set("b", 10)
    all_ok &= _check(f"[{name}] re-setting the same value doesn't double count", s.count(10) == 2)
    all_ok &= _check(f"[{name}] delete existing -> True, missing -> False",
                     s.delete("b") is True and s.delete("zz") is False and s.count(10) == 1)
    all_ok &= _check(f"[{name}] missing key -> None", s.get("b") is None)

    s.begin()
    s.set("a", 20)
    s.set("c", 20)
    all_ok &= _check(f"[{name}] read-your-writes inside a transaction",
                     s.get("a") == 20 and s.count(20) == 2 and s.count(10) == 0)
    s.rollback()
    all_ok &= _check(f"[{name}] rollback restores values, removes created keys, fixes counts",
                     s.get("a") == 10 and s.get("c") is None and s.count(10) == 1 and s.count(20) == 0)

    s.begin()
    s.delete("a")
    all_ok &= _check(f"[{name}] delete inside tx hides the value", s.get("a") is None and s.count(10) == 0)
    s.rollback()
    all_ok &= _check(f"[{name}] ...rollback brings it back", s.get("a") == 10 and s.count(10) == 1)

    print(f"--- [{name}] nesting (the docstring trace) ---")
    s = make()
    s.set("a", 10)
    s.begin()
    s.set("a", 20)
    s.set("a", 30)
    s.begin()
    s.delete("a")
    s.set("b", 1)
    s.commit()
    all_ok &= _check(f"[{name}] after inner commit: a deleted, b=1, depth 1",
                     s.get("a") is None and s.get("b") == 1 and s.depth == 1)
    s.rollback()
    all_ok &= _check(f"[{name}] parent rollback undoes the committed child too",
                     s.get("a") == 10 and s.get("b") is None and s.depth == 0 and len(s) == 1)

    s.begin()
    s.begin()
    s.set("x", 5)
    s.commit()
    s.commit()
    all_ok &= _check(f"[{name}] two commits persist to the store",
                     s.get("x") == 5 and s.depth == 0 and s.count(5) == 1)
    all_ok &= _check(f"[{name}] commit / rollback without a transaction -> NoTransaction",
                     _raises(NoTransaction, s.commit) and _raises(NoTransaction, s.rollback)
                     and s.get("x") == 5)
    all_ok &= _check(f"[{name}] None is not storable", _raises(ValueError, lambda: s.set("k", None)))
    return all_ok


def run_tests() -> bool:
    print("--- contract tests run against BOTH designs ---")
    ok = run_contract(KVStore)
    print()
    ok &= run_contract(LayeredKVStore)
    return ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
