# Day 48: Word Embeddings (Word2Vec & Skip-gram)

Welcome to Day 48. Until today, we have fed words into our Neural Networks by assigning them random ID numbers (e.g., `Dog = 45`, `Cat = 12`, `Apple = 99`). 
This is fundamentally flawed. In math, 45 is closer to 12 than it is to 99. But the AI doesn't know that. It treats them as completely arbitrary numbers.

Today, we teach the AI the absolute geometric meaning of human language. We are going to map every word in the dictionary into a 300-dimensional coordinate space.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Distributional Hypothesis
In 1957, linguist John Rupert Firth stated: *"You shall know a word by the company it keeps."*
If I tell you the sentence: *"I poured the blicket into a glass and drank it,"* you instantly know that a "blicket" is a liquid. You don't need a dictionary. You inferred its meaning entirely from the surrounding context words (*poured*, *glass*, *drank*). 
**Word2Vec** uses this exact logic to mathematically learn the meaning of words.

### 2. The Skip-gram Architecture
Word2Vec is actually a tiny Neural Network with a very specific, fake task.
**The Task:** You give the AI a Center Word (e.g., *"Apple"*). It must predict the Context Words surrounding it (e.g., *"Eating"*, *"Juice"*).
**The Architecture:** 
1. Input: The word *"Apple"* (represented as a One-Hot Vector, e.g., `[0, 0, 1, 0...]`).
2. Hidden Layer: A linear layer with no activation function. This is the **Embedding Matrix**. (e.g., 300 neurons).
3. Output Layer: A Softmax predicting the surrounding words.

Once the network is trained, we literally **throw away the Output Layer**. The only thing we care about is the Hidden Layer (The Embedding Matrix)! This matrix now contains the perfect geometric coordinates for every word.

### 3. Negative Sampling (The Math Trick)
If your dictionary has 100,000 words, running a Softmax over 100,000 words at every single step of training is computationally impossible. 
**Negative Sampling** is a genius trick. Instead of predicting the 1 correct context word out of 100,000, we change the game.
1. We give the AI the true pair: `("Apple", "Juice")` $\rightarrow$ Target: $1.0$
2. We give the AI 5 completely random "Negative" pairs: `("Apple", "Car")` $\rightarrow$ Target: $0.0$.
We turned a massive 100,000-class Softmax problem into a tiny, blazing-fast Binary Classification problem (Sigmoid). This speeds up training by 1000x!

### 4. Vector Arithmetic (The Magic)
Because words are now geometric coordinates, you can do math on them!
If you take the coordinate vector for $King$, subtract $Man$, and add $Woman$, the resulting coordinate will land exactly on top of the vector for $Queen$!
`King - Man + Woman = Queen`. 
The AI learned the mathematical vector for "Gender" purely by reading text!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build the Skip-gram architecture with Negative Sampling from scratch in PyTorch. We will use `nn.Embedding` layers, which are essentially lookup tables that store the coordinates for our words!

Create a file named `word2vec_skipgram.py`:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class SkipGramNegativeSampling(nn.Module):
    """
    A Word2Vec implementation using Negative Sampling.
    Instead of a massive Softmax, it uses Dot Products and Sigmoid!
    """
    def __init__(self, vocab_size, embedding_dim):
        super().__init__()
        
        # 1. The Target Embeddings (The coordinates for the Center words)
        self.target_embeddings = nn.Embedding(vocab_size, embedding_dim)
        
        # 2. The Context Embeddings (The coordinates for the Surrounding words)
        self.context_embeddings = nn.Embedding(vocab_size, embedding_dim)
        
        # Initialize the coordinates with small random numbers
        initrange = 0.5 / embedding_dim
        self.target_embeddings.weight.data.uniform_(-initrange, initrange)
        self.context_embeddings.weight.data.uniform_(-initrange, initrange)

    def forward(self, target_word_ids, context_word_ids, negative_word_ids):
        """
        target_word_ids: [Batch] (e.g., ID for "Apple")
        context_word_ids: [Batch] (e.g., ID for the True context "Juice")
        negative_word_ids: [Batch, Num_Negatives] (e.g., IDs for 5 random fake words)
        """
        # Look up the 300-D coordinates for the Target word
        # Shape: [Batch, 1, Embed_Dim]
        target_embeds = self.target_embeddings(target_word_ids).unsqueeze(1)
        
        # Look up coordinates for the True Context word
        # Shape: [Batch, Embed_Dim, 1] (Transposed for Dot Product!)
        context_embeds = self.context_embeddings(context_word_ids).unsqueeze(2)
        
        # Look up coordinates for the Fake Negative words
        # Shape: [Batch, Embed_Dim, Num_Negatives]
        negative_embeds = self.context_embeddings(negative_word_ids).transpose(1, 2)
        
        # --- THE MATH (Dot Products) ---
        
        # 1. True Pair Score: Target * Context
        # We want this dot product to be a LARGE POSITIVE number (meaning vectors point the same way)
        # Shape: [Batch, 1, 1] -> [Batch]
        true_score = torch.bmm(target_embeds, context_embeds).squeeze()
        
        # 2. Fake Pair Scores: Target * Negatives
        # We want these dot products to be LARGE NEGATIVE numbers (meaning vectors point opposite ways)
        # Shape: [Batch, 1, Num_Negatives] -> [Batch, Num_Negatives]
        fake_scores = torch.bmm(target_embeds, negative_embeds).squeeze(1)
        
        # --- THE LOSS FUNCTION ---
        # Log-Sigmoid of True Score + Log-Sigmoid of (-Fake Scores)
        true_loss = F.logsigmoid(true_score)
        fake_loss = F.logsigmoid(-fake_scores).sum(dim=1)
        
        # We want to MINIMIZE the negative sum of these
        total_loss = -(true_loss + fake_loss).mean()
        
        return total_loss

def test_word2vec():
    print("--- RUNNING WORD2VEC NEGATIVE SAMPLING ---")
    
    # 1. Setup
    VOCAB_SIZE = 10000
    EMBEDDING_DIM = 300
    BATCH_SIZE = 64
    NUM_NEGATIVES = 5
    
    model = SkipGramNegativeSampling(VOCAB_SIZE, EMBEDDING_DIM)
    
    # 2. Simulate a batch of data
    # 64 Center words
    target = torch.randint(0, VOCAB_SIZE, (BATCH_SIZE,))
    # 64 True context words
    context = torch.randint(0, VOCAB_SIZE, (BATCH_SIZE,))
    # 5 Fake random words for every single center word!
    negatives = torch.randint(0, VOCAB_SIZE, (BATCH_SIZE, NUM_NEGATIVES))
    
    # 3. Forward Pass (Calculates the Loss!)
    loss = model(target, context, negatives)
    
    print(f"Batch Loss: {loss.item():.4f}")
    print("The model used Dot Products to pull True words closer together, and push Fake words apart!")
    
    # How to extract the final coordinates after training:
    final_brain = model.target_embeddings.weight.data
    print(f"Final Brain Shape: {final_brain.shape}")

if __name__ == "__main__":
    test_word2vec()
```

### Key Takeaways from Code:
1. **The Dot Product:** `torch.bmm(target_embeds, context_embeds)`. If two vectors point in the exact same geometric direction, their Dot Product is a massive positive number. If they point in opposite directions, it's a massive negative number. Word2Vec literally pulls and pushes vectors around in space until they settle into the perfect semantic clusters!
2. **`logsigmoid(-fake_scores)`:** Notice the minus sign. We pass the *negative* fake scores into the Sigmoid. This mathematically forces the network to push the negative vectors away from the target vector.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Cosine Similarity
To find synonyms, you don't use Euclidean Distance (ruler distance). You use **Cosine Similarity** (the angle between the vectors).
**Your Task:**
1. Given two vectors $A$ and $B$, write a function to calculate Cosine Similarity.
2. The formula is: `Dot Product of A and B / (Magnitude of A * Magnitude of B)`.
3. In PyTorch: `dot = (A * B).sum()`, `norm_A = A.norm()`, `norm_B = B.norm()`.
4. The result will be between `-1.0` (opposites) and `1.0` (exact synonyms). Write this function from scratch!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Word embeddings like Word2Vec and GloVe revolutionized NLP, but they have one massive, fatal flaw when dealing with polysemous words (words with multiple meanings, like 'bank' or 'apple'). Explain this mathematical flaw, and explain how modern contextual models like ELMo and BERT solved it."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Static Dictionary Flaw:** 
   - State that Word2Vec is a **Static** embedding. Every word in the dictionary gets exactly *one* coordinate vector assigned to it.
   - Explain that the word "bank" has two meanings (a financial institution vs a river bank). Because Word2Vec averages the contexts during training, the single vector for "bank" ends up floating somewhere awkwardly in the middle of "money" and "water", accurately representing neither!
2. **The Contextual Solution:**
   - Conclude that models like ELMo (BiLSTMs) and BERT (Transformers) use **Contextual** embeddings. 
   - Instead of looking up a static vector in a dictionary, they calculate the vector *on the fly* at runtime by reading the entire sentence. Thus, the mathematical vector for "bank" in "river bank" will be physically different from the vector for "bank" in "bank account".

---
**Task for the end of the day:** Commit your code to Git. You have successfully mapped human language into mathematical geometry.

Tomorrow, in **Day 49**, we tackle the nightmare of Tokenization. How does the AI handle words it has never seen before? Welcome to **Byte Pair Encoding (BPE)!**
