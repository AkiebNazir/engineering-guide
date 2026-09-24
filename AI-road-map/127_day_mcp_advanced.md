# Day 127: MCP Advanced (Transports, Security, & Composition)

Welcome to Day 127. In the previous block, we introduced the Model Context Protocol (MCP) and built a basic FastMCP server over `stdio`.

In a true Enterprise environment, running a server over `stdio` on your local laptop is not viable. You need cloud-hosted servers, strict authentication, and complex architectures where servers talk to other servers. 

Today, we dive into the advanced mechanics of MCP: **Authentication, Server Composition, and Sampling**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Advanced Transports (SSE & HTTP)
MCP Clients and Servers communicate via JSON-RPC, but the *Transport Layer* can vary:
- **stdio:** The Client spawns the Server locally. Perfect for local IDEs (like Cursor).
- **SSE (Server-Sent Events):** The Server lives on the internet (e.g., AWS). The Client connects via HTTP. The Server uses SSE to push messages *down* to the Client asynchronously. 
- **Streamable HTTP:** The newest standard. It supports bidirectional streaming, allowing massive files (like gigabyte PDFs) to be streamed from the Server to the Client in chunks.

### 2. Authentication & Authorization
The MCP protocol *itself* does not define authentication. It relies on the Transport layer.
If you deploy an MCP server using SSE, you secure it using standard web protocols (like **OAuth 2.0**). The AI Client must send an `Authorization: Bearer <token>` header. 
The Server validates the token, extracts the `user_id`, and enforces **Authorization** (e.g., *"Does User 42 have permission to execute this Jira tool?"*).

### 3. Server Composition (The Proxy Pattern)
Imagine a Fortune 500 company with 50 different MCP servers (HR, Finance, Jira, GitHub). 
If an employee's AI Agent has to connect to 50 servers individually, the networking overhead is immense.
**Server Composition:** You deploy one massive "Gateway" or "Proxy" MCP Server. The AI Agent connects only to the Gateway. The Gateway dynamically aggregates the Tools and Resources from the 50 underlying micro-servers and presents them to the Agent as one unified toolkit!

### 4. Sampling (Reverse Tool Use)
Normally, the Agent (Client) calls the Server. 
**Sampling** reverses this. What if the Server needs a little bit of "intelligence" while executing a tool? 
The Server can pause its execution, send a `sampling/createMessage` request *back* to the Client, ask the LLM to summarize a string, receive the summary, and then finish executing the tool!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's conceptually build a Secure MCP Proxy Server using Python. We will mock the HTTP headers to demonstrate how authentication and routing work in an enterprise MCP gateway.

Create a file named `mcp_advanced.py`:

```python
import json

class SecureMCPGateway:
    def __init__(self):
        # The Gateway knows about the internal micro-servers
        self.internal_servers = {
            "hr_server": ["get_payroll", "request_pto"],
            "eng_server": ["query_github", "deploy_code"]
        }
        
        # A mock database of user permissions
        self.user_permissions = {
            "token_alice_engineer": ["eng_server"],
            "token_bob_manager": ["hr_server", "eng_server"]
        }

    def _authenticate(self, auth_header):
        """Extracts the Bearer token and returns the User Identity."""
        if not auth_header or not auth_header.startswith("Bearer "):
            raise Exception("401 Unauthorized: Missing Bearer Token")
        token = auth_header.split(" ")[1]
        if token not in self.user_permissions:
            raise Exception("403 Forbidden: Invalid Token")
        return token

    def handle_request(self, auth_header, request_json):
        """Simulates handling an incoming HTTP/SSE MCP Request."""
        try:
            user_token = self._authenticate(auth_header)
            request = json.loads(request_json)
            
            # 1. Gateway dynamically builds the Tool List based on User Permissions!
            if request["method"] == "tools/list":
                allowed_servers = self.user_permissions[user_token]
                available_tools = []
                
                for server in allowed_servers:
                    available_tools.extend(self.internal_servers[server])
                    
                print(f"[GATEWAY] User '{user_token}' requested tools.")
                print(f"[GATEWAY] Dynamically composing tools: {available_tools}")
                
                return {"jsonrpc": "2.0", "id": request["id"], "result": {"tools": available_tools}}
                
            # 2. Gateway routes the Tool Call to the correct internal server
            if request["method"] == "tools/call":
                tool_name = request["params"]["name"]
                
                # Check authorization
                allowed_servers = self.user_permissions[user_token]
                is_authorized = any(tool_name in self.internal_servers[srv] for srv in allowed_servers)
                
                if not is_authorized:
                    return {"error": f"403: You do not have permission to use {tool_name}"}
                    
                print(f"[GATEWAY] Routing '{tool_name}' execution to internal micro-service...")
                return {"jsonrpc": "2.0", "id": request["id"], "result": {"content": "Tool Executed Successfully."}}

        except Exception as e:
            return {"error": str(e)}

def run_advanced_simulation():
    print("--- RUNNING ENTERPRISE MCP GATEWAY SIMULATION ---\n")
    
    gateway = SecureMCPGateway()
    
    print("Scenario 1: Alice (Engineer) connects to the Gateway.")
    alice_header = "Bearer token_alice_engineer"
    list_req = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    
    alice_response = gateway.handle_request(alice_header, list_req)
    print(f"Alice sees tools: {alice_response['result']['tools']}\n")
    
    print("Scenario 2: Alice tries to run a Payroll tool (Unauthorized!)")
    hack_req = json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "get_payroll"}})
    hack_res = gateway.handle_request(alice_header, hack_req)
    print(f"Gateway Response: {hack_res}\n")
    
    print("Scenario 3: Bob (Manager) connects. He sees everything.")
    bob_header = "Bearer token_bob_manager"
    bob_response = gateway.handle_request(bob_header, list_req)
    print(f"Bob sees tools: {bob_response['result']['tools']}")

if __name__ == "__main__":
    run_advanced_simulation()
```

### Key Takeaways from Code:
1. **Dynamic Capability Negotiation:** The list of tools an Agent sees is entirely dependent on the *human user* driving the Agent. This is crucial for enterprise security. The LLM cannot hallucinate its way into a payroll database if the Gateway refuses to even show the LLM that the payroll tool exists!
2. **The Proxy Abstraction:** The Agent has no idea that `hr_server` and `eng_server` exist. It only talks to the Gateway. This allows backend engineers to refactor the internal microservices without breaking the AI Clients.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Sampling Server
You are building an MCP Server that reads 500-page legal PDFs (Resource). 
**Your Task:**
1. Conceptually design a `summarize_contract` tool on the Server.
2. The Server cannot process 500 pages itself. 
3. Design the flow where the Server uses **Sampling** to send 10 pages at a time *back* to the LLM Client, asking the LLM to summarize them, before the Server aggregates the 50 summaries and returns the final result.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"An MCP server has access to your production Postgres database via a `run_query` tool. How do you prevent SQL injection through LLM-generated queries, prevent unauthorized data access, and prevent accidental data modification? Design the complete security model."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Preventing Modification (Read-Only Replicas):** 
   - State that the MCP server MUST connect to a strictly read-only database replica. Never allow a generic `run_query` tool to connect to the master write-database.
2. **Preventing SQL Injection (No Raw SQL):**
   - Emphasize that exposing raw SQL execution to an LLM is a fatal flaw. 
   - Propose abstracting the tool: Instead of `run_query(sql_string)`, the tool should be `get_users_by_status(status: str)`. The MCP server uses parameterized SQL internally (e.g., `SELECT * FROM users WHERE status = ?`), completely neutralizing SQL injections.
3. **Preventing Unauthorized Access (Row-Level Security):**
   - The MCP Server must extract the `user_id` from the OAuth Bearer token.
   - The server must inject that `user_id` into every database query (e.g., `AND owner_id = 42`) to enforce Multi-Tenant Row-Level Security, ensuring the LLM can only query data belonging to the user making the request.

---
**Task for the end of the day:** Commit your code to Git. 

We have mastered MCP and how to connect Agents to Data securely. 
But how do we manage multiple Agents working together as a cohesive team? 
LangGraph requires manually wiring nodes. Is there a higher-level abstraction?

Tomorrow, in **Day 128**, we learn **CrewAI**, the orchestrator that treats Agents like human employees!
