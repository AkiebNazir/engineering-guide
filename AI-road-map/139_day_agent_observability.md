# Day 139: Agent Observability (Tracing & Debugging)

Welcome to Day 139. 

When traditional Python code fails, it throws a giant red Stack Trace on your screen pointing to the exact line of code.
When an Agent fails, it might just say, *"I am sorry, I cannot do that."* 
Or even worse, it might confidently output a completely hallucinated answer without throwing any errors at all. This is called a **Silent Failure**, and it is the nightmare of <abbr title="Artificial Intelligence">AI</abbr> Engineers.

Today, we learn **Observability**. We will use Tracing to look inside the Agent's brain.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Logging vs. Tracing
A **Log** is a flat string of text (e.g., `[INFO] Agent started`). It is useless for LLMs.
A **Trace** is a Directed Acyclic Graph (DAG). It tracks the hierarchical parent-child relationship of the execution.
If a LangGraph agent runs, the Trace shows:
```text
▼ Agent Execution (Total: 4.2s, $0.03)
  ▼ LLM Call 1: Planning (1.1s, $0.01)
  ▼ Tool Call: WebSearch (2.0s)
  ▼ LLM Call 2: Summarizing (1.1s, $0.02)
```

### 2. Key Agent Metrics
In production, you must build Grafana dashboards tracking these exact metrics:
- **Token Cost per Session:** (If an agent averages $\$0.05$ but suddenly spikes to $\$2.00$, it is stuck in a loop!)
- **Step Count:** (The Trajectory length. Optimal is 3 steps. If it takes 15 steps, your prompt is broken).
- **Tool Success Rate:** (If the `database_query` tool fails $40\%$ of the time, the <abbr title="Large Language Model">LLM</abbr> is probably hallucinating the SQL syntax).

### 3. Observability Platforms
You do not build tracing from scratch. You use platforms like **LangSmith** (built by LangChain) or **Arize Phoenix** (Open Source).
These platforms capture every <abbr title="Application Programming Interface">API</abbr> call, visualize the Trace Graph, and allow you to see the exact raw JSON prompt that was sent to OpenAI at step 4 of the loop.

### 4. Time-Travel Debugging
If a user reports a bug in production, you can download the failed Trace from LangSmith, load it into your local Jupyter Notebook, change the system prompt slightly, and **Replay** the exact same trace locally to see if your new prompt fixes the bug!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Custom Python Tracing class. We will wrap an Agent loop in "Spans" (a concept from OpenTelemetry) to track Start Time, End Time, Input, Output, and Cost.

Create a file named `agent_observability.py`:

```python
import time
import json

# --- 1. THE TRACER CLASS ---
class AgentTracer:
    def __init__(self):
        self.trace_tree = {"name": "Root Agent Execution", "spans": [], "total_cost": 0.0}
        
    def start_span(self, name, inputs):
        span = {
            "name": name,
            "inputs": inputs,
            "start_time": time.time(),
            "status": "RUNNING"
        }
        self.trace_tree["spans"].append(span)
        return span
        
    def end_span(self, span, outputs, cost=0.0):
        span["outputs"] = outputs
        span["end_time"] = time.time()
        span["duration_sec"] = round(span["end_time"] - span["start_time"], 2)
        span["cost"] = cost
        span["status"] = "SUCCESS"
        self.trace_tree["total_cost"] += cost
        
    def print_trace(self):
        print("\n=== EXECUTION TRACE ===")
        print(json.dumps(self.trace_tree, indent=2))
        print("=======================\n")

# --- 2. THE MOCK TOOLS AND LLM ---
def mock_llm(prompt):
    time.sleep(0.5) # Simulate API latency
    if "data" in prompt:
        return "Action: query_db", 0.01  # Returns output and cost
    return "Final Answer: The system is healthy.", 0.02

def mock_tool_query_db():
    time.sleep(1.2) # Simulate slow DB
    return "Database returned 5 rows."

# --- 3. THE TRACED AGENT LOOP ---
def run_traced_agent(user_input):
    print("--- RUNNING OBSERVABILITY AGENT ---\n")
    
    tracer = AgentTracer()
    print(f"User: {user_input}")
    
    # Span 1: The First LLM Call
    span1 = tracer.start_span("LLM_Thinking_Phase_1", {"prompt": user_input})
    llm_out_1, cost_1 = mock_llm(user_input)
    tracer.end_span(span1, {"response": llm_out_1}, cost=cost_1)
    
    # Span 2: Tool Execution
    if "Action: query_db" in llm_out_1:
        span2 = tracer.start_span("Tool_Execution: query_db", {})
        tool_out = mock_tool_query_db()
        tracer.end_span(span2, {"result": tool_out})
        
        # Span 3: The Final LLM Call
        span3 = tracer.start_span("LLM_Generation_Phase_2", {"prompt": tool_out})
        llm_out_2, cost_2 = mock_llm(tool_out)
        tracer.end_span(span3, {"response": llm_out_2}, cost=cost_2)
        
    # Output the JSON Trace!
    tracer.print_trace()

if __name__ == "__main__":
    run_traced_agent("Please get the data and summarize the system health.")
```

### Key Takeaways from Code:
1. **The Nested Data Structure:** By appending dictionaries to the `trace_tree`, we created a hierarchical view of the execution. If this script crashes, we can print the JSON and immediately see exactly which Span failed and how long it took.
2. **Cost Tracking at the Node Level:** We tracked the cost of *each specific <abbr title="Large Language Model">LLM</abbr> call*. This is crucial. If the total cost is $\$2.00$, the Trace tells us if `LLM_Thinking_Phase_1` cost $\$1.90` (a bloated system prompt) or if it was `LLM_Generation_Phase_2`.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Alerting System
You cannot manually read 50,000 JSON traces a day.
**Your Task:**
1. Conceptually design an Alerting function that runs at the end of every trace.
2. The function parses the `trace_tree`.
3. If `trace_tree["total_cost"] > 1.00`, trigger a PagerDuty alert: *"High Cost Runaway Agent"*.
4. Loop through the spans. If the count of spans where `name` contains `Tool_Execution` is $> 10$, trigger an alert: *"Agent stuck in infinite loop"*.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your agent system processes 50,000 customer support requests per day. 2% of the time, it fails silently (produces wrong answers without throwing any Python errors). Design the observability stack to detect and diagnose these silent failures."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **User Feedback Signals:** 
   - State that silent failures cannot be caught by Python `try/except` blocks. You MUST implement implicit and explicit user feedback. 
   - Explicit: A Thumbs Down button on the UI.
   - Implicit: The user immediately types *"No, that's not what I asked"* in the next turn.
2. **LLM-as-a-Judge (Automated Auditing):**
   - Propose running a secondary, highly-optimized Evaluator LLM (or a tiny local model) asynchronously over the 50,000 logs. It scores the Semantic Similarity between the User's intent and the Agent's final answer. If the score is low, it flags the Trace for human review.
3. **Trace Aggregation:**
   - Mention exporting all Traces to an OLAP database (like ClickHouse or Snowflake) to run SQL queries identifying patterns (e.g., *"Do all silent failures happen when the Agent uses the `billing_api` tool?"*).

---
**Task for the end of the day:** Commit your code to Git. 

We can now track exactly how much our Agents cost. And looking at the dashboards... they are way too expensive. 

Tomorrow, in **Day 140**, we learn **Agent Cost Optimization**. We will implement Semantic Caching and Model Routing to reduce our cloud bill by $80\%$!
