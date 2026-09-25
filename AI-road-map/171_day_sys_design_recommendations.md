# Day 171: System Design: Real-Time Recommendation Engines

Welcome to Day 171.

We are beginning the **MAANG System Design** phase. For the next 10 days, we are taking everything you learned over the last 170 days and applying it to high-level architectural whiteboarding.

If you interview for a Senior/Lead <abbr title="Machine Learning">ML</abbr> role at Netflix, TikTok, or YouTube, you will be asked to design a **Recommendation Engine**.
You have 45 minutes to design a system that takes 1 Billion videos, scores them against 100 Million users, and returns the top 10 videos in under 200 milliseconds.

Today, we learn the **Two-Tower Architecture** and the **Candidate Generation $\rightarrow$ Ranking** cascade.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The 200ms Math Problem
Imagine YouTube has 1 Billion videos. If a user opens the app, you cannot pass all 1 Billion videos through a massive <abbr title="Large Language Model">LLM</abbr> or Deep Neural Network to score them. It would take 3 years to render the homepage.
Because of the strict 200ms latency budget, Recommendation Engines are built as a **Funnel**.

### 2. The Funnel Architecture
1. **Candidate Generation (L0):** Takes 1 Billion items and whittles them down to 1,000 items in 50ms. (Fast, but inaccurate).
2. **Ranking (L1):** Takes those 1,000 items, passes them through a massive Deep Neural Network, and scores them 1-100 in 100ms. (Slow, but highly accurate).
3. **Re-ranking / Filtering (L2):** Takes the top 50 ranked items, removes videos the user has already watched, ensures diversity (not just showing 50 chess videos), and returns the final 10 to the UI in 50ms.

### 3. Candidate Generation (The Two-Tower Model)
How do you find 1,000 relevant videos out of 1 Billion in 50ms? You use **Embeddings**.
- **The User Tower:** A neural network that looks at the user's history ("Watched 5 chess videos") and generates a 256-dimensional User Embedding.
- **The Item Tower:** A neural network that looks at a video's metadata ("Title: Chess Strategy") and generates a 256-dimensional Item Embedding.

Because we pre-compute all 1 Billion Item Embeddings and store them in a Vector Database (like Pinecone/FAISS), when the user logs in, we simply run an Approximate Nearest Neighbor (ANN) search to find the 1,000 vectors closest to the User's vector!

### 4. Ranking (DLRM)
Now we have 1,000 candidates. We pass them into a **Deep Learning Recommendation Model (DLRM)**.
This model looks at complex, real-time cross-features: *"Does THIS user, on a TUESDAY, clicking from a MOBILE phone, want to watch THIS 30-minute video?"*
It outputs a probability of engagement (e.g., $P(click) = 0.85$). We sort the 1,000 items by this probability.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual implementation of the Funnel Architecture in Python. We will simulate having a massive Vector Database for Candidate Generation, and a heavy Model for Ranking.

```python
import time
import numpy as np
from typing import List, Dict

# --- MOCK INFRASTRUCTURE ---

class MockVectorDB:
    def __init__(self, num_items=1_000_000):
        # Simulating 1 Million videos pre-embedded in the database
        self.item_embeddings = np.random.rand(num_items, 64)
        
    def ann_search(self, user_embedding: np.ndarray, top_k: int = 1000) -> List[int]:
        """Candidate Generation (L0): Fast vector search."""
        # Mocking an incredibly fast FAISS/Pinecone search
        time.sleep(0.05) # 50ms
        # Returns a list of 1000 video IDs
        return list(np.random.randint(0, 1_000_000, top_k))

class MockRankingModel:
    def predict_engagement(self, user_features: dict, item_ids: List[int]) -> Dict[int, float]:
        """Ranking (L1): Slow, heavy neural network."""
        time.sleep(0.10) # 100ms to score 1000 items
        # Returns {video_id: predicted_click_probability}
        return {vid: np.random.random() for vid in item_ids}

# --- THE RECOMMENDATION SYSTEM ---

class RecommendationEngine:
    def __init__(self):
        self.vector_db = MockVectorDB()
        self.ranker = MockRankingModel()
        
    def generate_user_embedding(self, user_id: int) -> np.ndarray:
        # In reality, this queries the Feature Store (Day 166) for the user's history
        return np.random.rand(64)
        
    def get_homepage(self, user_id: int, user_context: dict) -> List[int]:
        start_time = time.time()
        
        # 1. User Context & Embedding
        user_vector = self.generate_user_embedding(user_id)
        
        # 2. L0: Candidate Generation (1,000 items)
        print("   [L0] Searching 1 Million items for top 1000 candidates...")
        candidates = self.vector_db.ann_search(user_vector, top_k=1000)
        
        # 3. L1: Ranking (Heavy Scoring)
        print("   [L1] Scoring 1000 candidates using Heavy Deep Learning Model...")
        scored_candidates = self.ranker.predict_engagement(user_context, candidates)
        
        # Sort by highest probability
        sorted_candidates = sorted(scored_candidates.items(), key=lambda x: x[1], reverse=True)
        
        # 4. L2: Business Logic / Filtering
        print("   [L2] Applying business rules (Diversity, Ads, Seen-history)...")
        # Grab the top 10 to show the user
        final_homepage = [vid for vid, score in sorted_candidates[:10]]
        
        latency = (time.time() - start_time) * 1000
        print(f"\n✅ Homepage generated in {latency:.0f}ms!")
        return final_homepage

# --- EXECUTION ---
def run_system():
    print("--- TIKTOK / YOUTUBE RECOMMENDATION REQUEST ---")
    engine = RecommendationEngine()
    
    user_context = {"device": "mobile", "time": "evening"}
    homepage = engine.get_homepage(user_id=8472, user_context=user_context)
    
    print(f"Top 10 Video IDs to render: {homepage}")

# To run:
# run_system()
```

### 🔍 Understanding the Enterprise Value
Notice how the math perfectly fits the latency budget! 50ms for Candidate Generation + 100ms for Ranking + 10ms for Sorting. We searched 1 Million items and returned a perfectly personalized homepage in 160ms. This Funnel Architecture is the absolute industry standard.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
The system above suffers from the "Echo Chamber" problem (it only shows the user exactly what they've seen before). 
**Your Task:** Modify the `get_homepage` L2 filtering step. Inject an "Exploration Factor". Out of the 10 final videos, ensure 2 of them are completely random (or from a "Trending" list) to help the user discover new content!

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Design the recommendation engine for TikTok's 'For You' page. Assume 1 Billion MAU, 100 Million daily active videos. Focus specifically on the real-time serving infrastructure and the Cold Start problem for new videos."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The Funnel Architecture:** Clearly draw the L0 (Candidate Generation) $\rightarrow$ L1 (Ranking) cascade on the whiteboard. Mention the 200ms latency budget constraint.
2. **Feature Store Integration:** Explain how the Ranking model cannot query an <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> database. It must query a Redis Feature Store (Day 166) to get the user's real-time engagement history (e.g., "They just liked 3 dog videos 5 seconds ago").
3. **The Cold Start Problem:** If a new video is uploaded 1 second ago, it has zero views. It will never be ranked high! Propose a multi-armed bandit approach: force 5% of all user traffic to see brand-new videos, collect their engagement metrics, and use those metrics to jumpstart the video's ranking score.
4. **Data Pipelining:** How do we train the models? Explain that the frontend logs stream into Kafka, which dumps into a Data Lake (Snowflake), which trains the Two-Tower model nightly via Airflow.

---
**Task for the end of the day:** Watch a system design video on "Designing YouTube".

Tomorrow, in **Day 172**, we pivot from Recommendations to **Search Engines**. How do you design a search engine that actually *understands* what the user meant, rather than just matching exact keywords?
