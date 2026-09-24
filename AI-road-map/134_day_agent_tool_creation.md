# Day 134: Agent Tool Creation (LLM-As-Tool-Maker)

Welcome to Day 134. 

Up until now, YOU (the human developer) had to write the Python tools for the Agent. If the Agent needed to scrape a PDF, you had to write a `pdf_scraper` Python function. If it needed to calculate standard deviation, you had to write a `math_helper` function.
What if the user asks for something you didn't anticipate? The Agent fails.

Today, we achieve true autonomy. We learn **LLM-As-Tool-Maker (LATM)**. We will teach our Agents to identify a missing capability, write the Python code for a new tool on the fly, test it, and save it for future use!

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. LLM-As-Tool-Maker (LATM)
LATM is a framework with two distinct phases:
1. **The Tool Making Phase:** The Agent attempts a task and realizes it lacks the correct tool. It acts as a Software Engineer, writes a raw Python function, writes a Unit Test, runs the test, and validates the tool works.
2. **The Tool Using Phase:** The Agent acts as the End-User, successfully executing the dynamically generated function to solve the original task.

### 2. Tool Caching & The Tool Library
If an Agent writes a brilliant `parse_receipt_pdf` tool, we shouldn't throw it away! 
We save the Python code to a persistent **Tool Library** (a database). 
If a different Agent needs to parse a receipt tomorrow, it queries the Tool Library, dynamically loads the python code into memory, and uses it instantly without having to rewrite it!

### 3. The Danger (Security Sandboxing)
Allowing an AI to write and execute raw Python code on your server is the most dangerous thing you can do in computer science. 
If the Agent hallucinates and writes `os.system("rm -rf /")`, it will delete your entire server. 
You MUST execute dynamically generated tools inside a **Docker Sandbox**, a secure `gVisor` container, or a strict **WebAssembly (WASM)** environment with zero network access and strict timeout limits.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a primitive LATM loop. The agent will realize it cannot count prime numbers, so it will write a custom Python function as a string, and we will use Python's `exec()` command to run it!
*(⚠️ WARNING: This code uses `exec()`. Never run this on a production web server without a Docker sandbox!)*

Create a file named `agent_tool_creation.py`:

```python
import traceback

def mock_tool_maker_llm(task):
    """
    The Agent acts as a Software Engineer.
    It writes raw Python code to solve the user's task.
    """
    print(f"\n[TOOL MAKER] I do not have a tool for '{task}'. I will write one!")
    
    # The LLM generates the Python code as a raw string!
    generated_code = """
def custom_tool(start, end):
    primes = []
    for num in range(start, end + 1):
        if num > 1:
            for i in range(2, int(num**0.5) + 1):
                if (num % i) == 0:
                    break
            else:
                primes.append(num)
    return len(primes)
"""
    return generated_code

def secure_sandbox_executor(python_code_string, *args):
    """
    WARNING: IN REALITY, THIS MUST BE A DOCKER CONTAINER!
    We use exec() to dynamically load the LLM's string into Python memory.
    """
    print("\n[SANDBOX] Loading dynamically generated tool into memory...")
    
    # Create an empty dictionary to hold the dynamically created function
    local_namespace = {}
    
    try:
        # 1. Compile the string into real Python code
        exec(python_code_string, globals(), local_namespace)
        
        # 2. Extract the function (we expect it to be named 'custom_tool')
        dynamic_func = local_namespace.get('custom_tool')
        
        if not dynamic_func:
            return "Error: Function 'custom_tool' was not defined in the code."
            
        print("[SANDBOX] Tool loaded successfully! Executing...")
        # 3. Run the dynamically generated tool!
        result = dynamic_func(*args)
        return result
        
    except Exception as e:
        # If the LLM wrote bad code, capture the exact traceback!
        error_msg = traceback.format_exc()
        return f"Tool crashed! Traceback:\n{error_msg}"

def run_latm_simulation():
    print("--- RUNNING LLM-AS-TOOL-MAKER (LATM) SIMULATION ---\n")
    
    user_task = "Count the number of prime numbers between 10,000 and 50,000."
    print(f"User Request: {user_task}")
    
    # 1. The Agent writes the tool
    generated_code = mock_tool_maker_llm(user_task)
    print(f"\n[GENERATED CODE STR]\n{generated_code}")
    
    # 2. We execute the tool dynamically!
    start_num = 10000
    end_num = 50000
    
    result = secure_sandbox_executor(generated_code, start_num, end_num)
    
    print(f"\n[FINAL RESULT] The Agent's custom tool returned: {result}")
    print("\n[SYSTEM] Saving this code to the Tool Library Database for future agents to use!")

if __name__ == "__main__":
    run_latm_simulation()
```

### Key Takeaways from Code:
1. **Dynamic Execution:** Notice how Python's `exec()` command takes a standard text string and turns it into executable machine logic. The LLM literally wrote a program that ran itself!
2. **The Feedback Loop:** If the `exec()` block threw an exception (e.g., SyntaxError), our `except` block catches the traceback. In a real system, you would feed that traceback back to the `mock_tool_maker_llm` and say *"Your code crashed. Fix it."* (This is the Generator-Critic architecture from Day 132!).

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Tool Registry
If your agent creates 100 tools, how does a future agent know which one to use?
**Your Task:**
1. Conceptually design a Vector Database for the Tool Library.
2. When the LLM generates a tool, you must also force it to generate a detailed Docstring (e.g., *"This tool takes a start and end integer and counts the prime numbers."*).
3. You embed that Docstring into the Vector DB.
4. When a future Agent is asked to count primes, it searches the Vector DB, finds the matching Docstring, retrieves the Python code, and runs it!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"An Agent that creates and executes its own tools is incredibly powerful but incredibly dangerous. Design the safety model. Cover sandboxing, code review, testing workflows. What types of tools should never be auto-generated?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Sandbox (Defense in Depth):** 
   - State that `exec()` is unacceptable. 
   - Propose using a serverless environment (like AWS Lambda) or ephemeral Docker containers with networking disabled. The code can only perform math or local text manipulation; it cannot access the internet to exfiltrate data.
2. **The CI/CD Workflow (Testing):**
   - The LLM must generate Unit Tests alongside the Tool. The Sandbox runs the Unit Tests. Only if the tests pass is the Tool added to the Registry.
3. **The Human Approval Gate (What NOT to Auto-Generate):**
   - State clearly: *Agents should never auto-generate tools that mutate external state.* (e.g., executing SQL `DELETE`, sending Emails, or calling Stripe APIs). 
   - If an Agent generates a tool that requires network access or database mutation, it must trigger a Human-in-the-Loop breakpoint, requiring a Senior Engineer to code-review the generated Python before it is allowed to execute.

---
**Task for the end of the day:** Commit your code to Git. 

We have taught Agents to write code. 
Now, it's time to build the ultimate software engineer. An agent that can read an entire GitHub repository, navigate the file tree, and fix bugs autonomously.

Tomorrow, in **Day 135**, we learn about **SWE-Agent and AI-Powered Software Development**!
