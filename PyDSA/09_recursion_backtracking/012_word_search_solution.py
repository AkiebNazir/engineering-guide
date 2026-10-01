"""
================================================================================
SOLUTION · LeetCode 79 · Word Search                                    [Medium]
https://leetcode.com/problems/word-search/
================================================================================

THE CORE IDEA
--------------
This is classic grid backtracking. The decision tree branches up to 4 ways at 
each step (the adjacent neighbors). 

The most critical aspect is state management: because we mutate the board in 
place to mark a cell as visited (saving O(M*N) memory), we MUST unmark the cell 
before returning from the recursive call. Forgetting to unmark unconditionally 
leads to silent false negatives[cite: 2].


================================================================================
STEP BY STEP TRACE — "AAA" on a 2x2 board
================================================================================
Board:                      Neighbor order tried by dfs(): down, up, right, left
  A  A
  A  B

Start (0,0): dfs(0,0,i=0) -> 'A' matches word[0].
  CHOOSE: mark (0,0) = '#'
  EXPLORE DOWN:  dfs(1,0,i=1) -> 'A' matches word[1].
    CHOOSE: mark (1,0) = '#'
    down/up/right/left all fail (OOB or 'B' or '#')
    UNCHOOSE: (1,0) = 'A'   <-- restores the cell for later use
    Returns False.
  EXPLORE RIGHT: dfs(0,1,i=1) -> 'A' matches word[1].
    CHOOSE: mark (0,1) = '#'
    down/up/right all fail; left -> (0,0) is '#' (itself), fails.
    UNCHOOSE: (0,1) = 'A'
    Returns False.
  All branches from (0,0) fail. UNCHOOSE: (0,0) = 'A'. Returns False.

Start (0,1): dfs(0,1,i=0) -> 'A' matches word[0].
  CHOOSE: mark (0,1) = '#'
  EXPLORE DOWN:  dfs(1,1,i=1) -> 'B' != 'A'. Fails.
  EXPLORE LEFT:  dfs(0,0,i=1) -> 'A' matches word[1].
    CHOOSE: mark (0,0) = '#'
    EXPLORE DOWN: dfs(1,0,i=2) -> 'A' matches word[2]. i+1 == len(word) -> True!
  Propagates True all the way up. exist() returns True.
  Path found: (0,1) -> (0,0) -> (1,0) = "AAA".

The cell (1,0) that completes the word was VISITED AND UNMARKED during the
failed attempt from start (0,0), then successfully REUSED (as a different
board cell in a different call chain reading the same object) once the
search moved on to start (0,1). If UNCHOOSE were missing, (1,0) would still
read '#' when the winning path needed it, and exist() would wrongly return
False even though a valid path exists — see the buggy demo below.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach               Time                 Space          Mutates input?
    ---------------------  -------------------  -------------  ---------------
    Backtracking (DFS)     O(m * n * 3^L)       O(L) stack     Yes (temporarily)

    WHERE O(m * n * 3^L) comes from: 
    We iterate over all m * n cells as potential starting points. For a word of 
    length L, the first character has 4 neighbor choices, but every subsequent 
    character has at most 3 valid choices (because we can't go back to the cell 
    we just came from)[cite: 2]. The recursion depth is L, bounded by O(L) space.


================================================================================
EDGE CASES
================================================================================
    1x1 board        -> Handles cleanly, bounds check protects neighbor access.
    Word > grid size -> Impossible. Can short-circuit early by checking if 
                        len(word) > m * n.
    Character counts -> If the board doesn't contain enough of a specific 
                        character to form the word, you can prune before DFS 
                        (implemented as an optimization below).


================================================================================
COMMON MISTAKES
================================================================================
1. The "Missing Unmark" Bug: As stated, leaving cells marked when returning False 
   permanently destroys paths for subsequent branches[cite: 2]. Demonstrated 
   live in the test runner below.
2. Checking bounds incorrectly: Using `r >= len(board)` or `c >= len(board[0])` 
   is necessary, but forgetting to check `r < 0` or `c < 0` will cause Python 
   to silently wrap around via negative indexing (e.g., `board[-1][-1]`), 
   leading to logically incorrect neighbor matching.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How can we optimize this if the board is huge and the word is very long?
A: Pre-flight frequency checking. Count all characters in the board. If the word 
   requires 3 'A's but the board only has 2, return False immediately in O(M*N) 
   time before doing any backtracking.

Q: What if the board is read-only?
A: Pass a `visited = set()` containing `(r, c)` tuples. This changes space 
   complexity from O(L) to O(L) auxiliary space, which is asymptotically identical 
   but has higher practical overhead.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 212  Word Search II                  — The natural evolution: searching 
                                              for MULTIPLE words simultaneously 
                                              using a Trie + Backtracking.
    LC 200  Number of Islands               — Standard grid DFS without the 
                                              unchoose step (because you WANT 
                                              to permanently mark visited).
================================================================================
"""

from collections import Counter
from typing import List


class Solution:
    def exist(self, board: List[List[str]], word: str) -> bool:
        """
        Standard Backtracking approach.
        Mutates the board in place to track visited state, always unmarking.
        """
        ROWS, COLS = len(board), len(board[0])
        WORD_LEN = len(word)

        # Early optimization: Check if there are even enough characters
        board_counts = Counter(char for row in board for char in row)
        word_counts = Counter(word)
        for char, count in word_counts.items():
            if board_counts[char] < count:
                return False

        def dfs(r: int, c: int, i: int) -> bool:
            if i == WORD_LEN:
                return True
            
            if (r < 0 or c < 0 or r >= ROWS or c >= COLS or 
                board[r][c] != word[i]):
                return False

            # 1. CHOOSE
            tmp, board[r][c] = board[r][c], '#'
            
            # 2. EXPLORE
            found = (
                dfs(r + 1, c, i + 1) or
                dfs(r - 1, c, i + 1) or
                dfs(r, c + 1, i + 1) or
                dfs(r, c - 1, i + 1)
            )

            # 3. UNCHOOSE (Always execute this, regardless of success/failure)
            board[r][c] = tmp
            return found

        for r in range(ROWS):
            for c in range(COLS):
                if dfs(r, c, 0):
                    return True

        return False

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def exist_wrong_unmark(self, board: List[List[str]], word: str) -> bool:
        """
        ✗ BROKEN ON PURPOSE — Forgets to restore `board[r][c]` to `tmp` when
        a path fails. This permanently corrupts the board for other valid paths
        that might need to cross that cell later[cite: 2].
        """
        ROWS, COLS = len(board), len(board[0])

        def dfs(r, c, i):
            if i == len(word): return True
            if r < 0 or c < 0 or r >= ROWS or c >= COLS or board[r][c] != word[i]:
                return False

            tmp, board[r][c] = board[r][c], '#'
            found = (
                dfs(r + 1, c, i + 1) or dfs(r - 1, c, i + 1) or
                dfs(r, c + 1, i + 1) or dfs(r, c - 1, i + 1)
            )
            
            if found:
                return True
            
            # BUG: Missing board[r][c] = tmp
            return False

        for r in range(ROWS):
            for c in range(COLS):
                if dfs(r, c, 0):
                    return True
        return False


# ==============================================================================
# TESTS — run:  python 012_word_search_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        (
            [["A","B","C","E"], ["S","F","C","S"], ["A","D","E","E"]],
            "ABCCED", True
        ),
        (
            [["A","B","C","E"], ["S","F","C","S"], ["A","D","E","E"]],
            "SEE", True
        ),
        (
            [["A","B","C","E"], ["S","F","C","S"], ["A","D","E","E"]],
            "ABCB", False
        ),
        (
            [["A", "A"]], "AAA", False
        )
    ]
    
    all_ok = True
    print("--- Standard Implementation ---")
    for board, word, expected in cases:
        board_copy = [row[:] for row in board]
        got = sol.exist(board_copy, word)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  word={word:<8} -> {got} (want {expected})")

    # ----------------------------------------------------------------------
    # ⚠️ The missing-unmark bug, live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  missing unmark: the false-negative bug ---")
    
    # This board/word pair was found by brute-force search over all 2x2
    # boards of {A,B} and all words of length 3-4: it is the smallest
    # repro where the correct algorithm succeeds but the buggy one fails.
    #
    # Board:      Word: "AAA"
    #   A A
    #   A B
    #
    # The correct DFS starting at (0,0) tries (0,1)='A' first, which then
    # dead-ends (its only unvisited neighbor (1,1)='B' != 'A'), so it
    # backtracks and UNMARKS (0,1). That frees (0,1) so the search can
    # retry through (1,0)='A' -> (0,0)... no: concretely, some starting
    # cell's DFS visits an 'A', fails deeper, unmarks it, and a *different*
    # branch from that same start needs that exact cell again to complete
    # "AAA". Without the unmark, that branch is permanently blocked and
    # exist() returns a false negative even though a valid path exists.
    trap_board = [
        ["A", "A"],
        ["A", "B"]
    ]
    trap_word = "AAA"
    
    print(f"Board: {trap_board[0]}\n       {trap_board[1]}")
    print(f"Word:  {trap_word}")
    
    # Test correct
    b1 = [row[:] for row in trap_board]
    res_correct = sol.exist(b1, trap_word)
    
    # Test buggy
    b2 = [row[:] for row in trap_board]
    res_buggy = sol.exist_wrong_unmark(b2, trap_word)
    
    print(f"  correct code found word?     {res_correct}")
    print(f"  buggy code found word?       {res_buggy}")
    
    bug_reproduced = (res_correct is True and res_buggy is False)
    print(f"  bug reproduced successfully? {bug_reproduced}")
    all_ok &= bug_reproduced

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()