# Project 1: Basic Retrieval-Augmented Generation (RAG) Pipeline

## Objective
Build a complete Retrieval-Augmented Generation (RAG) pipeline from scratch using Python. The system should be able to ingest a small set of documents, chunk them, embed them, store them in a simple in-memory vector store, retrieve the most relevant chunks given a user query, and synthesize an answer.

## Design Problem

You need to design a system with the following components:

1. **Document Ingestion & Chunking**
   - Take a list of text documents (e.g., Wikipedia snippets about a specific topic).
   - Split the text into smaller, manageable chunks (e.g., by sentences or fixed character counts with overlap).

2. **Embedding Model**
   - Use a local embedding model to convert text chunks into dense vector representations.
   - *Hint: Look into `sentence-transformers` for an easy local embedding solution.*

3. **Vector Store & Retrieval**
   - Implement a simple in-memory vector database (e.g., a Python list or a NumPy array).
   - Implement a similarity search function (e.g., Cosine Similarity) to find the top-K most relevant chunks for a given query vector.

4. **Generator / LLM**
   - Pass the retrieved context and the user's query to an LLM to generate a final answer.
   - **Requirement**: Your code should support a local model (e.g., using Ollama or a local HuggingFace pipeline) but also allow switching to an API-based model (like Google Gemini or OpenAI) via an environment variable or configuration.

## Challenge
Try building this yourself without looking at the solution! 
- Start by hardcoding 3-4 paragraphs of text.
- Create the chunking logic.
- Compute cosine similarity manually using `numpy` or `scipy`.
- Craft the prompt: `"Use the following context to answer the query: {context}\n\nQuery: {query}"`

Once you are done, compare your implementation with `01_basic_rag_project_solution.py`.
