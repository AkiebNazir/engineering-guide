   # Day 159: Evaluation in Production (Metrics, Monitoring & Alerting)

Welcome to Day 159.

When you deploy a standard <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> <abbr title="Application Programming Interface">API</abbr>, you monitor strict metrics: Latency, Error Rate (<abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> 500s), and <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> usage. If latency spikes, you get an alert, and you fix it.
But when you deploy an <abbr title="Large Language Model">LLM</abbr> <abbr title="Application Programming Interface">API</abbr>, these metrics are completely blind to **Quality Degradation**. 
If your model suddenly starts hallucinating or leaking private data, the <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> status code will still be `200 OK`. The latency will be perfect. From an infrastructure perspective, the server is healthy. From a business perspective, your company is on fire.

Today, we learn **Online Evaluation**. We will learn how to monitor the *quality* of <abbr title="Large Language Model">LLM</abbr> outputs in real-time using Prometheus, Grafana, and <abbr title="Large Language Model">LLM</abbr>-as-a-Judge.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Observability Triad
In DevOps, we rely on three pillars:
- **Metrics (Prometheus):** Aggregated numbers over time (e.g., "Cache Hit Rate is 45%").
- **Logs (ELK/Loki):** Raw, searchable text of every single <abbr title="Large Language Model">LLM</abbr> input and output.
- **Traces (Jaeger/LangSmith):** The step-by-step waterfall of a single request (User $\rightarrow$ Gateway $\rightarrow$ <abbr title="Retrieval-Augmented Generation">RAG</abbr> Retriever $\rightarrow$ Prompt $\rightarrow$ GPU $\rightarrow$ Output).

### 2. Online vs. Offline Evaluation
- **Offline Evaluation:** Running a test suite of 500 prompts *before* deploying to production.
- **Online Evaluation:** Evaluating real user queries *in production*. Because you don't know what users will ask, you cannot use Exact Match. You must use implicit signals and <abbr title="Large Language Model">LLM</abbr>-as-a-Judge.

### 3. Implicit Signals (The Free Metrics)
You can deduce <abbr title="Large Language Model">LLM</abbr> quality without reading the text by monitoring user behavior:
1. **Regeneration Rate:** If a user clicks "Regenerate Response", the first response was likely bad. If this rate spikes above 5%, trigger an alert.
2. **Session Length:** If a user asks 20 follow-up questions to accomplish a 2-step task, the <abbr title="Large Language Model">LLM</abbr> is probably failing to follow instructions.
3. **Copy/Paste Rate:** If the <abbr title="Large Language Model">LLM</abbr> generates code and the user immediately hits the "Copy" button, the code is likely good!

### 4. <abbr title="Large Language Model">LLM</abbr>-as-a-Judge (The Expensive Metric)
You cannot read 10,000 production logs a day. 
Instead, you build an asynchronous pipeline. You sample 5% of all production traffic. You send the user's prompt and the model's response to a much smarter, more expensive model (e.g., GPT-4) and ask it to grade the response on a scale of 1-5 for:
- **Faithfulness:** Did it hallucinate facts?
- **Helpfulness:** Did it actually answer the user's question?
- **Toxicity:** Did it swear or exhibit bias?

If the rolling average of "Helpfulness" drops below 4.0, Prometheus fires an alert to PagerDuty to wake up the engineering team.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a mock production monitoring pipeline. We will simulate an <abbr title="Application Programming Interface">API</abbr> Gateway that processes requests, logs metrics to Prometheus, and asynchronously sends a sample to an <abbr title="Large Language Model">LLM</abbr>-as-a-Judge for quality scoring!

*(Note: To run this exactly, you need `pip install prometheus_client`)*

```python
import time
import random
import threading
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# --- 1. PROMETHEUS METRICS SETUP ---
# These variables will be scraped by Grafana to build real-time dashboards!

# Infrastructure Metrics
REQUEST_COUNT = Counter('llm_requests_total', 'Total LLM requests')
LATENCY = Histogram('llm_latency_seconds', 'Latency of LLM requests')

# Quality Metrics (The AI-Specific part!)
REGENERATION_COUNT = Counter('llm_regenerations_total', 'User clicked regenerate')
QUALITY_SCORE = Gauge('llm_quality_score_rolling', 'Rolling average of LLM-as-a-Judge score')

# --- 2. ASYNC LLM-AS-A-JUDGE ---

class QualityEvaluator:
    def __init__(self):
        self.scores = []

    def evaluate_async(self, prompt, response):
        """Runs in the background. Does not slow down the user's API response!"""
        def run_judge():
            print(f"   [EVALUATOR] Judging response to: '{prompt}'...")
            time.sleep(1) # Simulate calling GPT-4
            
            # Simulate GPT-4 grading the response (1 to 5)
            # We inject a simulated bug: if prompt contains "math", the model fails.
            if "math" in prompt.lower():
                score = random.choice([1, 2])
            else:
                score = random.choice([4, 5])
                
            self.scores.append(score)
            
            # Keep rolling average of last 10
            recent_avg = sum(self.scores[-10:]) / len(self.scores[-10:])
            
            # UPDATE THE PROMETHEUS GAUGE!
            QUALITY_SCORE.set(recent_avg)
            print(f"   [EVALUATOR] Score: {score}/5. Rolling Avg: {recent_avg:.2f}")
            
            # TRIGGER ALERT IF QUALITY DROPS!
            if recent_avg < 3.0:
                print("   [PAGERDUTY ALERT] 🔥 QUALITY DEGRADATION DETECTED! Rolling avg < 3.0!")

        threading.Thread(target=run_judge).start()

# --- 3. THE PRODUCTION API PIPELINE ---

evaluator = QualityEvaluator()

def process_api_request(prompt: str, is_regeneration: bool = False):
    REQUEST_COUNT.inc()
    if is_regeneration:
        REGENERATION_COUNT.inc()
        
    start_time = time.time()
    
    # 1. Simulate the LLM Generation
    print(f"\n[API] Processing: '{prompt}'")
    time.sleep(random.uniform(0.1, 0.5)) 
    response = "This is the generated response."
    
    # 2. Record Latency
    LATENCY.observe(time.time() - start_time)
    
    # 3. Sample 100% of traffic for this demo (In reality, sample 5%)
    evaluator.evaluate_async(prompt, response)
    
    return response

# --- 4. EXECUTION SIMULATION ---

def run_production_simulation():
    # Start the Prometheus server on port 8000
    # Grafana would connect to this port to draw the charts!
    start_http_server(8000)
    print("Prometheus Metrics Server running on http://localhost:8000")
    
    # Good Traffic
    process_api_request("Write a poem.")
    process_api_request("Explain physics.")
    time.sleep(2)
    
    # Simulated Model Regression (Suddenly users are asking math, and the model is failing!)
    print("\n--- SIMULATING MODEL REGRESSION ---")
    for _ in range(5):
        process_api_request("Do this math problem.")
        time.sleep(0.5)
        
    time.sleep(3) # Wait for async evaluators to finish

# To run:
# run_production_simulation()
```

### 🔍 Understanding the Enterprise Value
In a real enterprise, your Grafana dashboard will have a massive green line for "Quality Score". 
If an engineer accidentally pushes a bad system prompt to production, the <abbr title="Large Language Model">LLM</abbr> will start outputting garbage. The users will complain, but long before the users tweet about it, your async <abbr title="Large Language Model">LLM</abbr>-as-a-Judge will rate the garbage as `1/5`. The rolling average will plummet, Grafana will turn red, PagerDuty will call your phone at 2:00 AM, and you will roll back the prompt before the CEO notices.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
The pipeline above uses <abbr title="Large Language Model">LLM</abbr>-as-a-Judge. This costs money.
Modify the script to implement **Heuristic Evaluation** (free evaluation). Write a function that checks the `response` string. If it contains phrases like "I am sorry," "I am just an <abbr title="Artificial Intelligence">AI</abbr>," or "I cannot fulfill this request," immediately log a `Model Refusal` metric to Prometheus. Track how often your model is refusing to answer users!

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Your <abbr title="Large Language Model">LLM</abbr> system's quality degrades gradually over 2 weeks. Users haven't explicitly complained, but internal metrics show a 15% drop in session length. Design the detection, diagnosis, and remediation system."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Detection:** We must rely on the Observability Triad. Explain how Prometheus tracks implicit signals (session length, copy/paste rate) and explicit signals (<abbr title="Large Language Model">LLM</abbr>-as-a-Judge scores). 
2. **Diagnosis (Root Cause Analysis):**
   - Did the prompt change? Check the Prompt Registry version history.
   - Did the model change? If using OpenAI, did they silently update the weights of `gpt-4-turbo` behind the <abbr title="Application Programming Interface">API</abbr>?
   - **Data Drift:** Did the user demographic change? Are we suddenly getting requests in Spanish, and our <abbr title="Retrieval-Augmented Generation">RAG</abbr> database only has English documents?
3. **Remediation:** If it's a prompt issue, instantly roll back to `v1.0`. If it's Data Drift, trigger an automated data pipeline to embed Spanish translations into the Vector DB.
4. **Prevention:** Implement Shadow Deployments. Never release a prompt/model update to 100% of users. Route 10% of traffic to the new version (Canary) and let the <abbr title="Large Language Model">LLM</abbr>-as-a-Judge compare the new version's score against the old version automatically.

---
**Task for the end of the day:** Review **Prometheus** and **Grafana**. They are the undisputed kings of infrastructure monitoring.

Tomorrow, in **Day 160**, we look at the other side of production monitoring: **Cost Engineering (FinOps)**. We will learn how to build architectures that prevent you from accidentally burning $50,000 in a single weekend!
