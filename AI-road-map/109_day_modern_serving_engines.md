# Day 109: Modern Quantized/Optimized Serving

Welcome to Day 109. You've trained a massive model, or perhaps you've downloaded a 70B parameter open-weight model. Now you need to serve it to users. 

Serving a Large Language Model (LLM) is fundamentally different from serving a standard REST API. LLM inference is severely memory-bandwidth bound. If you just load a raw PyTorch model and put it behind a Flask server, you will get terrible throughput and massive latency.

Today, we dive into the modern ecosystem of LLM serving engines and quantization formats that make production AI possible.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Bottleneck: Memory Bandwidth vs. Compute
When an LLM generates a token, it must load the *entire* neural network (all its weights) from the GPU's High Bandwidth Memory (HBM) into the GPU's compute cores. 
For a 70B parameter model in 16-bit precision, that's 140GB of data moving across the GPU bus for *every single word* generated.
The GPU compute cores are incredibly fast, but they sit idle waiting for the data to arrive. This means LLM serving is a **Memory Bandwidth** problem, not a compute problem.

### 2. Quantization: The Solution
If memory bandwidth is the bottleneck, the solution is to make the model smaller. **Quantization** reduces the precision of the weights.
- **FP16 / BF16 (16-bit):** Standard precision. A 7B model takes 14GB of VRAM.
- **INT8 (8-bit):** Halves the memory requirement.
- **INT4 (4-bit):** Quarters the memory requirement. A 7B model now fits in <4GB of VRAM!

But you can't just truncate the decimals; you will destroy the model's intelligence. Modern quantization techniques are smart:
- **AWQ (Activation-aware Weight Quantization):** Observes the model during inference. It realizes that 99% of the weights don't matter much, but 1% of the weights are "salient" (critical for accuracy). AWQ aggressively quantizes the unimportant weights to 4-bit, but keeps the salient weights at higher precision.
- **GPTQ:** Uses second-order mathematical information (Hessian matrix) to compensate for the error introduced by quantizing a weight by adjusting the remaining weights.

### 3. Modern Serving Engines
Once your model is quantized, you need an engine designed specifically for LLM inference.
- **vLLM:** The industry standard. Famous for inventing **PagedAttention**, which manages the KV cache exactly like an Operating System manages virtual memory (using pages). This prevents memory fragmentation and allows for massive batch sizes.
- **SGLang:** A newer engine that introduces **RadixAttention**. It automatically caches the KV states of prefixes (like system prompts or document context) across different requests using a Radix tree. If 100 users all send a prompt starting with the same long PDF, SGLang only computes the PDF once!
- **TensorRT-LLM:** Nvidia's highly optimized, low-level engine. Extremely fast, but notoriously difficult to compile and deploy compared to vLLM.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's look at how you actually use these tools in practice. We will simulate deploying a model using `vLLM`.

Create a file named `vllm_server_example.py`:

```python
# Note: This is a conceptual script demonstrating the vLLM API.
# You would need vllm installed and a GPU to run this for real.
# pip install vllm

from vllm import LLM, SamplingParams

def run_vllm_inference():
    print("--- STARTING vLLM SERVER ---")
    
    # 1. Load the Model
    # We specify an AWQ-quantized model. vLLM will automatically recognize the format
    # and use optimized INT4 compute kernels.
    model_id = "TheBloke/Llama-2-7B-Chat-AWQ"
    
    print(f"Loading {model_id} into VRAM using PagedAttention...")
    # In a real environment, this allocates a massive contiguous block of VRAM for the KV cache.
    llm = LLM(model=model_id, quantization="awq", gpu_memory_utilization=0.9)
    
    # 2. Define Sampling Parameters
    # Temperature, Top-P, etc.
    sampling_params = SamplingParams(temperature=0.7, top_p=0.95, max_tokens=100)
    
    # 3. Batch Inference
    # vLLM's true power is batching. We pass multiple prompts at once.
    # Continuous Batching will process these simultaneously, dynamically swapping them
    # in and out of the GPU as they generate tokens.
    prompts = [
        "Explain quantum mechanics in one sentence.",
        "Write a haiku about a GPU.",
        "What is the capital of France?"
    ]
    
    print("\nSending batch request to vLLM engine...")
    outputs = llm.generate(prompts, sampling_params)
    
    # 4. Print Results
    for output in outputs:
        prompt = output.prompt
        generated_text = output.outputs[0].text
        print(f"\nPrompt: {prompt!r}")
        print(f"Generated: {generated_text!r}")

if __name__ == "__main__":
    print("This script demonstrates the vLLM Python API.")
    print("To run it, you need a Linux machine with an NVIDIA GPU and vLLM installed.")
    # run_vllm_inference() # Uncomment to run if in a compatible environment
```

### Key Takeaways from Code:
1. **Simplicity:** Despite the insane underlying complexity of PagedAttention and continuous batching, the API is incredibly simple.
2. **Native Quantization Support:** You just tell the engine `quantization="awq"`, and it handles the low-level CUDA kernels required to do math on 4-bit integers.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: PagedAttention vs Continuous Batching
These two terms are often thrown around together, but they solve different problems.
**Your Task:**
1. Research **Continuous Batching** (also called iteration-level scheduling). Contrast it with traditional "Static Batching".
2. Research **PagedAttention**.
3. Explain how PagedAttention *enables* efficient Continuous Batching. (Hint: Think about memory fragmentation when requests finish at different times).

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your team has built an LLM application that summarizes user-uploaded documents. Users upload a 50-page PDF, ask 5 different questions about it in a chat interface, and then leave. Currently, you are using vLLM, and your latency is high because the model re-computes the KV cache for the entire 50-page PDF for every single question. How would you architect the serving layer to solve this?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Identify the Bottleneck (Prefill vs. Decode):** State that processing the 50-page PDF is the "Prefill" phase, which is compute-heavy. Answering the short questions is the "Decode" phase. The system is currently wasting massive compute re-doing the prefill.
2. **Propose Prefix Caching / Prompt Caching:** Explain that the KV cache for the 50-page document should be computed once and stored. Subsequent requests should recognize the shared prefix and reuse the cached KV states.
3. **Recommend a Specific Engine (SGLang/RadixAttention):** Mention that while vLLM has experimental prefix caching, engines designed specifically around this concept, like **SGLang** with its RadixAttention mechanism, are perfectly suited for this workload. It will automatically build a radix tree of the document and instantly serve the 5 questions without recomputing the PDF.

---
**Task for the end of the day:** Commit your notes to Git. 

You now understand how to serve models at scale. Tomorrow, we will look at how to deploy these systems onto Kubernetes clusters.
