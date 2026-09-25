# Day 61: Self-Attention (The Core Innovation)

Welcome to Day 61. Today we officially enter **Phase 3**.

In 2017, a team of Google researchers published a paper titled *"Attention Is All You Need"*. They were tired of how slow RNNs were to train. They took the Cross-Attention mechanism we learned in Day 47, realized they didn't actually need the <abbr title="Recurrent Neural Network">RNN</abbr> loop at all, and threw it in the garbage.

They invented the **Transformer**. Today, we learn the single mathematical equation that powers ChatGPT, Claude, and LLaMA: **Scaled Dot-Product Self-Attention**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Death of the <abbr title="Recurrent Neural Network">RNN</abbr>
An <abbr title="Recurrent Neural Network">RNN</abbr> must read Word 1, then Word 2, then Word 3. It is sequential. It is slow.
The Transformer looks at Word 1, Word 2, and Word 3 *at the exact same time*. It is parallel. It is blazing fast.

But if it looks at all the words simultaneously, how does it know which words are related?
It uses **Self-Attention**. Every single word in the sentence mathematically asks every other word in the sentence: *"How relevant are you to me right now?"*

### 2. Queries, Keys, and Values (The Database Analogy)
Self-Attention uses an analogy based on retrieving data from a Database.
Imagine you type a **Query** into YouTube: *"Funny cat video"*. 
YouTube searches through the **Keys** of every video (The title and tags). 
When the Query matches a Key, YouTube returns the **Value** (the actual MP4 video file).

In the Transformer, *every single word* generates all three!
- **Query (Q):** What the word is looking for. (e.g., The word *"Bank"* outputs a Query looking for context).
- **Key (K):** What the word contains. (e.g., The word *"River"* outputs a Key saying "I contain water").
- **Value (V):** The actual mathematical payload of the word.

Because *"Bank"*'s Query perfectly aligns with *"River"*'s Key, they mathematically bond, and the Transformer instantly realizes that *"Bank"* means dirt, not money!

### 3. The Master Equation
This is the most important equation of the decade:
$$ \text{Attention}(Q,K,V) = \text{softmax}\left(\frac{Q \cdot K^T}{\sqrt{d_k}}\right)V $$

1. $Q \cdot K^T$: The Dot Product. If a Query and a Key point in the same direction, this results in a massive positive score (High Attention).
2. **The Softmax:** Converts the raw scores into percentages (0.0 to 1.0).
3. **Multiply by $V$:** We take the percentages and multiply them against the Values, creating a brand new, context-infused vector!

### 4. Why divide by $\sqrt{d_k}$? (The Scaling Factor)
If your vectors are 512 dimensions large, the Dot Product adds up 512 separate multiplications. The resulting score will be massive (e.g., $1000$). 
If you feed $1000$ into a Softmax function, the Softmax gets pushed into the extreme flat corners of the curve. The gradients vanish to exactly $0.0$, and the <abbr title="Artificial Intelligence">AI</abbr> instantly stops learning!
By dividing the score by $\sqrt{d_k}$ (e.g., $\sqrt{512} \approx 22.6$), we shrink the scores back down, keeping the variance at exactly $1.0$, allowing Calculus to flow perfectly!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build Scaled Dot-Product Self-Attention entirely from scratch in PyTorch. 

Create a file named `self_attention.py`:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F
import math

class SelfAttention(nn.Module):
    """
    The exact math behind ChatGPT's contextual understanding.
    """
    def __init__(self, embed_dim):
        super().__init__()
        self.embed_dim = embed_dim
        
        # The Linear layers that generate the Queries, Keys, and Values
        # for EVERY word simultaneously!
        self.W_q = nn.Linear(embed_dim, embed_dim, bias=False)
        self.W_k = nn.Linear(embed_dim, embed_dim, bias=False)
        self.W_v = nn.Linear(embed_dim, embed_dim, bias=False)

    def forward(self, x):
        """
        x shape: [Batch, Seq_Len, Embed_Dim] (e.g., a 10-word sentence)
        """
        # 1. Generate Q, K, and V for all words!
        # Shape remains: [Batch, Seq_Len, Embed_Dim]
        Q = self.W_q(x)
        K = self.W_k(x)
        V = self.W_v(x)
        
        # 2. Calculate the Alignment Scores: Q * K^T
        # We must transpose K so the matrix multiplication aligns: [Batch, Embed_Dim, Seq_Len]
        # Result shape: [Batch, Seq_Len, Seq_Len] (A grid of how much every word cares about every other word!)
        scores = torch.bmm(Q, K.transpose(1, 2))
        
        # 3. Apply the Scaling Factor (Divide by sqrt(d_k))
        # This prevents the Softmax gradients from vanishing!
        scaling_factor = math.sqrt(self.embed_dim)
        scaled_scores = scores / scaling_factor
        
        # 4. Softmax to get Percentages
        # We apply softmax along the LAST dimension (the Keys)
        attention_weights = F.softmax(scaled_scores, dim=-1)
        
        # 5. Multiply by the Values!
        # [Batch, Seq_Len, Seq_Len] * [Batch, Seq_Len, Embed_Dim] 
        # Result shape: [Batch, Seq_Len, Embed_Dim]
        context_infused_output = torch.bmm(attention_weights, V)
        
        return context_infused_output, attention_weights

def test_self_attention():
    print("--- RUNNING SCALED DOT-PRODUCT SELF-ATTENTION ---")
    
    BATCH_SIZE = 1
    SEQ_LEN = 4 # E.g., "The", "bank", "of", "river"
    EMBED_DIM = 512
    
    # Simulate the raw word embeddings
    sentence_embeddings = torch.randn(BATCH_SIZE, SEQ_LEN, EMBED_DIM)
    
    model = SelfAttention(embed_dim=EMBED_DIM)
    output, weights = model(sentence_embeddings)
    
    print(f"Input Shape:  {sentence_embeddings.shape}")
    print(f"Output Shape: {output.shape}")
    print(f"Attention Grid Shape: {weights.shape} (A 4x4 matrix mapping every word to every word!)")
    
    print("\nLet's look at the Attention Weights for Word 2 ('bank'):")
    # Grab the second row of the 4x4 matrix
    bank_weights = weights[0, 1, :].detach().numpy()
    words = ["The", "bank", "of", "river"]
    
    for word, pct in zip(words, bank_weights):
        print(f"Focus on '{word:5}': {pct*100:.1f}%")
        
    print("\nBecause we didn't train it, the percentages are random.")
    print("But after training, the AI will heavily focus on the word 'river'!")

if __name__ == "__main__":
    test_self_attention()
```

### Key Takeaways from Code:
1. **No Loops!** Notice there is absolutely no `for` loop in this code. We process all 4 words at the exact same time using `torch.bmm` (Batch Matrix Multiplication). Because GPUs have thousands of cores, this runs almost instantly, whereas an <abbr title="Recurrent Neural Network">RNN</abbr> would have to wait 4 sequential steps.
2. **The 4x4 Attention Grid:** The `scores` tensor has a shape of `[Batch, 4, 4]`. This is literally a 2D map showing the mathematical relationship between every possible combination of words in the sentence.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Padded Sequence Masking
In reality, sentences have different lengths. We pad them with `<PAD>` tokens to make the batch rectangular (e.g., "I like cats `<PAD>` `<PAD>`"). 
You do not want the <abbr title="Artificial Intelligence">AI</abbr> to pay attention to `<PAD>` tokens!
**Your Task:**
1. Conceptually modify the `forward` function to accept an `attention_mask` tensor (a matrix of 1s for real words, and 0s for `<PAD>` words).
2. Right before you apply the `Softmax`, you must use `masked_fill_`.
3. Fill all the `<PAD>` locations in the `scaled_scores` tensor with a massive negative number: `-1e9`.
4. Now, when the `Softmax` runs, $e^{-1,000,000,000}$ evaluates to exactly $0.0$. The <abbr title="Artificial Intelligence">AI</abbr> will mathematically pay $0\%$ attention to the padding!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Derive the necessity of the scaling factor $\sqrt{d_k}$ in the Self-Attention equation from first principles. What exactly happens to the gradient flow through the Softmax function if we remove it for a model with a dimension of 1024?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Variance of Dot Products:** 
   - State that if the Query and Key vectors have elements with a Mean of 0 and a Variance of 1, their dot product $q \cdot k = \sum_{i=1}^{d_k} q_i k_i$ will have a Mean of 0, but a Variance of exactly $d_k$ (e.g., 1024).
2. **The Softmax Saturation:**
   - Explain that a variance of 1024 means the raw scores will be massive (e.g., +30, -45, +100). 
   - When fed into the Softmax function $e^{x_i} / \sum e^{x_j}$, the largest number (+100) will completely dominate the denominator. The Softmax output will instantly collapse to a one-hot vector: `[0.0, 0.0, 1.0, 0.0]`.
3. **The Vanishing Gradient:**
   - Conclude that the derivative of a saturated Softmax (where the output is near 1 or 0) is essentially zero. Without the $\sqrt{1024}$ division, the gradients vanish, and the Transformer is mathematically incapable of learning.

---
**Task for the end of the day:** Commit your code to Git. You have built the core engine of modern <abbr title="Natural Language Processing">NLP</abbr>.

Tomorrow, in **Day 62**, we realize that words have multiple different relationships simultaneously. We will split our attention into multiple parallel dimensions using **Multi-Head Attention!**
