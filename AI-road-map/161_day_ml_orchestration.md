# Day 161: ML Pipeline Orchestration (Airflow, Dagster & Prefect)

Welcome to Day 161.

We are entering the final weeks of the 180-day roadmap. It is time to learn **MLOps (Machine Learning Operations)**.
If you manually run a Jupyter Notebook to download data, clean it, and train a model, you are not doing MLOps. What happens if the data download fails halfway through? What happens when the model needs to be retrained every Sunday at 3:00 AM?

Today, we learn how to automate the entire lifecycle of an ML project using **DAG Orchestrators**. We will learn how to build pipelines that are fault-tolerant, retryable, and heavily monitored.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Problem with CRON Jobs
*Analogy:* Imagine cooking a complex dinner. You set an alarm (CRON) to bake the chicken at 5:00 PM, and another alarm to make the sauce at 5:30 PM. But what if the grocery delivery was late? At 5:00 PM, you put an empty pan in the oven, and at 5:30 PM you pour sauce on nothing.
CRON jobs run based on *time*. If step 1 fails, step 2 will still run, causing catastrophic data corruption.

### 2. DAGs (Directed Acyclic Graphs)
A **DAG** runs based on *dependencies*. Step B cannot run until Step A is 100% complete. 
If Step A fails, the Orchestrator pauses the entire graph, automatically retries Step A three times, and if it still fails, it sends an alert to your phone. Step B safely waits.

### 3. The Big Three Orchestrators
1. **Apache Airflow:** The undisputed industry standard. Built by Airbnb. It is massive, robust, and slightly archaic. It treats code as "Tasks" that don't easily pass data between each other.
2. **Prefect:** The modern, Pythonic alternative. It feels exactly like writing normal Python code with `@task` decorators.
3. **Dagster:** The future. Built around "Software-Defined Assets". Instead of defining *tasks* (e.g., "Run SQL Script"), you define the *asset* (e.g., "Clean User Table"), and Dagster figures out how to build it and track its lineage.

### 4. The Anatomy of an ML Pipeline
A production MLOps pipeline generally follows this DAG:
1. **Extract:** Pull 10GB of raw logs from Snowflake.
2. **Validate (Data Quality):** Check if there are null values or weird anomalies. (If yes, HALT).
3. **Preprocess:** Tokenize text, normalize vectors.
4. **Train:** Run the GPU training script.
5. **Evaluate:** Run the test dataset. Did the accuracy beat the current production model?
6. **Deploy:** If accuracy > prod, push to the Model Registry.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a fully automated ML Training Pipeline using **Dagster**. 
Notice how we define *Assets* (the data objects we are creating) and how Dagster automatically wires them together based on their input arguments!

*(Note: To run this exactly, you need `pip install dagster dagster-webserver scikit-learn`)*

```python
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from dagster import asset, Config, RetryPolicy, AssetExecutionContext

# --- 1. CONFIGURATION ---
class ModelConfig(Config):
    n_estimators: int = 100
    random_state: int = 42

# --- 2. THE DAGSTER ASSETS (THE PIPELINE) ---

# We add a RetryPolicy! If the database is down, Dagster will wait 5s and try again.
@asset(retry_policy=RetryPolicy(max_retries=3, delay=5))
def raw_user_data() -> pd.DataFrame:
    """ASSET 1: Extract data from the database."""
    print("[PIPELINE] Extracting raw data...")
    # Mocking database extraction
    data = {
        'age': [25, 45, 31, 19, 60],
        'purchases': [100, 500, 200, 50, 800],
        'will_churn': [1, 0, 0, 1, 0]
    }
    return pd.DataFrame(data)

@asset
def preprocessed_data(raw_user_data: pd.DataFrame):
    """ASSET 2: Clean the data. Notice it takes ASSET 1 as a direct input!"""
    print("[PIPELINE] Preprocessing data...")
    # Drop rows with missing values, normalize, etc.
    clean_df = raw_user_data.dropna()
    
    X = clean_df[['age', 'purchases']]
    y = clean_df['will_churn']
    return train_test_split(X, y, test_size=0.2, random_state=42)

@asset
def trained_model(context: AssetExecutionContext, config: ModelConfig, preprocessed_data):
    """ASSET 3: Train the model on the GPU."""
    print(f"[PIPELINE] Training model with {config.n_estimators} trees...")
    X_train, X_test, y_train, y_test = preprocessed_data
    
    model = RandomForestClassifier(
        n_estimators=config.n_estimators, 
        random_state=config.random_state
    )
    model.fit(X_train, y_train)
    
    # We can log metadata directly into the Dagster UI!
    context.add_output_metadata({"Training Size": len(X_train)})
    
    return model, X_test, y_test

@asset
def model_evaluation(context: AssetExecutionContext, trained_model):
    """ASSET 4: Evaluate the model and conditionally alert/deploy."""
    print("[PIPELINE] Evaluating model accuracy...")
    model, X_test, y_test = trained_model
    
    predictions = model.predict(X_test)
    accuracy = accuracy_score(y_test, predictions)
    
    # Log the accuracy to the UI
    context.add_output_metadata({"Accuracy": float(accuracy)})
    
    if accuracy > 0.80:
        print(f"✅ SUCCESS! Model beat threshold with {accuracy}. Deploying to Registry...")
        # Code to push to MLflow or AWS S3 goes here
    else:
        print(f"❌ FAIL! Model accuracy {accuracy} is too low. Halting deployment.")
        # Code to trigger a Slack alert goes here

# To run this pipeline, you would execute:
# dagster dev -f pipeline.py
# This opens a beautiful web UI showing the graph visually!
```

### 🔍 Understanding the Enterprise Value
If you run `dagster dev`, you get a stunning UI showing a flowchart of your 4 steps. 
If step 2 fails, the graph turns red and halts. 
If you update your code and only want to re-run step 4 without waiting 10 hours to re-train the model, you just click "Materialize" on step 4 in the UI! Dagster caches the outputs of the previous steps, saving immense time and money.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Currently, our pipeline runs once.
Modify the Dagster configuration to add a **Schedule**. Configure the pipeline to run automatically every Sunday at midnight. *(Hint: Look up `dagster.ScheduleDefinition`)*.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Design the ML pipeline infrastructure for a team of 50 ML engineers. Cover: pipeline definition, scheduling, monitoring, resource management, and multi-tenancy."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The Orchestrator:** Propose Airflow (for stability) or Dagster (for data lineage). Explain that the orchestrator itself does NOT do the heavy lifting; it just acts as the traffic cop.
2. **Resource Management:** When Airflow triggers the `Train_Model` task, it should use the `KubernetesPodOperator`. Airflow tells K8s: "Spin up a pod with 4 GPUs, run this Docker container, and destroy the pod when it finishes." This keeps the Airflow server extremely lightweight.
3. **Multi-Tenancy:** 50 engineers means 50 different projects. Create isolated "Workspaces" in Dagster or separate DAG folders in Airflow, ensuring Team A's broken code cannot crash Team B's production pipeline.
4. **Data Lineage:** If the Fraud Model starts hallucinating, we must trace the error backward. The orchestrator must track exactly which version of the dataset was used, which version of the Git code executed the training, and which Git commit caused the failure.

---
**Task for the end of the day:** Watch a 5-minute YouTube video comparing Airflow vs Prefect vs Dagster.

Tomorrow, in **Day 162**, we dive into the most critical tool for ML Engineers: **Experiment Tracking**. We will learn how to use MLflow and Weights & Biases to track thousands of hyperparameter experiments!
