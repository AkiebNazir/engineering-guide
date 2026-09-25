# Day 68: BERT Pre-training & Fine-tuning

Welcome to Day 68. Yesterday, we built the final piece of the Transformer architecture. But architecture is just math. A Transformer without data is just a random number generator.

To make an <abbr title="Artificial Intelligence">AI</abbr> intelligent, you must train it on a massive corpus of text (like the entire internet). But the internet doesn't come with human labels. How do you train a Neural Network using Cross-Entropy Loss if you don't have a label? 
Today, we learn the genius of **Self-Supervised Learning**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Pre-train / Fine-tune Paradigm Shift
Before 2018, if you wanted an <abbr title="Artificial Intelligence">AI</abbr> to classify Medical Documents, you had to hire doctors to label 100,000 documents, and then train an <abbr title="Long Short-Term Memory">LSTM</abbr> from scratch. It took months and cost millions.
BERT changed the world by splitting training into two phases:
1. **Pre-training:** Google trained BERT on all of Wikipedia and thousands of books. This cost millions of dollars and took weeks on massive GPU clusters. The model learned facts, logic, and grammar.
2. **Fine-tuning:** You download Google's pre-trained BERT for free. You train it on your MacBook for 1 hour using only 500 labeled Medical Documents. Because BERT already knows English, it instantly adapts to the medical domain and achieves state-of-the-art accuracy!

### 2. Masked Language Modeling (MLM)
How did Google train BERT without human labels? By turning the text itself into the label!
They took a sentence: *"The dog chased the cat across the yard."*
They mathematically corrupted the sentence by hiding 15% of the words:
*"The [MASK] chased the [MASK] across the yard."*

They passed this corrupted sentence into the BERT Encoder. The objective was simple: **Predict the missing words.**
Because BERT is bidirectional, the first `[MASK]` looks forward at *"chased"* and backwards at *"The"*, and mathematically deduces that the missing word is likely an animal. 

By playing this "fill-in-the-blank" game on 3 Billion words, BERT accidentally learned the entire structure of the human language!

### 3. The 80-10-10 Rule
If the <abbr title="Artificial Intelligence">AI</abbr> only ever sees `[MASK]` tokens during Pre-training, it will crash during Fine-tuning because real users don't type `[MASK]` in their sentences!
To fix this, Google applied a strict rule to the 15% of words chosen for corruption:
- **80% of the time:** Replace with `[MASK]`.
- **10% of the time:** Replace with a completely random word (e.g., *"The apple chased the cat"*). This forces the <abbr title="Artificial Intelligence">AI</abbr> to constantly double-check if a word makes logical sense!
- **10% of the time:** Leave the word exactly as it is. This proves to the <abbr title="Artificial Intelligence">AI</abbr> that sometimes the input is already perfectly correct.

### 4. Next Sentence Prediction (NSP)
Google also trained BERT on a second task simultaneously. They gave BERT two sentences (A and B), and asked: *"Does B logically follow A?"*
- 50% of the time, B was the actual next sentence.
- 50% of the time, B was a random sentence from a different book.
*(Note: A year later, Facebook released RoBERTa, which proved that NSP was actually completely useless and sometimes hurt training. Modern encoders exclusively use MLM!)*

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's implement the core logic of Masked Language Modeling from scratch. We will write the code that mathematically corrupts a sentence using the 80-10-10 rule!

Create a file named `bert_mlm_corruption.py`:

```python
import torch

def create_mlm_data(sentence_tokens, vocab_size, mask_token_id=0):
    """
    Applies the BERT 15% corruption rule to a batch of sentences.
    """
    # Clone the sentences so we don't destroy the original labels!
    inputs = sentence_tokens.clone()
    labels = sentence_tokens.clone()
    
    # Create a random matrix of the exact same shape
    # Values are between 0.0 and 1.0
    probability_matrix = torch.rand(labels.shape)
    
    # We want to corrupt 15% of the tokens. 
    # Create a boolean mask where the random number is < 0.15
    corruption_mask = probability_matrix < 0.15
    
    # BUT! We don't want to calculate loss on the 85% of words we DIDN'T corrupt.
    # In PyTorch, a label of -100 tells the CrossEntropyLoss function to completely ignore it!
    labels[~corruption_mask] = -100 
    
    # --- NOW APPLY THE 80/10/10 RULE to the corrupted 15% ---
    
    # Generate another random matrix to decide HOW to corrupt them
    corruption_type = torch.rand(labels.shape)
    
    # 1. 80% of the time: Replace with [MASK]
    mask_80_percent = corruption_mask & (corruption_type < 0.8)
    inputs[mask_80_percent] = mask_token_id
    
    # 2. 10% of the time: Replace with random word
    # (Values between 0.8 and 0.9)
    mask_10_percent = corruption_mask & (corruption_type >= 0.8) & (corruption_type < 0.9)
    random_words = torch.randint(1, vocab_size, labels.shape)
    inputs[mask_10_percent] = random_words[mask_10_percent]
    
    # 3. 10% of the time: Leave unchanged
    # (Values >= 0.9. We do nothing!)
    
    return inputs, labels

def test_mlm():
    print("--- RUNNING BERT MASKED LANGUAGE MODELING ---")
    
    VOCAB_SIZE = 1000
    MASK_ID = 0
    
    # Simulate a single 20-word sentence
    # Tokens range from 1 to 999
    sentence = torch.randint(1, VOCAB_SIZE, (1, 20))
    
    print("Original Sentence:")
    print(sentence[0].numpy())
    
    # Corrupt it!
    inputs, labels = create_mlm_data(sentence, VOCAB_SIZE, MASK_ID)
    
    print("\nCorrupted Input (What BERT sees):")
    print(inputs[0].numpy())
    
    print("\nTarget Labels (-100 means 'ignore this word'):")
    print(labels[0].numpy())
    
    print("\nNotice how the Loss Function will ONLY penalize BERT on the exact words that were chosen for corruption!")

if __name__ == "__main__":
    test_mlm()
```

### Key Takeaways from Code:
1. **The `-100` Label:** This is the most important concept in PyTorch classification. When `nn.CrossEntropyLoss` sees a target label of `-100`, it entirely skips that token. Because we only corrupted 15% of the sentence, we ONLY want to calculate loss on that 15%.
2. **Self-Supervised Learning:** Notice that we generated the `labels` tensor purely by cloning the input data. We created a highly complex mathematical training objective without a single human annotator!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Fine-Tuning HuggingFace BERT
You understand the math. Now use the industry standard library.
**Your Task:**
1. Run `pip install transformers` (mentally).
2. Write a script to load Google's pre-trained BERT: `from transformers import BertForSequenceClassification`.
3. Load it with `num_labels=2` (Positive/Negative).
4. Notice that HuggingFace automatically bolts an `nn.Linear` layer onto the `[CLS]` token for you!
5. Write a standard PyTorch training loop to pass text into this model and run `.backward()` using an Adam optimizer with an extremely small learning rate (e.g., `2e-5`). 

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"BERT revolutionized <abbr title="Natural Language Processing">NLP</abbr>, but it has severe limitations compared to modern LLMs. Explain the pre-train/fine-tune paradigm shift. Why was bidirectional context a breakthrough, but ultimately why did the industry abandon BERT in favor of few-shot prompting with GPT?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Paradigm Shift:** 
   - State that BERT shifted <abbr title="Natural Language Processing">NLP</abbr> from "training task-specific architectures from scratch" to "transfer learning from massive foundation models."
2. **The Bidirectional Breakthrough:**
   - Explain that by using Masked Language Modeling instead of autoregressive prediction, BERT could look both forwards and backwards, achieving unprecedented contextual understanding (making it state-of-the-art for NER, sentiment, and classification).
3. **The Limitation (Why GPT won):**
   - Conclude that fine-tuning BERT still requires hundreds of labeled examples and physically updating the model weights for *every single specific task*. You end up managing 50 different fine-tuned BERT models in production.
   - GPT (and modern LLMs) replaced this with **In-Context Learning (Few-Shot Prompting)**. You don't update weights at all. You just provide instructions in English in the prompt, allowing a single frozen model to perform infinite tasks simultaneously!

---
**Task for the end of the day:** Commit your code to Git. You have mastered the most famous Encoder model in history.

Tomorrow, in **Day 69**, we look at the model that won the <abbr title="Artificial Intelligence">AI</abbr> wars: **GPT**. We will learn about Autoregressive generation, the math behind decoding strategies, and the famous **Chinchilla Scaling Laws**!
