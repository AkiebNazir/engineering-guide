# Day 87: Vector Databases (Qdrant, Pinecone, FAISS)

Welcome to Day 87. In Phase 3, we built <abbr title="Retrieval-Augmented Generation">RAG</abbr> using FAISS in memory. 

But FAISS is just a C++ library. If your server crashes, the FAISS index is deleted from RAM. It also doesn't natively support advanced metadata filtering or multi-node clustering.
When building Enterprise <abbr title="Retrieval-Augmented Generation">RAG</abbr>, you need a true **Vector Database**. Today, we evaluate the landscape and build a local database using Qdrant.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. HNSW (Hierarchical Navigable Small World)
FAISS uses IVF-PQ (Inverted File with Product Quantization) to search fast. 
Modern Vector DBs (like Qdrant and Pinecone) use an algorithm called **HNSW**. 
- Imagine the database is a map of a city. 
- HNSW builds a multi-layered graph of vectors. 
- The top layer has very few connections (Highways). 
- The middle layer has more connections (Main streets). 
- The bottom layer has massive connections (Local roads).
When a query enters, it drops into the top layer, instantly travels down the "Highway" to the general vicinity of the answer, and then drops to the bottom layer to find the exact nearest neighbor. 
**Trade-off:** HNSW achieves lightning-fast sub-millisecond search, but requires massive amounts of RAM to store all the graph connections.

### 2. The Vector Database Landscape
- **FAISS:** Facebook's open-source library. Insanely fast, but requires custom engineering to persist to disk or scale across servers.
- **Pinecone:** Fully managed, serverless DB. Zero ops required. But it is closed-source and highly expensive at scale.
- **ChromaDB:** Python-native, extremely lightweight. Perfect for local prototyping, Jupyter notebooks, and tiny apps.
- **Qdrant / Milvus:** Written in Rust / Go. Open-source, blazing fast, enterprise-grade. They support distributed clustering, disk-persistence, and advanced pre-filtering.

### 3. Pre-filtering vs Post-filtering
Imagine you have 10 Million legal documents. A user searches for: *"Breach of contract cases in the year 2023"*.
- **Post-filtering (Bad):** The DB runs an ANN search and finds the Top 100 semantic matches for "Breach of contract". It *then* checks the metadata. If all 100 documents happen to be from 2022, the DB returns $0$ results to the user!
- **Pre-filtering (Good):** Modern databases (like Qdrant) look at the query metadata `{"year": 2023}`. They mathematically slice the Vector Space, temporarily masking out all non-2023 vectors. The ANN search *only* runs inside the 2023 sub-space, guaranteeing 100 perfect hits!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a production-ready Vector DB using **Qdrant**. We will create a collection, insert vectors with complex metadata, and perform a Pre-Filtered semantic search.

*(Mentally run: `pip install qdrant-client sentence-transformers`)*

Create a file named `qdrant_database.py`:

```python
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct, Filter, FieldCondition, MatchValue
from sentence_transformers import SentenceTransformer

def build_qdrant_db():
    print("--- RUNNING QDRANT VECTOR DATABASE ---")
    
    # 1. Initialize an in-memory Qdrant client (for production, use a URL and API Key!)
    client = QdrantClient(":memory:")
    
    # 2. Load the Embedding Model
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    VECTOR_DIMENSION = 384
    
    # 3. Create a Collection (Like a SQL Table)
    collection_name = "enterprise_knowledge"
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=VECTOR_DIMENSION, distance=Distance.COSINE),
    )
    print(f"Collection '{collection_name}' created successfully!")
    
    # 4. Our Data + Metadata!
    documents = [
        {"id": 1, "text": "The Q3 earnings report shows a 20% increase in revenue.", "dept": "finance", "year": 2023},
        {"id": 2, "text": "The new Python API v2 will be released next week.", "dept": "engineering", "year": 2024},
        {"id": 3, "text": "Employee health benefits have been expanded to cover dental.", "dept": "hr", "year": 2024},
        {"id": 4, "text": "Q1 2024 financial projections estimate a slight downturn.", "dept": "finance", "year": 2024}
    ]
    
    # Embed the texts
    texts = [doc["text"] for doc in documents]
    embeddings = embedder.encode(texts)
    
    # 5. Insert Points (Vectors + Metadata) into Qdrant
    points = []
    for doc, emb in zip(documents, embeddings):
        points.append(
            PointStruct(
                id=doc["id"], 
                vector=emb.tolist(), 
                payload={"department": doc["dept"], "year": doc["year"], "text": doc["text"]} # The Metadata!
            )
        )
        
    client.upsert(collection_name=collection_name, points=points)
    print("Inserted 4 documents with complex metadata payloads.\n")
    
    # 6. RETRIEVAL: Pre-Filtered Semantic Search!
    user_query = "What is the financial outlook?"
    query_vector = embedder.encode([user_query])[0].tolist()
    
    print(f"User Query: '{user_query}'")
    print("Executing search with PRE-FILTER: Only return documents from 'finance' in '2024'...\n")
    
    # Define the exact Pre-Filter
    query_filter = Filter(
        must=[
            FieldCondition(key="department", match=MatchValue(value="finance")),
            FieldCondition(key="year", match=MatchValue(value=2024))
        ]
    )
    
    # Execute the Search!
    search_result = client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        query_filter=query_filter,
        limit=2
    )
    
    # Print Results
    for hit in search_result:
        print(f"ID: {hit.id} | Score: {hit.score:.4f}")
        print(f"Payload: {hit.payload}\n")

if __name__ == "__main__":
    build_qdrant_db()
```

### Key Takeaways from Code:
1. **The Payload:** Notice how Qdrant stores the original `text` directly inside the database `payload`. This means you don't need a separate Postgres SQL database to hold your text! Qdrant acts as both the vector index and the document store.
2. **The Pre-Filter:** Even though Document #1 ("Q3 earnings") might have a higher Cosine Similarity to the query, the DB strictly ignores it because its `year` payload is 2023. This is essential for access-control (e.g., `user_id = 99`).

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: ChromaDB Persistence
ChromaDB is the most popular local DB for hackers. 
**Your Task:**
1. Conceptually design a script using the `chromadb` library.
2. Initialize a `PersistentClient(path="./chroma_db")`.
3. Create a collection and add 3 documents (ChromaDB automatically handles the embedding for you!).
4. Close the python script.
5. Write a second python script that connects to `./chroma_db` and successfully queries the documents. You have achieved local persistence!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are building a semantic search platform for 100 Million documents. The CEO asks you to choose between FAISS, Qdrant, and Pinecone. Discuss indexing strategy, query latency SLAs, cost, and operational complexity."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The FAISS Trade-off:** 
   - FAISS has the lowest latency and zero licensing costs. 
   - However, for 100M documents, operational complexity is a nightmare. You must manually write the C++ or Python code to shard the index across multiple machines, implement Raft consensus for high availability, and write custom metadata filtering logic. Not worth the engineering time.
2. **The Pinecone Trade-off:**
   - Serverless and zero ops. You can launch 100M vectors tomorrow.
   - However, it is insanely expensive at scale. You are locked into their proprietary ecosystem, and network latency is higher because you are making REST <abbr title="Application Programming Interface">API</abbr> calls across the public internet to their servers.
3. **The Qdrant/Milvus Choice (The Sweet Spot):**
   - Propose using open-source Qdrant or Milvus deployed on your own Kubernetes cluster inside your own VPC. 
   - This provides the advanced HNSW and Pre-filtering features of Pinecone, with the sub-millisecond local network latency and absolute data-privacy of FAISS.

---
**Task for the end of the day:** Commit your code to Git. 

Tomorrow, in **Day 88**, we step away from databases and focus purely on the <abbr title="Large Language Model">LLM</abbr> itself. We will master the algorithms of **Prompt Engineering (Chain of Thought, Self-Consistency, and Tree of Thought)**!
