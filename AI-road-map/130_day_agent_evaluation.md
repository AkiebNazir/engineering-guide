# Day 130: Agent Evaluation & Testing

Welcome to Day 130. 

You built a powerful Agent. You ran it locally on your laptop, and it successfully wrote a python script and emailed it to you. You deployed it to production.
Ten minutes later, the Agent went into an infinite loop, hallucinated a fake SQL query, and burned through $50 of API credits before crashing.

Why did this happen? Because **Agents are non-deterministic**. Traditional software engineering uses Unit Tests (e.g., `assert 2+2 == 4`). But you cannot write a Unit Test for an LLM because it might say "4" today, and "four" tomorrow.

Today, we learn the dark art of **Agent Evaluation and Testing**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Evaluation Dimensions
You cannot just grade the Agent's final answer. A good answer might have cost $10 to generate! You must evaluate:
- **Task Completion Rate:** Did it actually achieve the final goal?
- **Tool Call Accuracy:** Did it use the right tool with the right JSON syntax?
- **Cost Efficiency:** Did it burn unnecessary tokens?
- **Latency:** Did the loops take 5 seconds or 5 minutes?

### 2. Trajectory Analysis
This is the most critical agent metric. You must grade the *path* the agent took. 
If the agent needed to find the weather in Tokyo, the optimal trajectory is `[Thought -> Tool(Weather) -> Final Answer]`. That is 3 steps.
If the agent did `[Thought -> Tool(WebSearch) -> Thought -> Tool(Calculator) -> Thought -> Tool(Weather) -> Final Answer]`, it took 7 steps! The trajectory is wildly inefficient and points to a flawed system prompt.

### 3. The Agent Testing Pyramid
- **Unit Tests:** You test your pure Python Tool functions completely isolated from the LLM.
- **Integration Tests (Mocking):** You replace the real OpenAI API with a `MockLLM` that returns deterministic, hardcoded strings. You verify that your LangGraph orchestrator correctly parses the mocked string and routes to the correct node.
- **E2E Evaluations (LLM-as-a-Judge):** You run the real Agent against a dataset of 50 tasks. You use GPT-4o as a "Judge" to read the 50 outputs and score them from 1-10 based on a strict rubric.

### 4. Benchmarks
How do researchers prove their Agent is better than yours? They use public benchmarks:
- **SWE-Bench:** Gives the agent a real GitHub issue and the entire codebase. The agent must write the fix.
- **WebArena:** Drops the agent into a sandboxed e-commerce website and tells it to "Buy a red shirt size M."

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build an **Integration Test** for an Agent. We will use a Mock LLM so our CI/CD pipeline runs instantly without spending money on API calls. We will also implement a basic **Trajectory Evaluator**!

Create a file named `agent_evaluation.py`:

```python
import json

# --- 1. THE SYSTEM BEING TESTED (The Agent Loop) ---
def run_agent_loop(llm_function, max_steps=5):
    """A naive agent loop."""
    history = []
    trajectory_steps = 0
    
    for i in range(max_steps):
        trajectory_steps += 1
        llm_output = llm_function(history)
        history.append(llm_output)
        
        if "Final Answer:" in llm_output:
            return {"status": "SUCCESS", "trajectory": trajectory_steps, "history": history}
            
        if "Action:" in llm_output:
            # Mock tool execution
            history.append("Observation: Tool executed.")
            
    return {"status": "FAILED_TIMEOUT", "trajectory": trajectory_steps, "history": history}

# --- 2. THE TEST SUITE ---

def mock_perfect_llm(history):
    """Simulates an LLM taking the optimal path."""
    if len(history) == 0:
        return "Thought: I need data.\nAction: get_data"
    elif "Observation:" in history[-1]:
        return "Thought: I have data.\nFinal Answer: 42"

def mock_hallucinating_llm(history):
    """Simulates an LLM getting trapped in a loop!"""
    return "Thought: I am confused.\nAction: random_tool"

def test_optimal_trajectory():
    print("[TEST 1] Running Optimal Agent Test...")
    result = run_agent_loop(mock_perfect_llm)
    
    assert result["status"] == "SUCCESS", "Agent failed to complete task!"
    assert result["trajectory"] <= 3, f"Agent took too many steps: {result['trajectory']}"
    print(" -> PASSED! Agent completed task efficiently.")

def test_timeout_failure():
    print("\n[TEST 2] Running Timeout Protection Test...")
    result = run_agent_loop(mock_hallucinating_llm, max_steps=3)
    
    assert result["status"] == "FAILED_TIMEOUT", "Agent did not timeout correctly!"
    assert result["trajectory"] == 3, "Agent did not hit max steps!"
    print(" -> PASSED! Graph architecture correctly terminated the runaway agent.")

def run_test_suite():
    print("--- RUNNING AGENT CI/CD PIPELINE ---\n")
    try:
        test_optimal_trajectory()
        test_timeout_failure()
        print("\n[CI/CD SUCCESS] All tests passed! Ready to deploy.")
    except AssertionError as e:
        print(f"\n[CI/CD FAILED] {e}")

if __name__ == "__main__":
    run_test_suite()
```

### Key Takeaways from Code:
1. **Deterministic Testing:** We tested the *architecture* (the loop, the timeout logic, the trajectory counting) without making a single real API call. This is how you run tests in GitHub Actions.
2. **Trajectory Enforcement:** We explicitly asserted that the agent must solve the task in `<= 3` steps. If a developer accidentally updates the system prompt and the agent suddenly starts taking 5 steps, the CI/CD pipeline will fail and block the deployment, catching the inefficiency before it burns money in production!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Regression Test Fixtures
When you change an LLM's system prompt to fix a new bug, you often accidentally break an old capability.
**Your Task:**
1. Conceptually design a Regression Test framework.
2. You maintain a `datasets/gold_standard.jsonl` file containing 50 historical inputs and their expected perfect outputs.
3. Every time you push code to `main`, a script fires up the *real* LLM, runs all 50 inputs, and uses another LLM (GPT-4o) to grade the semantic similarity between the new outputs and the gold standard outputs.
4. If the overall score drops below 95%, the PR is blocked!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your enterprise agent system works 95% of the time in staging but fails unpredictably in production. Design a reliability engineering strategy covering testing, monitoring, fallbacks, and continuous improvement."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Testing (The Foundation):** 
   - Propose a 3-tier approach: Pytest for deterministic Python logic, Mock LLMs for routing logic, and LLM-as-a-Judge for prompt evaluation.
2. **Monitoring & Tracing (Observability):**
   - State that raw logs are useless for agents. You must deploy an tracing platform (like LangSmith or Phoenix) to capture the exact tree-structure of the Agent's reasoning. You need dashboards tracking Token Cost per Session and Step Count.
3. **Continuous Improvement (Data Flywheel):**
   - Propose an automated feedback loop. If an Agent crashes in production, the exact trajectory that caused the crash is automatically added to the `gold_standard.jsonl` evaluation dataset, ensuring the agent is tested against that exact failure mode in all future deployments.

---
**Task for the end of the day:** Commit your code to Git. 

We have mastered orchestrating and testing standard ReAct agents. 
But ReAct has a major flaw: The agent thinks one step at a time. It cannot plan for the future. If a task requires 20 steps, a ReAct agent will get lost by step 8.

Tomorrow, in **Day 131**, we enter **Advanced Agent Patterns**. We will learn how to build **Plan-and-Execute Agents** and use the **LLMCompiler** for parallel tool execution!
