# Project 2: ReAct Agent from Scratch

## Objective
Build a ReAct (Reasoning and Acting) agent using Python. The agent should be able to receive a user query, think about the next step, execute a tool (like a mock calculator or a mock web search), observe the output, and loop until it has the final answer.

## Design Problem

Design an Agent class with a `run()` loop.

1. **Prompt Design**
   - The <abbr title="Large Language Model">LLM</abbr> needs a system prompt that explains the ReAct format.
   - Format:
     ```
     Question: <the user's question>
     Thought: <reasoning about what to do next>
     Action: <the tool to call, e.g., Calculator: 2+2>
     Observation: <the output of the tool, provided by the system>
     ... (repeat Thought/Action/Observation) ...
     Thought: I know the final answer
     Final Answer: <the answer>
     ```

2. **Tools**
   - Implement at least two python functions:
     - `calculate(expression: str) -> str`: Evaluates a math expression (use `eval` carefully or just write a mock).
     - `search(query: str) -> str`: Returns mock information for specific queries (e.g., "capital of France" -> "Paris").

3. **Execution Loop**
   - Send the prompt (including the history of thoughts/actions/observations) to the <abbr title="Large Language Model">LLM</abbr>.
   - Parse the <abbr title="Large Language Model">LLM</abbr>'s response. If it outputs an `Action`, extract the tool name and argument, execute the tool, append the `Observation`, and call the <abbr title="Large Language Model">LLM</abbr> again.
   - If it outputs `Final Answer`, return it to the user.

4. **Model Support**
   - Like project 1, it should support a local model (Ollama) and a cloud <abbr title="Application Programming Interface">API</abbr> (Gemini/OpenAI) via configuration.

## Challenge
- Can you write the regex or string splitting logic to reliably parse `Thought:`, `Action:`, and `Final Answer:`?
- What happens if the <abbr title="Large Language Model">LLM</abbr> hallucinates a tool that doesn't exist? (Hint: your code should return an Observation like `Error: Tool not found`).

Once done, check out `02_react_agent_project_solution.py`.
