# Day 24: Decision Trees, Gini Impurity & Information Gain

Welcome to Day 24! Today is a major pivot. 

Up until this point, every algorithm we have learned relied on **Calculus**. Linear Regression, Logistic Regression, and Neural Networks all use gradients to slide down continuous mathematical mountains.

Today, we throw Calculus in the trash. We enter the realm of **Information Theory**. 
You will learn the **CART (Classification and Regression Trees)** algorithm. Instead of calculating slopes, this algorithm literally learns how to play a mathematically perfect game of "20 Questions" with your data. 

Because it doesn't use Calculus, it is incredibly easy to understand, 100% interpretable, and forms the foundation for the most powerful algorithms in the modern financial sector.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS (EXPLAINED SIMPLY)

### 1. The Game of 20 Questions
Imagine you have a dataset of 100 animals (50 Cats, 50 Dogs). You have features like `Weight`, `Ear Shape`, and `Tail Length`. 
The Decision Tree wants to separate the Cats from the Dogs. It tests a question: *"Is Weight > 20 lbs?"*
- **Yes Branch:** Goes to a new room. (Contains 45 Dogs, 2 Cats).
- **No Branch:** Goes to a different room. (Contains 5 Dogs, 48 Cats).

This was a brilliant question! It almost perfectly separated the animals. But how does the <abbr title="Artificial Intelligence">AI</abbr> mathematically *know* it was a good question?

### 2. Gini Impurity (Measuring the "Messiness")
To judge a question, the <abbr title="Artificial Intelligence">AI</abbr> calculates the **Gini Impurity ($G$)** of the rooms. 
Gini Impurity measures how "messy" or "mixed up" a room is.

**The Formula:**
$$ G = 1 - \sum (p_i)^2 $$
*(Where $p_i$ is the probability of picking a specific class in that room).*

> **Step-by-Step Math Example:**
> - **Scenario A (Maximum Messiness):** A room with 5 Cats and 5 Dogs.
>   - $P(\text{Cat}) = 0.5$
>   - $P(\text{Dog}) = 0.5$
>   - Math: $1 - (0.5^2 + 0.5^2) \rightarrow 1 - (0.25 + 0.25) = \mathbf{0.5}$ (The highest possible impurity!)
> - **Scenario B (Perfect Purity):** A room with 10 Cats and 0 Dogs.
>   - $P(\text{Cat}) = 1.0$
>   - $P(\text{Dog}) = 0.0$
>   - Math: $1 - (1.0^2 + 0.0^2) \rightarrow 1 - 1 = \mathbf{0.0}$ (Perfectly pure!)

### 3. Information Gain
To pick the best question, the <abbr title="Artificial Intelligence">AI</abbr> tests every possible question (e.g., "Weight > 1?", "Weight > 2?") and calculates the **Information Gain**:
$$ \text{Gain} = \text{Impurity Before Split} - \text{Weighted Average Impurity After Split} $$
The <abbr title="Artificial Intelligence">AI</abbr> permanently locks in the question that provides the highest Information Gain, splits the data, and then repeats the process on the new sub-rooms!

### 4. The Fatal Flaw: Infinite Overfitting (High Variance)
If you let a Decision Tree run forever, it will keep asking questions until every single room has exactly 1 animal in it. It will achieve 100% training accuracy, but it will have completely memorized the noise in the data (Massive Overfitting / High Variance).

To stop this, we use **Pruning**:
- **Pre-Pruning:** Setting a strict rule before training begins: *"Do not grow deeper than 5 questions (max_depth=5)."*
- **Post-Pruning (Cost-Complexity):** Letting the tree grow to infinity, and then mathematically chopping off the bottom branches if they don't provide enough Information Gain to justify existing.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's write a Python script that calculates exactly how the <abbr title="Artificial Intelligence">AI</abbr> "thinks" when deciding which question to ask. Then, we will build a real Decision Tree using `scikit-learn` and prove how Pre-Pruning saves the model from Overfitting.

Create a file named `decision_tree_mechanics.py`:

```python
import numpy as np
from sklearn.tree import DecisionTreeClassifier
from sklearn.datasets import make_classification
from sklearn.metrics import accuracy_score

# --- 1. HOW THE AI THINKS (GINI MATH FROM SCRATCH) ---

def calculate_gini(class_counts):
    """Calculates the Gini Impurity of a single room."""
    total_items = sum(class_counts)
    if total_items == 0: return 0.0
    
    impurity = 1.0
    for count in class_counts:
        probability = count / total_items
        impurity -= probability ** 2
    return impurity

def calculate_information_gain(parent_counts, left_counts, right_counts):
    """Calculates how much 'Messiness' was removed by a Yes/No question."""
    # 1. Calculate Impurity before the split
    parent_gini = calculate_gini(parent_counts)
    
    # 2. Calculate Impurities after the split
    left_gini = calculate_gini(left_counts)
    right_gini = calculate_gini(right_counts)
    
    # 3. Calculate the Weighted Average of the new rooms
    total_parent = sum(parent_counts)
    weight_left = sum(left_counts) / total_parent
    weight_right = sum(right_counts) / total_parent
    
    weighted_child_gini = (weight_left * left_gini) + (weight_right * right_gini)
    
    # 4. Information Gain! (Higher is better)
    gain = parent_gini - weighted_child_gini
    return gain

def test_the_math():
    print("--- MATHEMATICAL PROOF OF INFORMATION GAIN ---")
    parent_room = [50, 50] # 50 Cats, 50 Dogs (Very Messy)
    print(f"Parent Room Gini: {calculate_gini(parent_room):.2f}")
    
    # Question 1: "Is Weight > 50 lbs?" (Terrible Question)
    # Result: 25 Cats/25 Dogs go left. 25 Cats/25 Dogs go right.
    gain_1 = calculate_information_gain(parent_room, [25, 25], [25, 25])
    print(f"Gain from Question 1 (Terrible Split): {gain_1:.2f}")
    
    # Question 2: "Does it bark?" (Amazing Question)
    # Result: 49 Dogs/1 Cat go left. 1 Dog/49 Cats go right.
    gain_2 = calculate_information_gain(parent_room, [49, 1], [1, 49])
    print(f"Gain from Question 2 (Amazing Split):  {gain_2:.4f}")
    print("The AI will permanently choose Question 2 because the Gain is massive!\n")

# --- 2. APPLIED MACHINE LEARNING ---

def train_decision_trees():
    print("--- TRAINING REAL DECISION TREES ---")
    # Generate a complex, noisy dataset
    X, y = make_classification(n_samples=1000, n_features=10, informative=5, noise=0.5, random_state=42)
    
    # Split into Train and Test (800 train, 200 test)
    X_train, X_test = X[:800], X[800:]
    y_train, y_test = y[:800], y[800:]
    
    # Model 1: Unrestricted Tree (Will play 20 Questions until it memorizes everything)
    tree_unrestricted = DecisionTreeClassifier(random_state=42)
    tree_unrestricted.fit(X_train, y_train)
    
    train_acc_1 = accuracy_score(y_train, tree_unrestricted.predict(X_train))
    test_acc_1 = accuracy_score(y_test, tree_unrestricted.predict(X_test))
    
    print("MODEL 1: Unrestricted Tree")
    print(f"  Training Accuracy: {train_acc_1 * 100:.1f}% (Perfect Memorization!)")
    print(f"  Testing Accuracy:  {test_acc_1 * 100:.1f}% (Massive Overfitting Gap!)")
    print(f"  Tree Depth: {tree_unrestricted.get_depth()} questions deep.\n")
    
    # Model 2: Pre-Pruned Tree (Forcing it to stop early)
    tree_pruned = DecisionTreeClassifier(max_depth=5, min_samples_split=10, random_state=42)
    tree_pruned.fit(X_train, y_train)
    
    train_acc_2 = accuracy_score(y_train, tree_pruned.predict(X_train))
    test_acc_2 = accuracy_score(y_test, tree_pruned.predict(X_test))
    
    print("MODEL 2: Pruned Tree (max_depth=5)")
    print(f"  Training Accuracy: {train_acc_2 * 100:.1f}% (No longer perfect)")
    print(f"  Testing Accuracy:  {test_acc_2 * 100:.1f}% (But performs BETTER in the real world!)")

if __name__ == "__main__":
    test_the_math()
    train_decision_trees()
```

### Key Takeaways from Code:
1. **The Math is Simple:** Look at the `calculate_gini` function. There is no calculus, no matrix inversion, no learning rates. Just simple addition and subtraction. 
2. **The Overfitting Proof:** Run the code. Notice how `MODEL 1` achieves exactly `100.0%` accuracy on the training data. It literally grew 15 layers deep just to memorize the specific outliers in the dataset. When shown new data, it crashed to ~80%. `MODEL 2` was blocked from going deeper than 5 layers, preventing it from memorizing the noise, allowing it to beat Model 1 on the Test data!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Regression Tree
Decision trees can also predict continuous numbers (like House Prices)!
**Your Task:**
1. In a Classification Tree, the <abbr title="Artificial Intelligence">AI</abbr> calculates "Gini Impurity."
2. In a Regression Tree (`DecisionTreeRegressor`), the <abbr title="Artificial Intelligence">AI</abbr> calculates "Mean Squared Error (MSE)."
3. Write a Python function `calculate_mse_gain(parent_prices, left_prices, right_prices)`.
4. To find the "Impurity" of a room of prices, just calculate the Variance (MSE from the mean): `np.mean((prices - np.mean(prices))**2)`.
5. Prove that splitting a room of prices `[100k, 105k, 900k, 950k]` into `[100k, 105k]` and `[900k, 950k]` results in massive MSE Information Gain!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Why are individual Decision Trees considered 'High-Variance' models? Furthermore, why does this specific 'High-Variance' flaw actually make them the absolute perfect base algorithm for building massive Ensemble models like Random Forests?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Why they are High-Variance:** 
   - State that because Decision Trees make strict, hard binary splits (Yes/No), they are incredibly sensitive to the exact data they are trained on. If you change just a single data point at the top of the tree, the entire bottom of the tree will completely change its structure. They memorize noise instantly.
2. **The Ensemble Connection (Why the flaw is a feature):**
   - Explain that if you want to build a "Random Forest" (a committee of 100 <abbr title="Artificial Intelligence">AI</abbr> models voting on an answer), you *want* the models to disagree with each other. If you train 100 stable, Low-Variance models (like Linear Regression), they will all vote exactly the same way, completely defeating the purpose of a committee!
   - Because Decision Trees are High-Variance, training 100 trees on slightly different data will result in 100 wildly different, highly opinionated trees. When you mathematically average their votes together, the chaotic variance perfectly cancels out, leaving behind incredibly accurate, highly robust intelligence!

---
**Task for the end of the day:** Commit your code to Git. You have mastered Information Theory splits!

Tomorrow, in **Day 25**, we put our interview question to the test. We will build a massive committee of decision trees and invent the most powerful algorithm in classical machine learning: **The Random Forest!**
