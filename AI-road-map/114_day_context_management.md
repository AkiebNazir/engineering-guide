# Day 114: Multi-Turn Conversation & Context Management

Welcome to Day 114. You built a chatbot. You deployed it. 
A user logs in and talks to it for 2 hours. Suddenly, the app crashes with an error: **"TokenLimitExceeded: Context Window exceeds 8192 tokens."**

LLMs are entirely stateless. They have no internal memory of the conversation. When the user sends their 100th message, you (the developer) have to bundle up the previous 99 messages and send them ALL to the <abbr title="Large Language Model">LLM</abbr> again. 
This means <abbr title="Application Programming Interface">API</abbr> costs grow exponentially with every turn, and eventually, the array of messages hits the physical VRAM limit of the Transformer architecture.

Today, we solve this by mastering **Context Management**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Context Window Limit
Every <abbr title="Large Language Model">LLM</abbr> has a Maximum Sequence Length (e.g., Llama 3 has 8192 tokens, GPT-4 has 128k tokens). This is the absolute maximum number of words the Attention Mechanism can process in a single mathematical pass. 
The "Context Budget" is divided into:
`System Prompt + Tool Schemas + Chat History + User Message + Output Generation = Total Tokens`
If your Chat History consumes $90\%$ of the budget, the <abbr title="Large Language Model">LLM</abbr> will only have enough tokens left to generate a 1-sentence response before crashing!

### 2. Strategy 1: Truncation (The Goldfish)
The easiest solution is a Sliding Window (FIFO - First In, First Out). 
You only keep the last 10 messages in the array. When message 11 arrives, you delete message 1.
**Pros:** Easy to code. Never crashes.
**Cons:** The <abbr title="Artificial Intelligence">AI</abbr> becomes a goldfish. If the user told the <abbr title="Artificial Intelligence">AI</abbr> their name in message 1, by message 11, the <abbr title="Artificial Intelligence">AI</abbr> has completely forgotten who the user is!

### 3. Strategy 2: Rolling Summarization
When the history array hits a certain limit (e.g., 3000 tokens), you pause the conversation. 
You take the 3000 tokens of history and pass them to a fast, cheap <abbr title="Large Language Model">LLM</abbr> (like Llama 8B or GPT-4o-mini). You prompt it: *"Summarize this conversation into exactly 200 tokens."*
You delete the 3000 tokens of history and replace them with the 200-token summary! The context window is completely cleared, but the core facts remain.

### 4. Strategy 3: Retrieval-Augmented Memory (<abbr title="Retrieval-Augmented Generation">RAG</abbr> Memory)
You treat the Chat History exactly like a PDF document!
Every time the user sends a message, you embed it into a Vector Database.
When the user asks *"What was that book you recommended earlier?"*, you embed their question, search the Vector DB for the top 5 most relevant past messages, and inject *only* those 5 messages into the context window. Infinite memory with zero token bloat!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Python Conversation Manager. We will implement the **Rolling Summarization** technique to ensure a conversation can last infinitely.

Create a file named `context_manager.py`:

```python
def mock_summarize_llm(chat_history):
    """
    Simulates a cheap, fast LLM call to compress the chat history.
    """
    print("[SYSTEM] Compressing 500-token history into a 30-token summary...")
    return "User is Alice. Discussed learning Python. Alice struggles with loops."

def mock_chat_llm(system_prompt, messages):
    """
    Simulates the main conversational LLM.
    """
    return "I can help with that. What do you want to learn next?"

class ConversationManager:
    def __init__(self, token_limit=5):
        # We set an absurdly small token limit (5 messages) to trigger the compression instantly!
        self.max_messages = token_limit
        self.system_prompt = "You are a helpful Python tutor."
        
        # This holds the rolling summary of older messages
        self.summary = "" 
        
        # This holds the recent raw messages
        self.recent_messages = [] 
        
    def add_user_message(self, text):
        self.recent_messages.append({"role": "user", "content": text})
        self.check_and_compress()
        
    def add_assistant_message(self, text):
        self.recent_messages.append({"role": "assistant", "content": text})
        self.check_and_compress()
        
    def check_and_compress(self):
        """The Magic: If the history gets too long, compress it!"""
        if len(self.recent_messages) > self.max_messages:
            print(f"\n[ALERT] Context Limit Reached ({len(self.recent_messages)} messages). Triggering Compression!")
            
            # 1. Combine the OLD summary with the OLDEST messages in the recent array
            text_to_summarize = f"Old Summary: {self.summary}\nRecent Chat: {self.recent_messages[:3]}"
            
            # 2. Generate a new, unified summary
            self.summary = mock_summarize_llm(text_to_summarize)
            
            # 3. Delete the messages we just summarized! Keep only the newest ones.
            self.recent_messages = self.recent_messages[3:]
            print(f"[ALERT] Compression Complete. History reduced to {len(self.recent_messages)} raw messages.\n")

    def build_final_prompt(self):
        """Constructs the payload to send to the LLM."""
        payload = [{"role": "system", "content": self.system_prompt}]
        
        # Inject the Summary as a persistent system memory!
        if self.summary:
            payload.append({"role": "system", "content": f"Memory of past conversation: {self.summary}"})
            
        # Append the recent raw messages
        payload.extend(self.recent_messages)
        return payload

def run_chat_app():
    print("--- RUNNING MULTI-TURN CONVERSATION MANAGER ---\n")
    
    manager = ConversationManager(token_limit=3) # Very small limit!
    
    # Simulate a long conversation
    turns = [
        "Hi, I'm Alice.",
        "I want to learn Python.",
        "Can you explain for loops?",
        "I'm still confused about the syntax.", # This 4th message will trigger compression!
        "What about while loops?"
    ]
    
    for user_msg in turns:
        print(f"User: {user_msg}")
        manager.add_user_message(user_msg)
        
        # See what we are actually sending to the LLM!
        payload = manager.build_final_prompt()
        print(f"   -> Payload sent to LLM contains {len(payload)} items.")
        
        # Get AI response
        ai_response = mock_chat_llm(manager.system_prompt, payload)
        manager.add_assistant_message(ai_response)
        
    print("\n--- FINAL CONVERSATION STATE ---")
    print(f"Current Summary Memory: '{manager.summary}'")
    print(f"Number of Raw Messages stored: {len(manager.recent_messages)}")

if __name__ == "__main__":
    run_chat_app()
```

### Key Takeaways from Code:
1. **The Rolling Aspect:** Notice that when we compress, we pass the *Old Summary* along with the *Oldest Messages*. This ensures that the new summary contains the entire cumulative knowledge of the 2-hour conversation!
2. **The Prompt Injection:** We injected the summary directly into a `system` message. This anchors the <abbr title="Large Language Model">LLM</abbr>, ensuring it remembers the context without having to read the raw text of 100 previous messages.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Pinned Entity Memory
Summaries are great, but sometimes the <abbr title="Large Language Model">LLM</abbr> summarizes too aggressively and deletes the user's name!
**Your Task:**
1. Conceptually design an **Entity Extraction** pipeline.
2. Every 10 turns, pass the history to an <abbr title="Large Language Model">LLM</abbr> and prompt it: *"Extract any permanent facts about the user into a JSON object. E.g., Name, Age, Profession, Dietary Restrictions."*
3. Pin this JSON object to the top of the System Prompt permanently. This ensures the <abbr title="Large Language Model">LLM</abbr> never forgets critical user preferences, even if the raw chat history is summarized away!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your enterprise chatbot frequently handles 1000+ turn conversations. The users are complaining that it 'forgets' details from hour 1. However, if you pass all 1000 turns to the <abbr title="Large Language Model">LLM</abbr>, the <abbr title="Application Programming Interface">API</abbr> costs are bankrupting the company. Design an architecture to solve this."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Cost Dilemma:** 
   - Acknowledge that $O(N^2)$ token scaling is mathematically unsustainable for long conversations.
2. **The Hybrid Memory Architecture:**
   - Propose a 3-tier memory system.
   - **Tier 1 (Short-Term):** Keep the last 10 messages raw in the array for immediate conversational flow.
   - **Tier 2 (Entity Memory):** Run an asynchronous background task to extract hard facts (Name, Account ID) into a JSON block pinned to the System Prompt.
   - **Tier 3 (Long-Term <abbr title="Retrieval-Augmented Generation">RAG</abbr>):** Embed all older messages into a Vector Database. Use the user's current message to retrieve the Top 3 relevant past messages and inject them as "Context".
3. **Prompt Caching:**
   - Mention modern <abbr title="Application Programming Interface">API</abbr> features (like Anthropic's Prompt Caching). If the system prompt and long-term memory remain static, the <abbr title="Application Programming Interface">API</abbr> can cache the KV-tensors on the GPU, dropping the cost of a 10,000-token prompt by $90\%$!

---
**Task for the end of the day:** Commit your code to Git. 

We have mastered Tools and Context. But all our LLMs so far have been "Reactive". They just answer the user.
What if we want the <abbr title="Large Language Model">LLM</abbr> to think, plan, and execute a 10-step strategy completely on its own?

Tomorrow, in **Day 115**, we enter the world of **<abbr title="Large Language Model">LLM</abbr> Cognition**: Chain-of-Thought, Tree-of-Thought, and the ReAct architecture!
