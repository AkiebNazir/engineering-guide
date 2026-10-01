# Serving: Online vs Offline Inference

Once a model is trained, it has to produce predictions for real users, and the way you do
that shapes cost, freshness and latency more than the model itself. This chapter covers
the four serving patterns (batch, online, streaming, on-device), what happens inside a
model server, why **dynamic batching** is the single biggest lever for accelerator
utilisation, how to make models cheaper to run, and how to deploy and scale them on
Kubernetes without falling over when a dependency is slow.

## Foundations — How does a trained model answer a question?

### From file to prediction

A trained model is a file of learned parameters plus a description of the computation
(a tree ensemble, a neural network graph). **Inference** is running that computation on
new inputs to produce an output: a probability, a score, a class, an embedding, some
generated text. To do it for a product you need four things:

1. **A runtime** that can execute the model: XGBoost's own library, PyTorch, ONNX Runtime,
   TensorRT, a JVM library for a tree model.
2. **Inputs in the right form**: the same features, in the same order and encoding, as in
   training (chapter 02).
3. **A way to call it**: a nightly job, an HTTP/gRPC endpoint, a stream consumer, or a
   library inside a phone app.
4. **Somewhere to put the answer**: a table, the API response, an output topic, the screen.

### The four patterns, with an everyday example

A streaming service wants three things from its models:

- **"Top picks for you" in this morning's email.** Nobody is waiting. Score every user
  overnight and store the results: **batch (offline) inference**.
- **Ranking the home screen when a user opens the app.** The user is waiting, and the
  ranking should reflect what they watched five minutes ago: **online (real-time) inference**.
- **Flagging a sudden surge of playback errors from one region.** React within seconds
  to a stream of events, but no user request is blocked on it: **streaming inference**.
- **Blurring faces in a video call on the phone.** No network round trip is acceptable,
  and the video should not leave the device: **on-device (edge) inference**.

| Pattern | Who waits | Freshness | Latency target | Cost profile | Examples |
|---|---|---|---|---|---|
| **Batch** | Nobody | As old as the last run (hours) | None per prediction; the job has a deadline | Cheapest per prediction; big bursts of compute | Email recommendations, churn scores for a dashboard, lead scoring |
| **Online** | A user or a calling service | Uses request-time context | Tens of ms at p99 (≈) for ranking/fraud | Always-on capacity sized for peak | Search ranking, fraud on a card swipe, ad click prediction |
| **Streaming** | Nobody directly, but results needed in seconds | Seconds | Seconds end to end | Always-on consumers | Anomaly detection on IoT, real-time feature updates, content moderation queues |
| **On-device** | The user | Uses local context | ms, no network | Free to you; limited by device | Keyboard suggestions, camera effects, offline translation |

```arch
%% caption: Pick the serving pattern from who is waiting and how fresh the input must be; batch is the cheapest answer whenever it is good enough.
grid 125x110
node q "Someone waiting?" at 1,0 shape=diamond color=amber
node d1 "Known early?" at 0,1 shape=diamond color=amber
node d2 "Device only?" at 2,1 shape=diamond color=amber
node batch "Batch" at 0,2 icon=table sub="precompute, look up"
node stream "Streaming" at 1,2 icon=stream sub="events in, out"
node online "Online API" at 2,2 icon=api sub="request-time data"
node edge "On-device" at 3,1 icon=mobile sub="LiteRT, Core ML"
q:L -> d1:T : "no"
q:R -> d2:T : "yes"
d1 -> batch : "yes"
d1:R -> stream:T : "no"
d2 -> online : "no"
d2 -> edge : "yes"
```

A common hybrid: **precompute what you can, compute online what you must.** A
recommender precomputes candidate lists and item embeddings in batch, then ranks the
candidates online with fresh session features. Batch-scored results can also serve as the
fallback when the online path is slow.

## 1. Batch (offline) inference

A scheduled job loads the current champion model, reads a feature snapshot, scores every
entity and writes the results where the product reads them (a warehouse table for
dashboards, a key-value store for the app).

```python
# batch_score.py  (PySpark job, scheduled nightly by Airflow)
import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

MODEL_URI = "models:/churn-classifier@champion"
FEATURES = ["sessions_7d", "orders_90d", "avg_order_value_90d", "days_since_signup"]

spark = SparkSession.builder.appName("churn-batch-score").getOrCreate()
users = spark.read.table("features.churn_daily").where("ds = '2026-09-27'")


def score(batches):
    import mlflow                                   # imported on the executor
    model = mlflow.pyfunc.load_model(MODEL_URI)     # loaded once per task, not per row
    for pdf in batches:                             # each pdf is an Arrow batch as pandas
        out = pd.DataFrame({"user_id": pdf["user_id"]})
        out["churn_score"] = model.predict(pdf[FEATURES])
        yield out


scored = users.select("user_id", *FEATURES).mapInPandas(
    score, schema="user_id long, churn_score double")
(scored.withColumn("ds", F.lit("2026-09-27"))
       .write.mode("overwrite")
       .option("partitionOverwriteMode", "dynamic")    # replace only this ds partition
       .partitionBy("ds").saveAsTable("predictions.churn"))
```

(`mlflow.pyfunc.spark_udf` wraps the same idea in one call.) Things that matter in batch:

- **Load the model once per worker**, not per row; vectorise with Arrow batches.
- **Write atomically.** Write to a new partition or table version and switch readers to it,
  so the app never reads a half-written result.
- **Record which model version produced each row.** Debugging "why did this user get
  this email?" starts there.
- **Staleness is the cost.** A user who bought five things in the last hour still gets
  yesterday's recommendations. If that matters, add an online re-ranking step.

## 2. Online (real-time) inference

The model sits behind an HTTP or gRPC endpoint. A request carries entity IDs and
request-time context; the service fetches stored features, assembles the feature vector,
runs the model and returns the prediction.

```arch
%% caption: An online prediction spends its budget on feature lookups as much as on the model; every hop has a timeout and a fallback.
grid 150x110
node client "Calling service" at 0,0 icon=app sub="checkout, feed"
node gw "Prediction API" at 1,0 icon=api sub="validate, assemble"
node fs "Online features" at 2,0 icon=kv sub="Redis, 2-5 ms"
group ms "Model server" color=purple icon=model
node q "Batching queue" at 1,1 in ms icon=queue sub="waits up to 2 ms"
node gpu "Model runtime" at 2,1 in ms icon=cpu sub="GPU or CPU"
node log "Prediction log" at 0,1 icon=logs sub="features, score, version"
client -> gw
gw <-> fs
gw -> q -> gpu
gw ..> log : "async"
```

A latency budget for a fraud or ranking call with a 50 ms p99 target might look like this
(all numbers ≈ and illustrative):

| Step | p99 budget |
|---|---|
| Network in and out, TLS already established | 5 ms |
| Request validation, feature vector assembly | 2 ms |
| Online feature store multi-get | 8 ms |
| Queueing for a batch | 2–5 ms |
| Model execution | 10–20 ms |
| Post-processing, logging (async) | 2 ms |
| Headroom for tail effects | ≈ 10 ms |

The model is often not the biggest item. Feature fetches, serialisation and queueing add
up, so measure the whole path.

### A minimal online service

For small CPU models (trees, linear models), a plain Python web service is fine:

```python
# app.py  (FastAPI; run with: uvicorn app:app --workers 4)
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI
from pydantic import BaseModel

MODEL = {}
FEATURES = ["sessions_7d", "orders_90d", "avg_order_value_90d", "days_since_signup"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    import mlflow
    MODEL["m"] = mlflow.pyfunc.load_model("models:/churn-classifier@champion")  # once at startup
    MODEL["version"] = "champion"
    yield


app = FastAPI(lifespan=lifespan)


class Features(BaseModel):
    sessions_7d: int
    orders_90d: int
    avg_order_value_90d: float
    days_since_signup: int


@app.post("/v1/churn:predict")
def predict(f: Features) -> dict:
    x = np.array([[getattr(f, k) for k in FEATURES]], dtype=np.float32)
    score = float(MODEL["m"].predict(x)[0])
    return {"score": score, "model_version": MODEL["version"]}


@app.get("/healthz")
def healthz() -> dict:
    return {"ready": "m" in MODEL}   # readiness: only after the model is loaded
```

Two details: load the model once at startup (not per request), and make the readiness
probe depend on the model being loaded, so Kubernetes does not send traffic to a pod that
is still downloading a 2 GB artifact. A sync `def` endpoint runs in FastAPI's thread pool,
which is right for CPU-bound work that releases the GIL inside native code.

**Precision note on "Python is too slow to serve models".** The heavy math in PyTorch,
XGBoost or ONNX Runtime runs in C++/CUDA and releases the GIL, so Python is rarely the
bottleneck *inside* the model. What hurts a naive Flask/FastAPI GPU server is everything
around it: one request per forward pass (so the GPU runs tiny batches), per-request
JSON parsing and tensor conversion, and one model copy per worker process eating GPU
memory. Dedicated model servers fix those with dynamic batching, zero-copy binary
protocols and shared model instances. Free-threaded CPython (PEP 703, officially
supported from 3.14 but not the default build) doesn't change that picture.

## 3. Model servers

| Server | Good at | Notes (2026) |
|---|---|---|
| **NVIDIA Triton Inference Server** | Many frameworks on GPU: TensorRT, ONNX, PyTorch, TensorFlow, Python backends; dynamic batching; ensembles | C++ core; HTTP/gRPC (KServe v2 protocol); concurrent model instances per GPU |
| **TensorFlow Serving** | TensorFlow SavedModels | Mature, batching built in; TF-only |
| **TorchServe** | PyTorch | In limited maintenance since 2025; prefer Triton, Ray Serve, KServe or a custom server for new work |
| **KServe** | Kubernetes-native `InferenceService` resource; autoscaling, canary, scale to zero | Runs Triton, sklearn, XGBoost, Hugging Face and custom runtimes; CNCF project |
| **Ray Serve** | Python-first composition of models and business logic; batching decorator; autoscaling on Ray | Good for multi-model pipelines written in Python |
| **BentoML** | Packaging a model plus code as a service and container | Adaptive batching; simple developer experience |
| **ONNX Runtime** | Fast CPU/GPU execution of exported models, embedded in any service | A runtime, not a server; often inside the servers above |
| **vLLM, SGLang, TensorRT-LLM** | LLM serving: continuous batching, paged KV cache | See [vLLM Mastery: High-Throughput LLM Serving](../AI-Libraries-Guides/20_vllm.md) and the LLM inference flow in [Module 1 — Generative AI: LLM Architecture & Runtime Internals](../Agentic-AI/01_generative_ai_internals.md) |

For managed options, SageMaker endpoints, Vertex AI endpoints and Azure ML online
endpoints wrap similar runtimes with autoscaling and traffic splitting.

## 4. Dynamic batching

A GPU does a matrix multiply on 32 rows in about the same time as on 1 row, because the
cost is dominated by launching kernels and moving weights through memory, not by the
arithmetic on a few rows. So serving one request per forward pass wastes almost all of
the accelerator. **Dynamic batching** makes the server hold incoming requests in a queue
for a very short time (a few milliseconds at most), group whatever arrived into one
batch, run one forward pass, and split the results back to the waiting callers.

The two knobs:

- **Maximum batch size**: bounded by accelerator memory and by the largest batch whose
  latency still fits the budget.
- **Maximum queue delay**: how long the first request in a batch may wait for company.
  This latency is added to every request at low traffic, so keep it small (≈ 1–5 ms for
  online ranking). At high traffic, batches fill before the delay expires.

The simulation below models an accelerator where each forward pass costs a fixed 8 ms
plus 0.2 ms per row, and sends a burst of 400 concurrent requests:

```python
# micro_batcher.py  (stdlib only)
import asyncio
import time

FIXED_MS, PER_ITEM_MS = 8.0, 0.2          # simulated accelerator: launch cost + per-row cost


async def model_forward(rows: list) -> list:
    await asyncio.sleep((FIXED_MS + PER_ITEM_MS * len(rows)) / 1000)
    return [sum(r) for r in rows]


class MicroBatcher:
    """Collects concurrent requests into one forward pass (what Triton calls dynamic batching)."""

    def __init__(self, max_batch: int = 32, max_wait_ms: float = 2.0):
        self.max_batch, self.max_wait = max_batch, max_wait_ms / 1000
        self.queue: asyncio.Queue = asyncio.Queue()
        self.batches: list[int] = []

    async def predict(self, row):
        fut = asyncio.get_running_loop().create_future()
        await self.queue.put((row, fut))
        return await fut

    async def run(self):
        while True:
            row, fut = await self.queue.get()                 # block for the first request
            batch = [(row, fut)]
            deadline = time.perf_counter() + self.max_wait
            while len(batch) < self.max_batch:                 # then wait briefly for more
                timeout = deadline - time.perf_counter()
                if timeout <= 0:
                    break
                try:
                    batch.append(await asyncio.wait_for(self.queue.get(), timeout))
                except asyncio.TimeoutError:
                    break
            self.batches.append(len(batch))
            outputs = await model_forward([r for r, _ in batch])
            for (_, f), out in zip(batch, outputs):
                f.set_result(out)


async def load_test(n_requests: int, batched: bool):
    lock = asyncio.Lock()                                    # one accelerator: one forward at a time
    batcher = MicroBatcher()
    worker = asyncio.create_task(batcher.run()) if batched else None
    latencies = []

    async def one(i):
        t0 = time.perf_counter()
        if batched:
            await batcher.predict([i, 1.0])
        else:
            async with lock:
                await model_forward([[i, 1.0]])
        latencies.append((time.perf_counter() - t0) * 1000)

    t0 = time.perf_counter()
    await asyncio.gather(*(one(i) for i in range(n_requests)))
    wall = time.perf_counter() - t0
    if worker:
        worker.cancel()
    latencies.sort()
    p50, p99 = latencies[len(latencies) // 2], latencies[int(len(latencies) * 0.99) - 1]
    mean_batch = sum(batcher.batches) / len(batcher.batches) if batched else 1
    print(f"{'batched  ' if batched else 'unbatched'} throughput={n_requests / wall:7.0f} req/s "
          f"p50={p50:6.1f} ms p99={p99:6.1f} ms mean batch={mean_batch:.1f}")


asyncio.run(load_test(400, batched=False))
asyncio.run(load_test(400, batched=True))
```

One run printed:

```text
unbatched throughput=     96 req/s p50=2086.2 ms p99=4120.4 ms mean batch=1.0
batched   throughput=   1865 req/s p50= 115.2 ms p99= 212.5 ms mean batch=30.8
```

With the same simulated hardware, batching gives ≈ 19× the throughput, and because the
queue drains faster, far lower latency under the burst. The numbers come from the
simulated cost model, not a real GPU, but the shape is what real servers show: when a
forward pass has a large fixed cost, batching is close to free throughput.

In Triton, the same thing is a few lines of the model's `config.pbtxt`:

```text
name: "ranker"
platform: "onnxruntime_onnx"
max_batch_size: 64
input [ { name: "features", data_type: TYPE_FP32, dims: [ 256 ] } ]
output [ { name: "score", data_type: TYPE_FP32, dims: [ 1 ] } ]
instance_group [ { count: 2, kind: KIND_GPU } ]
dynamic_batching {
  preferred_batch_size: [ 16, 32 ]
  max_queue_delay_microseconds: 2000
}
```

`instance_group` runs two copies of the model per GPU so one can execute while the other
is being fed. **Continuous batching** for LLMs is a different technique: because each
request generates many tokens, the server adds and removes sequences from the running
batch at every decode step rather than waiting for a whole batch to finish. The LLM
inference flow in [Module 1 — Generative AI: LLM Architecture & Runtime Internals](../Agentic-AI/01_generative_ai_internals.md) animates it.

<div class="lab" data-viz="flow-ml-serving"></div>

## 5. Making models cheaper and faster

| Technique | What it does | Typical effect (≈, measure yours) | Risk |
|---|---|---|---|
| **Export + optimised runtime** | ONNX Runtime, TensorRT, `torch.compile`, XGBoost's native predictor or a compiled tree library | Often 2–5× over eager framework code | Export may not support every op; check numerics |
| **Quantisation** | Store weights (and maybe activations) in INT8, FP8 or 4-bit instead of FP32/FP16 | Smaller memory, faster on hardware with low-precision units | Accuracy loss; calibrate and re-evaluate |
| **Distillation** | Train a small "student" to mimic a large "teacher" | Much cheaper serving at modest quality loss | Needs a training pipeline of its own |
| **Pruning** | Remove weights or whole channels | Smaller model; speedups need structured pruning | Quality loss; hardware may not benefit from unstructured sparsity |
| **Caching** | Cache predictions or embeddings for repeated inputs | Removes work entirely for hot keys | Staleness; cache key must include model version |
| **Cascades** | A cheap model filters, an expensive one scores the survivors | Heavy model sees a fraction of traffic | Recall loss at the cheap stage (chapter 06) |
| **Right hardware** | CPU for trees and small models; GPU/TPU/Inferentia for large dense models | Big cost differences | GPU idle time is expensive; batch or don't use one |

**CPU or GPU?** Gradient-boosted trees and small MLPs usually serve fine on CPUs at a few
ms. Large embedding tables, transformers and image models need accelerators, and then
utilisation (batching) decides the bill.

## 6. Deploying and scaling on Kubernetes

KServe turns a model into a Kubernetes resource. This `InferenceService` serves a
scikit-learn model from object storage, autoscales on in-flight requests and sends 10% of
traffic to the newest revision as a canary (the canary split uses KServe's Knative-based
serverless mode):

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: churn
  namespace: ml-serving
spec:
  predictor:
    minReplicas: 2
    maxReplicas: 20
    scaleMetric: concurrency
    scaleTarget: 8                 # target in-flight requests per replica
    canaryTrafficPercent: 10       # newest revision gets 10%; previous keeps 90%
    model:
      modelFormat:
        name: sklearn
      storageUri: s3://ml-models/churn/v8
      resources:
        requests: { cpu: "1", memory: 2Gi }
        limits:   { cpu: "2", memory: 4Gi }
```

Operational points that come up in interviews:

- **Autoscale on the right signal.** CPU utilisation is a poor signal for GPU serving.
  Use in-flight requests (concurrency), queue depth or GPU utilisation, via Knative, KEDA
  or custom metrics for the Horizontal Pod Autoscaler ([Kubernetes and Orchestration](../Tool-Kit/02_kubernetes_and_helm.md)).
- **Cold starts are slow.** Pulling a multi-GB image and loading weights onto a GPU can
  take minutes. Keep a minimum replica count for online paths, pre-pull images, and
  store weights where nodes can load them quickly. Scale-to-zero suits rarely used
  models, not the checkout path.
- **GPU scheduling.** Request `nvidia.com/gpu` in the pod spec; small models can share a
  GPU through MIG partitions or time-slicing.
- **Separate model and code rollouts** where possible: a new model version should be a
  config change (a new `storageUri` or registry alias) with its own canary.
- **Roll out with shadow first**, then canary, then an A/B test (chapters 01 and 05).

## 7. Streaming inference

A consumer reads events from a topic, scores them and writes results to another topic or
a store. Use it when results are needed within seconds but nobody is blocked waiting.

| Concern | What to do |
|---|---|
| **Throughput** | Score in micro-batches pulled from the consumer (hundreds of events), not one at a time |
| **Ordering** | Partition by entity key so one entity's events are scored in order |
| **Delivery semantics** | At-least-once is the norm; make downstream writes idempotent (key by event ID) |
| **Model updates** | Consumers load the new version at a batch boundary; record the version on every output |
| **Back-pressure** | If scoring falls behind, consumer lag grows; alert on lag and autoscale consumers up to the partition count |

Flink, Spark Structured Streaming and Kafka Streams can host the model in-process, or
call an online model server per micro-batch. See [Stream Processing Fundamentals](../DataEngineering/04_stream_processing.md).

## 8. On-device inference

Models that run on phones, browsers or embedded devices trade model size for zero network
latency, offline operation and privacy. Common runtimes: **LiteRT** (the new name, since
2024, for TensorFlow Lite), **Core ML** on Apple platforms, **ONNX Runtime** mobile and web,
**ExecuTorch** for PyTorch models. The MLOps work shifts to shipping model updates with or
alongside app releases, supporting several model versions in the field at once, and
collecting telemetry without collecting private data.

## 9. Reliability: timeouts, fallbacks and load shedding

A model server is a dependency like any other, and the product must keep working when it
is slow. Patterns from [Application Resilience Patterns](../SystemDesign/building_blocks/12_application_resilience_patterns.md)
and [Overload Control and Graceful Degradation](../SystemDesign/building_blocks/28_overload_control_and_graceful_degradation.md) apply directly:

| Failure | Fallback |
|---|---|
| Feature store timeout | Use defaults for the missing features, flag the response as degraded, log it |
| Model server slow or down | A cheaper model, the last batch-computed score, a popularity list, or a rules-only decision |
| Overload | Shed low-priority traffic first; shrink candidate counts before failing requests |
| Bad new model version | Automatic rollback when canary guardrails (error rate, latency, prediction distribution) breach |

Always return the **model version** (and whether the answer was degraded) with the
prediction and in the prediction log, so later analysis can separate them.

## Common interview questions

**When would you choose batch over online inference?**
When nobody is waiting and the inputs are known ahead of time: emails, dashboards, nightly
scores. It is cheaper and simpler. Choose online when the prediction must use request-time
context or recent behaviour; often combine them (batch candidates, online re-rank).

**What is dynamic batching and what are its knobs?**
The server groups concurrent requests into one forward pass to use the accelerator
efficiently. The knobs are maximum batch size and maximum queue delay; the delay is added
to every request at low load, so it is kept to a few milliseconds for online paths.

**How is continuous batching different?**
It is for autoregressive generation. Sequences join and leave the running batch at every
token step, so short requests do not wait for long ones to finish.

**Your model p99 latency doubled after a deploy. Where do you look?**
Split the latency: feature fetch, queueing, model execution, serialisation. Check whether
the new model is larger, whether batching config changed, whether replicas are cold or
under-provisioned, and whether a feature fetch fan-out grew. Roll back if the canary
guardrail breached.

**How do you autoscale a GPU model server?**
On concurrency, queue depth or GPU utilisation, not CPU. Keep minimum replicas warm
because cold starts are long. Scale-to-zero is for rarely used models.

**How do you make a model 4× cheaper to serve?**
Export to an optimised runtime, quantise (and re-evaluate), batch, cache repeated
predictions, move small models to CPU, distil a smaller student, or put a cheap model in
front as a cascade.

**What happens when the feature store is down?**
The prediction service uses per-feature defaults (the same ones used in training for
missing values), marks the response degraded, and alerts. For critical decisions like
fraud, a rules-based fallback decides instead.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| **Student / Intern** | Intern | Intern (pre-L3) | Can explain batch vs online inference and wrap a model in a simple API that loads it once at startup. |
| **Junior (L3)** | ML Engineer I | L3 | Writes a batch scoring job and an online endpoint with health checks; returns model version; knows why readiness must wait for the model to load. |
| **Mid (L4)** | ML Engineer II | L4 | Chooses a model server, configures dynamic batching, sets latency budgets per hop, deploys with KServe or equivalent, autoscales on the right signal, adds fallbacks. |
| **Senior (L5)** | Senior ML Engineer | L5 | Designs the serving architecture for a product: hybrid batch/online, cascades, hardware choice, quantisation trade-offs, capacity planning, degradation ladder, shadow/canary rollout. |
| **Staff+ (L6+)** | Staff / Principal ML Engineer | L6–L8 | Owns fleet-level serving strategy and cost: shared inference platform, accelerator procurement and utilisation, multi-model packing, reliability standards across teams. |

## Interview checklist

- [ ] I can compare batch, online, streaming and on-device inference by who waits, freshness, latency and cost.
- [ ] I can write a batch scoring job that loads the model once per worker and writes atomically.
- [ ] I can draw the online request path and give a per-hop latency budget.
- [ ] I can explain dynamic batching, its two knobs, and how it differs from continuous batching.
- [ ] I can correct the "Python/GIL is why serving is slow" myth precisely.
- [ ] I can name the main model servers and what each is good at, including TorchServe's status.
- [ ] I can list ways to make a model cheaper to serve and the risk of each.
- [ ] I can deploy a model on Kubernetes with a canary and the right autoscaling signal.
- [ ] I can describe fallbacks for a slow feature store or model server.

Related: [Feature Stores and Data Leakage](02_feature_stores.md), [Monitoring and Model Drift](04_model_drift_and_monitoring.md),
[ML and LLM Systems](../SystemDesign/building_blocks/23_ml_and_llm_systems.md) (model serving),
[vLLM Mastery: High-Throughput LLM Serving](../AI-Libraries-Guides/20_vllm.md), [Kubernetes and Orchestration](../Tool-Kit/02_kubernetes_and_helm.md),
[Deployment Strategies](../CICD/03_deployment_strategies.md).
