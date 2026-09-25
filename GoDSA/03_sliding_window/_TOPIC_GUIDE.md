# Topic 03 · Sliding Window — Go Deep Dive

> A sliding window is just two indices into a slice you never re-slice. The
> entire trick is maintaining aggregate state *incrementally* as the window
> moves, instead of recomputing it. Get that wrong and an O(n) algorithm
> quietly becomes O(n·k). Go adds one wrinkle Python doesn't have: there is no
> built-in deque, and the "obvious" slice-based one leaks memory. This is the
> document that stops both classes of bug.

---

## Part 1 · Two Indices, Not Two Slices

### 1.1 The shape of every sliding window

Every sliding window problem walks a right pointer `r` forward, and — when
some condition is violated — walks a left pointer `l` forward to fix it. The
window is the half-open range `[l, r)` or `[l, r]` depending on convention.

```go
l := 0
for r := 0; r < len(s); r++ {
    include(s[r])                 // grow: absorb s[r] into window state
    for windowInvalid() {         // shrink: violates constraint
        exclude(s[l])              // remove s[l] from window state
        l++
    }
    updateAnswer(r - l + 1)        // window is valid here
}
```

**Never re-slice `s[l:r+1]` to "look at the window."** A slice expression is
O(1) header arithmetic (Part 1.2 of Topic 01), but if you then iterate that
sub-slice to recompute a sum, a max, or a frequency count, you've turned an
O(n) sliding window into O(n·k). The window's *content* lives in `s`; the
window's *state* (sum, frequency map, distinct count) is a separate variable
you update by ±1 as `l` and `r` move. That incremental update is the entire
algorithm — everything else is bookkeeping.

```arch
%% caption: Every window loop is enter, restore, record. The only decision is where "record" goes: after the shrink for the longest window, inside the shrink for the shortest.
grid 220x110
node a "for r := 0; r < n; r++" at 0,0 shape=pill
node b "ENTER" at 1,0 shape=card icon=start sub="add s[r] to the window state"
node c "window invalid?" at 1,1 shape=diamond color=amber sub="longest / fixed shapes"
node e "RECORD longest" at 0,1 shape=card icon=check color=green sub="r - l + 1"
node d "RESTORE" at 1,2 shape=card icon=sync color=orange sub="remove s[l], l++"
node f "window still valid?" at 2,1 shape=diamond color=amber sub="shortest shape"
node g "RECORD shortest" at 2,2 shape=card icon=sync color=orange sub="then remove s[l], l++"
a -> b
b -> c
b:R -> f:T
c -> d : "yes"
d:R -> c:R
c -> e : "no"
e -> a
f -> g : "yes"
g:R -> f:R
```

```go
// ❌ O(n·k): recomputes the sum every time the window moves
for r := range nums {
    for l := max(0, r-k+1); l <= r; l++ {
        sum += nums[l]           // re-scans up to k elements per r
    }
}

// ✅ O(n): sum is maintained incrementally
sum += nums[r]
if r >= k {
    sum -= nums[r-k]
}
```

### 1.2 Fixed-size vs. variable-size windows

| | Fixed-size (e.g. LC 643 max average subarray) | Variable-size (e.g. LC 3, LC 76) |
|---|---|---|
| Window width | Constant `k`, given | Grows/shrinks based on a constraint |
| Loop shape | Single loop, subtract when `r >= k` | Outer grow, inner shrink-while-invalid |
| When to record answer | Every step once `r >= k-1` | Every step the window is valid (or, for "minimum window," every step it's valid — you're looking for the *smallest* valid window, so you record right after shrinking, not before) |

The two look almost identical in code, and mixing up "record before shrink"
vs "record after shrink" is the single most common off-by-one in this topic.
For **maximum**-window problems (longest substring, longest subarray with
constraint), record after growing, before entering the shrink loop's next
iteration invalidates it. For **minimum**-window problems (LC 76), record
*inside* the shrink loop, once, at the moment the window is still valid —
because shrinking further might invalidate it, and you want the smallest
valid width you've seen.

### 1.3 Window state: fixed array vs. map

This is a direct extension of Topic 01 Part 2.6. The window's state is a
frequency count (or a running sum, or a distinct-count) — how you store it
depends on the alphabet:

```go
// ASCII-only text (most LeetCode string problems): fixed array.
// No hashing, no allocation, stack-resident, cache-friendly.
var window [128]int
window[s[r]]++
window[s[l]]--

// Full Unicode, or a small number of *arbitrary* keys (ints, structs):
// a map is the only option, but every access now hashes.
window := make(map[byte]int)
window[s[r]]++
```

> ✅ **Default to `[128]int` or `[256]int` for byte-indexed ASCII problems.**
> It is strictly faster than `map[byte]int` — no hash computation, no bucket
> lookup (Topic 01 Part 2.1), just a direct array index — and it lives on the
> stack if the array doesn't escape, so there's no <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr> pressure at all. Only
> reach for a map when the key space is genuinely large or the keys aren't
> small integers (e.g. windows over `[]int` with values in `[-10⁹, 10⁹]`).

### 1.4 The "each element enters and leaves once" complexity argument

`l` and `r` each only ever move forward, and each only ever moves at most
`n` times total across the whole run — not per iteration of the outer loop.
So even though there's a nested `for` loop for shrinking, the total work is
bounded by `2n`, not `n²`:

```
r: 0 1 2 3 4 5 6 7 8 9   → n steps, forward only
l:       0 1 2 3         → at most n steps total, forward only, across ALL r
```

This is the same amortized argument as two-pointer techniques in general:
**O(n) total, not O(n) per step.** If you find yourself resetting `l` back
to 0, or to some value less than its previous position, you no longer have a
sliding window — you have something else, and the O(n) bound no longer holds.

---

## Part 2 · The Monotonic Deque Problem (LC 239) — Go Has No Deque

### 2.1 Why a plain window doesn't give you the max in O(1)

"Sliding Window Maximum" needs the max of the current window after every
slide. Recomputing the max by scanning the window each time is O(n·k). The
standard fix is a **monotonic deque of indices**: push indices from the back,
but before pushing, pop everything from the back that has a *smaller* value
than the incoming one: an element that is smaller than a *newer* element can
never be a window maximum again — the newer one is at least as large and will
stay in the window longer, so the older one is dominated forever. Pop from the
*front* when the front index has fallen out of the window. The front is always
the max.

```
nums = [1,3,-1,-3,5,3,6,7], k = 3

deque holds INDICES, values shown in brackets for clarity:
r=0: [1]                       deque: [0]
r=1: [3] pops 1 (1<3)          deque: [1]
r=2: [-1]                      deque: [1,2]        window max = nums[1] = 3
r=3: [-3], front(1) still in   deque: [1,2,3]       window max = 3
r=4: [5] pops 3,2,1 (all <5)   deque: [4]           window max = 5
...
```

The deque needs **push-back, pop-back, pop-front, and peek-front** — all
O(1). That's a deque. Go's standard library has none.

```arch
%% caption: One step of the monotonic deque. It holds indices whose values decrease front to back, so the front is always the current window maximum.
grid 230x100
node n "new element nums[r]" at 0,0 shape=pill
node f "front index has left the window?" at 0,1 shape=diamond color=amber sub="deque[head] <= r - k"
node pf "Pop front" at 1,1 shape=card icon=sync color=orange sub="head++"
node b "back value <= nums[r]?" at 0,2 shape=diamond color=amber
node pb "Pop back" at 1,2 shape=card icon=sync color=orange sub="dominated for good: tail--"
node push "Push r at the back" at 0,3 shape=box
node out "r >= k - 1?" at 0,4 shape=diamond color=amber
node m "Window max" at 1,4 shape=card icon=check color=green sub="nums[deque[head]]"
n -> f
f:R -> pf:L : "yes"
pf:T -> f:T
f -> b : "no"
b:R -> pb:L : "yes"
pb:T -> b:T
b -> push : "no"
push -> out
out -> m : "yes"
```

### 2.2 Three ways to build one in Go, and what each costs

**(a) A slice used as a deque, popping the front with `q = q[1:]`**

```go
q = q[1:]     // "pop front": O(1) — it only moves the slice header
```

This is O(1) and the simplest thing that works. Two costs are worth knowing. The popped element **stays in
the backing array** — unreachable through `q`, but not freed, so if the elements are pointers they stay
alive until the array is reallocated (zero the slot first: `q[0] = nil; q = q[1:]`). And `cap(q)` shrinks by
one on every pop, so a later `append` runs out of room sooner and reallocates. Neither matters for one
bounded LeetCode input; on a long-running stream you pay for reallocations you did not need.

**(b) `container/list` — a real doubly linked list**

```go
import "container/list"
dq := list.New()
dq.PushBack(i)
dq.Remove(dq.Front())
front := dq.Front().Value.(int)
```

Correct and O(1) for every operation, but every node is a separate heap
allocation (`list.Element` wraps your value plus two pointers), and every
read needs a type assertion out of `interface{}`/`any`. For `n` up to LC's
usual `10⁵`, this is completely fine — but it is measurably slower than (c)
in a benchmark, because of allocation + pointer chasing vs. contiguous array
access.

**(c) A preallocated slice with two integer cursors**

```go
buf := make([]int, n)     // n known and bounded
head, tail := 0, 0        // [head, tail) is the live range, tail exclusive
// push back:  buf[tail] = idx; tail++
// pop back:   tail--
// pop front:  head++
// peek front: buf[head]
```

Zero allocations after the initial `make`, O(1) every operation, no aliasing
concern because `head`/`tail` are plain integers, not slice headers. When every
index is pushed **at most once** (as in LC 239) the cursors only ever move
forward, so no wrap-around is needed and a slice of length `n` is enough. (An
unbounded stream needs a true ring buffer — `% cap` on both cursors; see the
circular queue in topic 07.) This is the version to write in an interview once
you've stated the tradeoff — it reads almost identically to (a) but has no
lifetime subtlety.

> ✅ **Recommendation:** for a one-shot bounded-input problem (any LeetCode
> deque problem), use (c) — a slice sized to `n` up front with two integer
> cursors. Mention (a) as the "quick and correct for this input size" version
> and (b) as the "correct but allocates per element" version, and you've
> covered the tradeoff space an interviewer wants to hear.

### 2.3 Full LC 239 with the cursor-based deque

```go
func maxSlidingWindow(nums []int, k int) []int {
    n := len(nums)
    result := make([]int, 0, n-k+1)   // preallocate — size is known (Topic 01 §1.3)

    deque := make([]int, n)           // holds indices; head/tail cursors, no wrap needed
    head, tail := 0, 0                // live range is deque[head:tail]

    for r := 0; r < n; r++ {
        // evict indices that fell out of the window on the left
        for head < tail && deque[head] <= r-k {
            head++
        }
        // maintain decreasing order of VALUES from front to back:
        // pop any trailing index whose value is dominated by nums[r]
        for head < tail && nums[deque[tail-1]] <= nums[r] {
            tail--
        }
        deque[tail] = r
        tail++

        if r >= k-1 {
            result = append(result, nums[deque[head]])
        }
    }
    return result
}
```

Each index is pushed once and popped at most once across the whole run —
the same "enters and leaves once" argument as Part 1.4 — so this is O(n)
despite the inner `for` loops.

---

## Part 3 · Variable Windows Over Strings

### 3.1 Longest substring without repeating characters (LC 3)

The constraint is "no duplicate byte in the window." Track last-seen index
per byte; when `s[r]` was last seen *inside* the current window, jump `l`
past it directly rather than incrementing one step at a time — this is
still O(n) total because `l` only ever moves forward.

```go
func lengthOfLongestSubstring(s string) int {
    var lastSeen [128]int
    for i := range lastSeen {
        lastSeen[i] = -1          // sentinel: "not seen yet"
    }

    best, l := 0, 0
    for r := 0; r < len(s); r++ {
        c := s[r]
        if lastSeen[c] >= l {     // duplicate is INSIDE the current window
            l = lastSeen[c] + 1   // jump left past it — not l++
        }
        lastSeen[c] = r
        if width := r - l + 1; width > best {
            best = width
        }
    }
    return best
}
```

> ⚠️ **`lastSeen[c] >= l`, not just `lastSeen[c] != -1`.** A byte can have
> been seen *before* the current window started — that's not a duplicate
> inside the window and must not move `l` backward. This is the second most
> common bug in this topic, after the record-before/after-shrink mixup in
> Part 1.2.

### 3.2 Why `strings.Builder` never shows up in this topic

Sliding window problems *read* a fixed input and report an index, length, or
substring slice of the original — they don't construct new strings
character-by-character in a loop. When you do need to return the actual
matched text, a single `s[l:r+1]` slice expression is O(1) (Topic 01 Part
1.2, strings share the same header-not-copy slicing as `[]byte`) — there is
no accumulation loop for `strings.Builder` to optimize away.

---

## Part 4 · Building Minimum Window Substring From Scratch (LC 76)

This is the canonical "need map / window map" pattern: track how many of
each required character you *need*, how many you currently *have* in the
window, grow until the window satisfies every requirement, then shrink as
far as possible while it still does — recording the minimum width each time
it does.

```go
func minWindow(s, t string) string {
    if len(s) < len(t) || t == "" {
        return ""
    }

    var need, window [128]int
    for i := 0; i < len(t); i++ {
        need[t[i]]++
    }

    required := 0                  // distinct chars in t that need matching
    for _, c := range need {
        if c > 0 {
            required++
        }
    }
    formed := 0                    // distinct chars currently fully satisfied

    bestLen := len(s) + 1
    bestL := 0
    l := 0

    for r := 0; r < len(s); r++ {
        c := s[r]
        window[c]++
        if need[c] > 0 && window[c] == need[c] {
            formed++                // this char JUST became fully satisfied
        }

        // shrink while every requirement is still met
        for formed == required {
            if r-l+1 < bestLen {
                bestLen = r - l + 1
                bestL = l
            }
            left := s[l]
            window[left]--
            if need[left] > 0 && window[left] < need[left] {
                formed--             // shrinking JUST broke a requirement
            }
            l++
        }
    }

    if bestLen == len(s)+1 {
        return ""
    }
    return s[bestL : bestL+bestLen]
}
```

> ⚠️ `[128]int` assumes ASCII: a byte ≥ 128 (any <abbr title="Unicode Transformation Format. A family of character encodings capable of encoding all possible Unicode code points.">UTF</abbr>-8 multi-byte character) makes `need[t[i]]` panic with
> `index out of range`. LeetCode guarantees English letters here; otherwise use `[256]int` over bytes or a
> `map[rune]int` over `[]rune(s)`.

**Talk track while writing:** `need` is fixed once from `t` and never
changes; `window` mirrors it as the pointer moves. `formed` is the key
optimization — it turns "are all requirements met?" from an O(128) scan of
`need` vs `window` into an O(1) counter check, updated only at the exact
moments a single character's count crosses its required threshold in either
direction. This is what keeps the algorithm O(|s| + |t|) instead of
O(|s| · 128).

> ⚠️ **`formed++`/`formed--` must fire on the crossing, not on every
> increment.** `window[c] == need[c]` is true for exactly one increment (the
> one that reaches the requirement); every earlier increment of a
> still-needed char, and every later increment past the requirement, must
> *not* touch `formed`. Get the comparison operator wrong (`>=` instead of
> `==` for the grow side, or `<=` instead of `<` for the shrink side) and
> `formed` either double-counts or never reaches `required`.

---

## Part 5 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Deque | `collections.deque` — O(1) both ends, built in | **No built-in deque** — pick a re-sliced slice, `container/list`, or a preallocated slice with cursors (Part 2.2) |
| Frequency counter | `collections.Counter` | `[128]int` array or `map[byte]int` (Topic 01 §2.6) |
| `defaultdict(int)` for `need`/`window` maps | Built in | Zero value does this for free — no init needed |
| Popping the front of a list | O(n) (`list.pop(0)` shifts) | O(1) via `s = s[1:]` (header move) — but see the retention caveat in §2.2(a) |
| Substring slicing for the answer | O(k) copy | O(1) view — `s[l:r+1]` shares memory with `s` (Topic 01 §1.2) |
| Sentinel values | `float('inf')`, `-1`, `None` | No `None` for `int`; use `-1` or `math.MaxInt` explicitly, as in `lastSeen` above |

---

## Part 6 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| Fixed-size window, incremental sum/max | O(n) | O(1) | LC 643 Max Average Subarray |
| Variable window, expand/shrink on constraint | O(n) | O(1) or O(k) | LC 3, LC 209, LC 1004 |
| Two-map "need/have" counting window | O(n + m) | O(alphabet) | LC 76 Minimum Window Substring |
| Monotonic deque of indices | O(n) | O(k) | LC 239 Sliding Window Maximum |
| Fixed frequency array as window state | O(n) | O(1) (bounded alphabet) | LC 438, LC 567 |
| Jump-left-past-duplicate (last-seen index) | O(n) | O(alphabet) | LC 3 |

---

<!-- block:03_go_1_shapes -->
## Part 7 · The Six Window Shapes in Go

Part 1 gave the generic loop. Every sliding-window problem is one of six shapes; naming the shape *is*
the solution. All code below ran on Go 1.24.5 against LeetCode's own examples.

```arch
%% caption: Which window shape to reach for. Two questions decide it: is the size given, and what is being asked.
grid 240x100
node q "What is being asked?" at 1,0 shape=pill
node a "Window size k given?" at 1,1 shape=diamond color=amber
node fa "Shape A: fixed window" at 2,1 shape=card icon=grid color=green sub="add one on the right, drop one on the left"
node b "What is optimised?" at 1,2 shape=diamond color=amber
node fb "Longest valid" at 0,2 shape=card icon=filter color=green sub="Shape B: shrink while INVALID, record after"
node fc "Shortest valid" at 2,2 shape=card icon=filter color=green sub="Shape C: shrink while still VALID, record inside"
node fd "Longest, length only" at 0,3 shape=card icon=speed color=green sub="Shape D: never-shrinking window"
node fe "Count subarrays" at 1,3 shape=card icon=counter color=green sub="Shape E: atMost(g) minus atMost(g-1)"
node ff "Max or min of the window" at 2,3 shape=card icon=layers color=green sub="Shape F: monotonic deque"
q -> a
a -> fa : "yes"
a -> b : "no"
b -> fb
b -> fc
b:B -> fd:T
b -> fe
b:B -> ff:T
```

| Shape | Loop | Record where | Init the answer | Problems |
|---|---|---|---|---|
| **A** fixed | one `for`, subtract when `r >= k` | every step once `r >= k-1` | first window / `math.MinInt` | 643, 1456, 219, 567, 438 |
| **B** longest | `for` + `for invalid { shrink }` | after the shrink | `0` | 3, 1004, 904 |
| **C** shortest | `for` + `for valid { record; shrink }` | *inside* the shrink | `math.MaxInt` | 209, 76 |
| **D** never-shrinking | `for` + `if invalid { slide by ONE }` | the final width | — | 424 |
| **E** counting | `for` + `for over { shrink }`; `count += r-l+1` | every step | `0` | 930, 992 |
| **F** deque | `for` + pop-back / pop-front | every step once `r >= k-1` | — | 239, 1438 |

### C · shortest valid window (LC 209)

```go
func minSubArrayLen(target int, nums []int) int {
    best, l, total := math.MaxInt, 0, 0
    for r, x := range nums {
        total += x                              // ENTER
        for total >= target {                   // while still VALID
            best = min(best, r-l+1)             // record INSIDE the shrink
            total -= nums[l]; l++
        }
    }
    if best == math.MaxInt { return 0 }         // nothing qualified: the answer is 0, not "infinity"
    return best                                 // (7, [2 3 1 2 4 3]) -> 2
}
```

Two Go notes: `math.MaxInt` is the sentinel (there is no `inf` for `int`), and the `min` builtin (Go 1.21+)
replaces a hand-written helper. This only works while every number is **non-negative** — see the next Part.

### D · the never-shrinking window (LC 424)

When you only need the *length* of the longest window, the window never has to shrink: it may only grow, or
slide forward by one. `maxFreq` never has to decrease either, because a smaller value can never produce a
larger answer.

```go
func characterReplacement(s string, k int) int {
    var count [26]int
    l, maxFreq := 0, 0
    for r := 0; r < len(s); r++ {
        count[s[r]-'A']++
        maxFreq = max(maxFreq, count[s[r]-'A'])
        if (r-l+1)-maxFreq > k {                // invalid: slide by ONE, never below the best size
            count[s[l]-'A']--
            l++
        }
    }
    return len(s) - l                           // the final width is the answer
}                                               // ("AABABBA", 1) -> 4
```

`maxFreq` is a **count**, not a letter — you never need to know *which* letter is most frequent.

### E · counting subarrays: `atMost(g) − atMost(g−1)` (LC 930, 992)

"Exactly g" is not hereditary (a valid window can contain an invalid one), so no single window bounds it.
"At most g" *is* hereditary, and it counts a whole family per step: every subarray ending at `r` and
starting in `[l, r]` qualifies, which is `r - l + 1` of them.

```go
func atMost(nums []int, g int) int {
    if g < 0 { return 0 }                       // the goal == 0 case: atMost(-1) is 0
    l, sum, count := 0, 0, 0
    for r, x := range nums {
        sum += x
        for sum > g { sum -= nums[l]; l++ }
        count += r - l + 1                      // subarrays ending at r
    }
    return count
}
// numSubarraysWithSum = atMost(nums, goal) - atMost(nums, goal-1)     ([1 0 1 0 1], 2) -> 4
```

The distinct-values version (LC 992) swaps the state for a `map[int]int` and the test for `len(cnt) > k`.
**Delete the key when its count reaches zero**, or `len` never falls:

```go
cnt[y]--
if cnt[y] == 0 { delete(cnt, y) }               // len(cnt) is the distinct count
// atMostKDistinct(k) - atMostKDistinct(k-1)     ([1 2 1 2 3], 2) -> 7
```

---
<!-- /block:03_go_1_shapes -->

<!-- block:03_go_2_legality -->
## Part 8 · When a Window Is Legal — and When to Stop

A window moves `l` only forward, so it silently assumes **once a window is invalid, growing it further cannot
make it valid again**, and once it is valid, shrinking it *from the left* can only help or keep it valid. That
property is *hereditary validity*, and it is what makes the amortised O(n) argument true.

| Predicate | Hereditary? | Window? |
|---|---|---|
| Sum `≥ target` over **non-negative** numbers | yes — adding only raises the sum | ✅ Shape C (LC 209) |
| Sum `≥ target` with **negative** numbers | **no** — adding can lower the sum | ❌ prefix sums (topic 04); LC 862 needs a monotonic deque over prefix sums |
| "At most k distinct" / "at most k zeros" | yes | ✅ Shapes B, E |
| "**Exactly** k distinct" / "sum == goal" | **no** — a valid window contains invalid ones | ⚠️ only through `atMost − atMost` |
| Max − min ≤ limit | yes | ✅ Shape F with two deques |
| "Is a palindrome", "is sorted" | no aggregate can be updated in O(1) | ❌ not a window problem |

**LC 560 vs LC 209 is the fork to have ready.** "Subarray sum equals K" with negatives → prefix sums + a map,
O(n) but a different mechanism. "Shortest subarray with sum ≥ target" over positives → a window. The sign
constraint, not the wording, picks the tool.

### Where a window ends

| Symptom | Right tool |
|---|---|
| Values may be negative, aggregate is a sum | prefix sums + map (topic 04) |
| Subsequence, not subarray | <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> (topics 16/17) |
| Sorted array, want a pair | converging two pointers (topic 02) |
| k-th largest / median across the window | heaps with lazy deletion (topic 12) |
| Many arbitrary ranges queried later | prefix sums / segment tree (topics 04, 26) |

---
<!-- /block:03_go_2_legality -->

<!-- block:03_go_3_variations -->
## Part 9 · Variations, Go Traps and Follow-ups

### Two monotonic deques: `max − min ≤ limit` (LC 1438)

The validity test needs the window's max **and** min, and neither has an inverse, so keep one deque per
extreme. Each index enters and leaves each deque once, so it is still O(n):

```go
func longestSubarray(nums []int, limit int) int {
    maxq := make([]int, len(nums))              // indices, values decreasing
    minq := make([]int, len(nums))              // indices, values increasing
    mh, mt, nh, nt := 0, 0, 0, 0                // head/tail cursors, as in Part 2.3
    l, best := 0, 0
    for r, x := range nums {
        for mh < mt && nums[maxq[mt-1]] <= x { mt-- }
        maxq[mt] = r; mt++
        for nh < nt && nums[minq[nt-1]] >= x { nt-- }
        minq[nt] = r; nt++
        for nums[maxq[mh]]-nums[minq[nh]] > limit {   // invalid: shrink
            l++
            if maxq[mh] < l { mh++ }
            if minq[nh] < l { nh++ }
        }
        best = max(best, r-l+1)
    }
    return best     // [8 2 4 7],4 -> 2    [10 1 2 4 7 2],5 -> 4    [4 2 2 2 4 4 2 2],0 -> 3
}
```

### "At most K distinct" over bytes (LC 340)

```go
func longestKDistinct(s string, k int) int {
    var cnt [256]int
    distinct, l, best := 0, 0, 0
    for r := 0; r < len(s); r++ {
        if cnt[s[r]] == 0 { distinct++ }
        cnt[s[r]]++
        for distinct > k {
            cnt[s[l]]--
            if cnt[s[l]] == 0 { distinct-- }
            l++
        }
        best = max(best, r-l+1)
    }
    return best     // ("eceba", 2) -> 3
}
```

With an array, keep the distinct count in its own integer (an array has no `len` of non-zero entries); with a
map, `len(cnt)` plus `delete` on zero does the same job.

### Go traps in this topic

| Trap | What happens | The fix |
|---|---|---|
| `s[l:r+1]` inside the loop to "look at the window" | O(1) to make, but iterating it to recompute a sum or count makes the loop O(n·k). | Maintain the state by ±1; use `s[l:r+1]` only at the end to return the text. |
| `math.MaxInt` minus/plus something | Wraps to a huge negative/positive with no panic. | Compare against the sentinel; do not do arithmetic on it. |
| A `[128]int` window over non-ASCII text | `index out of range` panic on any byte ≥ 128. | `[256]int` over bytes, or `map[rune]int` over `[]rune(s)`. |
| `map[int]int` window with `len(cnt)` as the distinct count | Forgetting `delete` on zero leaves stale keys, so `len` never falls. | `if cnt[y] == 0 { delete(cnt, y) }`. |
| `l := 0` written *inside* the loop body | The left pointer resets to 0 on every iteration — the window silently becomes O(n²). | Declare `l` once, before the `for r` loop; `l` only ever moves forward. |
| Sizing the deque `make([]int, k)` | A cursor deque needs room for every index pushed *in total*, not just the live ones. | `make([]int, n)`. |

### Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "It is a stream." | Windows are single-pass already; keep the state plus the last `k` items. |
| "Values can be negative." | Stop — prefix sums + map (topic 04), or a monotonic deque over prefix sums for the shortest case (LC 862). |
| "Return the window, not the length." | Record `bestL`; return `s[bestL:bestL+bestLen]` once at the end (a substring is a free header). |
| "`k` larger than the slice." | Decide up front: return `0`/`nil`; check before priming the first window. |
| "The window wraps around." | Scan `slices.Concat(nums, nums[:k-1])` (Go 1.22+) with a fixed window. |
| "Median of every window." | Two heaps with lazy deletion (topic 12); a deque cannot hold an order statistic. |
| "Concurrent producers." | The window state is shared mutable data — guard it with a mutex or funnel updates through one goroutine. |

---
<!-- /block:03_go_3_variations -->

<!-- problem-map:start -->
## Part 10 · Every Problem in This Topic, by Pattern

Fifteen problems, six window shapes — the Python guide's map with the Go spelling and the Go-only traps. Topic 03's solutions are Python-first; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Best Time to Buy and Sell Stock](GoDSA/03_sliding_window/001_best_time_to_buy_and_sell_stock/solution.go) <br>LC 121 · Easy | The degenerate window | One pass carrying `minPrice`; `best = max(best, p - minPrice)` (the `max`/`min` builtins, Go 1.21+). **Trap:** `max(prices) - min(prices)` ignores that the buy comes first; seeding with `math.MinInt` and returning it on a falling slice (the answer is 0). |
| [002 · Maximum Average Subarray I](GoDSA/03_sliding_window/002_maximum_average_subarray_i/solution.go) <br>LC 643 · Easy | Shape A · fixed | `total += nums[r] - nums[r-k]` after priming; `float64(best) / float64(k)` at the end. **Trap:** an inner loop summing `nums[i:i+k]` — O(nk) that looks like O(n); integer division by `k` instead of a float divide. |
| [003 · Maximum Number of Vowels in a Substring of Given Length](GoDSA/03_sliding_window/003_maximum_number_of_vowels_in_a_substring/solution.go) <br>LC 1456 · Medium | Shape A · predicate count | A `[256]bool` (or a `switch`) for "is a vowel" instead of a map; count on enter, decrement on leave. **Trap:** re-counting each window; `len(s)` counts bytes, fine for ASCII. |
| [004 · Contains Duplicate II](GoDSA/03_sliding_window/004_contains_duplicate_ii/solution.go) <br>LC 219 · Easy | Shape A · over a set | A `map[int]struct{}` of the previous `k` values; check *before* inserting. **Trap:** evicting `nums[r-k]` instead of `nums[r-k-1]`; testing after inserting. |
| [005 · Longest Substring Without Repeating Characters](GoDSA/03_sliding_window/005_longest_substring_without_repeating_characters/solution.go) <br>LC 3 · Medium | Shape B · longest | `var last [128]int` seeded with `-1`, and `if last[c] >= l { l = last[c] + 1 }`. **Trap:** `last[c] != -1` instead of `>= l` moves `l` backwards (`"abba"`); `r - l` instead of `r - l + 1`. |
| [006 · Max Consecutive Ones III](GoDSA/03_sliding_window/006_max_consecutive_ones_iii/solution.go) <br>LC 1004 · Medium | Shape B/D · "at most k bad" | Longest subarray with at most `k` zeros — the flipping is a red herring. **Trap:** deciding *which* zeros to flip; `r - l` off by one. |
| [007 · Longest Repeating Character Replacement](GoDSA/03_sliding_window/007_longest_repeating_character_replacement/solution.go) <br>LC 424 · Medium | Shape D · never shrinks | `var count [26]int`; `maxFreq` is a *count*; on invalid slide by one; return `len(s) - l`. **Trap:** tracking the letter's identity; recomputing an honest max inside a `for` shrink and returning the wrong final width. |
| [008 · Minimum Size Subarray Sum](GoDSA/03_sliding_window/008_minimum_size_subarray_sum/solution.go) <br>LC 209 · Medium | Shape C · shortest | Shrink *while valid*, record inside, `math.MaxInt` as the sentinel, return `0` if it never changed. **Trap:** `best := 0`; returning `math.MaxInt`; negative numbers break it entirely. |
| [009 · Fruit Into Baskets](GoDSA/03_sliding_window/009_fruit_into_baskets/solution.go) <br>LC 904 · Medium | Shape B · ≤ 2 distinct | `map[int]int` with `delete` on zero, or a `[N]int` plus a `distinct` counter. **Trap:** forgetting `delete`, so `len(cnt)` never falls (infinite shrink, then an index panic). |
| [010 · Permutation in String](GoDSA/03_sliding_window/010_permutation_in_string/solution.go) <br>LC 567 · Medium | Shape A + have/need | Two `[26]int` arrays and a `matches` counter, or compare the arrays directly with `==` (arrays are comparable!). **Trap:** `len(s1) > len(s2)` unchecked; never comparing the primed window. |
| [011 · Find All Anagrams in a String](GoDSA/03_sliding_window/011_find_all_anagrams_in_a_string/solution.go) <br>LC 438 · Medium | Shape A at every index | 010 with `out = append(out, r-k+1)` instead of `return true`. **Trap:** appending `r`; missing a match at index 0. |
| [012 · Binary Subarrays With Sum](GoDSA/03_sliding_window/012_binary_subarrays_with_sum/solution.go) <br>LC 930 · Medium | Shape E · counting | `atMost(g) - atMost(g-1)` with the `g < 0` guard; `count += r - l + 1`. **Trap:** no guard for `goal == 0`; trying one direct window for "sum == goal". |
| [013 · Subarrays with K Different Integers](GoDSA/03_sliding_window/013_subarrays_with_k_different_integers/solution.go) <br>LC 992 · Hard | Shape E · exactly K | `atMostKDistinct(k) - atMostKDistinct(k-1)` over a `map[int]int` with `delete` on zero. **Trap:** a direct "exactly k" window (it is a band, not a suffix). |
| [014 · Minimum Window Substring](GoDSA/03_sliding_window/014_minimum_window_substring/solution.go) <br>LC 76 · Hard | Shape C + have/need | `need`/`window` as `[128]int`, plus `formed`/`required` counters that change only when a count *crosses* its need. **Trap:** `>=` instead of `==` on the grow side (double-counts); a byte ≥ 128 panics the array index. |
| [015 · Sliding Window Maximum](GoDSA/03_sliding_window/015_sliding_window_maximum/solution.go) <br>LC 239 · Hard | Shape F · monotonic deque | A `[]int` of length `n` with `head`/`tail` cursors holding *indices*; pop-back while `nums[back] <= nums[r]`, pop-front when `<= r-k`. **Trap:** storing values, so duplicates evict the wrong copy; sizing the buffer `k` instead of `n`. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] State whether a problem is fixed-size or variable-size before coding
- [ ] Never re-slice-and-rescan to inspect window contents — maintain state incrementally
- [ ] Know whether to record the answer before or after the shrink loop, and why (max vs. min window)
- [ ] Explain why total work is O(n) despite a nested loop (each index enters/leaves once)
- [ ] Default to a `[128]int`/`[256]int` frequency array for ASCII; justify a map otherwise
- [ ] Explain why Go has no deque, and name the three ways to build one (slice re-slice, `container/list`, cursors over a preallocated slice)
- [ ] Explain the `s = s[1:]` caveat — O(1) per call, but the popped slot is retained and `cap` shrinks
- [ ] Implement the monotonic deque for LC 239 with head/tail cursors in under 15 minutes
- [ ] Implement Minimum Window Substring's `need`/`window`/`formed` pattern from scratch
- [ ] Use `lastSeen[c] >= l`, not `lastSeen[c] != -1`, to detect in-window duplicates
- [ ] Name the window shape (A–F) before writing any code <!--ca-->
- [ ] Say why a sum-based window breaks with negative numbers, and what replaces it <!--ca-->
- [ ] Write `atMost(g) − atMost(g−1)` with the `g < 0` guard, and say why "exactly" is not hereditary <!--ca-->
- [ ] Delete a map key when its count reaches zero, and explain what `len` would report otherwise <!--ca-->
- [ ] Use two monotonic deques when validity needs both the max and the min <!--ca-->
