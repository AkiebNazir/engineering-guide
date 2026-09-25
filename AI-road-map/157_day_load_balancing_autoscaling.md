# Day 157: Load Balancing, Auto-Scaling & Traffic Management

Welcome to Day 157.

Imagine you build a successful <abbr title="Artificial Intelligence">AI</abbr> application. You launch it on Product Hunt. Traffic spikes from 10 requests per minute to 10,000 requests per minute. 
If your infrastructure is static, your vLLM nodes will OOM (Out of Memory) and crash. 

Today, we learn how to architect **Traffic Management Systems**. We will learn how to intelligently distribute traffic (Load Balancing) and how to automatically spin up massive GPU clusters exactly when you need them, and spin them down when you don't (Auto-Scaling).

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Load Balancing LLMs (The "Tokens in Flight" Problem)
*Analogy:* You have 3 grocery store checkout lanes (GPUs). A standard load balancer uses "Round Robin"—it sends Customer 1 to Lane A, Customer 2 to Lane B, Customer 3 to Lane C.
But what if Customer 1 has a cart with 500 items (a 30,000 token prompt), and Customers 2 and 3 have 1 item each? If you use Round Robin, Lane A will be choked for 10 minutes while B and C sit idle!

<abbr title="Large Language Model">LLM</abbr> Load Balancing is incredibly difficult because request sizes vary wildly.
**Least-Tokens-In-Flight (LTIF) Routing:** The Load Balancer constantly queries the vLLM nodes: *"How many tokens are you currently processing?"* It routes new requests to the GPU with the fewest tokens currently in memory, maximizing throughput.

### 2. Auto-Scaling with Kubernetes HPA
The Kubernetes **Horizontal Pod Autoscaler (HPA)** automatically increases the number of vLLM Pods when traffic spikes.
- **CPU Scaling (Flawed):** Scaling based on CPU is a bad idea for LLMs, because inference is heavily bottlenecked by GPU VRAM, not CPU.
- **GPU Scaling (Better):** You can configure HPA to scale when GPU Utilization hits >85%.
- **Queue Scaling (Best):** Using **KEDA (Kubernetes Event-driven Autoscaling)**, you configure <abbr title="Kubernetes">K8s</abbr> to watch a Redis Queue. If there are 500 pending requests in the queue, <abbr title="Kubernetes">K8s</abbr> instantly spins up 10 new GPU pods to chew through the backlog.

### 3. The Cold Start Problem
If traffic spikes and Kubernetes requests a new GPU pod, it takes time.
1. AWS must provision a physical GPU instance (1-2 minutes).
2. Docker must pull the massive 20GB vLLM image (1 minute).
3. vLLM must load 140GB of model weights into VRAM (2 minutes).
This 5-minute **Cold Start** is a killer. By the time the GPU is ready, the users have already abandoned your site!
**Solution:** Keep a baseline of "Warm" GPUs running 24/7. When traffic starts rising, scale *proactively* (predictive scaling) rather than reactively.

### 4. Circuit Breakers & Backpressure
If traffic exceeds your maximum scaling budget (e.g., you hard-capped <abbr title="Kubernetes">K8s</abbr> at 20 GPUs so you don't go bankrupt), you must apply **Backpressure**.
The <abbr title="Application Programming Interface">API</abbr> Gateway monitors the queue. If the queue hits 1,000 requests, it instantly returns an `HTTP 503 Service Unavailable: High Load` to new users. It is better to reject new users instantly than to let them wait 10 minutes and crash the system for everyone.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

We cannot launch a multi-GPU cluster locally, but we can build a conceptual **<abbr title="Large Language Model">LLM</abbr> Load Balancer** in Python that implements "Least-Tokens-in-Flight" routing instead of naive Round Robin!

```python
import time
import random
import threading

# --- 1. MOCK vLLM NODE ---
class MockVLLMNode:
    def __init__(self, node_id):
        self.node_id = node_id
        # Tracks how much work this node is currently doing
        self.active_tokens_in_flight = 0 
        self.lock = threading.Lock()

    def process_request(self, tokens: int):
        with self.lock:
            self.active_tokens_in_flight += tokens
            
        print(f"   [NODE {self.node_id}] Accepted {tokens} tokens. Total in flight: {self.active_tokens_in_flight}")
        
        # Simulate processing time (more tokens = more time)
        time.sleep(tokens / 1000.0) 
        
        with self.lock:
            self.active_tokens_in_flight -= tokens
        print(f"   [NODE {self.node_id}] Finished. Total in flight: {self.active_tokens_in_flight}")

# --- 2. THE INTELLIGENT LOAD BALANCER ---
class LLMLoadBalancer:
    def __init__(self, nodes):
        self.nodes = nodes

    def get_best_node(self):
        """
        The Magic Algorithm:
        Instead of picking randomly, we iterate through all nodes and pick 
        the one with the lowest 'active_tokens_in_flight'.
        """
        best_node = None
        lowest_tokens = float('inf')
        
        for node in self.nodes:
            if node.active_tokens_in_flight < lowest_tokens:
                lowest_tokens = node.active_tokens_in_flight
                best_node = node
                
        return best_node

    def route_request(self, request_id: int, tokens: int):
        best_node = self.get_best_node()
        print(f"\n[ROUTER] Request {request_id} ({tokens} tokens) -> Routed to NODE {best_node.node_id}")
        
        # Dispatch the work to the node in a background thread
        threading.Thread(target=best_node.process_request, args=(tokens,)).start()

# --- 3. SIMULATION ---
def run_traffic_simulation():
    print("--- STARTING TRAFFIC SIMULATION ---")
    
    # We have 3 GPU Nodes
    nodes = [MockVLLMNode("A"), MockVLLMNode("B"), MockVLLMNode("C")]
    router = LLMLoadBalancer(nodes)
    
    # 1. A massive request comes in
    router.route_request(1, 5000) # Takes 5 seconds
    time.sleep(0.5)
    
    # 2. A bunch of small requests come in
    # Because Node A is choked with 5000 tokens, the router will cleanly 
    # distribute these small requests entirely to Nodes B and C!
    router.route_request(2, 500)
    router.route_request(3, 500)
    router.route_request(4, 500)
    
    time.sleep(6) # Wait for simulation to finish
    print("--- SIMULATION COMPLETE ---")

# To run:
# run_traffic_simulation()
```

### 🔍 Understanding the Advantage
If we used Round Robin, Request 4 would have been routed to Node A, getting stuck behind the massive 5,000 token request. By querying `active_tokens_in_flight`, our router dynamically avoided the bottleneck, ensuring low latency for everyone!

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Modify the script above to include a **Circuit Breaker / Backpressure** mechanism.
If ALL nodes have `active_tokens_in_flight > 8000`, the `route_request` function should immediately `raise Exception("503 Service Unavailable: Cluster at maximum capacity")`. Test it by firing ten 5,000-token requests instantly.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Your <abbr title="Large Language Model">LLM</abbr> service has unpredictable traffic: a 100 req/min baseline, but massive spikes to 10,000 req/min during marketing launches. You are paying $10/hour per GPU. Design the auto-scaling architecture with cost optimization (you can't just keep 1,000 GPUs idle 24/7)."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The Baseline:** Keep a baseline of 5 GPUs running 24/7 on AWS Reserved Instances (cheaper) to handle the 100 req/min traffic with zero latency.
2. **The Auto-Scaler (KEDA):** Configure Kubernetes to scale based on **Queue Depth**, not CPU.
3. **Spot Instances:** Configure the Kubernetes Autoscaler to spin up **Spot/Preemptible Instances** for the spike traffic. Spot instances are 70% cheaper, but can be terminated by AWS randomly.
4. **Fault Tolerance:** Because Spot instances can vanish, the architecture must be strictly queue-based. If a Spot GPU dies mid-generation, the message must remain unacknowledged in the Redis Queue so another GPU can pick it up seamlessly.
5. **Cold Start Mitigation:** Implement a "predictive" scaling algorithm that watches traffic velocity. If traffic is increasing 20% minute-over-minute, spin up GPUs *before* the queue gets clogged, anticipating the 5-minute GPU startup delay.

---
**Task for the end of the day:** Read up on **KEDA** (Kubernetes Event-driven Autoscaling). It is the industry standard for scaling <abbr title="Artificial Intelligence">AI</abbr> workloads.

Tomorrow, in **Day 158**, we switch from Infrastructure to **Prompt Engineering for Production**. We will learn how to version control prompts and automatically optimize them using Stanford's DSPy!
