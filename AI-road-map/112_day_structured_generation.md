# Day 112: Structured Generation (Outlines & <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>)

Welcome to Day 112. 

If you use an <abbr title="Large Language Model">LLM</abbr> as the "brain" of a web application, you need the <abbr title="Large Language Model">LLM</abbr> to output structured data (like <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>) so your backend database can process it. 

You write a prompt: *"Extract the user's name and age from this text. Output strict <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>."*
$95\%$ of the time, the <abbr title="Large Language Model">LLM</abbr> outputs perfect <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>.
But $5\%$ of the time, it forgets a closing bracket `}`, or it adds a conversational prefix like *"Here is the <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> you requested:"*. 
When your Python backend calls `json.loads(llm_output)`, your entire application crashes. 

Today, we learn **Structured Generation**. We will mathematically force the <abbr title="Large Language Model">LLM</abbr> to output $100\%$ valid <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>, every single time!

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Parsing Nightmare
Developers usually try to fix the $5\%$ failure rate by writing complex Regex scripts to strip away the conversational prefixes, or by writing "Retry Loops" (if it fails, ask the <abbr title="Large Language Model">LLM</abbr> to try again). 
This increases latency and <abbr title="Application Programming Interface">API</abbr> costs massively.

### 2. Constrained Decoding (Masking Logits)
During Generation, an <abbr title="Large Language Model">LLM</abbr> outputs a probability distribution over its entire vocabulary of 32,000 words. 
What if we just *delete* the probabilities of words that break our <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> syntax?

If the <abbr title="Large Language Model">LLM</abbr> has already generated `{"name": "John"`, the <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> format dictates that the *only* valid next character is a comma `,` or a closing bracket `}`. 
Before the <abbr title="Large Language Model">LLM</abbr> selects the next token, we intercept the probabilities. We set the probability of `,` and `}` to their normal values, and we set the probability of every other word in the dictionary to **Negative Infinity**! 
The <abbr title="Large Language Model">LLM</abbr> is mathematically forced to output a valid <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> character!

### 3. Finite State Machines (FSM)
How do we know which characters are valid at any given microsecond?
Libraries like **Outlines** and **Guidance** compile your <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> Schema (or Pydantic Model) into a **Finite State Machine (FSM)**. 
An FSM is a computer science graph that tracks exactly where you are in the <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> structure. It acts as the ultimate bouncer, instantly blocking any token that violates the path of the graph.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's look at how the open-source `outlines` library implements this magic.
*(Note: Mentally run `pip install outlines pydantic`)*

Create a file named `structured_gen.py`:

```python
from pydantic import BaseModel
import json

# Let's pretend we imported outlines:
# import outlines

def mock_outlines_generation(pydantic_schema, user_prompt):
    """
    Simulates the Outlines constrained decoding engine.
    The LLM is FORCED to output data that perfectly matches the Pydantic Schema!
    """
    print(f"[OUTLINES FSM] Compiling Pydantic Schema '{pydantic_schema.__name__}' into a Regex Finite State Machine...")
    print("[LLM GENERATION] Logits are being masked at every step. Invalid syntax is blocked.")
    
    # The LLM cannot output "Here is the JSON:". It can ONLY output the raw JSON.
    return '{"name": "Alice Smith", "age": 28, "is_active": true}'

def run_structured_generation():
    print("--- RUNNING STRUCTURED GENERATION PIPELINE ---\n")
    
    # 1. Define the exact structure we want using standard Pydantic!
    class UserProfile(BaseModel):
        name: str
        age: int
        is_active: bool
        
    print("Pydantic Schema Defined. We need 'name' (str), 'age' (int), 'is_active' (bool).\n")
    
    # 2. The User Prompt
    prompt = "Extract the user profile: Hi, my name is Alice Smith. I just turned 28 years old, and my account is currently active."
    print(f"Prompt: '{prompt}'\n")
    
    # 3. Generate with Outlines!
    # In reality, the code looks like this:
    # generator = outlines.generate.json(model, UserProfile)
    # result_json_string = generator(prompt)
    
    result_json_string = mock_outlines_generation(UserProfile, prompt)
    
    print(f"\nRaw LLM Output String:\n{result_json_string}\n")
    
    # 4. Safely load into Python!
    try:
        # This will NEVER crash, because Outlines guaranteed the syntax!
        user_dict = json.loads(result_json_string)
        
        # We can safely pass it back into Pydantic to get a proper Python Object!
        user_object = UserProfile(**user_dict)
        
        print("Success! Parsed into a Python Object:")
        print(f"Name: {user_object.name} (Type: {type(user_object.name)})")
        print(f"Age: {user_object.age} (Type: {type(user_object.age)})")
        print(f"Active: {user_object.is_active} (Type: {type(user_object.is_active)})")
        
    except json.JSONDecodeError:
        print("FATAL ERROR: The JSON crashed the backend!")

if __name__ == "__main__":
    run_structured_generation()
```

### Key Takeaways from Code:
1. **The FSM Compilation:** Compiling a massive <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> schema into an FSM Regex graph takes a few milliseconds, but `outlines` caches the graph. Once cached, masked generation runs at the exact same speed as normal generation!
2. **Zero Prompt Engineering:** Notice the prompt: *"Extract the user profile"*. We didn't have to write a massive prompt saying *"You are a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> assistant. Ensure you use double quotes. Ensure you do not add conversational text."* The FSM enforces the rules, freeing up your prompt space for actual logic!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> Constrained Decoding
You want an <abbr title="Large Language Model">LLM</abbr> to generate <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> queries. But LLMs hallucinate table names!
**Your Task:**
1. Conceptually design an FSM constraint for <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>.
2. If your database only has a `users` table and an `orders` table, you can write a Regex constraint: `SELECT \* FROM (users|orders)`.
3. If you pass this Regex to `outlines.generate.regex(model, pattern)`, the <abbr title="Large Language Model">LLM</abbr> is mathematically prevented from querying any table that doesn't exist! It literally cannot hallucinate!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You need 100% valid <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> from an <abbr title="Large Language Model">LLM</abbr> in a high-traffic production app. Compare three approaches: OpenAI's '<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> Mode', Constrained Decoding (Outlines), and Post-Processing Retry Loops. Discuss reliability and latency."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Post-Processing Retry Loops:** 
   - Dismiss this immediately for high-traffic apps. Catching a `JSONDecodeError` and re-prompting the <abbr title="Large Language Model">LLM</abbr> doubles the <abbr title="Application Programming Interface">API</abbr> cost and doubles the latency for the user.
2. **OpenAI <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> Mode:**
   - Explain that <abbr title="Application Programming Interface">API</abbr> "<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> Mode" guarantees the output is syntactically valid <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>. *However*, it does NOT guarantee it matches your specific schema! It might output `{"first_name": "John"}` when your backend expected `{"name": "John"}`. Your app will still crash with a `KeyError`.
3. **Constrained Decoding (Outlines):**
   - Crown this the winner for self-hosted models. It guarantees valid syntax AND guarantees exact schema adherence. Because it masks logits during the forward pass, it requires exactly zero retries, providing the lowest latency and highest reliability.

---
**Task for the end of the day:** Commit your code to Git. 

We can now guarantee the <abbr title="Large Language Model">LLM</abbr> outputs perfect <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>. 
But what do we *do* with that <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>? What if that <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> represents a command to execute a Python function or search the web?

Tomorrow, in **Day 113**, we learn the foundation of Agentic <abbr title="Artificial Intelligence">AI</abbr>: **Tool Use and Function Calling Architecture**!
