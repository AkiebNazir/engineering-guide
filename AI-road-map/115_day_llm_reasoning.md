# Day 115: LLM Reasoning (CoT, ToT & ReAct)

Welcome to Day 115. We have given our LLM memory and tools. 
But standard LLMs still fail at logic. If you ask an LLM a complex math puzzle, it will instantly blurt out the wrong answer. 

Why? Because the Transformer architecture forces the model to predict the final answer in a single mathematical pass. Humans don't do that. If you ask a human $245 \times 13$, they don't blurt out the answer. They pull out a scratchpad and do the math step-by-step.

Today, we teach the LLM how to use a scratchpad. We learn **Cognitive Architectures**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Chain-of-Thought (CoT)
The simplest and most famous hack in AI history. By simply appending the phrase *"Let's think step-by-step"* to your prompt, you force the LLM to output its intermediate reasoning *before* outputting the final answer.
Because the LLM uses its own generated text as the context for the next word, "thinking out loud" mathematically improves its logical accuracy by $300\%$!

### 2. Self-Consistency
If an LLM makes a mistake on Step 2 of a CoT, the entire final answer will be wrong. 
To fix this, we use **Self-Consistency**: We run the exact same CoT prompt 5 times in parallel. The LLM will generate 5 different reasoning paths. We take the "Majority Vote" of the final answers!

### 3. Tree of Thought (ToT)
CoT is strictly linear. Humans don't think linearly. We explore a path, realize it's a dead end, and backtrack.
**Tree of Thought** allows the LLM to brainstorm 3 different possible *next steps*. We ask the LLM to "score" each step from 1 to 10. We use a standard computer science Breadth-First-Search (BFS) algorithm to navigate this "Tree" of logic, abandoning paths that score low!

### 4. The ReAct Architecture (Reason + Act)
The ultimate Agent paradigm. It merges Chain of Thought with Tool Use.
Instead of just calling a tool, the LLM is forced into a strict loop:
1. **Thought:** *"I need to find the CEO of Apple. I should use the Web Search tool."*
2. **Action:** `SearchWeb(Apple CEO)`
3. **Observation:** *"Tim Cook is the CEO of Apple."*
4. **Thought:** *"Now I need to find Tim Cook's age. I will use the Search tool again."*
By forcing the LLM to literally "think" about what it just observed, the agent can solve incredibly complex, multi-step web research tasks autonomously!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a raw **ReAct Agent Loop** in pure Python. We will see exactly how to parse the Thought, Action, and Observation cycle!

Create a file named `react_agent.py`:

```python
import re

# 1. The Mock Tool
def get_stock_ticker(company_name):
    print(f"[TOOL EXECUTED] Searching ticker for: {company_name}")
    if "apple" in company_name.lower(): return "AAPL"
    return "UNKNOWN"

# 2. The ReAct System Prompt
REACT_SYSTEM_PROMPT = """
You are a reasoning agent. You must solve the user's problem by looping through Thought, Action, and Observation.

You have access to the following tools:
- get_stock_ticker(company_name)

Use the exact following format:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [get_stock_ticker]
Action Input: the input to the action
Observation: the result of the action (provided by the system)
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question
"""

# 3. The Mock LLM Generation
def mock_llm_generation(prompt_history):
    history_text = "\n".join(prompt_history)
    
    # First Pass: The LLM thinks and calls a tool!
    if "Observation:" not in history_text:
        return """Thought: I need to find the stock ticker for Apple Inc to answer the user.
Action: get_stock_ticker
Action Input: Apple Inc"""
        
    # Second Pass: The LLM reads the Observation and gives the final answer!
    if "Observation: AAPL" in history_text:
        return """Thought: I now know the final answer. The ticker is AAPL.
Final Answer: The stock ticker for Apple is AAPL."""
        
    return "Thought: I am confused.\nFinal Answer: Error."

def run_react_loop():
    print("--- RUNNING ReAct AGENT LOOP ---\n")
    
    question = "Question: What is the stock ticker for Apple Inc?"
    prompt_history = [REACT_SYSTEM_PROMPT, question]
    print(f"User: {question}\n")
    
    max_steps = 5
    for step in range(max_steps):
        print(f"--- STEP {step+1} ---")
        
        # 1. LLM Generates Thought and Action
        llm_output = mock_llm_generation(prompt_history)
        print(f"LLM Output:\n{llm_output}\n")
        
        # We append what the LLM wrote to the history
        prompt_history.append(llm_output)
        
        # 2. Check if the LLM reached the Final Answer!
        if "Final Answer:" in llm_output:
            print("[SUCCESS] Agent reached final conclusion!")
            break
            
        # 3. Parse the Action and Action Input using Regex!
        action_match = re.search(r"Action: (.*)", llm_output)
        input_match = re.search(r"Action Input: (.*)", llm_output)
        
        if action_match and input_match:
            action_name = action_match.group(1).strip()
            action_input = input_match.group(1).strip()
            
            # 4. Execute the Tool!
            if action_name == "get_stock_ticker":
                observation_result = get_stock_ticker(action_input)
            else:
                observation_result = "Tool not found."
                
            # 5. Inject the Observation back into the prompt history!
            observation_text = f"Observation: {observation_result}"
            print(f"System injects: {observation_text}\n")
            prompt_history.append(observation_text)

if __name__ == "__main__":
    run_react_loop()
```

### Key Takeaways from Code:
1. **The Parsing Logic:** A ReAct agent relies entirely on Regex string parsing. If the LLM hallucinates and outputs `ActionToTake: get_stock_ticker` instead of the strict `Action: get_stock_ticker`, your regex will fail and the agent crashes! This is why you must use highly aligned models for agentic tasks.
2. **The Prompt History:** The prompt grows continuously with every loop. The LLM gets to literally "read its own mind" from previous steps!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Tree of Thought
ToT is extremely difficult to code because it requires managing multiple parallel conversational branches.
**Your Task:**
1. Conceptually design a Python script that maintains a List of active "Paths".
2. Ask the LLM to generate 3 possible "Thoughts" for the next step.
3. Use a secondary LLM call to score each Thought from 1 to 10.
4. Keep the path with the highest score, append it to the history, and repeat!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"LLMs are notoriously bad at multi-step reasoning. Propose a system that achieves reliable 10-step logical reasoning for a financial auditing tool. Discuss CoT, ToT, Verification, and when to fall back to symbolic algorithms."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Fallibility of Text Generation:** 
   - State that LLMs are not calculators. Even with CoT, if an LLM is asked to multiply two 8-digit numbers, it will fail because its arithmetic is statistically approximated.
2. **Tool-Backed ReAct:**
   - Propose a ReAct framework where the LLM is explicitly forbidden from doing math. If it needs to calculate taxes, it must output Python code or call a Calculator API (falling back to symbolic, deterministic algorithms).
3. **Verification (Process Reward Models):**
   - Explain that for a 10-step audit, the chance of a hallucination on a single step is high. Propose using a Process Reward Model (PRM)—a secondary model that evaluates the logical validity of *each individual step* before allowing the agent to proceed to the next step.

---
**Task for the end of the day:** Commit your code to Git. 

We can now build cognitive agents. But what if we want the agent to write code? 
Standard LLMs can write a 20-line Python function. But they cannot fix a bug in a 10,000-file Enterprise React repository.

Tomorrow, in **Day 116**, we learn the secrets behind GitHub Copilot: **Fill-in-the-Middle (FIM) and Repository-Level Context**!
