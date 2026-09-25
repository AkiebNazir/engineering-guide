# Day 12: Sampling Methods (<abbr title="Markov Chain Monte Carlo">MCMC</abbr> & Metropolis-Hastings)

Welcome to Day 12. In Day 10, we used pure Calculus (MLE and MAP) to find the absolute "peak" of a probability distribution. But what if the math is too hard? What if the distribution has 10,000 dimensions and the integral is literally impossible for any computer to solve?

When exact math fails, we use **Sampling**. If you can't calculate the exact shape of a mountain, you can just drop a million blindfolded hikers onto it, let them wander randomly, and record where they step. That is the essence of **Markov Chain Monte Carlo (<abbr title="Markov Chain Monte Carlo">MCMC</abbr>)**.

Let's learn how to conquer impossible math with pure randomness.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. Markov Chains
A **Markov Chain** is a mathematical system that hops from one state to another, following one strict rule: *The next hop depends ONLY on where you are right now, completely ignoring how you got there.*

### 2. Monte Carlo Integration
In high school, you learned to find the area under a curve using Calculus (Integrals). But integrating a 10,000-dimensional Bayesian Posterior is physically impossible. 

Instead, we use **Monte Carlo Integration**: we throw random points at the function and count them. The problem? If the "mountain" of probability is tiny, and the 10,000-dimensional "desert" is massive, throwing random points will result in 99.9% of them landing in the empty desert. We need a way to only explore the interesting parts of the mountain!

### 3. Metropolis-Hastings Algorithm
The **Metropolis-Hastings Algorithm** is the most famous <abbr title="Markov Chain Monte Carlo">MCMC</abbr> algorithm. It acts like a "drunk hiker" exploring a mountain in the dark. 

**The Algorithm Loop:**
1. Start at a random position $x_{old}$.
2. Propose a random jump to a new position $x_{new}$.
3. Calculate the Acceptance Ratio ($\alpha$): How high is the new position compared to the old one?
   $$ \alpha = \frac{P(x_{new})}{P(x_{old})} $$
4. **The Magic Rule:**
   - If $\alpha \ge 1$ (the new step is uphill), **always accept** the step.
   - If $\alpha < 1$ (the new step is downhill), **accept it randomly** with probability $\alpha$. (e.g., If the new step is half as high as the old step, accept it 50% of the time).

> **Mathematical Example (Concrete Numbers):**
> You are at $x_{old}$. The probability (height) of this spot is $0.4$. 
> You propose a step to $x_{new}$. 
> **Scenario A (Uphill):** The height of $x_{new}$ is $0.8$. $\alpha = \frac{0.8}{0.4} = 2.0$. Since $\alpha \ge 1$, we always accept the step! We move to $x_{new}$.
> **Scenario B (Downhill):** From $x_{new}$ (height $0.8$), you propose a step back to $x_{old}$ (height $0.4$). $\alpha = \frac{0.4}{0.8} = 0.5$. Since $\alpha < 1$, we roll a digital 100-sided die. If it lands on 1-50, we take the step downhill. If 51-100, we stay where we are.
> 
> **<abbr title="Artificial Intelligence">AI</abbr> Context (Mapping the Posterior):** 
> Why would we *ever* take a step downhill? Because if we only went uphill, we would get permanently stuck on the first tiny hill we found (a Local Minimum). By occasionally taking downhill steps, the hiker maps out the *entire* mountain range. Over millions of steps, the hiker spends exactly $80\%$ of their time on hills that represent $80\%$ of the probability, perfectly mapping the impossible distribution!

### 4. Gibbs Sampling
**Gibbs Sampling** *(a special case of Metropolis-Hastings where you only update one dimension or feature at a time)* is an optimization. By mathematically freezing all dimensions except one, the Acceptance Ratio $\alpha$ is mathematically guaranteed to be $1.0$. You never waste compute power rejecting a step!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's write a Metropolis-Hastings sampler from scratch. We will define an impossible-to-integrate "Twin Peaks" distribution, and watch the drunk hiker perfectly map out the two mountains.

Create a file named `mcmc_sampler.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import norm

def target_distribution(x: float) -> float:
    """
    Our target "Twin Peaks" probability landscape. 
    It is a mixture of two Gaussian distributions.
    This acts as P(x).
    """
    # Peak 1 at x=2, Peak 2 at x=7
    peak_1 = norm.pdf(x, loc=2, scale=1)
    peak_2 = norm.pdf(x, loc=7, scale=2) * 0.5 # Second peak is wider and half as tall
    
    return peak_1 + peak_2

def metropolis_hastings(iterations: int = 10000) -> np.ndarray:
    """
    The 'Drunk Hiker' MCMC algorithm.
    """
    print("--- STARTING METROPOLIS-HASTINGS MCMC ---")
    
    # 1. Start at a terrible, random guess
    current_x = -5.0 
    samples = []
    
    accepted_steps = 0
    
    for i in range(iterations):
        # 2. Propose a jump (Gaussian step from current position)
        proposed_x = np.random.normal(loc=current_x, scale=2.0)
        
        # 3. Calculate heights (Probability)
        p_current = target_distribution(current_x)
        p_proposed = target_distribution(proposed_x)
        
        # 4. Calculate Acceptance Ratio (alpha)
        # Adding tiny epsilon to prevent division by zero
        alpha = p_proposed / (p_current + 1e-15)
        
        # 5. The Magic Rule
        if alpha >= 1.0:
            # Uphill! Always accept.
            current_x = proposed_x
            accepted_steps += 1
        else:
            # Downhill. Accept it randomly based on alpha.
            random_coin = np.random.uniform(0, 1)
            if random_coin < alpha:
                current_x = proposed_x
                accepted_steps += 1
                
        # Record where the hiker is standing
        samples.append(current_x)
        
    print(f"Finished {iterations:,} iterations.")
    print(f"Acceptance Rate: {(accepted_steps/iterations)*100:.1f}%")
    return np.array(samples)

def plot_results(samples):
    """Visualizes the MCMC walk and the final distribution."""
    plt.figure(figsize=(12, 5))
    
    # Plot 1: The Random Walk (Trace Plot)
    plt.subplot(1, 2, 1)
    # We plot the first 1000 steps to see the hiker "find" the mountains
    plt.plot(samples[:1000], alpha=0.7, color='blue')
    plt.title("Trace Plot (The Hiker's Path)")
    plt.xlabel("Step Number")
    plt.ylabel("Position (x)")
    plt.grid(True, alpha=0.3)
    
    # Plot 2: The Histogram vs True Distribution
    plt.subplot(1, 2, 2)
    # The histogram of all steps
    plt.hist(samples, bins=50, density=True, alpha=0.6, color='green', label='MCMC Samples')
    
    # The true mathematical line
    x_axis = np.linspace(-2, 15, 1000)
    y_axis = target_distribution(x_axis)
    # Normalize the true distribution so it sums to 1.0 for the plot
    y_axis = y_axis / np.trapz(y_axis, x_axis) 
    
    plt.plot(x_axis, y_axis, 'r-', lw=3, label='True Probability Math')
    plt.title("Histogram of Hiker vs True Math")
    plt.legend()
    
    plt.tight_layout()
    filename = "mcmc_results.png"
    plt.savefig(filename)
    print(f"Saved visualization to {filename}. The histogram perfectly matches the math!")

if __name__ == "__main__":
    # We throw away the first 1000 samples (called the "Burn-in" period)
    # because the hiker started at x=-5 and took a while to find the mountain!
    raw_samples = metropolis_hastings(iterations=50000)
    valid_samples = raw_samples[1000:] 
    
    plot_results(valid_samples)
```

### Key Takeaways from Code:
1. **The Burn-in Period:** In real <abbr title="Markov Chain Monte Carlo">MCMC</abbr>, we initialize the <abbr title="Artificial Intelligence">AI</abbr> with random, terrible parameters. We let it run for a few thousand iterations and throw those results in the garbage (called the **Burn-in**). We only start recording data once the hiker has "found the mountain".
2. **The Acceptance Rate:** A good <abbr title="Markov Chain Monte Carlo">MCMC</abbr> algorithm should have an acceptance rate around 20% to 50%. If it's 99%, the hiker is taking microscopic baby steps and will never explore the whole mountain. If it's 1%, the hiker is trying to jump miles at a time and getting rejected constantly.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Bayesian Inference for Logistic Regression
**Your Task:** Grab a framework like `PyMC3` or `Stan` (or use raw Python).
1. Set up a basic 2D Logistic Regression classification problem (e.g., predicting Pass/Fail based on Hours Studied).
2. Instead of using standard MLE to find the *single best* line (Decision Boundary), use <abbr title="Markov Chain Monte Carlo">MCMC</abbr> to sample 1,000 different valid lines.
3. Plot all 1,000 lines on a graph. You will see a thick "blur" of lines. 
4. **The Magic:** This blur represents **Uncertainty**. If a student studies an average amount, the lines will be tightly packed (high confidence). If a student studies an extreme amount never seen in the data, the lines will fan out wildly (low confidence). Standard Machine Learning cannot do this!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You have built an incredible Bayesian fraud-detection model using <abbr title="Markov Chain Monte Carlo">MCMC</abbr>. It gives us a full probability distribution of uncertainty for every transaction. The problem? Our <abbr title="Application Programming Interface">API</abbr> requires predictions in under 10 milliseconds, and your <abbr title="Markov Chain Monte Carlo">MCMC</abbr> algorithm takes 5 seconds to run. What alternatives exist to solve this, and what mathematical trade-offs do you make?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Identifying the <abbr title="Markov Chain Monte Carlo">MCMC</abbr> Bottleneck:** 
   - State clearly that <abbr title="Markov Chain Monte Carlo">MCMC</abbr> is inherently sequential (you cannot take step 10 until you have taken step 9). Therefore, <abbr title="Markov Chain Monte Carlo">MCMC</abbr> cannot be easily parallelized on GPUs and is useless for real-time latency budgets.
2. **The Alternative: Variational Inference (VI):**
   - Propose **Variational Inference** as the enterprise solution. 
   - Instead of slowly mapping the true, complex probability distribution by walking around it (<abbr title="Markov Chain Monte Carlo">MCMC</abbr>), VI creates a simple, fake distribution (like a standard Gaussian). It then uses Machine Learning (Gradient Descent / Kullback-Leibler Divergence) to force the fake distribution to stretch and warp until it closely resembles the true distribution.
3. **The Trade-offs:**
   - **<abbr title="Markov Chain Monte Carlo">MCMC</abbr>:** Mathematically guaranteed to be exactly correct if run infinitely long, but infinitely slow.
   - **Variational Inference:** Extremely fast (can be parallelized on GPUs), but mathematically biased. It provides an *approximation* of the truth, often severely underestimating the "tails" (extreme outliers) of the probability distribution.

---
**Task for the end of the day:** Commit your code to Git. You now know how to map the un-mappable. 

Tomorrow, in **Day 13**, we use probability to prove whether or not our <abbr title="Artificial Intelligence">AI</abbr> models actually work in the real world: **Hypothesis Testing & A/B Testing!**
