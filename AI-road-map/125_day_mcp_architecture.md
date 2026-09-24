# Day 125: Model Context Protocol (MCP) Architecture

Welcome to Day 125. 

For the last 10 days, whenever we wanted our Agent to access a Tool (like a Calculator or a Database), we hardcoded the Python tool directly into our script. 
This works for toy apps, but it creates a massive architectural nightmare in production:
1. If you build 5 different Agents, you have to copy-paste the Tool code 5 times.
2. If you want your Agent to access your enterprise Postgres database, you have to hardcode your DB credentials directly into the Agent's environment. This is a massive security risk!

Today, we learn the revolutionary open standard that solves this: **The Model Context Protocol (MCP)**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The $M \times N$ Integration Problem
Before MCP, the AI industry was highly fragmented.
If a company used 5 AI Clients (Claude Desktop, a custom LangGraph agent, Cursor IDE) and wanted them to access 5 Data Sources (GitHub, Postgres, Slack, Jira, Google Drive), engineers had to write **25 custom API integrations**. Every LLM required a different tool schema format.

### 2. The MCP Solution (HTTP for AI)
Anthropic released MCP as an open standard to fix this. It is a Client-Server architecture.
- **MCP Clients:** The AI Agents (e.g., Claude Desktop or your LangGraph app). They don't know *how* to query a database or format a Slack message. They just know how to speak the "MCP Protocol" over JSON-RPC.
- **MCP Servers:** Lightweight, secure microservices that sit right next to your data. You deploy an "MCP Postgres Server" inside your secure VPC. The server holds the database credentials. 

### 3. Capability Negotiation & The 3 Primitives
When an MCP Client connects to an MCP Server, they perform a handshake. The Server tells the Client exactly what it can do using three primitives:
1. **Tools:** Executable functions the Agent can call (e.g., `query_database(sql="SELECT *")`).
2. **Resources:** Static data the Agent can read (e.g., `db://schema/users`).
3. **Prompts:** Pre-written templates provided by the server.

Because the Server generates the JSON schema and gives it to the Client dynamically, you write the Tool *once* on the Server, and *every* AI Agent in the world can instantly use it!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's simulate the JSON-RPC 2.0 message flow between an MCP Client (The Agent) and an MCP Server (The Data layer)!
*(Note: Tomorrow we will use the actual FastMCP SDK, but today we look at the raw protocol to understand the magic).*

Create a file named `mcp_architecture.py`:

```python
import json

def mock_mcp_server(request_json_str):
    """
    Simulates an MCP Server sitting securely inside a corporate VPC.
    It holds the database credentials. The Agent does NOT have the credentials.
    """
    request = json.loads(request_json_str)
    
    # 1. Capability Negotiation (Initialization)
    if request.get("method") == "initialize":
        print("[MCP SERVER] Received connection request. Sending capabilities...")
        return json.dumps({
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": True},
                    "resources": {}
                }
            }
        })
        
    # 2. Tool Discovery (Client asks: What tools do you have?)
    if request.get("method") == "tools/list":
        print("[MCP SERVER] Sending list of available tools to the Agent...")
        return json.dumps({
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {
                "tools": [
                    {
                        "name": "query_postgres",
                        "description": "Run a read-only SQL query on the production database.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"sql": {"type": "string"}},
                            "required": ["sql"]
                        }
                    }
                ]
            }
        })
        
    # 3. Tool Execution (Client asks Server to run a tool)
    if request.get("method") == "tools/call":
        tool_name = request["params"]["name"]
        sql_query = request["params"]["arguments"]["sql"]
        
        print(f"[MCP SERVER] Authenticating and executing '{tool_name}' with args: {sql_query}")
        # The Server securely executes the query using its own private credentials!
        mock_db_result = "ID: 1, Name: Alice, Role: Admin"
        
        return json.dumps({
            "jsonrpc": "2.0",
            "id": request["id"],
            "result": {
                "content": [{"type": "text", "text": mock_db_result}]
            }
        })

def run_mcp_simulation():
    print("--- RUNNING MCP PROTOCOL SIMULATION ---\n")
    
    # Step 1: The Client (Agent) connects to the Server
    init_request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
    init_response = mock_mcp_server(init_request)
    
    # Step 2: The Client asks what tools are available
    list_request = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    list_response = mock_mcp_server(list_request)
    
    print("\n[MCP CLIENT] Discovered Tools!")
    # The Client passes this schema to the LLM (e.g., GPT-4)
    # The LLM decides it needs to query the database!
    
    # Step 3: The Client tells the Server to execute the tool
    call_request = json.dumps({
        "jsonrpc": "2.0", 
        "id": 3, 
        "method": "tools/call", 
        "params": {
            "name": "query_postgres",
            "arguments": {"sql": "SELECT * FROM users LIMIT 1;"}
        }
    })
    print(f"\n[MCP CLIENT] Sending Tool Execution Request: {call_request}")
    
    call_response = mock_mcp_server(call_request)
    print(f"\n[MCP CLIENT] Received Final Result from Server: {json.loads(call_response)['result']['content'][0]['text']}")

if __name__ == "__main__":
    run_mcp_simulation()
```

### Key Takeaways from Code:
1. **Zero Hardcoding:** Notice that the Client did not have the schema for `query_postgres` hardcoded into its memory. It dynamically requested the schema from the server at runtime! If the Server updates its tool to require a new argument, the Client instantly adapts without any code changes!
2. **Security:** The database connection string and passwords exist *only* on the Server. If the Agent's laptop is compromised, the hacker does not get the database passwords, they only get an MCP connection that you can easily revoke!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Resource vs Tool
MCP distinguishes between Resources and Tools.
**Your Task:**
1. Conceptually define an MCP Server for GitHub.
2. **Tools** mutate state or require computation (e.g., `create_pull_request`, `search_codebase`).
3. **Resources** are static data that the Agent should just "read" (e.g., `github://repo/main/README.md`). 
4. Why is this distinction important? Because reading a Resource is fast, cheap, and safe. Executing a Tool is dangerous and usually requires Human-in-the-Loop approval!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"MCP standardizes tool use for LLMs. Compare this architecture to native Function Calling in the OpenAI SDK. Discuss protocol design trade-offs, security implications, and ecosystem effects."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Old Way (Native Function Calling):** 
   - State that native OpenAI function calling forces the application developer to maintain the tool definitions, handle execution, and manage secrets all within the same monolith application.
2. **The MCP Way (Decoupled Microservices):**
   - Explain that MCP moves tools *out* of the LLM application and into dedicated microservices. 
3. **Security & Ecosystem:**
   - Emphasize that MCP allows an enterprise to run a single `MCP-Jira-Server`. Then, the Data Science team's Jupyter notebooks, the Engineering team's Cursor IDEs, and the Marketing team's Claude Desktop can all securely connect to that *exact same server* without anyone having to share API keys or rewrite Jira logic!

---
**Task for the end of the day:** Commit your code to Git. 

We understand the JSON-RPC architecture of MCP. 
But writing JSON-RPC strings by hand is tedious. 

Tomorrow, in **Day 126**, we conclude our 20-Day block by building a production MCP Server using the blazing fast **FastMCP Python SDK**!
