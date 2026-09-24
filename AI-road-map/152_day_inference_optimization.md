# Day 152: Inference Optimization: KV-Cache, Prefix Caching & Quantization

Welcome to Day 152. 

Yesterday, we deployed vLLM to serve an 8B parameter model. An 8B model requires about 16GB of VRAM to run in FP16 (16-bit precision). If you rent an AWS `g5.xlarge` instance (24GB VRAM), this fits perfectly! 
But what if you want to deploy a 70B model? In FP16, a 70B model requires **140GB of VRAM**. A single 24GB GPU won't even load it. An 80GB A100 GPU costs $20,000 and still won't fit it.

Today, we learn the dark arts of **Inference Optimization**. We will learn how to compress models so they fit on cheap GPUs (Quantization) and how to manipulate the KV-Cache to save massive amounts of compute (Prefix Caching).

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Model Quantization (Shrinking the Weights)
*Analogy:* Imagine a recipe book where every ingredient is measured to 16 decimal places (e.g., `1.0000000000000000 cups of flour`). The book is 5,000 pages long. What if we just round the numbers to a whole integer (`1 cup`)? The book shrinks to 500 pages, and the cake still tastes 99% the same!
**Quantization** converts the 16-bit floating-point weights (FP16) of a neural network into 8-bit (INT8) or 4-bit (INT4) integers. 
- A 70B model in FP16 = 140GB VRAM.
- A 70B model in INT4 = 35GB VRAM. (Now it fits on two cheap gaming GPUs!).

**Popular Quantization Formats:**
- **GPTQ & AWQ:** The standard for GPU inference. Highly optimized for serving engines like vLLM.
- **GGUF (llama.cpp):** The standard for CPU and Apple Mac (Metal) inference.
- **FP8:** The new native 8-bit float standard supported natively by NVIDIA H100 GPUs.

### 2. The KV-Cache Formula
If you have a 100,000-token prompt, storing that context requires VRAM.
The formula for KV-Cache memory per token is:
`2 * Layers * Heads * Head_Dim * Bytes_Per_Element`
For a 70B model, processing a massive 32,000 token document might consume **30GB of VRAM just for the cache**, completely independent of the model weights! 

### 3. Prefix Caching (The Compute Saver)
Imagine you have an AI coding assistant. Every time a user asks a question, your system secretly injects a massive 2,000-token System Prompt explaining exactly how the AI should behave.
If 500 users ask a question, your GPU has to process that same 2,000-token System Prompt 500 times, wasting immense compute.
**Prefix Caching** allows vLLM to compute the KV-Cache for the System Prompt *once*, save it in VRAM, and instantly share it with all 500 users! This reduces the Time-To-First-Token (TTFT) from 2 seconds to 50 milliseconds!

### 4. Speculative Decoding
LLMs can only generate 1 token at a time. It is a massive bottleneck.
**Speculative Decoding** uses a tiny, fast "Draft" model (e.g., 1B parameters) to guess the next 5 tokens instantly. The massive "Target" model (e.g., 70B parameters) evaluates all 5 tokens in a single parallel pass. If it agrees, you just generated 5 tokens in the time it usually takes to generate 1!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's load a **Quantized Model** and enable **Prefix Caching** using vLLM to see how we can serve enterprise workloads on cheap hardware.

*(Note: To run this code, you would need `pip install vllm` and a GPU)*

```python
import time
from vllm import LLM, SamplingParams

def run_optimized_inference():
    print("=========================================")
    print("  OPTIMIZED PRODUCTION INFERENCE (vLLM)  ")
    print("=========================================\n")
    
    # --- 1. QUANTIZED MODEL LOADING ---
    print("[SYSTEM] Loading AWQ-Quantized Model into VRAM...")
    # This is a 4-bit quantized version of Llama-3-8B.
    # Instead of 16GB VRAM, it only requires ~5.5GB VRAM!
    quantized_model_id = "casperhansen/llama-3-8b-instruct-awq"
    
    # We enable Prefix Caching in the engine!
    llm = LLM(
        model=quantized_model_id,
        quantization="awq",           # Specify the quantization type
        enable_prefix_caching=True,   # TURN ON PREFIX CACHING!
        gpu_memory_utilization=0.90,
        max_model_len=4096
    )
    
    sampling_params = SamplingParams(temperature=0.0, max_tokens=50)
    
    # --- 2. PREFIX CACHING DEMONSTRATION ---
    
    # Imagine this is a massive 2,000 token System Prompt
    system_prompt = "You are an expert AI. " * 500 
    
    # Two different users ask different questions, but share the exact same System Prompt prefix!
    user_1_prompt = system_prompt + "\n\nUser: Tell me about Jupiter."
    user_2_prompt = system_prompt + "\n\nUser: Tell me about Mars."
    
    print("\n[USER 1] First request (Cold Cache)...")
    start_time = time.time()
    # The GPU has to read all 2,000 tokens of the system prompt and compute the KV-Cache
    outputs_1 = llm.generate([user_1_prompt], sampling_params)
    cold_time = time.time() - start_time
    print(f"Time Taken (Cold): {cold_time:.2f} seconds")
    
    print("\n[USER 2] Second request (Warm Cache / Prefix Hit!)...")
    start_time = time.time()
    # The GPU sees the identical system prompt prefix!
    # It completely skips the 2,000 token prefill computation and just computes the "Mars" part!
    outputs_2 = llm.generate([user_2_prompt], sampling_params)
    warm_time = time.time() - start_time
    print(f"Time Taken (Warm): {warm_time:.2f} seconds")
    
    print("\n--- RESULTS ---")
    print(f"Prefix Caching made the request {cold_time / warm_time:.1f}x faster!")
    print(f"And the AWQ Quantization saved 10GB of VRAM!")

# To run:
# run_optimized_inference()
```

### 🔍 Understanding the Magic

If you ran this script without Prefix Caching, User 2 would take the exact same amount of time as User 1. The GPU would stupidly recompute the 2,000 tokens of the system prompt.
With `enable_prefix_caching=True`, vLLM identifies the matching prefix block in memory, points User 2's request to that exact block, and saves massive amounts of Compute (Teraflops) and memory latency.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Go to the Hugging Face Model Hub. Search for "Llama 3 70B AWQ". Look at the model card and the file sizes. 
Calculate exactly how many 24GB GPUs (like the RTX 3090 or AWS g5) you would need to run the AWQ 4-bit version of the 70B model, versus the unquantized FP16 version.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"You're building an AI Code Editor (like GitHub Copilot). Every time the user types a character, you send their entire 5,000-line code file as the prompt so the LLM has context. The latency is currently 3 seconds per keystroke, which is unacceptable. How do you optimize this?"*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The Root Cause:** Explain that the 3-second latency is entirely due to the **Prefill Phase** of processing the massive 5,000-line prompt on every single keystroke.
2. **The Solution (Prefix Caching):** Implement Prefix Caching on the inference server.
3. **The Workflow:** 
   - Keystroke 1: Sends the 5,000 lines. The server computes the KV-Cache (takes 3s).
   - Keystroke 2: Sends 5,000 lines + 1 new character. The server sees the first 5,000 lines are a perfect prefix match! It grabs the KV-cache from VRAM, and only computes the 1 new character (Prefill takes 10 milliseconds).
4. **Cache Invalidation:** If the user edits line 10, the prefix match is broken at line 10. The cache from line 10 to 5,000 is invalidated and must be recomputed.

---
**Task for the end of the day:** Read up on the difference between GPTQ and AWQ quantization formats.

Tomorrow, in **Day 153**, we step away from the GPU internals and move up the stack to **API Design**. We will learn how to wrap these engines into robust, OpenAI-Compatible APIs with SSE Streaming and rate limits!
