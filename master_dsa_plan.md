# MAANG/FAANG DSA Master Plan 🚀

**Target date: Monday, 7 December 2026** · 13 weeks · 25 hrs/week · ~325 hours · 150 problems

This document is our single source of truth. It is not a reading list — it is a schedule. Work it top to bottom.

---

## §0 · How To Use This Document

### Status legend

| Mark | Meaning |
|:---:|---|
| `[ ]` | Not started |
| `[/]` | In progress |
| `[x]` | **Solved** — you got it working, once |
| `[★]` | **Mastered** — solved cold, correct on first run, ≤20 min, narrated out loud |

> **Only `[★]` counts toward interview readiness.** `[x]` means you've seen it. `[★]` means you own it. Most people confuse the two and that is exactly why they fail loops after "doing 300 problems."

In the problem tables, the **Py** and **Go** columns track each language separately:
`⬜` = todo · `✅` = done · `—` = optional in this language, skip without guilt.

### Workflow Agreement

1. **Problem Setup**: For each topic, I (your Senior Staff Engineer) create the problem file.
   - In Python (`PyDSA/`), a single file (e.g. `PyDSA/binary_search/koko_bananas.py`).
   - In Go (`GoDSA/`), a directory with a Go file (e.g. `GoDSA/binary_search/koko_bananas/koko_bananas.go`).
   - I write the problem description, constraints, and a call-tree/visual where it helps, as comments at the top.
2. **Your Attempt**: You attempt to solve the problem.
3. **Review & Guidance**:
   - **If you solve it**: I review your code, give feedback on Time/Space complexity, explain the optimal approach, and add step-by-step explanations as comments in your file.
   - **If you get stuck**: I guide you step-by-step with hints and ultimately provide the solution with thorough, commented explanations in the file.

### The hint ladder (this is the part that makes the 25 hrs/week work)

```
0:00 ──────────────► 25:00 ──────────► 40:00 ──────────► done
     solo attempt          ONE hint         full solution
                        (not the answer)    + walkthrough
                                            + auto-scheduled re-solve
```

Do not break the timer in either direction. Peeking at 10 minutes robs you of the struggle that
builds recall. Grinding for 90 minutes burns an hour you needed for three other problems.

**Any problem that required the full solution is automatically added to `REVIEW_LEDGER.md` for a cold re-solve.** No exceptions, no self-negotiation.

### Language policy

You're doing both languages. To make that fit in 325 hours instead of 500:

- **Python is your interview language.** It gets every problem. Write it the way you'd write it live.
- **Go is mandatory** where manual pointer and memory work *is* the lesson: linked lists, trees, tries, union-find, and the from-scratch builds. These are marked `⬜` in the Go column.
- **Go is optional** where the Go version teaches syntax rather than algorithms — most DP, sliding window, and hashing problems. These are marked `—`. Do them if you have slack in the week; drop them without guilt if you don't.

---

## §1 · Where You Are Right Now

Snapshot taken 7 September 2026, read from the actual source files.

| | Items |
|---|---|
| ✅ **Solved, both languages** | Linked List basics, Factorial, Fibonacci, Palindrome (two-pointer recursion), Subsets |
| ✅ **Solved, Python only** | Reverse Linked List, Permutations |
| ⬜ **Open stubs** | `PyDSA/recursion/combination_sum.py` · `GoDSA/recursion/permutations/permutations.go` · `GoDSA/reverse_linked_list/reverse_linked_list.go` |

**What you already have going for you:** your `subsets` and `permutations` solutions are clean, idiomatic, and correctly handle the copy-on-append trap (`subset[:]` in Python, `copy()` in Go). Your recursive `reverseList` correctly nulls `head.next` to avoid the cycle. That's a real foundation — recursion and backtracking are where most people stall out, and you're past it.

**What's missing and matters:** binary search (a top-5 interview pattern, absent from the old plan entirely), graphs, DP, heaps, and intervals. That's the bulk of the next 13 weeks.

---

## §2 · The 13-Week Schedule

| Wk | Dates (2026) | Focus | New | Milestone |
|:--:|---|---|:--:|---|
| **1** | Sep 7–13 | Close out Recursion & Backtracking | 11 | Backtracking done |
| **2** | Sep 14–20 | Arrays & Hashing · Two Pointers | 13 | |
| **3** | Sep 21–27 | Sliding Window · Prefix Sums | 12 | |
| **4** | Sep 28–Oct 4 | **Binary Search** · Stacks & Monotonic Stack | 14 | Phase 1 complete |
| **5** | Oct 5–11 | Linked Lists *(both languages)* | 11 | LRU Cache from scratch |
| **6** | Oct 12–18 | Trees I: traversals, DFS/BFS | 12 | 📐 **System design starts** |
| **7** | Oct 19–25 | Trees II: BST, construction · Tries | 12 | Phase 2 complete |
| **8** | Oct 26–Nov 1 | Heaps · Intervals · Greedy | 14 | Min-heap from scratch |
| **9** | Nov 2–8 | Graphs I: grids, topological sort | 12 | |
| **10** | Nov 9–15 | Graphs II: Union-Find, Dijkstra, MST · Bits | 13 | 🎤 **Behavioral starts** |
| **11** | Nov 16–22 | 1D Dynamic Programming | 12 | 🧪 **Mocks begin (2/wk)** |
| **12** | Nov 23–29 | 2D Dynamic Programming · Math & Geometry | 13 | Phase 4 complete |
| **13** | Nov 30–Dec 6 | Remediation · Full-loop simulation | — | **Interview ready** |

**150 problems.** The counts above are *new* problems. Two sections carry one extra table row that does **not** add to the weekly load: Week 5 re-lists Reverse Linked List (a Week 1 carry-over, Go side only), and Week 12 closes with an optional 3-problem stretch row.

### How to budget a 25-hour week

| Block | Hours | What |
|---|:--:|---|
| New problems | ~15 | ~12 problems at the hint-ladder cadence |
| Review (`REVIEW_LEDGER.md`) | ~5 | Cold re-solves that came due |
| From-scratch builds & pattern notes | ~2 | The mastery thread |
| System design / behavioral | ~3 | From Week 6 / Week 10 onward |

**~20% of every week is review, not new material.** This is deliberate. A sprint that is 100% new material is how people arrive at week 13 having forgotten week 3.

---

## §3 · Pattern Recognition Table

The single highest-leverage page in this document. Interviews are won in the first 90 seconds, when you map a problem statement onto a technique. Read this before every session until it's automatic.

| When the problem says… | Reach for | Typical cost |
|---|---|---|
| "sorted array" + find a pair/triple | **Two pointers** | O(n) |
| "sorted array" + find a specific value or boundary | **Binary search** | O(log n) |
| "minimize the maximum" / "smallest k such that…" | **Binary search on the answer** | O(n log range) |
| "contiguous subarray/substring" + longest/shortest | **Sliding window** | O(n) |
| "subarray sums" + many queries | **Prefix sums** | O(n) build, O(1) query |
| "have I seen this before?" / dedupe / count frequency | **Hash map / set** | O(1) avg |
| "next greater / next smaller element" | **Monotonic stack** | O(n) |
| "valid parentheses" / "undo the last thing" | **Stack** | O(n) |
| "top k" / "k largest" / "k closest" | **Heap** (size k) | O(n log k) |
| "median of a stream" | **Two heaps** (max-heap + min-heap) | O(log n) insert |
| "merge k sorted things" | **Heap** or divide & conquer | O(N log k) |
| "all combinations / permutations / subsets" | **Backtracking** | O(2ⁿ) / O(n!) |
| "place items subject to constraints" (N-Queens, Sudoku) | **Backtracking + pruning** | exponential, pruned |
| "shortest path, unweighted" | **BFS** | O(V+E) |
| "shortest path, weighted, non-negative" | **Dijkstra** | O(E log V) |
| "shortest path, negative weights / ≤k hops" | **Bellman-Ford** | O(V·E) |
| "prerequisites" / "build order" / "can this be ordered?" | **Topological sort** (Kahn's or DFS) | O(V+E) |
| "are these connected?" / "count the groups" | **Union-Find** or DFS flood fill | ~O(α(n)) |
| "connect everything at minimum cost" | **MST** (Prim / Kruskal) | O(E log V) |
| "count the ways" / "can I reach X?" / "min cost to…" | **Dynamic programming** | varies |
| "longest/shortest subsequence between two strings" | **2D DP** | O(m·n) |
| "make change" / "fill a knapsack" | **DP** (unbounded / 0-1 knapsack) | O(n·target) |
| "prefix" / "autocomplete" / "starts with" | **Trie** | O(len) |
| "overlapping ranges" / "meeting rooms" | **Sort by start, sweep** | O(n log n) |
| "cycle in a linked list" / "find the duplicate" | **Fast & slow pointers** (Floyd) | O(n), O(1) space |
| "in-place, O(1) extra space" required | Two pointers, in-place swaps, bit tricks | |
| "count with no extra space" / "appears once" | **XOR / bit manipulation** | O(n) |
| "tree, but the answer needs info from both children" | **Post-order DFS returning a tuple** | O(n) |

### Reading the constraints

The `n` in the constraints tells you the intended complexity before you've thought about the problem at all:

| n up to | You can afford | Which means |
|---|---|---|
| 10–12 | O(n!) | Permutations, brute-force backtracking |
| 15–22 | O(2ⁿ) | Subsets, bitmask DP |
| 100 | O(n³) | Triple loop, Floyd-Warshall |
| 1,000–5,000 | O(n²) | Double loop, most 2D DP |
| 10⁵–10⁶ | O(n log n) | Sort, heap, binary search |
| 10⁷–10⁸ | O(n) | Single pass, two pointers |
| 10⁹+ | O(log n) or O(1) | Binary search, math |

---

## §4 · The Curriculum

---

### Phase 1.5 · Recursion & Backtracking — Week 1

*You're mid-phase. Finish it before opening anything new.*

**Already done:**

| Status | Problem | Py | Go |
|:--:|---|:--:|:--:|
| `[x]` | Linear Recursion (Factorial) | ✅ | ✅ |
| `[x]` | Branching Recursion & Call Trees (Fibonacci) | ✅ | ✅ |
| `[x]` | Recursion with State/Pointers (Palindrome) | ✅ | ✅ |
| `[x]` | Subsets — Backtracking L1: include/exclude | ✅ | ✅ |
| `[/]` | Permutations — Backtracking L2: choose from available | ✅ | ⬜ |

**Week 1 work:**

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[/]` | **Combination Sum** *(open stub)* | Med | ⬜ | ⬜ | Pruning + reuse via `start` index |
| `[/]` | **Permutations** *(Go stub)* | Med | ✅ | ⬜ | Go slice-copy discipline |
| `[/]` | **Reverse Linked List** *(Go stub)* | Easy | ✅ | ⬜ | Pointer rewiring in Go |
| `[ ]` | Combinations (n choose k) | Med | ⬜ | — | Fixed-length backtracking |
| `[ ]` | Generate Parentheses | Med | ⬜ | — | Constraint-guided branching |
| `[ ]` | Subsets II | Med | ⬜ | — | Skip duplicates: `if i>start && a[i]==a[i-1]` |
| `[ ]` | Combination Sum II | Med | ⬜ | — | Sort + skip dupes + no reuse |
| `[ ]` | Letter Combinations of a Phone Number | Med | ⬜ | — | Cartesian product via recursion |
| `[ ]` | Palindrome Partitioning | Med | ⬜ | — | Backtrack over cut positions |
| `[ ]` | **N-Queens** 👑 | Hard | ⬜ | ⬜ | L4: 2D constraint sets (col, diag, anti-diag) |
| `[ ]` | **Word Search** 👑 | Med | ⬜ | ⬜ | L5: grid backtracking + visited-marking |

> 👑 marks the **boss problem** of a ladder — the one that proves you own the pattern.

---

### Phase 1 · Foundations — Weeks 2–4

#### Arrays & Hashing — Week 2

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Contains Duplicate | Easy | ⬜ | — | Set membership |
| `[ ]` | Valid Anagram | Easy | ⬜ | — | Frequency count |
| `[ ]` | Two Sum | Easy | ⬜ | — | Complement in a hash map |
| `[ ]` | Group Anagrams | Med | ⬜ | — | Canonical key (sorted str / 26-count tuple) |
| `[ ]` | Top K Frequent Elements | Med | ⬜ | — | Bucket sort by frequency — O(n) |
| `[ ]` | Encode and Decode Strings | Med | ⬜ | — | Length-prefix delimiting |
| `[ ]` | Product of Array Except Self | Med | ⬜ | — | Prefix × suffix, no division |
| `[ ]` | **Longest Consecutive Sequence** 👑 | Med | ⬜ | — | Only start counting at sequence heads |

#### Two Pointers — Week 2

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Valid Palindrome | Easy | ⬜ | — | Converge from both ends |
| `[ ]` | Two Sum II (sorted) | Med | ⬜ | — | Move the pointer that fixes the error |
| `[ ]` | 3Sum | Med | ⬜ | — | Sort, fix one, two-pointer the rest |
| `[ ]` | Container With Most Water | Med | ⬜ | — | Always move the shorter wall |
| `[ ]` | **Trapping Rain Water** 👑 | Hard | ⬜ | — | Track max-left / max-right |

#### Sliding Window — Week 3

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Best Time to Buy and Sell Stock | Easy | ⬜ | — | Track running min |
| `[ ]` | Longest Substring Without Repeating Characters | Med | ⬜ | — | Shrink on duplicate |
| `[ ]` | Longest Repeating Character Replacement | Med | ⬜ | — | Window valid while `len - maxFreq ≤ k` |
| `[ ]` | Permutation in String | Med | ⬜ | — | Fixed-size window + count match |
| `[ ]` | Fruit Into Baskets | Med | ⬜ | — | At most 2 distinct |
| `[ ]` | **Minimum Window Substring** 👑 | Hard | ⬜ | — | Expand to satisfy, shrink to optimize |
| `[ ]` | Sliding Window Maximum | Hard | ⬜ | ⬜ | Monotonic deque |

#### Prefix Sums — Week 3

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Range Sum Query — Immutable | Easy | ⬜ | — | Precompute cumulative array |
| `[ ]` | Find Pivot Index | Easy | ⬜ | — | `left == total - left - a[i]` |
| `[ ]` | Subarray Sum Equals K | Med | ⬜ | — | Hash map of prefix-sum counts |
| `[ ]` | Contiguous Array | Med | ⬜ | — | Map 0→−1, find equal prefix sums |
| `[ ]` | Range Sum Query 2D — Immutable | Med | ⬜ | — | Inclusion–exclusion on 2D prefix |

#### Binary Search — Week 4 ⭐ *new to this plan*

The pattern the old plan was missing entirely. Master the **boundary** form (`lo < hi`, return `lo`) — it handles far more interview problems than the "find exact value" form.

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Binary Search | Easy | ⬜ | ⬜ | Get the invariant right, once |
| `[ ]` | Search a 2D Matrix | Med | ⬜ | — | Treat as a flattened sorted array |
| `[ ]` | Koko Eating Bananas | Med | ⬜ | ⬜ | **Binary search on the answer** |
| `[ ]` | Find Minimum in Rotated Sorted Array | Med | ⬜ | — | Compare mid to right |
| `[ ]` | Search in Rotated Sorted Array | Med | ⬜ | — | One half is always sorted |
| `[ ]` | Time Based Key-Value Store | Med | ⬜ | — | Binary search for floor timestamp |
| `[ ]` | **Median of Two Sorted Arrays** 👑 | Hard | ⬜ | — | Binary search the partition point |

#### Stacks & Monotonic Stack — Week 4

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Valid Parentheses | Easy | ⬜ | ⬜ | Match-and-pop |
| `[ ]` | Min Stack | Med | ⬜ | ⬜ | Auxiliary stack of running minima |
| `[ ]` | Evaluate Reverse Polish Notation | Med | ⬜ | — | Operand stack |
| `[ ]` | Implement Queue using Stacks | Easy | ⬜ | ⬜ | Amortized O(1) with two stacks |
| `[ ]` | Daily Temperatures | Med | ⬜ | — | **Monotonic decreasing stack** |
| `[ ]` | Car Fleet | Med | ⬜ | — | Sort by position, stack of arrival times |
| `[ ]` | **Largest Rectangle in Histogram** 👑 | Hard | ⬜ | — | Monotonic increasing stack |

🔨 **From scratch this phase:** dynamic array (with amortized doubling), hash map with chaining.

---

### Phase 2 · Linked Lists & Trees — Weeks 5–7

#### Linked Lists — Week 5 · *both languages mandatory*

Go is required across this entire section. Manual pointer manipulation without a GC-shaped safety net is the whole lesson, and it's what makes the tree section click later.

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[x]` | Reverse Linked List | Easy | ✅ | ⬜ | *(Go stub — Week 1)* |
| `[ ]` | Merge Two Sorted Lists | Easy | ⬜ | ⬜ | Dummy head |
| `[ ]` | Linked List Cycle | Easy | ⬜ | ⬜ | **Fast & slow pointers** |
| `[ ]` | Middle of the Linked List | Easy | ⬜ | ⬜ | Fast moves 2, slow moves 1 |
| `[ ]` | Remove Nth Node From End | Med | ⬜ | ⬜ | Gap of n between pointers |
| `[ ]` | Reorder List | Med | ⬜ | ⬜ | Split + reverse + interleave |
| `[ ]` | Add Two Numbers | Med | ⬜ | ⬜ | Carry propagation |
| `[ ]` | Copy List with Random Pointer | Med | ⬜ | ⬜ | Two-pass with an old→new map |
| `[ ]` | Find the Duplicate Number | Med | ⬜ | — | Floyd's cycle detection on an array |
| `[ ]` | **LRU Cache** 👑 | Med | ⬜ | ⬜ | Hash map + doubly linked list |
| `[ ]` | Merge k Sorted Lists | Hard | ⬜ | — | Heap, or pairwise merge |
| `[ ]` | Reverse Nodes in k-Group | Hard | ⬜ | ⬜ | The pointer-discipline final boss |

#### Binary Trees I: Traversal & DFS — Week 6

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Binary Tree Traversals (in/pre/post, **iterative**) | Med | ⬜ | ⬜ | Explicit stack — know all three |
| `[ ]` | Invert Binary Tree | Easy | ⬜ | ⬜ | Swap children, recurse |
| `[ ]` | Maximum Depth of Binary Tree | Easy | ⬜ | ⬜ | `1 + max(left, right)` |
| `[ ]` | Same Tree | Easy | ⬜ | ⬜ | Structural comparison |
| `[ ]` | Subtree of Another Tree | Easy | ⬜ | — | Same Tree at every node |
| `[ ]` | Balanced Binary Tree | Easy | ⬜ | — | Return `(height, isBalanced)` together |
| `[ ]` | Diameter of Binary Tree | Easy | ⬜ | ⬜ | Return height, track best via side effect |
| `[ ]` | Path Sum | Easy | ⬜ | — | Carry remaining target down |
| `[ ]` | Binary Tree Level Order Traversal | Med | ⬜ | ⬜ | **BFS with level-sized batches** |
| `[ ]` | Binary Tree Right Side View | Med | ⬜ | — | Last node of each BFS level |
| `[ ]` | Count Good Nodes in Binary Tree | Med | ⬜ | — | Pass max-so-far down |
| `[ ]` | Lowest Common Ancestor of a BST | Med | ⬜ | ⬜ | Walk down using BST ordering |

#### Binary Trees II: BST & Construction — Week 7

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Validate Binary Search Tree | Med | ⬜ | ⬜ | Pass down `(min, max)` bounds |
| `[ ]` | Kth Smallest Element in a BST | Med | ⬜ | ⬜ | In-order traversal is sorted |
| `[ ]` | Delete Node in a BST | Med | ⬜ | ⬜ | Replace with in-order successor |
| `[ ]` | Lowest Common Ancestor of a Binary Tree | Med | ⬜ | — | Post-order, first node seeing both |
| `[ ]` | Construct Binary Tree from Preorder & Inorder | Med | ⬜ | — | Preorder gives root, inorder gives split |
| `[ ]` | Flatten Binary Tree to Linked List | Med | ⬜ | ⬜ | Reverse post-order rewiring |
| `[ ]` | **Binary Tree Maximum Path Sum** 👑 | Hard | ⬜ | — | Return best *downward* path, track best *through* |
| `[ ]` | Serialize and Deserialize Binary Tree | Hard | ⬜ | — | Preorder with null sentinels |

#### Tries — Week 7

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Implement Trie (Prefix Tree) | Med | ⬜ | ⬜ | Children map + `isEnd` flag |
| `[ ]` | Design Add and Search Words | Med | ⬜ | ⬜ | `.` wildcard → branch into all children |
| `[ ]` | Replace Words | Med | ⬜ | — | Walk the trie, stop at first root |
| `[ ]` | **Word Search II** 👑 | Hard | ⬜ | — | Trie + grid backtracking (Week 1 pays off) |

🔨 **From scratch this phase:** LRU cache, trie, BST insert/delete.

---

### Phase 3 · Graphs — Weeks 9–10

#### Graphs I: Traversal & Ordering — Week 9

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Number of Islands | Med | ⬜ | ⬜ | Flood fill, count launches |
| `[ ]` | Max Area of Island | Med | ⬜ | — | Flood fill returning a size |
| `[ ]` | Clone Graph | Med | ⬜ | ⬜ | DFS + old→new map |
| `[ ]` | Islands and Treasure (Walls and Gates) | Med | ⬜ | — | **Multi-source BFS** |
| `[ ]` | Rotting Oranges | Med | ⬜ | — | Multi-source BFS, count levels as time |
| `[ ]` | Pacific Atlantic Water Flow | Med | ⬜ | — | Reverse the flow, DFS from both borders |
| `[ ]` | Surrounded Regions | Med | ⬜ | — | Mark from the border, flip the rest |
| `[ ]` | Number of Connected Components | Med | ⬜ | ⬜ | DFS count, or Union-Find |
| `[ ]` | Graph Valid Tree | Med | ⬜ | — | Connected ∧ `edges == n−1` |
| `[ ]` | Course Schedule | Med | ⬜ | ⬜ | **Cycle detection** (3-color DFS) |
| `[ ]` | Course Schedule II | Med | ⬜ | ⬜ | **Topological sort** (Kahn's) |
| `[ ]` | **Word Ladder** 👑 | Hard | ⬜ | — | BFS over an implicit graph |

#### Graphs II: Weighted & Union-Find — Week 10

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Redundant Connection | Med | ⬜ | ⬜ | **Union-Find** — first edge that closes a cycle |
| `[ ]` | Min Cost to Connect All Points | Med | ⬜ | ⬜ | **MST** — Prim's with a heap |
| `[ ]` | Network Delay Time | Med | ⬜ | ⬜ | **Dijkstra** |
| `[ ]` | Cheapest Flights Within K Stops | Med | ⬜ | — | **Bellman-Ford** (k+1 relaxations) |
| `[ ]` | Swim in Rising Water | Hard | ⬜ | — | Dijkstra on max-edge, or binary search + BFS |
| `[ ]` | Reconstruct Itinerary | Hard | ⬜ | — | Hierholzer's (Eulerian path) |
| `[ ]` | **Alien Dictionary** 👑 | Hard | ⬜ | — | Build the graph, then topo sort |

#### Bit Manipulation — Week 10

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Single Number | Easy | ⬜ | — | XOR cancels pairs |
| `[ ]` | Number of 1 Bits | Easy | ⬜ | — | `n & (n−1)` clears the lowest set bit |
| `[ ]` | Counting Bits | Easy | ⬜ | — | `dp[i] = dp[i>>1] + (i&1)` |
| `[ ]` | Reverse Bits | Easy | ⬜ | — | Shift out, shift in |
| `[ ]` | Missing Number | Easy | ⬜ | — | XOR all indices and values |
| `[ ]` | Sum of Two Integers | Med | ⬜ | — | XOR = sum, AND<<1 = carry |

🔨 **From scratch this phase:** union-find with path compression + union by rank.

---

### Phase 4 · Optimization — Weeks 8, 11–12

#### Heaps / Priority Queues — Week 8

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Kth Largest Element in a Stream | Easy | ⬜ | ⬜ | Min-heap capped at size k |
| `[ ]` | Last Stone Weight | Easy | ⬜ | ⬜ | Max-heap (negate in Python) |
| `[ ]` | K Closest Points to Origin | Med | ⬜ | — | Heap by squared distance |
| `[ ]` | Kth Largest Element in an Array | Med | ⬜ | — | Heap, or quickselect for O(n) avg |
| `[ ]` | Task Scheduler | Med | ⬜ | — | Greedy on highest remaining count |
| `[ ]` | **Find Median from Data Stream** 👑 | Hard | ⬜ | ⬜ | **Two heaps**, kept balanced |

#### Intervals — Week 8

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Insert Interval | Med | ⬜ | — | Three phases: before / overlap / after |
| `[ ]` | Merge Intervals | Med | ⬜ | — | Sort by start, extend the end |
| `[ ]` | Non-overlapping Intervals | Med | ⬜ | — | Sort by **end**, greedily keep |
| `[ ]` | Meeting Rooms | Easy | ⬜ | — | Sort, check adjacency |
| `[ ]` | **Meeting Rooms II** 👑 | Med | ⬜ | — | Heap of end times, or a start/end sweep |

#### Greedy — Week 8

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Maximum Subarray | Med | ⬜ | — | Kadane's — reset when the sum goes negative |
| `[ ]` | Jump Game | Med | ⬜ | — | Track furthest reachable index |
| `[ ]` | Gas Station | Med | ⬜ | — | Restart at the failure point |

#### 1D Dynamic Programming — Week 11

Work every problem **memoization first, then tabulation**. Recognizing the recurrence matters more than the table mechanics, and you already have the recursion instincts from Phase 1.5.

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Climbing Stairs | Easy | ⬜ | — | Fibonacci in disguise |
| `[ ]` | Min Cost Climbing Stairs | Easy | ⬜ | — | Choose the cheaper predecessor |
| `[ ]` | House Robber | Med | ⬜ | — | `max(skip, take + dp[i−2])` |
| `[ ]` | House Robber II | Med | ⬜ | — | Run it twice on the circular split |
| `[ ]` | Longest Palindromic Substring | Med | ⬜ | — | Expand around each center |
| `[ ]` | Palindromic Substrings | Med | ⬜ | — | Same expansion, count instead |
| `[ ]` | Decode Ways | Med | ⬜ | — | Branch on 1-digit vs 2-digit |
| `[ ]` | Coin Change | Med | ⬜ | ⬜ | **Unbounded knapsack** — min coins |
| `[ ]` | Maximum Product Subarray | Med | ⬜ | — | Track running min *and* max |
| `[ ]` | Word Break | Med | ⬜ | — | `dp[i]` = prefix is segmentable |
| `[ ]` | Longest Increasing Subsequence | Med | ⬜ | — | O(n²) DP, then the O(n log n) patience form |
| `[ ]` | **Partition Equal Subset Sum** 👑 | Med | ⬜ | — | **0-1 knapsack** on `sum/2` |

#### 2D Dynamic Programming — Week 12

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Unique Paths | Med | ⬜ | — | The grid-DP starting point |
| `[ ]` | Longest Common Subsequence | Med | ⬜ | — | The canonical two-string grid |
| `[ ]` | Coin Change II | Med | ⬜ | — | Count combinations, not permutations |
| `[ ]` | Target Sum | Med | ⬜ | — | Knapsack over reachable sums |
| `[ ]` | Best Time to Buy/Sell Stock with Cooldown | Med | ⬜ | — | **State machine DP** |
| `[ ]` | Interleaving String | Med | ⬜ | — | 2D over two consumption pointers |
| `[ ]` | Longest Increasing Path in a Matrix | Hard | ⬜ | — | DFS + memo on a DAG |
| `[ ]` | **Edit Distance** 👑 | Med | ⬜ | — | insert / delete / replace recurrence |
| `[ ]` | *Stretch:* Distinct Subsequences · Burst Balloons · Regex Matching | Hard | — | — | Only if Week 12 has slack |

#### Math & Geometry — Week 12

| Status | Problem | Diff | Py | Go | Key idea |
|:--:|---|:--:|:--:|:--:|---|
| `[ ]` | Rotate Image | Med | ⬜ | — | Transpose, then reverse rows |
| `[ ]` | Spiral Matrix | Med | ⬜ | — | Four shrinking boundaries |
| `[ ]` | Set Matrix Zeroes | Med | ⬜ | — | Use row 0 / col 0 as the marker store |
| `[ ]` | Happy Number | Easy | ⬜ | — | Cycle detection on digit squares |
| `[ ]` | Pow(x, n) | Med | ⬜ | — | Fast exponentiation by squaring |

🔨 **From scratch this phase:** min-heap with sift-up/sift-down.

---

## §5 · Complexity Reference Card

| Structure | Access | Search | Insert | Delete | Space |
|---|:--:|:--:|:--:|:--:|:--:|
| Array (dynamic) | O(1) | O(n) | O(1)* | O(n) | O(n) |
| Hash map / set | — | O(1)† | O(1)† | O(1)† | O(n) |
| Linked list (singly) | O(n) | O(n) | O(1)‡ | O(1)‡ | O(n) |
| Stack / Queue | O(n) | O(n) | O(1) | O(1) | O(n) |
| Binary heap | O(1) peek | O(n) | O(log n) | O(log n) | O(n) |
| BST (balanced) | O(log n) | O(log n) | O(log n) | O(log n) | O(n) |
| BST (degenerate) | O(n) | O(n) | O(n) | O(n) | O(n) |
| Trie | — | O(L) | O(L) | O(L) | O(Σ·N·L) |
| Union-Find | — | ~O(α(n)) | ~O(α(n)) | — | O(n) |

\* amortized · † average; O(n) worst case on collisions · ‡ given the node reference · L = key length · α = inverse Ackermann, effectively ≤4

**Algorithms:** Sort O(n log n) · Binary search O(log n) · BFS/DFS O(V+E) · Dijkstra O(E log V) · Bellman-Ford O(V·E) · Topo sort O(V+E) · Prim/Kruskal O(E log V)

**Recursion space:** call depth counts. A recursive tree traversal is O(h) space — O(log n) balanced, **O(n) worst case**. Say this out loud in interviews; most candidates forget stack space entirely.

---

## §6 · The Interview Script

A 45-minute round is a communication test wearing an algorithms costume. Run this sequence every single time, including on practice problems, until it's muscle memory.

| Phase | Time | What you do |
|---|:--:|---|
| **1. Clarify** | 2–3 min | Restate the problem. Ask about input size, duplicates, empty input, negative values, sorted-ness, return format. |
| **2. Example** | 2 min | Write a small concrete example. Walk it by hand. Add one edge case. |
| **3. Brute force** | 3 min | State it out loud with its complexity. Do **not** code it. "The naive approach is O(n²) because… — let me see if I can do better." |
| **4. Optimize** | 5–8 min | Name the pattern (§3). Explain *why* it applies. Get buy-in before coding. |
| **5. State complexity** | 1 min | Time **and** space, **before** writing code. This signals you know where you're going. |
| **6. Code** | 15–20 min | Narrate as you write. Meaningful names. Handle edge cases explicitly. |
| **7. Dry run** | 5 min | Trace your example line by line. Then trace an edge case. Find your own bugs before they do. |

### When you're stuck — say these, don't go silent

Silence is the only unrecoverable failure mode in an interview. Stuck is fine and expected; stuck *and quiet* reads as frozen.

- "Let me think about the brute force first and optimize from there."
- "I notice this input is sorted — that usually means two pointers or binary search."
- "I want to try a small example to find the pattern."
- "I'm considering two approaches: X and Y. X is O(n log n) but simpler; Y is O(n) with more edge cases. Which would you prefer I code?"
- "I'm stuck on the recurrence. Could I get a nudge on the state definition?" *(asking a specific question is far better than a general "I'm stuck")*

### Red flags to eliminate from your own practice

Coding before stating the approach · Silence longer than ~20 seconds · Ignoring an interviewer's hint (a hint is *always* a course correction — take it immediately) · Saying "done" without tracing a single example · Not mentioning space complexity.

---

## §7 · System Design Track — Weeks 6–13

~2–3 hrs/week. You will get 1–2 of these rounds in a MAANG loop, and for L5+ they carry the same weight as coding.

**Weeks 6–7 — Building blocks.** Latency numbers every engineer should know · vertical vs horizontal scaling · load balancers · caching (write-through, write-back, eviction — you'll have built an LRU in Week 5) · SQL vs NoSQL and when each breaks · sharding & partitioning · replication and consistency · CAP in practice · message queues · CDNs · rate limiting.

**Weeks 8–10 — The framework.** Practice this 45-minute shape until it's automatic:
`Requirements (functional + non-functional) → Scale estimation (QPS, storage, bandwidth) → API design → Data model → High-level diagram → Deep dive on 1–2 components → Bottlenecks & tradeoffs`

**Weeks 11–13 — Full designs.** One per session, timed: URL shortener → Pastebin → Twitter feed → Instagram → WhatsApp → Uber → YouTube → Google Drive → Web crawler → Ticketmaster (write contention) → Distributed rate limiter → Notification system.

**The bar:** there is no correct answer. They are grading whether you can drive an ambiguous conversation, quantify your choices, and name the tradeoff you're accepting.

---

## §8 · Behavioral Track — Weeks 10–13

~2 hrs/week. This round eliminates more strong coders than the algorithms do.

**Write 8–10 STAR stories** (Situation, Task, Action, Result) from your real experience. Each should be ~2 minutes spoken, heavy on *your specific actions*, and end with a **quantified** result. One story can serve several prompts — you need coverage, not volume.

Required coverage: a conflict with a teammate · a project you led · a hard technical decision + its tradeoff · a failure and what changed afterward · handling ambiguity · an inflexible deadline · convincing someone who disagreed with you · feedback that changed how you work · something you'd do differently.

**Also prepare:** a crisp 2-minute "tell me about yourself," a specific reason for *this* company, and 3–4 real questions to ask them.

**Amazon specifically** maps every question to its 16 Leadership Principles and weights this round heavily — tag your stories to principles if Amazon is a target.

---

## §9 · Mock Interview Protocol — Weeks 11–13

**Two per week, minimum.** Non-negotiable. Solving problems alone and performing under observation are different skills, and only one of them is being graded.

**Rules:** 45 minutes, timed · a problem you have never seen · **out loud, the entire time** · in a plain editor with no autocomplete, no linter, no test runner · webcam on if it's a real remote loop.

**Sources:** Pramp / interviewing.io (free peer mocks) · a friend reading from this document's problem tables · solo with a recording, then watch yourself back — brutal, and the fastest fix for filler words and silence.

**After every mock, log:** the pattern you were asked · time to identify it · whether you got stuck and where · communication quality (1–5) · **the one thing to fix next time**.

Two consecutive mocks failing the same way means you go back to §4 and re-drill that pattern's ladder. That's what Week 13 is reserved for.

---

## §10 · The Retention System

### Rules of engagement

1. **25-minute timer.** One hint at 25. Full solution at 40. Never break it in either direction.
2. **Needed the solution → mandatory cold re-solve.** Logged in `REVIEW_LEDGER.md`, no self-negotiation.
3. **Cold means cold.** Blank file, no notes, no prior solution open, timed.
4. **Failing a re-solve resets the schedule to D+1.** The ladder only moves forward when you actually earn it.
5. **One line in the pattern journal per problem** — the trigger you should have spotted, and the technique. Not the code. The code you can re-derive; the trigger is what you're actually training.

### Spaced repetition

Every solved problem is re-solved at **D+1 → D+3 → D+10 → D+30**. Survive all four cold and it's `[★]`.

```
solve ──► D+1 ──► D+3 ──► D+10 ──► D+30 ──► [★] mastered
            │       │        │        │
            └───────┴────────┴────────┴──► fail? back to D+1
```

This is the mechanic that separates "I did 150 problems" from "I can solve 150 problems." Tracked in **`REVIEW_LEDGER.md`**.

### Weekly retro (30 min, every Sunday)

Update every checkbox here · promote anything that survived D+30 to `[★]` · note the two weakest patterns · adjust next week if you're drifting more than ~20% off the schedule.

### Readiness check — run this at the end of Week 12

- [ ] ≥120 problems at `[x]`, ≥80 at `[★]`
- [ ] Every pattern in §3 maps to a problem you can solve cold
- [ ] 6+ mocks completed, last 3 with no communication flags
- [ ] 4+ full system designs, done in 45 minutes each
- [ ] 8–10 STAR stories written and spoken out loud
- [ ] A Medium problem in an unfamiliar pattern: identified in <5 min, solved in <25

---

## Appendix · Repo Conventions

```
PyDSA/<topic>/<problem>.py              →  class Solution + test_<problem>()
GoDSA/<topic>/<problem>/<problem>.go    →  package main + main()
```

Run Python: `python PyDSA/recursion/combination_sum.py`
Run Go: `cd GoDSA && go run ./recursion/subsets`

Root-level legacy files (`PyDSA/link_list.py`, `PyDSA/double_link_list.py`, `PyDSA/reverse_linked_list.py`) stay where they are — new work goes into topic folders.

---

*Plan created 7 September 2026. Week 1 starts now: three open stubs, then the backtracking ladder.*
