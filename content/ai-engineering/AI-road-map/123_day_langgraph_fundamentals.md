# Day 123: LangGraph Fundamentals & State Mastery (The Exhaustive Masterclass)

Welcome to Day 123. 

Yesterday, we mastered LangChain (LCEL). But LCEL has a fatal flaw: it is a Directed Acyclic Graph (DAG). It flows from left to right and stops. 
Real AI agents require **Cyclic** logic. If an agent writes code, tests it, and fails, it must loop *backwards* to rewrite the code.

**LangGraph** is the solution. It is a framework for building highly controllable, stateful, cyclic graphs. This guide is an exhaustive reference for LangGraph's core primitives.

---

## 🧠 1. The Core Architecture

LangGraph orchestrates your code using three primitives:
1. **State:** A globally shared Python dictionary.
2. **Nodes:** Python functions that receive the State, do work, and return a dictionary to *update* the State.
3. **Edges:** The wiring that connects Nodes.

```python
from typing import TypedDict
from langgraph.graph import StateGraph, START, END

# 1. Define the State Schema
class AgentState(TypedDict):
    task: str
    result: str

# 2. Define a Node
def worker_node(state: AgentState):
    # Reads the state
    task_input = state["task"]
    # Returns an update to the state
    return {"result": f"Completed: {task_input}"}

# 3. Build the Graph
builder = StateGraph(AgentState)
builder.add_node("Worker", worker_node)

# 4. Wire the Edges
builder.add_edge(START, "Worker")
builder.add_edge("Worker", END)

# 5. Compile and Execute
graph = builder.compile()
output = graph.invoke({"task": "Clean data"})
print(output) # {'task': 'Clean data', 'result': 'Completed: Clean data'}
```

---

## 🧬 2. State Management Mastery (Reducers)

In basic LangGraph, `State` is a `TypedDict`. When a node returns `{"result": "foo"}`, it blindly **overwrites** the existing value of `result`.
But what if your state contains a chat history? Overwriting the history deletes the conversation!

### A. The `Annotated` Reducer
To append to a list instead of overwriting it, we use `Annotated` combined with a reducer function like `operator.add`.

```python
import operator
from typing import Annotated, TypedDict

class ChatState(TypedDict):
    # 'operator.add' tells LangGraph: "Concatenate lists, do not overwrite them!"
    messages: Annotated[list, operator.add]
    error_count: int # Normal type: overwrites the value.

def chat_node(state: ChatState):
    # Because of operator.add, returning a list APPENDS to the existing list.
    return {"messages": ["Hello User!"], "error_count": 1}
```

### B. Pydantic State Validation
For enterprise applications, `TypedDict` is too loose. You can use Pydantic `BaseModel` to enforce strict type checking on your State.

```python
from pydantic import BaseModel, Field

class StrictState(BaseModel):
    user_id: str = Field(pattern=r"^[A-Z0-9]+$")
    messages: list[str] = Field(default_factory=list)

# You can pass the Pydantic class directly into StateGraph!
builder = StateGraph(StrictState)
```

### C. Message Trimming (Context Overflow Protection)
If a graph loops 500 times, the `messages` array will exceed the LLM's 128k token limit. 
LangChain provides `trim_messages` to automatically slice the array while preserving system prompts.

```python
from langchain_core.messages import trim_messages

def node_with_trimming(state: ChatState):
    # Keeps only the last 100 tokens, but guarantees the System Prompt (SystemMessage) is never deleted.
    trimmed = trim_messages(
        state["messages"],
        max_tokens=100,
        strategy="last",
        token_counter=llm,
        include_system=True 
    )
    res = llm.invoke(trimmed)
    return {"messages": [res]}
```

---

## 🔀 3. Conditional Routing Mastery

Edges dictate flow. A basic `.add_edge("A", "B")` is static. Real agents require dynamic routing.

### A. Traditional `conditional_edges`
You pass a routing function that inspects the state and returns a string matching the next node's name.

```python
def QA_Router(state: ChatState):
    if state["error_count"] > 0:
        return "FixBugNode"
    return "DeployNode"

# The third parameter defines the exact allowed outputs for graph validation.
builder.add_conditional_edges("TestNode", QA_Router, ["FixBugNode", "DeployNode"])
```

### B. The Modern `Command` Object (LangGraph 0.1+)
Instead of using a bulky `conditional_edges` router, a Node can dynamically route *itself* by returning a `Command` object. This simplifies graph architectures drastically.

```python
from langgraph.types import Command

def node_tester(state: ChatState):
    if state["error_count"] > 0:
        # Instead of returning a dictionary, return a Command!
        # It updates the state AND routes the edge simultaneously!
        return Command(
            goto="FixBugNode",
            update={"messages": ["Bug found!"]}
        )
    return Command(goto="DeployNode", update={"messages": ["Ready!"]})
```

---

## ⚡ 4. Asynchronous & Parallel Execution

### A. Parallel Node Execution (Fan-out / Fan-in)
LangGraph automatically executes nodes in parallel if an edge routes to multiple nodes simultaneously.

```python
def route_parallel(state):
    # Returning a LIST of node names tells LangGraph to run them in parallel threads!
    return ["SearchGoogleNode", "SearchDatabaseNode"]

builder.add_conditional_edges("PlannerNode", route_parallel)
```
When `SearchGoogleNode` and `SearchDatabaseNode` finish, their results will both be passed to the Reducer. If `messages` uses `operator.add`, both search results will be safely appended to the array without race conditions!

### B. Async Graphs
For high-concurrency production servers (like FastAPI), define your nodes as `async def` and use `.astream()`.

```python
async def async_worker(state: AgentState):
    res = await llm.ainvoke(state["task"])
    return {"result": res.content}

# Execution
async for event in graph.astream({"task": "Calculate mass"}):
    print(event)
```

---

## 💻 5. Exhaustive Code Example: The Cyclic Agent

Let's combine Reducers, Pydantic, and Conditional Routing into a fully functional Cyclic Agent that writes a joke and refuses to stop looping until the joke meets a quality standard.

*(Note: To run this code, you would need `pip install langgraph`)*

```python
import operator
from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, START, END

class ComedyState(TypedDict):
    topic: str
    jokes_written: Annotated[list, operator.add]
    loop_count: int

def node_writer(state: ComedyState):
    print(f"[WRITER] Writing joke # {state.get('loop_count', 0) + 1}...")
    new_joke = f"Why did the {state['topic']} cross the road? To prove a point!"
    return {
        "jokes_written": [new_joke], 
        "loop_count": state.get("loop_count", 0) + 1
    }

def node_critic(state: ComedyState):
    print("[CRITIC] Reviewing the jokes...")
    return {} # Critic doesn't alter the state, it just routes.

def route_critic(state: ComedyState):
    if state["loop_count"] >= 3:
        print("[ROUTER] 3 jokes written. I'm satisfied. Going to END.")
        return END
    print("[ROUTER] Not funny enough. Routing back to Writer.")
    return "Writer"

builder = StateGraph(ComedyState)
builder.add_node("Writer", node_writer)
builder.add_node("Critic", node_critic)

builder.add_edge(START, "Writer")
builder.add_edge("Writer", "Critic")
builder.add_conditional_edges("Critic", route_critic)

comedy_graph = builder.compile()

# Execution
print("--- STARTING CYCLIC GRAPH ---")
final_state = comedy_graph.invoke({"topic": "chicken", "loop_count": 0})
print("\n--- FINAL GRAPH STATE ---")
print(f"Total Loops: {final_state['loop_count']}")
print(f"Jokes Memory Array: {final_state['jokes_written']}")
```

---
**Summary:** You now understand the fundamental mechanics of StateGraphs, Reducers, Edges, and Parallelism.

Tomorrow, in **Day 124**, we elevate this to the absolute maximum level of enterprise production. We will cover **Checkpointers (Database Persistence), Time Travel Debugging, Human-in-the-Loop, and massive Multi-Agent Architectures (Supervisor & Hierarchical).**
