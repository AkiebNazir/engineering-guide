# Graph-Augmented <abbr title="Retrieval-Augmented Generation">RAG</abbr> System (GraphRAG)

## Overview
This enterprise project explores the integration of semantic search (ChromaDB) with structural knowledge traversal (Neo4j) using LangGraph. This pattern solves complex multi-hop reasoning tasks that traditional vector databases fail at.

## Architecture
- **Vector DB (ChromaDB)**: Embeds and retrieves unstructured text.
- **Graph DB (Neo4j)**: Stores explicit entities and relationships.
- **Orchestration (LangGraph)**: A state graph that coordinates routing:
  1. Does this question require explicit relationships? -> Query Neo4j.
  2. Does this require semantic similarity? -> Query Chroma.
  3. Combine context and generate final answer.

## Directory Structure
```
├── _project.md          # Design Challenge
├── src/
│   ├── graph/           # Neo4j and structural retrieval logic
│   └── retrieval/       # LangGraph state machine and Chroma search
```
