# Day 84: RAG v2 (Hybrid Search & Reranking)

Welcome to Day 84. In Day 83, we built a **Dense Retriever** (Semantic Search). It matches documents based on underlying meaning. 

But Dense Retrieval has a fatal flaw: It is terrible at Exact Keyword Matching. If a user asks *"What is the warranty for part number AX-990-BZ?"*, a dense embedding might retrieve a document about *"Part number AX-990-CX"* because the two sentences are semantically identical.

Today, we fix this. We will build the ultimate production <abbr title="Retrieval-Augmented Generation">RAG</abbr> pipeline: **Hybrid Search with a Cross-Encoder Reranker**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Sparse Retrieval (BM25)
Before Vector Databases, there was **BM25** (the algorithm powering Elasticsearch). 
It is a **Sparse** retrieval system. It counts exactly how many times a keyword appears in a document. It uses TF-IDF (Term Frequency - Inverse Document Frequency) logic:
- If the word *"The"* appears 50 times, BM25 gives it a low score because *"The"* is common everywhere.
- If the word *"AX-990-BZ"* appears 2 times, BM25 gives it a massive score because it is incredibly rare!
BM25 is the perfect complement to Dense retrieval because it guarantees exact keyword hits.

### 2. Hybrid Search & Reciprocal Rank Fusion (RRF)
We don't choose between Dense and Sparse. We run both!
1. **Dense Search:** Returns the Top 50 semantic matches.
2. **Sparse Search (BM25):** Returns the Top 50 keyword matches.
3. **The Problem:** Dense outputs Cosine Similarity ($0.85$). Sparse outputs BM25 scores ($14.2$). You cannot mathematically compare them!
4. **The Fix (RRF):** We ignore the scores and look at the **Rank**. We merge the two lists using Reciprocal Rank Fusion: 
   $RRF\_Score = \frac{1}{Rank_{Dense} + 60} + \frac{1}{Rank_{Sparse} + 60}$
   If a document is Rank #1 in Dense and Rank #1 in Sparse, it gets a massive RRF score and bubbles to the absolute top of the combined list!

### 3. Cross-Encoder Reranking
We now have a combined list of 50 great documents. But we only want to send 3 to the <abbr title="Large Language Model">LLM</abbr>. 
The Bi-Encoder we used in Day 83 was fast, but stupid. It embedded the query and document separately.
A **Cross-Encoder** is a massive BERT model that takes the Query AND the Document *simultaneously* as input: `[CLS] Query [SEP] Document [SEP]`. 
Because both texts are in the Transformer at the same time, the Self-Attention mechanism allows the words in the question to directly interact with the words in the document!
- **Con:** It is incredibly slow. You cannot run it on 100M documents.
- **Pro:** It is incredibly accurate. We run it *only* on the Top 50 documents retrieved by Hybrid Search, and use it to extract the absolute best Top 3!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's implement the RRF math and the Reranker! We will simulate the outputs of a Dense and Sparse search, merge them, and rerank them.

*(Mentally run `pip install sentence-transformers`)*

Create a file named `hybrid_search_reranker.py`:

```python
import torch
from sentence_transformers import CrossEncoder

def reciprocal_rank_fusion(dense_ranks, sparse_ranks, k=60):
    """
    Mathematically merges two ranked lists without caring about their raw scores.
    dense_ranks: List of document IDs ranked by Dense Search
    sparse_ranks: List of document IDs ranked by Sparse (BM25) Search
    """
    rrf_scores = {}
    
    # Process Dense Ranks
    for rank, doc_id in enumerate(dense_ranks, start=1):
        if doc_id not in rrf_scores:
            rrf_scores[doc_id] = 0.0
        rrf_scores[doc_id] += 1.0 / (rank + k)
        
    # Process Sparse Ranks
    for rank, doc_id in enumerate(sparse_ranks, start=1):
        if doc_id not in rrf_scores:
            rrf_scores[doc_id] = 0.0
        rrf_scores[doc_id] += 1.0 / (rank + k)
        
    # Sort the final merged list by highest RRF score!
    sorted_merged_list = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
    return [doc_id for doc_id, score in sorted_merged_list]

def test_hybrid_pipeline():
    print("--- RUNNING RAG v2: HYBRID SEARCH & RERANKING ---")
    
    # 1. Our Corpus
    documents = {
        "doc1": "The AX-400 is our cheapest model.",
        "doc2": "Part number AX-990-BZ has a 5-year warranty. It is highly durable.",
        "doc3": "Warranty information for the AX-990-CX is 2 years.",
        "doc4": "All products have a baseline 1-year warranty."
    }
    query = "What is the warranty for part number AX-990-BZ?"
    
    # 2. Simulate the Search Engines
    # Dense Search captures "warranty" well, but misses the exact part number.
    mock_dense_ranks = ["doc3", "doc4", "doc2", "doc1"]
    
    # Sparse Search (BM25) captures the exact part number string perfectly!
    mock_sparse_ranks = ["doc2", "doc3", "doc1", "doc4"]
    
    # 3. Step 1: Hybrid Merge via RRF
    hybrid_top_docs = reciprocal_rank_fusion(mock_dense_ranks, mock_sparse_ranks)
    print("1. HYBRID MERGE (RRF)")
    print(f"Top Documents after RRF: {hybrid_top_docs}")
    
    # 4. Step 2: Cross-Encoder Reranking
    print("\n2. CROSS-ENCODER RERANKING")
    print("Loading Cross-Encoder (ms-marco-TinyBERT)...")
    # This model was trained specifically on Microsoft MARCO to score QA pairs!
    reranker = CrossEncoder('cross-encoder/ms-marco-TinyBERT-L-2-v2')
    
    # We create pairs: [[Query, DocA], [Query, DocB], ...]
    pairs_to_score = [[query, documents[doc_id]] for doc_id in hybrid_top_docs]
    
    # The Cross-Encoder scores them using full Self-Attention!
    reranker_scores = reranker.predict(pairs_to_score)
    
    # Sort the documents by the Reranker's precise scores
    final_ranked_results = sorted(zip(hybrid_top_docs, reranker_scores), key=lambda x: x[1], reverse=True)
    
    print("\nFINAL PIPELINE OUTPUT (Top 2 for the LLM):")
    for rank, (doc_id, score) in enumerate(final_ranked_results[:2], start=1):
        print(f"#{rank} [Score: {score:>.2f}] - {doc_id}: {documents[doc_id]}")

if __name__ == "__main__":
    test_hybrid_pipeline()
```

### Key Takeaways from Code:
1. **The $K=60$ Constant:** In the RRF formula, $60$ is a magic number empirically proven to work best. It prevents documents that rank #1 in one list and #100 in the other from completely dominating documents that consistently rank #5 in both lists.
2. **The Pipeline Funnel:** 10M Documents $\xrightarrow{\text{FAISS/BM25}}$ Top 100 $\xrightarrow{\text{RRF}}$ Top 50 $\xrightarrow{\text{Cross-Encoder}}$ Top 3 $\xrightarrow{\text{<abbr title="Large Language Model">LLM</abbr>}}$. This perfectly balances speed and accuracy!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Implementing BM25
You used a mock list. Now build the real BM25 algorithm.
**Your Task:**
1. Conceptually write a BM25 scoring script using the `rank_bm25` python library.
2. Tokenize your documents into lists of strings (e.g., `["The", "AX-400", "is", "cheap"]`).
3. Initialize `BM25Okapi(tokenized_corpus)`.
4. Tokenize a query, and run `bm25.get_scores(tokenized_query)`. 
5. Notice how words that appear in every document (like "The") mathematically receive a near-zero weight, while rare IDs explode in score!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design a <abbr title="Retrieval-Augmented Generation">RAG</abbr> system for a major Legal Firm with 10 Million case documents. They have strict Access Control (Lawyer A cannot see Lawyer B's cases) and absolute zero-tolerance for hallucination. Discuss the retrieval pipeline, access-controlled indexing, and hallucination prevention."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Access-Controlled Indexing (Metadata Filtering):** 
   - State that you cannot just dump 10M vectors into FAISS. 
   - You must use a Vector DB that supports **Pre-filtering** (like Pinecone or Qdrant). When embedding the chunk, you attach metadata: `{"lawyer_id": "123", "case_id": "456"}`. During the query, the DB mathematically filters the vector space *before* the ANN search to ensure no cross-case data leakage.
2. **The Retrieval Pipeline:**
   - Propose the Hybrid Search pipeline. BM25 is mandatory because lawyers search for exact legal statutes (e.g., "Section 14.b.2"). Combine with Dense retrieval via RRF, and use a Legal-specific Cross-Encoder to extract the Top 5 chunks.
3. **Hallucination Prevention (Strict Grounding):**
   - Explain that the <abbr title="Large Language Model">LLM</abbr> prompt must enforce citations. *"Answer using the context. Cite your sources using the [DocID]."* 
   - Before returning the answer to the lawyer, run a secondary lightweight <abbr title="Large Language Model">LLM</abbr> (or regex pipeline) to explicitly verify that the generated quotes actually exist word-for-word in the retrieved chunk.

---
**Task for the end of the day:** Commit your code to Git. 

You have built the ultimate production <abbr title="Retrieval-Augmented Generation">RAG</abbr> pipeline. But what if the user's question is so vague that even Hybrid Search fails?
Tomorrow, in **Day 85**, we explore **Advanced <abbr title="Retrieval-Augmented Generation">RAG</abbr> Patterns (HyDE, RAPTOR, and GraphRAG)**!
