# Day 173: System Design: Real-Time Fraud Detection

Welcome to Day 173.

When you swipe your credit card at a grocery store, the payment terminal connects to Visa. Visa has exactly **50 milliseconds** to approve or deny the transaction. 
If they approve a stolen card, the bank loses money. If they deny a legitimate card, the customer gets furious and switches to Mastercard.

Designing a Fraud Detection system is one of the most intense MAANG interview questions because it combines extreme latency constraints with extreme class imbalance (99.9% of transactions are legitimate).

Today, we learn the **Multi-Model Cascade** and the critical role of the **Feature Store**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Extreme Class Imbalance
If you build a model that just guesses "Not Fraud" every single time, it will be 99.9% accurate! 
Therefore, Accuracy is a useless metric for Fraud. We optimize for **Recall** (catching as much fraud as possible) and **Precision** (not angering innocent customers). 
To train the model, we use techniques like SMOTE (Synthetic Minority Over-sampling) to artificially inflate the 0.1% of fraud cases so the neural network can learn from them.

### 2. The Multi-Model Cascade
Because we only have 50ms, we cannot run a massive <abbr title="Large Language Model">LLM</abbr> or a 100-layer Neural Network. We use a cascade:
- **Layer 1 (The Rule Engine):** Takes 1ms. Hardcoded `if/else` rules written by humans. (e.g., *If transaction > $10,000 AND IP Address is from a sanctioned country $\rightarrow$ BLOCK*). If the rule triggers, the transaction is instantly denied.
- **Layer 2 (Gradient Boosting):** Takes 10ms. A lightning-fast <abbr title="Machine Learning">ML</abbr> model (like XGBoost or LightGBM). It looks at complex non-linear patterns (e.g., *User is in New York, but their phone's GPS is in London*). 
- **Layer 3 (Asynchronous Graph / <abbr title="Large Language Model">LLM</abbr>):** Takes 2,000ms. This runs *after* the transaction is approved. It analyzes massive graph networks to find coordinated crime rings. If it finds fraud, it flags the account to be blocked before the *next* swipe.

### 3. Velocity Features & The Feature Store
The most important indicator of fraud is Velocity. 
*Example:* A user spends $5 on coffee at 8:00 AM, $10 on gas at 8:15 AM, and $2,000 on electronics at 8:16 AM. 
To the <abbr title="Machine Learning">ML</abbr> model, the $2,000 transaction looks normal *unless* it knows about the previous two swipes!
We use a **Streaming Feature Store** (like Redis + Apache Flink). When a swipe occurs, Flink updates the `user_spend_last_10_min` counter in Redis in under 5ms. The <abbr title="Machine Learning">ML</abbr> model pulls this feature from Redis to make its prediction.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual Python implementation of a 50ms Real-Time Fraud Cascade!

```python
import time
import random

# --- MOCK INFRASTRUCTURE ---

class RedisFeatureStore:
    def get_user_features(self, user_id: str):
        # Extremely fast in-memory lookup (1-2ms)
        return {
            "account_age_days": 400,
            "spend_last_10_min": random.choice([0, 50, 5000]), # The crucial velocity feature!
            "distance_from_home_miles": random.choice([2, 500])
        }

class RuleEngine:
    def evaluate(self, transaction: dict, features: dict) -> str:
        """L1: Hardcoded rules. Executes in 1ms."""
        if transaction['amount'] > 10000 and features['account_age_days'] < 1:
            return "DENY" # Massive transaction on a brand new account
        return "PASS"

class LightGBMModel:
    def predict(self, transaction: dict, features: dict) -> float:
        """L2: The ML Model. Executes in 10ms."""
        # Mocking an ML prediction. High velocity + far from home = Fraud.
        if features['spend_last_10_min'] > 1000 and features['distance_from_home_miles'] > 100:
            return 0.95 # 95% probability of fraud
        return 0.05

# --- THE FRAUD PIPELINE ---

class PaymentGateway:
    def __init__(self):
        self.feature_store = RedisFeatureStore()
        self.rules = RuleEngine()
        self.ml_model = LightGBMModel()
        
    def process_transaction(self, user_id: str, amount: float, ip_location: str):
        start_time = time.time()
        print(f"\n--- SWIPE: User {user_id} | Amount: ${amount} ---")
        
        transaction = {"amount": amount, "ip": ip_location}
        
        # 1. Fetch Real-Time Features
        features = self.feature_store.get_user_features(user_id)
        
        # 2. L1: Rule Engine
        rule_decision = self.rules.evaluate(transaction, features)
        if rule_decision == "DENY":
            print(f"❌ DENIED by Rule Engine in {(time.time() - start_time)*1000:.1f}ms")
            return
            
        # 3. L2: ML Model
        fraud_probability = self.ml_model.predict(transaction, features)
        
        latency = (time.time() - start_time) * 1000
        
        if fraud_probability > 0.80:
            print(f"❌ DENIED by ML Model (Score: {fraud_probability:.2f}) in {latency:.1f}ms")
            # In production, we would trigger an async process here to text the user: 
            # "Did you just try to spend $X at Y?"
        else:
            print(f"✅ APPROVED (Score: {fraud_probability:.2f}) in {latency:.1f}ms")

# --- EXECUTION ---
def run_fraud_simulation():
    gateway = PaymentGateway()
    
    # Simulate a normal swipe
    gateway.process_transaction(user_id="U123", amount=15.00, ip_location="NY")
    
    # Simulate an anomalous swipe (The random mock data will likely trigger the ML model)
    gateway.process_transaction(user_id="U999", amount=2500.00, ip_location="London")

# To run:
# run_fraud_simulation()
```

### 🔍 Understanding the Enterprise Value
Notice the speed. The system fetched contextual data from Redis, ran a deterministic rule engine, and ran a Machine Learning model—all conceptually within our 50ms budget. If this was a massive deep learning model, the customer would be standing awkwardly at the cash register waiting for the green light!

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
When a transaction is approved, the `spend_last_10_min` feature in Redis must be updated instantly so the *next* swipe has the correct context.
**Your Task:** Research **Apache Flink**. It is a stream-processing framework. Understand how Flink connects to a Kafka stream of approved transactions and performs "Windowed Aggregations" (calculating the sum of the last 10 minutes continuously) to update Redis.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Design Stripe's real-time fraud detection system. You process 10,000 transactions per second. What is your architecture, how do you handle feature computation, and what is your strategy for Concept Drift when fraudsters change tactics?"*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The Architecture:** Draw the <abbr title="Application Programming Interface">API</abbr> Gateway routing to a highly available microservice. Explain the Rule Engine $\rightarrow$ <abbr title="Machine Learning">ML</abbr> Model cascade to meet latency constraints.
2. **Feature Computation:** Differentiate between Batch Features (calculated nightly in Snowflake, like `average_monthly_spend`) and Streaming Features (calculated in real-time via Kafka/Flink, like `spend_last_5_minutes`). Both are served to the <abbr title="Machine Learning">ML</abbr> model via a Redis Feature Store.
3. **Graph Analysis (Async):** Acknowledge that the real-time pipeline is blind to massive coordinated attacks. Propose a separate, asynchronous pipeline using a Graph Database (Neo4j) to detect rings of connected IP addresses and stolen devices.
4. **Human-in-the-Loop & Drift:** Fraudsters adapt daily. When the <abbr title="Machine Learning">ML</abbr> model flags a transaction with medium confidence (e.g., 60-80%), it routes to a human reviewer. The human's decision acts as Ground Truth data to continuously retrain the <abbr title="Machine Learning">ML</abbr> model (mitigating Concept Drift).

---
**Task for the end of the day:** Review the definition of **Precision vs. Recall**. In fraud detection, understand why optimizing purely for Recall (catching all fraud) will result in millions of angry, blocked legitimate customers (False Positives).

Tomorrow, in **Day 174**, we design an <abbr title="Artificial Intelligence">AI</abbr> system you likely use every day: **An Autonomous Coding Assistant (like GitHub Copilot)**. How does it know what code to suggest when you type a comment?
