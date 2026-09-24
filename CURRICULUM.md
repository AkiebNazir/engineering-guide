# Curriculum Index

**345 LeetCode problems** across **28 topics**, in Python and Go.

Easy **81** · Medium **208** · Hard **56**

Generated from `tools/problems.tsv` by `tools/gen_curriculum.py` — edit the TSV, not this file.

---

## Layout

Every topic folder opens with `_TOPIC_GUIDE.md`: what the structure is, how it works
*internally* in that language, how to build it from scratch, every algorithm that
operates on it, and when to reach for it. Then the problems.

```
PyDSA/01_arrays_hashing/
  _TOPIC_GUIDE.md                  <- read this first
  004_two_sum_question.py          <- problem + explanation + your stub
  004_two_sum_solution.py          <- solution + step-by-step walkthrough

GoDSA/01_arrays_hashing/
  _TOPIC_GUIDE.md
  004_two_sum/
    question.go                    <- problem + explanation + your stub
    solution.go                    <- solution + walkthrough + main()
```

Run them:

```bash
python  PyDSA/01_arrays_hashing/004_two_sum_solution.py
cd GoDSA && go run ./01_arrays_hashing/004_two_sum
```

---

## Progress

| # | Topic | Problems | Guide | Written |
|:--:|---|:--:|:--:|:--:|
| 01 | Arrays & Hashing | 14 | ✅ | 14/14 |
| 02 | Two Pointers | 11 | ✅ | 11/11 |
| 03 | Sliding Window | 15 | ✅ | 15/15 |
| 04 | Prefix Sum | 8 | ✅ | 8/8 |
| 05 | Binary Search | 12 | ✅ | 12/12 |
| 06 | Stack & Monotonic Stack | 14 | ✅ | 14/14 |
| 07 | Queue & Deque | 6 | ✅ | 6/6 |
| 08 | Linked List | 15 | ✅ | 15/15 |
| 09 | Recursion & Backtracking | 14 | ✅ | 14/14 |
| 10 | Binary Trees | 20 | ✅ | 20/20 |
| 11 | Binary Search Tree | 11 | ✅ | 11/11 |
| 12 | Heap / Priority Queue | 12 | ✅ | 12/12 |
| 13 | Trie (Prefix Tree) | 7 | ✅ | 7/7 |
| 14 | Graphs | 18 | ✅ | 18/18 |
| 15 | Advanced Graphs | 15 | ✅ | 15/15 |
| 16 | Dynamic Programming (1D) | 17 | ✅ | 17/17 |
| 17 | Dynamic Programming (2D) | 18 | ✅ | 18/18 |
| 18 | Greedy | 10 | ✅ | 10/10 |
| 19 | Intervals | 11 | ✅ | 11/11 |
| 20 | Bit Manipulation | 10 | ✅ | 10/10 |
| 21 | Math & Geometry | 10 | ✅ | 10/10 |
| 22 | Sorting Algorithms | 8 | ✅ | 8/8 |
| 23 | String Algorithms | 8 | ✅ | 8/8 |
| 24 | Matrix | 8 | ✅ | 8/8 |
| 25 | Design | 13 | ✅ | 13/13 |
| 26 | Segment Tree & Fenwick Tree | 6 | ✅ | 6/6 |
| 27 | Classic Algorithms (Randomized, Divide & Conquer, Quickselect) | 9 | ✅ | 9/9 |
| 28 | Recursion Mastery (Progressive Ladder) | 25 | ✅ | 25/25 |
| | **Total** | **345** | | **345/345** |

---

## 01 · Arrays & Hashing

`PyDSA/01_arrays_hashing/` · `GoDSA/01_arrays_hashing/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 1929 | [Concatenation of Array](https://leetcode.com/problems/concatenation-of-array/) | Easy |
| 002 | 217 | [Contains Duplicate](https://leetcode.com/problems/contains-duplicate/) | Easy |
| 003 | 242 | [Valid Anagram](https://leetcode.com/problems/valid-anagram/) | Easy |
| 004 | 1 | [Two Sum](https://leetcode.com/problems/two-sum/) | Easy |
| 005 | 169 | [Majority Element](https://leetcode.com/problems/majority-element/) | Easy |
| 006 | 448 | [Find All Numbers Disappeared in an Array](https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array/) | Easy |
| 007 | 49 | [Group Anagrams](https://leetcode.com/problems/group-anagrams/) | Medium |
| 008 | 347 | [Top K Frequent Elements](https://leetcode.com/problems/top-k-frequent-elements/) | Medium |
| 009 | 271 | [Encode and Decode Strings](https://leetcode.com/problems/encode-and-decode-strings/) | Medium |
| 010 | 238 | [Product of Array Except Self](https://leetcode.com/problems/product-of-array-except-self/) | Medium |
| 011 | 36 | [Valid Sudoku](https://leetcode.com/problems/valid-sudoku/) | Medium |
| 012 | 128 | [Longest Consecutive Sequence](https://leetcode.com/problems/longest-consecutive-sequence/) | Medium |
| 013 | 31 | [Next Permutation](https://leetcode.com/problems/next-permutation/) | Medium |
| 014 | 205 | [Isomorphic Strings](https://leetcode.com/problems/isomorphic-strings/) | Easy |

## 02 · Two Pointers

`PyDSA/02_two_pointers/` · `GoDSA/02_two_pointers/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 125 | [Valid Palindrome](https://leetcode.com/problems/valid-palindrome/) | Easy |
| 002 | 680 | [Valid Palindrome II](https://leetcode.com/problems/valid-palindrome-ii/) | Easy |
| 003 | 26 | [Remove Duplicates from Sorted Array](https://leetcode.com/problems/remove-duplicates-from-sorted-array/) | Easy |
| 004 | 27 | [Remove Element](https://leetcode.com/problems/remove-element/) | Easy |
| 005 | 283 | [Move Zeroes](https://leetcode.com/problems/move-zeroes/) | Easy |
| 006 | 167 | [Two Sum II - Input Array Is Sorted](https://leetcode.com/problems/two-sum-ii-input-array-is-sorted/) | Medium |
| 007 | 15 | [3Sum](https://leetcode.com/problems/3sum/) | Medium |
| 008 | 16 | [3Sum Closest](https://leetcode.com/problems/3sum-closest/) | Medium |
| 009 | 11 | [Container With Most Water](https://leetcode.com/problems/container-with-most-water/) | Medium |
| 010 | 42 | [Trapping Rain Water](https://leetcode.com/problems/trapping-rain-water/) | Hard |
| 011 | 881 | [Boats to Save People](https://leetcode.com/problems/boats-to-save-people/) | Medium |

## 03 · Sliding Window

`PyDSA/03_sliding_window/` · `GoDSA/03_sliding_window/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 121 | [Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/) | Easy |
| 002 | 643 | [Maximum Average Subarray I](https://leetcode.com/problems/maximum-average-subarray-i/) | Easy |
| 003 | 1456 | [Maximum Number of Vowels in a Substring of Given Length](https://leetcode.com/problems/maximum-number-of-vowels-in-a-substring/) | Medium |
| 004 | 219 | [Contains Duplicate II](https://leetcode.com/problems/contains-duplicate-ii/) | Easy |
| 005 | 3 | [Longest Substring Without Repeating Characters](https://leetcode.com/problems/longest-substring-without-repeating-characters/) | Medium |
| 006 | 1004 | [Max Consecutive Ones III](https://leetcode.com/problems/max-consecutive-ones-iii/) | Medium |
| 007 | 424 | [Longest Repeating Character Replacement](https://leetcode.com/problems/longest-repeating-character-replacement/) | Medium |
| 008 | 209 | [Minimum Size Subarray Sum](https://leetcode.com/problems/minimum-size-subarray-sum/) | Medium |
| 009 | 904 | [Fruit Into Baskets](https://leetcode.com/problems/fruit-into-baskets/) | Medium |
| 010 | 567 | [Permutation in String](https://leetcode.com/problems/permutation-in-string/) | Medium |
| 011 | 438 | [Find All Anagrams in a String](https://leetcode.com/problems/find-all-anagrams-in-a-string/) | Medium |
| 012 | 930 | [Binary Subarrays With Sum](https://leetcode.com/problems/binary-subarrays-with-sum/) | Medium |
| 013 | 992 | [Subarrays with K Different Integers](https://leetcode.com/problems/subarrays-with-k-different-integers/) | Hard |
| 014 | 76 | [Minimum Window Substring](https://leetcode.com/problems/minimum-window-substring/) | Hard |
| 015 | 239 | [Sliding Window Maximum](https://leetcode.com/problems/sliding-window-maximum/) | Hard |

## 04 · Prefix Sum

`PyDSA/04_prefix_sum/` · `GoDSA/04_prefix_sum/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 1480 | [Running Sum of 1d Array](https://leetcode.com/problems/running-sum-of-1d-array/) | Easy |
| 002 | 303 | [Range Sum Query - Immutable](https://leetcode.com/problems/range-sum-query-immutable/) | Easy |
| 003 | 724 | [Find Pivot Index](https://leetcode.com/problems/find-pivot-index/) | Easy |
| 004 | 560 | [Subarray Sum Equals K](https://leetcode.com/problems/subarray-sum-equals-k/) | Medium |
| 005 | 525 | [Contiguous Array](https://leetcode.com/problems/contiguous-array/) | Medium |
| 006 | 304 | [Range Sum Query 2D - Immutable](https://leetcode.com/problems/range-sum-query-2d-immutable/) | Medium |
| 007 | 974 | [Subarray Sums Divisible by K](https://leetcode.com/problems/subarray-sums-divisible-by-k/) | Medium |
| 008 | 523 | [Continuous Subarray Sum](https://leetcode.com/problems/continuous-subarray-sum/) | Medium |

## 05 · Binary Search

`PyDSA/05_binary_search/` · `GoDSA/05_binary_search/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 704 | [Binary Search](https://leetcode.com/problems/binary-search/) | Easy |
| 002 | 35 | [Search Insert Position](https://leetcode.com/problems/search-insert-position/) | Easy |
| 003 | 278 | [First Bad Version](https://leetcode.com/problems/first-bad-version/) | Easy |
| 004 | 374 | [Guess Number Higher or Lower](https://leetcode.com/problems/guess-number-higher-or-lower/) | Easy |
| 005 | 74 | [Search a 2D Matrix](https://leetcode.com/problems/search-a-2d-matrix/) | Medium |
| 006 | 875 | [Koko Eating Bananas](https://leetcode.com/problems/koko-eating-bananas/) | Medium |
| 007 | 153 | [Find Minimum in Rotated Sorted Array](https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/) | Medium |
| 008 | 33 | [Search in Rotated Sorted Array](https://leetcode.com/problems/search-in-rotated-sorted-array/) | Medium |
| 009 | 981 | [Time Based Key-Value Store](https://leetcode.com/problems/time-based-key-value-store/) | Medium |
| 010 | 1011 | [Capacity To Ship Packages Within D Days](https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/) | Medium |
| 011 | 410 | [Split Array Largest Sum](https://leetcode.com/problems/split-array-largest-sum/) | Hard |
| 012 | 4 | [Median of Two Sorted Arrays](https://leetcode.com/problems/median-of-two-sorted-arrays/) | Hard |

## 06 · Stack & Monotonic Stack

`PyDSA/06_stack/` · `GoDSA/06_stack/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 20 | [Valid Parentheses](https://leetcode.com/problems/valid-parentheses/) | Easy |
| 002 | 682 | [Baseball Game](https://leetcode.com/problems/baseball-game/) | Easy |
| 003 | 496 | [Next Greater Element I](https://leetcode.com/problems/next-greater-element-i/) | Easy |
| 004 | 155 | [Min Stack](https://leetcode.com/problems/min-stack/) | Medium |
| 005 | 150 | [Evaluate Reverse Polish Notation](https://leetcode.com/problems/evaluate-reverse-polish-notation/) | Medium |
| 006 | 22 | [Generate Parentheses](https://leetcode.com/problems/generate-parentheses/) | Medium |
| 007 | 739 | [Daily Temperatures](https://leetcode.com/problems/daily-temperatures/) | Medium |
| 008 | 853 | [Car Fleet](https://leetcode.com/problems/car-fleet/) | Medium |
| 009 | 901 | [Online Stock Span](https://leetcode.com/problems/online-stock-span/) | Medium |
| 010 | 84 | [Largest Rectangle in Histogram](https://leetcode.com/problems/largest-rectangle-in-histogram/) | Hard |
| 011 | 227 | [Basic Calculator II](https://leetcode.com/problems/basic-calculator-ii/) | Medium |
| 012 | 735 | [Asteroid Collision](https://leetcode.com/problems/asteroid-collision/) | Medium |
| 013 | 402 | [Remove K Digits](https://leetcode.com/problems/remove-k-digits/) | Medium |
| 014 | 907 | [Sum of Subarray Minimums](https://leetcode.com/problems/sum-of-subarray-minimums/) | Medium |

## 07 · Queue & Deque

`PyDSA/07_queue_deque/` · `GoDSA/07_queue_deque/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 232 | [Implement Queue using Stacks](https://leetcode.com/problems/implement-queue-using-stacks/) | Easy |
| 002 | 225 | [Implement Stack using Queues](https://leetcode.com/problems/implement-stack-using-queues/) | Easy |
| 003 | 933 | [Number of Recent Calls](https://leetcode.com/problems/number-of-recent-calls/) | Easy |
| 004 | 622 | [Design Circular Queue](https://leetcode.com/problems/design-circular-queue/) | Medium |
| 005 | 641 | [Design Circular Deque](https://leetcode.com/problems/design-circular-deque/) | Medium |
| 006 | 862 | [Shortest Subarray with Sum at Least K](https://leetcode.com/problems/shortest-subarray-with-sum-at-least-k/) | Hard |

## 08 · Linked List

`PyDSA/08_linked_list/` · `GoDSA/08_linked_list/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 206 | [Reverse Linked List](https://leetcode.com/problems/reverse-linked-list/) | Easy |
| 002 | 21 | [Merge Two Sorted Lists](https://leetcode.com/problems/merge-two-sorted-lists/) | Easy |
| 003 | 141 | [Linked List Cycle](https://leetcode.com/problems/linked-list-cycle/) | Easy |
| 004 | 876 | [Middle of the Linked List](https://leetcode.com/problems/middle-of-the-linked-list/) | Easy |
| 005 | 203 | [Remove Linked List Elements](https://leetcode.com/problems/remove-linked-list-elements/) | Easy |
| 006 | 83 | [Remove Duplicates from Sorted List](https://leetcode.com/problems/remove-duplicates-from-sorted-list/) | Easy |
| 007 | 234 | [Palindrome Linked List](https://leetcode.com/problems/palindrome-linked-list/) | Easy |
| 008 | 143 | [Reorder List](https://leetcode.com/problems/reorder-list/) | Medium |
| 009 | 19 | [Remove Nth Node From End of List](https://leetcode.com/problems/remove-nth-node-from-end-of-list/) | Medium |
| 010 | 138 | [Copy List with Random Pointer](https://leetcode.com/problems/copy-list-with-random-pointer/) | Medium |
| 011 | 2 | [Add Two Numbers](https://leetcode.com/problems/add-two-numbers/) | Medium |
| 012 | 287 | [Find the Duplicate Number](https://leetcode.com/problems/find-the-duplicate-number/) | Medium |
| 013 | 146 | [LRU Cache](https://leetcode.com/problems/lru-cache/) | Medium |
| 014 | 23 | [Merge k Sorted Lists](https://leetcode.com/problems/merge-k-sorted-lists/) | Hard |
| 015 | 25 | [Reverse Nodes in k-Group](https://leetcode.com/problems/reverse-nodes-in-k-group/) | Hard |

## 09 · Recursion & Backtracking

`PyDSA/09_recursion_backtracking/` · `GoDSA/09_recursion_backtracking/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 509 | [Fibonacci Number](https://leetcode.com/problems/fibonacci-number/) | Easy |
| 002 | 78 | [Subsets](https://leetcode.com/problems/subsets/) | Medium |
| 003 | 90 | [Subsets II](https://leetcode.com/problems/subsets-ii/) | Medium |
| 004 | 46 | [Permutations](https://leetcode.com/problems/permutations/) | Medium |
| 005 | 47 | [Permutations II](https://leetcode.com/problems/permutations-ii/) | Medium |
| 006 | 77 | [Combinations](https://leetcode.com/problems/combinations/) | Medium |
| 007 | 39 | [Combination Sum](https://leetcode.com/problems/combination-sum/) | Medium |
| 008 | 40 | [Combination Sum II](https://leetcode.com/problems/combination-sum-ii/) | Medium |
| 009 | 216 | [Combination Sum III](https://leetcode.com/problems/combination-sum-iii/) | Medium |
| 010 | 17 | [Letter Combinations of a Phone Number](https://leetcode.com/problems/letter-combinations-of-a-phone-number/) | Medium |
| 011 | 131 | [Palindrome Partitioning](https://leetcode.com/problems/palindrome-partitioning/) | Medium |
| 012 | 79 | [Word Search](https://leetcode.com/problems/word-search/) | Medium |
| 013 | 51 | [N-Queens](https://leetcode.com/problems/n-queens/) | Hard |
| 014 | 37 | [Sudoku Solver](https://leetcode.com/problems/sudoku-solver/) | Hard |

## 10 · Binary Trees

`PyDSA/10_trees/` · `GoDSA/10_trees/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 144 | [Binary Tree Preorder Traversal](https://leetcode.com/problems/binary-tree-preorder-traversal/) | Easy |
| 002 | 94 | [Binary Tree Inorder Traversal](https://leetcode.com/problems/binary-tree-inorder-traversal/) | Easy |
| 003 | 145 | [Binary Tree Postorder Traversal](https://leetcode.com/problems/binary-tree-postorder-traversal/) | Easy |
| 004 | 226 | [Invert Binary Tree](https://leetcode.com/problems/invert-binary-tree/) | Easy |
| 005 | 104 | [Maximum Depth of Binary Tree](https://leetcode.com/problems/maximum-depth-of-binary-tree/) | Easy |
| 006 | 111 | [Minimum Depth of Binary Tree](https://leetcode.com/problems/minimum-depth-of-binary-tree/) | Easy |
| 007 | 100 | [Same Tree](https://leetcode.com/problems/same-tree/) | Easy |
| 008 | 572 | [Subtree of Another Tree](https://leetcode.com/problems/subtree-of-another-tree/) | Easy |
| 009 | 110 | [Balanced Binary Tree](https://leetcode.com/problems/balanced-binary-tree/) | Easy |
| 010 | 543 | [Diameter of Binary Tree](https://leetcode.com/problems/diameter-of-binary-tree/) | Easy |
| 011 | 112 | [Path Sum](https://leetcode.com/problems/path-sum/) | Easy |
| 012 | 101 | [Symmetric Tree](https://leetcode.com/problems/symmetric-tree/) | Easy |
| 013 | 102 | [Binary Tree Level Order Traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/) | Medium |
| 014 | 199 | [Binary Tree Right Side View](https://leetcode.com/problems/binary-tree-right-side-view/) | Medium |
| 015 | 1448 | [Count Good Nodes in Binary Tree](https://leetcode.com/problems/count-good-nodes-in-binary-tree/) | Medium |
| 016 | 105 | [Construct Binary Tree from Preorder and Inorder Traversal](https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/) | Medium |
| 017 | 236 | [Lowest Common Ancestor of a Binary Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/) | Medium |
| 018 | 124 | [Binary Tree Maximum Path Sum](https://leetcode.com/problems/binary-tree-maximum-path-sum/) | Hard |
| 019 | 297 | [Serialize and Deserialize Binary Tree](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/) | Hard |
| 020 | 863 | [All Nodes Distance K in Binary Tree](https://leetcode.com/problems/all-nodes-distance-k-in-binary-tree/) | Medium |

## 11 · Binary Search Tree

`PyDSA/11_binary_search_tree/` · `GoDSA/11_binary_search_tree/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 700 | [Search in a Binary Search Tree](https://leetcode.com/problems/search-in-a-binary-search-tree/) | Easy |
| 002 | 108 | [Convert Sorted Array to Binary Search Tree](https://leetcode.com/problems/convert-sorted-array-to-binary-search-tree/) | Easy |
| 003 | 701 | [Insert into a Binary Search Tree](https://leetcode.com/problems/insert-into-a-binary-search-tree/) | Medium |
| 004 | 450 | [Delete Node in a BST](https://leetcode.com/problems/delete-node-in-a-bst/) | Medium |
| 005 | 235 | [Lowest Common Ancestor of a Binary Search Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/) | Medium |
| 006 | 98 | [Validate Binary Search Tree](https://leetcode.com/problems/validate-binary-search-tree/) | Medium |
| 007 | 230 | [Kth Smallest Element in a BST](https://leetcode.com/problems/kth-smallest-element-in-a-bst/) | Medium |
| 008 | 173 | [Binary Search Tree Iterator](https://leetcode.com/problems/binary-search-tree-iterator/) | Medium |
| 009 | 99 | [Recover Binary Search Tree](https://leetcode.com/problems/recover-binary-search-tree/) | Hard |
| 010 | 285 | [Inorder Successor in BST](https://leetcode.com/problems/inorder-successor-in-bst/) | Medium |
| 011 | 530 | [Minimum Absolute Difference in BST](https://leetcode.com/problems/minimum-absolute-difference-in-bst/) | Easy |

## 12 · Heap / Priority Queue

`PyDSA/12_heap_priority_queue/` · `GoDSA/12_heap_priority_queue/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 703 | [Kth Largest Element in a Stream](https://leetcode.com/problems/kth-largest-element-in-a-stream/) | Easy |
| 002 | 1046 | [Last Stone Weight](https://leetcode.com/problems/last-stone-weight/) | Easy |
| 003 | 973 | [K Closest Points to Origin](https://leetcode.com/problems/k-closest-points-to-origin/) | Medium |
| 004 | 215 | [Kth Largest Element in an Array](https://leetcode.com/problems/kth-largest-element-in-an-array/) | Medium |
| 005 | 621 | [Task Scheduler](https://leetcode.com/problems/task-scheduler/) | Medium |
| 006 | 355 | [Design Twitter](https://leetcode.com/problems/design-twitter/) | Medium |
| 007 | 767 | [Reorganize String](https://leetcode.com/problems/reorganize-string/) | Medium |
| 008 | 1834 | [Single-Threaded CPU](https://leetcode.com/problems/single-threaded-cpu/) | Medium |
| 009 | 295 | [Find Median from Data Stream](https://leetcode.com/problems/find-median-from-data-stream/) | Hard |
| 010 | 1851 | [Minimum Interval to Include Each Query](https://leetcode.com/problems/minimum-interval-to-include-each-query/) | Hard |
| 011 | 502 | [IPO](https://leetcode.com/problems/ipo/) | Hard |
| 012 | 480 | [Sliding Window Median](https://leetcode.com/problems/sliding-window-median/) | Hard |

## 13 · Trie (Prefix Tree)

`PyDSA/13_trie/` · `GoDSA/13_trie/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 208 | [Implement Trie (Prefix Tree)](https://leetcode.com/problems/implement-trie-prefix-tree/) | Medium |
| 002 | 211 | [Design Add and Search Words Data Structure](https://leetcode.com/problems/design-add-and-search-words-data-structure/) | Medium |
| 003 | 648 | [Replace Words](https://leetcode.com/problems/replace-words/) | Medium |
| 004 | 677 | [Map Sum Pairs](https://leetcode.com/problems/map-sum-pairs/) | Medium |
| 005 | 421 | [Maximum XOR of Two Numbers in an Array](https://leetcode.com/problems/maximum-xor-of-two-numbers-in-an-array/) | Medium |
| 006 | 212 | [Word Search II](https://leetcode.com/problems/word-search-ii/) | Hard |
| 007 | 1268 | [Search Suggestions System](https://leetcode.com/problems/search-suggestions-system/) | Medium |

## 14 · Graphs

`PyDSA/14_graphs/` · `GoDSA/14_graphs/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 733 | [Flood Fill](https://leetcode.com/problems/flood-fill/) | Easy |
| 002 | 200 | [Number of Islands](https://leetcode.com/problems/number-of-islands/) | Medium |
| 003 | 695 | [Max Area of Island](https://leetcode.com/problems/max-area-of-island/) | Medium |
| 004 | 133 | [Clone Graph](https://leetcode.com/problems/clone-graph/) | Medium |
| 005 | 286 | [Walls and Gates](https://leetcode.com/problems/walls-and-gates/) | Medium |
| 006 | 994 | [Rotting Oranges](https://leetcode.com/problems/rotting-oranges/) | Medium |
| 007 | 417 | [Pacific Atlantic Water Flow](https://leetcode.com/problems/pacific-atlantic-water-flow/) | Medium |
| 008 | 130 | [Surrounded Regions](https://leetcode.com/problems/surrounded-regions/) | Medium |
| 009 | 323 | [Number of Connected Components in an Undirected Graph](https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph/) | Medium |
| 010 | 261 | [Graph Valid Tree](https://leetcode.com/problems/graph-valid-tree/) | Medium |
| 011 | 207 | [Course Schedule](https://leetcode.com/problems/course-schedule/) | Medium |
| 012 | 210 | [Course Schedule II](https://leetcode.com/problems/course-schedule-ii/) | Medium |
| 013 | 684 | [Redundant Connection](https://leetcode.com/problems/redundant-connection/) | Medium |
| 014 | 542 | [01 Matrix](https://leetcode.com/problems/01-matrix/) | Medium |
| 015 | 1091 | [Shortest Path in Binary Matrix](https://leetcode.com/problems/shortest-path-in-binary-matrix/) | Medium |
| 016 | 127 | [Word Ladder](https://leetcode.com/problems/word-ladder/) | Hard |
| 017 | 785 | [Is Graph Bipartite?](https://leetcode.com/problems/is-graph-bipartite/) | Medium |
| 018 | 752 | [Open the Lock](https://leetcode.com/problems/open-the-lock/) | Medium |

## 15 · Advanced Graphs

`PyDSA/15_advanced_graphs/` · `GoDSA/15_advanced_graphs/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 547 | [Number of Provinces](https://leetcode.com/problems/number-of-provinces/) | Medium |
| 002 | 990 | [Satisfiability of Equality Equations](https://leetcode.com/problems/satisfiability-of-equality-equations/) | Medium |
| 003 | 743 | [Network Delay Time](https://leetcode.com/problems/network-delay-time/) | Medium |
| 004 | 787 | [Cheapest Flights Within K Stops](https://leetcode.com/problems/cheapest-flights-within-k-stops/) | Medium |
| 005 | 1584 | [Min Cost to Connect All Points](https://leetcode.com/problems/min-cost-to-connect-all-points/) | Medium |
| 006 | 1631 | [Path With Minimum Effort](https://leetcode.com/problems/path-with-minimum-effort/) | Medium |
| 007 | 1462 | [Course Schedule IV](https://leetcode.com/problems/course-schedule-iv/) | Medium |
| 008 | 778 | [Swim in Rising Water](https://leetcode.com/problems/swim-in-rising-water/) | Hard |
| 009 | 269 | [Alien Dictionary](https://leetcode.com/problems/alien-dictionary/) | Hard |
| 010 | 332 | [Reconstruct Itinerary](https://leetcode.com/problems/reconstruct-itinerary/) | Hard |
| 011 | 1489 | [Find Critical and Pseudo-Critical Edges in Minimum Spanning Tree](https://leetcode.com/problems/find-critical-and-pseudo-critical-edges-in-minimum-spanning-tree/) | Hard |
| 012 | 1192 | [Critical Connections in a Network](https://leetcode.com/problems/critical-connections-in-a-network/) | Hard |
| 013 | 721 | [Accounts Merge](https://leetcode.com/problems/accounts-merge/) | Medium |
| 014 | 399 | [Evaluate Division](https://leetcode.com/problems/evaluate-division/) | Medium |
| 015 | 1368 | [Minimum Cost to Make at Least One Valid Path in a Grid](https://leetcode.com/problems/minimum-cost-to-make-at-least-one-valid-path-in-a-grid/) | Hard |

## 16 · Dynamic Programming (1D)

`PyDSA/16_dp_1d/` · `GoDSA/16_dp_1d/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 1137 | [N-th Tribonacci Number](https://leetcode.com/problems/n-th-tribonacci-number/) | Easy |
| 002 | 70 | [Climbing Stairs](https://leetcode.com/problems/climbing-stairs/) | Easy |
| 003 | 746 | [Min Cost Climbing Stairs](https://leetcode.com/problems/min-cost-climbing-stairs/) | Easy |
| 004 | 118 | [Pascal's Triangle](https://leetcode.com/problems/pascals-triangle/) | Easy |
| 005 | 198 | [House Robber](https://leetcode.com/problems/house-robber/) | Medium |
| 006 | 213 | [House Robber II](https://leetcode.com/problems/house-robber-ii/) | Medium |
| 007 | 5 | [Longest Palindromic Substring](https://leetcode.com/problems/longest-palindromic-substring/) | Medium |
| 008 | 647 | [Palindromic Substrings](https://leetcode.com/problems/palindromic-substrings/) | Medium |
| 009 | 91 | [Decode Ways](https://leetcode.com/problems/decode-ways/) | Medium |
| 010 | 322 | [Coin Change](https://leetcode.com/problems/coin-change/) | Medium |
| 011 | 152 | [Maximum Product Subarray](https://leetcode.com/problems/maximum-product-subarray/) | Medium |
| 012 | 139 | [Word Break](https://leetcode.com/problems/word-break/) | Medium |
| 013 | 300 | [Longest Increasing Subsequence](https://leetcode.com/problems/longest-increasing-subsequence/) | Medium |
| 014 | 416 | [Partition Equal Subset Sum](https://leetcode.com/problems/partition-equal-subset-sum/) | Medium |
| 015 | 377 | [Combination Sum IV](https://leetcode.com/problems/combination-sum-iv/) | Medium |
| 016 | 279 | [Perfect Squares](https://leetcode.com/problems/perfect-squares/) | Medium |
| 017 | 354 | [Russian Doll Envelopes](https://leetcode.com/problems/russian-doll-envelopes/) | Hard |

## 17 · Dynamic Programming (2D)

`PyDSA/17_dp_2d/` · `GoDSA/17_dp_2d/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 62 | [Unique Paths](https://leetcode.com/problems/unique-paths/) | Medium |
| 002 | 63 | [Unique Paths II](https://leetcode.com/problems/unique-paths-ii/) | Medium |
| 003 | 64 | [Minimum Path Sum](https://leetcode.com/problems/minimum-path-sum/) | Medium |
| 004 | 221 | [Maximal Square](https://leetcode.com/problems/maximal-square/) | Medium |
| 005 | 1143 | [Longest Common Subsequence](https://leetcode.com/problems/longest-common-subsequence/) | Medium |
| 006 | 309 | [Best Time to Buy and Sell Stock with Cooldown](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/) | Medium |
| 007 | 518 | [Coin Change II](https://leetcode.com/problems/coin-change-ii/) | Medium |
| 008 | 494 | [Target Sum](https://leetcode.com/problems/target-sum/) | Medium |
| 009 | 97 | [Interleaving String](https://leetcode.com/problems/interleaving-string/) | Medium |
| 010 | 72 | [Edit Distance](https://leetcode.com/problems/edit-distance/) | Medium |
| 011 | 329 | [Longest Increasing Path in a Matrix](https://leetcode.com/problems/longest-increasing-path-in-a-matrix/) | Hard |
| 012 | 115 | [Distinct Subsequences](https://leetcode.com/problems/distinct-subsequences/) | Hard |
| 013 | 312 | [Burst Balloons](https://leetcode.com/problems/burst-balloons/) | Hard |
| 014 | 10 | [Regular Expression Matching](https://leetcode.com/problems/regular-expression-matching/) | Hard |
| 015 | 516 | [Longest Palindromic Subsequence](https://leetcode.com/problems/longest-palindromic-subsequence/) | Medium |
| 016 | 847 | [Shortest Path Visiting All Nodes](https://leetcode.com/problems/shortest-path-visiting-all-nodes/) | Hard |
| 017 | 902 | [Numbers At Most N Given Digit Set](https://leetcode.com/problems/numbers-at-most-n-given-digit-set/) | Hard |
| 018 | 2376 | [Count Special Integers](https://leetcode.com/problems/count-special-integers/) | Hard |

## 18 · Greedy

`PyDSA/18_greedy/` · `GoDSA/18_greedy/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 1005 | [Maximize Sum Of Array After K Negations](https://leetcode.com/problems/maximize-sum-of-array-after-k-negations/) | Easy |
| 002 | 53 | [Maximum Subarray](https://leetcode.com/problems/maximum-subarray/) | Medium |
| 003 | 55 | [Jump Game](https://leetcode.com/problems/jump-game/) | Medium |
| 004 | 45 | [Jump Game II](https://leetcode.com/problems/jump-game-ii/) | Medium |
| 005 | 134 | [Gas Station](https://leetcode.com/problems/gas-station/) | Medium |
| 006 | 122 | [Best Time to Buy and Sell Stock II](https://leetcode.com/problems/best-time-to-buy-and-sell-stock-ii/) | Medium |
| 007 | 846 | [Hand of Straights](https://leetcode.com/problems/hand-of-straights/) | Medium |
| 008 | 1899 | [Merge Triplets to Form Target Triplet](https://leetcode.com/problems/merge-triplets-to-form-target-triplet/) | Medium |
| 009 | 763 | [Partition Labels](https://leetcode.com/problems/partition-labels/) | Medium |
| 010 | 678 | [Valid Parenthesis String](https://leetcode.com/problems/valid-parenthesis-string/) | Medium |

## 19 · Intervals

`PyDSA/19_intervals/` · `GoDSA/19_intervals/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 252 | [Meeting Rooms](https://leetcode.com/problems/meeting-rooms/) | Easy |
| 002 | 56 | [Merge Intervals](https://leetcode.com/problems/merge-intervals/) | Medium |
| 003 | 57 | [Insert Interval](https://leetcode.com/problems/insert-interval/) | Medium |
| 004 | 435 | [Non-overlapping Intervals](https://leetcode.com/problems/non-overlapping-intervals/) | Medium |
| 005 | 253 | [Meeting Rooms II](https://leetcode.com/problems/meeting-rooms-ii/) | Medium |
| 006 | 986 | [Interval List Intersections](https://leetcode.com/problems/interval-list-intersections/) | Medium |
| 007 | 452 | [Minimum Number of Arrows to Burst Balloons](https://leetcode.com/problems/minimum-number-of-arrows-to-burst-balloons/) | Medium |
| 008 | 759 | [Employee Free Time](https://leetcode.com/problems/employee-free-time/) | Hard |
| 009 | 1094 | [Car Pooling](https://leetcode.com/problems/car-pooling/) | Medium |
| 010 | 729 | [My Calendar I](https://leetcode.com/problems/my-calendar-i/) | Medium |
| 011 | 731 | [My Calendar II](https://leetcode.com/problems/my-calendar-ii/) | Medium |

## 20 · Bit Manipulation

`PyDSA/20_bit_manipulation/` · `GoDSA/20_bit_manipulation/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 136 | [Single Number](https://leetcode.com/problems/single-number/) | Easy |
| 002 | 191 | [Number of 1 Bits](https://leetcode.com/problems/number-of-1-bits/) | Easy |
| 003 | 338 | [Counting Bits](https://leetcode.com/problems/counting-bits/) | Easy |
| 004 | 190 | [Reverse Bits](https://leetcode.com/problems/reverse-bits/) | Easy |
| 005 | 268 | [Missing Number](https://leetcode.com/problems/missing-number/) | Easy |
| 006 | 371 | [Sum of Two Integers](https://leetcode.com/problems/sum-of-two-integers/) | Medium |
| 007 | 7 | [Reverse Integer](https://leetcode.com/problems/reverse-integer/) | Medium |
| 008 | 137 | [Single Number II](https://leetcode.com/problems/single-number-ii/) | Medium |
| 009 | 260 | [Single Number III](https://leetcode.com/problems/single-number-iii/) | Medium |
| 010 | 201 | [Bitwise AND of Numbers Range](https://leetcode.com/problems/bitwise-and-of-numbers-range/) | Medium |

## 21 · Math & Geometry

`PyDSA/21_math_geometry/` · `GoDSA/21_math_geometry/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 9 | [Palindrome Number](https://leetcode.com/problems/palindrome-number/) | Easy |
| 002 | 66 | [Plus One](https://leetcode.com/problems/plus-one/) | Easy |
| 003 | 202 | [Happy Number](https://leetcode.com/problems/happy-number/) | Easy |
| 004 | 50 | [Pow(x, n)](https://leetcode.com/problems/powx-n/) | Medium |
| 005 | 43 | [Multiply Strings](https://leetcode.com/problems/multiply-strings/) | Medium |
| 006 | 12 | [Integer to Roman](https://leetcode.com/problems/integer-to-roman/) | Medium |
| 007 | 172 | [Factorial Trailing Zeroes](https://leetcode.com/problems/factorial-trailing-zeroes/) | Medium |
| 008 | 204 | [Count Primes](https://leetcode.com/problems/count-primes/) | Medium |
| 009 | 2013 | [Detect Squares](https://leetcode.com/problems/detect-squares/) | Medium |
| 010 | 149 | [Max Points on a Line](https://leetcode.com/problems/max-points-on-a-line/) | Hard |

## 22 · Sorting Algorithms

`PyDSA/22_sorting_algorithms/` · `GoDSA/22_sorting_algorithms/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 88 | [Merge Sorted Array](https://leetcode.com/problems/merge-sorted-array/) | Easy |
| 002 | 912 | [Sort an Array](https://leetcode.com/problems/sort-an-array/) | Medium |
| 003 | 75 | [Sort Colors](https://leetcode.com/problems/sort-colors/) | Medium |
| 004 | 148 | [Sort List](https://leetcode.com/problems/sort-list/) | Medium |
| 005 | 179 | [Largest Number](https://leetcode.com/problems/largest-number/) | Medium |
| 006 | 274 | [H-Index](https://leetcode.com/problems/h-index/) | Medium |
| 007 | 164 | [Maximum Gap](https://leetcode.com/problems/maximum-gap/) | Hard |
| 008 | 315 | [Count of Smaller Numbers After Self](https://leetcode.com/problems/count-of-smaller-numbers-after-self/) | Hard |

## 23 · String Algorithms

`PyDSA/23_string_algorithms/` · `GoDSA/23_string_algorithms/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 28 | [Find the Index of the First Occurrence in a String](https://leetcode.com/problems/find-the-index-of-the-first-occurrence-in-a-string/) | Easy |
| 002 | 459 | [Repeated Substring Pattern](https://leetcode.com/problems/repeated-substring-pattern/) | Easy |
| 003 | 8 | [String to Integer (atoi)](https://leetcode.com/problems/string-to-integer-atoi/) | Medium |
| 004 | 187 | [Repeated DNA Sequences](https://leetcode.com/problems/repeated-dna-sequences/) | Medium |
| 005 | 686 | [Repeated String Match](https://leetcode.com/problems/repeated-string-match/) | Medium |
| 006 | 214 | [Shortest Palindrome](https://leetcode.com/problems/shortest-palindrome/) | Hard |
| 007 | 1044 | [Longest Duplicate Substring](https://leetcode.com/problems/longest-duplicate-substring/) | Hard |
| 008 | 336 | [Palindrome Pairs](https://leetcode.com/problems/palindrome-pairs/) | Hard |

## 24 · Matrix

`PyDSA/24_matrix/` · `GoDSA/24_matrix/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 867 | [Transpose Matrix](https://leetcode.com/problems/transpose-matrix/) | Easy |
| 002 | 48 | [Rotate Image](https://leetcode.com/problems/rotate-image/) | Medium |
| 003 | 54 | [Spiral Matrix](https://leetcode.com/problems/spiral-matrix/) | Medium |
| 004 | 59 | [Spiral Matrix II](https://leetcode.com/problems/spiral-matrix-ii/) | Medium |
| 005 | 73 | [Set Matrix Zeroes](https://leetcode.com/problems/set-matrix-zeroes/) | Medium |
| 006 | 240 | [Search a 2D Matrix II](https://leetcode.com/problems/search-a-2d-matrix-ii/) | Medium |
| 007 | 289 | [Game of Life](https://leetcode.com/problems/game-of-life/) | Medium |
| 008 | 498 | [Diagonal Traverse](https://leetcode.com/problems/diagonal-traverse/) | Medium |

## 25 · Design

`PyDSA/25_design/` · `GoDSA/25_design/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 705 | [Design HashSet](https://leetcode.com/problems/design-hashset/) | Easy |
| 002 | 706 | [Design HashMap](https://leetcode.com/problems/design-hashmap/) | Easy |
| 003 | 359 | [Logger Rate Limiter](https://leetcode.com/problems/logger-rate-limiter/) | Easy |
| 004 | 707 | [Design Linked List](https://leetcode.com/problems/design-linked-list/) | Medium |
| 005 | 380 | [Insert Delete GetRandom O(1)](https://leetcode.com/problems/insert-delete-getrandom-o1/) | Medium |
| 006 | 1472 | [Design Browser History](https://leetcode.com/problems/design-browser-history/) | Medium |
| 007 | 353 | [Design Snake Game](https://leetcode.com/problems/design-snake-game/) | Medium |
| 008 | 460 | [LFU Cache](https://leetcode.com/problems/lfu-cache/) | Hard |
| 009 | 588 | [Design In-Memory File System](https://leetcode.com/problems/design-in-memory-file-system/) | Hard |
| 010 | 642 | [Design Search Autocomplete System](https://leetcode.com/problems/design-search-autocomplete-system/) | Hard |
| 011 | 362 | [Design Hit Counter](https://leetcode.com/problems/design-hit-counter/) | Medium |
| 012 | 1146 | [Snapshot Array](https://leetcode.com/problems/snapshot-array/) | Medium |
| 013 | 2034 | [Stock Price Fluctuation](https://leetcode.com/problems/stock-price-fluctuation/) | Medium |

## 26 · Segment Tree & Fenwick Tree

`PyDSA/26_segment_tree_fenwick/` · `GoDSA/26_segment_tree_fenwick/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 307 | [Range Sum Query - Mutable](https://leetcode.com/problems/range-sum-query-mutable/) | Medium |
| 002 | 308 | [Range Sum Query 2D - Mutable](https://leetcode.com/problems/range-sum-query-2d-mutable/) | Hard |
| 003 | 493 | [Reverse Pairs](https://leetcode.com/problems/reverse-pairs/) | Hard |
| 004 | 327 | [Count of Range Sum](https://leetcode.com/problems/count-of-range-sum/) | Hard |
| 005 | 699 | [Falling Squares](https://leetcode.com/problems/falling-squares/) | Hard |
| 006 | 218 | [The Skyline Problem](https://leetcode.com/problems/the-skyline-problem/) | Hard |

## 27 · Classic Algorithms (Randomized, Divide & Conquer, Quickselect)

`PyDSA/27_algorithms/` · `GoDSA/27_algorithms/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 384 | [Shuffle an Array](https://leetcode.com/problems/shuffle-an-array/) | Medium |
| 002 | 398 | [Random Pick Index](https://leetcode.com/problems/random-pick-index/) | Medium |
| 003 | 382 | [Linked List Random Node](https://leetcode.com/problems/linked-list-random-node/) | Medium |
| 004 | 528 | [Random Pick with Weight](https://leetcode.com/problems/random-pick-with-weight/) | Medium |
| 005 | 324 | [Wiggle Sort II](https://leetcode.com/problems/wiggle-sort-ii/) | Medium |
| 006 | 241 | [Different Ways to Add Parentheses](https://leetcode.com/problems/different-ways-to-add-parentheses/) | Medium |
| 007 | 1985 | [Find the Kth Largest Integer in a String](https://leetcode.com/problems/find-the-kth-largest-integer-in-a-string/) | Medium |
| 008 | 710 | [Random Pick with Blacklist](https://leetcode.com/problems/random-pick-with-blacklist/) | Hard |
| 009 | 470 | [Implement Rand10() Using Rand7()](https://leetcode.com/problems/implement-rand10-using-rand7/) | Medium |

## 28 · Recursion Mastery (Progressive Ladder)

`PyDSA/28_recursion_backtracking/` · `GoDSA/28_recursion_backtracking/`

| # | LC | Problem | Difficulty |
|:--:|:--:|---|:--:|
| 001 | 1342 | [Number of Steps to Reduce a Number to Zero](https://leetcode.com/problems/number-of-steps-to-reduce-a-number-to-zero/) | Easy |
| 002 | 344 | [Reverse String](https://leetcode.com/problems/reverse-string/) | Easy |
| 003 | 258 | [Add Digits](https://leetcode.com/problems/add-digits/) | Easy |
| 004 | 231 | [Power of Two](https://leetcode.com/problems/power-of-two/) | Easy |
| 005 | 326 | [Power of Three](https://leetcode.com/problems/power-of-three/) | Easy |
| 006 | 119 | [Pascal's Triangle II](https://leetcode.com/problems/pascals-triangle-ii/) | Easy |
| 007 | 24 | [Swap Nodes in Pairs](https://leetcode.com/problems/swap-nodes-in-pairs/) | Medium |
| 008 | 92 | [Reverse Linked List II](https://leetcode.com/problems/reverse-linked-list-ii/) | Medium |
| 009 | 341 | [Flatten Nested List Iterator](https://leetcode.com/problems/flatten-nested-list-iterator/) | Medium |
| 010 | 445 | [Add Two Numbers II](https://leetcode.com/problems/add-two-numbers-ii/) | Medium |
| 011 | 96 | [Unique Binary Search Trees](https://leetcode.com/problems/unique-binary-search-trees/) | Medium |
| 012 | 95 | [Unique Binary Search Trees II](https://leetcode.com/problems/unique-binary-search-trees-ii/) | Medium |
| 013 | 129 | [Sum Root to Leaf Numbers](https://leetcode.com/problems/sum-root-to-leaf-numbers/) | Medium |
| 014 | 337 | [House Robber III](https://leetcode.com/problems/house-robber-iii/) | Medium |
| 015 | 894 | [All Possible Full Binary Trees](https://leetcode.com/problems/all-possible-full-binary-trees/) | Medium |
| 016 | 372 | [Super Pow](https://leetcode.com/problems/super-pow/) | Medium |
| 017 | 776 | [Split BST](https://leetcode.com/problems/split-bst/) | Medium |
| 018 | 979 | [Distribute Coins in Binary Tree](https://leetcode.com/problems/distribute-coins-in-binary-tree/) | Medium |
| 019 | 1123 | [Lowest Common Ancestor of Deepest Leaves](https://leetcode.com/problems/lowest-common-ancestor-of-deepest-leaves/) | Medium |
| 020 | 1130 | [Minimum Cost Tree From Leaf Values](https://leetcode.com/problems/minimum-cost-tree-from-leaf-values/) | Medium |
| 021 | 1028 | [Recover a Tree From Preorder Traversal](https://leetcode.com/problems/recover-a-tree-from-preorder-traversal/) | Hard |
| 022 | 761 | [Special Binary String](https://leetcode.com/problems/special-binary-string/) | Hard |
| 023 | 87 | [Scramble String](https://leetcode.com/problems/scramble-string/) | Hard |
| 024 | 282 | [Expression Add Operators](https://leetcode.com/problems/expression-add-operators/) | Hard |
| 025 | 968 | [Binary Tree Cameras](https://leetcode.com/problems/binary-tree-cameras/) | Hard |

