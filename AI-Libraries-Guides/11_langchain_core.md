# LangChain Core Mastery: Orchestrating LLM Applications

## 1. The Core Concept (What and Why)

*Assuming you know absolutely nothing about this library, let's start from zero.*

**What is it?**
LangChain is a framework for developing applications powered by Language Models. It provides the "glue" to connect an LLM to the outside world.

**Why does it exist?**
An LLM (like GPT-4 or Llama-3) is fundamentally just a text-prediction engine trapped in a box. 
- It has **no memory** (if you ask it a question, it forgets it 2 seconds later).
- It has **no internet access** (it only knows facts up until its training cut-off date).
- It cannot **take actions** (it cannot run Python code, query an SQL database, or send an email).

LangChain provides standardized abstractions (Prompts, Memory, Document Loaders, and Output Parsers) to solve all these problems. It allows you to build a system where the LLM can read your private PDF documents, remember past conversations, and format its output perfectly as JSON.

---

## 2. Setup & Installation

LangChain is split into modular packages so you don't have to download the entire internet.

```bash
# Install the core library, the community integrations, and the OpenAI wrapper
pip install langchain langchain-core langchain-community langchain-openai
```

```python
import langchain_core

print(f"LangChain Core version: {langchain_core.__version__}")
```

---

## 3. The "Hello World": LCEL (LangChain Expression Language)

Historically, LangChain used a complex, buggy class called `LLMChain`. In modern LangChain (v0.1+), everything uses **LCEL**. LCEL heavily uses the Python pipe operator (`|`) to chain components together, exactly like Unix bash pipelines.

### Parameter Breakdown: `ChatOpenAI(...)`
- `temperature` (float): Default is usually `0.7`.
  - *Effect:* `0.0` is completely deterministic (best for coding/data extraction). `1.0` is highly creative (best for brainstorming).
- `model` (str): e.g., `"gpt-4o"`, `"gpt-3.5-turbo"`.
  - *Effect:* Dictates the intelligence, speed, and cost of the API call.

```python
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

os.environ["OPENAI_API_KEY"] = "your-api-key"

# 1. Define the Model
model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0)

# 2. Define a Prompt Template
# Templates allow you to inject variables into a static prompt dynamically.
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert translator. Translate the text to {language}."),
    ("user", "{text}")
])

# 3. Define the Output Parser
# LLMs output complex metadata dictionaries. This parser strips away the metadata 
# and returns just the raw string response.
parser = StrOutputParser()

# 4. LCEL Magic: Chain them together using the Pipe operator!
# Data flows from left to right: Prompt -> Model -> Parser
chain = prompt | model | parser

# 5. Execute the chain
result = chain.invoke({"language": "French", "text": "I love programming."})
print(result) # "J'adore la programmation."
```

---

## 4. Deep Dive: Memory Systems

Because LLMs are "stateless" APIs, every time you send a message, you must send the *entire history of the conversation* along with it, or it will forget what you said 5 seconds ago. LangChain automates this.

### A. `ConversationBufferMemory`
This simply appends every message to a running list and injects the entire list into the prompt.
- *The fatal flaw:* If the conversation goes on for 50 messages, the prompt becomes massive. You will hit the LLM's "Context Limit" and it will crash, or you will pay massive API fees because you are re-sending 10,000 tokens of history on every single chat message.

### B. `ConversationSummaryMemory`
The pro-level solution.
- *What it does:* Instead of storing the exact chat history, it uses a *second, smaller LLM* running in the background. Every time the user speaks, this background LLM reads the new message, reads the old summary, and rewrites a new, condensed summary of the entire conversation.
- *Effect:* Your token usage remains perfectly flat, no matter if the conversation lasts 10 messages or 10,000 messages. 

```python
from langchain.memory import ConversationSummaryMemory
from langchain_openai import OpenAI

# The background LLM whose only job is to compress text
summarizer_llm = OpenAI(temperature=0) 

memory = ConversationSummaryMemory(llm=summarizer_llm)

memory.save_context({"input": "Hi, my name is John and I have two dogs."}, {"output": "Hello John!"})
memory.save_context({"input": "What did I just tell you?"}, {"output": "You said your name is John and you have two dogs."})

print(memory.load_memory_variables({}))
# Output: {'history': 'The human introduces himself as John and mentions he has two dogs.'}
```

---

## 5. RAG (Retrieval-Augmented Generation)

If you want an LLM to answer questions about your company's private 500-page PDF manual, you cannot paste 500 pages into the prompt. The LLM will crash. 
You must use **RAG**.

RAG works in 4 steps:
1. **Load** the PDF.
2. **Split** it into small 500-word chunks.
3. **Embed** those chunks (convert the text into math vectors, as seen in Guide 01) and store them in a Vector Database.
4. **Retrieve** the 3 most relevant chunks when the user asks a question, and inject only those 3 chunks into the LLM prompt.

### Parameter Breakdown: `RecursiveCharacterTextSplitter`
- `chunk_size` (int): How many characters/tokens per chunk.
  - *Effect of increasing (e.g., 2000):* The LLM gets a lot of context, but the Vector Database struggles to find exact semantic matches because the chunk contains too many mixed topics.
  - *Effect of decreasing (e.g., 50):* The Vector DB will find highly precise keyword matches, but the LLM will fail to answer the question because the chunk is cut off mid-sentence and lacks surrounding context. `500` or `1000` is the standard sweet spot.
- `chunk_overlap` (int): How much the chunks should overlap.
  - *Effect of setting to 0:* If a critical sentence happens to cross the exact boundary between Chunk 1 and Chunk 2, the meaning is destroyed.
  - *Effect of setting to 200:* Chunk 2 will start by repeating the last 200 characters of Chunk 1. This guarantees that no sentences are lost during the split!

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

text = "Artificial Intelligence is fascinating. " * 100 # Simulate a long document

# Split the document, ensuring we don't slice words in half!
splitter = RecursiveCharacterTextSplitter(
    chunk_size=100, 
    chunk_overlap=20
)

chunks = splitter.split_text(text)
print(f"Split document into {len(chunks)} chunks.")
```

---

## 6. MAANG Interview Scenarios

### Scenario 1: The RAG "Lost in the Middle" Problem
*Interviewer:* "You built a RAG system. The Vector DB retrieves the top 20 most relevant chunks and pastes them into the LLM prompt. But the LLM keeps giving wrong answers, even though the correct answer is sitting right in Chunk #10. Why?"

*Answer:* "This is a well-documented phenomenon called the 'Lost in the Middle' effect. LLMs suffer from a U-shaped attention curve. They pay massive attention to the very beginning of the prompt and the very end of the prompt, but they 'gloss over' the middle. If I retrieve 20 chunks, Chunk #10 is completely ignored. 
To fix this, I would use LangChain's `LongContextReorder` document transformer. It takes the retrieved chunks and mathematically reorders them so the most highly-scored chunks are placed at the very beginning and very end of the list, placing the least relevant chunks in the middle where the LLM ignores them anyway."

### Scenario 2: Why LangChain is failing at Agents
*Interviewer:* "We tried using standard LangChain's `AgentExecutor` to build an AI that can write code, test it, and loop back to fix errors if the test fails. It keeps crashing. Why?"

*Answer:* "Because LangChain's core architecture (LCEL) is built as a **Directed Acyclic Graph (DAG)**. Data flows strictly in one direction (A $\rightarrow$ B $\rightarrow$ C). Standard chains cannot handle cycles or loops (A $\rightarrow$ B $\rightarrow$ A $\rightarrow$ B). If you want an Agent to execute code, read the error log, and loop back to rewrite the code, a DAG is mathematically incapable of doing this. For cyclical, long-running agents, we must abandon standard LangChain and upgrade to **LangGraph**, which is specifically designed for stateful, cyclical graph architectures."

---

## 7. Common Pitfalls & Debugging in Production

### ⚠️ Pitfall 1: Blindly passing `.invoke()` variables
In LCEL, the dictionary keys you pass into `.invoke()` must exactly match the variable names in your `PromptTemplate`.
```python
# Prompt expects {text} and {language}
prompt = ChatPromptTemplate.from_messages([("user", "Translate {text} to {language}")])

# ERROR! You passed 'input' instead of 'text'
chain.invoke({"input": "Hello", "language": "Spanish"}) # Crashes!
```

### ⚠️ Pitfall 2: Not using Streaming for UX
If you run `result = chain.invoke()`, the Python script will completely freeze for 10 seconds while the LLM generates the response, making your website look broken to the user.
*Fix:* Always use `chain.stream()`.
```python
# Streams the words to the console one by one, exactly like ChatGPT does visually!
for chunk in chain.stream({"text": "Tell me a long story", "language": "English"}):
    print(chunk, end="", flush=True)
```
