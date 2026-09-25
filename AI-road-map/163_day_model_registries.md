# Day 163: Model Registry, Version Control & Artifact Management

Welcome to Day 163.

Yesterday, you ran 50 experiments in MLflow. Experiment 42 had the highest accuracy. What happens next?
Do you download `model_42.pkl`, email it to the backend team, and say "Here's the new model, please deploy it?"
Absolutely not. 

Today, we learn about the **Model Registry**. We will learn how to formally package, version, and promote <abbr title="Artificial Intelligence">AI</abbr> models through strict lifecycle stages (Staging $\rightarrow$ Production) exactly like standard software engineering.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Model Registry
*Analogy:* An Experiment Tracker (Day 162) is a messy artist's studio filled with hundreds of rough sketches. The **Model Registry** is the art gallery. Only the absolute best sketches are framed, numbered, and put on the wall.

A Model Registry acts as a centralized database for your company's production-ready models. It provides:
- **Version Control:** `Fraud_Model_v1`, `Fraud_Model_v2`.
- **Lifecycle Stages:** A model can be tagged as `None`, `Staging`, `Production`, or `Archived`.
- **Access Control:** A Junior <abbr title="Machine Learning">ML</abbr> Engineer can push a model to `Staging`, but only the Lead Engineer can click the button to promote it to `Production`.

### 2. Semantic Versioning for Models
In standard software, v1.2.3 means `Major.Minor.Patch`. 
In Machine Learning:
- **Major (v2.0.0):** The architecture changed completely (e.g., switched from Random Forest to XGBoost, or changed the input data schema).
- **Minor (v1.1.0):** The model was retrained on a new month of data, improving accuracy.
- **Patch (v1.0.1):** A configuration setting or threshold was tweaked, but the model weights didn't change.

### 3. Model Lineage & Artifacts
When a model is in the Registry, it must have **Lineage**. You must be able to click the model and trace it backward:
- Which specific Git commit of the Python code generated it?
- Which specific version of the S3 bucket data was it trained on?
- What are its Artifacts? (The weights, the tokenizer, the `requirements.txt`).
If a model breaks in production, lineage allows you to pinpoint the exact line of code or row of bad data that caused the corruption.

### 4. Model Cards
A **Model Card** is the "Nutritional Label" for your <abbr title="Artificial Intelligence">AI</abbr>. It is a strict documentation standard created by Margaret Mitchell (Google). It formally states:
- **Intended Use:** (e.g., "This model predicts churn for US customers.")
- **Out of Scope Use:** (e.g., "Do not use this for EU customers.")
- **Bias & Limitations:** (e.g., "This model has a 12% higher false-positive rate for users under 25.")

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's use Python and the **MLflow Model Registry** <abbr title="Application Programming Interface">API</abbr> to take an experiment, register it as a formal versioned model, and programmatically promote it to Production!

*(Note: To run this, you need `pip install mlflow` and an active MLflow tracking server running on port 5000)*

```python
import mlflow
from mlflow.tracking import MlflowClient

# Connect to the MLflow Server
client = MlflowClient(tracking_uri="http://127.0.0.1:5000")
model_name = "Enterprise_Churn_Predictor"

def manage_model_lifecycle(run_id: str):
    print(f"\n--- REGISTERING MODEL FROM RUN: {run_id} ---")
    
    # 1. Register the Model (The Art Gallery)
    # We take the best run from our experiments and formally register it.
    model_uri = f"runs:/{run_id}/random_forest_model"
    registered_model = mlflow.register_model(model_uri, model_name)
    
    version = registered_model.version
    print(f"[REGISTRY] Model registered as '{model_name}' Version {version}!")
    
    # 2. Add Lineage and Model Card metadata
    client.update_model_version(
        name=model_name,
        version=version,
        description="""
        **Model Card:**
        - Intended Use: Predicting customer churn for the Q3 campaign.
        - Training Data: S3://bucket/data_v2.csv
        - Git Commit: 8f4a3b2
        """
    )
    
    # 3. Transition to STAGING
    print(f"\n[LIFECYCLE] Moving Version {version} to STAGING...")
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage="Staging",
        archive_existing_versions=False
    )
    
    # Normally, an automated CI/CD pipeline would run integration tests on the 
    # Staging model here before a human approves it.
    
    # 4. Transition to PRODUCTION (The Final Promotion)
    print(f"[LIFECYCLE] Tests passed! Promoting Version {version} to PRODUCTION...")
    client.transition_model_version_stage(
        name=model_name,
        version=version,
        stage="Production",
        archive_existing_versions=True # Automatically archives the old Production model!
    )
    
    print("\n✅ Lifecycle Complete. The backend API will now automatically load the new model.")

# --- MOCK EXECUTION ---
def run_simulation():
    # In reality, you get the run_id from your MLflow experiments
    mock_run_id = "abcd1234efgh5678" 
    try:
        manage_model_lifecycle(mock_run_id)
    except Exception as e:
        print("Note: Start the MLflow server (`mlflow ui`) to run this live!")

# To run:
# run_simulation()
```

### 🔍 Understanding the Enterprise Value
Because we used the MLflow Registry, the Backend Engineering team no longer needs to hardcode paths or download files!
Their FastAPI application simply calls `mlflow.pyfunc.load_model("models:/Enterprise_Churn_Predictor/Production")`.
Whenever you transition a new version to Production, the <abbr title="Application Programming Interface">API</abbr> automatically pulls the new weights without changing a single line of backend code.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Currently, our code blindly transitions the model from Staging to Production.
Modify the script so that before transitioning to Production, the code fetches the **accuracy metric** of the *current* Production model and compares it to the *new* Staging model. Only execute the transition if `new_accuracy > old_accuracy`.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Design a model registry architecture for a company deploying 200 different models across 50 microservices. Cover: versioning, deployment triggers, rollback procedures, and compliance requirements."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The Central Truth:** A centralized Registry (like AWS SageMaker Model Registry) acts as the single source of truth.
2. **Deployment Triggers:** When an <abbr title="Machine Learning">ML</abbr> Engineer clicks "Approve for Production" in the Registry UI, it triggers an AWS EventBridge webhook. This webhook fires a GitHub Actions pipeline that builds a new Docker container with the new model weights baked in.
3. **Rollback Procedures:** Because previous versions are marked as `Archived` in the registry (never deleted), a rollback is as simple as clicking the previous version and changing its tag back to `Production`. The webhook refires and automatically reverts the Docker containers.
4. **Compliance (Model Cards):** For highly regulated industries (Finance/Health), the Registry must enforce hard constraints. A model *cannot* be transitioned to Staging unless all 5 fields of the Model Card are filled out and an automated Fairness/Bias audit report is attached as an artifact.

---
**Task for the end of the day:** Read a real-world Model Card (like the official Llama-3 Model Card on GitHub). See how obsessively detailed they are about bias and limitations.

Tomorrow, in **Day 164**, we take this further. We will learn **<abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr> for <abbr title="Machine Learning">ML</abbr> (Continuous Integration / Continuous Deployment)**. How do we test a model automatically when we push code to GitHub?
