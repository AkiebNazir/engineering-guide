# Scikit-Learn Mastery: The Gold Standard of Classical <abbr title="Machine Learning">ML</abbr>

## 1. The Core Concept (What and Why)

**What is it?**
Scikit-Learn (`sklearn`) is the undisputed king of classical Machine Learning in Python. It provides hundreds of algorithms for Classification, Regression, Clustering, and Dimensionality Reduction.

**Why does it exist?**
Before Scikit-Learn, every researcher wrote their own algorithm from scratch with different function names and data formats. Scikit-Learn created the **Uniform <abbr title="Application Programming Interface">API</abbr>**. Whether you are running a simple Linear Regression or a complex Random Forest, the code is always the exact same: `model.fit(X, y)` and `model.predict(X)`. 

While Deep Learning (PyTorch) is used for text and images, Scikit-Learn is still the weapon of choice for 90% of enterprise tabular data (Excel spreadsheets, <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> databases).

---

## 2. Setup & Installation

```bash
pip install scikit-learn
```

```python
import sklearn

print(f"Scikit-Learn version: {sklearn.__version__}")
```

---

## 3. The "Hello World": End-to-End Classification

Let's build a model that predicts if a tumor is malignant or benign.

```python
from sklearn.datasets import load_breast_cancer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

# 1. Load Data (Features: X, Target: y)
X, y = load_breast_cancer(return_X_y=True)

# 2. Train / Test Split (Crucial for testing generalization)
# We reserve 20% of the data to test the model on data it has NEVER seen.
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Instantiate the Model
model = RandomForestClassifier(n_estimators=100, random_state=42)

# 4. Train (Fit) the Model
model.fit(X_train, y_train)

# 5. Predict on Unseen Data
predictions = model.predict(X_test)

# 6. Evaluate
acc = accuracy_score(y_test, predictions)
print(f"Accuracy: {acc * 100:.2f}%") # 96.49%
```

---

## 4. Deep Dive: The Scikit-Learn <abbr title="Application Programming Interface">API</abbr> Contract

Every object in Scikit-Learn falls into one of three categories. If you understand these three, you understand the entire library.

### A. Estimators
Any object that can learn from data. It must have a `.fit(X, y)` method.
- *Examples:* `LinearRegression`, `RandomForestClassifier`.

### B. Transformers
Any object that modifies or cleans data. It must have a `.transform(X)` method.
- *Examples:* `StandardScaler` (scales numbers), `OneHotEncoder` (turns text into binary columns), `SimpleImputer` (fills missing values).
- **The Shortcut:** `.fit_transform(X)` does both steps at once and is heavily optimized.

### C. Predictors
Any object that makes predictions. It must have a `.predict(X)` method.
- **Bonus:** Classification models also have `.predict_proba(X)`, which outputs the *probability* (e.g., "I am 80% confident this tumor is malignant"). This is critical for business logic!

---

## 5. Preprocessing (Transformers)

Machine Learning models cannot read text (like "Male"/"Female"), and they struggle if features are on vastly different scales (e.g., Age ranges 0-100, but Salary ranges 0-1,000,000). You must transform the data.

```python
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import pandas as pd

df = pd.DataFrame({
    'age': [25, 45, 30],
    'salary': [50000, 120000, 80000],
    'city': ['NY', 'SF', 'NY']
})

# 1. StandardScaler (Mean = 0, Standard Deviation = 1)
# Models like SVMs and Neural Networks REQUIRE scaled numbers.
scaler = StandardScaler()
scaled_numbers = scaler.fit_transform(df[['age', 'salary']])

# 2. OneHotEncoder (Converting categories to binary columns)
# 'NY' becomes [1, 0], 'SF' becomes [0, 1]
encoder = OneHotEncoder(sparse_output=False)
encoded_cities = encoder.fit_transform(df[['city']])
```

---

## 6. The Holy Grail: Pipelines & ColumnTransformers (Pro Level)

*Junior Engineers* apply transformers to their training data manually, one by one.
*Senior Engineers* use `Pipelines`. 

A Pipeline chains transformers and a predictor together. It guarantees that when you deploy the model to production, the raw incoming <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> data is scaled and encoded exactly the same way the training data was. It completely eliminates **Data Leakage**.

```python
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression

# Imagine a dataset with numerical columns and categorical columns
numeric_features = ['age', 'salary']
categorical_features = ['city', 'profession']

# 1. Define what happens to numbers (Fill missing with median -> Scale)
numeric_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())
])

# 2. Define what happens to text (Fill missing with 'missing' -> OneHotEncode)
categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

# 3. Combine them using ColumnTransformer
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_transformer, numeric_features),
        ('cat', categorical_transformer, categorical_features)
    ])

# 4. The Final Master Pipeline!
master_pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('classifier', LogisticRegression())
])

# To train the entire pipeline:
# master_pipeline.fit(X_train, y_train)

# To predict on raw production data:
# master_pipeline.predict(X_raw_production_data)
```

---

## 7. Hyperparameter Tuning (Finding the Best Model)

Models have settings called **Hyperparameters** (e.g., How deep should the Random Forest grow?). You cannot guess these. You must search for them.

```python
from sklearn.model_selection import GridSearchCV

# Define the grid of settings you want to try
param_grid = {
    'classifier__n_estimators': [50, 100, 200],
    'classifier__max_depth': [None, 10, 20]
}

# GridSearchCV will train the pipeline 9 times (3x3 grid) using Cross-Validation
# to definitively find the mathematically best combination.
grid_search = GridSearchCV(master_pipeline, param_grid, cv=5, n_jobs=-1)

# grid_search.fit(X_train, y_train)
# print(f"Best parameters: {grid_search.best_params_}")
```

---

## 8. Evaluation Metrics (Beyond Accuracy)

In the real world, Accuracy is a terrible metric. If you are predicting a rare disease that 1% of people have, a model that just says "No one is sick" will be 99% accurate!

```python
from sklearn.metrics import classification_report, confusion_matrix

# Assuming we have true labels (y_test) and model predictions
# print(confusion_matrix(y_test, predictions))

"""
Confusion Matrix Output:
[[True_Negatives,  False_Positives],
 [False_Negatives, True_Positives]]
"""

# print(classification_report(y_test, predictions))

"""
Precision: Of all the people the model SAID were sick, how many actually were?
Recall:    Of all the people who were ACTUALLY sick, how many did the model catch?
F1-Score:  The harmonic mean of Precision and Recall.
"""
```

---

## 9. MAANG Interview Scenarios

### Scenario 1: The Data Leakage Trap
*Interviewer:* "I scaled my entire dataset using `StandardScaler.fit_transform(X)`, and then I did `train_test_split(X, y)`. Why is this wrong?"

*Answer:* "You committed Data Leakage. `StandardScaler` calculates the Mean and Standard Deviation. Because you scaled the *entire* dataset before splitting, the Mean calculation included the test data! Your model secretly gained mathematical information about the test set during training. You must split *first*, `fit_transform` on the Train set, and only `.transform` on the Test set."

### Scenario 2: To Scale or Not to Scale?
*Interviewer:* "Do I need to run `StandardScaler` if I am using a Decision Tree or Random Forest?"

*Answer:* "No. Tree-based models find split points (e.g., 'If Age > 30'). Whether Age is 30, or scaled to 0.5, the tree splits the data identically. However, models based on distance (KNN, SVM, K-Means) or Gradient Descent (Neural Networks, Logistic Regression) absolutely REQUIRE scaling, otherwise large numbers (Salary = $100,000) will mathematically overpower small numbers (Age = 30)."

---

## 10. Common Pitfalls & Debugging in Production

### ⚠️ Pitfall 1: `.fit_transform()` on Test Data
This is the most common bug written by junior data scientists.
```python
# BAD CODE
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.fit_transform(X_test) # WRONG!
```
If you `fit` the scaler on the test data, it calculates a *brand new* Mean and Standard Deviation. The test data is now scaled to a completely different axis than the training data, ruining your predictions.
**The Fix:** Always `fit_transform` on `X_train`, and ONLY `.transform` on `X_test`.

### ⚠️ Pitfall 2: `OneHotEncoder` Unknown Categories
You train a model on data where the "City" column contains "NY" and "SF".
Tomorrow, in production, a user inputs "Chicago". The model crashes because it has never seen "Chicago" and doesn't know how to One-Hot Encode it.
**The Fix:** When defining your `OneHotEncoder`, always use `OneHotEncoder(handle_unknown='ignore')`. This will safely convert unknown cities into an array of all zeros `[0, 0]` without crashing the server.

### ⚠️ Pitfall 3: Pickle Version Mismatches
When you save a Scikit-Learn model to disk using `joblib` or `pickle`, it is deeply tied to the Scikit-Learn version. If you train a model on `scikit-learn==1.2` and try to load it on a server running `scikit-learn==1.4`, it will often crash.
**The Fix:** Always pin your exact `scikit-learn` version in your `requirements.txt` or `pyproject.toml` file. For robust production serialization, consider using ONNX (Open Neural Network Exchange).
