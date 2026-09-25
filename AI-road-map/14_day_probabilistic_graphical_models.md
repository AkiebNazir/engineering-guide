# Day 14: Week 2 Review & Probabilistic Graphical Models

Welcome to Day 14! Today is the final day of Phase 2 (Probability). 

For the last week, we have been studying individual probabilities, distributions, and hypothesis tests. But real-world <abbr title="Artificial Intelligence">AI</abbr> systems (like medical diagnostic tools or autonomous cars) do not deal with single variables. They deal with thousands of interconnected variables.

How do we model the chaotic, interconnected web of the real world? We use **Probabilistic Graphical Models (PGMs)**.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. What is a Probabilistic Graphical Model (PGM)?
A PGM is a visual and mathematical framework that represents complex probability distributions using a graph. Instead of writing out a massive, unreadable algebra equation for 10,000 variables, we draw nodes (the variables) and edges (the relationships).

There are two main types of PGMs:
1. **Bayesian Networks (Directed PGM):** The edges are arrows that represent strict cause-and-effect. *(e.g., Rain $\rightarrow$ Wet Grass $\leftarrow$ Sprinkler)*.
2. **Markov Random Fields (Undirected PGM):** The edges are just lines representing correlation, without strict causality. *(e.g., In an image, Pixel A is highly correlated with Pixel B next to it, but Pixel A doesn't "cause" Pixel B).*

### 2. Bayesian Networks (Deep Dive)
Let's look at a classic Bayesian Network:
`Burglar` $\rightarrow$ `Alarm` $\leftarrow$ `Earthquake`
`Alarm` $\rightarrow$ `John Calls Police`

> **Mathematical Example (Concrete Numbers):**
> Instead of storing a massive table of every possible combination, the network only stores the conditional probabilities!
> - $P(\text{Burglar}) = 0.001$
> - $P(\text{Earthquake}) = 0.002$
> - $P(\text{Alarm} | \text{Burglar}, \text{Earthquake}) = 0.95$
> 
> **<abbr title="Artificial Intelligence">AI</abbr> Context (Explaining Away):** 
> Imagine the Alarm goes off. Your probability of a Burglar spikes to 90%. But then you check Twitter and see an Earthquake just happened! Suddenly, your probability of a Burglar drops back down to 5%. This is called "Explaining Away." The PGM math perfectly mimics human deductive reasoning!

### 3. Belief Propagation
How do we calculate these probabilities across a massive network of 10,000 nodes? We use an algorithm called **Belief Propagation**. 
Nodes act like little computers. They calculate their own probability, and then send a mathematical "message" across the edge to their neighbor saying: *"Hey, I just updated my belief. You should update yours."* This ripples through the network until everything stabilizes.

### 4. Probabilistic Programming
Writing the math for Belief Propagation by hand is brutal. Modern <abbr title="Artificial Intelligence">AI</abbr> engineers use **Probabilistic Programming** languages (like `PyMC` or `Pyro`). In normal code, a variable holds a number (e.g., `x = 5`). In Probabilistic Programming, a variable holds an entire probability distribution!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's build our own microscopic **Probabilistic Programming** framework from scratch. We will use a technique called **Rejection Sampling** to simulate a Bayesian Network and solve the "Burglar / Alarm" problem using pure code.

Create a file named `probabilistic_programming.py`:

```python
import numpy as np

class ProbabilisticNetwork:
    """A microscopic Probabilistic Programming framework."""
    def __init__(self):
        self.samples = 100000
        
    def simulate_burglar_network(self):
        print("--- RUNNING BAYESIAN NETWORK INFERENCE ---")
        
        # 1. Priors (Independent Events)
        # We simulate 100,000 parallel universes
        burglar_happens = np.random.uniform(0, 1, self.samples) < 0.01 # 1% chance
        earthquake_happens = np.random.uniform(0, 1, self.samples) < 0.05 # 5% chance
        
        # 2. The Alarm Node (Conditional Dependency)
        alarm_rings = np.zeros(self.samples, dtype=bool)
        
        for i in range(self.samples):
            b = burglar_happens[i]
            e = earthquake_happens[i]
            
            # The Probability Table for the Alarm
            if b and e:   prob_alarm = 0.99
            elif b and not e: prob_alarm = 0.90
            elif not b and e: prob_alarm = 0.50
            else:             prob_alarm = 0.01 # False alarm
            
            alarm_rings[i] = np.random.uniform(0, 1) < prob_alarm
            
        # 3. Inference via Rejection Sampling!
        # Question: IF the alarm is ringing, what is the probability of a Burglar?
        
        # Step A: CONDITIONING (Throw away all universes where the alarm is NOT ringing)
        valid_universes = alarm_rings == True
        total_valid = np.sum(valid_universes)
        
        # Step B: INFERENCE (In those valid universes, how many had a burglar?)
        burglars_in_valid = np.sum(burglar_happens[valid_universes])
        
        prob_burglar_given_alarm = burglars_in_valid / total_valid
        
        print(f"Prior Probability of Burglar: 1.0%")
        print(f"Posterior P(Burglar | Alarm Ringing): {prob_burglar_given_alarm * 100:.1f}%")
        
        # Let's see "Explaining Away" in action
        valid_universes_with_eq = (alarm_rings == True) & (earthquake_happens == True)
        burglars_in_eq_universes = np.sum(burglar_happens[valid_universes_with_eq])
        
        prob_burglar_given_alarm_and_eq = burglars_in_eq_universes / np.sum(valid_universes_with_eq)
        
        print("\n*Wait, you feel an earthquake!*")
        print(f"Posterior P(Burglar | Alarm AND Earthquake): {prob_burglar_given_alarm_and_eq * 100:.1f}%")
        print("Notice how the probability of a burglar plummets! The earthquake 'explained away' the alarm.")

if __name__ == "__main__":
    network = ProbabilisticNetwork()
    network.simulate_burglar_network()
```

### Key Takeaways from Code:
1. **Rejection Sampling:** Instead of doing complex Bayes Theorem calculus, we just simulated 100,000 universes. When we asked *"Given that the alarm rang..."*, we literally just deleted every universe where the alarm didn't ring! Then we just counted the remaining universes. This is how Probabilistic Programming engines work under the hood when math fails.
2. **Explainability:** Unlike Deep Neural Networks (which are black boxes), Bayesian Networks are 100% explainable. You can trace the exact logic of why the model thinks there is a 90% chance of a burglar. This makes them highly preferred in the medical and legal fields.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Grade Predictor
**Your Task:** Modify the `probabilistic_programming.py` script.
1. Create a new network with three variables: `Difficulty` (Hard=0.6, Easy=0.4), `Intelligence` (High=0.3, Low=0.7), and `Grade` (A, B, or C).
2. `Grade` depends on both `Difficulty` and `Intelligence`. Write the nested IF statements for the probabilities. (e.g., IF Hard AND High Intel, $P(A) = 0.5$).
3. Run the Rejection Sampling inference. 
4. Calculate: $P(\text{Intelligence} = \text{High} | \text{Grade} = \text{A})$. 

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are designing a real-time Bayesian personalization engine for a streaming platform with 50 Million users. How do you handle the 'Cold Start' problem for brand new users? How does your system scale without computing massive probability graphs for all 50M users simultaneously?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Cold Start Problem (Using Priors):** 
   - Explicitly state that a new user has zero data. In standard Machine Learning (MLE), the model would fail completely.
   - Explain that because we are using a **Bayesian** model, we inject a **Prior distribution**. This Prior is calculated from the global average of the 50M existing users. The new user is immediately served recommendations based on this global Prior.
2. **Handling Model Updates (Posterior becomes Prior):**
   - As the new user watches their first 3 movies, we use Bayes Theorem to multiply their data (Likelihood) against the Prior to generate their unique **Posterior**.
   - **Crucial Point:** This Posterior mathematically becomes their *new* Prior for tomorrow! 
3. **Scalability:**
   - Explain that because the Posterior automatically encapsulates all historical data, we *do not* need to keep re-calculating the graph over their entire watch history. We only calculate the update for the movies watched *today*. This changes the compute time from $O(N)$ (where N is all movies ever watched) to $O(1)$, allowing the platform to easily scale to 50 Million users.

---
**Task for the end of the day:** Commit your code to Git. Take a deep breath. You have officially completed Phase 2.

Tomorrow, in **Day 15**, we enter **Phase 3: Optimization**. We throw away the probabilities and learn how <abbr title="Artificial Intelligence">AI</abbr> actually "learns" from its mistakes by sliding down mathematical mountains using **Gradient Descent**!
