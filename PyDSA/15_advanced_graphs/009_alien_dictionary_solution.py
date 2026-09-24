"""
================================================================================
SOLUTION · LeetCode 269 · Alien Dictionary                              [Hard]
https://leetcode.com/problems/alien-dictionary/
================================================================================

THE CORE IDEA
--------------
Every ADJACENT pair of words gives at most one ordering constraint: walk
both words together to the first differing character; that pair of
characters (earlier -> later) is a directed edge in the alien alphabet's
ordering graph. Collect all such edges, then topologically sort
(topic guide Part 7) -- Kahn's BFS is the right choice here because it
detects a cycle (contradictory ordering) as a natural side effect of not
being able to drain the whole queue.

    build indegree + adjacency from every adjacent-word-pair's first diff
    order = Kahn's BFS topological sort
    return "".join(order) if len(order) == number of distinct letters else ""

O(C) to scan all characters (C = total input length) + O(V+E) for the
sort, where V,E are bounded by the 26-letter alphabet.


================================================================================
THE PREFIX TRAP -- A SEPARATE FAILURE MODE FROM A CYCLE
================================================================================
["abc", "ab"]: walking together, EVERY character matches up to the shorter
word's length (a==a, b==b) and there is NO differing character at all --
"ab" is a complete prefix of "abc". For "abc" to correctly sort BEFORE
"ab" would require "ab" to somehow be "less than" its own prefix, which is
impossible under any consistent alphabet (a string is never less than its
own strict prefix in dictionary order, by definition). This is INVALID and
must return "" -- but it is not a cycle in the graph; no edge is even
generated from this pair. It must be checked explicitly: if the SHORTER
word is a prefix of the LONGER word, the SHORTER one must come FIRST, or
the input itself is already self-contradictory before any topological sort
runs. Missing this check is the single most common way this problem is
gotten wrong (demoed live below).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): try every permutation of
the letters that appear, check if it's consistent with every adjacent word
pair. O(26!) or O(k!) for k distinct letters -- absurd past k ~ 10.

Approach 1 (Kahn's BFS topological sort) [checked] -- the answer above.
Detects a cycle naturally: if the queue drains before every letter has
been dequeued, some letters never reached indegree 0, meaning they're
stuck in a cycle of mutual constraints.

Approach 2 (DFS-based topological sort with a 3-color cycle check) --
equally valid; requires an explicit WHITE/GRAY/BLACK visited-state array
to detect a back-edge (a GRAY node being revisited mid-recursion) as the
cycle signal, since a plain visited/unvisited DFS cannot distinguish "already
fully explored, fine" from "currently on the recursion stack, this is a
cycle." Kahn's is preferred here specifically because the cycle check
falls out for free (count of ordered letters < total letters) rather than
needing a dedicated three-state tracker.


================================================================================
STEP BY STEP TRACE
================================================================================
words = ["wrt","wrf","er","ett","rftt"]

Adjacent pairs -> edges (first differing character):
    "wrt" vs "wrf": w==w, r==r, t!=f -> edge t -> f
    "wrf" vs "er":  w!=e             -> edge w -> e
    "er"  vs "ett": e==e, r!=t       -> edge r -> t
    "ett" vs "rftt": e!=r            -> edge e -> r

All letters appearing: {w,r,t,f,e}  (5 distinct letters)
adjacency: t->f, w->e, r->t, e->r
indegree:  w:0, e:1(from w), r:1(from e), t:1(from r), f:1(from t)

Kahn's BFS:
    queue = [w]  (only indegree-0 letter)
    pop w, order=[w]. neighbor e: indegree[e] 1->0, push e. queue=[e]
    pop e, order=[w,e]. neighbor r: indegree[r] 1->0, push r. queue=[r]
    pop r, order=[w,e,r]. neighbor t: indegree[t] 1->0, push t. queue=[t]
    pop t, order=[w,e,r,t]. neighbor f: indegree[f] 1->0, push f. queue=[f]
    pop f, order=[w,e,r,t,f]. no neighbors. queue=[]

order length 5 == 5 distinct letters -> valid.
result = "wertf"   MATCHES expected output.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time                Space  Mutates input?
    -------------------------------------  ------------------  -----  --------------
    Brute-force permutation check          O(k! * C)           O(k)    no
    Kahn's BFS topological sort [chosen]   O(C + V + E)        O(26)   no
    DFS + 3-color cycle detection          O(C + V + E)        O(26)   no


================================================================================
EDGE CASES
================================================================================
    single word                 -> no adjacent pairs to compare -> zero
                                   edges. Every letter that appears has
                                   indegree 0. Any order of its distinct
                                   letters is valid -- Kahn's naturally
                                   returns them in whatever order they were
                                   registered (all tied at indegree 0).
    a word appearing twice        -> comparing it to itself as an "adjacent
    consecutively, identical        pair" finds no differing character
                                   and neither is longer -- no edge, no
                                   contradiction, harmless no-op pair.
    strict prefix in the WRONG    -> Example: ["abc","ab"] -- explicit
    order (longer, then shorter)    invalid check required (see prose
                                   above). Demoed live below.
    strict prefix in the RIGHT     -> ["ab","abc"] -- perfectly valid, no
    order (shorter, then longer)    edge needed at all since one is simply
                                   an extension of the other in the
                                   already-correct direction.
    a genuine CYCLE in the        -> Example 3: ["z","x","z"] derives z->x
    derived constraints             from the first pair and x->z from the
                                   second -- mutually contradictory. Kahn's
                                   queue drains with fewer than the total
                                   distinct-letter count dequeued -> "".
    letters that never appear      -> only build indegree/adjacency entries
    in ANY word                     for letters actually seen in `words` --
                                   never assume all 26 letters are present.
    multiple valid orderings        -> when several letters are mutually
    (weakly-ordered result)          unconstrained (tied at indegree 0
                                   simultaneously), ANY consistent order
                                   among them is accepted -- LeetCode's
                                   judge checks constraint-consistency, not
                                   a single fixed string.


================================================================================
COMMON MISTAKES
================================================================================
1. Never checking the prefix-order case at all -- ["abc","ab"] silently
   produces SOME topological order of the letters {a,b,c} (since no
   contradictory edge was ever generated) even though the input is
   provably invalid. Demoed live below.

2. Generating an edge for EVERY differing character position instead of
   stopping at the FIRST one. "wrt" vs "wrf" only tells you t comes before
   f -- continuing to compare characters past the first difference (there
   are none left to compare here, but in general) would be meaningless,
   since dictionary order is determined entirely by the first point of
   difference.

3. Building indegree/adjacency for all 26 letters unconditionally instead
   of only the letters that appear in `words`. Not fatal by itself (unused
   indegree-0 letters would just get appended to the order), but corrupts
   the "order length == number of distinct letters actually present"
   cycle-check invariant, silently masking real cycles or falsely
   flagging valid input as invalid.

4. Using DFS-based topological sort with only a plain visited/unvisited
   boolean instead of a three-state (white/gray/black) tracker --
   incorrectly treats "currently being explored, on the call stack" the
   same as "fully explored, safe," which fails to detect some cycles.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the dictionary had MULTIPLE valid orderings -- how would you
   return a specific canonical one, e.g. lexicographically smallest?
A: Swap Kahn's plain queue for a min-heap of ready (indegree-0) letters --
   at every step, pop the SMALLEST available letter first instead of an
   arbitrary FIFO order. Still O((V+E) log V) due to the heap.

Q: How would you validate a NEW word against an already-derived alien
   ordering?
A: Once you have the order, build a position-index map (letter -> rank)
   and compare the new word's characters positionally against its
   neighbors using that rank instead of raw character comparison --
   exactly what the test harness's `valid_order` helper does here.

Q: What's the actual worst-case input size, and does the algorithm scale?
A: Up to 100 words of up to 100 characters each -- 10^4 characters total
   to scan for edges, but at most 26 letters and ~325 possible edges in
   the graph itself; the topological sort step is trivially fast
   regardless of how many words there are.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 207  Course Schedule (topic 14 -- Kahn's BFS topological sort, plain)
    LC 210  Course Schedule II (topic 14 -- returning the order itself)
    LC 953  Verifying an Alien Dictionary (the EASY inverse of this problem
            -- order is GIVEN, just check words are sorted by it)
    LC 936  Stamping The Sequence (a different, harder use of reverse
            construction, unrelated algorithm but similar "derive
            something from a sequence of strings" flavor)
================================================================================
"""

from collections import defaultdict, deque
from typing import List


class Solution:
    def alienOrder(self, words: List[str]) -> str:
        """✅ Kahn's BFS topological sort over derived first-difference
        edges, with the explicit prefix-order validity check.
        O(C + V + E) time, O(26) space."""
        letters = set()
        for w in words:
            letters.update(w)

        adj = defaultdict(set)
        indegree = {ch: 0 for ch in letters}

        for a, b in zip(words, words[1:]):
            min_len = min(len(a), len(b))
            found_diff = False
            for i in range(min_len):
                if a[i] != b[i]:
                    if b[i] not in adj[a[i]]:
                        adj[a[i]].add(b[i])
                        indegree[b[i]] += 1
                    found_diff = True
                    break
            if not found_diff and len(a) > len(b):
                # "abc" before "ab" -- a longer word cannot precede its
                # own strict prefix in any valid ordering.
                return ""

        queue = deque(ch for ch in letters if indegree[ch] == 0)
        order = []
        while queue:
            ch = queue.popleft()
            order.append(ch)
            for nxt in adj[ch]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        if len(order) != len(letters):
            return ""            # cycle: not every letter reached indegree 0
        return "".join(order)

    def alienOrder_no_prefix_check_BROKEN(self, words: List[str]) -> str:
        """✗ BROKEN ON PURPOSE -- mistake #1. Omits the "longer word before
        its own strict prefix" validity check entirely. Demoed live
        below."""
        letters = set()
        for w in words:
            letters.update(w)

        adj = defaultdict(set)
        indegree = {ch: 0 for ch in letters}

        for a, b in zip(words, words[1:]):
            min_len = min(len(a), len(b))
            for i in range(min_len):
                if a[i] != b[i]:
                    if b[i] not in adj[a[i]]:
                        adj[a[i]].add(b[i])
                        indegree[b[i]] += 1
                    break
            # NOTE: no check for "a is longer than b with no diff" -- BUG

        queue = deque(ch for ch in letters if indegree[ch] == 0)
        order = []
        while queue:
            ch = queue.popleft()
            order.append(ch)
            for nxt in adj[ch]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        if len(order) != len(letters):
            return ""
        return "".join(order)


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    def valid_order(words: List[str], order: str) -> bool:
        if order == "":
            return False
        pos = {ch: i for i, ch in enumerate(order)}
        if len(pos) != len(order):
            return False
        for a, b in zip(words, words[1:]):
            m = min(len(a), len(b))
            i = 0
            while i < m and a[i] == b[i]:
                i += 1
            if i == m:
                if len(a) > len(b):
                    return False
                continue
            if a[i] not in pos or b[i] not in pos or pos[a[i]] >= pos[b[i]]:
                return False
        return True

    cases = [
        (["wrt", "wrf", "er", "ett", "rftt"], True),
        (["z", "x"], True),
        (["z", "x", "z"], False),
        (["abc", "ab"], False),
        (["ab", "abc"], True),
        (["a", "b", "ca", "cc"], True),
        (["abc", "abc"], True),
    ]

    print("--- correctness ---")
    for words, should_be_valid in cases:
        got = sol.alienOrder(list(words))
        if should_be_valid:
            ok = valid_order(words, got) and set(got) == set("".join(words))
        else:
            ok = got == ""
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {words!r:<32} -> {got!r}")

    # --------------------------------------------------------------------
    # ⚠️ LIVE DEMO: missing the prefix-order validity check.
    # --------------------------------------------------------------------
    print("\n--- ⚠️  live demo: mistake #1, no prefix-order check ---")
    words = ["abc", "ab"]
    correct = sol.alienOrder(list(words))
    broken = sol.alienOrder_no_prefix_check_BROKEN(list(words))
    print(f"  words = {words}  (a LONGER word appears before its own "
          f"strict prefix -- provably invalid)")
    print(f"  correct (with prefix check):    {correct!r}")
    print(f"  broken  (without prefix check): {broken!r}")
    exposed = broken != correct
    print(f"  the broken version returns a plausible-looking ordering for "
          f"input that has NO valid alien alphabet: {exposed}")
    all_ok &= exposed and correct == "" and broken != ""

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
