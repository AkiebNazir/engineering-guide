# Day 74: Pre-training Data Pipelines (Deduplication)

Welcome to Day 74. You have a massive architecture, you have a perfect Tokenizer, and you have $100 Million to rent GPUs. 

Where do you get the 1.4 Trillion tokens to satisfy the Chinchilla scaling laws? You scrape the entire internet (using datasets like Common Crawl).
But the internet is $80\%$ spam, duplicate boilerplate, and SEO garbage. If you train an <abbr title="Large Language Model">LLM</abbr> on garbage, it will output garbage. 

Today we build the massive Big Data engineering pipeline that cleans the internet.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The 4-Step Pipeline
To train LLaMA 3, Meta ran the entire internet through a strict pipeline:
1. **Extraction:** Download the raw HTML.
2. **Deduplication:** Remove exact and near-duplicate paragraphs.
3. **Quality Filtering:** Delete spam and low-quality text using Heuristics and Classifiers.
4. **Decontamination:** Ensure that none of the testing benchmarks (like Medical Exams) accidentally leaked into the training data!

### 2. The Danger of Duplicates
If the exact same paragraph appears 1,000 times in your training data, the <abbr title="Artificial Intelligence">AI</abbr> will memorize it perfectly. When a user writes a prompt that looks similar, the <abbr title="Artificial Intelligence">AI</abbr> will regurgitate the paragraph verbatim. This is plagiarism, and it ruins the model's ability to generalize.
**The Problem:** You have 100 Million documents. If you try to do an exact string comparison (`doc1 == doc2`) across all of them, the $O(N^2)$ algorithm will take 50,000 years to run.

### 3. MinHash LSH (Near-Deduplication)
How do you find near-duplicates in $O(N)$ time? We use **MinHash Locality Sensitive Hashing (LSH)**.
1. Break the document into small overlapping 5-word chunks called **N-Grams**.
2. Run a mathematical hash function over these N-Grams to create a unique "Fingerprint" for the document.
3. If two documents have a 90% overlapping fingerprint, they are flagged as duplicates and deleted! MinHash reduces a 50,000-year compute job into a 3-hour job.

### 4. Quality Filtering (Heuristics & Classifiers)
- **Heuristics:** Fast, hardcoded rules. (e.g., If the text has no punctuation, delete it. If the text is $90\%$ numbers, delete it. If the text has 50 consecutive curse words, delete it).
- **Classifiers:** We take Wikipedia (High Quality) and raw Reddit comments (Low Quality). We train a tiny, fast <abbr title="Artificial Intelligence">AI</abbr> classifier to distinguish between them. We then run the entire internet through this classifier. If the classifier says a webpage is low quality, we delete it!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a simulated Big Data pipeline using `datasketch` to implement MinHash deduplication!

*(Note: You will need the `datasketch` library. Mentally run `pip install datasketch`)*

Create a file named `data_pipeline.py`:

```python
from datasketch import MinHash, MinHashLSH

def extract_ngrams(text, n=3):
    """
    Splits text into overlapping chunks of N words.
    "The dog barked loud" -> ["The dog barked", "dog barked loud"]
    """
    words = text.lower().split()
    return [" ".join(words[i:i+n]) for i in range(len(words)-n+1)]

def build_deduplication_pipeline():
    print("--- RUNNING MINHASH DEDUPLICATION PIPELINE ---")
    
    # 1. Our scraped internet data
    documents = {
        "doc1": "Machine learning is the future of artificial intelligence.",
        "doc2": "Deep learning models require massive amounts of compute.",
        "doc3": "Machine learning is the future of artificial intelligence! Buy now!", # Near-duplicate of doc1
        "doc4": "Cats are great pets to have in your home."
    }
    
    # 2. Initialize the LSH Index
    # threshold=0.8 means we flag documents that are 80% similar!
    # num_perm=128 is the resolution of our fingerprint.
    lsh = MinHashLSH(threshold=0.8, num_perm=128)
    
    minhashes = {}
    
    # 3. Create a MinHash Fingerprint for every document
    for doc_id, text in documents.items():
        # Initialize an empty fingerprint
        m = MinHash(num_perm=128)
        
        # Extract 3-word chunks
        ngrams = extract_ngrams(text, n=3)
        
        # Update the fingerprint with the chunks
        for ngram in ngrams:
            m.update(ngram.encode('utf8'))
            
        minhashes[doc_id] = m
        
        # Insert the fingerprint into our LSH Database
        lsh.insert(doc_id, m)
        
    print(f"Processed {len(documents)} documents.\n")
    
    # 4. Find the Duplicates!
    duplicates_to_delete = set()
    
    for doc_id, m in minhashes.items():
        # Query the LSH index for ANY fingerprint that is 80% similar!
        # This search happens in O(1) time because of LSH!
        similar_docs = lsh.query(m)
        
        # We ignore matches with itself
        similar_docs.remove(doc_id)
        
        if similar_docs:
            print(f"⚠️ Near-Duplicate Found! '{doc_id}' is 80% similar to {similar_docs}")
            # Mark for deletion (keep doc1, delete doc3)
            duplicates_to_delete.update(similar_docs)
            
    print("\n--- FINAL CLEANED DATASET ---")
    for doc_id in documents:
        if doc_id not in duplicates_to_delete:
            print(f"Keep: {doc_id}")

if __name__ == "__main__":
    build_deduplication_pipeline()
```

### Key Takeaways from Code:
1. **The $O(1)$ Query:** `lsh.query(m)` does not scan every document. LSH (Locality Sensitive Hashing) mathematically drops the fingerprint into a specific "bucket". It only compares the fingerprint against the other 5 fingerprints in that exact bucket, returning results instantly!
2. **N-Grams:** Notice how `doc3` had extra words ("Buy now!"). Because we broke it into 3-word overlapping chunks, the first 6 chunks perfectly matched `doc1`, triggering the 80% similarity threshold. Exact string matching would have completely failed to catch this!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Perplexity Filter
You have removed duplicates. Now you must remove spam (like `"a a a a a a a"`).
**Your Task:**
1. You have a tiny, pre-trained GPT-2 model.
2. You pass a scraped paragraph into GPT-2. 
3. Calculate the **Perplexity** (the exponential of the Cross-Entropy Loss). 
4. Perplexity mathematically measures how "surprised" the <abbr title="Artificial Intelligence">AI</abbr> is by the text.
5. If the perplexity is extremely high (the text is absolute gibberish), you delete the document.
6. If the perplexity is extremely low (e.g., `"The the the the"`), you also delete it because it is repetitive spam!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You have a budget of $10M to train a 13B parameter model. Walk through every engineering decision: data collection, cleaning, tokenizer training, model architecture, training infrastructure, and evaluation. What is the single biggest risk that could ruin the model?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Architecture & Tokenizer:** 
   - Propose a Decoder-only architecture using Pre-Norm, SwiGLU, and RoPE. 
   - State that you will train a custom <abbr title="Byte Pair Encoding">BPE</abbr> Tokenizer, ensuring you up-sample code and multilingual text to balance the fertility disparity.
2. **The Data Pipeline (The true differentiator):**
   - According to Chinchilla, 13B parameters requires ~260 Billion tokens. 
   - Detail the pipeline: CommonCrawl $\rightarrow$ MinHash Deduplication $\rightarrow$ Quality Classifier $\rightarrow$ Decontamination. 
3. **Infrastructure & The Biggest Risk:**
   - Mention using PyTorch FSDP (Fully Sharded Data Parallel) across 1,000 GPUs.
   - Identify the single biggest risk: **Data Contamination**. If your testing benchmarks (e.g., MMLU, HumanEval) accidentally leak into your training data, your model will perfectly memorize the test. You will spend $10M, get a perfect score, release the model, and realize it is utterly useless in the real world. Decontamination (running MinHash against the test sets) is the most critical step.

---
**Task for the end of the day:** Commit your code to Git. 

You have built the architecture. You have gathered the data. In the final Chunk (Days 75-76), we assume the massive model is trained. We will learn how to adapt it, and how to compress it using **Knowledge Distillation** so it can run on an iPhone!
