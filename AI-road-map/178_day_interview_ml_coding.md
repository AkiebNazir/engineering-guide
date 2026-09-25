# Day 178: MAANG Mock Interview: <abbr title="Machine Learning">ML</abbr> Coding & Mathematical Rigor

Welcome to Day 178.

You survived the System Design round. Now comes the **<abbr title="Machine Learning">ML</abbr> Coding** round.
Unlike a standard Software Engineering interview (where you invert a Binary Tree), an <abbr title="Machine Learning">ML</abbr> Coding interview tests two things simultaneously:
1. Can you write clean, vectorized Python code?
2. Do you actually understand the math beneath the PyTorch abstractions?

If you rely on `model.fit()` and have no idea how Backpropagation or Attention actually works, you will fail this round.

Today, we practice the ultimate <abbr title="Machine Learning">ML</abbr> Coding question: **"Implement Self-Attention from scratch."**

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Anatomy of an <abbr title="Machine Learning">ML</abbr> Coding Interview
You will typically be asked to do one of three things:
- **Implement from Scratch:** e.g., "Write K-Means clustering using only NumPy."
- **Debug a Training Loop:** The interviewer gives you a PyTorch script. The loss isn't converging. You must find the subtle bug (e.g., they forgot `optimizer.zero_grad()` or applied Softmax before CrossEntropyLoss).
- **Data Engineering:** e.g., "Write a generator function that yields balanced batches from a massive, imbalanced dataset that doesn't fit in memory."

### 2. The Mathematical Rigor Expectation
When you write the code, the interviewer will interrupt you:
*"Why did you divide by the square root of the dimension size?"*
If your answer is "Because that's what the paper did," you lose points.
Your answer must be: *"Because the dot product of two vectors grows exponentially with their dimension size. If the numbers get too large, the Softmax function will be pushed into regions with extremely small gradients, causing the Vanishing Gradient problem during backpropagation."*

### 3. Vectorization (No For-Loops)
If you write a `for` loop to multiply matrices in Python, you will fail. 
Python `for` loops are incredibly slow because Python is an interpreted language. You MUST use vectorized operations in NumPy or PyTorch (`np.dot`, `torch.matmul`). These libraries push the calculation down into highly optimized C++ and CUDA code, running thousands of times faster.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's simulate a live coding interview. The prompt is: *"Write the Scaled Dot-Product Attention mechanism (the core of the Transformer) from scratch using only PyTorch."*

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

# --- WHAT YOU WRITE ON THE VIRTUAL WHITEBOARD ---

class SelfAttentionInterview(nn.Module):
    def __init__(self, embed_dim: int):
        super().__init__()
        self.embed_dim = embed_dim
        
        # 1. Explain out loud: "We need three linear transformations to create 
        # the Query, Key, and Value vectors from our input embeddings."
        self.W_q = nn.Linear(embed_dim, embed_dim, bias=False)
        self.W_k = nn.Linear(embed_dim, embed_dim, bias=False)
        self.W_v = nn.Linear(embed_dim, embed_dim, bias=False)

    def forward(self, x: torch.Tensor, mask: torch.Tensor = None):
        # x shape: (batch_size, sequence_length, embed_dim)
        
        # 2. Generate Q, K, V
        Q = self.W_q(x)
        K = self.W_k(x)
        V = self.W_v(x)
        
        # 3. Calculate Attention Scores
        # Explain: "We multiply Q by K-transposed to see how much each word 
        # should 'pay attention' to every other word."
        
        # Note: We transpose only the last two dimensions of K!
        # Q shape: (B, Seq, Dim) | K.transpose shape: (B, Dim, Seq)
        # Resulting scores shape: (B, Seq, Seq)
        scores = torch.matmul(Q, K.transpose(-2, -1))
        
        # 4. The Mathematical Rigor (Scaling)
        # Explain: "We divide by sqrt(embed_dim) to stabilize gradients before Softmax."
        scores = scores / (self.embed_dim ** 0.5)
        
        # 5. Optional Masking
        # Explain: "If this is a decoder, we must mask future tokens so it can't cheat."
        if mask is not None:
            # We fill masked positions with negative infinity. 
            # Softmax of -infinity is exactly 0.
            scores = scores.masked_fill(mask == 0, float('-inf'))
            
        # 6. Apply Softmax
        # Explain: "This converts the raw scores into probabilities that sum to 1."
        attention_weights = F.softmax(scores, dim=-1)
        
        # 7. Final Output
        # Multiply the weights by the Value vectors
        output = torch.matmul(attention_weights, V)
        
        return output

# --- INTERVIEW EXECUTION ---
def run_interview_test():
    print("--- INTERVIEWER: 'Does your code run?' ---")
    
    # Batch size 2, Sequence length 4 (e.g., 4 words), Embedding dimension 8
    dummy_input = torch.rand(2, 4, 8)
    attention_layer = SelfAttentionInterview(embed_dim=8)
    
    output = attention_layer(dummy_input)
    
    print(f"Input Shape:  {dummy_input.shape}")
    print(f"Output Shape: {output.shape}")
    print("✅ The shapes match! The attention mechanism successfully processed the sequence.")

# To run:
# run_interview_test()
```

### 🔍 Understanding the Enterprise Value
During this 20-minute coding exercise, you proved three things to the interviewer:
1. You understand PyTorch tensor shapes and broadcasting (using `transpose(-2, -1)`).
2. You understand the math (Scaling by `sqrt(d_k)` and masking with `-inf`).
3. You communicated your thought process clearly before writing each block of code.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
The interviewer says: *"Great job on the Attention mechanism. Now, write a Python generator function that yields batches of data from a massive CSV file that is too large to fit in <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr>. Ensure the batches are shuffled."*
**Your Task:** Write this function. (Hint: Read the CSV in chunks. Maintain a small buffer in memory. Shuffle the buffer, yield a batch, and read the next chunk into the buffer).

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"You trained a binary classification model. The training accuracy is 98%, but the validation accuracy is 65%. Your junior engineer says 'Let's just add 100,000 more rows of training data.' Is the junior engineer right? Explain mathematically."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Diagnosis (Overfitting):** Identify immediately that a 98% train / 65% val split means the model has massively overfit. It has memorized the training data and is failing to generalize.
2. **The High Variance Problem:** Use Andrew Ng's terminology. The model has High Variance. 
3. **Addressing the Junior Engineer:** Explain that adding more data *is* actually a valid way to combat High Variance (it forces the model to learn general patterns instead of memorizing). However, it is the most expensive and time-consuming solution.
4. **Better Solutions (Regularization):** Propose much faster mathematical solutions to try first:
   - Increase Dropout (forcing the network to rely on multiple pathways).
   - Add L2 Weight Decay (penalizing the network for relying too heavily on any single feature).
   - Reduce model complexity (e.g., shrink the network from 100 layers to 10 layers so it doesn't have enough "memory capacity" to memorize the training data).

---
**Task for the end of the day:** Practice writing K-Means clustering in Python using only standard lists and the `math` library. It is a classic interview question.

Tomorrow, in **Day 179**, we face the final interview round: **Behavioral & Technical Leadership**. How do you convince a panel that you are a Principal-level Engineer who can lead teams and navigate ambiguity?
