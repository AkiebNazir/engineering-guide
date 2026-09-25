# System Design: Search and Ranking

Search is a specialized form of recommendation where the user provides an explicit intent (the search query).

## 1. The Architecture

Search also follows a funnel, but the Retrieval phase is different.

```arch
%% caption: Search systems use an Inverted Index for exact keyword matches and a Vector Database for semantic search, combining them in the Ranking phase.
route straight
node query "Query: 'running shoes'" at 2,0 icon=search color=blue
group ret "Retrieval Phase" color=slate style=dashed
node text "Lexical Search\\n(Elasticsearch)" at 0,1 in ret icon=db color=amber
node vec "Semantic Search\\n(Vector DB)" at 4,1 in ret icon=db color=amber
node rank "Learning to Rank\\n(XGBoost / Deep Learning)" at 2,2 icon=cpu color=green

query -> text
query -> vec
text -> rank : "BM25 score"
vec -> rank : "Cosine similarity"
```

### Phase 1: Retrieval

1. **Lexical (Keyword) Search**: Uses an Inverted Index (like Elasticsearch or Solr). Good for exact matches ("Nike Air Max 90"). Uses TF-IDF or BM25 to score relevance.
2. **Semantic (Vector) Search**: Uses a neural network to embed the query into a vector. Finds items with similar meaning, even if they share no words. (Query: "footwear for jogging" -> matches "running shoes").

A modern system does both simultaneously (Hybrid Search) and merges the results into a candidate pool of ~1,000 items.

### Phase 2: Learning to Rank (LTR)

Take the 1,000 candidates and rank them using an ML model.
Features include:
- **Query-Item features**: BM25 score, Cosine similarity, whether the query matches the item title exactly.
- **Item features**: Price, average rating, number of reviews, historical CTR.
- **User features**: User's past purchase history, preferred brands.

## 2. Query Understanding

Before hitting the databases, the raw query text must be processed:
- **Spell Correction**: "runing shoes" -> "running shoes".
- **Query Expansion / Synonyms**: Add "sneakers" to the query.
- **Intent Extraction (NER)**: "cheap red nike running shoes size 10" -> `price: cheap`, `color: red`, `brand: nike`, `category: running shoes`, `size: 10`. This allows the system to apply hard filters to the database query, drastically improving precision.
