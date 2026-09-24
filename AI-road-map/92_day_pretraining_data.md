# Day 92: Pre-Training Data (Extraction & Deduplication)

Welcome to Day 92. A model is only as smart as the data it reads. 
LLaMA 3 was trained on 15 Trillion tokens. Where do you get 15 Trillion words? You scrape the entire public internet.

Today, we look at the massive Data Engineering pipelines required to process Petabytes of raw, dirty HTML into high-quality training data.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Common Crawl (The Foundation)
You don't need to write a web scraper. A non-profit organization called **Common Crawl** scrapes the internet continuously and releases petabytes of raw WARC (Web Archive) files for free. 
The problem? 90% of the internet is garbage (SEO spam, porn, duplicate footers, and malicious code). If you train a model on raw Common Crawl, the model will be toxic and stupid.

### 2. The Data Processing Pipeline
To turn Common Crawl into a dataset like **RedPajama** or **FineWeb**, you must run a massive pipeline across thousands of CPUs:
1. **Extraction:** Strip the HTML tags. Convert `<div>Hello</div>` into plain text.
2. **Language Detection:** Use a fast classifier (like `fastText`) to drop any document that isn't English (if you are building an English-only model).
3. **Quality Filtering (Perplexity):** How do you detect SEO spam programmatically? You take a tiny, previously trained model (like a 100M parameter model). You ask it to read the document. If the model outputs a massive **Perplexity Score** (meaning the model is highly confused by the text), the text is probably incoherent garbage. Delete it!
4. **Toxicity/PII Removal:** Run regex or fast classifiers to delete documents containing SSNs, phone numbers, and extreme toxicity.

### 3. The Deduplication Problem (MinHash)
The internet is full of duplicates. The WordPress footer *"Proudly powered by WordPress"* exists on 100 Million websites.
If you train an LLM on 100 Million identical sentences, the LLM will overfit. It will literally memorize the string and spit it out randomly.
**The Solution: MinHash & Jaccard Similarity.**
Exact string matching ($O(N^2)$) would take years for petabytes of data. 
MinHash mathematically hashes every document into a tiny "Signature" vector. It then compares the signatures to calculate the Approximate Jaccard Similarity. It can find documents that are $95\%$ identical in milliseconds, allowing you to delete the 99 Million duplicate footers!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a mock Data Processing Pipeline. We will simulate extracting text, calculating Exact Substring Deduplication, and filtering by a mock quality score.

Create a file named `data_pipeline.py`:

```python
import re

def extract_text_from_html(html_string):
    """
    Step 1: Strip HTML tags to get raw text.
    In production, use a fast C++ library like `trafilatura` or `lxml`.
    """
    # Naive Regex to remove anything inside < >
    clean_text = re.sub(r'<[^>]+>', ' ', html_string)
    # Remove extra whitespace
    return " ".join(clean_text.split())

def is_high_quality(text):
    """
    Step 2: Quality Heuristics.
    In production, this is a Perplexity score from a tiny LM or a fastText classifier.
    """
    # Simple heuristic: If it's too short, or lacks punctuation, it's probably a menu bar or spam.
    if len(text.split()) < 5:
        return False
    if not any(char in text for char in ['.', '?', '!']):
        return False
    return True

def exact_deduplication(documents):
    """
    Step 3: Deduplication.
    This is an Exact Deduplication (using a Python Set).
    In production, use MinHash for Fuzzy Deduplication.
    """
    unique_docs = set()
    deduped_corpus = []
    
    for doc in documents:
        if doc not in unique_docs:
            unique_docs.add(doc)
            deduped_corpus.append(doc)
            
    return deduped_corpus

def test_pipeline():
    print("--- RUNNING PRE-TRAINING DATA PIPELINE ---\n")
    
    # 1. Raw Web Scrape (Simulating Common Crawl)
    raw_crawl = [
        "<html><body><h1>The History of Rome</h1><p>Rome was founded in 753 BC.</p></body></html>",
        "<div>Click here to buy cheap shoes!!!</div>",
        "<html><body><p>Rome was founded in 753 BC.</p><footer>Copyright 2024</footer></body></html>",
        "<p>This is just a random fragment</p>",
        "<html><body><h1>The History of Rome</h1><p>Rome was founded in 753 BC.</p></body></html>" # Exact duplicate
    ]
    
    print(f"Total Raw Documents: {len(raw_crawl)}")
    
    # 2. Extraction Pipeline
    extracted_texts = [extract_text_from_html(html) for html in raw_crawl]
    print("\n--- After Extraction ---")
    for t in extracted_texts: print(f"-> {t}")
    
    # 3. Quality Filtering
    high_quality_texts = [t for t in extracted_texts if is_high_quality(t)]
    print(f"\n--- After Quality Filtering (Removed {len(extracted_texts) - len(high_quality_texts)} docs) ---")
    for t in high_quality_texts: print(f"-> {t}")
    
    # 4. Deduplication
    final_corpus = exact_deduplication(high_quality_texts)
    print(f"\n--- After Deduplication (Removed {len(high_quality_texts) - len(final_corpus)} exact duplicates) ---")
    for t in final_corpus: print(f"-> {t}")
    
    print(f"\nFinal Training Corpus Size: {len(final_corpus)} documents.")

if __name__ == "__main__":
    test_pipeline()
```

### Key Takeaways from Code:
1. **The Scale Problem:** The Python `set()` is perfect for 100 documents. But if you have 10 Billion documents, the `unique_docs` set will consume Terabytes of RAM and crash the server. This is why Databricks/Spark and advanced algorithms like MinHash LSH (Locality-Sensitive Hashing) are mandatory.
2. **The "Copyright" Problem:** Notice how Document #1 and Document #3 both survived deduplication. Even though the core text ("Rome was founded...") is identical, the presence of the word "Copyright 2024" in Doc 3 made the strings officially different! Exact deduplication fails here. Only Fuzzy Deduplication (MinHash) catches this!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: N-Gram Substring Deduplication
MinHash finds documents that are mostly similar. But what if a massive document contains one single paragraph of duplicate data? 
**Your Task:**
1. Conceptually design an **Exact Substring Deduplicator** using Suffix Arrays.
2. Break a document into 50-word chunks.
3. Hash the chunk.
4. If that exact 50-word chunk has been seen anywhere else in the massive 10TB dataset, physically slice it out of the document before training!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are curating training data for a 13B model. You have 5TB of raw web text. Walk through your complete pipeline including Deduplication, PII scrubbing, and Decontamination. Specifically, what is Decontamination and why does it matter?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Pipeline Scale:** 
   - State that you cannot run this on a single machine. You must use Apache Spark or Ray clusters to distribute the MinHash LSH and Quality Filtering logic across hundreds of CPU nodes.
2. **PII Scrubbing:**
   - Explain that LLMs memorize data. If a Social Security Number is in the dataset, the LLM might output it during a chat. You must use regex pipelines (like Microsoft's Presidio) to mask `[PHONE_NUMBER]` or `[EMAIL]` during the extraction phase.
3. **Decontamination (The Holy Grail):**
   - Decontamination means ensuring your test sets (like the GSM8k math benchmark or the Bar Exam questions) are **NOT** in your training data! 
   - If the LLM reads the Bar Exam during training, it will get a 100% on the test, but it didn't actually learn law—it just memorized the answer key (Data Leakage). You must run strict N-Gram deduplication against all known public benchmarks *before* training begins!

---
**Task for the end of the day:** Commit your code to Git. 

We now have 15 Trillion tokens of clean data, and a 70 Billion parameter architecture. 
But a 70B model requires 140 Gigabytes of VRAM just to load! An NVIDIA A100 GPU only has 80GB. **It physically does not fit.**

Tomorrow, we enter the most difficult DevOps engineering on the planet. **Day 93: Distributed Training (FSDP, Tensor Parallelism, and Pipeline Parallelism)**!
