from typing import Callable, List, Dict

class Agent:
    def __init__(self, name: str, instructions: str, tools: List[Callable] = None):
        self.name = name
        self.instructions = instructions
        self.tools = tools or []

# Mock tools
def search_database(query: str, state: Dict) -> str:
    """A tool that might fail to demonstrate error recovery."""
    if "error" in query.lower():
        raise ValueError("Database connection failed.")
    
    # Store result in shared state
    state["research_data"] = f"Found data for {query}: Revenue is up 20%."
    return "Successfully retrieved and stored data."

def transfer_to_writer(state: Dict):
    """Tool to signal hand-off."""
    return "HANDOFF_WRITER"

# Define the agents
researcher = Agent(
    name="Researcher",
    instructions="You are a data researcher. Use search_database to find facts, then use transfer_to_writer to hand off the work.",
    tools=[search_database, transfer_to_writer]
)

writer = Agent(
    name="Writer",
    instructions="You are a report writer. Read the research_data from the state and summarize it.",
    tools=[]
)
