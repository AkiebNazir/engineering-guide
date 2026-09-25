# Day 162: Experiment Tracking (MLflow, Weights & Biases)

Welcome to Day 162.

When you train a Neural Network, you have dozens of parameters to tune: Learning Rate, Batch Size, Dropout, Epochs. 
If you run 50 different training loops to find the best combination, how do you remember which settings produced the 98% accuracy model?
If you write them down in an Excel spreadsheet or an `experiments.txt` file, you will inevitably forget to log a run, lose track of the exact dataset you used, and experience the nightmare of **Experiment Rot**—where you have a great model file but no idea how to reproduce it.

Today, we learn **Experiment Tracking**. We will use enterprise-grade tools like MLflow and Weights & Biases to automatically log every parameter, metric, and model file so you can reproduce any experiment perfectly.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Reproducibility Crisis
If an <abbr title="Machine Learning">ML</abbr> engineer leaves the company, and they leave behind a file named `best_model_final_v3.pkl`, the company is in trouble.
To reproduce a model, you need:
1. **The Exact Code:** Which Git commit was running?
2. **The Exact Data:** Was the data cleaned? Did it include the December dataset?
3. **The Exact Environment:** Was it PyTorch 2.0 or 2.1?
4. **The Exact Hyperparameters:** What was the learning rate?

Experiment Trackers act as a "Flight Data Recorder" for your training script, automatically saving all 4 of these elements.

### 2. The Big Two Trackers
1. **MLflow:** Open-source, created by Databricks. It is the enterprise standard for tracking experiments, saving artifacts (model files), and deploying them to production. It runs locally for free.
2. **Weights & Biases (WandB):** The gold standard for Deep Learning and <abbr title="Large Language Model">LLM</abbr> training. Used by OpenAI to track GPT-4 training. It features incredible live charts, interactive dashboards, and cloud hosting.

### 3. What Exactly Are We Tracking?
- **Parameters (Inputs):** Learning rate `0.001`, batch size `32`, optimizer `AdamW`.
- **Metrics (Outputs):** Training Loss, Validation Accuracy, F1 Score. (These are logged *per epoch* to create beautiful line charts).
- **Artifacts:** The actual massive `.safetensors` model weights, the tokenizer file, the confusion matrix PNG image, and the `requirements.txt` file.

### 4. Hyperparameter Sweeps (Grid Search on Steroids)
Instead of manually typing a learning rate, running a script, and waiting 5 hours, you use a **Sweep**. 
You define a range (e.g., `learning_rate: [0.01 to 0.0001]`). WandB spins up 20 cloud machines, tries 20 different learning rates simultaneously, and visualizes the results on a beautiful 3D parallel coordinates chart so you instantly see which combination won.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a training script that automatically logs everything to an **MLflow** tracking server.

*(Note: To run this exactly, you need `pip install mlflow scikit-learn pandas`)*

### Step 1: Start the MLflow Server
Open a terminal and run:
```bash
mlflow ui
```
This launches a beautiful web dashboard at `http://localhost:5000`.

### Step 2: The Training Script
```python
import os
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score

# 1. Point the script to the tracking server
mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("Customer_Churn_Prediction")

def train_model(n_estimators: int, max_depth: int):
    
    # 2. Start the Flight Data Recorder!
    with mlflow.start_run(run_name=f"RF_{n_estimators}_{max_depth}"):
        
        print(f"\n[SYSTEM] Training Random Forest (Trees={n_estimators}, Depth={max_depth})...")
        
        # --- LOGGING PARAMETERS (INPUTS) ---
        mlflow.log_param("n_estimators", n_estimators)
        mlflow.log_param("max_depth", max_depth)
        
        # Fake Data Setup
        data = {
            'age': [25, 45, 31, 19, 60, 35, 22, 50],
            'spend': [100, 500, 200, 50, 800, 300, 80, 600],
            'churn': [1, 0, 0, 1, 0, 0, 1, 0]
        }
        df = pd.DataFrame(data)
        X_train, X_test, y_train, y_test = train_test_split(df[['age', 'spend']], df['churn'], test_size=0.25)
        
        # The Training
        model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth)
        model.fit(X_train, y_train)
        
        # The Evaluation
        predictions = model.predict(X_test)
        acc = accuracy_score(y_test, predictions)
        prec = precision_score(y_test, predictions, zero_division=0)
        
        # --- LOGGING METRICS (OUTPUTS) ---
        mlflow.log_metric("accuracy", acc)
        mlflow.log_metric("precision", prec)
        
        print(f"         Accuracy: {acc:.2f} | Precision: {prec:.2f}")
        
        # --- LOGGING ARTIFACTS (THE MODEL ITSELF) ---
        # This saves the model file directly into the MLflow database!
        mlflow.sklearn.log_model(model, "random_forest_model")
        
        print("[SYSTEM] Run successfully logged to MLflow UI!")

# --- EXECUTION SIMULATION ---
def run_experiments():
    # We run 3 different experiments with different hyperparameters.
    # We will be able to compare them visually in the MLflow UI!
    train_model(n_estimators=10, max_depth=5)
    train_model(n_estimators=50, max_depth=10)
    train_model(n_estimators=100, max_depth=20)

# To run:
# run_experiments()
```

### 🔍 Understanding the Enterprise Value
If you run this script and open `http://localhost:5000`, you will see all 3 runs neatly organized in a table. You can click two runs and hit "Compare" to see a chart showing exactly why the 100-tree model beat the 10-tree model.
More importantly, if you click a run, you can literally download the `.pkl` model file that generated that exact score. You have completely eliminated "Experiment Rot"!

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
MLflow has an "Autolog" feature that prevents you from having to type `mlflow.log_param()` manually. 
**Your Task:** Research `mlflow.autolog()`. Modify the script above, remove all the manual `log_` statements, enable autologging, and observe how MLflow automatically captures 50+ parameters you didn't even know existed inside the Random Forest algorithm!

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Your team of 10 <abbr title="Machine Learning">ML</abbr> researchers runs 500 experiments per month on a massive GPU cluster. Many experiments are abandoned. How do you design an experiment lifecycle management system to ensure 100% reproducibility and prevent wasted compute?"*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The Tracking Server:** Deploy a centralized Weights & Biases (WandB) or MLflow server backed by a scalable S3 bucket for artifact storage. No one is allowed to save models locally.
2. **Mandatory Metadata:** Enforce a strict wrapper script. An experiment will instantly crash if the researcher does not provide a `run_name`, a `project_id`, and a `git_commit_hash`.
3. **Data Versioning:** Before the run starts, the script must calculate an MD5 hash of the training dataset and log it to MLflow. This proves exactly which data was used.
4. **Early Stopping:** If an experiment is running for 10 hours and the validation loss has not improved in 5 epochs, the system must trigger an Early Stopping callback, killing the run automatically to prevent burning thousands of dollars of wasted GPU compute.

---
**Task for the end of the day:** Review the concept of **Hyperparameter Sweeps**.

Tomorrow, in **Day 163**, we take the best models from MLflow and push them to a **Model Registry**. We will learn about semantic versioning and the lifecycle from "Staging" to "Production"!
