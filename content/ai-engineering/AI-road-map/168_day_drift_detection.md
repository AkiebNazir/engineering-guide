# Day 168: Data Drift & Concept Drift (The Silent Killers)

Welcome to Day 168.

You build a Fraud Detection model. You train it, test it, and deploy it. The accuracy is 99%. 
Six months later, the CTO calls you into their office. Fraud is up 400%. The model's accuracy has silently plummeted to 60%, but the API hasn't thrown a single error.

What happened? The world changed. The fraudsters invented a new technique that didn't exist in your training data. 
In software engineering, code doesn't rot. `2 + 2` will always equal `4`. But in Machine Learning, models rot the moment you deploy them.

Today, we learn how to mathematically detect when the world has shifted out from beneath your model using **Drift Detection**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Three Types of Drift
1. **Data Drift (Covariate Shift):** The distribution of the *inputs* changes. 
   *Example:* You trained a housing model in 2019 where the average house size was 2,000 sq ft. In 2026, developers start building 4,000 sq ft mansions. The model has never seen inputs this large, so its predictions become wild guesses.
2. **Concept Drift:** The relationship between the input and the *target* changes.
   *Example:* In 2019, a 2,000 sq ft house in Texas cost $250k. In 2026, that exact same 2,000 sq ft house costs $500k. The input (2,000 sq ft) is the same, but the target meaning has fundamentally shifted.
3. **Prior Probability Shift:** The distribution of the *target classes* changes.
   *Example:* During COVID, 80% of transactions were online. Post-COVID, it drops to 40%.

### 2. Detecting Drift (The Math)
How do we prove that today's data is fundamentally different from the training data? We use statistical tests to compare distributions.
- **Population Stability Index (PSI):** A single number representing how much a feature's distribution has shifted. PSI < 0.1 means no change. PSI > 0.2 means significant drift (retrain immediately).
- **Kolmogorov-Smirnov (KS) Test:** A statistical test that calculates the maximum distance between two cumulative distribution curves.
- **Wasserstein Distance (Earth Mover's Distance):** Measures how much "work" it takes to transform today's distribution curve into the training data's distribution curve.

### 3. Drift Detection for LLMs
Drift is easy to measure on numerical data (like age or salary). How do you measure drift on text?
If your LLM app usually receives prompts like "Write a python script", but suddenly a viral TikTok causes users to ask "Explain this meme", your LLM will hallucinate.
**Embedding Drift:** We convert the training prompts into Vector Embeddings. We calculate the centroid (the mathematical center) of those vectors. In production, we constantly embed incoming user prompts. If the distance from the incoming prompts to the training centroid exceeds a threshold, we trigger a "Semantic Drift" alert!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a drift detection script using the **Population Stability Index (PSI)**. We will simulate an ML engineer comparing last year's training data against today's production data to prove the model is rotting!

```python
import numpy as np

# --- 1. THE MATH: POPULATION STABILITY INDEX (PSI) ---
def calculate_psi(expected, actual, buckets=10):
    """
    Calculates the PSI between a training distribution (expected)
    and a production distribution (actual).
    """
    # 1. Define the bin boundaries based on the training data
    breakpoints = np.percentile(expected, np.linspace(0, 100, buckets + 1))
    
    # 2. Count how many items fall into each bin for both datasets
    expected_percents = np.histogram(expected, breakpoints)[0] / len(expected)
    actual_percents = np.histogram(actual, breakpoints)[0] / len(actual)
    
    # 3. Handle 0% edge cases (to avoid divide-by-zero errors)
    expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
    actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)
    
    # 4. The core PSI formula: sum( (Actual - Expected) * ln(Actual / Expected) )
    psi_value = np.sum((actual_percents - expected_percents) * np.log(actual_percents / expected_percents))
    
    return psi_value

# --- 2. EXECUTION SIMULATION ---
def run_drift_analysis():
    print("--- DATA DRIFT DETECTION (PSI) ---")
    
    # 1. The baseline training data (e.g., ages of users in 2024)
    # Normally distributed around 30 years old
    training_data_age = np.random.normal(loc=30, scale=5, size=10000)
    
    # 2. Production data on a NORMAL day (Looks just like training data)
    production_normal = np.random.normal(loc=30, scale=5.1, size=1000)
    
    # 3. Production data on a DRIFT day (A viral ad brought in teenagers!)
    # Normally distributed around 19 years old
    production_drifted = np.random.normal(loc=19, scale=3, size=1000)
    
    # --- EVALUATE ---
    
    psi_normal = calculate_psi(training_data_age, production_normal)
    print(f"\n[NORMAL DAY] Age Feature PSI: {psi_normal:.4f}")
    if psi_normal < 0.1:
        print("   ✅ No significant drift detected. Model is safe.")
        
    psi_drifted = calculate_psi(training_data_age, production_drifted)
    print(f"\n[DRIFT DAY] Age Feature PSI: {psi_drifted:.4f}")
    if psi_drifted > 0.2:
        print("   🚨 SEVERE DRIFT DETECTED (PSI > 0.2)!")
        print("   The users are fundamentally different than the training data.")
        print("   ACTION: Halt predictions and retrain model immediately!")

# To run:
# run_drift_analysis()
```

### 🔍 Understanding the Enterprise Value
In a real MLOps pipeline, this script runs every night at midnight. It compares the last 24 hours of API traffic against the golden training dataset stored in S3. 
If the `psi_value` for any critical feature spikes above `0.2`, it automatically fires a webhook to the Airflow orchestrator (Day 161) to trigger a brand-new GPU training cycle on the fresh data! This is the holy grail of MLOps: **Continuous Training (CT) driven by Drift!**

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Currently, we detected drift on a 1D numerical feature (Age).
**Your Task:** Research how to detect drift on Unstructured Text (LLM Prompts). Look up libraries like `Evidently AI` or `NannyML`. Read their documentation on how they use Vector Embeddings to calculate "Data Drift" on text data.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"You deployed a pricing optimization model for Uber. It worked perfectly for 6 months, but suddenly revenue dropped 15%. Your metrics show the model is outputting much lower prices than usual. Diagnose the problem and design a system to prevent it from happening again."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Diagnosis (Concept Drift):** Identify that the underlying economic reality changed (e.g., inflation, or a competitor lowered their prices). The mapping between features (distance, time) and the target variable (willingness to pay) has fundamentally broken.
2. **The Delay Problem:** Acknowledge that you cannot calculate Concept Drift until you have ground truth labels. (If you predict a user will pay $20, you don't know if you were right until they actually accept or reject the ride).
3. **Prevention via Data Drift:** Because ground truth is delayed, we must monitor *Data Drift* (the inputs). If the average distance of a ride suddenly drops by 40% (Data Drift), we can assume the model is operating outside its training distribution and trigger an alert *before* revenue drops.
4. **Automated Retraining Architecture:** Design an Airflow DAG that monitors PSI daily. If PSI > 0.2, the DAG automatically pulls the last 30 days of data, retrains the model, evaluates it against the current production model (Shadow Mode), and deploys it if the accuracy is higher.

---
**Task for the end of the day:** Read up on the open-source library **Evidently AI**. It is the industry standard for generating beautiful HTML reports that visualize Data Drift.

Tomorrow, in **Day 169**, we cover the scariest part of engineering: **Incident Response**. What exactly do you do when the PagerDuty alarm goes off at 3:00 AM because the AI started cursing at customers?
