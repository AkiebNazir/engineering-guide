# Information Theory and Coding — Bits, Entropy, Compression and Error Correction

In 1948 Claude Shannon asked what "information" is, and answered with a number: the
**bit**, measured as reduced uncertainty. From that single idea come hard limits on how
far any file can be compressed, the loss function used to train nearly every classifier
(cross-entropy), how strong a password really is, and the codes that let a scratched CD,
a damaged QR code or a failed disk still return the right data. This chapter builds
information theory from twenty-questions games up to Huffman coding, cross-entropy, and
Hamming codes you can break and repair in the browser.

**Where this fits:** Part 4 · Maths behind computing, chapter 13 of 15. **Builds on:** [02 Number systems and binary](02_number_systems_and_binary.md) (bits); [07 Number theory](07_number_theory.md) (modular arithmetic); [10 Probability](10_probability.md) (probability). **Next in order:** [14 Automata, computability and complexity](14_automata_computability_complexity.md).

## Where You Will Use This

| Where | Information theory inside |
|---|---|
| gzip, zstd, PNG, video codecs | Entropy as the compression limit; Huffman / arithmetic coding |
| Classifiers and LLMs | Cross-entropy loss, perplexity, KL divergence |
| Decision trees, feature selection | Information gain |
| Passwords, keys, tokens | Entropy in bits = log₂(number of equally likely choices) |
| Networking, storage, memory | Parity, checksums, CRC, ECC RAM, RAID, Reed–Solomon |
| Logging and metrics | Why high-cardinality labels are expensive |

## Foundations — Information Is Surprise

A message tells you something when it **reduces your uncertainty**. "The sun rose today"
tells you almost nothing — you were sure. "It snowed in the Sahara" tells you a lot.

> **Analogy:** The game of twenty questions. Each yes/no answer can at best halve the
> remaining possibilities. **One bit is the information in the answer to a perfectly
> balanced yes/no question.** To identify one of 1,048,576 things you need 20 good
> questions, because $2^{20} = 1{,}048{,}576$ — the same logarithm as binary search
> (chapter 06).

> **Definition:** An outcome with probability p carries $\log_2 \frac{1}{p}$ bits of
> **information** (its "surprise"). Certain events (p = 1) carry 0 bits; a fair coin
> flip carries 1 bit; one of 8 equally likely outcomes carries 3 bits.

```python
import math
surprise = lambda p: math.log2(1 / p)
print(surprise(1 / 2), surprise(1 / 8), round(surprise(1 / 6), 3), round(surprise(1 / 52), 3))   # → 1.0 3.0 2.585 5.7
```

A die roll is worth about 2.585 bits; a card drawn from a deck, 5.7 bits. Information
from independent events adds, because logs turn products of probabilities into sums.

## 1 · Entropy: the Average Surprise

A source that emits symbols with probabilities $p_1, \dots, p_n$ produces, on average,

$$
H = \sum_i p_i \log_2 \frac{1}{p_i} \quad \text{bits per symbol}
$$

That is its **entropy**: the average information per symbol, or equivalently the average
number of yes/no questions needed to identify a symbol with the best possible strategy.

- It is largest when all outcomes are equally likely: $H = \log_2 n$.
- It is 0 when one outcome is certain.
- Skewed distributions have low entropy — they are predictable, and therefore
  compressible.

```python
import math
from collections import Counter

def entropy(probs):
    return sum(p * math.log2(1 / p) for p in probs if p > 0)

def text_entropy(s):
    n = len(s)
    return entropy([c / n for c in Counter(s).values()])

print(entropy([0.5, 0.5]), round(entropy([0.9, 0.1]), 3), entropy([0.25] * 4))   # → 1.0 0.469 2.0
print(round(text_entropy("abracadabra"), 3))                                       # → 2.04
```

A coin that lands heads 90% of the time carries only 0.469 bits per flip: most flips
tell you what you already expected.

> **In practice:** Entropy explains why **high-cardinality labels** hurt metrics systems
> and why a random 128-bit ID cannot be compressed, but a log line that is 95% the same
> template compresses 20-fold. Wherever something is predictable, there is redundancy to
> remove.

> **Notebook example:** A server log level is INFO half the time, WARN a quarter of the
> time, and ERROR and DEBUG an eighth each. How many bits per log level does it carry?
>
> 1. $H = \sum p \log_2 \frac1p$. The surprises are $\log_2 2 = 1$,
>    $\log_2 4 = 2$, $\log_2 8 = 3$ and $\log_2 8 = 3$.
> 2. Weight each by its probability: $\frac12 \cdot 1 + \frac14 \cdot 2 + \frac18 \cdot 3 + \frac18 \cdot 3$.
> 3. $= 0.5 + 0.5 + 0.375 + 0.375 = 1.75$ bits.
> 4. **Check** with yes/no questions: "INFO?" settles it half the time (1 question).
>    "WARN?" settles it a quarter of the time (2 questions). "ERROR?" settles the rest
>    (3 questions). On average $0.5 \cdot 1 + 0.25 \cdot 2 + 0.25 \cdot 3 = 1.75$. ✓
>
> **Answer:** 1.75 bits, less than the 2 bits a fixed-length code for 4 values uses.

## 2 · Compression: How Small Can a File Get?

> **Key idea:** **Shannon's source coding theorem** — you cannot losslessly compress
> symbols from a source below H bits per symbol on average, and you can get arbitrarily
> close to it. Entropy is the floor.

To compress, give **frequent symbols short codes and rare symbols long codes** (Morse code
already did this: E is `.`, Q is `--.-`). The codes must be decodable without separators,
which **prefix-free** codes guarantee: no code is the beginning of another, so the
decoder always knows where one symbol ends.

### Huffman coding

Huffman's algorithm (1952, from a student's term paper) builds the optimal prefix code:
repeatedly merge the two least frequent symbols into one node whose frequency is their
sum; the code of a symbol is the path from the root (left = 0, right = 1).

**Try it: build the tree.** Press *Build the tree* on "abracadabra" and watch the two
rarest nodes merge at each step. Frequent `a` ends near the root with a 1-bit code; the
rare letters get 3 bits. Compare the chips: fixed-length, Huffman, and the entropy
floor. Try *all equal* (Huffman cannot beat fixed length) and *skewed* (it wins big).

<div class="lab" data-viz="math-huffman"></div>

```python
import heapq
from collections import Counter

def huffman_codes(text):
    freq = Counter(text)
    heap = [(f, i, ch) for i, (ch, f) in enumerate(sorted(freq.items()))]
    heapq.heapify(heap)
    counter = len(heap)
    while len(heap) > 1:
        f1, _, a = heapq.heappop(heap)          # the two least frequent
        f2, _, b = heapq.heappop(heap)
        heapq.heappush(heap, (f1 + f2, counter, (a, b)))
        counter += 1
    codes = {}
    def walk(node, code):
        if isinstance(node, str):
            codes[node] = code or "0"
        else:
            walk(node[0], code + "0")
            walk(node[1], code + "1")
    walk(heap[0][2], "")
    return codes

text = "abracadabra"
codes = huffman_codes(text)
bits = "".join(codes[c] for c in text)
print(len(bits), 8 * len(text))                                  # → 23 88
print(sorted((ch, len(code)) for ch, code in codes.items()))     # → [('a', 1), ('b', 3), ('c', 3), ('d', 3), ('r', 3)]
```

23 bits instead of 88 as ASCII, against an entropy floor of 11 × 2.04 ≈ 22.4 bits.
Huffman is within one bit per symbol of the entropy; **arithmetic coding** and **ANS**
(used in zstd) get even closer by not rounding each code to whole bits.

> **Notebook example:** Huffman-code the string AAAAABBCD by hand.
>
> 1. Counts: A 5, B 2, C 1, D 1.
> 2. Merge the two smallest, C (1) and D (1), into a node of weight 2.
> 3. Now the smallest are B (2) and CD (2). Merge them into a node of weight 4.
> 4. Merge that node (4) with A (5) to get the root (9).
> 5. Read the codes off the paths (left 0, right 1): A = `0`, B = `10`, C = `110`,
>    D = `111`.
> 6. Total bits: $5 \times 1 + 2 \times 2 + 1 \times 3 + 1 \times 3 = 15$. A fixed 2-bit
>    code needs $9 \times 2 = 18$.
>
> **Answer:** 15 bits. The entropy floor is $9 \times 1.66 \approx 14.9$ bits, so Huffman
> is within a fraction of a bit here. **Check** the prefix rule: no code is the start of
> another (0, 10, 110, 111). ✓

### Real compressors, and what cannot be compressed

Practical compressors first remove **repetition** (LZ77 replaces a repeated substring
with "copy 12 bytes from 300 back"), then entropy-code what is left — DEFLATE (gzip, zip,
PNG) is LZ77 followed by Huffman. And by the counting argument in chapter 04, no
compressor can shrink **every** input: random data has maximal entropy and does not
compress at all.

```python
import zlib, random
random.seed(0)
repetitive = b"GET /api/v1/users 200 12ms\n" * 1000
noise = bytes(random.getrandbits(8) for _ in range(len(repetitive)))
r1 = len(zlib.compress(repetitive, 9)) / len(repetitive)
r2 = len(zlib.compress(noise, 9)) / len(noise)
print(r1 < 0.01, r2 > 1.0)   # → True True
```

The repeated log line shrinks to under 1% of its size; the random bytes come out slightly
**larger** (the format adds headers) — which is why you should not compress data that is
already compressed or encrypted.

## 3 · Cross-Entropy and KL Divergence: How Wrong Is a Model?

Suppose the true distribution is P but you encode (or predict) using a model Q. The
average number of bits you then spend is the **cross-entropy**

$$
H(P, Q) = \sum_i p_i \log_2 \frac{1}{q_i} \;\ge\; H(P)
$$

and the excess, $D_{KL}(P \,\|\, Q) = H(P, Q) - H(P)$, is the **Kullback–Leibler
divergence**: the cost of believing Q when the truth is P. It is zero only when Q = P.

> **In practice:** Training a classifier minimises cross-entropy between the true labels
> (P puts all its mass on the right class) and the model's predicted probabilities Q.
> For one example that is just $-\log q_{\text{correct}}$ — the **log loss**. Confident
> and right costs almost nothing; confident and wrong costs a lot. A language model's
> **perplexity** is $2^{\text{cross-entropy}}$: "on average, as uncertain as choosing
> among this many words".

```python
import math
log_loss = lambda q_correct: -math.log(q_correct)          # natural log, as ML libraries use
print([round(log_loss(q), 3) for q in (0.99, 0.6, 0.1, 0.01)])   # → [0.01, 0.511, 2.303, 4.605]

def kl(P, Q):
    return sum(p * math.log2(p / q) for p, q in zip(P, Q) if p > 0)
print(round(kl([0.5, 0.5], [0.9, 0.1]), 3), round(kl([0.9, 0.1], [0.5, 0.5]), 3))   # → 0.737 0.531
```

> **Notebook example:** The truth is 50/50 rain, but a model says 80% rain. Find the
> cross-entropy, the KL divergence, and the log loss of two predictions.
>
> 1. Entropy of the truth: $H(P) = 0.5 \log_2 2 + 0.5 \log_2 2 = 1$ bit.
> 2. Cross-entropy: $0.5 \log_2 \frac{1}{0.8} + 0.5 \log_2 \frac{1}{0.2} = 0.5 \times 0.322 + 0.5 \times 2.322 = 1.322$ bits.
> 3. KL $= 1.322 - 1 = 0.322$ bits wasted per day by believing the model.
> 4. Log loss when the right answer was given probability 0.9: $-\ln 0.9 \approx 0.105$.
>    When it was given 0.1: $-\ln 0.1 \approx 2.303$.
>
> **Answer:** 1.322 bits, 0.322 bits, and a 22 times bigger loss for the confident wrong
> prediction.

KL divergence is **not symmetric** — it is not a distance.

**Try it: drag P and Q.** Move the bars of the true distribution P and the model Q, and
watch entropy, cross-entropy and KL respond. Cross-entropy is always at least the
entropy; the gap is the KL divergence.

<div class="lab" data-viz="entropy"></div>

### Information gain in decision trees

A decision tree chooses the question that most reduces entropy. **Information gain** is
the entropy of the labels before a split minus the weighted entropy after it.

```python
import math
from collections import Counter

H = lambda labels: sum((c / len(labels)) * math.log2(len(labels) / c) for c in Counter(labels).values())
labels = ["spam"] * 5 + ["ham"] * 5
split_on_link = (["spam"] * 4 + ["ham"] * 1, ["spam"] * 1 + ["ham"] * 4)
after = sum(len(g) / len(labels) * H(g) for g in split_on_link)
print(H(labels), round(H(labels) - after, 3))   # → 1.0 0.278
```

"Contains a link?" turns a 50/50 mix (1 bit of uncertainty) into two 80/20 groups,
gaining 0.278 bits. The tree picks the feature with the largest gain, then recurses.

## 4 · Entropy of Secrets: Passwords and Keys

For a secret chosen **uniformly at random** from N possibilities, the entropy is
$\log_2 N$ bits, and an attacker needs about $2^{H-1}$ guesses on average. The word
"random" is doing all the work: a human-chosen password drawn from a small set of
likely patterns has far less entropy than its length suggests.

```python
import math
bits = lambda N: round(math.log2(N), 1)
print(bits(26**8), bits(62**12), bits(7776**6), bits(2**128))   # → 37.6 71.5 77.5 128.0
```

Eight random lowercase letters: 37.6 bits. Six random words from a 7,776-word
Diceware list: 77.5 bits — stronger, and far easier to remember. A 128-bit random key
is beyond brute force for any conceivable attacker.

> **Notebook example:** How many bits of entropy do these secrets have: a 4-digit PIN, 10
> random printable characters (94 symbols), and 4 Diceware words? How long does the
> Diceware phrase last at $10^{10}$ guesses per second?
>
> 1. PIN: $\log_2 10^4 = 4 \times 3.32 = 13.3$ bits, and 5,000 guesses on average.
> 2. Characters: $10 \times \log_2 94 = 10 \times 6.55 = 65.5$ bits.
> 3. Diceware: $4 \times \log_2 7776 = 4 \times 12.9 = 51.7$ bits.
> 4. An average attack tries half the space: $2^{51.7} / 2 \approx 1.8 \times 10^{15}$
>    guesses. At $10^{10}$ per second, that is $1.8 \times 10^5$ s, about **2 days**.
>
> **Answer:** 13.3, 65.5 and 51.7 bits. Four words fall in days against a fast hash, and
> six words (77.5 bits) take millions of years. Each extra bit doubles the attacker's
> work.

## 5 · Detecting Errors

Bits get flipped — by noise on a wire, cosmic rays in RAM, wear on a disk. To notice,
add redundancy.

- **Parity bit:** append one bit making the number of 1s even. Detects any single flipped
  bit (any odd number), misses two.
- **Checksums** (sums of the data mod some number) catch many errors cheaply; TCP and IP
  use a 16-bit ones'-complement sum.
- **CRC** (cyclic redundancy check) treats the data as a polynomial over bits and keeps
  the remainder after dividing by a fixed polynomial (arithmetic mod 2 — XOR instead of
  subtraction). CRC-32 detects every burst error up to 32 bits long. Ethernet, zip, PNG
  and most storage formats use CRCs.

```python
import zlib
data = bytearray(b"transfer 100 to alice")
good = zlib.crc32(data)
data[9] ^= 0b00000100                     # one flipped bit: "100" becomes "500"
print(bytes(data), zlib.crc32(data) == good)   # → b'transfer 500 to alice' False
```

> **Notebook example:** Add even parity to `1011001`, then check what the receiver sees
> after one flip and after two flips. Then compute a 3-bit CRC of `1101` with the
> generator `1011`.
>
> 1. `1011001` has four 1s, which is already even, so the parity bit is 0: send
>    `10110010`.
> 2. One flip, giving `10100010`: three 1s, which is odd. **Detected.**
> 3. Two flips, giving `10100011`: four 1s, which is even. **Missed.** Parity catches
>    odd numbers of errors only.
> 4. CRC: append 3 zeros to get `1101000`. Divide with XOR instead of subtraction:
>    `1101 ⊕ 1011 = 0110`. Bring down the next bit to get `1100`, and
>    `1100 ⊕ 1011 = 0111`. Bring down the next bit to get `1110`, and
>    `1110 ⊕ 1011 = 0101`. Bring down the last bit to get `1010`, and
>    `1010 ⊕ 1011 = 0001`.
> 5. The remainder is `001`. Send `1101 001`. The receiver divides again and expects
>    remainder 0.
>
> **Answer:** parity bit 0 (catches 1 flip, misses 2), and CRC remainder `001`.

> **Key idea:** The **Hamming distance** between two codewords is the number of bit
> positions where they differ. If every pair of valid codewords is at distance at least
> d, the code **detects** up to d − 1 errors (a corrupted word cannot turn into another
> valid one) and **corrects** up to ⌊(d − 1)/2⌋ (the corrupted word is still closest to
> the original). Parity gives d = 2: detect 1, correct 0.

> **Watch out:** Checksums and CRCs detect **accidents**, not attackers. Anyone can
> modify data and recompute the CRC. For tamper detection use a cryptographic MAC or
> signature.

## 6 · Correcting Errors

### Hamming(7,4): three parity bits locate the error

Richard Hamming, tired of weekend jobs that crashed on a single bad bit, designed a code
where every single-bit error announces its own position. Four data bits get three parity
bits, each covering an overlapping subset; a flipped bit breaks exactly the parity checks
that cover it, and the pattern of broken checks, read as a binary number, **is** the
position.

**Try it: break a bit, watch it heal.** Set the data bits, then click any bit in the
received row. The circles with odd parity turn red, the syndrome points at the flipped
bit, and the decoder restores the message. Now flip two bits: the syndrome points at an
innocent third bit and the "correction" makes it worse — distance 3 corrects one error,
not two.

<div class="lab" data-viz="math-hamming"></div>

```python
def encode(d1, d2, d3, d4):
    p1, p2, p3 = d1 ^ d2 ^ d4, d1 ^ d3 ^ d4, d2 ^ d3 ^ d4
    return [p1, p2, d1, p3, d2, d3, d4]           # positions 1..7

def decode(r):
    s1 = r[0] ^ r[2] ^ r[4] ^ r[6]                # checks positions 1,3,5,7
    s2 = r[1] ^ r[2] ^ r[5] ^ r[6]                # 2,3,6,7
    s3 = r[3] ^ r[4] ^ r[5] ^ r[6]                # 4,5,6,7
    pos = s1 + 2 * s2 + 4 * s3
    r = r[:]
    if pos:
        r[pos - 1] ^= 1
    return [r[2], r[4], r[5], r[6]], pos

word = encode(1, 0, 1, 1)
print(word)                                        # → [0, 1, 1, 0, 0, 1, 1]
ok = all(decode(word[:i] + [word[i] ^ 1] + word[i + 1:])[0] == [1, 0, 1, 1] for i in range(7))
print(ok)                                          # → True
```

Every one of the 7 possible single-bit errors is corrected. ECC memory in servers uses an
extended version (SECDED: single-error correction, double-error detection) on every
64-bit word.

> **Notebook example:** Encode the data bits 1011 with Hamming(7,4). Then flip position 5
> and decode.
>
> 1. With $d_1 d_2 d_3 d_4 = 1, 0, 1, 1$:
>    $p_1 = d_1 \oplus d_2 \oplus d_4 = 1 \oplus 0 \oplus 1 = 0$,
>    $p_2 = d_1 \oplus d_3 \oplus d_4 = 1 \oplus 1 \oplus 1 = 1$ and
>    $p_3 = d_2 \oplus d_3 \oplus d_4 = 0 \oplus 1 \oplus 1 = 0$.
> 2. The codeword, positions 1 to 7 ($p_1, p_2, d_1, p_3, d_2, d_3, d_4$), is `0110011`.
> 3. Flip position 5 to receive `0110111`.
> 4. Check the circles: $s_1$ = positions 1, 3, 5, 7 = $0 \oplus 1 \oplus 1 \oplus 1 = 1$.
>    $s_2$ = positions 2, 3, 6, 7 = $1 \oplus 1 \oplus 1 \oplus 1 = 0$.
>    $s_3$ = positions 4, 5, 6, 7 = $0 \oplus 1 \oplus 1 \oplus 1 = 1$.
> 5. Read the syndrome as binary, $s_3 s_2 s_1 = 101_2 = 5$. Flip position 5 back.
>
> **Answer:** the error announced its own position, 5, and the data 1011 is recovered.

### Stronger codes, and a code you already use: RAID

**Reed–Solomon** codes work on bytes instead of bits and correct bursts: a QR code
survives up to 30% damage, and CDs play through scratches. **Erasure codes** — where you
know *which* piece is missing — are simplest of all. RAID-5 stores the XOR of the data
disks on a parity disk; if any one disk dies, XOR the survivors to rebuild it, because
$a \oplus b \oplus (a \oplus b) = 0$.

```python
disks = [b"\x10\x20\x30", b"\x0a\x0b\x0c", b"\xff\x00\x7f"]
parity = bytes(x ^ y ^ z for x, y, z in zip(*disks))
lost = 1                                                          # disk 1 fails
survivors = [d for i, d in enumerate(disks) if i != lost] + [parity]
rebuilt = bytes(a ^ b ^ c for a, b, c in zip(*survivors))
print(rebuilt == disks[lost])                                     # → True
```

> **Notebook example:** Three data disks hold `1010`, `0111` and `1100`. Compute the
> parity disk, then rebuild disk 2 after it fails.
>
> 1. Parity $= 1010 \oplus 0111 \oplus 1100$. First $1010 \oplus 0111 = 1101$, then
>    $1101 \oplus 1100 = 0001$.
> 2. Disk 2 dies. XOR everything that survived:
>    $1010 \oplus 1100 \oplus 0001 = 0110 \oplus 0001 = 0111$.
>
> **Answer:** parity `0001`, and disk 2 rebuilt as `0111`. ✓ It works because every
> surviving value appears twice in the combined XOR and cancels, leaving only the lost
> one.

Cloud object stores use Reed–Solomon erasure codes across servers — for example 10 data
plus 4 parity pieces, surviving any 4 failures for 40% overhead instead of the 200% of
keeping three full copies. The System Design erasure-coding lab lets you compare the
two:

<div class="lab" data-viz="sd-erasure"></div>

## Common Mistakes

1. **Treating length as strength** for human-chosen passwords; entropy needs randomness.
2. **Compressing already-compressed or encrypted data.**
3. **Using a CRC or checksum for security.**
4. **Reading KL divergence as a distance** (it is not symmetric).
5. **Forgetting that log base sets the unit:** log₂ gives bits, ln gives "nats" (ML
   libraries use ln).
6. **Assuming a code corrects more errors than its distance allows** (Hamming(7,4)
   silently miscorrects two errors).

## Check Yourself

**1.** A service has 4 equally common status codes. How many bits per status? What if
one status is 97% of traffic and the others 1% each?

<details>
<summary>Open the answer</summary>

Uniform: $\log_2 4 = 2$ bits. Skewed:
$0.97\log_2\frac{1}{0.97} + 3 \cdot 0.01\log_2 100 \approx 0.043 + 0.199 = 0.24$ bits —
about 8× more compressible.

</details>

**2.** Why can Huffman coding not get below 1 bit per symbol, and what fixes that?

<details>
<summary>Open the answer</summary>

Every symbol gets a whole number of bits, at least 1. For a source like the 90/10 coin
(0.469 bits of entropy) that wastes half the space. Coding blocks of symbols together,
or arithmetic coding / ANS (fractional bits per symbol), approaches the entropy.

</details>

**3.** A classifier predicts the correct class with probability 0.2 on one example. What
is its log loss? Why is predicting 0.0 catastrophic?

<details>
<summary>Open the answer</summary>

$-\ln 0.2 \approx 1.61$. Predicting 0 for the true class gives $-\ln 0 = \infty$: an
infinite loss for one confident mistake. That is why models output probabilities
through a softmax (never exactly 0) and why libraries clip probabilities.

</details>

**4.** A code's valid words are all at Hamming distance ≥ 5 from each other. How many
errors can it detect? Correct?

<details>
<summary>Open the answer</summary>

Detect up to 4; correct up to ⌊4/2⌋ = 2.

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **Getting started** | Bits as answers to yes/no questions; $\log_2$ of the number of choices; entropy as average surprise; parity bits |
| **Interview-ready** | Entropy as the compression limit; Huffman coding; why random data does not compress; cross-entropy as ML loss; password entropy; CRC vs cryptographic hash; Hamming distance and what it detects/corrects; RAID XOR recovery |
| **Going deeper** | Source coding theorem, arithmetic coding and ANS; KL divergence and mutual information; channel capacity; Reed–Solomon and erasure-coded storage |

## Checklist

- [ ] I can compute the information in an outcome and the entropy of a distribution.
- [ ] I can explain why entropy is a lower bound for lossless compression.
- [ ] I can build a Huffman code by hand and explain why it is prefix-free.
- [ ] I can explain cross-entropy loss and perplexity.
- [ ] I can compute password/key entropy — and know when the formula does not apply.
- [ ] I know what parity, checksums and CRCs detect, and what they do not.
- [ ] I can explain how Hamming(7,4) locates an error and how RAID-5 rebuilds a disk.
