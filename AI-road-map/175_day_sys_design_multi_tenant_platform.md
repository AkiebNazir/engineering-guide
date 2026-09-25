# Day 175: System Design: Multi-Tenant <abbr title="Large Language Model">LLM</abbr> Platform

Welcome to Day 175.

Imagine you are the Head of <abbr title="Artificial Intelligence">AI</abbr> Infrastructure at a 10,000-person company. 
- The HR team wants a fine-tuned model to answer policy questions.
- The Engineering team wants a fine-tuned model to write Java code.
- The Marketing team wants a fine-tuned model to write tweets.

If you spin up a dedicated 8-GPU cluster for HR, another for Engineering, and another for Marketing, you will bankrupt the company in a month. Most of the time, those GPUs will sit at 0% utilization while you pay $30/hour for them.

Today, we learn how to design a **Multi-Tenant <abbr title="Large Language Model">LLM</abbr> Platform**. We will learn how to serve hundreds of custom fine-tuned models from a *single* GPU cluster using **S-<abbr title="Low-Rank Adaptation">LoRA</abbr> (Serverless <abbr title="Low-Rank Adaptation">LoRA</abbr>)**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Multi-Tenancy Problem
*Analogy:* You own an apartment building. "Single-Tenancy" means building a separate house for every person, each with its own plumbing and foundation (Very expensive). "Multi-Tenancy" means building one massive foundation and letting hundreds of people share the plumbing, while keeping their living spaces locked and isolated from each other.

In <abbr title="Artificial Intelligence">AI</abbr>, Multi-Tenancy means multiple teams share the same physical GPUs. 
The <abbr title="Application Programming Interface">API</abbr> Gateway must handle:
1. **Routing:** Ensuring HR's prompt goes to the HR model.
2. **Isolation:** Ensuring Marketing cannot read HR's private prompts.
3. **Quotas:** If Engineering writes an infinite `while` loop, they should be rate-limited before they crash the cluster for Marketing.

### 2. The <abbr title="Low-Rank Adaptation">LoRA</abbr> Serving Revolution (S-<abbr title="Low-Rank Adaptation">LoRA</abbr> / Lorax)
In Day 91, we learned that Fine-Tuning a 70B model requires changing all 70 billion weights. <abbr title="Low-Rank Adaptation">LoRA</abbr> (Low-Rank Adaptation) freezes the 70B model and only trains a tiny "Adapter" file (about 100MB).
In production, this is a superpower.
Instead of loading 100 different massive models into VRAM, you load the **Base Model** (Llama-3) *once*. 
When a request comes in, the server dynamically swaps the tiny 100MB HR Adapter into VRAM in 5 milliseconds, generates the text, and unloads it. 
This allows a single GPU cluster to serve thousands of different fine-tuned models simultaneously!

### 3. The Platform Architecture
A true enterprise platform has three layers:
1. **Control Plane (The Brain):** An <abbr title="Application Programming Interface">API</abbr> gateway that handles Auth (Bearer tokens), Quotas (Redis Rate Limiting), and Cost Attribution (FinOps from Day 160).
2. **Data Plane (The Muscle):** The vLLM / Lorax inference servers running on the Kubernetes GPU pods.
3. **Management Plane (The UI):** A web dashboard where Marketing can upload their dataset, click "Fine-Tune", and instantly get a deployed <abbr title="Application Programming Interface">API</abbr> endpoint without talking to an engineer.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual FastAPI **Control Plane** for a Multi-Tenant architecture. It will authenticate the user, check their budget, and route the request to the correct <abbr title="Low-Rank Adaptation">LoRA</abbr> adapter!

```python
import time
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel

app = FastAPI(title="Enterprise Multi-Tenant AI Platform")

# --- MOCK INFRASTRUCTURE ---

# The internal database of Teams and their assigned LoRA adapters
TENANT_DB = {
    "token_hr_123": {"team": "HR", "adapter_id": "lora_hr_policy_v2", "budget_remaining": 5.00},
    "token_eng_456": {"team": "Engineering", "adapter_id": "lora_java_coder_v1", "budget_remaining": 100.00},
    "token_mkt_789": {"team": "Marketing", "adapter_id": "lora_tweet_gen_v5", "budget_remaining": 0.00} # Out of money!
}

class CompletionRequest(BaseModel):
    prompt: str

# --- 1. AUTH & QUOTA MIDDLEWARE (Control Plane) ---

def authenticate_and_check_quota(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Token")
    
    token = authorization.split(" ")[1]
    tenant = TENANT_DB.get(token)
    
    if not tenant:
        raise HTTPException(status_code=403, detail="Invalid Tenant")
        
    if tenant["budget_remaining"] <= 0:
        raise HTTPException(status_code=402, detail="Tenant out of budget. Please contact Finance.")
        
    return tenant

# --- 2. LORA ROUTER (Data Plane Simulation) ---

def simulate_lora_vllm_cluster(prompt: str, adapter_id: str):
    """
    Simulates a vLLM / Lorax server.
    Notice it only takes 5ms to load the custom adapter!
    """
    print(f"   [GPU CLUSTER] ⚡ Dynamically loading adapter: {adapter_id} (5ms)")
    time.sleep(0.005) 
    
    print(f"   [GPU CLUSTER] Generating text using Base Model + {adapter_id}...")
    time.sleep(0.5) # GPU Compute
    
    if "java" in adapter_id:
        return "public static void main(String[] args) {}"
    elif "policy" in adapter_id:
        return "According to HR policy, you have 15 PTO days."
    else:
        return "Buy our product!"

# --- 3. THE API ENDPOINT ---

@app.post("/v1/completions")
async def generate(req: CompletionRequest, tenant: dict = Depends(authenticate_and_check_quota)):
    print(f"\n[GATEWAY] Request from Team: {tenant['team']}")
    
    # 1. Route to the GPU cluster, explicitly passing the team's custom adapter
    response = simulate_lora_vllm_cluster(req.prompt, tenant["adapter_id"])
    
    # 2. Cost Attribution (Deduct from their specific budget)
    cost = 0.05
    tenant["budget_remaining"] -= cost
    print(f"[FINOPS] Deducted ${cost:.2f} from {tenant['team']} budget. Remaining: ${tenant['budget_remaining']:.2f}")
    
    return {"response": response}

# --- EXECUTION ---
def run_platform_simulation():
    # Simulate HR making a request
    # tenant = authenticate_and_check_quota("Bearer token_hr_123")
    # print(generate(CompletionRequest(prompt="How much PTO do I get?"), tenant))
    pass

# To run:
# uvicorn main:app --reload
```

### 🔍 Understanding the Enterprise Value
This is a true Platform-as-a-Service (PaaS). 
Marketing, Engineering, and HR are all hitting the exact same `v1/completions` endpoint. They are all sharing the exact same pool of GPUs. But because the Gateway dynamically injects their specific <abbr title="Low-Rank Adaptation">LoRA</abbr> `adapter_id` based on their auth token, they feel like they each have a dedicated, personalized <abbr title="Artificial Intelligence">AI</abbr>. The company saves 90% on GPU costs.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Research **Lorax** (by Predibase) or **S-<abbr title="Low-Rank Adaptation">LoRA</abbr>**. Understand the mechanism of "Continuous Batching with <abbr title="Low-Rank Adaptation">LoRA</abbr>." How does the server handle a situation where Request A needs the HR Adapter, and Request B needs the Engineering Adapter, and they arrive at the exact same millisecond? (Hint: The GPU batches the base model weights, but applies the adapter weights separately per sequence!)

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Design an internal <abbr title="Large Language Model">LLM</abbr> platform for a 10,000-person company. The platform must allow non-technical PMs to upload a CSV of data, click 'Fine-Tune', and instantly get a deployed <abbr title="Application Programming Interface">API</abbr> endpoint without involving the infrastructure team."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The Self-Service Pipeline:** Draw the UI uploading the CSV to S3. This triggers a serverless function that formats the data into JSONL.
2. **The Orchestrator:** The serverless function triggers an Airflow/Dagster pipeline (Day 161). The pipeline spins up a Kubernetes job to run the <abbr title="Low-Rank Adaptation">LoRA</abbr> fine-tuning script.
3. **The Model Registry:** Once training finishes, the Airflow job uploads the 100MB <abbr title="Low-Rank Adaptation">LoRA</abbr> adapter to the MLflow Model Registry (Day 163).
4. **Dynamic Loading (Zero Downtime):** The Airflow job updates the `TENANT_DB` (PostgreSQL) to associate the new adapter ID with the PM's team. The PM immediately gets an email with their <abbr title="Application Programming Interface">API</abbr> key. When they use it, the GPU cluster pulls the adapter from the Registry directly into VRAM. No <abbr title="A set of platform as a service products that use OS-level virtualization to deliver software in packages called containers.">Docker</abbr> containers had to be rebuilt!

---
**Task for the end of the day:** Review the concept of **Multi-Tenancy** in <abbr title="Software as a Service - A software licensing and delivery model in which software is licensed on a subscription basis and is centrally hosted.">SaaS</abbr> applications.

Tomorrow, in **Day 176**, we design the final system of this curriculum: **A Document Intelligence Pipeline**. How do you process 100,000 messy, scanned legal PDFs a day and turn them into structured database rows using OCR and LLMs?
