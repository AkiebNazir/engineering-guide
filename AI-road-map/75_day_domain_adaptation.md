# Day 75: Transfer Learning & Domain Adaptation

Welcome to Day 75. You have pre-trained your <abbr title="Large Language Model">LLM</abbr> on a massive internet dataset. You are ready to deploy it to a Hospital to summarize Medical Records.
But you run into a fatal problem: Medical text does not look like Wikipedia text. The vocabulary is different, the grammar is different, and the sentence structure is different.

This is called a **Distribution Shift**. Today, we learn how to mathematically force an <abbr title="Artificial Intelligence">AI</abbr> to adapt to a new domain without destroying its previous knowledge.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Types of Distribution Shifts
When the data you trained on (Source Domain) does not match the data in the real world (Target Domain), the <abbr title="Artificial Intelligence">AI</abbr> degrades.
- **Covariate Shift:** The input features change, but the labels mean the same thing. (e.g., Training a self-driving car in sunny California, but deploying it in snowy Canada).
- **Concept Drift:** The fundamental truth changes over time. (e.g., In 1990, the word *"Amazon"* meant a river. In 2024, it means a technology company). 

### 2. Unsupervised Domain Adaptation (DANN)
Let's say you have 10,000 labeled Wikipedia documents, and 10,000 *unlabeled* Medical documents. How do you train the <abbr title="Artificial Intelligence">AI</abbr> for the hospital if you don't have medical labels?
You use a **Domain-Adversarial Neural Network (DANN)**. 
This is one of the most brilliant tricks in Deep Learning. It borrows the logic from GANs (Day 57)!

1. You feed both Wikipedia and Medical documents into a Feature Extractor (BERT).
2. The Extractor creates a 512D embedding.
3. You add a **Domain Classifier** (a small network) that looks at the embedding and tries to guess: *"Is this Wikipedia, or is this Medical?"*
4. **The Trick:** You use a **Gradient Reversal Layer (GRL)**. During backpropagation, you mathematically *multiply the gradient by -1* before it reaches the Feature Extractor.
5. **The Result:** The Extractor is mathematically forced to update its weights to *fool* the Domain Classifier. It physically deletes the "Medical-ness" and "Wikipedia-ness" from the embeddings! The embeddings become Domain-Agnostic, allowing the model to perform perfectly in the Hospital!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's implement the magic of Domain Adaptation. We will write the custom `GradientReversalLayer` in PyTorch and bolt it onto a standard network!

Create a file named `domain_adaptation.py`:

```python
import torch
import torch.nn as nn
from torch.autograd import Function

# 1. THE MAGIC: Gradient Reversal Layer (GRL)
class GradientReversalFunction(Function):
    @staticmethod
    def forward(ctx, x, alpha):
        # Save alpha for the backward pass
        ctx.alpha = alpha
        # During the forward pass, do absolutely nothing! Just pass x through.
        return x.view_as(x)

    @staticmethod
    def backward(ctx, grad_output):
        # DURING BACKPROPAGATION: Multiply the gradient by -alpha!
        # This forces the network to do the exact OPPOSITE of what the loss function wants!
        output = grad_output.neg() * ctx.alpha
        return output, None

class GradientReversalLayer(nn.Module):
    def __init__(self, alpha=1.0):
        super().__init__()
        self.alpha = alpha

    def forward(self, x):
        return GradientReversalFunction.apply(x, self.alpha)

# 2. The DANN Architecture
class DANN(nn.Module):
    def __init__(self, input_dim=512, num_classes=2):
        super().__init__()
        
        # The Main Feature Extractor (e.g., the output of a BERT encoder)
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_dim, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU()
        )
        
        # Pathway A: The standard Task Classifier (e.g., Sentiment Analysis)
        self.task_classifier = nn.Sequential(
            nn.Linear(128, num_classes)
        )
        
        # Pathway B: The Domain Classifier (Wikipedia vs Medical)
        # Notice we insert the Gradient Reversal Layer FIRST!
        self.domain_classifier = nn.Sequential(
            GradientReversalLayer(alpha=1.0),
            nn.Linear(128, 2)
        )

    def forward(self, x):
        # 1. Extract the shared features
        features = self.feature_extractor(x)
        
        # 2. Predict the Task (Standard backprop)
        task_preds = self.task_classifier(features)
        
        # 3. Predict the Domain (Reversed backprop!)
        domain_preds = self.domain_classifier(features)
        
        return task_preds, domain_preds

def test_dann():
    print("--- RUNNING DOMAIN ADVERSARIAL NEURAL NETWORK ---")
    
    BATCH_SIZE = 4
    INPUT_DIM = 512
    
    # Simulate embeddings from Wikipedia (Domain 0) and Medical (Domain 1)
    mock_embeddings = torch.randn(BATCH_SIZE, INPUT_DIM)
    
    model = DANN(input_dim=INPUT_DIM)
    task_out, domain_out = model(mock_embeddings)
    
    print(f"Input Shape: {mock_embeddings.shape}")
    print(f"Task Predictions: {task_out.shape} (e.g., Positive vs Negative)")
    print(f"Domain Predictions: {domain_out.shape} (Wikipedia vs Medical)")
    
    print("\nBecause of the GRL, when we call .backward(), the Feature Extractor")
    print("will update its weights to make the Domain Output as INACCURATE as possible!")
    print("This forces the embeddings to become Domain-Agnostic!")

if __name__ == "__main__":
    test_dann()
```

### Key Takeaways from Code:
1. **`torch.autograd.Function`:** In PyTorch, if you want to invent a completely new mathematical rule for Backpropagation, you inherit from `Function` and manually write the `forward` and `backward` methods.
2. **`grad_output.neg()`:** This is the core of Adversarial Learning. If the Domain Classifier says *"I am 99% sure this is a Medical document"*, the gradient flows backwards, hits the GRL, multiplies by $-1$, and tells the Feature Extractor: *"Change your weights so it looks LESS like a Medical document!"*

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Covariate Shift Detection
Before you can adapt to a domain, you need to know a shift has occurred in production.
**Your Task:**
1. Conceptually write a monitoring script.
2. Store the mean and variance of the 512D embeddings of your training data (Wikipedia).
3. In production, as medical documents flow in, calculate a moving average of their embeddings.
4. Calculate the Euclidean Distance (or KL Divergence) between the Training Distribution and the Production Distribution.
5. Set an alert: If the distance exceeds a threshold, send a Slack message to the MLOps team saying: *"Covariate Shift Detected! Model performance is likely degrading!"*

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your production <abbr title="Natural Language Processing">NLP</abbr> model was trained on 2023 data, but language has shifted (new slang, recent events). Design a continuous adaptation system that doesn't require full retraining from scratch."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Problem of Catastrophic Forgetting:** 
   - State that if you simply fine-tune the 2023 model on 2024 data, it will overfit to the new data and "forget" the 2023 data completely.
2. **Replay Buffers:**
   - Propose a Continuous Learning pipeline using a Replay Buffer. Store a small, randomized subset of the high-quality 2023 training data. 
   - When training on 2024 data, mix in 10-20% of the old data to anchor the model's weights and prevent catastrophic forgetting.
3. **<abbr title="Low-Rank Adaptation">LoRA</abbr> (Low-Rank Adaptation):**
   - Suggest that instead of updating the massive 70B parameter model directly, you freeze the base model and inject tiny <abbr title="Low-Rank Adaptation">LoRA</abbr> adapters (Day 83 topic!) into the attention layers. Train the adapter exclusively on the 2024 data. This allows rapid, cheap adaptation while physically preserving the original 2023 knowledge in the base weights.

---
**Task for the end of the day:** Commit your code to Git. 

Tomorrow, in **Day 76**, we tackle the final engineering problem: You trained a massive <abbr title="Large Language Model">LLM</abbr>, but you need to deploy it to a smartwatch. We will learn the ultimate compression algorithm: **Knowledge Distillation**!
