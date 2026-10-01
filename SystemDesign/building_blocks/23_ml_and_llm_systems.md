# ML and LLM Systems

Google designs increasingly include a model somewhere: a recommendation feed, search ranking, spam detection, or an LLM-powered feature. You are not expected to design the model. You are expected to design the **system around it** — how features get to the model, how predictions are served within a latency budget, how the model is kept fresh, how it is evaluated, and what it costs.

This file starts with what a model is from a systems point of view, then goes as deep as a senior
design round: feature leakage and training-serving skew measured, a vector index built from
scratch, the arithmetic of LLM memory and throughput, static versus continuous batching measured,
and a worked, sized design for an assistant feature.

> 💡 Treat a model as a dependency with unusual properties: expensive per call, sometimes slow, probabilistic, silently degradable, and dependent on data pipelines that can break without any error.

## Foundations — A Model, Seen as a System Component

### What a model is, from the outside

A trained model is a function learned from data: it takes **features** (numbers describing the
request, the user, the item, the context) and returns a **prediction** (a probability of a click,
a class such as spam or not spam, a vector, or generated text). Two very different workloads use
it:

| | Training | Inference (serving) |
|---|---|---|
| When | Offline, on a schedule or continuously | On the request path |
| Input | Months of logged features and **labels** (what actually happened) | One request's features |
| Cost shape | Large, batch, throughput-bound (GPU/TPU hours) | Per request, latency-bound (milliseconds) |
| Failure mode | A bad model gets produced | A slow or wrong answer reaches a user |
| Systems it looks like | Batch processing ([Batch and Stream Processing](21_batch_and_stream_processing.md)) | A stateless service with an expensive dependency |

Most ML systems design is about the boundary between the two: making sure the features and data
seen in training are the same as those seen in serving, and that what serving does is logged so
the next training run can learn from it.

### Four shapes of ML system

| Shape | Output | Examples | Systems concern |
|---|---|---|---|
| Classification / scoring | A probability or class per item | Spam, fraud, click-through prediction | Latency per call, thresholds, calibration |
| Retrieval | Nearest items to a vector | Search, "more like this", RAG | Vector indexes, freshness, filtering |
| Ranking / recommendation | An ordered list | Feeds, search results, ads | Multi-stage funnel, fan-out, feedback loops |
| Generation | Text, images, code | Assistants, summaries | Token throughput, GPU memory, cost, safety |

### Embeddings

An **embedding** is a vector (typically 64–1,024 numbers) produced by a model so that similar
things get nearby vectors: two photos of beaches, a query and the document that answers it, a
user and the videos they'll like. Once everything is a vector, "find related things" becomes
"find nearest vectors", which is a data-structure problem (approximate nearest-neighbour search,
below) rather than a modelling one.

### Offline and online metrics

A model is judged twice. **Offline** metrics (accuracy, AUC, recall@k) are computed on held-out
historical data before launch; they are cheap and fast, and easy to fool (the leakage section below
shows how). **Online** metrics (click-through, watch time, revenue, complaints) come from an A/B
test with real users and are what decides a launch. A gap between the two is a signal that the
offline setup doesn't match production.

### Vocabulary

| Term | Meaning |
|---|---|
| Feature | An input value the model uses (a count, a category, an embedding) |
| Label | The outcome the model learns to predict (clicked, bought, was spam) |
| Point-in-time correct | Features as they were when the prediction would have been made, not as they are now |
| Training-serving skew | The model sees different feature values in serving than in training |
| Drift | Production inputs or outcomes changing away from the training data over time |
| Recall@k | The share of the true top-k results that a system returns |
| Candidate generation | Cheaply narrowing millions of items to hundreds before expensive ranking |
| Prefill / decode | Processing an LLM prompt / generating output tokens one at a time |
| KV cache | Per-token attention state an LLM keeps for every sequence it is generating |
| Time to first token (TTFT) | How long before an LLM's first output token reaches the user |

## The two loops

```arch
%% caption: Offline, models are trained on logged data. Online, they serve predictions. Logging what was served closes the loop.
grid 160x100
group offline "Offline loop · hours to days" color=blue icon=time
node logs "Event logs" at 0,1 in offline icon=logs
node etl "Feature pipelines" at 0,2 in offline icon=workflow
node fs_off "Offline feature store" at 0,3 in offline icon=storage
node train "Training" at 0,4 in offline icon=model
node eval "Evaluation" at 0,5 in offline icon=check
node reg "Model registry" at 0,6 in offline icon=archive
group online "Online loop · milliseconds" color=teal icon=speed
node req "Request" at 2,0 in online shape=pill
node resp "Response" at 3,0 in online shape=pill
node svc "Serving service" at 2,1 in online icon=service
node model "Model server" at 3,6 in online icon=llm
node fs_on "Online feature store" at 2,2 in online icon=kv
logs -> etl -> fs_off -> train -> eval -> reg
req -> svc
svc -> fs_on
svc:R <-> model:T
svc:T -> resp:L
reg -> model : "deploy"
svc -> logs : "log features + prediction + outcome"
etl -> fs_on : "materialise"
```

## Feature stores and training-serving skew

A **feature store** keeps two views of the same features: an offline store (a warehouse table with full history, for training) and an online store (a low-latency key-value store with the latest value per entity, for serving). The main thing it prevents is **training-serving skew**: the model was trained on features computed one way and served features computed another way, so it quietly performs worse in production.

- Compute each feature with one definition, materialised to both stores.
- Use **point-in-time correct** joins for training — the feature value as it was when the label event happened, not today's value — to avoid label leakage.
- Log the exact features used at serving time so training can reuse them.

## Retrieval and candidate generation

Recommendation and search systems cannot score every item for every request. They use a funnel, and each stage is 10–100× more expensive per item and sees 10–100× fewer items:

| Stage | Input → output | Technique | Budget |
|---|---|---|---|
| Candidate generation (retrieval) | Millions → ~1,000 | Embedding nearest-neighbour search, co-visitation lists, rules, followed accounts | ~10–30 ms |
| Ranking | ~1,000 → ~100 | Heavier model with rich user/item/context features | ~50 ms |
| Re-ranking | ~100 → page | Diversity, freshness, business rules, deduplication, fairness | ~10 ms |

Several retrievers usually run in parallel and their candidates are merged, so fan-out and tail latency matter just as in search.

### Approximate nearest-neighbour search

Embeddings turn users, items, queries, and documents into vectors where similar things are close. Exact nearest-neighbour search over hundreds of millions of vectors is too slow, so systems use approximate indexes:

| Index | Idea | Trade-off |
|---|---|---|
| HNSW | Multi-layer proximity graph; search greedily walks from coarse to fine layers. | Excellent recall and latency; memory-hungry; slower to build and update. |
| IVF (inverted file) | Cluster vectors with k-means; search only the few nearest clusters. | Memory-efficient; recall depends on how many clusters you probe. |
| Product quantization (PQ) | Compress vectors into short codes; compare compressed distances. | Huge memory savings; some accuracy loss. Often combined with IVF. |
| ScaNN (Google) | Anisotropic quantization tuned for maximum inner product search. | State-of-the-art speed/recall for dot-product similarity at Google scale. |

Operational points: shard the index (by item partition) and fan out queries; rebuild or incrementally update as items change; filter (e.g. "in stock, in region") either before search with partitioned indexes or after with over-fetching.

## Model serving

- **Latency budget first**: decide how much of the request's p99 the model may use, and choose model size, hardware, and caching to fit.
- **Batching**: GPUs and TPUs are efficient only when they process many inputs at once. A serving system collects requests for a few milliseconds and runs them as one batch — trading a small, bounded latency increase for several times the throughput.
- **CPU vs accelerator**: small ranking models often run on CPU next to the service; large models need GPUs/TPUs in a dedicated serving tier.
- **Caching**: cache predictions for repeated inputs (popular queries, logged-out homepages) and cache embeddings for items that rarely change.
- **Fallbacks**: if the model is slow or down, serve a cheaper model, a cached result, or a heuristic (most popular). A recommender that times out should still show a page.
- **Rollout**: shadow traffic, then canary, then an A/B test on online metrics — offline metrics alone do not decide a launch.

## LLM serving

LLM inference has two phases with different bottlenecks:

1. **Prefill** processes the whole prompt in parallel and produces the first token. Cost grows with prompt length; this sets time-to-first-token.
2. **Decode** generates one token at a time, each step reading the growing **KV cache** (attention keys and values for all previous tokens). This is memory-bound and sets tokens per second.

Key techniques to name:

| Technique | What it does | Why it matters |
|---|---|---|
| Token streaming (SSE) | Send tokens as they are produced. | Perceived latency drops to time-to-first-token. |
| Continuous batching | Add new requests to the running batch as soon as any sequence finishes. | Several times higher throughput than static batching (vLLM, TGI). |
| PagedAttention | Allocate KV cache in fixed-size blocks instead of one contiguous region per request. | Near-zero fragmentation → more concurrent sequences per GPU. |
| Prefix (prompt) caching | Reuse the KV cache for a shared prefix such as a long system prompt or document. | Cuts prefill cost and latency for repeated context. |
| Quantization | Store weights in 8 or 4 bits. | Fits bigger models or more batch per GPU; small quality cost. |
| Speculative decoding | A small draft model proposes tokens; the large model verifies several at once. | 2–3× faster decoding with identical outputs. |
| Semantic caching | Return a stored answer for a sufficiently similar earlier question. | Saves full generations; risk of serving a wrong answer if the threshold is loose. |

### Cost and quotas

LLM cost scales with tokens, so product decisions are cost decisions. Put per-user and per-tenant **token quotas** and rate limits at the gateway, choose the smallest model that meets quality per task (route easy requests to cheap models), cap `max_tokens`, cache aggressively, and track cost per feature as a first-class metric.

### Safety and quality

- Input filtering (prompt-injection and abuse classifiers) and output filtering (policy classifiers, PII redaction) around the model.
- Grounding: retrieval-augmented generation with citations for factual features.
- Evaluation: an offline eval set with automated graders for every model or prompt change, plus online feedback signals and human review samples.

## Monitoring ML systems

Everything in [Observability and Reliability](15_observability_and_reliability.md) still applies, plus signals that normal monitoring misses:

- **Data quality**: missing or null feature rates, schema changes, feature pipeline freshness.
- **Drift**: input distributions (PSI, KS test) and prediction distributions versus the training baseline.
- **Model quality**: online metrics (click-through, conversion, user ratings) sliced by segment, with delayed labels joined back.
- **Cost and capacity**: GPU utilisation, batch sizes, queue time, tokens per second, cost per request.

## Interview angles

- "Design YouTube recommendations" → funnel (candidates → ranking → re-ranking), embeddings + ANN for retrieval, feature store, logging for training, freshness of new videos (cold start), A/B testing.
- "Add an AI assistant to Gmail" → gateway with quotas, streaming, context assembly from the user's data with permission checks, prefix caching of the system prompt, safety filters, cost controls, graceful fallback when the model is unavailable.
- "How do you know the model got worse?" → drift and data-quality monitors, delayed-label quality metrics, canary comparisons against the previous model.

## Going deeper

This file is the overview. [Ranking, Recommendation, and Experimentation](31_ranking_recommendation_and_experimentation.md) goes further on what interviews actually probe: the ranking cascade with per-stage budgets, position bias and feedback loops, exploration and cold start, offline versus online metrics, and how experimentation platforms decide whether a model change worked. For a full worked design, see [032 Ranked Home Feed](../solutions/032_ranked_home_feed_solution.md) and [037 Experimentation Platform](../solutions/037_experimentation_platform_solution.md).

## Leakage and training-serving skew, measured

The feature-store section above warns about point-in-time joins and training-serving skew. Here
is what each does to a simple model: predict which users buy next week from their purchases in the
last four weeks, using the rule "predict a purchase if they bought at least twice":

```python
"""Predict which users buy next week from one feature: purchases in the last
4 weeks. Two classic ways to get this wrong:
  leakage - the training join uses the feature as of today, so the window
            includes the very week being predicted;
  skew    - serving computes the feature from a real-time counter that misses
            the 30% of purchases recorded late, so it reads lower than in training."""
import random

rng = random.Random(12)
USERS, WEEKS = 50_000, 14
users = []
for _ in range(USERS):
    p = rng.betavariate(0.6, 4)                              # each user's weekly purchase chance
    users.append([rng.random() < p for _ in range(WEEKS)])   # weeks 0..13
LABEL = 12                                                   # predict week 12 from weeks 8..11


def feature(weeks, end, missing=0.0):
    """Purchases in the 4 weeks before `end`; `missing` = share not yet counted."""
    return sum(1 for w in weeks[end - 4:end] if w and rng.random() >= missing)


def auc(scores, labels):
    """Chance a random buyer scores higher than a random non-buyer (ties count half)."""
    pos = sorted(s for s, y in zip(scores, labels) if y)
    neg = sorted(s for s, y in zip(scores, labels) if not y)
    wins, j, k = 0.0, 0, 0
    for s in pos:
        while j < len(neg) and neg[j] < s:
            j += 1
        k = j
        while k < len(neg) and neg[k] == s:
            k += 1
        wins += j + (k - j) / 2
    return wins / (len(pos) * len(neg))


def precision_recall(scores, labels, threshold):
    pred = [s >= threshold for s in scores]
    tp = sum(p and y for p, y in zip(pred, labels))
    return tp / max(1, sum(pred)), tp / sum(labels)


labels = [u[LABEL] for u in users]
correct = [feature(u, LABEL) for u in users]                 # as of the prediction time
leaky = [feature(u, LABEL + 1) for u in users]               # as of "now": includes week 12
served = [feature(u, LABEL, missing=0.3) for u in users]     # what the online counter shows

print(f"{USERS:,} users, {sum(labels) / USERS:.1%} buy in the predicted week\n")
print(f"  {'what was evaluated':44} {'AUC':>5} {'precision':>10} {'recall':>7}")
for name, scores in [("offline, leaky join (what the team saw)", leaky),
                     ("offline, point-in-time join (= online best)", correct),
                     ("online, feature from the lagging counter", served)]:
    pr, rc = precision_recall(scores, labels, 2)             # rule tuned offline: ">= 2 purchases"
    print(f"  {name:44} {auc(scores, labels):5.2f} {pr:10.1%} {rc:7.1%}")
```

```text
50,000 users, 13.3% buy in the predicted week

  what was evaluated                             AUC  precision  recall
  offline, leaky join (what the team saw)       0.92      59.2%   56.6%
  offline, point-in-time join (= online best)   0.69      34.5%   32.8%
  online, feature from the lagging counter      0.66      36.3%   20.7%
```

- **The leaky join made the model look far better than it can be.** Joining "purchases in the last
  4 weeks" as of today, instead of as of the prediction time, puts the predicted week inside the
  feature. Offline AUC was 0.92; the honest number, which is the best production can do, is 0.69.
  The team would launch expecting 57% recall and get 33%. Leakage never raises an error; it only
  shows up as a gap between offline and online metrics.
- **Skew lowered recall again, silently.** The online counter missed purchases recorded late, so
  the feature read lower in production than in training, fewer users crossed the threshold, and
  recall fell from 33% to 21%. Nothing crashed, and the model and code were unchanged.
- **The fixes are data-engineering fixes**: one feature definition materialised to both the
  offline and online stores, point-in-time joins for every training example (the feature store's
  main job), and logging the features actually served so training can use exactly those. Then
  monitor the served feature distribution against training (a data-drift check would have caught
  the counter immediately).

## Vector search, built and measured

The IVF index from the table above, built from scratch: cluster the vectors with k-means into
100 lists, and at query time scan only the `nprobe` lists whose centres are nearest to the query.
The embeddings come in topics, as real ones do:

```python
"""An IVF (inverted file) vector index built from scratch: cluster 20,000
embeddings with k-means into 100 lists, then search only the nprobe lists whose
centroids are closest to the query. Recall@10 = how many of the true 10 nearest
neighbours the index returns."""
import heapq, random
from operator import mul

rng = random.Random(3)
DIM, N, LISTS, QUERIES = 24, 20_000, 100, 100


def dot(a, b):
    return sum(map(mul, a, b))


def unit(v):
    n = dot(v, v) ** 0.5
    return [x / n for x in v]


# Embeddings come in topics: 200 topic centres, each vector = centre + noise.
centres = [unit([rng.gauss(0, 1) for _ in range(DIM)]) for _ in range(200)]
def sample():
    c = rng.choice(centres)
    return unit([x + rng.gauss(0, 0.15) for x in c])
vecs = [sample() for _ in range(N)]
queries = [sample() for _ in range(QUERIES)]

# k-means (a few rounds are enough for an index) on a sample of the data.
cents = rng.sample(vecs, LISTS)
for _ in range(6):
    groups = [[] for _ in range(LISTS)]
    for v in rng.sample(vecs, 5_000):
        groups[max(range(LISTS), key=lambda c: dot(v, cents[c]))].append(v)
    cents = [unit([sum(col) for col in zip(*g)]) if g else cents[i] for i, g in enumerate(groups)]
lists = [[] for _ in range(LISTS)]
for i, v in enumerate(vecs):
    lists[max(range(LISTS), key=lambda c: dot(v, cents[c]))].append(i)

truth = [set(heapq.nlargest(10, range(N), key=lambda i: dot(q, vecs[i]))) for q in queries]

print(f"{N:,} vectors, {DIM} dims, {LISTS} lists (largest {max(map(len, lists))}, smallest {min(map(len, lists))})")
print(f"  {'nprobe':>6} {'recall@10':>10} {'vectors compared':>17} {'share of exact work':>20}")
for nprobe in (1, 2, 4, 8, 16, 100):
    hits = compared = 0
    for q, t in zip(queries, truth):
        near = heapq.nlargest(nprobe, range(LISTS), key=lambda c: dot(q, cents[c]))
        cand = [i for c in near for i in lists[c]]
        compared += len(cand) + LISTS
        hits += len(t & set(heapq.nlargest(10, cand, key=lambda i: dot(q, vecs[i]))))
    print(f"  {nprobe:6} {hits / (10 * QUERIES):10.1%} {compared / QUERIES:17,.0f} {compared / QUERIES / N:19.1%}")
```

```text
20,000 vectors, 24 dims, 100 lists (largest 398, smallest 90)
  nprobe  recall@10  vectors compared  share of exact work
       1      85.8%               317                1.6%
       2      92.0%               517                2.6%
       4      95.5%               921                4.6%
       8      97.8%             1,711                8.6%
      16      99.2%             3,292               16.5%
     100     100.0%            20,100              100.5%
```

- **Approximate search trades a little recall for a lot of work.** Scanning 4 of 100 lists compares
  under 5% of the vectors and still finds about 95% of the true 10 nearest neighbours; 16 lists
  reach 99%. `nprobe` is a knob you can turn per request: more recall for a premium query, less
  for a cheap one.
- **Misses happen at cluster boundaries.** A neighbour that falls just across a boundary is in a
  list you didn't scan. Recall therefore depends on how clustered the data is, so it must be
  measured on your own embeddings, against exact search on a sample.
- **At real scale, memory becomes the constraint.** A billion 768-dimension float32 vectors is
  3 TB. Product quantization compresses each vector to tens of bytes, and HNSW graphs add links
  per vector; both are chosen by recall, latency and memory budget together.
- **Filters complicate everything.** "Nearest items that are in stock, in my region" either
  searches a partition built per filter value, or over-fetches (take the top 100, then filter to
  10) and risks returning too few results for a restrictive filter.

## LLM serving arithmetic

LLM serving capacity is decided by GPU memory and memory bandwidth, and a few lines of arithmetic
predict it well. The shapes below match public open-weight models:

```python
"""Where an LLM server's memory and time go. Shapes follow public open-weight
models: an 8B model with grouped-query attention (32 layers, 8 KV heads of 128
dims) and a 70B one (80 layers, 8 KV heads of 128 dims). One GPU: 80 GB of
memory at about 3 TB/s. All numbers are 16-bit (2 bytes per value)."""

GPU_GB, GPU_BW = 80, 3.0e12
models = {"8B": (8e9, 32, 8, 128), "70B": (70e9, 80, 8, 128)}


def kv_bytes_per_token(layers, kv_heads, head_dim, bytes_per=2):
    return 2 * layers * kv_heads * head_dim * bytes_per      # a key and a value per layer


print("Memory: weights first, then how many sequences' KV caches fit alongside them")
for label, name, weight_bytes, gpus in [("8B, 16-bit, 1 GPU", "8B", 2, 1),
                                        ("70B, 16-bit, 2 GPUs", "70B", 2, 2),
                                        ("70B, 16-bit, 4 GPUs", "70B", 2, 4),
                                        ("70B, 8-bit weights, 2 GPUs", "70B", 1, 2)]:
    params, layers, kv_heads, dim = models[name]
    weights = params * weight_bytes
    per_tok = kv_bytes_per_token(layers, kv_heads, dim)
    free = gpus * GPU_GB * 1e9 * 0.9 - weights                # keep 10% for activations
    fits = "  ".join(f"{int(free // (per_tok * ctx)):4,} x {ctx // 1000}k" for ctx in (2_000, 8_000, 32_000))
    print(f"  {label:27} weights {weights / 1e9:4.0f} GB, KV {per_tok // 1024:3} KB/token, "
          f"{free / 1e9:4.0f} GB free -> sequences: {fits}")

print("\nDecoding is memory-bound: each step reads all weights once, plus each sequence's KV cache.")
params, layers, kv_heads, dim = models["8B"]
weights, per_tok, ctx = params * 2, kv_bytes_per_token(layers, kv_heads, dim), 2_000
print(f"8B model, 2,000-token contexts, one GPU")
print(f"  {'batch':>5} {'step time':>10} {'tokens/s per sequence':>22} {'tokens/s total':>15}")
for batch in (1, 8, 32, 64, 128):
    step = (weights + batch * ctx * per_tok) / GPU_BW
    print(f"  {batch:5} {step * 1000:8.1f} ms {1 / step:22.0f} {batch / step:15,.0f}")
```

```text
Memory: weights first, then how many sequences' KV caches fit alongside them
  8B, 16-bit, 1 GPU           weights   16 GB, KV 128 KB/token,   56 GB free -> sequences:  213 x 2k    53 x 8k    13 x 32k
  70B, 16-bit, 2 GPUs         weights  140 GB, KV 320 KB/token,    4 GB free -> sequences:    6 x 2k     1 x 8k     0 x 32k
  70B, 16-bit, 4 GPUs         weights  140 GB, KV 320 KB/token,  148 GB free -> sequences:  225 x 2k    56 x 8k    14 x 32k
  70B, 8-bit weights, 2 GPUs  weights   70 GB, KV 320 KB/token,   74 GB free -> sequences:  112 x 2k    28 x 8k     7 x 32k

Decoding is memory-bound: each step reads all weights once, plus each sequence's KV cache.
8B model, 2,000-token contexts, one GPU
  batch  step time  tokens/s per sequence  tokens/s total
      1      5.4 ms                    184             184
      8      6.0 ms                    166           1,326
     32      8.1 ms                    123           3,936
     64     10.9 ms                     92           5,858
    128     16.5 ms                     61           7,749
```

- **Weights come first, and decide the GPU count.** A 70B model in 16-bit needs 140 GB, so two
  80 GB GPUs hold the weights but leave almost nothing for sequences; four GPUs or 8-bit weights
  make it servable.
- **The KV cache decides concurrency.** Each token of every running sequence keeps its attention
  keys and values: 128 KB per token for the 8B model, 320 KB for the 70B. Long contexts are
  expensive: the memory that holds 213 sequences of 2,000 tokens holds 13 of 32,000. That is why
  PagedAttention (no wasted reservations), grouped-query attention (fewer KV heads) and prefix
  caching matter so much.
- **Batching is where throughput comes from.** Each decode step reads every weight from memory
  whether it serves 1 sequence or 128. Batching 128 sequences makes each one about 3 times slower
  (61 vs 184 tokens/s) but raises total throughput 40 times. Real servers reach a compute limit at
  some point, which this model ignores, but the shape holds.
- **Interactive features pick a point on that curve.** A chat product needs each user to see
  perhaps 30+ tokens/s; a batch summarisation job wants maximum total throughput. They are often run
  on separate pools with different batch limits.

## Static vs continuous batching, measured

Batching only helps if the server can keep the batch full. Static batching runs a batch until its
longest request finishes; continuous batching refills free slots at every decode step:

```python
"""Static vs continuous batching on one simulated LLM server. Requests arrive at
random; each wants between 20 and 1,000 output tokens (most are short). A decode
step takes 15 ms plus 0.1 ms per sequence in the batch (memory-bound, as in the
previous model), and adding a request costs a 30 ms prefill. At most 64 sequences
run at once."""
import random, statistics

STEP, PER_SEQ, PREFILL, MAX_BATCH = 0.015, 0.0001, 0.030, 64


def workload(rate, n=3000, seed=9):
    rng, t, reqs = random.Random(seed), 0.0, []
    for _ in range(n):
        t += rng.expovariate(rate)
        reqs.append((t, min(1000, max(20, int(rng.lognormvariate(4.8, 0.9))))))
    return reqs


def static(reqs):
    """Take up to 64 waiting requests, run the batch until its longest one finishes."""
    t, i, first, done, tokens = 0.0, 0, [], [], 0
    while i < len(reqs):
        t = max(t, reqs[i][0])
        batch = [r for r in reqs[i:i + MAX_BATCH] if r[0] <= t]
        i += len(batch)
        t += PREFILL * len(batch)
        first += [t - a for a, _ in batch]
        steps = max(n for _, n in batch)
        t += steps * (STEP + PER_SEQ * len(batch))       # finished sequences wait for the longest
        done += [t - a for a, _ in batch]
        tokens += sum(n for _, n in batch)
    return tokens / t, first, done


def continuous(reqs):
    """Every step: admit waiting requests into free slots, then decode one token for all."""
    t, i, running, first, done, tokens = 0.0, 0, [], [], [], 0
    while i < len(reqs) or running:
        if not running and reqs[i][0] > t:
            t = reqs[i][0]
        while i < len(reqs) and reqs[i][0] <= t and len(running) < MAX_BATCH:
            t += PREFILL
            first.append(t - reqs[i][0])
            running.append([reqs[i][0], reqs[i][1]])
            i += 1
        t += STEP + PER_SEQ * len(running)
        for r in running:
            r[1] -= 1
        for r in [r for r in running if r[1] == 0]:
            done.append(t - r[0])
            running.remove(r)
    return sum(n for _, n in reqs) / t, first, done


def p(xs, q):
    return sorted(xs)[int(q * len(xs))]


for rate in (2, 3, 8):
    reqs = workload(rate)
    print(f"{rate} requests/s, mean output {statistics.mean(n for _, n in reqs):.0f} tokens")
    print(f"  {'':11} {'tokens/s':>9} {'first token p50':>16} {'p99':>7} {'finished p50':>13} {'p99':>7}")
    for name, fn in (("static", static), ("continuous", continuous)):
        thr, first, done = fn(reqs)
        print(f"  {name:11} {thr:9,.0f} {p(first, .5):14.2f} s {p(first, .99):5.2f} s "
              f"{p(done, .5):11.1f} s {p(done, .99):5.1f} s")
```

```text
2 requests/s, mean output 176 tokens
               tokens/s  first token p50     p99  finished p50     p99
  static            357           6.82 s 20.55 s        19.7 s  39.9 s
  continuous        358           0.04 s  0.07 s         2.1 s  15.1 s
3 requests/s, mean output 176 tokens
               tokens/s  first token p50     p99  finished p50     p99
  static            532          14.77 s 37.91 s        32.3 s  55.9 s
  continuous        536           0.04 s  0.07 s         2.2 s  15.9 s
8 requests/s, mean output 176 tokens
               tokens/s  first token p50     p99  finished p50     p99
  static            558         287.97 s 570.98 s       301.8 s 580.7 s
  continuous      1,403           0.04 s  0.09 s         3.1 s  22.0 s
```

- **At light load, static batching wastes time, not throughput.** Both keep up with 2–3 requests
  a second, but with static batching a request waits for the whole previous batch, including its
  longest generation, so time to first token is 7–15 seconds at the median instead of a few tens of
  milliseconds.
- **At higher load, static batching collapses.** Its throughput is capped near 560 tokens/s
  because short requests sit finished in the batch while the longest one decodes, and the queue
  grows without bound (first tokens after about 5 minutes). Continuous batching serves all 1,400
  tokens/s with first tokens still in tens of milliseconds.
- **Output lengths vary widely** (here from 20 to 1,000 tokens), which is exactly why the
  difference is so large. Serving systems such as vLLM, TGI and TensorRT-LLM all use continuous
  batching, and separate or chunk prefills so a long prompt doesn't stall everyone's decoding.

## A worked design: an assistant feature

"Add an AI assistant to a productivity app with 10 million daily users."

| Quantity | Estimate | Consequence |
|---|---|---|
| Requests | 10M users × 5/day = 50M/day ≈ 580/s, ~1,700/s at peak | A gateway with per-user quotas and rate limits |
| Prompt tokens | ~1,500 each (system prompt ~1,000 + retrieved context + question) | ~870K prompt tokens/s: prefill dominates compute |
| Output tokens | ~300 each | ~174K tokens/s to generate, streamed to users |
| Prefill compute | 870K tokens × 2 × 8B parameters ≈ 1.4 × 10¹⁶ operations/s | ~30 GPUs at ~50% of ~10¹⁵ operations/s each, on average |
| Decode | ~5,000 tokens/s per GPU at a batch of 64 (from the model above) | ~35 GPUs on average |
| Peak with headroom | 3× peak, 70% target utilisation | Roughly 250–300 GPUs, which is why the levers below matter |

The levers, largest first:

1. **Prefix caching of the shared system prompt** removes about two thirds of prefill work (1,000 of
   1,500 tokens are identical across requests).
2. **Routing by difficulty**: most requests (rewrite this sentence, summarise this note) go to a
   small model; only hard ones go to the large one.
3. **Tighter context**: retrieve fewer, better chunks, since every context token is paid for on
   every request.
4. **Caps and quotas**: `max_tokens` per feature, token budgets per user and tenant.
5. **Semantic or exact caching** for repeated questions, where freshness and privacy allow.

Around the model: retrieval over the user's own documents with **permission checks at retrieval
time** (never let the model see what the user can't), streaming responses over SSE, input and
output safety filters, per-feature cost dashboards, an evaluation set run on every prompt or model
change, and a graceful fallback (a smaller model or a plain error message) when the GPU pool is
saturated.

## What each level should know

| Topic | L4 · Mid | L5 · Senior | L6+ · Staff |
|---|---|---|---|
| **ML system basics** | Knows training vs serving, features vs labels | Designs feature pipelines with point-in-time joins, logging and skew monitoring | Designs the ML platform (feature store, registry, evaluation, rollout) for many teams |
| **Retrieval and ranking** | Knows the funnel exists | Designs candidate generation with ANN, ranking and re-ranking within a latency budget | Owns trade-offs between recall, latency, freshness and cost across the funnel |
| **LLM serving** | Calls an LLM API with streaming | Explains prefill vs decode, KV cache memory, batching and prefix caching; sizes a GPU pool | Designs multi-model routing, capacity and cost governance for an organisation |
| **Quality and safety** | Knows offline metrics | Designs A/B tests, drift and data-quality monitors, and safety filters | Sets evaluation standards and launch criteria for ML features |

## Interview checklist

- [ ] I can explain training vs inference and the systems concerns of each.
- [ ] I can explain feature leakage and training-serving skew, show their effect, and design the fixes.
- [ ] I can explain embeddings and how an IVF or HNSW index trades recall for speed and memory.
- [ ] I can design a retrieval, ranking and re-ranking funnel with a latency budget per stage.
- [ ] I can estimate LLM memory: weights, KV cache per token, and how many sequences fit.
- [ ] I can explain why batching raises throughput and why continuous batching beats static batching.
- [ ] I can size a GPU pool for an LLM feature and name the biggest cost levers.
- [ ] I can design monitoring for ML: data quality, drift, online metrics, and cost.

## Related building blocks

- [Scaling and Load Balancing](13_scaling_and_load_balancing.md)
- [Specialized Data Structures and Indexes](20_specialized_data_structures.md)
- [Batch and Stream Processing](21_batch_and_stream_processing.md)
- [Back-of-the-Envelope Estimation](18_back_of_envelope_estimation.md)
- [Ranking, Recommendation, and Experimentation](31_ranking_recommendation_and_experimentation.md)
