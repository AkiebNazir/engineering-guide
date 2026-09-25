# Retrieval-Augmented Generation (RAG) — Deep Dive

## 1. The problem <abbr title="Retrieval-Augmented Generation">RAG</abbr> solves

LLMs have two structural weaknesses:
- **Knowledge cutoff** — anything that happened, or was written, after training has no representation in the model's weights.
- **No access to private data** — your company's docs, tickets, contracts, or codebase were never in the training set.
- **Hallucination under uncertainty** — when the model doesn't know something, it tends to generate a fluent, plausible-sounding answer rather than say "I don't know."

<abbr title="Retrieval-Augmented Generation">RAG</abbr> addresses all three by giving the model **retrieved, sourced text** at inference time, so it answers from evidence rather than from memory alone.

There are two phases: an offline **indexing phase** (done once, updated periodically) and an online **query phase** (done per user request). Below, every step of both.

---

## 2. Indexing phase

### 2.1 Document loading and parsing

Before you can chunk anything, you have to extract clean text from source formats — PDFs, HTML, Word docs, Confluence pages, Slack exports, code repos. This step is underrated and often the biggest source of downstream quality loss:

- **PDFs** — text extraction can scramble reading order in multi-column layouts, drop table structure, or merge headers into body text. Tools like `unstructured`, `PyMuPDF`, or vision-based extraction (rendering pages as images and using a multimodal model) handle this with varying fidelity.
- **HTML** — need to strip nav bars, ads, and boilerplate while preserving semantic structure (headings, lists, tables).
- **Tables** — flattening a table into plain text loses row/column relationships; some pipelines convert tables to markdown or <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> to preserve structure.

Garbage extraction here poisons every later stage — no amount of clever chunking or reranking fixes text that was already scrambled on the way in.

### 2.2 Chunking strategies (the part you asked about)

Chunking exists because you can't embed an entire 50-page document as one vector (the meaning gets averaged into mush) and you can't feed whole documents into every prompt (context limits, cost, noise). You need pieces small enough to be topically coherent, but large enough to retain context.

**a) Fixed-size chunking**
Split text every N tokens or characters (e.g., every 512 tokens), often with an overlap (e.g., 50 tokens) between consecutive chunks so meaning isn't severed at the boundary.
- *Pros*: trivial to implement, predictable size, fast.
- *Cons*: cuts sentences and ideas in half arbitrarily; no awareness of document structure.
- *Use when*: you need something working fast, or the corpus is unstructured (chat logs, raw text dumps).

**b) Sentence-based chunking**
Split on sentence boundaries (using a proper sentence tokenizer, not just periods — abbreviations, decimals, and initials break naive splitting), then group sentences into chunks up to a token budget.
- *Pros*: never cuts a thought mid-sentence.
- *Cons*: sentence count doesn't always correlate with semantic units — five short sentences might belong together, one long sentence might not.

**c) Recursive character/token splitting**
The most common production default (e.g., LangChain's `RecursiveCharacterTextSplitter`). It tries to split on the largest structural unit first (paragraph breaks), and only falls back to smaller units (sentences, then words, then characters) if a piece is still too big.
- *Pros*: respects natural document structure by default; graceful degradation.
- *Cons*: still fundamentally structure-blind — doesn't know what a "topic" is, just what a paragraph is.

**d) Document-structure-aware chunking**
Use the document's own structure — markdown headers, HTML tags, code function/class boundaries — as chunk boundaries. A chunk becomes "everything under this H2 heading" or "this one Python function."
- *Pros*: chunks map to units a human would recognize as coherent; great for docs, wikis, and code.
- *Cons*: requires structured input; chunk sizes become uneven (one section might be 50 tokens, another 2000).

**e) Semantic chunking**
Embed individual sentences, then split at points where consecutive sentence embeddings show a big similarity drop — i.e., where the *topic* actually shifts, rather than where a paragraph happens to end.
- *Pros*: chunk boundaries track meaning, not typography; often the highest-quality option for retrieval accuracy.
- *Cons*: expensive (embed every sentence just to decide chunk boundaries), and there's a tuning knob (similarity threshold) that needs calibration per corpus.

**f) Sliding window chunking**
Like fixed-size, but with a large overlap ratio (e.g., 50%+), so nearly every idea appears fully within at least one chunk regardless of where boundaries fall.
- *Pros*: minimizes the "split right through the important sentence" failure mode.
- *Cons*: multiplies storage and retrieval redundancy — you're indexing much more text for the same source content.

**g) Agentic / <abbr title="Large Language Model">LLM</abbr>-based chunking**
Have an <abbr title="Large Language Model">LLM</abbr> read the document and propose chunk boundaries directly, based on genuine topical or argumentative structure (this is close to how a human would summarize a document into sections).
- *Pros*: highest conceptual quality, adapts to any document type.
- *Cons*: slow and costly to run over a large corpus; usually reserved for high-value or frequently-queried documents.

**h) Parent-child / hierarchical chunking**
Index small chunks for precise retrieval matching, but when a small chunk is retrieved, return its larger "parent" chunk (or the full section/document) to the <abbr title="Large Language Model">LLM</abbr> for generation. This decouples *what you search over* from *what you feed the model*.
- *Pros*: gets the best of both — precise retrieval, rich context for generation.
- *Cons*: more moving pieces, needs a mapping between child and parent chunks maintained in your store.

**Practical chunk-size guidance**: 200–500 tokens is a common starting range for prose; smaller (100–200) for FAQ/QA-style content where each unit is already atomic; larger (500–1000) for code or dense technical docs where surrounding context is load-bearing. Overlap of 10–20% of chunk size is a common default. There's no universal right answer — this should be tuned against your own retrieval eval set (see Section 6).

### 2.3 Embedding generation

Each chunk is passed through an embedding model to produce a dense vector (typically 384–3072 dimensions) that encodes its semantic meaning — chunks about similar topics end up close together in vector space.

- **Dense embeddings** (e.g., OpenAI's `text-embedding-3`, Cohere embed models, open-source options like BGE or E5) capture semantic/conceptual similarity — good at matching paraphrases and related concepts even without shared words.
- **Sparse embeddings** (e.g., BM25, SPLADE) are closer to weighted keyword matching — good at exact term matches (product codes, names, acronyms) that dense embeddings can blur over.
- Many production systems use **both** (hybrid search — more in 3.2), since each covers the other's blind spot.

Metadata is typically stored alongside each vector: source document, section title, page number, date, author, access permissions — used later for filtering and for citing sources in the answer.

### 2.4 Storing in a vector database

The embeddings go into a vector database (Pinecone, Weaviate, Qdrant, pgvector, Milvus, or a plain FAISS index for smaller scale). These databases use **approximate nearest neighbor (ANN)** search algorithms — exact nearest-neighbor search doesn't scale, so they trade a small amount of accuracy for massive speed:

- **HNSW (Hierarchical Navigable Small World)** — builds a multi-layer graph of vectors; search hops through layers from coarse to fine. Very fast query time, higher memory use. Most common default today.
- **IVF (Inverted File Index)** — clusters vectors into buckets (via k-means), and search only scans the most relevant buckets. Lower memory, needs a training step.
- **Product Quantization (<abbr title="Priority Queue. An abstract data type similar to a regular queue or stack in which each element additionally has a priority associated with it.">PQ</abbr>)** — compresses vectors to reduce memory footprint, often combined with IVF (IVF-<abbr title="Priority Queue. An abstract data type similar to a regular queue or stack in which each element additionally has a priority associated with it.">PQ</abbr>), at some cost to precision.

Similarity is measured via **cosine similarity**, **dot product**, or **Euclidean (L2) distance** — cosine and normalized dot product are most common for text embeddings since they're insensitive to vector magnitude.

---

## 3. Query phase

### 3.1 Query embedding and (optionally) query transformation

The raw user question is embedded the same way as the chunks. But raw user questions are often poor search queries — short, ambiguous, or phrased very differently from how the answer is written in the source docs. Common fixes:

- **Query rewriting** — an <abbr title="Large Language Model">LLM</abbr> call reformulates the question into a clearer, more searchable form before embedding.
- **HyDE (Hypothetical Document Embeddings)** — instead of embedding the question directly, ask an <abbr title="Large Language Model">LLM</abbr> to write a *hypothetical answer* to the question, and embed that instead. Answers tend to be linguistically closer to the source documents than questions are, which can improve match quality.
- **Multi-query expansion** — generate several rephrasings of the question, retrieve for each, and merge/deduplicate the results — widens the net against phrasing mismatch.
- **Decomposition** — break a complex, multi-part question into sub-questions, retrieve separately for each, and combine.

### 3.2 Retrieval

The query vector is compared against the indexed chunk vectors to find the top-k most similar ones (k is often 3–20 depending on chunk size and context budget). Refinements commonly layered on top of plain vector search:

- **Hybrid search** — combine dense (semantic) and sparse (keyword/BM25) retrieval, then merge rankings (often via Reciprocal Rank Fusion). Covers both "conceptually related" and "exact term match" queries.
- **Metadata filtering** — restrict the search to chunks matching a filter (date range, document type, user's access permissions) before or alongside the vector search.
- **Maximal Marginal Relevance (MMR)** — instead of just taking the top-k most similar chunks (which can all be near-duplicates of each other), MMR balances relevance against diversity, so retrieved chunks cover different angles of the answer.

### 3.3 Reranking

Vector search is fast but approximate — it's optimized to *shortlist* candidates, not to make the final precision call. A common two-stage pattern:

1. Retrieve a wider candidate set cheaply (e.g., top 20–50) via vector/hybrid search.
2. Pass each candidate, paired with the query, through a **cross-encoder** reranking model (e.g., Cohere Rerank, a BGE reranker) that scores relevance far more accurately — because it looks at the query and chunk *together*, rather than comparing two independently-computed vectors.
3. Keep only the top 3–5 reranked chunks to actually send to the <abbr title="Large Language Model">LLM</abbr>.

This step alone is one of the highest-leverage additions to a basic <abbr title="Retrieval-Augmented Generation">RAG</abbr> system — it catches the frequent cases where "vector-similar" isn't the same as "actually answers this question."

### 3.4 Prompt construction (augmentation)

The retrieved chunks are assembled with the user's question into a single prompt, typically with:

- A system instruction telling the model to answer *only* from the provided context, and to say so explicitly if the context doesn't contain the answer (this is the main lever against hallucination).
- The chunks themselves, often labeled with source metadata so the model can cite them ("According to [Document X, Section 2]...").
- The original user question, placed either before or after the context depending on the framework — placement affects how strongly the model attends to it.

Context window management matters here: cramming in too many chunks dilutes attention and increases cost; too few risks missing the answer. This is largely why reranking is valuable — it lets you send fewer, better chunks.

### 3.5 Generation

The <abbr title="Large Language Model">LLM</abbr> produces the final answer, grounded in the supplied context rather than parametric memory alone. Techniques to strengthen grounding:

- Explicit instruction to quote or cite the source chunk for each claim.
- Asking the model to output "insufficient information" rather than guessing, when the retrieved context doesn't cover the question.
- Post-hoc **faithfulness checking** — a secondary pass (sometimes another <abbr title="Large Language Model">LLM</abbr> call) verifying that each claim in the generated answer is actually supported by the retrieved chunks.

---

## 4. Advanced patterns worth knowing

- **Agentic <abbr title="Retrieval-Augmented Generation">RAG</abbr>** — instead of a fixed retrieve-then-generate pipeline, an <abbr title="Large Language Model">LLM</abbr> agent decides *whether* to retrieve, *what* to search for, and whether to retrieve again based on what it got back (multi-hop retrieval for questions that need several pieces of evidence chained together).
- **GraphRAG** — build a knowledge graph from the corpus (entities and relationships) alongside the vector index, so retrieval can traverse relationships ("who reports to whom," "which components depend on which") that pure similarity search misses.
- **Self-<abbr title="Retrieval-Augmented Generation">RAG</abbr> / corrective <abbr title="Retrieval-Augmented Generation">RAG</abbr>** — the model critiques its own retrieved context and can trigger a re-retrieval or query rewrite if the first pass looks insufficient.

---

## 5. Common failure modes

- **Chunking cuts the answer in half** across two chunks, so neither individually contains enough context — parent-child chunking or larger overlap mitigates this.
- **Retrieval finds "similar," not "correct"** — a chunk can be topically close but not actually answer the question; this is what reranking is for.
- **Stale index** — the vector database wasn't updated after the source documents changed, so the model confidently cites outdated information.
- **Over-stuffed context** — dumping too many chunks into the prompt dilutes the model's attention and can *increase* hallucination rather than reduce it.
- **No "I don't know" path** — if the system prompt doesn't explicitly permit the model to say the context is insufficient, it will often still generate a confident-sounding guess.

## 6. Evaluating a <abbr title="Retrieval-Augmented Generation">RAG</abbr> system

Two layers get measured separately:
- **Retrieval quality** — did we fetch the right chunks? Measured via precision/recall@k, or human-labeled relevance judgments.
- **Generation quality** — given the retrieved chunks, did the model produce a faithful, relevant answer? Measured via **faithfulness** (is every claim supported by the context?) and **answer relevance** (does it actually address the question?). Frameworks like RAGAS automate these with <abbr title="Large Language Model">LLM</abbr>-as-judge scoring.

## 7. <abbr title="Retrieval-Augmented Generation">RAG</abbr> vs. fine-tuning (when to use which)

| | <abbr title="Retrieval-Augmented Generation">RAG</abbr> | Fine-tuning |
|---|---|---|
| Best for | Injecting facts/knowledge | Changing style, tone, format, task behavior |
| Update cost | Cheap — re-index documents | Expensive — retrain or re-tune |
| Freshness | Always current with the index | Frozen at training time |
| Transparency | Can cite sources | Opaque — no traceable source |
| Failure mode | Retrieval miss → no answer or hallucination | Overfits, forgets, or subtly drifts |

They're not mutually exclusive — many production systems fine-tune a model to be better at *using* retrieved context (following citation format, refusing when context is insufficient) while still relying on <abbr title="Retrieval-Augmented Generation">RAG</abbr> for the actual facts.