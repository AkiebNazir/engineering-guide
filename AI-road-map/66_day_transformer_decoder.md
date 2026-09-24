# Day 66: The Transformer Decoder (GPT architecture)

Welcome to Day 66. Yesterday, we built BERT (The Transformer Encoder). 
BERT reads sentences bidirectionally. It is an absolute genius at text classification. 
But if you ask BERT to write a poem, it crashes. You cannot write a poem bidirectionally. You must write it one word at a time, from left to right.

Today, we build the architecture that powers **ChatGPT, Claude, and LLaMA**: The **Transformer Decoder**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Autoregressive Generation
GPT (Generative Pre-trained Transformer) is a Decoder-only architecture. 
It is **Autoregressive**. This means its output today becomes its input tomorrow. 
1. Input: `"The"` $\rightarrow$ Output: `"dog"`
2. Input: `"The dog"` $\rightarrow$ Output: `"barked"`
3. Input: `"The dog barked"` $\rightarrow$ Output: `"loudly"`

### 2. The Cheat Code Problem
During training, we want to train fast. We don't want to run the model sequentially 1,000 times to train it on a 1,000-word essay. 
We want to feed the entire 1,000 words into the GPU simultaneously and predict all 1,000 next words at the exact same time!

**The Fatal Flaw:** The Transformer Self-Attention matrix processes everything simultaneously. If you feed it the entire sentence `"The dog barked loudly"`, and ask it to predict the word after `"The"`, the Attention mechanism will just *look at the next word* in the input vector and cheat! It will achieve 100% accuracy with zero intelligence. 

### 3. The Fix: Causal Masking
We must physically blind the AI. We create a **Causal Mask**.
It is a 2D matrix where the top-right triangle is filled with Negative Infinity ($-\infty$), and the bottom-left is filled with Zeros.
We literally add this Mask to the $Q \cdot K^T$ Attention grid *before* the Softmax!

- **Row 1 (Word 1):** `[0, -inf, -inf, -inf]`. Word 1 can only look at itself.
- **Row 2 (Word 2):** `[0, 0, -inf, -inf]`. Word 2 can look at Word 1 and itself.
- **Row 4 (Word 4):** `[0, 0, 0, 0]`. Word 4 can look at the entire past!

When the Softmax encounters $-\infty$, it turns it into exactly $0.0\%$. 
We have mathematically prevented the AI from seeing into the future!

### 4. Encoder vs Decoder
- **Encoder (BERT):** Uses standard Self-Attention. Perfect bidirectional context.
- **Decoder (GPT):** Uses **Masked** Self-Attention. Strictly one-way causal context.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build the Causal Mask and the Transformer Decoder in PyTorch. You will see exactly how we mathematically blind the AI during parallel training!

Create a file named `transformer_decoder.py`:

```python
import torch
import torch.nn as nn
import math

class MaskedSelfAttention(nn.Module):
    """
    Self-Attention with a Causal Mask to prevent cheating!
    """
    def __init__(self, embed_dim=512):
        super().__init__()
        self.embed_dim = embed_dim
        
        self.W_q = nn.Linear(embed_dim, embed_dim, bias=False)
        self.W_k = nn.Linear(embed_dim, embed_dim, bias=False)
        self.W_v = nn.Linear(embed_dim, embed_dim, bias=False)

    def forward(self, x):
        seq_len = x.size(1)
        
        Q = self.W_q(x)
        K = self.W_k(x)
        V = self.W_v(x)
        
        # 1. Calculate Raw Scores
        scores = torch.bmm(Q, K.transpose(1, 2)) / math.sqrt(self.embed_dim)
        
        # 2. CREATE THE CAUSAL MASK!
        # torch.tril creates a lower-triangular matrix of 1s (0s in the top right)
        mask = torch.tril(torch.ones(seq_len, seq_len)).to(x.device)
        
        # 3. APPLY THE MASK!
        # Wherever the mask is 0 (the future), we overwrite the score with -Infinity!
        # We use -1e9 instead of literal -inf for numerical stability.
        scores = scores.masked_fill(mask == 0, float('-1e9'))
        
        # 4. Softmax (The -1e9s become exactly 0.0!)
        attention_weights = torch.softmax(scores, dim=-1)
        
        # 5. Multiply by Values
        output = torch.bmm(attention_weights, V)
        
        return output, attention_weights

class TransformerDecoderLayer(nn.Module):
    """
    A single block of the GPT architecture!
    """
    def __init__(self, embed_dim=512):
        super().__init__()
        self.masked_mha = MaskedSelfAttention(embed_dim)
        
        # We'll use a simple FFN for this example
        self.ffn = nn.Sequential(
            nn.Linear(embed_dim, 2048),
            nn.ReLU(),
            nn.Linear(2048, embed_dim)
        )
        
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)

    def forward(self, x):
        # MASKED Attention
        x_norm = self.norm1(x)
        att_out, weights = self.masked_mha(x_norm)
        x = x + att_out
        
        # FFN
        x_norm2 = self.norm2(x)
        ffn_out = self.ffn(x_norm2)
        x = x + ffn_out
        
        return x, weights

def test_decoder():
    print("--- RUNNING TRANSFORMER DECODER (GPT) ---")
    
    BATCH_SIZE = 1
    SEQ_LEN = 4 # e.g., "The", "dog", "barked", "loudly"
    EMBED_DIM = 512
    
    sentence = torch.randn(BATCH_SIZE, SEQ_LEN, EMBED_DIM)
    
    decoder = TransformerDecoderLayer(embed_dim=EMBED_DIM)
    output, weights = decoder(sentence)
    
    print("\nLet's look at the Causal Mask (Attention Weights Grid):")
    # Grab the 4x4 matrix, round to 2 decimal places
    grid = torch.round(weights[0] * 100) / 100
    
    print(grid.detach().numpy())
    
    print("\nLook at the Upper Right Triangle! It is perfectly filled with 0.0!")
    print("Word 1 (Row 1) pays 100% attention to itself.")
    print("Word 2 (Row 2) pays attention to Word 1 and Word 2.")
    print("Word 3 CANNOT look at Word 4! The future is completely hidden!")

if __name__ == "__main__":
    test_decoder()
```

### Key Takeaways from Code:
1. **`torch.tril`:** This creates the triangle mask. If you print the `mask` before the `masked_fill`, it looks like this:
```
[1, 0, 0, 0]
[1, 1, 0, 0]
[1, 1, 1, 0]
[1, 1, 1, 1]
```
2. **`masked_fill`:** This is computationally brilliant. It finds every `0` in the mask and instantly replaces the corresponding Attention Score with `-1e9`. When you run Softmax, $e^{-1000000000} = 0.0$. The AI cannot cheat!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Autoregressive Inference Loop
You have built the training mechanism. Now build the Generation loop.
**Your Task:**
1. Start with a prompt: `[45]` (The token ID for "The").
2. Pass it through the Decoder. Grab the final output vector. 
3. Pass it through an `nn.Linear` classifier to predict the next word over the 50,000 word vocabulary.
4. Assume the AI predicts `[89]` ("dog").
5. Append `[89]` to the input. The new input is `[45, 89]`.
6. Run the entire thing again! Loop this 100 times until the AI generates the special `<EOS>` (End of Sentence) token!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Derive the FLOPs (Floating Point Operations) savings of using a KV-cache during autoregressive generation. For a GPT model with $L$ layers, $D$ model dimension, and current sequence length $N$, what is the exact memory cost to store the cache?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The $O(N^2)$ Recomputation Flaw:** 
   - State that without a KV-Cache, predicting word 101 requires passing all 100 previous words through the massive $W_q, W_k, W_v$ linear layers again, wasting massive amounts of compute.
2. **The KV-Cache FLOPs Saving:**
   - Explain that with a KV-Cache, the Keys and Values for words 1-100 are saved in VRAM. 
   - When word 101 arrives, you ONLY calculate $Q, K, V$ for the single new word. You append the new $K$ and $V$ to the cache, and calculate Attention using the single new $Q$ against the cached $K$. This reduces the compute complexity per step from $O(N^2)$ to $O(N)$!
3. **The Memory Cost Formula:**
   - Conclude with the memory formula: $2 \text{ (K and V)} \times N \text{ (Seq Len)} \times L \text{ (Layers)} \times D \text{ (Dimension)} \times 2 \text{ (FP16 Bytes)}$. 
   - Note that as sequence length $N$ grows, the KV-Cache memory grows linearly, eventually becoming the absolute bottleneck of LLM deployment.

---
**Task for the end of the day:** Commit your code to Git. 

You have just built the underlying engine of ChatGPT completely from scratch. 
In the next chunk, we will expand on Transformers. We will learn how to fine-tune BERT, how to scale GPT to 175 Billion parameters, and how to build Vision Transformers (ViT)!
