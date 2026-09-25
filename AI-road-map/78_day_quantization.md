# Day 78: Quantization & Precision (INT8, INT4, AWQ)

Welcome to Day 78. Pruning physically deletes weights from the model. **Quantization** takes a different approach: it leaves all the weights intact, but radically compresses their precision.

By mathematically crushing 32-bit floating-point numbers into 4-bit integers, we can take a 70-Billion parameter LLaMA model that requires a \$40,000 GPU cluster, and run it locally on a standard MacBook.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Memory Math (Why Quantization Exists)
When you train a Neural Network in PyTorch, it defaults to **FP32** (32-bit Floating Point).
A 32-bit float requires **4 bytes** of memory.
- LLaMA-70B has 70,000,000,000 parameters.
- $70\text{B} \times 4\text{ bytes} = 280\text{ Gigabytes}$ of VRAM just to load the model! 
An NVIDIA A100 GPU only has 80GB of VRAM. You would need four A100s just to open the file.

### 2. INT8 Quantization (The 4x Compression)
We don't actually need the massive decimal precision of FP32 (e.g., $3.14159265$). 
In **INT8 Quantization**, we mathematically map the entire range of the FP32 tensor into 8-bit integers ($[-128, 127]$).
- Because 8 bits = 1 byte, the parameter size shrinks from 4 bytes to 1 byte.
- The 70B model now takes **70GB** of VRAM. It fits on a single A100!

### 3. INT4 Quantization & GPTQ (The 8x Compression)
Can we compress it even further? Yes. **INT4 Quantization**.
4 bits can only represent 16 unique numbers ($[-8, 7]$). 
If we crush the weights into INT4, the 70B model shrinks to **35GB**, fitting on consumer hardware!
However, crushing continuous math into 16 numbers causes massive accuracy loss. To fix this, researchers invented **GPTQ** (Layer-wise Quantization). It uses the Hessian matrix to mathematically calculate exactly which weights are critical, and optimally rounds them to preserve the original loss function.

### 4. The Outlier Problem (AWQ)
LLMs have a weird flaw: $99\%$ of their weights are small (e.g., $[-1.0, 1.0]$), but $1\%$ of the activations suddenly spike to massive numbers (e.g., $150.0$).
If you blindly map $[-150.0, 150.0]$ to $[-8, 7]$, all the small, important weights get crushed to exactly $0$, destroying the model's intelligence!
**AWQ (Activation-aware Weight Quantization)** solves this by analyzing the model. It keeps the $1\%$ "Outlier" weights in high-precision FP16, and only quantizes the remaining $99\%$ to INT4. This perfectly preserves the intelligence of the model!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's look under the hood. We will write the exact mathematical formula used to map FP32 floats into INT8 integers (Min-Max Symmetric Quantization).

Create a file named `quantization_math.py`:

```python
import torch

def quantize_to_int8(tensor_fp32):
    """
    Mathematically maps an FP32 tensor to an INT8 tensor [-128, 127].
    """
    # 1. Find the absolute maximum value in the tensor (The Outlier)
    abs_max = torch.max(torch.abs(tensor_fp32))
    
    # 2. Calculate the Scaling Factor
    # We map the absolute maximum value to exactly 127 (the max of INT8)
    scale = abs_max / 127.0
    
    # 3. Apply the Scale
    # We divide the floats by the scale, and round to the nearest integer!
    tensor_int8 = torch.round(tensor_fp32 / scale)
    
    # 4. Clamp the values just in case
    tensor_int8 = torch.clamp(tensor_int8, -128, 127).to(torch.int8)
    
    return tensor_int8, scale

def dequantize_to_fp32(tensor_int8, scale):
    """
    To run the actual Matrix Multiplication, the GPU usually converts the INT8
    back to FP16/FP32 on the fly using the saved scale factor!
    """
    return tensor_int8.to(torch.float32) * scale

def test_quantization():
    print("--- RUNNING INT8 QUANTIZATION ---")
    
    # Simulate a weight matrix with one massive outlier
    fp32_weights = torch.tensor([0.15, -0.42, 1.25, -2.10, 150.0, -0.05])
    print(f"Original FP32: {fp32_weights.tolist()}")
    
    # Quantize
    int8_weights, scale = quantize_to_int8(fp32_weights)
    print(f"\nScale Factor: {scale.item():.4f}")
    print(f"Quantized INT8: {int8_weights.tolist()}")
    
    # Notice the Outlier Problem!
    # Because 150.0 became 127, the tiny numbers like 0.15 and -0.05 became 0!
    # Their precision was completely destroyed by the single outlier!
    
    # Dequantize
    recovered_fp32 = dequantize_to_fp32(int8_weights, scale)
    print(f"\nRecovered FP32: {recovered_fp32.tolist()}")
    
    # Calculate Quantization Error
    error = torch.mean(torch.abs(fp32_weights - recovered_fp32))
    print(f"\nAverage Quantization Error: {error.item():.4f}")
    print("This error is why AWQ exists—to protect those tiny numbers from the outlier!")

if __name__ == "__main__":
    test_quantization()
```

### Key Takeaways from Code:
1. **The Scale Factor:** Quantization is not just rounding. You must calculate a `scale` so the GPU knows how to un-crush the numbers later! The scale factor is kept in high-precision float.
2. **The Outlier Destruction:** Notice how the `0.15` became `0`. Because the scale was so massive (to accommodate the `150.0`), the tiny weights lost all their data. If an <abbr title="Large Language Model">LLM</abbr> loses its tiny weights, it starts generating gibberish.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The GGUF Format
The standard HuggingFace format (`.safetensors`) is designed for GPUs. But Apple MacBooks have incredible CPUs and Unified Memory.
**Your Task:**
1. Research the **GGUF** format (built by Georgi Gerganov for `llama.cpp`).
2. Conceptually understand how GGUF quantizes models specifically for CPU SIMD instructions (like Apple Silicon's AMX coprocessors). 
3. Understand why running an INT4 GGUF model on a 64GB Mac Studio is currently the cheapest way to run a 70B model locally in the world.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your team needs to serve a massive 70B parameter model on a server with 2x A100-40GB GPUs. Walk through your quantization strategy. How do you validate that quantization hasn't degraded the model's quality for your specific enterprise use case?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Memory Constraint & Selection:** 
   - State that a 70B model in FP16 takes ~140GB, which exceeds the combined 80GB of the two GPUs.
   - Propose using **INT4 Quantization** (which reduces the weights to ~35GB, leaving 45GB of VRAM for the massive KV-Cache required for multiple users).
2. **The Algorithm Choice (AWQ / GPTQ):**
   - Explicitly choose AWQ or GPTQ over naive Min-Max quantization to protect the outlier activations and preserve the model's reasoning capabilities. 
   - Note that you will use Tensor Parallelism to split the INT4 model across the two GPUs to maximize memory bandwidth.
3. **The Validation Strategy:**
   - Explain that perplexity scores are not enough.
   - Propose an **<abbr title="Large Language Model">LLM</abbr>-as-a-Judge** pipeline: Take 1,000 real enterprise queries. Run them through the original FP16 model and the new INT4 model. Have GPT-4 (or a human evaluation team) blindly grade the two outputs on accuracy and hallucination rates to ensure the business logic didn't degrade during compression.

---
**Task for the end of the day:** Commit your code to Git. 

You have mastered Model Compression. We are now ready to look at Advanced Architectures.
Tomorrow, in **Day 79**, we learn the secret behind GPT-4 and Mixtral: **The Mixture of Experts (<abbr title="Mixture of Experts">MoE</abbr>)** architecture!
