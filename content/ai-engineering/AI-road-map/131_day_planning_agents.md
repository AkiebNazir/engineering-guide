# Day 131: Planning Agents (Plan-and-Execute & LLMCompiler)

Welcome to Day 131. 

Up until now, we have relied on the **ReAct** framework (Reason + Act). The ReAct agent thinks one step at a time. It executes Step 1, looks at the result, and *then* decides what Step 2 should be.
This works for simple tasks. But if the task requires 20 complex steps, a ReAct agent will get lost, forget the original user request, and wander off into an infinite loop.

Today, we learn advanced planning architectures: **Plan-and-Execute**, and parallel tool execution via **LLMCompiler**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Plan-and-Execute Pattern
Instead of interleaving thinking and acting, we completely separate them into two different Agents!
1. **The Planner:** Reads the user's prompt and generates a strict, step-by-step JSON array of instructions (The Plan).
2. **The Executor:** Takes The Plan, blindly executes Step 1, records the result, executes Step 2, and so on.
Because the Planner generates the entire 20-step map upfront, the agent never gets lost!

### 2. Re-Planning
What if the Planner says *Step 3: Download the file*, but the file server is offline? The Executor will crash.
To fix this, we use **Re-Planning**. If the Executor encounters an error on Step 3, it stops, bundles the error log, and sends it *back* to the Planner. The Planner reads the error, dynamically deletes Steps 3-20, and writes a brand new set of steps to recover from the failure!

### 3. Task DAG Generation & LLMCompiler
A linear step-by-step plan is slow. 
What if the user asks: *"What is the stock price of Apple, Microsoft, and Google?"*
A linear agent searches Apple, waits 2 seconds. Searches Microsoft, waits 2 seconds. Searches Google, waits 2 seconds.
**LLMCompiler** is a revolutionary framework where the Planner generates a **Directed Acyclic Graph (DAG)** of tasks. It realizes that searching Apple, Microsoft, and Google are *independent* tasks, and the Executor runs all three API calls **in parallel** concurrently! This cuts latency by 66%!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual Plan-and-Execute agent. We will see how separating the Planner from the Executor allows for extreme clarity in long-term tasks.

Create a file named `plan_and_execute.py`:

```python
import json

# --- 1. THE TOOLS ---
def execute_tool(tool_name, tool_args):
    """Simulates executing a tool."""
    print(f"      [EXECUTOR] Running '{tool_name}' with args {tool_args}...")
    if tool_name == "web_search":
        return f"Found data for {tool_args['query']}."
    if tool_name == "calculator":
        return "Calculation complete: 42."
    return "Error: Tool not found."

# --- 2. THE PLANNER ---
def mock_planner_agent(user_request):
    """
    The Planner NEVER executes tools. It only generates a JSON array of steps.
    """
    print("\n[PLANNER] Analyzing the user request and drafting a master plan...")
    
    # Simulating the LLM generating a JSON array of sequential steps
    plan = [
        {"step_id": 1, "tool": "web_search", "args": {"query": "GDP of Japan 2026"}},
        {"step_id": 2, "tool": "web_search", "args": {"query": "GDP of Germany 2026"}},
        {"step_id": 3, "tool": "calculator", "args": {"query": "Japan GDP - Germany GDP"}},
        {"step_id": 4, "tool": "generate_report", "args": {"query": "Write the final comparison."}}
    ]
    return plan

# --- 3. THE RE-PLANNER ---
def mock_replanner_agent(failed_step, error_msg, remaining_plan):
    """
    If a step fails, the Re-Planner dynamically rewrites the rest of the plan!
    """
    print(f"\n[RE-PLANNER] Step {failed_step} failed with error: '{error_msg}'")
    print("[RE-PLANNER] Drafting a recovery plan...")
    
    # The Re-Planner decides to skip the calculator and just estimate
    new_plan = [
        {"step_id": 3, "tool": "generate_report", "args": {"query": "Write comparison stating data was unavailable."}}
    ]
    return new_plan

# --- 4. THE EXECUTION ENGINE ---
def run_plan_and_execute_simulation():
    print("--- RUNNING PLAN-AND-EXECUTE ARCHITECTURE ---\n")
    
    user_request = "Calculate the difference between the GDP of Japan and Germany in 2026."
    print(f"User: {user_request}")
    
    # 1. Generate the initial plan
    current_plan = mock_planner_agent(user_request)
    
    # 2. The Execution Loop
    results_memory = []
    
    while len(current_plan) > 0:
        # Pop the first task off the queue
        current_task = current_plan.pop(0)
        print(f"\n[SYSTEM] Starting Step {current_task['step_id']}: {current_task['tool']}")
        
        # Execute the tool
        if current_task["tool"] == "calculator":
            # Simulate a fatal tool crash!
            result = "FATAL EXCEPTION: Calculator API Offline."
            
            # 3. Trigger the Re-Planner!
            current_plan = mock_replanner_agent(current_task["step_id"], result, current_plan)
            continue
            
        else:
            result = execute_tool(current_task["tool"], current_task["args"])
            
        results_memory.append(f"Step {current_task['step_id']} Result: {result}")
        print(f"      [RESULT] {result}")
        
    print("\n--- FINAL EXECUTION COMPLETE ---")
    print("The Executor successfully navigated the failure without crashing!")

if __name__ == "__main__":
    run_plan_and_execute_simulation()
```

### Key Takeaways from Code:
1. **Separation of Concerns:** The Planner is a massive, expensive model (like GPT-4o) that is incredibly smart but slow. It runs exactly *once*. The Executor is a tiny, blazing-fast model (like Llama-3 8B) that just blindly formats inputs into tool calls. This saves massive amounts of money!
2. **Resilience:** Because the plan is maintained as a List (a queue), the Re-Planner can simply overwrite the List with new tasks if something goes wrong, acting as a dynamic GPS recalculating a route!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Parallel Execution DAG
Your task is to implement the **LLMCompiler** pattern.
**Your Task:**
1. Modify the JSON schema of the Planner. Instead of just returning a list of tasks, it must return a list of tasks where each task has a `depends_on` array.
   *(e.g., Task 3 depends_on [Task 1, Task 2]).*
2. Use Python's `asyncio` or `concurrent.futures.ThreadPoolExecutor` to loop through the plan.
3. If Task 1 and Task 2 both have `depends_on: []` (no dependencies), fire them off to the Executor concurrently! 
4. Task 3 must `await` the results of Task 1 and 2 before executing.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your agent needs to complete a complex 20-step database migration task. ReAct fails because it loses context. Plan-and-Execute fails because the database schema might change mid-migration, making the upfront 20-step plan completely stale. Design a hybrid approach."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Flaw of Upfront Planning:** 
   - State that Plan-and-Execute assumes a static environment. In a dynamic environment (like a live database), an upfront 20-step plan is dangerous.
2. **The Hybrid Solution (Chunked Planning):**
   - Propose an architecture where the Planner does not plan 20 steps. It generates a high-level "Epic" (e.g., *"Migrate User Table"*).
   - It then generates a micro-plan of exactly 3 steps. 
   - The Executor runs those 3 steps. Then, the Agent is forced into a **Reflection Node** to observe the new state of the database before asking the Planner to generate the next 3 steps.
3. **Rollback Mechanisms:**
   - Emphasize that in migration tasks, the Planner must generate a "Rollback Task" alongside every "Execution Task" so the system can gracefully revert changes if a step fails.

---
**Task for the end of the day:** Commit your code to Git. 

We can now plan 20 steps ahead. But what if the Agent executes a step, and the output is just... bad? 
Humans review their own work before submitting it. Agents should too.

Tomorrow, in **Day 132**, we learn **Reflexion and Self-Critique Agents**. We will teach the LLM to yell at itself until it gets the right answer!
