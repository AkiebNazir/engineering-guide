import logging
from typing import TypedDict, Annotated, Sequence
import operator
from src.graph.neo4j_manager import neo4j_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("langgraph_agent")

# 1. Define the State
class AgentState(TypedDict):
    messages: Annotated[Sequence[str], operator.add]
    question: str
    graph_context: str
    vector_context: str
    next_step: str

# 2. Define Nodes
def classify_question(state: AgentState) -> AgentState:
    """Determine if we need Graph, Vector, or Both."""
    question = state["question"].lower()
    
    # Simple heuristic for the mock
    if "supplier" in question or "who supplies" in question:
        return {"next_step": "graph_search"}
    else:
        return {"next_step": "vector_search"}

def graph_search(state: AgentState) -> AgentState:
    """Generate Cypher and query Neo4j."""
    logger.info("Executing Graph Search (Neo4j)...")
    # Mock LLM generating Cypher
    cypher_query = f"MATCH (n) WHERE n.name = '{state['question']}' RETURN n" 
    result = neo4j_db.execute_cypher(cypher_query)
    return {"graph_context": result, "next_step": "synthesize"}

def vector_search(state: AgentState) -> AgentState:
    """Query ChromaDB for semantic similarity."""
    logger.info("Executing Vector Search (ChromaDB)...")
    # Mock vector DB retrieval
    return {"vector_context": "Semantic chunk retrieved.", "next_step": "synthesize"}

def synthesize(state: AgentState) -> AgentState:
    """Combine contexts and generate final answer."""
    logger.info("Synthesizing Final Answer...")
    context = f"Graph: {state.get('graph_context', '')} | Vector: {state.get('vector_context', '')}"
    final_answer = f"Based on the context ({context}), here is your answer."
    return {"messages": [final_answer], "next_step": "end"}

# 3. Define the Graph Orchestrator
class GraphRAGOrchestrator:
    def __init__(self):
        # In a real LangGraph implementation, you use StateGraph(AgentState)
        # and add nodes/edges. We simulate the state machine here.
        self.nodes = {
            "classify": classify_question,
            "graph_search": graph_search,
            "vector_search": vector_search,
            "synthesize": synthesize
        }

    def run(self, question: str):
        state = AgentState(question=question, messages=[], graph_context="", vector_context="", next_step="classify")
        
        while state["next_step"] != "end":
            current_step = state["next_step"]
            logger.info(f"--- Node: {current_step} ---")
            
            # Execute node
            node_func = self.nodes[current_step]
            update = node_func(state)
            
            # Update state
            state.update(update)
            
        print("\nFinal Output:")
        print(state["messages"][-1])

if __name__ == "__main__":
    orchestrator = GraphRAGOrchestrator()
    orchestrator.run("Who supplies components to SupplierA?")
