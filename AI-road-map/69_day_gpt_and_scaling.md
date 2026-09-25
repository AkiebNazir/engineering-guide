# Day 69: GPT, Autoregressive Decoding & Scaling Laws

Welcome to Day 69. BERT won the classification war. But OpenAI placed their bets on the Transformer Decoder. They built **GPT** (Generative Pre-trained Transformer). 

Today, we learn how GPT mathematically generates human-like text, the math behind artificial "creativity", and the famous Scaling Laws that dictate the future of Artificial Intelligence.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Autoregressive Pre-training
GPT does not use `[MASK]` tokens. It is trained on one strict, brutal mathematical objective: **Next-Word Prediction**. 
$\mathcal{L} = -\sum_t \log p(x_t|x_{<t})$.
It reads a massive sequence of text from the internet, and at every single step, it is forced to predict the exact next word. Because it is physically blinded by the Causal Mask (Day 66), it is forced to develop deep logical reasoning to guess what comes next.

### 2. Decoding Strategies (The Math of Creativity)
When GPT predicts the next word, it outputs a probability distribution across 50,000 words. How do we pick the winner?
- **Greedy Search:** Always pick the #1 highest probability. This results in incredibly robotic, repetitive text (e.g., *"I went to the store and I went to the store"*).
- **Temperature ($T$):** We mathematically divide the raw output logits by $T$ *before* applying Softmax. 
  - If $T=0.1$ (Cold), the highest probability gets amplified to 99%. The AI is robotic and deterministic.
  - If $T=1.5$ (Hot), the probabilities flatten out. The #1 word might be 15%, and the #20 word might be 12%. The AI hallucinates highly creative (and sometimes crazy) text!
- **Top-K Sampling:** Even with high temperature, you don't want the AI to pick the 40,000th word (which might be gibberish). Top-K sorts the probabilities, throws away everything except the top 50 words, and samples randomly from those 50.
- **Top-P (Nucleus Sampling):** Top-K is flawed because sometimes there are only 3 logical words, and sometimes there are 100. Top-P dynamically adjusts. It sorts the words, and adds up their probabilities until the sum hits $0.90$ (90%). It throws away the rest!

### 3. The Chinchilla Scaling Laws
For years, companies just built bigger models (GPT-3 had 175 Billion parameters). 
But DeepMind researchers published a paper proving that the industry was doing it wrong. They derived the **Chinchilla Scaling Laws**.
They proved mathematically that if you double the parameters of a model, you **MUST** double the training tokens. 
If you have a 70 Billion parameter model, you must train it on at least 1.4 Trillion tokens to reach optimal intelligence. Most early massive models were severely under-trained!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build the math behind GPT's text generation! We will implement Temperature, Top-K, and Top-P Nucleus Sampling from scratch in PyTorch.

Create a file named `gpt_decoding.py`:

```python
import torch
import torch.nn.functional as F

def apply_temperature(logits, temperature=1.0):
    """
    Divides the logits by the temperature.
    T < 1.0 makes the AI confident/robotic.
    T > 1.0 makes the <abbr title="Artificial Intelligence">AI</abbr> creative/chaotic.
    """
    return logits / temperature

def top_k_filtering(logits, top_k=50):
    """
    Throws away all words except the top K most likely words.
    """
    # Find the value of the Kth largest logit
    top_k_values, _ = torch.topk(logits, top_k)
    kth_value = top_k_values[:, -1].unsqueeze(-1)
    
    # Overwrite everything smaller than the Kth value with Negative Infinity!
    # When Softmax runs, these will become exactly 0.0% probability.
    logits = torch.where(logits < kth_value, torch.tensor(float('-inf')), logits)
    
    return logits

def top_p_filtering(logits, top_p=0.9):
    """
    Nucleus Sampling. Keeps the top words until their cumulative probability hits P.
    """
    # 1. Sort the logits descending
    sorted_logits, sorted_indices = torch.sort(logits, descending=True)
    
    # 2. Convert to probabilities and calculate the cumulative sum
    cumulative_probs = torch.cumsum(F.softmax(sorted_logits, dim=-1), dim=-1)
    
    # 3. Find the indices to remove (everything AFTER the cumulative sum exceeds top_p)
    # We shift the mask by 1 to ensure we keep the word that pushes us over the threshold
    sorted_indices_to_remove = cumulative_probs > top_p
    sorted_indices_to_remove[..., 1:] = sorted_indices_to_remove[..., :-1].clone()
    sorted_indices_to_remove[..., 0] = 0
    
    # 4. Scatter the negative infinities back into the original logits tensor!
    indices_to_remove = sorted_indices_to_remove.scatter(1, sorted_indices, sorted_indices_to_remove)
    logits[indices_to_remove] = float('-inf')
    
    return logits

def test_decoding():
    print("--- RUNNING GPT DECODING STRATEGIES ---")
    
    # Simulate the raw logit output of GPT for a single word prediction
    # Vocab size of 10 for simplicity
    raw_logits = torch.tensor([[5.0, 4.0, 3.5, 2.0, 1.0, 0.5, 0.1, -1.0, -2.0, -3.0]])
    
    print("Original Probabilities:")
    print(torch.round(F.softmax(raw_logits, dim=-1) * 100))
    
    # Apply high temperature (Creative)
    hot_logits = apply_temperature(raw_logits.clone(), temperature=2.0)
    print("\nTemperature=2.0 Probabilities (Notice how it flattened out!):")
    print(torch.round(F.softmax(hot_logits, dim=-1) * 100))
    
    # Apply Top-K (K=3)
    k_logits = top_k_filtering(raw_logits.clone(), top_k=3)
    print("\nTop-K=3 Probabilities (Everything else is 0!):")
    print(torch.round(F.softmax(k_logits, dim=-1) * 100))
    
    # Apply Top-P (P=0.9)
    p_logits = top_p_filtering(raw_logits.clone(), top_p=0.90)
    print("\nTop-P=0.90 Probabilities (Dynamic cutoff!):")
    print(torch.round(F.softmax(p_logits, dim=-1) * 100))

if __name__ == "__main__":
    test_decoding()
```

### Key Takeaways from Code:
1. **The `-inf` Masking:** In all of these strategies, we never actually delete numbers from the tensor (that would break the math). We just overwrite the bad words with `-inf`. When we run `F.softmax()`, $e^{-\infty}$ mathematically evaluates to exactly $0.0$, completely removing that word from the AI's selection pool!
2. **Dynamic Cutoff:** Look at Top-P. If the #1 word has 95% probability, Top-P will instantly throw away *all other words* because the sum has already exceeded 90%. But if the top 10 words all have 9% probability, Top-P will keep all 10! It dynamically adjusts the "creativity" based on the AI's confidence!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Repetition Penalty
Even with Top-P, GPT sometimes gets stuck in a loop repeating the same word.
**Your Task:**
1. Create a function `apply_repetition_penalty(logits, generated_sequence, penalty=1.2)`.
2. `generated_sequence` is a list of token IDs the AI has already written.
3. Loop through the `generated_sequence`. For every ID in that sequence, find its corresponding logit in the `logits` tensor.
4. If the logit is $> 0$, divide it by the penalty ($1.2$). If it is $< 0$, multiply it by the penalty.
5. This mathematically shrinks the probability of any word the <abbr title="Artificial Intelligence">AI</abbr> has *already* used, forcing it to expand its vocabulary!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Explain the Chinchilla scaling laws. Given a massive compute budget of $10^{23}$ FLOPs, how would you determine the optimal model size (Parameters) and the required training data (Tokens)?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The FLOPs Equation:** 
   - State the fundamental equation for training compute: $C \approx 6 \times N \times D$ (Compute = 6 $\times$ Parameters $\times$ Tokens).
2. **The Chinchilla Discovery:**
   - Explain that prior to Chinchilla, companies scaled $N$ (Parameters) much faster than $D$ (Tokens). 
   - DeepMind proved that to achieve compute-optimal training, the ratio must be roughly **20 tokens for every 1 parameter**. Scaling must be proportional: $N \propto C^{0.5}$ and $D \propto C^{0.5}$.
3. **The Budget Allocation:**
   - Conclude that given $10^{23}$ FLOPs, you use the formulas $C = 6ND$ and $D = 20N$. 
   - $10^{23} = 6 \times N \times (20N) = 120 N^2$. 
   - Solving for $N$ gives roughly a 30 Billion parameter model trained on 600 Billion tokens. (Any larger model trained with this budget would be mathematically under-trained!).

---
**Task for the end of the day:** Commit your code to Git. You have mastered the math of <abbr title="Artificial Intelligence">AI</abbr> text generation.

Tomorrow, in **Day 70**, we learn how to turn this raw text-generation engine into a helpful <abbr title="Artificial Intelligence">AI</abbr> assistant like ChatGPT. We will learn about **T5, Span Corruption, and Instruction Tuning!**
