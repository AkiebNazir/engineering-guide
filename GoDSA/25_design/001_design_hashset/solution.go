package main

import "fmt"

/*
================================================================================
LeetCode 705 · Design HashSet                                             [Easy]
https://leetcode.com/problems/design-hashset/
Topic: 25 · Design
================================================================================

PROBLEM
-------
Design a HashSet WITHOUT using any built-in hash table libraries (no `set`,
no `dict`, no `collections.*`).

Implement the `MyHashSet` class:

    MyHashSet()               Initializes the object.
    add(key) -> None          Inserts `key` into the HashSet. No-op if
                               `key` already exists.
    remove(key) -> None       Removes `key` from the HashSet. No-op if
                               `key` does not exist.
    contains(key) -> bool     Returns True if `key` exists in the HashSet,
                               False otherwise.


EXAMPLES
--------
Example 1:
    Input:
        ["MyHashSet", "add", "add", "contains", "contains", "add",
         "contains", "remove", "contains"]
        [[], [1], [2], [1], [3], [2], [2], [2], [2]]
    Output:
        [null, null, null, true, false, null, true, null, false]

    Explanation:
        hs = MyHashSet()
        hs.add(1)          # {1}
        hs.add(2)          # {1, 2}
        hs.contains(1)     # True
        hs.contains(3)     # False (not added yet)
        hs.add(2)          # {1, 2}, no-op, 2 already present
        hs.contains(2)     # True
        hs.remove(2)       # {1}
        hs.contains(2)     # False (removed)


CONSTRAINTS
-----------
    0 <= key <= 10^6
    At most 10^4 calls will be made to add, remove, and contains.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is a DESIGN problem — you are hand-building the exact machinery Python's
`set`/`dict` hide behind `hash()`/`__eq__`. The banned-built-ins constraint
forces you to implement the two classic hash-table collision strategies
yourself: SEPARATE CHAINING (an array of buckets, each bucket a small list)
or OPEN ADDRESSING (one flat array, probe to the next slot on collision).

The key insight (topic guide Part 0): a hash TABLE is just an ARRAY plus a
function that maps a key to an array index, PLUS a collision-resolution
policy for when two different keys map to the same index. `key % bucket_count`
is your hash function here since keys are already integers.


WHAT TO THINK ABOUT
--------------------
1. `0 <= key <= 10^6` — a bucket count much smaller than 10^6 (e.g. a few
   thousand) keeps each bucket's average length small (load factor), which
   is what makes "O(1) average" true. A bucket count of exactly 1 would
   degrade every operation to O(n) — that's the naive baseline being ruled
   out.

2. Pick the bucket count as a PRIME number — reduces systematic collisions
   when keys share common factors with the bucket count (e.g. if keys are
   all multiples of 100 and the bucket count is 1000, only 10 buckets
   would ever be used).

3. Each bucket must support O(bucket length) insert/remove/contains — a
   plain Python list works, checking membership with `==`.


PROGRESSIVE HINTS
------------------
Hint 1: You need an array of "buckets." `hash(key) = key % NUM_BUCKETS`
        picks which bucket a key belongs to.

Hint 2: Each bucket must hold MULTIPLE keys (collisions happen) — a list
        per bucket, and add/remove/contains scan that one bucket's list.

Hint 3: Choosing `NUM_BUCKETS` close to (but not exceeding) the expected
        number of calls keeps each bucket's list short — average bucket
        length stays close to 1, which is what makes operations "O(1)
        average" rather than a fixed guarantee.


COMPLEXITY TARGET
------------------
    add / remove / contains:  O(1) average time (with a well-chosen
                               bucket count and hash function)
    Space: O(n + b)  where n = number of keys stored, b = bucket count
================================================================================
*/

func main() {
	fmt.Println("Solution for Design HashSet not implemented yet")
}
