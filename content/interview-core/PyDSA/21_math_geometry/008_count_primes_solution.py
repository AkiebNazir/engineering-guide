"""
================================================================================
SOLUTION · LeetCode 204 · Count Primes                             [Medium]
https://leetcode.com/problems/count-primes/
================================================================================

THE CORE IDEA
--------------
Checking whether ONE number k is prime by trial division costs O(sqrt(k))
(only need to test divisors up to sqrt(k)); doing that independently for
every k from 2 to n-1 costs O(n * sqrt(n)) total -- and that's the wrong
algorithmic SHAPE for this problem, not just a slow constant. The Sieve
of Eratosthenes flips the question around: instead of asking "is k prime"
one number at a time, it asks "which numbers does THIS prime rule out,"
starting from the smallest prime (2) and crossing off every multiple of
it, then the next number not yet crossed off (3) and crossing off its
multiples, and so on up to sqrt(n). Every composite number gets crossed
off by its SMALLEST prime factor exactly (crossing-offs from larger prime
factors happen too, but the total crossing-off work across all primes up
to n is bounded by the harmonic-like sum `n/2 + n/3 + n/5 + n/7 + ...`
over primes, which sums to `O(n log log n))` -- a genuinely different,
smaller order of growth than `O(n sqrt(n))`, not just a faster constant
factor doing the same asymptotic amount of work.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (trial division per number, price it): for each k in 2..n-1,
test divisibility by every integer up to sqrt(k) (or, weaker still, up to
k-1). O(n * sqrt(n)) time for the sqrt(k) version, O(n^2) for the naive
up-to-k-1 version. Correct, but at n in the hundred-thousands this becomes
measurably, not just theoretically, slow -- demonstrated below.

Approach 1 (chosen) -- Sieve of Eratosthenes: allocate a boolean array
`is_prime[0..n-1]`, mark 0 and 1 as not prime, then for each i from 2 to
sqrt(n), if `is_prime[i]` is still True, mark every multiple of i (starting
from i*i, since smaller multiples of i were already crossed off by a
smaller prime factor) as not prime. Count the remaining True entries.
O(n log log n) time, O(n) space.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 10   (count primes strictly less than 10)

    is_prime = [F,F,T,T,T,T,T,T,T,T]   (indices 0..9; 0,1 pre-marked False)

    i=2 (is_prime[2]=True, 2*2=4 <= 9): cross off multiples of 2 starting
        at 4: 4,6,8 -> is_prime = [F,F,T,T,F,T,F,T,F,T]
    i=3 (is_prime[3]=True, 3*3=9 <= 9): cross off multiples of 3 starting
        at 9: 9 -> is_prime = [F,F,T,T,F,T,F,T,F,F]
    i=4: is_prime[4] already False, skip (4*4=16 > 9 anyway, loop would
        stop here regardless -- sqrt(9) ~= 3, so i only needs to reach 3)

    remaining True positions: 2, 3, 5, 7 -> count = 4

    matches example 1 (primes less than 10: 2, 3, 5, 7).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time             Space   Mutates input?
    ------------------------------------------------------------------------
    Trial division per number [priced] O(n*sqrt(n))    O(1)     no
    Sieve of Eratosthenes [chosen]     O(n log log n)  O(n)     no


================================================================================
EDGE CASES
================================================================================
    n == 0 or n == 1        -> "primes strictly less than n" is an empty
                             range when n <= 2 (n=0 and n=1 both have zero
                             candidates, since the smallest prime is 2);
                             must return 0 without the sieve array logic
                             misbehaving on a size-0 or size-1 array.
    n == 2                  -> also 0 (only candidate is 1, not prime).
    n == 3                  -> 1 (only 2 qualifies, strictly less than 3).
    largest n (5*10^6)      -> exactly the scale where the O(n sqrt(n))
                             vs O(n log log n) gap becomes real, not just
                             theoretical -- measured below.
    the number 1 itself     -> never prime (excluded by definition), must
                             be pre-marked False in the sieve, not left
                             for the "cross off multiples" loop to handle
                             (it never gets crossed off by anything, since
                             1 has no smaller prime factor).


================================================================================
COMMON MISTAKES
================================================================================
1. Starting the "cross off multiples of i" inner loop at `2*i` instead of
   `i*i` -- correct, just slower: `2*i, 3*i, ...` up to `(i-1)*i` were
   already crossed off by SMALLER primes before i was reached, so starting
   at `i*i` skips redundant work (this is a real optimization the sieve
   relies on for its stated complexity, not just cosmetic).
2. Off-by-one on the "strictly less than n" wording -- the problem counts
   primes < n, not <= n; a sieve array sized `n` with valid indices
   `0..n-1` naturally matches this if built carefully, but it's easy to
   accidentally include n itself.
3. Forgetting to pre-mark 0 and 1 as not prime -- both are automatically
   "True" if the array is initialized to all-True and never explicitly
   corrected, since neither ever gets crossed off as a multiple of
   anything smaller.
4. Iterating the outer sieve loop all the way to n instead of stopping at
   sqrt(n) -- correct either way (values beyond sqrt(n) that are still
   marked True are genuinely prime and don't need to sieve anything, since
   any composite <= n has a factor <= sqrt(n)), but stopping early is what
   gives the sieve its actual O(n log log n) bound instead of degrading
   toward O(n^2).


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you reduce the O(n) space?" -> A bit-array (or Python's
  `bytearray`) cuts the constant factor significantly (1 byte or even 1
  bit per entry instead of a full Python object per bool in a list);
  segmented sieving can further bound memory to O(sqrt(n)) at the cost of
  more bookkeeping, useful when n is too large to fit a full array in RAM.
- "Why is it safe to start crossing off at i*i instead of 2*i?" -> Because
  every multiple of i smaller than i*i has a factor smaller than i (e.g.
  `2*i`, `3*i`, ..., `(i-1)*i` all have a factor < i), and since the outer
  loop processes primes in increasing order, all of those were already
  crossed off when their smaller factor was processed.
- "What's the actual proof the sieve is O(n log log n)?" -> Sum over
  primes p <= n of `n/p` (the number of multiples of p up to n) equals
  `n * sum(1/p for primes p <= n)`, and the sum of reciprocals of primes
  up to n grows like `log log n` (Mertens' second theorem) -- hence
  `O(n log log n)` total.


================================================================================
RELATED PROBLEMS
================================================================================
- Factorial Trailing Zeroes (LC 172, this topic, 007) -- another "count
  something about numbers up to n without brute-force per-number checks"
  problem, solved via a factor-multiplicity formula instead of a sieve.
- Ugly Number II / Super Ugly Number -- related "generate/count numbers
  with restricted prime factors" family, though solved differently (via a
  merge/heap technique, not a sieve).
- Prime Factorization / Smallest Prime Factor sieve -- a common
  augmentation of this exact sieve that also records EACH number's
  smallest prime factor, useful for fast repeated factorization queries.
================================================================================
"""

import time


class Solution:
    def countPrimes(self, n: int) -> int:
        if n < 3:
            return 0

        is_prime = bytearray([1]) * n
        is_prime[0] = is_prime[1] = 0

        i = 2
        while i * i < n:
            if is_prime[i]:
                is_prime[i * i:n:i] = bytearray(len(range(i * i, n, i)))
            i += 1

        return sum(is_prime)


def _trial_division(n: int) -> int:
    """O(n*sqrt(n)) alternative, priced but not shipped, used only for the
    measured comparison demo below."""
    def is_prime_naive(k: int) -> bool:
        if k < 2:
            return False
        i = 2
        while i * i <= k:
            if k % i == 0:
                return False
            i += 1
        return True

    return sum(1 for k in range(n) if is_prime_naive(k))


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        (10, 4),
        (0, 0),
        (1, 0),
        (2, 0),
        (3, 1),
        (4, 2),
        (5, 2),
        (20, 8),
        (100, 25),
        (1000, 168),
    ]
    for n, expected in cases:
        got = sol.countPrimes(n)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  countPrimes({n}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- sieve vs trial division, n = 0..3000")
    print("-" * 72)
    mismatch = 0
    for n in range(0, 3001, 37):  # sampled, not every n, to keep this fast
        a = sol.countPrimes(n)
        b = _trial_division(n)
        if a != b:
            mismatch += 1
            if mismatch <= 3:
                print(f"  FAIL example: n={n} -> sieve={a}, trial_division={b}")
    checked = len(range(0, 3001, 37))
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {checked - mismatch}/{checked} agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- Sieve of Eratosthenes vs trial division, measured live")
    print("-" * 72)
    n = 200_000

    t0 = time.perf_counter()
    sieve_result = sol.countPrimes(n)
    sieve_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    trial_result = _trial_division(n)
    trial_ms = (time.perf_counter() - t0) * 1000

    print(f"n={n}:")
    print(f"  Sieve of Eratosthenes (O(n log log n)): {sieve_ms:8.2f} ms  -> {sieve_result} primes")
    print(f"  trial division per number (O(n*sqrt(n))): {trial_ms:8.2f} ms  -> {trial_result} primes")
    speedup = trial_ms / sieve_ms if sieve_ms > 0 else float("inf")
    print(f"  measured: the sieve is {speedup:.0f}x faster at n={n} -- a genuinely different "
          f"algorithmic shape, not just a faster constant, and the gap widens further as n grows.")
    demo_ok = sieve_result == trial_result
    all_ok &= demo_ok
    print(f"{'PASS' if demo_ok else 'FAIL'}  both approaches agree on the count ({sieve_result})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
