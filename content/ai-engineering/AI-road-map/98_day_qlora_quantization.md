# Day 98: QLoRA & Memory-Efficient Fine-Tuning

Welcome to Day 98. Yesterday, we learned that LoRA eliminates the Optimizer VRAM problem by only training tiny $A$ and $B$ matrices.
But we STILL have to load the massive frozen Base Model into VRAM to run the forward pass! 
A 70-Billion parameter model in FP16 still requires 140GB of VRAM. It still will not fit on a single RTX 4090 (24GB).

Today, we achieve the impossible: **QLoRA (Quantized LoRA)**. We will mathematically compress the 70B model so it fits on cheap consumer hardware, without losing its intelligence.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The NormalFloat4 (NF4) Miracle
Tim Dettmers and the University of Washington made a massive realization.
If you simply quantize a Neural Network's weights from 16-bit to standard 4-bit integers (`int4`), the model becomes stupid. Why? Because `int4` spaces the numbers out equally ($1, 2, 3, 4$). 
But Neural Network weights are **Normally Distributed** (they form a Bell Curve centered around $0.0$). 
Tim invented **NF4 (NormalFloat4)**. It is a 4-bit data type where the 16 possible values are mathematically squeezed tightly around $0.0$, perfectly matching the Bell Curve of the weights!
This allows us to freeze a 70B model in 4-bit NF4 precision with almost ZERO accuracy loss!

### 2. The QLoRA Pipeline
How do you train a 4-bit model? You don't. You cannot do backpropagation math in 4-bit. QLoRA is a hybrid dance:
1. **The Base Model:** Loaded and frozen entirely in 4-bit NF4 precision.
2. **The LoRA Adapters:** Initialized in **16-bit precision (BF16)**.
3. **The Forward Pass:** As the data flows through Layer 1, PyTorch temporarily "de-quantizes" the 4-bit base weights back into BF16. It multiplies them with the BF16 LoRA adapters, calculates the output, and then instantly deletes the BF16 base weights, keeping only the 4-bit version in RAM!
4. **The Backward Pass:** The gradients are calculated and applied *only* to the 16-bit LoRA adapters. 

### 3. Paged Optimizers (Unified Memory)
Even with QLoRA, if you have a massive batch size, you might OOM the GPU. 
QLoRA introduced **Paged Optimizers**. Similar to how your computer's OS pages RAM to your SSD when you open too many Chrome tabs, NVIDIA Unified Memory will temporarily page the Adam Optimizer states out of the GPU VRAM and into your cheap CPU System RAM!

### 4. The Memory Math
Let's calculate the VRAM to fine-tune a 13-Billion parameter model using QLoRA:
- **Base Model (4-bit):** $13\text{B} \times 0.5\text{ bytes} = 6.5\text{ GB}$
- **LoRA Adapters (16-bit):** Very tiny, $\sim 0.2\text{ GB}$
- **Optimizer States:** $\sim 1\text{ GB}$
- **Activation Memory:** $\sim 2\text{ GB}$
**Total:** $\sim 10\text{ GB}$. You can fine-tune a 13B model on a standard gaming laptop!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's write a QLoRA fine-tuning script. In production, nobody writes this from scratch. We use the HuggingFace `peft` and `bitsandbytes` libraries.

*(Note: Mentally run `pip install bitsandbytes peft transformers`)*

Create a file named `qlora_finetune.py`:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model

def run_qlora_pipeline():
    print("--- INITIALIZING QLoRA PIPELINE ---")
    
    model_id = "meta-llama/Llama-2-7b-hf" # Or any open model
    
    # 1. BITS AND BYTES CONFIG (The 4-bit Magic)
    print("\n1. Configuring 4-bit NF4 Quantization...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True, # Double quantization saves an extra 0.4 bits/param!
        bnb_4bit_quant_type="nf4",      # The optimal NormalFloat4 data type
        bnb_4bit_compute_dtype=torch.bfloat16 # De-quantize to BF16 during the forward pass!
    )
    
    print("\n2. Loading massive Base Model into VRAM (in 4-bit)...")
    # In a real environment, this automatically downloads the model and quantizes it on the fly!
    """
    model = AutoModelForCausalLM.from_pretrained(
        model_id, 
        quantization_config=bnb_config, 
        device_map="auto"
    )
    """
    print("[MOCK] Model loaded. 7B parameters compressed to ~3.5 GB!")
    
    # 3. PREPARE FOR TRAINING
    # This function freezes the 4-bit weights and enables gradient checkpointing to save VRAM!
    # model = prepare_model_for_kbit_training(model)
    print("\n3. Base model frozen and gradient checkpointing enabled.")
    
    # 4. INJECT LoRA ADAPTERS
    print("\n4. Configuring LoRA Adapters...")
    lora_config = LoraConfig(
        r=16, # Rank 16
        lora_alpha=32, # Scaling
        target_modules=["q_proj", "v_proj"], # Which matrices to inject A and B into
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM"
    )
    
    # model = get_peft_model(model, lora_config)
    print("[MOCK] LoRA Adapters injected. 16-bit Trainable parameters added.")
    
    # 5. PRINT THE VRAM SAVINGS
    # In a real run, you would call `model.print_trainable_parameters()`
    print("\n--- PARAMETER BREAKDOWN ---")
    print("Total Parameters: ~7,000,000,000")
    print("Trainable Parameters: ~16,000,000")
    print("Percentage Trainable: 0.22%")
    
    print("\nSUCCESS! You can now pass this `model` into the HuggingFace Trainer.")
    print("You are training a 7B model on a single 12GB GPU!")

if __name__ == "__main__":
    run_qlora_pipeline()
```

### Key Takeaways from Code:
1. **Target Modules:** Notice `target_modules=["q_proj", "v_proj"]`. By default, LoRA only attaches $A$ and $B$ matrices to the Query and Value attention mechanisms. If you want a smarter model, you should add `"gate_proj", "up_proj", "down_proj"` to inject LoRA into the massive FFN layers too!
2. **Double Quantization:** Notice `bnb_4bit_use_double_quant=True`. When you quantize billions of numbers, the "Quantization Constants" (the mathematical mapping keys) take up memory too! Double Quantization literally *quantizes the quantization constants*, saving an additional $0.4\text{ GB}$ of VRAM!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Paged Optimizers
In the HuggingFace `TrainingArguments`, you configure the optimizer.
**Your Task:**
1. Look up the `TrainingArguments` documentation.
2. Find the `optim` argument.
3. Understand why we use `optim="paged_adamw_32bit"`. This enables the NVIDIA Unified Memory paging discussed in Hour 1!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your startup has four RTX 4090 GPUs (24GB each). What is the absolute largest model you can fine-tune, and how? Walk through the complete memory budget strategy."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Hardware Assessment:** 
   - State that $4 \times 24\text{GB} = 96\text{GB}$ total VRAM.
2. **The Framework (FSDP + QLoRA):**
   - Propose using QLoRA to compress the model to 4-bit, and wrapping it in PyTorch FSDP (Fully Sharded Data Parallel) to shatter the 4-bit weights across the 4 GPUs.
3. **The Memory Math for a 70B Model:**
   - Base 70B model in 4-bit = $35\text{GB}$.
   - LoRA Adapters (Rank 64) in 16-bit = $\sim 1\text{GB}$.
   - Optimizer States for Adapters = $\sim 2\text{GB}$.
   - Activation Memory (using Gradient Checkpointing) = $\sim 10\text{GB}$.
   - Total required = $\sim 48\text{GB}$.
4. **The Conclusion:**
   - Yes! You can comfortably fine-tune a massive **70 Billion parameter LLaMA 3** model on just four RTX 4090s using QLoRA + FSDP + Checkpointing, using roughly half of your 96GB capacity!

---
**Task for the end of the day:** Commit your code to Git. 

We now have the hardware and the math to fine-tune anything. But **what** do we train it on? You cannot train a chatbot on raw Wikipedia data.

Tomorrow, in **Day 99**, we learn **Supervised Fine-Tuning (SFT)** and Chat Templates (ChatML). We will teach the model how to act like a helpful assistant!
