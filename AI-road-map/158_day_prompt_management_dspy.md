# Day 158: Prompt Management & DSPy (Automated Prompt Optimization)

Welcome to Day 158.

When you are hacking on a weekend project, you write your prompt directly inside your `app.py` file. 
If you do this in an enterprise, you will cause a production outage.

What happens when OpenAI releases GPT-4o-mini? You swap the <abbr title="Application Programming Interface">API</abbr> endpoint. But suddenly, your carefully crafted prompt (which worked perfectly for GPT-4) causes the new model to hallucinate. 
If your prompt is hardcoded in the backend, you have to push a code change, rebuild the <abbr title="A set of platform as a service products that use OS-level virtualization to deliver software in packages called containers.">Docker</abbr> container, and redeploy the entire application just to change a sentence!

Today, we learn **Production Prompt Management** and **Automated Prompt Optimization** using DSPy.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Prompt-as-Code vs Prompt Registries
In production, Prompts are treated as independent software artifacts.
- **Option A (Prompt-as-Code):** Prompts live in a dedicated `prompts/` folder in Git. They undergo Code Review and <abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr> testing.
- **Option B (Prompt Registry):** Prompts live in an external database (like LangSmith or a headless CMS). The backend fetches `system_prompt_v2.4` via an <abbr title="Application Programming Interface">API</abbr> call. If a prompt breaks in production, a non-technical Product Manager can log into a dashboard, fix the typo, and instantly push `v2.5` live without touching the backend code.

### 2. The A/B Testing Mandate
You should never guess if a prompt is "better." 
If you change a prompt, you must route 10% of your user traffic to `v2` (Canary Deployment) and compare the success metrics (e.g., "Did the user click 'Accept' on the generated code?") against `v1` before rolling it out to 100%.

### 3. The DSPy Revolution (Stanford)
Writing prompts manually is essentially "programming in English." It is fragile.
*Analogy:* When you write a PyTorch neural network, you don't manually calculate the weights for a billion parameters. You define an architecture, provide a dataset, and use an Optimizer (Gradient Descent) to calculate the weights automatically.

**DSPy (Declarative Self-Improving Language Programs)** applies this exact logic to Prompts.
Instead of manually tweaking a prompt, you:
1. Define an architecture (e.g., `ChainOfThought`).
2. Provide a tiny dataset (e.g., 20 examples of inputs and perfect outputs).
3. Provide a Metric (e.g., `Exact Match`).
4. Run the **DSPy Teleprompter (Optimizer)**. 

DSPy will use an <abbr title="Large Language Model">LLM</abbr> to automatically generate 50 different prompt variations, test them all against your dataset, find the one that gets the highest score, and "compile" it into a highly optimized, bizarre-looking prompt that outperforms anything a human could write.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's look at how DSPy completely eliminates the need to write prompts manually.

*(Note: To run this, you would need `pip install dspy-ai`)*

```python
import dspy
from dspy.evaluate import Evaluate
from dspy.teleprompt import BootstrapFewShot

# --- 1. CONFIGURE THE LLM ---
# We configure DSPy to use a local or API model
turbo = dspy.OpenAI(model='gpt-3.5-turbo')
dspy.settings.configure(lm=turbo)

# --- 2. DEFINE THE DATASET ---
# We provide a few examples of exactly what we want.
# Notice we DO NOT provide a massive instruction prompt!
dataset = [
    dspy.Example(question="What is the capital of France?", answer="Paris").with_inputs('question'),
    dspy.Example(question="Who wrote Romeo and Juliet?", answer="William Shakespeare").with_inputs('question'),
    dspy.Example(question="What is the chemical symbol for water?", answer="H2O").with_inputs('question'),
    dspy.Example(question="What is 5 + 5?", answer="10").with_inputs('question'),
    dspy.Example(question="Who is the CEO of Tesla?", answer="Elon Musk").with_inputs('question'),
]

trainset = dataset[:3]
devset = dataset[3:]

# --- 3. DEFINE THE ARCHITECTURE (THE MODULE) ---
# We define the input/output signature, just like typing a Python function.
class BasicQA(dspy.Signature):
    """Answer questions with short factoid answers."""
    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")

# We wrap the signature in a DSPy Predict module
class QAModule(dspy.Module):
    def __init__(self):
        super().__init__()
        # We wrap it in ChainOfThought to force the LLM to think before answering!
        self.generate_answer = dspy.ChainOfThought(BasicQA)

    def forward(self, question):
        return self.generate_answer(question=question)

# --- 4. THE METRIC ---
# How do we know if a prompt is good? 
def exact_match_metric(example, pred, trace=None):
    return dspy.evaluate.answer_exact_match(example, pred)

# --- 5. THE OPTIMIZER (THE MAGIC) ---
def run_dspy_optimization():
    print("[SYSTEM] Starting DSPy Compilation (Prompt Optimization)...")
    
    # We use BootstrapFewShot. It will take our small dataset, use an LLM to generate 
    # dynamic reasoning chains for them, and compile an ultra-optimized few-shot prompt.
    optimizer = BootstrapFewShot(
        metric=exact_match_metric,
        max_bootstrapped_demos=2,
        max_labeled_demos=2
    )

    # Compile! (This takes a minute. DSPy is actively testing prompts against the LLM!)
    compiled_qa = optimizer.compile(QAModule(), trainset=trainset)
    
    print("\n[SYSTEM] Compilation Complete! Testing the optimized model...")
    
    # --- 6. EXECUTION ---
    response = compiled_qa(question="What planet is known as the Red Planet?")
    print(f"Prediction: {response.answer}")
    
    # Let's look at the bizarre, highly-optimized prompt DSPy generated under the hood!
    print("\n--- THE OPTIMIZED PROMPT DSPY WROTE ---")
    turbo.inspect_history(n=1)

# To run:
# run_dspy_optimization()
```

### 🔍 Understanding the Magic
If you run this and inspect the history, you will see a massive prompt filled with dynamic few-shot examples and reasoning chains that you *never wrote*. 
If you swap `gpt-3.5` for `Llama-3`, the old prompt might break. With DSPy, you just change the model string, hit "Compile" again, and DSPy will automatically calculate a completely new prompt perfectly tuned for Llama-3's internal quirks!

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Currently, our DSPy metric uses `exact_match`. This means if the <abbr title="Large Language Model">LLM</abbr> outputs "Paris." instead of "Paris", it scores a 0/100, which is too strict.
**Your Task:** Write a custom DSPy metric function. Instead of string matching, it should use a secondary <abbr title="Large Language Model">LLM</abbr> (an "<abbr title="Large Language Model">LLM</abbr>-as-a-Judge") to read the prediction and the ground truth, and return a True/False if they are semantically equivalent. Pass this new metric to the `BootstrapFewShot` optimizer.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Your company has 200 prompts hardcoded across 30 different products. You just upgraded your entire cluster to a new open-source model. 30% of your products immediately broke because the new model doesn't understand the old prompts. Design the infrastructure to prevent this from ever happening again."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Decoupling:** Immediately strip all hardcoded prompts from the application code. Move them to a centralized **Prompt Registry** (like LangSmith or a managed Git repo).
2. **Evaluation Datasets:** For every single prompt in the company, there must be a Golden Dataset (e.g., 50 inputs and perfect outputs).
3. **<abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr> for Prompts:** Before upgrading the central model, trigger a <abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr> pipeline. The pipeline runs all 200 prompts against their Golden Datasets using the new model. It generates a massive regression report showing exactly which prompts degraded.
4. **Automated Remediation:** For the prompts that failed, run them through a **DSPy Optimizer pipeline**. Pass the Golden Dataset to DSPy and let it automatically re-compile the prompt for the new model until it passes the <abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr> threshold.

---
**Task for the end of the day:** Skim the official DSPy documentation. It represents a paradigm shift from "Prompt Engineering" to "Prompt Programming".

Tomorrow, in **Day 159**, we tackle **Evaluation in Production**. How do you know if your <abbr title="Large Language Model">LLM</abbr> is failing when you have 100,000 real users? We will learn <abbr title="Large Language Model">LLM</abbr>-as-a-Judge, Prometheus, and Grafana!
