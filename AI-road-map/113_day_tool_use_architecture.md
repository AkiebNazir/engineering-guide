# Day 113: Tool Use & Function Calling

Welcome to Day 113. 

Language models have a fatal flaw: They are frozen in time. If you ask a base model *"What is the current stock price of Apple?"*, it will either confidently hallucinate a number, or it will apologize and state that its training data cut-off was 6 months ago.

But what if the <abbr title="Large Language Model">LLM</abbr> could browse the internet? What if it could use a calculator to solve math? What if it could run Python code? 
Today, we take our first step toward Agentic <abbr title="Artificial Intelligence">AI</abbr>: **Tool Use (Function Calling)**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Tool Paradigm
You do not teach the <abbr title="Large Language Model">LLM</abbr> the stock price. You give the <abbr title="Large Language Model">LLM</abbr> a "Tool" (a Python function that calls the Yahoo Finance <abbr title="Application Programming Interface">API</abbr>). 
When the user asks a question, the <abbr title="Large Language Model">LLM</abbr> makes a mathematical decision:
1. *Do I know the answer from my pre-training?* -> Just answer.
2. *Is this a dynamic/math question?* -> Output a JSON command to trigger a Tool!

### 2. The Tool Schema
How does the <abbr title="Large Language Model">LLM</abbr> know what tools exist? You inject a JSON Schema into the System Prompt. 
The schema describes the tool's name, its purpose, and the arguments it requires.
```json
{
  "name": "get_stock_price",
  "description": "Fetches the real-time stock price of a company.",
  "parameters": {
    "ticker": {"type": "string", "description": "The stock ticker symbol, e.g., AAPL"}
  }
}
```

### 3. The Execution Loop (The 4 Steps)
Tool use is not magic. The <abbr title="Large Language Model">LLM</abbr> cannot execute Python code. The <abbr title="Large Language Model">LLM</abbr> just outputs text. You (the developer) must build the loop:
1. **The Request:** User asks: *"What is Apple's stock?"*
2. **The <abbr title="Large Language Model">LLM</abbr> Decision:** The <abbr title="Large Language Model">LLM</abbr> outputs strict JSON: `{"tool_call": "get_stock_price", "args": {"ticker": "AAPL"}}`. **(The <abbr title="Large Language Model">LLM</abbr> stops generating here!)**
3. **The Backend Execution:** Your Python backend intercepts this JSON. *Your Python code* actually calls the Yahoo Finance <abbr title="Application Programming Interface">API</abbr> and gets the number `150.25`.
4. **The Feedback:** Your Python backend creates a new message in the chat history: `Role: Tool, Content: "150.25"`. You send this *back* to the <abbr title="Large Language Model">LLM</abbr>. 
5. **The Final Answer:** The <abbr title="Large Language Model">LLM</abbr> reads the tool response and generates: *"Apple's current stock price is $150.25."*

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Tool Use Execution Loop from scratch in Python. We will define a mock Weather <abbr title="Application Programming Interface">API</abbr> and simulate the <abbr title="Large Language Model">LLM</abbr> deciding to call it!

Create a file named `tool_use.py`:

```python
import json

# 1. The ACTUAL Python Tool (The LLM cannot run this, only the backend can!)
def get_current_weather(location):
    """Mock API call to get weather."""
    print(f"[BACKEND] Executing HTTP Request to Weather API for '{location}'...")
    # Mock response
    weather_data = {"location": location, "temperature": "72F", "condition": "Sunny"}
    return json.dumps(weather_data)

# 2. Mocking the LLM's logic
def mock_llm_generation(messages, tools):
    """Simulates an LLM choosing to use a tool based on the prompt."""
    last_message = messages[-1]["content"]
    
    # If the LLM sees a weather question, it outputs a TOOL CALL JSON!
    if "weather" in last_message.lower():
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "name": "get_current_weather",
                    "arguments": '{"location": "Tokyo"}'
                }
            ]
        }
        
    # If the LLM sees the Tool's result in the history, it answers the user!
    if messages[-1]["role"] == "tool":
        weather_info = json.loads(messages[-1]["content"])
        return {
            "role": "assistant",
            "content": f"The weather in {weather_info['location']} is currently {weather_info['temperature']} and {weather_info['condition']}."
        }
        
    return {"role": "assistant", "content": "I am a helpful assistant."}

def run_tool_loop():
    print("--- RUNNING TOOL EXECUTION LOOP ---\n")
    
    # The Chat History
    messages = [{"role": "user", "content": "What is the weather in Tokyo?"}]
    print(f"User: '{messages[0]['content']}'\n")
    
    # --- STEP 1: The First LLM Pass (The Decision) ---
    print("Step 1: LLM decides what to do...")
    llm_response = mock_llm_generation(messages, tools=["get_current_weather"])
    
    if "tool_calls" in llm_response:
        tool_call = llm_response["tool_calls"][0]
        tool_name = tool_call["name"]
        tool_args = json.loads(tool_call["arguments"])
        print(f"-> LLM Output: Please call tool '{tool_name}' with args {tool_args}\n")
        
        # --- STEP 2: The Backend Execution ---
        print("Step 2: Python Backend intercepts and executes the tool...")
        if tool_name == "get_current_weather":
            tool_result = get_current_weather(tool_args["location"])
            
            # --- STEP 3: Append to History ---
            # We append the LLM's tool call request, AND the actual tool result!
            messages.append(llm_response)
            messages.append({
                "role": "tool",
                "name": tool_name,
                "content": tool_result
            })
            print(f"-> Tool Result appended to chat history: {tool_result}\n")
            
            # --- STEP 4: The Second LLM Pass (The Final Answer) ---
            print("Step 4: Sending history back to LLM to write the final answer...")
            final_response = mock_llm_generation(messages, tools=["get_current_weather"])
            print(f"\nFinal LLM Response: '{final_response['content']}'")

if __name__ == "__main__":
    run_tool_loop()
```

### Key Takeaways from Code:
1. **The Middleman:** You are the middleman. The <abbr title="Large Language Model">LLM</abbr> is trapped inside a box. It slides a note under the door saying *"Please run this tool"*. You run the tool on your laptop, and slide the result back under the door. 
2. **Structured Generation:** How did we guarantee the <abbr title="Large Language Model">LLM</abbr> outputted valid JSON for the `arguments`? We used the techniques from Day 112 (Constrained Decoding/JSON Mode)!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Multi-Step Tool Chains
Sometimes an <abbr title="Large Language Model">LLM</abbr> needs to use multiple tools in a row before talking to the user.
**Your Task:**
1. Conceptually map out the loop for the prompt: *"What is the stock price of the company that makes the iPhone?"*
2. **Turn 1:** <abbr title="Large Language Model">LLM</abbr> calls Tool 1: `search_web("Company that makes iPhone")`. 
3. **Turn 2:** Backend returns `"Apple Inc. (Ticker: AAPL)"`.
4. **Turn 3:** <abbr title="Large Language Model">LLM</abbr> reads the history and calls Tool 2: `get_stock_price("AAPL")`.
5. **Turn 4:** Backend returns `150.25`.
6. **Turn 5:** <abbr title="Large Language Model">LLM</abbr> answers the user.
Notice how the <abbr title="Large Language Model">LLM</abbr> recursively calls itself until it has all the information it needs!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design a tool-use system where the <abbr title="Large Language Model">LLM</abbr> has access to 500 enterprise tools (APIs, databases, internal services). How do you handle tool discovery, selection, and the massive context window bloat?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Context Bloat Problem:** 
   - State that if you put 500 JSON Tool Schemas into the System Prompt, it will consume 20,000 tokens. The <abbr title="Large Language Model">LLM</abbr> will become confused (Lost in the Middle), latency will skyrocket, and <abbr title="Application Programming Interface">API</abbr> costs will bankrupt the company.
2. **Dynamic Tool Retrieval (<abbr title="Retrieval-Augmented Generation">RAG</abbr> for Tools):**
   - Propose embedding the descriptions of all 500 tools into a Vector Database. 
   - When the user asks a question, run a vector similarity search between the User Prompt and the Tool Descriptions. Retrieve only the Top 5 most relevant tools. 
   - Inject *only* those 5 JSON schemas into the <abbr title="Large Language Model">LLM</abbr>'s prompt! This reduces the context window from 20,000 tokens to 500 tokens!

---
**Task for the end of the day:** Commit your code to Git. 

Speaking of Context Window Bloat, what happens when a user talks to your chatbot for 2 hours? The chat history grows until it crashes the server with an `Out of Memory` error.

Tomorrow, in **Day 114**, we solve this by mastering **Multi-Turn Conversation and Context Management**!
