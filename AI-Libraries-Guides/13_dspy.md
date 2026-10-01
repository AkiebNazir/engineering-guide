# DSPy Mastery: The End of Prompt Engineering

## 1. The Core Concept (What and Why)

*Why is this tool relevant?* For the past 2 years, engineers have spent countless hours "prompt engineering"—tweaking strings, begging the LLM to act a certain way, and manually typing out examples of good behavior (Few-Shot Prompting). If they switched from GPT-4 to Llama-3, the prompt broke, and they had to rewrite it manually. **DSPy** is the framework that kills manual prompt engineering forever.

**What is it?**
DSPy (Declarative Self-Improving Language Programs) is a framework developed by Stanford. It shifts LLM development from "prompt tweaking" to **Programming and Compiling**. 

**Why does it exist?**
You don't write prompts in DSPy. You write a program (like a PyTorch neural network) that defines the *inputs* and *outputs* you want. Then, you write a *Metric* (a Python function that grades how good an answer is). 
Finally, you run the DSPy **Compiler**. The compiler automatically calls the LLM thousands of times, tests different prompt variations, generates its own perfect Few-Shot examples, and mathematically optimizes the prompt to achieve the highest score on your Metric.

If you switch models tomorrow, you just hit "Compile" again, and DSPy writes the perfect prompt for the new model automatically!

---

## 2. Setup & Installation

```bash
pip install dspy-ai
```

```python
import dspy

print(f"DSPy version: {dspy.__version__}")
```

---

## 3. The "Hello World": Signatures and Modules

In LangChain, you write string templates. In DSPy, you write **Signatures**. A signature is a short, declarative string that defines exactly what data goes in and what data comes out.

### A. The Signature
```python
import dspy

# Configure the LLM we want to use globally
lm = dspy.OpenAI(model='gpt-3.5-turbo', max_tokens=250)
dspy.settings.configure(lm=lm)

# 1. Define the Signature!
# "question -> answer" tells DSPy exactly what we want. We didn't write a prompt!
qa = dspy.Predict('question -> answer')

# 2. Run it
response = qa(question="What is the capital of France?")
print(response.answer) # "Paris"
```

### B. The Module (Building Complex Pipelines)
Just like `torch.nn.Module` in PyTorch, you can chain multiple DSPy modules together to build complex reasoning engines. Let's build a module that uses "Chain of Thought" reasoning before answering.

```python
class CoT_QA(dspy.Module):
    def __init__(self):
        super().__init__()
        # Instead of dspy.Predict, we use dspy.ChainOfThought.
        # This automatically forces the LLM to write out its reasoning step-by-step 
        # before generating the final answer.
        self.prog = dspy.ChainOfThought('question -> answer')
        
    def forward(self, question):
        return self.prog(question=question)

# Run it!
cot = CoT_QA()
response = cot(question="If I have 3 apples and eat 1, how many are left?")

print(f"Reasoning: {response.rationale}")
print(f"Answer: {response.answer}")
```

---

## 4. Deep Dive: Teleprompters (The Compiler)

This is the magic of DSPy. We want to optimize our `CoT_QA` module.

To compile a DSPy program, you need three things:
1. **A Training Set:** A tiny dataset of examples (e.g., 20 questions and answers).
2. **A Metric:** A Python function that returns `True` or `False` (or a score from 0.0 to 1.0) grading if the LLM's output is correct.
3. **A Teleprompter:** The DSPy optimization algorithm.

### Parameter Breakdown: `BootstrapFewShot`
- `metric` (function): The grading function.
  - *Effect:* The compiler will literally throw away prompts that score low on this metric and keep prompts that score high.
- `max_bootstrapped_demos` (int): 
  - *Effect:* If set to `3`, the compiler will automatically generate 3 perfect examples of the LLM "showing its work" and inject them into the final prompt as Few-Shot examples. This drastically improves LLM reliability.

```python
from dspy.teleprompt import BootstrapFewShot

# 1. Create a tiny training set
trainset = [
    dspy.Example(question="What is 2+2?", answer="4").with_inputs('question'),
    dspy.Example(question="What is the capital of Japan?", answer="Tokyo").with_inputs('question'),
]

# 2. Define the Metric (How do we know if the LLM did a good job?)
# Here, we do a simple exact match check.
def exact_match_metric(example, pred, trace=None):
    return example.answer.lower() in pred.answer.lower()

# 3. Setup the Optimizer (Teleprompter)
teleprompter = BootstrapFewShot(
    metric=exact_match_metric, 
    max_bootstrapped_demos=2
)

# 4. COMPILE! 
# DSPy will now run the un-optimized model, test it, generate synthetic 
# examples of good behavior, and output a highly optimized, compiled module!
compiled_cot = teleprompter.compile(CoT_QA(), trainset=trainset)

# 5. Use the highly-optimized model in production
result = compiled_cot(question="What is the capital of Germany?")
```

If you ever print out the internal prompt of `compiled_cot`, you will see a massive, highly-structured prompt containing perfectly formatted examples of Chain-of-Thought reasoning that DSPy wrote for you automatically!

---

## 5. MAANG Interview Scenarios

### Scenario 1: Model Migration
*Interviewer:* "We spent 6 months manually prompt engineering GPT-4 to behave perfectly for our customer service bot. Management just told us we have to switch to open-source Llama-3 tomorrow to save money. When we swapped the API key, the bot completely broke because Llama-3 responds differently to our manual prompts. How does DSPy solve this?"

*Answer:* "In a traditional pipeline, manual prompt engineering creates extreme vendor lock-in. Because prompts are brittle, they break when the underlying neural network changes. If we had built the pipeline in DSPy, the prompt strings wouldn't be hardcoded. We would simply change the global `dspy.settings.configure(lm=llama3)` and run the DSPy Compiler again. DSPy would automatically generate brand new, mathematically optimized prompts and Few-Shot examples tailored specifically to Llama-3's unique architecture, completing the migration in minutes instead of months."

### Scenario 2: The Hallucination Metric
*Interviewer:* "Your DSPy metric currently checks if the `example.answer` is inside the `pred.answer`. This is too simplistic for complex text generation. How can we use DSPy to optimize against hallucinations?"

*Answer:* "We can write an **LLM-as-a-Judge Metric**. Instead of a simple Python string-match, the `metric` function itself can call a separate, highly intelligent LLM (like GPT-4). We pass the prompt, the context, and the output to GPT-4, and ask it to return a boolean `True` if there are no hallucinations, and `False` if there are. 
We then pass this LLM-as-a-Judge metric into our DSPy `BootstrapFewShot` teleprompter. Now, DSPy will literally optimize our primary model's prompts by actively trying to maximize the approval score from the GPT-4 judge!"

---

## 6. Common Pitfalls & Debugging in Production

### ⚠️ Pitfall 1: Leaking `with_inputs()`
When defining your training set using `dspy.Example`, if you forget to append `.with_inputs('question')`, the compiler will assume the `answer` is also an input. It will feed the answer to the LLM during testing, achieving a fake 100% score, and the compilation will fail to optimize anything.
*Fix:* Always explicitly declare which fields in your Example are inputs vs labels.

### ⚠️ Pitfall 2: Too small of a trainset for advanced Teleprompters
`BootstrapFewShot` works fine with 5 examples. But if you try to use DSPy's advanced, deep-learning based optimizers like `MIPRO` (which optimizes both the instructions and the examples simultaneously), you will crash if you provide fewer than ~300 examples.
*Fix:* Match your teleprompter to your data size. Small data = `BootstrapFewShot`. Massive data = `MIPRO`.
