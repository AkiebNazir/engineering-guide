# Day 62: Multi-Head Attention & GQA

Welcome to Day 62. Yesterday, we learned how Self-Attention allows every word in a sentence to mathematically bond with every other word using a single Query, Key, and Value matrix.

But human language is complex. The word *"Apple"* relates to *"Ate"* grammatically (Noun-Verb relationship). But *"Apple"* also relates to *"Red"* visually (Object-Color relationship). 
A single Attention matrix cannot capture grammar, emotion, logic, and visual traits all at once. The math gets muddled. 

The solution? **Multi-Head Attention (MHA)**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Splitting the Dimension
Assume our word embeddings are $512$-dimensional.
Instead of doing one massive attention calculation on all 512 numbers, we mathematically slice the 512 numbers into **8 independent "Heads"** of 64 dimensions each.
- **Head 1 (64D):** Learns to exclusively look for Grammatical structure.
- **Head 2 (64D):** Learns to exclusively look for Rhyming patterns.
- **Head 3 (64D):** Learns to exclusively look for Emotional sentiment.

Each Head gets its own miniature $W_q, W_k, W_v$ matrices. They all run the exact same `Softmax(Q*K/sqrt(d))` formula, completely parallel and independent of each other!

### 2. The Concatenation ($W^O$)
After the 8 heads finish their calculations, they each output a new 64D vector.
We simply concatenate them back together side-by-side ($64 \times 8 = 512$). 
Finally, we pass this combined 512D vector through a final Linear layer ($W^O$) to mathematically mix the insights from the 8 heads together.

### 3. The Generative Bottleneck: The KV-Cache
When ChatGPT generates a 1000-word essay, it does so autoregressively (one word at a time).
To predict word 1001, it must mathematically look at the Keys and Values of all previous 1000 words. 
Re-calculating the Keys and Values for 1000 words on every single step is impossibly slow. So, we save them in VRAM. This is called the **KV-Cache**.
**The Problem:** Storing 8 separate Keys and Values for 1000 words for a 70-Billion parameter model requires *massive* amounts of VRAM. You will run out of memory instantly.

### 4. Grouped Query Attention (GQA)
To fix the VRAM crisis, researchers invented optimizations for the KV-Cache.
- **MQA (Multi-Query Attention):** We keep the 8 Query heads, but we force them to share a SINGLE Key head and a SINGLE Value head! This drops memory usage by 87%, but slightly hurts AI quality.
- **GQA (Grouped Query Attention):** The golden middle ground used in **LLaMA 2 & 3**. We have 8 Query heads, but we group them into pairs. Heads 1 & 2 share Key/Value A. Heads 3 & 4 share Key/Value B. 
GQA drops memory usage by 50% with almost zero degradation in intelligence!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build standard Multi-Head Attention in PyTorch. 
We will NOT use 8 separate `for` loops. That is too slow. We will use PyTorch's `view()` and `transpose()` to cleanly slice the dimension into 8 heads and calculate them all simultaneously on the GPU!

Create a file named `multi_head_attention.py`:

```python
import torch
import torch.nn as nn
import math

class MultiHeadAttention(nn.Module):
    """
    Standard Multi-Head Attention from 'Attention Is All You Need'
    """
    def __init__(self, embed_dim=512, num_heads=8):
        super().__init__()
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        
        # Ensure the math perfectly divides
        assert embed_dim % num_heads == 0, "embed_dim must be divisible by num_heads!"
        self.head_dim = embed_dim // num_heads # 512 / 8 = 64
        
        # We define one massive Linear layer for all heads combined!
        # This is mathematically identical to 8 small layers, but much faster on GPU.
        self.W_q = nn.Linear(embed_dim, embed_dim, bias=False)
        self.W_k = nn.Linear(embed_dim, embed_dim, bias=False)
        self.W_v = nn.Linear(embed_dim, embed_dim, bias=False)
        
        # The final mixing layer
        self.W_o = nn.Linear(embed_dim, embed_dim, bias=False)

    def forward(self, x):
        batch_size, seq_len, _ = x.shape
        
        # 1. Project into Q, K, V
        # Shape: [Batch, Seq_Len, 512]
        Q = self.W_q(x)
        K = self.W_k(x)
        V = self.W_v(x)
        
        # 2. THE SLICE! (Splitting into 8 Heads)
        # We reshape from [Batch, Seq_Len, 512] to [Batch, Seq_Len, 8, 64]
        Q = Q.view(batch_size, seq_len, self.num_heads, self.head_dim)
        K = K.view(batch_size, seq_len, self.num_heads, self.head_dim)
        V = V.view(batch_size, seq_len, self.num_heads, self.head_dim)
        
        # 3. THE TRANSPOSE! (Preparing for parallel multiplication)
        # We swap the dimensions to [Batch, 8, Seq_Len, 64]
        # Now, PyTorch treats the "8 Heads" as if they were just extra items in the batch!
        Q = Q.transpose(1, 2)
        K = K.transpose(1, 2)
        V = V.transpose(1, 2)
        
        # 4. Scaled Dot-Product Attention (Calculated for all 8 heads simultaneously!)
        # [Batch, 8, Seq_Len, 64] * [Batch, 8, 64, Seq_Len] -> [Batch, 8, Seq_Len, Seq_Len]
        scores = torch.matmul(Q, K.transpose(-2, -1)) / math.sqrt(self.head_dim)
        weights = torch.softmax(scores, dim=-1)
        
        # Multiply by Values: [Batch, 8, Seq_Len, Seq_Len] * [Batch, 8, Seq_Len, 64]
        # Result: [Batch, 8, Seq_Len, 64]
        head_outputs = torch.matmul(weights, V)
        
        # 5. THE RE-ASSEMBLY!
        # Swap back to [Batch, Seq_Len, 8, 64]
        head_outputs = head_outputs.transpose(1, 2).contiguous()
        
        # Crush the 8 heads back into the single 512 dimension!
        # Shape: [Batch, Seq_Len, 512]
        concat_output = head_outputs.view(batch_size, seq_len, self.embed_dim)
        
        # 6. Final Mixing
        final_output = self.W_o(concat_output)
        
        return final_output

def test_mha():
    print("--- RUNNING MULTI-HEAD ATTENTION ---")
    
    BATCH_SIZE = 2
    SEQ_LEN = 10
    EMBED_DIM = 512
    NUM_HEADS = 8
    
    # Simulate a sentence
    sentence = torch.randn(BATCH_SIZE, SEQ_LEN, EMBED_DIM)
    
    model = MultiHeadAttention(embed_dim=EMBED_DIM, num_heads=NUM_HEADS)
    output = model(sentence)
    
    print(f"Input Shape:  {sentence.shape}")
    print(f"Output Shape: {output.shape}")
    print(f"The 512D vector was sliced into {NUM_HEADS} independent parallel brains, and reassembled flawlessly!")

if __name__ == "__main__":
    test_mha()
```

### Key Takeaways from Code:
1. **The `view` and `transpose` trick:** This is the most famous code pattern in all of Deep Learning. By transposing the `num_heads` dimension next to the `batch` dimension, `torch.matmul` naturally treats the 8 heads completely independently. No `for` loops required!
2. **`.contiguous()`:** When you use `transpose` in PyTorch, the memory on the GPU physically stays in the old order, it just changes the metadata. Before you can use `.view()` to crush it back down, you MUST call `.contiguous()` to physically realign the memory bytes in the VRAM!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Implementing Grouped Query Attention (GQA)
Modify the code to support LLaMA's GQA!
**Your Task:**
1. In `__init__`, instead of `num_heads=8`, accept `num_q_heads=8` and `num_kv_heads=2`.
2. The `W_k` and `W_v` linear layers should only output `num_kv_heads * head_dim`!
3. During the `forward` pass, `Q` will have 8 heads. `K` will only have 2 heads.
4. You cannot multiply an 8-head tensor by a 2-head tensor. You must use `torch.repeat_interleave` to mathematically duplicate the 2 Key heads so they "stretch" to match the 8 Query heads! 
5. Because you only saved 2 KV heads, your KV-Cache size is reduced by 75%!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"A 70-Billion parameter LLM is deployed to production. Using standard MHA, calculate the exact VRAM cost of the KV-Cache for a single request with a sequence length of 4096. How much VRAM does GQA save?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The KV-Cache Formula:** 
   - State the memory formula for KV-Cache: $2 \times (\text{Seq\_Len}) \times (\text{Num\_Layers}) \times (\text{Hidden\_Dim}) \times (\text{Bytes\_per\_param})$.
   - The $2$ is because we must store both Keys AND Values.
2. **The Calculation (Assuming standard LLaMA-70B specs):**
   - Hidden Dim = 8192. Layers = 80. Seq_Len = 4096. Using FP16 (2 bytes per param).
   - $2 \times 4096 \times 80 \times 8192 \times 2 = 10.7$ Gigabytes of VRAM *just for the cache of one single user!*
3. **The GQA Savings:**
   - Explain that LLaMA-70B uses 64 Query heads, but only 8 KV heads.
   - This is an exactly $8\times$ reduction in the KV dimension size.
   - Conclude that GQA reduces the KV-Cache from 10.7 GB down to just **1.3 GB per user**, allowing the server to handle 8x more concurrent customers on the exact same GPU hardware!

---
**Task for the end of the day:** Commit your code to Git. You have mastered the most complex matrix transformations in AI.

Tomorrow, in **Day 63**, we solve a fatal physical flaw in the Transformer. Attention matrices don't know the difference between the 1st word and the 100th word. We will fix this using **Positional Encodings and RoPE!**
