# Serving: Online vs Offline Inference

Once a model is trained, it must generate predictions. The architecture heavily depends on latency requirements.

## 1. Offline (Batch) Inference

- **When to use**: Product recommendations sent via email at 8 AM, calculating churn risk for a dashboard.
- **How it works**: A daily Airflow job spins up a Spark cluster, loads the model, runs predictions for all 10 million users at once, and saves the results to a database (e.g., Cassandra or Postgres).
- **Pros**: High throughput, cheap, no latency SLA concerns.
- **Cons**: Predictions are stale. If a user clicks 5 items in the last 10 minutes, the batch recommendations won't reflect it until tomorrow.

## 2. Online (Real-time) Inference

- **When to use**: Search ranking, fraud detection on a credit card swipe, ad targeting.
- **How it works**: The model is wrapped in an HTTP/gRPC API (using FastAPI, TorchServe, or Triton). When a user makes a request, the API fetches features from the Online Feature Store (Redis), passes them through the model, and returns the result.
- **Pros**: Uses real-time context.
- **Cons**: Strict latency SLAs. Model must execute in <50ms. Requires autoscaling (HPA) to handle traffic spikes.

### The Inference API Bottleneck
Python is slow. If you wrap a PyTorch model in a standard Flask app, the Python Global Interpreter Lock (GIL) and web server overhead will bottleneck the GPU.
Use specialized serving engines like **NVIDIA Triton Inference Server** or **TensorFlow Serving**, which are written in C++, handle dynamic batching (grouping concurrent incoming requests into a single matrix multiplication on the GPU), and maximize hardware utilization.

## 3. Streaming Inference

A hybrid approach. 

- **When to use**: Updating a feed based on real-time activity, detecting anomalies in IoT streams.
- **How it works**: The model listens to a Kafka topic. As events flow in, it makes predictions and writes them to an output Kafka topic.
- **Pros**: Reactive and asynchronous. The user doesn't wait for the HTTP request to finish, but the system reacts within seconds.
