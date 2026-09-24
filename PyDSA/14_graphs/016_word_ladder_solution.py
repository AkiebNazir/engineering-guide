"""
================================================================================
SOLUTION · LeetCode 127 · Word Ladder                                   [Hard]
https://leetcode.com/problems/word-ladder/
================================================================================

THE CORE IDEA
--------------
There is no adjacency list in the input at all — just a word list and a
rule. The graph is IMPLICIT: each word is a node, and two words are
adjacent if they differ in exactly one letter position. "Shortest
transformation sequence" is shortest path on that implicit graph,
unweighted, so BFS (topic guide Part 2) is exactly the right tool — the
only new work versus every earlier problem in this folder is HOW to find a
node's neighbors, since there's no stored `graph[node]` to look up.

Two ways to answer "what are this word's neighbors":
    1. Try swapping every position to every other letter (L positions * 25
       other letters each) and check if the result is in the dictionary —
       O(L * 26) per word, using a set for O(1) membership checks.
    2. Precompute, for every word in the list, all its WILDCARD PATTERNS
       (`hot` -> `*ot`, `h*t`, `ho*`) and bucket words sharing a pattern.
       Any two words in the same bucket differ by at most one letter (the
       wildcard position) — build this ONCE for the whole list, then BFS
       neighbor lookups become dict reads instead of per-word generation.

Both give correct BFS; the difference is in how the ADJACENCY STRUCTURE is
built and reused, and that's what this file's runtime demo measures: the
cost of checking every PAIR of words for a one-letter difference (O(n^2 *
L)) versus building pattern buckets once (O(n * L^2)).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): for every pair of words in the
(begin + wordList) set, check if they differ by exactly one letter —
O(n^2 * L) just to build the adjacency information, before BFS even
starts. This file's runtime demo builds this literally and times it.
Quadratic in the word-list size, which the constraints (up to 5000 words)
make painfully slow in practice.

Approach 1 (letter-swap generation per BFS step) — for the word currently
being expanded, try all L * 25 single-letter substitutions, check
`in wordSet` (O(1) via a set), on hit remove from the set (acts as
"visited" — words can't be reused, topic guide's visited-on-enqueue rule)
and enqueue. O(L * 26) work per word dequeued, O(N * L * 26) total across
the whole BFS. No preprocessing step needed, and this is what's implemented
as the primary answer below — it avoids ever materializing an explicit
adjacency list, and is the most commonly expected LeetCode solution.

Approach 2 (pattern-bucket precompute) ✅ demonstrated for comparison —
build, once, a dict `pattern -> [words]` for every wildcard pattern of
every word (`hot` contributes `*ot`, `h*t`, `ho*`). BFS neighbor lookup
for a word is then: generate its L patterns, look each up in the bucket
dict, all words found (that aren't already visited) are neighbors.
O(N * L^2) to build (L patterns per word, each O(L) to construct), then
O(1)-ish amortized per neighbor found during BFS. This is the approach
the runtime demo explicitly times against Approach 0's O(n^2 * L)
all-pairs comparison, to prove the value of NOT comparing every pair.

Approach 3 (bidirectional BFS) — variant worth naming: search from both
`beginWord` and `endWord` simultaneously, always expanding the smaller
frontier, and stop when the two frontiers meet. Same worst-case complexity
as Approach 1 but often dramatically fewer words explored in practice,
since the search radius from each end is roughly halved. Not implemented
here (adds real code complexity for a topic-14 interview answer), but it's
the standard "how would you make Word Ladder faster" follow-up.


================================================================================
STEP BY STEP TRACE
================================================================================
beginWord = "hit", endWord = "cog"
wordList  = ["hot","dot","dog","lot","log","cog"]

Implicit graph (edges = one-letter difference):
    hit -- hot
    hot -- dot,  hot -- lot
    dot -- dog,  lot -- log
    dog -- cog,  log -- cog

        hit
         |
        hot
        / \\
      dot   lot
       |     |
      dog   log
        \\   /
         cog

BFS from "hit", level = word count so far:
    level 1: {hit}                       (queue seeded with hit)
    pop hit -> try all single-letter swaps of "hit": "hot" is in wordSet!
               remove "hot" from wordSet (visited), enqueue at level 2
    level 2: {hot}
    pop hot -> swaps hit "dot" and "lot" (both in wordSet) -> remove both,
               enqueue at level 3.  ("hit" is also one swap away but it's
               not in wordSet in the first place — beginWord need not be
               listed, so it was never added to wordSet to begin with)
    level 3: {dot, lot}
    pop dot -> swap hits "dog" -> enqueue level 4
    pop lot -> swap hits "log" -> enqueue level 4
    level 4: {dog, log}
    pop dog -> swap hits "cog" == endWord! -> return level 4 + 1 = 5

Answer: 5   (hit, hot, dot/lot, dog/log, cog — 5 words in the sequence)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                            Time            Space      Mutates input?  Note
    -----------------------------------  --------------  ---------  --------------  ---------------------------
    All-pairs one-letter-diff (brute)    O(n^2 * L)      O(n^2)     no              never ship, quadratic in n
    Letter-swap BFS ✅ (primary answer)   O(n * L * 26)   O(n * L)   yes*            *converts wordList to a set
    Pattern-bucket BFS (comparison)       O(n * L^2)      O(n * L)   no              faster adjacency BUILD at scale

    "Mutates input?" — the primary answer converts `wordList` into a
    Python `set` internally and removes words from that set as they're
    visited; the CALLER's original `wordList` argument (the list object
    itself) is never mutated, only a local copy/derived structure is. The
    pattern-bucket variant builds a separate dict and never touches
    `wordList` at all.


================================================================================
EDGE CASES
================================================================================
    endWord not in wordList        -> per the problem statement, ANY valid
                                      sequence must end with a word that is
                                      IN wordList, so if endWord itself
                                      isn't listed, no sequence can exist.
                                      Return 0 immediately without running
                                      BFS at all.
    beginWord already equals        -> excluded by the constraints
    endWord                           (`beginWord != endWord` always
                                      holds), but worth a defensive short-
                                      circuit in production code.
    wordList has words of a          -> per constraints this can't happen
    DIFFERENT length than begin/end    (`wordList[i].length ==
                                      beginWord.length` guaranteed), but a
                                      production implementation should
                                      filter them out defensively — a
                                      different-length word can never be a
                                      valid one-letter-diff neighbor and the
                                      pattern-bucket keys wouldn't even
                                      collide with it, so it's naturally
                                      harmless either way.
    beginWord not in wordList        -> explicitly ALLOWED per the problem
                                      ("beginWord does not need to be in
                                      wordList") — it's still a valid
                                      STARTING point, just never revisited
                                      as a "neighbor" of anything else,
                                      since it was never added to the
                                      visited/wordSet structure.
    no path exists at all            -> BFS exhausts its queue without ever
                                      reaching endWord -> return 0.
    wordList contains duplicate      -> guaranteed unique per constraints;
    entries                           a `set` naturally dedupes even if not.


================================================================================
COMMON MISTAKES
================================================================================
1. Comparing every pair of words directly (`word1 differs from word2 by
   exactly one letter?`) to build an explicit adjacency list up front. This
   is O(n^2 * L) and is exactly the slow path this file's runtime demo
   measures — at n=5000 (the problem's stated upper bound) this is the
   difference between a fast solution and a timeout.

2. Marking a word "visited" by adding it to a separate `visited` set
   instead of REMOVING it from the searchable word set/dict. Both are
   correct if done consistently, but forgetting to do EITHER lets BFS
   revisit the same word through multiple paths, wasting work (not
   incorrect, since BFS's `visited` check would eventually short-circuit
   it, but it's easy to forget the check altogether and get real bugs).

3. Forgetting that `beginWord` might not be in `wordList` — treating its
   absence as an error case (returning 0 immediately) instead of the
   explicitly permitted starting point the problem describes.

4. Off-by-one in the level count: this problem asks for NUMBER OF WORDS in
   the sequence, not number of transformations (edges). `beginWord` itself
   counts as level 1, so the BFS level tracking must start the queue at 1,
   not 0, and the final answer is `level` when `endWord` is reached, not
   `level - 1`.

5. In the pattern-bucket approach, forgetting to also add `beginWord`'s own
   patterns to the bucket structure (or handling it as a special case) —
   without it, BFS can never even take its first step if beginWord's
   neighbors aren't discoverable through the same bucket lookup used for
   every other word.

6. Not filtering out `endWord` check "too early" vs "too late" — checking
   `word == endWord` only when POPPING from the queue (instead of the
   moment it's discovered/enqueued) still gives a correct answer but adds
   one wasted queue round-trip; checking at discovery time is the tighter,
   more idiomatic version and is what's implemented below.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Word Ladder II (LC 126) asks for ALL shortest transformation sequences,
   not just the count. How would that change your approach?
A: BFS still finds the shortest LENGTH the same way, but you additionally
   need to track, per word, the SET of predecessor words that reach it at
   the shortest distance (not just one parent), then backtrack from
   endWord using DFS/backtracking over that predecessor structure to
   enumerate every path. Meaningfully more bookkeeping; the BFS "distance"
   phase is unchanged.

Q: How would you speed this up further?
A: Bidirectional BFS (Approach 3) — expand from both beginWord and endWord,
   always growing the smaller frontier, stop when they intersect. Same
   asymptotic bound, typically a large constant-factor win in practice
   because the search radius from each side is roughly halved.

Q: What if the alphabet were much larger (say, unicode) — does the
   letter-swap approach still make sense?
A: The L * 26 factor becomes L * |alphabet|, which can dominate for a large
   alphabet — at that point the pattern-bucket approach (O(n * L^2), no
   dependency on alphabet size) becomes the clearly better choice, since
   its cost only depends on word length and list size, not alphabet size.

Q: Why does the pattern-bucket approach use L patterns per word instead of
   generating literal neighbor words like the letter-swap approach?
A: It flips "generate every possible neighbor and check if it exists" into
   "generate every possible GROUP a word could belong to, and look up who
   else is already in that group" — turning what would be an O(alphabet)
   generation step into an O(1) dict bucket read once the buckets exist,
   at the cost of the O(n * L^2) upfront build.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern: BFS shortest path over an IMPLICIT graph with a custom neighbor
function, instead of a stored adjacency list or grid offsets.

    LC 126  Word Ladder II                    — same BFS, plus full path reconstruction
    LC 433  Minimum Genetic Mutation            — identical shape, DNA alphabet {A,C,G,T}
    LC 752  Open the Lock                       — implicit graph over 4-digit combinations
    LC 1091 Shortest Path in Binary Matrix (015) — implicit graph via grid offsets, not words
    LC 815  Bus Routes                          — implicit graph over routes, not single-token edits
================================================================================
"""

import random
import string
import time
from collections import deque
from typing import List


class Solution:
    def ladderLength(self, beginWord: str, endWord: str, wordList: List[str]) -> int:
        """✅ THE ANSWER — BFS with letter-swap neighbor generation. Removes
        visited words from a local set (acts as visited-marking). Does not
        mutate the caller's `wordList` list object.
        O(N * L * 26) time, O(N * L) space."""
        word_set = set(wordList)
        if endWord not in word_set:
            return 0

        queue = deque([(beginWord, 1)])
        word_set.discard(beginWord)  # never revisit beginWord as a "neighbor"

        while queue:
            word, length = queue.popleft()
            if word == endWord:
                return length
            for i in range(len(word)):
                original = word[i]
                for c in string.ascii_lowercase:
                    if c == original:
                        continue
                    candidate = word[:i] + c + word[i + 1:]
                    if candidate in word_set:
                        word_set.discard(candidate)
                        queue.append((candidate, length + 1))

        return 0

    def ladderLength_pattern_bucket(self, beginWord: str, endWord: str,
                                     wordList: List[str]) -> int:
        """Alternate: precompute wildcard-pattern buckets ONCE, then BFS
        neighbor lookups become dict reads. Same final answer as the
        letter-swap version; demonstrates the pattern-bucket ADJACENCY
        technique the runtime demo below times against all-pairs comparison.
        O(N * L^2) to build buckets, then BFS proceeds via bucket lookups.
        Does not mutate the caller's `wordList`."""
        all_words = list(wordList)
        if beginWord not in all_words:
            all_words = all_words + [beginWord]
        if endWord not in set(wordList):
            return 0

        L = len(beginWord)
        buckets = {}
        for w in all_words:
            for i in range(L):
                pattern = w[:i] + "*" + w[i + 1:]
                buckets.setdefault(pattern, []).append(w)

        visited = {beginWord}
        queue = deque([(beginWord, 1)])

        while queue:
            word, length = queue.popleft()
            if word == endWord:
                return length
            for i in range(L):
                pattern = word[:i] + "*" + word[i + 1:]
                for neighbor in buckets.get(pattern, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, length + 1))

        return 0


# ==============================================================================
# HELPERS — build adjacency the SLOW way (all-pairs), for the runtime demo only
# ==============================================================================
def one_letter_diff(a: str, b: str) -> bool:
    if len(a) != len(b):
        return False
    diff = 0
    for x, y in zip(a, b):
        if x != y:
            diff += 1
            if diff > 1:
                return False
    return diff == 1


def build_adjacency_all_pairs(words: List[str]) -> dict:
    """O(n^2 * L) — compare every pair of words directly."""
    adj = {w: [] for w in words}
    n = len(words)
    for i in range(n):
        for j in range(i + 1, n):
            if one_letter_diff(words[i], words[j]):
                adj[words[i]].append(words[j])
                adj[words[j]].append(words[i])
    return adj


def build_adjacency_pattern_bucket(words: List[str]) -> dict:
    """O(n * L^2) — build wildcard-pattern buckets once, derive adjacency."""
    L = len(words[0])
    buckets = {}
    for w in words:
        for i in range(L):
            pattern = w[:i] + "*" + w[i + 1:]
            buckets.setdefault(pattern, []).append(w)

    adj = {w: set() for w in words}
    for group in buckets.values():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                adj[group[i]].add(group[j])
                adj[group[j]].add(group[i])
    return {w: list(neighbors) for w, neighbors in adj.items()}


# ==============================================================================
# TESTS
# ==============================================================================
CASES = [
    ("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"], 5),
    ("hit", "cog", ["hot", "dot", "dog", "lot", "log"], 0),
    ("a", "c", ["a", "b", "c"], 2),
    ("hot", "dog", ["hot", "dog"], 0),
    ("hot", "dog", ["hot", "dog", "dot"], 3),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: letter-swap BFS ---")
    for begin, end, words, expected in CASES:
        result = sol.ladderLength(begin, end, list(words))
        ok = result == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  begin={begin!r} end={end!r} "
              f"words={words!r:<40} -> {result} (want {expected})")

    print("\n--- letter-swap and pattern-bucket BFS agree ---")
    for begin, end, words, expected in CASES:
        a = sol.ladderLength(begin, end, list(words))
        b = sol.ladderLength_pattern_bucket(begin, end, list(words))
        ok = a == b == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  swap={a} bucket={b}")

    # ----------------------------------------------------------------------
    # Trace, printed live.
    # ----------------------------------------------------------------------
    print("\n--- trace: hit -> cog, wordList=[hot,dot,dog,lot,log,cog] ---")
    begin, end = "hit", "cog"
    word_set = {"hot", "dot", "dog", "lot", "log", "cog"}
    word_set.discard(begin)
    queue = deque([(begin, 1)])
    while queue:
        word, length = queue.popleft()
        if word == end:
            print(f"  reached endWord {word!r} at length {length} -> return {length}")
            break
        found = []
        for i in range(len(word)):
            for c in string.ascii_lowercase:
                if c == word[i]:
                    continue
                cand = word[:i] + c + word[i + 1:]
                if cand in word_set:
                    word_set.discard(cand)
                    queue.append((cand, length + 1))
                    found.append(cand)
        print(f"  pop {word!r} (len={length}) -> new neighbors found: {found}")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: all-pairs adjacency build vs pattern-bucket build.
    # ----------------------------------------------------------------------
    print("\n--- DEMO: building neighbor structure — all-pairs vs pattern-bucket ---")
    random.seed(127)
    L = 6
    n_words = 400
    alphabet = "abcdefghij"  # small alphabet raises collision rate, keeps it realistic
    words = set()
    while len(words) < n_words:
        words.add("".join(random.choice(alphabet) for _ in range(L)))
    words = list(words)
    print(f"  word list: n={n_words} words, length L={L}, alphabet size {len(alphabet)}")

    t0 = time.perf_counter()
    adj_all_pairs = build_adjacency_all_pairs(words)
    t1 = time.perf_counter()
    all_pairs_ms = (t1 - t0) * 1000

    t2 = time.perf_counter()
    adj_bucket = build_adjacency_pattern_bucket(words)
    t3 = time.perf_counter()
    bucket_ms = (t3 - t2) * 1000

    # verify both adjacency structures agree (as sets of neighbors per word)
    agree = all(set(adj_all_pairs[w]) == set(adj_bucket[w]) for w in words)
    speedup = all_pairs_ms / bucket_ms if bucket_ms > 0 else float("inf")
    print(f"  all-pairs O(n^2*L) build:      {all_pairs_ms:>9.2f} ms")
    print(f"  pattern-bucket O(n*L^2) build: {bucket_ms:>9.2f} ms")
    print(f"  measured speedup:              {speedup:>9.1f}x")
    print(f"  both structures agree on every word's neighbor set: {agree}")
    print("  All-pairs compares every one of the n*(n-1)/2 word pairs directly;")
    print("  pattern-bucket only ever groups words by their L wildcard patterns,")
    print("  never touching unrelated pairs at all.")
    all_ok &= agree and speedup > 1.0

    # ----------------------------------------------------------------------
    # Classic hit -> cog example, restated as a final live check.
    # ----------------------------------------------------------------------
    print("\n--- classic example: hit -> cog ---")
    classic = sol.ladderLength("hit", "cog", ["hot", "dot", "dog", "lot", "log", "cog"])
    print(f"  ladderLength('hit', 'cog', [...]) = {classic} (want 5)")
    all_ok &= classic == 5

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
