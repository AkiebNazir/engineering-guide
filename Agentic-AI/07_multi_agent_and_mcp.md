# Module 7 — Multi-Agent Orchestration & Model Context Protocol (MCP)

If Module 2 taught us how a single Agent works (Reasoning, Tool Use, Memory), this module explores what happens when we scale up. How do multiple agents collaborate? How do we standardize the tools they use across an entire enterprise?

---

## 1. Multi-Agent Orchestration

A single LLM agent often fails when given a massive, multi-step objective. The context window gets cluttered, the reasoning diverges, and error rates skyrocket. 

**Multi-Agent Orchestration** solves this by breaking the objective into specialized agents.

### Key Architectures
1. **Hierarchical (Manager-Worker)**: A "Manager" agent breaks down a task and delegates it to "Worker" agents (e.g., a Researcher agent and a Coder agent). The Manager reviews their output.
2. **Sequential (Pipelines)**: Agent A finishes a task and hands its output directly to Agent B. (Often used in frameworks like CrewAI).
3. **State Machines / Cyclic Graphs**: Frameworks like **LangGraph** treat agents as nodes in a graph. The system flows from node to node, allowing for cyclic loops (e.g., Coder -> Tester -> (if fail) back to Coder).
4. **Swarm**: A decentralized approach where agents can independently choose to hand off tasks to other specialized agents.

### Shared State & Memory
When multiple agents collaborate, they need a "Shared State" (like a shared whiteboard). In LangGraph, this is literally a `State` object (a Python dictionary) that gets passed from agent to agent. If the Researcher finds a fact, they write it to the State, and the Writer reads it from the State.

---

## 2. The Tooling Bottleneck

In standard Agentic AI, if you want your agent to talk to your company's SQL database, you have to write custom Python code to define the tool, handle the API keys, and parse the SQL.

If you have 10 different agent frameworks (CrewAI, AutoGen, LangChain) and 50 different data sources (GitHub, Slack, SQL, Jira), you have an N x M integration nightmare.

---

## 3. Model Context Protocol (MCP)

**MCP (Model Context Protocol)** is an open standard introduced by Anthropic to solve the tooling bottleneck. It is to AI Agents what USB-C is to electronics.

### How it Works
Instead of giving an Agent direct access to a database, you build an **MCP Server**.
1. **The MCP Server**: A lightweight server (often running locally) that connects securely to your enterprise database. It exposes standard "Tools" and "Resources".
2. **The MCP Client**: Your Agent (whether it's Claude Desktop, a LangChain script, or a custom Swarm) connects to the MCP Server.

Because both speak the MCP protocol, the Agent instantly knows exactly what tools the server offers and how to use them, without any custom integration code.

### MCP in Enterprise Security (Zero-Trust)
In your `04_enterprise_ai_infrastructure` project, MCP acts as an air-gap. 
- The external LLM never sees your database credentials. 
- The LLM asks the MCP Client to execute a tool.
- The MCP Client talks to the MCP Server.
- The MCP Server runs the query and returns the context.

<div class="lab" data-viz="flow-mcp"></div>

### The 3 Primitives of MCP
1. **Resources**: Static data the agent can read (e.g., a specific log file or a Notion page).
2. **Tools**: Functions the agent can execute (e.g., `query_employee_db()`).
3. **Prompts**: Reusable prompt templates the server provides to the client.

---

## Summary
To build enterprise-grade AI, you don't just build one massive prompt. You build **Swarm architectures** to divide cognitive load, and you build **MCP Servers** to safely and standardly connect those agents to your proprietary data.
