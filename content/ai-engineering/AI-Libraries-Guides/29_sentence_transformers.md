# Sentence Transformers Mastery: Embedding Models, Rerankers and Fine-Tuning

## 1. The Core Concept (What and Why)

*Why is this tool relevant?* Every RAG pipeline in this module has an `embed()` step hiding in it. LangChain (Guide 11) and LlamaIndex (Guide 12) call an embedding model to turn chunks into vectors; FAISS, ChromaDB and Qdrant (Guides 17-19) store and search those vectors. The vector database decides how *fast* retrieval is; the **embedding model** decides whether the right chunk is anywhere near the top at all. When a RAG app has poor context recall (Guide 25), the fix is usually here: a better model, the right query/document prompts, a reranker, or fine-tuning on your own data.

**What is it?**
An **embedding** is a fixed-length vector (e.g. 384 or 1024 floats) that represents the meaning of a piece of text, so that texts with similar meaning have vectors pointing in similar directions (high cosine similarity). **Sentence Transformers** (`sentence-transformers`, maintained by Hugging Face) is the standard Python library for computing, evaluating and training such models. It wraps a Transformer (Guide 08) with a pooling layer, and gives you:
- `SentenceTransformer`: **bi-encoders** that embed each text independently (for search, clustering, deduplication).
- `CrossEncoder`: **rerankers** that read a (query, document) pair together and output a relevance score.
- `SparseEncoder`: **sparse** models (SPLADE-style), where each dimension is a vocabulary word, for keyword-aware hybrid search.
- A trainer, ~30 loss functions and evaluators for fine-tuning on your own data.

Thousands of models on the Hugging Face Hub load with one line, from the classic `all-MiniLM-L6-v2` (small, fast, English) to multilingual, instruction-aware models such as the BGE-M3, E5, GTE, Nomic, mxbai and Qwen3-Embedding families.

**Why does it exist?**
A raw Transformer outputs one vector *per token*. To get one vector per sentence you need pooling, and a model trained so that the pooled vectors are *comparable* (a plain BERT's mean-pooled vectors are poor at similarity). Sentence-BERT (Reimers & Gurevych, 2019) introduced this siamese training recipe; the library grew out of that paper and became the common interface for embedding models.

---

## 2. Setup & Installation

```bash
pip install sentence-transformers            # pulls in torch + transformers
pip install "sentence-transformers[train]"   # + datasets, accelerate for fine-tuning
```

```python
import sentence_transformers

print(f"Sentence Transformers version: {sentence_transformers.__version__}")  # 5.x / 6.x in 2026
```

*Version note:* v5 (2025) added `encode_query`/`encode_document` and `SparseEncoder`. v6 moved the training modules: losses and evaluators now live under `sentence_transformers.sentence_transformer.losses` / `.evaluation` (the old `sentence_transformers.losses` path still works with a deprecation warning, and is the path to use on v5). All model code below needs network access the first time, to download weights from the Hugging Face Hub.

---

## 3. The "Hello World": Embed and Compare (downloads a model)

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")   # ~90 MB, 384 dimensions

sentences = [
    "The cat sits on the mat.",
    "A feline is resting on a rug.",
    "Quarterly revenue grew 12%.",
    "The stock market rallied today.",
]
embeddings = model.encode(sentences)          # numpy array, shape (4, 384)
print(embeddings.shape)

similarity = model.similarity(embeddings, embeddings)   # (4, 4) tensor, cosine by default
print(similarity.round(decimals=2))
# Expect high similarity for (0, 1) and a moderate score for (2, 3),
# and low scores across the two groups, even though (0, 1) share almost no words.
```

That's the core idea: "cat on the mat" and "feline on a rug" share no keywords, yet their vectors are close. This is what keyword search (BM25) can't do, and why embeddings power semantic search.

---

## 4. Deep Dive: How an Embedding Model Works, and Bi- vs Cross-Encoders

### The pipeline inside `SentenceTransformer`

```python
print(model)
# SentenceTransformer(
#   (0): Transformer({'max_seq_length': 256, ...})   <- tokenize + BERT-style encoder: one vector per token
#   (1): Pooling({'pooling_mode_mean_tokens': True})  <- average the token vectors into one
#   (2): Normalize()                                  <- scale to length 1, so dot product == cosine
# )
```

- **Pooling**: mean pooling (average of token vectors, ignoring padding) is the most common; some models use the `[CLS]` token or the last token (decoder-based embedders such as Qwen3-Embedding). The model's config decides; don't change it.
- **`max_seq_length`**: tokens beyond it are **silently truncated**. `all-MiniLM-L6-v2` stops at 256 tokens (about 190 words); a 2,000-word chunk is embedded from its first paragraph only. Check `model.max_seq_length` against your chunk size (Guide 12).
- **Normalisation and similarity**: if embeddings are unit length, cosine similarity equals dot product, so you can use a fast inner-product index (Guide 17). `model.similarity_fn_name` tells you what the model was trained with.

### Parameter Breakdown: `model.encode(...)`
- `batch_size` (default 32): bigger is faster on a GPU until memory runs out. Texts are sorted by length internally to reduce padding.
- `normalize_embeddings=True`: return unit vectors (a no-op if the model already has a `Normalize` layer).
- `convert_to_tensor=True`: keep a torch tensor on the GPU instead of copying to NumPy.
- `precision="int8" | "binary" | "ubinary"`: quantized output for smaller indexes (Section 6).
- `truncate_dim=256`: Matryoshka truncation (Section 5).
- `prompt_name="query"` / `prompt="..."`: prepend an instruction (next section).

### Queries and documents are not the same thing

Many modern models are **asymmetric**: they expect a prefix or instruction on queries (and sometimes a different one on documents), e.g. `"query: "` / `"passage: "` for E5, or an `Instruct: ...\nQuery: ` template for Qwen3-Embedding. Forgetting the prefix silently costs retrieval quality. `encode_query` and `encode_document` apply whatever prompts the model's config defines:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")   # instruction-aware, prompts ship in its config
print(model.prompts)                                        # e.g. {'query': 'Instruct: ...\nQuery:', 'document': ''}

docs = ["Reset your password from Settings > Security.", "Invoices are emailed on the 1st of each month."]
doc_emb = model.encode_document(docs)
query_emb = model.encode_query("I forgot my login credentials")
print(model.similarity(query_emb, doc_emb))   # the password doc should score higher
```

### Bi-encoder vs cross-encoder

| | Bi-encoder (`SentenceTransformer`) | Cross-encoder (`CrossEncoder`) |
| --- | --- | --- |
| Input | One text at a time | A (query, document) pair, concatenated |
| Output | A vector per text | One relevance score per pair |
| Documents pre-computable? | Yes: embed the corpus once, store in a vector DB | No: must run the model for every pair at query time |
| Cost per query over N docs | 1 encoder pass + N cheap dot products (or ANN search) | N encoder passes |
| Quality | Good | Better: every query token attends to every document token |
| Use for | First-stage retrieval over millions of docs | Reranking the top 20-100 candidates |

So production search uses both: **retrieve** with a bi-encoder (fast, recall-oriented), then **rerank** a short list with a cross-encoder (slow, precision-oriented).

```arch
%% caption: Retrieve-then-rerank: the bi-encoder narrows millions of documents to a short list, and the cross-encoder orders that list.
node q "Query" at 0,0 icon=user
node bi "Bi-encoder" at 1,0 icon=embed sub="query -> vector"
node vdb "Vector index" at 2,0 icon=vector sub="ANN top-100"
node docs "Corpus" at 2,1 icon=doc sub="embedded offline"
node ce "Cross-encoder" at 3,0 icon=model sub="score 100 pairs"
node llm "LLM" at 3,1 icon=llm sub="top 5 as context"
q -> bi -> vdb
docs ..> vdb : "index once"
vdb -> ce : "candidates"
ce -> llm : "reranked"
```

```python
from sentence_transformers import CrossEncoder, SentenceTransformer

bi_encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L6-v2")   # trained on MS MARCO search queries

corpus = [
    "To reset your password, open Settings > Security and click 'Forgot password'.",
    "Password requirements: at least 12 characters, one number and one symbol.",
    "Our office is closed on public holidays.",
    "If you forgot your username, contact support with your order number.",
    "Two-factor authentication can be enabled under Settings > Security.",
    "Refunds are processed within 5 business days.",
]
query = "How do I change my password if I forgot it?"

# Stage 1: bi-encoder retrieval (in production: a vector DB over pre-computed embeddings)
corpus_emb = bi_encoder.encode_document(corpus, normalize_embeddings=True)
query_emb = bi_encoder.encode_query(query, normalize_embeddings=True)
scores = bi_encoder.similarity(query_emb, corpus_emb)[0]
top = scores.topk(4)
candidates = [corpus[i] for i in top.indices.tolist()]
print("Retrieved:", [round(s, 3) for s in top.values.tolist()])

# Stage 2: cross-encoder reranking of the short list
for hit in reranker.rank(query, candidates, return_documents=True):
    print(f"{hit['score']:7.3f}  {hit['text']}")
```

Cross-encoder scores are **not** probabilities or cosine values; many rerankers output unbounded logits. Use them to *order* candidates, and calibrate before using them as a threshold (e.g. "drop anything below X").

---

## 5. Pro Level: Matryoshka Embeddings and Fine-Tuning

### Matryoshka Representation Learning (MRL)

A **Matryoshka** model is trained so that the *first* 64, 128, 256... dimensions of its vector are each a usable embedding on their own (like nested dolls). You can truncate a 1024-dim vector to 256 dims, re-normalise, and keep most of the retrieval quality at a quarter of the storage and search cost. It only works for models trained with a Matryoshka loss (Nomic v1.5, mxbai-embed-large, Qwen3-Embedding, EmbeddingGemma, OpenAI's text-embedding-3 models via their `dimensions` parameter, and others); truncating a normal model's vector throws information away arbitrarily.

```python
from sentence_transformers import SentenceTransformer

full = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B")                      # 1024 dims
small = SentenceTransformer("Qwen/Qwen3-Embedding-0.6B", truncate_dim=256)   # same weights, first 256 dims

text = ["Matryoshka embeddings nest smaller embeddings inside larger ones."]
print(full.encode(text).shape, small.encode(text).shape)   # (1, 1024) (1, 256)
# Common pattern: search a big index with truncated vectors, then rescore the top hits with full vectors.
```

### Fine-tuning on your own data (downloads the base model; the training itself runs on a laptop CPU in minutes at this size)

Off-the-shelf models are trained on web data. On internal jargon ("SEV2", "the Phoenix migration", product codes) they can rank badly. A few thousand (question, relevant passage) pairs, often generated by an LLM from your own documents, can noticeably improve retrieval. The standard recipe:

- **Data**: `(anchor, positive)` pairs. No explicit negatives needed.
- **Loss**: `MultipleNegativesRankingLoss` (MNRL, a contrastive InfoNCE loss): for each anchor, its positive must score higher than every *other* positive in the batch, which act as **in-batch negatives**. Bigger batches mean more negatives and usually better models (`CachedMultipleNegativesRankingLoss` gets large effective batches in small memory).
- **Wrap in `MatryoshkaLoss`** to make the fine-tuned model truncatable too.
- **`BatchSamplers.NO_DUPLICATES`**: prevents the same text appearing twice in a batch, which would create false negatives.
- **Evaluate before and after** with a held-out `InformationRetrievalEvaluator`.

```python
from datasets import Dataset
from sentence_transformers import SentenceTransformer, SentenceTransformerTrainer, SentenceTransformerTrainingArguments
from sentence_transformers.sentence_transformer.evaluation import InformationRetrievalEvaluator
from sentence_transformers.sentence_transformer.losses import MatryoshkaLoss, MultipleNegativesRankingLoss
from sentence_transformers.sentence_transformer.training_args import BatchSamplers
# sentence-transformers v5: import from sentence_transformers.losses / .evaluation / .training_args instead

faq = [  # (question, answer passage): in real life thousands of these, e.g. LLM-generated from your docs
    ("How do I get VPN access?", "VPN access is requested through the IT portal under Network > Remote Access."),
    ("My laptop won't connect to the office wifi", "For wifi problems, forget the 'corp-secure' network and re-enrol your device certificate."),
    ("Who approves a SEV2 incident review?", "SEV2 postmortems are approved by the on-call engineering manager within 5 days."),
    ("Where do I file an expense for a conference?", "Conference expenses go in the Expensify 'Training' category with the agenda attached."),
    ("How do I rotate a service API key?", "Rotate service keys in Vault with 'vault kv rollback' and redeploy the service."),
    ("What is the Phoenix migration?", "Phoenix is the project moving billing from the monolith to the payments service."),
    ("Can I install Homebrew on my work Mac?", "Homebrew is allowed; install it from Self Service, not the public script."),
    ("How do I book a meeting room?", "Meeting rooms are booked in the calendar app by adding the room as a guest."),
    ("How long are logs retained?", "Application logs are retained for 30 days in hot storage and 1 year in archive."),
    ("Who do I ask for production database access?", "Production database access needs a Jira ticket approved by the data platform team."),
    ("How do I reset my SSO password?", "SSO passwords are reset at id.example.com with your hardware key."),
    ("What's the on-call compensation?", "On-call engineers receive a weekly stipend plus time off after night pages."),
]
train_pairs, eval_pairs = faq[:8], faq[8:]
train_dataset = Dataset.from_dict({"anchor": [q for q, _ in train_pairs], "positive": [a for _, a in train_pairs]})

# Held-out retrieval evaluation: each eval question must find its passage among ALL passages
corpus = {f"d{i}": a for i, (_, a) in enumerate(faq)}
queries = {f"q{i}": pair[0] for i, pair in enumerate(faq) if pair in eval_pairs}
relevant_docs = {qid: {"d" + qid[1:]} for qid in queries}
evaluator = InformationRetrievalEvaluator(queries, corpus, relevant_docs, name="it-faq", ndcg_at_k=[5], mrr_at_k=[5])

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
print("before:", {k: round(v, 3) for k, v in evaluator(model).items() if "cosine_ndcg@5" in k or "cosine_mrr@5" in k})

loss = MatryoshkaLoss(model, MultipleNegativesRankingLoss(model), matryoshka_dims=[384, 256, 128, 64])
args = SentenceTransformerTrainingArguments(
    output_dir="minilm-it-faq",
    num_train_epochs=3,
    per_device_train_batch_size=8,          # = number of in-batch negatives + 1: bigger is better for MNRL
    learning_rate=2e-5,
    warmup_steps=0.1,                       # a float = fraction of total steps (Transformers v5; on v4 use warmup_ratio=0.1)
    batch_sampler=BatchSamplers.NO_DUPLICATES,
    eval_strategy="epoch",
    save_strategy="no",
    logging_steps=1,
    report_to="none",                        # or "wandb" / "mlflow" (Guides 23-24)
)
trainer = SentenceTransformerTrainer(model=model, args=args, train_dataset=train_dataset, loss=loss, evaluator=evaluator)
trainer.train()

print("after:", {k: round(v, 3) for k, v in evaluator(model).items() if "cosine_ndcg@5" in k or "cosine_mrr@5" in k})
model.save_pretrained("minilm-it-faq/final")
```

On a dataset this small the numbers will jump around; the point is the workflow. With a few thousand real pairs, compare before/after on a held-out set of real user queries, never on the training questions.

**Hard negatives.** In-batch negatives are mostly easy (a VPN question vs a meal-expense passage). A **hard negative** is a passage that looks relevant but isn't ("VPN access for contractors" for an employee question). Adding them as a third column `(anchor, positive, negative)` teaches finer distinctions. `sentence_transformers.util.mine_hard_negatives(dataset, model, ...)` finds candidates with an existing model; use its `range_min`/`max_score` options (or a cross-encoder) to skip candidates that are actually relevant, or you'll train the model to push away correct answers.

**Rerankers** fine-tune the same way with `CrossEncoderTrainer` and losses such as `BinaryCrossEntropyLoss` or `LambdaLoss`, usually on (query, passage, label) data with mined hard negatives.

---

## 6. Pro Level: Evaluation and Embedding Quantization

### How to evaluate an embedding model

- **Public leaderboard (MTEB / MMTEB)**: the Massive Text Embedding Benchmark scores models on retrieval, classification, clustering, STS and more, across many languages. Use it to shortlist; look at the **retrieval** column for RAG, for your language, and check model size and max sequence length. Don't pick by the overall average alone: leaderboard scores don't guarantee performance on your domain, and some models train on data close to the benchmarks.
- **Your own data (the one that matters)**: 100-500 real queries with labelled relevant chunks, scored with `InformationRetrievalEvaluator` (recall@k, MRR@k, NDCG@k). Recall@k matters most for RAG: if the right chunk isn't in the top k, the LLM never sees it.
- Other evaluators: `EmbeddingSimilarityEvaluator` (correlation with human similarity scores), `RerankingEvaluator`, `TripletEvaluator`, `NanoBEIREvaluator` (a quick, small general retrieval benchmark).

### Quantized embeddings: 4x to 32x smaller indexes (runs offline)

Storage and RAM for a vector index scale with `num_vectors x dims x bytes`. 100M vectors x 1024 dims x 4 bytes (float32) is about 410 GB. Two quantizations cut that:
- **int8 (scalar)**: map each dimension's observed range onto 256 levels: 4x smaller.
- **binary**: keep only the sign bit of each dimension: 32x smaller, compared with Hamming distance (XOR + popcount), which CPUs do extremely fast.

Then **rescoring** recovers quality: fetch a few times more candidates with the cheap index, and re-rank them with the float32 query against the (still compressed) document vectors. The lab below implements both quantizations in NumPy on synthetic vectors (the library's `quantize_embeddings` and `encode(precision=...)` do the same thing):

```python
import numpy as np

rng = np.random.default_rng(0)
n_docs, dim, n_queries, k = 20_000, 384, 200, 10

# Synthetic "embeddings" with structure: 50 topics > 2,000 subtopics > documents, unit length like real models
topics = rng.normal(size=(50, dim))
subtopics = topics[rng.integers(0, 50, 2_000)] + rng.normal(scale=0.7, size=(2_000, dim))
docs = subtopics[rng.integers(0, 2_000, n_docs)] + rng.normal(scale=0.5, size=(n_docs, dim))
docs = (docs / np.linalg.norm(docs, axis=1, keepdims=True)).astype(np.float32)
queries = docs[rng.choice(n_docs, n_queries, replace=False)] + rng.normal(scale=0.03, size=(n_queries, dim))
queries = (queries / np.linalg.norm(queries, axis=1, keepdims=True)).astype(np.float32)

def top_k(scores, k):
    return np.argsort(-scores, axis=1)[:, :k]

def recall(found):
    return np.mean([len(set(f) & set(t)) / k for f, t in zip(found, truth)])

truth = top_k(queries @ docs.T, k)                        # exact float32 search

# int8 scalar quantization: map each dimension's [min, max] (from a calibration set) onto 256 levels
lo, hi = docs.min(axis=0), docs.max(axis=0)
def to_int8(x):
    return np.clip(np.round((x - lo) / (hi - lo) * 255 - 128), -128, 127).astype(np.int8)
docs_i8 = to_int8(docs)
found_i8 = top_k(to_int8(queries).astype(np.int32) @ docs_i8.astype(np.int32).T, k)

# binary quantization: keep only the sign of each dimension, 8 dimensions per byte
docs_bin = np.packbits(docs > 0, axis=1)                 # (n_docs, 48) uint8
q_bin = np.packbits(queries > 0, axis=1)
hamming = np.stack([np.bitwise_count(q ^ docs_bin).sum(axis=1) for q in q_bin])  # popcount of XOR (NumPy 2.0+)
found_bin = top_k(-hamming, k)

# binary + rescoring: 4k candidates by Hamming distance, re-ranked with the float32 query
cand = top_k(-hamming, 4 * k)
signs = np.unpackbits(docs_bin, axis=1).astype(np.float32) * 2 - 1     # back to -1/+1
cand_scores = np.einsum("qd,qcd->qc", queries, signs[cand])
found_rescored = np.take_along_axis(cand, top_k(cand_scores, k), axis=1)

for name, index, found in [("float32", docs, truth), ("int8", docs_i8, found_i8),
                           ("binary", docs_bin, found_bin), ("binary + rescore", docs_bin, found_rescored)]:
    print(f"{name:17} {index.nbytes / 2**20:6.2f} MiB   recall@{k} = {recall(found):.3f}")
```

Output:

```text
float32            29.30 MiB   recall@10 = 1.000
int8                7.32 MiB   recall@10 = 0.933
binary              0.92 MiB   recall@10 = 0.830
binary + rescore    0.92 MiB   recall@10 = 0.852
```

Recall here is measured against exact float32 search on synthetic data, so treat the exact numbers as illustrative. Real embedding models, especially ones trained with quantization in mind, typically lose less. The shape of the trade-off is the lesson: int8 is close to lossless at 4x; binary is 32x smaller and needs rescoring (and often a larger candidate pool) to get close; always measure on your own data. Qdrant (Guide 19) and FAISS (Guide 17) support both scalar and binary quantization with rescoring built in.

---

## 7. Production: Serving and Operating Embeddings

1. **Pin the model, and never mix vectors from two models** (or two versions, or with and without prompts) in one index; the spaces are incompatible. Changing the model means re-embedding the whole corpus, so store the source text and the model ID with every vector.
2. **Batch and sort by length** for throughput. For multiple GPUs or CPU cores, pass `pool=` / `device=[...]` to `encode` (or the older `encode_multi_process`).
3. **Faster runtimes**: `SentenceTransformer(..., backend="onnx")` or `"openvino"` for CPU inference, optionally with quantized ONNX weights. For a dedicated service, Hugging Face's Text Embeddings Inference (TEI) server or vLLM (Guide 20, which serves embedding models too) gives batching and an HTTP API.
4. **Cache query embeddings** for repeated queries; embed documents offline in batch jobs, not on the request path.
5. **Choose dimension deliberately**: a Matryoshka model at 256-512 dims plus int8 is often the best cost/quality point for large indexes.
6. **Hybrid search**: combine dense vectors with BM25 or a `SparseEncoder` (SPLADE) for exact terms like error codes and product SKUs, which dense models handle poorly. Fuse the result lists with reciprocal rank fusion.

---

## 8. MAANG Interview Scenarios

### Scenario 1: RAG Retrieves the Wrong Chunks
*Interviewer:* "Our RAG assistant for internal docs has low context recall. The vector DB is fine. What do you check in the embedding layer?"

*Answer:* "First, measure: build 200 real queries with labelled relevant chunks and compute recall@10 so every fix is measured. Then the usual suspects, cheapest first. Truncation: if chunks are longer than the model's `max_seq_length`, only the start is embedded. Prompts: asymmetric models need their query instruction; I'd use `encode_query`/`encode_document`. Model fit: if the model is English-only and docs are multilingual, or it's an old small model, try two or three strong candidates from the MTEB retrieval column on our eval set. Vocabulary: internal jargon and IDs suggest adding hybrid BM25/sparse search. Then add a cross-encoder reranker over the top 50, which usually gives a large precision gain. Finally, if it's still weak, fine-tune the bi-encoder with MNRL on LLM-generated question-passage pairs from our docs, with mined hard negatives, and compare on the held-out set."

### Scenario 2: Why Not Use the Cross-Encoder for Everything?
*Interviewer:* "The cross-encoder is more accurate. Why not score every document with it?"

*Answer:* "Cost scales with the corpus. A cross-encoder must run a full Transformer pass for every (query, document) pair at query time; for 10 million documents that's 10 million forward passes per query, which is impossible at interactive latency. A bi-encoder embeds the corpus once offline; at query time it's one forward pass for the query plus an ANN search that takes milliseconds. So we use the bi-encoder to cut 10 million down to about 100 candidates and the cross-encoder to order those 100. The cross-encoder is better because query and document tokens attend to each other; the bi-encoder has to compress each text into one vector without knowing what it will be compared to."

### Scenario 3: Cutting Vector Storage Cost
*Interviewer:* "We store 500 million 1024-dim float32 embeddings. The RAM bill is huge. Options?"

*Answer:* "That's about 2 TB of raw vectors. Levers, roughly in order of quality cost: int8 scalar quantization (4x, near-lossless, about 500 GB); a Matryoshka model truncated to 256 dims (another 4x); binary quantization (32x vs float32, about 64 GB) with rescoring from int8 or float vectors kept on disk for the top candidates; or product quantization in FAISS (Guide 17). I'd evaluate each on our retrieval eval set, because the loss depends on the model: models trained with Matryoshka and quantization-aware objectives degrade much less. A common end state is binary vectors in RAM for the first pass, int8 on SSD for rescoring, and full text for the reranker."

---

## 9. Common Pitfalls & Debugging in Production

### ⚠️ Pitfall 1: Silent truncation
Long chunks are cut at `max_seq_length` with no warning, so the end of every chunk is invisible to search.
*Fix:* Check `model.max_seq_length` and chunk below it (with the model's tokenizer, not word counts), or pick a long-context embedding model.

### ⚠️ Pitfall 2: Missing query/document prompts
Encoding queries with plain `encode()` on an instruction-tuned model (E5, BGE, Qwen3-Embedding, Nomic) can drop retrieval quality noticeably.
*Fix:* Use `encode_query` / `encode_document`, or pass `prompt_name`; read the model card for the expected prefixes.

### ⚠️ Pitfall 3: Mixing embedding spaces
A model upgrade embeds new documents while old ones stay in the index; queries now match only half the corpus well.
*Fix:* Store model ID with vectors, re-embed everything on a model change, and switch indexes atomically (blue/green indexes).

### ⚠️ Pitfall 4: Using cosine thresholds as if they were universal
"Similarity > 0.8 means relevant" is model-specific: some models put unrelated texts at 0.3, others at 0.7.
*Fix:* Calibrate thresholds per model on labelled pairs; for "is this relevant?" decisions prefer a cross-encoder score calibrated the same way.

### ⚠️ Pitfall 5: False negatives in contrastive training
With MNRL, duplicate or near-duplicate positives in the same batch are treated as negatives, and mined "hard negatives" are sometimes actually relevant; the model learns to push correct answers away.
*Fix:* `BatchSamplers.NO_DUPLICATES`, deduplicate the training set, and filter mined negatives with a margin or a cross-encoder score.
