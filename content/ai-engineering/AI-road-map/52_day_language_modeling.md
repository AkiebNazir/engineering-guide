# Day 52: Language Modeling & Perplexity

Welcome to Day 52. We are officially done with classifying text. 
Today, we learn the exact mathematical objective that trains ChatGPT. We enter the world of predicting the future: **Language Modeling**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Goal of Language Modeling
The goal of a Language Model is mathematically incredibly simple: 
**Given a sequence of words ($w_1, w_2, w_3$), predict the probability of the *next* word ($w_4$).**

If I give you the sequence: *"The cat sat on the"*, you instantly know the next word is highly likely to be *"mat"* or *"floor"*, and highly unlikely to be *"spaceship"*. You are running a Language Model in your brain.

### 2. The Old Way: N-gram Models & Smoothing
Before Neural Networks, we used pure statistics. 
An **N-gram Language Model** (e.g., a Trigram model) simply looks at Wikipedia and counts. 
If the AI wants to know the probability of *"mat"* following *"sat on the"*, it counts how many times *"sat on the mat"* appears in Wikipedia, and divides it by how many times *"sat on the"* appears.
- **The Fatal Flaw (Sparsity):** What if the phrase *"sat on the spaceship"* never appeared in Wikipedia? The math evaluates to $0 / 10 = 0.0\%$. The AI mathematically believes the sentence is impossible! 
- **Smoothing:** To prevent $0.0\%$, researchers used "Laplace Smoothing" (adding +1 to every count) or "Kneser-Ney Smoothing" to borrow probabilities from smaller N-grams. It was a mathematical hack.

### 3. The New Way: Neural Language Models
In 2003, Yoshua Bengio invented the Neural Language Model. 
Instead of counting raw words, the AI passes the words through **Word Embeddings** (Day 48). 
Because the Embeddings teach the AI that "Cat" and "Dog" are geometrically identical, if the AI has seen *"The dog sat on the spaceship"*, it can successfully predict *"The cat sat on the spaceship"* even if that exact sequence has never appeared in human history! 

### 4. Perplexity (PPL): How to Grade an LLM
If an AI takes an exam, we grade it using "Accuracy" (e.g., 90%). 
You cannot use Accuracy for Language Modeling because language is subjective. There is no single "correct" next word. 
We grade Language Models using **Perplexity (PPL)**.
- **The Math:** $\text{PPL} = \exp(\text{Cross Entropy Loss})$. (Or $2^H$).
- **The Intuition:** If a model has a Perplexity of `10`, it means that when it tries to guess the next word, it is mathematically as confused as if it were rolling a 10-sided die. 
- You want Perplexity to be as **low** as possible! A perfect model has a Perplexity of 1.0 (it is absolutely certain of the next word).

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Neural Language Model using an LSTM. We will train it to predict the next word, and we will write the exact formula to calculate its Perplexity!

Create a file named `language_model.py`:

```python
import torch
import torch.nn as nn
import math

class NeuralLanguageModel(nn.Module):
    """
    Predicts the next word in a sequence.
    The exact architecture that paved the way for GPT!
    """
    def __init__(self, vocab_size, embed_dim, hidden_size):
        super().__init__()
        
        # Turn the input words into coordinates
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        
        # The LSTM reads the sequence and builds a memory of the context
        self.lstm = nn.LSTM(embed_dim, hidden_size, batch_first=True)
        
        # The Classifier predicts the NEXT word out of the entire dictionary
        self.fc = nn.Linear(hidden_size, vocab_size)

    def forward(self, x, hidden=None):
        # x shape: [Batch, Seq_Len]
        embeds = self.embedding(x)
        
        # output shape: [Batch, Seq_Len, Hidden_Size]
        # The LSTM outputs a prediction state for EVERY word in the sequence!
        lstm_out, hidden = self.lstm(embeds, hidden)
        
        # Predict the probability of the next word for every step
        # logits shape: [Batch, Seq_Len, Vocab_Size]
        logits = self.fc(lstm_out)
        
        return logits, hidden

def calculate_perplexity(loss_tensor):
    """
    Converts raw Cross Entropy Loss into human-readable Perplexity.
    """
    # PPL = e^(Loss)
    return math.exp(loss_tensor.item())

def test_language_model():
    print("--- RUNNING NEURAL LANGUAGE MODEL ---")
    
    VOCAB_SIZE = 5000
    BATCH_SIZE = 2
    SEQ_LEN = 10
    
    # 1. Simulate the data
    # Input: "The cat sat on the mat and went to sleep"
    input_seq = torch.randint(0, VOCAB_SIZE, (BATCH_SIZE, SEQ_LEN))
    
    # Target: "cat sat on the mat and went to sleep <END>"
    # Notice the target is the exact same sequence, just shifted to the left by 1!
    target_seq = torch.randint(0, VOCAB_SIZE, (BATCH_SIZE, SEQ_LEN))
    
    # 2. Forward Pass
    model = NeuralLanguageModel(vocab_size=VOCAB_SIZE, embed_dim=128, hidden_size=256)
    logits, _ = model(input_seq)
    
    # 3. Calculate Loss and Perplexity
    # PyTorch CrossEntropy expects shapes: (Batch*SeqLen, Vocab_Size) and (Batch*SeqLen)
    criterion = nn.CrossEntropyLoss()
    
    flattened_logits = logits.view(-1, VOCAB_SIZE)
    flattened_targets = target_seq.view(-1)
    
    loss = criterion(flattened_logits, flattened_targets)
    ppl = calculate_perplexity(loss)
    
    print(f"Raw Cross Entropy Loss: {loss.item():.4f}")
    print(f"Perplexity (PPL): {ppl:.2f}")
    print("\nRight now, the untrained model is guessing randomly out of 5000 words.")
    print("Therefore, its Perplexity should be approximately 5000!")

if __name__ == "__main__":
    test_language_model()
```

### Key Takeaways from Code:
1. **The Target Shift:** Look closely at the data setup. Language Models don't need human labels! They use **Self-Supervised Learning**. The "Target" label is literally just the original text shifted by one word to the left. The internet contains trillions of words, meaning we have infinite free training data!
2. **Flattening for Loss:** `logits.view(-1, VOCAB_SIZE)`. When evaluating a sequence, we flatten the `Batch` and `Seq_Len` dimensions together. We calculate the loss for every single word prediction simultaneously.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Autocomplete Generation
You trained the model. Now you must use it to generate new text!
**Your Task:**
1. Given a starting word ID (e.g., `word = torch.tensor([[45]])`), pass it into the `NeuralLanguageModel`.
2. Grab the `logits` for that step. 
3. Apply `F.softmax(logits, dim=-1)` to get probabilities.
4. Use `torch.multinomial(probs, 1)` or `torch.argmax(probs)` to select the predicted next word ID.
5. Append the predicted word to a list.
6. Crucially, pass the new predicted word AND the `hidden` state back into the model for the next loop. Run this loop 10 times to generate a 10-word sentence!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"OpenAI releases a report stating GPT-4 achieved a Perplexity of 12.5 on a specific coding benchmark. What exactly does this number mathematically tell you? What does it NOT tell you? How would you evaluate the LLM beyond perplexity?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Math Meaning:** 
   - State that a Perplexity of 12.5 means that, on average, when GPT-4 was attempting to predict the next token in the coding benchmark, it had narrowed down the correct answer to a 1-in-12.5 guess. The lower the number, the more confident and accurate the model's internal probability distribution is.
2. **What it does NOT tell you (The Flaw):**
   - Explain that Perplexity only measures the model's ability to mimic the exact statistical distribution of the training data. 
   - It does **not** measure factual accuracy, logical reasoning, or safety. A model can have an amazing Perplexity of 2.0 while confidently generating grammatically perfect, highly-probable misinformation or toxic content!
3. **Beyond Perplexity (Evaluation):**
   - Conclude that LLMs must be evaluated using **Downstream Tasks** (e.g., MMLU for knowledge, HumanEval for code) and **Human/LLM-as-a-Judge Evaluation** (e.g., Chatbot Arena ELO ratings) to measure actual helpfulness and alignment to human intent.

---
**Task for the end of the day:** Commit your code to Git. You now understand the objective function of the most powerful AIs on earth.

Tomorrow, in **Day 53**, we step back to evaluate translation models. If we can't use Accuracy, how do we grade Google Translate? Welcome to **BLEU Scores and Data Augmentation!**
