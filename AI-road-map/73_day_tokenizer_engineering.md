# Day 73: Tokenizer Engineering & Compression

Welcome to Day 73. A Transformer does not read English. It reads numbers.
The Tokenizer is the very first step of any Large Language Model. If you build a bad Tokenizer, your Trillion-parameter model will be fundamentally broken before training even begins.

Today, we learn how to compress the entirety of human language into a perfectly optimized array of $50,000$ integers.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Tokenization Dilemma
How do we convert words into numbers?
- **Word-Level:** If every unique word gets an ID, our dictionary needs to be $1,000,000$ words long. The Embedding Matrix ($1,000,000 \times 512$) will use 2 Gigabytes of VRAM just to store the dictionary! Worse, if someone typos *"Applesz"*, the AI crashes because the word is Out-Of-Vocabulary (OOV).
- **Character-Level:** If every letter gets an ID, our dictionary is only 26 letters! But the word *"Apple"* now takes 5 sequence steps to process. The $O(N^2)$ Attention mechanism will crash because sentences become 5x longer!

### 2. The Solution: Byte-Pair Encoding (BPE)
BPE is the golden middle ground. We build a dictionary of **Sub-words**.
1. We start with the base characters: `a, b, c...`
2. We scan the entire internet and count the most frequent adjacent pairs. 
3. We see that `t` and `h` appear next to each other millions of times. We merge them into a single new token: `th`.
4. We repeat this process exactly 50,000 times!
5. Eventually, common prefixes and suffixes (`ing`, `tion`, `est`) become single tokens. Entire common words (`The`, `Apple`) become single tokens. But a rare typo (`Applesz`) is safely broken down into `Apple` + `s` + `z`!

### 3. The Fertility Disparity (The Multilingual Flaw)
"Fertility" is the mathematical average of how many tokens it takes to represent one word.
Most companies (like OpenAI) built their BPE tokenizers by scanning English text.
- **English Fertility:** $\approx 1.2$ tokens per word.
- **Hindi Fertility:** $\approx 3.5$ tokens per word.

**Why this is a disaster:** If a Hindi speaker types a 1,000-word prompt, it becomes 3,500 tokens.
1. The AI hits its context window limit 3x faster.
2. The $O(N^2)$ attention mechanism runs 9x slower!
3. The user gets charged 3x more API credits!
Tokenization is not just linguistics; it is a critical engineering optimization.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a BPE Tokenizer entirely from scratch using the HuggingFace `tokenizers` library. We will train it on a tiny corpus and watch it mathematically learn to merge characters!

Create a file named `train_tokenizer.py`:

```python
from tokenizers import Tokenizer
from tokenizers.models import BPE
from tokenizers.trainers import BpeTrainer
from tokenizers.pre_tokenizers import Whitespace

def build_custom_tokenizer():
    print("--- TRAINING A BPE TOKENIZER FROM SCRATCH ---")
    
    # 1. Initialize an empty BPE model
    # [UNK] is the Unknown token (if a character literally doesn't exist)
    tokenizer = Tokenizer(BPE(unk_token="[UNK]"))
    
    # 2. Pre-tokenization (Split by spaces before BPE runs!)
    tokenizer.pre_tokenizer = Whitespace()
    
    # 3. Create a tiny corpus of text
    corpus = [
        "I am learning machine learning.",
        "Machine learning is the future of learning.",
        "Tokens are fundamental to transformers."
    ]
    
    # Write the corpus to a temporary file (Tokenizers require files)
    with open("temp_corpus.txt", "w") as f:
        for sentence in corpus:
            f.write(sentence + "\n")
            
    # 4. Initialize the Trainer
    # We set a tiny vocab size (e.g., 40) just so we can see the subwords!
    trainer = BpeTrainer(
        vocab_size=40, 
        special_tokens=["[UNK]", "[PAD]", "[BOS]", "[EOS]"]
    )
    
    # 5. TRAIN IT! (This mathematically counts frequencies and merges pairs)
    tokenizer.train(files=["temp_corpus.txt"], trainer=trainer)
    
    # 6. Test the Tokenizer
    test_sentence = "I am learning transformers."
    encoded = tokenizer.encode(test_sentence)
    
    print(f"\nOriginal String: '{test_sentence}'")
    print(f"Token IDs: {encoded.ids}")
    print(f"Tokens:    {encoded.tokens}")
    
    print("\nVocabulary Built:")
    vocab = tokenizer.get_vocab()
    # Sort the vocab by ID
    sorted_vocab = sorted(vocab.items(), key=lambda x: x[1])
    for word, token_id in sorted_vocab[-10:]:  # Print the 10 most recent merges!
        print(f"ID {token_id}: '{word}'")
        
    print("\nNotice how it learned the subword 'learning' as a single token,")
    print("because it appeared so many times in our tiny corpus!")

if __name__ == "__main__":
    build_custom_tokenizer()
```

### Key Takeaways from Code:
1. **Pre-tokenization:** We split the text by whitespace *before* running BPE. If we didn't do this, BPE might merge the end of one word with the beginning of the next word (e.g., merging the `e` and `i` in `the internet`), which ruins linguistic structure!
2. **Special Tokens:** `[PAD]` ensures batches are rectangular. `[BOS]` (Beginning of Sequence) and `[EOS]` (End of Sequence) are critical for telling the AI when to start and stop generating.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Code Tokenizer
If you train a Tokenizer on Wikipedia, it will merge letters into English words. But if you try to use that Tokenizer for an AI coding assistant, it will be incredibly inefficient.
**Your Task:**
1. Conceptually design a corpus of 100 Python scripts.
2. If you ran BPE on this, what merges would you expect to see?
3. It would merge `d`, `e`, `f` into the single token `def`.
4. It would merge 4 spaces `    ` into a single token, drastically reducing the sequence length of indented loops!
5. This is exactly how GitHub Copilot's tokenizer was designed!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are building a multilingual LLM for global deployment. English uses 1.2 tokens/word but Hindi uses 3.5 tokens/word. Explain exactly how this disparity affects serving cost, model quality, and user experience. How would you architect the Tokenizer training pipeline to fix this?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Compounding Cost:** 
   - State that LLM compute is $O(N^2)$ for Attention, and autoregressive generation requires $O(N)$ KV-Cache memory. A 3x increase in tokens means a 9x increase in compute and a 3x increase in VRAM, making Hindi generation massively slower and significantly more expensive to serve.
2. **The Quality Degradation:**
   - Explain that if a word is shattered into 4 meaningless sub-characters, the LLM struggles to learn the semantic meaning of the word compared to English where the entire word is processed instantly as a single vector.
3. **The Solution (Data Sampling):**
   - Conclude that BPE is a purely statistical algorithm. If your corpus is 95% English, BPE will allocate 95% of the 50,000 vocabulary slots to English subwords.
   - To fix this, you must **Up-sample** the Hindi text data *during the Tokenizer training phase*. By intentionally feeding the Tokenizer a balanced mix of 50% English and 50% Hindi, BPE will allocate thousands of vocab slots to full Hindi words, equalizing the fertility rate!

---
**Task for the end of the day:** Commit your code to Git.

Tomorrow, in **Day 74**, we answer the final question of Pre-training: Where do you find 1 Trillion words, and how do you delete the spam? We will learn about **MinHash Deduplication**!
