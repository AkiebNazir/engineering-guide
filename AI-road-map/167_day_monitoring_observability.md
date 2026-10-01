# Day 167: Advanced Monitoring & Observability (Prometheus, Grafana, OpenTelemetry)

Welcome to Day 167.

In Day 159, we learned the basics of tracking LLM quality using LLM-as-a-Judge. But in a massive enterprise, your AI doesn't run in a vacuum. 
It relies on a vector database, an API Gateway, a Redis cache, and 5 different microservices. If your AI agent suddenly takes 10 seconds to respond, how do you know *which* of those 6 components is causing the bottleneck?

Today, we dive into **Distributed Tracing and Advanced Observability**. We will learn how to instrument your entire AI architecture using OpenTelemetry, Prometheus, and Grafana, and how to define strict SLIs and SLOs.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Observability Triad (Revisited)
- **Metrics (Prometheus):** Time-series data. "We are processing 500 requests per second."
- **Logs (ELK/Loki):** Discrete events. "User 123 requested a summary at 10:05 AM."
- **Traces (OpenTelemetry/Jaeger):** The connective tissue. "Request 123 hit the Gateway (5ms), which queried Redis (20ms), which missed the cache, so it queried Pinecone (200ms), and finally generated text with vLLM (3,500ms)."

### 2. OpenTelemetry (OTel)
Before 2019, if you wanted traces, you had to lock your entire company into proprietary tools like Datadog or New Relic. 
**OpenTelemetry** is a massive open-source standard. You instrument your Python code *once* using the OTel SDK. OTel generates the traces and can export them to *any* backend (Jaeger, Datadog, Zipkin, or LangSmith). It is vendor-agnostic.

### 3. Service Level Indicators (SLIs) and Objectives (SLOs)
You cannot just say "Make the AI fast." You need mathematical contracts.
- **SLI (Indicator):** What are we measuring? (e.g., *The percentage of LLM responses that return the first token in under 500ms*).
- **SLO (Objective):** What is the goal? (e.g., *99% of requests over a 30-day window must meet the SLI*).
- **Error Budget:** If you promise 99% uptime, you are mathematically allowed 1% downtime (about 7 hours a month). If your team burns through that Error Budget by pushing buggy prompts, the CTO freezes all new feature development until reliability improves.

### 4. Golden Signals of AI Monitoring
For standard REST APIs, we monitor Latency, Traffic, Errors, and Saturation (The 4 Golden Signals).
For LLM APIs, we must add:
1. **Time-To-First-Token (TTFT):** Measures responsiveness.
2. **Time-Per-Output-Token (TPOT):** Measures GPU saturation.
3. **Token Usage (In/Out):** Measures cost velocity.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's look at how an ML Engineer instruments a FastAPI application with **OpenTelemetry** to create a distributed trace. This trace will track the exact millisecond breakdown of a RAG query!

*(Note: To run this, you would need `pip install opentelemetry-api opentelemetry-sdk opentelemetry-instrumentation-fastapi`)*

```python
import time
from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# --- 1. SETUP OPENTELEMETRY ---
# In production, this would export to Jaeger or Datadog. 
# For this demo, we export to the Console.
provider = TracerProvider()
processor = BatchSpanProcessor(ConsoleSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

tracer = trace.get_tracer(__name__)
app = FastAPI(title="Instrumented AI Agent")

# Automatically instrument the FastAPI app!
FastAPIInstrumentor.instrument_app(app)

# --- 2. THE DISTRIBUTED TRACE ---

def query_vector_db(query: str):
    """Simulate querying Pinecone."""
    # We create a 'Span' (a specific block of time we want to measure)
    with tracer.start_as_current_span("Pinecone_Vector_Search") as span:
        span.set_attribute("search.query", query)
        
        print("   [DB] Searching vectors...")
        time.sleep(0.2) # Simulating 200ms latency
        
        span.set_attribute("search.results_found", 5)
        return "Relevant context found in DB."

def generate_llm_response(context: str, query: str):
    """Simulate calling an LLM."""
    with tracer.start_as_current_span("vLLM_Generation") as span:
        span.set_attribute("llm.model", "llama-3-8b")
        span.set_attribute("llm.input_tokens", 150)
        
        print("   [GPU] Generating text...")
        time.sleep(1.5) # Simulating 1.5s GPU time
        
        span.set_attribute("llm.output_tokens", 45)
        return "This is the final AI answer."

# --- 3. THE ENDPOINT ---

@app.get("/ask")
async def ask_agent(q: str):
    # The FastAPIInstrumentor automatically creates the "Root Span" for this HTTP request.
    # We will manually create Child Spans inside the helper functions.
    print(f"\n[API] Received query: {q}")
    
    # Trace Step 1
    context = query_vector_db(q)
    
    # Trace Step 2
    answer = generate_llm_response(context, q)
    
    return {"answer": answer}

# --- 4. EXECUTION SIMULATION ---
def run_telemetry_simulation():
    # If you hit this endpoint with a request, the console will print out 
    # a massive JSON trace showing exactly how many milliseconds were spent 
    # in the DB vs the GPU!
    print("Run `uvicorn main:app --reload` and visit http://localhost:8000/ask?q=Hello")

# To run:
# run_telemetry_simulation()
```

### 🔍 Understanding the Enterprise Value
If you deploy this code, and suddenly your AI takes 10 seconds to respond, you don't have to guess why. You open Jaeger (the tracing UI), click the request, and you see a beautiful waterfall chart. 
You instantly see: `Pinecone_Vector_Search (8,000ms)` and `vLLM_Generation (2,000ms)`. You immediately know the database is failing, not the AI model!

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Currently, our spans only track latency and string attributes.
Research **OpenTelemetry Events**. Modify the `generate_llm_response` function so that if the `query` contains a banned word (like "hack"), it adds an Exception Event to the span and instantly returns a 403 Forbidden.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Your team's LLM product has an SLO of 99% availability and a TTFT (Time-To-First-Token) SLI of <800ms. Over the last week, your TTFT has degraded to 1,500ms, burning through your error budget. Walk me through your entire strategy for diagnosing and fixing this."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Diagnosis via Tracing:** State that you will immediately look at the Distributed Traces in Datadog/Jaeger. Does the 1,500ms latency come from the network layer? The vector database? The prompt compression step? Or the vLLM engine itself?
2. **GPU Saturation (Metrics):** If the trace shows the delay is entirely within the vLLM step, check Prometheus metrics for GPU VRAM utilization and the queue depth (tokens-in-flight).
3. **Root Causes:** Identify potential reasons for the spike:
   - *Data Drift:* Users are suddenly pasting massive 20,000 token documents into the prompt, choking the attention mechanism.
   - *Traffic Spike:* The queue is too deep, causing requests to wait 700ms before processing even starts.
4. **Remediation:** 
   - Short term: Horizontally scale the Kubernetes pods to reduce queue depth. 
   - Long term: Implement strict `max_length` limits on the API gateway to prevent massive prompts from choking the system.

---
**Task for the end of the day:** Read about the difference between **Logs** and **Traces**. Why are Traces necessary in a microservice architecture?

Tomorrow, in **Day 168**, we tackle the silent killer of ML models: **Drift**. What happens when the world changes, but your model stays the same?
