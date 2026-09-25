# Day 86: Embedding Models (Contrastive Learning)

Welcome to Day 86. Up until now, we have assumed that our Embedding Model (like `sentence-transformers/all-MiniLM-L6-v2`) works perfectly. 

But pre-trained models are trained on Wikipedia and Reddit. If your company builds quantum computers, the embedding model has no idea what your technical jargon means. It will map your quantum physics documents to random places in the vector space, and your entire <abbr title="Retrieval-Augmented Generation">RAG</abbr> pipeline will collapse.

Today, we learn how to train our own mathematical Embedding Models from scratch using **Contrastive Learning**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Contrastive Learning
How do you teach a model what words mean? You don't use classification. You use **Distance**.
You want similar concepts to be mathematically close together, and dissimilar concepts to be far apart.
To train the model, we build a dataset of **Triplets**: `(Anchor, Positive, Negative)`.
- **Anchor:** The user's search query (e.g., *"How to fix a flat tire"*).
- **Positive:** A document that perfectly answers the query.
- **Negative:** A document that has nothing to do with the query.

### 2. The InfoNCE Loss (Triplet Loss)
During training, we pass all three texts through a BERT encoder to get three vectors: $V_a, V_p, V_n$.
The Loss function calculates the distance between the Anchor and the Positive ($D_{ap}$), and the distance between the Anchor and the Negative ($D_{an}$).
The Loss is minimized when $D_{ap}$ is $0.0$ and $D_{an}$ is as large as possible. 
**The Physics Analogy:** The math acts like a physical spring. It violently pulls the Anchor and Positive vectors together, and violently repels the Negative vector away!

### 3. The Secret: Hard Negatives
If your Negative is *"How to bake a cake"*, the model learns almost nothing because baking is obviously not related to tires. 
To build a world-class model, you must use **Hard Negatives**. 
- **Anchor:** *"How to fix a flat tire"*
- **Hard Negative:** *"How to fix a flat screen TV"*
The model sees the words *"How to fix a flat"*, assumes they are similar, and gets penalized heavily by the Loss function! This forces the model to look deeper than just keyword matching and truly understand the semantic difference between rubber tires and glass TVs.

### 4. Matryoshka Representation Learning (MRL)
Storing 100 Million 1024-dimensional vectors requires terabytes of expensive RAM. What if you could slice the vector in half to save space? Normally, slicing a vector destroys the math.
**Matryoshka Learning** (like Russian nesting dolls) is a brilliant trick. During training, we calculate the Contrastive Loss on the full 1024 dimensions. But we ALSO calculate the loss on the first 512 dimensions, the first 256, and the first 64!
This mathematically forces the model to pack the most important semantic information into the *very first 64 numbers*! The remaining numbers just add fine details. 
In production, you can literally slice `vector[:256]`, shrinking your database costs by 4x without retraining the model!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a Contrastive Learning training loop in pure PyTorch. We will use the `TripletMarginLoss` to mathematically pull Positives together and push Negatives apart!

Create a file named `embedding_training.py`:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class MockEncoder(nn.Module):
    """
    A mock embedding model (e.g., a mini-BERT).
    Takes a string (mocked as an ID here) and outputs a 128D vector.
    """
    def __init__(self, vocab_size=1000, embed_dim=128):
        super().__init__()
        # We use an Embedding layer to simulate the BERT output
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        
    def forward(self, x):
        # We must L2 normalize embeddings for Cosine Similarity to work!
        embeds = self.embedding(x)
        return F.normalize(embeds, p=2, dim=1)

def test_contrastive_learning():
    print("--- RUNNING CONTRASTIVE LEARNING (TRIPLET LOSS) ---")
    
    # Initialize the Model and the Triplet Loss function
    model = MockEncoder()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    
    # Margin=1.0 means we want the Negative to be at least 1.0 distance unit 
    # further away from the Anchor than the Positive is!
    triplet_loss_fn = nn.TripletMarginLoss(margin=1.0, p=2)
    
    # Simulate a Batch of 2 Triplets: [Anchor, Positive, Hard Negative]
    # In reality, these would be tokenized sentences. Here we mock them as token IDs.
    anchors = torch.tensor([10, 20])   # e.g., "Flat tire", "Python code"
    positives = torch.tensor([11, 21]) # e.g., "Bike repair", "Def function"
    negatives = torch.tensor([12, 22]) # e.g., "Flat TV", "Monty Python snake"
    
    print("Before Training (Random Initialization):")
    # Get vectors
    v_a = model(anchors)
    v_p = model(positives)
    v_n = model(negatives)
    
    # Calculate Distances (Lower is closer)
    dist_ap_start = F.pairwise_distance(v_a, v_p)
    dist_an_start = F.pairwise_distance(v_a, v_n)
    
    print(f"Distance Anchor <-> Positive: {dist_ap_start.detach().numpy()}")
    print(f"Distance Anchor <-> Negative: {dist_an_start.detach().numpy()}")
    
    # TRAINING LOOP (50 Epochs)
    print("\nTraining for 50 Epochs (Pulling Positives, Pushing Negatives)...")
    for epoch in range(50):
        optimizer.zero_grad()
        
        # Forward Pass
        v_a = model(anchors)
        v_p = model(positives)
        v_n = model(negatives)
        
        # Calculate Loss
        loss = triplet_loss_fn(v_a, v_p, v_n)
        
        # Backpropagate and Update Weights!
        loss.backward()
        optimizer.step()
        
    # After Training!
    print("\nAfter Training:")
    v_a = model(anchors)
    v_p = model(positives)
    v_n = model(negatives)
    
    dist_ap_end = F.pairwise_distance(v_a, v_p)
    dist_an_end = F.pairwise_distance(v_a, v_n)
    
    print(f"Distance Anchor <-> Positive: {dist_ap_end.detach().numpy()} (They moved closer!)")
    print(f"Distance Anchor <-> Negative: {dist_an_end.detach().numpy()} (They were pushed away!)")

if __name__ == "__main__":
    test_contrastive_learning()
```

### Key Takeaways from Code:
1. **L2 Normalization:** Embedding models must output normalized vectors (length = 1.0) so that Dot Product accurately represents Cosine Similarity during the FAISS search.
2. **The Margin:** The `margin` parameter is critical. If the Negative is already far enough away, the loss becomes $0.0$ and the gradients stop updating. This prevents the model from wasting compute pushing a Negative that is already lightyears away.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: In-Batch Negatives
Creating massive datasets of Hard Negatives is expensive.
**Your Task:**
1. Conceptually design an **In-Batch Negatives** loss function.
2. If your batch size is 32, you have 32 Anchors and 32 Positives.
3. For Anchor #1, Positive #1 is its target. But Positives #2 through #32 are *guaranteed* to be unrelated to Anchor #1!
4. You can use Positives #2 through #32 as "free" Negative examples!
5. This transforms the math from 1 comparison per Anchor to 31 comparisons per Anchor, making training 31x more efficient without any extra data!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your production <abbr title="Retrieval-Augmented Generation">RAG</abbr> system's retrieval accuracy dropped 15% after your company pivoted from analyzing Wikipedia articles to analyzing proprietary chemical engineering patents. Diagnose the issue and propose a concrete data pipeline to train a custom embedding model."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Diagnosis (Domain Shift):** 
   - State that the pre-trained embedding model suffers from Out-Of-Vocabulary (OOV) and Domain Shift issues. The complex chemical jargon was never seen during the model's pre-training, so it arbitrarily clusters the technical words.
2. **The Data Pipeline (Synthetic Generation):**
   - Propose using a massive Teacher <abbr title="Large Language Model">LLM</abbr> (like GPT-4) to synthetically generate training data.
   - Feed a chemical patent paragraph to GPT-4. Prompt it: *"Generate 3 questions that this paragraph perfectly answers."* 
   - You now have thousands of (Anchor Question, Positive Paragraph) pairs generated for pennies!
3. **Training & Evaluation (MTEB):**
   - Explain that you will use Sentence-Transformers to fine-tune `BGE-base` using MultipleNegativesRankingLoss (In-Batch Negatives).
   - Crucially, state that you must evaluate the new model against the **MTEB** (Massive Text Embedding Benchmark) to ensure that while it learned Chemistry, it didn't catastrophically forget basic English semantics!

---
**Task for the end of the day:** Commit your code to Git. 

Congratulations. You have completed the next 10 days! You have mastered Enterprise <abbr title="Artificial Intelligence">AI</abbr>, Model Compression, and the most advanced <abbr title="Retrieval-Augmented Generation">RAG</abbr> architectures on the planet.

In the next block (Days 87-96), we will cover **Vector Databases, Prompt Engineering, Agentic Tool Use (Function Calling), and Reinforcement Learning from Human Feedback (<abbr title="Reinforcement Learning from Human Feedback">RLHF</abbr>)!**
