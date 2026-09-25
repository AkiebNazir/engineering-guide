# Day 79: Mixture of Experts (MoE) & Sparse Gating

Welcome to Day 79. GPT-4 is estimated to have 1.8 Trillion parameters. If GPT-4 was a standard "Dense" Transformer, it would take seconds to generate a single word. How does it type so fast?

It uses a **Mixture of Experts (<abbr title="Mixture of Experts">MoE</abbr>)** architecture. <abbr title="Mixture of Experts">MoE</abbr> is the ultimate architectural trick. It allows you to build a massive, hyper-intelligent model that runs at the speed of a tiny model.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Dense vs Sparse
In a standard **Dense** model (like LLaMA 2), every single parameter processes every single word. When the word "The" enters the network, all 70 Billion parameters perform a matrix multiplication on it. This is highly inefficient.
In a **Sparse** <abbr title="Mixture of Experts">MoE</abbr> model (like Mixtral 8x7B), only a fraction of the parameters activate for a given word. 

### 2. The <abbr title="Mixture of Experts">MoE</abbr> Architecture
In a standard Transformer Block, the output of the Self-Attention layer goes into a single Feed-Forward Network (FFN). 
**The <abbr title="Mixture of Experts">MoE</abbr> Trick:** We delete that single FFN, and replace it with 8 separate FFNs (called the "Experts").
- **Expert 1** might implicitly learn to specialize in Math.
- **Expert 2** might specialize in French.
- **Expert 3** might specialize in Python code.

### 3. The Router (Sparse Gating)
How does the network know which expert to use? We add a tiny **Router** (a simple Linear layer).
When a word comes out of the Attention layer, it hits the Router. 
The Router applies a Softmax to calculate a probability score for all 8 experts. 
**Top-K Routing:** The Router is instructed to only pick the **Top 2** experts. 
It sends the word *only* to those 2 experts. The other 6 experts remain completely asleep (they consume zero compute)!

**The Result:** Mixtral 8x7B has 47 Billion total parameters. But because any given word only activates 2 out of 8 experts, the math physically executed on the GPU is only 13 Billion parameters! You get the intelligence of a 47B model at the speed of a 13B model!

### 4. Load Balancing Loss
Routers are lazy. During training, if the Router randomly prefers Expert 1, it will send all words to Expert 1. Expert 1 will become highly trained, while the other 7 experts die (Expert Collapse). 
To prevent this, we must add an **Auxiliary Load Balancing Loss** to the training loop. This mathematically penalizes the Router if it doesn't distribute tokens equally across all 8 experts!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build the <abbr title="Mixture of Experts">MoE</abbr> Layer from scratch! We will build 4 Experts, a Router, and the Top-K masking logic.

Create a file named `mixture_of_experts.py`:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class Expert(nn.Module):
    """A standard Feed-Forward Network (just one of many!)"""
    def __init__(self, d_model, d_hidden):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(d_model, d_hidden),
            nn.ReLU(),
            nn.Linear(d_hidden, d_model)
        )
    def forward(self, x):
        return self.net(x)

class MoELayer(nn.Module):
    def __init__(self, d_model, num_experts=4, top_k=2):
        super().__init__()
        self.num_experts = num_experts
        self.top_k = top_k
        
        # 1. The Experts (A list of 4 identical FFNs)
        self.experts = nn.ModuleList([Expert(d_model, d_model * 4) for _ in range(num_experts)])
        
        # 2. The Router (Predicts a score for each expert)
        self.router = nn.Linear(d_model, num_experts)

    def forward(self, x):
        batch_size, seq_len, d_model = x.shape
        # Flatten sequence to process each word individually
        x_flat = x.view(-1, d_model) 
        
        # 1. Router logits [Num_Words, Num_Experts]
        router_logits = self.router(x_flat)
        
        # 2. Get the Top-K experts for each word!
        # routing_weights: The softmax probabilities of the winners
        # selected_experts: The indices of the winning experts (e.g., Expert 1 and 3)
        routing_weights, selected_experts = torch.topk(router_logits, self.top_k, dim=-1)
        routing_weights = F.softmax(routing_weights, dim=-1)
        
        # 3. Initialize an empty output tensor
        final_output = torch.zeros_like(x_flat)
        
        # 4. Route the words to the experts! (This is conceptual, in production this is highly parallelized)
        for i, expert in enumerate(self.experts):
            # Find which words were sent to THIS expert
            # Create a boolean mask of words where this expert is in their Top-K list
            expert_mask = (selected_experts == i).any(dim=-1)
            
            if expert_mask.any():
                # Extract the specific words meant for this expert
                expert_inputs = x_flat[expert_mask]
                
                # Run the expert (The heavy compute happens here!)
                expert_outputs = expert(expert_inputs)
                
                # Find WHERE in the top_k list this expert was chosen (to get the correct weighting)
                # If it was the #1 choice, it might have a weight of 0.8. If #2, weight of 0.2.
                idx_in_topk = (selected_experts[expert_mask] == i).nonzero(as_tuple=True)[1]
                weights = routing_weights[expert_mask, idx_in_topk].unsqueeze(-1)
                
                # Add the weighted output back into the final tensor
                final_output[expert_mask] += expert_outputs * weights
                
        return final_output.view(batch_size, seq_len, d_model)

def test_moe():
    print("--- RUNNING MIXTURE OF EXPERTS (MoE) ---")
    
    BATCH_SIZE = 2
    SEQ_LEN = 5
    D_MODEL = 64
    
    # 1. Create mock input (10 total words)
    x = torch.randn(BATCH_SIZE, SEQ_LEN, D_MODEL)
    
    # 2. Initialize MoE with 8 experts, routing to Top-2
    moe = MoELayer(d_model=D_MODEL, num_experts=8, top_k=2)
    
    # 3. Forward pass
    output = moe(x)
    
    print(f"Input Shape: {x.shape}")
    print(f"Output Shape: {output.shape}")
    print("\nNotice: The math succeeded! Behind the scenes, the Router looked at all 10 words,")
    print("and dynamically activated ONLY 2 out of the 8 experts for each specific word.")
    print("This means 6 of the FFNs did absolutely zero math, saving massive compute!")

if __name__ == "__main__":
    test_moe()
```

### Key Takeaways from Code:
1. **The `expert_mask`:** Notice how we physically extract `expert_inputs = x_flat[expert_mask]`. If an expert is not chosen, it processes a tensor of size `0`. This is where the compute is saved!
2. **The Output Summation:** If Word 1 is sent to Expert A and Expert B, the final output for Word 1 is `(Output_A * Weight_A) + (Output_B * Weight_B)`.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Load Balancing Loss
Without a penalty, the Router will collapse.
**Your Task:**
1. In the `forward` pass, calculate the **Fraction of words** routed to each expert in the batch (e.g., `f = [0.9, 0.1, 0.0, 0.0]`).
2. Calculate the **Average Probability** assigned to each expert by the router (e.g., `p = [0.8, 0.1, 0.05, 0.05]`).
3. The standard <abbr title="Mixture of Experts">MoE</abbr> Load Balancing Loss is the dot product of those two vectors, multiplied by the number of experts: `Loss = N * sum(f * p)`.
4. If the router sends everything to Expert 1, $f \times p$ is massive. If it distributes evenly, the loss is minimized!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Mixtral 8x7B has 47B parameters but only activates 13B per token. Explain the serving challenges regarding memory footprint, routing overhead, and Expert Parallelism. How does <abbr title="Mixture of Experts">MoE</abbr> affect batching?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Memory Trap:** 
   - State clearly that while Mixtral runs at the *speed* of a 13B model, it still requires the *VRAM footprint* of a 47B model. You must load all 8 experts into memory simultaneously because you never know which expert the router will pick next. It saves compute (FLOPs), not memory.
2. **Batching Fragmentation (The Overhead):**
   - Explain that in a dense model, a batch of 1,000 words is multiplied in one massive, perfectly optimized matrix operation. 
   - In an <abbr title="Mixture of Experts">MoE</abbr>, those 1,000 words are shattered. 200 go to Expert 1, 50 go to Expert 2, etc. This fragmentation severely degrades GPU utilization because you are running many small matrix multiplications instead of one big one.
3. **Expert Parallelism:**
   - Propose that at massive scale, you use **Expert Parallelism**. You put Expert 1 on GPU 1, and Expert 2 on GPU 2. 
   - Note the network bottleneck: The Router on GPU 0 must literally transmit the token data across the server (via NVLink) to GPU 2, wait for the expert to compute, and receive the data back. All-to-All communication overhead is the primary bottleneck of massive MoEs.

---
**Task for the end of the day:** Commit your code to Git. 

You have mastered the <abbr title="Mixture of Experts">MoE</abbr>! Tomorrow, in **Day 80**, we look at an architecture that wants to kill the Transformer entirely. We will build **Mamba (State Space Models)**!
