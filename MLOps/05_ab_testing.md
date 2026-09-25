# A/B Testing and Experimentation

You have a new model (v2) that has higher accuracy on the historical test set than the current production model (v1). 
Should you deploy it to 100% of users? **No.**

Offline metrics (like AUC or F1-score) do not always translate to online business metrics (like click-through rate or revenue). You must run an A/B test.

## 1. The Experiment Setup

1. **Hypothesis**: Model v2 will increase Click-Through Rate (CTR) by 2%.
2. **Randomization**: Assign users to a bucket using a deterministic hash of their `user_id`. (e.g., `hash(user_id + "exp_123") % 100`). Users 0-49 get Control (v1), 50-99 get Treatment (v2).
3. **Consistency**: The deterministic hash ensures that if a user reloads the page, they get the same model.

## 2. Statistical Significance

You run the test for 3 days. v1 gets a CTR of 5.1%. v2 gets a CTR of 5.3%. Is v2 better?

Maybe. Or maybe you just got lucky with the random assignment.
You must run a **T-Test** (or similar statistical test) to calculate the **p-value**.
- The p-value is the probability of seeing this 0.2% difference just by random chance.
- The industry standard threshold is 0.05. If p < 0.05, the result is "Statistically Significant", meaning we are 95% confident v2 is actually better.

## 3. Common Pitfalls

### 1. Peeking (The Multiple Comparisons Problem)
A product manager checks the dashboard every day. On Day 2, the p-value dips below 0.05. They stop the test and declare v2 the winner.
This is mathematically invalid. If you check a test every day, the chance of finding a "significant" result due to random noise skyrockets. You must determine the sample size *before* the test, run it to the end, and only check the result once.

### 2. Novelty Effect
Users might click on the new recommendations more just because they look different. After two weeks, they get bored, and the CTR drops back to normal. Run tests long enough to outlast the novelty effect (usually 2-4 weeks).

### 3. Network Effects (Interference)
A/B testing a pricing algorithm for Uber drivers is hard. If you give Treatment drivers better routes, they steal rides from Control drivers. The Control group's metrics go down *because* the Treatment group exists. 
Solution: Switchback testing (the entire city is Control on Monday, Treatment on Tuesday) or Geo-based testing (New York is Control, Chicago is Treatment).
