# Day 136: Browser Agents (Web Automation with AI)

Welcome to Day 136. 

Our agents can now navigate the terminal. But many enterprise workflows (like scraping data from competitor websites, booking flights, or filling out government forms) do not have APIs. They require a human to open Chrome, look at the screen, and click buttons.

Today, we learn how to build **Browser Agents**. We will give our LLMs eyes, hands, and a headless web browser to automate the graphical web.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Observation Space (How the <abbr title="Artificial Intelligence">AI</abbr> "Sees")
When an <abbr title="Artificial Intelligence">AI</abbr> opens a webpage, it cannot just "look" at it like a human. It needs data. How do we feed the page to the <abbr title="Large Language Model">LLM</abbr>?
- **The Raw DOM (HTML):** We can extract the HTML. *Problem:* Modern websites have massive CSS/JS payloads. Passing the raw HTML of Amazon.com to an <abbr title="Large Language Model">LLM</abbr> will cost $5.00 in tokens per page load!
- **The Accessibility Tree:** We strip away the visual fluff and only pass the elements designed for screen readers (Headers, Buttons, Links, Inputs). This shrinks the context by $90\%$.
- **Vision (Screenshots):** We use a Multi-Modal <abbr title="Large Language Model">LLM</abbr> (like GPT-4o or Claude 3.5 Sonnet). The script takes a screenshot of the browser and sends the actual image to the <abbr title="Large Language Model">LLM</abbr>!

### 2. Set-of-Marks Prompting (SOM)
If the <abbr title="Large Language Model">LLM</abbr> looks at a screenshot and says *"Click the Login button"*, how does the Python script know *where* to click? The script doesn't know coordinates.
**Set-of-Marks (SOM):** The Python script uses a library like Playwright to find all clickable elements. It then draws a little red box with a number (e.g., `[12]`) over every button *before* taking the screenshot. 
The <abbr title="Large Language Model">LLM</abbr> looks at the image and outputs: `Action: Click element 12`. Playwright maps ID 12 to the exact X/Y coordinate and clicks it!

### 3. The Action Space
A standard Browser Agent uses 4 primary tools:
1. `navigate(url)`
2. `click(element_id)`
3. `type(element_id, text)`
4. `scroll(direction)`

### 4. WebArena Benchmark
The standard benchmark for Browser Agents. It drops the Agent into a massive, offline sandbox containing an e-commerce site, a forum, and a CMS, and asks it to perform complex, multi-page workflows (e.g., *"Cancel my latest order and request a refund to my wallet"*).

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual Browser Agent using the Set-of-Marks methodology! We will mock the Playwright execution to see how the <abbr title="Large Language Model">LLM</abbr> maps visual IDs to physical clicks.

Create a file named `browser_agent.py`:

```python
import time

# --- 1. THE MOCK BROWSER (PLAYWRIGHT) ---
class MockBrowser:
    def __init__(self):
        self.current_url = ""
        self.elements = {}
        
    def navigate(self, url):
        print(f"   [BROWSER] Navigating to {url}...")
        self.current_url = url
        time.sleep(1)
        
        # Mocking the Set-of-Marks extraction
        if "github.com" in url:
            self.elements = {
                1: "Search Bar (Input)",
                2: "Sign In (Button)",
                3: "Sign Up (Button)"
            }
            return "Page loaded. Generated Set-of-Marks screenshot."
            
    def click(self, element_id):
        print(f"   [BROWSER] Mouse moving to Element ID: {element_id}...")
        if element_id == 2:
            self.elements = {4: "Username (Input)", 5: "Password (Input)", 6: "Submit (Button)"}
            return "Clicked 'Sign In'. Page updated to Login Form."
        return "Clicked element. Nothing happened."
        
    def type_text(self, element_id, text):
        print(f"   [BROWSER] Typing '{text}' into Element ID: {element_id}...")
        return "Text entered."

# --- 2. THE BROWSER AGENT ---
def mock_vision_llm(history, available_elements):
    """Simulates an LLM looking at the Set-of-Marks screenshot."""
    if len(history) == 0:
        return {"action": "navigate", "args": {"url": "https://github.com"}}
        
    if "Generated Set-of-Marks" in history[-1]:
        print(f"\n[AGENT THOUGHT] I see the homepage. I need to click Sign In (Element 2).")
        return {"action": "click", "args": {"element_id": 2}}
        
    if "Login Form" in history[-1]:
        print(f"\n[AGENT THOUGHT] I am on the login form. I will type my username into Element 4.")
        return {"action": "type_text", "args": {"element_id": 4, "text": "agent_007"}}
        
    return {"action": "done", "args": {}}

def run_browser_simulation():
    print("--- RUNNING SET-OF-MARKS BROWSER AGENT ---\n")
    
    browser = MockBrowser()
    history = []
    
    print("User Request: Go to GitHub and start the login process.\n")
    
    for step in range(5):
        # 1. LLM decides what to do based on the "Screenshot" (elements)
        decision = mock_vision_llm(history, browser.elements)
        
        if decision["action"] == "done":
            print("\n[SUCCESS] Agent completed the web workflow!")
            break
            
        # 2. Execute the action in the Browser
        action = decision["action"]
        args = decision["args"]
        
        if action == "navigate":
            obs = browser.navigate(args["url"])
        elif action == "click":
            obs = browser.click(args["element_id"])
        elif action == "type_text":
            obs = browser.type_text(args["element_id"], args["text"])
            
        # 3. Agent reads the observation
        print(f"   [OBSERVATION] {obs}")
        history.append(obs)

if __name__ == "__main__":
    run_browser_simulation()
```

### Key Takeaways from Code:
1. **The ID Abstraction:** The <abbr title="Large Language Model">LLM</abbr> does not need to know CSS Selectors, XPath, or exact pixels. By abstracting the UI into a numbered list of interactive elements, the <abbr title="Large Language Model">LLM</abbr> only has to output a single integer. The Python backend handles the complex physical translation.
2. **State Management:** The web is dynamic. After the Agent clicked "Sign In" (Element 2), the page state completely changed. The system had to generate a brand new set of IDs (Elements 4, 5, 6) for the new screen.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Multi-Site Comparer
Browser agents are fantastic for avoiding CAPTCHAs and rate limits on data-scraping tasks.
**Your Task:**
1. Conceptually design a workflow where a user asks: *"Compare the price of an iPhone 15 on Amazon, BestBuy, and Walmart."*
2. Because web latency is high, design an architecture that spins up 3 parallel Browser Agents (using the LLMCompiler pattern from Day 131).
3. Each agent navigates to its assigned site, finds the search bar, types "iPhone 15", clicks search, parses the results, and returns the price.
4. A final "Aggregator" agent takes the 3 outputs and formats a markdown table.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design a browser agent system for automated software testing. It should navigate your web app, test user flows, and report bugs. Discuss reliability, parallelism, and handling dynamic content (like loading spinners)."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Handling Dynamic Content (The Wait Loop):** 
   - State that LLMs are too fast. If they try to click a button before the React component mounts, the script crashes. 
   - Propose an ACI that automatically waits for network idle and DOM stability before passing the screenshot to the <abbr title="Large Language Model">LLM</abbr>. 
2. **Reliability (Self-Healing):**
   - Web UIs change frequently (A/B testing, redesigns). Standard Selenium tests break instantly. 
   - Emphasize that the Browser Agent is "Self-Healing". Because it uses Vision to find the "Checkout" button, it doesn't care if the CSS class changed from `btn-blue` to `btn-red` or if it moved to the left side of the screen.
3. **Parallel Execution:**
   - Propose running the tests concurrently across a Kubernetes cluster of Headless Chromium containers. 

---
**Task for the end of the day:** Commit your code to Git. 

Our Agents can now write code and browse the web. They are extremely capable.
But how do we integrate them into actual enterprise businesses? How do they talk to Salesforce, trigger ETL pipelines, and respond to customer emails?

Tomorrow, in **Day 137**, we leave the sandbox and enter the enterprise. We will learn **Workflow Automation and Enterprise Integration Patterns**!
