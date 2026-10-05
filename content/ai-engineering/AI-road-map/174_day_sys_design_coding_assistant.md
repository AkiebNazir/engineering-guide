# Day 174: System Design: Autonomous Coding Assistant (Copilot)

Welcome to Day 174.

When you type a comment like `# Connect to the database` in VS Code, GitHub Copilot instantly suggests 20 lines of perfect Python code.
If you think Copilot just sends your one-line comment to OpenAI, you are wrong. A one-line comment isn't enough information to write database code. The AI needs to know what database library you are using, what the environment variables are named, and what the `User` schema looks like.

Today, we learn how to design a **Coding Assistant**. We will learn about Context Gathering, Jaccard Similarity, and Streaming Architectures.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Context Window Problem
If you have a massive enterprise codebase with 10,000 files, you cannot send the entire codebase to the LLM on every keystroke. It would cost $5.00 per keystroke and take 30 seconds to process.
The secret to Copilot is **Context Gathering (Retrieval)**. 
When you type a comment, the IDE extension quietly scans your local workspace to build a highly relevant, condensed prompt.

### 2. Context Ranking Algorithms
How does the IDE know which 3 files (out of 10,000) to include in the prompt?
1. **Jaccard Similarity / TF-IDF:** The IDE breaks your current file into keywords. It searches the rest of your open files for those same keywords. If `database.py` shares 40 keywords with your current file, it gets included in the prompt!
2. **Path Similarity:** If you are editing `app/models/user.py`, the IDE assumes `app/models/payment.py` is highly relevant because it sits in the same directory.
3. **LSP (Language Server Protocol):** The IDE looks at the actual Abstract Syntax Tree (AST). If you type `import sqlalchemy`, the IDE guarantees that `sqlalchemy` documentation/snippets are included in the prompt.

### 3. The Copilot Prompt Architecture
Once the IDE gathers the context, it constructs a massive, hidden prompt. It looks like this:
```text
<system>You are an expert programmer. Complete the code.</system>
<context_file name="database.py">class DB...</context_file>
<context_file name="models.py">class User...</context_file>
<current_file name="main.py">
import database
import models

def get_user():
    # Connect to the database
    [CURSOR_IS_HERE]
</current_file>
```
This entire text block is sent to the LLM. The LLM generates the text that replaces `[CURSOR_IS_HERE]`.

### 4. Streaming & Ghost Text
Developers type fast. If Copilot takes 2 seconds to generate 20 lines of code, the developer will have already typed past the suggestion point.
Copilot relies on **Server-Sent Events (SSE)** (Day 153). As the LLM generates tokens on the GPU, they are streamed down to the IDE in milliseconds and rendered as gray "Ghost Text". If the developer hits `Tab`, the Ghost Text becomes real code.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual implementation of the Copilot Backend. We will simulate an IDE sending a cursor position, the backend gathering context, and generating a code completion!

```python
import time
import random

# --- MOCK IDE WORKSPACE ---
# Simulating the files currently existing in the user's project
WORKSPACE_FILES = {
    "database.py": "def connect_db():\n    return 'connected_instance'",
    "utils.py": "def sanitize_string(s):\n    return s.strip()",
    "config.json": '{"db_url": "postgres://localhost"}'
}

# --- THE COPILOT BACKEND ---

class ContextGatherer:
    def rank_and_retrieve(self, current_file_content: str) -> str:
        """
        Simulates Jaccard Similarity. We look for keywords in the current 
        file to decide which workspace files to inject into the prompt.
        """
        context_string = ""
        print("   [CONTEXT] Scanning workspace for relevant files...")
        
        if "connect_db" in current_file_content or "database" in current_file_content:
            context_string += f"<file name='database.py'>\n{WORKSPACE_FILES['database.py']}\n</file>\n"
            
        return context_string

class CodeCompletionModel:
    def generate_stream(self, prompt: str):
        """Simulates an LLM generating code token-by-token."""
        print("   [LLM] Generating completion stream...")
        
        # A mocked completion based on the prompt
        completion = "db = connect_db()\n    return db"
        tokens = completion.split(" ")
        
        for token in tokens:
            time.sleep(0.1) # Simulate GPU compute time
            yield token + " "

# --- THE PIPELINE ---

def handle_ide_request(current_filename: str, file_content_before_cursor: str):
    print(f"\n--- COPILOT TRIGGERED IN '{current_filename}' ---")
    start_time = time.time()
    
    gatherer = ContextGatherer()
    llm = CodeCompletionModel()
    
    # 1. Gather Context
    relevant_context = gatherer.rank_and_retrieve(file_content_before_cursor)
    
    # 2. Construct the massive hidden prompt
    full_prompt = f"""
    {relevant_context}
    <current_file name='{current_filename}'>
    {file_content_before_cursor}
    """
    
    # 3. Stream the generation back to the IDE (Ghost Text)
    print("   [IDE] Rendering Ghost Text: ", end="")
    
    stream = llm.generate_stream(full_prompt)
    for chunk in stream:
        # In reality, this is sent over a WebSocket or SSE to VS Code
        print(f"\033[90m{chunk}\033[0m", end="", flush=True) # \033[90m makes text gray!
        
    print(f"\n\n✅ Total latency to final token: {(time.time() - start_time)*1000:.0f}ms")

# --- EXECUTION ---
def run_copilot_simulation():
    # The developer types a comment and pauses...
    code_in_ide = """import database

def fetch_data():
    # Connect to the database and
"""
    handle_ide_request("main.py", code_in_ide)

# To run:
# run_copilot_simulation()
```

### 🔍 Understanding the Enterprise Value
Notice how the LLM perfectly suggested `db = connect_db()`. If we hadn't gathered context, the LLM wouldn't know that the `database.py` file contained a function specifically named `connect_db`. 
The magic of Copilot is not the LLM. The magic is the highly aggressive, lightning-fast context gathering happening inside VS Code before the LLM is even called.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Currently, our pipeline only looks at the text *before* the cursor. 
If a developer goes into the middle of an existing function and hits Enter, there is code *after* the cursor! 
**Your Task:** Research **FIM (Fill-in-the-Middle)**. It is a specific training objective for code models. Understand how you format a prompt using `<PRE>`, `<SUF>` (Suffix), and `<MID>` tokens to force the LLM to write code that perfectly bridges the gap between the prefix and suffix!

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Design an Enterprise Coding Assistant for a bank. You cannot use public APIs like OpenAI due to data privacy. The bank has a massive 50-million-line proprietary monorepo. How do you design the context retrieval, model serving, and telemetry architecture?"*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Privacy & Security:** Acknowledge the constraint immediately. The model must be hosted internally (e.g., vLLM cluster running `StarCoder` or `CodeLlama`) inside the bank's VPC. Code cannot leave the network.
2. **Enterprise RAG (Retrieval):** Jaccard similarity isn't enough for a 50-million-line monorepo. Propose a nightly Airflow job that indexes the entire monorepo into a Vector Database. When the IDE extension needs context, it performs a Semantic Search (Day 172) against the Vector DB to find relevant proprietary functions before calling the internal LLM.
3. **Latency:** Ensure the model is served using Continuous Batching and Tensor Parallelism (Day 154) to meet the strict <300ms Time-To-First-Token constraint for IDE rendering.
4. **Telemetry (Evaluation):** How do we know if the model is good? We cannot use LLM-as-a-Judge. We must log **Acceptance Rate** (Did the developer hit Tab?) and **Retention Rate** (Did the developer delete the generated code 5 minutes later?).

---
**Task for the end of the day:** Install an open-source Copilot alternative (like `Continue.dev` or `Codeium`) in VS Code. Look at its settings to see how it allows you to connect to local models!

Tomorrow, in **Day 175**, we tackle the nightmare of **Multi-Tenant LLM Platforms**. How do you serve 100 different fine-tuned models to 100 different teams without buying 100 different GPUs?
