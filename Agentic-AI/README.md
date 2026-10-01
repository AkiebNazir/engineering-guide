# The Ultimate Guide to Agentic AI and Related Technologies

Welcome to the **Ultimate Guide to Agentic AI**. This repository is designed to take you from the foundational concepts of Generative AI all the way to advanced Agentic AI architectures, RAG systems, and Graph databases.

## Modules

This guide is broken down into 10 modules, each with deep-dive technical explanations, diagrams, runnable Python reference code and a self-check. Modules 1–5 cover the model and its knowledge; 6–8 the protocols agents talk over; 9–10 what it takes to evaluate, operate and ship an agent.

1. [**Generative AI: LLM Architecture & Runtime Internals**](01_generative_ai_internals.md)
   Dive deep into scaled dot-product attention, KV cache memory footprint, and the core mechanics of transformer-based LLMs.
2. [**Agentic AI Internals: Planning, Tools & Memory**](02_agentic_ai_internals.md)
   Understand how LLMs transition from text generators to autonomous agents using constrained decoding, tool-calling loops, and memory architectures.
3. [**Retrieval-Augmented Generation: RAG Internals**](03_rag_deep_dive.md)
   Learn the mechanics of BM25, dense embeddings, cosine similarity, and Reciprocal Rank Fusion (RRF) for building robust RAG systems.
4. [**Vector Databases: Vector Indexing & Storage Engines**](04_vector_databases_internals.md)
   Explore how vector databases work under the hood, including k-means clustering, Voronoi cells, inverted lists (IVF), and distance metrics.
5. [**Graph Databases & GraphRAG: Knowledge Representation & Traversal**](05_graph_databases_and_graphrag.md)
   Master index-free adjacency and how to extract and traverse knowledge graphs for advanced reasoning tasks (GraphRAG).
6. [**Protocol Buffers & gRPC: Typed, Streaming RPC for AI Services**](06_protocol_buffers_and_grpc.md)
   The Protobuf wire format byte by byte, schema evolution for rolling deploys, and gRPC streams, deadlines, cancellation and load balancing for embedding and inference services. Includes a from-scratch encoder and a live `grpcio` demo.
7. [**Multi-Agent Orchestration & MCP**](07_multi_agent_and_mcp.md)
   Orchestration patterns (supervisor, hierarchical, handoff, blackboard), shared state and reducers, budgets and failure modes; then the Model Context Protocol end to end: JSON-RPC lifecycle, transports, tools/resources/prompts, sampling, OAuth, and MCP security.
8. [**API Architectures: REST, GraphQL, gRPC, WebSockets & SSE**](08_api_architectures_engineering_guide.md)
   What each API style puts on the wire and the HTTP semantics that decide caching and retries, with five mechanics per style in Python and Go and a standard-library reference implementation.
9. [**Evaluation, Observability & Guardrails**](09_evaluation_observability_and_guardrails.md)
   Golden sets, code graders, LLM-as-judge and its biases, pass^k and confidence intervals, tracing agent runs with the OpenTelemetry GenAI conventions, cost and latency metrics, guardrails and prompt-injection defences.
10. [**Deploying Agents in Production**](10_deploying_agents_in_production.md)
   Rate limits, retries and timeouts, circuit breakers and fallbacks, caching, streaming, queues and durable execution for long tasks, human-in-the-loop approval, sandboxing, secrets, rollout and rollback of prompts and models, and cost control.

## Practice Projects

To solidify your understanding, we have provided hands-on projects. Each project comes with two files:
- `*_project.md`: The problem statement, design requirements, and a challenge for you to try building it yourself.
- `*_project_solution.py`: A full-fledged, running Python solution. These solutions are designed to work with **Local Models** (e.g., via Ollama or HuggingFace) by default, but can easily be configured to use cloud APIs (like Gemini or OpenAI) by providing your API keys.

### Foundational Projects
1. **Basic RAG Pipeline**
   - Challenge: [Project 1: Basic Retrieval-Augmented Generation (RAG) Pipeline](projects/01_basic_rag_project.md)
   - Solution: [projects/01_basic_rag_project_solution.py](projects/01_basic_rag_project_solution.py)
2. **ReAct Agent from Scratch**
   - Challenge: [Project 2: ReAct Agent from Scratch](projects/02_react_agent_project.md)
   - Solution: [projects/02_react_agent_project_solution.py](projects/02_react_agent_project_solution.py)
3. **Mini GraphRAG Extractor**
   - Challenge: [Project 3: Mini GraphRAG Knowledge Extractor](projects/03_graphrag_project.md)
   - Solution: [projects/03_graphrag_project_solution.py](projects/03_graphrag_project_solution.py)

### Advanced Enterprise Capstone Projects
For a more advanced challenge, consider exploring or building these enterprise-grade architectures:

1. **Enterprise AI Infrastructure (MCP & Local Inference)** — [projects/04_enterprise_ai_infrastructure/](projects/04_enterprise_ai_infrastructure/)
   - **Goal**: Develop Python-based MCP (Model Context Protocol) Servers to standardize connectivity between AI Agents and backend systems (bridged via Golang). Architect a private inference layer using Python (vLLM) to host open-source models (DeepSeek-R1 / Hugging Face), ensuring secure and air-gapped LLM execution.

2. **Secure AI Gateway & Semantic Cache** — [projects/05_secure_ai_gateway/](projects/05_secure_ai_gateway/)
   - **Goal**: Design a high-throughput API Gateway in Golang for LLM traffic to optimize cost and reduce latency. Implement gRPC communication and Semantic Caching using Redis and ChromaDB to intercept redundant prompts, returning cached responses for ~30% of traffic.

3. **Autonomous Multi-Agent Orchestration** — [projects/06_multi_agent_orchestration/](projects/06_multi_agent_orchestration/)
   - **Goal**: Engineer resilient agentic patterns using Python (OpenAI Swarm & CrewAI) to simulate complex decision-making pipelines, focusing on inter-agent hand-offs, shared state management, and error recovery.

4. **Graph-Augmented RAG System (GraphRAG)** — [projects/07_graphrag_system/](projects/07_graphrag_system/)
   - **Goal**: Develop an advanced retrieval system using Python (LangGraph) integrating Neo4j (Graph) with ChromaDB, utilizing optimized embedding models to retrieve structural relationships alongside semantic vectors.

Happy Learning!
