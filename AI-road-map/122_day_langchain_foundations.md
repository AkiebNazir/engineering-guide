# Day 122: LangChain In-Depth (The Exhaustive Masterclass)

Welcome to Day 122. 

Today we are stripping away the high-level overviews and diving into the absolute depths of **LangChain**. LangChain is not just a wrapper for OpenAI; it is an incredibly dense, standardized ecosystem for building LLM applications. 

This guide is designed as an exhaustive reference. We will cover **Model I/O, LCEL Mastery, Advanced RAG Capabilities, Tools, and Memory**, complete with isolated code examples for every feature.

---

## 🧠 1. Model I/O (The Foundation)

### A. LLMs vs. Chat Models
LangChain strictly separates legacy text-in/text-out models (`LLM`) from modern message-based models (`ChatModel`).

```python
from langchain_openai import OpenAI, ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

# Legacy LLM (Takes a string, returns a string)
llm = OpenAI(model="gpt-3.5-turbo-instruct")
res = llm.invoke("Tell me a joke.")

# Modern Chat Model (Takes an Array of Messages, returns an AIMessage object)
chat_model = ChatOpenAI(model="gpt-4o")
messages = [
    SystemMessage(content="You are a helpful assistant."),
    HumanMessage(content="Tell me a joke.")
]
res = chat_model.invoke(messages)
print(res.content) # Must extract .content from the AIMessage object!
```

### B. Prompt Templates
Never format strings manually. `PromptTemplates` prevent injection attacks and enforce structure.

```python
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder

# 1. Standard Prompt
prompt = PromptTemplate.from_template("Tell me a {adjective} joke about {subject}.")
formatted_str = prompt.format(adjective="sad", subject="cats")

# 2. Chat Prompt (For ChatModels)
chat_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a {profession}."),
    ("human", "Explain {topic}.")
])
formatted_messages = chat_prompt.format_messages(profession="physicist", topic="gravity")

# 3. MessagesPlaceholder (Crucial for injecting Chat History arrays!)
history_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are helpful."),
    MessagesPlaceholder(variable_name="chat_history"), # Injects a dynamic array of messages here
    ("human", "{input}")
])
```

### C. Output Parsers
LLMs output raw strings. Parsers force them into usable Python data structures.

```python
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field

# 1. StrOutputParser (Simplest: Extracts .content from AIMessage)
parser = StrOutputParser()

# 2. PydanticOutputParser (The Gold Standard for Extraction)
class Person(BaseModel):
    name: str = Field(description="The person's name")
    age: int = Field(description="The person's age")

json_parser = JsonOutputParser(pydantic_object=Person)

# You inject the JSON format instructions directly into the prompt!
prompt = PromptTemplate(
    template="Extract the info.\n{format_instructions}\nQuery: {query}",
    input_variables=["query"],
    partial_variables={"format_instructions": json_parser.get_format_instructions()}
)
```

---

## ⚡ 2. LCEL Mastery (LangChain Expression Language)

LCEL uses the `|` (pipe) operator to chain components. Every component is a `Runnable`.

### A. The Core Methods
Because everything is a `Runnable`, you get these methods for free:
- `chain.invoke(input)`: Runs synchronously.
- `chain.batch([input1, input2])`: Runs multiple inputs in parallel using a ThreadPool.
- `chain.stream(input)`: Yields token-by-token.
- `chain.astream_events(input)`: Advanced async streaming that yields events for *every* step in the chain (e.g., "tool started", "tool ended", "chunk generated").

### B. Manipulating State in Transit
When passing dictionaries through pipes, you often need to alter them without breaking the chain.

```python
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableAssign

# 1. RunnablePassthrough
# Passes the input dictionary exactly as it is, while calculating a new key.
chain = {"original_input": RunnablePassthrough(), "new_calc": some_function}

# 2. RunnableAssign
# Updates an existing dictionary with a new key.
# If input is {"x": 5}, output becomes {"x": 5, "y": 10}
chain = RunnablePassthrough.assign(y=lambda d: d["x"] * 2)

# 3. RunnableParallel
# Runs multiple branches at the exact same time.
parallel_chain = RunnableParallel(
    joke=joke_chain,
    poem=poem_chain
)
```

### C. Dynamic Routing & Fallbacks
```python
from langchain_core.runnables import RunnableBranch

# 1. RunnableBranch (If/Elif/Else)
branch_chain = RunnableBranch(
    (lambda x: x["topic"] == "math", math_prompt | llm),
    (lambda x: x["topic"] == "science", science_prompt | llm),
    default_prompt | llm # The 'Else' block
)

# 2. Fallbacks (High Availability)
# If OpenAI throws a 502 error, LCEL instantly retries with Anthropic.
resilient_llm = openai_llm.with_fallbacks([anthropic_llm])
```

---

## 📚 3. Advanced RAG (Retrieval-Augmented Generation)

Basic RAG fails in production. LangChain offers massive capabilities to fix it.

### A. Document Loaders & Splitters
```python
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

loader = PyPDFLoader("contract.pdf")
docs = loader.load()

# Recursive Splitter: Tries to split on paragraphs (\n\n) first, then sentences (\n).
# This prevents slicing a sentence in half!
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)
```

### B. Advanced Retrievers (The Pro Level)
```python
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore

# 1. MultiQueryRetriever
# Uses an LLM to rewrite the user's query into 5 variations before searching.
# Fixes the "Vague Query" problem.
mq_retriever = MultiQueryRetriever.from_llm(retriever=vectorstore.as_retriever(), llm=llm)

# 2. ParentDocumentRetriever
# Embeds small child chunks for precise searching, but returns the massive 
# Parent chunk to the LLM so context isn't lost!
store = InMemoryStore()
parent_retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=RecursiveCharacterTextSplitter(chunk_size=200),
    parent_splitter=RecursiveCharacterTextSplitter(chunk_size=2000)
)

# 3. Contextual Compression Retriever
# Wraps a base retriever. After retrieving 10 docs, an LLM explicitly deletes 
# irrelevant sentences from the documents BEFORE passing them to the final LLM.
# Saves massive amounts of context window tokens.
```

---

## 🛠️ 4. Tools & Agents

LangChain makes it incredibly easy to bind Python functions to LLMs using OpenAI's Function Calling API.

### A. Defining Tools
```python
from langchain_core.tools import tool

# The docstring and type hints are CRITICAL. LangChain converts them into 
# the JSON Schema sent to the LLM!
@tool
def get_weather(location: str) -> str:
    """Get the current weather for a specific location."""
    return f"It is sunny in {location}."

tools = [get_weather]
```

### B. Binding Tools to Models
```python
# .bind_tools() modifies the LLM so it knows the tools exist.
llm_with_tools = llm.bind_tools(tools)

res = llm_with_tools.invoke("What is the weather in Tokyo?")
# The LLM doesn't output text. It outputs an AIMessage with tool_calls!
print(res.tool_calls) 
# [{'name': 'get_weather', 'args': {'location': 'Tokyo'}, 'id': 'call_123'}]
```

---

## 💾 5. Memory & Callbacks

### A. Callbacks (Observability)
Callbacks let you hook into the execution lifecycle.
```python
from langchain_core.callbacks import StreamingStdOutCallbackHandler

# This instantly prints every generated token to the terminal in real-time.
llm = ChatOpenAI(streaming=True, callbacks=[StreamingStdOutCallbackHandler()])
```

### B. Memory (Legacy vs Modern)
Historically, LangChain used `ConversationBufferMemory`. 
```python
from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory(return_messages=True)
memory.save_context({"input": "hi"}, {"output": "hello"})
```
*Note: In modern LangChain architectures (mid-2024 onwards), stateful memory is heavily delegated to **LangGraph**, which we will cover exhaustively in Day 123.*

---
**Summary:** You now understand every major capability of the LangChain framework. It is a vast library of highly optimized primitives (Runnables, Loaders, Retrievers, Parsers). 

Tomorrow, in **Day 123**, we will learn **LangGraph**. We will learn how to take these LCEL primitives and orchestrate them into massive, stateful, multi-step loops using Checkpointers, Reducers, and the Command object.
