# Machine Learning System Design (MLOps)

Start here. This module is about everything between a data scientist's notebook and a
model that reliably serves millions of users: versioning, training pipelines, feature
stores, serving, monitoring, experimentation, and the architecture of the three classic
ML systems that come up in interviews (recommendations, search, fraud detection).

**Who it is for:** software engineers moving into ML engineering or ML platform work,
ML engineers preparing for ML system design interviews, and backend engineers who need
to integrate, serve or operate models. Each chapter starts with a *Foundations* section
for readers new to the topic and ends with interview questions, a level-by-level table
(Student to Staff+) and a checklist.

## Reading order

Chapters 1–5 are the MLOps building blocks; read them in order. Chapters 6–8 are full
ML system design answers that use those blocks; read them after 1–5, in any order.

| # | Chapter | What you learn |
|---|---|---|
| 1 | [The MLOps Lifecycle](01_mlops_lifecycle.md) | The lifecycle loop, how ML differs from ordinary software, versioning data/code/environment, MLflow 3 tracking and registry aliases, an Airflow 3 continuous-training DAG with gates, rollout patterns, maturity levels, testing ML |
| 2 | [Feature Stores and Data Leakage](02_feature_stores.md) | Training–serving skew, offline vs online stores, point-in-time (as-of) joins with a runnable example, kinds of leakage, Feast in practice, streaming features, feature logging; live flow of both paths |
| 3 | [Serving: Online vs Offline Inference](03_serving_and_inference.md) | Batch, online, streaming and on-device inference; model servers; dynamic batching with a runnable simulation and Triton config; making models cheaper; KServe on Kubernetes; fallbacks; live flow of a prediction under load |
| 4 | [Monitoring and Model Drift](04_model_drift_and_monitoring.md) | Kinds of drift vs pipeline breakage, monitoring layers, PSI and KS with runnable code, delayed labels, Prometheus metrics and alerts, triage and retraining strategies; live flow from alert to gated retrain |
| 5 | [A/B Testing and Experimentation](05_ab_testing.md) | Experiment design, sample size, hash assignment, p-values done right, CUPED, peeking (simulated), SRM, novelty, interference, interleaving, off-policy evaluation, bandits, a model launch sequence |
| 6 | [System Design: Recommendation Systems](06_sysdesign_recsys.md) | Video recommendations end to end: requirements, estimates, two-tower retrieval, multi-task ranking and value blend, diversity re-ranking, cold start, evaluation, trade-offs, follow-ups |
| 7 | [System Design: Search and Ranking](07_sysdesign_search.md) | Product search end to end: query understanding, hybrid BM25 + dense retrieval with RRF, LambdaMART and cross-encoders, click-label biases, NDCG, index freshness, follow-ups |
| 8 | [System Design: Fraud Detection](08_sysdesign_fraud.md) | Real-time payment fraud end to end: sync/async split, rules + model + decision policy, velocity and graph features, label delay and selection bias, cost-based thresholds, adversarial drift |

The module has 8 chapters and 3 live animated flows (feature store paths in chapter 2,
online serving with dynamic batching in chapter 3, drift alert to retrain in chapter 4).

## Prerequisites

- Python and basic ML vocabulary (training vs test set, a classifier, precision and
  recall). [Scikit-Learn Mastery](../AI-Libraries-Guides/03_scikit_learn.md) and [XGBoost Mastery: The King of Tabular Data](../AI-Libraries-Guides/04_xgboost.md) cover the
  libraries used in examples.
- Comfort with services, queues and databases at the level of
  [Building Blocks of Any System](../../interview-core/SystemDesign/building_blocks/00_overview.md).
- Helpful but optional: Docker and Kubernetes ([Docker and Containerization](../../ship-and-run/Tool-Kit/01_docker_and_containers.md),
  [Kubernetes and Orchestration](../../ship-and-run/Tool-Kit/02_kubernetes_and_helm.md)) and batch/stream processing
  ([Batch Processing with Apache Spark](../../ship-and-run/DataEngineering/03_batch_processing_spark.md), [Stream Processing Fundamentals](../../ship-and-run/DataEngineering/04_stream_processing.md)).

## Related modules

- [ML and LLM Systems](../../interview-core/SystemDesign/building_blocks/23_ml_and_llm_systems.md) and
  [Ranking, Recommendation, and Experimentation](../../interview-core/SystemDesign/building_blocks/31_ranking_recommendation_and_experimentation.md): the system design building blocks
  these chapters build on.
- [Ranked Home Feed](../../interview-core/SystemDesign/solutions/032_ranked_home_feed_solution.md) (feed cascade infrastructure),
  [Search and Autocomplete](../../interview-core/SystemDesign/solutions/009_search_and_autocomplete_solution.md), [Experimentation Platform](../../interview-core/SystemDesign/solutions/037_experimentation_platform_solution.md).
- `content/ship-and-run/DataEngineering/`: warehouses, Spark, streaming, Airflow and dbt, the data side of
  every pipeline here.
- `content/ship-and-run/CICD/`: deployment strategies and feature flags used for model rollouts.
- `content/ai-engineering/Agentic-AI/` and `content/ai-engineering/AI-Libraries-Guides/`: LLM serving, RAG, vector databases, MLflow,
  vLLM.
