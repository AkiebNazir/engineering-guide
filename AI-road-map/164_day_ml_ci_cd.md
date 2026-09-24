# Day 164: CI/CD for ML (Automated Testing & Deployment)

Welcome to Day 164.

In traditional software, when you push a code change to GitHub, an automated server (like GitHub Actions) runs a suite of Unit Tests. If the tests pass, it automatically deploys the code to production. This is Continuous Integration and Continuous Deployment (CI/CD).
But if you do this for Machine Learning, you will cause a disaster.
In ML, code is only 1/3 of the equation. A model can fail because the *code* is wrong, the *data* is biased, or the *weights* degraded. 

Today, we learn **CI/CD for Machine Learning (CT/CD)**. We will learn how to test data, test models, and safely deploy them without terrifying the engineering team.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The ML Testing Pyramid
When you push an update to an ML codebase, the CI pipeline must run three distinct layers of tests before anyone is allowed to click "Merge":
1. **Unit Tests (The Code):** Does the `clean_text()` function successfully strip emojis?
2. **Data Tests (The Fuel):** Is the training data formatted correctly? Are there 50,000 null values that will silently ruin the matrix math?
3. **Model Tests (The Brain):** Train a tiny mock model. Does it overfit on 10 examples? Does its accuracy exceed the 85% threshold? Does it pass a Bias check?

### 2. Continuous Training (CT)
In traditional CI/CD, the artifact is a compiled binary. In ML, the artifact is a massive model file. 
Because training takes 10 hours, you do not train the production model inside the GitHub Action runner. 
Instead, the GitHub Action triggers an **Airflow/Dagster pipeline** (Continuous Training). Once the training pipeline finishes, *it* pushes the new model to the Model Registry (Staging).

### 3. Progressive Deployment Strategies
You never swap a production model on a Friday at 5:00 PM and go home. You deploy it progressively to catch hidden regressions.

- **Shadow Mode (Dark Launch):** The new model is deployed behind the API. It receives real user traffic and calculates predictions, but the predictions are *thrown away*. The user still sees the old model's answer. Engineers monitor the Shadow Model's logs to ensure it doesn't crash on edge cases.
- **Canary Deployment:** The router sends 95% of users to the Old Model, and 5% of users to the New Model (the "Canary"). If the 5% don't complain, you dial it up to 10%, 50%, and 100%.

### 4. Automated Rollback
If the New Model hits 100% rollout, and suddenly the Latency metric spikes to 5 seconds, an automated script (connected to Prometheus/PagerDuty) instantly dials the router back to 100% Old Model. 

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual **GitHub Actions Workflow** (`.yml`) for an ML project, combined with a Python testing script that proves the model is safe to deploy!

### Step 1: The ML Test Suite (Python)
This script runs automatically on the CI server. If any `assert` statement fails, the pipeline halts, and the GitHub Pull Request is blocked!

```python
# File: tests/test_model_pipeline.py
import pytest
import pandas as pd
from my_app.model import train_model, preprocess_data

# --- 1. DATA QUALITY TESTS ---
def test_data_schema():
    """Ensure the dataset hasn't been corrupted or altered by another team."""
    df = pd.read_csv("data/training_data_sample.csv")
    
    assert 'age' in df.columns, "Missing 'age' feature!"
    assert 'spend' in df.columns, "Missing 'spend' feature!"
    assert df['age'].isnull().sum() == 0, "Null values detected in 'age'!"
    assert df['age'].min() >= 18, "Data contains underage users!"

# --- 2. MODEL QUALITY TESTS ---
def test_model_accuracy_threshold():
    """Train a small model and ensure it beats the baseline."""
    df = pd.read_csv("data/training_data_sample.csv")
    X, y = preprocess_data(df)
    
    # Train the model
    model, accuracy = train_model(X, y)
    
    # The Hard Threshold
    assert accuracy > 0.85, f"Model accuracy {accuracy} fell below 85% baseline!"

def test_model_bias():
    """Ensure the model doesn't severely discriminate based on gender."""
    df = pd.read_csv("data/training_data_sample.csv")
    model, _ = train_model(*preprocess_data(df))
    
    # Check predictions for Male vs Female users
    df_male = df[df['gender'] == 'M']
    df_female = df[df['gender'] == 'F']
    
    male_approval_rate = model.predict(df_male).mean()
    female_approval_rate = model.predict(df_female).mean()
    
    # The difference in approval rates cannot exceed 5%
    difference = abs(male_approval_rate - female_approval_rate)
    assert difference < 0.05, f"Bias detected! Gender approval difference is {difference*100}%"
```

### Step 2: The GitHub Actions Workflow
This YAML file lives in `.github/workflows/ml_cicd.yml`. It listens for Pull Requests to the `main` branch.

```yaml
name: ML CI/CD Pipeline

on:
  pull_request:
    branches: [ main ]

jobs:
  test_and_evaluate:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout Code
      uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install Dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest

    - name: Run Data and Model Tests
      run: |
        # If this fails, the PR turns red and cannot be merged!
        pytest tests/test_model_pipeline.py

    - name: Trigger Remote Training (Dagster)
      if: success() # Only run if the tests passed!
      run: |
        echo "Tests passed! Triggering the heavy GPU training pipeline..."
        curl -X POST https://dagster.mycompany.com/api/trigger_run \
          -H "Authorization: Bearer ${{ secrets.DAGSTER_TOKEN }}" \
          -d '{"pipeline": "retrain_prod_model", "commit": "${{ github.sha }}"}'
```

### 🔍 Understanding the Enterprise Value
With this CI/CD setup, an engineer cannot break production. 
If they accidentally delete a feature column in the code, the `test_data_schema` fails. If they tweak a hyperparameter that destroys accuracy, the `test_model_accuracy_threshold` fails. If they introduce a biased feature, the `test_model_bias` fails.
Only mathematically proven, safe code is allowed to trigger the expensive GPU training pipeline.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Currently, the pipeline triggers a training run. Once training is complete, the model goes to the Registry.
How do you safely deploy that model to the API gateway? 
**Your Task:** Research the **Seldon Core** or **KServe** Kubernetes frameworks. Understand how they allow you to deploy a model as a container and configure a `Canary` rollout (e.g., sending 5% of HTTP traffic to the new container automatically).

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Your team deploys ML models 5 times per week. Last week, a new model deployment caused a 30% revenue drop. The monitoring system didn't catch it because the latency and HTTP codes were perfectly fine (the model was just making terrible recommendations). Design the deployment safety system to prevent this."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The Gap:** Acknowledge that offline CI/CD tests (accuracy, bias) are not enough to catch revenue-destroying bugs in production user behavior.
2. **Shadow Mode Deployment:** Propose that every new model must run in Shadow Mode for 24 hours. If it crashes on weird production inputs, it is caught here without harming users.
3. **Canary & A/B Testing:** Once Shadow Mode passes, the model is rolled out as a Canary to 5% of users. Crucially, the system must track **Business Metrics** (Click-Through Rate, Revenue per User) for that 5% cohort versus the 95% baseline cohort.
4. **Automated Rollback:** If a statistical analysis shows the Canary cohort's revenue drops by more than 2% compared to the baseline, the API Gateway must instantly revert the 5% traffic back to the old model and trigger a severe PagerDuty alert.

---
**Task for the end of the day:** Review the concept of a "Shadow Deployment." It is the safest way to test AI in production.

Tomorrow, in **Day 165**, we tackle the hardest problem in ML: **Data Versioning**. We will learn how to use DVC (Data Version Control) to track massive gigabytes of data exactly like Git tracks code!
