# Day 135: Code Agents (AI-Powered Software Development)

Welcome to Day 135. 

You have likely seen viral demos of AI software engineers like **Devin**, **Aider**, or the open-source **SWE-Agent**. These are not just standard LLMs (like ChatGPT) where you paste code and ask for a fix. 
These are **Agents** that literally live inside your computer. They can type terminal commands, read file structures, run tests, and push commits.

Today, we learn the architecture behind autonomous coding agents.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Agent-Computer Interface (ACI)
An LLM cannot naturally type on a keyboard. We must build an **Agent-Computer Interface (ACI)**.
The ACI translates the LLM's text output into bash commands, and translates the computer's bash output back into text the LLM can read.
A bad ACI just feeds raw `stdout` to the LLM. If the Agent runs `cat giant_log.txt`, the terminal spits out 500,000 tokens, overflowing the LLM's context window and crashing the agent! A good ACI intercepts this, paginates the output, and tells the LLM: *"File is too large. Showing first 100 lines."*

### 2. Repository Understanding (Context Building)
An enterprise codebase has 1 Million lines of code. The Agent cannot read it all. 
How does it find the bug?
1. **File Tree:** The Agent first runs `tree` to understand the folder architecture.
2. **Search:** The Agent uses `grep` to find specific function names.
3. **Symbol Extraction:** The Agent uses tools like `ctags` to only read the function signatures and docstrings, ignoring the actual implementation until it finds the file it needs.

### 3. The SWE-Agent Action Space
Instead of raw bash, SWE-Agent provides the LLM with highly optimized custom tools:
- `search_dir(pattern)`
- `open_file(path)`
- `goto_line(number)`
- `edit_lines(start, end, new_code)`
- `run_tests(test_file)`

### 4. SWE-Bench
This is the ultimate benchmark for Code Agents. Researchers took 2,000 real-world, highly complex GitHub Issues from popular Python libraries (like `django` and `scikit-learn`). The Agent is dropped into the repo and told to fix the issue. Currently, the best AI agents in the world can only solve about $40\%$ of them!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a mock Code Agent! We will simulate the Agent-Computer Interface (ACI) and watch the Agent debug a broken python script.

Create a file named `code_agent_aci.py`:

```python
# --- 1. THE MOCK FILE SYSTEM ---
mock_file_system = {
    "math_utils.py": "def add(a, b):\n    return a - b  # BUG: Should be addition\n"
}

# --- 2. THE AGENT-COMPUTER INTERFACE (ACI) TOOLS ---
def aci_read_file(filename):
    print(f"   [ACI] Agent requested to read '{filename}'...")
    if filename in mock_file_system:
        return mock_file_system[filename]
    return "Error: File not found."

def aci_edit_file(filename, old_str, new_str):
    print(f"   [ACI] Agent replacing '{old_str.strip()}' with '{new_str.strip()}'...")
    if filename in mock_file_system:
        mock_file_system[filename] = mock_file_system[filename].replace(old_str, new_str)
        return "Edit successful."
    return "Error: File not found."

def aci_run_tests():
    print(f"   [ACI] Agent running pytest...")
    code = mock_file_system["math_utils.py"]
    if "return a + b" in code:
        return "PASSED: test_add() returned expected results."
    else:
        return "FAILED: test_add() expected 5, got -1."

# --- 3. THE CODE AGENT LOOP ---
def mock_code_agent_llm(history):
    """Simulates the LLM's thought process during debugging."""
    if len(history) == 0:
        return "Thought: I need to read the broken file.\nAction: read_file(math_utils.py)"
    
    last_obs = history[-1]
    
    if "return a - b" in last_obs:
        return "Thought: I found the bug! It is subtracting instead of adding. I will fix it.\nAction: edit_file(math_utils.py, 'return a - b', 'return a + b')"
        
    if "Edit successful" in last_obs:
        return "Thought: The code is updated. I should verify it works.\nAction: run_tests()"
        
    if "PASSED" in last_obs:
        return "Thought: The tests passed. My job is done.\nFinal Answer: Bug fixed successfully!"

def run_swe_agent_simulation():
    print("--- RUNNING SWE-AGENT SIMULATION ---\n")
    
    print("[ISSUE] User: The add() function in math_utils.py is returning negative numbers!\n")
    
    history = []
    max_steps = 10
    
    for step in range(max_steps):
        # 1. LLM Thinks and Acts
        llm_response = mock_code_agent_llm(history)
        print(f"[AGENT] {llm_response}")
        history.append(llm_response)
        
        if "Final Answer" in llm_response:
            break
            
        # 2. ACI Parses the Action and Executes
        if "read_file" in llm_response:
            obs = aci_read_file("math_utils.py")
        elif "edit_file" in llm_response:
            obs = aci_edit_file("math_utils.py", "return a - b", "return a + b")
        elif "run_tests" in llm_response:
            obs = aci_run_tests()
            
        print(f"   [OBSERVATION] {obs}\n")
        history.append(f"Observation: {obs}")

if __name__ == "__main__":
    run_swe_agent_simulation()
```

### Key Takeaways from Code:
1. **The Feedback Loop:** The Agent didn't just write code blindly. It read the file, edited it, and *crucially*, it ran the tests to verify its own work. If the tests had failed, the Agent would have stayed in the loop, read the traceback, and tried again (Generator-Critic architecture).
2. **Diff Editing:** Notice the `aci_edit_file` tool. Asking an LLM to rewrite a 10,000-line file just to change a plus sign wastes thousands of tokens. Good ACIs use strict string replacement or diff-formats so the LLM only outputs the exact line it wants to change.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Terminal Pagination
Your Code Agent keeps crashing because `npm install` outputs 10,000 lines of logs, blowing up the Context Window.
**Your Task:**
1. Conceptually design a wrapper for a `run_command` tool.
2. If the command output is $> 500$ lines, your Python wrapper should intercept it.
3. It should return the first 100 lines, the last 100 lines (which usually contain the error), and a message: `[Output truncated. 9,800 lines hidden.]`

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design the architecture for an AI coding assistant that works on legacy enterprise repositories with over 1 Million lines of code. How does it build context, make changes safely, and validate its work without hallucinations?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Context Building (Vector Search + Graph):** 
   - 1M lines cannot fit in context. The system must index the codebase nightly using a Vector Database (RAG). 
   - Furthermore, the system must build an Abstract Syntax Tree (AST) to map dependencies (e.g., "If I change this `User` class, which other files import it?").
2. **Safe Changes (The Sandbox):**
   - The Agent MUST NOT run in the developer's raw environment. The Agent runs in an isolated Docker container with a clone of the repo. It makes changes there.
3. **Validation (CI/CD):**
   - The Agent creates a Pull Request. The enterprise CI/CD pipeline runs all unit and integration tests. If the tests fail, the CI pipeline automatically tags the Agent in the PR with the failure logs, triggering the Agent to fix its own PR!

---
**Task for the end of the day:** Commit your code to Git. 

Our Agents can now navigate the terminal and edit files. 
But many human tasks require interacting with graphical User Interfaces (GUIs). 

Tomorrow, in **Day 136**, we learn about **Browser Agents**. We will teach LLMs how to open Chrome, "see" the screen, and click buttons to automate the web!
