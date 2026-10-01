# Day 99: Instruction Tuning & Chat Templates

Welcome to Day 99. You now know how to train a Base Model like `LLaMA-3-8B-Base`. 
But a Base Model is NOT a chatbot. It is a highly advanced autocomplete engine.

If you prompt a Base Model with: *"What is the capital of France?"*
It will not answer you. It will likely autocomplete the text with: *"And what is the capital of Germany? And what is the capital of Italy?"* because it thinks you are writing a geography quiz!

Today, we learn **Supervised Fine-Tuning (SFT)** and **Chat Templates** to transform a wild text-predictor into a polite, helpful assistant.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Supervised Fine-Tuning (SFT)
SFT is the first step of Alignment. 
We collect thousands of high-quality examples of a human "Instruction" and a perfect "Response". We fine-tune the model to recognize this pattern. We are literally teaching the model: *When you see a question, stop autocompleting the question, and instead switch into 'Answer Mode'.*

### 2. Chat Templates (The Secret Syntax)
An LLM only understands a single 1D string of text. It has no concept of a "User UI" or an "Assistant UI". 
To create the illusion of a conversation, researchers invented special control tokens.
- **ChatML (OpenAI's format):**
  `<|im_start|>user\nWhat is 2+2?<|im_end|>\n<|im_start|>assistant\nIt is 4.<|im_end|>`
- **LLaMA's format:**
  `[INST] What is 2+2? [/INST] It is 4. </s>`
The model learns that whatever is inside `[INST]` is the human, and whatever is outside is itself!

### 3. The EOS Token (Teaching it to stop)
The most important token in SFT is the **End of Sequence (EOS)** token (e.g., `<|im_end|>` or `</s>`).
During SFT, you force the model to output the EOS token at the end of every answer. 
If you don't do this, the model will answer the question, but then it will start hallucinating the *next* User's question, and then it will answer itself! The EOS token is the mathematical signal that tells the inference engine to stop generating and wait for the human.

### 4. System Prompts
The System Prompt is a hidden string placed at the very beginning of the chat template.
`<|im_start|>system\nYou are a helpful pirate.<|im_end|>`
Because it is the absolute first thing the Attention Mechanism reads, it sets the mathematical context for the entire sequence, forcing the model to adopt a persistent persona.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Python script that takes a raw JSON dataset of instructions and formats it strictly into ChatML strings, preparing it for the HuggingFace `SFTTrainer`.

Create a file named `chat_templates.py`:

```python
import json

def apply_chatml_template(system_prompt, user_message, assistant_response=None):
    """
    Formats raw text into the strict ChatML syntax.
    If assistant_response is None, it creates a prompt ready for inference!
    """
    # 1. Start with the System Prompt
    chatml_string = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
    
    # 2. Add the User Message
    chatml_string += f"<|im_start|>user\n{user_message}<|im_end|>\n"
    
    # 3. Add the Assistant
    chatml_string += "<|im_start|>assistant\n"
    
    # If we are Training, we include the answer AND the EOS token!
    if assistant_response:
        chatml_string += f"{assistant_response}<|im_end|>"
        
    return chatml_string

def prepare_sft_dataset():
    print("--- PREPARING SFT DATASET (CHATML) ---")
    
    # 1. Raw Data (Usually downloaded from HuggingFace Datasets)
    raw_dataset = [
        {"instruction": "Write a python loop from 1 to 5.", "output": "for i in range(1, 6):\n    print(i)"},
        {"instruction": "What is the capital of Japan?", "output": "The capital of Japan is Tokyo."}
    ]
    
    system_prompt = "You are a helpful, concise AI coding assistant."
    
    # 2. Format the Training Data
    print("Formatting Training Data (Notice the <|im_end|> tags!):")
    formatted_training_data = []
    
    for item in raw_dataset:
        formatted = apply_chatml_template(
            system_prompt=system_prompt,
            user_message=item["instruction"],
            assistant_response=item["output"]
        )
        formatted_training_data.append(formatted)
        print("\n--- Example ---")
        print(formatted)
        
    # 3. Format an Inference Prompt
    print("\n\nFormatting an Inference Prompt (Waiting for LLM generation):")
    inference_prompt = apply_chatml_template(
        system_prompt=system_prompt,
        user_message="Write a python function to add two numbers."
    )
    # Notice it ends exactly at '<|im_start|>assistant\n', forcing the LLM to autocomplete the answer!
    print(inference_prompt)

if __name__ == "__main__":
    prepare_sft_dataset()
```

### Key Takeaways from Code:
1. **The Inference Hack:** Notice the inference prompt ends exactly at `<|im_start|>assistant\n`. Because the LLM is an autocomplete engine, the only mathematical path forward is to generate the assistant's answer!
2. **Tokenizer Templates:** In modern HuggingFace, you don't need to write this string concatenation manually. You can use `tokenizer.apply_chat_template(messages)`, and the tokenizer will automatically pull the correct `ChatML` or `Llama-3` template directly from the model's config file!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The UI Parser
When the LLM finishes generating, it spits out a raw ChatML string. Your React frontend UI doesn't know what `<|im_start|>` is.
**Your Task:**
1. Conceptually write a Python script using Regex or `string.split()`.
2. Take an entire ChatML string containing a 4-turn conversation.
3. Parse it into a standard JSON List of Dictionaries: 
`[{"role": "user", "content": "Hello"}, {"role": "assistant", "content": "Hi there!"}]`.
4. This is the exact code that runs inside API gateways like OpenAI's `/v1/chat/completions`.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"The LIMA paper (Less Is More for Alignment) proved that 1,000 high-quality SFT examples can outperform a model trained on 1 Million low-quality examples. Design a data curation strategy for instruction tuning. How do you measure 'quality'?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Diversity over Volume:** 
   - State that training on 10,000 math problems is useless. The 1,000 examples must have massive diversity (10 math, 10 coding, 10 creative writing, 10 legal analysis).
2. **Tone and Formatting Consistency:**
   - Explain that the LLM is learning *style* during SFT, not facts. Every single one of the 1,000 examples must have perfect grammar, strict adherence to formatting (e.g., always using Markdown for code), and a consistent, polite, unbiased tone.
3. **Measuring Quality (LLM-as-a-Judge):**
   - Propose using GPT-4 as an automated evaluator. You pass the SFT example to GPT-4 and ask it to score the response from 1-10 based on Helpfulness, Clarity, and Formatting. Drop any example that scores below an 8.

---
**Task for the end of the day:** Commit your code to Git. 

We need 1,000 perfect, highly diverse, complex SFT examples. But paying PhD experts to write 1,000 perfect coding answers costs \$50,000. 

What if we just ask GPT-4 to write the training data for us? Tomorrow, in **Day 100**, we learn the dark magic of **Synthetic Data and Evol-Instruct**!
