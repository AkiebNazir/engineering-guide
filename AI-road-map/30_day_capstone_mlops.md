# Day 30: Phase 1 Capstone & MLOps

Welcome to Day 30. You have officially reached the end of **Phase 1: Classical Machine Learning**. 

You understand the underlying Linear Algebra. You can calculate Gradients. You can build Decision Trees, Random Forests, and XGBoost models. You know how to engineer features and prevent Data Leakage.

But in the real world, a brilliant XGBoost model sitting on your laptop in a Jupyter Notebook is utterly useless. It has to be deployed to a production server. It has to handle millions of requests a second. It has to be monitored so it doesn't crash the company. 

Today, we put the Math aside and learn the Software Engineering of AI: **MLOps**.

---

## 🕒 HOUR 1: DEEP THEORY & MLOPS

### 1. The ML System Design Pipeline
An enterprise AI system consists of 6 distinct phases:
1. **Data Ingestion:** Automatically pulling daily data from an SQL database.
2. **Feature Engineering:** Your `Pipeline` from Day 29 (Scaling, Imputing, Encoding).
3. **Model Training:** Tuning hyperparameters and running XGBoost.
4. **Evaluation:** Checking the accuracy against a Test set.
5. **Deployment:** Wrapping the model in an API (like FastAPI or Flask) so the website can talk to it.
6. **Monitoring:** Watching the model in real-time to ensure it isn't hallucinating.

### 2. DVC (Data Version Control)
You know how to use `Git` to track changes to your Python code. But what happens if an intern accidentally deletes half the rows in your 100GB training dataset? Git cannot track a 100GB CSV file; it will crash.
**DVC (Data Version Control)** solves this. It runs alongside Git and tracks massive datasets. If your data is corrupted, you can type `dvc checkout` and instantly roll your 100GB database back to what it looked like yesterday.

### 3. Experiment Tracking (MLflow)
When trying to build the best model, you might run XGBoost 500 different times, changing `max_depth` and `learning_rate` slightly every time. You *will* forget which combination was the best.
**MLflow** is a dashboard tool. Every time you hit "Run" on your Python script, MLflow automatically records the Hyperparameters you used, the final Accuracy, and silently saves the trained `.pkl` model file to a secure server. You never lose a model again.

### 4. Reproducibility & Environment Locking
Setting `random_state=42` is not enough to guarantee your model will behave the exact same way on a server. If your laptop runs `scikit-learn v1.2` and the server runs `v1.3`, the underlying C++ math libraries might be slightly different! 
You must **Lock the Environment** using Docker or a strict `requirements.txt` file, ensuring the server perfectly matches your laptop.

### 5. Concept Drift (The Silent Killer)
You deploy an AI that detects Credit Card Fraud with 99.9% accuracy. One year later, it starts failing. Why?
**Concept Drift**. The mathematical patterns of the real world changed. Fraudsters invented a new scam. The model hasn't "broken"; reality has just drifted away from the data the model was trained on. 
In MLOps, you must build a monitoring system that mathematically detects Concept Drift and automatically triggers a complete pipeline retraining on fresh data!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's write a professional Python script that wraps your entire Phase 1 knowledge (Pipelines, Random Forests) inside an `MLflow` experiment tracker. 

Create a file named `mlops_pipeline.py`:

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import mlflow
import mlflow.sklearn

def run_mlops_experiment(n_estimators_param, max_depth_param):
    print(f"--- STARTING MLFLOW EXPERIMENT ---")
    print(f"Testing Random Forest with {n_estimators_param} trees and max depth {max_depth_param}")
    
    # 1. Generate Mock Data
    X = np.random.rand(1000, 5)
    # Intentionally add NaN values to test the pipeline!
    X[::10, 0] = np.nan 
    y = (X[:, 1] + X[:, 2] > 1.0).astype(int)
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 2. Start the MLflow Tracker!
    # Anything inside this 'with' block will be securely logged to the dashboard
    with mlflow.start_run():
        
        # Step A: Log the parameters we are testing
        mlflow.log_param("n_estimators", n_estimators_param)
        mlflow.log_param("max_depth", max_depth_param)
        mlflow.log_param("imputation_strategy", "mean")
        
        # Step B: Build the unbreakable Pipeline
        model_pipeline = Pipeline(steps=[
            ('imputer', SimpleImputer(strategy='mean')),
            ('scaler', StandardScaler()),
            ('classifier', RandomForestClassifier(
                n_estimators=n_estimators_param, 
                max_depth=max_depth_param, 
                random_state=42
            ))
        ])
        
        # Step C: Train the model
        model_pipeline.fit(X_train, y_train)
        
        # Step D: Evaluate the model
        predictions = model_pipeline.predict(X_test)
        accuracy = accuracy_score(y_test, predictions)
        
        print(f"Final Accuracy: {accuracy * 100:.2f}%")
        
        # Step E: Log the final metric to MLflow
        mlflow.log_metric("accuracy", accuracy)
        
        # Step F: The Magic! Save the entire trained pipeline as an artifact
        mlflow.sklearn.log_model(model_pipeline, "production_rf_pipeline")
        print("Experiment securely logged to MLflow!")

if __name__ == "__main__":
    # Let's run two experiments. MLflow will track both!
    run_mlops_experiment(n_estimators_param=10, max_depth_param=2)
    print("\n")
    run_mlops_experiment(n_estimators_param=100, max_depth_param=10)
```

*(Note: To see the MLflow dashboard, you would type `mlflow ui` in your terminal and open your web browser!)*

### Key Takeaways from Code:
1. **The Automation:** Notice how clean the code is. We just tell MLflow what `params` we are testing, and what `metrics` came out. 
2. **Artifact Logging:** `mlflow.sklearn.log_model` is incredibly powerful. It takes the entire `Pipeline` (including the Imputer's calculated means and the Scaler's calculated variances) and saves it as a single file. When you deploy to a server, the server just loads that one file, and it is instantly ready to process raw, broken data!

---

## 🕒 HOUR 3: PHASE 1 CAPSTONE & MAANG INTERVIEW

### 🛠️ The Challenge: Rebuild from Memory
You have reached the end of Phase 1. 
**Your Task:**
Open a completely blank Python file. Do not look at any of your past notes. 
Attempt to write an End-to-End script that:
1. Generates data using `make_classification`.
2. Splits it into Train/Test.
3. Builds a `Pipeline` with a Scaler and an XGBoost Classifier.
4. Fits the Pipeline on the Train data.
5. Calculates the `accuracy_score` on the Test data.
If you can do this from memory, you are officially a Classical Machine Learning Engineer!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design a fraud detection system for our credit card division that processes 50,000 transactions per second. The latency must be under 50 milliseconds. Cover the feature engineering pipeline, model serving, and how you will handle Concept Drift."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following system architecture:

1. **The Latency Problem (Model Serving):** 
   - State that running Python `pandas` on a server for 50k requests/sec is too slow. 
   - You must export the trained XGBoost model to a low-latency format (like ONNX or TensorRT) and serve it using C++ or Triton Inference Server.
2. **Feature Engineering (Feature Store):**
   - You cannot calculate "User's Average Spend over 30 Days" in real-time within 50ms. 
   - Explain that you will use a **Feature Store** (like Redis). A background job pre-calculates the 30-day averages overnight and stores them in memory. When a transaction hits, the model instantly queries Redis, grabbing the pre-calculated features in 1 millisecond.
3. **Monitoring & Concept Drift:**
   - Explain that fraudsters constantly change their tactics. You will implement a monitoring system (like Evidently AI) that mathematically compares the statistical distribution of today's transactions against the distribution of the original training data.
   - If the distributions drift too far apart (Concept Drift detected), the system automatically triggers an MLflow pipeline to retrain the XGBoost model on the last 7 days of fresh data.

---
**Task for the end of the day:** Take a break. You have conquered Phase 1. 

Tomorrow, in **Day 31**, everything changes. We enter **Phase 2: Deep Learning & Neural Architectures**. We will build the foundational unit of artificial intelligence: **The Perceptron!**
