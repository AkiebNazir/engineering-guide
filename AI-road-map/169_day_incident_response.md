# Day 169: Incident Response & Chaos Engineering for AI

Welcome to Day 169.

It is 3:00 AM on a Saturday. Your phone screams with a PagerDuty alert. The CEO is awake and angry. The company's customer service <abbr title="Artificial Intelligence">AI</abbr> agent is actively hallucinating, offering users 99% discount codes for expensive electronics, and the users are posting screenshots on Twitter.

What do you do? If your answer is "Log into the server and try to fix the prompt," you will be fired.
In a massive enterprise, you never fix things live during a critical incident. You **Mitigate**, then you **Investigate**.

Today, we learn the dark art of **Site Reliability Engineering (SRE)**. We will learn how to handle <abbr title="Artificial Intelligence">AI</abbr> production incidents, write Runbooks, and intentionally break our own systems using Chaos Engineering.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Incident Response Lifecycle
When an <abbr title="Artificial Intelligence">AI</abbr> goes rogue, you follow a strict protocol:
1. **Triage:** Acknowledge the alert. Gather the team in a Slack channel (e.g., `#incident-ai-discount-bug`).
2. **Mitigation (The Bleeding):** Stop the damage instantly. You DO NOT debug the code. You click a giant red button that degrades the service gracefully (e.g., routing all <abbr title="Artificial Intelligence">AI</abbr> chats to human agents, or rolling back the model version to yesterday's snapshot).
3. **Investigation:** Now that the bleeding has stopped, look at the OpenTelemetry traces (Day 167). Find the root cause.
4. **Resolution:** Write a patch, run it through <abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr> (Day 164), and deploy the fix.
5. **Postmortem:** A blameless meeting where the team discusses *why* the system allowed the failure, and what safeguards will be built to prevent it.

### 2. Runbooks (The SRE Bible)
When you are woken up at 3:00 AM, your brain does not work. You cannot remember AWS <abbr title="Command-Line Interface. A text-based user interface used to view and manage computer files.">CLI</abbr> commands. 
A **Runbook** is a step-by-step markdown document that tells a sleep-deprived engineer exactly what to type to mitigate a specific alert.
*Example:* `Runbook: AI_Hallucination_Alert.md`
`Step 1: Go to AWS API Gateway. Step 2: Change routing rule X to point to Fallback Model Y.`

### 3. Graceful Degradation
If the primary <abbr title="Large Language Model">LLM</abbr> (GPT-4o) goes down, the system should not crash. It should "Degrade Gracefully."
- **Tier 1 (Normal):** GPT-4o powers the agent.
- **Tier 2 (Degraded):** If GPT-4o times out, the system automatically routes to an internally hosted Llama-3-8B. The answers are slightly worse, but the system stays online.
- **Tier 3 (Severely Degraded):** If the GPU cluster dies completely, the system returns a hardcoded string: *"Our <abbr title="Artificial Intelligence">AI</abbr> is currently sleeping. Please email support@company.com."*

### 4. Chaos Engineering
*Analogy:* You don't wait for a fire to test the fire alarms. You set a controlled fire.
**Chaos Engineering** (invented by Netflix) is the practice of intentionally breaking your production systems during business hours to prove that your graceful degradation actually works. 
In <abbr title="Artificial Intelligence">AI</abbr>, this means intentionally injecting corrupted prompts, shutting down the Vector DB, or simulating a 10,000 req/min traffic spike to ensure the Load Balancer (Day 157) holds up.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a highly resilient <abbr title="Artificial Intelligence">AI</abbr> <abbr title="Application Programming Interface">API</abbr> using the **Circuit Breaker** pattern. 
We will simulate a Chaos Engineering experiment where the primary <abbr title="Large Language Model">LLM</abbr> <abbr title="Application Programming Interface">API</abbr> suddenly crashes, and watch our code gracefully degrade to a fallback!

*(Note: To run this exactly, you need `pip install pybreaker`)*

```python
import time
import random
import pybreaker

# --- 1. THE CIRCUIT BREAKER ---
# If the primary function fails 3 times in a row, the breaker "trips" (opens).
# While open, it instantly fails new requests (saving time) for 10 seconds, 
# then "half-opens" to test if the primary is back online.
llm_breaker = pybreaker.CircuitBreaker(fail_max=3, reset_timeout=10)

class AI_System:
    def __init__(self):
        # We simulate a chaos event where the API dies on request #4
        self.request_count = 0 

    @llm_breaker
    def call_primary_llm(self, prompt: str):
        """Tier 1: The Expensive, Smart LLM"""
        self.request_count += 1
        print(f"   [SYSTEM] Attempting Primary LLM (Request {self.request_count})...")
        time.sleep(0.5)
        
        # CHAOS INJECTION: The API crashes on requests 4, 5, and 6!
        if 4 <= self.request_count <= 6:
            raise ConnectionError("OpenAI API 502 Bad Gateway!")
            
        return "This is a brilliant, nuanced answer from GPT-4o."

    def call_fallback_llm(self, prompt: str):
        """Tier 2: The Cheap, Local Fallback"""
        print(f"   [SYSTEM] ⚠️ Routing to Local Fallback Model (Llama-3-8B)...")
        time.sleep(0.1)
        return "This is a basic answer from the local model."

    def generate_response(self, prompt: str):
        try:
            # 1. Try the primary
            return self.call_primary_llm(prompt)
            
        except pybreaker.CircuitBreakerError:
            # 2. If the breaker is TRIPPED, we don't even try the primary. 
            # We instantly hit the fallback, saving 0.5s of timeout latency!
            print("   [BREAKER] 🛑 Circuit is OPEN! Primary is dead. Bypassing instantly.")
            return self.call_fallback_llm(prompt)
            
        except Exception as e:
            # 3. If the primary just failed normally, we catch it and fallback.
            print(f"   [ERROR] {str(e)}")
            return self.call_fallback_llm(prompt)

# --- 2. EXECUTION SIMULATION ---
def run_chaos_experiment():
    print("--- STARTING CHAOS EXPERIMENT ---")
    ai = AI_System()
    
    # Send 8 requests in a row
    for i in range(1, 9):
        print(f"\nUser Request {i}:")
        answer = ai.generate_response("Help me with my account.")
        print(f"Response: {answer}")
        time.sleep(1)

# To run:
# run_chaos_experiment()
```

### 🔍 Understanding the Enterprise Value
If you run this code, Requests 1-3 succeed. On Request 4, the primary fails, we catch the error, and hit the fallback. It fails again on 5 and 6. 
Because it failed 3 times, the Circuit Breaker trips! On Request 7, the system *knows* the primary is dead, so it doesn't even waste 500ms trying to call it. It instantly routes to the fallback, keeping latency low for the user despite a massive backend outage. This is true SRE engineering!

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Currently, our Circuit Breaker only tracks network failures. 
In <abbr title="Artificial Intelligence">AI</abbr>, we also have **Quality Failures**. 
Modify the `call_primary_llm` function. If the <abbr title="Large Language Model">LLM</abbr> generates a response containing the word "discount", manually `raise ValueError("Hallucination Detected")`. Ensure the Circuit Breaker counts this as a failure and trips if the model hallucinates 3 times in a row!

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Your company deployed a massive <abbr title="Retrieval-Augmented Generation">RAG</abbr> system. At 2:00 PM on a Tuesday, users report the <abbr title="Artificial Intelligence">AI</abbr> is responding to all questions in German. You are the Incident Commander. Walk me through your next 60 minutes."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **0:00 - Triage:** Acknowledge the alert, spin up a Zoom bridge, and assign roles (Incident Commander, Lead Investigator, Communications Lead).
2. **0:05 - Mitigation:** We do NOT investigate the prompt or the database yet. We instantly execute `Runbook_A1`. We push a button to rollback the <abbr title="Application Programming Interface">API</abbr> Gateway routing to yesterday's Git commit of the system prompt, or we degrade gracefully to the backup model.
3. **0:15 - Verification:** Confirm via Datadog/Grafana that the bleeding has stopped and users are seeing English again. Update the status page for customers.
4. **0:20 - Investigation:** Now we look at the traces. Did an engineer push a prompt update at 1:55 PM? Did the Vector Database ingest a massive batch of German documents that poisoned the <abbr title="Retrieval-Augmented Generation">RAG</abbr> context? Did the upstream foundational model (e.g., Anthropic) push a silent update to their weights?
5. **0:60 - The Postmortem:** Write a blameless document. *Action Item 1:* Implement a <abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr> test (Day 164) that explicitly fails if the model outputs >10% non-English tokens during staging.

---
**Task for the end of the day:** Look up the concept of a **Blameless Postmortem** (popularized by Google). It is the foundation of healthy engineering cultures.

Tomorrow, in **Day 170**, we finish the MLOps curriculum by tackling the most serious topic in modern <abbr title="Artificial Intelligence">AI</abbr>: **Compliance, Governance, and Ethics**. How do you ensure your <abbr title="Artificial Intelligence">AI</abbr> doesn't break international law?
