# Day 65: The Complete Transformer Encoder (BERT)

Welcome to Day 65. Over the last 4 days, we have built Multi-Head Attention, Positional Encodings, and Feed-Forward Networks. 

Today, we snap them together like Lego bricks to build the **Transformer Encoder**. This specific architecture is what powers **BERT** (Bidirectional Encoder Representations from Transformers). 

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Goal of the Encoder
The Transformer Encoder does **NOT** generate text. It cannot write essays. 
Its only job is to **Understand Context**. 
You feed it a 10-word sentence. It outputs 10 mathematical vectors. Those 10 vectors contain the absolute perfect, bidirectional understanding of the entire sentence. 

### 2. Bidirectional Context
Why is BERT so smart? Because it is allowed to cheat.
When an RNN reads the sentence: *"I went to the bank to deposit my check"*, when it reaches the word "bank", it doesn't know what "check" means yet, because "check" is in the future.
The Transformer Encoder processes the entire sentence simultaneously. The word "bank" mathematically looks *forwards* to the word "check" and *backwards* to the word "went" at the exact same time. It has **Bidirectional Context**.

### 3. Stacking Layers
A single layer of Attention is not enough. 
- Layer 1: Words look at adjacent words to form short phrases ("the dog").
- Layer 2: Phrases look at other phrases to form clauses.
- Layer 12: The entire sentence is completely mathematically intertwined.
BERT Base has 12 layers. BERT Large has 24 layers. They are completely identical blocks, stacked on top of each other!

### 4. The [CLS] Token
If you want to use BERT to classify the sentiment of a movie review (Positive/Negative), how do you do it? BERT outputs 500 word vectors. Which one do you use?
Researchers invented a genius hack: The **[CLS] Token** (Classification Token).
We artificially inject the `[CLS]` token at the very beginning of the sentence: `[CLS] The movie was great`.
As it passes through 12 layers of Attention, the `[CLS]` token mathematically absorbs the meaning of *every other word in the sentence*.
At the end of Layer 12, we throw away all the word vectors, and we just pass the `[CLS]` vector into an `nn.Linear` layer to predict sentiment!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a complete Transformer Encoder layer, and stack it $N$ times to create a full BERT architecture!

Create a file named `transformer_encoder.py`:

```python
import torch
import torch.nn as nn

# (Assume we have imported our MHA and FFN from previous days)
from multi_head_attention import MultiHeadAttention
from transformer_ffn import StandardFFN

class TransformerEncoderLayer(nn.Module):
    """
    A single block of the Transformer Encoder.
    We use the modern Pre-Norm architecture!
    """
    def __init__(self, embed_dim=512, num_heads=8, expand_dim=2048):
        super().__init__()
        
        # 1. The Attention Brain
        self.mha = MultiHeadAttention(embed_dim, num_heads)
        
        # 2. The Factual Brain
        self.ffn = StandardFFN(embed_dim, expand_dim)
        
        # 3. Normalization (To keep gradients stable)
        self.norm1 = nn.LayerNorm(embed_dim)
        self.norm2 = nn.LayerNorm(embed_dim)

    def forward(self, x):
        # x shape: [Batch, Seq_Len, Embed_Dim]
        
        # --- BLOCK 1: ATTENTION ---
        # Pre-Norm
        x_norm = self.norm1(x)
        # Attention
        attention_out = self.mha(x_norm)
        # The Residual Connection (Add the original x!)
        x = x + attention_out
        
        # --- BLOCK 2: FEED-FORWARD ---
        # Pre-Norm
        x_norm = self.norm2(x)
        # FFN
        ffn_out = self.ffn(x_norm)
        # The Residual Connection
        x = x + ffn_out
        
        return x

class TransformerEncoder(nn.Module):
    """
    The full BERT architecture! Stacking N layers together.
    """
    def __init__(self, vocab_size, num_layers=6, embed_dim=512, num_heads=8):
        super().__init__()
        
        # Word Embeddings
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        
        # Positional Encoding (Mocked for simplicity)
        self.pos_encoding = nn.Parameter(torch.randn(1, 1000, embed_dim))
        
        # The Stack of N Encoder Layers!
        # nn.ModuleList allows us to hold a list of PyTorch layers
        self.layers = nn.ModuleList([
            TransformerEncoderLayer(embed_dim, num_heads) 
            for _ in range(num_layers)
        ])
        
        # A final LayerNorm is required when using Pre-Norm architecture!
        self.final_norm = nn.LayerNorm(embed_dim)

    def forward(self, input_ids):
        # input_ids: [Batch, Seq_Len]
        batch_size, seq_len = input_ids.shape
        
        # 1. Embed the words
        x = self.embedding(input_ids)
        
        # 2. Add Positional Encoding
        x = x + self.pos_encoding[:, :seq_len, :]
        
        # 3. Pass through all N layers!
        for layer in self.layers:
            x = layer(x)
            
        # 4. Final Norm
        x = self.final_norm(x)
        
        return x

def test_encoder():
    print("--- RUNNING TRANSFORMER ENCODER (BERT) ---")
    
    BATCH_SIZE = 2
    SEQ_LEN = 15
    VOCAB_SIZE = 10000
    
    # Simulate two sentences of 15 words each
    sentences = torch.randint(0, VOCAB_SIZE, (BATCH_SIZE, SEQ_LEN))
    
    # Build a 6-layer BERT
    bert = TransformerEncoder(vocab_size=VOCAB_SIZE, num_layers=6)
    
    output = bert(sentences)
    
    print(f"Input Shape:  {sentences.shape} (2 Sentences, 15 Words)")
    print(f"Output Shape: {output.shape} (2 Sentences, 15 Words, 512D Vectors)")
    
    print("\nNotice the shape didn't change! The Encoder just refined the mathematical meaning of every single word 6 times over!")

if __name__ == "__main__":
    test_encoder()
```

### Key Takeaways from Code:
1. **The Residual Magic:** Look at `x = x + attention_out`. If a layer is completely useless, `attention_out` goes to zero, and the network just passes `x` forward untouched. This prevents deep networks from degrading!
2. **`nn.ModuleList`:** You cannot use a standard Python list `[]` to hold PyTorch layers. If you do, PyTorch won't register their parameters, and they won't train! You must use `nn.ModuleList` to stack layers.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The [CLS] Classifier
You have built BERT. Now use it to classify Sentiment.
**Your Task:**
1. Conceptually create a `BERTClassifier` class.
2. Initialize the `TransformerEncoder` inside it.
3. Add a final `nn.Linear(embed_dim, num_classes)` layer.
4. In the `forward` pass, pass the sentence through the Encoder.
5. You receive an output of shape `[Batch, Seq_Len, Embed_Dim]`.
6. Slice it to grab ONLY the first token (`seq_len` index `0`): `cls_token = output[:, 0, :]`.
7. Pass that `cls_token` into your Linear layer to predict Sentiment! 

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your Transformer encoder's Self-Attention layers scale quadratically $O(n^2)$ with sequence length, making 100k-token documents impossible. Propose three different architectural strategies to reduce the computational complexity of the Attention matrix while preserving context."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Sparse Attention (Local Window):** 
   - Propose forcing words to only attend to the $N$ words immediately surrounding them. This drops complexity to $O(n \times w)$. To preserve global context, you can add a few "Global Tokens" (like BigBird) that attend to everything.
2. **Linear Attention (Kernel Tricks):**
   - Explain that by removing the Softmax function, you can change the order of matrix multiplication from $(Q K^T) V$ to $Q (K^T V)$. 
   - Because $K^T V$ creates a tiny fixed-size matrix, the complexity instantly drops to $O(n)$, completely solving the sequence length bottleneck!
3. **Flash Attention (Hardware Optimization):**
   - Clarify that Flash Attention doesn't change the math or the $O(n^2)$ complexity. Instead, it solves the **IO Bottleneck**. It uses "Tiling" to prevent the GPU from constantly moving data between slow HBM memory and fast SRAM, resulting in a massive $3\times$ real-world speedup!

---
**Task for the end of the day:** Commit your code to Git. 

Tomorrow, in **Day 66**, we build the exact architecture behind GPT-4. We will build the **Transformer Decoder**, and we will learn how to mathematically prevent it from looking into the future!
