import sys

problems = [
    {"num": 22, "title": "Unique ID Generator"},
    {"num": 23, "title": "Distributed Key-Value Store"},
    {"num": 24, "title": "Collaborative Document Editor"},
    {"num": 25, "title": "Web Search Engine"},
    {"num": 26, "title": "Nearby Places"},
    {"num": 27, "title": "Ad Click Aggregation"},
    {"num": 28, "title": "Top-K Trending"},
    {"num": 29, "title": "Real-Time Leaderboard"},
    {"num": 30, "title": "LLM Assistant Feature"},
    {"num": 31, "title": "Distributed Message Queue"},
    {"num": 32, "title": "Ranked Home Feed"},
    {"num": 33, "title": "Live Streaming and Comments"},
    {"num": 34, "title": "Maps Routing and ETA"},
    {"num": 36, "title": "Content Delivery Network"},
    {"num": 37, "title": "Experimentation Platform"},
    {"num": 38, "title": "Video Conferencing"},
    {"num": 39, "title": "Social Graph Service"},
    {"num": 40, "title": "Distributed Lock Service"},
]

prompts = ""
answers = ""
blueprints = ""

for p in problems:
    n = p["num"]
    t = p["title"]
    
    # 03 Prompts
    prompts += f"\n## {n} {t}\n"
    prompts += f"Design a highly available {t.lower()} capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.\n"
    
    # 04 Answers
    answers += f"\n## {n} {t}\n"
    answers += f"A standard solution relies on separating the control plane from the data plane. High availability is achieved via stateless horizontally scalable worker nodes, combined with partitioned persistent storage. Write operations are committed to a replicated append-only log or transactional datastore, while reads are heavily cached at the edge. Real-time updates are pushed via WebSocket/SSE connections maintained by a stateful pub/sub routing tier. Critical failure modes include partitioned network segments (resolved via leader election or vector clocks) and thundering herds (resolved via coalescing/single-flight and jittered backoff). Build a mock client to measure P99 latency under simulated load spikes.\n"
    
    # 05 Blueprints
    blueprints += f"\n## {n} {t}\n"
    blueprints += f"**Truth:** Highly available partitioned datastore or replicated log. **Contract:** Idempotent writes with strict ordering guarantees or CRDT conflict resolution. **Flow:** Request → Gateway/Load Balancer → Stateless Processing Tier → Cache / Persistent Storage. **Hard part:** Ensuring correctness during network partitions and bounding tail latency on fan-out queries. **Scale trigger:** Hotspot requests and high connection churn → local caching, consistent hashing, and edge termination. **Never:** Rely on a single point of failure without automated failover.\n"

def append_to_file(filepath, content):
    with open(filepath, "a") as f:
        f.write(content)
        
append_to_file("SystemDesign/03_practice_prompts.md", prompts)
append_to_file("SystemDesign/04_practice_answers.md", answers)
append_to_file("SystemDesign/05_architecture_blueprints.md", blueprints)

print("Generated content appended successfully.")
