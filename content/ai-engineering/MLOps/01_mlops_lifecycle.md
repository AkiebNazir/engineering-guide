# The MLOps Lifecycle

A model that scores well in a notebook is only the start. To be useful it has to be
retrained when the world changes, shipped without breaking the product, served inside a
latency budget, watched for silent decay, and rebuilt exactly when something goes wrong.
This chapter starts from zero: what MLOps is and what the pieces are. It then walks the
whole lifecycle (data, training, tracking, registry, deployment, monitoring, retraining)
with real config and code, and ends with the failure modes interviewers ask about and a
level-by-level map of what each engineering level is expected to know.

## Foundations — What does it take to run a model in production?

### The problem MLOps solves

Picture a team that builds a spam filter. A data scientist exports a month of labelled
emails, trains a gradient-boosted tree in a notebook, and gets 97% precision on a held-out
set. Everyone is happy. Then the questions start:

- **How does the model get into the mail server?** The notebook is not a service. Someone
  has to package the model, its preprocessing code and its library versions, and put
  them behind an API with a latency budget.
- **Which model is running right now, and how was it built?** Three months later
  precision has dropped. Nobody can say which data, which code commit or which
  hyperparameters produced the model that is live, so nobody can rebuild it or compare
  against it.
- **Who notices when it gets worse?** Spammers change their wording every week. The
  service keeps returning `200 OK` with confident, wrong answers. Nothing in a normal
  CPU/error-rate dashboard turns red.
- **How is it retrained and replaced safely?** Retraining by hand every time is slow and
  error-prone, and swapping in a new model for 100% of traffic at once is how you find
  out in production that it was worse.

**MLOps** (machine learning operations) is the set of practices and systems that answer
those questions. It applies DevOps ideas (version control, automation, CI/CD, monitoring)
to a system whose behaviour is defined by *code plus data*, not code alone.

### The pieces and how they fit

| Piece | What it is | Everyday analogy for the spam filter |
|---|---|---|
| **Data pipeline** | Jobs that collect, clean and validate raw data | Export yesterday's emails and the "report spam" clicks |
| **Feature pipeline / feature store** | Code that turns raw data into model inputs, the same way for training and serving | "Number of links in the email", "sender's domain age" |
| **Training pipeline** | An automated, repeatable job that trains and evaluates a model | The notebook, turned into a scheduled job |
| **Experiment tracker** | A log of every training run: params, metrics, artifacts | A lab notebook that writes itself |
| **Model registry** | The catalogue of trained models, their versions, lineage and which one is live | The "releases" page for models |
| **Serving** | The component that turns inputs into predictions: batch job, API or stream processor | The mail server calling `is_spam(email)` |
| **Monitoring** | Checks on inputs, outputs, latency and (later) true labels | "Spam reports went up 3× since Tuesday" |
| **Feedback loop** | Getting ground-truth labels back and into the next training set | User clicks "not spam" |

They form a loop, not a line. Serving produces predictions and logs, monitoring and
labels flow back into data, and new data triggers the next training run:

```arch
%% caption: The MLOps lifecycle is a loop: serving logs and delayed labels become the next training set, and monitoring decides when to retrain.
grid 150x110
node raw "Raw data" at 0,0 icon=db sub="events, tables"
node feat "Feature pipeline" at 1,0 icon=workflow sub="one definition"
node fs "Feature store" at 2,0 icon=table sub="offline + online"
group ct "Continuous training" color=blue icon=cpu
node train "Train" at 2,1 in ct icon=cpu sub="scheduled or triggered"
node eval "Evaluate + gate" at 1,1 in ct icon=check sub="vs champion"
node reg "Model registry" at 0,1 in ct icon=archive sub="versions, lineage"
group prod "Production" color=green icon=server
node deploy "Deploy" at 0,2 in prod icon=rocket sub="shadow, canary"
node serve "Serving" at 1,2 in prod icon=model sub="batch, API, stream"
node mon "Monitoring" at 2,2 in prod icon=monitor sub="drift, quality"
raw -> feat -> fs
fs -> train
train -> eval
eval -> reg
reg -> deploy
deploy -> serve
serve -> mon
mon ..> train : "retrain trigger"
```

### Where the famous "5% of the code" comes from

**Precision note.** A line you will hear often is "ML code is only 5% of a production ML
system." It comes from the figure in *Hidden Technical Debt in Machine Learning Systems*
(Sculley et al., NeurIPS 2015), which draws the ML code as a small box surrounded by much
larger boxes for data collection, feature extraction, configuration, serving and
monitoring. The paper makes the point with a picture. It does not measure a percentage.
Say "the model code is a small fraction of the system", and name the surrounding boxes.

### Vocabulary you will meet below

| Term | Meaning |
|---|---|
| **Artifact** | Any file a pipeline produces: a dataset snapshot, a trained model, an evaluation report |
| **Lineage** | The recorded chain from a model back to the data, code and config that produced it |
| **Champion / challenger** | The model currently serving vs a candidate that wants to replace it |
| **Continuous training (CT)** | Automatically retraining on a schedule or trigger, the ML addition to CI/CD |
| **Training–serving skew** | The model sees features computed differently in production than in training (chapter 02) |
| **Drift** | The live data or the input→label relationship moves away from what the model learned (chapter 04) |
| **Shadow deployment** | A new model receives a copy of live traffic, but its answers are only logged |
| **Offline vs online metrics** | Metrics on held-out historical data (AUC) vs metrics on live users (CTR, revenue) (chapter 05) |

## 1. The lifecycle end to end

Each stage produces an artifact the next stage consumes, and each one has a typical way
of failing in production.

| Stage | Input → output | Common tools (2026) | How it fails in production |
|---|---|---|---|
| **Ingest + validate** | Raw events/tables → validated snapshot | Spark, dbt, Great Expectations, pandera, TFDV | An upstream team changes a column; the pipeline trains on nulls |
| **Feature engineering** | Snapshot → feature tables | Feast, Databricks Feature Engineering, Vertex AI / SageMaker Feature Store, Hopsworks | Offline SQL and online code disagree (skew); future data leaks into training |
| **Training** | Features + labels → model + metrics | PyTorch, XGBoost/LightGBM, scikit-learn, Ray Train | Non-reproducible runs; overfitting to a stale split |
| **Tracking** | Run → params, metrics, artifacts | MLflow, Weights & Biases, Vertex AI Experiments | Nobody logged the data version, so the run can't be rebuilt |
| **Registry** | Model artifact → versioned, aliased entry | MLflow Model Registry, Vertex AI Model Registry, SageMaker Model Registry | "Which model is live?" has no answer |
| **Validation gate** | Candidate vs champion → promote / reject | Pipeline step with thresholds, slice metrics | A model better on average but much worse for one country ships |
| **Deployment** | Registered model → running service | KServe, Triton, Ray Serve, BentoML, SageMaker endpoints, batch Spark | Preprocessing library version differs from training |
| **Serving** | Features → predictions | See chapter 03 | Latency spike under load; GPU idle because requests are not batched |
| **Monitoring** | Logs, labels → alerts, dashboards | Prometheus/Grafana, Evidently, NannyML, Arize | Everything is green while predictions are wrong |
| **Retraining** | Trigger → new candidate | Airflow, Kubeflow Pipelines, Vertex AI / SageMaker Pipelines | Retrains on data the old model influenced (feedback loop) |

Two loops run at different speeds. The **inner loop** is experimentation: a data scientist
changes features or architecture and trains many runs in a day. The **outer loop** is
production: a pipeline, not a person, retrains, validates and ships. Much of MLOps is
turning what worked in the inner loop into a reliable outer loop.

## 2. How ML systems differ from ordinary software

Most DevOps practice carries over. These are the differences that matter.

1. **Behaviour comes from code *and* data.** In ordinary software, the same source and the
   same build toolchain give the same program. In ML, identical training code run on a
   different data snapshot gives a different model. So you version data alongside code
   (§3), and "what changed?" has three answers to check: code, data, config.
2. **Models decay without anyone touching them.** Ordinary software keeps working until
   someone changes it or a dependency breaks. A model is a snapshot of the world at
   training time. A house-price model trained on 2019 sales was badly off by 2021, when
   interest rates and remote work reshaped demand. Retraining is part of normal operation,
   not an emergency.
3. **Correctness is statistical.** There is no single right output for a unit test to
   assert. You test distributions and thresholds: "AUC on the golden set ≥ 0.85",
   "no slice drops more than 2 points", "output rate of the positive class within 1–4%".
4. **Failures are silent.** A broken model still returns well-formed responses with 200
   status codes. You need ML-specific monitoring (chapter 04) on top of the usual
   latency and error dashboards.
5. **Changing anything changes everything.** Sculley et al. call this CACE: adding one
   feature, changing one threshold or fixing an upstream bug shifts every learned weight.
   A "harmless" upstream fix can hurt a model tuned to the old, buggy values.
6. **Hardware is specialised.** Training large models needs GPUs or TPUs, often many at
   once. Serving ranges from a CPU container for a small tree model to a GPU fleet for a
   deep ranking model or an LLM. The two often run on different clusters with different
   schedulers and budgets.
7. **Reproducibility is harder than it looks.** Even with fixed seeds, some GPU kernels
   are non-deterministic (atomic adds in parallel reductions), data loaders shuffle across
   workers, and library upgrades change numerics. Aim for "reproducible within a tolerance"
   and record everything needed to rebuild: data snapshot, code commit, container image,
   config, seeds.

## 3. Versioning data, code, config and environment

Rebuilding a model needs four things pinned: the **code** (a Git commit), the **data** (an
immutable snapshot or a table version), the **config** (hyperparameters, feature list),
and the **environment** (a container image digest with exact library versions).

| What | How to pin it | Notes |
|---|---|---|
| Code | Git commit SHA | Log it with every run automatically |
| Data (files) | DVC, lakeFS, or content-addressed object storage paths | DVC stores a small pointer file in Git; the data lives in S3/GCS |
| Data (tables) | Delta Lake / Apache Iceberg snapshot or time-travel version | `SELECT … VERSION AS OF 1234` (Delta) or `FOR VERSION AS OF` (Iceberg Spark SQL) |
| Config | A YAML/JSON file in Git, or logged params | Never only in a notebook cell |
| Environment | Container image digest (`sha256:…`), lock file (`uv.lock`, `poetry.lock`) | A tag like `:latest` is not a version |

A minimal DVC workflow for a file-based dataset:

```bash
dvc init
dvc remote add -d storage s3://ml-artifacts/dvc
dvc add data/train.parquet            # writes data/train.parquet.dvc (a hash pointer)
git add data/train.parquet.dvc data/.gitignore
git commit -m "Training snapshot 2026-09-27"
dvc push                              # uploads the data to S3

# later, on another machine or in CI:
git checkout <commit> && dvc pull     # gets exactly the data that commit points to
```

DVC can also describe the pipeline itself as stages in `dvc.yaml`, so `dvc repro` reruns
only the stages whose inputs changed:

```yaml
stages:
  features:
    cmd: python features.py --in data/train.parquet --out data/features.parquet
    deps: [features.py, data/train.parquet]
    outs: [data/features.parquet]
  train:
    cmd: python train.py --features data/features.parquet --params params.yaml
    deps: [train.py, data/features.parquet]
    params: [train.learning_rate, train.max_depth]
    outs: [models/model.json]
    metrics: [metrics.json]
```

For warehouse data, a table format with time travel is usually simpler than copying
files: record the table version with the run, and the training query can be replayed
exactly. See [OLTP vs OLAP & Data Warehouses](../../ship-and-run/DataEngineering/01_oltp_vs_olap.md) and [Batch Processing with Apache Spark](../../ship-and-run/DataEngineering/03_batch_processing_spark.md)
for the warehouse and lakehouse side.

## 4. Experiment tracking and the model registry

A Docker registry stores images; a **model registry** stores trained models with the
metadata needed to trust them. The tracking server records *runs*; the registry promotes a
run's model into a named, versioned entry that deployment reads from.

A registry entry is more than weights. It should carry:

| Field | Example | Why |
|---|---|---|
| Model artifact | `model.json` (XGBoost), `model.onnx`, a PyTorch state dict or exported program | What actually serves |
| Signature | Input schema (names, dtypes), output schema | Serving rejects malformed input instead of mis-predicting |
| Code version | Git SHA `4f2c9e1` | Rebuild and diff |
| Data version | Delta table `features.churn` v1234, or a DVC hash | Rebuild; audit what it learned from |
| Environment | Image digest, `requirements` / lock file | Same library versions at serving time |
| Params | `learning_rate=0.05, max_depth=6` | Rebuild; compare |
| Metrics | `val_auc=0.874`, per-slice metrics, p99 latency on the reference box | Decide promotion |
| Owner, description, model card | Intended use, known limits, fairness checks | Governance and audits |
| Alias / status | `@champion`, `@challenger` | Which version deployment should load |

### Tracking a run and registering a model with MLflow 3

```python
import mlflow
from mlflow import MlflowClient
from mlflow.models import infer_signature
from sklearn.datasets import make_classification
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

mlflow.set_tracking_uri("http://mlflow.internal:5000")
mlflow.set_experiment("churn")

X, y = make_classification(n_samples=20_000, n_features=20, weights=[0.9], random_state=7)
X_tr, X_val, y_tr, y_val = train_test_split(X, y, test_size=0.2, random_state=7)
params = {"learning_rate": 0.05, "max_depth": 6, "max_iter": 300}

with mlflow.start_run(run_name="hgb-weekly") as run:
    mlflow.set_tags({"git_sha": "4f2c9e1", "data_version": "features.churn@v1234"})
    mlflow.log_params(params)
    model = HistGradientBoostingClassifier(**params, random_state=7).fit(X_tr, y_tr)
    auc = roc_auc_score(y_val, model.predict_proba(X_val)[:, 1])
    mlflow.log_metric("val_auc", auc)
    info = mlflow.sklearn.log_model(
        model,
        name="model",                                  # MLflow 3: `name`, not `artifact_path`
        signature=infer_signature(X_val, model.predict_proba(X_val)[:, 1]),
        input_example=X_val[:3],
        registered_model_name="churn-classifier",      # creates a new registry version
    )

client = MlflowClient()
client.set_registered_model_alias("churn-classifier", "challenger", info.registered_model_version)

# Serving code never hard-codes a version number; it resolves the alias.
champion = mlflow.pyfunc.load_model("models:/churn-classifier@champion")
```

**Precision note.** Older tutorials promote models through fixed *stages* (`Staging`,
`Production`, `Archived`) with `transition_model_version_stage`. MLflow deprecated stages
in 2.9 in favour of free-form **aliases** (`@champion`, `@challenger`) and **tags**, and
MLflow 3 keeps that model. Moving the `champion` alias is the promotion; rolling back is
moving it back.

### Promotion flow

```arch
%% caption: A candidate becomes champion only after automated gates pass; rollback is moving the alias back to the previous version.
grid 150x105
node run "Training run" at 0,0 icon=cpu sub="params, metrics"
node v7 "Version 7" at 1,0 icon=archive sub="@challenger"
node gate "Gates pass?" at 2,0 shape=diamond color=amber
node shadow "Shadow / canary" at 2,1 icon=eye sub="live traffic, compare"
node champ "@champion = v7" at 1,1 icon=check color=green sub="deploy reads alias"
node reject "Rejected" at 3,0 icon=error color=red sub="report attached"
node prev "v6 kept" at 0,1 icon=archive sub="one alias move back"
run -> v7 -> gate
gate -> shadow : "yes"
gate -> reject : "no"
shadow -> champ : "healthy"
champ ..> prev : "rollback"
```

## 5. Training pipelines and continuous training

A **training pipeline** is the notebook turned into a directed graph of steps that a
scheduler can run without a person: extract, validate, build features, train, evaluate,
register. **Continuous training (CT)** means the pipeline reruns automatically on:

- a **schedule** (nightly, weekly), the simplest and most common trigger;
- **new data** arriving (an upstream table landed, an Airflow asset updated);
- a **monitoring alert** (drift or a performance drop, chapter 04);
- a **code change** merged to main (CI builds and runs the pipeline on a sample).

An Airflow 3 DAG for a weekly retrain with a promotion gate:

```python
# dags/churn_retrain.py  (Airflow 3.x, TaskFlow API)
from datetime import datetime, timedelta

from airflow.sdk import Asset, dag, task

features_asset = Asset("s3://ml-features/churn/")


@dag(
    schedule=[features_asset],          # run when the feature job updates the asset
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=10)},
    tags=["ml", "churn"],
)
def churn_retrain():
    @task
    def validate_data() -> str:
        # row counts, null rates, value ranges against expectations; raise to fail the run
        return "features.churn@v1235"

    @task
    def train(data_version: str) -> dict:
        # launch the training job (Kubernetes pod, Ray, SageMaker…) and log to MLflow
        return {"version": "8", "val_auc": 0.881, "worst_slice_delta": -0.004}

    @task.short_circuit
    def beats_champion(candidate: dict) -> bool:
        champion_auc = 0.874                      # read from the registry in real code
        return (candidate["val_auc"] >= champion_auc + 0.002
                and candidate["worst_slice_delta"] > -0.01)

    @task
    def mark_challenger(candidate: dict) -> None:
        # MlflowClient().set_registered_model_alias("churn-classifier", "challenger", candidate["version"])
        print(f"v{candidate['version']} is the new challenger")

    candidate = train(validate_data())
    beats_champion(candidate) >> mark_challenger(candidate)


churn_retrain()
```

Airflow 3 moved the authoring API to `airflow.sdk` and renamed *datasets* to **assets**
(data-aware scheduling). The same shape works in Kubeflow Pipelines v2 (`@dsl.component`,
`@dsl.pipeline`), Vertex AI Pipelines, SageMaker Pipelines or Dagster. Orchestration
itself is covered in [Orchestration with Apache Airflow](../../ship-and-run/DataEngineering/05_orchestration_airflow.md).

### The three gates

| Gate | Checks | Blocks |
|---|---|---|
| **Data validation** | Schema, null %, ranges, category sets, row count vs yesterday, label rate | Training on a broken or partial snapshot |
| **Model validation** | Candidate vs champion on the same held-out set; per-slice metrics (country, device, new users); calibration; fairness checks where required | A model that is better on average but worse for a segment |
| **Infra validation** | Model loads in the serving image, p99 latency and memory on the reference hardware, output on golden examples matches offline | A model that is accurate but too slow or too big to serve |

A gate that nobody can override is a gate someone will disable. Make overrides possible,
logged and reviewed.

## 6. Deployment: getting a model live safely

Deploying a model is deploying software, with two extra risks: the preprocessing must
match training exactly, and "worse" is measured statistically, often days later. The
rollout patterns from [Deployment Strategies](../../ship-and-run/CICD/03_deployment_strategies.md) all apply; ML adds shadow mode
and online experiments.

| Pattern | What happens | When to use |
|---|---|---|
| **Shadow (dark launch)** | New model gets a copy of live requests; responses are logged, not returned | First contact with real traffic: latency, errors, prediction distribution, disagreement rate vs champion |
| **Canary** | 1% → 5% → 25% → 100% of traffic, with automatic rollback on guardrail breach | Catch operational problems with a small blast radius |
| **A/B test** | Randomised split, run to a planned sample size, compare business metrics | Decide whether the model is *better* for users (chapter 05) |
| **Interleaving** | Mix two rankers' results into one list, see which one's items get clicked | Ranking changes; needs far less traffic than A/B |
| **Blue/green** | Two full stacks, switch the router | Fast rollback of the whole serving stack |
| **Batch swap** | Next nightly batch job uses the new model | Offline scoring (chapter 03) |

**Package the preprocessing with the model.** Ship one artifact that takes raw request
fields and returns a prediction (an sklearn `Pipeline`, a TorchScript/`torch.export`
program that includes tokenisation, or a model server ensemble), or read every feature
from a feature store that uses the same definitions for training and serving. Two
independently written preprocessing paths will drift apart.

**Pin the runtime.** Build the serving image from the same lock file as training. A
changed default in a library (a tokenizer, a float parser, a resize filter in an image
library) is enough to shift predictions.

## 7. MLOps maturity levels

Google Cloud's widely cited framework ("MLOps: Continuous delivery and automation
pipelines in machine learning") describes three levels. It is a useful way to answer
"how would you improve this team's ML process?"

| Level | What it looks like | Typical pain | Next step |
|---|---|---|---|
| **0 — Manual** | Notebooks; a person trains, exports a file and hands it to engineers; releases a few times a year | Nobody can rebuild the live model; skew between notebook and service; no monitoring | Track experiments, register models, script training |
| **1 — Pipeline automation** | The training pipeline is code and runs on a schedule or trigger (CT); feature store; validation gates; the *pipeline* is deployed, and it produces models | Pipeline changes are still deployed by hand | CI/CD for the pipeline itself |
| **2 — CI/CD for pipelines** | Changes to pipeline code are built, tested and deployed automatically; many pipelines, many models, shared platform | Platform cost and complexity | Self-service platform, governance, cost controls |

The key idea at level 1: **you deploy a training pipeline, not a model.** The pipeline
produces a new model whenever it runs.

## 8. Testing ML systems

Borrowing from Breck et al., *The ML Test Score* (IEEE Big Data 2017), tests fall into four
groups:

| Group | Examples |
|---|---|
| **Feature and data tests** | Feature code unit tests; schema and range checks; no feature is computed from post-label data |
| **Model development tests** | Model beats a simple baseline; hyperparameters were tuned; per-slice quality; model is not stale |
| **Infrastructure tests** | Training is reproducible within tolerance; the model loads and serves in the production image; rollback works |
| **Monitoring tests** | Alerts fire on injected drift; training–serving skew check; prediction quality tracked against labels |

Feature code is ordinary code and deserves ordinary unit tests. This one is runnable with
plain Python:

```python
# test_features.py  (run: python test_features.py, or pytest)
from datetime import datetime, timedelta


def clicks_last_7d(click_times: list[datetime], as_of: datetime) -> int:
    """Clicks in the 7 days strictly before `as_of`. Never counts the future."""
    start = as_of - timedelta(days=7)
    return sum(1 for t in click_times if start <= t < as_of)


def test_window_excludes_future_and_old():
    as_of = datetime(2026, 9, 28, 12, 0)
    clicks = [as_of - timedelta(days=8),       # too old
              as_of - timedelta(days=6),       # counted
              as_of - timedelta(minutes=1),    # counted
              as_of,                           # the prediction moment: excluded
              as_of + timedelta(hours=1)]      # future: must never count
    assert clicks_last_7d(clicks, as_of) == 2


def test_empty_history_is_zero_not_error():
    assert clicks_last_7d([], datetime(2026, 9, 28)) == 0


if __name__ == "__main__":
    test_window_excludes_future_and_old()
    test_empty_history_is_zero_not_error()
    print("ok")
```

Model-level tests are thresholds, not equalities: "on the golden set of 2,000 hand-labelled
emails, precision ≥ 0.95 and recall ≥ 0.80", or behavioural checks ("changing only the
sender's display name must not flip the prediction"). [The Testing Pyramid and Unit Tests](../../ship-and-run/TestingAndQuality/01_testing_pyramid.md)
covers the general testing strategy these slot into.

## 9. Failure modes you will be asked about

| Symptom in production | Likely cause | Detect with | Fix |
|---|---|---|---|
| Offline AUC 0.92, online no lift or worse | Training–serving skew, leakage, or offline metric doesn't match the business goal | Log served features and compare to training features; shadow mode | One feature definition; point-in-time joins (chapter 02); choose offline metrics that track the online one |
| Quality slowly declines over months | Drift: the world changed | Input/output distribution monitors; delayed-label metrics (chapter 04) | Scheduled or triggered retraining |
| Sudden drop after an unrelated deploy | Upstream schema or semantics change (units, enum values, nulls) | Data validation on serving inputs; null/unknown-category rate alerts | Data contracts with upstream teams; fail closed on schema change |
| Can't reproduce last month's model | Data or environment not versioned | Registry entry missing data version or image digest | Log data version, SHA, image digest on every run |
| New model great for most users, terrible for one market | Averaged metrics hid a slice | Per-slice evaluation in the gate | Slice gates; stratified test sets |
| Model reinforces its own past choices | Feedback loop: it only sees labels for what it chose to show or approve | Exploration traffic, counterfactual evaluation | Randomised exploration slice; log propensities (chapters 06, 08) |
| GPU serving costs explode | No batching, oversized model, or wrong instance type | GPU utilisation vs QPS | Dynamic batching, quantisation, distillation (chapter 03) |

## Common interview questions

**How is MLOps different from DevOps?**
DevOps versions and ships code. MLOps also versions data and models, adds continuous
training to CI/CD, tests statistically rather than with exact assertions, and monitors
prediction quality, because a model can decay or break silently while returning 200s.

**What goes in a model registry entry?**
The artifact plus everything needed to trust and rebuild it: input/output signature, code
SHA, data version, environment (image digest), params, metrics including per-slice, owner
and model card, and an alias saying which version is serving.

**How would you make a model reproducible?**
Pin code (Git SHA), data (snapshot or table version), config (logged params) and
environment (image digest, lock file); fix seeds; record all of it automatically in the
tracking system. Accept that GPU training may only be reproducible within a tolerance.

**What triggers retraining?**
A schedule is the baseline. Add triggers for new data, drift or performance alerts, and
code changes. Every retrain still passes the same validation gates before it can replace
the champion.

**How do you deploy a new model safely?**
Gate offline against the champion, including slices and latency. Run it in shadow on live
traffic and compare prediction distributions. Canary with automatic rollback on
guardrails. Run an A/B test to decide on the business metric. Promote by moving an alias,
so rollback is one step.

**What is "level 1" MLOps maturity and why does it matter?**
The training pipeline is automated and deployed, rather than a person handing over a model
file. You deploy the pipeline, and it produces models, so retraining is routine rather
than a project.

**A model's offline metrics are great but it does nothing online. Where do you look?**
First at training–serving skew (log served features, compare to training rows), then
leakage (features that were only available after the label), then the metric mismatch
(offline AUC vs online revenue), then the experiment itself (sample-ratio mismatch,
exposure logging).

**Who owns a production model?**
Name a team that is paged for it, just like a service. The model has an on-call owner, SLOs
(latency, availability, and a quality metric), a runbook with a rollback procedure, and a
retirement plan.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| **Student / Intern** | Intern, new to ML in production | Intern (pre-L3) | Can train a model in a notebook and explain why that is not a production system: no versioning, no serving, no monitoring. Knows what a model registry and a feature are. |
| **Junior (L3)** | ML Engineer I, Software Engineer (ML) | L3 | Turns a notebook into a scripted, tracked training job; logs params, metrics and data version to MLflow; writes unit tests for feature code; can deploy a registered model behind an API following an existing template. |
| **Mid (L4)** | ML Engineer II | L4 | Owns a training pipeline end to end: scheduled CT, data and model validation gates, registry aliases, shadow and canary rollout, basic drift dashboards. Debugs skew and reproducibility problems. |
| **Senior (L5)** | Senior ML Engineer, Senior MLOps / ML Platform Engineer | L5 | Designs the lifecycle for a product area: what triggers retraining, which gates and slices matter, rollout and rollback strategy, label feedback and its biases, cost. Explains the ML-vs-DevOps differences precisely and leads incident reviews for silent model failures. |
| **Staff+ (L6+)** | Staff / Principal ML Engineer, ML Platform lead | L6–L8 | Sets platform direction across many teams: shared feature store, registry and serving standards, maturity roadmap from level 0 to 2, governance (model cards, audits, regulatory requirements), build-vs-buy, and how to measure the platform's value in iteration speed and incidents avoided. |

## Interview checklist

- [ ] I can draw the MLOps loop (data → features → training → registry → deploy → serve → monitor → retrain) and name the artifact each stage produces.
- [ ] I can list at least five ways ML systems differ from ordinary software, including silent failure and CACE.
- [ ] I can say what to version (code, data, config, environment) and how (Git SHA, DVC/table versions, logged params, image digest).
- [ ] I can list what a model registry entry must contain and explain aliases vs the old MLflow stages.
- [ ] I can describe continuous training, its triggers, and the data / model / infra validation gates.
- [ ] I can compare shadow, canary, A/B and interleaving for rolling out a model.
- [ ] I can explain Google's MLOps maturity levels 0, 1 and 2 and "deploy the pipeline, not the model".
- [ ] I can walk a "great offline, flat online" incident: skew, leakage, metric mismatch, experiment bugs.
- [ ] I don't quote "5% of the code" as a measurement; I can name the boxes around the model.

Related: [Feature Stores and Data Leakage](02_feature_stores.md) (skew and leakage), [Serving: Online vs Offline Inference](03_serving_and_inference.md),
[Monitoring and Model Drift](04_model_drift_and_monitoring.md), [Deployment Strategies](../../ship-and-run/CICD/03_deployment_strategies.md),
[Orchestration with Apache Airflow](../../ship-and-run/DataEngineering/05_orchestration_airflow.md), [MLflow Mastery: The Engine of MLOps](../AI-Libraries-Guides/23_mlflow.md),
[ML and LLM Systems](../../interview-core/SystemDesign/building_blocks/23_ml_and_llm_systems.md).
