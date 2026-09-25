# Day 13: Hypothesis Testing, Confidence Intervals & A/B Testing

Welcome to Day 13. You have spent the last 12 days learning how to build complex <abbr title="Artificial Intelligence">AI</abbr> models. Today, we confront the harsh reality of the business world. 

When you deploy a new <abbr title="Artificial Intelligence">AI</abbr> recommendation engine to production, your product manager is going to ask: *"Did your model actually increase our sales by 5%, or did we just get lucky this week?"* 

If you cannot mathematically prove that your model is the direct cause of the success, your model will be deleted. We prove causation using **Hypothesis Testing and A/B Testing**.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. The Null and Alternative Hypothesis
In statistics, you must assume your new <abbr title="Artificial Intelligence">AI</abbr> model is garbage until proven otherwise. This is the foundation of the scientific method.

- **Null Hypothesis ($H_0$):** The default, boring assumption. *(e.g., "The new <abbr title="Artificial Intelligence">AI</abbr> model had exactly zero impact on user clicks.")*
- **Alternative Hypothesis ($H_A$):** Your actual theory. *(e.g., "The new <abbr title="Artificial Intelligence">AI</abbr> model increased user clicks.")*

### 2. The P-Value (The Most Misunderstood Number in Science)
To decide between $H_0$ and $H_A$, we calculate a **p-value**.
A p-value is **NOT** the probability that your hypothesis is right. 

**Algebraic Definition:**
A p-value is $P(\text{Data} | H_0)$. It asks: *"Assuming the new <abbr title="Artificial Intelligence">AI</abbr> model is actually garbage, what are the chances we would see this 5% spike in sales just due to random luck?"*

> **Mathematical Example (Concrete Numbers):**
> You run an A/B test. The p-value comes back as $0.02$ (or 2%). 
> This means: If the <abbr title="Artificial Intelligence">AI</abbr> model was completely broken and did nothing, there is only a 2% chance you would have randomly gotten this lucky. Because 2% is so low (usually $\le 5\%$), we **reject the Null Hypothesis** and conclude the <abbr title="Artificial Intelligence">AI</abbr> model actually works!

### 3. Type I and Type II Errors
Because A/B testing relies on probability, it is never 100% perfect. You will make mistakes.
- **Type I Error (False Positive):** Your p-value was very low, so you shipped the model to production. But you actually just got insanely lucky. The model does nothing. (You cost the company engineering time).
- **Type II Error (False Negative):** Your p-value was high, so you deleted the model. But the model was actually brilliant; you just got very unlucky during the test window. (You cost the company massive potential revenue).

**Power** is the mathematical probability that you avoid a Type II Error. If a test has 80% Power, it means if your model is actually good, you have an 80% chance of successfully detecting it.

### 4. Bootstrapping (Confidence Intervals for Free)
Historically, calculating the exact p-value and Confidence Interval *(a range of numbers, like 3% to 7%, where we are 95% sure the true sales increase lies)* required crazy calculus and Gaussian assumptions. 

Today, we use computers to cheat. It's called the **Bootstrap Method**.
Instead of using calculus, we take our dataset, randomly pull a data point out, record it, and put it back in. We do this 10,000 times to create a "fake" dataset. We calculate the average. We repeat this 1,000 times. We look at the top 95% of our fake averages. That is our Confidence Interval! No calculus required.

### 5. The Multiple Comparison Problem (Bonferroni)
What happens if you run 20 A/B tests at the exact same time, using the standard $p \le 0.05$ threshold for success?

> **Mathematical Example (Concrete Numbers):**
> If the threshold is 0.05, there is a 5% chance of a False Positive for *each* test.
> The math for getting zero False Positives across 20 tests is: $(0.95)^{20} \approx 0.36$.
> This means there is a $1.0 - 0.36 = 64\%$ chance that at least one of your "winning" A/B tests is a complete hallucination!
> 
> **<abbr title="Artificial Intelligence">AI</abbr> Context (Bonferroni Correction):** 
> To stop this, statisticians use the **Bonferroni Correction**. You divide your $p$-value threshold by the number of tests you are running. If you run 20 tests, your new threshold for success is $0.05 / 20 = 0.0025$. Only models with a p-value lower than $0.0025$ are allowed to ship to production!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's write a script that proves how powerful the **Bootstrap Method** is. We don't need any complex probability math to calculate exactly how much money our new <abbr title="Artificial Intelligence">AI</abbr> model is making the company.

Create a file named `ab_testing_bootstrap.py`:

```python
import numpy as np
import matplotlib.pyplot as plt

def bootstrap_confidence_interval():
    """
    Simulates an A/B test for an E-commerce site.
    Group A (Control) uses the old algorithm.
    Group B (Treatment) uses your new AI algorithm.
    We use Bootstrapping to find the Confidence Interval of the revenue increase.
    """
    print("--- BOOTSTRAP A/B TESTING ---")
    
    # 1. Real World Data Collection (Simulated)
    # Group A spent an average of $50, but it's very noisy (std_dev = 20)
    group_a_revenue = np.random.normal(loc=50.0, scale=20.0, size=1000)
    # Group B spent an average of $53. Is this a real increase, or just luck?
    group_b_revenue = np.random.normal(loc=53.0, scale=20.0, size=1000)
    
    actual_difference = np.mean(group_b_revenue) - np.mean(group_a_revenue)
    print(f"Raw Observed Difference: ${actual_difference:.2f} per user")
    
    # 2. Bootstrapping
    num_bootstraps = 5000
    bootstrap_differences = []
    
    for _ in range(num_bootstraps):
        # Sample WITH REPLACEMENT from the original data
        # This creates 'alternate realities' of our test
        sample_a = np.random.choice(group_a_revenue, size=1000, replace=True)
        sample_b = np.random.choice(group_b_revenue, size=1000, replace=True)
        
        diff = np.mean(sample_b) - np.mean(sample_a)
        bootstrap_differences.append(diff)
        
    bootstrap_differences = np.array(bootstrap_differences)
    
    # 3. Calculate 95% Confidence Interval
    # We chop off the bottom 2.5% and the top 2.5% of the fake realities
    lower_bound = np.percentile(bootstrap_differences, 2.5)
    upper_bound = np.percentile(bootstrap_differences, 97.5)
    
    print("\n--- RESULTS ---")
    print(f"95% Confidence Interval: [${lower_bound:.2f}, ${upper_bound:.2f}]")
    
    if lower_bound > 0:
        print("✅ SUCCESS! The lower bound is strictly > $0.")
        print("We are 95% confident the AI model actually increases revenue.")
    else:
        print("❌ FAIL. The interval includes $0 or negative numbers.")
        print("We cannot confidently say the AI model does anything. Do not ship.")
        
    # Plotting
    plt.figure(figsize=(10, 5))
    plt.hist(bootstrap_differences, bins=50, color='purple', alpha=0.7)
    plt.axvline(0, color='black', linestyle='--', linewidth=2, label='Zero Impact ($0)')
    plt.axvline(lower_bound, color='red', linestyle='--', label='95% Lower Bound')
    plt.axvline(upper_bound, color='red', linestyle='--', label='95% Upper Bound')
    
    plt.title("Bootstrap Distribution of Revenue Increase")
    plt.xlabel("Extra Revenue Per User ($)")
    plt.ylabel("Frequency (Bootstrap Realities)")
    plt.legend()
    plt.grid(True, alpha=0.3)
    
    filename = "bootstrap_ab_test.png"
    plt.savefig(filename)
    print(f"\nSaved visualization to {filename}.")

if __name__ == "__main__":
    bootstrap_confidence_interval()
```

### Key Takeaways from Code:
1. **Sampling with Replacement:** The secret to Bootstrapping is `replace=True`. If you have a dataset of `[1, 2, 3]`, a bootstrap sample might be `[1, 1, 3]`. This accurately mimics the variance of drawing new users from the general population.
2. **Visual Proof:** Look at `bootstrap_ab_test.png`. The entire purple bell curve shows all the possible parallel realities. If that red lower-bound line crosses the black $0.00 line, it means there is a highly realistic parallel universe where your <abbr title="Artificial Intelligence">AI</abbr> model actually *lost* money. You cannot ship it.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Statistical Power Simulator
**Your Task:** Create a file named `power_analysis.py`.

You need to tell the Product Manager how long to run the A/B test.
1. Write a `for` loop that tests different sample sizes: `[100, 500, 1000, 5000]`.
2. Inside the loop, run 1,000 mini A/B tests using `np.random.normal`. Group A mean is 50, Group B mean is 52. (The <abbr title="Artificial Intelligence">AI</abbr> definitely works, it makes +$2).
3. For each test, run a `scipy.stats.ttest_ind` to get the p-value.
4. Count how many times the p-value is $< 0.05$. Divide by 1,000 to get the **Power** percentage.
5. **The Revelation:** You will see that at `N=100`, the Power is maybe 15%. This means even though your <abbr title="Artificial Intelligence">AI</abbr> model is brilliantly successful, you will wrongly delete it 85% of the time (Type II Error) simply because your sample size was too small to mathematically prove it!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your data science team at Netflix runs 200 A/B tests per quarter for various UI tweaks and recommendation algorithm changes. The Product Manager comes to you excited because a test for a new thumbnail algorithm came back with a p-value of 0.04 (which is < 0.05!). They want to deploy it globally. What is statistically wrong with this, and how do you redesign the experimentation platform to prevent this in the future?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Diagnosing the Multiple Comparison Problem:** 
   - State that with an $\alpha = 0.05$ threshold, 5% of tests will show a false positive purely by chance.
   - If you run 200 tests and ALL 200 algorithms are completely broken (do nothing), you will mathematically still "win" 10 tests just by flipping coins. The $p=0.04$ is almost certainly a Type I error (a hallucination).
2. **Platform Redesign (Bonferroni Correction):**
   - Suggest implementing the **Bonferroni Correction** in the testing platform. The platform should automatically divide the threshold by the number of active tests ($0.05 / 200 = 0.00025$). The PM's test fails miserably against this new, rigorous threshold.
3. **Platform Redesign (FDR / Benjamini-Hochberg):**
   - *Advanced Points:* Note that Bonferroni is often too strict and kills actual good ideas (high Type II errors). 
   - Suggest implementing the **False Discovery Rate (FDR)** control using the Benjamini-Hochberg procedure. This is the industry standard for MAANG platforms. It guarantees that out of all the "winning" tests you ship to production, no more than exactly 5% of them are fake.

---
**Task for the end of the day:** Commit your code to Git. You now have the statistical armor required to defend your <abbr title="Artificial Intelligence">AI</abbr> models in a corporate boardroom. 

Tomorrow, in **Day 14**, we reach the end of Week 2! We will conduct a massive review of Probability, bringing it all together into a **Probabilistic Graphical Model**.
