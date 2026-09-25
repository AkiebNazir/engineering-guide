# Enterprise AI Infrastructure: MCP & Local Inference

## Overview
This capstone project focuses on architecting a secure, air-gapped local inference layer and bridging it to standard Agentic systems using the Model Context Protocol (<abbr title="Model Context Protocol">MCP</abbr>).

## Architecture
- **Inference Layer**: Python-based Langchain wrapper around Ollama hosting open-source models (e.g., Llama 3) for high-throughput, low-latency text generation.
- **<abbr title="Model Context Protocol">MCP</abbr> Server**: A Python FastMCP server that standardizes the connectivity between the <abbr title="Large Language Model">LLM</abbr> and backend enterprise data systems (e.g., <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> databases or internal APIs).
- **Security**: Designed for zero-trust environments.

## Directory Structure
```
├── _project.md          # The design challenge
├── src/
│   ├── inference/       # vLLM setup and local API 
│   └── mcp_server/      # FastMCP implementation for tool access
```
