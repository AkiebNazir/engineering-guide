# Capstone Project 2: Autonomous Agentic Workflow

## Objective
Build a Multi-Agent system capable of performing a complex, multi-step task autonomously. The agent must be able to use tools (like web search or file reading), evaluate its own work, and correct its mistakes without human intervention.

## Tech Stack to Use
- **Agent Orchestration:** LangGraph (for strict control) OR CrewAI (for persona-based autonomy)
- **Tools/Integration:** FastMCP or standard LangChain Tools (e.g., `TavilySearchResults`)
- **LLM:** A strong reasoning model (e.g., `gpt-4o` or `claude-3-5-sonnet`)

## Step-by-Step Implementation Guide (using LangGraph)

### Step 1: Define the Tools
1. Create a Python function that performs a Google Search (or uses the Tavily API).
2. Create a Python function that reads the contents of a local file.
3. Wrap these functions in `@tool` decorators so the LLM understands how to call them.

### Step 2: Define the State
1. Create a `TypedDict` for your Agent's memory (the `State`). It should store the `messages` history and a `current_step` integer.

### Step 3: Build the Nodes
1. **The Planner Node:** Looks at the user's request and outputs a 3-step plan.
2. **The Execution Node:** The LLM that actually calls the tools to execute the current step of the plan.
3. **The Critic Node (Self-Reflection):** An LLM node that reads the output of the Execution node and asks: "Did this actually succeed?" If yes, move to the next step. If no, generate feedback on what failed.

### Step 4: Wire the Graph (Edges & Logic)
1. Initialize the `StateGraph`.
2. Connect `Planner -> Execution`.
3. Create a **Conditional Edge** coming out of the `Critic`. 
   - If the Critic says "Failed", the edge loops back to the `Execution` node.
   - If the Critic says "Passed", the edge routes back to the `Planner` or to `END`.
   - *Crucial Safeguard:* Add logic to the edge: `if loop_count > 3: return END` to prevent infinite API billing loops.

### Step 5: Execution
1. Compile the graph.
2. Pass in a difficult prompt: *"Research the latest advancements in solid-state batteries in 2024, summarize the top 3 companies working on it, and save the report to a local markdown file."*
3. Watch the terminal as your agent creates a plan, searches the web, hits an error, critiques itself, fixes the error, and completes the task!
