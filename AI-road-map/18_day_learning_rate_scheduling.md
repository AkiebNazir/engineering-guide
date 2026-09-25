# Day 18: Learning Rate Scheduling & Warmup Strategies

Welcome to Day 18. Back in Day 15, you learned that the **Learning Rate ($\eta$)** is the absolute most important hyperparameter in <abbr title="Artificial Intelligence">AI</abbr>. 

If you guess a number that is too high, the model explodes to infinity. If you guess a number that is too low, the model takes a lifetime to train and gets stuck in terrible Local Minima.

The secret of modern <abbr title="Artificial Intelligence">AI</abbr>? **We stopped trying to guess a single perfect number.** Today, we learn how to write algorithms that dynamically warp and twist the learning rate while the model is training.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. The Classics: Step and Exponential Decay
In the early days of Deep Learning (2012-2016), engineers manually babysat their models.
- **Step Decay:** You train the model with an LR of $0.1$. When the Loss graph plateaus (stops going down), you manually cut the LR in half to $0.05$ to force the model to take smaller steps and settle deeper into the valley.
- **Exponential Decay:** Automating the process by multiplying the LR by $0.99$ at the end of every epoch.

### 2. Cosine Annealing
Instead of clunky steps, modern researchers prefer **Cosine Annealing**. It smoothly sweeps the learning rate from a high maximum down to a tiny minimum following the curve of a trigonometric Cosine wave.

**Algebraic Definition:**
$$ \eta_t = \eta_{min} + \frac{1}{2}(\eta_{max} - \eta_{min})\left(1 + \cos\left(\frac{\pi t}{T}\right)\right) $$

> **Mathematical Breakdown (Why this works):**
> - At $t = 0$ (the start of training), the math resolves to $\cos(0) = 1$. The equation becomes $\eta_{min} + \eta_{max} - \eta_{min}$, leaving exactly the **Maximum LR**. The model takes massive steps to quickly escape bad valleys.
> - At $t = T$ (the exact final step of training), the math resolves to $\cos(\pi) = -1$. The $1 + -1$ bracket becomes $0$, leaving exactly the **Minimum LR**. The model takes microscopic baby steps, perfectly landing in the dead center of the Global Minimum.

### 3. The Warmup Phase (Mandatory for LLMs)
If you train a massive Transformer (like ChatGPT) and you start with your Maximum LR on Step 1, the model will instantly explode and output `NaN` (Not a Number). 

Why? Because at initialization, all the weights in the massive network are completely random. A massive network with random weights produces terrifyingly huge, highly chaotic gradients. If you take a massive step using a chaotic gradient, you completely destroy the model's architecture.

**The Fix:** We use a **Warmup Phase**. We artificially force the LR to start at $0.0$. Over the first 2,000 steps, we slowly and linearly increase it until it hits the Maximum LR. This gives the random weights a chance to "settle down" before we hit the gas pedal!

### 4. The 1cycle Policy & Warm Restarts
- **1cycle Policy:** A famous hyper-optimization trick. You start at an LR of 0, ramp it up to a massive, almost dangerously high peak in the middle of training, and then drop it back to 0. That massive peak acts as the ultimate **Regularizer**—it violently bounces the model out of any sharp, poorly-generalizing valleys, forcing it to find a wide, flat valley!
- **Warm Restarts:** Imagine you are using Cosine Annealing and the LR hits zero. Instead of stopping training, you instantly reset the LR back to Maximum! This violently kicks the model out of whatever valley it was in, allowing it to explore a completely different part of the mountain range.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's write code to visualize these abstract mathematical schedules. You must see exactly what these curves look like to understand how they control the <abbr title="Artificial Intelligence">AI</abbr>.

Create a file named `lr_schedules.py`:

```python
import numpy as np
import matplotlib.pyplot as plt

def cosine_annealing(step, total_steps, lr_max, lr_min=0.0):
    """Calculates the exact LR for a given step using Cosine math."""
    cos_val = np.cos(np.pi * step / total_steps)
    return lr_min + 0.5 * (lr_max - lr_min) * (1 + cos_val)

def linear_warmup(step, warmup_steps, lr_max):
    """Linearly increases LR from 0 to lr_max."""
    return lr_max * (step / warmup_steps)

def generate_schedules():
    """Generates and plots the 4 most famous LR schedules."""
    print("--- GENERATING LEARNING RATE SCHEDULES ---")
    
    total_steps = 1000
    lr_max = 0.01
    
    # 1. Step Decay (Cut in half every 250 steps)
    step_decay = [lr_max * (0.5 ** (i // 250)) for i in range(total_steps)]
    
    # 2. Pure Cosine Annealing
    cosine = [cosine_annealing(i, total_steps, lr_max) for i in range(total_steps)]
    
    # 3. Linear Warmup + Cosine Annealing (The LLM Standard)
    warmup_steps = 200
    warmup_cosine = []
    for i in range(total_steps):
        if i < warmup_steps:
            warmup_cosine.append(linear_warmup(i, warmup_steps, lr_max))
        else:
            # Shift the cosine math to start AFTER the warmup
            adjusted_step = i - warmup_steps
            adjusted_total = total_steps - warmup_steps
            warmup_cosine.append(cosine_annealing(adjusted_step, adjusted_total, lr_max))
            
    # 4. Cosine Annealing with Warm Restarts
    restarts = []
    cycle_length = 250
    for i in range(total_steps):
        step_in_cycle = i % cycle_length
        restarts.append(cosine_annealing(step_in_cycle, cycle_length, lr_max))

    # Plotting
    plt.figure(figsize=(14, 8))
    
    plt.subplot(2, 2, 1)
    plt.plot(step_decay, 'r-', lw=2)
    plt.title("Step Decay (The Old Standard)")
    plt.ylabel("Learning Rate")
    
    plt.subplot(2, 2, 2)
    plt.plot(cosine, 'g-', lw=2)
    plt.title("Pure Cosine Annealing")
    
    plt.subplot(2, 2, 3)
    plt.plot(warmup_cosine, 'b-', lw=3)
    plt.title("Warmup + Cosine Decay (The LLM Standard)")
    plt.xlabel("Training Steps")
    plt.ylabel("Learning Rate")
    
    plt.subplot(2, 2, 4)
    plt.plot(restarts, 'purple', lw=2)
    plt.title("Cosine Annealing with Warm Restarts")
    plt.xlabel("Training Steps")
    
    plt.tight_layout()
    filename = "lr_schedules.png"
    plt.savefig(filename)
    print(f"Saved visualization to {filename}. Study the Warmup curve carefully!")

if __name__ == "__main__":
    generate_schedules()
```

### Key Takeaways from Code:
1. **The <abbr title="Large Language Model">LLM</abbr> Standard:** Look closely at the `Warmup + Cosine Decay` graph. This single curve is responsible for training GPT-4, Llama 3, and Claude. The steep upward slope protects the random weights. The gentle downward slope ensures the model perfectly converges.
2. **Warm Restarts:** Look at the purple graph. Notice the violent vertical lines resetting the LR to the maximum. If the model accidentally fell into a terrible Local Minimum during the first 250 steps, that sudden spike kicks the model right back out into the open to try again!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The LR Finder
**Your Task:** 
You have a dataset and a model, but you have no idea what `lr_max` should be. Is it $0.1$? $0.001$? $1e-5$?
1. Write a script that loops through 100 mini-batches of data.
2. Start the learning rate at a microscopic $1e-7$.
3. On every single step, exponentially increase the LR until it hits a massive $10.0$.
4. Record the Loss at every step and plot `Loss vs Learning Rate` on a log-scale graph.
5. **The Magic:** You will see the loss stay flat, then dramatically drop, and then suddenly violently spike upwards (when the LR gets too high and the model explodes). The perfect `lr_max` to use for your schedule is the point on the graph where the loss was dropping the fastest!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are the lead engineer tasked with training our new 7-Billion parameter Large Language Model from scratch. Design the complete Learning Rate schedule for this training run. Specifically outline your phases (Warmup, Peak, Decay, Cooldown) and mathematically justify why each phase is absolutely critical to the success of the model."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Phase 1: Linear Warmup (1-5% of training):** 
   - Start LR near 0 and ramp up linearly.
   - **Justification:** At initialization, a 7B parameter network has massive gradient variance. Without warmup, the Adam optimizer's momentum and variance trackers will permanently destabilize, and the model will suffer catastrophic divergence.
2. **Phase 2: The Peak:**
   - Hitting the maximum learning rate.
   - **Justification:** We need the LR to be as large as mathematically possible (without exploding) to act as implicit regularization, bouncing the <abbr title="Large Language Model">LLM</abbr> out of sharp local minima and forcing it to find a generalized, flat minimum.
3. **Phase 3: Cosine Decay (90% of training):**
   - Slowly decaying the LR down to about 10% of the peak value.
   - **Justification:** Cosine decay provides a much smoother descent than linear decay, ensuring the model's weights have time to slowly settle and refine their language representations.
4. **Phase 4: Cooldown (Final 5% of training):**
   - Holding the LR at a microscopic constant, or decaying it completely to zero.
   - **Justification:** The "landing gear." This ensures the model perfectly sinks into the exact mathematical center of the Global Minimum, squeezing out the final fractions of a percent of accuracy.

---
**Task for the end of the day:** Commit your code to Git. Look at your Python graphs and realize that training an <abbr title="Artificial Intelligence">AI</abbr> is just as much art as it is math. 

Tomorrow, in **Day 19**, we look at how to stop our models from memorizing the data. We dive into the ultimate mathematical battle: **Regularization, Bias, and Variance!**
