"""
================================================================================
SOLUTION · LeetCode 763 · Partition Labels                             [Medium]
https://leetcode.com/problems/partition-labels/
================================================================================

THE CORE IDEA
--------------
Precompute the LAST index at which each letter occurs anywhere in `s`. Then
scan left to right maintaining a running `end`, the farthest last-occurrence
index seen among all letters encountered SO FAR in the current partition.
Whenever the scan index reaches `end`, the current partition can safely
close right there — every letter seen since the last partition boundary has
now had its last occurrence accounted for, so no future index can force this
partition open again.

EXCHANGE ARGUMENT (why closing exactly at `end` gives the MAXIMUM number of
parts, i.e. is the greedy-optimal cut point)
-------------------------------------------------------------------
Claim: the earliest legal place to cut (index `end`, defined as the max of
`last[c]` for every letter `c` seen since the previous cut) is exactly where
you MUST cut to keep this partition valid, and cutting there is never worse
than cutting later. Proof of two parts:

1. **You cannot cut any earlier than `end`.** By definition, `end` is the
   last occurrence of some letter `c` that has already appeared in the
   current partition. If you cut before index `end`, that letter `c`'s
   later occurrence (at `end`) would fall into a DIFFERENT part than its
   earlier occurrence — violating "each letter appears in at most one
   part." So every valid cut point must be `>= end`.
2. **Cutting exactly at `end` (the earliest legal point) never produces
   fewer parts than cutting later.** Cutting later only means folding MORE
   letters into the current part (since between `end` and any later cut,
   more letters get absorbed into this same partition), which can only
   keep the same total part count or reduce it — it can never create an
   additional partition boundary that cutting earlier would have missed,
   because every legal partition boundary is itself a valid place to ALSO
   have cut earlier at an even smaller `end` if you'd tracked it (i.e. the
   greedy earliest-legal-cut sequence is a refinement of any other legal
   partition — every other valid partition's boundaries are a subset of
   points where "cut here" was legal, and the greedy schedule cuts at
   EVERY such earliest opportunity, so it produces the MAXIMUM number of
   parts, matching exactly what the problem asks for).

This is the same "always take the earliest safe opportunity" shape as
classic interval-partitioning arguments: maximizing the count of pieces is
achieved by never leaving a partition open longer than the minimum required.

================================================================================
APPROACH 0 · Brute force — try all possible cut point subsets (priced, not
coded)
================================================================================
Try every possible way to break `s` into contiguous parts (2^(n-1) possible
sets of cut points), check each for validity (no letter split across parts),
and keep the one with the most parts. Exponential; never the coded answer.

================================================================================
APPROACH 1 · Last-occurrence map + single greedy scan ✅ (the answer)
================================================================================
    def partitionLabels(s):
        last = {c: i for i, c in enumerate(s)}
        result = []
        start = end = 0
        for i, c in enumerate(s):
            end = max(end, last[c])
            if i == end:
                result.append(end - start + 1)
                start = i + 1
        return result

    Time:  O(n) — one pass to build `last`, one pass to scan (each letter
           has at most 26 distinct identities, but the map is built by
           index so it's O(n) regardless)
    Space: O(1) extra beyond the map (the map itself is O(26) = O(1) since
           the alphabet is fixed lowercase English letters; the output list
           is O(k) for k parts, not counted as "extra" working space)

================================================================================
APPROACH 2 · Interval merging (equivalent reframing, same complexity)
================================================================================
Reframe each letter as an interval `[first_occurrence, last_occurrence]`.
The answer is the number of parts after merging all OVERLAPPING intervals
(topic 19's interval-merge pattern) — two letters must share a part iff
their occurrence-spans overlap. Sort intervals by start, merge overlapping
ones exactly like the classic "merge intervals" problem, and the merged
groups' total lengths are the answer. Same O(n log n) or O(n) (if you avoid
an explicit sort by using the natural first-occurrence order) — Approach 1
is the more direct single-pass version of this same idea, avoiding building
explicit interval objects.

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
s = "ababcbacadefegdehijhklij"
     0123456789...

last-occurrence map (letter -> last index):
  a:8  b:5  c:7  d:14  e:15  f:11  g:13  h:19  i:22  j:23  k:20  l:21

  start=0, end=0
  i=0 'a': end=max(0,8)=8.   i==end? 0==8 no
  i=1 'b': end=max(8,5)=8.   1==8 no
  i=2 'a': end=max(8,8)=8.   2==8 no
  i=3 'b': end=max(8,5)=8.   3==8 no
  i=4 'c': end=max(8,7)=8.   4==8 no
  i=5 'b': end=max(8,5)=8.   5==8 no
  i=6 'a': end=max(8,8)=8.   6==8 no
  i=7 'c': end=max(8,7)=8.   7==8 no
  i=8 'a': end=max(8,8)=8.   8==8 YES -> part length = 8-0+1 = 9, start=9
  ---- first part closes: "ababcbaca" (length 9) ----

  i=9  'd': end=max(0,14)=14 -> using start=9 as new base (end init carries
       forward as a running value, but conceptually it's "farthest seen
       since start"); 9==14? no
  i=10 'e': end=max(14,15)=15
  i=11 'f': end=max(15,11)=15
  i=12 'e': end=max(15,15)=15
  i=13 'g': end=max(15,13)=15
  i=14 'd': end=max(15,14)=15
  i=15 'e': end=max(15,15)=15.  15==15 YES -> part length = 15-9+1 = 7, start=16
  ---- second part closes: "defegde" (length 7) ----

  i=16..23: 'h','i','j','h','k','l','i','j'
       end tracks up to max(19,22,23,19,20,21,22,23) = 23
  i=23: 23==end(23) YES -> part length = 23-16+1 = 8
  ---- third part closes: "hijhklij" (length 8) ----

  result = [9, 7, 8]   (matches expected output)

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                             | Time       | Space | Mutates input? |
|-------------------------------------------|-----------|-------|------------------|
| 0 · brute force (all cut subsets)         | O(2^n)    | O(n)  | No             |
| 1 · last-occurrence map + scan ✅          | O(n)      | O(1) extra (map bounded by alphabet size) | No |
| 2 · interval-merge reframing              | O(n) or O(n log n) if sorted | O(n) | No |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Every character unique (no repeats): every `end` equals its own index
  immediately, producing n parts of length 1 each.
- Every character the same (e.g. "aaaa"): `end` immediately jumps to the
  last index on the first character and never triggers a close until the
  very end — one part covering the whole string.
- Single-character string: trivially one part of length 1.
- A letter's two occurrences bracket the ENTIRE rest of the string (e.g.
  "a...a" with everything else unique in between and after): the whole
  string collapses into one part, since `end` locks onto that letter's
  last occurrence which is the final index.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. **Looks-greedy-but-wrong: closing a partition as soon as a letter seen
   earlier in it does NOT reappear for a while** (a "looks stable" local
   heuristic) — the only thing that matters is whether EVERY letter seen
   so far has had its FINAL occurrence accounted for, which requires the
   precomputed `last` map; you cannot safely guess "this partition is done"
   without knowing the true last-occurrence of every letter inside it.
2. Building the last-occurrence map INSIDE the same forward scan used to
   decide cuts (e.g. via a running `seen` dict updated as you go) —
   without precomputing last occurrences up front, you don't yet know
   whether a letter will reappear LATER, so you can't correctly decide
   `i == end` on the first pass; the two-pass (precompute, then scan) is
   required.
3. Off-by-one: computing part length as `end - start` instead of
   `end - start + 1` (both are 0-indexed inclusive boundaries).
4. Forgetting to reset `start = i + 1` after closing a partition, causing
   the next partition's length calculation to be wrong (it would include
   the previous partition's characters).

--------------------------------------------------------------------------------
RUNTIME DEMO — O(n) single pass vs. O(2^n) brute-force cut-subset search,
measured on this machine
--------------------------------------------------------------------------------
See the code below.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "Return the actual substrings, not just the lengths" — trivial extension:
  slice `s[start:end+1]` at each close instead of just appending the length.
- "What if the alphabet weren't fixed/small (e.g. arbitrary Unicode)?" —
  the last-occurrence map just needs to be a general hashmap keyed by
  character instead of a small fixed-size array; complexity is unchanged
  (still O(n) since there are at most n distinct characters in a string of
  length n).
- "How does this relate to merge intervals?" — see Approach 2; this
  problem is literally an interval-merge problem in disguise, which is why
  it lives conceptually next to topic 19 (Intervals) even though it's
  filed under greedy here.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- Topic 19 (Intervals) · Merge Intervals — the general version of the
  interval-overlap reasoning used in Approach 2.
- 18/007 Hand of Straights — same "sort/precompute, then a forced greedy
  scan" pattern family (topic guide §2.2).
================================================================================
"""

import random
import string
import time
from itertools import combinations


class Solution:
    def partitionLabels(self, s: str) -> list[int]:
        last = {c: i for i, c in enumerate(s)}
        result = []
        start = end = 0
        for i, c in enumerate(s):
            end = max(end, last[c])
            if i == end:
                result.append(end - start + 1)
                start = i + 1
        return result


def partition_labels_brute_force(s: str) -> list[int]:
    """Try every subset of cut points, keep the valid partition (no letter
    split across parts) with the MOST parts. Exponential -- oracle only."""
    n = len(s)
    best = None
    # cut points are positions 1..n-1 (before index i)
    positions = list(range(1, n))
    for r in range(len(positions), -1, -1):
        found = False
        for cuts in combinations(positions, r):
            bounds = [0] + list(cuts) + [n]
            parts = [s[bounds[i] : bounds[i + 1]] for i in range(len(bounds) - 1)]
            seen_letters = set()
            valid = True
            for part in parts:
                part_letters = set(part)
                if part_letters & seen_letters:
                    valid = False
                    break
                seen_letters |= part_letters
            if valid:
                best = [len(p) for p in parts]
                found = True
                break
        if found:
            break
    return best


def run_tests():
    sol = Solution()
    assert sol.partitionLabels("ababcbacadefegdehijhklij") == [9, 7, 8]
    assert sol.partitionLabels("eccbbbbdec") == [10]
    assert sol.partitionLabels("a") == [1]
    assert sol.partitionLabels("abcabc") == [6]
    assert sol.partitionLabels("abcdef") == [1, 1, 1, 1, 1, 1]

    # cross-check against exhaustive brute force on small random strings
    random.seed(41)
    for _ in range(60):
        n = random.randint(1, 7)
        s = "".join(random.choice("abc") for _ in range(n))
        assert sol.partitionLabels(s) == partition_labels_brute_force(
            s
        ), f"mismatch on s={s!r}"

    # --- Runtime demo: O(n) scan vs exponential brute force, measured ------
    random.seed(43)
    small_s = "".join(random.choice("abcd") for _ in range(16))

    t0 = time.perf_counter()
    fast_result = sol.partitionLabels(small_s)
    fast_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    slow_result = partition_labels_brute_force(small_s)
    slow_time = time.perf_counter() - t0

    assert fast_result == slow_result
    print(f"len(s)={len(small_s)}: O(n) scan took {fast_time*1000:.4f} ms")
    print(f"len(s)={len(small_s)}: brute-force cut search took {slow_time*1000:.2f} ms")
    print(f"greedy is {slow_time / fast_time:.1f}x faster on this run")
    assert fast_time < slow_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
