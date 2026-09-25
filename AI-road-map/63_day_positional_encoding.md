# Day 63: Positional Encoding & RoPE

Welcome to Day 63. The Transformer is blazing fast because it processes all words simultaneously. 
But this introduces a fatal physical flaw. The Attention matrix is mathematically blind to word order. 

To a Transformer, the sentence *"The dog chased the cat"* and *"The cat chased the dog"* result in the exact same mathematical computations. 
Today, we fix this. We must inject a sense of Time and Position into the mathematics.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Original Fix: Sinusoidal Positional Encoding
In the 2017 *"Attention Is All You Need"* paper, the researchers solved this by generating a unique mathematical fingerprint for every position in the sentence.
They used Sine and Cosine waves of varying frequencies. 
- Position 1 gets a specific mix of sine waves.
- Position 2 gets a slightly different mix.
They literally take this array of Sine/Cosine waves and mathematically **ADD** it to the original Word Embedding before it enters the Transformer!

**Why Sines and Cosines?**
Because of trigonometry. The math of Sine waves allows the <abbr title="Artificial Intelligence">AI</abbr> to calculate *relative distances* easily. Even if the <abbr title="Artificial Intelligence">AI</abbr> has never seen a 1,000-word sentence before, the Sine waves allow it to deduce: *"Word 500 is exactly 10 spaces away from Word 490"*. 

### 2. The Modern Upgrade: Rotary Position Embeddings (RoPE)
Sinusoidal Positional Encoding (Adding waves) is considered outdated today.
LLaMA, PaLM, and modern LLMs use **RoPE**. 

Instead of adding numbers, RoPE uses a **Rotation Matrix** from linear algebra. 
Imagine the word *"Apple"* is a vector pointing North. 
- If *"Apple"* is the 1st word in the sentence, RoPE rotates it 1 degree East.
- If *"Apple"* is the 100th word in the sentence, RoPE rotates it 100 degrees East.

We apply this rotation *directly to the Queries and Keys* inside the Attention mechanism! 
Because dot-products mathematically measure the angle between vectors, Rotating the Queries and Keys perfectly preserves the *relative distance* between words!

### 3. ALiBi (Attention with Linear Biases)
Another alternative to RoPE is ALiBi. ALiBi doesn't touch the word embeddings at all.
Instead, it waits until the Attention Grid (The Q*K scores) is calculated. Then, it mathematically subtracts a massive penalty from the score of words that are far away from each other! It physically forces words to pay more attention to their immediate neighbors.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's implement the classic Sinusoidal Positional Encoding in PyTorch. We will generate the 2D grid of sine and cosine waves from scratch.

Create a file named `positional_encoding.py`:

```python
import torch
import torch.nn as nn
import math
import matplotlib.pyplot as plt

class PositionalEncoding(nn.Module):
    """
    Injects order into the Transformer by adding Sine and Cosine waves!
    """
    def __init__(self, embed_dim, max_seq_len=5000):
        super().__init__()
        
        # Create a matrix of zeros: [Max_Seq_Len, Embed_Dim]
        # E.g., [5000, 512]
        pe = torch.zeros(max_seq_len, embed_dim)
        
        # Create a column vector of positions: [0, 1, 2, ..., 4999]
        position = torch.arange(0, max_seq_len, dtype=torch.float).unsqueeze(1)
        
        # The Divisor Term (The denominator of the formula: 10000^(2i/d))
        # We use exp and log for mathematical stability
        div_term = torch.exp(torch.arange(0, embed_dim, 2).float() * (-math.log(10000.0) / embed_dim))
        
        # Apply Sine to the EVEN indices (0, 2, 4, ...)
        pe[:, 0::2] = torch.sin(position * div_term)
        
        # Apply Cosine to the ODD indices (1, 3, 5, ...)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        # Add a Batch dimension so it can be added to sentences: [1, Max_Seq_Len, Embed_Dim]
        pe = pe.unsqueeze(0)
        
        # Register as a buffer. 
        # This tells PyTorch to save it with the model, but DO NOT train it (it's fixed math!)
        self.register_buffer('pe', pe)

    def forward(self, x):
        """
        x shape: [Batch, Seq_Len, Embed_Dim]
        """
        seq_len = x.size(1)
        
        # We slice the pre-calculated PE grid to match the length of the current sentence!
        # And we simply ADD it to the word embeddings!
        x = x + self.pe[:, :seq_len, :]
        
        return x

def test_positional_encoding():
    print("--- RUNNING POSITIONAL ENCODING ---")
    
    BATCH_SIZE = 1
    SEQ_LEN = 100
    EMBED_DIM = 512
    
    # 1. Simulate a sentence of word embeddings (all zeros for visual clarity)
    sentence = torch.zeros(BATCH_SIZE, SEQ_LEN, EMBED_DIM)
    
    # 2. Apply Positional Encoding!
    pe_layer = PositionalEncoding(embed_dim=EMBED_DIM)
    encoded_sentence = pe_layer(sentence)
    
    print(f"Original Sentence Shape: {sentence.shape}")
    print(f"Encoded Sentence Shape:  {encoded_sentence.shape}")
    
    print("\nIf you look at the tensor, it is no longer zeros.")
    print("It is filled with a unique wave fingerprint for every single position!")

if __name__ == "__main__":
    test_positional_encoding()
```

### Key Takeaways from Code:
1. **`register_buffer`:** The Positional Encoding math is fixed. It never changes. By using `register_buffer`, we tell PyTorch to physically move this matrix to the GPU, but *exclude* it from the optimizer so gradients don't ruin the sine waves!
2. **The Addition:** `x = x + self.pe`. We don't concatenate. We literally add the waves directly into the word vectors. Because Neural Networks exist in high dimensional space, adding a small sine wave doesn't destroy the semantic meaning of the word; it just nudges the coordinate slightly based on time!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Implementing RoPE
Let's build a mental model of RoPE (Rotary Position Embeddings).
**Your Task:**
1. Unlike Sine waves which are added *before* the Transformer, RoPE is applied *inside* the Attention mechanism, directly to the Queries and Keys.
2. Conceptually take a 512D Query vector.
3. Group the numbers into pairs: $(q_0, q_1), (q_2, q_3), \dots$
4. Treat each pair as an $(x, y)$ coordinate on a 2D plane.
5. Apply a 2D Rotation Matrix to rotate that coordinate by an angle $\theta$, where $\theta$ is based on the word's position in the sentence.
6. The dot-product $Q \cdot K^T$ will now naturally decay as words get further apart, perfectly encoding relative distance!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your <abbr title="Large Language Model">LLM</abbr> was trained with a 4K context window, but product requirements demand a 32K context window. Compare positional encoding approaches for length extrapolation: ALiBi, RoPE with NTK-aware scaling, and YaRN."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Extrapolation Failure:** 
   - State that standard RoPE mathematically fails if you input a sequence longer than it was trained on. The angles of rotation become extreme, and the attention mechanism crashes.
2. **ALiBi:**
   - Explain that ALiBi naturally extrapolates without any fine-tuning. Because it just subtracts a linear penalty based on distance, it handles 32K perfectly. However, ALiBi generally has slightly lower baseline accuracy than RoPE.
3. **RoPE Scaling (NTK / YaRN):**
   - Conclude that the modern solution is to use **Interpolation**. Instead of trying to extrapolate to unseen distances, you mathematically *compress* the 32K sequence to "look like" a 4K sequence to the model! 
   - Mention that **YaRN** (Yet another RoPE extensioN) alters the base frequency of the RoPE rotations, allowing LLaMA to achieve 128K context windows with zero fine-tuning!

---
**Task for the end of the day:** Commit your code to Git. You have given your Transformer the ability to perceive Time.

Tomorrow, in **Day 64**, we build the actual cognitive brain of the Transformer: The **Feed-Forward Network** and the **SwiGLU** activation function!
