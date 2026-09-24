# Day 91: LLM Architecture Deep Dive (LLaMA, Mistral, Gemma)

Welcome to Day 91, and welcome to **Phase 4: LLMs — Training, Fine-Tuning & Alignment**.

We are leaving the Application Layer (RAG, Agents, Prompting) behind. We are now entering the Core AI Engineering layer. Over the next 30 days, you will learn how to build, train, and align massive AI models.

Today, we break open the black box. The "Standard" Transformer from 2017 is dead. We will look at the exact architectural optimizations used inside LLaMA 3, Mistral, and Google's Gemma.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Modern LLM Architecture
If you open the source code for Meta's LLaMA 3, it is still a Decoder-Only Transformer, but with heavy mathematical modifications:
- **RMSNorm:** Standard LayerNorm calculates both the Mean and Variance of the vectors. LLaMA uses Root Mean Square Normalization (RMSNorm). It skips the Mean calculation entirely! This saves $10\%$ of compute time per layer without losing accuracy.
- **SwiGLU FFN:** The standard Transformer uses a ReLU activation in the Feed-Forward Network. LLaMA uses SwiGLU (Swish-Gated Linear Unit). It adds an extra matrix multiplication "Gate" that mathematically controls how much information flows through the network, significantly improving the model's reasoning capabilities.
- **RoPE (Rotary Position Embeddings):** Instead of adding absolute positions ($0, 1, 2$) to the words, RoPE mathematically *rotates* the word vectors in high-dimensional space. The angle of rotation represents the relative distance between two words.

### 2. Mistral & Sliding Window Attention
Mistral 7B shocked the world by beating LLaMA 13B. How? **Sliding Window Attention (SWA)**.
In standard attention, if the sequence is 8,000 words, Word 8000 looks back at all 7,999 previous words (Quadratic $O(N^2)$).
Mistral enforces a strict "Window" of 4,096. Word 8000 is only allowed to look back at words 3904 through 8000! 
Because the attention is restricted to a fixed block size, the compute time becomes Linear $O(N)$, allowing Mistral to process theoretical infinite context much faster!

### 3. The Parameter Math
Where do the 70 Billion parameters actually live?
The formula for a Transformer's parameter count is roughly: 
$P \approx 12 \cdot L \cdot d^2$ 
*(where $L$ = number of layers, $d$ = embedding dimension).*

For a massive model:
- The **Embedding Table** (Vocabulary Size $\times$ Dimension) is actually a tiny fraction of the total parameters.
- The **Attention Matrices** ($W_Q, W_K, W_V, W_O$) hold roughly $30\%$ of the weights.
- The **Feed-Forward Networks** (SwiGLU) hold the massive majority ($>60\%$) of the 70 Billion parameters! The FFN is where the factual knowledge of the LLM is stored!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's write a script to mathematically calculate exactly where the parameters live in a LLaMA-like architecture. We will build a mock layer and run a recursive parameter counter!

Create a file named `llm_architecture.py`:

```python
import torch
import torch.nn as nn

class RMSNorm(nn.Module):
    """LLaMA's faster normalization"""
    def __init__(self, dim):
        super().__init__()
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        # We only calculate the Root Mean Square, ignoring the Mean!
        variance = x.pow(2).mean(-1, keepdim=True)
        x_norm = x * torch.rsqrt(variance + 1e-6)
        return self.weight * x_norm

class MockLLaMALayer(nn.Module):
    """One single layer of a LLaMA model"""
    def __init__(self, dim=4096, n_heads=32):
        super().__init__()
        self.dim = dim
        self.head_dim = dim // n_heads
        
        # 1. Grouped Query Attention (GQA) Matrices
        # Q is full size. K and V might be smaller in real GQA, but we assume full here for simplicity.
        self.wq = nn.Linear(dim, dim, bias=False)
        self.wk = nn.Linear(dim, dim, bias=False)
        self.wv = nn.Linear(dim, dim, bias=False)
        self.wo = nn.Linear(dim, dim, bias=False)
        
        # 2. SwiGLU Feed Forward Network
        # LLaMA's FFN hidden dimension is roughly (8/3) * dim
        hidden_dim = int(2 * (4 * dim) / 3) 
        
        self.w1 = nn.Linear(dim, hidden_dim, bias=False) # Gate
        self.w2 = nn.Linear(hidden_dim, dim, bias=False) # Down projection
        self.w3 = nn.Linear(dim, hidden_dim, bias=False) # Up projection
        
        # 3. Norms
        self.attention_norm = RMSNorm(dim)
        self.ffn_norm = RMSNorm(dim)

def count_parameters(model):
    """Recursively counts and categorizes parameters"""
    total = 0
    attention_params = 0
    ffn_params = 0
    
    for name, param in model.named_parameters():
        num_params = param.numel()
        total += num_params
        
        if 'w1' in name or 'w2' in name or 'w3' in name:
            ffn_params += num_params
        elif 'wq' in name or 'wk' in name or 'wv' in name or 'wo' in name:
            attention_params += num_params
            
    return total, attention_params, ffn_params

def test_architecture():
    print("--- LLaMA ARCHITECTURE PARAMETER BREAKDOWN ---")
    
    # Simulate LLaMA 7B Dimensions (approx 32 layers, dim 4096)
    DIM = 4096
    
    # We instantiate JUST ONE LAYER
    layer = MockLLaMALayer(dim=DIM)
    
    total_layer, att_layer, ffn_layer = count_parameters(layer)
    
    print("\n--- ONE SINGLE LAYER ---")
    print(f"Attention Params:  {att_layer:,} ({att_layer/total_layer*100:.1f}%)")
    print(f"FFN Params:        {ffn_layer:,} ({ffn_layer/total_layer*100:.1f}%)")
    print(f"Total for 1 Layer: {total_layer:,}")
    
    # Multiply by 32 layers
    NUM_LAYERS = 32
    print(f"\n--- FULL MODEL ({NUM_LAYERS} LAYERS) ---")
    print(f"Total Transformer Params: {total_layer * NUM_LAYERS:,}")
    
    # Add the Vocabulary Embedding Table (Size 32,000 * 4096)
    vocab_params = 32000 * 4096
    print(f"Vocabulary Embedding Params: {vocab_params:,}")
    
    final_total = (total_layer * NUM_LAYERS) + vocab_params
    print(f"\nTOTAL MODEL SIZE: ~{final_total / 1_000_000_000:.1f} Billion Parameters!")
    print("Notice how the FFN dominates the parameter count!")

if __name__ == "__main__":
    test_architecture()
```

### Key Takeaways from Code:
1. **Bias=False:** In standard PyTorch, `nn.Linear` includes a Bias term. Modern LLMs like LLaMA explicitly disable the Bias (`bias=False`). Disabling the bias makes the math slightly faster, simplifies the backward pass, and empirical studies show it does not reduce the model's intelligence!
2. **The FFN Dominance:** The Attention layer determines *how* to route the information. But the FFN (which contains $60\%+$ of the weights) is where the actual facts (e.g., "Paris is the capital of France") are mathematically stored.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Sliding Window Mask
Mistral restricts attention to the last 4,096 tokens.
**Your Task:**
1. In a standard Transformer, we use a Causal Mask (a lower-triangular matrix of $1$s and $-\infty$) to prevent the model from looking into the future.
2. Conceptually write a Python script to generate a **Band Mask** (Sliding Window Mask).
3. The mask should be a matrix of $-\infty$, but with a diagonal "Band" of $0$s.
4. The band ensures that Token $t$ can only look at tokens from $t-4096$ to $t$. Anything before $t-4096$ is set to $-\infty$!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You have a fixed compute budget of 200 Billion FLOPs for training. Using the Chinchilla Scaling Laws, design the model architecture (parameter count vs token count) and justify your choices."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Chinchilla Law:** 
   - State DeepMind's Chinchilla Law: The optimal ratio of Model Size to Training Tokens is roughly **1 : 20**. 
   - For every 1 parameter in the model, you must train it on 20 tokens of data.
2. **The Math Breakdown:**
   - Explain that training compute is roughly $C \approx 6 \cdot P \cdot T$ (where $P$ is parameters and $T$ is tokens).
   - If you have a fixed $C$, and you know $T = 20 \cdot P$, you can solve for $P$: 
   $C \approx 6 \cdot P \cdot (20 \cdot P) \rightarrow C \approx 120 \cdot P^2$.
3. **The LLaMA 3 Exception (Over-training):**
   - Note that LLaMA 3 explicitly *violates* Chinchilla! LLaMA 3 8B was trained on 15 Trillion tokens (a ratio of 1 : 1800!). 
   - Explain why: Chinchilla optimizes for *training compute*. But Meta wanted to optimize for *inference latency*. By training a tiny 8B model for way too long, they created a model that is incredibly smart but incredibly cheap to run in production!

---
**Task for the end of the day:** Commit your code to Git. 

You know the architecture. But an architecture is useless without Data. LLaMA 3 was trained on 15 Trillion tokens. Where do you get 15 Trillion words? 

Tomorrow, in **Day 92**, we build the massive Petabyte-scale **Pre-Training Data Pipeline** (Common Crawl, MinHash Deduplication, and Toxicity Filtering)!
