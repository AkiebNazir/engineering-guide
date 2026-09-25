# Day 103: The Full RLHF Pipeline

Welcome to Day 103. We have Supervised Fine-Tuning (SFT). We have a Reward Model (RM). We have the Proximal Policy Optimization (PPO) algorithm.

Today, we assemble the holy grail of modern <abbr title="Artificial Intelligence">AI</abbr>. We will combine all three pieces into the **Reinforcement Learning from Human Feedback (<abbr title="Reinforcement Learning from Human Feedback">RLHF</abbr>)** pipeline. This is exactly how OpenAI turned a raw, chaotic text-predictor (GPT-3) into the polite, helpful, and aligned ChatGPT.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Three Stages of <abbr title="Reinforcement Learning from Human Feedback">RLHF</abbr>
Let's review the complete pipeline from the famous InstructGPT paper:
- **Stage 1 (SFT):** Train the Base Model on 10,000 human-written (Prompt, Answer) pairs. It learns the Chat format.
- **Stage 2 (RM):** Collect 100,000 (Chosen, Rejected) pairs. Train a Reward Model to score them using the Bradley-Terry loss.
- **Stage 3 (PPO):** The <abbr title="Large Language Model">LLM</abbr> generates text. The RM scores it. The PPO algorithm updates the <abbr title="Large Language Model">LLM</abbr>'s weights.

### 2. The Four-Model VRAM Nightmare
During Stage 3 (PPO), you cannot just load the <abbr title="Large Language Model">LLM</abbr>. You must load **FOUR** massive neural networks into VRAM simultaneously!
1. **The Policy Model:** The <abbr title="Large Language Model">LLM</abbr> being trained (Requires Gradients).
2. **The Reward Model:** The frozen model that scores the text.
3. **The Value Model:** A secondary model used by PPO to predict the "Expected" reward of a state (so we can calculate the Advantage).
4. **The Reference Model:** A frozen copy of the original SFT model. Why do we need this? Read below!

### 3. The KL Divergence Penalty
If you let PPO optimize the Policy Model using only the Reward Model, the Policy Model will inevitably discover a **Reward Hack**. 
Perhaps the RM slightly favors the word "Therefore". PPO will mutate the Policy Model's weights until it literally outputs *"Therefore therefore therefore"* 500 times. It gets a massive $+100$ reward, but it has completely destroyed the English language!

**The Fix:** We keep a frozen copy of the original SFT model (The Reference Model). 
For every single word the Policy Model generates, we ask the Reference Model: *"What probability would you have assigned to this word?"*
We calculate the **Kullback-Leibler (KL) Divergence** (the difference between the two probability distributions). 
If the Policy Model deviates too far from the Reference Model, we apply a massive mathematical **Penalty** to the Reward! 

**The Final Reward Equation:** 
$R_{final} = \text{Reward}_{\text{Model}}(x, y) - \beta \cdot D_{KL}(\pi_{Policy} || \pi_{Reference})$

The KL Penalty forces the Policy Model to maximize the reward *while strictly maintaining its original grammar and intelligence!*

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's conceptually build the <abbr title="Reinforcement Learning from Human Feedback">RLHF</abbr> Stage 3 loop in Python. We will simulate generating text, calculating the Reward, applying the KL Penalty, and updating the model.

Create a file named `rlhf_pipeline.py`:

```python
import torch
import torch.nn.functional as F

def mock_generate(policy_model, prompt):
    # Simulates the LLM generating a response
    return "Here is a safe, helpful answer."

def mock_get_probabilities(model, prompt, response):
    # Simulates getting the logits/probabilities for the generated response
    # Shape: (Sequence_Length)
    return torch.tensor([0.8, 0.7, 0.9, 0.6, 0.85], requires_grad=True)

def calculate_kl_penalty(policy_probs, ref_probs):
    """
    Calculates how far the new model has drifted from the original SFT model.
    KL Divergence ≈ log(Policy_Prob / Ref_Prob)
    """
    # If Policy and Ref agree exactly, the ratio is 1.0. log(1.0) = 0.0 (No penalty!)
    # If Policy is 0.9 and Ref is 0.1, the ratio is 9.0. log(9.0) = 2.19 (Big penalty!)
    kl_div = torch.log(policy_probs / (ref_probs + 1e-8))
    return kl_div.mean()

def run_rlhf_loop():
    print("--- RUNNING RLHF (PPO) TRAINING LOOP ---")
    
    # 1. We must load 4 models into memory!
    # (Mocking the models as None for this conceptual script)
    policy_model = "Policy LLM (Trainable)"
    ref_model = "Reference SFT Model (Frozen)"
    reward_model = "Reward Model (Frozen)"
    
    print(f"Loaded: {policy_model}, {ref_model}, {reward_model}\n")
    
    prompt = "How do I bake a cake?"
    
    # 2. GENERATION
    print(f"User Prompt: '{prompt}'")
    response = mock_generate(policy_model, prompt)
    print(f"Policy Generated: '{response}'\n")
    
    # 3. GET PROBABILITIES
    policy_probs = mock_get_probabilities(policy_model, prompt, response)
    
    # We turn off gradients for the Reference Model!
    with torch.no_grad():
        ref_probs = torch.tensor([0.7, 0.75, 0.8, 0.65, 0.8])
        
    # 4. GET RM SCORE
    # The Reward Model evaluates the response and gives a scalar score
    with torch.no_grad():
        raw_reward = torch.tensor([8.5]) 
    print(f"Raw Reward Model Score: {raw_reward.item()}")
    
    # 5. CALCULATE KL PENALTY
    beta = 0.1 # The KL Penalty Coefficient
    kl_penalty = calculate_kl_penalty(policy_probs, ref_probs)
    print(f"KL Divergence Penalty: {kl_penalty.item():.4f}")
    
    # 6. CALCULATE FINAL REWARD
    final_reward = raw_reward - (beta * kl_penalty)
    print(f"Final Penalized Reward: {final_reward.item():.4f}\n")
    
    # 7. PPO UPDATE
    print("Passing Final Reward into PPO Algorithm...")
    # loss = calculate_ppo_loss(old_probs, policy_probs, final_reward)
    # loss.backward()
    # optimizer.step()
    
    print("Policy Model weights updated successfully! It is now slightly more Aligned.")

if __name__ == "__main__":
    run_rlhf_loop()
```

### Key Takeaways from Code:
1. **The Beta Coefficient:** Notice the `beta = 0.1` variable. Tuning this is an absolute nightmare for <abbr title="Machine Learning">ML</abbr> Engineers. If $\beta$ is too high, the model is terrified of the KL penalty, so it refuses to change its weights at all (it learns nothing). If $\beta$ is too low, the model ignores the penalty, reward-hacks the RM, and destroys its grammar!
2. **The Compute Bottleneck:** Because you have to run a Forward Pass through the Policy Model, the Reference Model, AND the Reward Model for every single training step, <abbr title="Reinforcement Learning from Human Feedback">RLHF</abbr> is incredibly slow.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: HuggingFace TRL
In production, nobody writes PPO from scratch. We use HuggingFace `trl` (Transformer Reinforcement Learning).
**Your Task:**
1. Review the documentation for `trl.PPOTrainer`.
2. Notice how it takes a `model` (Policy) and a `ref_model`.
3. Notice how you must manually call `ppo_trainer.generate()` to create the text, manually pass that text to your own Reward Model pipeline to get the scores, and then manually call `ppo_trainer.step(queries, responses, rewards)`. The library handles the horrific PPO and KL math for you!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Walk through the complete <abbr title="Reinforcement Learning from Human Feedback">RLHF</abbr> pipeline for a 70B model. How many total models must be loaded into VRAM simultaneously during the PPO phase? Estimate the massive VRAM bottleneck and propose a solution."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Four Models:** 
   - State that you must load the Policy Model (70B, trainable), Reference Model (70B, frozen), Reward Model (70B, frozen), and Value Model (70B, trainable).
2. **The VRAM Calculation:**
   - Explain that a 70B model in FP16 is $140\text{GB}$. 
   - 4 models $\times 140\text{GB} = 560\text{GB}$ just for the weights!
   - Plus Optimizer states for the Policy and Value models ($280\text{GB}$).
   - Total: $>800\text{GB}$ of VRAM! This requires a cluster of 16 A100s just to do <abbr title="Reinforcement Learning from Human Feedback">RLHF</abbr>!
3. **The Solution (<abbr title="Low-Rank Adaptation">LoRA</abbr> / <abbr title="Quantized Low-Rank Adaptation">QLoRA</abbr>):**
   - Propose using <abbr title="Parameter-Efficient Fine-Tuning">PEFT</abbr>! Freeze the Base Model. Train a <abbr title="Low-Rank Adaptation">LoRA</abbr> adapter for the Policy, a <abbr title="Low-Rank Adaptation">LoRA</abbr> adapter for the Reward Model, and a <abbr title="Low-Rank Adaptation">LoRA</abbr> adapter for the Value Model. 
   - Now you only load ONE massive 70B Base Model into VRAM, and hot-swap the tiny <abbr title="Low-Rank Adaptation">LoRA</abbr> adapters during the different passes! You just reduced the VRAM requirement from $800\text{GB}$ to $150\text{GB}$!

---
**Task for the end of the day:** Commit your code to Git. 

<abbr title="Reinforcement Learning from Human Feedback">RLHF</abbr> works, but as you just saw, it is an engineering nightmare. It is highly unstable, requires 4 models in memory, and the hyperparameters are nearly impossible to tune. 

In 2023, researchers at Stanford published a mathematical breakthrough that made <abbr title="Reinforcement Learning from Human Feedback">RLHF</abbr> obsolete overnight. 
Tomorrow, in **Day 104**, we learn **<abbr title="Direct Preference Optimization">DPO</abbr> (Direct Preference Optimization)**! We will align a model without a Reward Model and without PPO!
