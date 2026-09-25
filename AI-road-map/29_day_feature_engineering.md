# Day 29: Feature Engineering, Data Imputation & Pipelines

Welcome to Day 29. For the last month, we have assumed that our datasets are perfect grids of numbers. 
In the real world, datasets are absolute nightmares. They are filled with empty blanks (`NaN`), text data (e.g., `"New York"`), and extreme outliers. 

If you feed the word `"New York"` or a `NaN` value into XGBoost or a Neural Network, the algorithm will instantly crash. Math equations cannot multiply words, and they cannot add "nothing". 

Data Scientists spend 80% of their time fixing this exact problem. Today, we learn the mathematical art of **Feature Engineering**—transforming chaotic reality into pure, clean numbers.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The 3 Types of Missing Data
When you see a blank `NaN` in your dataset, you cannot just delete the row. You must figure out *why* it is missing.
- **MCAR (Missing Completely At Random):** A sensor briefly lost battery power, or someone spilled coffee on a survey. The missingness has absolutely no pattern. You can safely fill this blank with the Column Average (Mean).
- **MAR (Missing At Random):** The missingness is tied to *another column*. For example, you are predicting shoe sizes. The "High Heels Preference" column is mostly blank. Why? Because the "Gender" column is Male. The missingness is predictable.
- **MNAR (Missing Not At Random):** The most dangerous type. The missingness depends on the *answer itself*. For example, people with the highest salaries are the most likely to refuse to state their salary. If you fill these blanks with the "Average Salary", you will completely destroy your dataset!

### 2. Imputation (Guessing the Blanks)
How do we mathematically fill in the blanks?
- **Mean/Median Imputation:** Just calculate the average of the column and paste it into the blank. (Terrible for MNAR data).
- **KNN Imputation:** The algorithm looks at a broken row, scans the dataset to find the 5 people who look most mathematically similar to this person, and takes the average of *their* answers.
- **MICE (Multiple Imputation):** The most advanced technique. It literally trains an entirely new Machine Learning model (like a Random Forest) for the sole purpose of predicting what the missing blank *should* have been!

### 3. Encoding (Turning Text into Math)
<abbr title="Artificial Intelligence">AI</abbr> cannot read the word `"Red"`. We must **Encode** it.
- **One-Hot Encoding:** Creates a new binary column for every possible category. (`Is_Red`: 1, `Is_Blue`: 0). 
  - *The Flaw:* If your column is "Zipcode", One-Hot Encoding will create 40,000 new columns! This instantly triggers the **Curse of Dimensionality** (Day 28) and breaks your <abbr title="Artificial Intelligence">AI</abbr>.
- **Target Encoding:** The Kaggle champion secret. Instead of creating new columns, you replace the text with the *average target value*. If predicting House Prices, you replace the word `"New York"` with `$850,000`. It keeps the dimensions small while providing massive Information Gain!

### 4. Data Leakage (The Time Machine Paradox)
Target Encoding is extremely dangerous because of **Data Leakage**.
**The Analogy:** Imagine you are studying for a Final Exam. Accidentally, the teacher leaves the Answer Key for the *actual* exam mixed into your study notes. You memorize it. You score 100% on the practice test. But when you get into the real world with brand new questions, you fail miserably.

If you apply Target Encoding to your *entire dataset* before you split it into `Train` and `Test`, the answers from the `Test` set "leak" into the averages of the `Train` set. The <abbr title="Artificial Intelligence">AI</abbr> will just memorize the averages, score 100% accuracy, and instantly crash in production.
**The Fix:** You MUST split your data into Train/Test *first*, and only calculate the Target Encoding averages using the Train data!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

To prevent Data Leakage, the software engineering industry invented the `Pipeline`. A Pipeline mathematically guarantees that your data is processed, imputed, and scaled in the exact right order, preventing the Test data from ever leaking into the Train data.

Create a file named `feature_pipelines.py`:

```python
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.ensemble import RandomForestClassifier

def build_production_pipeline():
    print("--- BUILDING A PRODUCTION ML PIPELINE ---")
    
    # 1. Create a chaotic, messy dataset
    data = pd.DataFrame({
        'Age': [25, np.nan, 30, 45, np.nan, 22, 50],
        'Salary': [50000, 60000, np.nan, 120000, 40000, 45000, 150000],
        'City': ['NY', 'NY', 'LA', 'LA', 'SF', 'SF', 'NY'],
        'Purchased': [0, 1, 0, 1, 0, 0, 1] # The Target
    })
    
    X = data.drop('Purchased', axis=1)
    y = data['Purchased']
    
    # CRITICAL: Always split first to prevent Data Leakage!
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 2. Define the exact rules for NUMERIC columns (Age, Salary)
    numeric_features = ['Age', 'Salary']
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median')), # Step A: Fill NaNs with Median
        ('scaler', StandardScaler())                   # Step B: Scale numbers from -1 to 1 (Day 28)
    ])
    
    # 3. Define the exact rules for TEXT columns (City)
    categorical_features = ['City']
    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')), # Step A: Fill NaNs with "missing"
        ('onehot', OneHotEncoder(handle_unknown='ignore'))                     # Step B: Convert to 1s and 0s
    ])
    
    # 4. Combine the rules using a ColumnTransformer
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, numeric_features),
            ('cat', categorical_transformer, categorical_features)
        ])
    
    # 5. Build the Ultimate Master Pipeline!
    # It will automatically Route the data, Clean it, and feed it into the AI.
    master_pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('classifier', RandomForestClassifier(random_state=42))
    ])
    
    # 6. Train the AI in one line of code!
    # The Pipeline mathematically ensures no data leakage occurs.
    print("Fitting the Pipeline to the Training Data...")
    master_pipeline.fit(X_train, y_train)
    
    print(f"Training Accuracy: {master_pipeline.score(X_train, y_train)*100:.1f}%")
    print(f"Testing Accuracy:  {master_pipeline.score(X_test, y_test)*100:.1f}%")
    
    # Let's look under the hood at what the Pipeline actually did to the raw data:
    processed_X = preprocessor.transform(X_train)
    print("\nWhat the AI actually sees (Pure Math Matrix):")
    print(np.round(processed_X, 2))

if __name__ == "__main__":
    build_production_pipeline()
```

### Key Takeaways from Code:
1. **The `ColumnTransformer` Routing:** Notice how the `ColumnTransformer` acts like a traffic cop. It rips the dataset apart, sends the numbers to the `numeric_transformer` (which fixes NaNs and scales them), sends the text to the `categorical_transformer` (which turns words into 1s and 0s), and then perfectly stitches them back together before handing them to the Random Forest.
2. **Leakage Prevention:** By calling `master_pipeline.fit(X_train, y_train)`, the `StandardScaler` inside the pipeline *only* calculates the Mean and Variance of the Training data! When we call `.score(X_test)`, it uses the Training data's scaling rules on the Test data, completely eliminating the Time Machine Paradox!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Kaggle Titanic Dataset
The most famous beginner <abbr title="Machine Learning">ML</abbr> dataset is the Titanic.
**Your Task:**
1. Download the Titanic dataset (`import seaborn as sns; df = sns.load_dataset('titanic')`).
2. It is incredibly messy. `Age` has missing values. `Deck` has massive missing values. `Sex` and `Embarked` are categorical text.
3. Build a `Pipeline` exactly like the one above.
4. Try swapping the `SimpleImputer` for a `KNNImputer` from `sklearn.impute`. Does the accuracy improve? 

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"A Junior Data Scientist on your team used 'Target Encoding' to convert $5,000$ unique Zipcodes into numbers. They proudly report a 99% accuracy on the test set. You look at their code and immediately realize they caused severe Data Leakage. Explain exactly how Target Encoding causes leakage, how it ruined the test set, and what mathematical 'Smoothing' technique you must implement to fix it."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Leakage Mechanism:** 
   - Explain that Target Encoding replaces "Zipcode 10001" with the average target answer for that Zipcode. 
   - State clearly that if the Junior Engineer encoded the *entire dataset* before splitting it, the averages literally contain the answers of the Test Set! The model didn't learn patterns; it just memorized the test answers hidden inside the Zipcode averages.
2. **The Rare Category Problem:**
   - Explain that if a Zipcode only appears exactly *once* in the training data, its Target Encoded value will perfectly equal its exact target answer. The <abbr title="Artificial Intelligence">AI</abbr> will instantly realize this and overfit aggressively to that single number.
3. **The Fix (Smoothing & Cross-Validation):**
   - Conclude that Target Encoding must ALWAYS be fit strictly on the Training set. 
   - To fix the rare category problem, you must apply **Smoothing**. This mathematical trick blends the specific Zipcode average with the *Global Average* of the entire dataset. If a Zipcode only has 1 row, the smoothing equation forces its value to be closer to the Global Average, mathematically preventing the <abbr title="Artificial Intelligence">AI</abbr> from memorizing it!

---
**Task for the end of the day:** Commit your code to Git. You now know how to build unbreakable, production-ready <abbr title="Machine Learning">ML</abbr> Pipelines.

Tomorrow, in **Day 30**, we reach the grand finale of Phase 4. You will combine everything you have learned (PCA, XGBoost, Pipelines) into a single, massive **End-to-End Machine Learning Project!**
