package main

import "fmt"

/*
================================================================================
LeetCode 380 · Insert Delete GetRandom O(1)                             [Medium]
https://leetcode.com/problems/insert-delete-getrandom-o1/
Topic: 25 · Design
================================================================================

PROBLEM
-------
Implement the `RandomizedSet` class:

    RandomizedSet()             Initializes the object (empty set).
    insert(val) -> bool         Inserts `val` if not already present.
                                 Returns True if it was NOT present
                                 (inserted), False otherwise.
    remove(val) -> bool         Removes `val` if present. Returns True if
                                 it WAS present (removed), False otherwise.
    getRandom() -> int          Returns a random element from the current
                                 set of elements, with EACH element having
                                 EQUAL probability of being returned.

All three operations must run in O(1) AVERAGE time complexity.


EXAMPLES
--------
Example 1:
    Input:
        ["RandomizedSet", "insert", "remove", "insert", "getRandom",
         "remove", "insert", "getRandom"]
        [[], [1], [2], [2], [], [1], [2], []]
    Output:
        [null, true, false, true, 2, true, false, 2]

    Explanation:
        rs = RandomizedSet()
        rs.insert(1)      # {1}, returns True (1 was absent)
        rs.remove(2)      # {1}, returns False (2 was absent)
        rs.insert(2)      # {1, 2}, returns True
        rs.getRandom()    # returns 1 or 2, each with probability 1/2
        rs.remove(1)      # {2}, returns True
        rs.insert(2)      # {2}, returns False (2 already present)
        rs.getRandom()    # returns 2 (only element)


CONSTRAINTS
-----------
    -2^31 <= val <= 2^31 - 1
    At most 2 * 10^5 calls total will be made to insert, remove, and
    getRandom.
    There will be at least one element when getRandom is called.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is the problem that makes the "combine two data structures for
complementary strengths" pattern (topic guide Part 0) unavoidable, in a
DIFFERENT direction than LRU Cache:

    - A hash SET alone gives O(1) insert/remove/contains, but has NO
      notion of "the k-th element" — you cannot pick a UNIFORMLY random
      element from a set in O(1); Python's `set` has no indexing, and
      `random.choice(list(my_set))` is O(n) just to materialize the list.
    - A plain ARRAY (list) gives O(1) random access by index (so
      `getRandom` is trivial: `arr[random.randrange(len(arr))]`), but
      arbitrary-value REMOVAL from an array is O(n) — you'd need to find
      the value first (O(n) scan) and then shift everything after it
      (O(n) more).

The fix: an ARRAY (for O(1) random access) PLUS a dict mapping `value ->
index in the array` (for O(1) lookup), and — the key trick — deletion by
SWAP-WITH-LAST-THEN-POP instead of shifting: move the last element into
the gap left by the removed value, update that moved element's index in
the dict, then pop the array's now-redundant last slot. This avoids ANY
O(n) shifting.


WHAT TO THINK ABOUT
--------------------
1. The dict stores `value -> index`, mirroring the array; both structures
   must be updated together on every insert/remove, or they silently
   disagree (same "keep two structures in sync" discipline as LRU Cache).

2. Swap-with-last-then-pop is the O(1) deletion trick: removing `arr[i]` by
   `arr[i], arr[-1] = arr[-1], arr[i]` THEN `arr.pop()` avoids shifting
   every element after index `i` — but only correct if you ALSO update the
   dict entry for whichever value just got moved into position `i`.

3. Special case: removing the LAST element of the array (swapping it with
   itself) must not corrupt the dict — swapping an element with itself is
   harmless, but it's worth tracing explicitly since it's the boundary
   case most implementations get wrong first.

4. `getRandom` must give EACH element equal probability — indexing
   uniformly into the array (`random.randrange(len(arr))`) does this
   automatically since the array holds no gaps/tombstones (this is
   precisely why swap-pop, not "clear the slot," is required).


PROGRESSIVE HINTS
------------------
Hint 1: A set alone can't give O(1) random access; an array alone can't
        give O(1) removal by value. You need BOTH: an array plus a
        value->index dict.

Hint 2: To delete `val` in O(1): look up its index via the dict, swap the
        element AT THAT INDEX with the array's LAST element, update the
        moved element's index in the dict, then pop the array's last slot.

Hint 3: Never leave a "hole" in the array (no `None` placeholders, no
        tombstones) — `getRandom` needs the array to be fully dense so a
        uniform random INDEX gives a uniform random ELEMENT.


COMPLEXITY TARGET
------------------
    insert / remove / getRandom:  O(1) average time
    Space: O(n)
================================================================================
*/

func main() {
	fmt.Println("Solution for Insert Delete GetRandom O(1) not implemented yet")
}
