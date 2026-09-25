# Day 151: LLM Serving Fundamentals (vLLM, TGI, TensorRT-LLM)

Welcome to Day 151! 

We are officially entering **Phase 6: Production LLMOps & System Design.** 
Until now, we have relied on external APIs (like OpenAI) or simple local scripts (like `transformers.pipeline`) to run models. 

If you are an <abbr title="Artificial Intelligence">AI</abbr> Engineer at a modern startup, you cannot send sensitive proprietary data to OpenAI. You must host your own open-source models (like Llama-3). But if you try to use standard PyTorch `pipeline` to serve 10,000 concurrent users, your server will instantly crash with an Out-Of-Memory (<abbr title="Out of Memory - An undesired state of computer operation where no additional memory can be allocated for use by programs.">OOM</abbr>) error.

Today, we learn **Production <abbr title="Large Language Model">LLM</abbr> Serving**. We will learn the physics of memory-bound inference, and the revolutionary frameworks (vLLM, TGI) that make massive scale possible.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Inference Bottleneck: Memory vs. Compute
When an <abbr title="Large Language Model">LLM</abbr> generates text, there are two distinct phases:
1. **Prefill Phase (Compute-Bound):** The <abbr title="Large Language Model">LLM</abbr> reads the user's prompt (e.g., 1,000 tokens) all at once. This is fast and maxes out the GPU's teraflops.
2. **Decode Phase (Memory-Bound):** The <abbr title="Large Language Model">LLM</abbr> generates the answer token-by-token. For every single token generated, the GPU must fetch the *entire* model weights (e.g., 14GB for a 7B model) from GPU VRAM into the compute cores. This is incredibly slow and constrained by memory bandwidth, not compute power!

### 2. The KV-Cache Problem
During the Decode phase, the <abbr title="Large Language Model">LLM</abbr> must remember the context of all previous tokens. It stores this context in the **Key-Value (KV) Cache**.
If you use standard PyTorch, it pre-allocates a massive contiguous block of VRAM for every user's KV-Cache, guessing how long their generation will be. 
*The result?* 60% to 80% of your $40,000 GPU's memory is completely wasted on empty space!

### 3. The Revolution: PagedAttention (vLLM)
*Analogy:* Imagine a restaurant giving every customer a massive 10-person table just in case their friends show up. Most tables are 80% empty. The restaurant is "full", but serves very few people.
**PagedAttention** (invented by UC Berkeley and used in vLLM) solves this. It divides the KV-cache into tiny "blocks" (like seating people in individual chairs). As a user generates more tokens, vLLM dynamically allocates new blocks. 
*The result?* Memory waste drops from 80% to 4%. You can suddenly serve 100 concurrent users on a single GPU instead of 5!

### 4. Continuous Batching
Standard batching forces all users to wait until the longest response finishes.
**Continuous Batching** (dynamic batching) constantly swaps requests in and out of the GPU at the token level. The millisecond User A finishes their generation, User C is injected into the batch.

### 5. The Big Three Serving Engines
1. **vLLM:** The open-source king. Best throughput, easiest to use, powered by PagedAttention.
2. **TGI (Text Generation Inference):** Built by Hugging Face. Excellent integration with the HF Hub.
3. **TensorRT-<abbr title="Large Language Model">LLM</abbr>:** Built by NVIDIA. The absolute fastest engine on Earth, but extremely difficult to compile and use.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's look at the difference between naive PyTorch inference and production vLLM serving. 

*(Note: To run this code, you would need a Linux machine with an NVIDIA GPU and `pip install vllm transformers`)*

### Part 1: The Naive Way (Do Not Use in Production)
```python
# naive_serving.py
from transformers import AutoModelForCausalLM, AutoTokenizer
import time

model_id = "meta-llama/Meta-Llama-3-8B-Instruct"

print("Loading massive model into VRAM... (This takes minutes)")
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id, device_map="auto")

prompts = ["Tell me a story about a brave knight.", "Explain quantum physics."]

start_time = time.time()
inputs = tokenizer(prompts, return_tensors="pt", padding=True).to("cuda")

# This is incredibly inefficient batching. The GPU is wasting memory!
outputs = model.generate(**inputs, max_new_tokens=100)
end_time = time.time()

print(f"Generation took: {end_time - start_time:.2f} seconds")
```

### Part 2: The Production Way (vLLM)

With vLLM, we bypass the standard PyTorch generation loop entirely. We load the model into a highly optimized C++/CUDA runtime engine that automatically implements PagedAttention and Continuous Batching.

```python
# vllm_serving.py
from vllm import LLM, SamplingParams
import time

model_id = "meta-llama/Meta-Llama-3-8B-Instruct"

print("[SYSTEM] Initializing vLLM Engine with PagedAttention...")
# vLLM automatically allocates 90% of your GPU VRAM to the KV-Cache pool!
llm = LLM(
    model=model_id, 
    gpu_memory_utilization=0.90, # How much VRAM to dedicate to the KV-Cache
    max_model_len=4096           # Max context window
)

# 1. Define how we want to sample tokens
sampling_params = SamplingParams(temperature=0.7, max_tokens=100)

prompts = [
    "Tell me a story about a brave knight.", 
    "Explain quantum physics.",
    "Write a poem about the ocean.",
    "How do I cook a steak?"
]

print("[SYSTEM] Executing Generation with Continuous Batching...")
start_time = time.time()

# This looks simple, but under the hood, vLLM is dynamically routing 
# memory blocks and continuously batching the tokens at the Cuda level!
outputs = llm.generate(prompts, sampling_params)

end_time = time.time()

# Print the results and metrics
for output in outputs:
    prompt = output.prompt
    generated_text = output.outputs[0].text
    print(f"Prompt: {prompt[:30]}... -> Output: {generated_text[:30]}...\n")

print(f"Total time for {len(prompts)} concurrent requests: {end_time - start_time:.2f} seconds")
```

### 🔍 Understanding the Metrics

In production, you don't measure "Total Time". You measure three strict metrics:
1. **TTFT (Time To First Token):** How long before the user sees the first word? (Should be < 200ms).
2. **TPOT (Time Per Output Token):** How fast do the words stream in? (Should be ~20-50ms per token, faster than humans can read).
3. **Throughput:** How many total tokens per second is the server outputting across ALL active users? (vLLM maximizes this).

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Deploy vLLM as a true OpenAI-Compatible <abbr title="Application Programming Interface"><abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr></abbr> Server. 
vLLM comes with a built-in FastAPI server that mimics OpenAI perfectly. 
Your challenge: Run the following command in your terminal (if you have a GPU), and then point your Python `openai` client to `http://localhost:8000` instead of `https://api.openai.com`!

```bash
python -m vllm.entrypoints.openai.api_server --model meta-llama/Meta-Llama-3-8B-Instruct
```

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"You need to serve a 70B parameter model with <200ms TTFT and 10,000 concurrent users. Design the complete serving architecture. Why wouldn't you just use standard PyTorch?"*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The PyTorch Flaw:** Explicitly mention the KV-Cache. Explain that PyTorch pre-allocates contiguous memory for the cache, leading to severe memory fragmentation (80% waste), causing <abbr title="Out of Memory - An undesired state of computer operation where no additional memory can be allocated for use by programs.">OOM</abbr> crashes at even 10 concurrent users.
2. **The Software Layer:** Propose using **vLLM** or **TGI** specifically for **PagedAttention** (virtual memory blocks for KV-cache) and **Continuous Batching** (token-level request swapping).
3. **The Hardware Layer:** A 70B model requires ~140GB of VRAM just for weights (in FP16). The candidate must state that a single 80GB A100 GPU cannot hold the model. They must propose using **Tensor Parallelism** across 2x A100 (80GB) or 4x A100 (40GB) GPUs.
4. **The Scaling Layer:** To handle 10,000 users, one machine isn't enough. Propose a Kubernetes cluster with a Load Balancer routing requests to multiple physical nodes, each running an independent vLLM engine.

---
**Task for the end of the day:** Memorize the acronyms **TTFT**, **TPOT**, and **KV-Cache**. 

Tomorrow, in **Day 152**, we will learn how to shrink models down so they fit on cheaper GPUs using **Quantization** (GPTQ, AWQ) and **Prefix Caching**!
