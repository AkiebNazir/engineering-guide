# Day 96: Parameter-Efficient Fine-Tuning (PEFT)

Welcome to Day 96. Over the last three days, we learned how to pre-train a 70 Billion parameter model across 256 GPUs. 

But what if you are a developer who just wants to fine-tune LLaMA to write code for your specific company? You don't have 256 GPUs. You have a single RTX 4090 GPU with 24GB of VRAM.
If you try to run **Full Fine-Tuning**, the Adam optimizer will instantly crash your GPU.

Today, we learn the mathematics of **PEFT (Parameter-Efficient Fine-Tuning)**, which allows you to fine-tune a massive AI using almost zero VRAM!

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Full Fine-Tuning vs PEFT
- **Full Fine-Tuning:** You unfreeze all 70 Billion weights. During backpropagation, you calculate gradients for all 70B weights. The Adam optimizer stores momentum vectors for all 70B weights. You run out of memory instantly. Furthermore, you suffer from **Catastrophic Forgetting** (by editing all the weights, the model forgets basic grammar while trying to learn Python!).
- **PEFT:** You **FREEZE** all 70 Billion original weights. You inject a tiny amount of *new* weights (e.g., 5 Million parameters) into the model. During backpropagation, you only calculate gradients for the 5 Million new weights! 

### 2. The PEFT Taxonomy
There are many ways to inject new weights into a frozen model:
- **Prompt Tuning:** You add 10 "Virtual Tokens" to the user's prompt. You freeze the model, and *only train the embeddings of those 10 tokens!* The tokens mathematically warp the prompt to force the LLM to behave differently.
- **Prefix Tuning:** Instead of virtual tokens at the input, you inject learnable tensors directly into the Key and Value matrices of every Attention layer.
- **Adapters (Houlsby et al.):** You insert a tiny "Bottleneck" MLP layer in between the massive frozen Transformer layers.

### 3. The Bottleneck Adapter Math
How does an Adapter layer save so much memory? It uses a **Bottleneck Architecture**.
Let's look at the math for a LLaMA layer with a dimension of `4096`. 
- If you trained a standard Linear layer, the weight matrix is $4096 \times 4096 = 16.7 \text{ Million}$ parameters.
- **The Bottleneck:** The Adapter projects the 4096 vector down to a tiny dimension (e.g., $r=64$). It then projects it back up to 4096!
- **The Savings:** The math becomes: $(4096 \times 64) + (64 \times 4096) = 524,288$ parameters. 
You achieve the exact same dimensional output, but you only have to train $500\text{k}$ parameters instead of $16.7\text{ Million}$! This fits easily on a cheap GPU!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Bottleneck Adapter Layer from scratch in pure PyTorch! We will inject it into a frozen mock Transformer layer and prove that only the Adapter updates during training.

Create a file named `peft_adapters.py`:

```python
import torch
import torch.nn as nn
import torch.optim as optim

class BottleneckAdapter(nn.Module):
    """
    A tiny Neural Network inserted into a frozen LLM.
    Projects down to a small bottleneck, runs an activation, and projects back up.
    """
    def __init__(self, d_model=4096, bottleneck_dim=64):
        super().__init__()
        # Down-projection (e.g., 4096 -> 64)
        self.down_proj = nn.Linear(d_model, bottleneck_dim)
        self.activation = nn.ReLU() # Or GELU/Swish
        # Up-projection (e.g., 64 -> 4096)
        self.up_proj = nn.Linear(bottleneck_dim, d_model)
        
    def forward(self, x):
        # We use a residual connection so the original LLM signal isn't destroyed!
        adapter_output = self.up_proj(self.activation(self.down_proj(x)))
        return x + adapter_output

class MockFrozenTransformerLayer(nn.Module):
    """A standard LLM layer (Attention + FFN)"""
    def __init__(self, d_model=4096):
        super().__init__()
        # The massive pre-trained weights
        self.ffn = nn.Linear(d_model, d_model)
        
        # WE INJECT THE ADAPTER HERE!
        self.adapter = BottleneckAdapter(d_model, bottleneck_dim=64)
        
    def forward(self, x):
        # Pass through the massive FFN
        x = self.ffn(x)
        # Pass through our tiny learnable Adapter
        x = self.adapter(x)
        return x

def test_peft():
    print("--- RUNNING PARAMETER-EFFICIENT FINE-TUNING (PEFT) ---")
    
    # 1. Initialize the massive LLM layer
    model = MockFrozenTransformerLayer(d_model=4096)
    
    # 2. THE MOST IMPORTANT STEP: Freeze the base model!
    print("Freezing the base model weights...")
    for name, param in model.named_parameters():
        # If it's the massive FFN, freeze it (requires_grad = False)
        if "ffn" in name:
            param.requires_grad = False
        # If it's our tiny adapter, UNFREEZE IT!
        elif "adapter" in name:
            param.requires_grad = True
            
    # 3. Print Trainable Parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"\nTotal Parameters: {total_params:,}")
    print(f"Trainable Parameters (Adapter): {trainable_params:,}")
    print(f"Percentage Trainable: {(trainable_params / total_params) * 100:.2f}%\n")
    
    # 4. Prove that it works
    optimizer = optim.Adam(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-3)
    criterion = nn.MSELoss()
    
    inputs = torch.randn(1, 4096)
    targets = torch.randn(1, 4096)
    
    # Save the original frozen weights to prove they don't change
    original_ffn_weight = model.ffn.weight.clone()
    
    print("Training for 1 step...")
    outputs = model(inputs)
    loss = criterion(outputs, targets)
    loss.backward()
    optimizer.step()
    
    # Verification!
    ffn_changed = not torch.equal(model.ffn.weight, original_ffn_weight)
    
    print(f"\nDid the massive FFN weights change? {ffn_changed} (It remained frozen!)")
    print(f"Did the Adapter weights receive gradients? {model.adapter.down_proj.weight.grad is not None} (It learned!)")
    print("\nWe successfully fine-tuned the model using almost zero VRAM!")

if __name__ == "__main__":
    test_peft()
```

### Key Takeaways from Code:
1. **The Residual Connection:** Notice `return x + adapter_output`. We add the adapter output to the original signal. This guarantees that at Initialization, the Adapter doesn't destroy the LLaMA model's pre-trained knowledge.
2. **The Optimizer Filter:** Notice `filter(lambda p: p.requires_grad, model.parameters())`. If you pass the frozen parameters into Adam, PyTorch will crash or waste memory trying to track momentum for them. You must explicitly tell the optimizer to *only* track the adapter!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: HuggingFace PEFT
Writing adapters from scratch is fun, but production engineering relies on libraries.
**Your Task:**
1. Read the documentation for the HuggingFace `peft` library.
2. Conceptually understand how you can wrap *any* HuggingFace model with `get_peft_model(model, config)`.
3. The library automatically injects the adapters, freezes the base weights, and prepares the model for `Trainer` without you having to write the `.requires_grad = False` loop!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your enterprise has one massive 70B foundational model. You need to serve 50 different fine-tuned variations of this model for 50 different clients. Compare Full Fine-Tuning vs Adapters regarding training cost, storage, and Serving Infrastructure."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Storage Cost:** 
   - State that Full Fine-Tuning creates 50 different 140GB models. You would need $50 \times 140\text{GB} = 7 \text{ Terabytes}$ of storage. 
   - With Adapters, you save one 140GB Base Model, and 50 tiny 10MB adapter files. The total storage is 140.5 GB!
2. **Serving Infrastructure (Multi-Tenant Routing):**
   - Explain the absolute magic of Adapters in production (using a framework like vLLM or LoRAX). 
   - Instead of spinning up 50 separate A100 instances (costing millions), you spin up ONE massive instance hosting the frozen Base Model. 
   - When Request A comes from Client 1, the router dynamically attaches Adapter #1 to the base model *for that specific batch*. When Request B comes from Client 2 in the same millisecond, the router dynamically attaches Adapter #2. You serve 50 clients simultaneously on a single GPU cluster!

---
**Task for the end of the day:** Commit your code to Git. 

You have mastered the foundation of PEFT. But the "Bottleneck Adapter" we built today is considered old technology. It adds latency during inference because it adds extra layers to the neural network.

Tomorrow, in **Day 97**, we learn the greatest breakthrough in AI fine-tuning history: **LoRA (Low-Rank Adaptation)**! We will use SVD matrix math to fine-tune without adding any inference latency!
