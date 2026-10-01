# Design Problem: Advanced GraphRAG with LangGraph

## Scenario
You have complex enterprise data consisting of both unstructured documents (PDFs, policies) and highly structured relationships (Supply chain graphs, org charts). 

## Requirements
1. **Hybrid Retrieval**: Build an agent that can query *both* a Vector Database (like ChromaDB) for semantic similarity, and a Graph Database (like Neo4j) for explicit structural queries.
2. **LangGraph Orchestration**: Use a state graph framework (like LangGraph) to define a cyclic workflow:
   - Node 1: Classify question type.
   - Node 2 (Conditional): If vector-heavy, execute Vector Search.
   - Node 3 (Conditional): If graph-heavy, execute Cypher Query generation and Graph Search.
   - Node 4: Synthesize final answer.

## The Challenge
Design the State object for LangGraph and write the node functions. 
Since you might not have a local Neo4j instance running, you can write a mock Neo4j manager that simulates executing Cypher queries and returning graph paths.

Check `src/retrieval/langgraph_agent.py` for a conceptual implementation of this workflow.
