# Module 7 — Multi-Agent Orchestration & Model Context Protocol (MCP)

If Module 2 taught us how a single Agent works (Reasoning, Tool Use, Memory), this module explores what happens when we scale up. How do multiple agents collaborate? How do we standardize the tools they use across an entire enterprise?

As the complexity of AI applications grows, single-agent architectures hit a ceiling. Context windows fill up, reasoning traces diverge, and the model struggles to balance specialized domain knowledge with general orchestration. 

This guide provides a comprehensive deep dive into **Multi-Agent Orchestration** and the **Model Context Protocol (MCP)**, equipping you with the patterns, tools, and code necessary to build advanced agentic systems.

---

## 1. Multi-Agent Orchestration: Beyond the Single Prompt

A single <abbr title="Large Language Model">LLM</abbr> agent often fails when given a massive, multi-step objective. The context window gets cluttered, the reasoning diverges, and error rates skyrocket. 

**Multi-Agent Orchestration** solves this by breaking the objective into specialized agents, each with a narrow focus, specific tools, and a distinct persona.

### 1.1 The Orchestration Ceiling
Before diving into patterns, understand why single agents fail:
1. **Context Dilution**: A single agent loaded with 50 tools struggles to pick the right one.
2. **Conflicting Personas**: An agent cannot effectively act as a creative brainstormer and a rigid, rules-based SQL analyst simultaneously.
3. **Error Recovery**: If a monolithic agent fails step 7 of a 10-step plan, it often has to restart. Multi-agent systems can localize and retry specific tasks.

### 1.2 Key Architectural Patterns

#### Pattern A: The Router Pattern
The simplest multi-agent system. A single "Router" agent analyzes the user's intent and routes the query to a specialized worker agent.

```arch
[User Request] --> [Router Agent]
[Router Agent] --> [SQL Agent]
[Router Agent] --> [Creative Writer Agent]
[Router Agent] --> [Web Search Agent]
```

**Implementation in Code (LangGraph pseudocode):**
```python
def router_node(state):
    intent = llm.predict(f"Classify intent: {state['query']}")
    if intent == "SQL": return "sql_agent"
    elif intent == "SEARCH": return "search_agent"
    return "writer_agent"
```

#### Pattern B: Sequential (Pipelines)
Agent A finishes a task and hands its output directly to Agent B. Often used in frameworks like CrewAI.

```arch
[Researcher Agent] --> [Data Analyst Agent]
[Data Analyst Agent] --> [Report Writer Agent]
[Report Writer Agent] --> [Final Output]
```

**Use Case:** Financial report generation where the pipeline is strict and predictable.

#### Pattern C: Hierarchical (Manager-Worker)
A "Manager" agent breaks down a task and delegates it to "Worker" agents. The Manager reviews their output and can request revisions.

```arch
[User] --> [Manager Agent]
[Manager Agent] --> [Coder Agent]
[Manager Agent] --> [Reviewer Agent]
[Reviewer Agent] --> [Manager Agent]
```

**Use Case:** Software development (e.g., AutoGen, Devin).

#### Pattern D: State Machines / Cyclic Graphs (LangGraph)
Frameworks like **LangGraph** treat agents as nodes in a graph. The system flows from node to node, allowing for cyclic loops (e.g., Coder -> Tester -> (if fail) back to Coder).

```arch
[Planner] --> [Coder]
[Coder] --> [Tester]
[Tester] --"Tests Fail"--> [Coder]
[Tester] --"Tests Pass"--> [Done]
```

#### Pattern E: Swarm
A decentralized approach where agents independently choose to hand off tasks to other specialized agents. No single manager dictates the flow.

---

## 2. Deep Dive: Building with LangGraph

LangGraph has become the industry standard for production multi-agent systems because it treats orchestration as a state machine.

### 2.1 The Shared State
When multiple agents collaborate, they need a "Shared State" (like a shared whiteboard). In LangGraph, this is a `TypedDict` or Pydantic model.

```python
from typing import TypedDict, Annotated
import operator

class AgentState(TypedDict):
    # 'messages' will be appended to, not overwritten
    messages: Annotated[list, operator.add]
    current_task: str
    research_notes: str
    code_snippet: str
```

### 2.2 Defining Nodes (Agents)
Each agent is a Python function that reads the state, does work, and returns a state update.

```python
def researcher_node(state: AgentState):
    notes = researcher_llm.invoke(f"Research: {state['current_task']}")
    return {"research_notes": notes}

def coder_node(state: AgentState):
    code = coder_llm.invoke(f"Write code based on: {state['research_notes']}")
    return {"code_snippet": code}
```

### 2.3 Compiling the Graph
```python
from langgraph.graph import StateGraph, END

workflow = StateGraph(AgentState)

workflow.add_node("researcher", researcher_node)
workflow.add_node("coder", coder_node)

workflow.set_entry_point("researcher")
workflow.add_edge("researcher", "coder")
workflow.add_edge("coder", END)

app = workflow.compile()
```

---

## 3. The Tooling Bottleneck

In standard Agentic <abbr title="Artificial Intelligence">AI</abbr>, giving an agent access to a tool requires writing custom wrapper code.

If you have 10 different agent frameworks (CrewAI, AutoGen, LangChain, LlamaIndex) and 50 different data sources (GitHub, Slack, SQL, Jira, Notion), you have an N x M integration nightmare. Every time an API changes, 10 different integrations break.

---

## 4. Model Context Protocol (<abbr title="Model Context Protocol">MCP</abbr>)

**<abbr title="Model Context Protocol">MCP</abbr> (Model Context Protocol)** is an open standard introduced by Anthropic to solve the tooling bottleneck. It is to <abbr title="Artificial Intelligence">AI</abbr> Agents what USB-C is to electronics.

### 4.1 How it Works

Instead of giving an Agent direct access to a database, you build an **<abbr title="Model Context Protocol">MCP</abbr> Server**.

1. **The <abbr title="Model Context Protocol">MCP</abbr> Server**: A lightweight server that connects securely to your enterprise database. It exposes standard "Tools" and "Resources" over stdio or SSE (Server-Sent Events).
2. **The <abbr title="Model Context Protocol">MCP</abbr> Client**: Your Agent (e.g., Claude Desktop, a LangGraph agent) connects to the <abbr title="Model Context Protocol">MCP</abbr> Server.

Because both speak the <abbr title="Model Context Protocol">MCP</abbr> protocol, the Agent instantly knows exactly what tools the server offers and how to use them, without any custom integration code.

### 4.2 <abbr title="Model Context Protocol">MCP</abbr> in Enterprise Security (Zero-Trust)

In enterprise infrastructure, <abbr title="Model Context Protocol">MCP</abbr> acts as an air-gap.

- The external <abbr title="Large Language Model">LLM</abbr> (e.g., GPT-4, Claude 3.5 Sonnet) never sees your database credentials.
- The <abbr title="Large Language Model">LLM</abbr> asks the local <abbr title="Model Context Protocol">MCP</abbr> Client to execute a tool.
- The <abbr title="Model Context Protocol">MCP</abbr> Client talks to the internal <abbr title="Model Context Protocol">MCP</abbr> Server.
- The <abbr title="Model Context Protocol">MCP</abbr> Server runs the query and returns the context.

```arch
[Cloud LLM] <-- "Tool call: get_user" --> [MCP Client (Local Agent)]
[MCP Client (Local Agent)] <-- "MCP Protocol" --> [MCP Server (Internal)]
[MCP Server (Internal)] <-- "SQL Query" --> [Enterprise DB]
```

<div class="lab" data-viz="flow-mcp"></div>

---

## 5. The 3 Primitives of <abbr title="Model Context Protocol">MCP</abbr>

MCP standardizes three core primitives:

### 5.1 Resources
Resources are static or dynamic data the agent can read. Think of them like files on a filesystem. They are identified by URIs.

Examples:
- `file:///app/logs/error.log`
- `postgres://schema/public/table/users`
- `notion://workspace/page/12345`

### 5.2 Tools
Tools are executable functions the agent can call. They have a defined JSON Schema for arguments.

Examples:
- `query_database(sql: string)`
- `create_github_issue(repo: string, title: string, body: string)`
- `restart_kubernetes_pod(pod_name: string)`

### 5.3 Prompts
Reusable prompt templates provided by the server. This allows domain experts to encode best practices into the server itself.

Examples:
- `review_code(language: string)` - Returns a system prompt tailored for reviewing specific languages.
- `analyze_logs` - Returns a prompt instructing the LLM on exactly what anomalies to look for.

---

## 6. Building an <abbr title="Model Context Protocol">MCP</abbr> Server

Let's build a practical MCP server in Python using the official `mcp` SDK.

### 6.1 Server Setup

```python
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

# Initialize the server
app = Server("weather-mcp-server")
```

### 6.2 Defining a Tool

We use decorators to expose tools to the agent.

```python
@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="get_weather",
            description="Get the current weather for a city",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "Name of the city"}
                },
                "required": ["city"]
            }
        )
    ]

@app.call_tool()
async def call_tool(
    name: str, arguments: dict
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    if name == "get_weather":
        city = arguments.get("city")
        # In a real app, call a weather API
        result = f"The weather in {city} is sunny and 72°F."
        return [types.TextContent(type="text", text=result)]
    
    raise ValueError(f"Tool {name} not found")
```

### 6.3 Defining a Resource

Resources allow agents to read context.

```python
@app.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri="weather://alerts",
            name="Active Weather Alerts",
            mimeType="text/plain",
            description="Current active weather alerts globally"
        )
    ]

@app.read_resource()
async def read_resource(uri: str) -> str | bytes:
    if uri == "weather://alerts":
        return "Tornado warning in Kansas. Flash flood watch in Florida."
    raise ValueError(f"Resource {uri} not found")
```

### 6.4 Running the Server

MCP servers typically run over standard input/output (stdio) so they can be launched as subprocesses by the client.

```python
async def main():
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="weather-mcp",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

---

## 7. Connecting to an <abbr title="Model Context Protocol">MCP</abbr> Server

Agents connect to the MCP server using an MCP Client. Here is how a client interacts with the server we just built.

```python
from mcp.client.stdio import stdio_client
from mcp.client.session import ClientSession
import asyncio

async def run_agent():
    # Define the command to start the MCP server
    server_params = mcp.client.stdio.StdioServerParameters(
        command="python",
        args=["weather_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Agent discovers tools
            tools = await session.list_tools()
            print("Available tools:", [t.name for t in tools.tools])
            
            # Agent calls a tool
            result = await session.call_tool("get_weather", {"city": "Seattle"})
            print("Tool result:", result.content[0].text)
            
            # Agent reads a resource
            resource = await session.read_resource("weather://alerts")
            print("Resource content:", resource.contents[0].text)

asyncio.run(run_agent())
```

---

## 8. Advanced Orchestration with <abbr title="Model Context Protocol">MCP</abbr>

When you combine Multi-Agent Orchestration with MCP, you unlock enterprise scalability.

### 8.1 The Swarm + <abbr title="Model Context Protocol">MCP</abbr> Pattern

Instead of giving a monolithic agent 50 tools, you build specialized agents that connect to specialized MCP servers.

```arch
[User Request] --> [Router Agent]
[Router Agent] --> [Database Agent]
[Database Agent] <--"MCP Protocol"--> [PostgreSQL MCP Server]
[Router Agent] --> [DevOps Agent]
[DevOps Agent] <--"MCP Protocol"--> [Kubernetes MCP Server]
```

1. **Isolation**: The DevOps agent does not have access to the HR database.
2. **Reusability**: The PostgreSQL MCP Server can be used by the Database Agent, the BI Agent, and the Auditor Agent without rewriting integration code.
3. **Auditability**: The MCP Server acts as a choke point where you can enforce RBAC (Role-Based Access Control) and log every tool execution.

### 8.2 Testing and Evaluation

Testing a multi-agent system is notoriously difficult. MCP simplifies this. Because the agent's environment is entirely abstracted behind the MCP protocol, you can build a **Mock MCP Server** for testing.

The Mock MCP Server returns deterministic responses for tools and resources, allowing you to run automated regression tests on your agents without hitting live databases or APIs.

---

## 9. Summary

To build enterprise-grade <abbr title="Artificial Intelligence">AI</abbr>, you don't just build one massive prompt. 
- You build **Swarm architectures** to divide cognitive load and handle failure gracefully.
- You build **<abbr title="Model Context Protocol">MCP</abbr> Servers** to safely, standardly, and securely connect those agents to your proprietary data and systems.

By separating the **Orchestration** (LangGraph, CrewAI) from the **Tooling Integration** (MCP), you create systems that are modular, secure, and scalable.
