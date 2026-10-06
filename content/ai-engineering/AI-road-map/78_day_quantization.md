# Day 78: Quantization & Precision (INT8, INT4, GPTQ, AWQ)

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
If we crush the weights into INT4, the 70B model shrinks to about **35GB** (a little more once you count the scales), small enough for two 24GB consumer GPUs or a 64GB Mac!
However, naively rounding every weight to one of 16 levels ("round-to-nearest", RTN) loses real accuracy. Two post-training algorithms fix most of it, and you will see their names on every model hub:
- **GPTQ** (2022) quantizes a layer one column at a time and, after each rounding step, adjusts the not-yet-quantized weights to cancel the error. It uses second-order information (the Hessian $X^\top X$ of the layer inputs on a small calibration set) to decide how to spread the correction.
- Both GPTQ and AWQ also use **per-group scales** (one scale per ~128 weights) instead of one scale per tensor, so a single large value cannot ruin the precision of everything else.

### 4. The Outlier Problem (LLM.int8() and AWQ)
LLMs have a weird property: most activations are small, but a handful of hidden *channels* (feature dimensions) regularly carry huge values (e.g., $60$ or more while the rest sit near $1$). Those large activations multiply whatever rounding error sits in the matching weights.
If you blindly map a range stretched by one outlier to $[-8, 7]$, all the small values get crushed to $0$, destroying the model's intelligence (you will see this in today's code).
Two famous fixes:
- **LLM.int8()** (the `bitsandbytes` 8-bit mode) detects the outlier feature dimensions at runtime and computes them in FP16, while everything else runs in INT8. Accurate, but the mixed layout is slower.
- **AWQ (Activation-aware Weight Quantization)** keeps *every* weight in INT4. It finds the ~1% of input channels with the largest activations and **scales their weights up** before quantization (dividing the activations by the same factor, so the math is unchanged). The important weights then use more of the 16 levels and lose less precision, and the uniform INT4 layout runs on fast kernels.

Day 92 will implement GPTQ and AWQ from scratch and cover FP8, the GGUF format and the serving engines that run these models.

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
    print("This error is why per-group scales, GPTQ and AWQ exist: to protect the small numbers from the outlier!")

if __name__ == "__main__":
    test_quantization()
```

### Key Takeaways from Code:
1. **The Scale Factor:** Quantization is not just rounding. You must calculate a `scale` so the GPU knows how to un-crush the numbers later! The scale factor is kept in high-precision float.
2. **The Outlier Destruction:** Notice how the `0.15` became `0`. Because the scale was so massive (to accommodate the `150.0`), the tiny weights lost all their data. If an LLM loses its tiny weights, it starts generating gibberish.

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
   - Explicitly choose AWQ or GPTQ (INT4 with per-group scales) over naive Min-Max quantization: AWQ protects the weights that meet large activations, GPTQ compensates rounding error using calibration data (details on Day 92). 
   - Note that you will use Tensor Parallelism to split the INT4 model across the two GPUs to maximize memory bandwidth.
3. **The Validation Strategy:**
   - Explain that perplexity scores are not enough.
   - Propose an **LLM-as-a-Judge** pipeline: Take 1,000 real enterprise queries. Run them through the original FP16 model and the new INT4 model. Have GPT-4 (or a human evaluation team) blindly grade the two outputs on accuracy and hallucination rates to ensure the business logic didn't degrade during compression.

---
**Task for the end of the day:** Commit your code to Git. 

You have mastered Model Compression. We are now ready to look at Advanced Architectures.
Tomorrow, in **Day 79**, we learn the secret behind GPT-4 and Mixtral: **The Mixture of Experts (MoE)** architecture!
