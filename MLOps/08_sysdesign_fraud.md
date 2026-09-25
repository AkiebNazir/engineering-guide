# System Design: Fraud Detection

Unlike Search or RecSys, Fraud Detection must often make a definitive Yes/No decision synchronously before a transaction is allowed to proceed (e.g., a credit card swipe). Latency must be extremely low, and the cost of false positives (declining a valid transaction) is high.

## 1. The Architecture

```arch
%% caption: Fraud detection evaluates transactions synchronously for blocking, and asynchronously for complex network analysis.
route straight
node req "Transaction Request" at 2,0 icon=client color=blue
node rules "Rules Engine\\n(Synchronous)" at 2,1 icon=code color=amber
node ml "ML Model\\n(Synchronous)" at 2,2 icon=cpu color=green
node graph "Graph Analysis\\n(Asynchronous)" at 4,1 icon=network color=slate

req -> rules
rules -> ml : "If rules pass"
req -> graph : "Event stream"
```

### Phase 1: Rules Engine (Heuristics)
Before running expensive ML models, apply hardcoded rules. 
- "If user account is < 1 hour old AND transaction > $5000 -> Block."
- "If user IP is in known bad botnet list -> Block."
Rules are fast, easy to explain, and catch 80% of obvious fraud.

### Phase 2: ML Model (Synchronous)
If the rules pass, invoke the ML model. The model needs real-time features:
- `user_transactions_last_24h`
- `distance_from_last_transaction`
- `device_fingerprint_risk_score`

Since latency is critical, these features must be pre-computed and stored in a low-latency Online Feature Store (like Redis). The model (often a Random Forest or XGBoost, as they are fast and handle tabular data well) returns a probability of fraud (0.0 to 1.0).

### Phase 3: Graph / Network Analysis (Asynchronous)
Fraud rings use complex networks of accounts. A synchronous API call doesn't have time to run a 5-hop graph traversal to see if this user shares a phone number with an account that was banned 3 years ago.
This runs asynchronously in the background. If it detects a fraud ring, it updates the database, blocking the accounts so their *next* transaction is caught by Phase 1.

## 2. Imbalanced Data

In fraud, 99.9% of transactions are legitimate. If a model predicts "Not Fraud" every single time, it will have 99.9% accuracy. Accuracy is a useless metric here.

**Metrics to use:**
- **Precision**: Of the transactions we blocked, how many were actually fraud? (High precision = few angry customers).
- **Recall**: Of all the actual fraud, how much did we catch? (High recall = little money lost).
- **PR-AUC**: Area Under the Precision-Recall Curve.

To train the model, you must use techniques like SMOTE (Synthetic Minority Over-sampling Technique) or down-sample the negative (legitimate) class so the model actually learns what fraud looks like.
