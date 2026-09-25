# Day 129: CrewAI Advanced (Custom Tools & Memory)

Welcome to Day 129. Yesterday, we built a Crew. But our agents were isolated; they couldn't search the web or query a database.

Today we supercharge our Agents. We will give them **Custom Tools**, connect them to **<abbr title="Model Context Protocol">MCP</abbr> Servers**, and grant the entire Crew **Long-Term Memory** so they learn from past executions!

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Custom Tool Creation & Pydantic
You can give CrewAI agents any Python function. But if the function takes multiple arguments (like `date` and `user_id`), the <abbr title="Large Language Model">LLM</abbr> will often hallucinate the format.
To fix this, we use the `@tool` decorator combined with **Pydantic Models**. 
By strictly defining the Input Schema with Pydantic, the <abbr title="Large Language Model">LLM</abbr> is mathematically constrained (via Structured Decoding from Day 112) to only output valid arguments!

### 2. CrewAI + <abbr title="Model Context Protocol">MCP</abbr> Integration
Writing custom <abbr title="Application Programming Interface">API</abbr> integrations for Jira, Slack, and Postgres is tedious. 
Because CrewAI supports the **Model Context Protocol (<abbr title="Model Context Protocol">MCP</abbr>)**, you can simply point your Crew to an <abbr title="Model Context Protocol">MCP</abbr> Server URL. CrewAI dynamically downloads all the Server's tools and instantly equips your Agents with them. Zero integration code required!

### 3. Agent Memory Systems
Standard LLMs suffer from "amnesia"—they forget everything the moment the script stops. CrewAI introduces three types of persistent memory:
1. **Short-Term Memory:** Remembers the context *during* a single Crew execution, preventing the agent from repeating the same tool call twice.
2. **Long-Term Memory:** CrewAI automatically embeds the final results of tasks and saves them to a local Vector Database (e.g., ChromaDB). If you run the script again tomorrow, the Agent queries the DB and remembers what it learned yesterday!
3. **Entity Memory:** The Agent automatically extracts specific facts about entities (e.g., *"The CEO of Apple is Tim Cook"*) and stores them in a Knowledge Graph for instant recall.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a CrewAI Agent equipped with a strictly-typed Custom Tool and conceptual Long-Term Memory!
*(Note: Mentally run `pip install crewai pydantic`).*

Create a file named `crewai_advanced.py`:

```python
import json
from pydantic import BaseModel, Field

# 1. Define the Strict Pydantic Schema for the Tool
class CustomerLookupInput(BaseModel):
    """Input schema for the customer database tool."""
    customer_id: str = Field(..., description="The exact 6-digit customer ID.")
    include_purchase_history: bool = Field(..., description="True if we need their past orders.")

# 2. Mocking the @tool Decorator logic
def mock_tool(name, schema):
    def decorator(func):
        func.tool_name = name
        func.schema = schema
        return func
    return decorator

# 3. Create the Custom Tool!
@mock_tool(name="LookupCustomer", schema=CustomerLookupInput)
def lookup_customer(args_json):
    """Queries the internal database for a customer."""
    print(f"\n[TOOL EXECUTING] Validating LLM Input against Pydantic Schema...")
    
    try:
        # Pydantic validation (simulated)
        args = json.loads(args_json)
        if "customer_id" not in args or "include_purchase_history" not in args:
            raise ValueError("Missing required fields!")
            
        print(f" -> Input Valid! Fetching Customer {args['customer_id']}...")
        return "Customer: Alice. Risk Level: Low. Total Spent: $500."
        
    except Exception as e:
        return f"Tool Error: {str(e)}. Please format your input correctly."

# --- SIMULATING THE CREW EXECUTION ---

def run_advanced_crew():
    print("--- RUNNING ADVANCED CREWAI SYSTEM ---\n")
    
    print("[SYSTEM] Initializing Long-Term Memory (Vector DB)...")
    print("[SYSTEM] Agent has access to memory from previous runs.\n")
    
    print("--- AGENT: Data Verification Specialist ---")
    print("Goal: Look up Customer 884910 and verify their status.")
    
    # Simulate LLM generating a perfect Tool Call because of Pydantic!
    perfect_llm_json = '{"customer_id": "884910", "include_purchase_history": true}'
    
    print(f"\n[AGENT THOUGHT] I need to use the LookupCustomer tool.")
    print(f"[AGENT ACTION] Calling tool with args: {perfect_llm_json}")
    
    # Execute Tool
    tool_result = lookup_customer(perfect_llm_json)
    
    print(f"\n[AGENT OBSERVATION] {tool_result}")
    print(f"[AGENT THOUGHT] I have the data. Generating final report.")
    
    # Save to Long-Term Memory
    print(f"\n[SYSTEM] Saving final report to Long-Term Memory for future executions...")
    print("Done!")

if __name__ == "__main__":
    run_advanced_crew()
```

### Key Takeaways from Code:
1. **Pydantic is Mandatory:** If you do not use Pydantic, the <abbr title="Large Language Model">LLM</abbr> might output `{"id": 884910}` instead of `{"customer_id": "884910"}`. The python function would crash. Pydantic ensures the <abbr title="Large Language Model">LLM</abbr>'s output perfectly matches your backend requirements.
2. **Memory Persistence:** Because Long-Term memory is enabled, if we run this exact same script tomorrow with the same customer ID, the Agent might skip the tool call entirely and just answer from Memory! This saves massive amounts of <abbr title="Application Programming Interface">API</abbr> tokens.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: CrewAI Flows
Sometimes, one Crew is not enough. You need multiple Crews talking to each other.
**Your Task:**
1. Research "CrewAI Flows" (a feature for multi-crew orchestration).
2. Conceptually map out a Customer Onboarding Flow:
   - **Crew 1 (Research):** Verify the company information on the web.
   - **Crew 2 (Compliance):** Takes output of Crew 1, checks it against financial regulations.
   - **Crew 3 (Setup):** Takes output of Crew 2, uses an <abbr title="Model Context Protocol">MCP</abbr> server to create their account in Postgres.
3. How does State flow between these three entirely separate organizations?

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"A Crew of 5 agents costs $5.00 per execution and takes 3 minutes. You need to process 10,000 customer onboarding tasks per day. Design the scaling strategy and optimize for cost and throughput."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Throughput Problem (Concurrency):** 
   - State that $10,000 \times 3$ minutes $= 30,000$ minutes (500 hours) of compute. This cannot be run linearly.
   - Propose an async worker pool architecture using Celery or AWS SQS. You must deploy the Crew on a Kubernetes cluster and run 50 Crews concurrently to hit the daily <abbr title="Service Level Agreement - A commitment between a service provider and a client outlining expected performance metrics such as availability.">SLA</abbr>.
2. **The Cost Problem ($50k/day):**
   - Propose **Model Routing**. Not all 5 agents need GPT-4o. The basic "Data Entry" agent should be swapped to a highly quantized open-source model (like Llama-3 8B) running locally, reducing the <abbr title="Application Programming Interface">API</abbr> cost of that agent to near $\$0$.
3. **Semantic Caching:**
   - Propose deploying Redis with Vector Search. If Customer B is identical to Customer A, the system should catch the semantic similarity at the Gateway level and instantly return yesterday's Crew result, skipping the 3-minute execution entirely!

---
**Task for the end of the day:** Commit your code to Git. 

We can build complex, memory-enabled Crews. But how do we know they actually work? 
Standard Unit Testing fails on <abbr title="Artificial Intelligence">AI</abbr> because LLMs are non-deterministic. If you run a Crew 10 times, you get 10 different outputs. 

Tomorrow, in **Day 130**, we learn the dark art of **Agent Evaluation & Testing**!
