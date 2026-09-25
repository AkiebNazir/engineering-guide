# Design Problem: Autonomous Multi-Agent Orchestration

## Scenario
A single <abbr title="Large Language Model">LLM</abbr> prompt often fails at complex, multi-step tasks. You need to build a Swarm-like architecture where multiple agents collaborate.
- **Agent 1 (Researcher)**: Finds facts.
- **Agent 2 (Writer)**: Synthesizes facts into a report.

## Requirements
1. **Shared State**: Both agents need access to a shared dictionary/object tracking the current context.
2. **Handoffs**: If the Researcher finishes its job, it must return a specific command to trigger a handoff to the Writer.
3. **Resiliency**: If a tool fails (e.g., search <abbr title="Application Programming Interface">API</abbr> is down), the agent must recognize the failure and attempt a fallback or pass the error gracefully to the orchestrator.

## The Challenge
Implement a lightweight Swarm orchestrator from scratch. Create an Agent class that accepts a name, instructions, and tools. Write an execution loop that handles the state and transitions between agents based on their output.

Check the `workflows/` and `agents/` directories for a reference implementation.
