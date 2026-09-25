# The Ultimate Guide to Agentic AI and Related Technologies

Welcome to the **Ultimate Guide to Agentic <abbr title="Artificial Intelligence">AI</abbr>**. This repository is designed to take you from the foundational concepts of Generative <abbr title="Artificial Intelligence">AI</abbr> all the way to advanced Agentic <abbr title="Artificial Intelligence">AI</abbr> architectures, <abbr title="Retrieval-Augmented Generation">RAG</abbr> systems, and Graph databases.

## Modules

This guide is broken down into 5 core modules, each with deep-dive technical explanations and Python implementations:

1. [**Generative AI: LLM Architecture & Runtime Internals**](01_generative_ai_internals.md)
   Dive deep into scaled dot-product attention, KV cache memory footprint, and the core mechanics of transformer-based LLMs.
2. [**Agentic AI Internals: Planning, Tools & Memory**](02_agentic_ai_internals.md)
   Understand how LLMs transition from text generators to autonomous agents using constrained decoding, tool-calling loops, and memory architectures.
3. [**Retrieval-Augmented Generation: RAG Internals**](03_rag_deep_dive.md)
   Learn the mechanics of BM25, dense embeddings, cosine similarity, and Reciprocal Rank Fusion (RRF) for building robust <abbr title="Retrieval-Augmented Generation">RAG</abbr> systems.
4. [**Vector Databases: Vector Indexing & Storage Engines**](04_vector_databases_internals.md)
   Explore how vector databases work under the hood, including k-means clustering, Voronoi cells, inverted lists (IVF), and distance metrics.
5. [**Graph Databases & GraphRAG: Knowledge Representation & Traversal**](05_graph_databases_and_graphrag.md)
   Master index-free adjacency and how to extract and traverse knowledge graphs for advanced reasoning tasks (GraphRAG).
6. [**Protocol Buffers & gRPC: High-Speed Microservices**](06_protocol_buffers_and_grpc.md)
   Learn the fundamentals of `.proto` files, binary serialization, and cross-language <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> communication used in high-throughput <abbr title="Artificial Intelligence">AI</abbr> gateways.
7. [**Multi-Agent Orchestration & MCP**](07_multi_agent_and_mcp.md)
   Scale up from a single agent to Swarm/LangGraph architectures, and learn how the Model Context Protocol (<abbr title="Model Context Protocol">MCP</abbr>) standardizes enterprise tool connectivity.
8. [**API Architectures: REST, GraphQL, and gRPC**](08_api_architectures_engineering_guide.md)
9. [**Agent Evaluation and Production**](09_agent_eval_and_production.md)
   A comprehensive guide to evaluating non-deterministic agents, observability, guardrails, red teaming, and deployment strategies like prompt versioning and shadow testing.
   A detailed engineering guide comparing <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr>, GraphQL, and <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr>. Contains 5 distinct implementation examples for each technology in both Python and Golang.

## Practice Projects

To solidify your understanding, we have provided hands-on projects. Each project comes with two files:
- `*_project.md`: The problem statement, design requirements, and a challenge for you to try building it yourself.
- `*_project_solution.py`: A full-fledged, running Python solution. These solutions are designed to work with **Local Models** (e.g., via Ollama or HuggingFace) by default, but can easily be configured to use cloud APIs (like Gemini or OpenAI) by providing your <abbr title="Application Programming Interface">API</abbr> keys.

### Foundational Projects
1. **Basic <abbr title="Retrieval-Augmented Generation">RAG</abbr> Pipeline**
   - Challenge: [projects/01_basic_rag_project.md](projects/01_basic_rag_project.md)
   - Solution: [projects/01_basic_rag_project_solution.py](projects/01_basic_rag_project_solution.py)
2. **ReAct Agent from Scratch**
   - Challenge: [projects/02_react_agent_project.md](projects/02_react_agent_project.md)
   - Solution: [projects/02_react_agent_project_solution.py](projects/02_react_agent_project_solution.py)
3. **Mini GraphRAG Extractor**
   - Challenge: [projects/03_graphrag_project.md](projects/03_graphrag_project.md)
   - Solution: [projects/03_graphrag_project_solution.py](projects/03_graphrag_project_solution.py)

### Advanced Enterprise Capstone Projects
For a more advanced challenge, consider exploring or building these enterprise-grade architectures:

1. **Enterprise <abbr title="Artificial Intelligence">AI</abbr> Infrastructure (<abbr title="Model Context Protocol">MCP</abbr> & Local Inference)**
   - **Goal**: Develop Python-based <abbr title="Model Context Protocol">MCP</abbr> (Model Context Protocol) Servers to standardize connectivity between <abbr title="Artificial Intelligence">AI</abbr> Agents and backend systems (bridged via Golang). Architect a private inference layer using Python (vLLM) to host open-source models (DeepSeek-R1 / Hugging Face), ensuring secure and air-gapped <abbr title="Large Language Model">LLM</abbr> execution.

2. **Secure <abbr title="Artificial Intelligence">AI</abbr> Gateway & Semantic Cache**
   - **Goal**: Design a high-throughput <abbr title="Application Programming Interface">API</abbr> Gateway in Golang for <abbr title="Large Language Model">LLM</abbr> traffic to optimize cost and reduce latency. Implement <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> communication and Semantic Caching using Redis and ChromaDB to intercept redundant prompts, returning cached responses for ~30% of traffic.

3. **Autonomous Multi-Agent Orchestration**
   - **Goal**: Engineer resilient agentic patterns using Python (OpenAI Swarm & CrewAI) to simulate complex decision-making pipelines, focusing on inter-agent hand-offs, shared state management, and error recovery.

4. **Graph-Augmented <abbr title="Retrieval-Augmented Generation">RAG</abbr> System (GraphRAG)**
   - **Goal**: Develop an advanced retrieval system using Python (LangGraph) integrating Neo4j (Graph) with ChromaDB, utilizing optimized embedding models to retrieve structural relationships alongside semantic vectors.

Happy Learning!
