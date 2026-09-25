# Day 70: T5 & Instruction Tuning

Welcome to Day 70. A base GPT model trained on the internet is an incredible autocomplete engine, but it is not an assistant. If you prompt a base model with *"Write a poem about the ocean"*, it might autocomplete it with *"Write a poem about the sky"*, because it thinks you are just listing writing prompts!

How do we force the <abbr title="Artificial Intelligence">AI</abbr> to follow our instructions? Today we look at Google's **T5** and the paradigm shift of **Instruction Tuning (Flan)**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. T5: The Text-to-Text Framework
Google released **T5 (Text-to-Text Transfer Transformer)**. It is a full Encoder-Decoder model.
Instead of having different architectures or classification heads for different tasks, T5 forces *everything* into a single Text-to-Text format. You simply append a string prompt to the input!
- **Translation:** `Input: "translate English to German: That is good." -> Output: "Das ist gut."`
- **Summarization:** `Input: "summarize: [Long Article]" -> Output: "[Short Summary]"`
- **Classification:** `Input: "sentiment: The movie was awful." -> Output: "negative"`

Because every task is just generating text, a single T5 model can do 50 different things simultaneously without changing its architecture!

### 2. Span Corruption (T5's Pre-training)
BERT used Masked Language Modeling (MLM), masking individual words. T5 uses **Span Corruption**.
Instead of masking a single word, T5 replaces an *entire phrase* (a span) with a single Sentinel Token.
- **Original:** *"The quick brown fox jumps over the lazy dog"*
- **Corrupted Input:** *"The quick [X] jumps over the [Y] dog"*
- **Target Output:** `"[X] brown fox [Y] lazy"`

The Encoder reads the corrupted input. The Decoder is trained to autoregressively output the missing spans! This forces the model to learn long-range grammar rather than just single-word guessing.

### 3. Instruction Tuning (The Flan Paper)
If you pre-train T5, it understands grammar. But if you give it a completely new task, it will fail.
Google released **Flan-T5**. They took 1,000 different <abbr title="Natural Language Processing">NLP</abbr> datasets (translation, math, logic, summaries) and rewrote them all as human instructions.
- *"Please solve this math problem step-by-step: 5 + 5"*
- *"Can you read this paragraph and tell me the main character's name?"*

By fine-tuning the model on thousands of *instructions*, a magical emergent property occurred: **Zero-Shot Generalization**. 
The <abbr title="Artificial Intelligence">AI</abbr> didn't just learn math or translation. It learned the *meta-skill of following instructions*. If you give Flan-T5 a completely brand new task it was never trained on, it will succeed simply because you phrased it as an instruction! This is the exact mechanism that turned base GPT-3 into ChatGPT!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's write the code to format raw data into the strict Text-to-Text instruction paradigm required by T5!

Create a file named `t5_instruction_formatting.py`:

```python
def format_instruction_data(task_type, input_text):
    """
    T5 requires explicit prefixes to know what task to perform!
    """
    if task_type == "translation":
        # T5 was trained specifically on these exact prefixes!
        return f"translate English to French: {input_text}"
    
    elif task_type == "summarization":
        return f"summarize: {input_text}"
    
    elif task_type == "sentiment":
        # We phrase it as a direct instruction for Flan-T5
        return f"Determine if the following review is positive or negative: {input_text}"
    
    elif task_type == "qa":
        # For Question Answering, we must provide context
        return f"Please answer the question based on the context.\nContext: {input_text['context']}\nQuestion: {input_text['question']}"
    
    else:
        raise ValueError("Unknown Task Type")

def test_t5_formatting():
    print("--- RUNNING T5 INSTRUCTION FORMATTING ---")
    
    # 1. Translation
    print("\n[Task: Translation]")
    english = "The weather is beautiful today."
    print("Formatted Input:", format_instruction_data("translation", english))
    print("Expected T5 Output: Le temps est magnifique aujourd'hui.")
    
    # 2. Sentiment
    print("\n[Task: Sentiment Analysis]")
    review = "I waited in line for 3 hours and the food was cold."
    print("Formatted Input:", format_instruction_data("sentiment", review))
    print("Expected T5 Output: negative")
    
    # 3. Question Answering
    print("\n[Task: Question Answering]")
    qa_data = {
        "context": "The Eiffel Tower is located in Paris, France. It was built in 1889.",
        "question": "When was the tower constructed?"
    }
    print("Formatted Input:", format_instruction_data("qa", qa_data))
    print("Expected T5 Output: 1889")

if __name__ == "__main__":
    test_t5_formatting()
```

### Key Takeaways from Code:
1. **No Output Layers:** Notice that we don't have a specific `nn.Linear(512, 2)` classifier for sentiment analysis. We literally just ask the model to generate the English word `"negative"`.
2. **Prompt Engineering:** Because the model was trained on these specific string formats, the way you phrase the prompt drastically alters the weights activated in the model. This is the birth of Prompt Engineering!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: HuggingFace Pipeline
You've formatted the data. Now run it.
**Your Task:**
1. Mentally run `pip install transformers`.
2. Load a pre-trained T5 model using HuggingFace's pipeline: 
   `from transformers import pipeline`
   `model = pipeline("text2text-generation", model="google/flan-t5-small")`
3. Pass your formatted string: `"translate English to German: How are you?"` into the pipeline.
4. Experiment with different instructions. Try to trick the model with tasks it might not know!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Compare the Text-to-Text paradigm (T5) with Task-Specific Heads (BERT). What are the production trade-offs in terms of model management, serving infrastructure, and cost?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Model Management (The Winner: T5):** 
   - State that with BERT, if your company has 50 <abbr title="Natural Language Processing">NLP</abbr> tasks (NER, Sentiment, Classification), you must manage, version, and store 50 separate fine-tuned BERT models. 
   - With T5, you manage exactly **ONE** model. You just change the string prompt.
2. **Serving Infrastructure (The Winner: T5):**
   - Explain that serving 50 BERT models requires massive VRAM routing. With T5, you can batch requests from completely different tasks (a translation request and a sentiment request) into the exact same GPU matrix multiplication, maximizing GPU utilization!
3. **Cost and Latency (The Winner: BERT):**
   - Conclude that T5 is an Encoder-Decoder model. It generates text autoregressively, which requires a KV-Cache and sequential generation steps. 
   - BERT only requires a single forward pass through an Encoder. Therefore, for a strict, high-speed classification task, BERT is significantly faster and cheaper to run than T5.

---
**Task for the end of the day:** Commit your code to Git. You now understand how raw <abbr title="Artificial Intelligence">AI</abbr> becomes a conversational assistant!

Tomorrow, in **Day 71**, we leave text behind. Can a Transformer process an Image? Yes! We will build the **Vision Transformer (ViT)** and the famous **CLIP** model!
