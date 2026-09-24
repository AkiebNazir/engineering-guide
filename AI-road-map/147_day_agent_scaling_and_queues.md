# Day 147: Scaling Agents: Concurrent Execution, Queuing & Rate Limiting

Welcome to Day 147! 

Until now, we have been running our Python Agent scripts in a terminal. We type a prompt, wait 10 seconds, and get an answer. 
But what happens when you deploy this script as a FastAPI backend, and 500 users click "Submit" at the exact same time?
Your server will immediately crash. If it doesn't crash, the OpenAI API will block you with a `429 Too Many Requests` error.

Today, we transition from building standalone agents to building **Enterprise Agentic Services**. We will learn the architecture required to handle thousands of concurrent agent sessions without dropping a single request.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Bottlenecks of Agent Scaling
When 500 users hit a standard API (like a database lookup), the server handles it easily. But when 500 users trigger a LangGraph Agent, three catastrophic bottlenecks occur:
1. **Thread Blocking:** If an Agent runs a `while` loop that takes 30 seconds, it locks up the server's CPU threads. Other users must wait.
2. **API Rate Limits:** OpenAI allows (for example) 500 requests per minute (RPM). If 500 users trigger a ReAct agent that loops 5 times, that's 2,500 LLM calls. You hit the rate limit in 5 seconds.
3. **Tool Execution Timeouts:** If the agent decides to scrape a slow website using a tool, the HTTP connection might time out before the agent finishes.

### 2. The Solution: Queue-Based Architecture
To scale agents, you cannot use a synchronous `Request -> Response` architecture. You must use a **Queue Architecture**.

*Analogy:* Imagine a popular restaurant. If 500 people walk in and yell their orders at the single chef (the CPU), the chef panics and the restaurant burns down (Server Crash).
Instead, you use a Hostess (FastAPI). The Hostess takes the orders instantly, gives the customer a buzzer (Task ID), and puts the order on a Ticket Line (Redis Queue). The Chefs (Worker Pool) pull tickets from the line at their own pace. When an order is ready, the buzzer flashes (Result Streaming).

**The Architecture:**
1. User sends a request to FastAPI.
2. FastAPI pushes the job to a **Message Broker** (e.g., Redis, RabbitMQ, Kafka) and immediately returns a `task_id` to the user.
3. A pool of **Background Workers** (e.g., Celery) listens to the queue.
4. The workers execute the heavy LangGraph agent.
5. The frontend polls the server or listens to a WebSocket for the result.

### 3. Concurrency Patterns
- **Asyncio:** Used for I/O-bound tasks. If your agent is mostly waiting for LLM API responses or Web Scraping, `async` allows a single worker to handle 100 agents at once by swapping tasks while waiting for network responses.
- **Multiprocessing:** Used for CPU-bound tasks. If your agent is doing heavy local embedding calculations, you must spin up entirely separate Python processes.

### 4. Rate Limiting & Backpressure
- **Token Bucket Algorithm:** A bucket holds 500 tokens. Every LLM call costs 1 token. Tokens refill at 10 per second. If the bucket is empty, the worker pauses the agent.
- **Backpressure:** If the Redis queue hits 10,000 pending tasks, the FastAPI server tells new users: *"System busy, please try again."* This prevents the queue from crashing the server's RAM.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's mock a queue-based architecture using Python's `asyncio` and `Queue` to simulate how FastAPI and Celery/Redis interact.

*(Note: We use standard libraries to demonstrate the concept cleanly, but in production, `asyncio.Queue` is replaced by Redis).*

```python
import asyncio
import time
import random
from datetime import datetime

# --- 1. MOCK LANGGRAPH AGENT ---
async def execute_heavy_agent(task_id: int, query: str):
    print(f"[{datetime.now().strftime('%M:%S')}] ⚙️ Worker starting Agent Task #{task_id} for '{query}'...")
    
    # Simulating a multi-step agent loop (LLM call -> Tool -> LLM)
    for step in range(3):
        # Simulate network latency (I/O bound)
        await asyncio.sleep(random.uniform(0.5, 1.5))
        print(f"   -> Task #{task_id} finished step {step+1}/3")
        
    print(f"[{datetime.now().strftime('%M:%S')}] ✅ Task #{task_id} COMPLETE.")
    return f"Result for '{query}'"

# --- 2. THE BACKGROUND WORKER ---
async def worker(worker_id: int, queue: asyncio.Queue, rate_limit_semaphore: asyncio.Semaphore):
    while True:
        # 1. Pull a task from the queue
        task_id, query = await queue.get()
        
        # 2. Enforce Rate Limiting! 
        # The semaphore acts as the Token Bucket. If it's empty, the worker waits here.
        async with rate_limit_semaphore:
            try:
                await execute_heavy_agent(task_id, query)
            except Exception as e:
                print(f"Task {task_id} failed: {e}")
            finally:
                # 3. Tell the queue the task is done
                queue.task_done()

# --- 3. THE API GATEWAY (FASTAPI SIMULATION) ---
async def main_server_simulation():
    print("--- STARTING ENTERPRISE AGENT SERVER ---")
    
    # The Queue (Redis in production)
    task_queue = asyncio.Queue()
    
    # The Rate Limiter (Allows max 2 concurrent LLM executions globally)
    # This prevents us from hitting OpenAI's 429 Too Many Requests!
    global_rate_limiter = asyncio.Semaphore(2)
    
    # Spin up a pool of 5 Background Workers
    workers = []
    for i in range(5):
        task = asyncio.create_task(worker(i, task_queue, global_rate_limiter))
        workers.append(task)
        
    print("[SYSTEM] 5 Workers Online. Global Rate Limit set to 2 concurrent tasks.\n")
    
    # Simulate 10 users hitting the API at the exact same millisecond
    print("[API] Receiving 10 concurrent user requests!")
    for i in range(1, 11):
        # The API instantly accepts the request and pushes to the queue
        await task_queue.put((i, f"User Query {i}"))
        # In a real API, we would return `{"status": "queued", "task_id": i}` here!
        
    print("[API] All requests queued instantly. Server is not blocked!\n")
    
    # Wait for the queue to empty
    await task_queue.join()
    
    # Shut down workers
    for w in workers:
        w.cancel()
        
    print("--- ALL TASKS PROCESSED SUCCESSFULLY ---")

# To run:
# asyncio.run(main_server_simulation())
```

### 🔍 Understanding the Output
If you run this, you will notice something beautiful:
1. The API instantly accepts all 10 requests. It does not freeze!
2. Even though we have 5 workers, because of the `asyncio.Semaphore(2)` (our Rate Limiter), **only 2 agents execute at any given time.** 
3. As soon as one agent finishes, the next worker grabs the token and starts.
4. We successfully processed 10 heavy agent requests concurrently without crashing the server and without triggering an LLM API block!

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Refactor the mock server above to include a **Priority Queue**. 
Imagine you have "Free Users" and "Premium Users". 
Update the queue logic so that if a Premium User submits a request, it jumps to the front of the queue ahead of the 500 Free Users currently waiting. 
*(Hint: Look into `asyncio.PriorityQueue` and tuple sorting `(priority_level, task_id)`).*

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Your agent platform needs to handle 100,000 requests per hour with a p99 latency of 30 seconds. Design the scaling architecture including queuing, worker management, and auto-scaling."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **API Layer:** Stateless FastAPI instances behind a Load Balancer (AWS ALB). They do zero processing; they only validate Auth and push to Kafka/Redis.
2. **Message Broker:** Kafka or Redis Streams. It provides durability so if workers crash, messages aren't lost.
3. **Worker Pool:** A Kubernetes deployment of Celery/RQ workers that pull from the broker.
4. **Auto-Scaling (KEDA):** The workers must autoscale based on **Queue Depth**, not CPU. If there are 1,000 pending messages, Kubernetes spins up 50 more worker pods.
5. **State Storage:** Because workers are stateless, the LangGraph `MemorySaver` must be backed by a managed PostgreSQL instance to persist the agent states across nodes.
6. **Result Retrieval:** Workers push the final state to a Redis Pub/Sub channel, which streams back to the frontend via WebSockets.

---
**Task for the end of the day:** Review how Kafka and Redis Streams work at a high level. 

Tomorrow, in **Day 148**, we take this architecture and containerize it. We will learn how to wrap our agents in Docker and deploy them to a Kubernetes cluster for infinite horizontal scaling!
