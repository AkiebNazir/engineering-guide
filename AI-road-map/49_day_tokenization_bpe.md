# Day 49: Subword Tokenization & Byte Pair Encoding (<abbr title="Byte Pair Encoding">BPE</abbr>)

Welcome to Day 49. Before you can pass human text into a Neural Network (like an <abbr title="Long Short-Term Memory">LSTM</abbr> or a Transformer), you must convert it into numbers. This process is called **Tokenization**.

If you do this incorrectly, your <abbr title="Artificial Intelligence">AI</abbr> will be fundamentally broken before the math even begins. Today, we learn the exact algorithm used by OpenAI to tokenize text for GPT-4.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Nightmare of Word-Level Tokenization
The naive approach is to use `string.split(' ')`. 
- **The Problem:** If your training data contains the word `"play"` and `"playing"`, the <abbr title="Artificial Intelligence">AI</abbr> treats them as two completely separate words. It doesn't realize they share the root "play". 
- **The Fatal Flaw (OOV):** If a user types a brand new word that wasn't in the training data (e.g., *"ChatGPT"*), the <abbr title="Artificial Intelligence">AI</abbr> crashes. This is the **Out Of Vocabulary (OOV)** error. To prevent this, old AIs used massive dictionaries of 200,000 words, which wasted massive amounts of <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr>.

### 2. The Nightmare of Character-Level Tokenization
If Words are too big, what if we tokenize by single Letters? 
The dictionary is only 26 letters! It will never hit an OOV error!
- **The Problem:** The letter "C" contains zero semantic meaning. It only means something when combined into "Cat". By forcing the <abbr title="Artificial Intelligence">AI</abbr> to read letter-by-letter, you force the <abbr title="Artificial Intelligence">AI</abbr> to learn how to spell before it can learn what words mean. 
- **The Fatal Flaw:** Sequence length. If a sentence has 10 words, it has 50 characters. Because LSTMs process sequences sequentially, processing 50 steps instead of 10 makes the <abbr title="Artificial Intelligence">AI</abbr> 5x slower to train!

### 3. The Goldilocks Solution: Subwords (<abbr title="Byte Pair Encoding">BPE</abbr>)
**Byte Pair Encoding (<abbr title="Byte Pair Encoding">BPE</abbr>)** is the perfect middle ground.
It starts at the character level. Then, it looks at the training data and finds the *most frequently occurring pair* of characters (e.g., "e" and "r"). It permanently merges them into a new token: `"er"`. 
It repeats this thousands of times. 
Eventually, it merges `"p"` + `"lay"` $\rightarrow$ `"play"`. 
**Why is this genius?** 
1. Common words (like `"The"`) become single tokens (Fast sequence length!).
2. Rare words (like `"Neuroscience"`) get broken down into logical subwords: `["Neuro", "science"]`. 
3. If a user types a brand new word, <abbr title="Byte Pair Encoding">BPE</abbr> just breaks it down into individual letters. It **never** hits an OOV error!

### 4. SentencePiece (The Google Solution)
Standard <abbr title="Byte Pair Encoding">BPE</abbr> uses spaces to split words *before* merging. This means it completely fails on languages that don't use spaces (like Chinese or Japanese). 
**SentencePiece** fixes this by treating the space character as just another normal letter (often represented as an underscore `_`). This allows the <abbr title="Artificial Intelligence">AI</abbr> to natively learn tokenization across all human languages!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build the <abbr title="Byte Pair Encoding">BPE</abbr> training algorithm entirely from scratch in pure Python. You will see exactly how the <abbr title="Artificial Intelligence">AI</abbr> learns to combine letters into subwords based on pure frequency!

Create a file named `bpe_tokenizer.py`:

```python
import collections

def get_stats(vocab):
    """
    Finds every adjacent pair of symbols in the vocabulary
    and counts how many times they occur.
    """
    pairs = collections.defaultdict(int)
    for word, freq in vocab.items():
        symbols = word.split()
        # Loop through the symbols to find pairs
        for i in range(len(symbols)-1):
            # Create a tuple of the pair: e.g., ('l', 'o')
            pairs[symbols[i], symbols[i+1]] += freq
    return pairs

def merge_vocab(best_pair, vocab_in):
    """
    Takes the most frequent pair (e.g., 'e' and 'r') and 
    physically merges them into 'er' across the entire vocabulary!
    """
    vocab_out = {}
    
    # We create a string representation of the pair to search for
    # e.g., "e r" -> "er"
    pair_str = ' '.join(best_pair)
    replacement = ''.join(best_pair)
    
    for word, freq in vocab_in.items():
        # Replace the separated pair with the merged pair
        # "l o w" -> "lo w"
        new_word = word.replace(pair_str, replacement)
        vocab_out[new_word] = freq
        
    return vocab_out

def train_bpe():
    print("--- TRAINING BYTE PAIR ENCODING (BPE) ---")
    
    # 1. Simulate a tiny training corpus!
    # Notice we start by splitting every word into individual characters separated by spaces.
    # The </w> tag tells the AI where the word officially ends.
    vocab = {
        'l o w </w>': 5,
        'l o w e r </w>': 2,
        'n e w e s t </w>': 6,
        'w i d e s t </w>': 3
    }
    
    print("Starting Vocabulary (Character Level):")
    for k, v in vocab.items(): print(f"{v}x : {k}")
    print("-" * 30)
    
    # 2. Run BPE for 5 Merges!
    num_merges = 5
    for i in range(num_merges):
        # Find the most frequent pair of symbols
        pairs = get_stats(vocab)
        
        if not pairs:
            break
            
        # Get the pair with the absolute highest count
        best_pair = max(pairs, key=pairs.get)
        print(f"Merge #{i+1}: The most frequent pair is {best_pair} (Occurred {pairs[best_pair]} times)")
        
        # Merge them!
        vocab = merge_vocab(best_pair, vocab)
        
    print("-" * 30)
    print("Final Vocabulary (Subword Level):")
    for k, v in vocab.items(): print(f"{v}x : {k}")
    
    print("\nNotice how 'e' and 's' merged into 'es'. Then 'es' and 't' merged into 'est'!")
    print("The AI has learned the suffix '-est' entirely on its own!")

if __name__ == "__main__":
    train_bpe()
```

### Key Takeaways from Code:
1. **The `</w>` Token:** Why do we append `</w>` to the end of every word before training? Because the "er" at the end of "lower" is a suffix, but the "er" in the middle of "error" is just a sound. By adding `</w>`, the <abbr title="Artificial Intelligence">AI</abbr> learns that `er</w>` is a specific mathematical token representing a suffix!
2. **Frequency Driven:** Look at the output of the code. The <abbr title="Artificial Intelligence">AI</abbr> blindly merged "e" and "s", and then "es" and "t", creating the subword `est`. It literally learned English grammar suffixes without ever being taught English grammar.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Encoding New Text
You trained the <abbr title="Byte Pair Encoding">BPE</abbr> rules. Now you must use them.
**Your Task:**
1. You have a list of ordered merge rules you learned during training: `[('e', 's'), ('es', 't')]`.
2. A user types a brand new OOV word: "highest".
3. Write a Python function `encode(word, merge_rules)`.
4. It must split the word into letters: `['h', 'i', 'g', 'h', 'e', 's', 't']`.
5. It must iterate through your `merge_rules` in the *exact order* they were learned, applying the merges to the array.
6. The final output array should be: `['h', 'i', 'g', 'h', 'est']`. 

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"The Tokenizer is arguably the most underrated, yet critical component of a Large Language Model. Explain exactly how the quality and dictionary size of a <abbr title="Byte Pair Encoding">BPE</abbr> tokenizer affects (1) Model Performance, (2) Multilingual Capability, and (3) Production Inference Cost."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Model Performance (Context Window):** 
   - Explain that LLMs have a strict maximum context window (e.g., 4000 tokens). If your tokenizer is inefficient and breaks the word "Apple" into 5 separate letters, you burn through your context window 5x faster, crippling the model's ability to read long documents.
2. **Multilingual Capability (Vocabulary Allocation):**
   - State that if the 50,000-word <abbr title="Byte Pair Encoding">BPE</abbr> dictionary was trained exclusively on English Wikipedia, it will not have any merged subwords for Hindi or Arabic. 
   - When a user types Hindi, the tokenizer will violently shred the Hindi text into individual byte-characters. The model will fail to understand the language because it has no semantic subwords to anchor onto.
3. **Inference Cost (The FLOPs):**
   - Conclude that <abbr title="Application Programming Interface">API</abbr> costs are charged *per token*. Furthermore, the Transformer's Attention mechanism is $O(N^2)$ based on Sequence Length. If a bad tokenizer outputs 100 tokens for a sentence instead of 50 tokens, the mathematical compute required to process that sentence increases by 4x, drastically increasing cloud hosting costs!

---
**Task for the end of the day:** Commit your code to Git. You have mastered how <abbr title="Artificial Intelligence">AI</abbr> reads text.

Tomorrow, in **Day 50**, we tackle **Sequence Labeling**. We will build the architecture required to read a document and highlight all the Names, Locations, and Dates using **Conditional Random Fields (CRF)!**
