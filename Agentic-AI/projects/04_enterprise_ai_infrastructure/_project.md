# Design Problem: Enterprise AI Infrastructure

## Scenario
Your enterprise requires an autonomous agent that can query internal employee databases. However, due to data privacy laws, you cannot send employee data or the prompts to external providers like OpenAI or Google. 

You must build a 100% on-premise solution.

## Requirements
1. **Local Inference**: Write a wrapper around `Ollama` using `Langchain` to host a local model. It must expose an OpenAI-compatible `/v1/chat/completions` endpoint using FastAPI.
2. **Model Context Protocol (MCP)**: Agents need standard ways to talk to your enterprise DB. Write an MCP server using Python (`fastmcp` or `@modelcontextprotocol/sdk`) that exposes a `query_employee_db` tool.
3. **Production Grade**: Include proper typing, logging, and environment variable configurations.

## The Challenge
Implement the architecture. Try to figure out how to start a vLLM server in Python and how to define a tool using the MCP standard. 

Once finished, review the `src/` directory for a reference solution.
