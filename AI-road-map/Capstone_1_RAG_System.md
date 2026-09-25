# Capstone Project 1: The End-to-End <abbr title="Retrieval-Augmented Generation">RAG</abbr> System

## Objective
Build a system that can accurately answer questions based entirely on a private corpus of documents (e.g., your personal PDFs, codebase, or company handbooks). The <abbr title="Large Language Model">LLM</abbr> must not hallucinate external knowledge.

## Tech Stack to Use
- **Data Orchestration:** LlamaIndex or LangChain Core
- **Vector Database:** ChromaDB (for local persistent storage)
- **Embeddings:** OpenAI `text-embedding-3-small` or Hugging Face `all-MiniLM-L6-v2`
- **<abbr title="Large Language Model">LLM</abbr>:** OpenAI `gpt-4o-mini` or Anthropic `claude-3-haiku`

## Step-by-Step Implementation Guide

### Step 1: Data Ingestion & Chunking
1. Create a folder named `data/` and place 3-5 complex PDF files inside it.
2. Write a Python script using `SimpleDirectoryReader` (LlamaIndex) to load the text.
3. Use a `SentenceSplitter` to break the text into chunks. 
   - *Experiment:* Try a `chunk_size` of 512 with an overlap of 50.

### Step 2: Embedding & Storage
1. Initialize a `chromadb.PersistentClient` saving to `./chroma_db`.
2. Create a collection.
3. Pass your chunks through the embedding model and store them in ChromaDB.

### Step 3: Retrieval Pipeline
1. Build a retriever that takes a string (the user's question).
2. Embed the user's question.
3. Perform a semantic similarity search against ChromaDB to return the top `k=3` most relevant chunks.

### Step 4: Generation Pipeline
1. Construct a strict Prompt Template:
   > "You are an expert assistant. Answer the user's question using ONLY the following context. If the context does not contain the answer, say 'I do not know.'"
2. Inject the retrieved chunks into the prompt.
3. Call the <abbr title="Large Language Model">LLM</abbr> and print the response.

### Pro-Level Extensions (Optional but highly recommended)
- **Metadata Filtering:** Add metadata to your chunks (e.g., "Year=2024", "Department=Engineering") and implement a feature where the user can filter the search space before querying.
- **<abbr title="Retrieval-Augmented Generation">RAG</abbr> Evaluation:** Write 10 test questions and use the **Ragas** library to calculate the `faithfulness` and `context_precision` of your system.
