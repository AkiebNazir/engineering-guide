# Day 142: Multi-Modal Agents (Vision + Code + Web)

Welcome to Day 142. 

We have built specialized agents: Code Agents that live in the terminal, Browser Agents that navigate websites, and <abbr title="Retrieval-Augmented Generation">RAG</abbr> Agents that read text. 
But the human brain does not separate these tasks. When you do your job, you look at a visual chart (Vision), you write an Excel formula (Code), and you email the result (Web).

Today, we build the **Omnimodal Agent**. We fuse Vision Encoders, Code Execution, and Web APIs into a single, unified architecture.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Omnimodal Architecture
A Multi-Modal Agent requires a massive foundational model (like GPT-4o or Claude 3.5 Sonnet) that natively understands text, images, and audio in the same latent space.
This "Brain" sits at the center of a LangGraph orchestrator and is equipped with a diverse Toolbelt:
- `vision_analyze(image_path)`
- `execute_python(code_string)`
- `search_web(query)`

### 2. The Grounding Problem
The hardest challenge in Multi-Modal <abbr title="Artificial Intelligence">AI</abbr> is **Grounding**—connecting a visual concept to a physical action.
If the Agent looks at a screenshot of a medical dashboard, it might say: *"I see the patient's heart rate is 120."* That is visual understanding.
But if you ask the Agent to *"Click the button next to the heart rate"*, the Agent must ground the visual concept of "Heart Rate" to a specific $(X, Y)$ pixel coordinate on the screen. (This is why we used Set-of-Marks prompting in Day 136!).

### 3. Cross-Modal Reasoning
The true power of this architecture is Cross-Modal Reasoning. The Agent can translate between modalities.
1. **Vision $\rightarrow$ Code:** The Agent looks at a handwritten math equation (Vision) and translates it into a Python `sympy` script (Code).
2. **Code $\rightarrow$ Vision:** The Agent executes a Python script that generates a matplotlib plot (Code), then looks at the plot (Vision) to verify it looks correct before sending it to the user!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual Omnimodal Agent loop. We will simulate an Agent receiving an image of a Bar Chart, using Vision to extract the data into JSON, and then using a Python tool to calculate the standard deviation!

Create a file named `multimodal_agents.py`:

```python
import json

# --- 1. THE MODAL TOOLS ---

def tool_vision_analyze(image_path):
    """Simulates GPT-4V looking at an image and extracting data."""
    print(f"   [VISION TOOL] Analyzing {image_path}...")
    if "chart" in image_path:
        # The LLM extracts the visual bars into structured text!
        return '{"Q1": 100, "Q2": 150, "Q3": 130, "Q4": 200}'
    return "Error: Image not recognized."

def tool_execute_python(code_str):
    """Simulates a secure Python REPL sandbox."""
    print(f"   [CODE TOOL] Executing Python code in sandbox...")
    try:
        # Educational mock. In reality, use Docker/gVisor.
        local_scope = {}
        exec(code_str, globals(), local_scope)
        return str(local_scope.get("result", "Code executed but no 'result' variable found."))
    except Exception as e:
        return f"Python Error: {str(e)}"

# --- 2. THE OMNIMODAL AGENT ---

def mock_omnimodal_llm(history):
    """The Brain of the Agent."""
    if len(history) == 1: # Just the user prompt
        return "Thought: I need to read the chart first.\nAction: vision_analyze(sales_chart.png)"
        
    last_obs = history[-1]
    
    if "Q1" in last_obs:
        return """Thought: I have the data. I need to calculate the average. I will write a python script.
Action: execute_python(
data = {"Q1": 100, "Q2": 150, "Q3": 130, "Q4": 200}
values = list(data.values())
result = sum(values) / len(values)
)"""
        
    if "145.0" in last_obs:
        return "Thought: The calculation is complete.\nFinal Answer: Based on the visual chart, the average sales across the 4 quarters is 145.0."

def run_multimodal_simulation():
    print("--- RUNNING OMNIMODAL AGENT SIMULATION ---\n")
    
    user_prompt = "User: Look at 'sales_chart.png' and calculate the exact average."
    print(user_prompt)
    
    history = [user_prompt]
    
    for step in range(5):
        # 1. The LLM thinks
        llm_response = mock_omnimodal_llm(history)
        print(f"\n[AGENT] {llm_response.split('Action:')[0].strip()}")
        
        if "Final Answer" in llm_response:
            break
            
        # 2. Extract and execute the tool
        action_line = [line for line in llm_response.split('\n') if "Action:" in line][0]
        
        if "vision_analyze" in action_line:
            obs = tool_vision_analyze("sales_chart.png")
        elif "execute_python" in action_line:
            # Extract the code block between the parentheses
            code = llm_response.split("execute_python(")[1].rsplit(")", 1)[0].strip()
            obs = tool_execute_python(code)
            
        print(f"   [OBSERVATION] {obs}")
        history.append(f"Observation: {obs}")

if __name__ == "__main__":
    run_multimodal_simulation()
```

### Key Takeaways from Code:
1. **Modality Bridging:** Notice how the Agent took unstructured visual pixels (a `.png` file) and seamlessly bridged it into strict, executable Python code. This is the holy grail of automation.
2. **The `result` Variable Protocol:** When building Code Tools, you must strictly prompt the <abbr title="Large Language Model">LLM</abbr> to assign its final answer to a specific variable (like `result`). Otherwise, the `exec()` environment won't know what data to return to the LangGraph state!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Automated QA Tester
You want to build an Agent that tests your company's website every night.
**Your Task:**
1. Conceptually define a Web-Vision-Code agent loop.
2. **Step 1 (Web):** Agent uses Playwright to open `localhost:3000`.
3. **Step 2 (Vision):** Agent takes a screenshot and asks GPT-4V: *"Does the UI look correct, or are elements overlapping?"*
4. **Step 3 (Code):** If the UI is broken, the Agent reads the DOM, writes a CSS fix (e.g., changing `margin-top`), and pushes a Git commit.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design a document processing agent that handles enterprise PDFs containing mixed modalities: text, massive financial tables, bar charts, and handwritten notes. It must extract structured JSON with 99% accuracy. Discuss the architecture and fallback strategies."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Routing Parser:** 
   - Standard OCR fails on charts. You must use a routing pipeline. First, run an Object Detection model (like YOLO, Day 41) over the PDF to draw bounding boxes around Text, Tables, and Images.
2. **Modality-Specific Processing:**
   - Send the Text boxes to a standard OCR tool (Tesseract).
   - Send the handwritten notes to a specialized Vision model.
   - Send the financial tables to an HTML-table-extraction script.
3. **The Multi-Agent Consensus (99% Accuracy):**
   - For high-accuracy extraction, use Multi-Agent Debate (Day 133). Send the extracted data to Agent A. Send the raw PDF image to Agent B (GPT-4V). If Agent A's extracted numbers don't match Agent B's visual analysis, trigger an anomaly alert and escalate to Human-in-the-Loop (Day 138)!

---
**Task for the end of the day:** Commit your code to Git. 

Our Agents are incredibly capable. They can see, code, and browse. 
But they still suffer from amnesia. When the LangGraph script ends, the Agent dies.

Tomorrow, in **Day 143**, we learn **Agent Memory Systems**. We will give our agents Short-Term, Long-Term, and Episodic memory so they can remember you for years!
