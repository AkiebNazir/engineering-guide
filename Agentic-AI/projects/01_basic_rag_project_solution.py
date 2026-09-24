import os
import numpy as np
from typing import List, Tuple
import json
import urllib.request
import urllib.error

# For local embeddings
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("Please install sentence-transformers: pip install sentence-transformers")
    exit(1)


class SimpleVectorStore:
    def __init__(self):
        self.embeddings = []
        self.chunks = []

    def add(self, chunks: List[str], embeddings: np.ndarray):
        self.chunks.extend(chunks)
        if len(self.embeddings) == 0:
            self.embeddings = embeddings
        else:
            self.embeddings = np.vstack([self.embeddings, embeddings])

    def search(self, query_embedding: np.ndarray, top_k: int = 2) -> List[Tuple[str, float]]:
        if len(self.embeddings) == 0:
            return []
        
        # Calculate cosine similarity
        norm_query = np.linalg.norm(query_embedding)
        norm_db = np.linalg.norm(self.embeddings, axis=1)
        
        # Avoid division by zero
        if norm_query == 0: return []
        
        similarities = np.dot(self.embeddings, query_embedding) / (norm_db * norm_query)
        
        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]
        
        return [(self.chunks[i], similarities[i]) for i in top_indices]


class RAGPipeline:
    def __init__(self, use_api=False):
        self.use_api = use_api
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
        print("Loading local embedding model (all-MiniLM-L6-v2)...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.vector_store = SimpleVectorStore()
        
        if self.use_api and not self.api_key:
            print("WARNING: use_api is True but GEMINI_API_KEY is not set. Falling back to local Ollama.")
            self.use_api = False

    def embed_text(self, text: str | List[str]) -> np.ndarray:
        return self.embedding_model.encode(text)

    def ingest(self, documents: List[str]):
        # Very simple chunking by splitting on double newlines
        chunks = []
        for doc in documents:
            paragraphs = [p.strip() for p in doc.split('\n\n') if p.strip()]
            chunks.extend(paragraphs)
            
        print(f"Ingesting {len(chunks)} chunks...")
        embeddings = self.embed_text(chunks)
        self.vector_store.add(chunks, embeddings)
        print("Ingestion complete.")

    def generate_local(self, prompt: str) -> str:
        """Uses local Ollama instance (requires Ollama running with e.g. llama3)"""
        url = "http://localhost:11434/api/generate"
        data = {
            "model": "llama3", # change this to your local model
            "prompt": prompt,
            "stream": False
        }
        
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode())
                return result.get('response', "Error generating response.")
        except urllib.error.URLError as e:
            return f"Error communicating with local Ollama: {e}. Is Ollama running?"

    def generate_api(self, prompt: str) -> str:
        """Uses Gemini API as an example of cloud fallback"""
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

    def ask(self, query: str) -> str:
        query_emb = self.embed_text(query)
        top_results = self.vector_store.search(query_emb, top_k=2)
        
        if not top_results:
            return "I don't have any context to answer that."
            
        context = "\n".join([res[0] for res in top_results])
        
        prompt = f"""You are a helpful assistant. Use the following context to answer the user's question accurately. If the answer is not in the context, say "I don't know based on the provided context."

Context:
{context}

Question: {query}
Answer:"""

        print(f"\n--- Retrieved Context ---\n{context}\n-------------------------\n")
        
        if self.use_api:
            print("Generating with Gemini API...")
            return self.generate_api(prompt)
        else:
            print("Generating with Local Model (Ollama)...")
            return self.generate_local(prompt)


if __name__ == "__main__":
    sample_docs = [
        "Agentic AI systems rely heavily on reasoning loops, such as ReAct, where the LLM interleaves thinking and tool execution. This allows them to interact with the environment.",
        "Vector databases index dense embeddings. Common algorithms include Hierarchical Navigable Small World (HNSW) and Inverted File (IVF) to ensure fast approximate nearest neighbor (ANN) search.",
        "GraphRAG integrates knowledge graphs into the RAG pipeline. It provides explicit relationships between entities, solving multi-hop reasoning problems that standard dense retrieval often fails at."
    ]
    
    # Set to True if you have GEMINI_API_KEY set, else uses local Ollama
    use_api_flag = os.environ.get("USE_API", "False").lower() in ("true", "1", "yes")
    
    rag = RAGPipeline(use_api=use_api_flag)
    rag.ingest(sample_docs)
    
    question = "What algorithms do vector databases use for fast search?"
    print(f"Question: {question}")
    answer = rag.ask(question)
    print(f"\nFinal Answer: {answer}")
