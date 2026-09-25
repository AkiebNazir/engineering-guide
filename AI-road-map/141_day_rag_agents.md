# Day 141: RAG Agents (Corrective RAG & Routing)

Welcome to Day 141. 

Back in Phase 3 (Day 83), we learned basic <abbr title="Retrieval-Augmented Generation">RAG</abbr>. Basic <abbr title="Retrieval-Augmented Generation">RAG</abbr> is "blind". It takes a user query, pulls the top 5 chunks from a Vector DB, and forces the <abbr title="Large Language Model">LLM</abbr> to write an answer. 
But what if the Vector DB returns 5 chunks of irrelevant garbage? The <abbr title="Large Language Model">LLM</abbr> will still try to answer, resulting in massive hallucinations.

Today, we upgrade <abbr title="Retrieval-Augmented Generation">RAG</abbr> to **Agentic <abbr title="Retrieval-Augmented Generation">RAG</abbr>**. We give the <abbr title="Retrieval-Augmented Generation">RAG</abbr> pipeline a brain, allowing it to route queries, grade documents, and dynamically fallback to the open web!

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Query Routing
Before retrieving anything, an Agent (or a fast classifier model) reads the user's prompt and decides *where* to look.
- If the prompt is *"What were my sales yesterday?"* $\rightarrow$ Route to **<abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> Agent**.
- If the prompt is *"How do I install the software?"* $\rightarrow$ Route to **Vector DB (Docs)**.
- If the prompt is *"Who won the game last night?"* $\rightarrow$ Route to **Web Search <abbr title="Application Programming Interface">API</abbr>**.

### 2. Corrective <abbr title="Retrieval-Augmented Generation">RAG</abbr> (CRAG)
This is a famous LangGraph architecture that fixes "blind" retrieval.
1. **Retrieve:** Pull 5 documents from the Vector DB.
2. **Grade:** An Evaluator <abbr title="Large Language Model">LLM</abbr> reads the 5 documents. If a document does not actually answer the user's question, the Evaluator deletes it.
3. **Fallback:** If *all* documents were deleted (the Vector DB failed), the Agent does not hallucinate. It dynamically rewrites the user's query and fires off a **Tavily Web Search** to find the answer on the internet!

### 3. Self-<abbr title="Retrieval-Augmented Generation">RAG</abbr>
Instead of using complex LangGraph routing, Self-<abbr title="Retrieval-Augmented Generation">RAG</abbr> uses a specifically fine-tuned <abbr title="Large Language Model">LLM</abbr>. During generation, the <abbr title="Large Language Model">LLM</abbr> emits special tokens:
- `[Retrieve]`: The <abbr title="Large Language Model">LLM</abbr> pauses itself and tells the system to fetch data.
- `[IsRelevant]`: The <abbr title="Large Language Model">LLM</abbr> grades the data it just received.
- `[IsSupported]`: The <abbr title="Large Language Model">LLM</abbr> verifies that the sentence it is currently writing is actually backed by the retrieved data!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual **CRAG (Corrective <abbr title="Retrieval-Augmented Generation">RAG</abbr>) Pipeline**! We will simulate the grading node and the Web Search fallback.

Create a file named `crag_agent.py`:

```python
# --- 1. MOCK DATA SOURCES ---
mock_vector_db = {
    "AI trends": "In 2026, multi-modal agents became the industry standard."
}

def mock_web_search(query):
    print(f"   [WEB API] Searching the internet for: '{query}'...")
    return "Web Result: Quantum computing saw a major breakthrough in 2026."

# --- 2. CRAG NODES ---

def retrieve_node(query):
    print(f"\n[NODE: RETRIEVE] Querying internal Vector DB for '{query}'...")
    # Simulate a hit or miss
    if "AI" in query:
        return mock_vector_db["AI trends"]
    return "Irrelevant document about office supplies."

def grade_node(query, document):
    print(f"[NODE: GRADER] Evaluating if document answers the query...")
    # A real LLM would do semantic grading here. We mock the logic.
    if "office supplies" in document:
        print("   -> FAIL: Document is irrelevant to the query!")
        return "FAIL"
    print("   -> PASS: Document is highly relevant.")
    return "PASS"

def generate_node(document):
    print(f"[NODE: GENERATOR] Writing final answer based on: '{document}'")
    return f"Final Answer: Based on the provided context, {document.lower()}"

def web_fallback_node(query):
    print(f"[NODE: WEB FALLBACK] Internal DB failed. Falling back to the Internet.")
    # The agent rewrites the query for better SEO
    optimized_query = f"Latest news {query}"
    web_doc = mock_web_search(optimized_query)
    return web_doc

# --- 3. THE CRAG ORCHESTRATOR ---
def run_crag_workflow(user_query):
    print("--- RUNNING CORRECTIVE RAG (CRAG) PIPELINE ---\n")
    print(f"User: {user_query}")
    
    # Step 1: Retrieve
    retrieved_doc = retrieve_node(user_query)
    
    # Step 2: Grade
    grade = grade_node(user_query, retrieved_doc)
    
    # Step 3: Conditional Routing!
    if grade == "PASS":
        # We trust the internal data
        final_output = generate_node(retrieved_doc)
    else:
        # Internal data was garbage. Use the Web!
        web_doc = web_fallback_node(user_query)
        final_output = generate_node(web_doc)
        
    print(f"\n{final_output}")

if __name__ == "__main__":
    print("SCENARIO 1: Vector DB has the answer.")
    run_crag_workflow("What are the AI trends?")
    
    print("\n" + "="*50 + "\n")
    
    print("SCENARIO 2: Vector DB fails. Agent dynamically uses the Web.")
    run_crag_workflow("What is the latest in quantum computing?")
```

### Key Takeaways from Code:
1. **The Grader Node:** This is the most important part of CRAG. By forcing an <abbr title="Large Language Model">LLM</abbr> to explicitly output `PASS` or `FAIL`, we prevent garbage data from ever reaching the final Generator. This virtually eliminates <abbr title="Retrieval-Augmented Generation">RAG</abbr> hallucinations.
2. **Self-Healing <abbr title="Retrieval-Augmented Generation">RAG</abbr>:** In Scenario 2, the basic <abbr title="Retrieval-Augmented Generation">RAG</abbr> pipeline would have crashed or lied. Our Agentic <abbr title="Retrieval-Augmented Generation">RAG</abbr> pipeline realized it didn't know the answer, dynamically pivoted to a Web Search tool, and successfully healed the execution path!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Multi-Source Router
You are building an Enterprise Assistant.
**Your Task:**
1. Conceptually define a Router Agent.
2. If the user says: *"Summarize my PDF"*, route to the Document QA node.
3. If the user says: *"How many users signed up today?"*, route to a Text-to-<abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> node.
4. If the user says: *"Who is the CEO of OpenAI?"*, route to the Web Search node.
5. If the user says: *"Compare the signup data to the PDF guidelines"*, how do you handle it? (Hint: The Router must split the query into two parallel tasks, run both nodes, and aggregate the results!).

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design a <abbr title="Retrieval-Augmented Generation">RAG</abbr> agent for a hospital. It must query patient records (<abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>), clinical guidelines (PDFs), and drug interactions (<abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> <abbr title="Application Programming Interface">API</abbr>). Discuss the routing architecture, access control (HIPAA), and citation mechanisms."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Intent Router:** 
   - Propose an <abbr title="Large Language Model">LLM</abbr> Router that strictly categorizes the intent. If `intent == patient_data`, it triggers the Text-to-<abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> Agent.
2. **Access Control (HIPAA):**
   - The <abbr title="Large Language Model">LLM</abbr> MUST NOT have raw database credentials. Use the **<abbr title="Model Context Protocol">MCP</abbr> (Model Context Protocol)** Gateway pattern from Day 127. The <abbr title="Model Context Protocol">MCP</abbr> Gateway intercepts the query, injects the Doctor's `user_id` into the <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> `WHERE` clause (Row-Level Security), ensuring the doctor can only query their own patients.
3. **Strict Citations:**
   - In healthcare, hallucinations are fatal. The Generator node must be prompted to output strict citations using `[Document_ID]`. 
   - Post-processing: A Regex script verifies that every sentence generated by the <abbr title="Large Language Model">LLM</abbr> contains a citation. If a sentence lacks a citation, the system deletes the sentence before showing it to the doctor!

---
**Task for the end of the day:** Commit your code to Git. 

We have combined <abbr title="Retrieval-Augmented Generation">RAG</abbr> with Agents. 
But text is only one modality. What if the Agent needs to read a pie chart, write code to analyze the data, and navigate a graphical website to email the report?

Tomorrow, in **Day 142**, we learn **Multi-Modal Agents (Vision + Code + Web)**!
