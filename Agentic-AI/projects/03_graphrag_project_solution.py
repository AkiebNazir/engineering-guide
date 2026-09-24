import os
import json
import urllib.request
import urllib.error
import re
from collections import defaultdict

class MiniGraphRAG:
    def __init__(self, use_api=False):
        self.use_api = use_api
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
        # Graph structure: { node: [ (relation, target_node), ... ] }
        self.graph = defaultdict(list)
        
        if self.use_api and not self.api_key:
            print("WARNING: use_api is True but GEMINI_API_KEY is not set. Falling back to local Ollama.")
            self.use_api = False

    def llm_generate(self, prompt: str) -> str:
        """Abstraction for calling the LLM"""
        if self.use_api:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
            data = {
                "contents": [{"parts":[{"text": prompt}]}]
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
                "stream": False
            }
            try:
                req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(req) as response:
                    result = json.loads(response.read().decode())
                    return result.get('response', "Error generating response.")
            except Exception as e:
                return f"Local Model Error: {e}"

    def extract_triplets(self, text: str):
        prompt = f"""Extract entities and relationships from the text below.
Return ONLY a valid JSON array of objects. Each object must have exactly three keys: "source", "relation", and "target".

Example:
[
  {{"source": "Alice", "relation": "works at", "target": "Google"}},
  {{"source": "Google", "relation": "located in", "target": "California"}}
]

Text:
{text}
"""
        response = self.llm_generate(prompt)
        
        # Try to parse the JSON output
        try:
            # Clean markdown formatting if present
            clean_resp = re.sub(r'```json\s*', '', response)
            clean_resp = re.sub(r'```\s*', '', clean_resp).strip()
            
            triplets = json.loads(clean_resp)
            for t in triplets:
                if 'source' in t and 'relation' in t and 'target' in t:
                    self.add_edge(t['source'], t['relation'], t['target'])
            print(f"Extracted {len(triplets)} relationships.")
        except json.JSONDecodeError as e:
            print("Failed to parse LLM output as JSON:")
            print(response)

    def add_edge(self, source: str, relation: str, target: str):
        self.graph[source].append((relation, target))

    def get_neighborhood(self, start_node: str, hops: int = 2) -> str:
        """Extract a local subgraph context string."""
        # Simple BFS
        visited = set()
        queue = [(start_node, 0)]
        context_triplets = []
        
        # Case insensitive key search for robustness
        start_node = next((k for k in self.graph.keys() if k.lower() == start_node.lower()), start_node)

        while queue:
            current, current_hop = queue.pop(0)
            
            if current in visited or current_hop >= hops:
                continue
                
            visited.add(current)
            
            for relation, target in self.graph.get(current, []):
                context_triplets.append(f"{current} --[{relation}]--> {target}")
                queue.append((target, current_hop + 1))
                
        return "\n".join(context_triplets)

    def answer_question(self, question: str, start_entity: str) -> str:
        # Get context up to 2 hops away from the starting entity
        context = self.get_neighborhood(start_entity, hops=2)
        
        if not context:
            return f"I don't have any knowledge about '{start_entity}' in my graph."
            
        prompt = f"""You are a Graph QA bot. Use ONLY the provided Graph Context to answer the question.
If the graph context doesn't contain the answer, say "I don't know based on the graph."

Graph Context:
{context}

Question: {question}
Answer:"""

        print(f"\n--- Graph Context Extracted ---\n{context}\n-------------------------------\n")
        return self.llm_generate(prompt)


if __name__ == "__main__":
    use_api_flag = os.environ.get("USE_API", "False").lower() in ("true", "1", "yes")
    graph_rag = MiniGraphRAG(use_api=use_api_flag)
    
    text = """Marie Curie was born in Warsaw. She later moved to Paris to study. 
In Paris, she discovered Radium. Radium is a highly radioactive element. 
Pierre Curie also lived in Paris and was married to Marie Curie."""

    print("Extracting knowledge graph...")
    graph_rag.extract_triplets(text)
    
    q = "What did the person married to Pierre Curie discover?"
    print(f"\nQuestion: {q}")
    answer = graph_rag.answer_question(q, start_entity="Pierre Curie")
    
    print(f"\nFinal Answer: {answer}")
