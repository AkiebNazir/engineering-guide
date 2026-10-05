# Ragas Mastery: Evaluating RAG Applications

## 1. The Core Concept (What and Why)

*Why is this tool relevant?* In Guide 11 (LangChain) and Guide 12 (LlamaIndex), we built RAG (Retrieval-Augmented Generation) applications. But how do you know if your RAG app is actually good? Traditionally, a developer would type 10 questions, read the 10 answers, and say, "Looks fine to me." This doesn't scale to production. If you change your `chunk_size` from 500 to 1000, did the app get better or worse? You need numbers. **Ragas** provides those numbers.

**What is it?**
Ragas (Retrieval Augmented Generation Assessment) is a framework that mathematically evaluates your RAG pipelines.

**Why does it exist?**
It exists to implement the **"LLM-as-a-Judge"** architecture. Instead of humans reading the outputs, Ragas uses a highly intelligent LLM (like GPT-4) to read the user's question, the retrieved documents, and the generated answer, and grade them from `0.0` to `1.0` based on strict logical metrics.

---

## 2. Setup & Installation

```bash
pip install ragas langchain-openai datasets
```

```python
import ragas

print(f"Ragas version: {ragas.__version__}")
```

---

## 3. The "Hello World": Evaluating a RAG Pipeline

To evaluate a RAG pipeline, you must provide a Dataset containing 4 specific columns of data:
1. `question`: The prompt the user asked.
2. `answer`: The text your RAG system generated.
3. `contexts`: A list of the raw text chunks your Vector DB retrieved.
4. `ground_truth`: The scientifically correct answer (written by a human beforehand).

```python
import os
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy

os.environ["OPENAI_API_KEY"] = "your-api-key"

# 1. Provide the data from your RAG pipeline
data = {
    "question": ["What is the capital of France?"],
    "answer": ["The capital of France is Paris."],
    "contexts": [["France is a country in Europe. Paris is its capital city."]],
    "ground_truth": ["Paris is the capital of France."]
}

# Convert to a Hugging Face Dataset
dataset = Dataset.from_dict(data)

# 2. Run the Evaluation!
# Ragas will call GPT-4 under the hood to act as a judge and score these metrics.
results = evaluate(
    dataset=dataset,
    metrics=[faithfulness, answer_relevancy]
)

print(results)
# Output: {'faithfulness': 1.0000, 'answer_relevancy': 0.9854}
```

---

## 4. Deep Dive: The 4 Core Metrics

Ragas is built upon 4 highly specific metrics. You must memorize these, as they isolate exactly *which* part of your RAG pipeline is failing.

### A. Metrics that evaluate the GENERATOR (The LLM)

1. **Faithfulness (`faithfulness`)**
   - *What it measures:* Did the LLM hallucinate? It checks if every claim made in the `answer` can be explicitly verified by the `contexts`.
   - *If this scores 0.2:* Your Vector DB successfully found the correct document, but your LLM ignored the document and made up a fake answer anyway.
   - *How to fix:* Lower the `temperature` (Guide 08) or strictly prompt the LLM: "Do not use prior knowledge."

2. **Answer Relevancy (`answer_relevancy`)**
   - *What it measures:* Did the LLM actually answer the user's question? 
   - *If this scores 0.2:* The user asked "How do I reset my password?", and your LLM answered, "We take security very seriously at our company. Here is a history of our security policies." It didn't hallucinate, but it was useless.
   - *How to fix:* Improve your Prompt Template (Guide 11) to force direct answers.

### B. Metrics that evaluate the RETRIEVER (The Vector Database)

3. **Context Precision (`context_precision`)**
   - *What it measures:* Did the Vector DB put the most relevant chunk at the very top of the list?
   - *If this scores 0.2:* Your DB retrieved 10 chunks. The correct answer was buried at chunk #9, where the LLM likely ignored it due to the "Lost in the Middle" effect.
   - *How to fix:* Implement a Re-Ranker (like Cohere) to mathematically re-sort the retrieved chunks before they hit the LLM.

4. **Context Recall (`context_recall`)**
   - *What it measures:* Did the retrieved chunks contain all the information necessary to answer the `ground_truth`?
   - *If this scores 0.2:* The Vector DB retrieved the wrong documents entirely. The LLM had no chance of answering correctly.
   - *How to fix:* Your embeddings are bad, or your `chunk_size` is too small (Guide 12). Switch to a better embedding model or increase the chunk size.

---

## 5. Pro Level: Synthetic Test Data Generation

The biggest bottleneck in Ragas is that you need a Human to write 100 `ground_truth` answers to create the test set. 
Ragas provides a massive superpower: **Synthetic Data Generation**. You hand it your raw PDFs, and it will use GPT-4 to automatically generate hundreds of difficult questions and correct answers based on the text.

```python
from ragas.testset.generator import TestsetGenerator
from ragas.testset.evolutions import simple, reasoning, multi_context
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader

# 1. Load your raw company PDF
loader = PyPDFLoader("./company_handbook.pdf")
documents = loader.load()

# 2. Setup the AI generators
generator_llm = ChatOpenAI(model="gpt-4o")
critic_llm = ChatOpenAI(model="gpt-4")
embeddings = OpenAIEmbeddings()

generator = TestsetGenerator.from_langchain(
    generator_llm,
    critic_llm,
    embeddings
)

# 3. Generate the Test Set!
# It will generate 50 questions.
# Some will be simple fact-retrieval.
# Some will require 'reasoning' (synthesizing two different pages).
testset = generator.generate_with_langchain_docs(
    documents, 
    test_size=50, 
    distributions={simple: 0.5, reasoning: 0.25, multi_context: 0.25}
)

# You now have 50 questions, contexts, and ground_truths ready to use in `evaluate()`!
print(testset.to_pandas().head())
```

---

## 6. MAANG Interview Scenarios

### Scenario 1: CI/CD Integration for RAG
*Interviewer:* "A developer on your team submitted a Pull Request that changes our LlamaIndex `chunk_size` from 512 to 2048. They claim it 'feels better.' How do we prevent this from being merged to production without mathematical proof?"

*Answer:* "We must integrate Ragas into our CI/CD pipeline (e.g., GitHub Actions). We maintain a golden dataset of 500 `question` and `ground_truth` pairs. When the developer opens the Pull Request, the CI runner automatically spins up the new LlamaIndex code with `chunk_size=2048`. It runs all 500 questions through the pipeline, collects the answers and contexts, and calls `ragas.evaluate()`. The CI pipeline asserts that `context_recall` and `faithfulness` must be greater than our baseline production scores (e.g., `> 0.85`). If the scores drop to `0.70`, the pipeline automatically blocks the PR and fails the build."

### Scenario 2: The LLM-as-a-Judge Bias
*Interviewer:* "Ragas relies on GPT-4 to act as the judge. What are the known biases of using an LLM as a judge, and how do we mitigate them?"

*Answer:* "LLMs exhibit three major biases when acting as judges:
1. **Position Bias:** If you ask it to compare Answer A and Answer B, it statistically favors Answer A simply because it appeared first. Ragas mitigates this by randomly swapping the order of answers internally.
2. **Verbosity Bias:** LLMs heavily favor long, wordy answers, even if they contain less factual information than a short, concise answer.
3. **Self-Enhancement Bias:** GPT-4 prefers answers generated by GPT-4 over answers generated by Claude or Llama. 
To mitigate these, we must ensure our grading prompts are highly deterministic (like DSPy signatures), explicitly asking the judge to break down the answer step-by-step and grade strictly on factual extraction rather than prose or length."
