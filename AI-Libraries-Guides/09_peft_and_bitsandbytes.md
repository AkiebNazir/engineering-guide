# <abbr title="Parameter-Efficient Fine-Tuning">PEFT</abbr> & BitsAndBytes Mastery: Fine-Tuning Massive LLMs Locally

## 1. The Core Concept (What and Why)

*Assuming you know absolutely nothing about this library, let's start from zero.*

**What is it?**
To fine-tune a massive Open-Source model like Llama-3-70B, you need two companion libraries alongside Hugging Face `transformers`:
1. `bitsandbytes`: A library that compresses (Quantizes) massive <abbr title="Artificial Intelligence">AI</abbr> models down to a fraction of their original size.
2. `peft` (Parameter-Efficient Fine-Tuning): A library that implements **<abbr title="Low-Rank Adaptation">LoRA</abbr>** (Low-Rank Adaptation), allowing you to train massive models without needing a $100,000 supercomputer.

**Why do they exist?**
A 70-Billion parameter model uses 140 Gigabytes of VRAM just to exist in 16-bit math. If you try to run `loss.backward()` (from Guide 05) to update all 70 billion weights simultaneously, the math requires roughly 400-600 Gigabytes of VRAM. It is mathematically impossible to do this on consumer hardware.

- `bitsandbytes` solves this by crunching the 16-bit numbers down into 4-bit numbers (Shrinking the 140GB model down to 35GB).
- `peft` solves this by **freezing** all 70 billion weights so they cannot be updated. It then injects a tiny "Adapter" (about 100 Megabytes in size) into the model. During training, ONLY the tiny 100MB adapter is updated! 

When combined, this is called **<abbr title="Quantized Low-Rank Adaptation">QLoRA</abbr>** (Quantized Low-Rank Adaptation). It is the only way everyday engineers can fine-tune frontier models.

---

## 2. Setup & Installation

You need an NVIDIA GPU. `bitsandbytes` relies heavily on custom CUDA kernels.

```bash
pip install peft bitsandbytes accelerate transformers
```

```python
import peft
import bitsandbytes as bnb

print(f"PEFT version: {peft.__version__}")
```

---

## 3. The "Hello World": Loading a Model in 4-bit

Before we fine-tune, we must load the massive model into memory without crashing the server. We do this by creating a `BitsAndBytesConfig` and passing it to the Hugging Face `AutoModelForCausalLM`.

### Parameter Breakdown: `BitsAndBytesConfig`
- `load_in_4bit` (bool): 
  - *Effect:* If `True`, the model's weights are aggressively compressed. You lose a tiny fraction of mathematical precision, but you save 75% of your VRAM.
- `bnb_4bit_compute_dtype` (torch.dtype): 
  - *Effect:* While the model is *stored* in 4-bit to save space, the GPU cannot actually multiply 4-bit numbers. During the forward pass, it temporarily decompresses the numbers back to 16-bit, does the math, and throws them away. Setting this to `torch.bfloat16` ensures the decompressed math is highly stable and fast on modern GPUs (like Ampere A100s or RTX 3090s).
- `bnb_4bit_use_double_quant` (bool): 
  - *Effect:* If `True`, it compresses the compression statistics! It squeezes an extra 0.5 GB of VRAM out of the model for free. Always set this to `True` for massive models.

```python
import torch
from transformers import AutoModelForCausalLM, BitsAndBytesConfig

# 1. Define the Quantization rules
bnb_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_use_double_quant=True,
    bnb_4bit_quant_type="nf4", # NormalFloat4 (An optimized 4-bit format)
    bnb_4bit_compute_dtype=torch.bfloat16
)

# 2. Load the model using the config
model_id = "meta-llama/Meta-Llama-3-8B"

model = AutoModelForCausalLM.from_pretrained(
    model_id,
    quantization_config=bnb_config,
    device_map="auto" # Automatically push to GPU
)

# 3. Verify the memory footprint!
print(model.get_memory_footprint() / 1e9, "Gigabytes") 
# Output: ~4.5 Gigabytes (Instead of 16GB!)
```

---

## 4. Deep Dive: <abbr title="Parameter-Efficient Fine-Tuning">PEFT</abbr> and the `LoraConfig`

Now the model is loaded in 4-bit, but it is completely frozen. We must use `peft` to inject the trainable <abbr title="Low-Rank Adaptation">LoRA</abbr> adapter.

### Parameter Breakdown: `LoraConfig`
- `r` (int - The "Rank"): The most important setting. Usually set between `8` and `64`.
  - *Effect of increasing (e.g., 256):* The adapter becomes massive. The model gains a ton of "expressive power" to learn entirely new languages or complex math, but it will use vastly more VRAM and train much slower.
  - *Effect of decreasing (e.g., 4):* The adapter is tiny. It uses almost zero VRAM. Perfect if you just want to teach the model a specific tone of voice (e.g., "Answer like a pirate"), but it doesn't have enough mathematical capacity to learn complex new facts.
- `lora_alpha` (int): The scaling factor.
  - *Effect:* A mathematical rule of thumb is to set `lora_alpha` to exactly **2x the Rank (`r`)**. If `r=16`, `lora_alpha=32`. This ensures that the tiny adapter's output is scaled up enough to actually influence the massive 70-Billion parameter model it is attached to.
- `target_modules` (list of strings): Where to inject the adapters.
  - *Effect:* If you only inject it into the `["q_proj", "v_proj"]` (Query and Value attention matrices), it trains fast. If you inject it into `["all-linear"]` (every single layer in the model), you get much higher accuracy, but training takes longer.
- `lora_dropout` (float): Similar to standard dropout in Neural Networks.
  - *Effect of increasing (e.g., 0.1):* It randomly disables 10% of the adapter weights during training. This forces the adapter to generalize and prevents it from simply memorizing the training dataset (Overfitting).

```python
from peft import prepare_model_for_kbit_training, LoraConfig, get_peft_model

# 1. Prepare the 4-bit model for training
# This freezes all original weights and converts them to the correct format for Autograd
model = prepare_model_for_kbit_training(model)

# 2. Define the LoRA Adapter rules
peft_config = LoraConfig(
    r=16, 
    lora_alpha=32, 
    target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], 
    lora_dropout=0.05,
    bias="none",
    task_type="CAUSAL_LM" # We are training a text generator!
)

# 3. Inject the Adapter into the model!
model = get_peft_model(model, peft_config)

# 4. Prove to yourself that LoRA works!
model.print_trainable_parameters()
# Output: trainable params: 41,943,040 || all params: 8,072,204,288 || trainable%: 0.519%
```

**Look at that output!** Instead of calculating calculus derivatives for 8 Billion parameters, PyTorch only has to calculate gradients for 41 Million parameters (0.5%). This is why you can fine-tune LLMs on a standard gaming PC.

---

## 5. Saving and Merging the Adapter

When training finishes, you do not save the 8 Billion parameter model. It was frozen the whole time! You only save the 41 Million parameter adapter.

```python
# Save the tiny 100MB adapter to your hard drive
model.save_pretrained("./my-custom-lora-adapter")

# --- LATER IN PRODUCTION ---
from peft import PeftModel

# 1. Load the BASE model normally
base_model = AutoModelForCausalLM.from_pretrained(model_id)

# 2. Snap the tiny adapter onto the base model like a LEGO piece!
production_model = PeftModel.from_pretrained(base_model, "./my-custom-lora-adapter")

# (Optional Pro Move) Merge the weights permanently
# This physically adds the LoRA matrix math into the Base model's matrix.
# It makes inference slightly faster because you don't have to calculate two paths!
final_merged_model = production_model.merge_and_unload()
```

---

## 6. MAANG Interview Scenarios

### Scenario 1: Multi-Tenant Inference (The True Power of <abbr title="Low-Rank Adaptation">LoRA</abbr>)
*Interviewer:* "We are a massive <abbr title="Software as a Service - A software licensing and delivery model in which software is licensed on a subscription basis and is centrally hosted.">SaaS</abbr> company. 500 different enterprise clients want their own custom-trained <abbr title="Large Language Model">LLM</abbr>. If we deploy 500 separate Llama-3 models to our AWS cluster, we will go bankrupt paying for GPU instances. How do we solve this?"

*Answer:* "We use Serverless <abbr title="Low-Rank Adaptation">LoRA</abbr> inference (like vLLM or Lorax). Because the Base Model is completely frozen, we only need to load the massive Base Model into the GPU's VRAM *once*. For all 500 clients, we fine-tune a tiny 100MB <abbr title="Low-Rank Adaptation">LoRA</abbr> adapter for them. 
When Client A makes an <abbr title="Application Programming Interface">API</abbr> request, the server dynamically injects Client A's 100MB adapter into the GPU in roughly 5 milliseconds, runs the inference, and unloads it. A single GPU cluster can serve 500 custom models simultaneously, saving 99% on infrastructure costs."

### Scenario 2: Catastrophic Forgetting
*Interviewer:* "You fine-tuned a coding model purely on Python code. Now, when you ask it to speak French, it outputs gibberish. The base model used to know French! What happened?"

*Answer:* "This is called **Catastrophic Forgetting**. During fine-tuning, the <abbr title="Low-Rank Adaptation">LoRA</abbr> adapter drastically shifted the mathematical distribution of the model to prioritize Python syntax, destroying its internal representations of other languages. 
To fix this, we must use **Replay / Mix-in Regularization**. During our Python fine-tuning, we must inject 10-20% of general-purpose conversational data (like French translations or general Wikipedia facts) into the training batches. This forces the adapter to learn Python *without* un-learning everything else."

---

## 7. Common Pitfalls & Debugging in Production

### ⚠️ Pitfall 1: Incorrect `lora_alpha` Scaling
If your loss is completely frozen and the model refuses to learn anything, your `lora_alpha` is likely too low (e.g., `r=64`, but `lora_alpha=1`). The adapter's mathematical output is being multiplied by a fraction, making its contribution to the final network essentially zero.
*Fix:* Always follow the rule: `lora_alpha = 2 * r`.

### ⚠️ Pitfall 2: `ValueError: Unrecognized configuration class`
When loading a saved <abbr title="Parameter-Efficient Fine-Tuning">PEFT</abbr> model using the standard `AutoModel.from_pretrained()` command, Hugging Face will crash because it doesn't know how to handle the `adapter_config.json` file.
*Fix:* You MUST use the `PeftModel.from_pretrained(base_model, adapter_path)` syntax to load a <abbr title="Low-Rank Adaptation">LoRA</abbr>.

### ⚠️ Pitfall 3: Not targeting all linear modules
In older tutorials, `target_modules` was often set to just `["q_proj", "v_proj"]` to save VRAM. Modern research (2024+) shows that if you do this, your model will heavily underperform on complex reasoning tasks. 
*Fix:* If you have the VRAM, you should almost always set `target_modules="all-linear"`. This injects <abbr title="Low-Rank Adaptation">LoRA</abbr> into every dense layer (including the MLPs), vastly improving the model's intelligence at the cost of slightly longer training times.
