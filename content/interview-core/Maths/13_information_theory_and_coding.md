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
> **What you need:** **entropy** is the average surprise:
> $H = \sum_i p_i \log_2 \frac{1}{p_i}$. For each outcome, take its probability p, work
> out its surprise $\log_2 \frac{1}{p}$, multiply the two, and add over all outcomes.
> $\log_2 N$ ("log base 2 of N") answers "how many times do I double 1 to reach N?", or
> equally "how many yes/no questions halve N things down to one?". So $\log_2 2 = 1$,
> $\log_2 4 = 2$ and $\log_2 8 = 3$, because $2 = 2^1$, $4 = 2^2$ and $8 = 2^3$.
>
> **Plan:** find each level's surprise, weight it by how often that level happens, and add.
>
> 1. **List the probabilities.** INFO $\frac12$, WARN $\frac14$, ERROR $\frac18$, DEBUG
>    $\frac18$. They add to 1, as they must.
> 2. **Flip each probability.** $\frac1p$ is 2, 4, 8 and 8.
>    *Why:* "one in 8" is more surprising than "one in 2", and $\frac1p$ is that "one
>    in ..." number.
> 3. **Take log₂ of each.** $\log_2 2 = 1$, $\log_2 4 = 2$, $\log_2 8 = 3$ and
>    $\log_2 8 = 3$. These are the surprises, in bits.
> 4. **Weight each surprise by its probability.** $\frac12 \cdot 1 = 0.5$,
>    $\frac14 \cdot 2 = 0.5$, $\frac18 \cdot 3 = 0.375$ and $\frac18 \cdot 3 = 0.375$.
>    *Why:* rare levels are very surprising but seldom happen, so they count for less in
>    the average.
> 5. **Add them up.** $0.5 + 0.5 = 1$, then $1 + 0.375 = 1.375$, then
>    $1.375 + 0.375 = 1.75$.
>
> **Answer:** 1.75 bits per log level, less than the 2 bits a fixed-length code for 4
> values uses. A clever code can save 0.25 bits per line.
>
> **Check:** play twenty questions. Ask "INFO?" first: that settles it half the time
> (1 question). Then "WARN?": that settles it a quarter of the time (2 questions). Then
> "ERROR?": that settles the last quarter (3 questions). On average
> $0.5 \cdot 1 + 0.25 \cdot 2 + 0.25 \cdot 3 = 0.5 + 0.5 + 0.75 = 1.75$. ✓ The `entropy`
> function above gives the same: `entropy([0.5, 0.25, 0.125, 0.125])` is 1.75.

> **Your turn:** A health check returns OK half the time, SLOW a quarter of the time and
> FAIL a quarter of the time. What is its entropy?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **List the probabilities.** $\frac12$, $\frac14$, $\frac14$.
> 2. **Flip each probability.** 2, 4, 4.
> 3. **Take log₂ of each.** 1, 2, 2.
> 4. **Weight each surprise by its probability.** $\frac12 \cdot 1 = 0.5$,
>    $\frac14 \cdot 2 = 0.5$ and $\frac14 \cdot 2 = 0.5$.
> 5. **Add them up.** $0.5 + 0.5 + 0.5 = 1.5$.
>
> **Answer:** 1.5 bits per health check.
>
> </details>

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

> **Notebook example:** Huffman-code the string AAAAABBCD by hand. How many bits does it
> take?
>
> **What you need:** Huffman's algorithm builds a **tree** (a branching diagram) from the
> bottom up. Start with one **node** (a box) per letter, labelled with its count, called
> its **weight**. Repeatedly join the two lightest nodes under a new node whose weight is
> their sum, until one node, the **root**, is left. Then each letter's code is the path
> from the root down to it: write 0 for every step left and 1 for every step right. The
> result is **prefix-free**: no code is the start of another, so the decoder always
> knows where one letter ends.
>
> **Plan:** count the letters, merge the two lightest nodes one merge at a time, read the
> codes off the tree, then add up the bits.
>
> 1. **Count each letter.** A 5, B 2, C 1, D 1. That is 9 letters in all.
> 2. **Merge the two lightest: C and D.** Both weigh 1. Join them under a new node CD of
>    weight $1 + 1 = 2$. The nodes left are A 5, B 2, CD 2.
>    *Why:* the rarest letters end up deepest in the tree, so they get the longest codes.
> 3. **Merge the two lightest: B and CD.** Both weigh 2. Join them under a new node BCD
>    of weight $2 + 2 = 4$. The nodes left are A 5, BCD 4.
> 4. **Merge the last two: A and BCD.** Join them under the root, of weight
>    $5 + 4 = 9$. Only one node is left, so the tree is finished.
> 5. **Label the branches.** At the root, A is on the left (0) and BCD on the right (1).
>    Under BCD, B is left (0) and CD right (1). Under CD, C is left (0) and D right (1).
>    *Why:* which side gets 0 is a free choice; any choice gives codes of the same
>    lengths.
> 6. **Read each code from the root down.** A = `0`. B = `1` then `0` = `10`.
>    C = `1`, `1`, `0` = `110`. D = `111`.
> 7. **Count the bits per letter.** A: $5 \times 1 = 5$. B: $2 \times 2 = 4$.
>    C: $1 \times 3 = 3$. D: $1 \times 3 = 3$.
> 8. **Add them up.** $5 + 4 + 3 + 3 = 15$ bits.
> 9. **Compare with a fixed-length code.** Four letters need 2 bits each (`00`, `01`,
>    `10`, `11`), so $9 \times 2 = 18$ bits.
>
> **Answer:** 15 bits instead of 18. The entropy floor is $9 \times 1.66 \approx 14.9$
> bits, so Huffman is within a fraction of a bit of the best possible here.
>
> **Check:** the prefix rule holds: none of `0`, `10`, `110`, `111` is the start of
> another. ✓ Running `huffman_codes("AAAAABBCD")` above gives the same code lengths
> (1 bit for A, 2 for B, 3 for C and D); only the choice of which side is 0 differs. ✓

> **Your turn:** Huffman-code the string AAABBC. How many bits does it take?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Count each letter.** A 3, B 2, C 1. That is 6 letters.
> 2. **Merge the two lightest: C and B.** $1 + 2 = 3$. The nodes left are A 3, BC 3.
> 3. **Merge the last two: A and BC.** $3 + 3 = 6$: the root.
> 4. **Label the branches and read the codes.** A = `0`, B = `10`, C = `11`.
> 5. **Count the bits per letter.** A: $3 \times 1 = 3$. B: $2 \times 2 = 4$.
>    C: $1 \times 2 = 2$.
> 6. **Add them up.** $3 + 4 + 2 = 9$ bits, against $6 \times 2 = 12$ for a fixed 2-bit
>    code.
>
> **Answer:** 9 bits.
>
> </details>

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

> **Notebook example:** The truth is 50/50 rain or dry, but a model says 80% rain and
> 20% dry. How many bits per day are wasted by believing the model?
>
> **What you need:** the true distribution P is (rain 0.5, dry 0.5); the model Q is
> (rain 0.8, dry 0.2). **Cross-entropy** $H(P, Q) = \sum_i p_i \log_2 \frac{1}{q_i}$ is
> the average number of bits you spend when reality follows P but your code is built
> for Q: the true probability $p_i$ sits outside the log, the model's $q_i$ inside. The
> **KL divergence** is the waste: $D_{KL} = H(P, Q) - H(P)$, cross-entropy minus the true
> entropy. $\log_2 x$ is "the power you raise 2 to in order to get x"; for awkward
> numbers use a calculator or `math.log2`.
>
> **Plan:** find the true entropy, find the cross-entropy one term at a time, then
> subtract.
>
> 1. **Find the entropy of the truth.** $\frac{1}{0.5} = 2$ and $\log_2 2 = 1$, so each
>    outcome contributes $0.5 \times 1 = 0.5$. In total $H(P) = 0.5 + 0.5 = 1$ bit.
> 2. **Cross-entropy, rain term: flip the model's probability.** $\frac{1}{0.8} = 1.25$.
> 3. **Take log₂.** $\log_2 1.25 \approx 0.322$.
>    *Why:* 1.25 is less than 2, so you double less than once to reach it: under 1 bit.
> 4. **Weight by the true probability.** $0.5 \times 0.322 = 0.161$.
> 5. **Cross-entropy, dry term: flip the model's probability.** $\frac{1}{0.2} = 5$.
> 6. **Take log₂.** $\log_2 5 \approx 2.322$.
>    *Why:* $2^2 = 4$ and $2^3 = 8$, so the answer is between 2 and 3.
> 7. **Weight by the true probability.** $0.5 \times 2.322 = 1.161$.
> 8. **Add the two terms.** $H(P, Q) = 0.161 + 1.161 = 1.322$ bits.
> 9. **Subtract the true entropy.** $D_{KL} = 1.322 - 1 = 0.322$ bits.
>
> **Answer:** believing the model costs 1.322 bits per day instead of 1, so 0.322 bits per
> day are wasted. That waste is the KL divergence.
>
> **Check:** `kl([0.5, 0.5], [0.8, 0.2])`, with the `kl` function above, gives 0.322. ✓
> And the cross-entropy (1.322) is at least the entropy (1), as it must always be. ✓

> **Your turn:** The truth is still 50/50, but the model says 75% rain and 25% dry. Find
> the cross-entropy and the KL divergence. ($\log_2 \frac{1}{0.75} \approx 0.415$.)
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the entropy of the truth.** $H(P) = 1$ bit, as before.
> 2. **Rain term.** $\frac{1}{0.75} \approx 1.333$, $\log_2 1.333 \approx 0.415$, and
>    $0.5 \times 0.415 \approx 0.208$.
> 3. **Dry term.** $\frac{1}{0.25} = 4$, $\log_2 4 = 2$, and $0.5 \times 2 = 1$.
> 4. **Add the two terms.** $H(P, Q) \approx 0.208 + 1 = 1.208$ bits.
> 5. **Subtract the true entropy.** $D_{KL} \approx 1.208 - 1 = 0.208$ bits.
>
> **Answer:** cross-entropy about 1.208 bits, KL divergence about 0.208 bits. This model is
> less wrong than the 80/20 one, so it wastes less.
>
> </details>

> **Notebook example:** The right answer is "rain". One model gave rain probability 0.9;
> another gave it only 0.1. Find each model's log loss.
>
> **What you need:** the **log loss** of one prediction is $-\ln q$, where q is the
> probability the model gave to the answer that turned out to be correct. $\ln$ is the
> natural logarithm (log base $e \approx 2.718$), which ML libraries use; its unit is
> "nats" instead of bits. Since $-\ln q = \ln \frac{1}{q}$, it is the same "surprise" idea
> as before.
>
> **Plan:** flip each q, take its natural log, and compare the two.
>
> 1. **Flip the confident, right prediction.** $\frac{1}{0.9} \approx 1.111$.
> 2. **Take ln.** $\ln 1.111 \approx 0.105$.
>    *Why:* the model was nearly sure and right, so it is barely surprised: a tiny loss.
> 3. **Flip the confident, wrong prediction.** $\frac{1}{0.1} = 10$.
> 4. **Take ln.** $\ln 10 \approx 2.303$.
> 5. **Compare them.** $2.303 \div 0.105 \approx 22$.
>
> **Answer:** 0.105 for the good model and 2.303 for the bad one: about 22 times bigger
> loss for the confident wrong prediction. Training pushes hard against being confidently
> wrong.
>
> **Check:** the `log_loss` line above prints 2.303 for 0.1, and `-math.log(0.9)` is
> 0.10536. ✓

> **Your turn:** Find the log loss when the correct answer was given probability 0.5, and
> when it was given 0.01.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Flip the first prediction.** $\frac{1}{0.5} = 2$.
> 2. **Take ln.** $\ln 2 \approx 0.693$.
> 3. **Flip the second prediction.** $\frac{1}{0.01} = 100$.
> 4. **Take ln.** $\ln 100 \approx 4.605$.
>
> **Answer:** 0.693 for a 50/50 guess, and 4.605 for being 99% sure of the wrong answer.
>
> </details>

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

> **Notebook example:** A 4-digit PIN is chosen at random. How many bits of entropy does
> it have, and how many guesses does an attacker need on average?
>
> **What you need:** a secret picked **uniformly at random** (every option equally
> likely) from N possibilities has $\log_2 N$ bits of entropy. $\log_2 N$ is "how many
> times you must double 1 to reach N", which is also the number of bits needed to number
> N things. Two helpful facts: when choices are made one after another, the counts
> **multiply**; and $\log_2$ of a power is the power times the log, so
> $\log_2 10^4 = 4 \times \log_2 10$. On average an attacker finds the secret after
> trying half of the possibilities.
>
> **Plan:** count the possible PINs, turn the count into bits, then halve the count.
>
> 1. **Count the choices for one digit.** 0 to 9: 10 choices.
> 2. **Multiply for four digits.** $10 \times 10 \times 10 \times 10 = 10^4 = 10{,}000$.
>    *Why:* each of the 10 first digits can pair with each of the 10 second digits, and
>    so on.
> 3. **Bracket it between powers of 2.** $2^{13} = 8{,}192$ and $2^{14} = 16{,}384$, so
>    10,000 sits between them and the answer is between 13 and 14 bits.
> 4. **Work out the exact log.** $\log_2 10 \approx 3.32$, so
>    $\log_2 10^4 = 4 \times 3.32 \approx 13.3$ bits.
> 5. **Halve the count for the average attack.** $10{,}000 \div 2 = 5{,}000$ guesses.
>    *Why:* the right PIN is equally likely to be anywhere in the list, so on average it
>    turns up halfway through.
>
> **Answer:** 13.3 bits, and 5,000 guesses on average. A computer tries that in well
> under a second, which is why PINs rely on lock-outs after a few wrong tries.
>
> **Check:** `math.log2(10**4)` prints 13.29. ✓ And $2^{13.3}$ should be close to
> 10,000: $2^{13} = 8{,}192$, and the extra 0.3 multiplies by about 1.23, giving about
> 10,000. ✓

> **Your turn:** A password is 10 characters, each picked at random from the 94 printable
> keyboard symbols. How many bits of entropy does it have? ($\log_2 94 \approx 6.55$.)
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Count the choices for one character.** 94.
> 2. **Multiply for ten characters.** $94^{10}$ possibilities.
> 3. **Bracket it between powers of 2.** $2^6 = 64$ and $2^7 = 128$, so one character is
>    worth between 6 and 7 bits.
> 4. **Work out the exact log.** $\log_2 94^{10} = 10 \times \log_2 94 \approx 10 \times 6.55 = 65.5$ bits.
>
> **Answer:** about 65.5 bits.
>
> </details>

> **Notebook example:** A passphrase is 4 words, each picked at random from the 7,776-word
> Diceware list. How long does it survive an attacker making $10^{10}$ guesses per
> second?
>
> **What you need:** the number of possible secrets N is the number of choices per word,
> multiplied once per word. An average attack tries half of them: $N \div 2$ guesses,
> which is $2^{H-1}$ when the entropy is H bits. Time = guesses ÷ guesses per second.
> One day is $24 \times 60 \times 60 = 86{,}400$ seconds. $10^{10}$ is 1 followed by 10
> zeros (ten billion), and $1.8 \times 10^{15}$ means 1.8 with the decimal point moved 15
> places right.
>
> **Plan:** count the passphrases, halve that for the average attack, divide by the
> guessing speed, and convert seconds to days.
>
> 1. **Count the passphrases.** $N = 7776 \times 7776 \times 7776 \times 7776 = 7776^4$.
> 2. **Work out two words first.** $7776 \times 7776 = 60{,}466{,}176$.
> 3. **Square that for four words.** $60{,}466{,}176^2 \approx 3.66 \times 10^{15}$.
>    *Why:* four words is two words followed by two more words.
> 4. **Turn it into bits.** $\log_2 7776^4 = 4 \times \log_2 7776 \approx 4 \times 12.92 = 51.7$ bits.
> 5. **Halve the count.** $3.66 \times 10^{15} \div 2 = 1.83 \times 10^{15}$ guesses on
>    average.
> 6. **Divide by the guessing speed.** $1.83 \times 10^{15} \div 10^{10} = 1.83 \times 10^5$
>    seconds, which is 183,000 seconds.
>    *Why:* dividing powers of 10 subtracts the exponents: $15 - 10 = 5$.
> 7. **Convert to days.** $183{,}000 \div 86{,}400 \approx 2.1$ days.
>
> **Answer:** about 2 days against a fast hash. Four words (51.7 bits) is not enough; six
> words (77.5 bits) push the same attack to roughly 350,000 years, because every extra bit
> doubles the attacker's work.
>
> **Check:** in Python, `7776**4 / 2 / 1e10 / 86400` prints 2.1158… ✓

> **Your turn:** How long do **3** Diceware words survive the same $10^{10}$ guesses per
> second?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Count the passphrases.** $7776^3 = 60{,}466{,}176 \times 7776 \approx 4.70 \times 10^{11}$.
> 2. **Halve the count.** $4.70 \times 10^{11} \div 2 = 2.35 \times 10^{11}$ guesses.
> 3. **Divide by the guessing speed.** $2.35 \times 10^{11} \div 10^{10} = 23.5$ seconds.
>
> **Answer:** about 23.5 seconds. Dropping one word cut the time from 2 days to under half
> a minute.
>
> </details>

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

> **Notebook example:** Add an even parity bit to `1011001`. Then check what the receiver
> sees after one bit flips, and after two bits flip.
>
> **What you need:** with **even parity**, the sender appends one extra bit chosen so
> that the total number of 1s is even. The receiver counts the 1s: an even count looks
> fine, an odd count means something was corrupted. A **flip** is one bit changing,
> 0 to 1 or 1 to 0, on the way.
>
> **Plan:** count the 1s to choose the parity bit, then count again in each corrupted
> message.
>
> 1. **Count the 1s in the data.** `1011001` has 1s in places 1, 3, 4 and 7: four of
>    them.
> 2. **Choose the parity bit.** Four is already even, so the parity bit is 0. Send
>    `10110010`.
> 3. **Flip one bit.** Say the 4th bit flips: the receiver gets `10100010`.
> 4. **Count the 1s.** `10100010` has three 1s. Three is odd: **detected**.
>    *Why:* one flip changes the count by exactly 1, which always turns even into odd.
> 5. **Flip two bits.** Say the 4th and the last bits flip: the receiver gets `10100011`.
> 6. **Count the 1s.** `10100011` has four 1s. Four is even: **missed**.
>    *Why:* the second flip changes the count back to even, so the damage is invisible.
>
> **Answer:** the parity bit is 0, so `10110010` is sent. Parity catches the single flip
> but misses the double flip: it catches only odd numbers of errors.
>
> **Check:** in Python, `"10110010".count("1")` is 4 (even, fine),
> `"10100010".count("1")` is 3 (odd, error) and `"10100011".count("1")` is 4 (even,
> looks fine). ✓

> **Your turn:** Add an even parity bit to `1100001`, then flip the first bit. Does the
> receiver notice?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Count the 1s in the data.** `1100001` has three 1s.
> 2. **Choose the parity bit.** Three is odd, so the parity bit is 1, making four. Send
>    `11000011`.
> 3. **Flip one bit.** The receiver gets `01000011`.
> 4. **Count the 1s.** Three, which is odd: detected.
>
> **Answer:** parity bit 1; the single flip is detected.
>
> </details>

> **Notebook example:** Compute the 3-bit CRC of the data `1101` with the generator
> `1011`.
>
> **What you need:** a **CRC** is the remainder of a long division done in binary with
> **XOR** in place of subtraction. XOR (written ⊕) compares two bits: the same gives 0,
> different gives 1 ($0 \oplus 0 = 0$, $1 \oplus 1 = 0$, $1 \oplus 0 = 1$,
> $0 \oplus 1 = 1$). There are no borrows, so each column is done on its own. The
> **generator** is the agreed divisor; a 4-bit generator gives a 3-bit remainder. The
> recipe: append 3 zeros; take the first 4 bits; XOR them with the generator; drop the
> leading bit (now 0) and bring down the next bit; repeat until no bits are left. (Every
> step in this example starts with a 1. If one ever starts with 0, XOR with `0000`
> instead, which changes nothing.)
>
> **Plan:** follow the recipe one XOR and one bring-down at a time.
>
> 1. **Append three zeros.** `1101` becomes `1101000`.
>    *Why:* the zeros make room for the 3-bit remainder at the end.
> 2. **XOR the first four bits with the generator.** `1101 ⊕ 1011`, column by column:
>    $1 \oplus 1 = 0$, $1 \oplus 0 = 1$, $0 \oplus 1 = 1$, $1 \oplus 1 = 0$. Result `0110`.
> 3. **Drop the leading 0 and bring down the next bit.** `110` plus the next bit, 0,
>    gives `1100`.
> 4. **XOR with the generator.** `1100 ⊕ 1011 = 0111`.
> 5. **Drop the leading 0 and bring down the next bit.** `111` plus 0 gives `1110`.
> 6. **XOR with the generator.** `1110 ⊕ 1011 = 0101`.
> 7. **Drop the leading 0 and bring down the last bit.** `101` plus 0 gives `1010`.
> 8. **XOR with the generator.** `1010 ⊕ 1011 = 0001`.
> 9. **Read off the remainder.** No bits are left to bring down, so the remainder is the
>    last 3 bits: `001`.
> 10. **Build the message to send.** The data followed by the remainder: `1101001`.
>     *Why:* the receiver divides this whole message by `1011`; if nothing was damaged
>     the remainder comes out as `000`.
>
> **Answer:** the CRC is `001`, so `1101001` is sent.
>
> **Check:** divide the sent message `1101001` by `1011` with the same recipe:
> `1101 ⊕ 1011 = 0110`, then `1100 → 0111`, then `1110 → 0101`, then
> `1011 ⊕ 1011 = 0000`. Remainder `000`: the receiver accepts it. ✓

> **Your turn:** Compute the 2-bit CRC of the data `11` with the generator `101`.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Append two zeros.** A 3-bit generator gives a 2-bit remainder, so `11` becomes
>    `1100`.
> 2. **XOR the first three bits with the generator.** `110 ⊕ 101 = 011`.
> 3. **Drop the leading 0 and bring down the last bit.** `11` plus 0 gives `110`.
> 4. **XOR with the generator.** `110 ⊕ 101 = 011`.
> 5. **Read off the remainder.** The last 2 bits: `11`.
>
> **Answer:** the CRC is `11`, so `1111` is sent. (Dividing `1111` by `101` leaves `00`. ✓)
>
> </details>

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

> **Notebook example:** Encode the data bits 1011 with Hamming(7,4).
>
> **What you need:** Hamming(7,4) turns 4 data bits $d_1 d_2 d_3 d_4$ into 7 bits by
> adding 3 parity bits:
> $p_1 = d_1 \oplus d_2 \oplus d_4$, $p_2 = d_1 \oplus d_3 \oplus d_4$ and
> $p_3 = d_2 \oplus d_3 \oplus d_4$. XOR (⊕) of several bits is 1 if they contain an odd
> number of 1s, and 0 if even; so each parity bit makes its group's count of 1s even.
> The 7 bits are laid out in positions 1 to 7 as $p_1, p_2, d_1, p_3, d_2, d_3, d_4$: the
> parity bits sit at positions 1, 2 and 4 (the powers of 2).
>
> **Plan:** name the data bits, compute the three parity bits one at a time, then lay all
> seven out in order.
>
> 1. **Name the data bits.** $d_1 = 1$, $d_2 = 0$, $d_3 = 1$, $d_4 = 1$.
> 2. **Compute $p_1$.** $d_1 \oplus d_2 \oplus d_4 = 1 \oplus 0 \oplus 1$. First
>    $1 \oplus 0 = 1$, then $1 \oplus 1 = 0$. So $p_1 = 0$.
> 3. **Compute $p_2$.** $d_1 \oplus d_3 \oplus d_4 = 1 \oplus 1 \oplus 1$. First
>    $1 \oplus 1 = 0$, then $0 \oplus 1 = 1$. So $p_2 = 1$.
>    *Why:* three 1s is an odd count, so the parity bit is 1 to make it even.
> 4. **Compute $p_3$.** $d_2 \oplus d_3 \oplus d_4 = 0 \oplus 1 \oplus 1$. First
>    $0 \oplus 1 = 1$, then $1 \oplus 1 = 0$. So $p_3 = 0$.
> 5. **Lay out the seven positions.** $p_1, p_2, d_1, p_3, d_2, d_3, d_4$ =
>    0, 1, 1, 0, 0, 1, 1.
>
> **Answer:** the codeword is `0110011`: the 4 data bits 1011 plus 3 parity bits that
> will let the receiver find any single flipped bit.
>
> **Check:** the code above prints `encode(1, 0, 1, 1)` as `[0, 1, 1, 0, 0, 1, 1]`. ✓

> **Your turn:** Encode the data bits 0110 with Hamming(7,4).
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Name the data bits.** $d_1 = 0$, $d_2 = 1$, $d_3 = 1$, $d_4 = 0$.
> 2. **Compute $p_1$.** $0 \oplus 1 \oplus 0 = 1$.
> 3. **Compute $p_2$.** $0 \oplus 1 \oplus 0 = 1$.
> 4. **Compute $p_3$.** $1 \oplus 1 \oplus 0 = 0$.
> 5. **Lay out the seven positions.** $p_1, p_2, d_1, p_3, d_2, d_3, d_4$ = 1, 1, 0, 0, 1, 1, 0.
>
> **Answer:** the codeword is `1100110`.
>
> </details>

> **Notebook example:** The codeword `0110011` was sent, but the receiver got `0110111`.
> Find the flipped bit and fix it.
>
> **What you need:** the receiver re-does three checks, each the XOR of a group of
> positions: $s_1$ covers positions 1, 3, 5, 7; $s_2$ covers 2, 3, 6, 7; $s_3$ covers 4,
> 5, 6, 7. A check gives 0 if its group has an even number of 1s (fine) and 1 if odd
> (broken). Written as $s_3 s_2 s_1$, the three results form a binary number called the
> **syndrome**: $s_3$ is worth 4, $s_2$ is worth 2 and $s_1$ is worth 1. The syndrome is
> the position of the flipped bit (0 means no error).
>
> **Plan:** number the received bits, run the three checks, read the syndrome as a
> number, and flip that bit back.
>
> 1. **Number the received bits.** Positions 1 to 7 of `0110111` hold 0, 1, 1, 0, 1, 1, 1.
> 2. **Run check $s_1$ (positions 1, 3, 5, 7).** The bits are 0, 1, 1, 1: three 1s, odd,
>    so $s_1 = 1$.
> 3. **Run check $s_2$ (positions 2, 3, 6, 7).** The bits are 1, 1, 1, 1: four 1s, even,
>    so $s_2 = 0$.
> 4. **Run check $s_3$ (positions 4, 5, 6, 7).** The bits are 0, 1, 1, 1: three 1s, odd,
>    so $s_3 = 1$.
> 5. **Read the syndrome.** $s_3 s_2 s_1 = 101$, which is $4 + 0 + 1 = 5$.
>    *Why:* position 5 is the only position covered by checks $s_1$ and $s_3$ but not
>    $s_2$, so only a flip there breaks exactly that pair.
> 6. **Flip position 5 back.** It holds 1, so it becomes 0: `0110011`.
> 7. **Read off the data.** The data sits at positions 3, 5, 6, 7: 1, 0, 1, 1.
>
> **Answer:** the error was at position 5. After fixing it, the data 1011 is recovered:
> the error announced its own position.
>
> **Check:** the fixed word `0110011` matches what was sent. ✓ In Python,
> `decode([0, 1, 1, 0, 1, 1, 1])` from the code above returns `([1, 0, 1, 1], 5)`. ✓

> **Your turn:** A Hamming(7,4) receiver gets `1100100`. Find the flipped bit and the data.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Number the received bits.** 1, 1, 0, 0, 1, 0, 0.
> 2. **Run check $s_1$ (positions 1, 3, 5, 7).** 1, 0, 1, 0: two 1s, even, so $s_1 = 0$.
> 3. **Run check $s_2$ (positions 2, 3, 6, 7).** 1, 0, 0, 0: one 1, odd, so $s_2 = 1$.
> 4. **Run check $s_3$ (positions 4, 5, 6, 7).** 0, 1, 0, 0: one 1, odd, so $s_3 = 1$.
> 5. **Read the syndrome.** $s_3 s_2 s_1 = 110 = 4 + 2 + 0 = 6$.
> 6. **Flip position 6 back and read the data.** `1100110`, whose positions 3, 5, 6, 7
>    hold 0, 1, 1, 0.
>
> **Answer:** position 6 was flipped, and the data is 0110.
>
> </details>

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

> **Notebook example:** Three data disks hold `1010`, `0111` and `1100`. Compute what
> RAID-5 stores on the parity disk.
>
> **What you need:** the parity disk holds the XOR of all the data disks. XOR (⊕) works
> column by column on bits: the same bits give 0, different bits give 1. To XOR three
> values, XOR the first two, then XOR that result with the third.
>
> **Plan:** XOR disk 1 with disk 2, then XOR the result with disk 3.
>
> 1. **Line up disks 1 and 2.** `1010` over `0111`.
> 2. **XOR them column by column.** $1 \oplus 0 = 1$, $0 \oplus 1 = 1$, $1 \oplus 1 = 0$,
>    $0 \oplus 1 = 1$. Result `1101`.
> 3. **Line up that result with disk 3.** `1101` over `1100`.
> 4. **XOR them column by column.** $1 \oplus 1 = 0$, $1 \oplus 1 = 0$, $0 \oplus 0 = 0$,
>    $1 \oplus 0 = 1$. Result `0001`.
>    *Why:* the order does not matter for XOR, so any pairing gives the same parity.
>
> **Answer:** the parity disk holds `0001`. It costs one extra disk, and in return any one
> disk can now fail without losing data.
>
> **Check:** count the 1s in each column across the three data disks: 2, 2, 2 and 1.
> Parity is 1 exactly where the count is odd, giving `0001`. ✓ In Python,
> `0b1010 ^ 0b0111 ^ 0b1100` is 1, which is `0001`.

> **Your turn:** Data disks hold `0011`, `0101` and `1111`. What goes on the parity disk?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Line up disks 1 and 2.** `0011` over `0101`.
> 2. **XOR them column by column.** 0, 1, 1, 0: `0110`.
> 3. **Line up that result with disk 3.** `0110` over `1111`.
> 4. **XOR them column by column.** 1, 0, 0, 1: `1001`.
>
> **Answer:** the parity disk holds `1001`.
>
> </details>

> **Notebook example:** In the array above (disk 1 `1010`, disk 3 `1100`, parity `0001`),
> disk 2 has failed. Rebuild it.
>
> **What you need:** XOR every surviving disk, including the parity disk; the result is
> the lost disk. It works because any value XORed with itself gives 0 ($a \oplus a = 0$)
> and XOR with 0 changes nothing. The parity already contains every disk once, so XORing
> in the survivors again cancels each of them, leaving only the lost one.
>
> **Plan:** XOR disk 1 with disk 3, then XOR the result with the parity disk.
>
> 1. **Line up disks 1 and 3.** `1010` over `1100`.
> 2. **XOR them column by column.** $1 \oplus 1 = 0$, $0 \oplus 1 = 1$, $1 \oplus 0 = 1$,
>    $0 \oplus 0 = 0$. Result `0110`.
> 3. **Line up that result with the parity disk.** `0110` over `0001`.
> 4. **XOR them column by column.** $0 \oplus 0 = 0$, $1 \oplus 0 = 1$, $1 \oplus 0 = 1$,
>    $0 \oplus 1 = 1$. Result `0111`.
>
> **Answer:** disk 2 is rebuilt as `0111`, exactly what it held before it failed. This is
> what the RAID code above does, byte by byte.
>
> **Check:** compare with the original disk 2, `0111`. ✓ The same bits come back.

> **Your turn:** Disks hold `0011` and `0101`, the parity disk holds `1001`, and disk 3 has
> failed. Rebuild disk 3.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Line up the two surviving data disks.** `0011` over `0101`.
> 2. **XOR them column by column.** `0110`.
> 3. **Line up that result with the parity disk.** `0110` over `1001`.
> 4. **XOR them column by column.** `1111`.
>
> **Answer:** disk 3 held `1111`.
>
> </details>

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
