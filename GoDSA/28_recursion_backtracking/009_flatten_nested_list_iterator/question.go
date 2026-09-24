package main

/*
================================================================================
LeetCode 341 · Flatten Nested List Iterator                             [Medium]
https://leetcode.com/problems/flatten-nested-list-iterator/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
You are given a nested list of integers `nestedList`. Each element is
either an integer, or a list whose elements may also be integers or other
lists. Design an iterator to flatten it.

Implement the `NestedIterator` class:
- `NestedIterator(nestedList)` initializes the iterator with the nested
  list `nestedList`.
- `int next()` returns the next integer in the nested list.
- `boolean hasNext()` returns `true` if there are still some integers in
  the nested list and `false` otherwise.

Your code will be tested with the following pseudocode:
    initialize iterator with nestedList
    res = []
    while iterator.hasNext():
        append iterator.next() to res
    if res matches the expected flattened list, then your code is judged
    correct.

EXAMPLES
--------
Example 1:
    Input:  nestedList = [[1,1],2,[1,1]]
    Output: [1,1,2,1,1]
    Explanation: By calling next repeatedly until hasNext returns false,
    the order of elements returned by next matches the order above.

Example 2:
    Input:  nestedList = [1,[4,[6]]]
    Output: [1,4,6]
    Explanation: By calling next repeatedly until hasNext returns false,
    the order of elements returned by next should be: 1, 4, 6.

CONSTRAINTS
-----------
    1 <= nestedList.length <= 1000
    The values of the integers in the nested list is in the range
    [-10^6, 10^6].

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is TREE recursion (not linear) for the first time in this folder: a
`NestedInteger` is either a leaf (an int) or a branch (a list of more
`NestedInteger`s), and flattening means visiting every leaf in order —
exactly a depth-first traversal, using the SAME recursive shape as a
binary tree's in-order traversal, except each "node" can have any number
of children instead of exactly two.

    flatten(nestedList) -> list of ints:
        result = []
        for item in nestedList:
            if item.isInteger():
                result.append(item.getInteger())        <- leaf: collect it
            else:
                result.extend(flatten(item.getList()))   <- branch: recurse, then splice in
        return result

The iterator interface (`next`/`hasNext`) is just this flattened list
served up one element at a time from an internal pointer/queue — the
recursion happens ENTIRELY at construction time in the simplest design;
a LAZY design (recursing only as far as needed before each `next()` call)
is the harder, more space-efficient follow-up.

WHAT TO THINK ABOUT
--------------------
1. What are the two "kinds" of thing you can encounter while flattening,
   and which one is the base case? (An integer needs no recursion; a
   list needs one recursive call PER ELEMENT, not just one call total —
   this is genuine tree/multi-way branching, unlike everything before it
   in this folder.)
2. If you flatten everything eagerly in the constructor, what does
   `next()` and `hasNext()` become? (Trivial index/pointer bookkeeping
   over a precomputed flat list.)
3. The eager approach is O(n) extra space up front even if the caller
   only ever calls `next()` once — what would a LAZY version look like,
   and when would it matter? (When `nestedList` is huge and the caller
   might stop early.)
4. How is this the same shape as a tree traversal, concretely? Map
   "leaf" and "branch" here onto "leaf node" and "internal node" in a
   binary tree.

PROGRESSIVE HINTS
------------------
Hint 1: In the constructor, walk `nestedList` and recursively flatten
        every element into one flat Python list of ints, stored as
        `self._data`.
Hint 2: For each element: if `.isInteger()`, append its value; else,
        recursively flatten `.getList()` and extend the result with it.
Hint 3: Keep an `self._index` pointer starting at 0. `hasNext()` is
        `self._index < len(self._data)`. `next()` returns
        `self._data[self._index]` then increments the pointer.
Hint 4: For the lazy follow-up: use an explicit STACK of iterators
        (pushed in reverse order) instead of recursion, popping/peeking
        to find the next actual integer only when `hasNext()` is called —
        this defers work until it's actually needed.

COMPLEXITY TARGET
------------------
    Eager (recursive flatten at construction): O(n) time & space up front,
                                                 O(1) per next()/hasNext()
    Lazy (explicit stack):                      O(n) total work across the
                                                 whole traversal, but work
                                                 is spread out — O(depth)
                                                 space instead of O(n)
================================================================================
*/

// TODO: Implement the stub
