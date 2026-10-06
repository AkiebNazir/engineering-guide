# Day 95: Training Infrastructure (NCCL & Checkpoints)

Welcome to Day 95. Training LLaMA 3 took 24,000 GPUs running continuously for months. 

In a cluster that large, hardware fails every single day. A GPU overheats. A PCIe lane corrupts. An InfiniBand cable drops. 
If you don't build fault-tolerant infrastructure, your 24,000 GPUs will sit idle while you sleep, wasting hundreds of thousands of dollars. 
Today, we master GPU Networking and Asynchronous Checkpointing.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Network Topology (NVLink vs InfiniBand)
When shattering models across 256 GPUs, the network is the bottleneck.
- **Intra-Node (Inside the box):** A standard AI server has 8 GPUs. They are physically wired together using **NVLink** (or NVSwitch). This connection is incredibly fast (~600 GB/s).
- **Inter-Node (Between boxes):** To connect Server 1 to Server 2, you use networking cables (InfiniBand or Ethernet RoCE). This is much slower (~50 GB/s).
*Rule of thumb: You must design your parallelism so that the heaviest network traffic (like Tensor Parallelism) stays strictly inside the NVLink boundary!*

### 2. NCCL & Ring All-Reduce
When the 8 GPUs finish calculating their gradients, they must average them together. 
If 7 GPUs try to send their gradients to GPU 0 at the exact same millisecond, GPU 0's network card will physically bottleneck and the system will freeze.
NVIDIA solved this with **NCCL** (NVIDIA Collective Communications Library). It uses the **Ring All-Reduce** algorithm.
- The GPUs form a logical circle.
- GPU 1 sends a tiny fraction of its gradients to GPU 2. Simultaneously, GPU 2 sends a fraction to GPU 3.
- The data spins around the ring. This prevents any single GPU from being bottlenecked, maximizing total cluster throughput!

### 3. Asynchronous Checkpointing
If GPU #47 dies on Day 14, the entire training run crashes. You must constantly save the model weights (Checkpointing) so you can resume.
- **The Problem:** Saving a 140GB model to an AWS S3 bucket takes 5 minutes. If you pause training to save it, 24,000 GPUs sit idle for 5 minutes. You just wasted $1,000 of compute to save a file.
- **The Solution:** Asynchronous Checkpointing. The GPU instantly copies the weights into the cheap CPU System RAM (takes 2 seconds). The GPU immediately resumes training the next batch! Meanwhile, a background Python Thread slowly uploads the CPU RAM data to S3 over the next 5 minutes without interrupting the GPUs!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Fault-Tolerant PyTorch training loop. We will implement Async Checkpoint saving, and most importantly, robust **Resumption Logic**.

Create a file named `fault_tolerance.py`:

```python
import torch
import torch.nn as nn
import torch.optim as optim
import threading
import time
import os

class MockModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.fc = nn.Linear(10, 10)
    def forward(self, x):
        return self.fc(x)

def async_save_checkpoint(state_dict, filename):
    """
    Simulates saving a massive 140GB file to S3.
    This runs in a separate thread so the GPU doesn't have to wait!
    """
    print(f"\n[Background Thread] Started uploading {filename} to S3...")
    time.sleep(3) # Simulate slow network upload
    torch.save(state_dict, filename)
    print(f"[Background Thread] Finished uploading {filename}!\n")

def robust_training_loop():
    print("--- RUNNING FAULT-TOLERANT TRAINING LOOP ---")
    
    model = MockModel()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    
    # We must also save the LR Scheduler and the Random Number Generator state!
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=10, gamma=0.1)
    
    start_step = 0
    checkpoint_file = "latest_checkpoint.pt"
    
    # 1. ROBUST RESUMPTION LOGIC
    # If the script crashes and is restarted, it will automatically resume here!
    if os.path.exists(checkpoint_file):
        print(f"CRASH DETECTED! Found {checkpoint_file}. Resuming training...")
        checkpoint = torch.load(checkpoint_file)
        
        # Restore EVERYTHING, not just the model weights!
        model.load_state_dict(checkpoint['model_state'])
        optimizer.load_state_dict(checkpoint['optimizer_state'])
        scheduler.load_state_dict(checkpoint['scheduler_state'])
        torch.set_rng_state(checkpoint['rng_state']) # CRITICAL for data shuffling consistency!
        
        start_step = checkpoint['step'] + 1
        print(f"Successfully restored all states. Resuming at Step {start_step}.\n")
    else:
        print("Starting fresh training run from Step 0.\n")

    # 2. THE TRAINING LOOP
    TOTAL_STEPS = 5
    
    for step in range(start_step, TOTAL_STEPS):
        print(f"Training Step {step} on GPU...")
        
        # Mock Forward/Backward pass
        inputs = torch.randn(2, 10)
        loss = model(inputs).sum()
        loss.backward()
        optimizer.step()
        scheduler.step()
        
        time.sleep(1) # Simulate math time
        
        # 3. ASYNC CHECKPOINTING
        if step % 2 == 0: # Save every 2 steps
            print(f"Triggering Async Checkpoint at Step {step}...")
            
            # Extract states to CPU memory instantly
            state_to_save = {
                'step': step,
                'model_state': model.state_dict(),
                'optimizer_state': optimizer.state_dict(),
                'scheduler_state': scheduler.state_dict(),
                'rng_state': torch.get_rng_state()
            }
            
            # Fire the background thread and IMMEDIATELY continue the loop!
            t = threading.Thread(target=async_save_checkpoint, args=(state_to_save, checkpoint_file))
            t.start()
            
    print("Training Complete!")

if __name__ == "__main__":
    robust_training_loop()
```

### Key Takeaways from Code:
1. **The RNG State:** The most common mistake juniors make when resuming a checkpoint is forgetting to save the `rng_state`. If you don't save the Random Number Generator state, PyTorch resets the dataloader's random seed. You will accidentally train the model on the exact same 10 million images you trained on yesterday!
2. **The Async Thread:** Notice how the `Training Step` loop continues printing *while* the `[Background Thread]` is sleeping. The GPU never paused!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: PyTorch Elastic (`torchrun`)
In the old days, if you started a run with 256 GPUs, and 1 GPU died, the other 255 GPUs would crash immediately because NCCL lost a node.
**Your Task:**
1. Research PyTorch Elastic (`torchrun` and `torchelastic`).
2. Conceptually understand how it uses a **Rendezvous Backend** (like etcd). 
3. When a node dies, Elastic automatically pauses the training, detects that the cluster now has 248 GPUs, mathematically re-shards the FSDP layers for 248 GPUs, and seamlessly resumes the training without human intervention!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your 128-GPU training run crashes at step 50,000 due to a hardware failure. Describe your recovery strategy. How do you prevent data loss, and how do you ensure the model convergence doesn't spike or degrade after resuming?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Infrastructure Recovery:** 
   - State that Kubernetes or Slurm will automatically detect the dead node, cordon it, provision a new node, and restart the `torchrun` elastic script.
2. **The State Restoration:**
   - Explicitly list the 4 things that must be loaded from the S3 checkpoint: Model Weights, Optimizer States (Adam momentum), LR Scheduler step, and the RNG state for the dataloader.
3. **The Loss Spike Prevention (Warmup):**
   - Explain that even with perfect resumption, network topology changes or minor numerical variations can cause a massive "Loss Spike" when resuming. 
   - Propose implementing a **Resumption Warmup**: Instead of resuming at the full Learning Rate of $1e-4$, you artificially drop the LR to $1e-5$ and slowly warm it back up to $1e-4$ over 100 steps to let the Adam optimizer stabilize!

---
**Task for the end of the day:** Commit your code to Git. 

We now know how to pre-train a massive foundation model from scratch. 
But what if you are just a developer who wants to fine-tune LLaMA to act like a specific persona? You don't have 256 GPUs. You have one RTX 4090.

Tomorrow, in **Day 96**, we master **Parameter-Efficient Fine-Tuning (PEFT) and Adapter Layers**!
