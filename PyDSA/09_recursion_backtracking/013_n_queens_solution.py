"""
================================================================================
SOLUTION · LeetCode 51 · N-Queens                                         [Hard]
https://leetcode.com/problems/n-queens/
================================================================================

THE CORE IDEA
--------------
This is the definitive Constraint Satisfaction problem. The entire reason this 
runs in milliseconds instead of geological time is that validity is checked 
BEFORE the recursive call is made[cite: 2].

By assigning exactly one queen per row, we eliminate row-conflicts entirely. 
By maintaining O(1) lookup sets for `columns`, `positive_diagonals`, and 
`negative_diagonals`, we can prune invalid branches instantly[cite: 2].

The Diagonal Math:
    - Positive Diagonals (bottom-left to top-right) share the same `row + col`.
      Example: (2,0), (1,1), (0,2) all sum to 2.
    - Negative Diagonals (top-left to bottom-right) share the same `row - col`.
      Example: (0,0), (1,1), (2,2) all subtract to 0.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. GENERATE ALL PLACEMENTS (Raw O(n^n)) — Place one queen per row blindly, build 
   the entire board, and check validity at the leaves. Astoundingly slow. 
   (Priced and measured below).
2. PRUNE WITH O(N) CHECK — At each cell, iterate through all previously placed 
   queens to see if they attack the current cell. Good, but does unnecessary work.
3. PRUNE WITH O(1) SETS — Maintain sets for cols and diags. The optimal answer, 
   reducing validity checks to O(1)[cite: 2].


================================================================================
STEP BY STEP TRACE — n = 4
================================================================================
Sets: cols=(), pos_diag(r+c)=(), neg_diag(r-c)=()

    backtrack(row=0)
      col=0: Safe? YES. 
        CHOOSE: cols=(0), pos_diag=(0), neg_diag=(0)
        EXPLORE: backtrack(row=1)
          col=0: Safe? NO (cols contains 0) -> PRUNE
          col=1: Safe? NO (neg_diag contains 1-1=0) -> PRUNE
          col=2: Safe? YES.
            CHOOSE: cols=(0,2), pos_diag=(0,3), neg_diag=(0,-1)
            EXPLORE: backtrack(row=2)
              col=0: Safe? NO -> PRUNE
              col=1: Safe? NO (pos_diag contains 2+1=3) -> PRUNE
              col=2: Safe? NO -> PRUNE
              col=3: Safe? NO (neg_diag contains 2-3=-1) -> PRUNE
              (All columns pruned at row 2! The branch is dead).
            UNCHOOSE: cols=(0), pos_diag=(0), neg_diag=(0)
          col=3: Safe? YES.
            CHOOSE...
            
Notice how at row 2, we didn't generate any boards. The moment we saw a 
conflict, we pruned the entire subtree underneath it[cite: 2].


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach               Time                 Space          Mutates input?
    ---------------------  -------------------  -------------  ---------------
    Raw Generate-All       O(n^n)               O(n^2)         no
    O(1) Set Pruning       O(n!) worst-case     O(n)           no

    WHERE O(n!) comes from: 
    For the first row, we have N choices. For the second row, we have at most 
    N-1 choices (since one column is blocked). For the third, N-2, and so on. 
    Thus, the upper bound of the tree is N!. 
    However, diagonal pruning cuts this down exponentially further. There is no 
    clean closed-form formula for the heavily pruned tree, which is why we 
    measure the nodes directly below[cite: 2]. Space is O(n) to store the 
    board state (an array of length n) and the sets. Building the string board 
    at the leaves takes O(n^2), but only for valid solutions.


================================================================================
EDGE CASES
================================================================================
    n = 1 -> [["Q"]] (Trivial).
    n = 2, 3 -> [] (Mathematically impossible to place queens without attack).
    n = 9 -> Solves in < 10ms with O(1) set pruning.


================================================================================
COMMON MISTAKES
================================================================================
1. Generating complete candidates instead of pruning BEFORE recursing[cite: 2].
2. Forgetting to unchoose from the sets. Just like removing from `path`, if you 
   don't remove the constraints from `cols` and `diags` when backtracking, they 
   corrupt sibling branches.
3. Over-complicating the board state. You don't need a 2D array of strings 
   during the recursion. Just keep a list of integers `board = [1, 3, 0, 2]`, 
   where the index is the row and the value is the column, then build the 
   strings at the very end.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can we optimize the space complexity even further?
A: Yes. Instead of Python `set()` objects, you can use bitmasking. Since N <= 9, 
   a single integer can represent `cols` (e.g., `00100101`). You can use bitwise 
   OR to mark choices and bitwise AND to check safety. This is how the absolute 
   fastest solvers work.

Q: What if we only needed to return the NUMBER of solutions, not the boards?
A: (LeetCode 52: N-Queens II). We drop the string building entirely and just 
   increment a global counter at the base case `row == n`.
================================================================================
"""

import time
from typing import List


class Solution:
    def solveNQueens(self, n: int) -> List[List[str]]:
        """
        O(1) Set Pruning Approach. The optimal backtracking strategy.
        Checks validity BEFORE recursing[cite: 2].
        """
        cols = set()
        pos_diag = set()  # row + col
        neg_diag = set()  # row - col
        
        results = []
        # We only need a 1D array to track state! 
        # board[row] = col
        board = []

        def backtrack(row: int):
            # Base Case: We successfully placed n queens
            if row == n:
                # Convert the 1D state into the 2D string grid format
                formatted_board = []
                for col_idx in board:
                    row_str = '.' * col_idx + 'Q' + '.' * (n - 1 - col_idx)
                    formatted_board.append(row_str)
                results.append(formatted_board)
                return

            # Explore all columns for the current row
            for col in range(n):
                # PRUNE HERE: Check validity before recursing[cite: 2]
                if (col in cols or 
                    (row + col) in pos_diag or 
                    (row - col) in neg_diag):
                    continue

                # 1. CHOOSE
                cols.add(col)
                pos_diag.add(row + col)
                neg_diag.add(row - col)
                board.append(col)

                # 2. EXPLORE
                backtrack(row + 1)

                # 3. UNCHOOSE
                cols.remove(col)
                pos_diag.remove(row + col)
                neg_diag.remove(row - col)
                board.pop()

        backtrack(0)
        return results

    # ------------------------------------------------------------------
    # Deliberate breakage / Bad Approach.
    # ------------------------------------------------------------------
    def solveNQueens_raw_generate(self, n: int) -> int:
        """
        ✗ HORRIBLY SLOW — This simulates generating all n^n one-queen-per-row 
        placements, checking validity only at the leaves[cite: 2].
        Returns just the count for benchmarking purposes.
        """
        valid_count = 0
        board = []

        def is_valid(b):
            for i in range(len(b)):
                for j in range(i + 1, len(b)):
                    # Check col
                    if b[i] == b[j]: return False
                    # Check diags
                    if abs(i - j) == abs(b[i] - b[j]): return False
            return True

        def backtrack(row):
            nonlocal valid_count
            if row == n:
                if is_valid(board):
                    valid_count += 1
                return
            
            for col in range(n):
                board.append(col)
                backtrack(row + 1)
                board.pop()

        backtrack(0)
        return valid_count


# ==============================================================================
# TESTS — run:  python 013_n_queens_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        (4, [[".Q..","...Q","Q...","..Q."],["..Q.","Q...","...Q",".Q.."]]),
        (1, [["Q"]]),
        (2, []),  # No solution for 2x2
        (3, []),  # No solution for 3x3
    ]
    
    all_ok = True
    print("--- Correctness Tests ---")
    for n, expected in cases:
        got = sol.solveNQueens(n)
        got_sorted = sorted(["".join(b) for b in got]) if got else []
        exp_sorted = sorted(["".join(b) for b in expected])
        
        ok = got_sorted == exp_sorted
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n} -> found {len(got)} solutions")

    # ----------------------------------------------------------------------
    # Measured: The astronomical difference pruning makes[cite: 2].
    # ----------------------------------------------------------------------
    print("\n--- Measured: Raw Generation vs Pruning (Tree Nodes Visited) ---")
    
    def solve_counted_pruned(n):
        cols, pos_diag, neg_diag = set(), set(), set()
        nodes = 0
        def backtrack(row):
            nonlocal nodes
            nodes += 1  # Count this node visit
            if row == n: return
            
            for col in range(n):
                if (col in cols or (row + col) in pos_diag or (row - col) in neg_diag):
                    continue
                cols.add(col); pos_diag.add(row + col); neg_diag.add(row - col)
                backtrack(row + 1)
                cols.remove(col); pos_diag.remove(row + col); neg_diag.remove(row - col)
        
        backtrack(0)
        return nodes

    print(f"  {'n':<3} {'Raw Search Space (n^n) Nodes':>30} {'Pruned Nodes Visited':>25}")
    for n in (4, 6, 8):
        raw_leaves = n**n
        
        # We calculate total raw nodes in the complete n-ary tree:
        # Sum(n^k) for k=0 to n = (n^(n+1) - 1) / (n - 1)
        raw_total_nodes = (n**(n+1) - 1) // (n - 1) 
        
        pruned_nodes = solve_counted_pruned(n)
        
        print(f"  {n:<3} {raw_total_nodes:>30,} {pruned_nodes:>25,}")

    print("\n  For n=8, the raw one-queen-per-row search space explores nearly")
    print("  19 million nodes. With O(1) set pruning applied BEFORE recursing,")
    print("  the actual number of tree nodes visited drops to 2,057[cite: 2].")
    print("  This is why constraint satisfaction pruning is not an optimization—")
    print("  it is what makes the algorithm tractable[cite: 2].")

    # ----------------------------------------------------------------------
    # Measured: Wall-clock timing.
    # ----------------------------------------------------------------------
    print("\n--- Measured Wall-Clock Time ---")
    bench_n = 7
    print(f"  Benchmarking n={bench_n}...")
    
    t0 = time.perf_counter()
    sol.solveNQueens_raw_generate(bench_n)
    t1 = time.perf_counter()
    
    sol.solveNQueens(bench_n)
    t2 = time.perf_counter()
    
    raw_ms = (t1 - t0) * 1000
    prune_ms = (t2 - t1) * 1000
    
    print(f"  Raw Generate-All: {raw_ms:>10.2f} ms")
    print(f"  O(1) Set Pruning: {prune_ms:>10.2f} ms")
    if prune_ms > 0:
        print(f"  Pruning is {raw_ms / prune_ms:,.0f}x faster.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()