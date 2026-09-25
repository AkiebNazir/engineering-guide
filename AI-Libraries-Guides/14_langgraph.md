# LangGraph Mastery: Stateful, Multi-Actor LLM Agents

## 1. The Core Concept (What and Why)

*Why is this tool relevant?* In Guide 11, we learned that standard LangChain (LCEL) is a **<abbr title="Directed Acyclic Graph. A directed graph with no directed cycles, consisting of vertices and edges where each edge is directed from one vertex to another.">DAG</abbr> (Directed Acyclic Graph)**. Data flows strictly from Left to Right. If you want an Agent to execute code, read the error message, and *loop back* to rewrite the code, standard LangChain crashes. **LangGraph** was built specifically to solve this. It replaces the old, broken `AgentExecutor` with a robust, cyclical graph architecture.

**What is it?**
LangGraph is an extension of LangChain designed for building stateful, multi-actor applications. You model your application as a graph, where:
- **Nodes** are Python functions (often calling an <abbr title="Large Language Model">LLM</abbr> or an <abbr title="Application Programming Interface">API</abbr>).
- **Edges** control the flow (including loops).
- **State** is a dictionary that gets passed around and updated by every Node.

---

## 2. Setup & Installation

```bash
pip install langgraph langchain-openai
```

```python
import langgraph

print(f"LangGraph version: {langgraph.__version__}")
```

---

## 3. The "Hello World": Building a Stateful Graph

Let's build a simple Agent. The user asks a question. Node 1 (The <abbr title="Large Language Model">LLM</abbr>) decides if it needs to search the web. If yes, it routes to Node 2 (The Search Tool). Node 2 updates the State with the search results and routes back to Node 1.

### A. Define the State
The `State` is the memory of the graph. Every Node receives this dictionary, reads it, and returns updates to it.

```python
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    # 'Annotated[list, operator.add]' tells LangGraph:
    # "If a Node returns a new message, do NOT overwrite the list. ADD to it!"
    messages: Annotated[list, operator.add]
```

### B. Define the Nodes (The Functions)
```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage

model = ChatOpenAI(model="gpt-3.5-turbo")

def chatbot_node(state: AgentState):
    """Reads the message history and generates a response."""
    response = model.invoke(state["messages"])
    
    # We return a dictionary that matches the State schema.
    # LangGraph will automatically use operator.add to append this to the history!
    return {"messages": [response]}

def tool_node(state: AgentState):
    """Simulates a web search."""
    # In a real app, you would execute an actual search here.
    return {"messages": [AIMessage(content="Search result: Paris is the capital of France.")]}
```

### C. Build the Graph and Edges
```python
from langgraph.graph import StateGraph, END

# 1. Initialize the Graph
workflow = StateGraph(AgentState)

# 2. Add the Nodes
workflow.add_node("chatbot", chatbot_node)
workflow.add_node("search_tool", tool_node)

# 3. Define the Edges (The Flow)
# We start at the chatbot
workflow.set_entry_point("chatbot")

# Conditional Edge! (The brain of the agent)
def should_search(state: AgentState):
    last_message = state["messages"][-1].content
    if "search" in last_message.lower():
        return "search_tool"
    return END # Ends the program!

workflow.add_conditional_edges(
    "chatbot",           # The node making the decision
    should_search,       # The function that decides
    {
        "search_tool": "search_tool", # If func returns 'search_tool', go there
        END: END                      # If func returns END, terminate.
    }
)

# If the search tool finishes, ALWAYS loop back to the chatbot to synthesize the final answer!
workflow.add_edge("search_tool", "chatbot")

# 4. Compile!
app = workflow.compile()
```

### D. Run It
```python
inputs = {"messages": [HumanMessage(content="Please search for the capital of France.")]}

# The app will loop through the graph automatically!
for output in app.stream(inputs):
    for key, value in output.items():
        print(f"Node '{key}' just ran!")
```

---

## 4. Deep Dive: Persistence and Memory (`checkpointer`)

In production, you don't run a script once and throw it away. A user chats with your bot, closes their laptop, and comes back 3 days later. The Agent must remember the state of the graph.

LangGraph handles this using **Checkpointers** (like a save-state in a video game).

### Parameter Breakdown: `thread_id` and `checkpointer`
- `checkpointer` (MemorySaver): An object (SQLite, Postgres, or Redis) that saves the graph's `State` to disk after every single node executes.
- `thread_id` (string): The unique ID for the user's conversation.
  - *Effect:* When you call `app.invoke()`, you pass the `thread_id`. LangGraph automatically queries the database, loads the exact state from 3 days ago into the graph, and resumes execution seamlessly.

```python
from langgraph.checkpoint.memory import MemorySaver

# 1. Setup the Database (In-memory for this example)
memory = MemorySaver()

# 2. Compile the graph WITH memory
app_with_memory = workflow.compile(checkpointer=memory)

# 3. Execution (Notice we pass a config dictionary!)
config = {"configurable": {"thread_id": "user_123_session"}}

# Run the graph
app_with_memory.invoke(inputs, config=config)

# 3 days later, the user sends a new message.
# LangGraph automatically loads the old history, appends the new message, and continues!
new_input = {"messages": [HumanMessage(content="What did I just ask you?")]}
response = app_with_memory.invoke(new_input, config=config)
```

---

## 5. Pro Level: Human-in-the-Loop (Interrupts)

You built an Agent that can execute <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> queries and drop production databases. You *do not* want the Agent to run this automatically. You need **Human-in-the-Loop** approval.

Because LangGraph saves the State after every node, you can explicitly tell it to pause execution right before a dangerous node.

```python
# Compile the graph, telling it to pause BEFORE executing 'search_tool'
app_safe = workflow.compile(
    checkpointer=memory, 
    interrupt_before=["search_tool"]
)

# Run it. It will hit the chatbot node, decide it needs to search, and PAUSE.
app_safe.invoke(inputs, config=config)

# The state is frozen in the database.
# ... The Human reviews the requested action in a UI ...
# If the human approves, we resume the graph with NO inputs!
# LangGraph just picks up exactly where it paused.
app_safe.invoke(None, config=config)
```

---

## 6. MAANG Interview Scenarios

### Scenario 1: LangChain Agents vs LangGraph
*Interviewer:* "We currently use LangChain's `create_openai_tools_agent()`. It works okay, but sometimes the agent gets stuck in an infinite loop of using the same broken tool over and over until it hits the <abbr title="Application Programming Interface">API</abbr> token limit and crashes. How does LangGraph solve this?"

*Answer:* "Standard LangChain agents are black boxes. The <abbr title="Large Language Model">LLM</abbr> controls the entire loop internally, which means we cannot inject hard logic to stop it. In LangGraph, the loop is explicitly defined by our Edges. I would update the `State` dictionary to include a `tool_error_count` integer. Inside the Conditional Edge, I would write standard Python logic: `if state['tool_error_count'] > 3: return END`. This forcibly wrests control away from the hallucinating <abbr title="Large Language Model">LLM</abbr> and gracefully degrades the system, guaranteeing we never hit an infinite <abbr title="Application Programming Interface">API</abbr> loop."

### Scenario 2: Time-Travel Debugging
*Interviewer:* "An agent executed a complex 10-step graph yesterday and ultimately generated a completely wrong answer. How do we debug what went wrong at step 4 without re-running the expensive <abbr title="Large Language Model">LLM</abbr> calls?"

*Answer:* "Because we compiled the LangGraph with a `checkpointer`, every single intermediate state was saved to the database. We can use the `app.get_state_history(config)` method to literally 'Time Travel' back to yesterday's execution. We can pull the exact `State` dictionary as it existed after step 4, inspect the variables, and even manually override the state and resume execution from step 4 to test a bug fix, saving massive amounts of compute."
