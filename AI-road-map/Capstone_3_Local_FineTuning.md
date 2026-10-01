# Capstone Project 3: The Hacker's Local Fine-Tuning Pipeline

## Objective
Take a pre-trained open-source Base Model that knows nothing about you. Fine-tune it locally on your own hardware so that it learns your unique writing style. Finally, compress it and serve it completely offline for free.

## Tech Stack to Use
- **Base Model:** `meta-llama/Meta-Llama-3-8B` (from Hugging Face)
- **Fine-Tuning:** `Transformers`, `TRL`, `PEFT`, `bitsandbytes` (QLoRA)
- **Deployment:** `llama.cpp` or `vLLM`
- **Hardware:** Apple Silicon Mac (using MLX) OR an NVIDIA GPU (using standard PyTorch)

## Step-by-Step Implementation Guide

### Step 1: The Dataset
1. Export a massive chunk of your personal text messages, Slack messages, or emails.
2. Format the data into a JSONL file containing Chat Templates.
   - Example format: `{"messages": [{"role": "user", "content": "Hey, when are you free?"}, {"role": "assistant", "content": "im super busy today tbh, maybe tmrw night?"}]}`

### Step 2: QLoRA Fine-Tuning (The Training)
1. Write a script to load the Base Model in 4-bit quantization using `bitsandbytes`.
2. Initialize a `LoraConfig` (PEFT). 
   - Set `r=16` and `lora_alpha=32`.
   - Target the `q_proj` and `v_proj` modules of the Transformer.
3. Pass the quantized model, the LoRA config, and your JSONL dataset into TRL's `SFTTrainer`.
4. Run the training for exactly 1 or 2 epochs. (Do NOT overfit!)

### Step 3: Merging the Adapters
1. The training will output a tiny 100MB LoRA adapter file. 
2. Write a script to load the original Base Model in full precision, apply the LoRA adapter to it, and merge the weights back into the main matrices (`model.merge_and_unload()`).
3. Save the final merged model to your hard drive.

### Step 4: Quantization and GGUF Conversion
1. You now have a massive 16GB PyTorch model. You want to run this fast on your CPU or Mac.
2. Clone the `llama.cpp` repository from GitHub.
3. Use their provided Python script to convert your PyTorch `.safetensors` model into a compressed 4-bit `.gguf` file.
   - Command: `python convert_hf_to_gguf.py ./my-merged-model --outtype q4_k_m`

### Step 5: Local Serving
1. Start the `llama-cpp-python` API server using your new `.gguf` file.
2. Write a simple Python script using the standard `openai` library to connect to `localhost:8000`.
3. Have a conversation with the AI clone of yourself, running completely offline!
