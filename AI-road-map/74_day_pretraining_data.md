# Day 74: Pre-training Data Pipelines (Extraction, Deduplication & Filtering)

Welcome to Day 74. You have a massive architecture, you have a perfect Tokenizer, and you have $100 Million to rent GPUs. 

Where do you get the trillions of tokens to satisfy the scaling laws? (Chinchilla-optimal for a 70B model is ~1.4 Trillion tokens; LLaMA 3 went far past that and trained on ~15 Trillion.) You scrape the entire public internet, using datasets like **Common Crawl**.
But most of the raw web is spam, duplicate boilerplate, navigation menus and SEO garbage. If you train an LLM on garbage, it will output garbage. 

Today we build the Big Data engineering pipeline that turns petabytes of raw, dirty HTML into high-quality training data.

> **Where this fits:** this is the single data day of the curriculum. It covers both halves of the problem: *extraction* (getting clean text out of the web) and *deduplication/filtering* (deciding which text deserves to be trained on). Day 91 builds the architecture that consumes this data, Day 93 trains it, and Days 100/110 cover the *post-training* data (instructions and synthetic data), which is a different problem.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Common Crawl (The Foundation)
You don't need to write a web scraper. A non-profit organization called **Common Crawl** has crawled the web continuously since 2008 and publishes each crawl for free as:
- **WARC** files: the raw HTTP responses (full HTML).
- **WET** files: Common Crawl's own plain-text extraction.
- **WAT** files: metadata and links.

Serious pipelines start from **WARC**, not WET. The WET extractor keeps menus, footers and cookie banners; re-extracting the main content from the HTML yourself (with `trafilatura` or `resiliparse`) is one of the biggest single quality wins. The FineWeb team at Hugging Face reported exactly this when they built their 15T-token dataset.

The public datasets you should know by name: **C4** (Google, T5), **The Pile** (EleutherAI), **RedPajama** (Together), **Dolma** (AI2, OLMo), **FineWeb / FineWeb-Edu** (Hugging Face) and **DCLM** (DataComp-LM, which showed that a well-trained quality classifier beats hand-written rules).

### 2. The Pipeline
To train LLaMA 3, Meta ran the web through a strict pipeline. Every modern open dataset has the same shape:
1. **Extraction:** Download the raw HTML and pull out the main text. `<div>Hello</div>` becomes `Hello`; the nav bar and footer disappear.
2. **Language Identification:** A fast classifier (like `fastText` `lid.176`) drops documents that are not in your target languages.
3. **Deduplication:** Remove exact and near-duplicate documents (and duplicated paragraphs inside documents).
4. **Quality Filtering:** Delete spam and low-quality text using heuristics, perplexity and classifiers.
5. **Toxicity & PII Removal:** Mask or drop emails, phone numbers, SSNs and extremely toxic content.
6. **Decontamination:** Make sure none of the evaluation benchmarks leaked into the training data.
7. **Mixing, Tokenizing & Sharding:** Blend web, code, books, papers and math at chosen ratios; tokenize and write fixed-size shards.

The order matters for cost: cheap filters (language, length, heuristics) run first so the expensive steps (MinHash, model-based classifiers) see less data.

### 3. The Danger of Duplicates
The WordPress footer *"Proudly powered by WordPress"* exists on millions of websites. If the exact same paragraph appears 1,000 times in your training data, the AI memorizes it perfectly. When a user writes a prompt that looks similar, the AI regurgitates the paragraph verbatim. That is a copyright and privacy problem, it wastes compute on tokens the model has already learned, and it hurts the model's ability to generalize.

There are three levels of duplication and three matching tools:
- **Exact document duplicates:** hash the normalized text (SHA-1/xxHash) and keep one per hash. Cheap and perfect, but a single changed character (`Copyright 2024` vs `Copyright 2025`) defeats it.
- **Near-duplicate documents:** MinHash LSH (next section).
- **Duplicated spans inside otherwise-unique documents:** exact substring deduplication with **suffix arrays** (Lee et al., 2022, "Deduplicating Training Data Makes Language Models Better"): any span of ~50 tokens that appears elsewhere in the corpus is cut out.

**The scale problem:** You have billions of documents. Comparing every pair (`doc1 == doc2`) is $O(N^2)$ and would take longer than the age of the universe. Even a Python `set()` of hashes for 10 Billion documents needs hundreds of GB of RAM. This is why the work runs on Spark/Ray/`datatrove` clusters across thousands of CPU cores, sharded by hash.

### 4. MinHash LSH (Near-Deduplication)
How do you find near-duplicates in roughly $O(N)$ time? **MinHash** plus **Locality Sensitive Hashing (LSH)**.
1. Break the document into small overlapping word chunks called **shingles** (n-grams, typically 5 words).
2. Two documents are similar if their shingle sets overlap: the **Jaccard similarity** $J(A,B) = \frac{|A \cap B|}{|A \cup B|}$.
3. Apply $k$ random hash functions to every shingle and keep the **minimum** hash value for each function. That $k$-number vector is the document's **signature** (its "fingerprint"). The key property: the probability that two documents agree on any one signature slot is exactly their Jaccard similarity. So the fraction of matching slots estimates $J$.
4. **LSH banding:** split the signature into $b$ bands of $r$ rows each and hash every band into a bucket. Two documents become candidates only if at least one entire band matches. The probability of that is $1 - (1 - J^r)^b$, an S-curve that is close to 0 below your threshold and close to 1 above it. You only compare documents that share a bucket.

MinHash turns a multi-year pairwise comparison into a few hours of distributed hashing. Typical production settings: 5-gram shingles, ~100–250 hash functions, threshold around 0.7–0.8.

### 5. Quality Filtering (Heuristics, Perplexity & Classifiers)
- **Heuristics:** Fast, hardcoded rules, most famously the Gopher and C4 rules. Drop documents that are too short, have no sentence-ending punctuation, are mostly numbers or symbols, have a very high fraction of repeated lines, contain "lorem ipsum" or "javascript must be enabled", or have too few common stop words.
- **Perplexity Filtering:** Take a small language model trained on clean text (CCNet used a KenLM model trained on Wikipedia). Ask it to read the document. Very high perplexity means the model is confused (incoherent garbage, keyword spam). Suspiciously low perplexity means repetitive boilerplate (`"the the the the"`).
- **Classifiers:** Take a trusted reference set (Wikipedia, textbooks, or pages referenced by Wikipedia) as "high quality" and random web pages as "low quality". Train a tiny, fast classifier (fastText) to tell them apart, and run the entire crawl through it. **FineWeb-Edu** went further: an LLM annotated ~450K pages for "educational value", a small classifier was trained on those labels, and filtering to the top scores improved knowledge and reasoning benchmarks substantially at the same token budget.

### 6. Toxicity & PII
LLMs memorize. If a Social Security Number appears in the dataset, the model might output it during a chat. Pipelines use regex plus NER tools (like Microsoft **Presidio**) to replace spans with placeholders such as `[EMAIL]` or `[PHONE_NUMBER]`, and URL blocklists to drop adult and malware domains. Be careful with aggressive toxicity classifiers: they also delete dialects and minority-community text disproportionately, which is a documented source of bias.

### 7. Decontamination (The Step That Protects Your Evals)
Decontamination means ensuring your test sets (MMLU, GSM8K, HumanEval, bar-exam questions) are **not** in your training data. The standard method: build the set of 13-gram (or 8–13 token) spans from every benchmark and drop or flag any training document that contains one. If the model reads the answer key during pre-training, it scores brilliantly on the benchmark and poorly on the real world, and you will not know until users complain.

### 8. Data Mixing & Budget
A final dataset is a *mixture*: mostly filtered web, plus upsampled code, math, scientific papers, books and multilingual text. The ratios are tuned with small proxy models before the big run, because they move benchmark scores as much as architecture choices. Budget with $C \approx 6ND$ FLOPs ($N$ parameters, $D$ tokens): a 13B model on 260B tokens (the Chinchilla ratio of ~20 tokens per parameter) is about $2 \times 10^{22}$ FLOPs. Modern models deliberately train far past 20 tokens/parameter because inference cost, not training cost, dominates their lifetime.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a miniature version of the whole pipeline: extraction, heuristic quality filtering, exact deduplication, MinHash near-deduplication with `datasketch`, and n-gram decontamination against a "benchmark".

*(You need the `datasketch` library: `pip install datasketch`.)*

Create a file named `data_pipeline.py`:

```python
import hashlib
import re

from datasketch import MinHash, MinHashLSH


# ---------- Step 1: Extraction ----------
def extract_text_from_html(html_string):
    """Strip HTML tags to get raw text.
    In production use trafilatura/resiliparse, which also drop nav bars and footers."""
    html_string = re.sub(r"<(script|style|footer|nav)[^>]*>.*?</\1>", " ", html_string, flags=re.S)
    clean_text = re.sub(r"<[^>]+>", " ", html_string)
    return " ".join(clean_text.split())


# ---------- Step 2: Heuristic quality filter ----------
def is_high_quality(text):
    """Gopher/C4-style rules. In production add a perplexity score and a fastText classifier."""
    words = text.split()
    if len(words) < 5:                                   # menus, fragments
        return False
    if not any(ch in text for ch in ".?!"):              # no sentences
        return False
    if sum(w.isupper() for w in words) / len(words) > 0.3:   # SHOUTING spam
        return False
    if len(set(words)) / len(words) < 0.3:               # "buy buy buy buy"
        return False
    return True


# ---------- Step 3: Exact deduplication ----------
def exact_dedup(docs):
    """Hash normalized text; keep the first document per hash."""
    seen, kept = set(), {}
    for doc_id, text in docs.items():
        digest = hashlib.sha1(text.lower().encode("utf8")).hexdigest()
        if digest not in seen:
            seen.add(digest)
            kept[doc_id] = text
    return kept


# ---------- Step 4: MinHash LSH near-deduplication ----------
def shingles(text, n=3):
    """'the dog barked loud' -> ['the dog barked', 'dog barked loud']"""
    words = re.sub(r"[^\w\s]", "", text.lower()).split()
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def near_dedup(docs, threshold=0.5, num_perm=128):
    # threshold is the Jaccard similarity above which two docs count as duplicates.
    # Production pipelines use ~0.7-0.8 on 5-gram shingles over long documents;
    # our toy documents are tiny, so we use 3-grams and a lower threshold.
    lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    kept = {}
    for doc_id, text in docs.items():
        m = MinHash(num_perm=num_perm)
        for sh in shingles(text):
            m.update(sh.encode("utf8"))
        matches = lsh.query(m)          # only compares against docs in the same LSH buckets
        if matches:
            print(f"   near-duplicate: {doc_id} ~ {matches} -> dropped")
            continue
        lsh.insert(doc_id, m)
        kept[doc_id] = text
    return kept


# ---------- Step 5: Decontamination ----------
def decontaminate(docs, benchmark_questions, n=8):
    """Drop any training doc sharing an n-gram with a benchmark item (real pipelines use ~13-grams)."""
    bench_ngrams = set()
    for q in benchmark_questions:
        bench_ngrams |= shingles(q, n)
    kept = {}
    for doc_id, text in docs.items():
        if shingles(text, n) & bench_ngrams:
            print(f"   contaminated: {doc_id} overlaps a benchmark question -> dropped")
            continue
        kept[doc_id] = text
    return kept


def run_pipeline():
    raw_crawl = {
        "d1": "<html><body><h1>The History of Rome</h1><p>Rome was founded in 753 BC according to legend, "
              "and grew from a small town on the Tiber into a vast empire.</p></body></html>",
        "d2": "<div>CLICK HERE BUY CHEAP SHOES NOW!!!</div>",
        "d3": "<html><body><p>Rome was founded in 753 BC according to legend, and grew from a small town "
              "on the Tiber into a vast empire.</p><footer>Copyright 2024</footer></body></html>",
        "d4": "<p>Home | About | Contact</p>",
        "d5": "<html><body><h1>The History of Rome</h1><p>Rome was founded in 753 BC according to legend, "
              "and grew from a small town on the Tiber into a vast empire.</p></body></html>",
        "d6": "<p>Machine learning is the future of artificial intelligence and will change every industry.</p>",
        "d7": "<p>Machine learning is the future of artificial intelligence and will change every industry! Buy now!</p>",
        "d8": "<p>Janet's ducks lay 16 eggs per day. She eats three for breakfast every morning and bakes "
              "muffins for her friends every day with four.</p>",
    }
    benchmark = ["Janet's ducks lay 16 eggs per day. She eats three for breakfast every morning and bakes "
                 "muffins for her friends every day with four. How much does she make every day?"]

    print(f"Raw documents: {len(raw_crawl)}")
    docs = {k: extract_text_from_html(v) for k, v in raw_crawl.items()}

    docs = {k: v for k, v in docs.items() if is_high_quality(v)}
    print(f"After quality filter: {len(docs)}  {sorted(docs)}")

    docs = exact_dedup(docs)
    print(f"After exact dedup:    {len(docs)}  {sorted(docs)}")

    print("MinHash LSH:")
    docs = near_dedup(docs)
    print(f"After near dedup:     {len(docs)}  {sorted(docs)}")

    print("Decontamination:")
    docs = decontaminate(docs, benchmark)
    print(f"Final corpus:         {len(docs)}  {sorted(docs)}")


if __name__ == "__main__":
    run_pipeline()
```

### Key Takeaways from Code:
1. **Each stage catches what the previous one can't.** The heuristics drop the shouting spam (`d2`) and the menu bar (`d4`). `d5` is byte-identical to `d1`, so the cheap hash removes it. `d3` is the same article on a different page layout (no heading), so its hash differs and it survives exact dedup; MinHash catches it. `d7` ("...! Buy now!") shares most of its shingles with `d6`, so it lands in the same LSH bucket and is dropped. Exact matching would have missed both. Expected final corpus: `['d1', 'd6']`.
2. **The LSH query does not scan every document.** `lsh.query(m)` hashes the signature's bands into buckets and only compares against the handful of documents already in those buckets. That is what makes near-dedup scale to billions of documents.
3. **Decontamination is just n-gram overlap.** `d8` is a GSM8K-style question that leaked onto a web page. If it stayed, your model would "solve" that benchmark item by memory.
4. **The scale problem:** the in-memory `set()` and LSH index work for 8 documents. For 10 Billion, you shard by hash across a Spark/Ray cluster and run each stage as a distributed job.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge (pick one, or both)
**A. The Perplexity Filter.** You have removed duplicates. Now remove the spam that heuristics miss.
1. Load a tiny pre-trained GPT-2 model.
2. Pass each scraped paragraph through it and calculate its **perplexity** (the exponential of the average cross-entropy loss): how "surprised" the model is by the text.
3. If the perplexity is extremely high (gibberish, keyword stuffing), delete the document.
4. If the perplexity is extremely low (e.g., `"The the the the"`), also delete it: that is repetitive boilerplate.
5. Plot the perplexity histogram of your corpus and pick the cut-offs from the tails, not from a guess.

**B. Exact Substring Deduplication.** MinHash finds documents that are *mostly* similar. But what if an otherwise unique document contains one paragraph copied from elsewhere?
1. Tokenize every document and slide a 50-token window across it.
2. Hash every window and count hashes across the whole corpus (the production version uses a suffix array so it finds every repeated span, not just aligned windows).
3. Any window seen more than once elsewhere is physically sliced out of the document before training.
4. Report what fraction of tokens you removed and look at the most common removed spans (you will find license text, cookie banners and forum signatures).

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You have a budget of $10M to train a 13B parameter model and 5TB of raw web text. Walk through every engineering decision: data collection, cleaning, deduplication, PII scrubbing, tokenizer, architecture, training infrastructure and evaluation. What is decontamination, and what is the single biggest risk that could ruin the model?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Architecture & Tokenizer:** 
   - Propose a Decoder-only architecture using Pre-Norm (RMSNorm), SwiGLU, RoPE and GQA. 
   - State that you will train a custom BPE Tokenizer, ensuring you up-sample code and multilingual text to balance the fertility disparity.
2. **The Data Pipeline (The true differentiator):**
   - Chinchilla says 13B parameters wants ~260 Billion tokens as a floor; say you would go well past it if the data exists, because a smaller over-trained model is cheaper to serve.
   - Detail the pipeline: WARC $\rightarrow$ main-content extraction $\rightarrow$ language ID $\rightarrow$ exact + MinHash deduplication $\rightarrow$ heuristic + classifier quality filtering $\rightarrow$ PII scrubbing $\rightarrow$ Decontamination $\rightarrow$ mixing with code/math/books. 
   - State that it cannot run on one machine: Spark, Ray or `datatrove` across hundreds of CPU nodes, sharded by hash.
3. **PII Scrubbing:**
   - LLMs memorize. Use regex + NER pipelines (like Microsoft Presidio) to replace `[EMAIL]` and `[PHONE_NUMBER]` during extraction, and drop blocklisted domains.
4. **Infrastructure:**
   - PyTorch FSDP (Fully Sharded Data Parallel) across on the order of 1,000 GPUs, checkpointing often (Day 93–95).
   - Validate data choices with small proxy models before committing the budget.
5. **The Biggest Risk: Data Contamination.**
   - If your benchmarks (e.g., MMLU, HumanEval) leak into your training data, the model memorizes the test. You spend $10M, get a great score, release the model, and discover it is much weaker in the real world. Decontamination (n-gram overlap against every eval set, run *before* training) is the most important step to get right, and a strong candidate also mentions holding out private, never-published evals.

---
**Task for the end of the day:** Commit your code to Git. 

You have built the architecture. You have gathered the data. In the final Chunk (Days 75-76), we assume the massive model is trained. We will learn how to adapt it to a new domain, and how to compress it using **Knowledge Distillation** so it can run on an iPhone!
