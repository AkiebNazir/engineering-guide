# Day 132: Reflection & Self-Critique Agents (Reflexion)

Welcome to Day 132. 

If you ask a human to write a complex Python script, they rarely get it perfect on the first try. They write a draft, read it, realize there is a bug, and rewrite it. 
Historically, we treated LLMs like slot machines: pull the lever once and hope the output is good. 

Today, we teach LLMs to act like humans. We learn **Reflexion**, a powerful architectural pattern where the Agent critiques its own work *before* showing it to the user.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Reflexion Pattern
Reflexion (with an 'x') is a famous AI paper that introduces a strict feedback loop:
1. **Attempt:** The Generator Agent attempts the task (e.g., writes a Python function).
2. **Evaluate:** The output is tested. This could be an automated Unit Test (did the code compile?) or an Evaluator Agent (does this essay have 3 metaphors?).
3. **Reflect:** If the evaluation fails, the Generator Agent is forced to write a "Verbal Reflection". It must explicitly write down *why* it failed (e.g., *"I failed because I used a `while` loop instead of a `for` loop."*).
4. **Retry:** The Agent tries again, but this time, its previous Verbal Reflection is injected into the prompt so it doesn't make the same mistake twice!

### 2. LATS (Language Agent Tree Search)
Standard Reflexion is linear. You try, fail, and try again.
**LATS** combines Reflexion with Tree-of-Thought (Day 115). 
The Generator creates 3 *different* drafts. The Evaluator critiques all 3 and scores them. The worst draft is immediately deleted. The Agent branches off the 2 best drafts and refines them. It is the ultimate search algorithm for text!

### 3. Generator-Critic Architecture
This is an adversarial setup used heavily in coding agents. 
- The **Generator** is an LLM trying to write code.
- The **Critic** is not an LLM. It is a literal Python compiler or `pytest` sandbox.
The Generator writes code. The Critic runs it, captures the giant red Traceback Error, and feeds it back to the Generator. They fight until the tests pass!

### 4. Adaptive Reflection
Reflection is magic; it increases coding accuracy from $40\%$ to $80\%$. 
But it multiplies token costs and latency by $4\times$ because the LLM is looping 4 times! 
**Adaptive Reflection** uses a fast Router to predict if reflection is needed. If the user asks *"What is 2+2?"*, the router skips reflection. If the user asks *"Write a React hook for websockets"*, the router enables the Reflexion loop.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual Reflexion loop. We will build a Writing Agent that is forced to critique its own drafts against a strict rubric before returning the final text!

Create a file named `reflexion_agent.py`:

```python
def mock_generator_agent(prompt, previous_reflection=""):
    """Generates the content."""
    print(f"\n[GENERATOR] Writing draft...")
    if previous_reflection:
        print(f"[GENERATOR] (Applying previous reflection: {previous_reflection})")
        
    # First attempt: A bad draft
    if not previous_reflection:
        return "The dog ran fast. He was a good boy."
        
    # Second attempt: A better draft based on the critique!
    return "The golden retriever bolted across the emerald lawn like a furry missile. He was a very good boy."

def mock_evaluator_agent(draft):
    """Critiques the content against a rubric."""
    print(f"[EVALUATOR] Critiquing draft: '{draft}'")
    
    rubric_passed = False
    critique = ""
    
    if "like a" not in draft:
        critique = "The draft is too simple. It failed the rubric because it does not contain a simile or metaphor."
        print(f"[EVALUATOR] Result: FAILED. Critique: {critique}")
    else:
        rubric_passed = True
        print("[EVALUATOR] Result: PASSED! The draft contains a simile.")
        
    return rubric_passed, critique

def run_reflexion_loop():
    print("--- RUNNING REFLEXION AGENT LOOP ---\n")
    
    user_prompt = "Write a 2-sentence story about a dog. Must include a simile."
    print(f"User Request: {user_prompt}")
    
    max_retries = 3
    current_reflection = ""
    
    for attempt in range(max_retries):
        print(f"\n--- ATTEMPT {attempt + 1} ---")
        
        # 1. Generator attempts the task
        draft = mock_generator_agent(user_prompt, current_reflection)
        print(f"[DRAFT] {draft}")
        
        # 2. Evaluator scores the draft
        passed, critique = mock_evaluator_agent(draft)
        
        # 3. Decision Gate
        if passed:
            print(f"\n[SUCCESS] Final Approved Output:\n{draft}")
            break
        else:
            # 4. Verbal Reflection (In reality, the LLM generates this based on the critique)
            current_reflection = f"I failed because I forgot to include a simile. Next time, I will use the word 'like' or 'as'."
            
    if not passed:
        print("\n[FAILED] Agent exhausted all retries and could not pass the rubric.")

if __name__ == "__main__":
    run_reflexion_loop()
```

### Key Takeaways from Code:
1. **The Verbal Reflection:** The key to Reflexion is not just telling the LLM "You failed." You must force the LLM to explicitly articulate *why* it failed in the `current_reflection` variable. This focuses the LLM's attention mechanism on the exact mistake for the next forward pass.
2. **Quality Assurance (QA):** This architecture guarantees a baseline level of quality. The user never sees the first, lazy draft. They only see the polished, rubric-approved final draft.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Generator-Critic Coder
You can combine Reflexion with raw Python execution to create a self-healing coding agent.
**Your Task:**
1. Conceptually define a `coder_node` that takes a prompt and outputs raw python code.
2. Define an `executor_node` that uses Python's `exec()` command to run the code. Wrap it in a `try/except` block.
3. If it throws an exception, capture the `traceback` error string.
4. Route back to the `coder_node`, injecting the traceback into the prompt: *"Your code failed with this error: {traceback}. Fix it."*

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Reflection agents significantly improve output quality but multiply latency and token costs by 3-5x. Design a system that uses reflection only when needed (Adaptive Reflection). How do you predict when reflection will be beneficial?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Adaptive Router:** 
   - Propose placing a fast, cheap router model (or a semantic classifier) in front of the Reflection loop.
2. **Prediction Heuristics (When to Reflect):**
   - **Task Complexity:** If the prompt length is short or requires simple factual retrieval (*"Who is the CEO of Apple?"*), route to standard execution. If the prompt requires synthesis (*"Write an essay"*), route to Reflection.
   - **Logprob Uncertainty:** Extract the Token Probabilities (`logprobs`) from the LLM's first generation. If the LLM generates the answer with $99\%$ confidence, skip reflection. If the LLM's confidence is hovering around $50\%$, it is uncertain and should be routed into a Reflection loop to double-check its work!
3. **The Budget Cap:**
   - Mention that you must enforce a strict `max_reflection_loops=3` budget constraint to prevent the agent from getting stuck in an infinite perfectionism loop.

---
**Task for the end of the day:** Commit your code to Git. 

We now have agents that can critique themselves. But what happens when we have multiple *different* agents critiquing each other? 

Tomorrow, in **Day 133**, we learn **Multi-Agent Debate and Consensus**. We will force agents to argue with each other until they find the truth!
