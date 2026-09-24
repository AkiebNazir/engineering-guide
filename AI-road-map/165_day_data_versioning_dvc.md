# Day 165: Data Versioning, Lineage & Governance (DVC)

Welcome to Day 165.

You know how to use Git. Git tracks changes in `.py` and `.md` files. 
But Machine Learning relies on **Data**. A model trained on `data_v1.csv` is completely different from a model trained on `data_v2.csv`.
If you try to commit a 50GB `.csv` file or a folder of 100,000 images to Git, GitHub will crash and your repository will break.

Today, we learn how to version control massive datasets using **DVC (Data Version Control)**. We will learn Data Lineage, LakeFS, and how to prove to a regulatory auditor exactly what data was used to train a model.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The DVC Architecture
*Analogy:* Imagine you have a massive safe (AWS S3) full of gold bars (100GB datasets). You don't mail the gold bars back and forth to your team. Instead, you keep a tiny piece of paper (a DVC `.dvc` file) in your pocket. The paper just says "Gold Bar #123 is stored on Shelf A." You can mail that tiny piece of paper instantly.

**DVC (Data Version Control)** sits on top of Git.
1. You run `dvc add huge_dataset.csv`.
2. DVC calculates a tiny MD5 hash of the massive file (e.g., `a1b2c3d4`).
3. DVC moves the massive file into a hidden cache folder and creates a tiny text file: `huge_dataset.csv.dvc`.
4. You commit the tiny `.dvc` file to Git! 
5. You run `dvc push`. DVC uploads the massive 100GB file to a remote storage bucket (AWS S3, Google Cloud Storage, or an internal server).
When another engineer clones your Git repo, they just type `dvc pull`, and DVC reads the `.dvc` file and downloads the exact 100GB dataset from S3!

### 2. Data Lineage
Data is never static. It goes through transformations:
`Raw Logs` $\rightarrow$ `Cleaned Data` $\rightarrow$ `Tokenized Features` $\rightarrow$ `Trained Model`.
If a bug is found in the `Trained Model`, **Data Lineage** allows you to trace the error backward. DVC can track the exact script that turned the raw logs into the cleaned data. If you change the raw logs, DVC knows that the downstream model is now "out of date" and must be retrained.

### 3. LakeFS (Git for Data Lakes)
If your company is massive, you don't use DVC. You use **LakeFS** or **Delta Lake**.
LakeFS provides Git-like branching for massive Data Lakes. You can literally run `lakefs branch create my_experiment`. You can modify petabytes of data on your branch, test a model, and if it works, run a "Data Merge" back into the `main` production branch, complete with ACID transactions!

### 4. Data Governance & Compliance
If you build a model for a bank, and a customer asks "Why was I denied a loan?", GDPR and CCPA laws dictate you must be able to explain the decision. You must prove the model was not trained on discriminatory features (like Race or Religion). 
Without strict data versioning, proving this to an auditor is impossible. With DVC, you hand the auditor the Git commit hash, the exact MD5 hash of the training data, and the Python script that processed it.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's walk through the exact terminal commands an ML Engineer uses to version control a massive dataset using Git and DVC.

*(Note: To run this exactly, you need `pip install dvc` and a dummy large file).*

### Step 1: Initialization
```bash
# Initialize a Git repository
git init

# Initialize DVC inside the Git repository
dvc init

# Commit the internal DVC config files to Git
git commit -m "Initialize DVC"
```

### Step 2: Tracking a Massive File
Imagine we download a massive 5GB file: `data/raw_customer_behavior_2026.csv`.

```bash
# Add the massive file to DVC
dvc add data/raw_customer_behavior_2026.csv

# Output:
# To track the changes with git, run:
#   git add data/raw_customer_behavior_2026.csv.dvc data/.gitignore

# Look at the tiny .dvc file DVC generated!
cat data/raw_customer_behavior_2026.csv.dvc
# Output:
# outs:
# - md5: 8f4a3b2c1d...
#   size: 5368709120
#   path: raw_customer_behavior_2026.csv

# Commit the TINY .dvc pointer file to Git!
git add data/raw_customer_behavior_2026.csv.dvc data/.gitignore
git commit -m "Add raw customer dataset for Q1"
```

### Step 3: Configuring Remote Storage
We cannot push the massive file to GitHub. We must push it to our company's AWS S3 bucket.

```bash
# Tell DVC where our remote massive storage lives
dvc remote add -d my_s3_storage s3://my-enterprise-ai-bucket/dvcstore

# Push the massive file to S3!
dvc push
```

### Step 4: The Magic of Reproducibility
Imagine it is 6 months later. An auditor asks to see the exact data used in the Q1 model.
```bash
# 1. Checkout the old Git commit
git checkout <commit_hash_from_6_months_ago>

# Git instantly replaces the `.dvc` files with the old Q1 versions.

# 2. Tell DVC to pull the data matching the old pointers
dvc pull

# DVC reaches out to S3, finds the exact 5GB file with the MD5 hash 
# from 6 months ago, and places it in your data/ folder. 
# You have perfectly reproduced the past!
```

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
DVC isn't just for tracking files; it tracks **Pipelines**. 
Research the `dvc stage add` (or `dvc.yaml`) command. Learn how you can define a pipeline step like: `dvc stage add -n clean_data -d raw.csv -o clean.csv python clean.py`. 
If you run this, DVC tracks that `clean.csv` depends on `raw.csv`. If `raw.csv` changes, DVC knows `clean.csv` must be recomputed!

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"A regulatory auditor asks you to prove that a production model used for credit scoring was not trained on discriminatory data. They need to see the exact dataset from 8 months ago. Design the data governance and versioning system that enables this instantly."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Immutable Storage:** Explain that data is never overwritten. Updates to the database are appended, and snapshots are taken regularly.
2. **Data Version Control (DVC):** Explain how DVC creates MD5 hashes of dataset snapshots. The `.dvc` pointer files are committed to Git alongside the Python training code.
3. **Model Registry Lineage:** Explain that the MLflow Model Registry logs the exact Git commit hash when the model is registered. 
4. **The Audit Workflow:** To answer the auditor, the engineer fetches the Git commit hash from the Model Registry, runs `git checkout <hash>`, and runs `dvc pull`. This flawlessly reconstitutes the exact Python code and the exact massive CSV file from 8 months ago.

---
**Task for the end of the day:** Skim the DVC documentation. Understand the difference between `git pull` and `dvc pull`.

Tomorrow, in **Day 166**, we cover the final piece of the MLOps puzzle: **Feature Stores**. We will learn how to compute features once, store them centrally, and serve them to LLMs in milliseconds!
