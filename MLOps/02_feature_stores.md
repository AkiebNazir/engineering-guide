# Feature Stores and Data Leakage

A "Feature" is an individual measurable property being observed (e.g., `user_age`, `num_clicks_last_7_days`). 

## 1. The Problem Feature Stores Solve

Without a Feature Store, you have two disconnected environments:
1. **Offline Training**: A Data Scientist writes a SQL query against the Data Warehouse to calculate `num_clicks_last_7_days` to train the model.
2. **Online Serving**: A Backend Engineer writes Java code that queries Redis or an event stream to calculate `num_clicks_last_7_days` in real-time when the user visits the site so the model can make a prediction.

If the Java code calculates the feature even *slightly* differently than the SQL query, the model will output garbage. This is called **Training-Serving Skew**.

## 2. The Feature Store Architecture

A Feature Store (like Feast or Hopsworks) centralizes feature definitions. You write the logic once.

```arch
%% caption: A Feature Store dual-writes features to an offline warehouse for training and an in-memory database for real-time serving.
route straight
node raw "Raw Data\n(Kafka/Postgres)" at 2,0 icon=db color=blue
node fs "Feature Store\nLogic" at 2,1 icon=code color=amber
node off "Offline Store\n(Batch)" at 0,2 icon=db color=slate
node on "Online Store\n(Real-time)" at 4,2 icon=db color=red
node train "Model Training" at 0,3 icon=cpu color=green
node serve "Inference API" at 4,3 icon=app color=green

raw -> fs
fs -> off
fs -> on
off -> train
on -> serve
```

## 3. Data Leakage (Time Travel)

The most common and devastating bug in ML pipelines is Data Leakage: when your model is trained using information that it would not actually have at prediction time.

**Example**: Predicting if a user will churn next month.
Your training query joins the `users` table with the `transactions` table.
However, the `users` table only has the *current* state of the user. If a user churned in 2023, they might have a flag `is_unsubscribed = True` in the `users` table *today*.
If you use the `users` table as it looks today to generate features for a prediction that supposedly happened in 2022, the model will learn that `is_unsubscribed = True` is a 100% perfect predictor of churn. 

In production, the model will fail entirely.

**Solution**: A Feature Store implements "Point-in-Time Correctness". When generating a training dataset for an event that happened on `2022-01-01`, it automatically rolls back the feature values to exactly what they were at `2022-01-01 23:59:59`, guaranteeing no leakage.
