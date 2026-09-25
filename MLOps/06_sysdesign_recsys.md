# System Design: Recommendation Systems

A recommendation system (RecSys) suggests items to users (e.g., Netflix movies, Amazon products, TikTok videos).

## 1. The Funnel Architecture

You cannot run a heavy deep neural network to score all 100 million videos on TikTok for every user in real-time. The system must act as a funnel.

```arch
%% caption: Recommendation systems use a funnel: Candidate Generation narrows millions of items down to hundreds, which Ranking then scores with heavy models.
route straight
node user "User Request" at 0,1 icon=client color=blue
group funnel "RecSys Funnel" color=slate style=dashed
node cg "1. Candidate Gen\n(100M -> 500)" at 2,0 in funnel icon=filter color=amber
node rank "2. Deep Ranking\n(500 -> 50)" at 2,1 in funnel icon=cpu color=green
node post "3. Post-Processing\n(Diversity/Ads)" at 2,2 in funnel icon=check color=slate

user -> cg
cg -> rank
rank -> post
```

### Phase 1: Candidate Generation (Retrieval)
- **Goal**: Quickly narrow down 100 million items to a few hundred relevant ones. Latency must be <20ms.
- **Methods**:
  - **Collaborative Filtering (Matrix Factorization)**: Find users similar to you, recommend what they liked.
  - **Two-Tower Models (Embeddings)**: Precompute user embeddings and item embeddings. Load item embeddings into a Vector Database (like Milvus or Pinecone). At runtime, fetch the user's embedding and do an Approximate Nearest Neighbor (ANN) search to find the closest items.
  - **Heuristics**: "Top trending items in your city."

### Phase 2: Ranking
- **Goal**: Take the 500 candidates and rank them precisely for this specific user. Latency must be <50ms.
- **Methods**: Heavy ML models (e.g., Deep Learning, XGBoost) that take hundreds of features: `user_age`, `item_historical_ctr`, `time_of_day`, `user_historical_interactions_with_this_category`.
- The model outputs a probability (e.g., probability of clicking, or predicted watch time). Sort the 500 items by this score.

### Phase 3: Post-Processing (Re-ranking)
- **Goal**: Apply business rules.
- **Methods**: 
  - Remove items the user already watched.
  - Ensure diversity (don't show 10 Batman movies in a row).
  - Inject sponsored ads into slots 3 and 7.

## 2. Cold Start Problem

How do you recommend items to a brand new user (User Cold Start)? How do you recommend a movie uploaded 5 seconds ago (Item Cold Start)?

- **User Cold Start**: Use popular items, ask them for their interests during onboarding, or use contextual features (location, time of day, device type).
- **Item Cold Start**: Content-based filtering. If it's an action movie, show it to users who like action movies, regardless of its interaction history. Use Multi-Armed Bandits to force a small percentage of users to see new items so the system can gather data on them.
