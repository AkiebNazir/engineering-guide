# Day 106: LLM Evaluation & Contamination

Welcome to Day 106. We have a fully trained, fine-tuned, aligned, and safe model. 

Is it actually good? You cannot evaluate an LLM using standard software unit tests because language is inherently open-ended and subjective. 
If your CEO asks: *"Is our model smarter than LLaMA 3?"*, how do you mathematically prove it?

Today, we face the final boss of AI Engineering: **LLM Evaluation, Benchmarks, and Data Contamination**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Benchmark Taxonomy
To measure intelligence, the industry created standardized tests:
- **MMLU (Massive Multitask Language Understanding):** 57 subjects ranging from elementary math to professional law and medicine. (Multiple Choice).
- **GSM8k:** Grade School Math word problems. Tests multi-step reasoning.
- **HumanEval:** Python coding challenges. The LLM must write a function to pass a hidden set of unit tests.
- **TruthfulQA:** Tests if the model mimics human falsehoods (e.g., *"If you crack your knuckles, what happens?"* -> Bad models say *"Arthritis"*. Good models say *"Nothing"*).

### 2. The Nightmare of Data Contamination
If your model scores $90\%$ on MMLU, did it actually learn physics, or did it just memorize the answer key?
LLMs are trained on 15 Trillion tokens scraped from the internet. The MMLU benchmark is posted publicly on GitHub! **It is almost mathematically guaranteed that the test answers were in your training data!**
This is called **Data Contamination** (or Data Leakage). 
Before training, you must run an **N-Gram Overlap check**. You hash every 13-word sequence in your Test Set, and search your Petabytes of training data. If you find a match, you physically delete it from the training corpus!

### 3. LLM-as-a-Judge (MT-Bench)
Static multiple-choice benchmarks are easily gamed. The modern standard for evaluating Chatbots is **MT-Bench (Multi-Turn Benchmark)**. 
- You ask the LLM a complex, open-ended question (e.g., *"Draft a polite email declining a job offer."*).
- You take the LLM's response, and you feed it into **GPT-4**.
- You prompt GPT-4: *"You are an impartial judge. Grade this response on a scale of 1 to 10 based on helpfulness and tone."*
GPT-4's automated grades correlate with human preferences $85\%$ of the time, allowing you to run 10,000 evaluations for \$50!

### 4. Chatbot Arena (ELO Rating)
The ultimate, un-gameable test. UC Berkeley created the Chatbot Arena.
- A real human on the internet types a prompt.
- **Model A** and **Model B** (hidden identities) generate responses side-by-side.
- The human clicks *"A is better"*.
- The arena uses the **ELO Rating System** (invented for Chess) to mathematically rank the models on a global leaderboard. This is the only benchmark the industry truly trusts.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's implement an **LLM-as-a-Judge Pairwise Evaluation** script. 
We will simulate passing two responses into GPT-4, having it declare a winner, and then we will implement the actual math for calculating an ELO rating update!

Create a file named `llm_eval.py`:

```python
import random

def mock_gpt4_judge(prompt, response_a, response_b):
    """
    Simulates GPT-4 acting as an impartial judge between two models.
    """
    print(f"GPT-4 is evaluating the responses...")
    # In reality, this is an API call with a massive system prompt!
    
    # Let's say Response A was slightly more helpful
    return "A"

def calculate_elo_update(rating_a, rating_b, winner, k_factor=32):
    """
    The Chess ELO Math!
    If a weak model beats a strong model, it steals massive points.
    If a strong model beats a weak model, it only gains a few points.
    """
    # 1. Calculate Expected Win Probability for A and B
    # Formula: 1 / (1 + 10^((Rating_B - Rating_A) / 400))
    expected_a = 1 / (1 + 10 ** ((rating_b - rating_a) / 400))
    expected_b = 1 / (1 + 10 ** ((rating_a - rating_b) / 400))
    
    # 2. Determine actual outcome (1 for win, 0 for loss)
    actual_a = 1 if winner == "A" else 0
    actual_b = 1 if winner == "B" else 0
    
    # 3. Update Ratings!
    new_rating_a = rating_a + k_factor * (actual_a - expected_a)
    new_rating_b = rating_b + k_factor * (actual_b - expected_b)
    
    return round(new_rating_a), round(new_rating_b)

def test_evaluation():
    print("--- RUNNING LLM-AS-A-JUDGE ARENA ---\n")
    
    # Initial Setup
    prompt = "Explain quantum computing to a 5-year-old."
    model_a_name = "Our Fine-Tuned Model"
    model_b_name = "Base LLaMA 3"
    
    print(f"Prompt: '{prompt}'\n")
    print(f"Response A ({model_a_name}): 'Imagine a magical coin that is both heads and tails at the same time!'")
    print(f"Response B ({model_b_name}): 'Quantum computing utilizes superposition and entanglement of qubits.'\n")
    
    # 1. The Judge Decide
    winner = mock_gpt4_judge(prompt, "Response A", "Response B")
    print(f"\n[JUDGE DECISION] The winner is: Response {winner}")
    
    # 2. Update the ELO Ratings!
    # Let's pretend Our Model is currently unranked (1000) and Base LLaMA is strong (1200)
    rating_our_model = 1000
    rating_base_llama = 1200
    
    print("\n--- ELO RATING UPDATE ---")
    print(f"Current Rating -> {model_a_name}: {rating_our_model} | {model_b_name}: {rating_base_llama}")
    
    # Calculate the massive upset!
    new_our, new_base = calculate_elo_update(rating_our_model, rating_base_llama, winner="A")
    
    print(f"New Rating     -> {model_a_name}: {new_our} | {model_b_name}: {new_base}")
    print(f"{model_a_name} gained {new_our - rating_our_model} points because it pulled off an upset!")

if __name__ == "__main__":
    test_evaluation()
```

### Key Takeaways from Code:
1. **Position Bias:** When using GPT-4 as a judge, it suffers from "Position Bias". It has a mathematical tendency to prefer whatever response you put in the "Response A" slot. To fix this, you must run the evaluation twice! Call GPT-4 with `(A, B)`, and then call it again with `(B, A)`. If it declares A the winner both times, it is a true win. If it flips its answer, it is a Tie!
2. **The K-Factor:** In ELO math, `k_factor=32` is standard. It determines the maximum amount of points a model can swing in a single match.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Custom Domain Evaluation
You cannot use MMLU to test a model fine-tuned for Medical Law.
**Your Task:**
1. Conceptually design an evaluation suite for a Medical Law LLM.
2. How do you create the golden answers? (Hint: Hire real Medical Lawyers to write 500 benchmark questions and the rubrics for grading them).
3. Write a System Prompt for GPT-4 to act as the Medical Judge, passing the Lawyer's rubric into the prompt so GPT-4 knows exactly how to grade it!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your model scores an incredible 85% on MMLU (beating GPT-4), but users in production complain that your model is worse and refuses to answer simple coding questions. How do you reconcile benchmark scores with user experience? Design a comprehensive evaluation strategy."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Diagnosis (Goodhart's Law & Overfitting):** 
   - State that the MMLU score is likely an illusion caused by Data Contamination or overfitting. The model memorized multiple-choice formats but lost conversational intelligence.
2. **Diagnosis (Alignment Tax):**
   - Explain the "Alignment Tax". If you apply too much Safety training (RLHF/DPO), the model becomes overly cautious. It refuses to write Python code because it thinks a simple `os.system()` call is a dangerous hacking attempt.
3. **The Comprehensive Evaluation Strategy:**
   - Propose abandoning static multiple-choice tests.
   - Implement an automated LLM-as-a-judge pipeline for internal CI/CD.
   - Implement **A/B Testing in Production** (Shadow Deployment). Send $5\%$ of user traffic to the new model, and measure the Implicit Feedback (e.g., do users copy/paste the code, or do they immediately regenerate?). If the copy/paste rate drops, roll back the deployment regardless of the MMLU score!

---

### 🎉 CONGRATULATIONS!
You have successfully completed **Days 97-106**!
You have mastered LoRA, QLoRA, Synthetic Data, PPO, DPO, Constitutional AI, and Evaluation!

You are officially a Senior LLM Engineer. You know how to take a raw statistical predictor and craft it into a safe, aligned, intelligent entity.

Take a deep breath. 
When you are ready, we will tackle the next block of the roadmap, diving into **Model Merging, Continuous Pre-Training, Speculative Decoding, and Multi-Agent Systems!**
