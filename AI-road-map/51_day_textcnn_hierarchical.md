# Day 51: Text Classification (TextCNN & Hierarchical Attention)

Welcome to Day 51. Recurrent Neural Networks (RNNs) are fundamentally slow. Because they use a loop, they cannot read Word 2 until they finish processing Word 1. 
If you are building a system that needs to classify 1,000,000 Tweets per hour as "Toxic" or "Safe", an RNN will bottleneck your servers. 

Today, we abandon the loop. We adapt the Computer Vision CNN to read text!

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. TextCNN (Convolutions for Text)
In Computer Vision (Day 38), a CNN slides a $3 \times 3$ filter over a 2D image grid.
Text is not a 2D grid. Text is a 1D sequence of words. 
In **TextCNN**, we use a 1D Convolution (`nn.Conv1d`). We slide a window across the sentence. 
- If our filter size is $3$, the CNN looks at 3 words at a time. It mathematically acts as an automatic **Trigram Detector**. It slides across the sentence looking for specific 3-word phrases like *"not very good"* or *"absolutely loved it"*.
- **The Speed:** Because Convolutions don't have loops, the GPU processes all 1,000 words in the document *simultaneously*!

### 2. Max-Over-Time Pooling
After the CNN slides across the document, it produces a feature map showing *where* it found the phrase *"not very good"*.
But for Document Classification, we don't care *where* the phrase is. We only care *if* it exists!
We apply **Max Pooling**. It collapses the entire feature map into a single number. It asks: *"Did this phrase appear anywhere in the document? Yes or No?"* This makes the model completely invariant to document length!

### 3. Hierarchical Attention Networks (HAN)
If you need to classify a massive 50-page PDF, even a CNN struggles. 
In 2016, researchers invented the **HAN**, which reads a document exactly like a human does:
1. **Word-Level Attention:** It reads the words in a single sentence. It uses Attention to find the single most important word (e.g., *"Terrible"*), and compresses the sentence into a vector.
2. **Sentence-Level Attention:** It looks at all the compressed sentences in the document. It uses Attention again to find the single most important sentence (e.g., *"I will never buy this again."*), and compresses the entire document into a final vector for classification.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build Yoon Kim's legendary 2014 **TextCNN** entirely from scratch in PyTorch. We will use multiple different filter sizes to capture 2-word, 3-word, and 4-word phrases simultaneously!

Create a file named `text_cnn.py`:

```python
import torch
import torch.nn as nn
import torch.nn.functional as F

class TextCNN(nn.Module):
    """
    A Convolutional Neural Network for Text Classification.
    Blazingly fast, highly effective for short-to-medium text.
    """
    def __init__(self, vocab_size, embed_dim, num_classes):
        super().__init__()
        
        # 1. Word Embeddings (Turn word IDs into 300D coordinates)
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        
        # 2. The Convolutional Filters (The N-gram detectors!)
        # We create 3 separate CNN layers. 
        # kernel_size=2 looks for 2-word phrases (Bigrams)
        # kernel_size=3 looks for 3-word phrases (Trigrams)
        # kernel_size=4 looks for 4-word phrases (Four-grams)
        num_filters = 100
        
        self.conv2 = nn.Conv1d(in_channels=embed_dim, out_channels=num_filters, kernel_size=2)
        self.conv3 = nn.Conv1d(in_channels=embed_dim, out_channels=num_filters, kernel_size=3)
        self.conv4 = nn.Conv1d(in_channels=embed_dim, out_channels=num_filters, kernel_size=4)
        
        # 3. The Final Classifier
        # We have 3 CNNs, each outputting 100 filters. Total = 300 features.
        self.fc = nn.Linear(3 * num_filters, num_classes)
        self.dropout = nn.Dropout(0.5)

    def forward(self, text_sequence):
        """
        text_sequence shape: [Batch, Seq_Len]
        """
        # Embed the words -> Shape: [Batch, Seq_Len, Embed_Dim]
        embeds = self.embedding(text_sequence)
        
        # CNNs in PyTorch expect the 'Channels' (Embed_Dim) to be in the middle!
        # Shape becomes: [Batch, Embed_Dim, Seq_Len]
        embeds = embeds.transpose(1, 2)
        
        # --- APPLY THE CNNs ---
        # Shape after CNN: [Batch, Num_Filters, Seq_Len - Kernel_Size + 1]
        c2 = F.relu(self.conv2(embeds))
        c3 = F.relu(self.conv3(embeds))
        c4 = F.relu(self.conv4(embeds))
        
        # --- APPLY MAX-OVER-TIME POOLING ---
        # We use F.max_pool1d to find the absolute maximum value across the entire Sequence Length!
        # This collapses the sequence dimension completely. Shape becomes: [Batch, Num_Filters, 1]
        p2 = F.max_pool1d(c2, c2.shape[2]).squeeze(2)
        p3 = F.max_pool1d(c3, c3.shape[2]).squeeze(2)
        p4 = F.max_pool1d(c4, c4.shape[2]).squeeze(2)
        
        # Concatenate the features from all 3 window sizes
        # Shape: [Batch, 300]
        combined_features = torch.cat([p2, p3, p4], dim=1)
        
        # Apply Dropout and Classify!
        dropped = self.dropout(combined_features)
        logits = self.fc(dropped)
        
        return logits

def test_textcnn():
    print("--- RUNNING TEXT-CNN ---")
    
    # Simulate a batch of 4 movie reviews, each 50 words long
    VOCAB_SIZE = 5000
    reviews = torch.randint(0, VOCAB_SIZE, (4, 50))
    
    model = TextCNN(vocab_size=VOCAB_SIZE, embed_dim=128, num_classes=2) # 2 classes: Pos/Neg
    
    predictions = model(reviews)
    
    print(f"Input Shape: {reviews.shape}")
    print(f"Predictions Shape: {predictions.shape}")
    print("The CNN processed all 50 words simultaneously without using a single loop!")

if __name__ == "__main__":
    test_textcnn()
```

### Key Takeaways from Code:
1. **The Shape Transpose:** PyTorch's `nn.Conv1d` expects data in `[Batch, Channels, Length]`. Because embeddings output `[Batch, Length, Channels]`, you *must* use `transpose(1, 2)` before feeding it to the CNN, otherwise the math will crash.
2. **The Max Pooling Squeeze:** Notice `F.max_pool1d(...).squeeze(2)`. The pooling layer shrinks the sequence length down to exactly `1`. By squeezing out that final dimension, we are left with a flat vector of features that we can safely pass into the final `nn.Linear` classifier!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Hierarchical Attention
You must understand how to chain attention mechanisms.
**Your Task:**
1. Conceptually design the `SentenceAttention` layer for a HAN.
2. Assume the input is `[Batch, Num_Sentences, Sentence_Vector_Size]`.
3. Apply a generic `nn.Linear` layer to the vectors, followed by `Tanh`.
4. Multiply by a learnable "Context Vector" (a generic query asking "Which sentence is important?").
5. Apply a `Softmax` over the `Num_Sentences` dimension to get percentages.
6. Multiply the original sentence vectors by these percentages and sum them up to produce the final `[Batch, Document_Vector]`.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are building a real-time Content Moderation system for a social network. It must process 1,000,000 text posts per hour. Compare TextCNN, BiLSTM, and Transformers across three axes: (1) Latency/Throughput, (2) Accuracy on complex sarcasm, and (3) Operational Cloud Cost. Which do you deploy?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Latency & Cost (Throughput):** 
   - State that TextCNN is incredibly fast and extremely cheap because it parallelizes perfectly across the GPU and requires very few FLOPs. 
   - BiLSTMs are unacceptably slow due to the sequential loop. Transformers (like BERT) parallelize well, but the $O(N^2)$ Attention mechanism makes them incredibly expensive to host at a scale of 1M posts/hour.
2. **Accuracy (Sarcasm):**
   - Explain that TextCNN fails at complex long-term dependencies (sarcasm) because it only looks at isolated 3-word windows. 
   - Transformers excel at sarcasm because Self-Attention gives them a global, contextual understanding of the entire post.
3. **The Hybrid Deployment Decision:**
   - Conclude that you deploy a **Cascade Architecture**. You deploy the cheap, blazing-fast TextCNN to instantly filter out the 95% of posts that are obviously safe or obviously toxic. You only route the borderline, ambiguous 5% of posts to the expensive Transformer to evaluate sarcasm, saving millions of dollars in cloud costs.

---
**Task for the end of the day:** Commit your code to Git. You have successfully conquered Text Classification.

Tomorrow, in **Day 52**, we learn the exact mathematical objective that trains ChatGPT. We move away from classification and enter the world of predicting the future: **Language Modeling!**
