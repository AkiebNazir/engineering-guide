# Day 128: CrewAI (Multi-Agent Orchestration)

Welcome to Day 128. 

We have learned how to build Agents using LangChain and LangGraph. LangGraph is incredibly powerful, but it is low-level. You have to manually write every node, every state vector, and every routing edge.
What if you just want to hire a team of AI employees, give them a project, and tell them to work together? 

Today, we learn **CrewAI**, a high-level framework that treats Agents like human employees, Tasks like Jira tickets, and Orchestrates them as a company (a Crew).

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. CrewAI Core Concepts
CrewAI abstracts away the `while` loops and State dictionaries, replacing them with a business-centric terminology:
- **Agents (The Employees):** An Agent is defined by its `Role`, `Goal`, and `Backstory`. The Backstory is a highly optimized system prompt that prevents the Agent from hallucinating outside its persona.
- **Tasks (The Tickets):** A Task is defined by a `Description`, an `Expected Output`, and `Dependencies`. A Task is strictly assigned to one Agent.
- **Crews (The Company):** A Crew is the orchestrator. It takes a list of Agents and a list of Tasks, and manages the execution flow.

### 2. Processes (The Workflow)
How do the Agents collaborate? CrewAI defines Processes:
- **Sequential:** The factory assembly line. Agent A finishes Task 1. The exact output of Task 1 is injected into the prompt of Agent B, who starts Task 2.
- **Hierarchical:** The corporate structure. You define a "Manager Agent". You hand the Manager all the Tasks. The Manager dynamically figures out which subordinate Agent to delegate work to, evaluates their work, and compiles the final result!
- **Consensual:** Agents vote on the final outcome.

### 3. Agent Delegation
In a Hierarchical or advanced Sequential process, an Agent doesn't have to do everything itself. 
If the `Writer Agent` realizes it is missing a fact, it can autonomously pause its task, send a delegation request to the `Researcher Agent` asking it to look up the fact, wait for the response, and then resume writing!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Content Creation Crew! We will mock the CrewAI syntax to see how Agents and Tasks are defined and linked together in a Sequential process.
*(Note: To run this for real, you would `pip install crewai`).*

Create a file named `crewai_orchestration.py`:

```python
# MOCKING CrewAI for educational clarity
class MockAgent:
    def __init__(self, role, goal, backstory):
        self.role = role
        self.goal = goal
        self.backstory = backstory
        print(f"[HR] Hired new employee: {role}")

class MockTask:
    def __init__(self, description, expected_output, agent):
        self.description = description
        self.expected_output = expected_output
        self.agent = agent

class MockCrew:
    def __init__(self, agents, tasks, process):
        self.agents = agents
        self.tasks = tasks
        self.process = process
        
    def kickoff(self):
        print(f"\n--- KICKING OFF CREW EXECUTION ({self.process} Process) ---")
        context = ""
        
        for index, task in enumerate(self.tasks):
            print(f"\n[TASK {index+1}] Assigned to: {task.agent.role}")
            print(f"Goal: {task.description}")
            print("Working...")
            
            # Simulate the Agent reading the context from the previous task!
            if context:
                print(f"-> {task.agent.role} is reading the output from the previous task...")
                
            # Simulate the Agent generating output
            if "Research" in task.description:
                context = "Research Data: AI models are scaling rapidly in 2026."
            else:
                context = f"Final Blog Post: '{context} Therefore, the future is bright!'"
                
            print(f"[OUTPUT] {context}")
            
        return context

# --- START OF CREWAI SCRIPT ---

def run_crewai_simulation():
    print("--- BUILDING THE CONTENT CREW ---\n")
    
    # 1. Define the Agents (The Employees)
    researcher = MockAgent(
        role="Senior Technology Analyst",
        goal="Uncover cutting-edge developments in AI.",
        backstory="You work at a top-tier tech think tank. You never make assumptions. You only provide verified facts."
    )
    
    writer = MockAgent(
        role="Tech Journalist",
        goal="Craft engaging blog posts about technology.",
        backstory="You write for Wired Magazine. You take dry research and turn it into thrilling narratives."
    )
    
    # 2. Define the Tasks (The Jira Tickets)
    research_task = MockTask(
        description="Research the state of Large Language Models in 2026.",
        expected_output="A 3-bullet point summary of key AI trends.",
        agent=researcher
    )
    
    writing_task = MockTask(
        description="Write a short blog post based on the research provided.",
        expected_output="A 2-paragraph engaging blog post.",
        agent=writer
    )
    
    # 3. Form the Crew (The Company)
    tech_crew = MockCrew(
        agents=[researcher, writer],
        tasks=[research_task, writing_task],
        process="Sequential" # Run Task 1, then pass result to Task 2
    )
    
    # 4. Execute!
    final_result = tech_crew.kickoff()
    
    print("\n--- MISSION ACCOMPLISHED ---")
    print(f"FINAL DELIVERABLE:\n{final_result}")

if __name__ == "__main__":
    run_crewai_simulation()
```

### Key Takeaways from Code:
1. **The Backstory is Critical:** The `backstory` parameter is not just flavor text. It is injected into the LLM's system prompt. Telling the Writer they "work for Wired Magazine" forces the LLM's weights to output a specific journalistic tone without you having to write a massive prompt template.
2. **Context Passing:** In a Sequential process, CrewAI automatically takes the output string of `research_task` and seamlessly injects it into the prompt of `writing_task`. You do not have to manage the memory variables yourself!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Investment Crew
You want to analyze a stock ticker (e.g., AAPL) before buying it.
**Your Task:**
1. Define 3 Agents: `Data_Collector` (Goal: Get stock prices), `Financial_Analyst` (Goal: Analyze trends), `Risk_Assessor` (Goal: Find potential downsides).
2. Define their Backstories. Make the Risk Assessor highly pessimistic.
3. Define the Tasks. 
4. Conceptually wire them together. Why might a Hierarchical process be better here than a Sequential one? (Hint: The Manager can ask the Data Collector and Risk Assessor to work in parallel, and compile their reports independently!)

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Compare LangGraph and CrewAI for building production agent systems. When would you choose one over the other? Discuss debugging, observability, and scaling."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Core Trade-off (Control vs Abstraction):** 
   - State that LangGraph is a low-level orchestration framework (like writing raw Python), while CrewAI is a high-level framework (like using Django).
2. **When to use CrewAI:**
   - Use CrewAI for "Information Worker" tasks: Research, drafting content, and standard multi-agent workflows where agents pass documents sequentially. It reduces boilerplate code by $80\%$.
3. **When to use LangGraph:**
   - Use LangGraph for complex, non-deterministic enterprise systems that require strict Human-in-the-Loop breakpoints, Time-Travel debugging, and extreme custom error-recovery loops. 
   - Emphasize that debugging a failed CrewAI run is difficult because the prompt routing is hidden inside the library, whereas LangGraph exposes the exact State vector at every node.

---
**Task for the end of the day:** Commit your code to Git. 

We can orchestrate Agents. But right now, our Agents are isolated. They have no memory of past executions, and they can't access our MCP servers.

Tomorrow, in **Day 129**, we learn **CrewAI Advanced: Custom Tools, Memory, and MCP Integration**!
