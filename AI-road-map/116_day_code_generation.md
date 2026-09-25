# Day 116: Code Generation & Repository-Level Context

Welcome to Day 116. Writing a 20-line Python function from scratch is easy for an <abbr title="Large Language Model">LLM</abbr>. 

But what if you are building an IDE assistant like GitHub Copilot? You want the <abbr title="Large Language Model">LLM</abbr> to autocomplete a line of code exactly in the middle of a 500-line file. 
Furthermore, you want the <abbr title="Large Language Model">LLM</abbr> to automatically understand the 50 other files in your repository, knowing exactly which functions to import without you having to copy-paste the entire codebase into the prompt!

Today, we learn the advanced architecture behind enterprise Code Assistants: **Fill-in-the-Middle (FIM)** and **Repository-Level Context**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Fill-in-the-Middle (FIM)
Standard base models are trained using strictly Left-to-Right Next-Token Prediction. They only know what comes *before* the cursor.
But if you put your cursor in the middle of a Python file, the <abbr title="Large Language Model">LLM</abbr> needs to know the code that comes *after* the cursor to intelligently autocomplete the middle!
To fix this, researchers introduced **FIM Training**. They take a file, cut it into three pieces (Prefix, Middle, Suffix), and shuffle them during training!
The format is: `<PREFIX> ... <SUFFIX> ... <MIDDLE>`. 
The model learns to read the Prefix, then read the Suffix, and finally predict the missing Middle!

### 2. Repository-Level Context
You cannot fit 10,000 files into a 128k context window. You must use <abbr title="Retrieval-Augmented Generation">RAG</abbr>. 
But standard semantic <abbr title="Retrieval-Augmented Generation">RAG</abbr> is terrible for code. If you search for "database connection", standard <abbr title="Retrieval-Augmented Generation">RAG</abbr> might pull a README file instead of the actual `db.py` connection pool.

Instead of Semantic Search, Code Assistants use **Abstract Syntax Trees (ASTs)**. 
An AST parser reads your codebase and builds a mathematical graph of dependencies. 
If the user opens `auth.py` and types `verify_token()`, the IDE extension instantly queries the AST, finds the file where `verify_token()` is defined (`jwt_utils.py`), and silently injects the source code of `jwt_utils.py` into the <abbr title="Large Language Model">LLM</abbr>'s prompt!

### 3. Evaluation: HumanEval vs SWE-Bench
- **HumanEval:** The old benchmark. 164 simple, isolated Python functions (e.g., *"Reverse a string"*). It is too easy for modern LLMs.
- **SWE-Bench (Software Engineering Benchmark):** The modern gold standard. They took 2,294 real, solved GitHub Issues from massive repositories like `django` and `scikit-learn`. The <abbr title="Large Language Model">LLM</abbr> is given the Issue text and the entire codebase. It must autonomously navigate the files, write the fix, and pass the repository's hidden test suite!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Python script that implements the FIM prompting format and simulates a naive AST parser retrieving repository context!

Create a file named `code_assistant.py`:

```python
import re

def mock_fim_llm(prefix, suffix):
    """
    Simulates a model trained with Fill-in-the-Middle (e.g., CodeLlama).
    It looks at BOTH the code before and after the cursor!
    """
    print(f"\n[FIM MODEL] Analyzing Prefix and Suffix...")
    
    # The model notices the prefix defines 'a' and 'b', and the suffix returns 'result'
    # It perfectly predicts the missing middle line!
    return "result = a + b"

def naive_ast_context_retriever(active_file_content, mock_filesystem):
    """
    A naive AST parser. It looks for import statements in the active file,
    and automatically retrieves those files from the filesystem!
    """
    print("[IDE EXTENSION] Parsing active file for dependencies...")
    context = ""
    
    # Regex to find 'import X' or 'from X import Y'
    imports = re.findall(r"import (\w+)|from (\w+) import", active_file_content)
    
    for imp in imports:
        # The regex returns tuples, grab the matched word
        module_name = imp[0] if imp[0] else imp[1]
        
        # If the imported module exists in our local repo, pull it!
        if module_name in mock_filesystem:
            print(f" -> Found local dependency: '{module_name}.py'. Retrieving source code!")
            context += f"--- {module_name}.py ---\n{mock_filesystem[module_name]}\n\n"
            
    return context

def run_ide_simulation():
    print("--- RUNNING IDE CODE ASSISTANT SIMULATION ---\n")
    
    # 1. The Mock Enterprise Repository
    mock_filesystem = {
        "database": "def connect_db():\n    return 'DB_CONNECTION_OBJECT'",
        "utils": "def hash_password(pw):\n    return 'HASHED_' + pw"
    }
    
    # 2. The Active File (Where the user's cursor is!)
    # Notice the <CURSOR> marker.
    active_file = """import database
import utils

def create_user(username, password):
    db = database.connect_db()
    <CURSOR>
    return db.insert(username, result)
"""
    
    print(f"Active File:\n{active_file}")
    
    # 3. Retrieve Repository Context
    print("\nStep 1: Building Prompt Context...")
    repo_context = naive_ast_context_retriever(active_file, mock_filesystem)
    
    # 4. Split the file into Prefix and Suffix based on Cursor
    parts = active_file.split("<CURSOR>")
    prefix = parts[0]
    suffix = parts[1]
    
    # 5. Build the massive FIM Prompt!
    # In reality, Code Models use special tokens like <PRE>, <SUF>, <MID>
    print("\nStep 2: Sending FIM prompt to LLM...")
    
    # The LLM generates the missing line!
    generated_middle = mock_fim_llm(prefix, suffix)
    
    # 6. The Final File!
    final_file = prefix + generated_middle + suffix
    print(f"\n[SUCCESS] Final Autocompleted File:\n{final_file}")

if __name__ == "__main__":
    run_ide_simulation()
```

### Key Takeaways from Code:
1. **The Context Injection:** Notice how the `database` and `utils` source code is silently retrieved in the background. When the <abbr title="Large Language Model">LLM</abbr> generates the middle line, it knows exactly what functions are available in `utils.py` because we injected them into the prompt!
2. **The Suffix:** If we only gave the model the Prefix, it might have guessed `print("User created")`. But because we gave it the Suffix (`return db.insert(username, result)`), the model realized it *must* define a variable named `result`!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Test-Driven Development (TDD) Agent
You can build an agent that never writes bad code.
**Your Task:**
1. Conceptually design a bash/Python script.
2. The Agent generates a Python function and saves it to `script.py`.
3. The Agent generates a `pytest` file and saves it to `test_script.py`.
4. Your script runs `pytest test_script.py` in a secure Docker sandbox.
5. If the test fails, you capture the terminal `Traceback Error`, feed it *back* to the <abbr title="Large Language Model">LLM</abbr>, and prompt it: *"Your code failed with this error. Fix it."*
6. Loop until the tests pass!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design the architecture for an internal company 'Copilot'. Cover IDE integration, context selection, model serving, and how you will measure if it actually makes your developers more productive."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **IDE Integration & Context:** 
   - Propose building a VSCode Extension. When the user types, the extension extracts the Prefix/Suffix, uses an AST parser (like Tree-sitter) to find imported local files, and builds a massive prompt.
2. **Model Serving (Latency is King):**
   - Emphasize that Autocomplete must be instant ($<200ms$). Propose deploying a highly quantized, specifically trained FIM model (like DeepSeek-Coder-7B or CodeLlama) using an optimized inference engine like vLLM. 
3. **Measuring Productivity:**
   - Warn that "Lines of Code Written" is a terrible metric (LLMs write verbose garbage).
   - Propose tracking **Acceptance Rate** (does the dev press 'Tab'?) and **Retention Rate** (does the dev delete the autocompleted code 10 seconds later?). 
   - Ultimately, propose tracking the overall **Pull Request cycle time** (Time from Jira Ticket creation to Code Merge) before and after deploying the tool.

---
**Task for the end of the day:** Commit your code to Git. 

We can now process Text and Code. But the world is not just text. 
What if you want the <abbr title="Large Language Model">LLM</abbr> to read a flowchart image, or watch a video?

Tomorrow, in **Day 117**, we enter the world of **Multi-Modal LLMs (LMMs)**. We will learn the architecture of LLaVA and how to bolt "eyes" onto a blind <abbr title="Large Language Model">LLM</abbr>!
