import logging
from typing import Dict, Any
from agents.definitions import researcher, writer, Agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestrator")

class SwarmOrchestrator:
    def __init__(self):
        self.state: Dict[str, Any] = {}
        self.agents = {
            "Researcher": researcher,
            "Writer": writer
        }

    def _mock_llm_decision(self, agent: Agent, input_prompt: str) -> str:
        """
        Mocking the LLM decision loop. In reality, this sends the prompt + tools to an LLM.
        """
        if agent.name == "Researcher":
            if "error" in input_prompt:
                return "CALL: search_database(error)"
            return "CALL: search_database(Q3 financials) THEN CALL: transfer_to_writer()"
        elif agent.name == "Writer":
            data = self.state.get("research_data", "No data found.")
            return f"FINAL OUTPUT: Based on the research, {data}"
        return "FINAL OUTPUT: Unknown agent."

    def run(self, start_agent: str, task: str):
        current_agent = self.agents[start_agent]
        logger.info(f"Starting Swarm with task: {task}")
        
        step_count = 0
        prompt = task
        
        while step_count < 10:
            logger.info(f"[{current_agent.name}] Thinking...")
            
            # 1. LLM predicts next action
            decision = self._mock_llm_decision(current_agent, prompt)
            
            # 2. Parse tools or Handoffs
            if "transfer_to_writer" in decision:
                logger.info("HANDOFF triggered -> Writer")
                current_agent = self.agents["Writer"]
                prompt = "Please write the report based on the state."
                
            elif "search_database" in decision:
                # 3. Resilient Tool Execution
                try:
                    logger.info(f"[{current_agent.name}] Executing tool: search_database")
                    # Simulating the exact failure condition
                    if "error" in decision:
                        raise ValueError("Database connection failed.")
                    self.state["research_data"] = "Revenue is up 20%."
                except Exception as e:
                    logger.error(f"Tool failed: {e}. Attempting recovery...")
                    prompt += f"\nObservation: Tool failed with error {e}. Please retry or take alternative action."
                    break # Break for mock purposes
                
            elif "FINAL OUTPUT" in decision:
                logger.info("Task Complete.")
                print(f"\nFinal Result: {decision}")
                return decision
                
            step_count += 1

if __name__ == "__main__":
    orchestrator = SwarmOrchestrator()
    orchestrator.run("Researcher", "Analyze Q3 financials.")
