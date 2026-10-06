# Day 77: Model Pruning (Unstructured vs Structured)

Welcome to Day 77. We have entered **Phase 6: Enterprise AI Engineering**.
In Day 76, we learned Knowledge Distillation, which required training an entirely new "Student" model. 

But what if you don't have the compute to train a new model? What if you just take the massive 70-Billion parameter model, open up its brain, and physically delete $50\%$ of its neurons? 

This is **Model Pruning**. Today we learn how to slice gigabytes out of a model by targeting its weakest connections.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Lottery Ticket Hypothesis
Why do we build massive models if we are just going to delete half of it? 
In 2018, Jonathan Frankle published the **Lottery Ticket Hypothesis**. 
A massive neural network is like buying 1 Billion lottery tickets. You initialize 1 Billion random weights, hoping some of them are in the perfect starting position to learn the task. 
After training is complete, you realize that only $10\%$ of the weights actually did the hard work (the "Winning Tickets"). The other $90\%$ of the weights are doing almost nothing! 
Pruning simply deletes the losing tickets.

### 2. Unstructured Pruning (Magnitude Pruning)
How do we find the losing tickets? We look at the magnitude of the weights.
If a weight in a Linear Layer is $0.95$, it is heavily influencing the output. If a weight is $0.00001$, it is mathematically irrelevant. 
In **Magnitude Pruning**, we sort the weights, and permanently change the smallest $50\%$ to exactly `0.0`. 
- **The Pro:** It compresses the file size massively. When you ZIP a file containing millions of `0.0`s, the file shrinks from 5GB to 1GB!
- **The Con:** Modern GPUs are designed for dense matrix multiplication. They are actually very bad at skipping random `0`s. So while the file size shrinks, **the inference speed on the GPU does not get faster!**

### 3. Structured Pruning
If we want the model to actually run faster, we must use **Structured Pruning**.
Instead of deleting random individual weights, we delete entire structural components!
- We delete an entire Row from the matrix.
- We delete an entire Column from the matrix.
- We delete an entire Attention Head! (e.g., shrinking $N_{heads}$ from 12 to 10).

Because we physically shrunk the dimensions of the matrix (e.g., $1024 \times 1024 \rightarrow 800 \times 1024$), the GPU does less math, resulting in massive latency reductions and real-world speedups!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's implement Magnitude Pruning using PyTorch's built-in pruning utilities! We will take a Linear layer, delete $30\%$ of its brain, and observe the "Sparse" matrix.

Create a file named `model_pruning.py`:

```python
import torch
import torch.nn as nn
import torch.nn.utils.prune as prune

def test_pruning():
    print("--- RUNNING UNSTRUCTURED MAGNITUDE PRUNING ---")
    
    # 1. Create a tiny mock Linear layer
    layer = nn.Linear(in_features=5, out_features=5)
    
    # Print the original weights
    print("Original Weights (Notice they are all non-zero):")
    print(layer.weight.data)
    
    # 2. Apply Magnitude Pruning
    # We tell PyTorch to prune 30% (amount=0.3) of the connections based on L1 norm (absolute value)
    prune.l1_unstructured(layer, name='weight', amount=0.3)
    
    print("\nPruned Weights (Notice the 0.0s!):")
    print(layer.weight.data)
    
    # 3. How PyTorch handles Pruning under the hood
    print("\nPyTorch doesn't actually delete the weights yet. It creates a Mask!")
    print("Weight Mask:")
    print(list(layer.named_buffers())[0][1]) # The mask buffer
    
    # 4. Make it permanent!
    # Removes the mask and makes the 0.0s permanent in the layer.weight parameter
    prune.remove(layer, 'weight')
    
    # 5. Calculate Sparsity
    total_weights = layer.weight.nelement()
    zero_weights = torch.sum(layer.weight == 0).item()
    sparsity = zero_weights / total_weights
    
    print(f"\nFinal Sparsity: {sparsity * 100}% of the brain has been deleted!")

if __name__ == "__main__":
    test_pruning()
```

### Key Takeaways from Code:
1. **The Mask:** During training, if you just set a weight to `0.0`, the gradient will immediately update it back to a non-zero number in the next step. PyTorch uses a boolean `weight_mask`. During the forward pass, it multiplies the weights by the mask, mathematically enforcing the zero without breaking autograd!
2. **`prune.remove`:** This doesn't remove the pruning; it makes the pruning permanent for deployment by baking the zeros directly into the final `layer.weight` tensor.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Attention Head Pruning
In Day 65 (BERT), we implemented Multi-Head Attention.
**Your Task:**
1. Conceptually design a script to prune Attention Heads.
2. An Attention Head has $W_Q, W_K, W_V$ and $W_O$ matrices.
3. If you want to delete Head #4 out of 12, you cannot use unstructured `0.0`s. 
4. You must use PyTorch tensor slicing (`tensor[:, :dim]`) to literally slice out the chunk of the matrix that corresponds to Head #4, creating a physically smaller tensor!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Unstructured magnitude pruning can achieve 90% sparsity with almost no accuracy loss, but Structured pruning often causes accuracy drops at just 30% sparsity. Yet, production systems prefer Structured pruning. Explain why, and design a pruning strategy that achieves real-world latency reduction."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Accuracy Discrepancy:** 
   - State that Unstructured pruning is highly precise. It surgically removes *only* the dead weights. 
   - Structured pruning deletes entire rows/neurons. Even if $90\%$ of a row is dead, deleting the row also deletes the $10\%$ of highly critical weights in that row, causing immediate accuracy degradation.
2. **The Hardware Reality:**
   - Explain that modern GPUs (like A100s) execute math using massive Tensor Cores. Tensor Cores require dense, contiguous blocks of memory. Random `0`s (Unstructured) do not speed up the matrix multiplication because the Tensor Core still multiplies the `0`. 
   - Structured pruning physically shrinks the $M \times N$ dimensions, resulting in fewer FLOPs and less memory bandwidth, directly lowering latency.
3. **The Production Strategy:**
   - Propose an **Iterative Structured Pruning** pipeline:
     1. Train the dense model.
     2. Prune $10\%$ of the channels/heads.
     3. **Fine-tune** the model for a few epochs so the remaining weights can "heal" and compensate for the lost channels.
     4. Repeat steps 2 and 3 until target latency is reached.

---
**Task for the end of the day:** Commit your code to Git. 

Pruning deletes weights. But what if we kept ALL the weights, but just compressed their resolution? 
Tomorrow, in **Day 78**, we learn **Quantization** and how 4-bit math allows LLMs to run on laptops!
