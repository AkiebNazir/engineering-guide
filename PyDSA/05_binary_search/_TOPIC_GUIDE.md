# Topic 05 · Binary Search — Python Deep Dive

> Binary search answers one question: *"where does a monotone predicate flip
> from false to true?"* Precisely half the space is on each side of the flip,
> so testing the middle point and discarding a whole half is always safe.
> That is the entire algorithm. Everything else in this guide is: recognising
> when a monotone predicate exists, and getting the boundary arithmetic right
> once you've found it.

---

## Part 1 · The Mechanism

### 1.0 The invariant, stated precisely

Binary search does **not** require a sorted array. It requires a predicate
`f(x)` over an ordered space such that:

```arch
%% caption: Binary search finds where a monotone predicate flips from False to True. Each probe discards the half that cannot contain the flip.
grid 64x80
route straight
group fg "predicate is False" color=red
node a0 "F" at 0,0 in fg shape=circle color=red
node a1 "F" at 1,0 in fg shape=circle color=red
node a2 "F" at 2,0 in fg shape=circle color=red
node a3 "F" at 3,0 in fg shape=circle color=red
group tg "predicate is True" color=green
node a4 "T" at 7,0 in tg shape=circle color=green
node a5 "T" at 8,0 in tg shape=circle color=green
node a6 "T" at 9,0 in tg shape=circle color=green
a0 -- a1 -- a2 -- a3
a4 -- a5 -- a6
a3 ==> a4 : "flip: the first True is the answer"
```


```
f(x) = False, False, False, ..., False, True, True, ..., True
                                  ^
                                  the flip point — this is what we're finding
```

(or the mirror image, `True...True, False...False` — same idea, flip the
comparison.) A sorted array is simply the most common way to manufacture this
shape: `f(x) = (a[x] >= target)` is false for every index before the target
and true from the target onward, *because the array is sorted*. But the
predicate is the real object. If you can name `f`, prove it's monotone, and
evaluate it in O(1) (or better), binary search applies — whether or not
anything resembling a sorted array is in sight.

**Contrast with topic 04 (prefix sum):** prefix sum answers "have I seen this
exact value before?" — an O(1) hash lookup keyed on equality. Binary search
answers "where does this ordering relationship flip?" — an O(log n)
elimination keyed on comparison. Prefix sum needs a hashable key and no
particular order; binary search needs an *order* and no particular hashing.
They solve disjoint problem shapes: "does X exist" (hashmap) vs. "where is
the boundary between X and not-X" (binary search). If a problem asks "is
there a subarray with property P" reach for topic 04's hashmap move; if it
asks "what is the smallest/largest value such that P holds," reach for this
topic.

---

### 1.1 Two families — this is the decision that matters most

**Family A — search ON THE ARRAY (index space).** The array itself is
sorted (or one contiguous half of it is — §1.4). You are looking for a
specific value, or the insertion point for one, or a boundary between two
regions of the array. `lo`/`hi` are **array indices**. Problems 001–005,
007–008 live here.

```arch
%% caption: Two families: search on the array's indices, or search on the range of candidate answers.
grid 240x100
node q "What are lo and hi moving over?" at 0.5,0 shape=pill
node a "Indices of a sorted array" at 0,1
node b "Candidate answers" at 1,1 sub="speed, capacity, days ..."
node a1 "Family A: search ON the array" at 0,2 color=green sub="while lo ≤ hi, hi = mid - 1"
node b1 "Family B: search ON the answer" at 1,2 color=amber sub="while lo < hi, hi = mid"
node b2 "Needs feasible(x), monotone" at 1,3 sub="False ... False True ... True"
q:B -> a:T
q:B -> b:T
a -> a1
b -> b1 -> b2
```


**Family B — search ON THE ANSWER (value space).** There is no sorted array
in sight. Instead there's a candidate *answer* (a capacity, a speed, a
maximum subarray sum, a number) and a **feasibility predicate**
`feasible(x)` that is monotone in that candidate: "can I finish in D days if
I ship at rate x?", "can Koko eat all bananas within H hours at speed x?".
`lo`/`hi` bound the **answer's possible values**, not any array's indices.
Problems 006, 010, 011 live here.

**The decision test:** ask "what am I moving `lo`/`hi` over?" If the answer
is "positions in a given sequence," you're in Family A. If the answer is
"candidate values of the thing I'm trying to compute — and I have to
simulate/check each candidate to know if it works," you're in Family B. This
is the single most-missed skill in this topic: candidates who are fluent in
Family A often don't recognise Family B at all, because there's no array to
search "on." The array is *used inside* `feasible(x)`, not searched directly.

```python
# Family A — search on the array
def search_array(a, target):
    lo, hi = 0, len(a) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if a[mid] == target:
            return mid
        elif a[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

# Family B — search on the answer
def search_answer(lo, hi, feasible):
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid          # mid might be the answer; keep it in range
        else:
            lo = mid + 1      # mid is too small/weak; rule it out
    return lo                 # lo == hi == the smallest x with feasible(x) == True
```

Family B's template is worth memorising verbatim: `while lo < hi`, `hi = mid`
(never `mid - 1`, because `mid` itself might be the answer and we must not
discard it), `lo = mid + 1` (mid has been proven infeasible, safe to
discard). This is the "find the leftmost True" shape, and it is what 006,
010, and 011 all reduce to once you've written `feasible(x)`.

---

### 1.2 The off-by-one minefield

This topic has more ways to write an infinite loop or an off-by-one than any
other in the curriculum. Four independent choices, and mixing the wrong pair
is the most common bug:

**(a) `lo <= hi` vs. `lo < hi`.**

- `while lo <= hi:` — used when you're searching for an EXACT match and are
  willing to end with "not found" (`lo > hi`, empty range). Standard for
  Family A exact-value search (001, 005).
- `while lo < hi:` — used when you're narrowing to a single boundary index
  that is GUARANTEED to exist in `[lo, hi]` (e.g., "the smallest index
  where X becomes true" — 002's insertion point, 003, 004, 006, 007, 010,
  011). The loop ends with `lo == hi`, and that value IS the answer — no
  separate "not found" case to handle.

Mixing these up is the #1 bug: using `lo < hi` with `hi = mid - 1` can skip
past the answer entirely, and using `lo <= hi` for a boundary search can
leave `lo` and `hi` crossing at the wrong point with no clean single answer.

**(b) `mid = (lo + hi) // 2` — the classic C/Java overflow, why Python
doesn't have it, and why it's still worth saying out loud.** In Java, C++,
or Go with fixed-width 32-bit integers, `lo + hi` can overflow when both are
near `INT_MAX`, silently wrapping to a negative number and corrupting `mid`.
The idiomatic fix there is `mid = lo + (hi - lo) // 2`, which never adds two
large numbers together. **Python ints are arbitrary-precision — this
overflow cannot happen here**, so `(lo + hi) // 2` is completely safe in
Python. Say this explicitly in an interview if you have C/Java background:
it demonstrates you know *why* the idiom exists, not just that it exists,
and that you know when it's genuinely unnecessary rather than cargo-culting
it everywhere.

**(c) `hi = mid - 1` vs. `hi = mid`.** This follows directly from whether
`mid` has been *proven wrong* or merely *not yet proven necessary*:

- If `a[mid]` has been conclusively ruled out (e.g., `a[mid] < target`, or
  `a[mid] == target` and you've already recorded/returned it), shrink past
  it: `hi = mid - 1` or `lo = mid + 1`.
- If `mid` might still BE the answer (e.g., `feasible(mid)` is true and you
  want the smallest feasible value — mid could be it, or something smaller
  could also work), keep it in range: `hi = mid`.

Using `hi = mid - 1` when `mid` could still be the answer is the classic way
to skip past the correct result; using `hi = mid` when `mid` has been fully
ruled out is the classic way to infinite-loop (see next point).

**(d) Infinite-loop traps.** With `while lo < hi` and *integer* division,
`mid = (lo + hi) // 2` **rounds down**. If your shrink step ever produces
`hi = mid` while `lo` stays where it is, and `mid` can equal `lo` (which
happens whenever `hi == lo + 1`), the loop never progresses:

```
lo=3, hi=4 -> mid = 3 (rounds down) -> if you do hi = mid, hi becomes 3 too
                                        -> lo=3, hi=3 -> loop exits, FINE
             but if the branch that should shrink lo does hi = mid instead
             of lo = mid + 1, you get lo=3, hi=3 forever on the WRONG branch
```

The rule that prevents this: whichever branch is supposed to move `lo`
**must** use `lo = mid + 1` (never `lo = mid`, or `lo` can freeze when
`mid == lo`). The branch that keeps `mid` in range uses `hi = mid` (never
`hi = mid - 1`, or you can skip the true answer). Getting this pairing
backwards is the #1 source of infinite loops in Family B code.

---

### 1.3 Search insert position and the "leftmost True" generalisation

LC 35 (002) — "find the index to insert `target` to keep the array sorted"
— is `bisect_left` under a different name: the smallest index `i` such that
`a[i] >= target`. Once you see this as "find the leftmost index where the
predicate `a[i] >= target` is true," it stops being a special case and
becomes the same `while lo < hi: ... hi = mid` template as everything else
in Family B, just with `f(x) = (a[x] >= target)` as the predicate and the
array itself supplying the ordering. Python's `bisect` module implements
exactly this template in C — `bisect.bisect_left(a, target)` returns the
same index — and knowing that connection is worth stating even when you
write it by hand for the interview.

---

### 1.4 Rotated sorted arrays — "one half is always sorted"

A rotated sorted array (007, 008) is not globally sorted, so `a[mid]`
compared to `target` alone tells you nothing. But it has a weaker, still
useful structure: **cut it at any point, and at least one of the two
resulting halves is a normal ascending sorted run.**

```arch
%% caption: One half is always sorted. Decide which, ask whether the target lies inside it, and discard the other half.
grid 170x100
node m "mid = (lo + hi) // 2" at 1,0 shape=pill
node f "a[mid] ==\ntarget?" at 1,1 shape=diamond color=amber
node r "return mid" at 2,1 color=green
node l "Left half\nsorted?" at 1,2 shape=diamond color=amber sub="a[lo] ≤ a[mid]"
node l2 "Target\ninside?" at 0,3 shape=diamond color=amber sub="a[lo] .. a[mid]"
node r2 "Target\ninside?" at 2,3 shape=diamond color=amber sub="a[mid] .. a[hi]"
node h1 "hi = mid - 1" at 0,4
node h2 "lo = mid + 1" at 1,4
node h3 "lo = mid + 1" at 2,4
node h4 "hi = mid - 1" at 3,4
m -> f
f -> r : "yes"
f -> l : "no"
l:L -> l2:T : "yes"
l:R -> r2:T : "no: right half is sorted"
l2 -> h1 : "yes"
l2:R -> h2:T : "no"
r2 -> h3 : "yes"
r2:R -> h4:T : "no"
```


```
a = [4, 5, 6, 7, 0, 1, 2]
         lo      mid         hi
      a[lo]=4  a[mid]=7   a[hi]=2

a[lo] <= a[mid]  (4 <= 7)  ->  the LEFT half [lo..mid] is sorted normally
```

The algorithm at every step: compute `mid`, then ask "is the left half
`[lo..mid]` sorted?" by checking `a[lo] <= a[mid]`.

- If yes, the left half is a clean ascending run. Check whether `target`
  falls inside `[a[lo], a[mid]]`; if so, search there (`hi = mid - 1`),
  otherwise the target must be in the (messier) right half
  (`lo = mid + 1`).
- If no, the RIGHT half `[mid..hi]` must be the sorted one instead (a
  rotated array cut anywhere always has at least one sorted side — if the
  left one isn't, the right one is). Check whether `target` falls inside
  `[a[mid], a[hi]]`; if so, search there, otherwise go left.

This is still one O(log n) elimination per step — you're just choosing
*which* half to trust based on which one is provably ordered, rather than
assuming the whole array is ordered. LC 153 (find the minimum / rotation
point, 007) is the same idea specialised to "which half contains the
rotation point" instead of "which half contains the target."

⚠️ Duplicates (a LC 154 variant, not in this folder but worth knowing)
break the `a[lo] <= a[mid]` test: `[1,1,1,0,1]` has `a[lo] == a[mid] == 1`
but the array is still rotated. The fix there is to fall back to a linear
step (`lo += 1`) when `a[lo] == a[mid] == a[hi]`, which costs the O(log n)
guarantee in the worst case (all-duplicate arrays degrade to O(n)) — worth
mentioning as a follow-up even though 007/008 in this folder guarantee
distinct values.

---

### 1.5 Binary search on a 2D matrix

LC 74 (005) gives a matrix where each row is sorted and each row's first
element is greater than the previous row's last element — meaning **the
whole matrix is one sorted sequence, wrapped**. Two equally valid moves:

**(a) Treat it as 1D via index math.** A single binary search over
`[0, rows*cols - 1]`, converting a flat index `k` to `(k // cols, k % cols)`
on each comparison:

```python
lo, hi = 0, rows * cols - 1
while lo <= hi:
    mid = (lo + hi) // 2
    r, c = divmod(mid, cols)
    if matrix[r][c] == target: return True
    elif matrix[r][c] < target: lo = mid + 1
    else: hi = mid - 1
```

**(b) Two binary searches.** First binary-search the row (find the last row
whose first element is `<= target`), then binary-search within that row.
Same O(log(rows) + log(cols)) = O(log(rows*cols)) complexity, more code,
but generalises better to matrices that are only row-sorted (not the
fully-flattenable LC 74 shape) — that variant is LC 240, which genuinely
needs a different technique (staircase search from a corner) because it
lacks the flattening property.

---

### 1.6 The interactive-oracle pattern

Three problems here (003, 004, 009) hand you a **black-box query** instead
of a plain array — the array either doesn't exist explicitly, or you're
told to minimise calls to some external checker. The binary search mechanism
is unchanged; what changes is that `f(mid)` is a function call with a cost,
not a free array read.

- **003 (First Bad Version)** — `isBadVersion(v)` is the predicate directly:
  false for good versions, true from the first bad version onward. Textbook
  Family B, `feasible = isBadVersion`.
- **004 (Guess Number Higher or Lower)** — `guess(num)` returns -1/0/1
  instead of a boolean, but it's the same monotone comparison in disguise:
  collapse it to a predicate (`guess(mid) <= 0`, say) and it's 003 again.
- **009 (Time Based Key-Value Store)** — no oracle function, but the
  operations reduce to `bisect` over a list that is sorted by construction
  (timestamps only ever append in increasing order per key, per the
  problem's guarantee) — "find the largest timestamp `<= t`" is
  `bisect_right(...) - 1`, another leftmost/rightmost-boundary search.

The lesson: recognising "this is binary search" does not require seeing an
array at all. It requires recognising a monotone yes/no (or three-way)
question and a way to ask it, whatever form that takes.

---

## Part 2 · Pattern Decision Tree

```
1. Is there an explicit sorted array (or a matrix flattenable to one) and
   I'm looking for a specific value, an insertion point, or a boundary
   between two regions OF THAT ARRAY?
       YES -> Family A, search on the array (§1.1). Index-space lo/hi.
       NO  -> continue.

2. Is the array "sorted with a twist" — rotated, or otherwise not globally
   ordered but with a locally-ordered half at every cut?
       YES -> §1.4: determine which half is the clean ascending run at each
              step, search there or the other half based on where target falls.
       NO  -> continue.

3. Am I trying to find the smallest (or largest) value X such that some
   condition feasible(X) holds, where feasible(X) requires simulating or
   computing something (not just an array lookup) — and feasible is
   monotone in X (true for all X >= some threshold, or the reverse)?
       YES -> Family B, search on the answer (§1.1). lo/hi bound the ANSWER's
              range, not array indices. Write feasible(x) first, prove it's
              monotone out loud, then binary search on it.
       NO  -> continue.

4. Is the "array" actually a black-box oracle (a query function, an API,
   an interactive judge) rather than a materialised list?
       YES -> §1.6. Same mechanism; f(mid) costs a call instead of an
              array read. Minimising the CALL COUNT is often the actual ask.
       NO  -> probably not this topic — check topic 04 (do I need "have I
              seen this value," not "where's the boundary") or topic 02
              (converging two pointers on a value-pair question).

5. Once the family is chosen, lock these four decisions together (§1.2):
       loop condition   lo <= hi  (exact match, may not exist)
                      or lo <  hi  (boundary guaranteed to exist in range)
       shrink-right     hi = mid - 1  (mid ruled out)
                      or hi = mid      (mid might still be the answer)
       shrink-left      lo = mid + 1  (ALWAYS, when lo needs to move —
                                        never lo = mid, or it can freeze)
       mid formula      (lo + hi) // 2 is safe in Python (§1.2b) — no
                         overflow guard needed, unlike Java/C/Go.
```

---

## Part 3 · Complexity Reference for This Topic

| Operation | Cost | Note |
|---|---|---|
| Binary search, array of size n | O(log n) | halves the space each step |
| Linear scan, array of size n | O(n) | the baseline every problem here beats |
| `feasible(x)` evaluation (Family B) | varies | often O(n) itself — total cost is O(n log(range)) |
| Binary search on the answer, range R | O(log R) calls to `feasible` | total: O(log R · cost(feasible)) |
| Rotated-array search (007/008) | O(log n) | same as plain, one extra comparison per step |
| 2D matrix search, flattened (005) | O(log(rows·cols)) | one search over the flat index space |
| `bisect.bisect_left` / `bisect_right` | O(log n) | C-implemented; use it once you can write it by hand |
| Median of two sorted arrays (012) | O(log(min(m, n))) | binary search over the SMALLER array's partition point |

Space is **O(1)** for every problem in this folder — binary search's other
selling point besides speed: no auxiliary structure, just a few integers.

---

## Part 4 · Common Mistakes Across This Topic

1. Reaching for binary search on an unsorted, non-monotone array "because
   it's fast" — there is no valid mid-point elimination without a monotone
   predicate. Confirm the predicate exists before writing the loop.
2. Confusing Family A and Family B — writing `lo, hi = 0, len(a) - 1` for a
   Family B problem (searching the answer) instead of `lo, hi = min_answer,
   max_answer`. The array is an *input to* `feasible(x)`, not the search
   space itself, in Family B.
3. Mismatched loop condition / shrink pair (§1.2): `while lo < hi` combined
   with `hi = mid - 1`, or `while lo <= hi` combined with `hi = mid` — both
   produce either an infinite loop or a skipped answer.
4. `lo = mid` instead of `lo = mid + 1` in a `while lo < hi` loop — freezes
   when `mid == lo` (always possible with floor division), infinite loop.
5. In rotated-array search, checking `a[lo] < a[mid]` to decide "is the left
   half sorted" without also handling `a[lo] == a[mid]` (fine when values
   are guaranteed distinct, as in 007/008, but a real bug the moment
   duplicates are allowed — see §1.4's note).
6. In Family B, not proving monotonicity of `feasible(x)` before searching.
   If capacity 5 is feasible, is capacity 6 also feasible? If you can't
   answer that in one sentence, you don't yet have a valid binary search.
7. Off-by-one in the final answer: returning `lo` when the problem wants
   `lo - 1` (or vice versa) because the loop's post-condition wasn't traced
   carefully. Always state what `lo == hi` MEANS before returning it.
8. In C/Java/Go, `(lo + hi) / 2` overflow — not a Python bug (§1.2b), but
   worth naming as a "this doesn't apply here, and here's why" if asked.
9. For the oracle pattern (003/004/009), writing a linear scan against the
   oracle instead of binary search — technically correct, but throws away
   the entire point when minimising query count is the ask.
10. For 012 (median of two arrays), attempting to literally merge the two
    arrays (O(m+n) or O((m+n)log(m+n)) if sorting is involved) when
    O(log(min(m,n))) is achievable and is what the interviewer is testing.

---

## Part 5 · The Progression in This Folder

```
  001  LC 704   Binary Search                        the mechanism, bare
  002  LC 35    Search Insert Position                leftmost True, bisect_left (§1.3)
  003  LC 278   First Bad Version                     oracle pattern (§1.6)
  004  LC 374   Guess Number Higher/Lower              oracle pattern, 3-way collapsed to 2-way
  005  LC 74    Search a 2D Matrix                    flatten-to-1D or two searches (§1.5)
  006  LC 875   Koko Eating Bananas                   Family B debut: search the answer (§1.1)
  007  LC 153   Find Minimum in Rotated Sorted Array   "one half is sorted" (§1.4), find the pivot
  008  LC 33    Search in Rotated Sorted Array         §1.4 applied to finding a target, not the pivot
  009  LC 981   Time Based Key-Value Store             bisect over a naturally sorted-by-time list
  010  LC 1011  Capacity To Ship Packages Within D Days Family B, feasible() simulates the ship
  011  LC 410   Split Array Largest Sum               Family B, feasible() simulates the split
  012  LC 4     Median of Two Sorted Arrays           partition search, O(log(min(m,n))), the boss
```

001 → 005 build Family A fluency and the oracle variant. 006 is the pivot of
the whole topic — 010 and 011 are 006's `feasible()` template applied to a
different simulation. 007/008 are one trick (which half is sorted) applied
twice. 012 is the hardest problem in the folder and deserves the most time.

---

<!-- block:05_py_1_shapes -->
## Part 6 · Shapes the Two Families Do Not Spell Out

Family A (search *on* the array) and Family B (search *on* the answer) cover the folder. Interviews reuse
them in shapes worth naming — including the one template Part 1 does not show: the **rightmost True**. Every
snippet was run against LeetCode's own examples while writing this section.

```arch
%% caption: Three boundary templates. The only differences are which side keeps mid and which mid you compute — get the pairing wrong and the loop never ends.
grid 250x140
node q "Find a boundary in a monotone predicate" at 1,0 shape=pill
node a "Which boundary?" at 1,1 shape=diamond color=amber
node l "lo = 0, hi = n" at 0,2 color=green w=220 sub="mid = (lo + hi) // 2 (LOWER mid). If ok(mid): hi = mid, else: lo = mid + 1"
node r "lo = 0, hi = n" at 1,2 color=amber w=220 sub="mid = (lo + hi + 1) // 2 (UPPER mid). If ok(mid): lo = mid, else: hi = mid - 1"
node e "lo = 0, hi = n - 1" at 2,2 color=green w=220 sub="while lo <= hi, mid ± 1 on both sides"
q -> a
a:L -> l:T : "leftmost True (smallest x that works)"
a:B -> r:T : "rightmost True (largest x that works)"
a:R -> e:T : "exact match, or 'is it there?'"
```

### 6.1 Both edges of a run of duplicates (LC 34)

The first and last position of `target` are the two boundaries `bisect_left` and `bisect_right − 1`. The
*count* of a value is their difference — O(log n) instead of a scan:

```python
def search_range(nums, target):
    lo = bisect_left(nums, target)
    if lo == len(nums) or nums[lo] != target:      # absent — the guard matters
        return [-1, -1]
    return [lo, bisect_right(nums, target) - 1]
# [5,7,7,8,8,10], 8 -> [3, 4]     [5,7,7,8,8,10], 6 -> [-1, -1]     [], 0 -> [-1, -1]
```

### 6.2 Rightmost True: the upper-mid rule (Sqrt, "maximise the minimum")

When you want the **largest** `x` that still works, the loop keeps `mid` on a *success* (`lo = mid`). With a
lower mid that never advances: `lo = 3, hi = 4 → mid = 3 → lo = 3` forever. The fix is one character —
round **up**: `mid = (lo + hi + 1) // 2`.

```python
def my_sqrt(x):                       # largest r with r*r <= x
    lo, hi = 0, x
    while lo < hi:
        mid = (lo + hi + 1) // 2      # UPPER mid, or `lo = mid` loops forever
        if mid * mid <= x: lo = mid
        else:              hi = mid - 1
    return lo                         # 8 -> 2    4 -> 2    0 -> 0    10**12 -> 1_000_000
```

The same shape solves "maximise the minimum" problems (Magnetic Force Between Two Balls, Aggressive Cows): binary-
search the *distance* `d`, and `feasible(d)` greedily places items at least `d` apart. `[1,2,3,4,7]`, 3 balls → **3**.

```python
lo, hi = 1, position[-1] - position[0]
while lo < hi:
    mid = (lo + hi + 1) // 2
    if feasible(mid): lo = mid        # mid works — try a bigger gap
    else:             hi = mid - 1
```

### 6.3 Peak finding: a boundary without a globally monotone predicate (LC 162)

There is no sorted order, yet binary search works. Compare `nums[mid]` with its **right neighbour**: if it is
still rising, a peak must exist to the right (the array falls off the end, treated as `−∞`); otherwise a peak is
at `mid` or to its left. Either way the half you keep provably contains a peak.

```python
def find_peak(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] < nums[mid + 1]: lo = mid + 1     # rising: a peak lies right
        else:                          hi = mid          # falling: a peak is at mid or left
    return lo          # [1,2,3,1] -> 2     [1,2,1,3,5,6,4] -> 5 (1 is also valid)
```

The lesson: binary search needs a *safe half to discard*, not necessarily a sorted array.

### 6.4 A counting predicate (LC 378 — k-th smallest in a sorted matrix)

Binary-search the **value** range `[matrix[0][0], matrix[-1][-1]]`. The predicate is *"are there at least `k`
elements `<= mid`?"* — a monotone count, computed in O(n) by walking a staircase from the bottom-left corner. It
is Family B where `feasible` is a *count*, and it generalises to "k-th smallest pair distance" and "k-th smallest
prime fraction".

```python
def kth_smallest(matrix, k):
    n = len(matrix)
    def count_le(x):
        c, r, col = 0, n - 1, 0
        while r >= 0 and col < n:
            if matrix[r][col] <= x: c += r + 1; col += 1   # the whole column above is <= x too
            else:                   r -= 1
        return c
    lo, hi = matrix[0][0], matrix[-1][-1]
    while lo < hi:
        mid = (lo + hi) // 2
        if count_le(mid) >= k: hi = mid
        else:                  lo = mid + 1
    return lo          # [[1,5,9],[10,11,13],[12,13,15]], k=8 -> 13
```

O(n · log(range)). The answer is always an element of the matrix, because `lo` converges on the smallest value with
`count >= k`.

### 6.5 Duplicates in a rotated array (LC 154 / 81)

With duplicates, `nums[mid] == nums[hi]` is genuinely ambiguous, so you drop one element from the right and pay
O(n) in the worst case (e.g. all equal). State that cost out loud:

```python
def find_min_dups(nums):
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if   nums[mid] > nums[hi]: lo = mid + 1
        elif nums[mid] < nums[hi]: hi = mid
        else:                      hi -= 1             # ambiguous: shrink safely, lose the log guarantee
    return nums[lo]    # [2,2,2,0,1] -> 0     [3,1,3] -> 1     [1,1,1,1] -> 1
```

### 6.6 Unknown size (LC 702): gallop first

If you cannot ask for `len`, **double** the upper bound until it passes the target, then binary-search inside it.
Locating the bound costs O(log p) for a target at position `p`, so the whole search is O(log p) — *exponential
search*. Timsort's "galloping mode" (topic 01) is the same idea.

```python
hi = 1
while get(hi) < target: hi *= 2          # find a bound
lo = hi // 2                             # then an ordinary closed-interval search on [lo, hi]
```

### 6.7 The `bisect` module: what it hides

| Fact | Consequence |
|---|---|
| `bisect_left` / `bisect_right` are the lower / upper bound | A sorted-by-construction list (LC 981) needs no extra structure. |
| `bisect.insort` is O(log n) to *find* but **O(n) to insert** | A list shifts its tail. Do not build a "sorted set" this way for large `n`; use a heap, a balanced tree, or `sortedcontainers` (third-party). |
| `key=` (Python 3.10+) | `bisect_left(rows, "b", key=lambda r: r[0])` searches records without a parallel key list. `key` is applied to the *elements*, not to the target. |
| No check that the input is sorted | On unsorted data it returns a plausible-looking wrong index, silently. |
| Real-valued search | Prefer a fixed iteration count (`for _ in range(100)`) to `hi - lo > eps`: an epsilon that suits every magnitude is hard, and the loop can stall on float rounding. |

### 6.8 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Why is this O(log n)?" | Each probe discards half the candidates; the count halves from `n` to `1` in `log₂ n` steps. |
| "It is a linked list." | No O(1) index — reaching the middle costs O(n) each time. Convert to an array, or use a skip list / balanced tree. |
| "Duplicates?" | Decide what you return (first? last? any?), then use the matching bound template. Rotated arrays lose the log guarantee. |
| "Real numbers." | Fixed iterations; state the precision the problem asks for. |
| "The array is huge / on disk." | Binary search touches `log n` pages — the reason B-trees exist; cache the top levels. |
| "Many searches on changing data." | A static array wants binary search; a changing set wants a balanced tree or heap. |

---
<!-- /block:05_py_1_shapes -->

<!-- problem-map:start -->
## Part 7 · Every Problem in This Topic, by Pattern

Twelve problems in three groups — Family A (search on the array: 001–005, 007–009), Family B (search on the answer: 006, 010, 011) and one partition search (012). Each **Trap** is one the tests in that problem's solution file actually trigger.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Binary Search](PyDSA/05_binary_search/001_binary_search_solution.py) <br>LC 704 · Easy | Family A · exact match | Sorted, so comparing `a[mid]` with the target discards half; closed interval `[lo, hi]`. **Trap:** `while lo < hi` silently drops the last candidate; `hi = mid` instead of `mid - 1` loops forever. |
| [002 · Search Insert Position](PyDSA/05_binary_search/002_search_insert_position_solution.py) <br>LC 35 · Easy | Leftmost True (lower bound) | "Where does target go?" is the smallest `i` with `a[i] >= target` — `bisect_left` — over the half-open range `[0, n]`. **Trap:** `hi = n - 1` makes "insert at the end" unreachable; `hi = mid - 1` throws away a `mid` that may be the answer. |
| [003 · First Bad Version](PyDSA/05_binary_search/003_first_bad_version_solution.py) <br>LC 278 · Easy | Oracle, boolean | There is no array: `isBadVersion(v)` *is* the monotone predicate — leftmost True over `1..n`. **Trap:** `lo = 0` (the <abbr title="Application Programming Interface">API</abbr> is 1-indexed); `hi = mid - 1` when the call returns True. |
| [004 · Guess Number Higher or Lower](PyDSA/05_binary_search/004_guess_number_higher_or_lower_solution.py) <br>LC 374 · Easy | Oracle, three-way | Collapse `guess` to a boolean: `f(mid) = guess(mid) <= 0`, then leftmost True. **Trap:** `< 0` instead of `<= 0` — an exact match must fold into "go left or stay", not "too low". |
| [005 · Search a 2D Matrix](PyDSA/05_binary_search/005_search_a_2d_matrix_solution.py) <br>LC 74 · Medium | Virtual flat index | Rows chained end to start form one sorted sequence, so search `0 .. rows*cols - 1` and decode with `r, c = divmod(mid, cols)`. **Trap:** treating `mid` as a row or column; swapping `//` and `%` (transposes the matrix, fails only on non-square inputs). |
| [006 · Koko Eating Bananas](PyDSA/05_binary_search/006_koko_eating_bananas_solution.py) <br>LC 875 · Medium | Family B · answer space | Search speeds `1 .. max(piles)`; `feasible(k)` sums `ceil(p / k)` and compares with `h`. **Trap:** binary-searching *indices* of `piles` (there is no sorted array to search); floor division instead of ceiling. |
| [007 · Find Minimum in Rotated Sorted Array](PyDSA/05_binary_search/007_find_minimum_in_rotated_sorted_array_solution.py) <br>LC 153 · Medium | Rotated · find the pivot | Cut anywhere: one half is a clean ascending run. Compare `nums[mid]` with **`nums[hi]`** and keep the side that holds the minimum. **Trap:** comparing with `nums[lo]` (ambiguous); `hi = mid - 1` discards the minimum itself. |
| [008 · Search in Rotated Sorted Array](PyDSA/05_binary_search/008_search_in_rotated_sorted_array_solution.py) <br>LC 33 · Medium | Rotated · search a target | Decide *which half is sorted*, then whether the target lies in that half's value range. **Trap:** `<` vs `<=` at the range edges — `nums[lo]` and `nums[mid]` are real, checkable values. |
| [009 · Time Based Key-Value Store](PyDSA/05_binary_search/009_time_based_key_value_store_solution.py) <br>LC 981 · Medium | Bisect on a sorted-by-construction list | Timestamps strictly increase per key, so an appended list is already sorted; `bisect_right(...) - 1` finds the latest `<= t`. **Trap:** `bisect_left` (wrong on exact hits); forgetting the `idx < 0` guard — `values[-1]` silently returns the last element. |
| [010 · Capacity To Ship Packages Within D Days](PyDSA/05_binary_search/010_capacity_to_ship_packages_within_d_days_solution.py) <br>LC 1011 · Medium | Family B · capacity | Search capacity in `[max(weights), sum(weights)]`; `feasible(cap)` is a greedy day count. **Trap:** `lo = 1` (cannot hold the heaviest package); forgetting to count the final, partly loaded day. |
| [011 · Split Array Largest Sum](PyDSA/05_binary_search/011_split_array_largest_sum_solution.py) <br>LC 410 · Hard | Family B · minimise the maximum | The same skeleton for the third time: greedy packing under `cap`, `hi = sum(nums)`. **Trap:** `lo = 0/1` with an unguarded greedy (an element larger than `cap` breaks it); a "tighter" `hi = sum // k` returns **16 instead of 18** on `[7,2,5,10,8]`, `k=2`. |
| [012 · Median of Two Sorted Arrays](PyDSA/05_binary_search/012_median_of_two_sorted_arrays_solution.py) <br>LC 4 · Hard | Search a partition | Binary-search *where to cut the shorter array* so every left element is `<=` every right element; the median comes from the four border values. **Trap:** searching the longer array (a negative index is silently accepted); dropping the `±inf` sentinels. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] I can state the core invariant — monotone predicate, not "sorted
      array" — as the real requirement for binary search.
- [ ] I can explain, in one sentence, why prefix-sum-as-hashmap (topic 04)
      and binary search solve different-shaped questions.
- [ ] I can tell Family A from Family B in under 10 seconds by asking "what
      is lo/hi measuring — positions, or candidate answers?"
- [ ] I can write the Family B template (`while lo < hi: ... hi = mid ...
      lo = mid + 1`) from memory and explain why each shrink step is safe.
- [ ] I know which loop-condition/shrink-step pairing goes together and can
      name the two failure modes (infinite loop vs. skipped answer) of
      getting it backwards.
- [ ] I can explain why `(lo + hi) // 2` needs no overflow guard in Python
      but does in Java/C/Go.
- [ ] I can derive, from a picture, why one half of a rotated sorted array
      is always a clean ascending run, and how to detect which half.
- [ ] I can binary-search a fully-flattenable 2D matrix without materialising
      the flattened array.
- [ ] I recognise the interactive-oracle shape (a query function instead of
      an array) as still being binary search underneath.
- [ ] I can state the partition invariant for median-of-two-sorted-arrays
      (012) without looking it up.
</content>
- [ ] Write the rightmost-True template with the upper mid, and say why the lower mid never terminates <!--ca-->
- [ ] Get both edges of a run of duplicates from `bisect_left` and `bisect_right` <!--ca-->
- [ ] Explain why peak finding works with no sorted order (a safe half to discard) <!--ca-->
- [ ] Binary-search a value range with a *counting* predicate (k-th smallest in a matrix) <!--ca-->
- [ ] Say what changes with duplicates in a rotated array, and what `insort` really costs <!--ca-->
