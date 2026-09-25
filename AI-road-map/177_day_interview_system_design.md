# Day 177: MAANG Mock Interview: ML System Design Deep Dive

Welcome to Day 177.

You have learned the theory. Now you must perform.
At companies like Meta, Google, and Amazon, the <abbr title="Machine Learning">ML</abbr> System Design interview is the ultimate gatekeeper for Senior and Staff positions. You are given a dry-erase marker, a whiteboard, and a wildly ambiguous prompt: *"Design a content moderation system for Instagram."*

You have 45 minutes. If you immediately start talking about Neural Network architectures, you fail.
Today, we learn the **6-Step Interview Framework** that guarantees a structured, Senior-level performance.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### The 45-Minute Framework
The interviewer is not looking for the "right" answer. They are looking to see if you can break down ambiguity and communicate technical trade-offs. You must rigidly follow this timeline:

### 1. Clarify Requirements (Minutes 0 - 5)
Never start designing. Assume the prompt is a trap. Ask constraints:
- *Scale:* How many users? How many posts per day? (This dictates the infrastructure).
- *Latency:* Does this need to run in 50ms, or can it be a nightly batch job?
- *Modality:* Is the content just text, or images and video too?

### 2. Define Metrics (Minutes 5 - 10)
How do we know if the system is good?
- *Offline Metrics:* Precision, Recall, F1-Score, AUC. (For moderation, optimizing for Recall is critical—we cannot let illegal content slip through).
- *Online Metrics:* User reports, appeals rate, latency (P99).
- *Business Metrics:* Daily Active Users (DAU), ad revenue.

### 3. High-Level Architecture (Minutes 10 - 20)
Draw the boxes. Do not write code.
- Draw the User $\rightarrow$ <abbr title="Application Programming Interface">API</abbr> Gateway $\rightarrow$ Message Queue (Kafka) $\rightarrow$ <abbr title="Machine Learning">ML</abbr> Workers $\rightarrow$ Databases (Redis / Cassandra).
- Explain the flow of data out loud as you draw.

### 4. Deep Dive on <abbr title="Machine Learning">ML</abbr> Components (Minutes 20 - 35)
Now you zoom in on the specific <abbr title="Artificial Intelligence">AI</abbr> models.
- *Data Collection:* How do we get labels? (Human moderators, active learning).
- *Feature Engineering:* What features matter? (User history, image embeddings, text sentiment).
- *Model Selection:* Why use a Two-Tower model here instead of an <abbr title="Large Language Model">LLM</abbr>? (Explain the latency/cost trade-offs).

### 5. Scale & Operational Concerns (Minutes 35 - 40)
How does it survive the real world?
- Discuss Auto-scaling (KEDA), Model Deployment (Shadow mode, Canary), and monitoring for Data Drift (PSI).

### 6. Extensions & Trade-offs (Minutes 40 - 45)
Acknowledge the flaws in your own design before the interviewer does.
- "A major trade-off here is that my Graph Database will struggle to scale past 1 Billion nodes. If we reach that size, we'll need to partition the graph."

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's simulate the output of Step 3 (High-Level Architecture) and Step 4 (Deep Dive) using Python pseudo-code. This represents exactly what you would draw and explain on the whiteboard.

**Prompt:** *"Design a Content Moderation System for a massive social network."*

```python
# --- WHAT YOU DRAW ON THE WHITEBOARD (Conceptualized as Code) ---

class ContentModerationSystem:
    def __init__(self):
        # 1. We use a multi-model cascade (to save money/time)
        self.fast_heuristics = RuleEngine()         # Latency: 1ms
        self.lightweight_ml = FastTextClassifier()  # Latency: 10ms
        self.heavy_llm = MultimodalLLM()            # Latency: 1000ms
        
    def process_post_async(self, post_data: dict):
        """
        Explain to interviewer: "We process asynchronously via Kafka 
        so we don't block the user from uploading their post."
        """
        # Step 1: Heuristics (Regex for banned words/hashes)
        if self.fast_heuristics.is_banned(post_data):
            return "REJECTED_L0"
            
        # Step 2: Lightweight ML (e.g., FastText or DistilBERT)
        # Filters out 95% of obvious safe/unsafe content cheaply.
        ml_score = self.lightweight_ml.predict(post_data['text'])
        
        if ml_score > 0.99:
            return "REJECTED_L1"
        elif ml_score < 0.20:
            return "APPROVED"
            
        # Step 3: The Gray Area (Scores between 0.20 and 0.99)
        # Only send the tricky 5% of posts to the expensive LLM.
        llm_decision = self.heavy_llm.analyze_nuance(post_data)
        
        if llm_decision.confidence < 0.70:
            # Step 4: Human in the Loop (HITL)
            print("Routing to human moderation queue...")
            return "PENDING_HUMAN_REVIEW"
            
        return llm_decision.status

# --- DEEP DIVE EXPLANATION (What you say out loud) ---
def explain_tradeoffs_to_interviewer():
    print("""
    INTERVIEWER: Why did you use a cascade instead of just passing 
    everything to GPT-4V?
    
    YOU: Two reasons: Cost and Latency.
    If we process 100 Million posts a day, and GPT-4V costs $0.01 per image, 
    that is $1,000,000 a day. 
    By using the Rule Engine and Lightweight ML models to filter 95% of the 
    easy cases, we reduce the LLM cost to $50,000 a day. 
    Furthermore, if the LLM goes down, our L0 and L1 models keep the 
    platform relatively safe, providing graceful degradation.
    """)
```

### 🔍 Understanding the Enterprise Value
The pseudo-code above proves you are a Senior Engineer. A Junior Engineer will jump straight to "Let's use a massive multimodal <abbr title="Large Language Model">LLM</abbr>." A Senior Engineer thinks about the **cost, latency, and fallback mechanisms** first.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
Cold Practice. Set a timer for 45 minutes. Find a whiteboard or a blank piece of paper.
**Prompt:** *"Design a real-time language translation system for video calls (like Skype/Zoom)."*
Force yourself to spend exactly 5 minutes on Requirements, 5 on Metrics, 10 on Architecture, 15 on <abbr title="Machine Learning">ML</abbr> Deep Dive, and 5 on Scale. If you get stuck, practice "thinking out loud" so the interviewer can guide you.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Design the personalized News Feed for LinkedIn. Users can post text, images, and articles. The feed must optimize for 'Meaningful Engagement'."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Clarify 'Meaningful':** Ask the interviewer what meaningful engagement means. (e.g., A long comment is worth more than a quick 'Like'. Clicking 'Share' is worth the most).
2. **Metrics:** Define a custom weighted metric: `Engagement_Score = (1*Likes) + (5*Comments) + (10*Shares)`.
3. **Architecture:** Draw the Two-Tower model (Candidate Generation) feeding into a DLRM (Ranking Model), just like Day 171.
4. **Feature Engineering (Deep Dive):** Explain the specific features: 
   - *User Features:* Industry, Seniority, Historical Click Rate.
   - *Author Features:* Affinity (Does the user often message this author?), Author's historical virality.
   - *Content Features:* Embeddings of the text, age of the post.
5. **Operational:** Explain how to handle the "Justin Bieber Problem" (when a massive influencer posts, it blows up the caching layer). Propose a Push/Pull hybrid caching architecture for celebrity feeds.

---
**Task for the end of the day:** Watch a mock <abbr title="Machine Learning">ML</abbr> System Design interview on YouTube (channels like *Exponent* or *Grokking*). Notice the pacing and how the candidate continuously checks in with the interviewer.

Tomorrow, in **Day 178**, we tackle the other half of the technical loop: **<abbr title="Machine Learning">ML</abbr> Coding & Theory**. Prepare to implement algorithms from scratch!
