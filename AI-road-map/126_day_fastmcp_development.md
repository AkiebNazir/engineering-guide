# Day 126: FastMCP Server Development

Welcome to Day 126. This is the final day of your current 20-day learning block!

Yesterday, we learned the raw JSON-RPC 2.0 architecture of the Model Context Protocol (MCP). Writing raw JSON strings by hand is tedious.
Today, we learn the **FastMCP Python SDK**. Just as `FastAPI` revolutionized web development by using Python type hints to automatically generate OpenAPI documentation, `FastMCP` automatically generates MCP Schemas!

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The FastMCP SDK
FastMCP is the official Python SDK built by Anthropic. It allows you to expose enterprise data and tools to *any* AI Agent with just a few lines of code.

### 2. The Magic of Decorators
You do not write JSON schemas in FastMCP. You just write standard Python functions!
- **`@mcp.tool()`:** You add this decorator above a Python function. FastMCP uses Python's `inspect` module to read your function's signature and docstring, and automatically generates the perfect JSON Schema for the LLM!
- **`@mcp.resource()`:** You use this to expose static data (like a log file or a database table). You assign it a URI like `logs://app/system.log`.
- **`@mcp.prompt()`:** You use this to define complex, pre-written prompt templates that the LLM Client can pull from the server.

### 3. Transports (How they talk)
How does the Claude Desktop app actually talk to your FastMCP server?
- **stdio (Standard I/O):** The easiest method. The LLM Client physically spawns your Python script as a subprocess on your local machine and sends JSON messages via the terminal's standard input/output.
- **SSE (Server-Sent Events) over HTTP:** The production method. You deploy the FastMCP server to the cloud. The LLM Client connects over the internet using a persistent HTTP connection.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a production-grade FastMCP Server for a Data Analytics Platform!
*(Note: To run this in real life, you would `pip install fastmcp` and run `mcp dev server.py`).*

Create a file named `fastmcp_analytics_server.py`:

```python
# MOCKING FastMCP for the code-along
class MockFastMCP:
    def __init__(self, name):
        self.name = name
        self.tools = {}
        self.resources = {}
        
    def tool(self):
        def decorator(func):
            # FastMCP magic: extracting the docstring to build the JSON schema!
            self.tools[func.__name__] = func.__doc__
            return func
        return decorator
        
    def resource(self, uri):
        def decorator(func):
            self.resources[uri] = func
            return func
        return decorator

# --- START OF FASTMCP SERVER CODE ---

mcp = MockFastMCP("Enterprise Analytics Server")

# 1. A Resource (Static Data)
@mcp.resource("data://datasets/users")
def get_user_dataset() -> str:
    """Returns the schema of the main users dataset."""
    return "Columns: id (int), username (str), revenue (float), is_active (bool)"

# 2. A Tool (Actionable Command)
@mcp.tool()
def execute_sql_analytics(query: str, limit: int = 10) -> str:
    """
    Run an analytics SQL query against the read-only replica database.
    WARNING: Only SELECT statements are allowed.
    
    Args:
        query: The SQL query to execute.
        limit: Max number of rows to return (default 10).
    """
    query = query.lower()
    if "drop" in query or "delete" in query or "update" in query:
        # Returning an error string so the LLM knows it messed up!
        return "Error: Tool only supports SELECT queries on the analytics replica."
        
    print(f"[FASTMCP EXECUTING TOOL] Running: {query} LIMIT {limit}")
    return f"Result: Retrieved {limit} rows showing $5000 in revenue."

# 3. Another Tool (Chart Generation)
@mcp.tool()
def generate_revenue_chart(timeframe: str) -> str:
    """
    Generates a matplotlib chart of revenue over the given timeframe.
    Args:
        timeframe: 'daily', 'weekly', or 'monthly'
    """
    print(f"[FASTMCP EXECUTING TOOL] Generating {timeframe} chart...")
    # In reality, this would return a base64 encoded image!
    return "[BASE64_IMAGE_STRING_HERE]"

def simulate_fastmcp_startup():
    print(f"--- STARTING FASTMCP SERVER: '{mcp.name}' ---\n")
    
    print("FastMCP automatically built the following schemas from your Python code:")
    print("\nRESOURCES:")
    for uri, func in mcp.resources.items():
        print(f" - {uri}")
        
    print("\nTOOLS:")
    for name, doc in mcp.tools.items():
        print(f" - {name}()")
        print(f"   Schema derived from: '{doc.strip().split(chr(10))[0]}'")
        
    print("\n[FASTMCP] Server listening on stdio. Any MCP Client (Claude, Cursor, LangGraph) can now instantly use these tools!")

if __name__ == "__main__":
    simulate_fastmcp_startup()
```

### Key Takeaways from Code:
1. **Developer Experience (DX):** Notice how clean the code is. You did not write a single line of JSON-RPC routing logic. FastMCP handles the entire networking layer for you.
2. **Type Hints are Mandatory:** FastMCP strictly requires Python Type Hints (`query: str`, `limit: int`). If you do not provide them, FastMCP cannot generate the JSON schema, and the LLM will not know what arguments to pass!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The GitHub Wrapper Server
You can build an MCP Server that wraps third-party REST APIs.
**Your Task:**
1. Conceptually design an MCP Server for GitHub.
2. Define a `@mcp.tool()` called `create_issue(repo: str, title: str, body: str)`.
3. Inside the Python function, use the standard `requests` library to POST to `api.github.com`.
4. Implement Error Handling: If the GitHub API returns a 429 Rate Limit error, the function should return a string: `"Error 429: Rate limit exceeded. Please wait 60 seconds."` This explicitly tells the LLM exactly why the tool failed so it can self-correct!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are building an MCP ecosystem for a Fortune 500 company. 50 internal microservices need to be exposed as MCP tools. Design the architecture: Server Registry, Authentication, Rate Limiting, and Versioning."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Server Registry:** 
   - Propose an internal Developer Portal where teams register their MCP Servers. Clients ping the Registry to dynamically discover new servers.
2. **Authentication (SSE/HTTP):**
   - State that `stdio` transport is useless for a massive company. You must deploy the servers using `SSE (Server-Sent Events)`.
   - Propose using standard OAuth 2.0. The AI Agent must pass a Bearer Token when connecting to the MCP Server.
3. **Rate Limiting & Blast Radius:**
   - Warn that an Agent trapped in an infinite loop could DDoS your internal databases by calling a tool 1,000 times a second.
   - Propose implementing a strict Redis-backed Rate Limiter in the FastMCP server, capping tool executions to 10 requests per minute per AI Agent.

---
### 🎉 CONGRATULATIONS ON COMPLETING YOUR 20-DAY SPRINT!
You have now covered Days 107 through 126!
You have mastered Model Merging, Speculative Decoding, LangGraph orchestration, and the Model Context Protocol.

You are now fully equipped to build Enterprise Agentic Systems. 
**End of Chunk 10.**
