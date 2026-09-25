# Day 109: Continued Pre-Training & Domain Adaptation

Welcome to Day 109. You work for a pharmaceutical company. You want an <abbr title="Large Language Model">LLM</abbr> that understands complex genetics and biology.
You try Supervised Fine-Tuning (SFT), but the model hallucinates wildly. You try <abbr title="Retrieval-Augmented Generation">RAG</abbr>, but the model fails to comprehend the retrieved documents because it doesn't actually understand the fundamental vocabulary of molecular biology.

How do you inject massive, fundamental knowledge into an <abbr title="Large Language Model">LLM</abbr>? 
You do not use SFT. SFT is for *behavior*. To inject *raw knowledge*, you must use **Continued Pre-Training (CPT)**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. SFT vs CPT
- **SFT (Supervised Fine-Tuning):** Changes the model's *behavior*. (e.g., "Always respond in <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> format"). SFT requires high-quality Question/Answer pairs.
- **CPT (Continued Pre-Training):** Injects *raw knowledge and vocabulary*. CPT does not use Q/A pairs. It uses millions of raw, unstructured text documents (e.g., raw PDFs of medical research papers). The objective is simply Next-Token Prediction, exactly like original Pre-Training!

### 2. The Learning Rate Danger
The most critical hyperparameter in CPT is the Learning Rate. 
If you use a high learning rate, the model will rapidly memorize the Medical textbooks, but it will suffer **Catastrophic Forgetting**. The new medical weights will overwrite the original language weights, and the model will completely forget how to speak English!
To prevent this, you must use a learning rate $10\times$ to $50\times$ lower than the original pre-training rate. You want to *nudge* the weights, not overwrite them.

### 3. Data Mixing (The General Replay)
To further prevent Catastrophic Forgetting, you cannot train *exclusively* on Medical data.
You must mix your Domain Data with **General Replay Data**. 
If your dataset is $80\%$ Medical Textbooks, you must inject $20\%$ General Wikipedia/News articles into the batch. This mathematically forces the model to retain its general reasoning and grammar capabilities while it learns biology!

### 4. Curriculum Learning
Do not shock the model. Start your CPT dataset with $50\%$ General / $50\%$ Medical. Over the course of the training run, slowly shift the distribution until the final epochs are $10\%$ General / $90\%$ Medical. This allows the gradient descent to smoothly carve out new neural pathways for the domain knowledge.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Unlike SFT, which uses small ChatML strings, CPT requires packing massive, continuous blocks of exactly 4096 tokens (the context window). Let's build a PyTorch `DataLoader` concept that streams infinite chunks of raw text!

Create a file named `domain_adaptation.py`:

```python
import torch

def tokenize_and_pack_stream(raw_text_stream, tokenizer, block_size=4096):
    """
    CPT requires maximizing GPU efficiency. 
    We don't feed the model 1 sentence at a time.
    We pack multiple documents together until we hit exactly 4096 tokens!
    """
    buffer = []
    
    for text_document in raw_text_stream:
        # 1. Tokenize the document
        tokens = tokenizer.encode(text_document)
        
        # 2. Add an EOS token so the model knows a document ended
        tokens.append(tokenizer.eos_token_id)
        
        # 3. Add to buffer
        buffer.extend(tokens)
        
        # 4. If the buffer is larger than our block size, yield a perfect chunk!
        while len(buffer) >= block_size:
            chunk = buffer[:block_size]
            buffer = buffer[block_size:] # Keep the remainder for the next chunk!
            
            # Yield as PyTorch Tensors for training
            input_ids = torch.tensor(chunk)
            # In CPT (Next Token Prediction), the Labels are just the Inputs shifted by 1!
            labels = input_ids.clone() 
            
            yield {"input_ids": input_ids, "labels": labels}

def run_cpt_simulation():
    print("--- RUNNING CONTINUED PRE-TRAINING (CPT) PIPELINE ---\n")
    
    class MockTokenizer:
        def encode(self, text):
            # 1 word = 1 token for this mock
            return text.split()
        @property
        def eos_token_id(self):
            return "<|END_OF_DOC|>"
            
    tokenizer = MockTokenizer()
    
    # 1. THE DATA MIX!
    print("Simulating Data Stream (80% Medical, 20% General Replay)...")
    data_stream = [
        "Medical Doc 1: The mitochondria is the powerhouse of the cell.",
        "Medical Doc 2: CRISPR-Cas9 allows targeted genome editing.",
        "General Doc 1: The capital of France is Paris.", # General Replay!
        "Medical Doc 3: Apoptosis is programmed cell death."
    ]
    
    # 2. PACKING
    print(f"Packing into blocks of size 10 (for simulation)...\n")
    packed_dataset = tokenize_and_pack_stream(data_stream, tokenizer, block_size=10)
    
    for i, batch in enumerate(packed_dataset):
        print(f"Batch {i+1} (Perfectly packed 10 tokens!):")
        print(batch["input_ids"].tolist())
        print()
        
    print("[TRAINING] We pass these dense blocks into standard Cross-Entropy Loss.")
    print("[WARNING] Remember to set your Learning Rate to 1e-5 (Very Low!)")

if __name__ == "__main__":
    run_cpt_simulation()
```

### Key Takeaways from Code:
1. **Packing:** Notice how "Medical Doc 1" and "Medical Doc 2" get smashed together into the same tensor, separated by an `<|END_OF_DOC|>` token. This ensures the GPU is operating at $100\%$ utilization. No padding tokens are wasted!
2. **Next-Token Prediction:** In SFT, we mask the loss on the User's prompt. In CPT, we calculate loss on *every single token* in the 4096-token block. The model is learning the statistical distribution of the entire vocabulary.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Perplexity Evaluation
How do you know if your CPT worked? You measure **Perplexity** (how "surprised" the model is by a piece of text).
**Your Task:**
1. Hold out a validation set of 1,000 Medical documents that the model has never seen.
2. Before CPT, calculate the Base Model's perplexity on the validation set. (It will likely be high, e.g., $15.0$, because the medical jargon surprises it).
3. After CPT, calculate the Perplexity again. If it drops to $4.0$, you successfully injected the medical knowledge!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"A pharmaceutical company wants an <abbr title="Large Language Model">LLM</abbr> specialized in drug discovery. They have 10 Million PDFs of internal research. Design the complete adaptation pipeline from base model to production deployment. Importantly, how do you validate the scientific accuracy?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Pipeline (CPT -> SFT -> <abbr title="Direct Preference Optimization">DPO</abbr>):** 
   - State that you extract the text from the 10M PDFs and run **Continued Pre-Training** (with $20\%$ General Replay data) to inject the biological vocabulary.
   - Then, you use GPT-4 to generate Q/A pairs based on those PDFs, and run **Supervised Fine-Tuning** to teach it how to act like a helpful lab assistant.
   - Finally, you run **<abbr title="Direct Preference Optimization">DPO</abbr>** to align it for safety.
2. **Validating Scientific Accuracy:**
   - Explain that Perplexity and standard benchmarks (MMLU) are not enough for enterprise Pharma. 
   - Propose a customized **<abbr title="Large Language Model">LLM</abbr>-as-a-Judge** pipeline. You prompt GPT-4 with a strict grading rubric created by PhD Chemists to evaluate the model's generated drug synthesis pathways for factual hallucinations. You also enforce rigorous A/B testing with internal scientists.

---
**Task for the end of the day:** Commit your code to Git. 

We injected knowledge into the model. But where do we get the high-quality Q/A pairs for the SFT phase? 

Tomorrow, in **Day 110**, we return to Synthetic Data. But this time, we scale it to enterprise levels using **Strong-to-Weak Distillation and Chain-of-Thought Traces (The Orca Method)**!
