# Day 88: Advanced Prompt Engineering (CoT, ToT)

Welcome to Day 88. 
Prompting is not just "typing English". A prompt is the source code for an <abbr title="Large Language Model">LLM</abbr>. 
A naive prompt turns a 70-Billion parameter model into a toddler. A highly-structured, algorithmic prompt turns that same model into a PhD-level reasoning engine.

Today, we master the algorithms of Prompt Engineering: **Chain of Thought (CoT), Self-Consistency, and Tree of Thought (ToT)**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Compute Constraint
To understand prompting, you must understand how a Transformer computes.
Every time an <abbr title="Large Language Model">LLM</abbr> predicts exactly 1 token (word), it executes exactly 1 forward pass of its neural network. 
- If you ask: *"What is 245 * 31? Answer immediately."*
- The <abbr title="Large Language Model">LLM</abbr> must output the token `"7595"`. That means it used exactly **1 forward pass** of compute to do the math. The model will almost certainly fail.

### 2. Chain of Thought (CoT)
In 2022, researchers discovered a hack. By simply adding the magic phrase *"Let's think step by step"*, the model's accuracy on math problems jumped from $17\%$ to $78\%$. Why?
Because it forces the model to output words like *"First, I will multiply 200 by 30..."*.
Every extra word it generates is an extra forward pass! **Chain of Thought gives the <abbr title="Large Language Model">LLM</abbr> more compute time.** It allows the model to temporarily store intermediate math inside the context window before predicting the final answer!

### 3. Self-Consistency (Majority Vote)
CoT has a flaw: LLMs hallucinate. What if it hallucinates an error on Step 2? The final answer will be completely wrong.
**Self-Consistency** fixes this using statistics.
1. You set the model's Temperature to $0.7$ (High randomness).
2. You run the exact same CoT prompt **5 different times** in parallel.
3. You parse the final answer from all 5 outputs. 
4. If the answers are `[42, 42, 19, 42, 42]`, you take a **Majority Vote**. Because 42 appeared the most, you output 42. Hallucinations are mathematically averaged out!

### 4. Tree of Thought (ToT)
For extremely complex tasks (like writing an entire software application), even Self-Consistency fails because the sequence of steps is too long.
**Tree of Thought** allows the <abbr title="Large Language Model">LLM</abbr> to explore multiple branches of logic simultaneously using Breadth-First Search (<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>) or Depth-First Search (<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>).
- The <abbr title="Large Language Model">LLM</abbr> generates 3 possible "Step 1" plans.
- A secondary "Evaluator Prompt" grades the 3 plans. It deletes the bad plans, and keeps the best plan.
- The <abbr title="Large Language Model">LLM</abbr> generates 3 possible "Step 2" plans based on the winning Step 1.
If the <abbr title="Large Language Model">LLM</abbr> realizes it has hit a dead end, it *backtracks* up the tree and tries a different branch!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Python pipeline that implements **Self-Consistency**. We will simulate calling an <abbr title="Large Language Model">LLM</abbr> <abbr title="Application Programming Interface">API</abbr> 5 times with a high temperature, parse the final answers, and implement the Majority Vote logic.

Create a file named `self_consistency.py`:

```python
import collections

def mock_llm_api_call(prompt, temperature):
    """
    Simulates calling an LLM API (like OpenAI) with a specific temperature.
    Since temperature > 0.0 means randomness, the LLM gives different answers!
    """
    import random
    
    # We simulate the LLM attempting to solve: "John has 5 apples, eats 2, buys 4."
    
    # 80% of the time, the LLM hallucinates slightly but does the math
    # 20% of the time, it hallucinates a totally wrong number
    chance = random.random()
    
    if chance < 0.3:
        return "Let's think step by step. John starts with 5. He eats 2, so 5-2=3. Then he buys 4. 3+4=7. Final Answer: 7"
    elif chance < 0.6:
        return "Step 1: 5 apples. Step 2: minus 2 is 3. Step 3: plus 4. The result is 7. Final Answer: 7"
    elif chance < 0.8:
        return "John has 5. 5 - 2 = 3. 3 + 4 = 7. Therefore, Final Answer: 7"
    else:
        # The Hallucination!
        return "Let's think step by step. 5 minus 2 is 4. 4 plus 4 is 8. Final Answer: 8"

def extract_final_answer(llm_output):
    """
    A simple parser to extract the number after 'Final Answer:'
    """
    try:
        # Split by 'Final Answer:' and grab the last part, strip whitespace
        answer_str = llm_output.split("Final Answer:")[1].strip()
        return int(answer_str)
    except:
        return None

def test_self_consistency():
    print("--- RUNNING SELF-CONSISTENCY PIPELINE ---")
    
    prompt = "John has 5 apples, eats 2, buys 4. How many does he have? End with 'Final Answer: [number]'"
    
    # 1. Run the LLM 5 times in parallel!
    NUM_RUNS = 5
    print(f"Running LLM {NUM_RUNS} times with Temperature = 0.7...\n")
    
    extracted_answers = []
    
    for i in range(NUM_RUNS):
        # Call the LLM
        output = mock_llm_api_call(prompt, temperature=0.7)
        print(f"Run {i+1} Output:\n-> {output}")
        
        # Parse the answer
        answer = extract_final_answer(output)
        if answer is not None:
            extracted_answers.append(answer)
            
    print(f"\nExtracted Answers Array: {extracted_answers}")
    
    # 2. MAJORITY VOTE LOGIC
    if extracted_answers:
        # collections.Counter counts the frequency of each item
        vote_counts = collections.Counter(extracted_answers)
        
        # most_common(1) returns the top item. Example: [(7, 4)] means '7' appeared 4 times.
        winning_answer, votes = vote_counts.most_common(1)[0]
        
        print("\n--- MAJORITY VOTE RESULT ---")
        print(f"The LLM hallucinated, but the pipeline suppressed the error!")
        print(f"Winning Answer: {winning_answer} (Received {votes}/{NUM_RUNS} votes)")
    else:
        print("Failed to extract any valid answers.")

if __name__ == "__main__":
    test_self_consistency()
```

### Key Takeaways from Code:
1. **The Temperature Trade-off:** Normally, for math, you set Temperature to `0.0`. But if you use `0.0` for Self-Consistency, all 5 runs will output the exact same string, defeating the purpose! You must increase the temperature to force the <abbr title="Large Language Model">LLM</abbr> to explore different logical paths.
2. **Formatting Enforcement:** The hardest part of advanced prompting is parsing the output. Notice the prompt: *"End with 'Final Answer: [number]'"*. If the <abbr title="Large Language Model">LLM</abbr> disobeys this formatting, our Python regex/parser will crash.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Prompt Chaining
Instead of asking an <abbr title="Large Language Model">LLM</abbr> to do 3 things in one massive prompt, it is always better to build a **Chain**.
**Your Task:**
1. Conceptually design a 3-Step Prompt Chain.
2. **Node 1 (Extraction):** Feed an article to Prompt 1: *"Extract all names mentioned in this text."*
3. **Node 2 (Formatting):** Take the output of Node 1, and feed it into Prompt 2: *"Format these names as a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> array."*
4. **Node 3 (Validation):** Take the output of Node 2, and feed it into Prompt 3: *"Check if this <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> is valid. If yes, output the <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>. If no, fix it."*
5. This is how production Agentic systems are built.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your enterprise relies on 50 complex prompts across 10 products. Every time OpenAI updates their model (e.g., from GPT-4 to GPT-4-Turbo), the models behave differently and your prompts randomly break. Design a prompt management and testing infrastructure."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Version Control for Prompts:** 
   - State that prompts are source code. You cannot hardcode them in Python strings. They must be stored in a Prompt Registry (like Langfuse or a Git repo) as versioned templates (e.g., `prompt_v1.0.txt`).
2. **The Golden Dataset (Evals):**
   - Explain that the only way to detect a broken prompt is with **Regression Testing**. 
   - You must curate a "Golden Dataset" of 100 historical inputs and their perfect expected outputs. 
3. **Automated <abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr> Pipeline:**
   - Propose an automated testing pipeline. When OpenAI releases a new model, the <abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr> pipeline automatically runs the 50 Prompts against the 100 Golden Dataset examples using the new model.
   - It uses an <abbr title="Large Language Model">LLM</abbr>-as-a-Judge to score the new outputs against the expected outputs. If the accuracy drops below $95\%$, the pipeline alerts the engineering team that the prompt must be re-engineered for the new model.

---
**Task for the end of the day:** Commit your code to Git. 

You have mastered the logic of Prompt Engineering. But parsing text like `split("Final Answer:")` is brittle and dangerous. 
Tomorrow, in **Day 89**, we learn the holy grail of modern <abbr title="Artificial Intelligence">AI</abbr>: **Structured Output and Function Calling**. We will force the <abbr title="Large Language Model">LLM</abbr> to output perfect <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> every single time!
