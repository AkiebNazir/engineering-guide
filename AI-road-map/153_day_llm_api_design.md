# Day 153: <abbr title="Application Programming Interface">API</abbr> Design for <abbr title="Large Language Model">LLM</abbr> Services

Welcome to Day 153.

We have our highly optimized, quantized Llama-3 model running inside vLLM. But a model running in memory is useless if other applications cannot talk to it.

Today, we move up the stack to **<abbr title="Application Programming Interface">API</abbr> Design**. We will learn why the entire <abbr title="Artificial Intelligence">AI</abbr> industry adopted the OpenAI <abbr title="Application Programming Interface">API</abbr> Specification as a universal standard, and how to build a production-grade FastAPI gateway that features real-time token streaming via Server-Sent Events (<abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr>).

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The OpenAI-Compatible <abbr title="Application Programming Interface">API</abbr> Standard
When OpenAI launched ChatGPT, they created an <abbr title="Application Programming Interface">API</abbr> structure that was so clean, the entire open-source community adopted it as the universal standard. 
If you build your internal <abbr title="Application Programming Interface">API</abbr> to exactly match OpenAI's schema, your engineers can use the standard Python `openai` package to talk to your custom Llama-3 models. They just change the `base_url`!

**The Standard Endpoints:**
- `GET /v1/models`: Lists available models.
- `POST /v1/chat/completions`: The core generation endpoint.
- `POST /v1/embeddings`: Generates vector embeddings.

### 2. The Request Schema
To be compatible, your `/chat/completions` endpoint must accept a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> payload exactly like this:
```json
{
  "model": "meta-llama/Meta-Llama-3-8B",
  "messages": [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "stream": true
}
```

### 3. Server-Sent Events (<abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr>) vs WebSockets
If `stream: false`, the server waits 10 seconds to generate the full answer, then returns a massive <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> blob. This is terrible UX.
If `stream: true`, we use **Server-Sent Events (<abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr>)**.
- **WebSockets** are bi-directional (like a phone call). They are overkill for LLMs.
- **<abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr>** is uni-directional over standard <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> (like a radio broadcast). The client sends one request, and the server keeps the connection open, trickling down chunks of text as soon as the GPU generates them.

### 4. <abbr title="Application Programming Interface">API</abbr> Gateways & Security
Your raw vLLM server should never be exposed to the public internet. It sits behind an **<abbr title="Application Programming Interface">API</abbr> Gateway** (like Kong, Nginx, or a custom FastAPI wrapper).
The Gateway handles:
- **Authentication:** Validating Bearer <abbr title="Application Programming Interface">API</abbr> Keys.
- **Rate Limiting:** Blocking users who exceed 50 requests/minute.
- **Cost Attribution:** Logging every token generated so Finance can bill specific teams.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a custom, OpenAI-Compatible <abbr title="Application Programming Interface">API</abbr> Gateway using FastAPI. It will authenticate the user, translate the standard OpenAI request into our mock model, and stream the response back using <abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr>!

*(Note: To run this code, you would need `pip install fastapi uvicorn sse-starlette`)*

```python
import asyncio
from fastapi import FastAPI, Depends, HTTPException, Header
from pydantic import BaseModel
from typing import List, Optional
from sse_starlette.sse import EventSourceResponse

app = FastAPI(title="Enterprise LLM Gateway")

# --- 1. THE OPENAI-COMPATIBLE SCHEMAS ---

class Message(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

# --- 2. SECURITY & AUTHENTICATION ---

def verify_api_key(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer Token")
    
    token = authorization.split(" ")[1]
    if token != "super-secret-enterprise-key":
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return "team_alpha" # Returns the authenticated user/team

# --- 3. MOCK LLM ENGINE ---

async def mock_llm_generator(prompt: str):
    """Simulates a GPU generating tokens one by one."""
    fake_response = f"This is a simulated streaming response to your prompt."
    words = fake_response.split(" ")
    
    for word in words:
        await asyncio.sleep(0.1) # Simulate GPU compute time
        yield word + " "

# --- 4. THE CORE ENDPOINT ---

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest, 
    user: str = Depends(verify_api_key)
):
    print(f"[GATEWAY] Request from {user} for model {request.model}")
    
    # Extract the last user message
    user_query = request.messages[-1].content
    
    # If the user doesn't want streaming, wait and return the full JSON
    if not request.stream:
        full_text = ""
        async for chunk in mock_llm_generator(user_query):
            full_text += chunk
            
        return {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "model": request.model,
            "choices": [{
                "message": {"role": "assistant", "content": full_text.strip()},
                "finish_reason": "stop"
            }],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        }

    # --- 5. SERVER-SENT EVENTS (STREAMING) ---
    async def sse_generator():
        # SSE requires a very specific string format: "data: {json}\n\n"
        async for chunk in mock_llm_generator(user_query):
            
            # The exact JSON structure OpenAI uses for streaming chunks!
            chunk_data = {
                "id": "chatcmpl-123",
                "object": "chat.completion.chunk",
                "model": request.model,
                "choices": [{
                    "delta": {"content": chunk}, # Note it's 'delta', not 'message'!
                    "index": 0,
                    "finish_reason": None
                }]
            }
            yield chunk_data
            
        # Send the final stop sequence
        yield {
            "id": "chatcmpl-123",
            "object": "chat.completion.chunk",
            "model": request.model,
            "choices": [{"delta": {}, "index": 0, "finish_reason": "stop"}]
        }
        yield "[DONE]" # OpenAI spec requires sending [DONE] at the very end.

    # Return the SSE Streaming Response
    return EventSourceResponse(sse_generator())

# To run: uvicorn main:app --reload
```

### 🔍 Understanding the Enterprise Value

If you run this FastAPI server, you can literally open a Jupyter notebook, `pip install openai`, set `openai.api_key = "super-secret-enterprise-key"`, and set `openai.base_url = "http://localhost:8000/v1"`. 

The official OpenAI Python client will successfully authenticate with your server, send the prompt, and parse the <abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr> streaming response flawlessly! You have just built a drop-in replacement for OpenAI!

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Currently, our <abbr title="Application Programming Interface">API</abbr> Gateway has no Rate Limiting.
Modify the FastAPI code to implement a **Token Bucket Rate Limiter**. Use a Redis backend (or a simple Python dictionary in memory) to track how many requests `team_alpha` has made in the last minute. If they exceed 10 requests, raise an `HTTPException(status_code=429, detail="Too Many Requests")`.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Design the <abbr title="Application Programming Interface">API</abbr> Gateway layer for a multi-tenant <abbr title="Large Language Model">LLM</abbr> platform. You serve 500 different enterprise teams. Some teams have higher rate limits. Some teams are only allowed to access cheap 8B models, while others can access expensive 70B models. How do you attribute costs at the end of the month?"*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The Gateway Architecture:** A centralized FastAPI (or Go) Gateway sitting in front of isolated vLLM clusters.
2. **Authentication & RBAC:** The Gateway intercepts the Bearer token, queries a fast cache (Redis) to get the team's profile (Tier, Allowed Models, Rate Limit).
3. **Model Routing:** If the user requests `Llama-70B`, the Gateway checks permissions. If allowed, it acts as a Reverse Proxy, forwarding the request to the internal Kubernetes service hosting the 70B cluster.
4. **Usage Tracking (FinOps):** The vLLM cluster returns the `usage` metrics (`prompt_tokens`, `completion_tokens`) at the very end of the stream. The Gateway intercepts this <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>, appends the `team_id`, and fires an async Kafka event. A billing microservice consumes the Kafka event and updates the team's monthly invoice in PostgreSQL.

---
**Task for the end of the day:** Review how <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> Server-Sent Events (<abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr>) work at the protocol level.

Tomorrow, in **Day 154**, we move to massive scale hardware. We will learn **GPU Cluster Management**, including Tensor Parallelism and Pipeline Parallelism!
