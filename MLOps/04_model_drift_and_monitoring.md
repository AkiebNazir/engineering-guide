# Monitoring and Model Drift

You deployed your model. It has 99% accuracy. Six months later, revenue drops by 20% because the model is making terrible predictions. Why?

## 1. Types of Drift

1. **Concept Drift**: The relationship between the features and the target changes. (e.g., Before COVID, buying toilet paper meant nothing. During COVID, it meant panic buying. The meaning of the feature changed).
2. **Data Drift (Covariate Shift)**: The distribution of the input features changes. (e.g., Your model was trained on users aged 18-25. Marketing launches a campaign targeting users aged 50-65. The inputs to the model now look entirely different than the training set).
3. **Upstream Data Changes**: A software engineer renames the `status` column in the database from `Active` to `ACTIVE`. The ML pipeline silently feeds this to the model. The model has never seen `ACTIVE` before, assigns it a weight of 0, and output degrades.

## 2. Monitoring Strategies

Standard DevOps monitoring (CPU, HTTP 500s) is not enough. An ML model will happily return a 200 OK while outputting wildly inaccurate predictions.

### 1. Monitor Model Inputs (Data Quality)
Calculate statistics (mean, median, standard deviation, missing value %) on the incoming requests every hour. Compare them to the statistics of the training dataset using a statistical test (like the Kolmogorov-Smirnov test). If the distribution diverges, fire an alert.

### 2. Monitor Model Outputs
If your fraud model historically predicted that 2% of transactions are fraudulent, and suddenly it's predicting 15% are fraudulent, the model is either broken, or there is a massive attack. Alert on prediction distribution shifts.

### 3. Monitor Ground Truth (Delayed)
The only way to know if a prediction was right is to wait.
If the model predicts a user will click an ad, wait 5 minutes to see if they actually did. Join the predictions with the ground truth in the Data Warehouse, and plot real-time Accuracy, Precision, and Recall in a Grafana dashboard.

## 3. Retraining

When drift is detected, the model must be retrained.
- **Manual Retraining**: A data scientist investigates the drift, curates a new dataset, and trains a new model.
- **Continuous Training (CT)**: Fully automated. Every week, an Airflow job pulls the latest data, trains a model, evaluates it against a holdout set, and if it beats the current production model, deploys it.
