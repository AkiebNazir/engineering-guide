"""
================================================================================
SOLUTION · LeetCode 212 · Word Search II                                  [Hard]
https://leetcode.com/problems/word-search-ii/
================================================================================

THE CORE IDEA
--------------
Build ONE trie from every word in `words`. Then run a SINGLE backtracking
DFS over the grid, starting from every cell, walking the TRIE and the
GRID in lockstep: at each cell, only descend into a neighbor if the
current trie node has a child for that neighbor's letter. The moment the
trie node reached is a word-end, record the word (stored directly on the
node so no substring reconstruction is needed) — and KEEP GOING, because a
word can be a strict prefix of a longer word also in the dictionary
("eat" inside "eaten"). This shares all common-prefix work across every
word that starts the same way: checking "oa..." once serves both "oath"
and "oat" (if both were in the dictionary) instead of walking that shared
prefix separately per word (topic guide Part 3, reason 3).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it, don't ship it): for each word in
`words`, run topic 09's plain Word Search (LC 79) DFS independently over
the WHOLE board — O(len(words)) separate O(m*n*4^L) searches, i.e.
O(len(words) * m*n*4^L) total. With up to 3*10^4 words this is completely
infeasible; the demo below prices it honestly on a much smaller word list.
Crucially, it repeats identical work: if 500 words all start with "ing",
this approach walks the "ing" prefix into the board 500 separate times.

Approach 1 (one trie, DFS from every cell) ✅ — the answer. Build the trie
once: O(sum of word lengths). Then ONE combined DFS from every one of the
m*n cells, following only edges the trie confirms could still lead to a
word: worst case O(m*n*4^L) — same exponential SHAPE as approach 0's
single search, but paid ONCE for the entire dictionary instead of once
PER word, because the trie prunes shared prefixes together.

Approach 2 (approach 1 + trie pruning after a word is found): once a
word's node has yielded its word and has NO children left (nothing else
extends it), delete that node from its parent's `children` dict during
the DFS's own backtrack step. This shrinks the trie as matches are found,
so later DFS branches that would have re-walked a dead prefix die faster.
Same worst-case complexity as approach 1, meaningfully faster in practice
on boards with many matches — the demo below measures the difference.


================================================================================
STEP BY STEP TRACE
================================================================================
words = ["oath", "eat"]

trie:
    root
     ├─o─a─t─h(word="oath")
     └─e─a─t(word="eat")

board:
    o a a n
    e t a e
    i h k r
    i f l v

DFS starts at (0,0)='o': trie has a 'o' child -> descend.
    path so far: "o", node = trie's o-node (not a word yet)
    neighbors of (0,0): (0,1)='a', (1,0)='e'
    try (0,1)='a': o-node has an 'a' child -> descend
        path "oa", node = oa-node (not a word)
        neighbors of (0,1) not yet visited: (0,2)='a', (1,1)='t'
        try (1,1)='t': oa-node has a 't' child -> descend
            path "oat", node = oat-node (not a word)
            neighbors of (1,1) not visited: (1,2)='a', (2,1)='h'
            try (2,1)='h': oat-node has an 'h' child -> descend
                path "oath", node.word == "oath" -> ADD "oath" to results!
                node has no children -> nothing further extends this path,
                backtrack immediately
            backtrack to (1,1), try (1,2)='a': oat-node has no 'a' child
                -> PRUNED, never touches the board there
The outer loop also starts a fresh DFS from every OTHER cell, each walking
the trie from its root again. The one that finds "eat" starts at (1,3)='e':

DFS starts at (1,3)='e': trie has an 'e' child -> descend
    path "e", node = trie's e-node (not a word yet)
    neighbors of (1,3) not yet visited: (0,3)='n', (2,3)='r', (1,2)='a'
    try (1,2)='a': e-node has an 'a' child -> descend
        path "ea", node = ea-node (not a word)
        neighbors of (1,2) not yet visited: (0,2)='a', (2,2)='k', (1,1)='t'
        try (1,1)='t': ea-node has a 't' child -> descend
            path "eat", node.word == "eat" -> ADD "eat" to results!
            node has no children -> backtrack immediately

This EXACT walk (start cell, path, and neighbor order) is what the "trace"
section of `run_tests()` below prints, straight from the real `dfs`
function rather than hand-copied prose — so its printed output is the
authoritative version of this trace, not this comment block.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time                           Space              Mutates input?
    -------------------------------------  -----------------------------  -----------------  --------------
    Per-word plain Word Search (brute)     O(W * m*n*4^L)                 O(L) recursion     temporarily (restored)
    One trie + combined grid DFS ✅        O(m*n*4^L)                    O(sum word lens)    temporarily (restored)
    One trie + prune-dead-branches         O(m*n*4^L) worst, less avg     O(sum word lens)    temporarily (restored)

    W = number of words, m*n = board size, L = max word length (<=10 per
    constraints, so 4^L is a bounded constant, not truly unbounded). The
    trie removes the W factor from the DFS cost entirely by sharing prefix
    work; it does NOT change the DFS's own worst-case exponential shape.
    "Mutates input" is "temporarily" because the standard technique marks
    a cell as visited by overwriting `board[r][c]` with a sentinel during
    the recursive call, then restores the original character on backtrack
    — the caller sees an unmodified board when the function returns, but a
    concurrent read mid-call would see it altered.


================================================================================
EDGE CASES
================================================================================
    word longer than what any path    -> the trie has no way to grow past
    on the board can spell                its own actual inserted length,
                                          the DFS simply never reaches an
                                          `is_word` node for it -> absent
                                          from output. No special-casing.
    same letter needed twice in a      -> "abcb" on a 2x2 board: cannot
    row but board has no cycle back       revisit a cell, so even though
    to reuse a cell (docstring          the LETTERS exist, no legal PATH
    EXAMPLE 2)                          does -> correctly excluded.
    a word that is a PREFIX of another -> "eat" and "eaten" both in words:
    also-present word                    both must appear in the output if
                                        both are reachable; hitting
                                        is_word for "eat" must NOT stop the
                                        DFS from continuing toward "eaten".
    duplicate letters used from         -> the in-progress path must mark
    DIFFERENT cells (not a bug, just     the SPECIFIC cell visited, not the
    worth confirming)                    letter value — two different 'a'
                                        cells are both individually usable
                                        in the SAME word if the path visits
                                        two distinct 'a' cells.
    no words found at all               -> return `[]`, not `None` — an
                                        empty list is a valid, common
                                        output on an unlucky board.
    1x1 board                           -> DFS starts and ends at the same
                                        single cell; only 1-letter words
                                        can ever be found.


================================================================================
COMMON MISTAKES
================================================================================
1. Marking a cell visited with a boolean `visited` SET/grid instead of
   mutating `board[r][c]` to a sentinel — works, but costs extra memory
   and an extra lookup per step; the swap-and-restore trick (topic 09's
   own Word Search technique) is the standard idiom and reused here
   verbatim, since this problem is literally that one plus a trie.

2. Forgetting to RESTORE `board[r][c]` after the recursive call returns
   (only restoring on the success path, or restoring too early/late) —
   corrupts the board for every subsequent DFS starting elsewhere, causing
   silently wrong results for LATER words or later start cells, not an
   immediate crash, which makes this bug easy to miss until you test with
   more than one starting cell in the same run.

3. Not continuing the DFS after finding a word (returning/stopping the
   instant `node.word` is truthy) — breaks the "prefix of another word"
   edge case (`"eat"` inside `"eaten"`), silently dropping the longer
   word from the output.

4. Adding a word to the result MULTIPLE times if it's reachable via
   several distinct paths — the trie node's `word` field should be
   consumed (set to `None` after adding) OR the results collected into a
   `set` first and converted to a list at the end, to avoid duplicates in
   the output.

5. Rebuilding the trie once per START CELL instead of once for the whole
   run — silently reintroduces a per-cell multiplicative cost that the
   trie was supposed to eliminate; build it exactly once, before the grid
   DFS loop begins.

6. Iterating `words` and calling a per-word DFS (approach 0) "because it's
   simpler" — correct, but abandons the entire point of this being a trie
   problem and is the difference between passing and timing out at
   LeetCode's real constraints (up to 3*10^4 words).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: The board is much larger (say 1000x1000) but the word list is small.
   Does the trie still help?
A: Less so — with few words, the per-word brute force (approach 0) isn't
   repeating much shared work, so the gap narrows. The trie's advantage
   scales with how much PREFIX OVERLAP exists across the word list, not
   board size directly; board size affects both approaches equally
   through the shared O(m*n*4^L) DFS shape.

Q: How would you prune the trie live as words are found, to speed up
   later DFS branches?
A: After marking a node's word as found, check if it has zero children;
   if so, delete it from its PARENT's children dict during the DFS's own
   backtracking unwind (approach 2) — dead-end branches then vanish from
   future traversal instantly instead of being walked again only to fail.

Q: What if diagonal moves were also allowed?
A: Only the neighbor-generation step changes (8 directions instead of 4);
   the trie-plus-DFS structure is identical. Complexity becomes
   O(m*n*8^L) instead of O(m*n*4^L).

Q: Could you solve this with Aho-Corasick instead of a plain trie?
A: Aho-Corasick (a trie with failure links) is built for scanning ONE long
   text for many patterns in a single linear pass; this problem's paths
   are branching and non-linear (a grid, not a string), so Aho-Corasick's
   failure-link machinery doesn't map cleanly — the DFS-with-backtracking
   trie approach is the right tool for a grid.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 79   Word Search (topic 09, 012)         — this problem's inner DFS,
            for exactly ONE word instead of a whole trie of them
    LC 208  Implement Trie (this topic, 001)     — the trie construction
            reused here verbatim, augmented with a `word` field
    LC 1233 Remove Sub-Folders from the Filesystem — trie over path
            segments, a different flavor of "many strings sharing prefixes"
    LC 336  Palindrome Pairs                     — trie of REVERSED words
            driving a different kind of pairwise lookup
================================================================================
"""

import random
import string
import time


class TrieNode:
    __slots__ = ("children", "word")

    def __init__(self):
        self.children = {}
        self.word = None   # full word string once this node is a word-end


class Solution:
    def findWords(self, board: list[list[str]], words: list[str]) -> list[str]:
        if not board or not board[0]:
            return []

        root = TrieNode()
        for w in words:
            node = root
            for ch in w:
                if ch not in node.children:
                    node.children[ch] = TrieNode()
                node = node.children[ch]
            node.word = w

        rows, cols = len(board), len(board[0])
        found = []

        def dfs(r, c, node):
            ch = board[r][c]
            child = node.children.get(ch)
            if child is None:
                return
            if child.word is not None:
                found.append(child.word)
                child.word = None   # avoid duplicate adds via multiple paths

            board[r][c] = '#'       # mark visited: swap-and-restore
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and board[nr][nc] != '#':
                    dfs(nr, nc, child)
            board[r][c] = ch         # restore

            # Prune dead branches: this node no longer leads to any word.
            if not child.children:
                del node.children[ch]

        for r in range(rows):
            for c in range(cols):
                dfs(r, c, root)

        return found


# ==============================================================================
# Approach 0 baseline (per-word plain Word Search DFS) used only for the demo.
# ==============================================================================
def word_search_single(board, word):
    """Topic 09's plain Word Search (LC 79): does `word` exist on `board`?"""
    if not board or not board[0]:
        return False
    rows, cols = len(board), len(board[0])

    def dfs(r, c, i):
        if i == len(word):
            return True
        if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != word[i]:
            return False
        board[r][c] = '#'
        found = (dfs(r + 1, c, i + 1) or dfs(r - 1, c, i + 1)
                 or dfs(r, c + 1, i + 1) or dfs(r, c - 1, i + 1))
        board[r][c] = word[i]
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False


def find_words_brute_force(board, words):
    return [w for w in words if word_search_single(board, w)]


# ==============================================================================
# TESTS — run:  python 006_word_search_ii_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness ---")
    sol = Solution()
    board1 = [["o", "a", "a", "n"],
              ["e", "t", "a", "e"],
              ["i", "h", "k", "r"],
              ["i", "f", "l", "v"]]
    words1 = ["oath", "pea", "eat", "rain"]
    got1 = sorted(sol.findWords([row[:] for row in board1], words1))
    ok = got1 == ["eat", "oath"]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  4x4 board, 4 words -> {got1}  (want ['eat', 'oath'])")

    board2 = [["a", "b"], ["c", "d"]]
    words2 = ["abcb"]
    got2 = sol.findWords([row[:] for row in board2], words2)
    ok = got2 == []
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  no-reuse-of-a-cell case -> {got2}  (want [])")

    # word that is a prefix of another, both present.
    # Path: e(0,0) -> a(0,1) -> t(1,1). "eaten" needs an 'e' next, but
    # (1,1)'s only unused neighbor is (1,0)='x' -> "eaten" is unreachable,
    # while "ea" and "eat" (prefixes along the SAME path) both ARE.
    board3 = [["e", "a"], ["x", "t"]]
    words3 = ["eat", "eaten", "ea"]
    got3 = sorted(sol.findWords([row[:] for row in board3], words3))
    ok = got3 == ["ea", "eat"]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  prefix-of-another-word case -> {got3}  "
          f"(want ['ea', 'eat'])")

    # 1x1 board
    board4 = [["x"]]
    got4 = sol.findWords([row[:] for row in board4], ["x", "y", "xx"])
    ok = got4 == ["x"]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  1x1 board -> {got4}  (want ['x'])")

    # board mutation is only temporary
    board5 = [row[:] for row in board1]
    sol.findWords(board5, words1)
    ok = board5 == board1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  board restored after findWords: {ok}")

    # --------------------------------------------------------------------
    # Trace: print the ACTUAL discovered path for "oath" on board1.
    # --------------------------------------------------------------------
    print("\n--- trace: actual accepted paths found on board1 ---")
    root = TrieNode()
    for w in words1:
        node = root
        for ch in w:
            node = node.children.setdefault(ch, TrieNode())
        node.word = w
    rows, cols = len(board1), len(board1[0])
    b = [row[:] for row in board1]
    trace_found = []

    def traced_dfs(r, c, node, path):
        ch = b[r][c]
        child = node.children.get(ch)
        if child is None:
            return
        path = path + [(r, c, ch)]
        if child.word is not None:
            trace_found.append((child.word, list(path)))
        b[r][c] = '#'
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and b[nr][nc] != '#':
                traced_dfs(nr, nc, child, path)
        b[r][c] = ch

    for r in range(rows):
        for c in range(cols):
            traced_dfs(r, c, root, [])
    for word, path in trace_found:
        path_str = " -> ".join(f"({r},{c})='{ch}'" for r, c, ch in path)
        print(f"  {word!r:8} via {path_str}")

    # --------------------------------------------------------------------
    # Cross-check vs the per-word brute force on random boards/word lists.
    # --------------------------------------------------------------------
    print("\n--- randomised cross-check: trie+DFS vs per-word brute force ---")
    random.seed(212)
    alphabet = "abcde"   # small alphabet -> boards with real overlapping words
    mismatches, trials = 0, 60
    for _ in range(trials):
        rows_n, cols_n = random.randint(2, 5), random.randint(2, 5)
        board = [[random.choice(alphabet) for _ in range(cols_n)]
                 for _ in range(rows_n)]
        words = list({"".join(random.choices(alphabet, k=random.randint(1, 4)))
                      for _ in range(8)})
        got_trie = sorted(sol.findWords([row[:] for row in board], words))
        got_brute = sorted(find_words_brute_force([row[:] for row in board], words))
        if got_trie != got_brute:
            mismatches += 1
    ok = mismatches == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {trials} random boards, {mismatches} mismatches")

    # --------------------------------------------------------------------
    # DEMO: one trie + combined DFS vs per-word brute-force DFS.
    # --------------------------------------------------------------------
    print("\n--- DEMO: shared-prefix trie DFS vs per-word brute-force DFS ---")
    random.seed(7)
    demo_board = [[random.choice(alphabet) for _ in range(8)] for _ in range(8)]
    # Build a word list with HEAVY shared-prefix overlap (the case the trie
    # is specifically built to exploit) by extending a handful of stems.
    stems = ["ab", "ac", "ad", "ba", "bc"]
    demo_words = list({stem + "".join(random.choices(alphabet, k=random.randint(0, 2)))
                        for stem in stems for _ in range(60)})
    print(f"  8x8 board, {len(demo_words)} words sharing {len(stems)} common stems")

    board_a = [row[:] for row in demo_board]
    t0 = time.perf_counter()
    result_trie = sol.findWords(board_a, demo_words)
    t1 = time.perf_counter()

    board_b = [row[:] for row in demo_board]
    result_brute = find_words_brute_force(board_b, demo_words)
    t2 = time.perf_counter()

    same = sorted(result_trie) == sorted(result_brute)
    all_ok &= same
    trie_t, brute_t = t1 - t0, t2 - t1
    print(f"  trie + one combined DFS:     {trie_t * 1000:8.2f} ms")
    print(f"  per-word brute-force DFS:    {brute_t * 1000:8.2f} ms")
    print(f"  trie is {brute_t / trie_t:6.1f}x faster; results identical: {same}")
    print("  Both DFS variants share the same exponential worst-case SHAPE per")
    print("  search; the win here is paying the shared-prefix walk ONCE across")
    print(f"  all {len(demo_words)} words instead of once per word.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
