# Computer Architecture & Data Representation — How Bits Become Programs

Every other chapter in this module sits on top of two facts it never stops to explain:
everything in a computer is a pattern of bits that means nothing until something
interprets it, and a CPU is a machine that runs those patterns as instructions far
faster than memory can feed it. This chapter starts from first principles — what a
computer is, how numbers and text are stored, how the processor actually executes
your loop — and goes as deep as interviews probe: why `0.1 + 0.2 != 0.3`, why a binary
search can overflow, why a sorted array can make the same loop 3.6× faster, why four
accumulators beat one, and why memory, not arithmetic, is usually what your code is
waiting on. Every number in this chapter was measured on the machine that wrote it (a
4-core Intel Xeon at 2.8 GHz: 32 KB L1d and 1 MB L2 per core, a shared 33 MB L3), with
the program that produced it shown next to it. Corrections of common myths are marked
**Precision note**. A breakdown of what Junior through Staff+ engineers are expected to
know closes the chapter, just before the interview checklist.

## Foundations — What Is a Computer, and How Does It Run Code?

### Why This Chapter Exists

Most bugs in this chapter's territory look impossible from the source code:

- A price computed as `0.1 + 0.2` fails an equality check.
- `(lo + hi) / 2` returns a negative index on a large array.
- A loop gets several times faster when its input is sorted, although it does exactly
  the same arithmetic.
- The same struct takes 24 bytes or 16 bytes depending only on field order.
- `len("café")` is 4 in Python and 5 in Go.

None of these are language quirks. Each is a direct consequence of how hardware stores
values and executes instructions. Once you know the mechanism, each one becomes
predictable — and interviewers use exactly these questions to tell apart candidates
who know *what* their code does from those who know *why*.

### What a Computer Actually Is

Almost every computer you'll program follows the **stored-program (von Neumann)
model**: a **CPU** that executes instructions, a **memory** that holds both the
instructions and the data they work on, and **I/O devices** (disk, network card,
screen), all connected by buses. The CPU runs a loop that never stops:

1. **Fetch** the next instruction from memory (the address is in the *program
   counter* register).
2. **Decode** it: which operation, which registers or memory locations.
3. **Execute** it: the arithmetic-logic unit (ALU) adds, compares, shifts; or the
   load/store unit moves data between registers and memory.
4. Move the program counter on — to the next instruction, or somewhere else if the
   instruction was a jump.

Your Python or Go source becomes, eventually, a long list of these instructions. The
set of instructions a CPU understands — `ADD`, `MOV`, `CMP`, `JMP` and a few hundred
more — is its **instruction set architecture (ISA)**: x86-64 on most servers and
laptops, ARM64 on phones, Apple silicon and a growing share of cloud servers. The ISA
is a contract; how a particular chip implements it (pipelines, caches, predictors —
§8–§12) is the *microarchitecture*, and that is where nearly all modern speed comes from.

### The Core Components

| Component | What it's responsible for | Covered deeper in |
|---|---|---|
| **Registers** | A few dozen tiny, instant storage slots inside the core; every instruction works on them | §8 |
| **ALU / execution units** | The circuits that actually add, multiply, compare and shift | §8, §9 |
| **Control unit, pipeline, branch predictor** | Fetch, decode and schedule instructions; guess which way branches go | §9, §10 |
| **Caches (L1, L2, L3)** | Small, fast copies of recently used memory, close to the core | §11, `01` §2 |
| **Main memory (RAM)** | Gigabytes of storage, ~100× slower to reach than L1 | §11, `14` |
| **Memory management unit (MMU) + TLB** | Translates the virtual addresses your program uses into physical ones | `01` §5 |
| **I/O devices and controllers** | Disk, network, GPU; talk to the CPU through interrupts and DMA | `01` §8 |

### How the Pieces Fit Together

```arch
%% caption: A core runs instructions on registers; loads and stores go through a hierarchy of caches that gets bigger and slower at every step, down to RAM.
grid 170x100
group core "One CPU core" color=orange icon=cpu
node fe "Fetch + decode" at 0,0 in core icon=code sub="program counter"
node bp "Branch predictor" at 1,0 in core icon=decision sub="guesses the next PC"
node alu "Execution units" at 0,1 in core icon=cpu sub="ALU, FPU, SIMD"
node reg "Registers" at 1,1 in core icon=memory sub="~0 cycles"
node l1 "L1 cache" at 0,2 in core icon=cache sub="32 KB, ~1.5 ns"
node l2 "L2 cache" at 1,2 in core icon=cache sub="1 MB, ~5-8 ns"
node l3 "L3 cache" at 0.5,3 icon=cache sub="shared, 33 MB"
node ram "RAM" at 0.5,4 icon=memory sub="GBs, 100-200 ns"
fe -> alu
bp -> fe
alu <-> reg
alu <-> l1
l1 <-> l2
l2 <-> l3
l3 <-> ram
```

The widths of those arrows are the whole story of performance tuning. A core can
finish several instructions per nanosecond, but a trip to RAM costs over a hundred
nanoseconds (§11 measures it). Almost everything clever in a modern CPU — caches,
prefetchers, out-of-order execution, branch prediction — exists to keep the execution
units busy while the data is on its way.

### Everything Is Bits: the Distinction This Chapter Assumes

Memory is a long array of bytes; a byte is eight bits. **A pattern of bits has no
meaning by itself.** The byte `11111011` is 251 if you read it as an unsigned 8-bit
integer, −5 as a signed one, part of a UTF-8 character, a CPU instruction, or one
eighth of a floating-point number. The *type* — in your language or in the
instruction the CPU runs — is what gives bits a meaning. Nearly every surprise in §2–§7
is a place where the bits were fine and the interpretation was not what the programmer
assumed.

### Vocabulary You'll Meet Below, in One Table

| Term | Meaning |
|---|---|
| Bit, byte, word | 0/1; 8 bits; the CPU's natural integer size (64 bits on x86-64/ARM64) |
| Two's complement | The standard encoding of signed integers (§2) |
| Overflow | A result that doesn't fit its fixed width, and wraps or traps (§3) |
| IEEE 754 | The floating-point standard every mainstream CPU implements (§5) |
| Endianness | Byte order of a multi-byte value in memory (§6) |
| Alignment, padding | A value's address must be a multiple of its size; compilers insert gap bytes to make it so (§6) |
| Code point, UTF-8 | A Unicode character's number; the dominant variable-width encoding of it (§7) |
| ISA | Instruction set architecture: the instructions a CPU accepts (x86-64, ARM64) |
| Pipeline | Overlapping the stages of many instructions, like an assembly line (§9) |
| Latency vs throughput | How long one operation takes vs how many finish per unit time (§9) |
| Branch misprediction | The CPU guessed the wrong side of an `if` and must discard work (§10) |
| Cache line | The 64-byte unit in which memory moves between RAM and caches (§11) |
| SIMD | Single instruction, multiple data: one instruction on 4–16 values at once (§12) |

## 1. Binary, Hexadecimal, and Positional Notation

Every positional number system works the same way: each digit is multiplied by a power
of the base. `0b1011` is 1·8 + 0·4 + 1·2 + 1·1 = 11. With *n* bits you can represent
2ⁿ distinct patterns: 8 bits give 256, 32 bits about 4.3 billion, 64 bits about
1.8 × 10¹⁹.

**Hexadecimal** exists because binary is unreadable and decimal doesn't line up with
bits. One hex digit is exactly four bits, so a byte is always two hex digits: `0xFF` =
`1111 1111` = 255, and `0x0A0B0C0D` is four bytes you can read off directly. That is why
memory addresses, colours, hashes and byte dumps are all shown in hex.

Quick facts worth knowing cold, because interview arithmetic uses them constantly:

| Power | Value | Where it shows up |
|---|---|---|
| 2¹⁰ | 1,024 ≈ 10³ | KB; a 10-level binary tree has ~1,000 leaves |
| 2²⁰ | ≈ 10⁶ | MB; binary search over a million items takes 20 steps |
| 2³⁰ | ≈ 10⁹ | GB; 20 more steps covers a billion |
| 2³¹ − 1 | 2,147,483,647 | Largest `int32`: the classic overflow line |
| 2⁵³ | ≈ 9 × 10¹⁵ | Largest range where a `float64` holds every integer exactly (§5) |
| 2⁶³ − 1 | ≈ 9.2 × 10¹⁸ | Largest `int64` |

## 2. Signed Integers: Two's Complement

To store negative numbers, every modern CPU uses **two's complement**: in an *n*-bit
integer, the top bit is worth −2ⁿ⁻¹ instead of +2ⁿ⁻¹. In 8 bits, `10000000` is −128 and
`11111011` is −128 + 64 + 32 + 16 + 8 + 2 + 1 = −5.

```python
def twos(x: int, width: int = 8) -> str:
    return format(x & ((1 << width) - 1), f"0{width}b")

for v in (5, -5, 127, -128, -1):
    print(f"{v:>5} in 8-bit two's complement: {twos(v)}")
print("~5 =", ~5, "(= -5 - 1)")
```

```text
    5 in 8-bit two's complement: 00000101
   -5 in 8-bit two's complement: 11111011
  127 in 8-bit two's complement: 01111111
 -128 in 8-bit two's complement: 10000000
   -1 in 8-bit two's complement: 11111111
~5 = -6 (= -5 - 1)
```

Why this encoding won over "a sign bit plus a magnitude":

- **One adder does everything.** Adding the bit patterns of 5 and −5 as if they were
  unsigned gives 256, which wraps to 0 in 8 bits — the right answer with no special
  case. Subtraction is addition of the negation.
- **Negation is "flip every bit, add 1":** `-x == ~x + 1`, which is why `~5` is −6.
- **There is exactly one zero.** Sign-magnitude has +0 and −0.

The cost is an **asymmetric range**: an 8-bit signed integer runs from −128 to +127.
The most negative value has no positive partner, which §3 shows is a real source of
bugs.

## 3. Integer Overflow and Division Semantics

Fixed-width integers **wrap around** when a result doesn't fit. Go, C, C++, Java and
Rust's release builds all do this silently (C and C++ make *signed* overflow undefined
behaviour, which is worse: the optimiser may assume it never happens). Python's `int`
is arbitrary-precision and never overflows, which is why these bugs surprise Python
programmers most when they switch languages or cross into NumPy, databases or
protocols.

```go
package main

import (
	"fmt"
	"math"
)

func main() {
	var a int8 = 127
	a++
	fmt.Println("int8 127+1 =", a)
	var u uint8 = 0
	u--
	fmt.Println("uint8 0-1 =", u)
	m := int64(math.MinInt64)
	fmt.Println("-MinInt64 =", -m, " (negating the most negative number gives itself)")
	lo, hi := 2_000_000_000, 2_100_000_000
	var l32, h32 int32 = int32(lo), int32(hi)
	fmt.Println("int32 (lo+hi)/2 =", (l32+h32)/2, " vs lo+(hi-lo)/2 =", l32+(h32-l32)/2)
	neg := int8(-5)
	fmt.Printf("-5 as int8 bits: %08b\n", uint8(neg))
	x := int8(-5)
	fmt.Println("-5 >> 1 (arithmetic) =", x>>1, "  uint8(-5) >> 1 (logical) =", uint8(x)>>1)
}
```

```text
int8 127+1 = -128
uint8 0-1 = 255
-MinInt64 = -9223372036854775808  (negating the most negative number gives itself)
int32 (lo+hi)/2 = -97483648  vs lo+(hi-lo)/2 = 2050000000
-5 as int8 bits: 11111011
-5 >> 1 (arithmetic) = -3   uint8(-5) >> 1 (logical) = 125
```

What each line teaches:

- **`(lo + hi) / 2` is the most famous overflow in interview code.** On 32-bit indices
  the sum passes 2³¹ − 1 and wraps negative. This exact bug sat in Java's
  `Arrays.binarySearch` for nine years before it was found in 2006. Write
  `lo + (hi - lo) / 2`, and say why when you do — interviewers notice.
- **`abs(MinInt64)` is negative.** −(−2⁶³) = 2⁶³ doesn't fit, so it wraps back to −2⁶³.
  Any code that "makes a number positive" to use it as an index or a hash bucket can go
  negative on exactly one input.
- **Unsigned underflow** turns "0 − 1" into the largest value: a loop
  `for i := uint(n-1); i >= 0; i--` never ends, because an unsigned `i` is always ≥ 0.
- **Right shift of a negative number** is *arithmetic* (copies the sign bit) for signed
  types and *logical* (shifts in zeros) for unsigned ones.

Division is the other semantics trap. Languages disagree on how to round a negative
quotient:

```python
print("-7 // 2 =", -7 // 2, "| -7 % 2 =", -7 % 2, "| int(-7/2) =", int(-7 / 2))
print("-5 >> 1 =", -5 >> 1, "(Python shifts are arithmetic: floor division)")
```

```text
-7 // 2 = -4 | -7 % 2 = 1 | int(-7/2) = -3
-5 >> 1 = -3 (Python shifts are arithmetic: floor division)
```

Python's `//` rounds toward −∞, so `%` always has the sign of the divisor (−7 % 2 is 1).
Go, Java, C and C++ truncate toward zero: `-7 / 2` is −3 and `-7 % 2` is −1. The
practical consequence: `hash % n` can be negative in Go or Java if `hash` is, which
indexes out of bounds. Mask the sign off or use an unsigned hash.

**Precision note:** "Python integers can't overflow" is true of `int`, but Python code
overflows all the time at the boundaries — a NumPy `int32` array, a `struct.pack('i')`,
a database `INTEGER` column, a JSON number read by JavaScript (which holds integers
exactly only up to 2⁵³). Real incidents follow this shape: Ariane 5's first flight
(1996) was lost when a 64-bit float was converted to a 16-bit signed integer that
couldn't hold it, and YouTube had to widen its view counter after a video passed
2³¹ − 1 views in 2014.

## 4. Bitwise Operations and the Tricks Interviews Use

| Operator | Python / Go | Meaning |
|---|---|---|
| AND | `a & b` | 1 where both are 1: **test** or **clear** bits with a mask |
| OR | `a \| b` | 1 where either is 1: **set** bits |
| XOR | `a ^ b` | 1 where they differ: **toggle** bits; `x ^ x == 0` |
| NOT | `~a` (Go: `^a`) | Flip every bit |
| Shifts | `a << k`, `a >> k` | Multiply / divide by 2ᵏ (arithmetic for signed) |

```python
x = 0b10110100
print(f"x         = {x:08b}")
print(f"x & (x-1) = {x & (x-1):08b}  clears the lowest set bit")
print(f"x & -x    = {x & -x:08b}  isolates the lowest set bit")
print(f"x | (1<<0)= {x | 1:08b}  sets bit 0")
print(f"x ^ (1<<2)= {x ^ 4:08b}  toggles bit 2")
print("popcount:", x.bit_count(), "| bit_length:", x.bit_length())
print("is power of two? 64:", 64 & 63 == 0, " 96:", 96 & 95 == 0)
mask = 0b1011
subs = []
s = mask
while True:
    subs.append(format(s, "04b"))
    if s == 0: break
    s = (s - 1) & mask
print("all submasks of 1011:", subs)
nums = [4, 1, 2, 1, 2]
r = 0
for v in nums: r ^= v
print("single number in", nums, "=", r)
```

```text
x         = 10110100
x & (x-1) = 10110000  clears the lowest set bit
x & -x    = 00000100  isolates the lowest set bit
x | (1<<0)= 10110101  sets bit 0
x ^ (1<<2)= 10110000  toggles bit 2
popcount: 4 | bit_length: 8
is power of two? 64: True  96: False
all submasks of 1011: ['1011', '1010', '1001', '1000', '0011', '0010', '0001', '0000']
single number in [4, 1, 2, 1, 2] = 4
```

Why each trick works, which is what an interviewer will ask next:

- **`x & (x - 1)`** — subtracting 1 flips the lowest set bit to 0 and every bit below it
  to 1; the AND then clears exactly that lowest set bit. Repeating it until zero counts
  set bits in O(number of ones) (Kernighan's method), and `x & (x - 1) == 0` tests for a
  power of two (for `x > 0`).
- **`x & -x`** — in two's complement, `-x` is `~x + 1`, which agrees with `x` only at the
  lowest set bit. This is the core step of a Fenwick (binary indexed) tree (DSA topic 26).
- **XOR cancels pairs** — XOR is associative, commutative and self-inverse, so XOR-ing
  every element leaves the one without a partner (LeetCode 136, and its variants).
- **`(s - 1) & mask`** walks every subset of a bitmask in decreasing order — the inner
  loop of bitmask DP over subsets (DSA topic 20, bit manipulation).
- **A bitmask is a set** of up to 64 small integers in one machine word: union is `|`,
  intersection is `&`, membership is `(s >> i) & 1`. Bitmask DP, visited-state encoding
  in BFS (“shortest path visiting all nodes”) and permission flags all rely on it.

**Precision note:** bit tricks are a win in C and Go, where an int is a register.
CPython's integers are heap objects, so a set of 27 small bitmasks can be *slower* than
27 Python `set`s — `PyDSA/01_arrays_hashing/011` measured exactly that. Use bits when
they make the algorithm simpler (subset DP, state encoding), not as a micro-optimisation
in Python.

## 5. Floating Point: IEEE 754

A `float64` (Python's `float`, Go's `float64`, Java's `double`) is binary scientific
notation packed into 64 bits: **1 sign bit, 11 exponent bits, 52 fraction bits**. The
value is (−1)^sign × 1.fraction × 2^(exponent − 1023). A `float32` has 1, 8 and 23 bits.

```python
import math, struct, sys

def bits(x: float) -> str:
    b = struct.unpack(">Q", struct.pack(">d", x))[0]
    s = f"{b:064b}"
    return f"{s[0]} {s[1:12]} {s[12:]}"

print("0.1 + 0.2 =", 0.1 + 0.2, "| == 0.3?", 0.1 + 0.2 == 0.3)
print("exact value stored for 0.1:", f"{0.1:.30f}")
print("bits of 0.1  :", bits(0.1))
print("bits of -2.0 :", bits(-2.0))
print("2**53 + 1 == 2**53 as float?", float(2**53 + 1) == float(2**53))
print("1e16 + 1 - 1e16 =", 1e16 + 1 - 1e16)
xs = [0.1] * 10
print("sum of ten 0.1:", sum(xs), "| math.fsum:", math.fsum(xs))
big = [1e16, 1.0, -1e16] * 1000
print("naive sum [1e16,1,-1e16]*1000:", sum(big), "| fsum:", math.fsum(big))
print("inf - inf =", float("inf") - float("inf"), "| nan == nan?", float("nan") == float("nan"))
print("isclose(0.1+0.2, 0.3):", math.isclose(0.1 + 0.2, 0.3))
print("machine epsilon:", sys.float_info.epsilon, "| max:", sys.float_info.max)
print("smallest subnormal:", 5e-324, "| 5e-324/2 =", 5e-324 / 2)
print("round(2.5), round(3.5):", round(2.5), round(3.5))
```

```text
0.1 + 0.2 = 0.30000000000000004 | == 0.3? False
exact value stored for 0.1: 0.100000000000000005551115123126
bits of 0.1  : 0 01111111011 1001100110011001100110011001100110011001100110011010
bits of -2.0 : 1 10000000000 0000000000000000000000000000000000000000000000000000
2**53 + 1 == 2**53 as float? True
1e16 + 1 - 1e16 = 0.0
sum of ten 0.1: 0.9999999999999999 | math.fsum: 1.0
naive sum [1e16,1,-1e16]*1000: 0.0 | fsum: 1000.0
inf - inf = nan | nan == nan? False
isclose(0.1+0.2, 0.3): True
machine epsilon: 2.220446049250313e-16 | max: 1.7976931348623157e+308
smallest subnormal: 5e-324 | 5e-324/2 = 0.0
round(2.5), round(3.5): 2 4
```

Reading the output line by line is the fastest way to understand floating point:

- **0.1 cannot be stored exactly.** In binary, 1/10 is a repeating fraction
  (`0.000110011001100…`), exactly like 1/3 in decimal. The 52 fraction bits hold the
  repeating `1001` pattern, rounded at the end (`…1010`). So `0.1` is really
  0.1000000000000000055…, and `0.2` and `0.3` are rounded too — in different directions,
  which is why their sum misses. The error is tiny (about 1 part in 10¹⁶) but `==`
  compares every bit.
- **Precision is relative, not absolute.** 52 fraction bits give about 15–17
  significant decimal digits whatever the magnitude. Near 1.0 the gap between adjacent
  floats (one **ULP**, unit in the last place) is 2.2 × 10⁻¹⁶ — **machine epsilon**. Near
  10¹⁶ the gap is 2, so adding 1 does nothing: `1e16 + 1 - 1e16` is 0. Above 2⁵³ a
  float64 can't even represent every integer.
- **Addition is not associative.** `(a + b) + c` and `a + (b + c)` can differ, so summing
  the same numbers in a different order gives a different answer. That is why the naive
  sum of `[1e16, 1, -1e16] * 1000` is 0 while the true answer is 1000.
  `math.fsum` tracks the lost low-order bits exactly (Shewchuk's algorithm); Kahan
  summation is the cheaper, approximately-compensated version you can write in any
  language.
- **Special values.** Overflow gives `±inf`, not an exception; `inf − inf` and `0/0`
  give **NaN**, which is not equal to anything, *including itself* — so `x != x` is the
  classic NaN test, and a NaN in a list can break sorting and `max`. Below the smallest
  normal number, **subnormals** trade precision for a gradual underflow, and below
  those, values flush to 0.
- **Rounding is round-half-to-even** (banker's rounding) by default, in hardware and in
  Python's `round`: 2.5 → 2, 3.5 → 4. It removes the upward bias that "always round
  half up" adds to large sums.

**The rules that follow, and that interviewers look for:**

1. **Never compare floats with `==`** unless you know both sides are exactly
   representable. Compare with a tolerance: `math.isclose(a, b, rel_tol=1e-9)` — a
   *relative* tolerance, because an absolute one is meaningless across magnitudes.
2. **Never store money in floats.** Use integer cents (or smaller units) or a decimal
   type (`decimal.Decimal`, SQL `NUMERIC`). Financial rounding rules are defined in
   decimal, and binary floats can't honour them.
3. **Beware subtracting nearly equal numbers** (*catastrophic cancellation*): the
   leading digits cancel and you're left with the rounding noise. Rearrange formulas
   to avoid it (the textbook example is the quadratic formula).
4. **Don't key a hash map by a float computed two different ways.** Topic 21 of the DSA
   module (`Max Points on a Line`) shows two different fractions that round to the same
   float; use a reduced integer pair instead.
5. **Integers are exact up to 2⁵³.** Beyond that, a JSON number parsed by JavaScript or
   a float column silently rounds IDs — one reason APIs send 64-bit IDs as strings.

**Precision note:** floating point is not "random error." Every IEEE 754 operation is
*exactly rounded*: the result is the representable number closest to the true result.
The errors are deterministic and analysable, which is why `(0.1 * 10) / 10 == 0.1` is
true here while `0.1 * 3 == 0.3` is false — each individual rounding happened to land
differently.

## 6. Byte Order, Alignment, and Struct Layout

### Endianness

A 4-byte integer occupies four consecutive addresses, and the CPU architecture decides
which end goes first. **Little-endian** (x86-64, and ARM64 as normally configured)
stores the least significant byte at the lowest address; **big-endian** stores the most
significant byte first, and it is the **network byte order** of IP, TCP and most binary
protocols.

```python
import struct, sys
print("sys.byteorder:", sys.byteorder)
n = 0x0A0B0C0D
print("0x0A0B0C0D little-endian bytes:", struct.pack("<I", n).hex(" "))
print("0x0A0B0C0D big-endian bytes   :", struct.pack(">I", n).hex(" "))
print("misread LE as BE:", hex(struct.unpack(">I", struct.pack("<I", n))[0]))
```

```text
sys.byteorder: little
0x0A0B0C0D little-endian bytes: 0d 0c 0b 0a
0x0A0B0C0D big-endian bytes   : 0a 0b 0c 0d
misread LE as BE: 0xd0c0b0a
```

Endianness never matters *inside* one program — the CPU reads its own layout
consistently. It matters the moment bytes cross a boundary: a file format, a network
protocol, a memory-mapped structure read by another machine. Serialize explicitly
(`struct.pack(">I")`, Go's `binary.BigEndian.PutUint32`, `htonl` in C) and never by
copying a struct's raw memory.

### Alignment and padding

CPUs load a value fastest — and on some architectures, only at all — when its address
is a multiple of its size: an 8-byte `int64` at an address divisible by 8. Compilers
enforce this by inserting **padding** bytes inside structs, and by rounding a struct's
size up to its largest field's alignment so that arrays of it stay aligned.

```go
package main

import (
	"fmt"
	"unsafe"
)

type Loose struct {
	A bool  // 1 byte + 7 padding (next field needs 8-byte alignment)
	B int64 // 8
	C bool  // 1 byte + 7 padding (struct size rounds up to its alignment)
}

type Tight struct {
	B int64 // 8
	A bool  // 1
	C bool  // 1 + 6 padding
}

func main() {
	var l Loose
	var t Tight
	fmt.Println("Loose:", unsafe.Sizeof(l), "bytes; offsets A,B,C =", unsafe.Offsetof(l.A), unsafe.Offsetof(l.B), unsafe.Offsetof(l.C))
	fmt.Println("Tight:", unsafe.Sizeof(t), "bytes; offsets B,A,C =", unsafe.Offsetof(t.B), unsafe.Offsetof(t.A), unsafe.Offsetof(t.C))
	fmt.Println("1M Loose:", unsafe.Sizeof(l)*1_000_000/1_000_000, "MB  1M Tight:", unsafe.Sizeof(t)*1_000_000/1_000_000, "MB")
}
```

```text
Loose: 24 bytes; offsets A,B,C = 0 8 16
Tight: 16 bytes; offsets B,A,C = 0 8 9
1M Loose: 24 MB  1M Tight: 16 MB
```

The same three fields cost 50% more memory in the wrong order. Ordering fields from
largest to smallest removes most padding; Go and C never reorder fields for you (Rust
does, by default). It matters for hot structures held in their millions — and in
concurrent code the opposite trick, *deliberately* padding a field onto its own 64-byte
cache line, prevents false sharing (`01` §2).

## 7. Text: Unicode and UTF-8

**Unicode** assigns every character a number, its **code point**, written `U+00E9`
for é. There are over 150,000 assigned code points, up to `U+10FFFF`. An **encoding**
turns code points into bytes, and **UTF-8** is the one that won: it is used by the vast
majority of the web and is the default in Python 3 source, Go source and most modern
protocols.

UTF-8 is variable-width. The leading bits of the first byte say how many bytes follow:

| Code points | Bytes | Bit pattern |
|---|---|---|
| U+0000–U+007F (ASCII) | 1 | `0xxxxxxx` |
| U+0080–U+07FF | 2 | `110xxxxx 10xxxxxx` |
| U+0800–U+FFFF | 3 | `1110xxxx 10xxxxxx 10xxxxxx` |
| U+10000–U+10FFFF | 4 | `11110xxx 10xxxxxx 10xxxxxx 10xxxxxx` |

```python
for ch in ["A", "é", "€", "😀"]:
    b = ch.encode("utf-8")
    print(f"{ch!r:6} U+{ord(ch):04X}  utf-8 {len(b)} bytes: {b.hex(' ')}  utf-16 {len(ch.encode('utf-16-le'))} bytes")
s = "café"
print("len('café') =", len(s), "| utf-8 bytes =", len(s.encode()))
import unicodedata
a, b = "café", "café"
print("composed == decomposed?", a == b, "| lens", len(a), len(b),
      "| after NFC:", unicodedata.normalize("NFC", a) == unicodedata.normalize("NFC", b))
print("latin-1 misdecode of 'é':", "é".encode("utf-8").decode("latin-1"))
```

```text
'A'    U+0041  utf-8 1 bytes: 41  utf-16 2 bytes
'é'    U+00E9  utf-8 2 bytes: c3 a9  utf-16 2 bytes
'€'    U+20AC  utf-8 3 bytes: e2 82 ac  utf-16 2 bytes
'😀'    U+1F600  utf-8 4 bytes: f0 9f 98 80  utf-16 4 bytes
len('café') = 4 | utf-8 bytes = 5
composed == decomposed? False | lens 4 5 | after NFC: True
latin-1 misdecode of 'é': Ã©
```

Why UTF-8's design is clever, and what it costs:

- **ASCII is unchanged**, so every ASCII file is already valid UTF-8.
- **It self-synchronises:** continuation bytes always start `10`, so from any byte you
  can find the start of the character, and a byte search for an ASCII character never
  matches inside a multi-byte one.
- **The cost is that indexing by character is O(n).** You can't jump to the 1,000th
  character without decoding the 999 before it. Languages choose differently: Python
  stores strings so that `s[i]` is a code point (it picks 1, 2 or 4 bytes per character
  for the whole string); Go strings are raw UTF-8 bytes.

```go
package main

import (
	"fmt"
	"unicode/utf8"
)

func main() {
	s := "café"
	fmt.Println("len(s) =", len(s), "bytes; runes =", utf8.RuneCountInString(s))
	fmt.Printf("s[3] = %d (a byte, not 'é')\n", s[3])
	for i, r := range s { // range decodes UTF-8: 'é' starts at byte 3 and uses bytes 3-4
		fmt.Printf("%d:%c ", i, r)
	}
	fmt.Println()
	fmt.Println("[]rune(s)[3] =", string([]rune(s)[3]))
}
```

```text
len(s) = 5 bytes; runes = 4
s[3] = 195 (a byte, not 'é')
0:c 1:a 2:f 3:é 
[]rune(s)[3] = é
```

Three traps interviewers probe:

1. **"Length" has at least three meanings**: bytes (storage, network), code points
   (Python's `len`), and user-perceived characters (*grapheme clusters* — a flag emoji
   or an accented letter built from two code points is one on screen). Say which one
   the question needs.
2. **The same text can be different code points.** `é` can be one code point (U+00E9)
   or `e` plus a combining accent (U+0301). They look identical and compare unequal;
   **normalise** (NFC) before comparing, hashing or using text as a key.
3. **Mojibake** — `é` shown as `Ã©` — is UTF-8 bytes decoded as Latin-1. It is always a
   missing or wrong encoding declaration at a boundary. Decode bytes to text at the
   edge of the program, work in text inside, encode on the way out.

In DSA problems: `[26]int` counts only work when input is guaranteed lowercase ASCII —
`PyDSA/01_arrays_hashing/003` shows the `IndexError` on `"école"` — and "reverse a
string" on bytes corrupts multi-byte characters.

## 8. How the CPU Executes Your Code

A compiler (Go, C, Rust) translates source ahead of time into machine instructions for
one ISA. An interpreter (CPython) compiles to *bytecode* for a virtual machine and then
runs a C loop that executes one bytecode at a time — each Python-level `+` is dozens of
machine instructions of type checks and dispatch, which is the root of the 30–100×
speed gap in tight loops. JIT compilers (the JVM's HotSpot, JavaScript's V8, PyPy)
start interpreting and compile hot code to machine instructions at run time.

Here is real output of the Go compiler for a small loop (`go build -gcflags=-S`),
trimmed to the instructions and annotated (the labels and comments are ours):

```go
func sumSimple(data []int) (s int) {
	for _, v := range data {
		if v >= 128 {
			s += v
		}
	}
	return
}
```

```text
XORL    CX, CX              ; i = 0
XORL    DX, DX              ; s = 0
JMP     check
loop:
MOVQ    (AX)(CX*8), SI      ; v = data[i]         (a load from memory)
LEAQ    (SI)(DX*1), DI      ; tmp = s + v          (compute the add speculatively)
INCQ    CX                  ; i++
CMPQ    SI, $128            ; compare v with 128
CMOVQGE DI, DX              ; if v >= 128 { s = tmp }   (no jump!)
check:
CMPQ    BX, CX              ; i < len(data)?
JGT     loop
RET
```

Four ideas to take from eight instructions:

- **Registers are the working set.** `AX` holds the slice's base address, `BX` its
  length, `CX` the index, `DX` the sum. Only `MOVQ (AX)(CX*8)` touches memory.
- **Addressing is arithmetic.** `data[i]` is "base + i × 8", computed inside the load
  instruction — which is why arrays of fixed-size elements give O(1) indexing.
- **The `if` became a conditional move.** The compiler computed `s + v` unconditionally
  and used `CMOVQGE` to keep it or not. There is no jump for the CPU to mispredict —
  §10 shows why this matters.
- **A loop is a compare and a backward jump** (`JGT loop`). The branch predictor learns
  that it is almost always taken.

## 9. Pipelining and Instruction-Level Parallelism

A modern core doesn't finish one instruction before starting the next. It works like an
assembly line (a **pipeline**): while one instruction executes, the next is decoding
and the one after is being fetched. On top of that, cores are **superscalar** (several
execution units, several instructions started per cycle) and **out-of-order** (they
look dozens to hundreds of instructions ahead and run any whose inputs are ready).

That gives two different speeds for the same operation, and the distinction is the
single most useful idea in performance work:

- **Latency**: how long one operation takes from inputs to result. A `float64` add is
  a few cycles (about 4 on this generation of Intel core).
- **Throughput**: how many can *finish* per cycle when they're independent. This core
  can finish two float adds every cycle.

A loop where each step needs the previous result runs at the latency. A loop with
independent steps runs at the throughput. Same arithmetic, same answer:

```go
package main

import (
	"fmt"
	"time"
)

//go:noinline
func sum1(a []float64) float64 {
	s := 0.0
	for _, v := range a {
		s += v // every add waits for the previous one
	}
	return s
}

//go:noinline
func sum4(a []float64) float64 {
	var s0, s1, s2, s3 float64
	for i := 0; i+3 < len(a); i += 4 {
		s0 += a[i] // four chains the CPU can run side by side
		s1 += a[i+1]
		s2 += a[i+2]
		s3 += a[i+3]
	}
	return s0 + s1 + s2 + s3
}

func best(f func([]float64) float64, a []float64) time.Duration {
	b := time.Hour
	for r := 0; r < 7; r++ {
		t := time.Now()
		for i := 0; i < 50; i++ {
			f(a)
		}
		if d := time.Since(t); d < b {
			b = d
		}
	}
	return b
}

func main() {
	a := make([]float64, 1<<14) // 128 KB: fits in L2, so memory is not the limit
	for i := range a {
		a[i] = float64(i % 7)
	}
	t1, t4 := best(sum1, a), best(sum4, a)
	fmt.Printf("1 accumulator: %v  4 accumulators: %v  speedup %.1fx\n", t1, t4, float64(t1)/float64(t4))
	fmt.Println("same answer:", sum1(a) == sum4(a))
}
```

```text
1 accumulator: 981.365µs  4 accumulators: 275.554µs  speedup 3.6x
same answer: true
```

Per add: 981 µs / (16,384 × 50) ≈ 1.2 ns with one accumulator — the add
latency (3–4 cycles, depending on the clock the VM is actually running at), because each `s += v` waits for the one before. With four independent chains
the core overlaps them: ≈ 0.34 ns, about one cycle per add or less.

**Precision note:** the compiler didn't do this for you, and it isn't allowed to.
Because float addition isn't associative (§5), splitting a sum into four partial sums can
change the result, so compilers only reorder float arithmetic when you opt in
(`-ffast-math` in C). The answers match here only because the inputs are small
integers, which floats represent exactly. For integers, compilers do this freely.

Where this shows up beyond micro-benchmarks: a linked-list traversal is one long
dependency chain (you can't load node *k + 1* until node *k* arrives), while an array
scan has none — one reason arrays beat linked lists by far more than Big-O suggests
(`06` §13).

## 10. Branch Prediction

A pipeline has a problem with `if`: the CPU needs to fetch the next instruction long
before the comparison deciding which instruction comes next has finished. So it
**guesses**. The **branch predictor** records the history of each branch and predicts
the direction; the CPU executes the predicted path *speculatively*. A correct guess
costs nothing. A wrong guess means throwing away everything started after the branch
and restarting — on the order of 15–20 cycles.

The classic demonstration: the same loop over the same numbers, first shuffled, then
sorted.

```go
package main

import (
	"fmt"
	"math/rand"
	"sort"
	"time"
)

// The compiler turns this if into a conditional move (CMOV): no branch to predict.
//
//go:noinline
func sumSimple(data []int) (s int) {
	for _, v := range data {
		if v >= 128 {
			s += v
		}
	}
	return
}

// A store inside the if keeps it a real conditional jump.
//
//go:noinline
func sumBranchy(data []int, hist *[256]int) (s int) {
	for _, v := range data {
		if v >= 128 {
			s += v
			hist[v]++
		}
	}
	return
}

func timeIt(f func()) time.Duration {
	best := time.Hour
	for r := 0; r < 5; r++ {
		t := time.Now()
		for i := 0; i < 20; i++ {
			f()
		}
		if d := time.Since(t); d < best {
			best = d
		}
	}
	return best
}

func main() {
	rng := rand.New(rand.NewSource(1))
	data := make([]int, 1<<20)
	for i := range data {
		data[i] = rng.Intn(256)
	}
	var h [256]int
	s1 := timeIt(func() { sumSimple(data) })
	b1 := timeIt(func() { sumBranchy(data, &h) })
	sort.Ints(data)
	s2 := timeIt(func() { sumSimple(data) })
	b2 := timeIt(func() { sumBranchy(data, &h) })
	fmt.Printf("branch-free (CMOV): shuffled %v  sorted %v  ratio %.1fx\n", s1, s2, float64(s1)/float64(s2))
	fmt.Printf("real branch:        shuffled %v  sorted %v  ratio %.1fx\n", b1, b2, float64(b1)/float64(b2))
}
```

```text
branch-free (CMOV): shuffled 13.309201ms  sorted 13.312923ms  ratio 1.0x
real branch:        shuffled 100.352098ms  sorted 27.625264ms  ratio 3.6x
```

What the numbers say:

- **With a real branch, shuffled data is 3.6× slower.** On random bytes the branch is a
  coin flip, so the predictor is wrong about half the time. The difference is ≈ 3.5 ns
  per element over ~0.5 mispredictions per element: roughly 7 ns, or 20-odd cycles,
  per misprediction. Sorted, the branch is "not taken" for the first half and "taken"
  for the second, and the predictor is almost always right.
- **Branch-free code doesn't care.** `sumSimple` compiled to `CMOVQGE` (§8), so there is
  no guess to get wrong, and sorted and shuffled run at the same speed. This is also why
  you'll see the famous "sorted array is faster" demonstration fail to reproduce on
  some compilers: they removed the branch.

Practical takeaways:

1. **Unpredictable branches in hot loops are expensive**; predictable ones are nearly
   free. Error checks (`if err != nil`) that almost never fire cost almost nothing.
2. **Branch-free forms** — `min`/`max`, arithmetic on booleans, lookup tables — remove the
   guess entirely. Compilers do it when they can prove it safe (no side effect on either
   side, as the `hist[v]++` store prevented here).
3. **Sorting or partitioning data first** can pay for itself when the same data is
   filtered many times.

**Precision note — the security cost of speculation.** Speculatively executed
instructions are thrown away, but their effect on the *caches* is not. Spectre (2018)
showed that an attacker can train the predictor to speculatively read memory it
shouldn't, then recover the value by timing which cache line got loaded; Meltdown did
the same across the user/kernel boundary on affected Intel chips. The mitigations
(kernel page-table isolation, retpolines, the "Mitigation: Aligned branch/return
thunks" lines in this machine's `lscpu`) cost real performance on system-call-heavy
workloads — one reason syscalls got more expensive after 2018 (`01` §8).

## 11. The Memory Hierarchy, Measured

`01` §2 and `06` §13 explain why caches exist and how access order changes hit rates.
Here is the hierarchy itself, measured: a pointer chase through a random cycle, so every
load depends on the previous one (§9) and the prefetcher can't guess the next address.
The time per load is the latency of whichever level the working set fits in.

```go
package main

import (
	"fmt"
	"math/rand"
	"time"
)

func main() {
	rng := rand.New(rand.NewSource(1))
	for _, kb := range []int{16, 32, 64, 256, 512, 1024, 2048, 8192, 32768, 65536, 262144} {
		n := kb * 1024 / 8
		perm := rng.Perm(n)
		next := make([]int, n)
		for i := 0; i < n; i++ { // one big cycle visiting every slot in random order
			next[perm[i]] = perm[(i+1)%n]
		}
		const steps = 20_000_000
		p := 0
		t := time.Now()
		for i := 0; i < steps; i++ {
			p = next[p]
		}
		ns := float64(time.Since(t).Nanoseconds()) / steps
		fmt.Printf("%8d KB  %6.2f ns/load  (p=%d)\n", kb, ns, p%2)
	}
}
```

```text
      16 KB    1.55 ns/load  (p=0)
      32 KB    1.55 ns/load  (p=1)
      64 KB    2.54 ns/load  (p=0)
     256 KB    4.21 ns/load  (p=0)
     512 KB    5.67 ns/load  (p=0)
    1024 KB    7.89 ns/load  (p=0)
    2048 KB   16.74 ns/load  (p=0)
    8192 KB  116.90 ns/load  (p=1)
   32768 KB  155.19 ns/load  (p=1)
   65536 KB  158.05 ns/load  (p=1)
  262144 KB  203.08 ns/load  (p=1)
```

(Printing `p` stops the compiler from deleting the loop as dead code.)

Reading the curve:

- **Up to 32 KB: 1.55 ns, about 4–5 cycles.** The working set fits in L1d (32 KB). That is L1
  latency.
- **64 KB – 1 MB: 2.5–8 ns.** Out of L1, into the 1 MB L2. The gradual climb rather than a
  step comes from the mix of L1 hits and L2 hits as the set outgrows L1, and from
  translation-cache (TLB) misses starting to appear.
- **2 MB: 17 ns.** Now in the shared L3.
- **8 MB and beyond: 117–203 ns — 75–130× slower than L1.** The climb starts well before
  the 33 MB L3 is full. Two causes on this machine: random 4 KB-page accesses outrun
  the second-level TLB's reach (1,536 entries × 4 KB ≈ 6 MB), so each load also walks the
  page table (`01` §5); and on a cloud VM the L3 is shared with other tenants. At
  256 MB almost every load is a RAM access plus a page walk.

The rules this gives you:

1. **Memory moves in 64-byte cache lines.** Touching one byte loads 64. Sequential
   access uses all 64; random access uses 8 and wastes 56. The labs below show the
   effect of order.
2. **Hardware prefetchers** detect sequential and strided access and fetch lines before
   you ask. Pointer chasing (linked lists, trees of heap objects, hash-map chains)
   defeats them; arrays feed them.
3. **Working-set size decides speed.** An algorithm whose hot data fits in L2 can be 10×
   faster than an equivalent one that doesn't — this is why B-trees use wide nodes, why
   column stores scan faster than row stores for analytics, and why "cache-oblivious"
   algorithms exist.
4. **Latency hides behind independence.** The chase above is slow because each load
   waits for the last. An array scan issues many loads at once (memory-level
   parallelism), so it sees bandwidth, not latency.

**Try it: feel the gap.** Switch between row order and column order through the same
array and watch the hit rate: same Big-O, very different cost.

<div class="lab" data-viz="cs-locality"></div>

Writes follow the same path: caches are **write-back** (a store updates the line in L1
and marks it dirty; RAM is updated only when the line is evicted), and caches are
**set-associative** (a given address can live in only a handful of slots, so power-of-two
strides can collide on the same set and thrash even a mostly empty cache).

## 12. SIMD, Multiple Cores, and Where Speed Comes From Today

Clock speeds stopped rising around 2005 (power and heat), so extra performance now
comes from doing more per cycle, not faster cycles:

- **SIMD** (single instruction, multiple data): vector registers hold 4, 8 or 16 values,
  and one instruction operates on all of them — SSE and AVX2 on x86 (AVX-512 on this
  machine), NEON and SVE on ARM. Compilers auto-vectorise simple loops; libraries such
  as NumPy, BLAS, `memchr`, JSON parsers (simdjson) and hash functions are built on it.
  This is a large part of why NumPy beats a Python loop by 100× — no interpreter, and
  eight values per instruction.
- **Multiple cores** give true parallelism, bounded by **Amdahl's law**: if a fraction
  *p* of the work parallelises across *N* cores, the speedup is 1 / ((1 − p) + p/N).
  With 95% parallel work, 8 cores give 5.9×, and even infinitely many cores give at most
  20×. The serial 5% dominates, so the first question in any parallelisation is "what
  can't be split?"
- **Simultaneous multithreading** (Hyper-Threading) runs two threads on one core's
  execution units, filling the gaps when one stalls on memory. It helps latency-bound
  code and does little for code already saturating the units. (This VM exposes one
  thread per core.)
- **Accelerators** — GPUs and TPUs — take SIMD to thousands of lanes for matrix math;
  that is the hardware behind modern ML ([ML and LLM Systems](../SystemDesign/building_blocks/23_ml_and_llm_systems.md)).

**What this means for how you write code**, in the order it usually matters:

1. Pick the right algorithm (`07`). Nothing here rescues O(n²) on a million items.
2. Pick data layouts that are contiguous and compact (§6, §11, `06` §13).
3. Keep hot loops free of unpredictable branches and long dependency chains (§9, §10).
4. Let libraries use SIMD for bulk numeric work; in Python, move the loop into C
   (NumPy, built-ins) rather than optimising the Python.
5. Parallelise last, after measuring what's serial.

## What Each Engineering Level Should Know

| Topic in this chapter | Junior / New Grad (Google L3) | Mid-Level (Google L4) | Senior (Google L5) | Staff+ (Google L6–L7) |
|---|---|---|---|---|
| **Binary, hex, two's complement** (§1–§2) | Converts between binary, hex and decimal; knows negatives exist in binary | Explains two's complement and the asymmetric range | Reasons about bit patterns when debugging dumps and protocols | Sets conventions for binary formats across systems |
| **Overflow and division** (§3) | Writes `lo + (hi - lo) / 2` | Knows wraparound and language differences in `/` and `%` | Spots overflow at language and system boundaries (JSON, DB, NumPy) | Designs ID and counter widths for decades of growth |
| **Bit manipulation** (§4) | Uses masks to test and set bits | Explains `x & (x-1)`, `x & -x`, XOR tricks | Uses bitmask DP and state encoding fluently | Chooses compact encodings (bitmaps, Roaring, bloom filters) for storage systems |
| **Floating point** (§5) | Knows floats are approximate; never `==` | Explains why 0.1 is inexact; uses relative tolerance and integer money | Explains non-associativity, cancellation, NaN, 2⁵³ limits | Sets numeric policy (decimal vs float, determinism across platforms) |
| **Endianness, alignment, UTF-8** (§6–§7) | Knows text has an encoding | Serialises explicitly; knows UTF-8 is variable width | Orders struct fields, normalises Unicode, avoids byte-index bugs | Defines wire formats and text-handling standards |
| **CPU execution** (§8–§10) | Knows code compiles to instructions | Knows interpreted vs compiled vs JIT | Explains latency vs throughput, pipelining, branch misprediction with numbers | Drives performance work from profiles and hardware counters |
| **Memory hierarchy, SIMD, Amdahl** (§11–§12) | Knows RAM is slower than cache | Knows cache lines and locality | Predicts cache behaviour of a data structure; applies Amdahl's law | Makes hardware-aware architecture calls (layout, batching, accelerators) |

**Reading this table as a study plan:** the Foundations and §1–§5 take you to the
Mid-Level column and cover almost every interview question about data representation.
§8–§12 are what separates a Senior answer to "why is this code slow?" from a guess.

## Interview checklist

- [ ] I can convert between binary, hex and decimal and explain two's complement, including why −128 has no positive partner.
- [ ] I can explain why `(lo + hi) / 2` overflows and why `abs(MIN_INT)` is negative.
- [ ] I can state how Python's `//` and `%` differ from Go/Java/C for negative numbers.
- [ ] I can explain `x & (x-1)`, `x & -x`, XOR cancellation and submask enumeration, and why each works.
- [ ] I can explain the IEEE 754 layout, why 0.1 + 0.2 ≠ 0.3, what epsilon and 2⁵³ mean, and why float addition isn't associative.
- [ ] I can say how to compare floats, why money shouldn't be a float, and what NaN does to comparisons.
- [ ] I can explain endianness, when it matters, and how padding changes a struct's size.
- [ ] I can explain UTF-8's encoding, the three meanings of "length", and why to normalise before comparing.
- [ ] I can describe fetch-decode-execute, pipelining, and latency vs throughput with a measured example.
- [ ] I can explain branch misprediction, why sorted data can run faster, and why branch-free code removes the effect.
- [ ] I can sketch the memory hierarchy with approximate latencies and explain cache lines, prefetching and working-set size.
- [ ] I can apply Amdahl's law and say where modern performance comes from (SIMD, cores, accelerators).

Related: [Operating Systems & Hardware Symbiosis](01_operating_systems_deep_dive.md) §2 (MESI, false sharing) and §5 (virtual memory, TLB), [Data Structure Internals](06_data_structure_internals_deep_dive.md) §13 (memory layout), [Complexity Analysis](07_complexity_analysis_deep_dive.md) §3 (hidden costs), [Memory Management & Garbage Collection](14_memory_management_deep_dive.md) (stack, heap, GC); DSA topics 20 (bit manipulation), 21 (math & geometry) and 26 (Fenwick trees).
