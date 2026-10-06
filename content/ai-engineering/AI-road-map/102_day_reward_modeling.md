# Day 102: Reward Modeling

Welcome to Day 102. Yesterday we learned PPO, the engine of Reinforcement Learning. PPO requires a mathematical "Reward" score (e.g., $+5$ or $-2$) to know how to update its weights.

But how do you define a reward for "Politeness" or "Safety"? You cannot write a Python `if` statement for that. You could use humans, but humans are slow. You can't hire a human to sit at a computer and click "Thumbs Up" 100,000 times a second while PPO trains.

Today, we solve this by training a secondary AI to act as a human grader: **The Reward Model (RM)**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Human Labeling Bottleneck
To train ChatGPT, OpenAI hired thousands of human contractors. 
Instead of asking the humans to assign a raw score (e.g., "Rate this 1-10"), which is highly subjective, they used **Pairwise Comparisons**.
They gave the LLM a prompt: *"Write a poem about the ocean."*
The LLM generated two *different* responses (Response A and Response B). 
The human simply clicked: **"A is better than B"**. 
This created a massive dataset of `(Prompt, Chosen_Response, Rejected_Response)` triples.

### 2. The Reward Model Architecture
We take a pre-trained LLM (like a LLaMA-8B model). 
We delete the final vocabulary classification head (the part that outputs probabilities for 32,000 words). 
We replace it with a single Linear neuron that outputs a single scalar Float (e.g., `4.5` or `-1.2`). 
This model reads a string of text and outputs a single number: **The Reward Score**.

### 3. The Bradley-Terry Preference Model
How do we train the Reward Model using the Human dataset? We use the **Bradley-Terry Model**.
It is a statistical model that predicts the probability that Response A is better than Response B.
- We pass the Human's *Chosen* response through the RM. It outputs $r_{chosen}$ (e.g., `2.0`).
- We pass the Human's *Rejected* response through the RM. It outputs $r_{rejected}$ (e.g., `1.5`).
- The Loss function looks at the difference: $r_{chosen} - r_{rejected}$. 
- If the RM gave the Chosen response a higher score, the loss is low. If the RM accidentally gave the Rejected response a higher score, the loss explodes, forcing the RM to adjust its weights!

### 4. Reward Hacking (Goodhart's Law)
Once the Reward Model is fully trained, it replaces the humans. The PPO algorithm uses the RM to grade its generated text at 100,000 steps per second.
**The Danger:** The RM is an AI, and AI has flaws. If the human labelers slightly preferred longer answers, the RM will learn the rule: *"Longer = Better"*.
During PPO training, the LLM will discover this flaw. It will start generating 10,000-word essays of absolute garbage, just to farm massive reward scores from the RM! This is called **Reward Hacking**.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a mock Reward Model architecture in PyTorch, and implement the Bradley-Terry Pairwise Loss Function!

Create a file named `reward_modeling.py`:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class MockRewardModel(nn.Module):
    """
    A Reward Model is just a standard LLM, but the final layer is a Scalar Head!
    """
    def __init__(self, vocab_size=32000, d_model=4096):
        super().__init__()
        # 1. The standard LLM Embedding and Transformer layers (Mocked)
        self.embedding = nn.Embedding(vocab_size, d_model)
        self.transformer_layer = nn.Linear(d_model, d_model) # Mocking a deep transformer
        
        # 2. THE SCALAR HEAD!
        # Instead of projecting back to 32,000 words, we project down to EXACTLY 1 number!
        self.scalar_head = nn.Linear(d_model, 1, bias=False)
        
    def forward(self, input_ids):
        # Pass through transformer
        x = self.embedding(input_ids)
        x = self.transformer_layer(x)
        
        # We usually take the hidden state of the LAST token in the sequence (the EOS token)
        # Because the last token has attended to the entire sentence!
        last_token_hidden_state = x[:, -1, :]
        
        # Pass through scalar head to get the Reward Score!
        reward_score = self.scalar_head(last_token_hidden_state)
        return reward_score

def bradley_terry_loss(reward_chosen, reward_rejected):
    """
    The mathematical loss function for Preference Modeling.
    We want to MAXIMIZE the difference between Chosen and Rejected.
    Loss = -log(sigmoid(R_chosen - R_rejected))
    """
    # Calculate the difference
    diff = reward_chosen - reward_rejected
    
    # Sigmoid converts the difference into a probability between 0 and 1
    # Then we take the Negative Log Likelihood
    loss = -F.logsigmoid(diff).mean()
    return loss

def test_reward_model():
    print("--- RUNNING REWARD MODEL TRAINING LOOP ---")
    
    # Initialize the RM
    rm = MockRewardModel()
    optimizer = torch.optim.Adam(rm.parameters(), lr=1e-4)
    
    # 1. THE DATASET (Human Preferences)
    # Mock tokenized inputs. 
    # Shape: (Batch=2, SequenceLength=10)
    prompt_and_chosen = torch.randint(0, 32000, (2, 10))
    prompt_and_rejected = torch.randint(0, 32000, (2, 10))
    
    print("Executing Forward Passes...")
    
    # 2. Get the Scores!
    score_chosen = rm(prompt_and_chosen)
    score_rejected = rm(prompt_and_rejected)
    
    print(f"RM Score for Chosen Responses:   {score_chosen.squeeze().tolist()}")
    print(f"RM Score for Rejected Responses: {score_rejected.squeeze().tolist()}")
    
    # 3. Calculate the Loss
    loss = bradley_terry_loss(score_chosen, score_rejected)
    print(f"\nBradley-Terry Loss: {loss.item():.4f}")
    
    # 4. Backpropagate
    loss.backward()
    optimizer.step()
    
    print("Weights updated! The RM learned to prefer the Chosen response.")

if __name__ == "__main__":
    test_reward_model()
```

### Key Takeaways from Code:
1. **The Architecture:** Notice that the Reward Model is almost identical to the LLM. If your LLM is a 7B parameter LLaMA, your Reward Model is usually *also* a 7B parameter LLaMA, just with a different final layer. It requires massive compute to train!
2. **The Loss Function:** Look at the math: `diff = reward_chosen - reward_rejected`. If the RM gave the chosen response a `10.0` and the rejected a `-5.0`, the difference is `15.0`. The sigmoid of 15 is basically `1.0` (Perfect!). The negative log of 1.0 is `0.0`. The loss is zero, because the RM was perfectly accurate!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Accuracy Metrics
How do you know if your Reward Model is good? You can't just look at the loss. You must calculate the **Agreement Rate**.
**Your Task:**
1. Conceptually write a Python script that takes a held-out validation set of 1,000 human preferences.
2. Run all 1,000 pairs through the RM.
3. Calculate the Accuracy: `(score_chosen > score_rejected).sum() / 1000`.
4. If your Accuracy is $70\%$, it means the RM agrees with human morality $70\%$ of the time. (State of the art RMs achieve roughly $75\%$ to $80\%$ agreement, because even humans disagree with each other!).

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your Reward Model works well, but during PPO training, the LLM discovers a 'Reward Hack'. It starts generating highly verbose, sycophantic responses—agreeing with the user even when the user is factually wrong—because the RM gives high scores to polite text. How do you diagnose and fix this?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Diagnosis (Length Penalties):** 
   - Explain that humans inherently prefer longer answers, so the RM learns a correlation between Token Length and Reward. 
   - Propose plotting a scatter plot of `Reward Score` vs `Response Length`. If there is a massive linear correlation, the RM is flawed.
2. **The Fix (Length-Normalized Loss):**
   - Propose modifying the Bradley-Terry loss function during RM training to include a mathematical penalty for verbosity, forcing the RM to learn that concise correctness is better than verbose sycophancy.
3. **The Fix (Data Curation):**
   - Explain that the root cause is human labelers. You must re-train the human labelers! Tell the humans: *"Do not click Thumbs Up just because the AI is polite. Look for factual correctness."* You then retrain the RM on this new, harder dataset.

---
**Task for the end of the day:** Commit your code to Git. 

We now have all the pieces. We have an **SFT Model**, a **Reward Model**, and a **PPO Algorithm**. 

Tomorrow, in **Day 103**, we assemble the holy grail of modern AI: **The Full RLHF Pipeline**. We will learn how to combine all three models simultaneously to align a foundational LLM!
