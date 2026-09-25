# Day 93: Distributed Training (FSDP, Tensor Parallelism)

Welcome to Day 93. We have a 70 Billion parameter architecture and 15 Trillion tokens of data. 
There is just one problem: **A 70B model requires 140 Gigabytes of VRAM just to load the weights.** An NVIDIA A100 GPU only has 80GB. The model physically cannot fit on the hardware.

Today, we learn the hardcore DevOps and Distributed Systems engineering required to shatter a model across 256 GPUs and train it simultaneously.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Data Parallelism (DDP)
If the model *does* fit on 1 GPU (e.g., a 7B model), you use Distributed Data Parallel (DDP).
- You literally copy the exact same 7B model onto 8 different GPUs.
- You have a batch of 800 images. You split it: GPU 1 gets 100 images. GPU 2 gets 100 images.
- All 8 GPUs do the forward pass and backward pass independently.
- At the end of the step, they communicate over the network (`All-Reduce`), average their gradients together, and update their weights identically. 

### 2. Fully Sharded Data Parallel (FSDP / ZeRO-3)
What if the model doesn't fit on 1 GPU? We must use DeepSpeed ZeRO-3 (or PyTorch FSDP).
FSDP mathematically shatters the model's weights, gradients, and optimizer states across the cluster.
- **The Setup:** GPU 1 holds Layer 1. GPU 2 holds Layer 2. GPU 3 holds Layer 3. 
- **The Forward Pass:** When the data hits Layer 1, GPU 1 calculates the math. When it's time for Layer 2, GPU 2 sends its weights over the network to GPU 1! GPU 1 calculates the math, and *instantly deletes* Layer 2 from its RAM to save space!
They pass the shattered shards back and forth across the network. It allows infinite model scaling, but requires massive network bandwidth.

### 3. Tensor Parallelism (TP)
For models >70B parameters, passing entire layers across the network causes massive latency. We use **Tensor Parallelism (Megatron-LM)**.
Instead of splitting the *layers*, we physically shatter the $W$ matrix of a *single linear layer*!
- GPU 1 calculates the left half of the matrix multiplication. 
- GPU 2 calculates the right half of the matrix multiplication simultaneously.
- They combine the output using an instantaneous `All-Reduce` operation!

### 4. Pipeline Parallelism (PP)
- GPU 1 holds Layers 1-10. GPU 2 holds Layers 11-20. 
- GPU 1 computes the data, sends the intermediate tensor to GPU 2, and then goes to sleep waiting for GPU 2 to finish. 
- **The Pipeline Bubble:** GPUs sleeping is a waste of money. To fix this, we use Micro-Batches. GPU 1 processes Micro-batch 1, sends it to GPU 2, and immediately starts processing Micro-batch 2 while GPU 2 works on Micro-batch 1!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's write a PyTorch script that implements FSDP. We will simulate wrapping a massive model so that PyTorch automatically shatters it across available GPUs.

*(Note: This code requires a multi-GPU environment to execute properly, but the logic is critical to understand).*

Create a file named `distributed_fsdp.py`:

```python
import torch
import torch.nn as nn
import torch.optim as optim
import os
import torch.distributed as dist

# Import the FSDP wrapper
from torch.distributed.fsdp import FullyShardedDataParallel as FSDP
from torch.distributed.fsdp.fully_sharded_data_parallel import CPUOffload

class MassiveMockModel(nn.Module):
    """A mock model that is 'too big' for one GPU"""
    def __init__(self):
        super().__init__()
        # Simulating massive linear layers
        self.layer1 = nn.Linear(10000, 10000)
        self.relu = nn.ReLU()
        self.layer2 = nn.Linear(10000, 10000)
        
    def forward(self, x):
        x = self.layer1(x)
        x = self.relu(x)
        return self.layer2(x)

def setup_distributed():
    """Initializes the distributed process group (NCCL Backend for NVIDIA GPUs)"""
    # These environment variables are usually set automatically by `torchrun`
    os.environ['MASTER_ADDR'] = 'localhost'
    os.environ['MASTER_PORT'] = '12355'
    
    # NCCL is the NVIDIA Collective Communications Library
    dist.init_process_group("nccl")
    
    # Get the local GPU ID assigned to this specific process
    local_rank = int(os.environ.get("LOCAL_RANK", 0))
    torch.cuda.set_device(local_rank)
    return local_rank

def train_fsdp():
    print("--- RUNNING FULLY SHARDED DATA PARALLEL (FSDP) ---")
    
    # 1. Setup Distributed Environment
    try:
        local_rank = setup_distributed()
    except Exception as e:
        print("Note: This script requires `torchrun` and multiple GPUs. Running mock logic.")
        local_rank = 0
        
    # 2. Instantiate the model on CPU first (so we don't OOM the GPU instantly)
    model = MassiveMockModel()
    
    # 3. THE MAGIC: Wrap the model in FSDP!
    # FSDP will automatically shatter the weights and move the shards to the correct GPUs
    # CPUOffload: If even the shattered shards are too big, it offloads optimizer states to system RAM!
    fsdp_model = FSDP(
        model,
        device_id=local_rank,
        cpu_offload=CPUOffload(offload_params=True)
    )
    
    # 4. Standard PyTorch Training Loop
    optimizer = optim.AdamW(fsdp_model.parameters(), lr=1e-3)
    criterion = nn.MSELoss()
    
    # Mock data
    inputs = torch.randn(32, 10000).to(local_rank)
    targets = torch.randn(32, 10000).to(local_rank)
    
    print("Executing Forward Pass... (FSDP is passing shards over the network!)")
    outputs = fsdp_model(inputs)
    
    loss = criterion(outputs, targets)
    
    print("Executing Backward Pass... (FSDP is aggregating gradients!)")
    loss.backward()
    
    optimizer.step()
    print("Step Complete! The massive model trained successfully without OOMing.")
    
    # Cleanup
    if dist.is_initialized():
        dist.destroy_process_group()

if __name__ == "__main__":
    train_fsdp()
```

### Key Takeaways from Code:
1. **The `torchrun` Launcher:** You do not run this script with `python script.py`. You run it with `torchrun --nproc_per_node=8 script.py`. PyTorch physically spawns 8 separate Python processes, one for each GPU!
2. **CPU Offload:** If you are a broke startup with only 1 GPU, you can use FSDP with `CPUOffload=True`. PyTorch will store the massive 70B model in your computer's standard CPU RAM (which is cheap), and only stream the specific layer it needs into the GPU for the math! It is slow, but it prevents OOM crashes.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Memory Math
**Your Task:**
1. Calculate the exact VRAM required to train a 70 Billion parameter model using FP32 (4 bytes per parameter) and the AdamW optimizer.
2. **Weights:** $70\text{B} \times 4\text{ bytes}$
3. **Gradients:** $70\text{B} \times 4\text{ bytes}$
4. **AdamW Optimizer States:** AdamW requires saving the *momentum* and the *variance* for every parameter. That is 2 extra matrices! $(70\text{B} \times 4) + (70\text{B} \times 4)$.
5. Add them all up. You will see why FSDP is mandatory for modern <abbr title="Artificial Intelligence">AI</abbr>.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You need to train a massive 175B parameter model on a cluster of 256 A100-80GB GPUs. Design the parallelism strategy (Data, Tensor, Pipeline) and explain how you minimize network communication overhead."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Network Topology Constraint:** 
   - State that network speeds *inside* a single server (NVLink, 600 GB/s) are 10x faster than speeds *between* servers (InfiniBand/RoCE, 50 GB/s). You must map your parallelism to the physical hardware!
2. **Tensor Parallelism (Intra-Node):**
   - Propose using **Tensor Parallelism (TP=8)**. Because TP requires instantaneous `All-Reduce` summation after every single layer, you can *only* run it across the 8 GPUs physically locked inside the same server via NVLink. If you run TP across servers, the network latency halts the training.
3. **Pipeline Parallelism (Inter-Node):**
   - Propose using **Pipeline Parallelism (PP=4)** across the servers. Server 1 computes Layers 1-20, then transmits a tiny activation tensor to Server 2 over the slower InfiniBand network. This minimizes cross-server communication!
4. **Data Parallelism (The Rest):**
   - With TP=8 and PP=4, a single replica of the model consumes 32 GPUs. Because you have 256 GPUs, you use **Data Parallelism (DP=8)** to replicate that 32-GPU pipeline 8 times to process massive batches of data!

---
**Task for the end of the day:** Commit your code to Git. 

FSDP solves the multi-GPU problem. But GPUs are $40,000 each. What if we could mathematically optimize the training so we only needed half the GPUs?

Tomorrow, in **Day 94**, we master the holy trinity of GPU poverty: **Mixed Precision (BF16), Gradient Accumulation, and Gradient Checkpointing**!
