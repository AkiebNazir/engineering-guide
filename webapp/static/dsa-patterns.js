/* ============================================================================
   DSA pattern playbooks — one per topic, the layer that turns "I solved this
   problem" into "I can solve the next one like it".

   Each playbook answers the four questions a strong candidate asks in the
   first minute of an interview:
     signals     what in the statement should make me think of this pattern?
     notThis     what looks like it but is not — and what to use instead
     invariant   the one sentence the code keeps true on every iteration
     templates   the skeleton to write from memory (canonical, runnable Python;
                 every one is executed by the webapp's pattern test before a
                 change ships — see CONTEXT.md)
   plus the pitfalls that cost people the problem, and `families`: every
   problem in the topic, grouped by the move it shares with its siblings, so
   the app can say "solved this? these use the same move".

   `neighbours` are the patterns a statement is most often confused with; the
   recognition drill draws its wrong answers from them. `accepts` lists other
   topics that are also a fair answer for this topic's problems.

   Families reference problems by seq within the topic; `also` reaches across
   topics ("<topic>/<seq>").
   ========================================================================= */
'use strict';

const PLAYBOOKS = {
  /* ------------------------------------------------------------------ 01 -- */
  '01_arrays_hashing': {
    name: 'Hash map / set',
    tagline: 'Remember what you have seen, so every later question is an O(1) lookup.',
    signals: [
      '“have I seen this before?” — duplicates, first repeat, membership',
      'count / frequency / “most common” / anagram',
      'find a pair that sums to X in an UNSORTED array',
      'group things that are “the same” under some key',
      'O(n) is required and the brute force is a double loop',
    ],
    notThis: [
      ['The array is sorted and you need a pair', 'Two pointers — same O(n), O(1) space'],
      ['A contiguous subarray must satisfy a condition', 'Sliding window or prefix sums'],
      ['“Count subarrays summing to k”', 'Prefix sums + a hash map of prefix counts'],
    ],
    invariant: 'The map holds exactly the elements to the left of i, keyed by what a future element will ask for.',
    templates: [{
      title: 'Complement lookup (Two Sum)',
      code: String.raw`def two_sum(nums, target):
    seen = {}                          # value -> index, only for indices < i
    for i, x in enumerate(nums):
        need = target - x              # what would complete the answer?
        if need in seen:               # 1. ask BEFORE inserting
            return [seen[need], i]
        seen[x] = i                    # 2. then remember x
    return []`,
    }, {
      title: 'Canonical key grouping (Group Anagrams)',
      code: String.raw`from collections import defaultdict

def group_anagrams(words):
    groups = defaultdict(list)
    for w in words:
        key = [0] * 26                 # the key: letter counts, not the word
        for ch in w:
            key[ord(ch) - ord('a')] += 1
        groups[tuple(key)].append(w)   # lists are unhashable; tuples are not
    return list(groups.values())`,
    }],
    complexity: 'O(n) time · O(n) space (O(1) average per lookup)',
    pitfalls: [
      'Inserting before checking lets an element pair with itself.',
      'Using a list for “seen” — `x in list` is O(n) and rebuilds the brute force.',
      'Hashing a mutable key (a list) — convert to a tuple or a string.',
      'Saying “O(1)” flatly: it is O(1) average, O(n) worst case.',
    ],
    families: [
      { name: 'Membership & frequency', when: 'A set or a Counter answers the question directly.', seqs: ['002', '003', '011', '012', '014'] },
      { name: 'Complement lookup', when: 'Fixing one element forces what its partner must be.', seqs: ['004'], also: ['04_prefix_sum/004', '02_two_pointers/006'] },
      { name: 'Canonical key → group or bucket', when: 'Equal-under-some-rule items must land together.', seqs: ['007', '008'] },
      { name: 'Positional scans & in-place tricks', when: 'The index itself carries information, or one clever pass replaces a map.', seqs: ['001', '005', '006', '009', '010', '013'] },
    ],
    neighbours: ['02_two_pointers', '04_prefix_sum', '03_sliding_window', '22_sorting_algorithms'],
  },

  /* ------------------------------------------------------------------ 02 -- */
  '02_two_pointers': {
    name: 'Two pointers',
    tagline: 'Two indices that only ever move one way turn a pair search into one pass.',
    signals: [
      'the input is SORTED (or sorting it costs nothing you care about)',
      'find a pair / triplet with a target sum',
      'palindrome, reverse, or compare from both ends',
      'modify the array IN PLACE with O(1) extra space',
      'remove / dedupe / partition while keeping order',
    ],
    notThis: [
      ['Unsorted and the original indices are needed', 'Hash map (sorting loses the indices)'],
      ['A contiguous window with a running condition', 'Sliding window (a two-pointer that keeps state between them)'],
      ['Values can be negative and you need subarray sums', 'Prefix sums — moving a pointer is no longer monotone'],
    ],
    invariant: 'Everything outside [lo, hi] has been proved unable to be part of the answer.',
    templates: [{
      title: 'Converging pointers on a sorted array',
      code: String.raw`def two_sum_sorted(nums, target):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        s = nums[lo] + nums[hi]
        if s == target:
            return [lo, hi]
        if s < target:
            lo += 1                    # need bigger: only moving lo can help
        else:
            hi -= 1                    # need smaller: only moving hi can help
    return []`,
    }, {
      title: 'Read / write pointers (in-place filter)',
      code: String.raw`def remove_duplicates(nums):
    write = 1                          # nums[:write] is the kept prefix
    for read in range(1, len(nums)):
        if nums[read] != nums[write - 1]:
            nums[write] = nums[read]
            write += 1
    return write`,
    }],
    complexity: 'O(n) time (O(n log n) if you sort first) · O(1) space',
    pitfalls: [
      'Forgetting to skip duplicates in 3Sum — the output repeats triplets.',
      '`lo <= hi` where `lo < hi` is required, pairing an element with itself.',
      'Moving the wrong pointer: always argue which move can still improve the answer.',
    ],
    families: [
      { name: 'Converging from both ends', when: 'Compare or combine the two extremes, then discard one.', seqs: ['001', '002', '009', '010'] },
      { name: 'Sort, anchor, converge', when: 'Pairs or triplets hitting a target after sorting.', seqs: ['006', '007', '008', '011'], also: ['01_arrays_hashing/004'] },
      { name: 'Read / write (fast & slow)', when: 'Filter or compact the array in place, keeping order.', seqs: ['003', '004', '005'] },
    ],
    neighbours: ['03_sliding_window', '01_arrays_hashing', '05_binary_search', '18_greedy'],
  },

  /* ------------------------------------------------------------------ 03 -- */
  '03_sliding_window': {
    name: 'Sliding window',
    tagline: 'Grow the right edge, shrink the left: each element enters once and leaves once.',
    signals: [
      'CONTIGUOUS subarray or substring',
      'longest / shortest / maximum sum / count of windows',
      '“at most k” distinct, zeros, replacements …',
      'a fixed window size k is given',
      'anagram / permutation of a pattern inside a longer string',
    ],
    notThis: [
      ['Subarray sums with NEGATIVE numbers', 'Prefix sums + hash map — shrinking is no longer safe'],
      ['Subsequence (not contiguous)', 'DP or greedy'],
      ['Exactly k of something', 'Window for at-most(k) − at-most(k−1)'],
    ],
    invariant: 'After the shrink loop, window [left, right] is the best valid window that ends at right.',
    templates: [{
      title: 'Variable window: longest valid',
      code: String.raw`def longest_at_most_k_distinct(s, k):
    count = {}
    left = best = 0
    for right, ch in enumerate(s):
        count[ch] = count.get(ch, 0) + 1       # 1. enter: add s[right]
        while len(count) > k:                  # 2. restore: shrink while INVALID
            out = s[left]
            count[out] -= 1
            if count[out] == 0:
                del count[out]
            left += 1
        best = max(best, right - left + 1)     # 3. record: the window is valid here
    return best`,
    }, {
      title: 'Fixed window of size k',
      code: String.raw`def max_sum_fixed(nums, k):
    window = sum(nums[:k])                     # prime the first window once
    best = window
    for right in range(k, len(nums)):
        window += nums[right] - nums[right - k]    # one in, one out: O(1)
        best = max(best, window)
    return best`,
    }],
    complexity: 'O(n) time — the inner while is amortised · O(k) or O(Σ) space',
    pitfalls: [
      '`right - left` instead of `right - left + 1`.',
      'Calling `sum()` or slicing inside the loop — a hidden O(n·k).',
      'Shortest-window shape: record INSIDE the `while valid` loop, initialise best to ∞.',
      'Not deleting a count that reaches 0, so `len(count)` never shrinks.',
    ],
    families: [
      { name: 'Fixed-size window', when: 'k is given; slide one in, one out.', seqs: ['002', '003', '004', '010', '011'] },
      { name: 'Longest valid window', when: 'Shrink only while the window is invalid; record after.', seqs: ['001', '005', '006', '007', '009'] },
      { name: 'Shortest valid window', when: 'Shrink while still valid; record inside the loop.', seqs: ['008', '014'] },
      { name: 'Count windows (exactly k)', when: 'count += right − left + 1, and exactly = atMost(k) − atMost(k−1).', seqs: ['012', '013'] },
      { name: 'Monotonic deque', when: 'The window needs its max or min on every step.', seqs: ['015'], also: ['07_queue_deque/006'] },
    ],
    neighbours: ['02_two_pointers', '04_prefix_sum', '01_arrays_hashing', '07_queue_deque'],
  },

  /* ------------------------------------------------------------------ 04 -- */
  '04_prefix_sum': {
    name: 'Prefix sums',
    tagline: 'Pay O(n) once so any range sum is one subtraction: P[j+1] − P[i].',
    signals: [
      'many range-sum queries on an array that does not change',
      '“number of subarrays whose sum is k / divisible by k”',
      'negative numbers in a subarray-sum problem',
      'balance problems: equal 0s and 1s, pivot index',
      '2D region sums in a matrix',
    ],
    notThis: [
      ['All numbers non-negative and you want longest/shortest', 'Sliding window — O(1) space'],
      ['The array is updated between queries', 'Fenwick tree / segment tree'],
      ['Just a single pass total', 'A running variable, no array needed'],
    ],
    invariant: 'P[i] = sum(nums[:i]), so sum(nums[i..j]) = P[j+1] − P[i]; a subarray is a pair of prefixes.',
    templates: [{
      title: 'Prefix + count map (subarrays summing to k)',
      code: String.raw`def subarray_sum_equals_k(nums, k):
    count = {0: 1}                         # the empty prefix, seen once
    prefix = answer = 0
    for x in nums:
        prefix += x
        answer += count.get(prefix - k, 0) # earlier prefixes P with prefix - P == k
        count[prefix] = count.get(prefix, 0) + 1
    return answer`,
    }, {
      title: 'Prefix array for range queries',
      code: String.raw`class RangeSum:
    def __init__(self, nums):
        self.P = [0]                       # length n + 1: P[i] = sum(nums[:i])
        for x in nums:
            self.P.append(self.P[-1] + x)

    def query(self, i, j):                 # sum(nums[i..j]), inclusive
        return self.P[j + 1] - self.P[i]`,
    }],
    complexity: 'O(n) build · O(1) per query · O(n) space',
    pitfalls: [
      'Forgetting `{0: 1}` — subarrays that start at index 0 are never counted.',
      'Updating the map before querying it (a subarray of length 0 gets counted).',
      'Longest-subarray variants store the FIRST index of each prefix, never overwrite.',
      'Python’s % is never negative; in Go/Java normalise `((p % k) + k) % k`.',
    ],
    families: [
      { name: 'Prefix array for range queries', when: 'Static array, many sum queries (1D or 2D).', seqs: ['001', '002', '003', '006'], also: ['26_segment_tree_fenwick/001'] },
      { name: 'Prefix + count map', when: 'Count subarrays with a sum / remainder property.', seqs: ['004', '007'], also: ['01_arrays_hashing/004'] },
      { name: 'Prefix + first-index map', when: 'Longest subarray with a sum / balance property.', seqs: ['005', '008'] },
    ],
    neighbours: ['03_sliding_window', '01_arrays_hashing', '26_segment_tree_fenwick', '02_two_pointers'],
  },

  /* ------------------------------------------------------------------ 05 -- */
  '05_binary_search': {
    name: 'Binary search',
    tagline: 'Find the boundary where a monotone yes/no flips — in the array or in the answer space.',
    signals: [
      'SORTED input and a target / boundary to find',
      'O(log n) is required',
      '“minimum k such that …” / “maximum x that still works”',
      'minimise the maximum (or maximise the minimum)',
      'a rotated sorted array, or a “peak”',
    ],
    notThis: [
      ['Sorted, but you need a pair', 'Two pointers'],
      ['The feasibility check is not monotone', 'It is not binary-searchable — rethink'],
      ['Many inserts and ordered queries', 'A balanced BST / SortedList / heap'],
    ],
    invariant: 'The answer is always inside [lo, hi): everything left of lo is “no”, everything from hi on is “yes”.',
    templates: [{
      title: 'First index where ok(x) is True',
      code: String.raw`def first_true(lo, hi, ok):
    """Smallest x in [lo, hi] with ok(x) True, where ok is False…False True…True.
    Returns hi + 1 if ok is never True."""
    hi += 1                                   # search the half-open range [lo, hi)
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(mid):
            hi = mid                          # mid might be the answer: keep it
        else:
            lo = mid + 1                      # mid is definitely not: drop it
    return lo`,
    }, {
      title: 'Binary search on the answer (Koko)',
      code: String.raw`def min_eating_speed(piles, h):
    def feasible(k):                          # monotone: once True, stays True
        return sum((p + k - 1) // k for p in piles) <= h
    lo, hi = 1, max(piles)                    # the answer space, not an array
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo`,
    }],
    complexity: 'O(log n) — or O(n · log range) when each probe costs O(n)',
    pitfalls: [
      'Mixing closed `[lo, hi]` and half-open `[lo, hi)` loops — pick one and keep it.',
      '`lo = mid` with `mid = (lo + hi) // 2` loops forever when hi = lo + 1.',
      'Searching the array when the question is about the answer space (Koko, ship capacity).',
      'Wrong bounds on the answer: the max must be feasible, the min must be plausible.',
    ],
    families: [
      { name: 'Search a sorted array', when: 'Exact match or lower bound in sorted data.', seqs: ['001', '002', '005', '009'] },
      { name: 'Search with an oracle', when: 'An API tells you higher/lower or bad/good.', seqs: ['003', '004'] },
      { name: 'Binary search on the answer', when: '“Minimum X such that feasible(X)”.', seqs: ['006', '010', '011'] },
      { name: 'Rotated or partitioned', when: 'One half is always sorted; decide which.', seqs: ['007', '008', '012'] },
    ],
    neighbours: ['02_two_pointers', '11_binary_search_tree', '18_greedy', '12_heap_priority_queue'],
  },

  /* ------------------------------------------------------------------ 06 -- */
  '06_stack': {
    name: 'Stack',
    tagline: 'The most recent unresolved thing is the one that matters next.',
    signals: [
      'matching brackets, tags, or nested structure',
      '“next greater / next smaller / previous smaller element”',
      'how far until a warmer day / how many days since …',
      'evaluate an expression, undo, backspace',
      'largest rectangle / area bounded by bars',
    ],
    notThis: [
      ['Need the max/min of a SLIDING window', 'Monotonic DEQUE (items expire from the front too)'],
      ['First-come first-served processing', 'Queue'],
      ['Need the k-th largest overall', 'Heap'],
    ],
    invariant: 'Monotonic stack: indices whose answer is still unknown, with values sorted from bottom to top.',
    templates: [{
      title: 'Monotonic stack: next greater element',
      code: String.raw`def next_greater(nums):
    ans = [-1] * len(nums)
    stack = []                                # indices still waiting for an answer;
    for i, x in enumerate(nums):              # their values decrease bottom → top
        while stack and nums[stack[-1]] < x:
            ans[stack.pop()] = x              # x is the first greater element for it
        stack.append(i)
    return ans`,
    }, {
      title: 'Matching stack (valid brackets)',
      code: String.raw`def is_valid(s):
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    for ch in s:
        if ch in pairs:                       # a closer must match the latest opener
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:
            stack.append(ch)
    return not stack                          # leftovers are unmatched openers`,
    }],
    complexity: 'O(n) time — every index is pushed and popped at most once · O(n) space',
    pitfalls: [
      'Storing values instead of indices when the answer is a distance or width.',
      'Popping from an empty stack — guard with `stack and …`.',
      'Forgetting the sentinel / final flush (largest rectangle leaves bars on the stack).',
      'Using `<` vs `<=` carelessly — it decides how duplicates are counted.',
    ],
    families: [
      { name: 'Matching, balance & undo', when: 'The latest open item must be closed or undone first.', seqs: ['001', '002', '004', '006', '012', '015'] },
      { name: 'Expression evaluation', when: 'Operands and operators with precedence.', seqs: ['005', '011'] },
      { name: 'Monotonic stack', when: 'Next / previous greater or smaller, spans, areas.', seqs: ['003', '007', '008', '009', '010', '013', '014', '016'], also: ['28_recursion_backtracking/020'] },
    ],
    neighbours: ['07_queue_deque', '02_two_pointers', '09_recursion_backtracking', '12_heap_priority_queue'],
  },

  /* ------------------------------------------------------------------ 07 -- */
  '07_queue_deque': {
    name: 'Queue / deque',
    tagline: 'First in, first out — or a deque when items leave from both ends.',
    signals: [
      'process in arrival order / “recent” requests in a time window',
      'implement one container using another',
      'fixed-capacity circular buffer',
      'window max/min where old items expire',
      'shortest subarray with sum ≥ k (with negatives)',
    ],
    notThis: [
      ['Shortest path in a graph or grid', 'BFS (a queue, but a graph pattern)'],
      ['Always take the largest / smallest next', 'Heap'],
      ['Undo the latest action', 'Stack'],
    ],
    invariant: 'Monotonic deque: indices inside the window whose values could still be the answer, sorted front to back.',
    templates: [{
      title: 'Queue from two stacks (amortised O(1))',
      code: String.raw`class MyQueue:
    def __init__(self):
        self.inbox, self.outbox = [], []

    def push(self, x):
        self.inbox.append(x)

    def peek(self):
        if not self.outbox:                   # refill ONLY when empty
            while self.inbox:
                self.outbox.append(self.inbox.pop())
        return self.outbox[-1]

    def pop(self):
        self.peek()
        return self.outbox.pop()

    def empty(self):
        return not self.inbox and not self.outbox`,
    }, {
      title: 'Monotonic deque: sliding window maximum',
      code: String.raw`from collections import deque

def max_sliding_window(nums, k):
    dq, out = deque(), []                     # indices; values decrease front → back
    for i, x in enumerate(nums):
        while dq and nums[dq[-1]] <= x:       # they can never be a maximum again
            dq.pop()
        dq.append(i)
        if dq[0] <= i - k:                    # the front slid out of the window
            dq.popleft()
        if i >= k - 1:
            out.append(nums[dq[0]])
    return out`,
    }],
    complexity: 'O(1) amortised per operation · O(n) for a full sweep',
    pitfalls: [
      '`list.pop(0)` is O(n) — use `collections.deque`.',
      'Refilling the out-stack on every pop instead of only when empty.',
      'Ring buffer: confusing full and empty — keep an explicit size.',
    ],
    families: [
      { name: 'One container from another', when: 'Queue via stacks, stack via a queue.', seqs: ['001', '002'] },
      { name: 'Ring buffers & time windows', when: 'Fixed capacity, or drop what is too old.', seqs: ['003', '004', '005'] },
      { name: 'Monotonic deque', when: 'Best candidate in a window whose items expire.', seqs: ['006'], also: ['03_sliding_window/015'] },
    ],
    neighbours: ['06_stack', '03_sliding_window', '14_graphs', '12_heap_priority_queue'],
  },

  /* ------------------------------------------------------------------ 08 -- */
  '08_linked_list': {
    name: 'Linked list',
    tagline: 'Rewire pointers carefully; a dummy head and a fast/slow pair solve most of it.',
    signals: [
      'the input is a ListNode head',
      'reverse all or part of the list',
      'cycle, middle, n-th from the end',
      'merge sorted lists / add numbers stored as lists',
      'O(1) extra space with a sequence you cannot index',
    ],
    notThis: [
      ['Array with “find the duplicate” in O(1) space', 'Still Floyd — the array is an implicit list'],
      ['Need O(1) access by key AND recency order', 'Hash map + doubly linked list (LRU)'],
    ],
    invariant: 'Reversal: prev is the reversed prefix, cur is the untouched suffix — never lose a reference to either.',
    templates: [{
      title: 'Reverse in place',
      code: String.raw`def reverse_list(head):
    prev, cur = None, head
    while cur:
        nxt = cur.next                        # 1. save the rest
        cur.next = prev                       # 2. flip one arrow
        prev, cur = cur, nxt                  # 3. step both forward
    return prev`,
    }, {
      title: 'Fast / slow pointers',
      code: String.raw`def middle_node(head):
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
    return slow                               # the second middle for even length

def has_cycle(head):
    slow = fast = head
    while fast and fast.next:
        slow, fast = slow.next, fast.next.next
        if slow is fast:                      # fast gains one step per round
            return True
    return False`,
    }],
    complexity: 'O(n) time · O(1) space',
    pitfalls: [
      'Losing the rest of the list by overwriting `cur.next` before saving it.',
      'Special-casing the head instead of using a dummy node.',
      '`while fast.next` without checking `fast` first — AttributeError on None.',
      'Comparing node VALUES where node IDENTITY (`is`) is meant.',
    ],
    families: [
      { name: 'Reverse & rewire', when: 'Change the direction of some or all links.', seqs: ['001', '015'], also: ['28_recursion_backtracking/008'] },
      { name: 'Fast & slow pointers', when: 'Cycles, middles, a fixed gap from the end.', seqs: ['003', '004', '009', '012'] },
      { name: 'Dummy head builders', when: 'Build or filter a new list without head special cases.', seqs: ['002', '005', '006', '011', '014'] },
      { name: 'Middle + reverse + merge', when: 'Compare or weave the two halves.', seqs: ['007', '008'] },
      { name: 'Node maps & hybrids', when: 'A hash map indexes the nodes.', seqs: ['010', '013'], also: ['25_design/008'] },
    ],
    neighbours: ['02_two_pointers', '25_design', '28_recursion_backtracking', '06_stack'],
  },

  /* ------------------------------------------------------------------ 09 -- */
  '09_recursion_backtracking': {
    name: 'Backtracking',
    tagline: 'Choose, explore, un-choose — a depth-first walk of the decision tree.',
    signals: [
      '“return ALL combinations / permutations / subsets / partitions”',
      'place items under constraints (N-Queens, Sudoku)',
      'find a path of letters in a grid (word search)',
      'n is small (≤ 10–20) — exponential is expected',
    ],
    notThis: [
      ['Only the COUNT or the best value is asked', 'DP — memoise instead of enumerating'],
      ['Shortest number of steps', 'BFS'],
    ],
    invariant: '`path` always equals the choices on the way from the root to the current node of the decision tree.',
    templates: [{
      title: 'Subsets (start index, every node is an answer)',
      code: String.raw`def subsets(nums):
    out, path = [], []
    def backtrack(start):
        out.append(path[:])                   # copy: path keeps changing
        for i in range(start, len(nums)):
            path.append(nums[i])              # choose
            backtrack(i + 1)                  # explore the rest
            path.pop()                        # un-choose
    backtrack(0)
    return out`,
    }, {
      title: 'Permutations (used flags)',
      code: String.raw`def permutations(nums):
    out, path, used = [], [], [False] * len(nums)
    def backtrack():
        if len(path) == len(nums):
            out.append(path[:])
            return
        for i, x in enumerate(nums):
            if used[i]:
                continue
            used[i] = True; path.append(x)    # choose
            backtrack()                       # explore
            used[i] = False; path.pop()       # un-choose
    backtrack()
    return out`,
    }],
    complexity: 'O(2ⁿ · n) subsets · O(n! · n) permutations',
    pitfalls: [
      '`out.append(path)` without a copy — every entry ends up as the same (empty) list.',
      'Duplicates: sort first, then skip `nums[i] == nums[i-1]` when i > start.',
      '`i` vs `i + 1` in the recursive call decides whether an element can be reused.',
      'Forgetting to un-mark a grid cell after exploring it.',
    ],
    families: [
      { name: 'Recursion → memo (the bridge to DP)', when: 'Overlapping subproblems in a plain recursion.', seqs: ['001'] },
      { name: 'Subsets: take or skip', when: 'Every subset, with or without duplicates.', seqs: ['002', '003'] },
      { name: 'Permutations', when: 'Order matters; each element used once.', seqs: ['004', '005'] },
      { name: 'Combinations (start index)', when: 'Choose k / reach a target; order does not matter.', seqs: ['006', '007', '008', '009', '010', '011'] },
      { name: 'Grid & constraint search', when: 'Mark, recurse, unmark — prune early.', seqs: ['012', '013', '014'], also: ['13_trie/006'] },
    ],
    neighbours: ['16_dp_1d', '28_recursion_backtracking', '14_graphs', '10_trees'],
    accepts: ['28_recursion_backtracking'],
  },

  /* ------------------------------------------------------------------ 10 -- */
  '10_trees': {
    name: 'Tree DFS / BFS',
    tagline: 'Decide what each call returns to its parent; the recursion does the rest.',
    signals: [
      'the input is a TreeNode root',
      'depth / height / diameter / balanced',
      'level by level, right side view, zigzag',
      'path sums from root to leaf, or anywhere',
      'lowest common ancestor, serialise, build from traversals',
    ],
    notThis: [
      ['The tree is a BST and order matters', 'BST pattern — use the ordering to prune'],
      ['Edges go upward too (distance k from a node)', 'Treat it as a graph and BFS'],
    ],
    invariant: 'Post-order: each call returns what its PARENT needs; any answer through the node is recorded on the side.',
    templates: [{
      title: 'Post-order: return up, record on the side (Diameter)',
      code: String.raw`def diameter(root):
    best = 0
    def height(node):                         # returns info UP to the parent
        nonlocal best
        if not node:
            return 0
        l, r = height(node.left), height(node.right)
        best = max(best, l + r)               # an answer that passes THROUGH node
        return 1 + max(l, r)                  # what the parent needs
    height(root)
    return best`,
    }, {
      title: 'BFS level by level',
      code: String.raw`from collections import deque

def level_order(root):
    if not root:
        return []
    out, q = [], deque([root])
    while q:
        level = []
        for _ in range(len(q)):               # exactly one level is in the queue
            node = q.popleft()
            level.append(node.val)
            if node.left:
                q.append(node.left)
            if node.right:
                q.append(node.right)
        out.append(level)
    return out`,
    }],
    complexity: 'O(n) time · O(h) recursion stack (O(n) worst case, O(log n) balanced)',
    pitfalls: [
      'Returning the global answer from the helper instead of what the parent needs.',
      'Minimum depth: a node with one child is not a leaf.',
      'Re-reading `len(q)` inside the level loop — children leak into the level.',
      'Recursion depth ~1000 in Python: a 10⁵-node skewed tree needs an iterative walk.',
    ],
    families: [
      { name: 'Traversal orders', when: 'Visit in pre / in / post order, or serialise.', seqs: ['001', '002', '003', '019'] },
      { name: 'Post-order: answer from the children', when: 'Height, balance, diameter, LCA, max path.', seqs: ['004', '005', '006', '009', '010', '017', '018'], also: ['28_recursion_backtracking/014'] },
      { name: 'Pre-order: pass state down', when: 'The answer depends on the path from the root.', seqs: ['011', '015'], also: ['28_recursion_backtracking/013'] },
      { name: 'Two trees at once', when: 'Walk two trees (or mirrored halves) in lockstep.', seqs: ['007', '008', '012'] },
      { name: 'BFS by levels', when: 'Per-level answers, or the tree as a graph.', seqs: ['013', '014', '020'] },
      { name: 'Build from traversals', when: 'Preorder gives roots, inorder splits sides.', seqs: ['016'] },
      { name: 'Binary lifting', when: 'Many "k-th ancestor" or LCA queries on a big tree.', seqs: ['021'] },
    ],
    neighbours: ['11_binary_search_tree', '14_graphs', '28_recursion_backtracking', '09_recursion_backtracking'],
    accepts: ['28_recursion_backtracking'],
  },

  /* ------------------------------------------------------------------ 11 -- */
  '11_binary_search_tree': {
    name: 'BST',
    tagline: 'Left < node < right: every comparison discards a whole subtree, and inorder is sorted.',
    signals: [
      'the tree is a BINARY SEARCH TREE',
      'k-th smallest / successor / closest value',
      'validate, insert, delete in a BST',
      'LCA in a BST',
      'an iterator over a tree in sorted order',
    ],
    notThis: [
      ['A plain binary tree', 'General tree DFS — no pruning is possible'],
      ['Sorted ARRAY', 'Binary search on the array'],
    ],
    invariant: 'Every node lies strictly between the bounds its ancestors imposed — not just its parent.',
    templates: [{
      title: 'Validate with inherited bounds',
      code: String.raw`def is_valid_bst(root, lo=float('-inf'), hi=float('inf')):
    if not root:
        return True
    if not lo < root.val < hi:                # every ancestor constrains this node
        return False
    return (is_valid_bst(root.left, lo, root.val) and
            is_valid_bst(root.right, root.val, hi))`,
    }, {
      title: 'Iterative inorder (sorted order, stoppable)',
      code: String.raw`def kth_smallest(root, k):
    stack, node = [], root
    while stack or node:
        while node:                           # dive left: the smallest comes first
            stack.append(node)
            node = node.left
        node = stack.pop()
        k -= 1
        if k == 0:
            return node.val                   # inorder visits in sorted order
        node = node.right`,
    }],
    complexity: 'O(h) per search / insert / delete · O(n) for a full inorder',
    pitfalls: [
      'Checking only `left.val < node.val < right.val` — a grandchild can still break the order.',
      'Using `<=` when the BST forbids duplicates (or `<` when it allows them).',
      'Delete with two children: replace with the inorder successor, then delete that.',
    ],
    families: [
      { name: 'Compare and discard', when: 'Walk one root-to-leaf path using the ordering.', seqs: ['001', '003', '005', '010'] },
      { name: 'Inorder is sorted', when: 'k-th, iterator, recover, min difference, build.', seqs: ['002', '007', '008', '009', '011'] },
      { name: 'Bounds & structural edits', when: 'Validate with bounds, delete with successor.', seqs: ['004', '006'], also: ['28_recursion_backtracking/017'] },
    ],
    neighbours: ['10_trees', '05_binary_search', '12_heap_priority_queue', '26_segment_tree_fenwick'],
  },

  /* ------------------------------------------------------------------ 12 -- */
  '12_heap_priority_queue': {
    name: 'Heap / priority queue',
    tagline: 'Always know the current best in O(1), and update it in O(log n).',
    signals: [
      '“top k / k largest / k closest / k most frequent”',
      'merge k sorted lists or streams',
      'median of a stream',
      'always process the smallest / largest / earliest available next',
      'scheduling with cooldowns or deadlines',
    ],
    notThis: [
      ['Need everything fully sorted once', 'Just sort'],
      ['Next greater element', 'Monotonic stack'],
      ['Only the k-th element once, fast on average', 'Quickselect (O(n) average)'],
    ],
    invariant: 'A size-k min-heap holds the k largest seen so far; its root is the k-th largest.',
    templates: [{
      title: 'Size-k heap for top-k',
      code: String.raw`import heapq

def kth_largest(nums, k):
    heap = []                                 # min-heap of the k largest so far
    for x in nums:
        heapq.heappush(heap, x)
        if len(heap) > k:
            heapq.heappop(heap)               # evict the smallest of the k + 1
    return heap[0]                            # the k-th largest`,
    }, {
      title: 'Two heaps straddling the median',
      code: String.raw`import heapq

class MedianFinder:
    def __init__(self):
        self.low, self.high = [], []          # max-heap (negated) | min-heap

    def addNum(self, x):
        heapq.heappush(self.low, -x)
        heapq.heappush(self.high, -heapq.heappop(self.low))       # low <= high
        if len(self.high) > len(self.low):
            heapq.heappush(self.low, -heapq.heappop(self.high))   # low holds the extra

    def findMedian(self):
        if len(self.low) > len(self.high):
            return -self.low[0]
        return (-self.low[0] + self.high[0]) / 2`,
    }],
    complexity: 'O(n log k) for top-k · O(log n) per push / pop · O(1) peek',
    pitfalls: [
      'Python’s heapq is a MIN-heap — negate values for a max-heap.',
      'A max-heap of size n for top-k costs O(n log n); a min-heap of size k costs O(n log k).',
      'Pushing tuples whose first fields tie and whose next field is not comparable.',
      'Removing an arbitrary element — use lazy deletion instead of `list.remove`.',
    ],
    families: [
      { name: 'Size-k heap (top-k)', when: 'Keep only the k best seen so far.', seqs: ['001', '003', '004'] },
      { name: 'Greedy: always take the extreme', when: 'Repeatedly process the current largest / smallest.', seqs: ['002', '005', '007', '011'] },
      { name: 'k-way merge', when: 'Merge several sorted sources.', seqs: ['006'], also: ['08_linked_list/014'] },
      { name: 'Sweep + heap of the active set', when: 'Sort by time, heap what is currently available.', seqs: ['008', '010'], also: ['19_intervals/005', '26_segment_tree_fenwick/006'] },
      { name: 'Two heaps', when: 'Median, or a balanced split of a stream.', seqs: ['009', '012'] },
    ],
    neighbours: ['22_sorting_algorithms', '18_greedy', '19_intervals', '05_binary_search'],
  },

  /* ------------------------------------------------------------------ 13 -- */
  '13_trie': {
    name: 'Trie',
    tagline: 'Share prefixes: a lookup costs the length of the word, not the size of the dictionary.',
    signals: [
      'prefix / “starts with” / autocomplete',
      'many words searched against one dictionary',
      'wildcard word search (“.” matches anything)',
      'find many dictionary words in a grid',
      'maximum XOR of two numbers (a trie of bits)',
    ],
    notThis: [
      ['One exact-match lookup', 'A hash set'],
      ['Substring search in one text', 'KMP / rolling hash'],
    ],
    invariant: 'The path from the root to a node spells a prefix; an end marker says whether the prefix is itself a word.',
    templates: [{
      title: 'Dict-of-dicts trie',
      code: String.raw`class Trie:
    def __init__(self):
        self.root = {}

    def insert(self, word):
        node = self.root
        for ch in word:
            node = node.setdefault(ch, {})
        node['$'] = True                      # end-of-word marker

    def _walk(self, s):
        node = self.root
        for ch in s:
            if ch not in node:
                return None
            node = node[ch]
        return node

    def search(self, word):
        node = self._walk(word)
        return node is not None and '$' in node

    def startsWith(self, prefix):
        return self._walk(prefix) is not None`,
    }],
    complexity: 'O(L) per insert / search · O(total characters) space',
    pitfalls: [
      '`search` returning True for a prefix — check the end marker.',
      'Word Search II: prune found words from the trie, or the grid DFS repeats work.',
      'Using a 26-slot array for arbitrary characters.',
    ],
    families: [
      { name: 'Prefix tree basics', when: 'Insert, search, prefix queries, per-node aggregates.', seqs: ['001', '003', '004', '007'], also: ['25_design/010'] },
      { name: 'Trie + DFS', when: 'Wildcards, or walking a grid against a dictionary.', seqs: ['002', '006'] },
      { name: 'Bitwise trie', when: 'Maximise XOR by choosing the opposite bit greedily.', seqs: ['005'] },
    ],
    neighbours: ['01_arrays_hashing', '23_string_algorithms', '25_design', '09_recursion_backtracking'],
  },

  /* ------------------------------------------------------------------ 14 -- */
  '14_graphs': {
    name: 'Graph BFS / DFS',
    tagline: 'Visit each node once: DFS to explore and count, BFS for the fewest steps.',
    signals: [
      'a grid of cells with neighbours (islands, regions, rotting)',
      'fewest moves / minimum steps in an unweighted graph',
      'prerequisites, build order, “can all courses be finished?”',
      'connected components, clone a graph, valid tree',
      'a state space you can move through (locks, word ladder)',
    ],
    notThis: [
      ['Edges have different non-negative weights', 'Dijkstra'],
      ['Repeated “are these connected?” as edges arrive', 'Union-find'],
      ['A tree with parent → child links only', 'Tree DFS'],
    ],
    invariant: 'BFS: when a node is dequeued, its distance is final — so mark visited when you ENQUEUE.',
    templates: [{
      title: 'Grid flood fill (count components)',
      code: String.raw`def num_islands(grid):
    rows, cols = len(grid), len(grid[0])
    def sink(r, c):
        if not (0 <= r < rows and 0 <= c < cols) or grid[r][c] != '1':
            return
        grid[r][c] = '0'                      # mark visited BEFORE recursing
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            sink(r + dr, c + dc)
    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1                    # found a new component
                sink(r, c)
    return count`,
    }, {
      title: 'BFS shortest path (seed several sources for multi-source)',
      code: String.raw`from collections import deque

def shortest_steps(grid, start, goal):
    rows, cols = len(grid), len(grid[0])
    q, dist = deque([start]), {start: 0}
    while q:
        r, c = q.popleft()
        if (r, c) == goal:
            return dist[(r, c)]               # first time dequeued = shortest
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 0 \
                    and (nr, nc) not in dist:
                dist[(nr, nc)] = dist[(r, c)] + 1   # mark when ENQUEUED
                q.append((nr, nc))
    return -1`,
    }, {
      title: 'Topological sort (Kahn)',
      code: String.raw`from collections import deque

def topo_order(n, edges):                     # edge (a, b): a must come before b
    graph = [[] for _ in range(n)]
    indeg = [0] * n
    for a, b in edges:
        graph[a].append(b)
        indeg[b] += 1
    q = deque(i for i in range(n) if indeg[i] == 0)
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in graph[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
    return order if len(order) == n else []   # shorter means a cycle`,
    }],
    complexity: 'O(V + E) — O(rows · cols) on a grid',
    pitfalls: [
      'Marking visited when popping instead of when pushing — nodes get queued many times.',
      'Recursive DFS on a 10⁵-cell grid overflows Python’s stack; use BFS or an explicit stack.',
      'Directed cycle detection needs three colours (or Kahn), not a single visited set.',
      'Forgetting disconnected parts: loop over every node as a potential start.',
    ],
    families: [
      { name: 'Grid flood fill', when: 'Count, size or recolour connected regions.', seqs: ['001', '002', '003', '007', '008'] },
      { name: 'BFS shortest path', when: 'Fewest steps; seed all sources at once for multi-source.', seqs: ['005', '006', '014', '015', '016', '018', '019'] },
      { name: 'Components & cycles (undirected)', when: 'Clone, count components, tree check, bipartite.', seqs: ['004', '009', '010', '013', '017'], also: ['15_advanced_graphs/001'] },
      { name: 'Topological sort', when: 'Dependencies in a directed graph.', seqs: ['011', '012'], also: ['15_advanced_graphs/009'] },
    ],
    neighbours: ['15_advanced_graphs', '10_trees', '09_recursion_backtracking', '24_matrix'],
  },

  /* ------------------------------------------------------------------ 15 -- */
  '15_advanced_graphs': {
    name: 'Advanced graphs',
    tagline: 'Weighted paths, spanning trees and dynamic connectivity — each has one standard tool.',
    signals: [
      'weighted edges and a cheapest / fastest path (Dijkstra)',
      '“at most k stops” (Bellman-Ford rounds)',
      'connect everything at minimum cost (MST)',
      'group items as “same” relations arrive (union-find)',
      'use every edge exactly once (Eulerian path); critical edges (bridges)',
    ],
    notThis: [
      ['All edges have the same weight', 'Plain BFS'],
      ['Negative edges without a hop limit', 'Bellman-Ford (Dijkstra breaks)'],
      ['Weights are only 0 or 1', '0-1 BFS with a deque'],
    ],
    invariant: 'Dijkstra: the first time a node is popped from the heap, its distance is final.',
    templates: [{
      title: 'Union-find (path halving + union by size)',
      code: String.raw`class DSU:
    def __init__(self, n):
        self.parent = list(range(n))
        self.size = [1] * n

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]   # path halving
            x = self.parent[x]
        return x

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False                      # already connected: this edge closes a cycle
        if self.size[ra] < self.size[rb]:
            ra, rb = rb, ra
        self.parent[rb] = ra                  # attach the smaller tree under the larger
        self.size[ra] += self.size[rb]
        return True`,
    }, {
      title: 'Dijkstra with a lazy heap',
      code: String.raw`import heapq

def dijkstra(n, edges, src):                  # edges: (u, v, w) with w >= 0
    graph = [[] for _ in range(n)]
    for u, v, w in edges:
        graph[u].append((v, w))
    dist = [float('inf')] * n
    dist[src] = 0
    heap = [(0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue                          # stale entry: u was settled cheaper
        for v, w in graph[u]:
            if d + w < dist[v]:
                dist[v] = d + w
                heapq.heappush(heap, (dist[v], v))
    return dist`,
    }],
    complexity: 'Dijkstra O(E log V) · union-find ≈ O(α(n)) per op · MST O(E log E)',
    pitfalls: [
      'Dijkstra without the stale-entry check does redundant work (still correct, slower).',
      'Bellman-Ford with k stops: relax from a SNAPSHOT of last round’s distances.',
      'Union-find without path compression or union by size degrades to O(n) per find.',
    ],
    families: [
      { name: 'Union-find', when: 'Connectivity as relations arrive; weighted variants for ratios.', seqs: ['001', '002', '013', '014'], also: ['14_graphs/013'] },
      { name: 'Shortest paths', when: 'Dijkstra, minimax Dijkstra, Bellman-Ford rounds, 0-1 BFS.', seqs: ['003', '004', '006', '008', '015'] },
      { name: 'Minimum spanning tree', when: 'Connect all nodes at minimum total cost.', seqs: ['005', '011'] },
      { name: 'Order & reachability', when: 'Topological order from data, transitive closure.', seqs: ['007', '009'] },
      { name: 'Edge-centric traversals', when: 'Eulerian paths (Hierholzer), bridges (Tarjan).', seqs: ['010', '012'] },
    ],
    neighbours: ['14_graphs', '12_heap_priority_queue', '17_dp_2d', '18_greedy'],
  },

  /* ------------------------------------------------------------------ 16 -- */
  '16_dp_1d': {
    name: '1D dynamic programming',
    tagline: 'Define dp[i] in words, write how it depends on smaller i, then roll it into O(1) space.',
    signals: [
      '“number of ways” / “minimum cost” / “maximum value” / “can you reach”',
      'choices at each step that affect later steps (take or skip)',
      'the brute-force recursion recomputes the same subproblems',
      'coins, stairs, houses, decodings, word break',
    ],
    notThis: [
      ['List every solution, not count them', 'Backtracking'],
      ['A locally best choice is provably safe', 'Greedy (simpler, O(1) space)'],
      ['Two sequences or a grid', '2D DP'],
    ],
    invariant: 'dp[i] is final once computed — it depends only on dp values for smaller indices.',
    templates: [{
      title: 'Take or skip with two rolling values (House Robber)',
      code: String.raw`def rob(nums):
    prev2 = prev1 = 0                         # dp[i-2], dp[i-1]
    for x in nums:
        prev2, prev1 = prev1, max(prev1, prev2 + x)   # skip i, or take i
    return prev1`,
    }, {
      title: 'Unbounded knapsack (Coin Change)',
      code: String.raw`def coin_change(coins, amount):
    INF = float('inf')
    dp = [0] + [INF] * amount                 # dp[a] = fewest coins that make a
    for a in range(1, amount + 1):
        for c in coins:
            if c <= a and dp[a - c] + 1 < dp[a]:
                dp[a] = dp[a - c] + 1
    return dp[amount] if dp[amount] != INF else -1`,
    }],
    complexity: 'O(n · choices) time · O(n), often O(1) with rolling variables',
    pitfalls: [
      'Not writing down what dp[i] MEANS before coding the recurrence.',
      'Wrong base case (dp[0] = 1 for counting ways, 0 for cost).',
      '0/1 knapsack in 1D must loop capacity DOWNWARD, unbounded loops it upward.',
      'Counting combinations vs permutations: which loop is outside decides it.',
    ],
    families: [
      { name: 'Linear recurrence', when: 'dp[i] from a fixed window of earlier values.', seqs: ['001', '002', '003', '004'] },
      { name: 'Take or skip', when: 'Each element is used or not; rolling states.', seqs: ['005', '006', '011'], also: ['28_recursion_backtracking/014'] },
      { name: 'Segment a prefix', when: 'Ways to split / decode the first i characters.', seqs: ['009', '012'] },
      { name: 'Knapsack in 1D', when: 'Reach a target sum with items (bounded or not).', seqs: ['010', '014', '015', '016'], also: ['17_dp_2d/007'] },
      { name: 'Palindromes by expansion', when: 'Expand around every centre.', seqs: ['007', '008'] },
      { name: 'Longest increasing subsequence', when: 'dp over “ending at i”, or patience sorting.', seqs: ['013', '017'] },
    ],
    neighbours: ['17_dp_2d', '18_greedy', '09_recursion_backtracking', '28_recursion_backtracking'],
  },

  /* ------------------------------------------------------------------ 17 -- */
  '17_dp_2d': {
    name: '2D dynamic programming',
    tagline: 'Two indices of state: positions in two strings, a grid cell, an interval, or an item and a capacity.',
    signals: [
      'TWO strings: common subsequence, edit distance, interleaving, matching',
      'paths in a grid moving right / down',
      'an interval [i, j] where the last choice splits it',
      'knapsack with an item index and a remaining capacity',
      'small n (≤ 20) with a subset state → bitmask DP',
      'two players alternate and both play optimally → minimax over [i, j]',
    ],
    notThis: [
      ['One sequence, one index of state', '1D DP'],
      ['Shortest path with arbitrary moves', 'BFS / Dijkstra'],
    ],
    invariant: 'dp[i][j] answers the question for prefixes a[:i] and b[:j]; row 0 and column 0 are the empty cases.',
    templates: [{
      title: 'Two strings (Longest Common Subsequence)',
      code: String.raw`def lcs(a, b):
    m, n = len(a), len(b)
    dp = [[0] * (n + 1) for _ in range(m + 1)]   # dp[i][j]: a[:i] vs b[:j]
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1  # both characters used
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])   # drop one of them
    return dp[m][n]`,
    }, {
      title: 'Grid paths with one rolling row',
      code: String.raw`def unique_paths(m, n):
    row = [1] * n                             # the first row: one way to each cell
    for _ in range(1, m):
        for j in range(1, n):
            row[j] += row[j - 1]              # from above (old row[j]) + from the left
    return row[-1]`,
    }],
    complexity: 'O(m · n) time · O(m · n), or O(n) with a rolling row',
    pitfalls: [
      'Off-by-one between string indices and dp indices (dp is one larger).',
      'Rolling to one row overwrites a value you still need (keep `prev` for the diagonal).',
      'Interval DP must fill by increasing interval LENGTH, not by i then j.',
    ],
    families: [
      { name: 'Grid paths', when: 'Count or optimise paths in a grid.', seqs: ['001', '002', '003', '004', '011'] },
      { name: 'Two strings', when: 'Align, match or transform one string into another.', seqs: ['005', '009', '010', '012', '014'] },
      { name: 'Knapsack in 2D', when: 'Item index × remaining target (or two capacities).', seqs: ['007', '008', '021'], also: ['16_dp_1d/014'] },
      { name: 'State machine', when: 'A small set of states per day or step.', seqs: ['006', '020'] },
      { name: 'Game minimax', when: 'Two players alternate optimally; track the mover\'s score difference.', seqs: ['019'] },
      { name: 'Interval DP', when: 'Pick the last split of [i, j].', seqs: ['013', '015'], also: ['28_recursion_backtracking/020'] },
      { name: 'Bitmask & digit DP', when: 'A subset or a digit position is part of the state.', seqs: ['016', '017', '018', '022'] },
    ],
    neighbours: ['16_dp_1d', '23_string_algorithms', '14_graphs', '09_recursion_backtracking'],
  },

  /* ------------------------------------------------------------------ 18 -- */
  '18_greedy': {
    name: 'Greedy',
    tagline: 'Commit to the locally best choice — after you can argue why it is never worse.',
    signals: [
      'maximum subarray / best single transaction (Kadane)',
      'can you reach the end / minimum jumps',
      'gas station, partition labels, hand of straights',
      'an exchange argument works: swapping into the greedy choice never hurts',
    ],
    notThis: [
      ['A counter-example beats the greedy choice', 'DP'],
      ['Intervals to schedule', 'Intervals pattern (greedy by end time)'],
    ],
    invariant: 'The greedy state after i (best so far, furthest reach) summarises everything the future needs.',
    templates: [{
      title: 'Running best with a reset (Kadane)',
      code: String.raw`def max_subarray(nums):
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)                 # extend the run, or restart at x
        best = max(best, cur)
    return best`,
    }, {
      title: 'Furthest reach (Jump Game)',
      code: String.raw`def can_jump(nums):
    reach = 0
    for i, step in enumerate(nums):
        if i > reach:
            return False                      # i is beyond everything reachable
        reach = max(reach, i + step)
    return True`,
    }],
    complexity: 'O(n), or O(n log n) with a sort first · O(1) space',
    pitfalls: [
      'Using greedy without a proof — test a small counter-example first.',
      'Kadane seeded with 0 fails on all-negative arrays.',
      'Gas station: the start is the index after the last point where the tank went negative.',
    ],
    families: [
      { name: 'Running best with a reset', when: 'Kadane, sum every rise, restart after a deficit.', seqs: ['002', '005', '006'], also: ['03_sliding_window/001'] },
      { name: 'Furthest reach', when: 'Track the frontier you can reach.', seqs: ['003', '004'] },
      { name: 'Sort, then greedy scan', when: 'Sorting makes the local choice safe.', seqs: ['001', '007', '008'] },
      { name: 'Ranges & last occurrences', when: 'Extend a range until nothing inside points past it.', seqs: ['009', '010'] },
    ],
    neighbours: ['16_dp_1d', '19_intervals', '02_two_pointers', '12_heap_priority_queue'],
  },

  /* ------------------------------------------------------------------ 19 -- */
  '19_intervals': {
    name: 'Intervals',
    tagline: 'Sort by start to merge, by end to keep the most, or sweep the events in time order.',
    signals: [
      'a list of [start, end] pairs',
      'merge / insert / overlap / intersection',
      'minimum rooms / maximum concurrency / car pooling',
      'remove the fewest intervals so none overlap',
      'booking calendars that accept or reject',
    ],
    notThis: [
      ['Point queries on changing ranges', 'Segment tree / Fenwick'],
      ['A contiguous window over an array', 'Sliding window'],
    ],
    invariant: 'After sorting by start, an interval can only overlap the most recently kept interval.',
    templates: [{
      title: 'Sort by start, merge',
      code: String.raw`def merge(intervals):
    intervals.sort(key=lambda iv: iv[0])
    out = []
    for start, end in intervals:
        if out and start <= out[-1][1]:       # overlaps the last kept interval
            out[-1][1] = max(out[-1][1], end)
        else:
            out.append([start, end])
    return out`,
    }, {
      title: 'Sweep line (peak concurrency)',
      code: String.raw`def min_meeting_rooms(intervals):
    events = []
    for s, e in intervals:
        events.append((s, 1))
        events.append((e, -1))
    events.sort()                             # at a tie, -1 (an end) sorts first
    rooms = best = 0
    for _, delta in events:
        rooms += delta
        best = max(best, rooms)
    return best`,
    }],
    complexity: 'O(n log n) for the sort · O(n) for the scan',
    pitfalls: [
      'Deciding whether touching intervals ([1,2] and [2,3]) overlap — read the problem.',
      'Merging with `out[-1][1] = end` instead of `max(…)`: a contained interval shrinks it.',
      'Maximum non-overlapping set: sort by END, not start.',
    ],
    families: [
      { name: 'Sort by start, merge', when: 'Merge, insert, check overlaps, find gaps.', seqs: ['001', '002', '003', '008'] },
      { name: 'Sort by end, keep greedily', when: 'Keep the most intervals / fewest arrows.', seqs: ['004', '007'] },
      { name: 'Sweep line', when: 'How many are active at once.', seqs: ['005', '009'], also: ['12_heap_priority_queue/008'] },
      { name: 'Two sorted lists', when: 'Intersect two lists with two pointers.', seqs: ['006'] },
      { name: 'Online bookings', when: 'Accept or reject one interval at a time.', seqs: ['010', '011'] },
    ],
    neighbours: ['18_greedy', '12_heap_priority_queue', '22_sorting_algorithms', '26_segment_tree_fenwick'],
  },

  /* ------------------------------------------------------------------ 20 -- */
  '20_bit_manipulation': {
    name: 'Bit manipulation',
    tagline: 'XOR cancels pairs, n & (n − 1) drops the lowest set bit, and every bit can be counted on its own.',
    signals: [
      '“every element appears twice except one”',
      'O(1) extra space where a set would be the obvious answer',
      'count set bits, powers of two, reverse bits',
      'add without + / −',
      'a range AND / missing number from 0..n',
    ],
    notThis: [
      ['Frequencies with no pairing structure', 'Hash map'],
      ['Subset enumeration for n ≤ 20', 'Bitmask as a set — backtracking or DP'],
    ],
    invariant: 'XOR of everything so far = XOR of the values that appeared an odd number of times.',
    templates: [{
      title: 'XOR cancellation and n & (n − 1)',
      code: String.raw`def single_number(nums):
    x = 0
    for n in nums:
        x ^= n                                # a ^ a = 0 and a ^ 0 = a
    return x

def count_set_bits(n):
    count = 0
    while n:
        n &= n - 1                            # clears the lowest set bit
        count += 1
    return count`,
    }],
    complexity: 'O(n) or O(number of bits) · O(1) space',
    pitfalls: [
      'Python integers are unbounded — mask with `& 0xFFFFFFFF` to emulate 32-bit.',
      'Operator precedence: `x & 1 == 0` parses as `x & (1 == 0)`.',
      'Right-shifting negatives in Python never reaches 0.',
    ],
    families: [
      { name: 'XOR cancellation', when: 'Pairs cancel; the odd one out survives.', seqs: ['001', '005', '009'] },
      { name: 'Lowest-bit tricks', when: 'n & (n − 1), popcount, common prefix.', seqs: ['002', '003', '010'] },
      { name: 'Per-bit construction', when: 'Build or count the answer one bit at a time.', seqs: ['004', '006', '008'] },
      { name: 'Overflow-safe arithmetic', when: 'Digits within a fixed-width range.', seqs: ['007'] },
    ],
    neighbours: ['21_math_geometry', '01_arrays_hashing', '13_trie', '16_dp_1d'],
  },

  /* ------------------------------------------------------------------ 21 -- */
  '21_math_geometry': {
    name: 'Math & geometry',
    tagline: 'Find the arithmetic fact that replaces the simulation.',
    signals: [
      'digits of a number, carries, big-number strings',
      'powers, primes, factorials, gcd',
      'a sequence that must eventually repeat',
      'points, lines, slopes, squares on a plane',
    ],
    notThis: [
      ['A formula is not obvious and n is small', 'Simulate — then look for the pattern'],
      ['Bit-level structure', 'Bit manipulation'],
    ],
    invariant: 'Fast power: result · x^n stays equal to the original xⁿ on every iteration.',
    templates: [{
      title: 'Exponentiation by squaring',
      code: String.raw`def my_pow(x, n):
    if n < 0:
        x, n = 1 / x, -n
    result = 1.0
    while n:
        if n & 1:
            result *= x                       # this bit of n is set
        x *= x                                # x, x^2, x^4, x^8, ...
        n >>= 1
    return result`,
    }, {
      title: 'Peel digits with divmod',
      code: String.raw`def reverse_digits(x):
    out = 0
    while x > 0:
        x, d = divmod(x, 10)                  # peel off the last digit
        out = out * 10 + d
    return out`,
    }],
    complexity: 'O(log n) for fast power / digit loops · O(n log log n) for a sieve',
    pitfalls: [
      'Float slopes — use a gcd-reduced integer pair (dy, dx) with a normalised sign.',
      'Integer overflow in fixed-width languages; check before multiplying by 10.',
      'Negative exponents and n = INT_MIN.',
    ],
    families: [
      { name: 'Digits & carries', when: 'Work digit by digit, right to left.', seqs: ['001', '002', '005'] },
      { name: 'Number theory', when: 'Primes, factors, fast power.', seqs: ['004', '007', '008'], also: ['28_recursion_backtracking/016'] },
      { name: 'Cycles in number sequences', when: 'A deterministic sequence must repeat.', seqs: ['003'], also: ['08_linked_list/003'] },
      { name: 'Greedy tables', when: 'A fixed table of values, largest first.', seqs: ['006'] },
      { name: 'Geometry by hashing', when: 'Count points / lines / squares with exact keys.', seqs: ['009', '010'] },
    ],
    neighbours: ['20_bit_manipulation', '01_arrays_hashing', '24_matrix', '27_algorithms'],
  },

  /* ------------------------------------------------------------------ 22 -- */
  '22_sorting_algorithms': {
    name: 'Sorting',
    tagline: 'Sort to create structure — or reuse the merge / partition step as the algorithm itself.',
    signals: [
      'implement a sort, or sort a linked list in O(n log n)',
      'three distinct values to arrange in one pass',
      'the order is defined by a custom comparison (largest number)',
      'count inversions / smaller elements to the right',
      'O(n) for bounded values → counting / bucket sort',
    ],
    notThis: [
      ['Only the top k are needed', 'Heap or quickselect'],
      ['Order must be preserved', 'Two pointers / stable filtering'],
    ],
    invariant: 'Merge step: the output holds the smallest elements of both halves, in order; what remains is all larger.',
    templates: [{
      title: 'Merge sort (the merge step counts inversions for free)',
      code: String.raw`def merge_sort(a):
    if len(a) <= 1:
        return a
    mid = len(a) // 2
    left, right = merge_sort(a[:mid]), merge_sort(a[mid:])
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if left[i] <= right[j]:               # <= keeps the sort stable
            out.append(left[i]); i += 1
        else:
            out.append(right[j]); j += 1      # len(left) - i inversions end here
    return out + left[i:] + right[j:]`,
    }, {
      title: 'Dutch national flag (three-way partition)',
      code: String.raw`def sort_colors(nums):
    lo, i, hi = 0, 0, len(nums) - 1           # [0,lo) 0s · [lo,i) 1s · (hi,end] 2s
    while i <= hi:
        if nums[i] == 0:
            nums[lo], nums[i] = nums[i], nums[lo]
            lo += 1; i += 1
        elif nums[i] == 2:
            nums[i], nums[hi] = nums[hi], nums[i]
            hi -= 1                           # do NOT advance i: the new value is unseen
        else:
            i += 1`,
    }],
    complexity: 'O(n log n) comparison sorts · O(n + k) counting sort',
    pitfalls: [
      'Quicksort with a fixed pivot is O(n²) on sorted input — randomise.',
      'Advancing i after swapping with hi in the Dutch flag.',
      'Custom comparator must be consistent (transitive) or the sort is undefined.',
    ],
    families: [
      { name: 'Merge-based', when: 'Merge sorted data, sort lists, count inversions.', seqs: ['001', '002', '004', '008'], also: ['26_segment_tree_fenwick/003'] },
      { name: 'Partitioning', when: 'Arrange a few classes in one pass.', seqs: ['003'], also: ['27_algorithms/005'] },
      { name: 'Custom order & counting', when: 'A comparator or a bounded range does the work.', seqs: ['005', '006', '007'] },
    ],
    neighbours: ['12_heap_priority_queue', '19_intervals', '02_two_pointers', '26_segment_tree_fenwick'],
  },

  /* ------------------------------------------------------------------ 23 -- */
  '23_string_algorithms': {
    name: 'String algorithms',
    tagline: 'Never re-read the text: prefix functions and rolling hashes find patterns in linear time.',
    signals: [
      'find a pattern inside a text',
      'repeated substring / period of a string',
      'shortest palindrome by adding characters in front',
      'longest duplicate substring (binary search + hash)',
      'parse a number or an expression by hand',
    ],
    notThis: [
      ['A dictionary of many words', 'Trie'],
      ['Longest substring with a property', 'Sliding window'],
      ['Edit distance / subsequences', '2D DP'],
    ],
    invariant: 'pi[i] is the length of the longest proper prefix of s[:i+1] that is also its suffix.',
    templates: [{
      title: 'Prefix function (KMP)',
      code: String.raw`def prefix_function(s):
    pi = [0] * len(s)                         # pi[i]: longest border of s[:i+1]
    for i in range(1, len(s)):
        k = pi[i - 1]
        while k and s[i] != s[k]:
            k = pi[k - 1]                     # fall back to the next shorter border
        if s[i] == s[k]:
            k += 1
        pi[i] = k
    return pi

def find(text, pattern):                      # first index of pattern in text, or -1
    if not pattern:
        return 0
    pi = prefix_function(pattern + '\x00' + text)
    m = len(pattern)
    for i in range(2 * m, len(pi)):
        if pi[i] == m:
            return i - 2 * m
    return -1`,
    }],
    complexity: 'O(n + m) for KMP · O(n) expected for rolling hash',
    pitfalls: [
      'The separator must be a character that cannot appear in either string.',
      'Rolling hash collisions — verify a hash hit, or use two moduli.',
      'Building strings with += in a loop is O(n²); collect and join.',
    ],
    families: [
      { name: 'Prefix function (KMP)', when: 'Pattern search, periods, palindromic prefixes.', seqs: ['001', '002', '006'] },
      { name: 'Hashing & encoding', when: 'Fixed-length windows or binary search on length.', seqs: ['004', '007'] },
      { name: 'Parsing & construction', when: 'Careful state machines and candidate checks.', seqs: ['003', '005', '008'] },
    ],
    neighbours: ['13_trie', '03_sliding_window', '17_dp_2d', '01_arrays_hashing'],
  },

  /* ------------------------------------------------------------------ 24 -- */
  '24_matrix': {
    name: 'Matrix',
    tagline: 'Index arithmetic: rotate by transpose + reverse, walk by shrinking boundaries.',
    signals: [
      'rotate / transpose / flip a matrix in place',
      'spiral or diagonal traversal order',
      'set rows / columns to zero with O(1) extra space',
      'search a row- and column-sorted matrix',
      'update every cell from its neighbours simultaneously (Game of Life)',
    ],
    notThis: [
      ['Connected regions of cells', 'Graph flood fill'],
      ['Paths from corner to corner', '2D DP'],
    ],
    invariant: 'Spiral: rows < top and > bottom, columns < left and > right are already emitted.',
    templates: [{
      title: 'Four shrinking boundaries (Spiral)',
      code: String.raw`def spiral_order(matrix):
    out = []
    top, bottom, left, right = 0, len(matrix) - 1, 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for c in range(left, right + 1):
            out.append(matrix[top][c])
        top += 1
        for r in range(top, bottom + 1):
            out.append(matrix[r][right])
        right -= 1
        if top <= bottom:                     # a single row is left: do not repeat it
            for c in range(right, left - 1, -1):
                out.append(matrix[bottom][c])
            bottom -= 1
        if left <= right:                     # a single column is left
            for r in range(bottom, top - 1, -1):
                out.append(matrix[r][left])
            left += 1
    return out`,
    }, {
      title: 'Rotate 90° clockwise in place',
      code: String.raw`def rotate(matrix):
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):             # transpose across the main diagonal
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:
        row.reverse()                         # then mirror each row`,
    }],
    complexity: 'O(rows · cols) time · O(1) extra space for the in-place variants',
    pitfalls: [
      '`[[0] * n] * m` creates m references to ONE row.',
      'Spiral without the inner guards repeats the middle row or column.',
      'Simultaneous updates: encode old and new state in the same cell.',
    ],
    families: [
      { name: 'Transform in place', when: 'Transpose, rotate, mark, encode two states.', seqs: ['001', '002', '005', '007'] },
      { name: 'Boundary walks', when: 'Spiral and diagonal orders.', seqs: ['003', '004', '008'] },
      { name: 'Staircase search', when: 'Sorted rows and columns: start at a corner that splits.', seqs: ['006'], also: ['05_binary_search/005'] },
    ],
    neighbours: ['14_graphs', '17_dp_2d', '21_math_geometry', '05_binary_search'],
  },

  /* ------------------------------------------------------------------ 25 -- */
  '25_design': {
    name: 'Data-structure design',
    tagline: 'Pick the structures whose combination makes every required operation hit its target cost.',
    signals: [
      '“design a class with get / put / add / remove …”',
      'each operation must be O(1) (or O(log n))',
      'eviction by recency or frequency (LRU / LFU)',
      'time-based data, snapshots, rate limits, history',
      'random access plus fast deletion',
    ],
    notThis: [
      ['Only one operation to answer', 'The underlying algorithm pattern'],
    ],
    invariant: 'Every structure in the design stays consistent with the others after each public method returns.',
    templates: [{
      title: 'Hash map + doubly linked list (LRU cache)',
      code: String.raw`class Node:
    def __init__(self, key=0, val=0):
        self.key, self.val = key, val
        self.prev = self.next = None

class LRUCache:
    def __init__(self, capacity):
        self.cap, self.map = capacity, {}
        self.head, self.tail = Node(), Node()     # sentinels: no edge cases
        self.head.next, self.tail.prev = self.tail, self.head

    def _unlink(self, node):
        node.prev.next, node.next.prev = node.next, node.prev

    def _push_front(self, node):
        node.prev, node.next = self.head, self.head.next
        self.head.next.prev = node
        self.head.next = node

    def get(self, key):
        if key not in self.map:
            return -1
        node = self.map[key]
        self._unlink(node)
        self._push_front(node)                    # touched: now the most recent
        return node.val

    def put(self, key, val):
        if key in self.map:
            self._unlink(self.map[key])
        node = self.map[key] = Node(key, val)
        self._push_front(node)
        if len(self.map) > self.cap:
            lru = self.tail.prev                  # the least recent sits before tail
            self._unlink(lru)
            del self.map[lru.key]`,
    }],
    complexity: 'Target O(1) per operation for LRU, LFU, RandomizedSet',
    pitfalls: [
      'Forgetting to update the map when a linked-list node is evicted.',
      'Removing from the middle of an array in O(n) — swap with the last, then pop.',
      'Mutable default arguments shared across instances.',
    ],
    families: [
      { name: 'Build a hash table', when: 'Buckets and chaining from scratch.', seqs: ['001', '002'] },
      { name: 'Map + list / array hybrids', when: 'O(1) access plus an order or random pick.', seqs: ['004', '005', '008'], also: ['08_linked_list/013'] },
      { name: 'Time-based designs', when: 'Rate limits, hit counters, snapshots, price feeds.', seqs: ['003', '011', '012', '013'], also: ['05_binary_search/009'] },
      { name: 'History & queues', when: 'Back / forward history, a moving snake.', seqs: ['006', '007'] },
      { name: 'Tree & trie designs', when: 'File systems and autocomplete.', seqs: ['009', '010'], also: ['13_trie/007'] },
    ],
    neighbours: ['08_linked_list', '01_arrays_hashing', '13_trie', '12_heap_priority_queue'],
  },

  /* ------------------------------------------------------------------ 26 -- */
  '26_segment_tree_fenwick': {
    name: 'Segment tree / Fenwick',
    tagline: 'Range queries AND point updates, both in O(log n).',
    signals: [
      'range sum / min / max queries with updates in between',
      'count elements smaller (or larger) than x seen so far',
      'reverse pairs / count of range sums',
      'coordinate compression over large values',
      'skyline / falling squares — heights over intervals',
    ],
    notThis: [
      ['The array never changes', 'Prefix sums'],
      ['Only the global max / min is needed', 'Heap'],
    ],
    invariant: 'Fenwick: tree[i] stores the sum of the (i & −i) elements that end at position i.',
    templates: [{
      title: 'Fenwick tree (binary indexed tree)',
      code: String.raw`class Fenwick:
    def __init__(self, n):
        self.tree = [0] * (n + 1)                 # 1-indexed internally

    def add(self, i, delta):                      # nums[i] += delta  (0-indexed)
        i += 1
        while i < len(self.tree):
            self.tree[i] += delta
            i += i & -i                           # climb to the next covering node

    def prefix(self, i):                          # sum(nums[0..i])
        i += 1
        s = 0
        while i > 0:
            s += self.tree[i]
            i -= i & -i                           # drop the lowest set bit
        return s

    def range_sum(self, l, r):
        return self.prefix(r) - (self.prefix(l - 1) if l else 0)`,
    }],
    complexity: 'O(log n) per update / query · O(n) space',
    pitfalls: [
      'Mixing 0- and 1-based indices in a Fenwick tree.',
      'Segment tree array sized 2n for a non-power-of-two n in the recursive form — use 4n.',
      'Point update “set to v” must add v − old, not v.',
    ],
    families: [
      { name: 'Range queries with updates', when: 'Fenwick or segment tree over positions or values.', seqs: ['001', '002', '005'], also: ['04_prefix_sum/002'] },
      { name: 'Counting inversions', when: 'Merge-sort counting or a Fenwick over ranks.', seqs: ['003', '004'], also: ['22_sorting_algorithms/008'] },
      { name: 'Sweep + heap', when: 'Critical points in x, active heights in a heap.', seqs: ['006'] },
    ],
    neighbours: ['04_prefix_sum', '22_sorting_algorithms', '19_intervals', '12_heap_priority_queue'],
  },

  /* ------------------------------------------------------------------ 27 -- */
  '27_algorithms': {
    name: 'Randomized & classic algorithms',
    tagline: 'Uniform randomness, reservoir sampling, quickselect and divide-and-conquer — each with a proof you should be able to say.',
    signals: [
      'shuffle / pick uniformly at random',
      'a stream of unknown length, pick one element',
      'pick with probability proportional to a weight',
      'k-th largest in O(n) average',
      'all ways to parenthesise / split an expression',
    ],
    notThis: [
      ['Deterministic top-k', 'Heap'],
      ['Count, not enumerate, the split results', 'Interval DP'],
    ],
    invariant: 'Reservoir: after n items, each one has been kept with probability exactly 1/n.',
    templates: [{
      title: 'Fisher–Yates shuffle and reservoir sampling',
      code: String.raw`import random

def shuffle(a):
    for i in range(len(a) - 1, 0, -1):
        j = random.randint(0, i)                  # inclusive: i may swap with itself
        a[i], a[j] = a[j], a[i]
    return a

def reservoir_pick(stream):
    chosen = None
    for n, x in enumerate(stream, 1):
        if random.randrange(n) == 0:              # keep x with probability 1/n
            chosen = x
    return chosen`,
    }],
    complexity: 'O(n) shuffle / reservoir · O(n) average quickselect · O(log n) weighted pick',
    pitfalls: [
      '`randint(0, n - 1)` for every i (not 0..i) produces a biased shuffle.',
      'Weighted pick: bisect on prefix sums with the right side (bisect_right vs left).',
      'Quickselect without a random pivot is O(n²) on sorted input.',
    ],
    families: [
      { name: 'Uniform randomness', when: 'Shuffles, reservoirs, rejection sampling.', seqs: ['001', '002', '003', '009'] },
      { name: 'Weighted & remapped sampling', when: 'Prefix sums + bisect, or remap forbidden values.', seqs: ['004', '008'] },
      { name: 'Selection & partitioning', when: 'Quickselect and three-way partitions.', seqs: ['005', '007'], also: ['22_sorting_algorithms/003'] },
      { name: 'Divide and conquer with memo', when: 'Split at every operator, combine results.', seqs: ['006'] },
    ],
    neighbours: ['22_sorting_algorithms', '21_math_geometry', '12_heap_priority_queue', '04_prefix_sum'],
  },

  /* ------------------------------------------------------------------ 28 -- */
  '28_recursion_backtracking': {
    name: 'Structural recursion',
    tagline: 'Trust the recursive call: define what it returns for a smaller input, then combine.',
    signals: [
      'the problem is defined in terms of a smaller copy of itself',
      'linked lists or trees where each call returns a new head or a pair of values',
      '“generate all structurally unique trees”',
      'nested input (a list containing lists) or a string encoding a tree',
      'choose where to split, then solve both sides',
    ],
    notThis: [
      ['Subproblems overlap heavily and only a count is needed', 'DP (memoise the recursion)'],
      ['Enumerate choices with undo', 'Backtracking'],
    ],
    invariant: 'Assume the call on the smaller input already returns the right answer; only the combine step is yours.',
    templates: [{
      title: 'Return a pair from each subtree (House Robber III)',
      code: String.raw`def rob_tree(root):
    def best(node):                               # returns (rob this node, skip it)
        if not node:
            return (0, 0)
        l_rob, l_skip = best(node.left)
        r_rob, r_skip = best(node.right)
        rob = node.val + l_skip + r_skip
        skip = max(l_rob, l_skip) + max(r_rob, r_skip)
        return (rob, skip)
    return max(best(root))`,
    }, {
      title: 'Memoised split-point counting (Unique BSTs)',
      code: String.raw`from functools import lru_cache

@lru_cache(maxsize=None)
def num_trees(n):
    if n <= 1:
        return 1                                  # the empty tree / a single node
    return sum(num_trees(root - 1) * num_trees(n - root)
               for root in range(1, n + 1))`,
    }],
    complexity: 'O(n) for one call per node / element · exponential for generation',
    pitfalls: [
      'Missing or wrong base case — the recursion never bottoms out.',
      'Returning too little: when the parent needs two facts, return a tuple.',
      'Recomputing identical subcalls — add @lru_cache when arguments repeat.',
    ],
    families: [
      { name: 'Linear recursion on numbers & arrays', when: 'One smaller call per step.', seqs: ['001', '002', '003', '004', '005', '006', '016'] },
      { name: 'Recursion on linked lists', when: 'The call returns the new head of what follows.', seqs: ['007', '008', '010'], also: ['08_linked_list/001'] },
      { name: 'Structural parsing', when: 'Nested lists, encoded trees, balanced blocks.', seqs: ['009', '021', '022'] },
      { name: 'Tree recursion with pair returns', when: 'Each subtree reports several facts.', seqs: ['013', '014', '017', '018', '019', '025'], also: ['10_trees/018'] },
      { name: 'Generate structures (Catalan)', when: 'Every choice of root, every shape.', seqs: ['011', '012', '015'] },
      { name: 'Split point & search', when: 'Try every split, or every operator between digits.', seqs: ['020', '023', '024'], also: ['17_dp_2d/013'] },
    ],
    neighbours: ['09_recursion_backtracking', '10_trees', '16_dp_1d', '08_linked_list'],
    accepts: ['09_recursion_backtracking', '10_trees'],
  },
};

/* ------------------------------------------------------------ lookups -- */
const playbook = topicId => PLAYBOOKS[topicId] || null;

/* { family, index } for a problem id "<topic>/<seq>", from its own topic's families */
function problemFamily(pid) {
  const [topic, seq] = String(pid).split('/');
  const pb = PLAYBOOKS[topic];
  if (!pb) return null;
  const index = pb.families.findIndex(f => f.seqs.includes(seq));
  return index < 0 ? null : { family: pb.families[index], index, topic };
}

/* problems that share the move: same family first, then cross-topic `also` links
   pointing at or from this problem */
function familySiblings(pid) {
  const hit = problemFamily(pid);
  const out = [];
  if (hit) {
    hit.family.seqs.forEach(s => { const id = `${hit.topic}/${s}`; if (id !== pid) out.push({ id, why: 'same move' }); });
    (hit.family.also || []).forEach(id => { if (id !== pid) out.push({ id, why: 'same move, other pattern' }); });
  }
  Object.entries(PLAYBOOKS).forEach(([topic, pb]) => pb.families.forEach(f => {
    if ((f.also || []).includes(pid)) f.seqs.forEach(s => {
      const id = `${topic}/${s}`;
      if (id !== pid && !out.some(o => o.id === id)) out.push({ id, why: 'same move, other pattern' });
    });
  }));
  return out;
}
