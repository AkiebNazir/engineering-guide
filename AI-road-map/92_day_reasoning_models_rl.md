# Day 92: Reasoning Models (RL-trained)

Welcome to Day 92. Over the past few weeks, we've explored how Large Language Models are pre-trained on massive datasets and fine-tuned for conversational instruction following. Today, we leap into the frontier of AI capabilities: **Reasoning Models** trained via Reinforcement Learning, such as OpenAI's o1 and DeepSeek-R1.

Unlike standard LLMs that generate the next token almost instantaneously based on pattern matching, reasoning models are trained to "think" before they speak. They do this by scaling *test-time compute*.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Limitation of Standard LLMs
Standard LLMs operate in a "System 1" thinking mode (fast, intuitive, pattern-matching). If you ask a complex math question, the model must output the answer token-by-token in a single forward pass without pausing to "think." 
If the immediate next token happens to be wrong, the entire subsequent generation is derailed. 

### 2. What is Test-Time-Compute Scaling?
In traditional AI development, models get smarter by scaling *training-time compute* (bigger datasets, more GPUs, more parameters). 
Reasoning models introduce a new axis: **Test-Time-Compute Scaling**. This means giving the model more time to compute *during inference*.

The model is allowed to generate a hidden "Chain of Thought" (CoT) before outputting the final answer. It can:
- Break the problem into sub-steps.
- Try a solution and recognize if it hit a dead end.
- Backtrack and try a different approach.
- Verify its own logic.

### 3. How are Reasoning Models Trained?
You cannot just prompt an LLM to "think step by step" to get an o1-level model. True reasoning models are trained using large-scale **Reinforcement Learning (RL)**.
1. **The Environment:** A massive dataset of STEM problems (Math, Coding, Logic) where the final answer can be programmatically verified (e.g., unit tests pass, or math formula matches).
2. **The Policy:** The LLM itself.
3. **The Reward:** The LLM is given a complex problem. It generates a long, meandering chain of thought. If the final answer is correct, it gets a massive positive reward. If it's wrong, a negative reward.

Through millions of RL episodes (using algorithms like PPO or GRPO), the model learns that generating a structured, self-correcting chain of thought *maximizes* its reward. It learns to "think" organically.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a mock script that demonstrates the conceptual difference between a standard LLM generation and a Reasoning Model (o1-style) generation process.

Create a file named `reasoning_model_sim.py`:

```python
import time

class StandardLLM:
    def generate(self, prompt):
        print(f"Standard LLM receiving: {prompt}")
        print("Generating immediate answer (System 1)...")
        time.sleep(1) # Fast inference
        # If it didn't immediately guess the trick, it fails.
        return "The answer is 12."

class ReasoningModel:
    def generate(self, prompt):
        print(f"\nReasoning Model receiving: {prompt}")
        print("Initiating hidden Chain of Thought (System 2)...\n")
        
        # Simulating test-time compute scaling
        thoughts = [
            "Let's break this down into steps.",
            "First, I need to calculate the area of the base. Area = pi * r^2.",
            "Wait, the problem gives diameter, not radius. Let me correct that.",
            "Radius = Diameter / 2. So radius is 5.",
            "Area = 3.14 * 25 = 78.5.",
            "Now, let's look at the height..."
        ]
        
        for thought in thoughts:
            print(f"<thinking> {thought} </thinking>")
            time.sleep(1) # Simulating compute time spent on reasoning
            
        print("\nChain of thought complete. Generating final answer...")
        time.sleep(0.5)
        return "The answer is 78.5."

def simulate_inference():
    prompt = "Calculate the area of a circle with a diameter of 10."
    
    standard_model = StandardLLM()
    print("Final Output:", standard_model.generate(prompt))
    
    reasoning_model = ReasoningModel()
    print("Final Output:", reasoning_model.generate(prompt))

if __name__ == "__main__":
    simulate_inference()
```

### Key Takeaways from Code:
1. **Latency for Accuracy:** The reasoning model is significantly slower. It trades latency for a massive boost in accuracy on complex tasks.
2. **Self-Correction:** The reasoning model can catch its own mistakes (e.g., using diameter instead of radius) *before* committing to a final answer.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Group Relative Policy Optimization (GRPO)
DeepSeek-R1 popularized an RL algorithm called **GRPO** for training reasoning models, which is much more memory efficient than PPO.
**Your Task:**
1. Research how GRPO differs from PPO.
2. Specifically, look into how GRPO eliminates the need for a massive, memory-hungry "Value Model" (Critic) by normalizing rewards across a group of sampled outputs.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Why are reinforcement learning techniques like PPO or GRPO better suited for training reasoning models than pure Supervised Fine-Tuning (SFT) on high-quality reasoning traces?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Limitation of Imitation:** SFT is just imitation learning. The model learns to mimic the *style* of human reasoning, but not the *substance*. It might generate text that looks like a mathematical proof without actually doing the math.
2. **Discovering Novel Strategies:** RL allows the model to explore and discover reasoning strategies that human annotators might never have thought of. It optimizes directly for the *outcome* (getting the right answer) rather than the *process* (mimicking a human).
3. **Data Scarcity:** It is incredibly expensive and difficult to get humans to write out exhaustive, perfect, step-by-step reasoning traces for complex math and coding problems. RL sidesteps this by using programmatic verification (unit tests, math checkers) as the reward signal, allowing the model to generate its own training data through exploration.

---
**Task for the end of the day:** Commit your notes and code to Git. 

Tomorrow, we will explore how these massive models are actually served in production environments efficiently.
