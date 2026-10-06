# Day 75: Transfer Learning, Domain Adaptation & Continued Pre-Training

Welcome to Day 75. You have pre-trained your LLM on a massive internet dataset. You are ready to deploy it to a Hospital to summarize Medical Records, or to a pharmaceutical company to reason about genetics.
But you run into a fatal problem: Medical text does not look like Wikipedia text. The vocabulary is different, the grammar is different, and the sentence structure is different. You try Supervised Fine-Tuning (SFT) and the model hallucinates. You try RAG, and the model fails to use the retrieved documents because it doesn't understand the fundamental vocabulary of molecular biology.

This is called a **Distribution Shift**. Today, we learn the full toolbox for adapting a model to a new domain without destroying its previous knowledge: classic **transfer learning and domain-adversarial training** for encoders and classifiers, and **Continued Pre-Training (CPT)**, the method used to inject raw domain knowledge into modern LLMs.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. Types of Distribution Shifts
When the data you trained on (Source Domain) does not match the data in the real world (Target Domain), the AI degrades.
- **Covariate Shift:** The input distribution $P(x)$ changes, but the labels mean the same thing: $P(y|x)$ is unchanged. (e.g., Training a self-driving car in sunny California, but deploying it in snowy Canada; or a sentiment model trained on movie reviews applied to product reviews).
- **Label Shift:** The class balance $P(y)$ changes. (e.g., A disease screener trained at 5% prevalence deployed in a clinic where prevalence is 30%).
- **Concept Drift:** The fundamental truth $P(y|x)$ changes over time. (e.g., In 1990, the word *"Amazon"* meant a river. Today, it usually means a technology company).

### 2. The Transfer Learning Menu
From cheapest to most invasive:
1. **Feature extraction:** Freeze the pre-trained model and train a small head on its embeddings.
2. **Fine-tuning:** Update all (or the top) layers on labeled target data.
3. **Parameter-efficient adapters:** Freeze the base, train LoRA/adapters (Days 96–98).
4. **Unsupervised domain adaptation:** Use *unlabeled* target data to align representations (DANN, below).
5. **Continued pre-training:** Keep training the base model with its original next-token objective on raw domain text (Section 4).

The rule of thumb: fine-tuning and SFT change **behavior** (format, style, task); continued pre-training changes **knowledge and vocabulary**.

### 3. Unsupervised Domain Adaptation (DANN)
Let's say you have 10,000 labeled Wikipedia documents, and 10,000 *unlabeled* Medical documents. How do you train the AI for the hospital if you don't have medical labels?
You use a **Domain-Adversarial Neural Network (DANN)** (Ganin et al., 2016). 
It borrows the adversarial logic from GANs (Day 57):

1. You feed both Wikipedia and Medical documents into a Feature Extractor (e.g., BERT).
2. The Extractor creates a 512D embedding.
3. A **Task Classifier** is trained on the labeled Wikipedia embeddings as usual.
4. A **Domain Classifier** (a small network) looks at every embedding and tries to guess: *"Is this Wikipedia, or is this Medical?"*
5. **The Trick:** A **Gradient Reversal Layer (GRL)** sits between the Extractor and the Domain Classifier. In the forward pass it does nothing. During backpropagation, it *multiplies the gradient by $-\lambda$* before it reaches the Feature Extractor.
6. **The Result:** The Domain Classifier still learns to tell the domains apart, but the Extractor is pushed to *fool* it. The embeddings lose the "Medical-ness" and "Wikipedia-ness" that the task doesn't need and become domain-invariant, so the task head trained on Wikipedia labels transfers to the hospital.

DANN is the classic answer for encoders and classifiers. It does not help a generative LLM learn *what* the new domain knows. For that you need CPT.

### 4. Continued Pre-Training (CPT) for LLMs
- **SFT (Supervised Fine-Tuning):** Changes the model's *behavior* (e.g., "Always respond in JSON format"). SFT requires high-quality prompt/response pairs, and research shows that using SFT to teach facts the model doesn't already know is slow and *increases* hallucination (Gekhman et al., 2024).
- **CPT (Continued Pre-Training):** Injects *raw knowledge and vocabulary*. CPT does not use Q/A pairs. It uses millions of raw, unstructured domain documents (research papers, clinical notes, codebases, legal filings). The objective is plain Next-Token Prediction, exactly like original pre-training. "Don't Stop Pretraining" (Gururangan et al., 2020) showed that even a short domain-adaptive phase (DAPT), and a task-adaptive phase on the unlabeled task text itself (TAPT), consistently improve downstream results.

Well-known domain models built this way: **CodeLlama** (code), **Meditron** (medicine), **SaulLM** (law), **Galactica** (science), and the math-heavy **DeepSeekMath** and **Llemma**.

### 5. The Learning Rate Danger (Catastrophic Forgetting)
The most critical hyperparameter in CPT is the Learning Rate. 
If you use a high learning rate, the model rapidly absorbs the medical textbooks, but it suffers **Catastrophic Forgetting**: the new gradients overwrite what the original weights encoded, and general ability (grammar, reasoning, instruction following) collapses.
In practice teams re-warm the learning rate to a peak well below the original pre-training peak (often around a tenth of it, sometimes much lower) and then decay it again. You want to *nudge* the weights, not overwrite them.

### 6. Data Mixing (The General Replay)
To further prevent forgetting, you cannot train *exclusively* on Medical data.
You mix your Domain Data with **General Replay Data**: a slice of text resembling the original pre-training mix. If your dataset is $80\%$ Medical Textbooks, the other $20\%$ is general web/Wikipedia/code. Published continual-pre-training studies found that even a few percent of replay, combined with a re-warmed and re-decayed learning rate, recovers most of the forgetting; 5–25% is a common range. The same idea protects a classic fine-tuned classifier: keep a **replay buffer** of old training data.

### 7. Curriculum & Tokenizer
- **Curriculum:** Do not shock the model. Start the CPT mix at $50\%$ General / $50\%$ Medical and shift it over the run until the final stretch is $10\%$ General / $90\%$ Medical.
- **Tokenizer:** If domain terms split into many tokens (a protein name becoming 9 tokens), you can extend the vocabulary with new tokens. The new embedding rows start untrained, so initialize them as the mean of their old sub-token embeddings and give CPT enough steps to learn them.

### 8. The Full Adaptation Pipeline
`Base model` $\rightarrow$ **CPT** on domain text + replay (knowledge) $\rightarrow$ **SFT** on domain instructions (behavior) $\rightarrow$ **DPO/RLHF** (preferences and safety, Days 101–105) $\rightarrow$ **Evaluation on both domain and general benchmarks**. Skipping the general benchmarks is how teams ship a model that aces pharmacology and can no longer write a coherent email.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Two builds today: the Gradient Reversal Layer that powers DANN, and the sequence-packing data loader that powers CPT.

### Part 1: Domain-Adversarial Training (PyTorch)

We write the custom `GradientReversalLayer` and bolt it onto a standard network, then *prove* the gradient flips sign.

Create a file named `domain_adaptation.py`:

```python
import torch
import torch.nn as nn
from torch.autograd import Function


# 1. THE MAGIC: Gradient Reversal Layer (GRL)
class GradientReversalFunction(Function):
    @staticmethod
    def forward(ctx, x, alpha):
        ctx.alpha = alpha            # save alpha for the backward pass
        return x.view_as(x)          # forward pass: identity

    @staticmethod
    def backward(ctx, grad_output):
        # Backward pass: multiply the gradient by -alpha.
        # The extractor receives the OPPOSITE of what the domain loss wants.
        return grad_output.neg() * ctx.alpha, None


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
        # Shared feature extractor (stand-in for a BERT encoder's output layers)
        self.feature_extractor = nn.Sequential(
            nn.Linear(input_dim, 256), nn.ReLU(),
            nn.Linear(256, 128), nn.ReLU(),
        )
        # Pathway A: the task classifier (e.g., sentiment), trained on labeled source data
        self.task_classifier = nn.Linear(128, num_classes)
        # Pathway B: the domain classifier (Wikipedia vs Medical), GRL inserted FIRST
        self.domain_classifier = nn.Sequential(
            GradientReversalLayer(alpha=1.0),
            nn.Linear(128, 2),
        )

    def forward(self, x):
        features = self.feature_extractor(x)
        return self.task_classifier(features), self.domain_classifier(features)


def test_dann():
    print("--- DOMAIN ADVERSARIAL NEURAL NETWORK ---")
    torch.manual_seed(0)

    # Prove the GRL flips the gradient: d(sum(GRL(x)))/dx should be -1
    x = torch.ones(3, requires_grad=True)
    GradientReversalLayer(alpha=1.0)(x).sum().backward()
    print(f"Gradient through GRL: {x.grad.tolist()}  (identity would give +1)")

    model = DANN(input_dim=512)
    src = torch.randn(4, 512)                   # labeled Wikipedia embeddings
    tgt = torch.randn(4, 512) + 0.5             # unlabeled Medical embeddings (shifted)
    src_labels = torch.tensor([0, 1, 1, 0])
    domain_labels = torch.tensor([0] * 4 + [1] * 4)

    task_out, _ = model(src)
    _, domain_out = model(torch.cat([src, tgt]))
    ce = nn.CrossEntropyLoss()
    loss = ce(task_out, src_labels) + ce(domain_out, domain_labels)
    loss.backward()

    print(f"Task logits: {tuple(task_out.shape)}, domain logits: {tuple(domain_out.shape)}")
    print(f"Combined loss: {loss.item():.4f}")
    print("The domain head learns to separate domains; the extractor receives the")
    print("reversed gradient and learns features the domain head CANNOT separate.")


if __name__ == "__main__":
    test_dann()
```

### Part 2: Continued Pre-Training Data Packing (pure Python)

Unlike SFT, which uses short chat-formatted examples, CPT packs raw documents into dense blocks of exactly `block_size` tokens (the context window, e.g., 4096). No padding is wasted.

Create a file named `cpt_packing.py`:

```python
import random


class MockTokenizer:
    """1 word = 1 token for this simulation."""
    eos_token = "<|END_OF_DOC|>"

    def encode(self, text):
        return text.split()


def mixed_stream(domain_docs, general_docs, domain_fraction, n_docs, seed=0):
    """Sample documents so that ~domain_fraction come from the domain corpus (the rest is general replay)."""
    rng = random.Random(seed)
    for _ in range(n_docs):
        pool = domain_docs if rng.random() < domain_fraction else general_docs
        yield rng.choice(pool)


def pack(stream, tokenizer, block_size):
    """Concatenate documents (separated by EOS) and cut into full blocks; keep the remainder."""
    buffer = []
    for doc in stream:
        buffer.extend(tokenizer.encode(doc) + [tokenizer.eos_token])
        while len(buffer) >= block_size:
            block, buffer = buffer[:block_size], buffer[block_size:]
            # Causal-LM trainers take labels == input_ids and shift by one internally,
            # so every token in the block is a prediction target.
            yield {"input_ids": block, "labels": list(block)}


def run_cpt_simulation():
    tok = MockTokenizer()
    medical = ["The mitochondria is the powerhouse of the cell.",
               "CRISPR-Cas9 allows targeted genome editing.",
               "Apoptosis is programmed cell death."]
    general = ["The capital of France is Paris.",
               "Water boils at 100 degrees Celsius at sea level."]

    print("--- CONTINUED PRE-TRAINING: CURRICULUM + REPLAY + PACKING ---\n")
    # Curriculum: the domain share rises over the run, replay never drops to zero.
    for phase, frac in [("early", 0.5), ("middle", 0.7), ("late", 0.9)]:
        docs = list(mixed_stream(medical, general, frac, n_docs=200, seed=len(phase)))
        share = sum(d in medical for d in docs) / len(docs)
        blocks = list(pack(iter(docs), tok, block_size=16))
        print(f"{phase:>6}: target domain share {frac:.0%}, sampled {share:.0%}, "
              f"{len(blocks)} packed blocks of 16 tokens")

    first = next(pack(iter(medical + general), tok, block_size=16))
    print("\nFirst packed block (note documents are glued together with EOS):")
    print(first["input_ids"])
    print("\n[TRAINING] Cross-entropy on every token. Peak LR re-warmed to a fraction")
    print("of the original pre-training peak, then decayed again.")


if __name__ == "__main__":
    run_cpt_simulation()
```

### Key Takeaways from Code:
1. **`torch.autograd.Function`:** To invent a new backpropagation rule in PyTorch, you inherit from `Function` and write `forward` and `backward` yourself. The printed gradient of `-1` is the whole trick of adversarial domain adaptation in one number.
2. **`grad_output.neg()`:** If the Domain Classifier says *"I am 99% sure this is a Medical document"*, the gradient flowing back hits the GRL, flips sign, and tells the Feature Extractor: *"Change your weights so it looks LESS like a Medical document!"*
3. **Packing:** Documents get glued into the same block, separated by an EOS token, so the GPU never computes on padding. (Production trainers can also mask attention across document boundaries so one document cannot attend to the previous one.)
4. **Next-Token Prediction on every token:** In SFT we mask the loss on the prompt. In CPT, the loss covers every token in the block: the model is learning the statistical distribution of the domain's language.
5. **Replay never goes to zero:** even the "late" phase keeps ~10% general text.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge (pick one, or both)
**A. Covariate Shift Detection.** Before you can adapt to a domain, you need to know a shift has occurred in production.
1. Store the mean and covariance of the 512D embeddings of your training data (Wikipedia).
2. In production, as medical documents flow in, compute a moving window of their embeddings.
3. Measure the distance between the training and production distributions (Euclidean distance between means, KL divergence under a Gaussian fit, or Maximum Mean Discrepancy).
4. Alert when it crosses a threshold: *"Covariate Shift Detected! Model performance is likely degrading!"* (Day 168 goes deeper on drift detection.)

**B. Perplexity Evaluation of CPT.** How do you know if your CPT worked?
1. Hold out 1,000 Medical documents the model has never seen, plus 1,000 general documents.
2. Before CPT, calculate the base model's perplexity on both sets. (Medical will be high because the jargon surprises it.)
3. After CPT, calculate both again. Success means medical perplexity dropped *and* general perplexity barely moved. If general perplexity rose sharply, increase replay or lower the learning rate.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting verbal answers to these two questions.

**Question 1:**
*"Your production NLP model was trained on 2023 data, but language has shifted (new slang, recent events). Design a continuous adaptation system that doesn't require full retraining from scratch."*

#### 📝 Strong Hire Rubric:
1. **The Problem of Catastrophic Forgetting:** If you simply fine-tune the 2023 model on 2024 data, it overfits to the new data and forgets the old distribution.
2. **Drift detection first:** Monitor embedding/prediction distributions so adaptation is triggered by evidence, not a calendar.
3. **Replay Buffers:** Store a randomized, high-quality subset of the 2023 training data and mix 10–20% of it into every update.
4. **LoRA (Low-Rank Adaptation, Day 97):** Freeze the base model and train small LoRA adapters on the new data. Cheap, fast, reversible (you can roll back by unloading the adapter), and the original knowledge stays physically intact in the base weights.
5. **Gate every update** on a fixed regression suite covering old and new data before it ships.

**Question 2:**
*"A pharmaceutical company wants an LLM specialized in drug discovery. They have 10 Million PDFs of internal research. Design the complete adaptation pipeline from base model to production deployment. How do you validate scientific accuracy?"*

#### 📝 Strong Hire Rubric:
1. **The Pipeline (CPT $\rightarrow$ SFT $\rightarrow$ DPO):** 
   - Extract text from the PDFs (tables and chemical structures need special handling), deduplicate (Day 74), and run **Continued Pre-Training** with ~5–20% general replay and a conservative, re-warmed learning rate to inject the vocabulary and knowledge.
   - Generate Q/A pairs grounded in those documents with a strong teacher LLM, have domain experts review a sample, and run **SFT** to teach assistant behavior.
   - Run **DPO** (Day 104) for preferences and safety (e.g., refusing to give synthesis routes for controlled substances).
2. **Keep RAG anyway:** CPT gives understanding; RAG gives up-to-date, citable facts. Production systems combine them.
3. **Validating Scientific Accuracy:**
   - Perplexity and general benchmarks (MMLU) are not enough. Build a domain eval set with PhD chemists: held-out questions with verified answers, plus an **LLM-as-a-Judge** rubric written by the experts for open-ended answers (checked against expert grades so you trust the judge).
   - Track general benchmarks alongside to catch forgetting, and run blinded A/B testing with internal scientists before rollout.

---
**Task for the end of the day:** Commit your code to Git. 

Tomorrow, in **Day 76**, we tackle the next engineering problem: You trained a massive LLM, but you need to deploy it to a smartwatch. We will learn the ultimate compression algorithm: **Knowledge Distillation**!
