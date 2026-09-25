# Day 94: Mixed Precision & Memory Optimization

Welcome to Day 94. Distributing a model across 256 GPUs works, but what if you don't have \$10 Million to buy a cluster? 
If we can mathematically optimize the training loop to use less <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr>, we can train massive models on fewer GPUs.

Today, we master the "Holy Trinity of GPU Poverty": **Mixed Precision (BF16), Gradient Accumulation, and Activation Checkpointing**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Mixed Precision (FP32 vs FP16 vs BF16)
By default, PyTorch initializes all neural networks in **FP32** (32-bit Floating Point). Every single number requires 4 bytes of memory.
But neural networks don't actually need 32 decimals of precision to learn. 
- If we convert the model to **FP16** (16-bit), we instantly cut the memory footprint in exactly half!
- **The Underflow Problem:** Standard FP16 has a massive flaw. It only supports exponents up to $10^{-5}$. During training, gradients get extremely small (e.g., $0.000004$). FP16 rounds this number to exactly $0.0$. The network stops learning! You have to use "Loss Scaling" to multiply the gradients and hack the math.
- **The BF16 Miracle:** Google invented **BFloat16** (Brain Float 16). It is a 16-bit number, but it steals bits from the decimal fraction and gives them to the exponent! It sacrifices decimal precision, but it has the exact same massive exponent range as FP32 ($10^{-38}$). You can train in BF16 natively without any underflow crashes!

### 2. Gradient Accumulation (Simulating Compute)
You have a 24GB consumer GPU. You want to train with a Batch Size of 32, but if you put 32 images on the GPU, you get a CUDA Out-Of-Memory (<abbr title="Out of Memory - An undesired state of computer operation where no additional memory can be allocated for use by programs.">OOM</abbr>) error. Your GPU can only hold 4 images at a time.
**The Fix:** Gradient Accumulation.
1. Run a forward/backward pass with a micro-batch of 4. Calculate the gradients.
2. **DO NOT run `optimizer.step()`!**
3. Run another micro-batch of 4. Add the new gradients to the old gradients.
4. Loop this 8 times. ($4 \times 8 = 32$).
5. Now, run `optimizer.step()`. You just mathematically simulated a batch size of 32 using the <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> required for a batch size of 4!

### 3. Gradient Checkpointing (Trading Compute for Memory)
During the Forward Pass, PyTorch must save all the intermediate activations (the outputs of every layer) into <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> so it can use them for the chain rule during the Backward Pass. For a 100-layer Transformer, these saved activations consume massive amounts of memory.
**The Fix:** Gradient (Activation) Checkpointing.
We simply delete the activations from <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr>! When the backward pass needs them, it literally re-runs the forward pass a second time to recalculate them on the fly!
**The Trade-off:** Training becomes $20\%$ slower (more compute), but it saves $50\%$ to $70\%$ of VRAM, allowing you to fit massive models on cheap GPUs!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's write the Holy Trinity. We will write a PyTorch training loop that implements BF16 Mixed Precision `autocast`, Gradient Accumulation, and Checkpointing.

Create a file named `memory_optimization.py`:

```python
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.checkpoint import checkpoint

class DeepNetwork(nn.Module):
    """A deep network where saving activations would cause OOM."""
    def __init__(self):
        super().__init__()
        # We define layers separately so we can checkpoint them
        self.block1 = nn.Sequential(nn.Linear(4096, 4096), nn.ReLU())
        self.block2 = nn.Sequential(nn.Linear(4096, 4096), nn.ReLU())
        self.block3 = nn.Sequential(nn.Linear(4096, 10))
        
    def forward(self, x):
        # 1. GRADIENT CHECKPOINTING
        # Instead of `x = self.block1(x)`, we use `checkpoint()`.
        # PyTorch will execute block1, but it will NOT save the intermediate activations!
        # During loss.backward(), it will re-run block1 automatically.
        x = checkpoint(self.block1, x, use_reentrant=False)
        x = checkpoint(self.block2, x, use_reentrant=False)
        x = self.block3(x) # We don't checkpoint the final layer
        return x

def test_optimized_training():
    print("--- RUNNING MEMORY OPTIMIZED TRAINING LOOP ---")
    
    # Check if BF16 is supported on this hardware (Ampere GPUs or newer)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    supports_bf16 = torch.cuda.is_available() and torch.cuda.is_bf16_supported()
    dtype = torch.bfloat16 if supports_bf16 else torch.float16
    
    print(f"Using Mixed Precision Dtype: {dtype}")
    
    model = DeepNetwork().to(device)
    optimizer = optim.AdamW(model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()
    
    # 2. GRADIENT ACCUMULATION SETUP
    TARGET_BATCH_SIZE = 32
    MICRO_BATCH_SIZE = 4
    ACCUMULATION_STEPS = TARGET_BATCH_SIZE // MICRO_BATCH_SIZE # 8 steps
    
    print(f"Target Batch: {TARGET_BATCH_SIZE} | Micro Batch: {MICRO_BATCH_SIZE} | Accumulation Steps: {ACCUMULATION_STEPS}\n")
    
    # Simulate a training loop with 16 total micro-batches
    for step in range(1, 17):
        inputs = torch.randn(MICRO_BATCH_SIZE, 4096).to(device)
        targets = torch.randn(MICRO_BATCH_SIZE, 10).to(device)
        
        # 3. MIXED PRECISION (AUTOCAST)
        # We tell PyTorch to automatically downcast linear layers to BF16 for speed/memory,
        # but keep sensitive operations (like Softmax or Loss) in FP32!
        with torch.autocast(device_type=device.type, dtype=dtype):
            outputs = model(inputs)
            loss = criterion(outputs, targets)
            
        # We must divide the loss by the accumulation steps so the gradients scale correctly!
        loss = loss / ACCUMULATION_STEPS
        
        # Backward pass (Calculates gradients and ADDS them to existing gradients)
        loss.backward()
        
        print(f"Micro-batch {step} completed. Gradients accumulated.")
        
        # 4. APPLY THE ACCUMULATED GRADIENTS
        if step % ACCUMULATION_STEPS == 0:
            print(f"-> Step {step}: Reached {TARGET_BATCH_SIZE} simulated items! Updating weights!")
            
            # Step the optimizer
            optimizer.step()
            
            # ZERO the gradients to start the next accumulation cycle!
            optimizer.zero_grad()
            
            print("-" * 50)

if __name__ == "__main__":
    test_optimized_training()
```

### Key Takeaways from Code:
1. **The `autocast` Context Manager:** You don't have to manually convert your model to `.half()`. `torch.autocast` is brilliant—it automatically runs computationally heavy matrix multiplications in BF16, but if you call `torch.exp()` (which requires high precision), it automatically runs it in FP32! This is why it is called *Mixed* Precision.
2. **Dividing the Loss:** Notice `loss = loss / ACCUMULATION_STEPS`. If you don't do this, adding 8 batches of gradients together will result in a gradient 8x larger than normal. Your learning rate will effectively multiply by 8 and your model will explode!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Gradient Scaler (FP16 Underflow)
If your GPU is an older T4 or V100, it doesn't support BF16. You must use FP16.
**Your Task:**
1. Conceptually implement `torch.cuda.amp.GradScaler`.
2. Wrap the forward pass in `autocast(dtype=torch.float16)`.
3. Instead of `loss.backward()`, use `scaler.scale(loss).backward()`. This multiplies the tiny loss by a massive number (like 65,000) so the gradients don't Underflow to 0!
4. Instead of `optimizer.step()`, use `scaler.step(optimizer)`. The scaler automatically divides the gradients back down to normal size before applying them!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your training run crashes with a CUDA Out-Of-Memory error on the backward pass, even with a batch size of 1. You cannot use a smaller model. Walk through the exact memory optimization techniques you would apply, in order of preference, to force the model to fit."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Step 1: Mixed Precision (Free VRAM):** 
   - State that you will immediately enable BF16 Autocast. This cuts the activation memory in half with absolutely zero compute penalty (it actually speeds up the GPU via Tensor Cores).
2. **Step 2: Gradient Checkpointing (Compute Trade-off):**
   - If it still OOMs, enable Gradient Checkpointing. Explain that you will trade $20\%$ slower training time for a massive $50\%$ reduction in VRAM by dropping the forward activations.
3. **Step 3: Paged Optimizers / <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> Offload (The Last Resort):**
   - If the model is so massive that the AdamW optimizer states crash the GPU, implement **DeepSpeed ZeRO-Offload** (or FSDP CPUOffload). 
   - Acknowledge the severe trade-off: Offloading states to <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> requires sending data over the PCIe bus, which is a massive bottleneck and will slow training down significantly.

---
**Task for the end of the day:** Commit your code to Git. 

We now know how to train across 256 GPUs, and we know how to squeeze maximum efficiency out of them. But what happens when GPU #47 suddenly catches fire and dies halfway through a 3-month training run? 

Tomorrow, in **Day 95**, we master **Training Infrastructure, NCCL Networking, and Fault-Tolerant Checkpointing**!
