# Day 16: Stochastic Gradient Descent (SGD) & Variance Reduction

Welcome to Day 16. Yesterday, we built the standard Gradient Descent algorithm. To find the exact slope of the mountain, we had to calculate the error for every single row in our dataset. 

But what if your dataset is Wikipedia (3 billion words) or ImageNet (14 million images)? If you have to process 14 million images just to take *one* step downhill, your <abbr title="Artificial Intelligence">AI</abbr> will take decades to train. 

Today, we learn how to cheat the math using probability. We introduce **Stochastic Gradient Descent (<abbr title="Stochastic Gradient Descent">SGD</abbr>)**, the algorithm that makes Deep Learning physically possible.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. The Power of "Stochastic" (Randomness)
Instead of calculating the exact gradient over 14 million images, what if we pick just **one** random image, calculate the gradient, and immediately take a step?

This is called **Stochastic Gradient Descent (<abbr title="Stochastic Gradient Descent">SGD</abbr>)**. 
- *The downside:* The gradient of a single image is incredibly noisy. If it's a picture of a cat, the gradient says "Change all weights to perfectly recognize cats!" It might point you exactly sideways, or even slightly uphill!
- *The upside:* Mathematically, the **Expectation** (average) of these chaotic, random gradients is exactly equal to the true gradient of the whole dataset: $\mathbb{E}[\nabla_\theta \mathcal{L}_i] = \nabla_\theta \mathcal{L}$.
- Over 14 million incredibly fast, jagged, chaotic steps, you will still reach the bottom of the valley in a fraction of the time it takes standard GD.

### 2. Mini-Batch <abbr title="Stochastic Gradient Descent">SGD</abbr>: The Gold Standard
Pure <abbr title="Stochastic Gradient Descent">SGD</abbr> (batch size = 1) is too chaotic, and it cannot utilize the massive parallel processing power of modern GPUs.
Standard GD (batch size = 14 million) is too slow, and it crashes GPU memory.

The solution is **Mini-Batch <abbr title="Stochastic Gradient Descent">SGD</abbr>**. We pick a random chunk of data (usually between 32 and 256 items). 
**Variance Reduction Formula:** $\text{Var} \propto \frac{1}{B}$
*(The mathematical variance/chaos of the gradient drops proportionally to the size of the Batch $B$)*. 

By using a batch of 128, the gradient points *mostly* downhill, and your GPU matrix cores can process all 128 images simultaneously. 

### 3. Gradient Noise as Implicit Regularization
Why don't we just buy a giant $1,000,000 supercomputer with enough <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> to process the whole dataset at once?
Because we *want* the noise!

> **<abbr title="Artificial Intelligence">AI</abbr> Context (The Generalization Gap):** 
> If you train with a massive batch size, the gradient is perfectly smooth. The <abbr title="Artificial Intelligence">AI</abbr> will slide perfectly into the very first valley it finds. But what if that valley is a "Local Minimum" (a false bottom) that only applies to the training data?
> 
> The chaotic noise of Mini-Batch <abbr title="Stochastic Gradient Descent">SGD</abbr> acts as an earthquake. If the <abbr title="Artificial Intelligence">AI</abbr> falls into a shallow, bad valley, the random gradient noise will literally "bounce" the <abbr title="Artificial Intelligence">AI</abbr> back out of it! It forces the <abbr title="Artificial Intelligence">AI</abbr> to keep wandering until it finds a massive, deep, wide valley (the Global Minimum). Models trained with Mini-Batch <abbr title="Stochastic Gradient Descent">SGD</abbr> generalize much better to unseen data!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's write a script that proves how much faster <abbr title="Stochastic Gradient Descent">SGD</abbr> is than standard Gradient Descent. We will also implement **Gradient Accumulation**, a crucial software engineering trick used by researchers who don't have infinite GPU memory.

Create a file named `sgd_and_accumulation.py`:

```python
import numpy as np
import matplotlib.pyplot as plt

def generate_massive_data():
    """Generates 10,000 rows of data"""
    X = np.random.rand(10000, 1) * 10
    y = 3 * X + 5 + np.random.randn(10000, 1) * 2
    return X, y

def train_models(X, y):
    """
    Compares Standard GD, Pure SGD, and Mini-Batch SGD.
    Notice the difference in the number of steps they get to take per epoch!
    """
    print("--- OPTIMIZER RACE ---")
    m = len(y)
    epochs = 5 # An epoch is one full pass over the entire dataset
    lr = 0.01
    
    # Standard GD (Batch Size = 10,000)
    W_gd, b_gd = np.random.randn(1,1), np.random.randn(1)
    # Pure SGD (Batch Size = 1)
    W_sgd, b_sgd = np.copy(W_gd), np.copy(b_gd)
    # Mini-Batch (Batch Size = 128)
    W_mb, b_mb = np.copy(W_gd), np.copy(b_gd)
    batch_size = 128
    
    loss_gd, loss_sgd, loss_mb = [], [], []
    
    for epoch in range(epochs):
        # 1. Standard GD (1 massive step per epoch)
        y_pred_gd = X.dot(W_gd) + b_gd
        W_gd -= lr * (1/m) * np.sum((y_pred_gd - y) * X)
        b_gd -= lr * (1/m) * np.sum(y_pred_gd - y)
        loss_gd.append(np.mean((y_pred_gd - y)**2))
        
        # Shuffle data for stochasticity
        indices = np.random.permutation(m)
        X_shuf, y_shuf = X[indices], y[indices]
        
        # 2. Pure SGD (10,000 chaotic steps per epoch!)
        current_loss_sgd = 0
        for i in range(m):
            xi, yi = X_shuf[i:i+1], y_shuf[i:i+1]
            pred = xi.dot(W_sgd) + b_sgd
            W_sgd -= lr * np.sum((pred - yi) * xi)
            b_sgd -= lr * np.sum(pred - yi)
            current_loss_sgd += np.mean((pred - yi)**2)
        loss_sgd.append(current_loss_sgd / m)
        
        # 3. Mini-Batch SGD (78 fast, stable steps per epoch)
        current_loss_mb = 0
        for i in range(0, m, batch_size):
            X_batch = X_shuf[i:i+batch_size]
            y_batch = y_shuf[i:i+batch_size]
            pred = X_batch.dot(W_mb) + b_mb
            W_mb -= lr * (1/len(y_batch)) * np.sum((pred - y_batch) * X_batch)
            b_mb -= lr * (1/len(y_batch)) * np.sum(pred - y_batch)
            current_loss_mb += np.mean((pred - y_batch)**2)
        loss_mb.append(current_loss_mb / (m/batch_size))
        
    print(f"Final Standard GD Loss: {loss_gd[-1]:.3f}")
    print(f"Final Pure SGD Loss:    {loss_sgd[-1]:.3f}")
    print(f"Final Mini-Batch Loss:  {loss_mb[-1]:.3f}")
    print("Mini-Batch perfectly balances speed and stability!")

def gradient_accumulation_example():
    """
    Software trick: What if you WANT a batch size of 256, 
    but your tiny GPU crashes if you load more than 32 images at a time?
    """
    print("\n--- GRADIENT ACCUMULATION ---")
    target_batch_size = 256
    micro_batch_size = 32
    accumulation_steps = target_batch_size // micro_batch_size # 8 steps
    
    print(f"Target Batch: {target_batch_size}")
    print(f"Micro-Batch (Fits in GPU RAM): {micro_batch_size}")
    print(f"We will run the model {accumulation_steps} times, adding up the gradients, BEFORE taking a step.")
    
    # Pseudo-code structure for PyTorch/TensorFlow:
    # 
    # optimizer.zero_grad()
    # for i, (x_micro, y_micro) in enumerate(dataloader):
    #     loss = model(x_micro, y_micro)
    #     loss = loss / accumulation_steps  # Normalize!
    #     loss.backward()                   # Math is added (accumulated) in memory
    #     
    #     if (i + 1) % accumulation_steps == 0:
    #         optimizer.step()              # Physically update the weights
    #         optimizer.zero_grad()         # Reset for the next massive batch
    print("You can now train massive LLMs on a single consumer GPU!")

if __name__ == "__main__":
    X, y = generate_massive_data()
    train_models(X, y)
    gradient_accumulation_example()
```

### Key Takeaways from Code:
1. **The Step Count Inequality:** In 5 epochs, Standard GD took exactly 5 steps downhill. Pure <abbr title="Stochastic Gradient Descent">SGD</abbr> took 50,000 chaotic steps. Mini-batch took 390 perfectly sized steps. This is why standard GD is completely dead in modern <abbr title="Artificial Intelligence">AI</abbr>.
2. **Gradient Accumulation Magic:** If you divide the loss by your `accumulation_steps`, mathematically, taking 8 small steps and adding them together is *exactly identical* to taking 1 massive step with a 256 batch size. You trade Time for Memory!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The MNIST Logistics
**Your Task:**
1. Grab a famous dataset like **MNIST** (70,000 images of handwritten digits) using `scikit-learn` or `PyTorch`.
2. Implement a simple Logistic Regression classifier.
3. Train it once using a Batch Size of `1` (Pure <abbr title="Stochastic Gradient Descent">SGD</abbr>). Plot the loss curve. It will look like a terrifying earthquake.
4. Train it again using a Batch Size of `10,000`. Plot the curve. It will be perfectly smooth, but it might take 10 minutes to train.
5. Train it with a Batch Size of `128`. Observe the perfect combination of slight noise and massive speed!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"At Google, we use thousands of TPUs to train LLMs with an effective Batch Size of 32,768 images at once. Because we increased the batch size, the Linear Scaling Rule says we should massively increase the Learning Rate. However, when we do this, the model instantly explodes to NaN in the first 10 steps. Why does this happen, what is a 'Warmup' schedule, and why do we use specialized LARS/LAMB optimizers for these massive batches?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Early Training Danger:** 
   - State that at the very beginning of training, the model's weights are completely random. The gradients are incredibly volatile. If you use a massive Learning Rate immediately, that volatility is multiplied, shooting the weights to infinity (NaN).
2. **The Warmup Schedule:**
   - Explain that a **Warmup Schedule** solves this by starting the Learning Rate near exactly $0.0$. Over the first few thousand steps (while the model figures out the basic layout of the loss landscape), the Learning Rate linearly increases until it hits the massive target rate.
3. **The LARS/LAMB Optimizers:**
   - Mention that standard <abbr title="Stochastic Gradient Descent">SGD</abbr> breaks at 32k batch sizes because some layers of the neural network have huge gradients, and some have tiny gradients. Applying one massive Learning Rate to all layers destroys the delicate layers.
   - **LARS (Layer-wise Adaptive Rate Scaling)** mathematically checks the size of the weights and gradients for *each individual layer*, and custom-scales the learning rate layer-by-layer to ensure no single layer explodes!

---
**Task for the end of the day:** Commit your code to Git. You now understand how engineers fit billion-parameter models onto tiny GPUs. 

Tomorrow, in **Day 17**, we take our Mini-Batch gradients and add the physics of **Momentum**. We will build the most famous optimizers in the world: RMSProp and **Adam**!
