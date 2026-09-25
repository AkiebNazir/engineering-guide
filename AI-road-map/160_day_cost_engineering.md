# Day 160: Cost Engineering & FinOps for <abbr title="Large Language Model">LLM</abbr> Systems

Welcome to Day 160.

<abbr title="Artificial Intelligence">AI</abbr> is the most expensive software paradigm in history.
If you build an image resizer, it costs a fraction of a cent in <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> compute. If you build an <abbr title="Large Language Model">LLM</abbr> Agent that loops 15 times parsing a 50-page PDF, it can easily cost $2.00 *per click*. If a malicious user writes a script to click that button 10,000 times while you sleep, you wake up to a $20,000 AWS bill.

Today, we learn **FinOps (Financial Operations)**. We will learn how to aggressively monitor costs, attribute them to specific teams, and implement **Cascade Routing** to slash your OpenAI bill by 80%.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Anatomy of <abbr title="Large Language Model">LLM</abbr> Costs
Unlike traditional APIs, LLMs charge per **Token**.
- **Input Tokens (Cheap):** The prompt you send.
- **Output Tokens (Expensive):** The text the model generates. Output tokens are often 3x to 5x more expensive because of the memory-bound decoding bottleneck.
*Rule of Thumb:* Never ask the <abbr title="Large Language Model">LLM</abbr> to output massive blocks of text if you just need a Boolean `True/False` or a tiny <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> object. Use `max_tokens` aggressively.

### 2. Cascade Routing (The 80% Cost Saver)
*Analogy:* If you need to solve $5 + 5$, you don't hire a PhD Mathematician ($500/hour). You hire a high school student ($15/hour). If you need to invent a new quantum algorithm, *then* you hire the PhD.

Most queries to your application are simple ("Summarize this paragraph"). You do not need GPT-4o for this.
**Cascade Routing** uses a tiny, lightning-fast <abbr title="Large Language Model">LLM</abbr> (like Llama-3-8B or Haiku) to classify the difficulty of the prompt.
- If Difficulty = Easy $\rightarrow$ Route to Haiku (Costs $0.25 / 1M tokens).
- If Difficulty = Hard $\rightarrow$ Route to GPT-4o (Costs $5.00 / 1M tokens).
By routing 80% of traffic to the cheap model, your monthly bill plummets.

### 3. Prompt Compression
If you have a 10,000 token System Prompt containing 50 few-shot examples, you pay for those 10,000 tokens *on every single <abbr title="Application Programming Interface">API</abbr> call*.
**Prompt Compression** uses an <abbr title="Large Language Model">LLM</abbr> (once) to read the prompt and rewrite it, removing stop words and condensing instructions. You can often shrink a prompt by 40% with zero loss in generation quality. (Or, as we learned in Day 152, use Prefix Caching!).

### 4. Hard Limits & Billing Attribution
In an enterprise, the "Marketing Team" and the "Engineering Team" might both use your internal <abbr title="Application Programming Interface">API</abbr> Gateway.
You must attach a `team_id` to every request. The Gateway tracks the tokens used and bills them to the correct department's budget.
**Hard Limits:** If a user/team exceeds their monthly $500 budget, the Gateway must physically block them with an `HTTP 402 Payment Required` error. Never rely on "soft alerts"—a runaway `while` loop can burn $10,000 in an hour before you read the email alert.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a **FinOps Gateway**. It will implement Cascade Routing, track the exact cost down to the fraction of a cent, and enforce a Hard Budget limit!

```python
import time

class FinOpsGateway:
    def __init__(self, monthly_budget_cents=500): # $5.00 budget
        self.budget_cents = monthly_budget_cents
        self.spend_cents = 0
        
        # PRICING (per 1,000 tokens)
        self.pricing = {
            "gpt-4o": {"input": 0.50, "output": 1.50},       # $0.005 / $0.015 per token
            "claude-haiku": {"input": 0.025, "output": 0.125} # $0.00025 / $0.00125 per token
        }

    def _calculate_cost(self, model, input_tokens, output_tokens):
        in_cost = (input_tokens / 1000) * self.pricing[model]["input"]
        out_cost = (output_tokens / 1000) * self.pricing[model]["output"]
        return in_cost + out_cost

    def _classify_difficulty(self, prompt: str) -> str:
        """The Cascade Router: Determines if prompt is Easy or Hard."""
        hard_keywords = ["code", "analyze", "complex", "calculate", "reason"]
        if any(word in prompt.lower() for word in hard_keywords):
            return "HARD"
        return "EASY"

    def execute_query(self, prompt: str):
        print(f"\n[USER QUERY] '{prompt}'")
        
        # 1. HARD LIMIT CHECK
        if self.spend_cents >= self.budget_cents:
            print(f"   [ERROR 402] Budget Exhausted! Spend: {self.spend_cents}c / {self.budget_cents}c")
            return "ERROR: Budget exceeded."

        # 2. CASCADE ROUTING
        difficulty = self._classify_difficulty(prompt)
        
        if difficulty == "HARD":
            model = "gpt-4o"
            print("   [ROUTER] Classified as HARD. Routing to expensive GPT-4o.")
        else:
            model = "claude-haiku"
            print("   [ROUTER] Classified as EASY. Routing to cheap Claude-Haiku.")

        # 3. SIMULATE EXECUTION & TOKEN COUNTING
        time.sleep(0.5)
        # Mocking token counts: Hard questions require longer answers
        input_tokens = len(prompt.split()) * 2 
        output_tokens = 500 if difficulty == "HARD" else 50 
        
        # 4. FINOPS ATTRIBUTION
        cost_cents = self._calculate_cost(model, input_tokens, output_tokens)
        self.spend_cents += cost_cents
        
        print(f"   [METRICS] Model: {model} | In: {input_tokens} | Out: {output_tokens}")
        print(f"   [BILLING] Cost for query: {cost_cents:.3f} cents.")
        print(f"   [BILLING] Total Month Spend: {self.spend_cents:.3f}c / {self.budget_cents}c")
        
        return "Generated Answer."

# --- EXECUTION SIMULATION ---
def run_finops_sim():
    # Only a $1.00 budget!
    gateway = FinOpsGateway(monthly_budget_cents=100) 
    
    # Query 1: Easy (Cheap)
    gateway.execute_query("What is the capital of France?")
    
    # Query 2: Hard (Expensive)
    gateway.execute_query("Analyze this Python code and find the memory leak.")
    
    # Simulate a massive attack/loop
    print("\n--- SIMULATING MASSIVE USAGE SPEND ---")
    for _ in range(5):
        gateway.execute_query("Write a complex application with reasoning.")
        
# To run:
# run_finops_sim()
```

### 🔍 Understanding the Savings
If the system didn't have Cascade Routing, the "Capital of France" question would have been sent to GPT-4o, costing 20x more than necessary. 
Furthermore, notice how the Gateway accurately tracks fractions of a cent, and physically blocks execution once the 100-cent ($1.00) budget is hit, saving the company from ruin!

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Currently, our cascade router uses a simple python `if/else` keyword check. This is brittle.
**Your Task:** Research **Semantic Routing**. There are open-source libraries (like `semantic-router`) that use blazing fast vector embeddings (running locally in 5ms) to classify the intent of a prompt with 99% accuracy before deciding which <abbr title="Large Language Model">LLM</abbr> to call. 

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"You're the engineering manager for an <abbr title="Artificial Intelligence">AI</abbr> platform. The CEO asks: 'Why does our <abbr title="Artificial Intelligence">AI</abbr> feature cost $1M/month?' Build the FinOps framework: cost attribution, optimization roadmap, and reporting."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Attribution:** We cannot just look at the AWS/OpenAI bill. The Gateway must inject headers (`TeamID`, `FeatureID`) into every request. Logs must be pushed to a Data Warehouse (Snowflake) to create a dashboard showing exactly which feature/team is burning the money.
2. **Immediate Optimization (Caching & Routing):** 
   - Deploy a Semantic Cache (Saves 30-40% instantly on redundant queries).
   - Implement Cascade Routing (Route simple queries to Llama-3-8B hosted internally on cheap hardware, saving 80% on <abbr title="Application Programming Interface">API</abbr> costs).
3. **Long-Term Optimization (Fine-Tuning):** If the highest cost is a massive 5,000-token prompt for <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> extraction, we should collect 10,000 logs of GPT-4 doing this perfectly. We then Fine-Tune a tiny 3B parameter model on that dataset. The tiny model can now do the extraction perfectly with zero prompting, cutting costs by 99% and latency by 80%.
4. **Safety Mechanisms:** Hard rate limits per user, circuit breakers, and automated PagerDuty alerts if spend velocity exceeds $X per hour.

---
**Task for the end of the day:** Review the exact pricing per 1M tokens for OpenAI, Anthropic, and Google APIs. Understand the massive price gap between flagship models and tier-2 models.

Tomorrow, in **Day 161**, we move into the final stretch of the roadmap: **MLOps**. We will learn how to orchestrate massive data and training pipelines using Airflow, Dagster, and Prefect!
