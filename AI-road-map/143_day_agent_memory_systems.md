# Day 143: Agent Memory Systems (Short, Long & Episodic)

Welcome to Day 143. 

Language models have profound amnesia. Every time you start a Python script, the <abbr title="Large Language Model">LLM</abbr> forgets everything about you. 
In Day 129, we briefly touched on CrewAI's memory. Today, we dive into the deep architecture of the famous **MemGPT** paper. We will learn the exact taxonomy of memory and how to build an Agent that remembers you for years!

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Taxonomy of <abbr title="Artificial Intelligence">AI</abbr> Memory
Human brains have different storage mechanisms. <abbr title="Artificial Intelligence">AI</abbr> needs them too.
- **Working Memory (RAM):** The <abbr title="Large Language Model">LLM</abbr>'s current Context Window (e.g., 128k tokens). It is instantly accessible but strictly limited by the <abbr title="Application Programming Interface">API</abbr>. If it overflows, the Agent crashes.
- **Short-Term Memory (L1 Cache):** The `ConversationBuffer` holding the last 10 messages of the *current* session. As new messages arrive, old ones are popped off the queue.
- **Semantic Memory (Hard Drive):** General facts stored in a Vector DB. If the user says *"I am allergic to peanuts"*, the Agent extracts that fact and saves it. 
- **Episodic Memory (The Diary):** Specific past interactions. *"Last Tuesday, the user asked me to debug their router, and we solved it by restarting the DNS."* This allows the Agent to perform Case-Based Reasoning (*"Oh, this error looks like the one we fixed last week!"*).

### 2. Memory Consolidation (The Sleep Cycle)
If you chat with an Agent for 8 hours, the Short-Term memory buffer will overflow.
**Memory Consolidation** is the <abbr title="Artificial Intelligence">AI</abbr> equivalent of sleeping. 
At midnight, a background cron job wakes up a "Summarizer Agent". It reads the 8 hours of raw chat logs, extracts the key entities (*"User learned Python today"*), saves those facts to Semantic Memory, and then permanently deletes the raw logs to save space! 

### 3. Retrieval Strategy (Recency vs Relevance)
When the user asks a question, how does the Agent know what to retrieve?
The Agent queries the Vector DB using two weights:
1. **Relevance (Cosine Similarity):** Does this memory match the current topic?
2. **Recency:** Is this memory from today, or 5 years ago? (You mathematically decay the score of older memories so the Agent prioritizes recent context).

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Persistent Memory Manager! We will simulate an Agent that uses Short-Term memory for the immediate conversation, but queries Long-Term memory *before* answering to ensure it doesn't forget user preferences.

Create a file named `agent_memory.py`:

```python
import time

# --- 1. THE MEMORY STORES ---
class MemoryManager:
    def __init__(self):
        # Short-term: Just a python list (cleared on restart)
        self.short_term_buffer = []
        
        # Long-term: Simulated Vector DB (persists across restarts)
        self.semantic_db = {
            "dietary_restrictions": "User is severely allergic to peanuts.",
            "coding_preference": "User hates Java, prefers Python."
        }
        
    def add_short_term(self, role, message):
        self.short_term_buffer.append({"role": role, "content": message})
        # Keep only the last 4 messages to prevent context overflow!
        if len(self.short_term_buffer) > 4:
            self.short_term_buffer.pop(0)
            
    def retrieve_long_term(self, topic):
        print(f"   [MEMORY] Searching Long-Term Vector DB for '{topic}'...")
        time.sleep(0.5) # Simulate DB latency
        
        if "food" in topic or "eat" in topic or "recipe" in topic:
            return self.semantic_db["dietary_restrictions"]
        if "code" in topic or "program" in topic:
            return self.semantic_db["coding_preference"]
        return None

# --- 2. THE MEMORY-AWARE AGENT ---
def run_memory_agent():
    print("--- RUNNING MEMORY-AWARE AGENT ---\n")
    
    memory = MemoryManager()
    
    def process_user_input(user_msg):
        print(f"\nUser: {user_msg}")
        memory.add_short_term("user", user_msg)
        
        # Step 1: The Agent extracts the 'Topic' and queries Long-Term Memory FIRST
        print("   [AGENT] Extracting intent and querying past memories...")
        retrieved_fact = memory.retrieve_long_term(user_msg)
        
        # Step 2: The Agent formulates the response using BOTH memories
        print("   [AGENT] Generating response...")
        
        if retrieved_fact and "peanut" in retrieved_fact:
            response = "I found a great Thai recipe! I made sure to substitute the peanut sauce with almond butter based on your allergy profile."
        elif retrieved_fact and "Java" in retrieved_fact:
            response = "I will write this script in Python for you, since I remember you dislike Java."
        else:
            response = "I can certainly help with that!"
            
        print(f"Agent: {response}")
        memory.add_short_term("agent", response)

    # --- SIMULATING A CHAT SESSION ---
    process_user_input("Can you write a script to sort an array?")
    process_user_input("I am hungry, give me a Thai recipe.")

if __name__ == "__main__":
    run_memory_agent()
```

### Key Takeaways from Code:
1. **Context Enrichment:** By querying the `semantic_db` *before* hitting the <abbr title="Large Language Model">LLM</abbr> <abbr title="Application Programming Interface">API</abbr>, the Agent injected the user's peanut allergy into the prompt. The user didn't have to remind the Agent! This creates a magical User Experience.
2. **Buffer Management:** Notice the `if len > 4: pop(0)` logic. This is the simplest form of Short-Term memory management. It acts as a sliding window over the conversation, ensuring the Agent never crashes due to a `max_tokens` error.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Memory Consolidator
Your agent's short-term buffer is full. It is time for it to "sleep".
**Your Task:**
1. Conceptually define a `consolidate_memory()` function that runs as a background task.
2. It takes the entire `short_term_buffer` (e.g., a 50-message debate about React vs Angular).
3. It passes the buffer to an <abbr title="Large Language Model">LLM</abbr> with the prompt: *"Extract 3 permanent facts about the user from this transcript. Format as JSON."*
4. It saves those JSON facts to the `semantic_db` and completely erases the `short_term_buffer`.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design a memory system for a personal <abbr title="Artificial Intelligence">AI</abbr> assistant used by 10 Million users. Each user has years of conversation history. Discuss storage, retrieval latency, privacy, and the cold-start problem."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Storage Architecture (Multi-Tenant Vector DB):** 
   - State that you cannot have 10 Million separate databases. You use a massive distributed Vector DB (like Pinecone or Milvus). 
   - *Crucial:* Every vector must be tagged with `user_id`. You must use Metadata Filtering (`WHERE user_id = 123`) *before* running the costly Cosine Similarity search to ensure users never cross-contaminate memories.
2. **The Cold-Start Problem:**
   - When a new user signs up, their memory is completely empty. The Agent will feel stupid.
   - Propose an "Onboarding Flow" where the user fills out a quick 5-question survey (diet, job, location). This instantly primes the Semantic Memory before the first chat even begins.
3. **Privacy (The Right to be Forgotten):**
   - If a user clicks "Delete my account", you must be able to delete all their vectors instantly. Standard LLMs bake data into their weights (impossible to delete). Memory systems keep data in a database, making GDPR compliance trivial!

---
**Task for the end of the day:** Commit your code to Git. 

Our Agents now have perfect memory. 
But up until now, all our multi-agent systems ran inside the *same* Python script. What if Agent A runs on AWS, and Agent B runs on Azure? How do they talk to each other over the internet?

Tomorrow, in **Day 144**, we learn **Agent Communication Protocols (A2A) and Message Passing**!
