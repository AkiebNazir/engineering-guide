# FastMCP Mastery: The Model Context Protocol Standard

## 1. The Core Concept (What and Why)

*Why is this tool relevant?* In 2023, every <abbr title="Artificial Intelligence">AI</abbr> company built their own proprietary plugin system. If you built a "GitHub integration," you had to write one version for ChatGPT, a completely different version for Claude, and a third version for LangChain. It was a fragmented nightmare. In late 2024, Anthropic open-sourced **<abbr title="Model Context Protocol">MCP</abbr> (Model Context Protocol)**. It is essentially "USB-C for <abbr title="Artificial Intelligence">AI</abbr>."

**What is it?**
<abbr title="Model Context Protocol">MCP</abbr> is a universal, open-source standard for connecting <abbr title="Artificial Intelligence">AI</abbr> models to data sources and tools. **FastMCP** is the fastest, most pythonic framework for building these <abbr title="Model Context Protocol">MCP</abbr> servers (heavily inspired by FastAPI).

**Why does it exist?**
You build a FastMCP server once. Instantly, Claude Desktop, Cursor IDE, LangGraph, and custom OpenAI scripts can ALL connect to your server and use your tools without changing a single line of code. It standardizes <abbr title="Artificial Intelligence">AI</abbr> integrations universally.

---

## 2. Setup & Installation

```bash
pip install fastmcp
```

```python
from fastmcp import FastMCP

# We will create our server
mcp = FastMCP("My Database Server")
print("FastMCP Initialized!")
```

---

## 3. The "Hello World": Prompts, Resources, and Tools

An <abbr title="Model Context Protocol">MCP</abbr> server provides exactly three things to any <abbr title="Large Language Model">LLM</abbr> that connects to it:
1. **Prompts:** Reusable templates (like macros).
2. **Resources:** Read-only data (like a file or a database table).
3. **Tools:** Executable functions (like running code or updating a database).

FastMCP uses Python decorators to make this incredibly simple.

### A. Defining a Tool (Execution)
If an <abbr title="Large Language Model">LLM</abbr> connects to this server, it will automatically know it has the ability to fetch the weather. The docstring and type-hints are CRITICAL. FastMCP reads them and uses them to explain to the <abbr title="Large Language Model">LLM</abbr> exactly how to use the tool!

```python
from fastmcp import FastMCP

mcp = FastMCP("WeatherServer")

# The @mcp.tool decorator exposes this function to the LLM universally!
@mcp.tool()
def get_weather(city: str) -> str:
    """Fetches the current weather for a specific city. 
    Use this when the user asks about the temperature or forecast."""
    
    # In reality, you would call a real API here
    weather_database = {
        "New York": "75°F and Sunny",
        "London": "60°F and Raining"
    }
    return weather_database.get(city, "City not found in database.")
```

### B. Defining a Resource (Read-Only Data)
Resources use URI templates (like web URLs). They are perfect for exposing massive logs or database tables that the <abbr title="Large Language Model">LLM</abbr> can read.

```python
# Exposes a specific server log file to the LLM
@mcp.resource("file://logs/server/{date}.log")
def read_server_logs(date: str) -> str:
    """Read the server logs for a specific date (YYYY-MM-DD)"""
    try:
        with open(f"/var/logs/server_{date}.log", "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading log: {str(e)}"
```

### C. Running the Server
```python
# This starts the server using stdio (Standard Input/Output)
# An LLM client (like Claude Desktop) will boot this script up and communicate 
# with it directly via the terminal stream!
if __name__ == "__main__":
    mcp.run()
```

---

## 4. Deep Dive: Connecting an <abbr title="Large Language Model">LLM</abbr> Client to FastMCP

Now that you have built the server (`server.py`), how does an <abbr title="Large Language Model">LLM</abbr> actually use it?
If you use Claude Desktop, you just add one line to your `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "my_weather_server": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```
That's it. When you open Claude Desktop, the <abbr title="Artificial Intelligence">AI</abbr> instantly has a button allowing it to fetch the weather.

**Connecting via Code (LangChain):**
If you want to use the <abbr title="Model Context Protocol">MCP</abbr> server inside a custom Python script, you use the <abbr title="Model Context Protocol">MCP</abbr> Client library.

```python
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_client():
    # 1. Point the client to your FastMCP python script
    server_params = StdioServerParameters(
        command="python",
        args=["server.py"]
    )

    # 2. Connect via Stdio
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # 3. Ask the server what tools it has available!
            tools = await session.list_tools()
            print("Available Tools:", [t.name for t in tools.tools])
            
            # 4. Execute the tool! (The LLM would decide to do this autonomously)
            result = await session.call_tool("get_weather", {"city": "London"})
            print(result.content) # "60°F and Raining"

# asyncio.run(run_client())
```

---

## 5. Parameter Breakdown and Advanced Features

### Dependency Injection (Context)
Often, a tool needs access to something the <abbr title="Large Language Model">LLM</abbr> shouldn't know about (like a raw database connection or <abbr title="Application Programming Interface">API</abbr> key). You inject this using the `Context` parameter.

- *Effect:* The <abbr title="Large Language Model">LLM</abbr> sees the `city` parameter and knows it must provide a city. But FastMCP hides the `ctx` parameter from the <abbr title="Large Language Model">LLM</abbr>. It injects the context securely in the background.

```python
from fastmcp import FastMCP, Context

mcp = FastMCP("SecureDB")

# Imagine we set this up elsewhere
secure_db_connection = {"api_key": "secret_123"}

@mcp.tool()
def query_private_db(city: str, ctx: Context) -> str:
    """Query the database for info about a city."""
    
    # We can access hidden server state!
    # The LLM doesn't know about this.
    ctx.info(f"LLM just queried for {city}")
    
    return f"Data for {city} accessed using hidden key."
```

---

## 6. MAANG Interview Scenarios

### Scenario 1: <abbr title="Model Context Protocol">MCP</abbr> vs REST APIs
*Interviewer:* "We already have a REST <abbr title="Application Programming Interface">API</abbr> for our weather database. Why should we wrap it in a FastMCP server instead of just giving the <abbr title="Large Language Model">LLM</abbr> the OpenAPI/Swagger JSON spec?"

*Answer:* "While LLMs can read OpenAPI specs and generate HTTP requests, it is brittle. REST APIs are designed for computer-to-computer interaction, not <abbr title="Large Language Model">LLM</abbr>-to-computer interaction. <abbr title="Model Context Protocol">MCP</abbr> provides a standardized layer of indirection. 
First, <abbr title="Model Context Protocol">MCP</abbr> supports **Resources** natively, allowing the <abbr title="Large Language Model">LLM</abbr> to subscribe to real-time data updates (like tailing a log file) which standard stateless REST cannot do easily. Second, <abbr title="Model Context Protocol">MCP</abbr> standardizes error handling; if an <abbr title="Model Context Protocol">MCP</abbr> tool fails, it returns the error directly to the <abbr title="Large Language Model">LLM</abbr> in a format it understands, allowing the <abbr title="Large Language Model">LLM</abbr> to autonomously self-correct and try again. Finally, by adopting <abbr title="Model Context Protocol">MCP</abbr>, our internal tooling becomes instantly compatible with any future vendor (Cursor, Anthropic, OpenAI) without rewriting custom REST integration logic."

### Scenario 2: Stdio vs SSE Transport
*Interviewer:* "FastMCP defaults to running over `stdio` (Standard Input/Output). When would you choose to run it over `SSE` (Server-Sent Events) over HTTP instead?"

*Answer:* "`stdio` is perfect for local, single-tenant use cases (like Cursor IDE connecting to a local script on my laptop). It's incredibly fast and requires no networking. 
However, if we are deploying this tool for our enterprise cloud architecture, `stdio` fails because it relies on local processes. We must switch FastMCP to use `SSE` transport (`mcp.run(transport='sse')`). This runs the <abbr title="Model Context Protocol">MCP</abbr> server as a standard web server accessible via HTTP. This allows multiple remote <abbr title="Large Language Model">LLM</abbr> agents hosted on different AWS servers to all connect to our single, centralized <abbr title="Model Context Protocol">MCP</abbr> tool server simultaneously."
