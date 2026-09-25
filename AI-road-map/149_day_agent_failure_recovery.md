# Day 149: Agent Failure Recovery & Graceful Degradation

Welcome to Day 149.

If you build a traditional web app and the database is down, the app crashes. You show the user a 500 error.
But if you build an <abbr title="Artificial Intelligence">AI</abbr> Agent, failure modes are much more complex. What if the <abbr title="Large Language Model">LLM</abbr> <abbr title="Application Programming Interface">API</abbr> times out? What if a Web Scraper tool hits a CAPTCHA? What if the agent gets stuck in an infinite `while` loop, bleeding your wallet dry?

Today, we learn **Resilience Engineering for Agents**. We will build systems that catch catastrophic failures, attempt intelligent recovery, and gracefully degrade their features so the user never experiences a hard crash.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The 5 Modes of Agent Failure
1. **<abbr title="Application Programming Interface">API</abbr> Timeouts:** OpenAI/Anthropic APIs go down frequently.
2. **Context Length Overflow:** A <abbr title="Retrieval-Augmented Generation">RAG</abbr> agent pulls too many documents and exceeds the 128k token limit, crashing the generation.
3. **Tool Execution Crashes:** The agent tries to execute `PythonREPL("1/0")` and throws a `ZeroDivisionError`.
4. **Infinite Loops:** The agent tries to fix a bug, the test fails, it tries again, fails again... repeating forever.
5. **Budget Exhaustion:** The agent spends $10 on a single task without solving it.

### 2. The Circuit Breaker Pattern
*Analogy:* If an electrical wire gets too hot, a physical switch "breaks" the circuit to prevent a fire.
In software, if your agent's `WeatherTool` relies on an external <abbr title="Application Programming Interface">API</abbr> that goes down, the agent might retry calling it 50 times, wasting <abbr title="Large Language Model">LLM</abbr> tokens and time. 
A **Circuit Breaker** tracks failures. If the `WeatherTool` fails 3 times in a row, the breaker "trips" (opens). For the next 5 minutes, any attempt to call the `WeatherTool` instantly returns `"Service Unavailable"`, saving the <abbr title="Large Language Model">LLM</abbr> from wasting tokens on broken tools.

### 3. Graceful Degradation
If a primary system fails, the app shouldn't crash; it should fall back to a "lesser" but functional state.
- **Model Degradation:** If `gpt-4o` (Primary) fails $\rightarrow$ Fallback to `claude-3-haiku` (Backup) $\rightarrow$ Fallback to local `Llama-3-8B` (Failsafe).
- **Architecture Degradation:** If the massive Plan-and-Execute agent graph crashes $\rightarrow$ Fallback to a simple ReAct agent $\rightarrow$ Fallback to a single zero-shot <abbr title="Large Language Model">LLM</abbr> prompt.
- **Tool Degradation:** If the Web Search tool fails $\rightarrow$ Fallback to using parametric memory (the <abbr title="Large Language Model">LLM</abbr>'s internal weights).

### 4. The Dead Letter Queue (DLQ)
If an agent task completely fails (e.g., all retries exhausted), you don't just drop the task. You push it to a **Dead Letter Queue**. This is a special database table where failed tasks sit. A human engineer can review the DLQ, fix the bug in the agent's code, and click "Replay" to push the task back into the main queue!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a resilient LangChain/LangGraph workflow that implements Exponential Backoff, <abbr title="Application Programming Interface">API</abbr> Fallbacks, and Tool Circuit Breaking.

*(Note: To run this code, you would need `pip install langchain langchain-openai langchain-anthropic tenacity`)*

```python
import time
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

# --- 1. MODEL FALLBACKS & DEGRADATION ---

print("[SYSTEM] Initializing Resilient Models...")
primary_llm = ChatOpenAI(model="gpt-4o")
backup_llm = ChatAnthropic(model="claude-3-haiku-20240307")

# LangChain LCEL makes graceful model degradation trivial:
resilient_llm = primary_llm.with_fallbacks([backup_llm])

# --- 2. THE CIRCUIT BREAKER (CUSTOM IMPLEMENTATION) ---

class CircuitBreaker:
    def __init__(self, failure_threshold=3, reset_timeout=10):
        self.failures = 0
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self.last_failure_time = 0
        self.is_open = False

    def check(self):
        # If open, check if enough time has passed to "half-open" and try again
        if self.is_open:
            if time.time() - self.last_failure_time > self.reset_timeout:
                print("   [CIRCUIT BREAKER] Timeout finished. Testing the tool again...")
                self.is_open = False
                self.failures = 0
                return True
            else:
                return False
        return True

    def record_failure(self):
        self.failures += 1
        self.last_failure_time = time.time()
        print(f"   [CIRCUIT BREAKER] Failure recorded ({self.failures}/{self.failure_threshold})")
        if self.failures >= self.failure_threshold:
            print("   [CIRCUIT BREAKER] THRESHOLD REACHED! Circuit tripped (Opened).")
            self.is_open = True

# --- 3. THE UNRELIABLE TOOL ---

db_circuit = CircuitBreaker(failure_threshold=2, reset_timeout=5)

@tool
def flaky_database_query(query: str) -> str:
    """Queries the internal database. Might crash."""
    
    # 1. Check the Circuit Breaker
    if not db_circuit.check():
        return "ERROR: Database tool is currently unavailable. Please rely on your internal knowledge or inform the user."
    
    # 2. Simulate the execution
    print(f"[TOOL] Executing query: {query}")
    time.sleep(1)
    
    # Simulate a random API crash
    # In a real scenario, this would be a network timeout or 500 error
    crash_happened = True # Forcing crash for demonstration
    
    if crash_happened:
        db_circuit.record_failure()
        raise ConnectionError("Database Connection Lost!")
        
    return "Query successful: The data is X."

# --- 4. EXPONENTIAL BACKOFF (TENACITY) ---

# We wrap the tool execution in a Tenacity decorator.
# If it throws a ConnectionError, it will wait 1s, then 2s, then 4s, up to 3 times.
@retry(
    stop=stop_after_attempt(3), 
    wait=wait_exponential(multiplier=1, min=1, max=4),
    retry=retry_if_exception_type(ConnectionError)
)
def safe_tool_execution(query):
    return flaky_database_query.invoke({"query": query})

# --- 5. EXECUTION DEMO ---

def run_resilience_demo():
    print("\n--- STARTING AGENT TASK ---")
    
    # Attempt 1: Will fail, Tenacity will retry.
    # Attempt 2: Will fail, Tenacity will retry. 
    # Attempt 3: Circuit Breaker hits threshold!
    
    try:
        print("\n[AGENT] Attempting to use the database tool...")
        safe_tool_execution("Select * from users")
    except Exception as e:
        print(f"\n[AGENT RECOVERY] Tool permanently failed after retries. Error: {e}")
        
    print("\n[AGENT] 5 seconds later, trying another task...")
    
    # Because the circuit breaker is Open, this instantly returns the safe fallback string 
    # without wasting time trying to execute the broken code!
    res = flaky_database_query.invoke({"query": "Select * from orders"})
    print(f"Tool returned: {res}")

# To run:
# run_resilience_demo()
```

### 🔍 Understanding the Safety Net
In this architecture:
1. **Model Fallback:** If OpenAI crashes, Anthropic takes over.
2. **Tenacity Retries:** If a network glitch happens, the code waits exponentially (1s, 2s, 4s) before trying again, preventing server spam.
3. **Circuit Breaker:** If the database is truly offline, we stop retrying. The tool returns a graceful string to the <abbr title="Large Language Model">LLM</abbr>: `"ERROR: Tool unavailable"`. The <abbr title="Large Language Model">LLM</abbr> reads this and can gracefully tell the user: *"I'm sorry, I cannot access the database right now."*

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Build a LangGraph infinite loop detector. 
Add a `loop_count` to your `AgentState`. In your router function, if `loop_count > 10`, force the graph to route to a custom `GracefulDegradationNode` that apologizes to the user and ends the graph, preventing infinite <abbr title="Large Language Model">LLM</abbr> token consumption.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Your production agent system had a 2-hour outage because the OpenAI <abbr title="Application Programming Interface">API</abbr> rate limit was hit. Design the resilience architecture to prevent this from ever taking the system offline again."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Multi-Provider Failover:** LCEL `.with_fallbacks()` routing from GPT-4 to Claude 3 to Gemini.
2. **Local Fallback:** If all external providers go down, route to an on-premise `vLLM` server hosting Llama-3-70B.
3. **Queue Backpressure:** Do not accept <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> requests if the Redis queue exceeds 10,000 tasks. Return `503 Service Unavailable` immediately.
4. **Token Rate Limiting (Token Bucket):** Throttle the agent workers locally so they never actually hit the OpenAI rate limit. 
5. **Graceful Degradation of Features:** If the <abbr title="Large Language Model">LLM</abbr> is down, disable the "Chat" feature in the frontend, but keep the core application functional.

---
**Task for the end of the day:** Review the `tenacity` Python library. It is essential for all network-bound <abbr title="Machine Learning">ML</abbr> code.

Tomorrow, in **Day 150**, we reach the **Phase 5 Capstone**. We will combine everything—Orchestration, Subgraphs, Scalable Queues, and Failure Recovery—into the ultimate Production Multi-Agent System!
