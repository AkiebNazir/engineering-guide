# Project 3: Mini GraphRAG Knowledge Extractor

## Objective
Build a miniature GraphRAG system. The system will use an <abbr title="Large Language Model">LLM</abbr> to read a paragraph of text, extract entities and relationships in a structured format (<abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>), build a simple in-memory graph (nodes and edges), and then traverse that graph to answer questions.

## Design Problem

1. **Entity Extraction (Information Extraction)**
   - Pass a text snippet to the <abbr title="Large Language Model">LLM</abbr>.
   - Use prompting (and optionally <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> mode or constrained decoding if your local model supports it) to force the <abbr title="Large Language Model">LLM</abbr> to output a list of relationships in the format:
     `[ {"source": "Entity1", "relation": "relationship type", "target": "Entity2"}, ... ]`

2. **Graph Construction (Index-Free Adjacency)**
   - In Python, build a simple graph data structure.
   - Example: A dictionary mapping an entity (node) to a list of its edges.
     ```python
     graph = {
         "Alice": [("knows", "Bob"), ("lives_in", "Paris")],
         "Bob": [("knows", "Alice")]
     }
     ```

3. **Graph Retrieval & Question Answering**
   - Given a question (e.g., "Where does the person Alice knows live?"), write a naive traversal or an <abbr title="Large Language Model">LLM</abbr>-assisted traversal.
   - For simplicity, given the entity "Alice" in the question, extract her 1-hop and 2-hop neighborhood from the dictionary.
   - Pass this sub-graph context to the <abbr title="Large Language Model">LLM</abbr> to answer the question.

4. **Model Support**
   - Support local (Ollama) and <abbr title="Application Programming Interface">API</abbr> (Gemini/OpenAI).

## Challenge
Structured output from LLMs can be tricky, especially with smaller local models! 
- Try to design a prompt that is very explicit about the <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> array format.
- Write a parser that can handle slightly malformed <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> (e.g., stripping out markdown ````json ```` blocks).
- Implement a Breadth-First Search (BFS) to grab exactly a 2-hop neighborhood of a starting entity.

Compare your code to `03_graphrag_project_solution.py`.
