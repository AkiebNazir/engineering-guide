# Day 154: GPU Cluster Management (Tensor & Pipeline Parallelism)

Welcome to Day 154.

Yesterday, we built a beautiful <abbr title="Application Programming Interface">API</abbr> Gateway to handle incoming traffic. But if a user requests a generation from a massive 70B or 405B parameter model, your Gateway must forward that request to a massive GPU Cluster.
A 70B model in 16-bit precision requires 140GB of VRAM just to store the weights. The largest single GPU on Earth (the NVIDIA H100) only has 80GB of VRAM.

**It is physically impossible to load a 70B model onto a single GPU.**

Today, we learn how to slice LLMs into pieces and spread them across massive GPU clusters using **Tensor Parallelism** and **Pipeline Parallelism**, connected by high-speed InfiniBand networking.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Tensor Parallelism (TP)
*Analogy:* Imagine you have a massive math problem: $A \times B$. It's too big for one person to solve. So, you cut the matrix $A$ in half vertically. You give the left half to Worker 1, and the right half to Worker 2. They both do their math at the exact same time, shout their answers to each other across the room, and sum it up to get the final answer.

**Tensor Parallelism (TP)** splits the actual weight matrices of individual Neural Network layers across multiple GPUs.
- **Pros:** It heavily reduces memory per GPU and drastically increases throughput (because 4 GPUs are computing the layer simultaneously).
- **Cons:** The GPUs must communicate with each other *constantly* (after almost every matrix multiplication). If they are on different physical servers, the network lag will destroy your speed. TP is generally restricted to GPUs physically connected inside the same server via **NVLink** (NVIDIA's massive bandwidth physical bridge).

### 2. Pipeline Parallelism (PP)
*Analogy:* An assembly line. Worker 1 builds the chassis and hands it to Worker 2. Worker 2 adds the engine and hands it to Worker 3.

**Pipeline Parallelism (PP)** splits the model by layers. If a model has 80 Transformer layers, GPU 1 gets layers 1-20. GPU 2 gets 21-40. 
- **Pros:** The GPUs only need to communicate once (when GPU 1 finishes layer 20 and passes the hidden state to GPU 2). Therefore, PP works brilliantly *across different physical servers* connected by standard networking (InfiniBand/RDMA).
- **Cons:** While GPU 1 is processing layer 1, GPUs 2, 3, and 4 are sitting completely idle waiting for the data! This is called the "Pipeline Bubble." 

### 3. Combining 3D Parallelism
To train or serve massive models (like GPT-4), MAANG companies combine three strategies:
1. **Tensor Parallelism (TP=8):** Split layers across 8 GPUs inside a single physical server (node).
2. **Pipeline Parallelism (PP=4):** String 4 physical servers together, passing the computation down the line.
3. **Data Parallelism (DP=10):** Clone that entire 32-GPU setup 10 times, so you can serve 10 different users at once.

### 4. CUDA Graphs
When running TP, the CPU must send thousands of tiny instructions ("Kernels") to the GPUs. For fast models, the CPU is too slow to send these instructions, causing the GPU to wait.
**CUDA Graphs** record the entire sequence of GPU instructions *once*, and then replay them instantly from the GPU's own memory, completely bypassing the CPU overhead!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

We cannot physically rent 8 A100 GPUs for a quick code-along. However, vLLM makes deploying a model across a multi-GPU cluster incredibly simple via the command line.

We will simulate how an <abbr title="Machine Learning">ML</abbr> Engineer deploys a 70B model using Tensor Parallelism across 4 GPUs, and how to verify the GPU topology.

*(Note: To run this exactly, you need a multi-GPU machine. Otherwise, study the conceptual workflow.)*

### Step 1: Checking GPU Topology
Before slicing a model, you must ensure your GPUs can talk to each other fast enough.

```bash
# Command to view GPU status and VRAM usage
nvidia-smi

# Command to view the physical interconnects between GPUs
nvidia-smi topo -m
```
If the topo output says `NVLink`, your GPUs are connected by massive physical bridges (hundreds of GB/s). Tensor Parallelism will be lightning fast. If it says `PHB` or `PIX`, they are connected via the motherboard PCIe bus. TP will be significantly slower.

### Step 2: Deploying with vLLM (Tensor Parallelism)
If we have a node with 4x 40GB A100 GPUs, we can load a 140GB model by splitting it using `--tensor-parallel-size`.

```bash
# The magic of vLLM! 
# We tell it to split the model weights across 4 GPUs.
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Meta-Llama-3-70B-Instruct \
    --tensor-parallel-size 4 \
    --enforce-eager False  # This ENABLES CUDA Graphs for maximum speed!
```
Under the hood, vLLM automatically invokes **Ray** (a distributed computing framework) or **PyTorch NCCL** to spawn 4 processes, shard the model weights, place a quarter of the model on each GPU VRAM, and orchestrate the matrix multiplications.

### Step 3: Integrating with the Python Client
Once the massive cluster is running on port 8000, your code doesn't change at all! The <abbr title="Application Programming Interface">API</abbr> Gateway we built on Day 153 just forwards standard HTTP requests to it.

```python
import openai
import time

# Point to our massive multi-GPU vLLM cluster!
client = openai.OpenAI(
    api_key="empty",
    base_url="http://localhost:8000/v1"
)

print("[SYSTEM] Querying the 70B Tensor-Parallel Cluster...")
start = time.time()

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3-70B-Instruct",
    messages=[{"role": "user", "content": "Explain the concept of Tensor Parallelism."}],
    stream=False
)

print(f"Time: {time.time() - start:.2f}s")
print(response.choices[0].message.content)
```

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
You have rented an AWS `p4d.24xlarge` instance. It contains 8x A100-40GB GPUs (320GB Total VRAM).
You need to serve the Llama-3-70B model (140GB VRAM required).
**Task:** Should you set `--tensor-parallel-size 8`? Or is there a more efficient way to utilize these 8 GPUs to maximize user throughput? 
*(Hint: Think about deploying multiple vLLM engines on the same node).*

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"You have a massive cluster of 32 A100-80GB GPUs. You need to serve three models for your company: an 8B model for fast routing, a 70B model for coding, and a massive 405B model for complex reasoning. How do you allocate the GPUs to ensure no system crashes and SLAs are met?"*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The 405B Model:** An FP16 405B model requires ~800GB of VRAM. A single 8-GPU server (8x80=640GB) cannot hold it! We must use **Pipeline Parallelism** across 2 physical servers (16 GPUs total), with **Tensor Parallelism=8** inside each server.
2. **The 70B Model:** Requires ~140GB VRAM. We allocate one 8-GPU server. However, instead of TP=8 (which has diminishing returns and high communication overhead), we split the server into two groups. We run one replica of the 70B model on GPUs 0-3 (TP=4) and a second replica on GPUs 4-7 (TP=4). We put a load balancer in front of them to double our concurrent throughput.
3. **The 8B Model:** Requires ~16GB VRAM. We allocate the final 8-GPU server. We do NOT use Tensor Parallelism. We run 8 independent instances of the model (one on each GPU) to handle massive, lightning-fast parallel routing traffic.

---
**Task for the end of the day:** Research **Ray**, the distributed computing framework created by Anyscale. It is the backbone of vLLM's multi-GPU orchestration.

Tomorrow, in **Day 155**, we look at the opposite of massive GPU clusters: **Edge Deployment.** We will learn how to shrink models down so they run entirely offline on an iPhone or a Macbook using `llama.cpp` and `MLX`!
