# Topic 20 · Bit Manipulation — Go Deep Dive

> Python integers are arbitrary-precision — they never overflow, and `~x`, `<<`,
> and `>>` operate on a conceptually infinite two's-complement representation.
> Go integers are fixed-width hardware words. The bit tricks you're about to
> write are secretly relying on wraparound, sign-bit semantics, and shift rules
> that Python's model doesn't have. Get these wrong and the bug is silent —
> the code compiles, runs, and returns a plausible-looking wrong answer.

---

## Part 1 · Go's Bitwise Operators

### 1.1 The standard set, plus one Python doesn't have

```go
a & b     // AND
a | b     // OR
a ^ b     // XOR (binary) — also used as unary NOT, see below
a &^ b    // AND NOT ("bit clear") — Go-only, see 1.2
a << n    // left shift
a >> n    // right shift — signed vs unsigned differ, see Part 2
^a        // unary NOT (bitwise complement) — see Part 2
```

### 1.2 `&^` — the operator Python doesn't have

`a &^ b` clears every bit in `a` that is set in `b`. It's defined as
`a & (^b)`, but Go gives it its own token because "clear these bits" is common
enough to deserve one:

```go
flags := 0b1111
mask  := 0b0101
flags &^= mask        // flags = 0b1010 — bits 0 and 2 cleared, others untouched
```

Python has no equivalent operator — you write `a & ~b`, and because Python's
`~b` is `-b-1` over infinite-precision integers (not a fixed-width flip), you
must additionally mask the result to the bit width you actually care about or
stray high-order bits creep in:

```python
a & ~b            # in Python, ~b is negative and infinite in bit-width
a & ~b & 0xFF     # you must mask explicitly to stay in an 8-bit window
```

In Go, `a &^ b` on a fixed-width type never has that problem — the width is
baked into the type, so there's nothing to mask.

> ✅ Reach for `&^` any time you're clearing a known set of flag bits. It reads
> as "a, but without b" — clearer than `a & ^b` in a code review.

---

## Part 2 · Fixed-Width Two's Complement — Where Go and Python Really Diverge

This is the central mental-model shift for this topic. Everything below follows
from one fact: **Go's `int`, `int32`, `int64`, etc. are fixed-width two's-complement
words that wrap on overflow. Python's `int` is arbitrary-precision and never
wraps.**

### 2.1 Left shift overflow

```go
var x int64 = 1
y := x << 63          // y == math.MinInt64  (-9223372036854775808)
```

Shifting a `1` into the sign bit of a signed 64-bit integer doesn't error and
doesn't grow the type — it silently becomes the most negative representable
value. This is the same wraparound behavior flagged in Topic 01 Part 3
(`left + (right-left)/2` vs `(left+right)/2`), now showing up for shifts
instead of addition.

```python
y = 1 << 63           # 9223372036854775808 — a perfectly normal positive int
```

Python just grows the integer. There is no wraparound to reason about, no
"which type width am I in" question. Porting a shift-heavy algorithm from
Python to Go without checking type widths is a common source of silent bugs.

### 2.2 Unary `^` is two's-complement flip, not `-x-1`-over-infinity

```go
var x int8 = 5        // 0000 0101
y := ^x               // 1111 1010  == -6 (int8)
```

`^x` flips every bit. On a signed type, per two's complement, flipping all
bits of `x` gives you `-x - 1` — so `^5 == -6` — but the *reason* is bit-flip
semantics inside a fixed 8 (or 32, or 64) bit register, not an abstract
arithmetic identity:

```
 5 = 0000 0101
^5 = 1111 1010  (invert every bit)
   = -6 in two's complement (sign bit set, magnitude = ~(-6)+1 = 6)
```

Python's `~x` is *defined* as `-x - 1` directly, over infinite-precision
integers — `~5 == -6` there too, so the *result* often matches, but the
*mechanism* doesn't, and the mismatch becomes visible the instant you're
working with an unsigned type (`^uint8(5) == 250`, not `-6`) — Go's `^` flips
within whatever width the type declares, Python has no unsigned-width concept
to flip within at all.

> ⚠️ `^x` on an unsigned Go type is NOT negative — it's "all bits set, minus
> `x`," which for `uint8` means `255 - x`. Mixing this up with the signed case
> is a real, easy-to-make mistake.

### 2.3 Signed vs. unsigned right shift — same operator, different hardware instruction

Go has **one** right-shift operator, `>>`, and its behavior is entirely
determined by the *declared type* of the left operand:

- On a **signed** type: **arithmetic shift** — fills the vacated high bits
  with copies of the sign bit (sign-extends). Negative numbers stay negative.
- On an **unsigned** type: **logical shift** — fills the vacated high bits
  with zero.

```go
var s int8  = -8        // 1111 1000
fmt.Println(s >> 1)     // -4   (1111 1100 — sign bit copied in)

var u uint8 = 248        // 1111 1000  (same bit pattern as -8 above)
fmt.Println(u >> 1)      // 124  (0111 1100 — zero-filled)
```

Same bit pattern, same shift amount, opposite results — because the *type*
changed, not the operator. Java has `>>` (arithmetic) and `>>>` (logical) as
two distinct operators specifically to avoid this ambiguity; Go does not, so
you must track the variable's type in your head. This bites people who declare
a bitmask as `int` out of habit and then are surprised by sign-extension on
a right shift.

> ✅ If you're shifting something that represents unsigned data (a bitmask, a
> hash, a byte buffer) declare it `uint`/`uint32`/`uint64` explicitly rather
> than `int`, so `>>` does what you mean without a cast at every call site.

---

## Part 3 · `math/bits` — Hardware-Backed Bit Ops Python Doesn't Stdlib-Provide

```go
import "math/bits"

bits.OnesCount(uint(x))      // popcount — number of set bits; platform-width
bits.OnesCount32(x32)        // popcount for uint32
bits.OnesCount64(x64)        // popcount for uint64 — compiles to a single
                              //   POPCNT instruction on supporting hardware
bits.LeadingZeros64(x64)     // count of leading 0 bits (0 → 64)
bits.TrailingZeros64(x64)    // count of trailing 0 bits — position of the
                              //   lowest set bit; 0 → 64 for x64==0
bits.Len64(x64)              // number of bits needed to represent x64
                              //   (i.e. 1 + floor(log2(x64)), 0 for x64==0)
```

These compile to dedicated <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> instructions where the platform has them
(`POPCNT`, `BSF`/`TZCNT`, `BSR`/`LZCNT` on amd64) — O(1) in practice, not a
32-iteration software loop.

Python has **no stdlib equivalent**. The idiomatic Python popcount is
`bin(x).count('1')` (builds a string, then scans it — genuinely O(bit-width)
with real constant overhead) or a manual Brian Kernighan loop; Python 3.10
finally added `int.bit_count()`, but leading/trailing-zero counting still has
no direct stdlib function. This is one of the rare spots where Go's stdlib is
ahead of Python's.

> ⚡ Prefer `bits.OnesCount64` over a hand-rolled `for x != 0 { x &= x-1; c++ }`
> loop when you just need a popcount — it's both shorter and faster.

---

## Part 4 · Classic Bit Tricks

### 4.1 `x & (x-1)` — clear the lowest set bit

```
x   = 0110 1100
x-1 = 0110 1011
x&(x-1) = 0110 1000     ← lowest set bit (the 4s place) cleared
```

Subtracting 1 flips every bit from the lowest set bit downward (that bit
becomes 0, all the 0-bits below it become 1, due to borrow propagation).
ANDing with the original `x` keeps everything above that point identical and
zeroes everything at-or-below it. Two direct uses:

```go
// Brian Kernighan popcount: loop runs once per SET bit, not once per bit-width
func popcount(x uint) int {
    count := 0
    for x != 0 {
        x &= x - 1
        count++
    }
    return count
}

// Power-of-two check: a power of two has exactly one set bit, so clearing
// it must yield zero. x != 0 excludes the trivial x==0 case (which would
// otherwise pass x&(x-1)==0 without being a power of two).
func isPowerOfTwo(x int) bool {
    return x > 0 && x&(x-1) == 0
}
```

```arch
%% caption: n & (n-1) clears the lowest set bit. Repeat until n is 0 to count set bits, or test n & (n-1) == 0 for a power of two.
grid 200x80
node a "n = 1100" at 0,0 color=blue
node b "n - 1 = 1011" at 1,0 w=200 sub="the lowest 1 became 0, the bits below it flipped"
node c "n & (n - 1) = 1000" at 2,0 color=green w=170 sub="lowest set bit cleared"
a -> b -> c
```

### 4.2 `x & -x` — isolate the lowest set bit

```go
lowestBit := x & -x
```

`-x` in two's complement is `^x + 1` (flip every bit, add one). Flipping `x`
turns every bit *below* the lowest set bit into 1s and that bit itself into 0;
adding 1 then carries through those 1s, flipping them back to 0 and setting
that original bit back to 1 — everything *above* it ends up inverted relative
to `x`. ANDing `x` with `-x` therefore leaves only that one bit standing. This
is the mechanism a Fenwick tree (Topic 26) uses to find a node's parent/child
range, and it's the same isolate-lowest-bit idea whether or not you invoke
that name.

### 4.3 <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> cancellation — Single Number (LC 136)

<abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> is commutative, associative, `a ^ a == 0`, and `a ^ 0 == a`. <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> every
element of a slice together and every value that appears in a pair cancels
itself out, leaving only the one that appears alone:

```go
func singleNumber(nums []int) int {
    result := 0
    for _, n := range nums {
        result ^= n
    }
    return result
}
```

O(n) time, O(1) space — strictly better than a `map[int]int` frequency count,
and a favorite because it demonstrates you know <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>'s algebraic properties
rather than reaching for a hash map by default.

### 4.4 Bitmask enumeration — bridge to <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> (Topics 16 / 17)

```go
n := len(items)
for mask := 0; mask < 1<<n; mask++ {
    for i := 0; i < n; i++ {
        if mask&(1<<i) != 0 {
            // item i is included in this subset
        }
    }
}
```

Representing a subset of `n` items as the `n` low bits of an integer is the
standard trick behind bitmask <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> (traveling-salesman-style <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr>, "assign each
of n items to a bucket" problems). It only works because Go's fixed-width
`int` gives you exactly `n` addressable bits without a general-purpose
big-integer type getting in the way — and it caps out fast: `1<<n` overflows
a 64-bit `int` once `n` exceeds 63, so bitmask <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> is a technique for small `n`
(typically ≤ 20-ish given the `2^n` factor dominates runtime long before the
overflow limit does).

---

## Part 5 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Integer width | Arbitrary precision, never overflows | Fixed width (`int` is 64-bit on amd64/arm64); wraps silently |
| Left shift into sign bit | Grows the integer, stays positive | Wraps — can become the most negative value |
| Unary complement | `~x == -x-1`, infinite-precision | `^x` flips bits *within the type's width*; sign or magnitude depends on signed/unsigned |
| Right shift | Single behavior (ints are signed-only, arbitrary precision) | `>>` is arithmetic on signed types, logical on unsigned — same operator, type-dependent behavior |
| AND-NOT | No dedicated operator (`a & ~b`, must mask) | `&^` — dedicated, width-safe operator |
| Popcount | `bin(x).count('1')` or `int.bit_count()` (3.10+) | `bits.OnesCount64` — hardware `POPCNT` |
| Leading/trailing zero count | No stdlib function | `bits.LeadingZeros64` / `bits.TrailingZeros64` |
| Unsigned integer types | None (no concept of unsigned width) | `uint`, `uint8`...`uint64` — real distinct types with real wraparound rules |

---

## Part 6 · Algorithms Owned by This Topic

| Algorithm / Trick | Time | Space | Problem |
|---|:--:|:--:|---|
| <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> cancellation | O(n) | O(1) | LC 136 Single Number |
| Brian Kernighan popcount | O(popcount(x)) | O(1) | General bit-counting |
| `x & (x-1)` power-of-two check | O(1) | O(1) | LC 231 Power of Two |
| `x & -x` lowest-set-bit isolation | O(1) | O(1) | Fenwick tree indexing (Topic 26) |
| <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> via `x & (x-1)` recurrence | O(n) | O(n) | LC 338 Counting Bits |
| `math/bits` hardware popcount | O(1)* | O(1) | LC 191 Number of 1 Bits |
| Bitmask subset enumeration | O(2^n · n) | O(1) extra | Bitmask <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr>, subset-sum variants |

\* one hardware instruction on supporting platforms; O(w) in the worst
theoretical software-emulated case, where w is the word width

---

## Part 7 · Building It From Scratch

```go
package main

import "math/bits"

// LC 136 — Single Number: every element appears twice except one.
// XOR cancels pairs; the value left over is the answer.
func singleNumber(nums []int) int {
    result := 0
    for _, n := range nums {
        result ^= n
    }
    return result
}

// LC 338 — Counting Bits: dp[i] = popcount(i) for every i in [0, n].
// Key recurrence: i & (i-1) clears i's lowest set bit, producing a strictly
// smaller number whose popcount we've already computed — so
// popcount(i) == popcount(i & (i-1)) + 1 (the +1 accounts for the bit we
// just cleared). This turns an O(n log(maxVal)) naive solution into O(n).
func countBits(n int) []int {
    dp := make([]int, n+1)
    for i := 1; i <= n; i++ {
        dp[i] = dp[i&(i-1)] + 1
    }
    return dp
}

// isPowerOfTwo: a power of two has exactly one set bit. Clearing the lowest
// set bit of a power of two must yield 0. The x > 0 guard excludes 0 itself,
// which would otherwise satisfy x&(x-1)==0 without being a power of two.
func isPowerOfTwo(x int) bool {
    return x > 0 && x&(x-1) == 0
}

// popcountHW: prefer the hardware-backed math/bits version over a hand-rolled
// loop whenever you're not specifically demonstrating the Kernighan trick.
func popcountHW(x uint64) int {
    return bits.OnesCount64(x)
}
```

**Talk track while writing:** `countBits` is the one worth narrating slowly —
say out loud that `i & (i-1)` is "i with its lowest set bit cleared," that
this produces a value you've *already* computed `dp` for because it's smaller
than `i`, and that the whole <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> is just "one more bit than whatever's left
after removing my lowest bit." That's the difference between reciting a trick
and showing you understand why it's O(n).

---

<!-- block:20_go_1_problems -->
## Part 8 · The Ten Problems in Go — Fixed-Width Types Do the Masking for You

Parts 1–4 explain Go's operators and `math/bits`. This Part is the folder in Go, where the central difference from Python
is that **a fixed-width type wraps by itself** — so the "mask to 32 bits" ritual either disappears (if you use `int32`/`uint32`)
or moves to a different place (if you use the 64-bit `int`). All code below ran on Go 1.24.5 against LeetCode's own
examples; timings are measurements from this machine.

```arch
%% caption: A bitmask is a set of small integers. Add, remove, toggle and test are one operation each, and Go's &^ makes "remove" read naturally.
grid 200x70
node s "set {3, 5}" at 0,2 color=blue sub="mask = 0b101000"
node a "add x" at 1,0 color=green w=240 sub="mask |= 1 << x"
node r "remove x" at 1,1 color=amber w=240 sub="mask &^= 1 << x"
node t "toggle x" at 1,2 color=green w=240 sub="mask ^= 1 << x"
node c "contains x" at 1,3 color=green w=240 sub="mask>>x&1 == 1"
node u "set algebra" at 1,4 color=green w=240 sub="union |   intersection &   difference &^"
s:R -> a:L
s:R -> r:L
s:R -> t:L
s:R -> c:L
s:R -> u:L
```

### <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> and clear-the-lowest-bit: Single Number, Number of 1 Bits, Counting Bits, Missing Number

```go
x := 0
for _, n := range nums { x ^= n }                 // Single Number: pairs cancel in any order  -> [4 1 2 1 2] -> 4

bits.OnesCount32(n)                                // Number of 1 Bits: one POPCNT instruction  -> 11 -> 3, 128 -> 1, 2147483645 -> 30

ans := make([]int, n+1)                            // Counting Bits: length n+1 (indices 0..n INCLUSIVE)
for i := 1; i <= n; i++ { ans[i] = ans[i>>1] + i&1 }   // [0 1 1 2 1 2] for n = 5

x := len(nums)                                     // Missing Number: start the fold at n, not 0
for i, v := range nums { x ^= i ^ v }              // [3 0 1] -> 2
```

Go's precedence helps here: `&` binds tighter than `+` and `==`, so `ans[i>>1] + i&1` groups as `ans[i>>1] + (i&1)`
(unlike C, Java and JavaScript, where `==` binds tighter than `&`). Popcount, measured over 20 million random `uint32`s:
`bits.OnesCount32` **7 ms**, Kernighan's loop (`x &= x - 1`) **235 ms** (~34×), and `strings.Count(strconv.FormatUint(n, 2), "1")`
about **540 ms** (extrapolated from a 1M sample). Use the library call; keep Kernighan's for the "no library" follow-up.

### Reverse Bits and Reverse Integer

`bits.Reverse32(43261596)` is `964176192` in one call. The hand-rolled form places bit `i` at `31 - i` (placing it at `i` is a
no-op copy that still "runs"). **Reverse Integer** is a digit peel with an overflow check — and Go gives you two conveniences
Python does not: `%` keeps the dividend's sign, so **no `abs` and no sign restore** are needed, and you check the bound
*before* the multiply:

```go
d := x % 10; x /= 10                               // d is negative for a negative x — the sign takes care of itself
if rev > math.MaxInt32/10 || (rev == math.MaxInt32/10 && d > 7) ||
   rev < math.MinInt32/10 || (rev == math.MinInt32/10 && d < -8) { return 0 }
rev = rev*10 + d                                   // 123 -> 321   -123 -> -321   120 -> 21   1534236469 -> 0 (overflow)
```

The bounds are **asymmetric**: `MaxInt32 = 2147483647` ends in 7 but `MinInt32 = -2147483648` ends in 8. On a 64-bit `int` the
overflow would never trigger by itself, so the check against the 32-bit range is the whole problem.

### Sum of Two Integers: use the fixed-width type and the loop is correct as written

With `int32`, the textbook loop (`a ^ b` is the sum without carry, `(a & b) << 1` the carry) needs no masking because the type
wraps at 32 bits. Take the carry through `uint32` so the shift of a set sign bit is well defined:

```go
func getSum(a, b int32) int32 {
    for b != 0 {
        carry := int32(uint32(a&b) << 1)            // shift as unsigned, then reinterpret
        a ^= b
        b = carry
    }
    return a                                          // (1, 2) -> 3    (-2, 3) -> 1
}
```

With the 64-bit `int` (LeetCode's signature) you must **emulate** 32 bits — mask both values *and the carry* each round, then
reinterpret the pattern as negative at the end:

```go
const mask = 0xFFFFFFFF
for b != 0 { a, b = (a^b)&mask, ((a&b)<<1)&mask }
if a > math.MaxInt32 { return ^(a ^ mask) }           // (-2, 3) -> 1    (-1, -1) -> -2
```

Forgetting to mask the *carry* is the classic slip — the carry can still be wider than 32 bits when `a` and `b` are masked.

### Single Number II and III: per-position counts and a differing bit

Triples do **not** cancel under <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> (`x ^ x ^ x == x`), so **count each bit position** across all numbers and keep the positions
whose count is not a multiple of 3. Build the result in a `uint32` and reinterpret at the end — that cast is the sign fix-up:

```go
for b := 0; b < 32; b++ {
    cnt := 0
    for _, n := range nums { cnt += int(uint32(n) >> b & 1) }
    if cnt%3 != 0 { res |= 1 << b }
}
return int32(res)                                     // [2 2 3 2] -> 3    [0 1 0 1 0 1 99] -> 99    negatives work too
```

**Single Number III:** <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> everything to get `a ^ b`; isolate a bit where they differ with `diff & -diff`; partition the array
by that bit and fold each group into its **own** accumulator (folding both into one collapses back to `a ^ b`):

```go
low := diff & -diff
if n&low != 0 { a ^= n } else { b ^= n }              // [1 2 1 3 2 5] -> [3 5]
```

`-diff` is the two's-complement negative (`^diff + 1`), so `diff & -diff` is exactly the lowest set bit. It works on unsigned
types too — unary minus on a `uint32` wraps modulo 2³², which is the same bit pattern (`u & -u == u & (^u + 1)`, measured `4` for `12`).

### Bitwise AND of a Range: shift both endpoints to the common prefix

The AND of `[left, right]` keeps only the binary prefix the two endpoints share. Shift **both** right until they are equal
(shifting one drifts them apart), count the shifts, and shift back:

```go
shift := 0
for left != right { left >>= 1; right >>= 1; shift++ }
return left << shift                                    // (5, 7) -> 4    (0, 0) -> 0    (1, 2147483647) -> 0
```

A brute-force loop over a range of up to `~2³¹` numbers times out even though it is "correct".

### Bitmask sets, subsets, submasks and Gray code

```go
mask |= 1 << x          // add
mask &^= 1 << x         // remove — Go's AND-NOT, no `& ^(...)` needed
mask ^= 1 << x          // toggle
mask>>x&1 == 1          // contains

for m := 0; m < 1<<n; m++ { for i := 0; i < n; i++ { if m>>i&1 == 1 { /* take nums[i] */ } } }    // all subsets
for sub := m; sub > 0; sub = (sub - 1) & m { /* every non-empty submask of m, largest first; handle sub == 0 after */ }
out[i] = i ^ i>>1                                       // Gray code: [0 1 3 2 6 7 5 4] for n = 3
```

Enumerating every submask of every mask costs `3ⁿ` in total, not `4ⁿ`. A bitmask is limited by the word: shifting `1 << 63` on
`int64` produces the **most negative** number, so use `uint64` for 64-element sets.

### Go-specific shift rules

| Case | Behaviour |
|---|---|
| Shift count `>=` the type's width | The result is `0` (or `-1` for a negative signed right shift) — **no panic** (`uint32(1) << 40 == 0`, `int32(-8) >> 40 == -1`). |
| Negative shift count | **Runtime panic** (`negative shift amount`) since Go 1.13 allows signed counts. |
| `>>` on a signed type | Arithmetic (sign-extending): `int8(-8) >> 1 == -4`. |
| `>>` on an unsigned type | Logical (zero-fill): `uint8(248) >> 1 == 124`. |
| Constant shift too big for the type | A compile error, not a wrap. |

### Go traps in this topic

| Trap | What happens | The fix |
|---|---|---|
| Bitmask stored in `int`, then `>>` | Sign extension on a negative pattern. | Use `uint32` / `uint64` for masks. |
| `1 << 31` typed as `int32` | Becomes `math.MinInt32`. | `uint32(1) << 31`. |
| Reverse Integer on a 64-bit `int` | The overflow never happens by itself. | Check against `math.MaxInt32` / `MinInt32` explicitly. |
| Unmasked carry in the 64-bit `getSum` | The loop misbehaves on negatives. | Mask `a`, `b` **and** the carry each round. |
| `n & (n-1) == 0` for "power of two" | True for `0`. | `n > 0 && n&(n-1) == 0`. |
| `bits.OnesCount(uint(x))` on a negative `int` | Counts the two's-complement pattern (64 bits wide). | Convert to `uint32` first if you mean a 32-bit pattern. |
| Reading a shift count from a negative variable | Panic. | Validate the count. |

### Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "No extra space / no arithmetic operators." | <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> for cancellation; <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>-and-carry for addition. |
| "Every number up to `n`." | `ans[i] = ans[i>>1] + i&1`. |
| "Three of each except one." | Count bits per position mod 3; <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> alone cannot. |
| "Called many times?" | A 256-entry byte table, or `bits.Reverse32` / `OnesCount32` (single instructions). |
| "32 vs 64 bits?" | State the width and use the matching fixed-width type. |
| "Why is `n & (n-1)` correct?" | Subtracting 1 flips the lowest set bit and every bit below it; AND-ing with the original clears exactly that bit. |

---
<!-- /block:20_go_1_problems -->

<!-- problem-map:start -->
## Part 9 · Every Problem in This Topic, by Pattern

Ten problems, five moves (<abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> cancellation · clear/isolate the lowest set bit · per-position counting · shifting to a common prefix · carry-by-hand) — the Python guide's map in Go, where fixed-width types replace the masking. Each **Trap** is a mistake documented in that problem's solution file, plus Go-specific hazards. Topic 20's solutions are Python-first; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Single Number](GoDSA/20_bit_manipulation/001_single_number/solution.go) <br>LC 136 · Easy | <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> cancellation | `x ^= n` over the slice. **Trap:** a `map[int]int` (breaks the O(1)-space constraint); believing only adjacent duplicates cancel. |
| [002 · Number of 1 Bits](GoDSA/20_bit_manipulation/002_number_of_1_bits/solution.go) <br>LC 191 · Easy | Clear the lowest set bit | `bits.OnesCount32(n)`, or Kernighan's `for n != 0 { n &= n - 1; c++ }`. **Trap:** a fixed 32-iteration loop combined with `n & (n-1)`; reading the sign of an `int` mask. |
| [003 · Counting Bits](GoDSA/20_bit_manipulation/003_counting_bits/solution.go) <br>LC 338 · Easy | Popcount from a smaller index | `ans[i] = ans[i>>1] + i&1` (`&` binds tighter than `+`). **Trap:** `make([]int, n)` instead of `n+1`. |
| [004 · Reverse Bits](GoDSA/20_bit_manipulation/004_reverse_bits/solution.go) <br>LC 190 · Easy | Mirror each bit | `bits.Reverse32(n)`, or place bit `i` at `31-i`. **Trap:** placing it at `i`; using a signed type for the accumulator. |
| [005 · Missing Number](GoDSA/20_bit_manipulation/005_missing_number/solution.go) <br>LC 268 · Easy | <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> with indices | Seed with `len(nums)`, then `x ^= i ^ v`. **Trap:** seeding 0; `len(nums)-1` in the Gauss-sum form. |
| [006 · Sum of Two Integers](GoDSA/20_bit_manipulation/006_sum_of_two_integers/solution.go) <br>LC 371 · Medium | Addition = <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> + carry | `int32` with a `uint32` shift for the carry, or 64-bit `int` with explicit 32-bit masks. **Trap:** an unmasked carry in the 64-bit form; shifting a signed value into the sign bit. |
| [007 · Reverse Integer](GoDSA/20_bit_manipulation/007_reverse_integer/solution.go) <br>LC 7 · Medium | Digit peel with an overflow check | `d := x % 10` (already signed), check `rev` against `MaxInt32/10` and `MinInt32/10` *before* multiplying. **Trap:** no check (a 64-bit `int` never overflows); the symmetric `abs(rev) > 2³¹`. |
| [008 · Single Number II](GoDSA/20_bit_manipulation/008_single_number_ii/solution.go) <br>LC 137 · Medium | Count bits per position | Per-bit counts mod 3 into a `uint32`, then `int32(res)`. **Trap:** the <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> fold; skipping the reinterpretation cast (the sign fix-up). |
| [009 · Single Number III](GoDSA/20_bit_manipulation/009_single_number_iii/solution.go) <br>LC 260 · Medium | Split by a differing bit | `low := diff & -diff`; two separate accumulators. **Trap:** returning `[]int{diff, 0}`; one shared accumulator. |
| [010 · Bitwise AND of Numbers Range](GoDSA/20_bit_manipulation/010_bitwise_and_of_numbers_range/solution.go) <br>LC 201 · Medium | Shift to the common prefix | Shift both endpoints right until equal; shift back. **Trap:** a brute-force loop; shifting one endpoint. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Explain `&^` and when you'd reach for it over `a & ^b`
- [ ] Explain why `1 << 63` wraps to a negative `int64` in Go but not in Python
- [ ] Explain why `^x` matches two's complement, not `-x-1` "by definition," in Go
- [ ] State when `>>` is arithmetic vs logical, and why the type — not the operator — decides
- [ ] Know `math/bits`'s OnesCount / LeadingZeros / TrailingZeros / Len and when to prefer them
- [ ] Derive why `x & (x-1)` clears the lowest set bit
- [ ] Derive why `x & -x` isolates the lowest set bit (two's-complement negation)
- [ ] Explain the <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>-cancellation argument for Single Number
- [ ] Write the `dp[i] = dp[i&(i-1)] + 1` Counting Bits recurrence from memory
- [ ] Know why bitmask <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> is only viable for small n (both `2^n` blowup and 64-bit overflow)
- [ ] Use `int32` / `uint32` so the type wraps for you, and emulate 32 bits (with masks on the carry too) when given a 64-bit `int` <!--ca-->
- [ ] Use `&^=` to clear bits, `mask>>x&1 == 1` to test, and enumerate submasks with `sub = (sub - 1) & m` <!--ca-->
- [ ] State Go's shift rules: count `>=` width gives 0, a negative count panics, `>>` is arithmetic on signed types <!--ca-->
- [ ] Guard the power-of-two test with `n > 0`, and isolate the lowest set bit with `x & -x` <!--ca-->
- [ ] Quote the popcount timings (library ≈ 7 ms vs Kernighan ≈ 235 ms per 20M) and prefer `bits.OnesCount` <!--ca-->
