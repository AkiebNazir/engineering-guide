"""
================================================================================
SOLUTION · LeetCode 341 · Flatten Nested List Iterator                  [Medium]
https://leetcode.com/problems/flatten-nested-list-iterator/
================================================================================

THE CORE IDEA
--------------
Each `NestedInteger` is either a leaf (an int, the base case) or a branch
(a list, needing one recursive call PER child, not just one). Flattening
is a depth-first traversal, structurally identical to a tree's DFS except
a "node" here can have any number of children — the first genuinely
TREE-shaped (multi-way branching) recursion in this folder, versus the
purely linear recursions in 001-008.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. EAGER — recursively flatten the entire structure into a plain list
   INSIDE THE CONSTRUCTOR, then serve `next()`/`hasNext()` off a simple
   index pointer. O(n) time and space up front (n = total integers),
   O(1) per `next()`/`hasNext()` call after that. Simple, and the version
   taught here.
2. LAZY, EXPLICIT STACK — push the top-level items onto a stack in
   REVERSE order; `hasNext()` repeatedly peeks the top, and if it's a
   list, pops it and pushes its children in reverse order, until the top
   is an actual integer (or the stack is empty). This defers work until
   it's needed and uses only O(depth) extra space instead of O(n) — the
   answer to "what if the caller stops early / the list is huge."
3. LAZY, RECURSIVE GENERATOR — a Python generator function that `yield`s
   integers via recursive delegation (`yield from flatten(child)`),
   wrapped so `next()`/`hasNext()` pull from it one value at a time with
   a one-element lookahead buffer. Conceptually lazy like approach 2, but
   leans on Python's generator machinery instead of an explicit stack.


================================================================================
STEP BY STEP TRACE — flatten([[1,1], 2, [1,1]])
================================================================================
    call flatten([[1,1], 2, [1,1]])
      item 0: [1,1] is a LIST -> call flatten([1,1])
        item 0: 1 is an INTEGER -> append 1          -> [1]
        item 1: 1 is an INTEGER -> append 1          -> [1, 1]
        return [1, 1]
      extend result with [1, 1]                      -> [1, 1]
      item 1: 2 is an INTEGER -> append 2             -> [1, 1, 2]
      item 2: [1,1] is a LIST -> call flatten([1,1]) -> [1, 1]  (same as above)
      extend result with [1, 1]                      -> [1, 1, 2, 1, 1]
    return [1, 1, 2, 1, 1]

Three total calls to `flatten` (top-level + 2 sub-lists), each doing ONE
call per LIST element it owns — the branching factor is "however many
elements are in this list," not a fixed 2 as with a binary tree.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time (total)  Space          Mutates input?  Note
    ----------------------------  ------------  -------------  ---------------  --------------------------------
    Eager (recursive flatten)    O(n)          O(n) upfront   no               O(1) per next()/hasNext() after
    Lazy, explicit stack          O(n) total    O(depth)       no               work spread across next() calls
    Lazy, recursive generator     O(n) total    O(depth)       no               same idea via Python generators


================================================================================
EDGE CASES
================================================================================
    [[]]              -> []    a list containing only an EMPTY list — no
                                integers anywhere; `hasNext()` must
                                correctly report False immediately, not
                                crash on an empty inner list.
    [[[[]]], 1]        -> [1]   deeply nested empty structure followed by
                                one real integer — exercises the base
                                case at real depth without producing
                                spurious output.
    a single bare integer at the top level (e.g. [5]) -> [5]  the
                                simplest possible non-empty case, exists
                                to confirm the top-level list itself is
                                handled the same way as any nested one.
    calling hasNext() multiple times in a row without calling next()
                       -> must be idempotent (not advance the pointer /
                                pop the stack) — this is the classic bug
                                in the lazy stack version specifically.


================================================================================
COMMON MISTAKES
================================================================================
1. In the LAZY stack version, having `hasNext()` mutate the stack (pop
   list-items and push their children) WITHOUT checking whether the
   result is already sitting at an integer — calling `hasNext()` twice
   in a row without an intervening `next()` must be safe and return the
   same answer both times, not silently advance past an element.
2. Pushing a list's children onto the stack in FORWARD order instead of
   REVERSE order in the lazy version — a stack pops last-in-first-out,
   so pushing `[a, b, c]` in forward order yields them back as `c, b, a`,
   reversing the intended left-to-right traversal order.
3. In the eager version, calling `.getList()` on something that's
   actually an integer (or vice versa) — always check `.isInteger()`
   FIRST and branch on that; the two accessor methods are only valid for
   their matching kind.
4. Treating this as a BINARY tree problem (only ever recursing on two
   fixed children) instead of recognizing the branching factor is
   "however many elements are in this list" — leads to code that only
   handles the first two elements of any nested list correctly.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if `nestedList` were huge and the caller might call `hasNext()`
   without ever draining it fully — does the eager approach waste work?
A: Yes — it pays the full O(n) flattening cost even if only one `next()`
   is ever called. The lazy stack version only does as much unwrapping
   as is needed to answer each `hasNext()`/`next()` call.

Q: Can you implement this without recursion at all?
A: Yes — the lazy explicit-stack version has no recursive calls; the
   stack itself plays the role the call stack would have played,
   managed manually.

Q: How would you extend this to support `peek()` (see the next integer
   without consuming it) in the lazy version?
A: `hasNext()` already has to advance the stack until the top is an
   integer to answer truthfully — once it has, that integer is simply
   `stack[-1].getInteger()`; `peek()` is `hasNext()` followed by reading
   without popping.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 10 Binary Trees (topic-level)   — DFS traversal with exactly 2
                                            children per node instead of
                                            an arbitrary count.
    LC 385  Mini Parser                   — parsing the SAME kind of
                                            nested structure from a raw
                                            string, recursion for parsing
                                            instead of flattening.
    Topic 13 Trie (Prefix Tree)           — another "arbitrary branching
                                            factor per node" recursive
                                            structure.
================================================================================
"""

from typing import List


class NestedInteger:
    def __init__(self, value=None, nested_list=None):
        self._value = value
        self._list = nested_list if nested_list is not None else []

    def isInteger(self) -> bool:
        return self._value is not None

    def getInteger(self) -> int:
        return self._value

    def getList(self) -> List["NestedInteger"]:
        return self._list


def _build(raw):
    if isinstance(raw, int):
        return NestedInteger(value=raw)
    return NestedInteger(nested_list=[_build(x) for x in raw])


class NestedIterator:
    """Eager: flatten fully at construction. O(n) up front, O(1) per call."""

    def __init__(self, nestedList: List[NestedInteger]):
        self._data = self._flatten(nestedList)
        self._index = 0

    def _flatten(self, nested_list: List[NestedInteger]) -> List[int]:
        result = []
        for item in nested_list:
            if item.isInteger():
                result.append(item.getInteger())
            else:
                result.extend(self._flatten(item.getList()))
        return result

    def next(self) -> int:
        value = self._data[self._index]
        self._index += 1
        return value

    def hasNext(self) -> bool:
        return self._index < len(self._data)


class NestedIteratorLazyStack:
    """Lazy: explicit stack, unwraps only as far as needed. O(depth) space."""

    def __init__(self, nestedList: List[NestedInteger]):
        self._stack = list(reversed(nestedList))

    def hasNext(self) -> bool:
        while self._stack and not self._stack[-1].isInteger():
            top = self._stack.pop()
            self._stack.extend(reversed(top.getList()))
        return bool(self._stack)

    def next(self) -> int:
        self.hasNext()  # ensure the top is an integer before popping
        return self._stack.pop().getInteger()


# ==============================================================================
# TESTS — run:  python 009_flatten_nested_list_iterator_solution.py
# ==============================================================================
def drain(cls, nested_raw):
    it = cls([_build(x) for x in nested_raw])
    out = []
    while it.hasNext():
        out.append(it.next())
    return out


CASES = [
    ([[1, 1], 2, [1, 1]], [1, 1, 2, 1, 1]),
    ([1, [4, [6]]], [1, 4, 6]),
    ([[]], []),
    ([[[[]]], 1], [1]),
    ([5], [5]),
]


def run_tests() -> None:
    all_ok = True

    impls = [
        ("eager (recursive flatten)", NestedIterator),
        ("lazy (explicit stack)    ", NestedIteratorLazyStack),
    ]

    for name, cls in impls:
        ok = True
        for nested_raw, expected in CASES:
            got = drain(cls, nested_raw)
            ok &= got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- redundant hasNext() calls don't advance the lazy iterator, measured live ---")
    it = NestedIteratorLazyStack([_build(x) for x in [[1, [2]], 3]])
    calls = [it.hasNext(), it.hasNext(), it.hasNext()]
    first = it.next()
    ok = calls == [True, True, True] and first == 1
    all_ok &= ok
    print(f"  {'PASS' if ok else 'FAIL'}  triple hasNext() -> {calls}, then next() -> {first}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
