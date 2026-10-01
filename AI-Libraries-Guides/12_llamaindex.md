# LlamaIndex Mastery: The Enterprise RAG Standard

## 1. The Core Concept (What and Why)

*Why is this tool relevant?* In 2023, naive RAG (Retrieval-Augmented Generation) meant chunking a PDF, putting it in a database, and doing a simple similarity search. Today, naive RAG fails in production. If a user asks, "Compare the Q3 revenue of Apple and Microsoft," naive RAG retrieves random paragraphs with the word "revenue." **LlamaIndex** is the modern, state-of-the-art framework that solves this. It replaces older, simplistic vector scripts with advanced routing, sub-queries, and knowledge graphs.

**What is it?**
LlamaIndex is a data framework specifically designed to connect custom data sources (PDFs, SQL, Notion, Slack) to LLMs. While LangChain is great for general logic and memory, LlamaIndex is the undisputed king of Data Ingestion and RAG.

---

## 2. Setup & Installation

```bash
pip install llama-index llama-index-llms-openai
```

```python
import llama_index.core

print(f"LlamaIndex version: {llama_index.core.__version__}")
```

---

## 3. The "Hello World": 5-Line RAG

If you want to build a baseline RAG system over a folder of PDFs, LlamaIndex makes it incredibly simple.

```python
import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader

os.environ["OPENAI_API_KEY"] = "your-api-key"

# 1. Load all PDFs, Word docs, and text files from a folder
documents = SimpleDirectoryReader("./data").load_data()

# 2. Chunk the text, embed it, and store it in an in-memory vector database
index = VectorStoreIndex.from_documents(documents)

# 3. Create a query engine (The pipeline that talks to the LLM)
query_engine = index.as_query_engine()

# 4. Ask a question!
response = query_engine.query("What are the main policies mentioned in the employee handbook?")
print(response)
```

---

## 4. Deep Dive: The Node Parser and Retrievers

Under the hood, a "Document" is too large for an LLM. It must be parsed into "Nodes" (chunks of text). 

### Parameter Breakdown: `SentenceSplitter`
- `chunk_size` (int): Usually set to `1024` or `512`.
  - *Effect of increasing (e.g., 4096):* The LLM receives massive blocks of text. It gets great context but might suffer from the "Lost in the Middle" syndrome. Vector searches become less precise.
  - *Effect of decreasing (e.g., 128):* Vector searches become highly accurate (keyword matching is easy in small text), but the LLM receives fractured, broken sentences and cannot synthesize a good answer.
- `chunk_overlap` (int): Usually `20` to `50`.
  - *Effect:* Prevents a critical sentence from being mathematically split in half by forcing the end of Node A to repeat at the beginning of Node B.

```python
from llama_index.core.node_parser import SentenceSplitter

# Customize the exact size of your chunks
parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
nodes = parser.get_nodes_from_documents(documents)
```

### Parameter Breakdown: `index.as_query_engine(...)`
- `similarity_top_k` (int): Default is usually `2`.
  - *Effect:* This dictates exactly how many chunks of text are pulled from the database and injected into the LLM prompt. If you set it to `10`, the LLM has much more data to read, but your API costs will skyrocket, and the prompt might exceed the context limit. `3` to `5` is the enterprise sweet spot.

```python
query_engine = index.as_query_engine(similarity_top_k=5)
```

---

## 5. Pro Level: Advanced RAG (SubQuestionQueryEngine)

This is why LlamaIndex is the enterprise standard. 
If a user asks: *"Compare the weather in New York and Tokyo."*
A standard vector database will search for "weather New York Tokyo" and likely fail to find a single paragraph containing all three terms.

LlamaIndex's `SubQuestionQueryEngine` uses an LLM to actively rewrite the user's question into multiple sub-questions, executes them independently, and synthesizes the final answer!

```python
from llama_index.core.tools import QueryEngineTool, ToolMetadata
from llama_index.core.query_engine import SubQuestionQueryEngine

# Imagine we have two separate indexes: one for NY, one for Tokyo
ny_tool = QueryEngineTool(
    query_engine=ny_index.as_query_engine(),
    metadata=ToolMetadata(name="ny_weather", description="Weather data for New York")
)

tokyo_tool = QueryEngineTool(
    query_engine=tokyo_index.as_query_engine(),
    metadata=ToolMetadata(name="tokyo_weather", description="Weather data for Tokyo")
)

# The SubQuestion Engine!
query_engine = SubQuestionQueryEngine.from_defaults(
    query_engine_tools=[ny_tool, tokyo_tool]
)

# When you run this, LlamaIndex will automatically print:
# > Sub query: What is the weather in New York? (Sent to ny_weather)
# > Sub query: What is the weather in Tokyo? (Sent to tokyo_weather)
# > Synthesizing final answer...
response = query_engine.query("Compare the weather in New York and Tokyo.")
```

---

## 6. MAANG Interview Scenarios

### Scenario 1: The "Small-to-Big" Retrieval Strategy
*Interviewer:* "When `chunk_size` is small (128), retrieval accuracy is high, but LLM generation is poor due to lack of context. When `chunk_size` is large (1024), generation is great, but retrieval accuracy drops. How do you solve this paradox in production?"

*Answer:* "I would use LlamaIndex's **Auto-Merging Retriever (Parent-Child Index)**. During ingestion, I chunk the document into massive 'Parent' nodes (1024 tokens). Then, I split each Parent into smaller 'Child' nodes (128 tokens). 
I embed and search *only* against the small Child nodes, guaranteeing highly precise retrieval accuracy. However, before sending the data to the LLM, LlamaIndex intercepts the request, looks up the Child's original Parent node, and sends the massive Parent node to the LLM. We get the mathematical precision of small chunks and the narrative context of massive chunks."

### Scenario 2: Hallucinations on missing data
*Interviewer:* "If the answer to the user's question does not exist in our database, the LLM hallucinates an answer anyway. How do we stop this?"

*Answer:* "We must alter the `PromptTemplate` inside the LlamaIndex Query Engine. By default, the LLM is told to answer the question using the context. We must explicitly append a strict instruction: *'If the context does not contain the answer, you must output exactly: [I do not have enough information to answer this]. Do not attempt to guess.'* Furthermore, we can use a post-processing evaluator to measure the semantic similarity between the LLM's final output and the retrieved context chunks to mathematically detect if it hallucinated."
