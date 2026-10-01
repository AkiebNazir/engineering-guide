"""
================================================================================
SOLUTION · LLD 006 · In-Memory Key-Value Store with Nested Transactions  [Tier 1]
================================================================================

THE CORE IDEA
--------------
BEGIN / COMMIT / ROLLBACK can nest. There are two honest designs, and a strong
candidate names both and picks one on purpose:

    A. LAYERED WRITE-SETS (redo layers)
       Each open transaction is a dict of its own writes on a stack; deletes are
       TOMBSTONES (you can't just "not have" the key — that would reveal the
       value underneath). get() searches top-down: O(depth).
       rollback = pop a layer.  commit = merge the layer into the one below.

    B. UNDO LOG (write in place)
       Writes go straight into the one real dict, so get() is O(1). Each open
       transaction remembers the ORIGINAL value of every key it touched (first
       write only). rollback = restore those originals. commit = hand the undo
       entries to the parent, keeping the parent's older original if it already
       has one.

B is what databases do for the working copy and is the better default: reads
are far more common than rollbacks. Demo 2 measures get() at depth 2,000.

The easy wrong answer — deepcopy the whole store on BEGIN — is O(n) per BEGIN
and O(n x depth) memory. Demo 1 uses it only as a slow, obviously-correct
ORACLE to differential-test both real designs over 60,000 random operations.

count(value) ("how many keys hold this value", the Karat/Stripe NUMEQUALTO
twist) must stay O(1): keep a value -> count map updated on every write AND
every rollback restore.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. get(key) -> value or None; set(key, value); delete(key) -> existed?
  2. count(value) -> number of keys currently holding value, O(1).
  3. begin() opens a transaction, may nest.
  4. rollback() discards the innermost transaction's changes.
  5. commit() merges the innermost transaction into its parent (or into the
     store if outermost). A later parent rollback also undoes it.
  6. commit/rollback with no open transaction -> NoTransaction.
  7. Reads inside a transaction see its own writes (read-your-writes).
  Out of scope: concurrency between clients, persistence, TTLs.


================================================================================
ENTITIES AND INVARIANTS
================================================================================
    KVStore (undo log)       _data, _counts, _undo: [ {key: original | MISSING} ]
                             INVARIANT: applying every undo map from top to bottom
                             reproduces the state before the outermost BEGIN
                             INVARIANT: _counts[v] == #keys with value v
    LayeredKVStore           _base, _layers: [ {key: value | TOMBSTONE} ], _counts
                             INVARIANT: effective(k) = first layer from the top
                             containing k, else _base
    MISSING / TOMBSTONE      sentinels (None is not a legal value)


================================================================================
TRACE · undo log
================================================================================
    op              _data        _undo
    set a 10        {a:10}       []                    (no tx: nothing to log)
    begin           {a:10}       [{}]
    set a 20        {a:20}       [{a:10}]              first touch logs original
    set a 30        {a:30}       [{a:10}]              second touch: not logged again
    begin           {a:30}       [{a:10}, {}]
    delete a        {}           [{a:10}, {a:30}]
    set b 1         {b:1}        [{a:10}, {a:30, b:MISSING}]
    commit          {b:1}        [{a:10, b:MISSING}]   a already logged in parent -> keep 10
    rollback        {a:10}       []                    restores a=10, removes b


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
    Design              get       set     begin    rollback   commit     memory
    deepcopy on begin   O(1)      O(1)    O(n)     O(1)       O(1)*      O(n*d)
    layered write-sets  O(d)      O(d)**  O(1)     O(w)       O(w)       O(w)
    undo log            O(1)      O(1)    O(1)     O(w)       O(w)       O(w)
      n keys, d depth, w keys written in the transaction
      *  commit = discard the saved copy     ** set is O(d) only to keep count() exact

  * Undo log chosen. Layered is the right answer when transactions must NOT
    be visible to other readers (MVCC-ish snapshots) — say so.
  * Sentinels (MISSING, TOMBSTONE) are private objects, never None, so a key
    that was absent is distinguishable from any stored value.
  * Both implementations satisfy one contract and are tested by the SAME test
    function — the tests describe behaviour, not structure.


================================================================================
EDGE CASES
================================================================================
  * delete a missing key -> False, nothing logged.
  * set a key to the value it already has -> counts unchanged.
  * delete inside a tx, then rollback -> value and count restored.
  * create a key inside a tx, rollback -> key gone (not set to None).
  * nested commit then parent rollback -> both levels undone.
  * rollback/commit with no transaction -> NoTransaction, store untouched.
  * count of a value nobody holds -> 0 (and no zero entries left behind).


================================================================================
COMMON MISTAKES
================================================================================
  1. Deleting by removing from the top layer only (the base value reappears).
  2. Logging every write instead of the FIRST original per transaction.
  3. On nested commit, overwriting the parent's original with the child's.
  4. count() implemented by scanning all values.
  5. Forgetting counts on rollback.
  6. commit() committing ALL levels when nested semantics were agreed (or the
     reverse). Ask which one the interviewer wants.
  7. Using None both as "missing" and as a storable value.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Many concurrent clients -> per-client transactions need isolation: MVCC
    (versioned values + snapshot timestamps) or 2PL with key locks.
  * Durability -> write-ahead log of committed write-sets; replay on start.
  * TTL per key -> expires_at alongside value; lazy expiry on get + sweeper.
  * "COMMIT commits everything" semantics -> collapse all undo maps at once.
  * Range queries -> sorted container (skip list / B-tree) instead of dict.
  * Savepoints -> named positions in the undo stack.


================================================================================
RELATED
================================================================================
  SoftwareDesign/04_design_patterns_in_practice.md  §8 Command / Memento
  CSFundamentals databases (WAL, MVCC, undo/redo logging)
  PyDSA/25_design (snapshot array, time-based KV)
  lld/009_lru_lfu_cache (another O(1) data-structure-design problem)
"""

from __future__ import annotations

import copy
import random
import time
from collections import Counter
from typing import Hashable

MISSING = object()
TOMBSTONE = object()


class NoTransaction(Exception): ...


# ----------------------------------------------------------------------------
# Design B (chosen): write in place + undo log
# ----------------------------------------------------------------------------
class KVStore:
    def __init__(self) -> None:
        self._data: dict[Hashable, object] = {}
        self._counts: Counter = Counter()
        self._undo: list[dict[Hashable, object]] = []

    def get(self, key):
        return self._data.get(key)

    def set(self, key, value) -> None:
        if value is None:
            raise ValueError("None is not a storable value")
        self._log(key)
        self._write(key, value)

    def delete(self, key) -> bool:
        if key not in self._data:
            return False
        self._log(key)
        self._write(key, MISSING)
        return True

    def count(self, value) -> int:
        return self._counts.get(value, 0)

    def begin(self) -> None:
        self._undo.append({})

    def rollback(self) -> None:
        if not self._undo:
            raise NoTransaction("rollback")
        for key, original in self._undo.pop().items():
            self._write(key, original)

    def commit(self) -> None:
        if not self._undo:
            raise NoTransaction("commit")
        child = self._undo.pop()
        if self._undo:
            parent = self._undo[-1]
            for key, original in child.items():
                parent.setdefault(key, original)          # parent's older original wins

    @property
    def depth(self) -> int:
        return len(self._undo)

    def __len__(self) -> int:
        return len(self._data)

    def _log(self, key) -> None:
        if self._undo and key not in self._undo[-1]:
            self._undo[-1][key] = self._data.get(key, MISSING)

    def _write(self, key, value) -> None:
        old = self._data.get(key, MISSING)
        if old is not MISSING:
            self._counts[old] -= 1
            if not self._counts[old]:
                del self._counts[old]
        if value is MISSING:
            self._data.pop(key, None)
        else:
            self._data[key] = value
            self._counts[value] += 1


# ----------------------------------------------------------------------------
# Design A (alternative): stack of write-set layers with tombstones
# ----------------------------------------------------------------------------
class LayeredKVStore:
    def __init__(self) -> None:
        self._base: dict[Hashable, object] = {}
        self._layers: list[dict[Hashable, object]] = []
        self._counts: Counter = Counter()

    def get(self, key):
        value = self._lookup(key)
        return None if value is MISSING else value

    def set(self, key, value) -> None:
        if value is None:
            raise ValueError("None is not a storable value")
        self._put(key, value)

    def delete(self, key) -> bool:
        if self._lookup(key) is MISSING:
            return False
        self._put(key, TOMBSTONE)
        return True

    def count(self, value) -> int:
        return self._counts.get(value, 0)

    def begin(self) -> None:
        self._layers.append({})

    def rollback(self) -> None:
        if not self._layers:
            raise NoTransaction("rollback")
        top = self._layers.pop()
        for key, value in top.items():
            self._recount(old=value, new=self._lookup(key))

    def commit(self) -> None:
        if not self._layers:
            raise NoTransaction("commit")
        top = self._layers.pop()
        if self._layers:
            self._layers[-1].update(top)                  # tombstones carry down
        else:
            for key, value in top.items():
                if value is TOMBSTONE:
                    self._base.pop(key, None)
                else:
                    self._base[key] = value

    @property
    def depth(self) -> int:
        return len(self._layers)

    def __len__(self) -> int:
        keys = set(self._base)
        for layer in self._layers:
            keys |= layer.keys()
        return sum(1 for k in keys if self.get(k) is not None)

    def _lookup(self, key):
        for layer in reversed(self._layers):
            if key in layer:
                v = layer[key]
                return MISSING if v is TOMBSTONE else v
        return self._base.get(key, MISSING)

    def _put(self, key, value) -> None:
        self._recount(old=self._lookup(key), new=value)
        if self._layers:
            self._layers[-1][key] = value
        elif value is TOMBSTONE:
            self._base.pop(key, None)
        else:
            self._base[key] = value

    def _recount(self, old, new) -> None:
        if old not in (MISSING, TOMBSTONE):
            self._counts[old] -= 1
            if not self._counts[old]:
                del self._counts[old]
        if new not in (MISSING, TOMBSTONE):
            self._counts[new] += 1


# ===================================================================== TESTS ==
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


class DeepCopyOracle:
    """Slow but obviously correct: snapshot the whole dict on begin."""

    def __init__(self) -> None:
        self.data: dict = {}
        self.saved: list[dict] = []

    def get(self, k): return self.data.get(k)
    def set(self, k, v): self.data[k] = v
    def delete(self, k): return self.data.pop(k, None) is not None
    def count(self, v): return sum(1 for x in self.data.values() if x == v)
    def begin(self): self.saved.append(copy.deepcopy(self.data))

    def rollback(self):
        if not self.saved:
            raise NoTransaction
        self.data = self.saved.pop()

    def commit(self):
        if not self.saved:
            raise NoTransaction
        self.saved.pop()


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 60,000 random ops, both designs vs a deepcopy oracle ---")
    rng = random.Random(42)
    stores = [DeepCopyOracle(), KVStore(), LayeredKVStore()]
    mismatches = 0
    for _ in range(60_000):
        op = rng.random()
        key, value = rng.randrange(40), rng.randrange(6)
        results = []
        for s in stores:
            try:
                if op < 0.35:
                    results.append(s.set(key, value))
                elif op < 0.5:
                    results.append(s.delete(key))
                elif op < 0.62:
                    results.append(s.begin())
                elif op < 0.72:
                    results.append(s.rollback())
                elif op < 0.8:
                    results.append(s.commit())
                else:
                    results.append((s.get(key), s.count(value)))
            except NoTransaction:
                results.append("NoTransaction")
        if not (results[0] == results[1] == results[2]):
            mismatches += 1
    all_ok &= _check(f"every result identical across all three stores ({mismatches} mismatches)",
                     mismatches == 0)

    print("\n--- DEMO 2: cost of get() and begin() at depth 2,000 with 50,000 keys ---")
    n, depth, reads = 50_000, 2_000, 20_000
    timings = {}
    for make in (KVStore, LayeredKVStore, DeepCopyOracle):
        s = make()
        for i in range(n):
            s.set(i, i % 7)
        start = time.perf_counter()
        for d in range(depth if make is not DeepCopyOracle else 20):
            s.begin()
            s.set(d % n, 3)
        begin_s = time.perf_counter() - start
        start = time.perf_counter()
        for i in range(reads):
            s.get(n - 1 - i)                 # untouched keys: layered must search every layer
        get_s = time.perf_counter() - start
        timings[make.__name__] = (begin_s, get_s)
    u_begin, u_get = timings["KVStore"]
    l_begin, l_get = timings["LayeredKVStore"]
    c_begin, _ = timings["DeepCopyOracle"]
    print(f"      undo log : {depth} begins {u_begin * 1000:7.1f} ms   {reads} gets {u_get * 1000:8.1f} ms")
    print(f"      layered  : {depth} begins {l_begin * 1000:7.1f} ms   {reads} gets {l_get * 1000:8.1f} ms "
          f"({l_get / u_get:.0f}x slower reads)")
    print(f"      deepcopy : only 20 begins {c_begin * 1000:7.1f} ms "
          f"(~{c_begin / 20 * depth:.0f} s projected for {depth})")
    all_ok &= _check("undo-log reads beat layered reads at depth", u_get < l_get)
    all_ok &= _check("deepcopy begin costs more per call than the undo log", c_begin / 20 > u_begin / depth)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
