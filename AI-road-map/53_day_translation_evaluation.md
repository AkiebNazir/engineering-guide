# Day 53: Machine Translation Evaluation & Data Augmentation

Welcome to Day 53. If you build a Seq2Seq translation model, you cannot evaluate it using standard Accuracy.

- **Human Reference:** *"The cat sat on the mat."*
- **<abbr title="Artificial Intelligence">AI</abbr> Prediction 1:** *"The feline rested on the rug."*
- **<abbr title="Artificial Intelligence">AI</abbr> Prediction 2:** *"The mat on sat cat the."*

If you use strict mathematical Accuracy, both Prediction 1 and Prediction 2 get $0\%$. But Prediction 1 is a perfect, fluent translation! Prediction 2 is complete garbage. 
How do we mathematically teach a computer to grade fluency and meaning?

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. BLEU Score (Bilingual Evaluation Understudy)
In 2002, IBM invented the **BLEU Score**. It became the absolute industry standard for grading translations.
Instead of checking if the entire sentence matches perfectly, BLEU checks the overlap of **N-grams** (1-word, 2-word, 3-word, and 4-word phrases).
- If the <abbr title="Artificial Intelligence">AI</abbr> writes *"rested on the rug"*, and the human reference contains the exact 4-word phrase *"rested on the rug"*, the <abbr title="Artificial Intelligence">AI</abbr> gets a massive score boost for matching a 4-gram. 
- Matching a 4-gram mathematically proves that the <abbr title="Artificial Intelligence">AI</abbr> understands grammar and word ordering, because guessing 4 words in a row perfectly by pure chance is impossible.

### 2. The Brevity Penalty
What if the <abbr title="Artificial Intelligence">AI</abbr> figures out a cheat code? What if the human writes a 10-word sentence, and the <abbr title="Artificial Intelligence">AI</abbr> just outputs the word *"The"* and stops. The 1-gram precision is $100\%$ because *"The"* is in the reference!
To stop this, BLEU introduces the **Brevity Penalty (BP)**. If the <abbr title="Artificial Intelligence">AI</abbr>'s translation is shorter than the human's reference, BLEU mathematically slashes the final score, forcing the <abbr title="Artificial Intelligence">AI</abbr> to output full-length sentences.

### 3. Modern Metrics: METEOR & BERTScore
BLEU is fast, but it is flawed because it does not understand synonyms (*cat* vs *feline*).
- **METEOR:** A metric that literally includes a dictionary. If the <abbr title="Artificial Intelligence">AI</abbr> guesses a synonym of the reference word, it still gets points!
- **BERTScore:** The modern state-of-the-art. It uses a pre-trained Transformer (BERT) to convert the <abbr title="Artificial Intelligence">AI</abbr>'s sentence and the Human's sentence into 300D Word Embeddings, and then calculates the Cosine Similarity between the math vectors!

### 4. Back-Translation (Data Augmentation)
To train Google Translate, you need 10 million pairs of `(English, French)` sentences translated by a highly paid human. This is incredibly expensive.
**Back-Translation** is a genius hack:
1. You have a tiny dataset of 10k human-translated `(English, French)` pairs.
2. You train a weak `French -> English` model.
3. You go to French Wikipedia and download 1,000,000 random French sentences (No English translations exist).
4. You run them through your weak model to generate 1,000,000 synthetic English sentences. 
5. You now have 1,000,000 synthetic `(English, French)` pairs! You mix them with your human data and train your main `English -> French` model. The performance violently skyrockets.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a simplified version of the BLEU metric entirely from scratch in Python to see exactly how N-gram matching is mathematically calculated.

Create a file named `bleu_metric.py`:

```python
import math
from collections import Counter

def get_ngrams(sequence, n):
    """
    Extracts all N-grams from a list of words.
    e.g., n=2 on ["The", "cat", "sat"] -> [("The", "cat"), ("cat", "sat")]
    """
    ngrams = []
    for i in range(len(sequence) - n + 1):
        ngrams.append(tuple(sequence[i:i+n]))
    return ngrams

def modified_precision(candidate, reference, n):
    """
    Calculates how many of the AI's N-grams actually exist in the Human's reference.
    """
    cand_ngrams = get_ngrams(candidate, n)
    ref_ngrams = get_ngrams(reference, n)
    
    if not cand_ngrams:
        return 0.0
        
    cand_counts = Counter(cand_ngrams)
    ref_counts = Counter(ref_ngrams)
    
    # We "clip" the count! If the AI generates "the the the the", but the reference
    # only has one "the", the AI only gets credit for ONE "the"!
    clipped_counts = {ngram: min(count, ref_counts[ngram]) 
                      for ngram, count in cand_counts.items()}
                      
    return sum(clipped_counts.values()) / len(cand_ngrams)

def calculate_bleu(candidate_sentence, reference_sentence, max_n=4):
    """
    The Full BLEU Score Algorithm.
    """
    cand = candidate_sentence.split()
    ref = reference_sentence.split()
    
    # 1. Calculate N-gram precisions (1-gram through 4-gram)
    precisions = []
    for n in range(1, max_n + 1):
        p_n = modified_precision(cand, ref, n)
        # Avoid log(0) error
        if p_n == 0:
            return 0.0
        precisions.append(p_n)
        
    # 2. Average the Precisions (Geometric Mean)
    # We take the log, average them, and exponentiate
    avg_precision = math.exp(sum(math.log(p) for p in precisions) / max_n)
    
    # 3. Calculate Brevity Penalty (BP)
    # If the candidate is shorter than the reference, we penalize it!
    cand_len = len(cand)
    ref_len = len(ref)
    
    if cand_len > ref_len:
        bp = 1.0
    else:
        bp = math.exp(1 - float(ref_len) / cand_len)
        
    # 4. Final Score!
    bleu_score = bp * avg_precision
    return bleu_score

def test_bleu():
    print("--- RUNNING BLEU SCORE EVALUATION ---")
    
    reference = "the cat is on the mat"
    
    # Example 1: Perfect translation
    cand1 = "the cat is on the mat"
    
    # Example 2: Good 1-grams, terrible grammar (order is wrong)
    cand2 = "the mat on the is cat"
    
    # Example 3: The AI tries to cheat by outputting short sentences
    cand3 = "the cat"
    
    print(f"Reference: '{reference}'\n")
    print(f"Candidate 1 ('{cand1}'): BLEU = {calculate_bleu(cand1, reference):.4f}")
    print(f"Candidate 2 ('{cand2}'): BLEU = {calculate_bleu(cand2, reference):.4f}")
    print(f"Candidate 3 ('{cand3}'):   BLEU = {calculate_bleu(cand3, reference):.4f}")
    
    print("\nNotice how Candidate 2 failed completely because its 2-grams and 3-grams were wrong.")
    print("Notice how Candidate 3 was destroyed by the Brevity Penalty!")

if __name__ == "__main__":
    test_bleu()
```

### Key Takeaways from Code:
1. **The Clipping Hack:** In `modified_precision`, notice the `min(count, ref_counts)`. Without this, an <abbr title="Artificial Intelligence">AI</abbr> could achieve 100% precision by translating everything as `"the the the the the"`. By clipping it against the reference, the <abbr title="Artificial Intelligence">AI</abbr> is mathematically stopped from repeating high-frequency words!
2. **Geometric Mean:** BLEU averages the 1-gram, 2-gram, 3-gram, and 4-gram scores using a `log` Geometric Mean. This means if the 4-gram score is $0$, the entire BLEU score drops to $0$. It is extremely strict.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Back-Translation Pipeline
You need to generate synthetic data.
**Your Task:**
1. Assume you have a PyTorch `French_to_English_Model` in memory.
2. Assume you have a CSV file with 1,000,000 monolingual French sentences.
3. Write a PyTorch inference loop that reads the French sentences in batches of 128.
4. Pass them through the model to generate English predictions using `argmax`.
5. Save the original French and the predicted English into a new CSV file formatted as `(synthetic_english, real_french)`. You just successfully augmented your dataset!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"BLEU score is the industry standard, but it often correlates poorly with actual human judgment, especially for languages with free word order (like Russian) or morphologically rich languages (like Arabic). Design a robust evaluation strategy for a production system serving 50 diverse language pairs."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Diagnose BLEU's Flaw:** 
   - Explain that BLEU relies on exact N-gram surface-level matching. In Russian, changing the word order often keeps the exact same meaning, but it completely destroys the BLEU 4-gram score. BLEU mathematically punishes correct translations.
2. **The Metric Ensemble Strategy:**
   - Propose using a suite of automated metrics. Keep BLEU for legacy baselines, but implement **chrF** (Character F-score) which excels at morphologically rich languages (because it matches sub-word prefixes/suffixes), and **COMET / BERTScore** to evaluate deep semantic meaning instead of surface tokens.
3. **The Human-in-the-Loop Strategy:**
   - Conclude that automated metrics are never enough for production. Propose an A/B testing pipeline where 1% of live traffic is evaluated by professional linguists using the **MQM (Multidimensional Quality Metrics)** framework to grade specific errors (fluency vs accuracy), giving the <abbr title="Machine Learning">ML</abbr> team actionable feedback.

---
**Task for the end of the day:** Commit your code to Git. You now know how to grade sequence models.

Tomorrow, in **Day 54**, we step away from Text entirely. We enter the world of Audio. Welcome to **Mel Spectrograms and Speech Recognition!**
