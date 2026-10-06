# Day 17: Momentum, RMSProp, and Adam Optimizers

Welcome to Day 17. Mini-Batch SGD is an incredible algorithm, but it has a fatal geometric flaw. 

Imagine a Loss Landscape shaped like a long, narrow ravine (a half-pipe). The slope pointing down the sides of the half-pipe is extremely steep, but the slope pointing forward toward the actual Global Minimum is extremely flat. 

Standard SGD will violently bounce side-to-side up the walls of the half-pipe, making almost zero forward progress. To fix this, we have to inject the laws of physics—specifically **Momentum**—into our calculus.

Today, we build **Adam**, the optimizer that powers almost every modern AI model on Earth.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. SGD with Momentum (The Heavy Ball)
Standard SGD has no memory. It only cares about the slope at the exact pixel it is standing on. 
**Momentum** changes the algorithm from a hiker into a heavy iron ball. As the ball rolls, it builds up velocity. 

**Algebraic Definition:**
1. Update Velocity: $v_t = \beta v_{t-1} + (1-\beta)\nabla_\theta \mathcal{L}$
2. Take Step: $\theta_{t+1} = \theta_t - \eta v_t$

*(Where $\beta$ is the friction/momentum term, usually set to $0.9$. This means your new step is $90\%$ based on the speed you were already going, and only $10\%$ based on the current slope!)*

> **Mathematical Example (The Ravine):**
> If you are bouncing side-to-side in a ravine, your gradient alternates: `[Left, Right, Left, Right]`. 
> Because Momentum averages your historical gradients, `Left` and `Right` perfectly cancel each other out to zero! Meanwhile, the tiny `Forward` gradients add up over time. The iron ball stops bouncing sideways and blasts straight down the ravine!

### 2. Nesterov Lookahead
A heavy iron ball is great, but it has a problem: if it builds up too much speed, it will blast right past the Global Minimum and roll up the other side!
**Nesterov Lookahead** is a clever fix. Instead of calculating the gradient where the ball is currently standing, we calculate the gradient at the spot the ball is *about to roll to*. If the future spot is going uphill, the algorithm hits the brakes *before* taking the step!

### 3. RMSProp (Adaptive Learning Rates)
What if we have 1 Million weights in our network? Giving all 1 Million weights the exact same Learning Rate ($\eta$) is a terrible idea. Some weights need to move quickly, others need to move slowly.

**RMSProp** automatically gives every single weight its own custom Learning Rate. It keeps a running average of the *squared* gradients.
- If a weight is bouncing wildly (massive gradients), RMSProp mathematically divides its Learning Rate by a huge number, slamming on the brakes.
- If a weight is barely moving (tiny gradients), RMSProp divides its Learning Rate by a tiny fraction, hitting the gas pedal!

### 4. Adam (Adaptive Moment Estimation)
In 2014, researchers realized they could just combine the two algorithms.
**Adam = Momentum (The Heavy Ball) + RMSProp (Custom Learning Rates).**

**The Bias Correction Hack:**
Because Adam initializes its memory tracking variables at exactly $0.0$, the first few steps of the algorithm are artificially tiny (the math is biased toward zero). Adam includes a mathematical hack called **Bias Correction**: $\hat{m}_t = \frac{m_t}{1-\beta_1^t}$. As $t$ (time) increases, this correction factor fades away to nothing!

> **AI Context (AdamW):** 
> Years later, researchers realized that combining standard $L_2$ Regularization (Weight Decay) with Adam caused a mathematical bug. Adam's RMSProp component was accidentally shrinking the regularization penalty! **AdamW** was invented to "decouple" the weight decay from the gradient math, fixing the bug. AdamW is now the standard for training LLMs.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's build an Object-Oriented `Optimizer` class from scratch in pure Python. We will implement standard SGD, Momentum, RMSProp, and the legendary Adam optimizer.

Create a file named `advanced_optimizers.py`:

```python
import numpy as np
import matplotlib.pyplot as plt

class Optimizers:
    """A collection of the world's most famous optimization algorithms."""
    
    @staticmethod
    def sgd(w, gradient, lr):
        """Standard Stochastic Gradient Descent"""
        return w - lr * gradient

    @staticmethod
    def momentum(w, gradient, lr, v, beta=0.9):
        """SGD with Momentum (The Heavy Ball)"""
        # Update velocity (90% old speed, 10% new gradient)
        v = beta * v + (1 - beta) * gradient
        # Take step
        w_new = w - lr * v
        return w_new, v

    @staticmethod
    def rmsprop(w, gradient, lr, s, beta=0.999, epsilon=1e-8):
        """Root Mean Square Propagation (Adaptive LR)"""
        # Track the squared gradients
        s = beta * s + (1 - beta) * (gradient ** 2)
        # Custom learning rate: divide by the square root of 's'
        w_new = w - (lr / (np.sqrt(s) + epsilon)) * gradient
        return w_new, s

    @staticmethod
    def adam(w, gradient, lr, m, v, t, beta1=0.9, beta2=0.999, epsilon=1e-8):
        """Adaptive Moment Estimation (Momentum + RMSProp)"""
        t += 1 # Time step
        
        # 1. Update Momentum (m)
        m = beta1 * m + (1 - beta1) * gradient
        # 2. Update RMSProp (v)
        v = beta2 * v + (1 - beta2) * (gradient ** 2)
        
        # 3. Bias Correction (Fixing the Zero-Initialization bug)
        m_hat = m / (1 - beta1 ** t)
        v_hat = v / (1 - beta2 ** t)
        
        # 4. Take the perfect step
        w_new = w - (lr / (np.sqrt(v_hat) + epsilon)) * m_hat
        
        return w_new, m, v, t

def run_optimizer_race():
    """Simulates optimizing a 1D function: y = x^2 (Gradient = 2x)"""
    print("--- STARTING OPTIMIZER RACE ---")
    
    # Starting extremely far away from the global minimum (x=0)
    start_pos = 100.0 
    iterations = 50
    lr = 0.5
    
    # Track paths
    path_sgd = [start_pos]
    path_mom = [start_pos]
    path_rms = [start_pos]
    path_adam = [start_pos]
    
    # State variables
    w_sgd, w_mom, w_rms, w_adam = start_pos, start_pos, start_pos, start_pos
    v_mom = 0
    s_rms = 0
    m_adam, v_adam, t_adam = 0, 0, 0
    
    for _ in range(iterations):
        # Calculate gradients (Derivative of x^2 is 2x)
        g_sgd = 2 * w_sgd
        g_mom = 2 * w_mom
        g_rms = 2 * w_rms
        g_adam = 2 * w_adam
        
        # Apply Optimizers
        w_sgd = Optimizers.sgd(w_sgd, g_sgd, lr=0.1) # Lower LR so it doesn't explode
        w_mom, v_mom = Optimizers.momentum(w_mom, g_mom, lr=0.1, v=v_mom)
        w_rms, s_rms = Optimizers.rmsprop(w_rms, g_rms, lr=10.0, s=s_rms) # High LR, RMSProp scales it down
        w_adam, m_adam, v_adam, t_adam = Optimizers.adam(w_adam, g_adam, lr=10.0, m=m_adam, v=v_adam, t=t_adam)
        
        path_sgd.append(w_sgd)
        path_mom.append(w_mom)
        path_rms.append(w_rms)
        path_adam.append(w_adam)
        
    # Plotting
    plt.figure(figsize=(10, 6))
    plt.plot(path_sgd, label='SGD (Slow)', linestyle=':')
    plt.plot(path_mom, label='Momentum (Fast but Overshoots)', linestyle='-.')
    plt.plot(path_rms, label='RMSProp (Stable)', linestyle='--')
    plt.plot(path_adam, label='Adam (Perfect Balance)', linewidth=3)
    
    plt.axhline(0, color='black', linewidth=1, label='Global Minimum')
    plt.title("Optimizer Convergence Race")
    plt.xlabel("Iterations")
    plt.ylabel("Weight Position (Distance from Minimum)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    filename = "optimizer_race.png"
    plt.savefig(filename)
    print(f"Saved visualization to {filename}.")
    print("Notice how Momentum plunges below 0 and bounces back up (overshooting).")
    print("Notice how Adam perfectly glides into the minimum without bouncing!")

if __name__ == "__main__":
    run_optimizer_race()
```

### Key Takeaways from Code:
1. **The Math is Simple:** Everyone treats "Adam" like a magical black box. Look at the code. It is literally just 5 lines of basic algebra. 
2. **The Overshoot:** Look at the `optimizer_race.png` image. Notice how the Momentum line (orange) dips below the black line (0.0) and has to bounce back up. This proves the "Heavy Iron Ball" analogy! It built up so much speed it rolled up the other side of the valley before gravity pulled it back. Adam manages this much better because of the RMSProp brakes.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Implementing AdamW
**Your Task:** Modify the `Optimizers` class.
1. Add a new `@staticmethod` called `adamw`.
2. Accept a new parameter `weight_decay` (e.g., `0.01`).
3. Standard Adam applies $L_2$ Regularization by adding the weights to the `gradient` *before* all the complex RMSProp math happens. This accidentally shrinks the penalty!
4. To fix it, do not change the gradient at all. Just subtract `lr * weight_decay * w` from the final `w_new` at the very end of the equation! 
5. Congratulations, you just implemented the algorithm that trained GPT-4.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Adam is the absolute default optimizer for Natural Language Processing and LLMs. However, if you look at the State-of-the-Art (SOTA) papers for Computer Vision (like ResNet or Vision Transformers), many researchers intentionally throw Adam in the trash and use basic SGD with Momentum instead. Why would they do this? Discuss the Generalization Gap."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Adam's Flaw (The Sharp Minima):** 
   - State that Adam is incredibly fast at finding a minimum. However, because of its adaptive learning rates, it aggressively dives into the *very first* minimum it finds. 
   - These minima are often "sharp" (narrow valleys). A sharp minimum means that if the real-world test data is even slightly different from the training data, the error will spike massively. Adam overfits.
2. **SGD's Strength (The Flat Minima):**
   - Explain that SGD with Momentum is much slower and mathematically "dumber". But because it uses the exact same learning rate for all weights, it acts like a heavy, blunt object. It literally rolls right out of sharp, narrow valleys.
   - It is forced to keep wandering until it finds a massive, wide, "flat" minimum. 
3. **The Generalization Gap Conclusion:**
   - Conclude that models trained in wide, flat valleys generalize significantly better to unseen real-world data. Therefore, CV researchers are willing to spend 3x more time training with SGD+Momentum just to gain that extra 2% of real-world accuracy!

---
**Task for the end of the day:** Commit your code to Git. You now have a deep, instinctual understanding of exactly how AI navigates the mathematical universe.

Tomorrow, in **Day 18**, we realize that humans are terrible at picking Learning Rates. We will write code that automatically finds the perfect Learning Rate for us: **Learning Rate Schedulers & Warmups!**
