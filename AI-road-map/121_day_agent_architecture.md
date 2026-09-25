# Day 121: Agent Architecture (Perception-Reasoning-Action)

Welcome to Phase 5: **Agentic <abbr title="Artificial Intelligence">AI</abbr>**. 

For the last 120 days, we have built *Passive Chatbots*. A chatbot is a pipeline: The user types a question, the <abbr title="Large Language Model">LLM</abbr> generates an answer, and the script terminates.

Today, we build an **Autonomous Agent**. An agent is not a pipeline; it is a *State Machine*. An agent runs inside an infinite `while True` loop. It can independently perceive its environment, reason about its goals, use tools, verify its own work, and decide for itself when to stop!

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Cognitive Architecture (OODA Loop)
Agents are built on a variation of the military OODA Loop (Observe, Orient, Decide, Act). In <abbr title="Artificial Intelligence">AI</abbr>, we call this the **Perception-Reasoning-Action Loop**.
1. **Observe:** Read the environment (e.g., Read a webpage, or read an error message).
2. **Think:** Mathematically deduce the next logical step based on the observation.
3. **Act:** Execute a Python Tool (e.g., Run a SQL query).
4. **Reflect:** Look at the result of the SQL query. Did it work? If not, loop back to Step 2!

### 2. The ReAct Framework Formalization
In Day 115, we touched on ReAct. Today we formalize it. To trap an <abbr title="Large Language Model">LLM</abbr> in a cognitive loop, you must enforce a strict parsing grammar. 
If the <abbr title="Large Language Model">LLM</abbr> outputs `Thought: ...`, it is allowed to continue generating.
If the <abbr title="Large Language Model">LLM</abbr> outputs `Action: ...`, your Python script must forcefully STOP the <abbr title="Large Language Model">LLM</abbr> from generating any more text! Your script executes the Action, appends the `Observation: ...`, and then restarts the <abbr title="Large Language Model">LLM</abbr>.

### 3. Agent Design Patterns
When tasks become complex, one Agent is not enough. You must build an "Agency" using specific design patterns:
- **The Router:** A fast, cheap <abbr title="Large Language Model">LLM</abbr> that reads the user's prompt and routes it to the correct specialist.
- **The Planner:** An <abbr title="Large Language Model">LLM</abbr> that takes a massive goal (*"Build a website"*) and breaks it down into 10 smaller JSON tasks.
- **The Executor:** The "blue-collar" Agent that actually runs the tools.
- **The Critic:** The "manager" Agent that reviews the Executor's work before showing it to the user.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a production-grade ReAct agent loop from scratch in pure Python. We will add structured JSON output for the Action so our parser never crashes!

Create a file named `agent_architecture.py`:

```python
import json

# 1. The Tool
def execute_calculator(math_string):
    """A dangerous tool! Evaluates math."""
    try:
        # DO NOT DO THIS IN PROD! Use a safe math parser.
        return str(eval(math_string))
    except Exception as e:
        return f"Error: {str(e)}"

# 2. The System Prompt
SYSTEM_PROMPT = """You are an Autonomous Agent.
You run in a loop of Thought, Action, PAUSE, Observation.

Use Thought to describe your thoughts about the question you have been asked.
Use Action to run a tool. The Action MUST be a valid JSON object.
After you output the Action, you MUST output the word PAUSE and stop generating!

Available Tools:
- calculator: Evaluates a math string. Args: {"math_string": "..."}

Example Session:
Question: What is 5 * 5?
Thought: I need to calculate 5 times 5.
Action: {"tool": "calculator", "args": {"math_string": "5 * 5"}}
PAUSE
Observation: 25
Thought: I have the answer.
Final Answer: 25
"""

def mock_llm(history):
    """Simulates the LLM's stateful generation."""
    history_str = str(history)
    
    if "Observation" not in history_str:
        return 'Thought: The user wants to know (100 * 45) / 2.\nAction: {"tool": "calculator", "args": {"math_string": "(100 * 45) / 2"}}\nPAUSE'
    
    if "Observation: 2250.0" in history_str:
        return 'Thought: I have the result from the calculator.\nFinal Answer: The answer is 2250.0'

def run_autonomous_agent():
    print("--- RUNNING AUTONOMOUS AGENT LOOP ---\n")
    
    question = "What is (100 * 45) / 2?"
    messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": question}]
    
    print(f"User: {question}\n")
    
    max_loops = 5
    for loop_num in range(max_loops):
        print(f"--- LOOP {loop_num + 1} ---")
        
        # 1. GENERATE
        response = mock_llm(messages)
        print(f"LLM:\n{response}\n")
        messages.append({"role": "assistant", "content": response})
        
        # 2. CHECK FOR COMPLETION
        if "Final Answer:" in response:
            print("[AGENT FINISHED MISSION]")
            break
            
        # 3. CHECK FOR PAUSE & ACTION
        if "PAUSE" in response and "Action:" in response:
            # Extract the JSON action
            action_line = [line for line in response.split('\n') if line.startswith('Action:')][0]
            json_str = action_line.replace("Action:", "").strip()
            
            try:
                action_data = json.loads(json_str)
                tool_name = action_data.get("tool")
                
                # 4. EXECUTE TOOL
                print(f"[SYSTEM] Executing tool '{tool_name}'...")
                if tool_name == "calculator":
                    result = execute_calculator(action_data["args"]["math_string"])
                    
                # 5. INJECT OBSERVATION
                observation = f"Observation: {result}"
                print(f"[SYSTEM] Injecting: {observation}\n")
                messages.append({"role": "user", "content": observation})
                
            except json.JSONDecodeError:
                messages.append({"role": "user", "content": "Observation: Error! You output invalid JSON. Try again."})

if __name__ == "__main__":
    run_autonomous_agent()
```

### Key Takeaways from Code:
1. **The `PAUSE` Token:** This is the most important concept in raw agent building. If you do not explicitly instruct the <abbr title="Large Language Model">LLM</abbr> to `PAUSE`, it will hallucinate the `Observation` itself instead of waiting for your Python script to run the real tool!
2. **Self-Correction:** Notice the `except` block. If the <abbr title="Large Language Model">LLM</abbr> outputs broken JSON, we don't crash the program. We literally inject an `Observation` telling the <abbr title="Large Language Model">LLM</abbr> it made a syntax error, and the <abbr title="Large Language Model">LLM</abbr> will fix its own mistake on the next loop!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Error Recovery
If a tool throws a Python Exception, the agent must not crash.
**Your Task:**
1. Conceptually modify the `execute_calculator` tool to throw a `ZeroDivisionError` if the <abbr title="Large Language Model">LLM</abbr> tries to divide by zero.
2. Ensure the exception traceback is captured and returned as a string.
3. Because the traceback is injected as the `Observation`, the <abbr title="Large Language Model">LLM</abbr> will read the traceback, realize it divided by zero, and output a new Thought: *"I cannot divide by zero. I must inform the user."*

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are designing an autonomous agent system for Enterprise Customer Support. The agents have access to databases to process refunds. Discuss the cognitive architecture, error recovery, and how you prevent the agent from looping infinitely and bankrupting our <abbr title="Application Programming Interface">API</abbr> budget."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Architecture (Supervisor Pattern):** 
   - Propose a Multi-Agent system. A cheap `Router` agent classifies the user's intent. If it's a refund, it routes to a `Refund Agent` equipped with SQL tools. 
2. **Human-in-the-Loop (Safety):**
   - State that autonomous agents must NEVER process financial transactions completely autonomously. The agent can draft the SQL and verify the user's eligibility, but the final execution requires a Human-in-the-Loop approval gate!
3. **Infinite Loop Prevention:**
   - Mention setting a hard `max_iterations=5` cap on the `while` loop. 
   - Propose using a fast, cheap model (GPT-4o-mini) for the intermediate Tool loops, and only using the expensive model (GPT-4o) for the final answer synthesis to optimize token costs.

---
**Task for the end of the day:** Commit your code to Git. 

Writing raw `while` loops and Regex parsers for Agents is tedious and brittle. Just as `React.js` revolutionized Javascript, a new framework revolutionized Agent development.

Tomorrow, in **Day 122**, we learn **LangChain** and the magical syntax of **LCEL (LangChain Expression Language)**!
