# Day 89: Structured Output & Function Calling

Welcome to Day 89. LLMs naturally generate unstructured conversational text (*"Sure, I'd be happy to help! Here is the data..."*). 

But software engineering requires deterministic, structured data. If your Python backend expects a JSON object, and the <abbr title="Large Language Model">LLM</abbr> outputs conversation, your application crashes. 
Today, we learn how to force an <abbr title="Large Language Model">LLM</abbr> to output 100% perfect JSON and how to give the <abbr title="Large Language Model">LLM</abbr> the ability to trigger real-world APIs via **Function Calling**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. JSON Mode vs Function Calling
- **JSON Mode:** You prompt the model: *"Output the result in JSON."* The model guarantees the output will have valid `{}` syntax, but it might invent random keys that your backend isn't expecting.
- **Function Calling (Tool Use):** You provide the model with a strict **Schema** (e.g., "I need an object with `name` (string) and `age` (int)"). The model is guaranteed to output a JSON object that perfectly matches your schema.

### 2. How "Agentic" Tool Use Actually Works
LLMs cannot browse the web or run code. They are just text predictors. "Tool Use" is just a clever sequence of parsing.
1. **The Setup:** The User says *"What is the weather in Tokyo?"*. You send this prompt to the <abbr title="Large Language Model">LLM</abbr>, but you *also* pass a JSON Schema describing a function: `get_weather(location: string)`.
2. **The <abbr title="Large Language Model">LLM</abbr> Decision:** The <abbr title="Large Language Model">LLM</abbr> realizes it doesn't know the weather. Instead of replying to the user, it outputs a raw JSON string: `{"tool": "get_weather", "args": {"location": "Tokyo"}}`.
3. **The Python Bridge:** Your Python script detects that the <abbr title="Large Language Model">LLM</abbr> outputted a tool request. Your script pauses the <abbr title="Large Language Model">LLM</abbr>, parses the JSON, and runs the actual `requests.get()` Python code to fetch the weather.
4. **The Resolution:** Your Python script appends the raw weather data (`72 Degrees, Sunny`) back into the <abbr title="Large Language Model">LLM</abbr>'s conversation history and hits "Generate" again.
5. **The Final Answer:** The <abbr title="Large Language Model">LLM</abbr> reads the weather data and finally replies to the user: *"It is currently 72 degrees in Tokyo!"*

### 3. Constrained Decoding (How it guarantees perfection)
How does OpenAI *guarantee* the <abbr title="Large Language Model">LLM</abbr> outputs perfect JSON? They use **Constrained Decoding** (Grammar-guided generation).
Normally, the <abbr title="Large Language Model">LLM</abbr> outputs a probability distribution over 32,000 words. 
If the JSON schema demands a boolean (`True` or `False`), the inference engine mathematically overrides the <abbr title="Large Language Model">LLM</abbr>'s logits. It forces the probability of 31,998 words to exactly `0.0`. The <abbr title="Large Language Model">LLM</abbr> is physically only allowed to predict the word `"True"` or `"False"`!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Data Extraction pipeline. We will use **Pydantic** to define our strict Python data model, and simulate how an <abbr title="Large Language Model">LLM</abbr> populates it.
*(Note: In production, you would use the `instructor` library, which automatically handles the OpenAI <abbr title="Application Programming Interface">API</abbr> mapping. Here, we build the core logic to understand it.)*

Create a file named `structured_output.py`:

```python
from pydantic import BaseModel, Field
from typing import List
import json

# 1. Define the Strict Schema using Pydantic
# This is the "Blueprint" we want the LLM to fill out!
class UserProfile(BaseModel):
    name: str = Field(description="The user's full name")
    age: int = Field(description="The user's age in years")
    skills: List[str] = Field(description="A list of technical skills mentioned")
    is_looking_for_work: bool = Field(description="True if they want a job, False otherwise")

def mock_llm_function_call(user_input: str, schema: dict):
    """
    Simulates the LLM receiving the prompt and the Schema, 
    and outputting the perfectly formatted JSON string.
    """
    print(f"LLM analyzing input: '{user_input}'")
    print("LLM constrained by schema. Generating JSON...")
    
    # The LLM generates this string internally
    llm_output = """
    {
        "name": "Johnathan Doe",
        "age": 28,
        "skills": ["Python", "PyTorch", "AWS"],
        "is_looking_for_work": true
    }
    """
    return llm_output.strip()

def test_data_extraction():
    print("--- RUNNING STRUCTURED DATA EXTRACTION ---")
    
    # 2. The Unstructured User Input (Messy Text)
    messy_text = "Hey guys, I'm Johnathan Doe. I just turned 28. I've been coding in Python and PyTorch for a few years, and I know AWS. Currently open to new opportunities!"
    
    # 3. Convert the Pydantic Model to a JSON Schema to pass to the LLM
    schema_dict = UserProfile.schema()
    
    # 4. Run the LLM (It outputs a JSON string)
    raw_json_string = mock_llm_function_call(messy_text, schema_dict)
    
    print(f"\nRaw LLM Output (String):\n{raw_json_string}")
    
    # 5. The Magic: Parse the JSON string directly into our Pydantic Object!
    try:
        parsed_dict = json.loads(raw_json_string)
        
        # Pydantic validates the data types instantly!
        # If the LLM put "Twenty Eight" instead of 28, Pydantic would throw a massive error here.
        user_obj = UserProfile(**parsed_dict)
        
        print("\n--- SUCCESSFULLY EXTRACTED PYDANTIC OBJECT ---")
        print(f"Name Type:   {type(user_obj.name)} -> {user_obj.name}")
        print(f"Age Type:    {type(user_obj.age)} -> {user_obj.age}")
        print(f"Skills Type: {type(user_obj.skills)} -> {user_obj.skills}")
        print(f"Looking?     {type(user_obj.is_looking_for_work)} -> {user_obj.is_looking_for_work}")
        
    except Exception as e:
        print(f"Validation Error: {e}")

if __name__ == "__main__":
    test_data_extraction()
```

### Key Takeaways from Code:
1. **Pydantic Validation:** The <abbr title="Large Language Model">LLM</abbr>'s job is just to output text. Your Python backend's job is to run `json.loads()` and pass it into a `BaseModel`. If the <abbr title="Large Language Model">LLM</abbr> hallucinated the schema, your code will safely catch the Pydantic `ValidationError` instead of crashing your database.
2. **Self-Correction:** In production pipelines (like the `instructor` library), if Pydantic throws an error, the library automatically sends the error message *back* to the <abbr title="Large Language Model">LLM</abbr> and says: *"You messed up the JSON. The 'age' field must be an Integer. Fix it."*

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Tool Use Loop
**Your Task:**
1. Conceptually design the "While Loop" required for an Agent.
2. The User asks: *"Multiply 45 by 12, then add 50."*
3. The <abbr title="Large Language Model">LLM</abbr> outputs `{"tool": "multiply", "args": [45, 12]}`.
4. Your Python loop detects the tool call, runs `45*12=540`, and sends `540` back to the <abbr title="Large Language Model">LLM</abbr>.
5. The <abbr title="Large Language Model">LLM</abbr> reads the `540` and outputs `{"tool": "add", "args": [540, 50]}`.
6. Your Python loop runs `540+50=590`, and sends it back.
7. The <abbr title="Large Language Model">LLM</abbr> finally outputs: *"The final answer is 590."*
8. The loop exits!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are building a data extraction pipeline that processes 1 Million unstructured resumes per day into a structured Postgres SQL database. Design the system, focusing on <abbr title="Large Language Model">LLM</abbr> constraint, validation, error handling, and human-in-the-loop review."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Extraction Architecture:** 
   - State that you will use a cheaper, fast model (like GPT-4o-mini or Llama-3-8B) with strict **Constrained Decoding** via a library like `Outlines` or `Instructor`. 
   - Define a highly rigorous Pydantic schema for the Resume.
2. **The Retry Pipeline (Error Handling):**
   - Explain that LLMs will occasionally fail the schema. You must implement a retry loop with exponential backoff. If Pydantic throws a `ValidationError`, feed the stack trace back to the <abbr title="Large Language Model">LLM</abbr> up to 3 times to let it self-correct.
3. **The Dead Letter Queue (Human Review):**
   - If the <abbr title="Large Language Model">LLM</abbr> fails 3 times, do NOT crash the pipeline. Send that specific resume to a **Dead Letter Queue (DLQ)**. 
   - Build an internal UI where human reviewers can look at the DLQ, manually fix the JSON, and commit it to Postgres. This guarantees 100% data integrity for the 1 Million daily resumes.

---
**Task for the end of the day:** Commit your code to Git. 

You have mastered the tools of Enterprise <abbr title="Artificial Intelligence">AI</abbr>. 
Tomorrow, in **Day 90**, we face the Phase 3 Capstone: We will combine Vector Databases, Hybrid Search, and <abbr title="Large Language Model">LLM</abbr> Generation into one massive **Production <abbr title="Retrieval-Augmented Generation">RAG</abbr> System**!
