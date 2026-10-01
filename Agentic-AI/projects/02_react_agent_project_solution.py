import os
import re
import json
import urllib.request
import urllib.error

# Define Tools
def calculate(expression: str) -> str:
    """A simple calculator tool."""
    try:
        # NOTE: eval is dangerous in production! This is just for demonstration.
        result = eval(expression, {"__builtins__": None}, {})
        return str(result)
    except Exception as e:
        return f"Error evaluating expression: {e}"

def search(query: str) -> str:
    """A mock search engine."""
    query = query.lower()
    if "president of us" in query or "president of the united states" in query:
        return "The President of the US is Joe Biden (as of 2024)."
    elif "age" in query and "biden" in query:
        return "Joe Biden is 81 years old (born Nov 20, 1942)."
    else:
        return "Search results not found."

TOOLS = {
    "Calculator": calculate,
    "Search": search
}

class ReActAgent:
    def __init__(self, use_api=False, max_steps=10):
        self.use_api = use_api
        self.max_steps = max_steps
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
        if self.use_api and not self.api_key:
            print("WARNING: use_api is True but GEMINI_API_KEY is not set. Falling back to local Ollama.")
            self.use_api = False

        self.system_prompt = """You are a helpful reasoning agent. You have access to the following tools:
- Calculator: evaluates math expressions. Input should be a valid python math string (e.g. 2+2).
- Search: searches the web for basic facts.

Use the following format strictly:

Question: the input question you must answer
Thought: you should always think about what to do next
Action: the action to take, should be one of [Calculator, Search]
Action Input: the input to the action
Observation: the result of the action (provided by the system, DO NOT hallucinate this)
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Let's begin!"""

    def llm_generate(self, prompt: str) -> str:
        """Abstraction for calling the LLM (local or API)"""
        # Stop sequences are critical for ReAct to prevent the LLM from hallucinating the observation.
        stop_seq = ["Observation:"]
        
        if self.use_api:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            data = {
                "contents": [{"parts":[{"text": prompt}]}],
                "generationConfig": {"stopSequences": stop_seq}
            }
            try:
                req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode())
                    return result['candidates'][0]['content']['parts'][0]['text']
            except Exception as e:
                return f"API Error: {e}"
        else:
            url = "http://localhost:11434/api/generate"
            data = {
                "model": "llama3",
                "prompt": prompt,
                "stream": False,
                "options": {"stop": stop_seq}
            }
            try:
                req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode())
                    return result.get('response', "Error generating response.")
            except Exception as e:
                return f"Local Model Error: {e}"

    def run(self, question: str) -> str:
        prompt = self.system_prompt + f"\n\nQuestion: {question}\n"
        
        for step in range(self.max_steps):
            print(f"\n--- Step {step + 1} ---")
            response = self.llm_generate(prompt).strip()
            
            # Print the LLM's raw generation (Thoughts, Actions)
            print(response)
            prompt += response + "\n"
            
            # Check if finished
            if "Final Answer:" in response:
                return response.split("Final Answer:")[-1].strip()
            
            # Parse Action
            action_match = re.search(r"Action:\s*(.*?)\n", response)
            action_input_match = re.search(r"Action Input:\s*(.*)", response)
            
            if action_match and action_input_match:
                action_name = action_match.group(1).strip()
                action_input = action_input_match.group(1).strip()
                
                print(f"[Executing Tool: {action_name} with input: {action_input}]")
                
                if action_name in TOOLS:
                    observation = TOOLS[action_name](action_input)
                else:
                    observation = f"Error: Tool '{action_name}' not found."
                
                print(f"Observation: {observation}")
                prompt += f"Observation: {observation}\n"
            else:
                # LLM output didn't conform perfectly, force it to think again or fail gracefully
                prompt += "Observation: Formatting error. Please use Thought/Action/Action Input/Observation format or provide Final Answer.\n"

        return "Max steps reached without a Final Answer."

if __name__ == "__main__":
    use_api_flag = os.environ.get("USE_API", "False").lower() in ("true", "1", "yes")
    agent = ReActAgent(use_api=use_api_flag)
    
    q = "Who is the President of the US and what is his age multiplied by 2?"
    print(f"Starting ReAct loop for question: {q}")
    final_answer = agent.run(q)
    print(f"\n>>> FINAL OUTPUT: {final_answer}")
