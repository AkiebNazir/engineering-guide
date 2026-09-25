# Design Problem: Secure <abbr title="Artificial Intelligence">AI</abbr> Gateway & Semantic Cache

## Scenario
<abbr title="Large Language Model">LLM</abbr> APIs are expensive. If 100 users ask "How do I reset my password?", you shouldn't pay the <abbr title="Large Language Model">LLM</abbr> 100 times. However, users might phrase it differently ("I forgot my password", "Password reset help"). Exact string matching (e.g., standard Redis caching) will miss these.

## Requirements
1. **<abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> Protocol**: Define a protobuf file `cache.proto` with a service `SemanticCache` that has a `CheckCache(Prompt) returns (CacheResponse)` method.
2. **Python Cache Server**: Write a Python <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> server. When it receives a prompt, it should:
   - Embed the prompt using a local model.
   - Query ChromaDB.
   - If a match is found with distance < threshold (e.g., 0.2), return the cached response.
   - Otherwise, return a cache miss.
3. **Golang <abbr title="Application Programming Interface"><abbr title="Application Programming Interface - A set of rules and protocols that allows different software applications to communicate with each other.">API</abbr></abbr> Gateway**: Write a basic Golang web server that receives user prompts, calls the Python <abbr title="gRPC Remote Procedure Call - A modern, open-source, high-performance <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> framework that can run in any environment.">gRPC</abbr> service, and returns the cached answer (or prints "Cache Miss - Routing to <abbr title="Large Language Model">LLM</abbr>").

## The Challenge
Implement the protobuf definition and the Python Semantic Caching logic. Understand how vector databases can save money in production deployments.

Check the `cache/` and `gateway/` folders for the solution.
