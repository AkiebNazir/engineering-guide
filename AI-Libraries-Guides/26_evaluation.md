# 26. LLM Evaluation & Testing (DeepEval, promptfoo)

Welcome to LLM Evaluation. In traditional software engineering, you write unit tests (`assert add(2, 2) == 4`). In Machine Learning, you test against a ground-truth label (e.g., accuracy = 95%).

But how do you test a generative LLM? If the model answers *"The capital of France is Paris"* and the ground truth is *"Paris is the capital of France"*, standard string matching fails. If the model starts hallucinating facts, how do you catch it before it hits production?

You need **LLM Evaluation Frameworks**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Evaluation Triad
To evaluate an LLM, you typically need three things:
1. **The Test Case:** A prompt and an expected behavior or context.
2. **The Metric:** What are you measuring? (e.g., Factual Consistency, Toxicity, Tone, Hallucination).
3. **The Judge:** An *even smarter* LLM (like GPT-4) programmed with a strict rubric to score the output of your smaller application model (like Llama-3-8B). This is known as **LLM-as-a-Judge**.

### 2. DeepEval (The Pytest for LLMs)
DeepEval is an open-source framework that treats LLM evaluation just like traditional CI/CD unit testing. It provides pre-built metrics for things like:
- **Answer Relevancy:** Did the model actually answer the user's question, or did it ramble?
- **Faithfulness (Hallucination):** Did the model invent facts that were not present in the provided context?
- **Toxicity:** Is the output safe?

### 3. Promptfoo (The Prompt Engineering Sandbox)
Promptfoo is used earlier in the pipeline. It allows you to rapidly A/B test 5 different prompts against 10 different models (GPT-4 vs Claude vs Gemini) across 50 test cases, and outputs a beautiful matrix showing which prompt/model combination scored the highest.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's write a mock DeepEval test script to catch hallucination in a RAG (Retrieval-Augmented Generation) pipeline.

Create a file named `test_llm_hallucination.py`:

```python
# Note: You would normally run this via the CLI: `deepeval test run test_llm_hallucination.py`
from deepeval import assert_test
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric

def test_rag_hallucination():
    # 1. The Context (What the RAG system retrieved from the database)
    retrieved_context = [
        "The company's Q3 revenue was $1.5 billion.",
        "The CEO is Jane Doe."
    ]
    
    # 2. The User Prompt
    user_prompt = "Who is the CEO and what was the Q4 revenue?"
    
    # 3. The LLM's Output (Notice it hallucinates Q4 revenue!)
    actual_output = "The CEO is Jane Doe and the Q4 revenue was $2.0 billion."
    
    # 4. Create the Test Case
    test_case = LLMTestCase(
        input=user_prompt,
        actual_output=actual_output,
        retrieval_context=retrieved_context
    )
    
    # 5. Define the Metric
    # We want 100% faithfulness. The LLM MUST NOT say anything that isn't in the context.
    # Under the hood, this uses an LLM-as-a-Judge to evaluate the claim.
    faithfulness_metric = FaithfulnessMetric(threshold=1.0)
    
    # 6. Run the Test!
    # This will FAIL because Q4 revenue is not in the context.
    print("Evaluating LLM output against retrieved context...")
    
    try:
        assert_test(test_case, [faithfulness_metric])
        print("✅ TEST PASSED: The LLM did not hallucinate.")
    except AssertionError as e:
        print("❌ TEST FAILED: Hallucination Detected!")
        print(e)

if __name__ == "__main__":
    test_rag_hallucination()
```

### Key Takeaways from Code:
1. **The Context is King:** The `FaithfulnessMetric` does not care if the LLM is factually correct about the real world. It only checks if the LLM's output is perfectly supported by the `retrieval_context`. If it's not in the context, it's a hallucination.
2. **CI/CD Integration:** Because this runs like `pytest`, you can put this in a GitHub Action. If someone changes the system prompt and it suddenly causes the model to start hallucinating, the PR will fail!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Tone and Bias Evaluation
Faithfulness is objective, but Tone is subjective.
**Your Task:**
1. Research how to create a custom LLM-as-a-Judge metric.
2. Write a rubric (a multi-paragraph instruction) that tells GPT-4 how to grade a response from 1 to 5 based on how "Passive Aggressive" it is.
3. Test it against the output: *"Well, if you had bothered to read the manual, you would know the answer."*

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"We are deploying a customer service chatbot. How do you prove to the stakeholders that the bot won't give dangerous or hallucinated advice before we deploy it to 1 million users?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:
1. **Golden Datasets:** Propose building a "Golden Dataset" of 1,000 highly diverse, historically difficult customer interactions.
2. **Automated Evaluation Pipelines:** Explain using a framework like DeepEval or Ragas to run the new model against the Golden Dataset on every commit, measuring Answer Relevancy, Factual Consistency, and Toxicity.
3. **The LLM-as-a-Judge Fallacy:** Acknowledge that LLM judges have biases (they prefer longer answers, and they prefer answers that agree with their own biases). Propose mitigating this by using diverse judges (claude-3-opus vs gpt-4) and swapping the order of options.

---
**Task for the end of the day:** Commit your code to Git. 
