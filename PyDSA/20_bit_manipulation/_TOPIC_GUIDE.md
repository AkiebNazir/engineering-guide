# Topic 20 · Bit Manipulation — Python Deep Dive

> Every problem in this folder reduces to one of four moves: cancel a value
> against itself with <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>, strip or isolate the lowest set bit with `n & (n-1)`
> / `n & -n`, count set-bit occurrences per position instead of per value, or
> emulate a fixed-width machine word inside a language that doesn't have one.
> The last item is THE distinguishing skill of this topic in Python — most of
> the folder is easy once you know the trick; the masking discipline is where
> people who "know the trick" still get the wrong answer.

---

## Part 1 · The Mechanism

### 1.0 The four core identities

```arch
%% caption: n & (n-1) clears the lowest set bit. Repeat until n is 0 to count set bits, or test n & (n-1) == 0 for a power of two.
grid 200x80
node a "n = 1100" at 0,0 color=blue
node b "n - 1 = 1011" at 1,0 w=200 sub="the lowest 1 became 0, the bits below it flipped"
node c "n & (n - 1) = 1000" at 2,0 color=green w=170 sub="lowest set bit cleared"
a -> b -> c
```


```
XOR self-cancellation:   x ^ x == 0        and       x ^ 0 == x
                          -> a ^ b ^ a == b   (order doesn't matter, XOR
                             is commutative and associative)

Drop the lowest set bit: n & (n - 1)
    n     = 0b10110100
    n - 1 = 0b10110011   (borrow flips everything below the lowest 1)
    n&n-1 = 0b10110000   <- lowest set bit gone, nothing else changed

Isolate the lowest set bit: n & -n   (two's complement: -n == ~n + 1)
    n     = 0b10110100
    -n    = 0b01001100   (in two's complement)
    n&-n  = 0b00000100   <- ONLY the lowest set bit survives

Count bits by POSITION, not by value:
    if every number in an array appears exactly k times except one number
    that appears a different number of times, sum each BIT POSITION's count
    across all numbers mod k — the surviving bits reconstruct the answer.
```

`n & (n - 1)` and `n & -n` both come from the same fact: subtracting 1 (or
negating, which is `~n + 1`) flips every bit below and including the lowest
set bit, and leaves everything above it untouched. AND-ing against the
original either clears that lowest run (`n & (n-1)`) or keeps only it
(`n & -n`), depending on which operand you complement.

---

### 1.1 <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> self-cancellation — Single Number (001) and its family

`a ^ a == 0` for any `a`, and <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> is commutative/associative, so <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>-ing an
entire array collapses every value that appears an even number of times to
zero, leaving only the value that appears an odd number of times:

```
nums = [4, 1, 2, 1, 2]
4 ^ 1 ^ 2 ^ 1 ^ 2
= 4 ^ (1 ^ 1) ^ (2 ^ 2)     <- reorder freely, XOR is commutative+associative
= 4 ^ 0 ^ 0
= 4
```

This generalises two directions in this folder:

- **"Exactly one element appears once, rest appear twice"** — 001, plain <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>.
- **"Exactly one appears once, rest appear THREE times"** (008) — plain <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>
  no longer works (`a ^ a ^ a == a`, doesn't cancel). Needs §1.2's
  per-bit-position counting instead.
- **"Exactly TWO elements appear once, rest appear twice"** (009) — plain
  <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> of everything gives `a ^ b`, not `a` or `b` alone. The fix: find any
  bit where `a` and `b` differ (any set bit of `a ^ b`, isolated with
  `diff & -diff`, see §1.0), then partition the whole array by that bit and
  <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> each partition separately. Since `a` and `b` differ on that bit, they
  land in different partitions, and every duplicate pair still shares the
  same bit value (duplicates are identical numbers) so they still cancel
  within their partition.

### 1.2 Counting bits per position — "every element appears k times except one"

When <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> can't cancel a value that appears an odd multiple of k times (any
k >= 3), fall back to first principles: for each of the 32 bit positions,
sum how many of the n numbers have that bit set. If every number but one
appears exactly k times, then (count at that position) mod k is 0 for every
bit belonging only to the k-repeated numbers, and equal to the *unique*
number's bit at every position where it differs. Reassemble the answer bit
by bit:

```
nums = [2, 2, 3, 2]   (3 appears once, 2 appears three times)
bit1: 2=10, so bit1 counts: 1+1+0+1 = 3   -> 3 % 3 == 0   -> answer bit1 = 0
bit0: 2=10, 3=11, so bit0 counts: 0+0+1+0 = 1  -> 1 % 3 == 1 -> answer bit0 = 1
answer = 0b01 = 1... 

# (worked with 3 in place of the unique value 3 = 0b11 for illustration;
#  see 008's solution file for the fully traced version with real numbers)
```

Counting Bits (003) uses a related but distinct idea: rather than counting
population per bit position, it builds a <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> over `i` using the recurrence
`bits[i] = bits[i >> 1] + (i & 1)` — "the popcount of `i` is the popcount of
`i` with its lowest bit dropped, plus that dropped bit." This is O(n) total
instead of O(n log n) from calling a popcount routine on every value.

### 1.3 Bitwise AND of a range — common prefix

`AND` of every integer from `m` to `n` inclusive (010) is the **common
binary prefix** of `m` and `n`, with every bit after the first place they
differ forced to 0. Why: as soon as the range spans a place where the bits
must flip from 0 to 1 (which happens at least once whenever `m != n`,
because incrementing eventually carries), some number in the range has a 0
in that position and some has a 1, and ANY 0 anywhere in the AND chain
zeroes that bit position for the whole AND. So every bit position at or
below the first differing bit becomes 0; only the identical, unchanging
high-order prefix survives:

```
m = 5  = 0b0101
n = 7  = 0b0111
AND(5,6,7) = 0b0101 & 0b0110 & 0b0111 = 0b0100
common prefix of 0101 and 0111 is 01, rest zeroed -> 0b0100 = 4   ✓
```

The algorithm: right-shift `m` and `n` together until they're equal (that's
the common prefix), counting the shifts, then shift back left by that count
to restore the trailing zeros:

```python
shift = 0
while m != n:
    m >>= 1
    n >>= 1
    shift += 1
return m << shift
```

This is itself a Family-B-flavored elimination (topic 05's language) — each
shift discards one bit of certainty-that-they-differ — but it is O(32) worst
case, not O(log(n - m)), since it walks bit positions, not the numeric gap.

---

### 1.4 THE distinguishing gotcha: Python has no fixed-width integers

This is the single biggest way this topic differs in Python versus
C/C++/Java/Go, and it is worth understanding in real depth, not just
memorizing "mask with `0xFFFFFFFF`."

```arch
%% caption: Python ints are unbounded, so negatives have infinitely many leading 1s. Mask to 32 bits to emulate fixed width, then convert back if the sign bit is set.
grid 170x80
node a "Python int" at 1,0 color=blue w=200 sub="-1 = ...1111 (infinite)"
node b "unsigned 32-bit" at 1,1 w=200 sub="4294967295"
node c "x > 0x7FFFFFFF?" at 1,2 shape=diamond color=amber
node d "x - 2**32" at 0,3 color=green sub="back to signed"
node e "x as is" at 2,3 color=green
a -> b : "x & 0xFFFFFFFF"
b -> c
c:L -> d:T : "yes"
c:R -> e:T : "no"
```


**In C/Java/Go**, an `int` is a fixed number of bits (32, typically). Every
bitwise operation is defined modulo `2**32`: shifting bits off the top edge
of the word discards them, and the highest bit is interpreted as the sign
bit (two's complement) — the <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>'s ALU does this natively, for free, as a
side effect of the hardware register width.

**In Python**, `int` is arbitrary-precision. There is no register, no fixed
width, and no bit ever falls off an edge, because there is no edge:

```python
>>> 1 << 40
1099511627776          # this is not an "overflow" in Python — it just grows
>>> (-1) >> 1
-1                      # arithmetic right shift preserves sign, but there is
                         # no 32nd bit to "run out of" — it shifts forever
>>> bin(-5)
'-0b101'                # NOT two's complement text! Python prints sign+magnitude,
                         # but internally treats negative ints as having an
                         # INFINITE prefix of 1-bits for bitwise-op purposes
                         # (a "sign-extended-to-infinity" two's complement)
```

That last point matters: `&`, `|`, `^`, `~` on negative Python ints behave
AS IF the number has an infinite two's-complement representation (infinite
leading 1s for negative numbers, infinite leading 0s for non-negative ones).
`~x` is exactly `-x - 1` — always, for any magnitude — which is correct
two's-complement inversion, just not truncated to any particular width.

**Why this breaks LeetCode problems that assume 32-bit hardware:**

- **Sum of Two Integers (006)**, forbidding `+`, is usually solved with
  `sum = a ^ b` (bits that differ, add without carry) and
  `carry = (a & b) << 1` (bits that both set, produce a carry), looped until
  carry is 0. On a real 32-bit machine, carry generation eventually shifts
  bits off the top of the word and the loop terminates. In Python, `carry`
  can keep growing arbitrarily — for two negative numbers in particular, the
  naive loop **never terminates**, because the infinite sign-extension keeps
  generating new carries forever. The fix is to mask every intermediate
  value to 32 bits (`0xFFFFFFFF`) so the simulation genuinely behaves like a
  32-bit register, then convert the final unsigned 32-bit pattern back to a
  signed Python int if the top bit is set (`if result > 0x7FFFFFFF: result
  -= 0x100000000`).
- **Reverse Bits (004)** reverses the 32 bits of an unsigned integer. Python
  has no natural "32 bits" to reverse — you must explicitly iterate exactly
  32 positions and build the result bit by bit (or use a mask-and-shift
  loop), because there's no hardware word boundary to reverse "up to."
- **Reverse Integer (007)** reverses the *decimal digits* of a 32-bit signed
  integer and must return 0 if the reversed value overflows the 32-bit
  signed range `[-2**31, 2**31 - 1]`. Python's ints never overflow on their
  own — reversing digits arithmetically always "succeeds" and produces
  whatever (possibly huge) integer results. The overflow check must be done
  EXPLICITLY by comparing against the fixed 32-bit signed bounds after the
  fact; skipping this check silently returns a mathematically correct but
  LeetCode-wrong answer for inputs like `1534236469` (reverses to
  `9646324351`, which overflows 32-bit signed and must yield 0).

The general pattern: **whenever a problem says "32-bit integer" or implies
hardware wraparound/overflow, Python needs an explicit mask (`& 0xFFFFFFFF`)
to emulate the fixed width, and an explicit sign-correction step
(subtract `2**32` if the result's top bit is set and you want a signed
interpretation) to convert the masked unsigned pattern back to what a
32-bit signed register would report.** Every solution file in this folder
that touches this (004, 006, 007) demonstrates the bug live: compute the
answer with no masking, show it's wrong or the loop hangs, then compute it
with masking and show it matches LeetCode's expected 32-bit behavior.

### 1.5 `~` in Python — a common trap unrelated to width

`~x == -x - 1` in Python, same identity as any two's-complement machine. But
because Python has no fixed width, `~0b1010` is **not** `0b0101` — it's
`-0b1011` (i.e., `-11`), the infinite-precision inversion, not a 4-bit
inversion. To get a width-bounded bitwise-NOT (e.g., "flip these 32 bits"),
you must explicitly do `(~x) & 0xFFFFFFFF`, masking after inverting.

---

## Part 2 · Pattern Decision Tree

```arch
%% caption: Which bit trick fits.
grid 210x80
node q "Bit problem" at 0,0 shape=pill
node a "Everything twice,\none exception?" at 0,1 shape=diamond color=amber
node x "XOR everything" at 1,1 color=green w=250 sub="pairs cancel"
node b "Appears k times,\none exception?" at 0,2 shape=diamond color=amber
node c "Count each bit position mod k" at 1,2 color=green w=250
node d "Power of two, or count set bits?" at 0,3 shape=diamond color=amber
node e "n & (n - 1) trick" at 1,3 color=green w=250
node f "AND over a range?" at 0,4 shape=diamond color=amber
node g "Shift both ends right until equal" at 1,4 color=green w=250 sub="common prefix"
node h "Small set of items" at 0,5 color=green w=250 sub="enumerate bitmask subsets"
q -> a
a -> x : "yes"
a -> b : "no"
b -> c : "yes"
b -> d : "no"
d -> e : "yes"
d -> f : "no"
f -> g : "yes"
f -> h : "no"
```


```
1. Is exactly one element unique and every other element appears exactly
   TWICE?
       YES -> plain XOR-fold the whole array (§1.1, 001).
       NO  -> continue.

2. Is exactly one element unique and every other element appears exactly
   THREE (or general k) times?
       YES -> per-bit-position counting mod k (§1.2, 008).
       NO  -> continue.

3. Are exactly TWO elements unique (appear once) and everything else
   appears twice?
       YES -> XOR-fold to get a^b, isolate one differing bit with
              diff & -diff, partition and XOR separately (§1.1, 009).
       NO  -> continue.

4. Does the problem explicitly say "32-bit integer," ask you to avoid `+`,
   or ask you to reverse bits/digits and detect overflow?
       YES -> §1.4. You need an explicit 0xFFFFFFFF mask during computation
              and an explicit sign-correction / overflow-bounds check
              afterward. Do not trust Python's arbitrary precision to
              "just work" — it will silently give the mathematically-true
              but LeetCode-wrong answer, or hang in a carry loop.
       NO  -> continue.

5. Is the question "AND (or OR) every integer across a contiguous range
   [m, n]"?
       YES -> §1.3, common-prefix-then-zero-fill via paired right shifts.
       NO  -> continue.

6. Is it "count the number of 1 bits" for one number, or for every number
   0..n?
       YES -> n & (n-1) drops the lowest set bit, loop until 0, for one
              number (002); DP recurrence bits[i] = bits[i>>1] + (i&1) for
              a whole range (003, §1.2).
       NO  -> plain n & (n-1) / n & -n isolation tricks (§1.0) probably
              still apply — look for "lowest set bit" language.
```

---

## Part 3 · Complexity Reference for This Topic

| Operation | Cost | Note |
|---|---|---|
| <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>-fold an array of n elements | O(n) time, O(1) space | 001, 009 |
| `n & (n - 1)` popcount loop | O(k), k = number of set bits | 002 |
| Per-bit-position counting, 32 bits × n elements | O(32n) = O(n) | 008 |
| Counting Bits 0..n via <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> | O(n) total | vs O(n log n) calling popcount per value |
| Reverse 32 bits | O(32) = O(1) | fixed iteration count |
| Sum of two ints via bit-add loop | O(32) = O(1), masked | unbounded without masking (§1.4) |
| Reverse integer digits | O(log10(n)) | digit count, plus O(1) overflow check |
| Bitwise AND of range [m, n] | O(32) = O(1) | paired right-shift to common prefix |

Space is O(1) for every problem in this folder — that's much of the appeal
of bit tricks over hashmap-counting alternatives, and every solution file
prices a hashmap/array-counting brute force against the O(1)-space bit
trick explicitly.

---

## Part 4 · Common Mistakes Across This Topic

1. Assuming Python's `&`/`|`/`^`/`~`/`<<`/`>>` behave like a 32-bit language
   without ever masking — silently wrong answers on Reverse Integer/Bits,
   an infinite or wrong-answer loop on Sum of Two Integers with negative
   inputs (§1.4). This is the #1 mistake in this topic and every relevant
   solution file demonstrates it live.
2. Using `+` or `-` (or `sum()`, which uses `+` internally) anywhere in
   "Sum of Two Integers" — the whole point is bitwise-only addition.
3. Forgetting `~x == -x - 1` in Python is NOT a fixed-width bit flip (§1.5)
   — `~0b1010` is `-11`, not `0b0101`.
4. For "every element appears k times except one," reaching for XOR when
   k != 2 — XOR only cancels pairs; k=3 needs per-bit counting (§1.2).
5. For Single Number III (two uniques), XOR-folding the whole array and
   stopping — that gives `a ^ b`, not either individual value; you must
   isolate a differing bit and partition (§1.1).
6. Off-by-one in the popcount loop (`n & (n-1)`) — forgetting the loop
   condition is `while n:`, not `while n > 1:`, which would skip the last
   set bit.
7. Not special-casing `n == 0` in Reverse Bits/Number of 1 Bits — technically
   handled correctly by the general loop, but worth stating as an edge case
   explicitly rather than trusting it silently.
8. In Reverse Integer, checking for overflow AFTER building the full
   reversed number using unbounded Python arithmetic without ever comparing
   against `[-2**31, 2**31 - 1]` — the reversal always "succeeds" in Python,
   so skipping the explicit bounds check is invisible until you compare
   against LeetCode's judge.
9. In Bitwise AND of Numbers Range, trying to iterate and AND every value
   from `m` to `n` directly — correct but O(n - m), not the intended O(32);
   catastrophic when the range is close to the full `2**31` span.
10. Treating `n & -n` and `n & (n-1)` as interchangeable — one isolates the
    lowest set bit, the other clears it. Confusing them silently breaks
    Counting Bits' DP recurrence or Missing Number's XOR framing if reused
    incorrectly.

---

## Part 5 · The Progression in This Folder

```
  001  LC 136  Single Number                    XOR self-cancellation, the bare mechanism (§1.1)
  002  LC 191  Number of 1 Bits                 n & (n-1) to drop the lowest set bit (§1.0)
  003  LC 338  Counting Bits                    DP over popcount, bits[i]=bits[i>>1]+(i&1) (§1.2)
  004  LC 190  Reverse Bits                     32-bit fixed width has to be emulated (§1.4)
  005  LC 268  Missing Number                   XOR indices against values, or Gauss sum
  006  LC 371  Sum of Two Integers              bitwise add, no +; 32-bit masking is mandatory (§1.4)
  007  LC 7    Reverse Integer                  digit reversal + explicit 32-bit overflow check (§1.4)
  008  LC 137  Single Number II                 per-bit-position counting mod 3 (§1.2)
  009  LC 260  Single Number III                two uniques, partition by a differing bit (§1.1)
  010  LC 201  Bitwise AND of Numbers Range     common-prefix-then-zero-fill (§1.3)
```

001 → 003 build the basic vocabulary (XOR, popcount, DP-over-popcount). 004,
006, 007 are the 32-bit-emulation trio — the hardest conceptual material in
the folder for a Python-native programmer, because "wrong" here means
"correct arithmetic, wrong problem." 005, 008, 009 return to the XOR family
with three genuinely different generalizations. 010 closes with the
range-AND common-prefix trick, a different flavor of bit elimination.

---

<!-- block:20_py_1_beyond -->
## Part 6 · Bitmasks as Sets, Popcount, Gray Code and the Everyday Tricks

The guide covers the four core identities and Python's no-fixed-width gotcha. These are the techniques that recur once you
leave the ten problems. Every snippet was run, and the timings are measurements from this machine (CPython 3.13).

```arch
%% caption: A bitmask is a set of small integers. Add, remove, toggle and test are one operation each, and a whole set fits in one machine word.
grid 200x70
node s "set {3, 5}" at 0,2 color=blue sub="mask = 0b101000"
node a "add x" at 1,0 color=green w=240 sub="mask |= 1 << x"
node r "remove x" at 1,1 color=green w=240 sub="mask &= ~(1 << x)"
node t "toggle x" at 1,2 color=green w=240 sub="mask ^= 1 << x"
node c "contains x" at 1,3 color=green w=240 sub="mask >> x & 1"
node u "set algebra" at 1,4 color=green w=240 sub="union |   intersection &   difference & ~"
s:R -> a:L
s:R -> r:L
s:R -> t:L
s:R -> c:L
s:R -> u:L
```

### 6.1 A bitmask *is* a set

If the universe is small (≤ ~20 elements, or ≤ 64 for a fixed-width word), a set is one integer, and every set operation is
one bit operation. Adding 3 and 5 gives `0b101000`; removing 3 and toggling 7 gives `0b10100000`.

```python
mask |= 1 << x            # add
mask &= ~(1 << x)         # remove
mask ^= 1 << x            # toggle
mask >> x & 1             # contains
a | b   a & b   a & ~b    # union, intersection, difference
```

This is the state compression behind bitmask DP (topic 17) and the "visited set" of Shortest Path Visiting All Nodes.

**All subsets** of `n` items is the loop `for m in range(1 << n)`, taking element `i` when `m >> i & 1` — `[1,2,3]` gives the
eight subsets in binary-counting order. **All submasks** of a mask `m` (used when a DP transitions from every subset of a set) is
a three-line loop that visits each submask exactly once, in decreasing order:

```python
sub = m
while sub:
    yield sub
    sub = (sub - 1) & m           # the next smaller submask: subtract, then mask back into m
yield 0
```

For `m = 0b1011` it yields `11, 10, 9, 8, 3, 2, 1, 0` — eight submasks (`2` to the number of set bits). Summed over **every**
mask of `n` bits the total work is `3ⁿ` (each element is *not in the mask*, *in the mask but not the submask*, or *in both*) —
checked: 81 for `n = 4`. That is why "iterate every subset of every subset" is `O(3ⁿ)`, not `O(4ⁿ)`.

### 6.2 Gray code (LC 89)

A **Gray code** orders the `2ⁿ` values so that consecutive ones differ in exactly one bit. It has a one-line closed form:

```python
[i ^ (i >> 1) for i in range(1 << n)]      # n = 3 -> [0, 1, 3, 2, 6, 7, 5, 4]
```

Adjacent entries — including the wrap from last to first — differ by one bit (checked). The construction that motivates it:
take the sequence for `n − 1`, then append it *reversed* with the top bit set.

### 6.3 Power-of-two and friends

| Test | Expression | Why |
|---|---|---|
| power of two (LC 231) | `n > 0 and n & (n - 1) == 0` | exactly one set bit; the `n > 0` guard excludes `0` |
| power of four (LC 342) | power of two **and** `n & 0x55555555 != 0` | the single bit must sit at an even position |
| `n` is even / odd | `n & 1` | the lowest bit |
| lowest set bit as a value | `n & -n` | two's complement: `-n = ~n + 1` |
| index of the lowest set bit | `(n & -n).bit_length() - 1` | Python has no `trailing_zeros` |
| round up to a power of two | `1 << (n - 1).bit_length()` | for `n ≥ 1` |

`n & (n - 1) == 0` on its own is **true for `0`** — the classic missing guard.

### 6.4 Hamming distance, per bit position

`hamming(a, b)` is `(a ^ b).bit_count()`. For **Total Hamming Distance** over all pairs, do not compare pairs (`O(n²)`);
count, *per bit position*, how many numbers have that bit set — `ones` of them — and each of the `ones × (n − ones)` mixed
pairs differs there:

```python
total = 0
for b in range(32):
    ones = sum(n >> b & 1 for n in nums)
    total += ones * (len(nums) - ones)
# [4, 14, 2] -> 6      [4, 14, 4] -> 4
```

O(32·n). The same "count bits by position" idea is Single Number II's engine (guide §1.2).

### 6.5 Popcount, measured

Three ways to count set bits, over 200,000 random 32-bit integers (×3 rounds):

| Method | Time |
|---|---:|
| `n.bit_count()` (Python 3.10+) | **0.008 s** |
| `bin(n).count("1")` | 0.080 s (~10× slower) |
| Kernighan's loop (`n &= n - 1`) | 0.278 s (~35× slower) |

`bit_count()` is a single C call over the integer's digits; the string version allocates a text per number; the interpreted
loop pays a bytecode dispatch per set bit. Kernighan's loop is still the answer to "count bits without a library call" — and
it does `popcount(n)` iterations, not 32.

### 6.6 Reverse bits without a 32-iteration loop

Swap adjacent bits, then adjacent pairs, then nibbles, bytes and halves — five steps regardless of the bit pattern
(divide and conquer). Checked equal to the loop on 5,000 random inputs; `43261596` → `964176192`:

```python
n = ((n & 0x55555555) << 1) | ((n >> 1) & 0x55555555)     # swap adjacent bits
n = ((n & 0x33333333) << 2) | ((n >> 2) & 0x33333333)     # swap adjacent pairs
n = ((n & 0x0F0F0F0F) << 4) | ((n >> 4) & 0x0F0F0F0F)     # swap nibbles
n = ((n & 0x00FF00FF) << 8) | ((n >> 8) & 0x00FF00FF)     # swap bytes
return ((n << 16) | (n >> 16)) & 0xFFFFFFFF               # swap halves
```

For "called a million times" follow-ups, precompute a 256-entry byte table and reverse four bytes.

### 6.7 The everyday tricks — and their pitfalls

| Trick | Code | Pitfall |
|---|---|---|
| Opposite signs | `(a ^ b) < 0` | Works because the sign bits differ. |
| Swap with no temporary | `x ^= y; y ^= x; x ^= y` | **With the same variable it zeroes it** (`z ^= z` → 0). Fine as a party trick; prefer tuple assignment. |
| Floor-divide by two | `n >> 1` | On negatives Python's shift **floors**: `-5 >> 1 == -3` (same as `-5 // 2`), not `-2`. |
| View a negative as a 32-bit pattern | `-5 & 0xFFFFFFFF` | Yields `0b111…11011`; Python ints have no width, so you must mask (guide §1.4). |
| Test many flags at once | `(flags & mask) == mask` | In Python (and Go) `&` binds *tighter* than `==`, so the parentheses are optional — but in C, Java and JavaScript `flags & mask == mask` parses as `flags & (mask == mask)`. Parenthesise for anyone who switches languages. |

### 6.8 A big integer as a bitset

A Python `int` is an arbitrary-length bit array. `seen |= 1 << x` records `x`; `seen >> x & 1` tests it; and a **shift processes
every position at once** — `bits |= bits << x` is the whole "subset sum" DP (topic 16). Memory is `max(x)` bits, so it suits
dense small universes and is wasteful for sparse huge ones (use a `set`).

### 6.9 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Do it without extra space / without arithmetic operators." | XOR for cancellation; XOR-and-carry for addition (Sum of Two Integers). |
| "Count bits for every number up to `n`." | `ans[i] = ans[i >> 1] + (i & 1)` — one DP array, O(n). |
| "The array has three of each except one." | Count set bits per position mod 3 (§1.2); XOR alone cannot do it. |
| "Called many times?" | Precompute a lookup table (bytes or nibbles). |
| "32-bit vs 64-bit?" | State the width and mask explicitly in Python; in Go/C use a fixed-width type. |
| "Why is `n & (n - 1)` correct?" | Subtracting 1 flips the lowest set bit and every bit below it; AND-ing with the original clears exactly that bit. |

---
<!-- /block:20_py_1_beyond -->

<!-- problem-map:start -->
## Part 7 · Every Problem in This Topic, by Pattern

Ten problems, five moves (XOR cancellation · clear/isolate the lowest set bit · per-position counting · shifting to a common prefix · carry-by-hand). Each **Trap** is a mistake documented in that problem's solution file — most come from Python having no fixed-width integers.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Single Number](PyDSA/20_bit_manipulation/001_single_number_solution.py) <br>LC 136 · Easy | <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> cancellation | <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> everything: `x ^ x == 0` and `x ^ 0 == x`, in any order (commutative and associative), so pairs vanish and the single value remains. O(1) space. **Trap:** reaching for a `Counter`/set (violates the O(1)-space constraint); believing <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> only cancels *adjacent* duplicates. |
| [002 · Number of 1 Bits](PyDSA/20_bit_manipulation/002_number_of_1_bits_solution.py) <br>LC 191 · Easy | Clear the lowest set bit | `n & (n - 1)` clears it, so the loop runs exactly `popcount(n)` times. **Trap:** adding `& 0xFFFFFFFF` masking that this problem does not need; capping the loop at 32 fixed iterations *and* using `n & (n - 1)`. |
| [003 · Counting Bits](PyDSA/20_bit_manipulation/003_counting_bits_solution.py) <br>LC 338 · Easy | Popcount from a smaller index | `ans[i] = ans[i >> 1] + (i & 1)` — drop the lowest bit, then add it back. **Trap:** an array of length `n` instead of `n + 1`; not being explicit that `>>`/`&` (not `//`/`%`) is the bit-manipulation framing. |
| [004 · Reverse Bits](PyDSA/20_bit_manipulation/004_reverse_bits_solution.py) <br>LC 190 · Easy | Mirror each bit | For `i` in `0..31`, take bit `i` of `n` and place it at `31 - i` of the result. **Trap:** placing it at `i` (a no-op copy that still "runs"); `bin(n)[2:].zfill(32)[::-1]` without confirming `n >= 0`. |
| [005 · Missing Number](PyDSA/20_bit_manipulation/005_missing_number_solution.py) <br>LC 268 · Easy | <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> with indices | <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> every index, every value and `n` itself: what remains is the missing number. **Trap:** starting the accumulator at `0` instead of `n`; `len(nums) - 1` in the Gauss-sum alternative. |
| [006 · Sum of Two Integers](PyDSA/20_bit_manipulation/006_sum_of_two_integers_solution.py) <br>LC 371 · Medium | Addition = <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> + carry | `a ^ b` is the sum ignoring carry, `(a & b) << 1` is the carry; repeat until the carry is 0. In Python **both must be masked to 32 bits** and the result sign-fixed. **Trap:** the textbook C loop with no masking (an infinite loop on negatives); masking `a` and `b` but not `carry`. |
| [007 · Reverse Integer](PyDSA/20_bit_manipulation/007_reverse_integer_solution.py) <br>LC 7 · Medium | Digit peel with an overflow check | `rev = rev * 10 + digit`, then check the 32-bit range. **Trap:** no bounds check (Python never overflows, so nothing signals the problem); testing `abs(rev) > 2**31` instead of the asymmetric `[-2³¹, 2³¹ − 1]`. |
| [008 · Single Number II](PyDSA/20_bit_manipulation/008_single_number_ii_solution.py) <br>LC 137 · Medium | Count bits per position | For each of the 32 positions, sum that bit across all numbers mod 3; the surviving bits spell the answer. **Trap:** the <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> fold (`x ^ x ^ x == x`, so triples do *not* cancel); forgetting the sign fix-up on the final unsigned pattern. |
| [009 · Single Number III](PyDSA/20_bit_manipulation/009_single_number_iii_solution.py) <br>LC 260 · Medium | Split by a differing bit | <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> everything to get `a ^ b`, isolate its lowest set bit (`diff & -diff`), and partition the array by that bit — then fold each group separately. **Trap:** returning `[diff, 0]`; folding both groups into *one* accumulator. |
| [010 · Bitwise AND of Numbers Range](PyDSA/20_bit_manipulation/010_bitwise_and_of_numbers_range_solution.py) <br>LC 201 · Medium | Shift to the common prefix | The AND of a range keeps only the common binary prefix of `left` and `right`: shift **both** right until equal, then shift back. **Trap:** a brute-force loop over `~2³¹` numbers; shifting only one endpoint. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] I can state <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> self-cancellation and why it solves "exactly one
      element appears an odd number of times, rest appear an even number."
- [ ] I can explain why plain <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> fails when the repeated count is 3 (or any
      odd k >= 3), and what per-bit-position counting does instead.
- [ ] I can derive `n & (n - 1)` clearing the lowest set bit and `n & -n`
      isolating it, from how two's complement subtraction/negation flips
      trailing bits.
- [ ] I can explain, in concrete terms, why Python integers are
      arbitrary-precision and what that means for `&`, `|`, `^`, `~`, `<<`,
      `>>`, and negative numbers specifically (no fixed word, infinite
      sign-extension) — not just "you need to mask sometimes."
- [ ] I can name the two things 32-bit masking buys you that Python doesn't
      give for free: (a) truncation so a bit-add loop terminates, and (b) a
      fixed range so overflow/sign can be checked at all.
- [ ] I can write the mask-then-sign-correct pattern from memory:
      `x &= 0xFFFFFFFF; if x > 0x7FFFFFFF: x -= 0x100000000`.
- [ ] I can explain why AND of a numeric range collapses to the common
      binary prefix of the endpoints, and derive the paired-right-shift
      algorithm for it.
- [ ] I can tell, from the problem statement alone, whether <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>-folding,
      per-bit counting, or 32-bit emulation is the tool needed, in under 10
      seconds.
</content>
- [ ] Use an integer as a set (add, remove, toggle, contains) and enumerate all submasks with `sub = (sub - 1) & m` <!--ca-->
- [ ] Explain why summing submask counts over all masks gives `3ⁿ` <!--ca-->
- [ ] Write `i ^ (i >> 1)` for Gray code and check adjacent values differ in one bit <!--ca-->
- [ ] Guard the power-of-two test with `n > 0`, and use `n & -n` to isolate the lowest set bit <!--ca-->
- [ ] Quote the popcount timings (`bit_count` ≪ `bin().count` ≪ Kernighan) and say what each is doing <!--ca-->
