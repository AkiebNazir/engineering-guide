# The MLOps Lifecycle

Machine Learning code is only 5% of a production ML system. The other 95% is glue code, data pipelines, serving infrastructure, and monitoring.

## 1. The Pipeline

```arch
%% caption: An MLOps pipeline automates the extraction of features, training, evaluation, and deployment of a model to a registry.
route straight
node raw "Raw Data\n(Warehouse)" at 0,0 icon=db color=blue
node fs "Feature Store\n(Engineered Data)" at 2,0 icon=package color=amber
node train "Training Pipeline\n(Airflow/Kubeflow)" at 2,1 icon=cpu color=slate
node reg "Model Registry\n(MLflow/SageMaker)" at 0,2 icon=file color=green
node serve "Inference Server\n(Prediction API)" at 2,2 icon=app color=blue

raw -> fs
fs -> train
train -> reg
reg -> serve
```

## 2. Key Differences from Standard DevOps

1. **Code is not enough**: In standard software, if the code is identical, the binary is identical. In ML, the code AND the data produce the model. If the data distribution shifts, the exact same code produces a drastically different (or broken) model. You must version your data alongside your code (e.g., DVC).
2. **Model Decay**: Standard software stays working until you change it or an API breaks. ML models "decay" silently as the real world changes (e.g., a model predicting housing prices trained in 2019 becomes useless in 2021). Continuous retraining is mandatory.
3. **Hardware**: Training requires distributed GPUs. Serving requires optimized CPUs or edge TPUs. The infrastructure is heavily specialized.

## 3. The Model Registry

Just as a Docker Registry stores Docker images, a Model Registry (like MLflow or AWS SageMaker) stores trained models.

A model artifact isn't just weights. A proper registry entry includes:
- The actual model file (e.g., `model.pkl` or `saved_model.pb`).
- The Git commit hash of the code that trained it.
- The hash or URI of the training dataset.
- The hyperparameters used (`learning_rate=0.01`).
- The evaluation metrics (`f1_score=0.92`, `latency=45ms`).

This ensures perfect reproducibility.
